"""Finishing pass applied to every frame: palette grade (darkening as the story darkens), aged paper
multiplied over the image (shifted slightly every second frame, so the paper itself 'boils'), film grain,
vignette and a candle-warm or cold tint per scene."""
import os

import numpy as np

from core import W, H, ASSETS, fbm2

_CACHE = {}


def paper(os_=1.0):
    """Aged parchment texture: blotches, fibres, foxing stains and a darker, burnt edge (made once)."""
    key = ('paper', os_)
    if key in _CACHE:
        return _CACHE[key]
    path = os.path.join(ASSETS, 'paper.png')
    w, h = int(W * os_) + 16, int(H * os_) + 16
    if os.path.exists(path):
        from PIL import Image
        im = np.asarray(Image.open(path).convert('L').resize((w, h)), np.float32) / 255.0
    else:
        im = make_paper(w, h)
    _CACHE[key] = im
    return im


def make_paper(w, h, seed=5):
    n1 = fbm2(h, w, seed, scale=w / 5, octaves=6)
    n2 = fbm2(h, w, seed + 1, scale=w / 40, octaves=4)
    rng = np.random.default_rng(seed)
    fib = np.zeros((h, w), np.float32)
    for _ in range(900):
        x, y = rng.integers(0, w), rng.integers(0, h)
        L = rng.integers(8, 40)
        a = rng.uniform(0, np.pi)
        xs = np.clip((x + np.cos(a) * np.arange(L)).astype(int), 0, w - 1)
        ys = np.clip((y + np.sin(a) * np.arange(L)).astype(int), 0, h - 1)
        fib[ys, xs] += rng.uniform(0.3, 1.0)
    from scipy import ndimage
    fib = ndimage.gaussian_filter(fib, 0.7)
    stains = np.zeros((h, w), np.float32)
    for _ in range(16):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.uniform(20, 120) * w / 1080
        yy, xx = np.ogrid[:h, :w]
        d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r
        stains += np.exp(-d * d) * rng.uniform(0.2, 0.6) + 0.25 * np.exp(-((d - 1) ** 2) * 30)
    yy, xx = np.ogrid[:h, :w]
    edge = np.minimum(np.minimum(xx, w - 1 - xx) / w, np.minimum(yy, h - 1 - yy) / h)
    burn = np.clip(1 - edge / 0.06, 0, 1) ** 2
    p = 1.0 - 0.10 * (1 - n1) - 0.05 * n2 - 0.10 * np.clip(fib, 0, 1) - 0.06 * np.clip(stains, 0, 1) - 0.18 * burn
    return np.clip(p, 0, 1).astype(np.float32)


def save_paper():
    from PIL import Image
    p = make_paper(W + 16, H + 16)
    Image.fromarray((p * 255).astype(np.uint8)).save(os.path.join(ASSETS, 'paper.png'))


def vignette(os_, strength):
    key = ('vig', os_)
    if key not in _CACHE:
        w, h = int(W * os_), int(H * os_)
        yy, xx = np.ogrid[:h, :w]
        dx = (xx - w / 2) / (w / 2)
        dy = (yy - h * 0.47) / (h / 2)
        r = np.sqrt(dx * dx * 0.9 + dy * dy * 0.75)
        _CACHE[key] = np.clip((r - 0.45) / 0.75, 0, 1) ** 1.6
    return 1 - strength * _CACHE[key]


def finish(bgra, os_, t, look):
    """bgra: (h, w, 4) uint8 from cairo. look: dict(dark, desat, tint, paper, grain, vig, warm, lift).
    Returns an RGB uint8 array."""
    h, w = bgra.shape[:2]
    rgb = bgra[..., [2, 1, 0]].astype(np.float32) / 255.0
    dark = look.get('dark', 0.0)
    # desaturate towards the palette's dusty grey
    lum = rgb[..., 0] * 0.3 + rgb[..., 1] * 0.59 + rgb[..., 2] * 0.11
    ds = look.get('desat', 0.25) + 0.3 * dark
    rgb = rgb * (1 - ds) + lum[..., None] * ds
    # tint: warm parchment by day, colder and darker as the story darkens
    tint = np.array(look.get('tint', (1.0, 0.95, 0.86)), np.float32)
    rgb *= tint
    # darken and add contrast (a gentle S-curve), lifting the blacks slightly like printed ink
    gain = 1.0 - 0.42 * dark
    rgb = rgb * gain
    rgb = np.clip(rgb, 0, 1)
    rgb = rgb * rgb * (3 - 2 * rgb) * 0.55 + rgb * 0.45
    lift = look.get('lift', 0.035)
    rgb = lift + rgb * (1 - lift)
    # aged paper multiplied over everything; it shifts a little every other frame
    pp = paper(os_)
    k = int(t * 15) % 4
    ox, oy = [(0, 0), (3, 1), (1, 4), (4, 3)][k]
    ox, oy = int(ox * os_), int(oy * os_)
    pap = pp[oy:oy + h, ox:ox + w]
    ps = look.get('paper', 0.75)
    rgb *= (1 - ps) + ps * pap[..., None]
    # vignette
    rgb *= vignette(os_, look.get('vig', 0.55) + 0.25 * dark)[..., None]
    # grain
    g = look.get('grain', 0.035)
    rng = np.random.default_rng(int(t * 30) * 7 + 1)
    rgb += (rng.random((h, w), np.float32)[..., None] - 0.5) * g
    return (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
