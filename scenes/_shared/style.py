"""
Shared palette + helpers for the Audio Scope on a Basys3 video.

Mirrors the conventions established in ~/Desktop/Youtube/mmnist/scenes/
(the neural-net-on-fpga video) so this video looks like part of the same
series. Every scene file should `from style import *`.
"""
from manim import *
import numpy as np
import textwrap

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
BG = "#000000"

GREEN_C = "#00ff88"   # positive / correct / signal-good / lowpass
RED_C = "#ff4444"     # negative / clipping / error
YELLOW_HL = "#ffff00" # highlight rectangles / active attention
BLUE_C = "#3f6bff"    # lowpass cutoff marker (matches the artifact's blue)
PURPLE_C = "#c04ce0"  # highpass cutoff marker (matches the artifact's purple)
GRAY_TXT = GRAY_B

# code-box palette (Verilog syntax coloring)
BOX_FILL = "#1e1e2e"
BOX_BORDER = "#3a3a5a"
KEYWORD = "#cc99ff"
NUMBER = "#ffaa44"
COMMENT = "#555577"
SIGNAL = "#ffffff"
SYSTASK = "#66aaff"

CODE_FONT = "Menlo"
CODE_FONT_SIZE = 18

# ---------------------------------------------------------------------------
# Frame-safety helper (identical contract to mmnist's fit_frame)
# ---------------------------------------------------------------------------
FRAME_X = 7.1
FRAME_Y = 4.0
MARGIN = 0.15


def fit_frame(mob, margin=MARGIN):
    """Shift a mobject (in place) so its bounding box stays within the
    visible camera frame. Safety net against off-screen clipping."""
    left = mob.get_left()[0]
    right = mob.get_right()[0]
    top = mob.get_top()[1]
    bottom = mob.get_bottom()[1]
    dx = 0.0
    dy = 0.0
    if right > FRAME_X - margin:
        dx = (FRAME_X - margin) - right
    elif left < -FRAME_X + margin:
        dx = (-FRAME_X + margin) - left
    if top > FRAME_Y - margin:
        dy = (FRAME_Y - margin) - top
    elif bottom < -FRAME_Y + margin:
        dy = (-FRAME_Y + margin) - bottom
    if dx or dy:
        mob.shift([dx, dy, 0])
    return mob


def set_bg(scene):
    """Call at the top of every construct(): standardizes the black bg."""
    config.background_color = BG
    scene.camera.background_color = BG


# ---------------------------------------------------------------------------
# Code-box builder (token-colored Verilog/Python snippets, from real RTL)
# ---------------------------------------------------------------------------
def code_frag(s, color):
    return Text(s, font=CODE_FONT, font_size=CODE_FONT_SIZE, color=color)


def code_line(indent, tokens, comment=None, char_w=None):
    """tokens: list of (text, color) pairs. Returns a dict with the
    assembled group plus handles for later highlighting."""
    if char_w is None:
        char_w = code_frag("0", SIGNAL).width
    frags = [code_frag(t, c) for t, c in tokens]
    parts = []
    if indent > 0:
        w = max(indent * char_w, 0.001)
        parts.append(Rectangle(width=w, height=0.001, stroke_opacity=0, fill_opacity=0))
    parts.extend(frags)
    code = VGroup(*parts).arrange(RIGHT, buff=0.09, aligned_edge=DOWN)
    group = VGroup(code)
    if comment:
        c = code_frag(comment, COMMENT)
        c.next_to(code, RIGHT, buff=0.35)
        group.add(c)
    return {"group": group, "code": code, "frags": frags}


def code_box(width=10.67, height=5.2, center=ORIGIN):
    box = RoundedRectangle(
        width=width, height=height, corner_radius=0.15,
        fill_color=BOX_FILL, fill_opacity=1.0,
        stroke_color=BOX_BORDER, stroke_width=2,
    )
    box.move_to(center)
    return box
