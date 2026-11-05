"""Music, ambience and sound effects for the September 11 Short - all synthesised with numpy, no samples.

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


def ping(f=880.0, d=1.2, seed=0):
    """A soft, rounded interface tone for the map markers."""
    t = tt(d)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 4) + 0.3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 7)
    return y * np.minimum(t / 0.004, 1)


def tick(seed=0):
    t = tt(0.06)
    return bandpass(noise(len(t), seed), 2500, 8000) * np.exp(-t * 90)


def soft_hit(d=2.5, seed=0):
    """A low, cushioned cinematic impact (sub swell, no crack)."""
    t = tt(d)
    y = np.sin(2 * np.pi * np.cumsum(48 + 20 * np.exp(-t * 4)) / SR) * np.exp(-t * 1.8)
    y += 0.3 * bandpass(noise(len(t), seed, 'brown'), 30, 200) * np.exp(-t * 3)
    return norm(y) * np.minimum(t / 0.03, 1)


def pad(notes, d, seed=0):
    """A warm string-like pad (detuned saws, low-passed, slow swell)."""
    t = tt(d)
    y = np.zeros_like(t)
    r = np.random.default_rng(seed)
    for f in notes:
        for det in (-0.2, 0.0, 0.18):
            y += 2 * ((t * f * (1 + det / 100) + r.uniform()) % 1.0) - 1
    y = bandpass(y, 60, 1400, order=2)
    return norm(y) * np.minimum(t / 1.5, 1) * np.minimum((d - t) / 1.5, 1)


NOTE.update({'D3': 146.83, 'F3': 174.61, 'A3': 220.0, 'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.0, 'A4': 440.0,
             'Bb3': 233.08, 'G3': 196.0, 'C3': 130.81, 'D2': 73.42, 'Bb2': 116.54, 'F2': 87.31, 'C2': 65.41})


def build():
    mus = np.zeros((2, N))
    amb = np.zeros((2, N))
    sfx = np.zeros((2, N))
    t_all = np.arange(N) / SR

    # --- 1: an ordinary morning
    n1 = int(4.9 * SR)
    place(amb, murmur(n1, 1, 0.6) * 0.5 + bandpass(noise(n1, 2, 'pink'), 80, 700) * 0.5, 0.0, 0.10)
    place(amb, lapping(n1, 3), 0.0, 0.07)
    place(amb, birdsong(n1, 4, 0.5), 0.0, 0.03, pan=0.4)
    for k, tm in enumerate((1.2, 3.1)):
        place(amb, bandpass(engine(int(1.2 * SR), 5 + k, 1800) * np.sin(np.pi * tt(1.2) / 1.2), 200, 900), tm, 0.03, pan=-0.5 + k)
    cue(0.0, 'A quiet city morning across the water: distant traffic, voices, water, a few birds', 'ambience')
    place(mus, pad([146.83, 220.0], 5.0, 1), 0.0, 0.14)
    place(sfx, soft_hit(3.0, 1), EV['date'], 0.32)
    cue(EV['date'], 'A low, cushioned impact as the date appears', 'sfx')

    # --- 2: the timeline
    place(sfx, whoosh(0.7, 6, 300, 1800) * 0.7, 4.05, 0.25)
    cue(4.05, 'A soft air whoosh into the timeline', 'sfx')
    place(mus, drone(73.42, 5.4, 7, 260) * env(tt(5.4), [(0, 0), (1.0, 0.5), (5.4, 0.55)]), 4.2, 0.24)
    for k in range(17):
        place(sfx, tick(20 + k), 4.6 + k * 0.28, 0.05 + 0.02 * (k % 2))
    cue(4.6, 'A quiet clock tick under the timeline', 'sfx')
    for tm in (EV['north'], EV['south']):
        place(sfx, soft_hit(2.4, int(tm * 10)), tm, 0.36)
        place(sfx, ping(440.0, 1.5, int(tm)), tm, 0.05)
    cue(EV['north'], '8:46 and 9:03: a deep, restrained hit for each time; no impact sounds', 'sfx')

    # --- 3: the map
    place(sfx, whoosh(0.8, 8, 2000, 300, up=False) * 0.7, 9.05, 0.22)
    for tm, f in ((EV['nyc'], 659.26), (EV['dc'], 587.33), (EV['pa'], 523.25)):
        place(sfx, ping(f, 1.4, int(tm)), tm, 0.10)
    cue(EV['nyc'], 'A soft tone as each place is marked: New York, the Pentagon, Shanksville', 'sfx')
    place(mus, drone(73.42, 5.8, 9, 300), 9.4, 0.22)
    place(mus, pad([146.83, 174.61, 220.0], 5.8, 2), 9.4, 0.10)
    cue(9.4, 'A low drone and a minor string pad', 'music')

    # --- 4: the aftermath
    n4 = int(7.2 * SR)
    place(amb, wind(n4, 10, 180, 600), 15.0, 0.18)
    place(sfx, bandpass(siren(5.5, 11, 500, 900, 4.0), 300, 1500), 16.4, 0.03, pan=-0.6)
    place(sfx, bandpass(siren(4.5, 12, 450, 850, 3.4), 300, 1400), 18.6, 0.025, pan=0.6)
    cue(16.4, 'Sirens far off, filtered and quiet; wind; dust', 'ambience')
    place(amb, murmur(int(3.8 * SR), 13, 0.8), 18.4, 0.05)
    for k, (tm, nm) in enumerate(((15.5, 'A4'), (16.5, 'F4'), (17.5, 'D4'), (18.7, 'E4'), (19.7, 'C4'), (20.7, 'A3'))):
        place(mus, reverb(np.pad(piano(NOTE[nm], 3.0, 20 + k), (0, SR)), 2.6, 30 + k, mix=0.5), tm, 0.13)
    place(mus, viol(146.83, 6.8, 14) * env(tt(6.8), [(0, 0), (1.5, 0.4), (6.8, 0.3)]), 15.3, 0.10)
    cue(15.5, 'Music: a slow, falling piano line over a low cello-like viol', 'music')

    # --- 5: the memorial, the beams, the mark
    n5 = int((DUR - 21.8) * SR)
    water = bandpass(noise(n5, 15, 'pink'), 300, 6000) * env(np.arange(n5) / SR, [(0, 0), (0.8, 1), (4.0, 1), (4.6, 0.2), (n5 / SR, 0)])
    place(amb, water, 21.8, 0.12)
    cue(22.2, 'The steady fall of water at the memorial pools', 'ambience')
    place(mus, pad([146.83, 220.0, 293.66], 8.0, 3), 22.0, 0.12)
    chords = [(22.4, ('D3', 'A3', 'F4')), (24.0, ('Bb2', 'F3', 'D4')), (25.6, ('F2', 'C3', 'A3')), (26.3, ('D2', 'A3', 'D4'))]
    for tm, nts in chords:
        for j, nm in enumerate(nts):
            place(mus, reverb(np.pad(piano(NOTE[nm], 3.5, 40 + j), (0, SR)), 3.0, 50 + j, mix=0.55), tm + j * 0.05, 0.12)
    cue(22.4, 'Quiet, reflective piano chords', 'music')
    place(sfx, soft_hit(3.0, 16) * 0.8, 26.3, 0.22)
    cue(26.3, '"WE WILL NEVER FORGET.": a soft swell under the final chord', 'music')
    place(mus, reverb(np.pad(ping(587.33, 2.0, 9), (0, SR)), 2.0, 60, mix=0.6), 28.5, 0.06)
    cue(28.5, 'The channel mark: one soft tone; fade to silence', 'sfx')
    fade = env(t_all, [(0, 1), (DUR - 1.2, 1), (DUR, 0)])
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
    L = ['SEPTEMBER 11, 2001: THE DAY THE WORLD STOOD STILL - SOUND DESIGN TIMELINE', '=' * 60, '',
         'Everything is synthesised in audio.py with numpy: no samples, no recordings, no third-party audio.',
         'Music: restrained and respectful: a warm string pad and low drones, a slow falling piano line for the aftermath,',
         'and quiet piano chords in D minor at the memorial. No impact, crash, explosion or collapse sounds are used:',
         'the times are marked by soft, low swells and quiet interface tones.',
         'Mix: music and ambience are ducked about 7 dB under the narration; both mixes are normalised to -14 LUFS (true peak -1.5 dB).',
        '', 'NARRATION (Kokoro-82M, voice bm_george)']
    for ln in vo:
        L.append(f'  {ln["start"]:6.2f} - {ln["end"]:6.2f}  {ln["text"]}')
    L += ['', 'CUES (time in seconds, layer, description)']
    for t, what, layer in sorted(CUES):
        L.append(f'  {t:6.2f}  {layer:9s} {what}')
    L += ['', 'SUGGESTED ASSETS FOR A RE-SCORE (licence-free options)',
          '  - Music: a solo piano or string piece of your own, or a CC0 recording.',
          '  - City ambience, wind and water: CC0 field recordings (e.g. Freesound filtered to CC0).']
    with open(os.path.join(ROOT, 'sound_design.txt'), 'w') as fh:
        fh.write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
