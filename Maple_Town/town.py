"""Maple Town: a bright, blocky toy town and blocky characters, built entirely in code (Blender 4.2, Cycles).
Original designs in a block-figure style; no game assets or logos.

  $BLENDER -b -P town.py -- --stills      # look-dev stills -> build/look_*.png
"""
import math
import random
import sys

import bpy
from mathutils import Vector

R = random.Random(7)


def hexc(h):
    h = h.lstrip('#')
    return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)) + (1.0,)


_MATS = {}


def mat(col, rough=0.55, emit=0.0):
    key = (col, rough, emit)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(f'm_{col}_{emit}')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hexc(col)
    b.inputs['Roughness'].default_value = rough
    if emit:
        b.inputs['Emission Color'].default_value = hexc(col)
        b.inputs['Emission Strength'].default_value = emit
    _MATS[key] = m
    return m


def box(name, size, loc, col, parent=None, bevel=0.04, rough=0.55, emit=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = o.modifiers.new('bv', 'BEVEL')
        md.width = bevel
        md.segments = 3
    o.data.materials.append(mat(col, rough, emit))
    for p in o.data.polygons:
        p.use_smooth = True
    if parent:
        o.parent = parent
    return o


def cyl(name, r, h, loc, col, parent=None, verts=24, emit=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat(col, 0.5, emit))
    bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.location = loc
    if parent:
        e.parent = parent
    return e


# ---------------------------------------------------------------------------------------------- characters
def cone(name, r, h, loc, col, parent, rot=(0, 0, 0), verts=5):
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0.0, depth=h, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat(col, 0.6))
    o.parent = parent
    return o


def oval(name, rx, rz, loc, col, parent, emit=0.0):
    o = cyl(name, 1.0, 0.03, loc, col, parent, 28, emit=emit, rot=(math.pi / 2, 0, 0))
    o.scale = (rx, rz, 1.0)       # local x = width, local y -> world z after the rotation
    return o


_FMAT = {}


def face_plate(name, parent, expr, eyes, r=0.672, z0=0.06, z1=1.22, half=1.12):
    """The painted face: a strip wrapped round the front of the head, textured with assets/faces/<expr>_<eyes>.png."""
    import os
    import bmesh
    key = (expr, eyes)
    if key not in _FMAT:
        m = bpy.data.materials.new(f'face_{expr}_{eyes}')
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes['Principled BSDF']
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'faces', f'{expr}_{eyes}.png'))
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        bsdf.inputs['Roughness'].default_value = 0.6
        m.blend_method = 'BLEND'
        _FMAT[key] = m
    me = bpy.data.meshes.new(name + '_face')
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    n = 18
    rows = []
    for k in range(n + 1):
        a = -half + 2 * half * k / n
        x, y = math.sin(a) * r, -math.cos(a) * r
        rows.append((bm.verts.new((x, y, z0)), bm.verts.new((x, y, z1)), k / n))
    for (a0, a1, u0), (b0, b1, u1) in zip(rows, rows[1:]):
        f = bm.faces.new((a0, b0, b1, a1))
        for lp, (u, v) in zip(f.loops, ((u0, 0), (u1, 0), (u1, 1), (u0, 1))):
            lp[uv].uv = (u, v)
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name + '_face', me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(_FMAT[key])
    o.parent = parent
    o.visible_shadow = False
    return o


def shade(col, k):
    h = col.lstrip('#')
    return ''.join(f'{max(0, min(255, int(int(h[i:i + 2], 16) * k))):02x}' for i in (0, 2, 4))


def character(name, loc=(0, 0, 0), rot=0.0, skin='f2c39b', shirt='4b8fe2', pants='2c3350', shoes=None, hair=None,
              hair_style='swoop', hood=None, mask=False, hat=None, face='smile', scale=1.0, sleeves='long', logo=None,
              stripe=None, acc=(), eyes='brown'):
    """A classic block avatar: torso 2 x 2 x 1, arms and legs 1 x 2 x 1, a small rounded head, a flat cartoon face.
    Customisable: skin, shirt (sleeves long/short, chest logo, stripe), pants, shoes, hair colour and style
    (swoop, spiky, flat, long, buns, buzz), face (smile, smirk, calm, happy, scared, angry), hood, mask, hat (cap,
    beanie, crown) and accessories (antlers, horns, headphones, glasses, scarf, backpack).
    Returns the pivots for animation: root, torso, head, arm_l, arm_r, leg_l, leg_r."""
    shoes = shoes or pants
    root = empty(name, loc)
    root.rotation_euler[2] = rot
    root.scale = (scale,) * 3
    P = {'root': root}
    B = 0.035
    P['torso'] = empty(name + '_torso', (0, 0, 2.0), root)
    box(name + '_body', (2.0, 1.0, 2.0), (0, 0, 1.0), shirt, P['torso'], B)
    # clothing detail: collar, hem and belt, cuffs and soles
    box(name + '_collar', (1.0, 1.02, 0.16), (0, 0, 1.94), shade(shirt, 0.72), P['torso'], 0.03)
    box(name + '_hem', (2.02, 1.02, 0.14), (0, 0, 0.07), shade(shirt, 0.78), P['torso'], 0.0)
    if not hood:
        box(name + '_belt', (2.03, 1.03, 0.16), (0, 0, -0.02), '2a2622', P['torso'], 0.0)
        box(name + '_buckle', (0.26, 0.04, 0.16), (0, -0.52, -0.02), '8a8f98', P['torso'], 0.02, rough=0.4)
    if stripe:
        box(name + '_stripe', (2.02, 1.02, 0.34), (0, 0, 1.15), stripe, P['torso'], 0.0)
    if logo:
        box(name + '_logo', (0.7, 0.04, 0.5), (0, -0.5, 1.35), logo, P['torso'], 0.02)
    for side, x in (('l', -1.5), ('r', 1.5)):
        P['arm_' + side] = empty(f'{name}_arm_{side}', (x, 0, 1.9), P['torso'])
        if sleeves == 'short':
            box(f'{name}_slv{side}', (1.0, 1.0, 0.85), (0, 0, -0.325), shirt, P['arm_' + side], B)
            box(f'{name}_arm{side}', (0.98, 0.98, 1.2), (0, 0, -1.3), skin, P['arm_' + side], B)
        else:
            box(f'{name}_slv{side}', (1.0, 1.0, 1.62), (0, 0, -0.71), shirt, P['arm_' + side], B)
            box(f'{name}_cuff{side}', (1.03, 1.03, 0.16), (0, 0, -1.46), shade(shirt, 0.75), P['arm_' + side], 0.02)
            box(f'{name}_hand{side}', (0.98, 0.98, 0.4), (0, 0, -1.7), skin, P['arm_' + side], B)
    for side, x in (('l', -0.5), ('r', 0.5)):
        P['leg_' + side] = empty(f'{name}_leg_{side}', (x, 0, 2.0), root)
        box(f'{name}_leg{side}', (0.98, 1.0, 1.55), (0, 0, -0.775), pants, P['leg_' + side], B)
        box(f'{name}_shoe{side}', (1.0, 1.12, 0.42), (0, -0.05, -1.72), shoes, P['leg_' + side], 0.08)
        box(f'{name}_sole{side}', (1.02, 1.16, 0.12), (0, -0.05, -1.94), 'f4f4f4', P['leg_' + side], 0.03)

    P['head'] = empty(name + '_head', (0, 0, 4.0), root)
    hd = cyl(name + '_skull', 0.66, 1.22, (0, 0, 0.64), skin, P['head'], 40)
    md = hd.modifiers.new('bv', 'BEVEL')
    md.width = 0.2
    md.segments = 6
    md.limit_method = 'ANGLE'
    fy, ey = -0.665, 0.74
    dark = '17181d'
    if mask:
        box(name + '_mask', (1.36, 1.36, 0.5), (0, 0, 0.76), dark, P['head'], 0.12)
    if mask:
        for x in (-0.25, 0.25):
            oval(name + '_eyew', 0.17, 0.17, (x, fy - 0.04, ey + 0.02), 'ffffff', P['head'])
            oval(name + '_eye', 0.085, 0.11, (x, fy - 0.05, ey), dark, P['head'])
            box(name + '_brow', (0.3, 0.03, 0.07), (x, fy - 0.05, ey + 0.2), 'ffffff', P['head'], 0.0, rot=(0, (0.45 if x < 0 else -0.45), 0))
    else:
        face_plate(name, P['head'], face, eyes)
    P['head'].scale = (1.06, 1.06, 1.06)
    # ---- hair
    if hair and not hood and hat != 'beanie':
        if hair_style == 'spiky':
            box(name + '_hbase', (1.36, 1.36, 0.4), (0, 0.03, 1.2), hair, P['head'], 0.14)
            box(name + '_hback', (1.36, 0.5, 0.8), (0, 0.48, 0.8), hair, P['head'], 0.12)
            for k in range(14):
                a = k / 14 * 2 * math.pi
                rr = 0.42 if k % 2 else 0.2
                cone(name + '_spk', 0.26, 0.85 + 0.25 * (k % 3), (math.cos(a) * rr, math.sin(a) * rr + 0.05, 1.55), hair, P['head'],
                     rot=(-math.sin(a) * 0.7 - 0.25, math.cos(a) * 0.7, 0))
            for k in range(4):
                cone(name + '_fr', 0.2, 0.6, (-0.42 + k * 0.28, -0.62, 1.12), hair, P['head'], rot=(math.pi * 0.86, 0, 0.3 - k * 0.2))
        elif hair_style == 'long':
            box(name + '_htop', (1.42, 1.42, 0.42), (0, 0.02, 1.2), hair, P['head'], 0.16)
            box(name + '_hback', (1.42, 0.5, 1.9), (0, 0.5, 0.3), hair, P['head'], 0.16)
            for x in (-0.68, 0.68):
                box(name + '_hside', (0.24, 0.9, 1.5), (x, 0.1, 0.5), hair, P['head'], 0.1)
            box(name + '_fringe', (1.3, 0.2, 0.3), (0, -0.66, 1.12), hair, P['head'], 0.08)
        elif hair_style == 'buns':
            box(name + '_htop', (1.4, 1.4, 0.4), (0, 0.02, 1.2), hair, P['head'], 0.16)
            box(name + '_hback', (1.4, 0.45, 0.9), (0, 0.5, 0.75), hair, P['head'], 0.14)
            for x in (-0.6, 0.6):
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.36, location=(x, 0.1, 1.6))
                o = bpy.context.object
                o.data.materials.append(mat(hair, 0.6))
                bpy.ops.object.shade_smooth()
                o.parent = P['head']
        elif hair_style == 'buzz':
            box(name + '_htop', (1.34, 1.34, 0.22), (0, 0.0, 1.2), hair, P['head'], 0.1)
        elif hair_style == 'flat':
            box(name + '_htop', (1.42, 1.42, 0.4), (0, 0.0, 1.2), hair, P['head'], 0.12)
            box(name + '_hback', (1.42, 0.45, 0.8), (0, 0.5, 0.8), hair, P['head'], 0.12)
            box(name + '_fringe', (1.36, 0.22, 0.36), (0, -0.64, 1.1), hair, P['head'], 0.08)
        else:                                          # swoop: a side-swept fringe
            box(name + '_htop', (1.42, 1.42, 0.44), (0, 0.02, 1.2), hair, P['head'], 0.16)
            box(name + '_hback', (1.42, 0.46, 0.9), (0, 0.5, 0.76), hair, P['head'], 0.14)
            box(name + '_swoop', (1.2, 0.3, 0.5), (0.16, -0.62, 1.12), hair, P['head'], 0.12, rot=(0, 0.32, 0))
            box(name + '_tuft', (0.5, 0.5, 0.4), (-0.36, -0.3, 1.46), hair, P['head'], 0.14, rot=(0, -0.3, 0.3))
    if hood:
        box(name + '_hood_t', (1.52, 1.5, 0.36), (0, 0.06, 1.24), hood, P['head'], 0.16)
        box(name + '_hood_b', (1.52, 0.36, 1.36), (0, 0.6, 0.7), hood, P['head'], 0.16)
        for x in (-0.68, 0.68):
            box(name + '_hood_s', (0.2, 1.3, 1.36), (x, 0.1, 0.7), hood, P['head'], 0.08)
        box(name + '_pocket', (1.2, 0.05, 0.55), (0, -0.5, 0.55), hood, P['torso'], 0.04, rough=0.9)
        for x in (-0.2, 0.2):
            box(name + '_cord', (0.06, 0.05, 0.6), (x, -0.52, 1.65), 'ffffff', P['torso'], 0.0)
    if hat == 'cap':
        box(name + '_cap', (1.4, 1.4, 0.36), (0, 0, 1.26), '27408a', P['head'], 0.12)
        box(name + '_peak', (1.3, 0.62, 0.09), (0, -0.86, 1.13), '27408a', P['head'], 0.04)
    elif hat == 'beanie' or mask:
        box(name + '_beanie', (1.42, 1.42, 0.5), (0, 0, 1.2), dark if mask else 'e2574b', P['head'], 0.2)
        box(name + '_brim', (1.48, 1.48, 0.2), (0, 0, 1.0), dark if mask else 'ffffff', P['head'], 0.08)
    elif hat == 'crown':
        box(name + '_crown', (1.2, 1.2, 0.3), (0, 0, 1.5), 'ffcc33', P['head'], 0.04, rough=0.25)
        for k in range(8):
            a = k / 8 * 2 * math.pi
            cone(name + '_cp', 0.16, 0.4, (math.cos(a) * 0.5, math.sin(a) * 0.5, 1.82), 'ffcc33', P['head'], verts=4)
    for a_ in acc:
        if a_ in ('antlers', 'horns'):
            for sx in (-1, 1):
                if a_ == 'horns':
                    cone(name + '_horn', 0.16, 0.7, (sx * 0.45, 0, 1.75), 'd6332e', P['head'], rot=(0, sx * 0.5, 0), verts=12)
                else:
                    for (dx, dz, ln, an) in ((0.5, 1.8, 0.9, 0.5), (0.72, 2.25, 0.6, 1.0), (0.52, 2.3, 0.6, -0.1), (0.9, 2.0, 0.45, 1.3)):
                        box(name + '_ant', (0.08, 0.08, ln), (sx * dx, 0.05, dz), '1c1a18', P['head'], 0.02, rot=(0, sx * an, 0))
        elif a_ == 'headphones':
            box(name + '_hpb', (1.5, 0.16, 0.14), (0, 0.05, 1.44), '2a2d36', P['head'], 0.05)
            for x in (-0.72, 0.72):
                box(name + '_hpc', (0.2, 0.5, 0.6), (x, 0.05, 0.75), 'ff4b6e', P['head'], 0.08)
        elif a_ == 'glasses':
            for x in (-0.25, 0.25):
                box(name + '_gl', (0.4, 0.04, 0.3), (x, fy - 0.04, ey), '1a1c22', P['head'], 0.04)
                box(name + '_gll', (0.3, 0.045, 0.2), (x, fy - 0.045, ey), '7fd0ff', P['head'], 0.02, rough=0.1)
            box(name + '_glb', (0.14, 0.04, 0.05), (0, fy - 0.04, ey + 0.04), '1a1c22', P['head'], 0.0)
        elif a_ == 'scarf':
            box(name + '_scarf', (1.5, 1.2, 0.34), (0, 0, 2.02), 'e2574b', P['torso'], 0.12)
            box(name + '_scarf2', (0.4, 0.14, 0.9), (0.4, -0.56, 1.5), 'e2574b', P['torso'], 0.05)
        elif a_ == 'backpack':
            box(name + '_pack', (1.5, 0.6, 1.5), (0, 0.8, 1.05), 'f0b63a', P['torso'], 0.14)
    return P


def pose(P, arm_l=0.0, arm_r=0.0, leg_l=0.0, leg_r=0.0, head=(0, 0, 0), lean=0.0):
    P['arm_l'].rotation_euler[0], P['arm_r'].rotation_euler[0] = arm_l, arm_r
    P['leg_l'].rotation_euler[0], P['leg_r'].rotation_euler[0] = leg_l, leg_r
    P['head'].rotation_euler = head
    P['torso'].rotation_euler[0] = lean


# ---------------------------------------------------------------------------------------------- the town
PASTEL = ['ff9fb0', 'ffc46b', '8fe0a8', '8fc4ff', 'd3a4f5', 'ffe680', 'ffab7a']
ROOFS = ['c95b4a', '4f7fb8', '6a9a5b', '8a5fa8', 'd08a3c']


def building(x, y, w, d, h, col, roof, face=-1, sign=None, lit=0.0):
    """A shop or house facing the street (face -1: front towards -y)."""
    g = empty('bld', (x, y, 0))
    box('wall', (w, d, h), (0, 0, h / 2), col, g, 0.12)
    box('roof', (w + 0.8, d + 0.8, 0.7), (0, 0, h + 0.35), roof, g, 0.18)
    fy = face * (d / 2 + 0.02)
    box('door', (1.5, 0.12, 2.6), (0, fy, 1.3), '6b4630', g, 0.05)
    n = max(1, int(w // 3.2))
    for fl in range(max(1, int((h - 3.4) // 3)) + 1):
        for i in range(n):
            wx = (i - (n - 1) / 2) * (w / n)
            z = 4.6 + fl * 3.0 if fl else 2.1
            if z > h - 1.0 or (fl == 0 and abs(wx) < 1.6):
                continue
            box('winf', (1.7, 0.1, 1.7), (wx, fy, z), 'ffffff', g, 0.03)
            box('win', (1.4, 0.14, 1.4), (wx, fy, z), 'ffe9a8' if lit else '9fd0f5', g, 0.02, rough=0.2, emit=lit * (1.0 if R.random() < 0.7 else 0.0))
    box('awning', (w * 0.8, 1.3, 0.22), (0, fy + face * 0.6, 3.3), R.choice(ROOFS), g, 0.06, rot=(face * -0.25, 0, 0))
    if sign:
        box('sign', (w * 0.7, 0.16, 1.1), (0, fy, h - 0.9), sign, g, 0.05)
    return g


def tree(x, y, s=1.0):
    g = empty('tree', (x, y, 0))
    cyl('trunk', 0.35 * s, 2.2 * s, (0, 0, 1.1 * s), '7a5134', g, 12)
    for dx, dy, dz, r in ((0, 0, 3.2, 1.9), (0.9, 0.3, 2.6, 1.3), (-0.8, -0.4, 2.7, 1.4), (0.1, 0.6, 4.2, 1.2)):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r * s, location=(dx * s, dy * s, dz * s))
        o = bpy.context.object
        o.data.materials.append(mat(R.choice(['6fbf5a', '7fcf63', '5fae52']), 0.8))
        bpy.ops.object.shade_smooth()
        o.parent = g
    return g


def lamp(x, y, night):
    g = empty('lamp', (x, y, 0))
    cyl('pole', 0.12, 5.0, (0, 0, 2.5), '2f3440', g, 10)
    box('head', (0.9, 0.9, 0.5), (0, 0, 5.2), 'fff2c4', g, 0.1, emit=5.0 if night else 0.0)
    if night:
        l = bpy.data.lights.new('lamp_l', 'POINT')
        l.energy = 700
        l.color = (1.0, 0.82, 0.55)
        l.shadow_soft_size = 0.6
        o = bpy.data.objects.new('lamp_l', l)
        bpy.context.collection.objects.link(o)
        o.location = (0, 0, 4.7)
        o.parent = g
    return g


def build_town(night=False):
    box('grass', (500, 500, 1), (0, 0, -0.5), '6fd15a', None, 0, rough=0.9)
    box('road', (200, 9, 0.12), (0, 0, 0.06), '4b5160', None, 0, rough=0.8)
    box('road2', (9, 200, 0.12), (30, 0, 0.065), '4b5160', None, 0, rough=0.8)
    for i in range(-24, 25):
        if abs(i * 4 - 30) > 5:
            box('dash', (1.8, 0.3, 0.02), (i * 4, 0, 0.14), 'f4f1e4', None, 0)
    for s in (-1, 1):
        box('walk', (200, 4, 0.3), (0, s * 6.5, 0.15), 'd8d4c8', None, 0.05, rough=0.9)
    lit = 1.6 if night else 0.0
    x = -52
    for i in range(9):                       # the north side of Oak Street
        w = R.choice([7, 8, 9, 10])
        h = R.choice([6.5, 8, 9.5, 11])
        if abs(x + w / 2 - 30) > 9:
            building(x + w / 2, 13.5, w, 8, h, PASTEL[i % len(PASTEL)], R.choice(ROOFS), -1, lit=lit)
        x += w + 1.2
    x = -52
    for i in range(9):                       # the south side: includes the bank and the empty house
        w = R.choice([7, 8, 9, 10])
        h = R.choice([6.5, 8, 9.5])
        cx = x + w / 2
        if abs(cx - 30) > 9 and not (-4 < cx < 14) and not (-30 < cx < -17):
            building(cx, -13.5, w, 8, h, PASTEL[(i + 3) % len(PASTEL)], R.choice(ROOFS), 1, lit=lit)
        x += w + 1.2
    # the bank
    b = empty('bank', (5, -15, 0))
    box('bank_wall', (16, 10, 10), (0, 0, 5), 'f1ead8', b, 0.15)
    box('bank_roof', (17.5, 11.5, 1.2), (0, 0, 10.6), '9aa3ad', b, 0.2)
    for i in range(5):
        cyl('col', 0.6, 8.6, ((i - 2) * 3.2, 5.6, 4.3), 'ffffff', b, 20)
    box('bank_step', (17, 3, 0.6), (0, 6.2, 0.3), 'd9d2c2', b, 0.08)
    box('bank_sign', (9, 0.3, 1.6), (0, 5.3, 9.0), '2f6fd1', b, 0.06, emit=3.0 if night else 0.0)
    box('bank_door', (3, 0.2, 4.2), (0, 5.05, 2.1), '3a2a1e', b, 0.05)
    if night:
        box('alarm', (0.8, 0.8, 0.8), (6.4, 5.4, 8.2), 'ff2a2a', b, 0.2, emit=25.0)
        l = bpy.data.lights.new('alarm_l', 'POINT')
        l.energy = 5000
        l.color = (1.0, 0.1, 0.08)
        l.shadow_soft_size = 1.0
        o = bpy.data.objects.new('alarm_l', l)
        bpy.context.collection.objects.link(o)
        o.location = (11.4, -8.4, 8.6)
    # the empty house on Oak Street: grey, boarded, one lit window
    h_ = empty('house', (-23.5, -14, 0))
    box('h_wall', (10, 8, 7), (0, 0, 3.5), '8e939c', h_, 0.12)
    box('h_roof', (11.4, 9.4, 1.0), (0, 0, 7.5), '4a4f5a', h_, 0.2)
    box('h_roof2', (8, 6.4, 1.0), (0, 0, 8.4), '4a4f5a', h_, 0.2)
    box('h_door', (1.6, 0.14, 2.8), (0, 4.05, 1.4), '3d2c20', h_, 0.05)
    box('h_win', (1.8, 0.16, 1.8), (2.9, 4.05, 4.4), 'ffd27a', h_, 0.03, emit=4.0 if night else 1.5)
    box('h_winb', (1.8, 0.16, 1.8), (-2.9, 4.05, 4.4), '3b4350', h_, 0.03)
    for k in range(2):
        box('board', (2.3, 0.1, 0.3), (-2.9, 4.16, 4.1 + k * 0.6), '7a5a3c', h_, 0.02, rot=(0, 0.25 - k * 0.5, 0))
    # clock tower at the end of the street
    t = empty('tower', (-58, 0, 0))
    box('tw', (9, 9, 20), (0, 0, 10), 'f4efe2', t, 0.2)
    box('tw_top', (10.4, 10.4, 1.4), (0, 0, 20.7), 'c95b4a', t, 0.25)
    box('tw_sp', (5, 5, 5), (0, 0, 23.5), 'c95b4a', t, 0.4)
    cyl('clock', 2.6, 0.3, (4.6, 0, 15.5), 'ffffff', t, 32, rot=(0, math.pi / 2, 0), emit=2.0 if night else 0.0)
    box('hand1', (0.1, 0.25, 2.0), (4.8, 0, 16.3), '20242c', t, 0)
    box('hand2', (0.1, 1.4, 0.22), (4.8, 0.6, 15.5), '20242c', t, 0)
    for x_ in range(-48, 50, 12):
        for s in (-1, 1):
            if abs(x_ - 30) > 7:
                lamp(x_ + 3, s * 5.2, night)
                tree(x_ - 3, s * 7.6, 0.8 + 0.3 * R.random())
    for _ in range(26):
        a = R.uniform(0, 2 * math.pi)
        r = R.uniform(40, 95)
        if abs(r * math.sin(a)) > 22:
            tree(r * math.cos(a), r * math.sin(a), R.uniform(1.0, 1.8))


def world(night=False, sunset=False):
    w = bpy.data.worlds.new('w')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_elevation = math.radians(-6 if night else (9 if sunset else 48))
    sky.sun_rotation = math.radians(250)
    sky.air_density = 1.4
    sky.dust_density = 3.0 if sunset else 1.0
    nt.links.new(sky.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 0.11 if sunset else 0.2
    if night:
        nt.links.remove(bg.inputs[0].links[0])
        bg.inputs[0].default_value = (0.012, 0.022, 0.07, 1.0)
        bg.inputs[1].default_value = 1.0
    sun = bpy.data.lights.new('sun', 'SUN')
    sun.energy = 0.5 if night else (2.4 if sunset else 3.2)
    sun.color = (0.55, 0.65, 1.0) if night else ((1.0, 0.62, 0.38) if sunset else (1.0, 0.96, 0.88))
    sun.angle = math.radians(6)
    o = bpy.data.objects.new('sun', sun)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = (math.radians(58 if night else (78 if sunset else 42)), 0, math.radians(-110))


def clouds():
    for i in range(26):
        a = R.uniform(0, 2 * math.pi)
        r = R.uniform(60, 220)
        g = empty('cloud', (r * math.cos(a), r * math.sin(a), R.uniform(38, 70)))
        for k in range(R.randint(3, 5)):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=R.uniform(5, 9), location=(k * 6.5 - 10, R.uniform(-2, 2), R.uniform(-1, 1.5)))
            o = bpy.context.object
            o.scale = (1.25, 1.0, 0.55)
            o.data.materials.append(mat('ffffff', 1.0, 0.35))
            bpy.ops.object.shade_smooth()
            o.parent = g
        g.rotation_euler[2] = R.uniform(0, 3.1)


def camera(loc, look, lens=35):
    cam = bpy.data.cameras.new('cam')
    cam.lens = lens
    o = bpy.data.objects.new('cam', cam)
    bpy.context.collection.objects.link(o)
    o.location = loc
    d = Vector(look) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = o
    return o


def setup(samples=24, scale=50):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 4
    s.render.resolution_x, s.render.resolution_y = 1080, 1920
    s.render.resolution_percentage = scale
    s.render.fps = 30
    s.view_settings.view_transform = 'Standard'
    s.view_settings.look = 'Medium High Contrast'
    s.view_settings.exposure = -1.15
    s.render.threads_mode = 'AUTO'


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()
    _FMAT.clear()


def still(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def townsfolk():
    out = []
    for i, (x, y, sh, hr, rot) in enumerate(((6, 5.8, 'e2574b', '5a3a22', 200), (9.5, 6.6, 'f0b63a', '1d1a18', 215), (-15, 6.2, '57b56a', 'c9903c', 120),
                                              (-1, -6.4, 'b06fd6', '3a2a1e', 20), (16, -6.2, '3fb7c9', '7a4a22', 300), (-12, -6.0, 'ff7fb0', '1d1a18', 60))):
        c = character(f'p{i}', (x, y, 0.3), math.radians(rot), shirt=sh, hair=hr, face='scared')
        pose(c, arm_l=-2.4 if i % 2 else 0.3, arm_r=-2.4, leg_l=0.5, leg_r=-0.5, lean=-0.15)
        out.append(c)
    return out


def stills(out):
    global R

    def scene():
        global R
        reset(); R = random.Random(7); setup(); world(); build_town(); clouds()
        k = character('kid', (-4, -0.6, 0), math.radians(90), shirt='8b9099', pants='3a3f4a', hood='8b9099', shoes='e8e8ec', face='calm')
        pose(k, arm_l=0.5, arm_r=-0.5, leg_l=-0.5, leg_r=0.5, head=(0.1, 0, 0))
        return k, townsfolk()
    # 1: the town from above, in daylight: the kid alone in the street, everyone else keeping away
    scene()
    camera((26, -30, 34), (-6, 0, 2), 28)
    still(f'{out}/look_1_town.png')
    # 2: low angle on a scared townsperson, the town and sky behind
    scene()
    camera((7.6, 2.6, 1.6), (6.1, 5.6, 4.9), 24)
    still(f'{out}/look_2_face.png')
    # 3: the kid in the grey hoodie, walking towards us down the street
    scene()
    camera((4.5, -1.6, 3.0), (-4, -0.5, 4.2), 40)
    still(f'{out}/look_3_kid.png')


def sheet(out):
    """A line-up of six differently customised characters on a plain backdrop."""
    reset(); setup(48, 60)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    world()
    box('floor', (400, 400, 1), (0, 0, -0.5), '6f86ad', None, 0, rough=1.0)
    cast = [
        dict(shirt='8b9099', pants='3a3f4a', shoes='e8e8ec', hood='8b9099', face='calm'),
        dict(shirt='e9ebf0', pants='1c1e24', shoes='aeb4c0', hair='7fa8e8', hair_style='spiky', face='smirk', logo='20242c', acc=('antlers',)),
        dict(shirt='e2574b', pants='2c3350', shoes='ffffff', hair='5a3a22', hair_style='swoop', face='smile', sleeves='short', stripe='ffffff', acc=('headphones',)),
        dict(shirt='b06fd6', pants='f4f1e4', shoes='ff7fb0', hair='f0c05a', hair_style='long', face='happy', skin='f7d2b0', acc=('backpack',)),
        dict(shirt='27408a', pants='27408a', shoes='15171c', hair='1d1a18', hair_style='buzz', face='scared', skin='8d5a3c', hat='cap', logo='ffd23f'),
        dict(shirt='23262e', pants='15171c', shoes='15171c', mask=True, face='angry', skin='e0b08a'),
    ]
    for i, kw in enumerate(cast):
        c = character(f'c{i}', ((i - 2.5) * 4.5, 0, 0), 0.0, eyes=['grey', 'red', 'green', 'blue', 'brown', 'brown'][i], **kw)
        pose(c, arm_l=0.12, arm_r=-0.12, head=(0, 0, 0.12 if i % 2 else -0.12))
        c['root'].rotation_euler[2] = math.radians((i - 2.5) * -5)
    camera((0, -36, 4.4), (0, 0, 3.0), 44)
    still(f'{out}/sheet.png')


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if '--sheet' in argv:
        import os
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
        os.makedirs(out, exist_ok=True)
        sheet(out)
    if '--stills' in argv:
        import os
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
        os.makedirs(out, exist_ok=True)
        stills(out)
