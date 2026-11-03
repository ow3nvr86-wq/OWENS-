"""Procedural prop textures for "What If Money Grew on Trees?" (Pillow + numpy, code only).

Draws every printed thing the 3D scene uses and writes PNGs to build/tex/:
  - the banknote (an invented design: it is NOT a copy of any real currency - no real portrait, seal, motto
    or serial format), the paper band of a cash bundle and a money sack print
  - price tags (shelf tags before/after, the sandwich card and its crossed-out version, the bicycle tag)
  - store signs and banners, aisle signs, product labels with invented brand names
  - hand-made and painted signs for the suburb, farm and forest
  - the static background of the city's giant screen (the moving graph lines are 3D geometry)
animation.py runs this automatically when build/tex/ is missing.

    $SHORTS_PY tools/textures.py

All prices are fictional: they belong to the hypothetical scenario and are labelled as such in the edit.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'tex')
FD = os.path.join(ROOT, 'assets', 'fonts')
BOLD = os.path.join(FD, 'Anton-Regular.ttf')
SERIF = os.path.join(FD, 'OldStandard-Bold.ttf')
HAND = os.path.join(FD, 'CoveredByYourGrace.ttf')


def F(path, size):
    return ImageFont.truetype(path, size)


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, name + '.png'))


def text_c(d, cx, cy, txt, font, fill, stroke=0, stroke_fill=None, anchor='mm'):
    d.text((cx, cy), txt, font=font, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def fit_font(path, txt, max_w, size):
    while size > 8:
        f = F(path, size)
        if f.getlength(txt) <= max_w:
            return f
        size -= 2
    return F(path, size)


def grain(img, amt=6, seed=0):
    a = np.asarray(img).astype(float)
    a[..., :3] += np.random.default_rng(seed).normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), img.mode)


# ----------------------------------------------------------------------------------------------
# money
# ----------------------------------------------------------------------------------------------
def banknote():
    """An invented green banknote, 2.35:1 like a dollar bill. Guilloche borders, big 100s, a tree in the oval."""
    W, H = 1024, 436
    y, x = np.mgrid[0:H, 0:W].astype(float)
    base = np.zeros((H, W, 3))
    base[:] = (196, 214, 188)
    # fine guilloche wave pattern over the paper
    g = 0.5 + 0.5 * np.sin(x * 0.21 + 9 * np.sin(y * 0.031)) * np.sin(y * 0.19 + 7 * np.sin(x * 0.017))
    base -= g[..., None] * np.array([30, 18, 30])
    # darker green border band with its own pattern
    e = np.minimum.reduce([x, W - 1 - x, y, H - 1 - y])
    band = (e < 46).astype(float)
    pat = 0.5 + 0.5 * np.sin((x + y) * 0.35) * np.sin((x - y) * 0.35)
    base = base * (1 - band[..., None]) + band[..., None] * (np.array([58, 98, 70]) + pat[..., None] * np.array([40, 46, 36]))
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    ink = (34, 70, 48)
    d.rectangle([52, 52, W - 53, H - 53], outline=ink, width=4)
    d.rectangle([62, 62, W - 63, H - 63], outline=(70, 110, 80), width=2)
    # central oval with a tree
    cx, cy = W // 2, H // 2 + 6
    for r, col, wd in ((112, ink, 6), (102, (80, 120, 88), 2)):
        d.ellipse([cx - r * 0.9, cy - r, cx + r * 0.9, cy + r], outline=col, width=wd)
    d.ellipse([cx - 88, cy - 98, cx + 88, cy + 98], fill=(176, 198, 168))
    d.rectangle([cx - 8, cy + 6, cx + 8, cy + 80], fill=ink)               # trunk
    d.polygon([(cx - 8, cy + 46), (cx - 38, cy + 14), (cx - 32, cy + 10), (cx - 4, cy + 38)], fill=ink)
    d.polygon([(cx + 8, cy + 40), (cx + 40, cy + 8), (cx + 34, cy + 4), (cx + 4, cy + 32)], fill=ink)
    rng = np.random.default_rng(7)
    for _ in range(46):                                                    # leaves and tiny bills
        a, rr = rng.uniform(0, 2 * math.pi), rng.uniform(0, 62)
        px, py = cx + math.cos(a) * rr * 0.95, cy - 30 + math.sin(a) * rr * 0.6
        if rng.random() < 0.25:
            d.rectangle([px - 9, py - 4, px + 9, py + 4], fill=(62, 104, 72), outline=ink)
        else:
            d.ellipse([px - 13, py - 9, px + 13, py + 9], fill=(48, 92, 60), outline=ink)
    d.line([(cx - 60, cy + 82), (cx + 60, cy + 82)], fill=ink, width=4)
    # corner numerals and text
    f100 = F(BOLD, 96)
    for (px, py) in ((140, 112), (W - 140, 112), (140, H - 112), (W - 140, H - 112)):
        text_c(d, px, py, '100', f100, (32, 66, 44), stroke=3, stroke_fill=(200, 216, 192))
    text_c(d, cx, 88, 'LEGAL TENDER', F(SERIF, 28), ink)
    text_c(d, cx, H - 82, 'ONE HUNDRED DOLLARS', F(SERIF, 30), ink)
    f = F(SERIF, 20)
    text_c(d, 300, 210, 'THIS NOTE', f, ink)
    text_c(d, 300, 236, 'GREW ON A TREE', f, ink)
    text_c(d, 722, 210, 'PICKED FRESH', f, ink)
    text_c(d, 722, 236, 'DO NOT WATER', f, ink)
    # a round "seal" and serial numbers (invented formats)
    d.ellipse([268, 268, 340, 340], outline=(30, 90, 60), width=5)
    text_c(d, 304, 304, '$', F(BOLD, 48), (30, 90, 60))
    text_c(d, 700, 300, 'TR 0000001 EE', F(SERIF, 22), (40, 110, 70))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    save(grain(img, 5, 1), 'bill')


def bundle_band():
    img = Image.new('RGB', (256, 128), (196, 160, 92))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 10, 255, 117], fill=(216, 178, 104))
    text_c(d, 128, 64, '$10,000', F(BOLD, 54), (120, 72, 30))
    save(grain(img, 4, 2), 'band')


def sack():
    W = 512
    rng = np.random.default_rng(3)
    y, x = np.mgrid[0:W, 0:W]
    weave = 0.5 + 0.25 * np.sin(x * 0.9) + 0.25 * np.sin(y * 0.9)
    base = np.array([168, 140, 96], float) * (0.82 + 0.18 * weave[..., None]) + rng.normal(0, 6, (W, W, 1))
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.ellipse([136, 136, 376, 376], outline=(52, 82, 52), width=12)
    text_c(d, 256, 262, '$', F(BOLD, 190), (52, 82, 52))
    save(img, 'sack')


# ----------------------------------------------------------------------------------------------
# price tags and store graphics
# ----------------------------------------------------------------------------------------------
def shelf_tag(name, item, price, hot=False, old=None):
    W, H = 512, 256
    img = Image.new('RGB', (W, H), (255, 214, 64) if hot else (250, 248, 240))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, 46], fill=(200, 30, 36) if hot else (32, 92, 60))
    text_c(d, W // 2, 24, item, F(BOLD, 34), (255, 255, 255))
    f = fit_font(BOLD, price, W - 40, 150)
    text_c(d, W // 2, 152, price, f, (20, 20, 20))
    if old:
        text_c(d, 70, 228, 'WAS ' + old, F(BOLD, 24), (110, 110, 110), anchor='lm')
    d.rectangle([0, 0, W - 1, H - 1], outline=(60, 60, 60), width=4)
    save(grain(img, 3, len(name)), name)


def sandwich_card(name, crossed=False):
    W, H = 768, 512
    img = Image.new('RGB', (W, H), (255, 252, 240))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, 92], fill=(32, 92, 60))
    text_c(d, W // 2, 48, 'TODAY\'S SPECIAL: SANDWICH', F(BOLD, 52), (255, 255, 255))
    if not crossed:
        f = fit_font(BOLD, '$1,999,999.99', W - 60, 170)
        text_c(d, W // 2, 270, '$1,999,999.99', f, (200, 30, 36))
        text_c(d, W // 2, 430, 'TAX NOT INCLUDED', F(BOLD, 40), (70, 70, 70))
    else:
        f = fit_font(BOLD, '$1,999,999.99', W - 260, 100)
        text_c(d, W // 2, 170, '$1,999,999.99', f, (120, 120, 120))
        bb = d.textbbox((W // 2, 170), '$1,999,999.99', font=f, anchor='mm')
        d.line([(bb[0] - 10, bb[3] - 6), (bb[2] + 10, bb[1] + 6)], fill=(30, 30, 30), width=12)
        d.line([(bb[0] - 10, bb[1] + 10), (bb[2] + 10, bb[3] - 10)], fill=(30, 30, 30), width=12)
        text_c(d, 120, 330, 'NOW', F(HAND, 76), (30, 30, 30))
        f2 = fit_font(BOLD, '$9,999,999.99', W - 230, 160)
        text_c(d, W // 2 + 60, 340, '$9,999,999.99', f2, (200, 30, 36))
        text_c(d, W // 2, 455, 'TAX NOT INCLUDED', F(BOLD, 36), (70, 70, 70))
    d.rectangle([0, 0, W - 1, H - 1], outline=(40, 40, 40), width=8)
    save(grain(img, 3, 11), name)


def banner(name, crossed=False):
    W, H = 2048, 320
    img = Image.new('RGB', (W, H), (214, 34, 40))
    d = ImageDraw.Draw(img)
    d.rectangle([14, 14, W - 15, H - 15], outline=(255, 220, 80), width=10)
    f = F(BOLD, 200 if not crossed else 160)
    cy = H // 2 if not crossed else 205
    text_c(d, W // 2, cy, 'LOW PRICES EVERY DAY!', f, (255, 255, 255))
    if crossed:
        bb = d.textbbox((W // 2, cy), 'LOW PRICES EVERY DAY!', font=f, anchor='mm')
        lw = f.getlength('LOW')
        x0 = bb[0]
        d.line([(x0 - 14, cy + 40), (x0 + lw + 14, cy - 44)], fill=(20, 20, 20), width=22)
        text_c(d, x0 + lw / 2, 70, 'HIGH', F(HAND, 120), (20, 20, 20))
    save(img, name)


def aisle_sign(name, txt, col):
    W, H = 768, 256
    img = Image.new('RGB', (W, H), col)
    d = ImageDraw.Draw(img)
    text_c(d, W // 2, H // 2, txt, fit_font(BOLD, txt, W - 60, 150), (255, 255, 255))
    save(img, name)


def store_front():
    W, H = 2048, 384
    img = Image.new('RGB', (W, H), (32, 92, 60))
    d = ImageDraw.Draw(img)
    text_c(d, W // 2, H // 2, 'CORNER GROCER', F(BOLD, 230), (255, 238, 196))
    save(img, 'storename')


def box_label(name, title, sub, c1, c2, seed):
    """Cereal-box style front: two-colour panel, a sun/ring motif, invented brand name."""
    W, H = 384, 512
    img = Image.new('RGB', (W, H), c1)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    d.ellipse([W * 0.15, H * 0.36, W * 0.85, H * 0.86], fill=c2)
    for _ in range(18):
        x, y, r = rng.uniform(70, 314), rng.uniform(220, 420), rng.uniform(10, 22)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(236, 196, 92), outline=(150, 100, 40), width=3)
    text_c(d, W // 2, 90, title, fit_font(BOLD, title, W - 40, 110), (255, 255, 255), stroke=5, stroke_fill=(40, 30, 30))
    text_c(d, W // 2, 175, sub, F(BOLD, 34), (255, 240, 200))
    save(img, name)


def can_label(name, title, c1, c2):
    W, H = 512, 256
    img = Image.new('RGB', (W, H), c1)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 70, W, 186], fill=c2)
    text_c(d, W // 2, 128, title, fit_font(BOLD, title, W - 60, 92), (255, 255, 255))
    save(img, name)


def milk_label():
    W, H = 512, 512
    img = Image.new('RGB', (W, H), (250, 250, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 140, W, 360], fill=(40, 90, 190))
    text_c(d, W // 2, 250, 'MILK', F(BOLD, 150), (255, 255, 255))
    text_c(d, W // 2, 420, 'WHOLE  1 GAL', F(BOLD, 44), (40, 90, 190))
    save(img, 'milk')


def egg_label():
    W, H = 512, 256
    img = Image.new('RGB', (W, H), (236, 226, 204))
    d = ImageDraw.Draw(img)
    text_c(d, W // 2, 90, 'FARM EGGS', F(BOLD, 90), (150, 70, 40))
    text_c(d, W // 2, 190, '12 LARGE', F(BOLD, 52), (90, 60, 40))
    save(img, 'eggs')


def bread_bag():
    W, H = 512, 256
    img = Image.new('RGBA', (W, H), (255, 255, 255, 40))
    d = ImageDraw.Draw(img)
    for k in range(6):
        d.ellipse([20 + k * 80, 18, 70 + k * 80, 58], fill=(230, 40, 50, 230))
        d.ellipse([20 + k * 80, 198, 70 + k * 80, 238], fill=(240, 200, 40, 230))
    text_c(d, W // 2, 128, 'SOFT WHITE', F(BOLD, 80), (30, 60, 150, 255))
    save(img, 'breadbag')


def limit_sign():
    W, H = 768, 384
    img = Image.new('RGB', (W, H), (255, 214, 64))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, W - 11, H - 11], outline=(200, 30, 36), width=14)
    text_c(d, W // 2, 120, 'LIMIT 1', F(BOLD, 150), (200, 30, 36))
    text_c(d, W // 2, 270, 'PER CUSTOMER', F(BOLD, 96), (30, 30, 30))
    save(img, 'limit')


def counter_display():
    for k, txt in enumerate(('$1,980,400', '$2,310,900', '$2,641,300', 'ERROR: TOO MUCH')):
        W, H = 512, 128
        img = Image.new('RGB', (W, H), (8, 16, 10))
        d = ImageDraw.Draw(img)
        text_c(d, W // 2, H // 2, txt, fit_font(BOLD, txt, W - 40, 88), (120, 255, 140))
        save(img, f'count{k}')


# ----------------------------------------------------------------------------------------------
# outdoor signs
# ----------------------------------------------------------------------------------------------
def wood(W, H, seed, tone=(150, 104, 62)):
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:H, 0:W]
    g = np.sin(y * 0.09 + 3 * np.sin(x * 0.006 + rng.uniform(0, 6))) * 0.5 + 0.5
    base = np.array(tone, float) * (0.78 + 0.22 * g[..., None]) + rng.normal(0, 5, (H, W, 1))
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


def signs():
    # MY FIRST MONEY TREE: marker on cardboard
    img = Image.new('RGB', (512, 320), (196, 160, 112))
    d = ImageDraw.Draw(img)
    text_c(d, 256, 110, 'MY FIRST', F(HAND, 110), (30, 30, 40))
    text_c(d, 256, 230, 'MONEY TREE', F(HAND, 100), (30, 30, 40))
    save(grain(img, 6, 4), 'sign_first')
    # MONEY FARM - EST. TODAY: painted wood
    img = wood(1024, 384, 5)
    d = ImageDraw.Draw(img)
    text_c(d, 512, 150, 'MONEY FARM', F(BOLD, 190), (245, 240, 220), stroke=6, stroke_fill=(60, 40, 20))
    text_c(d, 512, 315, 'EST. TODAY', F(SERIF, 80), (245, 240, 220))
    save(img, 'sign_farm')
    # SOLD real-estate rider
    img = Image.new('RGB', (768, 512), (250, 250, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 767, 511], outline=(200, 30, 36), width=30)
    text_c(d, 384, 220, 'SOLD', F(BOLD, 300), (200, 30, 36))
    text_c(d, 384, 430, 'ENTIRE FOREST', F(BOLD, 70), (30, 30, 30))
    save(img, 'sign_sold')
    img = wood(768, 256, 6, (120, 84, 50))
    d = ImageDraw.Draw(img)
    text_c(d, 384, 90, 'PRIVATE FOREST', F(BOLD, 96), (245, 230, 200))
    text_c(d, 384, 196, 'NO PICKING', F(BOLD, 80), (245, 230, 200))
    save(img, 'sign_private')
    # city signs
    for name, txt, bg, fg in (('sign_bank', 'BANK - VAULT FULL', (30, 50, 90), (240, 240, 240)),
                              ('sign_trees', 'WE BUY TREES', (200, 30, 36), (255, 255, 255)),
                              ('sign_cash', 'CASH FOR CASH', (240, 190, 40), (30, 30, 30)),
                              ('sign_seeds', 'SEEDS $90,000', (32, 92, 60), (255, 255, 255)),
                              ('sign_rent', 'RENT: $4,000,000/MO', (60, 60, 64), (255, 220, 120))):
        img = Image.new('RGB', (1024, 256), bg)
        d = ImageDraw.Draw(img)
        text_c(d, 512, 128, txt, fit_font(BOLD, txt, 960, 160), fg)
        save(img, name)


def screen_bg():
    """The city's giant screen: frame, grid, axes, legend. The two lines are animated geometry in 3D."""
    W, H = 1024, 1280
    img = Image.new('RGB', (W, H), (6, 12, 20))
    d = ImageDraw.Draw(img)
    x0, x1, y0, y1 = 120, 960, 300, 1130          # plot area (pixels); animation.py uses the same numbers
    for k in range(9):
        y = y1 - (y1 - y0) * k / 8
        d.line([(x0, y), (x1, y)], fill=(26, 44, 60), width=2)
    for k in range(7):
        x = x0 + (x1 - x0) * k / 6
        d.line([(x, y0), (x, y1)], fill=(26, 44, 60), width=2)
    d.line([(x0, y0 - 20), (x0, y1)], fill=(200, 210, 220), width=6)
    d.line([(x0, y1), (x1 + 20, y1)], fill=(200, 210, 220), width=6)
    text_c(d, W // 2, 90, 'MONEY vs. STUFF', F(BOLD, 110), (255, 255, 255))
    text_c(d, 300, 200, 'MONEY', F(BOLD, 70), (90, 255, 120))
    text_c(d, 720, 200, 'GOODS', F(BOLD, 70), (255, 170, 60))
    d.rectangle([150, 188, 180, 212], fill=(90, 255, 120))
    d.rectangle([570, 188, 600, 212], fill=(255, 170, 60))
    text_c(d, W // 2, 1190, 'TIME', F(BOLD, 56), (170, 180, 190))
    text_c(d, W // 2, 1250, 'ILLUSTRATIVE - NOT REAL DATA', F(BOLD, 38), (150, 160, 170))
    save(img, 'screen')


def plaid():
    W = 256
    y, x = np.mgrid[0:W, 0:W]
    a = ((x // 32) % 2).astype(float)
    b = ((y // 32) % 2).astype(float)
    c = np.ones((W, W, 3)) * np.array([170, 30, 34], float)
    c *= (1 - 0.35 * a[..., None]) * (1 - 0.35 * b[..., None])
    thin = ((x % 64) < 4) | ((y % 64) < 4)
    c[thin] = (230, 210, 190)
    save(Image.fromarray(c.astype(np.uint8)), 'plaid')


def main():
    banknote()
    bundle_band()
    sack()
    for name, item, price, hot, old in (
            ('tag_bread0', 'SOFT WHITE BREAD', '$4.99', False, None), ('tag_bread1', 'SOFT WHITE BREAD', '$500.00', True, '$4.99'),
            ('tag_buns0', 'BURGER BUNS', '$3.49', False, None), ('tag_buns1', 'BURGER BUNS', '$349.00', True, '$3.49'),
            ('tag_rye0', 'RYE LOAF', '$5.29', False, None), ('tag_rye1', 'RYE LOAF', '$529.00', True, '$5.29'),
            ('tag_bagel0', 'BAGELS 6PK', '$3.99', False, None), ('tag_bagel1', 'BAGELS 6PK', '$399.00', True, '$3.99'),
            ('tag_milk0', 'WHOLE MILK 1 GAL', '$2.50', False, None), ('tag_milk1', 'WHOLE MILK 1 GAL', '$250.00', True, '$2.50'),
            ('tag_bike0', 'CITY BICYCLE', '$199.00', False, None), ('tag_bike1', 'CITY BICYCLE', '$20,000', True, '$199'),
            ('tag_eggs', 'FARM EGGS 12', '$900.00', True, None), ('tag_cereal', 'CEREAL', '$480.00', True, None),
            ('tag_generic', 'SPECIAL', '$1,250.00', True, None)):
        shelf_tag(name, item, price, hot, old)
    sandwich_card('card0')
    sandwich_card('card1', crossed=True)
    banner('banner0')
    banner('banner1', crossed=True)
    for name, txt, col in (('aisle_bakery', 'BAKERY', (200, 120, 40)), ('aisle_dairy', 'DAIRY', (40, 90, 190)),
                           ('aisle_cereal', 'CEREAL', (200, 40, 60)), ('aisle_bikes', 'BIKES & TOYS', (110, 60, 160)),
                           ('aisle_produce', 'PRODUCE', (40, 140, 70)), ('aisle_checkout', 'CHECKOUT', (32, 92, 60))):
        aisle_sign(name, txt, col)
    store_front()
    for k, (t, s, c1, c2) in enumerate((('SUNNY O\'S', 'TOASTED OATS', (230, 160, 30), (250, 210, 80)),
                                        ('BRAN BITS', 'HIGH FIBRE', (120, 70, 40), (190, 140, 80)),
                                        ('CHOCO CRUNCH', 'NOW CRUNCHIER', (90, 50, 30), (170, 100, 60)),
                                        ('BERRY BLAST', 'FRUITY!', (170, 40, 90), (230, 110, 160)),
                                        ('CORN DAZE', 'FLAKES', (40, 110, 180), (120, 180, 230)))):
        box_label(f'box{k}', t, s, c1, c2, k)
    for k, (t, c1, c2) in enumerate((('BEANS', (200, 70, 40), (120, 40, 30)), ('SOUP', (220, 200, 180), (190, 30, 40)),
                                     ('TOMATOES', (40, 120, 60), (210, 50, 40)), ('PEACHES', (240, 170, 60), (200, 100, 40)))):
        can_label(f'can{k}', t, c1, c2)
    milk_label()
    egg_label()
    bread_bag()
    limit_sign()
    counter_display()
    signs()
    screen_bg()
    plaid()
    print('textures written to', OUT)


if __name__ == '__main__':
    main()
