"""WW2, Part 2: "How It All Fell Apart" (1942-1945). One continuous shot over the map, in the style of Part 1:
Hitler's Europe at its peak -> Stalingrad -> the Pacific -> D-Day -> Germany squeezed from west and east -> Berlin ->
Japan -> the cost. Every time comes from part2/scene_timing.json (the measured words of the narration).
"""
import math

import cairo
import numpy as np

from core import W, H, EV as E, Camera, clamp, smooth, smoother, ease_out, ease_in, ramp, hash01, vnoise, fnoise, set_c, \
    path_smooth, path_poly, soft_glow
import mapdata as M
import text as TX
from common import *  # noqa: F401,F403  (colours, sm, flood, tint, arrow, plane, burst, dot, number, ...)
from common import hexc, sm, visible, scr, draw_grid, blobs, hatch, tint, spline, along, arrow, tank, plane, burst, dot, number, \
    SEA, SEA2, LAND, EURO, SOV, RED, RED_L, RED_D, STRIPE, BLUE, BLUE_L, WHITE, YELLOW, INK, ARROW, EUROPE

END = 99.0
AX = ['POL_GER', 'DEN', 'NOR', 'NLD', 'BEL', 'LUX', 'FRA_OCC', 'FRA_VICHY', 'YUG', 'GRC', 'OCC_42']
ALLY = ['ITA', 'HUN', 'ROU', 'BGR', 'FIN', 'SVK']
STALINGRAD = (44.55, 48.71)
KALACH = (43.53, 48.68)
POCKET = (44.05, 48.72)
BERLIN = (13.4, 52.52)
HIROSHIMA, NAGASAKI = (132.46, 34.39), (129.87, 32.75)
NORMANDY = (-0.7, 49.3)
BLUE_A = hexc('3f8cff')
VOLGA = [(45.9, 51.5), (45.4, 50.1), (44.83, 49.05), (44.6, 48.75), (44.75, 48.5), (45.6, 48.35), (46.3, 48.2), (47.2, 47.2), (48.0, 46.35)]
DON = [(39.2, 51.7), (39.5, 51.0), (40.1, 50.45), (40.55, 49.95), (41.7, 49.6), (42.7, 49.6), (43.05, 49.3), (43.55, 48.7), (43.2, 48.1),
       (42.2, 47.6), (40.8, 47.5), (39.7, 47.2)]
BEACHES = [('UTAH', -1.18, 49.42), ('OMAHA', -0.87, 49.37), ('GOLD', -0.55, 49.34), ('JUNO', -0.42, 49.335), ('SWORD', -0.28, 49.30)]
PERIM = [(152, 50), (170, 40), (172, 10), (175, -2), (163, -11), (150, -9), (135, -10), (120, -11), (105, -9), (94, 4), (92, 20)]
HOPS = [
    ([(196, 19), (176, 4), (170, 8.5), (150, 14), (141.5, 24.5), (129, 26.5)], 'c'),
    ([(172, -19), (160.5, -10), (148, -6.5), (135, -1.5), (126, 10), (122, 16)], 's'),
]
ISLANDS = [('MIDWAY', 182.6, 28.2, 0.0, -1), ('GUADALCANAL', 160.0, -9.6, 0.22, 1), ('SAIPAN', 145.7, 15.2, 0.6, -1),
           ('IWO JIMA', 141.3, 24.8, 0.8, -1), ('OKINAWA', 127.8, 26.4, 0.97, 1)]

CAM = [
    (0.0, 16.5, 50.0, 29), (E['unstoppable'] + 0.5, 20.0, 50.0, 32.5), (E['then'], 21.0, 50.0, 33),
    (E['city'] + 0.1, 43.6, 48.9, 120), (E['stalingrad'], 43.9, 48.8, 150), (E['america'] - 0.1, 44.0, 48.75, 168),
    (E['america'] + 0.8, 163.0, 16.0, 15.5, 'out'), (E['june'] - 0.1, 160.0, 17.0, 16.5),
    (E['june'] + 0.8, -0.9, 49.95, 290), (E['about'] - 0.05, -0.9, 49.92, 310),
    (E['about'] + 0.95, -0.73, 49.47, 1300), (E['germany'] - 0.1, -0.72, 49.46, 1380),
    (E['crushed'] + 0.1, 12.0, 49.5, 33, 'out'), (E['inmay'], 13.0, 50.0, 35),
    (E['soviet'], 13.4, 52.3, 120), (E['august'] - 0.1, 13.4, 52.45, 150),
    (E['august'] + 0.7, 133.0, 33.0, 95, 'out'), (E['by'] - 0.05, 132.6, 32.8, 105),
    (E['war'], 140.0, 33.0, 24, 'out'), (E['estimated'], 143.0, 32.0, 21),
    (E['seventy'] + 0.3, 78.0, 32.0, 9.6, 'out'), (max(E['voice_end'] + 2.0, E['seventy'] + 3.5), 80.0, 32.0, 9.0),
]
SHAKES = [(E['part'], 20), (E['brk'], 16), (E['stalingrad'], 12), (E['surrenders'], 18), (E['dday'], 20), (E['land'], 12),
          (E['crushed'], 14), (E['berlin'], 16), (E['surrenders2'], 18), (E['two2'], 16), (E['bombs'], 16)]


def cam_state(t):
    if t <= CAM[0][0]:
        return CAM[0][1:4]
    for k0, k1 in zip(CAM, CAM[1:]):
        (t0, *a), (t1, *b) = k0[:4], k1[:4]
        if t <= t1:
            x = (t - t0) / (t1 - t0)
            u = smoother(x)
            uz = smoother(clamp(x * 1.7)) if len(k1) > 4 else u
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * uz)
    return CAM[-1][1:4]


def make_cam(t):
    lon, lat, pxd = cam_state(t)
    z = pxd / M.K
    x, y = M.P(lon, lat)
    sx = sy = 0.0
    for t0, amp in SHAKES:
        u = (t - t0) / 0.38
        if 0 <= u <= 1:
            k = (1 - u) ** 2 * amp
            sx += k * vnoise(t * 42, int(t0 * 10))
            sy += k * vnoise(t * 42, int(t0 * 10) + 5)
    return Camera(x + sx / z, y + sy / z, z, anchor=(0.0, 0.0)), z


def keyf(t, pts):
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * smooth((t - t0) / (t1 - t0))
    return pts[-1][1]


def fronts(ctx, t):
    """The path of the Allied fronts at time t: the beachhead growing from Normandy, the advance up Italy, and the
    Soviet front sweeping in from the east (a very large circle, so its edge reads as a line). Returns False if empty."""
    rw = keyf(t, [(E['land'], 0.0), (E['day'], 4.5), (E['germany'], 7.0), (E['crushed'], 24.0), (E['inmay'], 150.0), (E['berlin'], 262.0)])
    rs = keyf(t, [(E['america'], 0.0), (E['june'], 150.0), (E['inmay'], 232.0), (E['berlin'], 280.0)])
    re_ = keyf(t, [(E['surrenders'], 484.0), (E['june'], 760.0), (E['germany'], 800.0), (E['inmay'], 1000.0), (E['berlin'], 1090.0)]) if t >= E['surrenders'] else 0.0
    done = sm(t, E['surrenders2'], E['surrenders2'] + 0.5)
    ctx.new_path()
    if done > 0:
        cx, cy = M.P(*BERLIN)
        ctx.arc(cx, cy, 30 + 1500 * done, 0, 2 * math.pi)
        ctx.close_path()
    any_ = done > 0
    if rw > 0.5:
        blobs_add(ctx, [NORMANDY], rw, 41, t)
        any_ = True
    if rs > 0.5:
        blobs_add(ctx, [(14.0, 37.3)], rs, 43, t)
        any_ = True
    if re_ > 1:
        cx, cy = M.P(70.0, 50.0)
        pts = []
        for k in range(160):
            a = k / 160 * 2 * math.pi
            r = re_ * (1 + 0.012 * fnoise(k * 0.35 + t * 0.4, 5, 3))
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        path_poly(ctx, np.array(pts), True)
        any_ = True
    return any_


def blobs_add(ctx, srcs, R, seed, t):
    for i, (lo, la) in enumerate(srcs):
        cx, cy = M.P(lo, la)
        pts = []
        for k in range(64):
            a = k / 64 * 2 * math.pi
            r = R * (1 + 0.2 * fnoise(math.cos(a) * 1.8 + 3.1 * (seed + i), seed + i, 3) + 0.06 * fnoise(math.sin(a) * 3.0 + t * 0.8, seed + i + 9, 2))
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        path_smooth(ctx, np.array(pts), True, 0.5)


_CR = None


def cracks_from(center):
    global _CR
    if _CR is None:
        from scipy.spatial import Voronoi
        rng = np.random.default_rng(12)
        x0, y1 = M.P(-9, 34)
        x1, y0 = M.P(48, 63)
        pts = np.column_stack([rng.uniform(x0, x1, 60), rng.uniform(y0, y1, 60)])
        v = Voronoi(np.vstack([pts, [[x0 - 900, y0 - 900], [x1 + 900, y0 - 900], [x0 - 900, y1 + 900], [x1 + 900, y1 + 900]]]))
        c = np.array(M.P(*center))
        _CR = [(v.vertices[a], v.vertices[b], float(np.linalg.norm((v.vertices[a] + v.vertices[b]) / 2 - c)))
               for a, b in v.ridge_vertices if a >= 0 and b >= 0]
    return _CR


def draw_map(ctx, cam, z, t):
    set_c(ctx, SEA)
    ctx.paint()
    draw_grid(ctx, cam, z, 0.045)
    M.stroke(ctx, 'LAND', SEA2, 22 / z, 0.9)
    M.fill(ctx, 'LAND', LAND)
    for n in EUROPE:
        if visible(cam, z, n):
            M.fill(ctx, n, EURO)
    tint(ctx, cam, z, ['USSR', 'POL_SOV', 'LIT', 'LAT', 'EST'], SOV, 1.0)
    peace = sm(t, E['war'], E['over'] + 0.6)
    gone = sm(t, E['surrenders2'], E['surrenders2'] + 0.7)
    # --- Axis Europe
    ra = 1 - gone
    tint(ctx, cam, z, AX, RED, ra)
    tint(ctx, cam, z, ALLY, RED_D, ra, dark=True)
    if visible(cam, z, 'GER'):
        M.fill(ctx, 'GER', RED, ra)
    tint(ctx, cam, z, ['GBR'], BLUE, 0.92 * (1 - peace))
    # --- liberated ground, behind the advancing fronts
    names = [n for n in AX + ALLY + ['GER'] if visible(cam, z, n)]
    if names and t > E['america'] - 0.5:
        ctx.save()
        if fronts(ctx, t):
            ctx.clip()
            for n in names:
                M.fill(ctx, n, EURO)
                M.fill(ctx, n, BLUE, 0.8 * (1 - peace))
            M.clip(ctx, names)
            if fronts(ctx, t):
                for lw, al in ((18, 0.22), (6, 0.85)):
                    set_c(ctx, BLUE_L, al * (1 - gone))
                    ctx.set_line_width(lw / z)
                    ctx.stroke_preserve()
            ctx.new_path()
        ctx.restore()
    # --- the Stalingrad pocket
    px_, py_ = M.P(*POCKET)
    kp = sm(t, E['army'] - 0.1, E['army'] + 0.15)
    if kp > 0 and z > 1.2 and t < E['america'] + 1.0:
        dead = sm(t, E['surrenders'], E['surrenders'] + 0.35)
        ctx.arc(px_, py_, 14.5, 0, 2 * math.pi)
        col = tuple(np.array(RED_D) * (1 - dead) + np.array(hexc('15233c')) * dead)
        set_c(ctx, col, kp)
        ctx.fill_preserve()
        set_c(ctx, BLUE_L, kp)
        ctx.set_line_width(6 / z)
        ctx.stroke()
    # --- Japan and its conquests
    if visible(cam, z, 'JAP_EMPIRE'):
        M.fill(ctx, 'JAP_EMPIRE', RED, 0.9 * (1 - sm(t, E['august'] - 0.4, E['august'] + 0.2)))
        M.fill(ctx, 'JPN', RED, 1 - peace)
    if visible(cam, z, 'HAWAII', 400):
        M.fill(ctx, 'HAWAII', hexc('46567a'))
    for n in EUROPE:
        if visible(cam, z, n):
            M.stroke(ctx, n, WHITE, 1.25 / z, 0.26)
    M.stroke(ctx, 'LAND', WHITE, 1.3 / z, 0.34)
    if visible(cam, z, 'GER') and ra > 0:
        pulse = 0.5 + 0.5 * math.sin(t * 5.0)
        for lw, al in ((12, 0.14), (4, 0.5)):
            M.stroke(ctx, 'GER', RED_L, lw / z, al * (0.6 + 0.4 * pulse) * ra)
    # rivers at Stalingrad
    kr = sm(z, 1.6, 3.0) * (1 if t < E['america'] + 1 else 0)
    if kr > 0:
        for pts in (VOLGA, DON):
            ctx.new_path()
            path_smooth(ctx, M.PP(pts), False)
            set_c(ctx, hexc('5c8fd0'), 0.85 * kr)
            ctx.set_line_width(5 / z)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.stroke()
    # the empire starts to crack at Stalingrad
    kc = ramp(t, E['began'], E['brk'] + 1.0)
    fade = 1 - sm(t, E['america'] - 0.2, E['america'] + 0.3)
    if kc > 0 and fade > 0:
        R = 420 * ease_out(kc)
        nm = [n for n in AX + ['GER'] + ALLY if visible(cam, z, n)]
        if nm:
            ctx.save()
            M.clip(ctx, nm)
            for lw, col in ((11, INK), (4.5, hexc('fff0c0'))):
                ctx.new_path()
                for p, q, d in cracks_from(STALINGRAD):
                    if d < R:
                        m = (p + q) / 2 + np.array([vnoise(d * 0.07, 1), vnoise(d * 0.07, 2)]) * 9
                        ctx.move_to(*p)
                        ctx.line_to(*m)
                        ctx.line_to(*q)
                set_c(ctx, col, fade * (0.85 if col is INK else 1.0))
                ctx.set_line_width(lw / z)
                ctx.stroke()
            ctx.restore()


def ship(ctx, x, y, ang, z, s=1.0, alpha=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.scale(s / z, s / z)
    ctx.new_path()
    path_poly(ctx, np.array([(-11, -4), (7, -4), (12, 0), (7, 4), (-11, 4)], float), True)
    set_c(ctx, WHITE, alpha)
    ctx.fill_preserve()
    set_c(ctx, INK, alpha)
    ctx.set_line_width(1.5)
    ctx.stroke()
    ctx.move_to(-12, 0)
    ctx.line_to(-34, 0)
    set_c(ctx, WHITE, 0.35 * alpha)
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.restore()


_BEACH = None


def beaches():
    """The five beaches, snapped onto the map's own coastline."""
    global _BEACH
    if _BEACH is None:
        rings = [r for poly in M.R['FRA_OCC'] for r in poly]
        out = []
        for name, lo, la in BEACHES:
            p = np.array(M.P(lo, la))
            best, bd = p, 1e9
            for r in rings:
                a, b = r[:-1].astype(float), r[1:].astype(float)
                ab = b - a
                u = np.clip(((p - a) * ab).sum(1) / ((ab * ab).sum(1) + 1e-9), 0, 1)
                q = a + ab * u[:, None]
                d = np.linalg.norm(q - p, axis=1)
                k = int(np.argmin(d))
                if d[k] < bd:
                    best, bd = q[k], d[k]
            out.append((name, np.array([p[0], best[1]]) if bd < 4 else p))
        _BEACH = out
    return _BEACH


SQUEEZE = [
    ([(-0.5, 49.2), (2.3, 48.9), (6.0, 50.2), (10.2, 51.6)], 34),
    ([(13.6, 38.2), (13.0, 41.5), (11.6, 44.6)], 24),
    ([(34.0, 56.0), (26.0, 54.6), (19.5, 53.4), (14.4, 52.75)], 30),
    ([(35.0, 50.5), (27.5, 50.6), (20.5, 51.3), (14.6, 52.2)], 36),
    ([(31.5, 46.4), (25.5, 46.0), (20.5, 47.2), (16.9, 48.1)], 26),
]


def draw_action(ctx, cam, z, t):
    px = 1.0 / z
    # --- Stalingrad: the German drive, then the Soviet pincers close behind it
    if E['then'] <= t <= E['america'] + 0.6:
        al = 1 - sm(t, E['america'] - 0.1, E['america'] + 0.3)
        arrow(ctx, [(40.6, 49.0), (42.6, 48.85), (44.35, 48.74)], smooth(ramp(t, E['then'] + 0.3, E['city'] + 0.3)), z, 34, ARROW,
              al * (1 - 0.75 * sm(t, E['surrenders'], E['surrenders'] + 0.3)))
        u = ease_out(ramp(t, E['entire'], E['army'] + 0.05))
        arrow(ctx, [(42.6, 50.25), (43.1, 49.45), (43.5, 48.84)], u, z, 42, BLUE_A, al)
        arrow(ctx, [(45.3, 47.6), (44.4, 48.1), (43.64, 48.54)], u, z, 42, BLUE_A, al)
        kx, ky = M.P(*KALACH)
        burst(ctx, kx, ky, (t - E['army'] - 0.02) / 0.5, z, 0.7, 3)
        sx_, sy_ = M.P(*POCKET)
        for j in range(3):
            burst(ctx, sx_ + (j - 1) * 20 * px, sy_ + (j % 2) * 16 * px, (t - E['surrenders'] - j * 0.12) / 0.55, z, 0.6, j + 5)
    # --- the Pacific: the perimeter of Japan's conquests, and the two American drives through the islands
    if E['america'] - 0.2 <= t <= E['june'] + 0.9:
        al = 1 - sm(t, E['june'] + 0.2, E['june'] + 0.7)
        ctx.new_path()
        path_smooth(ctx, M.PP(PERIM), False)
        set_c(ctx, RED_L, 0.8 * al * sm(t, E['america'] + 0.5, E['america'] + 1.0))
        ctx.set_line_width(6 * px)
        ctx.set_dash([18 * px, 12 * px])
        ctx.stroke()
        ctx.set_dash([])
        u = smooth(ramp(t, E['fights'] + 0.1, E['pacific'] + 0.75))
        for route, _ in HOPS:
            arrow(ctx, route, u, z, 30, BLUE_A, al)
        mx_, my_ = M.P(182.6, 28.2)
        burst(ctx, mx_, my_, (t - E['fights'] - 0.05) / 0.6, z, 0.6, 9)
    # --- D-Day: the fleet crosses the Channel; the troops go ashore
    if E['june'] <= t <= E['crushed'] + 0.3:
        al = sm(t, E['june'] + 0.3, E['june'] + 0.7) * (1 - sm(t, E['germany'], E['crushed']))
        tgt = beaches()
        for i in range(64):
            b = tgt[i % 5][1]
            start = np.array(M.P(-3.4 + 4.0 * hash01(i, 1), 50.45 + 0.3 * hash01(i, 2)))
            end = b + np.array([(hash01(i, 3) - 0.5) * 2.4, -(0.4 + 2.2 * hash01(i, 4))])
            u = smooth(ramp(t, E['june'] + 0.4 + 0.9 * hash01(i, 5), E['land'] + 0.2 + 0.5 * hash01(i, 6)))
            p = start + (end - start) * u
            ship(ctx, p[0], p[1], math.atan2(end[1] - start[1], end[0] - start[0]), z, 1.25 if z < 20 else 2.2, al * (1 - 0.8 * sm(u, 0.9, 1.0) * (1 if z > 20 else 0)))
        for i in range(7):
            u = ramp(t, E['sixth'] + i * 0.07, E['about'] + 0.6 + i * 0.07)
            a0, a1 = np.array(M.P(-2.6 + i * 0.5, 51.1)), np.array(M.P(-1.6 + i * 0.25, 49.0))
            p = a0 + (a1 - a0) * u
            plane(ctx, p[0], p[1], math.atan2(a1[1] - a0[1], a1[0] - a0[0]), z, 1.5, hexc('dff0ff'), al * (1 - sm(u, 0.9, 1.0)) * (1 if z < 20 else 0))
        # inland from each beach
        for i, (name, b) in enumerate(tgt):
            u = ease_out(ramp(t, E['land'] + i * 0.06, E['land'] + 0.6 + i * 0.06))
            if u > 0:
                a0 = b + np.array([0, 0.2])
                a1 = b + np.array([(i - 2) * 0.35, 3.6])
                pa = a0 + (a1 - a0) * np.linspace(0, 1, 6)[:, None]
                arrow_w(ctx, pa, u, z, 26, BLUE_A, 1 - sm(t, E['germany'], E['crushed']))
    # --- Germany squeezed from west, south and east
    if E['germany'] - 0.1 <= t <= E['august'] + 0.5:
        al = sm(t, E['germany'], E['germany'] + 0.3) * (1 - sm(t, E['surrenders2'] + 0.3, E['surrenders2'] + 0.8))
        u = smooth(ramp(t, E['crushed'], E['berlin'] + 0.1))
        for route, w in SQUEEZE:
            arrow(ctx, route, 0.12 + 0.88 * u, z, w, BLUE_A, al)
        bx_, by_ = M.P(*BERLIN)
        for j in range(4):
            burst(ctx, bx_ + (hash01(j, 1) - 0.5) * 50 * px, by_ + (hash01(j, 2) - 0.5) * 40 * px, (t - E['berlin'] - 0.1 - j * 0.14) / 0.6, z, 0.8, j + 30)
    # --- Hiroshima and Nagasaki: a flash and a widening ring each, nothing more
    for (lo, la), t0 in ((HIROSHIMA, E['two2']), (NAGASAKI, E['bombs'])):
        k = (t - t0) / 1.6
        if 0 <= k <= 1:
            x, y = M.P(lo, la)
            soft_glow(ctx, x, y, (40 + 520 * ease_out(k)) * px, hexc('fff4dc'), 0.95 * (1 - k) ** 1.5)
            soft_glow(ctx, x, y, (30 + 200 * ease_out(k)) * px, hexc('ffb060'), 0.8 * (1 - k))
            for r0, a in ((1.0, 0.9), (0.6, 0.5)):
                set_c(ctx, WHITE, a * (1 - k))
                ctx.set_line_width((6 * (1 - k) + 1.5) * px)
                ctx.arc(x, y, (20 + 420 * ease_out(k)) * px * r0, 0, 2 * math.pi)
                ctx.stroke()


def arrow_w(ctx, wpts, u, z, w, col, alpha):
    """arrow() for a route already in world units."""
    lonlat = [(M.LON0 + p[0] / (M.CLAT * M.K), M.LAT0 - p[1] / M.K) for p in wpts]
    arrow(ctx, lonlat, u, z, w, col, alpha)


LABELS = [
    ('GERMANY', 10.8, 51.2, E['hitlers'], E['then'] + 0.3, 50),
    ('BRITAIN', -1.6, 53.2, E['hitlers'] + 0.15, E['then'] + 0.3, 44),
    ('SOVIET UNION', 38.5, 56.5, E['hitlers'] + 0.3, E['then'] + 0.5, 44),
    ('ENGLAND', -2.7, 50.98, E['june'] + 0.7, E['about'] + 0.3, 54),
    ('NORMANDY', -0.6, 48.85, E['june'] + 0.8, E['about'] + 0.3, 54),
    ('WESTERN ALLIES', 1.5, 46.6, E['crushed'], E['may'] + 0.2, 46),
    ('SOVIET ARMY', 27.5, 55.9, E['both'], E['may'] + 0.2, 46),
    ('JAPAN', 138.3, 37.6, E['august'] - 0.05, E['by'], 60),
    ('JAPAN', 138.0, 36.0, E['by'] + 0.6, E['estimated'], 50),
]


def draw_overlay(ctx, cam, z, t, os_):
    ctx.save()
    ctx.identity_matrix()
    for txt, lo, la, t0, t1, size in LABELS:
        if t0 <= t <= t1 + 0.25:
            x, y = scr(cam, lo, la)
            if -200 < x < 1280 and 290 < y < 1150:
                al, s = TX.pop(t, t0)
                TX.paint_label(ctx, txt, x, y, size, os_, TX.WHITE, al * (1 - sm(t, t1, t1 + 0.2)), s)
    # Stalingrad
    if E['city'] - 0.2 <= t <= E['america'] + 0.4:
        al, s = TX.pop(t, E['city'] - 0.1)
        al *= 1 - sm(t, E['america'] - 0.1, E['america'] + 0.2)
        x, y = scr(cam, *STALINGRAD)
        dot(ctx, x, y, os_, al, YELLOW, 12)
        TX.paint_label(ctx, 'STALINGRAD', x + 30, y - 62, 50, os_, TX.WHITE, al, s)
        x2, y2 = scr(cam, 46.0, 49.6)
        TX.paint_label(ctx, 'VOLGA', x2, y2, 30, os_, (130, 170, 225), al * sm(t, E['stalingrad'], E['stalingrad'] + 0.3), 1.0, ow=4)
        ka, ks_ = TX.pop(t, E['army'] + 0.1)
        x3, y3 = scr(cam, *POCKET)
        TX.paint_label(ctx, 'SURROUNDED', x3 - 40, y3 + 96, 46, os_, TX.BLUE, ka * al * (1 - sm(t, E['surrenders'], E['surrenders'] + 0.2)), ks_, ow=6)
        x4, y4 = scr(cam, 43.3, 50.35)
        TX.paint_label(ctx, 'SOVIET ARMY', x4, y4, 40, os_, TX.BLUE, al * sm(t, E['entire'], E['entire'] + 0.25), 1.0, ow=5)
    # the Pacific islands
    if E['america'] + 0.4 <= t <= E['june'] + 0.6:
        u = smooth(ramp(t, E['fights'] + 0.1, E['pacific'] + 0.75))
        fade = 1 - sm(t, E['june'] - 0.05, E['june'] + 0.3)
        for name, lo, la, f, side in ISLANDS:
            tt_ = E['fights'] + 0.1 + f * (E['pacific'] + 0.75 - E['fights'] - 0.1)
            if u >= f - 0.02:
                x, y = scr(cam, lo, la)
                al, s = TX.pop(t, tt_ if f > 0 else E['america'] + 0.6)
                dot(ctx, x, y, os_, al * fade, BLUE_L, 9)
                if 290 < y < 1150:
                    TX.paint_label(ctx, name, x, y + side * 44, 34, os_, TX.WHITE, al * fade, s, ow=5)
        x, y = scr(cam, 202.05, 21.4)
        al, s = TX.pop(t, E['america'] + 0.5)
        dot(ctx, x, y, os_, al * fade, YELLOW, 9)
        TX.paint_label(ctx, 'HAWAII', x - 6, y + 46, 34, os_, TX.WHITE, al * fade, s, ow=5)
        x, y = scr(cam, 137, 37)
        TX.paint_label(ctx, 'JAPAN', x, y - 60, 46, os_, TX.WHITE, al * fade, s)
        x, y = scr(cam, 186, 9)
        TX.paint_label(ctx, 'US FORCES', x, y, 40, os_, TX.BLUE, al * fade * sm(t, E['fights'], E['fights'] + 0.2), 1.0, ow=5)
    # the beaches and the count
    if E['about'] + 0.5 <= t <= E['crushed']:
        fade = 1 - sm(t, E['germany'] - 0.05, E['germany'] + 0.25)
        for i, (name, b) in enumerate(beaches()):
            x, y = cam.world_to_screen(*b)
            al, s = TX.pop(t, E['allied'] - 0.15 + i * 0.14)
            dot(ctx, x, y, os_, al * fade, YELLOW, 13)
            TX.paint_label(ctx, name, x, y - (64 if i % 2 == 0 else 122), 44, os_, TX.WHITE, al * fade, s, clampx=False)
    if E['n156'] <= t <= E['germany'] + 0.1:
        u = ease_out(ramp(t, E['n156'], E['allied']))
        n = int(round(156000 * u / 1000) * 1000)
        al = sm(t, E['n156'], E['n156'] + 0.12) * (1 - sm(t, E['germany'] - 0.12, E['germany'] + 0.08))
        punch = 1 + 0.18 * (1 - clamp((t - E['allied']) / 0.2)) if t >= E['allied'] else 1.0
        number(ctx, os_, f'{n:,}', 540, 400, 230, TX.YELLOW, al, punch)
        TX.paint_label(ctx, 'ALLIED TROOPS, IN ONE DAY', 540, 540, 46, os_, TX.WHITE, al * sm(t, E['allied'], E['allied'] + 0.2), 1.0)
    # Berlin
    if E['soviet'] - 0.3 <= t <= E['august'] + 0.3:
        x, y = scr(cam, *BERLIN)
        al, s = TX.pop(t, E['soviet'] - 0.2)
        al *= 1 - sm(t, E['august'] - 0.1, E['august'] + 0.2)
        dot(ctx, x, y, os_, al, YELLOW, 13)
        for k in range(2):
            v = ((t - E['soviet']) * 0.9 + k / 2) % 1.0
            set_c(ctx, YELLOW, 0.6 * (1 - v) * al)
            ctx.set_line_width(4 * os_)
            ctx.arc(x * os_, y * os_, (20 + 110 * v) * os_, 0, 2 * math.pi)
            ctx.stroke()
        TX.paint_label(ctx, 'BERLIN', x, y - 70, 66, os_, TX.WHITE, al, s)
    # Hiroshima and Nagasaki
    for name, (lo, la), t0, dy in (('HIROSHIMA', HIROSHIMA, E['two2'], -78), ('NAGASAKI', NAGASAKI, E['bombs'], 86)):
        if t0 - 0.02 <= t <= E['by'] + 0.4:
            x, y = scr(cam, lo, la)
            al, s = TX.pop(t, t0)
            al *= 1 - sm(t, E['by'], E['by'] + 0.3)
            dot(ctx, x, y, os_, al, WHITE, 8)
            TX.paint_label(ctx, name, x, y + dy, 46, os_, TX.WHITE, al, s)
            TX.paint_label(ctx, 'AUG 6' if name == 'HIROSHIMA' else 'AUG 9', x, y + dy + (48 if dy > 0 else -48), 34, os_, TX.YELLOW, al, s, ow=5)
            f = (t - t0) / 0.35
            if 0 <= f < 1:
                set_c(ctx, hexc('fff4dc'), 0.6 * (1 - f) ** 2)
                ctx.paint()
    # snow over Stalingrad
    ks = sm(t, E['frozen'] - 0.2, E['frozen'] + 0.6) * (1 - sm(t, E['america'] - 0.1, E['america'] + 0.3))
    if ks > 0:
        g = cairo.RadialGradient(540 * os_, 900 * os_, 500 * os_, 540 * os_, 900 * os_, 1250 * os_)
        g.add_color_stop_rgba(0, 0.8, 0.9, 1, 0)
        g.add_color_stop_rgba(1, 0.8, 0.9, 1, 0.3 * ks)
        ctx.set_source(g)
        ctx.paint()
        for i in range(170):
            sp = 240 + 420 * hash01(i, 1)
            x = (hash01(i, 2) * 1180 + 60 * math.sin(t * 1.3 + i) - 120 * t * (0.4 + hash01(i, 5))) % 1180 - 50
            y = (hash01(i, 3) * 2000 + t * sp) % 2000 - 40
            set_c(ctx, WHITE, (0.35 + 0.55 * hash01(i, 6)) * ks)
            ctx.arc(x * os_, y * os_, (1.6 + 4.2 * hash01(i, 4) ** 2) * os_, 0, 2 * math.pi)
            ctx.fill()
    # the cost: the map dims; one dot for every million people
    kd = sm(t, E['estimated'], E['seventy'] + 0.2)
    if kd > 0:
        set_c(ctx, INK, 0.5 * kd)
        ctx.paint()
        a1, s1 = TX.pop(t, E['seventy'])
        TX.paint_label(ctx, '70 - 85 MILLION', 540, 395, 150, os_, TX.WHITE, a1, s1, ow=0, fn='anton')
        a2, s2 = TX.pop(t, E['people'])
        TX.paint_label(ctx, 'PEOPLE DIED', 540, 520, 60, os_, TX.WHITE, a2, s2, ow=0)
        cols, n = 17, 85
        for i in range(n):
            r_, c_ = divmod(i, cols)
            x = 540 + (c_ - (cols - 1) / 2) * 54
            y = 690 + r_ * 62
            if i < 70:
                t0 = E['seventy'] + (E['eightyfive'] - E['seventy']) * i / 70
            else:
                t0 = E['eightyfive'] + (E['million'] + 0.2 - E['eightyfive']) * (i - 70) / 15
            a = sm(t, t0, t0 + 0.18)
            if a <= 0:
                continue
            if i < 70:
                soft_glow(ctx, x * os_, y * os_, 24 * os_, WHITE, 0.25 * a)
                set_c(ctx, WHITE, a)
                ctx.arc(x * os_, y * os_, 11 * os_, 0, 2 * math.pi)
                ctx.fill()
            else:
                set_c(ctx, WHITE, 0.75 * a)
                ctx.set_line_width(3 * os_)
                ctx.arc(x * os_, y * os_, 10 * os_, 0, 2 * math.pi)
                ctx.stroke()
        TX.paint_label(ctx, 'EACH DOT: ONE MILLION LIVES', 540, 1040, 34, os_, TX.GREY, sm(t, E['million'], E['million'] + 0.4), 1.0, ow=0)
        TX.paint_label(ctx, '1939 - 1945', 540, 1100, 34, os_, TX.GREY, sm(t, E['died'], E['died'] + 0.4), 1.0, ow=0)
    ctx.restore()


def scene_main(ctx, t, os_):
    cam, z = make_cam(t)
    ctx.save()
    cam.apply(ctx, 1.0, os_)
    draw_map(ctx, cam, z, t)
    draw_action(ctx, cam, z, t)
    ctx.restore()
    draw_overlay(ctx, cam, z, t, os_)
    c0, _ = make_cam(t - 1 / 60)
    c1, _ = make_cam(t + 1 / 60)
    bx, by = (c1.cx - c0.cx) * z * 0.55, (c1.cy - c0.cy) * z * 0.55
    look = dict(dark=0.0, desat=0.02, bloom=0.3, vig=0.5, grain=0.03, tint=(1.0, 1.0, 1.03))
    if abs(bx) > 22 or abs(by) > 22:
        look['blur'] = (min(abs(bx), 420), min(abs(by), 240))
        k = min(1.0, math.hypot(bx, by) / 260)
        ctx.save()
        ctx.identity_matrix()
        ctx.translate(540 * os_, 960 * os_)
        ctx.rotate(math.atan2(by, bx))
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
    ks = sm(t, E['frozen'] - 0.2, E['frozen'] + 0.6) * (1 - sm(t, E['america'] - 0.1, E['america'] + 0.3))
    kd = sm(t, E['estimated'], E['seventy'] + 0.2)
    look['tint'] = (1.0 - 0.06 * ks, 1.0, 1.03 + 0.05 * ks)
    look['desat'] = 0.02 + 0.2 * ks + 0.35 * kd
    if t > E['voice_end'] + 0.7:
        look['dark'] = 0.0
    return look
