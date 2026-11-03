"""Narration, subtitles and timing docs for the Short "What If Money Grew on Trees?".

Reads ../scene_timing.json, synthesises each narration line with a local, synthetic voice -
Kokoro-82M voice bm_george (Apache-2.0, default) or Piper en_US-joe-medium (CC0) - fits every
line into its slot, and writes:
  audio/narration.wav      full-length voice track (48 kHz mono) - import into CapCut or keep
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
BASE_SCALE = 0.87    # George reads at 1.15x: a calm, serious documentary pace
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


SPOKEN = {}   # caption word -> what is actually said (filled from each line's tts text)


def spoken_len(word):
    w = SPOKEN.get(word, word)
    return len(w) + 1 + 6 * len(re.findall(r'[,:;]', w)) + 9 * len(re.findall(r'[.?!]', w))


def pauses(a, min_len=0.07):
    """Silent stretches inside a synthesised line (seconds from its start)."""
    hop = int(0.01 * SR)
    n = len(a) // hop
    rms = np.sqrt(np.mean(a[:n * hop].reshape(n, hop) ** 2, axis=1))
    quiet = rms < max(0.012, 0.06 * rms.max())
    out, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) * 0.01 >= min_len and i > 3 and j < n - 3:
                out.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    return out


def word_times(text, dur, gaps):
    """Per-word (start, end) for a caption line. Phrase breaks (after punctuation) are snapped to real pauses in
    the audio; inside a phrase, words share the time by spoken length."""
    words = text.replace('"', '').split()
    w = np.array([spoken_len(x) for x in words], float)
    cum = np.concatenate([[0], np.cumsum(w)]) / w.sum() * dur
    anchors = [(0, 0.0, 0.0)]           # (word index, phrase start time, previous phrase end time)
    used = set()
    for k, x in enumerate(words[:-1]):
        if re.search(r'[.,?!:;]$', x):
            est = cum[k + 1]
            best = None
            for gi, (g0, g1) in enumerate(gaps):
                if gi in used:
                    continue
                d = abs((g0 + g1) / 2 - est)
                if d < 0.6 and (best is None or d < best[0]):
                    best = (d, gi)
            if best is not None:
                used.add(best[1])
                g0, g1 = gaps[best[1]]
                anchors.append((k + 1, g1, g0))
            else:
                anchors.append((k + 1, est, est))
    anchors.append((len(words), dur, dur))
    out = []
    for (i0, t0, _), (i1, _, t1e) in zip(anchors[:-1], anchors[1:]):
        ww = w[i0:i1]
        e = t0 + np.concatenate([[0], np.cumsum(ww)]) / ww.sum() * max(t1e - t0, 0.05)
        out += [(words[i0 + j], float(e[j]), float(e[j + 1])) for j in range(i1 - i0)]
    return out


def group_chunks(wt, max_words=3, max_chars=17):
    out, cur = [], []
    for item in wt:
        trial = ' '.join([c[0] for c in cur] + [item[0]])
        if cur and (len(cur) >= max_words or len(trial) > max_chars):
            out.append(cur)
            cur = []
        cur.append(item)
        if re.search(r'[.,:;?!]$', item[0]) and len(' '.join(c[0] for c in cur)) >= 5:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


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
        cw, tw = ln['text'].replace('"', '').split(), ln['tts'].replace('"', '').split()
        SPOKEN.clear()
        if cw != tw:
            # map caption tokens to spoken words: e.g. "$500." -> "Five hundred dollars."
            i = j = 0
            while i < len(cw):
                if j < len(tw) and cw[i].lower() == tw[j].lower():
                    i, j = i + 1, j + 1
                    continue
                nxt = cw[i + 1].lower() if i + 1 < len(cw) else None
                k = j + 1
                while k < len(tw) and tw[k].lower() != nxt:
                    k += 1
                SPOKEN[cw[i]] = ' '.join(tw[j:k])
                i, j = i + 1, k
        gaps = pauses(a) if voice is not None else []
        wt = [(x, ln['start'] + t0, ln['start'] + t1) for x, t0, t1 in word_times(ln['text'], dur, gaps)]
        chs = group_chunks(wt)
        timed.append({'scene': ln['scene'], 'text': ln['text'], 'start': round(ln['start'], 3),
                      'end': round(end, 3), 'length_scale': scale,
                      'words': [{'w': x, 'start': round(t0, 3), 'end': round(t1, 3)} for x, t0, t1 in wt],
                      'chunks': [{'text': ' '.join(c[0] for c in ch), 'start': round(ch[0][1], 3), 'end': round(ch[-1][2], 3),
                                  'words': [{'w': x, 'start': round(t0, 3), 'end': round(t1, 3)} for x, t0, t1 in ch]}
                                 for ch in chs]})
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
        fh.write(f'WHAT IF MONEY GREW ON TREES? - NARRATION SCRIPT ({T["duration"]:.1f} seconds, {words} words)\n')
        fh.write(f'Voice: {voice_name or "not synthesised"}. Start and end times are measured from the synthesised voice.\n')
        fh.write('Read as a completely serious nature/history documentary while the world gets steadily dumber: calm, dry, unhurried.\n'
                 'Never wink at the joke. Leave a full beat after "doesn\'t grow on trees." before "Well... technically, now it does."\n'
                 'Captions show digits ($500); the voice engine is given the numbers spelled out (see scene_timing.json, "tts").\n\n')
        for sc in T['scenes']:
            fh.write(f'[SCENE {sc["id"]} - {sc["name"]}  {sc["start"]:.1f}-{sc["end"]:.1f} s]\n')
            for ln in timed:
                if ln['scene'] == sc['id']:
                    fh.write(f'({ln["start"]:05.2f}-{ln["end"]:05.2f}) {ln["text"]}\n')
            fh.write('\n')
        fh.write(f'Total: {words} words.\n')

    # storyboard.txt
    L = ['WHAT IF MONEY GREW ON TREES? - STORYBOARD AND EDITING INSTRUCTIONS',
         '=' * 60, '',
         f'{T["duration"]:.1f} s, 1080x1920 (9:16), 30 fps. Every frame is rendered in 3D (0-{T["render_end"]:.1f} s). Times follow the measured voice, not the brief\'s rough timestamps.',
         'Generated by tools/voiceover.py from scene_timing.json (the single source of truth for every cut, title and event).',
         'Every shot is rendered in Blender from animation.py; transitions, titles, captions, grain and vignette are added in its edit stage.', '']
    for sc in T['scenes']:
        f0, f1 = round(sc['start'] * 30) + 1, round(sc['end'] * 30)
        L.append(f'SCENE {sc["id"]} - {sc["name"]}  ({sc["start"]:.1f}-{sc["end"]:.1f} s, frames {f0}-{f1})')
        L.append('-' * 60)
        L.append('Visual: ' + sc['desc'])
        for key, lab in (('actions', 'Characters'), ('lighting', 'Lighting'), ('sfx', 'Sound')):
            if sc.get(key):
                L.append(f'{lab}: ' + sc[key])
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
            L.append('  Transition / edit: ' + sc['edit'])
        L.append('')
    with open(os.path.join(ROOT, 'storyboard.txt'), 'w') as fh:
        fh.write('\n'.join(L) + '\n')
    print('wrote audio/narration.wav, build/vo_timing.json, subtitles.srt, script.txt, storyboard.txt')


if __name__ == '__main__':
    main()
