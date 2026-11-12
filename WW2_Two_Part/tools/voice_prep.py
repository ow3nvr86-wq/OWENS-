"""Prepare the supplied voiceover for a part: decode it, shorten pauses longer than MAX_PAUSE (only silence is cut,
with short crossfades, so no word is touched), and normalise its level.

  python tools/voice_prep.py part1      -> part1/audio/narration.wav (48 kHz mono), prints the duration
"""
import os
import subprocess
import sys
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
MAX_PAUSE = 0.40
LEAD = 0.08


def main():
    part = sys.argv[1] if len(sys.argv) > 1 else 'part1'
    d = os.path.join(ROOT, part)
    src = [f for f in sorted(os.listdir(os.path.join(d, 'voiceover'))) if f.lower().endswith(('.mp3', '.m4a', '.wav'))][0]
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(d, 'voiceover', src), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    a /= np.abs(a).max() + 1e-9
    e = np.convolve(np.abs(a), np.ones(int(0.012 * SR)) / (0.012 * SR), 'same')
    q = e < 0.012
    nz = np.nonzero(~q)[0]
    a, q = a[max(0, nz[0] - int(0.03 * SR)): nz[-1] + int(0.15 * SR)], q[max(0, nz[0] - int(0.03 * SR)): nz[-1] + int(0.15 * SR)]
    out, last, i, cut = [], 0, 0, 0.0
    tgt = int(MAX_PAUSE * SR)
    while i < len(q):
        if q[i]:
            j = i
            while j < len(q) and q[j]:
                j += 1
            if i > 0 and j < len(q) and j - i > tgt:
                mid = i + tgt // 2
                out.append(a[last:mid])
                last = j - (tgt - tgt // 2)
                cut += (j - i - tgt) / SR
            i = j
        else:
            i += 1
    out.append(a[last:])
    f = int(0.008 * SR)
    for k in range(len(out)):                      # tiny fades at each join
        if k:
            out[k][:f] *= np.linspace(0, 1, f)
        if k < len(out) - 1:
            out[k][-f:] *= np.linspace(1, 0, f)
    y = np.concatenate([np.zeros(int(LEAD * SR), np.float32)] + out)
    y *= 0.89 / (np.abs(y).max() + 1e-9)
    os.makedirs(os.path.join(d, 'audio'), exist_ok=True)
    with wave.open(os.path.join(d, 'audio', 'narration.wav'), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f'{src}: {len(a) / SR:.2f} s -> {len(y) / SR:.2f} s (pauses over {MAX_PAUSE} s shortened, {cut:.2f} s removed)')


if __name__ == '__main__':
    main()
