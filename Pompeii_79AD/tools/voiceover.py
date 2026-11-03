"""Narration, subtitles and timing docs for the Pompeii Short.

Reads ../scene_timing.json, synthesises each narration line with a local, synthetic voice -
Kokoro-82M voice bm_george (Apache-2.0, default) or Piper en_US-joe-medium (CC0) - fits every
line into its slot, and writes:
  audio/narration.wav      full-length 60 s voice track (48 kHz mono) - import into CapCut or keep
  build/vo_timing.json     measured line + caption-chunk times (read by animation.py)
  subtitles.srt            subtitles from the measured times
  script.txt               the narration script, scene by scene, with start times
  storyboard.txt           scene-by-scene storyboard: visuals, camera, narration, on-screen text

  $KOKORO_PY tools/voiceover.py                           # Kokoro, bm_george (default)
  $KOKORO_PY tools/voiceover.py --kokoro-voice am_michael
  $SHORTS_PY tools/voiceover.py --engine piper [--voice /path/en_US-joe-medium.onnx]
  $SHORTS_PY tools/voiceover.py --no-tts

--no-tts skips synthesis and uses an estimate of 2.7 words/s instead, so the timing files can be
made without a voice model (e.g. when the narration will be recorded later in CapCut).
"""
import argparse
import json
import os
import re
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
BASE_SCALE = 0.87    # George reads at 1.15x: a measured, serious pace that fits the 60 s
MIN_SCALE = 0.80


def load_timing():
    with open(os.path.join(ROOT, 'scene_timing.json')) as fh:
        return json.load(fh)


class KokoroVoice:
    """Kokoro-82M via kokoro-onnx; length_scale maps to 1/speed like Piper's."""
    def __init__(self, model_dir, name):
        from kokoro_onnx import Kokoro
        self.k = Kokoro(os.path.join(model_dir, 'kokoro-v1.0.onnx'), os.path.join(model_dir, 'voices-v1.0.bin'))
        self.name = name
        self.lang = 'en-gb' if name[:1] == 'b' else 'en-us'

    def synth(self, text, scale):
        a, sr = self.k.create(text, voice=self.name, speed=1.0 / scale, lang=self.lang)
        return np.asarray(a, np.float32), sr


def synth(voice, text, scale):
    if isinstance(voice, KokoroVoice):
        a, sr = voice.synth(text, scale)
    else:
        from piper import SynthesisConfig
        tmp = os.path.join(ROOT, 'build', '_tmp.wav')
        with wave.open(tmp, 'wb') as w:
            voice.synthesize_wav(text, w, syn_config=SynthesisConfig(length_scale=scale))
        with wave.open(tmp) as w:
            sr = w.getframerate()
            a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        os.remove(tmp)
    nz = np.nonzero(np.abs(a) > 0.01)[0]
    a = a[max(nz[0] - int(0.02 * sr), 0): nz[-1] + int(0.06 * sr)]
    # resample to 48 kHz (linear interpolation is fine for speech at this ratio)
    n = int(len(a) * SR / sr)
    a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a)
    return a.astype(np.float32)


def chunks(text, max_words=3, max_chars=18):
    """Split a caption line into short phrases, breaking after punctuation."""
    words = text.replace('"', '').split()
    out, cur = [], []
    for w in words:
        trial = ' '.join(cur + [w])
        if cur and (len(cur) >= max_words or len(trial) > max_chars):
            out.append(cur)
            cur = []
        cur.append(w)
        if re.search(r'[.,:;?!]$', w) and len(' '.join(cur)) >= 6:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [' '.join(c) for c in out]


def weight(s):
    # characters plus extra weight for the pauses Piper makes at punctuation
    return len(s) + 6 * len(re.findall(r'[,:;]', s)) + 9 * len(re.findall(r'[.?!]', s))


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine', choices=['kokoro', 'piper'], default='kokoro')
    ap.add_argument('--kokoro-voice', default='bm_george')
    ap.add_argument('--kokoro-dir', default=os.environ.get('KOKORO_DIR', '/opt/shorts/kokoro'))
    ap.add_argument('--voice', default=os.path.join(os.environ.get('PIPER_VOICES', '/opt/shorts/piper-voices'),
                                                    'en_US-joe-medium.onnx'))
    ap.add_argument('--no-tts', action='store_true')
    args = ap.parse_args()
    T = load_timing()
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'audio'), exist_ok=True)
    voice = None
    if not args.no_tts and args.engine == 'kokoro':
        voice = KokoroVoice(args.kokoro_dir, args.kokoro_voice)
        voice_name = f'Kokoro-82M {args.kokoro_voice}'
    elif not args.no_tts:
        from piper import PiperVoice
        voice = PiperVoice.load(args.voice)
        voice_name = f'Piper {os.path.basename(args.voice)}'
    else:
        voice_name = None
    track = np.zeros(int(T['duration'] * SR), np.float32)
    timed = []
    for i, ln in enumerate(T['lines']):
        slot = ln['deadline'] - ln['start']
        if voice is None:
            dur, scale = len(ln['text'].split()) / 2.7, None
        else:
            scale = BASE_SCALE
            a = synth(voice, ln['tts'], scale)
            for _ in range(4):
                if len(a) / SR <= slot or scale <= MIN_SCALE:
                    break
                scale = max(MIN_SCALE, scale * slot / (len(a) / SR) * 0.985)
                a = synth(voice, ln['tts'], scale)
            dur = len(a) / SR
            s0 = int(ln['start'] * SR)
            track[s0:s0 + len(a)] += a[:len(track) - s0]
            with wave.open(os.path.join(ROOT, 'build', f'vo_{i:02d}.wav'), 'wb') as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(SR)
                w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
        end = ln['start'] + dur
        over = end - ln['deadline']
        cs = chunks(ln['text'])
        ws = np.array([weight(c) for c in cs], float)
        edges = ln['start'] + np.concatenate([[0], np.cumsum(ws)]) / ws.sum() * dur
        timed.append({'scene': ln['scene'], 'text': ln['text'], 'start': round(ln['start'], 3),
                      'end': round(end, 3), 'length_scale': scale,
                      'chunks': [{'text': c, 'start': round(edges[k], 3), 'end': round(edges[k + 1], 3)}
                                 for k, c in enumerate(cs)]})
        flag = f'  OVER DEADLINE by {over:.2f}s' if over > 0 else ''
        print(f'line {i:2d} {ln["start"]:6.2f}-{end:6.2f}s  scale={scale}{flag}  {ln["text"]}')
    peak = np.abs(track).max()
    if voice is not None:
        track *= 0.89 / max(peak, 1e-6)
        with wave.open(os.path.join(ROOT, 'audio', 'narration.wav'), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())
    with open(os.path.join(ROOT, 'build', 'vo_timing.json'), 'w') as fh:
        json.dump({'voice': voice_name, 'lines': timed}, fh, indent=1)

    # subtitles.srt: one cue per caption phrase
    with open(os.path.join(ROOT, 'subtitles.srt'), 'w') as fh:
        n = 1
        for ln in timed:
            for c in ln['chunks']:
                fh.write(f'{n}\n{srt_time(c["start"])} --> {srt_time(c["end"])}\n{c["text"]}\n\n')
                n += 1

    words = sum(len(l['text'].split()) for l in timed)
    # script.txt
    with open(os.path.join(ROOT, 'script.txt'), 'w') as fh:
        fh.write(f'THE DAY POMPEII DISAPPEARED - NARRATION SCRIPT (60 seconds, {words} words)\n')
        fh.write(f'Voice: {voice_name or "not synthesised"}. Start and end times are measured from the synthesised voice.\n')
        fh.write('Read as a serious, suspenseful documentary: low, measured, unhurried; let the short sentences land.\n\n')
        for sc in T['scenes']:
            fh.write(f'[SCENE {sc["id"]} - {sc["name"]}  {sc["start"]:.1f}-{sc["end"]:.1f} s]\n')
            for ln in timed:
                if ln['scene'] == sc['id']:
                    fh.write(f'({ln["start"]:05.2f}-{ln["end"]:05.2f}) {ln["text"]}\n')
            fh.write('\n')
        fh.write(f'Total: {words} words.\n')

    # storyboard.txt
    L = ['THE DAY POMPEII DISAPPEARED - STORYBOARD AND EDITING INSTRUCTIONS',
         '=' * 60, '',
         f'60 s, 1080x1920 (9:16), 30 fps. The 3D render covers 0-{T["render_end"]:.0f} s; the last second is black with the end title.',
         'Generated by tools/voiceover.py from scene_timing.json (the single source of truth for every cut, title and event).',
         'Every shot is rendered in Blender from animation.py; transitions, titles, captions, grain and vignette are added in its edit stage.', '']
    for sc in T['scenes']:
        f0, f1 = round(sc['start'] * 30) + 1, round(sc['end'] * 30)
        L.append(f'SCENE {sc["id"]} - {sc["name"]}  ({sc["start"]:.1f}-{sc["end"]:.1f} s, frames {f0}-{f1})')
        L.append('-' * 60)
        L.append('Visual: ' + sc['desc'])
        for sh in sc['shots']:
            L.append(f'  Shot "{sh["name"]}" {sh["start"]:.1f}-{sh["end"]:.1f} s (frames {round(sh["start"] * 30) + 1}-{round(sh["end"] * 30)}): {sh.get("camera", "")}')
        for ln in timed:
            if ln['scene'] == sc['id']:
                L.append(f'  VO {ln["start"]:.2f}-{ln["end"]:.2f}: "{ln["text"]}"')
        for t in T['titles']:
            if sc['start'] <= t['start'] < sc['end']:
                L.append(f'  TEXT {t["start"]:.1f}-{t["end"]:.1f} [{t["style"]}]: {t["text"].replace("|", " / ")}')
        for k, v in T['events'].items():
            if sc['start'] <= v[0] < sc['end']:
                L.append(f'  EVENT {v[0]:.2f}-{v[1]:.2f}: {k}')
        if sc.get('edit'):
            L.append('  Edit: ' + sc['edit'])
        L.append('')
    with open(os.path.join(ROOT, 'storyboard.txt'), 'w') as fh:
        fh.write('\n'.join(L) + '\n')
    print('wrote audio/narration.wav, build/vo_timing.json, subtitles.srt, script.txt, storyboard.txt')


if __name__ == '__main__':
    main()
