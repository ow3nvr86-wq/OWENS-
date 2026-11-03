"""Scenes 2, 4, 5, 6, 7, 8 and the end card."""
import math

import cairo
import numpy as np

from core import (PAL, W, H, EV, Camera, draw_layer, keys, smooth, smoother, ease_out, ease_in, clamp, ramp, lerp,
                  twos, boil_seed, hash01, fnoise, set_c, ink_shape, ink_line, ellipse_pts, soft_glow, mix, shade_c,
                  path_smooth, taper_stroke, hatch_lines)
from figures import make_char, draw_figure
import poses
from props import handcart, fog_bank, dust, smoke, bird, ink_splats, candle
from scenes import S, DANCER, dancer_pose
from sets2 import MAP_STAGE, MAP_SPOTS


def figure_at(ctx, cam, c, p, x, y, s, face, d, os_, t, alpha=1.0):
    sx, sy = cam.world_to_screen(x, y, d)
    sc = s * cam.z ** d
    ctx.save()
    ctx.scale(os_, os_)
    draw_figure(ctx, c, p, sx, sy, sc, face, pix=sc * os_, boil_k=boil_seed(t), alpha=alpha)
    ctx.restore()


def layers(ctx, cam, os_, L):
    for name, d, sc in L:
        draw_layer(ctx, cam, name, d, os_, 0, 0, sc)


def in_world(ctx, cam, d, os_):
    ctx.save()
    cam.apply(ctx, d, os_)


# ----------------------------------------------------------------------------------------------
# Scene 2 - THE CITY
# ----------------------------------------------------------------------------------------------
CITY_WALKERS = None


def scene_city(ctx, t, os_):
    global CITY_WALKERS
    a, b = S('city')
    u = t - a
    cam = Camera(lerp(470, 690, smoother(u / 4.6)), 960, 1.02 + 0.03 * u / 4)
    layers(ctx, cam, os_, [('city_sky.png', 0.1, 1.0)])
    in_world(ctx, cam, 0.1, os_)
    for k in range(7):
        bird(ctx, (300 + k * 70 + u * 90 + 30 * math.sin(k)) % 1500, 300 + 40 * math.sin(k * 1.7 + u), 1.6, t, k)
    ctx.restore()
    layers(ctx, cam, os_, [('city_far.png', 0.3, 1.25)])
    in_world(ctx, cam, 0.3, os_)
    for k, (sx, sy) in enumerate([(220, 820), (520, 860), (1150, 830), (1420, 850)]):
        smoke(ctx, sx, sy, 1.4, t, seed=k + 3, alpha=0.4)
    fog_bank(ctx, -200, 820, 1900, 380, 0.35, t, speed=8, seed=6)
    ctx.restore()
    layers(ctx, cam, os_, [('city_mid.png', 0.6, 1.4)])
    in_world(ctx, cam, 0.6, os_)
    # the river moves: ripples and a boatman poling a flat boat
    for k in range(60):
        rx = (hash01(k, 1) * 2000 + u * (20 + 30 * hash01(k, 2))) % 2000 - 80
        ry = 1362 + hash01(k, 3) * 150
        L = 20 + 40 * hash01(k, 4)
        ink_line(ctx, np.array([[rx, ry], [rx + L, ry]]), 1.2, PAL['parch2'], alpha=0.35 + 0.2 * math.sin(t * 3 + k))
    bx = 300 + u * 55
    ink_shape(ctx, np.array([[bx - 150, 1420], [bx + 150, 1420], [bx + 130, 1446], [bx - 130, 1446]]), PAL['wood2'], lw=1.6, smooth_path=False)
    c = make_char(201, 'm', 'adult', head='hood')
    p = poses.idle(twos(t), 201, turn=0.8)
    pole = 0.5 + 0.5 * math.sin(u * 1.8)
    p['ua_f'], p['fa_f'], p['ua_b'], p['fa_b'] = 2.2 - 0.4 * pole, 2.6, 2.0 - 0.4 * pole, 2.8
    p['lean'] = 0.15 * pole
    draw_figure(ctx, c, p, bx + 40, 1424, 1.25, 1, pix=1.25 * cam.z ** 0.6 * os_, boil_k=boil_seed(t))
    ink_line(ctx, np.array([[bx + 70 - 40 * pole, 1230], [bx + 20 + 30 * pole, 1500]]), 2.2, PAL['wood2'])
    ctx.restore()
    layers(ctx, cam, os_, [('city_near.png', 1.0, 1.5)])
    # townspeople on the quay: walking, haggling, carrying
    if CITY_WALKERS is None:
        CITY_WALKERS = []
        for i in range(9):
            sd = 210 + i
            CITY_WALKERS.append((make_char(sd, None, ['adult', 'young', 'old', 'adult', 'child', 'adult', 'young', 'adult', 'old'][i]),
                                 hash01(sd, 1) * 1900 - 100, 1840 + 60 * hash01(sd, 2), 1 if i % 2 else -1, 60 + 50 * hash01(sd, 3)))
    order = sorted(CITY_WALKERS, key=lambda w_: w_[2])
    for c, x0, y, face, sp in order:
        x = x0 + face * sp * u
        s = 1.75 + (y - 1840) * 0.004
        p = poses.walk(twos(t), c['seed'], period=1.05 + 0.2 * hash01(c['seed'], 5))
        figure_at(ctx, cam, c, p, x, y, s, face, 1.0, os_, t)
    # a stallholder and a customer
    for c, x, face, kind in ((make_char(230, 'f', 'adult'), 290, 1, 'talk'), (make_char(231, 'm', 'adult'), 430, -1, 'point')):
        figure_at(ctx, cam, c, poses.gesture(kind, twos(t), c['seed'], turn=0.6), x, 1800, 1.75, face, 1.0, os_, t)
    layers(ctx, cam, os_, [('city_fg.png', 1.35, 1.0)])
    return dict(dark=0.05, desat=0.2, tint=(1.0, 0.95, 0.86), vig=0.5)


# ----------------------------------------------------------------------------------------------
# Scene 4 - THE CITY PANICS (council chamber)
# ----------------------------------------------------------------------------------------------
COUNCIL = None


def scene_council(ctx, t, os_):
    global COUNCIL
    a, b = S('council')
    u = t - a
    if COUNCIL is None:
        COUNCIL = [
            (make_char(301, 'm', 'old', role='council'), 360, 1700, 4.1, 1, 'talk'),
            (make_char(302, 'm', 'adult', role='council', beard='short'), 680, 1705, 4.1, 1, 'chin'),
            (make_char(303, 'm', 'adult', role='physician'), 960, 1840, 4.6, 1, 'flask'),
            (make_char(304, 'm', 'old', role='physician', beard='full'), 1240, 1840, 4.6, -1, 'book'),
            (make_char(305, 'm', 'adult', role='council'), 1500, 1705, 4.1, -1, 'fold'),
            (make_char(306, 'm', 'young', role='council', coat=PAL['charcoal']), 1760, 1740, 4.0, -1, 'write'),
        ]
    cam = Camera(lerp(600, 1280, smoother(u / 6.6)), 1180, 1.32)
    # candle flicker drives the light of the whole room
    flick = 0.85 + 0.15 * fnoise(t * 5.0, 3)
    layers(ctx, cam, os_, [('council_wall.png', 0.8, 1.25)])
    in_world(ctx, cam, 0.8, os_)
    dust(ctx, t, 0, 400, 1900, 1300, n=70, seed=4, size=2.0, alpha=0.4, speed=5)
    ctx.restore()
    for c, x, y, s, face, kind in COUNCIL:
        p = poses.gesture(kind, twos(t), c['seed'], turn=0.4)
        if kind == 'talk':
            p['hturn'] = 0.55
        figure_at(ctx, cam, c, p, x, y, s, face, 0.95, os_, t)
    layers(ctx, cam, os_, [('council_table.png', 1.0, 1.5)])
    in_world(ctx, cam, 1.0, os_)
    # on the table: papers (one lifts in a draught), an inkwell and quill, books, candles
    rng_x = [420, 760, 1080, 1380, 1650]
    for k, px in enumerate(rng_x):
        lift = 0.0 if k != 2 else 10 * max(0.0, math.sin(t * 2.2)) ** 2
        pts = np.array([[px - 70, 1352], [px + 60, 1346], [px + 75, 1372 - lift], [px - 62, 1378]])
        ink_shape(ctx, pts, PAL['parch'], lw=1.4, smooth_path=False, seed=k + boil_seed(t), boil=0.4, shadow=(PAL['parch2'], 4))
        for j in range(4):
            ink_line(ctx, np.array([[px - 55, 1356 + j * 5], [px + 45, 1352 + j * 5]]), 0.6, PAL['umber'], alpha=0.4)
    ink_shape(ctx, ellipse_pts(1260, 1340, 16, 9, 12), PAL['ink'], lw=1.4)
    taper_stroke(ctx, [[1262, 1338], [1280, 1300], [1300, 1262]], 1, 6, PAL['linen2'])
    for k, (bx, bw) in enumerate([(200, 120), (1520, 140)]):
        ink_shape(ctx, np.array([[bx, 1345], [bx + bw, 1345], [bx + bw, 1310], [bx, 1310]]), [PAL['burg3'], PAL['brown']][k], lw=1.6, smooth_path=False,
                  shadow=(PAL['charcoal'], 6))
        ink_shape(ctx, np.array([[bx + 6, 1310], [bx + bw - 6, 1310], [bx + bw - 6, 1300], [bx + 6, 1300]]), PAL['parch2'], lw=1.0, smooth_path=False)
    for k, cxp in enumerate([560, 900, 1330, 1800]):
        candle(ctx, cxp, 1340, 2.0, t, seed=k, glow=1.3)
    ctx.restore()
    # a large candlestick in the foreground, out of focus
    in_world(ctx, cam, 1.25, os_)
    candle(ctx, 300, 1960, 6.0, t, seed=9, glow=0.9, h=34)
    ctx.restore()
    return dict(dark=0.22, desat=0.18, tint=(1.04 * flick + 0.02, 0.9 * flick + 0.05, 0.72 * flick + 0.06), vig=0.68)


# ----------------------------------------------------------------------------------------------
# Scene 5 - THE STRANGE SOLUTION (the stage)
# ----------------------------------------------------------------------------------------------
CURE = None


def scene_cure(ctx, t, os_):
    global CURE
    a, b = S('cure')
    u = t - a
    if CURE is None:
        crowd = [(make_char(400 + i, None, None), 100 + i * 100 + 30 * hash01(i, 1), 1236 + 18 * hash01(i, 2)) for i in range(16)]
        dancers = [(make_char(420 + i, None, ['adult', 'young', 'adult', 'old', 'young', 'adult'][i]), 680 + i * 115, st)
                   for i, st in enumerate(['convulse', 'sway', 'stomp', 'sway', 'jig', 'convulse'])]
        musicians = [(make_char(440, 'm', 'adult', coat=PAL['burg3']), 330, 'drum'), (make_char(441, 'm', 'young'), 440, 'shawm'),
                     (make_char(442, 'm', 'old', beard='full'), 550, 'bagpipe')]
        officials = [(make_char(450, 'm', 'old', role='council'), 860, 'watch'), (make_char(451, 'm', 'adult', role='council'), 1010, 'fold')]
        CURE = (crowd, dancers, musicians, officials)
    crowd, dancers, musicians, officials = CURE
    z = 1.0 + 0.16 * smoother(u / 6.8)
    cam = Camera(700 + 60 * smoother(u / 6.8), 1180, z, roll=-0.012 + 0.03 * smooth(u / 6.8))
    layers(ctx, cam, os_, [('cure_sky.png', 0.2, 1.0), ('cure_back.png', 0.55, 1.25)])
    for c, x, y in crowd:
        p = poses.react(twos(t), -5, c['seed'], ['stare', 'whisper', 'cross', 'mouth', 'stare'][c['seed'] % 5], turn=0.15)
        figure_at(ctx, cam, c, p, x, y, 1.05, 1 if x < 800 else -1, 0.7, os_, t)
    layers(ctx, cam, os_, [('cure_stage.png', 1.0, 1.5)])
    for c, x, kind in musicians:
        figure_at(ctx, cam, c, poses.musician(kind, twos(t), c['seed']), x, 1370, 2.2, 1, 1.0, os_, t)
    for i, (c, x, st) in enumerate(dancers):
        p = poses.dance(st, twos(t), c['seed'], 0.85, 0.45 + 0.1 * i % 3)
        face = 1 if i % 2 else -1
        figure_at(ctx, cam, c, p, x + 20 * math.sin(t * 0.7 + i), 1370, 2.3, face, 1.0, os_, t)
    for c, x, kind in officials:
        figure_at(ctx, cam, c, poses.gesture(kind, twos(t), c['seed'], turn=0.7), x, 1890, 2.8, -1, 1.15, os_, t)
    layers(ctx, cam, os_, [('cure_fg.png', 1.3, 1.0)])
    return dict(dark=0.3 + 0.08 * ramp(u, 0, 6), desat=0.3, tint=(0.98, 0.93, 0.85), vig=0.62)


# ----------------------------------------------------------------------------------------------
# Scene 6 - THE MYSTERY DEEPENS (bird's-eye plan)
# ----------------------------------------------------------------------------------------------
def tiny_dancer(ctx, x, y, s, t, seed, col):
    """A dancer seen from above on the city plan: shadow, skirt, flailing arms, head."""
    ph = t * 5 + seed
    ctx.arc(x + 3 * s, y + 3 * s, 4.2 * s, 0, 2 * math.pi)
    set_c(ctx, PAL['ink'], 0.35)
    ctx.fill()
    for side in (-1, 1):
        a = ph + side * 1.6
        ink_line(ctx, np.array([[x, y], [x + side * 4.5 * s * math.cos(a * 0.5), y - 4.5 * s * abs(math.sin(a))]]), max(0.6, 0.9 * s), PAL['ink'])
    ink_shape(ctx, ellipse_pts(x, y, 3.2 * s, 2.6 * s, 8), col, lw=max(0.5, 0.7 * s))
    ctx.arc(x + 0.6 * s * math.sin(ph), y - 0.8 * s, 1.5 * s, 0, 2 * math.pi)
    set_c(ctx, PAL['linen'] if seed % 3 else PAL['charcoal'])
    ctx.fill_preserve()
    set_c(ctx, PAL['ink'])
    ctx.set_line_width(max(0.4, 0.5 * s))
    ctx.stroke()


def scene_map(ctx, t, os_):
    a, b = S('map')
    u = t - a
    z = keys(u, [(0.0, 2.3), (2.6, 0.82), (6.5, 0.9)], smoother)
    cx = keys(u, [(0.0, MAP_STAGE[0]), (2.6, 800.0), (6.5, 820.0)], smoother)
    cy = keys(u, [(0.0, MAP_STAGE[1]), (2.6, 1250.0), (6.5, 1260.0)], smoother)
    cam = Camera(cx, cy, z, anchor=(cx, cy))
    draw_layer(ctx, cam, 'map.png', 1.0, os_, 0, 0, 1.4)
    in_world(ctx, cam, 1.0, os_)
    cols = [PAL['burg3'], PAL['brown'], PAL['green3'], PAL['grey2'], PAL['umber'], PAL['burg2']]
    for k, (gx, gy) in enumerate(MAP_SPOTS):
        t_on = a + 0.15 + k * 0.42
        if t < t_on:
            continue
        g = smooth((t - t_on) / 0.6)
        n = int(6 + 12 * g * (1 + 0.3 * (k % 3)))
        # an ink ripple where a new group starts dancing
        soft_glow(ctx, gx, gy, 90 * g, PAL['burg2'], 0.35)
        for ring in range(2):
            rr = ((t - t_on) * 110 + ring * 90) % 220
            ink_shape(ctx, ellipse_pts(gx, gy, rr, rr * 0.8, 24), None, lw=3.0, line_alpha=0.7 * (1 - rr / 220), ink=PAL['burg3'])
        for i in range(n):
            ang = hash01(k, i) * 2 * math.pi + t * (0.4 + 0.3 * hash01(k, i, 2)) * (1 if i % 2 else -1)
            rad = 10 + 46 * math.sqrt(hash01(k, i, 3)) * (0.5 + 0.5 * g)
            tiny_dancer(ctx, gx + math.cos(ang) * rad, gy + math.sin(ang) * rad * 0.8, 2.9, twos(t), k * 31 + i, cols[(k + i) % len(cols)])
    # cloud shadows creeping over the city
    fog_bank(ctx, -400, -200, 2400, 2800, 0.0, t)
    ctx.restore()
    ctx.save()
    ctx.scale(os_, os_)
    dk = ramp(u, 1.5, 6.0)
    g = cairo.RadialGradient(540, 900, 200, 540, 900, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.05, 0.04, 0.03, 0.55 * dk)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    return dict(dark=0.3 + 0.25 * dk, desat=0.3, tint=(0.98, 0.92, 0.84), vig=0.6, paper=0.85)


# ----------------------------------------------------------------------------------------------
# Scene 7 - THE THEORIES (three illustrated plates)
# ----------------------------------------------------------------------------------------------
def plate_frame(ctx, os_, dark=0.0):
    """A dark parchment plate with an engraved double border and corner ornaments."""
    ctx.save()
    ctx.scale(os_, os_)
    set_c(ctx, mix(PAL['parch3'], PAL['brown'], 0.45 + 0.2 * dark))
    ctx.paint()
    for m, lw in ((44, 5), (62, 1.6)):
        ink_shape(ctx, np.array([[m, m + 120], [W - m, m + 120], [W - m, H - m - 120], [m, H - m - 120]]), None, lw=lw, smooth_path=False)
    for (x, y, sx, sy) in ((62, 182, 1, 1), (W - 62, 182, -1, 1), (62, H - 182, 1, -1), (W - 62, H - 182, -1, -1)):
        ink_line(ctx, np.array([[x, y + sy * 60], [x + sx * 20, y + sy * 20], [x + sx * 60, y]]), 2.2)
        ctx.arc(x + sx * 28, y + sy * 28, 6, 0, 2 * math.pi)
        set_c(ctx, PAL['ink'])
        ctx.fill()
    ctx.restore()


VITUS = make_char(501, 'm', 'young', role='physician', head='none', hair=PAL['hair_br'], coat=PAL['burg3'], sleeve=PAL['burg3'],
                  fur=PAL['parch3'], beard=None, dress='robe')


def scene_theory1(ctx, t, os_):
    """Belief at the time: the curse of Saint Vitus. A statue of the young saint with his palm and
    cockerel, candles before it, and a dancer jerking in its light."""
    a = 34.5
    u = t - a
    plate_frame(ctx, os_)
    cam = Camera(540, 1000 - 20 * u, 1.0 + 0.03 * u)
    in_world(ctx, cam, 1.0, os_)
    # rays and the niche
    for k in range(28):
        ang = -math.pi / 2 + (k - 13.5) * 0.11
        ink_line(ctx, np.array([[540, 780], [540 + math.cos(ang) * 700, 780 + math.sin(ang) * 700]]), 1.5, PAL['candle2'],
                 alpha=0.18 + 0.08 * math.sin(t * 2 + k))
    niche = np.array([[330, 1380], [330, 700], [360, 560], [440, 470], [540, 440], [640, 470], [720, 560], [750, 700], [750, 1380]])
    ink_shape(ctx, niche, mix(PAL['charcoal2'], PAL['brown'], 0.3), lw=4, smooth_path=True, shadow=(PAL['charcoal'], 40), hatch=(5, 70, 1.0, 0.4))
    p = poses.idle(1.0, 501, turn=0.05)
    p['ua_f'], p['fa_f'] = 0.4, 2.6
    p['ua_b'], p['fa_b'] = -0.25, -0.6
    p['eyes'] = 0.7
    p['prop'] = 'palm'
    from figures import skeleton
    J = skeleton(VITUS, p)
    hx, hy = 540 + J['Hd'][0] * 3.6, 1330 + J['Hd'][1] * 3.6
    ctx.arc(hx, hy - 6, 62, 0, 2 * math.pi)
    set_c(ctx, PAL['candle'], 0.85)
    ctx.fill()
    for k in range(16):
        ang = k * math.pi / 8
        ink_line(ctx, np.array([[hx + math.cos(ang) * 50, hy - 6 + math.sin(ang) * 50], [hx + math.cos(ang) * 70, hy - 6 + math.sin(ang) * 70]]), 2.2, PAL['burg3'])
    ink_shape(ctx, ellipse_pts(hx, hy - 6, 62, 62, 30), None, lw=2.5)
    draw_figure(ctx, VITUS, p, 540, 1330, 3.6, 1, pix=3.6 * cam.z * os_, boil_k=boil_seed(t))
    # the cockerel at his feet, one of the saint's emblems
    cock = np.array([[690, 1330], [650, 1300], [640, 1260], [660, 1230], [670, 1200], [690, 1195], [700, 1215], [712, 1250], [760, 1240], [790, 1200],
                     [800, 1260], [770, 1310], [740, 1330]])
    ink_shape(ctx, cock, PAL['brown2'], lw=3, shadow=(PAL['umber'], 12), hatch=(5, 40, 1, 0.4))
    ink_shape(ctx, np.array([[672, 1198], [680, 1180], [690, 1195]]), PAL['burg2'], lw=2, smooth_path=False)
    ink_shape(ctx, np.array([[320, 1330], [760, 1330], [780, 1400], [300, 1400]]), PAL['stone2'], lw=3, smooth_path=False, shadow=(PAL['grey2'], 14))
    for k, cxp in enumerate([360, 450, 630, 720]):
        candle(ctx, cxp, 1480, 3.0, t, seed=k, glow=1.2, h=40 + 10 * (k % 2))
    ink_shape(ctx, np.array([[300, 1480], [780, 1480], [780, 1500], [300, 1500]]), PAL['wood2'], lw=2.5, smooth_path=False)
    ctx.restore()
    # a dancer in the foreground, in silhouette against the candlelight
    in_world(ctx, cam, 1.25, os_)
    c = make_char(502, 'f', 'adult', gown=PAL['charcoal'], apron=None, sleeve=PAL['charcoal'])
    p = poses.dance('convulse', twos(t), 502)
    draw_figure(ctx, c, p, 820, 1980, 4.6, -1, pix=4.6 * os_, boil_k=boil_seed(t))
    ctx.restore()
    ctx.save()
    ctx.scale(os_, os_)
    g = cairo.LinearGradient(0, 1500, 0, H)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.05, 0.03, 0.02, 0.6)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    return dict(dark=0.45, desat=0.2, tint=(1.04, 0.9, 0.74), vig=0.7)


THEORY2 = None


def scene_theory2(ctx, t, os_):
    """Modern theory: mass psychogenic illness. Rows of townspeople; a wave of fear passes from one to
    the next, and each it reaches begins to move."""
    global THEORY2
    a = 37.6
    u = t - a
    plate_frame(ctx, os_, 0.2)
    if THEORY2 is None:
        THEORY2 = []
        for r in range(6):
            for k in range(5 + (r % 2)):
                x = 150 + k * 195 + (97 if r % 2 == 0 else 0)
                y = 790 + r * 185
                THEORY2.append((make_char(600 + r * 10 + k, None, None), x, y))
    cam = Camera(540, 1100, 1.02 + 0.02 * u)
    in_world(ctx, cam, 1.0, os_)
    cx, cy = 540, 1160
    R = 40 + 330 * u
    # threads of 'contagion' between neighbours the wave has passed
    reached = [(x, y) for c, x, y in THEORY2 if math.hypot(x - cx, (y - cy) * 1.3) < R]
    for i, (x1, y1) in enumerate(reached):
        for x2, y2 in reached[i + 1:]:
            if math.hypot(x1 - x2, y1 - y2) < 230:
                mid = ((x1 + x2) / 2 + 10 * math.sin(t * 9 + x1), (y1 + y2) / 2 - 160 + 8 * math.cos(t * 7 + y2))
                ink_line(ctx, np.array([[x1, y1 - 150], mid, [x2, y2 - 150]]), 1.6, PAL['burg2'], alpha=0.6)
    for c, x, y in sorted(THEORY2, key=lambda q: q[2]):
        d = math.hypot(x - cx, (y - cy) * 1.3)
        if d < R:
            k = clamp((R - d) / 140)
            p = poses.dance('convulse', twos(t), c['seed'], 0.6 * k, 0.0)
            p['brow'] = 0.9
            p['eyes'] = 1.0 - 0.6 * k
        else:
            p = poses.idle(twos(t), c['seed'], turn=0.1)
        draw_figure(ctx, c, p, x, y, 1.3, 1 if x < 540 else -1, pix=1.3 * cam.z * os_, boil_k=boil_seed(t))
    ink_shape(ctx, ellipse_pts(cx, cy - 80, R, R / 1.3, 40), None, lw=3.0, ink=PAL['burg3'], line_alpha=0.55)
    ink_shape(ctx, ellipse_pts(cx, cy - 80, R * 0.92, R / 1.3 * 0.92, 40), None, lw=1.2, ink=PAL['burg3'], line_alpha=0.4)
    ctx.restore()
    return dict(dark=0.48, desat=0.28, tint=(0.98, 0.9, 0.82), vig=0.7)


def rye_ear(ctx, x, y, s, angle, seed, ergot_idx=(), t=0.0):
    """An ear of rye drawn like a botanical engraving; some grains replaced by dark ergot sclerotia."""
    rng = np.random.default_rng(seed)
    c, sn = math.cos(angle), math.sin(angle)
    def P(px, py):
        return (x + (px * c - py * sn) * s, y + (px * sn + py * c) * s)
    ink_line(ctx, np.array([P(0, 0), P(4, 140), P(10, 320)]), 3 * s, PAL['parch3'])
    ink_line(ctx, np.array([P(0, 0), P(4, 140), P(10, 320)]), 0.8 * s, PAL['ink'])
    n = 18
    horns = []
    for i in range(n):
        yy = -i * 13
        for side in (-1, 1):
            j = i * 2 + (side > 0)
            gx, gy = P(side * 9, yy)
            rot = angle + side * 0.45
            if j in ergot_idx:
                horns.append([P(side * 4, yy + 6), P(side * 20, yy - 14), P(side * 30, yy - 44), P(side * 25, yy - 50), P(side * 12, yy - 22), P(side * 1, yy - 2)])
            else:
                g = ellipse_pts(gx[0] if isinstance(gx, tuple) else gx, gy, 6.5 * s, 11 * s, 12, rot=rot)
                ink_shape(ctx, g, mix(PAL['parch2'], PAL['brown3'], 0.3 + 0.3 * rng.random()), lw=1.2 * s, seed=j,
                          shadow=(PAL['brown3'], 2.5 * s), hatch=(3.0 * s, 60, 0.4 * s, 0.4))
                ax, ay = P(side * 14, yy - 10)
                ink_line(ctx, np.array([[gx, gy], [ax + side * 18 * s * math.cos(angle), ay - 40 * s]]), 0.6 * s, PAL['ink'], alpha=0.7)
    for k, horn in enumerate(horns):
        ink_shape(ctx, np.array(horn), mix(PAL['ink'], PAL['burg3'], 0.25), lw=1.6 * s, ink=PAL['ink'], seed=k,
                  shadow=(PAL['ink'], 4 * s))
        a0, a1 = horn[1], horn[2]
        ink_line(ctx, np.array([a0, a1]), 0.8 * s, PAL['grey2'], alpha=0.6)


def scene_theory3(ctx, t, os_):
    """Modern theory, disputed: ergot, a toxic fungus on damp rye. Ears of rye with the dark sclerotia,
    and a lens passing over them."""
    a = 40.3
    u = t - a
    plate_frame(ctx, os_, 0.1)
    cam = Camera(540, 1060, 1.0 + 0.04 * u)
    in_world(ctx, cam, 1.0, os_)
    # a loaf and a sickle, faint, behind
    ink_shape(ctx, ellipse_pts(300, 1450, 170, 90, 20), mix(PAL['brown3'], PAL['parch3'], 0.4), lw=2.5, shadow=(PAL['brown'], 26), hatch=(5, 40, 1, 0.3))
    for k in range(4):
        ink_line(ctx, np.array([[200 + k * 60, 1400], [240 + k * 60, 1470]]), 2.2, PAL['umber'])
    ink_line(ctx, np.array([[700, 1500], [760, 1380], [860, 1330], [930, 1360]]), 7, PAL['grey'])
    ink_line(ctx, np.array([[700, 1500], [660, 1580]]), 9, PAL['wood'])
    sway = 0.03 * math.sin(t * 1.3)
    for k, (x, ang, er) in enumerate([(360, -0.2, (5, 12, 19)), (560, 0.02, (8, 15, 22, 27)), (760, 0.22, (4, 17))]):
        rye_ear(ctx, x, 1200, 1.35, ang + sway * (k + 1), 700 + k, er, t)
    # the lens
    lx = 450 + 200 * smooth(u / 2.6)
    ly = 1040 + 40 * math.sin(u * 1.5)
    ctx.save()
    ctx.arc(lx, ly, 120, 0, 2 * math.pi)
    ctx.clip()
    set_c(ctx, mix(PAL['parch'], PAL['parch2'], 0.5))
    ctx.paint()
    ctx.translate(lx, ly)
    ctx.scale(2.2, 2.2)
    ctx.translate(-lx, -ly)
    rye_ear(ctx, 560, 1200, 1.35, 0.02 + sway * 2, 701, (8, 15, 22, 27), t)
    ctx.restore()
    ink_shape(ctx, ellipse_pts(lx, ly, 120, 120, 36), None, lw=9, ink=PAL['wood2'])
    ink_shape(ctx, ellipse_pts(lx, ly, 120, 120, 36), None, lw=2, ink=PAL['ink'])
    ink_line(ctx, np.array([[lx + 85, ly + 85], [lx + 190, ly + 200]]), 20, PAL['wood'])
    ink_line(ctx, np.array([[lx + 85, ly + 85], [lx + 190, ly + 200]]), 2, PAL['ink'])
    ctx.restore()
    return dict(dark=0.48, desat=0.25, tint=(1.0, 0.92, 0.8), vig=0.68)


# ----------------------------------------------------------------------------------------------
# Scene 8 - THE SHRINE
# ----------------------------------------------------------------------------------------------
PROC = None


def scene_shrine(ctx, t, os_):
    global PROC
    a, b = S('shrine')
    u = t - a
    if PROC is None:
        PROC = []
        priest = make_char(801, 'm', 'old', role='priest', surplice=True)
        PROC.append((priest, 0, 'priest'))
        for i in range(11):
            sd = 810 + i
            kind = ['tired', 'tired', 'convulse', 'tired', 'support', 'tired', 'sway', 'tired', 'tired', 'convulse', 'tired'][i]
            PROC.append((make_char(sd, None, None), -150 - i * 120 - 40 * hash01(sd, 1), kind))
    cam = Camera(lerp(420, 860, smoother(u / 7.4)), 980, 1.0)
    flash = 0.0
    tl = EV['thunder'][0]
    if tl <= t < tl + 0.5:
        flash = math.exp(-(t - tl) * 9) + 0.6 * math.exp(-max(0, t - tl - 0.18) * 14) * (t > tl + 0.18)
    layers(ctx, cam, os_, [('land_sky.png', 0.1, 1.0)])
    if flash > 0.05:
        in_world(ctx, cam, 0.1, os_)
        bolt = [[1080, 0], [1050, 160], [1095, 230], [1030, 420], [1075, 470], [1010, 700]]
        ink_line(ctx, np.array(bolt), 6, PAL['parch'], alpha=min(1, flash), smooth_path=False)
        ink_line(ctx, np.array(bolt), 2, (1, 1, 1, 1), alpha=min(1, flash), smooth_path=False)
        ctx.restore()
    layers(ctx, cam, os_, [('land_far.png', 0.25, 1.0), ('land_mid.png', 0.5, 1.25)])
    in_world(ctx, cam, 0.5, os_)
    fog_bank(ctx, -200, 980, 2300, 420, 0.45, t, speed=14, seed=8)
    ctx.restore()
    layers(ctx, cam, os_, [('land_near.png', 1.0, 1.5)])
    # the procession on the road, led by a priest with a cross
    base_x = 1040 + 62 * u
    for c, off, kind in sorted(PROC, key=lambda q: q[1]):
        x = base_x + off
        y = 1530 + 22 * math.sin(x / 300)
        if kind == 'priest':
            p = poses.walk(twos(t), c['seed'], period=1.3, stride=0.8)
            p['ua_f'], p['fa_f'] = 1.2, 2.8
            p['prop'] = 'cross'
        elif kind == 'convulse':
            p = poses.dance('convulse', twos(t), c['seed'], 0.6, 0.6)
            p['turn'] = 0.7
        elif kind == 'sway':
            p = poses.dance('sway', twos(t), c['seed'], 1.0, 0.8)
            p['turn'] = 0.7
        else:
            p = poses.walk(twos(t), c['seed'], period=1.35, stride=0.75, tired=0.85)
        figure_at(ctx, cam, c, p, x, y, 1.55, 1, 1.0, os_, t)
    in_world(ctx, cam, 1.0, os_)
    # wind-driven rain, drawn as fine ink strokes
    for k in range(160):
        rx = (hash01(k, 1) * 2400 + t * 900) % 2400 - 200
        ry = (hash01(k, 2) * 2200 + t * 1600) % 2200 - 100
        ink_line(ctx, np.array([[rx, ry], [rx - 18, ry + 44]]), 1.0, PAL['grey3'], alpha=0.35)
    ctx.restore()
    layers(ctx, cam, os_, [('land_fg.png', 1.4, 1.0)])
    if flash > 0:
        ctx.save()
        ctx.scale(os_, os_)
        set_c(ctx, PAL['parch'], 0.35 * min(1, flash))
        ctx.paint()
        ctx.restore()
    return dict(dark=0.55 - 0.3 * flash, desat=0.38, tint=(0.9, 0.92, 0.95), vig=0.72)


# ----------------------------------------------------------------------------------------------
# Scene 9b - the end card: dark parchment, and the ghost of the first dancer
# ----------------------------------------------------------------------------------------------
def scene_end_card(ctx, t, os_):
    a = 54.8
    u = t - a
    ctx.save()
    ctx.scale(os_, os_)
    set_c(ctx, mix(PAL['parch3'], PAL['brown'], 0.55))
    ctx.paint()
    g = cairo.RadialGradient(540, 900, 150, 540, 900, 1200)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.05, 0.03, 0.02, 0.6)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    # her figure, faint as an old engraving, still dancing slowly in the paper
    ctx.save()
    ctx.scale(os_, os_)
    p = dancer_pose(twos(t * 0.6), 0.8, 0.3)
    draw_figure(ctx, DANCER, p, 540, 1690, 4.2, 1, pix=4.2 * os_, boil_k=boil_seed(t, 3), alpha=0.16 + 0.04 * math.sin(u * 2))
    dust(ctx, t, 0, 0, 1080, 1920, n=60, seed=12, size=2.0, col=PAL['parch'], alpha=0.25, speed=3)
    ctx.restore()
    return dict(dark=0.6, desat=0.3, tint=(1.0, 0.92, 0.82), vig=0.75, paper=0.9)
