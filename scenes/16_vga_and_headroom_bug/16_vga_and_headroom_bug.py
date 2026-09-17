"""
Scene 16 - Drawing It on VGA

Real numbers / facts, pulled from the project's actual source
(FFTspectrum/VU.srcs/sources_1/new/):
  - vga_timing.v: 1024x768 @ 60Hz VESA DMT timing, driven directly off an
    exact 65MHz pixel clock (from the Clocking Wizard MMCM) - no internal
    divider, every clock edge is one pixel. (Earlier 640x480 version divided
    100MHz by 4 to approximate 25MHz; this design doesn't need to.)
  - waveform_view.v / fft_view.v: both traces and bars are stored in
    double-buffered ("ping-pong") memory - one buffer fills with new
    samples while the other is scanned out to the screen, and a
    `swap_pending` flip only takes effect at `is_frame_start`, so a frame
    already being drawn is never disturbed mid-scan.
  - waveform_view.v's own comment: the working full-height (HEIGHT=768)
    version used `>>2` (SHIFT=2) to map ADC codes into pixel rows, and that
    "clips above ADC code ~3068, reserving headroom" ratio is what actually
    made the trace look good/centered - it wasn't derived from first
    principles, it was tuned by eye at one specific height. Shrinking a view
    without re-deriving that ratio "blew the headroom the last two times
    HEIGHT changed" - this is the THIRD time this exact bug shape shows up.
  - The real fix (verbatim from waveform_view.v):
        localparam integer BASE_HEIGHT = 768;
        localparam integer BASE_SHIFT  = 2;
        localparam integer SHIFT = BASE_SHIFT + $clog2(BASE_HEIGHT / HEIGHT);
    Any power-of-two subdivision (full/half/quarter) re-derives the correct
    shift automatically.

Judgment call: SHIFT going from 2 -> 3 for a half-height view divides the
mapped pixel range by exactly 2, which conveniently matches "halve the
wave's on-screen amplitude to halve the box" 1:1 - so the fixed-vs-broken
visual literally uses that real relationship instead of an arbitrary number.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *


def sine_curve(center, half_amp, x_left, x_right, color, n_cycles=2.5, stroke_width=4):
    """A ParametricFunction sine trace (no Axes/MathTex needed)."""
    width = x_right - x_left

    def f(t):
        x = x_left + t * width
        y = center[1] + half_amp * np.sin(t * n_cycles * TAU)
        return np.array([x, y, 0])

    curve = ParametricFunction(f, t_range=[0, 1, 0.01], color=color, stroke_width=stroke_width)
    return curve


class VGAAndHeadroomBug(Scene):
    def construct(self):
        set_bg(self)

        # ==================================================================
        # BEAT 0 - Title
        # ==================================================================
        title = Text("Drawing It on VGA", font_size=40, color=WHITE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.6)

        # ==================================================================
        # BEAT 1 - VGA raster scan: one clock edge, one pixel
        # narration: "Every pixel on this display gets decided off an
        # exact 65 megahertz pixel clock." (0-5.76)
        # ==================================================================
        screen = Rectangle(width=6.4, height=4.4, color=WHITE, stroke_width=2,
                            fill_color=BOX_FILL, fill_opacity=1)
        screen.move_to(DOWN * 0.35 + LEFT * 0.6)
        res_label = Text("1024 x 768", font_size=20, color=GRAY_TXT)
        res_label.next_to(screen, DOWN, buff=0.2)

        clk_box = Square(side_length=0.5, color=WHITE, fill_color=BOX_FILL, fill_opacity=1)
        clk_box.move_to(RIGHT * 4.9 + UP * 2.0)
        clk_label_top = Text("CLK", font_size=16, color=WHITE).move_to(clk_box.get_center())
        clk_note = Text("65MHz -> 1 pixel / edge", font_size=20, color=YELLOW_HL)
        clk_note.next_to(clk_box, DOWN, buff=0.3)
        fit_frame(clk_note)

        self.play(FadeIn(screen), Write(res_label), run_time=0.6)
        self.play(FadeIn(clk_box), Write(clk_label_top), FadeIn(clk_note, shift=UP * 0.1), run_time=0.7)

        # a handful of scan lines, drawn left-to-right, stepping down --
        # suggests the raster without literally drawing 768 lines
        n_rows = 6
        top_y = screen.get_top()[1] - 0.35
        bot_y = screen.get_bottom()[1] + 0.35
        left_x = screen.get_left()[0] + 0.25
        right_x = screen.get_right()[0] - 0.25

        dot = Dot(radius=0.08, color=GREEN_C)
        dot.move_to([left_x, top_y, 0])
        self.play(FadeIn(dot, scale=0.5), Indicate(clk_box, color=YELLOW_HL, scale_factor=1.15), run_time=0.3)

        scan_lines = VGroup()
        for i in range(n_rows):
            y = top_y - i * (top_y - bot_y) / (n_rows - 1)
            line = Line([left_x, y, 0], [right_x, y, 0], color=GREEN_C, stroke_width=2, stroke_opacity=0.85)
            self.play(
                Create(line),
                dot.animate.move_to([right_x, y, 0]),
                Indicate(clk_box, color=YELLOW_HL, scale_factor=1.1),
                run_time=0.26,
            )
            scan_lines.add(line)
            if i < n_rows - 1:
                next_y = top_y - (i + 1) * (top_y - bot_y) / (n_rows - 1)
                self.play(dot.animate.move_to([left_x, next_y, 0]), run_time=0.11)

        beam_note = Text("line by line, left to right - no fractional divider", font_size=20, color=WHITE)
        beam_note.next_to(screen, UP, buff=0.15)
        fit_frame(beam_note)
        self.play(FadeIn(beam_note, shift=UP * 0.1), run_time=1.0)

        self.play(FadeOut(VGroup(screen, res_label, clk_box, clk_label_top, clk_note,
                                  dot, scan_lines, beam_note)), run_time=0.5)

        # ==================================================================
        # BEAT 2 - Ping-pong double buffering
        # ==================================================================
        # narration: "And every trace and every bar lives in
        # double-buffered memory." (5.76-10.04)
        subtitle1 = Text("Every trace and bar: double-buffered", font_size=28, color=WHITE)
        subtitle1.next_to(title, DOWN, buff=0.35)
        self.play(FadeOut(title), FadeIn(subtitle1), run_time=0.4)

        buf_a = RoundedRectangle(width=2.8, height=3.4, corner_radius=0.12,
                                  fill_color=BOX_FILL, fill_opacity=1, stroke_color=GREEN_C, stroke_width=3)
        buf_a.move_to(LEFT * 3.0 + DOWN * 0.3)
        buf_b = RoundedRectangle(width=2.8, height=3.4, corner_radius=0.12,
                                  fill_color=BOX_FILL, fill_opacity=1, stroke_color=BLUE_C, stroke_width=3)
        buf_b.move_to(RIGHT * 3.0 + DOWN * 0.3)

        label_a = Text("buffer A", font_size=20, color=WHITE).next_to(buf_a, UP, buff=0.15)
        label_b = Text("buffer B", font_size=20, color=WHITE).next_to(buf_b, UP, buff=0.15)
        state_a = Text("FILLING", font_size=22, color=GREEN_C).move_to(buf_a.get_top() + DOWN * 0.4)
        state_b = Text("READING", font_size=22, color=BLUE_C).move_to(buf_b.get_top() + DOWN * 0.4)

        self.play(FadeIn(buf_a), FadeIn(buf_b), Write(label_a), Write(label_b), run_time=2.0)
        self.play(FadeIn(state_a, shift=DOWN * 0.1), FadeIn(state_b, shift=DOWN * 0.1), run_time=2.0)

        # filling: samples popping in (offsets kept within buf_a's half-width
        # of 1.4, so no dot renders past the box edge)
        fill_dots = VGroup(*[
            Dot(radius=0.06, color=GREEN_C).move_to(
                buf_a.get_center() + DOWN * 0.6 + RIGHT * (0.38 * (i - 2.5)) + UP * 0.15 * np.sin(i)
            ) for i in range(6)
        ])
        # reading: a sweep line scanning down, feeding an arrow out toward the screen
        out_arrow = Arrow(buf_b.get_right(), buf_b.get_right() + RIGHT * 1.0, buff=0.1,
                           color=BLUE_C, stroke_width=3)
        out_label = Text("to screen", font_size=16, color=BLUE_C).next_to(out_arrow, RIGHT, buff=0.15)
        read_sweep = Line(buf_b.get_left() + UP * 1.1 + RIGHT * 0.15, buf_b.get_right() + UP * 1.1 + LEFT * 0.15,
                           color=BLUE_C, stroke_width=3)

        # narration: "One half fills with new data while the other half
        # feeds the screen." (10.38-14.54) - the sweep line's downward
        # motion is stretched to visibly travel across this whole phrase.
        self.play(LaggedStart(*[FadeIn(d, scale=0.4) for d in fill_dots], lag_ratio=0.15), run_time=1.5)
        self.play(Create(out_arrow), FadeIn(out_label), run_time=0.7)
        self.play(Create(read_sweep), run_time=0.6)
        self.play(read_sweep.animate.shift(DOWN * 1.6), run_time=1.36)

        # narration: "And they only ever swap at the clean buffer frame
        # boundary." (15.12-19.66)
        swap_note = Text("swap only at a frame boundary", font_size=22, color=YELLOW_HL)
        swap_note.next_to(VGroup(buf_a, buf_b), DOWN, buff=0.5)
        fit_frame(swap_note)
        self.play(FadeIn(swap_note, shift=UP * 0.1), run_time=1.6)

        # swap animation: roles trade
        swap_arrow_top = CurvedArrow(buf_a.get_top() + UP * 0.05, buf_b.get_top() + UP * 0.05,
                                      color=WHITE, stroke_width=3)
        swap_arrow_bot = CurvedArrow(buf_b.get_bottom() + DOWN * 0.05, buf_a.get_bottom() + DOWN * 0.05,
                                      color=WHITE, stroke_width=3)
        self.play(Create(swap_arrow_top), Create(swap_arrow_bot), run_time=1.3)
        new_state_a = Text("READING", font_size=22, color=BLUE_C).move_to(state_a.get_center())
        new_state_b = Text("FILLING", font_size=22, color=GREEN_C).move_to(state_b.get_center())
        self.play(
            Transform(state_a, new_state_a),
            Transform(state_b, new_state_b),
            FadeOut(fill_dots), FadeOut(read_sweep),
            run_time=1.0,
        )
        self.play(FadeOut(swap_arrow_top), FadeOut(swap_arrow_bot), run_time=0.64)

        # narration: "So nothing made drawn ever tears." (20.06-23.02) -
        # written slowly across the phrase instead of popping in and
        # freezing.
        never_torn = Text("a frame already being drawn is never disturbed mid-scan", font_size=20, color=GREEN_C)
        never_torn.next_to(swap_note, DOWN, buff=0.3)
        fit_frame(never_torn)
        self.play(Write(never_torn), run_time=2.56)

        self.play(FadeOut(VGroup(subtitle1, buf_a, buf_b, label_a, label_b, state_a, state_b,
                                  out_arrow, out_label, swap_note, never_torn)), run_time=0.6)

        # ==================================================================
        # BEAT 3 - The headroom bug, in disguise 3 times
        # ==================================================================
        subtitle2 = Text("The headroom bug, three disguises", font_size=28, color=WHITE)
        subtitle2.to_edge(UP, buff=0.5)
        self.play(Write(subtitle2), run_time=0.5)

        # full-height view box (tuned correctly)
        box_center = LEFT * 3.6 + DOWN * 0.2
        full_h = 4.6
        box = Rectangle(width=3.0, height=full_h, color=WHITE, stroke_width=2,
                         fill_color=BOX_FILL, fill_opacity=1)
        box.move_to(box_center)
        box_label = Text("HEIGHT=768  shift=2", font_size=18, color=GRAY_TXT)
        box_label.next_to(box, DOWN, buff=0.2)

        full_amp = full_h / 2 * 0.72
        wave = sine_curve(box_center, full_amp, box.get_left()[0] + 0.1, box.get_right()[0] - 0.1,
                           GREEN_C, n_cycles=2.5)

        fits_label = Text("fits cleanly", font_size=20, color=GREEN_C)
        fits_label.next_to(box, UP, buff=0.2)

        # narration: "Shrink a view's height without rescaling what's
        # drawn inside it." (23.36-28.68) - the wave draws itself slowly
        # and the shrink-transform is stretched into a visibly slow,
        # deliberate resize rather than a snap.
        self.play(FadeIn(box), Write(box_label), run_time=0.4)
        self.play(Create(wave), run_time=1.9)
        self.play(FadeIn(fits_label, shift=DOWN * 0.1), run_time=0.6)

        # shrink to half-height WITHOUT rescaling the wave -> clips
        half_h = full_h / 2
        new_box = Rectangle(width=3.0, height=half_h, color=RED_C, stroke_width=2,
                             fill_color=BOX_FILL, fill_opacity=1)
        new_box.move_to(box_center)

        self.play(
            FadeOut(fits_label),
            Transform(box, new_box),
            box_label.animate.next_to(new_box, DOWN, buff=0.2),
            run_time=2.42,
        )
        # wave amplitude is untouched - same curve, now overflowing the halved box
        clip_label = Text("shrunk to half-height - SHIFT not updated", font_size=18, color=RED_C)
        clip_label.next_to(box, DOWN, buff=0.55)
        fit_frame(clip_label)
        overflow_top = Rectangle(width=3.0, height=(full_amp - half_h / 2), color=RED_C,
                                  fill_color=RED_C, fill_opacity=0.25, stroke_width=0)
        overflow_top.move_to(box_center + UP * (half_h / 2 + (full_amp - half_h / 2) / 2))
        overflow_bot = overflow_top.copy().move_to(box_center + DOWN * (half_h / 2 + (full_amp - half_h / 2) / 2))
        clips_label = Text("CLIPS", font_size=22, color=RED_C)
        clips_label.next_to(overflow_top, UP, buff=0.1)
        fit_frame(clips_label)

        # narration: "And the signal blows straight through the edge."
        # (28.96-31.68)
        self.play(wave.animate.set_color(RED_C), run_time=0.9)
        self.play(FadeIn(overflow_top), FadeIn(overflow_bot), FadeIn(clip_label), FadeIn(clips_label), run_time=1.82)

        three_times = Text("this exact bug shape: 3 times in this project", font_size=20, color=RED_C)
        three_times.next_to(clip_label, DOWN, buff=0.25)
        fit_frame(three_times)
        self.play(FadeIn(three_times, shift=UP * 0.1), run_time=0.4)
        self.play(FadeOut(three_times), run_time=0.3)

        # ==================================================================
        # BEAT 4 - The fix formula
        # ==================================================================
        formula = Text("SHIFT = BASE_SHIFT + log2(BASE_HEIGHT / HEIGHT)", font_size=26, color=WHITE)
        formula.move_to(RIGHT * 3.4 + UP * 1.6)
        fit_frame(formula)
        formula_sub = Text("tuned once at 768px (shift=2) - any power-of-two\nsubdivision re-derives the right shift automatically",
                            font_size=17, color=GRAY_TXT, line_spacing=1.1)
        formula_sub.next_to(formula, DOWN, buff=0.3)
        fit_frame(formula_sub)

        # narration: "Drive the scale from actual height every time."
        # (31.68-34.56)
        self.play(Write(formula), run_time=1.3)
        self.play(FadeIn(formula_sub, shift=UP * 0.1), run_time=1.58)

        # ==================================================================
        # BEAT 5 - Apply the corrected shift: fits again
        # narration: "So resizing a view can never quietly reintroduce a
        # bug..." (34.82 onward) - the fix visibly, slowly reshapes the
        # box/wave back to a clean fit rather than snapping instantly.
        # ==================================================================
        fixed_box = Rectangle(width=3.0, height=half_h, color=GREEN_C, stroke_width=2,
                               fill_color=BOX_FILL, fill_opacity=1)
        fixed_box.move_to(box_center)
        fixed_wave = sine_curve(box_center, full_amp / 2, box.get_left()[0] + 0.1, box.get_right()[0] - 0.1,
                                 GREEN_C, n_cycles=2.5)
        fixed_label = Text("HEIGHT=384  shift=3 (auto)", font_size=18, color=GRAY_TXT)
        fixed_label.next_to(fixed_box, DOWN, buff=0.2)
        fits_again = Text("fits cleanly again", font_size=20, color=GREEN_C)
        fits_again.next_to(fixed_box, UP, buff=0.2)

        self.play(
            FadeOut(VGroup(overflow_top, overflow_bot, clips_label, clip_label)),
            Transform(box, fixed_box),
            Transform(wave, fixed_wave),
            Transform(box_label, fixed_label),
            run_time=1.8,
        )
        self.play(FadeIn(fits_again, shift=DOWN * 0.1), run_time=1.0)

        # ==================================================================
        # BEAT 6 - Close: sets up the build-log scene
        # narration: "...reintroduce a bug that I have already fixed."
        # (through 40.46, scene ends 40.86)
        # IMPORTANT: no trailing FadeOut here, and no wait() padding - this
        # scene gets freeze-hold padded to match the real narration length
        # in the final assembly (same pitfall fixed on scene 19's
        # credits). A trailing FadeOut would mean the freeze-hold lands on
        # an empty black frame instead of the closing line, so the
        # closing text's own fade-in is stretched to cover the rest of
        # the narration and the scene simply ends with it on screen.
        # ==================================================================
        self.play(FadeOut(VGroup(box, wave, box_label, fits_again, formula, formula_sub, subtitle2)),
                   run_time=0.5)

        closing = Text("Same bug, three disguises - one fix that can't be forgotten again",
                        font_size=26, color=WHITE)
        closing.move_to(ORIGIN)
        fit_frame(closing)
        self.play(FadeIn(closing, shift=UP * 0.15), run_time=3.87)
