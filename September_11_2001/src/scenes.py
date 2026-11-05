"""The scenes of the September 11 Short in a modern, flat 2D motion-graphics style. Each scene draws one frame
at time t (seconds on the film timeline) into a cairo context at output scale os_ and returns a 'look' dict.
Depth comes from flat layers moved at different speeds by the multiplane Camera (core.py). No impact, fire or
injury is shown: the attacks are told through a clock, a timeline and a map."""
import math

import cairo
import numpy as np

from core import W, H, Camera, keys, smooth, smoother, ease_out, ease_in, clamp, ramp, lerp, twos, boil_seed, hash01
from figures import draw_figure
import poses
from chars import person
import gfx as G
from gfx import C, mixc

GY = 1180          # the waterline / street line of the skyline scenes (world units at depth 1)
TX = 470           # the Twin Towers' left edge in the skyline layer (world units)
TS = 1.15          # px per metre for the towers in the skyline scenes


class World:
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


def fig_sil(ctx, cam, c, p, x, y, s, face, d, os_, t, col, rim=None):
    """A character drawn as a silhouette with a rim of light."""
    sx, sy = cam.world_to_screen(x, y, d)
    sc = s * cam.z ** d
    ctx.save()
    ctx.scale(os_, os_)
    G.silhouette(ctx, lambda cc: draw_figure(cc, c, p, sx, sy, sc, face, pix=sc * os_, boil_k=None), col, rim, rim_dx=-2.5 * sc / 1.5)
    ctx.restore()


# ----------------------------------------------------------------------------------------------
# The skyline across the Hudson (scenes 1 and 4)
# ----------------------------------------------------------------------------------------------
def skyline_scene(ctx, cam, t, os_, mood=0.0, towers=1.0, night=0.0, smoke=0.0, sun=1.0, ferry_t=None, beams=0.0):
    with World(ctx, cam, 0.05, os_) as c:
        G.sky(c, W, H, GY - 120, mood, night)
        if sun > 0 and night < 0.5:
            G.glow(c, 640, GY - 260, 900, mixc(C['warm'], C['white'], 0.4), 0.45 * sun * (1 - mood))
    with World(ctx, cam, 0.12, os_) as c:
        G.clouds(c, t, W, 180, GY - 500, n=7, seed=2, speed=18, col=mixc(C['white'], C['grey4'], mood), a=0.9 * (1 - night * 0.7))
    if beams > 0:
        with World(ctx, cam, 0.5, os_) as c:
            G.beams(c, TX + 30, TX + 125, GY - 30, -900, t, beams)
    with World(ctx, cam, 0.3, os_) as c:
        G.skyline(c, -800, 2000, GY - 40, 0.9, 7, mixc(C['blue2'], C['navy3'], 0.35 + 0.5 * night), haze=0.45 * (1 - night) + 0.1 * mood, low=True,
                  win=0.12 * night)
    with World(ctx, cam, 0.55, os_) as c:
        col = mixc(mixc(C['navy3'], C['grey2'], mood * 0.6), C['navy1'], night)
        G.skyline(c, -700, TX - 40, GY - 10, 1.15, 11, col, haze=0.08 * (1 - night), win=0.25 * night + 0.05)
        G.skyline(c, TX + 220, 2000, GY - 10, 1.15, 12, col, haze=0.08 * (1 - night), win=0.25 * night + 0.05)
        if towers > 0.01:
            c.push_group()
            G.twin_towers(c, TX, GY - 10, TS, t, col=mixc(col, C['blue2'], 0.15), rim=mixc(C['warm'], C['white'], 0.5) if night < 0.5 else None)
            c.pop_group_to_source()
            c.paint_with_alpha(towers)
        if night > 0.5:
            G.one_wtc(c, TX + 75, GY - 10, 1.0, mixc(C['navy3'], C['blue1'], 0.3), rim=C['blue3'])
        if smoke > 0:
            G.plume(c, TX + 60, GY - 300, 1.4, t, seed=5, n=16, col=mixc(C['grey3'], C['dust'], 0.4), alpha=0.75 * smoke, wind=0.9, spread=1.3)
            G.plume(c, TX + 110, GY - 220, 1.1, t + 4, seed=6, n=12, col=mixc(C['grey4'], C['dust'], 0.5), alpha=0.6 * smoke, wind=1.0, spread=1.2)
    with World(ctx, cam, 0.8, os_) as c:
        top = mixc(mixc(C['blue2'], C['grey3'], mood), C['navy2'], night)
        G.river(c, -900, 2200, GY, 2600, t, top=top, bot=mixc(C['navy3'], C['navy0'], night * 0.6), glint=(640, 160, 0.25 * sun * (1 - mood) * (1 - night)))
        if ferry_t is not None:
            G.ferry(c, -200 + 60 * ferry_t, GY + 140, 2.2, col=mixc(C['navy2'], C['grey2'], mood))
        for k in range(4):
            G.bird(c, (100 + k * 170 + t * 45) % 1400 - 200, 520 + 50 * math.sin(k * 1.7 + t), 2.0, t, k, col=mixc(C['navy2'], C['navy0'], night))
    with World(ctx, cam, 1.3, os_) as c:
        # a railing on the New Jersey waterfront, in the foreground
        rc = mixc(C['navy1'], C['navy0'], 0.5)
        G.rect(c, -600, GY + 640, 1800, GY + 652, rc)
        G.rect(c, -600, GY + 700, 1800, GY + 712, rc)
        for k in range(16):
            x = -600 + k * 160
            G.rect(c, x, GY + 640, x + 10, GY + 900, rc)
        G.rect(c, -600, GY + 760, 1800, 2600, mixc(C['navy0'], C['char'], 0.5))


def scene_opening(ctx, t, os_):
    u = t
    cx, cy, z = keys(u, [(0.0, (540.0, 980.0, 1.0)), (4.8, (560.0, 900.0, 1.22))], smooth)
    cam = Camera(cx, cy, z)
    skyline_scene(ctx, cam, t, os_, ferry_t=u)
    return dict(dark=0.0, desat=0.05, tint=(0.98, 1.0, 1.03), bloom=0.3)


# ----------------------------------------------------------------------------------------------
# Scene 2 - the attacks, told on a clock and a timeline over architectural silhouettes
# ----------------------------------------------------------------------------------------------
NORTH = dict(tower='N', f0=93, f1=99)
SOUTH = dict(tower='S', f0=77, f1=85)


def scene_attacks(ctx, t, os_):
    u = t - 4.4
    cam = Camera(540, 1000 + 10 * u, 1.0 + 0.03 * u)
    s = screen(ctx, os_)
    G.vgrad(s, 0, 0, W, H, [(0, C['navy0']), (0.6, C['navy1']), (1, C['navy2'])])
    for k in range(0, H, 60):
        G.line(s, [[0, k], [W, k]], 1, (*C['blue1'][:3], 0.08))
    for k in range(0, W, 60):
        G.line(s, [[k, 0], [k, H]], 1, (*C['blue1'][:3], 0.08))
    s.restore()
    gy = 1420
    with World(ctx, cam, 0.6, os_) as c:
        G.skyline(c, -400, 1600, gy, 1.2, 11, mixc(C['navy2'], C['navy3'], 0.4), win=0.0)
    with World(ctx, cam, 1.0, os_) as c:
        kN = smooth(ramp(t, 5.3, 5.8))
        kS = smooth(ramp(t, 7.3, 7.8))
        hl = None
        # the towers as line drawings, floors ruled across them
        tw = G.twin_towers(c, 330, gy, 1.55, t, outline=((*C['blue3'][:3], 0.9), 2.2), bands=True)
        for name, tx, h in tw:
            for fl in range(0, 111, 5):
                yy = gy - h * fl / 110
                G.line(c, [[tx, yy], [tx + 63 * 1.55, yy]], 0.8, (*C['blue2'][:3], 0.35))
        G.twin_towers(c, 330, gy, 1.55, t, outline=((0, 0, 0, 0), 0.1), bands=False, highlight=dict(NORTH, k=kN))
        G.twin_towers(c, 330, gy, 1.55, t, outline=((0, 0, 0, 0), 0.1), bands=False, highlight=dict(SOUTH, k=kS))
        _ = hl
        # thin smoke wisps from the marked floors, drawn with restraint
        if kN > 0:
            yN = gy - 417 * 1.55 * 96 / 110
            G.plume(c, 330 + 48, yN, 0.6, t, seed=3, n=10, col=C['grey3'], alpha=0.35 * kN, wind=1.2, grow=clamp((t - 5.5) / 2.5))
        if kS > 0:
            yS = gy - 415 * 1.55 * 81 / 110
            G.plume(c, 330 + 63 * 1.55 + 26 * 1.55 + 48, yS, 0.6, t, seed=4, n=10, col=C['grey3'], alpha=0.35 * kS, wind=1.2, grow=clamp((t - 7.5) / 2.0))
        G.line(c, [[-300, gy], [1500, gy]], 2, (*C['blue3'][:3], 0.6))
    # the timeline along the bottom of the drawing
    s = screen(ctx, os_)
    y = 1520
    x0, x1 = 140, 940
    G.line(s, [[x0, y], [x1, y]], 4, (*C['blue2'][:3], 0.7))
    prog = clamp((t - 4.8) / 3.4)
    G.line(s, [[x0, y], [x0 + (x1 - x0) * prog, y]], 4, C['white'])
    for frac, t0, lab in ((0.15, 5.3, '8:46'), (0.85, 7.3, '9:03')):
        xx = x0 + (x1 - x0) * frac
        k = smooth(ramp(t, t0, t0 + 0.3))
        s.arc(xx, y, 12 + 6 * k, 0, 2 * math.pi)
        G.setc(s, C['red2'] if k > 0.5 else C['blue2'])
        s.fill()
        G.text(s, xx, y + 62, 34, lab, (*C['white'][:3], 0.4 + 0.6 * k), track=0.04)
    s.restore()
    return dict(dark=0.1, desat=0.05, tint=(0.97, 1.0, 1.05), bloom=0.35)


# ----------------------------------------------------------------------------------------------
# Scene 3 - the map
# ----------------------------------------------------------------------------------------------
def scene_map(ctx, t, os_):
    u = t - 9.4
    lat0, lon0, k = keys(u, [(-0.4, (40.71, -74.0, 620.0)), (0.5, (40.71, -74.0, 620.0)), (2.4, (39.75, -76.45, 182.0)), (6.2, (39.75, -76.45, 195.0))],
                         smoother)
    P = G.MapProj(lat0, lon0, k, 540, 830)
    s = screen(ctx, os_)
    G.draw_map(s, P, t)
    pts = {n: P.p(*q) for n, q in G.PLACES.items()}
    # dashed lines linking the three places, drawn as each is reached
    for (a, b, t0) in (('nyc', 'dc', 10.2), ('dc', 'shanksville', 11.8)):
        kk = smooth(ramp(t, t0, t0 + 0.6))
        if kk > 0:
            pa, pb = np.array(pts[a]), np.array(pts[b])
            G.line(s, [pa, pa + (pb - pa) * kk], 3, (*C['blue4'][:3], 0.6), dash=[10, 10])
    G.marker(s, *pts['nyc'], t, 9.55)
    G.marker(s, *pts['dc'], t, 10.35)
    G.marker(s, *pts['shanksville'], t, 11.95)
    labels = [('nyc', 9.7, 'NEW YORK CITY', '8:46 / 9:03 AM', -1), ('dc', 10.5, 'THE PENTAGON', '9:37 AM', -1),
              ('shanksville', 12.1, 'SHANKSVILLE, PA', '10:03 AM', 1)]
    for n, t0, name, tm, side in labels:
        kk = smooth(ramp(t, t0, t0 + 0.35))
        if kk <= 0:
            continue
        x, y = pts[n]
        ox = 34 * side
        al = 'left' if side > 0 else 'right'
        G.text(s, x + ox + (1 - kk) * 20 * side, y - 8, 34, name, (*C['white'][:3], kk), align=al, track=0.08)
        G.text(s, x + ox + (1 - kk) * 20 * side, y + 34, 30, tm, (*C['red2'][:3], kk), align=al, track=0.06)
    # the Pentagon drawn as a small inset beside Washington
    kp = smooth(ramp(t, 10.6, 11.0))
    if kp > 0:
        x, y = pts['dc']
        G.pentagon_icon(s, x - 60, y + 120, 60 * kp, C['white'], lw=3, a=kp)
    # Flight 93: a small inset label
    k9 = smooth(ramp(t, 13.0, 13.4))
    if k9 > 0:
        x, y = pts['shanksville']
        G.text(s, x + 34, y + 74, 28, 'UNITED FLIGHT 93', (*C['grey4'][:3], k9), align='left', track=0.1)
    s.restore()
    return dict(dark=0.08, desat=0.05, tint=(0.97, 1.0, 1.05), bloom=0.3)


# ----------------------------------------------------------------------------------------------
# Scene 4 - the aftermath: the skyline under smoke and dust; responders in the streets
# ----------------------------------------------------------------------------------------------
def scene_skysmoke(ctx, t, os_):
    u = t - 15.2
    cam = Camera(560, 960 - 15 * u, 1.18 - 0.02 * u)
    tow = 1 - smooth(ramp(t, 15.6, 16.9))
    skyline_scene(ctx, cam, t, os_, mood=0.85, towers=tow, smoke=1.0, sun=0.3)
    s = screen(ctx, os_)
    G.particles(s, t, 0, 0, W, H, n=70, seed=4, col=C['dust'], size=2.2, alpha=0.45, fall=28)
    s.restore()
    return dict(dark=0.2, desat=0.3, tint=(1.0, 0.98, 0.95), bloom=0.15)


RESP = [person('fireman', 900 + i) for i in range(7)]
CIVS = [person(['man', 'woman', 'man', 'woman', 'man'][i], 950 + i) for i in range(5)]


def scene_responders(ctx, t, os_):
    u = t - 18.4
    cam = Camera(520 + 40 * u, 1180, 1.12)
    gy = 1500
    with World(ctx, cam, 0.05, os_) as c:
        G.vgrad(c, -400, -400, 1600, 2400, [(0, mixc(C['grey3'], C['dust2'], 0.4)), (0.6, mixc(C['grey4'], C['dust'], 0.5)), (1, C['grey3'])])
    with World(ctx, cam, 0.3, os_) as c:
        G.skyline(c, -800, 2000, gy - 160, 1.4, 21, mixc(C['grey3'], C['dust2'], 0.4), haze=0.25)
        G.plume(c, 700, gy - 400, 2.2, t, seed=8, n=14, col=mixc(C['grey4'], C['dust'], 0.5), alpha=0.55, wind=0.6, spread=1.6)
    with World(ctx, cam, 0.6, os_) as c:
        G.skyline(c, -800, 2000, gy - 40, 2.0, 22, mixc(C['grey2'], C['navy2'], 0.3), haze=0.15, win=0.0)
    with World(ctx, cam, 1.0, os_) as c:
        G.rect(c, -1000, gy, 2400, 2600, mixc(C['grey2'], C['dust2'], 0.35))
        for k in range(30):
            G.line(c, [[-1000 + k * 120, gy + 40], [-1100 + k * 120, 2600]], 1.0, (*C['grey3'][:3], 0.25))
        G.fire_truck(c, 120, gy + 80, 62, t, face=1, seed=1)
        G.fire_truck(c, 1180, gy + 60, 56, t, face=-1, seed=2)
    tt = twos(t)
    dark = mixc(C['char'], C['navy1'], 0.4)
    rim = mixc(C['warm'], C['white'], 0.5)
    for i, (x, y, face, kind) in enumerate(((300, gy + 260, 1, 'walk'), (440, gy + 300, 1, 'walk'), (600, gy + 240, 1, 'walk'),
                                             (780, gy + 330, -1, 'idle'), (860, gy + 280, 1, 'walk'))):
        c_ = RESP[i]
        if kind == 'walk':
            p = poses.walk(tt + i * 0.21, c_['seed'], period=1.25, tired=0.4)
            xx = x + 70 * (u + 0.4)
        else:
            p = poses.gesture('point', tt, c_['seed'], turn=0.4)
            xx = x
        fig_sil(ctx, cam, c_, p, xx, y, 1.9, face, 1.0, os_, t, dark, rim)
    # people gathered at the barrier, some holding one another
    for i, (x, face) in enumerate(((1060, -1), (1140, -1), (1230, 1))):
        p = poses.react(tt, 18.4, CIVS[i]['seed'], ['cross', 'mouth', 'stare'][i], turn=0.3)
        fig_sil(ctx, cam, CIVS[i], p, x, gy + 200, 1.7, face, 1.0, os_, t, mixc(C['navy1'], C['grey1'], 0.4), rim)
    with World(ctx, cam, 1.0, os_) as c:
        G.rect(c, 980, gy + 160, 1400, gy + 172, (*C['white'][:3], 0.7))
        for k in range(5):
            G.rect(c, 990 + k * 90, gy + 160, 998 + k * 90, gy + 205, (*C['grey4'][:3], 0.8))
    s = screen(ctx, os_)
    G.particles(s, t, 0, 0, W, H, n=110, seed=7, col=C['dust'], size=2.4, alpha=0.5, fall=34, drift=14)
    g = cairo.LinearGradient(0, 1200, 0, 1920)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.05, 0.06, 0.08, 0.55)
    s.set_source(g)
    s.paint()
    s.restore()
    return dict(dark=0.22, desat=0.35, tint=(1.0, 0.98, 0.95), bloom=0.15)


# ----------------------------------------------------------------------------------------------
# Scene 5 - the memorial, the Tribute in Light, the channel mark
# ----------------------------------------------------------------------------------------------
def scene_memorial(ctx, t, os_):
    u = t - 22.2
    P = G.Persp(f=820 + 30 * u, cx=540 - 10 * u, hy=620, hcam=17.0 - 0.4 * u)
    s = screen(ctx, os_)
    G.vgrad(s, 0, 0, W, 640, [(0, C['navy1']), (0.7, C['navy3']), (1, mixc(C['blue2'], C['warm'], 0.25))])
    G.clouds(s, t, W, 120, 460, n=5, seed=9, speed=10, col=mixc(C['blue3'], C['grey4'], 0.4), a=0.5)
    G.skyline(s, -100, 1200, 622, 0.9, 31, mixc(C['navy2'], C['navy3'], 0.5), haze=0.05, win=0.15)
    G.one_wtc(s, 760, 622, 1.1, mixc(C['navy3'], C['blue1'], 0.35), rim=C['blue3'])
    G.rect(s, 0, 620, W, H, mixc(C['grey2'], C['navy2'], 0.45))
    # paving: lines converging on the horizon, and cross joints
    for k in range(-14, 15):
        G.line(s, [P.p(k * 4, 0, 6), P.p(k * 4, 0, 200)], 1.0, (*C['grey3'][:3], 0.25))
    for k in range(40):
        Z = 6 * 1.12 ** k
        G.line(s, [P.p(-80, 0, Z), P.p(80, 0, Z)], 1.0, (*C['grey3'][:3], 0.2))
    for k in range(6):
        for side in (-1, 1):
            X = side * 24
            Z = 26 + k * 10
            x, y = P.p(X, 0, Z)
            G.tree_round(s, x, y, 3400 / Z, mixc(C['navy3'], C['blue1'], 0.25), seed=k * 2 + (side > 0))
    G.memorial_pool(s, P, t, -15, 15, 17, 37, depth=7.0, lit=0.6)
    s.restore()
    return dict(dark=0.12, desat=0.06, tint=(0.97, 1.0, 1.05), bloom=0.3)


def scene_tribute(ctx, t, os_):
    u = t - 26.0
    cam = Camera(560, 900 - 20 * u, 1.05 + 0.02 * u)
    skyline_scene(ctx, cam, t, os_, night=1.0, towers=0.0, sun=0.0, beams=smooth(ramp(t, 25.8, 26.8)))
    return dict(dark=0.05, desat=0.05, tint=(0.95, 1.0, 1.08), bloom=0.45)


def scene_logo(ctx, t, os_):
    u = t - 28.4
    s = screen(ctx, os_)
    G.vgrad(s, 0, 0, W, H, [(0, C['navy0']), (1, C['navy1'])])
    a = smooth(ramp(u, 0.1, 0.6)) * (1 - smooth(ramp(t, 29.3, 29.95)))
    G.logo(s, W / 2, 1000, 1.25 + 0.02 * u, a, t)
    s.restore()
    return dict(dark=0.0, desat=0.0, bloom=0.2, vig=0.6)
