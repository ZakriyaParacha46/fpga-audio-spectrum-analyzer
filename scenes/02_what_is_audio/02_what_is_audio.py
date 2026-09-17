"""
Scene 02 - What Is Audio?

Narrative beats:
  1. Sound is a pressure wave in a 2D medium: a vibrating source pushes air
     outward as expanding concentric wavefronts (compression = bright/dense
     rings, rarefaction = dim/sparse rings). The medium itself (small dots
     scattered through the field) only jitters in place, radially, once a
     wavefront reaches it - it's the disturbance that travels outward, not
     the air. That disturbance eventually reaches the microphone.
  2. A microphone/electret sensor's diaphragm gets pushed by that pressure
     wave - push in, voltage goes up; pull out, voltage goes down.
  3. Plot that voltage against time and you get the familiar waveform -
     but it's still continuous/analog here. No sample rate, no discrete
     numbers yet, just a voltage smoothly changing with infinitely many
     values between any two points in time.

This sets up scene 03 (sampling / the ADC), which is where discretization
gets introduced - so this scene deliberately shows NO numeric axis ticks
on the voltage-vs-time graph (just "time" / "voltage" axis labels). That
absence is part of the point: nothing is quantized yet.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *


def pressure_func(t):
    """A smooth, slightly organic-looking continuous voltage waveform."""
    return 0.55 * np.sin(1.7 * t) + 0.22 * np.sin(3.9 * t + 0.6)


class WhatIsAudio(Scene):
    def construct(self):
        set_bg(self)

        # ------------------------------------------------------------
        # Title
        # ------------------------------------------------------------
        title = Text("What Is Audio?", font_size=40, color=WHITE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.5)

        # Subtitle is created now (its position depends on title) but not
        # shown until the narration actually says "sound is a pressure
        # wave" (retimed below, ~7.1s in) - beat-level sync, not a
        # scene-opener.
        subtitle = Text("Sound is a pressure wave", font_size=24, color=YELLOW_HL)
        subtitle.next_to(title, DOWN, buff=0.3)

        # ------------------------------------------------------------
        # Beat 1: sound as a 2D wave. A point source vibrates and pushes
        # concentric compression/rarefaction wavefronts outward through
        # a 2D field of air. Small dots scattered in the field jitter
        # radially IN PLACE, only once a wavefront reaches them - the
        # medium doesn't travel with the wave, the disturbance does.
        # ------------------------------------------------------------
        wave_y = 0.9
        source_pos = np.array([-5.6, wave_y, 0.0])
        spacing = 0.7            # ring spacing == one wavelength
        num_rings = 15
        max_radius = num_rings * spacing

        phase = ValueTracker(0.0)

        def arrival_ramp(local_phase):
            """0 before a wavefront arrives, ramps to 1 over one unit of
            phase as it passes - avoids a jarring instant-on jitter."""
            return float(np.clip(local_phase, 0.0, 1.0))

        def make_rings():
            rings = VGroup()
            for i in range(num_rings):
                r = (i * spacing + phase.get_value()) % max_radius
                if r < 0.05:
                    continue
                fade = 1.0
                if r < 0.6:
                    fade *= r / 0.6
                if r > max_radius - 1.0:
                    fade *= (max_radius - r) / 1.0
                compression = (i % 2 == 0)
                color = WHITE if compression else GRAY_TXT
                base_op = 0.9 if compression else 0.3
                sw = 3.5 if compression else 1.5
                circ = Circle(radius=r, stroke_color=color, stroke_width=sw,
                              stroke_opacity=base_op * fade)
                circ.move_to(source_pos)
                rings.add(circ)
            return rings

        rings = always_redraw(make_rings)

        # the vibrating object making the sound
        source_dot = always_redraw(lambda: Dot(
            point=source_pos,
            radius=0.14 + 0.035 * np.sin(-phase.get_value()),
            color=YELLOW_HL,
        ))
        source_label = Text("sound source", font_size=18, color=GRAY_TXT)
        source_label.next_to(source_pos, DOWN, buff=0.35)
        fit_frame(source_label)

        # the medium: fixed base positions, each one only displaces
        # radially (toward/away from the source) once the wavefront
        # reaches it - it oscillates in place, it does not travel.
        field_base = []
        for fx in np.linspace(-4.7, 3.5, 7):
            for fy in np.linspace(-2.0, 2.0, 5):
                p = np.array([fx, fy, 0.0])
                if np.linalg.norm(p[:2] - source_pos[:2]) < 0.8:
                    continue
                if 2.2 < fx < 3.8 and -0.05 < fy < 1.9:
                    continue  # keep clear of the mic housing
                field_base.append(p)

        jitter_amp = 0.09

        def make_field_dots():
            grp = VGroup()
            for p in field_base:
                d = p - source_pos
                r = np.linalg.norm(d[:2])
                direction = d / r if r > 1e-6 else np.array([1.0, 0.0, 0.0])
                local_phase = phase.get_value() - r
                disp = jitter_amp * np.sin(-local_phase) * arrival_ramp(local_phase)
                grp.add(Dot(point=p + disp * direction, radius=0.045, color=GRAY_TXT))
            return grp

        field_dots = always_redraw(make_field_dots)

        # microphone: housing + diaphragm (a line that moves up/down).
        # Mic center is driven by ValueTrackers so the diaphragm updater can
        # keep working after the mic is animated to a new position, without
        # ever swapping in a second always_redraw mobject (that left a
        # frozen leftover copy behind in an earlier version of this scene).
        mic_cx = ValueTracker(3.0)
        mic_cy = ValueTracker(wave_y)
        r_mic = float(np.linalg.norm(
            np.array([mic_cx.get_value(), mic_cy.get_value()]) - source_pos[:2]
        ))

        mic_housing = RoundedRectangle(width=1.3, height=1.6, corner_radius=0.15,
                                        fill_color=BOX_FILL, fill_opacity=1,
                                        stroke_color=WHITE, stroke_width=3)
        mic_housing.add_updater(lambda m: m.move_to([mic_cx.get_value(), mic_cy.get_value(), 0]))

        mic_frame = VGroup(
            Line(DOWN * 0.75, UP * 0.75, color=WHITE, stroke_width=3),
            Line(DOWN * 0.75, UP * 0.75, color=WHITE, stroke_width=3),
        )

        def _mic_frame_update(m):
            cx, cy = mic_cx.get_value(), mic_cy.get_value()
            m[0].put_start_and_end_on([cx - 0.5, cy - 0.75, 0], [cx - 0.5, cy + 0.75, 0])
            m[1].put_start_and_end_on([cx + 0.5, cy - 0.75, 0], [cx + 0.5, cy + 0.75, 0])
        mic_frame.add_updater(_mic_frame_update)

        def diaphragm_offset():
            local_phase = phase.get_value() - r_mic
            return 0.28 * np.sin(-local_phase) * arrival_ramp(local_phase)

        diaphragm = always_redraw(lambda: Line(
            [mic_cx.get_value() - 0.42, mic_cy.get_value() + diaphragm_offset(), 0],
            [mic_cx.get_value() + 0.42, mic_cy.get_value() + diaphragm_offset(), 0],
            color=GREEN_C, stroke_width=6,
        ))

        mic_label = Text("microphone diaphragm", font_size=18, color=GRAY_TXT)
        mic_label.add_updater(lambda m: m.move_to([mic_cx.get_value(), mic_cy.get_value() - 1.05, 0]))

        caption1 = Text("bright rings = compression    dim rings = rarefaction",
                         font_size=18, color=GRAY_TXT)
        caption1.move_to(DOWN * 3.35)
        fit_frame(caption1)

        # Narration (0.14-4.54s): "Before any of this touches a single
        # wire, it isn't even electricity yet." - stretch these fade-ins
        # (rather than one quick pass + a frozen hold) so the source,
        # medium and mic keep gently assembling for the whole line.
        self.play(FadeIn(source_dot), FadeIn(source_label), run_time=0.95)
        self.play(FadeIn(field_dots, lag_ratio=0.15), run_time=0.95)
        self.play(FadeIn(mic_housing), FadeIn(mic_frame), FadeIn(mic_label), run_time=0.95)
        self.play(FadeIn(diaphragm), run_time=0.48)
        self.play(FadeIn(rings), FadeIn(caption1), run_time=0.71)
        self.wait(0.44)  # genuine gap in narration before "Its air..." (4.98s)

        # Narration (4.98-6.88s): "Its air slapped into itself,"
        self.play(phase.animate.set_value(1.576), run_time=2.14, rate_func=linear)
        # Narration (7.12s): "sound is a pressure wave" - subtitle lands
        # on the exact words it echoes.
        self.play(FadeIn(subtitle, shift=UP * 0.1),
                  phase.animate.set_value(1.870), run_time=0.4, rate_func=linear)
        # Narration (7.12-16.66s): "...something vibrates, the air around
        # it compresses and stretches and that disturbance spread outward
        # in every direction and a few hundred meters a second." - the
        # wavefront keeps expanding, reaching the mic exactly as the
        # narration turns to talking about the microphone.
        self.play(phase.animate.set_value(r_mic), run_time=9.14, rate_func=linear)

        # ------------------------------------------------------------
        # Beat 2: zoom into the mic - diaphragm push/pull -> voltage.
        # Narration (16.66-21.88s): "A microphone is just a very small,
        # very fast pressure sensor,"
        # ------------------------------------------------------------
        self.play(FadeOut(VGroup(source_dot, source_label, field_dots, rings, caption1)),
                   run_time=0.4)
        self.play(
            mic_cx.animate.set_value(-3.2),
            mic_cy.animate.set_value(0.6),
            run_time=0.5,
        )

        push_pull = Text("push in -> voltage up\npull out -> voltage down",
                          font_size=20, color=WHITE, line_spacing=1.1)
        push_pull.move_to(RIGHT * 2.6 + UP * 1.1)
        fit_frame(push_pull)

        volt_readout = always_redraw(lambda: Text(
            f"{0.9 * np.sin(-(phase.get_value() - r_mic)):+.2f} V",
            font_size=30,
            color=(GREEN_C if np.sin(-(phase.get_value() - r_mic)) >= 0 else RED_C),
        ).move_to(RIGHT * 2.6 + DOWN * 0.7))

        arrow = Arrow(LEFT * 2.0 + UP * 0.6, RIGHT * 1.2 + UP * 0.2, buff=0.15,
                      color=WHITE, stroke_width=3, max_tip_length_to_length_ratio=0.15)

        self.play(Write(push_pull), run_time=0.5)
        self.play(GrowArrow(arrow), FadeIn(volt_readout), run_time=0.5)
        # hold the push/pull demo running through the rest of the
        # "pressure sensor" line
        self.play(phase.animate.set_value(phase.get_value() + 12.07), run_time=3.32, rate_func=linear)
        self.wait(0.38)  # brief gap before "float the voltage over time..."

        # ------------------------------------------------------------
        # Clear beat-2 elements, transition to the continuous graph.
        # Narration (22.26-25.90s): "float the voltage over time and you
        # get the waveform everyone recognizes." - this line IS the
        # graph reveal, so the axes+curve land while it's being spoken.
        # ------------------------------------------------------------
        mic_housing.clear_updaters()
        mic_frame.clear_updaters()
        mic_label.clear_updaters()
        self.play(FadeOut(VGroup(
            mic_housing, mic_frame, mic_label, diaphragm,
            push_pull, volt_readout, arrow, title, subtitle,
        )), run_time=0.5)

        # ------------------------------------------------------------
        # Beat 3: plot voltage vs time - continuous, no numbers yet
        # ------------------------------------------------------------
        graph_title = Text("Voltage vs. Time", font_size=32, color=WHITE)
        graph_title.to_edge(UP, buff=0.5)
        self.play(Write(graph_title), run_time=0.5)

        axes = Axes(
            x_range=[0, 8.2, 1],
            y_range=[-1.3, 1.3, 0.5],
            x_length=10.8,
            y_length=4.3,
            axis_config={"color": WHITE, "include_tip": True, "stroke_width": 2.5,
                         "include_ticks": False},
            tips=True,
        )
        axes.move_to(DOWN * 0.4)

        x_label = Text("time", font_size=22, color=WHITE)
        x_label.next_to(axes.x_axis.get_end(), RIGHT, buff=0.15)
        fit_frame(x_label)
        y_label = Text("voltage", font_size=22, color=WHITE)
        y_label.next_to(axes.y_axis.get_end(), UP, buff=0.15)
        fit_frame(y_label)

        self.play(Create(axes), Write(x_label), Write(y_label), run_time=1.0)

        curve = axes.plot(pressure_func, x_range=[0, 8.2], color=GREEN_C, stroke_width=4)
        self.play(Create(curve), run_time=1.6, rate_func=linear)
        self.wait(0.38)  # genuine gap before "But right now..." (26.28s)

        # Narration (26.28-29.14s): "But right now, it's still pure
        # physics." - the zoom-highlight reveal is stretched to fill this
        # whole line (slow continuous reveal, not quick-then-frozen) to
        # visually back up "still pure physics" (infinite resolution,
        # nothing quantized).

        # zoom-highlight: a tiny window packed with many values.
        # Box is sized tight around the curve's local range (not the full
        # y-axis) so it stays small and low enough that the callout beside
        # it never reaches up into the title.
        t0, t1 = 3.0, 3.6
        local_ys = [pressure_func(t) for t in np.linspace(t0, t1, 30)]
        y_lo, y_hi = min(local_ys) - 0.2, max(local_ys) + 0.2
        box_bl = axes.c2p(t0, y_lo)
        box_tr = axes.c2p(t1, y_hi)
        box = DashedVMobject(
            Rectangle(width=box_tr[0] - box_bl[0], height=box_tr[1] - box_bl[1],
                      color=YELLOW_HL, stroke_width=2.5),
            num_dashes=14,
        )
        box.move_to([(box_bl[0] + box_tr[0]) / 2, (box_bl[1] + box_tr[1]) / 2, 0])

        dense_dots = VGroup(*[
            Dot(axes.c2p(t, pressure_func(t)), radius=0.035, color=YELLOW_HL)
            for t in np.linspace(t0, t1, 9)
        ])

        callout = Text("infinitely many\nvalues in between", font_size=18,
                        color=YELLOW_HL, line_spacing=1.1)
        callout.next_to(box, RIGHT, buff=0.5)
        fit_frame(callout)
        callout_arrow = Arrow(callout.get_left(), box.get_right(), buff=0.15,
                               color=YELLOW_HL, stroke_width=2.5,
                               max_tip_length_to_length_ratio=0.2)

        self.play(Create(box), run_time=0.90)
        self.play(FadeIn(dense_dots, lag_ratio=0.12), run_time=1.07)
        self.play(FadeIn(callout), GrowArrow(callout_arrow), run_time=0.89)
        self.wait(0.38)  # genuine gap before "Not one number exists..." (29.52s)

        # ------------------------------------------------------------
        # Closing caption.
        # Narration (29.52s onward): "Not one number exists..." (the line
        # continues/resolves into scene 03's opening) - caption echoes
        # this exact idea (not digital, not yet). Fade-out/fade-in are
        # slowed to fill the remaining time smoothly instead of a quick
        # cut followed by a frozen hold.
        # ------------------------------------------------------------
        self.play(FadeOut(VGroup(box, dense_dots, callout, callout_arrow)), run_time=0.90)

        caption = Text(
            "Continuous. Analog. Infinite resolution.\nNot digital - not yet.",
            font_size=26, color=WHITE, line_spacing=1.2,
        )
        caption.move_to(DOWN * 3.1)
        fit_frame(caption)
        self.play(FadeIn(caption, shift=UP * 0.15), run_time=1.36)
