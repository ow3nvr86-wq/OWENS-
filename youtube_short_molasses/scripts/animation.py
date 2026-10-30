"""The Wave of Molasses — fully procedural Blender scene, animation and render.

Run with Blender 4.2 LTS (headless):
  blender -b --factory-startup -P scripts/animation.py -- [options]

Options:
  --quality preview|final     preview = 25 % resolution, few samples (default final)
  --frames A-B                render an animation range (1-based frames, 30 fps)
  --stills F1,F2,...          render individual frames (for framing checks)
  --out DIR                   output folder for PNG frames (default renders/frames)
  --save-blend PATH           also save the generated .blend for inspection

Everything is generated here from code: terrain, buildings, the riveted tank, the
elevated railway, harbour, debris, people, materials, lights and cameras. The molasses
surface is driven every frame by the shallow-water simulation in build/flood_sim.npz
(see simulate_flood.py), and shot timing comes from build/timeline.json (voiceover.py).
"""
import argparse
import json
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import layout as L  # noqa: E402

FPS = 30
RES = (1080, 1920)
FONT_PATH = os.path.join(ROOT, 'assets', 'fonts', 'Anton-Regular.ttf')


# ----------------------------------------------------------------------------
# Arguments
# ----------------------------------------------------------------------------
def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--quality', default='final', choices=['preview', 'draft', 'final'])
    ap.add_argument('--frames', default=None)
    ap.add_argument('--stills', default=None)
    ap.add_argument('--out', default=os.path.join(ROOT, 'renders', 'frames'))
    ap.add_argument('--save-blend', default=None)
    ap.add_argument('--export-events', action='store_true',
                    help='write build/events.json (cue times and on-screen anchor points) and exit')
    return ap.parse_args(argv)


ARGS = parse_args()

# ----------------------------------------------------------------------------
# Timeline: shot list derived from the real voiceover timing
# ----------------------------------------------------------------------------
TL = json.load(open(os.path.join(ROOT, 'build', 'timeline.json')))
LINE = {l['id']: l for l in TL['lines']}
END_T = TL['duration'] + 1.6


def ls(i):
    return LINE[i]['start']


def frame(t):
    return int(round(t * FPS)) + 1


# (name, start time, sim-time mapping) — sim mapping: None = before the collapse,
# ('lin', a, b) = sim time runs from a to b across the shot, ('hold', a) = frozen.
CUTS = [
    ('hook', 0.0, ('lin', 0.8, 1.58)),
    ('aerial', ls('L02') - 0.2, None),
    ('scale', ls('L03') - 0.1, None),
    ('leaks', ls('L04') - 0.1, None),
    ('cutaway', ls('L05') - 0.1, None),
    ('paint', ls('L06') - 0.05, None),
    ('thermo', ls('L07') - 0.1, None),
    ('rivets', ls('L08') - 0.15, None),
    ('burst', ls('L09') - 0.05, ('lin', 0.0, 1.15)),
    ('race', ls('L10') - 0.1, ('lin', 1.15, 5.4)),
    ('house', ls('L11') - 0.05, ('lin', 1.6, 4.8)),
    ('el', ls('L11') + 1.95, ('lin', 1.8, 4.6)),
    ('rise', ls('L12') - 0.15, ('lin', 6.0, 13.0)),
    ('freeze', ls('L13') - 0.1, ('lin', 13.0, 41.0)),
    ('stuck', ls('L14') - 0.1, ('hold', 41.0)),
    ('decades', ls('L15') - 0.2, None),
    ('end', ls('L16') - 0.15, ('hold', 1.5)),
]
SHOTS = []
for i, (name, t0, sim) in enumerate(CUTS):
    t1 = CUTS[i + 1][1] if i + 1 < len(CUTS) else END_T
    SHOTS.append(dict(name=name, t0=t0, t1=t1, f0=frame(t0), f1=frame(t1) - 1, sim=sim))
SHOT = {s['name']: s for s in SHOTS}
LAST_FRAME = SHOTS[-1]['f1']


def shot_at(f):
    for s in SHOTS:
        if s['f0'] <= f <= s['f1']:
            return s
    return SHOTS[-1]


def sim_time(s, tv):
    if s['sim'] is None:
        return None
    if s['sim'][0] == 'hold':
        return s['sim'][1]
    a, b = s['sim'][1], s['sim'][2]
    u = (tv - s['t0']) / max(s['t1'] - s['t0'], 1e-6)
    return a + (b - a) * u


# ----------------------------------------------------------------------------
# Scene reset and render settings
# ----------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.name = 'MolassesFlood'
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, LAST_FRAME
    sc.unit_settings.system = 'METRIC'
    return sc


def setup_render(sc):
    q = ARGS.quality
    r = sc.render
    r.engine = 'CYCLES'
    r.resolution_x, r.resolution_y = RES
    # 'final' renders 540x960 and post.py upscales to 1080x1920 (CPU-only render budget, see README)
    r.resolution_percentage = {'preview': 25, 'draft': 50, 'final': 50}[q]
    r.use_motion_blur = False          # motion blur is added in post (see post.py)
    r.motion_blur_shutter = 0.45
    r.use_persistent_data = True
    r.use_lock_interface = True
    r.film_transparent = False
    r.use_overwrite = False            # lets an interrupted render resume where it stopped
    r.use_placeholder = True
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_mode = 'RGB'
    r.image_settings.color_depth = '8'
    c = sc.cycles
    c.device = 'CPU'
    c.samples = {'preview': 8, 'draft': 8, 'final': 8}[q]
    c.use_adaptive_sampling = True
    c.adaptive_threshold = {'preview': 0.1, 'draft': 0.06, 'final': 0.05}[q]
    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces = 4, 1, 1
    c.transmission_bounces, c.transparent_max_bounces, c.volume_bounces = 4, 4, 0
    c.sample_clamp_indirect = 4.0
    c.caustics_reflective = c.caustics_refractive = False
    c.blur_glossy = 1.0
    c.filter_width = 1.5
    c.seed = 7
    c.use_animated_seed = False        # steadier denoised result between frames
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass
    sc.view_layers[0].use_pass_mist = True


# ----------------------------------------------------------------------------
# Small helpers: meshes, materials, keyframes
# ----------------------------------------------------------------------------
COLL = {}


def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


def obj_from_bm(name, bm, mat=None, collection='World', smooth=False, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if mat is not None:
        me.materials.append(mat)
    coll(collection).objects.link(ob)
    return ob


def add_box(bm, x0, y0, z0, x1, y1, z1):
    m = Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal(
        (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), 1))
    bmesh.ops.create_cube(bm, size=1.0, matrix=m)


def add_cyl(bm, r1, r2, depth, seg=16, matrix=Matrix()):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r1, radius2=r2,
                          depth=depth, matrix=matrix)


def add_sphere(bm, r, u=16, v=10, matrix=Matrix()):
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r, matrix=matrix)


def empty(name, loc=(0, 0, 0), collection='Rig'):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    coll(collection).objects.link(e)
    return e


def key(target, path, f, value, interp='BEZIER', index=-1):
    if index >= 0:
        getattr(target, path)[index] = value
    else:
        setattr(target, path, value)
    target.keyframe_insert(data_path=path, frame=f, index=index)


def set_interp(idblock, interp='LINEAR'):
    ad = getattr(idblock, 'animation_data', None)
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = interp


# --- shader node helpers ---
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    return m, nt, out


def nd(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        if k.startswith('p_'):
            setattr(n, k[2:], v)
        else:
            sock = n.inputs[k]
            if hasattr(v, 'is_output') or isinstance(v, bpy.types.NodeSocket):
                nt.links.new(v, sock)
            else:
                sock.default_value = v
    return n


def lk(nt, a, b):
    nt.links.new(a, b)


def mth(nt, op, a, b=None, c=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, n.inputs[i])
        else:
            n.inputs[i].default_value = v
    return n.outputs[0]


def mixc(nt, fac, a, b):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    for idx, v in ((0, fac), (6, a), (7, b)):
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, n.inputs[idx])
        else:
            n.inputs[idx].default_value = v if idx else v
    return n.outputs[2]


def mixf(nt, fac, a, b):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'FLOAT'
    for idx, v in ((0, fac), (2, a), (3, b)):
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, n.inputs[idx])
        else:
            n.inputs[idx].default_value = v
    return n.outputs[0]


def rgba(c):
    return (c[0], c[1], c[2], 1.0)


def principled(nt, out, **kw):
    p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    for k, v in kw.items():
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, p.inputs[k])
        else:
            p.inputs[k].default_value = v
    nt.links.new(p.outputs[0], out.inputs['Surface'])
    return p


def frame_driver(sock, expr):
    d = sock.driver_add('default_value').driver
    d.type = 'SCRIPTED'
    d.expression = expr


# ----------------------------------------------------------------------------
# Global animated environment values shared by all materials (a node group)
# ----------------------------------------------------------------------------
ENV = None
ENV_KEYS = ['night', 'frost', 'wipe', 'stain', 'leak', 'wet']


def make_env_group():
    global ENV
    ENV = bpy.data.node_groups.new('ENV', 'ShaderNodeTree')
    go = ENV.nodes.new('NodeGroupOutput')
    for i, k in enumerate(ENV_KEYS):
        ENV.interface.new_socket(k, in_out='OUTPUT', socket_type='NodeSocketFloat')
        v = ENV.nodes.new('ShaderNodeValue')
        v.name = k
        v.outputs[0].default_value = 0.0
        ENV.links.new(v.outputs[0], go.inputs[i])


def env_node(nt):
    g = nt.nodes.new('ShaderNodeGroup')
    g.node_tree = ENV
    return g


def env_key(k, f, value):
    s = ENV.nodes[k].outputs[0]
    s.default_value = value
    s.keyframe_insert('default_value', frame=f)


# ----------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------
MAT = {}


def wall_uv(nt):
    """Facade coordinates in metres: u runs along the wall, v is height."""
    geo = nd(nt, 'ShaderNodeNewGeometry')
    sp = nd(nt, 'ShaderNodeSeparateXYZ', Vector=geo.outputs['Position'])
    sn = nd(nt, 'ShaderNodeSeparateXYZ', Vector=geo.outputs['Normal'])
    selx = mth(nt, 'GREATER_THAN', mth(nt, 'ABSOLUTE', sn.outputs['X']), 0.5)
    u = mth(nt, 'MULTIPLY_ADD', mth(nt, 'SUBTRACT', sp.outputs['Y'], sp.outputs['X']), selx, sp.outputs['X'])
    v = sp.outputs['Z']
    wall = mth(nt, 'LESS_THAN', mth(nt, 'ABSOLUTE', sn.outputs['Z']), 0.5)
    return u, v, wall, sp


def band(nt, x, lo, hi):
    return mth(nt, 'MULTIPLY', mth(nt, 'GREATER_THAN', x, lo), mth(nt, 'LESS_THAN', x, hi))


def facade_material(name, c1, c2, mortar, trim, bay=2.9, storey=3.4, wood=False, win=(0.3, 0.7, 0.22, 0.8),
                    shop=True, rough=0.85):
    m, nt, out = new_mat(name)
    env = env_node(nt)
    u, v, wall, sp = wall_uv(nt)
    uvw = nd(nt, 'ShaderNodeCombineXYZ', X=u, Y=v)
    if wood:
        bands_ = nd(nt, 'ShaderNodeTexWave', Vector=uvw.outputs[0], Scale=6.0, Distortion=0.0, Detail=0.0,
                    p_wave_type='BANDS', p_bands_direction='Y')
        nz = nd(nt, 'ShaderNodeTexNoise', Vector=uvw.outputs[0], Scale=3.0, Detail=4.0)
        surf_col = mixc(nt, mth(nt, 'MULTIPLY', nz.outputs['Fac'], 0.8), rgba(c1), rgba(c2))
        relief = bands_.outputs['Fac']
    else:
        br = nd(nt, 'ShaderNodeTexBrick', Vector=uvw.outputs[0], Color1=rgba(c1), Color2=rgba(c2),
                Mortar=rgba(mortar), Scale=1.0, **{'Mortar Size': 0.012, 'Brick Width': 0.23,
                                                    'Row Height': 0.076, 'Mortar Smooth': 0.2})
        br.offset = 0.5
        nz = nd(nt, 'ShaderNodeTexNoise', Vector=uvw.outputs[0], Scale=0.6, Detail=6.0)
        grime = mth(nt, 'MULTIPLY', mth(nt, 'SUBTRACT', 1.0, mth(nt, 'MULTIPLY', v, 0.04), clamp=True), 0.35)
        surf_col = mixc(nt, mth(nt, 'MULTIPLY', grime, nz.outputs['Fac']), br.outputs['Color'], (0.05, 0.04, 0.035, 1))
        relief = mth(nt, 'SUBTRACT', 1.0, br.outputs['Fac'])
    fu = mth(nt, 'FRACT', mth(nt, 'DIVIDE', u, bay))
    fv = mth(nt, 'FRACT', mth(nt, 'DIVIDE', v, storey))
    upper = mth(nt, 'GREATER_THAN', v, storey)
    w_up = mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', band(nt, fu, win[0], win[1]), band(nt, fv, win[2], win[3])), upper)
    f_up = mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', band(nt, fu, win[0] - 0.05, win[1] + 0.05),
                                    band(nt, fv, win[2] - 0.04, win[3] + 0.05)), upper)
    if shop:
        w_sh = mth(nt, 'MULTIPLY', band(nt, fu, 0.1, 0.9), band(nt, v, 0.6, 2.75))
        f_sh = mth(nt, 'MULTIPLY', band(nt, fu, 0.06, 0.94), band(nt, v, 0.45, 3.0))
        w_any = mth(nt, 'MAXIMUM', w_up, w_sh)
        f_any = mth(nt, 'MAXIMUM', f_up, f_sh)
    else:
        w_any, f_any = w_up, f_up
    winm = mth(nt, 'MULTIPLY', w_any, wall)
    frm = mth(nt, 'MULTIPLY', mth(nt, 'SUBTRACT', f_any, w_any, clamp=True), wall)
    # random lit windows at night
    oi = nd(nt, 'ShaderNodeObjectInfo')
    cell = nd(nt, 'ShaderNodeCombineXYZ', X=mth(nt, 'FLOOR', mth(nt, 'DIVIDE', u, bay)),
              Y=mth(nt, 'FLOOR', mth(nt, 'DIVIDE', v, storey)), Z=mth(nt, 'MULTIPLY', oi.outputs['Random'], 37.0))
    wn = nd(nt, 'ShaderNodeTexWhiteNoise', Vector=cell.outputs[0], p_noise_dimensions='3D')
    lit = mth(nt, 'GREATER_THAN', wn.outputs['Value'], 0.48)
    glow = mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', winm, lit), mth(nt, 'MULTIPLY', env.outputs['night'], 7.0))
    glass = mixc(nt, mth(nt, 'MULTIPLY', wn.outputs['Value'], 0.6), (0.02, 0.025, 0.03, 1), (0.08, 0.07, 0.06, 1))
    col = mixc(nt, frm, surf_col, rgba(trim))
    col = mixc(nt, winm, col, glass)
    roughs = mixf(nt, winm, mixf(nt, frm, rough, 0.5), 0.08)
    bump = nd(nt, 'ShaderNodeBump', Strength=0.35, Distance=0.02,
              Height=mth(nt, 'ADD', mth(nt, 'MULTIPLY', relief, 0.5), mth(nt, 'MULTIPLY', frm, 1.5)))
    nt.nodes.remove(bump)
    principled(nt, out, **{'Base Color': col, 'Roughness': roughs,
                           'Emission Color': (1.0, 0.62, 0.3, 1.0), 'Emission Strength': glow})
    return m


def simple_mat(name, color, rough=0.6, metal=0.0, noise_amt=0.15, noise_scale=3.0, bump=0.1, emission=None,
               emit_env=None, emit_strength=1.0):
    m, nt, out = new_mat(name)
    tc = nd(nt, 'ShaderNodeTexCoord')
    nz = nd(nt, 'ShaderNodeTexNoise', Vector=tc.outputs['Object'], Scale=noise_scale, Detail=6.0)
    col = mixc(nt, mth(nt, 'MULTIPLY', nz.outputs['Fac'], noise_amt * 2),
               rgba(color), (color[0] * 0.55, color[1] * 0.5, color[2] * 0.45, 1))
    bp = nd(nt, 'ShaderNodeBump', Strength=bump, Distance=0.02, Height=nz.outputs['Fac'])
    kw = {'Base Color': col, 'Roughness': rough, 'Metallic': metal}
    if bump >= 0.3:
        kw['Normal'] = bp.outputs['Normal']
    else:
        nt.nodes.remove(bp)
    if emission is not None:
        kw['Emission Color'] = rgba(emission)
        if emit_env:
            env = env_node(nt)
            kw['Emission Strength'] = mth(nt, 'MULTIPLY', env.outputs[emit_env], emit_strength)
        else:
            kw['Emission Strength'] = emit_strength
    principled(nt, out, **kw)
    return m


def cobble_material():
    m, nt, out = new_mat('Cobbles')
    geo = nd(nt, 'ShaderNodeNewGeometry')
    vor = nd(nt, 'ShaderNodeTexVoronoi', Vector=geo.outputs['Position'], Scale=6.5, Randomness=0.85,
             p_feature='DISTANCE_TO_EDGE', p_voronoi_dimensions='2D')
    vc = nd(nt, 'ShaderNodeTexVoronoi', Vector=geo.outputs['Position'], Scale=6.5, Randomness=0.85,
            p_voronoi_dimensions='2D')
    gap = mth(nt, 'LESS_THAN', vor.outputs['Distance'], 0.07)
    ramp = nd(nt, 'ShaderNodeValToRGB', Fac=vc.outputs['Color'])
    ramp.color_ramp.elements[0].color = (0.035, 0.032, 0.03, 1)
    ramp.color_ramp.elements[1].color = (0.12, 0.1, 0.085, 1)
    big = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=0.05, Detail=3.0)
    snow = mth(nt, 'GREATER_THAN', big.outputs['Fac'], 0.72)
    col = mixc(nt, gap, ramp.outputs['Color'], (0.025, 0.022, 0.02, 1))
    grime = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=0.4, Detail=6.0)
    col = mixc(nt, mth(nt, 'MULTIPLY', grime.outputs['Fac'], 0.6), col, (0.03, 0.025, 0.02, 1))
    col = mixc(nt, mth(nt, 'MULTIPLY', snow, 0.7), col, (0.62, 0.63, 0.65, 1))
    h = mth(nt, 'MINIMUM', mth(nt, 'MULTIPLY', vor.outputs['Distance'], 6.0), 1.0)
    bp = nd(nt, 'ShaderNodeBump', Strength=0.35, Distance=0.04, Height=h)
    principled(nt, out, **{'Base Color': col, 'Roughness': mixf(nt, gap, mixf(nt, grime.outputs['Fac'], 0.35, 0.7), 0.9),
                           'Normal': bp.outputs['Normal']})
    return m


def slab_material(name, c1, c2, size=1.2, rough=0.8):
    m, nt, out = new_mat(name)
    geo = nd(nt, 'ShaderNodeNewGeometry')
    br = nd(nt, 'ShaderNodeTexBrick', Vector=geo.outputs['Position'], Color1=rgba(c1), Color2=rgba(c2),
            Mortar=(0.06, 0.06, 0.06, 1), Scale=1.0, **{'Mortar Size': 0.015, 'Brick Width': size,
                                                         'Row Height': size * 0.6})
    nz = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=2.0, Detail=8.0)
    col = mixc(nt, mth(nt, 'MULTIPLY', nz.outputs['Fac'], 0.35), br.outputs['Color'], (0.1, 0.09, 0.08, 1))
    bp = nd(nt, 'ShaderNodeBump', Strength=0.3, Distance=0.02,
            Height=mth(nt, 'ADD', mth(nt, 'SUBTRACT', 1.0, br.outputs['Fac']), mth(nt, 'MULTIPLY', nz.outputs['Fac'], 0.3)))
    nt.nodes.remove(bp)
    principled(nt, out, **{'Base Color': col, 'Roughness': rough})
    return m


def dirt_material():
    m, nt, out = new_mat('Yard')
    geo = nd(nt, 'ShaderNodeNewGeometry')
    n1 = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=0.4, Detail=8.0, Roughness=0.6)
    n2 = nd(nt, 'ShaderNodeTexVoronoi', Vector=geo.outputs['Position'], Scale=14.0)
    col = mixc(nt, n1.outputs['Fac'], (0.16, 0.13, 0.1, 1), (0.3, 0.26, 0.21, 1))
    col = mixc(nt, mth(nt, 'MULTIPLY', n2.outputs['Distance'], 0.5), col, (0.08, 0.07, 0.06, 1))
    bp = nd(nt, 'ShaderNodeBump', Strength=0.4, Distance=0.03, Height=n2.outputs['Distance'])
    nt.nodes.remove(bp)
    principled(nt, out, **{'Base Color': col, 'Roughness': 0.95})
    return m


def tank_material():
    """Riveted steel plates; animated brown paint wipe; glossy molasses leak streaks."""
    m, nt, out = new_mat('TankSteel')
    env = env_node(nt)
    geo = nd(nt, 'ShaderNodeNewGeometry')
    sp = nd(nt, 'ShaderNodeSeparateXYZ', Vector=geo.outputs['Position'])
    dx = mth(nt, 'SUBTRACT', sp.outputs['X'], L.TANK_X)
    dy = mth(nt, 'SUBTRACT', sp.outputs['Y'], L.TANK_Y)
    ang = mth(nt, 'DIVIDE', mth(nt, 'ADD', mth(nt, 'ARCTAN2', dx, dy), math.pi), 2 * math.pi)  # 0..1 around
    z = sp.outputs['Z']
    course = mth(nt, 'FRACT', mth(nt, 'DIVIDE', z, L.TANK_H / 6))
    hseam = mth(nt, 'MAXIMUM', mth(nt, 'LESS_THAN', course, 0.008), mth(nt, 'GREATER_THAN', course, 0.992))
    vseam = mth(nt, 'LESS_THAN', mth(nt, 'FRACT', mth(nt, 'MULTIPLY', ang, 16.0)), 0.0016)
    seam = mth(nt, 'MAXIMUM', hseam, vseam)
    # leak streaks: run down from each plate seam
    sv = nd(nt, 'ShaderNodeCombineXYZ', X=mth(nt, 'MULTIPLY', ang, 260.0), Y=mth(nt, 'MULTIPLY', z, 0.35))
    sn = nd(nt, 'ShaderNodeTexNoise', Vector=sv.outputs[0], Scale=1.0, Detail=2.0, Roughness=0.4)
    streak = mth(nt, 'MULTIPLY', mth(nt, 'GREATER_THAN', sn.outputs['Fac'], 0.56),
                 mth(nt, 'POWER', course, 2.5))
    streak = mth(nt, 'MULTIPLY', streak, env.outputs['leak'])
    rust_n = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=1.4, Detail=10.0, Roughness=0.7)
    rust = mth(nt, 'GREATER_THAN', rust_n.outputs['Fac'], 0.6)
    steel = mixc(nt, rust, (0.32, 0.335, 0.34, 1), (0.3, 0.16, 0.08, 1))
    paint_n = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=5.0, Detail=4.0)
    paint = mixc(nt, mth(nt, 'MULTIPLY', paint_n.outputs['Fac'], 0.4), (0.25, 0.13, 0.06, 1), (0.16, 0.08, 0.035, 1))
    painted = mth(nt, 'LESS_THAN', ang, env.outputs['wipe'])
    fresh = mth(nt, 'MULTIPLY', painted, mth(nt, 'LESS_THAN', mth(nt, 'SUBTRACT', env.outputs['wipe'], ang), 0.025))
    col = mixc(nt, painted, steel, paint)
    col = mixc(nt, mth(nt, 'MULTIPLY', streak, 0.9), col, (0.07, 0.025, 0.006, 1))
    col = mixc(nt, mth(nt, 'MULTIPLY', seam, 0.6), col, (0.05, 0.04, 0.035, 1))
    rough = mixf(nt, painted, 0.5, 0.42)
    rough = mixf(nt, fresh, rough, 0.12)
    rough = mixf(nt, streak, rough, 0.07)
    bp = nd(nt, 'ShaderNodeBump', Strength=0.5, Distance=0.01,
            Height=mth(nt, 'ADD', mth(nt, 'MULTIPLY', seam, -1.0), mth(nt, 'MULTIPLY', streak, 0.6)))
    principled(nt, out, **{'Base Color': col, 'Roughness': rough, 'Metallic': mixf(nt, painted, 0.55, 0.0),
                           'Normal': bp.outputs['Normal']})
    return m


def molasses_material():
    m, nt, out = new_mat('Molasses')
    env = env_node(nt)
    depth = nd(nt, 'ShaderNodeAttribute', p_attribute_name='depth', p_attribute_type='GEOMETRY')
    speed = nd(nt, 'ShaderNodeAttribute', p_attribute_name='speed', p_attribute_type='GEOMETRY')
    dmap = nd(nt, 'ShaderNodeMapRange', Value=depth.outputs['Fac'], **{'From Min': 0.0, 'From Max': 2.5})
    ramp = nd(nt, 'ShaderNodeValToRGB', Fac=dmap.outputs[0])
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.3, 0.11, 0.022, 1)
    els[1].position, els[1].color = 1.0, (0.055, 0.02, 0.005, 1)
    e = els.new(0.08)
    e.color = (0.11, 0.04, 0.009, 1)
    geo = nd(nt, 'ShaderNodeNewGeometry')
    nz = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=0.8, Detail=6.0, Roughness=0.6,
            p_noise_dimensions='4D')
    frame_driver(nz.inputs['W'], 'frame/45')
    fine = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=9.0, Detail=3.0, p_noise_dimensions='4D')
    frame_driver(fine.inputs['W'], 'frame/20')
    spd = nd(nt, 'ShaderNodeMapRange', Value=speed.outputs['Fac'], **{'From Min': 0.5, 'From Max': 10.0})
    # frost crystals forming as the night freezes
    vor = nd(nt, 'ShaderNodeTexVoronoi', Vector=geo.outputs['Position'], Scale=110.0, p_feature='DISTANCE_TO_EDGE')
    fmask_n = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=0.35, Detail=4.0)
    frost = mth(nt, 'MULTIPLY', mth(nt, 'GREATER_THAN', fmask_n.outputs['Fac'],
                                     mth(nt, 'SUBTRACT', 1.05, mth(nt, 'MULTIPLY', env.outputs['frost'], 0.75))),
                env.outputs['frost'])
    crystal = mth(nt, 'MULTIPLY', frost, mth(nt, 'LESS_THAN', vor.outputs['Distance'], 0.05))
    frost_amt = mth(nt, 'MINIMUM', mth(nt, 'ADD', mth(nt, 'MULTIPLY', frost, 0.22), mth(nt, 'MULTIPLY', crystal, 0.6)), 1.0)
    col = mixc(nt, mth(nt, 'MULTIPLY', spd.outputs[0], 0.25), ramp.outputs['Color'], (0.16, 0.06, 0.012, 1))
    col = mixc(nt, frost_amt, col, (0.42, 0.45, 0.5, 1))
    h = mth(nt, 'ADD', mth(nt, 'MULTIPLY', nz.outputs['Fac'], mth(nt, 'ADD', 0.25, spd.outputs[0])),
            mth(nt, 'MULTIPLY', fine.outputs['Fac'], 0.12))
    h = mth(nt, 'ADD', h, mth(nt, 'MULTIPLY', crystal, 0.6))
    bp = nd(nt, 'ShaderNodeBump', Strength=mixf(nt, env.outputs['frost'], 0.35, 0.45), Distance=0.12, Height=h)
    principled(nt, out, **{'Base Color': col,
                           'Roughness': mixf(nt, frost_amt, mixf(nt, env.outputs['frost'], 0.3, 0.38), 0.75),
                           'Coat Weight': mixf(nt, frost_amt, 0.18, 0.0), 'Coat Roughness': 0.04,
                           'Specular IOR Level': 0.3,
                           'Subsurface Weight': 0.0, 'Subsurface Radius': (1.0, 0.35, 0.08),
                           'Subsurface Scale': 0.06, 'IOR': 1.48, 'Normal': bp.outputs['Normal']})
    return m


def water_material():
    m, nt, out = new_mat('Harbour')
    env = env_node(nt)
    geo = nd(nt, 'ShaderNodeNewGeometry')
    sp = nd(nt, 'ShaderNodeSeparateXYZ', Vector=geo.outputs['Position'])
    nz = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=0.25, Detail=6.0, p_noise_dimensions='4D')
    frame_driver(nz.inputs['W'], 'frame/90')
    dist = mth(nt, 'SQRT', mth(nt, 'ADD', mth(nt, 'POWER', mth(nt, 'SUBTRACT', sp.outputs['X'], L.TANK_X), 2.0),
                                 mth(nt, 'POWER', mth(nt, 'SUBTRACT', sp.outputs['Y'], L.SEAWALL_Y), 2.0)))
    st_n = nd(nt, 'ShaderNodeTexNoise', Vector=geo.outputs['Position'], Scale=0.03, Detail=3.0)
    radius = mth(nt, 'MULTIPLY', env.outputs['stain'], 220.0)
    stain = mth(nt, 'LESS_THAN', mth(nt, 'ADD', dist, mth(nt, 'MULTIPLY', st_n.outputs['Fac'], 60.0)), radius)
    col = mixc(nt, mth(nt, 'MULTIPLY', stain, 0.85), (0.012, 0.025, 0.03, 1), (0.05, 0.02, 0.006, 1))
    bp = nd(nt, 'ShaderNodeBump', Strength=0.25, Distance=0.1, Height=nz.outputs['Fac'])
    principled(nt, out, **{'Base Color': col, 'Roughness': 0.04, 'IOR': 1.33, 'Specular IOR Level': 0.6,
                           'Normal': bp.outputs['Normal']})
    return m


def glass_mat(name, color=(0.9, 0.95, 1.0)):
    m, nt, out = new_mat(name)
    g = nt.nodes.new('ShaderNodeBsdfGlass')
    g.inputs['Color'].default_value = rgba(color)
    g.inputs['Roughness'].default_value = 0.02
    g.inputs['IOR'].default_value = 1.45
    lk(nt, g.outputs[0], out.inputs['Surface'])
    return m


def wisp_material():
    m, nt, out = new_mat('Wisp')
    oi = nd(nt, 'ShaderNodeObjectInfo')
    sep = nd(nt, 'ShaderNodeSeparateColor', Color=oi.outputs['Color'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (1.0, 0.62, 0.25, 1)
    em.inputs['Strength'].default_value = 0.7
    lw = nd(nt, 'ShaderNodeLayerWeight', Blend=0.6)
    fac = mth(nt, 'MULTIPLY', mth(nt, 'POWER', mth(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), 2.0), mth(nt, 'MULTIPLY', sep.outputs[0], 0.16))
    mx = nt.nodes.new('ShaderNodeMixShader')
    lk(nt, fac, mx.inputs[0]); lk(nt, tr.outputs[0], mx.inputs[1]); lk(nt, em.outputs[0], mx.inputs[2])
    lk(nt, mx.outputs[0], out.inputs['Surface'])
    m.blend_method = 'BLEND'
    return m


def build_materials():
    MAT['cobble'] = cobble_material()
    MAT['sidewalk'] = slab_material('Granite', (0.36, 0.35, 0.34), (0.3, 0.29, 0.28), size=1.1)
    MAT['seawall'] = slab_material('Seawall', (0.33, 0.32, 0.3), (0.25, 0.24, 0.23), size=1.6, rough=0.9)
    MAT['yard'] = dirt_material()
    MAT['brick'] = facade_material('Brick', (0.2, 0.065, 0.035), (0.14, 0.045, 0.025), (0.26, 0.25, 0.23), (0.42, 0.4, 0.36))
    MAT['brick_dark'] = facade_material('BrickDark', (0.12, 0.045, 0.028), (0.09, 0.035, 0.022), (0.22, 0.21, 0.2), (0.1, 0.11, 0.1))
    MAT['stone'] = facade_material('Stone', (0.3, 0.27, 0.22), (0.25, 0.23, 0.19), (0.2, 0.19, 0.17), (0.14, 0.13, 0.12))
    MAT['warehouse'] = facade_material('Warehouse', (0.27, 0.11, 0.07), (0.22, 0.08, 0.05), (0.35, 0.33, 0.3),
                                       (0.1, 0.12, 0.11), bay=4.2, storey=3.8, win=(0.35, 0.65, 0.3, 0.75), shop=False)
    MAT['shed'] = facade_material('Shed', (0.3, 0.26, 0.2), (0.2, 0.17, 0.13), (0, 0, 0), (0.12, 0.1, 0.08),
                                  bay=5.5, storey=4.5, wood=True, win=(0.4, 0.6, 0.35, 0.7), shop=False, rough=0.9)
    MAT['house'] = facade_material('Clapboard', (0.3, 0.32, 0.28), (0.24, 0.26, 0.22), (0, 0, 0), (0.18, 0.2, 0.18),
                                   bay=2.6, storey=3.1, wood=True, win=(0.32, 0.68, 0.25, 0.75), shop=False, rough=0.8)
    MAT['roof'] = simple_mat('RoofTar', (0.07, 0.07, 0.075), rough=0.9, noise_amt=0.3)
    MAT['slate'] = simple_mat('Slate', (0.12, 0.13, 0.15), rough=0.7, noise_amt=0.3)
    MAT['cornice'] = simple_mat('Cornice', (0.4, 0.37, 0.33), rough=0.7)
    MAT['tank'] = tank_material()
    MAT['concrete'] = simple_mat('Concrete', (0.42, 0.41, 0.39), rough=0.85, noise_amt=0.25, noise_scale=1.5)
    MAT['molasses'] = molasses_material()
    MAT['water'] = water_material()
    MAT['el'] = simple_mat('ElSteel', (0.07, 0.09, 0.075), rough=0.55, metal=0.4, noise_amt=0.35, noise_scale=0.8)
    MAT['iron'] = simple_mat('Iron', (0.05, 0.05, 0.05), rough=0.45, metal=0.7)
    MAT['wood'] = simple_mat('Wood', (0.34, 0.22, 0.12), rough=0.75, noise_amt=0.4, noise_scale=8.0, bump=0.3)
    MAT['wood_dark'] = simple_mat('WoodDark', (0.16, 0.1, 0.06), rough=0.8, noise_amt=0.4, noise_scale=8.0, bump=0.3)
    MAT['truck'] = simple_mat('TruckPaint', (0.06, 0.13, 0.09), rough=0.35, metal=0.2)
    MAT['coat'] = simple_mat('WoolCoat', (0.07, 0.065, 0.07), rough=0.95, noise_amt=0.2, noise_scale=40.0)
    MAT['coat2'] = simple_mat('WoolCoatBrown', (0.16, 0.11, 0.08), rough=0.95, noise_amt=0.2, noise_scale=40.0)
    MAT['skin'] = simple_mat('Skin', (0.55, 0.38, 0.28), rough=0.55, noise_amt=0.05)
    MAT['hat'] = simple_mat('Felt', (0.03, 0.03, 0.03), rough=0.8)
    MAT['paper'] = simple_mat('Paper', (0.8, 0.78, 0.7), rough=0.9, noise_amt=0.05)
    MAT['lantern'] = simple_mat('Lantern', (0.9, 0.8, 0.6), rough=0.2, emission=(1.0, 0.72, 0.38), emit_env='night',
                                emit_strength=30.0)
    MAT['thermo_board'] = simple_mat('ThermoBoard', (0.75, 0.72, 0.64), rough=0.6, noise_amt=0.1)
    MAT['mercury'] = simple_mat('ThermoRed', (0.6, 0.02, 0.02), rough=0.2, emission=(1, 0.05, 0.02), emit_strength=0.6)
    MAT['ink'] = simple_mat('Ink', (0.02, 0.02, 0.02), rough=0.5)
    MAT['glass'] = glass_mat('Glass')
    MAT['puddle'] = glass_mat('WaterTest', (0.7, 0.85, 0.95))
    MAT['wisp'] = wisp_material()
    MAT['ship'] = simple_mat('ShipHull', (0.06, 0.06, 0.065), rough=0.6)
    MAT['distant'] = simple_mat('Distant', (0.2, 0.19, 0.18), rough=0.9)


# ----------------------------------------------------------------------------
# World: sky, sun, moon, mist; compositing
# ----------------------------------------------------------------------------
SKY = {}


def build_world(sc):
    w = bpy.data.worlds.new('Sky')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_disc = False
    sky.altitude = 30
    sky.air_density = 1.0
    sky.dust_density = 0.9
    bg = nt.nodes.new('ShaderNodeBackground')
    lk(nt, sky.outputs[0], bg.inputs['Color'])
    lk(nt, bg.outputs[0], out.inputs['Surface'])
    SKY['node'], SKY['bg'] = sky, bg
    w.mist_settings.start = 25
    w.mist_settings.depth = 900
    w.mist_settings.falloff = 'QUADRATIC'
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.angle = math.radians(0.8)
    so = bpy.data.objects.new('Sun', sun)
    coll('Lights').objects.link(so)
    moon = bpy.data.lights.new('Moon', 'SUN')
    moon.angle = math.radians(2.0)
    moon.color = (0.55, 0.68, 1.0)
    mo = bpy.data.objects.new('Moon', moon)
    mo.rotation_euler = (math.radians(50), 0, math.radians(140))
    coll('Lights').objects.link(mo)
    SKY['sun'], SKY['moon'] = so, mo


def light_key(f, elev, azim, sun_strength, sky_strength, moon, sun_color=(1.0, 0.93, 0.84), exposure=0.0,
              fog=0.5):
    sky, bg, so, mo = SKY['node'], SKY['bg'], SKY['sun'], SKY['moon']
    sky.sun_elevation = math.radians(max(elev, -4))
    sky.sun_rotation = math.radians(azim)
    sky.keyframe_insert('sun_elevation', frame=f)
    sky.keyframe_insert('sun_rotation', frame=f)
    bg.inputs['Strength'].default_value = sky_strength
    bg.inputs['Strength'].keyframe_insert('default_value', frame=f)
    so.rotation_euler = (math.radians(90 - elev), 0, math.radians(azim + 90))
    so.keyframe_insert('rotation_euler', frame=f)
    so.data.energy = sun_strength
    so.data.keyframe_insert('energy', frame=f)
    so.data.color = sun_color
    so.data.keyframe_insert('color', frame=f)
    mo.data.energy = moon
    mo.data.keyframe_insert('energy', frame=f)
    sc = bpy.context.scene
    sc.view_settings.exposure = exposure
    sc.view_settings.keyframe_insert('exposure', frame=f)
    fogn = sc.node_tree.nodes.get('FogMix')
    if fogn:
        fogn.inputs[0].default_value = fog
        fogn.inputs[0].keyframe_insert('default_value', frame=f)


def build_compositor(sc):
    sc.use_nodes = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new('CompositorNodeRLayers')
    ramp = nt.nodes.new('CompositorNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].position = 1.0
    nt.links.new(rl.outputs['Mist'], ramp.inputs[0])
    fogmul = nt.nodes.new('CompositorNodeMath')
    fogmul.name = 'FogMix'
    fogmul.operation = 'MULTIPLY'
    fogmul.inputs[0].default_value = 0.5
    nt.links.new(ramp.outputs[0], fogmul.inputs[1])
    mix = nt.nodes.new('CompositorNodeMixRGB')
    mix.blend_type = 'MIX'
    mix.inputs[2].default_value = (0.5, 0.56, 0.64, 1)
    mix.name = 'FogColor'
    nt.links.new(fogmul.outputs[0], mix.inputs[0])
    nt.links.new(rl.outputs['Image'], mix.inputs[1])
    glare = nt.nodes.new('CompositorNodeGlare')
    glare.glare_type = 'FOG_GLOW'
    glare.quality = 'HIGH'
    glare.threshold = 1.2
    glare.size = 7
    glare.mix = -0.7
    nt.links.new(mix.outputs[0], glare.inputs[0])
    comp = nt.nodes.new('CompositorNodeComposite')
    nt.links.new(glare.outputs[0], comp.inputs[0])


# ----------------------------------------------------------------------------
# Ground, harbour and the city
# ----------------------------------------------------------------------------
def plane(bm, x0, y0, x1, y1, z=0.0):
    vs = [bm.verts.new((x0, y0, z)), bm.verts.new((x1, y0, z)), bm.verts.new((x1, y1, z)), bm.verts.new((x0, y1, z))]
    bm.faces.new(vs)


def build_ground():
    x0, x1, y0, y1 = L.DOMAIN
    ext = 320
    bm = bmesh.new()
    plane(bm, -ext, L.STREET_Y0, ext, L.STREET_Y1, 0.0)
    for sx0, sx1 in L.SIDE_STREETS:
        plane(bm, sx0, L.STREET_Y1, sx1, 200, 0.0)
    plane(bm, -ext, L.STREET_Y1 + 22, ext, L.STREET_Y1 + 26, 0.0)     # back alley
    obj_from_bm('Street', bm, MAT['cobble'])
    bm = bmesh.new()
    plane(bm, -ext, L.STREET_Y1, ext, L.STREET_Y1 + 2.0, 0.03)
    plane(bm, -ext, L.STREET_Y0 - 2.6, ext, L.STREET_Y0, 0.03)
    obj_from_bm('Sidewalks', bm, MAT['sidewalk'])
    bm = bmesh.new()
    plane(bm, -ext, L.SEAWALL_Y, ext, L.STREET_Y0 - 2.6, 0.0)
    plane(bm, -ext, L.STREET_Y1 + 2, ext, 220, -0.02)                 # under north blocks
    obj_from_bm('Yard', bm, MAT['yard'])
    bm = bmesh.new()
    add_box(bm, -ext, L.SEAWALL_Y - 1.2, -4.0, ext, L.SEAWALL_Y, 0.05)
    obj_from_bm('Seawall', bm, MAT['seawall'])
    bm = bmesh.new()
    plane(bm, -1500, -1800, 1500, L.SEAWALL_Y - 0.5, -1.3)
    obj_from_bm('Harbour', bm, MAT['water'])
    # tank's concrete base
    bm = bmesh.new()
    add_cyl(bm, L.TANK_R + 0.6, L.TANK_R + 0.6, 0.25, seg=64, matrix=Matrix.Translation((L.TANK_X, L.TANK_Y, 0.125)))
    obj_from_bm('TankBase', bm, MAT['concrete'], collection='Tank')
    # piers
    bm = bmesh.new()
    for px in (-52.0, 78.0, -110.0):
        add_box(bm, px - 5, L.SEAWALL_Y - 70, -0.25, px + 5, L.SEAWALL_Y, 0.05)
        for k in range(14):
            for sx in (-4.5, 4.5):
                add_cyl(bm, 0.22, 0.22, 4.0, seg=8,
                        matrix=Matrix.Translation((px + sx, L.SEAWALL_Y - 3 - k * 5, -2.0)))
    obj_from_bm('Piers', bm, MAT['wood_dark'])


def building_mesh(b, rng):
    bm = bmesh.new()
    add_box(bm, b['x0'], b['y0'], 0.0, b['x1'], b['y1'], b['height'])
    return bm


def build_city():
    rng = random.Random(42)
    blds = L.buildings()
    # extra background blocks outside the simulated area (and Copp's Hill rising behind)
    extra = []
    for x0, x1 in [(-320, -132), (132, 320)]:
        x = x0
        while x < x1:
            w = rng.uniform(9, 15)
            extra.append(dict(x0=x, x1=x + w, y0=L.STREET_Y1 + 2, y1=L.STREET_Y1 + 2 + rng.uniform(14, 20),
                              height=rng.randint(3, 6) * 3.4 + 0.6, kind=rng.choice(['brick', 'brick_dark', 'stone'])))
            x += w
    for row in range(3):
        y = L.STREET_Y1 + 52 + row * 28
        x = -320
        while x < 320:
            w = rng.uniform(9, 16)
            if not any(a - 2 < x + w / 2 < b_ + 2 for a, b_ in L.SIDE_STREETS):
                extra.append(dict(x0=x, x1=x + w, y0=y, y1=y + rng.uniform(16, 24), base=row * 2.5,
                                  height=rng.randint(4, 7) * 3.4 + 0.6, kind=rng.choice(['brick', 'brick_dark', 'stone'])))
            x += w + 0.5
    for x0, x1 in [(-320, -132), (124, 320)]:
        extra.append(dict(x0=x0, x1=x1, y0=-41, y1=-8, height=10.5, kind='warehouse'))
    by_kind = {}
    for b in blds + extra:
        by_kind.setdefault(b['kind'], []).append(b)
    for kind, lst in by_kind.items():
        bm = bmesh.new()
        trim = bmesh.new()
        roofs = bmesh.new()
        for b in lst:
            z0 = b.get('base', 0.0)
            add_box(bm, b['x0'], b['y0'], z0 - 0.05, b['x1'], b['y1'], z0 + b['height'])
            if kind in ('shed',):
                # gabled roof
                gx0, gx1 = b['x0'], b['x1']
                ym = (b['y0'] + b['y1']) / 2
                h0 = z0 + b['height']
                vs = [roofs.verts.new(p) for p in [(gx0 - .4, b['y0'] - .6, h0), (gx1 + .4, b['y0'] - .6, h0),
                                                   (gx1 + .4, ym, h0 + 4.5), (gx0 - .4, ym, h0 + 4.5),
                                                   (gx0 - .4, b['y1'] + .6, h0), (gx1 + .4, b['y1'] + .6, h0)]]
                roofs.faces.new([vs[0], vs[1], vs[2], vs[3]])
                roofs.faces.new([vs[3], vs[2], vs[5], vs[4]])
                tri = [bm.verts.new(p) for p in [(gx0, b['y0'], h0), (gx0, ym, h0 + 4.4), (gx0, b['y1'], h0)]]
                bm.faces.new(tri)
                tri = [bm.verts.new(p) for p in [(gx1, b['y1'], h0), (gx1, ym, h0 + 4.4), (gx1, b['y0'], h0)]]
                bm.faces.new(tri)
            else:
                top = z0 + b['height']
                add_box(trim, b['x0'] - 0.25, b['y0'] - 0.35, top - 0.55, b['x1'] + 0.25, b['y1'] + 0.35, top)
                add_box(trim, b['x0'] - 0.05, b['y0'] - 0.12, z0 + 3.35, b['x1'] + 0.05, b['y1'] + 0.12, z0 + 3.6)
                add_box(roofs, b['x0'] + 0.2, b['y0'] + 0.2, top - 0.1, b['x1'] - 0.2, b['y1'] - 0.2, top + 0.05)
                for _ in range(rng.randint(1, 3)):
                    cx = rng.uniform(b['x0'] + 1, b['x1'] - 1.5)
                    cy = rng.uniform(b['y0'] + 2, b['y1'] - 2)
                    add_box(trim, cx, cy, top, cx + 0.8, cy + 1.2, top + rng.uniform(1.2, 2.4))
        obj_from_bm('Buildings_' + kind, bm, MAT[kind], collection='City')
        if len(trim.verts):
            obj_from_bm('Trim_' + kind, trim, MAT['cornice'], collection='City')
        else:
            trim.free()
        obj_from_bm('Roofs_' + kind, roofs, MAT['slate' if kind == 'shed' else 'roof'], collection='City')
    # Old North Church steeple on the hill behind (a North End landmark)
    bm = bmesh.new()
    sx, sy = -150.0, 150.0
    add_box(bm, sx - 6, sy - 6, 6, sx + 6, sy + 6, 34)
    add_box(bm, sx - 4.2, sy - 4.2, 34, sx + 4.2, sy + 4.2, 46)
    add_box(bm, sx - 3.2, sy - 3.2, 46, sx + 3.2, sy + 3.2, 54)
    add_cyl(bm, 3.0, 0.15, 26, seg=8, matrix=Matrix.Translation((sx, sy, 67)))
    obj_from_bm('Steeple', bm, MAT['brick_dark'], collection='City')
    # distant shoreline across the harbour
    bm = bmesh.new()
    for i in range(40):
        x = -900 + i * 46 + rng.uniform(-10, 10)
        add_box(bm, x, -760, -1.3, x + rng.uniform(25, 45), -720, rng.uniform(8, 30))
    obj_from_bm('FarShore', bm, MAT['distant'], collection='City')
    # a moored schooner
    build_ship(Vector((-30.0, L.SEAWALL_Y - 40, -1.3)), 0.15)


def build_ship(pos, yaw):
    bm = bmesh.new()
    add_box(bm, -16, -3.2, -1.5, 16, 3.2, 2.2)
    for v in bm.verts:
        t = abs(v.co.x) / 16
        v.co.y *= 1 - 0.75 * t ** 3
        if v.co.z < 0:
            v.co.y *= 0.6
        if v.co.x > 10:
            v.co.z += (v.co.x - 10) * 0.12
    obj = obj_from_bm('ShipHull', bm, MAT['ship'], collection='City', loc=pos)
    obj.rotation_euler.z = yaw
    bm = bmesh.new()
    for mx_ in (-6, 5):
        add_cyl(bm, 0.25, 0.14, 26, seg=8, matrix=Matrix.Translation((mx_, 0, 15)))
        add_cyl(bm, 0.1, 0.1, 10, seg=6, matrix=Matrix.Translation((mx_ + 4, 0, 6)) @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
    add_box(bm, -12, -2, 2.2, -4, 2, 4)
    m = obj_from_bm('ShipRig', bm, MAT['wood_dark'], collection='City')
    m.parent = obj


# ----------------------------------------------------------------------------
# Elevated railway (Atlantic Avenue El over Commercial Street)
# ----------------------------------------------------------------------------
EL = {}


def build_el():
    near = bmesh.new()
    far = bmesh.new()
    xs = []
    x = L.DOMAIN[0] - 200 + 4
    while x < L.DOMAIN[1] + 200:
        xs.append(x)
        x += L.EL_COL_SPACING
    z_g0, z_g1 = 6.9, 7.9
    for x in xs:
        target = near if abs(x - L.TANK_X) < 32 else far
        for y in (L.EL_Y - L.EL_COL_DY, L.EL_Y + L.EL_COL_DY):
            add_box(target, x - 0.25, y - 0.25, 0.0, x + 0.25, y + 0.25, z_g0)
            add_box(target, x - 0.45, y - 0.45, 0.0, x + 0.45, y + 0.45, 0.35)
            add_box(target, x - 0.4, y - 0.4, z_g0 - 0.8, x + 0.4, y + 0.4, z_g0)   # knee brace block
        add_box(target, x - 0.3, L.EL_Y - L.EL_COL_DY - 0.6, z_g0, x + 0.3, L.EL_Y + L.EL_COL_DY + 0.6, z_g1)
    # longitudinal girders and deck, split into segments so the near part can bend
    seg = 2.0
    x = xs[0]
    while x < xs[-1]:
        target = near if abs(x + seg / 2 - L.TANK_X) < 32 else far
        for y in (L.EL_Y - L.EL_COL_DY, L.EL_Y + L.EL_COL_DY, L.EL_Y - 1.5, L.EL_Y + 1.5):
            add_box(target, x, y - 0.22, z_g0, x + seg + 0.01, y + 0.22, z_g1)
        add_box(target, x, L.EL_Y - 3.0, z_g1, x + seg + 0.01, L.EL_Y + 3.0, z_g1 + 0.18)    # ties
        for y in (L.EL_Y - 2.2, L.EL_Y - 0.8, L.EL_Y + 0.8, L.EL_Y + 2.2):
            add_box(target, x, y - 0.05, z_g1 + 0.18, x + seg + 0.01, y + 0.05, z_g1 + 0.32)  # rails
        x += seg
    ofar = obj_from_bm('El_far', far, MAT['el'], collection='El')
    onear = obj_from_bm('El_near', near, MAT['el'], collection='El')
    # bend shape key driven by the simulated momentum hitting the columns
    onear.shape_key_add(name='Basis')
    sk = onear.shape_key_add(name='Bent')
    for i, v in enumerate(onear.data.vertices):
        x, y, z = v.co
        g = math.exp(-((x - L.TANK_X - 2) / 13.0) ** 2)
        lean = g * 1.9 * (z / 8.0) ** 1.3
        sag = g * 1.1 * (1.0 if z > 6.5 else z / 6.5 * 0.2)
        twist = g * 0.35 * (y - L.EL_Y) / 4.2 * (z / 8.0)
        sk.data[i].co = (x, y + lean, z - sag - twist)
    EL['near'] = onear


# ----------------------------------------------------------------------------
# The tank: 16 riveted panels that can burst open, a roof, rivets
# ----------------------------------------------------------------------------
TANK = {'panels': [], 'pop': []}
N_PANELS = 16
POP_SEAM_PANEL = 4            # left edge of panel 4 is the seam at 90° (facing the street)
POP_Z = (0.7, 5.4)


def panel_angles(k):
    a0 = k * 2 * math.pi / N_PANELS
    return a0, a0 + 2 * math.pi / N_PANELS


def build_tank():
    rng = random.Random(5)
    rivet_bm = bmesh.new()
    add_sphere(rivet_bm, 0.036, u=8, v=5)
    rivet_me = bpy.data.meshes.new('rivet')
    rivet_bm.to_mesh(rivet_me)
    rivet_bm.free()
    rivet_me.materials.append(MAT['tank'])
    base_z = 0.25
    hgt = L.TANK_H - base_z
    for k in range(N_PANELS):
        a0, a1 = panel_angles(k)
        am = (a0 + a1) / 2
        origin = Vector((L.TANK_X + L.TANK_R * math.cos(am), L.TANK_Y + L.TANK_R * math.sin(am), base_z))
        X = Vector((-math.sin(am), math.cos(am), 0))
        Yin = Vector((-math.cos(am), -math.sin(am), 0))
        bm = bmesh.new()
        segs, rows = 8, 6
        grid = []
        for r in range(rows + 1):
            z = hgt * r / rows
            row = []
            for s in range(segs + 1):
                a = a0 + (a1 - a0) * s / segs
                P = Vector((L.TANK_X + L.TANK_R * math.cos(a), L.TANK_Y + L.TANK_R * math.sin(a), base_z + z))
                d = P - origin
                row.append(bm.verts.new((d.dot(X), d.dot(Yin), z)))
            grid.append(row)
        for r in range(rows):
            for s in range(segs):
                bm.faces.new([grid[r][s], grid[r][s + 1], grid[r + 1][s + 1], grid[r + 1][s]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        ob = obj_from_bm(f'TankPanel_{k:02d}', bm, MAT['tank'], collection='Tank', smooth=True)
        ob.location = origin
        ob.rotation_mode = 'XYZ'
        ob.rotation_euler = (0, 0, am + math.pi / 2)
        sol = ob.modifiers.new('thick', 'SOLIDIFY')
        sol.thickness = 0.04
        sol.offset = 0.0
        # rivet positions (local coords), instanced on vertices
        pts = []
        for seam in range(1, 6):
            z = hgt * seam / 6 - 0.0
            for dz in (-0.06, 0.06):
                n = 24
                for s in range(n):
                    a = a0 + (a1 - a0) * (s + 0.5) / n
                    P = Vector((L.TANK_X + (L.TANK_R + 0.032) * math.cos(a), L.TANK_Y + (L.TANK_R + 0.032) * math.sin(a), base_z + z + dz))
                    d = P - origin
                    pts.append((d.dot(X), d.dot(Yin), z + dz))
        for da in (0.004, 0.012):
            a = a0 + da
            nz = int(hgt / 0.2)
            for s in range(nz):
                z = (s + 0.5) * hgt / nz
                if k == POP_SEAM_PANEL and POP_Z[0] - 0.1 < z < POP_Z[1] + 0.1 and da < 0.01:
                    continue
                P = Vector((L.TANK_X + (L.TANK_R + 0.032) * math.cos(a), L.TANK_Y + (L.TANK_R + 0.032) * math.sin(a), base_z + z))
                d = P - origin
                pts.append((d.dot(X), d.dot(Yin), z))
        rme = bpy.data.meshes.new(f'rivetpts_{k}')
        rme.from_pydata(pts, [], [])
        rob = bpy.data.objects.new(f'Rivets_{k:02d}', rme)
        coll('Tank').objects.link(rob)
        rob.parent = ob
        rob.instance_type = 'VERTS'
        tmpl = bpy.data.objects.new(f'RivetT_{k:02d}', rivet_me)
        coll('Tank').objects.link(tmpl)
        tmpl.parent = rob
        TANK['panels'].append(dict(obj=ob, rivets=rob, tmpl=tmpl, am=am, origin=origin.copy(),
                                   open=rng.uniform(0.9, 1.45) if math.sin(am) > -0.2 else rng.uniform(0.5, 1.0),
                                   delay=rng.uniform(0.0, 0.18) + (0.0 if k in (3, 4) else 0.08),
                                   slide=rng.uniform(0.8, 3.0), twist=rng.uniform(-0.25, 0.25)))
    # roof
    bm = bmesh.new()
    add_cyl(bm, L.TANK_R + 0.15, 0.6, 1.8, seg=64, matrix=Matrix.Translation((0, 0, 0.9)))
    add_cyl(bm, 0.8, 0.8, 0.6, seg=16, matrix=Matrix.Translation((0, 0, 2.0)))
    roof = obj_from_bm('TankRoof', bm, MAT['tank'], collection='Tank', smooth=True)
    roof.location = (L.TANK_X, L.TANK_Y, L.TANK_H)
    TANK['roof'] = roof
    # the rivets that pop on the street-facing seam
    a = panel_angles(POP_SEAM_PANEL)[0] + 0.004
    nz = int(hgt / 0.2)
    pop_mesh = bpy.data.meshes.new('rivet_pop')
    bm = bmesh.new()
    add_sphere(bm, 0.032, u=10, v=6)
    add_cyl(bm, 0.012, 0.012, 0.06, seg=6, matrix=Matrix.Translation((0, 0, -0.03)) @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
    bm.to_mesh(pop_mesh)
    bm.free()
    pop_mesh.materials.append(MAT['tank'])
    for s in range(nz):
        z = (s + 0.5) * hgt / nz
        if not (POP_Z[0] - 0.1 < z < POP_Z[1] + 0.1):
            continue
        P = Vector((L.TANK_X + (L.TANK_R + 0.032) * math.cos(a), L.TANK_Y + (L.TANK_R + 0.032) * math.sin(a), base_z + z))
        ob = bpy.data.objects.new(f'PopRivet_{s:02d}', pop_mesh)
        ob.location = P
        coll('Tank').objects.link(ob)
        TANK['pop'].append(dict(obj=ob, p0=P.copy(), z=z, normal=Vector((math.cos(a), math.sin(a), 0)),
                                rng=random.Random(s)))
    TANK['pop'].sort(key=lambda d: d['z'])
    # spurts and the opening crack on that seam
    bm = bmesh.new()
    add_cyl(bm, 0.018, 0.05, 1.0, seg=10, matrix=Matrix.Translation((0, 0, 0.5)))
    sp_me = bpy.data.meshes.new('spurt')
    bm.to_mesh(sp_me)
    bm.free()
    sp_me.materials.append(MAT['molasses'])
    sp_me.shade_smooth()
    TANK['spurts'] = []
    for d in TANK['pop'][::2]:
        ob = bpy.data.objects.new('Spurt', sp_me)
        coll('Tank').objects.link(ob)
        ob.location = d['p0']
        ob.rotation_mode = 'QUATERNION'
        TANK['spurts'].append((ob, d))
    bm = bmesh.new()
    add_box(bm, -0.025, -0.02, 0.0, 0.025, 0.02, 1.0)
    crack = obj_from_bm('Crack', bm, MAT['molasses'], collection='Tank')
    crack.location = TANK['pop'][0]['p0'] + TANK['pop'][0]['normal'] * 0.005
    TANK['crack'] = crack
    # leak drips on the street-facing wall
    bm = bmesh.new()
    add_sphere(bm, 0.07, u=10, v=8)
    for v in bm.verts:
        if v.co.z > 0:
            v.co.z *= 3.5
    dr_me = bpy.data.meshes.new('drip')
    bm.to_mesh(dr_me)
    bm.free()
    dr_me.materials.append(MAT['molasses'])
    dr_me.shade_smooth()
    TANK['drips'] = []
    drng = random.Random(11)
    for i in range(14):
        a = math.radians(drng.uniform(138, 166))
        z0 = L.TANK_H / 6 * drng.choice([1, 2, 2, 3]) + 0.25 - 0.1
        ob = bpy.data.objects.new('Drip', dr_me)
        coll('Tank').objects.link(ob)
        TANK['drips'].append(dict(obj=ob, a=a, z0=z0, period=drng.uniform(1.0, 2.2), phase=drng.random()))
    # the 1915 water test: six inches of water in the empty tank
    bm = bmesh.new()
    add_cyl(bm, L.TANK_R - 0.06, L.TANK_R - 0.06, 0.15, seg=64, matrix=Matrix.Translation((L.TANK_X, L.TANK_Y, 0.25 + 0.075)))
    TANK['puddle'] = obj_from_bm('WaterTest', bm, MAT['puddle'], collection='Tank')


def update_tank(st, tv):
    """Panels burst outward as the simulated collapse begins (st = seconds after failure)."""
    for p in TANK['panels']:
        ob = p['obj']
        if st is None or st <= p['delay']:
            ob.location = p['origin']
            ob.rotation_euler = (0, 0, p['am'] + math.pi / 2)
            continue
        u = min(1.0, (st - p['delay']) / 0.9)
        e = 1 - (1 - u) ** 3
        ang = p['open'] * e
        out = Vector((math.cos(p['am']), math.sin(p['am']), 0))
        ob.location = p['origin'] + out * (p['slide'] * e)
        ob.rotation_euler = (ang, 0, p['am'] + math.pi / 2 + p['twist'] * e)
    roof = TANK['roof']
    if st is None or st <= 0:
        roof.location = (L.TANK_X, L.TANK_Y, L.TANK_H)
        roof.rotation_euler = (0, 0, 0)
    else:
        u = min(1.0, st / 0.75)
        roof.location = (L.TANK_X + 2.0 * u, L.TANK_Y - 2.5 * u, L.TANK_H - (L.TANK_H + 1.5) * (u ** 1.5))
        roof.rotation_euler = (1.1 * u, -0.5 * u, 0.3 * u)


def update_rivet_pops(tv):
    s = SHOT['rivets']
    t_first = ls('L08') + 0.55
    n = len(TANK['pop'])
    interval = (SHOT['burst']['t0'] + 0.1 - t_first) / n
    for i, d in enumerate(TANK['pop']):
        tp = t_first + i * interval * (1.0 - 0.35 * i / n)
        ob = d['obj']
        dt = tv - tp
        if dt <= 0:
            ob.location = d['p0']
            ob.rotation_euler = (0, 0, math.atan2(d['normal'].y, d['normal'].x))
            ob.scale = (1, 1, 1)
            continue
        r = d['rng']
        side = Vector((-d['normal'].y, d['normal'].x, 0))
        vel = d['normal'] * (16 + (i % 5) * 2.0) + side * ((i * 7 % 5) - 2) * 1.6 + Vector((0, 0, 2.5 + (i % 3)))
        pos = d['p0'] + vel * dt + Vector((0, 0, -4.9 * dt * dt))
        ob.location = pos
        ob.rotation_euler = (dt * 40 + i, dt * 25, math.atan2(d['normal'].y, d['normal'].x))
        ob.scale = (0, 0, 0) if dt > 0.6 else (1, 1, 1)
    # spurts grow out of the holes after their rivets pop
    for ob, d in TANK['spurts']:
        i = TANK['pop'].index(d)
        tp = t_first + i * interval * (1.0 - 0.35 * i / n)
        dt = tv - tp
        if dt <= 0 or tv > SHOT['burst']['t0'] + 0.05:
            ob.scale = (0, 0, 0)
            continue
        ln = min(1.8, dt * 5.0)
        ob.scale = (1 + dt, 1 + dt, ln)
        dirv = (d['normal'] + Vector((0, 0, -0.25 - dt * 0.8))).normalized()
        ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(dirv)
        ob.location = d['p0']
    # the crack climbing the seam
    cr = TANK['crack']
    t0c = t_first
    u = min(1.0, max(0.0, (tv - t0c) / max(SHOT['burst']['t0'] - t0c, 0.1)))
    if tv > SHOT['burst']['t0'] + 0.05:
        u = 0
    cr.scale = (1 + u * 3, 1, max(0.001, (POP_Z[1] - POP_Z[0] + 0.4) * u))


def rivet_pop_times():
    t_first = ls('L08') + 0.55
    n = len(TANK['pop'])
    interval = (SHOT['burst']['t0'] + 0.1 - t_first) / n
    return [t_first + i * interval * (1.0 - 0.35 * i / n) for i in range(n)]


def update_drips(tv):
    for d in TANK['drips']:
        ph = ((tv / d['period']) + d['phase']) % 1.0
        z = d['z0'] - 2.2 * ph ** 1.7
        a = d['a']
        r = L.TANK_R + 0.03
        d['obj'].location = (L.TANK_X + r * math.cos(a), L.TANK_Y + r * math.sin(a), z)
        s = 0.6 + 0.6 * min(1.0, ph * 3)
        d['obj'].scale = (s, s, s * (1 + ph))


# ----------------------------------------------------------------------------
# Molasses surface driven by the shallow-water simulation
# ----------------------------------------------------------------------------
SIM = {}


def load_sim():
    d = np.load(os.path.join(ROOT, 'build', 'flood_sim.npz'))
    SIM.update({k: d[k] for k in d.files})
    SIM['x0'], SIM['y0'] = float(SIM['x0']), float(SIM['y0'])
    SIM['nx'], SIM['ny'] = int(SIM['nx']), int(SIM['ny'])


def build_molasses():
    nx, ny = SIM['nx'], SIM['ny']
    xs = SIM['x0'] + (np.arange(nx) + 0.5) * float(SIM['dx'])
    ys = SIM['y0'] + (np.arange(ny) + 0.5) * float(SIM['dx'])
    X, Y = np.meshgrid(xs, ys)
    verts = np.stack([X.ravel(), Y.ravel(), np.full(X.size, -0.4)], 1)
    idx = np.arange(nx * ny).reshape(ny, nx)
    faces = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    me = bpy.data.meshes.new('Molasses')
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.update()
    me.shade_smooth()
    me.attributes.new('depth', 'FLOAT', 'POINT')
    me.attributes.new('speed', 'FLOAT', 'POINT')
    me.materials.append(MAT['molasses'])
    ob = bpy.data.objects.new('Molasses', me)
    coll('Flood').objects.link(ob)
    sub = ob.modifiers.new('smooth', 'SUBSURF')
    sub.levels, sub.render_levels = 0, 1
    SIM['obj'] = ob
    SIM['X'], SIM['Y'] = X, Y
    SIM['harbour'] = Y < L.SEAWALL_Y
    SIM['in_tank'] = (X - L.TANK_X) ** 2 + (Y - L.TANK_Y) ** 2 < L.TANK_R ** 2


def sim_fields(st):
    times = SIM['times']
    st = float(np.clip(st, times[0], times[-1]))
    k = int(np.searchsorted(times, st))
    k = min(max(k, 1), len(times) - 1)
    w = (st - times[k - 1]) / max(times[k] - times[k - 1], 1e-6)
    h = SIM['h'][k - 1].astype(np.float32) * (1 - w) + SIM['h'][k].astype(np.float32) * w
    s = SIM['speed'][k - 1].astype(np.float32) * (1 - w) + SIM['speed'][k].astype(np.float32) * w
    return h, s, k, w


WAVE_SHOTS = {'hook': 1.5, 'burst': 1.25, 'race': 1.5, 'house': 1.5, 'el': 1.5, 'rise': 1.25, 'end': 1.5}


def update_molasses(st, shot_name=''):
    if st is None:
        return
    h, s, _, _ = sim_fields(st)
    hb = SIM['harbour']
    wet = h > 0.012
    # Visual treatment (documented in the README): the simulated depth is steepened at the thin
    # leading edge and, in the wave shots, exaggerated to match eyewitness estimates of the wave.
    gain = WAVE_SHOTS.get(shot_name, 1.0)
    href = 2.5
    hv = np.where(h < href, href * np.power(np.maximum(h, 0) / href, 0.55), h)
    hv = hv + (gain - 1.0) * np.minimum(hv, 3.0)
    hv = np.where(SIM['in_tank'], np.maximum(hv, h), hv)
    z = np.where(wet, hv + 0.02, -0.45)
    z = np.where(hb, np.where(wet, -1.27 + np.minimum(h, 1.5) * 0.45, -2.2), z)
    me = SIM['obj'].data
    co = np.stack([SIM['X'].ravel(), SIM['Y'].ravel(), z.ravel()], 1).astype(np.float32)
    me.vertices.foreach_set('co', co.ravel())
    me.attributes['depth'].data.foreach_set('value', h.ravel())
    me.attributes['speed'].data.foreach_set('value', s.ravel())
    me.update()


def interp_rows(arr, st):
    times = SIM['times']
    st = float(np.clip(st, times[0], times[-1]))
    k = int(np.searchsorted(times, st))
    k = min(max(k, 1), len(times) - 1)
    w = (st - times[k - 1]) / max(times[k] - times[k - 1], 1e-6)
    return arr[k - 1] * (1 - w) + arr[k] * w


# ----------------------------------------------------------------------------
# Debris, the pushed house, vehicles
# ----------------------------------------------------------------------------
DEB = []
HOUSE = {}


def make_barrel(name):
    bm = bmesh.new()
    add_cyl(bm, 0.3, 0.3, 0.9, seg=16, matrix=Matrix.Translation((0, 0, 0.45)))
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.5], cuts=4)
    for v in bm.verts:
        r = 1.0 + 0.14 * math.sin(math.pi * v.co.z / 0.9)
        v.co.x *= r
        v.co.y *= r
    ob = obj_from_bm(name, bm, MAT['wood'], collection='Debris', smooth=True)
    bm2 = bmesh.new()
    for zz in (0.12, 0.78):
        add_cyl(bm2, 0.34 if zz < 0.5 else 0.34, 0.34, 0.05, seg=16, matrix=Matrix.Translation((0, 0, zz)))
    hoops = obj_from_bm(name + '_hoops', bm2, MAT['iron'], collection='Debris')
    hoops.parent = ob
    return ob


def make_crate(name):
    bm = bmesh.new()
    add_box(bm, -0.55, -0.45, 0, 0.55, 0.45, 0.8)
    return obj_from_bm(name, bm, MAT['wood_dark'], collection='Debris')


def make_wheels(parent, xs, ys, r, width=0.12):
    bm = bmesh.new()
    for x in xs:
        for y in ys:
            add_cyl(bm, r, r, width, seg=18, matrix=Matrix.Translation((x, y, r)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    w = obj_from_bm(parent.name + '_wheels', bm, MAT['iron'], collection='Debris')
    w.parent = parent


def make_wagon(name):
    bm = bmesh.new()
    add_box(bm, -1.6, -0.8, 0.8, 1.6, 0.8, 1.0)
    add_box(bm, -1.6, -0.8, 1.0, 1.6, -0.72, 1.5)
    add_box(bm, -1.6, 0.72, 1.0, 1.6, 0.8, 1.5)
    add_box(bm, 1.6, -0.5, 0.85, 3.6, -0.44, 0.92)
    add_box(bm, 1.6, 0.44, 0.85, 3.6, 0.5, 0.92)
    for i in range(3):
        add_box(bm, -1.2 + i * 0.9, -0.7, 1.0, -0.6 + i * 0.9, 0.7, 1.55)
    ob = obj_from_bm(name, bm, MAT['wood'], collection='Debris')
    make_wheels(ob, (-1.1, 1.1), (-0.9, 0.9), 0.55)
    return ob


def make_truck(name):
    bm = bmesh.new()
    add_box(bm, 1.2, -0.75, 0.7, 2.6, 0.75, 1.6)       # hood
    add_box(bm, 0.0, -0.95, 0.7, 1.2, 0.95, 2.5)       # cab
    add_box(bm, -3.2, -1.1, 0.75, 0.0, 1.1, 0.95)      # flatbed
    add_box(bm, -3.2, -1.1, 0.95, 0.0, -1.0, 1.5)
    add_box(bm, -3.2, 1.0, 0.95, 0.0, 1.1, 1.5)
    ob = obj_from_bm(name, bm, MAT['truck'], collection='Debris')
    make_wheels(ob, (-2.2, 1.9), (-0.95, 0.95), 0.5, 0.18)
    return ob


def build_debris():
    names = list(SIM['debris_names'])
    makers = dict(barrel=make_barrel, crate=make_crate, wagon=make_wagon, truck=make_truck)
    for i, (n, kind, x, y, yaw) in enumerate(L.DEBRIS):
        ob = makers[kind]('Debris_' + n)
        ob.rotation_mode = 'XYZ'
        DEB.append(dict(obj=ob, kind=kind, i=names.index(n)))
    # house east of the tank, shoved off its foundation
    H = L.PUSHED_HOUSE
    w, d = H['x1'] - H['x0'], H['y1'] - H['y0']
    bm = bmesh.new()
    add_box(bm, -w / 2, -d / 2, 0, w / 2, d / 2, H['height'])
    house = obj_from_bm('PushedHouse', bm, MAT['house'], collection='House')
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in [(-w / 2 - .4, -d / 2 - .5, H['height']), (w / 2 + .4, -d / 2 - .5, H['height']),
                                    (w / 2 + .4, 0, H['height'] + 4.0), (-w / 2 - .4, 0, H['height'] + 4.0),
                                    (-w / 2 - .4, d / 2 + .5, H['height']), (w / 2 + .4, d / 2 + .5, H['height'])]]
    bm.faces.new([vs[0], vs[1], vs[2], vs[3]])
    bm.faces.new([vs[3], vs[2], vs[5], vs[4]])
    roof = obj_from_bm('PushedHouseRoof', bm, MAT['slate'], collection='House')
    roof.parent = house
    bm = bmesh.new()
    for sx in (-1, 1):
        tri = [bm.verts.new(p) for p in [(sx * w / 2, -d / 2, H['height']), (sx * w / 2, 0, H['height'] + 3.9),
                                         (sx * w / 2, d / 2, H['height'])]]
        bm.faces.new(tri)
    gab = obj_from_bm('PushedHouseGables', bm, MAT['house'], collection='House')
    gab.parent = house
    bm = bmesh.new()
    add_box(bm, -w / 2 - 0.3, -d / 2 - 0.3, -0.1, w / 2 + 0.3, d / 2 + 0.3, 0.35)
    obj_from_bm('HouseFoundation', bm, MAT['concrete'], collection='House',
                loc=((H['x0'] + H['x1']) / 2, (H['y0'] + H['y1']) / 2, 0))
    house.rotation_mode = 'XYZ'
    HOUSE.update(obj=house, base=Vector(((H['x0'] + H['x1']) / 2, (H['y0'] + H['y1']) / 2, 0.3)))


def update_debris(st):
    D = SIM['debris']
    row = D[0] if st is None else interp_rows(D, st)
    for d in DEB:
        x, y, z, yaw, roll = row[d['i']]
        ob = d['obj']
        ob.location = (x, y, max(z, -6) + (0.0 if d['kind'] != 'barrel' else 0.0))
        if d['kind'] == 'barrel':
            ob.rotation_euler = (math.pi / 2 if st is not None and st > 0.8 else 0.0, roll, yaw)
            if st is not None and st > 0.8:
                ob.location = (x, y, max(z, -6) + 0.3)
        elif d['kind'] == 'crate':
            ob.rotation_euler = (math.sin(roll) * 0.25, math.cos(roll * 0.7) * 0.2, yaw)
        else:
            ob.rotation_euler = (math.sin(roll * 0.3) * 0.12, 0.0, yaw)
    hx = SIM['house']
    dx, dy, tilt = (0.0, 0.0, 0.0) if st is None else interp_rows(hx, st)
    ob = HOUSE['obj']
    ob.location = HOUSE['base'] + Vector((dx, dy, -0.25 * min(1, tilt / 0.1)))
    ob.rotation_euler = (tilt * 0.35, -tilt * 0.9, dx * 0.02)


def update_el(st):
    v = 0.0 if st is None else float(interp_rows(SIM['el_bend'], st))
    kb = EL['near'].data.shape_keys.key_blocks['Bent']
    kb.value = v


# ----------------------------------------------------------------------------
# People: simple procedural mannequins with articulated limbs
# ----------------------------------------------------------------------------
PEOPLE = {}


def limb(name, r1, r2, length, mat, parent, loc, cap=True):
    bm = bmesh.new()
    add_cyl(bm, r1, r2, length, seg=10, matrix=Matrix.Translation((0, 0, -length / 2)))
    if cap:
        add_sphere(bm, r2 * 1.05, u=10, v=6, matrix=Matrix.Translation((0, 0, -length)))
    ob = obj_from_bm(name, bm, mat, collection='People', smooth=True)
    ob.parent = parent
    ob.location = loc
    ob.rotation_mode = 'XYZ'
    return ob


def build_person(name, coat_mat):
    root = empty(name, collection='People')
    root.rotation_mode = 'XYZ'
    bm = bmesh.new()
    add_cyl(bm, 0.17, 0.21, 0.6, seg=14, matrix=Matrix.Translation((0, 0, 0.3)))     # chest
    add_cyl(bm, 0.21, 0.27, 0.62, seg=14, matrix=Matrix.Translation((0, 0, -0.31)))  # coat skirt
    add_sphere(bm, 0.2, u=14, v=8, matrix=Matrix.Translation((0, 0, 0.58)) @ Matrix.Diagonal((1.15, 0.8, 0.45, 1)))
    torso = obj_from_bm(name + '_torso', bm, coat_mat, collection='People', smooth=True)
    torso.parent = root
    torso.location = (0, 0, 0.95)
    torso.rotation_mode = 'XYZ'
    bm = bmesh.new()
    add_sphere(bm, 0.115, u=16, v=10, matrix=Matrix.Translation((0, 0, 0.16)) @ Matrix.Diagonal((0.92, 1.0, 1.1, 1)))
    add_cyl(bm, 0.05, 0.05, 0.1, seg=8, matrix=Matrix.Translation((0, 0, 0.04)))
    head = obj_from_bm(name + '_head', bm, MAT['skin'], collection='People', smooth=True)
    head.parent = torso
    head.location = (0, 0, 0.66)
    head.rotation_mode = 'XYZ'
    bm = bmesh.new()
    add_sphere(bm, 0.12, u=16, v=8, matrix=Matrix.Translation((0, 0, 0.25)) @ Matrix.Diagonal((1, 1.05, 0.75, 1)))
    add_cyl(bm, 0.19, 0.19, 0.015, seg=20, matrix=Matrix.Translation((0, 0, 0.235)))
    hat = obj_from_bm(name + '_hat', bm, MAT['hat'], collection='People', smooth=True)
    hat.parent = head
    parts = dict(root=root, torso=torso, head=head)
    for side, sx in (('L', 1), ('R', -1)):
        ua = limb(f'{name}_arm{side}', 0.065, 0.055, 0.3, coat_mat, torso, (sx * 0.23, 0, 0.55))
        fa = limb(f'{name}_fore{side}', 0.055, 0.045, 0.27, coat_mat, ua, (0, 0, -0.3))
        hd = limb(f'{name}_hand{side}', 0.04, 0.035, 0.08, MAT['skin'], fa, (0, 0, -0.27))
        th = limb(f'{name}_thigh{side}', 0.085, 0.07, 0.46, MAT['coat'], torso, (sx * 0.1, 0, 0.0))
        sh = limb(f'{name}_shin{side}', 0.065, 0.055, 0.45, MAT['coat'], th, (0, 0, -0.46))
        bm = bmesh.new()
        add_box(bm, -0.05, -0.04, -0.07, 0.05, 0.2, 0.0)
        shoe = obj_from_bm(f'{name}_shoe{side}', bm, MAT['hat'], collection='People')
        shoe.parent = sh
        shoe.location = (0, 0, -0.45)
        parts.update({'arm' + side: ua, 'fore' + side: fa, 'hand' + side: hd, 'thigh' + side: th, 'shin' + side: sh})
    PEOPLE[name] = parts
    return parts


def pose(p, **rot):
    for k, v in rot.items():
        if k == 'loc':
            p['root'].location = v
        elif k == 'yaw':
            p['root'].rotation_euler = (0, 0, v)
        else:
            p[k].rotation_euler = v


def build_people():
    # the scale reference standing at the tank's base, looking up
    p = build_person('Bystander', MAT['coat'])
    pose(p, loc=(4.5, L.TANK_Y + L.TANK_R + 1.6, 0.03), yaw=math.pi + 0.25, head=(0.45, 0, 0),
         armL=(0.05, 0.1, 0), armR=(0.1, -0.1, 0), foreR=(0.3, 0, 0))
    # the man in charge with his clipboard (1915 flashback)
    p = build_person('Treasurer', MAT['coat2'])
    pose(p, loc=(-3.5, L.TANK_Y + 6.0, 0.25), yaw=math.pi * 0.8, head=(-0.25, 0, 0.2),
         armR=(0.55, -0.15, 0), foreR=(1.05, 0, 0), armL=(0.2, 0.25, 0), foreL=(1.2, 0, 0.3))
    bm = bmesh.new()
    add_box(bm, -0.11, -0.01, -0.15, 0.11, 0.01, 0.15)
    clip = obj_from_bm('Clipboard', bm, MAT['paper'], collection='People')
    clip.parent = p['foreR']
    clip.location = (0, 0.06, -0.26)
    clip.rotation_euler = (0.9, 0, 0)
    # three people trapped in the cooling molasses
    for nm, mat in (('Stuck1', MAT['coat']), ('Stuck2', MAT['coat2']), ('Stuck3', MAT['coat'])):
        build_person(nm, mat)


STUCK_BASE = {
    'Stuck1': dict(loc=(-24.5, 10.5, -0.38), yaw=0.6, kind='reach'),
    'Stuck2': dict(loc=(-28.5, 7.0, -0.22), yaw=-0.9, kind='crawl'),
    'Stuck3': dict(loc=(-20.0, 5.0, -0.32), yaw=2.4, kind='reach2'),
}


def update_people(tv, s):
    for nm, base in STUCK_BASE.items():
        p = PEOPLE[nm]
        lt = tv - SHOT['stuck']['t0']
        decay = math.exp(-max(lt, 0) * 0.35)
        osc = math.sin(lt * 2.4 + len(nm)) * decay
        osc2 = math.sin(lt * 1.7 + 1.3) * decay
        if base['kind'] == 'crawl':
            pose(p, loc=base['loc'], yaw=base['yaw'], torso=(-1.15 + 0.06 * osc, 0, 0.05 * osc2), head=(0.9, 0, 0.1),
                 thighL=(0.15, 0, 0), thighR=(0.25, 0, 0), shinL=(-1.6, 0, 0), shinR=(-1.5, 0, 0),
                 armL=(1.0 + 0.35 * osc, 0.1, 0), foreL=(0.2, 0, 0), armR=(0.55 - 0.3 * osc, -0.1, 0), foreR=(0.3, 0, 0))
        elif base['kind'] == 'reach':
            pose(p, loc=base['loc'], yaw=base['yaw'], torso=(0.15 + 0.05 * osc2, 0.05 * osc, 0), head=(0.35, 0.1 * osc, 0),
                 thighL=(1.45, 0.1, 0), thighR=(1.35, -0.1, 0), shinL=(-0.3, 0, 0), shinR=(-0.2, 0, 0),
                 armR=(2.7 + 0.3 * osc, -0.25, 0), foreR=(0.25 + 0.2 * osc2, 0, 0), armL=(0.6, 0.6, 0), foreL=(0.9, 0, 0))
        else:
            pose(p, loc=base['loc'], yaw=base['yaw'], torso=(-0.55 + 0.08 * osc2, 0.1 * osc, 0), head=(0.6, 0, 0),
                 thighL=(1.2, 0, 0), thighR=(0.9, 0, 0), shinL=(-1.0, 0, 0), shinR=(-0.9, 0, 0),
                 armL=(1.6 + 0.4 * osc, 0.35, 0), foreL=(0.5, 0, 0), armR=(1.2 - 0.3 * osc, -0.3, 0), foreR=(0.6, 0, 0))


# ----------------------------------------------------------------------------
# Thermometer on a facade, street lamps, smell wisps
# ----------------------------------------------------------------------------
THERMO = {}
TH_POS = Vector((-8.7, L.STREET_Y1 + 2.0 - 0.06, 4.9))


def text_obj(name, body, size, mat, loc, parent=None):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.font = bpy.data.fonts.load(FONT_PATH, check_existing=True)
    cu.size = size
    cu.extrude = 0.002
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    ob = bpy.data.objects.new(name, cu)
    ob.data.materials.append(mat)
    coll('Props').objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob


TH_MIN, TH_MAX = -10.0, 50.0
TH_BOT, TH_TOP = -0.38, 0.36


def build_thermometer():
    root = empty('Thermometer', loc=TH_POS, collection='Props')
    bm = bmesh.new()
    add_box(bm, -0.11, -0.018, -0.5, 0.11, 0.0, 0.5)
    board = obj_from_bm('ThermoBoard', bm, MAT['thermo_board'], collection='Props')
    board.parent = root
    bm = bmesh.new()
    add_cyl(bm, 0.012, 0.012, TH_TOP - TH_BOT + 0.05, seg=16, matrix=Matrix.Translation((0, -0.035, (TH_TOP + TH_BOT) / 2)))
    add_sphere(bm, 0.022, matrix=Matrix.Translation((0, -0.035, TH_BOT - 0.03)))
    tube = obj_from_bm('ThermoTube', bm, MAT['glass'], collection='Props', smooth=True)
    tube.parent = root
    bm = bmesh.new()
    add_cyl(bm, 0.0065, 0.0065, 1.0, seg=12, matrix=Matrix.Translation((0, 0, 0.5)))
    merc = obj_from_bm('ThermoMercury', bm, MAT['mercury'], collection='Props', smooth=True)
    merc.parent = root
    merc.location = (0, -0.035, TH_BOT)
    bm = bmesh.new()
    add_sphere(bm, 0.016, matrix=Matrix.Translation((0, -0.035, TH_BOT - 0.03)))
    bulb = obj_from_bm('ThermoBulb', bm, MAT['mercury'], collection='Props', smooth=True)
    bulb.parent = root
    bm = bmesh.new()
    for deg in range(-10, 51, 2):
        z = TH_BOT + (deg - TH_MIN) / (TH_MAX - TH_MIN) * (TH_TOP - TH_BOT)
        wdt = 0.035 if deg % 10 == 0 else 0.018
        add_box(bm, 0.02, -0.021, z - 0.0018, 0.02 + wdt, -0.018, z + 0.0018)
    ticks = obj_from_bm('ThermoTicks', bm, MAT['ink'], collection='Props')
    ticks.parent = root
    for deg in range(-10, 51, 10):
        z = TH_BOT + (deg - TH_MIN) / (TH_MAX - TH_MIN) * (TH_TOP - TH_BOT)
        text_obj(f'ThermoLbl{deg}', str(deg), 0.032, MAT['ink'], (-0.05, -0.02, z), parent=root)
    text_obj('ThermoF', '°F', 0.03, MAT['ink'], (0.0, -0.02, 0.44), parent=root)
    THERMO['merc'] = merc


def update_thermometer(tv):
    t0, t1 = ls('L07') + 0.3, LINE['L07']['end'] - 0.2
    u = min(1.0, max(0.0, (tv - t0) / (t1 - t0)))
    u = u * u * (3 - 2 * u)
    deg = 2.0 + (41.0 - 2.0) * u
    top = (deg - TH_MIN) / (TH_MAX - TH_MIN) * (TH_TOP - TH_BOT)
    THERMO['merc'].scale = (1, 1, max(top, 0.001))


LAMPS = []


def build_lamps():
    bm_post = bmesh.new()
    bm_lan = bmesh.new()
    pts = []
    for x in np.arange(-126, 127, 24.0):
        pts.append((x + 6, L.STREET_Y1 + 1.2))
        pts.append((x - 6, L.STREET_Y0 - 1.7))
    for (x, y) in pts:
        add_cyl(bm_post, 0.07, 0.1, 3.6, seg=8, matrix=Matrix.Translation((x, y, 1.8)))
        add_cyl(bm_post, 0.18, 0.18, 0.08, seg=8, matrix=Matrix.Translation((x, y, 3.64)))
        add_cyl(bm_lan, 0.16, 0.12, 0.45, seg=6, matrix=Matrix.Translation((x, y, 3.9)))
        add_cyl(bm_post, 0.24, 0.02, 0.22, seg=6, matrix=Matrix.Translation((x, y, 4.23)))
    obj_from_bm('LampPosts', bm_post, MAT['iron'], collection='Props')
    obj_from_bm('Lanterns', bm_lan, MAT['lantern'], collection='Props')
    for (x, y) in pts:
        if -50 < x < 10:
            ld = bpy.data.lights.new('Gas', 'POINT')
            ld.color = (1.0, 0.68, 0.36)
            ld.shadow_soft_size = 0.2
            ld.energy = 0
            lo = bpy.data.objects.new('GasLight', ld)
            lo.location = (x, y, 3.9)
            coll('Lights').objects.link(lo)
            LAMPS.append(lo)


WISPS = []


def build_wisps():
    rng = random.Random(3)
    bm = bmesh.new()
    add_sphere(bm, 1.0, u=16, v=10)
    me = bpy.data.meshes.new('wisp')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MAT['wisp'])
    me.shade_smooth()
    for i in range(0):   # tested and dropped: read as floating discs rather than scent
        ob = bpy.data.objects.new('Wisp', me)
        coll('Wisps').objects.link(ob)
        x = rng.uniform(-80, 60)
        y = rng.choice([rng.uniform(1, 17), rng.uniform(20, 80) if rng.random() < 0.3 else rng.uniform(-30, -3)])
        WISPS.append(dict(obj=ob, x=x, y=y, ph=rng.random(), sp=rng.uniform(0.6, 1.3), size=rng.uniform(2.5, 5.0)))


def update_wisps(tv):
    s = SHOT['decades']
    lt = tv - s['t0']
    for w in WISPS:
        u = (lt * 0.18 * w['sp'] + w['ph']) % 1.0
        ob = w['obj']
        ob.location = (w['x'] + math.sin(u * 6 + w['ph'] * 9) * 2.0, w['y'] + math.cos(u * 5) * 1.5, 0.5 + u * 22)
        sc = w['size'] * (0.4 + u * 1.6)
        ob.scale = (sc, sc, sc * 1.8)
        fade = math.sin(math.pi * u)
        ob.color = (fade, fade, fade, 1)


# ----------------------------------------------------------------------------
# Cameras: one per shot, each on a keyframed rig that tracks a keyframed target
# ----------------------------------------------------------------------------
CAMS = {}
SHAKE = {}


def camera_shot(name, lens, path, target, fstop=8.0, shake=0.0, focus=None):
    """path/target: list of (u, (x, y, z)) keys with u in 0..1 of the shot."""
    s = SHOT[name]
    rig = empty('Rig_' + name)
    tgt = empty('Target_' + name)
    cd = bpy.data.cameras.new('Cam_' + name)
    cd.lens = lens
    cd.sensor_width = 24
    cd.sensor_fit = 'VERTICAL'
    cd.clip_start, cd.clip_end = 0.05, 5000
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cd.dof.aperture_blades = 7
    cam = bpy.data.objects.new('Cam_' + name, cd)
    coll('Rig').objects.link(cam)
    cam.parent = rig
    con = rig.constraints.new('TRACK_TO')
    con.target = tgt
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    fe = empty('Focus_' + name)
    cd.dof.focus_object = fe if focus is not None else tgt
    if focus is not None:
        fe.location = focus
    span = s['f1'] - s['f0']
    for u, p in path:
        rig.location = p
        rig.keyframe_insert('location', frame=s['f0'] + u * span)
    for u, p in target:
        tgt.location = p
        tgt.keyframe_insert('location', frame=s['f0'] + u * span)
    for ob in (rig, tgt):
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.easing = 'EASE_IN_OUT'
    m = bpy.context.scene.timeline_markers.new('M_' + name, frame=s['f0'])
    m.camera = cam
    CAMS[name] = cam
    SHAKE[name] = shake
    return cam


def build_cameras():
    TX, TY, R, H = L.TANK_X, L.TANK_Y, L.TANK_R, L.TANK_H
    north_wall_y = TY + R
    # 0 HOOK: street level east of the tank, the wave rolling toward the lens
    camera_shot('hook', 15, [(0, (30.0, 2.6, 1.25)), (1, (34.0, 2.8, 1.1))],
                [(0, (4.0, -3.0, 4.5)), (1, (14.0, 0.0, 2.4))], fstop=5.6, shake=0.006)
    # 1 AERIAL: over the harbour toward the tank on Commercial Street
    camera_shot('aerial', 30, [(0, (150.0, -170.0, 95.0)), (1, (95.0, -120.0, 58.0))],
                [(0, (0.0, -12.0, 4.0)), (1, (0.0, -15.0, 6.0))], fstop=16)
    # 2 SCALE: low hero angle next to a person at the tank base
    camera_shot('scale', 18, [(0, (13.0, 7.5, 1.0)), (1, (17.0, 9.0, 1.4))],
                [(0, (4.0, north_wall_y + 1.4, 1.8)), (1, (0.0, TY, 11.0))], fstop=8, focus=(4.5, north_wall_y + 1.6, 1.6))
    # 3 LEAKS: close on the wall, molasses seeping from the seams
    a = math.radians(152)
    wall = Vector((TX + R * math.cos(a), TY + R * math.sin(a), 0))
    nrm = Vector((math.cos(a), math.sin(a), 0))
    tang = Vector((-nrm.y, nrm.x, 0))
    camera_shot('leaks', 28, [(0, tuple(wall + nrm * 2.6 + tang * 1.6 + Vector((0, 0, 1.6)))),
                              (1, tuple(wall + nrm * 2.0 + tang * 1.1 + Vector((0, 0, 1.9))))],
                [(0, tuple(wall - tang * 0.6 + Vector((0, 0, 3.2)))), (1, tuple(wall - tang * 0.6 + Vector((0, 0, 2.9))))],
                fstop=4.0)
    # 4 CUTAWAY (1915): half the shell removed to show the six-inch water test
    camera_shot('cutaway', 28, [(0, (4.0, 7.0, 25.0)), (1, (-2.0, 5.0, 22.0))],
                [(0, (0.0, TY + 1.0, 0.0)), (1, (-1.0, TY + 2.0, 0.5))], fstop=11)
    # 5 PAINT (1918): orbit while brown paint sweeps over the steel
    pts = []
    for i in range(5):
        ang = math.radians(35 + i * 27)
        pts.append((i / 4, (TX + 32 * math.cos(ang), TY + 32 * math.sin(ang), 10.0 + i * 0.4)))
    camera_shot('paint', 24, pts, [(0, (TX, TY, 7.0)), (1, (TX, TY, 7.5))], fstop=11)
    # 6 THERMOMETER on a facade
    camera_shot('thermo', 50, [(0, tuple(TH_POS + Vector((0.25, -2.2, -0.15)))), (1, tuple(TH_POS + Vector((0.05, -1.15, 0.0))))],
                [(0, tuple(TH_POS + Vector((0, 0, -0.05)))), (1, tuple(TH_POS + Vector((0, 0, 0.02))))], fstop=2.8)
    # 7 RIVETS: extreme close-up on the street-facing seam
    a = panel_angles(POP_SEAM_PANEL)[0]
    seam = Vector((TX + R * math.cos(a), TY + R * math.sin(a), 0))
    nrm = Vector((math.cos(a), math.sin(a), 0))
    side = Vector((-nrm.y, nrm.x, 0))
    camera_shot('rivets', 32, [(0, tuple(seam + nrm * 2.4 + side * 1.0 + Vector((0, 0, 2.2)))),
                               (1, tuple(seam + nrm * 1.7 + side * 0.7 + Vector((0, 0, 2.9))))],
                [(0, tuple(seam + Vector((0, 0, 2.6)))), (1, tuple(seam + Vector((0, 0, 3.4))))], fstop=3.5, shake=0.012)
    # 8 BURST: wide from the south sidewalk west of the tank
    camera_shot('burst', 22, [(0, (-16.0, -60.0, 6.5)), (1, (-18.0, -63.0, 7.0))],
                [(0, (TX, TY, 6.5)), (1, (TX, TY + 2, 3.5))], fstop=11, shake=0.02)
    # 9 RACE: tracking the eastbound front along Commercial Street
    fr = SIM['front']
    def front_x(st):
        k = int(np.argmin(np.abs(SIM['times'] - st)))
        return float(fr[k, 2])
    s = SHOT['race']
    keys_p, keys_t = [], []
    for i in range(6):
        u = i / 5
        st = s['sim'][1] + (s['sim'][2] - s['sim'][1]) * u
        fx = max(front_x(st), 14.0)
        keys_p.append((u, (fx + 13.0, -1.2, 5.0)))
        keys_t.append((u, (fx - 3.0, 9.0, 1.2)))
    camera_shot('race', 18, keys_p, keys_t, fstop=11, shake=0.006)
    # 10 HOUSE: the clapboard house shoved off its foundation
    camera_shot('house', 20, [(0, (50.0, 2.0, 6.2)), (1, (48.0, 0.5, 5.6))],
                [(0, (33.0, -23.0, 3.5)), (1, (34.0, -24.0, 2.5))], fstop=11, shake=0.01)
    # 11 EL: under the elevated railway as it buckles
    camera_shot('el', 20, [(0, (-40.0, 9.0, 4.6)), (1, (-44.0, 9.0, 4.9))],
                [(0, (0.0, 9.0, 6.5)), (1, (0.0, 10.0, 6.5))], fstop=11, shake=0.012)
    # 12 RISE: crane up over the flooded street
    camera_shot('rise', 24, [(0, (12.0, -52.0, 5.0)), (1, (34.0, -118.0, 62.0))],
                [(0, (2.0, -14.0, 2.0)), (1, (0.0, -2.0, 0.0))], fstop=11)
    # 13 FREEZE: dusk into a freezing night, close on the surface
    camera_shot('freeze', 24, [(0, (-11.5, 9.2, 2.6)), (1, (-12.5, 9.0, 1.8))],
                [(0, (-24.0, 7.0, 0.0)), (1, (-24.5, 7.5, 0.2))], fstop=5.6, focus=(-17.0, 8.5, 0.4))
    # 14 STUCK: people trapped as it thickens
    camera_shot('stuck', 30, [(0, (-16.0, 2.0, 1.4)), (1, (-17.3, 3.2, 1.2))],
                [(0, (-24.0, 8.0, 0.6)), (1, (-24.5, 8.4, 0.7))], fstop=4, focus=(-24.0, 8.0, 0.7))
    # 15 DECADES: summer evening aerial, the sweet smell rising
    camera_shot('decades', 28, [(0, (-70.0, -95.0, 48.0)), (1, (-35.0, -80.0, 40.0))],
                [(0, (-10.0, 18.0, 6.0)), (1, (0.0, 14.0, 4.0))], fstop=16)
    # 16 END: back on the street, the wave frozen mid-surge
    camera_shot('end', 15, [(0, (35.5, 2.9, 1.15)), (1, (33.0, 2.7, 1.25))],
                [(0, (10.0, -1.0, 3.0)), (1, (8.0, -2.0, 3.6))], fstop=5.6)


def update_shake(f, s):
    amp = SHAKE.get(s['name'], 0.0)
    cam = CAMS[s['name']]
    if amp <= 0:
        cam.rotation_euler = (0, 0, 0)
        return
    t = f / FPS
    ramp = 1.0
    if s['name'] == 'rivets':
        ramp = 0.2 + 0.8 * min(1.0, (t - s['t0']) / (s['t1'] - s['t0']))
    if s['name'] == 'burst':
        ramp = max(0.3, 1.0 - (t - s['t0']) / (s['t1'] - s['t0']))
    n = lambda k: math.sin(t * 37.1 + k) * 0.6 + math.sin(t * 61.7 + 2 * k) * 0.4
    cam.rotation_euler = (amp * ramp * n(0.3), amp * ramp * n(1.7), amp * ramp * n(4.1) * 0.5)


# ----------------------------------------------------------------------------
# Lighting, visibility and environment keyframes per shot
# ----------------------------------------------------------------------------
def build_keys():
    sc = bpy.context.scene
    D = dict(elev=22, azim=200, sun=3.4, sky=0.26, moon=0.0, col=(1.0, 0.91, 0.8), exp=-0.1, fog=0.3)
    def lk_(f, **kw):
        p = dict(D)
        p.update(kw)
        light_key(f, p['elev'], p['azim'], p['sun'], p['sky'], p['moon'], p['col'], p['exp'], p['fog'])
    S = SHOT
    lk_(1)
    lk_(S['thermo']['f0'], sun=2.2, sky=0.3, exp=-0.15)
    lk_(S['thermo']['f1'], sun=4.6, sky=0.38)
    lk_(S['rise']['f0'], elev=16, sun=4.0)
    lk_(S['rise']['f1'], elev=8, sun=3.2, col=(1.0, 0.75, 0.5), fog=0.55)
    lk_(S['freeze']['f0'], elev=6, sun=2.6, col=(1.0, 0.7, 0.45), fog=0.55)
    lk_(S['freeze']['f0'] + int(0.45 * (S['freeze']['f1'] - S['freeze']['f0'])), elev=-2, sun=0.0, sky=0.25,
        moon=0.5, col=(1.0, 0.6, 0.4), exp=0.4, fog=0.35)
    lk_(S['freeze']['f1'], elev=-4, sun=0.0, sky=0.2, moon=0.7, exp=0.7, fog=0.3)
    lk_(S['stuck']['f0'], elev=-4, sun=0.0, sky=0.2, moon=0.8, exp=0.45, fog=0.3)
    lk_(S['stuck']['f1'], elev=-4, sun=0.0, sky=0.2, moon=0.8, exp=0.45, fog=0.3)
    lk_(S['decades']['f0'], elev=9, azim=245, sun=4.2, sky=0.45, col=(1.0, 0.72, 0.45), exp=0.1, fog=0.6)
    lk_(S['decades']['f1'], elev=6, azim=250, sun=3.8, sky=0.42, col=(1.0, 0.66, 0.4), exp=0.1, fog=0.65)
    lk_(S['end']['f0'])
    # step changes at cuts: duplicate the previous value one frame before each cut
    for idb in (SKY['node'].id_data, SKY['sun'], SKY['sun'].data, SKY['moon'].data, sc, sc.node_tree):
        pass
    # environment values used by the materials
    env_key('night', 1, 0.0)
    env_key('leak', 1, 1.0)
    env_key('wipe', 1, 1.01)
    env_key('wipe', S['cutaway']['f0'] - 1, 1.01)
    env_key('wipe', S['cutaway']['f0'], 0.0)
    env_key('wipe', S['paint']['f0'], 0.12)
    env_key('wipe', S['paint']['f1'], 0.86)
    env_key('wipe', S['paint']['f1'] + 1, 1.01)
    env_key('leak', S['cutaway']['f0'] - 1, 1.0)
    env_key('leak', S['cutaway']['f0'], 0.0)       # brand-new tank in the 1915 flashback
    env_key('leak', S['paint']['f0'] - 1, 0.0)
    env_key('leak', S['paint']['f0'], 0.9)
    env_key('night', S['freeze']['f0'], 0.0)
    env_key('night', S['freeze']['f0'] + int(0.5 * (S['freeze']['f1'] - S['freeze']['f0'])), 0.85)
    env_key('night', S['stuck']['f1'], 1.0)
    env_key('night', S['decades']['f0'] - 1, 1.0)
    env_key('night', S['decades']['f0'], 0.15)
    env_key('night', S['end']['f0'] - 1, 0.15)
    env_key('night', S['end']['f0'], 0.0)
    env_key('frost', 1, 0.0)
    env_key('frost', S['freeze']['f0'] + int(0.3 * (S['freeze']['f1'] - S['freeze']['f0'])), 0.0)
    env_key('frost', S['freeze']['f1'], 1.0)
    env_key('frost', S['decades']['f0'] - 1, 1.0)
    env_key('frost', S['decades']['f0'], 0.0)
    env_key('stain', 1, 0.0)
    env_key('stain', S['burst']['f0'], 0.0)
    env_key('stain', S['rise']['f1'], 0.5)
    env_key('stain', S['stuck']['f1'], 1.0)
    env_key('stain', S['decades']['f0'] - 1, 1.0)
    env_key('stain', S['decades']['f0'], 0.0)
    env_key('stain', S['end']['f0'], 0.12)
    for fc in ENV.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    # lamps
    sl = bpy.data.lights.new('StuckLamp', 'POINT')
    sl.color = (1.0, 0.66, 0.34)
    sl.shadow_soft_size = 0.3
    slo = bpy.data.objects.new('StuckLamp', sl)
    slo.location = (-21.0, 4.0, 3.6)
    coll('Lights').objects.link(slo)
    for f, e in ((1, 0), (S['stuck']['f0'] - 1, 0), (S['stuck']['f0'], 380), (S['stuck']['f1'], 380), (S['stuck']['f1'] + 1, 0)):
        sl.energy = e
        sl.keyframe_insert('energy', frame=f)
    for fc in sl.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT'
    for lo in LAMPS:
        for f, e in ((1, 0), (S['freeze']['f0'] + int(0.4 * (S['freeze']['f1'] - S['freeze']['f0'])), 0),
                     (S['freeze']['f0'] + int(0.6 * (S['freeze']['f1'] - S['freeze']['f0'])), 120),
                     (S['stuck']['f1'], 120), (S['decades']['f0'], 0)):
            lo.data.energy = e
            lo.data.keyframe_insert('energy', frame=f)
    # light keys: hold values across the shot, step at cuts
    for idb in (SKY['node'].id_data, SKY['sun'], SKY['sun'].data, SKY['moon'].data, sc, sc.node_tree):
        ad = idb.animation_data
        if ad and ad.action:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'


def vis_key(obj, visible_ranges):
    """Keyframe hide_render with CONSTANT steps so it is only visible inside the given frame ranges."""
    merged = []
    for a, b in sorted(visible_ranges):
        if merged and a <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    obj.hide_render = True
    obj.keyframe_insert('hide_render', frame=1)
    for a, b in merged:
        obj.hide_render = False
        obj.keyframe_insert('hide_render', frame=a)
        obj.hide_render = True
        obj.keyframe_insert('hide_render', frame=b + 1)
    for fc in obj.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT'


def build_visibility():
    S = SHOT
    def rng(*names):
        return [(S[n]['f0'], S[n]['f1']) for n in names]
    post = ['hook', 'burst', 'race', 'house', 'el', 'rise', 'freeze', 'stuck', 'end']
    vis_key(SIM['obj'], rng(*post))
    vis_key(TANK['puddle'], rng('cutaway'))
    for p in TANK['panels']:
        k = TANK['panels'].index(p)
        north = math.sin(p['am']) > 0.15
        names = [s['name'] for s in SHOTS if s['name'] != 'decades' and not (north and s['name'] == 'cutaway')]
        for ob in (p['obj'], p['rivets'], p['tmpl']):
            vis_key(ob, rng(*names))
    vis_key(TANK['roof'], rng(*[s['name'] for s in SHOTS if s['name'] not in ('decades', 'cutaway')]))
    for d in TANK['pop']:
        vis_key(d['obj'], rng(*[s['name'] for s in SHOTS if s['name'] not in ('decades', 'hook', 'end', 'cutaway') and s['f0'] < S['burst']['f0']]))
    for ob, _ in TANK['spurts']:
        vis_key(ob, rng('rivets'))
    vis_key(TANK['crack'], rng('rivets'))
    for d in TANK['drips']:
        vis_key(d['obj'], rng('leaks', 'scale'))
    for nm in ('Bystander',):
        for ob in PEOPLE[nm]['root'].children_recursive:
            vis_key(ob, rng('scale', 'aerial'))
    for ob in PEOPLE['Treasurer']['root'].children_recursive:
        vis_key(ob, rng('cutaway'))
    for nm in STUCK_BASE:
        for ob in PEOPLE[nm]['root'].children_recursive:
            vis_key(ob, rng('stuck', 'freeze'))
    for w in WISPS:
        vis_key(w['obj'], rng('decades'))
    for d in DEB:
        for ob in [d['obj']] + list(d['obj'].children_recursive):
            vis_key(ob, rng(*[s['name'] for s in SHOTS if s['name'] != 'decades']))
    for ob in [HOUSE['obj']] + list(HOUSE['obj'].children_recursive):
        vis_key(ob, rng(*[s['name'] for s in SHOTS if s['name'] != 'decades']))
    for name in ('TankBase',):
        pass


# ----------------------------------------------------------------------------
# Per-frame update
# ----------------------------------------------------------------------------
def on_frame(scene, depsgraph=None):
    f_int = scene.frame_current
    fr = f_int + scene.frame_subframe
    s = shot_at(f_int)
    tv = (fr - 1) / FPS
    st = sim_time(s, tv)
    update_molasses(st, s['name'])
    update_tank(st, tv)
    update_rivet_pops(tv)
    update_drips(tv)
    update_debris(st)
    update_el(st)
    update_people(tv, s)
    update_thermometer(tv)
    update_wisps(tv)
    update_shake(fr, s)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def export_events(sc):
    from bpy_extras.object_utils import world_to_camera_view
    ev = {'shots': [{k: s[k] for k in ('name', 't0', 't1', 'f0', 'f1')} for s in SHOTS],
          'rivet_pops': rivet_pop_times(), 'drips': [], 'anchors': {}}
    for sname in ('leaks', 'scale'):
        s = SHOT[sname]
        for d in TANK['drips']:
            k0 = math.ceil(s['t0'] / d['period'] + d['phase'])
            k1 = math.floor(s['t1'] / d['period'] + d['phase'])
            ev['drips'] += [(k - d['phase']) * d['period'] for k in range(k0, k1 + 1)]
    ev['drips'] = sorted(set(round(t, 3) for t in ev['drips']))
    # where the tank's top and base land on screen during the scale shot (for the 50 FT bracket)
    s = SHOT['scale']
    pts = {'tank_top': Vector((L.TANK_X + 2.5, L.TANK_Y + L.TANK_R, L.TANK_H)),
           'tank_base': Vector((L.TANK_X + 2.5, L.TANK_Y + L.TANK_R, 0.0)),
           'person_head': Vector((4.5, L.TANK_Y + L.TANK_R + 1.6, 1.8))}
    anchors = {k: [] for k in pts}
    for f in range(s['f0'], s['f1'] + 1):
        sc.frame_set(f)
        cam = CAMS['scale']
        for k, p in pts.items():
            v = world_to_camera_view(sc, cam, p)
            anchors[k].append((f, round(v.x, 4), round(1 - v.y, 4)))
    ev['anchors'] = anchors
    with open(os.path.join(ROOT, 'build', 'events.json'), 'w') as fh:
        json.dump(ev, fh, indent=1)
    print('wrote build/events.json')


def main():
    sc = reset_scene()
    setup_render(sc)
    load_sim()
    make_env_group()
    build_materials()
    build_world(sc)
    build_compositor(sc)
    build_ground()
    build_city()
    build_el()
    build_tank()
    build_molasses()
    build_debris()
    build_people()
    build_thermometer()
    build_lamps()
    build_wisps()
    build_cameras()
    build_keys()
    build_visibility()
    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(on_frame)
    print('SHOTS:')
    for s in SHOTS:
        print(f"  {s['name']:8s} frames {s['f0']:4d}-{s['f1']:4d}  ({s['t0']:5.2f}-{s['t1']:5.2f}s)  sim={s['sim']}")
    print('objects:', len(bpy.data.objects), 'last frame', LAST_FRAME)
    if ARGS.export_events:
        export_events(sc)
        return
    if ARGS.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=ARGS.save_blend)
    os.makedirs(ARGS.out, exist_ok=True)
    if ARGS.stills:
        for tok in ARGS.stills.split(','):
            f = int(tok)
            sc.frame_set(f)
            sc.render.filepath = os.path.join(ARGS.out, f'still_{f:04d}.png')
            bpy.ops.render.render(write_still=True)
    if ARGS.frames:
        a, b = (int(x) for x in ARGS.frames.split('-'))
        sc.frame_start, sc.frame_end = a, min(b, LAST_FRAME)
        sc.render.filepath = os.path.join(ARGS.out, 'f_')
        bpy.ops.render.render(animation=True)


main()
