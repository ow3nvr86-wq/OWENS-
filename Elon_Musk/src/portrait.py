"""An illustrated editorial portrait of Elon Musk in flat vector shapes (a stylised likeness, not a photograph):
head turned slightly to the right, short dark hair swept back, a dark jacket over an open-collared shirt;
cool key light from the left, an electric-blue rim light on the right."""
import math

import numpy as np

from gfx import C, mixc, fill, glow, line, setc
from core import path_smooth

SKIN = (0.84, 0.69, 0.60, 1.0)
SKIN_SH = (0.62, 0.47, 0.43, 1.0)
SKIN_DK = (0.47, 0.34, 0.33, 1.0)
HAIR = (0.20, 0.15, 0.12, 1.0)
HAIR_HI = (0.36, 0.28, 0.22, 1.0)
JACKET = (0.07, 0.09, 0.13, 1.0)
SHIRT = (0.88, 0.90, 0.93, 1.0)
RIM = (0.36, 0.68, 1.0, 1.0)


def sm(ctx, pts, col):
    ctx.new_path()
    path_smooth(ctx, np.asarray(pts, float), True)
    setc(ctx, col)
    ctx.fill()


def portrait(ctx, x, y, s, t, blink=False, light=1.0):
    """(x, y) = centre of the face; s = scale (the head is about 330*s tall)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    # shoulders and jacket
    sm(ctx, [(-420, 760), (-400, 470), (-300, 330), (-120, 270), (0, 262), (130, 270), (310, 330), (410, 470), (430, 760)], JACKET)
    sm(ctx, [(300, 340), (405, 470), (425, 760), (370, 760), (360, 480)], (*RIM[:3], 0.35 * light))
    # shirt collar and the open neck
    fill(ctx, [(-95, 240), (0, 380), (95, 240), (70, 330), (0, 470), (-70, 330)], SHIRT)
    fill(ctx, [(-95, 240), (-150, 300), (-60, 420), (0, 470), (-70, 330)], mixc(SHIRT, C['grey4'], 0.25))
    fill(ctx, [(95, 240), (150, 300), (60, 420), (0, 470), (70, 330)], mixc(SHIRT, C['grey4'], 0.1))
    # lapels
    fill(ctx, [(-150, 300), (-230, 330), (-120, 560), (-60, 430)], mixc(JACKET, C['navy3'], 0.25))
    fill(ctx, [(150, 300), (230, 330), (120, 560), (60, 430)], mixc(JACKET, C['navy3'], 0.35))
    # neck
    sm(ctx, [(-75, 130), (-80, 250), (-30, 330), (35, 330), (85, 250), (80, 120)], SKIN_SH)
    sm(ctx, [(-75, 140), (-70, 250), (-20, 300), (0, 240), (-10, 160)], mixc(SKIN, SKIN_SH, 0.5))
    # head: a broad face, strong jaw, turned a little to the right
    face = [(-152, -60), (-150, -150), (-122, -215), (-60, -250), (20, -258), (95, -235), (140, -180), (156, -100), (156, -20),
            (148, 60), (130, 120), (95, 168), (35, 198), (-25, 196), (-85, 170), (-128, 118), (-148, 40)]
    sm(ctx, face, SKIN)
    # shading: the right side of the face falls into shadow; the jaw shadow under the chin
    sm(ctx, [(70, -230), (130, -190), (152, -100), (150, -10), (138, 65), (112, 125), (70, 170), (40, 150), (70, 100), (92, 20),
             (95, -80), (80, -170)], mixc(SKIN, SKIN_SH, 0.7))
    sm(ctx, [(-100, 140), (-40, 185), (30, 195), (90, 160), (50, 205), (-10, 218), (-70, 195)], SKIN_DK)
    # rim light down the right edge
    line(ctx, [(140, -180), (155, -100), (152, -20), (140, 60), (118, 120), (80, 170)], 7, (*RIM[:3], 0.8 * light))
    # ears
    sm(ctx, [(-150, -60), (-178, -78), (-188, -30), (-178, 30), (-150, 40)], SKIN_SH)
    sm(ctx, [(150, -55), (170, -70), (176, -30), (168, 22), (148, 30)], mixc(SKIN_SH, SKIN_DK, 0.3))
    # hair: short, swept back, fuller on top
    sm(ctx, [(-152, -100), (-166, -190), (-140, -270), (-70, -325), (20, -345), (105, -330), (160, -280), (172, -200), (158, -120),
             (136, -185), (90, -232), (10, -244), (-60, -236), (-118, -205), (-140, -150)], HAIR)
    sm(ctx, [(-90, -290), (-20, -330), (70, -320), (120, -285), (60, -300), (-20, -305)], HAIR_HI)
    sm(ctx, [(-152, -110), (-156, -60), (-146, -40), (-138, -100)], HAIR)
    # brows
    fill(ctx, [(-112, -110), (-40, -126), (-28, -112), (-104, -96)], HAIR)
    fill(ctx, [(28, -114), (100, -116), (118, -102), (36, -100)], HAIR)
    # eyes (with a blink)
    bl = 1.0
    if blink:
        ph = (t + 0.7) % 3.6
        bl = 0.12 if ph < 0.12 else 1.0
    for ex in (-72, 70):
        w, h = 42, 11 * bl
        fill(ctx, [(ex - w / 2, -78), (ex - w / 4, -78 - h), (ex + w / 4, -78 - h), (ex + w / 2, -78), (ex + w / 4, -78 + h * 0.6),
                   (ex - w / 4, -78 + h * 0.6)], (0.95, 0.94, 0.92, 1.0))
        if bl > 0.5:
            ctx.arc(ex + 4, -78, 8.5, 0, 2 * math.pi)
            setc(ctx, (0.18, 0.24, 0.30, 1.0))
            ctx.fill()
            ctx.arc(ex + 6, -81, 2.4, 0, 2 * math.pi)
            setc(ctx, (1, 1, 1, 0.9))
            ctx.fill()
        line(ctx, [(ex - w / 2 - 2, -80), (ex, -78 - h - 3), (ex + w / 2 + 2, -80)], 3.5, SKIN_DK)
    # nose
    sm(ctx, [(2, -70), (18, -10), (34, 32), (22, 44), (-10, 46), (-24, 36), (-10, 20)], mixc(SKIN, SKIN_SH, 0.45))
    line(ctx, [(4, -60), (24, 20), (30, 36)], 3, SKIN_DK)
    fill(ctx, [(-22, 42), (-8, 36), (2, 46), (-12, 50)], SKIN_DK)
    fill(ctx, [(16, 44), (30, 38), (36, 46), (24, 50)], SKIN_DK)
    # mouth: closed, a faint smile
    line(ctx, [(-50, 100), (-15, 106), (25, 104), (58, 94)], 5, (0.48, 0.30, 0.30, 1.0))
    sm(ctx, [(-40, 108), (0, 116), (42, 106), (0, 124)], mixc(SKIN, SKIN_SH, 0.35))
    # cheek and jaw lines
    line(ctx, [(-118, 30), (-96, 90), (-60, 140)], 2.5, (*SKIN_SH[:3], 0.6))
    ctx.restore()


_CACHE = {}


def portrait_duotone(scale=2.0):
    """The portrait rendered once to a bitmap and tone-mapped to a navy-to-ice duotone with soft shading and an
    electric-blue rim: the look of documentary key art. Returns a cairo surface (premultiplied), origin at the face
    centre offset (ox, oy)."""
    key = scale
    if key in _CACHE:
        return _CACHE[key]
    import cairo
    from scipy import ndimage
    from core import surf_array, array_surface
    w, h = int(1000 * scale), int(1300 * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(surf)
    portrait(c, w / 2, h * 0.36, scale, 0.0, blink=False)
    a = surf_array(surf).astype(np.float32) / 255.0
    alpha = a[..., 3]
    rgb = a[..., [2, 1, 0]] / np.maximum(alpha[..., None], 1e-4)
    lum = rgb[..., 0] * 0.3 + rgb[..., 1] * 0.59 + rgb[..., 2] * 0.11
    lum = ndimage.gaussian_filter(lum, 1.4 * scale)
    # light falls across from the upper left
    yy, xx = np.mgrid[0:h, 0:w]
    # low-key: a hard key light from the left that falls off across the face
    key_light = np.clip(1.25 - (xx / w) * 1.15, 0.12, 1.05) * np.clip(1.15 - (yy / h) * 0.5, 0.5, 1.0)
    v = np.clip(lum ** 1.25 * key_light, 0, 1)
    stops = np.array([[0.02, 0.04, 0.09], [0.07, 0.13, 0.24], [0.20, 0.36, 0.60], [0.55, 0.74, 0.95], [0.92, 0.97, 1.0]], np.float32)
    pos = np.clip(v * (len(stops) - 1), 0, len(stops) - 1.001)
    i0 = pos.astype(int)
    fr = (pos - i0)[..., None]
    col = stops[i0] * (1 - fr) + stops[i0 + 1] * fr
    # the electric-blue rim on the right edge of the silhouette
    edge = alpha - ndimage.uniform_filter(alpha, int(22 * scale))
    rim = np.clip(edge * 4.0, 0, 1) * np.clip((xx / w - 0.42) * 3.0, 0, 1)
    rim = np.maximum(rim, np.clip(edge * 2.0, 0, 1) * np.clip((0.4 - yy / h) * 4, 0, 1) * 0.7)
    col = col * (1 - rim[..., None]) + np.array([0.35, 0.72, 1.0], np.float32) * rim[..., None]
    out = np.zeros((h, w, 4), np.float32)
    out[..., 0], out[..., 1], out[..., 2] = col[..., 2] * alpha, col[..., 1] * alpha, col[..., 0] * alpha
    out[..., 3] = alpha
    res = array_surface((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
    _CACHE[key] = (res, w / 2 / scale, h * 0.36 / scale, scale)
    return _CACHE[key]
