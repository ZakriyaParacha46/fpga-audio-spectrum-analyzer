`timescale 1ns / 1ps
//
// fft_view: 256-bin magnitude spectrum display, computed with a bank of
// 256 Goertzel resonators rather than a radix-2 FFT butterfly network.
// Both are legitimate DFT implementations and give identical per-bin
// magnitudes for a fixed set of bins - Goertzel is used here because
// its control logic is a plain nested loop (no bit-reversal addressing,
// no staged twiddle-factor indexing), which matters a lot when the
// only way to test this is a full synth->impl->bitstream->hardware
// cycle with no simulator in the loop.
//
// FFT_SIZE = 512 real samples in, giving bins 0..256 out (real input ->
// Hermitian-symmetric spectrum, so only half the transform is unique).
// Bin 0 (DC) is skipped; bins 1..256 are displayed as 256 bars - which
// is why "256 bins" needs a 512-point transform, not a 256-point one.
//
// Pipeline:
//   1. Continuously collect `level` into a ping-pong pair of 512-deep
//      sample buffers at SAMPLE_RATE (one buffer fills while the other
//      is read by the step below), so the read side is never disturbed
//      mid-computation by fresh incoming samples.
//   2. Whenever a buffer finishes filling, sweep bin_idx = 1..256; for
//      each bin, run the Goertzel recurrence over all 512 samples, then
//      compute that bin's power (magnitude squared - no sqrt needed).
//   3. Compress power's huge dynamic range with an approximate log2
//      (position of the highest set bit + a few fractional bits from
//      the bits just below it, for smoother-looking bars instead of
//      blocky power-of-two jumps), then map to a bar height.
//   4. Bar heights live in their own ping-pong pair, swapped at a frame
//      boundary - same anti-tearing discipline waveform_view uses for
//      its trace buffers.
//
// A full 256-bin sweep takes 256*512 = 131,072 cycles (~2ms @ 65MHz) -
// far faster than the ~10.7ms it takes to even collect 512 fresh
// samples at 48kHz, so throughput is never the bottleneck.
//
module fft_view #(
    parameter integer CLK_FREQ    = 65_000_000,
    parameter integer SAMPLE_RATE = 48_000,
    parameter integer HEIGHT      = 384,
    parameter integer X_OFFSET    = 0,
    parameter integer Y_OFFSET    = 0
) (
    input  wire         clk,
    input  wire         reset,
    input  wire [11:0]  level,
    input  wire [10:0]  pixel_x,
    input  wire [9:0]   pixel_y,
    input  wire         video_on,
    input  wire [3:0]   lp_shift,     // live lowpass_filter shift, for the cutoff marker
    input  wire [3:0]   hp_shift,     // live highpass_filter shift, for the cutoff marker
    output wire         pixel_on,
    output wire         axis_on,      // single baseline at the bottom of the view
    output wire         lp_cutoff_on, // vertical marker at the lowpass cutoff bin
    output wire         hp_cutoff_on  // vertical marker at the highpass cutoff bin
);

    // Valid range for lp_shift/hp_shift - MUST match the clamp range
    // top.v's shift-control counters enforce. Below MIN_SHIFT the
    // cutoff exceeds this FFT's own Nyquist (24kHz) and would pin off
    // the right edge; above MAX_SHIFT it drops below one bin's 93.75Hz
    // resolution and would pin to bin 0 - the table below only covers
    // the range where the marker actually moves meaningfully.
    localparam integer MIN_SHIFT = 3;
    localparam integer MAX_SHIFT = 11;

    // shift_to_bin[s] = round((fs_filter/(2*pi*2^s)) / (SAMPLE_RATE/512)) - 1,
    // fs_filter ~= 963.5kHz (the ADC's real continuous-conversion rate
    // - see lowpass_filter's cutoff-frequency derivation). Generated
    // numerically, not hand-computed, same reasoning as coeff_rom.
    function [8:0] shift_to_bin;
        input [3:0] s;
        begin
            case (s)
                4'd3:  shift_to_bin = 9'd203;
                4'd4:  shift_to_bin = 9'd101;
                4'd5:  shift_to_bin = 9'd50;
                4'd6:  shift_to_bin = 9'd25;
                4'd7:  shift_to_bin = 9'd12;
                4'd8:  shift_to_bin = 9'd5;
                4'd9:  shift_to_bin = 9'd2;
                4'd10: shift_to_bin = 9'd1;
                4'd11: shift_to_bin = 9'd0;
                default: shift_to_bin = 9'd0;  // out-of-range input, clamp low
            endcase
        end
    endfunction

    wire [8:0] lp_cutoff_bin = shift_to_bin(lp_shift);
    wire [8:0] hp_cutoff_bin = shift_to_bin(hp_shift);

    localparam integer FFT_SIZE  = 512;
    localparam integer NUM_BINS  = 256;
    localparam integer BIN_WIDTH = 2;
    localparam integer BIN_GAP   = 2;
    localparam integer BIN_PITCH = BIN_WIDTH + BIN_GAP;         // 4
    // NUM_BINS * BIN_PITCH = 1024 - this view is always full-width by
    // construction, so WIDTH isn't a free parameter here.

    // Tune these two by eye against real hardware, same as BASELINE /
    // SHIFT elsewhere in this project - there's no way to compute the
    // "right" values without seeing what real signal power looks like.
    localparam integer FLOOR = 140;  // log2-units subtracted as a noise floor
    localparam integer SCALE = 2;    // contrast multiplier after the floor

    // --- Synchronize 'level' into this clock domain (same pattern as
    // waveform_view) ---
    reg [11:0] level_sync0, level_sync1;
    always @(posedge clk) begin
        level_sync0 <= level;
        level_sync1 <= level_sync0;
    end

    // --- Sample-rate tick ---
    localparam integer TICK_COUNT = CLK_FREQ / SAMPLE_RATE;
    reg [31:0] tick_counter;
    wire sample_tick = (tick_counter == TICK_COUNT - 1);
    always @(posedge clk) begin
        if (reset)
            tick_counter <= 32'd0;
        else if (sample_tick)
            tick_counter <= 32'd0;
        else
            tick_counter <= tick_counter + 1'b1;
    end

    // --- Goertzel coefficient ROM: coeff_rom[k] = round(2*cos(2*pi*k/512) * 2^13),
    // for k = 1..256 (bin 0 / DC is never computed or displayed). Q2.13
    // signed fixed point - generated, not hand-typed, to rule out a
    // transcription error in 256 constants. ---
    reg signed [15:0] coeff_rom [1:256];
    initial begin
        coeff_rom[1] = 16'sd16383;
        coeff_rom[2] = 16'sd16379;
        coeff_rom[3] = 16'sd16373;
        coeff_rom[4] = 16'sd16364;
        coeff_rom[5] = 16'sd16353;
        coeff_rom[6] = 16'sd16340;
        coeff_rom[7] = 16'sd16324;
        coeff_rom[8] = 16'sd16305;
        coeff_rom[9] = 16'sd16284;
        coeff_rom[10] = 16'sd16261;
        coeff_rom[11] = 16'sd16235;
        coeff_rom[12] = 16'sd16207;
        coeff_rom[13] = 16'sd16176;
        coeff_rom[14] = 16'sd16143;
        coeff_rom[15] = 16'sd16107;
        coeff_rom[16] = 16'sd16069;
        coeff_rom[17] = 16'sd16029;
        coeff_rom[18] = 16'sd15986;
        coeff_rom[19] = 16'sd15941;
        coeff_rom[20] = 16'sd15893;
        coeff_rom[21] = 16'sd15843;
        coeff_rom[22] = 16'sd15791;
        coeff_rom[23] = 16'sd15736;
        coeff_rom[24] = 16'sd15679;
        coeff_rom[25] = 16'sd15619;
        coeff_rom[26] = 16'sd15557;
        coeff_rom[27] = 16'sd15493;
        coeff_rom[28] = 16'sd15426;
        coeff_rom[29] = 16'sd15357;
        coeff_rom[30] = 16'sd15286;
        coeff_rom[31] = 16'sd15213;
        coeff_rom[32] = 16'sd15137;
        coeff_rom[33] = 16'sd15059;
        coeff_rom[34] = 16'sd14978;
        coeff_rom[35] = 16'sd14896;
        coeff_rom[36] = 16'sd14811;
        coeff_rom[37] = 16'sd14724;
        coeff_rom[38] = 16'sd14635;
        coeff_rom[39] = 16'sd14543;
        coeff_rom[40] = 16'sd14449;
        coeff_rom[41] = 16'sd14354;
        coeff_rom[42] = 16'sd14256;
        coeff_rom[43] = 16'sd14155;
        coeff_rom[44] = 16'sd14053;
        coeff_rom[45] = 16'sd13949;
        coeff_rom[46] = 16'sd13842;
        coeff_rom[47] = 16'sd13733;
        coeff_rom[48] = 16'sd13623;
        coeff_rom[49] = 16'sd13510;
        coeff_rom[50] = 16'sd13395;
        coeff_rom[51] = 16'sd13279;
        coeff_rom[52] = 16'sd13160;
        coeff_rom[53] = 16'sd13039;
        coeff_rom[54] = 16'sd12916;
        coeff_rom[55] = 16'sd12792;
        coeff_rom[56] = 16'sd12665;
        coeff_rom[57] = 16'sd12537;
        coeff_rom[58] = 16'sd12406;
        coeff_rom[59] = 16'sd12274;
        coeff_rom[60] = 16'sd12140;
        coeff_rom[61] = 16'sd12004;
        coeff_rom[62] = 16'sd11866;
        coeff_rom[63] = 16'sd11727;
        coeff_rom[64] = 16'sd11585;
        coeff_rom[65] = 16'sd11442;
        coeff_rom[66] = 16'sd11297;
        coeff_rom[67] = 16'sd11151;
        coeff_rom[68] = 16'sd11003;
        coeff_rom[69] = 16'sd10853;
        coeff_rom[70] = 16'sd10702;
        coeff_rom[71] = 16'sd10549;
        coeff_rom[72] = 16'sd10394;
        coeff_rom[73] = 16'sd10238;
        coeff_rom[74] = 16'sd10080;
        coeff_rom[75] = 16'sd9921;
        coeff_rom[76] = 16'sd9760;
        coeff_rom[77] = 16'sd9598;
        coeff_rom[78] = 16'sd9434;
        coeff_rom[79] = 16'sd9269;
        coeff_rom[80] = 16'sd9102;
        coeff_rom[81] = 16'sd8935;
        coeff_rom[82] = 16'sd8765;
        coeff_rom[83] = 16'sd8595;
        coeff_rom[84] = 16'sd8423;
        coeff_rom[85] = 16'sd8250;
        coeff_rom[86] = 16'sd8076;
        coeff_rom[87] = 16'sd7900;
        coeff_rom[88] = 16'sd7723;
        coeff_rom[89] = 16'sd7545;
        coeff_rom[90] = 16'sd7366;
        coeff_rom[91] = 16'sd7186;
        coeff_rom[92] = 16'sd7005;
        coeff_rom[93] = 16'sd6823;
        coeff_rom[94] = 16'sd6639;
        coeff_rom[95] = 16'sd6455;
        coeff_rom[96] = 16'sd6270;
        coeff_rom[97] = 16'sd6084;
        coeff_rom[98] = 16'sd5897;
        coeff_rom[99] = 16'sd5708;
        coeff_rom[100] = 16'sd5520;
        coeff_rom[101] = 16'sd5330;
        coeff_rom[102] = 16'sd5139;
        coeff_rom[103] = 16'sd4948;
        coeff_rom[104] = 16'sd4756;
        coeff_rom[105] = 16'sd4563;
        coeff_rom[106] = 16'sd4370;
        coeff_rom[107] = 16'sd4176;
        coeff_rom[108] = 16'sd3981;
        coeff_rom[109] = 16'sd3786;
        coeff_rom[110] = 16'sd3590;
        coeff_rom[111] = 16'sd3393;
        coeff_rom[112] = 16'sd3196;
        coeff_rom[113] = 16'sd2999;
        coeff_rom[114] = 16'sd2801;
        coeff_rom[115] = 16'sd2603;
        coeff_rom[116] = 16'sd2404;
        coeff_rom[117] = 16'sd2205;
        coeff_rom[118] = 16'sd2006;
        coeff_rom[119] = 16'sd1806;
        coeff_rom[120] = 16'sd1606;
        coeff_rom[121] = 16'sd1406;
        coeff_rom[122] = 16'sd1205;
        coeff_rom[123] = 16'sd1005;
        coeff_rom[124] = 16'sd804;
        coeff_rom[125] = 16'sd603;
        coeff_rom[126] = 16'sd402;
        coeff_rom[127] = 16'sd201;
        coeff_rom[128] = 16'sd0;
        coeff_rom[129] = -16'sd201;
        coeff_rom[130] = -16'sd402;
        coeff_rom[131] = -16'sd603;
        coeff_rom[132] = -16'sd804;
        coeff_rom[133] = -16'sd1005;
        coeff_rom[134] = -16'sd1205;
        coeff_rom[135] = -16'sd1406;
        coeff_rom[136] = -16'sd1606;
        coeff_rom[137] = -16'sd1806;
        coeff_rom[138] = -16'sd2006;
        coeff_rom[139] = -16'sd2205;
        coeff_rom[140] = -16'sd2404;
        coeff_rom[141] = -16'sd2603;
        coeff_rom[142] = -16'sd2801;
        coeff_rom[143] = -16'sd2999;
        coeff_rom[144] = -16'sd3196;
        coeff_rom[145] = -16'sd3393;
        coeff_rom[146] = -16'sd3590;
        coeff_rom[147] = -16'sd3786;
        coeff_rom[148] = -16'sd3981;
        coeff_rom[149] = -16'sd4176;
        coeff_rom[150] = -16'sd4370;
        coeff_rom[151] = -16'sd4563;
        coeff_rom[152] = -16'sd4756;
        coeff_rom[153] = -16'sd4948;
        coeff_rom[154] = -16'sd5139;
        coeff_rom[155] = -16'sd5330;
        coeff_rom[156] = -16'sd5520;
        coeff_rom[157] = -16'sd5708;
        coeff_rom[158] = -16'sd5897;
        coeff_rom[159] = -16'sd6084;
        coeff_rom[160] = -16'sd6270;
        coeff_rom[161] = -16'sd6455;
        coeff_rom[162] = -16'sd6639;
        coeff_rom[163] = -16'sd6823;
        coeff_rom[164] = -16'sd7005;
        coeff_rom[165] = -16'sd7186;
        coeff_rom[166] = -16'sd7366;
        coeff_rom[167] = -16'sd7545;
        coeff_rom[168] = -16'sd7723;
        coeff_rom[169] = -16'sd7900;
        coeff_rom[170] = -16'sd8076;
        coeff_rom[171] = -16'sd8250;
        coeff_rom[172] = -16'sd8423;
        coeff_rom[173] = -16'sd8595;
        coeff_rom[174] = -16'sd8765;
        coeff_rom[175] = -16'sd8935;
        coeff_rom[176] = -16'sd9102;
        coeff_rom[177] = -16'sd9269;
        coeff_rom[178] = -16'sd9434;
        coeff_rom[179] = -16'sd9598;
        coeff_rom[180] = -16'sd9760;
        coeff_rom[181] = -16'sd9921;
        coeff_rom[182] = -16'sd10080;
        coeff_rom[183] = -16'sd10238;
        coeff_rom[184] = -16'sd10394;
        coeff_rom[185] = -16'sd10549;
        coeff_rom[186] = -16'sd10702;
        coeff_rom[187] = -16'sd10853;
        coeff_rom[188] = -16'sd11003;
        coeff_rom[189] = -16'sd11151;
        coeff_rom[190] = -16'sd11297;
        coeff_rom[191] = -16'sd11442;
        coeff_rom[192] = -16'sd11585;
        coeff_rom[193] = -16'sd11727;
        coeff_rom[194] = -16'sd11866;
        coeff_rom[195] = -16'sd12004;
        coeff_rom[196] = -16'sd12140;
        coeff_rom[197] = -16'sd12274;
        coeff_rom[198] = -16'sd12406;
        coeff_rom[199] = -16'sd12537;
        coeff_rom[200] = -16'sd12665;
        coeff_rom[201] = -16'sd12792;
        coeff_rom[202] = -16'sd12916;
        coeff_rom[203] = -16'sd13039;
        coeff_rom[204] = -16'sd13160;
        coeff_rom[205] = -16'sd13279;
        coeff_rom[206] = -16'sd13395;
        coeff_rom[207] = -16'sd13510;
        coeff_rom[208] = -16'sd13623;
        coeff_rom[209] = -16'sd13733;
        coeff_rom[210] = -16'sd13842;
        coeff_rom[211] = -16'sd13949;
        coeff_rom[212] = -16'sd14053;
        coeff_rom[213] = -16'sd14155;
        coeff_rom[214] = -16'sd14256;
        coeff_rom[215] = -16'sd14354;
        coeff_rom[216] = -16'sd14449;
        coeff_rom[217] = -16'sd14543;
        coeff_rom[218] = -16'sd14635;
        coeff_rom[219] = -16'sd14724;
        coeff_rom[220] = -16'sd14811;
        coeff_rom[221] = -16'sd14896;
        coeff_rom[222] = -16'sd14978;
        coeff_rom[223] = -16'sd15059;
        coeff_rom[224] = -16'sd15137;
        coeff_rom[225] = -16'sd15213;
        coeff_rom[226] = -16'sd15286;
        coeff_rom[227] = -16'sd15357;
        coeff_rom[228] = -16'sd15426;
        coeff_rom[229] = -16'sd15493;
        coeff_rom[230] = -16'sd15557;
        coeff_rom[231] = -16'sd15619;
        coeff_rom[232] = -16'sd15679;
        coeff_rom[233] = -16'sd15736;
        coeff_rom[234] = -16'sd15791;
        coeff_rom[235] = -16'sd15843;
        coeff_rom[236] = -16'sd15893;
        coeff_rom[237] = -16'sd15941;
        coeff_rom[238] = -16'sd15986;
        coeff_rom[239] = -16'sd16029;
        coeff_rom[240] = -16'sd16069;
        coeff_rom[241] = -16'sd16107;
        coeff_rom[242] = -16'sd16143;
        coeff_rom[243] = -16'sd16176;
        coeff_rom[244] = -16'sd16207;
        coeff_rom[245] = -16'sd16235;
        coeff_rom[246] = -16'sd16261;
        coeff_rom[247] = -16'sd16284;
        coeff_rom[248] = -16'sd16305;
        coeff_rom[249] = -16'sd16324;
        coeff_rom[250] = -16'sd16340;
        coeff_rom[251] = -16'sd16353;
        coeff_rom[252] = -16'sd16364;
        coeff_rom[253] = -16'sd16373;
        coeff_rom[254] = -16'sd16379;
        coeff_rom[255] = -16'sd16383;
        coeff_rom[256] = -16'sd16384;
    end

    // --- Ping-pong sample collection: one buffer fills from `level`
    // while the other is (or is about to be) read by the compute
    // sweep, so incoming samples never disturb a computation in
    // progress. ---
    reg [11:0] sample_buf0 [0:FFT_SIZE-1];
    reg [11:0] sample_buf1 [0:FFT_SIZE-1];
    reg [8:0]  wr_ptr;
    reg        fill_sel;         // which buffer is currently being written
    reg        compute_buf_sel;  // which buffer the compute sweep should read
    reg        compute_pending;  // a freshly-filled buffer is waiting to be swept

    always @(posedge clk) begin
        if (reset) begin
            wr_ptr          <= 9'd0;
            fill_sel        <= 1'b0;
            compute_buf_sel <= 1'b0;
            compute_pending <= 1'b0;
        end else begin
            if (sample_tick) begin
                if (fill_sel == 1'b0)
                    sample_buf0[wr_ptr] <= level_sync1;
                else
                    sample_buf1[wr_ptr] <= level_sync1;

                if (wr_ptr == FFT_SIZE-1) begin
                    wr_ptr          <= 9'd0;
                    fill_sel        <= ~fill_sel;
                    compute_buf_sel <= fill_sel;   // the buffer just finished
                    compute_pending <= 1'b1;
                end else begin
                    wr_ptr <= wr_ptr + 1'b1;
                end
            end else if (fsm_state == CS_IDLE && compute_pending) begin
                compute_pending <= 1'b0;           // FSM is latching it this cycle
            end
        end
    end

    // --- Goertzel sweep FSM ---
    localparam CS_IDLE  = 3'd0;
    localparam CS_RUN   = 3'd1;
    localparam CS_FIN_A = 3'd2;
    localparam CS_FIN_B = 3'd3;
    localparam CS_FIN_C = 3'd4;

    reg [2:0]        fsm_state;
    reg [8:0]        bin_idx;      // 1..256
    reg [8:0]        sample_idx;   // 0..511
    reg signed [31:0] s1, s2;      // Goertzel state: s[n-1], s[n-2]
    reg signed [15:0] coeff;       // coeff_rom[bin_idx], latched for the sweep

    reg signed [63:0] s1sq_r, s2sq_r, cs1_r, cross_r;
    reg               fft_done_pulse;

    wire signed [31:0] x_cur_s = {20'd0, (compute_buf_sel ? sample_buf1[sample_idx]
                                                            : sample_buf0[sample_idx])};

    wire signed [47:0] cs1_full = coeff * s1;               // Q2.13 * s1
    wire signed [31:0] cs1      = cs1_full[44:13];           // >>>13, back to integer scale

    wire signed [31:0] s0_next = x_cur_s + cs1 - s2;

    always @(posedge clk) begin
        fft_done_pulse <= 1'b0;

        if (reset) begin
            fsm_state  <= CS_IDLE;
            bin_idx    <= 9'd1;
            sample_idx <= 9'd0;
            s1         <= 32'sd0;
            s2         <= 32'sd0;
            coeff      <= 16'sd0;
        end else begin
            case (fsm_state)
                CS_IDLE: begin
                    if (compute_pending) begin
                        bin_idx    <= 9'd1;
                        sample_idx <= 9'd0;
                        s1         <= 32'sd0;
                        s2         <= 32'sd0;
                        coeff      <= coeff_rom[1];
                        fsm_state  <= CS_RUN;
                    end
                end

                CS_RUN: begin
                    s2 <= s1;
                    s1 <= s0_next;
                    if (sample_idx == FFT_SIZE-1)
                        fsm_state <= CS_FIN_A;
                    else
                        sample_idx <= sample_idx + 1'b1;
                end

                // Spread the power computation over 3 cycles (a few
                // independent multiplies each) instead of one long
                // combinational chain - there's no timing pressure
                // here, only a strong preference to not find out the
                // hard way that 3 chained multiplies don't close
                // timing at 65MHz.
                CS_FIN_A: begin
                    s1sq_r    <= s1 * s1;
                    s2sq_r    <= s2 * s2;
                    cs1_r     <= cs1;          // stash coeff*s1 (>>>13); multiplied by s2 next cycle
                    fsm_state <= CS_FIN_B;
                end

                CS_FIN_B: begin
                    cross_r   <= cs1_r * s2;
                    fsm_state <= CS_FIN_C;
                end

                CS_FIN_C: begin
                    if (bin_idx == NUM_BINS) begin
                        fft_done_pulse <= 1'b1;
                        fsm_state      <= CS_IDLE;
                    end else begin
                        bin_idx    <= bin_idx + 1'b1;
                        sample_idx <= 9'd0;
                        s1         <= 32'sd0;
                        s2         <= 32'sd0;
                        coeff      <= coeff_rom[bin_idx + 1'b1];
                        fsm_state  <= CS_RUN;
                    end
                end

                default: fsm_state <= CS_IDLE;
            endcase
        end
    end

    // power = s1^2 + s2^2 - (coeff*s1>>>13)*s2, computed in CS_FIN_C
    // from the registers FIN_A/FIN_B built up.
    wire signed [63:0] power_signed = s1sq_r + s2sq_r - cross_r;
    wire [47:0] power_u = power_signed[63] ? 48'd0 : power_signed[47:0];

    // Approximate log2: position of the highest set bit (0-47), plus
    // 3 fractional bits from just below it for smoother bar steps
    // instead of jumps only at power-of-two boundaries. Range 0..383.
    function [8:0] log2_approx;
        input [47:0] val;
        integer i;
        reg [5:0] msb;
        reg [2:0] frac;
        begin
            msb = 6'd0;
            for (i = 0; i < 48; i = i + 1)
                if (val[i])
                    msb = i[5:0];
            if (msb >= 3)
                frac = val[msb-1 -: 3];
            else
                frac = 3'd0;
            log2_approx = {msb, frac};
        end
    endfunction

    wire [8:0] log2_val   = log2_approx(power_u);
    wire [8:0] height_raw = (log2_val > FLOOR) ? (log2_val - FLOOR) : 9'd0;
    wire [10:0] height_scaled = height_raw * SCALE;
    wire [8:0] bin_height = (height_scaled > (HEIGHT-1)) ? (HEIGHT-1) : height_scaled[8:0];

    // --- Bar height storage: ping-pong, swapped at a frame boundary
    // (same discipline as waveform_view's trace buffers) ---
    reg [8:0] height_buf0 [0:NUM_BINS-1];
    reg [8:0] height_buf1 [0:NUM_BINS-1];
    reg       front_sel;
    reg       swap_pending;

    wire is_frame_start = (pixel_x == 11'd0) && (pixel_y == 10'd0);

    always @(posedge clk) begin
        if (reset) begin
            front_sel    <= 1'b0;
            swap_pending <= 1'b0;
        end else begin
            if (fsm_state == CS_FIN_C && bin_idx == NUM_BINS)
                swap_pending <= 1'b1;
            if (is_frame_start && swap_pending) begin
                front_sel    <= ~front_sel;
                swap_pending <= 1'b0;
            end
        end
    end

    always @(posedge clk) begin
        if (fsm_state == CS_FIN_C) begin
            if (!front_sel)
                height_buf1[bin_idx - 1'b1] <= bin_height;   // write into the back buffer
            else
                height_buf0[bin_idx - 1'b1] <= bin_height;
        end
    end

    // --- Bar rendering ---
    wire [10:0] local_x = pixel_x - X_OFFSET;
    wire [9:0]  local_y = pixel_y - Y_OFFSET;
    wire in_region = video_on &&
                     (pixel_x >= X_OFFSET) && (pixel_x < X_OFFSET + NUM_BINS*BIN_PITCH) &&
                     (pixel_y >= Y_OFFSET) && (pixel_y < Y_OFFSET + HEIGHT);

    wire [8:0] bin_index    = local_x[10:2];   // /BIN_PITCH (=4), a plain bit-slice
    wire [1:0] pos_in_pitch = local_x[1:0];    // %BIN_PITCH
    wire       in_bar_col   = (pos_in_pitch < BIN_WIDTH);

    wire [8:0] bar_h = front_sel ? height_buf1[bin_index] : height_buf0[bin_index];

    assign pixel_on = in_region && in_bar_col &&
                      (local_y >= (HEIGHT - bar_h)) && (local_y < HEIGHT);

    assign axis_on = in_region && (local_y == HEIGHT-1);

    // Cutoff markers: full-height vertical lines at the bar column for
    // the given bin - drawn with priority over the bar itself at the
    // top level (see top.v), so they stay visible regardless of that
    // bin's current height.
    assign lp_cutoff_on = in_region && in_bar_col && (bin_index == lp_cutoff_bin);
    assign hp_cutoff_on = in_region && in_bar_col && (bin_index == hp_cutoff_bin);

endmodule
