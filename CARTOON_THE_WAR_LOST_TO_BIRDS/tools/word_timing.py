"""Word timestamps for the user's narration (Whisper small.en via transformers), aligned to script.txt so every
script word gets a start/end time. Writes work/words.json and work/phrases.json.
Run with /opt/shorts/chatterbox-venv/bin/python tools/word_timing.py audio/voice_user.mp3"""
import json, os, re, subprocess, sys, difflib
import numpy as np
from transformers import pipeline
from transformers.utils import logging
logging.set_verbosity_error(); logging.disable_progress_bar()

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                                 capture_output=True).stdout, np.float32)
dur = len(x) / 16000
asr = pipeline('automatic-speech-recognition', model='openai/whisper-small.en', device='cpu')
out = asr({'raw': x, 'sampling_rate': 16000}, chunk_length_s=30, return_timestamps='word')
hyp = [(c['text'].strip(), c['timestamp'][0], c['timestamp'][1]) for c in out['chunks']]
NUM = {'1932': 'nineteen thirty two', '20,000': 'twenty thousand', '10,000': 'ten thousand', '10': 'ten', '2': 'two'}
def norm(w):
    w = w.lower().strip(' .,?!:;"')
    w = NUM.get(w, w)
    return re.sub(r"[^a-z' ]", ' ', w.replace('-', ' ')).split()
# expand hypothesis tokens to normalised words, sharing the chunk's time span
H = []
for t, a, b in hyp:
    ws = norm(t) or ['']
    for k, w in enumerate(ws):
        H.append((w, a + (b - a) * k / len(ws), a + (b - a) * (k + 1) / len(ws)))
script = open(os.path.join(HERE, 'script.txt')).read().split()
S = []        # (display word, normalised piece, line index)
for li, line in enumerate(l for l in open(os.path.join(HERE, 'script.txt')) if l.strip()):
    for w in line.split():
        for p in norm(w):
            S.append((w, p, li))
sm = difflib.SequenceMatcher(None, [s[1] for s in S], [h[0] for h in H], autojunk=False)
times = [None] * len(S)
for op, a1, a2, b1, b2 in sm.get_opcodes():
    if op == 'equal' or (op == 'replace' and a2 - a1 == b2 - b1):
        for k in range(a2 - a1):
            times[a1 + k] = (H[b1 + k][1], H[b1 + k][2])
    elif op == 'replace':
        t0, t1 = H[b1][1], H[b2 - 1][2]
        for k in range(a2 - a1):
            times[a1 + k] = (t0 + (t1 - t0) * k / (a2 - a1), t0 + (t1 - t0) * (k + 1) / (a2 - a1))
# fill gaps (deleted words) by interpolation
for i in range(len(times)):
    if times[i] is None:
        prev = next((times[j][1] for j in range(i - 1, -1, -1) if times[j]), 0.0)
        nxt = next((times[j][0] for j in range(i + 1, len(times)) if times[j]), prev)
        times[i] = (prev, nxt)
# merge pieces back into display words
words, i = [], 0
while i < len(S):
    w, li = S[i][0], S[i][2]
    j = i
    while j + 1 < len(S) and S[j + 1][0] is w:
        j += 1
    words.append(dict(word=w, line=li, start=round(times[i][0], 3), end=round(times[j][1], 3)))
    i = j + 1
# phrases: split at punctuation
phrases, cur = [], []
for w in words:
    cur.append(w)
    if re.search(r'[.,?!:]$', w['word']):
        phrases.append(dict(text=' '.join(c['word'] for c in cur), start=cur[0]['start'], end=cur[-1]['end'],
                            line=cur[0]['line'])); cur = []
if cur:
    phrases.append(dict(text=' '.join(c['word'] for c in cur), start=cur[0]['start'], end=cur[-1]['end'], line=cur[0]['line']))
os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
json.dump(dict(duration=round(dur, 3), frames=round(dur * 30), words=words), open(os.path.join(HERE, 'work', 'words.json'), 'w'), indent=1)
json.dump(dict(duration=round(dur, 3), frames=round(dur * 30), phrases=phrases), open(os.path.join(HERE, 'work', 'phrases.json'), 'w'), indent=1)
print('heard:', out['text'])
print('match %.0f%%' % (sm.ratio() * 100), [(op, ' '.join(s[1] for s in S[a1:a2]), ' '.join(h[0] for h in H[b1:b2])) for op, a1, a2, b1, b2 in sm.get_opcodes() if op != 'equal'])
for p in phrases:
    print('%6.2f %6.2f  f%4d  %s' % (p['start'], p['end'], round(p['start'] * 30), p['text']))
