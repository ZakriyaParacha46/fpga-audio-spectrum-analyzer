"""
Scene 07 - Signal Path Overview

The full pipeline, block-diagram style: one signal, six stages, three
destinations. This is the orientation scene before the next several scenes
each zoom into one box, so it stays clean and readable rather than dense.

Pipeline (all real module/wire names from the FFTspectrum source tree):
  SENSOR -> DIVIDER -> XADC -> AUDIO_DRIVER
    produces `level` (12-bit, ~963.5 kSPS), which branches to:
      (a) WAVEFORM_VIEW  (raw, untouched)
      (b) LOWPASS_FILTER -> HIGHPASS_FILTER
            produces `level_bandpassed`, which branches to:
              (b1) WAVEFORM_VIEW (band-passed)
              (b2) FFT_VIEW (256-bin Goertzel spectrum)

Narration (as actually recorded - shorter than the written script; the
"every box is a real module... except one" sentence was cut, so the
IP-core beat is now reordered to AFTER the full pipeline build-out,
landing on "That ADC block isn't hand-written, it can't be" instead of
right after the XADC box first appears):
  0.00-3.24   "the entire pipeline, laid out end to end: one signal, six
               stages."
  3.24-9.10   "The divided voltage hits the ADC, producing a fresh 12-bit
               number nearly a million times a second."
  9.60-12.30  "That raw stream feeds a waveform view directly,"
  12.88-20.86 "completely untouched and also feeds a lowpass filter into
               a highpass filter, producing a cleaned up version that
               drives a second waveform view and a spectrum."
  21.46-25.82 "That ADC block isn't hand-written, it can't be."
  26.02-32.32 "Everything downstream of it, starting from that raw
               12-bit number, is still entirely mine."

Retiming note: run_time= on each self.play() is stretched to fill the
sentence it illustrates; self.wait() appears only at the transcript's real
short silences.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *


class SignalPathOverview(Scene):
    def construct(self):
        set_bg(self)

        # ------------------------------------------------------------
        # Title. Narration (0.00-3.24s): "the entire pipeline, laid out
        # end to end: one signal, six stages."
        # ------------------------------------------------------------
        title = Text("Signal Path Overview", font_size=36, color=WHITE)
        title.to_edge(UP, buff=0.35)
        subtitle = Text("one signal, six stages, three destinations",
                         font_size=18, color=GRAY_TXT)
        subtitle.next_to(title, DOWN, buff=0.15)

        self.play(Write(title), run_time=2.16)
        self.play(FadeIn(subtitle), run_time=1.08)

        # ------------------------------------------------------------
        # Layout constants
        # ------------------------------------------------------------
        LEFT_X = -4.7
        RIGHT_X = 4.4

        left_names = ["SENSOR", "DIVIDER", "XADC", "AUDIO_DRIVER",
                      "LOWPASS_FILTER", "HIGHPASS_FILTER"]
        left_texts = [Text(n, font_size=15, color=WHITE) for n in left_names]
        box_w = max(t.width for t in left_texts) + 0.45
        box_h = 0.52

        y_top = 2.15
        spacing = 0.98
        left_y = [y_top - i * spacing for i in range(6)]  # 2.15 .. -2.75

        def make_box(width, height, x, y):
            b = RoundedRectangle(width=width, height=height, corner_radius=0.08,
                                  fill_color=BOX_FILL, fill_opacity=1.0,
                                  stroke_color=WHITE, stroke_width=2)
            b.move_to([x, y, 0])
            return b

        left_boxes = [make_box(box_w, box_h, LEFT_X, y) for y in left_y]
        for box, label in zip(left_boxes, left_texts):
            label.move_to(box.get_center())

        # ------------------------------------------------------------
        # Right-column destination boxes
        # ------------------------------------------------------------
        right_names = ["WAVEFORM_VIEW", "WAVEFORM_VIEW", "FFT_VIEW"]
        right_captions = ["(raw, untouched)", "(band-passed)", "(256-bin Goertzel)"]
        right_texts = [Text(n, font_size=15, color=WHITE) for n in right_names]
        box_w_r = max(t.width for t in right_texts) + 0.45
        box_h_r = 0.52

        right_y = [1.05, -1.15, -2.75]
        right_boxes = [make_box(box_w_r, box_h_r, RIGHT_X, y) for y in right_y]
        for box, label in zip(right_boxes, right_texts):
            label.move_to(box.get_center())

        right_cap_texts = []
        for box, cap in zip(right_boxes, right_captions):
            c = Text(cap, font_size=13, color=GRAY_TXT)
            c.next_to(box, DOWN, buff=0.08)
            fit_frame(c)
            right_cap_texts.append(c)

        # ------------------------------------------------------------
        # Reveal left column, box by box, with chain arrows.
        # Narration (3.24-9.10s): "The divided voltage hits the ADC,
        # producing a fresh 12-bit number nearly a million times a
        # second." - the three boxes build up quickly (finishing right
        # as "ADC" is said), then a slow Indicate on XADC covers the
        # "producing a fresh 12-bit number..." clause.
        # ------------------------------------------------------------
        sensor_box, divider_box, xadc_box, audio_box, lp_box, hp_box = left_boxes
        sensor_lbl, divider_lbl, xadc_lbl, audio_lbl, lp_lbl, hp_lbl = left_texts

        self.play(Create(sensor_box), Write(sensor_lbl), run_time=0.47)

        def chain_arrow(a, b):
            return Arrow(a.get_bottom(), b.get_top(), buff=0.06,
                         stroke_width=3, color=GRAY_TXT,
                         max_tip_length_to_length_ratio=0.25)

        arr1 = chain_arrow(sensor_box, divider_box)
        self.play(Create(arr1), run_time=0.35)
        self.play(Create(divider_box), Write(divider_lbl), run_time=0.47)

        arr2 = chain_arrow(divider_box, xadc_box)
        self.play(Create(arr2), run_time=0.35)
        self.play(Create(xadc_box), Write(xadc_lbl), run_time=0.47)
        self.play(Indicate(xadc_box, scale_factor=1.1), run_time=4.25)

        # ------------------------------------------------------------
        # `level` branches: down into LOWPASS_FILTER, right into raw
        # waveform view. Narration (9.60-12.30s): "That raw stream feeds
        # a waveform view directly,"
        # ------------------------------------------------------------
        arr3 = chain_arrow(xadc_box, audio_box)
        self.play(Create(arr3), run_time=0.47)
        self.play(Create(audio_box), Write(audio_lbl), run_time=0.62)

        arr4 = chain_arrow(audio_box, lp_box)
        level_down_lbl = Text("level", font_size=14, color=GREEN_C)
        level_down_lbl.next_to(arr4, LEFT, buff=0.1)
        fit_frame(level_down_lbl)

        arr_raw = Arrow(audio_box.get_right(), right_boxes[0].get_left(),
                         buff=0.08, stroke_width=3, color=GREEN_C,
                         max_tip_length_to_length_ratio=0.12)
        level_right_lbl = Text("level  (12-bit, ~963.5 kSPS)", font_size=14, color=GREEN_C)
        level_right_lbl.move_to(arr_raw.get_center() + UP * 0.24)
        fit_frame(level_right_lbl)

        self.play(Create(arr4), FadeIn(level_down_lbl), run_time=0.62)
        self.play(Create(arr_raw), FadeIn(level_right_lbl), run_time=0.78)
        self.play(Create(right_boxes[0]), Write(right_texts[0]),
                   FadeIn(right_cap_texts[0]), run_time=0.78)

        # ------------------------------------------------------------
        # LOWPASS_FILTER -> HIGHPASS_FILTER, then the band-passed
        # branch. Narration (12.88-20.86s): "completely untouched and
        # also feeds a lowpass filter into a highpass filter, producing
        # a cleaned up version that drives a second waveform view and a
        # spectrum." - the whole rest of the diagram builds across this
        # one long sentence.
        # ------------------------------------------------------------
        self.play(Create(lp_box), Write(lp_lbl), run_time=1.11)

        arr5 = chain_arrow(lp_box, hp_box)
        self.play(Create(arr5), run_time=0.83)
        self.play(Create(hp_box), Write(hp_lbl), run_time=1.11)

        arr_band = Arrow(hp_box.get_right(), right_boxes[1].get_left(),
                          buff=0.08, stroke_width=3, color=PURPLE_C,
                          max_tip_length_to_length_ratio=0.12)
        arr_fft = Arrow(hp_box.get_right(), right_boxes[2].get_left(),
                         buff=0.08, stroke_width=3, color=PURPLE_C,
                         max_tip_length_to_length_ratio=0.12)

        bp_lbl = Text("level_bandpassed", font_size=14, color=PURPLE_C)
        bp_lbl.move_to(hp_box.get_right() + RIGHT * 1.5 + UP * 0.55)
        fit_frame(bp_lbl)

        self.play(FadeIn(bp_lbl, shift=RIGHT * 0.1), run_time=0.83)
        self.play(Create(arr_band), run_time=0.97)
        self.play(Create(right_boxes[1]), Write(right_texts[1]),
                   FadeIn(right_cap_texts[1]), run_time=1.38)
        self.play(Create(arr_fft), run_time=0.97)
        self.play(Create(right_boxes[2]), Write(right_texts[2]),
                   FadeIn(right_cap_texts[2]), run_time=1.38)

        # ------------------------------------------------------------
        # Aside: XADC is the one vendor IP core in this pipeline. Held
        # back until now (rather than right after the XADC box first
        # appeared) because the actual recorded narration circles back
        # to this point only after the full diagram is built.
        # Narration (21.46-25.82s): "That ADC block isn't hand-written,
        # it can't be."
        # ------------------------------------------------------------
        ip_ring = DashedVMobject(
            RoundedRectangle(width=box_w + 0.3, height=box_h + 0.3, corner_radius=0.12,
                              stroke_color=YELLOW_HL, stroke_width=2.5),
            num_dashes=16,
        )
        ip_ring.move_to(xadc_box.get_center())

        ip_badge = RoundedRectangle(width=0.98, height=0.3, corner_radius=0.06,
                                     fill_color=BG, fill_opacity=1.0,
                                     stroke_color=YELLOW_HL, stroke_width=1.5)
        ip_badge_lbl = Text("IP CORE", font_size=12, color=YELLOW_HL)
        ip_badge_lbl.move_to(ip_badge.get_center())
        ip_badge_group = VGroup(ip_badge, ip_badge_lbl)
        ip_badge_group.next_to(xadc_box, RIGHT, buff=0.2)
        fit_frame(ip_badge_group)

        self.play(Create(ip_ring), FadeIn(ip_badge_group, scale=0.85), run_time=1.92)

        ip_what = Text(
            "IP core = a vendor-verified hardware block\n"
            "you configure and generate, not hand-write",
            font_size=15, color=WHITE, line_spacing=1.15, should_center=True,
        )
        ip_which = Text(
            "Used here: Vivado's XADC Wizard\n"
            "Single Channel / Continuous, Unipolar, VAUX6\n"
            "DCLK = 50MHz  ->  generates module xadc_wiz_0",
            font_size=15, color=YELLOW_HL, line_spacing=1.15, should_center=True,
        )
        ip_why = Text(
            "ADC circuitry is hard silicon, not FPGA fabric;\n"
            "everything downstream is still hand-written Verilog",
            font_size=15, color=GRAY_TXT, line_spacing=1.15, should_center=True,
        )
        ip_text_group = VGroup(ip_what, ip_which, ip_why).arrange(DOWN, buff=0.16)
        ip_text_group.move_to([1.15, 0.15, 0])
        fit_frame(ip_text_group)

        ip_callout_arrow = Arrow(ip_badge_group.get_right(), ip_text_group.get_left(),
                                  buff=0.12, stroke_width=2.5, color=YELLOW_HL,
                                  max_tip_length_to_length_ratio=0.15)

        self.play(Create(ip_callout_arrow), run_time=1.20)
        self.play(FadeIn(ip_what), run_time=1.44)

        # ------------------------------------------------------------
        # Narration (26.02-32.32s): "Everything downstream of it,
        # starting from that raw 12-bit number, is still entirely
        # mine." - ip_why ("everything downstream is still hand-written
        # Verilog") is the closest on-screen echo of this line.
        # ------------------------------------------------------------
        self.play(FadeIn(ip_which), run_time=1.26)
        self.play(FadeIn(ip_why), run_time=1.26)

        self.play(FadeOut(VGroup(ip_ring, ip_callout_arrow, ip_text_group)), run_time=1.68)
        # ip_badge_group stays on screen, permanently marking XADC as the
        # one vendor IP core among the hand-written boxes in this pipeline.

        closing = Text(
            "Every box here is a real module in the source tree.\n"
            "Every arrow is a real wire in top.v.",
            font_size=18, color=WHITE, line_spacing=1.1, should_center=True,
        )
        closing.to_edge(DOWN, buff=0.18)
        fit_frame(closing)
        self.play(FadeIn(closing, shift=UP * 0.1), run_time=2.10)
