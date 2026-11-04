"""Drawing functions for Chernobyl and Pripyat, 1986, as flat 2D ink illustration: panel apartment blocks,
the power plant (turbine hall, reactor blocks, the striped ventilation stack), the destroyed Reactor 4, the
New Safe Confinement arch, Soviet cars, a LAZ-type bus, a ZIL-type fire engine, street lamps, poplars, the
control room's panels, dials and chart recorders, the funfair's Ferris wheel and a playground.
s = world units per metre for buildings and vehicles (people are about 100 units per metre)."""
import math

import cairo
import numpy as np

from core import (PAL, ink_shape, ink_line, taper_stroke, hatch_lines, set_c, mix, shade_c, hash01, vnoise, ellipse_pts,
                  soft_glow, path_poly, clamp, smooth)
from world import fogc, R

CONCRETE = mix(PAL['plaster'], PAL['grey3'], 0.45)
GLASS = mix(PAL['charcoal'], PAL['grey2'], 0.35)
YELLOW = mix(PAL['candle'], PAL['parch3'], 0.35)


def text(ctx, x, y, s, size, txt, col, bold=True, align='center', alpha=1.0):
    ctx.save()
    ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    xb, yb, tw, th, _, _ = ctx.text_extents(txt)
    if align == 'center':
        x -= tw / 2 + xb
    ctx.move_to(x, y)
    set_c(ctx, col, alpha)
    ctx.show_text(txt)
    ctx.restore()


# ----------------------------------------------------------------------------------------------
# Pripyat
# ----------------------------------------------------------------------------------------------
def panel_block(ctx, x, gy, w_m, floors, s, seed, lit=0.0, decay=0.0, fog=0.0, fogcol=None, lw=1.2, laundry=0.0, night=0.0):
    """A prefabricated concrete apartment block (the type built across the USSR in the 1970s): panel seams,
    rows of windows and loggias, entrances with canopies. x = left edge."""
    rng = np.random.default_rng(seed)
    fh = 2.8 * s
    W_ = w_m * s
    H_ = floors * fh + 0.8 * s
    body = fogc(shade_c(CONCRETE, -0.08 * rng.random()), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    glass = fogc(GLASS, fog * 0.9, fogcol)
    R(ctx, x, gy - H_, x + W_, gy, body, lw, inkc, (shade_c(body, -0.18), W_ * 0.02), None, seed)
    ink_shape(ctx, np.array([[x - 0.3 * s, gy - H_ - 0.2 * s], [x + W_ + 0.3 * s, gy - H_ - 0.2 * s], [x + W_ + 0.3 * s, gy - H_ + 0.8 * s],
                             [x - 0.3 * s, gy - H_ + 0.8 * s]]), shade_c(body, -0.3), lw=lw, ink=inkc, smooth_path=False)
    bay = 3.0 * s
    nb = max(1, int(W_ / bay))
    bw = W_ / nb
    for f in range(floors):
        y0 = gy - (f + 1) * fh + 0.2 * s
        ink_line(ctx, np.array([[x, y0 - 0.2 * s], [x + W_, y0 - 0.2 * s]]), max(0.4, lw * 0.4), inkc, alpha=0.35)
        for b in range(nb):
            bx = x + b * bw
            loggia = (b % 3 == 1) and f > 0
            wx0, wx1 = bx + bw * 0.22, bx + bw * 0.78
            wy0, wy1 = y0 + fh * 0.22, y0 + fh * 0.72
            lit_here = night > 0 and rng.random() < lit
            broken = decay > 0 and rng.random() < decay * 0.6
            if lit_here:
                col = mix(PAL['candle'], PAL['candle2'], rng.random())
            elif broken:
                col = fogc(PAL['ink'], fog, fogcol)
            else:
                col = shade_c(glass, 0.06 * rng.random())
            R(ctx, wx0, wy0, wx1, wy1, col, max(0.4, lw * 0.6), inkc, None, None, seed + f * 50 + b, 0.2)
            if lit_here and s > 4:
                soft_glow(ctx, (wx0 + wx1) / 2, (wy0 + wy1) / 2, bw * 0.6, PAL['candle'], 0.18)
            if not lit_here and not broken and s > 6:
                ink_line(ctx, np.array([[(wx0 + wx1) / 2, wy0], [(wx0 + wx1) / 2, wy1]]), max(0.3, lw * 0.35), inkc, alpha=0.5)
                ink_line(ctx, np.array([[wx0 + 2, wy0 + 2], [wx0 + (wx1 - wx0) * 0.4, wy0 + (wy1 - wy0) * 0.4]]), max(0.3, lw * 0.4),
                         fogc(PAL['parch'], fog, fogcol), alpha=0.35)
            if loggia and not (decay > 0 and rng.random() < decay * 0.3):
                rail = fogc(mix(CONCRETE, PAL['parch2'], 0.3) if seed % 2 else mix(CONCRETE, PAL['green2'], 0.2), fog, fogcol)
                R(ctx, bx + bw * 0.06, y0 + fh * 0.6, bx + bw * 0.94, y0 + fh * 0.98, rail, max(0.4, lw * 0.7), inkc,
                  (shade_c(rail, -0.2), 2), None, seed + f * 7 + b, 0.2)
                if s > 6:
                    for k in range(1, 6):
                        xx = bx + bw * (0.06 + 0.88 * k / 6)
                        ink_line(ctx, np.array([[xx, y0 + fh * 0.62], [xx, y0 + fh * 0.96]]), max(0.3, lw * 0.3), inkc, alpha=0.35)
                if laundry > 0 and rng.random() < laundry:
                    for k in range(3):
                        lx = bx + bw * (0.2 + 0.22 * k)
                        c_ = [PAL['linen'], PAL['burg2'], PAL['green2'], PAL['parch']][int(rng.random() * 4)]
                        ink_shape(ctx, np.array([[lx, y0 + fh * 0.55], [lx + bw * 0.15, y0 + fh * 0.55], [lx + bw * 0.14, y0 + fh * 0.78],
                                                 [lx + bw * 0.01, y0 + fh * 0.76]]), fogc(c_, fog, fogcol), lw=max(0.3, lw * 0.4), ink=inkc,
                                  smooth_path=False)
        if f == 0:
            for b in range(0, nb, 4):
                ex = x + b * bw + bw * 0.5
                ink_shape(ctx, np.array([[ex - bw * 0.45, gy - fh * 0.85], [ex + bw * 0.45, gy - fh * 0.85], [ex + bw * 0.45, gy - fh * 0.78],
                                         [ex - bw * 0.45, gy - fh * 0.78]]), shade_c(body, -0.3), lw=lw * 0.7, ink=inkc, smooth_path=False)
    for b in range(1, nb):
        xx = x + b * bw
        ink_line(ctx, np.array([[xx, gy - H_ + 0.8 * s], [xx, gy]]), max(0.4, lw * 0.4), inkc, alpha=0.3)
    if decay > 0:
        for k in range(int(nb * decay * 2)):
            sx = x + rng.uniform(0, W_)
            sy = gy - H_ + rng.uniform(0, H_ * 0.5)
            taper_stroke(ctx, [(sx, sy), (sx + rng.uniform(-2, 2), sy + rng.uniform(H_ * 0.1, H_ * 0.4))], s * 0.6, 0.5,
                         fogc(mix(PAL['umber'], PAL['charcoal'], 0.4), fog, fogcol), seed + k, alpha=0.35)


def poplar(ctx, x, gy, h, seed, fog=0.0, fogcol=None, lw=1.1, leaf=1.0, col=None, t=0.0, sway=0.0):
    """A tall poplar or a broad lime, the street trees of Pripyat, in spring leaf (leaf 0 = bare)."""
    rng = np.random.default_rng(seed)
    trunk = fogc(mix(PAL['wood2'], PAL['grey2'], 0.3), fog, fogcol)
    green = fogc(col or mix(PAL['green2'], PAL['green'], 0.4 + 0.3 * rng.random()), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    tw = h * 0.035
    sw = sway * math.sin(t * 1.3 + seed) * h * 0.012
    ink_shape(ctx, np.array([[x - tw, gy], [x - tw * 0.5 + sw * 0.5, gy - h * 0.55], [x + sw, gy - h * 0.95], [x + tw * 0.5 + sw * 0.5, gy - h * 0.55],
                             [x + tw, gy]]), trunk, lw=lw, ink=inkc, seed=seed, shadow=(shade_c(trunk, -0.35), tw * 0.7), light=(-1, 0))
    for k in range(5):
        a = rng.uniform(-0.6, 0.6)
        b0 = gy - h * rng.uniform(0.35, 0.7)
        ink_line(ctx, np.array([[x + sw * 0.6, b0], [x + math.sin(a) * h * 0.22 + sw, b0 - h * 0.18]]), max(0.5, lw * 0.8), inkc)
    if leaf > 0.02:
        for j in range(5):
            cy = gy - h * (0.45 + 0.11 * j) + rng.uniform(-0.03, 0.03) * h
            cx = x + rng.uniform(-0.06, 0.06) * h + sw * (0.5 + 0.1 * j)
            rw = h * (0.2 - 0.025 * j) * (0.6 + 0.4 * leaf)
            rh = h * 0.12 * (0.6 + 0.4 * leaf)
            P = []
            m = 40
            for i in range(m):
                a = 2 * math.pi * i / m
                rr = 1 + 0.15 * vnoise(i * 0.6 + seed * 3 + j * 5, 9) + 0.06 * abs(math.sin(a * 8 + j))
                P.append([cx + math.cos(a) * rw * rr, cy + math.sin(a) * rh * rr])
            ink_shape(ctx, np.array(P), (*green[:3], 0.5 + 0.5 * leaf), lw=lw, ink=inkc, seed=seed * 5 + j, line_alpha=0.4 + 0.6 * leaf,
                      shadow=(shade_c(green, -0.35), rh * 0.4), hatch=(max(2.0, rh * 0.14), 25, max(0.4, lw * 0.4), 0.35), light=(-0.6, -1))


def street_lamp(ctx, x, gy, h, seed=0, on=0.0, lw=1.2, fog=0.0, fogcol=None):
    c = fogc(mix(PAL['grey'], CONCRETE, 0.4), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    ink_shape(ctx, np.array([[x - h * 0.02, gy], [x - h * 0.012, gy - h], [x + h * 0.012, gy - h], [x + h * 0.02, gy]]), c, lw=lw, ink=inkc, smooth_path=False)
    ink_line(ctx, np.array([[x, gy - h], [x + h * 0.12, gy - h * 1.06], [x + h * 0.22, gy - h * 1.02]]), max(1.0, h * 0.018), inkc)
    ink_shape(ctx, ellipse_pts(x + h * 0.22, gy - h * 1.0, h * 0.05, h * 0.02, 12), mix(PAL['grey3'], PAL['candle2'], on), lw=lw * 0.7, ink=inkc)
    if on > 0:
        soft_glow(ctx, x + h * 0.22, gy - h * 0.98, h * 0.35, PAL['candle'], 0.3 * on)


def road(ctx, x0, x1, y_curb, y_far, s, col=None, lw=1.2, lines=True, cracks=0.0, seed=0):
    """Asphalt with a centre line, the kerb and the pavement."""
    asph = col or mix(PAL['charcoal2'], PAL['grey2'], 0.45)
    ink_shape(ctx, np.array([[x0, y_far], [x1, y_far], [x1, y_curb], [x0, y_curb]]), asph, lw=0, smooth_path=False)
    if lines:
        ym = (y_far + y_curb) / 2
        k = x0 - (x0 % (6 * s))
        while k < x1:
            ink_shape(ctx, np.array([[k, ym - 0.08 * s], [k + 3 * s, ym - 0.08 * s], [k + 3 * s, ym + 0.08 * s], [k, ym + 0.08 * s]]),
                      mix(PAL['linen'], asph, 0.35), lw=0, smooth_path=False)
            k += 6 * s
    rng = np.random.default_rng(seed)
    for i in range(int((x1 - x0) / (2 * s) * (0.3 + cracks * 2))):
        x = rng.uniform(x0, x1)
        y = rng.uniform(y_far, y_curb)
        ink_line(ctx, np.array([[x, y], [x + rng.uniform(-1, 1) * s, y + rng.uniform(-0.2, 0.2) * s], [x + rng.uniform(-2, 2) * s, y]]),
                 max(0.4, lw * 0.5), PAL['ink'], alpha=0.25 + 0.3 * cracks)
    ink_shape(ctx, np.array([[x0, y_curb], [x1, y_curb], [x1, y_curb + 0.25 * s], [x0, y_curb + 0.25 * s]]), CONCRETE, lw=lw, smooth_path=False)


# ----------------------------------------------------------------------------------------------
# Vehicles (side elevation, facing +x; flip with face=-1). (x, gy) = centre of the wheelbase on the ground.
# ----------------------------------------------------------------------------------------------
def _wheel(ctx, x, y, r, t, speed, lw, inkc):
    ink_shape(ctx, ellipse_pts(x, y, r, r, 18), PAL['ink'], lw=lw, ink=inkc)
    ink_shape(ctx, ellipse_pts(x, y, r * 0.55, r * 0.55, 14), PAL['grey'], lw=lw * 0.6, ink=inkc)
    a = -t * speed / max(r, 1e-3)
    for k in range(3):
        b = a + k * 2 * math.pi / 3
        ink_line(ctx, np.array([[x, y], [x + math.cos(b) * r * 0.5, y + math.sin(b) * r * 0.5]]), max(0.4, lw * 0.6), inkc)


def car(ctx, x, gy, s, t, col, speed=0.0, face=1, lw=1.2, lights=0.0, seed=0, fog=0.0, fogcol=None):
    """A boxy 1970s Soviet saloon (in the manner of the VAZ-2101)."""
    ctx.save()
    ctx.translate(x, gy)
    ctx.scale(face, 1)
    col = fogc(col, fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    L = 4.1 * s
    body = [[-L / 2, -0.35 * s], [-L / 2, -0.95 * s], [-L * 0.28, -1.0 * s], [-L * 0.18, -1.42 * s], [L * 0.18, -1.42 * s], [L * 0.28, -1.0 * s],
            [L / 2, -0.92 * s], [L / 2, -0.35 * s]]
    ink_shape(ctx, np.array(body), col, lw=lw, ink=inkc, smooth_path=False, shadow=(shade_c(col, -0.3), 0.15 * s), light=(0, -1))
    for (a, b) in ((-0.25, -0.02), (0.02, 0.25)):
        ink_shape(ctx, np.array([[L * a + 0.05 * s, -1.0 * s], [L * a + 0.1 * s, -1.34 * s], [L * b - 0.08 * s, -1.34 * s], [L * b - 0.02 * s, -1.0 * s]]),
                  fogc(GLASS, fog, fogcol), lw=lw * 0.7, ink=inkc, smooth_path=False)
    ink_line(ctx, np.array([[-L / 2, -0.62 * s], [L / 2, -0.62 * s]]), max(0.4, lw * 0.6), fogc(PAL['grey3'], fog, fogcol))
    ink_shape(ctx, ellipse_pts(L / 2 - 0.1 * s, -0.72 * s, 0.1 * s, 0.08 * s, 8), mix(PAL['linen'], PAL['candle2'], lights), lw=lw * 0.5, ink=inkc)
    if lights > 0:
        soft_glow(ctx, L / 2 + 0.6 * s, -0.7 * s, 1.6 * s, PAL['candle2'], 0.35 * lights)
    for wx in (-L * 0.32, L * 0.32):
        _wheel(ctx, wx, -0.32 * s, 0.32 * s, t, speed, lw, inkc)
    ctx.restore()


def bus(ctx, x, gy, s, t, speed=0.0, face=1, lw=1.3, seed=0, livery=None, lights=0.0, faces=None, fog=0.0, fogcol=None):
    """A city bus in the manner of the LAZ-695: a rounded body, a long row of windows, a two-tone livery.
    faces: optional list of passenger heads shown in the windows."""
    ctx.save()
    ctx.translate(x, gy)
    ctx.scale(face, 1)
    top_c, low_c = livery or (mix(PAL['linen2'], PAL['parch2'], 0.4), mix(PAL['burg2'], PAL['candle'], 0.25))
    top_c, low_c = fogc(top_c, fog, fogcol), fogc(low_c, fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    L = 9.2 * s
    Hh = 3.0 * s
    body = [[-L / 2, -0.5 * s], [-L / 2, -Hh + 0.5 * s], [-L / 2 + 0.6 * s, -Hh], [L / 2 - 1.0 * s, -Hh], [L / 2 - 0.1 * s, -Hh + 0.7 * s],
            [L / 2, -1.2 * s], [L / 2, -0.5 * s]]
    ink_shape(ctx, np.array(body), top_c, lw=lw, ink=inkc, smooth_path=False, shadow=(shade_c(top_c, -0.25), 0.3 * s), light=(0, -1))
    ink_shape(ctx, np.array([[-L / 2, -0.5 * s], [-L / 2, -1.3 * s], [L / 2, -1.3 * s], [L / 2, -0.5 * s]]), low_c, lw=lw, ink=inkc, smooth_path=False)
    n = 6
    for k in range(n):
        wx0 = -L / 2 + 0.5 * s + k * (L - 2.2 * s) / n
        wx1 = wx0 + (L - 2.2 * s) / n - 0.15 * s
        ink_shape(ctx, np.array([[wx0, -1.5 * s], [wx0, -Hh + 0.45 * s], [wx1, -Hh + 0.45 * s], [wx1, -1.5 * s]]),
                  mix(fogc(GLASS, fog, fogcol), PAL['candle'], 0.4 * lights), lw=lw * 0.7, ink=inkc, smooth_path=False)
        if faces and k < len(faces) and faces[k]:
            hc = faces[k]
            ink_shape(ctx, ellipse_pts((wx0 + wx1) / 2, -2.05 * s, 0.22 * s, 0.27 * s, 12), fogc(hc[0], fog, fogcol), lw=lw * 0.5, ink=inkc)
            ink_shape(ctx, ellipse_pts((wx0 + wx1) / 2, -2.25 * s, 0.24 * s, 0.14 * s, 10), fogc(hc[1], fog, fogcol), lw=lw * 0.4, ink=inkc)
    # front door and windscreen
    ink_shape(ctx, np.array([[L / 2 - 1.55 * s, -0.55 * s], [L / 2 - 1.55 * s, -Hh + 0.45 * s], [L / 2 - 0.75 * s, -Hh + 0.45 * s], [L / 2 - 0.75 * s, -0.55 * s]]),
              mix(fogc(GLASS, fog, fogcol), top_c, 0.3), lw=lw * 0.7, ink=inkc, smooth_path=False)
    ink_shape(ctx, np.array([[L / 2 - 0.65 * s, -1.5 * s], [L / 2 - 0.62 * s, -Hh + 0.6 * s], [L / 2 - 0.18 * s, -Hh + 0.9 * s], [L / 2 - 0.05 * s, -1.5 * s]]),
              fogc(GLASS, fog, fogcol), lw=lw * 0.7, ink=inkc, smooth_path=False)
    ink_shape(ctx, ellipse_pts(L / 2 - 0.15 * s, -0.85 * s, 0.14 * s, 0.11 * s, 8), mix(PAL['linen'], PAL['candle2'], lights), lw=lw * 0.5, ink=inkc)
    if lights > 0:
        soft_glow(ctx, L / 2 + 0.8 * s, -0.85 * s, 2.0 * s, PAL['candle2'], 0.35 * lights)
    for wx in (-L * 0.3, L * 0.3):
        _wheel(ctx, wx, -0.48 * s, 0.48 * s, t, speed, lw, inkc)
    ctx.restore()


def fire_engine(ctx, x, gy, s, t, speed=0.0, face=1, lw=1.3, seed=0, beacon=1.0, lights=0.0, fog=0.0, fogcol=None):
    """A 1970s-80s Soviet fire engine in the manner of a ZIL-130 tanker: red cab and body, a white stripe,
    a ladder on top and a blue flashing beacon."""
    ctx.save()
    ctx.translate(x, gy)
    ctx.scale(face, 1)
    red = fogc(mix(PAL['burg2'], PAL['candle'], 0.12), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    L = 7.6 * s
    ink_shape(ctx, np.array([[-L / 2, -0.7 * s], [-L / 2, -2.7 * s], [L * 0.18, -2.7 * s], [L * 0.18, -0.7 * s]]), red, lw=lw, ink=inkc,
              smooth_path=False, shadow=(shade_c(red, -0.3), 0.3 * s), light=(0, -1))
    for k in range(4):
        xx = -L / 2 + 0.3 * s + k * 1.15 * s
        ink_shape(ctx, np.array([[xx, -0.9 * s], [xx + 0.95 * s, -0.9 * s], [xx + 0.95 * s, -2.4 * s], [xx, -2.4 * s]]), shade_c(red, -0.15),
                  lw=lw * 0.6, ink=inkc, smooth_path=False)
    ink_line(ctx, np.array([[-L / 2, -1.6 * s], [L / 2, -1.6 * s]]), 0.16 * s, fogc(PAL['linen'], fog, fogcol))
    cab = [[L * 0.18, -0.7 * s], [L * 0.18, -2.8 * s], [L * 0.34, -2.85 * s], [L * 0.42, -1.85 * s], [L / 2, -1.6 * s], [L / 2, -0.7 * s]]
    ink_shape(ctx, np.array(cab), red, lw=lw, ink=inkc, smooth_path=False, shadow=(shade_c(red, -0.3), 0.3 * s), light=(0, -1))
    ink_shape(ctx, np.array([[L * 0.22, -1.95 * s], [L * 0.22, -2.6 * s], [L * 0.33, -2.62 * s], [L * 0.39, -1.95 * s]]), fogc(GLASS, fog, fogcol),
              lw=lw * 0.7, ink=inkc, smooth_path=False)
    # ladder on the roof
    ink_line(ctx, np.array([[-L / 2 - 0.4 * s, -2.95 * s], [L * 0.3, -2.95 * s]]), max(0.8, 0.08 * s), fogc(PAL['grey3'], fog, fogcol))
    ink_line(ctx, np.array([[-L / 2 - 0.4 * s, -3.2 * s], [L * 0.3, -3.2 * s]]), max(0.8, 0.08 * s), fogc(PAL['grey3'], fog, fogcol))
    for k in range(12):
        xx = -L / 2 - 0.3 * s + k * 0.6 * s
        ink_line(ctx, np.array([[xx, -2.95 * s], [xx, -3.2 * s]]), max(0.5, 0.05 * s), fogc(PAL['grey3'], fog, fogcol))
    # beacon
    ph = (t * 2.2 + seed * 0.37) % 1.0
    on = beacon * (1.0 if ph < 0.25 or 0.5 < ph < 0.75 else 0.15)
    bc = mix(PAL['grey3'], (0.45, 0.62, 0.95, 1.0), on)
    ink_shape(ctx, ellipse_pts(L * 0.3, -2.98 * s, 0.22 * s, 0.18 * s, 10), bc, lw=lw * 0.6, ink=inkc)
    if on > 0.5:
        soft_glow(ctx, L * 0.3, -2.98 * s, 3.2 * s, (0.45, 0.6, 0.95, 1.0), 0.45 * on)
    ink_shape(ctx, ellipse_pts(L / 2 - 0.12 * s, -1.05 * s, 0.14 * s, 0.12 * s, 8), mix(PAL['linen'], PAL['candle2'], lights), lw=lw * 0.5, ink=inkc)
    if lights > 0:
        soft_glow(ctx, L / 2 + 1.2 * s, -1.0 * s, 3.0 * s, PAL['candle2'], 0.35 * lights)
    for wx in (-L * 0.3, -L * 0.12, L * 0.36):
        _wheel(ctx, wx, -0.55 * s, 0.55 * s, t, speed, lw, inkc)
    ctx.restore()


# ----------------------------------------------------------------------------------------------
# The power plant
# ----------------------------------------------------------------------------------------------
def stack(ctx, x, gy, s, t, lw=1.2, lights=0.0, fog=0.0, fogcol=None):
    """The ventilation stack between Units 3 and 4: a tall tube, banded near the top, braced by a steel
    lattice tower, with red aviation lights."""
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    Hs = 150 * s
    wb, wt = 7.0 * s, 4.2 * s
    white = fogc(mix(CONCRETE, PAL['linen'], 0.3), fog, fogcol)
    red = fogc(mix(PAL['burg2'], PAL['candle'], 0.15), fog, fogcol)
    ink_shape(ctx, np.array([[x - wb, gy], [x - wt, gy - Hs], [x + wt, gy - Hs], [x + wb, gy]]), white, lw=lw, ink=inkc, smooth_path=False,
              shadow=(shade_c(white, -0.25), wb * 0.4), light=(-1, 0))
    for k, (a, b) in enumerate(((0.9, 0.94), (0.82, 0.86), (0.74, 0.78))):
        ya, yb = gy - Hs * b, gy - Hs * a
        wa = wb + (wt - wb) * b
        wb_ = wb + (wt - wb) * a
        ink_shape(ctx, np.array([[x - wb_, yb], [x - wa, ya], [x + wa, ya], [x + wb_, yb]]), red, lw=lw * 0.6, ink=inkc, smooth_path=False)
    lat = fogc(PAL['grey2'], fog, fogcol)
    for side in (-1, 1):
        ink_line(ctx, np.array([[x + side * 13 * s, gy], [x + side * 6.5 * s, gy - Hs * 0.86]]), max(0.6, lw * 0.8), lat)
    for k in range(14):
        y0 = gy - Hs * 0.86 * k / 14
        y1 = gy - Hs * 0.86 * (k + 1) / 14
        w0 = 13 * s + (6.5 - 13) * s * k / 14
        w1 = 13 * s + (6.5 - 13) * s * (k + 1) / 14
        ink_line(ctx, np.array([[x - w0, y0], [x + w1, y1]]), max(0.4, lw * 0.4), lat, alpha=0.8)
        ink_line(ctx, np.array([[x + w0, y0], [x - w1, y1]]), max(0.4, lw * 0.4), lat, alpha=0.8)
        ink_line(ctx, np.array([[x - w1, y1], [x + w1, y1]]), max(0.4, lw * 0.4), lat, alpha=0.6)
    if lights > 0:
        on = 1.0 if (t * 0.8) % 1.0 < 0.5 else 0.25
        for fy in (1.0, 0.66, 0.33):
            yy = gy - Hs * fy
            soft_glow(ctx, x, yy, 6 * s, (0.9, 0.2, 0.15, 1.0), 0.8 * on * lights)
            ctx.arc(x, yy, 0.9 * s, 0, 2 * math.pi)
            set_c(ctx, (1.0, 0.45, 0.35, 1.0), on * lights)
            ctx.fill()


def plant(ctx, x, gy, s, t, state='intact', lights=0.0, lw=1.2, fog=0.0, fogcol=None, seed=0, glow=0.0):
    """Units 3 and 4 of the Chernobyl plant seen from the north-east, in elevation: the long turbine hall in front,
    the tall reactor buildings behind, the stack between them. x = left end; Unit 4 at the right.
    state: 'intact', 'damaged' (the reactor hall and its roof destroyed), 'nsc' (under the arch)."""
    rng = np.random.default_rng(seed)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    wall = fogc(mix(CONCRETE, PAL['grey'], 0.35), fog, fogcol)
    dark = fogc(shade_c(wall, -0.25), fog, fogcol)
    Lh = 420 * s
    # reactor buildings (Unit 3 and Unit 4) behind
    for k, (ux, uw, uh) in enumerate(((120, 110, 72), (250, 110, 72))):
        bx = x + ux * s
        top = gy - uh * s
        if state == 'damaged' and k == 1:
            # the destroyed reactor hall: jagged broken walls, an open, glowing interior
            pts = [[bx, gy - 30 * s], [bx, top + 8 * s], [bx + 12 * s, top + 2 * s], [bx + 20 * s, top + 14 * s], [bx + 34 * s, top + 6 * s],
                   [bx + 44 * s, top + 26 * s], [bx + 58 * s, top + 22 * s], [bx + 66 * s, top + 40 * s], [bx + 80 * s, top + 30 * s],
                   [bx + 92 * s, top + 44 * s], [bx + uw * s, top + 36 * s], [bx + uw * s, gy - 30 * s]]
            ink_shape(ctx, np.array(pts), dark, lw=lw * 1.2, ink=inkc, smooth_path=False, shadow=(shade_c(dark, -0.3), 10 * s),
                      hatch=(3.2 * s, 70, max(0.4, lw * 0.4), 0.4), light=(-1, -0.2))
            core = [[bx + 24 * s, top + 30 * s], [bx + 40 * s, top + 34 * s], [bx + 62 * s, top + 46 * s], [bx + 84 * s, top + 50 * s],
                    [bx + 86 * s, top + 62 * s], [bx + 22 * s, top + 60 * s]]
            gcol = mix(PAL['candle'], PAL['burg2'], 0.35)
            ink_shape(ctx, np.array(core), mix(PAL['charcoal'], gcol, 0.4 + 0.3 * glow), lw=lw, ink=inkc, smooth_path=False)
            if glow > 0:
                fl = 1 + 0.12 * math.sin(t * 7) + 0.08 * math.sin(t * 17)
                soft_glow(ctx, bx + 55 * s, top + 48 * s, 60 * s * fl, PAL['candle'], 0.45 * glow)
                soft_glow(ctx, bx + 55 * s, top + 50 * s, 20 * s * fl, PAL['candle2'], 0.7 * glow)
            # twisted beams and fallen slabs
            for j in range(9):
                a = rng.uniform(-1.2, 1.2)
                px = bx + rng.uniform(15, 95) * s
                py = top + rng.uniform(20, 45) * s
                ink_line(ctx, np.array([[px, py], [px + math.sin(a) * 14 * s, py - math.cos(a) * 10 * s]]), max(0.8, 1.4 * s), inkc)
            continue
        R(ctx, bx, top, bx + uw * s, gy - 30 * s, wall, lw, inkc, (shade_c(wall, -0.2), 8 * s), (3.2 * s, 75, max(0.4, lw * 0.4), 0.3), seed + k)
        for j in range(int(uw / 9)):
            xx = bx + (4 + j * 9) * s
            ink_line(ctx, np.array([[xx, top + 4 * s], [xx, gy - 32 * s]]), max(0.4, lw * 0.4), inkc, alpha=0.3)
        for j in range(3):
            yy = top + (10 + j * 12) * s
            for i in range(int(uw / 12)):
                wx = bx + (5 + i * 12) * s
                lit = lights > 0 and rng.random() < 0.5
                R(ctx, wx, yy, wx + 5 * s, yy + 3 * s, mix(PAL['candle'], PAL['candle2'], rng.random()) if lit else fogc(GLASS, fog, fogcol),
                  max(0.3, lw * 0.4), inkc, None, None, seed + i)
        if k == 1 and state == 'intact':
            # the stepped deaerator gallery on the side of Unit 4
            R(ctx, bx + uw * s, gy - 52 * s, bx + (uw + 16) * s, gy - 30 * s, shade_c(wall, -0.1), lw, inkc, None, None, seed + 9)
    # the stack, between Units 3 and 4
    stack(ctx, x + 240 * s, gy - 30 * s, s, t, lw, lights, fog, fogcol)
    # the long turbine hall in front
    th = 30 * s
    R(ctx, x, gy - th, x + Lh, gy, fogc(mix(CONCRETE, PAL['parch3'], 0.2), fog, fogcol), lw, inkc, (shade_c(wall, -0.2), 6 * s), None, seed + 20)
    for j in range(int(Lh / (6 * s))):
        xx = x + j * 6 * s
        ink_line(ctx, np.array([[xx, gy - th + 2 * s], [xx, gy]]), max(0.4, lw * 0.4), inkc, alpha=0.3)
        lit = lights > 0 and rng.random() < 0.35
        R(ctx, xx + 1.2 * s, gy - th + 5 * s, xx + 4.8 * s, gy - th + 16 * s, mix(PAL['candle'], PAL['candle2'], rng.random()) if lit else fogc(GLASS, fog, fogcol),
          max(0.3, lw * 0.4), inkc, None, None, seed + j)
    if state == 'damaged':
        # the turbine hall roof broken and burning in places
        for j in range(5):
            fx = x + (270 + j * 22) * s
            ink_shape(ctx, np.array([[fx, gy - th], [fx + 8 * s, gy - th - 6 * s], [fx + 16 * s, gy - th]]), PAL['charcoal'], lw=lw, ink=inkc, smooth_path=False)
    if state == 'nsc':
        nsc(ctx, x + 300 * s, gy, s, lw, fog, fogcol)


def nsc(ctx, cx, gy, s, lw=1.2, fog=0.0, fogcol=None):
    """The New Safe Confinement (slid into place in November 2016): a steel arch about 108 m high and 257 m
    across, seen end-on, its end wall clad in vertical panels."""
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    steel = fogc(mix(PAL['grey3'], PAL['linen2'], 0.35), fog, fogcol)
    span, hgt = 257 * s, 108 * s
    pts = [(cx + span / 2 * math.cos(a), gy - hgt * math.sin(a)) for a in np.linspace(0, math.pi, 40)]
    ink_shape(ctx, np.array(pts), steel, lw=lw * 1.3, ink=inkc, smooth_path=True, shadow=(shade_c(steel, -0.25), 24 * s),
              hatch=(4.0 * s, 0, max(0.4, lw * 0.4), 0.25), light=(-1, -0.5))
    for k in range(1, 18):
        xx = cx - span / 2 + span * k / 18
        yy = gy - hgt * math.sqrt(max(0.0, 1 - ((xx - cx) / (span / 2)) ** 2))
        ink_line(ctx, np.array([[xx, gy], [xx, yy + 2 * s]]), max(0.4, lw * 0.5), inkc, alpha=0.45)
    for a in np.linspace(0.15, math.pi - 0.15, 9):
        ink_line(ctx, np.array([[cx + span / 2 * 0.93 * math.cos(a), gy - hgt * 0.93 * math.sin(a)], [cx + span / 2 * math.cos(a), gy - hgt * math.sin(a)]]),
                 max(0.6, lw * 0.8), inkc, alpha=0.6)
    inner = [(cx + span / 2 * 0.93 * math.cos(a), gy - hgt * 0.93 * math.sin(a)) for a in np.linspace(0, math.pi, 40)]
    ink_line(ctx, np.array(inner), max(0.6, lw * 0.7), inkc, alpha=0.6)


def pylon(ctx, x, gy, h, lw=1.0, fog=0.0, fogcol=None):
    c = fogc(PAL['grey2'], fog, fogcol)
    for sd in (-1, 1):
        ink_line(ctx, np.array([[x + sd * h * 0.16, gy], [x + sd * h * 0.04, gy - h]]), lw, c)
    for k in range(6):
        y0 = gy - h * k / 6
        y1 = gy - h * (k + 1) / 6
        w0 = h * (0.16 - 0.12 * k / 6)
        w1 = h * (0.16 - 0.12 * (k + 1) / 6)
        ink_line(ctx, np.array([[x - w0, y0], [x + w1, y1]]), lw * 0.6, c)
        ink_line(ctx, np.array([[x + w0, y0], [x - w1, y1]]), lw * 0.6, c)
    for yy, ww in ((gy - h * 0.8, h * 0.3), (gy - h * 0.62, h * 0.24)):
        ink_line(ctx, np.array([[x - ww, yy], [x + ww, yy]]), lw, c)


# ----------------------------------------------------------------------------------------------
# The control room
# ----------------------------------------------------------------------------------------------
def dial(ctx, x, y, r, val, lw=1.2, label='', red=0.0, seed=0, ticks=10):
    """An analogue dial; val 0..1 moves the needle across a 240-degree scale."""
    ink_shape(ctx, ellipse_pts(x, y, r * 1.08, r * 1.08, 28), PAL['charcoal'], lw=lw, smooth_path=True)
    ink_shape(ctx, ellipse_pts(x, y, r, r, 28), mix(PAL['linen'], PAL['parch2'], 0.3), lw=lw * 0.7)
    a0, a1 = math.radians(210), math.radians(-30)
    for k in range(ticks + 1):
        a = a0 + (a1 - a0) * k / ticks
        L = 0.18 if k % 2 == 0 else 0.1
        ink_line(ctx, np.array([[x + math.cos(a) * r * 0.86, y - math.sin(a) * r * 0.86], [x + math.cos(a) * r * (0.86 - L), y - math.sin(a) * r * (0.86 - L)]]),
                 max(0.5, lw * 0.6), PAL['ink'])
    # the red zone at the top of the scale
    pts = [(x + math.cos(a) * r * 0.84, y - math.sin(a) * r * 0.84) for a in np.linspace(a0 + (a1 - a0) * 0.8, a1, 8)]
    ink_line(ctx, np.array(pts), max(1.0, r * 0.08), mix(PAL['burg2'], PAL['candle'], 0.1))
    a = a0 + (a1 - a0) * clamp(val, -0.05, 1.08)
    ink_line(ctx, np.array([[x - math.cos(a) * r * 0.12, y + math.sin(a) * r * 0.12], [x + math.cos(a) * r * 0.78, y - math.sin(a) * r * 0.78]]),
             max(0.8, r * 0.04), PAL['ink'])
    ctx.arc(x, y, r * 0.07, 0, 2 * math.pi)
    set_c(ctx, PAL['ink'])
    ctx.fill()
    if label:
        text(ctx, x, y + r * 0.45, 1, r * 0.16, label, PAL['ink'], bold=False)
    if red > 0:
        soft_glow(ctx, x, y, r * 1.6, (0.9, 0.25, 0.2, 1.0), 0.35 * red)


def lamp(ctx, x, y, r, on, col=None, lw=0.6):
    col = col or (0.95, 0.3, 0.22, 1.0)
    ink_shape(ctx, ellipse_pts(x, y, r, r, 10), mix(mix(PAL['charcoal'], col, 0.25), col, on), lw=lw)
    if on > 0.5:
        soft_glow(ctx, x, y, r * 3, col, 0.4 * on)


def panel_wall(ctx, x0, x1, y_top, y_bot, t, alarm=0.0, lw=1.2, seed=0, flicker=0.0):
    """The back wall of the control room: tall instrument panels with rows of lamps, switches and dials,
    a mimic diagram of pipework, chart recorders and, in the middle, a large grid of indicator lamps."""
    rng = np.random.default_rng(seed)
    panel = mix(PAL['green2'], PAL['grey3'], 0.45)
    ink_shape(ctx, np.array([[x0, y_top], [x1, y_top], [x1, y_bot], [x0, y_bot]]), panel, lw=lw, smooth_path=False)
    n = int((x1 - x0) / 120)
    for k in range(n):
        px = x0 + k * (x1 - x0) / n
        pw = (x1 - x0) / n
        ink_line(ctx, np.array([[px, y_top], [px, y_bot]]), lw, PAL['ink'], alpha=0.8)
        kind = k % 4
        cx = px + pw / 2
        if kind == 0:
            for i in range(3):
                dial(ctx, cx, y_top + 70 + i * 92, 32, 0.3 + 0.25 * math.sin(t * 0.4 + k + i) * 0.1 + 0.4 * alarm * (i == 1), lw * 0.8, seed=k * 10 + i)
        elif kind == 1:
            for i in range(6):
                for j in range(5):
                    on = 1.0 if (alarm > 0.5 and hash01(k, i, j) < 0.5 and (t * 3 + hash01(k, i, j, 2)) % 1.0 < 0.5) else (0.9 if hash01(k, i, j, 3) < 0.25 else 0.0)
                    col = (0.95, 0.3, 0.22, 1.0) if hash01(k, i, j, 4) < 0.5 else (0.95, 0.85, 0.5, 1.0)
                    lamp(ctx, px + 18 + j * (pw - 36) / 4, y_top + 40 + i * 34, 7, on, col)
            for i in range(4):
                R(ctx, px + 14, y_top + 260 + i * 26, px + pw - 14, y_top + 278 + i * 26, mix(PAL['parch'], PAL['grey3'], 0.4), lw * 0.5, None, None, None, k + i)
        elif kind == 2:
            # chart recorder: paper scrolling past a moving pen
            R(ctx, px + 14, y_top + 40, px + pw - 14, y_top + 200, PAL['linen'], lw * 0.8, None, None, None, k)
            for g in range(5):
                gx = px + 14 + (pw - 28) * g / 4
                ink_line(ctx, np.array([[gx, y_top + 40], [gx, y_top + 200]]), 0.5, PAL['grey2'], alpha=0.5)
            pts = []
            for i in range(30):
                yy = y_top + 200 - i * 160 / 29
                v = 0.5 + 0.15 * math.sin((t * 30 - i) * 0.4 + k) * 0.3 + 0.08 * math.sin((t * 30 - i) * 1.7)
                if alarm > 0:
                    v += alarm * max(0.0, 1 - i / 8) * 0.4
                pts.append((px + 14 + (pw - 28) * clamp(v, 0.05, 0.95), yy))
            ink_line(ctx, np.array(pts), 1.4, PAL['burg2'])
            for i in range(8):
                lamp(ctx, px + 20 + i * (pw - 40) / 7, y_top + 230, 6, 0.9 if hash01(k, i, 5) < 0.3 else 0.0, (0.5, 0.85, 0.5, 1.0))
        else:
            # mimic diagram: pipe lines and valves
            for i in range(5):
                yy = y_top + 50 + i * 55
                ink_line(ctx, np.array([[px + 12, yy], [px + pw - 12, yy]]), 2.0, PAL['charcoal'])
                ctx.arc(px + pw * (0.3 + 0.4 * hash01(k, i)), yy, 8, 0, 2 * math.pi)
                set_c(ctx, PAL['burg3'] if hash01(k, i, 2) < 0.5 else PAL['green3'])
                ctx.fill()
            ink_line(ctx, np.array([[px + pw * 0.5, y_top + 50], [px + pw * 0.5, y_top + 270]]), 2.0, PAL['charcoal'])
        # switches along the bottom
        for i in range(4):
            ink_shape(ctx, ellipse_pts(px + 18 + i * (pw - 36) / 3, y_bot - 40, 6, 6, 10), PAL['charcoal'], lw=0.6)
            ink_line(ctx, np.array([[px + 18 + i * (pw - 36) / 3, y_bot - 40], [px + 18 + i * (pw - 36) / 3 + 5, y_bot - 52]]), 2, PAL['ink'])
    if flicker > 0:
        set_c(ctx, PAL['ink'], flicker)
        ctx.rectangle(x0, y_top, x1 - x0, y_bot - y_top)
        ctx.fill()


def core_grid(ctx, cx, cy, r, t, alarm=0.0, lw=1.0):
    """A large round grid of small indicator lamps (an illustration of the reactor's channel display)."""
    ink_shape(ctx, ellipse_pts(cx, cy, r * 1.06, r * 1.06, 36), PAL['charcoal'], lw=lw)
    n = 15
    for i in range(n):
        for j in range(n):
            x = cx - r + (i + 0.5) * 2 * r / n
            y = cy - r + (j + 0.5) * 2 * r / n
            if (x - cx) ** 2 + (y - cy) ** 2 > r * r * 0.92:
                continue
            base = 0.15 + 0.6 * hash01(i, j)
            on = base
            if alarm > 0:
                on = clamp(base + alarm * (0.6 + 0.4 * math.sin(t * 14 + i + j)))
            col = mix((0.95, 0.85, 0.5, 1.0), (0.95, 0.3, 0.22, 1.0), alarm * hash01(i, j, 3))
            lamp(ctx, x, y, r / n * 0.32, on, col, lw * 0.4)


def console(ctx, x0, x1, y_top, y_bot, t, lw=1.2, alarm=0.0, seed=0):
    """The operators' sloping desk console with rows of keys, switches and small lamps."""
    c = mix(PAL['grey3'], PAL['green2'], 0.35)
    ink_shape(ctx, np.array([[x0, y_bot], [x0 + 40, y_top], [x1 - 40, y_top], [x1, y_bot]]), c, lw=lw, smooth_path=False,
              shadow=(shade_c(c, -0.25), 14), light=(0, -1))
    ink_shape(ctx, np.array([[x0, y_bot], [x1, y_bot], [x1, y_bot + 120], [x0, y_bot + 120]]), shade_c(c, -0.3), lw=lw, smooth_path=False)
    for i in range(int((x1 - x0 - 100) / 30)):
        for j in range(3):
            x = x0 + 60 + i * 30 + j * 6
            y = y_top + 18 + j * (y_bot - y_top - 30) / 3
            ink_shape(ctx, np.array([[x - 7, y - 5], [x + 7, y - 5], [x + 7, y + 5], [x - 7, y + 5]]), PAL['charcoal2'] if (i + j) % 3 else PAL['linen2'], lw=0.6,
                      smooth_path=False)
            if hash01(seed, i, j) < 0.2:
                lamp(ctx, x, y - 11, 3, 1.0 if (alarm > 0.3 and (t * 4 + i) % 1 < 0.5) else 0.0)


# ----------------------------------------------------------------------------------------------
# The funfair and the playground
# ----------------------------------------------------------------------------------------------
def ferris_wheel(ctx, cx, cy, r, t, lw=1.4, fog=0.0, fogcol=None, rust=0.5, seed=0):
    """A Ferris wheel on an A-frame, its gondolas hanging still or rocking slightly in the wind."""
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    yel = fogc(mix(mix(PAL['candle'], PAL['parch3'], 0.35), PAL['brown2'], rust), fog, fogcol)
    frame = fogc(mix(PAL['grey2'], PAL['brown2'], rust * 0.5), fog, fogcol)
    for sd in (-1, 1):
        ink_line(ctx, np.array([[cx + sd * r * 0.55, cy + r * 1.18], [cx, cy]]), max(1.0, r * 0.035), frame)
    ink_line(ctx, np.array([[cx - r * 0.38, cy + r * 0.8], [cx + r * 0.38, cy + r * 0.8]]), max(0.8, r * 0.02), frame)
    for rr in (1.0, 0.93):
        ink_line(ctx, np.array([(cx + r * rr * math.cos(a), cy + r * rr * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 64)]), max(0.8, r * 0.018), yel)
    n = 26
    for k in range(n):
        a = 2 * math.pi * k / n
        ink_line(ctx, np.array([[cx, cy], [cx + r * math.cos(a), cy + r * math.sin(a)]]), max(0.4, r * 0.006), yel, alpha=0.9)
        if k % 2 == 0:
            b = 2 * math.pi * (k + 1) / n
            ink_line(ctx, np.array([[cx + r * 0.93 * math.cos(a), cy + r * 0.93 * math.sin(a)], [cx + r * math.cos(b), cy + r * math.sin(b)]]),
                     max(0.4, r * 0.006), yel, alpha=0.8)
    ink_shape(ctx, ellipse_pts(cx, cy, r * 0.07, r * 0.07, 14), frame, lw=lw, ink=inkc)
    for k in range(13):
        a = 2 * math.pi * k / 13 + 0.12
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        sw = 0.05 * math.sin(t * 1.4 + k * 0.9)
        gx, gy = px + math.sin(sw) * r * 0.1, py + math.cos(sw) * r * 0.1
        ink_line(ctx, np.array([[px, py], [gx, gy]]), max(0.5, r * 0.006), inkc)
        cab = fogc(mix(mix(PAL['candle'], PAL['burg2'], 0.4 * (k % 2)), PAL['brown2'], rust), fog, fogcol)
        ink_shape(ctx, np.array([[gx - r * 0.06, gy], [gx + r * 0.06, gy], [gx + r * 0.07, gy + r * 0.05], [gx + r * 0.05, gy + r * 0.11],
                                 [gx - r * 0.05, gy + r * 0.11], [gx - r * 0.07, gy + r * 0.05]]), cab, lw=max(0.5, lw * 0.6), ink=inkc, seed=k)
        ink_shape(ctx, np.array([[gx - r * 0.07, gy - r * 0.035], [gx + r * 0.07, gy - r * 0.035], [gx + r * 0.05, gy], [gx - r * 0.05, gy]]),
                  shade_c(cab, -0.15), lw=max(0.5, lw * 0.5), ink=inkc, smooth_path=False)


def swings(ctx, x, gy, s, t, lw=1.2, wind=1.0, fog=0.0, fogcol=None):
    """A swing frame; the empty seats move in the wind."""
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    c = fogc(mix(PAL['burg2'], PAL['brown2'], 0.6), fog, fogcol)
    for sd in (-1, 1):
        for d in (-0.4, 0.4):
            ink_line(ctx, np.array([[x + sd * 2.0 * s + d * s, gy], [x + sd * 2.0 * s, gy - 2.5 * s]]), max(1.0, 0.07 * s), c)
    ink_line(ctx, np.array([[x - 2.0 * s, gy - 2.5 * s], [x + 2.0 * s, gy - 2.5 * s]]), max(1.0, 0.08 * s), c)
    for k, sx in enumerate((-1.0, 1.0)):
        a = wind * 0.22 * math.sin(t * 1.9 + k * 1.3)
        px = x + sx * s
        bx, by = px + math.sin(a) * 1.9 * s, gy - 2.5 * s + math.cos(a) * 1.9 * s
        ink_line(ctx, np.array([[px - 0.25 * s, gy - 2.5 * s], [bx - 0.25 * s, by]]), max(0.5, 0.025 * s), inkc)
        ink_line(ctx, np.array([[px + 0.25 * s, gy - 2.5 * s], [bx + 0.25 * s, by]]), max(0.5, 0.025 * s), inkc)
        ink_shape(ctx, np.array([[bx - 0.32 * s, by], [bx + 0.32 * s, by], [bx + 0.3 * s, by + 0.1 * s], [bx - 0.3 * s, by + 0.1 * s]]),
                  fogc(PAL['wood3'], fog, fogcol), lw=lw * 0.7, ink=inkc, smooth_path=False)


def plume(ctx, x, y, s, t, seed=0, n=16, alpha=0.8, lit=0.0, wind=0.3, col=None, top=1.0):
    """A column of smoke rising and leaning with the wind: overlapping inked puffs that swell and drift.
    lit lights the base from below with firelight."""
    col = col or mix(PAL['charcoal2'], PAL['grey2'], 0.4)
    for k in range(n):
        u = ((t * 0.07 + k / n + hash01(seed, k) * 0.04) % 1.0)
        if u > top:
            continue
        h = u * 900 * s
        px = x + (wind * h * 0.6 + 40 * s * math.sin(u * 5 + t * 0.4 + seed + k)) * (0.4 + u)
        py = y - h
        r = (40 + 220 * u) * s
        a = alpha * min(1.0, u * 6) * (1 - u) ** 0.6
        c = mix(col, PAL['candle'], lit * max(0.0, 1 - u * 3.5))
        pts = ellipse_pts(px, py, r, r * 0.75, 18)
        pts = pts + np.array([[6 * s * math.sin(i * 1.7 + t + k), 6 * s * math.cos(i * 2.3 + t)] for i in range(len(pts))])
        ink_shape(ctx, pts, (*c[:3], a), lw=max(0.6, 1.2 * s), ink=(*PAL['ink'][:3], a * 0.6), seed=seed + k,
                  shadow=((*shade_c(c, -0.3)[:3], a * 0.8), r * 0.25), light=(-0.6, -1))


def embers(ctx, x0, x1, y0, y1, t, n=40, seed=0, size=2.0, alpha=1.0):
    for i in range(n):
        ph = (t * 0.25 * (0.5 + hash01(seed, i)) + hash01(seed, i, 2)) % 1.0
        x = x0 + (x1 - x0) * hash01(seed, i, 3) + 30 * math.sin(t * 1.6 + i)
        y = y1 - (y1 - y0) * ph
        a = alpha * (1 - ph) * (0.6 + 0.4 * math.sin(t * 9 + i))
        ctx.arc(x, y, size * (0.5 + hash01(seed, i, 4)), 0, 2 * math.pi)
        set_c(ctx, mix(PAL['candle2'], PAL['candle'], hash01(seed, i, 5)), max(0.0, a))
        ctx.fill()


def searchlight(ctx, x, y, ang, length, width, alpha=0.18, col=None):
    col = col or PAL['linen']
    g = cairo.LinearGradient(x, y, x + math.cos(ang) * length, y + math.sin(ang) * length)
    g.add_color_stop_rgba(0, *col[:3], alpha)
    g.add_color_stop_rgba(1, *col[:3], 0)
    nx, ny = -math.sin(ang), math.cos(ang)
    ctx.move_to(x, y)
    ctx.line_to(x + math.cos(ang) * length + nx * width, y + math.sin(ang) * length + ny * width)
    ctx.line_to(x + math.cos(ang) * length - nx * width, y + math.sin(ang) * length - ny * width)
    ctx.close_path()
    ctx.set_source(g)
    ctx.fill()
