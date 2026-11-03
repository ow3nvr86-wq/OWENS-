"""Procedural prop textures for "What If Gravity Turned Off for 10 Seconds?" (Pillow + numpy, code only).

Writes PNGs to build/tex/: shop signs with invented names, the coffee-cup sleeve, a newspaper page (invented
masthead, unreadable body text), the city view seen through the apartment window and three abstract framed prints.
animation.py runs this automatically when build/tex/ is missing.

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


def main():
    sign('sign_cafe', 'LUNA CAFE', (28, 40, 34), (236, 214, 160), font=SERIF, sub='COFFEE  -  BAKES  -  SINCE 1987', border=(236, 214, 160))
    sign('sign_books', 'PAGE & SPINE BOOKS', (90, 20, 24), (240, 230, 210), font=SERIF)
    sign('sign_bakery', 'HARBOUR BAKERY', (232, 222, 200), (80, 40, 20), font=SERIF, border=(80, 40, 20))
    sign('sign_pharmacy', 'PHARMACY', (20, 110, 70), (255, 255, 255), font=BOLD)
    sign('sign_market', 'FRESH MARKET', (230, 120, 30), (255, 255, 255), font=BOLD)
    sleeve()
    newspaper()
    window_view()
    art()
    print('textures ->', OUT)


if __name__ == '__main__':
    main()
