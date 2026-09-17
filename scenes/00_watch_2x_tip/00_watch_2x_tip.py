"""
Scene 00: Watch at 2x tip

Silent ~2.5s bumper, no narration line (not part of narration_script.txt).
Sits before 01_hook in the final cut, telling viewers to bump playback
speed. Built fast per house style: quick pop-in, brief hold, quick fade.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *


def play_chevron(color):
    """A single '>' playback chevron, built from two thin triangles-free
    strokes (a simple filled triangle) so it reads as a play glyph."""
    tri = Triangle(color=color, fill_color=color, fill_opacity=1, stroke_width=0)
    tri.rotate(-PI / 2)
    tri.scale(0.28)
    return tri


class Watch2xTip(Scene):
    def construct(self):
        set_bg(self)

        chev1 = play_chevron(GREEN_C)
        chev2 = play_chevron(GREEN_C)
        chevrons = VGroup(chev1, chev2).arrange(RIGHT, buff=0.08)

        label = Text("2×", font_size=72, color=GREEN_C, weight=BOLD)

        badge = VGroup(chevrons, label).arrange(RIGHT, buff=0.35)

        headline = Text("WATCH AT 2× SPEED", font_size=40, color=WHITE, weight=BOLD)

        group = VGroup(badge, headline).arrange(DOWN, buff=0.35)
        fit_frame(group)

        self.play(
            GrowFromCenter(badge),
            run_time=0.35,
        )
        self.play(
            FadeIn(headline, shift=UP * 0.1),
            run_time=0.3,
        )
        self.wait(1.35)
        self.play(FadeOut(group), run_time=0.35)
