"""Core of the 2D engine: frame constants, palette, timing, easing, noise, and ink drawing on cairo.

Everything visible is drawn with pycairo (vector paths with an ink outline, cel shadows and engraving
hatches) or generated with numpy (paper, fog, noise masks). Nothing is 3D: depth comes only from
flat layers moved at different speeds (a multiplane camera).
"""
import json
import math
import os

import cairo
import numpy as np
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
ASSETS = os.path.join(ROOT, 'assets')
LAYERS = os.path.join(ASSETS, 'layers')
FONTS = os.path.join(ASSETS, 'fonts')

PART = os.environ.get('WW2_PART', 'part1')
PART_DIR = os.path.join(ROOT, PART)
with open(os.path.join(PART_DIR, 'scene_timing.json')) as _fh:
    TIMING = json.load(_fh)
DURATION = TIMING['duration']
NFRAMES = int(round(DURATION * FPS))
EV = TIMING['events']
SCENES = {s['key']: s for s in TIMING['scenes']}


def vo_timing():
    p = os.path.join(ROOT, 'build', 'vo_timing.json')
    if os.path.exists(p):
        with open(p) as fh:
            return json.load(fh)['lines']
    return []


# ----------------------------------------------------------------------------------------------
# Palette: dark charcoal, muted brown, aged parchment, dusty grey, deep burgundy, desaturated green,
# warm candlelight. All colours in the film are mixed from these.
# ----------------------------------------------------------------------------------------------
def hexc(h, a=1.0):
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


PAL = {
    'ink':        hexc('1b1713'),
    'charcoal':   hexc('2b2724'),
    'charcoal2':  hexc('3a3531'),
    'brown':      hexc('5b4636'),
    'brown2':     hexc('7a5f48'),
    'brown3':     hexc('9a7d5f'),
    'umber':      hexc('46362a'),
    'parch':      hexc('e3d4b4'),
    'parch2':     hexc('cdb990'),
    'parch3':     hexc('b39c74'),
    'grey':       hexc('8c877d'),
    'grey2':      hexc('6c675f'),
    'grey3':      hexc('a9a397'),
    'burg':       hexc('6e1f27'),
    'burg2':      hexc('8d2d34'),
    'burg3':      hexc('4d151b'),
    'green':      hexc('5d6650'),
    'green2':     hexc('737b62'),
    'green3':     hexc('454c3c'),
    'candle':     hexc('f0b866'),
    'candle2':    hexc('ffd890'),
    'linen':      hexc('e8dfcc'),
    'linen2':     hexc('d2c7b0'),
    'skin':       hexc('d7b393'),
    'skin2':      hexc('c49a78'),
    'skin3':      hexc('b08566'),
    'hair_dk':    hexc('2f241c'),
    'hair_br':    hexc('6a4a30'),
    'hair_gr':    hexc('9a958c'),
    'hair_bl':    hexc('a88a58'),
    'wood':       hexc('6b4f37'),
    'wood2':      hexc('4e3a29'),
    'wood3':      hexc('8a6a4b'),
    'plaster':    hexc('cfc2a4'),
    'plaster2':   hexc('b9aa8a'),
    'stone':      hexc('a39a88'),
    'stone2':     hexc('857c6c'),
    'roof':       hexc('6a3a30'),
    'roof2':      hexc('523029'),
    'sky':        hexc('b8b2a2'),
    'skyd':       hexc('4a4a4a'),
    'red_shoe':   hexc('7d2328'),
}


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def shade_c(c, k):
    """Darken (k<0) or lighten towards parchment (k>0)."""
    if k < 0:
        return (c[0] * (1 + k), c[1] * (1 + k), c[2] * (1 + k), c[3] if len(c) > 3 else 1.0)
    return mix(c, PAL['parch'], k)


# ----------------------------------------------------------------------------------------------
# Easing and timing
# ----------------------------------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def smoother(x):
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def ramp(t, a, b):
    return clamp((t - a) / max(b - a, 1e-6))


def keys(t, pts, ease=smooth):
    """Piecewise interpolation through (time, value) keys; values may be numbers or tuples."""
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            u = ease((t - t0) / max(t1 - t0, 1e-6))
            if isinstance(v0, tuple):
                return tuple(a + (b - a) * u for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * u
    return pts[-1][1]


def twos(t):
    """Characters are animated 'on twos' (a new drawing every second frame, 15 per second), like
    traditional hand-drawn animation; the camera still moves on every frame."""
    return math.floor(t * FPS / 2) * 2 / FPS


def boil_seed(t, every=2):
    """Line boil: each new drawing is retraced slightly differently."""
    return int(math.floor(t * FPS / every))


# ----------------------------------------------------------------------------------------------
# Hash noise (deterministic, cheap) and numpy fractal noise for textures
# ----------------------------------------------------------------------------------------------
def hash01(*args):
    h = 2166136261
    for a in args:
        h ^= (int(a * 1000003) if isinstance(a, float) else int(a)) & 0xffffffff
        h = (h * 16777619) & 0xffffffff
    h ^= h >> 13
    h = (h * 0x5bd1e995) & 0xffffffff
    h ^= h >> 15
    return (h & 0xffffff) / float(0x1000000)


def vnoise(x, seed=0):
    """1D smooth value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a = hash01(i, seed) * 2 - 1
    b = hash01(i + 1, seed) * 2 - 1
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u


def fnoise(x, seed=0, oct=3):
    v, amp, fr, tot = 0.0, 1.0, 1.0, 0.0
    for o in range(oct):
        v += amp * vnoise(x * fr, seed + o * 17)
        tot += amp
        amp *= 0.5
        fr *= 2.03
    return v / tot


def fbm2(h, w, seed=0, scale=64.0, octaves=5, persist=0.5):
    """2D fractal value noise, values roughly in [0, 1]."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot, sc = 1.0, 0.0, scale
    for _ in range(octaves):
        gh, gw = max(2, int(h / sc) + 2), max(2, int(w / sc) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        z = ndimage.zoom(g, (h / (gh - 1) * 1.0001, w / (gw - 1) * 1.0001), order=3, mode='reflect')[:h, :w]
        if z.shape != (h, w):
            z = np.pad(z, ((0, h - z.shape[0]), (0, w - z.shape[1])), mode='edge')
        out += amp * z
        tot += amp
        amp *= persist
        sc /= 2.0
        if sc < 1.5:
            break
    out /= tot
    lo, hi = np.percentile(out, 1), np.percentile(out, 99)
    return np.clip((out - lo) / (hi - lo + 1e-6), 0, 1)


# ----------------------------------------------------------------------------------------------
# cairo <-> numpy
# ----------------------------------------------------------------------------------------------
def new_surface(w, h):
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w), int(h))


def surf_array(s):
    """View of a cairo ARGB32 surface as an (h, w, 4) uint8 array in B, G, R, A order (premultiplied)."""
    s.flush()
    return np.ndarray((s.get_height(), s.get_width(), 4), np.uint8, buffer=s.get_data(), strides=(s.get_stride(), 4, 1))


def array_surface(a):
    """Make a cairo surface from an (h, w, 4) uint8 BGRA premultiplied array."""
    h, w = a.shape[:2]
    s = new_surface(w, h)
    surf_array(s)[:] = a
    s.mark_dirty()
    return s


def rgba_to_surface(rgba):
    """Float or uint8 RGBA (straight alpha) -> cairo surface."""
    a = rgba.astype(np.float32)
    if a.max() > 1.5:
        a /= 255.0
    al = a[..., 3:4]
    bgra = np.concatenate([a[..., 2:3] * al, a[..., 1:2] * al, a[..., 0:1] * al, al], axis=2)
    return array_surface((np.clip(bgra, 0, 1) * 255 + 0.5).astype(np.uint8))


_PNG = {}


def load_png(name):
    if name not in _PNG:
        _PNG[name] = cairo.ImageSurface.create_from_png(os.path.join(LAYERS, name if name.endswith('.png') else name + '.png'))
    return _PNG[name]


# ----------------------------------------------------------------------------------------------
# Ink drawing
# ----------------------------------------------------------------------------------------------
def set_c(ctx, c, a=None):
    if a is None:
        ctx.set_source_rgba(*(c if len(c) == 4 else (*c, 1.0)))
    else:
        ctx.set_source_rgba(c[0], c[1], c[2], a)


def wob(pts, amp, seed, freq=1.0):
    """Perturb points with smooth noise: the small unsteadiness of a hand-drawn line."""
    if amp <= 0:
        return pts
    p = np.asarray(pts, float).copy()
    n = len(p)
    for i in range(n):
        p[i, 0] += amp * vnoise(i * 0.7 * freq + seed * 3.1, 11)
        p[i, 1] += amp * vnoise(i * 0.7 * freq + seed * 3.1, 23)
    return p


def path_smooth(ctx, pts, closed=True, tension=0.5):
    """Catmull-Rom spline through points as cairo bezier curves."""
    p = np.asarray(pts, float)
    n = len(p)
    if n < 2:
        return
    if n == 2:
        ctx.move_to(*p[0])
        ctx.line_to(*p[1])
        if closed:
            ctx.close_path()
        return
    ctx.move_to(*p[0])
    rng_end = n if closed else n - 1
    for i in range(rng_end):
        p0 = p[(i - 1) % n] if (closed or i > 0) else p[0]
        p1 = p[i]
        p2 = p[(i + 1) % n]
        p3 = p[(i + 2) % n] if (closed or i + 2 < n) else p[-1]
        c1 = p1 + (p2 - p0) * tension / 3.0
        c2 = p2 - (p3 - p1) * tension / 3.0
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        ctx.close_path()


def path_poly(ctx, pts, closed=True):
    p = np.asarray(pts, float)
    ctx.move_to(*p[0])
    for q in p[1:]:
        ctx.line_to(*q)
    if closed:
        ctx.close_path()


def ink_shape(ctx, pts, fill, lw=2.0, ink=None, smooth_path=True, closed=True, shadow=None,
              hatch=None, seed=0, boil=0.0, line_alpha=1.0, light=(-0.7, -0.7)):
    """Fill a shape, add a cel shadow on the side away from the light (and optional hatching inside it),
    then trace it with an ink outline.  `shadow` = (colour, depth in units); `hatch` = (spacing, angle_deg,
    width, alpha)."""
    pts = wob(pts, boil, seed)
    mk = path_smooth if smooth_path else path_poly
    if fill is not None:
        ctx.new_path()
        mk(ctx, pts, closed)
        set_c(ctx, fill)
        ctx.fill()
    if shadow is not None:
        col, d = shadow
        ctx.save()
        ctx.new_path()
        mk(ctx, pts, closed)
        ctx.clip()
        ctx.new_path()
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        x0, y0 = pts[:, 0].min() - 50, pts[:, 1].min() - 50
        x1, y1 = pts[:, 0].max() + 50, pts[:, 1].max() + 50
        ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
        sh = pts + np.array([light[0] * -d * -1, light[1] * -d * -1]) * 1.0
        mk(ctx, sh, closed)
        if len(col) < 4 or col[3] > 0:
            set_c(ctx, col)
            ctx.fill()
        else:
            ctx.new_path()
        if hatch is not None:
            sp, ang, hw, ha = hatch
            ctx.new_path()
            ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
            mk(ctx, sh, closed)
            ctx.clip()
            ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
            hatch_lines(ctx, x0, y0, x1, y1, sp, ang, hw, (*PAL['ink'][:3], ha), seed)
        ctx.restore()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    if lw > 0:
        ctx.new_path()
        mk(ctx, pts, closed)
        set_c(ctx, ink or PAL['ink'], line_alpha)
        ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


def hatch_lines(ctx, x0, y0, x1, y1, sp, ang, lw, col, seed=0, jitter=0.25):
    """Parallel engraving strokes across a box (clip first)."""
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + 2
    n = int(2 * R / sp) + 1
    set_c(ctx, col)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(n):
        o = -R + i * sp + (hash01(i, seed) - 0.5) * sp * jitter
        px, py = cx + nx * o, cy + ny * o
        ctx.move_to(px - dx * R, py - dy * R)
        ctx.line_to(px + dx * R, py + dy * R)
    ctx.stroke()


def ink_line(ctx, pts, lw=2.0, col=None, seed=0, boil=0.0, smooth_path=True, alpha=1.0):
    pts = wob(pts, boil, seed)
    ctx.new_path()
    (path_smooth if smooth_path else path_poly)(ctx, pts, closed=False)
    set_c(ctx, col or PAL['ink'], alpha)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def taper_stroke(ctx, pts, w0, w1, col=None, seed=0, boil=0.0, alpha=1.0):
    """A calligraphic stroke whose width tapers from w0 to w1 (a brush or quill line)."""
    p = wob(np.asarray(pts, float), boil, seed)
    if len(p) < 2:
        return
    d = np.gradient(p, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    ws = np.linspace(w0, w1, len(p))[:, None] * 0.5
    left = p + nrm * ws
    right = p - nrm * ws
    poly = np.concatenate([left, right[::-1]])
    ctx.new_path()
    path_smooth(ctx, poly, True, tension=0.3)
    set_c(ctx, col or PAL['ink'], alpha)
    ctx.fill()


def soft_glow(ctx, x, y, r, col, a=1.0):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], a)
    g.add_color_stop_rgba(0.35, col[0], col[1], col[2], a * 0.45)
    g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def ellipse_pts(cx, cy, rx, ry, n=24, rot=0.0):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    c, s = math.cos(rot), math.sin(rot)
    x, y = np.cos(a) * rx, np.sin(a) * ry
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)


# ----------------------------------------------------------------------------------------------
# Multiplane camera: flat layers at different depths, moved and scaled by different amounts
# ----------------------------------------------------------------------------------------------
class Camera:
    """cx, cy: the world point at the frame centre for the character plane (depth 1); z: zoom there.
    A layer at depth d is shifted by d times the camera move and scaled by z ** d, the multiplane
    rule of classic 2D animation. Optional roll for an uneasy tilted frame."""

    def __init__(self, cx=540.0, cy=960.0, z=1.0, roll=0.0, anchor=(540.0, 960.0), ox=W / 2, oy=H / 2):
        self.cx, self.cy, self.z, self.roll = cx, cy, z, roll
        self.ax, self.ay = anchor
        self.ox, self.oy = ox, oy

    def apply(self, ctx, d=1.0, out_scale=1.0):
        s = self.z ** d
        lx = self.ax + (self.cx - self.ax) * d
        ly = self.ay + (self.cy - self.ay) * d
        ctx.scale(out_scale, out_scale)
        ctx.translate(self.ox, self.oy)
        if self.roll:
            ctx.rotate(self.roll)
        ctx.scale(s, s)
        ctx.translate(-lx, -ly)

    def world_to_screen(self, x, y, d=1.0):
        s = self.z ** d
        lx = self.ax + (self.cx - self.ax) * d
        ly = self.ay + (self.cy - self.ay) * d
        px, py = (x - lx) * s, (y - ly) * s
        if self.roll:
            c, sn = math.cos(self.roll), math.sin(self.roll)
            px, py = px * c - py * sn, px * sn + py * c
        return self.ox + px, self.oy + py


def draw_layer(ctx, cam, name, d, out_scale, x=0.0, y=0.0, scale=1.0, alpha=1.0):
    """Composite a pre-drawn layer PNG. Layer PNGs carry their own pixel scale in their file name
    convention: the image is drawn so that `scale` image pixels... = 1 world unit (see sets.py)."""
    img = load_png(name)
    ctx.save()
    cam.apply(ctx, d, out_scale)
    ctx.translate(x, y)
    ctx.scale(1.0 / scale, 1.0 / scale)
    ctx.set_source_surface(img, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
    if alpha >= 0.999:
        ctx.paint()
    else:
        ctx.paint_with_alpha(alpha)
    ctx.restore()
