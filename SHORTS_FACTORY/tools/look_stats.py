"""Colour statistics of a set of frames (for matching a reference look): luminance percentiles, saturation,
shadow / mid / highlight tint, warm-cool balance, and vignette (edge vs centre brightness).
Run: $SHORTS_PY tools/look_stats.py "<glob>" [--crop-vertical]   (crop-vertical: take the 9:16 middle of a 4:3 frame)"""
import glob, sys, json
import numpy as np
from PIL import Image

def load(f, crop):
    im = Image.open(f).convert('RGB')
    if crop: w, h = im.size; cw = int(h * 9 / 16); x0 = (w - cw) // 2; im = im.crop((x0, 0, x0 + cw, h))
    return np.asarray(im.resize((180, 320)), float) / 255.0

def stats(frames):
    A = np.stack(frames); L = A @ np.array([0.2126, 0.7152, 0.0722])
    mx, mn = A.max(-1), A.min(-1); S = np.where(mx > 1e-3, (mx - mn) / np.maximum(mx, 1e-3), 0)
    out = dict(n=len(frames), L_pct={p: round(float(np.percentile(L, p)), 3) for p in (2, 10, 25, 50, 75, 90, 98)},
               L_mean=round(float(L.mean()), 3), sat_mean=round(float(S.mean()), 3), sat_p75=round(float(np.percentile(S, 75)), 3))
    for name, lo, hi in (('shadow', 0.0, 0.25), ('mid', 0.25, 0.65), ('high', 0.65, 1.01)):
        m = (L >= lo) & (L < hi); c = A[m].mean(0) if m.any() else np.zeros(3); out[name + '_rgb'] = [round(float(v), 3) for v in c]
        out[name + '_share'] = round(float(m.mean()), 3)
    out['warmth'] = round(float((A[..., 0] - A[..., 2]).mean()), 3)
    yy, xx = np.mgrid[0:320, 0:180]; r = np.hypot((xx - 90) / 90, (yy - 160) / 160)
    out['vignette'] = round(float(L[:, r > 0.95].mean() / max(1e-3, L[:, r < 0.45].mean())), 3)
    return out

if __name__ == '__main__':
    fs = sorted(glob.glob(sys.argv[1])); crop = '--crop-vertical' in sys.argv
    print(json.dumps(stats([load(f, crop) for f in fs]), indent=1))
