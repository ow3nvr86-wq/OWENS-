"""The Funny Town story: a town votes a dog in as mayor. Ten shots in the blocky town built by town.py, timed to the
narration (build/lines.json, build/words.json).

  $BLENDER -b -P anim.py -- --test [shot numbers]   # one frame from each shot -> build/test/
  $BLENDER -b -P anim.py -- --render K N            # frames with index % N == K -> build/frames/ (run N copies in parallel)
Frames are 15 per second at 540 x 960; post.py assembles them at 30 fps with captions and the soundtrack."""
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
WORDS = json.load(open(os.path.join(ROOT, 'build', 'words.json')))['words']
DUR = 34.0
RFPS = 15
CITIZENS = [dict(shirt='e2574b', hair='5a3a22', hair_style='swoop', sleeves='short', stripe='ffffff'),
            dict(shirt='b06fd6', pants='f4f1e4', shoes='ff7fb0', hair='f0c05a', hair_style='long', skin='f7d2b0'),
            dict(shirt='27408a', pants='27408a', shoes='15171c', hair='1d1a18', hair_style='buzz', skin='8d5a3c', hat='cap'),
            dict(shirt='57b56a', hair='c9903c', hair_style='flat'),
            dict(shirt='e9ebf0', pants='1c1e24', hair='7fa8e8', hair_style='spiky'),
            dict(shirt='f0b63a', hair='1d1a18', hair_style='buns', skin='c98e63')]
ROB = dict(shirt='23262e', pants='15171c', shoes='15171c', mask=True, skin='e0b08a')
MAIL = dict(shirt='3a6fd8', pants='2c3350', shoes='15171c', hair='5a3a22', hair_style='flat', hat='cap')


def wt(word, n=1):
    k = 0
    for w in WORDS:
        if w['w'].lower().strip('.,:') == word:
            k += 1
            if k == n:
                return w['start']
    raise KeyError(word)


def st(i):
    return L[i]['start'] - 0.12 if i else 0.0


def sm(t, a, b):
    x = min(1.0, max(0.0, (t - a) / max(b - a, 1e-6)))
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def place(P, x, y, rot_deg, z=None):
    P['root'].location.x, P['root'].location.y = x, y
    if z is not None:
        P['root'].location.z = z
        P['root']['z0'] = z
    P['root'].rotation_euler[2] = math.radians(rot_deg)


def walk(P, ph, amp=0.7, bob=0.12):
    s = math.sin(ph)
    T.pose(P, arm_l=s * amp, arm_r=-s * amp, leg_l=-s * amp, leg_r=s * amp)
    P['root'].location.z = P['root'].get('z0', 0.0) + abs(math.cos(ph)) * bob


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
    o.data.extrude = 0.05
    o.data.materials.append(T.mat(col, 0.5, emit))
    return o


def face_cam(o):
    o.rotation_euler = bpy.context.scene.camera.rotation_euler


def hide(P, h):
    def rec(o):
        o.hide_render = h
        for c in o.children:
            rec(c)
    rec(P['root'] if isinstance(P, dict) else P)


# ------------------------------------------------------------------------------------------------ animals
def animal(name, col='c8955a', light='f3e2c4', ear='8a5a34', cat=False, crown=False, sash=False):
    root = T.empty(name)
    P = {'root': root}
    T.box(name + '_body', (1.6, 3.0, 1.5) if not cat else (1.3, 2.7, 1.2), (0, 0, 1.95), col, root, 0.12)
    T.box(name + '_belly', (1.1, 2.0, 0.1), (0, 0, 1.2), light, root, 0.04)
    for nm, x, y in (('fl', -0.55, -1.05), ('fr', 0.55, -1.05), ('bl', -0.55, 1.05), ('br', 0.55, 1.05)):
        P[nm] = T.empty(f'{name}_{nm}', (x, y, 1.25), root)
        T.box(f'{name}_leg{nm}', (0.5, 0.5, 1.2), (0, 0, -0.6), col, P[nm], 0.06)
        T.box(f'{name}_paw{nm}', (0.52, 0.55, 0.25), (0, -0.03, -1.1), light, P[nm], 0.05)
    P['head'] = T.empty(name + '_head', (0, -1.5, 2.95), root)
    h = P['head']
    T.box(name + '_skull', (1.5, 1.4, 1.3), (0, -0.1, 0.05), col, h, 0.2)
    if not cat:
        T.box(name + '_snout', (0.8, 0.7, 0.55), (0, -0.95, -0.2), light, h, 0.12)
        T.box(name + '_nose', (0.32, 0.12, 0.25), (0, -1.32, -0.02), '14161c', h, 0.04)
        for sx in (-1, 1):
            T.box(name + '_ear', (0.36, 0.26, 0.95), (sx * 0.82, 0.05, 0.1), ear, h, 0.08, rot=(0.0, sx * 0.3, 0))
    else:
        T.box(name + '_snout', (0.5, 0.35, 0.3), (0, -0.85, -0.2), light, h, 0.1)
        T.box(name + '_nose', (0.18, 0.1, 0.14), (0, -1.05, -0.08), 'ff8fa3', h, 0.03)
        for sx in (-1, 1):
            T.cone(name + '_ear', 0.4, 0.8, (sx * 0.5, 0.0, 1.0), col, h, rot=(0, 0, 0), verts=4)
            for k in (-1, 1):
                T.box(name + '_wh', (0.7, 0.03, 0.03), (sx * 0.55, -1.0, -0.12 + k * 0.1), 'ffffff', h, 0.0, rot=(0, 0, sx * 0.1 * k))
    for sx in (-1, 1):
        T.oval(name + '_eye', 0.17, 0.2, (sx * 0.34, -0.82, 0.28), 'ffffff', h)
        T.oval(name + '_pup', 0.085, 0.11, (sx * 0.34, -0.835, 0.27), '14161c', h)
    P['brow_l'] = T.box(name + '_brow_l', (0.4, 0.04, 0.1), (-0.34, -0.83, 0.56), '2a1d14', h, 0.0)
    P['brow_r'] = T.box(name + '_brow_r', (0.4, 0.04, 0.1), (0.34, -0.83, 0.56), '2a1d14', h, 0.0)
    P['tail'] = T.empty(name + '_tail', (0, 1.5, 2.5), root)
    T.box(name + '_tailb', (0.3, 0.3, 1.2 if not cat else 1.9), (0, 0.2, 0.5 if not cat else 0.9), ear if not cat else col, P['tail'], 0.08, rot=(0.5, 0, 0))
    if crown:
        T.box(name + '_crown', (1.0, 1.0, 0.3), (0, 0, 0.82), 'ffcc33', h, 0.04, rough=0.2, emit=0.8)
        for k in range(6):
            a = k / 6 * 2 * math.pi
            T.cone(name + '_cp', 0.14, 0.4, (math.cos(a) * 0.4, math.sin(a) * 0.4, 1.15), 'ffcc33', h, verts=4)
    if sash:
        T.box(name + '_sash', (1.72, 0.5, 1.62), (0, -0.45, 1.95), 'd9342b', root, 0.06)
        T.box(name + '_star', (0.4, 0.06, 0.4), (0.0, -0.97, 2.1), 'ffd23f', root, 0.03, rot=(0, 0.78, 0))
    return P


def a_walk(P, ph, amp=0.8):
    s = math.sin(ph)
    P['fl'].rotation_euler[0], P['br'].rotation_euler[0] = s * amp, s * amp
    P['fr'].rotation_euler[0], P['bl'].rotation_euler[0] = -s * amp, -s * amp
    P['root'].location.z = P['root'].get('z0', 0.0) + abs(math.cos(ph)) * 0.1
    P['tail'].rotation_euler[1] = 0.5 * math.sin(ph * 2)


def a_wag(P, t, amp=0.7, rate=14):
    P['tail'].rotation_euler[1] = amp * math.sin(t * rate)


def a_sit(P, k):
    """k 0..1: the animal sits up on its haunches."""
    P['root'].rotation_euler[0] = -0.62 * k
    P['root'].location.z = P['root'].get('z0', 0.0) - 0.2 * k
    P['fl'].rotation_euler[0] = P['fr'].rotation_euler[0] = 0.62 * k
    P['bl'].rotation_euler[0] = P['br'].rotation_euler[0] = -1.1 * k
    P['head'].rotation_euler[0] = 0.55 * k


def a_back(P, k):
    """k 0..1: rolls onto its back, legs in the air."""
    P['root'].rotation_euler[0] = math.pi * k
    P['root'].location.z = P['root'].get('z0', 0.0) + 2.8 * k
    for n in ('fl', 'fr', 'bl', 'br'):
        P[n].rotation_euler[0] = 0.5 * k * (1 if n[0] == 'f' else -1) + 0.15 * math.sin(k * 20 + len(n))


def confetti(n=70, seed=3, spread=9.0):
    out = []
    cols = ['ff4b6e', 'ffd23f', '4bd1ff', '7be36a', 'b06fd6']
    for i in range(n):
        o = T.box('cf', (0.3, 0.3, 0.06), (0, 0, -99), cols[i % 5], None, 0.0, emit=1.2)
        out.append((o, random.Random(seed + i)))
    return out


def conf_upd(cf, t, t0, cx, cy, spread=9.0, life=3.0):
    for o, r in cf:
        u = t - t0 - r.uniform(0, 0.8)
        if u < 0 or u > life:
            o.location = (0, 0, -99)
            continue
        o.location = (cx + r.uniform(-spread, spread) + 1.5 * math.sin(u * 3 + r.random() * 6), cy + r.uniform(-spread, spread) * 0.6,
                      11 - 6.0 * u - r.uniform(0, 2))
        o.rotation_euler = (u * r.uniform(2, 6), u * r.uniform(2, 6), 0)


def base(mode='day'):
    T.reset()
    T.R = random.Random(7)
    T.setup(12, 50)
    T.world(night=mode == 'night', sunset=mode == 'sunset')
    T.build_town(night=mode == 'night')
    if mode != 'night':
        T.clouds()
    T.camera((0, -20, 5), (0, 0, 3), 30)


def podium():
    T.box('pd1', (5, 3.4, 0.7), (0, 6.8, 0.35), 'c9a15a', None, 0.1)
    T.box('pd2', (3.4, 2.4, 0.7), (0, 6.8, 1.05), 'dcb86a', None, 0.1)
    T.box('banner', (9, 0.25, 3.4), (0, 8.4, 3.6), 'd9342b', None, 0.1)
    t = text('MAYOR', (0, 8.2, 3.7), 1.5, 'ffffff', 1.5)
    t.rotation_euler = (math.pi / 2, 0, 0)


# ------------------------------------------------------------------------------------------------ shots
def s1():
    base('day')
    podium()
    bb = T.box('ballot_box', (2.2, 2.2, 2.8), (-2.5, 0.0, 1.4), 'e2574b', None, 0.15)
    T.box('slot', (1.2, 0.1, 0.25), (-2.5, -1.12, 2.6), '14161c', None, 0.02)
    cits = [T.character(f'c{i}', face='calm', **CITIZENS[i]) for i in range(5)]
    biscuit = animal('bis', crown=True, sash=True)
    cf = confetti()
    td = wt('dog')

    def upd(t, d):
        for i, c in enumerate(cits):
            arrive = 1.4 + 0.6 * i
            u = sm(t, 0.0, arrive)
            x = -24 - 3 * i + (-4.4 - (-24 - 3 * i) + 0.0) * u
            x = -24 + (-5.2 - 1.4 * (i % 2) + 24) * u if i < 3 else -5.2 + 1.0 * i - 0.0
            y = -0.9 - 1.0 * i if i < 3 else 1.2 + 0.9 * (i - 3)
            if i >= 3:
                x = -9 + (-3.6 - 1.2 * (i - 3) + 9) * sm(t, 0.2, 1.0 + 0.5 * i) if i == 3 else -5.4
            place(c, x, y, 90 if i < 3 else 0, 0.12)
            moving = (u < 0.97) if i < 3 else (t < 1.5)
            if moving:
                walk(c, t * 7 + i, 0.55)
            else:
                T.pose(c, arm_l=-0.3, arm_r=-1.4 * (math.sin(t * 6 + i) > 0.3) if t < td else -2.6, head=(0.1, 0, 0))
            if t > td:
                T.pose(c, arm_l=-2.6, arm_r=-2.6)
        k = sm(t, td, td + 0.35)
        biscuit['root'].scale = (max(k, 0.001),) * 3
        place(biscuit, 0, 6.8, 0, 1.4)
        a_wag(biscuit, t)
        conf_upd(cf, t, td, 0, 5, 9)
        e = sm(t, 0, d * 0.9)
        cam(lerp((20, -3.0, 8.5), (13.0, -3.2, 4.6), e), lerp((0, 3.0, 3.0), (-1, 3.5, 3.0), e), 28)
    return upd


def s2():
    base('day')
    podium()
    biscuit = animal('bis', crown=True, sash=True)
    place(biscuit, 0, 6.8, 0, 1.4)
    cf = confetti(60, 11)
    tb = wt('biscuit') - st(2)
    txt = text('BISCUIT', (0, 6.8, 6.6), 1.5, 'ffd23f', 3.0)

    def upd(t, d):
        a_wag(biscuit, t, 0.8, 16)
        biscuit['head'].rotation_euler[2] = 0.18 * math.sin(t * 2.2)
        conf_upd(cf, t, -1, 0, 6, 8, 3.5)
        s = sm(t, tb, tb + 0.3)
        txt.scale = (s,) * 3
        cam(lerp((3.4, 1.8, 3.6), (2.6, 2.6, 3.8), sm(t, 0, d)), (0, 6.8, 3.6), 40)
        face_cam(txt)
    return upd


def s3():
    base('day')
    podium()
    biscuit = animal('bis', crown=True, sash=True)
    sad = T.character('sad', face='scared', shirt='5b8fd6', pants='2c3350', hair='3a2a1e', hair_style='flat')
    glad = T.character('glad', face='happy', shirt='5b8fd6', pants='2c3350', hair='3a2a1e', hair_style='flat')
    place(sad, -5.5, 5.6, 100, 0.12)
    place(glad, -5.5, 5.6, 100, 0.12)
    ts = wt('sad') - st(3)
    cf = confetti(60, 21)

    def upd(t, d):
        u = sm(t, 0.3, 1.9)
        place(biscuit, 0 - 4.0 * u, 6.8 - 0.6 * u, 270 if u > 0.02 else 0, 1.4 if u < 0.02 else 0.12)
        if u > 0.02 and u < 0.99:
            a_walk(biscuit, t * 11)
        else:
            a_wag(biscuit, t, 0.8, 16)
            for n in ('fl', 'fr', 'bl', 'br'):
                biscuit[n].rotation_euler[0] = 0
        swap = t > ts
        hide(sad, swap)
        hide(glad, not swap)
        T.pose(sad, arm_l=0.1, arm_r=0.1, head=(0.5, 0, 0), lean=0.15)
        jump = abs(math.sin((t - ts) * 8)) * 0.7 if swap else 0.0
        T.pose(glad, arm_l=-2.7, arm_r=-2.7, head=(0, 0, 0.2 * math.sin(t * 7)))
        glad['root'].location.z = 0.12 + jump
        conf_upd(cf, t, ts, -5.5, 5.6, 6, 2.5)
        cam(lerp((2.5, 1.0, 3.4), (1.2, 1.4, 3.8), sm(t, 0, d)), (-3.5, 5.8, 3.2), 34)
    return upd


def s4():
    base('day')
    podium()
    mail = T.character('mail', face='happy', **MAIL)
    pack = T.box('pack', (1.6, 0.7, 1.8), (0, 0, -99), 'f0b63a', None, 0.2)
    letters = [T.box('let', (0.7, 0.04, 0.5), (0, 0, -99), 'ffffff', None, 0.0) for _ in range(5)]
    dog = animal('bis', crown=True, sash=True)
    tb = wt('banned') - st(4)
    to = wt('obviously') - st(4)

    def upd(t, d):
        run = sm(t, tb, tb + 2.4)
        xm = -5 + 38 * run * run
        place(mail, xm, 1.4, 90, 0.12)
        if t > tb:
            walk(mail, t * 13, 1.0, 0.25)
            pack.location = (xm - 2.5, 1.4 + 1.0, 0.9 + abs(math.sin(t * 9)) * 1.5)
        else:
            T.pose(mail, arm_l=0.0, arm_r=-1.3, head=(0.0, 0, 0))
            pack.location = (xm - 0.2, 0.2, 1.7)
        for i, l in enumerate(letters):
            l.location = (xm + 1.4 + 0.2 * i, 1.0, 2.4 - 0.1 * i) if t <= tb else (xm + 1.4 + 0.5 * i + (t - tb) * 5, 1.0, 2.4 + 3 * (t - tb) - 5 * (t - tb) ** 2 + 0.1 * i)
        # the dog: facing the mailman, then chasing him, then sitting proudly
        chase = sm(t, tb + 0.15, tb + 1.9)
        xd = -1.0 + 15.0 * chase
        stop = sm(t, tb + 1.9, to)
        place(dog, xd, 1.6, 90 if t < to + 0.2 else 20, 0.12)
        if t < to - 0.05:
            a_walk(dog, t * 14, 0.9) if t > tb else a_wag(dog, t, 0.7)
        else:
            for n in ('fl', 'fr', 'bl', 'br'):
                dog[n].rotation_euler[0] = 0
            a_sit(dog, sm(t, to - 0.05, to + 0.35))
            a_wag(dog, t, 0.9, 15)
        dog['head'].rotation_euler[2] = 0.0
        cx = max(2.0, min(xm - 2.0, 20.0))
        cam((cx + 9, -3.4, 3.6), (cx - 1.0, 1.4, 3.4), 28)
    return upd


def s5():
    base('day')
    podium()
    dog = animal('bis', crown=True, sash=True)
    place(dog, 0, 6.8, 0, 1.4)
    cits = [T.character(f'c{i}', face='happy', **CITIZENS[i]) for i in range(4)]
    snacks = []
    cols = ['e8a33a', 'd9342b', 'f2d36b', 'c98b4f', '8fd45a', 'f08ac0', 'ff9e5a', 'ffd23f', 'e87a5a', 'b9774a']
    for i in range(10):
        snacks.append(T.box('sn', (0.9, 0.9, 0.6), (0, 0, -99), cols[i], None, 0.18))
    t0 = st(6)

    def upd(t, d):
        a_wag(dog, t, 0.9, 15)
        for i, c in enumerate(cits):
            u = sm(t, 0.1 + 0.45 * i, 1.0 + 0.45 * i)
            x = (-13 + 0.6 * i) + (6.2 - 1.0 * i - (-13 + 0.6 * i)) * u
            place(c, x, 3.0 + 0.4 * i, 90, 0.12)
            if u < 0.98:
                walk(c, t * 7 + i, 0.5)
                T.pose(c, arm_l=0.0, arm_r=-1.2, leg_l=c['leg_l'].rotation_euler[0], leg_r=c['leg_r'].rotation_euler[0])
            else:
                T.pose(c, arm_l=0.1, arm_r=-0.2, head=(0.0, 0, 0.0))
            for k in range(2):
                n = i * 2 + k
                if n < 10:
                    drop = sm(t, 0.95 + 0.45 * i + 0.12 * k, 1.25 + 0.45 * i + 0.12 * k)
                    x_ = 8.2 + 0.9 * (n % 3)
                    z_ = 0.3 + 0.62 * (n // 3)
                    if drop > 0:
                        snacks[n].location = (x_, 4.6 + 0.4 * (n % 2), 3.2 * (1 - drop) + z_ if drop < 1 else z_)
        cam(lerp((14.5, -3.0, 4.4), (13.0, -2.4, 4.2), sm(t, 0, d)), (4.0, 4.6, 2.8), 26)
    return upd


def bank_scene(mode='day'):
    base(mode)
    for o in list(bpy.data.objects):          # clear the lamps and trees in front of the bank so the camera has a clear view
        if o.type == 'EMPTY' and o.parent is None and o.name.split('.')[0] in ('lamp', 'tree') and o.location.y < 0 and -6 < o.location.x < 17:
            hide(o, True)
    rob = T.character('rob', face='angry', **ROB)
    bag = T.box('bag', (1.4, 1.0, 1.5), (0, 0, -99), 'b9a26a', None, 0.3)
    return rob, bag


def s6():
    rob, bag = bank_scene()
    cit = T.character('c0', face='scared', **CITIZENS[3])
    place(cit, 15, -6.6, 90, 0.12)

    def upd(t, d):
        u = sm(t, 0.1, d - 0.2)
        place(rob, 24 - 18.6 * u, -4.4 - 3.3 * u, 283, 0.12)
        ph = t * 5.0
        T.pose(rob, arm_l=0.3, arm_r=-0.7, leg_l=math.sin(ph) * 0.5, leg_r=-math.sin(ph) * 0.5, head=(0.0, 0, 0.4 * math.sin(t * 3)), lean=0.25)
        rob['root'].location.z = 0.12 + abs(math.cos(ph)) * 0.18
        bag.location = (rob['root'].location.x - 1.0, rob['root'].location.y + 0.8, 1.9)
        T.pose(cit, arm_l=-2.5, arm_r=-2.5, lean=-0.1)
        cam(lerp((-6.5, -3.0, 3.6), (-5.0, -3.2, 3.4), sm(t, 0, d)), (7.5, -7.2, 3.0), 26)
    return upd


def s7():
    rob, bag = bank_scene()
    dog = animal('bis', crown=True, sash=True)
    place(rob, 5.6, -7.6, 180, 0.12)
    tw = wt('walked') - st(8)
    ts = wt('sat') - st(8)
    sweat = [T.box('sw', (0.18, 0.1, 0.3), (0, 0, -99), '6fc3ff', None, 0.05, emit=1.0) for _ in range(6)]

    def upd(t, d):
        u = sm(t, tw - 0.1, ts + 0.1)
        place(dog, -3.0 + 9.0 * u, -4.6 - 1.6 * u, 90 - 105 * sm(t, ts - 0.3, ts + 0.1), 0.12)
        if u < 0.98:
            a_walk(dog, t * 10, 0.85)
        else:
            for n in ('fl', 'fr', 'bl', 'br'):
                dog[n].rotation_euler[0] = 0
            dog['root'].rotation_euler[2] = math.radians(-15)
            a_sit(dog, sm(t, ts, ts + 0.4))
            dog['tail'].rotation_euler[1] = 0.0
        sh = sm(t, ts + 0.3, ts + 1.2)
        T.pose(rob, arm_l=-0.3, arm_r=-0.3, head=(0.0, 0, 0.0))
        rob['root'].location.x = 5.6 + 0.07 * math.sin(t * 50) * sh
        rob['root'].location.y = -7.6 + 0.04 * math.cos(t * 43) * sh
        bag.location = (4.6, -6.6, 0.9)
        for i, s in enumerate(sweat):
            v = ((t * 1.6 + i / 6) % 1.0) if sh > 0.2 else 2.0
            s.location = (5.6 + (i - 2.5) * 0.35, -8.3, 5.4 - 3.2 * v) if v <= 1.0 else (0, 0, -99)
        cam(lerp((-1.5, -3.0, 3.0), (0.0, -3.4, 3.1), sm(t, 0, d)), (5.3, -7.0, 3.2), 30)
    return upd


def s8():
    rob, bag = bank_scene()
    dog = animal('bis', crown=True, sash=True)
    place(dog, 3.8, -6.1, 35, 0.12)
    place(rob, 5.8, -8.0, 235, 0.12)
    tg = wt('gave') - st(9)
    tbelly = wt('belly') - st(9)
    hearts = [T.box('ht', (0.3, 0.1, 0.3), (0, 0, -99), 'ff4b6e', None, 0.08, emit=1.5, rot=(0, 0.78, 0)) for _ in range(6)]

    def upd(t, d):
        kneel = sm(t, tg - 0.2, tg + 0.4)
        rob['leg_l'].rotation_euler[0] = -1.4 * kneel
        rob['leg_r'].rotation_euler[0] = 0.2 * kneel
        rob['torso'].rotation_euler[0] = 0.0
        give = sm(t, tg, tg + 0.9)
        T.pose(rob, arm_l=-1.5 * give, arm_r=-1.0 * give, head=(0.2, 0, 0), leg_l=rob['leg_l'].rotation_euler[0], leg_r=rob['leg_r'].rotation_euler[0])
        rub = sm(t, tbelly, tbelly + 0.3)
        if rub > 0:
            rob['arm_r'].rotation_euler[0] = -1.7 + 0.6 * math.sin(t * 12)
        rob['root'].location.z = 0.12 - 0.5 * kneel
        bx = 5.0 + (4.2 - 5.0) * give
        bag.location = (bx, -7.0 + 1.0 * give, 1.4 - 0.4 * give)
        roll = sm(t, tbelly - 0.1, tbelly + 0.5)
        a_sit(dog, 1.0 - roll)
        if roll > 0:
            a_back(dog, roll)
            dog['root'].location.z = 0.12 + 2.8 * roll
        a_wag(dog, t, 0.4, 10)
        for i, h in enumerate(hearts):
            v = ((t * 0.9 + i / 6) % 1.0) if rub > 0.5 else 2.0
            h.location = (3.8 + 0.8 * math.sin(i * 2 + t * 3), -6.1 - 0.2 * i, 3.6 + 3.5 * v) if v <= 1.0 else (0, 0, -99)
        cam(lerp((-4.5, -2.6, 3.4), (-3.2, -2.9, 3.4), sm(t, 0, d)), (4.8, -7.4, 2.6), 30)
    return upd


def s9():
    base('day')
    podium()
    dog = animal('bis', crown=True, sash=True)
    place(dog, 0, 6.8, 0, 1.4)
    cits = [T.character(f'c{i}', face='happy', **CITIZENS[i]) for i in range(6)]
    spots = [(-6, 0.6), (-2, -1.4), (3, 0.8), (8.5, 2.4), (-9.5, 3.5), (5, 3.3)]
    cf = confetti(90, 31)
    tz = wt('zero') - st(10)
    td = wt('doubled') - st(10)
    t1 = text('CRIME: 0', (-4.5, 1.0, 9.0), 1.8, '7be36a', 3.0)
    t2 = text('HAPPINESS x2', (4.0, 1.0, 5.8), 1.6, 'ffd23f', 3.0)
    for o in (t1, t2):
        o.scale = (0.001,) * 3

    def upd(t, d):
        a_wag(dog, t, 0.9, 16)
        for i, c in enumerate(cits):
            x, y = spots[i]
            place(c, x, y, 160 + 30 * i, 0.12)
            T.pose(c, arm_l=-2.7, arm_r=-2.7, head=(0, 0, 0.2 * math.sin(t * 4 + i)))
            c['root'].location.z = 0.12 + abs(math.sin(t * 7 + i * 1.3)) * 1.0
        conf_upd(cf, t, -1, 0, 2, 10, 3.5)
        for o, t0 in ((t1, tz), (t2, td)):
            s = sm(t, t0, t0 + 0.3)
            o.scale = (max(s, 0.001),) * 3
            face_cam(o)
        cam(lerp((17, -3.6, 8.5), (12, -3.4, 5.5), sm(t, 0, d)), (0, 2.0, 3.6), 28)
    return upd


def s10():
    base('day')
    podium()
    dog = animal('bis', crown=True, sash=True)
    place(dog, 0, 6.8, 0, 1.4)
    cat = animal('cat', col='7d8794', light='e6e9ee', ear='7d8794', cat=True)
    sign = T.box('sign', (2.8, 0.15, 1.5), (0, 0, -99), 'ffffff', None, 0.05)
    sgt = text('VOTE CAT', (0, 0, -99), 0.5, '14161c', 0.0)
    tc = wt('cat') - st(11)
    cf = confetti(50, 41)

    def upd(t, d):
        a_wag(dog, t, 0.8, 14)
        walkin = sm(t, tc - 0.6, tc + 1.7)
        x = 15 - 11.0 * walkin
        place(cat, x, 3.6, 90, 0.12)
        if 0 < walkin < 0.99:
            a_walk(cat, t * 12)
        else:
            for n in ('fl', 'fr', 'bl', 'br'):
                cat[n].rotation_euler[0] = 0
        cat['tail'].rotation_euler[1] = 0.3 * math.sin(t * 4)
        sign.location = (x + 0.2, 2.4, 4.6) if walkin > 0 else (0, 0, -99)
        sgt.location = (x + 0.2, 2.25, 4.55) if walkin > 0 else (0, 0, -99)
        sign.rotation_euler = (0, 0, 0)
        sgt.rotation_euler = (math.pi / 2, 0, 0)
        gl = sm(t, tc + 0.9, tc + 1.6)
        dog['head'].rotation_euler[2] = 0.0
        dog['head'].rotation_euler[0] = 0.0
        dog['brow_l'].rotation_euler[1] = 0.4 * gl
        dog['brow_r'].rotation_euler[1] = -0.4 * gl
        conf_upd(cf, t, -1, 0, 6, 8, 3.5) if t < tc - 0.5 else None
        cam(lerp((5.8, -2.0, 4.0), (6.4, -1.0, 3.9), sm(t, 0, d)), (3.2, 5.6, 3.5), 28)
    return upd


SHOTS = [(s1, st(0), st(2)), (s2, st(2), st(3)), (s3, st(3), st(4)), (s4, st(4), st(6)), (s5, st(6), st(7)), (s6, st(7), st(8)),
         (s7, st(8), st(9)), (s8, st(9), st(10)), (s9, st(10), st(11)), (s10, st(11), DUR)]


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
