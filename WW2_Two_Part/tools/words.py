"""Word-level timing of the supplied voiceover: an offline speech recogniser (faster-whisper, small.en) gives each
word's start and end; the words are aligned to the caption script (partN/captions.txt, one caption line per line)
and each start is snapped to the nearest point where speech resumes in the audio.

  <python with faster-whisper> -I tools/words.py part1   -> part1/build/words.json
"""
import difflib
import json
import os
import re
import sys
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = {'first': '1st', 'seventh': '7th', 'sixth': '6th', '6': 'six', '3': 'three', '20': 'twenty', '2': 'two', '70': 'seventy',
         '85': 'eightyfive', 'nineteen': '19'}


def norm(w):
    w = re.sub(r"[^a-z0-9']", '', w.lower().replace('’', "'"))
    return CANON.get(w, w)


def main():
    from faster_whisper import WhisperModel
    part = sys.argv[1] if len(sys.argv) > 1 else 'part1'
    d = os.path.join(ROOT, part)
    lines = [l.strip() for l in open(os.path.join(d, 'captions.txt')) if l.strip()]
    wav = os.path.join(d, 'audio', 'narration.wav')
    m = WhisperModel('small.en', device='cpu', compute_type='float32', cpu_threads=4)
    segs, _ = m.transcribe(wav, word_timestamps=True, beam_size=5,
                           initial_prompt='In 1939, this was Europe. Hitler, Poland, Stalingrad, D-Day, Pearl Harbor.')
    heard = [{'w': p, 'start': w.start, 'end': w.end} for s in segs for w in s.words for p in w.word.strip().split()]
    print('HEARD:', ' '.join(h['w'] for h in heard))
    script = [{'w': w, 'line': i} for i, ln in enumerate(lines) for w in ln.split()]
    sm = difflib.SequenceMatcher(a=[norm(s['w']) for s in script], b=[norm(h['w']) for h in heard], autojunk=False)
    for tag, i0, i1, j0, j1 in sm.get_opcodes():
        if tag == 'equal' or (tag == 'replace' and i1 - i0 == j1 - j0):
            for i, j in zip(range(i0, i1), range(j0, j1)):
                script[i].update(start=heard[j]['start'], end=heard[j]['end'], ok=True)
        elif tag == 'replace':                       # e.g. '1939' heard as two words: spread over the heard span
            t0, t1 = heard[j0]['start'], heard[j1 - 1]['end']
            n = i1 - i0
            for k, i in enumerate(range(i0, i1)):
                script[i].update(start=t0 + (t1 - t0) * k / n, end=t0 + (t1 - t0) * (k + 1) / n, ok=True)
    miss = [s['w'] for s in script if 'start' not in s]
    for i, s in enumerate(script):
        if 'start' in s:
            continue
        a = next((script[j]['end'] for j in range(i - 1, -1, -1) if 'start' in script[j]), 0.0)
        b = next((script[j]['start'] for j in range(i + 1, len(script)) if 'start' in script[j]), a + 0.3)
        s.update(start=a, end=b, ok=False)
    with wave.open(wav) as wf:
        sr = wf.getframerate()
        au = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
    # The recogniser places the first word after a pause too early (inside the silence) and squeezes the next one.
    # So: find the runs of speech between pauses from the audio itself; the first word of each run starts where the
    # run starts; every later word starts no earlier than a minimum spoken length after the word before it.
    e = np.convolve(np.abs(au), np.ones(int(0.01 * sr)) / (0.01 * sr), 'same')
    q = e < 0.01
    runs, i = [], 0
    while i < len(q):
        if not q[i]:
            j = i
            while j < len(q) and not (q[j] and q[j:j + int(0.16 * sr)].all()):
                j += 1
            runs.append((i / sr, j / sr))
            i = j
        else:
            i += 1
    SPOKEN = {'1939': 'nineteenthirtynine', '1940': 'nineteenforty', '1st': 'first', '7th': 'seventh', '1943': 'nineteenfortythree',
              '1944': 'nineteenfortyfour', '1945': 'nineteenfortyfive', '156,000': 'ahundredandfiftysixthousand', '6th': 'sixth',
              '70': 'seventy', '85': 'eightyfive'}

    def min_dur(w):
        k = re.sub(r"[^a-z0-9,']", '', w.lower())
        k = SPOKEN.get(k.strip(','), k)
        return min(0.9, 0.048 * len(k) + 0.03)

    def run_of(t):
        for k, (a, b) in enumerate(runs):
            if a - 0.05 <= t <= b + 0.05:
                return k
        return int(np.argmin([min(abs(t - a), abs(t - b)) for a, b in runs]))
    seen, prev = set(), None
    for s in script:
        k = run_of(max(s['end'] - 0.02, s['start']))
        if k not in seen:
            seen.add(k)
            st = runs[k][0]
        else:
            st = max(s['start'], runs[k][0])
        if prev is not None:
            st = max(st, prev['start'] + min_dur(prev['w']))
        s['start'], prev = st, s
    for a, b in zip(script, script[1:]):
        a['end'] = min(max(a['end'], a['start'] + 0.05), b['start'])
    out = [{'w': s['w'], 'line': s['line'], 'start': round(s['start'], 3), 'end': round(s['end'], 3)} for s in script]
    os.makedirs(os.path.join(d, 'build'), exist_ok=True)
    json.dump({'duration': len(au) / sr, 'words': out}, open(os.path.join(d, 'build', 'words.json'), 'w'), indent=1)
    print(f'{len(out)} words; not matched: {miss}')
    print(' '.join(f"{x['w']}@{x['start']:.2f}" for x in out))


if __name__ == '__main__':
    sys.exit(main())
