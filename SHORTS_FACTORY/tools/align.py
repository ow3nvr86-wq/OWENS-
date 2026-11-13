"""Word timestamps (Whisper small.en) aligned to narration.txt, snapped to the voice's pauses, plus a per-frame mouth
amplitude. Writes <episode>/work/words.json and work/amp.json.  Run: $ALIGN_PY tools/align.py episodes/<name>"""
import json, os, re, subprocess, sys, difflib
import numpy as np
ep = sys.argv[1]; FPS = 30
src = os.path.join(ep, 'voice.wav')
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
dur = len(x) / 16000
from transformers import pipeline
from transformers.utils import logging; logging.set_verbosity_error(); logging.disable_progress_bar()
asr = pipeline('automatic-speech-recognition', model='openai/whisper-small.en', device='cpu')
# transcribe in short windows cut at pauses (long-form chunking can loop and repeat phrases)
_log = subprocess.run(['ffmpeg', '-nostats', '-i', src, '-af', 'silencedetect=n=-38dB:d=0.2', '-f', 'null', '-'], capture_output=True, text=True).stderr
_mids = [(float(a) + float(b)) / 2 for a, b in zip(re.findall(r'silence_start: ([0-9.]+)', _log), re.findall(r'silence_end: ([0-9.]+)', _log))]
cuts, last = [0.0], 0.0
for m in _mids:
    if m - last >= 12.0: cuts.append(m); last = m
cuts.append(dur)
res = {'text': '', 'chunks': []}
for a0, a1 in zip(cuts[:-1], cuts[1:]):
    seg = x[int(a0 * 16000):int(a1 * 16000)]
    r = asr({'raw': seg, 'sampling_rate': 16000}, return_timestamps='word', generate_kwargs={'no_repeat_ngram_size': 4})
    res['text'] += ' ' + r['text']
    for c in r['chunks']:
        ta, tb = c['timestamp']; res['chunks'].append(dict(text=c['text'], timestamp=(ta + a0, (tb if tb is not None else ta + 0.3) + a0)))
ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = 'x x twenty thirty forty fifty sixty seventy eighty ninety'.split()
def say(n):            # small number -> words, for matching digits Whisper writes
    n = int(n)
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ('' if n % 10 == 0 else ' ' + ONES[n % 10])
    if n < 1000: return ONES[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' and ' + say(n % 100))
    if 1100 <= n < 2000 and n % 100: return say(n // 100) + ' ' + say(n % 100)
    return say(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else ' ' + say(n % 1000))
def norm(w):
    w = w.lower().strip(' .,?!:;"…').replace('-', ' ')
    w = re.sub(r'(\d[\d,]*)', lambda m: say(m.group(1).replace(',', '')), w)
    return re.sub(r"[^a-z' ]", ' ', w).split()
chunks = []                        # glue numbers Whisper splits at the comma ('30,' + '000' -> '30,000')
for c in res['chunks']:
    if chunks and re.fullmatch(r'\s*\d{1,3},?', chunks[-1]['text']) and re.match(r'\s*,?\d{3}', c['text']):
        chunks[-1] = dict(text=chunks[-1]['text'].strip() + c['text'].strip(), timestamp=(chunks[-1]['timestamp'][0], c['timestamp'][1])); continue
    chunks.append(dict(c))
H = []
for c in chunks:
    a, b = c['timestamp']; b = b if b is not None else a + 0.3
    ws = norm(c['text']) or ['']
    for k, w in enumerate(ws): H.append((w, a + (b - a) * k / len(ws), a + (b - a) * (k + 1) / len(ws)))
S = []
for li, line in enumerate(l for l in open(os.path.join(ep, 'narration.txt')) if l.strip()):
    for w in line.split():
        for p in norm(w): S.append((w, p, li))
sm = difflib.SequenceMatcher(None, [s[1] for s in S], [h[0] for h in H], autojunk=False)
T = [None] * len(S)
for op, a1, a2, b1, b2 in sm.get_opcodes():
    if op == 'equal' or (op == 'replace' and a2 - a1 == b2 - b1):
        for k in range(a2 - a1): T[a1 + k] = (H[b1 + k][1], H[b1 + k][2])
    elif op == 'replace' and b2 > b1:
        t0, t1 = H[b1][1], H[b2 - 1][2]
        for k in range(a2 - a1): T[a1 + k] = (t0 + (t1 - t0) * k / (a2 - a1), t0 + (t1 - t0) * (k + 1) / (a2 - a1))
for i in range(len(T)):
    if T[i] is None:
        p = next((T[j][1] for j in range(i - 1, -1, -1) if T[j]), 0.0); n = next((T[j][0] for j in range(i + 1, len(T)) if T[j]), p); T[i] = (p, n)
words, i = [], 0
while i < len(S):
    w, li = S[i][0], S[i][2]; j = i
    while j + 1 < len(S) and S[j + 1][0] is w: j += 1
    words.append(dict(word=w, line=li, start=round(T[i][0], 3), end=round(T[j][1], 3))); i = j + 1
# snap each sentence start to the end of the pause before it
log = subprocess.run(['ffmpeg', '-nostats', '-i', src, '-af', 'silencedetect=n=-38dB:d=0.12', '-f', 'null', '-'], capture_output=True, text=True).stderr
se = [float(v) for v in re.findall(r'silence_end: ([0-9.]+)', log)]
for k, w in enumerate(words):
    if k and re.search(r'[.?!,]$', words[k - 1]['word']):
        c = [e for e in se if w['start'] - 0.35 < e < w['start'] + 0.5]
        if c: w['start'] = round(max(c[0], words[k - 1]['start'] + 0.05), 3)
# per-frame amplitude for mouth flaps (0..1)
a48 = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
hop = 48000 // FPS; amp = [float(np.sqrt(np.mean(a48[i:i + hop] ** 2))) for i in range(0, len(a48), hop)]
m = np.percentile(amp, 95) or 1; amp = [round(min(1.0, v / m), 3) for v in amp]
os.makedirs(os.path.join(ep, 'work'), exist_ok=True)
json.dump(dict(duration=round(dur, 3), fps=FPS, frames=int(round(dur * FPS)), words=words), open(os.path.join(ep, 'work', 'words.json'), 'w'), indent=1)
json.dump(amp, open(os.path.join(ep, 'work', 'amp.json'), 'w'))
print('heard:', res['text'].strip()[:200], '...')
print('match %.0f%%' % (sm.ratio() * 100), [(op, ' '.join(s[1] for s in S[a1:a2]), ' '.join(h[0] for h in H[b1:b2])) for op, a1, a2, b1, b2 in sm.get_opcodes() if op != 'equal'][:6])
print('duration %.2f s, %d words' % (dur, len(words)))
