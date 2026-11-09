"""Kokoro reference clips (about 12 s each) that give Chatterbox each voice's timbre. Run with $KOKORO_PY."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voice_common import HERE, write_wav, trim
from kokoro_onnx import Kokoro

REF_TEXT = ("Some stories sound too strange to be true. This one is real, and it happened on a dusty farm "
            "at the edge of the desert, where the wheat grew tall and the nights were very quiet.")
UPBEAT_TEXT = ("Oh, you are going to love this one! It's a true story, it's completely ridiculous, "
               "and I promise you, the ending is the best part. Let's go!")
VOICES = ['bm_george', 'am_onyx', 'am_michael', 'am_fenrir', 'af_bella', 'af_heart', 'bf_emma', 'bm_fable']
kd = os.environ.get('KOKORO_DIR', '/opt/shorts/kokoro')
k = Kokoro(os.path.join(kd, 'kokoro-v1.0.onnx'), os.path.join(kd, 'voices-v1.0.bin'))
for v in VOICES:
    a, sr = k.create(REF_TEXT, voice=v, speed=1.0, lang='en-gb' if v[0] == 'b' else 'en-us')
    a = trim(np.asarray(a, np.float32), sr)
    write_wav(os.path.join(HERE, 'audio', 'voice_samples', 'refs', v + '.wav'), a / np.abs(a).max() * 0.9, sr)
    print(v, '%.1f s' % (len(a) / sr))
# an energetic read of the gravelly voice, so Chatterbox picks up a brighter delivery as well as the timbre
a, sr = k.create(UPBEAT_TEXT, voice='am_fenrir', speed=1.12, lang='en-us')
a = trim(np.asarray(a, np.float32), sr)
write_wav(os.path.join(HERE, 'audio', 'voice_samples', 'refs', 'am_fenrir_upbeat.wav'), a / np.abs(a).max() * 0.9, sr)
print('am_fenrir_upbeat', '%.1f s' % (len(a) / sr))
