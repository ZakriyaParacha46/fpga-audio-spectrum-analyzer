`timescale 1ns / 1ps
//
// debounce: synchronizes an asynchronous pushbutton input (2-FF, same
// idea as every other async input in this project), then only accepts
// a new level once it has been stable for DEBOUNCE_MS - and emits a
// single clk-cycle pulse on each clean press (rising edge of the
// debounced level), not a continuous level, so holding the button
// down doesn't repeatedly re-trigger whatever it's wired to.
//
module debounce #(
    parameter integer CLK_FREQ    = 100_000_000,
    parameter integer DEBOUNCE_MS = 10
) (
    input  wire clk,
    input  wire reset,
    input  wire btn_raw,
    output reg  press_pulse
);

    // --- 2-FF synchronizer ---
    reg btn_sync0, btn_sync1;
    always @(posedge clk) begin
        btn_sync0 <= btn_raw;
        btn_sync1 <= btn_sync0;
    end

    // --- Stable-for-N-cycles debounce ---
    localparam integer STABLE_COUNT = (CLK_FREQ / 1000) * DEBOUNCE_MS;
    localparam integer CNT_WIDTH    = $clog2(STABLE_COUNT + 1);

    reg [CNT_WIDTH-1:0] stable_counter;
    reg                 btn_debounced;

    always @(posedge clk) begin
        if (reset) begin
            stable_counter <= {CNT_WIDTH{1'b0}};
            btn_debounced  <= 1'b0;
        end else if (btn_sync1 != btn_debounced) begin
            // disagrees with the currently-accepted level - has to
            // stay different for STABLE_COUNT cycles before it counts
            if (stable_counter == STABLE_COUNT - 1) begin
                btn_debounced  <= btn_sync1;
                stable_counter <= {CNT_WIDTH{1'b0}};
            end else begin
                stable_counter <= stable_counter + 1'b1;
            end
        end else begin
            stable_counter <= {CNT_WIDTH{1'b0}};
        end
    end

    // --- Edge detect on the debounced level: one-cycle pulse per press ---
    reg btn_debounced_prev;
    always @(posedge clk) begin
        if (reset) begin
            btn_debounced_prev <= 1'b0;
            press_pulse        <= 1'b0;
        end else begin
            btn_debounced_prev <= btn_debounced;
            press_pulse        <= btn_debounced && !btn_debounced_prev;
        end
    end

endmodule
