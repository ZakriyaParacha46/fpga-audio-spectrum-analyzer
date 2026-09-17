"""
Scene 13 - What Is the FFT

Narrative beat: the previous scene established the DFT costs O(N^2) --
for N=512 that's ~262,144 multiplies. This scene introduces the classic
speedup, the FFT: divide-and-conquer splits the DFT into halves,
recursively, down to single points (log2(512) = 9 stages), recombined
with "butterflies" and twiddle factors, bringing total cost down to
N*log2(N). But it requires bit-reversed addressing and staged,
criss-crossing indexing - real control-flow complexity.

IMPORTANT: this scene sets up a contrast with scene 14 (which reveals the
project actually used Goertzel resonators instead). Do NOT resolve that
tension here - just establish what an FFT/butterfly network is and looks
like, ending on the complexity point.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from style import *

N = 512
N_SQUARED = N * N
STAGES = 9  # log2(512)
N_LOGN = N * STAGES


def split_box(label, w, h, font_size, color=WHITE):
    box = RoundedRectangle(width=w, height=h, corner_radius=0.06,
                            fill_color=BOX_FILL, fill_opacity=1, stroke_color=color, stroke_width=2)
    txt = Text(label, font_size=font_size, color=color)
    txt.move_to(box.get_center())
    return VGroup(box, txt)


class WhatIsTheFFT(Scene):
    def construct(self):
        set_bg(self)

        # ------------------------------------------------------------
        # Title
        # ------------------------------------------------------------
        title = Text("What Is the FFT?", font_size=40, color=WHITE)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=0.7)

        # ------------------------------------------------------------
        # Beat 1: recap the N^2 problem
        # narration: "A quarter million multiplications is the kind of
        # number that makes engineers invent shortcuts" (0.1-4.52) - the
        # line is slowly written out (not popped in + frozen) so it's
        # still resolving as the number is spoken.
        # ------------------------------------------------------------
        recap = Text(f"straight DFT: {N} points -> {N}² ≈ {N_SQUARED:,} multiplies",
                     font_size=26, color=RED_C)
        recap.next_to(title, DOWN, buff=0.6)
        fit_frame(recap)
        self.play(Write(recap), run_time=3.8)

        # narration: "And the famous one is the fast Fourier transform." (5.54-8.14)
        idea = Text("the FFT: split the problem instead of brute-forcing it",
                    font_size=24, color=WHITE)
        idea.next_to(recap, DOWN, buff=0.4)
        fit_frame(idea)
        self.play(Write(idea), run_time=3.3)
        self.play(FadeOut(VGroup(recap, idea)), run_time=0.5)

        # ------------------------------------------------------------
        # Beat 2: divide-and-conquer recursive split tree
        # ------------------------------------------------------------
        tree_title = Text("Divide and conquer: split N in half, recursively",
                          font_size=24, color=WHITE)
        tree_title.next_to(title, DOWN, buff=0.5)
        fit_frame(tree_title)
        self.play(FadeIn(tree_title), run_time=0.5)

        row0_y = 1.75
        row1_y = 0.95
        row2_y = 0.15
        row3_y = -0.65
        row4_y = -1.45

        b0 = split_box("512", 1.3, 0.55, 22)
        b0.move_to(UP * row0_y)

        b1a = split_box("256", 1.05, 0.5, 20)
        b1b = split_box("256", 1.05, 0.5, 20)
        VGroup(b1a, b1b).arrange(RIGHT, buff=1.6).move_to(UP * row1_y)

        b2 = VGroup(*[split_box("128", 0.9, 0.45, 17) for _ in range(4)])
        b2.arrange(RIGHT, buff=0.55).move_to(UP * row2_y)

        dots_row = Text("⋮  splitting continues  ⋮", font_size=20, color=GRAY_TXT)
        dots_row.move_to(UP * row3_y)

        b4 = VGroup(*[split_box("1", 0.45, 0.4, 16) for _ in range(8)])
        b4.arrange(RIGHT, buff=0.28).move_to(UP * row4_y)

        tree = VGroup(b0, b1a, b1b, b2, dots_row, b4)
        fit_frame(tree)

        def connectors(parent, children):
            lines = VGroup()
            for c in children:
                lines.add(Line(parent.get_bottom(), c.get_top(), color=GRAY_TXT, stroke_width=2))
            return lines

        lines01 = connectors(b0, [b1a, b1b])
        lines12 = VGroup(
            *connectors(b1a, [b2[0], b2[1]]),
            *connectors(b1b, [b2[2], b2[3]]),
        )
        lines_dots = VGroup(*[Line(b2[i].get_bottom(), dots_row.get_top() + RIGHT * (i - 1.5) * 0.5,
                                    color=GRAY_TXT, stroke_width=2) for i in range(4)])
        lines_final = VGroup(*[Line(dots_row.get_bottom() + RIGHT * (i - 3.5) * 0.5, b4[i].get_top(),
                                     color=GRAY_TXT, stroke_width=2) for i in range(8)])

        # narration: "Split the problem in half, then half again" (8.42-10.8)
        self.play(FadeIn(b0), run_time=0.3)
        self.play(Create(lines01), FadeIn(b1a), FadeIn(b1b), run_time=0.7)
        self.play(Create(lines12), FadeIn(b2), run_time=0.7)
        self.play(Create(lines_dots), FadeIn(dots_row), run_time=0.7)
        self.play(Create(lines_final), FadeIn(b4), run_time=0.9)

        # narration: "recombines the pieces with what are called
        # butterflies" (11.06-15.08) - written slowly so it's still
        # resolving while that phrase plays out.
        stage_note = Text(f"log₂(512) = {STAGES} stages", font_size=22, color=YELLOW_HL)
        stage_note.next_to(b4, DOWN, buff=0.45)
        fit_frame(stage_note)
        self.play(Write(stage_note), run_time=2.9)

        # narration: "the total cost collapses from N squared all the way
        # down to N log N... For 512 points, that's a massive win." (15.08-23.98)
        cost_line = Text(f"cost: {N} × {STAGES} ≈ {N_LOGN:,}   (vs {N_SQUARED:,} before)",
                         font_size=22, color=GREEN_C)
        cost_line.next_to(stage_note, DOWN, buff=0.3)
        fit_frame(cost_line)
        self.play(Write(cost_line), run_time=8.9)

        # narration: "But that speed comes with a cost of its own."
        # (24.58-27.54) - the whole "win" tableau slowly dissolves as
        # narration pivots to the complexity caveat, instead of sitting
        # frozen then cutting away.
        self.play(FadeOut(VGroup(
            tree_title, tree, lines01, lines12, lines_dots, lines_final,
            stage_note, cost_line,
        )), run_time=4.0)

        # ------------------------------------------------------------
        # Beat 3 (was Beat 4): bit-reversed addressing
        # narration: "Bit reversed, addressing," (27.92-29.38) - moved to
        # play first since it's literally the first item named
        # ------------------------------------------------------------
        br_title = Text("...and it needs bit-reversed addressing", font_size=26, color=WHITE)
        br_title.next_to(title, DOWN, buff=0.5)
        fit_frame(br_title)
        self.play(FadeIn(br_title), run_time=0.3)

        idx_lbl = Text("index 1", font_size=22, color=WHITE)
        bin_lbl = Text("001", font_size=30, color=YELLOW_HL)
        arrow = Text("→ reversed →", font_size=20, color=GRAY_TXT)
        rev_lbl = Text("100", font_size=30, color=YELLOW_HL)
        idx2_lbl = Text("= index 4", font_size=22, color=WHITE)

        bits_row = VGroup(idx_lbl, bin_lbl, arrow, rev_lbl, idx2_lbl).arrange(RIGHT, buff=0.35)
        bits_row.move_to(UP * 1.3)
        fit_frame(bits_row)
        self.play(Write(idx_lbl), Write(bin_lbl), run_time=0.5)
        self.play(FadeIn(arrow), Write(rev_lbl), run_time=0.45)
        self.play(FadeIn(idx2_lbl), run_time=0.6)

        natural = [0, 1, 2, 3, 4, 5, 6, 7]
        reversed_order = [0, 4, 2, 6, 1, 5, 3, 7]

        def index_row(values, label, color):
            boxes = VGroup(*[split_box(str(v), 0.7, 0.55, 18, color=color) for v in values])
            boxes.arrange(RIGHT, buff=0.12)
            lbl = Text(label, font_size=18, color=GRAY_TXT)
            lbl.next_to(boxes, LEFT, buff=0.3)
            row = VGroup(lbl, boxes)
            return row

        row_natural = index_row(natural, "natural:", WHITE)
        row_reversed = index_row(reversed_order, "reordered:", GREEN_C)
        rows = VGroup(row_natural, row_reversed).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        rows.move_to(DOWN * 0.7)
        fit_frame(rows)

        self.play(FadeIn(row_natural), run_time=0.4)
        self.play(FadeIn(row_reversed), run_time=0.6)

        # narration: "staged" (29.96) leading into "butterflies," (30.28-30.92)
        idx1_box = row_natural[1][1]
        idx4_box_after = row_reversed[1][0]
        self.play(Indicate(idx1_box, color=YELLOW_HL, scale_factor=1.2),
                  Indicate(idx4_box_after, color=YELLOW_HL, scale_factor=1.2), run_time=0.7)

        self.play(FadeOut(VGroup(br_title, bits_row, rows)), run_time=0.35)

        # ------------------------------------------------------------
        # Beat 4 (was Beat 3): the butterfly network
        # narration: "staged butterflies, indexing that has to be exactly
        # right at every single stage." (29.96-34.94)
        # ------------------------------------------------------------
        bf_title = Text("Recombined with \"butterflies\"", font_size=26, color=WHITE)
        bf_title.next_to(title, DOWN, buff=0.5)
        fit_frame(bf_title)
        self.play(FadeIn(bf_title), run_time=0.3)

        in0 = Dot(LEFT * 3.2 + UP * 1.0, radius=0.07, color=WHITE)
        in1 = Dot(LEFT * 3.2 + DOWN * 0.4, radius=0.07, color=WHITE)
        out0 = Dot(RIGHT * 0.2 + UP * 1.0, radius=0.07, color=GREEN_C)
        out1 = Dot(RIGHT * 0.2 + DOWN * 0.4, radius=0.07, color=GREEN_C)

        in0_lbl = Text("x0", font_size=20, color=WHITE).next_to(in0, LEFT, buff=0.2)
        in1_lbl = Text("x1", font_size=20, color=WHITE).next_to(in1, LEFT, buff=0.2)
        out0_lbl = Text("X0", font_size=20, color=GREEN_C).next_to(out0, RIGHT, buff=0.2)
        out1_lbl = Text("X1", font_size=20, color=GREEN_C).next_to(out1, RIGHT, buff=0.2)

        straight0 = Line(in0.get_center(), out0.get_center(), color=WHITE, stroke_width=2.5)
        straight1 = Line(in1.get_center(), out1.get_center(), color=WHITE, stroke_width=2.5)
        cross0 = Line(in0.get_center(), out1.get_center(), color=YELLOW_HL, stroke_width=2.5)
        cross1 = Line(in1.get_center(), out0.get_center(), color=YELLOW_HL, stroke_width=2.5)

        twiddle_lbl = Text("× W (twiddle factor)", font_size=18, color=YELLOW_HL)
        twiddle_lbl.next_to(VGroup(cross0, cross1), DOWN, buff=0.35)
        fit_frame(twiddle_lbl)

        butterfly = VGroup(in0, in1, out0, out1, in0_lbl, in1_lbl, out0_lbl, out1_lbl,
                           straight0, straight1, cross0, cross1)

        self.play(FadeIn(in0), FadeIn(in1), Write(in0_lbl), Write(in1_lbl), run_time=0.35)
        self.play(Create(straight0), Create(straight1), Create(cross0), Create(cross1), run_time=0.45)
        self.play(FadeIn(out0), FadeIn(out1), Write(out0_lbl), Write(out1_lbl), run_time=0.35)
        self.play(FadeIn(twiddle_lbl, shift=UP * 0.1), run_time=0.45)

        self.play(FadeOut(twiddle_lbl), run_time=0.2)
        self.play(butterfly.animate.scale(0.55).move_to(LEFT * 4.3 + UP * 0.3), run_time=0.35)

        # small multi-stage network sketch (iconic, not a real 512-point graph)
        net_title = Text("stacked across stages → a butterfly network",
                         font_size=22, color=WHITE)
        net_title.move_to(RIGHT * 1.1 + UP * 1.7)
        fit_frame(net_title)
        self.play(FadeIn(net_title), run_time=0.3)

        n_nodes = 4
        stage_x = [-1.6, 0.4, 2.4]
        cols = []
        for sx in stage_x:
            col = VGroup(*[Dot(RIGHT * sx + UP * (1.05 - i * 0.7), radius=0.06, color=WHITE)
                           for i in range(n_nodes)])
            cols.append(col)
        net_dots = VGroup(*cols)

        # continuation cue: only 2 of the real 9 FFT stages are drawn here
        # (iconic sketch, not the full 512-point network) - without this the
        # network reads as if it simply stops, which looks like missing lines
        continue_cue = Text("⋯", font_size=32, color=GRAY_TXT)
        continue_cue.next_to(cols[-1], RIGHT, buff=0.3)

        net_lines = VGroup()
        for s in range(2):
            col_a, col_b = cols[s], cols[s + 1]
            for i in range(n_nodes):
                for j in range(n_nodes):
                    same_group = (i // 2 == j // 2) if s == 0 else ((i % 2) == (j % 2))
                    if same_group:
                        col = YELLOW_HL if i != j else GRAY_TXT
                        net_lines.add(Line(col_a[i].get_center(), col_b[j].get_center(),
                                            color=col, stroke_width=1.6, stroke_opacity=0.85))

        network = VGroup(net_lines, net_dots, continue_cue)
        network.move_to(RIGHT * 1.1 + DOWN * 0.1)
        fit_frame(network)

        self.play(FadeIn(net_dots), run_time=0.25)
        self.play(Create(net_lines), run_time=0.55)
        self.play(FadeIn(continue_cue), run_time=0.3)

        # narration: "...exactly right at every single stage." (31.64-34.94)
        net_note = Text("staged, criss-crossing recombination - 2 of 9 real stages shown",
                         font_size=18, color=GRAY_TXT)
        net_note.next_to(network, DOWN, buff=0.35)
        fit_frame(net_note)
        self.play(FadeIn(net_note), run_time=0.6)

        self.play(FadeOut(VGroup(bf_title, butterfly, net_title, network, net_note)), run_time=0.35)

        # ------------------------------------------------------------
        # Beat 5: closing - big win, but complex control flow
        # narration: "The kind that's easy to get subtly wrong and brutal
        # to debug without a simulator watching your back." (35.54-42.16)
        # ------------------------------------------------------------
        self.play(FadeOut(title), run_time=0.2)

        line1 = Text(f"N log N is a big win - for {N} points, a huge one.",
                     font_size=28, color=GREEN_C)
        line1.move_to(UP * 1.1)
        fit_frame(line1)
        self.play(FadeIn(line1, shift=UP * 0.15), run_time=0.6)

        # "The kind that's easy to get subtly wrong," (35.86-38.88) -
        # written slowly across the whole phrase rather than popping in
        # and freezing.
        line2 = Text("But the control flow is easy to get subtly wrong,",
                     font_size=26, color=WHITE)
        line2.next_to(line1, DOWN, buff=0.45)
        fit_frame(line2)
        self.play(Write(line2), run_time=1.9)

        # "and brutal to debug without a simulator watching your back." (38.88-42.16)
        line3 = Text("and hard to debug without a simulator.",
                     font_size=26, color=RED_C)
        line3.next_to(line2, DOWN, buff=0.35)
        fit_frame(line3)
        self.play(Write(line3), run_time=2.68)
