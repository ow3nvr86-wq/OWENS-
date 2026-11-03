"""Animated captions and on-screen titles, drawn natively at full resolution with PIL and composited
over the finished frame. Captions: bold Cinzel capitals in parchment with a dark outline; key words sit
on a burgundy ink plate. Titles: blackletter (UnifrakturMaguntia), old-style serif (IM Fell English SC),
Cinzel, and an 'ink stamp' style that slams in, slightly rotated and distressed."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from core import FONTS, TIMING, vo_timing, clamp, smooth, ease_out, hash01

PARCH = (239, 226, 196)
INK = (24, 19, 15)
BURG = (122, 30, 38)
BURG_L = (168, 46, 52)

_F = {}


def font(name, size):
    key = (name, size)
    if key not in _F:
        path = {'cinzel': 'Cinzel.ttf', 'fell': 'IMFellEnglishSC-Regular.ttf', 'fell_it': 'IMFellEnglish-Italic.ttf',
                'frak': 'UnifrakturMaguntia-Book.ttf', 'anton': 'Anton-Regular.ttf'}[name]
        f = ImageFont.truetype(os.path.join(FONTS, path), size)
        if name == 'cinzel':
            f.set_variation_by_name('Black')
        _F[key] = f
    return _F[key]


STYLES = {
    #            font     size  fill   outline  ow  plate   y
    'tag':      ('fell',   40, PARCH, INK,     0, (20, 16, 13, 175), 0.155),
    'hero':     ('frak',  132, PARCH, INK,     7, None, 0.205),
    'date':     ('fell',   66, PARCH, INK,     5, None, 0.272),
    'label':    ('cinzel', 62, PARCH, INK,     6, None, 0.185),
    'big':      ('cinzel', 118, BURG_L, INK,   8, None, 0.245),
    'plate':    ('cinzel', 76, PARCH, INK,     6, None, 0.215),
    'stamp':    ('cinzel', 88, BURG, None,   0, None, 0.40),
    'stamp_end': ('cinzel', 88, INK, None,     0, None, 0.38),
    'tag_end':  ('fell',   46, PARCH, INK,     4, None, 0.585),
}

_SPR = {}


def text_sprite(text, style, os_=1.0):
    """RGBA float sprite (premultiplied) for one title, cached."""
    key = (text, style, os_)
    if key in _SPR:
        return _SPR[key]
    fn, size, fill, outl, ow, plate, _ = STYLES[style]
    size = int(size * os_)
    ow = max(1, int(ow * os_)) if ow else 0
    f = font(fn, size)
    lines = text.split('|')
    d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
    boxes = [d0.textbbox((0, 0), ln, font=f, stroke_width=ow) for ln in lines]
    lh = int(size * 1.12)
    tw = max(b[2] - b[0] for b in boxes)
    th = lh * len(lines)
    pad = int(60 * os_)
    im = Image.new('RGBA', (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if plate:
        d.rounded_rectangle([pad - int(26 * os_), pad - int(12 * os_), pad + tw + int(26 * os_), pad + th + int(6 * os_)],
                            radius=int(6 * os_), fill=plate)
    if style == 'stamp':
        m3 = int(44 * os_)
        d.rectangle([pad - m3, pad - m3, pad + tw + m3, pad + th + m3 - int(10 * os_)], fill=(226, 211, 178, 236))
    if style in ('stamp', 'stamp_end'):
        col = fill
        m = int(18 * os_)
        d.rectangle([pad - m, pad - m, pad + tw + m, pad + th + m // 2], outline=col + (255,), width=max(2, int(7 * os_)))
        m2 = int(30 * os_)
        d.rectangle([pad - m2, pad - m2, pad + tw + m2, pad + th + m2 - m // 2], outline=col + (255,), width=max(1, int(3 * os_)))
    for i, ln in enumerate(lines):
        b = boxes[i]
        x = pad + (tw - (b[2] - b[0])) // 2 - b[0]
        y = pad + i * lh - b[1] + int(size * 0.04)
        if style == 'stamp_end' and i == len(lines) - 1:
            colr = BURG
        else:
            colr = fill
        if outl is not None and ow:
            sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).text((x + int(5 * os_), y + int(7 * os_)), ln, font=f, fill=(0, 0, 0, 150), stroke_width=ow, stroke_fill=(0, 0, 0, 150))
            sh = sh.filter(ImageFilter.GaussianBlur(int(6 * os_) + 1))
            im = Image.alpha_composite(im, sh)
            d = ImageDraw.Draw(im)
        d.text((x, y), ln, font=f, fill=colr + (255,), stroke_width=ow, stroke_fill=(outl + (255,)) if outl else None)
    a = np.asarray(im, np.float32) / 255.0
    if style in ('stamp', 'stamp_end'):
        # distress the stamp: ink that did not take, blotted edges
        rng = np.random.default_rng(len(text))
        h, w = a.shape[:2]
        from scipy import ndimage
        n = ndimage.gaussian_filter(rng.random((h, w)).astype(np.float32), 2.2 * os_)
        n = (n - n.min()) / (n.max() - n.min() + 1e-6)
        a[..., 3] *= np.clip((n - 0.18) * 4.0, 0.15, 1.0)
        a[..., 3] *= 0.93
    a[..., :3] *= a[..., 3:4]
    _SPR[key] = a
    return a


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


def draw_titles(rgb, t, os_):
    Hh, Ww = rgb.shape[:2]
    for tl in TIMING['titles']:
        a, b = tl['start'], tl['end']
        if not (a - 0.05 <= t <= b + 0.05):
            continue
        st = tl['style']
        y = tl.get('y', STYLES[st][6])
        spr = text_sprite(tl['text'], st, os_)
        u_in = clamp((t - a) / 0.35)
        u_out = clamp((b - t) / 0.3)
        al = smooth(u_in) * smooth(u_out)
        scale, rot, dy = 1.0, 0.0, (1 - ease_out(u_in)) * 18 * os_
        if st in ('stamp', 'stamp_end'):
            # the stamp slams down: big, then a hard landing with a small shake
            u = clamp((t - a) / 0.16)
            scale = 1.0 + 0.55 * (1 - u) ** 2
            al = min(1.0, u * 1.6) * smooth(u_out)
            rot = -2.5 if st == 'stamp' else 1.5
            if 0.16 < t - a < 0.4:
                dy = 3 * os_ * math.sin((t - a) * 90)
            else:
                dy = 0
        if st == 'hero':
            scale = 1.06 - 0.06 * ease_out(u_in)
        blit(rgb, spr, Ww / 2, y * Hh + dy, al, scale, rot)


# ----------------------------------------------------------------------------------------------
# Captions
# ----------------------------------------------------------------------------------------------
CAP_SIZE = 72
CAP_Y = 0.648


def caption_sprite(words, hl, os_):
    key = ('cap', words, tuple(hl), os_)
    if key in _SPR:
        return _SPR[key]
    size = int(CAP_SIZE * os_)
    f = font('cinzel', size)
    ow = max(1, int(6 * os_))
    ws = words.split()
    d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
    space = int(size * 0.32)
    widths = [d0.textbbox((0, 0), w_, font=f, stroke_width=ow)[2] for w_ in ws]
    tw = sum(widths) + space * (len(ws) - 1)
    pad = int(36 * os_)
    hgt = int(size * 1.5)
    im = Image.new('RGBA', (tw + 2 * pad, hgt + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    x = pad
    y = pad + int(size * 0.12)
    for w_, wd in zip(ws, widths):
        ds.text((x + int(4 * os_), y + int(7 * os_)), w_, font=f, fill=(0, 0, 0, 170), stroke_width=ow, stroke_fill=(0, 0, 0, 170))
        x += wd + space
    sh = sh.filter(ImageFilter.GaussianBlur(int(7 * os_) + 1))
    im = Image.alpha_composite(im, sh)
    d = ImageDraw.Draw(im)
    x = pad
    for w_, wd in zip(ws, widths):
        key_w = w_.upper().strip('"') in hl
        if key_w:
            # a burgundy ink plate behind the key word, slightly uneven like a brush swipe
            rng = np.random.default_rng(len(w_))
            j = [int(v * os_) for v in rng.integers(-4, 5, 4)]
            d.polygon([(x - int(12 * os_) + j[0], y + int(size * 0.06)), (x + wd + int(10 * os_) + j[1], y + int(size * 0.02)),
                       (x + wd + int(14 * os_) + j[2], y + int(size * 1.08)), (x - int(10 * os_) + j[3], y + int(size * 1.12))],
                      fill=BURG + (235,))
        d.text((x, y), w_, font=f, fill=PARCH + (255,), stroke_width=ow, stroke_fill=INK + (255,))
        x += wd + space
    a = np.asarray(im, np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    _SPR[key] = a
    return a


_VO = None


def draw_captions(rgb, t, os_):
    global _VO
    if _VO is None:
        _VO = vo_timing()
    Hh, Ww = rgb.shape[:2]
    for ln in _VO:
        hl = [h.upper() for h in ln.get('hl', [])]
        cs = ln['chunks']
        for i, c in enumerate(cs):
            a = c['start']
            b = cs[i + 1]['start'] if i + 1 < len(cs) else c['end'] + 0.35
            if not (a <= t < b):
                continue
            spr = caption_sprite(c['text'].upper(), hl, os_)
            u = clamp((t - a) / 0.14)
            last = i + 1 == len(cs)
            out = clamp((b - t) / 0.12) if last else 1.0
            scale = 0.9 + 0.1 * ease_out(u) + 0.02 * math.sin(clamp(u) * math.pi)
            blit(rgb, spr, Ww / 2, CAP_Y * Hh + (1 - ease_out(u)) * 16 * os_, smooth(u) * out, scale)
    _ = hash01
