"""Snap phrase boundaries in work/phrases.json to the real pauses in the narration (silencedetect), since Whisper's
word ends run on to the next word. Rewrites work/phrases.json and work/words.json with 'start'/'end' refined."""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
log = subprocess.run(['ffmpeg', '-nostats', '-i', src, '-af', 'silencedetect=n=-38dB:d=0.12', '-f', 'null', '-'],
                     capture_output=True, text=True).stderr
ss = [float(v) for v in re.findall(r'silence_start: ([0-9.]+)', log)]
se = [float(v) for v in re.findall(r'silence_end: ([0-9.]+)', log)]
P = json.load(open(os.path.join(HERE, 'work', 'phrases.json')))
W = json.load(open(os.path.join(HERE, 'work', 'words.json')))
ph = P['phrases']
for i, p in enumerate(ph):          # starts: the end of the pause just before the spoken phrase
    c = [e for e in se if p['start'] - 0.35 < e < p['start'] + 0.8]
    if c and i > 0:
        p['start'] = round(c[0], 3)
for i, p in enumerate(ph):          # ends: the last pause that begins before the next phrase starts
    nxt = ph[i + 1]['start'] if i + 1 < len(ph) else P['duration']
    c = [s for s in ss if p['start'] + 0.3 < s <= nxt]
    p['end'] = round(c[-1], 3) if c else round(nxt, 3)
json.dump(P, open(os.path.join(HERE, 'work', 'phrases.json'), 'w'), indent=1)
# words: clamp each word into its phrase and shift a phrase's first word to the refined start
k = 0
for p in ph:
    n = len(p['text'].split())
    ws = W['words'][k:k + n]; k += n
    ws[0]['start'] = p['start']
    for w in ws:
        w['start'] = round(max(p['start'], min(w['start'], p['end'])), 3)
        w['end'] = round(max(w['start'], min(w['end'], p['end'])), 3)
json.dump(W, open(os.path.join(HERE, 'work', 'words.json'), 'w'), indent=1)
for p in ph:
    print('%6.2f %6.2f  f%4d-%4d  %s' % (p['start'], p['end'], round(p['start'] * 30), round(p['end'] * 30), p['text']))
