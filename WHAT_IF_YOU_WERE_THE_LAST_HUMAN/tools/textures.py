"""Procedural prop textures for "What If You Were the Last Human on Earth?" (Pillow + numpy, code only).

Writes PNGs to build/tex/: shop, mall, cinema and station signs with invented names, the two phone screens (morning:
"No notifications"; the next dawn: "No service", "No new messages"), the old photograph (invented, stylised figures -
no real people), a departure board, the film in the empty cinema and the TV in the empty house (abstract landscapes),
supermarket shelf fronts, a newspaper page and three abstract framed prints. animation.py runs this automatically
when build/tex/ is missing.

    $SHORTS_PY tools/textures.py
"""
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


def fit(path, txt, max_w, size):
    while size > 8:
        f = F(path, size)
        if f.getlength(txt) <= max_w:
            return f
        size -= 2
    return F(path, size)


def sign(name, text, bg, fg, font=SERIF, sub=None, w=1600, h=200, border=None):
    im = Image.new('RGB', (w, h), bg)
    d = ImageDraw.Draw(im)
    if border:
        d.rectangle([8, 8, w - 9, h - 9], outline=border, width=6)
    f = fit(font, text, w * 0.86, int(h * 0.62))
    d.text((w / 2, h * (0.44 if sub else 0.52)), text, font=f, fill=fg, anchor='mm')
    if sub:
        d.text((w / 2, h * 0.82), sub, font=fit(BOLD, sub, w * 0.6, int(h * 0.16)), fill=fg, anchor='mm')
    save(im, name)


def sleeve():
    w, h = 1024, 256
    im = Image.new('RGB', (w, h), (120, 82, 50))
    d = ImageDraw.Draw(im)
    for x in range(0, w, 6):
        d.line([(x, 0), (x, h)], fill=(112, 76, 46), width=2)
    for cx in (w * 0.25, w * 0.75):
        d.ellipse([cx - 80, h / 2 - 80, cx + 80, h / 2 + 80], fill=(236, 226, 205))
        d.text((cx, h / 2 - 8), 'LUNA', font=F(SERIF, 54), fill=(60, 36, 20), anchor='mm')
        d.text((cx, h / 2 + 40), 'COFFEE', font=F(BOLD, 26), fill=(60, 36, 20), anchor='mm')
    save(im, 'sleeve')


def newspaper():
    w, h = 768, 1024
    rng = np.random.default_rng(4)
    im = Image.new('RGB', (w, h), (232, 228, 214))
    d = ImageDraw.Draw(im)
    d.text((w / 2, 70), 'THE DAILY CURRENT', font=F(SERIF, 66), fill=(25, 25, 25), anchor='mm')
    d.line([(30, 120), (w - 30, 120)], fill=(30, 30, 30), width=4)
    d.text((w / 2, 190), 'CITY PARK REOPENS', font=F(BOLD, 72), fill=(20, 20, 20), anchor='mm')
    d.rectangle([40, 250, 440, 560], fill=(150, 150, 145))
    for col in range(3):
        x0 = 40 + col * 236
        y0 = 590 if col < 2 else 250
        for y in range(y0, h - 40, 16):
            ln = rng.uniform(0.6, 1.0) * 210
            d.line([(x0, y), (x0 + ln, y)], fill=(90, 90, 88), width=5)
    save(im.filter(ImageFilter.GaussianBlur(0.6)), 'newspaper')


def window_view():
    w, h = 1800, 1000
    rng = np.random.default_rng(9)
    y = np.linspace(0, 1, h)[:, None]
    sky = (np.array([110, 160, 220]) * (1 - y[..., None]) + np.array([225, 230, 235]) * y[..., None])
    arr = np.repeat(sky, w, axis=1)
    im = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(im)
    x = 0
    while x < w:
        bw = int(rng.uniform(90, 220))
        bh = int(rng.uniform(250, 800))
        c = int(rng.uniform(120, 175))
        col = (c, c - 4, c - 12)
        d.rectangle([x, h - bh, x + bw, h], fill=col)
        for wy in range(h - bh + 20, h - 10, 34):
            for wx in range(x + 12, x + bw - 18, 26):
                g = int(rng.uniform(60, 110))
                d.rectangle([wx, wy, wx + 14, wy + 20], fill=(g, g + 10, g + 25))
        x += bw + int(rng.uniform(0, 30))
    save(im.filter(ImageFilter.GaussianBlur(3.0)), 'window_view')


def art():
    rng = np.random.default_rng(12)
    pal = [[(200, 80, 50), (240, 200, 120), (40, 70, 110)], [(30, 90, 120), (230, 230, 220), (220, 140, 40)],
           [(90, 120, 70), (240, 230, 200), (150, 60, 50)]]
    for k in range(3):
        im = Image.new('RGB', (512, 512), pal[k][1])
        d = ImageDraw.Draw(im)
        for j in range(5):
            x0, y0 = rng.uniform(0, 380, 2)
            s = rng.uniform(80, 240)
            fill = pal[k][j % 3]
            if j % 2:
                d.ellipse([x0, y0, x0 + s, y0 + s], fill=fill)
            else:
                d.rectangle([x0, y0, x0 + s, y0 + s * 0.6], fill=fill)
        d.rectangle([0, 0, 511, 511], outline=(240, 240, 235), width=28)
        save(im, f'art{k}')


def phone(name, clock, day, centre, sub, bars, battery, warn=False):
    w, h = 600, 1260
    y = np.linspace(0, 1, h)[:, None, None]
    top, bot = (np.array([18, 30, 58]), np.array([70, 40, 60])) if not warn else (np.array([12, 14, 22]), np.array([40, 26, 30]))
    arr = np.repeat(top * (1 - y) + bot * y, w, axis=1)
    im = Image.fromarray(arr.astype(np.uint8))
    # soft wallpaper shapes
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.ellipse([-200, 700, 500, 1400], fill=(120, 70, 140, 70))
    dl.ellipse([250, 500, 900, 1150], fill=(60, 110, 170, 60))
    im = Image.alpha_composite(im.convert('RGBA'), lay.filter(ImageFilter.GaussianBlur(60)))
    d = ImageDraw.Draw(im)
    wh = (245, 245, 250)
    # status bar
    for k in range(4):
        hh = 10 + k * 7
        d.rectangle([40 + k * 13, 52 - hh, 49 + k * 13, 52], fill=wh if k < bars else (110, 110, 120))
    d.text((104, 46), 'No service' if bars == 0 else 'NORTHCELL', font=F(BOLD, 26), fill=wh, anchor='lm')
    d.rounded_rectangle([470, 32, 540, 60], radius=7, outline=wh, width=3)
    d.rectangle([475, 37, 475 + 60 * battery / 100, 55], fill=(230, 60, 50) if battery < 20 else wh)
    d.text((462, 46), f'{battery}%', font=F(BOLD, 24), fill=wh, anchor='rm')
    d.text((w / 2, 190), day, font=F(BOLD, 40), fill=wh, anchor='mm')
    d.text((w / 2, 320), clock, font=F(BOLD, 190), fill=wh, anchor='mm')
    # the notification area
    box = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([60, 560, w - 60, 700], radius=28, fill=(255, 255, 255, 46))
    im = Image.alpha_composite(im, box)
    d = ImageDraw.Draw(im)
    d.text((w / 2, 610), centre, font=F(BOLD, 44), fill=wh, anchor='mm')
    d.text((w / 2, 662), sub, font=F(BOLD, 26), fill=(200, 200, 210), anchor='mm')
    d.rounded_rectangle([w / 2 - 110, h - 40, w / 2 + 110, h - 30], radius=5, fill=wh)
    save(im.convert('RGB'), name)


def photo():
    """An old snapshot of four friends at the seaside: invented, stylised figures (no real people)."""
    w, h = 900, 680
    y = np.linspace(0, 1, h)[:, None, None]
    sky = np.array([250, 196, 130]) * (1 - y) + np.array([236, 120, 90]) * y
    arr = np.repeat(sky, w, axis=1)
    arr[int(h * 0.58):] = np.array([70, 110, 140])
    arr[int(h * 0.72):] = np.array([214, 186, 140])
    im = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.ellipse([w * 0.62, h * 0.30, w * 0.80, h * 0.54], fill=(255, 226, 170))
    cols = [(200, 70, 60), (60, 90, 150), (240, 200, 90), (70, 140, 100)]
    skins = [(225, 170, 130), (150, 100, 70), (235, 190, 150), (110, 70, 50)]
    for k, cx in enumerate((0.22, 0.40, 0.58, 0.76)):
        x = w * cx
        hy = h * (0.42 + 0.03 * (k % 2))
        d.rounded_rectangle([x - 62, hy + 50, x + 62, h * 0.98], radius=40, fill=cols[k])
        d.ellipse([x - 42, hy - 40, x + 42, hy + 48], fill=skins[k])
        d.chord([x - 44, hy - 46, x + 44, hy + 30], 180, 360, fill=(40, 26, 18) if k != 2 else (150, 100, 50))
        d.arc([x - 18, hy + 4, x + 18, hy + 26], 20, 160, fill=(60, 20, 20), width=4)
        for ex in (-14, 14):
            d.ellipse([x + ex - 4, hy - 4, x + ex + 4, hy + 4], fill=(30, 20, 20))
        if k < 3:   # arms around each other
            d.line([(x + 40, hy + 80), (x + w * 0.18 - 40, hy + 80)], fill=skins[k], width=18)
    im = im.filter(ImageFilter.GaussianBlur(1.6))
    arr = np.asarray(im).astype(float)
    arr = arr * 0.82 + np.array([40, 30, 10]) * 0.18 + 12       # faded print
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    arr *= (1 - 0.35 * np.clip(r - 0.6, 0, 1))[..., None]
    pic = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    out = Image.new('RGB', (w + 80, h + 200), (236, 230, 214))
    out.paste(pic, (40, 40))
    ImageDraw.Draw(out).text(((w + 80) / 2, h + 120), 'the four of us - summer', font=F(HAND, 64), fill=(50, 50, 80), anchor='mm')
    save(out, 'photo')


def board():
    w, h = 1400, 520
    im = Image.new('RGB', (w, h), (8, 8, 10))
    d = ImageDraw.Draw(im)
    amber = (255, 170, 30)
    d.text((40, 50), 'TIME   DESTINATION', font=F(BOLD, 40), fill=(150, 150, 150), anchor='lm')
    d.text((w - 40, 50), 'PLATFORM   STATUS', font=F(BOLD, 40), fill=(150, 150, 150), anchor='rm')
    rows = [('08:12', 'HARBOUR', '2', 'DELAYED'), ('08:20', 'NORTH PARK', '1', 'DELAYED'), ('08:31', 'RIVERSIDE', '3', 'DELAYED'),
            ('08:44', 'HILLCREST', '2', 'DELAYED'), ('08:52', 'OLD TOWN', '1', 'DELAYED')]
    for k, (t, dst, pl, st) in enumerate(rows):
        y = 140 + k * 82
        d.text((40, y), t, font=F(BOLD, 58), fill=amber, anchor='lm')
        d.text((230, y), dst, font=F(BOLD, 58), fill=amber, anchor='lm')
        d.text((w - 330, y), pl, font=F(BOLD, 58), fill=amber, anchor='mm')
        d.text((w - 40, y), st, font=F(BOLD, 58), fill=(255, 80, 40), anchor='rm')
    save(im, 'board')


def landscape(name, seed, warm=True):
    w, h = 1600, 680
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, h)[:, None, None]
    c0, c1 = (np.array([60, 90, 160]), np.array([250, 170, 110])) if warm else (np.array([40, 120, 170]), np.array([200, 230, 240]))
    arr = np.repeat(c0 * (1 - y) + c1 * y, w, axis=1)
    im = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(im)
    for layer, (base, col) in enumerate(((0.55, (90, 80, 120)), (0.66, (60, 60, 90)), (0.78, (30, 40, 50)))):
        pts = [(0, h)]
        x = 0
        yy = h * base
        while x <= w:
            yy = np.clip(yy + rng.normal(0, 18 + 10 * layer), h * (base - 0.2), h * (base + 0.08))
            pts.append((x, yy))
            x += 40
        pts.append((w, h))
        d.polygon(pts, fill=col)
    if warm:
        d.ellipse([w * 0.6, h * 0.30, w * 0.68, h * 0.48], fill=(255, 230, 180))
    save(im.filter(ImageFilter.GaussianBlur(2.0)), name)


def shelf(name, seed, kind):
    """Shelf fronts: rows of invented packaging (boxes or bottles), unreadable labels."""
    w, h = 2048, 512
    rng = np.random.default_rng(seed)
    im = Image.new('RGB', (w, h), (30, 30, 32))
    d = ImageDraw.Draw(im)
    pal = [(200, 40, 40), (240, 190, 40), (40, 110, 190), (40, 150, 80), (230, 120, 30), (240, 240, 235), (120, 50, 140),
           (20, 20, 25), (190, 160, 110)]
    x = 0
    while x < w:
        c = pal[int(rng.integers(len(pal)))]
        n = int(rng.integers(3, 7))
        pw = int(rng.uniform(60, 120)) if kind == 'box' else int(rng.uniform(40, 70))
        ph = int(rng.uniform(300, 460)) if kind == 'box' else int(rng.uniform(260, 440))
        for k in range(n):
            if x > w:
                break
            if kind == 'box':
                d.rectangle([x + 2, h - ph, x + pw - 2, h], fill=c)
                d.rectangle([x + 8, h - ph + 40, x + pw - 8, h - ph + 110], fill=(250, 250, 245))
                d.rectangle([x + 14, h - ph + 60, x + pw - 14, h - ph + 70], fill=c)
            else:
                d.rounded_rectangle([x + 4, h - ph + 60, x + pw - 4, h], radius=12, fill=c)
                d.rectangle([x + pw / 2 - 8, h - ph, x + pw / 2 + 8, h - ph + 70], fill=c)
                d.rectangle([x + 4, h - ph * 0.55, x + pw - 4, h - ph * 0.3], fill=(245, 245, 240))
            x += pw
        x += int(rng.uniform(0, 12))
    d.rectangle([0, h - 30, w, h], fill=(225, 225, 228))          # shelf-edge price strip
    for k in range(0, w, 160):
        d.rectangle([k + 20, h - 26, k + 90, h - 6], fill=(250, 220, 40))
    save(im, name)


def main():
    sign('sign_cafe', 'LUNA CAFE', (28, 40, 34), (236, 214, 160), font=SERIF, sub='COFFEE  -  BAKES  -  SINCE 1987', border=(236, 214, 160))
    sign('sign_books', 'PAGE & SPINE BOOKS', (90, 20, 24), (240, 230, 210), font=SERIF)
    sign('sign_bakery', 'HARBOUR BAKERY', (232, 222, 200), (80, 40, 20), font=SERIF, border=(80, 40, 20))
    sign('sign_pharmacy', 'PHARMACY', (20, 110, 70), (255, 255, 255), font=BOLD)
    sign('sign_market', 'FRESH MARKET', (230, 120, 30), (255, 255, 255), font=BOLD)
    sign('sign_cinema', 'PALACE CINEMA', (110, 14, 20), (255, 214, 120), font=SERIF, border=(255, 214, 120))
    sign('sign_station', 'CENTRAL', (16, 40, 90), (255, 255, 255), font=BOLD, w=1200)
    sign('mall0', 'NORTHWIND', (20, 20, 22), (240, 240, 240), font=BOLD)
    sign('mall1', 'ATLAS SHOES', (240, 236, 228), (30, 30, 30), font=SERIF)
    sign('mall2', 'BLOOM & CO', (200, 120, 130), (255, 255, 255), font=SERIF)
    sign('mall3', 'VOLT ELECTRONICS', (20, 60, 120), (255, 255, 255), font=BOLD)
    sign('mall4', 'THE KITCHEN DRAWER', (60, 90, 70), (240, 230, 200), font=SERIF)
    phone('phone_lock', '07:12', 'Tuesday', 'No notifications', 'You are all caught up', 3, 82)
    phone('phone_end', '05:58', 'Wednesday', 'No new messages', 'No calls  -  No service', 0, 9, warn=True)
    photo()
    board()
    landscape('film', 3, warm=True)
    landscape('tv', 8, warm=False)
    shelf('shelf_box', 1, 'box')
    shelf('shelf_bottle', 2, 'bottle')
    newspaper()
    art()
    print('textures ->', OUT)


if __name__ == '__main__':
    main()
