"""Paint the characters' faces as transparent PNGs (pycairo): big eyes with iris, pupil and highlights, lashes, brows,
blush and an expressive mouth. One PNG per (expression, eye colour).   $SHORTS_PY faces.py  -> assets/faces/*.png"""
import math
import os

import cairo

ROOT = os.path.dirname(os.path.abspath(__file__))
S = 512
INK = (0.09, 0.08, 0.1)
EYES = {'brown': (0.45, 0.27, 0.14), 'blue': (0.2, 0.5, 0.9), 'green': (0.25, 0.62, 0.35), 'red': (0.85, 0.15, 0.15), 'grey': (0.45, 0.5, 0.58)}


def ell(c, x, y, rx, ry):
    c.save(); c.translate(x, y); c.scale(rx, ry); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore()


def eye(c, x, y, col, w=62, h=78, look=(0, 0), lid=0.0, wide=False):
    c.save()
    ell(c, x, y, w, h); c.clip()
    c.set_source_rgb(1, 1, 1); c.paint()
    ir = 40 if not wide else 30
    ix, iy = x + look[0] * 14, y + 6 + look[1] * 12
    g = cairo.RadialGradient(ix, iy + 10, 4, ix, iy, ir)
    g.add_color_stop_rgb(0, min(1, col[0] + 0.35), min(1, col[1] + 0.35), min(1, col[2] + 0.35))
    g.add_color_stop_rgb(0.75, *col)
    g.add_color_stop_rgb(1, col[0] * 0.4, col[1] * 0.4, col[2] * 0.4)
    c.set_source(g); c.arc(ix, iy, ir, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*INK); c.arc(ix, iy, ir * 0.5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(1, 1, 1); c.arc(ix - ir * 0.36, iy - ir * 0.42, ir * 0.26, 0, 2 * math.pi); c.fill()
    c.arc(ix + ir * 0.34, iy + ir * 0.36, ir * 0.12, 0, 2 * math.pi); c.fill()
    if lid > 0:                                   # upper lid coming down (calm, smirk, angry)
        c.set_source_rgba(0.80, 0.62, 0.5, 1); c.rectangle(x - w, y - h, 2 * w, 2 * h * lid); c.fill()
        c.set_source_rgb(*INK); c.set_line_width(9); c.move_to(x - w, y - h + 2 * h * lid); c.line_to(x + w, y - h + 2 * h * lid); c.stroke()
    c.restore()
    c.set_source_rgb(*INK); c.set_line_width(9); ell(c, x, y, w, h); c.stroke()
    c.set_line_width(13); c.set_line_cap(cairo.LINE_CAP_ROUND)       # lash line
    c.save(); c.translate(x, y); c.scale(w, h); c.arc(0, 0, 1, math.pi * 1.08, math.pi * 1.92); c.restore(); c.stroke()


def brow(c, x, y, tilt, side, w=74):
    c.save(); c.translate(x, y); c.rotate(tilt * side)
    c.move_to(-w, 8); c.curve_to(-w / 2, -16, w / 2, -16, w, 4); c.line_to(w, 16); c.curve_to(w / 2, 2, -w / 2, 2, -w, 22); c.close_path()
    c.set_source_rgb(0.16, 0.11, 0.09); c.fill(); c.restore()


def face(expr, col):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
    c = cairo.Context(s)
    ex, ey = 104, 200
    for sx in (-1, 1):                                     # blush
        g = cairo.RadialGradient(256 + sx * 150, 318, 4, 256 + sx * 150, 318, 52)
        g.add_color_stop_rgba(0, 1, 0.45, 0.45, 0.45); g.add_color_stop_rgba(1, 1, 0.45, 0.45, 0)
        c.set_source(g); c.arc(256 + sx * 150, 318, 52, 0, 2 * math.pi); c.fill()
    P = dict(smile=dict(lid=0, tilt=0.05, by=0), happy=dict(lid=0, tilt=0.12, by=-6), calm=dict(lid=0.3, tilt=0.0, by=6),
             smirk=dict(lid=0.24, tilt=-0.18, by=4), scared=dict(lid=0, tilt=0.38, by=-22), angry=dict(lid=0.22, tilt=-0.42, by=14))[expr]
    for sx in (-1, 1):
        eye(c, 256 + sx * ex, ey, col, look=(0.25 if expr == 'smirk' else 0, 0), lid=P['lid'], wide=expr == 'scared',
            h=86 if expr == 'scared' else 78)
        brow(c, 256 + sx * ex, ey - 108 + P['by'], P['tilt'], -sx)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    my = 372
    if expr == 'happy':                                    # open grin: teeth and tongue
        c.move_to(166, my - 14); c.curve_to(200, my + 86, 312, my + 86, 346, my - 14); c.close_path()
        c.set_source_rgb(0.3, 0.07, 0.1); c.fill_preserve(); c.save(); c.clip()
        c.set_source_rgb(1, 1, 1); c.rectangle(150, my - 20, 220, 30); c.fill()
        c.set_source_rgb(0.95, 0.45, 0.5); ell(c, 256, my + 70, 56, 30); c.fill(); c.restore()
        c.move_to(166, my - 14); c.curve_to(200, my + 86, 312, my + 86, 346, my - 14); c.close_path()
        c.set_source_rgb(*INK); c.set_line_width(9); c.stroke()
    elif expr == 'smile':
        c.set_source_rgb(*INK); c.set_line_width(13); c.move_to(176, my); c.curve_to(214, my + 52, 298, my + 52, 336, my); c.stroke()
        c.set_line_width(8); c.move_to(166, my - 8); c.line_to(180, my + 4); c.move_to(346, my - 8); c.line_to(332, my + 4); c.stroke()
    elif expr == 'smirk':
        c.set_source_rgb(*INK); c.set_line_width(13); c.move_to(200, my + 22); c.curve_to(250, my + 40, 310, my + 26, 344, my - 16); c.stroke()
    elif expr == 'calm':
        c.set_source_rgb(*INK); c.set_line_width(12); c.move_to(210, my + 16); c.curve_to(240, my + 22, 272, my + 22, 302, my + 16); c.stroke()
    elif expr == 'scared':
        ell(c, 256, my + 26, 54, 62); c.set_source_rgb(0.3, 0.07, 0.1); c.fill_preserve(); c.save(); c.clip()
        c.set_source_rgb(1, 1, 1); c.rectangle(190, my - 44, 132, 26); c.fill()
        c.set_source_rgb(0.95, 0.45, 0.5); ell(c, 256, my + 84, 40, 26); c.fill(); c.restore()
        ell(c, 256, my + 26, 54, 62); c.set_source_rgb(*INK); c.set_line_width(9); c.stroke()
        c.set_source_rgba(0.5, 0.8, 1, 0.9); c.move_to(408, 150); c.curve_to(392, 180, 392, 196, 408, 200); c.curve_to(424, 196, 424, 180, 408, 150); c.fill()
    else:                                                  # angry: gritted teeth
        c.move_to(172, my - 6); c.curve_to(210, my - 22, 302, my - 22, 340, my - 6); c.line_to(332, my + 46)
        c.curve_to(296, my + 34, 216, my + 34, 180, my + 46); c.close_path()
        c.set_source_rgb(1, 1, 1); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(9); c.stroke()
        c.set_line_width(5)
        for k in range(1, 6):
            c.move_to(172 + k * 28, my - 16); c.line_to(174 + k * 27.5, my + 38)
        c.move_to(176, my + 16); c.line_to(336, my + 16); c.stroke()
    return s


if __name__ == '__main__':
    d = os.path.join(ROOT, 'assets', 'faces')
    os.makedirs(d, exist_ok=True)
    for e in ('smile', 'happy', 'calm', 'smirk', 'scared', 'angry'):
        for n, col in EYES.items():
            face(e, col).write_to_png(os.path.join(d, f'{e}_{n}.png'))
    print('faces written')
