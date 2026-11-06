"""Procedural screen graphics and prop textures for "What If You Were the Only Man Alive? Part 2" (Pillow + numpy, code only).

Everything here is invented and drawn with code: the phone's breaking-news alert, an invented news channel's on-air
graphics (GLOBAL 24), the giant screens in the city square, a stylised globe of alerts, the "only man alive" card,
the lab's scan and DNA screens, office monitors, signs for the hospital and the train, a parliament crest, and the
final screen THE LAST MAN ALIVE. Placeholders for the rendered portrait and news-presenter feed are replaced by
animation.py with renders of its own 3D characters. animation.py runs this automatically when build/tex/ is missing.

    $SHORTS_PY tools/textures.py
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

AMBER = (255, 184, 36)
CYAN = (90, 220, 255)
RED = (235, 40, 40)
NAVY = (8, 14, 28)

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


def gradient(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, float)[None, None, :] * (1 - t) + np.array(bottom, float)[None, None, :] * t
    return Image.fromarray(np.repeat(a, w, axis=1).astype(np.uint8), 'RGB')


def radial(w, h, inner, outer, cx=0.5, cy=0.5, r=0.7):
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt(((x / w - cx) / r) ** 2 + ((y / h - cy) / r * h / w) ** 2)
    t = np.clip(d, 0, 1)[..., None]
    a = np.array(inner, float) * (1 - t) + np.array(outer, float) * t
    return Image.fromarray(a.astype(np.uint8), 'RGB')


def glow(img, radius=18, amount=1.0):
    g = img.filter(ImageFilter.GaussianBlur(radius))
    a = np.clip(np.asarray(img, float) + amount * np.asarray(g, float), 0, 255)
    return Image.fromarray(a.astype(np.uint8), img.mode)


def scan(img, k=0.12, period=4):
    a = np.asarray(img, float).copy()
    a[::period] *= (1 - k)
    return Image.fromarray(a.astype(np.uint8), img.mode)



RED = (220, 30, 36)
CH_NAME = 'GLOBAL 24'


def bug(d, x, y, s=1.0):
    d.rectangle([x, y, x + 210 * s, y + 64 * s], fill=RED)
    d.text((x + 105 * s, y + 32 * s), CH_NAME, font=F(BOLD, int(40 * s)), fill=(255, 255, 255), anchor='mm')


def phone_alert():
    w, h = 600, 1300
    im = gradient(w, h, (30, 40, 70), (8, 10, 20))
    d = ImageDraw.Draw(im)
    d.text((w / 2, 150), '07:41', font=F(BOLD, 150), fill=(245, 245, 250), anchor='mm')
    d.text((w / 2, 255), 'Tuesday, 14 May', font=F(BOLD, 34), fill=(200, 205, 220), anchor='mm')
    cards = [(RED, 'BREAKING NEWS', ['Every man on Earth has', 'disappeared, reports say', 'now']),
             ((60, 70, 90), 'GLOBAL 24', ['Live: governments call', 'emergency meetings', '1m ago']),
             ((60, 70, 90), 'Mum', ['Are you OK??? Call me', 'right now', '2m ago'])]
    y = 380
    for col, t, lines in cards:
        d.rounded_rectangle([30, y, w - 30, y + 210], radius=28, fill=(235, 236, 240))
        d.rounded_rectangle([50, y + 22, 90, y + 62], radius=8, fill=col)
        d.text((105, y + 42), t, font=F(BOLD, 30), fill=(30, 30, 35), anchor='lm')
        d.text((w - 50, y + 42), lines[2], font=F(BOLD, 24), fill=(120, 120, 130), anchor='rm')
        d.text((52, y + 100), lines[0], font=F(BOLD, 34), fill=(25, 25, 30), anchor='lm')
        d.text((52, y + 150), lines[1], font=F(BOLD, 34), fill=(25, 25, 30), anchor='lm')
        y += 235
    save(im, 'phone_alert')


def broadcast():
    """TV frame. The left 55 % is the presenter feed (a separate plane in 3D shows the rendered presenter)."""
    w, h = 1600, 900
    im = gradient(w, h, (16, 24, 46), (6, 8, 16))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], outline=(0, 0, 0))
    bug(d, w - 260, 40)
    d.rectangle([0, h - 250, w, h - 140], fill=RED)
    d.text((40, h - 195), 'BREAKING NEWS', font=F(BOLD, 74), fill=(255, 255, 255), anchor='lm')
    d.rectangle([0, h - 140, w, h - 60], fill=(250, 250, 250))
    d.text((40, h - 100), 'EVERY MAN ON EARTH HAS DISAPPEARED', font=fit(BOLD, 'EVERY MAN ON EARTH HAS DISAPPEARED', w - 80, 60), fill=(15, 15, 20), anchor='lm')
    d.rectangle([0, h - 60, w, h], fill=(10, 14, 26))
    d.text((40, h - 30), 'WORLDWIDE  -  NO MEN REPORTED IN ANY COUNTRY  -  GOVERNMENTS IN EMERGENCY SESSION  -  STAY TUNED',
           font=F(BOLD, 30), fill=(220, 225, 235), anchor='lm')
    d.text((1180, 180), 'LIVE', font=F(BOLD, 60), fill=RED, anchor='mm')
    save(im, 'broadcast')


def square_screens():
    w, h = 2048, 1152
    im = radial(w, h, (150, 20, 26), (40, 4, 8), r=0.9)
    d = ImageDraw.Draw(im)
    d.text((w / 2, 330), 'BREAKING NEWS', font=F(BOLD, 250), fill=(255, 255, 255), anchor='mm')
    d.rectangle([0, 560, w, 820], fill=(255, 255, 255))
    d.text((w / 2, 690), 'EVERY MAN ON EARTH HAS DISAPPEARED', font=fit(BOLD, 'EVERY MAN ON EARTH HAS DISAPPEARED', w - 120, 150), fill=(20, 10, 10), anchor='mm')
    bug(d, 60, 1020, 1.4)
    save(glow(im, 16, 0.3), 'sq_breaking')
    im = gradient(1024, 1536, (20, 30, 60), (5, 8, 18))
    d = ImageDraw.Draw(im)
    d.text((512, 500), 'WHERE', font=F(BOLD, 200), fill=(255, 255, 255), anchor='mm')
    d.text((512, 720), 'ARE THE', font=F(BOLD, 200), fill=(255, 255, 255), anchor='mm')
    d.text((512, 940), 'MEN?', font=F(BOLD, 260), fill=(255, 196, 40), anchor='mm')
    bug(d, 410, 1300, 1.0)
    save(glow(im, 16, 0.3), 'sq_where')


def globe():
    """A stylised globe of alerts (no real data): latitude/longitude lines and pulsing red markers."""
    w, h = 1600, 900
    im = Image.new('RGB', (w, h), (6, 10, 22))
    d = ImageDraw.Draw(im)
    cx, cy, r = 560, 450, 380
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 30, 60), outline=(60, 140, 220), width=4)
    for k in range(-80, 81, 20):
        yy = cy - r * math.sin(math.radians(k))
        rr = r * math.cos(math.radians(k))
        d.ellipse([cx - rr, yy - 4, cx + rr, yy + 4], outline=(40, 90, 150), width=2)
    for k in range(0, 180, 20):
        rr = r * abs(math.cos(math.radians(k)))
        d.ellipse([cx - rr, cy - r, cx + rr, cy + r], outline=(40, 90, 150), width=2)
    rng = np.random.default_rng(3)
    for _ in range(70):
        a, b = rng.uniform(0, 2 * math.pi), rng.uniform(0, 0.92)
        x, y = cx + r * b * math.cos(a), cy + r * b * math.sin(a) * 0.9
        q = rng.uniform(6, 16)
        d.ellipse([x - q, y - q, x + q, y + q], fill=(230, 40, 40))
        d.ellipse([x - 2.2 * q, y - 2.2 * q, x + 2.2 * q, y + 2.2 * q], outline=(230, 40, 40), width=2)
    d.text((1000, 280), 'ALERTS', font=F(BOLD, 80), fill=(255, 255, 255), anchor='lm')
    d.text((1000, 400), 'EVERY COUNTRY', font=F(BOLD, 64), fill=(255, 196, 40), anchor='lm')
    d.text((1000, 520), 'MEN MISSING', font=F(BOLD, 64), fill=(255, 255, 255), anchor='lm')
    d.text((1000, 640), 'MEN FOUND: 1', font=F(BOLD, 64), fill=RED, anchor='lm')
    bug(d, w - 260, 40)
    save(glow(im, 12, 0.3), 'globe')


def only_card():
    """His ID card on the news. Portrait frame at x 80..640, y 120..780 (a separate plane in 3D)."""
    w, h = 1600, 900
    im = gradient(w, h, (24, 30, 50), (6, 8, 14))
    d = ImageDraw.Draw(im)
    d.rectangle([70, 110, 650, 790], outline=(255, 255, 255), width=6)
    d.text((720, 210), 'CONFIRMED', font=F(BOLD, 70), fill=(255, 196, 40), anchor='lm')
    d.text((720, 360), 'THE ONLY', font=F(BOLD, 160), fill=(255, 255, 255), anchor='lm')
    d.text((720, 530), 'MAN ALIVE', font=F(BOLD, 160), fill=(255, 255, 255), anchor='lm')
    d.rectangle([720, 640, 1520, 650], fill=RED)
    d.text((720, 720), 'LOCATED IN THE CITY  -  IDENTITY WITHHELD', font=F(BOLD, 40), fill=(200, 210, 230), anchor='lm')
    bug(d, w - 260, 40)
    save(im, 'only_card')
    im = Image.new('RGB', (2048, 1152), (10, 10, 14))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 2048, 150], fill=RED)
    d.text((1024, 76), 'LIVE  -  GLOBAL 24', font=F(BOLD, 90), fill=(255, 255, 255), anchor='mm')
    d.rectangle([90, 230, 790, 1060], outline=(255, 255, 255), width=8)
    d.text((880, 470), 'THE LAST', font=F(BOLD, 250), fill=(255, 255, 255), anchor='lm')
    d.text((880, 740), 'MAN ALIVE', font=F(BOLD, 250), fill=(255, 196, 40), anchor='lm')
    d.text((880, 960), 'DAY 1  -  THE WORLD IS WATCHING', font=F(BOLD, 64), fill=(220, 220, 230), anchor='lm')
    save(glow(im, 16, 0.3), 'last_man')


def lab():
    w, h = 1600, 900
    im = Image.new('RGB', (w, h), (8, 16, 26))
    d = ImageDraw.Draw(im)
    d.text((40, 50), 'SUBJECT 001  -  GENETIC PROFILE', font=F(BOLD, 52), fill=(140, 220, 255), anchor='lm')
    for k in range(240):                                   # a DNA double helix
        t = k / 240 * 6 * math.pi
        x = 120 + k * 5.6
        y1, y2 = 470 + 150 * math.sin(t), 470 - 150 * math.sin(t)
        d.ellipse([x - 5, y1 - 5, x + 5, y1 + 5], fill=(90, 200, 255))
        d.ellipse([x - 5, y2 - 5, x + 5, y2 + 5], fill=(255, 120, 160))
        if k % 6 == 0:
            d.line([(x, y1), (x, y2)], fill=(80, 120, 160), width=3)
    d.rectangle([40, 700, 820, 800], outline=(255, 196, 40), width=4)
    d.text((60, 750), 'Y CHROMOSOME: PRESENT', font=F(BOLD, 56), fill=(255, 196, 40), anchor='lm')
    d.text((900, 750), 'ANALYSIS RUNNING...', font=F(BOLD, 48), fill=(140, 220, 255), anchor='lm')
    save(scan(im, 0.12), 'lab_dna')
    im = Image.new('RGB', (w, h), (6, 12, 20))
    d = ImageDraw.Draw(im)
    d.text((40, 50), 'SUBJECT 001  -  FACIAL SCAN', font=F(BOLD, 52), fill=(140, 220, 255), anchor='lm')
    d.rectangle([60, 120, 620, 840], outline=(140, 220, 255), width=4)
    for k in range(9):
        d.line([(60, 120 + 80 * k), (620, 120 + 80 * k)], fill=(30, 70, 100), width=1)
    labels = ['MATCH: 0 RECORDS', 'AGE: 30-35', 'HEALTH: NORMAL', 'STATUS: UNEXPLAINED']
    for k, t in enumerate(labels):
        d.text((700, 220 + 130 * k), t, font=F(BOLD, 60), fill=(255, 196, 40) if k == 3 else (200, 230, 250), anchor='lm')
    save(scan(im, 0.12), 'lab_face')


def office():
    rng = np.random.default_rng(4)
    for k in range(3):
        w, h = 800, 500
        im = Image.new('RGB', (w, h), (235, 238, 242))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w, 50], fill=(40, 90, 160))
        if k == 0:
            vals = np.cumsum(rng.normal(1, 3, 20)) + 40
            pts = [(40 + i * 37, 440 - v * 4) for i, v in enumerate(vals)]
            d.line(pts, fill=(40, 140, 80), width=6)
        elif k == 1:
            for i in range(8):
                hh = rng.uniform(80, 360)
                d.rectangle([60 + i * 88, 450 - hh, 120 + i * 88, 450], fill=(60, 120, 200))
        else:
            for i in range(9):
                d.rectangle([30, 80 + i * 44, 770, 116 + i * 44], outline=(180, 185, 195))
                d.rectangle([30, 80 + i * 44, 200, 116 + i * 44], fill=(210, 220, 235))
        save(im, f'office{k}')


def signs():
    sign_ = lambda name, text, bg, fg, w=1400, h=260: _sign(name, text, bg, fg, w, h)
    sign_('hosp_sign', 'WARD 4    ->', (20, 90, 160), (255, 255, 255))
    sign_('train_sign', 'CENTRAL   2 min', (10, 10, 12), (255, 170, 30))
    sign_('office_sign', 'MERIDIAN & CO', (240, 240, 242), (30, 40, 60))
    im = Image.new('RGB', (1024, 1024), (40, 24, 20))
    d = ImageDraw.Draw(im)
    d.ellipse([162, 112, 862, 812], outline=(214, 186, 120), width=16)
    d.polygon([(512, 230), (640, 500), (512, 700), (384, 500)], outline=(214, 186, 120), width=12)
    d.text((512, 900), 'THE ASSEMBLY', font=F(SERIF, 90), fill=(214, 186, 120), anchor='mm')
    save(im, 'parl_crest')


def _sign(name, text, bg, fg, w, h):
    im = Image.new('RGB', (w, h), bg)
    d = ImageDraw.Draw(im)
    d.text((w / 2, h / 2), text, font=fit(BOLD, text, w * 0.9, int(h * 0.62)), fill=fg, anchor='mm')
    save(im, name)


def placeholder(name, w, h, txt):
    rng = np.random.default_rng(len(name))
    a = (rng.random((h // 4, w // 4)) * 60).astype(np.uint8)
    im = Image.fromarray(np.kron(a, np.ones((4, 4), np.uint8))).convert('RGB')
    d = ImageDraw.Draw(im)
    d.text((w / 2, h / 2), txt, font=F(BOLD, h // 8), fill=(200, 200, 200), anchor='mm')
    save(im, name)


# --- Part 2 -------------------------------------------------------------------------------------------------------------
VIOLET = (190, 120, 255)


def search_board():
    """The billboard that switches on in scene 1. Portrait frame at x 90..790, y 200..1060 (a separate plane in 3D)."""
    w, h = 2048, 1152
    im = Image.new('RGB', (w, h), (8, 10, 18))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 140], fill=RED)
    d.text((w / 2, 72), 'GLOBAL ALERT  -  HAVE YOU SEEN THIS MAN?', font=F(BOLD, 86), fill=(255, 255, 255), anchor='mm')
    d.rectangle([80, 190, 800, 1070], outline=(255, 255, 255), width=8)
    d.text((880, 380), 'THE ENTIRE', font=F(BOLD, 200), fill=(255, 255, 255), anchor='lm')
    d.text((880, 590), 'WORLD IS', font=F(BOLD, 200), fill=(255, 255, 255), anchor='lm')
    d.text((880, 800), 'SEARCHING', font=F(BOLD, 200), fill=(255, 196, 40), anchor='lm')
    d.text((880, 990), 'FOR YOU.', font=F(BOLD, 150), fill=(255, 196, 40), anchor='lm')
    bug(d, w - 300, 1050, 1.3)
    save(glow(im, 14, 0.3), 'search_board')


def urgent():
    w, h = 1600, 900
    im = Image.new('RGB', (w, h), (14, 6, 8))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 110], fill=(180, 20, 26))
    d.text((40, 56), 'URGENT  -  PRIORITY ONE', font=F(BOLD, 70), fill=(255, 255, 255), anchor='lm')
    d.text((w - 40, 56), '07:12 UTC', font=F(BOLD, 56), fill=(255, 220, 220), anchor='rm')
    d.text((40, 200), 'LOCATE AND PROTECT: SUBJECT 001', font=F(BOLD, 78), fill=(255, 196, 40), anchor='lm')
    msgs = ['INCOMING  -  NORTH ATLANTIC COUNCIL', 'INCOMING  -  PACIFIC ALLIANCE', 'INCOMING  -  AFRICAN UNION OFFICE',
            'INCOMING  -  SOUTH AMERICAN BLOC', 'INCOMING  -  EAST ASIA SUMMIT', 'INCOMING  -  GLOBAL HEALTH AGENCY']
    for k, m in enumerate(msgs):
        y = 330 + k * 88
        d.rectangle([40, y - 34, 1000, y + 34], outline=(200, 60, 60), width=3)
        d.text((70, y), m, font=F(BOLD, 44), fill=(240, 220, 220), anchor='lm')
        d.text((980, y), 'OPEN', font=F(BOLD, 40), fill=(255, 120, 120), anchor='rm')
    d.ellipse([1100, 330, 1520, 750], outline=(200, 60, 60), width=6)
    d.text((1310, 540), '193', font=F(BOLD, 140), fill=(255, 255, 255), anchor='mm')
    d.text((1310, 800), 'MESSAGES', font=F(BOLD, 50), fill=(255, 160, 160), anchor='mm')
    save(scan(im, 0.12), 'urgent')


def dis_data():
    """Worldwide disappearance data: a stylised world grid and charts (no real data)."""
    w, h = 1600, 900
    im = Image.new('RGB', (w, h), (6, 10, 22))
    d = ImageDraw.Draw(im)
    d.text((40, 50), 'DISAPPEARANCE EVENT  -  ALL REGIONS', font=F(BOLD, 56), fill=(140, 220, 255), anchor='lm')
    rng = np.random.default_rng(9)
    for i in range(36):
        for j in range(16):
            x, y = 60 + i * 24, 130 + j * 24
            v = rng.random()
            col = (int(40 + 200 * v), int(30 + 40 * v), int(80 + 60 * (1 - v)))
            d.rectangle([x, y, x + 20, y + 20], fill=col)
    for k in range(8):
        hh = rng.uniform(60, 300)
        d.rectangle([980 + k * 70, 560 - hh, 1030 + k * 70, 560], fill=(90, 180, 255))
    d.text((980, 620), 'REPORTS BY REGION', font=F(BOLD, 40), fill=(160, 200, 230), anchor='lm')
    d.text((60, 600), 'SIMULTANEOUS IN ALL TIME ZONES', font=F(BOLD, 54), fill=(255, 196, 40), anchor='lm')
    d.text((60, 690), 'MEN FOUND:  1', font=F(BOLD, 54), fill=(255, 255, 255), anchor='lm')
    save(scan(im, 0.12), 'dis_data')


def timeline(highlight=False):
    w, h = 3200, 900
    im = Image.new('RGB', (w, h), (4, 8, 16))
    d = ImageDraw.Draw(im)
    d.text((60, 70), 'GLOBAL POPULATION  -  MALE  -  LAST 24 HOURS', font=F(BOLD, 64), fill=(140, 220, 255), anchor='lm')
    for x in range(200, 3100, 200):
        d.line([(x, 150), (x, 760)], fill=(16, 34, 56), width=2)
        d.text((x, 800), f'{(x // 200) % 24:02d}:00', font=F(BOLD, 30), fill=(90, 130, 170), anchor='mm')
    xs = np.arange(200, 3100, 4)
    spike = 1730
    ys = np.where(xs < spike, 240 + 6 * np.sin(xs / 60.0), 740)
    pts = list(zip(xs.tolist(), ys.tolist()))
    d.line(pts, fill=(90, 210, 255), width=8)
    d.line([(spike, 150), (spike, 770)], fill=(255, 80, 80), width=5)
    d.rectangle([spike + 30, 300, spike + 1120, 560], fill=(30, 8, 12), outline=(255, 80, 80), width=4)
    d.text((spike + 60, 370), '04:17:09.000 UTC', font=F(BOLD, 80), fill=(255, 255, 255), anchor='lm')
    d.text((spike + 60, 470), 'ABOUT 4 BILLION GONE  -  SAME INSTANT', font=F(BOLD, 52), fill=(255, 160, 160), anchor='lm')
    if highlight:
        d.rectangle([300, 300, 1100, 720], fill=(40, 6, 10), outline=(255, 50, 50), width=10)
        d.rectangle([330, 330, 640, 690], outline=(255, 255, 255), width=5)
        d.text((680, 400), 'ANOMALY', font=F(BOLD, 96), fill=(255, 70, 70), anchor='lm')
        d.text((680, 520), 'SUBJECT 001', font=F(BOLD, 60), fill=(255, 255, 255), anchor='lm')
        d.text((680, 610), 'NOT AFFECTED', font=F(BOLD, 60), fill=(255, 196, 40), anchor='lm')
    save(scan(glow(im, 10, 0.3), 0.1), 'anomaly' if highlight else 'timeline')


def symbol():
    """An invented symbol: a ring open at the top, a vertical line through it, a small triangle and a column of three
    dots. It means nothing (yet)."""
    w, h = 2048, 1152
    im = Image.new('RGB', (w, h), (3, 2, 8))
    d = ImageDraw.Draw(im)
    cx, cy = w / 2, h / 2
    d.arc([cx - 380, cy - 380, cx + 380, cy + 380], -60, 240, fill=VIOLET, width=26)
    d.line([(cx, cy - 480), (cx, cy + 470)], fill=VIOLET, width=20)
    d.polygon([(cx - 120, cy - 70), (cx + 120, cy - 70), (cx, cy + 120)], outline=VIOLET, width=16)
    for k in range(3):
        y = cy + 200 + k * 70
        d.ellipse([cx + 150 - 26, y - 26, cx + 150 + 26, y + 26], fill=(240, 220, 255))
    for sx in (-1, 1):
        d.line([(cx + sx * 470, cy), (cx + sx * 560, cy)], fill=VIOLET, width=14)
    save(glow(glow(im, 30, 0.8), 10, 0.5), 'symbol')

def main():
    phone_alert()
    broadcast()
    square_screens()
    globe()
    only_card()
    lab()
    office()
    signs()
    search_board()
    urgent()
    dis_data()
    timeline(False)
    timeline(True)
    symbol()
    placeholder('portrait', 480, 600, '?')
    placeholder('anchorfeed', 880, 650, 'LIVE')
    print('textures ->', OUT)


if __name__ == '__main__':
    main()
