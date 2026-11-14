"""Shared drawing for the WW2 Shorts: colours, the map grid, spreading fronts, arrows, vehicles, aircraft, bursts,
markers and counters. (Extracted from part1.py, which keeps its own copies.)"""
import math

import cairo
import numpy as np

from core import W, H, Camera, clamp, smooth, smoother, ease_out, ease_in, ramp, hash01, vnoise, fnoise, set_c, \
    path_smooth, path_poly, soft_glow
import mapdata as M
import text as TX


def hexc(h, a=1.0):
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


SEA, SEA2 = hexc('0a111e'), hexc('0e1828')
LAND, EURO, SOV = hexc('172030'), hexc('232d40'), hexc('2c3038')
RED, RED_L, RED_D, STRIPE = hexc('c81f2d'), hexc('ff5148'), hexc('6f1620'), hexc('a82430')
BLUE, BLUE_L = hexc('2b6fd6'), hexc('6bb0ff')
WHITE, YELLOW, INK = hexc('f4f7fb'), hexc('ffd23f'), hexc('05080f')
ARROW = hexc('ff4136')
EUROPE = [n for n in M.R if n not in ('LAND', 'OCC_EAST', 'OCC_42', 'JPN', 'JAP_EMPIRE', 'HAWAII')]


def sm(t, a, b):
    return smooth(ramp(t, a, b))


def visible(cam, z, name, margin=60):
    x0, y0, x1, y1 = M.BBOX[name]
    hw, hh = (W / 2 + margin) / z, (H / 2 + margin) / z
    return not (x1 < cam.cx - hw or x0 > cam.cx + hw or y1 < cam.cy - hh or y0 > cam.cy + hh)


def scr(cam, lon, lat):
    return cam.world_to_screen(*M.P(lon, lat))


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
