"""Narration, subtitles and script for the September 11 Short.

Reads ../scene_timing.json, synthesises every narration line with a local synthetic voice
(Kokoro-82M, voice bm_george, Apache-2.0), fits each line into its slot, and writes:
  audio/narration.wav     the full-length voice track (48 kHz mono)
  build/vo_timing.json    measured line and caption-chunk times (read by the renderer and the audio stage)
  subtitles.srt           subtitles from the measured times
  script.txt              the narration script with start and end times

  $KOKORO_PY tools/voiceover.py              # Kokoro bm_george
  $KOKORO_PY tools/voiceover.py --no-tts     # timing estimate only (2.7 words/s), no voice model needed
"""
import argparse
import json
import os
import re
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
BASE_SCALE = 0.87   # George at 1.15x: serious, measured and unhurried
MIN_SCALE = 0.80

HOOKS = [
    ('A', 'The ordinary morning (CHOSEN)',
     'Picture: a clear blue September sky over the Hudson, a ferry, the Twin Towers catching the sun, the date typed in. '
     'Voice: "At 8:46 a.m., an ordinary morning changed forever." The calm image and the exact time open the question '
     '"what happened at 8:46?", which the next scene answers on a clock.'),
    ('B', 'The minute before',
     'A clock reading 8:45 over the calm skyline, ticking. "In one minute, this skyline would change forever." Strong '
     'suspense, but it spends two seconds on a clock instead of the city.'),
    ('C', '102 minutes',
     '"In 102 minutes, the New York skyline changed forever." (8:46 to the North Tower\'s collapse at 10:28.) Precise and '
     'striking, but a number means little until the viewer knows what it measures.'),
]


def load_timing():
    with open(os.path.join(ROOT, 'scene_timing.json')) as fh:
        return json.load(fh)


class KokoroVoice:
    def __init__(self, model_dir, name):
        from kokoro_onnx import Kokoro
        self.k = Kokoro(os.path.join(model_dir, 'kokoro-v1.0.onnx'), os.path.join(model_dir, 'voices-v1.0.bin'))
        self.name = name
        self.lang = 'en-gb' if name[:1] == 'b' else 'en-us'

    def synth(self, text, scale):
        a, sr = self.k.create(text, voice=self.name, speed=1.0 / scale, lang=self.lang)
        a = np.asarray(a, np.float32)
        nz = np.nonzero(np.abs(a) > 0.01)[0]
        a = a[max(nz[0] - int(0.02 * sr), 0): nz[-1] + int(0.06 * sr)]
        n = int(len(a) * SR / sr)
        return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)


def chunks(text, max_words=3, max_chars=17):
    """Split a caption line into short phrases, breaking after punctuation."""
    words = text.replace('"', '').split()
    out, cur = [], []
    for w in words:
        trial = ' '.join(cur + [w])
        if cur and (len(cur) >= max_words or len(trial) > max_chars):
            out.append(cur)
            cur = []
        cur.append(w)
        if re.search(r'[.,:;?!]$', w) and len(' '.join(cur)) >= 4:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [' '.join(c) for c in out]


def weight(s):
    # characters, plus extra weight for the pauses the voice makes at punctuation
    return len(s) + 6 * len(re.findall(r'[,:;]', s)) + 9 * len(re.findall(r'[.?!]', s)) + 10 * s.count('...')


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def write_wav(path, a):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kokoro-voice', default='bm_george')
    ap.add_argument('--kokoro-dir', default=os.environ.get('KOKORO_DIR', '/opt/shorts/kokoro'))
    ap.add_argument('--no-tts', action='store_true')
    args = ap.parse_args()
    T = load_timing()
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'audio'), exist_ok=True)
    voice = None if args.no_tts else KokoroVoice(args.kokoro_dir, args.kokoro_voice)
    voice_name = None if voice is None else f'Kokoro-82M {args.kokoro_voice}'
    track = np.zeros(int(T['duration'] * SR), np.float32)
    timed = []
    for i, ln in enumerate(T['lines']):
        slot = ln['deadline'] - ln['start']
        if voice is None:
            dur, scale = len(ln['text'].split()) / 2.7, None
        else:
            scale = BASE_SCALE
            a = voice.synth(ln['tts'], scale)
            for _ in range(4):
                if len(a) / SR <= slot or scale <= MIN_SCALE:
                    break
                scale = max(MIN_SCALE, scale * slot / (len(a) / SR) * 0.985)
                a = voice.synth(ln['tts'], scale)
            dur = len(a) / SR
            s0 = int(ln['start'] * SR)
            track[s0:s0 + len(a)] += a[:len(track) - s0]
            write_wav(os.path.join(ROOT, 'build', f'vo_{i:02d}.wav'), a)
        end = ln['start'] + dur
        cs = chunks(ln['text'])
        ws = np.array([weight(c) for c in cs], float)
        edges = ln['start'] + np.concatenate([[0], np.cumsum(ws)]) / ws.sum() * dur
        timed.append({'scene': ln['scene'], 'text': ln['text'], 'start': round(ln['start'], 3),
                      'end': round(end, 3), 'length_scale': scale, 'hl': ln.get('hl', []),
                      'chunks': [{'text': c, 'start': round(edges[k], 3), 'end': round(edges[k + 1], 3)}
                                 for k, c in enumerate(cs)]})
        flag = f'  OVER DEADLINE by {end - ln["deadline"]:.2f}s' if end > ln['deadline'] else ''
        print(f'line {i} {ln["start"]:6.2f}-{end:6.2f}s scale={scale}{flag}  {ln["text"]}')
    if voice is not None:
        track *= 0.89 / max(np.abs(track).max(), 1e-6)
        write_wav(os.path.join(ROOT, 'audio', 'narration.wav'), track)
    with open(os.path.join(ROOT, 'build', 'vo_timing.json'), 'w') as fh:
        json.dump({'voice': voice_name, 'lines': timed}, fh, indent=1)

    with open(os.path.join(ROOT, 'subtitles.srt'), 'w') as fh:
        n = 1
        for ln in timed:
            for c in ln['chunks']:
                fh.write(f'{n}\n{srt_time(c["start"])} --> {srt_time(c["end"])}\n{c["text"]}\n\n')
                n += 1

    words = sum(len(l['text'].split()) for l in timed)
    with open(os.path.join(ROOT, 'script.txt'), 'w') as fh:
        fh.write(f'SEPTEMBER 11, 2001: THE DAY THE WORLD STOOD STILL - NARRATION SCRIPT ({T["duration"]:.1f} s, {words} words)\n')
        fh.write(f'Voice: {voice_name or "not synthesised"}. Times are measured from the synthesised voice.\n')
        fh.write('Delivery: serious, calm, respectful documentary tone; never dramatic; let the short sentences land.\n\n')
        fh.write('OPENING HOOKS (three candidates)\n')
        for k, name, desc in HOOKS:
            fh.write(f'  {k}. {name}: {desc}\n')
        fh.write('\n')
        for sc in T['scenes']:
            fh.write(f'[SCENE {sc["id"]} - {sc["name"]}  {sc["start"]:.1f}-{sc["end"]:.1f} s]\n')
            for ln in timed:
                if ln['scene'] == sc['id']:
                    fh.write(f'({ln["start"]:05.2f}-{ln["end"]:05.2f}) {ln["text"]}\n')
            fh.write('\n')
        fh.write(f'Total: {words} words. Every line is checked against sources.txt (section 4).\n')


if __name__ == '__main__':
    main()
