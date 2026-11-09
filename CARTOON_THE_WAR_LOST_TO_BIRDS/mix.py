"""Level lock: music at exactly 50 % of the voice's gated RMS (-6 dB) and SFX at 50 % with peaks capped at 0.7 x the
voice peak. No ducking or compression: the only processing is one gain per stem (plus the SFX peak cap).
Run: $SHORTS_PY mix.py audio/voice_user.mp3 audio/music.wav audio/sfx.wav  -> audio/mix_raw.wav, audio/bed_raw.wav"""
import subprocess, sys, os, wave, json
import numpy as np
SR = 48000
def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
def gated_rms(x):
    """RMS over 400 ms blocks (75 % overlap), ignoring silent blocks: absolute gate -60 dBFS, then a relative gate
    10 dB below the mean of the remaining blocks (the EBU R128 gating idea, without K-weighting)."""
    b, h = int(0.4 * SR), int(0.1 * SR)
    e = np.array([np.mean(x[i:i + b] ** 2) for i in range(0, max(1, len(x) - b), h)])
    e = e[e > 10 ** (-60 / 10)]
    if not len(e): return 1e-9
    e = e[e > np.mean(e) * 10 ** (-10 / 10)]
    return float(np.sqrt(np.mean(e)))
db = lambda v: 20 * np.log10(max(v, 1e-12))
v, m, s = (load(p) for p in sys.argv[1:4])
n = len(v); m = np.pad(m, (0, max(0, n - len(m))))[:n]; s = np.pad(s, (0, max(0, n - len(s))))[:n]
rv, pv = gated_rms(v), np.abs(v).max()
gm = 0.5 * rv / gated_rms(m)
gs = 0.5 * rv / gated_rms(s)
m2 = m * gm
s2 = s * gs
cap = 0.7 * pv
s2 = np.clip(s2, -cap, cap)                       # peak cap: no hit pokes out over the narration
mix = v + m2 + s2
rep = dict(voice_gated_rms_db=round(db(rv), 2), voice_peak_db=round(db(pv), 2),
           music_vs_voice_db=round(db(gated_rms(m2)) - db(rv), 2), sfx_vs_voice_db=round(db(gated_rms(s2)) - db(rv), 2),
           sfx_peak_vs_voice_peak=round(np.abs(s2).max() / pv, 3), mix_peak_db=round(db(np.abs(mix).max()), 2))
for k, val in rep.items(): print('%-24s %s' % (k, val))
def write(p, x):
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(4); w.setframerate(SR)
        w.writeframes((np.clip(x, -1.99, 1.99) / 2 * 2147483647).astype('<i4').tobytes())   # 32-bit, half scale (headroom)
here = os.path.dirname(os.path.abspath(__file__))
write(os.path.join(here, 'audio', 'mix_raw.wav'), mix)
write(os.path.join(here, 'audio', 'bed_raw.wav'), m2 + s2)
json.dump(rep, open(os.path.join(here, 'audio', 'mix_levels.json'), 'w'), indent=1)
