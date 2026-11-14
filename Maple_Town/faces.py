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
    """Classic block-avatar faces: small dark eyes with a tiny glint, thin brows only where the mood needs them, and a
    simple line mouth. Flat and understated, like a printed decal."""
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
    c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    ex, ey = 82, 214
    eh = dict(smile=40, happy=30, calm=26, smirk=30, scared=46, angry=28)[expr]
    for sx in (-1, 1):
        x = 256 + sx * ex
        if expr == 'scared':
            ell(c, x, ey, 34, 44); c.set_source_rgb(1, 1, 1); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(7); c.stroke()
            c.arc(x, ey + 4, 14, 0, 2 * math.pi); c.fill()
        else:
            ell(c, x, ey, 21, eh); c.set_source_rgb(*INK); c.fill()
            c.set_source_rgb(1, 1, 1); ell(c, x + 6, ey - eh * 0.45, 6, 8); c.fill()
            c.set_source_rgba(col[0], col[1], col[2], 0.55); ell(c, x, ey + eh * 0.45, 12, eh * 0.3); c.fill()
        tilt = dict(smile=None, happy=None, calm=0.0, smirk=-0.16, scared=0.34, angry=-0.38)[expr]
        if tilt is not None:
            by = ey - eh - (34 if expr == 'scared' else 20)
            c.save(); c.translate(x, by); c.rotate(-tilt * sx)
            c.set_source_rgb(*INK); c.set_line_width(11); c.move_to(-34, 0); c.line_to(34, 0); c.stroke(); c.restore()
    c.set_source_rgb(*INK); c.set_line_width(11)
    my = 348
    if expr == 'smile':
        c.move_to(190, my); c.curve_to(222, my + 40, 290, my + 40, 322, my); c.stroke()
    elif expr == 'happy':
        c.move_to(182, my - 4); c.curve_to(214, my + 62, 298, my + 62, 330, my - 4); c.close_path()
        c.set_source_rgb(0.32, 0.08, 0.1); c.fill_preserve(); c.set_source_rgb(*INK); c.stroke()
        c.set_source_rgb(1, 1, 1); c.move_to(196, my + 2); c.line_to(316, my + 2); c.set_line_width(12); c.stroke()
    elif expr == 'calm':
        c.move_to(214, my + 12); c.line_to(298, my + 12); c.stroke()
    elif expr == 'smirk':
        c.move_to(206, my + 18); c.curve_to(250, my + 30, 300, my + 20, 326, my - 12); c.stroke()
    elif expr == 'scared':
        ell(c, 256, my + 22, 34, 40); c.set_source_rgb(0.32, 0.08, 0.1); c.fill_preserve(); c.set_source_rgb(*INK); c.set_line_width(8); c.stroke()
    else:
        c.move_to(196, my + 30); c.curve_to(226, my - 4, 286, my - 4, 316, my + 30); c.stroke()
    return s


if __name__ == '__main__':
    d = os.path.join(ROOT, 'assets', 'faces')
    os.makedirs(d, exist_ok=True)
    for e in ('smile', 'happy', 'calm', 'smirk', 'scared', 'angry'):
        for n, col in EYES.items():
            face(e, col).write_to_png(os.path.join(d, f'{e}_{n}.png'))
    print('faces written')
