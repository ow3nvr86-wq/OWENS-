#!/usr/bin/env python3
"""Rainy Night: a sleep video generator.

Builds a seamless loop (picture and sound) entirely in code, then stretches
it to any length without re-rendering:

    python3 rainy_night.py loop            # render the 60 s seamless loop
    python3 rainy_night.py extend 2m       # loop it out to 2 minutes
    python3 rainy_night.py extend 8h       # ...or a full night

Everything that moves or changes repeats a whole number of times per loop,
so the last frame flows straight into the first and the audio has no click.
"""
import argparse
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")

W, H, FPS = 1920, 1080, 24
LOOP_S = 60
FRAMES = LOOP_S * FPS
SR = 48000
SEED = 7


# ----------------------------------------------------------------- audio --

def _shaped_noise(rng, n, gain_fn):
    """Periodic noise: random phases, magnitude set by gain_fn(freqs)."""
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    g = gain_fn(np.maximum(f, 1e-3))
    g[0] = 0
    x = np.fft.irfft(spec * g, n)
    return x / (np.std(x) + 1e-12)


def _band(f, lo, hi, order=2):
    hp = (f / lo) ** order / (1 + (f / lo) ** order)
    lp = 1 / (1 + (f / hi) ** order)
    return hp * lp


def _loop_lfo(t, cycles, phase=0.0):
    return np.sin(2 * np.pi * cycles * t / LOOP_S + phase)


def _circ_conv(x, kernel):
    k = np.zeros_like(x)
    k[: len(kernel)] = kernel
    return np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(k), len(x))


def make_audio(path):
    rng = np.random.default_rng(SEED)
    n = LOOP_S * SR
    t = np.arange(n) / SR
    out = np.zeros((2, n))

    # Low rumble: brown noise, mostly shared between ears so it feels centred.
    rumble_gain = lambda f: (1 / f) * _band(f, 25, 220, 3)
    shared = _shaped_noise(rng, n, rumble_gain)
    for c in range(2):
        own = _shaped_noise(rng, n, rumble_gain)
        out[c] += 0.32 * (0.8 * shared + 0.45 * own)

    # Rain body: pink noise, wide and soft, breathing slowly in intensity.
    swell = 1 + 0.14 * _loop_lfo(t, 2) + 0.07 * _loop_lfo(t, 5, 1.3)
    body_gain = lambda f: (1 / np.sqrt(f)) * _band(f, 350, 5500, 2)
    for c in range(2):
        body = _shaped_noise(rng, n, body_gain)
        out[c] += 0.30 * body * (swell + 0.04 * _loop_lfo(t, 3, c * 2.1))

    # Fine hiss of distant rain, rolled off early so it never sounds harsh.
    hiss_gain = lambda f: _band(f, 2500, 7000, 2)
    for c in range(2):
        out[c] += 0.06 * _shaped_noise(rng, n, hiss_gain) * swell

    # Droplets: three families of tiny decaying noise bursts, randomly panned.
    f = np.fft.rfftfreq(n, 1 / SR)
    for rate, tau_ms, lo, hi, level in [
        (14, 3.0, 1800, 5200, 0.40),   # close, bright ticks
        (32, 6.0, 700, 2600, 0.22),    # soft patter on leaves
        (5, 14.0, 250, 1100, 0.30),    # heavy drops off the eaves
    ]:
        klen = int(SR * tau_ms * 6 / 1000)
        kt = np.arange(klen) / SR
        kernel = rng.standard_normal(klen) * np.exp(-kt / (tau_ms / 1000))
        kernel *= np.minimum(1, kt / 0.0008)            # soften the attack
        count = rate * LOOP_S
        pos = rng.integers(0, n, count)
        amp = rng.pareto(3.0, count) * 0.5 + 0.2
        amp = np.minimum(amp, 2.5)
        pan = rng.uniform(0.1, 0.9, count)
        bandg = _band(f, lo, hi, 2)
        for c in range(2):
            imp = np.zeros(n)
            w = np.sqrt(pan if c else 1 - pan)
            np.add.at(imp, pos, amp * w)
            d = _circ_conv(imp, kernel)
            d = np.fft.irfft(np.fft.rfft(d) * bandg, n)
            out[c] += level * d / (np.std(d) + 1e-12) * swell

    # Warm overall tilt: gently darken everything above ~6 kHz.
    tilt = 1 / np.sqrt(1 + (f / 6000) ** 2)
    for c in range(2):
        out[c] = np.fft.irfft(np.fft.rfft(out[c]) * tilt, n)

    # Quiet, steady level: about -24 dBFS RMS, peaks held under -3 dBFS.
    rms = np.sqrt(np.mean(out ** 2))
    out *= 10 ** (-24 / 20) / rms
    peak = np.max(np.abs(out))
    if peak > 10 ** (-3 / 20):
        out *= 10 ** (-3 / 20) / peak

    pcm = (out.T * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


# ----------------------------------------------------------------- video --

def _periodic_field(rng, h, w, cutoff, power=2.2):
    """Tileable smooth noise in [0,1]; cutoff in cycles across the field."""
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.rfftfreq(w)[None, :] * w
    r = np.sqrt((fy * w / h) ** 2 + fx ** 2) + 1e-6
    g = r ** (-power) * np.exp(-((r / cutoff) ** 2))
    g[0, 0] = 0
    spec = np.fft.rfft2(rng.standard_normal((h, w))) * g
    x = np.fft.irfft2(spec, (h, w))
    x = (x - x.min()) / (x.max() - x.min())
    return x.astype(np.float32)


def _smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def _rain_layer(rng, count, length, width, alpha):
    """Tileable sheet of falling streaks, W x H, wraps vertically."""
    sheet = np.zeros((H, W), np.float32)
    xs = rng.integers(0, W, count)
    ys = rng.integers(0, H, count)
    ln = rng.integers(length[0], length[1], count)
    a = rng.uniform(alpha * 0.4, alpha, count).astype(np.float32)
    for x, y, L, al in zip(xs, ys, ln, a):
        prof = np.linspace(0, 1, L, dtype=np.float32) ** 1.5 * al
        rows = (y + np.arange(L)) % H
        for dx in range(width):
            col = (x + dx) % W
            fall = 1.0 if dx == 0 else 0.35
            sheet[rows, col] = np.maximum(sheet[rows, col], prof * fall)
    return sheet


def build_scene():
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = yy / H

    # Sky: deep navy at the top, sinking to near black.
    top = np.array([16, 22, 40], np.float32)
    bot = np.array([5, 7, 13], np.float32)
    bg = top[None, None] * (1 - v[..., None]) + bot[None, None] * v[..., None]

    # Moon, low and soft, with a wide halo.
    mx, my = W * 0.72, H * 0.26
    d = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)
    halo = np.exp(-((d / 340) ** 2)) * 0.55 + np.exp(-((d / 120) ** 2)) * 0.6
    disc = _smoothstep(60, 50, d)
    moon_col = np.array([128, 140, 165], np.float32)
    bg += halo[..., None] * np.array([26, 32, 48], np.float32)
    bg = bg * (1 - disc[..., None] * 0.85) + disc[..., None] * moon_col * 0.85

    # Fog: two tileable layers drifting left at different speeds (parallax).
    # Widths are chosen so each moves exactly a whole tile in one loop.
    fog_far = _periodic_field(rng, H, 1440, 5)      # 1 px/frame
    fog_near = _periodic_field(rng, H, 2880, 6)     # 2 px/frame
    band_far = _smoothstep(0.05, 0.35, v) * _smoothstep(0.85, 0.55, v)
    band_near = _smoothstep(0.25, 0.6, v) * _smoothstep(1.0, 0.75, v)

    # Hills: two dark silhouettes along the bottom.
    def ridge(base, amp, cyc, seed):
        r = np.random.default_rng(seed)
        x = np.arange(W) / W
        y = np.zeros(W)
        for k, c in enumerate(cyc):
            y += amp / (k + 1) * np.sin(2 * np.pi * c * x + r.uniform(0, 6.28))
        return (base + y) * H

    far_ridge = ridge(0.78, 0.035, [1.3, 3.1, 7.7], 1)
    near_ridge = ridge(0.88, 0.03, [0.9, 2.4, 6.3, 13.0], 2)
    far_mask = _smoothstep(-1.5, 1.5, yy - far_ridge[None, :])
    near_mask = _smoothstep(-1.5, 1.5, yy - near_ridge[None, :])

    rain_far = _rain_layer(rng, 1400, (18, 34), 1, 0.16)
    rain_near = _rain_layer(rng, 520, (40, 80), 2, 0.26)

    # Static dither frames to keep the dark gradients free of banding.
    dither = [rng.uniform(-0.7, 0.7, (H, W, 1)).astype(np.float32) for _ in range(4)]

    return dict(bg=bg, fog_far=fog_far, fog_near=fog_near,
                band_far=band_far, band_near=band_near,
                far_mask=far_mask, near_mask=near_mask,
                rain_far=rain_far, rain_near=rain_near, dither=dither)


def _tile_x(field, shift):
    """Take a W-wide window from a horizontally tileable field."""
    fw = field.shape[1]
    idx = (np.arange(W) + shift) % fw
    return field[:, idx]


def render_frame(s, i):
    fog_col = np.array([60, 70, 92], np.float32)
    far_fog = _tile_x(s["fog_far"], i * 1) ** 2.0 * s["band_far"]
    near_fog = _tile_x(s["fog_near"], i * 2) ** 2.4 * s["band_near"]

    img = s["bg"] + (0.5 * far_fog)[..., None] * fog_col
    hill_far = np.array([9, 11, 18], np.float32)
    img = img * (1 - s["far_mask"][..., None]) + s["far_mask"][..., None] * hill_far
    img += (0.6 * near_fog)[..., None] * fog_col
    hill_near = np.array([3, 4, 7], np.float32)
    img = img * (1 - s["near_mask"][..., None]) + s["near_mask"][..., None] * hill_near

    # Rain: vertical scroll. 18 and 36 px/frame cover a whole number of
    # screen heights per loop (1440*18 = 24*1080), so it wraps cleanly.
    rf = np.roll(s["rain_far"], i * 18, axis=0)
    rn = np.roll(s["rain_near"], i * 36, axis=0)
    rain_col = np.array([150, 165, 190], np.float32)
    img += (rf * 0.55 + rn)[..., None] * rain_col

    img += s["dither"][i % 4]
    return np.clip(img, 0, 255).astype(np.uint8)


def make_video(wav_path, mp4_path):
    s = build_scene()
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav_path,
           "-c:v", "libx264", "-preset", "slow", "-crf", "17",
           "-tune", "grain", "-pix_fmt", "yuv420p", "-g", str(FPS * 4),
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           mp4_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(FRAMES):
        frame = render_frame(s, i)
        if i == FRAMES // 3:
            from PIL import Image
            Image.fromarray(frame).save(os.path.join(OUT, "rainy-night-still.png"))
        p.stdin.write(frame.tobytes())
        if i % 120 == 0:
            print(f"  frame {i}/{FRAMES}", flush=True)
    p.stdin.close()
    if p.wait():
        sys.exit("ffmpeg failed")


# ------------------------------------------------------------------ main --

def parse_duration(s):
    mult = {"s": 1, "m": 60, "h": 3600}
    return float(s[:-1]) * mult[s[-1]] if s[-1] in mult else float(s)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("loop", help="render the seamless loop")
    ex = sub.add_parser("extend", help="repeat the loop out to a duration")
    ex.add_argument("duration", help="e.g. 2m, 1h, 8h")
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    wav = os.path.join(OUT, "rainy-night-loop.wav")
    loop = os.path.join(OUT, "rainy-night-loop.mp4")

    if a.cmd == "loop":
        print("audio...", flush=True)
        make_audio(wav)
        print("video...", flush=True)
        make_video(wav, loop)
        print("done:", loop)
    else:
        secs = parse_duration(a.duration)
        reps = int(np.ceil(secs / LOOP_S))
        name = os.path.join(OUT, f"rainy-night-{a.duration}.mp4")
        # Video is copied as-is; audio is re-looped from the sample-exact WAV
        # so the seam is click-free. A 10 s fade in, 30 s fade out.
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-stream_loop", str(reps - 1), "-i", loop,
               "-stream_loop", str(reps - 1), "-i", wav,
               "-map", "0:v", "-map", "1:a", "-c:v", "copy",
               "-af", f"afade=t=in:d=10,afade=t=out:st={max(secs - 30, 0)}:d=30",
               "-c:a", "aac", "-b:a", "192k", "-t", str(secs),
               "-movflags", "+faststart", name]
        subprocess.run(cmd, check=True)
        print("done:", name)


if __name__ == "__main__":
    main()
