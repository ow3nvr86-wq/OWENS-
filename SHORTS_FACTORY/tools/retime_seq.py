"""Re-time a rendered one-shot sequence to a new voiceover without re-rendering the 3D.

    python tools/retime_seq.py <scene_script.py> <old_seq_dir> <new_seq_dir> <old_words.json> <new_words.json>

The scene script's beat block (from `norm = ` to `b = B`) is run on both word files, giving matching story beats
(cue words plus derived beats such as "boom"). A piecewise-linear map new time -> old time through those beats picks,
for every new frame, a fractional old frame: the image is a cross-fade of the two neighbouring rendered frames, and the
camera, actor tracks, visibility and roll in camera.json are interpolated at the same point. Every beat lands on its
new word exactly; between beats the action plays a little faster or slower."""
import sys, os, json, re, bisect
from PIL import Image

script, old_dir, new_dir, old_w, new_w = sys.argv[1:6]
src = open(script).read()
block = src[src.index('norm = '):src.index('b = B')]


def beats(words_path):
    WORDS = json.load(open(words_path))
    g = {'re': re, 'json': json, 'WORDS': WORDS, 'DUR': WORDS['duration'] + 1.2, 'print': lambda *a, **k: None}
    exec(block, g)
    return g['B'], g['DUR']


Bo, Do = beats(old_w)
Bn, Dn = beats(new_w)
pairs = sorted((Bn[k], Bo[k]) for k in Bo if k != 'end')
anchors = [(0.0, 0.0)]
for tn, to in pairs:                                    # keep the map strictly increasing in both times
    if tn > anchors[-1][0] + 1e-3 and to > anchors[-1][1] + 1e-3:
        anchors.append((tn, to))
    else:
        print('skip anchor', round(tn, 2), round(to, 2))
anchors.append((Dn, Do))
AN = [a for a, _ in anchors]


def to_old(tn):
    i = max(0, min(len(anchors) - 2, bisect.bisect_right(AN, tn) - 1))
    (a0, b0), (a1, b1) = anchors[i], anchors[i + 1]
    return b0 + (b1 - b0) * (tn - a0) / (a1 - a0)


meta = json.load(open(os.path.join(old_dir, 'camera.json')))
fps, NO = meta['fps'], meta['frames']
NN = int(round(Dn * fps))
lerp = lambda a, b, u: a + (b - a) * u


def lerp_any(a, b, u):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return round(lerp(a, b, u), 5)
    if isinstance(a, list):
        return [lerp_any(x, y, u) for x, y in zip(a, b)]
    if isinstance(a, dict):
        return {k: lerp_any(a[k], b.get(k, a[k]), u) for k in a}
    return a if u < 0.5 else b


def sample(arr, x):
    i = min(len(arr) - 2, int(x)); u = x - i
    return lerp_any(arr[i], arr[i + 1], u)


os.makedirs(new_dir, exist_ok=True)
out = dict(meta, frames=NN, track=[], roll=[], actors={k: [] for k in meta['actors']}, vis={k: [] for k in meta['vis']},
           beats={k: round(v, 3) for k, v in Bn.items()})
maxf = NO - 1
for f in range(NN):
    x = min(maxf, max(0.0, to_old(f / fps) * fps))
    out['track'].append(sample(meta['track'], x))
    out['roll'].append(sample(meta['roll'], x))
    for k in meta['actors']:
        out['actors'][k].append(sample(meta['actors'][k], x))
    for k in meta['vis']:
        out['vis'][k].append(sample(meta['vis'][k], x))
    i = int(x); u = x - i
    pa = os.path.join(old_dir, 'f%04d.jpg' % i); pb = os.path.join(old_dir, 'f%04d.jpg' % min(maxf, i + 1))
    dst = os.path.join(new_dir, 'f%04d.jpg' % f)
    if u < 0.03 or pa == pb:
        Image.open(pa).save(dst, quality=92)
    elif u > 0.97:
        Image.open(pb).save(dst, quality=92)
    else:
        Image.blend(Image.open(pa).convert('RGB'), Image.open(pb).convert('RGB'), u).save(dst, quality=92)
json.dump(out, open(os.path.join(new_dir, 'camera.json'), 'w'), separators=(',', ':'))
sp = [(b1 - b0) / (a1 - a0) for (a0, b0), (a1, b1) in zip(anchors, anchors[1:])]
print('%d -> %d frames, %d anchors, playback speed %.2f..%.2f' % (NO, NN, len(anchors), min(sp), max(sp)))
