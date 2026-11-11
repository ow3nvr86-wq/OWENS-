"""Music and SFX for The Odyssey in 45 Seconds, synthesised in numpy and placed in narration seconds
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

music = np.zeros(N)
BPM = 100; BEAT = 60 / BPM
SCALE = [62, 63, 65, 67, 69, 70, 72, 74]            # D phrygian-ish (Greek colour)
def arp(t0, t1, root=50, density=1.0, vol=1.0, bright=1.0, drums=True):
    t = t0; k = 0
    while t < t1:
        step = BEAT / 2 / density
        n = SCALE[[0, 2, 4, 2, 5, 4, 2, 1][k % 8]] + (12 if k % 16 > 11 else 0)
        put(music, pluck(mtof(n), 0.8, bright), t, 0.22 * vol)
        if k % 4 == 0: put(music, pluck(mtof(root), 1.2, 0.7), t, 0.35 * vol)
        if drums and k % 2 == 0: put(music, drum(0.3, 90 if k % 4 == 0 else 120), t, (0.35 if k % 4 == 0 else 0.18) * vol)
        t += step; k += 1

# 0 - 3.9 adventurous open
arp(0.0, 3.9, 50, 1.0, 0.8)
# 3.9 - 6.7 the monster: drone + heartbeat
put(music, pad(mtof(38), 2.9, 0.6), 3.9, 0.8)
heartbeat(4.45, music, 0.9); heartbeat(5.70, music, 1.2)
# 6.7 - 23.1 the journey, building
arp(6.72, 10.95, 50, 1.0, 0.75)
put(music, pad(mtof(50), 4.2), 6.72, 0.25)
arp(10.95, 23.1, 50, 1.25, 1.0, 1.3)
for i in range(int((23.1 - 10.95) / (BEAT * 4)) + 1): put(music, pad(mtof([50, 48, 46, 45][i % 4]), BEAT * 4 + 0.3), 10.95 + i * BEAT * 4, 0.22)
# 23.1 - 25.1 storm: only a low rumble (music thins)
put(music, pad(mtof(38), 2.0, 0.5), 23.1, 0.5)
# 25.1 - 29.5 dreamy lotus: slow major harp
for i, n in enumerate([62, 66, 69, 74, 69, 66, 64, 67, 71, 76, 71, 67, 62, 66, 69, 74, 78, 74]):
    put(music, pluck(mtof(n), 1.6, 0.6), 25.1 + i * 0.24, 0.2)
put(music, pad(mtof(62), 4.4, 1.3), 25.1, 0.25)
# 29.5 - 37.5 back home: march-y pluck building to the bow
arp(29.55, 33.7, 50, 1.0, 0.85)
arp(33.7, 36.05, 50, 2.0, 0.9, 1.4)
put(music, boom(1.2, 60, 3.5), 36.66, 0.9)
arp(36.7, 37.5, 50, 1.0, 0.7)
# 37.57 "The twist?" - stop. 38.5 - 42.0 ominous pulse rising to "Greeks"
for i in range(9): put(music, boom(0.5, 45, 8), 38.55 + i * 0.4, 0.5 + i * 0.05)
put(music, pad(mtof(38), 3.5, 0.7), 38.5, 0.6); put(music, pad(mtof(45), 3.4, 1.0), 38.6, 0.25 * 1)
put(music, boom(1.6, 42, 2.5), 41.02, 1.0)
# "They were him." - the last hit, then nothing
put(music, boom(3.0, 38, 1.6), 42.30, 1.4)
music[int(37.57 * SR):int(38.50 * SR)] = 0.0                      # the twist: the music stops dead

# ---------------- SFX ----------------
sfx = np.zeros(N)
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

# shot changes (whips) - a whoosh just before each
for b in [1.37, 2.07, 6.67, 8.41, 10.90, 13.35, 14.88, 17.55, 18.78, 20.41, 27.0, 29.52, 33.66, 38.48]:
    put(sfx, whoosh(0.32), b - 0.16, 0.7)
# 1 cyclops stab
put(sfx, swish(0.3), 0.15, 0.6); put(sfx, impact(0.6), 0.52, 1.0); put(sfx, growl(0.9), 0.62, 0.8)
# 2 witch zap; 3 ghosts and a sword
put(sfx, zap(0.45), 1.47, 0.7); put(sfx, wail(0.9, 560), 2.15, 0.45); put(sfx, wail(0.8, 430), 2.5, 0.35)
put(sfx, swish(0.25), 2.62, 0.7); put(sfx, poof(0.35), 2.87, 0.6)
# 4 the monster
put(sfx, boom(1.5, 40, 3), 3.90, 0.9); put(sfx, lp(noise(1.6), 400) * env(int(1.6 * SR), 0.6, 0.3), 4.3, 0.25)
# 5 Troy burning
fire = lp(noise(1.8), 2000) * (0.4 + 0.6 * (rng.random(int(1.8 * SR)) > 0.995)); put(sfx, fire * env(len(fire), 0.1, 0.3), 6.70, 0.35)
put(sfx, steps(1.6, 4), 6.8, 0.5)
# 6 sea and gulls
for at in [8.8, 9.7]: put(sfx, wail(0.35, 1500), at, 0.25)          # gulls
put(sfx, lp(noise(2.4), 500) * env(int(2.4 * SR), 0.5, 0.6), 8.45, 0.4)
# 7 cyclops eats
put(sfx, whoosh(0.3), 11.0, 0.8); put(sfx, chomp(), 11.70, 0.9); put(sfx, chomp(), 11.95, 0.8); put(sfx, chomp(), 12.2, 0.7); put(sfx, gulp(), 12.45, 0.8)
put(sfx, clang(), 12.95, 0.6); put(sfx, boing(0.5), 12.98, 0.3)
# 8 giants
put(sfx, whoosh(0.5), 13.5, 0.7); put(sfx, crash(0.8), 13.90, 1.0); put(sfx, splash(1.0), 13.95, 0.8)
# 9 pigs
put(sfx, zap(0.5), 15.32, 0.7)
for i in range(3): put(sfx, poof(0.4), 15.85 + i * 0.05, 0.7)
put(sfx, oink(0.22, 300), 16.55, 0.9); put(sfx, oink(0.2, 360), 16.85, 0.8); put(sfx, oink(0.25, 260), 17.15, 0.7)
# 10 ghosts say hello
put(sfx, wail(0.7, 480), 17.7, 0.4); put(sfx, wail(0.6, 620), 18.0, 0.3)
# 11 sirens
put(sfx, siren_song(1.7), 18.9, 0.9); put(sfx, creak(0.6, 260), 19.2, 0.6)
# 12 cattle
put(sfx, steps(0.9, 7) , 20.5, 0.35); put(sfx, moo(0.9), 21.50, 0.7); put(sfx, thunder(1.4), 22.0, 0.6); put(sfx, growl(0.6), 22.05, 0.5)
# 13 storm
put(sfx, crack(0.4), 23.12, 1.0); put(sfx, thunder(2.2), 23.15, 1.0); put(sfx, crash(0.6), 23.6, 0.7)
for at in [23.9, 24.1, 24.3]: put(sfx, splash(0.5), at, 0.5)
put(sfx, hp(noise(1.9), 2500) * 0.25, 23.15, 0.5)
# 14 lotus
put(sfx, gliss(0.9), 25.05, 0.8); put(sfx, munch(0.4), 25.92, 0.8); put(sfx, boing(0.8), 26.38, 0.5)
# 15 seven years: clock ticks speeding up, a chime on "seven"
tt = 27.2
for i in range(26): put(sfx, tick(0.04), tt, 0.5); tt += max(0.04, 0.12 - i * 0.004)
put(sfx, chime(1975, 1.2), 28.06, 0.45)
# 16 suitors
put(sfx, murmur(2.4), 29.6, 0.5); put(sfx, chime(2350, 0.8), 31.22, 0.4); put(sfx, drum(0.3, 80), 31.3, 0.5)
# 17 disguise
put(sfx, creak(1.0, 180), 32.05, 0.7); put(sfx, steps(1.4, 3), 32.2, 0.5); put(sfx, ting(3200, 0.5), 32.8, 0.35)
# 18 bow
put(sfx, creak(0.9, 220), 33.8, 0.7); put(sfx, boing(0.6), 34.55, 0.6); put(sfx, crash(0.4), 34.7, 0.4)
put(sfx, creak(0.5, 340), 35.05, 0.6); put(sfx, creak(0.5, 400), 35.5, 0.5)
# 19 the arrow and the suitors pay
put(sfx, twang(0.6), 36.02, 0.9); put(sfx, whoosh(0.4), 36.05, 0.9)
for i, at in enumerate([36.15, 36.24, 36.33, 36.42]): put(sfx, ting(2400 + i * 300, 0.4), at, 0.45)
put(sfx, crash(0.7), 36.66, 1.0); put(sfx, murmur(0.8), 36.7, 0.4)
# 20 the twist: record scratch, then silence
put(sfx, scratch(0.45), 37.50, 0.9)
# 21 war horns over the sea
put(sfx, horn(1.8), 38.75, 0.6); put(sfx, horn(1.4), 39.9, 0.5)
# 22 the last word
put(sfx, impact(0.8), 42.30, 0.7)


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
mix[int(42.72 * SR) + int(0.9 * SR):] *= 0          # silence after the final hit rings out
os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
write(os.path.join(HERE, 'audio', 'music.wav'), music); write(os.path.join(HERE, 'audio', 'sfx.wav'), sfx)
write(os.path.join(HERE, 'audio', 'mix_raw.wav'), mix); write(os.path.join(HERE, 'audio', 'bed_raw.wav'), music + sfx)
db = lambda v: 20 * np.log10(max(v, 1e-12))
print('voice gated RMS %.1f dB | music %.1f dB vs voice | sfx %.1f dB vs voice | mix peak %.1f dB' % (
    db(rv), db(gated_rms(music)) - db(rv), db(gated_rms(sfx)) - db(rv), db(np.abs(mix).max())))
