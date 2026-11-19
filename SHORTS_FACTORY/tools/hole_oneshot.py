"""WHAT IF YOU FELL INTO A HOLE THROUGH THE EARTH? one continuous camera move (two white flashes hide set swaps).
  a sunny field with a hole and a '42 MIN' sign -> up into the sky, flash -> a cutaway Earth in space with the tunnel
  through its centre -> dive to the top, flash -> back at the hole: you step off -> the fall: strata stream past, the
  12 KM marker (the deepest hole ever dug), the mantle glows, the white-hot core -> slow-motion at the centre ->
  gravity flips, you rise and stop at the top -> the far side: a night ocean, a buoy 'INDIAN OCEAN' -> you fall back
  in -> down again, with air: you end up floating at the centre.
The tunnel is drawn compressed (900 m from rim to centre); the numbers on screen are the real ones (see sources.txt).
The far half reuses the same shaft: after the centre the top of the shaft swaps from the field to the ocean.
Every camera key is tied to a cue word in work/words.json, so a new voiceover re-times the whole shot.
Run: $BLENDER -b --factory-startup -P tools/hole_oneshot.py -- <out> --words <words.json> [--scale 0.5] [--spp 6]
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
ISL = F2.ISL; box, cyl, cone, ball = ISL.box, ISL.cyl, ISL.cone, ISL.ball; m_plain, m_noise, m_emis = F2.m_plain, F2.m_noise, ISL.m_emis
os.makedirs(OUT, exist_ok=True); random.seed(11)

# ------------------------------------------------------------------ beats from the voice ---------------------------
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
CUES = [('hook', 'jump'), ('here', 'here'), ('minutes', 'minutes'), ('picture', 'picture'), ('tunnel', 'tunnel'), ('no', 'no'), ('step', 'step'),
        ('edge', 'edge'), ('fall', 'fall'), ('weightless', 'weightless'), ('under', 'under'), ('deepest', 'deepest'), ('twelve', 'twelve'),
        ('about', 'about'), ('center', 'center'), ('hot', 'hot'), ('eight', 'eight'), ('then', 'then'), ('flips', 'flips'), ('slows', 'slows'),
        ('rise', 'rise'), ('stop', 'stop'), ('top', 'top'), ('fortytwo', 'fortytwo'), ('really', 'really'), ('thirtyeight', 'thirtyeight'),
        ('jump2', 'jump'), ('us', 'us'), ('pop', 'pop'), ('indian', 'indian'), ('nobody', 'nobody'), ('fall2', 'fall'), ('forever', 'forever'),
        ('air', 'air'), ('stuck', 'stuck'), ('floating', 'floating'), ('would', 'would')]
B = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while j < len(ws) and norm(ws[j]['word']) != cue: j += 1
    if j == len(ws): raise SystemExit('cue word not found: ' + cue)
    B[key] = ws[j]['start']; wi = j + 1
B['end'] = DUR
B['flashA'] = B['picture'] + 0.42          # field -> cutaway Earth
B['flashB'] = B['step'] + 0.22             # cutaway Earth -> field
B['swap'] = B['hot']                       # top of the shaft: field -> ocean (camera is deep in the core)
B['offEdge'] = B['edge'] + 0.15
print('beats', json.dumps({k: round(v, 2) for k, v in B.items()}), flush=True)

def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def keyed(keys, t, fn=ease):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1: u = fn((t - t0) / max(1e-6, t1 - t0)); return tuple(x + (y - x) * u for x, y in zip(a, b))
    return keys[-1][1]
def pchip(keys):                                       # monotone cubic through (t, v) keys -> f(t)
    T = [k[0] for k in keys]; V = [k[1] for k in keys]; n = len(T); d = [(V[i + 1] - V[i]) / (T[i + 1] - T[i]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else 2 / (1 / d[i - 1] + 1 / d[i]) for i in range(1, n - 1)] + [d[-1]]
    def f(t):
        if t <= T[0]: return V[0]
        if t >= T[-1]: return V[-1]
        i = max(k for k in range(n - 1) if T[k] <= t); h = T[i + 1] - T[i]; s = (t - T[i]) / h
        return (2 * s ** 3 - 3 * s ** 2 + 1) * V[i] + (s ** 3 - 2 * s ** 2 + s) * h * m[i] + (-2 * s ** 3 + 3 * s ** 2) * V[i + 1] + (s ** 3 - s ** 2) * h * m[i + 1]
    return f

# ------------------------------------------------------------------ layout (metres) ---------------------------------
R_SH = 4.5                    # shaft radius
DEPTH = 900.0                 # rim -> centre (drawn compressed)
ZC = -DEPTH                   # the centre of the Earth
PLAQ = -131.0                 # the 12 km marker
G = Vector((20000.0, 0.0, 0.0)); GR = 10.0          # the cutaway Earth model in space
HERO0 = (0.0, -(R_SH + 0.75), 0.25)    # standing at the rim (collar top is z = 0.25)
TOPZ = 1.1                    # hovering over the rim on the far side

# the hero: one z(t) curve per trip
b = B
zA = pchip([(b['offEdge'], 0.6), (b['offEdge'] + 0.6, -1.2), (b['weightless'], -22), (b['under'], -70), (b['under'] + 0.7, -100), (b['twelve'] - 0.9, -124),
            (b['twelve'] + 0.6, -136), (b['about'] + 0.4, -200), (b['center'] - 0.8, -560), (b['center'], ZC + 0.2)])
zB = pchip([(b['flips'] + 0.25, ZC - 1.6), (b['slows'], ZC + 120), (b['rise'], -260), (b['rise'] + 0.8, -70), (b['stop'] - 0.5, -6), (b['stop'], TOPZ)])
zC = pchip([(b['fall2'], TOPZ), (b['fall2'] + 0.5, -2.0), (b['forever'] + 0.4, -40), (b['air'], -120), (b['stuck'], -700), (b['floating'] - 0.2, ZC - 0.4), (b['floating'] + 0.6, ZC)])
def hero_pos(t):
    if b['flashA'] <= t < b['flashB']: return HERO0, 0
    if t < b['edge']: return HERO0, 1
    if t < b['offEdge']: u = ease((t - b['edge']) / 0.15); return (0, HERO0[1] + (-(R_SH - 1.4) - HERO0[1]) * u, 0.25 + 0.35 * u), 1
    if t < b['center']: u = ease((t - b['offEdge']) / 1.6); return (0.0, -(R_SH - 1.4) + (R_SH - 1.7) * u, zA(t)), 1
    if t < b['flips'] + 0.25:                                                         # slow motion at the centre: drifting through
        u = (t - b['center']) / (b['flips'] + 0.25 - b['center']); return (0.25 * math.sin(u * 3), -0.3 + 0.2 * u, ZC + 0.2 - 1.8 * u), 1
    if t < b['stop']: return (0.0, -0.1, zB(t)), 1
    if t < b['fall2']: return (0.0, -0.1, TOPZ + 0.12 * math.sin((t - b['stop']) * 2.2) + (0.35 * math.sin(math.pi * min(1, max(0, (t - b['pop']) / 0.5))) if t > b['pop'] else 0)), 1
    if t < b['floating'] + 0.6: return (0.0, -0.1, zC(t)), 1
    return (0.12 * math.sin(t * 0.9), -0.1, ZC + 0.18 * math.sin(t * 1.3)), 1
def hero_roll(t):                                                                     # head-over-heels when gravity flips
    if b['flips'] - 0.2 < t < b['flips'] + 0.9: return math.pi * 2 * ease((t - b['flips'] + 0.2) / 1.1)
    return 0.0
ACTORS = dict(hero=hero_pos)

# ------------------------------------------------------------------ camera (t, position, look-at, lens) -------------
def H(t): return Vector(hero_pos(t)[0])
CAM = [(0.0, (2.4, -12.6, 1.8), (0.6, -4.2, 1.0), 26), (b['here'] + 0.2, (1.9, -11.4, 2.0), (0.4, -4.0, 0.8), 26),
       (b['minutes'], (1.4, -9.6, 4.6), (0.0, -1.0, -2.5), 24), (b['picture'] + 0.05, (1.2, -9.2, 5.0), (0.0, -1.0, -2.0), 24),
       (b['flashA'], (6.0, -40.0, 160.0), (0.0, 0.0, 0.0), 24),
       # the cutaway Earth (teleport at the flash)
       (b['flashA'] + 0.001, tuple(G + Vector((24, -52, 16))), tuple(G), 40), (b['no'], tuple(G + Vector((38, -42, 11))), tuple(G), 40),
       (b['step'] - 0.1, tuple(G + Vector((42, -34, 14))), tuple(G + Vector((0, 0, 2))), 40), (b['flashB'], tuple(G + Vector((0.4, -0.9, GR + 0.9))), tuple(G + Vector((0, 0, GR))), 40),
       # back at the hole
       (b['flashB'] + 0.001, (1.7, -10.0, 2.6), (0.0, -4.4, 0.6), 26), (b['offEdge'] + 0.15, (1.3, -7.4, 3.8), (0.0, -2.6, -0.5), 24)]
FALL = [  # hero-relative camera during the trips: (t, cam offset, look offset, lens)
    (b['offEdge'] + 0.6, None), (b['fall'] + 0.35, ((0.9, -2.2, 3.6), (0, 0.2, -6), 24)), (b['weightless'] - 0.1, ((0.9, -2.2, 3.7), (0, 0.2, -6), 24)),
    (b['weightless'] + 0.6, ((1.0, -2.0, -3.6), (0, 0, 0.5), 22)), (b['under'] + 0.3, ((1.0, -2.0, -3.6), (0, 0, 0.5), 22)),
    (b['deepest'], ((2.3, 3.0, 0.7), (0, -4.0, 0.0), 20)), (b['twelve'] + 0.7, ((2.3, 3.0, 0.6), (0, -4.0, -0.2), 20)),
    (b['about'] + 0.2, ((0.9, -2.2, 3.6), (0, 0.2, -8), 22)), (b['center'] - 0.35, ((0.8, -2.0, 3.4), (0, 0.1, -6), 22))]
def orbit(t, t0, t1, r, a0, a1, dz, lens, ctr=(0, 0, ZC)):
    u = ease((t - t0) / (t1 - t0)); a = math.radians(a0 + (a1 - a0) * u)
    return Vector((ctr[0] + r * math.cos(a), ctr[1] + r * math.sin(a), ctr[2] + dz)), Vector((ctr[0], ctr[1] - 0.2, ctr[2] + 0.4)), lens
def cam_keys(keys, t):
    for a, c in zip(keys, keys[1:]):
        if t <= c[0]:
            u = ease((t - a[0]) / max(1e-6, c[0] - a[0])); m = lambda A, C: tuple(x + (y - x) * u for x, y in zip(A, C))
            return Vector(m(a[1], c[1])), Vector(m(a[2], c[2])), a[3] + (c[3] - a[3]) * u
    return Vector(keys[-1][1]), Vector(keys[-1][2]), keys[-1][3]
def rel_keys(keys, t):                                  # hero-relative keys -> world
    pts = [k for k in keys if k[1]]
    if t <= pts[0][0]: o, l, n = pts[0][1]
    else:
        o, l, n = pts[-1][1]
        for a, c in zip(pts, pts[1:]):
            if t <= c[0]:
                u = ease((t - a[0]) / (c[0] - a[0])); o = Vector(a[1][0]).lerp(Vector(c[1][0]), u); _L = Vector(a[1][0]).length * (1 - u) + Vector(c[1][0]).length * u; o = tuple(o.normalized() * _L) if o.length > 0.1 else tuple(o); l = tuple(x + (y - x) * u for x, y in zip(a[1][1], c[1][1])); n = a[1][2] + (c[1][2] - a[1][2]) * u; break
    h = H(t); return h + Vector(o), h + Vector(l), n
def blend(A, Bv, u): u = ease(u); return A[0].lerp(Bv[0], u), A[1].lerp(Bv[1], u), A[2] + (Bv[2] - A[2]) * u
def cam_at(t):
    if t < b['offEdge'] + 0.15: return cam_keys(CAM, t)
    if t < b['fall'] + 0.35:                                             # from the rim, dive in after the hero
        return blend(cam_keys(CAM, b['offEdge'] + 0.15), rel_keys(FALL, b['fall'] + 0.35), (t - b['offEdge'] - 0.15) / (b['fall'] + 0.2 - b['offEdge']))
    if t < b['center'] - 0.35: return rel_keys(FALL, t)
    if t < b['flips'] + 0.25:                                            # slow orbit in the core
        if t < b['center'] + 0.6:
            p, l, n = blend(rel_keys(FALL, b['center'] - 0.35), orbit(b['center'] + 0.6, b['center'] + 0.6, b['flips'] + 0.25, 4.6, -100, 20, 0.9, 22), (t - b['center'] + 0.35) / 0.95)
            rmax = 2.2 if p.z > ZC + 7.5 else 2.2 + (ZC + 7.5 - p.z) * 1.2
            rr = math.hypot(p.x, p.y)
            if rr > rmax: p = Vector((p.x * rmax / rr, p.y * rmax / rr, p.z))
            return p, l, n
        return orbit(t, b['center'] + 0.6, b['flips'] + 0.25, 4.6, -100, 20, 0.9, 22)
    rise_rel = lambda tt: (H(tt) + Vector((0.9, -2.2, 3.6)), H(tt) + Vector((0, 0.2, -4.0)), 22)
    if t < b['slows']: return blend(orbit(b['flips'] + 0.25, b['center'] + 0.6, b['flips'] + 0.25, 4.6, -100, 20, 0.9, 22), rise_rel(t), (t - b['flips'] - 0.25) / (b['slows'] - b['flips'] - 0.25))
    TOP = [(b['stop'] - 0.7, None), (b['stop'] + 0.2, (2.0, -6.4, 3.4), (0, 0, 1.0), 26), (b['top'] + 0.5, (2.6, -5.6, 2.6), (0, 0, 1.2), 28),
           (b['really'], (-2.4, -5.8, 2.2), (0, 0, 1.3), 30), (b['jump2'] - 0.2, (-3.2, -6.4, 2.0), (0, 0, 1.3), 30),
           (b['indian'] + 0.2, (-1.5, -17.5, 3.4), (-1.6, -3.4, 1.4), 26), (b['nobody'] - 0.1, (-1.4, -17.0, 3.3), (-1.6, -3.4, 1.4), 26),
           (b['fall2'] - 0.1, (1.3, -3.6, 2.4), (0, 0, 1.0), 26), (b['fall2'] + 0.5, (0.5, -1.6, 3.6), (0, 0.2, -10.0), 24), (b['air'] - 0.3, (0.5, -1.6, 3.4), (0, 0.2, -30.0), 24)]
    if t < b['stop'] - 0.7: return rise_rel(t)
    if t < b['stop'] + 0.2: return blend(rise_rel(b['stop'] - 0.7), cam_keys([k for k in TOP if k[1]], b['stop'] + 0.2), (t - b['stop'] + 0.7) / 0.9)
    if t < b['air'] - 0.3: return cam_keys([k for k in TOP if k[1]], t)
    dive = lambda tt: (H(tt) + Vector((0.9, -2.2, 3.7)), H(tt) + Vector((0, 0.2, -8.0)), 22)
    if t < b['air'] + 0.4: return blend(cam_keys([k for k in TOP if k[1]], b['air'] - 0.3), dive(b['air'] + 0.4), (t - b['air'] + 0.3) / 0.7)
    if t < b['floating'] - 0.3: return dive(t)
    END_ORB = lambda tt: orbit(tt, b['floating'] + 0.3, b['end'], 4.2, -96, -60, 0.7, 24)
    if t < b['floating'] + 0.3: return blend(dive(b['floating'] - 0.3), END_ORB(b['floating'] + 0.3), (t - b['floating'] + 0.3) / 0.6)
    p, l, n = END_ORB(t); push = ease((t - b['would']) / 2.0) if t > b['would'] else 0; return p.lerp(l, 0.12 * push), l, n

FY = 0.72                                              # where your feet sit on screen (fraction of the height)
cam_raw = cam_at
def cam_at(t):
    p, l, n = cam_raw(t)
    if b['flashA'] - 0.42 <= t < b['flashB'] + 0.02: return p, l, n
    h = H(t); v = h - p; dist = v.length; d0 = v.normalized(); Z = Vector((0, 0, 1))
    right = d0.cross(Z); right = right.normalized() if right.length > 1e-3 else Vector((1, 0, 0)); up = right.cross(d0).normalized()
    th = math.atan((FY - 0.5) * 2 * (12.0 / n)); d = d0 * math.cos(th) + up * math.sin(th)
    fxr = 0.1 * min(1, max(0, (t - b['jump2'] + 0.3) / 1.0)) * (1 - min(1, max(0, (t - b['nobody'] + 0.2) / 0.8)))   # you right of centre: the buoy comes in
    ph = math.atan(fxr * 2 * (12.0 / n) * 9 / 16); right2 = d.cross(up).normalized(); d = (d * math.cos(ph) - right2 * math.sin(ph)).normalized()
    w = 1.0
    if t < b['flashA'] - 0.42: w = 1.0 - min(1, max(0, (t - (b['flashA'] - 0.9)) / 0.48))
    return p, l.lerp(p + d * max(dist, 2.0), w), n

# ------------------------------------------------------------------ the world -------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True); ISL._T.clear()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 3
sc.render.resolution_x, sc.render.resolution_y = int(1080 * SCALE), int(1920 * SCALE)
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = -0.4
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92; sc.render.fps = FPS
sc.cycles.light_sampling_threshold = 0.05; sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.45

SETS = {k: [] for k in ('field', 'space', 'ocean', 'plaque')}
class group:
    def __init__(s, name): s.name = name
    def __enter__(s): s.before = set(bpy.data.objects)
    def __exit__(s, *a): SETS[s.name] += [o for o in bpy.data.objects if o not in s.before]

# world: day sky / space / night (keyed), stars from a voronoi
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']; L = nt.links.new
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L(tc.outputs['Generated'], sep.inputs[0])
ramp = nt.nodes.new('ShaderNodeValToRGB'); L(sep.outputs['Z'], ramp.inputs[0])
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.55, 0.75, 1.0, 1); ramp.color_ramp.elements[1].position = 0.55; ramp.color_ramp.elements[1].color = (0.09, 0.3, 0.9, 1)
night = nt.nodes.new('ShaderNodeMix'); night.data_type = 'RGBA'; L(ramp.outputs['Color'], night.inputs[6]); night.inputs[7].default_value = (0.02, 0.04, 0.11, 1)
vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 420; L(tc.outputs['Generated'], vor.inputs['Vector'])
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.035; mr.inputs['From Max'].default_value = 0.0; L(vor.outputs['Distance'], mr.inputs['Value'])
stars = nt.nodes.new('ShaderNodeMath'); stars.operation = 'MULTIPLY'; L(mr.outputs['Result'], stars.inputs[0])
add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'; add.inputs[0].default_value = 1.0; L(night.outputs[2], add.inputs[6])
sv = nt.nodes.new('ShaderNodeCombineXYZ'); L(stars.outputs[0], sv.inputs[0]); L(stars.outputs[0], sv.inputs[1]); L(stars.outputs[0], sv.inputs[2]); L(sv.outputs[0], add.inputs[7])
L(add.outputs[2], bg.inputs['Color'])
def key_world(t, nightv, starv, strength, const=True):
    f = int(round(t * FPS))
    for sock, v in ((night.inputs[0], nightv), (stars.inputs[1], starv), (bg.inputs['Strength'], strength)):
        sock.default_value = v; sock.keyframe_insert('default_value', frame=f)
key_world(0, 0.0, 0.0, 1.0); key_world(b['flashA'] - 0.02, 0.0, 0.0, 1.0); key_world(b['flashA'], 1.0, 6.0, 1.0)
key_world(b['flashB'] - 0.02, 1.0, 6.0, 1.0); key_world(b['flashB'], 0.0, 0.0, 1.0); key_world(b['swap'] - 0.02, 0.0, 0.0, 1.0); key_world(b['swap'], 1.0, 2.0, 1.6)
bpy.ops.object.light_add(type='SUN'); sun = bpy.context.object; sun.data.angle = math.radians(3); sun.rotation_euler = (math.radians(40), 0, math.radians(30))
def key_sun(t, e, col):
    f = int(round(t * FPS)); sun.data.energy = e; sun.data.color = col; sun.data.keyframe_insert('energy', frame=f); sun.data.keyframe_insert('color', frame=f)
key_sun(0, 3.4, (1.0, 0.95, 0.85)); key_sun(b['swap'] - 0.02, 3.4, (1.0, 0.95, 0.85)); key_sun(b['swap'], 0.35, (0.55, 0.65, 1.0))

grass = m_noise('grass', (0.13, 0.36, 0.08), (0.24, 0.52, 0.12), 0.8, 0.9, 0.0)
dirt = m_noise('dirt', (0.22, 0.14, 0.08), (0.34, 0.22, 0.12), 2.0, 0.9, 0.0)
concrete = m_noise('concrete', (0.48, 0.48, 0.47), (0.6, 0.59, 0.57), 3, 0.9, 0.0)
yellow = m_plain('hazard', (0.95, 0.68, 0.05), 0.5); black = m_plain('black', (0.02, 0.02, 0.02), 0.6); white = m_plain('white', (0.9, 0.9, 0.88), 0.5)
wood = m_plain('wood', (0.32, 0.2, 0.1), 0.8); steel = m_plain('steel', (0.4, 0.41, 0.43), 0.35, 0.8)
trunk = m_plain('trunk', (0.25, 0.15, 0.08), 0.9); leaf1 = m_plain('leaf1', (0.09, 0.3, 0.07), 0.8); leaf2 = m_plain('leaf2', (0.14, 0.4, 0.1), 0.8)

def text(body, loc, size, m, rot=(math.pi / 2, 0, 0), ext=0.01):
    bpy.ops.object.text_add(location=loc); tx = bpy.context.object; tx.rotation_euler = rot; tx.data.body = body; tx.data.size = size
    tx.data.align_x = 'CENTER'; tx.data.align_y = 'CENTER'; tx.data.extrude = ext; tx.data.materials.append(m); return tx

# the collar around the hole (shared by both ends)
def ring(z0, z1, r0, r1, m, v=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=r1, depth=z1 - z0, vertices=v, location=(0, 0, (z0 + z1) / 2)); o = bpy.context.object
    bpy.ops.mesh.primitive_cylinder_add(radius=r0, depth=(z1 - z0) + 0.2, vertices=v, location=(0, 0, (z0 + z1) / 2)); c = bpy.context.object
    md = o.modifiers.new('cut', 'BOOLEAN'); md.object = c; md.operation = 'DIFFERENCE'; bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier='cut')
    bpy.data.objects.remove(c); o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o
ring(-1.6, 0.25, R_SH, R_SH + 0.55, concrete)
for k in range(16):                                                          # hazard stripes on the collar
    a = k / 16 * 2 * math.pi; box((math.cos(a) * (R_SH + 0.56), math.sin(a) * (R_SH + 0.56), 0.05), (0.02, 0.5, 0.26), yellow if k % 2 == 0 else black, (0, 0, a))
ring(0.24, 0.3, R_SH - 0.02, R_SH + 0.6, steel)

# ---- the field (day, this side)
with group('field'):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=80, size=1, location=(0, 0, 0)); gnd = bpy.context.object; gnd.scale = (900, 900, 1)
    for v in gnd.data.vertices:
        x, y = v.co.x * 900, v.co.y * 900; d = math.hypot(x, y)
        v.co.z = 0 if d < 30 else min(1, (d - 30) / 120) * (6 * math.sin(x * 0.012 + 1) * math.cos(y * 0.01) + 4 * math.sin(x * 0.03 + y * 0.02))
    # cut the hole out of the ground
    bpy.ops.mesh.primitive_cylinder_add(radius=R_SH + 0.5, depth=4, vertices=64, location=(0, 0, 0)); hc = bpy.context.object
    md = gnd.modifiers.new('hole', 'BOOLEAN'); md.object = hc; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; bpy.context.view_layer.objects.active = gnd; bpy.ops.object.modifier_apply(modifier='hole'); bpy.data.objects.remove(hc)
    gnd.data.materials.append(grass); bpy.ops.object.shade_smooth()
    ring(-0.3, 0.02, R_SH + 0.55, R_SH + 1.6, dirt)
    for (x, y, h) in [(-14, 9, 9), (-19, 16, 12), (12, 14, 10), (18, 7, 8), (25, 24, 13), (-30, 32, 14), (6, 40, 12), (-8, 55, 15), (34, -6, 9), (-26, -4, 10),
                      (45, 50, 16), (-50, 60, 18), (60, 20, 14), (-60, 18, 13), (20, 70, 17)]:
        F2.tree(x, y, 0, h, trunk, leaf1, leaf2)
    for k in range(60):                                                      # far trees / bushes
        a = random.uniform(0, 2 * math.pi); r = random.uniform(80, 260); F2.tree(r * math.cos(a), r * math.sin(a) + 40, 0, random.uniform(10, 20), trunk, leaf1, leaf2)
    # the sign: THE OTHER SIDE / 42 MIN, with an arrow pointing down at the hole
    SX, SY = 3.7, -6.6
    for dx in (-0.75, 0.75): box((SX + dx, SY, 0.9), (0.09, 0.09, 1.8), wood)
    box((SX, SY, 1.75), (1.9, 0.07, 0.95), white); box((SX, SY + 0.04, 1.75), (2.0, 0.05, 1.05), black)
    text('THE OTHER SIDE', (SX, SY - 0.05, 1.98), 0.22, black, ext=0.004); text('42 MIN', (SX, SY - 0.05, 1.62), 0.42, m_plain('red', (0.8, 0.06, 0.04), 0.5), ext=0.004)
    cone((SX - 1.25, SY - 0.02, 1.15), 0.18, 0.32, m_plain('red2', (0.8, 0.06, 0.04), 0.5), 12, (math.pi, 0, 0))
    for k in range(10):                                                      # little barrier posts around the collar
        a = k / 10 * 2 * math.pi + 0.3
        if abs(math.atan2(math.sin(a - 4.71), math.cos(a - 4.71))) < 0.45: continue
        cyl((math.cos(a) * (R_SH + 1.3), math.sin(a) * (R_SH + 1.3), 0.45), 0.07, 0.9, yellow, (0, 0, 0), 10)

# ---- the far side (night ocean)
with group('ocean'):
    water = bpy.data.materials.new('ocean'); water.use_nodes = True; wn = water.node_tree.nodes; wb = wn['Principled BSDF']
    wb.inputs['Base Color'].default_value = (0.01, 0.03, 0.06, 1); wb.inputs['Roughness'].default_value = 0.28
    wv = wn.new('ShaderNodeTexNoise'); wv.inputs['Scale'].default_value = 0.6; wv.inputs['Detail'].default_value = 4; bm = wn.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.25
    water.node_tree.links.new(wv.outputs['Fac'], bm.inputs['Height']); water.node_tree.links.new(bm.outputs['Normal'], wb.inputs['Normal'])
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=2500, fill_type='NGON', location=(0, 0, -0.25)); sea = bpy.context.object
    bpy.ops.mesh.primitive_cylinder_add(radius=R_SH + 0.5, depth=4, vertices=64, location=(0, 0, 0)); hc = bpy.context.object
    md = sea.modifiers.new('hole', 'BOOLEAN'); md.object = hc; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; bpy.context.view_layer.objects.active = sea; bpy.ops.object.modifier_apply(modifier='hole'); bpy.data.objects.remove(hc)
    sea.data.materials.append(water)
    ball((-900, 1600, 520), 70, m_emis('moon', (0.95, 0.95, 1.0), 6.0), 3)
    bpy.ops.object.light_add(type='SUN'); moon = bpy.context.object; moon.data.energy = 0.0; moon.data.color = (0.6, 0.7, 1.0); moon.rotation_euler = (math.radians(70), 0, math.radians(210)); moon.data.angle = math.radians(2)
    BX, BY = -2.4, -9.6                                                      # the buoy
    red = m_plain('buoyRed', (0.75, 0.05, 0.03), 0.5)
    cyl((BX, BY, 0.1), 0.75, 0.9, red, (0, 0, 0), 24); cyl((BX, BY, 0.75), 0.55, 0.45, white, (0, 0, 0), 24); cone((BX, BY, 1.45), 0.4, 0.9, red, 16)
    for dx in (-0.5, 0.5): box((BX + dx, BY, 1.6), (0.05, 0.05, 1.6), steel)
    box((BX, BY, 2.35), (1.9, 0.07, 0.7), m_emis('signGlow', (0.85, 0.88, 0.9), 0.35, (0.9, 0.9, 0.9)))
    text('INDIAN OCEAN', (BX, BY - 0.05, 2.35), 0.3, black, ext=0.004)
    ball((BX, BY, 2.95), 0.12, m_emis('beacon', (1.0, 0.25, 0.1), 30), 2)
    bpy.ops.object.light_add(type='POINT', location=(1.8, -4.2, 3.0)); fill = bpy.context.object; fill.data.energy = 0; fill.data.color = (0.6, 0.7, 1.0); fill.data.shadow_soft_size = 2
for o in SETS['ocean']:
    if o.type == 'LIGHT' and o.data.type == 'SUN':
        for (t, e) in [(0, 0.0), (b['swap'] - 0.02, 0.0), (b['swap'], 2.6)]: o.data.energy = e; o.data.keyframe_insert('energy', frame=int(round(t * FPS)))

# ---- the shaft: strata by depth (crust -> mantle -> outer core -> inner core), lit by its own glow
sh = bpy.data.materials.new('shaft'); sh.use_nodes = True; sn = sh.node_tree.nodes; sl = sh.node_tree.links.new; sb = sn['Principled BSDF']
geo = sn.new('ShaderNodeNewGeometry'); sxyz = sn.new('ShaderNodeSeparateXYZ'); sl(geo.outputs['Position'], sxyz.inputs[0])
dmap = sn.new('ShaderNodeMapRange'); dmap.inputs['From Min'].default_value = 0.0; dmap.inputs['From Max'].default_value = ZC; dmap.clamp = True; sl(sxyz.outputs['Z'], dmap.inputs['Value'])
col = sn.new('ShaderNodeValToRGB'); sl(dmap.outputs['Result'], col.inputs[0]); cr = col.color_ramp
stops = [(0.0, (0.36, 0.28, 0.2)), (0.08, (0.3, 0.25, 0.21)), (0.16, (0.36, 0.22, 0.12)), (0.22, (0.38, 0.12, 0.05)), (0.42, (0.6, 0.18, 0.04)), (0.62, (0.95, 0.35, 0.04)), (0.85, (1.0, 0.4, 0.05)), (1.0, (1.0, 0.48, 0.08))]
cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1); cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
for p, c in stops[1:-1]: e = cr.elements.new(p); e.color = (*c, 1)
emr = sn.new('ShaderNodeFloatCurve'); sl(dmap.outputs['Result'], emr.inputs['Value']); cv = emr.mapping.curves[0]
cv.points[0].location = (0, 0); cv.points[1].location = (1, 1); [cv.points.new(x, y) for x, y in ((0.16, 0.0), (0.24, 0.07), (0.45, 0.22), (0.65, 0.36), (0.85, 0.45))]; emr.mapping.update()
wave = sn.new('ShaderNodeTexWave'); wave.wave_type = 'BANDS'; wave.bands_direction = 'Z'; wave.inputs['Scale'].default_value = 0.035; wave.inputs['Distortion'].default_value = 6; wave.inputs['Detail'].default_value = 3
sl(geo.outputs['Position'], wave.inputs['Vector'])
nz = sn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 6; sl(geo.outputs['Position'], nz.inputs['Vector'])
mixb = sn.new('ShaderNodeMath'); mixb.operation = 'MULTIPLY_ADD'; sl(wave.outputs['Fac'], mixb.inputs[0]); mixb.inputs[1].default_value = 0.45; sl(nz.outputs['Fac'], mixb.inputs[2])
br = sn.new('ShaderNodeMix'); br.data_type = 'RGBA'; br.blend_type = 'MULTIPLY'; br.inputs[0].default_value = 0.65; sl(col.outputs['Color'], br.inputs[6])
gry = sn.new('ShaderNodeCombineXYZ'); sl(mixb.outputs[0], gry.inputs[0]); sl(mixb.outputs[0], gry.inputs[1]); sl(mixb.outputs[0], gry.inputs[2]); sl(gry.outputs[0], br.inputs[7])
sl(br.outputs[2], sb.inputs['Base Color']); sl(col.outputs['Color'], sb.inputs['Emission Color'])
cracks = sn.new('ShaderNodeTexVoronoi'); cracks.feature = 'DISTANCE_TO_EDGE'; cracks.inputs['Scale'].default_value = 0.45; sl(geo.outputs['Position'], cracks.inputs['Vector'])
crm = sn.new('ShaderNodeMapRange'); crm.inputs['From Min'].default_value = 0.06; crm.inputs['From Max'].default_value = 0.0; crm.inputs['To Min'].default_value = 0.35; crm.inputs['To Max'].default_value = 1.6; sl(cracks.outputs['Distance'], crm.inputs['Value'])
ems = sn.new('ShaderNodeMath'); ems.operation = 'MULTIPLY'; sl(emr.outputs[0], ems.inputs[0]); sl(crm.outputs['Result'], ems.inputs[1])
em2 = sn.new('ShaderNodeMath'); em2.operation = 'MULTIPLY'; em2.inputs[1].default_value = 3.6; sl(ems.outputs[0], em2.inputs[0]); sl(em2.outputs[0], sb.inputs['Emission Strength'])
sb.inputs['Roughness'].default_value = 0.9
for (z0, z1) in ((-1.5, ZC + 8.6), (ZC - 8.6, ZC - 80)):                  # above and below the core room
    bpy.ops.mesh.primitive_cylinder_add(radius=R_SH - 0.02, depth=z0 - z1, vertices=48, end_fill_type='NOTHING', location=(0, 0, (z0 + z1) / 2)); shaft = bpy.context.object
    for p in shaft.data.polygons: p.use_smooth = True
    shaft.data.materials.append(sh); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
# the core room at the centre: a glowing cavity the shaft runs through
core = bpy.data.materials.new('coreRoom'); core.use_nodes = True; cn = core.node_tree.nodes; cl = core.node_tree.links.new; cb = cn['Principled BSDF']
cnz = cn.new('ShaderNodeTexNoise'); cnz.inputs['Scale'].default_value = 0.9; cnz.inputs['Detail'].default_value = 10; cnz.inputs['Distortion'].default_value = 4.0
crp = cn.new('ShaderNodeValToRGB'); cl(cnz.outputs['Fac'], crp.inputs[0]); crp.color_ramp.elements[0].position = 0.4; crp.color_ramp.elements[0].color = (0.22, 0.02, 0.0, 1); _e = crp.color_ramp.elements.new(0.52); _e.color = (0.9, 0.16, 0.01, 1); crp.color_ramp.elements[1].position = 0.66; crp.color_ramp.elements[1].color = (1.0, 0.55, 0.1, 1)
cb.inputs['Base Color'].default_value = (0.03, 0.01, 0.0, 1); cl(crp.outputs['Color'], cb.inputs['Emission Color']); cb.inputs['Emission Strength'].default_value = 1.0
bpy.ops.mesh.primitive_uv_sphere_add(radius=9, segments=48, ring_count=24, location=(0, 0, ZC)); room = bpy.context.object; room.data.materials.append(core)
bpy.ops.object.shade_smooth(); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
for k in range(46):                                                          # floating embers in the core
    a = random.uniform(0, 2 * math.pi); r = random.uniform(2.5, 7.5); z = random.uniform(-6, 6)
    ball((r * math.cos(a), r * math.sin(a), ZC + z), random.uniform(0.03, 0.09), m_emis('ember', (1.0, 0.45, 0.08), 5), 2)
bpy.ops.object.light_add(type='POINT', location=(0, 0, ZC + 3)); cl_ = bpy.context.object; cl_.data.energy = 120; cl_.data.color = (1.0, 0.7, 0.35); cl_.data.shadow_soft_size = 6
# a lamp that rides with the camera (the crust is dark)
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0)); camlamp = bpy.context.object; camlamp.data.energy = 1400; camlamp.data.color = (1.0, 0.92, 0.8); camlamp.data.shadow_soft_size = 1.0

# ---- the 12 km marker (this side only)
with group('plaque'):
    gold = m_emis('markerRing', (1.0, 0.75, 0.2), 4.0)
    ring(PLAQ - 1.45, PLAQ - 1.0, R_SH - 0.08, R_SH + 0.05, gold)
    PY = -R_SH + 0.06
    box((0, PY, PLAQ + 1.1), (2.2, 0.05, 1.35), m_emis('plaqueBoard', (0.95, 0.92, 0.8), 0.6, (0.95, 0.92, 0.82)))
    box((0, PY - 0.01, PLAQ + 1.1), (2.32, 0.04, 1.47), black)
    text('12 KM', (0, PY + 0.045, PLAQ + 1.37), 0.5, black, rot=(math.pi / 2, 0, math.pi), ext=0.004)
    text('DEEPEST HOLE EVER DUG', (0, PY + 0.045, PLAQ + 0.95), 0.19, black, rot=(math.pi / 2, 0, math.pi), ext=0.004)
    text('KOLA BOREHOLE, 1989', (0, PY + 0.045, PLAQ + 0.68), 0.15, m_plain('red3', (0.7, 0.05, 0.03), 0.5), rot=(math.pi / 2, 0, math.pi), ext=0.004)
    cyl((1.55, -R_SH + 0.02, PLAQ + 1.05), 0.12, 0.1, black, (math.pi / 2, 0, 0), 16)   # the borehole itself, 23 cm wide

PA = math.radians(-143.6 + 90)                                              # turn the plaque to where the camera sees it beside you
for o in SETS['plaque']:
    if o.name.startswith('Cylinder') and o.data.materials and o.data.materials[0].name.startswith('markerRing'): continue
    x, y = o.location.x, o.location.y; o.location.x = x * math.cos(PA) - y * math.sin(PA); o.location.y = x * math.sin(PA) + y * math.cos(PA)
    o.rotation_euler.z += PA

# ---- the cutaway Earth (in space)
with group('space'):
    land = bpy.data.materials.new('earthSurface'); land.use_nodes = True; ln = land.node_tree.nodes; ll = land.node_tree.links.new; lb = ln['Principled BSDF']
    lnz = ln.new('ShaderNodeTexNoise'); lnz.inputs['Scale'].default_value = 0.22; lnz.inputs['Detail'].default_value = 8; lnz.inputs['Roughness'].default_value = 0.6
    lrp = ln.new('ShaderNodeValToRGB'); ll(lnz.outputs['Fac'], lrp.inputs[0]); E = lrp.color_ramp.elements
    E[0].position = 0.5; E[0].color = (0.02, 0.12, 0.42, 1); E[1].position = 0.53; E[1].color = (0.14, 0.38, 0.1, 1); e3 = E.new(0.62); e3.color = (0.42, 0.34, 0.16, 1)
    gco = ln.new('ShaderNodeTexCoord'); ll(gco.outputs['Object'], lnz.inputs['Vector']); ll(lrp.outputs['Color'], lb.inputs['Base Color']); lb.inputs['Roughness'].default_value = 0.6
    LAYERS = [(GR, land), (GR * 0.97, m_plain('crustCut', (0.42, 0.3, 0.18), 0.8)), (GR * 3480 / 6371, m_emis('outerCore', (1.0, 0.55, 0.08), 3.0)), (GR * 1221 / 6371, m_emis('innerCore', (1.0, 0.92, 0.6), 8.0))]
    mant = m_emis('mantle', (0.85, 0.22, 0.04), 1.2, (0.6, 0.18, 0.05))
    for k, (r, m) in enumerate([(GR, land), (GR * 0.985, mant), (GR * 3480 / 6371, LAYERS[2][1]), (GR * 1221 / 6371, LAYERS[3][1])]):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=96, ring_count=48, location=G); o = bpy.context.object; bpy.ops.object.shade_smooth()
        o.data.materials.append(m if k else land)
        if k == 0: o.data.materials.append(m_plain('crustFace', (0.42, 0.3, 0.18), 0.8))
        off = 0.03 * k                                                       # inner layers stand a hair proud so their cut faces show
        bpy.ops.mesh.primitive_cube_add(size=1, location=G + Vector((GR + off, -GR - off, 0))); cut = bpy.context.object; cut.scale = (2 * GR, 2 * GR, 2.4 * GR)
        cut.data.materials.append(o.data.materials[-1] if k == 0 else m)
        md = o.modifiers.new('wedge', 'BOOLEAN'); md.object = cut; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.material_mode = 'TRANSFER'
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier='wedge'); bpy.data.objects.remove(cut)
    tun = cyl(tuple(G), 0.1, 2 * GR + 0.6, m_emis('tunnelLine', (0.3, 0.9, 1.0), 3.0), (0, 0, 0), 12); tun.location = G + Vector((0.12, -0.12, 0))
    ball(tuple(G + Vector((0.12, -0.12, GR + 0.25))), 0.22, m_emis('youDot', (1.0, 0.2, 0.15), 10), 2)
    for k in range(380):                                                     # stars around the model
        d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized(); ball(tuple(G + d * random.uniform(260, 420)), random.uniform(0.25, 0.8), m_emis('star', (1, 1, 1), 14), 1)
    bpy.ops.object.light_add(type='SUN'); gsun = bpy.context.object; gsun.data.energy = 3.0; gsun.rotation_euler = (math.radians(60), 0, math.radians(-50))

# ------------------------------------------------------------------ visibility of the sets -------------------------
def key_hide(objs, keys):
    for o in objs:
        for (t, h) in keys:
            o.hide_render = h; o.keyframe_insert('hide_render', frame=max(0, int(round(t * FPS))))
for o in SETS['space']:
    if o.type == 'LIGHT': o.hide_render = True
key_hide(SETS['field'], [(0, False), (b['flashA'], True), (b['flashB'], False), (b['swap'], True)])
key_hide(SETS['space'], [(0, True), (b['flashA'], False), (b['flashB'], True)])
key_hide(SETS['ocean'], [(0, True), (b['swap'], False)])
key_hide(SETS['plaque'], [(0, False), (b['swap'], True)])
key_hide([sun], [(0, False), (b['flashA'], True), (b['flashB'], False)])
for ob in bpy.data.objects:
    ad_ = ob.animation_data
    if ad_ and ad_.action:
        for fc in ad_.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT' if fc.data_path == 'hide_render' else 'LINEAR'
for wt in (w,):
    if wt.node_tree.animation_data and wt.node_tree.animation_data.action:
        for fc in wt.node_tree.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for o in [sun] + [x for x in SETS['ocean'] if x.type == 'LIGHT']:
    if o.data.animation_data and o.data.animation_data.action:
        for fc in o.data.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# ------------------------------------------------------------------ camera ---------------------------------------
bpy.ops.object.camera_add(location=CAM[0][1]); cam = bpy.context.object; cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24; cam.data.clip_start = 0.05; cam.data.clip_end = 8000; sc.camera = cam
tgt = bpy.data.objects.new('camTarget', None); sc.collection.objects.link(tgt)
tc_ = cam.constraints.new('TRACK_TO'); tc_.target = tgt; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
for f in range(NF):
    t = f / FPS; p_, l_, lens = cam_at(t); cam.location = p_; tgt.location = l_; cam.data.lens = lens
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f); cam.data.keyframe_insert('lens', frame=f)
    camlamp.location = p_ + (l_ - p_).normalized() * 0.6; camlamp.keyframe_insert('location', frame=f)
    camlamp.data.energy = 1400 * min(1, max(0, (p_.z + 320) / 170)) * min(1, max(0, (-p_.z - 0.5) / 3)) if p_.x < 1000 else 0; camlamp.data.keyframe_insert('energy', frame=f)
for ob in (cam, tgt, cam.data, camlamp, camlamp.data):
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# camera + actor track + roll + beats for the engine
track, actors, vis, roll = [], {k: [] for k in ACTORS}, {k: [] for k in ACTORS}, []
for f in range(NF):
    sc.frame_set(f); M = cam.matrix_world; t = f / FPS
    track.append(dict(C=[round(v, 4) for v in M.translation], R=[[round(M[r][c], 5) for c in range(3)] for r in range(3)], tanh=round(12.0 / cam.data.lens, 6)))
    for k, fn_ in ACTORS.items(): p_, v = fn_(t); actors[k].append([round(c, 3) for c in p_]); vis[k].append(v)
    roll.append(round(hero_roll(t), 4))
json.dump(dict(fps=FPS, frames=NF, track=track, actors=actors, vis=vis, roll=roll, beats=B), open(os.path.join(OUT, 'camera.json'), 'w'))
print('tracks written', NF, flush=True)

sc.frame_start, sc.frame_end = START, END; sc.render.use_persistent_data = True
LIST = [int(v) for v in arg('--list', '').split(',') if v]
if LIST:
    for f in LIST: sc.frame_set(f); sc.render.filepath = os.path.join(OUT, 'f%04d.jpg' % f); bpy.ops.render.render(write_still=True)
    print('list done', flush=True)
elif '--tracks-only' not in argv:
    sc.render.use_overwrite = False; sc.render.use_placeholder = True; sc.render.filepath = os.path.join(OUT, 'f####'); bpy.ops.render.render(animation=True); print('sequence done', flush=True)
