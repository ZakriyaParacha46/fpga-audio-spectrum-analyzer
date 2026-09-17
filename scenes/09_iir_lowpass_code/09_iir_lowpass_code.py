"""
Scene 09 - Building an IIR Lowpass From Scratch

Real source: FFTspectrum/VU.srcs/sources_1/new/lowpass_filter.v (verbatim).

This is a single-pole IIR (exponential moving average): each clock, when a
new sample arrives, diff = new_sample - running_average; step = diff >>> shift
(arithmetic right shift, NOT a divider); acc += step. No multiplier, no
divider - just subtract, shift, add. `shift` is a runtime input (4-bit port,
tunable from the board's buttons), not a compile-time parameter, so the
cutoff can be changed live.

Real cutoff table (fs ~= 963.5kHz), from the project's build doc:
  shift=3 -> ~19.2kHz | shift=5 -> ~4.8kHz (lowpass default)
  shift=7 -> ~1.2kHz  | shift=9 -> ~300Hz  | shift=11 -> ~75Hz

Beat order matches the RECORDED narration, which opens on the graphical
"trace chasing the signal" demo before ever mentioning the code:
  "Watch this trace fight to keep up with the signal - that's the entire
  filter, live." (~0-5.4s into this scene)
  "It's a single-pole IIR..." (~5.7-7.3s)                    -> code intro
  "Every cycle: subtract...shift...add the result back."     -> highlight 1
    (~7.6-15.4s)
  "That's the whole filter - no multiplier, no divider..."   -> highlight 2
    (~15.8-18.9s)
  "Watch what happens as shift changes: small shift tracks
  almost exactly; big shift smooths into a lazy crawl."      -> shift demo
    (~19.3-26.7s)
  "And because shift is a runtime input, instead of a
  hardwired constant,"                                       -> cutoff table
    (~27.2-32.3s)
  "you can change the cutoff live, from the board's own
  buttons, while it's running."                               -> closing
    (~33.3-37.8s)

So (unlike the original scene-level ordering, which put the code block
first) the "acc chasing the signal" demo is moved to the very front of
construct() to land under its own narration instead of appearing ~20s
after the words that describe it.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *
import textwrap

RIGHT_X = 5.4  # x-position for highlight labels beside the code box

CUTOFFS = [
    (3, "~19.2kHz", False),
    (5, "~4.8kHz", True),   # lowpass default
    (7, "~1.2kHz", False),
    (9, "~300Hz", False),
    (11, "~75Hz", False),
]

# ---------------------------------------------------------------------------
# Graphical demo helpers - a jittery signal and the acc recurrence chasing it
# (same "busy signal" shape used in scene 08, for visual continuity)
# ---------------------------------------------------------------------------
DEMO_SLOW_AMP = 0.9
DEMO_SLOW_FREQ = 0.55
DEMO_FAST_AMP = 0.3
DEMO_FAST_FREQ = 6.0


def raw_signal(x):
    return DEMO_SLOW_AMP * np.sin(DEMO_SLOW_FREQ * x) + DEMO_FAST_AMP * np.sin(DEMO_FAST_FREQ * x)


def ema_trace(xs, shift):
    """Continuous analog of acc <= acc + (level - acc) >>> shift: each
    valid sample, acc moves a 1/2^shift fraction of the way toward the
    raw sample. shift bigger means a smaller step, so acc moves less
    per sample."""
    ys = raw_signal(xs)
    acc = np.zeros_like(ys)
    acc[0] = ys[0]
    alpha = 1.0 / (2 ** shift)
    for i in range(1, len(xs)):
        acc[i] = acc[i - 1] + (ys[i] - acc[i - 1]) * alpha
    return acc


def make_curve(xs, ys, axes, color, stroke_width=3, opacity=1.0):
    pts = [axes.c2p(x, y) for x, y in zip(xs, ys)]
    curve = VMobject(color=color, stroke_width=stroke_width, stroke_opacity=opacity)
    curve.set_points_as_corners(pts)
    return curve


class IIRLowpassCode(Scene):
    def construct(self):
        set_bg(self)

        xs = np.arange(0, 10, 0.02)
        raw_ys = raw_signal(xs)

        # ------------------------------------------------------------
        # Graphical demo, part 1 - acc chasing a jittery signal.
        # Narration opens here: "Watch this trace fight to keep up with
        # the signal - that's the entire filter, live." (~0-5.4s)
        # ------------------------------------------------------------
        ex_title = Text("Watching acc chase the signal", font_size=32, color=WHITE)
        ex_title.to_edge(UP, buff=0.5)
        ex_sub = Text("acc <= acc + (level - acc) >>> shift, every valid sample",
                       font_size=18, color=GRAY_TXT)
        ex_sub.next_to(ex_title, DOWN, buff=0.2)
        self.play(Write(ex_title), run_time=0.4)
        self.play(FadeIn(ex_sub), run_time=0.3)
        # NOTE: no self.wait() calls anywhere in this construct() other
        # than for a genuine transcript silence - every other bit of
        # "extra time" needed to match the real narration pacing lives in
        # a longer run_time= on the play() that's already animating
        # something (a curve drawing further, a label taking longer to
        # settle, a highlight sweeping through code), so the picture is
        # always still in smooth motion instead of popping in and then
        # freezing on a static frame while the voiceover catches up.

        demo_axes = Axes(
            x_range=[0, 10, 2], y_range=[-1.5, 1.5, 1],
            x_length=9.5, y_length=2.9,
            axis_config={"color": GRAY_TXT, "stroke_width": 2, "include_tip": False},
        )
        demo_axes.move_to(DOWN * 0.6)

        raw_curve = make_curve(xs, raw_ys, demo_axes, GREEN_C, stroke_width=3)

        shift_demo = 5
        acc_ys = ema_trace(xs, shift_demo)
        acc_curve = make_curve(xs, acc_ys, demo_axes, BLUE_C, stroke_width=3)

        raw_label = Text("raw level (jittery)", font_size=18, color=GREEN_C)
        acc_label = Text(f"acc, filtered (shift={shift_demo})", font_size=18, color=BLUE_C)
        legend = VGroup(raw_label, acc_label).arrange(RIGHT, buff=0.6)
        legend.next_to(demo_axes, UP, buff=0.3)
        fit_frame(legend)

        self.play(Create(demo_axes), run_time=0.4)
        # "...fight to keep up with the signal" (~0.5-3.2s) - the raw
        # curve keeps drawing across that whole clause instead of
        # popping in and waiting.
        self.play(Create(raw_curve), FadeIn(raw_label), run_time=1.3)
        # "...the signal. That's the entire filter, live." (~2.8-5.4s) -
        # acc curve continues drawing through this.
        self.play(Create(acc_curve), FadeIn(acc_label), run_time=1.6)

        note = Text("acc smooths the fast wiggles away, but lags a little behind the trend.",
                     font_size=18, color=GRAY_TXT)
        note.next_to(demo_axes, DOWN, buff=0.3)
        fit_frame(note)
        # Slow settle through the rest of "That's the entire filter, live."
        self.play(FadeIn(note, shift=UP * 0.1), run_time=1.36)

        self.play(FadeOut(VGroup(ex_title, ex_sub, demo_axes, raw_curve, acc_curve, legend, note)), run_time=0.4)

        # ------------------------------------------------------------
        # Title + code box
        # Narration: "It's a single-pole IIR..." (~5.7-7.3s)
        # ------------------------------------------------------------
        title = Text("Building an IIR Lowpass From Scratch", font_size=34, color=WHITE)
        title.to_edge(UP, buff=0.35)
        subtitle = Text("lowpass_filter.v - one line of arithmetic, hand-verifiable",
                         font_size=18, color=GRAY_TXT)
        subtitle.next_to(title, DOWN, buff=0.15)

        self.play(Write(title), run_time=0.5)
        self.play(FadeIn(subtitle), run_time=0.3)

        box_w, box_h = 10.67, 5.2
        box_center = LEFT * 1.6 + DOWN * 0.35
        box = code_box(width=box_w, height=box_h, center=box_center)
        # Slow fade-in carries through the rest of "single-pole IIR."
        self.play(FadeIn(box), run_time=0.76)

        # ------------------------------------------------------------
        # Build the module, verbatim, token-colored
        # ------------------------------------------------------------
        L = []
        L.append(code_line(0, [("module", KEYWORD), ("lowpass_filter", SIGNAL), ("(", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("wire", KEYWORD), ("clk,", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("wire", KEYWORD), ("reset,", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("wire", KEYWORD), ("[11:0]", NUMBER), ("level,", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("wire", KEYWORD), ("level_valid,", SIGNAL)]))
        L.append(code_line(4, [("input", KEYWORD), ("wire", KEYWORD), ("[3:0]", NUMBER), ("shift,", SIGNAL)]))
        L.append(code_line(4, [("output", KEYWORD), ("wire", KEYWORD), ("[11:0]", NUMBER), ("level_filtered", SIGNAL)]))
        L.append(code_line(0, [(");", SIGNAL)]))
        L.append(code_line(4, [("reg", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("acc;", SIGNAL)],
                            comment="// holds 0-4095 as a signed 13-bit value"))
        L.append(code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("level_s", SIGNAL),
                                ("=", SIGNAL), ("{1'b0,", NUMBER), ("level};", SIGNAL)]))
        L.append(code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("diff", SIGNAL),
                                ("=", SIGNAL), ("level_s", SIGNAL), ("-", SIGNAL), ("acc;", SIGNAL)]))
        L.append(code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("step", SIGNAL),
                                ("=", SIGNAL), ("diff", SIGNAL), (">>>", SIGNAL), ("shift;", SIGNAL)],
                            comment="// arithmetic shift keeps the sign"))
        L.append(code_line(4, [("wire", KEYWORD), ("signed", KEYWORD), ("[12:0]", NUMBER), ("next", SIGNAL),
                                ("=", SIGNAL), ("acc", SIGNAL), ("+", SIGNAL), ("step;", SIGNAL)]))
        L.append(code_line(4, [("always", KEYWORD), ("@(posedge", KEYWORD), ("clk)", SIGNAL), ("begin", KEYWORD)]))
        L.append(code_line(8, [("if", KEYWORD), ("(reset)", SIGNAL)]))
        L.append(code_line(12, [("acc", SIGNAL), ("<=", SIGNAL), ("13'sd0;", NUMBER)]))
        L.append(code_line(8, [("else", KEYWORD), ("if", KEYWORD), ("(level_valid)", SIGNAL)]))
        L.append(code_line(12, [("acc", SIGNAL), ("<=", SIGNAL), ("next;", SIGNAL)]))
        L.append(code_line(4, [("end", KEYWORD)]))
        L.append(code_line(4, [("assign", KEYWORD), ("level_filtered", SIGNAL), ("=", SIGNAL), ("acc[11:0];", SIGNAL)]))
        L.append(code_line(0, [("endmodule", KEYWORD)]))

        def gap():
            return {"group": Rectangle(width=0.01, height=0.05, stroke_opacity=0, fill_opacity=0)}

        # index map into L (the flat list built above, before gaps are spliced in):
        # 0 module, 1-6 ports, 7 );, 8 reg acc, 9 level_s, 10 diff, 11 step,
        # 12 next, 13 always, 14 if(reset), 15 acc<=0, 16 else if,
        # 17 acc<=next, 18 end, 19 assign, 20 endmodule
        layout = L[0:8] + [gap()] + L[8:9] + [gap()] + L[9:13] + [gap()] + \
                 L[13:19] + [gap()] + L[19:20] + [gap()] + L[20:21]
        full_code = VGroup(*[item["group"] for item in layout])
        full_code.arrange(DOWN, aligned_edge=LEFT, buff=0.05)

        avail_w = box_w - 0.5
        avail_h = box_h - 0.4
        scale = min(avail_w / full_code.width, avail_h / full_code.height, 1.0)
        full_code.scale(scale)
        full_code.move_to(box.get_center())

        # Code lands across the tail of "single-pole IIR" (~7.6s).
        self.play(
            LaggedStart(*[FadeIn(item["group"], shift=UP * 0.04) for item in L], lag_ratio=0.05),
            run_time=1.2,
        )

        # ------------------------------------------------------------
        # Highlight helper (rect + arrow + label beside the box)
        # ------------------------------------------------------------
        def show_label(target, text, prev_rect, wrap=24):
            rect = SurroundingRectangle(
                target, color=YELLOW_HL, buff=0.06, stroke_width=0,
                fill_color=YELLOW_HL, fill_opacity=0.25,
            )
            if prev_rect is None:
                self.play(FadeIn(rect), run_time=0.4)
            else:
                self.play(Transform(prev_rect, rect), run_time=0.4)
                rect = prev_rect

            y = max(-3.2, min(3.2, target.get_center()[1]))
            label = Text(textwrap.fill(text, width=wrap), font_size=19,
                         color=WHITE, line_spacing=0.9)
            label.move_to(RIGHT * RIGHT_X + UP * y)
            fit_frame(label)

            arrow = Arrow(rect.get_right(), label.get_left() + LEFT * 0.15,
                          buff=0.1, color=YELLOW_HL, stroke_width=3)
            self.play(GrowArrow(arrow), FadeIn(label, shift=LEFT * 0.15), run_time=0.5)
            return rect, label, arrow

        def hide(mobs, run_time=0.3):
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)

        rect = None

        # diff / step / next - subtract, shift, add.
        # Narration: "Every cycle: subtract the running average from the
        # new sample (~8.3-10.8s), shift that difference right by some
        # amount (~11.0-13.5s), and add the result back (~13.5-15.4s)."
        # Rather than one static highlight box sitting still for the
        # whole ~6s sentence, the outer box+label land once (covering the
        # whole "subtract/shift/add" block) and a short pulse sweeps
        # through diff -> step -> next in turn, so something is always
        # visibly moving in step with which operation is being narrated.
        target1 = VGroup(L[10]["group"], L[11]["group"], L[12]["group"])
        rect, label1, arrow1 = show_label(
            target1, "subtract, shift, add - no divider, no multiplier", rect,
        )
        self.play(Indicate(L[10]["group"], color=YELLOW_HL, scale_factor=1.1), run_time=1.42)
        self.play(Indicate(L[11]["group"], color=YELLOW_HL, scale_factor=1.1), run_time=2.48)
        self.play(Indicate(L[12]["group"], color=YELLOW_HL, scale_factor=1.1), run_time=2.08)
        hide([rect, label1, arrow1], run_time=0.36)
        rect = None

        # acc <= next - becomes the new running average.
        # Narration: "That's the whole filter - no multiplier, no divider
        # circuit..." (~15.8-18.9s). The arrow+label take their time
        # settling into place (GrowArrow/FadeIn stretched) across most of
        # that sentence instead of appearing instantly and then waiting.
        target2 = L[17]["group"]
        rect_new = SurroundingRectangle(
            target2, color=YELLOW_HL, buff=0.06, stroke_width=0,
            fill_color=YELLOW_HL, fill_opacity=0.25,
        )
        self.play(FadeIn(rect_new), run_time=0.4)
        rect = rect_new
        y2 = max(-3.2, min(3.2, target2.get_center()[1]))
        label2 = Text(textwrap.fill("next becomes the new acc every valid sample", width=24),
                       font_size=19, color=WHITE, line_spacing=0.9)
        label2.move_to(RIGHT * RIGHT_X + UP * y2)
        fit_frame(label2)
        arrow2 = Arrow(rect.get_right(), label2.get_left() + LEFT * 0.15,
                       buff=0.1, color=YELLOW_HL, stroke_width=3)
        self.play(GrowArrow(arrow2), FadeIn(label2, shift=LEFT * 0.15), run_time=2.78)

        self.play(FadeOut(VGroup(rect, label2, arrow2, box, full_code, title, subtitle)), run_time=0.36)

        # ------------------------------------------------------------
        # Graphical demo, part 2 - small shift vs large shift, side by side
        # Narration: "Watch what happens as that shift amount changes: a
        # small shift tracks the signal almost exactly, jitter and all;
        # a big shift smooths everything into a lazy crawl that lags
        # behind." (~19.3-26.7s)
        # ------------------------------------------------------------
        cmp_title = Text("bigger shift = smoother, slower to react", font_size=28, color=WHITE)
        cmp_title.to_edge(UP, buff=0.5)
        self.play(Write(cmp_title), run_time=0.4)

        def make_small_axes(center):
            ax = Axes(
                x_range=[0, 10, 2], y_range=[-1.5, 1.5, 1],
                x_length=5.4, y_length=2.5,
                axis_config={"color": GRAY_TXT, "stroke_width": 2, "include_tip": False},
            )
            ax.move_to(center)
            return ax

        left_axes = make_small_axes(LEFT * 3.5 + DOWN * 0.6)
        right_axes = make_small_axes(RIGHT * 3.5 + DOWN * 0.6)

        left_raw = make_curve(xs, raw_ys, left_axes, GREEN_C, stroke_width=2, opacity=0.5)
        right_raw = make_curve(xs, raw_ys, right_axes, GREEN_C, stroke_width=2, opacity=0.5)

        shift_small = 2
        shift_large = 8
        left_curve = make_curve(xs, ema_trace(xs, shift_small), left_axes, NUMBER, stroke_width=3)
        right_curve = make_curve(xs, ema_trace(xs, shift_large), right_axes, BLUE_C, stroke_width=3)

        left_title = Text(f"shift = {shift_small}", font_size=22, color=NUMBER)
        left_title.next_to(left_axes, UP, buff=0.25)
        left_sub = Text("fast, still jittery", font_size=15, color=GRAY_TXT)
        left_sub.next_to(left_axes, DOWN, buff=0.25)

        right_title = Text(f"shift = {shift_large}", font_size=22, color=BLUE_C)
        right_title.next_to(right_axes, UP, buff=0.25)
        right_sub = Text("smooth, slow to react", font_size=15, color=GRAY_TXT)
        right_sub.next_to(right_axes, DOWN, buff=0.25)

        self.play(
            Create(left_axes), Create(right_axes),
            FadeIn(left_title), FadeIn(right_title),
            run_time=0.4,
        )
        self.play(Create(left_raw), Create(right_raw), run_time=0.3)
        # "A small shift tracks the signal almost exactly" (~19.6-23.4s) -
        # the curve draws itself across the whole clause in real time
        # instead of popping in and sitting still.
        self.play(Create(left_curve), run_time=3.02)
        self.play(FadeIn(left_sub, shift=UP * 0.08), run_time=0.3)
        # "A big shift smooths everything into a lazy crawl" (~23.7-26.7s)
        self.play(Create(right_curve), run_time=2.66)
        self.play(FadeIn(right_sub, shift=UP * 0.08), run_time=0.3)

        self.play(FadeOut(VGroup(
            cmp_title, left_axes, right_axes, left_raw, right_raw,
            left_curve, right_curve, left_title, right_title, left_sub, right_sub,
        )), run_time=0.5)

        # ------------------------------------------------------------
        # Real cutoff table
        # Narration: "And because shift is a runtime input, instead of a
        # hardwired constant," (~27.2-32.3s)
        # ------------------------------------------------------------
        tbl_title = Text("shift -> cutoff frequency", font_size=32, color=WHITE)
        tbl_title.to_edge(UP, buff=0.5)
        fs_note = Text("sample rate fs ~= 963.5kHz", font_size=18, color=GRAY_TXT)
        fs_note.next_to(tbl_title, DOWN, buff=0.2)
        self.play(Write(tbl_title), run_time=0.4)
        self.play(FadeIn(fs_note), run_time=0.3)

        rows = VGroup()
        default_tag = None
        for shift_val, freq, is_default in CUTOFFS:
            color = GREEN_C if is_default else WHITE
            row = code_line(0, [("shift", SIGNAL if not is_default else GREEN_C),
                                 ("=", SIGNAL), (str(shift_val), NUMBER),
                                 ("->", SIGNAL), (freq, color)])
            rows.add(row["group"])
            if is_default:
                tag = Text("<- lowpass default", font_size=18, color=GREEN_C)
                tag.next_to(row["group"], RIGHT, buff=0.4)
                default_tag = (row["group"], tag)

        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        rows.scale(1.5)
        rows.move_to(ORIGIN + DOWN * 0.15)
        fit_frame(rows)

        # Rows count off slowly across "runtime input, instead of a
        # hardwired constant" instead of popping in all at once.
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.08) for r in rows], lag_ratio=0.15), run_time=2.5)

        if default_tag is not None:
            row_group, tag = default_tag
            tag.next_to(row_group, RIGHT, buff=0.4)
            fit_frame(tag)
            self.play(FadeIn(tag, shift=LEFT * 0.1), Indicate(row_group, color=GREEN_C, scale_factor=1.05),
                       run_time=1.92)

        self.play(FadeOut(VGroup(tbl_title, fs_note, rows, default_tag[1] if default_tag else VGroup())),
                   run_time=0.3)
        # Genuine transcript gap between "...hardwired constant," and
        # "you can change..." (~1.0s of real silence).
        self.wait(0.74)

        # ------------------------------------------------------------
        # Closing - shift is a runtime input
        # Narration: "you can change the cutoff live, from the board's
        # own buttons, while it's running." (~33.3-37.8s)
        # ------------------------------------------------------------
        close_title = Text("shift is a runtime input, not a constant", font_size=30, color=WHITE)
        close_title.to_edge(UP, buff=1.0)

        port_line = code_line(0, [("input", KEYWORD), ("wire", KEYWORD), ("[3:0]", NUMBER), ("shift,", SIGNAL)])
        port_line["group"].scale(1.8)
        port_line["group"].move_to(ORIGIN + UP * 0.3)

        port_box = code_box(width=port_line["group"].width + 0.8, height=port_line["group"].height + 0.6,
                             center=port_line["group"].get_center())

        # "you can change" (~33.3-33.8s)
        self.play(Write(close_title), run_time=0.4)
        # "the cut-off" (~34.0-34.4s)
        self.play(FadeIn(port_box), FadeIn(port_line["group"]), run_time=0.6)

        glow = SurroundingRectangle(port_line["group"], color=YELLOW_HL, buff=0.08, stroke_width=0,
                                     fill_color=YELLOW_HL, fill_opacity=0.25)
        # "life [live] from the board" (~34.4-35.8s)
        self.play(FadeIn(glow), run_time=0.4)

        closing = Text("a 4-bit port - the cutoff is tuned live, from the board's buttons.",
                        font_size=22, color=GRAY_TXT)
        closing.next_to(port_box, DOWN, buff=0.6)
        fit_frame(closing)
        # Slow settle carries through "on button while it's running." and
        # a touch of trailing silence after (~35.8-37.8s + pad).
        self.play(FadeIn(closing, shift=UP * 0.15), run_time=3.44)
