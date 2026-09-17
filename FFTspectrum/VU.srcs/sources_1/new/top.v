`timescale 1ns / 1ps
//
// top: audio_driver (100MHz domain, unchanged/working) -> a
// 1024x768@60Hz display, split into three regions:
//   top-left  (x 0-511,    y 0-383): raw waveform
//   top-right (x 512-1023, y 0-383): band-passed signal - lowpass_filter
//                                     then highpass_filter in series,
//                                     side by side with the raw trace
//   bottom    (x 0-1023,   y 384-767): 256-bin magnitude spectrum of
//                                     that same band-passed signal
//                                     (fft_view, hand-written Goertzel
//                                     bank - see fft_view.v), with a
//                                     blue vertical line marking the
//                                     lowpass cutoff and a purple line
//                                     marking the highpass cutoff
//
// Both filters' cutoffs are live-adjustable from the board:
//   sw0 = 0: btnL/btnR step the LOWPASS  cutoff down/up
//   sw0 = 1: btnL/btnR step the HIGHPASS cutoff down/up
// The blue/purple FFT markers track whichever cutoff is being moved,
// in real time (see fft_view.v's shift_to_bin lookup).
//
module top (
    input  wire        clk,        // 100 MHz onboard clock
    input  wire        reset,      // active-high, e.g. btnC
    input  wire        vauxp6,
    input  wire        vauxn6,
    input  wire        sw0,        // 0 = adjust lowpass, 1 = adjust highpass
    input  wire        btnL,       // step selected filter's cutoff down
    input  wire        btnR,       // step selected filter's cutoff up
    output wire        Hsync,
    output wire        Vsync,
    output wire [3:0]  vgaRed,
    output wire [3:0]  vgaGreen,
    output wire [3:0]  vgaBlue
);

    // --- Clocking Wizard: 65MHz for VGA, buffered 100MHz for audio ---
    wire clk_100;
    wire vga_clk;
    wire vga_clk_locked;

    clk_wiz_0 clk_wiz_inst (
        .clk_in1  (clk),
        .clk_out1 (vga_clk),
        .clk_out2 (clk_100),
        .reset    (reset),
        .locked   (vga_clk_locked)
    );

    wire vga_reset = reset || !vga_clk_locked;

    // --- Audio input (100MHz domain, unchanged/working) ---
    wire [11:0] level;
    wire        level_valid;

    audio_driver audio_inst (
        .clk         (clk_100),
        .reset       (reset),
        .vauxp6      (vauxp6),
        .vauxn6      (vauxn6),
        .level       (level),
        .level_valid (level_valid)
    );

    // --- VGA timing (1024x768@60Hz, exact 65MHz pixel clock) ---
    wire        vga_hsync, vga_vsync, vga_video_on;
    wire [10:0] vga_x;
    wire [9:0]  vga_y;

    vga_timing vga_timing_inst (
        .clk      (vga_clk),
        .reset    (vga_reset),
        .hsync    (vga_hsync),
        .vsync    (vga_vsync),
        .pixel_x  (vga_x),
        .pixel_y  (vga_y),
        .video_on (vga_video_on)
    );

    // --- Filter cutoff shift control: sw0 picks which filter btnL/btnR
    // steps, both clamped to the range fft_view.v's shift_to_bin table
    // covers (MUST match its MIN_SHIFT/MAX_SHIFT). Debounced in the
    // same clk_100 domain the filters themselves live in, so lp_shift/
    // hp_shift feed straight into them with no extra synchronization. ---
    localparam integer MIN_SHIFT = 3;   // must match fft_view.v's MIN_SHIFT
    localparam integer MAX_SHIFT = 11;  // must match fft_view.v's MAX_SHIFT

    wire btnL_pulse, btnR_pulse;

    debounce #(.CLK_FREQ(100_000_000)) debounce_L (
        .clk         (clk_100),
        .reset       (reset),
        .btn_raw     (btnL),
        .press_pulse (btnL_pulse)
    );

    debounce #(.CLK_FREQ(100_000_000)) debounce_R (
        .clk         (clk_100),
        .reset       (reset),
        .btn_raw     (btnR),
        .press_pulse (btnR_pulse)
    );

    reg [3:0] lp_shift, hp_shift;
    always @(posedge clk_100) begin
        if (reset) begin
            lp_shift <= 4'd5;   // starting points match the old fixed defaults
            hp_shift <= 4'd9;
        end else begin
            if (btnL_pulse) begin
                if (!sw0 && lp_shift > MIN_SHIFT) lp_shift <= lp_shift - 1'b1;
                if ( sw0 && hp_shift > MIN_SHIFT) hp_shift <= hp_shift - 1'b1;
            end
            if (btnR_pulse) begin
                if (!sw0 && lp_shift < MAX_SHIFT) lp_shift <= lp_shift + 1'b1;
                if ( sw0 && hp_shift < MAX_SHIFT) hp_shift <= hp_shift + 1'b1;
            end
        end
    end

    // Cross lp_shift/hp_shift into the vga_clk domain for fft_view's
    // cutoff markers. Plain 2-FF sync of a multi-bit bus: a value that
    // changes by +-1 can flip more than one bit at once (e.g. 3->4),
    // so a glitched intermediate value could in principle be sampled
    // for one frame - the same accepted tradeoff as the original
    // `level` CDC elsewhere in this project. Consequence here is just
    // a reference line briefly settling one frame later, not lost or
    // corrupted audio data, so it isn't worth a slower Gray-coded
    // handoff for values that only change a few times a second.
    reg [3:0] lp_shift_sync0, lp_shift_sync1;
    reg [3:0] hp_shift_sync0, hp_shift_sync1;
    always @(posedge vga_clk) begin
        lp_shift_sync0 <= lp_shift;
        lp_shift_sync1 <= lp_shift_sync0;
        hp_shift_sync0 <= hp_shift;
        hp_shift_sync1 <= hp_shift_sync0;
    end

    // --- Lowpass-filtered copy of the audio signal, filtered in the
    // ADC's own clk_100 domain at the real sample rate (see
    // lowpass_filter.v for why it isn't done downstream instead) ---
    wire [11:0] level_filtered;

    lowpass_filter lowpass_inst (
        .clk            (clk_100),
        .reset          (reset),
        .level          (level),
        .level_valid    (level_valid),
        .shift          (lp_shift),
        .level_filtered (level_filtered)
    );

    // --- High-pass, chained after the low-pass (same clk_100 domain,
    // same level_valid pulse - level_filtered already updates on it,
    // so no extra synchronization is needed to chain straight onto
    // it). Low-pass then high-pass in series = band-pass. ---
    wire [11:0] level_bandpassed;

    highpass_filter highpass_inst (
        .clk               (clk_100),
        .reset             (reset),
        .level             (level_filtered),
        .level_valid       (level_valid),
        .shift             (hp_shift),
        .level_highpassed  (level_bandpassed)
    );

    // --- Raw waveform view: TOP-LEFT (x 0-511, y 0-383), with axis lines ---
    wire trace_pixel_on_raw, trace_axis_on_raw;

    waveform_view #(
        .CLK_FREQ    (65_000_000),
        .SAMPLE_RATE (48_000),
        .WIDTH       (512),
        .HEIGHT      (384),
        .X_OFFSET    (0),
        .Y_OFFSET    (0)
    ) waveform_raw_inst (
        .clk        (vga_clk),
        .reset      (vga_reset),
        .level      (level),
        .pixel_x    (vga_x),
        .pixel_y    (vga_y),
        .video_on   (vga_video_on),
        .pixel_on   (trace_pixel_on_raw),
        .axis_on    (trace_axis_on_raw)
    );

    // --- Filtered waveform view: TOP-RIGHT (x 512-1023, y 0-383) ---
    wire trace_pixel_on_filt, trace_axis_on_filt;

    waveform_view #(
        .CLK_FREQ    (65_000_000),
        .SAMPLE_RATE (48_000),
        .WIDTH       (512),
        .HEIGHT      (384),
        .X_OFFSET    (512),
        .Y_OFFSET    (0)
    ) waveform_filt_inst (
        .clk        (vga_clk),
        .reset      (vga_reset),
        .level      (level_bandpassed),
        .pixel_x    (vga_x),
        .pixel_y    (vga_y),
        .video_on   (vga_video_on),
        .pixel_on   (trace_pixel_on_filt),
        .axis_on    (trace_axis_on_filt)
    );

    // --- FFT view: BOTTOM HALF (x 0-1023, y 384-767), on the band-passed signal ---
    wire trace_pixel_on_fft, trace_axis_on_fft, lp_cutoff_on_fft, hp_cutoff_on_fft;

    fft_view #(
        .CLK_FREQ    (65_000_000),
        .SAMPLE_RATE (48_000),
        .HEIGHT      (384),
        .X_OFFSET    (0),
        .Y_OFFSET    (384)
    ) fft_inst (
        .clk          (vga_clk),
        .reset        (vga_reset),
        .level        (level_bandpassed),
        .pixel_x      (vga_x),
        .pixel_y      (vga_y),
        .video_on     (vga_video_on),
        .lp_shift     (lp_shift_sync1),
        .hp_shift     (hp_shift_sync1),
        .pixel_on     (trace_pixel_on_fft),
        .axis_on      (trace_axis_on_fft),
        .lp_cutoff_on (lp_cutoff_on_fft),
        .hp_cutoff_on (hp_cutoff_on_fft)
    );

    // All three views' regions are disjoint (top-left / top-right /
    // bottom), so a plain OR is safe - exactly one of them (or none)
    // is active for any given pixel. Only fft_view produces cutoff
    // markers, so those pass through directly.
    wire trace_pixel_on = trace_pixel_on_raw | trace_pixel_on_filt | trace_pixel_on_fft;
    wire trace_axis_on  = trace_axis_on_raw  | trace_axis_on_filt  | trace_axis_on_fft;

    reg [3:0] vga_r, vga_g, vga_b;
    always @(posedge vga_clk) begin
        if (lp_cutoff_on_fft)
            {vga_r, vga_g, vga_b} <= 12'h00F; // blue: lowpass cutoff marker
        else if (hp_cutoff_on_fft)
            {vga_r, vga_g, vga_b} <= 12'hF0F; // purple: highpass cutoff marker
        else if (trace_pixel_on)
            {vga_r, vga_g, vga_b} <= 12'h0F0; // green trace/bars
        else if (trace_axis_on)
            {vga_r, vga_g, vga_b} <= 12'hF00; // red axis lines
        else
            {vga_r, vga_g, vga_b} <= 12'h000; // black background
    end

    assign vgaRed   = vga_r;
    assign vgaGreen = vga_g;
    assign vgaBlue  = vga_b;

    assign Hsync = vga_hsync;
    assign Vsync = vga_vsync;

endmodule