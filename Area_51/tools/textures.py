"""Procedural prop textures for the Area 51 Short (PIL + numpy, code only).

Draws every paper prop and sign the 3D scene uses: the perimeter warning signs (wording as widely photographed
at the boundary, recreated), three 1950s-style front pages about strange lights (generic, fictional mastheads,
no invented quotes), project folders, a recreation of the cover of the declassified CIA history "The Central
Intelligence Agency and Overhead Reconnaissance: The U-2 and OXCART Programs, 1954-1974" (real title, authors
and date), declassified pages with redaction bars, an illustrative sketch map, drawn "photographs" of the U-2
and A-12 (plan views to scale), stamps and archive box labels. Writes PNGs to build/tex/. animation.py runs
this automatically when the folder is missing.

    $SHORTS_PY tools/textures.py

Accuracy notes (see sources.txt): the documents, photographs, map and newspapers are recreations and labelled
as such; they are not copies of real records.
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'tex')
FD = os.path.join(ROOT, 'assets', 'fonts')
HAND = os.path.join(FD, 'CoveredByYourGrace.ttf')
TYPE = os.path.join(FD, 'SpecialElite-Regular.ttf')
MONO = os.path.join(FD, 'CourierPrime-Regular.ttf')
HEAD = os.path.join(FD, 'OldStandard-Bold.ttf')
BOLD = os.path.join(FD, 'Anton-Regular.ttf')

INK = (24, 30, 58)          # felt-tip blue-black
PENCIL_RED = (150, 32, 30)
STAMP_RED = (170, 30, 28)
TYPE_INK = (34, 32, 34)


def F(path, size):
    return ImageFont.truetype(path, size)


# ----------------------------------------------------------------------------------------------
# paper
# ----------------------------------------------------------------------------------------------
def paper(w, h, seed, tone=(226, 214, 186), age=1.0, folds=0, lines=False):
    rng = np.random.default_rng(seed)
    base = np.ones((h, w, 3)) * np.array(tone, float)
    # low-frequency blotches + fibre noise
    for sc, amp in ((64, 10), (16, 5), (4, 3)):
        n = rng.normal(0, 1, (h // sc + 2, w // sc + 2))
        n = np.array(Image.fromarray(((n - n.min()) / (np.ptp(n) + 1e-9) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), float) / 255 - 0.5
        base += n[..., None] * amp * age
    base += rng.normal(0, 2.2, (h, w, 1))
    # darker, yellower edges
    y, x = np.mgrid[0:h, 0:w]
    e = np.minimum.reduce([x, w - 1 - x, y, h - 1 - y]) / (0.06 * min(w, h))
    edge = np.clip(1 - e, 0, 1) ** 2
    base -= edge[..., None] * np.array([28, 30, 40]) * age
    # a few coffee / water stains
    for _ in range(int(2 * age)):
        cx, cy, r = rng.uniform(0.1, 0.9) * w, rng.uniform(0.1, 0.9) * h, rng.uniform(0.04, 0.12) * w
        d = np.hypot(x - cx, y - cy) / r
        ring = np.exp(-((d - 1.0) / 0.06) ** 2) * 0.8 + (d < 1) * 0.25
        base -= ring[..., None] * np.array([10, 16, 26]) * age
    # fold creases
    for k in range(folds):
        yy = int(h * (k + 1) / (folds + 1))
        band = np.exp(-((y - yy) / 3.0) ** 2)
        base -= band[..., None] * 22
        base += np.exp(-((y - yy - 4) / 3.0) ** 2)[..., None] * 8
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    if lines:
        d = ImageDraw.Draw(img)
        for yy in range(int(h * 0.12), h - 20, int(h * 0.04)):
            d.line([(0, yy), (w, yy)], fill=(150, 170, 200), width=2)
    return img


def hand_text(img, xy, text, size, seed, ink=INK, spacing=1.0, jitter=1.0):
    """Hand-printed capitals: each character drawn on its own with a small rotation and wobble."""
    rng = random.Random(seed)
    font = F(HAND, size)
    x, y = xy
    for ch in text:
        if ch == ' ':
            x += size * 0.38 * spacing
            continue
        s = int(size * rng.uniform(0.92, 1.08))
        f = F(HAND, s) if s != size else font
        bb = f.getbbox(ch)
        cw, chh = bb[2] - bb[0] + 8, bb[3] - bb[1] + 8
        layer = Image.new('L', (cw * 2, chh * 2), 0)
        ImageDraw.Draw(layer).text((cw // 2 - bb[0], chh // 2 - bb[1]), ch, font=f, fill=255)
        layer = layer.filter(ImageFilter.MaxFilter(3)).rotate(rng.uniform(-6, 6) * jitter, resample=Image.BICUBIC)
        ox = int(x - cw // 2)
        oy = int(y - chh // 2 + rng.uniform(-0.06, 0.06) * size * jitter)
        img.paste(Image.new('RGB', layer.size, ink), (ox, oy), layer)
        x += (bb[2] - bb[0]) * spacing + size * 0.08
    return x


def typed(d, xy, text, size, font=TYPE, fill=TYPE_INK, seed=0):
    rng = random.Random(seed)
    f = F(font, size)
    x, y = xy
    for ch in text:
        g = rng.randint(-12, 10)
        d.text((x, y + rng.uniform(-0.6, 0.6)), ch, font=f, fill=tuple(max(0, c + g) for c in fill))
        x += f.getlength(ch)
    return x


def stamp(img, xy, text, size, angle, color=STAMP_RED, box=True, seed=0):
    f = F(BOLD, size)
    tw = int(f.getlength(text))
    pad = int(size * 0.25)
    layer = Image.new('L', (tw + pad * 4, int(size * 1.6) + pad * 2), 0)
    ld = ImageDraw.Draw(layer)
    ld.text((pad * 2, pad), text, font=f, fill=255)
    if box:
        ld.rectangle([pad // 2, pad // 3, layer.width - pad // 2, layer.height - pad // 3], outline=255, width=max(3, size // 12))
    # worn ink
    a = np.array(layer, float)
    rng = np.random.default_rng(seed)
    a *= np.clip(rng.normal(0.85, 0.25, a.shape), 0, 1)
    layer = Image.fromarray(a.astype(np.uint8)).rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(Image.new('RGB', layer.size, color), (int(xy[0] - layer.width / 2), int(xy[1] - layer.height / 2)), layer)


# ----------------------------------------------------------------------------------------------
# cipher glyphs (in the style of the Zodiac ciphers; NOT a transcription)
# ----------------------------------------------------------------------------------------------


def lines_block(d, x0, y0, w, rows, pitch, rng, fill=(95, 92, 88), width=7, para=9):
    """Grey 'text' lines standing in for newspaper / document body copy (unreadable by design)."""
    for k in range(rows):
        ln = rng.uniform(0.62, 1.0) * w if k % para != para - 1 else rng.uniform(0.2, 0.5) * w
        d.line([(x0, y0 + k * pitch), (x0 + ln, y0 + k * pitch)], fill=fill, width=width)




def halftone(img, box, kind, seed):
    """A newspaper halftone picture drawn by code (illustrative, not a real photograph)."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    pic = bw_scene(kind, seed, w, h)
    a = np.array(pic, float).mean(2)
    cell = 7
    out = np.full_like(a, 225.0)
    yy, xx = np.mgrid[0:h, 0:w]
    cy = (yy // cell) * cell + cell / 2
    cx = (xx // cell) * cell + cell / 2
    dark = 1 - a[np.clip(cy.astype(int), 0, h - 1), np.clip(cx.astype(int), 0, w - 1)] / 255.0
    r = np.hypot(yy - cy, xx - cx) / (cell * 0.72)
    out[r < np.sqrt(dark)] = 28.0
    im = Image.fromarray(out.astype(np.uint8)).convert('RGB')
    img.paste(im, (x0, y0))
    ImageDraw.Draw(img).rectangle(box, outline=(30, 30, 30), width=3)


def u2_plan(d, cx, cy, s, fill):
    """Top view of a U-2 (span 80 ft, length 50 ft), nose up; s = pixels per foot."""
    L, B = 50 * s, 80 * s
    d.ellipse([cx - 2.6 * s, cy - L * 0.5, cx + 2.6 * s, cy + L * 0.5], fill=fill)
    d.polygon([(cx - 2 * s, cy - 2 * s), (cx - B / 2, cy + 1.5 * s), (cx - B / 2, cy + 5.5 * s), (cx - 2 * s, cy + 9 * s),
               (cx + 2 * s, cy + 9 * s), (cx + B / 2, cy + 5.5 * s), (cx + B / 2, cy + 1.5 * s), (cx + 2 * s, cy - 2 * s)], fill=fill)
    d.polygon([(cx - 1.5 * s, cy + L * 0.36), (cx - 11 * s, cy + L * 0.42), (cx - 11 * s, cy + L * 0.47), (cx + 11 * s, cy + L * 0.47),
               (cx + 11 * s, cy + L * 0.42), (cx + 1.5 * s, cy + L * 0.36)], fill=fill)


def a12_plan(d, cx, cy, s, fill):
    """Top view of an A-12 (length 102 ft, span 55 ft), nose up; s = pixels per foot."""
    L, B = 102 * s, 55 * s
    top, bot = cy - L * 0.5, cy + L * 0.5
    d.polygon([(cx, top), (cx + 4.5 * s, top + 22 * s), (cx + 8 * s, top + 45 * s), (cx + B / 2, bot - 18 * s), (cx + B / 2, bot - 10 * s),
               (cx + 9 * s, bot - 6 * s), (cx + 3 * s, bot), (cx - 3 * s, bot), (cx - 9 * s, bot - 6 * s), (cx - B / 2, bot - 10 * s),
               (cx - B / 2, bot - 18 * s), (cx - 8 * s, top + 45 * s), (cx - 4.5 * s, top + 22 * s)], fill=fill)
    for sx in (-1, 1):
        nx = cx + sx * 15.5 * s
        d.rounded_rectangle([nx - 3.4 * s, top + 44 * s, nx + 3.4 * s, bot + 2 * s], int(3 * s), fill=fill)
        d.polygon([(nx, top + 36 * s), (nx - 2.6 * s, top + 45 * s), (nx + 2.6 * s, top + 45 * s)], fill=fill)


def bw_scene(kind, seed, w, h):
    """Grey-scale drawings (used for the halftones and 'photographs'): illustrative, not real photographs."""
    rng = np.random.default_rng(seed)
    yy = np.mgrid[0:h, 0:w][0].astype(float)
    if kind in ('lights', 'night_road'):
        sky = 40 + 50 * (yy / h)
    else:
        sky = 150 + 70 * (1 - yy / h)
    img = Image.fromarray(np.dstack([sky] * 3).astype(np.uint8)).convert('L').convert('RGB')
    d = ImageDraw.Draw(img)
    hz = h * 0.66
    # mountains on the horizon
    pts = [(0, h)]
    for x in np.linspace(0, w, 24):
        pts.append((x, hz - rng.uniform(10, 70) * (1 + math.sin(x / w * 5 + seed))))
    pts.append((w, h))
    d.polygon(pts, fill=(30, 30, 32) if kind in ('lights', 'night_road') else (110, 110, 112))
    d.rectangle([0, hz + 25, w, h], fill=(25, 25, 27) if kind in ('lights', 'night_road') else (170, 168, 160))
    if kind == 'lights':
        # a bright blurred point and a faint streak above the hills (an unidentified light)
        x0, y0 = w * rng.uniform(0.35, 0.65), h * rng.uniform(0.2, 0.35)
        d.line([(x0 - w * 0.22, y0 + h * 0.06), (x0, y0)], fill=(140, 140, 140), width=3)
        d.ellipse([x0 - 14, y0 - 14, x0 + 14, y0 + 14], fill=(250, 250, 250))
        for k in range(30):
            sx, sy = rng.uniform(0, w), rng.uniform(0, hz * 0.8)
            d.point((sx, sy), fill=(200, 200, 200))
    elif kind == 'night_road':
        d.polygon([(w * 0.45, hz + 25), (w * 0.55, hz + 25), (w * 0.95, h), (w * 0.05, h)], fill=(50, 50, 52))
        x0, y0 = w * 0.62, h * 0.28
        d.ellipse([x0 - 10, y0 - 10, x0 + 10, y0 + 10], fill=(245, 245, 245))
        d.rectangle([w * 0.18, hz - 20, w * 0.24, hz + 40], fill=(10, 10, 10))
    elif kind == 'u2':
        u2_plan(d, w / 2, h * 0.47, min(w, h) / 95, (60, 60, 62))
    elif kind == 'a12':
        a12_plan(d, w / 2, h * 0.5, min(w, h) / 120, (35, 35, 38))
    elif kind == 'base':
        d.rectangle([0, hz + 25, w, h], fill=(190, 188, 180))
        d.rectangle([w * 0.05, hz + 70, w * 0.95, hz + 86], fill=(90, 90, 92))
        for k in range(6):
            x0 = w * (0.08 + 0.14 * k)
            d.rectangle([x0, hz - 10, x0 + w * 0.1, hz + 40], fill=(120 - 8 * k, 120 - 8 * k, 122 - 8 * k))
    arr = np.array(img, float).mean(2)
    arr = np.array(Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.3)), float)
    arr += rng.normal(0, 8, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGB')


def photo_print(name, kind, seed, caption):
    w, h = 900, 700
    ph = bw_scene(kind, seed, w, h)
    a = np.array(ph, float)
    yy, xx = np.mgrid[0:h, 0:w]
    a *= (1 - 0.35 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2))[..., None]
    card = paper(w + 80, h + 200, seed + 5, tone=(236, 232, 222), age=0.3)
    card.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (40, 40))
    typed(ImageDraw.Draw(card), (50, h + 70), caption, 42, seed=seed)
    card.save(os.path.join(OUT, name + '.png'))


# ----------------------------------------------------------------------------------------------
# newspapers (generic, fictional mastheads; recreations)
# ----------------------------------------------------------------------------------------------
def front_page(name, masthead, date, lines, sub, seed, pic, place='NEVADA', second=None):
    w, h = 1400, 1900
    img = paper(w, h, seed, tone=(216, 208, 186), age=0.6)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    top = 70
    d.text((w / 2, top + 60), masthead, font=F(HEAD, 92), fill=(18, 18, 20), anchor='mm')
    d.line([(60, top + 130), (w - 60, top + 130)], fill=(30, 30, 30), width=4)
    d.text((70, top + 142), place, font=F(MONO, 30), fill=(40, 40, 40))
    d.text((w / 2, top + 142), date, font=F(MONO, 30), fill=(40, 40, 40), anchor='ma')
    d.text((w - 70, top + 142), '10 CENTS', font=F(MONO, 30), fill=(40, 40, 40), anchor='ra')
    d.line([(60, top + 185), (w - 60, top + 185)], fill=(30, 30, 30), width=2)
    y = top + 200
    for ln in lines:
        f = F(BOLD, 236)
        while f.getlength(ln) > w - 120:
            f = F(BOLD, f.size - 6)
        d.text((w / 2, y), ln, font=f, fill=(14, 14, 16), anchor='ma')
        y += int(f.size * 1.08)
    d.text((w / 2, y + 34), sub, font=F(HEAD, 54), fill=(28, 28, 28), anchor='ma')
    y += 124
    halftone(img, (80, y, 860, y + 560), pic, seed + 1)
    if second:
        d.text((1120, y + 10), second[0], font=F(BOLD, 60), fill=(18, 18, 20), anchor='ma')
        d.text((1120, y + 90), second[1], font=F(HEAD, 34), fill=(30, 30, 30), anchor='ma')
        lines_block(d, 900, y + 150, 420, 22, 19, rng)
    else:
        lines_block(d, 900, y, 420, 29, 19, rng)
    for col in range(4):
        lines_block(d, 80 + col * 315, y + 600, 290, int((h - y - 640) / 19), 19, rng)
    img.save(os.path.join(OUT, name + '.png'))


def tex_newspapers():
    # Generic headlines in the style of the period's UFO coverage. Fictional mastheads; no invented quotes.
    front_page('paper_lights', 'THE DESERT HERALD', 'LATE 1950s', ['PILOTS REPORT', 'STRANGE LIGHTS'],
               'Airline Crews Describe Objects Far Above Them', 301, 'lights', second=('AIR FORCE', 'Says Reports Are Being Studied'))
    front_page('paper_saucers', 'THE MORNING TRIBUNE', 'LATE 1950s', ['MORE SAUCER', 'SIGHTINGS'],
               'Reports Pour In From Across the West', 302, 'night_road')
    front_page('paper_what', 'THE WEEKLY OBSERVER', 'LATE 1950s', ['WHAT ARE THE', 'LIGHTS IN', 'THE SKY?'],
               'No Explanation Yet, Officials Say', 303, 'lights')


# ----------------------------------------------------------------------------------------------
# the archive (recreations; the CIA history's title is real)
# ----------------------------------------------------------------------------------------------
def folder(name, lines, seed, tone=(196, 168, 112), secret=True):
    w, h = 1300, 900
    img = paper(w, h, seed, tone=tone, age=0.9)
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, w - 60, h - 60], outline=(90, 70, 40), width=4)
    lab = paper(900, 330, seed + 1, tone=(236, 230, 214), age=0.3)
    ld = ImageDraw.Draw(lab)
    for k, (txt, size) in enumerate(lines):
        typed(ld, (40, 30 + sum(s * 1.45 for _, s in lines[:k])), txt, size, seed=seed + k)
    img.paste(lab, (200, 200))
    if secret:
        stamp(img, (w * 0.5, h * 0.78), 'TOP SECRET', 70, 3, seed=seed)
    img.save(os.path.join(OUT, name + '.png'))


def tex_folders():
    folder('folder_aquatone', [('PROJECT AQUATONE', 56), ('U-2 PROGRAM', 46), ('', 20), ('1954 - 1974', 46)], 401)
    folder('folder_oxcart', [('PROJECT OXCART', 56), ('A-12 PROGRAM', 46), ('', 20), ('1959 - 1968', 46)], 402, tone=(170, 150, 110))
    folder('folder_site', [('AREA 51', 60), ('GROOM LAKE, NEVADA', 44), ('', 20), ('SITE HISTORY', 46)], 403, tone=(186, 160, 118))


def tex_history_cover():
    """A recreation of the cover of the declassified CIA history (real title, authors and date)."""
    w, h = 1000, 1300
    img = paper(w, h, 420, tone=(232, 230, 222), age=0.35)
    d = ImageDraw.Draw(img)
    stamp(img, (w / 2, 110), 'DECLASSIFIED', 64, -2, color=(160, 34, 30), seed=1)
    y = 240
    for txt, size, fnt in (('THE CENTRAL', 58, HEAD), ('INTELLIGENCE AGENCY', 58, HEAD), ('AND', 44, HEAD), ('OVERHEAD', 58, HEAD),
                           ('RECONNAISSANCE', 58, HEAD), ('', 40, HEAD), ('The U-2 and OXCART Programs,', 40, HEAD),
                           ('1954 - 1974', 40, HEAD), ('', 70, HEAD), ('Gregory W. Pedlow', 34, MONO), ('Donald E. Welzenbach', 34, MONO),
                           ('', 50, HEAD), ('History Staff', 30, MONO), ('Central Intelligence Agency', 30, MONO), ('1992', 30, MONO)):
        if txt:
            d.text((w / 2, y), txt, font=F(fnt, size), fill=(26, 26, 30), anchor='ma')
        y += int(size * 1.32)
    d.text((w / 2, h - 70), 'RECREATION OF THE COVER - RELEASED 2013', font=F(MONO, 24), fill=(120, 120, 120), anchor='ma')
    img.save(os.path.join(OUT, 'cia_history.png'))


def tex_docs():
    heads = ['MEMORANDUM FOR THE RECORD', 'MEMORANDUM', 'PROJECT OXCART', 'MEMORANDUM', 'SITE REPORT', 'SUMMARY']
    for k in range(6):
        w, h = 850, 1100
        img = paper(w, h, 500 + k, tone=(232, 228, 214), age=0.5)
        d = ImageDraw.Draw(img)
        rng = np.random.default_rng(510 + k)
        typed(d, (70, 70), heads[k], 40, font=MONO, seed=k)
        lines_block(d, 70, 150, 690, 4, 30, rng, fill=(70, 70, 72), width=6, para=99)
        y = 300
        for b in range(int(rng.integers(3, 6))):
            n = int(rng.integers(3, 8))
            lines_block(d, 70, y, 700, n, 30, rng, fill=(80, 80, 82), width=6, para=99)
            for _ in range(int(rng.integers(0, 3))):                    # redaction bars
                ry = y + int(rng.integers(0, n)) * 30 - 10
                rx = 70 + int(rng.uniform(0, 300))
                d.rectangle([rx, ry, rx + int(rng.uniform(120, 380)), ry + 22], fill=(12, 12, 14))
            y += n * 30 + 40
        stamp(img, (w * 0.76, 210), 'SECRET', 40, -4, color=(150, 40, 36), seed=k)
        d.line([(w * 0.66, 192), (w * 0.86, 228)], fill=(30, 30, 30), width=5)          # struck out: declassified
        img.save(os.path.join(OUT, f'doc_{k}.png'))


def tex_map():
    """Illustrative sketch map: southern Nevada, Las Vegas, the test site and Groom Lake (not a copy of a real map)."""
    w, h = 1100, 1400
    img = paper(w, h, 470, tone=(230, 226, 210), age=0.5)
    d = ImageDraw.Draw(img)
    typed(d, (70, 60), 'SOUTHERN NEVADA - SKETCH MAP', 44, font=MONO, seed=1)
    d.rectangle([70, 140, w - 70, h - 140], outline=(60, 60, 60), width=3)
    rng = np.random.default_rng(471)
    for k in range(60):                                                  # ridges
        x, y = rng.uniform(100, w - 100), rng.uniform(170, h - 170)
        a = rng.uniform(0, math.pi)
        d.line([(x, y), (x + 60 * math.cos(a), y + 60 * math.sin(a))], fill=(160, 150, 130), width=3)
    gx, gy = 640, 430
    d.ellipse([gx - 60, gy - 90, gx + 60, gy + 90], fill=(244, 242, 232), outline=(80, 80, 80), width=3)
    d.text((gx + 80, gy - 20), 'GROOM LAKE', font=F(MONO, 34), fill=(30, 30, 30))
    d.rectangle([gx - 150, gy - 130, gx + 260, gy + 170], outline=(170, 30, 28), width=5)
    d.text((gx - 140, gy + 180), 'AREA 51', font=F(BOLD, 64), fill=(170, 30, 28))
    d.rectangle([180, 600, 620, 1000], outline=(60, 60, 60), width=3)
    d.text((200, 1010), 'NEVADA TEST SITE', font=F(MONO, 30), fill=(40, 40, 40))
    lx, ly = 860, 1180
    d.ellipse([lx - 14, ly - 14, lx + 14, ly + 14], fill=(30, 30, 30))
    d.text((lx - 20, ly + 24), 'LAS VEGAS', font=F(MONO, 34), fill=(30, 30, 30), anchor='ra')
    d.line([(lx, ly), (gx + 30, gy + 100)], fill=(120, 120, 120), width=2)
    d.text(((lx + gx) / 2 + 30, (ly + gy) / 2 + 40), '~80 MI', font=F(MONO, 30), fill=(90, 90, 90))
    d.text((w / 2, h - 90), 'ILLUSTRATIVE SKETCH', font=F(MONO, 26), fill=(120, 120, 120), anchor='ma')
    img.save(os.path.join(OUT, 'map51.png'))


def tex_photos():
    photo_print('photo_u2', 'u2', 451, 'U-2  (ILLUSTRATION)')
    photo_print('photo_a12', 'a12', 452, 'A-12 OXCART  (ILLUSTRATION)')
    photo_print('photo_base', 'base', 453, 'GROOM LAKE  (ILLUSTRATION)')


def stamp_tex(name, text, color, size=120):
    f = F(BOLD, size)
    tw = int(f.getlength(text))
    img = Image.new('RGBA', (tw + 120, int(size * 1.9)), (0, 0, 0, 0))
    layer = Image.new('L', img.size, 0)
    ld = ImageDraw.Draw(layer)
    ld.text((60, int(size * 0.3)), text, font=f, fill=255)
    ld.rectangle([12, 12, img.width - 12, img.height - 12], outline=255, width=10)
    a = np.array(layer, float) * np.clip(np.random.default_rng(len(text)).normal(0.85, 0.22, layer.size[::-1]), 0, 1)
    img.paste(Image.new('RGBA', img.size, color + (255,)), (0, 0), Image.fromarray(a.astype(np.uint8)))
    img.save(os.path.join(OUT, name + '.png'))


def tex_stamps():
    stamp_tex('stamp_declass', 'DECLASSIFIED', (170, 30, 28))
    stamp_tex('stamp_2013', 'RELEASED 2013', (30, 50, 120))


def tex_boxlabels():
    """8 archive-box end labels in one atlas (columns of 4 x 2)."""
    W, Hh = 1024, 512
    img = Image.new('RGB', (W, Hh), (180, 160, 120))
    d = ImageDraw.Draw(img)
    for k in range(8):
        x0, y0 = (k % 4) * 256, (k // 4) * 256
        d.rectangle([x0 + 40, y0 + 60, x0 + 216, y0 + 196], fill=(236, 230, 214))
        d.text((x0 + 128, y0 + 100), 'BOX', font=F(MONO, 30), fill=(40, 40, 40), anchor='mm')
        d.text((x0 + 128, y0 + 150), f'{51 + 23 * k:04d}', font=F(MONO, 40), fill=(40, 40, 40), anchor='mm')
        d.ellipse([x0 + 108, y0 + 214, x0 + 148, y0 + 236], fill=(90, 74, 50))
    img.save(os.path.join(OUT, 'boxlabels.png'))


# ----------------------------------------------------------------------------------------------
# the perimeter: warning signs (wording as widely photographed at the boundary; recreated, not copied)
# ----------------------------------------------------------------------------------------------
def tex_signs():
    w, h = 1200, 1500
    a = np.ones((h, w, 3)) * np.array((226, 224, 214), float)
    rng = np.random.default_rng(431)
    a += rng.normal(0, 3, (h, w, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    a -= (np.clip(1 - np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]) / 50.0, 0, 1) ** 2)[..., None] * 40
    for _ in range(40):                                                  # sand-blasted pits and rust streaks
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a[int(y):int(y + rng.uniform(20, 160)), int(x):int(x + rng.uniform(2, 6))] *= rng.uniform(0.75, 0.92)
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.rectangle([30, 30, w - 30, h - 30], outline=(30, 30, 30), width=10)
    d.rectangle([60, 60, w - 60, 300], fill=(178, 32, 28))
    d.text((w / 2, 180), 'WARNING', font=F(BOLD, 190), fill=(240, 236, 226), anchor='mm')
    d.text((w / 2, 420), 'RESTRICTED', font=F(BOLD, 200), fill=(20, 20, 22), anchor='mm')
    d.text((w / 2, 630), 'AREA', font=F(BOLD, 200), fill=(20, 20, 22), anchor='mm')
    for k, (txt, sz) in enumerate((('NO TRESPASSING', 84), ('BEYOND THIS POINT', 84))):
        d.text((w / 2, 820 + k * 100), txt, font=F(BOLD, sz), fill=(30, 30, 32), anchor='mm')
    d.text((w / 2, 1060), 'PHOTOGRAPHY OF THIS AREA', font=F(BOLD, 64), fill=(30, 30, 32), anchor='mm')
    d.text((w / 2, 1140), 'IS PROHIBITED', font=F(BOLD, 64), fill=(30, 30, 32), anchor='mm')
    d.rectangle([60, 1230, w - 60, h - 60], fill=(178, 32, 28))
    d.text((w / 2, 1335), 'USE OF DEADLY FORCE AUTHORIZED', font=F(BOLD, 74), fill=(240, 236, 226), anchor='mm')
    img.save(os.path.join(OUT, 'sign_restricted.png'))
    w, h = 900, 600
    img = Image.new('RGB', (w, h), (222, 220, 210))
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, w - 20, h - 20], outline=(30, 30, 30), width=8)
    d.text((w / 2, 150), 'MILITARY', font=F(BOLD, 130), fill=(20, 20, 22), anchor='mm')
    d.text((w / 2, 300), 'INSTALLATION', font=F(BOLD, 110), fill=(20, 20, 22), anchor='mm')
    d.rectangle([50, 390, w - 50, 540], fill=(178, 32, 28))
    d.text((w / 2, 465), 'NO TRESPASSING', font=F(BOLD, 96), fill=(240, 236, 226), anchor='mm')
    img.save(os.path.join(OUT, 'sign_small.png'))


def main():
    os.makedirs(OUT, exist_ok=True)
    for fn in (tex_newspapers, tex_folders, tex_history_cover, tex_docs, tex_map, tex_photos, tex_stamps, tex_boxlabels, tex_signs):
        fn()
    print('textures written to', OUT, len(os.listdir(OUT)))


if __name__ == '__main__':
    main()
