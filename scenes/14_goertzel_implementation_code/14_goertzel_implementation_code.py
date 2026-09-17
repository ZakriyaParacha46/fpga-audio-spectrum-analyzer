"""
Scene 14 - How It's Actually Implemented (Goertzel, not FFT)

Direct sequel to scene 13 (13_what_is_the_fft), which explained the classic
radix-2 FFT / butterfly-network approach and closed on its control-flow
complexity ("hard to debug without a simulator"). This scene reveals the
real board does NOT use a butterfly network - it uses 256 Goertzel
resonators, swept one at a time.

Real source: FFTspectrum/VU.srcs/sources_1/new/fft_view.v
  FFT_SIZE = 512, NUM_BINS = 256 (bin 0 / DC skipped, bins 1-256 displayed).
  Goertzel recurrence run per-bin over 512 samples; coeff is Q2.13 fixed
  point (2*cos(2*pi*bin/512)). Power (magnitude^2) needs no sqrt for a bar
  chart. A full 256-bin sweep costs 256*512 = 131,072 cycles, ~2ms @ 65MHz
  - comfortably faster than the ~10.7ms it takes to collect another 512
  fresh samples, so throughput was never the bottleneck. The real reason
  for Goertzel: its control logic is a plain nested loop - no bit-reversal
  addressing, no staged twiddle-factor indexing - which matters when the
  only way to test a change is a full synth->impl->bitstream->reflash cycle
  with no simulator.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *
import textwrap

RIGHT_X = 5.4  # x-position for highlight labels beside the code box


class GoertzelImplementationCode(Scene):
    def construct(self):
        set_bg(self)

        # ==================================================================
        # 1. Direct contrast with scene 13's butterfly network
        # ==================================================================
        # narration: "So here's the twist. This port doesn't use a
        # butterfly network at all. No bit reversal, no stage FFT."
        # (0.2-5.84)
        no_bf = Text("No butterfly network.", font_size=38, color=RED_C)
        strike = Line(no_bf.get_left() + LEFT * 0.05, no_bf.get_right() + RIGHT * 0.05,
                      color=RED_C, stroke_width=3)
        strike.move_to(no_bf.get_center())

        # written slowly so it's still resolving as "So here's the twist"
        # is spoken (0.2-0.92), rather than popping in and freezing.
        self.play(Write(no_bf), run_time=1.46)
        # the strike draws itself slowly across "a butterfly network at
        # all. No bit reversal, no stage FFT." (2.14-5.84)
        self.play(Create(strike), run_time=4.74)

        # narration: "Instead, 256 go to resonators, swept one at a time."
        # (6.24-11.4)
        aha = Text("256 Goertzel resonators, swept one at a time.",
                    font_size=34, color=GREEN_C)
        fit_frame(aha)
        self.play(FadeOut(VGroup(no_bf, strike), shift=UP * 0.3), run_time=0.3)
        self.play(Write(aha), run_time=4.9)
        self.play(FadeOut(aha), run_time=0.3)

        # ==================================================================
        # 2. Code box: the real Goertzel recurrence
        # ==================================================================
        box_w, box_h = 10.67, 5.2
        box_center = LEFT * 1.6 + UP * 0.5

        title = Text("Goertzel Resonator - fft_view.v (excerpt)", font_size=22, color=WHITE)
        title.to_edge(UP, buff=0.35)

        box = code_box(width=box_w, height=box_h, center=box_center)

        self.play(Write(title), run_time=0.5)
        self.play(FadeIn(box), run_time=0.35)

        L = []
        L.append(code_line(0, [("// s1, s2 are Goertzel state: s[n-1], s[n-2].", COMMENT)]))
        L.append(code_line(0, [("// coeff = 2*cos(2*pi*bin/512), Q2.13 fixed point.", COMMENT)]))
        L.append(code_line(0, [("wire", KEYWORD), ("signed", KEYWORD), ("[47:0]", NUMBER),
                                ("cs1_full", SIGNAL), ("=", SIGNAL), ("coeff", SIGNAL),
                                ("*", SIGNAL), ("s1;", SIGNAL)]))
        L.append(code_line(0, [("wire", KEYWORD), ("signed", KEYWORD), ("[31:0]", NUMBER),
                                ("cs1", SIGNAL), ("=", SIGNAL), ("cs1_full[44:13];", SIGNAL)],
                            comment="// >>>13, back to integer scale"))
        L.append(code_line(0, [("wire", KEYWORD), ("signed", KEYWORD), ("[31:0]", NUMBER),
                                ("s0_next", SIGNAL), ("=", SIGNAL), ("x_cur_s", SIGNAL),
                                ("+", SIGNAL), ("cs1", SIGNAL), ("-", SIGNAL), ("s2;", SIGNAL)],
                            comment="// s[n]=x[n]+coeff*s[n-1]-s[n-2]"))
        L.append(code_line(0, [("// each cycle of the sweep, for all 512 samples:", COMMENT)]))
        L.append(code_line(0, [("CS_RUN", KEYWORD), (":", KEYWORD), ("s2", SIGNAL), ("<=", SIGNAL),
                                ("s1;", SIGNAL), ("s1", SIGNAL), ("<=", SIGNAL), ("s0_next;", SIGNAL)]))
        L.append(code_line(0, [("// power = s1^2 + s2^2 - (coeff*s1>>>13)*s2", COMMENT)]))
        L.append(code_line(0, [("// (no sqrt needed - magnitude squared is enough)", COMMENT)]))
        L.append(code_line(0, [("wire", KEYWORD), ("signed", KEYWORD), ("[63:0]", NUMBER),
                                ("power_signed", SIGNAL), ("=", SIGNAL), ("s1sq_r", SIGNAL),
                                ("+", SIGNAL), ("s2sq_r", SIGNAL), ("-", SIGNAL), ("cross_r;", SIGNAL)]))

        def gap():
            return {"group": Rectangle(width=0.01, height=0.06, stroke_opacity=0, fill_opacity=0)}

        layout = L[0:5] + [gap()] + L[5:7] + [gap()] + L[7:10]
        full_code = VGroup(*[item["group"] for item in layout])
        full_code.arrange(DOWN, aligned_edge=LEFT, buff=0.05)

        avail_w = box_w - 0.5
        avail_h = box_h - 0.4
        scale = min(avail_w / full_code.width, avail_h / full_code.height, 1.0)
        full_code.scale(scale)
        full_code.move_to(box.get_center())

        self.play(
            LaggedStart(*[FadeIn(item["group"], shift=UP * 0.05) for item in L], lag_ratio=0.08),
            run_time=1.1,
        )

        # ------------------------------------------------------------
        # Highlight helper (same pattern as inference_mac_code.py)
        # ------------------------------------------------------------
        def show_label(target, text, prev_rect, wrap=24, transform_time=0.5, grow_time=0.6):
            rect = SurroundingRectangle(
                target, color=YELLOW_HL, buff=0.05, stroke_width=0,
                fill_color=YELLOW_HL, fill_opacity=0.27,
            )
            if prev_rect is None:
                self.play(FadeIn(rect), run_time=transform_time)
            else:
                self.play(Transform(prev_rect, rect), run_time=transform_time)
                rect = prev_rect

            y = max(-2.6, min(3.0, target.get_center()[1]))
            label = Text(textwrap.fill(text, width=wrap), font_size=19,
                         color=WHITE, line_spacing=0.9)
            label.move_to(RIGHT * RIGHT_X + UP * y)
            fit_frame(label)

            arrow = Arrow(rect.get_right(), label.get_left() + LEFT * 0.15,
                          buff=0.1, color=YELLOW_HL, stroke_width=3)
            # grow_time stretched to span the narration this highlight
            # covers, so the arrow/label are still resolving into place
            # while the words play, rather than an instant pop + hold.
            self.play(GrowArrow(arrow), FadeIn(label, shift=LEFT * 0.15), run_time=grow_time)
            return rect, label, arrow

        def hide(mobs, run_time=0.4):
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)

        # narration: "Each one just a two-term recurring recurrence."
        # (11.58-14.82) into "Multiply at subtract repeat 512 times and
        # out comes the bin power." (15.46-20.4) - the arrow/label grow in
        # slowly across this whole span instead of popping in and
        # freezing on a static highlight.
        rect = None
        target1 = VGroup(L[2]["group"], L[3]["group"], L[4]["group"])
        rect, label1, arrow1 = show_label(
            target1, "The whole resonator: a two-term recurrence, one add, one multiply.", rect,
            grow_time=4.5,
        )
        hide([label1, arrow1], run_time=1.25)

        # narration: "No square root needed." (20.7-21.72)
        target2 = L[9]["code"]
        rect, label2, arrow2 = show_label(
            target2, "No sqrt needed - power is enough for a bar chart.", rect,
            transform_time=0.6, grow_time=1.0,
        )
        hide([label2, arrow2, rect], run_time=0.4)

        self.play(FadeOut(VGroup(box, title, *[item["group"] for item in layout])), run_time=0.5)

        # ==================================================================
        # 3. The sweep: bin_idx 1->256, each run over 512 samples
        # ==================================================================
        sweep_title = Text("Sweep: one bin at a time", font_size=30, color=WHITE)
        sweep_title.to_edge(UP, buff=0.5)
        self.play(Write(sweep_title), run_time=0.5)

        loop_lines = VGroup(
            Text("for bin_idx in 1..256:", font="Menlo", font_size=20, color=KEYWORD),
            Text("    for sample in 0..512:", font="Menlo", font_size=20, color=KEYWORD),
            Text("        s2 <= s1;  s1 <= s0_next;", font="Menlo", font_size=20, color=SIGNAL),
        ).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        loop_lines.move_to(UP * 1.1)

        self.play(FadeIn(loop_lines, shift=UP * 0.1), run_time=0.5)
        inner_rect = SurroundingRectangle(loop_lines[2], color=YELLOW_HL, buff=0.06,
                                           stroke_width=0, fill_color=YELLOW_HL, fill_opacity=0.22)
        self.play(FadeIn(inner_rect), run_time=0.35)

        bin_counter = Text("bin_idx = 1", font="Menlo", font_size=22, color=NUMBER)
        sample_counter = Text("sample = 0", font="Menlo", font_size=22, color=NUMBER)
        counters = VGroup(bin_counter, sample_counter).arrange(RIGHT, buff=0.7)
        counters.next_to(loop_lines, DOWN, buff=0.55)
        self.play(FadeIn(counters), run_time=0.4)

        # inner loop ticks for bin 1 - a touch slower than instant so it
        # reads as counting, not a jump-cut
        for val in (128, 256, 384, 512):
            new_sc = Text(f"sample = {val}", font="Menlo", font_size=22, color=NUMBER)
            new_sc.move_to(sample_counter.get_center())
            self.play(ReplacementTransform(sample_counter, new_sc), run_time=0.3)
            sample_counter = new_sc

        # bin advances, sample resets
        new_bc = Text("bin_idx = 2", font="Menlo", font_size=22, color=NUMBER)
        new_bc.move_to(bin_counter.get_center())
        new_sc = Text("sample = 0", font="Menlo", font_size=22, color=NUMBER)
        new_sc.move_to(sample_counter.get_center())
        self.play(ReplacementTransform(bin_counter, new_bc),
                   ReplacementTransform(sample_counter, new_sc), run_time=0.4)
        bin_counter, sample_counter = new_bc, new_sc

        dots = Text("...continues for all 256 bins...", font_size=18, color=GRAY_TXT)
        dots.next_to(counters, DOWN, buff=0.4)
        self.play(FadeIn(dots), run_time=0.6)

        # narration: "Do the math and the whole 256-bin sweep costs about
        # 2 milliseconds at 65 megahertz." (22.14-30.42) - the jump to the
        # final bin is stretched into a slow, continuous transform so the
        # counters visibly sweep through the run instead of snapping and
        # sitting still.
        new_bc = Text("bin_idx = 256", font="Menlo", font_size=22, color=NUMBER)
        new_bc.move_to(bin_counter.get_center())
        new_sc = Text("sample = 512", font="Menlo", font_size=22, color=NUMBER)
        new_sc.move_to(sample_counter.get_center())
        self.play(ReplacementTransform(bin_counter, new_bc),
                   ReplacementTransform(sample_counter, new_sc), run_time=3.25)
        bin_counter, sample_counter = new_bc, new_sc

        self.play(FadeOut(VGroup(sweep_title, loop_lines, inner_rect, counters, dots,
                                  bin_counter, sample_counter)), run_time=1.0)

        # ==================================================================
        # 4. Closing stats block (styled like inference_mac_code.py)
        # ==================================================================
        stats = VGroup(
            Text("256 bins x 512 samples = 131,072 cycles",
                 font="Menlo", font_size=24, color=WHITE),
            Text("= ~2ms @ 65MHz", font="Menlo", font_size=24, color=GREEN_C),
            Text("(collecting the next 512 samples alone takes ~10.7ms --",
                 font="Menlo", font_size=18, color=GRAY_TXT),
            Text(" the sweep was never the bottleneck)",
                 font="Menlo", font_size=18, color=GRAY_TXT),
        ).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        fit_frame(stats)

        # narration: "But speed was never really the point." (30.8-32.46)
        self.play(FadeIn(stats[0], shift=UP * 0.15), run_time=0.6)
        self.play(FadeIn(stats[1], shift=UP * 0.15), run_time=0.9)
        self.play(FadeIn(stats[2], shift=UP * 0.1), FadeIn(stats[3], shift=UP * 0.1), run_time=1.6)

        self.play(FadeOut(stats), run_time=0.5)

        # ==================================================================
        # 5. The real reason
        # narration: "The real reason: a plain nested loop is something
        # you can trust on the very first reflash." (33.26-39.22)
        # ==================================================================
        final1 = Text("The real reason: a plain nested loop you can trust",
                       font_size=27, color=WHITE)
        final2 = Text("on the first reflash.", font_size=27, color=GREEN_C)
        final3 = Text("Not bit-reversal. Not staged twiddle indexing.",
                       font_size=24, color=GRAY_TXT)
        final = VGroup(final1, final2, final3).arrange(DOWN, buff=0.3)
        fit_frame(final)

        # written slowly across "The real reason: a plain nested loop is
        # something you can trust" (33.26-37.24) instead of popping in and
        # sitting frozen
        self.play(Write(final1), run_time=2.7)
        # "on the very first reflash." (37.24-39.22)
        self.play(Write(final2), run_time=2.0)
        self.play(FadeIn(final3, shift=UP * 0.15), run_time=0.7)
