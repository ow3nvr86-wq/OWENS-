"""Narration for The War Lost to Birds: Kokoro-82M voice bm_george, one clip per sentence, trimmed and joined
with fixed pauses. Writes audio/voice.wav (48 kHz mono) and audio/voice_timing.json (sentence start/end times).
Run: $KOKORO_PY tools/voiceover.py [--speed 1.0]"""
import argparse, json, os, re
import numpy as np
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('--speed', type=float, default=1.1)
ap.add_argument('--kokoro-dir', default=os.environ.get('KOKORO_DIR', '/opt/shorts/kokoro'))
args = ap.parse_args()

text = open(os.path.join(HERE, 'script.txt')).read()
sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
k = Kokoro(os.path.join(args.kokoro_dir, 'kokoro-v1.0.onnx'), os.path.join(args.kokoro_dir, 'voices-v1.0.bin'))

def trim(a, sr, thr=0.012, pad=0.03):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return a
    return a[max(0, idx[0] - int(pad * sr)): idx[-1] + int(pad * sr)]

LEAD = 0.10                       # silence before the first word
out, timing, t, sr0 = [], [], LEAD, None
for i, s in enumerate(sents):
    a, sr = k.create(s, voice='bm_george', speed=args.speed, lang='en-gb')
    sr0 = sr
    a = trim(np.asarray(a, dtype=np.float32), sr)
    if i == 0:
        out.append(np.zeros(int(LEAD * sr), np.float32))
    out.append(a)
    timing.append(dict(i=i, text=s, start=round(t, 3), end=round(t + len(a) / sr, 3)))
    t += len(a) / sr
    nxt = sents[i + 1] if i + 1 < len(sents) else None
    # short beat inside a line pair, longer at line ends, longest before the payoff
    gap = 0.0 if nxt is None else (0.45 if nxt == 'Per bird.' else 0.24)
    out.append(np.zeros(int(gap * sr), np.float32)); t += gap
out.append(np.zeros(int(0.25 * sr0), np.float32))
v = np.concatenate(out)
v = v / max(1e-6, np.abs(v).max()) * 0.89
import wave
pcm = (np.clip(v, -1, 1) * 32767).astype('<i2')
tmp = os.path.join(HERE, 'audio', 'voice_24k.wav')
with wave.open(tmp, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr0); w.writeframes(pcm.tobytes())
os.system(f'ffmpeg -v error -y -i "{tmp}" -ar 48000 "{os.path.join(HERE, "audio", "voice.wav")}" && rm "{tmp}"')
json.dump(dict(voice='Kokoro-82M bm_george', speed=args.speed, duration=round(len(v) / sr0, 3), sentences=timing),
          open(os.path.join(HERE, 'audio', 'voice_timing.json'), 'w'), indent=1)
print('duration %.2f s' % (len(v) / sr0))
for s in timing:
    print('%6.2f %6.2f  %s' % (s['start'], s['end'], s['text']))
