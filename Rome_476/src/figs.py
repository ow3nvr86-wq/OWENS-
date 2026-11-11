"""Illustrations for the Short, drawn in ink with flat cel shading: the legionary in extreme close-up (Imperial
Gallic helmet with brow peak and cheek guards), the marble bust of Trajan (his straight comma-lock fringe), the
clashing legionaries in silhouette, the small marching legion icons, and the golden city of Constantinople.
All coordinates are frame units (1080 x 1920) unless noted."""
import math

import cairo
import numpy as np

from core import clamp, smooth, ease_out, hash01, vnoise, fnoise, set_c, path_smooth, path_poly, ink_line, taper_stroke, \
    soft_glow, ellipse_pts, hatch_lines


def hexc(h, a=1.0):
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


C = {
    'ink': hexc('1a1410'), 'parch': hexc('e9d8b4'), 'parch2': hexc('d9c39a'), 'red': hexc('b3121d'), 'red_d': hexc('7e0c14'),
    'red_l': hexc('d8333a'), 'purple': hexc('5b2a86'), 'purple_l': hexc('8455b0'), 'gold': hexc('d4a017'),
    'gold_l': hexc('f2cf5b'), 'gold_d': hexc('8f6a0c'), 'steel': hexc('6f7176'), 'steel_l': hexc('a9abb0'),
    'steel_d': hexc('3b3c40'), 'bronze': hexc('a8772f'), 'bronze_l': hexc('dcae5c'), 'bronze_d': hexc('5e3f15'),
    'skin': hexc('c99572'), 'skin_l': hexc('dfb08a'), 'skin_d': hexc('8e5f43'), 'skin_dd': hexc('5a3726'),
    'marble': hexc('ece7dc'), 'marble_d': hexc('aeb0b4'), 'marble_dd': hexc('7d8088'), 'ember': hexc('ff9a3c'),
}


def fillp(ctx, pts, col, smooth_=True, tension=0.5):
    ctx.new_path()
    if smooth_:
        path_smooth(ctx, pts, True, tension)
    else:
        path_poly(ctx, pts, True)
    set_c(ctx, col)
    ctx.fill()


def strokep(ctx, pts, col, lw, closed=False, smooth_=True, alpha=None):
    ctx.new_path()
    (path_smooth if smooth_ else path_poly)(ctx, pts, closed)
    set_c(ctx, col, alpha)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def lgrad(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *c)
    return g


def P(*a):
    return np.array(a, float).reshape(-1, 2)


# ----------------------------------------------------------------------------------------------
# Embers drifting up through the firelit dark (periodic over 32 s so the loop is seamless)
# ----------------------------------------------------------------------------------------------
def embers(ctx, t, n=46, seed=3, a=1.0, period=32.0):
    for i in range(n):
        sp = 0.5 + hash01(i, seed) * 1.2                     # screen-heights per period, an integer number of cycles
        cyc = max(1, int(round(sp * 6)))
        ph = (t / period * cyc + hash01(i, seed + 1)) % 1.0
        x = hash01(i, seed + 2) * 1180 - 50 + 40 * math.sin(t * 0.9 + i)
        y = 1980 - ph * 2100
        r = 1.5 + 3.5 * hash01(i, seed + 3)
        fl = 0.55 + 0.45 * math.sin(t * (5 + i % 4) + i)
        soft_glow(ctx, x, y, r * 4, C['ember'], 0.35 * fl * a)
        set_c(ctx, C['gold_l'], 0.9 * fl * a)
        ctx.arc(x, y, r * 0.6, 0, 2 * math.pi)
        ctx.fill()


# ----------------------------------------------------------------------------------------------
# The legionary, extreme close-up (frame coordinates; the caller sets up the camera)
# ----------------------------------------------------------------------------------------------
def _eye(ctx, cx, cy, side, open_, look=(0.0, 0.0)):
    """side: -1 left eye (viewer's left), +1 right. open_: 0 closed .. 1 open."""
    w, h = 104, 40 * open_ + 2
    # socket shadow
    fillp(ctx, ellipse_pts(cx + 4 * side, cy - 8, 150, 92, 30), (*C['skin_d'][:3], 0.55))
    up = P((cx - w, cy + 6), (cx - w * 0.55, cy - h * 1.05), (cx + w * 0.05, cy - h * 1.25), (cx + w * 0.62, cy - h * 0.95), (cx + w, cy - 2))
    lo = P((cx + w, cy - 2), (cx + w * 0.5, cy + h * 0.72 + 6), (cx - w * 0.2, cy + h * 0.8 + 8), (cx - w * 0.7, cy + h * 0.5 + 6))
    if side > 0:
        up[:, 0] = 2 * cx - up[:, 0]
        lo[:, 0] = 2 * cx - lo[:, 0]
    almond = np.concatenate([up, lo[1:]])
    if open_ > 0.08:
        ctx.save()
        ctx.new_path()
        path_smooth(ctx, almond, True, 0.5)
        ctx.clip()
        set_c(ctx, hexc('e6dccb'))
        ctx.paint()
        # the lid's shadow on the eyeball
        set_c(ctx, hexc('9c8a78'), 0.8)
        ctx.rectangle(cx - 140, cy - 80, 280, 40 + h * 0.35)
        ctx.fill()
        ix, iy = cx + look[0] * 30, cy + 2 + look[1] * 10
        g = cairo.RadialGradient(ix, iy, 6, ix, iy, 40)
        g.add_color_stop_rgba(0, 0.55, 0.36, 0.17, 1)
        g.add_color_stop_rgba(0.75, 0.34, 0.2, 0.09, 1)
        g.add_color_stop_rgba(1, 0.12, 0.07, 0.04, 1)
        ctx.set_source(g)
        ctx.arc(ix, iy, 40, 0, 2 * math.pi)
        ctx.fill()
        set_c(ctx, C['ink'])
        ctx.arc(ix, iy, 17, 0, 2 * math.pi)
        ctx.fill()
        # iris fibres
        set_c(ctx, hexc('2a170b'), 0.5)
        ctx.set_line_width(1.6)
        for k in range(18):
            a = k / 18 * 2 * math.pi
            ctx.move_to(ix + math.cos(a) * 19, iy + math.sin(a) * 19)
            ctx.line_to(ix + math.cos(a) * 36, iy + math.sin(a) * 36)
        ctx.stroke()
        # lid shadow over the top of the iris
        set_c(ctx, C['ink'], 0.45)
        ctx.rectangle(cx - 140, cy - 90, 280, 90 - h * 0.55)
        ctx.fill()
        # catchlights: the fire
        set_c(ctx, hexc('fff4dc'))
        ctx.arc(ix - 13 * side - 4, iy - 13, 8, 0, 2 * math.pi)
        ctx.fill()
        set_c(ctx, C['ember'], 0.8)
        ctx.arc(ix + 14, iy + 12, 3.5, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
    else:
        strokep(ctx, lo, C['skin_dd'], 3)
    # upper lid: heavy ink line, with the crease above
    lid = up if open_ > 0.08 else np.concatenate([up[:1], (up[1:-1] + lo[-1:0:-1][:len(up) - 2]) / 2, up[-1:]])
    taper_stroke(ctx, lid, 13, 5, C['ink'])
    crease = up.copy()
    crease[:, 1] -= 30 + 10 * (1 - open_)
    crease[0, 1] += 18
    strokep(ctx, crease[1:], C['skin_dd'], 4, alpha=0.8)
    strokep(ctx, lo, C['skin_dd'], 3, alpha=0.9)
    # lower-lid bag line
    bag = lo.copy()
    bag[:, 1] += 22
    strokep(ctx, bag[1:-1], C['skin_d'], 3, alpha=0.6)


def legionary_face(ctx, t, blink=0.0, squint=0.0, look=(0.0, 0.0), fire=1.0):
    # background: dark smoke lit by fire
    g = cairo.RadialGradient(900, 260, 40, 760, 600, 1500)
    g.add_color_stop_rgba(0, 0.62, 0.26, 0.08, 1)
    g.add_color_stop_rgba(0.35, 0.28, 0.1, 0.05, 1)
    g.add_color_stop_rgba(1, 0.07, 0.05, 0.04, 1)
    ctx.set_source(g)
    ctx.paint()
    open_ = clamp(1 - blink) * (1 - 0.32 * squint)

    # --- face (skin) ---
    face = P((140, 640), (540, 600), (940, 640), (900, 1250), (740, 1700), (540, 1840), (340, 1700), (180, 1250))
    fillp(ctx, face, C['skin'])
    ctx.save()
    ctx.new_path()
    path_smooth(ctx, face, True)
    ctx.clip()
    # cel shadow: the far side of the face away from the firelight
    fillp(ctx, P((800, 600), (1000, 600), (1000, 1900), (660, 1900), (700, 1560), (780, 1260), (840, 1060), (830, 820)), C['skin_d'], tension=0.4)
    # warm light on the near cheek
    soft_glow(ctx, 330, 1150, 260, C['skin_l'], 0.55)
    # the brow peak's shadow across the forehead and the eyes
    set_c(ctx, C['skin_dd'], 0.75)
    ctx.rectangle(0, 560, 1080, 170)
    ctx.fill()
    g = lgrad(ctx, 0, 730, 0, 860, [(0, (*C['skin_dd'][:3], 0.55)), (1, (*C['skin_dd'][:3], 0.0))])
    ctx.set_source(g)
    ctx.rectangle(0, 730, 1080, 130)
    ctx.fill()
    # stubble
    for i in range(520):
        x = 300 + hash01(i, 5) * 480
        y = 1260 + hash01(i, 6) * 520
        if abs(x - 540) < 120 and y < 1330:
            continue
        set_c(ctx, C['skin_dd'], 0.35)
        ctx.arc(x, y, 1.6 + hash01(i, 7) * 1.4, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()

    # brows: heavy, drawn together
    for side in (-1, 1):
        bx = 540 + side * 175
        br = P((540 + side * 40, 812), (540 + side * 95, 792), (bx, 776), (540 + side * 280, 784))
        br[:, 1] += 10 * squint
        taper_stroke(ctx, br, 26, 10, C['ink'])
    # the furrow between the brows
    strokep(ctx, P((520, 800), (515, 840)), C['skin_dd'], 4, alpha=0.8)
    strokep(ctx, P((560, 800), (566, 836)), C['skin_dd'], 3, alpha=0.6)

    _eye(ctx, 368, 905, -1, open_, look)
    _eye(ctx, 712, 905, 1, open_, look)

    # nose
    fillp(ctx, P((540, 860), (590, 1010), (620, 1170), (590, 1215), (540, 1225), (490, 1215), (470, 1170), (505, 1010)), C['skin'])
    fillp(ctx, P((548, 880), (600, 1020), (628, 1168), (596, 1214), (556, 1222)), C['skin_d'], tension=0.4)
    taper_stroke(ctx, P((512, 900), (500, 1040), (470, 1160)), 6, 3, C['skin_dd'])
    ink_line(ctx, P((470, 1165), (500, 1210), (540, 1222), (585, 1210), (615, 1170)), 5, C['ink'])
    for side in (-1, 1):
        fillp(ctx, ellipse_pts(540 + side * 42, 1196, 20, 9, 14, side * 0.25), C['skin_dd'])
    soft_glow(ctx, 515, 1050, 40, C['skin_l'], 0.5)
    # cheek lines and mouth
    taper_stroke(ctx, P((450, 1230), (420, 1300), (410, 1380)), 6, 1, C['skin_dd'])
    taper_stroke(ctx, P((632, 1230), (662, 1300), (672, 1380)), 6, 1, C['skin_dd'])
    taper_stroke(ctx, P((450, 1410), (500, 1402), (540, 1406), (585, 1400), (630, 1412)), 9, 6, C['ink'])
    fillp(ctx, P((470, 1418), (540, 1428), (612, 1418), (580, 1450), (500, 1450)), C['skin_d'])
    # a small scar across the near cheek
    taper_stroke(ctx, P((300, 1080), (330, 1130), (348, 1176)), 5, 2, C['skin_dd'])

    # --- helmet: cheek guards ---
    for side in (-1, 1):
        def sx(x):
            return x if side < 0 else 1080 - x
        outer = [(-80, 690), (-80, 1960)]
        inner = [(150, 690), (225, 760), (246, 860), (232, 980), (262, 1080), (325, 1175), (298, 1290), (352, 1430),
                 (405, 1560), (398, 1720), (330, 1960)]
        poly = P(*[(sx(x), y) for x, y in outer[:1] + inner + outer[1:]][::1])
        poly = np.concatenate([P(*[(sx(x), y) for x, y in inner]), P((sx(-80), 1960), (sx(-80), 690))])
        lit = side < 0
        g = lgrad(ctx, sx(-80), 0, sx(380), 0, [(0, C['steel_d']), (0.55, C['steel'] if lit else C['steel_d']), (1, C['steel_l'] if lit else C['steel'])])
        ctx.new_path()
        path_smooth(ctx, poly, True, 0.35)
        ctx.set_source(g)
        ctx.fill_preserve()
        set_c(ctx, C['ink'])
        ctx.set_line_width(9)
        ctx.stroke()
        # bronze trim along the inner edge, and the embossed line
        trim = P(*[(sx(x), y) for x, y in inner])
        strokep(ctx, trim, C['bronze'], 16)
        strokep(ctx, trim, C['bronze_l'] if lit else C['bronze'], 5)
        emb = trim.copy()
        emb[:, 0] += -side * -1 * 0 + (-48 if side < 0 else 48)
        strokep(ctx, emb[1:-1], C['steel_d'], 6, alpha=0.8)
        strokep(ctx, emb[1:-1] + np.array([3 * (-side), -3]), C['steel_l'], 2.5, alpha=0.6 if lit else 0.25)
        # rivets
        for (x, y) in ((70, 760), (95, 1300), (150, 1650)):
            soft_glow(ctx, sx(x), y, 30, C['bronze_l'], 0.25)
            set_c(ctx, C['bronze'])
            ctx.arc(sx(x), y, 15, 0, 2 * math.pi)
            ctx.fill_preserve()
            set_c(ctx, C['ink'])
            ctx.set_line_width(4)
            ctx.stroke()
            set_c(ctx, C['bronze_l'])
            ctx.arc(sx(x) - 4, y - 5, 5, 0, 2 * math.pi)
            ctx.fill()

    # --- helmet: bowl, eyebrow ridges, brow peak ---
    bowl = P((-120, 660), (-120, -60), (1200, -60), (1200, 660), (540, 612))
    g = lgrad(ctx, 0, -60, 300, 640, [(0, C['steel_l']), (0.6, C['steel']), (1, C['steel_d'])])
    ctx.new_path()
    path_poly(ctx, bowl, True)
    ctx.set_source(g)
    ctx.fill()
    soft_glow(ctx, 230, 200, 320, C['ember'], 0.25 * fire)
    soft_glow(ctx, 260, 330, 120, (1, 0.9, 0.75, 1), 0.35)
    # the two embossed 'eyebrows' of the Imperial Gallic bowl
    for side in (-1, 1):
        arc = P((540 + side * 30, 470), (540 + side * 170, 400), (540 + side * 330, 420), (540 + side * 420, 500))
        taper_stroke(ctx, arc + np.array([0, 10]), 34, 22, C['steel_d'])
        taper_stroke(ctx, arc, 30, 18, C['steel_l'] if side < 0 else C['steel'])
        taper_stroke(ctx, arc - np.array([0, 8]), 8, 4, (1, 0.93, 0.8, 1), alpha=0.7 if side < 0 else 0.25)
    # bronze boss on the brow
    soft_glow(ctx, 540, 520, 70, C['gold_l'], 0.3)
    fillp(ctx, ellipse_pts(540, 520, 38, 30, 20), C['bronze'])
    fillp(ctx, ellipse_pts(532, 512, 16, 11, 14), C['bronze_l'])
    # brow peak: the reinforcing band that juts out over the eyes
    peak = P((-120, 618), (540, 566), (1200, 618), (1200, 712), (540, 676), (-120, 712))
    g = lgrad(ctx, 0, 566, 0, 712, [(0, C['bronze_l']), (0.35, C['bronze']), (1, C['bronze_d'])])
    ctx.new_path()
    path_smooth(ctx, peak, True, 0.15)
    ctx.set_source(g)
    ctx.fill_preserve()
    set_c(ctx, C['ink'])
    ctx.set_line_width(9)
    ctx.stroke()
    strokep(ctx, P((-120, 626), (540, 576), (1200, 626)), C['gold_l'], 5, alpha=0.85)
    for k in range(9):
        x = 60 + k * 120
        y = 640 - 30 * math.cos((x - 540) / 900)
        set_c(ctx, C['bronze_d'])
        ctx.arc(x, y + 6, 9, 0, 2 * math.pi)
        ctx.fill()
        set_c(ctx, C['gold_l'], 0.8)
        ctx.arc(x - 2, y + 3, 3.5, 0, 2 * math.pi)
        ctx.fill()
    # firelight rim on the near edge of the helmet
    strokep(ctx, P((-20, 40), (40, 300), (110, 560)), C['ember'], 10, alpha=0.35 * fire)


# ----------------------------------------------------------------------------------------------
# Trajan: marble bust, three-quarter view, facing right (origin at the top of the head; s = scale)
# ----------------------------------------------------------------------------------------------
def trajan_bust(ctx, x0, y0, s, t, glow=1.0):
    ctx.save()
    ctx.translate(x0, y0)
    ctx.scale(s, s)
    soft_glow(ctx, 30, 230, 520, C['gold_l'], 0.55 * glow)
    soft_glow(ctx, 30, 230, 260, (1, 0.92, 0.6, 1), 0.35 * glow)
    M, Md, Mdd = C['marble'], C['marble_d'], C['marble_dd']
    # shoulders and the cloak (paludamentum), with a round brooch on the right shoulder
    body = P((-330, 760), (-250, 560), (-90, 470), (120, 470), (300, 560), (380, 760))
    fillp(ctx, body, M, tension=0.4)
    fillp(ctx, P((60, 480), (300, 560), (380, 760), (120, 760), (150, 620)), Md, tension=0.4)
    for k, (a, b) in enumerate((((-240, 600), (-120, 760)), ((-160, 540), (-30, 760)), ((150, 560), (90, 760)), ((240, 600), (230, 760)))):
        taper_stroke(ctx, P(a, ((a[0] + b[0]) / 2 + 20, (a[1] + b[1]) / 2), b), 8, 2, Mdd)
    fillp(ctx, ellipse_pts(200, 560, 34, 30, 18), C['gold'])
    fillp(ctx, ellipse_pts(194, 553, 12, 10, 12), C['gold_l'])
    path_smooth(ctx, body, True, 0.4)
    set_c(ctx, C['ink'])
    ctx.set_line_width(6)
    ctx.stroke()
    # neck
    fillp(ctx, P((-70, 300), (60, 300), (80, 480), (-80, 480)), M, smooth_=False)
    fillp(ctx, P((20, 300), (70, 300), (85, 480), (30, 480)), Md, smooth_=False)
    ink_line(ctx, P((-72, 320), (-80, 470)), 5)
    ink_line(ctx, P((66, 320), (82, 470)), 5)
    # head
    head = P((-120, 40), (-30, -40), (90, -20), (150, 60), (160, 160), (150, 240), (110, 320), (40, 360), (-40, 340), (-110, 260), (-140, 150))
    fillp(ctx, head, M)
    fillp(ctx, P((60, -10), (150, 60), (160, 170), (140, 250), (100, 320), (50, 350), (80, 250), (90, 140)), Md)
    # ear (far side hidden; near ear on the left)
    fillp(ctx, P((-150, 140), (-170, 170), (-160, 220), (-130, 235)), Md)
    ink_line(ctx, P((-130, 140), (-165, 160), (-168, 205), (-135, 232)), 5)
    # features, turned to the right
    ink_line(ctx, P((-10, 120), (40, 108), (85, 116)), 6)               # brow
    ink_line(ctx, P((95, 116), (128, 112), (150, 122)), 5)
    fillp(ctx, ellipse_pts(48, 142, 22, 9, 14), Md)                      # eyes (blank marble)
    fillp(ctx, ellipse_pts(125, 142, 14, 8, 12), Md)
    ink_line(ctx, P((26, 140), (48, 134), (70, 142)), 4)
    ink_line(ctx, P((114, 140), (126, 136), (138, 142)), 3.5)
    ink_line(ctx, P((96, 128), (104, 190), (124, 214), (104, 224)), 5)  # nose
    taper_stroke(ctx, P((60, 262), (95, 256), (125, 262)), 6, 3, C['ink'])  # lips
    ink_line(ctx, P((70, 284), (100, 286), (118, 280)), 3, Mdd)
    ink_line(ctx, P((30, 210), (50, 250), (62, 262)), 3, Mdd)             # cheek fold
    taper_stroke(ctx, P((20, 330), (70, 342), (120, 320)), 4, 2, Mdd)     # strong chin
    path_smooth(ctx, head, True)
    set_c(ctx, C['ink'])
    ctx.set_line_width(6)
    ctx.stroke()
    # hair: a close cap with the straight fringe of comma-shaped locks across the forehead
    cap = P((-135, 130), (-128, 40), (-40, -48), (80, -34), (150, 40), (158, 92), (120, 80), (60, 78), (0, 80), (-60, 86), (-110, 110))
    fillp(ctx, cap, Md)
    for k in range(13):
        x = -95 + k * 19
        y = 78 + 4 * math.sin(k * 1.3)
        taper_stroke(ctx, P((x - 8, y - 46), (x - 2, y - 18), (x + 6, y + 2)), 10, 2, Mdd)
        taper_stroke(ctx, P((x - 6, y - 44), (x - 1, y - 20), (x + 4, y - 2)), 4, 1, M)
    for k in range(10):
        a = -2.6 + k * 0.28
        cx, cy = 20 + 110 * math.cos(a), 60 + 90 * math.sin(a)
        taper_stroke(ctx, P((cx, cy), (cx + 10, cy + 18), (cx + 4, cy + 34)), 7, 1, Mdd)
    path_smooth(ctx, cap, True)
    set_c(ctx, C['ink'])
    ctx.set_line_width(5)
    ctx.stroke()
    # gold rim light from behind
    strokep(ctx, P((-120, 40), (-138, 150), (-112, 262), (-40, 344)), C['gold_l'], 6, alpha=0.8 * glow)
    strokep(ctx, P((-250, 560), (-330, 760)), C['gold_l'], 6, alpha=0.7 * glow)
    ctx.restore()


# ----------------------------------------------------------------------------------------------
# Legionaries in silhouette (for the clash) and tiny legion icons (for the map)
# ----------------------------------------------------------------------------------------------
def _limb(ctx, pts, w, col):
    ctx.new_path()
    path_smooth(ctx, P(*pts), False, 0.5)
    set_c(ctx, col)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def legionary_silhouette(ctx, x, y, s, face=1, lunge=0.0, sword=0.0, crest=None, rim=None):
    """A legionary in profile, standing on (x, y) (feet), about 780*s tall, facing right (face=+1) or left (-1).
    lunge 0..1 bends the knees and leans in; sword: the sword arm's angle above horizontal (radians)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * face, s)
    ink = C['ink']
    rim = rim or C['ember']
    L = lunge
    hip = (0 + 30 * L, -380 + 40 * L)
    # legs: back leg straight behind, front leg bent forward
    back = [hip, (-70 - 20 * L, -200 + 10 * L), (-150 - 40 * L, -14)]
    front = [hip, (100 + 40 * L, -230 + 50 * L), (120 + 70 * L, -14)]
    _limb(ctx, back, 58, ink)
    _limb(ctx, front, 62, ink)
    fillp(ctx, P((back[2][0] - 40, -30), (back[2][0] + 30, -30), (back[2][0] + 40, 0), (back[2][0] - 50, 0)), ink, smooth_=False)
    fillp(ctx, P((front[2][0] - 30, -30), (front[2][0] + 50, -24), (front[2][0] + 60, 0), (front[2][0] - 34, 0)), ink, smooth_=False)
    # torso, leaning in
    lean = 70 * L
    sh = (40 + lean, -640 + 30 * L)
    torso = P((hip[0] - 70, hip[1] + 10), (hip[0] + 70, hip[1] + 10), (sh[0] + 85, sh[1] + 40), (sh[0] + 60, sh[1] - 20),
              (sh[0] - 70, sh[1] - 10), (sh[0] - 90, sh[1] + 60))
    fillp(ctx, torso, ink, tension=0.35)
    # military belt and the strap skirt
    for k in range(6):
        sx = hip[0] - 50 + k * 20
        _limb(ctx, [(sx, hip[1] + 10), (sx - 6, hip[1] + 95)], 13, ink)
    # neck, head, helmet with neck guard, brow peak and crest
    hx, hy = sh[0] + 30, sh[1] - 85
    _limb(ctx, [(sh[0], sh[1]), (hx - 5, hy + 40)], 46, ink)
    fillp(ctx, ellipse_pts(hx, hy, 52, 58, 24), ink)
    fillp(ctx, P((hx - 62, hy - 6), (hx - 56, hy - 52), (hx - 10, hy - 76), (hx + 42, hy - 66), (hx + 66, hy - 26), (hx + 82, hy - 6),
                 (hx + 40, hy - 2), (hx - 40, hy + 4), (hx - 80, hy + 36), (hx - 92, hy + 26)), ink)
    fillp(ctx, P((hx + 20, hy + 4), (hx + 34, hy + 66), (hx + 4, hy + 70), (hx - 4, hy + 6)), ink)       # cheek guard
    if crest is not None:
        fillp(ctx, P((hx - 60, hy - 64), (hx - 46, hy - 120), (hx + 10, hy - 140), (hx + 66, hy - 116), (hx + 60, hy - 72), (hx, hy - 82)), crest)
        strokep(ctx, P((hx - 60, hy - 64), (hx - 46, hy - 120), (hx + 10, hy - 140), (hx + 66, hy - 116)), ink, 5)
    # shield arm and the curved scutum, held side-on in front
    _limb(ctx, [(sh[0] + 10, sh[1] + 20), (sh[0] + 70, sh[1] + 120), (sh[0] + 120, sh[1] + 150)], 40, ink)
    scx, scy = sh[0] + 150, sh[1] + 170
    fillp(ctx, P((scx - 30, scy - 250), (scx + 26, scy - 236), (scx + 34, scy), (scx + 26, scy + 236), (scx - 30, scy + 250),
                 (scx - 46, scy)), ink, tension=0.3)
    strokep(ctx, P((scx + 26, scy - 236), (scx + 34, scy), (scx + 26, scy + 236)), C['bronze'], 6, alpha=0.9)
    fillp(ctx, ellipse_pts(scx + 30, scy, 14, 30, 14), C['bronze'])
    # sword arm, raised; the gladius
    ctx.save()
    ctx.translate(sh[0] + 20, sh[1] + 10)
    ctx.rotate(-sword)
    _limb(ctx, [(0, 0), (100, 30), (190, 0)], 40, ink)
    fillp(ctx, P((180, -26), (196, -26), (196, 26), (180, 26)), ink, smooth_=False)
    fillp(ctx, P((196, -13), (360, -10), (392, 0), (360, 10), (196, 13)), C['steel_l'], smooth_=False)
    strokep(ctx, P((200, -4), (360, -3)), (1, 1, 1, 1), 2.5, smooth_=False, alpha=0.8)
    ctx.restore()
    # rim light from the fire behind
    strokep(ctx, P((torso[5][0], torso[5][1]), (torso[4][0], torso[4][1])), rim, 8, alpha=0.75)
    strokep(ctx, P((hx - 92, hy + 26), (hx - 62, hy - 6), (hx - 56, hy - 52)), rim, 7, alpha=0.75)
    strokep(ctx, P(*back), rim, 6, alpha=0.5)
    ctx.restore()


def legion_icon(ctx, x, y, s, t, seed=0, col=None):
    """A tiny marching legionary: red shield, helmet and spear, bobbing with each step."""
    bob = abs(math.sin(t * 9 + seed)) * 3 * s
    ctx.save()
    ctx.translate(x, y - bob)
    ctx.scale(s, s)
    ink = C['ink']
    ctx.set_line_width(2.4)
    set_c(ctx, ink)
    ph = t * 9 + seed
    ctx.move_to(-2, 0)
    ctx.line_to(-2 - 4 * math.sin(ph), 12)
    ctx.move_to(2, 0)
    ctx.line_to(2 + 4 * math.sin(ph), 12)
    ctx.stroke()
    fillp(ctx, P((-5, -14), (5, -14), (5, 1), (-5, 1)), ink, smooth_=False)
    set_c(ctx, ink)
    ctx.arc(0, -19, 5, 0, 2 * math.pi)
    ctx.fill()
    fillp(ctx, P((-4, -24), (6, -27), (2, -21)), col or C['red'], smooth_=False)
    ink_line(ctx, P((7, 8), (9, -32)), 1.6, ink)
    fillp(ctx, P((-11, -12), (-1, -13), (-1, 6), (-11, 5)), col or C['red'], smooth_=False)
    ctx.set_line_width(1.4)
    set_c(ctx, ink)
    ctx.rectangle(-11, -12, 10, 18)
    ctx.stroke()
    set_c(ctx, C['gold'])
    ctx.arc(-6, -3, 1.8, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def person(ctx, x, y, s, fill, ink=None):
    """A small standing figure for the crowd."""
    ink = ink or C['ink']
    fillp(ctx, ellipse_pts(x, y - 30 * s, 9 * s, 9 * s, 16), fill)
    ctx.new_path()
    path_smooth(ctx, ellipse_pts(x, y - 30 * s, 9 * s, 9 * s, 16), True)
    set_c(ctx, ink)
    ctx.set_line_width(2.2 * s)
    ctx.stroke()
    body = P((x - 13 * s, y + 14 * s), (x - 11 * s, y - 12 * s), (x, y - 18 * s), (x + 11 * s, y - 12 * s), (x + 13 * s, y + 14 * s))
    ctx.new_path()
    path_smooth(ctx, body, True, 0.3)
    set_c(ctx, fill)
    ctx.fill_preserve()
    set_c(ctx, ink)
    ctx.stroke()


# ----------------------------------------------------------------------------------------------
# Constantinople: a golden city rising from the map (origin at the base centre; s = scale; rise 0..1)
# ----------------------------------------------------------------------------------------------
def constantinople(ctx, x, y, s, rise, t, glow=1.0):
    if rise <= 0.001:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s * ease_out(rise))
    soft_glow(ctx, 0, -60, 260, C['gold_l'], 0.45 * glow)
    G, Gd, Gl, ink = C['gold'], C['gold_d'], C['gold_l'], C['ink']
    def blk(pts, col):
        fillp(ctx, pts, col, smooth_=False)
        ctx.new_path()
        path_poly(ctx, pts, True)
        set_c(ctx, ink)
        ctx.set_line_width(3)
        ctx.stroke()
    # domes and towers behind
    for dx, w, h in ((-110, 70, 110), (90, 80, 120), (0, 120, 150)):
        blk(P((dx - w / 2, 0), (dx - w / 2, -h), (dx + w / 2, -h), (dx + w / 2, 0)), Gd if dx else G)
        ctx.new_path()
        ctx.arc(dx, -h, w / 2, math.pi, 2 * math.pi)
        ctx.close_path()
        set_c(ctx, Gl if dx == 0 else G)
        ctx.fill_preserve()
        set_c(ctx, ink)
        ctx.set_line_width(3)
        ctx.stroke()
        ink_line(ctx, P((dx, -h - w / 2), (dx, -h - w / 2 - 22)), 3)
        set_c(ctx, Gl)
        ctx.arc(dx, -h - w / 2 - 26, 6, 0, 2 * math.pi)
        ctx.fill()
    # a column (Constantine's porphyry column) on the right
    blk(P((170, 0), (170, -190), (186, -190), (186, 0)), Gd)
    blk(P((162, -190), (194, -190), (190, -204), (166, -204)), G)
    # the land walls with towers in front
    blk(P((-220, 0), (-220, -60), (220, -60), (220, 0)), G)
    for k in range(-5, 6):
        tx = k * 42
        blk(P((tx - 14, -60), (tx - 14, -82), (tx + 14, -82), (tx + 14, -60)), Gd if k % 2 else G)
    for k in range(-2, 3):
        tx = k * 100
        blk(P((tx - 22, 0), (tx - 22, -98), (tx + 22, -98), (tx + 22, 0)), Gl if k == 0 else G)
        for m in range(3):
            set_c(ctx, ink)
            ctx.rectangle(tx - 18 + m * 13, -106, 8, 10)
            ctx.fill()
    # lit windows
    for k in range(9):
        wx = -180 + k * 45
        fl = 0.6 + 0.4 * math.sin(t * 4 + k)
        set_c(ctx, (1, 0.95, 0.7, 1), fl)
        ctx.rectangle(wx, -40, 7, 12)
        ctx.fill()
    ctx.restore()
