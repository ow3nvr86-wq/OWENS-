"""Post-production: upscale, grade, transitions, animated captions, stat graphics, encode.

Reads the Blender frames (renders/frames/f_####.png, 540x960), the voiceover timeline and
build/events.json, draws every caption and graphic with Pillow at 1080x1920, and pipes the
result to ffmpeg together with audio/mix.wav.

Run:
  python scripts/post.py                      # full video -> renders/the_wave_of_molasses.mp4
  python scripts/post.py --stills 100,700     # write individual graded frames for checking
"""
import argparse
import json
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1920
FPS = 30
FONT = os.path.join(ROOT, 'assets', 'fonts', 'Anton-Regular.ttf')
SERIF = os.path.join(ROOT, 'assets', 'fonts', 'OldStandard-Bold.ttf')
AMBER = (244, 181, 74)
ICE = (150, 205, 255)
WHITE = (255, 255, 255)

TL = json.load(open(os.path.join(ROOT, 'build', 'timeline.json')))
EV = json.load(open(os.path.join(ROOT, 'build', 'events.json')))
SHOT = {s['name']: s for s in EV['shots']}
LINE = {l['id']: l for l in TL['lines']}
LAST = SHOT['end']['f1']

_fonts = {}


def font(size, serif=False):
    k = (size, serif)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(SERIF if serif else FONT, size)
    return _fonts[k]


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def ease_out_back(u):
    u = min(1.0, max(0.0, u))
    c = 1.7
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


# ---------------------------------------------------------------------------
# Word timing for captions
# ---------------------------------------------------------------------------
def build_words():
    words = []
    for ln in TL['lines']:
        toks = ln['caption'].split()
        weights = [len(t.strip('.,?!')) + 2 + (3 if t[-1] in '.,?!' else 0) for t in toks]
        total = sum(weights)
        t = ln['start']
        span = ln['end'] - ln['start']
        for tok, wgt in zip(toks, weights):
            d = span * wgt / total
            words.append(dict(text=tok, t0=t, t1=t + d, line=ln['id']))
            t += d
    # group into short chunks (max 3 words / 17 characters), never across lines
    chunks, cur = [], []
    for w in words:
        if cur and (cur[0]['line'] != w['line'] or len(cur) >= 3 or
                    sum(len(x['text']) + 1 for x in cur) + len(w['text']) > 17):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if w['text'][-1] in '.,?!':
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        t0 = c[0]['t0']
        t1 = c[-1]['t1']
        nxt = chunks[i + 1][0]['t0'] if i + 1 < len(chunks) else t1 + 1.0
        if nxt - t1 < 0.35:
            t1 = nxt
        else:
            t1 += 0.2
        out.append(dict(words=c, t0=t0, t1=t1))
    return words, out


WORDS, CHUNKS = build_words()


def word_time(line_id, contains):
    for w in WORDS:
        if w['line'] == line_id and contains.lower() in w['text'].lower():
            return w['t0']
    return LINE[line_id]['start']


def draw_text_fx(img, xy, text, size, fill, stroke=8, serif=False, anchor='mm', shadow=True, alpha=255):
    """Text with a black outline and a soft drop shadow."""
    f = font(size, serif)
    if shadow:
        sh = Image.new('L', img.size, 0)
        ImageDraw.Draw(sh).text((xy[0] + 6, xy[1] + 8), text, font=f, anchor=anchor, fill=int(160 * alpha / 255),
                                stroke_width=stroke + 2, stroke_fill=int(160 * alpha / 255))
        sh = sh.filter(ImageFilter.GaussianBlur(9))
        black = Image.new('RGBA', img.size, (0, 0, 0, 255))
        img.paste(black, (0, 0), sh)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=f, anchor=anchor, fill=fill + (alpha,), stroke_width=stroke,
                               stroke_fill=(10, 6, 3, alpha))
    img.alpha_composite(layer)


def draw_captions(img, t):
    for c in CHUNKS:
        if c['t0'] <= t < c['t1']:
            break
    else:
        return
    size = 104
    f = font(size)
    texts = [w['text'].upper() for w in c['words']]
    space = f.getlength(' ')
    widths = [f.getlength(x) for x in texts]
    total = sum(widths) + space * (len(texts) - 1)
    scale_in = ease_out_back((t - c['t0']) / 0.16)
    y = 1235
    x = W / 2 - total / 2
    # shadow pass for the whole chunk
    sh = Image.new('L', img.size, 0)
    d = ImageDraw.Draw(sh)
    xx = x
    for tx, wd in zip(texts, widths):
        d.text((xx + 7, y + 9), tx, font=f, anchor='lm', fill=170, stroke_width=10, stroke_fill=170)
        xx += wd + space
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    sh = sh.point(lambda v: int(v * min(1.0, scale_in * 1.3)))
    img.paste(Image.new('RGBA', img.size, (0, 0, 0, 255)), (0, 0), sh)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    xx = x
    for w, tx, wd in zip(c['words'], texts, widths):
        active = w['t0'] <= t < w['t1'] + 0.05
        spoken = t >= w['t0']
        col = AMBER if active else (WHITE if spoken else (225, 225, 225))
        sz = size
        if active:
            sz = int(size * (1.0 + 0.1 * (1 - ease((t - w['t0']) / 0.12))))
        fy = y + (1 - scale_in) * 40
        d.text((xx + wd / 2, fy), tx, font=font(sz), anchor='mm', fill=col + (int(255 * min(1, scale_in * 1.3)),),
               stroke_width=9, stroke_fill=(10, 6, 3, 255))
        xx += wd + space
    img.alpha_composite(layer)


# ---------------------------------------------------------------------------
# Stat graphics
# ---------------------------------------------------------------------------
def tag(img, xy, text, size=44, fg=(20, 14, 8), bg=AMBER, alpha=1.0, serif=False, pad=(22, 12)):
    if alpha <= 0:
        return
    f = font(size, serif)
    w = f.getlength(text)
    x, y = xy
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * alpha)
    d.rounded_rectangle([x - w / 2 - pad[0], y - size / 2 - pad[1], x + w / 2 + pad[0], y + size / 2 + pad[1]],
                        radius=8, fill=bg + (a,))
    d.text((x, y), text, font=f, anchor='mm', fill=fg + (a,))
    img.alpha_composite(layer)


def fade(t, t0, t1, fin=0.25, fout=0.25):
    return min(ease((t - t0) / fin), ease((t1 - t) / fout))


def stamp(img, center, text, t, t_on, angle=-9):
    if t < t_on:
        return
    u = ease_out_back((t - t_on) / 0.22)
    s = 2.2 - 1.2 * u
    f = font(int(78 * s))
    w = f.getlength(text)
    layer = Image.new('RGBA', (int(w + 120 * s), int(160 * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(235 * min(1, u))
    d.rectangle([10, 10, layer.width - 10, layer.height - 10], outline=(200, 30, 25, a), width=int(9 * s))
    d.text((layer.width / 2, layer.height / 2), text, font=f, anchor='mm', fill=(200, 30, 25, a))
    layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(layer, (int(center[0] - layer.width / 2), int(center[1] - layer.height / 2)))


def date_card(img, t):
    s = SHOT['aerial']
    a = fade(t, s['t0'], s['t1'] + 0.2, 0.3, 0.3)
    if a <= 0:
        return
    y = 330 + (1 - ease((t - s['t0']) / 0.4)) * -60
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    al = int(235 * a)
    d.rectangle([110, y - 120, W - 110, y + 120], fill=(236, 226, 205, al))
    d.line([140, y - 92, W - 140, y - 92], fill=(30, 22, 14, al), width=4)
    d.line([140, y + 92, W - 140, y + 92], fill=(30, 22, 14, al), width=4)
    d.text((W / 2, y - 30), 'JANUARY 15, 1919', font=font(76, True), anchor='mm', fill=(25, 18, 12, al))
    d.text((W / 2, y + 48), 'NORTH END  ·  BOSTON, MASS.', font=font(36, True), anchor='mm', fill=(60, 45, 30, al))
    img.alpha_composite(layer)


def gallons(img, t):
    s = SHOT['scale']
    a = fade(t, s['t0'] + 0.1, s['t1'], 0.25, 0.2)
    if a <= 0:
        return
    t_on = word_time('L03', '2.3')
    u = ease((t - s['t0'] - 0.5) / max(t_on + 0.6 - s['t0'] - 0.5, 0.5))
    n = int(2_300_000 * u)
    draw_text_fx(img, (W / 2, 330), f'{n:,}', 132, AMBER, stroke=8, alpha=int(255 * a))
    draw_text_fx(img, (W / 2, 440), 'GALLONS OF MOLASSES', 54, WHITE, stroke=6, alpha=int(255 * a))
    if t > t_on + 1.3:
        tag(img, (W / 2, 525), '≈ 13,000 TONS', 40, alpha=a * ease((t - t_on - 1.3) / 0.3))
    # 50 ft bracket on the tank, anchored to the 3D projection exported from Blender
    f = int(round(t * FPS)) + 1
    top = {a_[0]: a_ for a_ in EV['anchors']['tank_top']}.get(f)
    base = {a_[0]: a_ for a_ in EV['anchors']['tank_base']}.get(f)
    if top and base and t > s['t0'] + 0.8:
        b = a * ease((t - s['t0'] - 0.8) / 0.4)
        x = max(top[1], base[1]) * W + 42
        y0 = max(top[2] * H, 620)
        y1 = min(base[2] * H, 1650)
        layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        al = int(255 * b)
        for dx, col in ((3, (0, 0, 0, al)), (0, AMBER + (al,))):
            d.line([x + dx, y0 + dx, x + dx, y1 + dx], fill=col, width=6)
            d.line([x - 22 + dx, y0 + dx, x + 22 + dx, y0 + dx], fill=col, width=6)
            d.line([x - 22 + dx, y1 + dx, x + 22 + dx, y1 + dx], fill=col, width=6)
        img.alpha_composite(layer)
        draw_text_fx(img, (min(x + 95, W - 100), (y0 + y1) / 2), '50 FT', 64, AMBER, stroke=6, alpha=al)


def thermo_readout(img, t):
    s = SHOT['thermo']
    a = fade(t, s['t0'] + 0.15, s['t1'], 0.25, 0.15)
    if a <= 0:
        return
    t0, t1 = LINE['L07']['start'] + 0.3, LINE['L07']['end'] - 0.2
    u = ease((t - t0) / (t1 - t0))
    deg = 2 + 39 * u
    col = tuple(int(ICE[i] + (AMBER[i] - ICE[i]) * u) for i in range(3))
    draw_text_fx(img, (W / 2, 340), f'{deg:.0f}°F', 190, col, stroke=10, alpha=int(255 * a))
    lbl = 'BITTER COLD SNAP' if u < 0.5 else 'UNUSUALLY WARM'
    tag(img, (W / 2, 485), lbl, 40, alpha=a)


def clock_label(img, t):
    s = SHOT['rivets']
    a = fade(t, s['t0'] + 0.1, s['t1'], 0.2, 0.1)
    if a <= 0:
        return
    flick = 0.85 + 0.15 * math.sin(t * 40)
    draw_text_fx(img, (W / 2, 330), '12:40 PM', 150, WHITE, stroke=9, alpha=int(255 * a * flick))
    tag(img, (W / 2, 450), 'JAN 15, 1919', 38, alpha=a)


def race_tags(img, t):
    s = SHOT['race']
    a = fade(t, s['t0'], s['t1'], 0.2, 0.2)
    if a <= 0:
        return
    t25 = word_time('L10', '25')
    t35 = word_time('L10', '35')
    if t > t25 - 0.1:
        b = a * ease_out_back((t - t25 + 0.1) / 0.25)
        draw_text_fx(img, (W / 2, 330), 'UP TO 25 FT', 112, AMBER, stroke=8, alpha=int(255 * min(1, b)))
    if t > t35 - 0.1:
        b = a * ease_out_back((t - t35 + 0.1) / 0.25)
        draw_text_fx(img, (W / 2, 460), '≈ 35 MPH', 112, WHITE, stroke=8, alpha=int(255 * min(1, b)))


def viscosity_meter(img, t):
    s = SHOT['freeze']
    a = fade(t, s['t0'] + 0.3, s['t1'], 0.3, 0.2)
    if a <= 0:
        return
    t_on = word_time('L13', 'Scientists')
    u = ease((t - t_on) / 1.6)
    k = 1 + 3 * u
    x0, x1, y = 160, W - 160, 380
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    al = int(255 * a)
    d.rounded_rectangle([x0, y - 26, x1, y + 26], radius=26, fill=(0, 0, 0, int(150 * a)), outline=WHITE + (al,), width=4)
    fill_x = x0 + (x1 - x0) * (k / 4.0)
    col = tuple(int(AMBER[i] + (ICE[i] - AMBER[i]) * u) for i in range(3))
    d.rounded_rectangle([x0 + 6, y - 20, max(x0 + 46, fill_x - 6), y + 20], radius=20, fill=col + (al,))
    img.alpha_composite(layer)
    draw_text_fx(img, (W / 2, y - 95), 'THICKNESS (VISCOSITY)', 52, WHITE, stroke=6, alpha=al)
    draw_text_fx(img, (W / 2, y + 100), f'×{k:.1f}' + ('+' if u >= 1 else ''), 96, col, stroke=8, alpha=al)
    if t > t_on:
        tag(img, (W / 2, y + 190), 'SHARP, KENNEDY & RUBINSTEIN · APS 2016', 28, alpha=a * ease((t - t_on) / 0.4),
            fg=WHITE, bg=(25, 25, 30))


def toll(img, t):
    s = SHOT['stuck']
    t_on = s['t0'] + 1.6
    a = fade(t, t_on, s['t1'] + 0.1, 0.4, 0.15)
    if a > 0:
        draw_text_fx(img, (W / 2, 360), '21 KILLED', 120, WHITE, stroke=8, alpha=int(255 * a))
        draw_text_fx(img, (W / 2, 470), '≈150 INJURED', 64, (220, 220, 220), stroke=6, alpha=int(255 * a))


def year_tag(img, t, shot, text):
    s = SHOT[shot]
    a = fade(t, s['t0'] + 0.1, s['t1'], 0.2, 0.15)
    if a > 0:
        tag(img, (W / 2, 300), text, 58, fg=(25, 18, 12), bg=(236, 226, 205), alpha=a, serif=True, pad=(34, 16))


def end_card(img, t):
    s = SHOT['end']
    a = fade(t, s['t0'] + 0.15, s['t1'] + 1, 0.3, 0.3)
    if a <= 0:
        return
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    al = int(255 * a)
    rows = [('MOLASSES WAVE', 35, AMBER), ('FASTEST HUMAN SPRINT', 27.8, WHITE)]
    x0, x1 = 150, W - 150
    for i, (label, mph, col) in enumerate(rows):
        y = 300 + i * 175
        u = ease((t - s['t0'] - 0.3 - i * 0.35) / 0.9)
        d.text((x0, y - 48), label, font=font(46), anchor='lm', fill=WHITE + (al,), stroke_width=5, stroke_fill=(0, 0, 0, al))
        d.rounded_rectangle([x0, y, x1, y + 52], radius=26, fill=(0, 0, 0, int(140 * a)))
        bw = (x1 - x0) * (mph / 35.0) * u
        if bw > 30:
            d.rounded_rectangle([x0, y, x0 + bw, y + 52], radius=26, fill=col + (al,))
        d.text((x1, y - 48), f'≈ {mph:.0f} MPH' if i == 0 else '≈ 28 MPH', font=font(46), anchor='rm',
               fill=col + (al,), stroke_width=5, stroke_fill=(0, 0, 0, al))
    img.alpha_composite(layer)
    if t > s['t0'] + 1.8:
        tag(img, (W / 2, 690), 'USAIN BOLT\'S PEAK, 2009', 30, fg=WHITE, bg=(25, 25, 30),
            alpha=a * ease((t - s['t0'] - 1.8) / 0.3))


def overlays(img, t):
    s_hook = SHOT['hook']
    if t < s_hook['t1']:
        tag(img, (W / 2, 290), 'BOSTON · 1919', 46, alpha=fade(t, 0.15, s_hook['t1'], 0.3, 0.15), serif=True,
            fg=(25, 18, 12), bg=(236, 226, 205), pad=(30, 14))
    date_card(img, t)
    gallons(img, t)
    year_tag(img, t, 'cutaway', '1915')
    if SHOT['cutaway']['t0'] < t < SHOT['cutaway']['t1'] + 0.05:
        stamp(img, (W / 2, 520), 'WATER TEST: 6 INCHES', t, word_time('L05', 'skipped'))
    year_tag(img, t, 'paint', '1918')
    thermo_readout(img, t)
    clock_label(img, t)
    race_tags(img, t)
    viscosity_meter(img, t)
    toll(img, t)
    year_tag(img, t, 'decades', 'DECADES LATER')
    end_card(img, t)
    draw_captions(img, t)


# ---------------------------------------------------------------------------
# Frames, grading, transitions
# ---------------------------------------------------------------------------
_cache = {}


def load_frame(f):
    f = min(max(f, 1), LAST)
    if f in _cache:
        return _cache[f]
    p = os.path.join(ROOT, 'renders', 'frames', f'f_{f:04d}.png')
    if os.path.exists(p) and os.path.getsize(p) > 0:
        im = Image.open(p).convert('RGB').resize((W, H), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=2.0, percent=60, threshold=2))
        arr = np.asarray(im).astype(np.float32) / 255.0
    else:
        arr = np.zeros((H, W, 3), np.float32)
    if len(_cache) > 8:
        _cache.pop(next(iter(_cache)))
    _cache[f] = arr
    return arr


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIGNETTE = 1.0 - 0.32 * np.clip(((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H / 2) / (H * 0.6)) ** 2, 0, 1.5) ** 1.3
RNG = np.random.default_rng(4)


def cut_frames():
    return {s['name']: s['f0'] for s in EV['shots']}


CUT = cut_frames()


def shake_offset(f):
    for name, amp, dur in (('burst', 18, 20), ('house', 8, 10), ('el', 9, 10), ('end', 12, 12), ('hook', 6, 8)):
        d = f - CUT[name]
        if 0 <= d < dur:
            k = (1 - d / dur) * amp
            return int(k * math.sin(d * 2.7)), int(k * math.cos(d * 3.9))
    return 0, 0


def compose(f):
    t = (f - 1) / FPS
    arr = load_frame(f)
    # whip transitions on selected cuts: smear the frames either side of the cut
    for name in ('scale', 'thermo', 'rivets', 'race', 'house', 'el'):
        d = f - CUT[name]
        if -2 <= d <= 1:
            k = (3 - abs(d + 0.5)) * 14
            acc = np.zeros_like(arr)
            n = 7
            for i in range(n):
                acc += np.roll(arr, int((i - n // 2) * k), axis=1)
            arr = acc / n
    dx, dy = shake_offset(f)
    if dx or dy:
        arr = np.roll(np.roll(arr, dx, axis=1), dy, axis=0)
    # grade: gentle S-curve, warm highlights, cool lifted shadows
    x = np.clip(arr, 0, 1)
    x = x * x * (3 - 2 * x) * 0.35 + x * 0.65
    lum = x.mean(axis=2, keepdims=True)
    x = x + (lum - 0.5) * np.array([0.03, 0.0, -0.03], np.float32)
    x = x * 0.96 + np.array([0.012, 0.014, 0.022], np.float32)
    x *= VIGNETTE[..., None]
    # transitions: white flash on the burst, dip to black into 'decades', fade in/out
    d = f - CUT['burst']
    if 0 <= d < 6:
        x = x + (1 - x) * (1 - d / 6) ** 1.5
    d = f - CUT['decades']
    if -8 <= d < 8:
        x *= min(1.0, abs(d + 0.5) / 8)
    if f <= 4:
        x *= f / 4
    if f > LAST - 18:
        x *= max(0.0, (LAST - f) / 18)
    # film grain
    g = RNG.standard_normal((H // 2, W // 2)).astype(np.float32)
    g = np.repeat(np.repeat(g, 2, 0), 2, 1) * 0.018
    x = np.clip(x + g[..., None], 0, 1)
    img = Image.fromarray((x * 255).astype(np.uint8)).convert('RGBA')
    overlays(img, t)
    return img.convert('RGB')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stills', default=None)
    ap.add_argument('--out', default=os.path.join(ROOT, 'renders', 'the_wave_of_molasses.mp4'))
    args = ap.parse_args()
    if args.stills:
        os.makedirs(os.path.join(ROOT, 'build', 'post'), exist_ok=True)
        for tok in args.stills.split(','):
            f = int(tok)
            compose(f).save(os.path.join(ROOT, 'build', 'post', f'post_{f:04d}.png'))
        return
    missing = [f for f in range(1, LAST + 1) if not os.path.exists(os.path.join(ROOT, 'renders', 'frames', f'f_{f:04d}.png'))]
    if missing:
        print(f'warning: {len(missing)} frames missing (first {missing[:5]}) — they will be black')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-i', os.path.join(ROOT, 'audio', 'mix.wav'),
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-shortest', args.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(1, LAST + 1):
        p.stdin.write(compose(f).tobytes())
        if f % 150 == 0:
            print('frame', f, '/', LAST, flush=True)
    p.stdin.close()
    p.wait()
    print('wrote', args.out)


if __name__ == '__main__':
    main()
