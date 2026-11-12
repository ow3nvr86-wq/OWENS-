"""Music and sound effects for the WW2 two-parter - all synthesised with numpy, no samples.

Reads scene_timing.json, build/vo_timing.json and audio/narration.wav and writes:
  audio/music_sfx.wav        music + ambience + effects (unducked)
  audio/mix_with_voice.wav   final mix, narration on top, music ducked under the voice, -14 LUFS
  audio/mix_no_voice.wav     music + effects only, -14 LUFS (for recording your own voice)
  sound_design.txt           every cue with its time

  python audio.py
"""
import json
import math
import os
import subprocess
import wave

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
import sys
PART = next((x for x in sys.argv[1:] if x.startswith('part')), 'part1')
PDIR = os.path.join(ROOT, PART)
SR = 48000
T = json.load(open(os.path.join(PDIR, 'scene_timing.json')))
DUR = T['duration']
N = int(DUR * SR)
EV = T['events']
CUES = []


def cue(t, what, layer):
    CUES.append((t, what, layer))


# ----------------------------------------------------------------------------------------------
# DSP helpers
# ----------------------------------------------------------------------------------------------
def noise(n, seed, colour='white'):
    r = np.random.default_rng(seed).standard_normal(n)
    if colour == 'white':
        return r
    X = np.fft.rfft(r)
    f = np.fft.rfftfreq(n, 1 / SR) + 1.0
    X /= np.sqrt(f) if colour == 'pink' else f
    y = np.fft.irfft(X, n)
    return y / (np.abs(y).max() + 1e-9)


def bandpass(x, lo=None, hi=None, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-3
    Hh = np.ones_like(f)
    if lo:
        Hh /= np.sqrt(1 + (lo / f) ** (2 * order))
    if hi:
        Hh /= np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * Hh, len(x))


def sweep_bp(x, centre_fn, q=6.0, block=4096):
    out = np.zeros(len(x) + block)
    win = np.hanning(block)
    hop = block // 2
    f = np.fft.rfftfreq(block, 1 / SR) + 1e-3
    for i in range(0, len(x), hop):
        seg = x[i:i + block]
        if len(seg) < block:
            seg = np.pad(seg, (0, block - len(seg)))
        fc = centre_fn((i + block / 2) / SR)
        H_ = 1.0 / np.sqrt(1 + ((f - fc) / (fc / q)) ** 2)
        out[i:i + block] += np.fft.irfft(np.fft.rfft(seg * win) * H_, block)
    return out[:len(x)]


def norm(y):
    return y / (np.abs(y).max() + 1e-9)


def env(t, pts):
    ts, vs = zip(*pts)
    return np.interp(t, ts, vs)


def reverb(x, seconds=2.4, seed=0, damp=3.0, mix=0.35):
    n = int(seconds * SR)
    tt = np.arange(n) / SR
    ir = np.random.default_rng(seed).standard_normal(n) * np.exp(-damp * tt / seconds * 2.3)
    ir = bandpass(ir, 150, 5000)
    ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n
    wet = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    return x * (1 - mix) + wet * mix * 2.2


def place(buf, sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= buf.shape[1] or i + len(sig) <= 0:
        return
    j0 = max(0, -i)
    sig = sig[j0:]
    i = max(i, 0)
    n = min(len(sig), buf.shape[1] - i)
    gl = math.cos((pan + 1) * math.pi / 4) * gain
    gr = math.sin((pan + 1) * math.pi / 4) * gain
    buf[0, i:i + n] += sig[:n] * gl
    buf[1, i:i + n] += sig[:n] * gr


def tt(d):
    return np.arange(int(d * SR)) / SR


# ----------------------------------------------------------------------------------------------
# Instruments (period-style: pipe, shawm, bagpipe drone, tabor, hurdy-gurdy-like drone, bells, choir)
# ----------------------------------------------------------------------------------------------
def pipe(f, d, vib=0.004, breath=0.08):
    t = tt(d)
    ph = 2 * np.pi * np.cumsum(f * (1 + vib * np.sin(2 * np.pi * 5.2 * t))) / SR
    y = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    y += breath * bandpass(np.random.default_rng(int(f)).standard_normal(len(t)), 1500, 6000)
    a = np.minimum(t / 0.025, 1) * np.minimum((d - t) / 0.05, 1)
    return y * a


def shawm(f, d, detune=0.0, bright=1.0):
    """Double-reed shawm: a buzzy pulse wave through a nasal formant."""
    t = tt(d)
    fr = f * 2 ** (detune / 1200) * (1 + 0.005 * np.sin(2 * np.pi * 5.6 * t))
    ph = np.cumsum(fr) / SR
    y = ((ph % 1.0) < 0.32).astype(float) * 2 - 1
    y = bandpass(y, 300, 3500 * bright, order=1)
    a = np.minimum(t / 0.03, 1) * np.minimum((d - t) / 0.06, 1)
    return y * a


def drone(f, d, seed=0, cutoff=900, buzz=0.15):
    t = tt(d)
    y = np.zeros_like(t)
    r = np.random.default_rng(seed)
    for det in (-0.15, 0.0, 0.12):
        y += 2 * ((t * f * (1 + det / 100) + r.uniform()) % 1.0) - 1
        y += 0.5 * (2 * ((t * f * 2 * (1 + det / 100) + r.uniform()) % 1.0) - 1)
    y = bandpass(y, 40, cutoff)
    y += buzz * bandpass(np.sign(np.sin(2 * np.pi * f * 4 * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t)), 800, 3000)
    return norm(y)


def tabor(seed=0, f0=130.0):
    t = tt(0.45)
    ph = 2 * np.pi * np.cumsum(f0 * (0.7 + 0.3 * np.exp(-t * 30))) / SR
    body = np.sin(ph) * np.exp(-t * 11)
    slap = bandpass(np.random.default_rng(seed).standard_normal(len(t)), 500, 5000) * np.exp(-t * 60) * 0.5
    snare = bandpass(np.random.default_rng(seed + 1).standard_normal(len(t)), 2000, 7000) * np.exp(-t * 18) * 0.25
    return norm(body + slap + snare)


def stomp(seed=0):
    t = tt(0.35)
    r = np.random.default_rng(seed)
    body = np.sin(2 * np.pi * (70 + 30 * np.exp(-t * 40)) * t) * np.exp(-t * 16)
    grit = bandpass(r.standard_normal(len(t)), 200, 2500) * np.exp(-t * 40)
    return norm(body + 0.7 * grit)


def tap(seed=0):
    """A hard leather sole on a cobble."""
    t = tt(0.12)
    r = np.random.default_rng(seed)
    y = bandpass(r.standard_normal(len(t)), 900, 7000) * np.exp(-t * 70) + 0.4 * np.sin(2 * np.pi * 420 * t) * np.exp(-t * 50)
    return norm(y)


def bell(freq, d=6.0):
    t = tt(d)
    y = np.zeros_like(t)
    for k, a, dk in ((0.5, 0.6, 0.5), (1.0, 1.0, 0.8), (1.19, 0.55, 1.2), (1.5, 0.35, 1.5), (2.0, 0.3, 1.9), (2.74, 0.22, 2.4), (3.3, 0.12, 3.0)):
        y += a * np.sin(2 * np.pi * freq * k * t) * np.exp(-t * dk)
    return y * np.minimum(t / 0.003, 1)


def choir(notes, d, seed=0):
    """A wordless 'ah' choir pad: detuned saws through two vowel formants."""
    t = tt(d)
    y = np.zeros_like(t)
    r = np.random.default_rng(seed)
    for f in notes:
        for det in (-0.25, 0.0, 0.22):
            y += 2 * ((t * f * (1 + det / 100) * (1 + 0.003 * np.sin(2 * np.pi * 4.5 * t + r.uniform(0, 6))) + r.uniform()) % 1.0) - 1
    a = bandpass(y, 600, 900, order=2)
    b = bandpass(y, 1050, 1400, order=2)
    y = norm(a + 0.6 * b + 0.15 * bandpass(y, 80, 400))
    return y * np.minimum(t / 1.2, 1) * np.minimum((d - t) / 1.2, 1)


def heartbeat(seed=0):
    t = tt(0.6)
    k1 = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 18)
    t2 = np.clip(t - 0.22, 0, None)
    k2 = 0.7 * np.sin(2 * np.pi * 46 * t2) * np.exp(-t2 * 20) * (t > 0.22)
    return norm(k1 + k2)


def boom(d=2.5, f0=62, f1=30, seed=0):
    t = tt(d)
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-t * 3.0)) / SR
    body = np.sin(ph) * np.exp(-t * 1.6)
    n_ = bandpass(noise(len(t), seed), None, 300) * np.exp(-t * 5.0) * 0.6
    return np.tanh(1.6 * (body + n_))


def whoosh(d=0.8, seed=0, lo=300, hi=3000, up=True):
    t = tt(d)
    x = noise(len(t), seed, 'pink')
    y = sweep_bp(x, lambda s: lo + (hi - lo) * (s / d if up else 1 - s / d), q=3)
    return norm(y) * np.sin(np.pi * t / d) ** 1.5


def tear(d=0.55, seed=0):
    t = tt(d)
    r = np.random.default_rng(seed)
    crackle = (r.random(len(t)) < 0.06) * r.standard_normal(len(t))
    y = bandpass(crackle + 0.4 * r.standard_normal(len(t)), 1200, 9000) * (0.4 + 0.6 * np.sin(np.pi * t / d))
    return norm(y)


def page(d=0.6, seed=0):
    t = tt(d)
    r = np.random.default_rng(seed)
    swish = sweep_bp(r.standard_normal(len(t)), lambda s: 800 + 2600 * math.sin(math.pi * s / d), q=2)
    flap = (t > d * 0.75) * bandpass(r.standard_normal(len(t)), 200, 2000) * np.exp(-(t - d * 0.75).clip(0) * 30)
    return norm(norm(swish) * np.sin(np.pi * t / d) + 0.8 * flap)


def ink_swoosh(d=0.8, seed=0):
    t = tt(d)
    y = sweep_bp(noise(len(t), seed, 'brown'), lambda s: 200 + 900 * s / d, q=2)
    return norm(y) * np.sin(np.pi * t / d)


def murmur(n, seed, density=1.0):
    r = np.random.default_rng(seed)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for k in range(int(4 * density)):
        c0 = r.uniform(380, 700)
        ph = r.uniform(0, 6.28)
        rate = r.uniform(0.6, 1.4)
        sw = sweep_bp(noise(n, seed * 10 + k, 'pink'), lambda x, c0=c0, ph=ph, rate=rate: c0 + 260 * math.sin(2 * math.pi * x * rate + ph), q=5)
        e = 0.5 + 0.5 * np.sin(2 * np.pi * t / r.uniform(1.6, 3.4) + r.uniform(0, 6.28))
        y += norm(sw) * e ** 2
    return norm(y)


def wind(n, seed, lo=200, hi=900):
    t = np.arange(n) / SR
    y = sweep_bp(noise(n, seed, 'pink'), lambda s: lo + (hi - lo) * (0.5 + 0.5 * math.sin(s * 0.7 + seed)), q=4)
    return norm(y) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 5.3 + seed))


# ----------------------------------------------------------------------------------------------
# More instruments and effects for Roanoke: a plucked lute, a bowed viol, a natural trumpet, surf,
# gulls, crows, a creaking hull, oars, hammer blows, an arrow, cannon, fire, rain, crickets and frogs.
# ----------------------------------------------------------------------------------------------
def lute(f, d=2.0, seed=0, bright=0.5):
    """Karplus-Strong plucked string."""
    n = int(d * SR)
    p = max(2, int(SR / f))
    r = np.random.default_rng(seed)
    buf = r.uniform(-1, 1, p)
    out = np.zeros(n)
    for i in range(n):
        j = i % p
        out[i] = buf[j]
        buf[j] = 0.996 * (bright * buf[j] + (1 - bright) * 0.5 * (buf[j] + buf[(j + 1) % p]))
    return out * np.minimum(np.arange(n) / 30.0, 1)


def lute_fast(f, d=2.0, seed=0):
    """A cheaper pluck: decaying harmonics with a soft attack (used for many notes)."""
    t = tt(d)
    y = np.zeros_like(t)
    for k, a in ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.18), (5, 0.1)):
        y += a * np.sin(2 * np.pi * f * k * t + k) * np.exp(-t * (1.6 + 1.3 * k))
    return y * np.minimum(t / 0.004, 1)


def viol(f, d, seed=0, vib=0.006):
    """A bowed viol: a saw with a slow bow attack through a woody body resonance."""
    t = tt(d)
    fr = f * (1 + vib * np.sin(2 * np.pi * 5.0 * t) * np.minimum(t / 0.6, 1))
    ph = np.cumsum(fr) / SR
    y = 2 * (ph % 1.0) - 1
    y = bandpass(y, 120, 2600, order=1)
    y += 0.15 * bandpass(noise(len(t), seed), 1200, 4000) * 0.3
    a = np.minimum(t / 0.35, 1) * np.minimum((d - t) / 0.4, 1)
    return norm(y) * np.clip(a, 0, 1)


def recorder(f, d, seed=0):
    return pipe(f, d, vib=0.005, breath=0.12)


def trumpet(f, d, seed=0):
    """A natural (valveless) trumpet note: bright, with a lip-buzz attack."""
    t = tt(d)
    fr = f * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)) * (1 - 0.03 * np.exp(-t * 30))
    ph = np.cumsum(fr) / SR
    y = 2 * (ph % 1.0) - 1
    bright = 1200 + 3500 * np.minimum(t / 0.08, 1)
    y = bandpass(y, 200, 4200, order=1)
    a = np.minimum(t / 0.04, 1) * np.minimum((d - t) / 0.08, 1)
    return norm(y) * a


def surf(n, seed, rate=0.33):
    t = np.arange(n) / SR
    x = noise(n, seed, 'pink')
    y = bandpass(x, 150, 3500)
    e = (0.35 + 0.65 * np.clip(np.sin(2 * np.pi * rate * t + seed), 0, 1) ** 2)
    return norm(y) * e


def lapping(n, seed):
    t = np.arange(n) / SR
    y = bandpass(noise(n, seed, 'pink'), 200, 1400)
    e = 0.25 + 0.75 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.9 * t + seed)) ** 3
    return norm(y) * e


def gull(seed=0):
    r = np.random.default_rng(seed)
    out = []
    for k in range(r.integers(2, 4)):
        d = r.uniform(0.18, 0.32)
        t = tt(d)
        f = 1700 + 900 * np.sin(np.pi * t / d) + r.uniform(-150, 150)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR + 2.5 * np.sin(2 * np.pi * 380 * t))
        out.append(y * np.sin(np.pi * t / d) ** 0.6)
        out.append(np.zeros(int(r.uniform(0.05, 0.12) * SR)))
    return bandpass(np.concatenate(out), 900, 6000)


def caw(seed=0):
    r = np.random.default_rng(seed)
    out = []
    for k in range(r.integers(2, 4)):
        d = r.uniform(0.22, 0.3)
        t = tt(d)
        f = 520 - 120 * t / d
        y = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.6 + bandpass(noise(len(t), seed + k), 600, 3000)
        y = bandpass(y, 500, 2800)
        out.append(norm(y) * np.sin(np.pi * t / d) ** 0.5)
        out.append(np.zeros(int(0.16 * SR)))
    return np.concatenate(out)


def creak(d=1.2, seed=0, f0=90):
    t = tt(d)
    r = np.random.default_rng(seed)
    f = f0 * (1 + 0.5 * np.sin(np.pi * t / d)) + 10 * np.sin(2 * np.pi * 3 * t)
    pulses = np.sin(2 * np.pi * np.cumsum(f) / SR) > 0.97
    y = bandpass(pulses.astype(float) + 0.2 * r.standard_normal(len(t)), 300, 2500)
    return norm(y) * np.sin(np.pi * t / d)


def knock(seed=0, f=180.0):
    """A mallet on timber."""
    t = tt(0.25)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 30) + 0.5 * np.sin(2 * np.pi * f * 2.3 * t) * np.exp(-t * 45)
    y += 0.4 * bandpass(noise(len(t), seed), 800, 4000) * np.exp(-t * 80)
    return norm(y)


def splash(seed=0):
    t = tt(0.5)
    return norm(bandpass(noise(len(t), seed, 'pink'), 400, 5000)) * np.exp(-t * 7) * np.minimum(t / 0.02, 1)


def arrow(seed=0):
    t = tt(0.32)
    wh = sweep_bp(noise(len(t), seed), lambda s: 3500 - 2000 * s / 0.32, q=6) * np.minimum(t / 0.2, 1)
    thunk = np.zeros(int(0.35 * SR))
    t2 = tt(0.35)
    thunk += np.sin(2 * np.pi * 140 * t2) * np.exp(-t2 * 25) + 0.6 * bandpass(noise(len(t2), seed + 1), 300, 3000) * np.exp(-t2 * 60)
    tw = np.sin(2 * np.pi * 95 * t2 * (1 + 0.05 * np.sin(2 * np.pi * 30 * t2))) * np.exp(-t2 * 9) * 0.5
    return np.concatenate([norm(wh) * 0.6, norm(thunk + tw)])


def cannon(seed=0):
    t = tt(2.8)
    y = boom(2.8, 70, 30, seed)
    crack = bandpass(noise(len(t), seed + 5), 500, 6000) * np.exp(-t * 25)
    return norm(y + 0.7 * crack)


def fire(n, seed):
    r = np.random.default_rng(seed)
    y = bandpass(noise(n, seed, 'brown'), 100, 900) * 0.6
    cr = np.zeros(n)
    for i in r.integers(0, n - 400, int(n / SR * 30)):
        cr[i:i + 400] += r.standard_normal(400) * np.exp(-np.arange(400) / 50) * r.uniform(0.3, 1)
    return norm(y + bandpass(cr, 1500, 9000))


def rain(n, seed):
    return norm(bandpass(noise(n, seed), 1800, 9000) + 0.4 * bandpass(noise(n, seed + 1, 'pink'), 300, 1500))


def crickets(n, seed):
    t = np.arange(n) / SR
    y = np.zeros(n)
    r = np.random.default_rng(seed)
    for k in range(5):
        f = r.uniform(4200, 5200)
        rate = r.uniform(2.5, 4.0)
        gate = (np.sin(2 * np.pi * rate * t + r.uniform(0, 6)) > 0.2) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * t + k))
        y += np.sin(2 * np.pi * f * t) * gate * r.uniform(0.4, 1)
    return norm(y)


def frogs(n, seed):
    r = np.random.default_rng(seed)
    y = np.zeros(n)
    for i in r.integers(0, n - SR // 2, int(n / SR * 2.5)):
        t = tt(0.22)
        f = r.uniform(180, 320)
        s_ = np.sign(np.sin(2 * np.pi * f * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 28 * t)) * np.sin(np.pi * t / 0.22)
        y[i:i + len(s_)] += bandpass(s_, 150, 1200) * r.uniform(0.3, 1)
    return norm(y)


def steps(n_steps, period, seed, surface='leaves'):
    out = []
    for k in range(n_steps):
        t = tt(period)
        if surface == 'sand':
            x = bandpass(noise(len(t), seed + k, 'pink'), 200, 2500) * np.exp(-t * 18)
        else:
            x = bandpass(noise(len(t), seed + k), 1200, 7000) * np.exp(-t * 14) * (0.6 + 0.4 * np.random.default_rng(k).random())
        out.append(x)
    return norm(np.concatenate(out))


def scratch(d, seed):
    t = tt(d)
    return bandpass(noise(len(t), seed), 2500, 8000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 9 * t))) * np.sin(np.pi * t / d)


# ----------------------------------------------------------------------------------------------
# The theme: an original, slow air in D minor (3/4) on recorder and lute over a viol; it returns,
# alone and unaccompanied, at the very end.
# ----------------------------------------------------------------------------------------------
NOTE = {'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.0, 'A4': 440.0, 'Bb4': 466.16, 'B4': 493.88,
        'C#5': 554.37, 'C5': 523.25, 'D5': 587.33, 'E5': 659.26, 'F5': 698.46, 'A3': 220.0, 'D3': 146.83, 'G3': 196.0,
        'F3': 174.61, 'C3': 130.81, 'Bb3': 233.08, 'A2': 110.0, 'D2': 73.42, 'G2': 98.0, 'F2': 87.31, 'C2': 65.41, 'Bb2': 116.54}
AIR = [('A4', 2), ('D5', 1), ('C5', 2), ('A4', 1), ('Bb4', 2), ('A4', 1), ('G4', 3), ('F4', 2), ('G4', 1), ('A4', 2), ('D4', 1), ('E4', 3),
       ('A4', 2), ('D5', 1), ('C5', 2), ('A4', 1), ('Bb4', 2), ('G4', 1), ('A4', 3), ('G4', 1), ('F4', 1), ('E4', 1), ('D4', 3)]
BASS = [('D3', 3), ('F3', 3), ('G3', 3), ('C3', 3), ('F3', 3), ('Bb2', 3), ('A2', 6), ('D3', 3), ('F3', 3), ('G3', 3), ('C3', 3),
        ('F3', 3), ('A2', 3), ('D3', 6)]
BEAT = 0.42


def play_line(buf, line, t0, t1, inst, gain, pan=0.0, octave=1.0, filt=None, seed=0, start=0):
    t = t0
    i = start
    while t < t1:
        nm, ln = line[i % len(line)]
        d = ln * BEAT
        f = NOTE[nm] * octave
        if inst == 'recorder':
            s_ = recorder(f * 2, d * 0.97, seed + i)
        elif inst == 'viol':
            s_ = viol(f, d * 1.02, seed + i)
        elif inst == 'lute':
            s_ = lute_fast(f, min(2.4, d + 1.2), seed + i)
            # a broken chord: the fifth above, a little after
            s2 = np.pad(lute_fast(f * 1.5, min(2.4, d + 1.0), seed + i + 50), (int(0.09 * SR), 0))
            s2 = np.pad(s2, (0, max(0, len(s_) - len(s2))))[:len(s_)]
            s_ = s_ + 0.5 * s2
        else:
            s_ = pipe(f, d)
        if filt:
            s_ = bandpass(s_, None, filt)
        place(buf, s_, t, gain, pan)
        t += d
        i += 1


def hum(n, seed, f0=50.0, level=1.0):
    """Industrial mains hum: 50 Hz and its harmonics with a little noise (the plant at night, the control room)."""
    t = np.arange(n) / SR
    y = np.zeros(n)
    for k, a in ((1, 1.0), (2, 0.6), (3, 0.35), (4, 0.2), (6, 0.1)):
        y += a * np.sin(2 * np.pi * f0 * k * t + k)
    y += 0.4 * bandpass(noise(n, seed, 'pink'), 60, 600)
    return norm(y) * level


def clicks(n, seed, rate=3.0):
    r = np.random.default_rng(seed)
    y = np.zeros(n)
    for i in r.integers(0, n - 600, int(n / SR * rate)):
        y[i:i + 600] += bandpass(r.standard_normal(600), 1500, 7000) * np.exp(-np.arange(600) / 60) * r.uniform(0.4, 1)
    return y


def alarm(d, seed=0, f=880.0):
    """A two-tone electronic alarm beep."""
    t = tt(d)
    gate = (np.sin(2 * np.pi * 2.0 * t) > 0).astype(float)
    fr = np.where((t * 2) % 2 < 1, f, f * 0.8)
    y = np.sign(np.sin(2 * np.pi * np.cumsum(fr) / SR)) * gate
    return bandpass(y, 400, 3000) * np.minimum(t / 0.05, 1)


def siren(d, seed=0, f_lo=420, f_hi=980, period=3.2):
    """An electromechanical siren: a slow rising and falling wail."""
    t = tt(d)
    w = 0.5 - 0.5 * np.cos(2 * np.pi * t / period)
    f = f_lo + (f_hi - f_lo) * w
    ph = np.cumsum(f) / SR
    y = np.sin(2 * np.pi * ph) + 0.4 * np.sin(4 * np.pi * ph) + 0.2 * np.sign(np.sin(2 * np.pi * ph * 3))
    return norm(bandpass(y, 300, 4000)) * np.minimum(t / 0.6, 1)


def engine(n, seed, rpm=900, load=1.0):
    """A diesel or petrol engine: a firing-rate buzz with harmonics through a low body."""
    t = np.arange(n) / SR
    f = rpm / 60 * 3 * (1 + 0.02 * np.sin(2 * np.pi * 0.7 * t))
    if callable(load):
        f = f * load(t)
    ph = np.cumsum(f) / SR
    y = ((ph % 1.0) < 0.25).astype(float) * 2 - 1
    y = bandpass(y, 40, 600) + 0.3 * bandpass(noise(n, seed, 'brown'), 30, 400)
    return norm(y)


def roar(n, seed):
    """The roar of a large fire."""
    y = bandpass(noise(n, seed, 'brown'), 40, 700) + 0.3 * bandpass(noise(n, seed + 1, 'pink'), 300, 2000)
    return norm(y + 0.4 * fire(n, seed + 2))


def birdsong(n, seed, density=1.0):
    r = np.random.default_rng(seed)
    y = np.zeros(n)
    for i in r.integers(0, max(1, n - SR // 2), int(n / SR * 3 * density)):
        d = r.uniform(0.05, 0.16)
        t = tt(d)
        f = r.uniform(2800, 5200) + r.uniform(-1500, 1500) * t / d
        s_ = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d)
        y[i:i + len(s_)] += s_ * r.uniform(0.3, 1)
    return norm(y)


def piano(f, d=2.5, seed=0):
    t = tt(d)
    y = np.zeros_like(t)
    for k, a in ((1, 1.0), (2, 0.45), (3, 0.25), (4, 0.12), (5, 0.06)):
        y += a * np.sin(2 * np.pi * f * k * (1 + 0.0004 * k * k) * t) * np.exp(-t * (0.9 + 0.7 * k))
    return y * np.minimum(t / 0.003, 1)


MOTIF = [('E5', 1), ('C5', 1), ('A4', 2), ('B4', 1), ('C5', 1), ('E4', 2), ('A4', 1), ('B4', 1), ('C5', 1), ('D5', 1), ('B4', 4)]
CHORDS = [('A2', 'E3', 'A3'), ('F2', 'C3', 'A3'), ('C3', 'G3', 'E4'), ('G2', 'D3', 'B3')]
NOTE.update({'E3': 164.81, 'A3': 220.0, 'B3': 246.94, 'D3': 146.83, 'G3': 196.0, 'C3': 130.81, 'F2': 87.31, 'G2': 98.0, 'E4': 329.63})


def play_piano(buf, t0, t1, gain, motif=True, chords=True, beat=0.5, start=0, pan=0.0):
    if chords:
        k = 0
        t = t0
        while t < t1:
            for j, nm in enumerate(CHORDS[k % len(CHORDS)]):
                place(buf, piano(NOTE[nm], 3.5, k * 3 + j), t + j * 0.05, gain * 0.5, pan=-0.2)
            t += beat * 8
            k += 1
    if motif:
        t = t0 + beat * 2
        i = start
        while t < t1:
            nm, ln = MOTIF[i % len(MOTIF)]
            place(buf, piano(NOTE[nm], 2.2, 100 + i), t, gain * 0.55, pan=0.15 + pan)
            t += ln * beat
            i += 1



# ----------------------------------------------------------------------------------------------
# Sounds for this film
# ----------------------------------------------------------------------------------------------
def war_drum(seed=0, f0=58.0, d=1.1):
    """A big low frame drum / taiko hit: a pitch-dropping body, a skin slap and a room tail."""
    t = tt(d)
    ph = 2 * np.pi * np.cumsum(f0 * (0.75 + 0.6 * np.exp(-t * 22))) / SR
    body = np.sin(ph) * np.exp(-t * 4.2) + 0.35 * np.sin(2 * ph) * np.exp(-t * 9)
    slap = bandpass(noise(len(t), seed), 300, 3500) * np.exp(-t * 45) * 0.55
    return np.tanh(1.4 * norm(body + slap))


def ring(freqs, d, decay=3.0, seed=0):
    t = tt(d)
    y = sum(a * np.sin(2 * np.pi * f * t + i) * np.exp(-t * decay * (1 + i * 0.4)) for i, (f, a) in enumerate(freqs))
    return norm(y)


def stamp_hit(seed=0):
    t = tt(0.7)
    thud = np.sin(2 * np.pi * (90 + 60 * np.exp(-t * 40)) * t) * np.exp(-t * 14)
    grit = bandpass(noise(len(t), seed), 150, 2500) * np.exp(-t * 30)
    return norm(reverb(norm(thud + 0.8 * grit), 0.8, seed, mix=0.25))


def sword_slash(seed=0):
    t = tt(0.9)
    sw = sweep_bp(noise(len(t), seed), lambda s: 6000 - 4500 * min(1, s / 0.18), q=5) * np.exp(-t * 9) * (t < 0.3)
    metal = ring([(2310, 1.0), (3120, 0.7), (4730, 0.5), (6150, 0.3)], 0.9, 4.5, seed)
    return norm(norm(sw) + 0.5 * metal * np.minimum(t / 0.01, 1))


def stone_crack(seed=0, d=0.9):
    t = tt(d)
    r = np.random.default_rng(seed)
    cr = np.zeros(len(t))
    for i in np.sort(r.integers(0, int(0.45 * SR), 70)):
        n = 300
        cr[i:i + n] += r.standard_normal(n) * np.exp(-np.arange(n) / 40) * r.uniform(0.3, 1) * math.exp(-i / SR * 4)
    thump = np.sin(2 * np.pi * (70 + 40 * np.exp(-t * 30)) * t) * np.exp(-t * 10)
    return norm(bandpass(cr, 800, 9000) + 0.8 * thump)


def shatter(seed=0, d=1.2):
    t = tt(d)
    r = np.random.default_rng(seed)
    y = np.zeros(len(t))
    for i in np.sort(r.integers(0, int(0.8 * SR), 160)):
        n = 600
        f = r.uniform(1500, 6000)
        k = np.arange(n) / SR
        y[i:i + n] += np.sin(2 * np.pi * f * k) * np.exp(-k * r.uniform(60, 160)) * r.uniform(0.2, 1) * math.exp(-i / SR * 3)
    return norm(y + 0.6 * norm(whoosh(d, seed + 1, 200, 1500, up=False)))


def blip(seed=0, f0=620.0):
    t = tt(0.16)
    f = f0 * (1 + 0.5 * np.minimum(t / 0.04, 1))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 26)
    return norm(y + 0.3 * bandpass(noise(len(t), seed), 2000, 8000) * np.exp(-t * 120))


def sparkle(d, seed=0, rate=24.0):
    n = int(d * SR)
    r = np.random.default_rng(seed)
    y = np.zeros(n)
    for i in r.integers(0, n - 4000, int(d * rate)):
        f = r.uniform(2200, 5200)
        k = np.arange(4000) / SR
        y[i:i + 4000] += np.sin(2 * np.pi * f * k) * np.exp(-k * 18) * r.uniform(0.2, 1)
    return norm(y)


def clang(seed=0):
    t = tt(1.4)
    metal = ring([(1210, 1.0), (1870, 0.8), (2650, 0.6), (3970, 0.45), (5300, 0.3)], 1.4, 2.2, seed)
    burst = bandpass(noise(len(t), seed), 1500, 9000) * np.exp(-t * 40)
    return norm(metal + 0.8 * burst)


def tick(seed=0):
    t = tt(0.05)
    return norm(bandpass(noise(len(t), seed), 2500, 9000) * np.exp(-t * 200) + 0.5 * np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 160))


def brass(notes, d, seed=0):
    y = sum(trumpet(f, d, seed + i) for i, f in enumerate(notes))
    y = bandpass(y, 120, 3500)
    t = tt(d)
    return norm(y) * np.minimum(t / 0.6, 1) * np.minimum((d - t) / 0.4, 1)



def rumble(d, seed=0):
    """Tank columns: a low engine-and-track rumble."""
    t = tt(d)
    y = bandpass(noise(len(t), seed, 'brown'), 28, 170) * (0.7 + 0.3 * np.sin(2 * np.pi * 11 * t))
    clat = bandpass(noise(len(t), seed + 1), 900, 3500) * (np.sin(2 * np.pi * 17 * t) > 0.6) * 0.12
    return norm(y + clat) * np.minimum(t / 0.25, 1) * np.minimum((d - t) / 0.35, 1)


def gun(seed=0):
    """A short burst of machine-gun fire."""
    t = tt(0.5)
    y = np.zeros(len(t))
    for k in range(7):
        i = int(k * 0.062 * SR)
        n = int(0.05 * SR)
        y[i:i + n] += bandpass(noise(n, seed + k), 500, 5000) * np.exp(-np.arange(n) / SR * 70)
    return norm(y)


def rewind(d=0.55, seed=0):
    t = tt(d)
    f = 300 * (2 ** (4.2 * t / d))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * t)))
    return norm(y * 0.6 + norm(whoosh(d, seed, 400, 5000)) * 0.8) * np.sin(np.pi * t / d)


def riser(d, seed=0):
    t = tt(d)
    y = sweep_bp(noise(len(t), seed), lambda s: 200 + 5000 * (s / d) ** 2, q=4)
    return norm(y) * (t / d) ** 2


def build_part1():
    mus = np.zeros((2, N))
    sfx = np.zeros((2, N))
    E = EV
    BEAT = 60 / 104.0
    quiet0, quiet1 = E['by'], E['then']
    # music level over time: steady pulse, rising with each conquest, held breath at Moscow, a hit at Pearl Harbor
    lvl = [(0, 0.7), (E['sept'], 0.75), (E['in1940'], 0.85), (E['so'], 0.95), (E['pour'], 1.0), (quiet0, 1.0), (quiet0 + 0.5, 0.12),
           (quiet1 - 0.1, 0.12), (quiet1 + 0.4, 0.8), (E['harbor'], 1.0), (E['part'], 0.9), (DUR - 1.0, 0.7), (DUR, 0.0)]
    t, k = 0.0, 0
    while t < DUR - 0.3:
        lv = env(t, lvl)
        if lv > 0.2:
            b = k % 8
            if b in (0, 4) or (b == 6 and t > E['in1940']) or (b in (3, 7) and t > E['so']):
                place(mus, war_drum(k, 50 if b == 0 else 62), t, (0.95 if b == 0 else 0.6) * lv)
            place(mus, tick(k) * (1.0 if b % 2 == 0 else 0.55), t, 0.22 * lv, pan=0.3 if k % 2 else -0.3)
        t += BEAT / 2
        k += 1
    cue(0.0, 'Music: a driving pulse at 104 BPM (low drums and a ticking clock) over a D minor drone', 'music')
    for a, b, f, g in ((0.0, E['sept'], 73.42, 0.3), (E['sept'], E['in1940'], 73.42, 0.34), (E['in1940'], E['so'], 82.41, 0.36),
                       (E['so'], quiet0 + 0.4, 87.31, 0.4), (quiet1, E['part'], 77.78, 0.38), (E['part'], DUR, 73.42, 0.4)):
        d = b - a
        place(mus, drone(f, d, int(a * 10), 420) * env(tt(d), [(0, 0), (0.25, 1), (d - 0.2, 1), (d, 0)]), a, g)
    dq = quiet1 - quiet0
    place(mus, drone(36.71, dq, 91, 160) * env(tt(dq), [(0, 0), (0.6, 1), (dq - 0.3, 1), (dq, 0)]), quiet0, 0.5)
    for i in range(int(dq / 0.95)):
        place(mus, heartbeat(i), quiet0 + 0.55 + i * 0.95, 0.5)
    cue(quiet0, 'The music drops out at the gates of Moscow: a sub drone, a heartbeat and the wind', 'music')
    for tm, notes, g in ((E['later'] + 0.1, [73.42, 110.0, 146.83], 0.4), (E['first'], [73.42, 110.0, 146.83], 0.4), (E['war'], [82.41, 123.47, 164.81], 0.4),
                         (E['six'], [82.41, 123.47, 164.81], 0.45), (E['pour'], [87.31, 130.81, 174.61], 0.5), (E['part'], [73.42, 110.0, 146.83, 220.0], 0.55)):
        place(mus, brass(notes, 1.5, int(tm * 7)), tm, g)
        cue(tm, 'Low brass stab', 'music')

    def hit(tm, what, g=0.8):
        place(sfx, stamp_hit(int(tm * 13)), tm, g)
        cue(tm, what, 'sfx')

    # --- the hook
    place(sfx, boom(2.0, 60, 30, 1), 0.0, 0.8)
    place(sfx, whoosh(0.7, 2, 300, 2500, up=False), 0.0, 0.4)
    cue(0.0, 'Frame one: a low boom as the map of 1939 opens', 'sfx')
    hit(E['y1939'], '"1939" slams in')
    for i in range(5):
        place(sfx, blip(10 + i, 520 + 40 * i), E['europe'] - 0.5 + i * 0.15, 0.3)
    hit(E['two'] + 0.02, 'The year ticks to 1940', 0.5)
    hit(E['later'] + 0.1, '... and 1941', 0.8)
    place(sfx, ink_swoosh(2.0, 3), E['two'] + 0.25, 0.7)
    cue(E['two'] + 0.25, 'A rising rush as German control floods across Europe', 'sfx')
    place(sfx, boom(1.8, 55, 28, 4), E['most'], 0.6)
    place(sfx, rewind(0.55, 5), E['sept'] - 0.2, 0.7)
    cue(E['sept'] - 0.2, 'Rewind: the map snaps back to 1939', 'sfx')
    # --- Poland
    hit(E['first'], '"SEPT 1, 1939" slams in')
    place(sfx, rumble(1.7, 6), E['invades'] - 0.1, 0.8)
    for i in range(4):
        place(sfx, whoosh(0.4, 20 + i, 500, 3500), E['invades'] + i * 0.05, 0.35, pan=(i % 3 - 1) * 0.5)
    cue(E['invades'], '"invades": tanks rumble, arrows whoosh across the border', 'sfx')
    for j in range(3):
        place(sfx, cannon(30 + j), E['poland'] + 0.12 + j * 0.16, 0.55 - 0.1 * j, pan=(j - 1) * 0.3)
    cue(E['poland'] + 0.12, '"Poland": shell bursts over Warsaw', 'sfx')
    place(sfx, whoosh(0.6, 7, 300, 3000), E['britain'] - 0.15, 0.6)
    place(sfx, blip(40, 660), E['britain'], 0.5)
    place(sfx, blip(41, 740), E['france'], 0.5)
    cue(E['britain'], 'Whip west; Britain and France light up blue', 'sfx')
    hit(E['war'], '"war": a heavy stamp')
    place(sfx, clang(42), E['war'], 0.35)
    # --- 1940
    hit(E['y1940'], '"1940" slams in')
    place(sfx, whoosh(0.7, 8, 400, 3000), E['y1940'] + 0.12, 0.45)
    place(sfx, rumble(1.5, 9), E['tanks'] - 0.05, 0.8)
    for i in range(3):
        place(sfx, whoosh(0.45, 50 + i, 500, 3500), E['tanks'] + i * 0.1, 0.4, pan=-0.3 * i)
    cue(E['tanks'], '"tanks roll west": rumble and arrows through the Low Countries', 'sfx')
    place(sfx, whoosh(0.5, 10, 300, 2500), E['france2'] - 0.2, 0.45)
    for i in range(14):
        place(sfx, blip(60 + i, 480 + 25 * (i % 5)), E['biggest'] - 0.05 + i * 0.05, 0.22)
    cue(E['biggest'], 'Unit markers pop across France', 'sfx')
    place(sfx, rumble(1.4, 11), E['falls'], 0.7)
    place(sfx, whoosh(0.8, 12, 300, 3000), E['falls'], 0.5)
    place(sfx, boom(2.2, 60, 28, 13), E['six'], 0.9)
    hit(E['six'], '"six weeks": a deep hit as "6 WEEKS" lands', 0.9)
    # --- Britain
    place(sfx, whoosh(0.6, 14, 300, 3000), E['britain2'] - 0.15, 0.5)
    ds = E['so'] - E['britain2'] + 0.2
    place(sfx, siren(ds, 15, 400, 760, 2.6) * env(tt(ds), [(0, 0), (0.3, 1), (ds - 0.4, 1), (ds, 0)]), E['britain2'] - 0.1, 0.16)
    place(sfx, engine(int(ds * SR), 16, 1500, 1.0) * env(tt(ds), [(0, 0), (0.4, 1), (ds - 0.4, 1), (ds, 0)]), E['britain2'] - 0.1, 0.3)
    cue(E['britain2'], 'An air-raid siren and aero engines over the Channel', 'sfx')
    for i in range(3):
        place(sfx, gun(70 + i), E['refuses'] + 0.15 + i * 0.3, 0.4, pan=(i - 1) * 0.5)
    cue(E['refuses'] + 0.15, 'Fighters open fire', 'sfx')
    for j in range(2):
        place(sfx, cannon(80 + j), E['surrender'] + j * 0.14, 0.45)
    cue(E['surrender'], '"surrender": two bombers go down; the rest turn back', 'sfx')
    # --- the East
    hit(E['so'], '"1941" slams in')
    place(sfx, whoosh(1.0, 17, 250, 3500), E['so'] + 0.05, 0.75)
    cue(E['so'] + 0.05, 'Whip-pan east', 'sfx')
    hit(E['over'], '"JUNE 22, 1941"', 0.6)
    tm = E['three']
    while tm < E['troops'] + 0.1:
        place(sfx, tick(int(tm * 100)), tm, 0.4)
        tm += 0.045
    cue(E['three'], 'Rapid ticking as the counter runs up to 3,000,000', 'sfx')
    place(sfx, boom(1.6, 70, 32, 18), E['troops'] + 0.1, 0.7)
    place(sfx, rumble(2.6, 19), E['pour'] - 0.05, 0.9)
    place(sfx, ink_swoosh(2.4, 20), E['pour'], 0.6)
    for j in range(5):
        place(sfx, cannon(90 + j), E['pour'] + 0.1 + j * 0.33, 0.5, pan=(j % 3 - 1) * 0.5)
    cue(E['pour'], '"pour": artillery and armour as three army groups cross the border', 'sfx')
    # --- Moscow
    dw = quiet1 - quiet0 + 0.3
    place(sfx, wind(int(dw * SR), 21, 200, 900) * env(tt(dw), [(0, 0), (0.6, 1), (dw - 0.3, 1), (dw, 0)]), quiet0, 0.55)
    cue(quiet0, 'Winter wind', 'sfx')
    hit(E['december'], '"DECEMBER 1941"', 0.5)
    for i in range(6):
        place(sfx, tick(200 + i), E['less'] + i * (E['twenty'] - E['less']) / 6, 0.4)
    hit(E['twenty'], '"twenty miles": the distance lands', 0.7)
    place(sfx, reverb(np.pad(bell(98.0, 3.5), (0, SR // 2)), 2.2, 22, mix=0.4), E['moscow'], 0.45)
    cue(E['moscow'], '"Moscow": a single low bell', 'sfx')
    # --- Pearl Harbor
    place(sfx, whoosh(1.1, 23, 200, 4000), E['then'] - 0.05, 0.85)
    cue(E['then'], 'A long whip-pan across Asia to the Pacific', 'sfx')
    hit(E['seventh'], '"DEC 7, 1941" slams in')
    place(sfx, blip(90, 600), E['japan'], 0.5)
    de = E['harbor'] - E['attacks'] + 0.2
    place(sfx, engine(int(de * SR), 24, 2100, 1.0) * env(tt(de), [(0, 0), (de - 0.1, 1), (de, 0)]), E['attacks'], 0.5)
    place(sfx, riser(E['harbor'] - E['attacks'], 25), E['attacks'], 0.45)
    cue(E['attacks'], '"attacks": aero engines rise as the planes go in', 'sfx')
    for j in range(5):
        place(sfx, cannon(100 + j), E['harbor'] + j * 0.12, 0.95 - 0.12 * j, pan=(j % 3 - 1) * 0.4)
    place(sfx, boom(3.0, 55, 24, 26), E['harbor'], 1.0)
    cue(E['harbor'], '"Harbor": explosions', 'sfx')
    # --- cliffhanger
    place(sfx, whoosh(0.7, 27, 250, 4000, up=False), E['part'] - 0.08, 0.7)
    place(sfx, boom(2.6, 60, 26, 28), E['part'] + 0.02, 1.0)
    hit(E['part'], '"PART 2" slams in', 1.0)
    hit(E['how'], '"HOW IT ALL FELL APART"', 0.55)
    place(sfx, stone_crack(29, 1.0), E['fell'], 0.9)
    place(sfx, shatter(30, 1.2), E['apart'], 0.6)
    place(sfx, boom(2.4, 50, 24, 31), E['apart'] + 0.1, 0.9)
    cue(E['fell'], '"fell apart": the red map cracks', 'sfx')
    return mus, sfx


def read_wav(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(1)
    return a


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x.T * 32767).astype(np.int16).tobytes())


def loudnorm(src, dst, I=-14.0):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', f'loudnorm=I={I}:TP=-1.5:LRA=11', '-ar', str(SR), dst], check=True)


def main():
    mus, sfx = globals()['build_' + PART]()
    vo = read_wav(os.path.join(PDIR, 'audio', 'narration.wav'))
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
    e = np.convolve(np.abs(vo), np.ones(int(0.12 * SR)) / (0.12 * SR), mode='same')
    duck = 1 - 0.5 * np.clip(e / (e.max() + 1e-9) * 3.0, 0, 1)
    m = mus / (np.abs(mus).max() + 1e-9)
    s = sfx / (np.abs(sfx).max() + 1e-9)
    vrms = np.sqrt(np.mean(vo[np.abs(vo) > 0.02] ** 2)) + 1e-9
    mrms = np.sqrt(np.mean(m ** 2)) + 1e-9
    fade = np.interp(np.arange(N) / SR, [0, DUR - 0.6, DUR], [1, 1, 0])
    # the voice is always on top: music about 20% of its level (and ducked while it speaks), effects punchy but under it
    bed = (m * (0.2 * vrms / mrms) * duck[None, :] + s * 0.42 * (0.6 + 0.4 * duck[None, :])) * fade[None, :]
    mix = bed + np.stack([vo, vo])
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    nv = (m * 0.5 + s * 0.6) * fade[None, :]
    os.makedirs(os.path.join(PDIR, 'build'), exist_ok=True)
    write_wav(os.path.join(PDIR, 'build', 'mix_with_voice_raw.wav'), mix)
    write_wav(os.path.join(PDIR, 'build', 'music_sfx_raw.wav'), nv / max(1.0, np.abs(nv).max() / 0.95))
    loudnorm(os.path.join(PDIR, 'build', 'mix_with_voice_raw.wav'), os.path.join(PDIR, 'audio', 'mix_with_voice.wav'))
    loudnorm(os.path.join(PDIR, 'build', 'music_sfx_raw.wav'), os.path.join(PDIR, 'audio', 'mix_no_voice.wav'))
    L = [f'{T["title"].upper()} - SOUND DESIGN TIMELINE', '', 'Narration: the supplied voiceover (pauses over 0.4 s shortened; nothing else changed).',
         'Music and effects are synthesised in audio.py with numpy: no samples or third-party audio.',
         'Mix: voice on top; music about 20% of the voice level and ducked while it speaks; -14 LUFS, true peak -1.5 dB.',
         '', 'CUES (seconds, layer, description)']
    for tm, what, layer in sorted(CUES):
        L.append(f'  {tm:6.2f}  {layer:6s} {what}')
    open(os.path.join(PDIR, 'sound_design.txt'), 'w').write('\n'.join(L) + '\n')
    print('wrote', os.path.join(PART, 'audio', 'mix_with_voice.wav'))


if __name__ == '__main__':
    main()
