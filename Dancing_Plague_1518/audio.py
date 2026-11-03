"""Music, ambience and sound effects for the Dancing Plague Short - all synthesised with numpy, no samples.

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
# The dance tune: D dorian, 6/8. The same motif returns, slower and alone, at the very end.
# ----------------------------------------------------------------------------------------------
NOTE = {'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.0, 'G#4': 415.3, 'A4': 440.0, 'B4': 493.88,
        'C5': 523.25, 'D5': 587.33, 'E5': 659.26, 'F5': 698.46, 'A3': 220.0, 'D3': 146.83}
TUNE = [('D4', 1), ('F4', 1), ('A4', 1), ('G4', 1), ('F4', 1), ('E4', 1), ('D4', 1), ('E4', 1), ('F4', 1), ('E4', 2), ('C4', 1),
        ('D4', 1), ('F4', 1), ('A4', 1), ('C5', 1), ('B4', 1), ('A4', 1), ('G#4', 1), ('A4', 1), ('F4', 1), ('E4', 1), ('D4', 2)]
EIGHTH = 0.25


def play_tune(buf, t0, t1, inst='pipe', gain=0.3, pan=0.0, detune=0.0, octave=1.0, filt=None):
    t = t0
    i = 0
    while t < t1:
        nm, ln = TUNE[i % len(TUNE)]
        d = ln * EIGHTH
        f = NOTE[nm] * octave
        if inst == 'pipe':
            s = pipe(f * 2, d * 0.95)
        else:
            s = shawm(f, d * 0.95, detune=detune(t) if callable(detune) else detune)
        if filt:
            s = bandpass(s, None, filt)
        place(buf, s, t, gain, pan)
        t += d
        i += 1


def build():
    mus = np.zeros((2, N))
    amb = np.zeros((2, N))
    sfx = np.zeros((2, N))
    t_all = np.arange(N) / SR
    sc = {s['key']: (s['start'], s['end']) for s in T['scenes']}

    # --- 1: the first dancer: a lone pipe tune from the very first frame, her steps on the cobbles
    play_tune(mus, 0.0, 6.2, 'pipe', 0.30, pan=0.1)
    cue(0.0, 'A lone pipe begins the dance tune (D dorian, 6/8) on the first frame', 'music')
    for k in range(9):
        place(sfx, tap(k), 0.18 + k * 0.675 + 0.03 * math.sin(k), 0.35, pan=0.05)
    cue(0.18, 'Her shoes on the cobbles, in time with her steps', 'sfx')
    for k in range(8):
        place(mus, tabor(k), 0.75 + k * 0.75, 0.22)
    cue(0.75, 'A soft tabor drum joins on the beat', 'music')
    place(amb, murmur(int(6.5 * SR), 3, 0.6) * env(tt(6.5), [(0, 0), (1.0, 0.25), (2.6, 0.25), (3.0, 0.55), (6.5, 0.4)]), 0.0, 0.5)
    cue(2.6, 'A murmur rises as the onlookers turn', 'ambience')

    # --- 2: the city
    place(sfx, whoosh(0.9, 1, 400, 2400), 5.55, 0.5, pan=-0.5)
    cue(5.55, 'Whoosh: a timber post sweeps across the lens', 'sfx')
    for k, (tb, f) in enumerate([(6.1, 196.0), (7.35, 146.8), (8.6, 196.0)]):
        place(amb, reverb(np.pad(bell(f, 5.0), (0, SR)), 3.0, k, mix=0.5), tb, 0.33, pan=-0.2 + 0.2 * k)
    cue(6.1, 'Distant cathedral bells (three strikes)', 'ambience')
    m2 = murmur(int(4.6 * SR), 7, 1.2)
    place(amb, m2 * env(tt(4.6), [(0, 0), (0.5, 0.55), (4.0, 0.55), (4.6, 0.2)]), 5.8, 0.55)
    cue(6.0, 'Market crowd murmur, footsteps and a cart on the quay', 'ambience')
    for k in range(14):
        place(amb, tap(40 + k), 6.0 + k * 0.29, 0.12, pan=0.4 * math.sin(k))
    play_tune(mus, 6.2, 10.0, 'pipe', 0.10, pan=0.5, filt=2500)

    # --- 3: it spreads: the tune grows, stamping feet, a crowd
    place(sfx, ink_swoosh(0.9, 2), 9.6, 0.45)
    cue(9.6, 'Wet ink swoosh (ink-spread transition)', 'sfx')
    play_tune(mus, 10.0, 15.6, 'pipe', 0.26, pan=-0.15)
    play_tune(mus, 11.0, 15.6, 'shawm', 0.10, pan=0.25)
    for k in range(8):
        place(mus, tabor(10 + k), 10.0 + k * 0.75, 0.3)
    for k in range(40):
        tm = 11.0 + k * 0.125 * (1 if k < 12 else 1)
        if tm > 15.4:
            break
        if (k % 3) or k > 20:
            place(sfx, stomp(k), tm + 0.02 * math.sin(k * 3), 0.16 + 0.12 * min(1, k / 20), pan=0.5 * math.sin(k * 1.3))
    cue(11.0, 'Stamping feet multiply as more dancers join', 'sfx')
    place(amb, murmur(int(5.8 * SR), 11, 1.6) * env(tt(5.8), [(0, 0.2), (3.0, 0.6), (5.8, 0.7)]), 10.0, 0.6)
    place(mus, drone(73.4, 5.8, 1, 700) * env(tt(5.8), [(0, 0), (2, 0.4), (5.8, 0.6)]), 10.0, 0.22)
    cue(13.6, 'A low drone enters under the crowd', 'music')

    # --- 4: the council chamber
    place(sfx, tear(0.6, 3), 15.2, 0.5, pan=0.3)
    cue(15.2, 'Paper tearing (tear transition)', 'sfx')
    place(mus, drone(73.4, 6.4, 4, 500) * env(tt(6.4), [(0, 0), (0.6, 0.6), (6.0, 0.6), (6.4, 0.3)]), 15.4, 0.34)
    play_tune(mus, 15.5, 21.5, 'shawm', 0.06, pan=0.6, filt=700)
    cue(15.5, 'Inside: a low drone; the tune only muffled through the walls', 'music')
    for k, tm in enumerate([16.2, 19.9]):
        place(sfx, page(0.5, 20 + k), tm, 0.18, pan=-0.3)
    scr = bandpass(noise(int(1.6 * SR), 31), 2500, 8000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 7 * tt(1.6))))
    place(sfx, scr * np.sin(np.pi * tt(1.6) / 1.6), 18.6, 0.06, pan=0.4)
    cue(18.6, 'A quill scratching; papers shuffled', 'sfx')
    crack = np.zeros(int(6 * SR))
    rr = np.random.default_rng(5)
    for i in rr.integers(0, len(crack) - 300, 40):
        crack[i:i + 300] += rr.standard_normal(300) * np.exp(-np.arange(300) / 40)
    place(amb, bandpass(crack, 1500, 8000), 15.5, 0.05)
    place(amb, murmur(int(6 * SR), 13, 0.6), 15.5, 0.10)

    # --- 5: the 'cure': a hired band, too loud, slowly going out of tune
    place(sfx, page(0.7, 4), 21.15, 0.4, pan=0.3)
    cue(21.15, 'Page turn', 'sfx')
    play_tune(mus, 21.5, 30.6, 'shawm', 0.26, pan=-0.2)
    play_tune(mus, 21.5, 30.6, 'shawm', 0.14, pan=0.3, detune=lambda tm: -45 * (tm - 21.5) / 9, octave=0.5)
    place(mus, drone(146.8, 9.2, 7, 2000, buzz=0.35) * env(tt(9.2), [(0, 0), (0.4, 0.5), (9.2, 0.6)]), 21.5, 0.2, pan=0.2)
    place(mus, drone(73.4, 9.2, 8, 600), 21.5, 0.14)
    for k in range(int(9.0 / 0.375)):
        tm = 21.5 + k * 0.375
        place(mus, tabor(50 + k, 120 if k % 2 else 150), tm, 0.30 if k % 2 == 0 else 0.18)
    cue(21.5, 'The hired band: shawms, bagpipe drone and tabor; one shawm drifts out of tune', 'music')
    for k in range(60):
        tm = 22.0 + k * 0.14
        if tm > 30.4:
            break
        place(sfx, stomp(100 + k), tm, 0.14, pan=0.6 * math.sin(k * 0.7))
    place(amb, murmur(int(9 * SR), 17, 1.4), 21.5, 0.4)

    # --- 6: the plan of the city; the ban: the music stops dead
    place(sfx, whoosh(1.0, 5, 2500, 300, up=False), 27.6, 0.45)
    cue(27.6, 'Down-whoosh as the stage shrinks into the city plan', 'sfx')
    cut = 30.62
    mus[:, int(cut * SR):int((cut + 0.05) * SR)] *= np.linspace(1, 0, int(0.05 * SR))[None, :]
    mus[:, int((cut + 0.05) * SR):int(34.5 * SR)] = 0
    tail = reverb(np.pad(shawm(293.66, 0.2), (0, int(2.5 * SR))), 2.5, 9, mix=0.9)
    place(mus, tail, cut, 0.12)
    cue(cut, 'On "banned": the music stops dead, leaving only its echo', 'music')
    place(mus, drone(55.0, 4.0, 9, 300) * env(tt(4.0), [(0, 0), (0.8, 0.7), (4.0, 0.7)]), 30.7, 0.35)
    for k in range(5):
        place(sfx, heartbeat(k), 31.0 + k * 0.85, 0.45)
    cue(31.0, 'Silence, a low drone and a heartbeat', 'music')
    place(sfx, boom(2.2, 70, 34, 1), EV['stamp'][0], 0.55)
    place(sfx, tap(99) * 0.8, EV['stamp'][0], 0.6)
    cue(EV['stamp'][0], 'Ink stamp lands: "WHY WERE THEY DANCING?" (deep hit)', 'sfx')

    # --- 7: the theories
    place(sfx, ink_swoosh(1.0, 6), 34.0, 0.45)
    place(mus, choir([146.8, 174.6, 220.0], 3.4, 1), 34.4, 0.30)
    for k, tm in enumerate([34.6, 35.9]):
        place(mus, reverb(np.pad(bell(587.3, 2.0), (0, SR)), 2.0, 20 + k, mix=0.6), tm, 0.08)
    cue(34.5, 'Saint Vitus: a wordless choir and a small bell', 'music')
    place(sfx, page(0.6, 7), 37.3, 0.4, pan=0.3)
    for k in range(6):
        place(sfx, heartbeat(10 + k), 37.7 + k * 0.48, 0.42)
    wh = np.zeros(int(2.6 * SR))
    for k in range(9):
        i0 = int(k * 0.27 * SR)
        b_ = bandpass(noise(int(0.25 * SR), 60 + k, 'pink'), 1800, 5000) * np.sin(np.pi * tt(0.25) / 0.25)
        wh[i0:i0 + len(b_)] += b_ * (0.4 + 0.6 * k / 9)
    place(sfx, wh, 37.7, 0.18, pan=0.5)
    rise = np.sin(2 * np.pi * np.cumsum(220 + 220 * tt(2.6) / 2.6) / SR) * env(tt(2.6), [(0, 0), (2.4, 0.5), (2.6, 0)])
    place(mus, rise, 37.7, 0.06)
    cue(37.6, 'Mass psychogenic illness: a quickening heartbeat, whispers, a rising tone', 'music')
    place(sfx, page(0.6, 8), 40.0, 0.4, pan=-0.3)
    eerie = np.sin(2 * np.pi * np.cumsum(880 + 60 * np.sin(2 * np.pi * 0.7 * tt(2.8))) / SR) * env(tt(2.8), [(0, 0), (0.6, 0.4), (2.4, 0.4), (2.8, 0)])
    place(mus, eerie, 40.3, 0.05, pan=0.3)
    place(mus, drone(73.4, 2.8, 12, 400), 40.3, 0.25)
    place(amb, wind(int(2.8 * SR), 3, 300, 800), 40.3, 0.12)
    cue(40.3, 'Ergot: a thin, wavering high tone over a drone', 'music')

    # --- 8: the shrine: storm, rain, a slow procession drum, the chapel bell
    place(sfx, boom(2.6, 50, 28, 2) * 0.6, 42.6, 0.4)
    st, en = sc['shrine']
    nW = int((en - st + 0.6) * SR)
    place(amb, wind(nW, 7, 200, 700), st - 0.3, 0.32)
    place(amb, bandpass(noise(nW, 8), 2500, 9000) * 0.5, st - 0.3, 0.12)
    cue(st, 'Storm wind and rain', 'ambience')
    th = boom(3.5, 45, 24, 3) + 0.6 * bandpass(noise(int(3.5 * SR), 9, 'brown'), 30, 900) * np.exp(-tt(3.5) * 1.3)
    place(sfx, th, EV['thunder'][0] + 0.12, 0.6)
    cue(EV['thunder'][0], 'Lightning and a long roll of thunder', 'sfx')
    for k in range(5):
        place(mus, tabor(200 + k, 90), 43.6 + k * 1.4, 0.3)
    place(mus, drone(73.4, 7.2, 13, 500), 43.0, 0.25)
    place(mus, choir([146.8, 220.0], 6.8, 2) * 0.6, 43.2, 0.18)
    for k, tm in enumerate([46.4, 48.4]):
        place(amb, reverb(np.pad(bell(329.6, 4.0), (0, SR)), 3.0, 30 + k, mix=0.6), tm, 0.16, pan=0.4)
    cue(43.6, 'A slow procession drum; the chapel bell tolls from the hill', 'music')

    # --- 9: the empty street, then the parchment and the question
    st, en = sc['end']
    nW = int((DUR - st) * SR)
    place(amb, wind(nW, 11, 180, 500) * env(np.arange(nW) / SR, [(0, 0.5), (4, 0.4), (nW / SR, 0)]), st, 0.25)
    cue(st, 'Match cut: the empty street; only the wind', 'ambience')
    place(amb, reverb(np.pad(bell(196.0, 5.0), (0, SR)), 3.4, 40, mix=0.6), st + 1.0, 0.22)
    cue(st + 1.0, 'One distant bell', 'ambience')
    place(mus, drone(73.4, DUR - st, 14, 400) * env(np.arange(int((DUR - st) * SR)) / SR, [(0, 0), (1.5, 0.5), (DUR - st - 2.0, 0.5), (DUR - st, 0)]), st, 0.28)
    place(sfx, ink_swoosh(1.0, 12), 54.3, 0.3)
    place(sfx, boom(2.6, 60, 30, 4), EV['stamp_end'][0], 0.45)
    cue(EV['stamp_end'][0], 'Stamp lands: "WHAT REALLY HAPPENED IN STRASBOURG?"', 'sfx')
    echo = np.zeros((2, int(4.5 * SR)))
    play_tune(echo, 0.0, 3.0, 'pipe', 0.5)
    e = reverb(echo[0] + echo[1], 3.5, 50, mix=0.7) * env(tt(4.5), [(0, 0.9), (3.0, 0.6), (4.5, 0)])
    place(mus, bandpass(e, 300, 3000), 55.4, 0.12, pan=0.2)
    cue(55.4, 'The dance tune returns, faint and alone, and fades out', 'music')
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
    L = ['THE DANCING PLAGUE OF 1518 - SOUND DESIGN TIMELINE', '=' * 60, '',
         'Everything is synthesised in audio.py with numpy: no samples, no recordings, no third-party audio.',
         'Music: a dance tune in D dorian, 6/8, on a synthetic pipe and shawm with a tabor drum and drones. It builds from a',
         'lone pipe to a full, slightly out-of-tune band, stops dead when the council bans music, and returns faint at the end.',
         'Mix: music and ambience are ducked about 7 dB under the narration; both mixes are normalised to -14 LUFS (true peak -1.5 dB).',
         '', 'NARRATION (Kokoro-82M, voice bm_george)']
    for ln in vo:
        L.append(f'  {ln["start"]:6.2f} - {ln["end"]:6.2f}  {ln["text"]}')
    L += ['', 'CUES (time in seconds, layer, description)']
    for t, what, layer in sorted(CUES):
        L.append(f'  {t:6.2f}  {layer:9s} {what}')
    L += ['', 'SUGGESTED ASSETS FOR A RE-SCORE (licence-free options)',
          '  - Period dance music: public-domain Renaissance dances (e.g. Susato, Danserye 1551) in a CC0 recording,',
          '    or record your own; shawm, recorder, bagpipe and tabor suit the setting.',
          '  - Bells, storm, crowd, footsteps: CC0 field recordings (e.g. Freesound filtered to CC0).']
    with open(os.path.join(ROOT, 'sound_design.txt'), 'w') as fh:
        fh.write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
