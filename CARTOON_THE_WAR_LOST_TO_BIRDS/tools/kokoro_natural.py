"""Kokoro read with the less-robotic pipeline: one clip per script LINE (not per sentence, so intonation carries
across short sentences), a slightly different pace per line, varied pauses and the finishing chain.
Run with $KOKORO_PY: tools/kokoro_natural.py VOICE OUT.wav"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voice_common import HERE, LINES, pause_after, trim, write_wav, finish
from kokoro_onnx import Kokoro

voice, out = sys.argv[1], sys.argv[2]
SPEED = [1.12, 1.08, 1.12, 1.06, 1.10, 1.10, 1.0]     # hook brisk, the plan and the payoff a touch slower
kd = os.environ.get('KOKORO_DIR', '/opt/shorts/kokoro')
k = Kokoro(os.path.join(kd, 'kokoro-v1.0.onnx'), os.path.join(kd, 'voices-v1.0.bin'))
parts, sr = [np.zeros(2400, np.float32)], 24000
for i, line in enumerate(LINES):
    a, sr = k.create(line, voice=voice, speed=SPEED[i], lang='en-gb' if voice[0] == 'b' else 'en-us')
    parts += [trim(np.asarray(a, np.float32), sr), np.zeros(int(pause_after(i) * sr), np.float32)]
a = np.concatenate(parts + [np.zeros(int(0.3 * sr), np.float32)])
tmp = out + '.raw.wav'
write_wav(tmp, a / np.abs(a).max() * 0.9, sr); finish(tmp, out); os.remove(tmp)
print(out, '%.2f s' % (len(a) / sr))
