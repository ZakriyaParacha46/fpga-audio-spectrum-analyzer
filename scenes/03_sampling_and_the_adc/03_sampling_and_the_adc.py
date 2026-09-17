"""
Scene 03 - Sampling & the ADC

Narrative: to get a continuous voltage into the FPGA you have to sample it
(measure at regular instants) and quantize it (round each measurement to the
nearest value a fixed number of bits can represent). This board's ADC is
12-bit: every sample becomes an integer 0-4095. 0V -> code 0, the top of the
ADC's input range -> code 4095. Everything downstream is these plain
integers - the waveform is gone, replaced by a stream of numbers, one every
1.038 microseconds.

Beats:
  1. smooth continuous curve (carried over from scene 02)
  2. vertical sample-time gridlines + dots landing on the curve (time axis
     discretized)
  3. zoom on one sample: a quantization ladder near it, the point snapping
     to the nearest rung (amplitude axis discretized)
  4. the curve is gone - replaced by a plain stream of integers
  5. closing caption: 12-bit, codes 0-4095, ~1.038us/sample

Retiming note: beats are stretched via run_time= on the self.play() calls
so the motion itself is slow/continuous across each narration sentence
(e.g. the ladder reveal plays out gradually across the whole sentence it
illustrates, and a couple of Indicate() pulses fill sentences that don't
introduce a new visual so the screen never just freezes). self.wait() is
used ONLY for the real, short silences between sentences in the transcript.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *

ADC_BITS = 12
ADC_MAX_CODE = 4095
SAMPLE_PERIOD_US = 1.038

# a handful of "real-looking" sample codes for the ticking stream, centered
# near mid-scale like the voltage-divider scene's idle code (~3276)
STREAM_CODES = [2867, 2901, 2889, 2913, 2878, 2855, 2902, 2867, 2841, 2896]


def signal(x):
    return 0.5 + 0.32 * np.sin(x * 1.35) + 0.06 * np.sin(x * 3.1)


class SamplingAndTheADC(Scene):
    def construct(self):
        set_bg(self)

        # Narration (0.08-0.76s): "Here is the problem,"
        title = Text("Sampling & the ADC", font_size=40, color=WHITE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.70)
        self.wait(0.46)  # genuine gap to "FPGA cannot touch..." (1.16s)

        # ------------------------------------------------------------
        # Beat 1: smooth continuous curve, carried over from scene 02.
        # Narration (1.16-5.14s): "FPGA cannot touch the continuous
        # voltage at all." - axes/curve/label draw slowly across the
        # whole line instead of popping in and freezing.
        # ------------------------------------------------------------
        axes = Axes(
            x_range=[0, 6.4, 1], y_range=[0, 1.0, 0.25],
            x_length=10.6, y_length=3.4,
            axis_config={"color": GRAY_TXT, "include_ticks": False, "stroke_width": 2},
            tips=False,
        )
        axes.move_to(DOWN * 0.55)

        curve = axes.plot(signal, x_range=[0, 6.4], color=GREEN_C, stroke_width=4)
        continuous_label = Text("a continuous voltage", font_size=20, color=GRAY_TXT)
        continuous_label.next_to(axes, UP, buff=0.25)
        fit_frame(continuous_label)

        self.play(Create(axes), run_time=1.49)
        self.play(Create(curve), Write(continuous_label), run_time=2.49)
        self.wait(0.20)  # genuine gap to "So somewhere," (5.34s)

        # Narration (5.34-6.32s): "So somewhere," - slow fade-out fills
        # the line instead of a quick cut + hold.
        self.play(FadeOut(continuous_label), run_time=0.98)
        self.wait(0.62)  # genuine gap to "the smooth curve..." (6.94s)

        # ------------------------------------------------------------
        # Beat 2: sample-time gridlines + dots landing on the curve.
        # Narration (6.94-9.40s): "the smooth curve has to be chopped
        # up," - the gridlines appearing (staggered, slow) IS the
        # "chopping" being described.
        # ------------------------------------------------------------
        sample_xs = np.arange(0.4, 6.4, 0.55)
        gridlines = VGroup(*[
            DashedLine(
                axes.c2p(x, 0), axes.c2p(x, 1.0),
                color=GRAY_TXT, stroke_width=1.5, dash_length=0.08,
            ).set_opacity(0.55)
            for x in sample_xs
        ])
        sample_dots = VGroup(*[
            Dot(axes.c2p(x, signal(x)), radius=0.065, color=YELLOW_HL)
            for x in sample_xs
        ])
        time_label = Text("sampled at regular instants in time", font_size=20, color=YELLOW_HL)
        time_label.next_to(axes, UP, buff=0.25)
        fit_frame(time_label)

        self.play(Create(gridlines, lag_ratio=0.05), run_time=2.46)
        self.wait(0.38)  # genuine gap to "measured at regular instances" (9.78s)

        # Narration (9.78-11.10s): "measured at regular instances" - the
        # dots landing on the curve are this clause.
        self.play(FadeIn(sample_dots, lag_ratio=0.1), Write(time_label), run_time=1.32)

        # ------------------------------------------------------------
        # Beat 3: zoom on one sample - quantization ladder + rounding.
        # Narration (11.10-17.14s): "...and each measurement rounded to
        # the nearest value a fixed number of bits can hold." - the
        # whole ladder build-and-snap plays out slowly across this line.
        # ------------------------------------------------------------
        pick_x = sample_xs[4]
        pick_y = signal(pick_x)
        pick_dot = sample_dots[4]

        self.play(Indicate(pick_dot, color=WHITE, scale_factor=1.8), run_time=0.86)

        fade_group = VGroup(axes, curve, gridlines, sample_dots, time_label)
        self.play(fade_group.animate.set_opacity(0.15), run_time=0.72)

        # small zoomed panel: a vertical ladder of quantization levels
        # around the picked sample's amplitude
        ladder_x = 4.6
        ladder_bottom = -1.7
        ladder_top = 1.7
        n_rungs = 9
        true_frac = 0.47  # where the "true" analog value sits, between rungs
        rung_ys = np.linspace(ladder_bottom, ladder_top, n_rungs)
        snap_index = 4  # index of the rung it rounds to
        true_y = rung_ys[snap_index] + true_frac * (rung_ys[snap_index + 1] - rung_ys[snap_index])

        panel_bg = RoundedRectangle(width=3.6, height=4.3, corner_radius=0.12,
                                     fill_color=BOX_FILL, fill_opacity=0.95,
                                     stroke_color=BOX_BORDER, stroke_width=2)
        panel_bg.move_to(RIGHT * ladder_x + UP * 0.05)

        # rung lines are inset enough from the box's left edge to leave room
        # for the code labels to sit INSIDE the panel, anchored to each
        # line's actual left endpoint (not the line's full-width bounding
        # box, which previously pushed the labels out past the box edge)
        rungs = VGroup(*[
            Line(panel_bg.get_left() + RIGHT * 0.9, panel_bg.get_right() + LEFT * 0.3, color=GRAY_TXT, stroke_width=2)
            .move_to([ladder_x, y, 0])
            for y in rung_ys
        ])
        codes_near = [2841 + 64 * i for i in range(n_rungs)]
        rung_labels = VGroup(*[
            Text(str(codes_near[i]), font_size=14, color=GRAY_TXT).next_to(rungs[i].get_start(), LEFT, buff=0.1)
            for i in range(n_rungs)
        ])

        ladder_title = Text("quantization levels (zoomed in)", font_size=18, color=WHITE)
        ladder_title.next_to(panel_bg, UP, buff=0.2)
        fit_frame(ladder_title)

        self.play(FadeIn(panel_bg), Write(ladder_title), run_time=0.72)
        self.play(Create(rungs), FadeIn(rung_labels, lag_ratio=0.1), run_time=1.01)

        true_pt = np.array([ladder_x, true_y, 0])
        true_dot = Dot(true_pt, radius=0.08, color=YELLOW_HL)
        true_label = Text("true value", font_size=15, color=YELLOW_HL)
        true_label.next_to(true_dot, RIGHT, buff=0.2)
        fit_frame(true_label)

        self.play(FadeIn(true_dot, scale=0.5), FadeIn(true_label), run_time=0.72)

        snap_pt = np.array([ladder_x, rung_ys[snap_index], 0])
        snap_dot = Dot(snap_pt, radius=0.09, color=GREEN_C)
        snap_arrow = Arrow(true_pt, snap_pt, buff=0.08, color=GREEN_C, stroke_width=3, max_tip_length_to_length_ratio=0.35)

        self.play(GrowArrow(snap_arrow), run_time=0.72)
        self.play(FadeOut(true_dot), FadeIn(snap_dot, scale=0.6), run_time=0.58)

        rounded_label = Text(f"rounds to code {codes_near[snap_index]}", font_size=17, color=GREEN_C)
        rounded_label.next_to(panel_bg, DOWN, buff=0.25)
        fit_frame(rounded_label)
        self.play(FadeOut(true_label), Write(rounded_label), run_time=0.72)
        self.wait(0.78)  # genuine gap to "On this board..." (17.92s)

        # Narration (17.92-20.74s): "On this board, that's a 12-bit
        # ADC." - no new visual is introduced, so a slow Indicate on the
        # integer codes already on screen keeps the frame alive instead
        # of freezing (these codes ARE the 12-bit quantization).
        self.play(Indicate(rung_labels, color=YELLOW_HL, scale_factor=1.15), run_time=2.81)
        self.wait(0.88)  # genuine gap to "Every sample becomes..." (21.62s)

        # Narration (21.62-26.24s): "Every sample becomes one integer,
        # somewhere between 0 to 4095." - slow Indicate on the concrete
        # rounded code, which IS "one integer."
        self.play(Indicate(rounded_label, color=GREEN_C, scale_factor=1.2), run_time=4.62)
        self.wait(0.80)  # genuine gap to "The instant this happens..." (27.04s)

        # ------------------------------------------------------------
        # Beat 4: the curve is gone - replaced by a stream of integers.
        # Narration (27.04-30.64s): "The instant this happens, the
        # waveform is gone for good, replaced by a plain stream of
        # numbers" - fade-out/fade-in stretched across the whole line.
        # ------------------------------------------------------------
        zoom_group = VGroup(panel_bg, rungs, rung_labels, ladder_title,
                             snap_dot, snap_arrow, rounded_label)
        self.play(FadeOut(zoom_group), FadeOut(fade_group), run_time=1.66)

        gone_label = Text("the waveform is gone --", font_size=24, color=WHITE)
        gone_label2 = Text("replaced by a stream of plain integers", font_size=24, color=GREEN_C)
        gone_group = VGroup(gone_label, gone_label2).arrange(DOWN, buff=0.2)
        gone_group.move_to(UP * 1.3)
        self.play(FadeIn(gone_group, shift=UP * 0.15), run_time=1.94)
        self.wait(0.40)  # genuine gap to "One new integer..." (31.04s)

        # Narration (31.04-34.98s): "One new integer every 1.038
        # microseconds," - the ticking number stream + rate label ARE
        # this sentence, stretched to fill it exactly.
        stream_y = -0.4
        number_items = [Text(str(code), font="Menlo", font_size=26, color=WHITE)
                         for code in STREAM_CODES[:6]]
        ellipsis = Text("...", font="Menlo", font_size=26, color=GRAY_TXT)
        shown = VGroup(*number_items, ellipsis).arrange(RIGHT, buff=0.35)
        shown.move_to([0, stream_y, 0])
        fit_frame(shown)

        self.play(AnimationGroup(*[FadeIn(t, shift=UP * 0.1) for t in number_items],
                                  lag_ratio=0.35), run_time=2.33)
        self.play(FadeIn(ellipsis), run_time=0.54)

        rate_label = Text("one number every 1.038 microseconds", font_size=20, color=YELLOW_HL)
        rate_label.next_to(shown, DOWN, buff=0.55)
        fit_frame(rate_label)
        self.play(FadeIn(rate_label, shift=UP * 0.1), run_time=1.07)
        self.wait(0.22)  # genuine gap to "forever whether..." (35.20s)

        # ------------------------------------------------------------
        # Beat 5: closing caption with the real numbers.
        # Narration (35.20s onward): "forever whether you're listening
        # or not." - final summary card lands as the scene's closing
        # thought; this sequence's natural run_times already fill the
        # remaining span exactly, no padding needed.
        # ------------------------------------------------------------
        self.play(FadeOut(VGroup(gone_group, shown, rate_label)), run_time=0.5)

        closing1 = Text("12-bit ADC  ·  codes 0 - 4095", font_size=30, color=WHITE)
        closing2 = Text("~1.038 microseconds per sample", font_size=26, color=GREEN_C)
        closing_group = VGroup(closing1, closing2).arrange(DOWN, buff=0.35)
        closing_group.move_to(ORIGIN)
        fit_frame(closing_group)

        self.play(Write(closing1), run_time=0.6)
        self.play(FadeIn(closing2, shift=UP * 0.1), run_time=0.58)
