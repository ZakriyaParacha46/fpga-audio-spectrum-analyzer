"""
Scene 19: Credits

Short closing card (~10s target at normal pacing, built fast per house
style - narration/timing retimed once real audio exists). Second video in
the series (after neural-net-on-fpga / mmnist), so it nods to that without
overclaiming a sponsor credit this project doesn't have.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *


class Credits(Scene):
    def construct(self):
        set_bg(self)

        thanks = Text("Thanks for Watching", font_size=44, color=WHITE)
        thanks.move_to(UP * 1.7)

        github_line = Text("Full source on GitHub", font_size=26, color=WHITE)
        github_line.next_to(thanks, DOWN, buff=0.55)

        link_line = Text("audio_driver.v, the filters, the Goertzel bank, the VGA driver",
                          font_size=18, color=GRAY_TXT)
        link_line.next_to(github_line, DOWN, buff=0.25)

        desc_line = Text("link in the description", font_size=18, color=GRAY_TXT)
        desc_line.next_to(link_line, DOWN, buff=0.15)

        divider = Line(LEFT * 2.2, RIGHT * 2.2, color=GRAY_TXT, stroke_width=1)
        divider.next_to(desc_line, DOWN, buff=0.5)

        series_line = Text("Part two of a series on building real hardware from scratch",
                            font_size=20, color=GREEN_C)
        series_line.next_to(divider, DOWN, buff=0.45)

        # narration: "Thanks for watching." (0.54-1.12) - a slow fade so
        # it's still resolving as the line is spoken, rather than popping
        # in immediately and sitting frozen.
        self.play(FadeIn(thanks, shift=UP * 0.15), run_time=1.4)

        # narration: "The full source - the filters, the Goertzel bank, the
        # VGA driver, all of it - is on GitHub. Linked in the description."
        # (1.4-8.78) - the three lines stagger in slowly across the whole
        # sentence instead of popping in fast and then freezing.
        self.play(
            LaggedStart(
                FadeIn(github_line, shift=UP * 0.1),
                FadeIn(link_line, shift=UP * 0.1),
                FadeIn(desc_line, shift=UP * 0.1),
                lag_ratio=0.3,
            ),
            run_time=7.9,
        )

        # narration: "This is part two of a series on building real
        # hardware from scratch." (9.38 onward, through end of scene window)
        self.play(Create(divider), run_time=0.3)
        # IMPORTANT: no trailing FadeOut here, and no wait() padding either
        # - this scene gets freeze-hold padded to match the real narration
        # length in the final assembly. A trailing FadeOut would mean the
        # freeze-hold lands on an empty black frame instead of the
        # credits, so the series_line fade-in itself is stretched to
        # cover the rest of the narration, ending exactly at the scene's
        # real length with the full card still on screen.
        self.play(FadeIn(series_line, shift=UP * 0.1), run_time=2.94)
