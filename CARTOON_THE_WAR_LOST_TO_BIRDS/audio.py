"""Music and SFX stems for The War Lost to Birds, synthesised with numpy and timed to the picture (frames / 30).
Writes audio/music.wav and audio/sfx.wav (48 kHz mono). Levels are set later by mix.py, so stems are unnormalised.
Run: $SHORTS_PY audio.py"""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
DUR = json.load(open(os.path.join(HERE, 'work', 'words.json')))['duration']
N = int(round(DUR * SR))
rng = np.random.default_rng(7)
F = lambda fr: fr / 30.0            # frame -> seconds


def t_(d): return np.arange(int(d * SR)) / SR
def env(n, a, r, sus=None):
    a, r = max(1, int(a * SR)), max(1, int(r * SR))
    e = np.ones(n)
    e[:min(a, n)] = np.linspace(0, 1, min(a, n))
    e[max(0, n - r):] *= np.linspace(1, 0, n - max(0, n - r))
    return e
def lp(x, fc):                       # one-pole low-pass
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y
def box(x, k):                       # centred moving average via cumulative sums (fast for any k)
    if k <= 1: return x
    c = np.cumsum(np.concatenate([np.zeros(1), x]))
    h = k // 2
    i0 = np.clip(np.arange(len(x)) - h, 0, len(x)); i1 = np.clip(np.arange(len(x)) - h + k, 0, len(x))
    return (c[i1] - c[i0]) / np.maximum(1, i1 - i0)
def lp_fast(x, fc, passes=2):
    k = max(1, int(SR / fc / 2))
    for _ in range(passes): x = box(x, k)
    return x
def hp_fast(x, fc): return x - lp_fast(x, fc)
def put(buf, x, at):
    i = int(at * SR)
    if i >= len(buf) or i + len(x) <= 0: return
    j0 = max(0, -i); x = x[j0:]; i = max(0, i)
    n = min(len(x), len(buf) - i); buf[i:i + n] += x[:n]
def noise(d): return rng.standard_normal(int(d * SR))
def nfreq(note): return 440.0 * 2 ** ((note - 69) / 12)

# ---------------- music: a jaunty military march (116 bpm) ----------------
BPM = 116; BEAT = 60 / BPM
END_MUSIC = F(1208)                  # music stops on "The emus had won."
music = np.zeros(N)

def kick(d=0.35):
    t = t_(d); f = 110 * np.exp(-t * 30) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
def snare(d=0.22):
    t = t_(d); n = hp_fast(noise(d), 1200) * np.exp(-t * 22)
    return n * 0.8 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.4
def pluck(f, d=0.4):                 # tuba-ish plucked bass
    t = t_(d); x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.15 * np.sin(2 * np.pi * 3 * f * t)
    return x * np.exp(-t * 6) * env(len(t), 0.004, 0.05)
def brass(f, d):                     # soft brass pad: saw stack through a low-pass
    t = t_(d); x = sum(np.sin(2 * np.pi * f * k * t * (1 + 0.002 * k)) / k for k in range(1, 9))
    x = lp_fast(x, 1800) * env(len(t), 0.06, 0.12)
    return x * (1 + 0.04 * np.sin(2 * np.pi * 5.2 * t))
def piccolo(f, d):
    t = t_(d); return (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)) * env(len(t), 0.01, 0.06) * (1 + 0.03 * np.sin(2 * np.pi * 6 * t))

# chord roots per bar (C major march, then a minor turn in the "weeks" montage)
PROG = [48, 43, 48, 43, 45, 41, 43, 43]                  # C G C G A F G G (midi bass notes)
CHORD = {48: [60, 64, 67], 43: [55, 59, 62], 45: [57, 60, 64], 41: [53, 57, 60]}
MELODY = [72, 74, 76, 72, 74, 71, 67, 71, 72, 76, 79, 76, 74, 72, 71, 74]
bars = int(END_MUSIC / (BEAT * 4)) + 1
for b in range(bars):
    t0 = b * BEAT * 4
    root = PROG[b % len(PROG)]
    sad = F(938) <= t0 < F(1095) and False
    for k in range(4):
        tb = t0 + k * BEAT
        if tb >= END_MUSIC: break
        put(music, kick() * (0.9 if k % 2 == 0 else 0.6), tb)
        if k % 2 == 1: put(music, snare() * 0.55, tb)
        put(music, snare(0.08) * 0.12, tb + BEAT / 2)                       # light ghost note
        put(music, pluck(nfreq(root - 12 + (7 if k % 2 else 0))) * 0.8, tb)  # oom-pah bass
        if k % 2 == 1:
            for n in CHORD[root]: put(music, brass(nfreq(n), BEAT * 0.45) * 0.12, tb)
    for k in range(2):
        tm = t0 + k * BEAT * 2
        if tm + BEAT < END_MUSIC:
            put(music, piccolo(nfreq(MELODY[(b * 2 + k) % len(MELODY)] + 12), BEAT * 1.6) * 0.16, tm)
# soften the bed under the montage tension, and lift on the arrival
mlev = np.ones(N)
def seg(a, b, v):
    i, j = int(a * SR), int(b * SR); mlev[i:j] = v
seg(F(183), F(364), 0.85)
seg(F(938), F(989), 1.15)
mlev = lp_fast(mlev, 3)
music *= mlev
music[int(END_MUSIC * SR):] = 0
# the sting: a low hit and a long drone after the music stops
def boom(d=2.5, f0=55):
    t = t_(d); f = f0 * (1 + 0.6 * np.exp(-t * 8))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2) + lp_fast(noise(d), 200) * np.exp(-t * 6) * 0.5
put(music, boom() * 1.4, END_MUSIC)
dr = t_(DUR - END_MUSIC)
drone = (np.sin(2 * np.pi * 65.4 * dr) + 0.5 * np.sin(2 * np.pi * 98.0 * dr)) * env(len(dr), 0.3, 0.4) * 0.25
put(music, drone, END_MUSIC)
# a final comic tag on the smug blink (two notes)
put(music, piccolo(nfreq(84), 0.18) * 0.35, F(1234)); put(music, piccolo(nfreq(91), 0.35) * 0.35, F(1240))

# ---------------- SFX ----------------
sfx = np.zeros(N)
def whoosh(d=0.6, up=True):
    t = t_(d); n = noise(d)
    lo = lp_fast(n, 900); hi = hp_fast(n, 300)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return (lo * 0.6 + hi * 0.4) * e
def thunk(d=0.25, f0=80):
    t = t_(d); return (np.sin(2 * np.pi * f0 * t * (1 - 0.3 * t)) + lp_fast(noise(d), 400) * 0.6) * np.exp(-t * 18)
def ting(f=2200, d=0.9):
    t = t_(d); return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * 5)
def click(d=0.05):
    t = t_(d); return hp_fast(noise(d), 2500) * np.exp(-t * 120)
def clunk(d=0.3):
    t = t_(d); x = (np.sin(2 * np.pi * 320 * t) * 0.6 + np.sin(2 * np.pi * 517 * t) * 0.4) * np.exp(-t * 14); x[:int(0.05 * SR)] += click(0.05) * 0.8; return x
def puffsnd(d=0.7):
    t = t_(d); return lp_fast(noise(d), 600) * np.exp(-t * 5) * env(len(t), 0.01, 0.2)
def boing(d=0.8):
    t = t_(d); f = 180 + 120 * np.sin(2 * np.pi * 7 * t) * np.exp(-t * 3)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.5)
def engine(d, rough=1.0):
    t = t_(d); f = 38 + 4 * np.sin(2 * np.pi * 0.7 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sign(np.sin(ph)) * 0.4 + np.sin(ph * 2) * 0.3
    x = lp_fast(x, 400) + lp_fast(noise(d), 250) * 0.6 * rough
    rattle = hp_fast(noise(d), 3000) * (np.sin(2 * np.pi * 9 * t) > 0.6) * 0.15 * rough
    return (x + rattle) * env(len(t), 0.25, 0.3)
def creak(d=0.7, f0=420):
    t = t_(d); f = f0 + 80 * np.sin(2 * np.pi * 1.3 * t)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (np.sin(2 * np.pi * 35 * t) > 0)
    return lp_fast(x, 2500) * env(len(t), 0.05, 0.2) * 0.4
def scribble(d):
    t = t_(d); n = hp_fast(noise(d), 1800) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * t))) * 0.4
    return n * env(len(t), 0.03, 0.05)
def rustle(d=0.5):
    t = t_(d); return hp_fast(noise(d), 1500) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 13 * t))) * env(len(t), 0.03, 0.15) * 0.6
def step(d=0.07):
    t = t_(d); return lp_fast(noise(d), 700) * np.exp(-t * 60)
def pop(d=0.06):
    t = t_(d); return np.sin(2 * np.pi * 900 * t * np.exp(-t * 20)) * np.exp(-t * 60)

# chase engines and bumps
put(sfx, engine(F(183), 1.0) * 0.9, 0)
for fr in [12, 40, 63, 86, 110, 150]: put(sfx, thunk(f0=70) * 0.6, F(fr))
put(sfx, engine(F(862 - 794), 1.2) * 0.9, F(794))
for fr in [800, 808]: put(sfx, thunk(f0=70) * 0.5, F(fr))
put(sfx, thunk(0.4, 55) * 1.3, F(818)); put(sfx, boing() * 0.55, F(819)); put(sfx, whoosh(0.5) * 0.5, F(824))
# glides, flashes and pushes
for fr, d in [(126, 0.7), (180, 0.6), (258, 1.2), (438, 0.5), (532, 0.6), (617, 0.4), (703, 0.4), (750, 0.35), (792, 0.35), (899, 0.6), (1024, 0.5), (1093, 0.4)]:
    put(sfx, whoosh(d) * 0.55, F(fr) - d / 2)
put(sfx, ting(2600) * 0.35, F(150))                                     # smug glance
# farm: windmill creaks and pecks
for k in range(5): put(sfx, creak(0.8, 380 + k * 15) * 0.5, F(190 + k * 36))
for k in range(30): put(sfx, pop() * 0.25, F(268 + k * 3.2 + (k % 3)))
# farmer
put(sfx, ting(2900, 1.2) * 0.4, F(408)); put(sfx, ting(3700, 1.0) * 0.25, F(412))
put(sfx, rustle(0.5) * 0.6, F(436))
# arrival: engine in, brakes, crates wobble, two guns, the tower
put(sfx, engine(F(530 - 491), 0.8) * 0.9, F(491))
t = t_(0.45); put(sfx, np.sin(2 * np.pi * (1900 + 300 * t) * t) * np.exp(-t * 4) * 0.12, F(518))
put(sfx, thunk(0.3, 60) * 0.6, F(528))
for k in range(4): put(sfx, creak(0.5, 300 - k * 20) * 0.6, F(532 + k * 9))
put(sfx, ting(2000) * 0.35, F(537)); put(sfx, ting(2500) * 0.35, F(543))
for k in range(3): put(sfx, creak(0.45, 250 - k * 25) * 0.5, F(565 + k * 12))
# the plan: scribbles and taps
put(sfx, scribble(F(690 - 640)) * 0.7, F(640))
for fr in [690, 697, 701]: put(sfx, click(0.04) * 0.7, F(fr)); put(sfx, thunk(0.08, 300) * 0.3, F(fr))
# scatter: a burst and lots of fast feet
put(sfx, whoosh(0.5) * 0.7, F(706)); put(sfx, thunk(0.3, 90) * 0.6, F(709))
for k in range(70): put(sfx, step() * (0.25 + 0.2 * rng.random()), F(709) + k * 0.045 + rng.random() * 0.02)
# the jam
put(sfx, click() * 0.8, F(755)); put(sfx, click() * 0.8, F(759)); put(sfx, puffsnd() * 0.9, F(762)); put(sfx, clunk() * 0.8, F(766))
# the army leaves and comes back
put(sfx, engine(F(902 - 863), 0.7) * 0.8 * np.linspace(1, 0.3, int(F(902 - 863) * SR)), F(863))
put(sfx, engine(F(936 - 903), 0.9) * 0.8 * np.linspace(0.3, 1.0, int(F(936 - 903) * SR)), F(903))
put(sfx, thunk(0.3, 60) * 0.5, F(934))
# weeks of shooting: distant rat-a-tat bursts, swelling day/night pads
for k in range(40):
    tb = F(940) + k * 0.042 * 1.0 + (k // 8) * 0.12
    put(sfx, lp_fast(click(0.06) + noise(0.06) * 0.3, 1500) * 0.35, tb)
# tally: casings clink, pencil
for k in range(10): put(sfx, ting(3200 + 300 * (k % 4), 0.25) * 0.12, F(992 + k * 5))
put(sfx, scribble(F(1078 - 1030)) * 0.6, F(1030))
# the letter slides; the stamp
put(sfx, rustle(0.6) * 0.7, F(1095))
put(sfx, thunk(0.35, 70) * 1.3, F(1181)); put(sfx, click(0.05) * 0.6, F(1181)); put(sfx, puffsnd(0.5) * 0.35, F(1182))
# final smug blink
put(sfx, ting(3000, 0.6) * 0.3, F(1235))


def write(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
for name, x in [('music', music), ('sfx', sfx)]:
    x = x / max(1e-9, np.abs(x).max()) * 0.9
    write(os.path.join(HERE, 'audio', name + '.wav'), x)
    print(name, 'written', '%.2f s' % (len(x) / SR))
