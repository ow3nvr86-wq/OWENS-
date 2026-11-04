"""Music, ambience and sound effects for the Lost Colony of Roanoke Short - all synthesised with numpy, no samples.

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
SR = 48000
T = json.load(open(os.path.join(ROOT, 'scene_timing.json')))
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


def build():
    mus = np.zeros((2, N))
    amb = np.zeros((2, N))
    sfx = np.zeros((2, N))
    t_all = np.arange(N) / SR

    # --- 1 (0-4): the abandoned fort at dusk
    place(mus, drone(73.42, 4.6, 1, 400) * env(tt(4.6), [(0, 0), (1.2, 0.6), (4.6, 0.6)]), 0.0, 0.35)
    place(mus, viol(146.83, 4.2, 2) * env(tt(4.2), [(0, 0), (1.0, 0.6), (4.2, 0.5)]), 0.2, 0.18, pan=-0.2)
    cue(0.0, 'A low drone and a single bowed viol note swell out of silence', 'music')
    place(amb, wind(int(4.8 * SR), 1, 180, 600), 0.0, 0.3)
    place(amb, bandpass(noise(int(4.8 * SR), 2, 'pink'), 2000, 6000) * 0.15, 0.0, 0.2)
    cue(0.0, 'Wind in the pines; moss and grass rustle', 'ambience')
    place(sfx, caw(3), EV['crow'], 0.35, pan=-0.4)
    place(sfx, whoosh(0.5, 4, 900, 2500) * 0.4, EV['crow'] + 0.05, 0.15, pan=-0.2)
    cue(EV['crow'], 'A crow caws and flaps off the palisade', 'sfx')
    place(sfx, boom(2.4, 60, 30, 1) * 0.8, 3.72, 0.4)
    cue(3.72, 'A deep, soft hit as the camera reaches the word', 'sfx')

    # --- 2 (4-11): the ships, the landing
    place(sfx, ink_swoosh(0.8, 2), 3.6, 0.4)
    cue(3.6, 'Wet ink swoosh (ink transition)', 'sfx')
    place(amb, surf(int(7.6 * SR), 5, 0.4), 3.8, 0.32)
    place(amb, wind(int(3.8 * SR), 6, 400, 1400), 3.8, 0.22)
    cue(4.0, 'Open sea: waves, wind in the sails', 'ambience')
    for k, tm in enumerate((4.6, 6.0)):
        place(sfx, creak(1.3, 10 + k, 80 + 20 * k), tm, 0.18, pan=-0.3)
    cue(4.6, 'The hull and rigging creak', 'sfx')
    for k, tm in enumerate((4.9, 6.6, 8.2, 9.9)):
        place(amb, gull(20 + k), tm, 0.12, pan=0.6 * math.sin(k * 2))
    cue(4.9, 'Gulls', 'ambience')
    play_line(mus, AIR, 4.4, 17.6, 'recorder', 0.14, pan=0.15)
    play_line(mus, BASS, 4.4, 17.6, 'lute', 0.16, pan=-0.2, octave=1.0)
    place(mus, viol(73.42, 13.5, 3) * env(tt(13.5), [(0, 0), (1.5, 0.5), (12, 0.5), (13.5, 0)]), 4.2, 0.12)
    cue(4.4, 'The theme: an original slow air in D minor on recorder, lute and viol', 'music')
    place(sfx, steps(10, 0.5, 30, 'sand'), 7.6, 0.18)
    cue(7.6, 'Footsteps in the sand; the surf on the beach', 'sfx')

    # --- 3 (11-18): building; supplies short; the arrow
    place(sfx, whoosh(0.9, 7, 400, 2400), 10.55, 0.4, pan=-0.5)
    cue(10.55, 'Whoosh: a timber post sweeps across the lens', 'sfx')
    for k in range(9):
        place(sfx, knock(40 + k, 170 + 25 * (k % 3)), 11.15 + k * 0.32 + 0.05 * math.sin(k), 0.22, pan=-0.3 + 0.2 * (k % 4))
    cue(11.15, 'Mallets on timber', 'sfx')
    place(amb, fire(int(3.0 * SR), 7), 11.0, 0.08)
    for k, tm in enumerate((11.4, 12.6)):
        place(amb, bell(2600 + 300 * k, 0.4) * 0.3, tm, 0.03, pan=0.5)
    place(mus, drone(73.42, 4.6, 5, 300) * env(tt(4.6), [(0, 0), (1.0, 0.6), (4.6, 0.6)]), 13.6, 0.3)
    cue(13.75, 'Food short: the air thins to the drone and a single line', 'music')
    place(amb, wind(int(4.4 * SR), 8, 200, 700), 13.6, 0.25)
    place(sfx, arrow(5), EV['arrow'] - 0.32, 0.45, pan=0.4)
    cue(EV['arrow'], 'An arrow whistles in and strikes the post', 'sfx')
    place(mus, boom(2.0, 55, 30, 6) * 0.5, EV['arrow'], 0.3)

    # --- 4 (18-25): White departs
    place(sfx, page(0.7, 4), 17.6, 0.38, pan=0.3)
    cue(17.6, 'Page turn', 'sfx')
    place(amb, surf(int(7.4 * SR), 9, 0.3), 17.8, 0.22)
    play_line(mus, AIR, 18.2, 25.0, 'viol', 0.11, pan=0.1, octave=0.5, start=12)
    play_line(mus, BASS, 18.2, 25.0, 'lute', 0.15, pan=-0.2, start=6)
    cue(18.2, 'The air passes to the viol, lower and slower', 'music')
    place(mus, choir([146.83, 174.61, 220.0], 4.2, 4) * 0.7, 21.2, 0.14)
    cue(21.6, 'A soft choir as the ship sails out over the horizon', 'music')
    place(sfx, creak(1.4, 14, 70), 21.8, 0.08, pan=0.5)

    # --- 5 (25-32): the Armada; the seasons
    place(sfx, tear(0.6, 3), 24.62, 0.5, pan=0.3)
    cue(24.62, 'Paper tearing (tear transition)', 'sfx')
    for k in range(4):
        tm = 25.0 + (k + 0.2) / 0.9
        if tm < 28.7:
            place(sfx, cannon(60 + k), tm, 0.36, pan=-0.4 + 0.25 * k)
    cue(25.2, 'Cannon fire: broadsides at the Armada', 'sfx')
    place(amb, fire(int(4.0 * SR), 11), 25.0, 0.12)
    for k in range(9):
        place(mus, tabor(70 + k, 95), 25.1 + k * 0.42, 0.26)
    place(mus, drone(73.42, 4.0, 9, 700, buzz=0.3), 25.0, 0.22)
    cue(25.1, 'A war drum and a buzzing drone', 'music')
    place(sfx, ink_swoosh(0.7, 8), 28.45, 0.35)
    for k, (tm, f) in enumerate(((28.95, 98.0), (29.85, 87.31), (30.85, 73.42))):
        place(sfx, boom(1.6, 70, 34, 10 + k) * 0.5, tm, 0.3)
        place(mus, viol(f * 2, 1.0, 20 + k), tm, 0.12)
    cue(28.95, 'A soft hit on each new year: 1588, 1589, 1590', 'music')
    place(amb, wind(int(1.2 * SR), 12, 300, 1200) * 0.8, 28.8, 0.2)
    place(amb, wind(int(1.2 * SR), 13, 500, 1800), 29.7, 0.3)
    cue(29.7, 'Winter wind', 'ambience')
    place(amb, rain(int(1.2 * SR), 14), 30.7, 0.25)
    th = boom(2.6, 45, 24, 3) + 0.6 * bandpass(noise(int(2.6 * SR), 9, 'brown'), 30, 900) * np.exp(-tt(2.6) * 1.3)
    place(sfx, th, EV['lightning'] + 0.1, 0.5)
    cue(EV['lightning'], 'Storm: rain, lightning and thunder', 'sfx')
    place(amb, bell(3100, 0.5) * 0.2, 31.55, 0.03, pan=0.5)
    place(amb, bandpass(noise(int(0.8 * SR), 15, 'pink'), 2000, 7000) * 0.3, 31.4, 0.15)
    cue(31.4, 'Summer 1590: insects in the long grass, and nobody', 'ambience')

    # --- 6 (32-40): night; the trumpet; the songs; no answer; dawn in the forest
    nN = int(6.6 * SR)
    place(amb, crickets(nN, 21) * env(np.arange(nN) / SR, [(0, 0), (0.6, 0.3), (6.6, 0.3)]), 31.7, 0.08)
    place(amb, frogs(nN, 22), 31.7, 0.06, pan=-0.3)
    place(amb, lapping(nN, 23), 31.7, 0.16)
    cue(32.0, 'Night: crickets, frogs, water lapping', 'ambience')
    for k in range(10):
        tm = 32.3 + (k + 0.3) / 0.55
        if tm < 38.2:
            place(sfx, splash(80 + k), tm, 0.12, pan=0.2)
            place(sfx, creak(0.4, 90 + k, 140), tm - 0.3, 0.05)
    cue(32.3, 'Oars dip and creak in the rowlocks', 'sfx')
    place(mus, drone(73.42, 4.4, 15, 300) * env(tt(4.4), [(0, 0), (1.0, 0.45), (4.4, 0.45)]), 32.0, 0.24)
    tr = np.zeros(int(1.4 * SR))
    for (st_, d_, f_) in ((0.0, 0.25, 293.66), (0.27, 0.25, 440.0), (0.54, 0.25, 587.33), (0.82, 0.55, 587.33)):
        s_ = trumpet(f_, d_)
        i0 = int(st_ * SR)
        tr[i0:i0 + len(s_)] += s_[:len(tr) - i0]
    place(sfx, reverb(np.pad(tr, (0, int(2.0 * SR))), 3.0, 31, mix=0.55), EV['trumpet'], 0.2, pan=-0.1)
    cue(EV['trumpet'], 'A trumpet call carries across the water (D - A - D)', 'sfx')
    sing = choir([146.83, 220.0], 1.2, 9) * 0.6 + choir([174.61], 1.2, 10) * 0.4
    place(sfx, reverb(np.pad(sing, (0, SR)), 2.6, 32, mix=0.5), 37.15, 0.16)
    cue(37.15, 'Men singing an English tune into the dark', 'sfx')
    c0, c1 = int(38.3 * SR), int(38.3 * SR) + int(0.05 * SR)
    mus[:, c0:c1] *= np.linspace(1, 0, c1 - c0)[None, :]
    mus[:, c1:int(40.0 * SR)] = 0
    cue(38.3, '"No one answered": the music stops; only the night', 'music')
    place(amb, wind(int(2.2 * SR), 24, 200, 600) * 0.7, 38.0, 0.22)
    place(sfx, steps(5, 0.55, 40, 'leaves'), 38.3, 0.2)
    place(amb, bandpass(caw(41), 400, 2000) * 0.4, 39.1, 0.06, pan=0.7)
    cue(38.3, 'Dawn: footsteps in dead leaves, a far-off crow', 'sfx')

    # --- 7 (40-48): the empty fort; the word
    place(sfx, whoosh(0.9, 9, 400, 2400), 39.55, 0.4, pan=-0.5)
    place(amb, wind(int(8.4 * SR), 25, 180, 520), 39.8, 0.28)
    place(mus, drone(73.42, 8.2, 16, 350) * env(tt(8.2), [(0, 0), (1.5, 0.5), (8.2, 0.6)]), 40.0, 0.3)
    place(sfx, creak(1.6, 26, 60), 40.6, 0.12, pan=0.4)
    cue(40.0, 'The empty enclosure: wind, a creaking timber, a low drone', 'ambience')
    for k in range(4):
        place(sfx, heartbeat(30 + k), 42.6 + k * 0.82, 0.32)
    cue(42.6, 'A slow heartbeat as the camera closes on the post', 'sfx')
    place(sfx, boom(3.0, 58, 28, 12), 43.56, 0.45)
    place(mus, viol(146.83, 3.6, 33) * 0.7 + viol(155.56, 3.6, 34) * 0.4, 43.6, 0.1)
    cue(43.56, 'CROATOAN: a deep hit and a dissonant viol cluster', 'music')
    shim = np.sin(2 * np.pi * 1318.5 * tt(2.0)) * env(tt(2.0), [(0, 0), (0.4, 0.5), (1.6, 0.3), (2.0, 0)])
    place(mus, reverb(np.pad(shim, (0, SR)), 2.0, 35, mix=0.6), EV['ghost_cross'], 0.04, pan=0.2)
    cue(EV['ghost_cross'], 'A thin shimmer as the missing cross is sketched in', 'music')

    # --- 8 (48-55): the theories on the map
    place(sfx, whoosh(1.0, 11, 2500, 300, up=False), 47.55, 0.4)
    cue(47.55, 'Down-whoosh as the post shrinks into the map', 'sfx')
    play_line(mus, AIR, 48.3, 55.0, 'lute', 0.12, pan=0.1, octave=1.0, start=0)
    place(mus, drone(73.42, 6.8, 17, 300), 48.2, 0.18)
    cue(48.3, 'The theme returns on a lute, questioning', 'music')
    for tm in (51.0, 52.2):
        place(sfx, scratch(0.9, int(tm * 10)), tm, 0.07, pan=0.3)
    cue(51.0, 'A quill scratches as each route is drawn', 'sfx')
    place(sfx, boom(2.2, 70, 34, 13), EV['stamp'], 0.5)
    place(sfx, tap(99) * 0.8, EV['stamp'], 0.5)
    cue(EV['stamp'], 'Ink stamp lands: "NOT PROVEN"', 'sfx')

    # --- 9 (55-59.8): back to the fort; the fade; the question
    place(sfx, ink_swoosh(0.9, 12), 54.55, 0.35)
    nW = int((DUR - 54.8) * SR)
    place(amb, wind(nW, 27, 160, 480) * env(np.arange(nW) / SR, [(0, 0.5), (3, 0.45), (nW / SR, 0)]), 54.8, 0.3)
    place(sfx, caw(44) * 0.7, 56.2, 0.1, pan=0.6)
    cue(55.0, 'The fort again: wind and a distant crow', 'ambience')
    nD = int((DUR - 55.0) * SR)
    place(mus, drone(73.42, DUR - 55.0, 18, 300) * env(np.arange(nD) / SR, [(0, 0), (1.2, 0.5), (DUR - 57.0, 0.5), (DUR - 55.0, 0)]), 55.0, 0.28)
    echo = np.zeros((2, int(4.4 * SR)))
    play_line(echo, AIR, 0.0, 2.6, 'recorder', 0.5)
    e = reverb(echo[0] + echo[1], 3.5, 50, mix=0.7) * env(tt(4.4), [(0, 0.9), (2.6, 0.6), (4.4, 0)])
    place(mus, bandpass(e, 300, 3000), 55.3, 0.12, pan=0.2)
    cue(55.3, 'The theme, alone on the recorder, fading', 'music')
    place(sfx, boom(3.0, 50, 26, 14) * 0.8, 57.3, 0.4)
    cue(57.3, '"WHAT REALLY HAPPENED TO ROANOKE?" fades up on black over a low hit', 'sfx')
    fade = env(t_all, [(0, 1), (DUR - 0.5, 1), (DUR, 0)])
    out = (mus * 0.9 + amb * 0.8 + sfx * 0.9) * fade[None, :]
    return out, mus, amb, sfx


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
    out, mus, amb, sfx = build()
    vo = read_wav(os.path.join(ROOT, 'audio', 'narration.wav'))
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
    # duck the music and ambience under the voice
    e = np.abs(vo)
    k = int(0.12 * SR)
    e = np.convolve(e, np.ones(k) / k, mode='same')
    e = np.clip(e / (e.max() + 1e-9) * 3.0, 0, 1)
    duck = 1 - 0.55 * e
    bed = (mus * 0.9 + amb * 0.8) * duck[None, :] + sfx * 0.9
    fade = np.interp(np.arange(N) / SR, [0, DUR - 0.5, DUR], [1, 1, 0])
    bed *= fade[None, :]
    peak = np.abs(out).max() + 1e-9
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    write_wav(os.path.join(ROOT, 'build', 'music_sfx_raw.wav'), out / peak * 0.8)
    voice_mix = bed / peak * 0.42 + np.stack([vo, vo]) * 0.85
    write_wav(os.path.join(ROOT, 'build', 'mix_with_voice_raw.wav'), voice_mix / max(1.0, np.abs(voice_mix).max() / 0.95))
    loudnorm(os.path.join(ROOT, 'build', 'mix_with_voice_raw.wav'), os.path.join(ROOT, 'audio', 'mix_with_voice.wav'))
    loudnorm(os.path.join(ROOT, 'build', 'music_sfx_raw.wav'), os.path.join(ROOT, 'audio', 'mix_no_voice.wav'))
    write_sound_design()
    print('wrote audio/mix_with_voice.wav, audio/mix_no_voice.wav, sound_design.txt')


def write_sound_design():
    vo = json.load(open(os.path.join(ROOT, 'build', 'vo_timing.json')))['lines']
    L = ['THE LOST COLONY OF ROANOKE - SOUND DESIGN TIMELINE', '=' * 60, '',
         'Everything is synthesised in audio.py with numpy: no samples, no recordings, no third-party audio.',
         'Music: an original slow air in D minor (3/4) on a synthetic recorder, lute and viol, over drones. It is hopeful at',
         'the landing, thins as food runs short, turns martial for the Armada, stops dead when no one answers, and',
         'returns alone and fading at the end.',
         'Mix: music and ambience are ducked about 7 dB under the narration; both mixes are normalised to -14 LUFS (true peak -1.5 dB).',
        '', 'NARRATION (Kokoro-82M, voice bm_george)']
    for ln in vo:
        L.append(f'  {ln["start"]:6.2f} - {ln["end"]:6.2f}  {ln["text"]}')
    L += ['', 'CUES (time in seconds, layer, description)']
    for t, what, layer in sorted(CUES):
        L.append(f'  {t:6.2f}  {layer:9s} {what}')
    L += ['', 'SUGGESTED ASSETS FOR A RE-SCORE (licence-free options)',
          '  - Period music: public-domain Elizabethan consort or lute pieces (e.g. Dowland, Byrd) in a CC0 recording,',
          '    or record your own; recorder, lute and viol suit the setting.',
          '  - Surf, gulls, crows, crickets, storm and footsteps: CC0 field recordings (e.g. Freesound filtered to CC0).']
    with open(os.path.join(ROOT, 'sound_design.txt'), 'w') as fh:
        fh.write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
