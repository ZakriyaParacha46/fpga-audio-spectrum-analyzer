"""
Scene 12 - The DFT, The Math

Content beats:
  1. Correlate the signal against ONE test frequency -> a single number
     ("how much of this frequency is present"). Keep it visual, not formulaic.
  2. Repeat that for every frequency bin -> N test frequencies, each
     correlated against N samples -> N x N = N^2 multiplications.
  3. Plug in real numbers: N=512 -> 512 x 512 = 262,144 multiplications
     (over a quarter million).
  4. Hermitian symmetry: a real-valued input always produces a
     mirror-symmetric spectrum, so only half the output bins are unique.
     Visualize a 512-point spectrum and fold the right half onto the left.
  5. Close: bin 0 (DC) is dropped, bins 1-256 become the 256 bars on
     screen - which is why a 256-bar display needs a 512-point transform.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *

N = 512
TOTAL_MULTS = N * N


def signal_fn(x):
    return 0.55 * np.sin(2.3 * x) + 0.25 * np.sin(5.1 * x + 0.6)


def test_fn(freq):
    return lambda x: 0.7 * np.sin(freq * x)


def graph_card(func, x_range, color, with_dots=False, n_dots=10, stroke_width=3):
    graph = FunctionGraph(func, x_range=x_range, color=color, stroke_width=stroke_width)
    group = VGroup(graph)
    if with_dots:
        xs = np.linspace(x_range[0], x_range[1], n_dots)
        dots = VGroup(*[Dot([x, func(x), 0], radius=0.045, color=color) for x in xs])
        group.add(dots)
    return group


class DFTMath(Scene):
    def construct(self):
        set_bg(self)

        # Narration: "So how do you actually pull those frequencies back
        # out?" (~0.1-3.3s). As in the other retimed scenes, extra time
        # to match narration pacing lives in longer run_time= values on
        # plays already in motion, not in self.wait() padding - so the
        # picture never freezes on a static frame mid-explanation.
        title = Text("The DFT: The Math", font_size=40, color=WHITE)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=3.18)

        # ------------------------------------------------------------
        # BEAT 1 - correlate signal against ONE test frequency
        # Narration: "The discrete Fourier transform does it by brute
        # force." (~3.5-6.4s) covers the subtitle; "Correlate the signal
        # against a test frequency and see how well it matches."
        # (~6.5-12.1s) covers the rest of this beat's build-up.
        # ------------------------------------------------------------
        subtitle1 = Text("Correlate the signal against a test frequency", font_size=24, color=GRAY_TXT)
        subtitle1.next_to(title, DOWN, buff=0.35)
        self.play(FadeIn(subtitle1), run_time=2.9)

        sig = graph_card(signal_fn, [-1.8, 1.8, 0.03], WHITE, with_dots=True, n_dots=12)
        sig.move_to(LEFT * 3.6 + UP * 1.6)
        sig_label = Text("signal (samples)", font_size=18, color=WHITE).next_to(sig, DOWN, buff=0.25)

        times = Text("x", font_size=36, color=GRAY_TXT).move_to(UP * 1.6)

        test = graph_card(test_fn(3.0), [-1.8, 1.8, 0.03], BLUE_C, with_dots=False)
        test.move_to(RIGHT * 3.6 + UP * 1.6)
        test_label = Text("test sine wave", font_size=18, color=BLUE_C).next_to(test, DOWN, buff=0.25)

        # "Correlate the signal" (~6.5-7.8s)
        self.play(FadeIn(sig), FadeIn(sig_label), run_time=1.0)
        self.play(FadeIn(times), run_time=0.5)
        # "against a test frequency" (~7.8-9.1s)
        self.play(FadeIn(test), FadeIn(test_label), run_time=1.24)

        arrow_down = Arrow(UP * 0.65, UP * 0.0, color=GRAY_TXT, buff=0, stroke_width=3,
                            max_tip_length_to_length_ratio=0.35)
        sigma = Text("Σ", font_size=34, color=YELLOW_HL).next_to(arrow_down, DOWN, buff=0.15)

        result_box = RoundedRectangle(width=1.9, height=0.85, corner_radius=0.12,
                                       fill_color=BOX_FILL, fill_opacity=1, stroke_color=YELLOW_HL)
        result_box.next_to(sigma, DOWN, buff=0.3)
        result_num = Text("0.71", font_size=28, color=YELLOW_HL).move_to(result_box)

        result_caption = Text("how much of this frequency is present", font_size=18, color=GRAY_TXT)
        result_caption.next_to(result_box, DOWN, buff=0.25)
        fit_frame(result_caption)

        # "and" (~9.1-9.4s)
        self.play(GrowArrow(arrow_down), run_time=0.34)
        # "see how" (~9.4-11.2s)
        self.play(Write(sigma), run_time=1.74)
        # "well it" (~11.2-11.8s)
        self.play(FadeIn(result_box), FadeIn(result_num), run_time=0.62)
        # "matches." (~11.8-12.1s)
        self.play(FadeIn(result_caption, shift=UP * 0.1), run_time=0.34)

        beat1_group = VGroup(subtitle1, sig, sig_label, times, test, test_label,
                              arrow_down, sigma, result_box, result_num, result_caption)
        self.play(FadeOut(beat1_group), run_time=0.3)

        # ------------------------------------------------------------
        # BEAT 2 - repeat for every frequency bin -> N times -> N^2
        # ------------------------------------------------------------
        # Narration: "Then repeat that for every single frequency bin you
        # care about," (~12.1-15.9s) covers the subtitle + mini-graphs;
        # "for 512 samples and 512 test frequency." (~15.9-19.5s) covers
        # the N x N = N^2 recap lines.
        subtitle2 = Text("Repeat that for every frequency bin", font_size=24, color=GRAY_TXT)
        subtitle2.next_to(title, DOWN, buff=0.35)
        self.play(FadeIn(subtitle2), run_time=0.7)

        freqs = [1.0, 2.0, 3.0, 4.0, 5.0]
        xs_positions = np.linspace(-5.2, 3.6, len(freqs))
        mini_graphs = VGroup()
        for fx, freq in zip(xs_positions, freqs):
            g = graph_card(test_fn(freq), [-0.85, 0.85, 0.05], BLUE_C, with_dots=False, stroke_width=2.5)
            g.move_to(RIGHT * fx + UP * 1.7)
            mini_graphs.add(g)
        dots_more = Text("...", font_size=28, color=GRAY_TXT).move_to(RIGHT * 5.4 + UP * 1.7)

        freq_label = Text("N test frequencies, one per output bin", font_size=18, color=BLUE_C)
        freq_label.next_to(mini_graphs, DOWN, buff=0.35)
        fit_frame(freq_label)

        self.play(LaggedStart(*[FadeIn(g, scale=0.8) for g in mini_graphs], lag_ratio=0.15), run_time=1.3)
        self.play(FadeIn(dots_more), FadeIn(freq_label), run_time=1.5)

        work_line1 = Text("N frequencies  x  N samples correlated per frequency", font_size=22, color=WHITE)
        work_line1.move_to(DOWN * 0.4)
        fit_frame(work_line1)
        # "for 512 samples and" (~15.9-17.5s)
        self.play(FadeIn(work_line1, shift=UP * 0.15), run_time=1.77)

        nsq = Text("N x N  =  N²  multiplications", font_size=30, color=YELLOW_HL)
        nsq.next_to(work_line1, DOWN, buff=0.45)
        fit_frame(nsq)
        # "512 test frequency." (~17.5-19.5s)
        self.play(FadeIn(nsq, shift=UP * 0.15), run_time=1.77)

        beat2_group = VGroup(subtitle2, mini_graphs, dots_more, freq_label, work_line1, nsq)
        self.play(FadeOut(beat2_group), run_time=0.2)

        # ------------------------------------------------------------
        # BEAT 3 - plug in real numbers
        # ------------------------------------------------------------
        # Narration: "That's on the order of a quarter million
        # multiplications just to look at one snapshot of sound."
        # (~19.7-24.9s)
        n_label = Text(f"N = {N} samples", font_size=32, color=WHITE)
        n_label.move_to(UP * 1.6)
        # "That's on the order of" (~19.7-21.1s)
        self.play(FadeIn(n_label, shift=UP * 0.15), run_time=1.44)

        calc = Text(f"{N} x {N}  =  {TOTAL_MULTS:,}", font_size=36, color=YELLOW_HL)
        calc.next_to(n_label, DOWN, buff=0.6)
        # "quarter million multiplication[s]" (~21.1-22.2s)
        self.play(FadeIn(calc, shift=UP * 0.15), run_time=1.12)

        quarter = Text("over a quarter million multiplications", font_size=22, color=RED_C)
        quarter.next_to(calc, DOWN, buff=0.5)
        fit_frame(quarter)
        # "just to look at one snapshot of sound." (~22.2-24.9s)
        self.play(FadeIn(quarter, shift=UP * 0.15), run_time=2.64)

        beat3_group = VGroup(n_label, calc, quarter)
        # Genuine transcript gap before "A real valued signal..." (~0.76s).
        self.play(FadeOut(beat3_group), run_time=0.76)

        # ------------------------------------------------------------
        # BEAT 4 - Hermitian symmetry: half the bins are a mirror
        # ------------------------------------------------------------
        # Narration: "A real valued signal always produces a mirror
        # symmetric spectrum." (~25.6-29.8s), then "So half the output is
        # a duplicate you can throw away." (~30.2-33.1s)
        subtitle4 = Text("But a real-valued signal has a shortcut", font_size=24, color=GRAY_TXT)
        subtitle4.next_to(title, DOWN, buff=0.35)
        # "A real valued" (~25.6-26.3s)
        self.play(FadeIn(subtitle4), run_time=0.7)

        spec_axes = Axes(
            x_range=[0, N, 64], y_range=[0, 1.3, 1.3],
            x_length=11.2, y_length=2.6,
            axis_config={"color": GRAY_TXT, "include_ticks": False},
            tips=False,
        )
        spec_axes.move_to(UP * 0.4)

        def envelope(k):
            kk = k if k <= N / 2 else N - k
            return 0.15 + 0.95 * np.exp(-((kk - 90) ** 2) / (2 * 40 ** 2)) \
                        + 0.55 * np.exp(-((kk - 200) ** 2) / (2 * 18 ** 2))

        bin_ks = np.arange(0, N + 1, 16)
        bars = VGroup()
        left_bars = VGroup()
        right_bars = VGroup()
        for k in bin_ks:
            h = envelope(k)
            bottom = spec_axes.c2p(k, 0)
            top = spec_axes.c2p(k, h)
            color = GREEN_C if k <= N / 2 else GRAY_TXT
            bar = Line(bottom, top, color=color, stroke_width=4)
            bars.add(bar)
            if k <= N / 2:
                left_bars.add(bar)
            else:
                right_bars.add(bar)

        mid_line = DashedLine(spec_axes.c2p(N / 2, 0), spec_axes.c2p(N / 2, 1.3), color=WHITE, stroke_width=2)
        axis_line = Line(spec_axes.c2p(0, 0), spec_axes.c2p(N, 0), color=GRAY_TXT, stroke_width=2)

        tick_labels = VGroup(*[
            Text(str(v), font_size=14, color=GRAY_TXT).next_to(spec_axes.c2p(v, 0), DOWN, buff=0.15)
            for v in [0, 128, 256, 384, 512]
        ])

        # "signal" (~26.3-27.0s)
        self.play(Create(axis_line), FadeIn(tick_labels), run_time=0.68)
        # "always produce a mirror" (~27.0-28.8s)
        self.play(LaggedStart(*[Create(b) for b in bars], lag_ratio=0.03), run_time=1.74)
        # "symmetric spectrum." (~28.8-29.8s)
        self.play(Create(mid_line), run_time=1.02)

        left_label = Text("unique bins", font_size=18, color=GREEN_C)
        left_label.next_to(spec_axes.c2p(N / 4, 1.3), UP, buff=0.15)
        right_label = Text("mirror image", font_size=18, color=GRAY_TXT)
        right_label.next_to(spec_axes.c2p(3 * N / 4, 1.3), UP, buff=0.15)
        fit_frame(left_label)
        fit_frame(right_label)

        # bridges into "So half the output" (~29.8-30.2s)
        self.play(FadeIn(left_label), FadeIn(right_label), run_time=0.4)

        fold_note = Text("real input -> Hermitian-symmetric spectrum", font_size=20, color=WHITE)
        fold_note.next_to(spec_axes, DOWN, buff=1.1)
        fit_frame(fold_note)
        # "So half the output" (~30.2-30.9s)
        self.play(FadeIn(fold_note, shift=UP * 0.1), run_time=0.68)

        # fold the right half onto the left half - it's a literal mirror,
        # timed to "is a duplicate" (~30.9-31.8s)
        self.play(
            right_bars.animate.flip(axis=UP, about_point=spec_axes.c2p(N / 2, 0)),
            FadeOut(right_label),
            run_time=0.94,
        )
        # "you can" (~31.8-32.4s)
        self.play(Indicate(left_bars, color=GREEN_C, scale_factor=1.05), run_time=0.62)
        # "throw away." (~32.4-33.1s)
        self.play(FadeOut(right_bars), FadeOut(mid_line), run_time=0.68)

        beat4_leftover = VGroup(subtitle4, fold_note, left_label)
        # Genuine transcript gap before "That's the whole reason..." (~0.4s).
        self.play(FadeOut(beat4_leftover), run_time=0.4)

        # ------------------------------------------------------------
        # BEAT 5 - bin 0 dropped, bins 1-256 -> the 256 bars
        # Narration: "That's the whole reason 256 usable bars actually
        # require 512 point transform, not a 256-point one." (~33.5-41.5s)
        # ------------------------------------------------------------
        subtitle5 = Text("Bin 0 (DC) is dropped - bins 1-256 become the bars", font_size=22, color=GRAY_TXT)
        subtitle5.next_to(title, DOWN, buff=0.35)
        fit_frame(subtitle5)
        # "That's the whole reason" (~33.5-34.2s)
        self.play(FadeIn(subtitle5), run_time=0.66)

        bin0_bar = left_bars[0]
        bin0_mark = Cross(scale_factor=0.2, color=RED_C, stroke_width=3).move_to(bin0_bar.get_top())
        bin0_label = Text("DC - dropped", font_size=16, color=RED_C).next_to(bin0_mark, UP, buff=0.2)
        fit_frame(bin0_label)

        # "256" (~34.5-35.6s)
        self.play(FadeIn(bin0_mark), FadeIn(bin0_label), run_time=1.4)

        usable_bars = VGroup(*left_bars[1:])
        brace = Brace(usable_bars, direction=UP, color=GREEN_C)
        brace_label = Text("256 bars on screen", font_size=18, color=GREEN_C)
        brace_label.next_to(brace, UP, buff=0.15)
        fit_frame(brace_label)

        # "usable bars" (~35.6-36.7s)
        self.play(GrowFromCenter(brace), FadeIn(brace_label), run_time=1.16)

        closing = Text("A 256-bar display needs a 512-point transform.", font_size=24, color=WHITE)
        closing.next_to(spec_axes, DOWN, buff=1.1)
        fit_frame(closing)
        # Slow settle carries through "actually require 512 point
        # transform, not a 256-point one." (~36.7-41.5s) plus a touch of
        # trailing silence at the very end of the scene.
        self.play(FadeIn(closing, shift=UP * 0.15), run_time=5.24)
