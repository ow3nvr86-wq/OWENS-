"""Procedural document textures for the Zodiac Killer Short (PIL + numpy, code only).

Draws every paper prop the 3D scene uses: the recreated letter, envelope, the three 408-cipher parts,
the glyph atlas for the 340-cipher tiles, the newspaper, index cards for the timeline board, the map
of the confirmed attack sites, location "photographs", the fingerprint card, case-file labels and
notes. Writes PNGs to build/tex/. animation.py runs this automatically when the folder is missing.

    $SHORTS_PY tools/textures.py

Accuracy notes (see research_sources.md): the cipher glyphs are generated in the style of the Zodiac
ciphers and are NOT a transcription of the real ones. The only real wording used is "DEAR EDITOR / THIS
IS THE ZODIAC SPEAKING", the 408 phrase "I WILL NOT GIVE YOU MY NAME" and the first line of the decoded
340. The newspaper masthead is generic. No suspect is named anywhere.
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

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


def zodiac_symbol(img, cx, cy, r, width, seed, ink=INK):
    """The crossed-circle signature: a circle with a cross whose arms run past the rim."""
    rng = random.Random(seed)
    d = ImageDraw.Draw(img)
    pts = []
    for k in range(73):
        a = k / 72 * 2 * math.pi
        rr = r * (1 + 0.025 * math.sin(3 * a + rng.random()) + rng.uniform(-0.006, 0.006))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.line(pts, fill=ink, width=width, joint='curve')
    ext = 1.32
    d.line([(cx - r * ext + rng.uniform(-3, 3), cy + rng.uniform(-3, 3)), (cx + r * ext, cy + rng.uniform(-4, 4))], fill=ink, width=width)
    d.line([(cx + rng.uniform(-3, 3), cy - r * ext), (cx + rng.uniform(-4, 4), cy + r * ext)], fill=ink, width=width)


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
UPRIGHT = list('ABCDEFGHIJKLMNPRSTUVWYZ')        # 23
MIRROR = list('EFJKLPRYBDQ')                     # 11 reversed letters
FLIP = list('ATVKMLY')                           # 7 upside-down
SHAPES = ['tri', 'tri_f', 'tri_d', 'sq', 'sq_dot', 'sq_half', 'circ', 'circ_dot', 'circ_half', 'circ_q', 'circ_h',
          'circ_v', 'plus', 'slash', 'bslash', 'caret', 'lt', 'gt', 'bar', 'colon', 'dot_tri', 'diamond']   # 22
GLYPHS = [('u', c) for c in UPRIGHT] + [('m', c) for c in MIRROR] + [('f', c) for c in FLIP] + [('s', s) for s in SHAPES]
assert len(GLYPHS) == 63


def draw_glyph(img, gi, cx, cy, s, seed, ink=INK, width=None):
    """Draw glyph gi centred at (cx, cy), about s px tall."""
    kind, g = GLYPHS[gi]
    rng = random.Random(seed)
    w = width or max(3, int(s * 0.09))
    if kind in 'umf':
        size = int(s * 1.05)
        f = F(HAND, size)
        bb = f.getbbox(g)
        L = Image.new('L', (int(s * 2), int(s * 2)), 0)
        ImageDraw.Draw(L).text((s - (bb[0] + bb[2]) / 2, s - (bb[1] + bb[3]) / 2), g, font=f, fill=255)
        if kind == 'm':
            L = ImageOps.mirror(L)
        if kind == 'f':
            L = L.rotate(180)
        L = L.filter(ImageFilter.MaxFilter(3)).rotate(rng.uniform(-6, 6), resample=Image.BICUBIC)
        img.paste(Image.new('RGB', L.size, ink), (int(cx - s), int(cy - s)), L)
        return
    d = ImageDraw.Draw(img)
    h = s * 0.42
    j = lambda: rng.uniform(-0.04, 0.04) * s  # noqa: E731
    if g in ('tri', 'tri_f', 'dot_tri'):
        pts = [(cx + j(), cy - h + j()), (cx + h + j(), cy + h * 0.85 + j()), (cx - h + j(), cy + h * 0.85 + j())]
        if g == 'tri_f':
            d.polygon(pts, fill=ink)
        else:
            d.line(pts + [pts[0]], fill=ink, width=w, joint='curve')
        if g == 'dot_tri':
            d.ellipse([cx - w, cy + h * 0.2 - w, cx + w, cy + h * 0.2 + w], fill=ink)
    elif g == 'tri_d':
        pts = [(cx + j(), cy + h + j()), (cx + h + j(), cy - h * 0.85 + j()), (cx - h + j(), cy - h * 0.85 + j())]
        d.line(pts + [pts[0]], fill=ink, width=w, joint='curve')
    elif g.startswith('sq'):
        q = h * 0.85
        box = [cx - q + j(), cy - q + j(), cx + q + j(), cy + q + j()]
        if g == 'sq_half':
            d.rectangle([box[0], cy, box[2], box[3]], fill=ink)
        d.rectangle(box, outline=ink, width=w)
        if g == 'sq_dot':
            d.ellipse([cx - w * 1.2, cy - w * 1.2, cx + w * 1.2, cy + w * 1.2], fill=ink)
    elif g.startswith('circ'):
        box = [cx - h + j(), cy - h + j(), cx + h + j(), cy + h + j()]
        if g == 'circ_half':
            d.pieslice(box, 90, 270, fill=ink)
        if g == 'circ_q':
            d.pieslice(box, 270, 360, fill=ink)
        d.ellipse(box, outline=ink, width=w)
        if g == 'circ_dot':
            d.ellipse([cx - w * 1.2, cy - w * 1.2, cx + w * 1.2, cy + w * 1.2], fill=ink)
        if g == 'circ_h':
            d.line([(cx - h, cy), (cx + h, cy)], fill=ink, width=w)
        if g == 'circ_v':
            d.line([(cx, cy - h * 1.35), (cx, cy + h * 1.35)], fill=ink, width=w)
    elif g == 'plus':
        d.line([(cx - h, cy + j()), (cx + h, cy + j())], fill=ink, width=w)
        d.line([(cx + j(), cy - h), (cx + j(), cy + h)], fill=ink, width=w)
    elif g == 'slash':
        d.line([(cx - h * 0.6, cy + h), (cx + h * 0.6, cy - h)], fill=ink, width=w)
    elif g == 'bslash':
        d.line([(cx - h * 0.6, cy - h), (cx + h * 0.6, cy + h)], fill=ink, width=w)
    elif g == 'caret':
        d.line([(cx - h, cy + h * 0.5), (cx, cy - h * 0.6), (cx + h, cy + h * 0.5)], fill=ink, width=w, joint='curve')
    elif g == 'lt':
        d.line([(cx + h * 0.6, cy - h), (cx - h * 0.6, cy), (cx + h * 0.6, cy + h)], fill=ink, width=w, joint='curve')
    elif g == 'gt':
        d.line([(cx - h * 0.6, cy - h), (cx + h * 0.6, cy), (cx - h * 0.6, cy + h)], fill=ink, width=w, joint='curve')
    elif g == 'bar':
        d.line([(cx + j(), cy - h), (cx + j(), cy + h)], fill=ink, width=w)
    elif g == 'colon':
        for yy in (cy - h * 0.45, cy + h * 0.45):
            d.ellipse([cx - w * 1.3, yy - w * 1.3, cx + w * 1.3, yy + w * 1.3], fill=ink)
    elif g == 'diamond':
        pts = [(cx, cy - h), (cx + h * 0.8, cy), (cx, cy + h), (cx - h * 0.8, cy)]
        d.line(pts + [pts[0]], fill=ink, width=w, joint='curve')


def cipher_rows(rng, n):
    return [int(rng.integers(0, 63)) for _ in range(n)]


def cipher_sheet(path, seed, cols=17, rows=8, w=1400, h=900, title=None):
    img = paper(w, h, seed, age=0.8, folds=1)
    rng = np.random.default_rng(seed)
    mx, my = 90, 120 if title else 80
    cw, chh = (w - 2 * mx) / cols, (h - my - 70) / rows
    s = min(cw, chh) * 0.78
    for r in range(rows):
        for c in range(cols):
            gi = int(rng.integers(0, 63))
            draw_glyph(img, gi, mx + (c + 0.5) * cw + rng.normal(0, 2), my + (r + 0.5) * chh + rng.normal(0, 2), s, seed * 1000 + r * 31 + c)
    img.save(path)


# ----------------------------------------------------------------------------------------------
# individual textures
# ----------------------------------------------------------------------------------------------
def tex_letter():
    w, h = 1700, 2200
    img = paper(w, h, 11, tone=(232, 226, 210), age=0.7, folds=2)
    hand_text(img, (150, 230), 'DEAR EDITOR', 120, 1)
    hand_text(img, (150, 420), 'THIS IS THE ZODIAC', 120, 2)
    hand_text(img, (150, 590), 'SPEAKING.', 120, 3)
    # illustrative cipher rows (not a transcription)
    rng = np.random.default_rng(21)
    for r in range(4):
        for c in range(13):
            draw_glyph(img, int(rng.integers(0, 63)), 190 + c * 102, 1010 + r * 135, 92, 500 + r * 13 + c)
    zodiac_symbol(img, 1250, 1840, 150, 16, 4)
    img.save(os.path.join(OUT, 'letter.png'))


def tex_envelope():
    w, h = 1600, 900
    img = paper(w, h, 12, tone=(236, 230, 214), age=0.5)
    d = ImageDraw.Draw(img)
    # stamps (generic, no denominations from real issues) and wavy cancel lines
    for k in range(2):
        x0 = 1180 + k * 170
        d.rectangle([x0, 70, x0 + 140, 240], fill=(120, 40, 46))
        d.rectangle([x0 + 12, 82, x0 + 128, 228], outline=(230, 220, 200), width=4)
    for k in range(5):
        pts = [(1000 + i * 12, 120 + k * 28 + 8 * math.sin(i * 0.5)) for i in range(45)]
        d.line(pts, fill=(40, 40, 50), width=4)
    hand_text(img, (360, 420), 'EDITOR', 96, 31)
    hand_text(img, (360, 540), 'S.F. CHRONICLE', 96, 32)
    hand_text(img, (360, 660), 'SAN FRANCISCO CALIF', 96, 33)
    zodiac_symbol(img, 190, 160, 70, 10, 5)
    img.save(os.path.join(OUT, 'envelope.png'))


def tex_cipher_parts():
    for k in range(3):
        cipher_sheet(os.path.join(OUT, f'c408_{k}.png'), 40 + k)


def tex_strip408():
    w, h = 1400, 160
    img = paper(w, h, 50, tone=(240, 236, 222), age=0.3)
    d = ImageDraw.Draw(img)
    typed(d, (60, 42), 'I WILL NOT GIVE YOU MY NAME', 72, seed=3)
    img.save(os.path.join(OUT, 'strip408.png'))


def tex_atlas():
    """Glyph atlas for the 340 tiles: 12 x 8 cells of 128 px. 0-62 glyphs, 63-88 A-Z (typed), 89 blank."""
    cs = 128
    img = Image.new('RGB', (12 * cs, 8 * cs))
    for i in range(96):
        cx, cy = (i % 12) * cs, (i // 12) * cs
        tile = paper(cs, cs, 600 + i, tone=(228, 218, 192), age=0.25)
        if i < 63:
            draw_glyph(tile, i, cs / 2, cs / 2, cs * 0.7, 900 + i, width=7)
        elif i < 89:
            d = ImageDraw.Draw(tile)
            f = F(BOLD, 100)
            ch = chr(ord('A') + i - 63)
            bb = f.getbbox(ch)
            d.text((cs / 2 - (bb[0] + bb[2]) / 2, cs / 2 - (bb[1] + bb[3]) / 2), ch, font=f, fill=(120, 18, 16))
        img.paste(tile, (cx, cy))
    img.save(os.path.join(OUT, 'atlas.png'))


def tex_newspaper():
    w, h = 1400, 1900
    img = paper(w, h, 70, tone=(214, 206, 184), age=0.6)
    d = ImageDraw.Draw(img)
    d.text((w / 2, 110), 'THE EVENING EDITION', font=F(HEAD, 96), fill=(20, 20, 22), anchor='mm')
    d.line([(60, 190), (w - 60, 190)], fill=(30, 30, 30), width=4)
    d.text((70, 205), 'NORTHERN CALIFORNIA', font=F(MONO, 30), fill=(40, 40, 40))
    d.text((w - 70, 205), 'FINAL  10 CENTS', font=F(MONO, 30), fill=(40, 40, 40), anchor='ra')
    d.line([(60, 250), (w - 60, 250)], fill=(30, 30, 30), width=2)
    d.text((w / 2, 360), 'CODE LETTER SENT', font=F(BOLD, 150), fill=(18, 18, 20), anchor='mm')
    d.text((w / 2, 520), 'TO NEWSPAPERS', font=F(BOLD, 150), fill=(18, 18, 20), anchor='mm')
    d.text((w / 2, 640), 'Writer Claims Two Attacks; Police Study Cipher', font=F(HEAD, 54), fill=(30, 30, 30), anchor='mm')
    # the printed cipher panel (illustrative glyphs)
    d.rectangle([80, 720, 820, 1260], outline=(30, 30, 30), width=3)
    rng = np.random.default_rng(71)
    for r in range(8):
        for c in range(12):
            draw_glyph(img, int(rng.integers(0, 63)), 120 + c * 58, 760 + r * 62, 46, 700 + r * 12 + c, ink=(20, 20, 24), width=4)
    # body columns as grey "text" lines
    for col in range(2):
        x0 = 860 + col * 255
        for k in range(28):
            y = 730 + k * 19
            ln = rng.uniform(0.6, 1.0) * 230 if k % 9 != 8 else rng.uniform(0.2, 0.5) * 230
            d.line([(x0, y), (x0 + ln, y)], fill=(95, 92, 88), width=7)
    for col in range(4):
        x0 = 80 + col * 315
        for k in range(30):
            y = 1300 + k * 19
            ln = rng.uniform(0.7, 1.0) * 290 if k % 11 != 10 else rng.uniform(0.2, 0.5) * 290
            d.line([(x0, y), (x0 + ln, y)], fill=(95, 92, 88), width=7)
    img.save(os.path.join(OUT, 'newspaper.png'))


CARDS = [('DEC 20, 1968', 'LAKE HERMAN ROAD', 'BENICIA'),
         ('JUL 4-5, 1969', 'BLUE ROCK SPRINGS', 'VALLEJO'),
         ('AUG 1, 1969', 'LETTERS TO 3 PAPERS', '408 CIPHER IN 3 PARTS'),
         ('AUG 1969', '408 CIPHER SOLVED', 'NO NAME GIVEN'),
         ('SEP 27, 1969', 'LAKE BERRYESSA', 'NAPA COUNTY'),
         ('OCT 11, 1969', 'PRESIDIO HEIGHTS', 'SAN FRANCISCO'),
         ('NOV 8, 1969', '340 CIPHER MAILED', 'UNSOLVED'),
         ('DEC 2020', '340 CIPHER SOLVED', 'STILL NO NAME')]


def tex_cards():
    for k, (date, l1, l2) in enumerate(CARDS):
        w, h = 900, 540
        img = paper(w, h, 80 + k, tone=(238, 234, 220), age=0.4)
        d = ImageDraw.Draw(img)
        for yy in range(150, h, 62):
            d.line([(0, yy), (w, yy)], fill=(150, 175, 205), width=3)
        d.line([(0, 118), (w, 118)], fill=(200, 90, 90), width=4)
        typed(d, (50, 40), date, 70, seed=k)
        typed(d, (50, 210), l1, 58, seed=k + 10)
        typed(d, (50, 330), l2, 50, seed=k + 20, fill=(70, 60, 60))
        img.save(os.path.join(OUT, f'card_{k}.png'))


def tex_decoded():
    w, h = 1300, 900
    img = paper(w, h, 90, tone=(240, 236, 224), age=0.4)
    d = ImageDraw.Draw(img)
    typed(d, (70, 60), '340 CIPHER  -  DECODED DEC. 2020', 52, seed=1)
    d.line([(70, 135), (w - 70, 135)], fill=(60, 60, 60), width=3)
    for k, line in enumerate(['I HOPE YOU ARE HAVING', 'LOTS OF FUN IN TRYING', 'TO CATCH ME . . .']):
        typed(d, (70, 220 + k * 105), line, 74, seed=5 + k)
    img.save(os.path.join(OUT, 'decoded.png'))
    # the NO NAME stamp as its own transparent decal (it is stamped onto the card in the board shot)
    st = Image.new('RGB', (900, 420), (0, 0, 0))
    stamp(st, (450, 210), 'NO NAME', 150, 6, color=(255, 255, 255), seed=3)
    a = np.array(st.convert('L'))
    rgba = np.zeros((420, 900, 4), np.uint8)
    rgba[..., :3] = STAMP_RED
    rgba[..., 3] = a
    Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, 'stamp_noname.png'))


# confirmed attack sites, approximate (lat, lon); see research_sources.md
SITES = [('LAKE HERMAN RD', 38.093, -122.144), ('BLUE ROCK SPRINGS', 38.128, -122.198),
         ('LAKE BERRYESSA', 38.567, -122.235), ('PRESIDIO HEIGHTS, S.F.', 37.789, -122.452)]
MAP_BOX = (37.70, 38.70, -122.62, -121.92)       # lat0, lat1, lon0, lon1


def map_xy(lat, lon, w, h, m=110):
    la0, la1, lo0, lo1 = MAP_BOX
    return m + (lon - lo0) / (lo1 - lo0) * (w - 2 * m), h - m - (lat - la0) / (la1 - la0) * (h - 2 * m)


def tex_map():
    w, h = 1500, 2000
    img = paper(w, h, 100, tone=(222, 216, 196), age=0.5, folds=1)
    d = ImageDraw.Draw(img)
    la0, la1, lo0, lo1 = MAP_BOX
    for lat in np.arange(37.8, 38.71, 0.1):
        x0, y = map_xy(lat, lo0, w, h)
        x1, _ = map_xy(lat, lo1, w, h)
        d.line([(x0, y), (x1, y)], fill=(150, 160, 170), width=2)
        d.text((x0 - 8, y), f'{lat:.1f}N', font=F(MONO, 26), fill=(90, 95, 100), anchor='rm')
    for lon in np.arange(-122.6, -121.91, 0.1):
        x, y0 = map_xy(la0, lon, w, h)
        _, y1 = map_xy(la1, lon, w, h)
        d.line([(x, y0), (x, y1)], fill=(150, 160, 170), width=2)
        d.text((x, y0 + 14), f'{-lon:.1f}W', font=F(MONO, 26), fill=(90, 95, 100), anchor='ma')
    typed(d, (110, 40), 'CONFIRMED ATTACK SITES (APPROX.)', 60, seed=4)
    for k, (name, lat, lon) in enumerate(SITES):
        x, y = map_xy(lat, lon, w, h)
        d.ellipse([x - 26, y - 26, x + 26, y + 26], outline=(160, 30, 28), width=6)
        dx, dy = {0: (40, 10), 1: (-560, -70), 2: (-520, -80), 3: (40, -20)}[k]
        typed(d, (x + dx, y + dy), name, 46, seed=10 + k, fill=(40, 30, 30))
    # scale bar: 10 km
    km = 10 / (111.0 * math.cos(math.radians(38.2)))
    xa, ya = map_xy(37.76, -122.05, w, h)
    xb, _ = map_xy(37.76, -122.05 + km, w, h)
    d.line([(xa, ya), (xb, ya)], fill=(40, 40, 40), width=6)
    d.text(((xa + xb) / 2, ya - 20), '10 KM', font=F(MONO, 30), fill=(40, 40, 40), anchor='mb')
    img.save(os.path.join(OUT, 'map.png'))


def bw_photo(kind, seed, caption):
    """A grainy black-and-white location photo drawn by code (illustrative, not a real photograph)."""
    w, h = 900, 700
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(float)
    sky = 70 + 50 * (1 - y / h)
    img = Image.fromarray(np.dstack([sky] * 3).astype(np.uint8))
    d = ImageDraw.Draw(img)
    hz = h * 0.48
    if kind == 'road':
        pts = [(0, hz - 30)] + [(xx, hz - 40 - 50 * math.sin(xx / w * 3 + 1) ** 2) for xx in range(0, w + 1, 30)] + [(w, h), (0, h)]
        d.polygon(pts, fill=(52, 52, 52))
        d.polygon([(w * 0.47, hz), (w * 0.53, hz), (w * 0.95, h), (w * 0.05, h)], fill=(38, 38, 40))
        for k in range(12):
            px = w * 0.08 + k * 70
            d.line([(px, hz + 70 + k * 10), (px, hz + 40 + k * 10)], fill=(25, 25, 25), width=5)
    elif kind == 'lot':
        d.rectangle([0, hz, w, h], fill=(60, 60, 62))
        d.polygon([(0, hz), (w, hz - 20), (w, hz - 120), (w * 0.6, hz - 160), (0, hz - 90)], fill=(40, 42, 40))
        d.line([(w * 0.7, h * 0.15), (w * 0.7, hz + 30)], fill=(30, 30, 30), width=8)
        d.ellipse([w * 0.67, h * 0.13, w * 0.73, h * 0.17], fill=(220, 220, 210))
        for k in range(6):
            d.line([(k * 160, h), (k * 160 + 220, hz + 10)], fill=(150, 150, 150), width=3)
    elif kind == 'lake':
        d.rectangle([0, hz, w, h], fill=(95, 98, 100))
        d.polygon([(0, hz)] + [(xx, hz - 60 - 60 * abs(math.sin(xx / 170.0))) for xx in range(0, w + 1, 20)] + [(w, hz)], fill=(48, 50, 48))
        for k in range(9):
            tx = rng.uniform(0, w)
            d.ellipse([tx - 60, h * 0.62, tx + 60, h * 0.95], fill=(35, 37, 35))
    elif kind == 'city':
        d.rectangle([0, hz + 60, w, h], fill=(55, 55, 58))
        for k in range(8):
            x0 = k * 120 - 20
            top = hz - rng.uniform(40, 200)
            d.rectangle([x0, top, x0 + 112, hz + 60], fill=(int(70 + 20 * (k % 2)),) * 3)
            for wy in range(int(top) + 20, int(hz + 40), 46):
                for wx in range(x0 + 14, x0 + 100, 34):
                    d.rectangle([wx, wy, wx + 18, wy + 26], fill=(40, 40, 44))
        d.line([(0, hz + 110), (w, hz + 110)], fill=(140, 140, 140), width=3)
    arr = np.array(img, float).mean(2)
    arr = np.array(Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)), float)
    arr += rng.normal(0, 9, arr.shape)
    yy, xx = np.mgrid[0:h, 0:w]
    arr *= 1 - 0.35 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    ph = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGB')
    card = paper(w + 80, h + 200, seed + 5, tone=(236, 232, 222), age=0.3)
    card.paste(ph, (40, 40))
    typed(ImageDraw.Draw(card), (50, h + 70), caption, 48, seed=seed)
    return card


def tex_photos():
    for k, (kind, cap) in enumerate((('road', 'LAKE HERMAN RD.'), ('lot', 'BLUE ROCK SPRINGS'),
                                     ('lake', 'LAKE BERRYESSA'), ('city', 'PRESIDIO HEIGHTS'))):
        bw_photo(kind, 120 + k, cap).save(os.path.join(OUT, f'photo_{k}.png'))


def whorl(d, cx, cy, r, seed):
    rng = random.Random(seed)
    for k in range(18):
        rr = r * (k + 1) / 18
        pts = []
        start = rng.uniform(0, 6.28)
        for i in range(60):
            a = start + i / 59 * 2 * math.pi * rng.uniform(0.75, 0.97)
            q = rr * (1 + 0.08 * math.sin(3 * a))
            pts.append((cx + q * 1.0 * math.cos(a), cy + q * 1.3 * math.sin(a)))
        d.line(pts, fill=(30, 30, 34), width=5)


def tex_fingerprint():
    w, h = 1300, 900
    img = paper(w, h, 140, tone=(240, 238, 230), age=0.3)
    d = ImageDraw.Draw(img)
    typed(d, (60, 50), 'LATENT PRINT COMPARISON', 56, seed=2)
    for k, lab in enumerate(('EVIDENCE', 'COMPARISON')):
        x0 = 120 + k * 580
        d.rectangle([x0, 170, x0 + 480, 760], outline=(60, 60, 60), width=4)
        whorl(d, x0 + 240, 465, 190, 7 + k * 3)
        typed(d, (x0, 790), lab, 44, seed=k + 5)
    img.save(os.path.join(OUT, 'fingerprint.png'))


def tex_handwriting():
    w, h = 1300, 1000
    img = paper(w, h, 150, tone=(238, 236, 228), age=0.4, lines=True)
    d = ImageDraw.Draw(img)
    typed(d, (60, 40), 'HANDWRITING COMPARISON', 56, seed=3)
    hand_text(img, (90, 330), 'DEAR EDITOR', 104, 61)
    hand_text(img, (90, 460), 'THIS IS THE', 104, 62)
    typed(d, (80, 560), 'QUESTIONED', 40, seed=4)
    hand_text(img, (90, 730), 'DEAR EDITOR', 98, 71, ink=(40, 40, 46), jitter=1.6)
    hand_text(img, (90, 850), 'THIS IS THE', 98, 72, ink=(40, 40, 46), jitter=1.6)
    typed(d, (80, 930), 'EXEMPLAR', 40, seed=5)
    img.save(os.path.join(OUT, 'handwriting.png'))


def tex_labels():
    specs = {'file_open': ('CASE FILE', 'ZODIAC', 'OPEN'), 'file_unsolved': ('HOMICIDE', 'CASE NO. ______', 'UNSOLVED'),
             'file_suspect': ('SUSPECT FILE', '______________', 'NOT CHARGED'), 'file_lab': ('EVIDENCE', 'STAMP & ENVELOPE', 'PARTIAL DNA - 2002')}
    for k, (name, (a, b, st)) in enumerate(specs.items()):
        w, h = 1200, 820
        img = paper(w, h, 160 + k, tone=(196, 168, 118), age=0.7)
        d = ImageDraw.Draw(img)
        d.rectangle([80, 70, 760, 330], fill=(234, 228, 210))
        typed(d, (110, 100), a, 64, seed=k)
        typed(d, (110, 210), b, 56, seed=k + 3)
        stamp(img, (720, 590), st, 96 if len(st) < 12 else 70, -7 + 4 * k, seed=k)
        img.save(os.path.join(OUT, name + '.png'))


def tex_notes():
    for k, txt in enumerate(('UNSOLVED', 'WHO?', 'LEADS?')):
        w, h = 700, 520
        img = paper(w, h, 170 + k, tone=(232, 224, 150), age=0.3)
        hand_text(img, (70, 260), txt, 150, 80 + k, ink=(40, 40, 44))
        img.save(os.path.join(OUT, f'note_{k}.png'))


def tex_report():
    w, h = 1300, 1700
    img = paper(w, h, 180, tone=(240, 238, 230), age=0.3)
    d = ImageDraw.Draw(img)
    typed(d, (90, 80), 'HOMICIDE DETAIL - INVESTIGATION REPORT', 46, seed=1)
    lines = ['RE:  LETTERS RECEIVED BY THREE NEWSPAPERS', 'ENCL: CIPHER IN THREE PARTS (408 SYMBOLS)',
             'WRITER CLAIMS RESPONSIBILITY FOR TWO', 'ATTACKS (BENICIA, VALLEJO).', '',
             'ACTION: COPIES FORWARDED FOR ANALYSIS.', 'HANDWRITING SAMPLES REQUESTED.', 'LATENT PRINTS: PENDING.']
    for k, ln in enumerate(lines):
        typed(d, (90, 230 + k * 78), ln, 42, seed=10 + k)
    img.save(os.path.join(OUT, 'report.png'))


def tex_newspaper2():
    """The front page in the street vending box (before the letters): a generic local headline."""
    w, h = 1400, 1900
    img = paper(w, h, 75, tone=(214, 206, 184), age=0.5)
    d = ImageDraw.Draw(img)
    d.text((w / 2, 110), 'THE EVENING EDITION', font=F(HEAD, 96), fill=(20, 20, 22), anchor='mm')
    d.line([(60, 190), (w - 60, 190)], fill=(30, 30, 30), width=4)
    d.text((w - 70, 205), 'FINAL  10 CENTS', font=F(MONO, 30), fill=(40, 40, 40), anchor='ra')
    d.line([(60, 250), (w - 60, 250)], fill=(30, 30, 30), width=2)
    d.text((w / 2, 380), 'POLICE SEEK', font=F(BOLD, 170), fill=(18, 18, 20), anchor='mm')
    d.text((w / 2, 560), 'CLUES', font=F(BOLD, 170), fill=(18, 18, 20), anchor='mm')
    rng = np.random.default_rng(76)
    d.rectangle([80, 700, 700, 1150], fill=(70, 68, 66))
    for col in range(4):
        x0 = 80 + col * 315
        for k in range(36):
            y = 1200 + k * 19 if col < 2 else 700 + k * 19
            if col >= 2 or y < h - 60:
                ln = rng.uniform(0.7, 1.0) * 290 if k % 11 != 10 else rng.uniform(0.2, 0.5) * 290
                d.line([(x0 if col < 2 else 760 + (col - 2) * 300, y), ((x0 if col < 2 else 760 + (col - 2) * 300) + ln * (0.85 if col >= 2 else 1), y)], fill=(95, 92, 88), width=7)
    img.save(os.path.join(OUT, 'newspaper2.png'))


def tex_clock():
    w = 600
    img = Image.new('RGB', (w, w), (226, 220, 204))
    d = ImageDraw.Draw(img)
    c = w / 2
    for k in range(60):
        a = k / 60 * 2 * math.pi
        r0 = c * (0.80 if k % 5 == 0 else 0.86)
        d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + c * 0.92 * math.sin(a), c - c * 0.92 * math.cos(a))],
               fill=(30, 30, 30), width=9 if k % 5 == 0 else 3)
    for k in range(1, 13):
        a = k / 12 * 2 * math.pi
        d.text((c + c * 0.66 * math.sin(a), c - c * 0.66 * math.cos(a)), str(k), font=F(HEAD, 54), fill=(30, 30, 30), anchor='mm')
    img.save(os.path.join(OUT, 'clock.png'))


def tex_symbol_card():
    w, h = 1200, 1200
    img = paper(w, h, 190, tone=(230, 222, 200), age=0.8)
    zodiac_symbol(img, w / 2, h / 2, 330, 34, 9)
    img.save(os.path.join(OUT, 'symbol_card.png'))


def main():
    os.makedirs(OUT, exist_ok=True)
    for fn in (tex_letter, tex_envelope, tex_cipher_parts, tex_strip408, tex_atlas, tex_newspaper, tex_cards, tex_decoded,
               tex_map, tex_photos, tex_fingerprint, tex_handwriting, tex_labels, tex_notes, tex_report, tex_symbol_card, tex_newspaper2, tex_clock):
        fn()
    print('textures written to', OUT, len(os.listdir(OUT)))


if __name__ == '__main__':
    main()
