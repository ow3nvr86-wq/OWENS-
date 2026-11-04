"""The scenes of the Roanoke Short. Each scene function draws one frame at time t (seconds, on the film
timeline) into a cairo context at output scale os_, and returns a 'look' dict for the finishing pass.

Depth comes only from flat layers moved at different speeds (the multiplane Camera in core.py): painted
PNG layers for sky and forest, and live-drawn planes (palisade, post, houses, ships, sea, figures) which
stay sharp at any zoom. Characters are drawn on twos with line boil."""
import math

import cairo
import numpy as np

from core import (PAL, W, H, Camera, draw_layer, keys, smooth, smoother, ease_out, ease_in, clamp, ramp, lerp, twos, boil_seed,
                  hash01, fnoise, vnoise, set_c, ink_shape, ink_line, ellipse_pts, soft_glow, mix, shade_c, path_poly, path_smooth,
                  taper_stroke, hatch_lines, load_png)
from figures import make_char, draw_figure
import poses
import world as Wd
from props import fog_bank, dust, smoke, bird, ink_splats

FOG = mix(PAL['grey3'], PAL['parch2'], 0.3)
AT, AB = mix(PAL['grey'], PAL['grey2'], 0.5), mix(PAL['charcoal'], PAL['grey2'], 0.3)
NT, NB = mix(PAL['grey2'], PAL['charcoal'], 0.5), mix(PAL['ink'], PAL['charcoal'], 0.5)

# ----------------------------------------------------------------------------------------------
# The cast (every person is an invented likeness; no portraits of the colonists survive)
# ----------------------------------------------------------------------------------------------
WHITE = make_char(1, 'm', 'adult', role='gent', beard='full', hair=PAL['hair_gr'], coat=PAL['charcoal'], hunch=0.04,
                  height=172, nose=1.15, brow_w=1.2)
ELEANOR = make_char(2, 'f', 'young', role='gent', gown=PAL['burg3'])
ANANIAS = make_char(3, 'm', 'adult', role='gent', beard='short', coat=PAL['umber'])
SOLDIER = make_char(30, 'm', 'adult', role='soldier', beard='short')
SAILORS = [make_char(40 + i, 'm', 'adult', role='sailor') for i in range(5)]
COLONISTS = [make_char(60 + i) for i in range(16)]
TRUMPETER = make_char(45, 'm', 'young', role='sailor', cap=PAL['burg3'])


def fig(ctx, cam, c, p, x, y, s, face, d, os_, t, alpha=1.0):
    sx, sy = cam.world_to_screen(x, y, d)
    sc = s * cam.z ** d
    ctx.save()
    ctx.scale(os_, os_)
    draw_figure(ctx, c, p, sx, sy, sc, face, pix=sc * os_, boil_k=boil_seed(t), alpha=alpha)
    ctx.restore()


def layer(ctx, cam, os_, name, d, x=0.0, y=0.0, sc=1.0, alpha=1.0):
    draw_layer(ctx, cam, name, d, os_, x, y, sc, alpha)


class World:
    """Context manager: draw in world units at depth d."""

    def __init__(self, ctx, cam, d, os_):
        self.ctx, self.cam, self.d, self.os_ = ctx, cam, d, os_

    def __enter__(self):
        self.ctx.save()
        self.cam.apply(self.ctx, self.d, self.os_)
        return self.ctx

    def __exit__(self, *a):
        self.ctx.restore()


def screen(ctx, os_):
    ctx.save()
    ctx.scale(os_, os_)
    return ctx


def lwz(cam, d=1.0, base=1.3):
    """Line width in world units that thickens only gently as the camera zooms in."""
    return base / (cam.z ** d) ** 0.55


def ground(ctx, x0, x1, gy, y1, col, seed=0, lw=1.2, hatch=True):
    g = cairo.LinearGradient(0, gy, 0, gy + 420)
    top = mix(col, PAL['parch2'], 0.22)
    g.add_color_stop_rgba(0, *top[:3], 1)
    g.add_color_stop_rgba(1, *shade_c(col, -0.12)[:3], 1)
    ctx.rectangle(x0, gy, x1 - x0, y1 - gy)
    ctx.set_source(g)
    ctx.fill()
    if hatch:
        rng = np.random.default_rng(seed)
        for k in range(int((x1 - x0) * (y1 - gy) / 5000)):
            x, y = rng.uniform(x0, x1), rng.uniform(gy + 6, y1)
            L = rng.uniform(10, 30) * (1 + (y - gy) / 300)
            ink_line(ctx, np.array([[x, y], [x + L, y + rng.uniform(-1, 1)]]), lw * 0.7, PAL['ink'], alpha=0.35)


def crow(ctx, x, y, s, t, t_fly=None, seed=0):
    """A crow sitting on the palisade; it takes off at t_fly."""
    if t_fly is not None and t > t_fly:
        u = t - t_fly
        x += u * 160 * s + 40 * s * u * u
        y -= u * 120 * s
        f = math.sin(u * 22)
        ink_shape(ctx, np.array([[x - 6 * s, y], [x + 8 * s, y - 2 * s], [x + 14 * s, y], [x + 6 * s, y + 3 * s]]), PAL['ink'], lw=0)
        for sg in (-1, 1):
            ink_line(ctx, np.array([[x, y], [x - 4 * s, y - 12 * s * f * sg], [x - 14 * s, y - 16 * s * f * sg]]), 3 * s, PAL['ink'])
        return
    b = 0.6 * math.sin(t * 3)
    ink_shape(ctx, np.array([[x - 10 * s, y], [x - 6 * s, y - 10 * s], [x + 4 * s, y - 13 * s + b], [x + 9 * s, y - 15 * s + b], [x + 12 * s, y - 13 * s + b],
                             [x + 8 * s, y - 9 * s], [x + 6 * s, y], [x - 2 * s, y + 2 * s]]), PAL['ink'], lw=0)
    ink_line(ctx, np.array([[x + 12 * s, y - 13 * s + b], [x + 16 * s, y - 12 * s + b]]), 1.6 * s, PAL['ink'])


# ----------------------------------------------------------------------------------------------
# The fort from outside (scenes 1 and 9)
# ----------------------------------------------------------------------------------------------
FORT_GY = 1450
POST_X = 641


def draw_fort_outside(ctx, cam, t, os_, crow_fly=None, fg=1.0, fog=0.5):
    layer(ctx, cam, os_, 'sky_dusk', 0.08, -210, -330)
    layer(ctx, cam, os_, 'pines_far', 0.3, -760, FORT_GY - 1460)
    with World(ctx, cam, 0.42, os_) as c:
        fog_bank(c, -600, FORT_GY - 380, 2400, 420, 0.55 * fog, t, speed=10, seed=2)
    layer(ctx, cam, os_, 'woods_mid', 0.6, -760, FORT_GY - 1470 + 10)
    with World(ctx, cam, 0.7, os_) as c:
        fog_bank(c, -700, FORT_GY - 300, 2600, 380, 0.5 * fog, t, speed=16, seed=4)
    lw = lwz(cam)
    with World(ctx, cam, 0.9, os_) as c:
        # inside, seen through the entrance: what is left of a house
        Wd.ruin(c, 520, FORT_GY - 40, 110, 160, 11, fog=0.45, fogcol=FOG, lw=lw)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -900, 2200, FORT_GY, 2400, mix(PAL['green3'], PAL['brown'], 0.45), seed=3, lw=lw)
        Wd.palisade(c, -900, 1900, FORT_GY, 330, 21, gap=(455, POST_X + 52), lw=lw, decay=0.6)
        Wd.carved_post(c, 410, FORT_GY, 74, 380, 22, reveal=0.0, lw=lw * 1.2, word='', band=False)
        Wd.carved_post(c, POST_X, FORT_GY, 104, 430, 23, reveal=1.0, lw=lw * 1.3, light=0.2)
        crow(c, 250, FORT_GY - 318, 1.5, t, crow_fly, 1)
        Wd.barrel(c, 120, FORT_GY + 120, 1.4, 4, lw=lw, empty=True)
        Wd.ruin(c, 930, FORT_GY + 150, 200, 40, 77, lw=lw)
        draw_layer(c, Camera(), 'grass_strip', 1.0, 1.0, -900, FORT_GY - 196, 1.0)
        draw_layer(c, Camera(), 'grass_strip', 1.0, 1.0, 1900, FORT_GY - 196, 1.0)
        Wd.grass_tufts(c, POST_X - 70, POST_X + 70, FORT_GY + 4, 6, 1.3, 7, t=t, wind=1.0)
    with World(ctx, cam, 1.0, os_) as c:
        fog_bank(c, -800, FORT_GY - 160, 2600, 300, 0.4 * fog, t, speed=24, seed=6)
    if fg > 0.01:
        with World(ctx, cam, 1.3, os_) as c:
            for k in range(11):
                bx = -260 + k * 62 + 30 * hash01(k, 5)
                Wd.moss_strand(c, bx, -40 - 30 * hash01(k, 6), 260 + 260 * hash01(k, 3) * (1 - abs(k - 2) / 8), t, 70 + k, alpha=0.92 * fg,
                               col=mix(PAL['grey2'], PAL['green3'], 0.4))
            Wd.grass_tufts(c, -400, 1500, 1930, 46, 3.0, 55, col=mix(PAL['green3'], PAL['ink'], 0.4), t=t, wind=1.0, alpha=fg)


def scene_vanish(ctx, t, os_):
    u = t
    cx, cy, z = keys(u, [(0.0, (540.0, 1010.0, 1.0)), (0.6, (546.0, 1030.0, 1.06)), (3.5, (POST_X + 1.0, FORT_GY - 150.0, 3.6)),
                         (4.6, (POST_X + 1.0, FORT_GY - 150.0, 4.0))], smoother)
    cam = Camera(cx, cy, z)
    draw_fort_outside(ctx, cam, t, os_, crow_fly=1.6, fg=1 - smooth(ramp(z, 1.2, 2.2)))
    # a cold light finds the letters as the camera arrives
    with World(ctx, cam, 1.0, os_) as c:
        soft_glow(c, POST_X, FORT_GY - 152, 90, PAL['parch'], 0.25 * smooth(ramp(u, 2.4, 3.6)))
    return dict(dark=0.38, desat=0.3, tint=(0.92, 0.93, 0.9), vig=0.6)


def scene_end(ctx, t, os_):
    u = t - 55.0
    cx, cy, z = keys(u, [(0.0, (540.0, 1010.0, 1.0)), (4.8, (560.0, 1120.0, 1.22))], smooth)
    cam = Camera(cx, cy, z)
    draw_fort_outside(ctx, cam, t, os_, crow_fly=None, fg=1.0, fog=0.8)
    k = smooth(ramp(u, 2.2, 3.6))
    if k > 0:
        ctx.save()
        set_c(ctx, PAL['ink'], 0.97 * k)
        ctx.paint()
        ctx.restore()
    return dict(dark=0.5 + 0.2 * k, desat=0.4, tint=(0.88, 0.9, 0.92), vig=0.7)


# ----------------------------------------------------------------------------------------------
# Scene 2 - the arrival: ships at sea, then the landing
# ----------------------------------------------------------------------------------------------
def wave_band(ctx, x0, x1, y, h, t, col, seed=0, s=1.0):
    pts = [[x, y + 3 * s * math.sin(x * 0.03 / s + t * 2.2 + seed)] for x in np.linspace(x0, x1, 40)]
    ink_shape(ctx, np.array(pts + [[x1, y + h], [x0, y + h]]), col, lw=0, smooth_path=False)
    Wd.foam(ctx, x0 + 10, x1 - 10, y + 1, t, s, seed, alpha=0.7)


def scene_sea(ctx, t, os_):
    u = t - 4.0
    pan = 70 * u
    s = screen(ctx, os_)
    sk = load_png('sky_day')
    s.save()
    s.translate(-210 - pan * 0.04, -380)
    s.set_source_surface(sk, 0, 0)
    s.paint()
    s.restore()
    yh = 900
    # the low island on the horizon slides in from the right
    isl = load_png('island_strip')
    s.save()
    s.translate(900 - pan * 0.25 - 300, yh - 270)
    s.scale(0.8, 0.8)
    s.set_source_surface(isl, 0, 0)
    s.paint_with_alpha(0.85)
    s.restore()
    Wd.sea(s, 0, W, yh, H, t, pan=pan, dark=0.45, lw=1.3)
    sea_far = mix(PAL['grey3'], PAL['grey'], 0.5)
    # gulls
    for k in range(4):
        gx = (200 + k * 260 + u * (30 + 12 * k)) % 1300 - 100
        bird(s, gx, 420 + 60 * math.sin(k * 2 + u * 0.7) + k * 40, 1.6 + 0.3 * k, t, k)
    # the pinnace and the flyboat further out, the Lion (the flagship) close
    for (x0, y, sc, kind, seed, fogk) in ((160, yh + 46, 0.42, 'pinnace', 3, 0.5), (860, yh + 70, 0.62, 'galleon', 2, 0.35)):
        x = x0 + 60 * u - pan * 0.3
        roll = 0.02 * math.sin(t * 1.1 + seed)
        Wd.ship(s, x, y + 3 * math.sin(t * 1.3 + seed), sc, t, seed, kind=kind, roll=roll, fog=fogk, fogcol=FOG, lw=1.0)
        wave_band(s, x - 160 * sc, x + 170 * sc, y + 4, 26 * sc, t, Wd.sea_at(y + 12 * sc, yh, H, 0.45), seed, sc)
    x = 400 + 74 * u - pan * 0.8
    y = 1150 + 6 * math.sin(t * 1.2)
    Wd.ship(s, x, y, 1.75, t, 1, roll=0.035 * math.sin(t * 1.05), lw=1.6)
    wave_band(s, x - 300, x + 320, y + 6, 70, t, Wd.sea_at(y + 30, yh, H, 0.45), 1, 1.75)
    # spray at the bow
    for k in range(6):
        ph = (t * 1.4 + k / 6) % 1.0
        bx = x + 250 + ph * 50
        by = y - 10 - math.sin(ph * math.pi) * 40
        s.arc(bx, by, 3 + 3 * ph, 0, 2 * math.pi)
        set_c(s, PAL['linen'], 0.6 * (1 - ph))
        s.fill()
    s.restore()
    return dict(dark=0.05, desat=0.25, tint=(1.0, 0.96, 0.88), vig=0.5)


LAND_WALKERS = None


def scene_land(ctx, t, os_):
    global LAND_WALKERS
    u = t - 7.4
    cx, cy, z = keys(u, [(-0.4, (520.0, 1240.0, 1.02)), (3.8, (640.0, 1270.0, 1.1))], smooth)
    cam = Camera(cx, cy, z)
    layer(ctx, cam, os_, 'sky_day', 0.08, -210, -300)
    with World(ctx, cam, 0.3, os_) as c:
        Wd.sea(c, -700, 1800, 1180, 1700, t, pan=cx * 0.3, dark=0.3)
        Wd.ship(c, 160, 1218, 0.62, t, 2, roll=0.015 * math.sin(t), sail=0.15, fog=0.3, fogcol=FOG, lw=1.0)
        wave_band(c, 40, 290, 1222, 16, t, Wd.sea_at(1230, 1180, 1700, 0.3), 3, 0.6)
    layer(ctx, cam, os_, 'shore_mid', 0.6, 470, 1300 - 1230)
    lw = lwz(cam)
    with World(ctx, cam, 1.0, os_) as c:
        sand = mix(PAL['parch2'], PAL['parch3'], 0.3)
        ink_shape(c, np.array([[-400, 1350], [2000, 1330], [2000, 2300], [-400, 2300]]), sand, lw=0, smooth_path=False)
        rng = np.random.default_rng(4)
        for k in range(80):
            x, y = rng.uniform(-400, 2000), rng.uniform(1360, 2200)
            ink_line(c, np.array([[x, y], [x + rng.uniform(8, 30), y]]), 0.9, PAL['ink'], alpha=0.25)
        # the water's edge: a wedge of the sound on the left with a wash of foam
        wl = [(-400, 1352), (180, 1352), (420, 1700), (560, 2300), (-400, 2300)]
        wet = [(180 + 18, 1352), (420 + 40, 1700), (560 + 46, 2300), (560, 2300), (420, 1700), (180, 1352)]
        ink_shape(c, np.array(wet), mix(sand, PAL['grey2'], 0.35), lw=0, smooth_path=False)
        ctx_s = c
        ctx_s.save()
        path_poly(ctx_s, np.array(wl))
        ctx_s.clip()
        Wd.sea(ctx_s, -400, 700, 1352, 2300, t, pan=0, dark=0.0, lw=1.2, chop=0.6)
        ctx_s.restore()
        for k in range(3):
            ph = (t * 0.35 + k / 3) % 1.0
            off = 14 * math.sin(ph * math.pi)
            P = np.array([(x + off * 1.2, y) for x, y in ((185, 1356), (300, 1520), (425, 1705), (500, 1960), (566, 2300))])
            ink_line(c, P, 3.0, PAL['linen'], alpha=0.75 * (1 - ph) + 0.2)
        # the ship's boat, run up on the sand
        Wd.longboat(c, 300, 1610, 1.5, t, 7, oars=False, lw=lw)
    if LAND_WALKERS is None:
        LAND_WALKERS = [
            (COLONISTS[0], 'chest', 400, 1760, 2.3, 0.0, 1.0),
            (ELEANOR, None, 560, 1660, 2.0, 0.2, 0.9),
            (COLONISTS[4], 'child', 650, 1680, 2.0, 0.25, 0.9),
            (SOLDIER, 'musket', 330, 1620, 1.8, 0.4, 0.8),
            (COLONISTS[2], 'sack', 720, 1860, 2.5, 0.1, 1.05),
            (COLONISTS[7], None, 860, 1630, 1.85, 0.5, 0.85),
            (WHITE, 'roll', 1000, 1720, 2.2, 0.0, 0.6),
            (COLONISTS[9], 'basket', 200, 1880, 2.5, 0.7, 0.95),
        ]
    tt = twos(t)
    order = sorted(LAND_WALKERS, key=lambda a: a[3])
    for c_, prop, x0, y, s, ph, spd in order:
        x = x0 + 60 * spd * (u + 0.4)
        if prop == 'child':
            c_ = make_char(64, 'f', 'child')
        p = poses.walk(tt + ph, c_['seed'], period=0.95 if prop != 'child' else 0.7, stride=0.9)
        if prop in ('chest', 'sack'):
            poses.carry(p, prop)
        elif prop == 'musket':
            p.update(prop='musket', ua_f=0.3, fa_f=1.1)
        elif prop == 'roll':
            p.update(prop='roll', ua_f=0.5, fa_f=1.3)
        elif prop == 'basket':
            p.update(prop='basket', ua_f=0.2, fa_f=1.4)
        fig(ctx, cam, c_, p, x, y, s, 1, 1.0, os_, t)
        with World(ctx, cam, 1.0, os_) as c:
            ink_shape(c, ellipse_pts(x, y + 4, 22 * s, 4 * s, 14), (0, 0, 0, 0.16), lw=0)
    # a man still stepping out of the boat
    p = poses.idle(tt, 77, turn=0.6)
    p.update(th_f=0.6, sh_f=0.1, lean=0.15)
    fig(ctx, cam, COLONISTS[11], p, 260, 1585, 1.5, 1, 1.0, os_, t)
    with World(ctx, cam, 1.0, os_) as c:
        Wd.longboat(c, 300, 1610, 1.5, t, 7, oars=False, lw=lwz(cam))
    layer(ctx, cam, os_, 'grass_strip', 1.25, -300, 1760, 1.0)
    return dict(dark=0.05, desat=0.25, tint=(1.0, 0.96, 0.88), vig=0.5)


# ----------------------------------------------------------------------------------------------
# Scene 3 - building a new life; supplies run short
# ----------------------------------------------------------------------------------------------
CLEAR_GY = 1450


def clearing_bg(ctx, cam, t, os_, sky='sky_day', fog=0.25):
    layer(ctx, cam, os_, sky, 0.08, -210, -380)
    layer(ctx, cam, os_, 'pines_far', 0.3, -760, CLEAR_GY - 1460)
    with World(ctx, cam, 0.45, os_) as c:
        fog_bank(c, -600, CLEAR_GY - 340, 2400, 360, 0.4 * fog, t, speed=8, seed=3)
    layer(ctx, cam, os_, 'woods_mid', 0.6, -760, CLEAR_GY - 1470 - 30)


def scene_build(ctx, t, os_):
    u = t - 11.0
    cx, cy, z = keys(u, [(-0.5, (440.0, 1330.0, 1.38)), (3.4, (620.0, 1340.0, 1.46))], smooth)
    cam = Camera(cx, cy, z)
    clearing_bg(ctx, cam, t, os_)
    lw = lwz(cam)
    tt = twos(t)
    with World(ctx, cam, 0.85, os_) as c:
        ground(c, -900, 2200, CLEAR_GY - 20, 1600, mix(PAL['green3'], PAL['brown2'], 0.5), seed=5, lw=lw)
        Wd.cottage(c, 160, CLEAR_GY - 20, 300, 190, 31, 1.0, lw=lw, smoke_t=t)
        Wd.cottage(c, 1080, CLEAR_GY - 20, 280, 180, 33, clamp(0.05 + 0.1 * u), lw=lw)
    fig(ctx, cam, COLONISTS[3], poses.hammer(tt, 3), 1010, CLEAR_GY - 20, 1.25, 1, 0.85, os_, t)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -900, 2200, CLEAR_GY + 30, 2300, mix(PAL['green3'], PAL['brown'], 0.5), seed=6, lw=lw)
        st = 0.33 + 0.12 * u
        Wd.cottage(c, 640, CLEAR_GY + 30, 330, 205, 32, st, lw=lw)
        for k, (bx, s_) in enumerate(((880, 1.2), (930, 1.15), (905, 1.15))):
            Wd.barrel(c, bx, CLEAR_GY + 40 + k * 4, s_, k, lw=lw)
        Wd.crate(c, 980, CLEAR_GY + 50, 1.2, 5, lw=lw)
        Wd.sack(c, 840, CLEAR_GY + 52, 1.2, 6, lw=lw)
        Wd.campfire(c, 300, CLEAR_GY + 70, 1.3, t, 3)
        smoke(c, 300, CLEAR_GY + 30, 1.2, t, 3, 0.35)
        Wd.grass_tufts(c, -600, 1800, CLEAR_GY + 34, 60, 1.2, 12, t=t, wind=0.6)
    # the men at work on the house, the log carrier, a woman at the fire
    fig(ctx, cam, COLONISTS[5], poses.hammer(tt + 0.3, 5), 520, CLEAR_GY + 30, 1.5, 1, 1.0, os_, t)
    fig(ctx, cam, COLONISTS[6], poses.hammer(tt + 0.7, 6, rate=1.05), 790, CLEAR_GY + 30, 1.5, -1, 1.0, os_, t)
    p = poses.idle(tt, 66, turn=0.6)
    p.update(lean=0.35, ua_f=0.6, fa_f=0.9, tilt=0.3, lookv=0.6, prop='staff')
    fig(ctx, cam, COLONISTS[10], p, 360, CLEAR_GY + 76, 1.55, -1, 1.0, os_, t)
    x = -60 + 85 * (u + 0.5)
    fig(ctx, cam, COLONISTS[8], poses.carry(poses.walk(tt, 8, period=1.15), 'log'), x, CLEAR_GY + 150, 1.75, 1, 1.0, os_, t)
    x2 = 1150 - 55 * (u + 0.5)
    p = poses.walk(tt + 0.3, 12, period=1.0)
    p.update(prop='basket', ua_f=0.2, fa_f=1.4)
    fig(ctx, cam, COLONISTS[12], p, x2, CLEAR_GY + 120, 1.7, -1, 1.0, os_, t)
    fig(ctx, cam, make_char(65, 'm', 'child'), poses.walk(tt, 65, period=0.65), x2 + 70, CLEAR_GY + 128, 1.7, -1, 1.0, os_, t)
    layer(ctx, cam, os_, 'grass_strip', 1.3, -500, CLEAR_GY + 300, 1.0)
    return dict(dark=0.06, desat=0.25, tint=(1.0, 0.96, 0.87), vig=0.5)


def scene_short(ctx, t, os_):
    u = t - 13.75
    cx, cy, z = keys(u, [(-0.5, (560.0, 1330.0, 1.5)), (4.6, (600.0, 1350.0, 1.72))], smooth)
    cam = Camera(cx, cy, z)
    clearing_bg(ctx, cam, t, os_, sky='sky_grey', fog=0.6)
    lw = lwz(cam)
    tt = twos(t)
    with World(ctx, cam, 0.8, os_) as c:
        ground(c, -900, 2200, CLEAR_GY - 10, 1700, mix(PAL['green3'], PAL['brown2'], 0.5), seed=7, lw=lw)
        Wd.palisade(c, 700, 1300, CLEAR_GY - 10, 240, 41, lw=lw, logw=30)
        # an arrow strikes the post beside the sentry
        if u > 2.8:
            k = clamp((u - 2.8) / 0.06)
            ax, ay = 742, CLEAR_GY - 150
            ink_line(c, np.array([[ax + 70 * (1 - k), ay - 12 * (1 - k)], [ax + 70 * (1 - k) + 46, ay - 12 * (1 - k) - 6]]), 1.6, PAL['wood2'])
            for sg in (-1, 1):
                ink_line(c, np.array([[ax + 70 * (1 - k) + 40, ay - 12 * (1 - k) - 5], [ax + 70 * (1 - k) + 50, ay - 12 * (1 - k) - 5 + sg * 6]]),
                         1.3, PAL['parch3'])
    p = poses.idle(tt, 30, turn=0.55)
    p.update(prop='musket', ua_f=0.35, fa_f=1.1, look=-0.6, hturn=0.2 + 0.5 * smooth(ramp(u, 2.85, 3.1)), brow=0.6)
    fig(ctx, cam, SOLDIER, p, 640, CLEAR_GY - 10, 1.55, -1 if u < 2.85 else 1, 0.8, os_, t)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -900, 2200, CLEAR_GY + 60, 2300, mix(PAL['green3'], PAL['brown'], 0.5), seed=8, lw=lw)
        Wd.barrel(c, 470, CLEAR_GY + 260, 2.6, 9, lw=lw, empty=True)
        Wd.barrel(c, 300, CLEAR_GY + 240, 2.4, 10, lw=lw, empty=True)
        Wd.sack(c, 640, CLEAR_GY + 270, 2.2, 11, lw=lw, fill=0.25)
    # a woman scrapes the bottom of a barrel with a wooden scoop
    p = poses.idle(tt, 61, turn=0.7)
    sc_ = 0.5 + 0.5 * math.sin(t * 2.4)
    p.update(lean=0.55, tilt=0.3, ua_f=0.45 + 0.15 * sc_, fa_f=0.2 + 0.25 * sc_, lookv=0.8, brow=0.75, ua_b=0.3, fa_b=0.5)
    fig(ctx, cam, COLONISTS[13] if COLONISTS[13]['sex'] == 'f' else make_char(61, 'f', 'adult'), p, 560, CLEAR_GY + 268, 2.5, -1, 1.0, os_, t)
    with World(ctx, cam, 1.0, os_) as c:
        Wd.barrel(c, 470, CLEAR_GY + 260, 2.6, 9, lw=lw, empty=True)
    layer(ctx, cam, os_, 'grass_strip', 1.25, -400, CLEAR_GY + 330, 1.0)
    return dict(dark=0.28, desat=0.4, tint=(0.92, 0.93, 0.92), vig=0.65)


# ----------------------------------------------------------------------------------------------
# Scene 4 - the departure
# ----------------------------------------------------------------------------------------------
def scene_white(ctx, t, os_):
    u = t - 18.0
    cx, cy, z = keys(u, [(-0.5, (540.0, 1180.0, 1.0)), (4.2, (520.0, 1220.0, 1.1))], smooth)
    cam = Camera(cx, cy, z)
    layer(ctx, cam, os_, 'sky_grey', 0.08, -210, -330)
    with World(ctx, cam, 0.3, os_) as c:
        Wd.sea(c, -700, 1800, 1060, 1500, t, pan=0, dark=0.2)
        Wd.ship(c, 820, 1112, 0.75, t, 1, roll=0.02 * math.sin(t), sail=0.35, lw=1.0, fog=0.2, fogcol=FOG)
        wave_band(c, 600, 1060, 1116, 18, t, Wd.sea_at(1124, 1060, 1500, 0.2), 3, 0.75)
    tt = twos(t)
    with World(ctx, cam, 0.7, os_) as c:
        sand = mix(PAL['parch2'], PAL['parch3'], 0.3)
        Wd.sea(c, -700, 1800, 1290, 1420, t, pan=0, dark=0.1, chop=0.7)
        ink_shape(c, np.array([[-700, 1420], [1900, 1400], [1900, 2400], [-700, 2400]]), sand, lw=0, smooth_path=False)
        for k in range(2):
            ph = (t * 0.33 + k / 2) % 1.0
            ink_line(c, np.array([[-700, 1418 + 6 * ph], [1900, 1398 + 6 * ph]]), 2.4, PAL['linen'], alpha=0.7 * (1 - ph))
    p = poses.idle(tt, 41, turn=0.6)
    fig(ctx, cam, SAILORS[1], p, 120, 1470, 1.4, 1, 0.7, os_, t)
    with World(ctx, cam, 0.7, os_) as c:
        Wd.longboat(c, 200, 1500, 1.4, t, 8, oars=False)
    with World(ctx, cam, 1.0, os_) as c:
        sand = mix(PAL['parch2'], PAL['parch3'], 0.25)
        ink_shape(c, np.array([[-700, 1760], [1900, 1740], [1900, 2400], [-700, 2400]]), shade_c(sand, -0.04), lw=0, smooth_path=False)
        Wd.grass_tufts(c, -300, 1400, 1900, 30, 2.2, 21, t=t, wind=1.0)
    # Ananias, Eleanor with the baby, and John White saying goodbye
    p = poses.idle(tt, 3, turn=0.45, look=-0.4)
    fig(ctx, cam, ANANIAS, p, 980, 1840, 4.6, -1, 1.0, os_, t)
    p = poses.carry(poses.idle(tt, 2, turn=0.55), 'baby')
    p.update(look=-0.5 * smooth(ramp(u, 0.8, 1.4)) + 0.6 * smooth(ramp(u, 2.6, 3.0)), lookv=0.2 + 0.4 * smooth(ramp(u, 2.6, 3.0)),
             bob=1.2 * math.sin(t * 2.2), brow=0.5)
    fig(ctx, cam, ELEANOR, p, 760, 1880, 5.0, -1, 1.0, os_, t)
    p = poses.idle(tt, 1, turn=0.62)
    reach = smooth(ramp(u, 1.4, 2.2)) * (1 - smooth(ramp(u, 3.0, 3.5)))
    p.update(prop='roll', ua_b=0.2, fa_b=0.9, ua_f=0.3 + 0.75 * reach, fa_f=0.5 + 1.25 * reach, look=0.4, lookv=0.35 * reach,
             brow=0.55, tilt=0.06 + 0.05 * reach)
    p['prop'] = None
    fig(ctx, cam, WHITE, p, 330, 1890, 5.6, 1, 1.0, os_, t)
    return dict(dark=0.14, desat=0.32, tint=(0.97, 0.95, 0.9), vig=0.58)


def scene_sail(ctx, t, os_):
    u = t - 21.6
    k = smooth(ramp(u, -0.3, 3.4))
    s = screen(ctx, os_)
    sk = load_png('sky_dusk')
    s.save()
    s.translate(-210, -460)
    s.set_source_surface(sk, 0, 0)
    s.paint()
    s.restore()
    yh = 1060
    soft_glow(s, 760, yh - 40, 520, PAL['candle'], 0.22)
    Wd.sea(s, 0, W, yh, H, t, pan=0, dark=0.3, glint=(760, 160, 0.25))
    # the ship sails out and sinks below the horizon, hull first
    sc = lerp(0.95, 0.12, ease_out(k))
    x = lerp(470, 760, k)
    y = yh + 52 * sc
    sk_ = smooth(ramp(u, 1.9, 3.3))
    sink = sk_ * 300 * sc
    s.save()
    s.rectangle(0, 0, W, y + 30 * sc - (y + 30 * sc - yh) * sk_)
    s.clip()
    Wd.ship(s, x, y + sink, sc, t, 1, roll=0.02 * math.sin(t), lw=max(0.6, 1.4 * sc ** 0.5), fog=0.25 + 0.45 * k, fogcol=mix(FOG, PAL['candle'], 0.2))
    s.restore()
    if sc > 0.3:
        wave_band(s, x - 160 * sc, x + 170 * sc, y + 3, 26 * sc, t, Wd.sea_at(y + 12 * sc, yh, H, 0.3), 2, sc)
    # the beach and the settlers watching, dark against the evening
    sand = mix(PAL['brown2'], PAL['charcoal'], 0.3)
    ink_shape(s, np.array([[0, 1500], [W, 1440], [W, H], [0, H]]), sand, lw=0, smooth_path=False)
    for kk in range(3):
        ph = (t * 0.33 + kk / 3) % 1.0
        ink_line(s, np.array([[0, 1500 + 10 * ph], [W, 1440 + 10 * ph]]), 3, PAL['linen'], alpha=0.5 * (1 - ph))
    tt = twos(t)
    sil = dict(boil_k=boil_seed(t))
    watchers = [(COLONISTS[1], 140, 1600, 2.4, 'idle'), (COLONISTS[3], 250, 1580, 2.3, 'wave'), (COLONISTS[12], 380, 1640, 2.6, 'idle'),
                (make_char(66, 'm', 'child'), 470, 1650, 2.5, 'idle'), (ANANIAS, 650, 1700, 3.0, 'idle'), (COLONISTS[7], 890, 1610, 2.4, 'cross')]
    for c_, x_, y_, s_, kind in watchers:
        if kind == 'wave':
            p = poses.wave_hand(tt, c_['seed'], turn=0.05)
        elif kind == 'cross':
            p = poses.react(tt, -1, c_['seed'], 'cross', turn=0.05)
        else:
            p = poses.idle(tt, c_['seed'], turn=0.05)
        p['hturn'] = 0.05
        draw_figure(s, c_, p, x_, y_, s_, 1, pix=s_ * os_, **sil)
    p = poses.carry(poses.idle(tt, 2, turn=0.2), 'baby')
    p.update(bob=1.0 * math.sin(t * 2.2), lookv=0.0, look=0.0, hturn=0.1)
    draw_figure(s, ELEANOR, p, 790, 1830, 4.6, -1, pix=4.6 * os_, **sil)
    s.restore()
    return dict(dark=0.3, desat=0.35, tint=(1.0, 0.92, 0.82), vig=0.62)


# ----------------------------------------------------------------------------------------------
# Scene 5 - the long wait: the Armada, and the seasons
# ----------------------------------------------------------------------------------------------
def plate_frame(ctx, os_, dark=0.0):
    s = screen(ctx, os_)
    m = 46
    s.rectangle(0, 0, W, H)
    s.rectangle(m, m + 100, W - 2 * m, H - 2 * m - 260)
    s.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    set_c(s, mix(PAL['parch2'], PAL['charcoal'], 0.55 + 0.3 * dark))
    s.fill()
    s.set_fill_rule(cairo.FILL_RULE_WINDING)
    for k, wdt in ((0, 6), (14, 1.5)):
        s.rectangle(m - k, m + 100 - k, W - 2 * m + 2 * k, H - 2 * m - 260 + 2 * k)
        set_c(s, PAL['ink'])
        s.set_line_width(wdt)
        s.stroke()
    s.restore()


def scene_armada(ctx, t, os_):
    u = t - 25.0
    z = lerp(1.0, 1.12, smooth(u / 3.8))
    s = screen(ctx, os_)
    s.translate(W / 2, H / 2)
    s.scale(z, z)
    s.translate(-W / 2, -H / 2)
    sk = load_png('sky_storm')
    s.save()
    s.translate(-210, -620)
    s.set_source_surface(sk, 0, 0)
    s.paint()
    s.restore()
    yh = 820
    Wd.sea(s, -100, W + 100, yh, H, t, pan=20 * u, dark=0.8, lw=1.3, top_col=AT, bot_col=AB)
    # the Spanish fleet in its crescent
    for k in range(9):
        a = -1.0 + 2.0 * k / 8
        x = 540 + a * 400 + 5 * u
        y = yh + 70 + (1 - a * a) * 120
        sc = 0.36 + 0.14 * (1 - abs(a))
        Wd.ship(s, x, y, sc, t, 100 + k, roll=0.025 * math.sin(t + k), fog=0.3, fogcol=mix(FOG, PAL['charcoal'], 0.3), lw=0.9)
        wave_band(s, x - 150 * sc, x + 160 * sc, y + 3, 22 * sc, t, Wd.sea_at(y + 10 * sc, yh, H, 0, AT, AB), k, sc)
    # gun smoke and flashes along the line
    for k in range(8):
        ph = ((t * 0.5 + hash01(k, 1)) % 1.0)
        x = 120 + k * 120 + ph * 30
        y = yh + 150 + 50 * math.sin(k * 1.7)
        r = 26 + 70 * ph
        ink_shape(s, ellipse_pts(x, y - ph * 50, r, r * 0.7, 16), (*PAL['grey3'][:3], 0.6 * (1 - ph)), lw=0.8, ink=(*PAL['grey2'][:3], 0.5 * (1 - ph)))
        if ph < 0.07:
            soft_glow(s, x, y, 50, PAL['candle2'], 0.9)
    # English fire ships drifting in, burning (Calais, 1588)
    for k in range(3):
        x = 150 + k * 330 + 22 * u
        y = 1330 + (k % 2) * 90
        sc = 0.8 + 0.15 * (k % 2)
        Wd.ship(s, x, y, sc, t, 120 + k, kind='pinnace', roll=0.03 * math.sin(t * 1.3 + k), sail=0.4, lw=1.2)
        wave_band(s, x - 110 * sc, x + 110 * sc, y + 4, 26 * sc, t, Wd.sea_at(y + 12 * sc, yh, H, 0, AT, AB), k, sc)
        soft_glow(s, x, y - 70 * sc, 280 * sc, PAL['candle'], 0.5)
        for j in range(6):
            fl = 1 + 0.3 * math.sin(t * (13 + j * 3) + j)
            fx = x - 70 * sc + j * 28 * sc
            ink_shape(s, np.array([[fx - 14 * sc, y - 20 * sc], [fx - 6 * sc, y - 90 * sc * fl], [fx + 2 * sc, y - 160 * sc * fl], [fx + 12 * sc, y - 80 * sc * fl],
                                   [fx + 16 * sc, y - 20 * sc]]), PAL['candle'] if j % 2 else PAL['burg2'], lw=0.8, ink=PAL['burg3'], seed=j + int(t * 15))
        smoke(s, x, y - 150 * sc, sc * 1.8, t + k, 40 + k, 0.6)
    # an English galleon in the foreground, firing a broadside
    x, y = 420, 1700
    Wd.ship(s, x, y, 1.15, t, 1, roll=0.03 * math.sin(t * 1.1), lw=1.5)
    wave_band(s, x - 220, x + 230, y + 6, 70, t, Wd.sea_at(y + 30, yh, H, 0, AT, AB), 9, 1.15)
    ph = (t * 0.9) % 1.0
    if ph < 0.3:
        for k in range(3):
            soft_glow(s, x - 40 + k * 60, y - 22, 90, PAL['candle2'], 0.9 * (1 - ph / 0.3))
    s.restore()
    plate_frame(ctx, os_, 0.5)
    return dict(dark=0.42, desat=0.42, tint=(0.95, 0.92, 0.86), vig=0.6)


def leaves(ctx, t, n, seed, x0, x1, y0, y1, col, size=6.0, speed=80.0, alpha=1.0):
    for i in range(n):
        ph = (t * speed / (y1 - y0) * (0.6 + 0.6 * hash01(seed, i)) + hash01(seed, i, 2)) % 1.0
        x = x0 + (x1 - x0) * hash01(seed, i, 3) + 40 * math.sin(t * 1.7 + i) - ph * 120
        y = y0 + (y1 - y0) * ph
        a = t * 3 + i
        P = ellipse_pts(x, y, size, size * 0.45, 8, rot=a)
        ink_shape(ctx, P, col, lw=0.6, ink=PAL['ink'], seed=i, line_alpha=0.6 * alpha) if alpha >= 0.99 else ink_shape(ctx, P, (*col[:3], alpha), lw=0)


def precip(ctx, t, n, seed, x0, x1, y0, y1, kind='snow', alpha=1.0):
    if kind == 'snow':
        for i in range(n):
            ph = (t * 0.25 * (0.6 + 0.8 * hash01(seed, i)) + hash01(seed, i, 2)) % 1.0
            x = x0 + (x1 - x0) * hash01(seed, i, 3) + 20 * math.sin(t * 1.3 + i)
            y = y0 + (y1 - y0) * ph
            ctx.arc(x, y, 2.2 + 2.5 * hash01(seed, i, 4), 0, 2 * math.pi)
            set_c(ctx, PAL['linen'], 0.85 * alpha)
            ctx.fill()
    else:
        set_c(ctx, PAL['grey3'], 0.55 * alpha)
        ctx.set_line_width(1.6)
        for i in range(n):
            ph = (t * 2.4 * (0.8 + 0.4 * hash01(seed, i)) + hash01(seed, i, 2)) % 1.0
            x = x0 + (x1 - x0) * hash01(seed, i, 3)
            y = y0 + (y1 - y0) * ph
            ctx.move_to(x, y)
            ctx.line_to(x - 14, y + 46)
        ctx.stroke()


SEASON_T = (28.8, 29.8, 30.8, 31.6)


def scene_seasons(ctx, t, os_):
    u = t - 28.8
    cam = Camera(*keys(u, [(-0.4, (560.0, 1320.0, 1.32)), (3.6, (600.0, 1330.0, 1.42))], smooth))
    # weights of autumn, winter, storm, summer (overgrown, empty)
    wa = 1 - smooth(ramp(t, 29.65, 29.95))
    ww = smooth(ramp(t, 29.65, 29.95)) * (1 - smooth(ramp(t, 30.65, 30.95)))
    wst = smooth(ramp(t, 30.65, 30.95)) * (1 - smooth(ramp(t, 31.4, 31.7)))
    wsu = smooth(ramp(t, 31.4, 31.7))
    sky = 'sky_storm' if wst > 0.5 else ('sky_grey' if ww > 0.5 else 'sky_dusk' if wa > 0.5 else 'sky_grey')
    clearing_bg(ctx, cam, t, os_, sky=sky, fog=0.5)
    lw = lwz(cam)
    tt = twos(t)
    snow = ww
    with World(ctx, cam, 0.85, os_) as c:
        ground(c, -900, 2200, CLEAR_GY - 20, 1600, mix(mix(PAL['green3'], PAL['brown2'], 0.5), PAL['linen'], 0.6 * snow), seed=5, lw=lw)
        Wd.cottage(c, 160, CLEAR_GY - 20, 300, 190, 31, 1.0, lw=lw, smoke_t=t if wa + ww > 0.5 else None, snow=snow, lit=ww)
        Wd.cottage(c, 1080, CLEAR_GY - 20, 280, 180, 33, 1.0, lw=lw, snow=snow)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -900, 2200, CLEAR_GY + 30, 2300, mix(mix(PAL['green3'], PAL['brown'], 0.5), PAL['linen'], 0.65 * snow), seed=6, lw=lw)
        Wd.cottage(c, 640, CLEAR_GY + 30, 330, 205, 32, 1.0, lw=lw, snow=snow, lit=0.6 * ww)
        if wa + ww > 0.3:
            Wd.barrel(c, 900, CLEAR_GY + 44, 1.2, 1, lw=lw)
            Wd.campfire(c, 330, CLEAR_GY + 70, 1.3, t, 3, alpha=ww + 0.4 * wa)
        if wsu > 0.01:
            # summer 1590: tall grass over everything
            for k in range(3):
                Wd.grass_tufts(c, -600, 1800, CLEAR_GY + 40 + k * 40, 70, 2.4 + k * 0.6, 80 + k, t=t, wind=0.8,
                               col=mix(PAL['green3'], PAL['parch3'], 0.3), alpha=wsu)
    with World(ctx, cam, 1.12, os_) as c:
        for k, (sx_, sy_) in enumerate(((60, CLEAR_GY + 240), (980, CLEAR_GY + 260))):
            ink_shape(c, ellipse_pts(sx_, sy_, 46, 14, 16), PAL['wood3'], lw=1.4, seed=k)
            ink_shape(c, np.array([[sx_ - 46, sy_], [sx_ + 46, sy_], [sx_ + 44, sy_ + 40], [sx_ - 44, sy_ + 40]]), PAL['wood2'], lw=1.4, smooth_path=False)
            ink_shape(c, ellipse_pts(sx_, sy_, 46, 14, 16), mix(PAL['wood3'], PAL['linen'], 0.8 * snow), lw=1.4, seed=k)
    layer(ctx, cam, os_, 'grass_strip', 1.25, -500, CLEAR_GY + 320, 1.0)
    # fewer people each season
    if wa > 0.01:
        for i, (cc, x, f) in enumerate(((COLONISTS[3], 470, 1), (COLONISTS[12], 760, -1), (COLONISTS[8], 220, 1), (make_char(66, 'm', 'child'), 820, -1))):
            fig(ctx, cam, cc, poses.idle(tt, cc['seed'], turn=0.4), x, CLEAR_GY + 120 + i * 12, 1.6, f, 1.0, os_, t, alpha=wa)
    if ww > 0.01:
        for i, (cc, x, f) in enumerate(((COLONISTS[1], 400, 1), (COLONISTS[13], 280, 1))):
            p = poses.idle(tt, cc['seed'], turn=0.5)
            p.update(ua_f=0.8, fa_f=1.4, lean=0.12, brow=0.6)
            fig(ctx, cam, cc, p, x, CLEAR_GY + 110 + i * 14, 1.6, f, 1.0, os_, t, alpha=ww)
    s = screen(ctx, os_)
    if wa > 0.01:
        leaves(s, t, 26, 3, -100, W + 200, -50, H, mix(PAL['burg2'], PAL['brown3'], 0.4), 7, 260, alpha=wa)
    if ww > 0.01:
        precip(s, t, 140, 4, -40, W + 40, -20, H, 'snow', ww)
    if wst > 0.01:
        precip(s, t, 220, 5, -40, W + 80, -60, H, 'rain', wst)
        fl = max(0.0, 1 - abs(t - 31.05) / 0.08)
        if fl > 0:
            set_c(s, PAL['linen'], 0.55 * fl)
            s.paint()
    s.restore()
    dark = 0.18 * wa + 0.25 * ww + 0.45 * wst + 0.15 * wsu
    tint = tuple(np.array((1.0, 0.92, 0.82)) * wa + np.array((0.9, 0.94, 1.0)) * ww + np.array((0.86, 0.9, 0.95)) * wst
                 + np.array((0.98, 0.97, 0.88)) * wsu)
    return dict(dark=dark, desat=0.32, tint=tint, vig=0.6)


# ----------------------------------------------------------------------------------------------
# Scene 6 - the return: a boat at night, then dawn in the forest
# ----------------------------------------------------------------------------------------------
def scene_night(ctx, t, os_):
    u = t - 32.0
    cx, cy, z = keys(u, [(-0.5, (420.0, 1360.0, 1.3)), (6.6, (640.0, 1400.0, 1.42))], smooth)
    cam = Camera(cx, cy, z)
    layer(ctx, cam, os_, 'sky_night', 0.08, -210, -420)
    with World(ctx, cam, 0.12, os_) as c:
        mx, my = 760, 560
        soft_glow(c, mx, my, 260, PAL['linen'], 0.25)
        ink_shape(c, ellipse_pts(mx, my, 40, 40, 24), mix(PAL['linen'], PAL['parch'], 0.4), lw=1.0)
        fog_bank(c, 420, 470, 700, 160, 0.45, t, speed=14, seed=8)
    layer(ctx, cam, os_, 'shore_mid', 0.5, -760, 1260 - 1230)
    with World(ctx, cam, 0.5, os_) as c:
        set_c(c, PAL['ink'], 0.55)
        c.mask_surface(load_png('shore_mid'), -760, 1260 - 1230)
        # the light of a great fire through the woods
        fl = 1 + 0.15 * math.sin(t * 9) + 0.1 * math.sin(t * 23)
        soft_glow(c, 980, 1215, 160 * fl, PAL['candle'], 0.5)
        soft_glow(c, 980, 1225, 40 * fl, PAL['candle2'], 0.8)
    with World(ctx, cam, 1.0, os_) as c:
        Wd.sea(c, -700, 2000, 1330, 2400, t, pan=0, dark=1.0, glint=(mx, 120, 0.22), top_col=NT, bot_col=NB, lw=1.3)
    # the boat: rowers, White with a lantern in the bow, a trumpeter in the stern
    bx = 260 + 52 * u
    by = 1620 + 5 * math.sin(t * 1.4)
    tt = twos(t)
    sing = smooth(ramp(t, 37.1, 37.4))
    trump = smooth(ramp(t, 36.2, 36.55)) * (1 - smooth(ramp(t, 37.0, 37.3)))
    ps = []
    for k in range(3):
        p = poses.row(tt, 50 + k)
        p['mouth'] = 0.35 * sing * abs(math.sin(t * 5 + k))
        ps.append(p)
        fig(ctx, cam, SAILORS[k], p, bx - 70 + k * 62, by + 100, 1.5, 1, 1.0, os_, t)
    p = poses.idle(tt, 45, turn=0.5)
    p.update(ua_f=0.2 + 1.0 * trump, fa_f=0.3 + 1.9 * trump, prop='trumpet' if trump > 0.5 else None, tilt=-0.12 * trump,
             mouth=0.35 * sing * abs(math.sin(t * 4.6)), lookv=-0.25 * trump)
    fig(ctx, cam, TRUMPETER, p, bx - 140, by + 44, 1.5, 1, 1.0, os_, t)
    p = poses.idle(tt, 1, turn=0.7)
    p.update(prop='lantern', ua_f=0.9, fa_f=1.5, look=0.5, lookv=-0.1, brow=0.6, prop_t=t, mouth=0.2 * sing * abs(math.sin(t * 4.1)))
    fig(ctx, cam, WHITE, p, bx + 140, by + 40, 1.55, 1, 1.0, os_, t)
    with World(ctx, cam, 1.0, os_) as c:
        Wd.longboat(c, bx, by, 2.1, tt, 9, oars=True, lw=1.4)
        wave_band(c, bx - 180, bx + 190, by + 6, 50, t, Wd.sea_at(by + 30, 1330, 2400, 0, NT, NB), 4, 2.0)
        soft_glow(c, bx + 150, by - 40, 60, PAL['candle'], 0.2)
    return dict(dark=0.62, desat=0.4, tint=(0.8, 0.86, 1.0), vig=0.7, lift=0.03)


def scene_woods(ctx, t, os_):
    u = t - 38.2
    wx = 250 + 105 * (u + 0.4)
    cam = Camera(wx + 70, 1240, 1.25)
    layer(ctx, cam, os_, 'sky_dawn', 0.08, -210, -380)
    layer(ctx, cam, os_, 'pines_far', 0.3, -760, CLEAR_GY - 1460)
    with World(ctx, cam, 0.45, os_) as c:
        fog_bank(c, -600, CLEAR_GY - 360, 2600, 420, 0.6, t, speed=8, seed=3)
    layer(ctx, cam, os_, 'woods_mid', 0.62, -760, CLEAR_GY - 1470 + 20)
    with World(ctx, cam, 0.7, os_) as c:
        # shafts of early light between the trunks
        for k in range(4):
            x0 = 200 + k * 320
            set_c(c, PAL['parch'], 0.10)
            c.move_to(x0, 0)
            c.line_to(x0 + 90, 0)
            c.line_to(x0 + 420, CLEAR_GY)
            c.line_to(x0 + 250, CLEAR_GY)
            c.close_path()
            c.fill()
    lw = lwz(cam)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -600, 2600, CLEAR_GY, 2400, mix(PAL['green3'], PAL['brown'], 0.45), seed=13, lw=lw)
        draw_layer(c, Camera(), 'grass_strip', 1.0, 1.0, -600, CLEAR_GY - 190, 1.0)
        draw_layer(c, Camera(), 'grass_strip', 1.0, 1.0, 2200, CLEAR_GY - 190, 1.0)
    tt = twos(t)
    for k, (cc, dx) in enumerate(((SAILORS[3], -330), (SAILORS[2], -190))):
        fig(ctx, cam, cc, poses.walk(tt + 0.3 * k, cc['seed'], period=1.1), wx + dx, CLEAR_GY + 40, 1.5, 1, 1.0, os_, t)
    p = poses.walk(tt, 1, period=1.15)
    p.update(look=0.4, brow=0.6)
    fig(ctx, cam, WHITE, p, wx, CLEAR_GY + 50, 1.55, 1, 1.0, os_, t)
    with World(ctx, cam, 1.5, os_) as c:
        for k in range(6):
            x = -200 + k * 620
            Wd.pine(c, x, 2400, 2600, 700 + k, lw=2.0)
    return dict(dark=0.3, desat=0.38, tint=(0.94, 0.94, 0.92), vig=0.62)


# ----------------------------------------------------------------------------------------------
# Scene 7 - the clue
# ----------------------------------------------------------------------------------------------
def scene_inside(ctx, t, os_):
    u = t - 40.0
    cx, cy, z = keys(u, [(-0.5, (360.0, 1380.0, 1.45)), (2.8, (470.0, 1390.0, 1.55))], smooth)
    cam = Camera(cx, cy, z)
    layer(ctx, cam, os_, 'sky_grey', 0.08, -210, -330)
    layer(ctx, cam, os_, 'pines_far', 0.3, -760, FORT_GY - 1460)
    layer(ctx, cam, os_, 'woods_mid', 0.55, -760, FORT_GY - 1470 - 60)
    lw = lwz(cam)
    with World(ctx, cam, 0.72, os_) as c:
        ground(c, -900, 2400, FORT_GY - 90, 1800, mix(PAL['green3'], PAL['brown2'], 0.5), seed=21, lw=lw)
        Wd.palisade(c, -900, 2400, FORT_GY - 90, 330, 51, lw=lw, decay=0.5)
        fog_bank(c, -800, FORT_GY - 300, 3000, 300, 0.4, t, speed=14, seed=9)
    with World(ctx, cam, 0.86, os_) as c:
        ground(c, -900, 2400, FORT_GY - 40, 1900, mix(PAL['green3'], PAL['brown2'], 0.45), seed=22, lw=lw, hatch=False)
        Wd.ruin(c, 160, FORT_GY - 40, 220, 200, 61, lw=lw)
        Wd.ruin(c, 900, FORT_GY - 40, 240, 210, 62, lw=lw)
        Wd.grass_tufts(c, -600, 1800, FORT_GY - 36, 80, 1.8, 23, t=t, wind=0.5)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -900, 2400, FORT_GY + 30, 2400, mix(PAL['green3'], PAL['brown'], 0.5), seed=23, lw=lw)
        Wd.ruin(c, 560, FORT_GY + 30, 260, 230, 63, lw=lw)
        Wd.sea_chest(c, 420, FORT_GY + 170, 1.6, 64, open_=1.0, lw=lw)
        Wd.sea_chest(c, 800, FORT_GY + 150, 1.4, 65, open_=0.6, lw=lw)
        Wd.scatter_pages(c, 560, FORT_GY + 190, 1.6, 66, n=8)
        # rusted armour in the grass
        ink_shape(c, np.array([[650, FORT_GY + 200], [700, FORT_GY + 186], [732, FORT_GY + 200], [724, FORT_GY + 228], [660, FORT_GY + 230]]),
                  mix(PAL['brown2'], PAL['burg3'], 0.4), lw=lw, seed=4, shadow=(PAL['umber'], 6))
        for k in range(3):
            Wd.grass_tufts(c, -600, 1800, FORT_GY + 60 + k * 70, 60, 2.0 + 0.4 * k, 30 + k, t=t, wind=0.7)
    tt = twos(t)
    walk_u = clamp((u + 0.3) / 1.9)
    x = lerp(-40, 300, walk_u)
    if u < 1.6:
        p = poses.walk(tt, 1, period=1.2)
    else:
        p = poses.react(tt, 1.6 + 40.0, 1, 'stare', turn=0.5)
        p['hturn'] = 0.55 + 0.35 * math.sin((u - 1.6) * 1.6)
    p.update(brow=0.7)
    for k, (cc, dx) in enumerate(((SAILORS[3], -190), (SAILORS[2], -320))):
        xx = lerp(-260 + dx, 130 + dx, clamp((u + 0.3) / 2.1))
        pp = poses.walk(tt + 0.25 * k, cc['seed'], period=1.2) if u < 1.8 else poses.idle(tt, cc['seed'], turn=0.5)
        fig(ctx, cam, cc, pp, xx, FORT_GY + 140 - k * 30, 1.6, 1, 1.0, os_, t)
    fig(ctx, cam, WHITE, p, x, FORT_GY + 160, 1.75, 1, 1.0, os_, t)
    layer(ctx, cam, os_, 'grass_strip', 1.3, -600, FORT_GY + 330, 1.0)
    return dict(dark=0.32, desat=0.42, tint=(0.93, 0.94, 0.92), vig=0.62)


def scene_carving(ctx, t, os_):
    u = t - 42.3
    cx, cy, z = keys(u, [(-0.4, (POST_X - 140.0, FORT_GY - 200.0, 1.75)), (1.3, (POST_X - 20.0, FORT_GY - 158.0, 3.0)),
                         (4.0, (POST_X + 1.0, FORT_GY - 152.0, 4.6)), (5.9, (POST_X + 1.0, FORT_GY - 152.0, 6.2))], smooth)
    cam = Camera(cx, cy, z)
    layer(ctx, cam, os_, 'sky_grey', 0.08, -210, -330)
    layer(ctx, cam, os_, 'pines_far', 0.3, -760, FORT_GY - 1460)
    layer(ctx, cam, os_, 'woods_mid', 0.6, -760, FORT_GY - 1470 + 10)
    lw = lwz(cam)
    light = smooth(ramp(u, 0.3, 1.6))
    ghost = smooth(ramp(t, 44.45, 44.8)) * (1 - smooth(ramp(t, 46.3, 46.9)))
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -900, 2200, FORT_GY, 2400, mix(PAL['green3'], PAL['brown'], 0.45), seed=3, lw=lw)
        Wd.palisade(c, -900, 1900, FORT_GY, 330, 21, gap=(455, POST_X + 52), lw=lw, decay=0.6)
        Wd.carved_post(c, POST_X, FORT_GY, 104, 430, 23, reveal=1.0, lw=lw * 1.3, light=light, ghost_cross=ghost)
        # a shaft of light falls across the letters
        soft_glow(c, POST_X - 6, FORT_GY - 150, 120, PAL['parch'], 0.28 * light)
        set_c(c, PAL['parch'], 0.07 * light)
        c.move_to(POST_X - 600, FORT_GY - 900)
        c.line_to(POST_X - 420, FORT_GY - 900)
        c.line_to(POST_X + 60, FORT_GY - 110)
        c.line_to(POST_X - 70, FORT_GY - 110)
        c.close_path()
        c.fill()
        fog_bank(c, -800, FORT_GY - 140, 2600, 260, 0.35, t, speed=20, seed=6)
    # White, seen from behind his shoulder, looking at the post
    tt = twos(t)
    p = poses.idle(tt, 1, turn=0.85)
    p.update(hturn=0.95, lookv=-0.05, brow=0.85, ua_f=0.3 + 0.9 * smooth(ramp(u, 0.6, 1.6)), fa_f=0.4 + 1.1 * smooth(ramp(u, 0.6, 1.6)))
    al = 1 - smooth(ramp(z, 2.7, 3.4))
    if al > 0.01:
        fig(ctx, cam, WHITE, p, POST_X - 175, FORT_GY + 70, 1.7, 1, 1.12, os_, t, alpha=al)
    return dict(dark=0.4, desat=0.4, tint=(0.94, 0.93, 0.9), vig=0.72)


# ----------------------------------------------------------------------------------------------
# Scene 8 - the theories, on a map of the coast
# ----------------------------------------------------------------------------------------------
def dashed_route(ctx, pts, k, lw, col, dash=(14, 10)):
    """Draw a route along pts, revealed to fraction k, with an arrow head at its tip."""
    P = np.array(pts, float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    L = seg.sum() * clamp(k)
    if L <= 1:
        return
    out = [P[0]]
    acc = 0
    for i, sl in enumerate(seg):
        if acc + sl >= L:
            out.append(P[i] + (P[i + 1] - P[i]) * (L - acc) / sl)
            break
        out.append(P[i + 1])
        acc += sl
    Q = np.array(out)
    ctx.save()
    ctx.set_dash(list(dash))
    ink_line(ctx, Q, lw, col)
    ctx.restore()
    d = Q[-1] - Q[-2] if len(Q) > 1 else np.array([1, 0])
    d = d / (np.linalg.norm(d) + 1e-6)
    n = np.array([-d[1], d[0]])
    tip = Q[-1]
    ink_shape(ctx, np.array([tip + d * lw * 3, tip - d * lw * 2 + n * lw * 2.4, tip - d * lw * 2 - n * lw * 2.4]), col, lw=0, smooth_path=False)


def village(ctx, x, y, s, alpha=1.0, seed=0):
    """An Algonquian town as on the 1580s charts: a ring of rounded, mat-covered houses."""
    for k in range(7):
        a = 2 * math.pi * k / 7
        hx, hy = x + math.cos(a) * 26 * s, y + math.sin(a) * 18 * s
        ink_shape(ctx, np.array([[hx - 9 * s, hy + 5 * s], [hx - 9 * s, hy - 2 * s], [hx, hy - 8 * s], [hx + 9 * s, hy - 2 * s], [hx + 9 * s, hy + 5 * s]]),
                  (*PAL['brown3'][:3], alpha), lw=1.2 * s, ink=(*PAL['ink'][:3], alpha), seed=seed + k, line_alpha=alpha)
    ctx.arc(x, y, 36 * s, 0, 2 * math.pi)
    set_c(ctx, PAL['ink'], 0.6 * alpha)
    ctx.set_line_width(1.4 * s)
    ctx.stroke()


def dig(ctx, x, y, s, alpha=1.0):
    """An excavation symbol: a squared trench with a spade."""
    set_c(ctx, PAL['burg'], alpha)
    ctx.set_line_width(3.2 * s)
    ctx.rectangle(x - 22 * s, y - 22 * s, 44 * s, 44 * s)
    ctx.stroke()
    for k in range(4):
        ctx.move_to(x - 22 * s + k * 11 * s, y - 22 * s)
        ctx.line_to(x - 22 * s + k * 11 * s + 8 * s, y + 22 * s)
    ctx.set_line_width(1.2 * s)
    ctx.stroke()
    ink_line(ctx, np.array([[x + 26 * s, y - 40 * s], [x + 40 * s, y + 4 * s]]), 3 * s, (*PAL['wood2'][:3], 1), alpha=alpha)
    ink_shape(ctx, np.array([[x + 36 * s, y], [x + 48 * s, y - 4 * s], [x + 52 * s, y + 16 * s], [x + 44 * s, y + 20 * s]]), (*PAL['grey'][:3], alpha), lw=1.2 * s,
              ink=(*PAL['ink'][:3], alpha), smooth_path=False, line_alpha=alpha)


def scene_map(ctx, t, os_):
    from sets import MAP_PTS, MAP_W, MAP_H
    u = t - 48.0
    cx, cy, z = keys(u, [(-0.5, (930.0, 1150.0, 1.35)), (0.4, (930.0, 1150.0, 1.35)), (2.6, (960.0, 1460.0, 0.86)),
                         (3.8, (840.0, 1280.0, 0.78)), (7.2, (800.0, 1260.0, 0.8))], smoother)
    cam = Camera(cx, cy, z)
    set_c(ctx, PAL['charcoal'])
    ctx.paint()
    layer(ctx, cam, os_, 'map', 1.0, 0, 0, 1.0)
    P = MAP_PTS
    with World(ctx, cam, 1.0, os_) as c:
        # Roanoke Island marked; then Croatoan to the south, home of Manteo's people
        rk = smooth(ramp(u, 0.0, 0.5))
        c.arc(*P['roanoke'], 125, 0, 2 * math.pi)
        set_c(c, PAL['burg'], 0.8 * rk)
        c.set_line_width(3)
        c.stroke()
        ck = smooth(ramp(u, 0.8, 1.6))
        if ck > 0:
            soft_glow(c, P['croatoan'][0] + 40, P['croatoan'][1] - 30, 230, PAL['burg2'], 0.35 * ck * (0.85 + 0.15 * math.sin(t * 4)))
            village(c, P['hatteras_vil'][0] + 40, P['hatteras_vil'][1] - 60, 1.3, smooth(ramp(u, 1.7, 2.2)), 3)
        # theory one: south to Croatoan
        k1 = smooth(ramp(t, 51.0, 51.9))
        if k1 > 0:
            dashed_route(c, [(950, 1150), (1010, 1400), (1080, 1650), (1180, 1820)], k1, 6, PAL['burg'])
        # theory two: west, inland, among the peoples of the mainland
        k2 = smooth(ramp(t, 52.2, 53.2))
        if k2 > 0:
            dashed_route(c, [(905, 1030), (800, 900), (640, 760), (470, 660)], k2, 6, PAL['burg'])
            village(c, 560, 1150, 1.2, smooth(ramp(t, 52.4, 52.8)), 5)
            village(c, 360, 760, 1.2, smooth(ramp(t, 52.8, 53.2)), 6)
        # where archaeologists have dug: Cape Creek on Hatteras, and 'Site X' in Bertie County
        k3 = smooth(ramp(t, 53.6, 54.0))
        if k3 > 0:
            dig(c, P['cape'][0], P['cape'][1] - 10, 1.3, k3)
            dig(c, P['sitex'][0], P['sitex'][1], 1.3, k3)
    s = screen(ctx, os_)
    # the page darkens towards the edges
    g = cairo.RadialGradient(W / 2, H / 2, 300, W / 2, H / 2, 1100)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    s.set_source(g)
    s.paint()
    s.restore()
    return dict(dark=0.22, desat=0.25, tint=(1.0, 0.95, 0.86), vig=0.55, paper=0.6)
