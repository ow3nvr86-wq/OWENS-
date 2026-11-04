"""Procedural screen graphics and prop textures for "What If You Were Selected?" (Pillow + numpy, code only).

Everything here is invented and drawn with code: the competition's logo (VANTAGE), the government crest (Ministry of
Public Harmony), the giant-screen countdown and name cards, the news graphics, the arena map, the classified list,
monitor overlays, the console panel, city billboards (invented slogans), and placeholder images for the portrait and
the "live feeds" (animation.py later replaces those with renders of its own 3D sets). animation.py runs this
automatically when build/tex/ is missing.

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

NAME = 'ALEX VERRAN'
CITIZEN = '4471-09'
AMBER = (255, 184, 36)
CYAN = (90, 220, 255)
RED = (235, 40, 40)
NAVY = (8, 14, 28)

# The arena layout used by the map (metres, relative to the arena centre; +y is north). animation.py uses the same numbers.
ARENA_R = 1500.0
GATE = (0.0, -700.0)
RIVER = [(-1300, -330), (-900, -420), (-500, -330), (-150, -420), (150, -400), (500, -300), (850, -380), (1300, -260)]
TOWERS = [(-60, -470), (260, -560), (-420, -150), (380, 120), (-150, 330), (700, -620), (-760, -560)]
GATES = [(GATE[0] + 700 * math.sin(a), 700 * -math.cos(a)) for a in np.radians(np.arange(0, 360, 30))]


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


# --- the two emblems -----------------------------------------------------------------------------------------------
def vantage_mark(d, cx, cy, s, col=(240, 244, 250), dot=AMBER):
    """VANTAGE: two blades meeting in a V, with a ring and a dot (an eye) in the notch."""
    w = s * 0.16
    for sx in (-1, 1):
        d.polygon([(cx + sx * s * 0.62, cy - s * 0.55), (cx + sx * (s * 0.62 - w * 1.25), cy - s * 0.55),
                   (cx + sx * w * 0.15, cy + s * 0.55), (cx + sx * w * 0.95, cy + s * 0.55 - w * 0.6)], fill=col)
    d.ellipse([cx - s * 0.17, cy - s * 0.32, cx + s * 0.17, cy + 0.02 * s], outline=col, width=max(3, int(s * 0.035)))
    d.ellipse([cx - s * 0.06, cy - s * 0.21, cx + s * 0.06, cy - s * 0.09], fill=dot)


def crest(d, cx, cy, s, col=(214, 196, 150), bg=None):
    """Ministry of Public Harmony: an octagon, an eye of two arcs with a dot, and three bars."""
    pts = [(cx + s * math.cos(math.radians(22.5 + 45 * k)), cy + s * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    if bg:
        d.polygon(pts, fill=bg)
    d.polygon(pts, outline=col, width=max(3, int(s * 0.05)))
    pts2 = [(cx + s * 0.84 * math.cos(math.radians(22.5 + 45 * k)), cy + s * 0.84 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    d.polygon(pts2, outline=col, width=max(2, int(s * 0.02)))
    d.arc([cx - s * 0.55, cy - s * 0.62, cx + s * 0.55, cy + s * 0.28], 200, 340, fill=col, width=max(3, int(s * 0.05)))
    d.arc([cx - s * 0.55, cy - s * 0.48, cx + s * 0.55, cy + s * 0.42], 20, 160, fill=col, width=max(3, int(s * 0.05)))
    d.ellipse([cx - s * 0.11, cy - s * 0.21, cx + s * 0.11, cy + 0.01 * s], fill=col)
    for k in range(3):
        y = cy + s * (0.32 + 0.1 * k)
        hw = s * (0.42 - 0.1 * k)
        d.rectangle([cx - hw, y, cx + hw, y + s * 0.05], fill=col)


def logo():
    w, h = 2048, 1152
    im = radial(w, h, (24, 40, 78), (4, 7, 16), r=0.75)
    d = ImageDraw.Draw(im)
    vantage_mark(d, w / 2, h * 0.38, 430)
    f = F(BOLD, 190)
    txt = 'V A N T A G E'
    d.text((w / 2, h * 0.76), txt, font=f, fill=(240, 244, 250), anchor='mm')
    d.text((w / 2, h * 0.89), 'THE BIGGEST SHOW ON EARTH', font=F(BOLD, 52), fill=AMBER, anchor='mm')
    im = glow(im, 22, 0.6)
    save(scan(im, 0.08), 'logo')
    # vertical banner
    w, h = 600, 1800
    im = gradient(w, h, (12, 20, 40), (4, 6, 12))
    d = ImageDraw.Draw(im)
    vantage_mark(d, w / 2, h * 0.24, 260)
    for k, ch in enumerate('VANTAGE'):
        d.text((w / 2, h * 0.43 + k * 136), ch, font=F(BOLD, 126), fill=(236, 240, 246), anchor='mm')
    d.rectangle([40, 30, w - 40, 40], fill=AMBER)
    d.rectangle([40, h - 40, w - 40, h - 30], fill=AMBER)
    save(im, 'banner')


def crest_panel():
    w, h = 1024, 1024
    im = Image.new('RGB', (w, h), (10, 10, 12))
    d = ImageDraw.Draw(im)
    crest(d, w / 2, h * 0.42, 330, bg=(26, 24, 22))
    d.text((w / 2, h * 0.86), 'MINISTRY OF PUBLIC HARMONY', font=fit(SERIF, 'MINISTRY OF PUBLIC HARMONY', w * 0.9, 64),
           fill=(214, 196, 150), anchor='mm')
    d.text((w / 2, h * 0.94), 'OFFICE OF NATIONAL BROADCAST', font=F(BOLD, 34), fill=(150, 140, 110), anchor='mm')
    save(im, 'crest')


# --- the giant screen in the square ---------------------------------------------------------------------------------
def sq_count():
    w, h = 2048, 1152
    im = radial(w, h, (18, 46, 96), (3, 8, 22), cy=0.55, r=0.8)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 120], fill=(6, 12, 26))
    d.text((70, 60), 'SELECTION DAY', font=F(BOLD, 74), fill=(236, 240, 246), anchor='lm')
    d.text((w - 70, 60), 'CYCLE 12', font=F(BOLD, 74), fill=AMBER, anchor='rm')
    vantage_mark(d, w / 2, 260, 150)
    d.text((w / 2, 945), 'ONE CITIZEN WILL BE CHOSEN', font=F(BOLD, 86), fill=(200, 214, 236), anchor='mm')
    d.rectangle([0, h - 90, w, h], fill=(6, 12, 26))
    d.text((w / 2, h - 45), 'STAY CALM   -   STAY IN PLACE   -   THE SELECTION IS FINAL', font=F(BOLD, 44), fill=(130, 150, 180), anchor='mm')
    for x in range(0, w, 64):                 # faint grid
        d.line([(x, 120), (x, h - 90)], fill=(20, 40, 76), width=1)
    save(scan(glow(im, 14, 0.4), 0.1), 'sq_count')


def sq_name():
    w, h = 2048, 1152
    im = radial(w, h, (110, 24, 18), (14, 4, 4), cx=0.6, cy=0.5, r=0.9)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 150], fill=AMBER)
    d.text((w / 2, 77), 'S E L E C T E D', font=F(BOLD, 116), fill=(20, 10, 4), anchor='mm')
    # portrait frame (the portrait itself is a separate plane in the 3D scene) at x 120..700, y 230..1000
    d.rectangle([110, 220, 710, 1010], outline=(255, 255, 255), width=8)
    d.text((790, 420), NAME, font=fit(BOLD, NAME, 1180, 250), fill=(255, 255, 255), anchor='lm')
    d.text((800, 610), f'CITIZEN  {CITIZEN}', font=F(BOLD, 92), fill=AMBER, anchor='lm')
    d.text((800, 730), 'SECTOR 4   -   AGE 23', font=F(BOLD, 70), fill=(236, 200, 190), anchor='lm')
    d.text((800, 900), 'REPORT TO THE STAGE', font=F(BOLD, 70), fill=(255, 255, 255), anchor='lm')
    vantage_mark(d, w - 150, h - 130, 110)
    save(scan(glow(im, 16, 0.35), 0.1), 'sq_name')


def leak():
    """What the city sees when the hidden footage goes out: the classified list, broadcast in place of the show."""
    w, h = 2048, 1152
    im = Image.new('RGB', (w, h), (6, 6, 8))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 130], fill=RED)
    d.text((w / 2, 66), 'NOT FOR BROADCAST   -   LIVE FROM INSIDE THE ARENA', font=F(BOLD, 80), fill=(255, 255, 255), anchor='mm')
    lst = Image.open(os.path.join(OUT, 'list.png')).resize((1050, 1000))
    im.paste(lst, (60, 150))
    crest(d, 1500, 470, 250, bg=(20, 18, 16))
    d.text((1500, 840), 'THE SELECTION WAS DECIDED', font=F(BOLD, 74), fill=(255, 255, 255), anchor='mm')
    d.text((1500, 930), '21 DAYS IN ADVANCE', font=F(BOLD, 74), fill=AMBER, anchor='mm')
    save(scan(im, 0.12), 'leak')


# --- broadcast / news -----------------------------------------------------------------------------------------------
def broadcast():
    """TV frame: the portrait area on the left is left dark (a portrait plane sits in front in 3D)."""
    w, h = 1600, 900
    im = gradient(w, h, (20, 34, 70), (6, 10, 22))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 90], fill=(6, 12, 26))
    d.rectangle([40, 24, 170, 66], fill=RED)
    d.text((105, 45), 'LIVE', font=F(BOLD, 40), fill=(255, 255, 255), anchor='mm')
    d.text((200, 45), 'VANTAGE  -  SELECTION DAY', font=F(BOLD, 44), fill=(236, 240, 246), anchor='lm')
    d.rectangle([90, 150, 560, 700], fill=(2, 4, 8))
    d.text((620, 300), 'SELECTED', font=F(BOLD, 110), fill=AMBER, anchor='lm')
    d.text((620, 450), NAME, font=fit(BOLD, NAME, 900, 150), fill=(255, 255, 255), anchor='lm')
    d.text((620, 570), f'CITIZEN {CITIZEN}  -  SECTOR 4', font=F(BOLD, 56), fill=(170, 190, 220), anchor='lm')
    d.rectangle([0, h - 140, w, h - 60], fill=AMBER)
    d.text((40, h - 100), 'BREAKING:  THE NATION HAS ITS CONTESTANT', font=F(BOLD, 52), fill=(20, 10, 4), anchor='lm')
    d.rectangle([0, h - 60, w, h], fill=(6, 12, 26))
    d.text((40, h - 30), 'THE ARENA OPENS AT DAWN   -   12 CONTESTANTS   -   WATCH ON EVERY CHANNEL', font=F(BOLD, 34), fill=(200, 210, 230), anchor='lm')
    vantage_mark(d, w - 110, 160, 90)
    save(im, 'broadcast')


def news_wall():
    w, h = 1600, 900
    im = radial(w, h, (30, 70, 140), (6, 12, 30), cx=0.3, r=0.9)
    d = ImageDraw.Draw(im)
    for k in range(0, w, 50):
        d.line([(k, 0), (k - 400, h)], fill=(26, 56, 110), width=2)
    vantage_mark(d, w * 0.78, h * 0.4, 230)
    d.text((w * 0.78, h * 0.78), 'VANTAGE', font=F(BOLD, 120), fill=(240, 244, 250), anchor='mm')
    save(glow(im, 14, 0.4), 'news_wall')


def desk_front():
    w, h = 2048, 256
    im = gradient(w, h, (14, 28, 60), (4, 8, 18))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 10], fill=AMBER)
    d.text((w / 2, h / 2 + 6), 'NATIONAL NEWS   -   VANTAGE   -   NATIONAL NEWS', font=F(BOLD, 110), fill=(220, 230, 246), anchor='mm')
    save(im, 'desk_front')


# --- arena graphics -------------------------------------------------------------------------------------------------
def to_map(x, y, w, h):
    s = (min(w, h) * 0.46) / ARENA_R
    return w / 2 + x * s, h / 2 - y * s


def arena_map():
    w, h = 1600, 1600
    im = Image.new('RGB', (w, h), (4, 14, 12))
    a = np.asarray(im, float).copy()
    yy, xx = np.mgrid[0:h, 0:w]
    rx, ry = (xx - w / 2) / (w * 0.46) * ARENA_R, -(yy - h / 2) / (h * 0.46) * ARENA_R
    r = np.hypot(rx, ry)
    hgt = (400 * np.clip((r - 950) / 450, 0, 1) ** 1.5 + 14 * np.sin(rx / 173 + ry / 311) + 11 * np.sin(ry / 137 - rx / 263 + 1.0)
           + 8 * np.sin((rx + 2 * ry) / 97 + 2.0))
    band = (np.abs(np.mod(hgt, 25) - 12.5) > 11.4) & (r < ARENA_R)
    a[band] = (30, 120, 90)
    a[r > ARENA_R] = (2, 4, 6)
    im = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(im)
    for k in range(-15, 16):                               # grid
        x0, _ = to_map(k * 100, 0, w, h)
        d.line([(x0, 0), (x0, h)], fill=(10, 40, 34), width=1)
        _, y0 = to_map(0, k * 100, w, h)
        d.line([(0, y0), (w, y0)], fill=(10, 40, 34), width=1)
    d.line([to_map(x, y, w, h) for x, y in RIVER], fill=(60, 170, 255), width=14, joint='curve')
    cx, cy = to_map(0, 0, w, h)
    rr = ARENA_R * (min(w, h) * 0.46) / ARENA_R
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(90, 220, 200), width=6)
    for (x, y) in TOWERS:
        px, py = to_map(x, y, w, h)
        d.rectangle([px - 10, py - 10, px + 10, py + 10], outline=(90, 220, 200), width=4)
    for (x, y) in GATES:
        px, py = to_map(x, y, w, h)
        d.polygon([(px, py - 14), (px + 12, py + 10), (px - 12, py + 10)], outline=(200, 200, 200))
    d.rectangle([0, 0, w, 90], fill=(2, 8, 8))
    d.text((30, 45), 'VANTAGE  -  LIVE CONTESTANT POSITIONS', font=F(BOLD, 52), fill=(160, 240, 220), anchor='lm')
    d.text((w - 30, 45), '12 / 12', font=F(BOLD, 52), fill=AMBER, anchor='rm')
    save(scan(im, 0.12), 'map')


def countdown_frame():
    w, h = 2048, 860
    im = gradient(w, h, (6, 16, 30), (2, 4, 8))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 120], fill=(4, 10, 20))
    vantage_mark(d, 110, 60, 80)
    d.text((200, 62), 'VANTAGE  -  THE ARENA OPENS IN', font=F(BOLD, 70), fill=(236, 240, 246), anchor='lm')
    d.rectangle([0, h - 70, w, h], fill=AMBER)
    d.text((w / 2, h - 35), 'ALL CONTESTANTS  -  REMAIN IN YOUR GATE UNTIL ZERO', font=F(BOLD, 44), fill=(20, 10, 4), anchor='mm')
    save(im, 'countdown')


# --- the hidden control room ------------------------------------------------------------------------------------------
def classified_list():
    w, h = 1200, 1140
    im = Image.new('RGB', (w, h), (232, 230, 222))
    d = ImageDraw.Draw(im)
    crest(d, 90, 95, 60, col=(60, 50, 40))
    d.text((180, 62), 'MINISTRY OF PUBLIC HARMONY', font=F(SERIF, 44), fill=(30, 26, 22), anchor='lm')
    d.text((180, 118), 'OFFICE OF NATIONAL BROADCAST  -  VANTAGE CYCLE 12', font=F(BOLD, 30), fill=(70, 60, 50), anchor='lm')
    d.rectangle([40, 160, w - 40, 166], fill=(30, 26, 22))
    d.text((50, 200), 'PRE-APPROVED CONTESTANTS', font=F(BOLD, 62), fill=(20, 18, 16), anchor='lm')
    d.text((50, 260), 'APPROVED 21 DAYS BEFORE SELECTION DAY.  THE PUBLIC DRAW IS A FORMALITY.', font=F(BOLD, 28), fill=(140, 20, 20), anchor='lm')
    cols = [50, 130, 520, 720, 1000]
    for x, t in zip(cols, ('NO', 'NAME', 'CITIZEN', 'STORYLINE', 'STATUS')):
        d.text((x, 320), t, font=F(BOLD, 30), fill=(90, 80, 70), anchor='lm')
    rows = [('HALE, JONAH', '1180-33', 'THE FAVOURITE'), ('OKAFOR, MIA', '2209-14', 'THE VETERAN'),
            ('LINDQVIST, ERIK', '0937-52', 'THE RIVAL'), ('VERRAN, ALEX', CITIZEN, 'THE UNDERDOG'),
            ('SOTO, IRENE', '3341-07', 'THE STRATEGIST'), ('DUVAL, THEO', '5520-61', 'THE WILDCARD'),
            ('ARDEN, KIM', '4105-28', 'THE ROOKIE'), ('MARSH, PETRA', '6612-90', 'THE LONER'),
            ('YILMAZ, CAN', '7078-15', 'THE CHARMER'), ('NOVAK, LENA', '2851-44', 'THE SURVIVOR'),
            ('REYES, OMAR', '9930-02', 'THE COMEBACK'), ('BRANDT, SAL', '1764-38', 'THE OUTSIDER')]
    for k, (nm, cid, story) in enumerate(rows):
        y = 380 + k * 56
        hero = nm.startswith('VERRAN')
        if hero:
            d.rectangle([40, y - 26, w - 40, y + 26], fill=(255, 214, 120))
            d.rectangle([40, y - 26, w - 40, y + 26], outline=(200, 20, 20), width=5)
        fill = (20, 18, 16)
        d.text((cols[0], y), f'{k + 1:02d}', font=F(BOLD, 34), fill=fill, anchor='lm')
        d.text((cols[1], y), nm, font=F(BOLD, 34), fill=fill, anchor='lm')
        d.text((cols[2], y), cid, font=F(BOLD, 34), fill=fill, anchor='lm')
        d.text((cols[3], y), story, font=F(BOLD, 34), fill=fill, anchor='lm')
        d.text((cols[4], y), 'APPROVED', font=F(BOLD, 34), fill=(20, 110, 40), anchor='lm')
    # stamp
    st = Image.new('RGBA', (700, 170), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rectangle([6, 6, 694, 164], outline=(200, 20, 20, 230), width=10)
    sd.text((350, 88), 'CONFIDENTIAL', font=F(BOLD, 120), fill=(200, 20, 20, 230), anchor='mm')
    st = st.rotate(14, expand=True, resample=Image.BICUBIC)
    im.paste(st, (430, 1000 - st.size[1] // 2 + 20), st)
    save(im, 'list')


def list_screen():
    """The list as shown on a control-room monitor (dark UI around the document)."""
    w, h = 1600, 900
    im = Image.new('RGB', (w, h), (8, 12, 18))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 60], fill=(16, 24, 34))
    d.text((24, 30), 'ARCHIVE / CYCLE 12 / CASTING / pre_approved_final.doc', font=F(BOLD, 30), fill=(140, 170, 200), anchor='lm')
    d.text((w - 24, 30), 'RESTRICTED', font=F(BOLD, 30), fill=RED, anchor='rm')
    lst = Image.open(os.path.join(OUT, 'list.png')).resize((860, 817))
    im.paste(lst, (60, 72))
    d.text((960, 140), 'STORYLINE NOTES', font=F(BOLD, 44), fill=(220, 230, 240), anchor='lm')
    notes = ['04  VERRAN, A.', 'Ordinary. Sympathetic.', 'Audience score: 91 %', 'Keep in until the final week.',
             'Weather events: day 3, day 9', 'Route: north gate -> river', 'Outcome: SCRIPTED']
    for k, t in enumerate(notes):
        d.text((960, 230 + k * 70), t, font=F(BOLD, 40), fill=AMBER if k in (0, 6) else (200, 210, 220), anchor='lm')
    save(scan(im, 0.1), 'list_screen')


def hud(k, label, sector):
    w, h = 960, 540
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for (x0, y0, sx, sy) in ((24, 24, 1, 1), (w - 24, 24, -1, 1), (24, h - 24, 1, -1), (w - 24, h - 24, -1, -1)):
        d.line([(x0, y0), (x0 + 60 * sx, y0)], fill=(255, 255, 255, 200), width=4)
        d.line([(x0, y0), (x0, y0 + 60 * sy)], fill=(255, 255, 255, 200), width=4)
    d.ellipse([44, 44, 72, 72], fill=(235, 40, 40, 255))
    d.text((84, 58), f'CAM {label}', font=F(BOLD, 40), fill=(255, 255, 255, 235), anchor='lm')
    d.text((w - 44, 58), sector, font=F(BOLD, 34), fill=(255, 255, 255, 200), anchor='rm')
    d.text((44, h - 58), f'D1  {9 + k % 3:02d}:{(17 * k) % 60:02d}:{(31 * k) % 60:02d}', font=F(BOLD, 34), fill=(255, 255, 255, 200), anchor='lm')
    d.text((w - 44, h - 58), 'LIVE', font=F(BOLD, 34), fill=(235, 40, 40, 255), anchor='rm')
    save(im, f'hud{k}')


def console_panel():
    w, h = 2048, 512
    im = Image.new('RGB', (w, h), (16, 18, 22))
    d = ImageDraw.Draw(im)
    for k in range(18):                                     # channel strips
        x = 60 + k * 100
        d.rectangle([x, 60, x + 60, 470], outline=(50, 56, 64), width=3)
        d.rectangle([x + 26, 140, x + 34, 440], fill=(4, 4, 6))
        d.text((x + 30, 40), f'{k + 1:02d}', font=F(BOLD, 26), fill=(120, 130, 140), anchor='mm')
    x = 1880
    d.rectangle([x - 60, 40, x + 90, 490], fill=(40, 10, 10), outline=RED, width=5)
    d.rectangle([x + 10, 140, x + 22, 440], fill=(4, 4, 6))
    d.text((x + 16, 85), 'ALL', font=F(BOLD, 40), fill=(255, 220, 220), anchor='mm')
    d.text((x + 16, 470), 'CHANNELS', font=F(BOLD, 26), fill=(255, 220, 220), anchor='mm')
    save(im, 'console')


# --- the city ---------------------------------------------------------------------------------------------------------
def billboard(name, lines, bg, fg, accent, mark=None):
    w, h = 1024, 1536
    im = gradient(w, h, bg, tuple(int(c * 0.35) for c in bg))
    d = ImageDraw.Draw(im)
    y = h * 0.52
    for k, t in enumerate(lines):
        f = fit(BOLD, t, w * 0.84, 170)
        d.text((w / 2, y + k * 190), t, font=f, fill=fg if k < len(lines) - 1 else accent, anchor='mm')
    if mark == 'vantage':
        vantage_mark(d, w / 2, h * 0.24, 250, dot=accent)
    elif mark == 'crest':
        crest(d, w / 2, h * 0.26, 220, col=fg)
    save(glow(im, 18, 0.35), name)


def placeholder(name, w, h, txt):
    im = Image.new('RGB', (w, h), (18, 20, 24))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(len(name))
    a = (rng.random((h // 4, w // 4)) * 60).astype(np.uint8)
    im = Image.fromarray(np.kron(a, np.ones((4, 4), np.uint8))).convert('RGB')
    d = ImageDraw.Draw(im)
    d.text((w / 2, h / 2), txt, font=F(BOLD, h // 8), fill=(200, 200, 200), anchor='mm')
    save(im, name)


def main():
    logo()
    crest_panel()
    sq_count()
    sq_name()
    classified_list()
    list_screen()
    leak()
    broadcast()
    news_wall()
    desk_front()
    arena_map()
    countdown_frame()
    for k, (lab, sec) in enumerate((('A-01', 'SECTOR 1'), ('F-14', 'SECTOR 3'), ('R-07', 'RIVER'), ('G-04', 'GATE 4'),
                                   ('C-22', 'CITY SQUARE'), ('T-02', 'TOWER 2'), ('M-11', 'MINISTRY'), ('F-31', 'SECTOR 5'))):
        hud(k, lab, sec)
    console_panel()
    billboard('bb0', ['WATCH', 'VANTAGE', 'TONIGHT'], (20, 40, 90), (240, 244, 250), (255, 184, 36), 'vantage')
    billboard('bb1', ['STAY SAFE.', 'STAY SEEN.'], (90, 16, 16), (250, 236, 220), (255, 214, 120), 'crest')
    billboard('bb2', ['HARMONY', 'IS EVERYONE\'S', 'JOB'], (16, 60, 60), (230, 246, 240), (255, 184, 36), 'crest')
    billboard('bb3', ['ONE OF US', 'COULD BE', 'NEXT'], (40, 20, 70), (240, 234, 250), (255, 184, 36), 'vantage')
    for k in range(8):
        placeholder(f'feed{k}', 960, 540, 'NO SIGNAL')
    placeholder('portrait', 400, 500, '?')
    print('textures ->', OUT)


if __name__ == '__main__':
    main()
