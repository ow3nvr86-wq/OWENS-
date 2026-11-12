"""Music and SFX for Trapped in Minecraft, synthesised in numpy and placed in narration seconds
(word times: work/words.json). Writes audio/music.wav, audio/sfx.wav and audio/mix_raw.wav (voice unchanged + music
ducked under the voice + SFX at ~0.38 of the voice level). Run: $SHORTS_PY audio.py"""
import json, os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
rng = np.random.default_rng(11)


def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


VO = load(os.path.join(HERE, 'audio', 'vo.mp3'))
N = len(VO); DUR = N / SR
def t_(d): return np.arange(max(1, int(d * SR))) / SR
def env(n, a, r):
    e = np.ones(n); a, r = max(1, int(a * SR)), max(1, int(r * SR))
    e[:min(a, n)] = np.linspace(0, 1, min(a, n)); e[max(0, n - r):] *= np.linspace(1, 0, n - max(0, n - r)); return e
def box(x, k):
    if k <= 1: return x
    c = np.cumsum(np.concatenate([[0.0], x])); h = k // 2
    i0 = np.clip(np.arange(len(x)) - h, 0, len(x)); i1 = np.clip(np.arange(len(x)) - h + k, 0, len(x))
    return (c[i1] - c[i0]) / np.maximum(1, i1 - i0)
def lp(x, fc, passes=2):
    k = max(1, int(SR / fc / 2))
    for _ in range(passes): x = box(x, k)
    return x
def hp(x, fc): return x - lp(x, fc)
def bp(x, lo, hi): return lp(hp(x, lo), hi)
def put(buf, x, at, g=1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(x) <= 0: return
    j0 = max(0, -i); x = x[j0:]; i = max(0, i); n = min(len(x), len(buf) - i); buf[i:i + n] += x[:n] * g
def noise(d): return rng.standard_normal(int(d * SR))
def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)

# ---------------- instruments ----------------
def pluck(f, d=0.9, bright=1.0):            # lyre-ish pluck: harmonics decaying faster as they go up
    t = t_(d); x = np.zeros_like(t)
    for k in range(1, 9):
        x += np.sin(2 * np.pi * f * k * t + k) * (0.9 ** k) * np.exp(-t * (3 + k * 2.2 / bright))
    return x * env(len(t), 0.002, 0.08)
def pad(f, d, warm=1):
    t = t_(d); x = sum(np.sin(2 * np.pi * f * k * t * (1 + 0.003 * k)) / k for k in range(1, 7))
    return lp(x, 900 * warm) * env(len(t), 0.4, 0.6) * (1 + 0.05 * np.sin(2 * np.pi * 4.5 * t))
def drum(d=0.35, f0=95):                    # frame drum
    t = t_(d); f = f0 * (1 + 0.8 * np.exp(-t * 25))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11) + lp(noise(d), 1200) * np.exp(-t * 30) * 0.4
def tick(d=0.05): t = t_(d); return hp(noise(d), 3000) * np.exp(-t * 90)
def boom(d=2.5, f0=48, k=2.0):
    t = t_(d); f = f0 * (1 + 0.7 * np.exp(-t * 7))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * k) + lp(noise(d), 180) * np.exp(-t * 5) * 0.6
def heartbeat(at, buf, g=1.0):
    for dt, a in [(0, 1.0), (0.22, 0.7)]: put(buf, boom(0.4, 55, 14), at + dt, g * a)

def whoosh(d=0.35):
    t = t_(d); n = noise(d); e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return (lp(n, 1400) * 0.7 + hp(n, 500) * 0.3) * e
def impact(d=0.5): t = t_(d); return boom(d, 70, 10) * 0.8 + lp(noise(d), 2500) * np.exp(-t * 25) * 0.7
def zap(d=0.45):
    t = t_(d); f = 1800 * np.exp(-t * 4) + 300
    return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3 * np.exp(-t * 4) + hp(noise(d), 4000) * 0.15 * np.exp(-t * 6)
def poof(d=0.4): t = t_(d); return lp(noise(d), 1500) * np.exp(-t * 9) * env(len(t), 0.005, 0.1)
def wail(d=0.8, f0=520):
    t = t_(d); f = f0 + 140 * np.sin(2 * np.pi * 1.6 * t) - 120 * t
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.15, 0.3) * (1 + 0.3 * np.sin(2 * np.pi * 6 * t)) * 0.5
def swish(d=0.22): t = t_(d); f = np.linspace(2500, 500, len(t)); return bp(noise(d), 600, 4000) * np.sin(np.pi * t / d) ** 2
def growl(d=0.8):
    t = t_(d); f = 70 + 15 * np.sin(2 * np.pi * 9 * t)
    return lp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) + lp(noise(d), 300), 700) * env(len(t), 0.05, 0.3) * 0.5
def chomp(d=0.18): t = t_(d); return (lp(noise(d), 1800) + np.sin(2 * np.pi * 140 * t)) * np.exp(-t * 28)
def gulp(d=0.3): t = t_(d); f = 300 - 220 * t / d; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
def clang(d=0.9):
    t = t_(d); return sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, k in [(820, 5), (1373, 7), (2210, 9)]) * 0.4
def splash(d=0.8): t = t_(d); return (hp(noise(d), 800) * 0.6 + lp(noise(d), 600)) * np.exp(-t * 5) * env(len(t), 0.005, 0.3)
def crash(d=0.7): t = t_(d); return (lp(noise(d), 3500) * np.exp(-t * 7) + boom(d, 60, 9) * 0.8)
def oink(d=0.22, f0=280):
    t = t_(d); f = f0 * (1 + 0.6 * t / d)
    x = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in range(1, 8))
    return bp(x, 300, 2500) * env(len(t), 0.01, 0.06) + lp(noise(d), 900) * 0.15
def voice_formant(f0, d, formants, vib=5.0):
    t = t_(d); f = f0 * (1 + 0.012 * np.sin(2 * np.pi * vib * t))
    ph = 2 * np.pi * np.cumsum(f) / SR; x = np.zeros_like(t)
    for k in range(1, 30):
        fk = f0 * k; w = sum(a * np.exp(-((fk - F) / bw) ** 2) for F, bw, a in formants)
        x += np.sin(ph * k) * w / k ** 0.3
    return x * env(len(t), 0.08, 0.25)
def siren_song(d):
    out = np.zeros(int(d * SR))
    for i, (n, dd) in enumerate([(76, 0.35), (79, 0.35), (81, 0.5), (79, 0.3)]):
        put(out, voice_formant(mtof(n), dd + 0.15, [(800, 200, 1), (1150, 250, 0.6), (2900, 400, 0.25)]), sum(x for _, x in [(76, 0.35), (79, 0.35), (81, 0.5), (79, 0.3)][:i]), 0.25)
    return out
def moo(d=0.9):
    return voice_formant(115, d, [(300, 120, 1), (870, 200, 0.4)], 3.0) * 0.8
def thunder(d=2.4): t = t_(d); return lp(noise(d), 260) * np.exp(-t * 1.5) * env(len(t), 0.02, 0.8) * 1.6 + hp(noise(d), 1500) * np.exp(-t * 18) * 0.8
def crack(d=0.4): t = t_(d); return hp(noise(d), 2000) * np.exp(-t * 20) + lp(noise(d), 500) * np.exp(-t * 8)
def gliss(d=0.9):
    out = np.zeros(int(d * SR))
    for i, n in enumerate(range(62, 86, 2)): put(out, pluck(mtof(n), 0.6, 1.3), i * 0.05, 0.25)
    return out
def munch(d=0.4):
    out = np.zeros(int(d * SR))
    for i in range(3): put(out, chomp(0.1) * 0.6, i * 0.12)
    return out
def boing(d=0.7): t = t_(d); f = 220 + 160 * np.sin(2 * np.pi * 7 * t) * np.exp(-t * 3); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4)
def chime(f=1760, d=1.0): t = t_(d); return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * 4)
def murmur(d):
    out = np.zeros(int(d * SR))
    for i in range(int(d * 6)): put(out, voice_formant(150 + rng.random() * 90, 0.25, [(500 + rng.random() * 300, 200, 1), (1300, 300, 0.5)], 6) * 0.4, rng.random() * (d - 0.3))
    return out
def creak(d=0.6, f0=300):
    t = t_(d); f = f0 + 70 * np.sin(2 * np.pi * 1.3 * t)
    return lp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (np.sin(2 * np.pi * 30 * t) > 0), 2500) * env(len(t), 0.05, 0.2) * 0.35
def twang(d=0.6): t = t_(d); return (np.sin(2 * np.pi * 180 * t) + 0.5 * np.sin(2 * np.pi * 360 * t)) * np.exp(-t * 7)
def ting(f=2600, d=0.5): return chime(f, d) * 0.6
def scratch(d=0.45):
    t = t_(d); f = 600 + 1400 * np.abs(np.sin(2 * np.pi * 2.4 * t))
    return bp(noise(d), 400, 4000) * (0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR / 40)) * env(len(t), 0.01, 0.06)
def horn(d=1.6):
    t = t_(d); f = 98 * (1 + 0.02 * np.sin(2 * np.pi * 5 * t))
    x = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in range(1, 10))
    return lp(x, 900) * env(len(t), 0.25, 0.5)
def steps(d, rate=5):
    out = np.zeros(int(d * SR))
    for i in range(int(d * rate)): put(out, lp(noise(0.06), 600) * np.exp(-t_(0.06) * 60), i / rate)
    return out

music = np.zeros(N)
sfx = np.zeros(N)
BPM = 112; BEAT = 60 / BPM
def marimba(f, d=0.5):
    t = t_(d); return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 30)) * np.exp(-t * 9) * env(len(t), 0.003, 0.05)
def musicbox(f, d=1.2):
    t = t_(d); return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 3.01 * t) + 0.1 * np.sin(2 * np.pi * f * 5.4 * t)) * np.exp(-t * 3.5)
MEL = [72, 76, 79, 76, 74, 77, 81, 77, 72, 76, 79, 84, 83, 79, 74, 71]
CH = {0: [48, 55], 1: [53, 60], 2: [55, 62], 3: [48, 55]}
def bouncy(t0, t1, vol=1.0, minor=False):
    t = t0; k = 0
    while t < t1:
        bar = int(k / 8) % 4
        if k % 2 == 0: put(music, marimba(mtof(MEL[(k // 2) % 16] - (3 if minor and MEL[(k // 2) % 16] % 12 in (4, 9, 11) else 0)), 0.45), t, 0.22 * vol)
        if k % 4 == 0: put(music, pluck(mtof(CH[bar][0] - (0 if not minor else 3 * (bar == 0))), 0.9, 0.8), t, 0.32 * vol)
        if k % 4 == 2: put(music, pluck(mtof(CH[bar][1]), 0.6, 0.8), t, 0.18 * vol)
        if k % 2 == 1: put(music, tick(0.03), t, 0.10 * vol)
        t += BEAT / 2; k += 1
# 0-22.6: playful daytime
bouncy(0.15, 22.6, 0.9)
# 22.6-30.4: sunset gets tense (minor, quicker ticks)
bouncy(22.6, 29.5, 1.0, minor=True)
put(music, pad(mtof(45), 7.0, 0.8), 22.6, 0.18)
# 30.45-35.6: bedtime music box
for i, n in enumerate([84, 79, 76, 79, 84, 86, 84, 79, 77, 81, 84, 81, 79, 76, 72, 76, 79, 76, 74, 72]):
    if 30.5 + i * 0.27 < 35.5: put(music, musicbox(mtof(n), 1.3), 30.5 + i * 0.27, 0.18)
# 35.6 the music stops; a low drone and heartbeat under the eyes
put(music, pad(mtof(33), 6.5, 0.5), 35.6, 0.55)
heartbeat(36.6, music, 0.8); heartbeat(37.4, music, 1.0)
# 38.35 "Herobrine." - the sting; then wind and an unsettling cluster to the end
put(music, boom(2.6, 40, 1.8), 38.36, 1.5)
put(music, pad(mtof(37), 3.2, 0.6) + 0, 38.8, 0.25); put(music, pad(mtof(38), 3.0, 0.6), 38.9, 0.2)
put(music, boom(1.0, 55, 4), 41.34, 0.7)
music[int(35.6 * SR):int(35.62 * SR)] *= 0

def thud(d=0.22): t = t_(d); return (np.sin(2 * np.pi * 85 * t * (1 - 0.4 * t / d)) + lp(noise(d), 600) * 0.6) * np.exp(-t * 20)
def blockpop(d=0.18): t = t_(d); f = 520 * np.exp(-t * 6) + 200; return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.6 + bp(noise(d), 800, 3000) * 0.5) * np.exp(-t * 18)
def plip(d=0.12): t = t_(d); f = 900 + 1400 * t / d; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 20)
def clink(d=0.35): t = t_(d); return sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, k in [(2400, 14), (3750, 18), (5100, 22)]) * 0.3 + bp(noise(d), 1500, 6000) * np.exp(-t * 40) * 0.6
def crumble(d=0.3): t = t_(d); return lp(noise(d), 1800) * np.exp(-t * 12) * (0.6 + 0.4 * (rng.random(len(t)) > 0.97))
def fallwhistle(d=0.65): t = t_(d); f = 1800 - 1300 * t / d; return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.05, 0.05) * 0.4
def growl_tummy(d=0.7): t = t_(d); f = 60 + 25 * np.sin(2 * np.pi * 3 * t); return lp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) + lp(noise(d), 200), 300) * env(len(t), 0.1, 0.3) * 0.5
def pat(d=0.08): t = t_(d); return lp(noise(d), 900) * np.exp(-t * 50)
def tada(): out = np.zeros(int(0.8 * SR)); [put(out, marimba(mtof(n), 0.6), i * 0.07, 0.4) for i, n in enumerate([72, 76, 79, 84])]; return out
def slam(d=0.6): t = t_(d); return boom(d, 70, 9) * 0.9 + lp(noise(d), 2500) * np.exp(-t * 30) * 0.8
def rip(d=0.5): t = t_(d); return bp(noise(d), 1200, 7000) * (0.5 + 0.5 * (rng.random(len(t)) > 0.6)) * env(len(t), 0.01, 0.1) * np.exp(-t * 2)
def crickets(d):
    t = t_(d); return np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 28 * t) > 0.3) * (np.sin(2 * np.pi * 0.9 * t) > 0) * 0.08
def wind(d): t = t_(d); return lp(noise(d), 500) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t)) * env(len(t), 0.4, 0.4) * 0.5
def glint(d=0.8): return chime(3100, d) * 0.5 + chime(4650, d) * 0.3

# whips
for b in [13.50, 22.60]: put(sfx, whoosh(0.34), b - 0.17, 0.7)
# A: wake, pockets, tummy, clock, walk, punches, logs pop, pickups, shrug
put(sfx, boing(0.5), 0.55, 0.45)
for at in [2.62, 2.78, 2.95, 3.1]: put(sfx, pat(), at, 0.8)
put(sfx, growl_tummy(0.8), 3.55, 0.9)
for i in range(18): put(sfx, tick(0.04), 4.6 + i * 0.1, 0.35)
put(sfx, steps(0.5, 6), 6.55, 0.5)
for i in range(10): put(sfx, thud(), 7.2 + i * 0.26, 0.9)
put(sfx, glint(0.6), 8.35, 0.4)
for at in [9.70, 10.12, 10.38, 10.62]: put(sfx, blockpop(), at, 0.9); put(sfx, plip(), at + 0.85, 0.5)
put(sfx, steps(0.55, 6), 10.75, 0.45)
put(sfx, fallwhistle(0.5)[::-1] * 0.6, 11.4, 0.4); put(sfx, boing(0.45), 12.6, 0.4)
# B: craft, walk, mine 64 blocks, the weight drops, skip away
for i in range(4): put(sfx, thud(0.1), 13.55 + i * 0.09, 0.4)
put(sfx, glint(0.7), 13.95, 0.6)
put(sfx, steps(0.65, 6), 14.35, 0.45)
for i in range(11):
    at = 15.0 + i * 0.3 + 0.12; put(sfx, clink(), at, 0.7); put(sfx, crumble(), at + 0.02, 0.6); put(sfx, plip(), at + 0.25, 0.35)
put(sfx, fallwhistle(0.65), 18.6, 0.8); put(sfx, boom(1.6, 45, 3), 19.25, 1.0); put(sfx, crash(0.6), 19.25, 0.6)
put(sfx, crumble(0.6), 19.3, 0.5)
for i, n in enumerate([79, 81, 83, 84, 83, 81, 79]): put(sfx, voice_formant(mtof(n), 0.16, [(1200, 400, 1), (2600, 600, 0.4)]), 21.15 + i * 0.13, 0.25)   # whistling
put(sfx, steps(1.4, 7), 21.1, 0.35)
# C: sunset, the house slapped together, door, nervous, slam
put(sfx, crickets(7.8), 22.6, 1.0)
for i in range(31): put(sfx, thud(0.12), 24.08 + (25.6 - 24.08) * i / 31, 0.55)
put(sfx, tada(), 25.62, 0.6); put(sfx, blockpop(), 26.45, 0.8); put(sfx, chime(2600, 0.6), 27.22, 0.35)
put(sfx, voice_formant(90, 1.1, [(500, 200, 1), (900, 250, 0.5)], 2.5) * 0.6, 28.35, 0.5)    # distant groan
put(sfx, gulp(), 28.95, 0.7); put(sfx, steps(0.4, 10), 29.15, 0.5); put(sfx, slam(), 29.55, 1.0)
# D: inside - torch crackle, yay, bed, quiet, the eyes
torchn = lp(noise(5.2), 2500) * (rng.random(int(5.2 * SR)) > 0.996) * 0.8 + lp(noise(5.2), 300) * 0.05
put(sfx, torchn, 30.45, 0.5)
put(sfx, boing(0.4), 30.55, 0.35); put(sfx, creak(0.6, 200), 31.65, 0.6); put(sfx, rustle(0.5) if 'rustle' in dir() else crumble(0.3), 32.1, 0.4)
put(sfx, glint(1.0), 36.15, 0.5); put(sfx, voice_formant(220, 0.35, [(700, 200, 1), (1200, 300, 0.5)]) * 0.5, 37.35, 0.5)  # gasp
# E/F: the sting, the wind, the rip
put(sfx, impact(0.6), 38.36, 0.8); put(sfx, wind(3.6), 38.4, 0.8)
put(sfx, rip(0.45), 41.32, 0.9)

def gated_rms(x):
    b, h = int(0.4 * SR), int(0.1 * SR)
    e = np.array([np.mean(x[i:i + b] ** 2) for i in range(0, max(1, len(x) - b), h)])
    e = e[e > 1e-6]; e = e[e > np.mean(e) * 0.1] if len(e) else e
    return float(np.sqrt(np.mean(e))) if len(e) else 1e-9
def write(p, x, scale=1.0):
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(4); w.setframerate(SR)
        w.writeframes((np.clip(x * scale, -1.99, 1.99) / 2 * 2147483647).astype('<i4').tobytes())

rv, pv = gated_rms(VO), np.abs(VO).max()
# music: quiet underscore ~13 dB under the voice, ducked another ~7 dB while the voice speaks
music *= (10 ** (-13 / 20)) * rv / gated_rms(music)
ve = lp(np.abs(VO), 8, 3); ve = ve / max(1e-9, np.percentile(ve, 95))
duck = 1 - 0.55 * np.clip(ve, 0, 1)
# keep the big hits un-ducked (they sit in pauses anyway)
music *= duck
# SFX: about 0.38 of the voice level, peaks capped below the voice peak
sfx *= 0.38 * rv / gated_rms(sfx)
sfx = np.clip(sfx, -0.85 * pv, 0.85 * pv)
mix = VO + music + sfx
mix[int(41.95 * SR) + int(0.15 * SR):] *= np.linspace(1, 0, len(mix) - int(41.95 * SR) - int(0.15 * SR)) if len(mix) > int(42.1 * SR) else 1   # quick fade on the cut to black
os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
write(os.path.join(HERE, 'audio', 'music.wav'), music); write(os.path.join(HERE, 'audio', 'sfx.wav'), sfx)
write(os.path.join(HERE, 'audio', 'mix_raw.wav'), mix); write(os.path.join(HERE, 'audio', 'bed_raw.wav'), music + sfx)
db = lambda v: 20 * np.log10(max(v, 1e-12))
print('voice gated RMS %.1f dB | music %.1f dB vs voice | sfx %.1f dB vs voice | mix peak %.1f dB' % (
    db(rv), db(gated_rms(music)) - db(rv), db(gated_rms(sfx)) - db(rv), db(np.abs(mix).max())))
