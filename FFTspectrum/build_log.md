# FFT-on-FPGA (Basys3) — Build Log

Running notes for the project: audio → ADC → 16-LED VU meter (Phase 1) →
VGA/7-seg display of FFT bars (Phase 2) → real-time FFT (Phase 3).
Kept up to date as we build, so it doubles as raw material for the video
and as a reference for what was actually decided and why.

---

## Hardware

**Board:** Basys3 (Xilinx Artix-7, part `xc7a35tcpg236-1`)
**Sensor:** generic Arduino-style sound sensor module (electret mic + amp),
5V-capable, analog output pin.

### Why an external divider is needed
The Basys3's XADC (built into the Artix-7) only accepts **0–1V** on its
analog input pins (unipolar mode). The sensor's analog output can swing
well above that, so it must be attenuated before reaching the FPGA.

### Measured signal levels
- Via ESP8266 analog read (10-bit, 0-1023 over 0-3.3V), early check: quiet
  reading ~40-50 → ~0.13-0.16V.
- Via multimeter directly at sensor AO (5V-powered): quiet baseline
  ~1.2V.
- Via the FPGA's own ADC + 7-seg readout (final working setup, see
  Divider section): silence fluctuates ~400-500 counts; loud peak
  measured at `0xE14` = 3604 counts (~0.88V post-divider).

### Divider used
**Went through two versions:**
1. First tried 10kΩ (sensor→node) / 1kΩ (node→GND), ratio 1/11 - sized
   for a worst-case 5V swing. In practice this over-attenuated the
   sensor's actual (much smaller) real-world swing, leaving too little
   ADC range to work with - barely any LED/display movement.
2. **Final, working setup: 10kΩ / 10kΩ (equal divider, ratio 1/2).**
   Gentler attenuation, uses much more of the ADC's usable range given
   the sensor's real output levels. Confirmed working well.

### XADC overvoltage safety (why this doesn't risk damage)
Per Xilinx UG480: the XADC analog input pins tolerate up to **100mV
above VCCADC (1.8V), i.e. up to ~1.9V**, without permanent damage -
*provided the source current is limited by a series resistor of at
least 100Ω*. Our divider resistors (10k�q) are far above that minimum,
so this is automatically satisfied. Below 1.9V: safe. Above 1.9V: real
risk. Inputs above the normal 0-1V *operating* range just clip the ADC
reading at max code (4095) - no damage there either, as long as under
~1.9V. Our measured peak (~0.88V) isn't even hitting the 1V operating
limit, so there's comfortable margin.

### Wiring
- Sensor VCC → Basys3 5V pin
- Sensor GND → Basys3 GND
- Sensor AO → divider (10k to signal, 10k to GND) → divider output node
- Divider output → **JXADC pin 1** (`XA1_P`, FPGA pin J3, port `vauxp6`)
- **JXADC pin 7** (`XA1_N`, FPGA pin K3, port `vauxn6`) → GND directly

### Why there are two pins (P/N) per analog channel
The XADC is a **differential** ADC — every channel measures a voltage
*difference* between a P and N pin, not a single voltage vs. a fixed
ground (this rejects common-mode noise). For a single-ended sensor like
ours, tie the N pin to GND — the XADC then reads P − 0 = P directly. This
is a normal, supported way to use it (sometimes called pseudo-differential
or single-ended-via-ground).

---

## Vivado / XADC IP setup

Using the **XADC Wizard** IP (search "XADC" in IP Catalog), component
name `xadc_wiz_0`, configured as:
- **Basic tab:** Single Channel, Continuous Mode
- **ADC Setup tab:** Sequencer Mode = Off, Channel Averaging = None
- **Single Channel tab:** Channel = VAUX6 (VAUXP6/VAUXN6 — matches
  JXADC pin 1/7), **Bipolar checkbox left unchecked** (there's no
  separate "Unipolar" dropdown — unipolar is just the unchecked/default
  state of that checkbox)
- **Alarms tab:** everything disabled/unchecked
- Output products generated with strategy = **Global** (simpler than
  Out-of-Context for a project this size; OOC synthesizes the IP
  separately, mainly useful for bigger projects / reuse — not needed here)

### Actual generated port list (from the .veo instantiation template)
This differs slightly from generic examples found online — this is the
one that's actually correct for our config:
```
.di_in(di_in),          // input  [15:0]
.daddr_in(daddr_in),    // input  [6:0]
.den_in(den_in),        // input
.dwe_in(dwe_in),        // input
.drdy_out(drdy_out),    // output
.do_out(do_out),        // output [15:0]
.dclk_in(dclk_in),      // input
.reset_in(reset_in),    // input
.vp_in(vp_in),          // input  - dedicated Vp/Vn pins, required even though unused - tie to 0
.vn_in(vn_in),          // input  - same
.vauxp6(vauxp6),        // input
.vauxn6(vauxn6),        // input
.channel_out(channel_out), // output [4:0]
.eoc_out(eoc_out),      // output
.alarm_out(alarm_out),  // output
.eos_out(eos_out),      // output - end-of-sequence, unused in single-channel mode
.busy_out(busy_out)     // output
```
Lesson learned: `vp_in`/`vn_in` and `eos_out` are easy to miss if copying
from an older tutorial's port list — always check the actual generated
`.veo` file for your specific Vivado version/config rather than trusting
a remembered list.

---

## Code structure

Kept modular from the start so later phases (VGA driver, seven-seg
driver, FFT core) can slot in cleanly:

- **`top.v`** — top-level module (was originally named `main`, renamed to
  `top`). Instantiates `audio_driver`, `seven_seg_driver`, and
  `envelope_follower`, and maps the envelope to a 16-LED bar (linear
  thresholds, tunable via `LED_STEP` parameter). This is where future
  phases' modules will also be instantiated and wired together.
- **`audio_driver.v`** — wraps the `xadc_wiz_0` IP only. Exposes a clean
  `level` (12-bit, 0–4095, raw instantaneous sample) and `level_valid`
  pulse. Knows nothing about LEDs/VGA/FFT — just "here's the current
  sample."
- **`seven_seg_driver.v`** — multiplexes the 4-digit display to show a
  16-bit value in hex. Added so the actual ADC/envelope reading could be
  watched live instead of guessing from LED behavior alone.
- **`envelope_follower.v`** — converts the raw, audio-rate-oscillating
  `level` samples into a stable loudness reading. See "Envelope follower"
  section below for why this was needed.

### Also found and fixed: 7-seg display tearing
Symptom: display showed nonsense values (e.g. `2A01`) that couldn't be
real, since `envelope` is only 12 bits (max `0xFFF`).
Root cause: `seven_seg_driver` was reading the *live* value on every one
of its 4 multiplexed digit slots. Since the underlying value could change
mid-scan (fast attacks, decay steps), each digit ended up showing a
nibble from a different instant - a mismatched composite, not one real
reading.
Fix: latch the value once per full 4-digit scan (`value_latched`,
captured when `refresh_counter == 0`) and display that frozen snapshot
for the whole scan instead of the live-changing signal.

### Final calibration (working)
- Silence reading on the hex display: `0x400`-`0x500` = DECIMAL
  1024-1280 (initially misread as decimal 400-500 - corrected here).
  `BASELINE = 1280` (upper end, so ambient noise floor doesn't trigger
  false LED movement)
- Peak (loud sound) measured: `0xE14` = 3604 decimal
- `LED_STEP = (3604 - 1280) / 16 ≈ 145`
- `envelope_follower` decay: `DECAY_INTERVAL = 200000` (100MHz clk → one
  decay step every 2ms), `DECAY_STEP = 1` - gives a visible fall over a
  few hundred ms to ~1s after a loud sound, similar to real VU meter
  ballistics. Adjust if the meter falls too fast/slow.

### LED bar-graph mapping
`LED_STEP` parameter = counts-per-LED, applied to the envelope value
(post-baseline-subtraction). Final calibrated value: `145` (see above).

---

## Phase 1 status: working
Audio → divider → XADC → envelope follower → 16-LED bar + live hex
display on the 7-segment, all calibrated against real measured values.

---

## Phase 2: VGA bar display (switch-selected count)

### New modules
- **`vga_timing.v`** — standard 640x480 @ 60Hz sync generator. 25MHz
  pixel clock derived from the 100MHz system clock via a free-running
  2-bit divider (`pixel_tick` pulses once every 4 clk cycles). Outputs
  hsync/vsync (active-low, per this timing standard), pixel_x/pixel_y,
  video_on. Pure timing only, no drawing logic.
- **`bar_display.v`** — draws `num_bars` vertical bars evenly across the
  640px width, heights from a packed `bar_heights_flat` bus. Grows bars
  up from the bottom of the screen.

### Design choice: no divider for bar widths
Splitting 640px evenly among a *variable* N (from switches) would
normally need a division (`640/N`) every pixel or every line - expensive
in hardware and a timing-closure risk at pixel rate. Used a running-
accumulator ("DDA"/Bresenham-style) technique instead: add `num_bars` to
an accumulator each column, and whenever it rolls past 640, bump the bar
index and subtract 640 back off. This distributes N items over 640
columns with widths differing by at most 1px, using only an adder and a
comparator - no divider needed.

### Design choice: flattened array instead of a Verilog array port
Plain Verilog-2001 (unlike SystemVerilog) doesn't support unpacked
arrays as module ports. `bar_heights_flat` is `MAX_BARS * HEIGHT_BITS`
bits packed into one bus; `bar_display.v` pulls out the height for the
current bar using an indexed part-select (`bar_heights_flat[bar_index *
HEIGHT_BITS +: HEIGHT_BITS]`), which variable-indexes cleanly into a flat
bus without needing an actual array port.

### Switches -> bar count
`sw[7:0]` used directly as an 8-bit count (not thermometer-coded),
clamped: 0 -> 1 (avoid a "zero bars" edge case), values above `MAX_BARS`
(64) clamp down to 64. 64 was chosen as a practical cap so bars don't
get too thin to see clearly on a 640px-wide screen (~10px/bar at 64).

### Bar heights - placeholder until the FFT (Phase 3)
All bars currently share ONE height, driven by the same audio envelope
value from Phase 1 (`envelope >> 3`, clamped to `MAX_BAR_HEIGHT` = 400px,
avoiding a real divider the same way). This is intentionally a
placeholder: Phase 3's FFT core will write MAX_BARS independent per-bin
values into the same `bar_heights_flat` bus instead of one value
replicated everywhere - `bar_display.v` itself doesn't need to change
for that, only what feeds `bar_heights_flat` in `top.v`.

### VGA pinout (Basys3, confirmed against Digilent's master XDC)
4 bits per color channel: `vgaRed[3:0]`, `vgaGreen[3:0]`, `vgaBlue[3:0]`,
plus `Hsync`/`Vsync`. Switches `sw[0..7]` on pins
V17/V16/W16/W17/W15/V15/W14/W13.

### Debugging notes from this phase
- Hit a "duplicate module bar_display" HDL error - turned out `top.v` had
  accidentally picked up a full copy of the bar_display module body
  pasted into it, in addition to the real one in bar_display.v. Lesson:
  when an "unplaced ports"/duplicate-module error looks bizarre, check
  for accidental copy-paste duplication before assuming a deeper bug.
- Separately, Vivado's active top-level got set to `audio_driver`
  instead of `top` at some point (diagnosed from the IO placement error
  listing `level[0..11]`/`level_valid` as unplaced ports - those are
  audio_driver's ports, not top's). Fixed via Sources panel -> right-click
  `top` -> Set as Top. Also had a stray second constraints file
  (`const.xdc`) with a stale `led[0]` reference - consolidated down to
  one XDC file (`audio_vu_meter_additions.xdc`).

---

## Phase 3: real FFT-per-bar spectrum

### Why bars all moved together before
Phase 2's bars were a placeholder - every bar mirrored the same single
audio envelope value, so more bars just meant more copies of the same
number, not real per-frequency data.

### Pipeline
`audio_driver.level` (fast/raw) -> **`audio_sampler.v`** (decimates to a
fixed 48kHz, centers around zero) -> **`fft_feeder.v`** (buffers 1024
samples, bursts them into the FFT core's AXI-Stream input) ->
**`xfft_0`** (Xilinx FFT LogiCORE IP, generated via IP Catalog like the
XADC - NOT hand-written; 1024-point, Pipelined/Streaming I/O, Natural
Order output) -> **`fft_bin_grouper.v`** (magnitude + groups bins into
`num_bars` zones, peak per zone) -> `bar_heights_flat` -> `bar_display.v`
(unchanged from Phase 2).

### Design choices and honest tradeoffs
- **Sample rate 48kHz**: satisfies Nyquist for 20kHz content (needs
  >40kHz).
- **1024-point FFT**: bin spacing = 48000/1024 ~= 46.9Hz. The practical
  low end is therefore **~47Hz, not a literal 20Hz** - bin 1 is treated
  as the "20Hz" edge. True 20Hz resolution would need a much longer FFT
  (far more BRAM/DSPs than this project needs) - documented here so it's
  not a surprise later.
- **Magnitude approximation**: alpha-max-plus-beta-min
  (`max(|re|,|im|) + 0.5*min(|re|,|im|)`) instead of true
  `sqrt(re^2+im^2)` - avoids needing a square-root circuit, close enough
  for a visual meter.
- **Pseudo-log height mapping**: bar height comes from the position of
  the highest set bit in the magnitude (a cheap priority-encoder-style
  operation), not a real log2/dB calculation - gives log-like dynamic
  range compression (important, since audio spectra span huge ranges)
  without a divider or logarithm circuit.
- **Bin grouping**: same division-free Bresenham-style accumulator
  technique as the VGA pixel/bar distribution in Phase 2 - reused here to
  group `USABLE_BINS` (427) raw FFT bins into `num_bars` buckets without
  a divider. More bars = fewer bins per bucket = finer frequency
  resolution per bar, as intended.
- **Single-buffered feeder (not ping-pong)**: `fft_feeder.v` collects a
  full 1024-sample frame (~21ms at 48kHz), THEN bursts it out - new
  samples aren't collected during the (much shorter) burst-out window.
  A small gap, not eliminated. Noted as a future improvement (see Open
  items).
- **Double-buffered grouper output**: `fft_bin_grouper.v` writes into a
  private `build_buffer` as bins stream in, and only copies the complete
  result into the public `bar_heights_flat` in one shot per frame -
  applying the same tearing lesson learned from the 7-seg display bug
  in Phase 1.
- **num_bars is read live, not latched per-frame**: if switches change
  mid-frame, that frame's bin grouping could be inconsistent. Rare/brief
  in practice (switches change slowly), but a known simplification.

### Bug found and fixed: bars jittering randomly with no audio
Symptom: with the FFT running, bars moved up/down apparently randomly
even in silence - "too much noise and randomness."

Root causes (two, both fixed):
1. **No smoothing between FFT frames.** Each ~21ms frame's raw peak-per-
   bucket magnitude overwrote the display outright, so ordinary noise
   floor (mic self-noise, ADC quantization noise, room noise) showed up
   directly as frame-to-frame jitter. Same underlying problem
   `envelope_follower` solved for the single-value loudness meter in
   Phase 1 - just hadn't been applied to the FFT bars yet.
2. **The pseudo-log height mapping (highest-set-bit position) is
   oversensitive near zero** - a tiny noise-level magnitude change (e.g.
   15->16) flips the bit position entirely, causing a large visible
   height jump from an inaudible amount of noise.

Fix:
- **`bar_smoother.v`** (new module) - applies the same fast-attack/slow-
  decay ballistics as `envelope_follower`, independently to all
  `MAX_BARS` heights, updated once per completed FFT frame
  (`frame_ready` pulse from the grouper). Sits between
  `fft_bin_grouper` and `bar_display` in `top.v`.
- **`NOISE_FLOOR` parameter added to `fft_bin_grouper.v`** (default
  `100`) - magnitudes below this are clamped to zero before height
  mapping, so ambient noise reads as flat bars instead of registering
  at all. TUNE ON THE BENCH like `BASELINE`/`LED_STEP` were: raise if
  bars still wiggle with no sound, lower if quiet sounds don't register.

## Open items
- [ ] Watch real usage over time - re-tune `BASELINE`/`LED_STEP` if the
      ambient noise floor drifts (e.g. different room, time of day)
- [ ] Consider a log/dB-scaled LED mapping instead of linear, since ear/
      mic response is closer to logarithmic
- [ ] Verify xfft_0's actual generated port names/widths against
      fft_feeder.v and fft_bin_grouper.v (same process as the XADC IP)
- [ ] Double-buffer fft_feeder.v to eliminate the small sample-collection
      gap during burst-out
- [ ] Latch num_bars at frame start instead of reading it live, to avoid
      inconsistent grouping if switches change mid-frame
- [ ] Consider longer FFT (e.g. 2048/4096) for finer low-frequency
      resolution if 47Hz bins feel too coarse once seen on screen
- [ ] Tune bar_smoother's DECAY_STEP (currently 2) and
      fft_bin_grouper's NOISE_FLOOR (currently 100) once running -
      first real-world values to calibrate in Phase 3


---

## Phase 3 REPLANNED: dropped the Xilinx FFT IP, hand-wrote our own

### Why
The Xilinx FFT LogiCORE IP required a runtime scaling schedule sent
through `s_axis_config_tdata` (confirmed: no fixed/compile-time
schedule option exists anywhere in the IP wizard GUI for this core).
Getting that exact bit-packing right required guessing at undocumented
internal architecture details (radix, stage count) with no reliable
way to verify against the datasheet's exact bit diagram. After several
rounds of debugging genuinely mysterious "random, scattered" output
that turned out to trace back to an all-zero (no-op) scaling schedule
causing internal overflow, decided to drop the black-box IP entirely
in favor of a fully self-written, fully verifiable FFT core.

### New design: fft128.v
Hand-written 128-point radix-2 Decimation-In-Time FFT, single reused
butterfly unit stepping sequentially through 7 stages x 64 butterflies
= 448 operations per frame (not pipelined/streaming - unnecessary,
since 448 cycles at 100MHz takes <5us versus the ~2.67ms it takes to
collect 128 samples at 48kHz - >500x margin).

**Scaling (the exact thing that broke the IP integration) is now
fully under our control and provably correct**: every butterfly output
is divided by 2 before storing. Since |twiddle|=1 exactly, a
butterfly's output is bounded by |A|+|B| <= 2*max(|A|,|B|) - dividing
by 2 every stage exactly compensates that worst case, so values can
never overflow, by construction rather than guesswork.

Twiddle factors (64 cos/sin values, Q15 fixed point) were computed
numerically (Python) and hardcoded directly into the module - no
external .mem file dependency, fully self-contained.

Addressing (which two memory slots each butterfly touches, and which
twiddle factor to use) is computed via bit shifts keyed on the current
stage number - avoids needing a runtime divider or a bulky per-stage
case statement.

### Consequences accepted for this simplification
- **Fixed 128 bars**, not switch-selectable anymore. `sw[7:0]` is
  unused now (constraint left in XDC harmlessly, not removed).
- **Frequency resolution drops**: 48000/128 = 375Hz/bin (was ~47Hz
  with the 1024-point IP-based version). Bin 1 is ~375Hz, not 20Hz.
- **Bins 65-127 mirror bins 1-63** (standard property of a real-valued
  input's FFT) - displayed as-is, not hidden, so the mirroring is
  visible on screen rather than a hidden surprise.
- `bar_display.v` got simpler too: since bar count is now a fixed
  constant (128) rather than a runtime switch value, bar width is a
  **constant** division (640/128=5, synthesizes efficiently as plain
  `/`) instead of needing the Bresenham-style runtime accumulator the
  variable-bar-count version required.

### Removed
`fft_feeder.v`, `fft_bin_grouper.v`, and the `xfft_0` IP - all
superseded by `fft128.v`.

### Kept unchanged
`audio_driver.v`, `baseline_tracker.v`, `envelope_follower.v`,
`seven_seg_driver.v`, `vga_timing.v`, `test_tone_gen.v` (now more
important than before - verifying our own hand-written FFT against a
known signal matters even more with no IP vendor to trust).

## Open items
- [ ] Test with btnU held - confirm fft128 shows a concentrated peak
      near the ~1kHz bar (bin ~3) plus odd harmonics, not scattered
      noise
- [ ] Once confirmed working, test with real mic audio
- [ ] Re-tune NOISE_FLOOR/DECAY_STEP for the new 128-bar, 375Hz/bin
      setup if needed
- [ ] Watch real usage over time - re-tune BASELINE_SEED/LED_STEP if
      ambient noise floor drifts

---

## Learning references (for the video / understanding the FFT work)

**Why the test tone shows energy at odd harmonics (1kHz, 3kHz, 5kHz...
not 2kHz, 4kHz):** a square wave has half-wave symmetry (second half
of each cycle is an upside-down copy of the first) - this symmetry
mathematically cancels all even harmonics in its Fourier series,
leaving only odd ones, each 1/n the amplitude of the fundamental. A
pure sine wave by contrast has no harmonics at all - one clean spike.

**Videos, in this order:**
1. 3Blue1Brown - "But what is the Fourier Transform? A visual
   introduction" - https://www.youtube.com/watch?v=spUNpyF58BY
   Builds intuition for what a Fourier transform actually does.
2. Reducible - "The Fast Fourier Transform (FFT): Most Ingenious
   Algorithm Ever?" - https://www.youtube.com/watch?v=h7apO7q16V0
   Explains the actual algorithm (Cooley-Tukey divide-and-conquer,
   butterflies, bit-reversal) - directly matches what fft128.v does.
