"""
Scene 04 - The Nyquist Theorem

Narrative: sample too slowly and a fast signal doesn't just look choppy --
it lies to you, appearing as an entirely different, slower frequency that
was never actually there (aliasing). The Nyquist theorem says: to faithfully
capture a signal up to frequency f, you must sample at more than 2f.

This board's XADC doesn't run at a tidy round number - it's retriggered
back-to-back as fast as the hardware allows: 26 clock cycles per conversion,
off a 100.208MHz clock divided by 4 (25.05MHz ADCCLK), which works out to
~1.038us per sample -> ~963.5 kSPS. That gives a Nyquist limit of ~482kHz --
audio was never going to be the limit.

Beats:
  1. title
  2. a fast sine, sampled densely - reconstruction matches, clean read
  3. the SAME fast sine, sampled sparsely - the dots trace out a totally
     different, slower "ghost" wave (aliasing), labeled in RED_C
  4. the Nyquist rule as plain text: fs > 2f
  5. the real math for this board's ADC (26 cycles / 25.05MHz -> 1.038us
     -> 963.5kSPS), readout style matching scene 06
  6. closing: Nyquist limit ~482kHz - audio was never going to be the limit

Retiming note: every beat's run_time= is stretched to fill the narration
sentence it illustrates (slow continuous motion), and self.wait() is used
ONLY for the real short silences between sentences in the transcript. Where
a sentence introduces no new visual (e.g. "This board doesn't run its ADC
at some tidy number like 48kHz either."), a slow Indicate() pulse on the
already-visible content fills the time instead of freezing.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *

# ---------------------------------------------------------------------------
# Real numbers, straight from the XADC config registers (matches scene 03's
# closing caption of "~1.038us per sample")
# ---------------------------------------------------------------------------
FPGA_CLK_MHZ = 100.208
CLOCK_DIVIDE = 4
ADCCLK_MHZ = FPGA_CLK_MHZ / CLOCK_DIVIDE                 # 25.052 MHz
CYCLES_PER_CONV = 26
CONV_TIME_US = CYCLES_PER_CONV / ADCCLK_MHZ              # ~1.038 us
SAMPLE_RATE_KSPS = 1000.0 / CONV_TIME_US                  # ~963.5 kSPS
NYQUIST_LIMIT_KHZ = SAMPLE_RATE_KSPS / 2.0                # ~481.75 -> ~482kHz (kSPS/2 = kHz limit)

# ---------------------------------------------------------------------------
# The demo sine: true_freq cycles across the domain [0, DOMAIN]. Sampling it
# with only ALIAS_SAMPLES points (< 2 * true_freq, violating Nyquist) makes
# the samples land exactly on a much slower "ghost" sine of GHOST_FREQ cycles
# across the same domain - a mathematically real aliasing example, not a
# fudged animation.
# ---------------------------------------------------------------------------
DOMAIN = 4.0
TRUE_FREQ = 9        # fast signal: 9 cycles across the domain
GOOD_SAMPLES = 60     # dense: way more than 2*TRUE_FREQ -> faithful
ALIAS_SAMPLES = 10    # sparse: less than 2*TRUE_FREQ -> aliases
GHOST_FREQ = 1        # the apparent (wrong) frequency the sparse samples imply


def true_signal(x):
    return np.sin(2 * PI * TRUE_FREQ * x / DOMAIN)


def ghost_signal(x):
    return -np.sin(2 * PI * GHOST_FREQ * x / DOMAIN)


class NyquistTheorem(Scene):
    def construct(self):
        set_bg(self)

        # ------------------------------------------------------------
        # Title. Narration (-0.02-2.02s): "Here's the part that should
        # bother you." While the title lands, also set up the axes and
        # a briefly-shown correctly-sampled "good case" reconstruction,
        # so the actual demo (the bad case) can start right as narration
        # states the problem. The real ~0.85s silence before that
        # (2.02-2.87s) is absorbed by the good_label fade-in running
        # slightly slower, rather than a separate wait.
        # ------------------------------------------------------------
        title = Text("The Nyquist Theorem", font_size=40, color=WHITE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        axes = Axes(
            x_range=[0, DOMAIN, 1], y_range=[-1.3, 1.3, 1],
            x_length=10.6, y_length=2.6,
            axis_config={"color": GRAY_TXT, "include_ticks": False, "stroke_width": 2},
            tips=False,
        )
        axes.move_to(UP * 0.75)

        true_curve = axes.plot(true_signal, x_range=[0, DOMAIN], color=WHITE, stroke_width=2.5)

        self.play(Create(axes), run_time=0.4)
        self.play(Create(true_curve), run_time=0.5)

        # ------------------------------------------------------------
        # Beat A: dense sampling - faithful reconstruction (the "good"
        # case, shown briefly before the narration states the problem)
        # ------------------------------------------------------------
        good_xs = np.linspace(0, DOMAIN, GOOD_SAMPLES, endpoint=False)
        good_dots = VGroup(*[
            Dot(axes.c2p(x, true_signal(x)), radius=0.035, color=YELLOW_HL)
            for x in good_xs
        ])
        good_label = Text("sampled fast enough - reconstruction matches",
                           font_size=20, color=GREEN_C)
        good_label.next_to(axes, DOWN, buff=0.5)
        fit_frame(good_label)

        self.play(FadeIn(good_dots, lag_ratio=0.02), run_time=0.5)
        self.play(FadeIn(good_label, shift=UP * 0.1), run_time=0.67)

        # ------------------------------------------------------------
        # Beat B: same fast signal, sparse sampling - aliasing.
        # Narration (2.87-6.86s): "If you sample too slowly, your data
        # doesn't just get blurry," - these four beats are stretched to
        # fill the whole line with slow continuous motion.
        # ------------------------------------------------------------
        self.play(FadeOut(good_dots), FadeOut(good_label), run_time=0.73)

        same_label = Text("same signal - sampled way too slow",
                           font_size=20, color=YELLOW_HL)
        same_label.next_to(axes, DOWN, buff=0.5)
        fit_frame(same_label)
        self.play(FadeIn(same_label, shift=UP * 0.1), run_time=0.91)

        self.play(true_curve.animate.set_opacity(0.25), run_time=0.73)

        alias_xs = np.linspace(0, DOMAIN, ALIAS_SAMPLES, endpoint=False)
        alias_dots = VGroup(*[
            Dot(axes.c2p(x, true_signal(x)), radius=0.09, color=YELLOW_HL)
            for x in alias_xs
        ])
        self.play(FadeIn(alias_dots, lag_ratio=0.06), run_time=1.63)
        self.wait(0.28)  # genuine gap to "it lies to you..." (7.14s)

        # Narration (7.14-13.48s): "it lies to you, convincingly, as an
        # entirely different, slower signal that was never actually
        # there." - the ghost curve draws in VERY slowly, its reveal
        # spanning almost the entire sentence.
        ghost_curve_full = axes.plot(ghost_signal, x_range=[0, DOMAIN], color=RED_C, stroke_width=3)
        ghost_curve = DashedVMobject(ghost_curve_full, num_dashes=40)

        self.play(FadeOut(same_label), run_time=1.46)
        self.play(Create(ghost_curve), run_time=4.88)
        self.wait(0.32)  # genuine gap to "That's aliasing." (13.80s)

        # Narration (13.80-14.74s): "That's aliasing."
        alias_label = Text("ALIASING - a different, slower frequency that was never there",
                            font_size=20, color=RED_C)
        alias_label.next_to(axes, DOWN, buff=0.5)
        fit_frame(alias_label)
        self.play(FadeIn(alias_label, shift=UP * 0.1), run_time=0.94)
        self.wait(0.38)  # genuine gap to "The fix [is] Nyquist's theorem..." (15.12s)

        # ------------------------------------------------------------
        # Beat C: the Nyquist rule, plain text.
        # Narration (15.12-20.40s): "The fix [is] Nyquist's theorem,
        # sample at more than twice the highest frequency you care
        # about." - fade-out/write/fade-in all slowed to fill the line.
        # ------------------------------------------------------------
        self.play(FadeOut(VGroup(title, axes, true_curve, alias_dots, ghost_curve, alias_label)), run_time=1.51)

        rule = Text("fs > 2 × f", font_size=64, color=WHITE)
        rule.move_to(UP * 0.4)
        rule_sub = Text("sample rate must exceed twice the highest frequency you care about",
                         font_size=20, color=GRAY_TXT)
        rule_sub.next_to(rule, DOWN, buff=0.45)
        fit_frame(rule_sub)

        self.play(Write(rule), run_time=2.26)
        self.play(FadeIn(rule_sub, shift=UP * 0.1), run_time=1.51)
        self.wait(0.46)  # genuine gap to "This board doesn't run..." (20.86s)

        # ------------------------------------------------------------
        # Beat D: the real math for this board's ADC.
        # Narration (20.86-27.06s): "This board doesn't run its ADC at
        # some tidy number like 48kHz either." - no new visual belongs
        # here, so a slow Indicate pulse on the board title keeps the
        # frame alive instead of freezing on it.
        # ------------------------------------------------------------
        self.play(FadeOut(VGroup(rule, rule_sub)), run_time=0.5)

        board_title = Text("This board's ADC", font_size=32, color=WHITE)
        board_title.to_edge(UP, buff=0.6)
        self.play(Write(board_title), run_time=0.6)
        self.play(Indicate(board_title, scale_factor=1.08), run_time=5.10)
        self.wait(0.48)  # genuine gap to "It's retriggered..." (27.54s)

        # Narration (27.54-36.64s): "It's retriggered back to back as
        # fast as the silicon allows, which works out to roughly
        # 963,000 samples a second." - the derivation builds line by
        # line, with a slow Indicate on line3 bridging "which works out
        # to roughly" so line4 lands exactly as "963,000" is spoken.
        line1 = Text(f"{CYCLES_PER_CONV} clock cycles per conversion", font_size=24, color=WHITE)
        line2 = Text(
            f"{FPGA_CLK_MHZ}MHz ÷ {CLOCK_DIVIDE}  =  {ADCCLK_MHZ:.2f}MHz ADCCLK",
            font_size=24, color=WHITE,
        )
        line3 = Text(
            f"{CYCLES_PER_CONV} ÷ {ADCCLK_MHZ:.2f}MHz  ≈  {CONV_TIME_US:.3f}µs per conversion",
            font_size=24, color=WHITE,
        )
        line4 = Text(f"≈ {SAMPLE_RATE_KSPS:.1f} kSPS", font_size=30, color=GREEN_C)

        lines = VGroup(line1, line2, line3, line4).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        lines.move_to(ORIGIN)
        fit_frame(lines)

        self.play(FadeIn(line1, shift=UP * 0.1), run_time=0.8)
        self.play(FadeIn(line2, shift=UP * 0.1), run_time=0.8)
        self.play(FadeIn(line3, shift=UP * 0.1), run_time=0.8)
        self.play(Indicate(line3, scale_factor=1.1), run_time=3.54)
        self.play(FadeIn(line4, shift=UP * 0.1), run_time=1.2)  # lands as "963,000" is spoken
        self.play(Indicate(line4, color=GREEN_C, scale_factor=1.15), run_time=1.96)
        self.wait(0.46)  # genuine gap to "At that rate..." (37.10s)

        # ------------------------------------------------------------
        # Beat E: closing - the Nyquist limit for this board.
        # Narration (37.10-41.78s): "At that rate, this ADC can trust
        # anything up to 482kHz." - closing1 is slowly hand-written
        # across the WHOLE line instead of appearing after a blank
        # hold, finishing exactly as "482kHz" is spoken.
        # ------------------------------------------------------------
        self.play(FadeOut(VGroup(board_title, lines)), run_time=0.6)

        closing1 = Text(f"Nyquist limit: up to ~{NYQUIST_LIMIT_KHZ:.0f}kHz", font_size=36, color=GREEN_C)
        closing2 = Text("Audio was never going to be the limit.", font_size=24, color=WHITE)
        closing_group = VGroup(closing1, closing2).arrange(DOWN, buff=0.4)
        closing_group.move_to(ORIGIN)
        fit_frame(closing_group)

        self.play(Write(closing1), run_time=4.08)
        self.wait(0.38)  # genuine gap to "Audio was never going to be..." (42.16s)

        # Narration (42.16s onward): "Audio was never going to be [the
        # bottleneck]." - fills the rest of the scene.
        self.play(FadeIn(closing2, shift=UP * 0.1), run_time=1.38)
