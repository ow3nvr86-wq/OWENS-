"""Sound for an episode: synthesised music + cartoon SFX placed from script.json cues and the word times, mixed under
the voice: voice 0 dB, music about -20 dB under it (ducked while the voice speaks), SFX about -12 dB under it.
Writes <episode>/audio/{music,sfx,mix}.wav.   Run: $SHORTS_PY tools/audio.py episodes/<name>"""
import json, os, re, subprocess, sys, wave
import numpy as np

EP = sys.argv[1]; SR = 48000
rng = np.random.default_rng(3)
S = json.load(open(os.path.join(EP, 'script.json'))); WJ = json.load(open(os.path.join(EP, 'work', 'words.json')))
WORDS = WJ['words']
def load(p):
    return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32).astype(np.float64)
VO = load(os.path.join(EP, 'voice.wav')); N = len(VO)
norm = lambda s: re.sub(r"[^a-z0-9 ]", ' ', s.lower().replace("'", '')).split()
NORM = [''.join(norm(w['word'])) for w in WORDS]
def cue_index(cue, frm=0):
    toks = norm(str(cue))
    for i in range(frm, len(NORM)):
        if all(i + k < len(NORM) and NORM[i + k] == tk for k, tk in enumerate(toks)): return i
    raise SystemExit('cue not found: %r' % cue)
# scene starts, same rule as the compositor
starts, ptr = [], 0
for i, sc in enumerate(S['scenes']):
    idx = 0 if i == 0 else cue_index(sc['cue'], ptr); ptr = idx; starts.append((0.0 if i == 0 else WORDS[idx]['start'] - 0.06, idx))

def t_(d): return np.arange(max(1, int(d * SR))) / SR
def env(n, a, r):
    e = np.ones(n); a, r = max(1, int(a * SR)), max(1, int(r * SR)); e[:min(a, n)] = np.linspace(0, 1, min(a, n)); e[max(0, n - r):] *= np.linspace(1, 0, n - max(0, n - r)); return e
def box(x, k):
    if k <= 1: return x
    c = np.cumsum(np.concatenate([[0.0], x])); h = k // 2
    i0 = np.clip(np.arange(len(x)) - h, 0, len(x)); i1 = np.clip(np.arange(len(x)) - h + k, 0, len(x)); return (c[i1] - c[i0]) / np.maximum(1, i1 - i0)
def lp(x, fc, p=2):
    k = max(1, int(SR / fc / 2))
    for _ in range(p): x = box(x, k)
    return x
def hp(x, fc): return x - lp(x, fc)
def bp(x, a, b): return lp(hp(x, a), b)
def noise(d): return rng.standard_normal(int(d * SR))
def put(buf, x, at, g=1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(x) <= 0: return
    j = max(0, -i); x = x[j:]; i = max(0, i); n = min(len(x), len(buf) - i); buf[i:i + n] += x[:n] * g
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)

# ---------------- instruments ----------------
def pluck(f, d=0.6): t = t_(d); return sum(np.sin(2 * np.pi * f * k * t) * 0.85 ** k * np.exp(-t * (4 + 2.5 * k)) for k in range(1, 7)) * env(len(t), 0.002, 0.05)
def kick(d=0.3): t = t_(d); f = 55 * (1 + 1.2 * np.exp(-t * 30)); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)
def snare(d=0.18): t = t_(d); return hp(noise(d), 1500) * np.exp(-t * 25) * 0.7 + np.sin(2 * np.pi * 200 * t) * np.exp(-t * 30) * 0.3
def taiko(d=0.6): t = t_(d); f = 70 * (1 + 0.5 * np.exp(-t * 12)); return (np.sin(2 * np.pi * np.cumsum(f) / SR) + lp(noise(d), 300) * 0.4) * np.exp(-t * 6)
def brass(f, d): t = t_(d); x = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 9)); return lp(x, 1400) * env(len(t), 0.05, 0.12)
def flute(f, d): t = t_(d); return (np.sin(2 * np.pi * f * t * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t))) + 0.1 * np.sin(4 * np.pi * f * t)) * env(len(t), 0.04, 0.08)

def music_march(dur, bpm):
    out = np.zeros(int(dur * SR)); beat = 60 / bpm
    PROG = [50, 45, 47, 43]; MEL = [74, 76, 77, 76, 74, 72, 74, 69, 74, 77, 79, 77, 76, 74, 72, 74]
    nb = int(dur / beat)
    for b in range(nb):
        tb = b * beat; bar = (b // 4) % 4
        if b % 2 == 0: put(out, kick(), tb, 0.9)
        else: put(out, snare(), tb, 0.6)
        put(out, snare(0.06), tb + beat / 2, 0.15)
        put(out, pluck(mtof(PROG[bar] - 12 + (7 if b % 2 else 0))), tb, 0.7)
        if b % 4 == 0: put(out, taiko(), tb, 0.5)
        if b % 4 == 1:
            for n in (PROG[bar] + 12, PROG[bar] + 16 - (1 if bar in (1, 2) else 0), PROG[bar] + 19): put(out, brass(mtof(n), beat * 0.45), tb, 0.08)
        if b % 2 == 0: put(out, flute(mtof(MEL[(b // 2) % 16]), beat * 1.7), tb, 0.12)
    return out

def sq(f, d, duty=0.5):                                   # a soft square-ish lead
    t = t_(d); x = np.sign(np.sin(2 * np.pi * f * t) - (1 - 2 * duty) * 0.0); return lp(x, 3500) * env(len(t), 0.005, 0.06)
def clap(d=0.2): t = t_(d); return bp(noise(d), 900, 4000) * (np.exp(-t * 30) + 0.5 * np.exp(-np.maximum(0, t - 0.012) * 40))


def music_bouncy(dur, bpm):
    """upbeat game-show bounce: four-on-the-floor kick, claps, an octave bass, a square-lead hook"""
    out = np.zeros(int(dur * SR)); beat = 60 / bpm
    PROG = [48, 45, 41, 43]                               # C Am F G
    HOOK = [72, 76, 79, 76, 77, 76, 74, 72, 69, 72, 76, 72, 71, 74, 79, 74]
    for b in range(int(dur / beat)):
        tb = b * beat; bar = (b // 4) % 4; root = PROG[bar]
        put(out, kick(0.25), tb, 0.85)
        if b % 2: put(out, clap(), tb, 0.45)
        put(out, snare(0.04), tb + beat / 2, 0.12)
        for k, off in enumerate((0, 0.5)): put(out, pluck(mtof(root - 12 + 12 * k), 0.3), tb + off * beat, 0.5)
        if b % 2 == 0: put(out, sq(mtof(HOOK[(b // 2) % 16]), beat * 0.9, 0.25), tb, 0.07)
        if b % 4 == 0:
            for n in (root + 12, root + 16 - (1 if bar == 1 else 0), root + 19): put(out, sq(mtof(n), beat * 3.6), tb, 0.025)
    return out


# ---------------- SFX ----------------
def whoosh(d=0.3): t = t_(d); n = noise(d); return (lp(n, 1500) * 0.7 + hp(n, 600) * 0.3) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
def boing(d=0.5): t = t_(d); f = 230 + 160 * np.sin(2 * np.pi * 7 * t) * np.exp(-t * 3); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4)
def knock(): out = np.zeros(int(0.5 * SR)); [put(out, lp(noise(0.06), 900) * np.exp(-t_(0.06) * 60) + np.sin(2 * np.pi * 180 * t_(0.06)) * np.exp(-t_(0.06) * 50) * 0.5, k * 0.14) for k in range(3)]; return out
def ting(f=2600, d=0.6): t = t_(d); return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * 5) * 0.6
def gulp(d=0.3): t = t_(d); f = 300 - 220 * t / d; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
def tada(): out = np.zeros(int(0.9 * SR)); [put(out, brass(mtof(n), 0.25), i * 0.09, 0.5) for i, n in enumerate([67, 72, 76, 79])]; return out
def sting(): out = np.zeros(int(1.0 * SR)); put(out, taiko(0.8), 0, 1.0); put(out, brass(mtof(62), 0.7), 0, 0.5); put(out, brass(mtof(69), 0.7), 0, 0.3); return out
def fuse(d=1.0): t = t_(d); return hp(noise(d), 3000) * (0.5 + 0.5 * (rng.random(len(t)) > 0.97)) * env(len(t), 0.02, 0.2) * 0.6
def volley(d=1.4):
    out = np.zeros(int(d * SR))
    for k in range(22): put(out, whoosh(0.35 + rng.random() * 0.3) * (0.4 + rng.random() * 0.5), rng.random() * 0.5)
    put(out, hp(noise(d), 2500) * env(int(d * SR), 0.05, 0.6) * 0.25, 0)
    return out
def boom(d=1.4): t = t_(d); f = 45 * (1 + 0.8 * np.exp(-t * 7)); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5) + lp(noise(d), 250) * np.exp(-t * 4) * 0.7
def voiceish(f0, d, formants, vib=6):
    t = t_(d); f = f0 * (1 + 0.02 * np.sin(2 * np.pi * vib * t)); ph = 2 * np.pi * np.cumsum(f) / SR; x = np.zeros_like(t)
    for k in range(1, 26):
        w = sum(a * np.exp(-((f0 * k - F) / bw) ** 2) for F, bw, a in formants); x += np.sin(ph * k) * w / k ** 0.3
    return x * env(len(t), 0.05, 0.15)
def charge(d=1.6):
    out = np.zeros(int(d * SR))
    for k in range(14): put(out, voiceish(140 + rng.random() * 80, d * 0.7, [(700, 200, 1), (1200, 300, 0.6)], 7) * 0.35, rng.random() * d * 0.3)
    return out
def scramble(d=1.2):
    out = np.zeros(int(d * SR))
    for k in range(30): put(out, lp(noise(0.05), 700) * np.exp(-t_(0.05) * 60), k * 0.04 + rng.random() * 0.01, 0.7)
    for k in range(4): put(out, voiceish(260 + k * 40, 0.3, [(800, 200, 1), (1300, 300, 0.5)]) * 0.5, 0.1 + k * 0.25)
    return out
def sneeze():
    out = np.zeros(int(0.9 * SR)); put(out, voiceish(330, 0.3, [(900, 250, 1), (1500, 300, 0.5)]) * 0.6, 0)                   # "ah-"
    put(out, hp(noise(0.35), 1800) * np.exp(-t_(0.35) * 8) * 0.9 + voiceish(280, 0.35, [(400, 150, 1), (900, 200, 0.4)]) * 0.5, 0.38)   # "-CHOO"
    return out
def drums(d=2.5):
    out = np.zeros(int(d * SR))
    for k in range(6): put(out, taiko(), k * 0.36, 0.9 - k * 0.08)
    return out
def march_steps(d=2.0):
    out = np.zeros(int(d * SR))
    for k in range(int(d / 0.29)): put(out, lp(noise(0.08), 500) * np.exp(-t_(0.08) * 45), k * 0.29, 0.8)
    return out
def pop(): t = t_(0.08); return np.sin(2 * np.pi * 900 * t * np.exp(-t * 20)) * np.exp(-t * 50)
SFX = dict(whoosh=whoosh, boing=boing, knock=knock, ting=ting, gulp=gulp, tada=tada, sting=sting, fuse=fuse, volley=volley, boom=boom,
           charge=charge, scramble=scramble, sneeze=sneeze, drums=drums, march=march_steps, pop=pop)

style = S.get('music', {}).get('style', 'march')
music = (music_bouncy if style == 'bouncy' else music_march)(N / SR + 1, S.get('music', {}).get('bpm', 104))[:N]
sfx = np.zeros(N)
for i, sc in enumerate(S['scenes']):
    st, wi = starts[i]
    for c in sc.get('sfx', []):
        at = st + c['at'] if isinstance(c['at'], (int, float)) else WORDS[cue_index(c['at'], wi)]['start'] - 0.04
        put(sfx, SFX[c['type']](), at, c.get('gain', 1.0))
    if sc.get('transition') in ('whip', 'zoom') and i + 1 < len(starts): put(sfx, whoosh(0.32), starts[i + 1][0] - 0.16, 0.8)
# levels: music ~-20 dB under the voice (ducked while speaking), SFX ~-12 dB
def grms(x):
    b, h = int(0.4 * SR), int(0.1 * SR); e = np.array([np.mean(x[i:i + b] ** 2) for i in range(0, max(1, len(x) - b), h)])
    e = e[e > 1e-7]; e = e[e > np.mean(e) * 0.1] if len(e) else e; return float(np.sqrt(np.mean(e))) if len(e) else 1e-9
rv = grms(VO)
level = S.get('music', {}).get('level_db', -20)
music *= 10 ** ((level + 2.5) / 20) * rv / grms(music)                     # about -17.5 dB in the gaps ...
ve = lp(np.abs(VO), 6, 3); ve = np.clip(ve / max(1e-9, np.percentile(ve, 95)), 0, 1)
music *= 1 - 0.37 * ve                                                     # ... about -20 dB under speech
sfx *= 10 ** (-12 / 20) * rv / max(1e-9, grms(sfx)); sfx = np.clip(sfx, -0.95 * np.abs(VO).max(), 0.95 * np.abs(VO).max())
mix = VO + music + sfx
def write(p, x):
    with wave.open(p, 'wb') as w: w.setnchannels(1); w.setsampwidth(4); w.setframerate(SR); w.writeframes((np.clip(x, -1.99, 1.99) / 2 * 2147483647).astype('<i4').tobytes())
os.makedirs(os.path.join(EP, 'audio'), exist_ok=True)
for n, x in [('music', music), ('sfx', sfx), ('mix', mix)]: write(os.path.join(EP, 'audio', n + '.wav'), x)
db = lambda v: 20 * np.log10(max(v, 1e-12))
print('music %.1f dB vs voice (gated), sfx %.1f dB vs voice' % (db(grms(music)) - db(rv), db(grms(sfx)) - db(rv)))
