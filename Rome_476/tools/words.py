"""Word-level timing for the narration: an offline speech recogniser (faster-whisper, small.en) listens to
audio/narration.wav and gives each word's start and end; the recognised words are aligned to the script's caption
words (build/vo_lines.json), so every caption word, title stamp and sound cue can land on the exact word.

  <python with faster-whisper> -I tools/words.py      -> build/words.json

Also prints the recogniser's transcript, a check that every word is heard as written.
"""
import difflib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(w):
    w = w.lower().replace('’', "'")
    w = re.sub(r"[^a-z0-9']", '', w)
    return {'a.d.': 'ad'}.get(w, w)


def main():
    from faster_whisper import WhisperModel
    lines = json.load(open(os.path.join(ROOT, 'build', 'vo_lines.json')))['lines']
    m = WhisperModel('small.en', device='cpu', compute_type='float32', cpu_threads=4)
    segs, _ = m.transcribe(os.path.join(ROOT, 'audio', 'narration.wav'), word_timestamps=True, beam_size=5,
                           initial_prompt='Rome, 476, Britain, Egypt, 117 AD, Emperor Trajan, 1453.')
    heard = []
    for s in segs:
        for w in s.words:
            for part in w.word.strip().split():
                heard.append({'w': part, 'start': w.start, 'end': w.end, 'p': w.probability})
    print('HEARD:', ' '.join(h['w'] for h in heard))
    script = []
    for ln in lines:
        for k, w in enumerate(ln['text'].split()):
            script.append({'w': w, 'line': ln['i'], 'k': k, 'lstart': ln['start'], 'lend': ln['end']})
    a = [norm(s['w']) for s in script]
    b = [norm(h['w']) for h in heard]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, i0, i1, j0, j1 in sm.get_opcodes():
        if tag == 'equal' or (tag == 'replace' and i1 - i0 == j1 - j0):
            for i, j in zip(range(i0, i1), range(j0, j1)):
                script[i]['start'], script[i]['end'], script[i]['p'] = heard[j]['start'], heard[j]['end'], heard[j]['p']
    # words the recogniser missed: spread them inside their line between the neighbours that were found
    for i, s in enumerate(script):
        if 'start' in s:
            continue
        j0 = i - 1
        while j0 >= 0 and 'start' not in script[j0]:
            j0 -= 1
        j1 = i + 1
        while j1 < len(script) and 'start' not in script[j1]:
            j1 += 1
        t0 = script[j0]['end'] if j0 >= 0 and script[j0]['line'] == s['line'] else s['lstart']
        t1 = script[j1]['start'] if j1 < len(script) and script[j1]['line'] == s['line'] else s['lend']
        n = j1 - j0 - 1
        k = i - j0 - 1
        s['start'] = t0 + (t1 - t0) * k / n
        s['end'] = t0 + (t1 - t0) * (k + 1) / n
        s['p'] = None
    # The recogniser's times inside a line are good, but it stretches a line's first word back into the silence
    # before it (or starts it late). Each line's true start and end are known exactly from synthesis: the first word
    # starts at the line's start, every word is kept inside its line, and each start is snapped to the nearest point
    # where speech resumes in the audio (within 0.12 s), so cues land on the consonant itself.
    import wave
    import numpy as np
    with wave.open(os.path.join(ROOT, 'audio', 'narration.wav')) as wf:
        sr = wf.getframerate()
        au = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
    e = np.convolve(np.abs(au), np.ones(int(0.01 * sr)) / (0.01 * sr), 'same')
    q = e < 0.006
    rise = np.nonzero(q[:-1] & ~q[1:])[0] / sr          # quiet -> sound
    for li in sorted(set(x['line'] for x in script)):
        ws = [x for x in script if x['line'] == li]
        b0, b1 = ws[0]['lstart'], ws[0]['lend']
        prev = None
        for k, x in enumerate(ws):
            st = b0 if k == 0 else min(max(x['start'], b0), b1 - 0.05)
            if k:
                near = rise[(rise > st - 0.12) & (rise < st + 0.12) & (rise > b0)]
                if len(near):
                    st = float(near[np.argmin(np.abs(near - st))])
                st = max(st, prev + 0.07)
            x['start'] = st
            x['end'] = min(max(x['end'], st + 0.06), b1)
            prev = st
        for k in range(len(ws) - 1):
            ws[k]['end'] = min(ws[k]['end'], ws[k + 1]['start'])
        ws[-1]['end'] = b1
    out = [{'w': s['w'], 'line': s['line'], 'start': round(s['start'], 3), 'end': round(s['end'], 3),
            'heard': s['p'] is not None} for s in script]
    json.dump(out, open(os.path.join(ROOT, 'build', 'words.json'), 'w'), indent=1)
    miss = [s['w'] for s in out if not s['heard']]
    print(f'{len(out)} words, {len(out) - len(miss)} matched to the recogniser, interpolated: {miss}')


if __name__ == '__main__':
    sys.exit(main())
