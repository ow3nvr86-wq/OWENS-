"""Procedural screen graphics and prop textures for "What If You Were the Only Man Alive? Part 3" (Pillow + numpy, code only).

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


# --- Part 3 -------------------------------------------------------------------------------------------------------------
BLUE = (70, 170, 255)
SIG = (110, 200, 255)

# Approximate coastlines as (longitude, latitude) polygons, typed in by hand (no map data is downloaded). Coastlines are
# roughened with noise afterwards; the result reads as Earth from orbit, not as an accurate map.
LAND = [
    # North America
    [(-166, 68), (-156, 71), (-141, 70), (-128, 70), (-110, 68), (-95, 68), (-90, 69), (-82, 67), (-80, 63), (-75, 62),
     (-65, 60), (-60, 55), (-56, 52), (-60, 47), (-66, 44), (-70, 42), (-74, 40), (-76, 35), (-80, 32), (-81, 28), (-80, 25),
     (-82, 27), (-84, 30), (-89, 30), (-94, 29), (-97, 26), (-97, 22), (-95, 19), (-91, 19), (-87, 21), (-88, 16), (-84, 15),
     (-83, 10), (-80, 8), (-78, 9), (-80, 7), (-83, 8), (-86, 11), (-91, 14), (-96, 16), (-105, 20), (-109, 23), (-112, 29),
     (-114, 31), (-117, 32), (-121, 35), (-124, 40), (-124, 46), (-125, 49), (-130, 54), (-135, 57), (-140, 60), (-147, 61),
     (-152, 59), (-158, 57), (-165, 55), (-160, 58), (-165, 61), (-166, 64)],
    # Arctic islands
    [(-120, 72), (-100, 73), (-80, 73), (-75, 79), (-90, 81), (-110, 78), (-122, 76)],
    # Greenland
    [(-73, 78), (-60, 82), (-35, 83), (-20, 82), (-18, 77), (-22, 70), (-32, 68), (-42, 60), (-50, 62), (-55, 68), (-60, 76)],
    # Iceland
    [(-24, 64), (-14, 64), (-14, 66), (-22, 66)],
    # South America
    [(-77, 8), (-72, 12), (-63, 11), (-60, 8), (-52, 5), (-50, 0), (-44, -2), (-35, -5), (-35, -9), (-39, -15), (-41, -22),
     (-48, -26), (-53, -34), (-58, -38), (-62, -40), (-65, -45), (-68, -50), (-69, -55), (-72, -53), (-75, -47), (-73, -40),
     (-72, -30), (-70, -20), (-75, -15), (-80, -6), (-81, -2), (-79, 2)],
    # Africa
    [(-17, 21), (-13, 28), (-9, 32), (-6, 36), (0, 36), (10, 37), (11, 33), (20, 31), (25, 32), (32, 31), (34, 28), (37, 22),
     (43, 12), (51, 12), (51, 10), (44, 1), (40, -5), (40, -11), (35, -20), (33, -26), (28, -33), (20, -35), (18, -30),
     (12, -18), (13, -10), (9, -1), (9, 4), (5, 6), (-3, 5), (-8, 4), (-13, 8), (-17, 14)],
    # Madagascar
    [(44, -25), (47, -25), (50, -15), (49, -12), (44, -17)],
    # Eurasia (with Arabia)
    [(-9, 43), (-9, 37), (-5, 36), (0, 38), (3, 42), (8, 44), (12, 42), (16, 38), (18, 40), (20, 40), (23, 36), (26, 40),
     (29, 41), (36, 37), (36, 34), (35, 31), (35, 28), (39, 22), (43, 15), (45, 13), (52, 16), (56, 18), (59, 22), (56, 26),
     (52, 24), (50, 26), (48, 30), (52, 28), (57, 26), (62, 25), (67, 24), (70, 21), (73, 16), (76, 9), (78, 8), (80, 13),
     (80, 16), (87, 21), (90, 22), (92, 21), (94, 17), (98, 16), (98, 8), (100, 4), (103, 1), (104, 2), (102, 6), (100, 13),
     (103, 11), (106, 9), (109, 12), (108, 16), (106, 20), (110, 21), (117, 23), (121, 28), (122, 31), (120, 35), (122, 37),
     (118, 38), (122, 40), (125, 40), (129, 35), (129, 38), (130, 43), (135, 44), (141, 48), (141, 53), (136, 55), (141, 59),
     (150, 59), (157, 61), (162, 58), (156, 51), (160, 53), (165, 60), (172, 63), (180, 65), (180, 69), (170, 70), (160, 70),
     (150, 72), (140, 72), (130, 72), (120, 73), (113, 74), (105, 77), (95, 76), (80, 73), (70, 73), (66, 70), (60, 70),
     (55, 68), (45, 68), (40, 66), (35, 69), (28, 71), (20, 70), (15, 68), (10, 63), (5, 60), (6, 58), (8, 57), (10, 59),
     (12, 56), (10, 54), (8, 54), (5, 53), (3, 51), (-2, 48), (-5, 48), (-1, 46), (-2, 44)],
    # Britain and Ireland
    [(-5, 50), (1, 51), (2, 53), (0, 54), (-2, 56), (-2, 58), (-5, 59), (-6, 57), (-5, 55), (-3, 54), (-5, 52)],
    [(-10, 52), (-6, 52), (-6, 55), (-8, 55), (-10, 54)],
    # Japan
    [(130, 31), (132, 34), (136, 34), (140, 35), (141, 38), (142, 42), (145, 43), (141, 45), (140, 41), (139, 38), (136, 36),
     (132, 35), (130, 33)],
    # Sumatra, Borneo, Java, New Guinea, the Philippines, Sri Lanka, Cuba
    [(95, 5), (98, 4), (104, -2), (106, -6), (102, -4), (96, 2)],
    [(109, 1), (111, -3), (116, -4), (119, 1), (117, 7), (113, 3)],
    [(105, -6), (114, -7), (114, -8), (106, -7)],
    [(131, -1), (138, -2), (145, -5), (150, -10), (142, -9), (138, -8), (134, -4)],
    [(120, 18), (122, 18), (126, 8), (124, 6), (120, 12)],
    [(80, 9), (82, 7), (81, 6), (80, 7)],
    [(-85, 22), (-80, 23), (-75, 20), (-78, 20), (-84, 21)],
    # Australia, New Zealand
    [(114, -22), (114, -34), (118, -35), (124, -34), (131, -31), (137, -34), (140, -38), (146, -39), (150, -37), (153, -30),
     (153, -25), (146, -19), (142, -11), (140, -17), (136, -12), (131, -11), (126, -14), (122, -17)],
    [(166, -46), (172, -41), (175, -37), (178, -38), (174, -42), (170, -46)],
]
WATER = [  # inland seas cut back out of the land
    [(-95, 58), (-88, 56), (-80, 52), (-78, 58), (-79, 63), (-86, 64), (-93, 63)],                      # Hudson Bay
    [(28, 42), (41, 41), (39, 47), (31, 46)],                                                           # Black Sea
    [(47, 37), (54, 37), (53, 45), (48, 46)],                                                           # Caspian Sea
    [(33, 28), (35, 27.5), (39, 21), (43.5, 13), (42.5, 13), (38, 19), (34, 26)],                       # Red Sea
    [(48, 30), (50, 29), (56, 26.5), (56, 25), (52, 24), (50, 26)],                                     # Persian Gulf
]


def _fbm(h, w, seed, octaves=6, base=4):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = base * 2 ** o, base * 2 ** o * 2
        g = rng.random((gh + 1, gw + 1))
        g[:, -1] = g[:, 0]                       # wraps around in longitude
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += amp * np.asarray(im, float) / 255
        tot += amp
        amp *= 0.5
    return out / tot


def earth():
    """Equirectangular Earth for the satellite views and the hologram: coastlines from LAND, roughened with noise;
    forests, deserts, tundra and ice by latitude and noise; ocean shelves; plus a separate cloud layer."""
    W, H = 4096, 2048
    px = lambda lon, lat: ((lon + 180) / 360 * W, (90 - lat) / 180 * H)
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for poly in LAND:
        d.polygon([px(*p) for p in poly], fill=255)
    for poly in WATER:
        d.polygon([px(*p) for p in poly], fill=0)
    lat = np.linspace(90, -90, H)[:, None] * np.ones((1, W))
    d.rectangle([0, px(0, -70)[1], W, H], fill=255)                     # Antarctica
    # roughen the coasts: warp the mask by noise, then re-threshold with noise
    mask = np.asarray(m.filter(ImageFilter.GaussianBlur(6)), float) / 255
    n1, n2 = _fbm(H, W, 1, 7, 6), _fbm(H, W, 2, 7, 6)
    yy, xx = np.mgrid[0:H, 0:W]
    wx = np.clip((xx + (n1 - 0.5) * 70).astype(int) % W, 0, W - 1)
    wy = np.clip((yy + (n2 - 0.5) * 50).astype(int), 0, H - 1)
    mask = mask[wy, wx]
    land = mask + (_fbm(H, W, 3, 7, 8) - 0.5) * 0.35 > 0.5
    ant = lat < -66 - 5 * _fbm(H, W, 9, 4, 3)
    land |= ant
    shelf = np.asarray(Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14)), float) / 255
    # ocean
    deep = np.array([4, 18, 52], float)
    mid = np.array([10, 42, 92], float)
    shallow = np.array([30, 92, 130], float)
    t = np.clip(shelf * 2.2, 0, 1)[..., None]
    ocean = deep * (1 - t) + mid * t
    ocean = ocean * (1 - np.clip(shelf - 0.35, 0, 1)[..., None] * 1.2) + shallow * np.clip(shelf - 0.35, 0, 1)[..., None] * 1.2
    ocean *= (0.92 + 0.12 * _fbm(H, W, 4, 5, 4))[..., None]
    # land
    n = _fbm(H, W, 5, 7, 8)
    alat = np.abs(lat)
    forest = np.array([34, 62, 28], float)
    grass = np.array([88, 104, 52], float)
    desert = np.array([186, 156, 108], float)
    tundra = np.array([104, 100, 84], float)
    ice = np.array([236, 240, 244], float)
    dry = np.clip(1 - np.abs(alat - 24) / 12, 0, 1) * np.clip((n - 0.32) * 3, 0, 1)
    col = forest * (1 - n[..., None]) + grass * n[..., None]
    col = col * (1 - dry[..., None]) + desert * dry[..., None]
    tun = np.clip((alat - 55) / 12, 0, 1)
    col = col * (1 - tun[..., None]) + tundra * tun[..., None]
    snow = np.clip((alat - 68) / 6, 0, 1) + ant
    gl = (np.abs(xx / W * 360 - 180 + 42) < 22) & (lat > 60)              # Greenland ice
    snow = np.clip(snow + gl * 0.9, 0, 1)
    col = col * (1 - snow[..., None]) + ice * snow[..., None]
    col *= (0.85 + 0.3 * _fbm(H, W, 6, 6, 16))[..., None]
    img = np.where(land[..., None], col, ocean)
    save(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB'), 'earth')
    # clouds: banded fractal noise, thinner in the subtropics, swirled
    c = _fbm(H, W, 7, 8, 6)
    c2 = _fbm(H, W, 8, 8, 12)
    band = 0.75 + 0.25 * np.cos(np.radians(alat) * 6.0)
    cl = np.clip((c * 0.65 + c2 * 0.35 - 0.47) * 3.2 * band, 0, 1) ** 1.3
    save(Image.fromarray((cl * 255).astype(np.uint8), 'L'), 'clouds')


def stars():
    W, H = 4096, 2048
    rng = np.random.default_rng(11)
    a = np.zeros((H, W, 3))
    yy, xx = np.mgrid[0:H, 0:W]
    lon = xx / W * 2 * math.pi
    lat = (0.5 - yy / H) * math.pi
    # the Milky Way: a soft band along a tilted great circle
    v = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    nrm = np.array([0.35, -0.45, 0.82])
    nrm /= np.linalg.norm(nrm)
    db = np.abs(v @ nrm)
    band = np.exp(-(db / 0.16) ** 2) * (0.55 + 0.6 * _fbm(H, W, 12, 6, 6))
    a += band[..., None] * np.array([22, 24, 34]) * 1.2
    n = 26000
    ys, xs = rng.integers(0, H, n), rng.integers(0, W, n)
    b = rng.pareto(2.2, n) * 60 + 40
    tint = rng.choice([[1, 0.9, 0.8], [0.85, 0.9, 1], [1, 1, 1], [1, 0.8, 0.6]], n)
    a[ys, xs] += np.minimum(b, 255)[:, None] * tint
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGB')
    big = Image.fromarray(np.clip(a * (a.max(axis=2, keepdims=True) > 150), 0, 255).astype(np.uint8), 'RGB')
    img = Image.fromarray(np.clip(np.asarray(img, float) + np.asarray(big.filter(ImageFilter.GaussianBlur(2)), float) * 2.5,
                                  0, 255).astype(np.uint8), 'RGB')
    save(img, 'stars')


def sig_wave(d, x0, y0, w, h, col=SIG, width=6, reps=3):
    """The signal's signature - three short pulses and one long one, repeating - drawn as a waveform."""
    pts = []
    unit = w / (reps * 10.0)
    for r in range(reps):
        for k in range(3):
            base = x0 + (r * 10 + k * 1.6) * unit
            pts += [(base, y0), (base + 0.25 * unit, y0 - h * 0.85), (base + 0.5 * unit, y0 + h * 0.35), (base + 0.75 * unit, y0)]
        base = x0 + (r * 10 + 5.2) * unit
        pts += [(base, y0), (base + 0.4 * unit, y0 - h), (base + 2.4 * unit, y0 - h), (base + 2.8 * unit, y0 + h * 0.3),
                (base + 3.2 * unit, y0)]
    pts = [(x0, y0)] + pts + [(x0 + w, y0)]
    d.line(pts, fill=col, width=width, joint='curve')


def sig_glyph(d, cx, cy, r, col=SIG, width=10):
    """The signal's mark: three short arcs and one long arc around a dot (3 + 1)."""
    for k in range(3):
        a0 = -150 + k * 34
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + 22, fill=col, width=width)
    d.arc([cx - r, cy - r, cx + r, cy + r], -30, 170, fill=col, width=width)
    rr = r * 0.62
    for k in range(3):
        a0 = 30 + k * 34
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], a0, a0 + 22, fill=col, width=int(width * 0.8))
    d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 350, fill=col, width=int(width * 0.8))
    d.ellipse([cx - r * 0.12, cy - r * 0.12, cx + r * 0.12, cy + r * 0.12], fill=(235, 248, 255))


def sig_monitor(pattern):
    """The lead scientist's vertical monitor (900 x 1600): SUBJECT 001 on top (photo frame x 70..500, y 170..710 - the 3D
    portrait is laid over it), and below it the unidentified pattern appearing beside his data."""
    w, h = 900, 1600
    im = Image.new('RGB', (w, h), (3, 8, 18))
    d = ImageDraw.Draw(im)
    d.text((40, 60), 'CROSS-REFERENCE', font=F(BOLD, 52), fill=(140, 200, 255), anchor='lm')
    d.text((40, 116), 'DISAPPEARANCE EVENT  -  SUBJECT 001', font=F(BOLD, 34), fill=(90, 140, 190), anchor='lm')
    d.rectangle([70, 170, 500, 710], outline=(230, 240, 255), width=6)
    for k, (a_, b_) in enumerate((('STATUS', 'UNAFFECTED'), ('AGE', '30-35'), ('MATCHES', '0'), ('SCANS', '41'))):
        d.text((540, 220 + k * 120), a_, font=F(BOLD, 34), fill=(110, 160, 210), anchor='lm')
        d.text((540, 270 + k * 120), b_, font=F(BOLD, 50), fill=(235, 245, 255), anchor='lm')
    if pattern:
        d.rectangle([40, 770, 860, 1520], fill=(4, 18, 40), outline=SIG, width=5)
        d.text((450, 830), 'UNIDENTIFIED PATTERN', font=F(BOLD, 58), fill=SIG, anchor='mm')
        sig_glyph(d, 450, 1100, 200, width=18)
        sig_wave(d, 90, 1400, 720, 70, width=7, reps=2)
        d.text((450, 1480), 'LINKED TO SUBJECT 001', font=F(BOLD, 40), fill=(255, 200, 80), anchor='mm')
    else:
        d.rectangle([40, 770, 860, 1520], fill=(6, 12, 22), outline=(40, 70, 100), width=3)
        d.text((450, 1140), 'SEARCHING...', font=F(BOLD, 64), fill=(70, 110, 150), anchor='mm')
    save(scan(glow(im, 12, 0.6 if pattern else 0.3), 0.1), 'sigmon_b' if pattern else 'sigmon_a')


def timeline3():
    """The giant holographic timeline ribbon: the male population trace and the signal trace, one above the other."""
    w, h = 4096, 640
    im = Image.new('RGB', (w, h), (0, 0, 0))
    d = ImageDraw.Draw(im)
    X = 2460                                   # the instant
    for x in range(120, w - 60, 160):
        d.line([(x, 70), (x, 560)], fill=(18, 40, 70), width=2)
        d.text((x, 600), f'{(x // 160) % 24:02d}:00', font=F(BOLD, 26), fill=(80, 130, 180), anchor='mm')
    d.text((130, 40), 'GLOBAL POPULATION  -  MALE', font=F(BOLD, 40), fill=(150, 220, 255), anchor='lm')
    xs = np.arange(120, w - 60, 4)
    ys = np.where(xs < X, 150 + 5 * np.sin(xs / 50.0), 280)
    d.line(list(zip(xs.tolist(), ys.tolist())), fill=(120, 220, 255), width=8)
    d.text((130, 345), 'DEEP-SPACE BAND  -  UNIDENTIFIED SIGNAL', font=F(BOLD, 40), fill=(110, 170, 255), anchor='lm')
    rng = np.random.default_rng(3)
    ys2 = 470 + rng.normal(0, 4, len(xs))
    ys2[np.abs(xs - X) < 6] = 380
    d.line(list(zip(xs.tolist(), ys2.tolist())), fill=(90, 150, 255), width=5)
    sig_wave(d, X - 10, 470, 380, 80, col=(170, 225, 255), width=7, reps=1)
    d.line([(X, 60), (X, 570)], fill=(255, 255, 255), width=8)
    d.rectangle([X + 420, 70, X + 1380, 250], fill=(6, 20, 44), outline=(170, 225, 255), width=4)
    d.text((X + 450, 120), '04:17:09.000 UTC', font=F(BOLD, 72), fill=(255, 255, 255), anchor='lm')
    d.text((X + 450, 205), 'SIGNAL + DISAPPEARANCE  -  SAME INSTANT', font=F(BOLD, 40), fill=(255, 200, 80), anchor='lm')
    save(glow(glow(im, 24, 0.6), 6, 0.4), 'timeline3')


def compare():
    w, h = 1600, 900
    im = Image.new('RGB', (w, h), (3, 8, 18))
    d = ImageDraw.Draw(im)
    d.text((40, 56), 'TRACE COMPARISON', font=F(BOLD, 56), fill=(255, 255, 255), anchor='lm')
    X = 1000
    xs = np.arange(60, 1540, 3)
    d.line(list(zip(xs.tolist(), np.where(xs < X, 260 + 4 * np.sin(xs / 30.0), 520).tolist())), fill=(120, 220, 255), width=7)
    rng = np.random.default_rng(5)
    y2 = 640 + rng.normal(0, 4, len(xs))
    d.line(list(zip(xs.tolist(), y2.tolist())), fill=(90, 150, 255), width=5)
    sig_wave(d, X - 8, 640, 300, 90, col=(180, 230, 255), width=7, reps=1)
    d.line([(X, 140), (X, 800)], fill=(255, 255, 255), width=5)
    d.text((70, 330), 'POPULATION - MALE', font=F(BOLD, 34), fill=(120, 220, 255), anchor='lm')
    d.text((70, 720), 'UNIDENTIFIED SIGNAL', font=F(BOLD, 34), fill=(110, 170, 255), anchor='lm')
    d.rectangle([X + 30, 150, X + 530, 260], fill=(40, 30, 6), outline=(255, 200, 80), width=4)
    d.text((X + 60, 205), 'OFFSET  0.000 s', font=F(BOLD, 56), fill=(255, 210, 90), anchor='lm')
    save(scan(glow(im, 10, 0.4), 0.1), 'compare')


def sigmap():
    """The giant display: a deep-space chart with the incoming signal's path to Earth."""
    w, h = 2048, 1152
    rng = np.random.default_rng(21)
    a = np.zeros((h, w, 3))
    for _ in range(2500):
        y, x = rng.integers(0, h), rng.integers(0, w)
        a[y, x] = rng.uniform(60, 220)
    im = Image.fromarray(a.astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(im)
    for r in range(120, 1400, 140):
        d.ellipse([1700 - r, 640 - r, 1700 + r, 640 + r], outline=(16, 40, 70), width=2)
    d.ellipse([1640, 580, 1760, 700], fill=(30, 90, 170), outline=(150, 210, 255), width=4)
    d.text((1700, 740), 'EARTH', font=F(BOLD, 34), fill=(150, 210, 255), anchor='mm')
    pts = [(120 + k * 30, 520 + 120 * math.sin(k / 9.0) * (1 - k / 52)) for k in range(52)]
    for k in range(0, len(pts) - 1, 2):
        d.line([pts[k], pts[k + 1]], fill=SIG, width=6)
    sig_glyph(d, 300, 470, 110, width=10)
    d.text((70, 90), 'UNEXPLAINED SIGNAL', font=F(BOLD, 84), fill=(255, 255, 255), anchor='lm')
    d.text((70, 175), 'ORIGIN: DEEP SPACE  -  DISTANCE: UNKNOWN', font=F(BOLD, 44), fill=SIG, anchor='lm')
    d.text((70, 1020), 'ARRIVAL  04:17:09.000 UTC  -  PATTERN  3 + 1 PULSES, REPEATING', font=F(BOLD, 44), fill=(255, 200, 80), anchor='lm')
    sig_wave(d, 1000, 1000, 900, 60, width=6, reps=3)
    save(glow(im, 14, 0.5), 'sigmap')


def source(reversed_=False):
    """The monitors once the signal reverses: the origin is recalculated to this facility - to SUBJECT 001."""
    w, h = 1600, 900
    im = Image.new('RGB', (w, h), (10, 4, 8) if reversed_ else (3, 8, 18))
    d = ImageDraw.Draw(im)
    red = (255, 70, 70)
    d.text((40, 56), 'SIGNAL ORIGIN  -  RECALCULATED', font=F(BOLD, 52), fill=(255, 255, 255), anchor='lm')
    cx, cy = 420, 500
    for r in (330, 250, 170, 90):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=red, width=4)
    d.line([(cx - 360, cy), (cx + 360, cy)], fill=red, width=2)
    d.line([(cx, cy - 360), (cx, cy + 360)], fill=red, width=2)
    d.text((cx + 20, cy - 30), 'FACILITY 7  -  HALL A', font=F(BOLD, 34), fill=(255, 200, 200), anchor='lm')
    d.text((880, 330), 'SOURCE:', font=F(BOLD, 64), fill=(255, 160, 160), anchor='lm')
    d.text((880, 450), 'SUBJECT 001', font=F(BOLD, 120), fill=red, anchor='lm')
    d.text((880, 570), 'DISTANCE: 0 m', font=F(BOLD, 56), fill=(255, 255, 255), anchor='lm')
    sig_wave(d, 880, 720, 640, 60, col=(255, 120, 120), width=6, reps=2)
    save(scan(glow(im, 14, 0.6), 0.1), 'source')


def symbol_screen():
    """The Part 2 symbol on the vertical monitor, now beside the signal's mark (900 x 1600)."""
    w, h = 900, 1600
    im = Image.new('RGB', (w, h), (4, 3, 10))
    d = ImageDraw.Draw(im)
    VIO = (190, 120, 255)
    cx, cy = 450, 520
    d.arc([cx - 300, cy - 300, cx + 300, cy + 300], -60, 240, fill=VIO, width=20)
    d.line([(cx, cy - 380), (cx, cy + 370)], fill=VIO, width=16)
    d.polygon([(cx - 95, cy - 55), (cx + 95, cy - 55), (cx, cy + 95)], outline=VIO, width=13)
    for k in range(3):
        y = cy + 160 + k * 56
        d.ellipse([cx + 120 - 20, y - 20, cx + 120 + 20, y + 20], fill=(240, 220, 255))
    sig_glyph(d, 450, 1130, 170, width=14)
    d.text((450, 1380), 'PATTERN MATCH', font=F(BOLD, 64), fill=(255, 255, 255), anchor='mm')
    d.text((450, 1490), '100%', font=F(BOLD, 110), fill=(255, 200, 80), anchor='mm')
    save(glow(glow(im, 26, 0.7), 8, 0.4), 'symbol2')


def sig_strip():
    """The signal's signature as a 1-D strip (3 short pulses + 1 long, then a gap) for the beam shader."""
    w = 1024
    a = np.zeros(w)
    u = w / 10.0
    x = np.arange(w)
    for k in range(3):
        a += np.exp(-((x - (0.6 + k * 1.3) * u) / (0.18 * u)) ** 2)
    c0, c1 = 4.8 * u, 7.0 * u
    a += np.clip(np.minimum((x - c0) / (0.25 * u), (c1 - x) / (0.25 * u)), 0, 1)
    img = np.repeat((np.clip(a, 0, 1) * 255).astype(np.uint8)[None, :], 4, axis=0)
    save(Image.fromarray(img, 'L'), 'sigstrip')


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
    earth()
    stars()
    sig_monitor(False)
    sig_monitor(True)
    timeline3()
    compare()
    sigmap()
    source()
    symbol_screen()
    sig_strip()
    if not os.path.exists(os.path.join(OUT, 'portrait.png')):
        placeholder('portrait', 480, 600, '?')
    print('textures ->', OUT)


if __name__ == '__main__':
    main()
