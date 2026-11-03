"""Vector props and environmental effects drawn live every frame: a handcart, baskets, candles with
flickering flames and glow, drifting fog banks, floating dust, chimney smoke, birds, rain of ink."""
import math

import cairo
import numpy as np

from core import (PAL, ink_shape, ink_line, set_c, ellipse_pts, soft_glow, fnoise, hash01, mix, shade_c, fbm2,
                  rgba_to_surface, taper_stroke, path_smooth)


def handcart(ctx, x, y, s, seed=0, boil=0):
    """A two-wheeled handcart with sacks, seen from the side. (x, y) = ground under the axle, s px per cm."""
    wood, wood2 = PAL['wood3'], PAL['wood2']
    def P(pts):
        return np.array([[x + px * s, y + py * s] for px, py in pts])
    sd = seed * 31 + boil * 7
    ink_shape(ctx, P([(-90, -62), (70, -62), (75, -40), (-85, -40)]), wood, lw=max(1.0, 1.2 * s), smooth_path=False, seed=sd, boil=0.5 * s,
              shadow=(shade_c(wood, -0.3), 6 * s))
    for k in range(4):
        ink_line(ctx, P([(-80 + k * 45, -60), (-80 + k * 45, -42)]), max(0.6, 0.6 * s), seed=sd + k)
    ink_shape(ctx, P([(-70, -62), (-50, -98), (-10, -104), (10, -62)]), PAL['parch3'], lw=max(1.0, 1.1 * s), seed=sd + 5, boil=0.5 * s,
              shadow=(shade_c(PAL['parch3'], -0.3), 8 * s))
    ink_shape(ctx, P([(0, -62), (14, -94), (52, -100), (62, -62)]), PAL['parch2'], lw=max(1.0, 1.1 * s), seed=sd + 6, boil=0.5 * s,
              shadow=(shade_c(PAL['parch2'], -0.3), 8 * s))
    ink_line(ctx, P([(-85, -50), (-160, -20)]), max(1.2, 2.6 * s), wood2, seed=sd + 8)
    ink_line(ctx, P([(-85, -56), (-160, -28)]), max(1.2, 2.6 * s), wood2, seed=sd + 9)
    wheel = np.array([[x + math.cos(a) * 34 * s, y - 34 * s + math.sin(a) * 34 * s] for a in np.linspace(0, 2 * math.pi, 20, endpoint=False)])
    ink_shape(ctx, wheel, None, lw=max(1.4, 3.0 * s), seed=sd + 10, boil=0.5 * s)
    for a in np.linspace(0, math.pi, 4, endpoint=False):
        ink_line(ctx, np.array([[x + math.cos(a) * 33 * s, y - 34 * s + math.sin(a) * 33 * s],
                                [x - math.cos(a) * 33 * s, y - 34 * s - math.sin(a) * 33 * s]]), max(0.8, 1.4 * s), wood2, seed=sd + 11)


def candle(ctx, x, y, s, t, seed=0, glow=1.0, h=26.0):
    """A tallow candle on a pewter stick; the flame flickers, its glow breathes."""
    fl = 0.75 + 0.25 * fnoise(t * 6 + seed, seed) + 0.08 * math.sin(t * 31 + seed)
    sway = 2.0 * fnoise(t * 3 + seed * 2, seed + 4)
    if glow > 0:
        soft_glow(ctx, x, y - h * s - 6 * s, 160 * s * fl, PAL['candle'], 0.20 * glow)
        soft_glow(ctx, x, y - h * s - 6 * s, 45 * s * fl, PAL['candle2'], 0.35 * glow)
    ink_shape(ctx, np.array([[x - 11 * s, y], [x + 11 * s, y], [x + 6 * s, y - 4 * s], [x + 2 * s, y - 6 * s], [x - 2 * s, y - 6 * s],
                             [x - 6 * s, y - 4 * s]]), PAL['grey'], lw=max(0.8, 1.0 * s), smooth_path=False)
    ink_shape(ctx, np.array([[x - 3.5 * s, y - 6 * s], [x + 3.5 * s, y - 6 * s], [x + 3.5 * s, y - h * s], [x - 3.5 * s, y - h * s]]),
              PAL['linen'], lw=max(0.8, 1.0 * s), smooth_path=False, shadow=(PAL['linen2'], 2 * s))
    tip = (x + sway * s, y - h * s - 15 * s * fl)
    flame = np.array([[x - 2.6 * s, y - h * s - 1.5 * s], [x - 2.4 * s + sway * 0.4 * s, y - h * s - 8 * s * fl], tip,
                      [x + 2.4 * s + sway * 0.4 * s, y - h * s - 8 * s * fl], [x + 2.6 * s, y - h * s - 1.5 * s]])
    ink_shape(ctx, flame, PAL['candle2'], lw=max(0.6, 0.6 * s), ink=PAL['burg2'], seed=seed)
    ink_shape(ctx, np.array(flame) * 0.0 + np.array([[x - 1.0 * s, y - h * s - 2 * s], [x - 0.8 * s, y - h * s - 6 * s],
                                                     [x + sway * 0.6 * s, y - h * s - 10 * s * fl], [x + 0.8 * s, y - h * s - 6 * s],
                                                     [x + 1.0 * s, y - h * s - 2 * s]]), (1.0, 0.97, 0.85, 1.0), lw=0)
    return fl


_FOG = {}


def fog_tex(seed=1, w=1400, h=900):
    key = (seed, w, h)
    if key not in _FOG:
        n = fbm2(h, w, seed, scale=w / 3.5, octaves=5)
        a = np.clip((n - 0.35) * 1.6, 0, 1) ** 1.3
        # soft top and bottom
        yy = np.linspace(0, 1, h)[:, None]
        a *= np.sin(np.pi * yy) ** 0.8
        rgba = np.zeros((h, w, 4), np.float32)
        rgba[..., 0], rgba[..., 1], rgba[..., 2] = 0.74, 0.72, 0.68
        rgba[..., 3] = a
        _FOG[key] = rgba_to_surface(rgba)
    return _FOG[key]


def fog_bank(ctx, x, y, w, h, alpha, t, speed=12.0, seed=1, col=None):
    """A drifting fog band drawn from a tiling noise texture."""
    tex = fog_tex(seed)
    tw, th = tex.get_width(), tex.get_height()
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    off = (t * speed) % tw
    sx, sy = w / tw * 1.4, h / th
    for k in (-1, 0, 1):
        ctx.save()
        ctx.translate(x + (k * tw - off) * sx, y)
        ctx.scale(sx, sy)
        ctx.set_source_surface(tex, 0, 0)
        ctx.paint_with_alpha(alpha)
        ctx.restore()
    ctx.restore()


def dust(ctx, t, x0, y0, x1, y1, n=40, seed=3, size=2.0, col=None, alpha=0.5, speed=8.0):
    """Floating dust motes catching the light."""
    col = col or PAL['candle2']
    for i in range(n):
        bx = hash01(seed, i, 1)
        by = hash01(seed, i, 2)
        x = x0 + (x1 - x0) * ((bx + 0.01 * t * speed * (0.5 + hash01(seed, i, 3)) / 10) % 1.0)
        y = y0 + (y1 - y0) * ((by - 0.006 * t * speed * hash01(seed, i, 4) / 10) % 1.0)
        x += 6 * math.sin(t * 0.7 + i)
        tw = 0.5 + 0.5 * math.sin(t * (1.5 + hash01(seed, i, 5) * 2) + i)
        r = size * (0.6 + hash01(seed, i, 6))
        ctx.arc(x, y, r, 0, 2 * math.pi)
        set_c(ctx, col, alpha * tw)
        ctx.fill()


def smoke(ctx, x, y, s, t, seed=0, alpha=0.5):
    """A chimney smoke plume: a chain of inked puffs drifting and swelling."""
    for k in range(7):
        u = ((t * 0.18 + k / 7 + hash01(seed, k) * 0.05) % 1.0)
        px = x + (u * 60 + 14 * math.sin(u * 6 + t + seed)) * s
        py = y - u * 160 * s
        r = (8 + 26 * u) * s
        a = alpha * (1 - u) * min(1, u * 5)
        pts = ellipse_pts(px, py, r, r * 0.8, 14)
        pts = pts + np.array([[3 * s * math.sin(i * 1.7 + t), 3 * s * math.cos(i * 2.3 + t)] for i in range(len(pts))])
        ink_shape(ctx, pts, (*PAL['grey3'][:3], a), lw=max(0.5, 0.8 * s), ink=(*PAL['grey2'][:3], a), seed=seed + k)


def bird(ctx, x, y, s, t, seed=0):
    f = math.sin(t * 9 + seed)
    ink_line(ctx, np.array([[x - 9 * s, y - 3 * s * f], [x - 3 * s, y], [x, y + 1 * s], [x + 3 * s, y], [x + 9 * s, y - 3 * s * f]]),
             max(0.8, 1.2 * s), PAL['ink'])


def ink_splats(ctx, cx, cy, r, seed, alpha=1.0, col=None):
    """Ink splatter dots around a point (stamps and blooms)."""
    col = col or PAL['ink']
    for i in range(18):
        a = hash01(seed, i) * 2 * math.pi
        d = r * (0.8 + hash01(seed, i, 2) * 0.8)
        rr = r * 0.04 * (0.4 + hash01(seed, i, 3))
        ctx.arc(cx + math.cos(a) * d, cy + math.sin(a) * d, rr, 0, 2 * math.pi)
        set_c(ctx, col, alpha)
        ctx.fill()
