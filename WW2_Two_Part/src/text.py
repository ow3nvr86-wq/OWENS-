"""Type for the WW2 Shorts, drawn with PIL at full resolution: word-by-word captions (Inter Black capitals, white
with a thick dark outline, key words in yellow), title slams (Anton), plates, and labels painted into the map."""
import json
import math
import os

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from core import FONTS, TIMING, PART_DIR, clamp, smooth, ease_out, rgba_to_surface

WHITE = (246, 248, 252)
INK = (6, 9, 16)
YELLOW = (255, 210, 63)
RED = (214, 36, 48)
RED_L = (255, 84, 80)
BLUE = (64, 150, 255)
GREY = (170, 182, 200)

_F = {}


def font(name, size):
    key = (name, size)
    if key not in _F:
        path = {'black': 'Inter-Black.otf', 'xb': 'Inter-ExtraBold.otf', 'bold': 'Inter-Bold.otf', 'semi': 'Inter-SemiBold.otf',
                'anton': 'Anton-Regular.ttf'}[name]
        _F[key] = ImageFont.truetype(os.path.join(FONTS, path), size)
    return _F[key]


def _sprite(lines, os_, shadow=True, plate=None):
    """lines: (text, font, size, fill, outline_w). plate: RGBA behind the text. Premultiplied float RGBA."""
    d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
    meas = []
    for txt, fn, size, fill, ow in lines:
        f = font(fn, max(6, int(size * os_)))
        o = max(1, int(ow * os_)) if ow else 0
        meas.append((txt, f, fill, o, d0.textbbox((0, 0), txt, font=f, stroke_width=o)))
    tw = max(m[4][2] - m[4][0] for m in meas)
    gaps = [int((m[4][3] - m[4][1]) * 1.14) for m in meas]
    th = sum(gaps)
    pad = int(44 * os_) + 8
    im = Image.new('RGBA', (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    if plate:
        px, py = int(26 * os_), int(14 * os_)
        ImageDraw.Draw(im).rounded_rectangle([pad - px, pad - py, pad + tw + px, pad + th + py - int(gaps[-1] * 0.1)], radius=int(10 * os_), fill=plate)
    y = pad
    pos = []
    for (txt, f, fill, o, b), g in zip(meas, gaps):
        pos.append((pad + (tw - (b[2] - b[0])) // 2 - b[0], y - b[1], txt, f, fill, o))
        y += g
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ds = ImageDraw.Draw(sh)
        if plate:
            px, py = int(26 * os_), int(14 * os_)
            ds.rounded_rectangle([pad - px, pad - py + int(8 * os_), pad + tw + px, pad + th + py], radius=int(10 * os_), fill=(0, 0, 0, 150))
        else:
            for x, yy, txt, f, fill, o in pos:
                ds.text((x + int(3 * os_), yy + int(8 * os_)), txt, font=f, fill=(0, 0, 0, 170), stroke_width=o, stroke_fill=(0, 0, 0, 170))
        sh = sh.filter(ImageFilter.GaussianBlur(int(8 * os_) + 1))
        im = Image.alpha_composite(sh, im)
    d = ImageDraw.Draw(im)
    for x, yy, txt, f, fill, o in pos:
        d.text((x, yy), txt, font=f, fill=fill + (255,), stroke_width=o, stroke_fill=INK + (255,))
    a = np.asarray(im, np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a


_SPR = {}


def sprite(key, lines, os_, plate=None):
    k = (key, os_)
    if k not in _SPR:
        _SPR[k] = _sprite(lines, os_, plate=plate)
    return _SPR[k]


def blit(rgb, spr, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.003:
        return
    if scale != 1.0:
        im = Image.fromarray((np.clip(spr, 0, 1) * 255).astype(np.uint8), 'RGBA')
        w, h = im.size
        spr = np.asarray(im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR), np.float32) / 255.0
    h, w = spr.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    H_, W_ = rgb.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    ex, ey = min(w, W_ - x0), min(h, H_ - y0)
    if ex <= sx0 or ey <= sy0:
        return
    s = spr[sy0:ey, sx0:ex]
    region = rgb[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex].astype(np.float32) / 255.0
    out = region * (1 - s[..., 3:4] * alpha) + s[..., :3] * alpha
    rgb[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex] = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


# ---- labels painted into the scene (cairo), in 1080x1920 frame coordinates ----------------------------
_SURF = {}


def label_surface(text, size, fill, os_, ow=6, fn='black', plate=None):
    key = (text, size, fill, os_, ow, fn, plate)
    if key not in _SURF:
        a = _sprite([(text, fn, size, fill, ow)], os_, True, plate)
        st = a.copy()
        st[..., :3] = a[..., :3] / np.clip(a[..., 3:4], 1e-6, 1)
        _SURF[key] = rgba_to_surface(st)
    return _SURF[key]


def paint_label(ctx, text, x, y, size, os_, fill=WHITE, alpha=1.0, scale=1.0, ow=6, fn='black', plate=None, clampx=True):
    if alpha <= 0.003 or scale <= 0.01:
        return
    s = label_surface(text, size, fill, os_, ow, fn, plate)
    w, h = s.get_width(), s.get_height()
    if clampx:
        half = w / os_ / 2 * scale - 40
        x = min(max(x, 30 + half), 1050 - half) if half < 510 else 540
    ctx.save()
    ctx.identity_matrix()
    ctx.translate(x * os_, y * os_)
    ctx.scale(scale, scale)
    ctx.set_source_surface(s, -w / 2, -h / 2)
    ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def pop(t, t0, dur=0.26):
    """(alpha, scale) of something popping in with a little overshoot."""
    u = clamp((t - t0) / dur)
    if u <= 0:
        return 0.0, 0.0
    return smooth(u * 2.5), (0.6 + 0.4 * ease_out(u * 1.5)) * (1 + 0.22 * math.sin(u * math.pi) * (1 - u))


# ---- titles ------------------------------------------------------------------------------------------
TITLE = {
    #          lines: (font, size, colour, outline)                     plate
    'year':   ((('anton', 250, WHITE, 0),), None),
    'date':   ((('anton', 128, WHITE, 0),), None),
    'big':    ((('anton', 230, YELLOW, 0), ('black', 50, WHITE, 0)), None),
    'plate':  ((('black', 50, WHITE, 0),), RED + (255,)),
    'plateb': ((('black', 50, WHITE, 0),), (36, 110, 220, 255)),
    'part':   ((('anton', 300, WHITE, 0),), None),
    'follow': ((('black', 46, INK, 0),), YELLOW + (255,)),
}
SLAM = ('year', 'date', 'big', 'part')


def draw_titles(rgb, t, os_):
    Hh, Ww = rgb.shape[:2]
    for tl in TIMING['titles']:
        a, b = tl['start'], tl['end']
        if not (a - 0.02 <= t <= b + 0.02):
            continue
        st = tl['style']
        spec, plate = TITLE[st]
        parts = tl['text'].split('|')
        lines = [(p, *spec[min(i, len(spec) - 1)]) for i, p in enumerate(parts)]
        spr = sprite(('title', tl['text'], st), lines, os_, plate)
        u_out = clamp((b - t) / 0.16)
        dy = 0.0
        if st in SLAM:
            u = clamp((t - a) / 0.13)
            scale = 1.0 + 0.75 * (1 - u) ** 2
            al = min(1.0, u * 2.0) * smooth(u_out)
            if 0.13 < t - a < 0.4:
                dy = 6 * os_ * math.sin((t - a) * 85) * (0.4 - (t - a)) / 0.27
        else:
            u = clamp((t - a) / 0.2)
            scale = 0.8 + 0.2 * ease_out(u) + 0.06 * math.sin(u * math.pi)
            al = smooth(u * 1.6) * smooth(u_out)
        scale *= min(1.0, 0.94 * Ww / max(1, spr.shape[1] - 2 * 44 * os_))
        blit(rgb, spr, Ww / 2, tl['y'] * Hh + dy, al, scale)


# ---- captions: word by word, centre of the lower third ---------------------------------------------------
CAP_SIZE = 92
CAP_Y = 0.668
_CAPS = None


def caps():
    global _CAPS
    if _CAPS is None:
        p = os.path.join(PART_DIR, 'build', 'vo_timing.json')
        _CAPS = json.load(open(p))['captions'] if os.path.exists(p) else []
    return _CAPS


def caption_sprite(words, hl, os_):
    k = (('cap', words, tuple(hl)), os_)
    if k in _SPR:
        return _SPR[k]
    size = int(CAP_SIZE * os_)
    f = font('black', size)
    ow = max(1, int(10 * os_))
    ws = words.split()
    d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
    space = int(size * 0.27)
    bbs = [d0.textbbox((0, 0), w_, font=f, stroke_width=ow) for w_ in ws]
    widths = [b[2] - b[0] for b in bbs]
    tw = sum(widths) + space * (len(ws) - 1)
    pad = int(40 * os_) + 6
    im = Image.new('RGBA', (tw + 2 * pad, int(size * 1.35) + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    x = pad
    for w_, wd, b in zip(ws, widths, bbs):
        ds.text((x - b[0] + int(3 * os_), pad + int(10 * os_)), w_, font=f, fill=(0, 0, 0, 185), stroke_width=ow, stroke_fill=(0, 0, 0, 185))
        x += wd + space
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(int(8 * os_) + 1)))
    d = ImageDraw.Draw(im)
    x = pad
    for w_, wd, b in zip(ws, widths, bbs):
        col = YELLOW if w_.strip('.,:?!') in hl else WHITE
        d.text((x - b[0], pad), w_, font=f, fill=col + (255,), stroke_width=ow, stroke_fill=INK + (255,))
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
        spr = caption_sprite(c['text'].upper(), c['hl'], os_)
        u = clamp((t - c['start']) / 0.11)
        scale = (1.0 + 0.16 * (1 - ease_out(u))) * min(1.0, 0.95 * Ww / spr.shape[1])
        out = clamp((c['until'] - t) / 0.07) if c['until'] - c['end'] > 0.18 else 1.0
        blit(rgb, spr, Ww / 2, CAP_Y * Hh, smooth(u * 1.6) * out, scale)
