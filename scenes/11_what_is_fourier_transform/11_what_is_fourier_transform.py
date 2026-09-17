"""
Scene 11 - What Is a Fourier Transform

Concept beat, no real project numbers involved. Narrative:
  1. Any messy signal can be built by adding pure sine waves of different
     frequency/amplitude/phase together - and we watch that combination
     happen live, one wave morphing into the sum as the next sine is added.
  2. Zoom out into 3D: a single complex waveform is really a stack of pure
     sine waves, one per frequency, receding into the distance. The Fourier
     transform is just the process of pulling that stack back out.
  3. This sets up the spectrum display later in the video - it's not a
     new kind of measurement, just decomposition of what's already there.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *

# ---------------------------------------------------------------------------
# The three component waves (arbitrary units, domain [0, 8])
# ---------------------------------------------------------------------------
DOMAIN = [0, 8]

def make_wave(k, amp, phase):
    return lambda x: amp * np.sin(2 * np.pi * k * x / 8 + phase)

WAVE1 = make_wave(1, 1.00, 0.0)   # low frequency, big amplitude
WAVE2 = make_wave(3, 0.55, 0.4)   # mid frequency
WAVE3 = make_wave(6, 0.35, 1.0)   # high frequency, small amplitude

COMBINED = lambda x: WAVE1(x) + WAVE2(x) + WAVE3(x)

COMP_COLORS = [GREEN_C, BLUE_C, PURPLE_C]
COMP_WAVES = [WAVE1, WAVE2, WAVE3]
COMP_LABELS = ["low frequency", "mid frequency", "high frequency"]
COMP_AMPS = [1.00, 0.55, 0.35]


def small_axes():
    return Axes(
        x_range=[0, 8, 2], y_range=[-1.3, 1.3, 1],
        x_length=7.4, y_length=1.3,
        axis_config={"color": GRAY_TXT, "stroke_width": 1.5, "include_tip": False},
    )


class WhatIsFourierTransform(ThreeDScene):
    def construct(self):
        set_bg(self)

        # ------------------------------------------------------------
        # Title
        # ------------------------------------------------------------
        # Narration: "Here's the idea that makes the rest of the video
        # possible." (~0.2-2.9s). A slow Write draws the title out across
        # the whole sentence instead of popping in and freezing.
        #
        # Retiming note: every self.wait() in this construct() is either
        # removed in favor of a longer run_time= on the play that's
        # already animating something (so the picture keeps moving
        # smoothly through the narration instead of freezing on a static
        # frame), or - for the ambient 3D camera drift near the end - a
        # wait during a rotation that's still actively turning the camera,
        # which is motion, not a freeze.
        title = Text("What Is a Fourier Transform?", font_size=38, color=WHITE)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=2.86)

        # ------------------------------------------------------------
        # Beat 1: three pure sine waves, stacked, distinct colors.
        # Narration: "Almost any sound you've ever heard is secretly a
        # chord." (~3.5-6.4s) lands on wave 1; "Any signal, no matter how
        # messy, you can build by adding together pure sine waves"
        # (~7.1-11.3s) on wave 2; "...at different frequencies,
        # amplitudes, and phases." (~11.3-14.2s) on wave 3.
        # ------------------------------------------------------------
        row_ys = [2.15, 0.35, -1.45]
        comp_axes = VGroup()
        comp_plots = VGroup()
        comp_labels = VGroup()

        wave_axis_rt = [1.0, 0.9, 1.5]
        wave_plot_rt = [2.5, 1.54, 3.92]

        for i in range(3):
            ax = small_axes()
            ax.move_to(UP * row_ys[i])
            plot = ax.plot(COMP_WAVES[i], color=COMP_COLORS[i], stroke_width=3.5)
            dot = Dot(radius=0.07, color=COMP_COLORS[i])
            lbl = Text(COMP_LABELS[i], font_size=18, color=COMP_COLORS[i])
            grp = VGroup(dot, lbl).arrange(RIGHT, buff=0.15)
            grp.next_to(ax, RIGHT, buff=0.3)
            fit_frame(grp)

            comp_axes.add(ax)
            comp_plots.add(plot)
            comp_labels.add(grp)

            self.play(Create(ax), run_time=wave_axis_rt[i])
            self.play(Create(plot), FadeIn(grp), run_time=wave_plot_rt[i])

        plus1 = Text("+", font_size=32, color=WHITE).move_to(
            LEFT * 4.5 + UP * (row_ys[0] + row_ys[1]) / 2)
        plus2 = Text("+", font_size=32, color=WHITE).move_to(
            LEFT * 4.5 + UP * (row_ys[1] + row_ys[2]) / 2)
        # Bridges into "Watch three clean tones fold together..." (~14.2s)
        self.play(FadeIn(plus1), FadeIn(plus2), run_time=0.6)

        # ------------------------------------------------------------
        # Beat 2: LIVE combination - watch the sines actually sum
        # ------------------------------------------------------------
        stacked_group = VGroup(comp_axes, comp_plots, comp_labels, plus1, plus2)
        self.play(FadeOut(stacked_group), FadeOut(title), run_time=0.4)

        add_title = Text("Watch them add together...", font_size=32, color=WHITE)
        add_title.to_edge(UP, buff=0.5)
        self.play(Write(add_title), run_time=0.5)

        big_axes = Axes(
            x_range=[0, 8, 2], y_range=[-2.2, 2.2, 1],
            x_length=10.5, y_length=3.2,
            axis_config={"color": GRAY_TXT, "stroke_width": 2, "include_tip": False},
        )
        big_axes.move_to(DOWN * 0.55)
        self.play(Create(big_axes), run_time=0.5)

        # weight trackers - ramping a tracker 0 -> 1 fades a wave's
        # contribution into the running sum, redrawn every frame so the
        # combined curve visibly *morphs* as each wave is folded in.
        w1 = ValueTracker(1.0)
        w2 = ValueTracker(0.0)
        w3 = ValueTracker(0.0)
        weights = [w1, w2, w3]

        def running_sum(x):
            total = 0.0
            for w, wave in zip(weights, COMP_WAVES):
                total += w.get_value() * wave(x)
            return total

        combined_plot = always_redraw(
            lambda: big_axes.plot(running_sum, color=WHITE, stroke_width=4)
        )

        # legend chips that light up as each wave joins the sum
        chips = VGroup()
        for i in range(3):
            dot = Dot(radius=0.08, color=COMP_COLORS[i], fill_opacity=0.25)
            lbl = Text(COMP_LABELS[i].split()[0], font_size=16, color=COMP_COLORS[i])
            chip = VGroup(dot, lbl).arrange(RIGHT, buff=0.12)
            chips.add(chip)
        chips.arrange(RIGHT, buff=0.6)
        chips.next_to(big_axes, UP, buff=0.25)
        fit_frame(chips)
        for chip in chips:
            chip[0].set_fill(opacity=0.25)

        self.play(FadeIn(chips), run_time=0.6)
        self.add(combined_plot)
        self.play(chips[0][0].animate.set_fill(opacity=1.0), run_time=0.3)

        # fold in wave 2: the curve visibly reshapes in real time, in step
        # with "fold together into something" (~16.4-18.9s)
        self.play(
            w2.animate.set_value(1.0),
            chips[1][0].animate.set_fill(opacity=1.0),
            run_time=1.86,
            rate_func=smooth,
        )

        # fold in wave 3: final messy waveform forms, matching "that looks
        # nothing like a sine wave anymore." (~18.9-20.7s)
        self.play(
            w3.animate.set_value(1.0),
            chips[2][0].animate.set_fill(opacity=1.0),
            run_time=1.78,
            rate_func=smooth,
        )

        messy_label = Text("...and the sum looks nothing like a sine anymore.",
                            font_size=22, color=GRAY_TXT)
        messy_label.next_to(big_axes, DOWN, buff=0.4)
        fit_frame(messy_label)
        self.play(FadeIn(messy_label, shift=UP * 0.1), run_time=0.54)

        # freeze the always_redraw curve into a plain static plot before
        # moving into the 3D beat (always_redraw mobjects don't transform
        # cleanly)
        final_combined = big_axes.plot(COMBINED, color=WHITE, stroke_width=4)
        self.remove(combined_plot)
        self.add(final_combined)

        # Narration keeps going here with a NEW idea that this scene's
        # original visuals didn't have a dedicated beat for: "A Fourier
        # transform runs that process in reverse. Hand it the messy
        # result and it tells you exactly which frequencies went into it
        # and how strongly." (~21.2-31.0s). Rather than freezing the
        # "...anymore." caption on screen for 10s while unrelated words
        # play, swap it for a second caption that names this exact idea -
        # the messy waveform underneath (literally "the messy result")
        # keeps making the point visually while the caption text catches
        # up to what's being said.
        self.play(FadeOut(messy_label), run_time=0.4)
        reverse_caption = Text(
            "A Fourier transform reverses this: hand it the messy result,\n"
            "get back exactly which frequencies - and how strongly.",
            font_size=22, color=GRAY_TXT, line_spacing=1.1,
        )
        reverse_caption.next_to(big_axes, DOWN, buff=0.4)
        fit_frame(reverse_caption)
        self.play(FadeIn(reverse_caption, shift=UP * 0.1), run_time=9.4)

        self.play(
            FadeOut(VGroup(add_title, chips, reverse_caption)),
            run_time=0.4,
        )

        # ------------------------------------------------------------
        # Beat 3: real 3D decomposition - the combined wave unrolls into
        # a stack of pure sine waves receding into the distance
        # ------------------------------------------------------------
        # Narration: "One signal isn't really one thing at all." (~31.4-34.5s)
        # - the cross-fade from the 2D combined view to this title spans
        # the whole sentence.
        split_title = Text("In 3D: one signal is really a stack of pure tones.",
                            font_size=26, color=WHITE)
        split_title.to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(split_title)
        split_title.set_opacity(0)
        self.play(
            FadeOut(big_axes),
            FadeOut(final_combined),
            split_title.animate.set_opacity(1),
            run_time=3.5,
        )

        # "It's a stack of pure tones" (~34.8-37.0s)
        # Retiming v2 (Fix 1): shortened from 1.6s -> 0.6s as part of
        # trimming the ~5.3s overshoot in this scene's trailing 3D coda
        # (see notes near the ambient rotation below). Still a smooth
        # eased pan, just brisker.
        self.move_camera(phi=68 * DEGREES, theta=-70 * DEGREES, distance=9,
                          run_time=0.6)

        ax3d = ThreeDAxes(
            x_range=[0, 8, 2], y_range=[-2.2, 2.2, 2], z_range=[0, 6, 2],
            x_length=7.5, y_length=3.0, z_length=5.2,
            axis_config={"color": GRAY_TXT, "stroke_width": 2, "include_tip": False},
        )
        ax3d.move_to(DOWN * 0.5)
        self.play(Create(ax3d), run_time=0.8)

        depth_label = Text("frequency", font_size=20, color=GRAY_TXT)
        depth_label.rotate(90 * DEGREES, axis=RIGHT).rotate(90 * DEGREES, axis=OUT)
        depth_label.move_to(ax3d.c2p(0, 0, 5.0) + LEFT * 0.3)
        time_label = Text("time", font_size=20, color=GRAY_TXT)
        time_label.rotate(90 * DEGREES, axis=RIGHT)
        time_label.move_to(ax3d.c2p(8.8, 0, 0))
        # "sitting right on top of" (~37.6-38.9s)
        self.play(FadeIn(depth_label), FadeIn(time_label), run_time=0.6)

        # the single combined waveform, sitting at the front (z = 0)
        combined_curve = ParametricFunction(
            lambda t: ax3d.c2p(t, COMBINED(t), 0),
            t_range=[0, 8, 0.05], color=WHITE, stroke_width=4,
        )
        # "each other" (~38.9-39.5s)
        self.play(Create(combined_curve), run_time=1.0)

        # three ghost copies of the SAME combined curve, all still at z=0,
        # about to peel apart into their own pure-tone shapes further back
        depths = [0.6, 3.0, 5.4]
        ghosts = VGroup(*[combined_curve.copy() for _ in range(3)])

        targets = VGroup(*[
            ParametricFunction(
                lambda t, i=i: ax3d.c2p(t, COMP_WAVES[i](t), depths[i]),
                t_range=[0, 8, 0.05], color=COMP_COLORS[i], stroke_width=4,
            )
            for i in range(3)
        ])

        self.play(FadeOut(combined_curve), run_time=0.2)
        self.add(ghosts)

        # the actual decomposition: each ghost reshapes into a pure sine
        # AND slides back along the depth axis, at the same time, in step
        # with "and the Fourier transform is just what happens when you"
        # (~39.5-43.1s)
        self.play(
            *[ReplacementTransform(ghosts[i], targets[i]) for i in range(3)],
            run_time=2.4,
            rate_func=smooth,
        )

        # small screen-fixed legend naming each receding tone
        legend = VGroup()
        for i in range(3):
            dot = Dot(radius=0.08, color=COMP_COLORS[i])
            lbl = Text(COMP_LABELS[i], font_size=18, color=COMP_COLORS[i])
            row = VGroup(dot, lbl).arrange(RIGHT, buff=0.15)
            legend.add(row)
        legend.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        legend.to_corner(UR, buff=0.5)
        self.add_fixed_in_frame_mobjects(legend)
        legend.set_opacity(0)
        self.play(legend.animate.set_opacity(1), run_time=0.35)

        # Retiming v2 (Fix 1): this whole trailing 3D-camera-rotation coda
        # (ambient drift + caption + return pan + closer) originally ran
        # ~5.3s longer than the scene's 43.58s narration window allows.
        # Sell the depth with a slow camera drift - the wait here is
        # during an ACTIVE ambient rotation, so the camera keeps moving
        # rather than sitting on a static frame. It's now split into two
        # stages at a decreasing rate (fast drift, then a slower trickle)
        # so the rotation eases down into the stop instead of cutting off
        # abruptly at full speed.
        self.begin_ambient_camera_rotation(rate=0.12)
        self.wait(0.5)
        self.stop_ambient_camera_rotation()
        self.begin_ambient_camera_rotation(rate=0.04)
        self.wait(0.2)
        self.stop_ambient_camera_rotation()

        unroll_caption = Text("A Fourier transform is what pulls this stack back out.",
                               font_size=22, color=GRAY_TXT)
        unroll_caption.to_edge(DOWN, buff=0.5)
        fit_frame(unroll_caption)
        self.add_fixed_in_frame_mobjects(unroll_caption)
        unroll_caption.set_opacity(0)
        self.play(unroll_caption.animate.set_opacity(1), run_time=0.3)

        # ------------------------------------------------------------
        # Back to a flat 2D view for the closing line
        # ------------------------------------------------------------
        self.move_camera(phi=0, theta=-90 * DEGREES, distance=9, run_time=0.5)

        self.play(FadeOut(VGroup(
            ax3d, targets, depth_label, time_label, legend, unroll_caption,
            split_title,
        )), run_time=0.15)

        closing = Text("Decomposition - not a new measurement.",
                        font_size=34, color=GREEN_C)
        closing.move_to(ORIGIN)
        fit_frame(closing)
        self.play(FadeIn(closing, shift=UP * 0.15), run_time=0.25)
        self.wait(0.05)
