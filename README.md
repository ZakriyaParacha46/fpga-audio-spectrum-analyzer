# FPGA Audio Spectrum Analyzer

A real-time audio spectrum analyzer built entirely from scratch in raw Verilog on a Digilent Basys3 (Xilinx Artix-7). No microcontroller, no operating system, no vendor FFT core, and debugged with zero simulator — synthesize, flash the board, and see what breaks.

**Video walkthrough:** [Why Every Sound Is Secretly a Chord](https://www.youtube.com/watch?v=MUcwDwSObPo)

This is part two of a series on building real hardware from scratch, no shortcuts.

## What it does

A sound sensor feeds an analog signal into the FPGA's XADC, which gets sampled, filtered, transformed into a 256-bin frequency spectrum, and drawn live on a VGA display — bar by bar, sixty times a second. Point it at a real sound and you see the harmonics: a fundamental frequency plus its weaker copies, which is why a violin and a flute playing the same note still look (and sound) nothing alike on the display.

## Why it's not a vendor FFT core

The project started with Xilinx's FFT LogiCORE IP, but its runtime scaling schedule required guessing at undocumented internal architecture with no reliable way to verify against the datasheet. After chasing "random, scattered" output that turned out to trace back to an all-zero scaling schedule causing internal overflow, the IP was dropped in favor of a fully self-written, fully verifiable core — a hand-written 128-point radix-2 FFT, followed by a redesign to 256 Goertzel resonators (a two-term recurrence swept one bin at a time) rather than a butterfly network. Slower isn't the point; a plain nested loop is something you can trust on the very first reflash, with no simulator to catch a mistake before it hits real silicon.

## Signal path

```
sensor → voltage divider → XADC → raw 12-bit samples
                                        │
                        ┌───────────────┼───────────────┐
                        │                               │
                  waveform view                   lowpass filter
                  (untouched)                            │
                                                   highpass filter
                                                          │
                                              ┌───────────┴───────────┐
                                        waveform view          Goertzel bank (×256)
                                                                       │
                                                                log compression
                                                                       │
                                                                  VGA spectrum
```

- **Voltage divider** — the sensor idles well above the XADC's 0–1V input range, so a 10kΩ/10kΩ divider steps it down before it ever reaches the FPGA.
- **XADC** — the one piece of vendor IP in the project (the actual analog-to-digital conversion happens in dedicated silicon, not fabric); everything downstream of the raw 12-bit sample is hand-written.
- **IIR lowpass** — a single-pole exponential moving average: subtract, shift, add. No multiplier, no divider circuit. Cutoff is a runtime input, adjustable live from the board's buttons.
- **Complementary highpass** — reuses the same lowpass and subtracts it from the input, since lowpass + highpass always reconstructs the original signal by definition. A third, deliberately slow tracker learns the true resting baseline rather than assuming a fixed offset.
- **Goertzel bank** — 256 resonators swept one at a time instead of an FFT butterfly network. About 2ms per full sweep at 65MHz, comfortably faster than the time it takes to collect the next batch of samples.
- **Log compression** — a cheap approximate log2 from the position of the highest set bit, no hardware log unit or lookup table, so six orders of magnitude of raw power become a readable bar height.
- **VGA driver** — 65MHz pixel clock, double-buffered so nothing mid-draw ever tears.

## Repo structure

```
FFTspectrum/
  VU.srcs/sources_1/new/   real hand-written Verilog: audio_driver, filters, VGA timing, top
  VU.srcs/sources_1/ip/    vendor IP (clock wizard, XADC wizard) — generated, not hand-written
  VU.srcs/constrs_1/       pin constraints (.xdc)
  VU.xpr                   Vivado project file
  build_log.md             running build notes — real bugs, real fixes, kept as-built
scenes/                    Manim scene source for the video's animations
scripts/publish_release.sh release/publish helper used for this project
```

## Hardware

- **Board:** Basys3 (Xilinx Artix-7, `xc7a35tcpg236-1`)
- **Sensor:** generic electret mic + amp module, analog output
- **Divider:** two 10kΩ resistors, sensor idling at 1.45V pulled down to ~0.8V measured at the ADC node

## Build honesty

`FFTspectrum/build_log.md` is the real, as-built log — including the bugs that got found and fixed along the way (7-segment display tearing, bars jittering with no smoothing, the abandoned vendor FFT core) and the open items still left for future tuning. A build log with visible rough edges is more honest than a suspiciously perfect one.

## Learning references

- [3Blue1Brown — But what is the Fourier Transform? A visual introduction](https://www.youtube.com/watch?v=spUNpyF58BY)
- [Reducible — The Fast Fourier Transform (FFT): Most Ingenious Algorithm Ever?](https://www.youtube.com/watch?v=h7apO7q16V0)
