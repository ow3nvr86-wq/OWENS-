"""Procedural document textures for the JFK assassination Short (PIL + numpy, code only).

Draws every paper prop and small graphic the 3D scene uses: the two 1963 front pages (generic, fictional
mastheads), case folders, a portrait-style card for Lee Harvey Oswald (a silhouette and verified facts,
no likeness), a reporter's notepad page, location "photographs" (drawn by code), timeline cards, a
diagram of Dealey Plaza, a TV news bulletin, the covers of the Warren Commission (1964) and House Select
Committee on Assassinations (1979) reports, an acoustic-analysis printout (illustrative), declassified
pages with redaction bars and release stamps, archive box labels, shop signs and flags. Writes PNGs to
build/tex/. animation.py runs this automatically when the folder is missing.

    $SHORTS_PY tools/textures.py

Accuracy notes (see sources.txt): every date, time and name on these props is a verified fact; the
documents, photographs and newspapers themselves are recreations, not copies of real records.
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
    # coarse dot screen
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


def bw_scene(kind, seed, w, h):
    """Simple grey-scale drawings of places (used for the halftones and 'photographs')."""
    rng = np.random.default_rng(seed)
    y = np.mgrid[0:h, 0:w][0].astype(float)
    sky = 150 + 60 * (1 - y / h)
    img = Image.fromarray(np.dstack([sky] * 3).astype(np.uint8)).convert('L').convert('RGB')
    d = ImageDraw.Draw(img)
    hz = h * 0.55
    if kind == 'depository':
        # a seven-storey brick warehouse on a corner, rows of windows, trees in front
        bx0, bx1, top = w * 0.18, w * 0.78, h * 0.12
        d.rectangle([bx0, top, bx1, hz + h * 0.25], fill=(92, 92, 92))
        d.rectangle([bx0 - 6, top - 10, bx1 + 6, top + 8], fill=(70, 70, 70))
        rows = 7
        for r in range(rows):
            yy = top + 22 + r * (hz + h * 0.25 - top - 30) / rows
            for c in range(9):
                xx = bx0 + 16 + c * (bx1 - bx0 - 30) / 9
                d.rectangle([xx, yy, xx + (bx1 - bx0) / 9 * 0.55, yy + (hz - top) / rows * 0.6], fill=(40, 40, 42))
        d.rectangle([0, hz + h * 0.25, w, h], fill=(120, 120, 120))
        for k in range(4):
            tx = w * (0.05 + 0.3 * k)
            d.ellipse([tx - 70, hz + h * 0.1, tx + 70, hz + h * 0.32], fill=(55, 58, 55))
    elif kind == 'plaza':
        d.rectangle([0, hz, w, h], fill=(150, 152, 148))
        d.polygon([(0, hz + 40), (w, hz - 10), (w, hz + 30), (0, hz + 90)], fill=(80, 80, 82))
        d.rectangle([w * 0.62, hz - 70, w, hz - 40], fill=(70, 70, 72))
        for k in range(5):
            d.rectangle([w * 0.62 + k * 60, hz - 40, w * 0.62 + k * 60 + 14, hz + 20], fill=(70, 70, 72))
        for k in range(6):
            tx = rng.uniform(0, w * 0.6)
            d.ellipse([tx - 50, hz - 80, tx + 50, hz + 10], fill=(70, 74, 70))
        d.rectangle([w * 0.05, h * 0.15, w * 0.32, hz - 30], fill=(95, 95, 95))
    elif kind == 'theatre':
        d.rectangle([0, hz + 60, w, h], fill=(120, 120, 120))
        d.rectangle([w * 0.15, h * 0.1, w * 0.85, hz + 60], fill=(100, 100, 102))
        d.rectangle([w * 0.1, hz - 40, w * 0.9, hz + 10], fill=(210, 210, 205))
        d.text((w / 2, hz - 15), 'THEATRE', font=F(BOLD, int(h * 0.09)), fill=(40, 40, 40), anchor='mm')
        d.rectangle([w * 0.4, hz + 10, w * 0.6, hz + 60], fill=(35, 35, 35))
    elif kind == 'motorcade':
        d.rectangle([0, hz, w, h], fill=(110, 110, 112))
        for k in range(7):
            x0 = k * w / 7
            d.rectangle([x0, h * 0.05 + rng.uniform(0, 60), x0 + w / 7 - 6, hz], fill=(int(80 + 25 * (k % 3)),) * 3)
        for k in range(60):
            px = rng.uniform(0, w)
            d.ellipse([px - 5, hz - 14, px + 5, hz - 2], fill=(50, 50, 50))
            d.rectangle([px - 6, hz - 3, px + 6, hz + 22], fill=(int(rng.uniform(40, 120)),) * 3)
        d.rounded_rectangle([w * 0.32, hz + 40, w * 0.68, hz + 90], 10, fill=(30, 30, 34))
        d.ellipse([w * 0.36, hz + 75, w * 0.42, hz + 100], fill=(15, 15, 15))
        d.ellipse([w * 0.58, hz + 75, w * 0.64, hz + 100], fill=(15, 15, 15))
    arr = np.array(img, float).mean(2)
    arr = np.array(Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.4)), float)
    arr += rng.normal(0, 8, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGB')


def photo_print(kind, seed, caption):
    w, h = 900, 700
    ph = bw_scene(kind, seed, w, h)
    a = np.array(ph, float)
    yy, xx = np.mgrid[0:h, 0:w]
    a *= (1 - 0.35 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2))[..., None]
    card = paper(w + 80, h + 200, seed + 5, tone=(236, 232, 222), age=0.3)
    card.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (40, 40))
    typed(ImageDraw.Draw(card), (50, h + 70), caption, 46, seed=seed)
    return card


# ----------------------------------------------------------------------------------------------
# newspapers (generic mastheads; recreations)
# ----------------------------------------------------------------------------------------------
def front_page(name, masthead, date, lines, sub, seed, extra=False, pic='motorcade', second=None):
    w, h = 1400, 1900
    img = paper(w, h, seed, tone=(216, 208, 186), age=0.55)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    top = 70
    if extra:
        d.rectangle([60, 40, w - 60, 150], fill=(150, 26, 24))
        d.text((w / 2, 95), 'E X T R A', font=F(BOLD, 86), fill=(236, 226, 206), anchor='mm')
        top = 170
    d.text((w / 2, top + 60), masthead, font=F(HEAD, 92), fill=(18, 18, 20), anchor='mm')
    d.line([(60, top + 130), (w - 60, top + 130)], fill=(30, 30, 30), width=4)
    d.text((70, top + 142), 'DALLAS, TEXAS', font=F(MONO, 30), fill=(40, 40, 40))
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
        d.text((1120, y + 10), second[0], font=F(BOLD, 64), fill=(18, 18, 20), anchor='ma')
        d.text((1120, y + 90), second[1], font=F(HEAD, 34), fill=(30, 30, 30), anchor='ma')
        lines_block(d, 900, y + 150, 420, 22, 19, rng)
    else:
        lines_block(d, 900, y, 420, 29, 19, rng)
    for col in range(4):
        lines_block(d, 80 + col * 315, y + 600, 290, int((h - y - 640) / 19), 19, rng)
    img.save(os.path.join(OUT, name + '.png'))


def tex_newspapers():
    front_page('paper_assassinated', 'THE MORNING EDITION', 'SATURDAY, NOVEMBER 23, 1963', ['PRESIDENT KENNEDY', 'ASSASSINATED'],
               'Shot in Dallas Motorcade;  Gov. Connally Wounded', 301, pic='motorcade',
               second=('JOHNSON SWORN IN', 'Oath Taken Aboard Plane'))
    front_page('paper_dead', 'THE EVENING EDITION', 'FRIDAY, NOVEMBER 22, 1963', ['THE PRESIDENT', 'IS DEAD'],
               'Kennedy Shot in Dallas;  Connally Wounded', 302, extra=True, pic='depository')
    front_page('paper_suspect', 'THE MORNING EDITION', 'SATURDAY, NOVEMBER 23, 1963', ['SUSPECT HELD'],
               'Ex-Marine, 24, Charged;  Denies Shooting', 303, pic='theatre')


# ----------------------------------------------------------------------------------------------
# the investigation room (recreations)
# ----------------------------------------------------------------------------------------------
def folder(name, lines, seed, tone=(196, 168, 112)):
    w, h = 1300, 900
    img = paper(w, h, seed, tone=tone, age=0.9)
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, w - 60, h - 60], outline=(90, 70, 40), width=4)
    lab = paper(900, 330, seed + 1, tone=(236, 230, 214), age=0.3)
    ld = ImageDraw.Draw(lab)
    for k, (txt, size) in enumerate(lines):
        typed(ld, (40, 30 + sum(s * 1.45 for _, s in lines[:k])), txt, size, seed=seed + k)
    img.paste(lab, (200, 220))
    img.save(os.path.join(OUT, name + '.png'))


def tex_folders():
    folder('folder_case', [('DALLAS POLICE DEPARTMENT', 46), ('HOMICIDE AND ROBBERY BUREAU', 40), ('', 20),
                           ('NOV. 22, 1963', 54), ('PRESIDENT JOHN F. KENNEDY', 46)], 401)
    folder('folder_evidence', [('EVIDENCE - DEALEY PLAZA', 46), ('TEXAS SCHOOL BOOK DEPOSITORY', 40), ('411 ELM STREET', 40),
                               ('', 20), ('NOVEMBER 22, 1963', 46)], 402, tone=(178, 160, 120))
    folder('folder_tippit', [('OFFICER J. D. TIPPIT', 52), ('10TH ST. & PATTON AVE.', 40), ('', 20), ('NOV. 22, 1963  1:15 P.M. (APPROX.)', 40)],
           403, tone=(190, 176, 140))


def tex_portrait():
    """Portrait-style card for Lee Harvey Oswald: a silhouette and verified facts only (no likeness)."""
    w, h = 1000, 1300
    img = paper(w, h, 410, tone=(232, 226, 210), age=0.5)
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, w - 40, h - 40], outline=(60, 60, 60), width=3)
    # neutral silhouette, framed like a portrait print
    px0, py0, px1, py1 = 210, 110, 790, 760
    yy, xx = np.mgrid[py0:py1, px0:px1]
    bg = 150 + 40 * ((yy - py0) / (py1 - py0))
    pic = np.dstack([bg] * 3)
    pim = Image.fromarray(pic.astype(np.uint8))
    pd = ImageDraw.Draw(pim)
    cw = px1 - px0
    pd.ellipse([cw * 0.33, 120, cw * 0.67, 430], fill=(46, 46, 48))
    pd.rectangle([cw * 0.43, 400, cw * 0.57, 480], fill=(46, 46, 48))
    pd.pieslice([cw * 0.05, 450, cw * 0.95, 900], 180, 360, fill=(46, 46, 48))
    pim = pim.filter(ImageFilter.GaussianBlur(2))
    img.paste(pim, (px0, py0))
    d.rectangle([px0, py0, px1, py1], outline=(30, 30, 30), width=4)
    d.text((w / 2, 830), 'LEE HARVEY OSWALD', font=F(BOLD, 92), fill=(22, 22, 24), anchor='mm')
    rows = ['AGE 24  -  FORMER U.S. MARINE', 'ORDER FILLER, TEXAS SCHOOL BOOK DEPOSITORY', 'ARRESTED NOV. 22, 1963, TEXAS THEATRE',
            'CHARGED: MURDER OF PRESIDENT KENNEDY', 'AND OF OFFICER J. D. TIPPIT']
    for k, r in enumerate(rows):
        typed(d, (80, 905 + k * 56), r, 33, seed=411 + k)
    stamp(img, (720, 1210), 'DENIED THE CHARGES', 44, 6, seed=3)
    d.text((w / 2, 1255), 'ILLUSTRATIVE CARD - NOT A PHOTOGRAPH', font=F(MONO, 22), fill=(90, 90, 90), anchor='mm')
    img.save(os.path.join(OUT, 'portrait.png'))


def tex_notepad():
    w, h = 800, 1100
    img = paper(w, h, 420, tone=(236, 232, 204), age=0.4, lines=True)
    d = ImageDraw.Draw(img)
    for k in range(10):
        d.ellipse([w / 2 - 330 + k * 72, 18, w / 2 - 312 + k * 72, 36], fill=(60, 60, 60))
    hand_text(img, (60, 150), 'FRI NOV 22 - DPD 3RD FLOOR', 46, 421, spacing=0.95)
    hand_text(img, (60, 250), 'OSWALD IN HALLWAY:', 50, 422)
    hand_text(img, (60, 360), '"I\'M JUST A PATSY!"', 64, 423, ink=(20, 20, 60))
    hand_text(img, (60, 480), 'DENIES SHOOTING', 46, 424)
    hand_text(img, (60, 580), 'CHARGED W/ TIPPIT', 46, 425)
    hand_text(img, (60, 680), 'MURDER - 7 PM', 46, 426)
    d.line([(60, 420), (690, 425)], fill=(150, 32, 30), width=4)
    img.save(os.path.join(OUT, 'notepad.png'))


def tex_photos():
    for k, (kind, cap) in enumerate((('depository', 'BOOK DEPOSITORY - ELM & HOUSTON'), ('plaza', 'DEALEY PLAZA - ELM ST.'),
                                     ('theatre', 'TEXAS THEATRE - JEFFERSON BLVD.'), ('motorcade', 'MAIN STREET - 12:20 P.M.'))):
        photo_print(kind, 430 + k, cap).save(os.path.join(OUT, f'photo_{k}.png'))


CARDS = [('12:30 PM', 'SHOTS IN', 'DEALEY PLAZA'), ('1:00 PM', 'PRESIDENT DIES', 'PARKLAND HOSP.'),
         ('~1:15 PM', 'OFFICER TIPPIT', 'KILLED, OAK CLIFF'), ('~1:50 PM', 'OSWALD ARRESTED', 'TEXAS THEATRE'),
         ('2:38 PM', 'JOHNSON SWORN IN', 'AIR FORCE ONE'), ('NOV 24', 'OSWALD SHOT', 'BY JACK RUBY'),
         ('SEPT 1964', 'WARREN REPORT', '"ACTED ALONE"')]


def tex_cards():
    for k, (a, b, c) in enumerate(CARDS):
        w, h = 1000, 600
        img = paper(w, h, 440 + k, tone=(240, 236, 222), age=0.35, lines=True)
        d = ImageDraw.Draw(img)
        d.line([(0, 95), (w, 95)], fill=(190, 60, 60), width=3)
        typed(d, (50, 25), a, 64, seed=k)
        hand_text(img, (60, 260), b, 74, 450 + k)
        hand_text(img, (60, 420), c, 66, 460 + k)
        img.save(os.path.join(OUT, f'card_{k}.png'))


def tex_map():
    """A diagram of Dealey Plaza with the motorcade route (positions match the 3D layout in animation.py)."""
    w, h = 1400, 1100
    img = paper(w, h, 470, tone=(232, 228, 214), age=0.5)
    d = ImageDraw.Draw(img)

    def P(x, y):                               # world metres -> map pixels (x -230..90, y -140..140)
        return (int((x + 230) / 320 * (w - 120) + 60), int((140 - y) / 280 * (h - 160) + 100))
    def bez(p0, p1, p2, n=30):
        return [P(*(((1 - t) ** 2) * np.array(p0) + 2 * (1 - t) * t * np.array(p1) + t * t * np.array(p2))) for t in np.linspace(0, 1, n)]
    road = (70, 70, 72)
    d.line(bez((0, 80), (-80, 66), (-178, 22)), fill=road, width=26)
    d.line([P(0, 0), P(-178, 0)], fill=road, width=26)
    d.line(bez((0, -80), (-80, -66), (-178, -22)), fill=road, width=26)
    d.line([P(0, 140), P(0, -140)], fill=road, width=26)
    d.line([P(0, 80), P(90, 80)], fill=road, width=26)
    d.line([P(0, 0), P(90, 0)], fill=road, width=26)
    d.line([P(0, -80), P(90, -80)], fill=road, width=26)
    d.rectangle([P(-192, 140), P(-180, -140)], fill=(120, 110, 100))
    d.rectangle([P(-40, 120), P(-8, 88)], fill=(150, 60, 40))
    d.text(P(-24, 128), 'BOOK DEPOSITORY', font=F(MONO, 26), fill=(30, 30, 30), anchor='mm')
    d.text(P(-186, 128), 'TRIPLE UNDERPASS', font=F(MONO, 24), fill=(30, 30, 30), anchor='lm')
    for nm, x, y in (('ELM ST', -95, 80), ('MAIN ST', -110, 6), ('COMMERCE ST', -110, -82), ('HOUSTON ST', 8, -120)):
        d.text(P(x, y), nm, font=F(MONO, 26), fill=(30, 30, 30), anchor='mm')
    route = [P(90, -2), P(4, -2), P(4, 76)] + bez((-4, 80), (-80, 64), (-170, 24))[1:]
    for a, b in zip(route[:-1], route[1:]):
        d.line([a, b], fill=(160, 30, 30), width=6)
    hand_text(img, (P(40, 30)[0], P(40, 30)[1]), 'ROUTE', 50, 471, ink=(160, 30, 30))
    d.text((w / 2, h - 40), 'DEALEY PLAZA  (DIAGRAM, NOT TO SCALE)', font=F(MONO, 30), fill=(40, 40, 40), anchor='mm')
    img.save(os.path.join(OUT, 'map_plaza.png'))


def tex_tv():
    w, h = 800, 600
    yy, xx = np.mgrid[0:h, 0:w]
    a = 70 + 30 * np.exp(-(((xx - w / 2) / (w * 0.5)) ** 2 + ((yy - h / 2) / (h * 0.5)) ** 2))
    a = a * (0.9 + 0.1 * (yy % 4 < 2))
    img = Image.fromarray(np.dstack([a * 0.95, a, a * 1.04]).clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.text((w / 2, h * 0.42), 'BULLETIN', font=F(BOLD, 150), fill=(235, 235, 235), anchor='mm')
    d.text((w / 2, h * 0.68), 'DALLAS, TEXAS', font=F(HEAD, 54), fill=(220, 220, 220), anchor='mm')
    img = img.filter(ImageFilter.GaussianBlur(1.6))
    img.save(os.path.join(OUT, 'tv_bulletin.png'))


# ----------------------------------------------------------------------------------------------
# the archive (report covers are the real titles; pages and stamps are illustrative)
# ----------------------------------------------------------------------------------------------
def cover(name, tone, lines, seed, gold=(196, 160, 82)):
    w, h = 1000, 1400
    rng = np.random.default_rng(seed)
    a = np.ones((h, w, 3)) * np.array(tone, float)
    a += rng.normal(0, 4, (h, w, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    a += (np.sin(xx * 1.9) * np.sin(yy * 2.3))[..., None] * 3            # cloth weave
    e = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]) / 60.0
    a -= (np.clip(1 - e, 0, 1) ** 2)[..., None] * 25
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, w - 60, h - 60], outline=gold, width=4)
    y = 260
    for txt, size in lines:
        if not txt:
            y += size
            continue
        f = F(HEAD, size)
        d.text((w / 2, y), txt, font=f, fill=gold, anchor='ma')
        y += int(size * 1.35)
    d.ellipse([w / 2 - 110, h - 420, w / 2 + 110, h - 200], outline=gold, width=6)
    d.ellipse([w / 2 - 80, h - 390, w / 2 + 80, h - 230], outline=gold, width=3)
    img.save(os.path.join(OUT, name + '.png'))


def tex_reports():
    cover('warren', (26, 34, 52), [('REPORT OF', 50), ("THE PRESIDENT'S COMMISSION", 52), ('ON THE', 46), ('ASSASSINATION', 70),
                                   ('OF', 46), ('PRESIDENT', 60), ('JOHN F. KENNEDY', 60), ('', 40), ('1964', 54)], 480)
    cover('hsca', (44, 52, 46), [('REPORT OF THE', 50), ('SELECT COMMITTEE', 64), ('ON ASSASSINATIONS', 64), ('', 30),
                                 ('U.S. HOUSE OF', 46), ('REPRESENTATIVES', 50), ('', 40), ('1979', 54)], 481)


def tex_acoustic():
    w, h = 1400, 1000
    img = paper(w, h, 490, tone=(234, 232, 222), age=0.3)
    d = ImageDraw.Draw(img)
    for x in range(80, w - 60, 40):
        d.line([(x, 160), (x, h - 120)], fill=(200, 210, 200), width=1)
    for y in range(160, h - 110, 40):
        d.line([(80, y), (w - 60, y)], fill=(200, 210, 200), width=1)
    rng = np.random.default_rng(491)
    for row in range(3):
        cy = 290 + row * 230
        pts = []
        for x in range(80, w - 60, 2):
            v = rng.normal(0, 8)
            for c in (0.22, 0.47, 0.71, 0.86):
                if row == 1 or (row != 1 and c < 0.5):
                    v += 75 * math.exp(-((x / w - c - 0.02 * row) / 0.006) ** 2) * math.sin(x * 0.9)
            pts.append((x, cy + v))
        d.line(pts, fill=(30, 30, 40), width=2)
    typed(d, (80, 50), 'ACOUSTIC ANALYSIS - POLICE RADIO RECORDING', 46, seed=492)
    d.text((80, h - 80), 'ILLUSTRATIVE RECREATION - NOT THE ORIGINAL DATA', font=F(MONO, 28), fill=(110, 110, 110))
    img.save(os.path.join(OUT, 'acoustic.png'))


def tex_docs():
    heads = ['MEMORANDUM', 'MEMORANDUM FOR THE RECORD', 'TELETYPE', 'REPORT', 'MEMORANDUM', 'SUMMARY']
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
        stamp(img, (w * 0.78, 210), 'SECRET', 40, -4, color=(150, 40, 36), seed=k)
        d.line([(w * 0.68, 192), (w * 0.88, 228)], fill=(30, 30, 30), width=5)          # struck out: declassified
        img.save(os.path.join(OUT, f'doc_{k}.png'))


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
    stamp_tex('stamp_2025', 'RELEASED 2025', (170, 30, 28))
    stamp_tex('stamp_2026', 'RELEASED 2026', (170, 30, 28))
    stamp_tex('stamp_declass', 'DECLASSIFIED', (30, 50, 120))


def tex_boxlabels():
    """8 archive-box end labels in one atlas (columns of 4 x 2)."""
    W, Hh = 1024, 512
    img = Image.new('RGB', (W, Hh), (180, 160, 120))
    d = ImageDraw.Draw(img)
    for k in range(8):
        x0, y0 = (k % 4) * 256, (k // 4) * 256
        d.rectangle([x0 + 40, y0 + 60, x0 + 216, y0 + 196], fill=(236, 230, 214))
        d.text((x0 + 128, y0 + 100), 'BOX', font=F(MONO, 30), fill=(40, 40, 40), anchor='mm')
        d.text((x0 + 128, y0 + 150), f'{312 + 37 * k:04d}', font=F(MONO, 40), fill=(40, 40, 40), anchor='mm')
        d.ellipse([x0 + 108, y0 + 214, x0 + 148, y0 + 236], fill=(90, 74, 50))
    img.save(os.path.join(OUT, 'boxlabels.png'))


# ----------------------------------------------------------------------------------------------
# Dallas 1963: shop signs, flags
# ----------------------------------------------------------------------------------------------
SIGNS = ['HOTEL', 'DRUGS', 'CAFE', 'SHOES', 'FURNITURE', 'JEWELERS', 'LOANS', 'RECORDS']


def tex_signs():
    """Blade / fascia signs (atlas of 8 rows); enamel letters on painted boards."""
    W, Hh = 1024, 1024
    img = Image.new('RGB', (W, Hh), (30, 30, 30))
    d = ImageDraw.Draw(img)
    cols = [((150, 30, 26), (240, 232, 210)), ((236, 226, 200), (150, 30, 26)), ((24, 48, 90), (240, 232, 210)),
            ((40, 40, 42), (230, 190, 90)), ((230, 190, 90), (30, 30, 30)), ((20, 70, 50), (240, 232, 210)),
            ((240, 232, 210), (24, 48, 90)), ((150, 30, 26), (230, 190, 90))]
    for k, word in enumerate(SIGNS):
        bg, fg = cols[k]
        y0 = k * 128
        d.rectangle([0, y0 + 4, W, y0 + 124], fill=bg)
        d.rectangle([10, y0 + 12, W - 10, y0 + 116], outline=fg, width=5)
        f = F(BOLD, 96)
        while f.getlength(word) > W - 80:
            f = F(BOLD, f.size - 4)
        d.text((W / 2, y0 + 64), word, font=f, fill=fg, anchor='mm')
    img.save(os.path.join(OUT, 'signs.png'))


def tex_flags():
    w, h = 760, 400
    img = Image.new('RGB', (w, h), (240, 238, 232))
    d = ImageDraw.Draw(img)
    for k in range(13):
        if k % 2 == 0:
            d.rectangle([0, k * h / 13, w, (k + 1) * h / 13], fill=(178, 34, 52))
    d.rectangle([0, 0, w * 0.4, h * 7 / 13], fill=(40, 52, 110))
    for r in range(9):
        for c in range(11 if r % 2 == 0 else 10):
            cx = (c + (0.5 if r % 2 else 0) + 0.5) * w * 0.4 / 11.5
            cy = (r + 0.6) * h * 7 / 13 / 9.6
            d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(240, 238, 232))
    img.save(os.path.join(OUT, 'flag_us.png'))
    img = Image.new('RGB', (w, h), (36, 46, 100))
    d = ImageDraw.Draw(img)
    d.ellipse([w / 2 - 110, h / 2 - 110, w / 2 + 110, h / 2 + 110], fill=(236, 232, 220))
    d.ellipse([w / 2 - 60, h / 2 - 60, w / 2 + 60, h / 2 + 60], fill=(200, 160, 80))
    img.save(os.path.join(OUT, 'flag_pres.png'))


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


def main():
    os.makedirs(OUT, exist_ok=True)
    for fn in (tex_newspapers, tex_folders, tex_portrait, tex_notepad, tex_photos, tex_cards, tex_map, tex_tv, tex_reports,
               tex_acoustic, tex_docs, tex_stamps, tex_boxlabels, tex_signs, tex_flags, tex_clock):
        fn()
    print('textures written to', OUT, len(os.listdir(OUT)))


if __name__ == '__main__':
    main()
