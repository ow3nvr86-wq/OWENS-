"""Painted background layers for the Roanoke Short, drawn once into assets/layers/ as PNG depth layers
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
    """A far, fogged line of pines on a low rise (depth about 0.35)."""
    surf, ctx = canvas(2600, 1500, 1.0)
    rng = np.random.default_rng(3)
    gy = 1460
    ink_shape(ctx, np.array([[0, gy], [2600, gy - 10], [2600, 1500], [0, 1500]]), Wd.fogc(PAL['green3'], 0.65, FOG), lw=0)
    for i in range(70):
        x = rng.uniform(-40, 2640)
        Wd.pine(ctx, x, gy + rng.uniform(-6, 6), rng.uniform(380, 640), 100 + i, fog=0.62, fogcol=FOG, lw=0.9, detail=False)
    for i in range(10):
        Wd.oak(ctx, rng.uniform(0, 2600), gy + 4, rng.uniform(260, 360), 300 + i, fog=0.6, fogcol=FOG, lw=0.9, detail=False, moss=False)
    save(surf, 'pines_far', 0.16)


def build_woods_mid():
    """The forest close behind the clearing: pines, live oaks with moss, palmetto (depth about 0.6)."""
    surf, ctx = canvas(2600, 1520, 1.0)
    rng = np.random.default_rng(5)
    gy = 1470
    ink_shape(ctx, np.array([[0, gy], [2600, gy], [2600, 1520], [0, 1520]]), Wd.fogc(PAL['green3'], 0.35, FOG), lw=0)
    for i in range(26):
        x = rng.uniform(-60, 2660)
        Wd.pine(ctx, x, gy + rng.uniform(-4, 8), rng.uniform(760, 1100), 200 + i, fog=0.32, fogcol=FOG, lw=1.1)
    for i in range(9):
        Wd.oak(ctx, rng.uniform(0, 2600), gy + 6, rng.uniform(420, 560), 400 + i, fog=0.3, fogcol=FOG, lw=1.1)
    for i in range(30):
        Wd.palmetto(ctx, rng.uniform(0, 2600), gy + 10, rng.uniform(0.9, 1.4), 500 + i, fog=0.3, fogcol=FOG)
    Wd.grass_tufts(ctx, 0, 2600, gy + 12, 120, 1.0, 9, fog=0.3, fogcol=FOG)
    save(surf, 'woods_mid', 0.2)


def build_shore():
    """The forest edge of Roanoke Island above the beach: dunes with grass, pines and oaks (depth 0.6)."""
    surf, ctx = canvas(2600, 1400, 1.0)
    rng = np.random.default_rng(8)
    gy = 1230
    for i in range(34):
        x = rng.uniform(-60, 2660)
        Wd.pine(ctx, x, gy + rng.uniform(-10, 10), rng.uniform(520, 820), 600 + i, fog=0.25, fogcol=FOG, lw=1.1)
    for i in range(8):
        Wd.oak(ctx, rng.uniform(0, 2600), gy + 10, rng.uniform(330, 460), 700 + i, fog=0.25, fogcol=FOG, lw=1.1)
    # the dune ridge
    pts = [[x, gy + 20 + 22 * math.sin(x * 0.006) + 10 * math.sin(x * 0.021)] for x in np.linspace(-20, 2620, 60)]
    sand = mix(PAL['parch2'], PAL['parch3'], 0.35)
    ink_shape(ctx, np.array(pts + [[2620, 1400], [-20, 1400]]), sand, lw=1.2, smooth_path=False, shadow=(shade_c(sand, -0.15), 14),
              light=(0, -1))
    Wd.grass_tufts(ctx, 0, 2600, gy + 26, 160, 1.3, 10, col=mix(PAL['green2'], PAL['parch3'], 0.4))
    for i in range(18):
        Wd.palmetto(ctx, rng.uniform(0, 2600), gy + 22, rng.uniform(1.0, 1.4), 800 + i, fog=0.2, fogcol=FOG)
    # the wooded point tapers away on the left
    a = surf_array(surf)
    ramp_ = np.clip(np.arange(a.shape[1]) / 340.0, 0, 1) ** 1.5
    for ch in range(4):
        a[..., ch] = (a[..., ch] * ramp_[None, :]).astype(np.uint8)
    surf.mark_dirty()
    save(surf, 'shore_mid', 0.18)


def build_island_strip():
    """A low wooded island on the horizon, seen from the sea (depth about 0.2)."""
    surf, ctx = canvas(3000, 300, 1.0)
    rng = np.random.default_rng(12)
    gy = 280
    for i in range(160):
        Wd.pine(ctx, rng.uniform(300, 3000), gy, rng.uniform(70, 140), 900 + i, fog=0.6, fogcol=FOG, lw=0.6, detail=False)
    pts = [[x, gy - 6 + 5 * math.sin(x * 0.01)] for x in np.linspace(250, 3000, 40)]
    ink_shape(ctx, np.array(pts + [[3000, 300], [250, 300]]), Wd.fogc(PAL['green3'], 0.6, FOG), lw=0, smooth_path=False)
    save(surf, 'island_strip', 0.1)


def build_fg_oak():
    """A huge live-oak trunk and limb for the foreground (depth about 1.3), hung with moss."""
    surf, ctx = canvas(900, 1920, 1.0)
    trunk = mix(PAL['wood2'], PAL['charcoal'], 0.45)
    pts = [[-40, 1920], [-30, 900], [10, 560], [120, 380], [330, 260], [620, 200], [900, 180], [900, 290], [640, 300], [380, 380],
           [230, 520], [170, 760], [190, 1920]]
    ink_shape(ctx, np.array(pts), trunk, lw=2.4, seed=3, shadow=(shade_c(trunk, -0.45), 60), hatch=(5, 70, 1.2, 0.45), light=(-1, -0.4))
    rng = np.random.default_rng(4)
    for k in range(60):
        y = rng.uniform(600, 1900)
        x = rng.uniform(0, 160)
        ink_line(ctx, np.array([[x, y], [x + rng.uniform(-6, 6), y + rng.uniform(30, 90)]]), 1.4, PAL['ink'], alpha=0.5)
    save(surf, 'fg_oak', 0.2)


def build_grass_strip():
    surf, ctx = canvas(2800, 220, 1.0)
    Wd.grass_tufts(ctx, 0, 2800, 200, 260, 1.6, 31, col=mix(PAL['green3'], PAL['parch3'], 0.3))
    Wd.grass_tufts(ctx, 0, 2800, 214, 200, 2.0, 32, col=mix(PAL['green3'], PAL['charcoal'], 0.3))
    save(surf, 'grass_strip', 0.15)


# ----------------------------------------------------------------------------------------------
# The map of the coast (in the manner of a 1580s chart; an illustration, not a survey)
# ----------------------------------------------------------------------------------------------
MAP_W, MAP_H = 1600, 2600
# key places in map units
MAP_PTS = {'roanoke': (930, 1060), 'croatoan': (1180, 1900), 'cape': (1290, 1860), 'sitex': (430, 640), 'chesapeake': (760, 120),
           'mainland_vil': (560, 1150), 'hatteras_vil': (1170, 1930)}


def _coast():
    """Outlines in map units: the mainland (left), the barrier islands (right, a long curve with the
    elbow of Cape Hatteras), Roanoke Island between them."""
    main = [(0, 0), (700, 0), (690, 200), (640, 380), (700, 470), (860, 520), (900, 600), (760, 640), (600, 600), (470, 560),
            (380, 600), (330, 700), (420, 760), (600, 780), (780, 820), (860, 900), (850, 1000), (820, 1120), (760, 1260),
            (700, 1400), (600, 1560), (560, 1720), (480, 1900), (420, 2100), (360, 2300), (300, 2600), (0, 2600)]
    banks = []
    for i in range(60):
        u = i / 59
        y = 60 + u * 1830
        x = 1000 + 180 * u + 120 * math.sin(u * 2.4) + 40 * math.sin(u * 11)
        banks.append((x, y))
    # the cape: bend back west towards Ocracoke
    banks += [(1300, 1880), (1250, 1960), (1100, 2040), (940, 2140), (800, 2260)]
    outer = [(x + 38 + 8 * math.sin(i * 0.9), y) for i, (x, y) in enumerate(banks)]
    inner = [(x - 4, y) for (x, y) in banks]
    island = [(x, y) for x, y in ellipse_pts(930, 1060, 34, 92, 22)]
    return main, inner, outer, island


def build_map():
    from PIL import Image, ImageDraw, ImageFont
    sc = 1.0
    surf, ctx = canvas(MAP_W, MAP_H, sc)
    sea = mix(PAL['parch2'], PAL['grey3'], 0.25)
    set_c(ctx, sea)
    ctx.paint()
    hatch_lines(ctx, 0, 0, MAP_W, MAP_H, 9, 0, 0.6, (*PAL['ink'][:3], 0.12), 3)
    main, inner, outer, island = _coast()
    land = mix(PAL['parch'], PAL['parch2'], 0.25)
    ink_shape(ctx, np.array(main), land, lw=2.4, seed=1, shadow=(shade_c(land, -0.08), 18))
    # water-lining along the mainland shore, as on old charts
    for k in range(1, 5):
        P = np.array(main[1:-1]) + np.array([k * 7, 0])
        ink_line(ctx, P, 0.8, PAL['ink'], alpha=0.35 - k * 0.06)
    banks = np.array(outer + inner[::-1])
    ink_shape(ctx, banks, land, lw=2.0, smooth_path=True, seed=2)
    ink_shape(ctx, np.array(island), land, lw=2.0, seed=3)
    # rivers into Albemarle Sound: the Chowan and the Roanoke
    for pts in ([(520, 590), (480, 420), (500, 260), (450, 60)], [(390, 640), (250, 700), (120, 760), (0, 790)]):
        ink_line(ctx, np.array(pts), 3.0, mix(sea, PAL['ink'], 0.3))
    # woods drawn as small tree symbols; and the native villages as rings of houses
    rng = np.random.default_rng(4)
    tmp = cairo.Context(new_surface(4, 4))
    path_poly(tmp, np.array(main))
    for k in range(420):
        x, y = rng.uniform(10, 860), rng.uniform(10, 2580)
        if not tmp.in_fill(x, y):
            continue
        ink_line(ctx, np.array([[x, y], [x, y - 12]]), 1.0, PAL['ink'], alpha=0.5)
        ink_shape(ctx, ellipse_pts(x, y - 16, 6, 7, 10), mix(PAL['green2'], PAL['parch2'], 0.5), lw=0.8, seed=k)
    for k in range(70):
        u = rng.uniform(0.02, 0.98)
        i = int(u * (len(inner) - 1))
        x, y = inner[i]
        ink_shape(ctx, ellipse_pts(x + 12, y - 6, 4, 5, 8), mix(PAL['green2'], PAL['parch2'], 0.5), lw=0.7, seed=k)
    # compass rose
    cx, cy = 1360, 2380
    for a in range(16):
        L = 90 if a % 4 == 0 else (55 if a % 2 == 0 else 35)
        ang = a * math.pi / 8
        tip = (cx + math.sin(ang) * L, cy - math.cos(ang) * L)
        l = (cx + math.sin(ang - 0.25) * 12, cy - math.cos(ang - 0.25) * 12)
        r = (cx + math.sin(ang + 0.25) * 12, cy - math.cos(ang + 0.25) * 12)
        ink_shape(ctx, np.array([l, tip, r, (cx, cy)]), PAL['burg'] if a % 4 == 0 else PAL['parch'], lw=1.0, smooth_path=False)
    ctx.arc(cx, cy, 104, 0, 2 * math.pi)
    set_c(ctx, PAL['ink'], 0.6)
    ctx.set_line_width(1.2)
    ctx.stroke()
    # a sea serpent's coil and a small ship, chart ornaments
    Wd.ship(ctx, 1420, 1400, 0.3, 0.0, 5, lw=1.0)
    Wd.ship(ctx, 1380, 700, 0.22, 0.0, 6, kind='pinnace', lw=0.8)
    # border
    for k, wdt in ((14, 6), (30, 1.4)):
        ctx.rectangle(k, k, MAP_W - 2 * k, MAP_H - 2 * k)
        set_c(ctx, PAL['ink'])
        ctx.set_line_width(wdt)
        ctx.stroke()
    texturize(surf, 77, amount=0.07)
    # place names with PIL (IM Fell, the chart's old-style lettering)
    a = surf_array(surf)
    im = Image.fromarray(a[..., [2, 1, 0, 3]].copy(), 'RGBA')
    d = ImageDraw.Draw(im)
    fi = ImageFont.truetype(os.path.join(FONTS, 'IMFellEnglish-Italic.ttf'), 44)
    fs = ImageFont.truetype(os.path.join(FONTS, 'IMFellEnglishSC-Regular.ttf'), 46)
    fb = ImageFont.truetype(os.path.join(FONTS, 'IMFellEnglishSC-Regular.ttf'), 70)
    ink = (27, 23, 19, 255)
    for txt, (x, y), f in (('Roanoke', (990, 1020), fs), ('Croatoan', (1040, 1990), fs), ('Hatorask', (1100, 700), fi),
                           ('The Main', (150, 1250), fb), ('Albemarle Sound', (420, 470), fi), ('Pamlico Sound', (700, 1560), fi),
                           ('Mare Atlanticum', (1250, 1150), fi), ('Chowan R.', (330, 300), fi), ('to Chesapeake', (560, 60), fi)):
        if txt == 'Mare Atlanticum':
            tmp = Image.new('RGBA', (600, 80), (0, 0, 0, 0))
            ImageDraw.Draw(tmp).text((0, 0), txt, font=f, fill=ink)
            tmp = tmp.rotate(80, expand=True)
            im.alpha_composite(tmp, (x, y - 200))
            continue
        d.text((x, y), txt, font=f, fill=ink)
    # cartouche
    d.rectangle([90, 2280, 700, 2500], fill=(226, 211, 178, 255), outline=ink, width=4)
    d.rectangle([104, 2294, 686, 2486], outline=ink, width=1)
    d.text((130, 2310), 'Virginia', font=fb, fill=ink)
    d.text((132, 2400), 'the coast about 1587', font=fi, fill=ink)
    a2 = np.asarray(im, np.uint8)
    out = new_surface(MAP_W, MAP_H)
    surf_array(out)[:] = a2[..., [2, 1, 0, 3]]
    out.mark_dirty()
    os.makedirs(LAYERS, exist_ok=True)
    out.write_to_png(os.path.join(LAYERS, 'map.png'))


BUILDERS = {'skies': build_skies, 'pines_far': build_pines_far, 'woods_mid': build_woods_mid, 'shore': build_shore,
            'island': build_island_strip, 'fg_oak': build_fg_oak, 'grass': build_grass_strip, 'map': build_map}

if __name__ == '__main__':
    import time
    names = sys.argv[1:] or list(BUILDERS)
    for n in names:
        t0 = time.time()
        BUILDERS[n]()
        print(f'{n}: {time.time() - t0:.1f}s', flush=True)
