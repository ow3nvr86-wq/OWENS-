"""Drawing functions for the world of Roanoke Island, 1587-1590, all as flat 2D ink illustration:
loblolly pines, live oaks hung with Spanish moss, palmetto and marsh grass, the palisade and its carved
post, English timber-framed cottages that rise stage by stage, Elizabethan ships, boats, an engraved sea,
chests, barrels and a campfire. Units: world units (an adult is about 170 tall, about 100 units a metre).
"""
import math

import cairo
import numpy as np

from core import (PAL, ink_shape, ink_line, taper_stroke, hatch_lines, set_c, mix, shade_c, hash01, vnoise,
                  fnoise, ellipse_pts, soft_glow, path_smooth, path_poly, clamp, smooth)


def fogc(c, k, fog=None):
    return mix(c, fog or PAL['grey3'], k)


def R(ctx, x0, y0, x1, y1, fill, lw=1.2, ink=None, shadow=None, hatch=None, seed=0, boil=0.3):
    ink_shape(ctx, np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float), fill, lw=lw, ink=ink, smooth_path=False,
              shadow=shadow, hatch=hatch, seed=seed, boil=boil)


# ----------------------------------------------------------------------------------------------
# Trees and plants
# ----------------------------------------------------------------------------------------------
def pine(ctx, x, gy, h, seed, fog=0.0, fogcol=None, lw=1.2, sway=0.0, detail=True):
    """A loblolly pine: a tall straight trunk, bare below, with a high irregular crown of needle tufts."""
    rng = np.random.default_rng(seed)
    trunk = mix(PAL['wood2'], PAL['charcoal'], 0.3)
    green = mix(PAL['green3'], PAL['charcoal'], 0.25 + 0.2 * rng.random())
    trunk, green = fogc(trunk, fog, fogcol), fogc(green, fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    tw = h * (0.022 + 0.008 * rng.random())
    top = (x + sway * h * 0.04, gy - h)
    lean = rng.uniform(-0.03, 0.03) * h
    pts = [[x - tw, gy], [x - tw * 0.55 + lean * 0.5, gy - h * 0.5], [top[0] - tw * 0.2 + lean, top[1]],
           [top[0] + tw * 0.2 + lean, top[1]], [x + tw * 0.55 + lean * 0.5, gy - h * 0.5], [x + tw, gy]]
    ink_shape(ctx, np.array(pts), trunk, lw=lw, ink=inkc, seed=seed, shadow=(shade_c(trunk, -0.35), tw * 0.7),
              hatch=(max(2.0, tw * 0.35), 80, max(0.5, lw * 0.5), 0.35) if detail else None, light=(-1, 0))
    # a few dead side branches low on the trunk
    for k in range(int(rng.integers(1, 4))):
        yy = gy - h * rng.uniform(0.35, 0.6)
        sd = 1 if rng.random() < 0.5 else -1
        ink_line(ctx, np.array([[x + lean * 0.4, yy], [x + sd * h * 0.06, yy - h * 0.03]]), max(0.8, lw * 0.8), inkc)
    # crown: clumps of needles on short branches
    n = int(rng.integers(6, 10))
    for k in range(n):
        fy = rng.uniform(0.0, 0.33)
        cy = top[1] + h * fy
        sd = rng.uniform(-1, 1)
        cx = top[0] + lean + sd * h * (0.05 + 0.13 * fy * 2.2)
        rw, rh = h * rng.uniform(0.055, 0.09), h * rng.uniform(0.028, 0.045)
        bx = top[0] + lean * (1 - fy)
        ink_line(ctx, np.array([[bx, cy + rh * 0.5], [cx, cy]]), max(0.8, lw * 0.9), inkc)
        P = []
        m = 34
        for i in range(m):
            a = 2 * math.pi * i / m
            rr = 1 + 0.22 * vnoise(i * 0.7 + seed + k * 7, 5)
            spike = 0.32 if (i % 2 and math.sin(a) > -0.3) else 0.0
            P.append([cx + math.cos(a) * rw * (rr + spike * 0.4), cy + math.sin(a) * rh * (rr + spike) - (rh * 0.3 if math.sin(a) < 0 else 0)])
        ink_shape(ctx, np.array(P), green, lw=lw, ink=inkc, seed=seed * 13 + k, smooth_path=False,
                  shadow=(shade_c(green, -0.38), rh * 0.55), hatch=(max(2.0, rh * 0.22), 20, max(0.4, lw * 0.45), 0.4) if detail else None,
                  light=(0, -1))
        if detail:
            for j in range(5):
                a = rng.uniform(math.pi * 0.1, math.pi * 0.9)
                q = (cx + math.cos(a) * rw * 0.9, cy + math.sin(a) * rh * 0.9)
                ink_line(ctx, np.array([q, (q[0] + rng.uniform(-3, 3), q[1] + rh * 0.5)]), max(0.5, lw * 0.5), inkc, alpha=0.7)


def oak(ctx, x, gy, h, seed, fog=0.0, fogcol=None, lw=1.3, moss=True, detail=True, bare=0.0):
    """A live oak: a thick, leaning, twisting trunk, long spreading limbs and dense rounded leaf masses,
    hung with grey Spanish moss. bare > 0 thins the crown (late autumn and winter)."""
    rng = np.random.default_rng(seed)
    trunk = fogc(mix(PAL['wood2'], PAL['charcoal2'], 0.4), fog, fogcol)
    green = fogc(mix(PAL['green3'], PAL['green'], rng.random() * 0.5), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    mossc = fogc(mix(PAL['grey'], PAL['green2'], 0.35), fog, fogcol)
    tw = h * 0.07
    lean = rng.uniform(-0.12, 0.12) * h
    fork = (x + lean, gy - h * 0.42)
    pts = [[x - tw * 1.5, gy + 2], [x - tw * 0.9, gy - h * 0.12], [fork[0] - tw * 0.8, fork[1]], [fork[0] + tw * 0.8, fork[1] - tw * 0.3],
           [x + tw * 0.8, gy - h * 0.15], [x + tw * 1.6, gy + 2]]
    ink_shape(ctx, np.array(pts), trunk, lw=lw * 1.2, ink=inkc, seed=seed, shadow=(shade_c(trunk, -0.35), tw * 0.8),
              hatch=(max(2.0, tw * 0.18), 75, max(0.5, lw * 0.5), 0.4) if detail else None, light=(-1, -0.3))
    limbs = []
    for k in range(int(rng.integers(4, 7))):
        a = rng.uniform(-1.35, 1.35)
        L = h * rng.uniform(0.35, 0.62)
        ex = fork[0] + math.sin(a) * L
        ey = fork[1] - math.cos(a) * L * 0.75
        mid = (fork[0] + math.sin(a) * L * 0.5 + rng.uniform(-0.05, 0.05) * h, fork[1] - math.cos(a) * L * 0.5 + h * 0.06)
        taper_stroke(ctx, [fork, mid, (ex, ey)], tw * 1.0, tw * 0.25, inkc, seed + k)
        taper_stroke(ctx, [fork, mid, (ex, ey)], tw * 0.75, tw * 0.15, trunk, seed + k)
        limbs.append((ex, ey))
    if bare < 0.95:
        for k, (ex, ey) in enumerate(limbs):
            for j in range(3):
                cx, cy = ex + rng.uniform(-0.14, 0.14) * h, ey + rng.uniform(-0.06, 0.06) * h
                rw, rh = h * rng.uniform(0.18, 0.27) * (1 - bare * 0.6), h * rng.uniform(0.11, 0.16) * (1 - bare * 0.6)
                P = []
                m = 44
                for i in range(m):
                    a = 2 * math.pi * i / m
                    rr = 1 + 0.16 * vnoise(i * 0.6 + seed * 3 + k * 5 + j, 9) + 0.07 * abs(math.sin(a * 9 + j))
                    P.append([cx + math.cos(a) * rw * rr, cy + math.sin(a) * rh * rr * (0.7 if math.sin(a) > 0 else 1.0)])
                g = green if bare < 0.3 else mix(green, PAL['brown2'], min(1, bare * 1.2))
                ink_shape(ctx, np.array(P), (*g[:3], 1.0 - bare * 0.5), lw=lw, ink=inkc, seed=seed * 7 + k * 3 + j,
                          shadow=(shade_c(g, -0.4), rh * 0.45), hatch=(max(2.0, rh * 0.16), 25, max(0.4, lw * 0.45), 0.4) if detail else None,
                          light=(0, -1), line_alpha=1.0 - bare * 0.5)
    if moss:
        for k, (ex, ey) in enumerate(limbs):
            for j in range(4):
                u = rng.uniform(0.3, 1.0)
                bx = fork[0] + (ex - fork[0]) * u
                by = fork[1] + (ey - fork[1]) * u + h * 0.03
                L = h * rng.uniform(0.07, 0.18)
                taper_stroke(ctx, [(bx, by), (bx + L * 0.08, by + L * 0.5), (bx - L * 0.05, by + L)], L * 0.12, 0.5, mossc, seed + k * 9 + j,
                             alpha=0.85)


def moss_strand(ctx, x, y, L, t, seed, col=None, w=None, alpha=0.9):
    """One hanging strand of Spanish moss that sways in the air (drawn every frame)."""
    col = col or mix(PAL['grey'], PAL['green2'], 0.35)
    ph = t * 0.9 + hash01(seed, 1) * 10
    pts = []
    for i in range(7):
        u = i / 6
        sw = (math.sin(ph + u * 2.2) * 0.07 + 0.03 * math.sin(ph * 2.3 + u * 4)) * L * u
        pts.append((x + sw, y + L * u))
    taper_stroke(ctx, pts, w or L * 0.09, 0.6, col, seed, alpha=alpha)
    for k in range(3):
        u = 0.35 + 0.2 * k
        q = pts[int(u * 6)]
        taper_stroke(ctx, [q, (q[0] + L * 0.06 * (1 if k % 2 else -1), q[1] + L * 0.18)], (w or L * 0.09) * 0.5, 0.4, col, seed + k, alpha=alpha * 0.8)


def palmetto(ctx, x, gy, s, seed, fog=0.0, fogcol=None, lw=1.0):
    """A dwarf palmetto: a fan of stiff, split leaves."""
    rng = np.random.default_rng(seed)
    g = fogc(mix(PAL['green3'], PAL['green2'], 0.3), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.8, fogcol)
    for k in range(int(rng.integers(3, 6))):
        a = rng.uniform(-1.1, 1.1)
        L = s * rng.uniform(40, 62)
        cx, cy = x + math.sin(a) * L, gy - math.cos(a) * L * 0.8
        ink_line(ctx, np.array([[x, gy], [cx, cy]]), max(0.6, lw * 0.8), inkc)
        pts = [[cx, cy]]
        for i in range(9):
            b = a - 0.9 + 1.8 * i / 8
            rr = s * (20 + 4 * (i % 2))
            pts.append([cx + math.sin(b) * rr, cy - math.cos(b) * rr * 0.85])
        ink_shape(ctx, np.array(pts), g, lw=lw, ink=inkc, smooth_path=False, seed=seed + k, shadow=(shade_c(g, -0.35), s * 4))
        for i in range(9):
            b = a - 0.9 + 1.8 * i / 8
            ink_line(ctx, np.array([[cx, cy], [cx + math.sin(b) * s * 18, cy - math.cos(b) * s * 15]]), max(0.4, lw * 0.4), inkc, alpha=0.6)


def grass_tufts(ctx, x0, x1, gy, n, s, seed, col=None, fog=0.0, fogcol=None, t=0.0, wind=0.0, alpha=1.0):
    """Marsh grass and weeds: tapering blades, optionally swaying."""
    rng = np.random.default_rng(seed)
    col = fogc(col or mix(PAL['green3'], PAL['parch3'], 0.25), fog, fogcol)
    for i in range(n):
        x = rng.uniform(x0, x1)
        y = gy + rng.uniform(-3, 3) * s
        for k in range(int(rng.integers(3, 7))):
            L = s * rng.uniform(14, 34)
            a = rng.uniform(-0.5, 0.5) + wind * (0.15 + 0.1 * math.sin(t * 2.1 + x * 0.01 + k))
            tip = (x + math.sin(a) * L, y - math.cos(a) * L)
            mid = (x + math.sin(a * 0.5) * L * 0.5, y - math.cos(a * 0.5) * L * 0.5)
            taper_stroke(ctx, [(x + k * s * 0.8, y), mid, tip], s * 1.6, 0.3, col, seed + i * 7 + k, alpha=alpha)


def fern(ctx, x, gy, s, seed, col=None):
    rng = np.random.default_rng(seed)
    col = col or mix(PAL['green3'], PAL['green'], 0.4)
    for k in range(5):
        a = -1.0 + k * 0.5 + rng.uniform(-0.15, 0.15)
        L = s * rng.uniform(30, 48)
        pts = [(x + math.sin(a) * L * u + math.sin(u * 2.5) * L * 0.1 * math.copysign(1, a), gy - math.cos(a) * L * u * 0.8 + L * 0.25 * u * u)
               for u in np.linspace(0, 1, 8)]
        ink_line(ctx, np.array(pts), max(0.5, s * 0.8), PAL['ink'])
        for i in range(1, 7):
            q = pts[i]
            for sg in (-1, 1):
                taper_stroke(ctx, [q, (q[0] + sg * s * 7 * (1 - i / 8), q[1] - s * 3)], s * 2.2, 0.3, col, seed + i * sg + k)


# ----------------------------------------------------------------------------------------------
# The palisade and the carved post
# ----------------------------------------------------------------------------------------------
def palisade(ctx, x0, x1, gy, h, seed, gap=None, fog=0.0, fogcol=None, lw=1.3, decay=0.0, logw=34.0):
    """A wall of upright logs with sharpened tops and a lashed rail. gap = (xa, xb) leaves an entrance.
    decay > 0 leans and drops some logs (weathered, abandoned)."""
    rng = np.random.default_rng(seed)
    wood = fogc(mix(PAL['wood'], PAL['grey2'], 0.25 + 0.25 * decay), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    x = x0
    k = 0
    while x < x1:
        w = logw * rng.uniform(0.85, 1.15)
        if gap and gap[0] < x + w * 0.5 < gap[1]:
            x += w
            continue
        hh = h * rng.uniform(0.9, 1.06)
        if decay > 0 and rng.random() < 0.18 * decay:
            hh *= rng.uniform(0.45, 0.75)       # a broken, rotted log
        tilt = rng.uniform(-0.02, 0.02) + (rng.uniform(-0.08, 0.08) if decay > 0 and rng.random() < 0.3 * decay else 0)
        top = gy - hh
        cx = x + w / 2 + tilt * hh
        pts = [[x, gy + 4], [x + tilt * hh, top + w * 0.6], [cx, top], [x + w + tilt * hh, top + w * 0.6], [x + w, gy + 4]]
        c = shade_c(wood, rng.uniform(-0.12, 0.08))
        ink_shape(ctx, np.array(pts), c, lw=lw, ink=inkc, smooth_path=False, seed=seed + k,
                  shadow=(shade_c(c, -0.35), w * 0.32), hatch=(max(2.0, w * 0.12), 82, max(0.4, lw * 0.4), 0.35), light=(-1, 0))
        # grain and knots
        for j in range(3):
            gx = x + w * rng.uniform(0.25, 0.75)
            ink_line(ctx, np.array([[gx, gy - hh * rng.uniform(0.05, 0.3)], [gx + tilt * hh * 0.5, gy - hh * rng.uniform(0.5, 0.85)]]),
                     max(0.4, lw * 0.4), inkc, alpha=0.45)
        x += w
        k += 1
    # the lashed rail
    for ry in (gy - h * 0.62, gy - h * 0.22):
        segs = [(x0, x1)] if not gap else [(x0, gap[0]), (gap[1], x1)]
        for a, b in segs:
            if b - a < 10:
                continue
            ink_shape(ctx, np.array([[a, ry - 5], [b, ry - 7], [b, ry + 5], [a, ry + 6]]), shade_c(wood, -0.2), lw=lw, ink=inkc,
                      smooth_path=False, seed=seed + int(ry))


# Roman capitals as carving strokes, in a unit box (x 0..w, y 0..1, y down)
def _arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a)), cy - ry * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


LETTERS = {
    'C': (0.8, [_arc(0.48, 0.5, 0.42, 0.5, 48, 312, 18)]),
    'R': (0.76, [[(0.12, 0.0), (0.12, 1.0)], [(0.12, 0.02)] + _arc(0.42, 0.26, 0.3, 0.24, 90, -90, 10) + [(0.12, 0.5)], [(0.38, 0.5), (0.74, 1.0)]]),
    'O': (0.9, [_arc(0.45, 0.5, 0.43, 0.5, 0, 360, 24)]),
    'A': (0.92, [[(0.02, 1.0), (0.46, 0.0), (0.9, 1.0)], [(0.22, 0.62), (0.7, 0.62)]]),
    'T': (0.94, [[(-0.02, 0.02), (0.94, 0.02)], [(0.46, 0.04), (0.46, 0.5), (0.46, 1.0)], [(0.33, 1.0), (0.59, 1.0)]]),
    'N': (0.84, [[(0.08, 1.0), (0.08, 0.0), (0.76, 1.0), (0.76, 0.0)]]),
}


def carve_word(ctx, word, x, y, hgt, seed, reveal=1.0, wood=None, track=0.17, curve=0.0):
    """Cut a word into wood as V-grooves: a pale rim of fresh-cut wood, the dark groove, and the lit far
    wall of the cut. x, y = centre of the word; hgt = letter height. reveal (0..1) cuts the letters in order."""
    wood = wood or PAL['wood3']
    total = sum(LETTERS[ch][0] for ch in word) * hgt + track * hgt * (len(word) - 1)
    cx = x - total / 2
    g = hgt * 0.2
    nlet = len(word)
    for i, ch in enumerate(word):
        lw_, strokes = LETTERS[ch]
        u = clamp(reveal * nlet - i)
        if u <= 0:
            break
        for k, st in enumerate(strokes):
            pts = [(cx + (px + 0.025 * vnoise(seed + i * 5 + k + j * 0.5, 3)) * hgt,
                    y - hgt / 2 + (py + 0.02 * vnoise(seed * 2 + i + j * 0.5, 4)) * hgt) for j, (px, py) in enumerate(st)]
            if curve:
                pts = [(px, py + curve * ((px - x) / max(total, 1)) ** 2 * hgt) for px, py in pts]
            n = max(2, int(len(pts) * u + 0.999))
            P = np.array(pts[:n])
            sm = len(P) > 4
            ink_line(ctx, P, g * 1.6, mix(PAL['parch2'], wood, 0.45), seed + i, smooth_path=sm, alpha=0.45)
            ink_line(ctx, P, g * 1.2, shade_c(wood, -0.75), seed + i, smooth_path=sm)
            ink_line(ctx, P + np.array([g * 0.25, g * 0.28]), g * 0.38, mix(wood, PAL['parch2'], 0.1), seed + i, smooth_path=sm, alpha=0.7)
            # serifs on the ends of upright strokes
            if len(st) == 2 and u >= 1 and abs(st[0][0] - st[1][0]) < 0.05:
                for q in (P[0], P[-1]):
                    ink_line(ctx, np.array([[q[0] - g * 1.3, q[1]], [q[0] + g * 1.3, q[1]]]), g * 0.75, shade_c(wood, -0.7), seed, smooth_path=False)
        cx += (lw_ + track) * hgt
    return total


def carved_post(ctx, x, gy, w, h, seed, reveal=1.0, light=0.0, fog=0.0, fogcol=None, lw=1.6, word='CROATOAN', ghost_cross=0.0, band=True):
    """The great post at the right of the entrance: bark stripped off for a stretch, 'five foot from the
    ground', and the word cut into it in fair capital letters."""
    rng = np.random.default_rng(seed)
    bark = fogc(mix(PAL['wood2'], PAL['charcoal2'], 0.35), fog, fogcol)
    heart = fogc(mix(PAL['wood3'], PAL['parch3'], 0.35), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.8, fogcol)
    top = gy - h
    body = [[x - w / 2, gy + 4], [x - w / 2 + 2, top + w * 0.4], [x, top], [x + w / 2 - 2, top + w * 0.4], [x + w / 2, gy + 4]]
    ink_shape(ctx, np.array(body), bark, lw=lw, ink=inkc, smooth_path=False, seed=seed)
    # the stripped band (about 1.2 to 1.9 m up), as a lighter cylinder
    y0, y1 = gy - 196, gy - 112
    for side in ((0,) if band else ()):
        ctx.save()
        ctx.rectangle(x - w / 2 - 2, y0, w + 4, y1 - y0)
        ctx.clip()
        pts = [[x - w / 2 + 2, y0 + 4], [x - w / 4, y0 - 3], [x + w / 4, y0 + 3], [x + w / 2 - 2, y0 - 2],
               [x + w / 2 - 2, y1 + 2], [x + w / 4, y1 + 5], [x - w / 4, y1 - 2], [x - w / 2 + 2, y1 + 3]]
        ink_shape(ctx, np.array(pts), heart, lw=lw * 0.8, ink=inkc, seed=seed + 1)
        ctx.restore()
    # cylinder shading across the whole post
    g = cairo.LinearGradient(x - w / 2, 0, x + w / 2, 0)
    g.add_color_stop_rgba(0.0, 0, 0, 0, 0.55)
    g.add_color_stop_rgba(0.28, 0, 0, 0, 0.0)
    g.add_color_stop_rgba(0.45, 1, 0.95, 0.85, 0.10 + 0.25 * light)
    g.add_color_stop_rgba(0.7, 0, 0, 0, 0.12)
    g.add_color_stop_rgba(1.0, 0, 0, 0, 0.6)
    ctx.save()
    path_poly(ctx, np.array(body))
    ctx.clip()
    ctx.set_source(g)
    ctx.paint()
    # bark furrows above and below the band
    for k in range(int(w / 6)):
        bx = x - w / 2 + 4 + k * 6 + rng.uniform(-1.5, 1.5)
        for (a, b) in (((top + 20, y0 - 4), (y1 + 6, gy)) if band else ((top + 20, gy),)):
            yy = a
            while yy < b:
                L = rng.uniform(14, 40)
                ink_line(ctx, np.array([[bx, yy], [bx + rng.uniform(-1.5, 1.5), min(b, yy + L)]]), max(0.5, lw * 0.45), inkc, alpha=0.6)
                yy += L + rng.uniform(4, 12)
    # adze marks on the stripped wood
    for k in range(10):
        ax = x + rng.uniform(-0.4, 0.4) * w
        ay = rng.uniform(y0 + 6, y1 - 6)
        ink_line(ctx, np.array([[ax - 5, ay], [ax + 5, ay + rng.uniform(-1, 1)]]), 0.6, inkc, alpha=0.3)
    ctx.restore()
    if word:
        carve_word(ctx, word, x + 1, gy - 152, 10.8, seed + 3, reveal, heart, curve=1.5)
    if ghost_cross > 0.01:
        # the agreed sign of distress that was NOT there: a cross over the letters, shown as a faint ghost
        ctx.save()
        ctx.set_dash([3.0, 2.4])
        set_c(ctx, PAL['burg2'], 0.85 * ghost_cross)
        ctx.set_line_width(2.2)
        cxx, cyy, rr = x + 1, gy - 152, 26
        ctx.move_to(cxx, cyy - rr)
        ctx.line_to(cxx, cyy + rr)
        ctx.move_to(cxx - rr * 0.8, cyy - rr * 0.25)
        ctx.line_to(cxx + rr * 0.8, cyy - rr * 0.25)
        ctx.stroke()
        ctx.restore()


# ----------------------------------------------------------------------------------------------
# An English timber-framed cottage (a reconstruction), built stage by stage
# ----------------------------------------------------------------------------------------------
def cottage(ctx, x, gy, w, h, seed, stage=1.0, fog=0.0, fogcol=None, lw=1.3, smoke_t=None, lit=0.0, snow=0.0):
    """x: centre. stage 0..1: posts rise (0-0.25), beams and rafters (0.25-0.45), wattle-and-daub walls
    (0.45-0.7), thatch laid from the eaves up (0.7-1.0)."""
    rng = np.random.default_rng(seed)
    wood = fogc(mix(PAL['wood'], PAL['wood2'], 0.4), fog, fogcol)
    daub = fogc(mix(PAL['plaster'], PAL['parch3'], 0.4), fog, fogcol)
    thatch = fogc(mix(PAL['parch3'], PAL['brown3'], 0.45), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    x0, x1 = x - w / 2, x + w / 2
    eave = gy - h
    ridge = eave - h * 0.95
    nposts = 4
    pw = w * 0.045
    s1 = clamp(stage / 0.25)
    s2 = clamp((stage - 0.25) / 0.2)
    s3 = clamp((stage - 0.45) / 0.25)
    s4 = clamp((stage - 0.7) / 0.3)
    # walls: wattle panels, then daub
    if s3 > 0:
        for i in range(nposts - 1):
            a = x0 + (w - pw) * i / (nposts - 1) + pw
            b = x0 + (w - pw) * (i + 1) / (nposts - 1)
            u = clamp(s3 * (nposts - 1) - i)
            if u <= 0:
                continue
            top = gy - (gy - eave) * u
            ink_shape(ctx, np.array([[a, gy], [b, gy], [b, top], [a, top]]), daub if u >= 1 else shade_c(daub, -0.15), lw=lw * 0.8,
                      ink=inkc, smooth_path=False, seed=seed + i, shadow=(shade_c(daub, -0.22), w * 0.02))
            if u < 1 or stage < 0.62:
                for k in range(int((gy - top) / 9)):        # woven wattle showing before the daub
                    yy = gy - 5 - k * 9
                    ink_line(ctx, np.array([[a, yy], [(a + b) / 2, yy - 3], [b, yy]]), max(0.5, lw * 0.5), inkc, alpha=0.5)
        if s3 >= 1:
            # door and a small shuttered window
            dx = x0 + w * 0.42
            ink_shape(ctx, np.array([[dx, gy], [dx + w * 0.16, gy], [dx + w * 0.16, gy - h * 0.72], [dx, gy - h * 0.72]]),
                      shade_c(wood, -0.25), lw=lw, ink=inkc, smooth_path=False, seed=seed + 50)
            wx = x0 + w * 0.73
            win = [[wx, gy - h * 0.62], [wx + w * 0.12, gy - h * 0.62], [wx + w * 0.12, gy - h * 0.38], [wx, gy - h * 0.38]]
            ink_shape(ctx, np.array(win), mix(PAL['charcoal'], PAL['candle'], lit), lw=lw, ink=inkc, smooth_path=False, seed=seed + 51)
            if lit > 0:
                soft_glow(ctx, wx + w * 0.06, gy - h * 0.5, w * 0.25, PAL['candle'], 0.4 * lit)
    # posts
    for i in range(nposts):
        px = x0 + (w - pw) * i / (nposts - 1)
        u = clamp(s1 * nposts - i)
        if u <= 0:
            continue
        top = gy - (gy - eave) * smooth(u)
        ink_shape(ctx, np.array([[px, gy + 2], [px + pw, gy + 2], [px + pw, top], [px, top]]), wood, lw=lw, ink=inkc,
                  smooth_path=False, seed=seed + 10 + i, shadow=(shade_c(wood, -0.35), pw * 0.4))
    # wall plate and rafters
    if s2 > 0:
        pl = x0 + w * s2
        ink_shape(ctx, np.array([[x0 - 4, eave - 6], [pl + 4, eave - 6], [pl + 4, eave + 2], [x0 - 4, eave + 2]]), wood, lw=lw, ink=inkc,
                  smooth_path=False, seed=seed + 20)
        nr = 7
        for i in range(nr):
            u = clamp(s2 * nr - i)
            if u <= 0:
                continue
            rx = x0 + w * i / (nr - 1)
            top = (x + (rx - x) * 0.15, ridge)
            end = (rx + (top[0] - rx) * u, eave + (ridge - eave) * u)
            ink_line(ctx, np.array([[rx, eave], end]), max(1.0, pw * 0.45), wood)
            ink_line(ctx, np.array([[rx, eave], end]), max(0.5, lw * 0.6), inkc, alpha=0.6)
    # thatch, laid in courses from the eaves to the ridge
    if s4 > 0:
        ov = w * 0.1
        ncourse = 6
        for i in range(ncourse):
            u = clamp(s4 * ncourse - i)
            if u <= 0:
                continue
            ya = eave + 8 - (eave - ridge) * i / ncourse
            yb = eave + 8 - (eave - ridge) * (i + 1) / ncourse - 6
            fa = (ya - ridge) / (eave - ridge + 1e-6)
            fb = max(0.0, (yb - ridge) / (eave - ridge + 1e-6))
            ha = (w / 2 + ov) * fa + w * 0.04
            hb = (w / 2 + ov) * fb + w * 0.04
            xa0 = x - ha
            xa1 = x - ha + 2 * ha * u
            pts = [[xa0, ya], [xa1, ya], [min(xa1, x + hb), yb], [x - hb, yb]]
            c = shade_c(thatch, -0.06 * (i % 2))
            ink_shape(ctx, np.array(pts), c, lw=lw, ink=inkc, smooth_path=False, seed=seed + 30 + i,
                      shadow=(shade_c(c, -0.25), 5), hatch=(3.0, 95, max(0.4, lw * 0.4), 0.45), light=(0, -1))
            if snow > 0:
                ink_shape(ctx, np.array([[xa0 + 4, yb + 4], [min(xa1, x + hb) - 2, yb + 4], [min(xa1, x + hb) - 6, yb + 4 + 6 * snow],
                                         [x - hb, yb + 4 + 7 * snow]]), (*PAL['linen'][:3], 0.92 * snow), lw=0, seed=seed + i)
        if s4 >= 1:
            ink_line(ctx, np.array([[x - w * 0.06, ridge - 2], [x + w * 0.06, ridge - 2]]), 5, shade_c(thatch, -0.3))
    if smoke_t is not None and s4 >= 1:
        from props import smoke
        smoke(ctx, x + w * 0.18, ridge + 18, w / 160, smoke_t, seed, 0.45)


def ruin(ctx, x, gy, w, h, seed, fog=0.0, fogcol=None, lw=1.2):
    """The place where a house stood, 'taken down': a few posts left, timbers in the grass."""
    rng = np.random.default_rng(seed)
    wood = fogc(mix(PAL['wood'], PAL['grey2'], 0.35), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    for i in range(int(rng.integers(1, 3))):
        px = x - w / 2 + rng.uniform(0, w)
        ph = h * rng.uniform(0.35, 0.9)
        tl = rng.uniform(-0.18, 0.18)
        ink_shape(ctx, np.array([[px, gy + 2], [px + w * 0.05, gy + 2], [px + w * 0.05 + tl * ph, gy - ph], [px + tl * ph, gy - ph]]), wood,
                  lw=lw, ink=inkc, smooth_path=False, seed=seed + i, shadow=(shade_c(wood, -0.35), 4))
    for i in range(3):
        a = x - w / 2 + rng.uniform(0, w * 0.6)
        L = w * rng.uniform(0.4, 0.8)
        yy = gy - rng.uniform(0, 6)
        ink_shape(ctx, np.array([[a, yy - 5], [a + L, yy - 8], [a + L, yy], [a, yy + 1]]), shade_c(wood, -0.1), lw=lw, ink=inkc,
                  smooth_path=False, seed=seed + 10 + i)


# ----------------------------------------------------------------------------------------------
# Ships, boats and the sea
# ----------------------------------------------------------------------------------------------
def ship(ctx, x, y, s, t, seed=0, kind='galleon', roll=0.0, sail=1.0, fog=0.0, fogcol=None, lw=1.4, night=0.0, flag=True, lantern=0.0):
    """An Elizabethan ship in side elevation, bow to the right. (x, y) = midships at the waterline,
    s = scale (a galleon is about 320 units long at s = 1). Sails billow, pennants stream, the hull rolls."""
    rng = np.random.default_rng(seed)
    wood = fogc(mix(PAL['wood'], PAL['wood2'], 0.35), fog, fogcol)
    wood_d = fogc(shade_c(PAL['wood2'], -0.3), fog, fogcol)
    canvas = fogc(mix(PAL['parch2'], PAL['linen2'], 0.3), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    small = kind == 'pinnace'
    L = 200 if small else 320
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.rotate(roll)
    lws = lw / max(s, 0.05)
    hl = L / 2
    hull = [[-hl * 0.92, -48 if not small else -26], [-hl * 0.78, -54 if not small else -28], [-hl * 0.62, -40 if not small else -22],
            [hl * 0.45, -24 if not small else -16], [hl * 0.7, -34 if not small else -20], [hl * 0.88, -36 if not small else -20],
            [hl * 0.98, -20], [hl * 0.8, 6], [hl * 0.45, 14], [-hl * 0.5, 14], [-hl * 0.86, 4], [-hl * 0.95, -14]]
    ink_shape(ctx, np.array(hull), wood, lw=lws * 1.2, ink=inkc, smooth_path=False, seed=seed,
              shadow=(shade_c(wood, -0.4), 7), hatch=(3.0, 8, lws * 0.5, 0.35), light=(0, -1))
    # wales and gun-ports
    for k, yy in enumerate((-12, -2) if not small else (-6,)):
        ink_line(ctx, np.array([[-hl * 0.9, yy - 6], [0, yy + 2], [hl * 0.85, yy - 4]]), lws * 2.4, wood_d)
    if not small:
        for k in range(6):
            gx = -hl * 0.45 + k * hl * 0.17
            R(ctx, gx, -22, gx + 9, -14, wood_d, lw=lws * 0.8, ink=inkc, seed=seed + k)
        # stern lantern
        if lantern > 0:
            soft_glow(ctx, -hl * 0.9, -62, 40, PAL['candle'], 0.5 * lantern)
            soft_glow(ctx, -hl * 0.9, -62, 8, PAL['candle2'], 0.9 * lantern)
    # beakhead and bowsprit
    ink_line(ctx, np.array([[hl * 0.92, -28], [hl * 1.32, -70]]), lws * 3.0, wood_d)
    masts = [(hl * 0.42, 210, 0.95), (-hl * 0.05, 245, 1.0), (-hl * 0.55, 165, 0.7)] if not small else [(hl * 0.25, 150, 0.9), (-hl * 0.3, 120, 0.7)]
    flap = math.sin(t * 2.1 + seed)
    for mi, (mx, mh, sk) in enumerate(masts):
        base_y = -28 if mi != 2 else -40
        top = base_y - mh
        ink_line(ctx, np.array([[mx, base_y], [mx, top]]), lws * 3.2, wood_d)
        # shrouds
        for k in range(4):
            ink_line(ctx, np.array([[mx - 14 - k * 5, -26], [mx, top + mh * 0.45]]), lws * 0.6, inkc, alpha=0.55)
        ink_line(ctx, np.array([[mx, top], [mx + (hl * 0.6 if mi == 0 else hl * 0.45), -30]]), lws * 0.6, inkc, alpha=0.5)
        is_lateen = (mi == 2 and not small) or (mi == 1 and small)
        if sail > 0.01:
            if is_lateen:
                a = (mx - 60 * sk, base_y - mh * 0.25)
                b = (mx + 50 * sk, base_y - mh * 0.95)
                ink_line(ctx, np.array([a, b]), lws * 2.0, wood_d)
                bil = 12 * sail * (1 + 0.1 * flap)
                pts = [a, ((a[0] + b[0]) / 2 + bil, (a[1] + b[1]) / 2 + bil * 0.2), b, (mx + 2, base_y - mh * 0.25)]
                ink_shape(ctx, np.array(pts), canvas, lw=lws, ink=inkc, seed=seed + mi, shadow=(shade_c(canvas, -0.25), 6), light=(-1, 0))
            else:
                for si, (fy0, fy1, wd) in enumerate(((0.1, 0.42, 62), (0.47, 0.8, 74))):
                    y0_, y1_ = top + mh * fy0, top + mh * fy1
                    wd *= sk * (0.7 if small else 1.0)
                    ink_line(ctx, np.array([[mx - wd, y0_], [mx + wd, y0_]]), lws * 2.0, wood_d)
                    bil = (16 + 3 * flap) * sail * (1 if si else 0.8)
                    hh = (y1_ - y0_) * sail
                    pts = [[mx - wd, y0_], [mx + wd, y0_], [mx + wd + bil * 0.5, y0_ + hh * 0.5], [mx + wd * 0.9, y0_ + hh],
                           [mx, y0_ + hh + bil * 0.3], [mx - wd * 0.9, y0_ + hh], [mx - wd + bil * 0.5, y0_ + hh * 0.5]]
                    ink_shape(ctx, np.array(pts), canvas, lw=lws, ink=inkc, seed=seed + mi * 3 + si,
                              shadow=(shade_c(canvas, -0.28), wd * 0.25), hatch=(3.2, 90, lws * 0.45, 0.3), light=(-1, 0))
                    for k in (-0.5, 0.0, 0.5):
                        ink_line(ctx, np.array([[mx + wd * k, y0_ + 2], [mx + wd * k + bil * 0.25, y0_ + hh - 3]]), lws * 0.5, inkc, alpha=0.35)
            if mi == 1 and not small and sail > 0.3:
                # the cross of St George on the mainsail
                cy_ = top + mh * 0.63
                ink_line(ctx, np.array([[mx + 10, cy_ - 20], [mx + 12, cy_ + 20]]), lws * 5, fogc(PAL['burg2'], fog, fogcol), alpha=0.8)
                ink_line(ctx, np.array([[mx - 18, cy_ - 2], [mx + 40, cy_ + 2]]), lws * 5, fogc(PAL['burg2'], fog, fogcol), alpha=0.8)
        if flag:
            # streaming pennant
            pts = []
            for i in range(9):
                u = i / 8
                pts.append((mx - 4 - u * 55 * sk, top + 3 + math.sin(t * 6 + u * 5 + mi) * 4 * u))
            for i in range(8, -1, -1):
                u = i / 8
                pts.append((mx - 4 - u * 55 * sk, top + 3 + (1 - u) * 7 + math.sin(t * 6 + u * 5 + mi) * 4 * u))
            ink_shape(ctx, np.array(pts), fogc(PAL['linen'], fog, fogcol), lw=lws * 0.8, ink=inkc, seed=seed + 9 + mi)
            if mi == 0:
                ink_line(ctx, np.array([pts[2], pts[-3]]), lws * 2, fogc(PAL['burg2'], fog, fogcol))
    ctx.restore()


def longboat(ctx, x, y, s, t, seed=0, oars=True, lw=1.3, fog=0.0, fogcol=None, rowing=True, n_oars=3):
    """A ship's boat in side elevation (bow to the right), its waterline at y."""
    wood = fogc(mix(PAL['wood'], PAL['wood3'], 0.3), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    lws = lw / max(s, 0.05)
    hull = [[-70, -22], [70, -26], [86, -36], [74, -6], [50, 6], [-55, 6], [-72, -6]]
    if oars:
        for k in range(n_oars):
            ph = (t * 0.55 + k * 0.03) * 2 * math.pi if rowing else 0.4
            ox = -40 + k * 36
            a = 0.9 + 0.45 * math.sin(ph)
            ink_line(ctx, np.array([[ox, -26], [ox + math.sin(a) * 70, -26 + math.cos(a) * 52]]), lws * 2.4, shade_c(wood, -0.25))
    ink_shape(ctx, np.array(hull), wood, lw=lws * 1.2, ink=inkc, smooth_path=False, seed=seed,
              shadow=(shade_c(wood, -0.4), 6), hatch=(3.0, 5, lws * 0.5, 0.35), light=(0, -1))
    for k in range(3):
        ink_line(ctx, np.array([[-66, -16 + k * 7], [72, -20 + k * 7 - k]]), lws * 0.6, inkc, alpha=0.45)
    ctx.restore()


def sea_colors(dark=0.0):
    return mix(PAL['grey3'], PAL['grey'], 0.4 + 0.4 * dark), mix(PAL['grey2'], PAL['charcoal'], 0.35 + 0.5 * dark)


def sea_at(y, y_h, y_b, dark=0.0, top_col=None, bot_col=None):
    """The sea's ground colour at height y (to paint over a hull's waterline seamlessly)."""
    a, b = sea_colors(dark)
    a, b = top_col or a, bot_col or b
    return mix(a, b, clamp((y - y_h) / max(y_b - y_h, 1)))


def sea(ctx, x0, x1, y_h, y_b, t, pan=0.0, dark=0.0, seed=1, top_col=None, bot_col=None, lw=1.0, chop=1.0, glint=None):
    """An engraved sea between the horizon y_h and the bottom y_b (screen or world space): a tonal ground
    and rows of short curling wave strokes, smaller and denser towards the horizon, drifting with their
    own speed and shifted by the camera pan in proportion to their nearness (parallax)."""
    ta, tb = sea_colors(dark)
    top_col = top_col or ta
    bot_col = bot_col or tb
    g = cairo.LinearGradient(0, y_h, 0, y_b)
    g.add_color_stop_rgba(0, *top_col[:3], 1)
    g.add_color_stop_rgba(1, *bot_col[:3], 1)
    ctx.rectangle(x0, y_h, x1 - x0, y_b - y_h)
    ctx.set_source(g)
    ctx.fill()
    if glint is not None:
        gx, gw, ga = glint
        gg = cairo.LinearGradient(gx - gw, 0, gx + gw, 0)
        gg.add_color_stop_rgba(0, *PAL['parch'][:3], 0)
        gg.add_color_stop_rgba(0.5, *PAL['parch'][:3], ga)
        gg.add_color_stop_rgba(1, *PAL['parch'][:3], 0)
        ctx.rectangle(gx - gw, y_h, 2 * gw, (y_b - y_h) * 0.5)
        ctx.set_source(gg)
        ctx.fill()
    ink = mix(PAL['ink'], top_col, 0.25)
    light = mix(PAL['parch'], top_col, 0.45 + 0.4 * dark)
    rows = 34
    span = x1 - x0
    for i in range(rows):
        v = (i + 0.5) / rows
        near = v ** 1.8
        y = y_h + (y_b - y_h) * near
        sc = 0.18 + 1.8 * near
        sp = 46 * sc
        off = (t * (8 + 22 * near) * (1 if i % 2 else -0.6) + pan * (0.05 + 0.95 * near)) % sp
        n = int(span / sp) + 3
        for k in range(n):
            xx = x0 - sp + k * sp + off + hash01(seed, i, k) * sp * 0.6
            yy = y + math.sin(t * 1.3 + k * 0.9 + i) * 2.5 * sc * chop
            ww = sp * (0.35 + 0.3 * hash01(seed, i, k, 2))
            hh = 3.2 * sc * chop
            pts = np.array([[xx, yy], [xx + ww * 0.35, yy - hh], [xx + ww * 0.65, yy - hh * 0.6], [xx + ww, yy]])
            ink_line(ctx, pts, max(0.5, lw * sc * 0.9), ink, alpha=0.55 + 0.35 * near)
            if near > 0.25 and hash01(seed, i, k, 3) < 0.5:
                ink_line(ctx, pts[:3] + np.array([0, -1.2 * sc]), max(0.4, lw * sc * 0.6), light, alpha=0.5)


def foam(ctx, x0, x1, y, t, s=1.0, seed=2, alpha=0.8):
    """Wash of foam where waves break (on a beach or against a hull)."""
    rng = np.random.default_rng(seed)
    for k in range(int((x1 - x0) / (14 * s)) + 1):
        xx = x0 + k * 14 * s + rng.uniform(-4, 4) * s
        yy = y + math.sin(t * 2.0 + k) * 2 * s
        ink_line(ctx, np.array([[xx, yy], [xx + 8 * s, yy - 2 * s], [xx + 14 * s, yy]]), max(0.6, 1.6 * s), PAL['linen'], alpha=alpha)


# ----------------------------------------------------------------------------------------------
# Small props
# ----------------------------------------------------------------------------------------------
def barrel(ctx, x, gy, s, seed, fog=0.0, fogcol=None, lw=1.2, empty=False):
    w = fogc(mix(PAL['wood'], PAL['wood3'], 0.3), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    pts = [[x - 18 * s, gy], [x - 21 * s, gy - 24 * s], [x - 18 * s, gy - 48 * s], [x + 18 * s, gy - 48 * s], [x + 21 * s, gy - 24 * s], [x + 18 * s, gy]]
    ink_shape(ctx, np.array(pts), w, lw=lw, ink=inkc, seed=seed, shadow=(shade_c(w, -0.35), 8 * s), hatch=(3.0 * s, 85, lw * 0.4, 0.3), light=(-1, 0))
    for yy in (6, 22, 40):
        ink_line(ctx, np.array([[x - 19.5 * s, gy - yy * s], [x, gy - yy * s + 2 * s], [x + 19.5 * s, gy - yy * s]]), lw * 1.6, fogc(PAL['charcoal'], fog, fogcol))
    ink_shape(ctx, ellipse_pts(x, gy - 48 * s, 18 * s, 4 * s, 16), shade_c(w, -0.2 if not empty else -0.5), lw=lw, ink=inkc, seed=seed + 1)


def crate(ctx, x, gy, s, seed, fog=0.0, fogcol=None, lw=1.2):
    w = fogc(mix(PAL['wood3'], PAL['parch3'], 0.2), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    R(ctx, x - 22 * s, gy - 36 * s, x + 22 * s, gy, w, lw, inkc, (shade_c(w, -0.3), 7 * s), None, seed)
    ink_line(ctx, np.array([[x - 22 * s, gy - 36 * s], [x + 22 * s, gy]]), lw, inkc, alpha=0.6)
    ink_line(ctx, np.array([[x - 22 * s, gy - 18 * s], [x + 22 * s, gy - 18 * s]]), lw, inkc, alpha=0.6)


def sack(ctx, x, gy, s, seed, fog=0.0, fogcol=None, lw=1.2, fill=1.0):
    c = fogc(PAL['parch3'], fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    hh = 34 * s * (0.4 + 0.6 * fill)
    pts = [[x - 18 * s, gy], [x - 20 * s, gy - hh * 0.6], [x - 8 * s, gy - hh], [x, gy - hh - 8 * s], [x + 8 * s, gy - hh], [x + 20 * s, gy - hh * 0.6], [x + 18 * s, gy]]
    ink_shape(ctx, np.array(pts), c, lw=lw, ink=inkc, seed=seed, shadow=(shade_c(c, -0.3), 7 * s), hatch=(3.0 * s, 60, lw * 0.4, 0.3))


def sea_chest(ctx, x, gy, s, seed, open_=0.0, broken=0.0, lw=1.3, fog=0.0, fogcol=None):
    """A sea chest; open_ lifts the lid (dug up and broken open, 1590)."""
    w = fogc(mix(PAL['wood'], PAL['wood2'], 0.3), fog, fogcol)
    inkc = fogc(PAL['ink'], fog * 0.85, fogcol)
    R(ctx, x - 40 * s, gy - 34 * s, x + 40 * s, gy, w, lw, inkc, (shade_c(w, -0.35), 9 * s), (3.0 * s, 10, lw * 0.4, 0.3), seed)
    for dx in (-30, 30):
        ink_line(ctx, np.array([[x + dx * s, gy - 34 * s], [x + dx * s, gy]]), lw * 2.2, fogc(PAL['charcoal'], fog, fogcol))
    if open_ > 0:
        a = -1.9 * open_
        hx, hy = x - 40 * s, gy - 34 * s
        lid = [(0, 0), (80, 0), (80, -12), (0, -12)]
        P = np.array([[hx + (px * math.cos(a) - py * math.sin(a)) * s, hy + (px * math.sin(a) + py * math.cos(a)) * s] for px, py in lid])
        ink_shape(ctx, P, shade_c(w, 0.05), lw=lw, ink=inkc, smooth_path=False, seed=seed + 1)
        ink_shape(ctx, np.array([[x - 37 * s, gy - 33 * s], [x + 37 * s, gy - 33 * s], [x + 37 * s, gy - 28 * s], [x - 37 * s, gy - 28 * s]]),
                  PAL['charcoal'], lw=0, smooth_path=False)
    else:
        R(ctx, x - 42 * s, gy - 44 * s, x + 42 * s, gy - 33 * s, shade_c(w, 0.06), lw, inkc, None, None, seed + 1)


def campfire(ctx, x, gy, s, t, seed=0, alpha=1.0):
    soft_glow(ctx, x, gy - 14 * s, 120 * s, PAL['candle'], 0.35 * alpha)
    for k in range(3):
        a = -0.5 + k * 0.5
        ink_line(ctx, np.array([[x - math.cos(a) * 24 * s, gy + 2], [x + math.cos(a) * 24 * s, gy - 6 * s]]), 4 * s, PAL['wood2'])
    for k in range(3):
        fl = 1 + 0.25 * math.sin(t * (17 + k * 5) + k) + 0.15 * math.sin(t * 29 + k * 2)
        w = (14 - k * 3) * s
        pts = [[x - w, gy - 4 * s], [x - w * 0.5, gy - 20 * s * fl], [x + (k - 1) * 3 * s, gy - (34 - k * 6) * s * fl],
               [x + w * 0.5, gy - 18 * s * fl], [x + w, gy - 4 * s]]
        ink_shape(ctx, np.array(pts), [PAL['burg2'], PAL['candle'], PAL['candle2']][k], lw=0.8 * s if k == 0 else 0, ink=PAL['burg3'],
                  seed=seed + k + int(t * 15))


def scatter_pages(ctx, x, gy, s, seed, n=6, lw=1.0):
    """White's books 'torn from the covers', maps and pictures spoiled with rain, in the grass."""
    rng = np.random.default_rng(seed)
    for k in range(n):
        px, py = x + rng.uniform(-90, 90) * s, gy - rng.uniform(-6, 10) * s
        a = rng.uniform(-0.6, 0.6)
        w, h = 26 * s, 9 * s
        c, sn = math.cos(a), math.sin(a)
        P = np.array([[px + (dx * c - dy * sn), py + (dx * sn + dy * c)] for dx, dy in ((-w / 2, -h), (w / 2, -h), (w / 2, h * 0.3), (-w / 2, h * 0.3))])
        ink_shape(ctx, P, mix(PAL['parch'], PAL['parch3'], rng.random() * 0.6), lw=lw, smooth_path=False, seed=seed + k)
        for j in range(3):
            q = P[0] + (P[1] - P[0]) * 0.15 + (P[3] - P[0]) * (0.25 + 0.25 * j)
            ink_line(ctx, np.array([q, q + (P[1] - P[0]) * 0.65]), 0.5 * lw, PAL['ink'], alpha=0.4)
