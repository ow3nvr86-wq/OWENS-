"""Animated captions and on-screen titles, drawn natively at full resolution with PIL and composited
over the finished frame. Captions: bold Cinzel capitals in parchment with a dark outline; key words sit
on a burgundy ink plate. Titles: blackletter (UnifrakturMaguntia), old-style serif (IM Fell English SC),
Cinzel, and an 'ink stamp' style that slams in, slightly rotated and distressed."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from core import FONTS, TIMING, vo_timing, clamp, smooth, ease_out, hash01

PARCH = (244, 246, 249)
INK = (6, 10, 20)
BURG = (200, 52, 58)
BURG_L = (224, 82, 79)
GREYB = (160, 178, 200)

_F = {}


def font(name, size):
    key = (name, size)
    if key not in _F:
        path = {'xb': 'Inter-ExtraBold.otf', 'black': 'Inter-Black.otf', 'bold': 'Inter-Bold.otf', 'semi': 'Inter-SemiBold.otf',
                'med': 'Inter-Medium.otf', 'anton': 'Anton-Regular.ttf'}[name]
        f = ImageFont.truetype(os.path.join(FONTS, path), size)
        _F[key] = f
    return _F[key]


STYLES = {
    #            font     size  fill    outline  ow  plate   y      tracking (em)
    'kicker':   ('semi',   32, PARCH,  None,    0, (8, 14, 26, 150), 0.165, 0.3),
    'date':     ('black',  82, PARCH,  None,    0, None, 0.205, 0.08),
    'clock':    ('anton', 210, PARCH,  None,    0, None, 0.19, 0.02),
    'event':    ('xb',     50, PARCH,  None,    0, None, 0.30, 0.06),
    'eventr':   ('xb',     50, BURG_L, None,    0, None, 0.30, 0.06),
    'label':    ('xb',     46, PARCH,  None,    0, (8, 14, 26, 150), 0.2, 0.06),
    'big':      ('anton', 220, PARCH,  None,    0, None, 0.24, 0.02),
    'sub':      ('xb',     38, PARCH,  None,    0, None, 0.31, 0.25),
    'endline':  ('black',  78, PARCH,  None,    0, None, 0.42, 0.06),
}

_SPR = {}


def text_sprite(text, style, os_=1.0):
    """RGBA float sprite (premultiplied) for one title, cached: letter-spaced type with a soft shadow."""
    key = (text, style, os_)
    if key in _SPR:
        return _SPR[key]
    fn, size, fill, outl, ow, plate, _, track = STYLES[style]
    size = int(size * os_)
    f = font(fn, size)
    lines = text.split('|')
    d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
    def width(ln):
        return sum(d0.textlength(ch, font=f) for ch in ln) + track * size * (len(ln) - 1)
    widths = [width(ln) for ln in lines]
    lh = int(size * 1.15)
    tw = int(max(widths)) + 2
    th = lh * len(lines)
    pad = int(50 * os_)
    im = Image.new('RGBA', (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    if plate:
        ImageDraw.Draw(im).rounded_rectangle([pad - int(24 * os_), pad - int(10 * os_), pad + tw + int(24 * os_), pad + th + int(2 * os_)],
                                             radius=int(10 * os_), fill=plate)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    for i, ln in enumerate(lines):
        x = pad + (tw - widths[i]) / 2
        y = pad + i * lh
        colr = BURG_L if (style == 'endline' and i == len(lines) - 1 and len(lines) > 1) else fill
        for ch in ln:
            ds.text((x + 2 * os_, y + 5 * os_), ch, font=f, fill=(0, 0, 0, 150))
            dl.text((x, y), ch, font=f, fill=colr + (255,))
            x += d0.textlength(ch, font=f) + track * size
    sh = sh.filter(ImageFilter.GaussianBlur(int(9 * os_) + 1))
    im = Image.alpha_composite(im, sh)
    im = Image.alpha_composite(im, layer)
    a = np.asarray(im, np.float32) / 255.0
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
    """Titles slide up and sharpen in with a little letter-spacing settle; times can 'roll'."""
    Hh, Ww = rgb.shape[:2]
    for tl in TIMING['titles']:
        a, b = tl['start'], tl['end']
        if not (a - 0.05 <= t <= b + 0.05):
            continue
        st = tl['style']
        y = tl.get('y', STYLES[st][6])
        spr = text_sprite(tl['text'], st, os_)
        u_in = clamp((t - a) / (0.9 if st == 'endline' else 0.4))
        u_out = clamp((b - t) / 0.3)
        al = smooth(u_in) * smooth(u_out)
        scale = 1.04 - 0.04 * ease_out(u_in)
        dy = (1 - ease_out(u_in)) * 26 * os_
        fit = 0.9 * Ww / spr.shape[1] * (1 + 2 * 50 * os_ / max(spr.shape[1], 1))
        scale *= min(1.0, fit)
        blit(rgb, spr, Ww / 2, y * Hh + dy, al, scale)


# ----------------------------------------------------------------------------------------------
# Captions
# ----------------------------------------------------------------------------------------------
CAP_SIZE = 70
CAP_Y = 0.655


def caption_sprite(words, hl, os_):
    key = ('cap', words, tuple(hl), os_)
    if key in _SPR:
        return _SPR[key]
    size = int(CAP_SIZE * os_)
    f = font('xb', size)
    ow = max(1, int(2 * os_))
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
            # a thin red bar under the key word
            d.rectangle([x, y + int(size * 1.14), x + wd - ow * 2, y + int(size * 1.22)], fill=BURG + (255,))
        d.text((x, y), w_, font=f, fill=(BURG_L if key_w else PARCH) + (255,), stroke_width=ow, stroke_fill=INK + (200,))
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
    nocap = {l['text'] for l in TIMING['lines'] if l.get('nocap')}
    for ln in _VO:
        if ln['text'] in nocap:
            continue
        hl = [h.upper() for h in ln.get('hl', [])]
        cs = ln['chunks']
        nxt = min([l2['start'] for l2 in _VO if l2['start'] > ln['start']] or [1e9])
        for i, c in enumerate(cs):
            a = c['start']
            b = cs[i + 1]['start'] if i + 1 < len(cs) else min(c['end'] + 0.35, nxt - 0.02)
            if not (a <= t < b):
                continue
            spr = caption_sprite(c['text'].upper(), hl, os_)
            u = clamp((t - a) / 0.14)
            last = i + 1 == len(cs)
            out = clamp((b - t) / 0.12) if last else 1.0
            scale = 0.9 + 0.1 * ease_out(u) + 0.02 * math.sin(clamp(u) * math.pi)
            blit(rgb, spr, Ww / 2, CAP_Y * Hh + (1 - ease_out(u)) * 16 * os_, smooth(u) * out, scale)
    _ = hash01
