"""WW2, Part 1: "How Hitler Took Europe" (1939-1941). One continuous shot over a real map: the camera never cuts, it
flies from Europe in 1939 through Poland, the West, Britain, the invasion of the USSR and the gates of Moscow, whips
across Asia to Pearl Harbor and back to the map of Hitler's Europe for the cliffhanger.

Every time comes from part1/scene_timing.json (built from the measured words of the voiceover).
"""
import math

import cairo
import numpy as np

from core import W, H, EV as E, Camera, clamp, smooth, smoother, ease_out, ease_in, ramp, hash01, vnoise, fnoise, set_c, \
    path_smooth, path_poly, soft_glow
import mapdata as M
import text as TX

END = 99.0


def hexc(h, a=1.0):
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


SEA, SEA2 = hexc('0a111e'), hexc('0e1828')
LAND, EURO, SOV = hexc('172030'), hexc('232d40'), hexc('2c3038')
RED, RED_L, RED_D, STRIPE = hexc('c81f2d'), hexc('ff5148'), hexc('6f1620'), hexc('a82430')
BLUE, BLUE_L = hexc('2b6fd6'), hexc('6bb0ff')
WHITE, YELLOW, INK = hexc('f4f7fb'), hexc('ffd23f'), hexc('05080f')
ARROW = hexc('ff4136')

OCC = ['POL_GER', 'DEN', 'NOR', 'NLD', 'BEL', 'LUX', 'FRA_OCC', 'YUG', 'GRC', 'OCC_EAST']
ALLY = ['ITA', 'HUN', 'ROU', 'BGR', 'FIN', 'FRA_VICHY']
EUROPE = [n for n in M.R if n not in ('LAND', 'OCC_EAST', 'JPN', 'HAWAII')]
BERLIN = (13.4, 52.5)
MOSCOW = (37.62, 55.75)
FRONT_TIP = (37.4, 56.0)
OAHU = (202.05, 21.4)
LAUNCH = (202.0, 26.2)


def sm(t, a, b):
    return smooth(ramp(t, a, b))


# ----------------------------------------------------------------------------------------------
# Camera: (time, lon, lat, pixels per degree of latitude). Zoom is interpolated geometrically.
# ----------------------------------------------------------------------------------------------
CAM = [
    (0.0, 12.0, 51.2, 58), (E['europe'] + 0.2, 13.0, 50.6, 36), (E['two'], 13.0, 50.6, 35.5),
    (E['most'] + 0.3, 17.0, 50.0, 31), (E['sept'] - 0.1, 17.0, 50.0, 31),
    (E['y1939b'], 17.5, 51.6, 52), (E['germany'], 19.2, 52.0, 100), (E['britain'] - 0.12, 19.8, 52.0, 110),
    (E['britain'] + 0.5, 1.5, 50.4, 50), (E['in1940'], 1.2, 50.6, 53),
    (E['y1940'] + 0.6, 8.5, 56.5, 41), (E['tanks'] + 0.05, 6.6, 51.6, 62), (E['france2'] - 0.15, 4.2, 50.6, 78),
    (E['france2'] + 0.6, 2.6, 47.0, 66), (E['falls'], 2.6, 46.8, 70), (E['britain2'] - 0.15, 2.4, 46.6, 64),
    (E['britain2'] + 0.5, 0.2, 51.6, 100), (E['so'] - 0.05, 0.5, 51.4, 112),
    (E['east'], 24.0, 49.6, 34, 'out'), (E['pour'], 26.0, 50.6, 33), (E['by'], 30.0, 52.6, 34),
    (E['twenty'], 37.42, 55.86, 620), (E['then'], 37.45, 55.87, 690),
    (E['december7'] + 0.25, 165.0, 35.0, 17, 'out'), (E['japan'] + 0.25, 167.0, 34.5, 17.5),
    (E['pearl'] + 0.1, 201.9, 20.9, 150), (E['part'] - 0.08, 202.0, 20.6, 172),
    (E['part'] + 0.5, 17.0, 50.0, 30, 'out'), (END, 17.6, 50.0, 34.5),
]
CAM[-1] = (max(E['voice_end'] + 1.5, CAM[-2][0] + 2.0), 17.6, 50.0, 33.5)
SHAKES = [(E['first'], 12), (E['poland'], 18), (E['war'], 14), (E['y1940'], 10), (E['falls'], 12), (E['six'], 18), (E['surrender'], 10),
          (E['pour'], 16), (E['seventh'], 12), (E['harbor'], 30), (E['part'], 22), (E['apart'], 20)]


def cam_state(t):
    if t <= CAM[0][0]:
        return CAM[0][1:4]
    for k0, k1 in zip(CAM, CAM[1:]):
        (t0, *a), (t1, *b) = k0[:4], k1[:4]
        if t <= t1:
            x = (t - t0) / (t1 - t0)
            u = smoother(x)
            # a whip that pulls out: the zoom is done early, so the camera is already wide while it travels
            uz = smoother(clamp(x * 1.7)) if len(k1) > 4 else u
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * uz)
    return CAM[-1][1:4]


def shake(t):
    sx = sy = 0.0
    for t0, amp in SHAKES:
        u = (t - t0) / 0.38
        if 0 <= u <= 1:
            k = (1 - u) ** 2 * amp
            sx += k * vnoise(t * 42, int(t0 * 10))
            sy += k * vnoise(t * 42, int(t0 * 10) + 5)
    return sx, sy


def make_cam(t):
    lon, lat, pxd = cam_state(t)
    z = pxd / M.K
    x, y = M.P(lon, lat)
    sx, sy = shake(t)
    return Camera(x + sx / z, y + sy / z, z, anchor=(0.0, 0.0)), z


def visible(cam, z, name, margin=60):
    x0, y0, x1, y1 = M.BBOX[name]
    hw, hh = (W / 2 + margin) / z, (H / 2 + margin) / z
    return not (x1 < cam.cx - hw or x0 > cam.cx + hw or y1 < cam.cy - hh or y0 > cam.cy + hh)


def scr(cam, lon, lat):
    return cam.world_to_screen(*M.P(lon, lat))


# ----------------------------------------------------------------------------------------------
# Map
# ----------------------------------------------------------------------------------------------
def draw_grid(ctx, cam, z, alpha):
    pxd = z * M.K
    step = next((s for s in (20, 10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05) if s * pxd <= 430), 0.05)
    hw, hh = (W / 2 + 20) / z, (H / 2 + 20) / z
    lon0 = M.LON0 + (cam.cx - hw) / (M.CLAT * M.K)
    lon1 = M.LON0 + (cam.cx + hw) / (M.CLAT * M.K)
    lat0, lat1 = M.LAT0 - (cam.cy + hh) / M.K, M.LAT0 - (cam.cy - hh) / M.K
    ctx.new_path()
    v = math.floor(lon0 / step) * step
    while v <= lon1:
        x = (v - M.LON0) * M.CLAT * M.K
        ctx.move_to(x, cam.cy - hh)
        ctx.line_to(x, cam.cy + hh)
        v += step
    v = math.floor(lat0 / step) * step
    while v <= lat1:
        y = -(v - M.LAT0) * M.K
        ctx.move_to(cam.cx - hw, y)
        ctx.line_to(cam.cx + hw, y)
        v += step
    set_c(ctx, WHITE, alpha)
    ctx.set_line_width(1.2 / z)
    ctx.stroke()


def blobs(ctx, srcs, R, seed, t):
    """Wobbly ink-like fronts spreading from the source points (sub-paths of one path)."""
    ctx.new_path()
    for i, (lo, la) in enumerate(srcs):
        cx, cy = M.P(lo, la)
        pts = []
        for k in range(64):
            a = k / 64 * 2 * math.pi
            r = R * (1 + 0.24 * fnoise(math.cos(a) * 1.8 + 3.1 * (seed + i), seed + i, 3) + 0.1 * fnoise(math.sin(a) * 3.0 + t * 0.8, seed + i + 9, 2))
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        path_smooth(ctx, np.array(pts), True, 0.5)


def hatch(ctx, names, z, col, a):
    x0 = min(M.BBOX[n][0] for n in names)
    y0 = min(M.BBOX[n][1] for n in names)
    x1 = max(M.BBOX[n][2] for n in names)
    y1 = max(M.BBOX[n][3] for n in names)
    ctx.save()
    M.clip(ctx, names)
    s = 13 / z
    k = math.floor((x0 - (y1 - y0)) / s) * s
    ctx.new_path()
    while k < x1:
        ctx.move_to(k, y1)
        ctx.line_to(k + (y1 - y0), y0)
        k += s
    set_c(ctx, col, a)
    ctx.set_line_width(4.2 / z)
    ctx.stroke()
    ctx.restore()


def flood(ctx, cam, z, t, names, col, srcs, k, Rmax, seed=1, dark=False, edge=RED_L):
    """Colour regions as far as fronts spreading from srcs have reached (k: 0 nothing .. 1 everything)."""
    if k <= 0:
        return
    vis = [n for n in names if visible(cam, z, n)]
    if not vis:
        return
    ctx.save()
    R = Rmax * k ** 0.85
    if k < 1:
        blobs(ctx, srcs, R, seed, t)
        ctx.clip()
    for n in vis:
        M.fill(ctx, n, col)
    if dark:
        hatch(ctx, vis, z, STRIPE, 0.55)
    if k < 1:
        M.clip(ctx, vis)
        blobs(ctx, srcs, R, seed, t)
        for lw, al in ((16, 0.25), (6, 0.9)):
            set_c(ctx, edge, al)
            ctx.set_line_width(lw / z)
            ctx.stroke_preserve()
        ctx.new_path()
    ctx.restore()


def tint(ctx, cam, z, names, col, a, dark=False):
    if a <= 0.003:
        return
    vis = [n for n in names if visible(cam, z, n)]
    for n in vis:
        M.fill(ctx, n, col, a)
    if dark and vis:
        hatch(ctx, vis, z, STRIPE, 0.55 * a)


def draw_map(ctx, cam, z, t):
    set_c(ctx, SEA)
    ctx.paint()
    draw_grid(ctx, cam, z, 0.045)
    # a soft lighter shelf around the coasts
    M.stroke(ctx, 'LAND', SEA2, 22 / z, 0.9)
    M.fill(ctx, 'LAND', LAND)
    for n in EUROPE:
        if visible(cam, z, n):
            M.fill(ctx, n, EURO)
    tint(ctx, cam, z, ['USSR'], SOV, 1.0)
    tint(ctx, cam, z, ['POL_SOV'], SOV, sm(t, E['poland'] + 0.5, E['poland'] + 1.1) * (1 if t > E['sept'] else 0))

    # --- the hook: fast-forward to 1941, then rewind
    hk = sm(t, E['two'] + 0.25, E['most'] + 0.2) * (1 - sm(t, E['sept'] - 0.16, E['sept'] + 0.34))
    if hk > 0:
        flood(ctx, cam, z, t, OCC, RED, [BERLIN], hk, 980, 3)
        flood(ctx, cam, z, t, ALLY, RED_D, [BERLIN], hk, 980, 3, dark=True)
    main = t > E['sept'] + 0.3
    # --- Allies in blue
    kb = sm(t, E['britain'], E['britain'] + 0.25)
    tint(ctx, cam, z, ['GBR'], BLUE, 0.92 * kb)
    kf = sm(t, E['france'], E['france'] + 0.25)
    tint(ctx, cam, z, ['FRA_OCC', 'FRA_VICHY'], BLUE, 0.92 * kf * (1 - sm(t, E['weeks'], E['weeks'] + 0.5)))
    if main:
        flood(ctx, cam, z, t, ['POL_GER'], RED, [(17.0, 51.0), (20.5, 53.5), (17.3, 53.6), (19.8, 49.4)], ramp(t, E['invades'] + 0.05, E['poland'] + 0.9), 200, 11)
        flood(ctx, cam, z, t, ['DEN', 'NOR'], RED, [(10.0, 54.6)], ramp(t, E['y1940'] + 0.1, E['y1940'] + 1.05), 640, 13)
        flood(ctx, cam, z, t, ['NLD', 'BEL', 'LUX'], RED, [(6.4, 50.9)], ramp(t, E['tanks'], E['west'] + 0.75), 180, 15)
        flood(ctx, cam, z, t, ['FRA_OCC'], RED, [(4.9, 49.7)], ramp(t, E['falls'], E['weeks'] + 0.4), 430, 17)
        tint(ctx, cam, z, ['FRA_VICHY', 'ITA'], RED_D, sm(t, E['six'], E['weeks'] + 0.5), dark=True)
        flood(ctx, cam, z, t, ['YUG', 'GRC'], RED, [(19.5, 46.2)], ramp(t, E['so'] + 0.1, E['east'] + 0.1), 500, 19)
        tint(ctx, cam, z, ['HUN', 'ROU', 'BGR', 'FIN'], RED_D, sm(t, E['so'], E['turns'] + 0.25), dark=True)
        flood(ctx, cam, z, t, ['OCC_EAST'], RED, [(22.5, 54.8), (23.6, 52.2), (24.5, 50.3), (27.5, 47.2)], ramp(t, E['pour'], E['by'] + 1.2), 620, 21)
    tint(ctx, cam, z, ['SVK'], RED_D, 1.0, dark=True)
    M.fill(ctx, 'GER', RED)
    # Japan lights up for Pearl Harbor
    if visible(cam, z, 'JPN'):
        M.fill(ctx, 'JPN', RED, sm(t, E['japan'] - 0.05, E['japan'] + 0.25) * (1 - sm(t, E['part'], E['part'] + 0.3)))
    if visible(cam, z, 'HAWAII', 400):
        M.fill(ctx, 'HAWAII', hexc('46567a'))
        M.stroke(ctx, 'HAWAII', WHITE, 2.2 / z, 0.9)
    # borders and coast
    for n in EUROPE:
        if visible(cam, z, n):
            M.stroke(ctx, n, WHITE, 1.25 / z, 0.26)
    M.stroke(ctx, 'LAND', WHITE, 1.3 / z, 0.34)
    pulse = 0.5 + 0.5 * math.sin(t * 5.0)
    if visible(cam, z, 'GER'):
        for lw, al in ((12, 0.14), (4, 0.5)):
            M.stroke(ctx, 'GER', RED_L, lw / z, al * (0.6 + 0.4 * pulse))
    if main and t > E['pour'] and visible(cam, z, 'OCC_EAST'):
        M.stroke(ctx, 'OCC_EAST', RED_L, 3 / z, 0.55 * sm(t, E['by'] + 0.8, E['by'] + 1.4))


# ----------------------------------------------------------------------------------------------
# Arrows and icons (world space; sizes are given in screen pixels and divided by the zoom)
# ----------------------------------------------------------------------------------------------
def spline(pts, n=56):
    p = np.asarray(pts, float)
    if len(p) == 2:
        return p[0] + (p[1] - p[0]) * np.linspace(0, 1, n)[:, None]
    out = []
    m = len(p)
    per = max(2, n // (m - 1))
    for i in range(m - 1):
        p0, p1, p2, p3 = p[max(i - 1, 0)], p[i], p[i + 1], p[min(i + 2, m - 1)]
        for u in np.linspace(0, 1, per, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(p[-1])
    return np.array(out)


def along(path, u):
    """Point and heading at fraction u of a sampled path."""
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    d = clamp(u) * cum[-1]
    k = int(min(np.searchsorted(cum, d), len(path) - 1))
    k = max(k, 1)
    f = (d - cum[k - 1]) / max(cum[k] - cum[k - 1], 1e-9)
    p = path[k - 1] + (path[k] - path[k - 1]) * f
    v = path[k] - path[k - 1]
    return p, math.atan2(v[1], v[0])


def arrow(ctx, lonlat, u, z, w=28, col=ARROW, alpha=1.0):
    """A bold tapered arrow growing along a curved route; u = how much of it is drawn."""
    if u <= 0.02 or alpha <= 0.003:
        return
    path = spline(M.PP(lonlat))
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    L = cum[-1] * clamp(u)
    px = 1.0 / z
    head = min(54 * px, L * 0.6)
    k = int(np.searchsorted(cum, max(L - head, 1e-6)))
    k = max(1, min(k, len(path) - 1))
    f = (L - head - cum[k - 1]) / max(cum[k] - cum[k - 1], 1e-9)
    body = np.vstack([path[:k], path[k - 1] + (path[k] - path[k - 1]) * clamp(f)])
    tip, ang = along(path, clamp(u))
    d = np.array([math.cos(ang), math.sin(ang)])
    nrm = np.array([-d[1], d[0]])
    g = np.gradient(body, axis=0) if len(body) > 1 else np.array([d])
    g /= np.linalg.norm(g, axis=1, keepdims=True) + 1e-9
    nn = np.stack([-g[:, 1], g[:, 0]], 1)
    ws = np.linspace(0.22, 1.0, len(body))[:, None] * w * px * 0.5
    base = body[-1]
    poly = np.vstack([body + nn * ws, [base + nrm * w * px * 1.25], [tip], [base - nrm * w * px * 1.25], (body - nn * ws)[::-1]])
    ctx.save()
    ctx.translate(0, 7 * px)
    ctx.new_path()
    path_poly(ctx, poly, True)
    set_c(ctx, INK, 0.45 * alpha)
    ctx.fill()
    ctx.restore()
    ctx.new_path()
    path_poly(ctx, poly, True)
    set_c(ctx, col, alpha)
    ctx.fill_preserve()
    set_c(ctx, INK, 0.9 * alpha)
    ctx.set_line_width(3 * px)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    if len(body) > 2:
        ctx.new_path()
        path_poly(ctx, body[len(body) // 5:] - nn[len(body) // 5:] * ws[len(body) // 5:] * 0.45, False)
        set_c(ctx, WHITE, 0.55 * alpha)
        ctx.set_line_width(2.6 * px)
        ctx.stroke()


def tank(ctx, x, y, ang, z, s=1.0, alpha=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.scale(s / z, s / z)
    for (a, b, c, d_, col) in ((-19, -13, 38, 26, INK), (-17, -11, 34, 5.5, hexc('3a3f4a')), (-17, 5.5, 34, 5.5, hexc('3a3f4a')), (-15, -7.5, 30, 15, hexc('8c95a6'))):
        ctx.rectangle(a, b, c, d_)
        set_c(ctx, col, alpha)
        ctx.fill()
    ctx.rectangle(4, -2, 24, 4)
    set_c(ctx, hexc('d5dbe6'), alpha)
    ctx.fill()
    ctx.arc(0, 0, 7.5, 0, 2 * math.pi)
    set_c(ctx, hexc('d5dbe6'), alpha)
    ctx.fill_preserve()
    set_c(ctx, INK, alpha)
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.restore()


def plane(ctx, x, y, ang, z, s=1.0, col=WHITE, alpha=1.0, bomber=False):
    span = 24 if bomber else 17
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.scale(s / z, s / z)
    shapes = [[(20, 0), (11, 2.6), (-15, 1.8), (-20, 0), (-15, -1.8), (11, -2.6)],
              [(7, 0), (1, span), (-4, span), (-2, 0), (-4, -span), (1, -span)],
              [(-14, 0), (-17, 7), (-20, 7), (-18, 0), (-20, -7), (-17, -7)]]
    for dy, c, a in ((6, INK, 0.45), (0, col, 1.0)):
        for sh in shapes:
            ctx.new_path()
            path_poly(ctx, np.array(sh, float) + np.array([-dy * 0.4, dy]), True)
            set_c(ctx, c, a * alpha)
            ctx.fill()
    if bomber:
        for e in (-9, 9):
            ctx.rectangle(0, e - 2, 9, 4)
            set_c(ctx, col, alpha)
            ctx.fill()
    ctx.restore()


def burst(ctx, x, y, k, z, s=1.0, seed=0):
    """An explosion at age k (0..1): white core, orange glow, a shock ring and sparks."""
    if k <= 0 or k >= 1:
        return
    px = s / z
    soft_glow(ctx, x, y, (60 + 260 * ease_out(k)) * px, hexc('ff8a2a'), 0.8 * (1 - k))
    soft_glow(ctx, x, y, (30 + 90 * ease_out(k)) * px, hexc('fff2c8'), 1.0 * (1 - k) ** 2)
    set_c(ctx, hexc('ffd9a0'), 0.9 * (1 - k))
    ctx.set_line_width(5 * px * (1 - k) + px)
    ctx.arc(x, y, (20 + 240 * ease_out(k)) * px, 0, 2 * math.pi)
    ctx.stroke()
    for j in range(12):
        a = hash01(j, seed) * 2 * math.pi
        r0, r1 = (30 + 200 * k) * px, (60 + 260 * k) * px
        ctx.move_to(x + math.cos(a) * r0, y + math.sin(a) * r0)
        ctx.line_to(x + math.cos(a) * r1, y + math.sin(a) * r1)
    set_c(ctx, hexc('ffe9b0'), 0.8 * (1 - k))
    ctx.set_line_width(3 * px)
    ctx.stroke()


# (route, start, grow time, fade start, width)
ARROWS = [
    ([(17.2, 51.1), (18.8, 51.6), (20.6, 52.1)], E['invades'], 0.7, E['britain'] - 0.15, 36),
    ([(20.4, 53.6), (20.9, 53.0), (21.2, 52.5)], E['invades'] + 0.1, 0.6, E['britain'] - 0.15, 30),
    ([(16.9, 53.5), (18.3, 53.6), (19.6, 53.0)], E['invades'] + 0.05, 0.6, E['britain'] - 0.15, 30),
    ([(19.6, 49.3), (20.6, 49.9), (22.4, 49.9)], E['invades'] + 0.15, 0.7, E['britain'] - 0.15, 30),
    ([(9.8, 54.0), (10.2, 56.0), (9.0, 58.6), (8.5, 60.8)], E['y1940'] + 0.12, 0.75, E['tanks'] - 0.1, 24),
    ([(7.0, 50.3), (5.2, 49.8), (3.4, 49.9), (1.9, 50.4)], E['tanks'], 0.85, E['france2'] - 0.05, 28),
    ([(7.3, 52.3), (5.6, 52.2), (4.6, 52.0)], E['tanks'] + 0.1, 0.6, E['france2'] - 0.05, 20),
    ([(6.6, 51.1), (5.2, 50.8), (4.0, 50.9)], E['tanks'] + 0.2, 0.6, E['france2'] - 0.05, 20),
    ([(3.2, 49.9), (2.6, 49.2), (2.35, 48.4), (1.8, 47.0), (0.5, 45.6)], E['falls'], 0.95, E['britain2'] - 0.15, 28),
    ([(5.6, 49.3), (5.2, 48.2), (5.0, 46.9), (4.9, 45.6)], E['falls'] + 0.1, 0.9, E['britain2'] - 0.15, 24),
    ([(1.6, 49.8), (0.0, 49.0), (-1.6, 48.2), (-1.5, 47.2)], E['falls'] + 0.15, 0.9, E['britain2'] - 0.15, 22),
    ([(20.5, 47.0), (20.8, 45.0), (21.5, 43.0), (22.5, 40.5), (23.2, 38.6)], E['so'] + 0.2, 0.8, E['over'], 24),
    ([(21.5, 54.9), (24.5, 56.6), (28.0, 58.3), (29.9, 59.4)], E['pour'], 1.7, E['then'] + 0.1, 30),
    ([(23.5, 52.3), (27.5, 53.6), (32.0, 54.7), (37.02, 55.83)], E['pour'] + 0.05, 2.6, E['then'] + 0.1, 36),
    ([(24.0, 50.4), (28.5, 50.2), (33.0, 49.3), (38.4, 47.7)], E['pour'] + 0.1, 2.1, E['then'] + 0.1, 30),
]
ROUTE = [(147.9, 45.0), (160.0, 43.6), (175.0, 42.2), (190.0, 38.0), (198.5, 31.5), LAUNCH]
UNITS = [(1.5, 48.0), (3.0, 48.3), (4.6, 48.5), (0.2, 47.3), (2.0, 47.1), (3.8, 47.2), (5.5, 47.4), (0.6, 45.9), (2.4, 45.7), (4.2, 45.7),
         (1.3, 44.5), (3.1, 44.4), (5.6, 44.7), (-1.2, 48.1)]


def draw_action(ctx, cam, z, t):
    px = 1.0 / z
    for route, t0, grow, tf, w in ARROWS:
        if t0 - 0.05 <= t <= tf + 0.3:
            u = ease_out(ramp(t, t0, t0 + grow)) if grow < 1.5 else smooth(ramp(t, t0, t0 + grow))
            al = 1 - sm(t, tf, tf + 0.28)
            arrow(ctx, route, u, z, w, ARROW, al)
            if t0 == E['invades'] or abs(t0 - E['tanks']) < 0.01 or abs(t0 - E['falls']) < 0.01 or (grow > 1.5 and z < 4):
                path = spline(M.PP(route))
                for k in range(2):
                    uu = u - 0.2 - 0.17 * k
                    if uu > 0.03:
                        p, a = along(path, uu)
                        nrm = np.array([-math.sin(a), math.cos(a)]) * (34 if k == 0 else -34) * px
                        tank(ctx, p[0] + nrm[0], p[1] + nrm[1], a, z, 0.95, al)
    # Warsaw under attack
    wx, wy = M.P(21.0, 52.23)
    for j in range(3):
        burst(ctx, wx + (j - 1) * 14 * px, wy + (j % 2) * 10 * px, (t - E['poland'] - 0.12 - j * 0.16) / 0.55, z, 0.5, j)
    # the Battle of Britain: bombers come over the Channel, fighters meet them, the bombers turn back
    if E['britain2'] - 0.4 <= t <= E['so'] + 0.3:
        u = ramp(t, E['britain2'] - 0.3, E['surrender'] + 0.6)
        al = sm(t, E['britain2'] - 0.4, E['britain2']) * (1 - sm(t, E['so'] - 0.1, E['so'] + 0.25))
        a0, a1 = np.array(M.P(2.6, 50.1)), np.array(M.P(-0.3, 51.45))
        back = sm(u, 0.62, 0.8)
        for i in range(7):
            off = np.array([-(i // 2 + (i % 2)) * 84 * px, ((i % 2) * 2 - 1) * ((i + 1) // 2) * 62 * px])
            f = min(u, 0.66) / 0.66 * 0.8 - 1.1 * max(0, u - 0.66)
            p = a0 + (a1 - a0) * f + off
            ang = math.atan2(a1[1] - a0[1], a1[0] - a0[0]) + math.pi * back
            hit = i in (1, 4) and u > 0.6
            if hit:
                burst(ctx, p[0], p[1], (u - 0.6 - 0.05 * i) / 0.25, z, 0.8, i)
            plane(ctx, p[0], p[1], ang, z, 2.3, RED_L, al * (0 if hit and u > 0.72 else 1), bomber=True)
        b0, b1 = np.array(M.P(-2.6, 53.0)), np.array(M.P(0.9, 51.0))
        for i in range(5):
            f = ease_out(ramp(u, 0.12 + i * 0.03, 0.62)) * (0.78 + 0.05 * i) + 0.25 * max(0, u - 0.62)
            p = b0 + (b1 - b0) * f + np.array([(i - 2) * 64 * px, (i % 2) * 70 * px])
            plane(ctx, p[0], p[1], math.atan2(b1[1] - b0[1], b1[0] - b0[0]), z, 1.9, hexc('dff0ff'), al)
            if 0.45 < u < 0.8 and int(t * 22 + i) % 2 == 0:
                q = p + (b1 - b0) / np.linalg.norm(b1 - b0) * 110 * px
                ctx.move_to(*(p + (q - p) * 0.4))
                ctx.line_to(*q)
                set_c(ctx, YELLOW, 0.9 * al)
                ctx.set_line_width(3 * px)
                ctx.stroke()
        # radar pulses from the coast
        for k in range(3):
            v = ((t - E['britain2']) * 0.9 + k / 3) % 1.0
            cx, cy = M.P(1.2, 51.3)
            set_c(ctx, BLUE_L, 0.5 * (1 - v) * al)
            ctx.set_line_width(3 * px)
            ctx.arc(cx, cy, (20 + 190 * v) * px, -0.9, 1.0)
            ctx.stroke()
    # the strike force crosses the north Pacific; the planes go in
    if E['japan'] - 0.1 <= t <= E['part'] + 0.3:
        al = 1 - sm(t, E['part'] - 0.05, E['part'] + 0.25)
        path = spline(M.PP(ROUTE), 90)
        u = sm(t, E['japan'], E['attacks'] + 0.25)
        seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
        cum = np.concatenate([[0], np.cumsum(seg)])
        n = int(np.searchsorted(cum, u * cum[-1]))
        if n > 1:
            ctx.new_path()
            path_poly(ctx, path[:n], False)
            set_c(ctx, YELLOW, 0.95 * al)
            ctx.set_line_width(4 * px)
            ctx.set_dash([14 * px, 10 * px])
            ctx.stroke()
            ctx.set_dash([])
        if 0.02 < u:
            p, a = along(path, u)
            for k in range(3):      # the carriers
                q = p - np.array([math.cos(a), math.sin(a)]) * k * 34 * px + np.array([0, (k - 1) * 12 * px])
                ctx.save()
                ctx.translate(*q)
                ctx.rotate(a)
                ctx.scale(px, px)
                ctx.new_path()
                path_poly(ctx, np.array([(-16, -4.5), (10, -4.5), (17, 0), (10, 4.5), (-16, 4.5)], float), True)
                set_c(ctx, WHITE, al)
                ctx.fill_preserve()
                set_c(ctx, INK, al)
                ctx.set_line_width(1.5)
                ctx.stroke()
                ctx.restore()
        v = ramp(t, E['attacks'] + 0.15, E['pearl'] + 0.3)
        if v > 0:
            a0, a1 = np.array(M.P(*LAUNCH)), np.array(M.P(*OAHU))
            for i in range(9):
                vv = clamp(v * 1.25 - 0.03 * i)
                p = a0 + (a1 - a0) * (vv * 1.1) + np.array([((i % 3) - 1) * 70 * px, -(i // 3) * 80 * px])
                plane(ctx, p[0], p[1], math.atan2(a1[1] - a0[1], a1[0] - a0[0]), z, 2.0, RED_L, al * (1 - sm(vv, 0.95, 1.0)))
        ox, oy = M.P(*OAHU)
        for j in range(5):
            burst(ctx, ox + (hash01(j, 3) - 0.5) * 110 * px, oy + (hash01(j, 4) - 0.5) * 80 * px, (t - E['harbor'] - j * 0.12) / 0.65, z, 1.5, j + 20)


# ----------------------------------------------------------------------------------------------
# Screen-space overlay: labels, markers, counters, snow, cracks
# ----------------------------------------------------------------------------------------------
LABELS = [
    # text, lon, lat, in, out, size, colour
    ('GERMANY', 10.6, 51.2, 0.45, E['sept'] - 0.2, 50, TX.WHITE),
    ('FRANCE', 2.5, 47.0, E['europe'] - 0.5, E['later'] + 0.4, 44, TX.WHITE),
    ('BRITAIN', -1.6, 53.2, E['europe'] - 0.35, E['later'] + 0.4, 44, TX.WHITE),
    ('POLAND', 20.0, 52.0, E['europe'] - 0.2, E['later'] + 0.4, 44, TX.WHITE),
    ('SOVIET UNION', 33.0, 54.5, E['europe'], E['later'] + 0.4, 44, TX.WHITE),
    ('ITALY', 12.3, 43.2, E['europe'] + 0.1, E['later'] + 0.4, 40, TX.WHITE),
    ('GERMANY', 13.8, 51.3, E['germany'], E['britain'] - 0.1, 54, TX.WHITE),
    ('POLAND', 20.3, 51.6, E['y1939b'] + 0.3, E['britain'] - 0.1, 58, TX.WHITE),
    ('BRITAIN', -1.6, 53.0, E['britain'], E['in1940'], 56, TX.WHITE),
    ('FRANCE', 2.5, 47.2, E['france'], E['in1940'], 56, TX.WHITE),
    ('NORWAY', 9.0, 61.0, E['y1940'] + 0.5, E['tanks'], 46, TX.WHITE),
    ('FRANCE', 2.4, 46.6, E['france2'], E['britain2'] - 0.1, 70, TX.WHITE),
    ('BRITAIN', -1.9, 53.3, E['britain2'], E['so'], 66, TX.WHITE),
    ('SOVIET UNION', 39.5, 49.2, E['east'] - 0.1, E['by'] + 0.7, 54, TX.WHITE),
    ('JAPAN', 137.5, 38.5, E['japan'], E['pearl'] - 0.15, 60, TX.WHITE),
]
DOTS = [('WARSAW', 21.0, 52.23, E['germany'] + 0.2, E['britain'] - 0.1), ('PARIS', 2.35, 48.86, E['france2'] + 0.3, E['britain2'] - 0.1),
        ('LONDON', -0.12, 51.5, E['britain2'] + 0.1, E['so']), ('LENINGRAD', 30.3, 59.93, E['pour'] + 0.2, E['less']),
        ('MOSCOW', 37.62, 55.75, E['pour'] + 0.3, E['december'] + 0.4), ('KIEV', 30.5, 50.45, E['pour'] + 0.4, E['less'])]


def dot(ctx, x, y, os_, a, col=None, r=10):
    if a <= 0:
        return
    soft_glow(ctx, x * os_, y * os_, r * 3.4 * os_, WHITE, 0.5 * a)
    set_c(ctx, INK, a)
    ctx.arc(x * os_, y * os_, (r + 3) * os_, 0, 2 * math.pi)
    ctx.fill()
    set_c(ctx, col or WHITE, a)
    ctx.arc(x * os_, y * os_, r * os_, 0, 2 * math.pi)
    ctx.fill()


def number(ctx, os_, s, x, y, size, col, alpha=1.0, scale=1.0):
    """Draw a changing number from cached single-character sprites."""
    adv = {',': 0.3, '+': 0.56, ' ': 0.3, '<': 0.56}
    ws = [adv.get(ch, 0.5) * size for ch in s]
    x0 = x - sum(ws) / 2 * scale
    for ch, w_ in zip(s, ws):
        if ch != ' ':
            sf = TX.label_surface(ch, size, col, os_, ow=0, fn='anton')
            ctx.save()
            ctx.identity_matrix()
            ctx.translate((x0 + w_ / 2 * scale) * os_, (y + (0.4 * size * scale if ch == ',' else 0)) * os_)
            ctx.scale(scale, scale)
            ctx.set_source_surface(sf, -sf.get_width() / 2, -sf.get_height() / 2)
            ctx.paint_with_alpha(alpha)
            ctx.restore()
        x0 += w_ * scale


_CRACKS = None


def cracks():
    global _CRACKS
    if _CRACKS is None:
        from scipy.spatial import Voronoi
        rng = np.random.default_rng(7)
        x0, y1 = M.P(-9, 34)
        x1, y0 = M.P(44, 63)
        pts = np.column_stack([rng.uniform(x0, x1, 46), rng.uniform(y0, y1, 46)])
        v = Voronoi(np.vstack([pts, [[x0 - 900, y0 - 900], [x1 + 900, y0 - 900], [x0 - 900, y1 + 900], [x1 + 900, y1 + 900]]]))
        c = np.array(M.P(*BERLIN))
        _CRACKS = [(v.vertices[a], v.vertices[b], float(np.linalg.norm((v.vertices[a] + v.vertices[b]) / 2 - c)))
                   for a, b in v.ridge_vertices if a >= 0 and b >= 0]
    return _CRACKS


def draw_overlay(ctx, cam, z, t, os_):
    ctx.save()
    ctx.identity_matrix()
    # city dots and labels
    for name, lo, la, t0, t1 in DOTS:
        if t0 <= t <= t1 + 0.25:
            x, y = scr(cam, lo, la)
            if -40 < x < 1120 and 150 < y < 1700:
                al, s = TX.pop(t, t0)
                al *= 1 - sm(t, t1, t1 + 0.2)
                dot(ctx, x, y, os_, al)
                if 300 < y < 1140:
                    TX.paint_label(ctx, name, x, y - 46, 34, os_, TX.WHITE, al, s, ow=5)
    for txt, lo, la, t0, t1, size, col in LABELS:
        if t0 <= t <= t1 + 0.25:
            x, y = scr(cam, lo, la)
            if -200 < x < 1280 and 290 < y < 1150:
                al, s = TX.pop(t, t0)
                TX.paint_label(ctx, txt, x, y, size, os_, col, al * (1 - sm(t, t1, t1 + 0.2)), s)
    # France's army: unit markers fill the country, then are swept away
    if E['biggest'] - 0.05 <= t <= E['weeks'] + 0.5:
        for i, (lo, la) in enumerate(UNITS):
            x, y = scr(cam, lo, la)
            al, s = TX.pop(t, E['biggest'] - 0.05 + i * 0.05, 0.2)
            gone = sm(t, E['falls'] + 0.1 + i * 0.05, E['falls'] + 0.4 + i * 0.05)
            if al <= 0 or gone >= 1:
                continue
            ctx.save()
            ctx.translate(x * os_, y * os_)
            ctx.scale(os_ * s * (1 - 0.5 * gone), os_ * s * (1 - 0.5 * gone))
            ctx.rotate(0.5 * gone * (1 if i % 2 else -1))
            col = tuple(np.array(BLUE_L) * (1 - gone) + np.array(RED_L) * gone)
            ctx.rectangle(-24, -16, 48, 32)
            set_c(ctx, INK, 0.9 * al * (1 - gone))
            ctx.fill_preserve()
            set_c(ctx, col, al * (1 - gone))
            ctx.set_line_width(4)
            ctx.stroke()
            ctx.move_to(-24, -16)
            ctx.line_to(24, 16)
            ctx.move_to(24, -16)
            ctx.line_to(-24, 16)
            ctx.set_line_width(3)
            ctx.stroke()
            ctx.restore()
    # 3,000,000+ counting up
    if E['three'] <= t <= E['by'] - 0.02:
        u = ease_out(ramp(t, E['three'], E['troops'] + 0.1))
        n = int(round(3000000 * u / 10000) * 10000)
        al = sm(t, E['three'], E['three'] + 0.12) * (1 - sm(t, E['by'] - 0.2, E['by'] - 0.02))
        punch = 1 + 0.18 * (1 - clamp((t - E['troops'] - 0.1) / 0.2)) if t >= E['troops'] + 0.1 else 1.0
        number(ctx, os_, f'{n:,}' + ('+' if u >= 1 else ''), 540, 452, 210, TX.YELLOW, al, punch)
        TX.paint_label(ctx, 'TROOPS INVADE THE USSR', 540, 585, 46, os_, TX.WHITE, al * sm(t, E['troops'], E['troops'] + 0.2), 1.0)
    # Moscow: the city, the stalled front and the distance
    km = sm(t, E['december'] + 0.5, E['less'] + 0.1) * (1 - sm(t, E['then'], E['then'] + 0.22))
    if km > 0:
        mx, my = scr(cam, *MOSCOW)
        fx, fy = scr(cam, *FRONT_TIP)
        pxd = z * M.K
        for r_deg, a in ((0.085, 0.16), (0.05, 0.22), (0.022, 0.3)):
            set_c(ctx, WHITE, a * km)
            ctx.set_line_width(2.5 * os_)
            ctx.arc(mx * os_, my * os_, r_deg * pxd * os_, 0, 2 * math.pi)
            ctx.stroke()
        for k in range(10):
            a = k / 10 * 2 * math.pi + 0.2
            ctx.move_to((mx + math.cos(a) * 0.022 * pxd) * os_, (my + math.sin(a) * 0.022 * pxd) * os_)
            ctx.line_to((mx + math.cos(a) * 0.1 * pxd) * os_, (my + math.sin(a) * 0.1 * pxd) * os_)
        set_c(ctx, WHITE, 0.12 * km)
        ctx.stroke()
        # the Kremlin's star
        ctx.new_path()
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            r = (26 if k % 2 == 0 else 11) * os_
            ctx.line_to(mx * os_ + math.cos(a) * r, my * os_ + math.sin(a) * r)
        ctx.close_path()
        set_c(ctx, WHITE, km)
        ctx.fill_preserve()
        set_c(ctx, INK, km)
        ctx.set_line_width(3 * os_)
        ctx.stroke()
        TX.paint_label(ctx, 'MOSCOW', mx + 10, my + 78, 60, os_, TX.WHITE, km, 1.0)
        kd = sm(t, E['less'], E['twenty'] + 0.1) * km
        if kd > 0:
            ex, ey = fx + (mx - fx) * kd, fy + (my - fy) * kd
            for lw, col, a in ((12, INK, 0.8), (6, YELLOW, 1.0)):
                set_c(ctx, col, a * km)
                ctx.set_line_width(lw * os_)
                ctx.set_dash([18 * os_, 10 * os_])
                ctx.move_to(fx * os_, fy * os_)
                ctx.line_to(ex * os_, ey * os_)
                ctx.stroke()
            ctx.set_dash([])
            dot(ctx, fx, fy, os_, km, RED_L, 9)
            al, s = TX.pop(t, E['twenty'])
            TX.paint_label(ctx, '< 20 MILES', (fx + mx) / 2 + 235, (fy + my) / 2 - 40, 96, os_, TX.YELLOW, al * km, s, ow=8, fn='anton')
            TX.paint_label(ctx, 'GERMAN FRONT LINE', fx - 170, fy - 78, 40, os_, TX.WHITE, km * sm(t, E['less'], E['less'] + 0.2), 1.0, ow=5)
    # snow and frost
    ks = sm(t, E['by'], E['by'] + 0.9) * (1 - sm(t, E['then'], E['then'] + 0.3))
    if ks > 0:
        g = cairo.RadialGradient(540 * os_, 900 * os_, 500 * os_, 540 * os_, 900 * os_, 1250 * os_)
        g.add_color_stop_rgba(0, 0.8, 0.9, 1, 0)
        g.add_color_stop_rgba(1, 0.8, 0.9, 1, 0.34 * ks)
        ctx.set_source(g)
        ctx.paint()
        for i in range(170):
            sp = 240 + 420 * hash01(i, 1)
            x = (hash01(i, 2) * 1180 + 60 * math.sin(t * 1.3 + i) - 120 * t * (0.4 + hash01(i, 5))) % 1180 - 50
            y = (hash01(i, 3) * 2000 + t * sp) % 2000 - 40
            r = 1.6 + 4.2 * hash01(i, 4) ** 2
            set_c(ctx, WHITE, (0.35 + 0.55 * hash01(i, 6)) * ks)
            ctx.arc(x * os_, y * os_, r * os_, 0, 2 * math.pi)
            ctx.fill()
    # Hawaii: the destination, marked as soon as the route starts
    if E['japan'] + 0.15 <= t <= E['pearl']:
        ox, oy = scr(cam, *OAHU)
        al, s_ = TX.pop(t, E['japan'] + 0.15)
        al *= 1 - sm(t, E['attacks'] + 0.3, E['pearl'])
        dot(ctx, ox, oy, os_, al, YELLOW, 9)
        TX.paint_label(ctx, 'HAWAII', ox - 10, oy + 56, 46, os_, TX.WHITE, al, s_)
    # Pearl Harbor: target, label, flash
    if E['attacks'] <= t <= E['part'] + 0.2:
        ox, oy = scr(cam, *OAHU)
        al = 1 - sm(t, E['part'] - 0.05, E['part'] + 0.2)
        k = sm(t, E['attacks'] + 0.1, E['pearl'])
        for r, a in ((70 + 160 * (1 - k), 0.9), (36 + 80 * (1 - k), 0.6)):
            set_c(ctx, YELLOW, a * k * al)
            ctx.set_line_width(4 * os_)
            ctx.arc(ox * os_, oy * os_, r * os_, 0, 2 * math.pi)
            ctx.stroke()
        pa, ps = TX.pop(t, E['pearl'])
        TX.paint_label(ctx, 'PEARL HARBOR', ox, oy + 200, 66, os_, TX.WHITE, pa * al, ps, plate=TX.RED + (255,))
        TX.paint_label(ctx, 'HAWAII, USA', ox, oy + 286, 38, os_, TX.GREY, pa * al, 1.0, ow=5)
        f = (t - E['harbor']) / 0.3
        if 0 <= f < 1:
            set_c(ctx, hexc('fff4dc'), 0.75 * (1 - f) ** 2)
            ctx.paint()
    # the rewind: scan bars as the map snaps back to 1939
    rw = (t - (E['sept'] - 0.2)) / 0.55
    if 0 <= rw <= 1:
        for i in range(9):
            y = (hash01(i, int(t * 30)) * 1920)
            set_c(ctx, WHITE, 0.16 * math.sin(rw * math.pi))
            ctx.rectangle(0, y * os_, 1080 * os_, (8 + 50 * hash01(i, 9)) * os_)
            ctx.fill()
    ctx.restore()


def draw_cracks(ctx, cam, z, t):
    k = ramp(t, E['fell'] - 0.05, E['apart'] + 0.75)
    if k <= 0:
        return
    R = 900 * ease_out(k)
    names = [n for n in ['GER', 'SVK'] + OCC + ALLY if visible(cam, z, n)]
    ctx.save()
    M.clip(ctx, names)
    for lw, col, a in ((11, INK, 0.85), (4.5, hexc('fff0c0'), 1.0)):
        ctx.new_path()
        for p, q, d in cracks():
            if d < R:
                m = (p + q) / 2 + np.array([vnoise(d * 0.07, 1), vnoise(d * 0.07, 2)]) * 9
                ctx.move_to(*p)
                ctx.line_to(*m)
                ctx.line_to(*q)
        set_c(ctx, col, a)
        ctx.set_line_width(lw / z)
        ctx.set_line_join(cairo.LINE_JOIN_MITER)
        ctx.stroke()
    ctx.restore()


def scene_main(ctx, t, os_):
    cam, z = make_cam(t)
    ctx.save()
    cam.apply(ctx, 1.0, os_)
    draw_map(ctx, cam, z, t)
    draw_cracks(ctx, cam, z, t)
    draw_action(ctx, cam, z, t)
    ctx.restore()
    draw_overlay(ctx, cam, z, t, os_)
    # motion blur from the camera's own speed (the whip-pans)
    c0, z0 = make_cam(t - 1 / 60)
    c1, z1 = make_cam(t + 1 / 60)
    bx, by = (c1.cx - c0.cx) * z * 0.55, (c1.cy - c0.cy) * z * 0.55
    look = dict(dark=0.0, desat=0.02, bloom=0.3, vig=0.5, grain=0.03, tint=(1.0, 1.0, 1.03))
    if abs(bx) > 22 or abs(by) > 22:
        look['blur'] = (min(abs(bx), 420), min(abs(by), 240))
        # speed streaks along the direction of travel
        k = min(1.0, math.hypot(bx, by) / 260)
        ang = math.atan2(by, bx)
        ctx.save()
        ctx.identity_matrix()
        ctx.translate(540 * os_, 960 * os_)
        ctx.rotate(ang)
        for i in range(22):
            f = int(t * 30)
            y = (hash01(i, f) - 0.5) * 2200
            x = (hash01(i, f + 7) - 0.5) * 1400
            ln = 260 + 900 * hash01(i, f + 3)
            set_c(ctx, WHITE, (0.06 + 0.2 * hash01(i, f + 5)) * k)
            ctx.set_line_width((1.5 + 4 * hash01(i, f + 9)) * os_)
            ctx.move_to((x - ln / 2) * os_, y * os_)
            ctx.line_to((x + ln / 2) * os_, y * os_)
            ctx.stroke()
        ctx.restore()
    ks = sm(t, E['by'], E['by'] + 0.9) * (1 - sm(t, E['then'], E['then'] + 0.3))
    if ks > 0:
        look['tint'] = (1.0 - 0.06 * ks, 1.0, 1.03 + 0.05 * ks)
        look['desat'] = 0.02 + 0.2 * ks
    return look
