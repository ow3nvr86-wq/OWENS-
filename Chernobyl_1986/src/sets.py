"""Painted background layers for the Chernobyl Short, drawn once into assets/layers/ as PNG depth layers
(skies, far and middle forest, the forest edge above the beach, the low island on the horizon, a
foreground live oak, the map of the coast). The planes the camera pushes into are drawn live every frame
(src/scenes.py), so they stay sharp at any zoom.

  python src/sets.py            # all layers
  python src/sets.py map        # one
"""
import math
import os
import sys

import cairo
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import (PAL, W, H, LAYERS, FONTS, new_surface, surf_array, set_c, ink_shape, ink_line, hatch_lines, mix, shade_c, hash01,
                  path_poly, path_smooth, ellipse_pts, taper_stroke, soft_glow, fbm2, rgba_to_surface)
import world as Wd
import soviet as S


def sky_surface(w, h, seed=3, dark=0.0, horizon=0.55, storm=0.0):
    """A painted sky: soft cloud masses from stretched fractal noise, lit from above and shaded below,
    over a gradient that brightens to a haze at the horizon."""
    from core import rgba_to_surface
    hh, ww = int(h), int(w)
    n = fbm2(hh, ww // 3 + 2, seed, scale=max(20, ww / 9), octaves=6)
    from scipy import ndimage
    n = ndimage.zoom(n, (1, ww / n.shape[1]), order=1)[:hh, :ww]
    yy = np.linspace(0, 1, hh)[:, None]
    dens = np.clip((n - 0.42 + 0.25 * storm) * 2.2, 0, 1) * np.clip(1.2 - yy / horizon * 0.9, 0, 1)
    shade = np.clip(np.roll(dens, -int(hh * 0.012), axis=0) - dens, -1, 1)
    top = np.array(mix(PAL['grey2'], PAL['skyd'], dark)[:3])
    bot = np.array(mix(mix(PAL['grey3'], PAL['parch2'], 0.35), PAL['grey2'], dark)[:3])
    g = np.clip(yy / horizon, 0, 1)
    base = top[None, None, :] * (1 - g[..., None]) + bot[None, None, :] * g[..., None]
    lightc = np.array(mix(mix(PAL['parch2'], PAL['grey3'], 0.5), PAL['grey2'], dark * 0.8)[:3])
    darkc = np.array(mix(PAL['grey2'], PAL['charcoal'], 0.35 + 0.5 * dark)[:3])
    cloud = lightc[None, None, :] * (1 - dens[..., None] * 0.6) + darkc[None, None, :] * (dens[..., None] * 0.6)
    cloud = cloud + shade[..., None] * 0.25
    img = base * (1 - dens[..., None] * 0.85) + cloud * dens[..., None] * 0.85
    rgba = np.concatenate([np.clip(img, 0, 1), np.ones((hh, ww, 1))], 2).astype(np.float32)
    surf = rgba_to_surface(rgba)
    ctx = cairo.Context(surf)
    # engraved strokes in the cloud undersides
    rng = np.random.default_rng(seed)
    for i in range(int(ww * hh / 1400)):
        x, y = rng.uniform(0, ww), rng.uniform(0, hh * horizon * 1.05)
        if dens[int(min(y, hh - 1)), int(min(x, ww - 1))] > 0.45 and shade[int(min(y, hh - 1)), int(min(x, ww - 1))] < 0.0:
            L = rng.uniform(10, 34) * ww / 1080
            ink_line(ctx, np.array([[x, y], [x + L, y + rng.uniform(-1, 1)]]), 0.8 * ww / 1080, PAL['ink'], alpha=0.22)
    return surf


def feather(surf, px):
    """Fade the edges of a patch layer to transparent so it blends into the layer beneath."""
    a = surf_array(surf)
    h, w = a.shape[:2]
    yy = np.minimum(np.arange(h), np.arange(h)[::-1])[:, None] / px
    xx = np.minimum(np.arange(w), np.arange(w)[::-1])[None, :] / px
    m = np.clip(np.minimum(yy, xx), 0, 1)
    m = m * m * (3 - 2 * m)
    for ch in range(4):
        a[..., ch] = (a[..., ch] * m).astype(np.uint8)
    surf.mark_dirty()


def texturize(surf, seed=0, amount=0.22, speck=0.5):
    """Give flat vector fills the mottled, printed texture of an aged engraving: low-frequency
    blotches, fine grain and a few ink specks, multiplied into the colour (alpha untouched)."""
    a = surf_array(surf)
    h, w = a.shape[:2]
    n1 = fbm2(h, w, seed=int(seed) % 10000, scale=max(40, w / 14), octaves=5)
    n2 = np.random.default_rng(int(seed) + 1).random((h, w)).astype(np.float32)
    m = (1 - amount) + amount * 1.25 * n1 + 0.06 * (n2 - 0.5)
    m = np.clip(m, 0.55, 1.12)
    sp = (n2 > 1 - 0.0009 * speck)
    for ch in range(3):
        v = a[..., ch].astype(np.float32) * m
        v[sp] *= 0.35
        a[..., ch] = np.minimum(v, a[..., 3]).astype(np.uint8)
    surf.mark_dirty()


def save(surf, name, tex=0.22):
    texturize(surf, hash01(len(name), 7) * 1000, amount=tex)
    os.makedirs(LAYERS, exist_ok=True)
    surf.write_to_png(os.path.join(LAYERS, name + '.png'))


def canvas(w, h, scale):
    surf = new_surface(int(w * scale), int(h * scale))
    ctx = cairo.Context(surf)
    ctx.scale(scale, scale)
    return surf, ctx


FOG = mix(PAL['grey3'], PAL['parch2'], 0.3)


def build_skies():
    for name, seed, dark, storm, hz in (('sky_dusk', 11, 0.35, 0.25, 0.62), ('sky_day', 12, 0.0, 0.0, 0.6), ('sky_grey', 13, 0.15, 0.35, 0.6),
                                         ('sky_night', 14, 0.95, 0.3, 0.6), ('sky_storm', 15, 0.6, 0.9, 0.62), ('sky_dawn', 16, 0.2, 0.15, 0.6)):
        sk = sky_surface(1500, 1500, seed, dark, horizon=hz, storm=storm)
        save(sk, name, 0.12)


def build_pines_far():
    """A far, fogged line of pine forest on the flat land around the plant (depth about 0.3)."""
    surf, ctx = canvas(2600, 1500, 1.0)
    rng = np.random.default_rng(3)
    gy = 1460
    ink_shape(ctx, np.array([[0, gy], [2600, gy - 10], [2600, 1500], [0, 1500]]), Wd.fogc(PAL['green3'], 0.65, FOG), lw=0)
    for i in range(110):
        Wd.pine(ctx, rng.uniform(-40, 2640), gy + rng.uniform(-6, 6), rng.uniform(150, 300), 100 + i, fog=0.62, fogcol=FOG, lw=0.8, detail=False)
    save(surf, 'pines_far', 0.16)


def build_city_far(night=False):
    """Pripyat on the horizon: rows of 9- and 16-storey blocks, fogged (depth about 0.25)."""
    surf, ctx = canvas(2600, 1500, 1.0)
    rng = np.random.default_rng(7)
    gy = 1460
    fog = 0.5 if not night else 0.35
    fc = FOG if not night else mix(PAL['charcoal'], PAL['grey2'], 0.4)
    x = 0
    while x < 2600:
        floors = int(rng.choice([9, 9, 12, 16, 5]))
        wm = rng.uniform(28, 70) if floors < 16 else rng.uniform(16, 24)
        S.panel_block(ctx, x, gy - rng.uniform(0, 30), wm, floors, 5.0, 300 + int(x), lit=0.45 if night else 0.0, night=1.0 if night else 0.0,
                      fog=fog, fogcol=fc, lw=0.7)
        x += wm * 5.0 + rng.uniform(10, 60)
    for i in range(50):
        Wd.pine(ctx, rng.uniform(0, 2600), gy + 4, rng.uniform(60, 130), 500 + i, fog=fog + 0.1, fogcol=fc, lw=0.6, detail=False)
    save(surf, 'city_far_night' if night else 'city_far', 0.12)


def build_street(decay=0.0, name='street_blocks'):
    """A street of Pripyat: apartment blocks set back behind a row of trees (depth about 0.6)."""
    surf, ctx = canvas(3200, 1520, 1.0)
    rng = np.random.default_rng(11)
    gy = 1470
    ink_shape(ctx, np.array([[0, gy], [3200, gy], [3200, 1520], [0, 1520]]), mix(PAL['green2'], PAL['parch3'], 0.3 + 0.2 * decay), lw=0)
    x = -40
    k = 0
    while x < 3200:
        floors = [9, 5, 9, 16][k % 4]
        wm = [42, 36, 40, 20][k % 4]
        sc = 18.0 if floors < 16 else 13.0
        S.panel_block(ctx, x, gy - 40 + rng.uniform(-10, 10), wm, floors, sc, 20 + k, decay=decay, laundry=0.35 * (1 - decay),
                      fog=0.15, fogcol=FOG, lw=1.1)
        x += wm * sc + rng.uniform(120, 240)
        k += 1
    for i in range(12 + int(14 * decay)):
        S.poplar(ctx, rng.uniform(-50, 3250), gy + rng.uniform(-4, 8), rng.uniform(300, 420) * (1 + 0.7 * decay), 700 + i, fog=0.1, fogcol=FOG, lw=1.0)
    if decay > 0:
        for i in range(40):
            Wd.oak(ctx, rng.uniform(0, 3200), gy + 10, rng.uniform(160, 300), 900 + i, fog=0.08, fogcol=FOG, lw=1.0, moss=False, detail=False)
    Wd.grass_tufts(ctx, 0, 3200, gy + 12, 200 + int(400 * decay), 1.2 + 1.5 * decay, 9)
    save(surf, name, 0.2)


def build_school():
    """A school building (a long three-storey block with tall windows) behind a low fence."""
    surf, ctx = canvas(2600, 1520, 1.0)
    gy = 1470
    rng = np.random.default_rng(5)
    ink_shape(ctx, np.array([[0, gy], [2600, gy], [2600, 1520], [0, 1520]]), mix(PAL['green2'], PAL['parch3'], 0.3), lw=0)
    S.panel_block(ctx, 1500, gy - 120, 40, 9, 15.0, 62, fog=0.25, fogcol=FOG, lw=1.0, laundry=0.4)
    S.panel_block(ctx, 60, gy - 20, 66, 4, 18.0, 61, fog=0.1, fogcol=FOG, lw=1.1)
    for i in range(7):
        S.poplar(ctx, rng.uniform(0, 2600), gy + 2, rng.uniform(380, 520), 760 + i, fog=0.1, fogcol=FOG, lw=1.0)
    for i in range(80):
        x = 40 + i * 32
        ink_line(ctx, np.array([[x, gy + 10], [x, gy - 50]]), 2.2, PAL['charcoal2'])
    ink_line(ctx, np.array([[40, gy - 40], [2600, gy - 40]]), 2.2, PAL['charcoal2'])
    Wd.grass_tufts(ctx, 0, 2600, gy + 12, 160, 1.2, 9)
    save(surf, 'school', 0.2)


def build_aerial():
    """Pripyat from above: the roofs of the blocks among trees grown over the city (an illustration)."""
    surf, ctx = canvas(1600, 2600, 1.0)
    rng = np.random.default_rng(21)
    set_c(ctx, mix(PAL['green3'], PAL['green2'], 0.4))
    ctx.paint()
    for i in range(1400):
        x, y = rng.uniform(-40, 1640), rng.uniform(-40, 2640)
        r = rng.uniform(14, 40)
        g = mix(PAL['green3'], PAL['green'], rng.random())
        ink_shape(ctx, ellipse_pts(x, y, r, r * 0.9, 12), g, lw=0.8, seed=i, shadow=(shade_c(g, -0.3), r * 0.4), light=(-1, -1))
    for k in range(5):
        y = 200 + k * 520
        ink_shape(ctx, np.array([[-40, y], [1640, y + 40], [1640, y + 80], [-40, y + 40]]), mix(PAL['grey2'], PAL['green3'], 0.3), lw=1.0, smooth_path=False)
    for i in range(46):
        x, y = rng.uniform(40, 1500), rng.uniform(40, 2500)
        w, h = (rng.uniform(260, 420), rng.uniform(46, 60)) if rng.random() < 0.7 else (rng.uniform(46, 60), rng.uniform(200, 340))
        roof = mix(PAL['grey3'], PAL['grey'], rng.random())
        ink_shape(ctx, np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]]), roof, lw=1.2, smooth_path=False,
                  shadow=(shade_c(roof, -0.25), 6))
        ink_shape(ctx, np.array([[x + w, y + 8], [x + w + 18, y + 26], [x + w + 18, y + h + 18], [x + 18, y + h + 18], [x, y + h]]),
                  (0, 0, 0, 0.35), lw=0, smooth_path=False)
        for j in range(int(w / 50)):
            ink_shape(ctx, np.array([[x + 16 + j * 50, y + 12], [x + 34 + j * 50, y + 12], [x + 34 + j * 50, y + 24], [x + 16 + j * 50, y + 24]]),
                      shade_c(roof, -0.2), lw=0.6, smooth_path=False)
    # the funfair's wheel seen from above, and the square
    S.ferris_wheel(ctx, 900, 1300, 80, 0.0, lw=1.0)
    save(surf, 'aerial', 0.15)


BUILDERS = {'skies': build_skies, 'pines_far': build_pines_far, 'city_far': build_city_far, 'city_far_night': lambda: build_city_far(True),
            'street': build_street, 'street_empty': lambda: build_street(0.8, 'street_empty'), 'school': build_school, 'aerial': build_aerial}

if __name__ == '__main__':
    import time
    names = sys.argv[1:] or list(BUILDERS)
    for n in names:
        t0 = time.time()
        BUILDERS[n]()
        print(f'{n}: {time.time() - t0:.1f}s', flush=True)
