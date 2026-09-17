"""
Scene 08 - What Is a Filter

Concept scene, no real measurements needed. Sets up filtering-by-frequency
before the next scenes (09+) show the actual repeated IIR building block.

Beats:
  1. A "busy" signal: slow drifting trend + fast jittery wiggles, GREEN_C.
  2. Split into lowpass (BLUE_C, keeps the slow trend, smooths the wiggles
     away) and highpass (PURPLE_C, throws away the drift, keeps only the
     fast wiggles, centered on zero).
  3. A simple frequency-response sketch for each: attenuation vs frequency,
     high-then-drop for lowpass, low-then-rise for highpass, with a dashed
     "cutoff" line.
  4. Closing line planting the seed for the next scenes: everything here is
     built from one repeated building block (don't over-explain - that's
     scene 09's job).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *

SLOW_AMP = 0.9
SLOW_FREQ = 0.55
FAST_AMP = 0.3
FAST_FREQ = 6.0


def busy_fn(x):
    return SLOW_AMP * np.sin(SLOW_FREQ * x) + FAST_AMP * np.sin(FAST_FREQ * x)


def slow_fn(x):
    return SLOW_AMP * np.sin(SLOW_FREQ * x)


def fast_fn(x):
    return FAST_AMP * np.sin(FAST_FREQ * x)


CUTOFF_X = 5.0


def lowpass_response(x):
    return 1.0 / (1.0 + np.exp((x - CUTOFF_X) * 1.6))


def highpass_response(x):
    return 1.0 - lowpass_response(x)


class WhatIsAFilter(Scene):
    def construct(self):
        set_bg(self)

        # ------------------------------------------------------------
        # Beat 0: title
        # ------------------------------------------------------------
        title = Text("What Is a Filter?", font_size=40, color=WHITE)
        title.to_edge(UP, buff=0.5)
        subtitle = Text("It reshapes a signal by frequency", font_size=22, color=GRAY_TXT)
        subtitle.next_to(title, DOWN, buff=0.25)
        # Narration: "A filter is just a signal on a diet -" (~0.0-3.3s
        # into this scene) then "it reshapes something by frequency"
        # (~3.5-6.2s), then straight into "A lowpass filter keeps slow
        # changes..." at ~6.6s. Rather than a fast title/subtitle pop
        # followed by a dead wait, stretch the entrance animations
        # themselves (run_time) so the title write and subtitle fade are
        # still smoothly in motion while those words are spoken, and let
        # the busy-signal build (axes -> curve -> caption) continuously
        # fill the runway up to the lowpass line - no static hold anywhere
        # in this whole intro.
        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(subtitle, shift=UP * 0.1), run_time=1.9)

        # ------------------------------------------------------------
        # Beat 1: the busy signal
        # ------------------------------------------------------------
        big_axes = Axes(
            x_range=[0, 10, 2], y_range=[-1.5, 1.5, 1],
            x_length=9.5, y_length=2.9,
            axis_config={"color": GRAY_TXT, "stroke_width": 2, "include_tip": False},
        )
        big_axes.move_to(DOWN * 0.6)
        big_curve = big_axes.plot(busy_fn, x_range=[0, 10, 0.02], color=GREEN_C, stroke_width=3)

        signal_label = Text("a busy signal", font_size=26, color=GREEN_C)
        signal_label.next_to(big_axes, UP, buff=0.3)
        fit_frame(signal_label)
        signal_sub = Text("slow drifting trend + fast jittery wiggles on top", font_size=18, color=GRAY_TXT)
        signal_sub.next_to(big_axes, DOWN, buff=0.3)
        fit_frame(signal_sub)

        self.play(Create(big_axes), run_time=1.0)
        self.play(Create(big_curve), FadeIn(signal_label), run_time=1.4)
        self.play(FadeIn(signal_sub, shift=UP * 0.1), run_time=0.78)

        # Clear right as "A lowpass filter" starts (~6.58s).
        self.play(FadeOut(VGroup(big_axes, big_curve, signal_label, signal_sub, subtitle)), run_time=0.4)

        # ------------------------------------------------------------
        # Beat 2: split into lowpass / highpass
        #
        # Narration walks lowpass first ("A lowpass filter keeps slow
        # changes and smooths away anything fast", ~6.6-11.8s), then
        # highpass ("A highpass filter does the exact opposite... throw
        # away the slow drift, keep only the fast wiggles", ~12.2-19.2s).
        # Reveal the two sides sequentially (not simultaneously) so each
        # side lands while its own half of the sentence is being spoken.
        # ------------------------------------------------------------
        split_header = Text("split it by frequency", font_size=26, color=WHITE)
        split_header.next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(split_header, shift=UP * 0.1), run_time=0.6)

        lp_axes = Axes(
            x_range=[0, 10, 2], y_range=[-1.5, 1.5, 1],
            x_length=5.4, y_length=2.3,
            axis_config={"color": GRAY_TXT, "stroke_width": 2, "include_tip": False},
        )
        lp_axes.move_to(LEFT * 3.5 + DOWN * 0.5)
        lp_curve = lp_axes.plot(slow_fn, x_range=[0, 10, 0.02], color=BLUE_C, stroke_width=3)
        lp_title = Text("lowpass", font_size=24, color=BLUE_C)
        lp_title.next_to(lp_axes, UP, buff=0.25)
        lp_sub = Text("keeps the slow trend,\nsmooths the fast wiggles away", font_size=15, color=GRAY_TXT, line_spacing=1.0)
        lp_sub.next_to(lp_axes, DOWN, buff=0.28)
        fit_frame(lp_sub)

        hp_axes = Axes(
            x_range=[0, 10, 2], y_range=[-1.5, 1.5, 1],
            x_length=5.4, y_length=2.3,
            axis_config={"color": GRAY_TXT, "stroke_width": 2, "include_tip": False},
        )
        hp_axes.move_to(RIGHT * 3.5 + DOWN * 0.5)
        hp_curve = hp_axes.plot(fast_fn, x_range=[0, 10, 0.02], color=PURPLE_C, stroke_width=3)
        hp_title = Text("highpass", font_size=24, color=PURPLE_C)
        hp_title.next_to(hp_axes, UP, buff=0.25)
        hp_sub = Text("throws away the drift,\nkeeps only the fast wiggles", font_size=15, color=GRAY_TXT, line_spacing=1.0)
        hp_sub.next_to(hp_axes, DOWN, buff=0.28)
        fit_frame(hp_sub)

        # -- lowpass side lands first, while "keeps slow changes" plays,
        #    with the curve continuing to draw slowly through "and smooths
        #    away anything fast" instead of popping in and freezing --
        self.play(Create(lp_axes), FadeIn(lp_title), run_time=1.0)
        self.play(Create(lp_curve), run_time=2.0)
        self.play(FadeIn(lp_sub, shift=UP * 0.08), run_time=1.6)

        # -- highpass side lands as "A highpass filter does the exact
        #    opposite" starts (~12.2s); curve + caption again stretched to
        #    stay in motion through "throw away the slow drift, keep only
        #    the fast wiggles" (~14.9-19.2s) --
        self.play(Create(hp_axes), FadeIn(hp_title), run_time=1.2)
        self.play(Create(hp_curve), run_time=2.3)
        self.play(FadeIn(hp_sub, shift=UP * 0.08), run_time=3.98)

        # Clear right as "Every filter has a cutoff" starts (~19.66s).
        self.play(FadeOut(VGroup(
            split_header, lp_axes, lp_curve, lp_title, lp_sub,
            hp_axes, hp_curve, hp_title, hp_sub,
        )), run_time=0.3)

        # ------------------------------------------------------------
        # Beat 3: frequency-response sketches
        # Narration: "Every filter has a cutoff" (~19.7-20.9s). Keep the
        # axes/curve build quick so the cutoff line itself lands right on
        # the word "cutoff".
        # ------------------------------------------------------------
        fr_header = Text("every filter has a cutoff frequency", font_size=26, color=WHITE)
        fr_header.next_to(title, DOWN, buff=0.3)
        fit_frame(fr_header)
        self.play(FadeIn(fr_header, shift=UP * 0.1), run_time=0.3)

        def make_response_axes(center):
            ax = Axes(
                x_range=[0, 10, 10], y_range=[0, 1.2, 1.2],
                x_length=5.2, y_length=2.5,
                axis_config={"color": GRAY_TXT, "stroke_width": 2, "include_tip": True,
                              "tip_length": 0.15},
            )
            ax.move_to(center)
            return ax

        lp_fr_axes = make_response_axes(LEFT * 3.5 + DOWN * 0.6)
        hp_fr_axes = make_response_axes(RIGHT * 3.5 + DOWN * 0.6)

        lp_fr_curve = lp_fr_axes.plot(lowpass_response, x_range=[0, 10, 0.02], color=BLUE_C, stroke_width=3)
        hp_fr_curve = hp_fr_axes.plot(highpass_response, x_range=[0, 10, 0.02], color=PURPLE_C, stroke_width=3)

        lp_x_label = Text("frequency", font_size=14, color=GRAY_TXT)
        lp_x_label.next_to(lp_fr_axes.x_axis, DOWN, buff=0.15)
        lp_y_label = Text("attenuation", font_size=14, color=GRAY_TXT)
        lp_y_label.rotate(PI / 2)
        lp_y_label.next_to(lp_fr_axes.y_axis, LEFT, buff=0.15)
        fit_frame(lp_y_label)

        hp_x_label = Text("frequency", font_size=14, color=GRAY_TXT)
        hp_x_label.next_to(hp_fr_axes.x_axis, DOWN, buff=0.15)
        hp_y_label = Text("attenuation", font_size=14, color=GRAY_TXT)
        hp_y_label.rotate(PI / 2)
        hp_y_label.next_to(hp_fr_axes.y_axis, LEFT, buff=0.15)
        fit_frame(hp_y_label)

        lp_cutoff_line = DashedLine(
            lp_fr_axes.c2p(CUTOFF_X, 0), lp_fr_axes.c2p(CUTOFF_X, 1.2),
            color=YELLOW_HL, stroke_width=2,
        )
        lp_cutoff_label = Text("cutoff", font_size=15, color=YELLOW_HL)
        lp_cutoff_label.next_to(lp_cutoff_line, UP, buff=0.1)

        hp_cutoff_line = DashedLine(
            hp_fr_axes.c2p(CUTOFF_X, 0), hp_fr_axes.c2p(CUTOFF_X, 1.2),
            color=YELLOW_HL, stroke_width=2,
        )
        hp_cutoff_label = Text("cutoff", font_size=15, color=YELLOW_HL)
        hp_cutoff_label.next_to(hp_cutoff_line, UP, buff=0.1)

        lp_fr_title = Text("lowpass response", font_size=18, color=BLUE_C)
        lp_fr_title.next_to(lp_fr_axes, UP, buff=0.55)
        hp_fr_title = Text("highpass response", font_size=18, color=PURPLE_C)
        hp_fr_title.next_to(hp_fr_axes, UP, buff=0.55)

        self.play(
            Create(lp_fr_axes), Create(hp_fr_axes),
            FadeIn(lp_x_label), FadeIn(lp_y_label),
            FadeIn(hp_x_label), FadeIn(hp_y_label),
            run_time=0.3,
        )
        self.play(FadeIn(lp_fr_title), FadeIn(hp_fr_title), run_time=0.25)
        self.play(Create(lp_fr_curve), Create(hp_fr_curve), run_time=0.25)
        # Cutoff line lands right as "cut-off" is spoken (~20.6-20.9s).
        self.play(
            Create(lp_cutoff_line), FadeIn(lp_cutoff_label),
            Create(hp_cutoff_line), FadeIn(hp_cutoff_label),
            run_time=0.3,
        )

        # Clear as "The entire project builds..." gets going (~21.2s).
        self.play(FadeOut(VGroup(
            fr_header, lp_fr_axes, lp_fr_curve, lp_x_label, lp_y_label, lp_fr_title,
            lp_cutoff_line, lp_cutoff_label,
            hp_fr_axes, hp_fr_curve, hp_x_label, hp_y_label, hp_fr_title,
            hp_cutoff_line, hp_cutoff_label, title,
        )), run_time=0.3)

        # ------------------------------------------------------------
        # Beat 4: closing line, seed for next scenes
        # Narration: "...this entire project builds both filters out of
        # one repeated trick, not a table of magic coefficients"
        # (~21.2-27.5s). Instead of popping the closing card in and then
        # sitting on a static frame for ~5s, fade it in slowly across the
        # entire remaining sentence so it's still gently settling into
        # place the whole time it's being talked about; only the very
        # last fraction of a second (after "coefficients" actually ends)
        # is genuine trailing silence, not filler.
        # ------------------------------------------------------------
        closing = Text(
            "This project builds everything from one repeated building block.",
            font_size=28, color=WHITE,
        )
        closing.move_to(ORIGIN)
        fit_frame(closing)
        self.play(FadeIn(closing, shift=UP * 0.15), run_time=5.68)
        self.wait(0.3)
