"""Illustrated sets for scenes 2, 4, 5, 6 and 8, drawn in flat elevation (like a period town view)
and saved as depth layers in assets/layers/.

  python src/sets2.py [city|council|cure|land|map]
"""
import math
import os
import sys

import cairo
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import (PAL, W, H, LAYERS, new_surface, set_c, ink_shape, ink_line, hatch_lines, mix, shade_c, hash01, path_poly,
                  path_smooth, ellipse_pts, taper_stroke, soft_glow, fbm2)
from sets import texturize, draw_cloud, draw_cathedral, sky_surface


def save(surf, name, tex=0.22):
    texturize(surf, hash01(len(name), 7) * 1000, amount=tex)
    os.makedirs(LAYERS, exist_ok=True)
    surf.write_to_png(os.path.join(LAYERS, name + '.png'))


def canvas(w, h, scale):
    surf = new_surface(int(w * scale), int(h * scale))
    ctx = cairo.Context(surf)
    ctx.scale(scale, scale)
    return surf, ctx


def R(ctx, x0, y0, x1, y1, fill, lw=1.2, ink=None, shadow=None, hatch=None, seed=0, boil=0.4):
    ink_shape(ctx, np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]), fill, lw=lw, ink=ink, smooth_path=False, shadow=shadow,
              hatch=hatch, seed=seed, boil=boil)


def fogc(c, k, fog=None):
    return mix(c, fog or PAL['grey3'], k)


# ----------------------------------------------------------------------------------------------
# A half-timbered house in elevation
# ----------------------------------------------------------------------------------------------
def house_elev(ctx, x, gy, wm, floors, s, seed, plaster=None, kind='gable', fogk=0.0, fog=None, shop=True, dormers=3, lit=0.0):
    """x: left edge, gy: ground y, wm: width in metres, s: px per metre."""
    rng = np.random.default_rng(seed)
    F = lambda c: fogc(c, fogk, fog)
    ink = F(PAL['ink'])
    lw = max(0.6, 0.06 * s)
    w = wm * s
    plaster = plaster or [PAL['plaster'], PAL['parch2'], mix(PAL['plaster'], PAL['burg2'], 0.2), PAL['plaster2']][int(rng.integers(0, 4))]
    stone = mix(PAL['stone'], PAL['burg2'], 0.22)
    wood = PAL['wood2']
    h0, fh, jet = 3.2 * s, 2.8 * s, 0.25 * s
    detail = s > 4
    # ground floor
    R(ctx, x, gy - h0, x + w, gy, F(stone), lw, ink, seed=seed)
    if detail:
        if shop and rng.random() < 0.7:
            sx0, sx1 = x + w * 0.12, x + w * 0.58
            R(ctx, sx0, gy - h0 * 0.75, sx1, gy - h0 * 0.28, F(PAL['charcoal']), lw * 0.8, ink, seed=seed + 1)
            R(ctx, sx0 - 0.1 * s, gy - h0 * 0.3, sx1 + 0.1 * s, gy - h0 * 0.22, F(PAL['wood3']), lw * 0.7, ink, seed=seed + 2)
            ink_shape(ctx, np.array([[sx0 - 0.15 * s, gy - h0 * 0.75], [sx1 + 0.15 * s, gy - h0 * 0.75], [sx1 + 0.4 * s, gy - h0 * 0.62],
                                     [sx0 - 0.4 * s, gy - h0 * 0.62]]), F(PAL['wood']), lw=lw * 0.7, ink=ink, smooth_path=False, seed=seed + 3)
            dx0, dx1 = x + w * 0.68, x + w * 0.88
        else:
            dx0, dx1 = x + w * 0.38, x + w * 0.62
        arch = [[dx0, gy], [dx0, gy - h0 * 0.62]] + [[(dx0 + dx1) / 2 + (dx1 - dx0) / 2 * math.cos(a), gy - h0 * 0.62 - (dx1 - dx0) / 2 * math.sin(a)]
                                                     for a in np.linspace(math.pi, 0, 7)[1:-1]] + [[dx1, gy - h0 * 0.62], [dx1, gy]]
        ink_shape(ctx, np.array(arch), F(PAL['wood']), lw=lw, ink=ink, smooth_path=False, seed=seed + 4)
    # upper floors
    y = gy - h0
    for fl in range(1, floors):
        xa, xb = x - jet * fl, x + w + jet * fl
        R(ctx, xa, y - fh, xb, y, F(plaster), lw, ink, seed=seed + 10 + fl)
        if detail:
            R(ctx, xa, y - 0.22 * s, xb, y, F(wood), lw * 0.6, ink, seed=seed + 20 + fl, boil=0.2)
            nb = max(3, int((xb - xa) / (1.15 * s)))
            posts = [xa + (xb - xa) * k / nb for k in range(nb + 1)]
            for pz in posts:
                R(ctx, pz - 0.09 * s, y - fh, pz + 0.09 * s, y, F(wood), lw * 0.5, ink, boil=0.2)
            R(ctx, xa, y - fh * 0.68, xb, y - fh * 0.62, F(wood), lw * 0.5, ink, boil=0.2)
            wins = set(rng.choice(nb, size=max(1, nb // 2), replace=False).tolist())
            for k in range(nb):
                a, b = posts[k] + 0.09 * s, posts[k + 1] - 0.09 * s
                if k in wins:
                    R(ctx, a + 0.05 * s, y - fh + 0.3 * s, b - 0.05 * s, y - fh * 0.68, F(mix(PAL['charcoal'], PAL['grey2'], 0.3)), lw * 0.6, ink, boil=0.2)
                    if lit > 0 and rng.random() < 0.5:
                        soft_glow(ctx, (a + b) / 2, y - fh * 0.82, (b - a) * 1.2, PAL['candle'], 0.4 * lit)
                        R(ctx, a + 0.05 * s, y - fh + 0.3 * s, b - 0.05 * s, y - fh * 0.68, (*PAL['candle'][:3], 0.55 * lit), 0, ink)
                    for q in range(1, 3):
                        xx = a + (b - a) * q / 3
                        ink_line(ctx, np.array([[xx, y - fh + 0.3 * s], [xx, y - fh * 0.68]]), lw * 0.35, F(PAL['grey3']), alpha=0.6)
                    ink_line(ctx, np.array([[a, y - 0.22 * s], [b, y - fh * 0.62]]), lw * 1.2, F(wood))
                    ink_line(ctx, np.array([[a, y - fh * 0.62], [b, y - 0.22 * s]]), lw * 1.2, F(wood))
                else:
                    ink_line(ctx, np.array([[a, y - 0.22 * s], [b, y - fh]]), lw * 1.5, F(wood))
        y -= fh
    xa, xb = x - jet * (floors - 1), x + w + jet * (floors - 1)
    # roof
    if kind == 'gable':
        gh = (xb - xa) * 0.5 * 1.8
        m = (xa + xb) / 2
        ink_shape(ctx, np.array([[xa - 0.3 * s, y], [xb + 0.3 * s, y], [m, y - gh - 0.3 * s]]), F(PAL['roof']), lw=lw, ink=ink,
                  smooth_path=False, seed=seed + 40)
        ink_shape(ctx, np.array([[xa + 0.25 * s, y], [xb - 0.25 * s, y], [m, y - gh + 0.4 * s]]), F(plaster), lw=lw, ink=ink,
                  smooth_path=False, seed=seed + 41)
        if detail:
            ink_line(ctx, np.array([[m, y], [m, y - gh + 0.6 * s]]), lw * 1.3, F(wood))
            ink_line(ctx, np.array([[xa + (m - xa) * 0.5, y - gh * 0.5], [xb - (xb - m) * 0.5, y - gh * 0.5]]), lw * 1.3, F(wood))
            for q in (-1, 1):
                wx = m + q * (xb - xa) * 0.17
                R(ctx, wx - 0.28 * s, y - 1.4 * s, wx + 0.28 * s, y - 0.45 * s, F(PAL['charcoal']), lw * 0.6, ink)
            R(ctx, m - 0.2 * s, y - gh * 0.68, m + 0.2 * s, y - gh * 0.55, F(PAL['charcoal']), lw * 0.6, ink)
        top = y - gh
    else:
        # eaves to the front: a tall tiled roof with rows of small dormers (the drying lofts of Strasbourg)
        rh = (xb - xa) * 0.62
        ink_shape(ctx, np.array([[xa - 0.4 * s, y], [xb + 0.4 * s, y], [xb - rh * 0.18, y - rh], [xa + rh * 0.18, y - rh]]),
                  F(PAL['roof2']), lw=lw, ink=ink, smooth_path=False, seed=seed + 42,
                  shadow=(F(shade_c(PAL['roof2'], -0.25)), rh * 0.3), hatch=(max(2.0, 0.18 * s), 0, lw * 0.4, 0.35))
        if detail:
            for row in range(dormers):
                yy = y - rh * (0.2 + row * 0.27)
                inset = rh * 0.18 * (0.2 + row * 0.27)
                n = max(2, int((xb - xa - 2 * inset) / (1.6 * s)) - row)
                for k in range(n):
                    dx = xa + inset + (k + 0.5) * (xb - xa - 2 * inset) / n
                    ds = 0.5 * s * (1 - 0.18 * row)
                    ink_shape(ctx, np.array([[dx - ds, yy], [dx + ds, yy], [dx, yy - ds * 1.3]]), F(PAL['roof']), lw=lw * 0.6, ink=ink, smooth_path=False)
                    ink_shape(ctx, np.array([[dx - ds * 0.45, yy], [dx + ds * 0.45, yy], [dx, yy - ds * 0.7]]), F(PAL['charcoal']), lw=0, smooth_path=False)
        top = y - rh
    if rng.random() < 0.6:
        cx = xa + (xb - xa) * rng.uniform(0.25, 0.75)
        R(ctx, cx - 0.35 * s, top + 0.3 * (y - top) - 1.8 * s, cx + 0.35 * s, top + 0.3 * (y - top) + 1.0 * s, F(mix(PAL['stone'], PAL['brown'], 0.5)), lw * 0.8, ink)
    return xb - x + jet * (floors - 1), top


# ----------------------------------------------------------------------------------------------
# Scene 2 - the city on the river
# ----------------------------------------------------------------------------------------------
def build_city():
    # sky
    rng = np.random.default_rng(4)
    surf = sky_surface(1500, H, 41, 0.0, horizon=0.55)
    save(surf, 'city_sky', 0.12)
    # far: the cathedral and the roofs of the old island
    surf, ctx = canvas(1700, H, 1.25)
    gy = 1060
    x = -60
    i = 0
    while x < 1760:
        wm = rng.uniform(9, 15)
        wd, top = house_elev(ctx, x, gy, wm, int(rng.integers(3, 5)), 6.5, 600 + i, kind='eave' if rng.random() < 0.55 else 'gable', fogk=0.5, shop=False)
        x += wd + rng.uniform(-10, 0)
        i += 1
    draw_cathedral(ctx, 780, gy + 10, 6.6, fogk=0.32)
    for k in range(6):
        house_elev(ctx, 440 + k * 120 + rng.uniform(-20, 20), gy + 70, rng.uniform(11, 15), 3, 7.2, 700 + k, kind='eave', fogk=0.45, shop=False)
    save(surf, 'city_far', 0.18)
    # mid: houses along the river, their gables to the water, and the river itself
    surf, ctx = canvas(1900, H, 1.4)
    gy = 1330
    s = 21.0
    x = -80
    i = 0
    while x < 1980:
        wm = rng.uniform(6.5, 9)
        wd, top = house_elev(ctx, x, gy, wm, int(rng.integers(3, 4)), s, 800 + i, kind='gable' if rng.random() < 0.65 else 'eave', fogk=0.14,
                             dormers=3)
        x += wd + rng.uniform(4, 30)
        i += 1
    # quay wall and the river Ill
    R(ctx, -80, gy, 1980, gy + 26, mix(PAL['stone'], PAL['brown'], 0.3), 1.4, seed=5)
    for k in range(40):
        ink_line(ctx, np.array([[k * 50 - 80, gy], [k * 50 - 80, gy + 26]]), 0.6, alpha=0.5)
    g = cairo.LinearGradient(0, gy + 26, 0, gy + 200)
    g.add_color_stop_rgba(0, *mix(PAL['green3'], PAL['grey2'], 0.5)[:3], 1)
    g.add_color_stop_rgba(1, *mix(PAL['green3'], PAL['charcoal'], 0.4)[:3], 1)
    ctx.set_source(g)
    ctx.rectangle(-80, gy + 26, 2060, 300)
    ctx.fill()
    # a wooden footbridge
    bx = 1120
    ink_shape(ctx, np.array([[bx - 260, gy + 4], [bx + 260, gy + 4], [bx + 230, gy + 40], [bx - 230, gy + 40]]), PAL['wood'], lw=1.6, smooth_path=False,
              shadow=(PAL['wood2'], 8), seed=9)
    for k in range(9):
        px = bx - 220 + k * 55
        R(ctx, px - 6, gy + 40, px + 6, gy + 190, PAL['wood2'], 1.0)
    for k in range(20):
        ink_line(ctx, np.array([[bx - 255 + k * 26, gy - 30], [bx - 255 + k * 26, gy + 4]]), 1.0)
    ink_line(ctx, np.array([[bx - 260, gy - 30], [bx + 260, gy - 30]]), 2.0)
    save(surf, 'city_mid', 0.2)
    # near: the market quay - stalls, awnings, barrels, sacks, a cart
    surf, ctx = canvas(2100, H, 1.5)
    gy = 1800
    g = cairo.LinearGradient(0, 1500, 0, H)
    g.add_color_stop_rgba(0, *mix(PAL['stone2'], PAL['brown'], 0.4)[:3], 1)
    g.add_color_stop_rgba(1, *mix(PAL['stone2'], PAL['brown'], 0.6)[:3], 1)
    ctx.set_source(g)
    ctx.rectangle(-100, 1500, 2300, 500)
    ctx.fill()
    R(ctx, -100, 1490, 2200, 1512, mix(PAL['stone'], PAL['brown'], 0.3), 1.6)
    ground_texture(ctx, -100, 1512, 2200, H + 10, rng)
    for k, sx in enumerate([60, 700, 1340, 1900]):
        stall(ctx, sx, gy - 130, 3.4, 900 + k, rng)
    for k in range(7):
        bx_ = rng.uniform(0, 2000)
        barrel(ctx, bx_, gy + rng.uniform(40, 110), 2.6, 950 + k)
    save(surf, 'city_near', 0.22)
    # foreground: the edge of an awning and a timber post, close to the lens
    surf, ctx = canvas(2300, H, 1.0)
    ink_shape(ctx, np.array([[-60, -40], [700, -40], [640, 160], [520, 200], [400, 160], [280, 205], [160, 165], [-60, 210]]), PAL['burg3'], lw=3,
              shadow=(shade_c(PAL['burg3'], -0.4), 30), hatch=(6, 70, 1.2, 0.4), seed=3)
    R(ctx, 1980, -40, 2150, H + 40, PAL['wood2'], 3, shadow=(shade_c(PAL['wood2'], -0.4), 40), hatch=(6, 80, 1.2, 0.4))
    for k in range(6):
        hx = 60 + k * 90
        ink_line(ctx, np.array([[hx, 180], [hx + 8, 260 + 40 * (k % 2)]]), 2)
        ink_shape(ctx, ellipse_pts(hx + 8, 290 + 40 * (k % 2), 18, 34, 10), PAL['green3'], lw=2, seed=k, shadow=(PAL['green'], 8))
    save(surf, 'city_fg', 0.2)


def ground_texture(ctx, x0, y0, x1, y1, rng):
    """Packed earth and worn paving, drawn as rows of small inked stones that shrink with distance."""
    y = y0 + 4
    k = 0
    while y < y1:
        sc = 0.5 + (y - y0) / 260.0
        x = x0 + rng.uniform(0, 20)
        while x < x1:
            w = rng.uniform(16, 30) * sc
            if rng.random() < 0.8:
                ink_shape(ctx, ellipse_pts(x + w / 2, y, w * 0.45, 5.5 * sc, 8), shade_c(mix(PAL['stone'], PAL['brown3'], rng.random() * 0.5), -0.2 * rng.random()),
                          lw=0.5 + 0.2 * sc, seed=k, ink=mix(PAL['ink'], PAL['stone2'], 0.3))
            x += w
            k += 1
        y += 10 * sc


def stall(ctx, x, gy, s, seed, rng):
    """A market stall: trestle table with goods and a striped canvas awning on poles (s px per cm/10)."""
    w = 160 * s
    R(ctx, x, gy - 34 * s, x + w, gy - 26 * s, PAL['wood3'], 1.4, seed=seed)
    for px in (x + 6 * s, x + w - 6 * s):
        R(ctx, px - 2 * s, gy - 100 * s, px + 2 * s, gy, PAL['wood2'], 1.2)
        ink_line(ctx, np.array([[px, gy - 26 * s], [px - 12 * s, gy]]), 1.6, PAL['wood2'])
    cols = [PAL['burg3'], PAL['parch2']]
    n = 6
    for k in range(n):
        a = x - 10 * s + k * (w + 20 * s) / n
        b = a + (w + 20 * s) / n
        ink_shape(ctx, np.array([[a, gy - 104 * s], [b, gy - 104 * s], [b + 2 * s, gy - 82 * s], [(a + b) / 2, gy - 78 * s], [a - 2 * s, gy - 82 * s]]),
                  cols[k % 2], lw=1.2, smooth_path=False, seed=seed + k, shadow=(shade_c(cols[k % 2], -0.3), 4 * s))
    kind = seed % 3
    for k in range(7):
        gx = x + 14 * s + k * 20 * s
        if kind == 0:
            ink_shape(ctx, ellipse_pts(gx, gy - 40 * s, 9 * s, 6 * s, 10), PAL['brown3'], lw=1.0, seed=seed + k, shadow=(PAL['brown2'], 2 * s))
        elif kind == 1:
            ink_shape(ctx, np.array([[gx - 6 * s, gy - 34 * s], [gx + 6 * s, gy - 34 * s], [gx + 7 * s, gy - 50 * s], [gx, gy - 56 * s], [gx - 7 * s, gy - 50 * s]]),
                      PAL['brown'], lw=1.0, seed=seed + k, shadow=(PAL['umber'], 2 * s))
        else:
            ink_shape(ctx, ellipse_pts(gx, gy - 40 * s, 8 * s, 7 * s, 10), [PAL['green2'], PAL['burg2'], PAL['parch3']][k % 3], lw=1.0, seed=seed + k)


def barrel(ctx, x, gy, s, seed):
    pts = [[x - 18 * s, gy], [x - 21 * s, gy - 25 * s], [x - 18 * s, gy - 50 * s], [x + 18 * s, gy - 50 * s], [x + 21 * s, gy - 25 * s], [x + 18 * s, gy]]
    ink_shape(ctx, np.array(pts), PAL['wood3'], lw=1.4, seed=seed, shadow=(PAL['wood'], 6 * s), hatch=(4, 80, 0.7, 0.3))
    for yy in (8, 25, 42):
        ink_line(ctx, np.array([[x - 20 * s, gy - yy * s], [x + 20 * s, gy - yy * s]]), 1.6, PAL['charcoal'])


# ----------------------------------------------------------------------------------------------
# Scene 4 - the council chamber
# ----------------------------------------------------------------------------------------------
def build_council():
    surf, ctx = canvas(1900, H, 1.25)
    # plastered upper wall, beamed ceiling
    set_c(ctx, mix(PAL['plaster2'], PAL['brown'], 0.45))
    ctx.paint()
    for k in range(8):
        R(ctx, k * 260 - 40, 0, k * 260 + 30, 380, PAL['wood2'], 2, seed=k, shadow=(shade_c(PAL['wood2'], -0.4), 18), hatch=(5, 80, 1, 0.4))
    R(ctx, -40, 360, 1940, 420, PAL['wood2'], 2, seed=99, shadow=(shade_c(PAL['wood2'], -0.4), 20))
    # tall leaded windows: grey daylight through small panes
    for k, wx in enumerate([180, 760, 1340]):
        R(ctx, wx, 470, wx + 260, 1060, PAL['wood'], 2.4, seed=10 + k)
        R(ctx, wx + 20, 490, wx + 240, 1040, mix(PAL['grey3'], PAL['parch2'], 0.35), 1.4, seed=20 + k)
        for i in range(1, 6):
            ink_line(ctx, np.array([[wx + 20 + i * 37, 490], [wx + 20 + i * 37, 1040]]), 0.9, PAL['charcoal2'], alpha=0.8)
        for j in range(1, 12):
            ink_line(ctx, np.array([[wx + 20, 490 + j * 46], [wx + 240, 490 + j * 46]]), 0.9, PAL['charcoal2'], alpha=0.8)
        R(ctx, wx + 120, 470, wx + 140, 1060, PAL['wood'], 1.4)
        soft_glow(ctx, wx + 130, 760, 360, PAL['grey3'], 0.18)
    # the city's arms: argent, a bend gules (a red diagonal band on white)
    ax, ay = 1080, 640
    shield = np.array([[ax - 70, ay - 90], [ax + 70, ay - 90], [ax + 70, ay + 10], [ax, ay + 95], [ax - 70, ay + 10]])
    ink_shape(ctx, shield, PAL['linen'], lw=3, smooth_path=True, seed=5, shadow=(PAL['linen2'], 10))
    ctx.save()
    path_smooth(ctx, shield, True)
    ctx.clip()
    ink_shape(ctx, np.array([[ax - 110, ay - 120], [ax - 60, ay - 140], [ax + 110, ay + 80], [ax + 60, ay + 100]]), PAL['burg2'], lw=2, smooth_path=False)
    ctx.restore()
    ink_shape(ctx, shield, None, lw=4, seed=6)
    # carved wood panelling below
    R(ctx, -40, 1080, 1940, H + 40, PAL['wood'], 2, seed=30)
    for k in range(16):
        px = k * 125 - 30
        R(ctx, px + 12, 1110, px + 112, 1400, shade_c(PAL['wood'], -0.12), 1.6, seed=40 + k, shadow=(shade_c(PAL['wood'], -0.4), 12),
          hatch=(5, 85, 0.9, 0.35))
        ink_line(ctx, np.array([[px + 30, 1140], [px + 62, 1180], [px + 94, 1140]]), 1.2, PAL['wood2'])
        ink_line(ctx, np.array([[px + 30, 1370], [px + 62, 1330], [px + 94, 1370]]), 1.2, PAL['wood2'])
    R(ctx, -40, 1070, 1940, 1100, PAL['wood3'], 2, seed=80)
    save(surf, 'council_wall', 0.2)
    # the council table, front edge: heavy oak covered with a dark cloth
    surf, ctx = canvas(2100, H, 1.5)
    ink_shape(ctx, np.array([[-60, 1330], [2160, 1330], [2160, 1420], [-60, 1420]]), mix(PAL['green3'], PAL['charcoal'], 0.35), lw=3, smooth_path=False,
              shadow=(PAL['charcoal'], 26), hatch=(5, 75, 1.0, 0.35), seed=2)
    ink_shape(ctx, np.array([[-60, 1410], [2160, 1410], [2160, H + 50], [-60, H + 50]]), mix(PAL['green3'], PAL['charcoal'], 0.55), lw=3,
              smooth_path=False, seed=3)
    for k in range(22):
        fx = k * 100 - 40
        ink_line(ctx, np.array([[fx, 1420], [fx + 12, 1700], [fx - 6, H]]), 1.4, PAL['ink'], alpha=0.5)
    for k in range(5):
        lx = 120 + k * 450
        R(ctx, lx - 26, 1600, lx + 26, H + 40, PAL['wood2'], 2, seed=60 + k, shadow=(shade_c(PAL['wood2'], -0.4), 16))
    save(surf, 'council_table', 0.18)


# ----------------------------------------------------------------------------------------------
# Scene 5 - the stage in the market
# ----------------------------------------------------------------------------------------------
def build_cure():
    rng = np.random.default_rng(55)
    surf = sky_surface(1500, H, 52, 0.35, horizon=0.6, storm=0.15)
    save(surf, 'cure_sky', 0.12)
    # back: the grain hall's great roof and the houses round the square
    surf, ctx = canvas(1700, H, 1.25)
    gy = 1180
    x = -80
    i = 0
    while x < 1780:
        wd, top = house_elev(ctx, x, gy, rng.uniform(7, 10), int(rng.integers(3, 5)), 13.0, 1000 + i, kind='gable' if rng.random() < 0.6 else 'eave', fogk=0.3)
        x += wd + rng.uniform(2, 14)
        i += 1
    hx, hw = 400, 900
    ink_shape(ctx, np.array([[hx - 40, gy - 150], [hx + hw + 40, gy - 150], [hx + hw - 120, gy - 520], [hx + 120, gy - 520]]),
              fogc(PAL['roof2'], 0.2), lw=2, smooth_path=False, shadow=(fogc(shade_c(PAL['roof2'], -0.3), 0.2), 80), hatch=(5, 0, 0.9, 0.35), seed=4)
    for row in range(3):
        yy = gy - 200 - row * 100
        for k in range(10 - row * 2):
            dx = hx + 160 + row * 50 + k * (hw - 320 - row * 100) / max(1, 9 - row * 2)
            ink_shape(ctx, np.array([[dx - 16, yy], [dx + 16, yy], [dx, yy - 22]]), fogc(PAL['roof'], 0.2), lw=1, smooth_path=False)
    R(ctx, hx, gy - 150, hx + hw, gy, fogc(mix(PAL['stone'], PAL['burg2'], 0.2), 0.2), 2, seed=7)
    for k in range(6):
        ax = hx + 60 + k * 140
        arch = [[ax, gy], [ax, gy - 80]] + [[ax + 50 + 50 * math.cos(a), gy - 80 - 50 * math.sin(a)] for a in np.linspace(math.pi, 0, 8)[1:-1]] + [[ax + 100, gy - 80], [ax + 100, gy]]
        ink_shape(ctx, np.array(arch), fogc(PAL['charcoal'], 0.2), lw=1.4, smooth_path=False)
    g = cairo.LinearGradient(0, gy, 0, H)
    g.add_color_stop_rgba(0, *mix(PAL['stone2'], PAL['brown'], 0.4)[:3], 1)
    g.add_color_stop_rgba(1, *mix(PAL['stone2'], PAL['brown'], 0.65)[:3], 1)
    ctx.set_source(g)
    ctx.rectangle(-80, gy, 1800, 800)
    ctx.fill()
    ground_texture(ctx, -80, gy, 1700, H + 10, rng)
    save(surf, 'cure_back', 0.2)
    # the wooden stage
    surf, ctx = canvas(1800, H, 1.5)
    sx0, sx1, top, gy2 = 260, 1340, 1380, 1560
    ink_shape(ctx, np.array([[sx0 - 20, top - 16], [sx1 + 20, top - 16], [sx1 + 20, top + 10], [sx0 - 20, top + 10]]), PAL['wood3'], lw=2.5,
              smooth_path=False, seed=1, shadow=(PAL['wood'], 10))
    R(ctx, sx0, top + 10, sx1, gy2, PAL['wood'], 2.5, seed=2, shadow=(PAL['wood2'], 30), hatch=(5, 80, 1.0, 0.4))
    for k in range(18):
        ink_line(ctx, np.array([[sx0 + k * 60, top + 10], [sx0 + k * 60 + 4, gy2]]), 1.2, PAL['wood2'])
    for k in range(5):
        lx = sx0 + 30 + k * (sx1 - sx0 - 60) / 4
        ink_line(ctx, np.array([[lx, top + 10], [lx + 60 * (1 if k % 2 else -1), gy2]]), 4, PAL['wood2'])
    for k in range(6):
        st = [[sx1 + 20 + k * 26, top + 10 + k * 30], [sx1 + 110 + k * 26, top + 10 + k * 30], [sx1 + 110 + k * 26, top + 40 + k * 30],
              [sx1 + 20 + k * 26, top + 40 + k * 30]]
        ink_shape(ctx, np.array(st), PAL['wood3'], lw=1.6, smooth_path=False, seed=20 + k)
    save(surf, 'cure_stage', 0.2)
    # foreground: rope barrier on posts
    surf, ctx = canvas(2000, H, 1.0)
    for k, px in enumerate([60, 700, 1350, 1950]):
        R(ctx, px - 18, 1500, px + 18, H + 40, PAL['wood2'], 3, shadow=(shade_c(PAL['wood2'], -0.4), 14), seed=k)
    ink_line(ctx, np.array([[60, 1520], [380, 1600], [700, 1520], [1020, 1600], [1350, 1520], [1650, 1600], [1950, 1520]]), 7, PAL['parch3'])
    ink_line(ctx, np.array([[60, 1520], [380, 1600], [700, 1520], [1020, 1600], [1350, 1520], [1650, 1600], [1950, 1520]]), 1.6, PAL['ink'])
    save(surf, 'cure_fg', 0.15)


# ----------------------------------------------------------------------------------------------
# Scene 8 - hills, the road and the shrine
# ----------------------------------------------------------------------------------------------
def build_land():
    rng = np.random.default_rng(88)
    surf = sky_surface(1500, H, 83, 0.8, horizon=0.6, storm=0.35)
    save(surf, 'land_sky', 0.12)
    # far hills: the Vosges
    surf, ctx = canvas(1700, H, 1.0)
    for j, (base, amp, col, fk) in enumerate([(1010, 120, PAL['grey2'], 0.5), (1080, 150, PAL['green3'], 0.42)]):
        xs = np.linspace(-80, 1780, 90)
        ys = base - amp * (0.55 + 0.45 * np.sin(xs / (260 - j * 60) + j)) - 30 * np.sin(xs / 73 + j * 2)
        pts = np.vstack([np.stack([xs, ys], 1), [[1780, H + 20], [-80, H + 20]]])
        ink_shape(ctx, pts, fogc(col, fk, PAL['grey2']), lw=1.4, ink=fogc(PAL['ink'], 0.5), smooth_path=True, seed=j,
                  shadow=(fogc(shade_c(col, -0.3), fk, PAL['grey2']), 40), hatch=(5, 30, 0.7, 0.25), light=(-0.3, -1))
    save(surf, 'land_far', 0.2)
    # mid: wooded hillside with the chapel of Saint Vitus
    surf, ctx = canvas(1900, H, 1.25)
    xs = np.linspace(-80, 1980, 120)
    ys = 1180 - 210 * np.exp(-((xs - 1250) / 420) ** 2) - 30 * np.sin(xs / 90)
    pts = np.vstack([np.stack([xs, ys], 1), [[1980, H + 20], [-80, H + 20]]])
    ink_shape(ctx, pts, mix(PAL['green3'], PAL['charcoal'], 0.25), lw=2, smooth_path=True, seed=3,
              shadow=(mix(PAL['green3'], PAL['ink'], 0.5), 60), hatch=(5, 35, 0.8, 0.35), light=(-0.4, -1))
    for k in range(70):
        tx = rng.uniform(-60, 1960)
        ty = np.interp(tx, xs, ys) + rng.uniform(5, 160)
        tree(ctx, tx, ty, rng.uniform(0.6, 1.2), 30 + k)
    chapel(ctx, 1250, float(np.interp(1250, xs, ys)) + 10, 2.1)
    save(surf, 'land_mid', 0.2)
    # near: the road and a bank of grass
    surf, ctx = canvas(2100, H, 1.5)
    xs = np.linspace(-80, 2180, 100)
    ys = 1490 + 30 * np.sin(xs / 300)
    pts = np.vstack([np.stack([xs, ys], 1), [[2180, H + 20], [-80, H + 20]]])
    ink_shape(ctx, pts, mix(PAL['brown'], PAL['stone2'], 0.4), lw=2, smooth_path=True, seed=5)
    for k in range(300):
        rx = rng.uniform(-80, 2180)
        ry = np.interp(rx, xs, ys) + rng.uniform(10, 120)
        ink_line(ctx, np.array([[rx, ry], [rx + rng.uniform(10, 40), ry + rng.uniform(-2, 2)]]), 1.0, PAL['umber'], alpha=0.6)
    ys2 = 1640 + 40 * np.sin(xs / 210 + 1)
    pts = np.vstack([np.stack([xs, ys2], 1), [[2180, H + 20], [-80, H + 20]]])
    ink_shape(ctx, pts, mix(PAL['green3'], PAL['charcoal'], 0.4), lw=2, smooth_path=True, seed=6,
              shadow=(mix(PAL['green3'], PAL['ink'], 0.6), 40), hatch=(5, 70, 0.9, 0.4))
    for k in range(500):
        gx = rng.uniform(-80, 2180)
        gyy = np.interp(gx, xs, ys2) + rng.uniform(-5, 200)
        ink_line(ctx, np.array([[gx, gyy], [gx + rng.uniform(-8, 8), gyy - rng.uniform(15, 40)]]), 1.1, PAL['green3'] if k % 3 else PAL['ink'], alpha=0.8)
    save(surf, 'land_near', 0.2)
    # foreground: a dead tree
    surf, ctx = canvas(2300, H, 1.0)
    dead_tree(ctx, 1700, H + 20, 2.2, 7)
    dead_tree(ctx, 160, H + 20, 1.6, 8)
    save(surf, 'land_fg', 0.15)


def tree(ctx, x, y, s, seed):
    rng = np.random.default_rng(seed)
    R(ctx, x - 4 * s, y - 30 * s, x + 4 * s, y, PAL['wood2'], 1.0)
    pts = []
    for i in range(14):
        a = math.pi + i / 13 * math.pi
        r = (40 + rng.uniform(-8, 8)) * s
        pts.append([x + math.cos(a) * r * 0.6, y - 40 * s + math.sin(a) * r * 1.3])
    pts.append([x + 24 * s, y - 25 * s])
    pts.append([x - 24 * s, y - 25 * s])
    ink_shape(ctx, np.array(pts), mix(PAL['green3'], PAL['charcoal'], 0.35), lw=1.2, seed=seed,
              shadow=(mix(PAL['green3'], PAL['ink'], 0.55), 10 * s), hatch=(4, 50, 0.7, 0.35))


def dead_tree(ctx, x, y, s, seed):
    rng = np.random.default_rng(seed)
    def branch(x0, y0, a, L, w, d):
        x1, y1 = x0 + math.sin(a) * L, y0 - math.cos(a) * L
        taper_stroke(ctx, [[x0, y0], [(x0 + x1) / 2 + rng.uniform(-8, 8) * s, (y0 + y1) / 2], [x1, y1]], w, w * 0.6, PAL['ink'], seed)
        if d > 0:
            for k in range(2):
                branch(x1, y1, a + rng.uniform(-0.8, 0.8), L * rng.uniform(0.55, 0.75), w * 0.6, d - 1)
    branch(x, y, rng.uniform(-0.15, 0.15), 260 * s, 44 * s, 5)


def chapel(ctx, x, gy, s):
    """A small hillside chapel with a bell-cote and a glowing doorway (an artistic reconstruction)."""
    stone = mix(PAL['stone'], PAL['parch2'], 0.25)
    R(ctx, x - 60 * s, gy - 70 * s, x + 50 * s, gy, stone, 1.6, seed=1, shadow=(shade_c(stone, -0.3), 18 * s), hatch=(4, 70, 0.8, 0.35))
    ink_shape(ctx, np.array([[x - 70 * s, gy - 70 * s], [x + 60 * s, gy - 70 * s], [x + 30 * s, gy - 118 * s], [x - 40 * s, gy - 118 * s]]),
              PAL['roof2'], lw=1.6, smooth_path=False, seed=2)
    R(ctx, x - 92 * s, gy - 95 * s, x - 56 * s, gy, stone, 1.6, seed=3)
    ink_shape(ctx, np.array([[x - 96 * s, gy - 95 * s], [x - 52 * s, gy - 95 * s], [x - 74 * s, gy - 140 * s]]), PAL['roof2'], lw=1.6, smooth_path=False)
    ink_line(ctx, np.array([[x - 74 * s, gy - 140 * s], [x - 74 * s, gy - 158 * s]]), 2)
    ink_line(ctx, np.array([[x - 80 * s, gy - 152 * s], [x - 68 * s, gy - 152 * s]]), 2)
    arch = [[x - 84 * s, gy], [x - 84 * s, gy - 26 * s], [x - 74 * s, gy - 40 * s], [x - 64 * s, gy - 26 * s], [x - 64 * s, gy]]
    ink_shape(ctx, np.array(arch), PAL['candle'], lw=1.4, smooth_path=False)
    soft_glow(ctx, x - 74 * s, gy - 20 * s, 60 * s, PAL['candle'], 0.5)
    for k in range(3):
        wx = x - 30 * s + k * 26 * s
        ink_shape(ctx, np.array([[wx - 5 * s, gy - 30 * s], [wx - 5 * s, gy - 52 * s], [wx, gy - 58 * s], [wx + 5 * s, gy - 52 * s], [wx + 5 * s, gy - 30 * s]]),
                  mix(PAL['candle'], PAL['charcoal'], 0.4), lw=1.0, smooth_path=False)


# ----------------------------------------------------------------------------------------------
# Scene 6 - a bird's-eye plan of the city
# ----------------------------------------------------------------------------------------------
MAP_W, MAP_H = 1600, 2400
MAP_STAGE = (980, 1290)
MAP_SPOTS = [(980, 1290), (760, 1050), (1110, 980), (640, 1420), (880, 1600), (1200, 1450), (560, 1200), (1000, 820), (720, 1760),
             (1300, 1180), (460, 1560), (1180, 1700)]


def island_shape(n=80):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    r = 1 + 0.08 * np.sin(3 * a + 1) + 0.05 * np.sin(5 * a)
    return np.stack([800 + np.cos(a) * 560 * r, 1300 + np.sin(a) * 690 * r], 1)


def build_map():
    rng = np.random.default_rng(66)
    surf, ctx = canvas(MAP_W, MAP_H, 1.4)
    set_c(ctx, mix(PAL['parch2'], PAL['green2'], 0.18))
    ctx.paint()
    # fields outside the walls
    for k in range(60):
        x0, y0 = rng.uniform(-100, MAP_W), rng.uniform(-100, MAP_H)
        ink_shape(ctx, np.array([[x0, y0], [x0 + rng.uniform(120, 260), y0 + rng.uniform(-20, 20)], [x0 + rng.uniform(120, 260), y0 + rng.uniform(100, 220)],
                                 [x0 + rng.uniform(-20, 20), y0 + rng.uniform(100, 220)]]), mix(PAL['parch3'], PAL['green2'], rng.uniform(0.1, 0.5)),
                  lw=1.0, smooth_path=False, seed=k, ink=mix(PAL['ink'], PAL['parch3'], 0.5))
        hatch_lines(ctx, x0, y0, x0 + 1, y0 + 1, 7, rng.uniform(0, 180), 0.5, (*PAL['ink'][:3], 0.0))
    isl = island_shape()
    # the Ill: two arms round the old island
    river = PAL['green3']
    outer = isl * 1.0 + (isl - np.array([800, 1300])) * 0.12
    ink_shape(ctx, outer, mix(river, PAL['grey2'], 0.3), lw=2.5, seed=3)
    for k in range(70):
        a = rng.uniform(0, 2 * math.pi)
        p0 = np.array([800 + math.cos(a) * 620, 1300 + math.sin(a) * 760])
        ink_line(ctx, np.array([p0, p0 + np.array([-math.sin(a), math.cos(a)]) * 40]), 0.8, PAL['parch2'], alpha=0.5)
    ink_line(ctx, np.array([[-100, 600], [300, 820], [500, 760]]), 30, mix(river, PAL['grey2'], 0.3))
    ink_line(ctx, np.array([[1100, 2000], [1300, 2200], [1700, 2350]]), 30, mix(river, PAL['grey2'], 0.3))
    # the walls with towers
    wall = isl + (isl - np.array([800, 1300])) * 0.03
    ink_shape(ctx, wall, mix(PAL['parch2'], PAL['brown3'], 0.3), lw=6, seed=4)
    for k in range(0, len(wall), 5):
        q = wall[k]
        ink_shape(ctx, ellipse_pts(q[0], q[1], 14, 14, 10), PAL['stone'], lw=2, shadow=(PAL['stone2'], 5))
    # streets and blocks
    ctx.save()
    path_smooth(ctx, isl * 0.985 + np.array([800, 1300]) * 0.015, True)
    ctx.clip()
    set_c(ctx, mix(PAL['parch2'], PAL['brown3'], 0.25))
    ctx.paint()
    for gx in range(200, 1450, 92):
        for gy in range(560, 2100, 84):
            if hash01(gx, gy) < 0.14:
                continue
            jx, jy = rng.uniform(-10, 10), rng.uniform(-10, 10)
            bw, bh = rng.uniform(52, 80), rng.uniform(48, 70)
            x0, y0 = gx + jx, gy + jy
            # each block: a cluster of roofs with a shaded side (oblique, as in old town plans)
            roof = mix(PAL['roof'], PAL['brown3'], rng.uniform(0, 0.5))
            ink_shape(ctx, np.array([[x0, y0], [x0 + bw, y0 + rng.uniform(-4, 4)], [x0 + bw, y0 + bh], [x0, y0 + bh]]), roof, lw=1.3, smooth_path=False,
                      seed=gx * 7 + gy, shadow=(shade_c(roof, -0.35), 9), hatch=(4, 45, 0.6, 0.35))
            for q in range(2):
                ink_line(ctx, np.array([[x0 + bw * (0.3 + 0.4 * q), y0 + 4], [x0 + bw * (0.3 + 0.4 * q), y0 + bh - 4]]), 0.7, alpha=0.6)
    ctx.restore()
    # the cathedral, drawn large
    cx, cy = 905, 1180
    ink_shape(ctx, np.array([[cx - 30, cy - 150], [cx + 30, cy - 150], [cx + 34, cy + 90], [cx - 34, cy + 90]]), mix(PAL['stone'], PAL['burg2'], 0.3), lw=2.5,
              smooth_path=False, shadow=(mix(PAL['stone2'], PAL['burg2'], 0.3), 14), seed=8)
    ink_shape(ctx, np.array([[cx - 80, cy - 20], [cx + 80, cy - 20], [cx + 80, cy + 20], [cx - 80, cy + 20]]), mix(PAL['stone'], PAL['burg2'], 0.3), lw=2.5,
              smooth_path=False, seed=9)
    ink_shape(ctx, ellipse_pts(cx - 14, cy + 112, 24, 24, 12), mix(PAL['stone'], PAL['burg2'], 0.35), lw=2.5, shadow=(PAL['stone2'], 8))
    ink_shape(ctx, np.array([[cx - 14, cy + 112], [cx - 6, cy + 80], [cx - 22, cy + 80]]), PAL['stone2'], lw=1.5, smooth_path=False)
    # the market where the stage stood
    sx, sy = MAP_STAGE
    ink_shape(ctx, np.array([[sx - 70, sy - 50], [sx + 70, sy - 50], [sx + 70, sy + 50], [sx - 70, sy + 50]]), mix(PAL['parch'], PAL['stone'], 0.5), lw=2,
              smooth_path=False, seed=10)
    R(ctx, sx - 30, sy - 14, sx + 30, sy + 14, PAL['wood3'], 1.5)
    # bridges
    for a in (0.3, 1.5, 2.6, 3.9, 5.1):
        p0 = np.array([800 + math.cos(a) * 560, 1300 + math.sin(a) * 690])
        p1 = np.array([800 + math.cos(a) * 650, 1300 + math.sin(a) * 790])
        ink_line(ctx, np.array([p0, p1]), 14, PAL['wood3'])
        ink_line(ctx, np.array([p0, p1]), 1.4, PAL['ink'])
    # a compass rose and the cartouche border
    rx, ry = 1340, 260
    for k in range(8):
        a = k * math.pi / 4
        L = 90 if k % 2 == 0 else 50
        ink_shape(ctx, np.array([[rx, ry], [rx + math.cos(a + 0.18) * L * 0.25, ry + math.sin(a + 0.18) * L * 0.25], [rx + math.cos(a) * L, ry + math.sin(a) * L],
                                 [rx + math.cos(a - 0.18) * L * 0.25, ry + math.sin(a - 0.18) * L * 0.25]]), PAL['burg3'] if k % 2 == 0 else PAL['parch3'],
                  lw=1.4, smooth_path=False)
    ink_shape(ctx, ellipse_pts(rx, ry, 30, 30, 20), None, lw=2)
    for m in (20, 34):
        ink_shape(ctx, np.array([[m, m], [MAP_W - m, m], [MAP_W - m, MAP_H - m], [m, MAP_H - m]]), None, lw=4 if m == 20 else 1.6, smooth_path=False)
    save(surf, 'map', 0.24)


SETS = {'city': build_city, 'council': build_council, 'cure': build_cure, 'land': build_land, 'map': build_map}

if __name__ == '__main__':
    which = sys.argv[1:] or list(SETS)
    for k in which:
        SETS[k]()
        print('built', k)
