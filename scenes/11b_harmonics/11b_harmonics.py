"""
Scene 11b - Harmonics

Slots in right after Scene 11 (What Is a Fourier Transform) and before
Scene 12 (DFT Math). Direct answer to the user's own observation on real
hardware: one tall peak at the played note, then shorter bars at evenly
repeated distances above it.

Content beats:
  1. A pure sine wave has ONE peak in the spectrum, at its fundamental.
  2. A real periodic signal is a fundamental PLUS weaker components at
     exact integer multiples of it (2x, 3x, 4x, 5x...) - harmonics. This
     is just the special case of Scene 11's "any signal = sum of sines"
     idea where the component frequencies land on exact integer multiples
     of one fundamental. On a bar-chart spectrum this is one tall peak,
     then a shrinking, evenly-spaced ladder of bars.
  3. One-beat physical reason: almost nothing that vibrates moves in a
     perfect sine, so the exact vibration shape sets the harmonic content
     (why a violin and a flute playing "the same note" sound different).
  4. Tie back to this project's real 256-bin Goertzel display - same
     bar-chart visual language as Scene 15 - so it reads as "this is what
     you're actually seeing," not a textbook diagram.
  5. Closing line connecting back to the user's own hardware observation.

Fast first pass - short self.wait() calls, narration/timing added later.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *

# ---------------------------------------------------------------------------
# Waveforms (arbitrary units, domain [0, 8], same convention as Scene 11)
# ---------------------------------------------------------------------------
HARM_KS = [1, 2, 3, 4, 5]
HARM_AMPS = [1.0, 0.5, 0.33, 0.22, 0.15]


def pure_sine(x):
    return 1.0 * np.sin(2 * np.pi * 1 * x / 8)


def real_tone(x):
    return sum(a * np.sin(2 * np.pi * k * x / 8) for k, a in zip(HARM_KS, HARM_AMPS))


def wave_axes(y_range=1.3, x_length=9.2, y_length=2.3):
    return Axes(
        x_range=[0, 8, 2], y_range=[-y_range, y_range, 1],
        x_length=x_length, y_length=y_length,
        axis_config={"color": GRAY_TXT, "stroke_width": 1.5, "include_tip": False},
    )


# ---------------------------------------------------------------------------
# Bar-chart spectrum helper (same visual language as Scene 15's bar charts:
# flat gray baseline bars, tall colored bars for the signal actually present)
# ---------------------------------------------------------------------------
def make_bar(i, height, color, bar_w, gap, start_x, baseline_y, flat_h=0.05):
    h = max(height, flat_h)
    r = Rectangle(width=bar_w, height=h, fill_color=color, fill_opacity=0.9, stroke_width=0)
    x = start_x + i * (bar_w + gap)
    r.move_to([x, baseline_y + h / 2, 0])
    return r


def build_spectrum(n_slots, bar_w, gap, baseline_y, active, flat_h=0.05):
    """active: dict {slot_index: height} for bars that carry real signal
    (drawn green); every other slot is a flat gray baseline bar."""
    total_w = n_slots * (bar_w + gap) - gap
    start_x = -total_w / 2 + bar_w / 2
    bars = VGroup()
    xs = {}
    for i in range(n_slots):
        h = active.get(i, flat_h)
        color = GREEN_C if i in active else GRAY_TXT
        bar = make_bar(i, h, color, bar_w, gap, start_x, baseline_y, flat_h)
        bars.add(bar)
        xs[i] = start_x + i * (bar_w + gap)
    axis = Line([start_x - bar_w, baseline_y, 0], [start_x + total_w, baseline_y, 0],
                color=WHITE, stroke_width=2)
    return bars, axis, xs, start_x, total_w


class Harmonics(Scene):
    def construct(self):
        set_bg(self)

        BASELINE_Y = -1.6

        title = Text("Harmonics", font_size=38, color=WHITE)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=0.7)
        self.wait(0.2)

        # =========================================================
        # BEAT 1 - a pure sine wave has ONE peak
        # =========================================================
        sub1 = Text("a pure sine wave has one peak", font_size=24, color=GRAY_TXT)
        sub1.next_to(title, DOWN, buff=0.35)
        self.play(FadeIn(sub1, shift=UP * 0.1), run_time=0.4)

        ax1 = wave_axes()
        ax1.move_to(UP * 0.9)
        plot1 = ax1.plot(pure_sine, color=GREEN_C, stroke_width=3.5)
        wave1_label = Text("one frequency, nothing else", font_size=18, color=GREEN_C)
        wave1_label.next_to(ax1, DOWN, buff=0.3)

        self.play(Create(ax1), run_time=0.4)
        self.play(Create(plot1), FadeIn(wave1_label), run_time=0.6)
        self.wait(0.4)

        self.play(FadeOut(VGroup(ax1, plot1, wave1_label)), run_time=0.4)

        # bar-chart spectrum: single fundamental peak
        n_slots = 20
        bar_w = 0.28
        gap = 0.06
        FUND_IDX = 3
        FUND_H = 2.6

        bars1, axis1, xs1, start_x, total_w = build_spectrum(
            n_slots, bar_w, gap, BASELINE_Y, {FUND_IDX: FUND_H})

        self.play(Create(axis1), run_time=0.3)
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.05) for b in bars1],
                               lag_ratio=0.03), run_time=0.7)

        fund_label1 = Text("one peak, at the fundamental frequency",
                            font_size=20, color=GREEN_C)
        fund_label1.next_to(bars1[FUND_IDX], UP, buff=0.3)
        fit_frame(fund_label1)
        self.play(FadeIn(fund_label1, shift=DOWN * 0.1), run_time=0.5)
        self.wait(0.6)

        self.play(FadeOut(VGroup(sub1, fund_label1)), run_time=0.4)

        # =========================================================
        # BEAT 2 - a real tone: fundamental + harmonics
        # =========================================================
        sub2 = Text("a real tone is never a perfect sine", font_size=24, color=GRAY_TXT)
        sub2.next_to(title, DOWN, buff=0.35)
        self.play(FadeOut(axis1), FadeOut(bars1), FadeIn(sub2, shift=UP * 0.1), run_time=0.4)

        ax2 = wave_axes(y_range=2.4)
        ax2.move_to(UP * 0.9)
        plot2 = ax2.plot(real_tone, color=WHITE, stroke_width=3.5)
        wave2_label = Text("fundamental + weaker components riding on top",
                            font_size=18, color=WHITE)
        wave2_label.next_to(ax2, DOWN, buff=0.3)
        fit_frame(wave2_label)

        self.play(Create(ax2), run_time=0.4)
        self.play(Create(plot2), FadeIn(wave2_label), run_time=0.7)
        self.wait(0.4)

        sub2b = Text("a fundamental, plus integer multiples of it: 2x, 3x, 4x, 5x...",
                      font_size=20, color=WHITE)
        sub2b.move_to(sub2.get_center())
        fit_frame(sub2b)
        self.play(ReplacementTransform(sub2, sub2b), run_time=0.4)
        self.wait(0.3)

        self.play(FadeOut(VGroup(ax2, plot2, wave2_label)), run_time=0.4)

        # rebuild the same fundamental-only bar chart, then grow harmonics
        # out of it at 2x, 3x, 4x, 5x that bin position - evenly spaced
        bars2, axis2, xs2, _, _ = build_spectrum(n_slots, bar_w, gap, BASELINE_Y, {FUND_IDX: FUND_H})
        self.play(Create(axis2), run_time=0.25)
        self.play(FadeIn(bars2), run_time=0.4)
        self.wait(0.2)

        harm_idxs = [FUND_IDX * k for k in (2, 3, 4, 5)]   # 6, 9, 12, 15
        harm_heights = [FUND_H * a for a in HARM_AMPS[1:]]  # decreasing

        targets = [make_bar(i, h, GREEN_C, bar_w, gap, xs2[FUND_IDX] - FUND_IDX * (bar_w + gap), BASELINE_Y)
                   for i, h in zip(harm_idxs, harm_heights)]

        dash_top = BASELINE_Y + 3.0
        all_idxs = [FUND_IDX] + harm_idxs
        dashed_lines = VGroup(*[
            DashedLine([xs2[i], BASELINE_Y, 0], [xs2[i], dash_top, 0],
                       color=GRAY_TXT, stroke_width=1.5, dash_length=0.1)
            for i in all_idxs
        ])
        harm_tags = ["f", "2f", "3f", "4f", "5f"]
        tag_labels = VGroup(*[
            Text(tag, font_size=15, color=GREEN_C).next_to([xs2[i], BASELINE_Y, 0], DOWN, buff=0.2)
            for tag, i in zip(harm_tags, all_idxs)
        ])

        self.play(
            *[Transform(bars2[i], t) for i, t in zip(harm_idxs, targets)],
            Create(dashed_lines),
            run_time=1.0,
        )
        self.play(FadeIn(tag_labels), run_time=0.4)
        self.wait(0.3)

        spacing_note = Text("shorter bars, at repeated, evenly-spaced distances",
                             font_size=19, color=YELLOW_HL)
        spacing_note.next_to(axis2, DOWN, buff=0.55)
        fit_frame(spacing_note)
        self.play(FadeIn(spacing_note, shift=UP * 0.1), run_time=0.5)
        self.wait(0.7)

        beat2_group = VGroup(sub2b, bars2, axis2, dashed_lines, tag_labels, spacing_note)
        self.play(FadeOut(beat2_group), run_time=0.5)

        # =========================================================
        # BEAT 3 - one-beat physical reason
        # =========================================================
        phys1 = Text("almost nothing that vibrates moves in a perfect sine",
                      font_size=24, color=WHITE)
        phys1.move_to(UP * 0.6)
        phys2 = Text("a string, a speaker cone, a voice, a non-ideal circuit",
                      font_size=19, color=GRAY_TXT)
        phys2.next_to(phys1, DOWN, buff=0.3)
        phys3 = Text("the exact shape sets how much energy lands in each harmonic",
                      font_size=19, color=GRAY_TXT)
        phys3.next_to(phys2, DOWN, buff=0.25)
        phys4 = Text("which is why a violin and a flute on the same note sound different",
                      font_size=20, color=GREEN_C)
        phys4.next_to(phys3, DOWN, buff=0.45)
        for m in (phys1, phys2, phys3, phys4):
            fit_frame(m)

        self.play(FadeIn(phys1, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(phys2, shift=UP * 0.1), run_time=0.4)
        self.play(FadeIn(phys3, shift=UP * 0.1), run_time=0.4)
        self.wait(0.2)
        self.play(FadeIn(phys4, shift=UP * 0.1), run_time=0.5)
        self.wait(0.7)

        self.play(FadeOut(VGroup(phys1, phys2, phys3, phys4)), run_time=0.5)

        # =========================================================
        # BEAT 4 - what the real 256-bin Goertzel display shows
        # =========================================================
        sub4 = Text("this is what the real 256-bin display shows", font_size=24, color=WHITE)
        sub4.next_to(title, DOWN, buff=0.35)
        self.play(FadeIn(sub4, shift=UP * 0.1), run_time=0.5)

        n2 = 36
        bar_w2 = 0.17
        gap2 = 0.03
        FUND2 = 4
        harm2_idxs = [FUND2 * k for k in (2, 3, 4, 5)]
        active2 = {FUND2: FUND_H}
        for i, h in zip(harm2_idxs, harm_heights):
            active2[i] = h

        bars4, axis4, xs4, _, _ = build_spectrum(n2, bar_w2, gap2, BASELINE_Y, active2)

        left_tag = Text("bin 0", font_size=14, color=GRAY_TXT)
        left_tag.next_to(axis4.get_left(), DOWN, buff=0.15)
        right_tag = Text("bin 255", font_size=14, color=GRAY_TXT)
        right_tag.next_to(axis4.get_right(), DOWN, buff=0.15)

        self.play(Create(axis4), FadeIn(left_tag), FadeIn(right_tag), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.04) for b in bars4],
                               lag_ratio=0.02), run_time=0.9)
        self.wait(0.4)

        hw_note = Text("one played note, one fundamental bin and its harmonic ladder",
                        font_size=18, color=GREEN_C)
        hw_note.next_to(axis4, DOWN, buff=0.55)
        fit_frame(hw_note)
        self.play(FadeIn(hw_note, shift=UP * 0.1), run_time=0.5)
        self.wait(0.7)

        beat4_group = VGroup(sub4, bars4, axis4, left_tag, right_tag, hw_note)
        self.play(FadeOut(beat4_group), run_time=0.5)

        # =========================================================
        # BEAT 5 - closing, ties back to the user's own observation
        # =========================================================
        close1 = Text("a single played tone isn't one frequency", font_size=30, color=WHITE)
        close1.move_to(UP * 0.4)
        close2 = Text("it's a fundamental, plus a shrinking ladder of harmonics above it",
                       font_size=24, color=GREEN_C)
        close2.next_to(close1, DOWN, buff=0.4)
        fit_frame(close1)
        fit_frame(close2)

        self.play(FadeIn(close1, shift=UP * 0.15), run_time=0.6)
        self.wait(0.2)
        self.play(FadeIn(close2, shift=UP * 0.15), run_time=0.6)
        self.wait(0.9)
