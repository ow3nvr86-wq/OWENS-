"""Type for the Short, drawn with PIL at full resolution: word-by-word captions (Cinzel Black, near-white with a
thick near-black outline, dates and numbers in gold), title slams, and the map labels and stamp that the scenes
paint into the picture itself (so they move with the camera and take the paper texture)."""
import math
import os

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from core import FONTS, TIMING, ROOT, clamp, smooth, ease_out, rgba_to_surface
import json

PARCH = (233, 216, 180)
WHITE = (250, 244, 230)
INK = (26, 20, 16)
GOLD = (212, 160, 23)
GOLD_L = (240, 196, 72)
RED = (179, 18, 29)
RED_L = (214, 44, 50)
PURPLE = (91, 42, 134)
PURPLE_L = (150, 98, 196)

_F = {}


def font(name, size):
    key = (name, size)
    if key not in _F:
        path = {'cinzel': 'Cinzel.ttf', 'fell': 'IMFellEnglishSC-Regular.ttf', 'fell_it': 'IMFellEnglish-Italic.ttf',
                'anton': 'Anton-Regular.ttf'}[name]
        f = ImageFont.truetype(os.path.join(FONTS, path), size)
        if name == 'cinzel':
            f.set_variation_by_name('Black')
        _F[key] = f
    return _F[key]


def _sprite(lines, os_, shadow=True):
    """lines: list of (text, font, size, fill, outline_w). Returns premultiplied float RGBA, centred."""
    d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
    meas = []
    for txt, fn, size, fill, ow in lines:
        f = font(fn, max(6, int(size * os_)))
        o = max(1, int(ow * os_)) if ow else 0
        b = d0.textbbox((0, 0), txt, font=f, stroke_width=o)
        meas.append((txt, f, fill, o, b))
    tw = max(m[4][2] - m[4][0] for m in meas)
    gaps = [int((m[4][3] - m[4][1]) * 1.12) for m in meas]
    th = sum(gaps)
    pad = int(40 * os_) + 8
    im = Image.new('RGBA', (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ds, d = ImageDraw.Draw(sh), ImageDraw.Draw(im)
    y = pad
    pos = []
    for (txt, f, fill, o, b), g in zip(meas, gaps):
        x = pad + (tw - (b[2] - b[0])) // 2 - b[0]
        pos.append((x, y - b[1], txt, f, fill, o))
        y += g
    if shadow:
        for x, yy, txt, f, fill, o in pos:
            ds.text((x + int(4 * os_), yy + int(8 * os_)), txt, font=f, fill=(0, 0, 0, 160), stroke_width=o, stroke_fill=(0, 0, 0, 160))
        sh = sh.filter(ImageFilter.GaussianBlur(int(7 * os_) + 1))
        im = Image.alpha_composite(sh, im)
        d = ImageDraw.Draw(im)
    for x, yy, txt, f, fill, o in pos:
        d.text((x, yy), txt, font=f, fill=fill + (255,), stroke_width=o, stroke_fill=INK + (255,))
    a = np.asarray(im, np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a


_SPR = {}


def sprite(key, lines, os_):
    k = (key, os_)
    if k not in _SPR:
        _SPR[k] = _sprite(lines, os_)
    return _SPR[k]


def blit(rgb, spr, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    """Alpha-composite a premultiplied RGBA float sprite centred at (cx, cy) on an RGB uint8 frame."""
    if alpha <= 0.003:
        return
    if scale != 1.0 or rot != 0.0:
        im = Image.fromarray((np.clip(spr, 0, 1) * 255).astype(np.uint8), 'RGBA')
        w, h = im.size
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
        if rot:
            im = im.rotate(rot, resample=Image.BILINEAR, expand=True)
        spr = np.asarray(im, np.float32) / 255.0
    h, w = spr.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    H_, W_ = rgb.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    ex, ey = min(w, W_ - x0), min(h, H_ - y0)
    if ex <= sx0 or ey <= sy0:
        return
    s = spr[sy0:ey, sx0:ex]
    region = rgb[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex].astype(np.float32) / 255.0
    a = s[..., 3:4] * alpha
    out = region * (1 - a) + s[..., :3] * alpha
    rgb[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


# ----------------------------------------------------------------------------------------------
# Labels painted into the scene (cairo), positioned in 1080x1920 frame coordinates
# ----------------------------------------------------------------------------------------------
_SURF = {}


def label_surface(text, size, fill, os_, ow=7, fn='cinzel', shadow=True):
    key = (text, size, fill, os_, ow, fn, shadow)
    if key not in _SURF:
        a = _sprite([(text, fn, size, fill, ow)], os_, shadow)
        straight = a.copy()
        al = np.clip(a[..., 3:4], 1e-6, 1)
        straight[..., :3] = a[..., :3] / al
        _SURF[key] = rgba_to_surface(straight)
    return _SURF[key]


def paint_label(ctx, text, x, y, size, os_, fill=WHITE, alpha=1.0, scale=1.0, rot=0.0, ow=7, fn='cinzel', shadow=True):
    """Paint a label centred at frame point (x, y) (1080x1920 units) on an untransformed context."""
    if alpha <= 0.003 or scale <= 0.01:
        return
    s = label_surface(text, size, fill, os_, ow, fn, shadow)
    w, h = s.get_width(), s.get_height()
    half = w / os_ / 2 * scale - 34
    x = min(max(x, 24 + half), 1056 - half) if half < 516 else 540
    ctx.save()
    ctx.identity_matrix()
    ctx.translate(x * os_, y * os_)
    if rot:
        ctx.rotate(rot)
    ctx.scale(scale, scale)
    ctx.set_source_surface(s, -w / 2, -h / 2)
    ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def pop(t, t0, dur=0.28):
    """A label popping in with a little overshoot: (alpha, scale)."""
    u = clamp((t - t0) / dur)
    if u <= 0:
        return 0.0, 0.0
    s = 1 + 0.32 * math.sin(u * math.pi) * (1 - u) + (0.6 * (1 - u) ** 3 if u < 0.35 else 0)
    return smooth(u * 2.5), min(s, 1.35) * (0.55 + 0.45 * ease_out(u * 1.6))


# ----------------------------------------------------------------------------------------------
# Titles
# ----------------------------------------------------------------------------------------------
TITLE = {
    #               first line: font, size, colour      second line
    'gold':        (('cinzel', 104, GOLD), ('cinzel', 60, WHITE)),
    'slam':        (('cinzel', 150, GOLD), ('cinzel', 64, WHITE)),
    'slam_red':    (('cinzel', 150, RED_L), ('cinzel', 64, WHITE)),
    'slam_purple': (('cinzel', 104, PURPLE_L), ('cinzel', 104, GOLD)),
    'question':    (('cinzel', 92, WHITE), ('cinzel', 92, GOLD)),
}


def title_sprite(text, style, os_):
    a, b = TITLE[style]
    parts = text.split('|')
    lines = [(parts[0], a[0], a[1], a[2], 9)]
    for p in parts[1:]:
        lines.append((p, b[0], b[1], b[2], 7))
    return sprite(('title', text, style), lines, os_)


def draw_titles(rgb, t, os_):
    Hh, Ww = rgb.shape[:2]
    for tl in TIMING['titles']:
        a, b = tl['start'], tl['end']
        if not (a - 0.02 <= t <= b + 0.02):
            continue
        st = tl['style']
        spr = title_sprite(tl['text'], st, os_)
        u_out = clamp((b - t) / 0.22)
        dy, rot = 0.0, 0.0
        if st.startswith('slam'):
            # slams down from large with a hard landing and a little shake
            u = clamp((t - a) / 0.15)
            scale = 1.0 + 0.7 * (1 - u) ** 2
            al = min(1.0, u * 1.8) * smooth(u_out)
            if 0.15 < t - a < 0.42:
                dy = 5 * os_ * math.sin((t - a) * 80) * (0.42 - (t - a)) / 0.27
        else:
            u = clamp((t - a) / 0.3)
            al = smooth(u) * smooth(u_out)
            scale = 0.86 + 0.14 * ease_out(u)
        fit = 0.92 * Ww / spr.shape[1] * (1 + 2 * 48 * os_ / max(spr.shape[1], 1))
        scale *= min(1.0, fit)
        blit(rgb, spr, Ww / 2, tl.get('y', 0.19) * Hh + dy, al, scale, rot)
        if st == 'question' and t > a + 0.5:
            # a pointing arrow towards the comments
            ua = clamp((t - a - 0.5) / 0.3)
            arr = sprite(('arrow',), [('↓', 'anton', 120, GOLD, 8)], os_)
            bob = 10 * os_ * math.sin((t - a) * 6.0)
            blit(rgb, arr, Ww / 2, (tl.get('y', 0.19) + 0.12) * Hh + bob, smooth(ua) * smooth(u_out), 1.0)


# ----------------------------------------------------------------------------------------------
# Captions: word by word, centre of the lower third
# ----------------------------------------------------------------------------------------------
CAP_SIZE = 96
CAP_Y = 0.665
_CAPS = None


def caps():
    global _CAPS
    if _CAPS is None:
        p = os.path.join(ROOT, 'build', 'vo_timing.json')
        _CAPS = json.load(open(p))['captions'] if os.path.exists(p) else []
    return _CAPS


def caption_sprite(words, gold, os_):
    key = ('cap', words, tuple(gold))
    k = (key, os_)
    if k in _SPR:
        return _SPR[k]
    size = int(CAP_SIZE * os_)
    f = font('cinzel', size)
    ow = max(1, int(9 * os_))
    ws = words.split()
    d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
    space = int(size * 0.28)
    bbs = [d0.textbbox((0, 0), w_, font=f, stroke_width=ow) for w_ in ws]
    widths = [b[2] - b[0] for b in bbs]
    tw = sum(widths) + space * (len(ws) - 1)
    pad = int(40 * os_) + 6
    hgt = int(size * 1.35)
    im = Image.new('RGBA', (tw + 2 * pad, hgt + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    y = pad
    x = pad
    for w_, wd, b in zip(ws, widths, bbs):
        ds.text((x - b[0] + int(4 * os_), y + int(9 * os_)), w_, font=f, fill=(0, 0, 0, 175), stroke_width=ow, stroke_fill=(0, 0, 0, 175))
        x += wd + space
    sh = sh.filter(ImageFilter.GaussianBlur(int(7 * os_) + 1))
    im = Image.alpha_composite(im, sh)
    d = ImageDraw.Draw(im)
    x = pad
    for w_, wd, b in zip(ws, widths, bbs):
        col = GOLD if w_.upper().strip('.,:?') in gold else WHITE
        d.text((x - b[0], y), w_, font=f, fill=col + (255,), stroke_width=ow, stroke_fill=INK + (255,))
        x += wd + space
    a = np.asarray(im, np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    _SPR[k] = a
    return a


def draw_captions(rgb, t, os_):
    Hh, Ww = rgb.shape[:2]
    for c in caps():
        if not (c['start'] <= t < c['until']):
            continue
        spr = caption_sprite(c['text'].upper(), c['gold'], os_)
        u = clamp((t - c['start']) / 0.12)
        scale = 1.0 + 0.14 * (1 - ease_out(u))
        out = clamp((c['until'] - t) / 0.08) if c['until'] - c['end'] > 0.2 else 1.0
        fit = 0.94 * Ww / spr.shape[1]
        blit(rgb, spr, Ww / 2, CAP_Y * Hh, smooth(u * 1.5) * out, scale * min(1.0, fit))
