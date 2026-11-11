"""The scenes of "Rome Never Fell in 476". Every scene function draws one frame at time t into a cairo context
(sized W*os_ x H*os_) and returns a 'look' for the finishing pass. Times come from scene_timing.json, which is
built from the measured narration, so each stamp, label, arrow and tear lands on its word.

Scenes: hook (the legionary's eyes, the 476 stamp, the slash, the crack) -> scale (the ink flood of the empire,
labels, marching legions, three continents, one in four people) -> trajan (AD 117: the bust, the glowing border,
the roads racing like veins, the crack) -> clash (civil war) -> plague (the shadow) -> divide (invaders on every
border, the tear of 395, the West burning in 476, Constantinople, the counter to 1453, the ink dissolve) ->
end (back to the eyes; the last frame is the first frame, so the Short loops).
"""
import math

import cairo
import numpy as np

from core import W, H, EV, TIMING, Camera, clamp, smooth, smoother, ease_out, ease_in, ramp, keys, hash01, vnoise, \
    fnoise, set_c, path_smooth, path_poly, ink_line, taper_stroke, soft_glow, ellipse_pts, hatch_lines
import figs
from figs import C, P, fillp, strokep
import mapdata as M
import text as TX

CUT = TIMING['cuts']
SC = {s['key']: s for s in TIMING['scenes']}

LAND = figs.hexc('eadbb6')
LAND2 = figs.hexc('dcc89c')
SEA = figs.hexc('c9c3a8')
SEA2 = figs.hexc('b3ad92')
ASH = figs.hexc('2e2723')
ASH2 = figs.hexc('4a3f37')


# ----------------------------------------------------------------------------------------------
# Map drawing (world = map units, see mapdata)
# ----------------------------------------------------------------------------------------------
def rings_path(ctx, rings):
    for poly in rings:
        for r in poly:
            ctx.move_to(float(r[0, 0]), float(r[0, 1]))
            for p in r[1:]:
                ctx.line_to(float(p[0]), float(p[1]))
            ctx.close_path()


def fill_rings(ctx, rings, col, alpha=None):
    ctx.new_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    rings_path(ctx, rings)
    set_c(ctx, col, alpha)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


def stroke_rings(ctx, rings, col, lw, alpha=None):
    ctx.new_path()
    rings_path(ctx, rings)
    set_c(ctx, col, alpha)
    ctx.set_line_width(lw)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def clip_rings(ctx, rings):
    ctx.new_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    rings_path(ctx, rings)
    ctx.clip()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


def map_base(ctx, cam, t, z):
    """Parchment sea with engraved water lines, coast ripples, graticule, land and an inked coastline."""
    d = M.data()
    px = 1.0 / z                       # one output pixel (at 1080 width) in world units
    set_c(ctx, SEA)
    ctx.paint()
    # engraved horizontal water lines (screen-locked spacing would swim; these are world lines)
    x0, y0 = cam.cx - 700 / z, cam.cy - 1100 / z
    x1, y1 = cam.cx + 700 / z, cam.cy + 1100 / z
    sp = max(7.0, 9 * px)
    set_c(ctx, SEA2, 0.55)
    ctx.set_line_width(1.1 * px)
    yy = math.floor(y0 / sp) * sp
    while yy < y1:
        ctx.move_to(x0, yy)
        ctx.line_to(x1, yy)
        yy += sp
    ctx.stroke()
    # graticule every 10 degrees
    set_c(ctx, C['ink'], 0.12)
    ctx.set_line_width(1.2 * px)
    for lon in range(-20, 61, 10):
        a = M.P(lon, 70)
        b = M.P(lon, 10)
        ctx.move_to(*a)
        ctx.line_to(*b)
    for lat in range(10, 71, 10):
        a = M.P(-30, lat)
        b = M.P(70, lat)
        ctx.move_to(*a)
        ctx.line_to(*b)
    ctx.stroke()
    # coast ripples: wide soft strokes of the land outline, the way old maps shade the shore
    for w_, a in ((26, 0.22), (14, 0.3)):
        stroke_rings(ctx, d['land'], SEA2, w_ * px, a)
    stroke_rings(ctx, d['land'], LAND, 6 * px, 0.6)
    fill_rings(ctx, d['land'], LAND)
    stroke_rings(ctx, d['land'], C['ink'], 2.0 * px, 0.85)


def empire_fill(ctx, rings, col, z, hatch=0.18, border=None, border_w=3.0):
    px = 1.0 / z
    fill_rings(ctx, rings, col)
    if hatch > 0:
        ctx.save()
        clip_rings(ctx, rings)
        set_c(ctx, C['ink'], hatch)
        ctx.set_line_width(1.3 * px)
        bx = [r[:, 0] for poly in rings for r in poly]
        by = [r[:, 1] for poly in rings for r in poly]
        xa, xb = min(a.min() for a in bx), max(a.max() for a in bx)
        ya, yb = min(a.min() for a in by), max(a.max() for a in by)
        s = max(6.0, 8 * px)
        k = xa - (yb - ya)
        while k < xb:
            ctx.move_to(k, yb)
            ctx.line_to(k + (yb - ya), ya)
            k += s
        ctx.stroke()
        ctx.restore()
    stroke_rings(ctx, rings, border or C['red_d'], border_w * px, 0.95)


def blob_path(ctx, cx, cy, R, seed, t=0.0, wob=0.28, n=72, new=True):
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        r = R * (1 + wob * fnoise(math.cos(a) * 1.7 + 3.3 + seed, seed, 3) + wob * 0.5 * fnoise(math.sin(a) * 2.9 + t * 0.6, seed + 9, 2))
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    if new:
        ctx.new_path()
    path_smooth(ctx, np.array(pts), True, 0.5)


_ROADC = None


def roads_cum():
    global _ROADC
    if _ROADC is None:
        out = []
        for r in M.data()['roads']:
            p = r['pts']
            seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
            out.append((p, np.concatenate([[0], np.cumsum(seg)]), r['d'], r['len']))
        _ROADC = out
    return _ROADC


def draw_roads(ctx, front, z, glow=1.0):
    """Gold roads racing out from Rome: a road is drawn as far as the front (distance from Rome + length) has reached."""
    px = 1.0 / z
    paths = []
    for p, cum, d0, L in roads_cum():
        f = front - d0
        if f <= 0:
            continue
        if f >= L:
            paths.append(p)
        else:
            k = int(np.searchsorted(cum, f))
            k = max(1, min(k, len(p) - 1))
            u = (f - cum[k - 1]) / max(cum[k] - cum[k - 1], 1e-6)
            paths.append(np.vstack([p[:k], p[k - 1] + (p[k] - p[k - 1]) * u]))
    for lw, col, a in ((7.0, C['gold_l'], 0.18 * glow), (3.2, C['gold'], 0.9), (1.2, figs.hexc('fff1c4'), 0.8)):
        ctx.new_path()
        for p in paths:
            ctx.move_to(float(p[0, 0]), float(p[0, 1]))
            for q in p[1:]:
                ctx.line_to(float(q[0]), float(q[1]))
        set_c(ctx, col, a)
        ctx.set_line_width(lw * px)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()


def map_cam(lon, lat, z, shake=(0.0, 0.0)):
    x, y = M.P(lon, lat)
    return Camera(x + shake[0] / z, y + shake[1] / z, z, anchor=(0.0, 0.0))


def shake_at(t, t0, amp=14.0, dur=0.35, seed=1):
    u = (t - t0) / dur
    if u < 0 or u > 1:
        return 0.0, 0.0
    k = (1 - u) ** 2 * amp
    return k * vnoise(t * 40, seed), k * vnoise(t * 40, seed + 5)


def screen(cam, lon, lat):
    return cam.world_to_screen(*M.P(lon, lat))


def city_dot(ctx, x, y, os_, col=None, r=12):
    soft_glow(ctx, x * os_, y * os_, r * 3.2 * os_, C['gold_l'], 0.6)
    set_c(ctx, C['ink'])
    ctx.arc(x * os_, y * os_, r * os_, 0, 2 * math.pi)
    ctx.fill()
    set_c(ctx, col or C['gold_l'])
    ctx.arc(x * os_, y * os_, r * 0.6 * os_, 0, 2 * math.pi)
    ctx.fill()


# ----------------------------------------------------------------------------------------------
# Scene 1 and 7: the legionary (with the stamp, the slash and the crack in scene 1)
# ----------------------------------------------------------------------------------------------
EYE_C = (540.0, 905.0)
Z_ECU = 1.55          # extreme close-up of the eyes: the first and the last frame
IMPACT = (540.0, 640.0)


def face_cam(t, z, shake=(0.0, 0.0)):
    # zoom about the eyes, which sit a little above the centre of the frame
    return Camera(EYE_C[0] + shake[0], EYE_C[1] + 120 / z + shake[1], z, anchor=(0, 0))


def draw_face(ctx, cam, os_, t, blink=0.0, squint=0.0, look=(0.0, 0.0)):
    ctx.save()
    cam.apply(ctx, 1.0, os_)
    figs.legionary_face(ctx, t, blink, squint, look)
    ctx.restore()
    ctx.save()
    ctx.scale(os_, os_)
    figs.embers(ctx, t, 50, 3, 0.9)
    ctx.restore()


def blink_at(t, t0, dur=0.16):
    u = (t - t0) / dur
    return 0.0 if u < 0 or u > 1 else math.sin(u * math.pi)


_STAMP = None


def stamp_surface(os_):
    """'476 AD' in a red double-ruled stamp, distressed like ink that did not fully take."""
    global _STAMP
    if _STAMP is not None and _STAMP[0] == os_:
        return _STAMP[1]
    from PIL import Image, ImageDraw
    from scipy import ndimage
    f = TX.font('cinzel', int(176 * os_))
    d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
    b = d0.textbbox((0, 0), '476 AD', font=f)
    tw, th = b[2] - b[0], b[3] - b[1]
    m = int(54 * os_)
    w, h = tw + 2 * m + 20, th + 2 * m + 20
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = TX.RED + (255,)
    d.rectangle([10, 10, w - 10, h - 10], outline=col, width=max(3, int(12 * os_)))
    d.rectangle([10 + int(22 * os_), 10 + int(22 * os_), w - 10 - int(22 * os_), h - 10 - int(22 * os_)], outline=col, width=max(2, int(4 * os_)))
    d.text(((w - tw) // 2 - b[0], (h - th) // 2 - b[1]), '476 AD', font=f, fill=col)
    a = np.asarray(im, np.float32) / 255.0
    rng = np.random.default_rng(476)
    n = ndimage.gaussian_filter(rng.random((h, w)).astype(np.float32), 2.0 * os_ + 0.5)
    n = (n - n.min()) / (n.max() - n.min() + 1e-6)
    a[..., 3] *= np.clip((n - 0.16) * 4.5, 0.2, 1.0)
    s = TX.rgba_to_surface(a)
    _STAMP = (os_, s)
    return s


_SHARDS = None


def shards():
    """The stone crack network: Voronoi cells around the impact point (denser near it). Their edges are the
    cracks drawn on the hook; the cells are the shards that fly away in the shatter into the map."""
    global _SHARDS
    if _SHARDS is None:
        from scipy.spatial import Voronoi
        from shapely.geometry import Polygon, box
        rng = np.random.default_rng(11)
        pts = []
        for i in range(70):
            r = 1300 * rng.random() ** 1.7 + 20
            a = rng.uniform(0, 2 * math.pi)
            pts.append((IMPACT[0] + math.cos(a) * r * 0.8, IMPACT[1] + math.sin(a) * r))
        pts += [(-2000, -2000), (3000, -2000), (-2000, 4000), (3000, 4000)]
        vor = Voronoi(np.array(pts))
        frame = box(-40, -40, W + 40, H + 40)
        cells = []
        for i, reg in enumerate(vor.point_region[:70]):
            rv = vor.regions[reg]
            if -1 in rv or len(rv) < 3:
                continue
            poly = Polygon(vor.vertices[rv]).intersection(frame)
            if poly.is_empty or poly.area < 50:
                continue
            c = np.asarray(poly.exterior.coords)
            cells.append(c)
        edges = []
        for (a, b) in vor.ridge_vertices:
            if a < 0 or b < 0:
                continue
            p, q = vor.vertices[a], vor.vertices[b]
            mid = (p + q) / 2
            if -60 < mid[0] < W + 60 and -60 < mid[1] < H + 60:
                edges.append((p, q, float(np.hypot(*(mid - np.array(IMPACT))))))
        _SHARDS = (cells, edges)
    return _SHARDS


def draw_cracks(ctx, os_, R):
    """Cracks spread out from the impact; R is the reach (frame units)."""
    _, edges = shards()
    ctx.save()
    ctx.scale(os_, os_)
    for lw, col, off in ((9, (0, 0, 0, 0.75), (0, 0)), (3.5, C['ink'], (0, 0)), (2.0, (1, 0.93, 0.8, 0.55), (2.5, 2.0))):
        ctx.new_path()
        for p, q, dist in edges:
            if dist > R:
                continue
            # jagged: a midpoint kink
            m = (p + q) / 2 + np.array([vnoise(dist * 0.05, 3), vnoise(dist * 0.05, 7)]) * 18
            ctx.move_to(p[0] + off[0], p[1] + off[1])
            ctx.line_to(m[0] + off[0], m[1] + off[1])
            ctx.line_to(q[0] + off[0], q[1] + off[1])
        set_c(ctx, col)
        ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_MITER)
        ctx.stroke()
    ctx.restore()


def scene_hook(ctx, t, os_):
    ts, tw = EV['stamp'], EV['slash']
    sh = shake_at(t, ts, 22, 0.35, 1)
    sh2 = shake_at(t, tw, 30, 0.45, 2)
    z = Z_ECU + 0.12 * smooth(t / CUT['scale'])
    cam = face_cam(t, z, (sh[0] + sh2[0], sh[1] + sh2[1]))
    squint = smooth(ramp(t, tw - 0.1, tw + 0.15))
    draw_face(ctx, cam, os_, t, blink=blink_at(t, 2.05), squint=squint)
    # the stamp slams down on '476'
    if t >= ts:
        u = clamp((t - ts) / 0.13)
        s = stamp_surface(os_)
        sc = (1.0 + 0.8 * (1 - u) ** 2) * 0.92
        ctx.save()
        ctx.translate(IMPACT[0] * os_, IMPACT[1] * os_)
        ctx.rotate(-0.07)
        ctx.scale(sc, sc)
        ctx.set_source_surface(s, -s.get_width() / 2, -s.get_height() / 2)
        ctx.paint_with_alpha(min(1.0, u * 1.6))
        ctx.restore()
        if t - ts < 0.18:
            ctx.save()
            ctx.scale(os_, os_)
            soft_glow(ctx, IMPACT[0], IMPACT[1], 520, (1, 0.85, 0.7, 1), 0.35 * (1 - (t - ts) / 0.18))
            ctx.restore()
    # the slash: two thick red brush strokes on 'wrong'
    if t >= tw - 0.02:
        ctx.save()
        ctx.scale(os_, os_)
        for k, (a, b) in enumerate((((150, 420), (930, 860)), ((930, 410), (150, 870)))):
            u = clamp((t - tw - k * 0.07) / 0.085)
            if u <= 0:
                continue
            a, b = np.array(a, float), np.array(b, float)
            e = a + (b - a) * ease_out(u)
            mid = (a + e) / 2 + np.array([0, -18])
            taper_stroke(ctx, P(a, mid, e), 26, 70 * (0.4 + 0.6 * u), (0, 0, 0, 1), alpha=0.35)
            taper_stroke(ctx, P(a, mid, e) - np.array([4, 6]), 22, 64 * (0.4 + 0.6 * u), C['red'])
            taper_stroke(ctx, P(a + (e - a) * 0.1, mid, e) - np.array([10, 14]), 3, 10, C['red_l'], alpha=0.8)
            if u >= 1:
                for j in range(9):
                    sx = b[0] + (hash01(j, k) - 0.5) * 120
                    sy = b[1] + (hash01(j, k + 3) - 0.5) * 90
                    set_c(ctx, C['red'])
                    ctx.arc(sx, sy, 3 + 9 * hash01(j, k + 5), 0, 2 * math.pi)
                    ctx.fill()
        # white flash of the blow
        if 0 <= t - tw < 0.12:
            set_c(ctx, (1, 0.96, 0.9, 1), 0.45 * (1 - (t - tw) / 0.12))
            ctx.paint()
        ctx.restore()
    # the stone cracks spread from the blow
    if t >= tw + 0.05:
        R = 2400 * ease_out(clamp((t - tw - 0.05) / 0.32))
        draw_cracks(ctx, os_, R)
    return dict(dark=0.12, paper=0.35, desat=0.05, tint=(1.04, 0.97, 0.9), vig=0.55)


def scene_end(ctx, t, os_):
    a, b = SC['end']['start'], TIMING['duration']
    # the camera settles back to the opening framing, so the last frame matches the first
    z = keys(t, [(a, Z_ECU + 0.07), (b, Z_ECU)], smoother)
    cam = face_cam(t, z)
    draw_face(ctx, cam, os_, t, blink=blink_at(t, EV['fall'] + 0.65), look=(0.0, 0.0))
    return dict(dark=0.12, paper=0.35, desat=0.05, tint=(1.04, 0.97, 0.9), vig=0.55)


# ----------------------------------------------------------------------------------------------
# Scene 2: the scale
# ----------------------------------------------------------------------------------------------
LIT = set(sorted(range(40), key=lambda i: hash01(i, 77))[:10])     # exactly 10 of 40, scattered
LABELS_S2 = [('ROME', 'rome', (12.48, 41.89), (0, -60)), ('HISPANIA', 'hispania', (-4.2, 40.0), (0, 0)),
             ('BRITAIN', 'britain', (-1.8, 52.6), (0, 0)), ('EGYPT', 'egypt', (29.5, 28.8), (0, 0))]
MARCH = [((10.0, 43.5), (-3.5, 40.5)), ((11.0, 44.5), (1.0, 48.5)), ((15.5, 41.0), (23.0, 41.5)), ((16.0, 39.5), (35.5, 36.5)),
         ((11.0, 37.0), (8.0, 34.0))]


def scene_scale(ctx, t, os_):
    a = SC['scale']['start']
    rome = M.PLACES['rome']
    # a fast pull-back from Rome to the whole empire, then a slow drift
    zz = keys(t, [(a - 0.2, 3.6), (a + 2.3, 0.8), (SC['scale']['end'], 0.78)], smoother)
    lon = keys(t, [(a - 0.2, rome[0]), (a + 2.3, 16.5), (SC['scale']['end'], 17.0)], smoother)
    lat = keys(t, [(a - 0.2, rome[1]), (a + 2.3, 36.2), (SC['scale']['end'], 36.0)], smoother)
    cam = map_cam(lon, lat, zz)
    ctx.save()
    cam.apply(ctx, 1.0, os_)
    map_base(ctx, cam, t, zz)
    # the ink flood: the empire spreads out from Rome like spilled ink
    R = 1150 * ease_in(clamp((t - a - 0.05) / 2.6)) ** 0.75
    rx, ry = M.P(*rome)
    d = M.data()
    if R > 1:
        ctx.save()
        blob_path(ctx, rx, ry, R, 5, t)
        ctx.clip()
        empire_fill(ctx, d['e117'], C['red'], zz, hatch=0.16)
        ctx.restore()
        if R < 1150:
            ctx.save()
            clip_rings(ctx, d['e117'])
            blob_path(ctx, rx, ry, R, 5, t)
            set_c(ctx, C['red_d'], 0.8)
            ctx.set_line_width(9 / zz)
            ctx.stroke()
            ctx.restore()
    # legions marching out
    for i, (p0, p1) in enumerate(MARCH):
        tt = EV['rome'] + 0.1 + i * 0.12
        u = clamp((t - tt) / 2.4)
        fade_l = 1 - smooth(ramp(t, EV['continents'], EV['continents'] + 0.5))
        if u <= 0 or fade_l <= 0:
            continue
        a0, a1 = np.array(M.P(*p0)), np.array(M.P(*p1))
        for k in range(3):
            uu = clamp(ease_out(u) - k * 0.11)
            if uu <= 0.04:
                continue
            pos = a0 + (a1 - a0) * uu
            figs.legion_icon(ctx, pos[0], pos[1], 1.9 / zz, t, i * 3 + k, col=C['gold'])
    ctx.restore()
    # Rome, and the labels popping in on their words (screen-space, never smaller than 80 px)
    sx, sy = screen(cam, *rome)
    city_dot(ctx, sx, sy, os_, r=13)
    for txt, ev, (lo, la), off in LABELS_S2:
        al, s = TX.pop(t, EV[ev])
        if al <= 0:
            continue
        x, y = screen(cam, lo, la)
        x = min(max(x + off[0], 230), 850)
        TX.paint_label(ctx, txt, x, y + off[1], 84, os_, TX.WHITE, al, s)
    # three continents
    tc = EV['continents']
    if t >= tc - 0.05:
        for k, (txt, lo, la) in enumerate((('EUROPE', 8.0, 48.5), ('AFRICA', 5.0, 30.5), ('ASIA', 38.0, 40.0))):
            al, s = TX.pop(t, tc + k * 0.12)
            x, y = screen(cam, lo, la)
            x = min(max(x, 200), 880)
            TX.paint_label(ctx, txt, x, y, 64, os_, TX.GOLD, al * (1 - smooth(ramp(t, EV['crowd'] - 0.2, EV['crowd'] + 0.1))), s, fn='fell')
    # one in four: a crowd, every fourth figure lights up red
    tcw, tq = EV['crowd'], EV['quarter']
    if t >= tcw - 0.1:
        veil = smooth(ramp(t, tcw - 0.1, tcw + 0.2))
        ctx.save()
        ctx.scale(os_, os_)
        set_c(ctx, C['parch'], 0.72 * veil)
        ctx.paint()
        cols, rows = 8, 5
        for r in range(rows):
            for c_ in range(cols):
                i = r * cols + c_
                x = 540 + (c_ - (cols - 1) / 2) * 112 + (r % 2) * 18 - 9
                y = 640 + r * 104
                al, s = TX.pop(t, tcw + (i % 9) * 0.025 + r * 0.03, 0.22)
                if al <= 0:
                    continue
                lit = i in LIT
                ul = clamp((t - tq - (i // 4) * 0.035) / 0.12) if lit else 0.0
                col = tuple(np.array(C['parch2']) * (1 - ul) + np.array(C['red']) * ul)
                ctx.save()
                ctx.translate(x, y)
                ctx.scale(s, s)
                if ul > 0:
                    soft_glow(ctx, 0, -6, 60, C['red_l'], 0.4 * ul)
                figs.person(ctx, 0, 0, 2.3, col)
                ctx.restore()
        ctx.restore()
    return dict(dark=0.0, paper=0.6, desat=0.06, tint=(1.03, 0.99, 0.92), vig=0.42)


# ----------------------------------------------------------------------------------------------
# Scene 3: AD 117, Trajan, the roads, the crack
# ----------------------------------------------------------------------------------------------
def map_crack(ctx, cam, os_, t, t0, seed=4):
    """A crack splitting the map from top to bottom near the line the empire will later divide along."""
    u = clamp((t - t0) / 0.3)
    if u <= 0:
        return
    sl = M.data()['split']
    ctx.save()
    ctx.scale(os_, os_)
    pts = []
    for k in range(90):
        f = k / 89
        y = -40 + f * 2000
        if f > u:
            break
        # follow the split line's screen x at this height, with a jagged walk
        wy = cam.cy + (y - H / 2) / cam.z
        j = int(np.argmin(np.abs(sl[:, 1] - wy)))
        x, _ = cam.world_to_screen(sl[j, 0], wy)
        x += 55 * fnoise(f * 7, seed, 3) + 22 * vnoise(f * 47, seed + 2) + 10 * vnoise(f * 130, seed + 4)
        pts.append((x, y))
    if len(pts) > 1:
        p = np.array(pts)
        for lw, col, off in ((14, (0, 0, 0, 0.7), 0), (5, C['ink'], 0), (2.2, (1, 0.94, 0.82, 0.6), 3)):
            ctx.new_path()
            path_poly(ctx, p + off, False)
            set_c(ctx, col)
            ctx.set_line_width(lw)
            ctx.set_line_join(cairo.LINE_JOIN_MITER)
            ctx.stroke()
        # side branches
        for b in range(7):
            k = int(hash01(b, seed) * (len(p) - 1))
            q0 = p[k]
            ang = (hash01(b, seed + 1) - 0.5) * 2.2 + (0 if b % 2 else math.pi)
            L = 60 + 140 * hash01(b, seed + 2)
            q1 = q0 + np.array([math.cos(ang), math.sin(ang)]) * L * u
            ink_line(ctx, P(q0, (q0 + q1) / 2 + np.array([8, -6]), q1), 3.5, C['ink'], smooth_path=False)
    ctx.restore()


def scene_trajan(ctx, t, os_):
    a, b = SC['trajan']['start'], SC['trajan']['end']
    sh = shake_at(t, EV['y117'], 16, 0.3, 4)
    sh2 = shake_at(t, EV['cracked'], 26, 0.45, 5)
    zz = keys(t, [(a, 0.82), (EV['ever'], 1.0), (b, 1.03)], smooth)
    lon = keys(t, [(a, 14.0), (EV['ever'], 16.5), (b, 16.8)], smooth)
    lat = keys(t, [(a, 38.4), (EV['ever'], 38.6), (b, 38.6)], smooth)
    cam = map_cam(lon, lat, zz, (sh[0] + sh2[0], sh[1] + sh2[1]))
    d = M.data()
    cracked = smooth(ramp(t, EV['cracked'], EV['cracked'] + 0.5))
    ctx.save()
    cam.apply(ctx, 1.0, os_)
    map_base(ctx, cam, t, zz)
    red = tuple(np.array(C['red']) * (1 - 0.25 * cracked) + np.array(C['red_d']) * 0.25 * cracked)
    empire_fill(ctx, d['e117'], red, zz, hatch=0.14)
    # the border glows and pulses
    pulse = 0.5 + 0.5 * math.sin((t - a) * 6.5)
    for lw, al in ((26, 0.10), (14, 0.18), (6, 0.5)):
        stroke_rings(ctx, d['e117'], C['red_l'], lw / zz, al * (0.6 + 0.4 * pulse) * (1 - 0.6 * cracked))
    stroke_rings(ctx, d['e117'], C['gold_l'], 2.2 / zz, (0.5 + 0.5 * pulse) * (1 - cracked))
    # the roads light up like veins, racing out from Rome
    front = 2100 * smooth(ramp(t, EV['y117'] + 0.15, EV['ever'] + 0.3))
    draw_roads(ctx, front, zz, glow=1 - 0.7 * cracked)
    ctx.restore()
    rx, ry = screen(cam, *M.PLACES['rome'])
    city_dot(ctx, rx, ry, os_, r=12)
    # Trajan slides in from the left, gold light behind him; he leaves before the crack
    xin = keys(t, [(a, -420.0), (a + 0.55, 250.0), (EV['ever'] + 0.35, 262.0), (EV['ever'] + 0.75, -460.0)], smoother)
    if xin > -440:
        ctx.save()
        ctx.scale(os_, os_)
        figs.trajan_bust(ctx, xin, 1335, 0.78, t, glow=0.8 + 0.2 * math.sin(t * 3))
        ctx.restore()
    map_crack(ctx, cam, os_, t, EV['cracked'])
    return dict(dark=0.08 * cracked, paper=0.6, desat=0.05, tint=(1.04, 0.98, 0.9), vig=0.45 + 0.15 * cracked)


# ----------------------------------------------------------------------------------------------
# Scene 4: civil wars
# ----------------------------------------------------------------------------------------------
def scene_clash(ctx, t, os_):
    a, b = SC['clash']['start'], SC['clash']['end']
    tw = EV['wars']
    sh = shake_at(t, tw, 30, 0.4, 6)
    ctx.save()
    ctx.scale(os_, os_)
    ctx.translate(sh[0], sh[1])
    # blood-orange sky and smoke
    g = figs.lgrad(ctx, 0, 0, 0, H, [(0, figs.hexc('2a0d08')), (0.45, figs.hexc('8a2a10')), (0.62, figs.hexc('d0661e')), (0.7, figs.hexc('5a1a0c')), (1, figs.hexc('140a07'))])
    ctx.set_source(g)
    ctx.paint()
    soft_glow(ctx, 540, 1180, 700, figs.hexc('ffb050'), 0.45)
    for i in range(9):
        x = (hash01(i, 2) * 1400 - 160 + (t - a) * 60 * (0.5 + hash01(i, 3)))
        y = 700 + hash01(i, 4) * 600
        soft_glow(ctx, x, y, 260 + 200 * hash01(i, 5), (0.1, 0.05, 0.04, 1), 0.45)
    # ground
    fillp(ctx, P((0, 1330), (300, 1312), (700, 1326), (1080, 1308), (1080, 1920), (0, 1920)), C['ink'])
    # the two legionaries lunge in and their swords meet on 'wars'
    u = smoother(ramp(t, a, tw))
    gap = 300 * (1 - u) + 40
    rec = smooth(ramp(t, tw, tw + 0.5))
    sw = 0.55 + 0.6 * (1 - u) - 0.25 * rec
    s = 0.92 + 0.05 * (t - a)
    figs.legionary_silhouette(ctx, 540 - gap - 330 * s, 1330, s, 1, lunge=u, sword=sw, crest=C['red'])
    figs.legionary_silhouette(ctx, 540 + gap + 330 * s, 1330, s, -1, lunge=u, sword=sw, crest=C['red'])
    # sparks at the clash
    if t >= tw:
        k = t - tw
        cx, cy = 540, 1330 - 760 * s
        soft_glow(ctx, cx, cy, 260 * clamp(1 - k / 0.5), (1, 0.9, 0.6, 1), 0.9)
        for j in range(26):
            ang = hash01(j, 7) * 2 * math.pi
            v = 500 + 900 * hash01(j, 8)
            x = cx + math.cos(ang) * v * k
            y = cy + math.sin(ang) * v * k + 900 * k * k
            if k > 0.55:
                continue
            set_c(ctx, figs.hexc('ffe9a8'), 1 - k / 0.55)
            ctx.set_line_width(3)
            ctx.move_to(x, y)
            ctx.line_to(x - math.cos(ang) * 30, y - math.sin(ang) * 30)
            ctx.stroke()
        if k < 0.08:
            set_c(ctx, (1, 0.97, 0.9, 1), 0.6 * (1 - k / 0.08))
            ctx.paint()
    figs.embers(ctx, t, 40, 8, 1.0)
    ctx.restore()
    return dict(dark=0.1, paper=0.4, desat=0.02, tint=(1.06, 0.96, 0.86), vig=0.6)


# ----------------------------------------------------------------------------------------------
# Scene 5: plague
# ----------------------------------------------------------------------------------------------
PLAGUE_SRC = [(36.0, 33.0, 0.0), (30.5, 30.5, 0.08), (22.0, 38.5, 0.18), (12.5, 41.9, 0.26), (3.0, 46.0, 0.34), (-4.0, 40.0, 0.4)]


def scene_plague(ctx, t, os_):
    a, b = SC['plague']['start'], SC['plague']['end']
    zz = keys(t, [(a, 1.08), (b, 1.16)], smooth)
    cam = map_cam(keys(t, [(a, 20.0), (b, 18.0)], smooth), 39.0, zz)
    d = M.data()
    ctx.save()
    cam.apply(ctx, 1.0, os_)
    map_base(ctx, cam, t, zz)
    empire_fill(ctx, d['e117'], C['red_d'], zz, hatch=0.14)
    # a dark shadow spreads across the empire from the east
    ctx.save()
    clip_rings(ctx, d['e117'])
    for i, (lo, la, dt) in enumerate(PLAGUE_SRC):
        u = clamp((t - a - dt) / 0.7)
        if u <= 0:
            continue
        x, y = M.P(lo, la)
        for k, (rs, al) in enumerate(((1.0, 0.35), (0.75, 0.4), (0.5, 0.45))):
            blob_path(ctx, x, y, 420 * ease_out(u) * rs, 20 + i, t)
            set_c(ctx, figs.hexc('0f120c'), al)
            ctx.fill()
    ctx.restore()
    # specks
    for i in range(160):
        lo, la = -8 + hash01(i, 1) * 48, 27 + hash01(i, 2) * 25
        if t - a < hash01(i, 3) * 0.6:
            continue
        x, y = M.P(lo, la)
        set_c(ctx, C['ink'], 0.7)
        ctx.arc(x, y, (2.0 + 2.5 * hash01(i, 4)) / zz, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()
    return dict(dark=0.35, paper=0.6, desat=0.25, tint=(0.98, 1.0, 0.92), vig=0.7)


# ----------------------------------------------------------------------------------------------
# Scene 6: invaders, the split, the fall of the West, the East to 1453
# ----------------------------------------------------------------------------------------------
ARROWS = [((7.5, 54.5), (7.8, 50.0)), ((-3.0, 58.6), (-2.6, 55.3)), ((14.0, 52.5), (15.0, 48.4)), ((22.5, 50.0), (21.8, 45.3)),
          ((31.0, 49.5), (28.6, 45.4)), ((49.0, 41.0), (41.2, 38.6)), ((50.0, 33.0), (41.0, 34.4)), ((8.0, 23.0), (8.6, 30.6)),
          ((-9.0, 27.5), (-6.4, 33.3))]
WEST_C = (4.0, 44.0)


def tear_jag(sl, seed=7):
    """The split line with a fine paper-tear zigzag."""
    out = []
    for k in range(len(sl) - 1):
        p, q = sl[k], sl[k + 1]
        n = max(2, int(np.hypot(*(q - p)) / 6))
        for i in range(n):
            f = i / n
            x = p + (q - p) * f
            out.append((x[0] + 5 * vnoise((k * n + i) * 0.9, seed) + 2.5 * vnoise((k * n + i) * 3.1, seed + 1), x[1]))
    out.append(tuple(sl[-1]))
    return np.array(out)


_JAG = None


def jag():
    global _JAG
    if _JAG is None:
        _JAG = tear_jag(M.data()['split'])
    return _JAG


def half_clip(ctx, side):
    j = jag()
    far = -3000 if side < 0 else 3000
    pts = np.vstack([j, [[far, j[-1, 1]], [far, j[0, 1]]]])
    ctx.new_path()
    path_poly(ctx, pts, True)
    ctx.clip()


def draw_divide_content(ctx, cam, os_, t, zz, side):
    """Everything on the map for one half of the torn sheet (side -1 West, +1 East; 0 = whole sheet)."""
    d = M.data()
    map_base(ctx, cam, t, zz)
    tsp = EV['split']
    if side <= 0:
        # the West: red, then burning from its edges to ash
        burn_u = smooth(ramp(t, EV['in476'] + 0.1, EV['collapsed'] + 0.25))
        if burn_u < 1:
            ctx.save()
            if burn_u > 0:
                cx, cy = M.P(*WEST_C)
                blob_path(ctx, cx, cy, 1250 * (1 - burn_u) ** 1.2 + 1, 31, t * 2, wob=0.35)
                ctx.clip()
            empire_fill(ctx, d['west'] if t >= tsp else d['e395'], C['red'], zz, hatch=0.15)
            ctx.restore()
        if burn_u > 0:
            ctx.save()
            clip_rings(ctx, d['west'])
            # ash where the fire has passed
            ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            cx, cy = M.P(*WEST_C)
            ctx.new_path()
            ctx.rectangle(-3000, -3000, 6000, 6000)
            blob_path(ctx, cx, cy, 1250 * (1 - burn_u) ** 1.2 + 1, 31, t * 2, wob=0.35, new=False)
            ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            ctx.clip()
            ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
            set_c(ctx, ASH)
            ctx.paint()
            for i in range(220):
                x, y = M.P(-10 + hash01(i, 1) * 30, 30 + hash01(i, 2) * 26)
                set_c(ctx, ASH2, 0.8)
                ctx.arc(x, y, (2 + 5 * hash01(i, 3)) / zz, 0, 2 * math.pi)
                ctx.fill()
            ctx.restore()
            # the glowing fire front
            if burn_u < 1:
                ctx.save()
                clip_rings(ctx, d['west'])
                blob_path(ctx, cx, cy, 1250 * (1 - burn_u) ** 1.2 + 1, 31, t * 2, wob=0.35)
                for lw, col, al in ((30, C['ember'], 0.35), (14, figs.hexc('ffb347'), 0.7), (5, figs.hexc('fff0b0'), 0.9)):
                    set_c(ctx, col, al)
                    ctx.set_line_width(lw / zz)
                    ctx.stroke_preserve()
                ctx.new_path()
                ctx.restore()
    if side >= 0:
        # the East: red, recoloured purple and gold after the split; glows brighter as the West falls
        k = smooth(ramp(t, tsp + 0.15, tsp + 0.65)) if side > 0 or t >= tsp else 0.0
        col = tuple(np.array(C['red']) * (1 - k) + np.array(C['purple']) * k)
        dis = smooth(ramp(t, EV['y1453'] + 0.25, EV['y1453'] + 1.2))
        east = d['east'] if t >= tsp else d['e395']
        if dis < 1:
            ctx.save()
            ctx.push_group()
            empire_fill(ctx, east, col, zz, hatch=0.15, border=C['gold'] if k > 0.5 else C['red_d'], border_w=3.0 + 2 * k)
            glow = smooth(ramp(t, EV['but'], EV['but'] + 0.6)) * (1 - dis)
            if glow > 0 or k > 0:
                pulse = 0.5 + 0.5 * math.sin(t * 5)
                for lw, al in ((22, 0.12), (10, 0.25)):
                    stroke_rings(ctx, east, C['gold_l'], lw / zz, al * (0.4 * k + glow * (0.7 + 0.3 * pulse)))
            holes = []
            if dis > 0:
                # ink dissolve: holes open in the purple, merge and spread until it is gone
                for i in range(8):
                    x, y = M.P(21 + hash01(i, 41) * 18, 29 + hash01(i, 42) * 14)
                    r = 560 * ease_in(clamp(dis * 1.2 - hash01(i, 43) * 0.25)) + 0.5
                    pts = []
                    for m in range(56):
                        aa = m / 56 * 2 * math.pi
                        rr = r * (1 + 0.35 * fnoise(math.cos(aa) * 2.2 + i * 3.1, 50 + i, 3) + 0.12 * vnoise(m * 1.7, 60 + i))
                        pts.append((x + math.cos(aa) * rr, y + math.sin(aa) * rr))
                    holes.append(np.array(pts))
                ctx.set_operator(cairo.OPERATOR_DEST_OUT)
                for hp in holes:
                    ctx.new_path()
                    path_smooth(ctx, hp, True)
                    set_c(ctx, (0, 0, 0, 1))
                    ctx.fill()
                ctx.set_operator(cairo.OPERATOR_OVER)
            ctx.pop_group_to_source()
            ctx.paint()
            if holes:
                clip_rings(ctx, east)
                for hp in holes:
                    ctx.new_path()
                    path_smooth(ctx, hp, True)
                    set_c(ctx, C['ink'], 0.55 * (1 - dis))
                    ctx.set_line_width(5 / zz)
                    ctx.stroke()
            ctx.restore()


def scene_divide(ctx, t, os_):
    a, b = SC['divide']['start'], SC['divide']['end']
    tsp = EV['split']
    sh = shake_at(t, tsp, 18, 0.35, 8)
    sh2 = shake_at(t, EV['collapsed'], 24, 0.45, 9)
    sh3 = shake_at(t, EV['y1453'], 12, 0.3, 10)
    shx, shy = sh[0] + sh2[0] + sh3[0], sh[1] + sh2[1] + sh3[1]
    zz = keys(t, [(a, 0.86), (tsp, 0.84), (EV['in476'], 0.84), (EV['but'], 0.9), (EV['for'] + 0.1, 0.92), (EV['for'] + 1.2, 1.5),
                  (b, 1.56)], smoother)
    lon = keys(t, [(a, 16.0), (EV['but'], 16.5), (EV['for'] + 0.1, 19.0), (EV['for'] + 1.2, 29.5), (b, 30.0)], smoother)
    lat = keys(t, [(a, 38.6), (EV['but'], 38.6), (EV['for'] + 0.1, 38.4), (EV['for'] + 1.2, 35.0), (b, 35.0)], smoother)
    cam = map_cam(lon, lat, zz, (shx, shy))
    set_c(ctx, C['ink'])
    ctx.paint()
    # the tear: two halves of the sheet pull apart
    tu = ease_out(ramp(t, tsp, tsp + 0.42))
    gap = 26 * tu
    for side in (-1, 1):
        ctx.save()
        cam.apply(ctx, 1.0, os_)
        if t >= tsp:
            sl = M.data()['split']
            pivot = sl[len(sl) // 2]
            ctx.translate(side * gap, 0)
            ctx.translate(*pivot)
            ctx.rotate(side * 0.012 * tu)
            ctx.translate(-pivot[0], -pivot[1])
            half_clip(ctx, side)
            draw_divide_content(ctx, cam, os_, t, zz, side)
            # torn paper fibres along the edge
            j = jag()
            ctx.new_path()
            path_poly(ctx, j, False)
            set_c(ctx, figs.hexc('f6ecd6'), 0.95)
            ctx.set_line_width(7 / zz)
            ctx.stroke()
        else:
            if side > 0:
                ctx.restore()
                continue
            draw_divide_content(ctx, cam, os_, t, zz, 0)
        ctx.restore()
    # arrows from every border
    arrows_out = 1 - smooth(ramp(t, tsp - 0.25, tsp + 0.05))
    if arrows_out > 0:
        ctx.save()
        cam.apply(ctx, 1.0, os_)
        span = EV['border'] + 0.35 - (a + 0.1)
        for i, (p0, p1) in enumerate(ARROWS):
            t0 = a + 0.1 + i * span / len(ARROWS)
            u = clamp((t - t0) / 0.22)
            if u <= 0:
                continue
            A, B = np.array(M.P(*p0)), np.array(M.P(*p1))
            tip = A + (B - A) * ease_in(u)
            dvec = (B - A) / (np.linalg.norm(B - A) + 1e-6)
            nv = np.array([-dvec[1], dvec[0]])
            s = 1 / zz
            taper_stroke(ctx, P(A, (A + tip) / 2, tip - dvec * 40 * s), 6 * s, 26 * s, C['ink'], alpha=arrows_out)
            head = P(tip + dvec * 22 * s, tip - dvec * 58 * s + nv * 40 * s, tip - dvec * 38 * s, tip - dvec * 58 * s - nv * 40 * s)
            ctx.new_path()
            path_poly(ctx, head, True)
            set_c(ctx, C['ink'], arrows_out)
            ctx.fill()
            if u >= 1:
                k = clamp((t - t0 - 0.22) / 0.5)
                set_c(ctx, C['red_l'], 0.8 * (1 - k) * arrows_out)
                ctx.set_line_width(5 * s)
                ctx.arc(B[0], B[1], (14 + 60 * k) * s, 0, 2 * math.pi)
                ctx.stroke()
        ctx.restore()
    # labels: WEST and EAST on 'two'
    if t >= EV['two'] - 0.05:
        for txt, (lo, la), side, col in (('WEST', (2.0, 44.5), -1, TX.RED_L), ('EAST', (33.0, 38.5), 1, TX.PURPLE_L)):
            al, s = TX.pop(t, EV['two'] + (0.1 if side > 0 else 0))
            x, y = screen(cam, lo, la)
            x += side * gap * zz
            fade = 1 - smooth(ramp(t, EV['for'] + 0.1, EV['for'] + 0.6))
            if side < 0:
                fade *= 1 - 0.55 * smooth(ramp(t, EV['collapsed'], EV['collapsed'] + 0.4))
            else:
                fade *= 1 - smooth(ramp(t, EV['east'] - 0.1, EV['east'] + 0.25))
            x = min(max(x, 220), 860)
            TX.paint_label(ctx, txt, x, y, 96, os_, TX.WHITE if side < 0 else TX.GOLD, al * fade, s)
    # Constantinople rises on 'But the East'
    rise = smooth(ramp(t, EV['east'] - 0.05, EV['east'] + 0.6))
    if rise > 0:
        cx, cy = screen(cam, *M.PLACES['constantinople'])
        dis = smooth(ramp(t, EV['y1453'] + 0.25, EV['y1453'] + 1.2))
        ctx.save()
        ctx.scale(os_, os_)
        s = 1.0 * (zz / 0.9) ** 0.5
        ctx.push_group()
        figs.constantinople(ctx, cx + gap * zz, cy + 10, s, rise, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1 - dis)
        ctx.restore()
        al, sc = TX.pop(t, EV['east'] + 0.25)
        ly = cy + 95
        TX.paint_label(ctx, 'CONSTANTINOPLE', min(max(cx, 470), 610), ly, 80, os_, TX.GOLD, al * (1 - smooth(ramp(t, EV['for'] + 0.4, EV['for'] + 0.9))), sc)
    # the year counter: 476 -> 1453, landing on the word
    tf, ty = EV['for'], EV['y1453']
    if t >= tf:
        u = clamp((t - tf) / (ty - tf))
        e = 1 - (1 - u) ** 2.2
        year = int(round(476 + (1453 - 476) * e)) if u < 1 else 1453
        al = smooth(ramp(t, tf, tf + 0.2))
        punch = 1 + 0.25 * (1 - clamp((t - ty) / 0.25)) if t >= ty else 1.0
        draw_counter(ctx, os_, year, 540, 470, al, punch, frozen=t >= ty)
        if t >= ty:
            k = clamp((t - ty) / 0.8)
            ctx.save()
            ctx.scale(os_, os_)
            set_c(ctx, C['gold_l'], 0.7 * (1 - k))
            ctx.set_line_width(10 * (1 - k) + 2)
            ctx.arc(540, 470, 120 + 420 * ease_out(k), 0, 2 * math.pi)
            ctx.stroke()
            ctx.restore()
    dark = 0.0
    return dict(dark=dark, paper=0.6, desat=0.05, tint=(1.03, 0.98, 0.92), vig=0.45)


_DIG = {}


def digit_surface(ch, os_, frozen):
    key = (ch, os_, frozen)
    if key not in _DIG:
        _DIG[key] = TX.label_surface(ch, 250, TX.GOLD_L if frozen else TX.GOLD, os_, ow=10)
    return _DIG[key]


def draw_counter(ctx, os_, year, x, y, alpha, scale, frozen):
    s = str(year)
    adv = 150
    x0 = x - adv * (len(s) - 1) / 2
    ctx.save()
    ctx.scale(os_, os_)
    soft_glow(ctx, x, y, 420, C['gold_l'], 0.25 * alpha * (1.4 if frozen else 1.0))
    ctx.restore()
    for i, ch in enumerate(s):
        surf = digit_surface(ch, os_, frozen)
        ctx.save()
        ctx.translate((x + (x0 + i * adv - x) * scale) * os_, y * os_)
        ctx.scale(scale, scale)
        ctx.set_source_surface(surf, -surf.get_width() / 2, -surf.get_height() / 2)
        ctx.paint_with_alpha(alpha)
        ctx.restore()
