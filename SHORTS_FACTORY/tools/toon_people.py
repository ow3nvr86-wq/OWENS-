"""Toon people: original stylized 3D characters for the cel-shaded one-shots (Blender, bpy).

A person is a small joint hierarchy of empties (root at the feet, hips, spine, chest, neck, head, shoulders, elbows,
hands, hip joints, knees, ankles) with smooth rounded parts parented to it: a tapered torso, capsule limbs, mitten
hands, boots and a big rounded head with oval eyes, pupils with a catch-light, brows, a button nose, ears and a hair
shell cut from a sphere (several styles). Proportions are about five heads tall for adults and four for children,
so they read as cartoon people rather than mannequins or stick figures. Clothing is flat colour per part, or a
spacesuit (soft white suit, orange joint rings, chest unit, backpack, an open-face helmet shell).

The rig is posed with angles in radians, forward-positive (an arm or leg swung forward toward the character's front).
A person faces -y in its own space; the root's yaw turns it. Animation is baked straight into f-curves (fast) from a
pose function of time, so walks, falls and physics-driven motion all come from Python functions.

Usage (inside a Blender script that has toon(name, hex) and flat(name, hex) material factories):
    import toon_people as TP; TP.setup(toon, flat)
    cooper = TP.Person('cooper', dict(skin='#e8b48f', hair='#5a3a22', style='short', top='#4f7fb8', legs='#3e4a5e'))
    TP.bake(cooper, f0, f1, fps, lambda t: dict(loc=(0, 0, 0), yaw=0.0, pose=TP.walk_pose(t * 1.8)))
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

_toon = _flat = None
_MAT = {}
def setup(toon, flat):
    global _toon, _flat; _toon, _flat = toon, flat
def M(hexc, flat=False):
    k = (hexc, flat)
    if k not in _MAT: _MAT[k] = (_flat if flat else _toon)(('f_' if flat else 't_') + hexc.lstrip('#'), hexc)
    return _MAT[k]

# ------------------------------------------------------------------ mesh builders ------------------------------------
def _obj(name, bm, mat, parent, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); o.data.materials.append(mat); _coll.objects.link(o); o.parent = parent; return o
def ellipsoid(name, c, r, mat, parent, seg=24, rings=14, cut=None):
    """an ellipsoid at c with radii r in the parent's space; cut(n) -> True deletes the vertex (n = unit-sphere dir)"""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    if cut:
        kill = [v for v in bm.verts if cut(v.co.copy())]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
    for v in bm.verts: v.co = Vector((c[0] + v.co.x * r[0], c[1] + v.co.y * r[1], c[2] + v.co.z * r[2]))
    return _obj(name, bm, mat, parent)
def capsule(name, top, length, r0, r1, mat, parent, sx=1.0, sy=1.0, seg=16):
    """a tapered capsule hanging DOWN from `top` (radius r0 at the top, r1 at the bottom), cross-section scaled sx, sy"""
    bm = bmesh.new(); rings = []
    prof = []                                                         # (z, radius) from the top cap to the bottom cap
    for k in range(5):                                                # top hemisphere
        a = math.pi / 2 * (1 - k / 4); prof.append((r0 * math.sin(a), r0 * math.cos(a)))
    for k in range(1, 6):                                             # the shaft
        u = k / 6; prof.append((-length * u, r0 + (r1 - r0) * u))
    for k in range(5):                                                # bottom hemisphere
        a = math.pi / 2 * k / 4; prof.append((-length - r1 * math.sin(a), r1 * math.cos(a)))
    top_v = bm.verts.new((top[0], top[1], top[2] + r0)); bot_v = bm.verts.new((top[0], top[1], top[2] - length - r1))
    for z, rr in prof[1:-1]:
        ring = [bm.verts.new((top[0] + math.cos(2 * math.pi * i / seg) * rr * sx, top[1] + math.sin(2 * math.pi * i / seg) * rr * sy, top[2] + z)) for i in range(seg)]
        rings.append(ring)
    for i in range(seg):
        j = (i + 1) % seg; bm.faces.new((top_v, rings[0][j], rings[0][i])); bm.faces.new((bot_v, rings[-1][i], rings[-1][j]))
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg; bm.faces.new((a[i], a[j], b[j], b[i]))
    return _obj(name, bm, mat, parent)
def boxm(name, c, size, mat, parent, bevel=0.3):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((c[0] + v.co.x * size[0], c[1] + v.co.y * size[1], c[2] + v.co.z * size[2]))
    if bevel: bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(size) * bevel, segments=2, affect='EDGES')
    return _obj(name, bm, mat, parent, smooth=False)
def torus(name, c, R, r, mat, parent, rot=(0, 0, 0), seg=24):
    bm = bmesh.new()
    rings = [[bm.verts.new(((R + r * math.cos(2 * math.pi * j / 8)) * math.cos(2 * math.pi * i / seg), (R + r * math.cos(2 * math.pi * j / 8)) * math.sin(2 * math.pi * i / seg), r * math.sin(2 * math.pi * j / 8))) for j in range(8)] for i in range(seg)]
    for i in range(seg):
        for j in range(8): bm.faces.new((rings[i][j], rings[(i + 1) % seg][j], rings[(i + 1) % seg][(j + 1) % 8], rings[i][(j + 1) % 8]))
    R_ = Matrix.Translation(c) @ Matrix.Rotation(rot[2], 4, 'Z') @ Matrix.Rotation(rot[1], 4, 'Y') @ Matrix.Rotation(rot[0], 4, 'X')
    bmesh.ops.transform(bm, matrix=R_, verts=bm.verts)
    return _obj(name, bm, mat, parent)
def joint(name, loc, parent):
    e = bpy.data.objects.new(name, None); e.empty_display_size = 0.05; _coll.objects.link(e); e.parent = parent; e.location = loc
    e.rotation_mode = 'XYZ'; return e

_coll = None
# ------------------------------------------------------------------ the person -------------------------------------
HAIR_CUTS = {                                     # n: unit-sphere direction (front = -y). True = no hair there
    'short': lambda n: (n.y < -0.18 and n.z < 0.5) or n.z < -0.22 or (abs(n.x) > 0.55 and n.z < 0.15 and n.y < 0.2),
    'bob':   lambda n: (n.y < -0.22 and n.z < 0.36) or n.z < -0.62,
    'long':  lambda n: (n.y < -0.22 and n.z < 0.36) or (n.z < -0.75),
    'bun':   lambda n: (n.y < -0.18 and n.z < 0.42) or n.z < -0.25,
    'fringe': lambda n: n.z > 0.32 or n.y < -0.1 or n.z < -0.32,        # bald on top: a ring of hair round the back
    'buzz':  lambda n: (n.y < -0.12 and n.z < 0.5) or n.z < -0.1,
}
class Person:
    def __init__(self, name, spec, coll):
        global _coll; _coll = coll; self.name = name; s = self.spec = dict(spec)
        kid = s.get('kid', False); H = s.get('height', 1.30 if kid else 1.80); self.H = H
        hs = (1.18 if kid else 1.0) * s.get('head', 1.0)           # head scale
        k = H / 1.80; self.k = k
        skin, hairc = M(s['skin']), M(s.get('hair', '#3a2a1e'))
        suit = s.get('suit', False)
        top = M(s.get('top', '#4f7fb8')); legs = M(s.get('legs', '#3e4a5e')); boots = M(s.get('boots', '#4a3424'))
        if suit: top = legs = M('#eeeae2'); boots = M('#9aa0aa'); ring = M('#ff8a3a'); glove = M('#b8bec8')
        hand_m = glove if suit else skin
        # joints (adult numbers scaled by k; kids get shorter legs, bigger heads)
        legk = 0.86 if kid else 1.0
        self.root = joint(name, (0, 0, 0), None)
        hipz = 0.92 * k * legk
        self.hips = joint(name + '.hips', (0, 0, hipz), self.root)
        self.chest = joint(name + '.chest', (0, 0, 0.30 * k), self.hips)
        self.neck = joint(name + '.neck', (0, 0, 0.19 * k), self.chest)
        self.head = joint(name + '.head', (0, 0, 0.06 * k), self.neck)
        self.sh = [joint(name + '.sh' + sd, (sx * 0.21 * k, 0, 0.17 * k), self.chest) for sd, sx in (('L', 1), ('R', -1))]
        self.el = [joint(name + '.el' + sd, (0, 0, -0.29 * k), self.sh[i]) for i, sd in enumerate('LR')]
        self.ha = [joint(name + '.ha' + sd, (0, 0, -0.26 * k), self.el[i]) for i, sd in enumerate('LR')]
        self.hp = [joint(name + '.hp' + sd, (sx * 0.10 * k, 0, -0.02 * k), self.hips) for sd, sx in (('L', 1), ('R', -1))]
        self.kn = [joint(name + '.kn' + sd, (0, 0, -0.43 * k * legk), self.hp[i]) for i, sd in enumerate('LR')]
        self.an = [joint(name + '.an' + sd, (0, 0, -0.42 * k * legk), self.kn[i]) for i, sd in enumerate('LR')]
        # body
        bw = s.get('build', 1.0)
        capsule(name + '.pelvis', (0, 0, 0.05 * k), 0.10 * k, 0.15 * k * bw, 0.14 * k * bw, legs, self.hips, sy=0.75)
        capsule(name + '.torso', (0, 0, 0.36 * k), 0.30 * k, 0.17 * k * bw, 0.145 * k * bw, top, self.hips, sx=1.12, sy=0.72)
        capsule(name + '.neckm', (0, 0, 0.10 * k), 0.05 * k, 0.045 * k, 0.05 * k, skin if not suit else M('#d8d4cc'), self.neck)
        if s.get('dress'):
            capsule(name + '.skirt', (0, 0, 0.02 * k), 0.36 * k, 0.15 * k, 0.24 * k, M(s['dress']), self.hips, sy=0.8)
        for i, sx in enumerate((1, -1)):
            capsule(name + '.uarm' + 'LR'[i], (0, 0, 0), 0.24 * k, 0.058 * k * bw, 0.05 * k * bw, top, self.sh[i])
            capsule(name + '.farm' + 'LR'[i], (0, 0, 0), 0.23 * k, 0.05 * k * bw, 0.042 * k * bw, top if s.get('sleeves', True) or suit else skin, self.el[i])
            ellipsoid(name + '.hand' + 'LR'[i], (0, -0.01 * k, -0.05 * k), (0.05 * k, 0.034 * k, 0.068 * k), hand_m, self.ha[i], seg=14, rings=8)
            ellipsoid(name + '.thumb' + 'LR'[i], (-sx * 0.035 * k, -0.025 * k, -0.025 * k), (0.016 * k, 0.016 * k, 0.03 * k), hand_m, self.ha[i], seg=8, rings=6)
            capsule(name + '.thigh' + 'LR'[i], (0, 0, 0), 0.38 * k * legk, 0.085 * k * bw, 0.065 * k * bw, legs, self.hp[i])
            capsule(name + '.shin' + 'LR'[i], (0, 0, 0), 0.34 * k * legk, 0.065 * k * bw, 0.055 * k * bw, legs, self.kn[i])
            ellipsoid(name + '.boot' + 'LR'[i], (0, -0.05 * k, -0.035 * k), (0.07 * k, 0.13 * k, 0.06 * k), boots, self.an[i], seg=16, rings=8,
                      cut=lambda n: n.z < -0.55)
            if suit:
                torus(name + '.ringE' + 'LR'[i], (0, 0, 0), 0.052 * k, 0.014 * k, ring, self.el[i])
                torus(name + '.ringK' + 'LR'[i], (0, 0, 0), 0.07 * k, 0.016 * k, ring, self.kn[i])
                torus(name + '.ringW' + 'LR'[i], (0, 0, -0.01 * k), 0.044 * k, 0.012 * k, ring, self.ha[i])
        if suit:
            boxm(name + '.chestunit', (0, -0.11 * k, 0.22 * k), (0.15 * k, 0.05 * k, 0.1 * k), M('#7a8494'), self.hips)
            for j, c in enumerate(('#ff5a4a', '#ffd23a', '#4ad08a')):
                ellipsoid(name + '.btn%d' % j, ((j - 1) * 0.04 * k, -0.137 * k, 0.23 * k), (0.012 * k,) * 3, M(c, flat=True), self.hips, seg=8, rings=6)
            boxm(name + '.pack', (0, 0.14 * k, 0.32 * k), (0.3 * k, 0.12 * k, 0.36 * k), M('#d8d4cc'), self.hips)
            torus(name + '.collar', (0, 0, 0.02 * k), 0.1 * k, 0.025 * k, ring, self.neck)
            if s.get('patch'): boxm(name + '.patch', (0.1 * k, -0.105 * k, 0.33 * k), (0.06 * k, 0.012 * k, 0.04 * k), M(s['patch'], flat=True), self.hips, bevel=0)
        # head (in head-joint space; head centre above the joint)
        hc = Vector((0, 0, 0.14 * k * hs)); R = Vector((0.118, 0.118, 0.135)) * k * hs; self.hc, self.hR = hc, R
        ellipsoid(name + '.skull', hc, R, skin, self.head, seg=32, rings=18)
        ellipsoid(name + '.jaw', hc + Vector((0, -0.012, -0.065)) * k * hs, Vector((0.088, 0.09, 0.075)) * k * hs, skin, self.head, seg=24, rings=12)
        for i, sx in enumerate((1, -1)):
            ellipsoid(name + '.ear' + 'LR'[i], hc + Vector((sx * 0.117, 0.005, -0.01)) * k * hs, Vector((0.018, 0.028, 0.04)) * k * hs, skin, self.head, seg=12, rings=8)
            ec = hc + Vector((sx * 0.047, -0.1, 0.012)) * k * hs
            ellipsoid(name + '.eye' + 'LR'[i], ec, Vector((0.03, 0.02, 0.038)) * k * hs, M('#fbfaf6', flat=True), self.head, seg=16, rings=10)
            pc = ec + Vector((0, -0.016, -0.004)) * k * hs
            ellipsoid(name + '.pupil' + 'LR'[i], pc, Vector((0.016, 0.008, 0.02)) * k * hs, M(s.get('eyes', '#2a1c14'), flat=True), self.head, seg=12, rings=8)
            ellipsoid(name + '.glint' + 'LR'[i], pc + Vector((sx * -0.005, -0.007, 0.008)) * k * hs, Vector((0.005,) * 3) * k * hs, M('#ffffff', flat=True), self.head, seg=6, rings=4)
            bc = hc + Vector((sx * 0.05, -0.105, 0.062 + s.get('brow', 0.0))) * k * hs
            b_ = capsule(name + '.brow' + 'LR'[i], (0, 0, 0), 0.04 * k * hs, 0.009 * k * hs, 0.007 * k * hs, hairc, self.head)
            b_.location = bc + Vector((sx * 0.02, 0, 0)) * k * hs; b_.rotation_euler = (0, sx * (math.pi / 2 + 0.12 + s.get('browtilt', 0.0)), 0)
        ellipsoid(name + '.nose', hc + Vector((0, -0.128, -0.025)) * k * hs, Vector((0.022, 0.02, 0.024)) * k * hs, skin, self.head, seg=12, rings=8)
        m_ = capsule(name + '.mouth', (0, 0, 0), 0.034 * k * hs, 0.007 * k * hs, 0.007 * k * hs, M('#7a3a34'), self.head)
        m_.location = hc + Vector((0.017, -0.113, -0.07)) * k * hs; m_.rotation_euler = (0, math.pi / 2, 0)
        style = s.get('style', 'short')
        if style != 'bald':
            ellipsoid(name + '.hair', hc + Vector((0, 0.006, 0.008)) * k * hs, R * 1.075, hairc, self.head, seg=32, rings=18, cut=HAIR_CUTS[style])
        if style == 'short':
            ellipsoid(name + '.quiff', hc + Vector((0.02, -0.06, 0.11)) * k * hs, Vector((0.08, 0.06, 0.04)) * k * hs, hairc, self.head, seg=16, rings=8)
        if style == 'long':
            ellipsoid(name + '.tail', hc + Vector((0, 0.11, -0.12)) * k * hs, Vector((0.05, 0.045, 0.13)) * k * hs, hairc, self.head, seg=16, rings=10)
        if style == 'bun':
            ellipsoid(name + '.bunb', hc + Vector((0, 0.1, 0.07)) * k * hs, Vector((0.055,) * 3) * k * hs, hairc, self.head, seg=16, rings=10)
        if style == 'bob':
            ellipsoid(name + '.fringe', hc + Vector((0, -0.07, 0.085)) * k * hs, Vector((0.1, 0.05, 0.04)) * k * hs, hairc, self.head, seg=16, rings=8)
        if s.get('beard'):
            ellipsoid(name + '.beard', hc + Vector((0, -0.04, -0.085)) * k * hs, Vector((0.095, 0.085, 0.07)) * k * hs, hairc, self.head, seg=20, rings=10,
                      cut=lambda n: n.z > 0.45)
            ellipsoid(name + '.mous', hc + Vector((0, -0.112, -0.052)) * k * hs, Vector((0.045, 0.014, 0.012)) * k * hs, hairc, self.head, seg=12, rings=6)
        if s.get('glasses'):
            for i, sx in enumerate((1, -1)):
                torus(name + '.lens' + 'LR'[i], hc + Vector((sx * 0.047, -0.13, 0.012)) * k * hs, 0.03 * k * hs, 0.004 * k * hs, M('#2a2a30'), self.head, rot=(math.pi / 2, 0, 0))
            capsule(name + '.bridge', (0, 0, 0), 0.03 * k * hs, 0.003 * k, 0.003 * k, M('#2a2a30'), self.head).location = hc + Vector((0.015, -0.135, 0.015)) * k * hs
        if s.get('cap'):
            ellipsoid(name + '.capdome', hc + Vector((0, 0.0, 0.03)) * k * hs, R * Vector((1.1, 1.1, 0.95)), M(s['cap']), self.head, seg=24, rings=12, cut=lambda n: n.z < 0.15)
            ellipsoid(name + '.brim', hc + Vector((0, -0.12, 0.05)) * k * hs, Vector((0.1, 0.09, 0.012)) * k * hs, M(s['cap']), self.head, seg=16, rings=6, cut=lambda n: n.y > 0.3)
        if suit and s.get('helmet', True):
            ellipsoid(name + '.helmet', hc + Vector((0, 0.01, 0.0)) * k * hs, R * 1.32, M('#f4f2ec'), self.head, seg=32, rings=18,
                      cut=lambda n: n.y < -0.05 and n.z < 0.62 and n.z > -0.7)
            torus(name + '.visor', hc + Vector((0, -0.075, -0.01)) * k * hs, 0.125 * k * hs, 0.012 * k * hs, ring, self.head, rot=(math.pi / 2 - 0.05, 0, 0))
        self.joints = dict(hips=self.hips, chest=self.chest, neck=self.neck, head=self.head, shL=self.sh[0], shR=self.sh[1], elL=self.el[0], elR=self.el[1],
                           haL=self.ha[0], haR=self.ha[1], hpL=self.hp[0], hpR=self.hp[1], knL=self.kn[0], knR=self.kn[1], anL=self.an[0], anR=self.an[1])
        self.parts = [o for o in bpy.data.objects if o.name.startswith(name + '.') and o.type == 'MESH']
    def head_world(self, loc, yaw=0.0):
        """approximate head-top position for tags (feet loc + height)"""
        return (loc[0], loc[1], loc[2] + self.H)

# ------------------------------------------------------------------ poses ------------------------------------------
# A pose is {joint: (forward, side, twist)} in radians: forward swings a limb toward the front (-y); side swings it out
# (away from the body), twist turns about the limb. Missing joints rest at 0. Arms rest slightly out from the body.
def _apply(name, a):
    f, sd, tw = (tuple(a) + (0, 0, 0))[:3]
    if name in ('shL', 'elL', 'haL', 'hpL', 'knL', 'anL'): return (-f, tw, sd)
    if name in ('shR', 'elR', 'haR', 'hpR', 'knR', 'anR'): return (-f, -tw, -sd)
    return (-f, sd, tw)                                       # spine: forward lean, side bend, twist
REST = dict(shL=(0, 0.09), shR=(0, 0.09), elL=(0.12, 0), elR=(0.12, 0))
def blend(a, b, u):
    out = {}
    for k in set(a) | set(b):
        x, y = tuple(a.get(k, (0, 0, 0))) + (0, 0, 0), tuple(b.get(k, (0, 0, 0))) + (0, 0, 0)
        out[k] = tuple(x[i] + (y[i] - x[i]) * u for i in range(3))
    return out
def stand(breath=0.0):
    p = dict(REST); p['chest'] = (0.02 * math.sin(breath), 0, 0); return p
def walk_pose(ph, amp=1.0, run=0.0):
    """ph: gait phase in radians (2*pi per stride pair)"""
    s, c = math.sin(ph), math.cos(ph); a = amp * (0.42 + 0.3 * run)
    return dict(hpL=(a * s,), hpR=(-a * s,), knL=(-(0.5 + 0.5 * run) * amp * max(0, -c) - 0.06,), knR=(-(0.5 + 0.5 * run) * amp * max(0, c) - 0.06,),
                anL=(0.15 * amp * s,), anR=(-0.15 * amp * s,),
                shL=(-0.5 * a * s, 0.1), shR=(0.5 * a * s, 0.1), elL=(0.25 + 0.5 * run,), elR=(0.25 + 0.5 * run,),
                hips=(0.04 * run, 0, 0.06 * amp * s), chest=(0.05 * run, 0, -0.08 * amp * s))
def walk_bob(ph, amp=1.0): return 0.025 * amp * abs(math.cos(ph))

# ------------------------------------------------------------------ baking -----------------------------------------
def _fc(ob, path, idx):
    ad = ob.animation_data or ob.animation_data_create()
    if ad.action is None: ad.action = bpy.data.actions.new(ob.name + 'Act')
    fc = ad.action.fcurves.find(path, index=idx)
    return fc or ad.action.fcurves.new(path, index=idx)
def keys(ob, path, idx, frames, vals, interp='LINEAR'):
    fc = _fc(ob, path, idx); n0 = len(fc.keyframe_points); fc.keyframe_points.add(len(frames))
    co = []
    for f, v in zip(frames, vals): co += [f, v]
    pts = fc.keyframe_points
    flat_ = [0.0] * (2 * len(pts)); pts.foreach_get('co', flat_); flat_[2 * n0:] = co; pts.foreach_set('co', flat_)
    for kp in list(pts)[n0:]: kp.interpolation = interp
    fc.update()
def bake(p, f0, f1, fps, fn, hide_outside=True):
    """fn(t) -> dict(loc=(x,y,z), yaw=rad, pose={joint: angles}, roll=(rx, ry) optional whole-body tilt about the feet)"""
    frames = list(range(f0, f1 + 1)); L = [[], [], []]; Rr = [[], [], []]; J = {k: [[], [], []] for k in p.joints}
    for f in frames:
        d = fn(f / fps); loc = d.get('loc', (0, 0, 0)); yaw = d.get('yaw', 0.0); rl = d.get('roll', (0.0, 0.0))
        for i in range(3): L[i].append(loc[i])
        Rr[0].append(rl[0]); Rr[1].append(rl[1]); Rr[2].append(yaw)
        pose = dict(REST); pose.update(d.get('pose', {}))
        for k in p.joints:
            r = _apply(k, pose.get(k, (0, 0, 0)))
            for i in range(3): J[k][i].append(r[i])
    for i in range(3):
        keys(p.root, 'location', i, frames, L[i]); keys(p.root, 'rotation_euler', i, frames, Rr[i])
        for k, ob in p.joints.items(): keys(ob, 'rotation_euler', i, frames, J[k][i])
    if hide_outside: vis(p, f0, f1)
def vis(p, f0, f1):
    """the person renders only between frames f0 and f1 (may be called several times for several spans)"""
    for o in p.parts:
        o.hide_render = True; o.keyframe_insert('hide_render', frame=0)
        if f0 > 0: o.hide_render = True; o.keyframe_insert('hide_render', frame=f0 - 1)
        o.hide_render = False; o.keyframe_insert('hide_render', frame=f0)
        o.hide_render = False; o.keyframe_insert('hide_render', frame=f1)
        o.hide_render = True; o.keyframe_insert('hide_render', frame=f1 + 1)
        for kp in o.animation_data.action.fcurves.find('hide_render').keyframe_points: kp.interpolation = 'CONSTANT'
