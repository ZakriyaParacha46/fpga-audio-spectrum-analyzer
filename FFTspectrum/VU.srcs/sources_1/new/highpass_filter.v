`timescale 1ns / 1ps
//
// highpass_filter: complementary-filter high-pass, built from the same
// single-pole EMA as lowpass_filter.v rather than a new filter
// structure - a highpass is just "the input minus its own smoothed
// average" (input = lowpass(input) + highpass(input), exactly, by
// construction), so reusing the already-verified EMA recurrence here
// is lower-risk than introducing a different two-history-term filter
// equation blind.
//
//   ema[n]   = ema[n-1] + (level[n] - ema[n-1]) >>> SHIFT   (internal lowpass)
//   highpass = level[n] - ema[n]                             (everything else)
//
// highpass is naturally centered on 0 (it's an AC-only signal), which
// doesn't fit the 0-4095 unsigned convention every view in this
// project expects - so it's re-biased back onto the real hardware
// baseline (tracked adaptively - see BIAS_SHIFT below, not a hardcoded
// guess like the old BASELINE constant was) and clamped into 0-4095
// before being exposed.
//
// Runs in the same clock domain and on the same level_valid pulse as
// lowpass_filter, so it can be chained directly onto lowpass_filter's
// output with no extra synchronization needed.
//
// `shift` is a runtime input (not a compile-time parameter) so it can
// be adjusted live from the board's buttons - see top.v's shift
// control logic and fft_view.v's matching cutoff-bin lookup.
//
module highpass_filter (
    input  wire        clk,
    input  wire        reset,
    input  wire [11:0] level,
    input  wire        level_valid,
    input  wire [3:0]  shift,
    output wire [11:0] level_highpassed
);

    reg signed [12:0] ema;   // holds 0-4095 as a positive 13-bit signed value

    wire signed [12:0] level_s  = {1'b0, level};
    wire signed [12:0] diff     = level_s - ema;
    wire signed [12:0] step     = diff >>> shift;
    wire signed [12:0] ema_next = ema + step;

    always @(posedge clk) begin
        if (reset)
            ema <= 13'sd0;
        else if (level_valid)
            ema <= ema_next;
    end

    // AC-only content needs SOME bias added back to display on this
    // project's unsigned, 0=quiet convention - a fixed +2048 was
    // wrong (real rest point isn't mid-scale, so the trace never
    // matched raw and never settled to 0 when grounded). Re-biasing
    // by adding back `level` or `ema` themselves is a dead end: it
    // either exactly cancels back to the unfiltered input (algebraic
    // tautology) or leaves sub-cutoff content unattenuated (a shelf
    // filter, not a highpass). So: a SEPARATE, much slower tracker,
    // decoupled from `shift`, dedicated only to this re-bias - always
    // slower than the highpass itself (BIAS_SHIFT > any live `shift`
    // value top.v allows), so it only ever captures the true
    // long-term baseline, never the midband content being displayed.
    localparam integer BIAS_SHIFT = 12;
    reg signed [12:0] bias_ema;
    wire signed [12:0] bias_diff = level_s - bias_ema;
    wire signed [12:0] bias_step = bias_diff >>> BIAS_SHIFT;

    always @(posedge clk) begin
        if (reset)
            bias_ema <= 13'sd0;
        else if (level_valid)
            bias_ema <= bias_ema + bias_step;
    end

    wire signed [13:0] hp_biased = {level_s[12], level_s} - {ema[12], ema} + {bias_ema[12], bias_ema};

    assign level_highpassed = (hp_biased < 0)    ? 12'd0    :
                              (hp_biased > 4095) ? 12'd4095 :
                                                   hp_biased[11:0];

endmodule
