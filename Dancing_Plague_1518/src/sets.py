"""Illustrated sets, drawn once and saved as layer PNGs in assets/layers/.

Each set is split into flat depth layers for the multiplane camera (sky, distant skyline, far buildings,
near buildings, foreground). The street is drawn in one-point perspective like a period engraving:
perspective is a drawing technique here, not a 3D render - every shape is a flat inked polygon.

  python src/sets.py            # draw every layer
  python src/sets.py street     # one set
"""
import math
import os
import sys

import cairo
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import (PAL, W, H, LAYERS, new_surface, set_c, ink_shape, ink_line, hatch_lines, mix, shade_c, hash01,
                  path_poly, path_smooth, ellipse_pts, taper_stroke, soft_glow, wob, fbm2, surf_array)

FOG = PAL['grey3']


def fogmix(c, k):
    return mix(c, FOG, min(max(k, 0.0), 0.92))


class Persp:
    """One-point street perspective: X across (m, + right), Y up (m), Z depth (m)."""

    def __init__(self, f=1375.0, vx=540.0, hy=950.0, hcam=1.6):
        self.f, self.vx, self.hy, self.h = f, vx, hy, hcam

    def p(self, X, Y, Z):
        return (self.vx + self.f * X / Z, self.hy + self.f * (self.h - Y) / Z)

    def fog(self, Z):
        return 1 - math.exp(-max(Z - 3.0, 0) / 55.0)


PS = Persp()
STREET_X = 3.1


def clipz(poly, z0, z1):
    """Clip a polygon given as (z, y) points to z0 <= z <= z1 (Sutherland-Hodgman, two planes)."""
    def clip(pts, keep, inter):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            ka, kb = keep(a), keep(b)
            if ka:
                out.append(a)
            if ka != kb:
                out.append(inter(a, b))
        return out
    pts = [tuple(q) for q in poly]
    pts = clip(pts, lambda q: q[0] >= z0, lambda a, b: (z0, a[1] + (b[1] - a[1]) * (z0 - a[0]) / (b[0] - a[0])))
    if len(pts) < 3:
        return []
    pts = clip(pts, lambda q: q[0] <= z1, lambda a, b: (z1, a[1] + (b[1] - a[1]) * (z1 - a[0]) / (b[0] - a[0])))
    return pts if len(pts) >= 3 else []


class Facade:
    """Draw on the plane X = const of one side of the street."""

    def __init__(self, ctx, side, X, z0, z1, seed, pix=1.0):
        self.ctx, self.side, self.X, self.z0, self.z1, self.seed = ctx, side, X, z0, z1, seed
        self.n = 0
        self.pix = pix

    def proj(self, pts):
        return np.array([PS.p(self.X, y, z) for z, y in pts])

    def poly(self, pts, fill, lw=1.4, shadow=None, boil=0.6, densify=0, hatch=None):
        c = clipz(pts, self.z0, self.z1)
        if not c:
            return None
        if densify:
            c = densify_pts(c, densify)
        P = self.proj(c)
        zmid = sum(q[0] for q in c) / len(c)
        k = PS.fog(zmid)
        self.n += 1
        w = lw * min(1.0, 9.0 / zmid + 0.25)
        ink_shape(self.ctx, P, fogmix(fill, k) if fill is not None else None, lw=w, ink=fogmix(PAL['ink'], k * 0.8),
                  smooth_path=False, seed=self.seed * 97 + self.n, boil=boil * min(1, 6 / zmid), shadow=shadow)
        if hatch is None:
            hatch = self.side < 0 and fill is not None and k < 0.8
        if hatch:
            ctx = self.ctx
            ctx.save()
            path_poly(ctx, P)
            ctx.clip()
            x0, y0 = P[:, 0].min(), P[:, 1].min()
            x1, y1 = P[:, 0].max(), P[:, 1].max()
            hatch_lines(ctx, x0, y0, x1, y1, 5.0 / self.pix, 62, 0.8 / self.pix, (*PAL['ink'][:3], 0.22 * (1 - k)), self.seed + self.n)
            ctx.restore()
        return P

    def line(self, pts, lw=1.2, col=None, alpha=1.0):
        a, b = pts[0], pts[-1]
        za, zb = a[0], b[0]
        if max(za, zb) < self.z0 or min(za, zb) > self.z1:
            return
        def at(z):
            t = 0 if zb == za else (z - za) / (zb - za)
            return (z, a[1] + (b[1] - a[1]) * t)
        if za != zb:
            lo, hi = sorted((za, zb))
            a2 = at(max(lo, self.z0))
            b2 = at(min(hi, self.z1))
            pts = [a2, b2]
        zmid = (pts[0][0] + pts[-1][0]) / 2
        k = PS.fog(zmid)
        self.n += 1
        ink_line(self.ctx, self.proj(pts), lw * min(1.0, 9.0 / zmid + 0.25), fogmix(col or PAL['ink'], k * 0.8),
                 seed=self.seed * 89 + self.n, boil=0.5 * min(1, 6 / zmid), smooth_path=False, alpha=alpha)


def densify_pts(pts, n):
    out = []
    for i in range(len(pts)):
        a, b = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
        for k in range(n):
            out.append(tuple(a + (b - a) * k / n))
    return out


# ----------------------------------------------------------------------------------------------
# The street
# ----------------------------------------------------------------------------------------------
def street_houses(side, seed):
    rng = np.random.default_rng(seed)
    z = 1.2
    out = []
    plasters = [PAL['plaster'], PAL['parch2'], mix(PAL['plaster'], PAL['burg2'], 0.18), mix(PAL['plaster'], PAL['green2'], 0.2),
                PAL['plaster2'], mix(PAL['parch'], PAL['brown3'], 0.3)]
    i = 0
    while z < 95:
        w = rng.uniform(4.6, 7.6)
        floors = int(rng.integers(2, 4)) + 1
        out.append(dict(z0=z, z1=z + w, floors=floors, gable=rng.random() < 0.62, plaster=plasters[int(rng.integers(0, len(plasters)))],
                        shop=rng.random() < 0.6, sign=(rng.random() < 0.45) and z < 30, seed=seed * 100 + i,
                        h0=rng.uniform(3.0, 3.4), fh=rng.uniform(2.6, 2.9), jet=rng.uniform(0.3, 0.45)))
        z += w
        i += 1
    return out


def draw_house(ctx, side, hs, z0c, z1c, pix):
    """One half-timbered house on one side: stone ground floor, jettied timber-framed upper floors,
    leaded windows, shop counter and shutters, and a steep street-facing gable or a roof band."""
    za, zb = hs['z0'], hs['z1']
    rng = np.random.default_rng(hs['seed'])
    wood = PAL['wood2']
    stone = mix(PAL['stone'], PAL['burg2'], 0.22)
    lit = side > 0
    shade_k = 0.0 if lit else -0.28
    def S(c):
        return shade_c(c, shade_k) if shade_k else c
    X0 = side * STREET_X
    y = 0.0
    tops = []
    for fl in range(hs['floors']):
        X = side * (STREET_X - fl * hs['jet'])
        F = Facade(ctx, side, X, z0c, z1c, hs['seed'] + fl, pix)
        fh = hs['h0'] if fl == 0 else hs['fh']
        y0, y1 = y, y + fh
        if fl == 0:
            F.poly([(za, y0 - 0.3), (zb, y0 - 0.3), (zb, y1), (za, y1)], S(stone), lw=1.6)
            # ashlar joints
            for k in range(1, 4):
                yy = y0 + fh * k / 4
                F.line([(za, yy), (zb, yy)], lw=0.6, alpha=0.35)
            nb = max(2, int((zb - za) / 2.4))
            if hs['shop']:
                # shop opening: counter shutter folded down, awning shutter propped up
                sa, sb = za + 0.5, za + (zb - za) * 0.62
                F.poly([(sa, 0.85), (sb, 0.85), (sb, 2.3), (sa, 2.3)], S(PAL['charcoal']), lw=1.2)
                F.poly([(sa - 0.1, 0.75), (sb + 0.1, 0.75), (sb + 0.1, 0.95), (sa - 0.1, 0.95)], S(PAL['wood3']), lw=1.0)
                F.poly([(sa - 0.15, 2.3), (sb + 0.15, 2.3), (sb + 0.15, 2.55), (sa - 0.15, 2.55)], S(PAL['wood']), lw=1.0)
                # goods on the counter: loaves, jugs, cloth
                kind = int(rng.integers(0, 3))
                for g in range(int((sb - sa) / 0.5)):
                    gz = sa + 0.25 + g * 0.5
                    if kind == 0:
                        F.poly([(gz - 0.18, 0.95), (gz + 0.18, 0.95), (gz + 0.14, 1.12), (gz - 0.14, 1.12)], S(PAL['brown3']), lw=0.8)
                    elif kind == 1:
                        F.poly([(gz - 0.1, 0.95), (gz + 0.1, 0.95), (gz + 0.12, 1.25), (gz, 1.32), (gz - 0.12, 1.25)], S(PAL['brown']), lw=0.8)
                    else:
                        F.poly([(gz - 0.2, 0.95), (gz + 0.2, 0.95), (gz + 0.2, 1.5), (gz - 0.2, 1.5)], S(mix(PAL['burg'], PAL['green'], g % 2)), lw=0.8)
                da, db = sb + 0.35, min(sb + 1.5, zb - 0.3)
            else:
                da, db = za + (zb - za) * 0.4, za + (zb - za) * 0.4 + 1.2
                for k in range(nb):
                    wz = za + (k + 0.5) * (zb - za) / nb
                    if abs(wz - (da + db) / 2) > 1.3:
                        F.poly([(wz - 0.35, 1.2), (wz + 0.35, 1.2), (wz + 0.35, 2.1), (wz - 0.35, 2.1)], S(PAL['charcoal']), lw=1.0)
            if db > da + 0.6:
                arch = [(da, 0.0), (db, 0.0), (db, 1.9)] + [((da + db) / 2 + (db - da) / 2 * math.cos(a), 1.9 + 0.45 * math.sin(a))
                                                            for a in np.linspace(0, math.pi, 7)[1:-1]] + [(da, 1.9)]
                F.poly(arch, S(PAL['wood']), lw=1.4)
                F.line([((da + db) / 2, 0.0), ((da + db) / 2, 2.3)], lw=0.7, alpha=0.7)
                for k in range(3):
                    F.line([(da + 0.1, 0.5 + k * 0.6), (db - 0.1, 0.5 + k * 0.6)], lw=0.6, alpha=0.5)
        else:
            F.poly([(za, y0), (zb, y0), (zb, y1), (za, y1)], S(hs['plaster']), lw=1.4)
            # timber framing: sill and head beams, posts, window rail, braces
            F.poly([(za, y0), (zb, y0), (zb, y0 + 0.24), (za, y0 + 0.24)], S(wood), lw=0.9)
            F.poly([(za, y1 - 0.2), (zb, y1 - 0.2), (zb, y1), (za, y1)], S(wood), lw=0.9)
            nb = max(3, int((zb - za) / 1.15))
            posts = [za + (zb - za) * k / nb for k in range(nb + 1)]
            for k, pz in enumerate(posts):
                F.poly([(pz - 0.09, y0), (pz + 0.09, y0), (pz + 0.09, y1), (pz - 0.09, y1)], S(wood), lw=0.8)
            F.poly([(za, y0 + 0.85), (zb, y0 + 0.85), (zb, y0 + 0.98), (za, y0 + 0.98)], S(wood), lw=0.8)
            win_bays = set(rng.choice(nb, size=max(1, nb // 2), replace=False).tolist())
            for k in range(nb):
                a, b = posts[k] + 0.09, posts[k + 1] - 0.09
                if k in win_bays:
                    # leaded window with small panes
                    F.poly([(a + 0.06, y0 + 1.05), (b - 0.06, y0 + 1.05), (b - 0.06, y1 - 0.32), (a + 0.06, y1 - 0.32)],
                           S(mix(PAL['charcoal'], PAL['grey2'], 0.35)), lw=1.0)
                    for q in range(1, 4):
                        zz = a + (b - a) * q / 4
                        F.line([(zz, y0 + 1.05), (zz, y1 - 0.32)], lw=0.4, col=PAL['grey3'], alpha=0.5)
                    for q in range(1, 3):
                        yy = y0 + 1.05 + (y1 - 0.32 - y0 - 1.05) * q / 3
                        F.line([(a + 0.06, yy), (b - 0.06, yy)], lw=0.4, col=PAL['grey3'], alpha=0.5)
                    # under the window: a St Andrew's cross
                    F.line([(a, y0 + 0.24), (b, y0 + 0.85)], lw=1.6, col=wood)
                    F.line([(a, y0 + 0.85), (b, y0 + 0.24)], lw=1.6, col=wood)
                else:
                    if rng.random() < 0.5:
                        F.line([(a, y0 + 0.98), (b, y1 - 0.2)], lw=2.2, col=wood)
                    else:
                        m = (a + b) / 2
                        F.line([(a, y0 + 0.24), (m, y0 + 0.98)], lw=2.0, col=wood)
                        F.line([(b, y0 + 0.24), (m, y0 + 0.98)], lw=2.0, col=wood)
                        F.line([(m, y0 + 0.98), (a, y1 - 0.2)], lw=2.0, col=wood)
                        F.line([(m, y0 + 0.98), (b, y1 - 0.2)], lw=2.0, col=wood)
            # the jetty: carved bracket ends under the overhang
            for pz in posts[::2]:
                F.poly([(pz - 0.12, y0 - 0.28), (pz + 0.12, y0 - 0.28), (pz + 0.12, y0), (pz - 0.12, y0)], S(PAL['wood3']), lw=0.7)
        tops.append(X)
        y = y1
    # roof
    X = side * (STREET_X - (hs['floors'] - 1) * hs['jet'])
    F = Facade(ctx, side, X, z0c, z1c, hs['seed'] + 50, pix)
    if hs['gable']:
        m = (za + zb) / 2
        gh = (zb - za) * 0.5 * 1.75
        F.poly([(za - 0.15, y), (zb + 0.15, y), (m, y + gh)], S(hs['plaster']), lw=1.5)
        F.line([(za, y), (m, y + gh)], lw=2.4, col=wood)
        F.line([(zb, y), (m, y + gh)], lw=2.4, col=wood)
        F.line([(m, y), (m, y + gh * 0.92)], lw=1.8, col=wood)
        F.line([(za + (m - za) * 0.45, y + gh * 0.45), (zb - (zb - m) * 0.45, y + gh * 0.45)], lw=1.8, col=wood)
        for q in (-1, 1):
            wz = m + q * (zb - za) * 0.18
            F.poly([(wz - 0.25, y + 0.5), (wz + 0.25, y + 0.5), (wz + 0.25, y + 1.3), (wz - 0.25, y + 1.3)], S(PAL['charcoal']), lw=0.9)
        F.poly([(m - 0.2, y + gh * 0.55), (m + 0.2, y + gh * 0.55), (m + 0.2, y + gh * 0.72), (m - 0.2, y + gh * 0.72)], S(PAL['charcoal']), lw=0.8)
        # the roof slopes show behind the gable edge as a thin tiled band
        F.poly([(za - 0.35, y - 0.05), (za - 0.05, y - 0.05), (m, y + gh + 0.2), (m - 0.25, y + gh + 0.35)], S(PAL['roof']), lw=1.1)
        F.poly([(zb + 0.35, y - 0.05), (zb + 0.05, y - 0.05), (m, y + gh + 0.2), (m + 0.25, y + gh + 0.35)], S(PAL['roof']), lw=1.1)
    else:
        # eaves to the street: the roof plane climbs away from us; drawn as a tiled band above the wall
        Fr = Facade(ctx, side, X, z0c, z1c, hs['seed'] + 60, pix)
        rh = 3.6
        P = Fr.poly([(za - 0.1, y), (zb + 0.1, y), (zb + 0.1, y + rh), (za - 0.1, y + rh)], S(PAL['roof2']), lw=1.3)
        if P is not None:
            for k in range(1, 7):
                Fr.line([(za, y + rh * k / 7), (zb, y + rh * k / 7)], lw=0.5, alpha=0.45)
        # a dormer
        m = (za + zb) / 2
        Fr.poly([(m - 0.6, y + 0.4), (m + 0.6, y + 0.4), (m + 0.6, y + 1.5), (m, y + 2.2), (m - 0.6, y + 1.5)], S(hs['plaster']), lw=1.1)
        Fr.poly([(m - 0.3, y + 0.6), (m + 0.3, y + 0.6), (m + 0.3, y + 1.3), (m - 0.3, y + 1.3)], S(PAL['charcoal']), lw=0.8)
    return y


def draw_sign(ctx, side, hs, z0c, z1c, kind):
    """A hanging trade sign on an iron bracket, facing down the street (so it faces us)."""
    z = hs['z0'] + 0.6
    if not (z0c <= z <= z1c):
        return
    Xw = side * (STREET_X - hs['jet'])
    Xe = side * (STREET_X - 1.35)
    y = hs['h0'] + 0.6
    a = PS.p(Xw, y, z)
    b = PS.p(Xe, y, z)
    k = PS.fog(z)
    s = PS.f / z
    ink_line(ctx, np.array([a, b]), max(1.2, 0.05 * s), fogmix(PAL['ink'], k), seed=hs['seed'])
    ink_line(ctx, np.array([a, ((a[0] + b[0]) / 2, a[1] - 0.25 * s), b]), max(0.8, 0.025 * s), fogmix(PAL['ink'], k), seed=hs['seed'] + 1)
    cx = (a[0] * 0.35 + b[0] * 0.65)
    cy = a[1] + 0.12 * s
    ink_line(ctx, np.array([[cx - 0.22 * s, a[1]], [cx - 0.22 * s, cy + 0.08 * s]]), max(0.8, 0.012 * s), fogmix(PAL['ink'], k))
    ink_line(ctx, np.array([[cx + 0.22 * s, a[1]], [cx + 0.22 * s, cy + 0.08 * s]]), max(0.8, 0.012 * s), fogmix(PAL['ink'], k))
    if kind == 'pretzel':
        # the bakers' sign of the Upper Rhine
        t = np.linspace(0, 2 * math.pi, 60)
        xs = np.sin(t) * 0.36
        ys = np.sin(2 * t) * 0.16 + 0.32 - np.cos(t) * 0.05
        P = np.stack([cx + xs * s, cy + 0.1 * s + ys * s], 1)
        ink_line(ctx, P, max(2.0, 0.09 * s), fogmix(PAL['brown3'], k), seed=hs['seed'] + 2)
        ink_line(ctx, P, max(0.8, 0.018 * s), fogmix(PAL['ink'], k), seed=hs['seed'] + 3)
    else:
        bd = np.array([[cx - 0.3 * s, cy + 0.08 * s], [cx + 0.3 * s, cy + 0.08 * s], [cx + 0.3 * s, cy + 0.62 * s], [cx - 0.3 * s, cy + 0.62 * s]])
        ink_shape(ctx, bd, fogmix(PAL['wood3'], k), lw=max(1.0, 0.03 * s), ink=fogmix(PAL['ink'], k), smooth_path=False, seed=hs['seed'])
        em = {'shoe': PAL['charcoal'], 'key': PAL['grey2'], 'jug': PAL['burg3']}[kind]
        if kind == 'shoe':
            e = np.array([[cx - 0.2, cy + 0.42], [cx - 0.18, cy + 0.25], [cx - 0.05, cy + 0.27], [cx + 0.2, cy + 0.42]])
            e = np.array([[cx + (q[0] - cx) * s, cy + (q[1] - cy) * s] for q in e])
        elif kind == 'key':
            e = ellipse_pts(cx - 0.12 * s, cy + 0.35 * s, 0.08 * s, 0.08 * s, 10)
            ink_line(ctx, np.array([[cx - 0.04 * s, cy + 0.35 * s], [cx + 0.2 * s, cy + 0.35 * s], [cx + 0.2 * s, cy + 0.45 * s]]), max(1, 0.03 * s), fogmix(PAL['ink'], k))
        else:
            e = np.array([[cx - 0.12, cy + 0.55], [cx + 0.12, cy + 0.55], [cx + 0.15, cy + 0.3], [cx + 0.05, cy + 0.2], [cx - 0.05, cy + 0.2], [cx - 0.15, cy + 0.3]])
            e = np.array([[cx + (q[0] - cx) * s, cy + (q[1] - cy) * s] for q in e])
        ink_shape(ctx, e, fogmix(em, k), lw=max(0.8, 0.02 * s), ink=fogmix(PAL['ink'], k), smooth_path=True, seed=hs['seed'] + 5)


COBBLES = None


def cobbles():
    global COBBLES
    if COBBLES is None:
        rng = np.random.default_rng(7)
        out = []
        z = 1.6
        while z < 60:
            row = 0.15 * (1 + (z / 14) ** 1.3)
            X = -STREET_X + rng.uniform(0, 0.2)
            while X < STREET_X:
                w = row * rng.uniform(0.8, 1.25)
                out.append((X + w / 2, z + rng.uniform(-0.03, 0.03) * row / 0.24, w * 0.46, row * 0.44, rng.random(), rng.random()))
                X += w
            z += row
        COBBLES = out
    return COBBLES


def draw_ground(ctx, z0c, z1c, pix=1.0, detail=1.0, night=0.0):
    """Cobbled street with a central gutter, the cast shadow of the left-hand houses, straw and mud."""
    zz0, zz1 = max(z0c, 1.3), min(z1c, 400)
    a, b = PS.p(-STREET_X, 0, zz0), PS.p(STREET_X, 0, zz0)
    c, d = PS.p(STREET_X, 0, zz1), PS.p(-STREET_X, 0, zz1)
    k = PS.fog((zz0 + zz1) / 2)
    ink_shape(ctx, np.array([a, b, c, d]), fogmix(mix(PAL['stone2'], PAL['brown'], 0.35), k), lw=0, smooth_path=False)
    for (X, z, rx, rz, r1, r2) in cobbles():
        if z < z0c or z >= z1c:
            continue
        k = PS.fog(z)
        pts = [PS.p(X + rx * math.cos(t) * (0.9 + 0.2 * r1), 0, z + rz * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 9)[:-1]]
        P = np.array(pts)
        sz = PS.f * rx / z
        base = mix(PAL['stone'], PAL['brown3'], r2 * 0.6)
        if abs(X) < 0.32:
            base = shade_c(base, -0.25)
        if X < -0.2 + 0.0 * z:
            base = shade_c(base, -0.22)
        col = fogmix(shade_c(base, -0.15 * r1), k)
        ink_shape(ctx, P, col, lw=(max(0.5, min(1.6, sz * 0.09)) * detail) if sz > 5 else 0.35, ink=fogmix(PAL['ink'], k * 0.7 + (0.25 if sz < 8 else 0)), smooth_path=True,
                  seed=int(r1 * 1e6), boil=min(0.5, sz * 0.03), shadow=(shade_c(col, -0.3), max(0.5, sz * 0.18)) if sz > 4 else None,
                  light=(-0.5, -0.85))
        if sz > 14 and detail > 0.9:
            # cracks, wear, a highlight on the worn top
            if r2 > 0.55:
                q = P[int(r1 * 7)]
                ink_line(ctx, np.array([q, q * 0.6 + P.mean(0) * 0.4]), max(0.4, sz * 0.03), PAL['ink'], alpha=0.5)
            c0 = P.mean(0)
            ink_shape(ctx, ellipse_pts(c0[0] - sz * 0.18, c0[1] - sz * 0.12, sz * 0.32, sz * 0.12, 8), (*PAL['parch'][:3], 0.18), lw=0)
    # cast shadow from the left-hand houses
    for j in range(6):
        shadow_w = 1.5 + 0.12 * j
        pts = [PS.p(-STREET_X, 0, zz0), PS.p(-STREET_X + shadow_w, 0, zz0), PS.p(-STREET_X + shadow_w * 1.25, 0, zz1), PS.p(-STREET_X, 0, zz1)]
        set_c(ctx, PAL['ink'], 0.06 + 0.02 * night)
        path_poly(ctx, pts)
        ctx.fill()


def sky_surface(w, h, seed=3, dark=0.0, horizon=0.55, storm=0.0):
    """A painted sky: soft cloud masses from stretched fractal noise, lit from above and shaded below,
    over a gradient that brightens to a haze at the horizon."""
    from core import rgba_to_surface
    hh, ww = int(h), int(w)
    n = fbm2(hh, ww // 3 + 2, seed, scale=max(20, ww / 9), octaves=6)
    from scipy import ndimage
    n = ndimage.zoom(n, (1, ww / n.shape[1]), order=1)[:hh, :ww]
    yy = np.linspace(0, 1, hh)[:, None]
    dens = np.clip((n - 0.42 + 0.25 * storm) * 2.2, 0, 1) * np.clip(1.2 - yy / horizon * 0.9, 0, 1)
    shade = np.clip(np.roll(dens, -int(hh * 0.012), axis=0) - dens, -1, 1)
    top = np.array(mix(PAL['grey2'], PAL['skyd'], dark)[:3])
    bot = np.array(mix(mix(PAL['grey3'], PAL['parch2'], 0.35), PAL['grey2'], dark)[:3])
    g = np.clip(yy / horizon, 0, 1)
    base = top[None, None, :] * (1 - g[..., None]) + bot[None, None, :] * g[..., None]
    lightc = np.array(mix(mix(PAL['parch2'], PAL['grey3'], 0.5), PAL['grey2'], dark * 0.8)[:3])
    darkc = np.array(mix(PAL['grey2'], PAL['charcoal'], 0.35 + 0.5 * dark)[:3])
    cloud = lightc[None, None, :] * (1 - dens[..., None] * 0.6) + darkc[None, None, :] * (dens[..., None] * 0.6)
    cloud = cloud + shade[..., None] * 0.25
    img = base * (1 - dens[..., None] * 0.85) + cloud * dens[..., None] * 0.85
    rgba = np.concatenate([np.clip(img, 0, 1), np.ones((hh, ww, 1))], 2).astype(np.float32)
    surf = rgba_to_surface(rgba)
    ctx = cairo.Context(surf)
    # engraved strokes in the cloud undersides
    rng = np.random.default_rng(seed)
    for i in range(int(ww * hh / 1400)):
        x, y = rng.uniform(0, ww), rng.uniform(0, hh * horizon * 1.05)
        if dens[int(min(y, hh - 1)), int(min(x, ww - 1))] > 0.45 and shade[int(min(y, hh - 1)), int(min(x, ww - 1))] < 0.0:
            L = rng.uniform(10, 34) * ww / 1080
            ink_line(ctx, np.array([[x, y], [x + L, y + rng.uniform(-1, 1)]]), 0.8 * ww / 1080, PAL['ink'], alpha=0.22)
    return surf


def draw_sky(ctx, w, h, seed=3, dark=0.0, hy=950):
    sk = sky_surface(w, h, seed, dark, horizon=hy / h)
    ctx.set_source_surface(sk, 0, 0)
    ctx.paint()
    return


def draw_sky_old(ctx, w, h, seed=3, dark=0.0, hy=950):
    g = cairo.LinearGradient(0, 0, 0, hy + 200)
    top = mix(PAL['grey2'], PAL['skyd'], dark)
    bot = mix(PAL['grey3'], PAL['grey2'], dark)
    g.add_color_stop_rgba(0, *top[:3], 1)
    g.add_color_stop_rgba(1, *bot[:3], 1)
    ctx.set_source(g)
    ctx.paint()
    rng = np.random.default_rng(seed)
    for i in range(8):
        cx, cy = rng.uniform(-100, w + 100), rng.uniform(40, hy * 0.7)
        rw, rh = rng.uniform(220, 420), rng.uniform(30, 60)
        draw_cloud(ctx, cx, cy, rw, rh, seed * 50 + i, dark)


def draw_cloud(ctx, cx, cy, rw, rh, seed, dark=0.0, col=None):
    """An engraved cloud: a chain of round puffs with an inked edge and hatched underside."""
    rng = np.random.default_rng(seed)
    n = 7
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = cx - rw / 2 + rw * t
        r = rh * (0.55 + 0.45 * math.sin(math.pi * t)) * rng.uniform(0.75, 1.1)
        for a in np.linspace(math.pi, 2 * math.pi, 6):
            pts.append((x + r * 0.9 * math.cos(a), cy + r * math.sin(a) * 0.95))
    pts.append((cx + rw / 2 + rh * 0.2, cy + rh * 0.15))
    pts.append((cx - rw / 2 - rh * 0.2, cy + rh * 0.15))
    P = np.array(pts)
    base = col or mix(PAL['grey3'], PAL['parch2'], 0.35)
    base = mix(base, PAL['grey2'], dark)
    ink_shape(ctx, P, (*base[:3], 0.85), lw=0.9, ink=mix(PAL['ink'], base, 0.7), smooth_path=True, seed=seed,
              shadow=(shade_c(base, -0.12), rh * 0.4), hatch=(4.0, 12, 0.6, 0.18), light=(0, -1), line_alpha=0.6)


def draw_cathedral(ctx, x, ground_y, s, fogk=0.6):
    """Strasbourg cathedral's west front with its single north spire (finished 1439), seen far off.
    s = pixels per metre."""
    col = fogmix(mix(PAL['stone'], PAL['burg2'], 0.3), fogk)
    ink = fogmix(PAL['ink'], fogk * 0.85)
    def R(x0, y0, x1, y1, c=col, lw=1.2):
        ink_shape(ctx, np.array([[x + x0 * s, ground_y - y0 * s], [x + x1 * s, ground_y - y0 * s], [x + x1 * s, ground_y - y1 * s],
                                 [x + x0 * s, ground_y - y1 * s]]), c, lw=lw, ink=ink, smooth_path=False)
    # nave roof behind
    ink_shape(ctx, np.array([[x - 30 * s, ground_y - 30 * s], [x + 26 * s, ground_y - 30 * s], [x + 16 * s, ground_y - 48 * s],
                             [x - 22 * s, ground_y - 48 * s]]), fogmix(PAL['roof2'], fogk), lw=1.0, ink=ink, smooth_path=False)
    R(-26, 0, 26, 66)
    # the two west towers to the platform
    R(-24, 66, -6, 72, c=shade_c(col, -0.05))
    R(6, 66, 24, 72, c=shade_c(col, -0.05))
    # north tower octagon and the spire (on the left as seen from the west)
    R(-22, 72, -8, 100)
    ink_shape(ctx, np.array([[x - 22 * s, ground_y - 100 * s], [x - 8 * s, ground_y - 100 * s], [x - 13.5 * s, ground_y - 142 * s],
                             [x - 16.5 * s, ground_y - 142 * s]]), col, lw=1.2, ink=ink, smooth_path=False)
    ink_line(ctx, np.array([[x - 15 * s, ground_y - 142 * s], [x - 15 * s, ground_y - 147 * s]]), 1.4, ink)
    # tracery: the 'harp strings' of the west front, the rose window, portals
    for k in range(18):
        xx = x + (-24 + k * 2.8) * s
        ink_line(ctx, np.array([[xx, ground_y - 12 * s], [xx, ground_y - 64 * s]]), 0.6, ink, alpha=0.55)
    for k in range(9):
        yy = ground_y - (75 + k * 2.6) * s
        ink_line(ctx, np.array([[x - 21 * s, yy], [x - 9 * s, yy]]), 0.5, ink, alpha=0.5)
    for k in range(6):
        t = k / 5
        xa = x + (-22 + 8 * t) * s * 1.0
        ink_line(ctx, np.array([[x - 22 * s + 7 * s * t, ground_y - 100 * s], [x - 15 * s, ground_y - 141 * s]]), 0.5, ink, alpha=0.5)
        _ = xa
    rose = ellipse_pts(x, ground_y - 42 * s, 7.5 * s, 7.5 * s, 24)
    ink_shape(ctx, rose, fogmix(mix(PAL['charcoal2'], PAL['stone'], 0.45), fogk), lw=1.0, ink=ink)
    for a in np.linspace(0, math.pi, 8, endpoint=False):
        ink_line(ctx, np.array([[x + math.cos(a) * 7.5 * s, ground_y - 42 * s + math.sin(a) * 7.5 * s],
                                [x - math.cos(a) * 7.5 * s, ground_y - 42 * s - math.sin(a) * 7.5 * s]]), 0.5, ink, alpha=0.6)
    for px in (-14, 0, 14):
        arch = [[x + (px - 4) * s, ground_y], [x + (px - 4) * s, ground_y - 12 * s], [x + px * s, ground_y - 19 * s],
                [x + (px + 4) * s, ground_y - 12 * s], [x + (px + 4) * s, ground_y]]
        ink_shape(ctx, np.array(arch), fogmix(PAL['charcoal'], fogk * 0.8), lw=1.0, ink=ink, smooth_path=False)


def street_layer(name, z0, z1, scale, with_sky=False, with_cath=False, ground=True, signs=True, crop=None, night=0.0):
    """Render one depth slice of the street to assets/layers/<name>.png at `scale` px per world unit."""
    x0, y0, x1, y1 = crop or (0, 0, W, H)
    surf = new_surface((x1 - x0) * scale, (y1 - y0) * scale)
    ctx = cairo.Context(surf)
    ctx.scale(scale, scale)
    ctx.translate(-x0, -y0)
    if with_sky:
        draw_sky(ctx, W, H, dark=night)
    if with_cath:
        # the end of the street: far roofs and the cathedral above them
        draw_cathedral(ctx, 560, PS.hy + 1375 * 1.6 / 300, 1375 / 300 * 1.0, fogk=0.55 + 0.2 * night)
    if ground:
        draw_ground(ctx, z0, z1, scale, detail=1.0, night=night)
    houses = {s: street_houses(s, 11 if s < 0 else 23) for s in (-1, 1)}
    kinds = ['pretzel', 'shoe', 'key', 'jug']
    allh = [(hs['z0'], s, hs) for s in (-1, 1) for hs in houses[s]]
    for zf, s, hs in sorted(allh, key=lambda q: -q[0]):
        if hs['z1'] < z0 or hs['z0'] > z1:
            continue
        draw_house(ctx, s, hs, z0, z1, scale)
    if signs:
        for zf, s, hs in sorted(allh, key=lambda q: -q[0]):
            if hs['sign']:
                draw_sign(ctx, s, hs, z0, z1, kinds[int(hash01(hs['seed'], 3) * 4)])
    texturize(surf, hash01(len(name), z0) * 1000)
    if crop is not None:
        feather(surf, int(50 * scale))
    os.makedirs(LAYERS, exist_ok=True)
    surf.write_to_png(os.path.join(LAYERS, name + '.png'))
    return surf


def feather(surf, px):
    """Fade the edges of a patch layer to transparent so it blends into the layer beneath."""
    a = surf_array(surf)
    h, w = a.shape[:2]
    yy = np.minimum(np.arange(h), np.arange(h)[::-1])[:, None] / px
    xx = np.minimum(np.arange(w), np.arange(w)[::-1])[None, :] / px
    m = np.clip(np.minimum(yy, xx), 0, 1)
    m = m * m * (3 - 2 * m)
    for ch in range(4):
        a[..., ch] = (a[..., ch] * m).astype(np.uint8)
    surf.mark_dirty()


def texturize(surf, seed=0, amount=0.22, speck=0.5):
    """Give flat vector fills the mottled, printed texture of an aged engraving: low-frequency
    blotches, fine grain and a few ink specks, multiplied into the colour (alpha untouched)."""
    a = surf_array(surf)
    h, w = a.shape[:2]
    n1 = fbm2(h, w, seed=int(seed) % 10000, scale=max(40, w / 14), octaves=5)
    n2 = np.random.default_rng(int(seed) + 1).random((h, w)).astype(np.float32)
    m = (1 - amount) + amount * 1.25 * n1 + 0.06 * (n2 - 0.5)
    m = np.clip(m, 0.55, 1.12)
    sp = (n2 > 1 - 0.0009 * speck)
    for ch in range(3):
        v = a[..., ch].astype(np.float32) * m
        v[sp] *= 0.35
        a[..., ch] = np.minimum(v, a[..., 3]).astype(np.uint8)
    surf.mark_dirty()


def build_street():
    street_layer('street_sky', 300, 301, 1.0, with_sky=True, with_cath=True, ground=False, signs=False)
    street_layer('street_far', 18, 300, 1.25)
    street_layer('street_mid', 7, 18, 1.5)
    street_layer('street_near', 1.0, 7, 2.0)
    # a high-resolution patch of cobbles around the first dancer, for the opening close-up
    street_layer('street_patch', 2.6, 6.2, 4.5, ground=True, signs=False, crop=(250, 1330, 830, 1760))


SETS = {'street': build_street}

if __name__ == '__main__':
    which = sys.argv[1:] or list(SETS)
    for k in which:
        SETS[k]()
        print('built', k)
