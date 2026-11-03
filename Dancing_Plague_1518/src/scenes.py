"""The nine scenes. Each scene function draws one frame at global time t on a cairo context whose
surface is W*os x H*os pixels, and returns the 'look' for the finishing pass (darkness, tint, paper).
Characters are animated on twos with line boil; the camera and environment move on every frame."""
import math

import cairo
import numpy as np

from core import (PAL, W, H, EV, SCENES, Camera, draw_layer, keys, smooth, smoother, ease_out, ease_in, clamp, ramp, lerp,
                  twos, boil_seed, hash01, fnoise, set_c, ink_shape, ink_line, ellipse_pts, soft_glow, mix, shade_c,
                  path_smooth, taper_stroke, hatch_lines, load_png)
from figures import make_char, draw_figure
import poses
from sets import PS
from props import handcart, fog_bank, dust, smoke, bird, ink_splats, candle


def S(key):
    return SCENES[key]['start'], SCENES[key]['end']


# ----------------------------------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------------------------------
class Actor:
    def __init__(self, c, X, z, face, fn, bloom=None, d=None, name=''):
        self.c, self.X, self.z, self.face, self.fn, self.bloom, self.d, self.name = c, X, z, face, fn, bloom, d, name


def street_depth(z):
    return 1.0 if z < 7 else (0.7 if z < 18 else 0.45)


def d_eff(d, cam):
    """Close in, the street zooms as one picture; parallax opens up as the camera pulls back."""
    w = clamp((1.9 - cam.z) / 0.8)
    return 1.0 - (1.0 - d) * w


def draw_actor_street(ctx, cam, a, t, os_, extra_x=0.0):
    tt = twos(t)
    p = a.fn(tt)
    face = a.face(tt) if callable(a.face) else a.face
    X = a.X(tt) if callable(a.X) else a.X
    x, y = PS.p(X + extra_x, 0, a.z)
    s = PS.f / a.z / 100.0
    d = d_eff(a.d if a.d is not None else street_depth(a.z), cam)
    sx, sy = cam.world_to_screen(x, y, d)
    sc = s * cam.z ** d
    if sx < -400 * sc or sx > W + 400 * sc:
        return
    ctx.save()
    ctx.scale(os_, os_)
    if a.bloom is not None and t < a.bloom + 0.5:
        u = clamp((t - a.bloom) / 0.45)
        if u <= 0:
            ctx.restore()
            return
        cx, cy = sx, sy - 95 * sc
        R = 130 * sc * ease_out(u) * 1.15
        blot = np.array([[cx + math.cos(q) * R * (0.85 + 0.3 * hash01(a.c['seed'], k)), cy + math.sin(q) * R * 1.35 * (0.85 + 0.3 * hash01(a.c['seed'], k, 2))]
                         for k, q in enumerate(np.linspace(0, 2 * math.pi, 22, endpoint=False))])
        ctx.save()
        path_smooth(ctx, blot, True)
        ctx.clip()
        draw_figure(ctx, a.c, p, sx, sy, sc, face, pix=sc * os_, boil_k=boil_seed(t))
        ctx.restore()
        # the spreading ink edge
        ink_shape(ctx, blot, None, lw=max(1.5, 4 * sc * (1 - u)), ink=PAL['ink'], line_alpha=0.7 * (1 - u), seed=a.c['seed'])
        ink_splats(ctx, cx, cy, R, a.c['seed'], alpha=0.8 * (1 - u))
    else:
        draw_figure(ctx, a.c, p, sx, sy, sc, face, pix=sc * os_, boil_k=boil_seed(t))
    ctx.restore()


STREET_LAYERS = [('street_sky.png', 0.25, 1.0, 0, 0, 300), ('street_far.png', 0.45, 1.25, 0, 0, 18),
                 ('street_mid.png', 0.7, 1.5, 0, 0, 7), ('street_near.png', 1.0, 2.0, 0, 0, 0)]


def draw_street(ctx, cam, actors, t, os_, night=0.0, patch=True, fog=0.3, props_fn=None):
    """Composite the street layers far to near, with each band's characters drawn on its own plane."""
    bands = [(300, 1e9), (18, 300), (7, 18), (0, 7)]
    order = sorted(actors, key=lambda a: -a.z)
    for (name, d, sc, x, y, zmin), (b0, b1) in zip(STREET_LAYERS, bands):
        d = d_eff(d, cam)
        draw_layer(ctx, cam, name, d, os_, x, y, sc)
        if name == 'street_near.png' and patch and cam.z > 1.6:
            draw_layer(ctx, cam, 'street_patch.png', 1.0, os_, 250, 1330, 4.5)
        if name == 'street_far.png':
            ctx.save()
            cam.apply(ctx, d, os_)
            fog_bank(ctx, -200, 700, 1480, 520, fog, t, speed=10, seed=2)
            for k in range(3):
                smoke(ctx, 300 + k * 260, 520 + 40 * k, 1.2, t, seed=k)
            ctx.restore()
        if props_fn:
            props_fn(ctx, cam, b0, b1)
        for a in order:
            if b0 <= a.z < b1:
                draw_actor_street(ctx, cam, a, t, os_)
    ctx.save()
    cam.apply(ctx, 1.0, os_)
    fog_bank(ctx, -300, 900, 1700, 700, fog * 0.55, t, speed=18, seed=4)
    ctx.restore()


# ----------------------------------------------------------------------------------------------
# Scene 1 - THE FIRST DANCER
# ----------------------------------------------------------------------------------------------
DANCER = make_char(1518, 'f', 'adult', gown=PAL['burg3'], apron=PAL['linen2'], sleeve=shade_c(PAL['burg3'], -0.2), head='coif',
                   skin=PAL['skin'], eye=1.08, nose=0.95, jaw=1.0, hem=9.0)


def dancer_pose(tt, energy=1.0, tired=0.0):
    return poses.dance('whirl', tt, 1518, energy, tired)


def onlookers_s1():
    t_turn = EV['heads_turn'][0]
    A = []
    spec = [  # (seed, sex, age, X, z, face, kind, delay)
        (21, 'f', 'adult', -0.98, 3.25, 1, 'mouth', 0.0),
        (22, 'm', 'adult', 1.08, 3.6, -1, 'point', 0.25),
        (23, 'f', 'old', -2.05, 6.2, 1, 'cross', 0.1),
        (24, 'm', 'adult', 2.25, 6.8, -1, 'recoil', 0.35),
        (25, 'm', 'child', -1.75, 8.2, 1, 'stare', 0.2),
        (26, 'f', 'young', 2.4, 9.5, -1, 'whisper', 0.5),
        (27, 'm', 'old', -2.4, 11.5, 1, 'stare', 0.4),
        (28, 'f', 'adult', 1.9, 13.0, -1, 'stare', 0.6),
        (29, 'm', 'young', -1.2, 16.0, 1, 'stare', 0.7),
        (30, 'f', 'adult', 0.9, 21.0, -1, 'stare', 0.8),
    ]
    for seed, sex, age, X, z, face, kind, dl in spec:
        c = make_char(seed, sex, age)
        A.append(Actor(c, X, z, face, (lambda kind, seed, dl: lambda tt: poses.react(tt, t_turn + dl, seed, kind, turn=0.3))(kind, seed, dl)))
    # a man crossing the street who stops to look
    c = make_char(31, 'm', 'adult')
    def walker_X(tt):
        return -2.6 + 0.9 * min(tt, t_turn + 0.2) * 1.0
    def walker_pose(tt):
        if tt < t_turn + 0.2:
            return poses.walk(tt, 31)
        p = poses.react(tt, t_turn + 0.2, 31, 'stare', turn=0.6)
        return p
    A.append(Actor(c, walker_X, 10.5, 1, walker_pose))
    return A


S1_ACTORS = None


def scene_dancer(ctx, t, os_):
    global S1_ACTORS
    if S1_ACTORS is None:
        S1_ACTORS = onlookers_s1()
    a, b = S('dancer')
    u = t - a
    # camera: on her feet, tilt up to her face, then pull back to show the crowd and the street
    cy = keys(u, [(0.0, 1455.0), (1.2, 1440.0), (2.6, 1010.0), (5.0, 975.0), (6.6, 965.0)], smoother)
    z = keys(u, [(0.0, 4.3), (1.2, 4.1), (2.6, 3.0), (5.0, 1.12), (6.6, 1.0)], smoother)
    cx = 540 + 10 * math.sin(u * 0.8)
    cam = Camera(cx, cy, z, roll=0.012 * math.sin(u * 0.6))
    dancer = Actor(DANCER, 0.0, 4.0, 1, lambda tt: dancer_pose(tt), name='dancer')
    draw_street(ctx, cam, S1_ACTORS + [dancer], t, os_, fog=0.25)
    return dict(dark=0.0, desat=0.22, tint=(1.0, 0.95, 0.86), vig=0.5)


# ----------------------------------------------------------------------------------------------
# Scene 3 - IT SPREADS
# ----------------------------------------------------------------------------------------------
S3_ACTORS = None


def spread_actors():
    b1, b2, b3 = EV['bloom1'][0], EV['bloom2'][0], EV['bloom3'][0]
    styles = ['jig', 'convulse', 'stomp', 'sway', 'twirl', 'jig', 'convulse', 'stomp']
    A = []
    A.append(Actor(DANCER, 0.0, 4.0, 1, lambda tt: dancer_pose(tt, 0.95, 0.15), name='dancer'))
    # beat 1: the first to join her
    c = make_char(41, 'm', 'adult', coat=PAL['brown'], head='flat')
    A.append(Actor(c, 1.05, 4.6, -1, lambda tt: poses.dance('jig', tt, 41), bloom=b1))
    # beat 2: several
    pos2 = [(-1.2, 5.2), (1.9, 6.4), (-2.0, 7.6), (0.6, 8.5), (-0.6, 10.5)]
    for i, (X, z) in enumerate(pos2):
        sd = 50 + i
        c = make_char(sd, None, ['adult', 'young', 'old', 'adult', 'young'][i])
        st = styles[i + 1]
        face = (lambda sd: (lambda tt: poses.twirl_face(tt, sd)))(sd) if st == 'twirl' else (1 if X < 0 else -1)
        A.append(Actor(c, X, z, face, (lambda st, sd: lambda tt: poses.dance(st, tt, sd))(st, sd), bloom=b2 + 0.12 * i))
    # beat 3: a crowded street
    rng = np.random.default_rng(9)
    for i in range(16):
        sd = 70 + i
        z = rng.uniform(5.5, 24)
        X = rng.uniform(-2.5, 2.5)
        if abs(X) < 0.5 and z < 7:
            X += 1.2
        c = make_char(sd, None, None)
        st = styles[i % len(styles)]
        face = (lambda sd: (lambda tt: poses.twirl_face(tt, sd)))(sd) if st == 'twirl' else (1 if hash01(sd, 1) < 0.5 else -1)
        A.append(Actor(c, X, z, face, (lambda st, sd: lambda tt: poses.dance(st, tt, sd, 1.0, 0.2 * hash01(sd, 3)))(st, sd),
                       bloom=b3 + 0.08 * i))
    # onlookers pressed against the walls
    for i, (X, z, face) in enumerate([(-2.6, 5.0, 1), (2.7, 5.6, -1), (-2.7, 9.0, 1), (2.75, 12.0, -1)]):
        sd = 95 + i
        c = make_char(sd, None, 'adult')
        A.append(Actor(c, X, z, face, (lambda sd: lambda tt: poses.react(tt, -10, sd, ['mouth', 'cross', 'recoil', 'stare'][sd % 4]))(sd)))
    return A


def scene_spread(ctx, t, os_):
    global S3_ACTORS
    if S3_ACTORS is None:
        S3_ACTORS = spread_actors()
    a, b = S('spread')
    u = t - a
    z = keys(u, [(0.0, 1.55), (1.2, 1.45), (2.8, 1.22), (4.0, 1.06), (6.0, 1.0)], smoother)
    cy = keys(u, [(0.0, 1180.0), (1.2, 1170.0), (2.8, 1080.0), (4.0, 1000.0), (6.0, 975.0)], smoother)
    cx = 540 + 16 * math.sin(u * 0.5)
    cam = Camera(cx, cy, z, roll=0.02 * math.sin(u * 0.9) * ramp(u, 2.5, 5))
    draw_street(ctx, cam, S3_ACTORS, t, os_, fog=0.3 + 0.1 * ramp(u, 2, 5))
    return dict(dark=0.12 + 0.06 * ramp(u, 0, 5), desat=0.26, tint=(1.0, 0.94, 0.85), vig=0.55)


# ----------------------------------------------------------------------------------------------
# Scene 9 - THE FINAL MYSTERY (the empty street)
# ----------------------------------------------------------------------------------------------
def scene_end_street(ctx, t, os_):
    a, b = S('end')
    u = t - a
    # a slow push down the empty street, then a tilt down to the cobbles where she danced
    z = keys(u, [(0.0, 1.0), (2.6, 1.32), (4.4, 4.2), (6.0, 4.3)], smoother)
    cy = keys(u, [(0.0, 960.0), (2.6, 1080.0), (4.4, 1455.0), (6.0, 1460.0)], smoother)
    cam = Camera(540 + 6 * math.sin(u * 0.4), cy, z)
    draw_street(ctx, cam, [], t, os_, night=1.0, fog=0.55)
    ctx.save()
    cam.apply(ctx, 1.0, os_)
    dust(ctx, t, 0, 600, 1080, 1700, n=50, seed=9, size=2.2, col=PAL['parch2'], alpha=0.35, speed=4)
    ctx.restore()
    return dict(dark=0.62, desat=0.42, tint=(0.88, 0.9, 0.95), vig=0.75)
