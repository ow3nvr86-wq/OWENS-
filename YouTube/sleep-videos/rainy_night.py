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

    # Steady level for sleep (about -27 LUFS). The odd loud droplet is
    # rounded off by a soft limiter rather than turning everything down,
    # which also stops sharp ticks that could wake a light sleeper.
    rms = np.sqrt(np.mean(out ** 2))
    out *= 10 ** (-30 / 20) / rms
    ceil = 10 ** (-9 / 20)
    out = ceil * np.tanh(out / ceil)

    pcm = (out.T * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


# ----------------------------------------------------------------- video --
#
# Scene: a lake at night in light rain. A low moon behind drifting clouds,
# twinkling stars (and a shooting star), misty mountains, a pine shoreline and a small cabin with a
# warm window. The lake mirrors it all, with rings where the rain lands.
#
# Every moving layer repeats a whole number of times in one loop, so the
# last frame flows into the first.

HZ = int(H * 0.60)            # waterline
WH = H - HZ                   # water height in px
MOON = (W * 0.27, H * 0.27, 44)
WARM = np.array([255, 172, 92], np.float32)
MOONLIGHT = np.array([225, 230, 245], np.float32)


def _field(rng, h, w, size_px, aspect=1.0, power=1.6):
    """Tileable smooth noise in [0,1]. size_px ~ feature size; aspect>1
    stretches features horizontally."""
    ky = np.fft.fftfreq(h)[:, None]
    kx = np.fft.rfftfreq(w)[None, :] * aspect
    r = np.sqrt(ky ** 2 + kx ** 2) + 1e-9
    g = r ** (-power) * np.exp(-((r * size_px) ** 2))
    g[0, 0] = 0
    x = np.fft.irfft2(np.fft.rfft2(rng.standard_normal((h, w))) * g, (h, w))
    lo, hi = np.percentile(x, [0.5, 99.5])
    return np.clip((x - lo) / (hi - lo), 0, 1).astype(np.float32)


def _smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def _cyc(i, cycles, phase=0.0):
    """Sine with a whole number of cycles per loop, at frame i."""
    return np.sin(2 * np.pi * cycles * i / FRAMES + phase)


def _over(dst, col, a):
    """Composite flat colour col with alpha a over dst, in place."""
    dst *= 1 - a[..., None]
    dst += a[..., None] * col


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


def _ridge(base, amp, seed, rough=1.9, detail=60):
    """Natural mountain profile: 1/f noise with sharpened peaks."""
    r = np.random.default_rng(seed)
    k = np.arange(W // 2 + 1, dtype=np.float64)
    spec = (r.standard_normal(k.size) + 1j * r.standard_normal(k.size))
    spec *= np.where(k > 0, np.maximum(k, 1) ** (-rough), 0) * (k < detail)
    y = np.fft.irfft(spec, W)
    y = (y - y.min()) / (y.max() - y.min())
    y = y ** 1.6                                   # sharper peaks, wide valleys
    return (base - amp * y) * H


def _pine(mask, x0, base, h, w):
    """Draw one soft-edged pine silhouette into mask (max blend)."""
    top = base - h
    y0, y1 = max(int(top), 0), min(int(base) + 1, mask.shape[0])
    x_lo, x_hi = max(int(x0 - w), 0), min(int(x0 + w) + 1, W)
    if x_hi <= x_lo:
        return
    ys = np.arange(y0, y1, dtype=np.float32)[:, None]
    xs = np.arange(x_lo, x_hi, dtype=np.float32)[None, :]
    rel = np.clip((ys - top) / h, 0, 1)
    tiers = 5
    saw = (rel * tiers) % 1.0
    half = (w / 2) * rel * (0.55 + 0.45 * saw) + 0.6
    m = _smoothstep(half + 0.8, half - 0.8, np.abs(xs - x0))
    trunk = (np.abs(xs - x0) < max(1.0, w * 0.05)) & (rel > 0.85)
    m = np.maximum(m, trunk.astype(np.float32))
    sub = mask[y0:y1, x_lo:x_hi]
    np.maximum(sub, m, out=sub)


def _stamp_disc(mask, cx, cy, r):
    ri = int(np.ceil(r)) + 1
    y0, y1 = max(int(cy) - ri, 0), min(int(cy) + ri + 1, mask.shape[0])
    x0, x1 = max(int(cx) - ri, 0), min(int(cx) + ri + 1, mask.shape[1])
    if y1 <= y0 or x1 <= x0:
        return
    ys = np.arange(y0, y1)[:, None]
    xs = np.arange(x0, x1)[None, :]
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    m = _smoothstep(r + 0.7, r - 0.7, d).astype(np.float32)
    sub = mask[y0:y1, x0:x1]
    np.maximum(sub, m, out=sub)


def build_scene():
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = yy / H
    S = {}

    # --- sky: indigo overhead, dusky violet at the horizon -----------------
    stops = [0.0, 0.30, 0.48, 0.60]
    cols = np.array([[7, 9, 24], [14, 18, 42], [30, 34, 68], [54, 54, 88]], np.float32)
    sky = np.stack([np.interp(v[:, 0], stops, cols[:, c]) for c in range(3)], -1)
    sky = np.broadcast_to(sky[:, None, :], (H, W, 3)).copy()

    mx, my, mr = MOON
    d = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)
    halo_wide = np.exp(-((d / 460) ** 2))
    sky += np.exp(-((d / 360) ** 2))[..., None] * np.array([30, 34, 60], np.float32)
    sky += np.exp(-((d / 100) ** 2))[..., None] * np.array([60, 66, 96], np.float32) * 0.7
    disc = _smoothstep(mr + 1.2, mr - 1.2, d)
    tex = _field(rng, 128, 128, 10, power=1.2)
    tx = ((xx - mx + 64) % 128).astype(int)
    ty = ((yy - my + 64) % 128).astype(int)
    shade = 0.80 + 0.2 * tex[ty, tx] - 0.10 * np.clip((xx - mx + yy - my) / mr, -1, 1)
    sky = sky * (1 - disc[..., None]) + disc[..., None] * MOONLIGHT * 0.86 * shade[..., None]
    S["sky"] = sky[:HZ]
    S["disc"] = disc[:HZ]
    S["cloud_lit"] = (np.array([22, 25, 46], np.float32)
                      + halo_wide[:HZ, :, None] * np.array([105, 110, 135], np.float32))

    # --- clouds: long wisps drifting right, 2 px/frame over a 2880 px tile -
    S["clouds"] = _field(rng, HZ, 2880, 70, aspect=2.6)
    S["cloud_band"] = (_smoothstep(0.62, 0.30, v[:HZ, :1]) * 0.9 + 0.1).astype(np.float32)

    # --- stars: twinkle at whole-number rates per loop ----------------------
    # Most are faint pinpricks; a few hundred are brighter with a soft core,
    # and the brightest couple of dozen carry a small glow. Each has its own
    # colour, from cool blue-white to warm white.
    n = 1500
    sy = (rng.uniform(0, 1, n) ** 1.25 * HZ * 0.86).astype(int)
    sx = rng.integers(0, W, n)
    keep = np.hypot(sx - mx, sy - my) > 120
    sy, sx = sy[keep], sx[keep]
    n = sy.size
    b = rng.uniform(0, 1, n) ** 3.2
    b *= _smoothstep(HZ * 0.92, HZ * 0.55, sy)          # fade into the haze
    tint = np.where(rng.uniform(0, 1, n)[:, None] < 0.7,
                    np.array([0.82, 0.90, 1.00]), np.array([1.00, 0.93, 0.82]))
    py, px, pw, pid = [], [], [], []

    def sprite(k, rad, sigma, gain):
        o = np.arange(-rad, rad + 1)
        oy, ox = np.meshgrid(o, o, indexing="ij")
        w = np.exp(-(oy ** 2 + ox ** 2) / (2 * sigma ** 2)) * gain
        y, x = sy[k] + oy.ravel(), sx[k] + ox.ravel()
        ok = (y >= 0) & (y < HZ) & (x >= 0) & (x < W)
        py.append(y[ok]); px.append(x[ok]); pw.append(w.ravel()[ok])
        pid.append(np.full(ok.sum(), k))

    order = np.argsort(-b)
    for rank, k in enumerate(order):
        if rank < 24:
            sprite(k, 6, 2.2, 0.22)                        # glow
            sprite(k, 2, 0.75, 1.0)                        # core
        elif rank < 260:
            sprite(k, 2, 0.6, 1.0)
        else:
            sprite(k, 0, 1.0, 1.0)
    pid = np.concatenate(pid)
    S["stars"] = dict(
        y=np.concatenate(py), x=np.concatenate(px),
        w=(np.concatenate(pw)[:, None] * tint[pid]).astype(np.float32),
        id=pid, b=b.astype(np.float32),
        c=rng.integers(2, 36, n),
        depth=rng.uniform(0.15, 0.45, n),
        p=rng.uniform(0, 6.28, n))

    # One slow shooting star per loop, high on the right, away from the moon.
    S["meteor"] = dict(start=int(FRAMES * 0.58), frames=int(FPS * 1.1),
                       p0=np.array([W * 0.62, H * 0.07]),
                       p1=np.array([W * 0.80, H * 0.20]), tail=150)

    # --- silhouettes (premultiplied colour + alpha), top half only ---------
    sil_c = np.zeros((HZ, W, 3), np.float32)
    sil_a = np.zeros((HZ, W), np.float32)

    def layer(mask, col):
        nonlocal sil_c, sil_a
        sil_c = sil_c * (1 - mask[..., None]) + mask[..., None] * col
        sil_a = sil_a * (1 - mask) + mask

    Y = yy[:HZ]
    far = _ridge(0.58, 0.23, 11)
    near = _ridge(0.595, 0.085, 14, rough=1.7, detail=90)
    layer(_smoothstep(-1, 1, Y - far[None]) * 0.82, np.array([40, 44, 80], np.float32))
    layer(_smoothstep(-1, 1, Y - near[None]) * 0.92, np.array([20, 23, 44], np.float32))

    trees = np.zeros((HZ, W), np.float32)
    trng = np.random.default_rng(21)
    for x in np.arange(-20, W + 20, 9.0):
        u = x / W
        if 0.40 < u < 0.60 and trng.uniform() < 0.92:
            continue                       # open water view in the middle
        edge = max(0.0, abs(u - 0.5) - 0.1) / 0.4
        h = trng.uniform(24, 60) + 70 * edge * trng.uniform(0.4, 1.0)
        if trng.uniform() < 0.08:
            h *= 1.5
        x0 = x + trng.uniform(-4, 4)
        _pine(trees, x0, HZ + 1, h, h * trng.uniform(0.32, 0.42))
    trees[HZ - 3:HZ] = np.maximum(trees[HZ - 3:HZ], 1.0)     # dark shoreline

    # Cabin on the right bank, in front of the trees.
    cx, base = int(W * 0.70), HZ - 1
    cab = np.zeros((HZ, W), np.float32)
    cab[base - 46:base, cx:cx + 124] = 1
    for k in range(44):                                      # gable roof
        half = 72 - k * 72 / 44
        cab[base - 46 - k, int(cx + 62 - half):int(cx + 62 + half)] = 1
    cab[base - 96:base - 60, cx + 92:cx + 104] = 1           # chimney
    trees = np.maximum(trees, cab)
    layer(trees, np.array([6, 7, 14], np.float32))
    S["sil_c"], S["sil_a"] = sil_c, sil_a

    # Warm windows: flat glow plus a soft bloom, scaled each frame (flicker).
    glow = np.zeros((HZ, W, 3), np.float32)
    S["windows"] = []
    for wx in (cx + 16, cx + 82):
        wy0, wy1, wx1 = base - 34, base - 18, wx + 22
        glow[wy0:wy1, wx:wx1] = WARM * 0.92
        glow[wy0:wy1, wx + 10:wx + 12] *= 0.25               # mullion
        glow[wy0 + 7:wy0 + 9, wx:wx1] *= 0.25
        dd = np.hypot(xx[:HZ] - (wx + 11), (yy[:HZ] - (wy0 + 8)) * 1.3)
        glow += (np.exp(-((dd / 22) ** 2)) * 0.30 + np.exp(-((dd / 110) ** 2)) * 0.10)[..., None] * WARM
        S["windows"].append(wx + 11)
    S["glow"] = glow

    # Chimney smoke: a drifting plume textured by noise scrolling upward.
    sx0, sy0 = cx + 98, base - 96
    S["smoke_box"] = (sy0 - 300, sy0, sx0 - 60, sx0 + 240)
    ys = np.arange(sy0 - 300, sy0, dtype=np.float32)[:, None]
    xs = np.arange(sx0 - 60, sx0 + 240, dtype=np.float32)[None, :]
    u = (sy0 - ys) / 300
    centre = sx0 + 150 * u ** 1.6
    width = 5 + 55 * u
    S["smoke_mask"] = (np.exp(-(((xs - centre) / width) ** 2)) * (1 - u) ** 1.3
                       * _smoothstep(0, 0.06, u)).astype(np.float32)
    S["smoke_tex"] = _field(rng, 480, 300, 14)                # 1 px/frame up

    # --- water ---------------------------------------------------------------
    j = np.arange(WH, dtype=np.float32)
    depth = ((j + 0.5) / WH)[:, None]                          # 0 far .. 1 near
    S["depth"] = depth
    S["row_map"] = (depth[:, 0] ** 1.7 * (WH - 1)).astype(np.int32)
    xg = np.arange(W, dtype=np.float32)[None, :]
    S["col_map"] = ((W / 2 + (xg - W / 2) * (2.6 - 1.6 * depth)) % W).astype(np.int32)
    S["wave1"] = _field(rng, 480, W, 9, aspect=5)              # 1 px/frame
    S["wave2"] = _field(rng, 720, W, 26, aspect=4)             # 2 px/frame
    S["sparkle"] = _field(rng, 480, W, 2.5, aspect=3, power=1.0)
    S["moon_col"] = np.exp(-(((xg - mx) / (26 + 190 * depth)) ** 2)) * (1.1 - 0.5 * depth)
    S["warm_col"] = sum(np.exp(-(((xg - wx) / (3 + 26 * depth)) ** 2)) for wx in S["windows"]) \
        * np.exp(-depth * 2.2)
    S["refl_rows"] = (HZ - 1 - j).astype(np.int32)

    # Rain rings: births spread over the loop; age wraps, so it loops.
    n = 7 * LOOP_S
    S["ripples"] = dict(
        t0=rng.uniform(0, FRAMES, n),
        x=rng.uniform(0, W, n),
        d=rng.uniform(0.06, 1, n) ** 0.8)

    # Mist sitting on the shoreline, drifting left 1 px/frame.
    S["mist"] = _field(rng, 160, 1440, 40, aspect=3)
    mrows = np.arange(HZ - 80, HZ + 80, dtype=np.float32)
    S["mist_band"] = np.exp(-(((mrows - HZ + 6) / 34) ** 2))[:, None].astype(np.float32)

    # --- foreground reeds, both bottom corners -----------------------------
    reeds = np.zeros((H, W), np.float32)
    rr = np.random.default_rng(31)
    for _ in range(70):
        left = rr.uniform() < 0.6
        bx = rr.uniform(-20, 360) if left else rr.uniform(1640, W + 20)
        h = rr.uniform(70, 280)
        lean = rr.uniform(-0.5, 0.5) * h * (1 if left else -1) + (25 if left else -25)
        steps = int(h)
        for t in np.linspace(0, 1, steps):
            px = bx + lean * t ** 2
            py = H + 4 - h * t
            _stamp_disc(reeds, px, py, 2.6 * (1 - t) + 0.5)
    S["reeds"] = reeds

    S["rain_far"] = _rain_layer(rng, 1300, (16, 30), 1, 0.13)
    S["rain_near"] = _rain_layer(rng, 420, (40, 80), 2, 0.22)

    # Vignette and dither.
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2 * 0.8)
    S["vignette"] = (1 - 0.55 * _smoothstep(0.45, 1.35, r))[..., None].astype(np.float32)
    S["dither"] = [rng.uniform(-0.7, 0.7, (H, W, 1)).astype(np.float32) for _ in range(4)]
    return S


def render_frame(S, i):
    flicker = 1 + 0.05 * _cyc(i, 13) + 0.035 * _cyc(i, 29, 1.0) + 0.025 * _cyc(i, 47, 2.0)

    # --- sky -----------------------------------------------------------------
    up = S["sky"].copy()
    st = S["stars"]
    tw = st["b"] * (1 - st["depth"] + st["depth"] * np.sin(2 * np.pi * st["c"] * i / FRAMES + st["p"]))
    star = np.zeros((HZ, W, 3), np.float32)
    vals = tw[st["id"]][:, None] * st["w"]
    for ch in range(3):
        np.add.at(star[..., ch], (st["y"], st["x"]), vals[:, ch])

    m = S["meteor"]
    prog = (i - m["start"]) / m["frames"]
    if 0 <= prog <= 1:
        env = np.sin(np.pi * prog) ** 1.5
        head = m["p0"] + (m["p1"] - m["p0"]) * prog
        dirv = (m["p1"] - m["p0"]) / np.linalg.norm(m["p1"] - m["p0"])
        tl = m["tail"] * min(1.0, prog * 3)
        for u in np.linspace(0, 1, 400):
            q = head - dirv * tl * u
            yq, xq = int(q[1]), int(q[0])
            if 0 <= yq < HZ - 1 and 0 <= xq < W - 1:
                v = env * (1 - u) ** 2 * 1.1
                star[yq, xq] += v
                star[yq + 1, xq] += v * 0.35

    cl = np.roll(S["clouds"], -i * 2, axis=1)[:, :W]
    dens = _smoothstep(0.40, 0.78, cl) * S["cloud_band"]
    up += star * ((1 - dens) * 235)[..., None]
    a = dens * (0.88 - 0.35 * S["disc"])
    up *= 1 - a[..., None]
    up += a[..., None] * S["cloud_lit"]

    # --- land, cabin, window light, smoke ----------------------------------
    up *= 1 - S["sil_a"][..., None]
    up += S["sil_c"]
    up += S["glow"] * flicker

    y0, y1, x0, x1 = S["smoke_box"]
    tex = np.roll(S["smoke_tex"], -i, axis=0)[: y1 - y0]
    sm = S["smoke_mask"] * (0.25 + 1.1 * tex) * 0.28
    region = up[y0:y1, x0:x1]
    _over(region, np.array([78, 80, 96], np.float32), np.clip(sm, 0, 1))

    # --- water: rippled mirror of everything above -------------------------
    rm, cm = S["row_map"], S["col_map"]
    w1 = S["wave1"][((rm + i) % 480)[:, None], cm]
    w2 = S["wave2"][((rm + 2 * i) % 720)[:, None], cm]
    depth = S["depth"]
    amp = 1.5 + 11 * depth ** 1.3
    dx = ((w1 - 0.5) * 2 + (w2 - 0.5)) * amp
    dy = (w1 - 0.5) * (1 + 5 * depth)
    src_y = np.clip(S["refl_rows"][:, None] + dy.astype(np.int32), 0, HZ - 1)
    src_x = np.clip(np.arange(W)[None, :] + dx.astype(np.int32), 0, W - 1)
    water = up[src_y, src_x]
    shade = (0.60 - 0.22 * depth) * (0.82 + 0.40 * (w2 - 0.5) + 0.25 * (w1 - 0.5))
    water *= shade[..., None]
    water += np.array([4, 6, 13], np.float32)

    sp = S["sparkle"][((rm + i) % 480)[:, None], cm]
    glint = np.clip((sp - 0.57) * 5, 0, 1) ** 2
    water += (glint * S["moon_col"] * 120)[..., None] * MOONLIGHT / 255
    water += (glint * S["warm_col"] * 190 * flicker)[..., None] * WARM / 255

    rp = S["ripples"]
    life = 1.6 * FPS
    age = (i - rp["t0"]) % FRAMES
    ring = np.zeros((WH, W), np.float32)
    for k in np.nonzero(age < life)[0]:
        g = age[k] / life
        dpt = rp["d"][k]
        rad = (3 + 46 * g) * (0.25 + 0.9 * dpt)
        ry = rad * (0.10 + 0.22 * dpt)
        cy = dpt ** (1 / 1.7) * (WH - 1)
        cx = rp["x"][k]
        ya, yb = int(max(cy - ry - 3, 0)), int(min(cy + ry + 4, WH))
        xa, xb = int(max(cx - rad - 3, 0)), int(min(cx + rad + 4, W))
        if yb <= ya or xb <= xa:
            continue
        yy = np.arange(ya, yb, dtype=np.float32)[:, None]
        xx = np.arange(xa, xb, dtype=np.float32)[None, :]
        e = np.sqrt(((xx - cx) / rad) ** 2 + ((yy - cy) / max(ry, 0.5)) ** 2)
        val = np.exp(-(((e - 1) * rad / (1.0 + 1.5 * dpt)) ** 2)) * (1 - g) ** 2
        ring[ya:yb, xa:xb] += val
    water += (ring * 55)[..., None] * np.array([0.85, 0.9, 1.0], np.float32)

    img = np.concatenate([up, water], axis=0)

    # --- mist, reeds, rain, finish -----------------------------------------
    mist = np.roll(S["mist"], i, axis=1)
    mist = np.concatenate([mist, mist[:, : W - mist.shape[1]]], axis=1)[:, :W]
    ma = (mist ** 1.6) * S["mist_band"] * 0.45
    _over(img[HZ - 80:HZ + 80], np.array([70, 76, 106], np.float32), ma)

    _over(img, np.array([2, 3, 6], np.float32), S["reeds"])

    rf = np.roll(S["rain_far"], i * 18, axis=0)
    rn = np.roll(S["rain_near"], i * 36, axis=0)
    img += (rf * 0.6 + rn)[..., None] * np.array([150, 160, 185], np.float32)

    img *= S["vignette"]
    img += S["dither"][i % 4]
    return np.clip(img, 0, 255).astype(np.uint8)


_SCENE = None


def _render_bytes(i):
    return render_frame(_SCENE, i).tobytes()


def save_still(i, path):
    from PIL import Image
    Image.fromarray(render_frame(build_scene(), i)).save(path)


def make_video(wav_path, mp4_path, workers=None):
    import multiprocessing as mp
    global _SCENE
    _SCENE = build_scene()
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav_path,
           "-c:v", "libx264", "-preset", "slow", "-crf", "17",
           "-tune", "grain", "-pix_fmt", "yuv420p", "-g", str(FPS * 4),
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           mp4_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ctx = mp.get_context("fork")
    with ctx.Pool(workers or max(1, (os.cpu_count() or 2) - 1)) as pool:
        for i, buf in enumerate(pool.imap(_render_bytes, range(FRAMES), chunksize=4)):
            p.stdin.write(buf)
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
    sub.add_parser("audio", help="remake the audio only and remux the loop")
    stl = sub.add_parser("still", help="save one frame as a PNG (quick preview)")
    stl.add_argument("frame", nargs="?", type=int, default=0)
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    wav = os.path.join(OUT, "rainy-night-loop.wav")
    loop = os.path.join(OUT, "rainy-night-loop.mp4")

    if a.cmd == "still":
        path = os.path.join(OUT, f"rainy-night-frame{a.frame}.png")
        save_still(a.frame, path)
        print("done:", path)
    elif a.cmd == "audio":
        make_audio(wav)
        tmp = loop + ".tmp.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", loop, "-i", wav,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, loop)
        print("done:", loop)
    elif a.cmd == "loop":
        print("audio...", flush=True)
        make_audio(wav)
        print("video...", flush=True)
        make_video(wav, loop)
        save_still(FRAMES // 3, os.path.join(OUT, "rainy-night-still.png"))
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
