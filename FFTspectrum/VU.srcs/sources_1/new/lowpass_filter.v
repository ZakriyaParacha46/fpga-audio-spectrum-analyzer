`timescale 1ns / 1ps
//
// lowpass_filter: simple single-pole IIR (exponential moving average)
// noise filter on the raw ADC level. Runs directly in the ADC's own
// clock domain (clk_100), updated once per real conversion
// (level_valid) - NOT tied to any display sample-rate tick, so it
// filters the actual signal rather than an already-decimated copy of
// it that a waveform_view instance would otherwise see.
//
//   acc[n] = acc[n-1] + (level[n] - acc[n-1]) >>> SHIFT
//
// This is a plain integer shift, not a fixed-point accumulator, so
// once acc gets within +-(2^SHIFT - 1) of level the step truncates to
// 0 and acc stops moving - a few-LSB steady-state deadband. That's
// invisible after waveform_view's own >>SHIFT scale-to-height mapping,
// so it isn't worth spending extra fixed-point bits on here.
//
// Bigger shift = more smoothing (lower cutoff), at the cost of a
// slower step response. Tune by eye against the raw trace next to it.
//
// `shift` is a runtime input (not a compile-time parameter) so it can
// be adjusted live from the board's buttons - see top.v's shift
// control logic and fft_view.v's matching cutoff-bin lookup.
//
module lowpass_filter (
    input  wire        clk,
    input  wire        reset,
    input  wire [11:0] level,
    input  wire        level_valid,
    input  wire [3:0]  shift,
    output wire [11:0] level_filtered
);

    reg signed [12:0] acc;   // holds 0-4095 as a positive 13-bit signed value

    wire signed [12:0] level_s = {1'b0, level};
    wire signed [12:0] diff    = level_s - acc;
    wire signed [12:0] step    = diff >>> shift;   // arithmetic shift keeps the sign
    wire signed [12:0] next    = acc + step;

    always @(posedge clk) begin
        if (reset)
            acc <= 13'sd0;
        else if (level_valid)
            acc <= next;
    end

    assign level_filtered = acc[11:0];

endmodule
