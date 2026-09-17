"""
Stitches every built scene's rendered preview.mp4 into one review reel, with
a short title card between each scene so it's easy to tell what's playing
without pausing. Uses cv2 directly (not ffmpeg, which is broken on this
machine, see the skill's environment-gotchas section) so this only depends
on the same opencv-python already used for frame review.

Run with the manim/framework python:
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 make_review_reel.py
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

SCENES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (folder, display title) in video order
SCENES = [
    ("02_what_is_audio", "02 - What Is Audio"),
    ("03_sampling_and_the_adc", "03 - Sampling & the ADC"),
    ("04_nyquist_theorem", "04 - The Nyquist Theorem"),
    ("06_voltage_divider", "06 - The Voltage Divider"),
    ("07_signal_path_overview", "07 - Signal Path Overview"),
    ("08_what_is_a_filter", "08 - What Is a Filter"),
    ("09_iir_lowpass_code", "09 - Building an IIR Lowpass From Scratch"),
    ("10_complementary_highpass_code", "10 - The Complementary Highpass"),
    ("11_what_is_fourier_transform", "11 - What Is a Fourier Transform"),
    ("11b_harmonics", "11b - Harmonics"),
    ("12_dft_math", "12 - The DFT, The Math"),
    ("13_what_is_the_fft", "13 - What Is the FFT"),
    ("14_goertzel_implementation_code", "14 - How It's Actually Implemented"),
    ("15_log_compression_code", "15 - Compressing the Spectrum"),
    ("16_vga_and_headroom_bug", "16 - Drawing It on VGA"),
]

W, H = 854, 480
FPS = 15
CARD_SECONDS = 1.3
CARD_FRAMES = int(CARD_SECONDS * FPS)

FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def load_font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def make_title_card(title, index, total):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_title = load_font(34)
    font_sub = load_font(16)

    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((W - tw) / 2, (H - th) / 2 - 10), title, font=font_title, fill=(255, 255, 255))

    sub = f"scene {index} of {total}"
    bbox2 = draw.textbbox((0, 0), sub, font=font_sub)
    sw = bbox2[2] - bbox2[0]
    draw.text(((W - sw) / 2, H / 2 + 40), sub, font=font_sub, fill=(120, 130, 120))

    arr = np.array(img)[:, :, ::-1].copy()  # RGB -> BGR for cv2
    return arr


def main():
    out_path = os.path.join(SCENES_DIR, "review_reel_480p.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, FPS, (W, H))

    total = len(SCENES)
    for i, (folder, title) in enumerate(SCENES, start=1):
        video_path = None
        candidate = os.path.join(SCENES_DIR, folder, "media", "videos", folder, "480p15", "preview.mp4")
        if os.path.exists(candidate):
            video_path = candidate
        if video_path is None:
            print(f"SKIP (no render found): {folder}")
            continue

        card = make_title_card(title, i, total)
        for _ in range(CARD_FRAMES):
            writer.write(card)

        cap = cv2.VideoCapture(video_path)
        n = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame.shape[1] != W or frame.shape[0] != H:
                frame = cv2.resize(frame, (W, H))
            writer.write(frame)
            n += 1
        cap.release()
        print(f"{i:2d}/{total}  {folder}: {n} frames")

    writer.release()
    print("wrote", out_path)


if __name__ == "__main__":
    main()
