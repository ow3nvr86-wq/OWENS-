"""3D prop sprites: each prop is modelled, lit warm-dusk with soft ink outlines and rendered on a transparent background,
so it sits in the 2D/3D scenes like the sets. Writes <out>/<name>.png and <out>/sprites.json (size + anchor points in
pixels: 'base' = where it stands / is held, 'grip' for hand props).   Original designs.
Run: $BLENDER -b --factory-startup -P tools/props_blender.py -- <out_dir> [name ...] [--spp 32]"""
import bpy, math, sys, os, json, random, importlib.util
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0]; SPP = int(argv[argv.index('--spp') + 1]) if '--spp' in argv else 32
NAMES = ['wall', 'ramp', 'stairs', 'hoprock', 'shotgun', 'sniper', 'bus', 'glider']
WANT = [a for a in argv[1:] if a in NAMES] or NAMES
HERE = os.path.dirname(os.path.abspath(__file__))
def _load(n): s = importlib.util.spec_from_file_location(n, os.path.join(HERE, n + '.py')); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
F2 = _load('presets_fn2'); ISL = F2.ISL
box, cyl, cone, ball, m_emis, m_plain, m_planks, m_noise = ISL.box, ISL.cyl, ISL.cone, ISL.ball, ISL.m_emis, F2.m_plain, F2.m_planks, F2.m_noise
os.makedirs(OUT, exist_ok=True)
meta = json.load(open(os.path.join(OUT, 'sprites.json'))) if os.path.exists(os.path.join(OUT, 'sprites.json')) else {}


def scene(res):
    bpy.ops.wm.read_factory_settings(use_empty=True); ISL._T.clear(); random.seed(3)
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = 0.5
    ISL.dusk_world(sc, 0.9); F2.outlines(sc, 2.6)
    ISL.sunlight(30, 35, 4.2, (1.0, 0.7, 0.48)); ISL.sunlight(25, 200, 2.0, (0.6, 0.5, 1.0))
    return sc


def camera(sc, loc, look, ortho):
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.data.type = 'ORTHO'; c.data.ortho_scale = ortho; sc.camera = c; return c


def px(sc, p):
    v = world_to_camera_view(sc, sc.camera, Vector(p)); return [round(v.x * sc.render.resolution_x, 1), round((1 - v.y) * sc.render.resolution_y, 1)]


def render(sc, name, anchors):
    sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)
    meta[name] = dict(w=sc.render.resolution_x, h=sc.render.resolution_y, **{k: px(sc, v) for k, v in anchors.items()})
    print('rendered sprite', name, flush=True)


for name in WANT:
    if name in ('wall', 'ramp', 'stairs'):
        sc = scene((900, 900)); wood = m_planks('buildWood', (0.62, 0.38, 0.18), (0.55, 0.33, 0.15), 1.4); frame = m_plain('frame', (0.36, 0.2, 0.09), 0.7)
        if name == 'wall':
            box((0, 0, 1.6), (3.2, 0.18, 3.2), wood)
            for x in (-1.55, 1.55): box((x, -0.05, 1.6), (0.22, 0.28, 3.2), frame)
            for z in (0.12, 3.1): box((0, -0.05, z), (3.3, 0.28, 0.22), frame)
            box((0, -0.06, 1.6), (0.18, 0.26, 3.0), frame, (0, math.radians(45), 0))
        elif name == 'ramp':
            box((0, 0, 1.55), (3.2, 0.18, 4.4), wood, (math.radians(-90 + 45), 0, 0)); box((0, 0.2, 0.0), (3.3, 3.3, 0.06), frame)
            for x in (-1.55, 1.55): box((x, 0, 1.55), (0.2, 0.25, 4.4), frame, (math.radians(-90 + 45), 0, 0))
            for x in (-1.5, 1.5): box((x, 1.55, 1.6), (0.2, 0.2, 3.2), frame)
        else:
            for k in range(6): box((0, -1.4 + k * 0.56, 0.27 + k * 0.53), (3.0, 0.62, 0.16), wood)
            for x in (-1.5, 1.5): box((x, 0, 1.6), (0.18, 0.2, 4.4), frame, (math.radians(-90 + 46), 0, 0))
        camera(sc, (7.5, -9.5, 4.6), (0, 0, 1.6), 5.4)
        render(sc, name, {'base': (0, 0, 0)})
    elif name == 'hoprock':
        sc = scene((600, 600)); rock = m_emis('hop', (0.5, 0.08, 1.0), 1.1, (0.36, 0.06, 0.72), 0.2)
        o = ball((0, 0, 0.5), 0.6, rock, 1, (1.1, 0.9, 0.85), smooth=False); o.rotation_euler = (0.4, 0.3, 0.7)
        for k in range(5): a = k * 1.25; cone((math.cos(a) * 0.45, math.sin(a) * 0.45, 0.3), 0.16, 0.6, rock, 5, (math.cos(a) * 0.6, math.sin(a) * 0.6, a))
        bpy.ops.object.light_add(type='POINT', location=(0, -1.2, 0.8)); bpy.context.object.data.energy = 60; bpy.context.object.data.color = (0.6, 0.3, 1.0)
        camera(sc, (2.6, -3.4, 2.0), (0, 0, 0.45), 2.0)
        render(sc, name, {'base': (0, 0, 0), 'grip': (0, 0, 0.45)})
    elif name in ('shotgun', 'sniper'):
        sc = scene((1100, 360)); metal = m_plain('gunMetal', (0.12, 0.12, 0.14), 0.35, 0.8); wood = m_noise('stock', (0.36, 0.18, 0.07), (0.46, 0.25, 0.1), 6, 0.6, 0.15)
        L = 1.0 if name == 'shotgun' else 1.3
        cyl((0.15 + L * 0.5, 0, 0.05), 0.035, L, metal, (0, math.pi / 2, 0), 16)                         # barrel
        box((0.05, 0, 0.0), (0.36, 0.07, 0.14), metal)                                                   # receiver
        box((-0.38, 0, -0.04), (0.52, 0.06, 0.13), wood, (0, math.radians(-8), 0))                       # stock
        box((-0.07, 0, -0.12), (0.06, 0.05, 0.16), wood, (0, math.radians(15), 0))                        # grip
        if name == 'shotgun': box((0.55, 0, -0.03), (0.32, 0.075, 0.07), wood)                           # pump
        else:
            cyl((0.15, 0, 0.14), 0.045, 0.52, metal, (0, math.pi / 2, 0), 20); cyl((0.42, 0, 0.14), 0.06, 0.06, m_emis('lens', (0.5, 0.8, 1.0), 2.0), (0, math.pi / 2, 0), 20)
            box((0.15, 0, 0.08), (0.06, 0.04, 0.08), metal); cyl((0.05, 0.06, 0.04), 0.012, 0.09, metal, (math.pi / 2, 0, 0), 8)
        camera(sc, (0.3, -4, 0.02), (0.3, 0, 0.02), 2.0 if name == 'shotgun' else 2.4)
        render(sc, name, {'grip': (-0.07, 0, -0.16), 'muzzle': (0.15 + L, 0, 0.05)})
    elif name == 'bus':
        sc = scene((900, 1300)); blue = m_plain('busBlue', (0.08, 0.32, 0.75), 0.35); yel = m_plain('busY', (0.95, 0.75, 0.15), 0.4)
        glass = m_plain('busGlass', (0.55, 0.75, 0.9), 0.1); tire = m_plain('tire', (0.04, 0.04, 0.05), 0.7)
        box((0, 0, 1.4), (2.5, 9.0, 2.2), blue); box((0, 0, 1.0), (2.52, 9.02, 0.25), yel); box((0, 4.6, 1.1), (2.3, 0.3, 1.4), blue)
        for k in range(6): box((1.27, -3.6 + k * 1.35, 1.9), (0.04, 1.0, 0.8), glass); box((-1.27, -3.6 + k * 1.35, 1.9), (0.04, 1.0, 0.8), glass)
        box((0, 4.52, 1.9), (2.1, 0.04, 0.8), glass)
        for x in (-1.2, 1.2):
            for y in (-3, 3): cyl((x, y, 0.4), 0.5, 0.35, tire, (0, math.pi / 2, 0), 20)
        stripes = [m_plain('bal%d' % i, c, 0.6) for i, c in enumerate([(0.85, 0.12, 0.1), (0.95, 0.8, 0.2)])]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=4.2, location=(0, 0, 10.5), segments=16, ring_count=12); bal = bpy.context.object; bal.scale = (1, 1, 1.15)
        for i in range(2): bal.data.materials.append(stripes[i])
        for p in bal.data.polygons: p.material_index = (int((math.atan2(p.center.y, p.center.x) + math.pi) / (2 * math.pi) * 16)) % 2
        bpy.ops.object.shade_smooth()
        for (x, y) in [(-1.1, -3.5), (1.1, -3.5), (-1.1, 3.5), (1.1, 3.5)]:
            a = Vector((x, y, 2.5)); b = Vector((x * 2.2, y * 0.6, 7.0)); d = b - a
            cyl(tuple((a + b) / 2), 0.04, d.length, tire, (0, math.atan2(math.hypot(d.x, d.y), d.z), math.atan2(d.y, d.x) + math.pi / 2 * 0), 6)
        camera(sc, (14, -16, 8), (0, 0, 5.2), 21)
        render(sc, name, {'base': (0, 0, 0.0), 'roof': (0, 0, 2.5)})
    elif name == 'glider':
        sc = scene((900, 600)); cols = [m_plain('gl%d' % i, c, 0.6) for i, c in enumerate([(0.95, 0.75, 0.15), (0.85, 0.15, 0.1)])]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=2.0, location=(0, 0, 0), segments=12, ring_count=8); o = bpy.context.object
        for i in range(2): o.data.materials.append(cols[i])
        for p in o.data.polygons: p.material_index = (int((math.atan2(p.center.y, p.center.x) + math.pi) / (2 * math.pi) * 12)) % 2
        bm = o.data; [setattr(v.co, 'z', max(v.co.z, 0.4) * 0.55) for v in bm.vertices]; bpy.ops.object.shade_smooth()
        dark = m_plain('rope', (0.05, 0.05, 0.06), 0.7)
        for a in (0.5, 2.6): x, y = math.cos(a) * 1.8, math.sin(a) * 0.4; cyl((x * 0.5, y, -1.0), 0.03, 2.6, dark, (0, -math.atan2(x, 2.6) * 1.0, 0), 6)
        camera(sc, (0, -7, 0.4), (0, 0, -0.4), 5.0)
        render(sc, name, {'gripL': (-0.6, 0, -2.2), 'gripR': (0.6, 0, -2.2)})
json.dump(meta, open(os.path.join(OUT, 'sprites.json'), 'w'), indent=1)
