`timescale 1ns / 1ps
//
// audio_driver: wraps the Basys3 XADC and exposes a clean digital reading.
// Knows nothing about LEDs/VGA/FFT - just "here's the current audio level".
//
module audio_driver #(
    parameter [6:0] XADC_CHANNEL_ADDR = 7'h16   // VAUX6 (JXADC pin 1/7)
) (
    input  wire        clk,          // 100 MHz onboard clock
    input  wire        reset,        // active-high
    input  wire        vauxp6,       // JXADC pin 1 (signal, via divider)
    input  wire        vauxn6,       // JXADC pin 7 (tied to GND)

    output reg  [11:0] level,        // latest sample, 0-4095
    output reg         level_valid   // 1-cycle pulse when `level` updates
);

    wire        eoc;      // end-of-conversion
    wire        drdy;     // data-ready
    wire [15:0] do_out;   // raw XADC data word

    // Generated via Vivado IP Catalog: XADC Wizard,
    // Single Channel / Continuous Mode, Unipolar, Channel = VAUX6, DCLK = 50MHz.
    // If Vivado names the ports slightly differently for your generated
    // core, just match them up here.
    xadc_wiz_0 xadc_inst (
        .di_in       (16'b0),
        .daddr_in    (XADC_CHANNEL_ADDR),
        .den_in      (eoc),          // request next conversion as soon as one finishes
        .dwe_in      (1'b0),
        .drdy_out    (drdy),
        .do_out      (do_out),
        .dclk_in     (clk),
        .reset_in    (reset),
        .vp_in       (1'b0),         // dedicated Vp/Vn pins unused - tied off
        .vn_in       (1'b0),
        .vauxp6      (vauxp6),
        .vauxn6      (vauxn6),
        .channel_out (),
        .eoc_out     (eoc),
        .alarm_out   (),
        .eos_out     (),
        .busy_out    ()
    );

    always @(posedge clk) begin
        if (reset) begin
            level       <= 12'd0;
            level_valid <= 1'b0;
        end else begin
            level_valid <= drdy;
            if (drdy)
                level <= do_out[15:4];   // top 12 bits are the actual sample
        end
    end

endmodule