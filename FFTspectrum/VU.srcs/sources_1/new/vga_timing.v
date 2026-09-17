`timescale 1ns / 1ps
//
// vga_timing: 1024x768 @ 60Hz VGA sync generator (VESA DMT standard).
// Assumes the input clock IS the exact 65MHz pixel clock (from a
// Clocking Wizard MMCM) - no internal division needed, unlike the
// earlier 640x480 version which divided 100MHz by 4 to approximate
// 25MHz. Every clock edge here is one pixel.
//
module vga_timing (
    input  wire        clk,        // exact 65MHz pixel clock
    input  wire        reset,
    output wire        hsync,
    output wire        vsync,
    output wire [10:0] pixel_x,    // 0-1023, valid when video_on
    output wire [9:0]  pixel_y,    // 0-767, valid when video_on
    output wire        video_on
);

    // 1024x768 @ 60Hz, VESA DMT standard timing, 65MHz pixel clock
    localparam H_DISPLAY = 1024;
    localparam H_FRONT   = 24;
    localparam H_SYNC    = 136;
    localparam H_BACK    = 160;
    localparam H_TOTAL   = H_DISPLAY + H_FRONT + H_SYNC + H_BACK; // 1344

    localparam V_DISPLAY = 768;
    localparam V_FRONT   = 3;
    localparam V_SYNC    = 6;
    localparam V_BACK    = 29;
    localparam V_TOTAL   = V_DISPLAY + V_FRONT + V_SYNC + V_BACK; // 806

    reg [10:0] h_count;
    reg [9:0]  v_count;

    always @(posedge clk) begin
        if (reset) begin
            h_count <= 11'd0;
            v_count <= 10'd0;
        end else begin
            if (h_count == H_TOTAL - 1) begin
                h_count <= 11'd0;
                v_count <= (v_count == V_TOTAL - 1) ? 10'd0 : v_count + 1'b1;
            end else begin
                h_count <= h_count + 1'b1;
            end
        end
    end

    // Both sync pulses are active-low (negative polarity) for this timing
    assign hsync = ~((h_count >= H_DISPLAY + H_FRONT) &&
                      (h_count <  H_DISPLAY + H_FRONT + H_SYNC));
    assign vsync = ~((v_count >= V_DISPLAY + V_FRONT) &&
                      (v_count <  V_DISPLAY + V_FRONT + V_SYNC));

    assign video_on = (h_count < H_DISPLAY) && (v_count < V_DISPLAY);
    assign pixel_x  = h_count;
    assign pixel_y  = v_count;

endmodule