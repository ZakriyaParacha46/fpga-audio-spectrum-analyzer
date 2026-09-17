"""
Scene 10 - The Complementary Highpass

Sequel to scene 09 (the lowpass EMA code scene). Since
lowpass(x) + highpass(x) = x by construction, the highpass filter doesn't
need a new equation - it reuses the SAME verified EMA recurrence and just
subtracts it from the input: highpass = level - ema.

That result is naturally zero-mean, which doesn't fit this project's
unsigned "0 = quiet" display convention (0-4095). A fixed +2048 re-bias
was tried and was WRONG - the real idle point isn't mid-scale (scene 06
measured it at code 3276, not 2048). The actual fix: a THIRD, independent,
much-slower EMA (BIAS_SHIFT=12, always slower than any live `shift`) whose
only job is tracking the true long-term baseline, so it can be added back
onto the zero-mean highpass output. Final result clamped to 0-4095.

Real source (verbatim, from FFTspectrum/VU.srcs/sources_1/new/highpass_filter.v):
see the module below - code logic/ports are reproduced exactly; the one
multi-line source comment about the re-bias tracker is condensed to fit the
box (noted in the build report), and the two long lines (hp_biased combine,
and the ternary clamp) are wrapped across physical rows the same way any
code viewer would soft-wrap them - tokens themselves are untouched.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *

IDLE_WRONG = 2048
IDLE_REAL = 3276  # measured on the real board, scene 06


class ComplementaryHighpassCode(Scene):
    def construct(self):
        set_bg(self)

        # =================================================================
        # SECTION 1 - recap: highpass = input - lowpass
        # =================================================================
        # Narration: "Here's a shortcut most people miss." (~0.1-1.4s).
        # As with the other scenes in this retiming pass, extra time
        # needed to match narration pacing lives in longer run_time=
        # values on the plays that are already moving (a slow Write, a
        # slow settling FadeIn) rather than in self.wait() pauses that
        # would freeze the frame - so motion is continuous throughout.
        title0 = Text("The Complementary Highpass", font_size=40, color=WHITE)
        title0.to_edge(UP, buff=0.5)
        self.play(Write(title0), run_time=1.7)

        # "Since a lowpass version of the signal plus its highpass version
        # always adds back up to the original signal" (~2.0-9.7s)
        eq1 = Text("lowpass(x)  +  highpass(x)  =  x", font_size=28, color=WHITE)
        eq1.move_to(UP * 2.5)
        self.play(FadeIn(eq1, shift=UP * 0.1), run_time=2.3)

        # three small wave panels: input, lowpass, highpass
        def wave_panel(color, freq, amp, label_text):
            wave = FunctionGraph(lambda t: amp * np.sin(freq * t), x_range=[-1.6, 1.6],
                                  color=color, stroke_width=3)
            base = DashedLine(LEFT * 1.7, RIGHT * 1.7, color=GRAY_TXT, stroke_width=1.5)
            lbl = Text(label_text, font_size=18, color=color)
            lbl.next_to(wave, DOWN, buff=0.22)
            grp = VGroup(base, wave, lbl)
            return grp

        panel_in = wave_panel(WHITE, 3.2, 0.55, "input x[n]")
        panel_lp = wave_panel(BLUE_C, 0.9, 0.3, "lowpass (ema)")
        panel_hp = wave_panel(PURPLE_C, 3.2, 0.5, "highpass (x - ema)")

        minus = Text("-", font_size=34, color=GRAY_TXT)
        equals = Text("=", font_size=34, color=GRAY_TXT)

        row = VGroup(panel_in, minus, panel_lp, equals, panel_hp).arrange(RIGHT, buff=0.45)
        row.move_to(DOWN * 0.7)
        fit_frame(row)

        # Wave panels reveal one at a time, each landing under its own
        # clause: "...plus its highpass version..." (~3.9-5.5s), "...
        # always adds back..." (~5.5-7.4s), "...up to the original
        # signal" (~7.4-9.7s).
        self.play(FadeIn(panel_in), run_time=1.2)
        self.play(FadeIn(minus), FadeIn(panel_lp), run_time=1.8)
        self.play(FadeIn(equals), FadeIn(panel_hp), run_time=2.68)

        # "...you don't need a second filter." (~10.2-11.7s) - the morph
        # from eq1 to eq2 spans the short pause plus the whole sentence.
        eq2 = Text("highpass(x)  =  x  -  lowpass(x)", font_size=30, color=GREEN_C)
        eq2.move_to(UP * 2.5)
        self.play(ReplacementTransform(eq1, eq2), run_time=2.02)

        # Bridges into "Just run the same lowpass filter again..." (~12.3s)
        note0 = Text("same EMA. no new equation to verify.", font_size=20, color=GRAY_TXT)
        note0.next_to(eq2, DOWN, buff=0.3)
        self.play(FadeIn(note0), run_time=0.86)

        self.play(FadeOut(VGroup(title0, eq2, note0, row)), run_time=0.3)

        # =================================================================
        # SECTION 2 - the real code, verbatim, token-colored
        # =================================================================
        # Narration: "Just run the same lowpass filter again and subtract
        # it from the output." (~12.3-17.1s)
        title = Text("highpass_filter.v", font="Menlo", font_size=26, color=WHITE)
        title.to_edge(UP, buff=0.3)

        box = code_box(width=12.4, height=6.6, center=DOWN * 0.28)

        self.play(Write(title), run_time=0.6)
        self.play(FadeIn(box), run_time=0.9)

        def gap(h=0.05):
            return {"group": Rectangle(width=0.01, height=h, stroke_opacity=0, fill_opacity=0)}

        L = []
        L.append(code_line(0, [("module", KEYWORD), ("highpass_filter", SIGNAL), ("(", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("wire", KEYWORD), ("clk,", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("wire", KEYWORD), ("reset,", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("wire", KEYWORD), ("[11:0]", NUMBER), ("level,", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("wire", KEYWORD), ("level_valid,", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("wire", KEYWORD), ("[3:0]", NUMBER), ("shift,", SIGNAL)]))
        L.append(code_line(4, [("output", KEYWORD), ("wire", KEYWORD), ("[11:0]", NUMBER), ("level_highpassed", SIGNAL)]))
        L.append(code_line(0, [(");", SIGNAL)]))
        gap1 = gap(0.12)

        ema_decl = code_line(4, [("reg", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("ema;", SIGNAL)],
                              comment="// holds 0-4095 as a signed 13-bit value")
        L.append(ema_decl)
        gap2 = gap(0.1)

        level_s = code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("level_s", SIGNAL), ("=", SIGNAL), ("{1'b0,", NUMBER), ("level};", SIGNAL)])
        diff_l = code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("diff", SIGNAL), ("=", SIGNAL), ("level_s", SIGNAL), ("-", SIGNAL), ("ema;", SIGNAL)])
        step_l = code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("step", SIGNAL), ("=", SIGNAL), ("diff", SIGNAL), (">>>", SIGNAL), ("shift;", SIGNAL)])
        next_l = code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("ema_next", SIGNAL), ("=", SIGNAL), ("ema", SIGNAL), ("+", SIGNAL), ("step;", SIGNAL)])
        L += [level_s, diff_l, step_l, next_l]
        gap3 = gap(0.1)

        always1 = code_line(4, [("always", KEYWORD), ("@(posedge", KEYWORD), ("clk)", SIGNAL), ("begin", KEYWORD)])
        if1 = code_line(8, [("if", KEYWORD), ("(reset)", SIGNAL)])
        ema0 = code_line(12, [("ema", SIGNAL), ("<=", SIGNAL), ("13'sd0;", NUMBER)])
        else1 = code_line(8, [("else", KEYWORD), ("if", KEYWORD), ("(level_valid)", SIGNAL)])
        emanext = code_line(12, [("ema", SIGNAL), ("<=", SIGNAL), ("ema_next;", SIGNAL)])
        end1 = code_line(4, [("end", KEYWORD)])
        L += [always1, if1, ema0, else1, emanext, end1]
        gap4 = gap(0.12)

        cmt1 = code_line(4, [("// re-bias tracker: a separate, much slower EMA", COMMENT)])
        cmt2 = code_line(4, [("// (BIAS_SHIFT=12) - tracks only the long-term baseline", COMMENT)])
        L += [cmt1, cmt2]

        biasshift = code_line(4, [("localparam", KEYWORD), ("integer", KEYWORD), ("BIAS_SHIFT", NUMBER), ("=", SIGNAL), ("12;", NUMBER)])
        biasreg = code_line(4, [("reg", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("bias_ema;", SIGNAL)])
        biasdiff = code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("bias_diff", SIGNAL), ("=", SIGNAL), ("level_s", SIGNAL), ("-", SIGNAL), ("bias_ema;", SIGNAL)])
        biasstep = code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("bias_step", SIGNAL), ("=", SIGNAL), ("bias_diff", SIGNAL), (">>>", SIGNAL), ("BIAS_SHIFT;", NUMBER)])
        L += [biasshift, biasreg, biasdiff, biasstep]
        gap5 = gap(0.1)

        always2 = code_line(4, [("always", KEYWORD), ("@(posedge", KEYWORD), ("clk)", SIGNAL), ("begin", KEYWORD)])
        if2 = code_line(8, [("if", KEYWORD), ("(reset)", SIGNAL)])
        bias0 = code_line(12, [("bias_ema", SIGNAL), ("<=", SIGNAL), ("13'sd0;", NUMBER)])
        else2 = code_line(8, [("else", KEYWORD), ("if", KEYWORD), ("(level_valid)", SIGNAL)])
        biasnext = code_line(12, [("bias_ema", SIGNAL), ("<=", SIGNAL), ("bias_ema", SIGNAL), ("+", SIGNAL), ("bias_step;", SIGNAL)])
        end2 = code_line(4, [("end", KEYWORD)])
        L += [always2, if2, bias0, else2, biasnext, end2]
        gap6 = gap(0.12)

        hp_decl = code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[13:0]", NUMBER), ("hp_biased", SIGNAL), ("=", SIGNAL)])
        hp_body = code_line(8, [("{level_s[12],", SIGNAL), ("level_s}", SIGNAL), ("-", SIGNAL), ("{ema[12],", SIGNAL), ("ema}", SIGNAL), ("+", SIGNAL), ("{bias_ema[12],", SIGNAL), ("bias_ema};", SIGNAL)])
        L += [hp_decl, hp_body]
        gap7 = gap(0.1)

        clamp1 = code_line(4, [("assign", KEYWORD), ("level_highpassed", SIGNAL), ("=", SIGNAL), ("(hp_biased", SIGNAL), ("<", SIGNAL), ("0)", NUMBER), ("?", SIGNAL), ("12'd0", NUMBER), (":", SIGNAL)])
        clamp2 = code_line(30, [("(hp_biased", SIGNAL), (">", SIGNAL), ("4095)", NUMBER), ("?", SIGNAL), ("12'd4095", NUMBER), (":", SIGNAL)])
        clamp3 = code_line(35, [("hp_biased[11:0];", SIGNAL)])
        L += [clamp1, clamp2, clamp3]
        gap8 = gap(0.1)

        endmod = code_line(0, [("endmodule", KEYWORD)])
        L.append(endmod)

        layout_items = (
            L[0:8] + [gap1] + [ema_decl] + [gap2]
            + [level_s, diff_l, step_l, next_l] + [gap3]
            + [always1, if1, ema0, else1, emanext, end1] + [gap4]
            + [cmt1, cmt2, biasshift, biasreg, biasdiff, biasstep] + [gap5]
            + [always2, if2, bias0, else2, biasnext, end2] + [gap6]
            + [hp_decl, hp_body] + [gap7]
            + [clamp1, clamp2, clamp3] + [gap8]
            + [endmod]
        )
        # de-dup: items above were appended into L twice for some; rebuild cleanly
        full_code = VGroup(*[item["group"] for item in layout_items])
        full_code.arrange(DOWN, aligned_edge=LEFT, buff=0.035)

        avail_w = box.width - 0.5
        avail_h = box.height - 0.4
        scale = min(avail_w / full_code.width, avail_h / full_code.height, 1.0)
        full_code.scale(scale)
        full_code.move_to(box.get_center())

        # Code types itself out across "subtract it from the output"
        # (~14.4-16.3s) rather than popping in all at once.
        self.play(
            LaggedStart(*[FadeIn(item["group"], shift=UP * 0.03) for item in layout_items], lag_ratio=0.03),
            run_time=2.0,
        )

        # -----------------------------------------------------------
        # highlight helper (mirrors the mmnist code-scene pattern)
        # -----------------------------------------------------------
        RIGHT_X = 5.3

        def show_label(target, text, prev_rect, side=RIGHT, wrap=24, y_override=None):
            rect = SurroundingRectangle(
                target, color=YELLOW_HL, buff=0.05, stroke_width=0,
                fill_color=YELLOW_HL, fill_opacity=0.27,
            )
            if prev_rect is None:
                self.play(FadeIn(rect), run_time=0.4)
            else:
                self.play(Transform(prev_rect, rect), run_time=0.5)
                rect = prev_rect

            y = y_override if y_override is not None else max(-3.0, min(3.2, target.get_center()[1]))
            label = Text(textwrap.fill(text, width=wrap), font_size=18,
                         color=WHITE, line_spacing=0.9)
            x = RIGHT_X if side is RIGHT else -RIGHT_X
            label.move_to(RIGHT * x + UP * y)
            fit_frame(label)

            arrow = Arrow(
                rect.get_right() if side is RIGHT else rect.get_left(),
                label.get_left() + LEFT * 0.15 if side is RIGHT else label.get_right() + RIGHT * 0.15,
                buff=0.1, color=YELLOW_HL, stroke_width=3,
            )
            self.play(GrowArrow(arrow), FadeIn(label, shift=LEFT * 0.15 if side is RIGHT else RIGHT * 0.15), run_time=0.5)
            return rect, label, arrow

        def hide(mobs, run_time=0.4):
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)

        # --- Highlight A: the reused EMA recurrence ---------------------
        # This is the ONLY highlight shown on this first pass through the
        # code - narration here is "run the same lowpass filter again and
        # subtract it from the output. Whatever's left over is the
        # highpass... centered on zero." (~12.6-23.1s). The bias-tracker
        # and clamp code (further down in the module) get their own
        # narration only much later (~37-51s), covered by SECTION 5's
        # fast/slow waveform + formula recap instead of a second code
        # highlight here - showing those lines now, this early, would put
        # them on screen a full 15-20s before anyone starts talking about
        # them.
        targetA = VGroup(ema_decl["group"], level_s["group"], diff_l["group"], step_l["group"], next_l["group"])
        rect = SurroundingRectangle(
            targetA, color=YELLOW_HL, buff=0.05, stroke_width=0,
            fill_color=YELLOW_HL, fill_opacity=0.27,
        )
        # Rect lands on "the output." (~16.5-17.1s).
        self.play(FadeIn(rect), run_time=0.4)
        y = max(-3.0, min(3.2, targetA.get_center()[1]))
        labelA = Text(textwrap.fill(
            "same EMA recurrence as the lowpass filter - literally reused", width=24),
            font_size=18, color=WHITE, line_spacing=0.9)
        labelA.move_to(RIGHT * RIGHT_X + UP * y)
        fit_frame(labelA)
        arrowA = Arrow(rect.get_right(), labelA.get_left() + LEFT * 0.15,
                        buff=0.1, color=YELLOW_HL, stroke_width=3)
        # Arrow/label settle in slowly through "Whatever's left over is
        # the highpass" (~17.6-20.5s).
        self.play(GrowArrow(arrowA), FadeIn(labelA, shift=LEFT * 0.15), run_time=3.72)
        # A gentle pulse on the highlighted block itself carries through
        # "...except now the result is centered on zero." (~20.8-23.1s)
        # instead of sitting on a static frame.
        self.play(Indicate(targetA, color=YELLOW_HL, scale_factor=1.04), run_time=2.58)

        self.play(FadeOut(VGroup(title, box, full_code, rect, labelA, arrowA)), run_time=0.5)

        # =================================================================
        # SECTION 3 - the zero-mean problem
        # =================================================================
        # Narration: "And this whole project's display expects zero to
        # mean quiet, not negative." (~23.7-28.3s)
        title2 = Text("But highpass output is zero-mean...", font_size=30, color=WHITE)
        title2.to_edge(UP, buff=0.5)
        self.play(Write(title2), run_time=0.6)

        axis = NumberLine(x_range=[0, 4095, 1024], length=10.5, color=WHITE)
        axis.move_to(UP * 0.3)
        axis_label = Text("display range: 0 - 4095 (unsigned)", font_size=18, color=GRAY_TXT)
        axis_label.next_to(axis, UP, buff=0.75)
        ticks = VGroup(*[
            Text(str(v), font_size=14, color=GRAY_TXT).next_to(axis.number_to_point(v), DOWN, buff=0.12)
            for v in [0, 1024, 2048, 3072, 4095]
        ])
        # "display" (~25.0-25.3s)
        self.play(Create(axis), Write(axis_label), FadeIn(ticks), run_time=0.9)

        axis_center = axis.get_center()
        below_zone = Rectangle(width=axis.get_right()[0] - axis.get_left()[0], height=1.4,
                                fill_color=RED_C, fill_opacity=0.15, stroke_width=0)
        below_zone.move_to(axis_center + DOWN * 1.35)
        below_label = Text("negative half of the signal has nowhere to go", font_size=18, color=RED_C)
        below_label.next_to(below_zone, DOWN, buff=0.2)
        fit_frame(below_label)

        wave = FunctionGraph(lambda t: 0.7 * np.sin(2.4 * t), x_range=[-4.2, 4.2],
                              color=WHITE, stroke_width=3)
        wave.move_to(axis_center)
        # "expects zero to mean" (~25.3-26.8s)
        self.play(FadeIn(below_zone), FadeIn(below_label), run_time=1.0)
        # "quiet, not negative." (~26.8-28.3s) - wave keeps drawing through it.
        self.play(Create(wave), run_time=2.2)

        self.play(FadeOut(VGroup(title2, axis, axis_label, ticks, below_zone, below_label, wave)), run_time=0.58)

        # =================================================================
        # SECTION 4 - the wrong fix
        # Narration: "Adding a fixed offset back seemed reasonable. It was
        # wrong, because the sensor's real resting point isn't the middle
        # of the scale." (~28.8-36.6s)
        # =================================================================
        # "Adding a fix[ed] offset" (~28.8-29.5s)
        title3 = Text("Tried: a fixed +2048 re-bias", font_size=30, color=RED_C)
        title3.to_edge(UP, buff=0.5)
        self.play(Write(title3), run_time=0.66)

        axis2 = NumberLine(x_range=[0, 4095, 1024], length=10.5, color=WHITE)
        axis2.move_to(DOWN * 0.6)
        ticks2 = VGroup(*[
            Text(str(v), font_size=14, color=GRAY_TXT).next_to(axis2.number_to_point(v), DOWN, buff=0.12)
            for v in [0, 1024, 2048, 3072, 4095]
        ])
        # "back" (~29.5-30.7s)
        self.play(Create(axis2), FadeIn(ticks2), run_time=1.2)

        wrong_pt = axis2.number_to_point(IDLE_WRONG)
        wrong_dot = Dot(wrong_pt, radius=0.1, color=RED_C)
        wrong_label = Text(f"assumed idle: {IDLE_WRONG}", font_size=18, color=RED_C)
        wrong_label.next_to(wrong_dot, UP, buff=0.3)
        cross = Cross(stroke_color=RED_C, stroke_width=4).scale(0.18).move_to(wrong_dot)

        real_pt = axis2.number_to_point(IDLE_REAL)
        real_dot = Dot(real_pt, radius=0.1, color=GREEN_C)
        real_label = Text(f"real idle (measured, scene 06): {IDLE_REAL}", font_size=18, color=GREEN_C)
        real_label.next_to(real_dot, UP, buff=0.3)
        fit_frame(real_label)

        # "seemed reasonable." (~30.7-31.5s)
        self.play(FadeIn(wrong_dot, scale=0.5), FadeIn(wrong_label), run_time=0.84)
        # "It was wrong," (~31.9-32.5s, plus the short pause before it)
        self.play(Create(cross), run_time=0.98)
        # "...but the sensor's real resting point isn't the middle" (~32.9-36.2s)
        self.play(FadeIn(real_dot, scale=0.5), FadeIn(real_label), run_time=3.66)

        verdict = Text("mid-scale was assumed quiet - it isn't.", font_size=22, color=RED_C)
        verdict.next_to(axis2, DOWN, buff=0.9)
        fit_frame(verdict)
        # "of the scale." (~36.2-36.6s)
        self.play(FadeIn(verdict, shift=UP * 0.15), run_time=0.38)

        # "The actual fix," (~37.0-37.8s, plus the short pause before it)
        self.play(FadeOut(VGroup(title3, axis2, ticks2, wrong_dot, wrong_label, cross,
                                  real_dot, real_label, verdict)), run_time=0.42)

        # =================================================================
        # SECTION 5 - closing: the real fix, visualized
        # Narration: "The actual fix, a third tracker, deliberately much
        # slower than the filter itself. Slower than the signal it's
        # tracking means it only ever sees the baseline, never the thing
        # it's supposed to be measuring around." (~37.0-50.7s)
        # =================================================================
        title4 = Text("The fix: a third, much slower EMA", font_size=30, color=GREEN_C)
        title4.to_edge(UP, buff=0.5)
        self.play(Write(title4), run_time=0.86)

        fast = FunctionGraph(lambda t: 0.7 * np.sin(3.0 * t), x_range=[-4.5, 4.5],
                              color=WHITE, stroke_width=2.5)
        fast.move_to(UP * 0.6)
        fast_label = Text("live signal", font_size=16, color=GRAY_TXT)
        fast_label.move_to(fast.get_left() + LEFT * 0.9 + UP * 0.1)
        fit_frame(fast_label)

        slow = FunctionGraph(lambda t: 0.08 * np.sin(0.5 * t), x_range=[-4.5, 4.5],
                              color=GREEN_C, stroke_width=3.5)
        slow.move_to(UP * 0.6 + DOWN * 0.05)
        slow_label = Text("bias_ema - only the long-term baseline", font_size=16, color=GREEN_C)
        slow_label.next_to(fast, DOWN, buff=1.1)
        fit_frame(slow_label)

        # "a third tracker," (~38.2-38.9s)
        self.play(Create(fast), FadeIn(fast_label), run_time=1.06)
        # "deliberately much slower than the filter itself." (~39.4-42.7s)
        self.play(Create(slow), FadeIn(slow_label), run_time=3.76)

        # "Slower than the signal it's tracking means it only ever sees
        # the baseline, never the thing it's supposed to be measuring
        # around." (~42.9-50.7s) - the formula settles in slowly across
        # this whole final sentence instead of popping in and waiting.
        formula = Text("output = level - ema + bias_ema   (clamped 0-4095)",
                        font="Menlo", font_size=20, color=WHITE)
        formula.next_to(slow_label, DOWN, buff=0.5)
        fit_frame(formula)
        self.play(FadeIn(formula, shift=UP * 0.15), run_time=8.42)
