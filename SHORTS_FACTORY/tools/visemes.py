"""Lip sync data: word timestamps (work/words.json, from tools/align.py) -> phonemes (CMU pronouncing dictionary, with
a simple letter-to-sound fallback for unknown words) -> timed viseme keys in work/visemes.json.
Phonemes are spread across each word's time (vowels get more time than consonants). M/B/P are held at least
2 frames (of 30 fps). Each viseme starts one frame early (coarticulation). Loudness is NOT used here: the engine
only uses it to scale how far the mouth opens.        Run: $SHORTS_PY tools/visemes.py episodes/<name>"""
import json, os, re, sys
import cmudict

EP = sys.argv[1]
WJ = json.load(open(os.path.join(EP, 'work', 'words.json')))
D = cmudict.dict()
FR = 1 / 30
MAP = {'M': 'MBP', 'B': 'MBP', 'P': 'MBP', 'F': 'FV', 'V': 'FV', 'TH': 'TH', 'DH': 'TH', 'L': 'L',
       'IY': 'EE', 'IH': 'EE', 'EH': 'EE', 'EY': 'EE', 'CH': 'EE', 'SH': 'EE', 'JH': 'EE', 'ZH': 'EE', 'Y': 'EE',
       'AA': 'AA', 'AE': 'AA', 'AH': 'AA', 'AY': 'AA', 'AW': 'AA', 'AO': 'OH', 'OW': 'OH', 'OY': 'OH', 'ER': 'ETC',
       'UW': 'OO', 'UH': 'OO', 'W': 'OO',
       'K': 'ETC', 'G': 'ETC', 'NG': 'ETC', 'N': 'ETC', 'T': 'ETC', 'D': 'ETC', 'S': 'ETC', 'Z': 'ETC', 'R': 'ETC', 'HH': 'ETC'}
NUM = {'1': 'one', '4': 'four', '99': 'ninety nine'}
G2P = [('tion', ['SH', 'AH', 'N']), ('th', ['TH']), ('sh', ['SH']), ('ch', ['CH']), ('ph', ['F']), ('oo', ['UW']), ('ee', ['IY']),
       ('ea', ['IY']), ('ou', ['AW']), ('ow', ['OW']), ('ai', ['EY']), ('ay', ['EY']), ('qu', ['K', 'W']), ('ck', ['K']), ('ng', ['NG']),
       ('a', ['AE']), ('e', ['EH']), ('i', ['IH']), ('o', ['AA']), ('u', ['AH']), ('y', ['IY']), ('b', ['B']), ('c', ['K']), ('d', ['D']),
       ('f', ['F']), ('g', ['G']), ('h', ['HH']), ('j', ['JH']), ('k', ['K']), ('l', ['L']), ('m', ['M']), ('n', ['N']), ('p', ['P']),
       ('r', ['R']), ('s', ['S']), ('t', ['T']), ('v', ['V']), ('w', ['W']), ('x', ['K', 'S']), ('z', ['Z'])]


def g2p(w):                                       # fallback letter-to-sound rules for words not in the dictionary
    out, i = [], 0
    while i < len(w):
        for k, ph in G2P:
            if w.startswith(k, i): out += ph; i += len(k); break
        else: i += 1
    return out


def phones(word):
    out = []
    for part in re.split(r'[-\s]+', NUM.get(word, word)):
        part = re.sub(r"[^a-z']", '', part.lower())
        if not part: continue
        if part in NUM: out += phones(NUM[part]); continue
        p = D.get(part) or D.get(part.replace("'", ''))
        out += [re.sub(r'\d', '', x) for x in p[0]] if p else g2p(part)
    return out


# words that the aligner squeezed onto the same start time share their combined window by phoneme count
WORDS = [dict(w) for w in WJ['words']]
i = 0
while i < len(WORDS):
    j = i
    while j + 1 < len(WORDS) and WORDS[j + 1]['start'] - WORDS[i]['start'] < 0.06: j += 1
    if j > i:
        grp = WORDS[i:j + 1]; t0, t1 = grp[0]['start'], max(w['end'] for w in grp); n = [max(1, len(phones(re.sub(r"[^A-Za-z0-9'\- ]", '', w['word']).lower()))) for w in grp]
        t = t0
        for w, k in zip(grp, n): w['start'] = t; t += (t1 - t0) * k / sum(n); w['end'] = t
    i = j + 1
keys, unknown = [], []
for wd in WORDS:
    raw = wd['word']; clean = re.sub(r'[^A-Za-z0-9\'\- ]', '', raw).lower().strip()
    ph = phones(clean)
    if not ph: continue
    if any(re.sub(r"[^a-z']", '', p) not in D for p in re.split(r'[-\s]+', clean) if p and not p.isdigit()): unknown.append(clean)
    wts = [2.2 if MAP.get(p) in ('AA', 'OH', 'EE', 'OO') else 1.0 for p in ph]
    t0, t1 = wd['start'], max(wd['end'], wd['start'] + 0.08); span = t1 - t0; tot = sum(wts); t = t0
    for p, w in zip(ph, wts):
        v = MAP.get(p, 'ETC'); dur = span * w / tot
        keys.append(dict(t=round(t - FR, 4), v=v, word=raw, dur=max(dur, 2 * FR) if v == 'MBP' else dur))   # one frame early
        t += dur
    keys.append(dict(t=round(t1, 4), v='REST', word='', dur=0.1))
keys.sort(key=lambda k: k['t'])
# enforce the M/B/P hold: the next key can't start until the closed lips have shown for 2 frames
for i in range(len(keys) - 1):
    if keys[i]['v'] == 'MBP' and keys[i + 1]['t'] < keys[i]['t'] + 2 * FR: keys[i + 1]['t'] = round(keys[i]['t'] + 2 * FR, 4)
    keys[i + 1]['t'] = max(keys[i + 1]['t'], keys[i]['t'])
# drop REST keys that land inside the next word (no flapping shut between fast words)
out = [k for i, k in enumerate(keys) if not (k['v'] == 'REST' and i + 1 < len(keys) and keys[i + 1]['t'] - k['t'] < 0.07)]
json.dump(dict(fps=30, keys=out), open(os.path.join(EP, 'work', 'visemes.json'), 'w'), indent=0)
print('visemes:', len(out), 'keys; words not in the dictionary (letter rules used):', sorted(set(unknown)) or 'none')
