`timescale 1ns / 1ps
//
// waveform_view: positionable scrolling trace view of the RAW ADC
// level directly (no centering, no baseline math) - the last
// confirmed-working configuration.
//
module waveform_view #(
    parameter integer CLK_FREQ    = 65_000_000,
    parameter integer SAMPLE_RATE = 48_000,
    parameter integer WIDTH       = 1024,
    parameter integer HEIGHT      = 768,
    parameter integer X_OFFSET    = 0,
    parameter integer Y_OFFSET    = 0
) (
    input  wire         clk,
    input  wire         reset,
    input  wire [11:0]  level,
    input  wire [10:0]  pixel_x,
    input  wire [9:0]   pixel_y,
    input  wire         video_on,
    output wire         pixel_on,
    output wire         axis_on   // X-axis (vertical center) + Y-axis (left edge)
);

    // --- Synchronize 'level' into this clock domain ---
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

    // Map raw level (0-4095) to a LOCAL Y coordinate within this view
    // (0=top of view, HEIGHT-1=bottom). The >>2 in the original
    // full-screen (HEIGHT=768) confirmed-working version deliberately
    // maps only ADC codes 0-3068 across the full height and clips
    // above that, reserving the top ~25% of the ADC range as headroom
    // - that ratio is what actually made it "look good, centered".
    // SHIFT re-derives that same ratio for whatever HEIGHT this view
    // is instantiated with, so shrinking the view (e.g. to a top-half
    // display) can't silently blow the headroom the way a fixed >>2
    // did the last two times HEIGHT changed. Only exact power-of-two
    // subdivisions of BASE_HEIGHT keep this ratio exactly - fine for
    // full/half/quarter splits, which is all this project needs.
    localparam integer BASE_HEIGHT = 768;
    localparam integer BASE_SHIFT  = 2;
    localparam integer SHIFT       = BASE_SHIFT + $clog2(BASE_HEIGHT / HEIGHT);

    localparam [9:0] MAX_Y = HEIGHT - 1;
    wire [9:0] level_scaled = level_sync1[11:SHIFT];
    wire [9:0] y_clamped    = (level_scaled > MAX_Y) ? MAX_Y : level_scaled;
    wire [9:0] y_value      = MAX_Y - y_clamped;

    // --- Double-buffered storage ---
    reg [9:0] buf0 [0:WIDTH-1];
    reg [9:0] buf1 [0:WIDTH-1];
    reg [9:0] wr_ptr0, wr_ptr1;
    reg       front_sel;
    reg [9:0] front_wr_ptr;
    reg       swap_pending;

    wire in_region = (pixel_x >= X_OFFSET) && (pixel_x < X_OFFSET + WIDTH) &&
                     (pixel_y >= Y_OFFSET) && (pixel_y < Y_OFFSET + HEIGHT);
    wire is_frame_start = (pixel_x == 11'd0) && (pixel_y == 10'd0);

    wire back_buffer_wrapped =
        sample_tick && (front_sel == 1'b0) ? (wr_ptr1 == WIDTH-1) :
        sample_tick && (front_sel == 1'b1) ? (wr_ptr0 == WIDTH-1) : 1'b0;

    always @(posedge clk) begin
        if (reset) begin
            wr_ptr0      <= 10'd0;
            wr_ptr1      <= 10'd0;
            front_sel    <= 1'b0;
            front_wr_ptr <= 10'd0;
            swap_pending <= 1'b0;
        end else begin
            if (back_buffer_wrapped)
                swap_pending <= 1'b1;

            if (is_frame_start && swap_pending) begin
                front_wr_ptr <= front_sel ? wr_ptr0 : wr_ptr1;
                front_sel    <= ~front_sel;
                swap_pending <= 1'b0;
            end

            if (sample_tick) begin
                if (front_sel == 1'b0) begin
                    buf1[wr_ptr1] <= y_value;
                    wr_ptr1       <= wr_ptr1 + 1'b1;
                end else begin
                    buf0[wr_ptr0] <= y_value;
                    wr_ptr0       <= wr_ptr0 + 1'b1;
                end
            end
        end
    end

    // --- Read side: local column index within this view ---
    wire [10:0] local_x = pixel_x - X_OFFSET;
    wire [10:0] read_addr_raw = {1'b0, front_wr_ptr} + local_x;
    wire [10:0] read_addr_wrapped = read_addr_raw - WIDTH;
    wire [9:0]  read_addr = (read_addr_raw >= WIDTH) ?
                             read_addr_wrapped[9:0] : read_addr_raw[9:0];
    wire [9:0]  trace_y = front_sel ? buf1[read_addr] : buf0[read_addr];

    reg [9:0] prev_trace_y;
    always @(posedge clk) begin
        if (in_region)
            prev_trace_y <= trace_y;
    end

    wire [9:0] effective_prev = (local_x == 11'd0) ? trace_y : prev_trace_y;
    wire [9:0] seg_top    = (trace_y < effective_prev) ? trace_y : effective_prev;
    wire [9:0] seg_bottom = (trace_y < effective_prev) ? effective_prev : trace_y;
    wire [9:0] local_y    = pixel_y - Y_OFFSET;

    assign pixel_on = in_region && (local_y >= seg_top) && (local_y <= seg_bottom);

    // X-axis: horizontal line at the vertical center of this view
    // Y-axis: vertical line at the left edge of this view
    localparam [9:0] AXIS_Y = HEIGHT/2;
    wire is_x_axis = (local_y == AXIS_Y);
    wire is_y_axis = (local_x == 11'd0);
    assign axis_on = in_region && (is_x_axis || is_y_axis);

endmodule