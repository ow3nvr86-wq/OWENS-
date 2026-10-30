"""Code-generated score, sound effects and final mix.

Everything here is synthesised with numpy/scipy — no samples or stock audio:
  * score: drones, pads, an ostinato, taiko-style drums, risers and impacts (D minor)
  * sound effects: rushing flood, rivet pings (timed to the animation's rivet pops),
    metal groans, drips, brush strokes, gulls, wind, ice crackle, whooshes
  * mix: voiceover on top, music ducked under the voice, soft limiting

Inputs : audio/vo/voiceover.wav, build/timeline.json, build/events.json
Outputs: audio/music/score.wav, audio/sfx/sfx.wav, audio/mix.wav, audio/timing_sheet.md
Run    : python scripts/audio.py
"""
import json
import os
import wave

import numpy as np
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
RNG = np.random.default_rng(1919)

TL = json.load(open(os.path.join(ROOT, 'build', 'timeline.json')))
EV = json.load(open(os.path.join(ROOT, 'build', 'events.json')))
SHOT = {s['name']: s for s in EV['shots']}
END = SHOT['end']['t1']
N = int(END * SR) + SR
LINE = {l['id']: l for l in TL['lines']}

CUES = []   # (time, track, description) for the timing sheet


def cue(t, track, text):
    CUES.append((round(t, 2), track, text))


# ---------------------------------------------------------------------------
# DSP helpers
# ---------------------------------------------------------------------------
def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def sos(kind, f, order=2):
    if kind == 'bp':
        return signal.butter(order, [f[0] / (SR / 2), f[1] / (SR / 2)], 'bandpass', output='sos')
    return signal.butter(order, f / (SR / 2), kind, output='sos')


def filt(x, kind, f, order=2):
    return signal.sosfilt(sos(kind, f, order), x)


def white(dur):
    return RNG.standard_normal(int(dur * SR))


def brown(dur):
    b = np.cumsum(white(dur))
    b = filt(b, 'high', 20.0)
    return b / (np.max(np.abs(b)) + 1e-9)


def pink(dur):
    w = white(dur)
    b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
    p = signal.lfilter(b, a, w)
    return p / (np.max(np.abs(p)) + 1e-9)


def env_adsr(n, a, d, s, r, sustain=0.7):
    t = np.arange(n) / SR
    dur = n / SR
    e = np.ones(n) * sustain
    e = np.where(t < a, t / max(a, 1e-4), e)
    e = np.where((t >= a) & (t < a + d), 1 - (1 - sustain) * (t - a) / max(d, 1e-4), e)
    e = np.where(t > dur - r, e * np.clip((dur - t) / max(r, 1e-4), 0, 1), e)
    return e


def expdecay(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


def saw(f, dur, detune=0.0):
    t = tvec(dur)
    ph = (f * (1 + detune)) * t + RNG.random()
    return 2 * (ph % 1.0) - 1


def place(track, x, t, gain=1.0, pan=0.0):
    """Add mono or stereo x into stereo track at time t."""
    i = int(t * SR)
    if i >= track.shape[0]:
        return
    if x.ndim == 1:
        l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        x = np.stack([x * l, x * r], 1)
    n = min(len(x), track.shape[0] - i)
    track[i:i + n] += x[:n] * gain


def reverb(x, seconds=2.2, mix=0.25, damp=4000):
    n = int(seconds * SR)
    ir_l = white(seconds) * expdecay(n, seconds / 5)
    ir_r = white(seconds) * expdecay(n, seconds / 5)
    ir_l, ir_r = filt(ir_l, 'low', damp), filt(ir_r, 'low', damp)
    ir_l /= np.sqrt(np.sum(ir_l ** 2)); ir_r /= np.sqrt(np.sum(ir_r ** 2))
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    wl = signal.fftconvolve(x[:, 0], ir_l)[:len(x)]
    wr = signal.fftconvolve(x[:, 1], ir_r)[:len(x)]
    return x * (1 - mix) + np.stack([wl, wr], 1) * mix


def sweep_bp(x, f0, f1, q=2.0, block=1024):
    """Band-pass with a centre frequency gliding from f0 to f1 (block-wise)."""
    out = np.zeros_like(x)
    nb = int(np.ceil(len(x) / block))
    zi = None
    for k in range(nb):
        u = k / max(nb - 1, 1)
        fc = f0 * (f1 / f0) ** u
        bw = fc / q
        lo, hi = max(fc - bw / 2, 20), min(fc + bw / 2, SR / 2 - 100)
        sos_ = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], 'bandpass', output='sos')
        if zi is None:
            zi = signal.sosfilt_zi(sos_) * 0
        seg = x[k * block:(k + 1) * block]
        out[k * block:k * block + len(seg)], zi = signal.sosfilt(sos_, seg, zi=zi)
    return out


NOTE = {'D1': 36.71, 'A1': 55.0, 'Bb1': 58.27, 'C2': 65.41, 'D2': 73.42, 'E2': 82.41, 'F2': 87.31, 'G2': 98.0,
        'A2': 110.0, 'Bb2': 116.54, 'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.0,
        'A3': 220.0, 'Bb3': 233.08, 'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'A4': 440.0,
        'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'A5': 880.0}


# ---------------------------------------------------------------------------
# Instruments
# ---------------------------------------------------------------------------
def pad(notes, dur, bright=1400, attack=1.2, release=1.5):
    x = np.zeros(int(dur * SR))
    for nm in notes:
        f = NOTE[nm]
        for dt in (-0.004, 0.0, 0.005):
            x += saw(f, dur, dt)
    x = filt(x, 'low', bright, 2)
    x *= env_adsr(len(x), attack, 0.5, 0.85, release)
    return x / (len(notes) * 3)


def pluck(f, dur=0.35, cutoff=1600):
    x = saw(f, dur) + 0.5 * saw(f * 2.0, dur, 0.002)
    x = filt(x, 'low', cutoff)
    return x * expdecay(len(x), dur / 3) * env_adsr(len(x), 0.004, 0.05, 0.8, 0.05)


def boom(dur=3.0, f0=90, f1=28, gain=1.0):
    t = tvec(dur)
    f = f1 + (f0 - f1) * np.exp(-t / 0.18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * expdecay(len(t), 0.9)
    crack = filt(white(dur), 'low', 900) * expdecay(len(t), 0.12)
    sub = np.sin(2 * np.pi * 32 * t) * expdecay(len(t), 1.4) * 0.6
    x = body + 0.7 * crack + sub
    return np.tanh(x * 1.6) * gain


def taiko(f=70, dur=0.7, gain=1.0):
    t = tvec(dur)
    ff = f * (1 + 0.9 * np.exp(-t / 0.03))
    x = np.sin(2 * np.pi * np.cumsum(ff) / SR) * expdecay(len(t), 0.22)
    x += filt(white(dur), 'bp', (200, 1800)) * expdecay(len(t), 0.02) * 0.6
    return np.tanh(1.4 * x) * gain


def heartbeat():
    a = taiko(48, 0.35, 0.8)
    out = np.zeros(int(0.6 * SR))
    out[:len(a)] += a
    b = taiko(44, 0.35, 0.6)
    i = int(0.22 * SR)
    out[i:i + len(b)] += b[:len(out) - i]
    return filt(out, 'low', 300)


def riser(dur, f0=200, f1=5000, gain=1.0):
    n = sweep_bp(white(dur), f0, f1, q=1.5)
    t = tvec(dur)
    tone = np.sin(2 * np.pi * np.cumsum(110 * (2 ** (2.5 * t / dur))) / SR) * 0.35
    e = (t / dur) ** 2.2
    return (n * 0.8 + tone) * e * gain


def bell(f, dur=3.0):
    t = tvec(dur)
    x = np.zeros_like(t)
    for ratio, amp, tau in ((1, 1, 1.4), (2.76, 0.5, 0.7), (5.4, 0.25, 0.35), (8.93, 0.12, 0.2)):
        x += amp * np.sin(2 * np.pi * f * ratio * t) * expdecay(len(t), tau)
    return x * env_adsr(len(t), 0.002, 0.1, 1.0, 0.3) * 0.4


# ---------------------------------------------------------------------------
# Sound effects
# ---------------------------------------------------------------------------
def rush(dur, intensity=1.0):
    """Rushing, gurgling flood."""
    b = brown(dur)
    low = filt(b, 'low', 380) * 1.2
    mid = filt(white(dur), 'bp', (250, 1600)) * 0.22
    t = tvec(dur)
    lfo = 0.6 + 0.4 * np.abs(filt(white(dur), 'low', 6.0)) * 6
    gurgle = np.zeros_like(t)
    for _ in range(int(dur * 10)):
        c = RNG.uniform(0, dur - 0.2)
        g = filt(white(0.2), 'bp', (RNG.uniform(150, 300), RNG.uniform(500, 900))) * np.hanning(int(0.2 * SR))
        i = int(c * SR)
        gurgle[i:i + len(g)] += g * 0.5
    return (low + mid * np.clip(lfo, 0, 2) + gurgle) * intensity


def ping(f=2400):
    dur = 0.6
    t = tvec(dur)
    x = np.zeros_like(t)
    for ratio, amp, tau in ((1.0, 1.0, 0.18), (1.47, 0.6, 0.12), (2.09, 0.4, 0.08), (2.98, 0.25, 0.05)):
        x += amp * np.sin(2 * np.pi * f * ratio * t + RNG.random() * 6) * expdecay(len(t), tau)
    click = filt(white(dur), 'high', 3000) * expdecay(len(t), 0.004) * 1.5
    bang = filt(white(dur), 'low', 500) * expdecay(len(t), 0.03) * 0.8
    return (x * 0.5 + click + bang) * 0.9


def ricochet():
    dur = 0.45
    t = tvec(dur)
    f = 3200 * np.exp(-t / 0.25) + 500
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * expdecay(len(t), 0.12) * 0.25
    return x


def groan(dur, f0=55, f1=80):
    t = tvec(dur)
    wander = np.cumsum(RNG.standard_normal(len(t))) / SR
    wander = filt(wander, 'low', 2.0)
    f = f0 + (f1 - f0) * t / dur + 12 * wander / (np.max(np.abs(wander)) + 1e-9)
    car = np.sin(2 * np.pi * np.cumsum(f) / SR + 3.0 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR))
    grit = filt(white(dur), 'bp', (300, 1400)) * 0.15
    x = (car + grit) * env_adsr(len(t), dur * 0.3, 0.1, 0.9, dur * 0.4)
    return filt(x, 'low', 2200) * 0.6


def drip():
    dur = 0.12
    t = tvec(dur)
    f = 500 + 1300 * (t / dur) ** 0.6
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * expdecay(len(t), 0.025)
    return x * 0.5


def swish(dur=0.7):
    x = sweep_bp(white(dur), 600, 2400, q=1.2) * np.hanning(int(dur * SR))
    return x * 0.6


def whoosh(dur=0.6, up=True):
    f0, f1 = (300, 4000) if up else (4000, 300)
    x = sweep_bp(white(dur), f0, f1, q=1.0)
    e = np.hanning(int(dur * SR)) ** (0.8 if up else 1.4)
    return x * e


def gull():
    dur = 0.5
    t = tvec(dur)
    f = 1500 + 700 * np.sin(np.pi * t / dur) - 600 * t / dur
    x = np.sin(2 * np.pi * np.cumsum(f) / SR + 2.5 * np.sin(2 * np.pi * 9 * t))
    return x * np.hanning(len(t)) ** 2 * 0.12


def wind(dur, gain=1.0):
    p = pink(dur)
    x = filt(p, 'bp', (200, 1800))
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * tvec(dur) / 3.7 + 1)
    return x * lfo * gain


def crackle(dur, rate=25):
    x = np.zeros(int(dur * SR))
    for _ in range(int(dur * rate)):
        i = int(RNG.uniform(0, dur - 0.02) * SR)
        c = filt(white(0.01), 'high', 4000) * expdecay(int(0.01 * SR), 0.0015) * RNG.uniform(0.2, 1.0)
        x[i:i + len(c)] += c
    return x * 0.5


def wood_crack():
    dur = 1.2
    t = tvec(dur)
    x = filt(white(dur), 'bp', (180, 2500)) * expdecay(len(t), 0.08)
    for k in range(5):
        i = int(RNG.uniform(0.02, 0.5) * SR)
        b = filt(white(0.08), 'bp', (400, 3000)) * expdecay(int(0.08 * SR), 0.01)
        x[i:i + len(b)] += b * 0.8
    return x * 0.9


def tick():
    dur = 0.05
    return filt(white(dur), 'bp', (2000, 7000)) * expdecay(int(dur * SR), 0.004) * 0.35


def cicadas(dur):
    t = tvec(dur)
    x = filt(white(dur), 'bp', (4500, 7000)) * (0.5 + 0.5 * np.sin(2 * np.pi * 34 * t)) ** 2
    return x * (0.6 + 0.4 * np.sin(2 * np.pi * t / 2.3)) * 0.12


# ---------------------------------------------------------------------------
# Build the score
# ---------------------------------------------------------------------------
def build_music():
    m = np.zeros((N, 2))
    S = SHOT
    # HOOK: impact, drone and heartbeat under a rising whine
    place(m, boom(3.5, 80, 26, 0.9), 0.0)
    cue(0.0, 'MUSIC', 'Cold open: sub impact + low D drone')
    place(m, pad(['D1', 'D2', 'A2'], S['hook']['t1'] + 0.6, bright=500, attack=0.3, release=0.4), 0.0, 0.5)
    for k, tt in enumerate(np.arange(0.5, S['hook']['t1'] - 0.2, 0.85)):
        place(m, heartbeat(), tt, 0.7)
    place(m, riser(S['hook']['t1'] - 1.2, 300, 3000, 0.25), 1.0)
    # SETUP + STORY: ostinato and pad in D minor
    t0, t1 = S['aerial']['t0'], S['rivets']['t0']
    cue(t0, 'MUSIC', 'Main theme in: D-minor ostinato (100 BPM) + pad, low intensity')
    place(m, boom(2.0, 70, 35, 0.45), t0)
    beat = 0.6
    pattern = ['D2', 'D2', 'F2', 'D2', 'A2', 'D2', 'C3', 'A2']
    chords = [['D3', 'F3', 'A3'], ['Bb2', 'D3', 'F3'], ['F2', 'A2', 'C3'], ['C3', 'E3', 'G3']]
    k = 0
    t = t0
    while t < t1:
        u = (t - t0) / (t1 - t0)
        place(m, pluck(NOTE[pattern[k % 8]], 0.3, 900 + 1800 * u), t, 0.32 + 0.25 * u, pan=0.25 * np.sin(k))
        t += beat / 2
        k += 1
    c = 0
    t = t0
    while t < t1:
        place(m, pad(chords[c % 4], beat * 4 + 1.2, bright=900 + 800 * ((t - t0) / (t1 - t0))), t, 0.55)
        t += beat * 4
        c += 1
    # clock ticks through the temperature rise and the rivet build-up, accelerating
    t = S['thermo']['t0']
    gap = 0.6
    cue(t, 'MUSIC', 'Clock ticks begin, accelerating toward the collapse')
    while t < S['burst']['t0'] - 0.25:
        place(m, tick(), t, 0.9, pan=0.3)
        t += gap
        if t > S['rivets']['t0']:
            gap = max(0.12, gap * 0.93)
    # RIVETS: riser into a hard stop, then silence before the boom
    rs = S['rivets']['t0']
    place(m, riser(S['burst']['t0'] - rs - 0.1, 150, 6000, 0.55), rs)
    for k, tt in enumerate(np.arange(rs, S['burst']['t0'] - 0.25, 0.3)):
        place(m, pluck(NOTE['D2'] * (1 if k % 2 else 2), 0.22, 2600), tt, 0.4)
    cue(S['burst']['t0'] - 0.12, 'MUSIC', 'Hard stop: 0.12 s of silence before the impact (dramatic pause)')
    # BURST
    bt = S['burst']['t0']
    place(m, boom(4.0, 110, 24, 1.15), bt)
    place(m, pad(['D1', 'A1', 'D2', 'F2'], 2.2, bright=700, attack=0.02, release=1.2), bt, 0.9)
    cue(bt, 'MUSIC', 'BOOM: massive impact + low D-minor brass-like hit')
    # RACE / HOUSE / EL: drums and driving ostinato
    a, b = S['race']['t0'], S['rise']['t0']
    cue(a, 'MUSIC', 'Drums in: taiko-style groove + driving ostinato')
    t = a
    k = 0
    while t < b - 0.1:
        if k % 4 == 0:
            place(m, taiko(62, 0.8, 1.0), t, 0.95, pan=-0.1)
        elif k % 4 == 2:
            place(m, taiko(78, 0.6, 0.75), t, 0.85, pan=0.15)
        if k % 2 == 1:
            place(m, taiko(110, 0.3, 0.35), t, 0.6, pan=0.3)
        place(m, pluck(NOTE[pattern[k % 8]], 0.25, 2400), t, 0.38)
        place(m, pluck(NOTE[pattern[(k + 3) % 8]] * 2, 0.2, 3000), t + beat / 4, 0.18, pan=-0.3)
        t += beat / 2
        k += 1
    place(m, pad(['D2', 'A2', 'D3', 'F3'], b - a + 0.5, bright=1600, attack=0.3, release=0.5), a, 0.5)
    for cut in (S['house']['t0'], S['el']['t0']):
        place(m, boom(1.5, 90, 40, 0.45), cut)
    # RISE: everything drops away to one low note and an eerie high tone (the pause before the payoff)
    r = S['rise']['t0']
    cue(r, 'MUSIC', 'Drop-out: single low D + eerie high tone')
    place(m, pad(['D2'], S['freeze']['t0'] - r + 1.0, bright=400, attack=0.05, release=1.0), r, 0.6)
    t_ = tvec(S['freeze']['t0'] - r + 1.0)
    eerie = np.sin(2 * np.pi * NOTE['A5'] * t_ + 0.4 * np.sin(2 * np.pi * 5 * t_)) * env_adsr(len(t_), 0.8, 0.2, 0.8, 0.8) * 0.06
    place(m, eerie, r, 1.0, pan=0.2)
    # FREEZE + STUCK: cold, sparse
    f0 = S['freeze']['t0']
    cue(f0, 'MUSIC', 'Cold pad (Dm add9) + sparse bells; heartbeat returns in the stuck shot')
    place(m, pad(['D3', 'E3', 'F3', 'A3'], S['decades']['t0'] - f0 + 0.8, bright=1100, attack=2.0, release=1.2), f0, 0.55)
    for tt, nm in zip(np.arange(f0 + 0.6, S['decades']['t0'] - 0.5, 1.9), ['A4', 'F4', 'E4', 'D4', 'A4', 'E4']):
        place(m, bell(NOTE[nm]), tt, 0.35, pan=RNG.uniform(-0.5, 0.5))
    for tt in np.arange(S['stuck']['t0'] + 0.3, S['decades']['t0'] - 0.4, 1.15):
        place(m, heartbeat(), tt, 0.55)
    # DECADES: warm, nostalgic
    d0 = S['decades']['t0']
    cue(d0, 'MUSIC', 'Warm turn: F major -> Bb major pad (decades later)')
    place(m, pad(['F2', 'A2', 'C3', 'F3'], 2.2, bright=1500, attack=0.6, release=0.8), d0, 0.5)
    place(m, pad(['Bb1', 'D3', 'F3', 'A3'], S['end']['t0'] - d0 - 1.6, bright=1500, attack=0.6, release=0.6), d0 + 2.0, 0.5)
    for tt, nm in zip(np.arange(d0 + 0.4, S['end']['t0'] - 0.4, 0.9), ['C4', 'A3', 'F4', 'D4', 'C4']):
        place(m, pluck(NOTE[nm], 0.6, 2500) * 0.6, tt, 0.4, pan=0.2)
    # END: final hit and a ring-out
    e0 = S['end']['t0']
    place(m, whoosh(0.8, up=True)[::-1], e0 - 0.8, 0.5)
    place(m, boom(4.0, 85, 28, 0.9), e0)
    place(m, pad(['D2', 'A2', 'D3', 'F3'], END - e0 + 0.5, bright=900, attack=0.05, release=2.2), e0, 0.6)
    cue(e0, 'MUSIC', 'Final impact on the question, ring-out to end')
    return reverb(m, 2.6, 0.22)


def build_sfx():
    x = np.zeros((N, 2))
    S = SHOT
    # HOOK: flood roaring toward the camera
    h1 = S['hook']['t1']
    r = rush(h1 + 0.3, 1.0) * np.linspace(0.35, 1.0, int((h1 + 0.3) * SR))
    place(x, r, 0.0, 0.55)
    place(x, whoosh(1.0, True), h1 - 0.7, 0.6)
    cue(0.0, 'SFX', 'Rushing flood swelling toward camera; whoosh into the cut')
    # AERIAL: harbour wind, gulls
    a0 = S['aerial']['t0']
    place(x, wind(S['scale']['t1'] - a0, 0.35), a0, 0.5)
    for k, tt in enumerate((a0 + 0.3, a0 + 1.1, a0 + 1.5)):
        place(x, gull(), tt, 0.8, pan=(-0.6, 0.4, 0.7)[k])
    cue(a0, 'SFX', 'Harbour wind + gulls')
    # SCALE: tank groan
    place(x, groan(3.5, 50, 62), S['scale']['t0'] + 0.6, 0.55)
    cue(S['scale']['t0'] + 0.6, 'SFX', 'Low metal groan of the full tank')
    # drips (timed to the animated drips)
    for tt in EV['drips']:
        if S['scale']['t0'] <= tt < S['leaks']['t1']:
            place(x, drip(), tt, 0.5 if tt >= S['leaks']['t0'] else 0.15, pan=RNG.uniform(-0.3, 0.3))
    cue(S['leaks']['t0'], 'SFX', 'Molasses drips (synced to the drip animation)')
    # CUTAWAY: a trickle of water
    c0 = S['cutaway']['t0']
    tr = filt(white(S['cutaway']['t1'] - c0), 'bp', (900, 4000)) * 0.08
    place(x, tr * env_adsr(len(tr), 0.3, 0.1, 1.0, 0.5), c0, 0.6)
    cue(c0, 'SFX', 'Thin trickle of water (the six-inch test)')
    # PAINT: brush strokes
    p0 = S['paint']['t0']
    for k in range(4):
        place(x, swish(0.65), p0 + 0.3 + k * 0.72, 0.55, pan=(-0.4, 0.3, -0.2, 0.4)[k])
    cue(p0, 'SFX', 'Brush strokes x4')
    # THERMO: wind easing, distant city
    place(x, wind(S['thermo']['t1'] - S['thermo']['t0'], 0.2), S['thermo']['t0'], 0.5)
    # RIVETS: pings timed to each popped rivet, groaning steel underneath
    for i, tt in enumerate(EV['rivet_pops']):
        place(x, ping(RNG.uniform(1900, 2900)), tt, 0.75, pan=RNG.uniform(-0.6, 0.6))
        if i % 3 == 0:
            place(x, ricochet(), tt + 0.03, 0.6, pan=RNG.uniform(-0.8, 0.8))
    place(x, groan(S['burst']['t0'] - S['rivets']['t0'], 45, 95), S['rivets']['t0'], 0.7)
    cue(EV['rivet_pops'][0], 'SFX', f"{len(EV['rivet_pops'])} rivet pings, machine-gun cadence (synced to pops)")
    # BURST: tearing steel and the release
    b0 = S['burst']['t0']
    tear = filt(white(1.6), 'bp', (400, 3500)) * expdecay(int(1.6 * SR), 0.4) * 0.7
    place(x, tear, b0, 0.8)
    place(x, rush(10.0, 1.0) * env_adsr(int(10.0 * SR), 0.05, 0.3, 0.9, 1.5), b0, 0.9)
    cue(b0, 'SFX', 'Steel tearing + flood release')
    # RACE / HOUSE / EL
    place(x, rush(S['rise']['t0'] - S['race']['t0'], 1.0), S['race']['t0'], 0.7)
    place(x, whoosh(0.5, True), S['race']['t0'] - 0.25, 0.5)
    place(x, wood_crack(), S['house']['t0'] + 0.15, 0.9, pan=-0.3)
    place(x, wood_crack(), S['house']['t0'] + 1.0, 0.6, pan=0.3)
    place(x, groan(2.2, 60, 38) * 1.4, S['el']['t0'] + 0.1, 0.9)
    for tt in (S['el']['t0'] + 0.3, S['el']['t0'] + 1.1):
        place(x, ping(900) * 0.7, tt, 0.7)
    cue(S['house']['t0'], 'SFX', 'Wood splintering (house shoved off foundation)')
    cue(S['el']['t0'], 'SFX', 'Steel girders groaning and bending (elevated railway)')
    # RISE: flow subsiding
    rr = S['rise']['t0']
    place(x, rush(S['freeze']['t0'] - rr + 0.5, 0.6) * np.linspace(1, 0.3, int((S['freeze']['t0'] - rr + 0.5) * SR)), rr, 0.6)
    # FREEZE / STUCK: night wind, ice crackle, slow ooze
    f0 = S['freeze']['t0']
    place(x, wind(S['decades']['t0'] - f0, 0.45), f0, 0.6)
    cr = crackle(S['decades']['t0'] - f0, 30) * np.linspace(0.1, 1.0, int((S['decades']['t0'] - f0) * SR))
    place(x, cr, f0, 0.7, pan=0.2)
    ooze = filt(brown(S['decades']['t0'] - f0), 'low', 160) * 0.25
    place(x, ooze, f0, 0.6)
    cue(f0, 'SFX', 'Night wind + ice crackle building as the molasses freezes')
    # DECADES: summer evening
    d0 = S['decades']['t0']
    place(x, cicadas(S['end']['t0'] - d0) * env_adsr(int((S['end']['t0'] - d0) * SR), 0.8, 0.2, 1.0, 0.6), d0, 0.6)
    place(x, gull(), d0 + 1.8, 0.4, pan=0.6)
    cue(d0, 'SFX', 'Summer evening: insects, a distant gull')
    # END
    e0 = S['end']['t0']
    place(x, rush(END - e0, 0.6) * np.linspace(1, 0, int((END - e0) * SR)), e0, 0.5)
    # transition whooshes on fast cuts
    for name in ('scale', 'thermo', 'rivets', 'house', 'el', 'decades'):
        place(x, whoosh(0.45, True), S[name]['t0'] - 0.3, 0.3, pan=RNG.uniform(-0.5, 0.5))
    return reverb(x, 1.4, 0.15, damp=6000)


def read_wav(path):
    with wave.open(path, 'rb') as w:
        sr = w.getframerate()
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:
        d = signal.resample_poly(d, SR, sr)
    return d


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    pcm = (x * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def main():
    music = build_music()
    sfx = build_sfx()
    vo = read_wav(os.path.join(ROOT, 'audio', 'vo', 'voiceover.wav'))
    vo = filt(vo, 'high', 80)
    # gentle presence boost and compression on the voice
    vo = vo + 0.25 * filt(vo, 'bp', (2000, 5000))
    vo = np.tanh(vo * 1.8) / np.tanh(1.8)
    vo_t = np.zeros(N)
    vo_t[:min(len(vo), N)] = vo[:N]
    # duck music and effects under the voice
    env = np.abs(vo_t)
    env = filt(env, 'low', 6.0)
    env = env / (np.max(env) + 1e-9)
    duck = 1.0 - 0.55 * np.clip(env * 3.0, 0, 1)
    duck = filt(duck, 'low', 3.0)
    music_n = music / (np.max(np.abs(music)) + 1e-9)
    sfx_n = sfx / (np.max(np.abs(sfx)) + 1e-9)
    mix = (music_n * 0.42 * duck[:, None] + sfx_n * 0.42 * (0.5 + 0.5 * duck[:, None])
           + np.stack([vo_t, vo_t], 1) * 0.95)
    # fade out the last half second, soft-limit, normalise to -1 dBFS
    nf = int(0.6 * SR)
    end_i = int(END * SR)
    mix[end_i - nf:end_i] *= np.linspace(1, 0, nf)[:, None]
    mix[end_i:] = 0
    mix = np.tanh(mix * 1.3) / np.tanh(1.3)
    mix = mix / np.max(np.abs(mix)) * 10 ** (-1 / 20)
    mix = mix[:end_i]
    os.makedirs(os.path.join(ROOT, 'audio', 'music'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'audio', 'sfx'), exist_ok=True)
    write_wav(os.path.join(ROOT, 'audio', 'music', 'score.wav'), (music_n * 0.9)[:end_i])
    write_wav(os.path.join(ROOT, 'audio', 'sfx', 'sfx.wav'), (sfx_n * 0.9)[:end_i])
    write_wav(os.path.join(ROOT, 'audio', 'mix.wav'), mix)
    write_sheet()
    print('wrote audio/mix.wav', round(len(mix) / SR, 2), 's')


def write_sheet():
    lines = ['# Audio & SFX timing sheet', '',
             'All music and sound effects are synthesised by `scripts/audio.py` (numpy/scipy). '
             'The voiceover is Piper TTS (`scripts/voiceover.py`, voice `en_US-ljspeech-high`). '
             'Times are seconds from the start of the video (30 fps → frame = t × 30 + 1).', '',
             '## Voiceover', '', '| Start | End | Line | Section | Text |', '|---|---|---|---|---|']
    for l in TL['lines']:
        lines.append(f"| {l['start']:.2f} | {l['end']:.2f} | {l['id']} | {l['section']} | {l['text']} |")
    lines += ['', '## Shots (cuts)', '', '| Shot | Start | End | Frames |', '|---|---|---|---|']
    for s in EV['shots']:
        lines.append(f"| {s['name']} | {s['t0']:.2f} | {s['t1']:.2f} | {s['f0']}–{s['f1']} |")
    lines += ['', '## Music and SFX cues', '', '| Time | Track | Cue |', '|---|---|---|']
    for t, tr, txt in sorted(CUES):
        lines.append(f'| {t:.2f} | {tr} | {txt} |')
    lines += ['', '## Mix', '',
              '- Voice: high-pass 80 Hz, presence lift 2–5 kHz, soft compression, level 0.95.',
              '- Music: ducked up to −55 % under the voice (envelope follower), level 0.42.',
              '- SFX: ducked up to −27 % under the voice, level 0.42.',
              '- Master: soft-clip limiter, normalised to −1 dBFS, 0.6 s fade-out.', '',
              'Stems: `audio/vo/voiceover.wav`, `audio/music/score.wav`, `audio/sfx/sfx.wav`; '
              'final mix `audio/mix.wav` (48 kHz stereo).']
    with open(os.path.join(ROOT, 'audio', 'timing_sheet.md'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
