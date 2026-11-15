"""A reusable colour look: tone curve + saturation + split toning (shadow / highlight tint) + vignette, applied to a
finished frame. The same maths runs in the engine (engine/look.js) and here (for Blender-only pipelines and for fitting).
  Fit a look so a set of frames matches a reference set's statistics (tools/look_stats.py):
    $SHORTS_PY tools/look.py fit "<our frames glob>" "<reference glob>" looks/<name>.json [--crop-vertical-ref]
  Apply it to images:  $SHORTS_PY tools/look.py apply looks/<name>.json in.jpg out.jpg"""
import glob, json, sys
import numpy as np
from PIL import Image
sys.path.insert(0, __file__.rsplit('/', 1)[0]); from look_stats import load, stats

def apply(A, P):
    """A: float RGB [0,1] (h, w, 3) -> graded copy"""
    xs, ys = np.array(P['curve_x']), np.array(P['curve_y'])
    A = np.interp(A, xs, ys)
    L = (A @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
    A = L + P['sat'] * (A - L)
    ws = np.clip(1 - L / 0.35, 0, 1) ** 2; wh = np.clip((L - 0.6) / 0.4, 0, 1) ** 2
    A = A + ws * np.array(P['shadow_tint']) + wh * np.array(P['high_tint'])
    h, w = A.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
    u = np.clip((r - 0.45) / 0.7, 0, 1); A = A * (1 - P['vignette'] * (u * u * (3 - 2 * u)))[..., None]
    return np.clip(A, 0, 1)

def params(v, ours, ref):
    k, sat, a, b, vig = v
    o = [ours['L_pct'][p] for p in (2, 10, 25, 50, 75, 90, 98)]; r = [ref['L_pct'][p] for p in (2, 10, 25, 50, 75, 90, 98)]
    cx = [0.0] + o + [1.0]; cy = [0.0] + [oi + k * (ri - oi) for oi, ri in zip(o, r)] + [1.0]
    for i in range(1, len(cy)): cy[i] = max(cy[i], cy[i - 1] + 1e-3)
    chroma = lambda c: np.array(c) - np.mean(c)
    st = (chroma(ref['shadow_rgb']) - chroma(ours['shadow_rgb'])) * a; ht = (chroma(ref['high_rgb']) - chroma(ours['high_rgb'])) * b
    return dict(curve_x=[round(x, 4) for x in cx], curve_y=[round(min(1.0, y), 4) for y in cy], sat=round(float(sat), 3),
                shadow_tint=[round(float(x), 4) for x in st], high_tint=[round(float(x), 4) for x in ht], vignette=round(float(vig), 3))

def err(S, ref):
    e = sum((S['L_pct'][p] - ref['L_pct'][p]) ** 2 for p in (10, 25, 50, 75, 90)) * 4
    e += (S['sat_mean'] - ref['sat_mean']) ** 2 * 6 + (S['vignette'] - ref['vignette']) ** 2 * 2
    ch = lambda c: np.array(c) - np.mean(c)
    e += float(((ch(S['shadow_rgb']) - ch(ref['shadow_rgb'])) ** 2).sum()) * 20 + float(((ch(S['high_rgb']) - ch(ref['high_rgb'])) ** 2).sum()) * 20
    return e

if __name__ == '__main__':
    if sys.argv[1] == 'fit':
        F = [load(f, False) for f in sorted(glob.glob(sys.argv[2]))]; R = [load(f, '--crop-vertical-ref' in sys.argv) for f in sorted(glob.glob(sys.argv[3]))]
        ours, ref = stats(F), stats(R)
        from scipy.optimize import minimize
        f = lambda v: err(stats([apply(a, params(v, ours, ref)) for a in F[::2]]), ref)
        res = minimize(f, [0.8, 1.6, 1.5, 1.0, 0.15], method='Nelder-Mead', options=dict(maxiter=160, xatol=1e-3, fatol=1e-5))
        P = params(res.x, ours, ref); P['fit'] = dict(ours=ours, ref=ref, graded=stats([apply(a, P) for a in F]), x=[round(float(x), 4) for x in res.x])
        json.dump(P, open(sys.argv[4], 'w'), indent=1); print(json.dumps({k: v for k, v in P.items() if k != 'fit'}), '\ngraded', json.dumps(P['fit']['graded']))
    elif sys.argv[1] == 'apply':
        P = json.load(open(sys.argv[2])); A = np.asarray(Image.open(sys.argv[3]).convert('RGB'), float) / 255
        Image.fromarray((apply(A, P) * 255 + 0.5).astype(np.uint8)).save(sys.argv[4], quality=95)
