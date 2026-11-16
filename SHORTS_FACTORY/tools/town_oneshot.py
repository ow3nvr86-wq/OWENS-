"""THE LAST TOWN ON EARTH: one continuous camera shot (no cuts) for the dystopian town Short. An original, made-up place:
one 14-floor tower in a snowy fjord, a single tunnel out, a bay that breathes out the Whiteout every night.
  aerial dive -> in through the floor-9 end window -> down the hall (store, police, clinic, school) -> you at your door
  -> 10:15 clock, speakers, red lights -> back out of the window -> the steel shutters slam down floor by floor
  -> the Whiteout rolls in off the bay -> down into the fog -> the smiling man at the entrance -> the doors lock
  -> the tunnel gate shuts -> morning: up to the resident counter -> 270 ... 271 -> dive back in -> the vacant door opens.
Every camera key is tied to a cue word in work/words.json, so a new voiceover re-times the whole shot.
Writes a 60 fps image sequence + camera.json (camera per frame + 2D actor tracks + beat times).
Run: $BLENDER -b --factory-startup -P tools/town_oneshot.py -- <out> --words <words.json> [--scale 0.5] [--spp 6]
     [--list a,b,c] [--start A --end B]"""
import bpy, math, sys, os, json, random, re, importlib.util
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0]; arg = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
SCALE, SPP = arg('--scale', 0.5), arg('--spp', 6)
WORDS = json.load(open(arg('--words', '')))
FPS = 60; DUR = WORDS['duration'] + 1.2; NF = int(round(DUR * FPS))
START, END = arg('--start', 0), arg('--end', NF - 1)
HERE = os.path.dirname(os.path.abspath(__file__))
s_ = importlib.util.spec_from_file_location('presets_fn2', os.path.join(HERE, 'presets_fn2.py')); F2 = importlib.util.module_from_spec(s_); s_.loader.exec_module(F2)
ISL = F2.ISL; box, cyl, cone, ball = ISL.box, ISL.cyl, ISL.cone, ISL.ball; m_plain, m_noise, m_brick, m_emis = F2.m_plain, F2.m_noise, F2.m_brick, ISL.m_emis
os.makedirs(OUT, exist_ok=True); random.seed(7)

# ------------------------------------------------------------------ beats from the voice ---------------------------
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
CUES = [('hook', 'nobody'), ('live', 'live'), ('people', 'people'), ('one', 'one'), ('store', 'store'), ('school', 'school'), ('hall', 'hall'),
        ('never', 'never'), ('good', 'good'), ('cant', 'cant'), ('night', 'night'), ('speakers', 'speakers'), ('sealing', 'sealing'),
        ('ret', 'return'), ('then', 'then'), ('slam', 'slam'), ('window', 'window'), ('whiteout', 'whiteout'), ('bay', 'bay'),
        ('nobody2', 'nobody'), ('inside', 'inside'), ('man', 'man'), ('later', 'later'), ('smiling', 'smiling'), ('name', 'name'),
        ('lock', 'lock'), ('tunnel', 'tunnel'), ('shuts', 'shuts'), ('morning', 'morning'), ('counts', 'counts'), ('seventy', 'seventy'),
        ('single', 'single'), ('except', 'except'), ('counted', 'counted'), ('seventyone', 'seventyone'), ('somebody', 'somebody'),
        ('empty', 'empty'), ('next', 'next'), ('yours', 'yours')]
B = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while j < len(ws) and norm(ws[j]['word']) != cue: j += 1
    if j == len(ws): raise SystemExit('cue word not found: ' + cue)
    B[key] = ws[j]['start']; wi = j + 1
B['end'] = DUR
print('beats', json.dumps({k: round(v, 2) for k, v in B.items()}), flush=True)

def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def keyed(keys, t, fn=ease):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1: u = fn((t - t0) / max(1e-6, t1 - t0)); return tuple(x + (y - x) * u for x, y in zip(a, b))
    return keys[-1][1]

# world layout (metres): the tower at the origin, 44 x 16 m, 14 floors of 3.1 m; floor 9 hallway along x at y = 0
FH, NFL = 3.1, 14; TW, TD = 44.0, 16.0; TOP = FH * NFL
Z9 = FH * 8; EYE = Z9 + 1.55                      # floor 9: floor level and eye height
WIN_W = (-22.0, 0.0, EYE)                         # the west end window of the floor-9 hallway (the camera's way in and out)
HERO_DOOR, VACANT_DOOR = 1.5, -2.5                # x of your door and of the empty apartment (both on the south side)
ENTRANCE = (0.0, -8.0, 0.0); MAN = (0.0, -11.2, 0.0); PORTAL = (172.0, 50.0, 0.0); SIGN = (0.0, -8.6, TOP + 2.6)

# ------------------------------------------------------------------ 2D actors -------------------------------------
def hero_pos(t):
    if t < B['ret'] + 0.25: return (HERO_DOOR, -1.0, Z9), 1
    if t < B['ret'] + 0.95: return keyed([(B['ret'] + 0.25, (HERO_DOOR, -1.0, Z9)), (B['ret'] + 0.95, (HERO_DOOR, -2.6, Z9))], t, lambda u: u), 1
    return (HERO_DOOR, -2.6, Z9), 0
RES = [(-16.0, 0.45, 1.0, 0.0), (-11.5, -0.5, -0.9, 0.3), (-9.5, 0.5, 1.1, 0.8), (9.0, -0.4, -1.0, 0.1), (8.5, 0.5, 0.9, 0.5), (13.0, -0.3, -1.1, 0.2)]
def res_pos(i, t):
    x0, y, v, ph = RES[i]
    if t < B['ret']: x = x0 + v * 0.55 * (t - B['store'] + ph); return (x, y, Z9), (1 if B['store'] - 1.5 < t else 0)
    xr = x0 + v * 0.55 * (B['ret'] - B['store'] + ph); east = xr > -1.0; x = xr + 5.2 * (t - B['ret']) * (1 if east else -1)    # flee away from the camera
    return (x, y, Z9), (1 if (x < 21.0 and t < B['then'] + 1.0 if east else t < B['ret'] + 0.7) else 0)
def man_pos(t): return MAN, (1 if B['inside'] + 0.6 < t < B['tunnel'] + 0.4 else 0)
ACTORS = dict(hero=hero_pos, man=man_pos)
for i in range(len(RES)): ACTORS['res%d' % i] = (lambda i: lambda t: res_pos(i, t))(i)

# ------------------------------------------------------------------ camera keys (t, position, look-at, lens) -----
b = B
CAM = [(0.0, (-175, -195, 125), (0, 0, 26), 30), (b['live'] - 0.6, (-95, -115, 72), (0, 0, 25), 28),
       (b['people'], (-78, -45, 40), (0, 0, 24), 26), (b['one'] + 0.2, (-44, 0.0, EYE + 0.4), (-22, 0, EYE), 26),
       (b['store'] - 0.15, (-21.2, 0.0, EYE), (-10, 0, EYE - 0.1), 24), (b['school'] + 0.2, (-8.5, 0.15, EYE), (2, -0.3, EYE - 0.2), 24),
       (b['never'], (-2.4, 0.55, EYE + 0.1), (HERO_DOOR, -1.1, EYE - 0.1), 26), (b['good'] + 0.2, (-0.6, 0.45, EYE), (HERO_DOOR, -1.0, EYE), 30),
       (b['night'], (-0.3, 0.55, EYE + 0.1), (HERO_DOOR, 1.3, EYE + 1.0), 28), (b['speakers'] + 0.2, (-1.4, 0.1, EYE - 0.5), (0.4, 0.0, Z9 + 2.75), 24),
       (b['ret'], (-0.6, 0.0, EYE), (9, 0.1, EYE - 0.4), 24), (b['then'] + 0.55, (-12.0, 0.0, EYE), (10, 0, EYE - 0.2), 24),
       (b['slam'] + 0.05, (-28.0, -1.0, EYE + 0.4), (0, 0, EYE), 24), (b['window'], (-58, -20, 30), (0, 0, 22), 26),
       (b['whiteout'] + 0.3, (-30, -46, 54), (-150, -10, 8), 24), (b['bay'], (-18, -50, 44), (-70, -5, 8), 24),
       (b['inside'], (-6, -40, 6.5), (0, -12, 3.0), 26), (b['man'] + 0.2, (0.4, -24, 2.3), (0, -11.2, 1.6), 28),
       (b['smiling'], (0.0, -14.8, 1.75), (0, -11.2, 1.55), 34), (b['name'], (-0.35, -14.1, 1.7), (0, -11.2, 1.45), 36),
       (b['lock'], (2.6, -16.5, 2.2), (0, -8.0, 2.0), 30), (b['tunnel'] + 0.15, (8, -20, 6), (PORTAL[0], PORTAL[1], 5), 55),
       (b['shuts'] + 0.6, (10, -20, 6.5), (PORTAL[0], PORTAL[1], 5), 70), (b['morning'] + 0.3, (22, -42, 14), (0, 0, 28), 24),
       (b['counts'] + 0.1, (13, -38, 38), (0, -8.6, SIGN[2]), 26), (b['seventy'], (7, -27, 44), (0, -8.6, SIGN[2]), 28),
       (b['except'], (3.5, -20, 45), (0, -8.6, SIGN[2]), 30), (b['seventyone'] + 0.6, (2.5, -18.5, 45.2), (0, -8.6, SIGN[2]), 30),
       (b['somebody'] + 1.0, (-42, -12, 30), (-22, 0, EYE), 24), (b['empty'], (-20.0, 0.0, EYE), (-5, 0, EYE - 0.2), 24),
       (b['next'] + 0.2, (-5.2, 0.35, EYE), (VACANT_DOOR, -1.3, EYE - 0.4), 26), (b['end'], (-3.5, -0.15, EYE - 0.1), (VACANT_DOOR, -1.3, EYE - 0.3), 30)]
CAM.sort(key=lambda k: k[0])
def cam_at(t):
    if t <= CAM[0][0]: return CAM[0][1], CAM[0][2], CAM[0][3]
    for a, c in zip(CAM, CAM[1:]):
        if t <= c[0]:
            u = ease((t - a[0]) / max(1e-6, c[0] - a[0])); m = lambda A, C: tuple(x + (y - x) * u for x, y in zip(A, C))
            return m(a[1], c[1]), m(a[2], c[2]), a[3] + (c[3] - a[3]) * u
    return CAM[-1][1], CAM[-1][2], CAM[-1][3]

# ------------------------------------------------------------------ the world -------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True); ISL._T.clear()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 3
sc.render.resolution_x, sc.render.resolution_y = int(1080 * SCALE), int(1920 * SCALE)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92; sc.render.fps = FPS
sc.cycles.light_sampling_threshold = 0.05

# sky: an overcast arctic day -> blue night -> cold pink morning (keyed)
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']
grad = nt.nodes.new('ShaderNodeTexGradient'); tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, math.pi / 2, 0)
ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(tc.outputs['Generated'], mp.inputs[0]); nt.links.new(mp.outputs[0], grad.inputs[0]); nt.links.new(grad.outputs['Fac'], ramp.inputs[0])
mixc = nt.nodes.new('ShaderNodeMix'); mixc.data_type = 'RGBA'; nt.links.new(ramp.outputs['Color'], mixc.inputs[6]); nt.links.new(mixc.outputs[2], bg.inputs['Color'])
ramp.color_ramp.elements[0].color = (0.62, 0.66, 0.72, 1); ramp.color_ramp.elements[1].color = (0.34, 0.40, 0.50, 1)
tint = mixc.inputs[7]; mixc.inputs[0].default_value = 0.0; mixc.blend_type = 'MULTIPLY'
def key_world(t, strength, tintc, fac):
    f = int(t * FPS); bg.inputs['Strength'].default_value = strength; bg.inputs['Strength'].keyframe_insert('default_value', frame=f)
    tint.default_value = (*tintc, 1); tint.keyframe_insert('default_value', frame=f); mixc.inputs[0].default_value = fac; mixc.inputs[0].keyframe_insert('default_value', frame=f)
key_world(0, 0.9, (1, 1, 1), 0.0); key_world(B['night'] - 0.3, 0.9, (1, 1, 1), 0.0); key_world(B['night'] + 1.2, 0.34, (0.32, 0.4, 0.72), 1.0)
key_world(B['morning'] - 0.2, 0.34, (0.32, 0.4, 0.72), 1.0); key_world(B['morning'] + 1.6, 0.75, (1.0, 0.78, 0.8), 1.0)
bpy.ops.object.light_add(type='SUN'); sun = bpy.context.object; sun.data.angle = math.radians(6); sun.rotation_euler = (math.radians(58), 0, math.radians(-35))
def key_sun(t, e, col):
    f = int(t * FPS); sun.data.energy = e; sun.data.color = col; sun.data.keyframe_insert('energy', frame=f); sun.data.keyframe_insert('color', frame=f)
key_sun(0, 2.2, (0.95, 0.95, 1.0)); key_sun(B['night'] - 0.3, 2.2, (0.95, 0.95, 1.0)); key_sun(B['night'] + 1.2, 1.1, (0.5, 0.6, 1.0))
key_sun(B['morning'] - 0.2, 1.1, (0.5, 0.6, 1.0)); key_sun(B['morning'] + 1.6, 2.6, (1.0, 0.72, 0.6))

snow = m_noise('snow', (0.82, 0.86, 0.92), (0.95, 0.97, 1.0), 0.4, 0.75, 0.15)
rock = m_noise('rock', (0.16, 0.17, 0.19), (0.3, 0.31, 0.34), 0.08, 0.9, 0.3)
water = m_plain('bay', (0.03, 0.06, 0.08), 0.06)
concrete = m_noise('concrete', (0.42, 0.42, 0.41), (0.52, 0.51, 0.5), 3, 0.9, 0.1)
towerm = m_noise('towerWall', (0.5, 0.49, 0.46), (0.6, 0.58, 0.55), 1.2, 0.9, 0.1)
dark = m_plain('dark', (0.03, 0.03, 0.035), 0.6); steel = m_plain('steel', (0.32, 0.33, 0.35), 0.35, 0.8)
rust = m_noise('rust', (0.28, 0.12, 0.06), (0.42, 0.2, 0.1), 4, 0.8, 0.3)
glass = bpy.data.materials.new('glass'); glass.use_nodes = True; gb = glass.node_tree.nodes['Principled BSDF']
gb.inputs['Base Color'].default_value = (0.8, 0.9, 1.0, 1); gb.inputs['Roughness'].default_value = 0.05; gb.inputs['Transmission Weight'].default_value = 1.0; gb.inputs['IOR'].default_value = 1.05
glass.blend_method = 'BLEND'

# ground, the bay, the mountains
box((40, 0, -0.1), (900, 900, 0.2), snow)
box((-330, 0, -0.35), (500, 900, 0.2), water)
def mountain(cx, cy, r, h, seed):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=48, y_subdivisions=48, size=1, location=(cx, cy, 0)); o = bpy.context.object; o.scale = (r * 2, r * 2, 1)
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(6)]
    for v in o.data.vertices:
        x, y = v.co.x * 2, v.co.y * 2; d = math.hypot(x, y)
        n = 1 + 0.18 * math.sin(x * 7 + ph[0]) * math.cos(y * 6 + ph[1]) + 0.08 * math.sin(x * 19 + ph[2] + y * 13)
        v.co.z = max(0.0, h * (1 - d) ** 1.4 * n) if d < 1 else 0.0
    me = o.data; me.materials.append(rock); me.materials.append(snow)
    for p in me.polygons: p.material_index = 1 if (p.center.z > h * 0.35 or p.normal.z > 0.82) else 0
    bpy.ops.object.shade_smooth(); return o
for (cx, cy, r, h, sd) in [(60, 260, 230, 210, 1), (-160, 300, 200, 240, 2), (320, 60, 140, 170, 3), (300, -160, 190, 200, 4),
                           (60, -330, 220, 190, 5), (-220, -320, 170, 160, 6), (450, 280, 260, 260, 7), (-60, 520, 300, 300, 8)]: mountain(cx, cy, r, h, sd)

# the tower: concrete slab, lit windows (texture), floor bands, a roof with the resident counter and an antenna
def m_windows(name, facade, lit, unlit, sx=3.0, sz=FH):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(geo.outputs['Position'], sp.inputs[0])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; nt.links.new(sp.outputs['X'], ad.inputs[0]); nt.links.new(sp.outputs['Y'], ad.inputs[1])
    dx = nt.nodes.new('ShaderNodeMath'); dx.operation = 'DIVIDE'; dx.inputs[1].default_value = sx; nt.links.new(ad.outputs[0], dx.inputs[0]); nt.links.new(dx.outputs[0], cb.inputs['X'])
    dz = nt.nodes.new('ShaderNodeMath'); dz.operation = 'DIVIDE'; dz.inputs[1].default_value = sz; nt.links.new(sp.outputs['Z'], dz.inputs[0]); nt.links.new(dz.outputs[0], cb.inputs['Y'])
    br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = 0.0; br.inputs['Scale'].default_value = 1.0; br.inputs['Brick Width'].default_value = 1.0; br.inputs['Row Height'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.28; br.inputs['Mortar Smooth'].default_value = 0.0; br.inputs['Bias'].default_value = -0.35
    br.inputs['Color1'].default_value = (*lit, 1); br.inputs['Color2'].default_value = (*unlit, 1); br.inputs['Mortar'].default_value = (0, 0, 0, 1)
    nt.links.new(cb.outputs[0], br.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs[7].default_value = (*facade, 1); nt.links.new(br.outputs['Fac'], mx.inputs[0]); nt.links.new(br.outputs['Color'], mx.inputs[6])
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; nt.links.new(br.outputs['Fac'], inv.inputs[1])
    nt.links.new(mx.outputs[2], bsdf.inputs['Base Color']); nt.links.new(br.outputs['Color'], bsdf.inputs['Emission Color'])
    em = nt.nodes.new('ShaderNodeMath'); em.operation = 'MULTIPLY'; em.inputs[1].default_value = 2.2; nt.links.new(inv.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], bsdf.inputs['Emission Strength'])
    bsdf.inputs['Roughness'].default_value = 0.8; return m
facade = m_windows('towerFacade', (0.47, 0.46, 0.43), (1.0, 0.62, 0.3), (0.02, 0.03, 0.05))
LITNODE = [n for n in facade.node_tree.nodes if n.type == 'MATH' and n.operation == 'MULTIPLY'][0]
def key_lit(t, v): LITNODE.inputs[1].default_value = v; LITNODE.inputs[1].keyframe_insert('default_value', frame=int(t * FPS))
key_lit(0, 1.2); key_lit(B['night'] - 0.3, 1.2); key_lit(B['night'] + 1.0, 3.0); key_lit(B['morning'], 3.0); key_lit(B['morning'] + 1.6, 0.6)
# the slab is built as four facade walls (so the floor-9 hallway can sit inside) + floors' slab edges
T = 0.3
box((0, -TD / 2, TOP / 2), (TW, T, TOP), facade); box((0, TD / 2, TOP / 2), (TW, T, TOP), facade)
for sx in (-1, 1):                                                       # end walls with a real hole for the floor-9 hallway window
    x = sx * TW / 2
    box((x, -4.95, TOP / 2), (T, 6.1, TOP), facade); box((x, 4.95, TOP / 2), (T, 6.1, TOP), facade)
    box((x, 0, (Z9 + 0.9) / 2), (T, 3.8, Z9 + 0.9), facade); box((x, 0, (TOP + Z9 + 2.6) / 2), (T, 3.8, TOP - Z9 - 2.6), facade)
    for sy in (-1, 1): box((x, sy * 1.425, Z9 + 1.75), (T, 0.95, 1.7), facade)
    box((x, 0, Z9 + 1.75), (0.06, 1.9, 1.7), glass); box((x - sx * 0.02, 0, Z9 + 0.87), (0.4, 2.0, 0.08), steel); box((x - sx * 0.02, 0, Z9 + 2.63), (0.4, 2.0, 0.08), steel)
for k in range(1, NFL + 1):                                                                                     # slab edges (perimeter bands only)
    for (cx_, cy_, w_, d_) in [(0, -TD / 2, TW + 0.5, 0.5), (0, TD / 2, TW + 0.5, 0.5), (-TW / 2, 0, 0.5, TD + 0.5), (TW / 2, 0, 0.5, TD + 0.5)]: box((cx_, cy_, k * FH - 0.05), (w_, d_, 0.18), concrete)
box((0, 0, TOP + 0.6), (TW + 0.6, TD + 0.6, 1.2), concrete)
for (x, y, w_, d_, h_) in [(-12, 2, 6, 5, 3.5), (8, -2, 4, 4, 2.6), (15, 3, 3, 3, 2.0)]: box((x, y, TOP + 1.2 + h_ / 2), (w_, d_, h_), concrete)
cyl((-12, 2, TOP + 12), 0.15, 16, steel, v=8); ball((-12, 2, TOP + 20.2), 0.35, m_emis('beacon', (1, 0.05, 0.03), 30))
# the resident counter: a black LED panel on the roof edge (the digits are drawn by the engine)
box((0, -8.7, SIGN[2]), (11, 0.4, 3.6), dark); box((0, -8.92, SIGN[2]), (10.4, 0.05, 3.0), m_emis('ledPanel', (0.05, 0.0, 0.0), 1.0, (0.02, 0.02, 0.02)))
for x in (-4.5, 4.5): box((x, -8.7, TOP + 0.6), (0.3, 0.3, 1.6), steel)
bpy.ops.object.text_add(location=(-4.6, -8.96, SIGN[2] + 1.05), rotation=(math.pi / 2, 0, 0)); tx = bpy.context.object; tx.data.body = 'RESIDENTS'; tx.data.size = 0.55; tx.data.extrude = 0.02
tx.data.materials.append(m_emis('ledLabel', (1.0, 0.85, 0.6), 4))
# steel shutter bands: one per floor per face, rolled up in a housing; they slam down floor by floor (top first)
shutm = m_brick('shutter', (0.36, 0.37, 0.39), (0.3, 0.31, 0.33), (0.16, 0.16, 0.18), 6, 4.0, 0.08)
SHUT = []
for k in range(NFL):
    zt = k * FH + 2.55
    for (cx, cy, ww, dd) in [(0, -TD / 2 - 0.25, TW, 0.12), (0, TD / 2 + 0.25, TW, 0.12), (-TW / 2 - 0.25, 0, 0.12, TD), (TW / 2 + 0.25, 0, 0.12, TD)]:
        box((cx, cy, zt + 0.12), (ww + 0.5 if dd < 1 else 0.36, dd + 0.5 if dd >= 1 else 0.36, 0.3), steel)               # housing
        o = box((cx, cy, zt), (ww, dd, 1.7), shutm); o.data = o.data.copy()
        for v in o.data.vertices: v.co.z -= 0.5                                                                         # origin at the top edge
        o.location.z = zt; SHUT.append((k, o))
def key_shutters():
    t0, t1 = B['slam'] - 0.15, B['window'] + 0.3; up0 = B['morning'] + 0.4
    for k, o in SHUT:
        tk = t0 + (NFL - 1 - k) / (NFL - 1) * (t1 - t0)
        for (t, s) in [(0, 0.02), (tk, 0.02), (tk + 0.18, 1.06), (tk + 0.26, 0.97), (tk + 0.32, 1.0), (up0 + k * 0.05, 1.0), (up0 + 1.1 + k * 0.05, 0.02)]:
            o.scale.z = s * 1.7; o.keyframe_insert('scale', index=2, frame=int(t * FPS))
key_shutters()
# entrance: canopy, doors with sliding bolts, a sign
box((0, -9.6, 3.3), (9, 3.4, 0.3), concrete); [cyl((sx * 4.2, -11.1, 1.6), 0.15, 3.3, steel, v=10) for sx in (-1, 1)]
box((0, -8.18, 1.4), (3.6, 0.12, 2.8), steel); box((0, -8.26, 1.4), (0.06, 0.06, 2.8), dark)
for sx in (-1, 1): box((sx * 0.95, -8.27, 1.9), (0.5, 0.06, 0.9), glass)
bolts = [box((sx * 0.4, -8.32, z), (0.6, 0.12, 0.14), m_plain('bolt', (0.75, 0.62, 0.2), 0.3, 1.0)) for z in (0.8, 1.4, 2.0) for sx in (-1, 1)]
for o in bolts:
    sx = 1 if o.location.x > 0 else -1; x1 = o.location.x
    for (t, x) in [(0, x1 + sx * 0.6), (B['lock'] - 0.05, x1 + sx * 0.6), (B['lock'] + 0.12, x1), (B['morning'] + 0.5, x1), (B['morning'] + 0.8, x1 + sx * 0.6)]:
        o.location.x = x; o.keyframe_insert('location', index=0, frame=int(t * FPS))
bpy.ops.object.text_add(location=(0, -11.3, 3.55), rotation=(math.pi / 2, 0, 0)); tx = bpy.context.object; tx.data.body = 'LAST TOWN ON EARTH'; tx.data.size = 0.36; tx.data.extrude = 0.04; tx.data.align_x = 'CENTER'
tx.data.materials.append(m_emis('towerSign', (0.7, 0.9, 1.0), 3))
lampE = m_emis('entranceLamp', (1.0, 0.8, 0.5), 6)
for sx in (-1, 1): box((sx * 2.6, -8.3, 3.0), (0.4, 0.2, 0.3), lampE)
bpy.ops.object.light_add(type='POINT', location=(0, -10.5, 3.0)); el = bpy.context.object; el.data.energy = 300; el.data.color = (1.0, 0.78, 0.5)
def spot(loc, aim, energy, col, size=math.radians(40)):                  # floodlights that wash the facade (prison-yard style)
    bpy.ops.object.light_add(type='SPOT', location=loc); o = bpy.context.object; o.data.energy = energy; o.data.color = col; o.data.spot_size = size; o.data.spot_blend = 0.6
    d = Vector(aim) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); return o
for sx in (-1, 1): spot((sx * 13, -17, 0.6), (sx * 9, -8, 26), 90000, (0.85, 0.92, 1.0))
for sy in (-1, 1): spot((-33, sy * 7, 0.6), (-22, sy * 4, 26), 70000, (0.85, 0.92, 1.0))

# the rest of the town: abandoned blocks with dark windows, containers by the harbour, the road and rail to the tunnel
ab = m_windows('abandoned', (0.3, 0.29, 0.28), (0.06, 0.05, 0.05), (0.01, 0.01, 0.015), 3.0, 3.0)
for (x, y, w_, d_, h_) in [(40, 20, 30, 14, 9), (36, -30, 16, 12, 6), (66, -46, 20, 12, 12), (-30, 40, 18, 10, 6), (95, 30, 14, 10, 5)]:
    box((x, y, h_ / 2), (w_, d_, h_), ab); box((x, y, h_ + 0.2), (w_ + 0.4, d_ + 0.4, 0.4), rust)
for k in range(10): box((-45 + random.uniform(-6, 6), -60 + k * 9, 1.3), (6.0, 2.4, 2.6), m_plain('cont%d' % k, random.choice([(0.5, 0.12, 0.08), (0.1, 0.25, 0.4), (0.55, 0.4, 0.1)]), 0.7))
box((-58, -10, 0.4), (30, 8, 0.8), concrete)                                                               # pier
road = m_noise('road', (0.08, 0.08, 0.09), (0.13, 0.13, 0.14), 20, 0.8, 0.05)
def strip(a, b_, wdt, m, z=0.02):
    a, b_ = Vector(a), Vector(b_); d = b_ - a; ang = math.atan2(d.y, d.x); box(((a.x + b_.x) / 2, (a.y + b_.y) / 2, z), (d.length, wdt, 0.04), m, (0, 0, ang))
strip((0, -12, 0), (40, -12, 0), 7, road); strip((40, -12, 0), (120, 10, 0), 7, road); strip((120, 10, 0), (PORTAL[0] - 4, PORTAL[1], 0), 7, road)
strip((-20, -16, 0), (PORTAL[0] - 4, PORTAL[1] - 4, 0), 0.12, steel, 0.08); strip((-20, -17.4, 0), (PORTAL[0] - 4, PORTAL[1] - 5.4, 0), 0.12, steel, 0.08)
# the tunnel portal in the mountain + a gate that shuts
ang = math.atan2(PORTAL[1] - 10, PORTAL[0] - 120)
P = Vector(PORTAL); dirv = Vector((math.cos(ang), math.sin(ang), 0)); side = Vector((-dirv.y, dirv.x, 0))
for s in (-1, 1): box(tuple(P + side * s * 6.0 + Vector((0, 0, 4.5))), (2.5, 2.0, 9), concrete, (0, 0, ang + math.pi / 2))
box(tuple(P + Vector((0, 0, 8.8))), (14.5, 2.4, 2.0), concrete, (0, 0, ang + math.pi / 2)); box(tuple(P + dirv * 1.6 + Vector((0, 0, 3.5))), (9.5, 0.4, 7), dark, (0, 0, ang + math.pi / 2))
bpy.ops.object.text_add(location=tuple(P - dirv * 1.3 + Vector((0, 0, 8.3)))); tx = bpy.context.object; tx.data.body = 'TUNNEL'; tx.data.size = 1.2; tx.data.extrude = 0.05; tx.data.align_x = 'CENTER'
tx.rotation_euler = (math.pi / 2, 0, ang - math.pi / 2); tx.data.materials.append(m_plain('tunTxt', (0.9, 0.9, 0.85), 0.5))
gate = box(tuple(P - dirv * 0.8 + Vector((0, 0, 7.3))), (9.2, 0.25, 6.5), m_brick('gate', (0.55, 0.12, 0.08), (0.5, 0.1, 0.07), (0.12, 0.05, 0.03), 5, 4.0, 0.06), (0, 0, ang + math.pi / 2))
gz0, gz1 = P.z + 7.3 + 3.3, P.z + 3.25
for (t, z) in [(0, gz0), (B['shuts'] - 0.25, gz0), (B['shuts'] + 0.15, gz1 - 0.05), (B['shuts'] + 0.25, gz1 + 0.08), (B['shuts'] + 0.32, gz1)]:
    gate.location.z = z; gate.keyframe_insert('location', index=2, frame=int(t * FPS))
tl = m_emis('tunnelLight', (1, 0.05, 0.02), 1)
for s in (-1, 1): ball(tuple(P + side * s * 6.0 - dirv * 1.3 + Vector((0, 0, 7.2))), 0.4, tl)
for s in (-1, 1): spot(tuple(P - dirv * 14 + side * s * 7 + Vector((0, 0, 9))), tuple(P + Vector((0, 0, 4))), 60000, (1.0, 0.62, 0.3), math.radians(55))
tlnode = tl.node_tree.nodes.get('Emission') or [n for n in tl.node_tree.nodes if 'Emission Strength' in n.inputs][0]
inp = tlnode.inputs['Strength'] if 'Strength' in tlnode.inputs else tlnode.inputs['Emission Strength']
for (t, v) in [(0, 0.5), (B['tunnel'], 0.5), (B['tunnel'] + 0.2, 25), (B['morning'] + 1, 25), (B['morning'] + 1.5, 0.5)]: inp.default_value = v; inp.keyframe_insert('default_value', frame=int(t * FPS))

# ------------------------------------------------------------------ floor 9: the hallway --------------------------
wallm = m_noise('hallWall', (0.52, 0.6, 0.5), (0.58, 0.65, 0.55), 2.0, 0.85, 0.05)
floorm = m_brick('lino', (0.28, 0.26, 0.24), (0.31, 0.29, 0.26), (0.18, 0.17, 0.16), 3.0, 0.5, 0.5)
ceilm = m_plain('ceiling', (0.75, 0.75, 0.72), 0.9); doorm = m_plain('door', (0.2, 0.22, 0.25), 0.5, 0.4)
HW = 1.3; X0, X1 = -TW / 2 + 0.2, TW / 2 - 0.2
box((0, 0, Z9 + 0.04), (TW - 0.4, TD - 0.4, 0.06), floorm); box((0, 0, Z9 + 2.8), (TW - 0.4, 2 * HW + 0.2, 0.1), ceilm)
box((0, 0, Z9 - 0.25), (TW, TD, 0.4), concrete); box((0, 0, Z9 + 3.05), (TW, TD, 0.4), concrete)
DOORS = [(-17, 1, 'STORE', (0.9, 0.75, 0.2)), (-13, -1, 'POLICE', (0.3, 0.5, 1.0)), (-9, 1, 'CLINIC', (0.95, 0.3, 0.3)), (-5, -1, 'SCHOOL', (0.4, 0.85, 0.4)),
         (VACANT_DOOR, -1, 'VACANT', None), (HERO_DOOR, -1, '914', None), (5.5, 1, '917', None), (9.5, -1, '918', None), (13.5, 1, '921', None), (17.5, -1, '922', None)]
doorx = {s: sorted([d[0] for d in DOORS if d[1] == s]) for s in (-1, 1)}
for s in (-1, 1):                                                        # walls with door openings (1.1 m wide, 2.2 m tall)
    xs = [X0] + sum([[d - 0.55, d + 0.55] for d in doorx[s]], []) + [X1]
    for a, c in zip(xs[::2], xs[1::2]): box(((a + c) / 2, s * HW, Z9 + 1.4), (c - a, 0.14, 2.8), wallm)
    for d in doorx[s]: box((d, s * HW, Z9 + 2.5), (1.1, 0.14, 0.6), wallm); box((d, s * (HW + 0.07), Z9 + 2.22), (1.25, 0.06, 0.1), steel)
DOOR = {}
for (x, s, label, col) in DOORS:
    hinge = bpy.data.objects.new('hinge%.1f' % x, None); sc.collection.objects.link(hinge); hinge.location = (x - 0.53, s * (HW + 0.02), Z9)
    d = box((x, s * (HW + 0.02), Z9 + 1.1), (1.04, 0.06, 2.18), doorm); bpy.context.view_layer.update(); mw = d.matrix_world.copy(); d.parent = hinge; d.matrix_world = mw
    knob = ball((x + 0.38, s * (HW - 0.03), Z9 + 1.05), 0.05, steel); mw = knob.matrix_world.copy(); knob.parent = hinge; knob.matrix_world = mw
    DOOR[label] = hinge
    lab = label if col else label
    bpy.ops.object.text_add(location=(x - 0.48, s * (HW - 0.09), Z9 + 2.45), rotation=(math.pi / 2, 0, 0 if s > 0 else math.pi)); tx = bpy.context.object
    if s < 0: tx.location.x = x + 0.48
    tx.data.body = lab; tx.data.size = 0.2 if col else 0.17; tx.data.extrude = 0.01
    tx.data.materials.append(m_emis('lab' + label, col, 3.5) if col else m_plain('labN' + label, (0.9, 0.9, 0.85), 0.5))
    if col: box((x, s * (HW - 0.09), Z9 + 2.5), (1.15, 0.03, 0.34), m_plain('signbg' + label, (0.05, 0.05, 0.06), 0.5))
def key_door(label, keys):
    h = DOOR[label]
    for (t, deg) in keys: h.rotation_euler.z = math.radians(deg); h.keyframe_insert('rotation_euler', index=2, frame=int(t * FPS))
key_door('914', [(0, -95), (B['ret'] + 0.95, -95), (B['ret'] + 1.2, 0)])                                   # your door: open, then slammed
key_door('STORE', [(0, 70), (B['ret'] + 0.3, 70), (B['ret'] + 0.6, 0)]); key_door('CLINIC', [(0, 60), (B['ret'] + 0.4, 60), (B['ret'] + 0.7, 0)])
key_door('VACANT', [(0, 0), (B['end'] - 1.3, 0), (B['end'] - 0.2, -16)])                                    # the empty apartment's door creaks open
# your apartment behind the open door: a warm lamp, a bed, a window; the vacant one: pitch dark
ap = m_noise('aptWall', (0.55, 0.45, 0.36), (0.6, 0.5, 0.4), 2, 0.9, 0.05)
box((HERO_DOOR, -HW - 2.6, Z9 + 1.4), (4.0, 0.14, 2.8), ap); box((HERO_DOOR - 2.0, -HW - 1.3, Z9 + 1.4), (0.14, 2.6, 2.8), ap); box((HERO_DOOR + 2.0, -HW - 1.3, Z9 + 1.4), (0.14, 2.6, 2.8), ap)
box((HERO_DOOR + 1.0, -HW - 1.9, Z9 + 0.3), (1.4, 1.8, 0.5), m_plain('bed', (0.5, 0.15, 0.12), 0.8)); box((HERO_DOOR - 1.2, -HW - 2.3, Z9 + 0.5), (0.6, 0.5, 1.0), m_plain('dresser', (0.35, 0.22, 0.12), 0.7))
bpy.ops.object.light_add(type='POINT', location=(HERO_DOOR - 1.2, -HW - 2.2, Z9 + 1.4)); al = bpy.context.object; al.data.energy = 60; al.data.color = (1.0, 0.65, 0.35); al.data.shadow_soft_size = 0.3
box((VACANT_DOOR, -HW - 2.6, Z9 + 1.4), (4.0, 0.14, 2.8), dark); box((VACANT_DOOR, -HW - 1.3, Z9 + 2.85), (4.0, 2.6, 0.1), dark)
for s in (-1, 1): box((VACANT_DOOR + s * 2.0, -HW - 1.3, Z9 + 1.4), (0.14, 2.6, 2.8), dark)
box((VACANT_DOOR, -HW - 1.3, Z9 + 0.03), (4.0, 2.6, 0.04), dark)
# the 10:15 clock, ceiling speakers, light panels, red emergency lamps (keyed)
cx = HERO_DOOR; cz = Z9 + 2.2
cyl((cx, HW - 0.1, cz), 0.32, 0.06, m_plain('clockFace', (0.92, 0.9, 0.84), 0.5), (math.pi / 2, 0, 0), 32); cyl((cx, HW - 0.08, cz), 0.35, 0.05, dark, (math.pi / 2, 0, 0), 32)
for (ang, L, wdt) in [(math.radians(-90 - 15 * 30 / 30 * 1 + 0), 0.0, 0)]: pass
def hand(angle_deg, L, wdt):                                                   # angle measured clockwise from 12
    a = math.radians(angle_deg); box((cx + math.sin(a) * L / 2, HW - 0.13, cz + math.cos(a) * L / 2), (wdt, 0.02, L), dark, (0, a, 0))
hand(10 * 30 + 15 * 0.5, 0.17, 0.035); hand(15 * 6, 0.26, 0.022)                                            # 10:15
panelM = m_emis('panel', (1.0, 0.95, 0.85), 6); redM = m_emis('redLamp', (1.0, 0.04, 0.02), 0.2)
for x in range(-20, 21, 4): box((x, 0, Z9 + 2.74), (1.2, 0.5, 0.04), panelM)
for x in (-16, -8, 0, 8, 16): box((x, HW - 0.12, Z9 + 2.6), (0.3, 0.12, 0.18), redM); box((x, -HW + 0.12, Z9 + 2.6), (0.3, 0.12, 0.18), redM)
for x in (-12, 0, 12): cyl((x, 0, Z9 + 2.72), 0.22, 0.12, m_plain('speaker', (0.15, 0.15, 0.16), 0.6), (0, 0, 0), 16); cyl((x, 0, Z9 + 2.65), 0.17, 0.03, m_plain('grille', (0.4, 0.4, 0.42), 0.4, 0.8), (0, 0, 0), 16)
def em_input(m):
    n = [n for n in m.node_tree.nodes if n.type == 'EMISSION' or 'Emission Strength' in n.inputs][0]; return n.inputs['Strength'] if 'Strength' in n.inputs else n.inputs['Emission Strength']
pin, rin = em_input(panelM), em_input(redM)
for (t, v) in [(0, 6), (B['speakers'] - 0.1, 6), (B['speakers'] + 0.05, 0.6), (B['speakers'] + 0.12, 4), (B['speakers'] + 0.2, 0.4), (B['morning'], 0.4), (B['morning'] + 0.8, 6)]:
    pin.default_value = v; pin.keyframe_insert('default_value', frame=int(t * FPS))
for (t, v) in [(0, 0.2), (B['speakers'] + 0.1, 0.2), (B['speakers'] + 0.25, 40), (B['morning'], 40), (B['morning'] + 0.8, 0.2)]:
    rin.default_value = v; rin.keyframe_insert('default_value', frame=int(t * FPS))
LIGHTS = []
for x in (-16, -8, 0, 8, 16):
    bpy.ops.object.light_add(type='AREA', location=(x, 0, Z9 + 2.6)); L_ = bpy.context.object; L_.data.size = 1.6; L_.data.energy = 140; L_.data.color = (1, 0.93, 0.82); LIGHTS.append(L_)
for L_ in LIGHTS:
    for (t, e, c) in [(0, 140, (1, 0.93, 0.82)), (B['speakers'] - 0.1, 140, (1, 0.93, 0.82)), (B['speakers'] + 0.25, 70, (1.0, 0.08, 0.05)), (B['morning'], 70, (1.0, 0.08, 0.05)), (B['morning'] + 0.8, 140, (1, 0.93, 0.82))]:
        L_.data.energy = e; L_.data.color = c; f = int(t * FPS); L_.data.keyframe_insert('energy', frame=f); L_.data.keyframe_insert('color', frame=f)
# the hallway's own window shutter (inside the end window) is the floor-9 band outside: same keys

# ------------------------------------------------------------------ the Whiteout ------------------------------------
fogm = bpy.data.materials.new('whiteout'); fogm.use_nodes = True; fn = fogm.node_tree.nodes; fl = fogm.node_tree.links; fn.remove(fn['Principled BSDF'])
tr = fn.new('ShaderNodeBsdfTransparent'); emn = fn.new('ShaderNodeEmission'); emn.inputs['Color'].default_value = (0.86, 0.9, 0.95, 1); emn.inputs['Strength'].default_value = 0.9
mix = fn.new('ShaderNodeMixShader'); tcn = fn.new('ShaderNodeTexCoord'); nz = fn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6.0; nz.inputs['Detail'].default_value = 6
fl.new(tcn.outputs['Generated'], nz.inputs['Vector'])
sepn = fn.new('ShaderNodeSeparateXYZ'); fl.new(tcn.outputs['Generated'], sepn.inputs[0])
vg = fn.new('ShaderNodeFloatCurve'); fl.new(sepn.outputs['Y'], vg.inputs['Value'])
cv = vg.mapping.curves[0]; cv.points[0].location = (0, 1); cv.points[1].location = (1, 0); cv.points.new(0.55, 0.75); vg.mapping.update()
eg = fn.new('ShaderNodeFloatCurve'); fl.new(sepn.outputs['X'], eg.inputs['Value'])
cv2 = eg.mapping.curves[0]; cv2.points[0].location = (0, 0); cv2.points[1].location = (1, 0); cv2.points.new(0.2, 1); cv2.points.new(0.8, 1); eg.mapping.update()
m1 = fn.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; fl.new(vg.outputs[0], m1.inputs[0]); fl.new(eg.outputs[0], m1.inputs[1])
cr = fn.new('ShaderNodeMapRange'); cr.inputs['From Min'].default_value = 0.3; cr.inputs['From Max'].default_value = 0.62; fl.new(nz.outputs['Fac'], cr.inputs['Value'])
m2 = fn.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; fl.new(m1.outputs[0], m2.inputs[0]); fl.new(cr.outputs['Result'], m2.inputs[1])
m3 = fn.new('ShaderNodeMath'); m3.operation = 'MULTIPLY'; m3.inputs[1].default_value = 0.85; fl.new(m2.outputs[0], m3.inputs[0])
fl.new(m3.outputs[0], mix.inputs[0]); fl.new(tr.outputs[0], mix.inputs[1]); fl.new(emn.outputs[0], mix.inputs[2]); fl.new(mix.outputs[0], fn['Material Output'].inputs['Surface'])
fogm.blend_method = 'BLEND'
FOG = []
for k in range(22):
    bpy.ops.mesh.primitive_plane_add(size=1); p = bpy.context.object; p.scale = (1, 1, 1); p.data.materials.append(fogm)
    p.rotation_euler = (math.pi / 2, 0, math.pi / 2); p.scale = (random.uniform(180, 280), random.uniform(45, 80), 1)
    for v in p.data.vertices: v.co.y += 0.5                                       # bottom edge on the ground
    y0 = random.uniform(-110, 110); xe = random.uniform(-120, -12); zs = 0.0
    p.location = (xe - 330, y0, zs); FOG.append((p, xe))
for p, xe in FOG:
    t0, t1 = B['whiteout'] - 0.5, B['bay'] + 0.9
    for (t, x) in [(0, xe - 330), (t0, xe - 330), (t1, xe), (B['morning'] - 0.2, xe + 25), (B['morning'] + 1.5, xe + 400)]:
        p.location.x = x; p.keyframe_insert('location', index=0, frame=int(t * FPS))

# ------------------------------------------------------------------ animation curves: linear, camera ---------------
for ob in bpy.data.objects:
    ad_ = ob.animation_data
    if ad_ and ad_.action:
        for fc in ad_.action.fcurves:
            if fc.data_path in ('scale',) or 'rotation' in fc.data_path: continue
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
bpy.ops.object.camera_add(location=CAM[0][1]); cam = bpy.context.object; cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24; cam.data.clip_start = 0.05; cam.data.clip_end = 6000; sc.camera = cam
tgt = bpy.data.objects.new('camTarget', None); sc.collection.objects.link(tgt)
tc_ = cam.constraints.new('TRACK_TO'); tc_.target = tgt; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 5.6; cam.data.dof.focus_object = tgt
for f in range(NF):
    p_, l_, lens = cam_at(f / FPS); cam.location = p_; tgt.location = l_; cam.data.lens = lens
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f); cam.data.keyframe_insert('lens', frame=f)
for ob in (cam, tgt, cam.data):
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# camera + actor tracks + beats for the engine
track, actors, vis = [], {k: [] for k in ACTORS}, {k: [] for k in ACTORS}
for f in range(NF):
    sc.frame_set(f); M = cam.matrix_world; t = f / FPS
    track.append(dict(C=[round(v, 4) for v in M.translation], R=[[round(M[r][c], 5) for c in range(3)] for r in range(3)], tanh=round(12.0 / cam.data.lens, 6)))
    for k, fn_ in ACTORS.items(): p_, v = fn_(t); actors[k].append([round(c, 3) for c in p_]); vis[k].append(v)
json.dump(dict(fps=FPS, frames=NF, track=track, actors=actors, vis=vis, beats=B, sign=list(SIGN), portal=list(PORTAL)), open(os.path.join(OUT, 'camera.json'), 'w'))
print('tracks written', NF, flush=True)

sc.frame_start, sc.frame_end = START, END; sc.render.use_persistent_data = True
LIST = [int(v) for v in arg('--list', '').split(',') if v]
if LIST:
    for f in LIST: sc.frame_set(f); sc.render.filepath = os.path.join(OUT, 'f%04d.jpg' % f); bpy.ops.render.render(write_still=True)
    print('list done', flush=True)
else:
    sc.render.use_overwrite = False; sc.render.use_placeholder = True; sc.render.filepath = os.path.join(OUT, 'f####'); bpy.ops.render.render(animation=True); print('sequence done', flush=True)
