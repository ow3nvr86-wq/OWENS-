"""Modern flat 2D graphics for the September 11 Short: clean vector shapes with gradients and soft light,
no ink outlines, no paper. Sky, clouds, the Lower Manhattan skyline and the Twin Towers, the Hudson and a
ferry, architectural line drawings, smoke and dust, a map of the eastern United States, the Pentagon icon,
silhouette figures with rim light, emergency vehicles, the 9/11 Memorial pools, One World Trade Center, the
Tribute in Light and the channel mark."""
import math

import cairo
import numpy as np

from core import hash01, vnoise, clamp, smooth, ellipse_pts, path_poly, path_smooth


def hexc(h, a=1.0):
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


C = {
    'navy0': hexc('070d1a'), 'navy1': hexc('0c1628'), 'navy2': hexc('13233d'), 'navy3': hexc('1d3254'), 'navy4': hexc('2b4670'),
    'blue1': hexc('3d5f8f'), 'blue2': hexc('5f83b3'), 'blue3': hexc('8fb0d6'), 'blue4': hexc('bcd3ea'), 'sky_hz': hexc('dce8f2'),
    'grey1': hexc('2a2f37'), 'grey2': hexc('4a525e'), 'grey3': hexc('7a8494'), 'grey4': hexc('a9b2bf'), 'grey5': hexc('d3d8df'),
    'white': hexc('f4f6f9'), 'red': hexc('c8343a'), 'red2': hexc('e0524f'), 'redd': hexc('7d1f24'), 'warm': hexc('f1d2a6'),
    'bronze': hexc('4a3b2c'), 'bronze2': hexc('6d5840'), 'char': hexc('101215'), 'dust': hexc('b9ad9a'), 'dust2': hexc('8d8577'),
}


def mixc(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))


def setc(ctx, c, a=None):
    ctx.set_source_rgba(c[0], c[1], c[2], c[3] if a is None else a)


def fill(ctx, pts, col, smooth_=False):
    ctx.new_path()
    (path_smooth if smooth_ else path_poly)(ctx, np.asarray(pts, float), True)
    setc(ctx, col)
    ctx.fill()


def rect(ctx, x0, y0, x1, y1, col):
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    setc(ctx, col)
    ctx.fill()


def vgrad(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(0, y0, 0, y1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *c)
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.set_source(g)
    ctx.fill()


def glow(ctx, x, y, r, col, a=1.0):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], a)
    g.add_color_stop_rgba(0.4, col[0], col[1], col[2], a * 0.35)
    g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def line(ctx, pts, lw, col, dash=None, cap=cairo.LINE_CAP_ROUND):
    ctx.new_path()
    p = np.asarray(pts, float)
    ctx.move_to(*p[0])
    for q in p[1:]:
        ctx.line_to(*q)
    setc(ctx, col)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cap)
    if dash:
        ctx.set_dash(dash)
    ctx.stroke()
    ctx.set_dash([])


def text(ctx, x, y, size, txt, col, weight='bold', align='center', track=0.0):
    """Inter set with optional letter-spacing (track, in em)."""
    ctx.save()
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if weight == 'bold' else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    widths = [ctx.text_extents(ch)[4] for ch in txt]
    tw = sum(widths) + track * size * (len(txt) - 1)
    if align == 'center':
        x -= tw / 2
    elif align == 'right':
        x -= tw
    setc(ctx, col)
    for ch, w in zip(txt, widths):
        ctx.move_to(x, y)
        ctx.show_text(ch)
        x += w + track * size
    ctx.restore()
    return tw


# ----------------------------------------------------------------------------------------------
# Sky, clouds, water
# ----------------------------------------------------------------------------------------------
def sky(ctx, w, h, hz, mood=0.0, night=0.0):
    """A clear morning sky (mood 0), dimming to a dusty grey (mood 1); night blends to deep navy."""
    top = mixc(mixc(C['blue2'], C['grey2'], mood), C['navy0'], night)
    mid = mixc(mixc(C['blue3'], C['grey3'], mood), C['navy2'], night)
    low = mixc(mixc(C['sky_hz'], C['dust'], mood), C['navy3'], night)
    vgrad(ctx, -200, -400, w + 200, hz + 40, [(0, top), (0.6, mid), (1, low)])


def cloud(ctx, x, y, w, h, col, seed=0, a=1.0):
    rng = np.random.default_rng(seed)
    n = 6
    for k in range(n):
        u = k / (n - 1)
        cx = x - w / 2 + w * u + rng.uniform(-0.05, 0.05) * w
        r = h * (0.45 + 0.55 * math.sin(math.pi * u)) * rng.uniform(0.7, 1.0)
        g = cairo.RadialGradient(cx, y, 0, cx, y, r)
        g.add_color_stop_rgba(0, col[0], col[1], col[2], 0.55 * a)
        g.add_color_stop_rgba(0.7, col[0], col[1], col[2], 0.3 * a)
        g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
        ctx.set_source(g)
        ctx.save()
        ctx.translate(cx, y)
        ctx.scale(1.6, 0.7)
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()


def clouds(ctx, t, w, y0, y1, n=7, seed=1, speed=14.0, col=None, a=1.0):
    col = col or C['white']
    for k in range(n):
        u = hash01(seed, k)
        x = ((u * (w + 800) + t * speed * (0.6 + 0.6 * hash01(seed, k, 2))) % (w + 800)) - 400
        y = y0 + (y1 - y0) * hash01(seed, k, 3)
        cloud(ctx, x, y, 260 + 300 * hash01(seed, k, 4), 50 + 40 * hash01(seed, k, 5), col, seed * 10 + k, a)


def river(ctx, x0, x1, y0, y1, t, top=None, bot=None, glint=None, pan=0.0):
    top = top or C['blue2']
    bot = bot or C['navy3']
    vgrad(ctx, x0, y0, x1, y1, [(0, top), (1, bot)])
    rows = 26
    for i in range(rows):
        v = (i + 0.5) / rows
        near = v ** 1.6
        y = y0 + (y1 - y0) * near
        sp = 30 + 140 * near
        off = (t * (12 + 40 * near) + pan * near) % sp
        for k in range(int((x1 - x0) / sp) + 2):
            xx = x0 - sp + k * sp + off + hash01(i, k) * sp * 0.5
            L = sp * (0.25 + 0.3 * hash01(i, k, 2))
            line(ctx, [[xx, y], [xx + L, y]], 1.0 + 2.5 * near, mixc(C['blue4'], C['white'], 0.3), cap=cairo.LINE_CAP_ROUND)
            ctx.set_source_rgba(0, 0, 0, 0)
    if glint:
        gx, gw, ga = glint
        g = cairo.LinearGradient(gx - gw, 0, gx + gw, 0)
        g.add_color_stop_rgba(0, 1, 1, 1, 0)
        g.add_color_stop_rgba(0.5, 1, 0.95, 0.85, ga)
        g.add_color_stop_rgba(1, 1, 1, 1, 0)
        ctx.rectangle(gx - gw, y0, 2 * gw, (y1 - y0) * 0.6)
        ctx.set_source(g)
        ctx.fill()


def ferry(ctx, x, y, s, col=None, light=None):
    col = col or C['navy2']
    hull = [[-60, -6], [64, -6], [56, 8], [-54, 8]]
    fill(ctx, np.array(hull) * s + [x, y], col)
    fill(ctx, np.array([[-44, -6], [40, -6], [36, -20], [-38, -20]]) * s + [x, y], mixc(col, C['white'], 0.55))
    fill(ctx, np.array([[-30, -20], [22, -20], [18, -30], [-26, -30]]) * s + [x, y], mixc(col, C['white'], 0.4))
    for k in range(7):
        rect(ctx, x + (-38 + k * 11) * s, y - 16 * s, x + (-33 + k * 11) * s, y - 11 * s, mixc(col, C['navy0'], 0.3))
    line(ctx, [[x - 70 * s, y + 8 * s], [x - 130 * s, y + 10 * s]], 2 * s, mixc(C['white'], C['blue3'], 0.3))


def bird(ctx, x, y, s, t, seed=0, col=None):
    f = math.sin(t * 8 + seed)
    line(ctx, [[x - 9 * s, y - 3 * s * f], [x - 3 * s, y], [x, y + s], [x + 3 * s, y], [x + 9 * s, y - 3 * s * f]], max(1.0, 1.6 * s),
         col or C['navy2'])


# ----------------------------------------------------------------------------------------------
# The skyline of Lower Manhattan (seen from the west, across the Hudson) and the Twin Towers
# ----------------------------------------------------------------------------------------------
def building(ctx, x, gy, w, h, col, lit=None, seed=0, setback=0, crown=None, win=0.0, wincol=None, edge=None):
    rect(ctx, x, gy - h, x + w, gy, col)
    if setback:
        rect(ctx, x + w * 0.15, gy - h - setback, x + w * 0.85, gy - h, col)
    if crown == 'spire':
        fill(ctx, [[x + w * 0.42, gy - h - setback], [x + w * 0.5, gy - h - setback - h * 0.18], [x + w * 0.58, gy - h - setback]], col)
    elif crown == 'pyramid':
        fill(ctx, [[x + w * 0.1, gy - h - setback], [x + w * 0.5, gy - h - setback - w * 0.5], [x + w * 0.9, gy - h - setback]], col)
    if edge:
        rect(ctx, x + w * 0.82, gy - h - setback, x + w, gy, edge)
    if win > 0:
        rng = np.random.default_rng(seed)
        wc = wincol or mixc(col, C['white'], 0.18)
        for yy in range(int(gy - h + 8), int(gy - 6), 10):
            for xx in range(int(x + 4), int(x + w - 4), 7):
                if rng.random() < win:
                    rect(ctx, xx, yy, xx + 3, yy + 4, wc)


def twin_towers(ctx, x, gy, s, t, col=None, lit=None, rim=None, bands=True, highlight=None, alpha=1.0, outline=None):
    """WTC 1 (the North Tower, with its antenna, on the left seen from the west) and WTC 2 (the South Tower).
    s = px per metre: each tower is 63 m wide and about 415 m tall; the North Tower's antenna added about 110 m.
    highlight: dict(tower='N'|'S', f0, f1, k) marks a band of floors (out of 110) in red."""
    col = col or C['navy3']
    rim = rim or mixc(col, C['white'], 0.35)
    w = 63 * s
    towers = [('N', x - 4 * s, 417 * s), ('S', x + w + 26 * s, 415 * s)]
    for name, tx, h in towers:
        top = gy - h
        if outline:
            ctx.rectangle(tx, top, w, h)
            setc(ctx, outline[0])
            ctx.set_line_width(outline[1])
            ctx.stroke()
        else:
            g = cairo.LinearGradient(tx, 0, tx + w, 0)
            g.add_color_stop_rgba(0, *mixc(col, C['white'], 0.12)[:3], alpha)
            g.add_color_stop_rgba(0.55, *col[:3], alpha)
            g.add_color_stop_rgba(1, *mixc(col, C['navy0'], 0.35)[:3], alpha)
            ctx.rectangle(tx, top, w, h)
            ctx.set_source(g)
            ctx.fill()
            # the narrow steel columns of the façade
            n = 22
            for k in range(1, n):
                xx = tx + w * k / n
                line(ctx, [[xx, top + 2], [xx, gy]], max(0.5, 0.35 * s), mixc(col, C['white'], 0.08 + 0.05 * (k % 2)), cap=cairo.LINE_CAP_BUTT)
            rect(ctx, tx, top, tx + max(1.0, 1.2 * s), gy, rim)
        if bands:
            for fl in (44, 78):
                yy = gy - h * fl / 110
                rect(ctx, tx, yy - 2.5 * s, tx + w, yy + 2.5 * s, mixc(col, C['navy0'], 0.25) if not outline else outline[0])
        if name == 'N':
            line(ctx, [[tx + w / 2, top], [tx + w / 2, top - 110 * s]], max(1.0, 2.2 * s), col if not outline else outline[0])
            rect(ctx, tx + w / 2 - 4 * s, top - 18 * s, tx + w / 2 + 4 * s, top, col if not outline else outline[0])
        if highlight and highlight.get('tower') == name and highlight.get('k', 0) > 0:
            k = highlight['k']
            y0, y1 = gy - h * highlight['f1'] / 110, gy - h * highlight['f0'] / 110
            rect(ctx, tx - 2, y0, tx + w + 2, y1, (*C['red'][:3], 0.85 * k))
            glow(ctx, tx + w / 2, (y0 + y1) / 2, w * 1.4, C['red'], 0.35 * k)
    return towers


def skyline(ctx, x0, x1, gy, s, seed, col, haze=0.0, win=0.0, low=False):
    """A band of generic towers and blocks (not portraits of particular buildings)."""
    rng = np.random.default_rng(seed)
    x = x0
    while x < x1:
        w = rng.uniform(18, 46) * s
        h = rng.uniform(40, 150 if low else 230) * s
        c = mixc(col, C['sky_hz'], haze * rng.uniform(0.85, 1.1))
        crown = rng.choice([None, None, None, 'spire', 'pyramid'])
        building(ctx, x, gy, w, h, c, seed=abs(int(x)) + seed, setback=rng.uniform(0, 20) * s if rng.random() < 0.4 else 0, crown=crown, win=win)
        x += w + rng.uniform(-6, 10) * s


def one_wtc(ctx, x, gy, s, col, rim=None):
    """One World Trade Center (completed 2014): a square base rising into a tapering, faceted glass tower with a spire."""
    w = 62 * s
    h = 417 * s
    base = 56 * s
    rect(ctx, x - w / 2, gy - base, x + w / 2, gy, mixc(col, C['navy0'], 0.2))
    fill(ctx, [[x - w / 2, gy - base], [x + w / 2, gy - base], [x + w * 0.3, gy - h], [x - w * 0.3, gy - h]], col)
    fill(ctx, [[x, gy - base], [x + w / 2, gy - base], [x + w * 0.3, gy - h], [x, gy - h + 30 * s]], mixc(col, C['white'], 0.12))
    rect(ctx, x - w * 0.3, gy - h - 6 * s, x + w * 0.3, gy - h, mixc(col, C['navy0'], 0.3))
    line(ctx, [[x, gy - h - 6 * s], [x, gy - h - 124 * s]], max(1.0, 2.0 * s), col)
    if rim:
        line(ctx, [[x - w / 2, gy - base], [x - w * 0.3, gy - h]], max(1.0, 1.2 * s), rim)


# ----------------------------------------------------------------------------------------------
# Smoke and dust, drawn with restraint
# ----------------------------------------------------------------------------------------------
def plume(ctx, x, y, s, t, seed=0, n=14, col=None, alpha=0.7, wind=0.6, grow=1.0, spread=1.0):
    """A soft column of grey smoke drifting downwind (no flame)."""
    col = col or C['grey3']
    for k in range(n):
        u = ((t * 0.05 + k / n + hash01(seed, k) * 0.05) % 1.0)
        if u > grow:
            continue
        h = u * 700 * s
        px = x + wind * h * 1.1 * spread + 30 * s * math.sin(u * 5 + t * 0.3 + k)
        py = y - h * 0.55
        r = (30 + 260 * u) * s * spread
        a = alpha * min(1.0, u * 8) * (1 - u) ** 0.7
        c = mixc(col, C['grey5'], 0.3 * hash01(seed, k, 2))
        g = cairo.RadialGradient(px, py, 0, px, py, r)
        g.add_color_stop_rgba(0, c[0], c[1], c[2], a)
        g.add_color_stop_rgba(0.6, c[0], c[1], c[2], a * 0.6)
        g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
        ctx.set_source(g)
        ctx.arc(px, py, r, 0, 2 * math.pi)
        ctx.fill()


def particles(ctx, t, x0, y0, x1, y1, n=80, seed=3, col=None, size=2.0, alpha=0.6, fall=20.0, drift=8.0):
    col = col or C['grey5']
    for i in range(n):
        bx, by = hash01(seed, i, 1), hash01(seed, i, 2)
        x = x0 + (x1 - x0) * ((bx + t * drift / max(x1 - x0, 1) * (0.5 + hash01(seed, i, 3))) % 1.0) + 12 * math.sin(t * 0.8 + i)
        y = y0 + (y1 - y0) * ((by + t * fall / max(y1 - y0, 1) * (0.5 + hash01(seed, i, 4))) % 1.0)
        ctx.arc(x, y, size * (0.5 + hash01(seed, i, 5)), 0, 2 * math.pi)
        setc(ctx, col, alpha * (0.4 + 0.6 * hash01(seed, i, 6)))
        ctx.fill()


# ----------------------------------------------------------------------------------------------
# The map of the eastern United States (equirectangular, simplified outlines)
# ----------------------------------------------------------------------------------------------
COAST = [(47.4, -68.3), (44.8, -66.9), (44.3, -68.2), (43.6, -70.2), (42.9, -70.8), (42.5, -70.9), (42.0, -70.6), (41.8, -69.95),
         (41.55, -70.6), (41.45, -71.4), (41.3, -72.3), (41.05, -73.6), (40.75, -73.8), (40.6, -74.0), (40.47, -74.0), (40.2, -74.03),
         (39.75, -74.1), (39.35, -74.45), (38.93, -74.9), (39.2, -75.2), (39.6, -75.55), (38.8, -75.1), (38.45, -75.05), (38.0, -75.25),
         (37.55, -75.65), (37.1, -75.95), (37.25, -76.3), (37.95, -76.3), (38.6, -76.45), (39.3, -76.45), (38.9, -76.2), (38.3, -76.35),
         (37.6, -76.3), (37.0, -76.2), (36.85, -75.97), (36.2, -75.7), (35.2, -75.5), (34.6, -76.5), (34.2, -77.8), (33.8, -78.6),
         (32.0, -80.8), (30.5, -81.4), (30.5, -88.0), (47.4, -88.0)]
LAKE_ERIE = [(42.85, -78.9), (42.6, -79.8), (42.25, -80.9), (41.75, -81.8), (41.4, -82.7), (41.7, -83.4), (42.0, -83.2), (42.5, -81.8),
             (42.8, -80.4), (42.9, -79.1)]
LAKE_ONTARIO = [(43.25, -79.8), (43.65, -79.4), (43.95, -78.0), (44.2, -76.4), (43.6, -76.2), (43.3, -77.4), (43.3, -78.8)]
PA = [(42.27, -80.52), (42.0, -79.76), (42.0, -75.36), (41.36, -74.69), (40.6, -75.2), (39.85, -75.42), (39.72, -75.79), (39.72, -80.52)]
LONG_ISLAND = [(40.6, -74.0), (40.58, -73.4), (40.7, -72.6), (40.9, -72.0), (41.08, -71.85), (41.0, -72.4), (40.97, -73.1), (40.88, -73.6),
               (40.8, -73.85)]
POTOMAC = [(39.72, -77.75), (39.4, -77.55), (39.05, -77.25), (38.9, -77.05), (38.6, -77.2), (38.3, -77.0), (38.0, -76.4)]
DELAWARE_R = [(42.0, -75.36), (41.36, -74.69), (40.6, -75.2), (40.2, -74.75), (39.85, -75.42)]
STATE_LABELS = [('PENNSYLVANIA', 40.95, -77.6), ('NEW YORK', 42.55, -75.6), ('NEW JERSEY', 40.15, -74.55), ('VIRGINIA', 37.75, -78.3),
                ('MARYLAND', 39.45, -76.9), ('ATLANTIC OCEAN', 38.9, -72.4)]
PLACES = {'nyc': (40.71, -74.01), 'dc': (38.87, -77.06), 'shanksville': (40.05, -78.91)}


class MapProj:
    def __init__(self, lat0=40.0, lon0=-76.0, scale=320.0, cx=540.0, cy=960.0):
        self.lat0, self.lon0, self.k, self.cx, self.cy = lat0, lon0, scale, cx, cy
        self.cosl = math.cos(math.radians(lat0))

    def p(self, lat, lon):
        return self.cx + (lon - self.lon0) * self.cosl * self.k, self.cy - (lat - self.lat0) * self.k


def draw_map(ctx, proj, t, land=None, water=None, border=None, labels=1.0):
    land = land or mixc(C['navy3'], C['blue1'], 0.35)
    water = water or C['navy0']
    rect(ctx, -2000, -2000, 4000, 4000, water)
    # a faint graticule
    for lat in range(30, 50):
        a = proj.p(lat, -90)
        b = proj.p(lat, -60)
        line(ctx, [a, b], 1.0, (*C['blue1'][:3], 0.18))
    for lon in range(-90, -60):
        a = proj.p(28, lon)
        b = proj.p(50, lon)
        line(ctx, [a, b], 1.0, (*C['blue1'][:3], 0.18))
    pts = [proj.p(*q) for q in COAST]
    fill(ctx, pts, land)
    ctx.new_path()
    path_poly(ctx, np.array(pts), True)
    setc(ctx, mixc(land, C['blue3'], 0.4))
    ctx.set_line_width(2.0)
    ctx.stroke()
    li = [proj.p(*q) for q in LONG_ISLAND]
    fill(ctx, li, land, smooth_=True)
    for lake in (LAKE_ERIE, LAKE_ONTARIO):
        fill(ctx, [proj.p(*q) for q in lake], water, smooth_=True)
    bc = border or (*C['blue4'][:3], 0.4)
    ctx.new_path()
    path_poly(ctx, np.array([proj.p(*q) for q in PA]), True)
    setc(ctx, bc)
    ctx.set_line_width(2.0)
    ctx.set_dash([8, 6])
    ctx.stroke()
    ctx.set_dash([])
    for river_ in (POTOMAC, DELAWARE_R):
        line(ctx, [proj.p(*q) for q in river_], 2.0, bc, dash=[8, 6])
    for name, la, lo in STATE_LABELS:
        x, y = proj.p(la, lo)
        text(ctx, x, y, 26, name, (*C['blue4'][:3], 0.55 * labels), track=0.3)


def marker(ctx, x, y, t, t0, col=None, r=14):
    """A location pin that pops in at t0 with an expanding ring."""
    u = t - t0
    if u < 0:
        return
    col = col or C['red2']
    k = min(1.0, u / 0.25)
    pop = 1 + 0.35 * math.sin(math.pi * k) if k < 1 else 1.0
    for j in range(2):
        ph = (u * 0.8 + j * 0.5) % 1.0
        ctx.arc(x, y, r * (1 + 3.5 * ph), 0, 2 * math.pi)
        setc(ctx, col, 0.5 * (1 - ph) * k)
        ctx.set_line_width(2.5)
        ctx.stroke()
    glow(ctx, x, y, r * 4, col, 0.35 * k)
    ctx.arc(x, y, r * pop * k, 0, 2 * math.pi)
    setc(ctx, col)
    ctx.fill()
    ctx.arc(x, y, r * 0.42 * pop * k, 0, 2 * math.pi)
    setc(ctx, C['white'])
    ctx.fill()


def pentagon_icon(ctx, x, y, r, col=None, lw=2.0, a=1.0):
    """The Pentagon seen from above: five concentric pentagonal rings around a central court."""
    col = col or C['white']
    for k, rr in enumerate((1.0, 0.82, 0.64, 0.42)):
        pts = [(x + rr * r * math.sin(2 * math.pi * i / 5), y - rr * r * math.cos(2 * math.pi * i / 5)) for i in range(5)]
        ctx.new_path()
        path_poly(ctx, np.array(pts), True)
        setc(ctx, col, a * (0.95 if k in (0, 3) else 0.45))
        ctx.set_line_width(lw if k in (0, 3) else lw * 0.6)
        ctx.stroke()
    for i in range(5):
        ang = 2 * math.pi * (i + 0.5) / 5
        line(ctx, [[x + 0.42 * r * math.sin(ang), y - 0.42 * r * math.cos(ang)], [x + 0.95 * r * math.sin(ang), y - 0.95 * r * math.cos(ang)]],
             lw * 0.5, (*col[:3], a * 0.4))


# ----------------------------------------------------------------------------------------------
# Street level: vehicles and silhouettes
# ----------------------------------------------------------------------------------------------
def light_bar(ctx, x, y, s, t, seed=0, a=1.0):
    ph = (t * 2.6 + seed * 0.37) % 1.0
    lc = C['red2'] if ph < 0.5 else C['white']
    glow(ctx, x, y, 90 * s, lc, 0.55 * a)
    rect(ctx, x - 10 * s, y - 2 * s, x + 10 * s, y + 2 * s, lc)


def fire_truck(ctx, x, gy, s, t, col=None, face=1, seed=0):
    """A fire engine as a dark silhouette with a red rim, chrome and flashing lights."""
    col = col or C['char']
    ctx.save()
    ctx.translate(x, gy)
    ctx.scale(face, 1)
    L = 10 * s
    fill(ctx, [[-L / 2, -0.5 * s], [-L / 2, -3.0 * s], [L * 0.22, -3.0 * s], [L * 0.24, -3.4 * s], [L * 0.42, -3.4 * s], [L / 2, -2.2 * s],
               [L / 2, -0.5 * s]], col)
    rect(ctx, -L / 2, -1.6 * s, L / 2, -1.35 * s, (*C['red'][:3], 0.9))
    rect(ctx, -L / 2, -3.1 * s, L * 0.2, -2.95 * s, (*C['grey4'][:3], 0.5))
    fill(ctx, [[L * 0.28, -3.3 * s], [L * 0.41, -3.3 * s], [L * 0.47, -2.3 * s], [L * 0.28, -2.3 * s]], (*C['blue3'][:3], 0.3))
    for wx in (-L * 0.32, -L * 0.18, L * 0.34):
        ctx.arc(wx, -0.5 * s, 0.5 * s, 0, 2 * math.pi)
        setc(ctx, C['navy0'])
        ctx.fill()
    light_bar(ctx, L * 0.33, -3.5 * s, s / 6, t, seed)
    ctx.restore()


def silhouette(ctx, draw_fn, col, rim=None, rim_dx=-3.0):
    """Draw something (a figure) as a flat silhouette with an optional rim of light on one side."""
    ctx.push_group()
    draw_fn(ctx)
    pat = ctx.pop_group()
    if rim:
        ctx.save()
        ctx.translate(rim_dx, -1.0)
        setc(ctx, rim)
        ctx.mask(pat)
        ctx.restore()
    setc(ctx, col)
    ctx.mask(pat)


# ----------------------------------------------------------------------------------------------
# The memorial
# ----------------------------------------------------------------------------------------------
class Persp:
    """A simple one-point perspective for the memorial plaza: ground point (X, Z) -> screen."""

    def __init__(self, f=900.0, cx=540.0, hy=760.0, hcam=9.0):
        self.f, self.cx, self.hy, self.h = f, cx, hy, hcam

    def p(self, X, Y, Z):
        return self.cx + self.f * X / Z, self.hy + self.f * (self.h - Y) / Z


def memorial_pool(ctx, P, t, x0, x1, z0, z1, depth=9.0, names=True, lit=0.0):
    """One reflecting pool set in a tower's footprint: a bronze parapet with names, water falling down all four
    walls into the pool, and the central void into which the water falls again."""
    def quad(pts, col):
        fill(ctx, [P.p(*q) for q in pts], col)
    # the parapet (bronze band around the edge)
    pw = 1.2
    quad([(x0 - pw, 1.0, z0 - pw), (x1 + pw, 1.0, z0 - pw), (x1 + pw, 1.0, z1 + pw), (x0 - pw, 1.0, z1 + pw)], C['bronze'])
    quad([(x0, 1.0, z0), (x1, 1.0, z0), (x1, 1.0, z1), (x0, 1.0, z1)], C['navy0'])
    if names:
        for k in range(26):
            u = (k + 0.5) / 26
            for (a, b) in (((x0 - pw * 0.6 + (x1 - x0 + pw * 1.2) * u, z0 - pw * 0.5), (x0 - pw * 0.6 + (x1 - x0 + pw * 1.2) * u + 0.7, z0 - pw * 0.5)),):
                pa, pb = P.p(a[0], 1.0, a[1]), P.p(b[0], 1.0, b[1])
                line(ctx, [pa, pb], 1.0, (*C['warm'][:3], 0.35 + 0.3 * lit))
    # the far wall and the side walls, with falling water
    far = [(x0, 1.0, z1), (x1, 1.0, z1), (x1, -depth, z1), (x0, -depth, z1)]
    quad(far, C['grey2'])
    for side in ((x0, x0), (x1, x1)):
        quad([(side[0], 1.0, z0), (side[0], 1.0, z1), (side[0], -depth, z1), (side[0], -depth, z0)], C['grey1'])
    # falling water: animated vertical streaks on the far wall
    ctx.save()
    ctx.new_path()
    path_poly(ctx, np.array([P.p(*q) for q in far]), True)
    ctx.clip()
    for k in range(60):
        u = (k + 0.5) / 60
        X = x0 + (x1 - x0) * u
        top = P.p(X, 1.0, z1)
        bot = P.p(X, -depth, z1)
        ph = (t * 0.9 + hash01(k, 3)) % 1.0
        yy = top[1] + (bot[1] - top[1]) * ph
        line(ctx, [[top[0], top[1]], [bot[0], bot[1]]], 2.0, (*C['white'][:3], 0.28))
        line(ctx, [[top[0], yy - 14], [top[0], yy + 14]], 2.2, (*C['white'][:3], 0.55))
    ctx.restore()
    for X in (x0, x1):
        for k in range(14):
            Z = z0 + (z1 - z0) * (k + 0.5) / 14
            top, bot = P.p(X, 1.0, Z), P.p(X, -depth, Z)
            ph = (t * 0.9 + hash01(k, X > 0, 5)) % 1.0
            line(ctx, [top, bot], 1.6, (*C['white'][:3], 0.18))
            yy = top[1] + (bot[1] - top[1]) * ph
            xx = top[0] + (bot[0] - top[0]) * ph
            line(ctx, [[xx, yy - 10], [xx, yy + 10]], 1.8, (*C['white'][:3], 0.45))
    # the pool floor and the central void
    quad([(x0, -depth, z0), (x1, -depth, z0), (x1, -depth, z1), (x0, -depth, z1)], C['navy2'])
    cxm, czm = (x0 + x1) / 2, (z0 + z1) / 2
    hw = (x1 - x0) * 0.18
    quad([(cxm - hw, -depth, czm - hw), (cxm + hw, -depth, czm - hw), (cxm + hw, -depth, czm + hw), (cxm - hw, -depth, czm + hw)], C['navy0'])
    for k in range(20):
        u = (k + 0.5) / 20
        a = P.p(cxm - hw + 2 * hw * u, -depth, czm + hw)
        ph = (t * 1.2 + hash01(k, 7)) % 1.0
        line(ctx, [a, (a[0], a[1] + 10 + 20 * ph)], 1.5, (*C['white'][:3], 0.35 * (1 - ph)))
    # shimmer on the pool surface
    for k in range(30):
        X = x0 + (x1 - x0) * hash01(k, 11)
        Z = z0 + (z1 - z0) * hash01(k, 12)
        q = P.p(X + 0.4 * math.sin(t + k), -depth + 0.01, Z)
        line(ctx, [q, (q[0] + 16, q[1])], 1.2, (*C['blue4'][:3], 0.25 + 0.2 * math.sin(t * 2 + k)))


def tree_round(ctx, x, gy, h, col, seed=0):
    rect(ctx, x - h * 0.025, gy - h * 0.45, x + h * 0.025, gy, mixc(col, C['navy0'], 0.4))
    rng = np.random.default_rng(seed)
    for k in range(4):
        cx = x + rng.uniform(-0.12, 0.12) * h
        cy = gy - h * rng.uniform(0.55, 0.85)
        ctx.arc(cx, cy, h * rng.uniform(0.18, 0.26), 0, 2 * math.pi)
        setc(ctx, mixc(col, C['white'], 0.05 * k))
        ctx.fill()


def beams(ctx, x1, x2, gy, top, t, a=1.0):
    """The Tribute in Light: two vertical columns of light rising from Lower Manhattan."""
    for k, x in enumerate((x1, x2)):
        fl = 1 + 0.03 * math.sin(t * 3 + k)
        for wdt, aa in ((90, 0.10), (44, 0.18), (18, 0.4)):
            g = cairo.LinearGradient(0, gy, 0, top)
            g.add_color_stop_rgba(0, 0.85, 0.92, 1.0, aa * a * fl)
            g.add_color_stop_rgba(0.7, 0.75, 0.85, 1.0, aa * 0.6 * a)
            g.add_color_stop_rgba(1, 0.7, 0.8, 1.0, 0)
            ctx.move_to(x - wdt * 0.5, gy)
            ctx.line_to(x + wdt * 0.5, gy)
            ctx.line_to(x + wdt * 0.62, top)
            ctx.line_to(x - wdt * 0.62, top)
            ctx.close_path()
            ctx.set_source(g)
            ctx.fill()
        glow(ctx, x, gy, 140, (0.85, 0.92, 1.0, 1.0), 0.4 * a)


def logo(ctx, cx, cy, s, a=1.0, t=0.0):
    """The channel mark: an archive drawer with a keyhole, and the wordmark HIDDEN ARCHIVES."""
    w, h = 120 * s, 92 * s
    ctx.new_path()
    r = 10 * s
    x0, y0 = cx - w / 2, cy - h - 30 * s
    ctx.move_to(x0 + r, y0)
    ctx.arc(x0 + w - r, y0 + r, r, -math.pi / 2, 0)
    ctx.arc(x0 + w - r, y0 + h - r, r, 0, math.pi / 2)
    ctx.arc(x0 + r, y0 + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x0 + r, y0 + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()
    setc(ctx, C['white'], a)
    ctx.set_line_width(5 * s)
    ctx.stroke()
    line(ctx, [[x0 + 12 * s, y0 + h * 0.5], [x0 + w - 12 * s, y0 + h * 0.5]], 4 * s, (*C['white'][:3], a * 0.8))
    kx, ky = cx, y0 + h * 0.27
    ctx.arc(kx, ky, 8 * s, 0, 2 * math.pi)
    setc(ctx, C['red2'], a)
    ctx.fill()
    fill(ctx, [[kx - 5 * s, ky + 2 * s], [kx + 5 * s, ky + 2 * s], [kx + 3 * s, ky + 16 * s], [kx - 3 * s, ky + 16 * s]], (*C['red2'][:3], a))
    rect(ctx, cx - 18 * s, y0 + h * 0.68, cx + 18 * s, y0 + h * 0.74, (*C['white'][:3], a * 0.8))
    text(ctx, cx, cy + 40 * s, 52 * s, 'HIDDEN ARCHIVES', (*C['white'][:3], a), track=0.18)
