#!/usr/bin/env bash
# Run this once the video is finished and uploaded.
#
# Usage: scripts/publish_release.sh <youtube_url> [github_repo_url]
#
# 1. Writes a PR/ folder at the project root:
#      PR/PR.md              - title + full description + LinkedIn post draft
#      PR/artifacts.md        - links to every Claude Artifact made for this
#                                project (thumbnails etc), plus the video/repo links
#      PR/website_prompt.md   - a ready-to-paste prompt for a Claude Code session
#                                running in your website's repo, to add this
#                                project to the portfolio/projects page
# 2. Stages and commits the source code (Manim scenes + Verilog project), never
#    the huge generated media/audio/footage/build directories (see .gitignore).
# 3. Asks for confirmation before pushing anything to GitHub - never pushes
#    silently.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

YOUTUBE_URL="${1:-}"
GITHUB_URL="${2:-}"

if [ -z "$YOUTUBE_URL" ]; then
  echo "Usage: $0 <youtube_url> [github_repo_url]"
  exit 1
fi

mkdir -p "$ROOT/PR"

# ---------------------------------------------------------------------------
# 1a. PR/PR.md - title, description, LinkedIn post
# ---------------------------------------------------------------------------
cat > "$ROOT/PR/PR.md" <<EOF
# Why Every Sound Is Secretly a Chord

## Video

$YOUTUBE_URL

## Description

A real audio spectrum analyzer, built entirely from scratch in raw Verilog on a
Digilent Basys3 FPGA. No microcontroller, no operating system, no vendor FFT
core - and debugged with zero simulator: just synthesize, flash the board, and
see what breaks.

This video covers what a Fourier transform actually is, why almost nobody
builds one this way, and why that was still the right call - from the sensor
hack that exposed an analog signal that "shouldn't" exist, through two
hand-built filters, to why this project uses 256 Goertzel resonators instead
of a classic FFT butterfly network.

TIMESTAMPS
0:00 Intro & Hook
0:37 What Is Audio?
1:09 Sampling & the ADC
1:46 The Nyquist Theorem
2:29 The Hack (Finding a Pin That "Doesn't Exist")
3:21 The Voltage Divider
4:15 Signal Path Overview
4:48 What Is a Filter?
5:15 Building an IIR Lowpass From Scratch
5:52 The Complementary Highpass
6:43 What Is a Fourier Transform?
7:26 Harmonics (Real Hardware Demo)
8:40 The DFT, the Math
9:22 What Is the FFT?
10:04 Why This Board Uses Goertzel Instead
10:43 Compressing the Spectrum (Log Scale)
11:24 Drawing It on VGA
12:05 Live Demo
12:28 Credits
12:40 Closing Thoughts

Full source (filters, Goertzel bank, VGA driver, all of it) on GitHub:
${GITHUB_URL:-[link]}

This is part two of a series on building real hardware from scratch, no
shortcuts. Part one, a neural network running on the same class of FPGA:
[link]

#FPGA #Verilog #DigitalSignalProcessing #FourierTransform #HardwareHacking
#EmbeddedSystems #DSP #Basys3

## LinkedIn Post

Just shipped part two of my "build real hardware from scratch" series: a
256-bin audio spectrum analyzer running entirely in raw Verilog on an FPGA.

No microcontroller. No vendor FFT core. No simulator in the debugging loop -
just synthesize, flash the board, and see what breaks.

The short version: every sound you've ever heard is secretly a chord - a
fundamental frequency plus weaker copies of itself stacked on top. This
project pulls that stack apart in real time, on real hardware, and shows
exactly why a violin and a flute playing the same note still sound nothing
alike.

Full build log, including the bugs I left in on purpose:
$YOUTUBE_URL

#FPGA #Verilog #EmbeddedSystems #DSP #BuildInPublic
EOF

echo "Wrote $ROOT/PR/PR.md"

# ---------------------------------------------------------------------------
# 1b. PR/artifacts.md - every Claude Artifact + link made for this project
# ---------------------------------------------------------------------------
cat > "$ROOT/PR/artifacts.md" <<EOF
# Project artifacts - Why Every Sound Is Secretly a Chord

- Thumbnail concepts (Claude Artifact): https://claude.ai/artifact/S4Ud7gBKerFi6F1yRKLNrk
- YouTube video: $YOUTUBE_URL
- GitHub source: ${GITHUB_URL:-[link once pushed]}

Add any other design/planning artifacts made for this project to this list as
they're created, so they're all in one place when it's time to update the
website or reference the project later.
EOF

echo "Wrote $ROOT/PR/artifacts.md"

# ---------------------------------------------------------------------------
# 1c. PR/website_prompt.md - paste into a Claude Code session in the website repo
# ---------------------------------------------------------------------------
cat > "$ROOT/PR/website_prompt.md" <<EOF
Add a new project to the portfolio/projects section of this website:

Title: Why Every Sound Is Secretly a Chord
One-line summary: A 256-bin audio spectrum analyzer built entirely from
scratch in raw Verilog on a Basys3 FPGA - no CPU, no vendor FFT core, no
simulator in the debugging loop.
Video: $YOUTUBE_URL
Source code: ${GITHUB_URL:-[link once pushed]}
Thumbnail/hero image reference: https://claude.ai/artifact/S4Ud7gBKerFi6F1yRKLNrk
  (the "Full-Bleed Hero" concept - export/screenshot it if the site needs a
  static image rather than a link)
Tech/tags: FPGA, Verilog, DSP, Digital Signal Processing, Fourier Transform,
  Basys3, hardware from scratch
Series: part two, after the neural-network-on-FPGA project (link that one too
  if it's already on the site)

First look at how existing projects are structured on this site (find the
projects data file, CMS content, or component that renders the projects
list/page) and add this one following the exact same pattern - same fields,
same formatting, same image handling convention already established. Don't
invent a new structure for it.
EOF

echo "Wrote $ROOT/PR/website_prompt.md"

# ---------------------------------------------------------------------------
# 2. Stage + commit source code (scenes + Verilog project), never generated media
# ---------------------------------------------------------------------------
if [ ! -d "$ROOT/.git" ]; then
  echo "No git repo here yet. Run 'git init' and set up a remote first, then re-run this script."
  exit 1
fi

git add scenes/ FFTspectrum/VU.srcs FFTspectrum/VU.xpr FFTspectrum/build_log.md \
        .gitignore PR/ 2>/dev/null || true

echo
echo "Staged files:"
git status --short

read -r -p "Commit these? [y/N] " confirm_commit
if [[ "$confirm_commit" =~ ^[Yy]$ ]]; then
  git commit -m "Release: Why Every Sound Is Secretly a Chord (Manim scenes + Verilog source)"
else
  echo "Skipped commit. Nothing pushed."
  exit 0
fi

# ---------------------------------------------------------------------------
# 3. Push (only with explicit confirmation)
# ---------------------------------------------------------------------------
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "No 'origin' remote configured. Add one (e.g. 'gh repo create' or 'git remote add origin <url>') then push manually."
  exit 0
fi

read -r -p "Push to origin now? This makes the code public. [y/N] " confirm_push
if [[ "$confirm_push" =~ ^[Yy]$ ]]; then
  git push origin HEAD
  echo "Pushed."
else
  echo "Not pushed - run 'git push origin HEAD' yourself when ready."
fi

echo
echo "Don't forget: PR/website_prompt.md is ready to paste into a Claude Code"
echo "session running in your website's repo to add this project there too."
