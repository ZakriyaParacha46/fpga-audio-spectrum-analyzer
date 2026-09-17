"""
Scene 06: The Voltage Divider

Real numbers, measured on the actual board:
  - sensor idle output      ~1.45V
  - divider: two 10k0hm resistors (equal split)
  - measured node voltage   ~0.8V   (not the 0.725V the plain formula predicts)
  - XADC (unipolar aux channel): reads only 0V-1V, as 12-bit codes 0-4095

Narrative beat: the sensor's idle voltage alone would blow past the ADC's
1V ceiling and clip flat forever. A resistor divider brings it into range
-- but the real measured node voltage doesn't exactly match the textbook
formula, which is why you measure the real board instead of trusting the
math alone (this mirrors the "divider bug" story from the build log).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *

SENSOR_IDLE = 1.45
R1 = 10.0  # kOhm
R2 = 10.0  # kOhm
IDEAL_VOUT = SENSOR_IDLE * (R2 / (R1 + R2))   # 0.725V
MEASURED_VOUT = 0.80

ADC_MAX_CODE = 4095
idle_code = round(MEASURED_VOUT / 1.0 * ADC_MAX_CODE)          # 3276
headroom_up = ADC_MAX_CODE - idle_code                          # 819
headroom_down = idle_code                                       # 3276


class VoltageDivider(Scene):
    def construct(self):
        set_bg(self)

        # ------------------------------------------------------------
        # Title + sensor block, idling at 1.45V.
        # Narration (0.34-4.32s): "Small problem that this sensor idles
        # at about 1.45V." Run_times are stretched so sensor_v lands
        # (and stays) on screen right as "1.45V" is actually spoken,
        # rather than a quick reveal + frozen wait.
        # ------------------------------------------------------------
        title = Text("The Voltage Divider", font_size=40, color=WHITE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.3)

        sensor = RoundedRectangle(width=3.0, height=1.1, corner_radius=0.1,
                                   fill_color=BOX_FILL, fill_opacity=1, stroke_color=WHITE)
        sensor.move_to(LEFT * 4.6 + UP * 1.0)
        sensor_label = Text("SENSOR", font_size=22, color=WHITE).move_to(sensor.get_center() + UP * 0.2)
        sensor_v = Text(f"idles at {SENSOR_IDLE}V", font_size=18, color=YELLOW_HL).move_to(sensor.get_center() + DOWN * 0.28)

        self.play(FadeIn(sensor), Write(sensor_label), run_time=1.5)
        self.play(FadeIn(sensor_v, shift=UP * 0.1), run_time=1.92)

        # ------------------------------------------------------------
        # The XADC ceiling problem.
        # Narration (4.72-8.94s): "And this board's ADC input can only
        # see 0 to 1V." / (9.41-13.54s): "Anything above that just spins
        # flat against the ceiling, forever." - each reveal is stretched
        # to land as the matching phrase is spoken, ending right on
        # "forever."
        # ------------------------------------------------------------
        adc_axis = NumberLine(x_range=[0, 1.6, 0.2], length=6.0, color=WHITE)
        adc_axis.move_to(DOWN * 1.6)
        adc_axis_label = Text("XADC input range (volts)", font_size=20, color=WHITE)
        adc_axis_label.next_to(adc_axis, UP, buff=0.85)
        adc_ticks = VGroup(*[
            Text(f"{v:.1f}", font_size=14, color=GRAY_TXT).next_to(adc_axis.number_to_point(v), DOWN, buff=0.12)
            for v in [0.0, 0.4, 0.8, 1.0, 1.2, 1.6]
        ])

        ceiling_zone = Rectangle(
            width=adc_axis.number_to_point(1.6)[0] - adc_axis.number_to_point(1.0)[0],
            height=0.5, fill_color=RED_C, fill_opacity=0.18, stroke_width=0,
        )
        ceiling_zone.move_to(adc_axis.number_to_point(1.3) + UP * 0.0)
        ceiling_label = Text("unreachable\n(clips flat)", font_size=16, color=RED_C, line_spacing=0.9)
        ceiling_label.next_to(ceiling_zone, UP, buff=0.15)

        self.play(Create(adc_axis), Write(adc_axis_label), FadeIn(adc_ticks), run_time=2.51)
        self.play(FadeIn(ceiling_zone), FadeIn(ceiling_label), run_time=1.50)

        sensor_dot = Dot(adc_axis.number_to_point(SENSOR_IDLE), radius=0.1, color=YELLOW_HL)
        sensor_dot_label = Text(f"sensor: {SENSOR_IDLE}V", font_size=18, color=YELLOW_HL)
        sensor_dot_label.next_to(sensor_dot, DOWN, buff=0.25)
        fit_frame(sensor_dot_label)

        self.play(FadeIn(sensor_dot, scale=0.5), FadeIn(sensor_dot_label), run_time=1.50)
        self.play(Indicate(sensor_dot, color=RED_C, scale_factor=1.6), run_time=2.01)

        problem = Text("Straight into the ADC, this pins the reading flat. Forever.",
                        font_size=22, color=RED_C)
        problem.next_to(adc_axis, DOWN, buff=0.9)
        fit_frame(problem)
        self.play(FadeIn(problem, shift=UP * 0.15), run_time=1.76)

        # ------------------------------------------------------------
        # Move sensor block, introduce the divider circuit.
        # Narration (14.00-14.78s): "The fix isn't clever." / (15.70-
        # 22.84s): "It's two 10kΩ resistors in series, splitting the
        # voltage roughly in half." - the circuit is built up piece by
        # piece across this whole line at a slower pace.
        # ------------------------------------------------------------
        self.play(FadeOut(VGroup(problem, sensor_dot, sensor_dot_label, ceiling_zone, ceiling_label,
                                  adc_axis, adc_axis_label, adc_ticks)), run_time=1.13)

        self.play(sensor.animate.move_to(LEFT * 5.4 + UP * 1.6),
                   sensor_label.animate.move_to(LEFT * 5.4 + UP * 1.8),
                   sensor_v.animate.move_to(LEFT * 5.4 + UP * 1.32),
                   run_time=1.13)

        divider_title = Text("Two 10kΩ resistors, in series to ground", font_size=24, color=WHITE)
        divider_title.to_edge(UP, buff=1.3)
        self.play(FadeOut(title), FadeIn(divider_title), run_time=1.13)

        # Horizontal layout: sensor lead drops to a rail, then runs
        # left-to-right through R1 -> node (Vout tap) -> R2 -> GND.
        rail_y = -0.6
        r_width = 1.1
        r_height = 0.5
        lead_gap = 0.6
        gnd_stub_len = 0.4

        x0 = sensor.get_right()[0]
        r1_left_x = x0 + 0.5
        r1_right_x = r1_left_x + r_width
        node_x = r1_right_x + lead_gap
        r2_left_x = node_x + lead_gap
        r2_right_x = r2_left_x + r_width
        gnd_x = r2_right_x + lead_gap

        bend_pt = np.array([x0, rail_y, 0])
        r1_left_pt = np.array([r1_left_x, rail_y, 0])
        r1_right_pt = np.array([r1_right_x, rail_y, 0])
        node_pt = np.array([node_x, rail_y, 0])
        r2_left_pt = np.array([r2_left_x, rail_y, 0])
        r2_right_pt = np.array([r2_right_x, rail_y, 0])
        gnd_top_pt = np.array([gnd_x, rail_y, 0])
        gnd_stub_pt = gnd_top_pt + DOWN * gnd_stub_len

        wire_in = VGroup(
            Line(sensor.get_right(), bend_pt, color=WHITE, stroke_width=3),
            Line(bend_pt, r1_left_pt, color=WHITE, stroke_width=3),
        )

        r1 = Rectangle(width=r_width, height=r_height, color=WHITE, fill_color=BOX_FILL, fill_opacity=1)
        r1.move_to((r1_left_pt + r1_right_pt) / 2)
        r1_label = Text("10kΩ", font_size=20, color=WHITE).next_to(r1, UP, buff=0.25)

        r2 = Rectangle(width=r_width, height=r_height, color=WHITE, fill_color=BOX_FILL, fill_opacity=1)
        r2.move_to((r2_left_pt + r2_right_pt) / 2)
        r2_label = Text("10kΩ", font_size=20, color=WHITE).next_to(r2, UP, buff=0.25)

        wire_mid_left = Line(r1.get_right(), node_pt, color=WHITE, stroke_width=3)
        wire_mid_right = Line(node_pt, r2.get_left(), color=WHITE, stroke_width=3)
        wire_out = Line(r2.get_right(), gnd_top_pt, color=WHITE, stroke_width=3)
        wire_gnd_stub = Line(gnd_top_pt, gnd_stub_pt, color=WHITE, stroke_width=3)

        node_dot = Dot(node_pt, radius=0.09, color=GREEN_C)
        node_label = Text("Vout → to XADC", font_size=20, color=GREEN_C)
        node_label.next_to(node_dot, DOWN, buff=0.35)
        fit_frame(node_label)

        gnd_sym = VGroup(
            Line(gnd_stub_pt + LEFT * 0.35, gnd_stub_pt + RIGHT * 0.35, stroke_width=3, color=WHITE),
            Line(gnd_stub_pt + LEFT * 0.22 + DOWN * 0.12, gnd_stub_pt + RIGHT * 0.22 + DOWN * 0.12, stroke_width=3, color=WHITE),
            Line(gnd_stub_pt + LEFT * 0.1 + DOWN * 0.24, gnd_stub_pt + RIGHT * 0.1 + DOWN * 0.24, stroke_width=3, color=WHITE),
        )
        gnd_label = Text("GND", font_size=18, color=GRAY_TXT).next_to(gnd_sym, DOWN, buff=0.15)

        circuit = VGroup(wire_in, r1, wire_mid_left, wire_mid_right, r2, wire_out, wire_gnd_stub, gnd_sym)

        self.play(Create(wire_in), run_time=0.75)
        self.play(FadeIn(r1), Write(r1_label), run_time=1.13)
        self.play(Create(wire_mid_left), run_time=0.57)
        self.play(FadeIn(node_dot), FadeIn(node_label, shift=UP * 0.15), run_time=0.94)
        self.play(Create(wire_mid_right), run_time=0.57)
        self.play(FadeIn(r2), Write(r2_label), run_time=1.13)
        self.play(Create(wire_out), Create(wire_gnd_stub), FadeIn(gnd_sym), Write(gnd_label), run_time=0.94)

        # ------------------------------------------------------------
        # The formula, ideal vs measured.
        # Narration (23.42-29.90s): "Do your textbook math and you would
        # expect exactly 0.725V at the midpoint." - formula draws slowly
        # through the setup, then ideal_line lands exactly on "0.725V at
        # the midpoint."
        # ------------------------------------------------------------
        formula = Text(
            "Vout = Vin × R2 / (R1 + R2)",
            font_size=30, color=WHITE,
        )
        formula.move_to(RIGHT * 3.6 + UP * 1.7)
        fit_frame(formula)
        self.play(Write(formula), run_time=3.90)

        ideal_line = Text(
            f"ideal:  {SENSOR_IDLE}V × 0.5  =  {IDEAL_VOUT:.3f}V",
            font_size=24, color=WHITE,
        )
        ideal_line.next_to(formula, DOWN, buff=0.5)
        fit_frame(ideal_line)
        self.play(FadeIn(ideal_line, shift=UP * 0.15), run_time=2.58)
        self.wait(0.42)  # genuine gap to "Measure the real board..." (30.32s)

        # Narration (30.32-33.74s): "Measure the real board and you get
        # 0.8V. That's the gap." - measured_line IS this sentence.
        measured_line = Text(
            f"measured on the real board:  {MEASURED_VOUT:.2f}V",
            font_size=24, color=GREEN_C,
        )
        measured_line.next_to(ideal_line, DOWN, buff=0.35)
        fit_frame(measured_line)
        self.play(FadeIn(measured_line, shift=UP * 0.15), run_time=3.42)

        # Narration (33.90-41.30s): "Real resistors, real loading is
        # exactly what you put a meter on the actual node instead of
        # trusting the formula at paper." - note IS this sentence,
        # stretched (plus the small trailing gap) to fill it.
        note = Text(
            "Real resistors, real loading, real board.\nMeasure the node - don't just trust the math.",
            font_size=19, color=GRAY_TXT, line_spacing=1.1,
        )
        note.next_to(measured_line, DOWN, buff=0.5)
        fit_frame(note)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=8.30)

        # ------------------------------------------------------------
        # Clear circuit + formulas, show the headroom result on the code
        # axis. Narration (42.04-47.24s): "At 0.8V, this lands at code
        # 3276 out of 4095." - the labeled dot lands and finishes
        # appearing exactly as "...out of 4095" is spoken.
        # ------------------------------------------------------------
        self.play(FadeOut(VGroup(
            sensor, sensor_label, sensor_v, divider_title, circuit,
            r1_label, r2_label, node_dot, node_label, gnd_label,
            formula, ideal_line, measured_line, note,
        )), run_time=1.0)

        result_title = Text("What the XADC actually sees", font_size=32, color=WHITE)
        result_title.to_edge(UP, buff=0.6)
        self.play(Write(result_title), run_time=1.0)

        code_axis = NumberLine(x_range=[0, ADC_MAX_CODE, 1024], length=11.5, color=WHITE)
        code_axis.move_to(DOWN * 0.2)
        code_axis_label = Text("ADC code  (0 - 4095, 12-bit)", font_size=20, color=WHITE)
        code_axis_label.next_to(code_axis, UP, buff=0.35)
        code_ticks = VGroup(*[
            Text(str(v), font_size=14, color=GRAY_TXT).next_to(code_axis.number_to_point(v), DOWN, buff=0.12)
            for v in [0, 1024, 2048, 3072, ADC_MAX_CODE]
        ])
        self.play(Create(code_axis), Write(code_axis_label), FadeIn(code_ticks), run_time=1.5)

        idle_pt = code_axis.number_to_point(idle_code)
        idle_dot = Dot(idle_pt, radius=0.1, color=GREEN_C)
        idle_label = Text(f"idle: code {idle_code}", font_size=18, color=GREEN_C)
        idle_label.next_to(idle_dot, UP, buff=0.3)
        fit_frame(idle_label)
        self.play(FadeIn(idle_dot, scale=0.5), FadeIn(idle_label), run_time=1.7)
        self.wait(0.48)  # genuine gap to "Not perfectly centered..." (47.72s)

        # Narration (47.72s onward): "Not perfectly centered, but
        # nowhere near either edge, with real room to swing before
        # anything clips again." - braces and closing caption build up
        # slowly across the rest of the line.
        up_brace = Brace(Line(idle_pt, code_axis.number_to_point(ADC_MAX_CODE)), direction=DOWN, color=BLUE_C)
        up_text = Text(f"{headroom_up} codes to ceiling", font_size=16, color=BLUE_C)
        up_text.next_to(up_brace, DOWN, buff=0.15)

        down_brace = Brace(Line(code_axis.number_to_point(0), idle_pt), direction=DOWN, color=PURPLE_C)
        down_text = Text(f"{headroom_down} codes to floor", font_size=16, color=PURPLE_C)
        down_text.next_to(down_brace, DOWN, buff=0.15)

        self.play(GrowFromCenter(up_brace), FadeIn(up_text), run_time=1.89)
        self.play(GrowFromCenter(down_brace), FadeIn(down_text), run_time=1.89)

        closing = Text(
            "Not perfectly centered - but nowhere near either rail. No clipping.",
            font_size=22, color=WHITE,
        )
        closing.next_to(VGroup(up_brace, down_brace), DOWN, buff=0.7)
        fit_frame(closing)
        self.play(FadeIn(closing, shift=UP * 0.15), run_time=2.43)
