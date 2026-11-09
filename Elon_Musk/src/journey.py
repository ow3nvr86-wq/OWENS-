"""ONE CONTINUOUS SHOT: the whole Short is a single camera journey with no cuts. The world is built in four
connected spaces, and every hand-over is part of the animation itself:

  A  portrait -> payment streams -> city road   one shared plane; the camera pushes in, then travels right; the
                                                interface ring unspools into payment streams, which straighten
                                                into the lane markings the car drives on
  B  launch -> landing -> climb -> orbit        the camera dives into the car's headlight; its light becomes the
                                                rocket's engine light as the camera pulls back out of it
  C  network                                    the camera pushes into one satellite; its links become the edges of
                                                a neural network
  D  connected world                            the network folds onto a globe; cars, rockets and satellites circle it

Everything is flat 2D vector drawing (cairo); depth comes only from layers moved at different rates."""
import math

import cairo
import numpy as np

from core import W, H, EV, Camera, keys, smooth, smoother, ease_out, ease_in, clamp, ramp, lerp, hash01, vnoise
import gfx as G
from gfx import C, mixc
from portrait import portrait_duotone

EB = (0.27, 0.64, 1.0, 1.0)          # electric blue
EB2 = (0.62, 0.84, 1.0, 1.0)
RED = (0.88, 0.30, 0.30, 1.0)
HEAD = (0.0, -110.0)                  # the face centre in space A
RING_R = 430.0

HOOK = EV.get('hook', [0.05, 0.79, 1.78, 2.65])   # onsets of 'Rockets.', 'Electric cars.', 'Satellites.', 'AI.' in the narration
T_UNSPOOL, T_LANES, T_CAR = 4.6, 9.3, 10.25
T_DIVE, T_SWAP = 14.25, 14.95         # the dive into the headlight; the hand-over to the launch
T_LIFT, T_SEP, T_LAND, T_CLIMB = 15.05, 16.25, 17.45, 17.7
T_ORBIT, T_PUSH, T_NET, T_SPLIT, T_FOLD = 18.6, 21.55, 22.35, 24.0, 27.55


class World:
    def __init__(self, ctx, cam, d, os_):
        self.ctx, self.cam, self.d, self.os_ = ctx, cam, d, os_

    def __enter__(self):
        self.ctx.save()
        self.cam.apply(self.ctx, self.d, self.os_)
        return self.ctx

    def __exit__(self, *a):
        self.ctx.restore()


# ----------------------------------------------------------------------------------------------
# Icons (line art)
# ----------------------------------------------------------------------------------------------
def icon(ctx, kind, x, y, r, col, a=1.0, lw=3.0):
    c = (*col[:3], a)
    if kind == 'rocket':
        G.fill(ctx, [(x, y - r), (x + r * 0.28, y - r * 0.45), (x + r * 0.28, y + r * 0.55), (x - r * 0.28, y + r * 0.55), (x - r * 0.28, y - r * 0.45)], c)
        G.fill(ctx, [(x - r * 0.28, y + r * 0.2), (x - r * 0.55, y + r * 0.7), (x - r * 0.28, y + r * 0.55)], c)
        G.fill(ctx, [(x + r * 0.28, y + r * 0.2), (x + r * 0.55, y + r * 0.7), (x + r * 0.28, y + r * 0.55)], c)
        G.glow(ctx, x, y + r * 0.8, r * 0.5, EB2, 0.8 * a)
    elif kind == 'car':
        G.fill(ctx, [(x - r, y + r * 0.25), (x - r * 0.95, y - r * 0.05), (x - r * 0.45, y - r * 0.15), (x - r * 0.15, y - r * 0.45),
                     (x + r * 0.45, y - r * 0.42), (x + r * 0.95, y - r * 0.05), (x + r, y + r * 0.25)], c)
        for wx in (-0.55, 0.55):
            ctx.arc(x + wx * r, y + r * 0.28, r * 0.2, 0, 2 * math.pi)
            G.setc(ctx, C['navy0'])
            ctx.fill()
            ctx.arc(x + wx * r, y + r * 0.28, r * 0.2, 0, 2 * math.pi)
            G.setc(ctx, c)
            ctx.set_line_width(lw)
            ctx.stroke()
    elif kind == 'sat':
        G.rect(ctx, x - r * 0.18, y - r * 0.18, x + r * 0.18, y + r * 0.18, c)
        for sd in (-1, 1):
            G.rect(ctx, x + sd * r * 0.25, y - r * 0.12, x + sd * r * 0.95, y + r * 0.12, (*c[:3], a * 0.75))
            G.line(ctx, [(x + sd * r * 0.18, y), (x + sd * r * 0.25, y)], lw, c)
        G.line(ctx, [(x, y - r * 0.18), (x, y - r * 0.5)], lw * 0.7, c)
    elif kind == 'chip':
        G.rect(ctx, x - r * 0.42, y - r * 0.42, x + r * 0.42, y + r * 0.42, c)
        G.rect(ctx, x - r * 0.24, y - r * 0.24, x + r * 0.24, y + r * 0.24, (*C['navy0'][:3], a))
        G.text(ctx, x, y + r * 0.13, r * 0.36, 'AI', c)
        for k in range(4):
            o = -0.3 + 0.2 * k
            for (dx, dy) in ((o, -0.42), (o, 0.42), (-0.42, o), (0.42, o)):
                ex = 0 if abs(dx) < 0.42 else math.copysign(0.18, dx)
                ey = 0 if abs(dy) < 0.42 else math.copysign(0.18, dy)
                G.line(ctx, [(x + dx * r, y + dy * r), (x + (dx + ex) * r, y + (dy + ey) * r)], lw * 0.8, c)


# ----------------------------------------------------------------------------------------------
# Space A: the portrait, the interface ring, the payment streams, the city road
# ----------------------------------------------------------------------------------------------
def car_x(t):
    if t < T_CAR:
        return 2700 + 820 * (t - T_CAR)
    if t < T_DIVE:
        return 2700 + 820 * (t - T_CAR)
    u = t - T_DIVE
    return 2700 + 820 * (T_DIVE - T_CAR) + 820 * u - 500 * u * u


ROAD_Y = 380.0
LANES = [300.0, 340.0, 380.0, 420.0, 460.0]
N_STREAMS = 9


def headlight(t):
    return car_x(t) + 205, ROAD_Y - 32


def cam_A(t):
    if t < T_CAR + 0.3:
        cx, cy, z, roll = keys(t, [(0.0, (0.0, -70.0, 1.12, 0.0)), (T_UNSPOOL, (0.0, -105.0, 1.5, 0.0)), (6.3, (900.0, -20.0, 1.0, 0.025)),
                                   (8.6, (2000.0, 60.0, 0.95, -0.02)), (T_CAR + 0.3, (car_x(T_CAR + 0.3) + 160, 230.0, 1.0, 0.0))], smooth)
        return Camera(cx, cy, z, roll)
    cx = car_x(t) + 160
    cy = 230.0
    z = 1.0 + 0.03 * (t - T_CAR)
    if t > T_DIVE:
        hx, hy = headlight(t)
        k = smoother(ramp(t, T_DIVE, T_SWAP))
        cx, cy = lerp(cx, hx, k), lerp(cy, hy, k)
        z = z * math.exp(math.log(10.0 / z) * ease_in(k))
    return Camera(cx, cy, z, 0.0)


def stream_y(i, x, t):
    """A payment stream: a gentle wave between the ring and the road; it straightens into a lane as the car arrives."""
    base = -240 + 520 * i / (N_STREAMS - 1)
    wave = 70 * math.sin(x * 0.0024 + i * 0.9 + t * 0.6) + 40 * math.sin(x * 0.0051 - i * 0.6)
    y = base + wave
    lane = LANES[int(round(i * (len(LANES) - 1) / (N_STREAMS - 1)))]
    k = smooth(ramp(t, T_LANES - 0.4, T_LANES + 0.9)) * smooth(ramp(x, 1500, 2700))
    return lerp(y, lane, k)


def stream_start(i):
    a = math.radians(-60 + 120 * i / (N_STREAMS - 1))
    return HEAD[0] + RING_R * math.cos(a), HEAD[1] + RING_R * math.sin(a)


def draw_streams(c, t, cam):
    grow = smooth(ramp(t, T_UNSPOOL, T_UNSPOOL + 1.6))
    if grow <= 0:
        return
    xend = lerp(RING_R, 9000, grow)
    for i in range(N_STREAMS):
        sx, sy = stream_start(i)
        pts = []
        for k in range(90):
            x = sx + (xend - sx) * k / 89
            u = clamp((x - sx) / 500)
            y = lerp(sy, stream_y(i, x, t), smooth(u))
            pts.append((x, y))
        lanes = smooth(ramp(t, T_LANES, T_LANES + 0.8))
        col = mixc(EB, C['white'], 0.25 * lanes)
        G.line(c, pts, 3.0 + 2.0 * lanes, (*col[:3], 0.55 - 0.15 * lanes))
        G.line(c, pts, 10, (*EB[:3], 0.08))
        # packets: glowing payment chips gliding along each stream
        if lanes < 0.95:
            for j in range(7):
                ph = (t * 0.22 + j / 7 + hash01(i, j) * 0.3) % 1.0
                x = sx + (min(xend, 3200) - sx) * ph
                y = lerp(sy, stream_y(i, x, t), smooth(clamp((x - sx) / 500)))
                a = (1 - lanes) * min(1, grow * 2)
                G.glow(c, x, y, 34, EB, 0.5 * a)
                ctx_card(c, x, y, a, (i + j) % 3)


def ctx_card(c, x, y, a, kind):
    if kind == 0:
        c.new_path()
        G.rect(c, x - 22, y - 14, x + 22, y + 14, (*C['white'][:3], 0.9 * a))
        G.rect(c, x - 22, y - 7, x + 22, y - 2, (*C['navy2'][:3], 0.8 * a))
    elif kind == 1:
        c.arc(x, y, 15, 0, 2 * math.pi)
        G.setc(c, (*EB2[:3], 0.95 * a))
        c.fill()
        G.text(c, x, y + 7, 20, '$', (*C['navy0'][:3], a))
    else:
        G.rect(c, x - 8, y - 8, x + 8, y + 8, (*C['white'][:3], 0.8 * a))


def draw_ring(c, t):
    """The interface around the portrait: rotating rings, ticks, and four icons that snap in with the hook."""
    k_in = smooth(ramp(t, 0.0, 0.5))
    unsp = smooth(ramp(t, T_UNSPOOL, T_UNSPOOL + 1.2))
    a = k_in * (1 - unsp)
    if a <= 0.01:
        return
    hx, hy = HEAD
    for rr, w, sp, dash in ((RING_R, 3, 0.25, None), (RING_R + 36, 2, -0.4, [6, 14]), (RING_R - 40, 1.5, 0.6, [40, 20])):
        c.save()
        c.translate(hx, hy)
        c.rotate(t * sp)
        c.arc(0, 0, rr, 0, 2 * math.pi)
        G.setc(c, (*EB[:3], 0.55 * a))
        c.set_line_width(w)
        if dash:
            c.set_dash(dash)
        c.stroke()
        c.set_dash([])
        c.restore()
    for k in range(60):
        ang = 2 * math.pi * k / 60 + t * 0.1
        L = 18 if k % 5 == 0 else 8
        G.line(c, [(hx + (RING_R + 50) * math.cos(ang), hy + (RING_R + 50) * math.sin(ang)),
                   (hx + (RING_R + 50 + L) * math.cos(ang), hy + (RING_R + 50 + L) * math.sin(ang))], 2, (*EB2[:3], 0.4 * a))
    kinds = ['rocket', 'car', 'sat', 'chip']
    for i, kind in enumerate(kinds):
        t0 = HOOK[i]
        kk = smooth(ramp(t, t0, t0 + 0.25))
        if kk <= 0:
            continue
        ang = math.radians(-135 + 90 * i) + 0.04 * math.sin(t + i)
        px, py = hx + RING_R * math.cos(ang), hy + RING_R * math.sin(ang)
        pop = 1 + 0.4 * math.sin(math.pi * min(1, (t - t0) / 0.3)) if t - t0 < 0.3 else 1
        G.glow(c, px, py, 120 * kk, EB, 0.45 * a)
        c.arc(px, py, 62 * kk * pop, 0, 2 * math.pi)
        G.setc(c, (*C['navy1'][:3], 0.9 * a))
        c.fill()
        c.arc(px, py, 62 * kk * pop, 0, 2 * math.pi)
        G.setc(c, (*EB[:3], a))
        c.set_line_width(3)
        c.stroke()
        icon(c, kind, px, py, 34 * kk * pop, C['white'], a)
    # 'One man is behind them all': lines from every icon converge on him
    km = smooth(ramp(t, EV.get('one_man', 3.1), EV.get('one_man', 3.1) + 0.6)) * a
    if km > 0:
        for i in range(4):
            ang = math.radians(-135 + 90 * i)
            px, py = hx + RING_R * math.cos(ang), hy + RING_R * math.sin(ang)
            G.line(c, [(px, py), (lerp(px, hx, km), lerp(py, hy, km))], 2.5, (*EB2[:3], 0.7 * km))


def draw_portrait(c, t):
    a = 1 - smooth(ramp(t, 5.0, 6.6))
    if a <= 0.01:
        return
    img, ox, oy, sc = portrait_duotone(2.0)
    G.glow(c, HEAD[0] + 160, HEAD[1] - 40, 900, EB, 0.22 * a)
    c.save()
    c.translate(HEAD[0], HEAD[1])
    s = 1.0 / sc
    c.scale(s, s)
    c.translate(-ox * sc, -oy * sc)
    c.set_source_surface(img, 0, 0)
    c.get_source().set_filter(cairo.FILTER_GOOD)
    c.paint_with_alpha(a)
    c.restore()
    # a slow band of light sweeping across him
    ph = (t * 0.18) % 1.0
    g = cairo.LinearGradient(HEAD[0] - 600 + 1200 * ph, 0, HEAD[0] - 400 + 1200 * ph, 0)
    g.add_color_stop_rgba(0, 1, 1, 1, 0)
    g.add_color_stop_rgba(0.5, 0.7, 0.85, 1, 0.06 * a)
    g.add_color_stop_rgba(1, 1, 1, 1, 0)
    c.rectangle(HEAD[0] - 500, HEAD[1] - 500, 1000, 1400)
    c.set_source(g)
    c.fill()


def tower(c, x, gy, w, h, col, seed, lit, t=0.0, grow=1.0):
    h = h * grow
    if h < 2:
        return
    g = cairo.LinearGradient(x, 0, x + w, 0)
    g.add_color_stop_rgba(0, *mixc(col, C['white'], 0.08)[:3], 1)
    g.add_color_stop_rgba(1, *mixc(col, C['navy0'], 0.3)[:3], 1)
    c.rectangle(x, gy - h, w, h)
    c.set_source(g)
    c.fill()
    G.rect(c, x, gy - h, x + 2, gy, (*EB[:3], 0.35))
    rng = np.random.default_rng(seed)
    if lit > 0:
        for yy in np.arange(gy - h + 14, gy - 10, 22):
            for xx in np.arange(x + 8, x + w - 10, 16):
                if rng.random() < lit:
                    G.rect(c, xx, yy, xx + 7, yy + 9, (*mixc(EB2, C['warm'], rng.random() * 0.4)[:3], 0.55 + 0.35 * rng.random()))
    if rng.random() < 0.3:
        G.line(c, [(x + w / 2, gy - h), (x + w / 2, gy - h - 80)], 2, col)
        if (t * 1.2 + seed) % 1.0 < 0.5:
            G.glow(c, x + w / 2, gy - h - 80, 18, RED, 0.9)


def city_layer(c, cam, t, d, seed, gy, hmin, hmax, wmin, wmax, col, lit, x0, x1, growfrom=None):
    rng = np.random.default_rng(seed)
    x = x0
    while x < x1:
        w = rng.uniform(wmin, wmax)
        h = rng.uniform(hmin, hmax)
        grow = 1.0
        if growfrom is not None:
            # each building rises out of the ground as the camera arrives
            sx = cam.world_to_screen(x, gy, d)[0] / 1.0
            grow = smoother(clamp((1500 - sx) / 600))
        tower(c, x, gy, w, h, col, int(x) + seed, lit, t, grow)
        x += w + rng.uniform(20, 90)


def draw_city(c_ctx, cam, t, os_):
    """The city around the road, in four depth planes; it rises out of the dark as the streams become lanes."""
    k = smooth(ramp(t, T_LANES - 0.6, T_LANES + 1.0))
    if k <= 0:
        return
    c_ctx.push_group()
    with World(c_ctx, cam, 0.4, os_) as c:
        city_layer(c, cam, t, 0.4, 3, 300, 400, 1100, 90, 200, mixc(C['navy2'], C['blue1'], 0.25), 0.25, 1500, 5200)
    with World(c_ctx, cam, 0.65, os_) as c:
        city_layer(c, cam, t, 0.65, 5, 300, 300, 800, 120, 240, mixc(C['navy2'], C['navy3'], 0.6), 0.35, 1800, 6400)
    with World(c_ctx, cam, 1.0, os_) as c:
        city_layer(c, cam, t, 1.0, 7, 290, 160, 620, 140, 300, C['navy3'], 0.45, 2600, 8000, growfrom=True)
        # the road
        G.rect(c, 2200, LANES[0] - 6, 9000, LANES[-1] + 30, (*C['navy1'][:3], 1.0))
        G.rect(c, 2200, LANES[-1] + 30, 9000, 3000, (*C['navy0'][:3], 1.0))
        for i, ly in enumerate(LANES):
            if i in (0, len(LANES) - 1):
                G.line(c, [(2200, ly), (9000, ly)], 4, (*EB[:3], 0.6))
            else:
                c.save()
                c.set_dash([60, 50])
                G.line(c, [(2200, ly), (9000, ly)], 4, (*C['white'][:3], 0.55))
                c.restore()
        # reflections of the towers on the wet road
        for kx in range(30):
            xx = 2600 + kx * 210
            G.rect(c, xx, LANES[-1] + 34, xx + 60, LANES[-1] + 120, (*EB[:3], 0.06))
    with World(c_ctx, cam, 1.35, os_) as c:
        # street lights flashing past in the foreground
        for kx in range(30):
            xx = 2400 + kx * 520
            G.line(c, [(xx, 700), (xx, 120)], 10, C['navy0'])
            G.line(c, [(xx, 120), (xx + 80, 110)], 8, C['navy0'])
            G.glow(c, xx + 80, 120, 70, EB2, 0.6)
    c_ctx.pop_group_to_source()
    c_ctx.paint_with_alpha(k)


def ev(c, x, y, s, t, glow_k=1.0):
    """A sleek electric car in profile (a generic design), wheels turning, a light bar and headlight."""
    L = 400 * s
    body = [(-L / 2, -20 * s), (-L / 2 + 10 * s, -70 * s), (-L * 0.25, -86 * s), (-L * 0.08, -128 * s), (L * 0.18, -132 * s),
            (L * 0.36, -96 * s), (L / 2, -70 * s), (L / 2 + 6 * s, -30 * s), (L / 2 - 6 * s, -10 * s), (-L / 2 + 6 * s, -10 * s)]
    G.glow(c, x, y - 40 * s, 300 * s, EB, 0.18)
    G.fill(c, [(x + px, y + py) for px, py in body], mixc(C['grey5'], C['blue3'], 0.25))
    G.fill(c, [(x + px, y + py) for px, py in [(-L * 0.2, -88 * s), (-L * 0.06, -122 * s), (L * 0.16, -126 * s), (L * 0.31, -94 * s)]], C['navy1'])
    G.line(c, [(x - L / 2 + 10 * s, y - 50 * s), (x + L / 2, y - 52 * s)], 2.5 * s, (*C['white'][:3], 0.5))
    G.line(c, [(x - L / 2 + 6 * s, y - 62 * s), (x - L / 2 + 40 * s, y - 64 * s)], 6 * s, RED)
    for wx in (-L * 0.3, L * 0.3):
        c.arc(x + wx, y - 10 * s, 34 * s, 0, 2 * math.pi)
        G.setc(c, C['navy0'])
        c.fill()
        ang = -t * 22
        for k in range(5):
            b = ang + k * 2 * math.pi / 5
            G.line(c, [(x + wx, y - 10 * s), (x + wx + 24 * s * math.cos(b), y - 10 * s + 24 * s * math.sin(b))], 3 * s, C['grey3'])
    hx, hy = x + L / 2 + 5 * s, y - 32 * s
    G.glow(c, hx, hy, 60 * s, EB2, 0.9 * glow_k)
    G.glow(c, hx + 220 * s, hy + 10 * s, 260 * s, EB, 0.25 * glow_k)


def draw_A(ctx, t, os_):
    cam = cam_A(t)
    s = ctx
    s.save()
    s.scale(os_, os_)
    G.vgrad(s, 0, 0, W, H, [(0, C['navy0']), (0.55, mixc(C['navy1'], C['navy2'], 0.5)), (1, C['navy0'])])
    s.restore()
    # a faint dot grid on the far plane gives the dark space depth
    with World(ctx, cam, 0.25, os_) as c:
        for gx in range(-1200, 4000, 120):
            for gy_ in range(-1400, 1400, 120):
                c.new_sub_path()
                c.arc(gx, gy_, 2.2, 0, 2 * math.pi)
        G.setc(c, (*EB[:3], 0.12))
        c.fill()
    draw_city(ctx, cam, t, os_)
    with World(ctx, cam, 1.0, os_) as c:
        draw_portrait(c, t)
        draw_ring(c, t)
        draw_streams(c, t, cam)
        if t > T_LANES:
            ev(c, car_x(t), ROAD_Y + 18, 1.0, t, glow_k=1.0 + 3 * smooth(ramp(t, T_DIVE, T_SWAP)))
    return cam


# ----------------------------------------------------------------------------------------------
# Space B: launch, booster landing, climb, orbit
# ----------------------------------------------------------------------------------------------
A_LIFT = 1500.0


def rocket_y(t):
    u = max(0.0, t - T_LIFT)
    return -0.5 * A_LIFT * u * u


def booster_state(t):
    """Booster position/rotation: rides with the rocket, separates, flips, falls back and lands on the pad."""
    if t < T_SEP:
        return 0.0, rocket_y(t), 0.0, 'up'
    y_sep = rocket_y(T_SEP)
    u = clamp((t - T_SEP) / (T_LAND - T_SEP))
    # a smooth arc back down to the pad, offset to one side
    x = 380 * math.sin(math.pi * u) * 0.9 + 420 * smooth(u)
    y = lerp(y_sep, 0.0, smoother(u))
    rot = math.pi * smooth(ramp(t, T_SEP, T_SEP + 0.45)) * (1 - smooth(ramp(t, T_SEP + 0.45, T_LAND - 0.25)))
    return x, y, rot, 'landing' if t < T_LAND else 'landed'


def cam_B(t):
    if t < T_SEP:
        yr = rocket_y(t)
        k = smoother(ramp(t, T_SWAP, T_SWAP + 0.75))
        z = math.exp(lerp(math.log(10.0), math.log(1.0), k))
        cy = lerp(28.0, yr - 380, k)
        return Camera(0.0, cy, z, 0.0)
    if t < T_CLIMB:
        bx, by, _, _ = booster_state(t)
        k = smooth(ramp(t, T_SEP, T_SEP + 0.5))
        cy = lerp(rocket_y(T_SEP) - 380, by - 380, k)
        return Camera(lerp(0, bx * 0.8, k), cy, 1.0, 0.0)
    # the climb: rise along the second stage's trail into space, pulling back
    u = smoother(ramp(t, T_CLIMB, T_ORBIT + 0.4))
    bx, by, _, _ = booster_state(T_LAND)
    cy = lerp(-380.0, -12000.0, u)
    return Camera(lerp(bx * 0.8, 0.0, u), cy, lerp(1.0, 0.7, u), 0.0)


def rocket(c, x, y, s, t, plume=1.0, stages=('booster', 'upper'), rot=0.0, legs=0.0, fins=0.0, burn=None):
    """A two-stage launch vehicle in a generic design: white body, black interstage, nine-engine base glow."""
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    w = 46 * s
    if 'booster' in stages:
        if plume > 0:
            for k in range(4):
                L = (240 + 120 * k) * s * plume * (1 + 0.06 * math.sin(t * 40 + k))
                g = cairo.LinearGradient(0, 0, 0, L)
                g.add_color_stop_rgba(0, 1, 1, 1, 0.9 / (k + 1))
                g.add_color_stop_rgba(0.3, *EB2[:3], 0.6 / (k + 1))
                g.add_color_stop_rgba(1, *EB[:3], 0)
                c.move_to(-w * (0.5 - 0.06 * k), 0)
                c.line_to(w * (0.5 - 0.06 * k), 0)
                c.line_to(w * (0.9 + 0.5 * k), L)
                c.line_to(-w * (0.9 + 0.5 * k), L)
                c.close_path()
                c.set_source(g)
                c.fill()
            G.glow(c, 0, 20 * s, 160 * s * plume, EB2, 0.8)
        G.rect(c, -w / 2, -470 * s, w / 2, 0, mixc(C['white'], C['grey5'], 0.2))
        G.rect(c, w * 0.15, -470 * s, w / 2, 0, mixc(C['grey4'], C['grey5'], 0.4))
        G.rect(c, -w / 2, -470 * s, w / 2, -440 * s, C['char'])
        G.rect(c, -w / 2 - 2, -12 * s, w / 2 + 2, 0, C['grey2'])
        if fins > 0:
            for sd in (-1, 1):
                G.rect(c, sd * w / 2, -430 * s, sd * (w / 2 + 22 * s * fins), -414 * s, C['grey3'])
        if legs > 0:
            for sd in (-1, 1):
                G.line(c, [(sd * w / 2, -60 * s), (sd * (w / 2 + 70 * s * legs), 6 * s * legs)], 6 * s, C['char'])
    if 'upper' in stages:
        base = -470 * s if 'booster' in stages else 0
        if 'booster' not in stages and plume > 0:
            G.glow(c, 0, 20 * s, 90 * s * plume, EB2, 0.8)
            for k in range(3):
                L = (160 + 80 * k) * s * plume
                c.move_to(-w * 0.3, 0)
                c.line_to(w * 0.3, 0)
                c.line_to(w * (0.6 + 0.4 * k), L)
                c.line_to(-w * (0.6 + 0.4 * k), L)
                c.close_path()
                G.setc(c, (*EB2[:3], 0.4 / (k + 1)))
                c.fill()
        G.rect(c, -w / 2, base - 170 * s, w / 2, base, mixc(C['white'], C['grey5'], 0.15))
        G.rect(c, w * 0.15, base - 170 * s, w / 2, base, mixc(C['grey4'], C['grey5'], 0.4))
        G.fill(c, [(-w / 2 - 4 * s, base - 170 * s), (w / 2 + 4 * s, base - 170 * s), (w / 2 + 4 * s, base - 230 * s), (0, base - 290 * s),
                   (-w / 2 - 4 * s, base - 230 * s)], C['white'])
    if burn is not None:
        G.glow(c, 0, 10 * s, 120 * s * burn, EB2, 0.9)
        for k in range(3):
            L = (120 + 60 * k) * s * burn
            c.move_to(-w * 0.3, 0)
            c.line_to(w * 0.3, 0)
            c.line_to(w * (0.5 + 0.3 * k), L)
            c.line_to(-w * (0.5 + 0.3 * k), L)
            c.close_path()
            G.setc(c, (*EB2[:3], 0.45 / (k + 1)))
            c.fill()
    c.restore()


def draw_B(ctx, t, os_):
    cam = cam_B(t)
    alt = max(0.0, -cam.cy)
    space = smooth(clamp((alt - 1500) / 7000))
    s = ctx
    s.save()
    s.scale(os_, os_)
    G.vgrad(s, 0, 0, W, H, [(0, mixc(C['navy1'], (0.0, 0.0, 0.02, 1), space)), (1, mixc(C['navy3'], C['navy0'], space))])
    # stars come out as the sky thins
    if space > 0.05:
        for i in range(160):
            x = hash01(i, 1) * W
            y = (hash01(i, 2) * H + (cam.cy * 0.02)) % H
            s.arc(x, y, 1.2 + 1.6 * hash01(i, 3), 0, 2 * math.pi)
            G.setc(s, C['white'], space * (0.4 + 0.6 * hash01(i, 4)))
            s.fill()
    s.restore()
    with World(ctx, cam, 0.35, os_) as c:
        # the city's glow on the horizon, far behind the pad
        for k in range(26):
            x = -1600 + k * 130
            h = 80 + 240 * hash01(k, 7)
            G.rect(c, x, 300 - h, x + 90, 300, mixc(C['navy2'], C['navy3'], 0.5))
        G.glow(c, 0, 300, 1400, EB, 0.12)
    with World(ctx, cam, 1.0, os_) as c:
        G.rect(c, -4000, 0, 4000, 4000, C['navy0'])
        G.line(c, [(-4000, 0), (4000, 0)], 3, (*EB[:3], 0.5))
        # the launch tower and the landing pad
        for k in range(14):
            G.rect(c, -150, -k * 52 - 50, -110, -k * 52, (0, 0, 0, 0))
        G.line(c, [(-150, 0), (-150, -720)], 8, C['grey2'])
        G.line(c, [(-110, 0), (-110, -720)], 8, C['grey2'])
        for k in range(14):
            G.line(c, [(-150, -k * 52), (-110, -k * 52 - 52)], 3, C['grey2'])
        bx_land = booster_state(T_LAND)[0]
        c.save()
        c.translate(bx_land, 0)
        c.scale(1, 0.25)
        c.arc(0, 0, 150, 0, 2 * math.pi)
        G.setc(c, (*C['grey2'][:3], 1))
        c.fill()
        c.arc(0, 0, 110, 0, 2 * math.pi)
        G.setc(c, (*EB[:3], 0.6))
        c.set_line_width(6)
        c.stroke()
        c.restore()
        # the rocket
        ign = smooth(ramp(t, T_SWAP - 0.1, T_LIFT + 0.2))
        if t < T_SEP:
            rocket(c, 0, rocket_y(t), 1.0, t, plume=ign)
        else:
            yu = rocket_y(t)
            rocket(c, 0, yu, 1.0, t, plume=1.0, stages=('upper',))
            # the second stage's trail into the sky
            G.line(c, [(0, yu + 60), (0, rocket_y(T_SEP))], 6, (*EB2[:3], 0.25 * (1 - space)))
            bx, by, rot, st = booster_state(t)
            burn = smooth(ramp(t, T_LAND - 0.55, T_LAND - 0.35)) * (1 - smooth(ramp(t, T_LAND - 0.05, T_LAND + 0.1)))
            rocket(c, bx, by, 1.0, t, plume=0.0, stages=('booster',), rot=rot, legs=smooth(ramp(t, T_LAND - 0.5, T_LAND - 0.2)),
                   fins=smooth(ramp(t, T_SEP + 0.3, T_SEP + 0.6)), burn=burn)
            if t > T_LAND:
                d = smooth(ramp(t, T_LAND, T_LAND + 0.15)) * (1 - smooth(ramp(t, T_LAND + 0.2, T_LAND + 1.4)))
                G.glow(c, bx, 0, 260, C['grey4'], 0.35 * d)
    draw_orbit(ctx, t, os_)
    return cam


def earth(c, cx, cy, R, t, night=0.6):
    g = cairo.RadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.1, cx, cy, R)
    g.add_color_stop_rgba(0, 0.18, 0.42, 0.72, 1)
    g.add_color_stop_rgba(0.7, 0.08, 0.2, 0.42, 1)
    g.add_color_stop_rgba(1, 0.03, 0.08, 0.18, 1)
    c.arc(cx, cy, R, 0, 2 * math.pi)
    c.set_source(g)
    c.fill()
    c.save()
    c.arc(cx, cy, R, 0, 2 * math.pi)
    c.clip()
    rot = t * 0.02
    for k in range(7):
        a = 2 * math.pi * hash01(k, 1) + rot
        r = R * (0.2 + 0.7 * hash01(k, 2))
        px, py = cx + r * math.cos(a), cy + r * math.sin(a) * 0.9
        pts = []
        for i in range(40):
            b = 2 * math.pi * i / 40
            rr = R * (0.12 + 0.1 * hash01(k, 3)) * (1 + 0.35 * vnoise(i * 0.35 + k * 5, 3) + 0.15 * vnoise(i * 1.1 + k, 4))
            pts.append((px + rr * 1.5 * math.cos(b), py + rr * 0.85 * math.sin(b)))
        G.fill(c, pts, (0.12, 0.27, 0.28, 0.9), smooth_=True)
        G.fill(c, [(px + (x - px) * 0.7, py + (y - py) * 0.7 - R * 0.01) for x, y in pts], (0.16, 0.33, 0.32, 0.6), smooth_=True)
    for k in range(260):
        a = 2 * math.pi * hash01(k, 11) + rot
        r = R * math.sqrt(hash01(k, 12))
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        if (px - cx) > R * 0.1:
            c.arc(px, py, 1.6 + hash01(k, 13) * 1.5, 0, 2 * math.pi)
            G.setc(c, C['warm'], 0.7 * night)
            c.fill()
    g = cairo.LinearGradient(cx - R, 0, cx + R, 0)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(0.55, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0.02, 0.6 * night)
    c.rectangle(cx - R, cy - R, 2 * R, 2 * R)
    c.set_source(g)
    c.fill()
    c.restore()
    for k, (wdt, aa) in enumerate(((10, 0.6), (40, 0.18), (90, 0.08))):
        c.arc(cx, cy, R + wdt * 0.3, 0, 2 * math.pi)
        G.setc(c, (*EB[:3], aa))
        c.set_line_width(wdt)
        c.stroke()


SATS = None


def sat_positions(t, cx, cy, R):
    """Trains of satellites on inclined orbits drawn as arcs above the Earth (screen space)."""
    out = []
    for tr in range(6):
        inc = -0.5 + 0.2 * tr
        rr = R + 120 + 40 * tr
        for k in range(14):
            ph = t * (0.05 + 0.006 * tr) + tr * 0.7 + k * 0.025
            a = -math.pi * 0.95 + (ph % 1.0) * math.pi * 0.9
            x = cx + rr * math.cos(a)
            y = cy + rr * math.sin(a) * (0.35 + 0.06 * tr) - 40 * math.sin(inc) * math.cos(a)
            out.append((x, y, tr, k))
    return out


def orbit_frame(t):
    k = smooth(ramp(t, T_ORBIT - 0.6, T_ORBIT + 0.8))
    R = 1500.0
    cy = lerp(1920 + R + 200, 1920 + R * 0.45, k) - 30 * (t - T_ORBIT)
    return 540 + 40 * math.sin(t * 0.2), cy, R, k


def draw_orbit(ctx, t, os_):
    if t < T_ORBIT - 0.6:
        return
    cx, cy, R, k = orbit_frame(t)
    s = ctx
    s.save()
    s.scale(os_, os_)
    earth(s, cx, cy, R, t)
    sk = smooth(ramp(t, T_ORBIT, T_ORBIT + 1.0))
    if sk > 0:
        sats = sat_positions(t, cx, cy, R)
        ground = [(cx - R * 0.6 + R * 1.2 * hash01(g, 1), cy - R * math.sqrt(max(0.0, 1 - (hash01(g, 1) * 1.2 - 0.6) ** 2)) + 20) for g in range(8)]
        for i, (x, y, tr, kk) in enumerate(sats):
            if kk % 4 == 0:
                gx, gy = ground[(tr + kk) % len(ground)]
                ph = (t * 1.5 + i * 0.1) % 1.0
                G.line(s, [(x, y), (gx, gy)], 1.5, (*EB[:3], 0.25 * sk))
                G.glow(s, lerp(x, gx, ph), lerp(y, gy, ph), 10, EB2, 0.7 * sk)
            icon(s, 'sat', x, y, 18, C['white'], sk)
    s.restore()


# ----------------------------------------------------------------------------------------------
# Space C: the network; D: the connected world
# ----------------------------------------------------------------------------------------------
_NET = None


def net_nodes():
    global _NET
    if _NET is None:
        rng = np.random.default_rng(11)
        nodes = []
        cols = 7
        for ci in range(cols):
            n = [4, 7, 9, 10, 9, 7, 4][ci]
            for j in range(n):
                x = -720 + 1440 * ci / (cols - 1) + rng.uniform(-30, 30)
                y = (j - (n - 1) / 2) * 150 + rng.uniform(-25, 25)
                nodes.append((x, y, ci))
        edges = []
        for i, (x, y, ci) in enumerate(nodes):
            for j, (x2, y2, cj) in enumerate(nodes):
                if cj == ci + 1 and rng.random() < 0.45:
                    edges.append((i, j))
        _NET = (nodes, edges)
    return _NET


def push_target(t):
    """The satellite the camera pushes into (screen space)."""
    cx, cy, R, k = orbit_frame(T_PUSH)
    sats = sat_positions(T_PUSH, cx, cy, R)
    best = min(sats, key=lambda p: (p[0] - 600) ** 2 + (p[1] - 900) ** 2)
    return best[0], best[1]


def draw_C(ctx, t, os_):
    """Push into a satellite: the orbit view scales up about it and fades, and the network grows out of its point."""
    px, py = push_target(t)
    zk = smooth(ramp(t, T_PUSH, T_NET + 0.3))
    s = ctx
    s.save()
    s.scale(os_, os_)
    G.vgrad(s, 0, 0, W, H, [(0, (0.01, 0.02, 0.05, 1)), (1, C['navy1'])])
    s.restore()
    if zk < 0.999:
        # the orbit view scaled up around the target satellite
        sc = math.exp(math.log(12.0) * ease_in(zk))
        ctx.push_group()
        ctx.save()
        ctx.translate(px * os_, py * os_)
        ctx.scale(sc, sc)
        ctx.translate(-px * os_, -py * os_)
        draw_orbit(ctx, T_PUSH + (t - T_PUSH) * 0.3, os_)
        ctx.restore()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1 - smooth(ramp(t, T_PUSH + 0.3, T_NET)))
    draw_network(ctx, t, os_, (px, py), zk)


def node_pos(i, t, focus, zk, fold):
    nodes, _ = net_nodes()
    x, y, ci = nodes[i]
    split = smooth(ramp(t, T_SPLIT + 0.4, T_SPLIT + 2.2))
    side = -1 if x < 0 else 1
    x2 = x + side * 220 * split + 18 * math.sin(t * 0.8 + i)
    y2 = y + 14 * math.cos(t * 0.7 + i * 1.3) - 60 * split * math.sin(i)
    sc = lerp(0.02, 0.62, zk)
    fx, fy = focus
    sx = lerp(fx, 540, zk) + x2 * sc
    sy = lerp(fy, 930, zk) + y2 * sc
    if fold > 0:
        # fold onto the globe: each node finds a point on its disc
        a = 2 * math.pi * hash01(i, 21)
        r = 300 * math.sqrt(hash01(i, 22))
        gx, gy = 540 + r * math.cos(a), 1010 + r * math.sin(a)
        sx, sy = lerp(sx, gx, fold), lerp(sy, gy, fold)
    return sx, sy, side


def draw_network(ctx, t, os_, focus, zk, fold=0.0):
    nodes, edges = net_nodes()
    if zk <= 0.01 and fold <= 0:
        return
    s = ctx
    s.save()
    s.scale(os_, os_)
    split = smooth(ramp(t, T_SPLIT + 0.2, T_SPLIT + 1.2))
    P = [node_pos(i, t, focus, zk, fold) for i in range(len(nodes))]
    for e, (i, j) in enumerate(edges):
        xi, yi, si = P[i]
        xj, yj, sj = P[j]
        cross = si != sj
        a = 0.35 * (1 - (split if cross else 0)) * (1 - 0.6 * fold)
        if a <= 0.01:
            continue
        col = EB if (si < 0 or split < 0.1) else mixc(EB, RED, split)
        G.line(s, [(xi, yi), (xj, yj)], 1.6, (*col[:3], a))
        ph = (t * 0.9 + hash01(e, 3)) % 1.0
        if hash01(e, 4) < 0.35:
            G.glow(s, lerp(xi, xj, ph), lerp(yi, yj, ph), 12, col, 0.8 * a / 0.35)
    for i, (x, y, side) in enumerate(P):
        col = EB2 if (side < 0 or split < 0.1) else mixc(EB2, RED, split)
        r = (7 + 5 * hash01(i, 5)) * (0.4 + 0.6 * zk) * (1 - 0.4 * fold)
        pulse = 1 + 0.25 * math.sin(t * 3 + i)
        G.glow(s, x, y, r * 4 * pulse, col, 0.35)
        s.arc(x, y, r, 0, 2 * math.pi)
        G.setc(s, col)
        s.fill()
    # a few small data read-outs beside the network
    if zk > 0.6 and fold < 0.5:
        a = smooth(ramp(t, T_NET, T_NET + 0.6)) * (1 - fold * 2)
        for k in range(3):
            bx, by = 160 + k * 340, 560 + 40 * math.sin(t + k)
            for j in range(6):
                hgt = 20 + 50 * (0.5 + 0.5 * math.sin(t * 2.5 + j + k * 2))
                G.rect(s, bx + j * 16, by - hgt, bx + j * 16 + 10, by, (*EB[:3], 0.5 * a))
    s.restore()


def draw_D(ctx, t, os_):
    """Pull back: the network folds onto a globe; a car circles it on a ring road, a rocket arcs over it,
    satellites orbit, and lines connect it all."""
    fold = smoother(ramp(t, T_FOLD, T_FOLD + 1.6))
    s = ctx
    s.save()
    s.scale(os_, os_)
    G.vgrad(s, 0, 0, W, H, [(0, (0.01, 0.02, 0.05, 1)), (1, C['navy1'])])
    for i in range(120):
        s.arc(hash01(i, 1) * W, hash01(i, 2) * H, 1.0 + 1.5 * hash01(i, 3), 0, 2 * math.pi)
        G.setc(s, C['white'], 0.5 * hash01(i, 4) * fold)
        s.fill()
    s.restore()
    if fold > 0.05:
        s = ctx
        s.save()
        s.scale(os_, os_)
        gcx, gcy = 540, 1010
        sc = lerp(1.15, 1.0, smooth(ramp(t, T_FOLD + 1.0, 32.0)))
        s.translate(gcx, gcy)
        s.scale(sc, sc)
        s.translate(-gcx, -gcy)
        s.push_group()
        earth(s, gcx, gcy, 300, t, night=0.4)
        s.pop_group_to_source()
        s.paint_with_alpha(fold)
        k2 = smooth(ramp(t, T_FOLD + 0.8, T_FOLD + 1.8))
        # orbits and what travels on them
        for ri, (rx, ry, rot, spd, kind) in enumerate(((420, 150, -0.35, 0.18, 'sat'), (380, 120, 0.4, -0.22, 'rocket'),
                                                       (460, 190, 0.05, 0.12, 'car'))):
            s.save()
            s.translate(gcx, gcy)
            s.rotate(rot)
            s.save()
            s.scale(1, ry / rx)
            s.arc(0, 0, rx, 0, 2 * math.pi)
            s.restore()
            G.setc(s, (*EB[:3], 0.45 * k2))
            s.set_line_width(2)
            s.stroke()
            for m in range(3 if kind == 'sat' else 1):
                a = t * spd * 2 * math.pi + m * 2.1 + ri
                x, y = rx * math.cos(a), ry * math.sin(a)
                if math.sin(a) < 0:      # behind the globe: dim
                    aa = 0.35
                else:
                    aa = 1.0
                icon(s, kind, x, y, 26, C['white'], k2 * aa)
            s.restore()
        s.restore()
    draw_network(ctx, t, os_, (540, 930), 1.0, fold=fold)
    k = smooth(ramp(t, 31.2, 31.95))
    if k > 0:
        s = ctx
        s.save()
        set_ = (0, 0, 0, 0.98 * k)
        s.set_source_rgba(*set_)
        s.paint()
        s.restore()


# ----------------------------------------------------------------------------------------------
# The one shot
# ----------------------------------------------------------------------------------------------
def scene_journey(ctx, t, os_):
    if t < T_SWAP:
        draw_A(ctx, t, os_)
    elif t < T_PUSH:
        draw_B(ctx, t, os_)
    elif t < T_FOLD:
        draw_C(ctx, t, os_)
    else:
        draw_D(ctx, t, os_)
    # the light of the dive: the headlight swells to fill the frame and becomes the engine light
    gk = smooth(ramp(t, T_DIVE + 0.25, T_SWAP)) * (1 - smooth(ramp(t, T_SWAP, T_SWAP + 0.45)))
    if gk > 0:
        s = ctx
        s.save()
        s.scale(os_, os_)
        G.glow(s, 540, 960, 1500 * gk + 200, EB2, 0.95 * gk)
        G.glow(s, 540, 960, 600 * gk + 60, C['white'], 0.9 * gk)
        # for the few frames around the hand-over the light fills the whole frame, edge to edge
        fk = smooth(ramp(t, T_SWAP - 0.42, T_SWAP - 0.02)) * (1 - smooth(ramp(t, T_SWAP + 0.02, T_SWAP + 0.45)))
        if fk > 0:
            s.rectangle(0, 0, W, H)
            G.setc(s, mixc(EB2, C['white'], 0.6), 0.98 * fk)
            s.fill()
        s.restore()
    return dict(dark=0.0, desat=0.03, tint=(0.97, 1.0, 1.05), bloom=0.38, grain=0.022, vig=0.5)
