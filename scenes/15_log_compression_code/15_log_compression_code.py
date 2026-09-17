"""
Scene 15 - Compressing the Spectrum

Real production code, verbatim from
  FFTspectrum/VU.srcs/sources_1/new/fft_view.v

Narrative: raw FFT bin power spans enormous orders of magnitude. Plotted
linearly, one bin dwarfs the rest - one tall spike, 255 flat bars. The
fix is an approximate log2: the position of the highest set bit in the
48-bit power value is itself a coarse log2 (free, in hardware - it's
just "where's the top 1 bit"). Three more fractional bits pulled from
just below that msb give a smooth ramp between power-of-two steps
instead of the bars only moving at power-of-two boundaries. Then a
noise floor (FLOOR=140) and a contrast multiplier (SCALE=2), both
tuned by eye against the real hardware, finish the compression.

Fast first pass - short self.wait() calls, narration/timing added later.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *

# ---------------------------------------------------------------------------
# Worked binary example used in beats 2 & 3.
# 16 low bits of the 48-bit power value (bits 15..0), MSB first.
# bit15..bit0 = 0 0 0 0 1 0 1 1 0 1 1 0 1 0 0 0
# highest set bit -> index 11  (msb = 11)
# 3 fractional bits just below it -> bits[10:8] = 0 1 1 = 3
# log2_approx = {msb, frac} = 11*8 + 3 = 91
# ---------------------------------------------------------------------------
BITS = [0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0]  # idx 15 -> 0
MSB_IDX = 11
FRAC_A = 3   # bits[10:8] = 011
FRAC_B = 6   # a nearby value's bits[10:8] = 110, same msb
LOG2_A = MSB_IDX * 8 + FRAC_A   # 91
LOG2_B = MSB_IDX * 8 + FRAC_B   # 94

FLOOR = 140
SCALE = 2


class LogCompressionCode(Scene):
    def construct(self):
        set_bg(self)

        # =========================================================
        # BEAT 1 - the linear problem: one spike, 255 flat bars
        # =========================================================
        title = Text("Compressing the Spectrum", font_size=38, color=WHITE)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=0.6)

        # narration: "Float raw powers on a normal scale and you get one
        # bar that eats the entire screen..." (0-4.58)
        sub1 = Text("plotted linearly: one spike, 255 flat bars",
                    font_size=22, color=RED_C)
        sub1.next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(sub1, shift=UP * 0.1), run_time=0.5)

        n_bars = 20
        bar_w = 0.28
        gap = 0.06
        baseline_y = -2.0
        total_w = n_bars * (bar_w + gap) - gap
        start_x = -total_w / 2 + bar_w / 2

        spike_i = 8
        heights = [0.04] * n_bars
        heights[spike_i] = 3.6

        bars = VGroup()
        for i, h in enumerate(heights):
            color = RED_C if i == spike_i else GRAY_TXT
            r = Rectangle(width=bar_w, height=max(h, 0.04),
                          fill_color=color, fill_opacity=0.9, stroke_width=0)
            x = start_x + i * (bar_w + gap)
            r.move_to([x, baseline_y + r.height / 2, 0])
            bars.add(r)

        axis_line = Line([start_x - bar_w, baseline_y, 0],
                         [start_x + total_w, baseline_y, 0],
                         color=WHITE, stroke_width=2)

        self.play(Create(axis_line), run_time=0.3)
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.05) for b in bars],
                              lag_ratio=0.03), run_time=1.3)

        # "...that eats the entire screen" (3.24-4.58)
        spike_label = Text("keeps climbing off scale", font_size=16, color=RED_C)
        spike_label.next_to(bars[spike_i], UP, buff=0.35)
        fit_frame(spike_label)
        self.play(FadeIn(spike_label, shift=DOWN * 0.1), run_time=1.9)

        # "and 255 bars so short they might as well not exist. The
        # dynamic range is just too large to look directly." (4.58-12.2) -
        # written slowly across the whole span instead of popping in and
        # freezing.
        flat_label = Text("everything else: invisible at this scale",
                          font_size=18, color=GRAY_TXT)
        flat_label.next_to(axis_line, DOWN, buff=0.35)
        fit_frame(flat_label)
        self.play(Write(flat_label), run_time=7.6)

        beat1 = VGroup(sub1, axis_line, bars, spike_label, flat_label)
        self.play(FadeOut(beat1), run_time=0.3)

        # =========================================================
        # BEAT 2 - highest set bit = coarse log2
        # narration: "The fix is cheap. Find the position of the highest
        # set bit in that bin's powers." (12.96-19.02)
        # =========================================================
        sub2 = Text("highest set bit position ≈ log2", font_size=26, color=WHITE)
        sub2.next_to(title, DOWN, buff=0.35)
        self.play(FadeIn(sub2, shift=UP * 0.1), run_time=0.4)

        bit_cells = VGroup()
        bit_texts = []
        idx_texts = []
        for pos, val in enumerate(BITS):
            bit_idx = 15 - pos
            t = code_frag(str(val), SIGNAL)
            idx = Text(str(bit_idx), font_size=13, color=GRAY_TXT)
            cell = VGroup(t, idx).arrange(DOWN, buff=0.12)
            bit_texts.append(t)
            idx_texts.append(idx)
            bit_cells.add(cell)
        bit_cells.arrange(RIGHT, buff=0.22)
        bit_cells.move_to(UP * 1.0)

        val_label = Text("power value, bits 15..0", font_size=17, color=GRAY_TXT)
        val_label.next_to(bit_cells, UP, buff=0.3)

        self.play(FadeIn(val_label), run_time=0.3)
        self.play(LaggedStart(*[FadeIn(c) for c in bit_cells], lag_ratio=0.03),
                  run_time=1.0)

        # "Find the position of the highest set..." (14.24-16.22)
        msb_pos = 15 - MSB_IDX  # index into bit_cells (0 = leftmost)
        msb_rect = SurroundingRectangle(bit_cells[msb_pos], color=YELLOW_HL,
                                        buff=0.08, stroke_width=3)
        msb_arrow_label = Text("msb = 11  →  coarse log2", font_size=20, color=YELLOW_HL)
        msb_arrow_label.next_to(bit_cells, DOWN, buff=0.7)
        fit_frame(msb_arrow_label)
        self.play(Create(msb_rect), run_time=0.4)
        self.play(FadeIn(msb_arrow_label, shift=UP * 0.1), run_time=2.0)

        # "...bit in that bin's powers." (16.22-19.02) - written slowly
        # across the phrase instead of popping in and freezing.
        explain2 = Text("walk all 48 bits, remember the last one that's set",
                        font_size=18, color=GRAY_TXT)
        explain2.next_to(msb_arrow_label, DOWN, buff=0.3)
        fit_frame(explain2)
        self.play(Write(explain2), run_time=2.3)

        self.play(FadeOut(VGroup(sub2, explain2)), run_time=0.35)

        # =========================================================
        # BEAT 3 - fractional bits for a smooth ramp
        # narration: "Grab a few more fractional bits just below it for a
        # smooth ramp instead of blocky jump." (19.02-26.2)
        # =========================================================
        sub3 = Text("3 fractional bits just below msb: smoother steps",
                    font_size=24, color=WHITE)
        sub3.next_to(title, DOWN, buff=0.35)
        fit_frame(sub3)
        self.play(FadeIn(sub3, shift=UP * 0.1),
                  FadeOut(msb_arrow_label), run_time=0.4)

        frac_cells = VGroup(*bit_cells[msb_pos + 1: msb_pos + 4])
        frac_rect = SurroundingRectangle(frac_cells, color=PURPLE_C,
                                         buff=0.08, stroke_width=3)
        frac_label = Text("frac = val[msb-1 -: 3]", font_size=18, color=PURPLE_C)
        frac_label.next_to(bit_cells, DOWN, buff=0.65)
        fit_frame(frac_label)
        self.play(Create(frac_rect), run_time=0.4)
        self.play(FadeIn(frac_label, shift=UP * 0.1), run_time=2.6)

        self.play(FadeOut(VGroup(bit_cells, val_label, msb_rect, frac_rect,
                                  frac_label, sub3)), run_time=0.4)

        # two nearby values, same msb, different frac -> different heights
        # "...for a smooth ramp instead of blocky jump." (23.62-26.2)
        sub3b = Text("same msb, different frac  →  different bar height",
                     font_size=22, color=WHITE)
        sub3b.next_to(title, DOWN, buff=0.35)
        fit_frame(sub3b)
        self.play(FadeIn(sub3b, shift=UP * 0.1), run_time=0.4)

        cmp_baseline = -1.6
        barA = Rectangle(width=0.9, height=LOG2_A / 40, fill_color=BLUE_C,
                         fill_opacity=0.9, stroke_width=0)
        barB = Rectangle(width=0.9, height=LOG2_B / 40, fill_color=GREEN_C,
                         fill_opacity=0.9, stroke_width=0)
        barA.move_to([-1.3, cmp_baseline + barA.height / 2, 0])
        barB.move_to([1.3, cmp_baseline + barB.height / 2, 0])
        cmp_axis = Line([-2.6, cmp_baseline, 0], [2.6, cmp_baseline, 0],
                        color=WHITE, stroke_width=2)

        labelA = Text(f"val A: msb=11 frac=3\nlog2_approx = {LOG2_A}",
                      font_size=16, color=BLUE_C, line_spacing=0.9)
        labelA.next_to(barA, DOWN, buff=0.25)
        labelB = Text(f"val B: msb=11 frac=6\nlog2_approx = {LOG2_B}",
                      font_size=16, color=GREEN_C, line_spacing=0.9)
        labelB.next_to(barB, DOWN, buff=0.25)
        fit_frame(labelA)
        fit_frame(labelB)

        self.play(Create(cmp_axis), run_time=0.25)
        self.play(FadeIn(barA, shift=UP * 0.1), FadeIn(labelA), run_time=0.4)
        # "for a smooth ramp instead of blocky jump." (23.62-26.2)
        self.play(FadeIn(barB, shift=UP * 0.1), FadeIn(labelB), run_time=1.9)

        # "And suddenly six orders of magnitude turn into a readable
        # power height." (26.78-31.04) - the two-bar comparison is the
        # visual payoff for this line; the note is written slowly across
        # the whole span rather than popping in and freezing.
        note3 = Text("without frac bits, both would snap to the same height",
                     font_size=16, color=GRAY_TXT)
        note3.next_to(cmp_axis, DOWN, buff=1.3)
        fit_frame(note3)
        self.play(Write(note3), run_time=5.0)

        self.play(FadeOut(VGroup(sub3b, cmp_axis, barA, barB, labelA, labelB, note3)),
                  run_time=0.3)

        # =========================================================
        # BEAT 4 - the real code
        # narration: "No hardware log unit anywhere on the chip. No
        # lookup tables for logarithms." (31.32-36.38)
        # =========================================================
        box = code_box(width=11.0, height=5.3, center=DOWN * 0.15)
        box_title = Text("fft_view.v - log2_approx", font_size=20, color=WHITE)
        box_title.next_to(box, UP, buff=0.2)
        fit_frame(box_title)
        self.play(FadeOut(title), FadeIn(box), FadeIn(box_title), run_time=0.4)

        L = []
        L.append(code_line(0, [("function", KEYWORD), ("[8:0]", NUMBER), ("log2_approx;", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("[47:0]", NUMBER), ("val;", SIGNAL)]))
        L.append(code_line(4, [("integer", KEYWORD), ("i;", SIGNAL)]))
        L.append(code_line(4, [("reg", KEYWORD), ("[5:0]", NUMBER), ("msb;", SIGNAL)]))
        L.append(code_line(4, [("reg", KEYWORD), ("[2:0]", NUMBER), ("frac;", SIGNAL)]))
        L.append(code_line(4, [("begin", KEYWORD)]))
        L.append(code_line(8, [("msb", SIGNAL), ("=", SIGNAL), ("6'd0;", NUMBER)]))
        L.append(code_line(8, [("for", KEYWORD), ("(i", SIGNAL), ("=", SIGNAL), ("0;", NUMBER),
                               ("i", SIGNAL), ("<", SIGNAL), ("48;", NUMBER),
                               ("i", SIGNAL), ("=", SIGNAL), ("i", SIGNAL), ("+", SIGNAL), ("1)", NUMBER)]))
        L.append(code_line(12, [("if", KEYWORD), ("(val[i])", SIGNAL)]))
        L.append(code_line(16, [("msb", SIGNAL), ("=", SIGNAL), ("i[5:0];", SIGNAL)]))
        L.append(code_line(8, [("if", KEYWORD), ("(msb", SIGNAL), (">=", SIGNAL), ("3)", NUMBER)]))
        L.append(code_line(12, [("frac", SIGNAL), ("=", SIGNAL), ("val[msb-1", SIGNAL), ("-:", SIGNAL), ("3];", NUMBER)]))
        L.append(code_line(8, [("else", KEYWORD)]))
        L.append(code_line(12, [("frac", SIGNAL), ("=", SIGNAL), ("3'd0;", NUMBER)]))
        L.append(code_line(8, [("log2_approx", SIGNAL), ("=", SIGNAL), ("{msb,", SIGNAL), ("frac};", SIGNAL)]))
        L.append(code_line(4, [("end", KEYWORD)]))
        L.append(code_line(0, [("endfunction", KEYWORD)]))

        full_code = VGroup(*[item["group"] for item in L])
        full_code.arrange(DOWN, aligned_edge=LEFT, buff=0.10)
        avail_w = box.width - 0.6
        avail_h = box.height - 0.5
        scale = min(avail_w / full_code.width, avail_h / full_code.height, 1.0)
        full_code.scale(scale)
        full_code.move_to(box.get_center())

        self.play(LaggedStart(*[FadeIn(item["group"], shift=UP * 0.04) for item in L],
                              lag_ratio=0.06), run_time=1.1)

        # highlight the msb-finding loop - "No hardware log unit anywhere
        # on the chip." (31.32-34.16)
        loop_target = VGroup(L[7]["group"], L[8]["group"], L[9]["group"])
        loop_rect = SurroundingRectangle(loop_target, color=YELLOW_HL, buff=0.06,
                                         stroke_width=0, fill_color=YELLOW_HL,
                                         fill_opacity=0.22)
        loop_label = Text("scans every bit; last '1' found wins = highest set bit",
                          font_size=16, color=YELLOW_HL)
        loop_label.next_to(box, DOWN, buff=0.35)
        fit_frame(loop_label)
        self.play(FadeIn(loop_rect), run_time=0.3)
        self.play(FadeIn(loop_label, shift=UP * 0.1), run_time=1.6)
        self.play(FadeOut(loop_label), run_time=0.25)

        # highlight the fractional-bit line - "No lookup tables for
        # logarithms." (34.44-36.38)
        frac_target = L[11]["group"]
        frac_rect2 = SurroundingRectangle(frac_target, color=PURPLE_C, buff=0.06,
                                          stroke_width=0, fill_color=PURPLE_C,
                                          fill_opacity=0.22)
        frac_label2 = Text("grabs 3 bits just below msb - the fractional part",
                           font_size=16, color=PURPLE_C)
        frac_label2.next_to(box, DOWN, buff=0.35)
        fit_frame(frac_label2)
        self.play(Transform(loop_rect, frac_rect2), run_time=0.4)
        self.play(FadeIn(frac_label2, shift=UP * 0.1), run_time=0.8)

        self.play(FadeOut(VGroup(box, box_title, full_code, loop_rect, frac_label2)),
                  run_time=0.35)

        # =========================================================
        # BEAT 5 - FLOOR / SCALE and the "after" spectrum
        # narration: "Just bit, position, math, resolve, combinationally
        # for free." (36.8-41.26) - fast, punchy narration, so this beat
        # moves quickly too rather than lingering on any one sub-point.
        # =========================================================
        title2 = Text("Compressing the Spectrum", font_size=38, color=WHITE)
        title2.to_edge(UP, buff=0.4)
        self.play(FadeIn(title2), run_time=0.3)

        formula = code_frag(
            "height_raw = (log2_val > FLOOR) ? log2_val - FLOOR : 0",
            SIGNAL,
        )
        formula.scale(0.85)
        formula.next_to(title2, DOWN, buff=0.4)
        fit_frame(formula)
        self.play(FadeIn(formula, shift=UP * 0.1), run_time=0.7)

        floor_line = Text(f"FLOOR = {FLOOR}   - noise floor, log2-units",
                          font_size=20, color=NUMBER)
        scale_line = Text(f"SCALE = {SCALE}     - contrast multiplier",
                          font_size=20, color=NUMBER)
        consts = VGroup(floor_line, scale_line).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        consts.next_to(formula, DOWN, buff=0.35)
        fit_frame(consts)
        self.play(FadeIn(floor_line, shift=UP * 0.1), run_time=0.3)
        self.play(FadeIn(scale_line, shift=UP * 0.1), run_time=0.5)

        tuned_note = Text("both tuned by eye against real hardware",
                          font_size=16, color=GRAY_TXT)
        tuned_note.next_to(consts, DOWN, buff=0.3)
        fit_frame(tuned_note)
        self.play(FadeIn(tuned_note), run_time=0.6)

        self.play(FadeOut(VGroup(formula, consts, tuned_note)), run_time=0.3)

        # "resolve," (39.06-39.44)
        sub5 = Text("after: visible variation across every bar", font_size=24, color=GREEN_C)
        sub5.next_to(title2, DOWN, buff=0.35)
        self.play(FadeIn(sub5, shift=UP * 0.1), run_time=0.3)

        after_heights = [3.2, 2.7, 3.0, 2.3, 2.9, 1.9, 2.4, 1.6, 2.2,
                        1.3, 1.9, 1.1, 1.6, 0.9, 1.3, 0.7, 1.0, 0.5, 0.8, 0.35]
        after_bars = VGroup()
        for i, h in enumerate(after_heights):
            r = Rectangle(width=bar_w, height=h, fill_color=GREEN_C,
                          fill_opacity=0.85, stroke_width=0)
            x = start_x + i * (bar_w + gap)
            r.move_to([x, baseline_y + r.height / 2, 0])
            after_bars.add(r)
        after_axis = Line([start_x - bar_w, baseline_y, 0],
                          [start_x + total_w, baseline_y, 0],
                          color=WHITE, stroke_width=2)

        self.play(Create(after_axis), run_time=0.2)
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.05) for b in after_bars],
                              lag_ratio=0.03), run_time=0.8)

        # "combinationally for free." (40.06-41.26) - near-verbatim match
        closing = Text("no hardware log unit, no lookup table --\njust bit-position math, done combinationally",
                       font_size=18, color=WHITE, line_spacing=1.0)
        closing.next_to(after_axis, DOWN, buff=0.4)
        fit_frame(closing)
        self.play(FadeIn(closing, shift=UP * 0.1), run_time=0.76)
