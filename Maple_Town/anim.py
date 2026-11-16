"""Animate the Maple Town story: nine shots in the town built by town.py, timed to the narration (build/lines.json).

  $BLENDER -b -P anim.py -- --test          # one frame from each shot -> build/test/
  $BLENDER -b -P anim.py -- --render K N    # frames with index % N == K -> build/frames/ (run N copies in parallel)
Frames are rendered at 15 per second (animation 'on twos') at 540 x 960 and assembled at 30 fps by post.py.
"""
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import town as T  # noqa: E402

L = json.load(open(os.path.join(ROOT, 'build', 'lines.json')))
DUR = 38.0
RFPS = 15
GREY = dict(shirt='8b9099', pants='3a3f4a', shoes='e8e8ec', hood='8b9099')
FOLK = [dict(shirt='e2574b', hair='5a3a22', hair_style='swoop', sleeves='short', stripe='ffffff', acc=('headphones',)),
        dict(shirt='b06fd6', pants='f4f1e4', shoes='ff7fb0', hair='f0c05a', hair_style='long', skin='f7d2b0'),
        dict(shirt='27408a', pants='27408a', shoes='15171c', hair='1d1a18', hair_style='buzz', skin='8d5a3c', hat='cap', logo='ffd23f'),
        dict(shirt='57b56a', hair='c9903c', hair_style='flat'),
        dict(shirt='e9ebf0', pants='1c1e24', hair='7fa8e8', hair_style='spiky', logo='20242c'),
        dict(shirt='f0b63a', hair='1d1a18', hair_style='buns', skin='c98e63')]
ROB = dict(shirt='23262e', pants='15171c', shoes='15171c', mask=True, skin='e0b08a')


def sm(t, a, b):
    x = min(1.0, max(0.0, (t - a) / max(b - a, 1e-6)))
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def walk(P, ph, amp=0.7, bob=0.12):
    s = math.sin(ph)
    T.pose(P, arm_l=s * amp, arm_r=-s * amp, leg_l=-s * amp, leg_r=s * amp)
    P['root'].location.z = P['root'].get('z0', 0.0) + abs(math.cos(ph)) * bob


def place(P, x, y, rot_deg, z=None):
    P['root'].location.x, P['root'].location.y = x, y
    if z is not None:
        P['root']['z0'] = z
        P['root'].location.z = z
    P['root'].rotation_euler[2] = math.radians(rot_deg)


def cam(loc, look, lens=None):
    c = bpy.context.scene.camera
    c.location = loc
    c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if lens:
        c.data.lens = lens


def text(body, loc, size, col, emit=3.0):
    bpy.ops.object.text_add(location=loc)
    o = bpy.context.object
    o.data.body = body
    o.data.align_x = 'CENTER'
    o.data.align_y = 'CENTER'
    o.data.size = size
    o.data.extrude = 0.04
    o.data.materials.append(T.mat(col, 0.5, emit))
    return o


def face_cam(o):
    o.rotation_euler = bpy.context.scene.camera.rotation_euler


def base(mode):
    T.reset()
    T.R = random.Random(7)
    T.setup(12, 50)
    T.world(night=mode == 'night', sunset=mode == 'sunset')
    T.build_town(night=mode == 'night')
    if mode != 'night':
        T.clouds()
    T.camera((0, -20, 5), (0, 0, 3), 30)


def folk(spots, face='scared'):
    out = []
    for i, (x, y, r) in enumerate(spots):
        c = T.character(f'f{i}', (x, y, 0.3), math.radians(r), face=face, **FOLK[i % len(FOLK)])
        c['root']['z0'] = 0.3
        out.append(c)
    return out


SPOTS = [(8, 5.8, 200), (11.5, 6.6, 215), (-13, 6.2, 150), (1, -6.4, 20), (15, -6.2, 330), (-9, -6.0, 60)]


# ------------------------------------------------------------------------------------------------ shots
def s1():
    base('day')
    k = T.character('kid', face='calm', **GREY)
    fs = folk(SPOTS)

    def upd(t, d):
        u = t / d
        place(k, -18 + 15 * u, -0.4, 90, 0.12)
        walk(k, t * 7.5, 0.55)
        for i, f in enumerate(fs):
            x, y, r = SPOTS[i]
            back = sm(t, 0.6 + i * 0.25, 1.6 + i * 0.25)
            place(f, x, y + (1.6 if y > 0 else -1.6) * back, r)
            T.pose(f, arm_l=-2.5 * back, arm_r=-2.5 * back, lean=-0.18 * back, head=(0, 0, 0))
        e = sm(t, 0.0, d * 0.85)
        cam(lerp((36, -3.5, 15), (9, -2.2, 4.0), e), lerp((-6, 0, 2), (-8, 0.2, 3.8), e), 28)
    return upd


def s2():
    base('sunset')
    k = T.character('kid', face='calm', **GREY)

    def upd(t, d):
        u = t / d
        place(k, -23.5, -5.6 - 2.2 * sm(t, 0, d * 0.6), 180, 0.3)
        walk(k, t * 7.0, 0.5 * (1 - sm(t, d * 0.55, d * 0.65)))
        cam(lerp((-15, 9.5, 6.5), (-21.5, 3.0, 4.6), sm(t, 0, d)), (-23.5, -9, 4.2), 32)
    return upd


def s2b():
    base('night')
    k = T.character('kid', face='calm', **GREY)

    def upd(t, d):
        x = -14 + 10 * t / d
        place(k, x, -1.0, 90, 0.12)
        walk(k, t * 7.0, 0.5)
        cam((x + 7.0, -3.7, 2.7), (x + 0.5, -1.0, 3.9), 34)
    return upd


def s3():
    base('day')
    a = T.character('a', face='scared', **FOLK[0])
    b = T.character('b', face='scared', **FOLK[2])
    k = T.character('kid', face='calm', **GREY)
    place(a, 6.0, 5.8, 250, 0.3)
    place(b, 9.2, 5.6, 110, 0.3)

    def upd(t, d):
        T.pose(a, arm_r=-2.2, head=(0.1 * math.sin(t * 9), 0, 0.5), lean=-0.1)
        T.pose(b, arm_l=-1.2, arm_r=-1.4, head=(0, 0, -0.5 + 0.1 * math.sin(t * 7)), lean=-0.15)
        place(k, 30 - 13 * t / d, 2.8, 270, 0.12)
        walk(k, t * 7.0, 0.5)
        cam(lerp((7.2, -3.2, 1.8), (7.8, -2.4, 2.0), t / d), (7.6, 5.8, 4.3), 34)
    return upd


def robbers(n=2, x0=2.5, y=-5.6):
    out = []
    for i in range(n):
        r = T.character(f'rob{i}', face='angry', **ROB)
        bag = T.box(f'bag{i}', (1.5, 1.2, 1.7), (0, 0, 0), 'b9a26a', None, 0.3)
        T.box('bagm', (0.6, 0.1, 0.6), (0, -0.62, 0.1), '3f8f4a', bag, 0.05)
        out.append((r, bag))
    return out


def s4():
    base('night')
    rb = robbers()
    al = bpy.data.objects['alarm_l'].data

    def upd(t, d):
        al.energy = 9000 * (0.25 + 0.75 * (math.sin(t * 9) > 0))
        for i, (r, bag) in enumerate(rb):
            y = -9.0 + 4.6 * sm(t, 0.3 + i * 0.4, 2.6 + i * 0.4)
            x = 3.2 + i * 3.8
            place(r, x, y, 0 if True else 0, 0.3)
            r['root'].rotation_euler[2] = math.radians(180)
            walk(r, t * 8, 0.5 if y < -4.5 else 0.0)
            T.pose(r, arm_l=-1.1, arm_r=-1.1, leg_l=r['leg_l'].rotation_euler[0], leg_r=r['leg_r'].rotation_euler[0])
            bag.location = (x, y + 1.2, 2.3)
        cam(lerp((14, 9, 7.5), (9.5, 3.6, 4.2), sm(t, 0, d)), (5, -9, 4.6), 28)
    return upd


def barricade(x):
    for i, (dy, dz, c) in enumerate(((-3, 0.9, '8a5a34'), (-1, 0.9, '9a6a3c'), (1, 0.9, '8a5a34'), (3, 0.9, '9a6a3c'), (-2, 2.7, '9a6a3c'), (0, 2.7, '8a5a34'), (2, 2.7, '9a6a3c'), (0, 4.4, '8a5a34'))):
        T.box('crate', (1.9, 1.9, 1.8), (x, dy, dz), c, None, 0.06)
    for dy in (-5.2, 5.2):
        T.box('bar', (0.5, 2.6, 0.5), (x, dy, 1.6), 'ff3b30', None, 0.05, emit=1.0)
        T.box('barw', (0.52, 0.7, 0.52), (x, dy, 1.6), 'ffffff', None, 0.05)


def s4b():
    base('night')
    barricade(19)
    rb = robbers()

    def upd(t, d):
        for i, (r, bag) in enumerate(rb):
            place(r, 15.5, -2.2 + i * 4.4, 90, 0.12)
            T.pose(r, arm_l=-0.3, arm_r=-2.6 if i == 0 else -0.3, head=(0, 0, 0.3 * math.sin(t * 2 + i)))
            bag.location = (17, -3.8 + i * 7.6, 0.95)
        cam(lerp((2, -3.5, 2.6), (5, -3.0, 3.2), sm(t, 0, d)), (17, 0, 3.6), 30)
    return upd


def s5():
    base('night')
    fs = folk([(-4, 5.6, 280), (-1, 6.4, 270), (-6, -5.8, 80), (-2.5, -6.2, 95), (0.5, -5.6, 100), (-8, 6.0, 285)])
    k = T.character('kid', face='calm', **GREY)

    def upd(t, d):
        for i, f in enumerate(fs):
            T.pose(f, arm_l=-2.5, arm_r=-2.5, lean=-0.15, head=(0.03 * math.sin(t * 30 + i), 0, 0))
        st = d * 0.42
        x = -12 + 9 * sm(t, st, d + 0.6)
        place(k, x, -0.3, 90, 0.12)
        walk(k, t * 7.0, 0.55 if t > st else 0.0)
        cam(lerp((7, -1.0, 3.0), (5.5, -0.8, 3.4), t / d), (-4, 0, 3.8), 30)
    return upd


def s6():
    base('night')
    barricade(19)
    rb = robbers()
    k = T.character('kid', face='calm', **GREY)
    bub = T.box('bubble', (4.4, 0.2, 1.7), (0, 0, 0), 'ffffff', None, 0.3, emit=1.2)
    tx = text('leave.', (0, 0, 0), 1.15, '14161c', 0.0)
    tw = L[12]['end'] - L[12]['start']

    def upd(t, d):
        x = 6.5 + 5.5 * sm(t, 0, d * 0.6)
        place(k, x, 0.2, 90, 0.12)
        walk(k, t * 7.0, 0.55 * (1 - sm(t, d * 0.55, d * 0.62)))
        for i, (r, bag) in enumerate(rb):
            place(r, 15.5, -2.2 + i * 4.4, 270, 0.12)
            T.pose(r, arm_l=-0.3, arm_r=-0.3)
            bag.location = (17, -3.8 + i * 7.6, 0.95)
        cam(lerp((3.0, -5.6, 3.6), (5.0, -5.6, 3.4), sm(t, 0, d)), (13.0, 0.4, 3.9), 26)
        s = sm(t, tw * 0.72, tw * 0.82)
        bub.scale = tx.scale = (s, s, s)
        bub.location = (x + 0.3, 0.1, 6.9)
        tx.location = (x + 0.3, -0.25, 6.9)
        face_cam(tx)
        bub.rotation_euler[2] = tx.rotation_euler[2]
    return upd


def s7():
    base('night')
    barricade(19)
    rb = robbers()
    k = T.character('kid', face='calm', **GREY)
    place(k, 12, 0.2, 90, 0.12)
    t_run = L[14]['start'] - L[13]['start']

    def upd(t, d):
        for i, (r, bag) in enumerate(rb):
            run = sm(t, t_run + 0.5 + i * 0.15, d + 0.5)
            y0 = -2.2 + i * 4.4
            sgn = -1 if i == 0 else 1
            place(r, 15.5 - 2 * run, y0 + sgn * 26 * run, 270 if run < 0.02 else (180 if i == 0 else 0), 0.12)
            if t < t_run + 0.4:
                T.pose(r, arm_l=-2.6, arm_r=-2.6, head=(0.05 * math.sin(t * 40), 0, 0), lean=-0.2)
            else:
                walk(r, t * 13, 0.95, 0.25)
            drop = sm(t, t_run, t_run + 0.35)
            bag.location = (16.6, y0 * 1.2, 2.4 - 1.5 * drop)
        cam(lerp((4.5, -6.3, 3.0), (5.4, -6.1, 3.3), sm(t, 0, d)), (14.0, 0.2, 3.4), 30)
    return upd


def s8():
    base('night')
    k = T.character('kid', face='calm', **GREY)
    place(k, 12, 0.2, 325, 0.12)
    crown = T.box('crown', (1.3, 1.3, 0.34), (0, 0, 1.62), 'ffcc33', k['head'], 0.04, rough=0.2, emit=1.5)
    for i in range(8):
        a = i / 8 * 2 * math.pi
        T.cone('cp', 0.17, 0.42, (math.cos(a) * 0.53, math.sin(a) * 0.53, 1.98), 'ffcc33', k['head'], verts=4)
    tag = text('OWNER', (12, 0.2, 7.5), 1.05, 'ffcc33', 4.0)
    l = bpy.data.lights.new('key', 'POINT')
    l.energy = 900
    l.color = (1.0, 0.85, 0.55)
    lo = bpy.data.objects.new('key', l)
    bpy.context.collection.objects.link(lo)
    lo.location = (9.5, -3.5, 5.5)
    rev = L[16]['start'] - L[15]['start']

    def upd(t, d):
        s = sm(t, rev + 0.05, rev + 0.4)
        over = 1 + 0.25 * math.sin(min(1, (t - rev) / 0.5) * math.pi) if t > rev else 1
        tag.scale = (s * over,) * 3
        crown.hide_render = s < 0.05
        for o in k['head'].children:
            if o.name.startswith('cp'):
                o.hide_render = s < 0.05
        l.energy = 900 + 1600 * s
        T.pose(k, head=(0.0, 0, 0.25 * sm(t, 0, 1.5)))
        cam(lerp((7.6, -6.0, 1.7), (8.3, -5.2, 2.1), sm(t, 0, d)), (12, 0.2, 5.0 + 0.5 * s), 30)
        face_cam(tag)
    return upd


def s9():
    base('day')
    k = T.character('kid', face='smile', **GREY)
    place(k, 1.2, 0.0, 325, 0.12)
    n = T.character('new', face='smile', shirt='4b8fe2', pants='4f9d4a', skin='f7d24a', shoes='4f9d4a')
    fs = folk([(-5, 5.6, 300), (8, 6.2, 230), (-3, -6.0, 60), (9, -5.8, 120)], face='happy')

    def upd(t, d):
        drop = sm(t, 0.2, 0.9)
        place(n, -2.6, -0.6, 35, 0.12 + 9 * (1 - drop))
        T.pose(n, arm_l=-0.3 * math.sin(t * 5), arm_r=-2.6 * sm(t, 1.4, 1.9) + 0.3 * math.sin(t * 9) * sm(t, 1.9, 2.0))
        T.pose(k, arm_r=-2.7 + 0.35 * math.sin(t * 9), head=(0, 0, 0.1))
        for i, f in enumerate(fs):
            T.pose(f, arm_l=-2.6 if i % 2 else 0, arm_r=-2.6, head=(0, 0, 0.2 * math.sin(t * 3 + i)))
            f['root'].location.z = 0.3 + 0.5 * abs(math.sin(t * 5 + i))
        cam(lerp((-0.7, -7.2, 3.4), (15, -3.6, 15), sm(t, 0.8, d)), (-0.7, 0, 3.6), 26)
    return upd


def st(i):
    return L[i]['start'] - 0.12 if i else 0.0


SHOTS = [(s1, st(0), st(2)), (s2, st(2), st(4)), (s2b, st(4), st(5)), (s3, st(5), st(7)), (s4, st(7), st(9) + 0.25), (s4b, st(9) + 0.25, st(10)),
         (s5, st(10), st(12)), (s6, st(12), st(13)), (s7, st(13), st(15)), (s8, st(15), st(17)), (s9, st(17), DUR)]


def render(sel, out, fmt):
    todo = {}
    for f in sel:
        t = f / RFPS
        k = next(i for i, (_, a, b) in enumerate(SHOTS) if a <= t < b or i == len(SHOTS) - 1)
        todo.setdefault(k, []).append(f)
    for k, fr in sorted(todo.items()):
        fn, a, b = SHOTS[k]
        fr = [f for f in fr if not os.path.exists(os.path.join(out, fmt % f))]
        if not fr:
            continue
        upd = fn()
        for f in fr:
            upd(f / RFPS - a, b - a)
            bpy.context.scene.render.filepath = os.path.join(out, fmt % f)
            bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    if argv[0] == '--test':
        out = os.path.join(ROOT, 'build', 'test')
        os.makedirs(out, exist_ok=True)
        want = [int(x) for x in argv[1:]] or range(len(SHOTS))
        render([int((SHOTS[k][1] + (SHOTS[k][2] - SHOTS[k][1]) * 0.7) * RFPS) for k in want], out, 't_%05d.png')
    else:
        k, n = int(argv[1]), int(argv[2])
        out = os.path.join(ROOT, 'build', 'frames')
        os.makedirs(out, exist_ok=True)
        render([f for f in range(int(DUR * RFPS)) if f % n == k], out, 'f_%05d.png')
