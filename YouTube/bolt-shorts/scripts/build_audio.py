#!/usr/bin/env python3
"""
Synthesise BOLT #001's original score and sound effects from scratch.

No samples, no third-party audio: every sound is generated here with numpy/scipy,
so all audio is original and free of licensing restrictions.

Outputs:
  public/audio/music/bolt_score.wav          32.0 s stereo score, sections locked to timeline.json
  public/audio/sound-effects/<name>.wav      one file per SFX cue in src/audio/sfxTimeline.ts
"""
import json
import os
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = json.load(open(os.path.join(ROOT, "src/timeline.json")))
BEATS = TL["beats"]
DUR = TL["durationSeconds"]
rng = np.random.default_rng(1001)

# ----------------------------------------------------------------- helpers

def tvec(d):
    return np.arange(int(d * SR)) / SR

def env_ad(n, a, d, curve=4.0):
    """attack (s) then exponential decay over d seconds."""
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), np.exp(-curve * (t - a) / max(d, 1e-4)))
    return e

def env_adsr(n, a, d, s, r):
    t = np.arange(n) / SR
    total = n / SR
    e = np.ones(n) * s
    e[t < a] = t[t < a] / max(a, 1e-4)
    m = (t >= a) & (t < a + d)
    e[m] = 1 - (1 - s) * (t[m] - a) / max(d, 1e-4)
    rel = t > total - r
    e[rel] *= np.clip((total - t[rel]) / max(r, 1e-4), 0, 1)
    return e

def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)

def lp(x, f, order=2):
    sos = signal.butter(order, f, btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)

def hp(x, f, order=2):
    sos = signal.butter(order, f, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)

def noise(d):
    return rng.standard_normal(int(d * SR))

def sweep(f0, f1, d, kind="exp"):
    t = tvec(d)
    if kind == "exp":
        f = f0 * (f1 / f0) ** (t / d)
    else:
        f = f0 + (f1 - f0) * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR)

def saw(freq, d, detune=0.0):
    t = tvec(d)
    return 2 * ((t * freq * (1 + detune)) % 1.0) - 1

def sq(freq, d):
    return np.sign(np.sin(2 * np.pi * freq * tvec(d)))

def tri(freq, d):
    return 2 * np.abs(saw(freq, d)) - 1

def supersaw(freq, d, voices=5, spread=0.012):
    out = np.zeros(int(d * SR))
    for k in range(voices):
        dt = (k - (voices - 1) / 2) * spread / voices
        out += saw(freq, d, dt) * (1.0 if k == voices // 2 else 0.7)
    return out / voices

def fit(x, n, offset=0.0):
    """Pad/trim x to n samples, optionally delayed by `offset` seconds."""
    x = np.concatenate([np.zeros(int(offset * SR)), np.asarray(x, dtype=float)])
    return np.pad(x, (0, max(0, n - len(x))))[:n]

def mixs(*xs):
    """Sum signals of different lengths (zero-padded to the longest)."""
    n = max(len(x) for x in xs)
    return sum(fit(x, n) for x in xs)

def norm(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak

def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def stereo(x, pan=0.0):
    l = x * np.cos((pan + 1) * np.pi / 4)
    r = x * np.sin((pan + 1) * np.pi / 4)
    return np.stack([l, r], axis=1)

def write(path, x):
    x = np.asarray(x)
    if x.ndim == 1:
        x = stereo(x)
    x = np.clip(x, -1, 1)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wavfile.write(path, SR, (x * 32767).astype(np.int16))

def place(buf, start, sig, gain=1.0, pan=0.0):
    i = int(round(start * SR))
    if i >= len(buf):
        return
    s = sig if sig.ndim == 2 else stereo(sig, pan)
    n = min(len(s), len(buf) - i)
    if i < 0:
        s = s[-i:]
        n = min(len(s), len(buf))
        i = 0
    buf[i:i + n] += s[:n] * gain

# ----------------------------------------------------------------- drum kit

def kick(d=0.35):
    t = tvec(d)
    f = 45 + 120 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    click = hp(noise(d), 2000) * np.exp(-t * 120) * 0.3
    return np.tanh((body + click) * 1.6)

def snare(d=0.22):
    t = tvec(d)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    nz = bp(noise(d), 1200, 8000) * np.exp(-t * 16)
    return tone * 0.6 + nz * 0.9

def clap(d=0.25):
    nz = bp(noise(d), 900, 5000)
    t = tvec(d)
    e = np.zeros_like(t)
    for k, o in enumerate([0, 0.011, 0.022]):
        e += np.where(t >= o, np.exp(-(t - o) * (140 if k < 2 else 22)), 0)
    return nz * e * 0.8

def hat(d=0.06, open_=False):
    t = tvec(d if not open_ else 0.25)
    nz = hp(noise(len(t) / SR), 7000)
    return nz * np.exp(-t * (60 if not open_ else 12)) * 0.5

def crash(d=1.8):
    t = tvec(d)
    nz = hp(noise(d), 4000) + 0.3 * bp(noise(d), 2000, 6000)
    return nz * np.exp(-t * 2.2) * 0.5

def tom(freq=110, d=0.3):
    t = tvec(d)
    f = freq * (1 + 0.6 * np.exp(-t * 20))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)

# ----------------------------------------------------------------- tonal voices

def bass_note(m, d):
    f = mtof(m)
    x = saw(f, d) * 0.7 + np.sin(2 * np.pi * f * tvec(d)) * 0.6
    x = lp(x, 900)
    return np.tanh(x * 1.5) * env_adsr(len(x), 0.005, 0.08, 0.7, 0.03)

def stab(ms, d, cutoff=3500):
    x = sum(supersaw(mtof(m), d) for m in ms) / len(ms)
    x = lp(x, cutoff)
    return x * env_ad(len(x), 0.004, d * 0.6, 5)

def pluck(m, d=0.5, bright=1.0):
    f = mtof(m)
    t = tvec(d)
    x = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(4 * np.pi * f * t) * bright + 0.2 * np.sin(6 * np.pi * f * t) * bright)
    return x * np.exp(-t * 7) * env_ad(len(t), 0.003, d, 0.1)

def piano(m, d=1.2):
    f = mtof(m)
    t = tvec(d)
    x = np.zeros_like(t)
    for h, a in [(1, 1), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)]:
        x += a * np.sin(2 * np.pi * f * h * (1 + 0.0004 * h * h) * t) * np.exp(-t * (2.2 + h * 0.9))
    return x * env_ad(len(t), 0.004, d, 0.2)

def brass(ms, d, cutoff=2600):
    t = tvec(d)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t * 3, 0, 1)
    x = np.zeros_like(t)
    for m in ms:
        f = mtof(m)
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        x += (2 * ((ph / (2 * np.pi)) % 1) - 1) * 0.6 + np.sin(ph) * 0.4
    x = lp(x / len(ms), cutoff)
    return x * env_adsr(len(t), 0.03, 0.15, 0.8, 0.12)

def pad(ms, d, cutoff=1800):
    x = sum(supersaw(mtof(m), d, 7, 0.02) for m in ms) / len(ms)
    x = lp(x, cutoff, 2)
    return x * env_adsr(len(x), 0.35, 0.2, 0.85, 0.5)

def bell(m, d=1.5):
    f = mtof(m)
    t = tvec(d)
    x = np.sin(2 * np.pi * f * t + 2.2 * np.sin(2 * np.pi * f * 3.5 * t) * np.exp(-t * 4))
    return x * np.exp(-t * 3.2)

def riser(d, f0=200, f1=2400):
    t = tvec(d)
    nz = noise(d)
    out = np.zeros_like(nz)
    segs = 24
    for k in range(segs):
        a, b = int(k * len(nz) / segs), int((k + 1) * len(nz) / segs)
        fc = f0 * (f1 / f0) ** (k / segs)
        out[a:b] = bp(nz, fc * 0.7, min(fc * 1.4, SR / 2 - 100))[a:b]
    tone = sweep(f0 / 2, f1 / 3, d) * 0.3
    return (out + tone) * (t / d) ** 2

def boom(d=1.6):
    t = tvec(d)
    f = 30 + 90 * np.exp(-t * 6)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5)
    nz = lp(noise(d), 400) * np.exp(-t * 6) * 0.6
    return np.tanh((x + nz) * 1.8)

def heartbeat():
    d = 0.5
    t = tvec(d)
    def thump(o, a):
        tt = np.clip(t - o, 0, None)
        return np.where(t >= o, np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 18) * a, 0)
    return lp(thump(0, 1.0) + thump(0.16, 0.75), 300)

# ----------------------------------------------------------------- the score

def build_score():
    n = int(DUR * SR)
    mus = np.zeros((n, 2))
    beat = 0.5  # 120 BPM: scene cuts land on beats
    slip = BEATS["slip"]
    p0, p1 = BEATS["musicPauseStart"], BEATS["musicPauseEnd"]
    win = BEATS["buttonSlam"]
    go = BEATS["go"]

    def drums(t0, t1, kick_every=1, clap_on=True, hats=8, fill_end=False, gain=1.0):
        t = t0
        while t < t1 - 1e-6:
            bi = round((t - 0) / beat)
            place(mus, t, kick(), 0.85 * gain)
            if clap_on and bi % 2 == 1:
                place(mus, t, clap(), 0.45 * gain)
                place(mus, t, snare(), 0.35 * gain)
            t += beat * kick_every
        step = beat / (hats / 2)
        t = t0
        k = 0
        while t < t1 - 1e-6:
            place(mus, t, hat(), (0.22 if k % 2 else 0.13) * gain, pan=0.25)
            t += step
            k += 1
        if fill_end:
            for i, f in enumerate([220, 180, 150, 120]):
                place(mus, t1 - beat + i * beat / 4, tom(f), 0.5 * gain, pan=-0.3 + i * 0.2)

    # HOOK 0-3: impact, Cm stabs, riser
    place(mus, 0, boom(), 0.9)
    place(mus, 0, crash(), 0.55)
    for i, tt in enumerate(np.arange(0, 3, beat)):
        ch = [60, 63, 67] if i < 4 else [56, 60, 63]
        place(mus, tt, stab(ch, 0.35), 0.45, pan=-0.15)
        place(mus, tt, bass_note(36 if i < 4 else 32, 0.45), 0.5)
    drums(0.5, 3.0, hats=8, clap_on=True, gain=0.9)
    place(mus, 1.5, riser(1.5), 0.35)

    # START 3-8: driving groove, tension during beeps, GO hit
    place(mus, 3.0, crash(), 0.4)
    drums(3.0, 5.0, hats=16)
    prog = [36, 36, 32, 34]
    for i, tt in enumerate(np.arange(3.0, 5.0, beat / 2)):
        place(mus, tt, bass_note(prog[int((tt - 3) // 1) % 4], 0.24), 0.45)
    arp = [60, 63, 67, 72, 67, 63]
    for i, tt in enumerate(np.arange(3.0, 5.0, beat / 4)):
        place(mus, tt, pluck(arp[i % len(arp)] + 12, 0.25), 0.16, pan=0.3)
    # beeps section: kick only + riser
    for tt in np.arange(5.0, go, beat / 2):
        place(mus, tt, kick(0.2), 0.45)
    place(mus, 5.0, riser(go - 5.0, 300, 3000), 0.45)
    place(mus, go, boom(1.0), 0.6)
    place(mus, go, crash(), 0.5)
    place(mus, go, stab([60, 63, 67, 72], 0.5), 0.5)

    # RUN 6.05-14.55: full percussion, energetic
    drums(6.0, slip - 0.05, hats=16, gain=1.0)
    bassline = [36, 36, 44, 44, 46, 46, 43, 43]  # C C Ab Ab Bb Bb G G (per half-bar)
    for i, tt in enumerate(np.arange(6.0, slip - 0.05, beat / 2)):
        m = bassline[int((tt - 6.0) // 1) % len(bassline)]
        place(mus, tt, bass_note(m, 0.22), 0.5)
    lead = [72, 75, 79, 75, 72, 70, 67, 70, 72, 75, 79, 82, 84, 82, 79, 75]
    for i, tt in enumerate(np.arange(8.0, slip - 0.05, beat / 2)):
        place(mus, tt, pluck(lead[i % len(lead)], 0.3), 0.18, pan=-0.25)
    chords = {0: [60, 63, 67], 1: [56, 60, 63], 2: [58, 62, 65], 3: [55, 59, 62]}
    for i, tt in enumerate(np.arange(6.0, slip - 0.05, 1.0)):
        place(mus, tt, stab(chords[i % 4], 0.3, 2800), 0.25, pan=0.2)
    for tt in [10.0, 12.0, 14.0]:
        place(mus, tt, crash(1.0), 0.25)
    for i, f in enumerate([260, 220, 180, 150]):
        place(mus, 13.5 + i * 0.125, tom(f), 0.4)

    # DISASTER slip-20.45: music drop, heartbeat, rising suspense, pause
    d1 = p0 - slip
    t = tvec(d1)
    drone = (np.sin(2 * np.pi * mtof(36) * t) + 0.5 * np.sin(2 * np.pi * mtof(43) * t * 1.001)) * np.clip(t / 0.4, 0, 1)
    place(mus, slip, lp(drone, 500) * 0.5, 0.6)
    rise = sweep(mtof(60), mtof(72), d1) * 0.25 + sweep(mtof(63), mtof(75), d1) * 0.18
    place(mus, slip, rise * np.clip(t / d1, 0, 1) ** 1.5, 0.55)
    hb = 15.0
    while hb < p0 - 0.1:
        place(mus, hb, heartbeat(), 0.9)
        hb += 0.75 if hb < 17 else 0.55
    place(mus, slip, boom(1.2), 0.5)
    # pause = silence; then roll + riser into the win
    place(mus, p1, heartbeat(), 1.0)
    dr = win - p1 - 0.05
    tt = p1 + 0.3
    k = 0
    while tt < win - 0.05:
        gap = max(0.04, 0.2 * (1 - (tt - p1) / dr))
        place(mus, tt, snare(0.1), 0.25 + 0.4 * (tt - p1) / dr)
        tt += gap
        k += 1
    place(mus, p1 + 0.1, riser(win - p1 - 0.1, 250, 4000), 0.5)

    # WIN 20.45-25: fanfare in C major
    place(mus, win, boom(1.4), 0.8)
    place(mus, win, crash(2.2), 0.6)
    fan = [(win, [60, 64, 67, 72], 0.6), (win + 0.6, [60, 64, 67, 72], 0.25), (win + 0.85, [65, 69, 72, 77], 0.6),
           (win + 1.5, [67, 71, 74, 79], 0.9), (win + 2.5, [65, 69, 72, 77], 0.5), (win + 3.0, [67, 71, 74, 79], 0.5),
           (win + 3.5, [60, 64, 67, 72, 76], 1.0)]
    for st, ch, d in fan:
        place(mus, st, brass(ch, d), 0.42, pan=-0.1)
        place(mus, st, stab(ch, min(d, 0.4), 4500), 0.22, pan=0.2)
    drums(win, 24.95, hats=16, gain=0.95)
    winbass = [36, 41, 43, 36]
    for tt in np.arange(win, 24.95, beat / 2):
        place(mus, tt, bass_note(winbass[int((tt - win) // 1.15) % 4], 0.22), 0.45)
    mel = [72, 76, 79, 84, 83, 79, 76, 79, 81, 79, 77, 76, 74, 76, 79, 72]
    for i, tt in enumerate(np.arange(win + 0.5, 24.9, beat / 2)):
        place(mus, tt, pluck(mel[i % len(mel)] + 12, 0.35), 0.13, pan=0.35)
    place(mus, 24.4, riser(0.6, 800, 5000) * 0.5, 0.3)

    # DONATION 25-32: warm, emotional, uplifting
    place(mus, 25.0, bell(84, 2.0), 0.18)
    prog2 = [(25.0, [53, 57, 60, 65], 41), (26.0, [57, 60, 64, 69], 45), (27.0, [55, 59, 62, 67], 43),
             (BEATS["donatePress"], [60, 64, 67, 72], 36), (28.9, [53, 57, 60, 65], 41), (BEATS["donatedText"], [60, 64, 67, 72], 48),
             (30.15, [53, 57, 60, 65], 41), (31.0, [55, 59, 62, 67], 43), (31.5, [60, 64, 67, 72], 36)]
    for i, (st, ch, b) in enumerate(prog2):
        en = prog2[i + 1][0] if i + 1 < len(prog2) else DUR
        d = en - st + 0.4
        place(mus, st, pad(ch, d), 0.34)
        place(mus, st, bass_note(b, min(d, 1.2)) * 0.6, 0.4)
    melody = [(25.0, 77), (25.5, 76), (26.0, 72), (26.5, 76), (27.0, 74), (27.5, 71),
              (27.9, 79), (28.2, 84), (28.5, 81), (28.9, 77), (29.35, 84), (29.7, 79), (30.15, 81), (30.6, 77), (31.0, 79), (31.5, 84)]
    for st, m in melody:
        place(mus, st, piano(m, 1.3), 0.3, pan=0.1)
    # gentle uplifting groove after the donation
    for tt in np.arange(28.9, 31.5, beat):
        place(mus, tt, kick(0.25), 0.35)
        if round((tt - 28.9) / beat) % 2 == 1:
            place(mus, tt, clap(), 0.22)
    for tt in np.arange(28.9, 31.5, beat / 2):
        place(mus, tt, hat(), 0.08, pan=0.3)
    place(mus, 29.35, crash(2.0), 0.25)

    # clean ending: final chord, fade the last 0.45 s
    fade = int(0.45 * SR)
    mus[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 1.5

    # gentle bus glue + normalise
    mus = np.tanh(mus * 1.2) / np.tanh(1.2)
    mus = mus / (np.max(np.abs(mus)) + 1e-9) * 0.89
    return mus

# ----------------------------------------------------------------- sound effects

def sfx():
    S = {}
    S["impact_big"] = mixs(np.tanh(boom(1.4) * 1.3), hp(noise(0.3), 1500) * env_ad(int(0.3 * SR), 0.001, 0.1, 6) * 0.4)
    def whoosh(d, f0, f1, g=1.0):
        nz = noise(d)
        out = np.zeros_like(nz)
        segs = 20
        for k in range(segs):
            a, b = int(k * len(nz) / segs), int((k + 1) * len(nz) / segs)
            fc = f0 * (f1 / f0) ** (k / segs)
            out[a:b] = bp(nz, fc * 0.6, min(fc * 1.6, SR / 2 - 100))[a:b]
        tt = tvec(d)
        return out * np.sin(np.pi * tt / d) ** 2 * g
    S["whoosh_long"] = whoosh(0.9, 300, 2500)
    S["whoosh_short"] = whoosh(0.35, 500, 3500)
    S["whoosh_hammer"] = whoosh(0.55, 200, 900) * 1.3 + lp(noise(0.55), 200) * np.sin(np.pi * tvec(0.55) / 0.55) * 0.6
    S["whoosh_slowmo"] = whoosh(1.4, 1200, 150) * 0.9 + sweep(400, 90, 1.4) * np.exp(-tvec(1.4) * 1.5) * 0.3
    S["launch_whoosh"] = whoosh(0.6, 250, 4000) * 1.2 + fit(kick(0.3), int(0.6 * SR)) * 0.6
    S["slam"] = np.tanh(boom(0.7) * 2) * 0.8 + fit(clap(0.25), int(0.7 * SR)) * 0.7
    # cash register: drawer rattle + bell ding
    d = 0.9
    t = tvec(d)
    rattle = bp(noise(d), 1500, 6000) * (np.exp(-t * 10) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * t)))) * 0.6
    ding = fit(bell(91, 0.8) + 0.6 * bell(96, 0.8), len(t), 0.1)
    S["cash_register"] = rattle + ding * 0.7
    S["boing"] = np.sin(2 * np.pi * np.cumsum(180 + 260 * tvec(0.45) / 0.45 + 40 * np.sin(2 * np.pi * 16 * tvec(0.45))) / SR) * np.exp(-tvec(0.45) * 5)
    S["board_drop"] = np.tanh(boom(0.6) * 1.5) * 0.8 + bp(noise(0.6), 300, 2500) * np.exp(-tvec(0.6) * 14) * 0.6
    def beep(f, d=0.16):
        x = sq(f, d) * 0.4 + np.sin(2 * np.pi * f * tvec(d)) * 0.6
        return lp(x, 5000) * env_adsr(int(d * SR), 0.003, 0.02, 0.9, 0.03)
    S["beep"] = beep(880)
    S["beep_low"] = beep(660, 0.12)
    S["buzzer_go"] = lp(sq(220, 0.7) * 0.5 + saw(330, 0.7) * 0.5, 3000) * env_adsr(int(0.7 * SR), 0.005, 0.05, 0.85, 0.12) + fit(beep(1320, 0.4), int(0.7 * SR)) * 0.4
    def servo(d, f0, f1, wob=30):
        tt = tvec(d)
        f = f0 + (f1 - f0) * tt / d + wob * np.sin(2 * np.pi * 9 * tt)
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.35 + np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * 0.3
        return bp(x, 300, 4000) * env_adsr(len(tt), 0.02, 0.05, 0.8, 0.06)
    S["servo"] = servo(0.3, 500, 900)
    S["servo_panic"] = servo(1.0, 700, 1400, 200)
    S["servo_strain"] = servo(0.9, 300, 700, 60)
    S["hatch_open"] = np.tanh(boom(1.0) * 1.2) * 0.7 + servo(1.0, 120, 60, 20) * 0.6 + bp(noise(1.0), 200, 1200) * np.exp(-tvec(1.0) * 3) * 0.4
    tt = tvec(0.5)
    S["spin_feet"] = bp(noise(0.5), 400, 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * 40 * tt)) * env_adsr(len(tt), 0.02, 0.1, 0.8, 0.1) + sweep(300, 1200, 0.5) * 0.25
    def step(f):
        tt = tvec(0.09)
        return (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 45) + bp(noise(0.09), 1500, 5000) * np.exp(-tt * 90) * 0.3)
    S["step_a"] = step(520)
    S["step_b"] = step(460)
    S["squish"] = bp(noise(0.25), 200, 1500) * env_ad(int(0.25 * SR), 0.01, 0.2, 5) * 0.8 + sweep(400, 150, 0.25) * np.exp(-tvec(0.25) * 10) * 0.5
    S["jump"] = sweep(250, 1100, 0.3) * np.exp(-tvec(0.3) * 6) * 0.8
    S["land_thud"] = np.tanh(kick(0.35) * 1.4) + bp(noise(0.35), 150, 900) * np.exp(-tvec(0.35) * 15) * 0.6
    S["ping_antenna"] = bell(100, 0.8) * 0.7 + np.sin(2 * np.pi * mtof(96) * tvec(0.8)) * np.exp(-tvec(0.8) * 6) * (1 + 0.5 * np.sin(2 * np.pi * 22 * tvec(0.8))) * 0.4
    tt = tvec(0.35)
    S["yikes"] = np.sin(2 * np.pi * np.cumsum(900 + 900 * tt / 0.35 + 120 * np.sin(2 * np.pi * 30 * tt)) / SR) * env_adsr(len(tt), 0.01, 0.05, 0.8, 0.1) * 0.5
    tt = tvec(0.45)
    S["squeak_slip"] = np.sin(2 * np.pi * np.cumsum(1400 - 900 * tt / 0.45 + 200 * np.sin(2 * np.pi * 25 * tt)) / SR) * env_adsr(len(tt), 0.01, 0.1, 0.7, 0.1) * 0.6
    tt = tvec(1.2)
    clang = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, k in [(523, 3), (1287, 4), (2093, 6), (3321, 9)])
    S["clang_grab"] = clang * 0.5 + fit(np.tanh(kick(0.4) * 1.5), len(tt)) * 0.6
    tt = tvec(0.5)
    S["clank"] = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, k in [(700, 8), (1650, 10), (2900, 14)]) * 0.5
    tt = tvec(2.2)
    S["alarm"] = (sq(880, 2.2) * (np.sin(2 * np.pi * 2 * tt) > 0) + sq(660, 2.2) * (np.sin(2 * np.pi * 2 * tt) <= 0)) * 0.3
    S["alarm"] = lp(S["alarm"], 3500) * env_adsr(len(tt), 0.02, 0.1, 0.9, 0.3)
    S["button_slam"] = np.tanh(boom(1.0) * 2.0) + fit(clap(0.25), int(1.0 * SR)) * 0.8 + fit(beep(1046, 0.5), int(1.0 * SR), 0.05) * 0.5
    def pops(d, n, seed):
        r = np.random.default_rng(seed)
        out = np.zeros(int(d * SR))
        for _ in range(n):
            o = int(r.uniform(0, d * 0.7) * SR)
            p = bp(r.standard_normal(int(0.05 * SR)), 1500, 9000) * np.exp(-tvec(0.05) * 70)
            out[o:o + len(p)] += p * r.uniform(0.3, 1)
        return out
    S["confetti_pop"] = np.tanh(boom(0.5) * 1.2) * 0.6 + fit(hp(noise(0.08), 800) * np.exp(-tvec(0.08) * 50), int(0.5 * SR)) + pops(0.5, 25, 7) * 0.5
    def crowd(d, swell=1.0, seed=11, voices=40, base=260):
        r = np.random.default_rng(seed)
        tt = tvec(d)
        n = len(tt)
        body = bp(r.standard_normal(n), 350, 2800) * 0.5
        am = 0.6 + 0.4 * lp(r.standard_normal(n), 3) / 0.05
        out = body * np.clip(am, 0.2, 1.4)
        for _ in range(voices):
            st = r.uniform(0, d * 0.5)
            ln = r.uniform(0.4, 1.1)
            f0 = base * r.uniform(0.8, 2.0)
            vt = tvec(ln)
            f = f0 * (1 + 0.35 * np.sin(np.pi * vt / ln)) * (1 + 0.02 * np.sin(2 * np.pi * 6 * vt))
            v = 2 * ((np.cumsum(f) / SR) % 1) - 1
            v = bp(v, 500, 1400) + 0.5 * bp(v, 1800, 2800)
            v *= np.sin(np.pi * vt / ln) ** 2
            i = int(st * SR)
            out[i:i + len(v)] += v[: max(0, n - i)] * r.uniform(0.2, 0.5)
        out += pops(d, 60, seed + 1) * 0.35
        e = np.clip(tt / 0.15, 0, 1) * np.exp(-np.clip(tt - d * 0.45, 0, None) * 2.0 / swell)
        return out * e
    S["crowd_cheer"] = crowd(3.0, 1.2, 11, 50)
    S["crowd_happy"] = crowd(2.6, 1.0, 21, 30, 300) * 0.9
    def chime(notes, gap, d=1.6):
        out = np.zeros(int((d + gap * len(notes)) * SR))
        for k, m in enumerate(notes):
            b = bell(m, d) * 0.6 + piano(m, d) * 0.4
            i = int(k * gap * SR)
            out[i:i + len(b)] += b
        return out
    mc = chime([84, 88, 91, 96, 100], 0.07, 1.4)
    S["magic_chime"] = mc + fit(hp(noise(1.75), 6000) * np.exp(-tvec(1.75) * 3), len(mc)) * 0.1
    S["soft_chime"] = chime([79, 84, 88], 0.11, 1.4)
    dc = chime([72, 76, 79, 84, 88, 91], 0.06, 1.8)
    S["donate_chime"] = dc + fit(np.tanh(kick(0.3)), len(dc)) * 0.3
    # coin stream: many tiny metallic tinks
    d = 1.4
    out = np.zeros(int(d * SR))
    r = np.random.default_rng(5)
    for _ in range(70):
        o = int(r.uniform(0, d - 0.15) * SR)
        f = r.uniform(2500, 5200)
        tk = np.sin(2 * np.pi * f * tvec(0.12)) * np.exp(-tvec(0.12) * 40) + np.sin(2 * np.pi * f * 1.5 * tvec(0.12)) * np.exp(-tvec(0.12) * 55) * 0.5
        out[o:o + len(tk)] += tk * r.uniform(0.2, 0.6)
    S["coins_stream"] = out + whoosh(d, 400, 2000) * 0.5
    d = 0.9
    out = np.zeros(int(d * SR))
    for k in range(7):
        o = int(k * 0.08 * SR)
        p = sweep(300 + 60 * k, 900 + 80 * k, 0.12) * np.exp(-tvec(0.12) * 25)
        out[o:o + len(p)] += p
    S["pop_boxes"] = out * 0.7
    return S

if __name__ == "__main__":
    score = build_score()
    write(os.path.join(ROOT, "public/audio/music/bolt_score.wav"), score)
    print(f"score: {len(score) / SR:.2f}s")
    for name, x in sfx().items():
        x = np.asarray(x, dtype=float)
        x = norm(x, 0.9)
        write(os.path.join(ROOT, f"public/audio/sound-effects/{name}.wav"), x)
    print("sfx:", len(os.listdir(os.path.join(ROOT, "public/audio/sound-effects"))))
