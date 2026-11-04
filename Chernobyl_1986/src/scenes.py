"""The scenes of the Chernobyl Short. Each scene function draws one frame at time t (seconds on the film
timeline) into a cairo context at output scale os_ and returns a 'look' dict for the finishing pass.
Depth comes only from flat layers moved at different speeds (the multiplane Camera in core.py)."""
import math

import cairo
import numpy as np

from core import (PAL, W, H, Camera, draw_layer, keys, smooth, smoother, ease_out, ease_in, clamp, ramp, lerp, twos, boil_seed,
                  hash01, fnoise, vnoise, set_c, ink_shape, ink_line, ellipse_pts, soft_glow, mix, shade_c, path_poly, load_png,
                  taper_stroke)
from figures import draw_figure
import poses
import world as Wd
import soviet as S
from chars import person, crowd
from props import fog_bank, dust, smoke, bird

FOG = mix(PAL['grey3'], PAL['parch2'], 0.3)
NIGHT_FOG = mix(PAL['charcoal'], PAL['grey2'], 0.45)
POND_T, POND_B = mix(PAL['grey2'], PAL['charcoal'], 0.55), mix(PAL['ink'], PAL['charcoal'], 0.5)


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
    return base / (cam.z ** d) ** 0.55


def ground(ctx, x0, x1, gy, y1, col, seed=0, lw=1.2):
    g = cairo.LinearGradient(0, gy, 0, gy + 420)
    g.add_color_stop_rgba(0, *mix(col, PAL['parch2'], 0.2)[:3], 1)
    g.add_color_stop_rgba(1, *shade_c(col, -0.12)[:3], 1)
    ctx.rectangle(x0, gy, x1 - x0, y1 - gy)
    ctx.set_source(g)
    ctx.fill()


def shake(t, t0, amp=14.0, dur=0.8):
    if t < t0 or t > t0 + dur:
        return 0.0, 0.0
    k = (1 - (t - t0) / dur) ** 2
    return amp * k * math.sin(t * 71), amp * k * math.cos(t * 53)


def walker(ctx, cam, c, x, y, s, face, t, os_, d=1.0, period=1.05, prop=None, ph=0.0):
    p = poses.walk(twos(t) + ph, c['seed'], period=period)
    if prop in ('suitcase', 'bag'):
        p.update(prop=prop, ua_f=0.05, fa_f=0.05)
    elif prop == 'clipboard':
        p.update(prop='clipboard', ua_f=0.4, fa_f=1.8)
    fig(ctx, cam, c, p, x, y, s, face, d, os_, t)


# ----------------------------------------------------------------------------------------------
# Scene 1 - the night: the plant across the cooling pond, then the explosion (at about 4.15 s)
# ----------------------------------------------------------------------------------------------
BLAST = 4.15


def blast_fx(c, x, y, s, t, t0):
    """The explosion in illustration: a flash, a fireball, debris flung up in arcs, a rising column."""
    u = t - t0
    if u < 0:
        return
    # the fireball: a ragged burst of light
    rr = (60 + 220 * ease_out(min(1.0, u * 2.5))) * s
    pts = [(x + math.cos(a) * rr * (0.75 + 0.35 * hash01(int(a * 10), 7)), y - abs(math.sin(a)) * rr * 1.2 * (0.8 + 0.3 * hash01(int(a * 7), 9)) + rr * 0.15)
           for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    fa = max(0.0, 1 - u * 0.8)
    ink_shape(c, np.array(pts), (*PAL['candle'][:3], fa), lw=2 * s, ink=(*PAL['burg2'][:3], fa), smooth_path=False)
    ink_shape(c, np.array(pts) * 0.6 + np.array([x, y]) * 0.4, (*PAL['candle2'][:3], fa), lw=0, smooth_path=False)
    soft_glow(c, x, y, (120 + 900 * min(1, u * 4)) * s, PAL['candle2'], max(0.0, 0.9 - u * 0.9))
    soft_glow(c, x, y, 260 * s, PAL['candle'], 0.7 * max(0.2, 1 - u * 0.5))
    for k in range(26):
        a = -math.pi / 2 + (hash01(k, 1) - 0.5) * 2.2
        v = (300 + 500 * hash01(k, 2)) * s
        px = x + math.cos(a) * v * u
        py = y + math.sin(a) * v * u + 0.5 * 900 * s * u * u
        L = 18 * s
        ink_line(c, np.array([[px, py], [px - math.cos(a) * L, py - math.sin(a) * L + 6 * s]]), max(1.0, 3 * s), PAL['ink'])
        if hash01(k, 3) < 0.4:
            c.arc(px, py, 3 * s, 0, 2 * math.pi)
            set_c(c, PAL['candle2'], max(0.0, 1 - u))
            c.fill()
    S.plume(c, x, y, s * 1.1, t, seed=3, n=18, alpha=0.85 * min(1, u * 3), lit=1.0, wind=0.15, top=clamp(u * 1.4))
    if u < 0.5:
        c.arc(x, y, (80 + 1400 * u) * s, 0, 2 * math.pi)
        set_c(c, PAL['linen'], 0.5 * (1 - u * 2))
        c.set_line_width(10 * s)
        c.stroke()


def scene_night(ctx, t, os_):
    u = t
    cx, cy, z = keys(u, [(0.0, (540.0, 1080.0, 1.0)), (4.0, (700.0, 1060.0, 1.45)), (5.4, (705.0, 1050.0, 1.5))], smooth)
    dx, dy = shake(t, BLAST + 0.05, 16, 0.9)
    cam = Camera(cx + dx, cy + dy, z)
    layer(ctx, cam, os_, 'sky_night', 0.08, -210, -440)
    with World(ctx, cam, 0.12, os_) as c:
        fog_bank(c, -300, 200, 1800, 300, 0.35, t, speed=6, seed=8)
    layer(ctx, cam, os_, 'city_far_night', 0.2, -900, 1110 - 1460, 1.0)
    layer(ctx, cam, os_, 'pines_far', 0.3, -760, 1150 - 1460)
    gy = 1150
    boom = u > BLAST
    with World(ctx, cam, 0.42, os_) as c:
        S.plant(c, 180, gy, 1.75, t, state='damaged' if boom else 'intact', lights=1.0, lw=0.9, glow=1.0 if boom else 0.0,
                fog=0.12, fogcol=NIGHT_FOG)
        for k in range(6):
            S.pylon(c, -200 + k * 120, gy, 90, 0.8, fog=0.3, fogcol=NIGHT_FOG)
        if boom:
            blast_fx(c, 180 + 305 * 1.75, gy - 70 * 1.75, 0.7, t, BLAST)
    # the cooling pond in front, with the lights reflected
    with World(ctx, cam, 0.7, os_) as c:
        Wd.sea(c, -900, 2200, 1215, 2400, t, pan=0, dark=1.0, top_col=POND_T, bot_col=POND_B, lw=1.0, chop=0.4)
        for k in range(14):
            rx = 200 + k * 55
            for j in range(6):
                yy = 1230 + j * 26 + 4 * math.sin(t * 2 + k + j)
                ink_line(c, np.array([[rx - 10, yy], [rx + 10, yy]]), 2.0, PAL['candle'], alpha=0.25 * (1 - j / 6))
        if boom:
            soft_glow(c, 690, 1300, 500, PAL['candle'], 0.3 * min(1, (u - BLAST) * 2))
    with World(ctx, cam, 1.0, os_) as c:
        Wd.grass_tufts(c, -300, 1400, 1960, 50, 3.0, 5, col=mix(PAL['green3'], PAL['ink'], 0.5), t=t, wind=0.6)
    if boom and u - BLAST < 0.12:
        s = screen(ctx, os_)
        set_c(s, PAL['linen'], 0.8 * (1 - (u - BLAST) / 0.12))
        s.paint()
        s.restore()
    if boom:
        return dict(dark=0.38, desat=0.25, tint=(1.0, 0.9, 0.82), vig=0.66, lift=0.03)
    return dict(dark=0.5, desat=0.35, tint=(0.82, 0.88, 1.0), vig=0.68, lift=0.03)


# ----------------------------------------------------------------------------------------------
# Scene 2 - Pripyat the day before
# ----------------------------------------------------------------------------------------------
CITY_GY = 1520


def bicycle(c, x, gy, s, t, speed, col):
    r = 0.34 * s
    for wx in (-0.55 * s, 0.55 * s):
        S._wheel(c, x + wx, gy - r, r, t, speed, 1.0, PAL['ink'])
    pts = [[x - 0.55 * s, gy - r], [x - 0.1 * s, gy - 0.9 * s], [x + 0.45 * s, gy - 0.9 * s], [x + 0.55 * s, gy - r], [x, gy - r], [x - 0.55 * s, gy - r]]
    ink_line(c, np.array(pts), max(1.0, 0.05 * s), col)
    ink_line(c, np.array([[x + 0.45 * s, gy - 0.9 * s], [x + 0.4 * s, gy - 1.05 * s], [x + 0.52 * s, gy - 1.08 * s]]), max(1.0, 0.04 * s), PAL['ink'])


def cyclist_pose(t, seed):
    p = poses.idle(t, seed, turn=0.85)
    ph = t * 6.0
    p.update(lean=0.25, ua_f=1.0, fa_f=1.3, ua_b=0.9, fa_b=1.3, th_f=1.2 + 0.35 * math.sin(ph), sh_f=0.2 + 0.4 * math.sin(ph + 1.2),
             th_b=1.2 - 0.35 * math.sin(ph), sh_b=0.2 - 0.4 * math.sin(ph + 1.2), bob=-18)
    return p


def city_street(ctx, cam, t, os_, layer_name='street_blocks', sky='sky_day', people=True, traffic=True, decay=0.0, plant_far=True, plume_far=0.0):
    layer(ctx, cam, os_, sky, 0.08, -210, -300)
    layer(ctx, cam, os_, 'pines_far', 0.25, -760, CITY_GY - 140 - 1460)
    if plant_far:
        with World(ctx, cam, 0.27, os_) as c:
            S.plant(c, 1150, CITY_GY - 140, 0.6, t, lw=0.6, fog=0.55, fogcol=FOG)
            if plume_far > 0:
                S.plume(c, 1150 + 300 * 0.6, CITY_GY - 140 - 40, 0.18, t, seed=9, n=14, alpha=0.6 * plume_far, wind=0.6, col=mix(PAL['grey2'], PAL['grey3'], 0.4))
    layer(ctx, cam, os_, layer_name, 0.62, -900, CITY_GY - 30 - 1470)
    lw = lwz(cam)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -1500, 3200, CITY_GY - 20, CITY_GY + 30, mix(PAL['green2'], PAL['parch3'], 0.35 + 0.2 * decay))
        S.road(c, -1500, 3200, CITY_GY + 260, CITY_GY + 30, 60, lw=lw, cracks=decay, seed=4)
        ink_shape(c, np.array([[-1500, CITY_GY + 275], [3200, CITY_GY + 275], [3200, 2600], [-1500, 2600]]),
                  mix(CONCRETE_PAVE, PAL['green3'], 0.25 * decay), lw=0, smooth_path=False)
        rng = np.random.default_rng(3)
        for k in range(60):
            x = -1500 + k * 80
            ink_line(c, np.array([[x, CITY_GY + 280], [x - 40, 2600]]), 0.8, PAL['ink'], alpha=0.25)
        for k in range(8):
            S.street_lamp(c, -1200 + k * 600, CITY_GY + 285, 520, k, lw=lw)
        if decay > 0:
            for k in range(3):
                Wd.grass_tufts(c, -1500, 3200, CITY_GY + 60 + k * 90, 90, 2.2 + 0.6 * k, 40 + k, t=t, wind=0.8, alpha=decay,
                               col=mix(PAL['green3'], PAL['parch3'], 0.3))
            Wd.grass_tufts(c, -1500, 3200, CITY_GY + 290, 120, 3.2, 47, t=t, wind=0.8, alpha=decay)


CONCRETE_PAVE = mix(PAL['grey3'], PAL['parch2'], 0.35)
CITY_PEOPLE = None


def scene_city(ctx, t, os_):
    global CITY_PEOPLE
    u = t - 5.0
    cx = 460 + 70 * (u + 0.5)
    cam = Camera(cx, 1240, 1.05)
    city_street(ctx, cam, t, os_)
    tt = twos(t)
    # traffic on the road
    with World(ctx, cam, 1.0, os_) as c:
        for k, (x0, v, col, lane) in enumerate(((-400, 260, PAL['green2'], 0), (1400, -300, PAL['burg2'], 1), (300, 220, PAL['linen2'], 0),
                                                 (2200, -260, PAL['grey'], 1))):
            x = x0 + v * u
            y = CITY_GY + (110 if lane == 0 else 200)
            if v > 0:
                S.car(c, x, y, 58, t, col, speed=v, face=1, lw=1.2)
            else:
                S.car(c, x, y, 62, t, col, speed=-v, face=-1, lw=1.2)
        S.bus(c, 2600 - 200 * (u + 0.5), CITY_GY + 210, 60, t, speed=200, face=-1, lw=1.2)
    if CITY_PEOPLE is None:
        CITY_PEOPLE = crowd(12, 3)
    ppl = CITY_PEOPLE
    # the pavement: people walking both ways, a cyclist, children with satchels
    lanes = [(CITY_GY + 330, 1.25), (CITY_GY + 420, 1.4), (CITY_GY + 520, 1.55)]
    specs = [(0, 0, 1, 70, -300, 'bag'), (1, 1, -1, 60, 1400, None), (2, 2, 1, 55, 200, None), (3, 0, -1, 65, 1700, None),
             (4, 2, 1, 80, 600, None), (5, 1, 1, 75, 900, 'bag'), (6, 0, -1, 50, 1100, 'bag'), (7, 2, -1, 70, 1900, None),
             (8, 1, 1, 60, -100, None), (9, 0, 1, 90, 1300, None)]
    for i, lane, face, v, x0, prop in sorted(specs, key=lambda a: a[1]):
        y, s = lanes[lane]
        x = x0 + face * v * (u + 0.5)
        c_ = ppl[i]
        per = 0.75 if c_['age'] == 'child' else 1.05
        walker(ctx, cam, c_, x, y, s, face, t, os_, period=per, prop=prop, ph=i * 0.3)
    # a cyclist
    bx = -200 + 260 * (u + 0.5)
    with World(ctx, cam, 1.0, os_) as c:
        bicycle(c, bx, CITY_GY + 470, 118, t, 260, PAL['burg2'])
    fig(ctx, cam, person('boy', 41, age='young', height=150), cyclist_pose(tt, 41), bx - 10, CITY_GY + 470 - 2, 1.3, 1, 1.0, os_, t)
    with World(ctx, cam, 1.3, os_) as c:
        for k, x in enumerate((-260, 1560)):
            S.poplar(c, x, 2300, 1500, 50 + k, lw=1.6, t=t, sway=1.0)
    return dict(dark=0.04, desat=0.25, tint=(1.0, 0.97, 0.9), vig=0.5)


# ----------------------------------------------------------------------------------------------
# Scene 3 - the control room
# ----------------------------------------------------------------------------------------------
OPS = [person('operator', 500 + i) for i in range(5)]


def control_room(ctx, cam, t, os_, alarm=0.0, flicker=0.0):
    lw = lwz(cam)
    with World(ctx, cam, 0.85, os_) as c:
        set_c(c, mix(PAL['grey2'], PAL['green3'], 0.4))
        c.rectangle(-1200, -200, 3600, 2600)
        c.fill()
        # ceiling light panels
        for k in range(8):
            fl = 1.0 if not (flicker > 0 and hash01(k, int(t * 15)) < flicker) else 0.2
            x = -600 + k * 330
            ink_shape(c, np.array([[x, 300], [x + 240, 300], [x + 260, 340], [x - 20, 340]]), mix(PAL['linen'], PAL['grey3'], 1 - fl), lw=1.0,
                      smooth_path=False)
            soft_glow(c, x + 120, 330, 220, PAL['linen'], 0.25 * fl)
        S.panel_wall(c, -900, 2000, 520, 1380, t, alarm=alarm, lw=lw, seed=4)
        S.core_grid(c, 560, 800, 200, t, alarm=alarm)
        set_c(c, mix(PAL['grey3'], PAL['parch2'], 0.3))
        c.rectangle(-1200, 1380, 3600, 1000)
        c.fill()
    with World(ctx, cam, 1.0, os_) as c:
        if alarm > 0:
            soft_glow(c, 560, 900, 900, (0.9, 0.2, 0.15, 1.0), 0.12 * alarm * (0.6 + 0.4 * math.sin(t * 12)))


def scene_control(ctx, t, os_):
    u = t - 11.0
    cx, cy, z = keys(u, [(-0.5, (420.0, 1200.0, 1.0)), (3.4, (600.0, 1220.0, 1.12))], smooth)
    cam = Camera(cx, cy, z)
    control_room(ctx, cam, t, os_)
    tt = twos(t)
    specs = [(0, 'clipboard', 150, 1640, 1), (1, 'reach', 470, 1660, 1), (2, 'reach', 760, 1660, -1), (3, 'fold', 1060, 1620, -1)]
    with World(ctx, cam, 1.0, os_) as c:
        pass
    for i, kind, x, y, face in specs:
        if kind == 'clipboard':
            p = poses.gesture('write', tt, 500 + i, turn=0.5)
            p['prop'] = 'clipboard'
        elif kind == 'reach':
            p = poses.idle(tt, 500 + i, turn=0.8)
            a = 0.5 + 0.5 * math.sin(tt * 1.3 + i)
            p.update(ua_f=1.0 + 0.2 * a, fa_f=1.7 + 0.2 * a, lean=0.2, lookv=0.3, brow=0.5)
        else:
            p = poses.gesture('fold', tt, 500 + i, turn=0.5)
        fig(ctx, cam, OPS[i], p, x, y, 2.6, face, 1.0, os_, t)
    with World(ctx, cam, 1.0, os_) as c:
        S.console(c, -200, 1300, 1700, 1820, t, lw=lwz(cam), seed=2)
        ink_shape(c, np.array([[-400, 1940], [1600, 1940], [1600, 2600], [-400, 2600]]), shade_c(PAL['grey2'], -0.3), lw=0, smooth_path=False)
    return dict(dark=0.2, desat=0.32, tint=(0.92, 0.98, 0.95), vig=0.58)


def scene_gauges(ctx, t, os_):
    u = t - 14.0
    z = lerp(1.75, 2.0, smooth(u / 2.4))
    cam = Camera(570 + 10 * u, 860, z)
    alarm = smooth(ramp(t, 15.2, 16.2))
    control_room(ctx, cam, t, os_, alarm=alarm)
    with World(ctx, cam, 1.0, os_) as c:
        # a large dial in the foreground panel: the needle climbs, then swings hard over
        v = 0.25 + 0.25 * smooth(ramp(t, 14.0, 15.4)) + 0.6 * ease_in(ramp(t, 15.6, 16.4)) + 0.02 * math.sin(t * 30)
        ink_shape(c, np.array([[340, 600], [800, 600], [800, 1060], [340, 1060]]), mix(PAL['green2'], PAL['grey3'], 0.4), lw=1.6, smooth_path=False,
                  shadow=(shade_c(PAL['green2'], -0.3), 12))
        S.dial(c, 570, 820, 170, v, lw=1.6, label='МВт', red=alarm * (0.6 + 0.4 * math.sin(t * 14)))
        for k in range(5):
            S.lamp(c, 380 + k * 95, 1020, 16, 1.0 if (alarm > 0.4 and (t * 4 + k * 0.3) % 1 < 0.6) else 0.1)
    return dict(dark=0.25, desat=0.3, tint=(0.95, 0.96, 0.94), vig=0.66)


def scene_faces(ctx, t, os_):
    u = t - 16.4
    dx, dy = shake(t, 17.45, 22, 0.6)
    cam = Camera(600 + dx, 1180 + dy, 1.55 + 0.05 * u)
    alarm = 1.0
    flick = 0.55 if t > 17.45 else 0.0
    control_room(ctx, cam, t, os_, alarm=alarm, flicker=flick)
    tt = twos(t)
    for i, (x, face, kind) in enumerate(((430, 1, 'stare'), (760, -1, 'recoil'))):
        p = poses.react(tt, 16.5 + i * 0.25, 510 + i, kind, turn=0.35, look_dir=-1 if face < 0 else 1)
        p['lookv'] = -0.3
        fig(ctx, cam, OPS[i + 1], p, x, 1700, 3.4, face, 1.0, os_, t)
    with World(ctx, cam, 1.0, os_) as c:
        soft_glow(c, 600, 1150, 700, (0.95, 0.2, 0.15, 1.0), 0.22 * (0.6 + 0.4 * math.sin(t * 12)))
        S.console(c, -200, 1400, 1620, 1760, t, lw=lwz(cam), alarm=1.0, seed=3)
    if 17.45 < t < 17.58:
        s = screen(ctx, os_)
        set_c(s, PAL['linen'], 0.6)
        s.paint()
        s.restore()
    return dict(dark=0.35, desat=0.3, tint=(1.0, 0.88, 0.85), vig=0.72)


# ----------------------------------------------------------------------------------------------
# Scene 4 - Reactor 4 destroyed, burning
# ----------------------------------------------------------------------------------------------
PLANT_GY = 1600


def burning_plant(c, t, s=4.0, x0=-500, glow=1.0, wind=0.25):
    S.plant(c, x0, PLANT_GY, s, t, state='damaged', lights=0.6, lw=1.3, glow=glow, seed=2)
    cx = x0 + 305 * s
    top = PLANT_GY - 60 * s
    fl = 1 + 0.1 * math.sin(t * 6) + 0.06 * math.sin(t * 15)
    soft_glow(c, cx, top + 20 * s, 160 * s * fl, PAL['candle'], 0.35 * glow)
    S.plume(c, cx + 10 * s, top - 30 * s, s * 0.55, t, seed=4, n=18, alpha=0.8, lit=0.9, wind=wind)
    S.plume(c, cx + 40 * s, top - 10 * s, s * 0.35, t + 3.0, seed=5, n=12, alpha=0.65, lit=0.7, wind=wind + 0.1)
    # fires on the roof of the turbine hall
    for k in range(6):
        fx = x0 + (262 + k * 24) * s
        fy = PLANT_GY - 30 * s
        fl = 1 + 0.3 * math.sin(t * (11 + k * 3) + k)
        for j in range(3):
            w = (5 - j) * s
            ink_shape(c, np.array([[fx - w, fy], [fx - w * 0.4, fy - 10 * s * fl], [fx + (j - 1) * s, fy - (18 - j * 4) * s * fl], [fx + w * 0.5, fy - 9 * s * fl],
                                   [fx + w, fy]]), [PAL['burg2'], PAL['candle'], PAL['candle2']][j], lw=0.8 if j == 0 else 0, ink=PAL['burg3'],
                      seed=k * 3 + j + int(t * 15))
        soft_glow(c, fx, fy - 8 * s, 30 * s, PAL['candle'], 0.4)
    S.embers(c, cx - 80 * s, cx + 120 * s, top - 300 * s, top + 20 * s, t, n=50, seed=3, size=1.2 * s)


def scene_fire(ctx, t, os_):
    u = t - 18.0
    cx, cy, z = keys(u, [(-0.5, (700.0, 1230.0, 1.2)), (7.4, (760.0, 1300.0, 1.42))], smooth)
    cam = Camera(cx, cy, z)
    layer(ctx, cam, os_, 'sky_night', 0.08, -210, -440)
    layer(ctx, cam, os_, 'pines_far', 0.3, -760, PLANT_GY - 20 - 1460)
    with World(ctx, cam, 0.5, os_) as c:
        for k in range(4):
            S.pylon(c, -300 + k * 380, PLANT_GY, 300, 1.2, fog=0.35, fogcol=NIGHT_FOG)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -2000, 3000, PLANT_GY, 2800, mix(PAL['charcoal2'], PAL['brown'], 0.3))
        burning_plant(c, t)
        # emergency lights far off at the foot of the building
        for k in range(4):
            bx = 300 + k * 160
            ph = (t * 2.2 + k * 0.4) % 1.0
            if ph < 0.25 or 0.5 < ph < 0.75:
                soft_glow(c, bx, PLANT_GY - 10, 50, (0.45, 0.6, 0.95, 1.0), 0.6)
    s = screen(ctx, os_)
    S.embers(s, 0, W, 300, H, t, n=30, seed=8, size=2.0, alpha=0.7)
    s.restore()
    return dict(dark=0.4, desat=0.25, tint=(1.0, 0.86, 0.78), vig=0.68, lift=0.03)


# ----------------------------------------------------------------------------------------------
# Scene 5 - the firefighters
# ----------------------------------------------------------------------------------------------
FIREMEN = [person('fireman', 600 + i) for i in range(8)]


def scene_firemen(ctx, t, os_):
    u = t - 25.0
    cx, cy, z = keys(u, [(-0.5, (380.0, 1380.0, 1.1)), (7.4, (760.0, 1400.0, 1.15))], smooth)
    cam = Camera(cx, cy, z)
    layer(ctx, cam, os_, 'sky_night', 0.08, -210, -440)
    with World(ctx, cam, 0.5, os_) as c:
        burning_plant(c, t, s=3.2, x0=-200, glow=0.8, wind=0.3)
    gy = 1700
    with World(ctx, cam, 0.8, os_) as c:
        for k in range(3):
            ang = -math.pi / 2 + 0.5 * math.sin(t * 0.5 + k * 2.1)
            S.searchlight(c, 200 + k * 500, gy - 20, ang, 1600, 140, 0.12)
    lw = lwz(cam)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -1500, 3000, gy, 2800, mix(PAL['charcoal2'], PAL['grey2'], 0.4))
        # trucks: two parked, one arriving and braking
        S.fire_engine(c, 140, gy + 40, 70, t, face=1, lw=lw, seed=1, lights=0.8)
        x3 = lerp(-1100, 820, ease_out(clamp((u + 0.5) / 4.0)))
        v3 = 480 * (1 - clamp((u + 0.5) / 4.0)) ** 2
        S.fire_engine(c, x3, gy + 120, 76, t, speed=v3, face=1, lw=lw, seed=2, lights=1.0)
        S.fire_engine(c, 1500, gy + 30, 66, t, face=-1, lw=lw, seed=3, lights=0.6)
        # hose lines across the ground
        for k in range(3):
            ink_line(c, np.array([[100 + k * 200, gy + 220], [400 + k * 200, gy + 120], [700 + k * 250, gy + 60]]), 5, shade_c(PAL['parch3'], -0.2))
    tt = twos(t)
    # crews: two on a hose, others running to the building, one directing
    for i, (x, y, face, kind) in enumerate(((420, gy + 230, 1, 'hose'), (530, gy + 240, 1, 'hose'), (900, gy + 180, 1, 'run'),
                                             (1050, gy + 200, 1, 'run'), (300, gy + 260, -1, 'point'), (1250, gy + 170, 1, 'run'))):
        c_ = FIREMEN[i]
        if kind == 'hose':
            p = poses.idle(tt, 600 + i, turn=0.75)
            p.update(prop='hose', ua_f=1.0, fa_f=1.45, ua_b=0.9, fa_b=1.4, arms_front=True, lean=0.25, th_f=0.4, sh_f=0.1, spray=1.0, prop_t=t)
            fig(ctx, cam, c_, p, x, y, 1.6, face, 1.0, os_, t)
        elif kind == 'run':
            p = poses.walk(tt + i * 0.2, 600 + i, period=0.62, stride=1.25)
            p['lean'] = 0.2
            fig(ctx, cam, c_, p, x + 160 * (u + 0.5) * (0.5 + 0.1 * i), y, 1.6, face, 1.0, os_, t)
        else:
            p = poses.gesture('point', tt, 600 + i, turn=0.6)
            fig(ctx, cam, c_, p, x, y, 1.65, face, 1.0, os_, t)
    s = screen(ctx, os_)
    S.embers(s, 0, W, 200, H, t, n=40, seed=9, size=2.2, alpha=0.8)
    s.restore()
    return dict(dark=0.45, desat=0.3, tint=(0.9, 0.9, 1.0), vig=0.7, lift=0.03)


# ----------------------------------------------------------------------------------------------
# Scene 6 - Saturday morning in Pripyat
# ----------------------------------------------------------------------------------------------
MORNING_PEOPLE = None


def scene_morning(ctx, t, os_):
    global MORNING_PEOPLE
    u = t - 32.0
    cx = 520 + 60 * (u + 0.5)
    cam = Camera(cx, 1300, 1.2)
    layer(ctx, cam, os_, 'sky_day', 0.08, -210, -300)
    layer(ctx, cam, os_, 'pines_far', 0.25, -760, CITY_GY - 140 - 1460)
    with World(ctx, cam, 0.27, os_) as c:
        S.plume(c, 1450, CITY_GY - 160, 0.16, t, seed=9, n=14, alpha=0.55, wind=0.7, col=mix(PAL['grey2'], PAL['grey3'], 0.5))
    layer(ctx, cam, os_, 'school', 0.62, -40, CITY_GY - 30 - 1470)
    lw = lwz(cam)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -1500, 3200, CITY_GY + 60, 2600, mix(CONCRETE_PAVE, PAL['green2'], 0.25))
        for k in range(50):
            x = -1500 + k * 90
            ink_line(c, np.array([[x, CITY_GY + 70], [x - 50, 2600]]), 0.8, PAL['ink'], alpha=0.22)
        # a bench with two older women
    if MORNING_PEOPLE is None:
        MORNING_PEOPLE = crowd(14, 7, kinds=('girl', 'boy', 'woman', 'man', 'girl', 'boy', 'woman', 'boy'))
    ppl = MORNING_PEOPLE
    tt = twos(t)
    # two neighbours stop to talk
    for k, x in enumerate((900, 1010)):
        p = poses.gesture('talk' if k == 0 else 'fold', tt, 700 + k, turn=0.45)
        fig(ctx, cam, person('woman', 720 + k, age='old' if k else 'adult'), p, x, CITY_GY + 250, 1.3, 1 if k == 0 else -1, 1.0, os_, t)
    specs = [(0, CITY_GY + 200, 1, 55, -200, 0.75), (1, CITY_GY + 210, 1, 60, -120, 0.7), (2, CITY_GY + 230, 1, 45, -330, 1.05),
             (3, CITY_GY + 320, -1, 55, 1700, 1.05), (4, CITY_GY + 340, -1, 70, 1500, 0.75), (5, CITY_GY + 420, 1, 65, 200, 0.7),
             (6, CITY_GY + 440, 1, 50, 120, 1.05), (7, CITY_GY + 280, -1, 75, 1200, 0.7)]
    for i, y, face, v, x0, per in sorted(specs, key=lambda a: a[1]):
        s_ = 1.3 + (y - CITY_GY - 200) / 240 * 0.35
        walker(ctx, cam, ppl[i], x0 + face * v * (u + 0.5), y, s_, face, t, os_, period=per, ph=i * 0.37,
               prop='bag' if ppl[i]['age'] != 'child' and i % 2 else None)
    # children playing with a ball
    bx = 500 + 120 * math.sin(t * 1.6)
    by = CITY_GY + 450 - abs(math.sin(t * 3.2)) * 120
    for k, (kx, face) in enumerate(((330, 1), (680, -1))):
        p = poses.idle(tt, 800 + k, turn=0.6)
        p.update(ua_f=0.8 + 0.6 * abs(math.sin(t * 3.2 + k)), fa_f=1.6, lean=0.1, smile=0.5)
        fig(ctx, cam, ppl[8 + k] if len(ppl) > 9 else ppl[k], p, kx, CITY_GY + 480, 1.5, face, 1.0, os_, t)
    with World(ctx, cam, 1.0, os_) as c:
        ink_shape(c, ellipse_pts(bx, by, 16, 16, 14), PAL['burg2'], lw=1.2)
        ink_shape(c, ellipse_pts(bx, CITY_GY + 484, 16, 4, 10), (0, 0, 0, 0.2), lw=0)
    with World(ctx, cam, 1.3, os_) as c:
        for k, x in enumerate((-380, 1500)):
            S.poplar(c, x, 2300, 1500, 60 + k, lw=1.6, t=t, sway=1.0)
    return dict(dark=0.06, desat=0.25, tint=(1.0, 0.97, 0.88), vig=0.5)


# ----------------------------------------------------------------------------------------------
# Scene 7 - the evacuation, 27 April
# ----------------------------------------------------------------------------------------------
EVAC = None


def scene_buses(ctx, t, os_):
    global EVAC
    u = t - 39.0
    cx, cy, z = keys(u, [(-0.5, (700.0, 1260.0, 1.05)), (3.0, (560.0, 1250.0, 1.05)), (7.5, (-120.0, 1250.0, 1.05))], smooth)
    cam = Camera(cx, cy, z)
    city_street(ctx, cam, t, os_, sky='sky_grey', plant_far=True, plume_far=0.4)
    if EVAC is None:
        EVAC = crowd(16, 11, kinds=('woman', 'man', 'girl', 'woman', 'boy', 'man', 'woman', 'woman'))
    lw = lwz(cam)
    tt = twos(t)
    # the column of buses: the leading ones pull away to the left
    with World(ctx, cam, 1.0, os_) as c:
        for k in range(7):
            start = 40.4 + k * 0.55
            dep = ease_in(clamp((t - start) / 3.0)) * 3.0
            x = 380 + k * 640 - 320 * max(0.0, t - start) * min(1.0, max(0.0, t - start) / 2.0)
            heads = [((PAL['skin'], PAL['hair_br']) if hash01(k, j) < 0.7 else None) for j in range(6)]
            S.bus(c, x, CITY_GY + 200, 62, t, speed=320 if t > start else 0, face=-1, lw=lw, seed=k, faces=heads,
                  livery=[(mix(PAL['linen2'], PAL['parch2'], 0.4), mix(PAL['burg2'], PAL['candle'], 0.25)),
                          (mix(PAL['linen2'], PAL['parch2'], 0.4), mix(PAL['green2'], PAL['grey2'], 0.4)),
                          (mix(PAL['candle'], PAL['parch3'], 0.4), mix(PAL['linen2'], PAL['grey3'], 0.4))][k % 3])
            _ = dep
    # residents queueing on the pavement with suitcases and bags, a militia officer and an official
    for i in range(10):
        c_ = EVAC[i]
        qx = 300 + i * 95
        y = CITY_GY + 330 + (i % 2) * 40
        board = 39.2 + i * 0.25
        if t > board:
            x = qx - 120 * (t - board)
            if x < -900:
                continue
            walker(ctx, cam, c_, x, y, 1.35, -1, t, os_, period=0.95 if c_['age'] != 'child' else 0.7,
                   prop=['suitcase', 'bag', None][i % 3] if c_['age'] != 'child' else None, ph=i * 0.3)
        else:
            p = poses.idle(tt, c_['seed'], turn=0.4)
            if c_['age'] != 'child':
                p.update(prop=['suitcase', 'bag', 'suitcase'][i % 3], ua_f=0.05, fa_f=0.05)
            fig(ctx, cam, c_, p, qx, y, 1.35, -1, 1.0, os_, t)
    p = poses.wave_hand(tt, 31, turn=0.5)
    p['ua_f'] = 1.6
    p['fa_f'] = 1.7
    fig(ctx, cam, person('militia', 31), p, 120, CITY_GY + 420, 1.45, -1, 1.0, os_, t)
    p = poses.gesture('write', tt, 32, turn=0.5)
    p['prop'] = 'clipboard'
    fig(ctx, cam, person('official', 32), p, 1260, CITY_GY + 420, 1.45, -1, 1.0, os_, t)
    return dict(dark=0.18, desat=0.35, tint=(0.95, 0.95, 0.93), vig=0.58)


# ----------------------------------------------------------------------------------------------
# Scene 8 - the empty city: the street, then years later; the funfair
# ----------------------------------------------------------------------------------------------
def scene_empty(ctx, t, os_):
    u = t - 46.0
    cam = Camera(300 + 40 * u, 1240, 1.05 + 0.02 * u)
    k = smooth(ramp(t, 46.8, 48.6))
    city_street(ctx, cam, t, os_, layer_name='street_blocks', sky='sky_grey', plant_far=False)
    if k > 0.01:
        sub = cairo.Context(ctx.get_target())
        sub.push_group()
        city_street(sub, cam, t, os_, layer_name='street_empty', sky='sky_grey', plant_far=False, decay=1.0)
        sub.pop_group_to_source()
        sub.paint_with_alpha(k)
    s = screen(ctx, os_)
    leaves = mix(PAL['brown3'], PAL['green2'], 0.3)
    for i in range(14):
        ph = (t * 0.2 + hash01(i, 3)) % 1.0
        x = (hash01(i, 4) * W + ph * 900) % (W + 200) - 100
        y = 1500 + 300 * hash01(i, 5) - 200 * math.sin(ph * 6)
        ink_shape(s, ellipse_pts(x, y, 7, 3, 8, rot=t * 3 + i), leaves, lw=0.6)
    s.restore()
    return dict(dark=0.25 + 0.1 * k, desat=0.38 + 0.1 * k, tint=(0.93, 0.95, 0.92), vig=0.62)


def scene_funfair(ctx, t, os_):
    u = t - 49.6
    cx, cy, z = keys(u, [(-0.4, (420.0, 1150.0, 1.0)), (3.6, (560.0, 1120.0, 1.1))], smooth)
    cam = Camera(cx, cy, z)
    layer(ctx, cam, os_, 'sky_grey', 0.08, -210, -330)
    layer(ctx, cam, os_, 'street_empty', 0.4, -1100, 1500 - 1470 - 120, 1.0)
    gy = 1560
    lw = lwz(cam)
    with World(ctx, cam, 0.75, os_) as c:
        ground(c, -1200, 2600, gy - 40, 2400, mix(PAL['green3'], PAL['parch3'], 0.3))
        S.ferris_wheel(c, 700, gy - 560, 470, t, lw=1.4)
        for k, x in enumerate((-260, 80, 1330, 1620)):
            Wd.oak(c, x, gy - 30, 380 + 60 * k, 950 + k, lw=1.2, moss=False)
        Wd.grass_tufts(c, -1200, 2600, gy - 30, 160, 2.2, 11, t=t, wind=1.0)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -1200, 2600, gy + 120, 2600, mix(PAL['green3'], PAL['brown'], 0.4))
        S.swings(c, 260, gy + 330, 120, t, lw=lw, wind=1.0)
        for k in range(4):
            Wd.grass_tufts(c, -1200, 2600, gy + 140 + k * 90, 110, 2.6 + 0.6 * k, 60 + k, t=t, wind=1.0)
    s = screen(ctx, os_)
    for i in range(18):
        ph = (t * 0.25 + hash01(i, 3)) % 1.0
        x = (hash01(i, 4) * W + ph * 1100) % (W + 200) - 100
        y = 600 + 1200 * hash01(i, 5) - 160 * math.sin(ph * 6 + i)
        ink_shape(s, ellipse_pts(x, y, 7, 3, 8, rot=t * 3 + i), mix(PAL['brown3'], PAL['burg2'], 0.3), lw=0.6)
    s.restore()
    return dict(dark=0.35, desat=0.48, tint=(0.92, 0.95, 0.92), vig=0.66)


# ----------------------------------------------------------------------------------------------
# Scene 9 - the legacy
# ----------------------------------------------------------------------------------------------
def scene_arch(ctx, t, os_):
    u = t - 53.0
    cam = Camera(620 + 20 * u, 1300, 1.2 + 0.05 * u)
    layer(ctx, cam, os_, 'sky_dusk', 0.08, -210, -330)
    layer(ctx, cam, os_, 'pines_far', 0.3, -760, PLANT_GY - 20 - 1460)
    with World(ctx, cam, 0.5, os_) as c:
        for k in range(5):
            S.pylon(c, -400 + k * 360, PLANT_GY - 40, 260, 1.1, fog=0.3, fogcol=FOG)
    with World(ctx, cam, 1.0, os_) as c:
        ground(c, -2000, 3000, PLANT_GY, 2800, mix(PAL['grey2'], PAL['green3'], 0.4))
        # Unit 3 and the turbine hall, the old Shelter hidden under the arch (the stack came down in 2013)
        wall = mix(CONCRETE_PAVE, PAL['grey'], 0.3)
        Wd.R(c, -900, PLANT_GY - 330, -200, PLANT_GY - 120, wall, 1.3)
        Wd.R(c, -900, PLANT_GY - 120, 1900, PLANT_GY, mix(CONCRETE_PAVE, PAL['parch3'], 0.2), 1.3)
        S.nsc(c, 620, PLANT_GY, 4.6, lw=1.6)
        fog_bank(c, -1200, PLANT_GY - 180, 3600, 300, 0.4, t, speed=18, seed=4)
    s = screen(ctx, os_)
    for i in range(6):
        bird(s, (200 + i * 160 + t * 40) % 1200 - 60, 500 + 40 * math.sin(i + t), 1.6, t, i)
    s.restore()
    return dict(dark=0.3, desat=0.4, tint=(0.97, 0.93, 0.88), vig=0.62)


def scene_aerial(ctx, t, os_):
    u = t - 55.4
    cam = Camera(800 + 40 * u, 1200 + 90 * u, 0.9 + 0.04 * u)
    layer(ctx, cam, os_, 'aerial', 1.0, 0, 0, 1.0)
    with World(ctx, cam, 1.0, os_) as c:
        fog_bank(c, -200, 900, 2200, 800, 0.45, t, speed=30, seed=3)
    return dict(dark=0.35, desat=0.42, tint=(0.94, 0.95, 0.92), vig=0.66)


def scene_card(ctx, t, os_):
    u = t - 56.8
    s = screen(ctx, os_)
    set_c(s, mix(PAL['parch2'], PAL['charcoal'], 0.55))
    s.paint()
    # the reactor building, faintly, like a print in the paper
    s.save()
    s.translate(W / 2, 1400)
    s.scale(0.9 + 0.02 * u, 0.9 + 0.02 * u)
    s.translate(-W / 2, -1400)
    s.push_group()
    S.nsc(s, 540, 1500, 2.6, lw=1.4)
    s.pop_group_to_source()
    s.paint_with_alpha(0.14)
    s.restore()
    k = smooth(ramp(t, 58.6, 59.75))
    if k > 0:
        set_c(s, PAL['ink'], 0.97 * k)
        s.paint()
    s.restore()
    return dict(dark=0.4 + 0.3 * k, desat=0.3, tint=(0.97, 0.92, 0.84), vig=0.7)
