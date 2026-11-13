"""Voice: keep <episode>/voice.wav if you recorded one; otherwise synthesise narration.txt with Kokoro (TTS fallback).
Run: $KOKORO_PY tools/voice.py episodes/<name> [--voice bm_george] [--speed 1.08]"""
import argparse, os, re, subprocess, wave
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument('episode'); ap.add_argument('--voice', default='bm_george'); ap.add_argument('--speed', type=float, default=1.08)
ap.add_argument('--force', action='store_true'); a = ap.parse_args()
out = os.path.join(a.episode, 'voice.wav')
if os.path.exists(out) and not a.force:
    print('using your recording:', out); raise SystemExit
from kokoro_onnx import Kokoro
kd = os.environ.get('KOKORO_DIR', '/opt/shorts/kokoro')
k = Kokoro(os.path.join(kd, 'kokoro-v1.0.onnx'), os.path.join(kd, 'voices-v1.0.bin'))
lines = [l.strip() for l in open(os.path.join(a.episode, 'narration.txt')) if l.strip()]
def trim(x, sr, thr=0.012, pad=0.03):
    i = np.where(np.abs(x) > thr)[0]
    return x if not len(i) else x[max(0, i[0] - int(pad * sr)): i[-1] + int(pad * sr)]
parts, sr = [], 24000
for i, line in enumerate(lines):
    x, sr = k.create(line, voice=a.voice, speed=a.speed, lang='en-gb' if a.voice[0] == 'b' else 'en-us')
    parts += [np.zeros(int(0.12 * sr) if i == 0 else 0), trim(np.asarray(x, np.float32), sr), np.zeros(int((0.42 if line.endswith('?') else 0.30) * sr))]
v = np.concatenate(parts + [np.zeros(int(0.6 * sr))]); v = v / np.abs(v).max() * 0.89
tmp = out + '.24k.wav'
with wave.open(tmp, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((v * 32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-ar', '48000', out], check=True); os.remove(tmp)
print('TTS voice written:', out, '%.1f s' % (len(v) / sr))
