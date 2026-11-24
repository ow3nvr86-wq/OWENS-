"""MOVIES IN A MINUTE: THE MATRIX. One continuous camera move, no cuts. The program world is a green-tinted night city;
the real world lies UNDER it. Street (the world flips to green code and back) -> up to an office window (9 AM) -> a
cramped apartment lit by three green screens (1 AM) -> an old hotel room in the rain: two red armchairs, two pills ->
down through the floor to a pod in a field of pod towers under a dark ceiling -> along to a giant pipe and a rusty
hovercraft (a chair with a cable) -> straight up into a warm kitchen (cookies in the oven) -> a restaurant booth (a
deal over steak) -> the street (a black car) -> a marble lobby (stormed) -> a hotel hallway: he is shot, gets up,
the hallway turns to green code, bullets stop, the agent bursts. All set and character designs are original.
Characters are 2D (engine); this script exports their 3D tracks in camera.json. Every time comes from a cue word.
Run: $BLENDER -b --factory-startup -P tools/matrix_oneshot.py -- <out> --words <words.json> [--scale 0.5]
     [--spp 6] [--list a,b,c] [--start A --end B] [--tracks-only]"""
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
CUES = [('every', 'everything'), ('computer', 'computer'), ('program', 'program'), ('chose', 'chose'), ('find', 'find'), ('thomas', 'thomas'),
        ('code', 'code'), ('day', 'day'), ('hacks', 'hacks'), ('night', 'night'), ('neo1', 'neo'), ('stranger', 'stranger'), ('morpheus1', 'morpheus'),
        ('pills', 'pills'), ('blue', 'blue'), ('normal', 'normal'), ('red1', 'red'), ('truth', 'truth'), ('takes', 'takes'), ('red2', 'red'),
        ('wakes', 'wakes'), ('pod', 'pod'), ('countless', 'countless'), ('machines', 'machines'), ('energy', 'energy'), ('minds', 'minds'),
        ('fake', 'fake'), ('matrix1', 'matrix'), ('ship', 'ship'), ('kung', 'kung'), ('uploaded', 'uploaded'), ('brain', 'brain'),
        ('morpheus3', 'morpheus'), ('one', 'one'), ('oracle', 'oracle'), ('isnt', 'isnt'), ('then', 'then'), ('cypher', 'cypher'), ('agents', 'agents'),
        ('comfortable', 'comfortable'), ('inside1', 'inside'), ('captured', 'captured'), ('trinity1', 'trinity'), ('storm', 'storm'),
        ('building', 'building'), ('save', 'save'), ('smith1', 'smith'), ('shoots', 'shoots'), ('dead', 'dead'), ('trinity2', 'trinity'),
        ('loves', 'loves'), ('wakes2', 'wakes'), ('now', 'now'), ('sees', 'sees'), ('code2', 'code'), ('stops', 'stops'), ('bullets', 'bullets'),
        ('destroys', 'destroys'), ('smith2', 'smith'), ('inside2', 'inside'), ('would', 'would'), ('pill', 'pill')]
B = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while j < len(ws) and norm(ws[j]['word']) != cue: j += 1
    if j == len(ws): raise SystemExit('cue word not found: ' + cue)
    B[key] = ws[j]['start']; wi = j + 1
B['end'] = DUR
B['dive'] = B['red2'] + 0.12            # he swallows the red pill: the camera drops through the floor
B['shot'] = B['shoots'] + 0.1           # the agent fires in the hallway
B['freeze'] = B['stops'] + 0.05         # bullets stop in mid-air
B['dash'] = B['destroys'] + 0.02        # he dives into the agent
B['burst'] = B['inside2'] + 0.05        # the agent bursts into light
b = B
print('beats', json.dumps({k: round(v, 2) for k, v in B.items()}), flush=True)


def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def clamp(u, a=0.0, c=1.0): return min(c, max(a, u))
def lerp3(a, c, u): return tuple(x + (y - x) * u for x, y in zip(a, c))

def walk(t, t0, t1, p0, p1):
    u = clamp((t - t0) / (t1 - t0)); return lerp3(p0, p1, u)
def seg(t, table):                        # [(t0, t1, fn(t) -> pos)], vis 0 outside
    for t0, t1, fn in table:
        if t0 <= t < t1: return fn(t), 1
    return (0, 0, -80), 0
C_ = lambda p: (lambda t: p)

# ------------------------------------------------------------------ layout (metres) ---------------------------------
# The program world (a green-tinted night city) sits on z = 0; the street runs along x (road y -16..-8). Sets face the
# street (south). The real world is UNDER the city: a dark ceiling at VZ, towers of pods down to PFZ, and a giant pipe
# where the hovercraft hangs. Original set designs throughout.
OFZ = 8.0                                # office floor
APZ = 14.0                               # apartment floor
HZ = 4.0                                 # the old hotel room (the two armchairs)
VZ = -10.0                               # underside of the city: the real world's ceiling
PFZ = -90.0                              # pod field floor
POD = (44.0, 1.4, -34.0)                 # his pod (centre)
SZ = -62.0                               # ship deck
HALL_Y = -1.0                            # hallway centre line

# ------------------------------------------------------------------ the 2D actors' tracks ---------------------------
HOOK = (0.0, b['find'] + 0.6)
OFFICE = (b['find'] + 0.6, b['day'] + 0.7)
APT = (b['day'] + 0.7, b['neo1'] + 0.8)
ROOM = (b['neo1'] + 0.8, b['dive'] + 0.15)
PODT = (b['wakes'] - 0.35, b['matrix1'] + 0.9)
SHIP = (b['ship'] - 0.9, b['one'] + 0.3)
KITCH = (b['oracle'] - 0.75, b['then'] + 0.35)
REST = (b['then'] - 0.05, b['captured'] - 0.2)
CAPT = (b['captured'] - 0.75, b['trinity1'] + 0.1)
LOBBY = (b['captured'] + 0.6, b['save'] + 0.6)
HALL = (b['save'] + 0.3, DUR + 1)
def dash(t):                              # he runs at the agent and dives into him
    if t < b['dash']: return (161.2, -1.55, 0.0)
    return lerp3((161.2, -1.55, 0.0), (166.4, -0.55, 0.0), ease((t - b['dash']) / 0.4))
def mentor_led(t): return walk(t, b['captured'] - 0.6, b['captured'] + 0.9, (123.0, -7.3, 0.12), (125.3, -9.0, 0.0))
TRACKS = {
    'neo': lambda t: seg(t, [(*HOOK, C_((0.0, -7.0, 0.12))), (*OFFICE, C_((12.5, -2.55, OFZ))), (*APT, C_((25.25, 0.0, APZ))),
                             (*ROOM, C_((44.5, 0.85, HZ))), (*PODT, C_((44.0, 1.3, POD[2] - 1.15))), (*SHIP, C_((99.55, 0.75, SZ))),
                             (*KITCH, C_((101.6, 1.0, 0.0))),
                             (*LOBBY, lambda t: walk(t, LOBBY[0], b['save'] + 0.3, (135.6, -2.6, 0.0), (141.4, -2.0, 0.0))),
                             (*HALL, dash)]),
    'mentor': lambda t: seg(t, [(*ROOM, C_((41.5, 0.85, HZ))), (*SHIP, C_((101.9, 0.35, SZ))), (*CAPT, mentor_led)]),
    'trinity': lambda t: seg(t, [(*SHIP, C_((97.3, 0.45, SZ))),
                                 (*LOBBY, lambda t: walk(t, LOBBY[0] + 0.1, b['save'] + 0.4, (134.4, -1.5, 0.0), (140.0, -1.0, 0.0)))]),
    'oracle': lambda t: seg(t, [(*KITCH, C_((98.6, 2.2, 0.0)))]),
    'cypher': lambda t: seg(t, [(*SHIP, C_((104.0, 0.6, SZ))), (*REST, C_((112.55, 1.05, 0.0)))]),
    'smith': lambda t: seg(t, [(*REST, C_((115.45, 1.05, 0.0))), (*CAPT, lambda t: walk(t, b['captured'] - 0.6, b['captured'] + 0.9, (124.4, -7.6, 0.12), (126.6, -9.3, 0.0))),
                               (HALL[0], b['burst'] + 0.08, C_((166.9, -0.45, 0.0)))]),
    'agent2': lambda t: seg(t, [(*CAPT, lambda t: walk(t, b['captured'] - 0.6, b['captured'] + 0.9, (121.7, -7.1, 0.12), (124.0, -8.8, 0.0)))]),
    'guard1': lambda t: seg(t, [(*LOBBY, C_((137.4, 3.6, 0.0)))]),
    'guard2': lambda t: seg(t, [(*LOBBY, C_((142.3, 2.8, 0.0)))]),
    'cow1': lambda t: seg(t, [(*OFFICE, C_((9.0, -0.6, OFZ)))]),
    'cow2': lambda t: seg(t, [(*OFFICE, C_((16.2, -0.9, OFZ)))]),
    'walker1': lambda t: seg(t, [(*HOOK, lambda t: walk(t, 0.0, HOOK[1], (-6.5, -6.9, 0.12), (3.0, -7.2, 0.12)))]),
    'walker2': lambda t: seg(t, [(*HOOK, lambda t: walk(t, 0.0, HOOK[1], (5.5, -7.5, 0.12), (-2.5, -7.1, 0.12)))]),
}
def roll_at(t):                           # he falls flat when he is shot, and gets back up
    if t < b['shot'] or t > b['wakes2'] + 0.6: return 0.0
    if t < b['wakes2']: return -1.5 * ease((t - b['shot']) / 0.35)
    return -1.5 * (1 - ease((t - b['wakes2']) / 0.5))

# ------------------------------------------------------------------ camera (t, position, look-at, lens) -------------
SEG_A = [
    (0.0, (0.0, -14.8, 1.75), (0.0, -6.8, 1.45), 22),
    (b['program'] + 0.2, (0.0, -13.6, 1.7), (0.0, -6.8, 1.4), 23),
    (b['find'], (0.4, -13.2, 1.75), (0.6, -6.8, 1.5), 23),
    (b['find'] + 0.3, (2.4, -12.8, 3.6), (9.5, -4.0, 8.4), 22),
    (b['find'] + 0.8, (10.2, -10.8, 8.9), (12.5, -2.0, 9.0), 22),
    (b['thomas'] + 0.05, (12.5, -8.6, 9.7), (12.5, -2.2, 9.0), 23),
    (b['day'] + 0.25, (12.6, -7.6, 9.65), (12.5, -2.2, 9.0), 24),
    (b['day'] + 0.6, (15.0, -9.0, 11.0), (22.0, -2.0, 14.5), 22),
    (b['hacks'] + 0.15, (24.8, -8.2, 15.3), (25.2, 0.5, 14.9), 22),
    (b['night'] + 0.2, (25.6, -5.0, 15.25), (24.7, 0.5, 14.85), 22),
    (b['neo1'] + 0.4, (25.9, -4.3, 15.2), (24.7, 0.5, 14.85), 23),
    (b['neo1'] + 0.62, (27.4, -7.0, 15.1), (34.0, -4.0, 9.0), 22),
    (b['neo1'] + 0.85, (31.5, -9.8, 11.6), (40.0, -2.0, 6.0), 22),
    (b['stranger'] + 0.1, (40.2, -9.8, 6.6), (43.0, 1.0, 5.4), 22),
    (b['morpheus1'] + 0.25, (43.0, -7.0, 5.95), (43.0, 1.0, 5.25), 18),
    (b['pills'] - 0.1, (43.0, -3.8, 5.5), (43.0, 1.0, 5.05), 14),
    (b['blue'] + 0.3, (42.85, -3.65, 5.45), (42.8, 1.0, 5.05), 14),
    (b['red1'] + 0.2, (43.2, -3.6, 5.45), (43.4, 1.0, 5.05), 14.5),
    (b['takes'], (43.5, -3.3, 5.4), (43.9, 1.0, 5.05), 16),
    (b['dive'] + 0.12, (44.0, -3.3, 4.6), (44.0, -1.0, -10.0), 22),
    (b['dive'] + 0.42, (44.0, -3.4, -9.0), (44.0, 0.0, -35.0), 22),
    (b['wakes'] - 0.05, (44.0, -3.6, -31.6), (44.0, 1.4, -34.3), 23),
    (b['wakes'] + 0.45, (44.0, -3.7, -33.3), (44.0, 1.4, -34.2), 24),
    (b['countless'] - 0.25, (44.0, -3.4, -33.4), (44.0, 1.4, -34.2), 25),
    (b['countless'] + 0.1, (41.2, -5.0, -31.0), (43.0, 8.0, -34.0), 22),
    (b['countless'] + 0.6, (38.0, -14.0, -26.0), (44.0, 10.0, -38.0), 19),
    (b['machines'] + 0.3, (38.0, -22.0, -21.5), (44.0, 14.0, -40.0), 18),
    (b['minds'], (38.0, -24.5, -20.0), (40.0, 12.0, -30.0), 18),
    (b['fake'] + 0.2, (38.0, -25.0, -19.5), (40.0, 6.0, -11.0), 18),
    (b['matrix1'] + 0.55, (38.5, -25.0, -19.6), (41.0, 8.0, -10.8), 18),
    (b['matrix1'] + 1.0, (52.0, -18.0, -36.0), (80.0, -2.0, -56.0), 20),
    (b['ship'] - 0.35, (76.0, -6.0, -56.5), (96.0, 0.0, -59.5), 21),
    (b['ship'] + 0.3, (99.6, -6.2, -59.8), (99.7, 0.8, -60.6), 22),
    (b['kung'] + 0.3, (99.6, -5.2, -60.3), (99.6, 0.8, -60.8), 25),
    (b['morpheus3'] - 0.2, (100.4, -6.3, -60.0), (100.6, 0.8, -60.7), 22),
    (b['one'] + 0.15, (100.6, -6.0, -60.0), (100.8, 0.8, -60.6), 23),
    (b['one'] + 0.4, (100.3, -8.5, -57.5), (100.0, -8.0, 0.0), 22),
    (b['oracle'] - 0.35, (100.0, -9.4, -2.0), (100.0, 2.0, 1.6), 22),
    (b['oracle'] + 0.05, (100.0, -7.2, 1.65), (100.0, 2.5, 1.25), 22),
    (b['isnt'] + 0.1, (100.1, -4.7, 1.6), (100.1, 2.5, 1.2), 23),
    (b['then'] + 0.35, (106.0, -9.0, 2.2), (112.0, 1.0, 1.3), 22),
    (b['cypher'] + 0.2, (113.4, -7.4, 1.8), (114.0, 1.6, 1.15), 22),
    (b['agents'] + 0.1, (114.0, -4.9, 1.55), (114.0, 1.6, 1.1), 23),
    (b['inside1'] + 0.2, (114.2, -4.6, 1.5), (114.1, 1.6, 1.1), 24),
    (b['captured'] - 0.6, (118.5, -9.4, 2.0), (124.0, -6.0, 1.2), 22),
    (b['captured'] + 0.1, (123.0, -14.0, 1.9), (124.8, -7.5, 1.05), 22),
    (b['trinity1'] - 0.1, (125.2, -14.6, 1.95), (125.6, -8.0, 1.0), 23),
    (b['storm'] + 0.15, (134.0, -14.2, 2.3), (139.5, -3.0, 1.6), 22),
    (b['building'] + 0.1, (138.8, -9.4, 2.0), (138.8, 2.0, 1.3), 20),
    (b['save'] + 0.1, (139.8, -8.7, 1.9), (140.0, 2.0, 1.3), 20),
    (b['save'] + 0.55, (150.0, -12.0, 2.0), (158.0, -6.0, 1.6), 22),
    (b['smith1'] - 0.2, (157.9, -8.6, 1.65), (158.0, -3.0, 1.6), 20),
    (b['smith1'] + 0.2, (158.0, -3.6, 1.62), (162.0, -1.6, 1.5), 20),
    (b['shoots'] - 0.05, (158.2, -1.6, 1.62), (170.0, -0.9, 1.3), 20),
    (b['dead'] + 0.2, (158.4, -1.4, 1.5), (170.0, -0.9, 1.1), 21),
    (b['wakes2'], (158.6, -1.3, 1.5), (170.0, -0.9, 1.15), 21),
    (b['sees'], (158.5, -1.2, 1.62), (170.0, -0.9, 1.3), 21),
    (b['stops'], (158.7, -1.1, 1.6), (170.0, -0.9, 1.3), 22),
    (b['destroys'], (159.0, -1.0, 1.6), (170.0, -0.85, 1.3), 22),
    (b['inside2'], (161.0, -0.9, 1.55), (170.0, -0.7, 1.25), 22),
    (b['would'], (162.2, -0.75, 1.5), (170.0, -0.6, 1.25), 23),
    (DUR, (163.3, -0.65, 1.45), (170.0, -0.55, 1.25), 24),
]

def spline(keys, t):
    T = [k[0] for k in keys]
    if t <= T[0]: return Vector(keys[0][1]), Vector(keys[0][2]), keys[0][3]
    if t >= T[-1]: return Vector(keys[-1][1]), Vector(keys[-1][2]), keys[-1][3]
    i = max(j for j in range(len(T) - 1) if T[j] <= t); h = T[i + 1] - T[i]; s = (t - T[i]) / h
    h00 = 2 * s ** 3 - 3 * s ** 2 + 1; h10 = s ** 3 - 2 * s ** 2 + s; h01 = -2 * s ** 3 + 3 * s ** 2; h11 = s ** 3 - s ** 2
    def slope(vals, j):                  # monotone (pchip) slope per component: no overshoot between keys
        if j == 0 or j == len(T) - 1: return 0.0
        d0 = (vals[j] - vals[j - 1]) / (T[j] - T[j - 1]); d1 = (vals[j + 1] - vals[j]) / (T[j + 1] - T[j])
        if d0 * d1 <= 0: return 0.0
        w0 = 2 * (T[j + 1] - T[j]) + (T[j] - T[j - 1]); w1 = (T[j + 1] - T[j]) + 2 * (T[j] - T[j - 1])
        return (w0 + w1) / (w0 / d0 + w1 / d1)
    def comp1(vals): return vals[i] * h00 + slope(vals, i) * h * h10 + vals[i + 1] * h01 + slope(vals, i + 1) * h * h11
    def comp(idx):
        if idx == 3: return comp1([k[3] for k in keys])
        return Vector([comp1([k[idx][c] for k in keys]) for c in range(3)])
    return comp(1), comp(2), comp(3)
assert all(a[0] < c[0] for a, c in zip(SEG_A, SEG_A[1:])), 'camera keys out of order'
def cam_at(t): return spline(SEG_A, t)

bpy.ops.wm.read_factory_settings(use_empty=True); ISL._T.clear()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4
sc.render.resolution_x, sc.render.resolution_y = int(1080 * SCALE), int(1920 * SCALE)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = 0.6
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92; sc.render.fps = FPS
sc.cycles.light_sampling_threshold = 0.03; sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.45
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False; sc.cycles.blur_glossy = 1.0

def kf(owner, path, f, v):
    setattr(owner, path, v); owner.keyframe_insert(path, frame=f)
def F(t): return int(round(t * FPS))
def point(loc, energy, col, soft=0.2):
    bpy.ops.object.light_add(type='POINT', location=loc); l = bpy.context.object; l.data.energy = energy; l.data.color = col; l.data.shadow_soft_size = soft; return l
def area(loc, energy, col, size, rot=(0, 0, 0)):
    bpy.ops.object.light_add(type='AREA', location=loc); l = bpy.context.object; l.data.energy = energy; l.data.color = col; l.data.size = size; l.rotation_euler = rot; return l
def text(body, loc, size, m, rot=(math.pi / 2, 0, 0), ext=0.01, font_bold=True):
    bpy.ops.object.text_add(location=loc); tx = bpy.context.object; tx.rotation_euler = rot; tx.data.body = body; tx.data.size = size
    tx.data.align_x = 'CENTER'; tx.data.align_y = 'CENTER'; tx.data.extrude = ext; tx.data.materials.append(m); return tx
def cut(obj, cutter, solver='EXACT'):
    md = obj.modifiers.new('cut', 'BOOLEAN'); md.object = cutter; md.operation = 'DIFFERENCE'; md.solver = solver
    bpy.context.view_layer.objects.active = obj; bpy.ops.object.modifier_apply(modifier='cut'); bpy.data.objects.remove(cutter)
def solid_box(loc, size, m, name='box'):          # a real mesh (not instanced) so it can be cut
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = size; bpy.ops.object.transform_apply(scale=True); o.name = name
    o.data.materials.append(m); return o
def span(x0, x1, y0, y1, z0, z1, m, name='box'):  # solid box from extents
    return solid_box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), m, name)
def hole(obj, x0, x1, y0, y1, z0, z1):
    cut(obj, span(x0, x1, y0, y1, z0, z1, m_plain('cutter', (1, 0, 0)), 'cutter'))

def m_city(name, wall, lit=0.32, strength=3.2, cell=(3.0, 3.4), glass=(0.015, 0.02, 0.026), warm=(1.0, 0.7, 0.36), cool=(0.6, 0.85, 1.0)):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; Lk = m.node_tree.links.new; bs = n['Principled BSDF']
    geo = n.new('ShaderNodeNewGeometry'); sp_ = n.new('ShaderNodeSeparateXYZ'); Lk(geo.outputs['Position'], sp_.inputs[0])
    sn = n.new('ShaderNodeSeparateXYZ'); Lk(geo.outputs['Normal'], sn.inputs[0])
    def math_(op, a=None, c=None, va=0.0, vc=0.0):
        mm = n.new('ShaderNodeMath'); mm.operation = op
        if a is not None: Lk(a, mm.inputs[0])
        else: mm.inputs[0].default_value = va
        if c is not None: Lk(c, mm.inputs[1])
        else: mm.inputs[1].default_value = vc
        return mm.outputs[0]
    u = math_('DIVIDE', math_('ADD', sp_.outputs['X'], sp_.outputs['Y']), None, vc=cell[0]); v = math_('DIVIDE', sp_.outputs['Z'], None, vc=cell[1])
    cb = n.new('ShaderNodeCombineXYZ'); Lk(u, cb.inputs[0]); Lk(v, cb.inputs[1])
    bk = n.new('ShaderNodeTexBrick'); bk.offset = 0.0; Lk(cb.outputs[0], bk.inputs['Vector']); bk.inputs['Scale'].default_value = 1.0
    bk.inputs['Mortar Size'].default_value = 0.24; bk.inputs['Brick Width'].default_value = 1.0; bk.inputs['Row Height'].default_value = 1.0
    bk.inputs['Color1'].default_value = (1, 1, 1, 1); bk.inputs['Color2'].default_value = (0, 0, 0, 1); bk.inputs['Mortar'].default_value = (0, 0, 0, 1); bk.inputs['Bias'].default_value = 0.0
    bw = n.new('ShaderNodeRGBToBW'); Lk(bk.outputs['Color'], bw.inputs[0])
    litm = math_('GREATER_THAN', bw.outputs[0], None, vc=1.0 - lit)
    win = math_('SUBTRACT', None, bk.outputs['Fac'], va=1.0)
    side = math_('LESS_THAN', math_('ABSOLUTE', sn.outputs['Z']), None, vc=0.5)
    winS = math_('MULTIPLY', win, side)
    mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; Lk(winS, mx.inputs[0]); mx.inputs[6].default_value = (*wall, 1); mx.inputs[7].default_value = (*glass, 1)
    Lk(mx.outputs[2], bs.inputs['Base Color'])
    hue = math_('FRACT', math_('MULTIPLY', bw.outputs[0], None, vc=7.31))
    mc = n.new('ShaderNodeMix'); mc.data_type = 'RGBA'; Lk(math_('GREATER_THAN', hue, None, vc=0.7), mc.inputs[0]); mc.inputs[6].default_value = (*warm, 1); mc.inputs[7].default_value = (*cool, 1)
    Lk(mc.outputs[2], bs.inputs['Emission Color'])
    Lk(math_('MULTIPLY', math_('MULTIPLY', litm, winS), None, vc=strength), bs.inputs['Emission Strength'])
    rr = n.new('ShaderNodeMix'); rr.data_type = 'FLOAT'; Lk(winS, rr.inputs[0]); rr.inputs[2].default_value = 0.85; rr.inputs[3].default_value = 0.12
    Lk(rr.outputs[0], bs.inputs['Roughness'])
    return m

# ---- world: a green-grey night (the program world's tint) with a dim haze on the horizon
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']; L = nt.links.new
tco = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L(tco.outputs['Generated'], sep.inputs[0])
ramp = nt.nodes.new('ShaderNodeValToRGB'); L(sep.outputs['Z'], ramp.inputs['Fac'])
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.035, 0.07, 0.045, 1)
ramp.color_ramp.elements[1].position = 0.4; ramp.color_ramp.elements[1].color = (0.004, 0.014, 0.01, 1)
e_ = ramp.color_ramp.elements.new(0.08); e_.color = (0.05, 0.09, 0.06, 1)
L(ramp.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0
bpy.ops.object.light_add(type='SUN'); moon = bpy.context.object; moon.data.angle = math.radians(3); moon.data.color = (0.6, 0.85, 0.7); moon.data.energy = 0.18
moon.rotation_euler = (math.radians(58), 0, math.radians(200))

# ---- materials (city materials get the green "code" look switched in by ENV; real-world ones are named rw_*)
WALLS = [(0.14, 0.15, 0.14), (0.2, 0.19, 0.16), (0.11, 0.13, 0.13), (0.23, 0.22, 0.2), (0.1, 0.11, 0.1)]
CITYM = [m_city('city%d' % k, WALLS[k], lit=[0.3, 0.22, 0.35, 0.26, 0.3][k], warm=(0.85, 1.0, 0.75), cool=(1.0, 0.85, 0.55)) for k in range(5)]
asph = bpy.data.materials.new('wetAsphalt'); asph.use_nodes = True; an_ = asph.node_tree.nodes; ab = an_['Principled BSDF']; AL = asph.node_tree.links.new
anz = an_.new('ShaderNodeTexNoise'); anz.inputs['Scale'].default_value = 0.35; anz.inputs['Detail'].default_value = 6
amr = an_.new('ShaderNodeMapRange'); AL(anz.outputs['Fac'], amr.inputs['Value']); amr.inputs['From Min'].default_value = 0.45; amr.inputs['From Max'].default_value = 0.6
amr.inputs['To Min'].default_value = 0.08; amr.inputs['To Max'].default_value = 0.6; AL(amr.outputs['Result'], ab.inputs['Roughness'])
ab.inputs['Base Color'].default_value = (0.03, 0.034, 0.032, 1)
concrete = m_noise('concrete', (0.2, 0.21, 0.19), (0.32, 0.32, 0.29), 3.0, 0.85, 0.15)
concD = m_noise('concreteDark', (0.12, 0.12, 0.12), (0.2, 0.2, 0.19), 2.5, 0.9, 0.2)
iron = m_plain('iron', (0.05, 0.05, 0.055), 0.4, 0.8); woodD = m_noise('woodDark', (0.14, 0.08, 0.05), (0.24, 0.15, 0.09), 5, 0.7, 0.05)
mercury = m_emis('mercury', (0.8, 1.0, 0.85), 16.0); fluor = m_emis('fluor', (0.86, 1.0, 0.92), 9.0); paper = m_plain('paper', (0.85, 0.84, 0.78), 0.8)
grey = m_plain('greyPlastic', (0.35, 0.36, 0.38), 0.5); screenG = m_emis('screenGreen', (0.3, 1.0, 0.45), 7.0, (0.02, 0.05, 0.03))
leather = m_plain('redLeather', (0.32, 0.04, 0.03), 0.35); brass = m_plain('brass', (0.55, 0.4, 0.15), 0.3, 0.9)
wallpaper = m_noise('wallpaper', (0.16, 0.12, 0.08), (0.24, 0.18, 0.11), 9.0, 0.9, 0.1)
bulbW = m_emis('bulbWarm', (1.0, 0.72, 0.4), 14.0); black = m_plain('carBlack', (0.02, 0.02, 0.022), 0.2, 0.5)
glassD = m_plain('glassDark', (0.02, 0.03, 0.03), 0.05)

# ================================================================== GROUND, STREET, LAMPS ============================
span(-160, 260, -160, 420, -0.32, -0.12, concD, 'groundBase')
span(-70, 200, -40, 30, -0.1, 0.0, asph, 'streetGround')
for (y0, y1) in [(-8.0, -6.0), (-18.0, -16.0)]: span(-70, 200, y0, y1, 0.0, 0.12, concrete, 'sidewalk')
for x in range(-66, 198, 6): box((x, -12.0, 0.004), (2.6, 0.14, 0.01), m_emis('laneLine', (0.75, 0.8, 0.6), 0.12, (0.5, 0.55, 0.4)))
LAMPS = [(x, -7.4) for x in (-12, 20, 52, 84, 118, 150, 178)] + [(x, -16.6) for x in (-28, 4, 36, 68, 102, 134, 166)]
for (x, y) in LAMPS:
    cyl((x, y, 2.9), 0.08, 5.8, iron, v=8); box((x, y + (0.6 if y < -12 else -0.6), 5.85), (0.12, 1.3, 0.1), iron)
    ly = y + (1.2 if y < -12 else -1.2); box((x, ly, 5.75), (0.5, 0.3, 0.14), iron); box((x, ly, 5.66), (0.36, 0.2, 0.03), mercury)
    point((x, ly, 5.4), 300, (0.75, 1.0, 0.8), 0.25)
span(-8, 4, -6, 6, 0.0, 22.0, CITYM[3], 'hookBuilding')
for x in (-6.0, -2.0, 2.0): box((x, -6.05, 1.4), (1.6, 0.06, 2.4), m_emis('shopWin', (0.7, 1.0, 0.75), 1.6, (0.1, 0.15, 0.1)))
box((-2.0, -6.4, 3.2), (6.0, 0.8, 0.12), m_plain('awning', (0.08, 0.2, 0.12), 0.7))
point((0.0, -9.0, 4.0), 260, (0.75, 1.0, 0.8), 1.0)

# ================================================================== OFFICE (by day: bright fluorescent) ==============
ofc = span(6, 20, -6, 6, 0.0, 30.0, CITYM[0], 'office')
hole(ofc, 6.4, 19.6, -5.6, 5.6, OFZ, OFZ + 3.4)
hole(ofc, 7.0, 19.0, -6.6, -5.4, OFZ + 0.6, OFZ + 3.0)
for x in range(7, 20, 2): box((x, -6.0, OFZ + 1.8), (0.12, 0.3, 2.4), concrete)
span(6.4, 19.6, -5.6, 5.6, OFZ - 0.2, OFZ + 0.012, m_plain('officeCarpet', (0.22, 0.24, 0.25), 0.9), 'officeFloor')
for (x0, x1, y0, y1, z0, z1) in [(6.4, 6.5, -5.6, 5.6, OFZ, OFZ + 3.4), (19.5, 19.6, -5.6, 5.6, OFZ, OFZ + 3.4), (6.4, 19.6, 5.5, 5.6, OFZ, OFZ + 3.4), (6.4, 19.6, -5.6, 5.6, OFZ + 3.3, OFZ + 3.4)]:
    span(x0, x1, y0, y1, z0, z1, m_plain('officeWall', (0.42, 0.45, 0.43), 0.85), 'liner')
for x in (9.0, 12.5, 16.0):
    box((x, 0.0, OFZ + 3.32), (0.3, 8.0, 0.05), fluor); area((x, 0.0, OFZ + 3.25), 260, (0.88, 1.0, 0.92), 1.4).data.shape = 'RECTANGLE'
for (x, y) in [(9.0, -1.4), (16.2, -1.7), (9.0, 3.0), (12.5, 3.0), (16.0, 3.0)]:      # cubicles
    box((x, y + 0.95, OFZ + 0.65), (2.8, 0.06, 1.3), m_plain('cubicle', (0.36, 0.4, 0.42), 0.9)); box((x - 1.4, y, OFZ + 0.65), (0.06, 1.9, 1.3), m_plain('cubicle', (0.36, 0.4, 0.42), 0.9))
    box((x, y + 0.35, OFZ + 0.74), (2.4, 0.7, 0.05), grey); box((x, y + 0.25, OFZ + 1.0), (0.45, 0.06, 0.34), m_emis('screenDay', (0.7, 0.9, 1.0), 1.2, (0.05, 0.05, 0.06)))
box((12.5, -3.4, OFZ + 0.74), (2.2, 0.8, 0.05), grey); box((12.5, -3.4, OFZ + 0.36), (2.1, 0.7, 0.72), m_plain('deskBody', (0.2, 0.2, 0.22), 0.7))   # his desk (monitor faces him)
box((12.5, -3.55, OFZ + 1.05), (0.6, 0.06, 0.42), m_plain('monitorBack', (0.1, 0.1, 0.11), 0.5))
for k in range(4): box((11.6 + k * 0.08, -3.3, OFZ + 0.78 + k * 0.02), (0.32, 0.42, 0.02), paper)
box((12.5, 5.52, OFZ + 2.5), (1.6, 0.06, 0.6), m_plain('clockBack', (0.03, 0.03, 0.03), 0.4))
text('9:00 AM', (12.5, 5.47, OFZ + 2.5), 0.36, m_emis('clockRed', (1.0, 0.15, 0.1), 10), rot=(math.pi / 2, 0, 0), ext=0.005)
point((12.5, -7.5, OFZ + 2.2), 120, (0.9, 1.0, 0.95), 1.5)

# ================================================================== APARTMENT (by night: three green screens) =======
apb = span(22, 32, -6, 4, 0.0, 22.0, CITYM[2], 'apartmentBlock')
hole(apb, 22.4, 31.6, -5.6, 3.6, APZ, APZ + 3.0)
hole(apb, 23.0, 31.0, -6.6, -5.4, APZ + 0.7, APZ + 2.6)
for x in (25.0, 29.0): box((x, -6.0, APZ + 1.65), (0.12, 0.3, 1.9), concrete)
span(22.4, 31.6, -5.6, 3.6, APZ - 0.2, APZ + 0.012, m_plain('aptFloor', (0.12, 0.09, 0.07), 0.6), 'aptFloor')
for (x0, x1, y0, y1, z0, z1) in [(22.4, 22.5, -5.6, 3.6, APZ, APZ + 3.0), (31.5, 31.6, -5.6, 3.6, APZ, APZ + 3.0), (22.4, 31.6, 3.5, 3.6, APZ, APZ + 3.0), (22.4, 31.6, -5.6, 3.6, APZ + 2.9, APZ + 3.0)]:
    span(x0, x1, y0, y1, z0, z1, m_plain('aptWall', (0.13, 0.14, 0.15), 0.9), 'liner')
box((23.6, 0.0, APZ + 0.74), (1.4, 3.6, 0.06), woodD); box((23.6, 0.0, APZ + 0.36), (1.3, 3.4, 0.72), m_plain('deskBody', (0.12, 0.11, 0.1), 0.7))
for (y, rz) in [(-1.25, -0.75), (0.0, -0.55), (1.2, -0.3)]:
    mon = box((23.45, y, APZ + 1.12), (0.08, 0.95, 0.58), m_plain('monitorCase', (0.05, 0.05, 0.06), 0.5), (0, 0, rz))
    box((23.5 + 0.0, y, APZ + 1.12), (0.04, 0.88, 0.52), screenG, (0, 0, rz))
for k in range(6): cyl((23.2 + 0.05 * k, -1.6 + 0.6 * k, APZ + 0.3), 0.015, 0.6, iron, (0.3, 0.2 * k, 0), 6)
point((24.3, 0.0, APZ + 1.3), 90, (0.35, 1.0, 0.5), 0.4)
box((29.6, 1.8, APZ + 0.3), (2.0, 1.6, 0.6), m_plain('bed', (0.18, 0.2, 0.22), 0.9))
box((27.5, 3.45, APZ + 1.7), (1.0, 0.03, 1.4), m_plain('poster', (0.08, 0.16, 0.1), 0.8))
for k in range(5): box((26.5 + k * 0.4, 2.5, APZ + 0.06 + 0.12 * (k % 2)), (0.35, 0.35, 0.1), m_plain('pizzaBox', (0.55, 0.45, 0.3), 0.9))
area((27.0, -7.0, APZ + 2.0), 45, (0.5, 0.7, 0.9), 3.0, (math.radians(80), 0, 0))
text('1:12 AM', (23.53, 0.0, APZ + 1.36), 0.09, m_emis('termText', (0.7, 1.0, 0.75), 8), rot=(math.pi / 2, 0, math.pi / 2), ext=0.002)

# ================================================================== THE OLD HOTEL ROOM (two armchairs, rain) ========
htl = span(36, 50, -6, 6, 0.0, 18.0, m_noise('hotelBrick', (0.2, 0.1, 0.07), (0.3, 0.16, 0.1), 4.0, 0.9, 0.2), 'hotel')
hole(htl, 37.0, 49.0, -5.6, 5.6, HZ, HZ + 3.8)
hole(htl, 38.0, 48.0, -6.6, -5.4, HZ + 0.5, HZ + 3.6)                              # front window band (the camera comes in)
hole(htl, 41.0, 45.0, 5.4, 6.6, HZ + 0.8, HZ + 3.4)                                # tall back window (rain, lightning)
for x in (40.0, 46.0): box((x, -6.0, HZ + 2.05), (0.14, 0.3, 3.1), concrete)
for x in (42.3, 43.7): box((x, 6.0, HZ + 2.1), (0.08, 0.2, 2.6), woodD)
span(37.0, 49.0, -5.6, 5.6, HZ - 0.2, HZ + 0.012, m_noise('oldFloor', (0.12, 0.07, 0.04), (0.2, 0.12, 0.07), 6, 0.6, 0.05), 'roomFloor')
for (x0, x1, y0, y1, z0, z1) in [(37.0, 37.1, -5.6, 5.6, HZ, HZ + 3.8), (48.9, 49.0, -5.6, 5.6, HZ, HZ + 3.8), (37.0, 41.0, 5.5, 5.6, HZ, HZ + 3.8), (45.0, 49.0, 5.5, 5.6, HZ, HZ + 3.8),
                                 (41.0, 45.0, 5.5, 5.6, HZ, HZ + 0.8), (41.0, 45.0, 5.5, 5.6, HZ + 3.4, HZ + 3.8), (37.0, 49.0, -5.6, 5.6, HZ + 3.7, HZ + 3.8)]:
    span(x0, x1, y0, y1, z0, z1, wallpaper, 'liner')
box((43.0, 1.2, HZ + 0.015), (6.0, 3.6, 0.01), m_plain('rug', (0.22, 0.06, 0.05), 0.95))
def armchair(x, face):                                  # face +1: looks toward +x
    box((x, 0.85, HZ + 0.25), (0.95, 0.95, 0.5), leather); box((x - face * 0.42, 0.85, HZ + 0.75), (0.2, 0.95, 1.0), leather)
    for s in (-1, 1): box((x, 0.85 + s * 0.42, HZ + 0.55), (0.9, 0.18, 0.45), leather)
    for (dx, dy) in [(-0.4, 0.45), (0.4, 0.45), (-0.4, 1.25), (0.4, 1.25)]: box((x + dx, dy, HZ + 0.04), (0.06, 0.06, 0.08), brass)
armchair(41.35, 1); armchair(44.65, -1)
cyl((43.0, 0.95, HZ + 0.3), 0.3, 0.04, woodD, v=20); cyl((43.0, 0.95, HZ + 0.6), 0.04, 0.58, woodD, v=8); cyl((43.0, 0.95, HZ + 0.62), 0.32, 0.03, woodD, v=20)
cyl((43.1, 0.95, HZ + 0.72), 0.05, 0.16, m_plain('water', (0.6, 0.7, 0.75), 0.05), v=12)
cyl((38.4, 3.4, HZ + 0.9), 0.025, 1.8, brass, v=8); cone((38.4, 3.4, HZ + 1.9), 0.3, 0.35, m_emis('lampShade', (1.0, 0.7, 0.35), 2.5, (0.5, 0.3, 0.1)), 16)
point((38.4, 3.2, HZ + 1.7), 380, (1.0, 0.66, 0.35), 0.3)
point((43.0, -2.0, HZ + 3.2), 420, (0.9, 0.85, 0.7), 1.0)
area((43.0, 0.8, HZ + 3.6), 160, (1.0, 0.8, 0.6), 3.0)
storm = area((43.0, 9.0, HZ + 2.5), 0, (0.75, 0.85, 1.0), 4.0, (math.radians(-90), 0, 0)); storm.visible_camera = False
FLASHES = [b['stranger'] - 0.3, b['blue'] + 0.6, b['takes'] - 0.25]
for f in range(0, NF, 2):
    t = f / FPS; e = 60
    for t0 in FLASHES:
        u = t - t0
        if 0 <= u < 0.45: e = max(e, 6000 * (1.0 if u < 0.06 else 0.25 if u < 0.12 else 0.8 if u < 0.2 else max(0, 1 - (u - 0.2) / 0.25)))
    storm.data.energy = e; storm.data.keyframe_insert('energy', frame=f)
for k in range(40): cyl((41.2 + random.uniform(0, 3.6), 6.3, HZ + random.uniform(1.0, 3.2)), 0.004, random.uniform(0.2, 0.5), m_emis('rainStreak', (0.7, 0.8, 0.9), 0.6), (0.15, 0, 0), 4)


# ================================================================== THE REAL WORLD (under the city) =================
rwCeil = m_noise('rw_ceiling', (0.03, 0.025, 0.025), (0.07, 0.05, 0.045), 0.06, 0.95, 0.4)
span(-60, 230, -70, 130, VZ, -0.35, rwCeil, 'rw_voidSlab')
grid = bpy.data.materials.new('rw_grid'); grid.use_nodes = True; gn = grid.node_tree.nodes; GL = grid.node_tree.links.new
for nn in list(gn): gn.remove(nn)
go = gn.new('ShaderNodeOutputMaterial'); gem = gn.new('ShaderNodeEmission'); gtr = gn.new('ShaderNodeBsdfTransparent'); gmx = gn.new('ShaderNodeMixShader')
gbr = gn.new('ShaderNodeTexBrick'); gbr.inputs['Scale'].default_value = 0.4; gbr.inputs['Mortar Size'].default_value = 0.03; gbr.offset = 0.0
gtc = gn.new('ShaderNodeTexCoord'); GL(gtc.outputs['Object'], gbr.inputs['Vector'])
GL(gbr.outputs['Fac'], gmx.inputs['Fac']); GL(gtr.outputs[0], gmx.inputs[1]); GL(gem.outputs[0], gmx.inputs[2]); GL(gmx.outputs[0], go.inputs['Surface'])
gem.inputs['Color'].default_value = (0.25, 1.0, 0.4, 1); gstr = gem.inputs['Strength']
gp = span(-60, 230, -70, 130, VZ - 0.06, VZ - 0.02, grid, 'rw_gridPlane')
for (t, e) in [(0, 0.15), (b['minds'] - 0.2, 0.15), (b['fake'] + 0.2, 3.5), (b['matrix1'] + 0.8, 3.5), (b['matrix1'] + 1.6, 0.4), (DUR, 0.4)]:
    gstr.default_value = e; gstr.keyframe_insert('default_value', frame=F(t))
podGlow = m_emis('rw_podGoo', (1.0, 0.25, 0.42), 1.6, (0.4, 0.05, 0.1)); podMetal = m_plain('rw_podMetal', (0.06, 0.06, 0.07), 0.35, 0.8)
spineM = m_noise('rw_spine', (0.04, 0.04, 0.045), (0.09, 0.09, 0.1), 2.0, 0.6, 0.3); cableM = m_plain('rw_cable', (0.03, 0.03, 0.035), 0.4, 0.5)
eyeR = m_emis('rw_eyeRed', (1.0, 0.08, 0.05), 25.0)
def unit_mesh():                                            # one tower level: six pods around a spine segment (joined)
    objs = []
    for k in range(6):
        a = k / 6 * 2 * math.pi - math.pi / 2; cx, cy = 2.8 * math.cos(a), 2.8 * math.sin(a)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=16, ring_count=10, location=(cx, cy, 0)); o = bpy.context.object; o.scale = (0.95, 0.95, 1.35); o.data.materials.append(podGlow); objs.append(o)
        for zz in (-0.75, 0.75):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.92 * math.sqrt(1 - (zz / 1.35) ** 2) + 0.06, minor_radius=0.06, major_segments=20, minor_segments=6, location=(cx, cy, zz)); t_ = bpy.context.object; t_.data.materials.append(podMetal); objs.append(t_)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=1.5, vertices=8, location=(cx * 0.55, cy * 0.55, 0.3), rotation=(0, math.pi / 2, a)); c_ = bpy.context.object; c_.data.materials.append(cableM); objs.append(c_)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=3.2, vertices=12, location=(0, 0, 0)); sp = bpy.context.object; sp.data.materials.append(spineM); objs.append(sp)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); u = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)   # origin at the spine, no inherited pod scale
    am = u.modifiers.new('arr', 'ARRAY'); am.count = 24; am.use_relative_offset = False; am.use_constant_offset = True; am.constant_offset_displace = (0, 0, 3.2)
    bpy.ops.object.modifier_apply(modifier='arr'); return u
tower = unit_mesh(); tower.name = 'rw_tower'; tower.location = (44.0, 4.2, POD[2] - 3.2 * 17)     # level 17 is his pod's level
for x in (2, 14, 26, 50, 62, 74, 86):
    for y in [4.2 + 12 * k for k in range(-3, 5)]:
        if (x, round(y, 1)) == (44, 4.2): continue
        o = bpy.data.objects.new('rw_towerI', tower.data); sc.collection.objects.link(o); o.location = (x, y, POD[2] - 3.2 * 17 + random.choice([0.0, 1.6])); o.rotation_euler = (0, 0, random.choice([0.0, 0.5]))
for (x0, x1, y0, y1) in [(-34, -30, -60, 120), (-34, 96, 60, 64), (-34, 96, -56, -52)]:                     # far haze walls (dark red)
    span(x0, x1, y0, y1, PFZ, VZ, m_emis('rw_haze', (0.35, 0.05, 0.05), 0.25, (0.02, 0.0, 0.0)), 'rw_haze')
span(-40, 100, -60, 70, PFZ - 1, PFZ, m_noise('rw_ground', (0.02, 0.02, 0.02), (0.05, 0.04, 0.04), 0.5, 0.9, 0.3), 'rw_ground')
for k in range(7):                                                                       # storm flicker under the ceiling
    lt = area((random.uniform(10, 80), random.uniform(-30, 40), VZ - 1.0), 0, (0.8, 0.5, 0.6), 12.0, (math.pi, 0, 0))
    for f in range(0, NF, 6):
        t = f / FPS; ph = math.sin(t * (1.7 + k * 0.37) + k * 2.1); lt.data.energy = 9000 if ph > 0.985 else 400; lt.data.keyframe_insert('energy', frame=f)
point((44.0, -1.2, POD[2] + 0.6), 160, (1.0, 0.35, 0.5), 0.8)                            # his pod glows on his face
area((40.0, -20.0, -14.0), 900, (0.6, 0.65, 1.0), 30.0, (math.radians(-140), 0, 0))
podE = podGlow.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
for (t, e) in [(0, 1.6), (b['energy'] - 0.1, 1.6), (b['energy'] + 0.15, 5.0), (b['energy'] + 0.8, 2.2), (DUR, 2.2)]: podE.default_value = e; podE.keyframe_insert('default_value', frame=F(t))
# the harvester: a dark body with red eyes trailing cables (an original machine design)
bpy.ops.object.empty_add(location=(0, 0, 0)); drone = bpy.context.object
ball((0, 0, 0), 1.2, podMetal, 2).parent = drone
for k in range(3): ball((-0.55 + k * 0.55, -1.05, 0.25), 0.16, eyeR, 1).parent = drone
for k in range(8):
    a = k / 8 * 2 * math.pi; c_ = cyl((0.9 * math.cos(a), 0.9 * math.sin(a) + 1.6, -0.6), 0.07, 3.6, cableM, (math.radians(70), 0, a), 6); c_.parent = drone
dl = point((0, -1.6, 0.2), 0, (1.0, 0.1, 0.05), 0.3); dl.parent = drone
for (t, p) in [(0, (24.0, -14.0, -27.0)), (b['machines'] - 0.5, (28.0, -13.0, -27.0)), (b['minds'] + 0.8, (54.0, -10.0, -24.0)), (DUR, (60.0, -8.0, -24.0))]:
    drone.location = p; drone.keyframe_insert('location', frame=F(t))
for (t, e) in [(0, 0), (b['machines'] - 0.5, 300), (b['matrix1'] + 1.0, 300), (b['matrix1'] + 1.2, 0)]: dl.data.energy = e; dl.data.keyframe_insert('energy', frame=F(t))

# ================================================================== THE PIPE + THE HOVERCRAFT ========================
bpy.ops.mesh.primitive_cylinder_add(radius=13.0, depth=70, vertices=36, end_fill_type='NOTHING', location=(115.0, 0.0, -58.0), rotation=(0, math.pi / 2, 0)); pipe = bpy.context.object
pipe.data.materials.append(m_noise('rw_pipe', (0.05, 0.05, 0.05), (0.1, 0.09, 0.08), 1.2, 0.8, 0.4))
sl = pipe.modifiers.new('s', 'SOLIDIFY'); sl.thickness = 0.5; bpy.context.view_layer.objects.active = pipe; bpy.ops.object.modifier_apply(modifier='s')
for x in range(84, 150, 8): bpy.ops.mesh.primitive_torus_add(major_radius=12.8, minor_radius=0.25, major_segments=36, minor_segments=6, location=(x, 0, -58.0), rotation=(0, math.pi / 2, 0)); bpy.context.object.data.materials.append(podMetal)
for x in range(86, 150, 16): point((x, 9.0, -50.0), 300, (0.5, 0.7, 1.0), 1.0)
rust = m_noise('rw_rust', (0.12, 0.07, 0.05), (0.22, 0.13, 0.08), 3.0, 0.85, 0.5)
hull = span(92.0, 110.0, -3.6, 3.6, -64.6, -56.0, rust, 'rw_hull')
hole(hull, 92.4, 109.6, -3.2, 3.2, SZ, -56.4); hole(hull, 95.0, 105.0, -4.2, -2.6, SZ, SZ + 3.3)
span(92.4, 109.6, -3.2, 3.2, SZ - 0.2, SZ + 0.012, m_plain('rw_deck', (0.08, 0.08, 0.085), 0.5, 0.7), 'rw_deck')
bpy.ops.mesh.primitive_cone_add(radius1=3.6, depth=5.0, vertices=4, location=(88.0, 0, -60.3), rotation=(0, -math.pi / 2, math.pi / 4)); nose = bpy.context.object; nose.data.materials.append(rust); nose.scale = (1.0, 1.0, 1.0)
for x in (95.0, 101.0, 107.0): cyl((x, 0.0, -64.9), 1.5, 0.3, m_emis('rw_hover', (0.3, 0.6, 1.0), 6.0), v=20); point((x, 0.0, -66.0), 500, (0.35, 0.6, 1.0), 1.0)
def jack_chair(x):
    box((x, 1.2, SZ + 0.5), (0.8, 0.8, 0.14), m_plain('rw_seat', (0.18, 0.16, 0.14), 0.7)); box((x, 1.62, SZ + 1.1), (0.75, 0.14, 1.2), m_plain('rw_seat', (0.18, 0.16, 0.14), 0.7))
    box((x, 1.55, SZ + 1.9), (0.42, 0.22, 0.34), podMetal); cyl((x, 1.75, SZ + 2.6), 0.04, 1.6, cableM, (math.radians(-20), 0, 0), 6); cyl((x, 1.2, SZ + 0.22), 0.1, 0.44, podMetal, v=8)
for x in (97.3, 99.6, 104.0): jack_chair(x)
code_mat = bpy.data.materials.new('rw_codeScreen'); code_mat.use_nodes = True; cn = code_mat.node_tree.nodes; CL = code_mat.node_tree.links.new
cb_ = cn['Principled BSDF']; cb_.inputs['Base Color'].default_value = (0.01, 0.03, 0.015, 1); cwv = cn.new('ShaderNodeTexWave'); cwv.wave_type = 'BANDS'; cwv.bands_direction = 'Z'
cwv.inputs['Scale'].default_value = 6.0; cwv.inputs['Distortion'].default_value = 6.0; cmp = cn.new('ShaderNodeMapping'); ctc = cn.new('ShaderNodeTexCoord')
CL(ctc.outputs['Object'], cmp.inputs['Vector']); CL(cmp.outputs['Vector'], cwv.inputs['Vector'])
cb_.inputs['Emission Color'].default_value = (0.2, 1.0, 0.35, 1); CL(cwv.outputs['Fac'], cb_.inputs['Emission Strength'])
for (t, z) in [(0, 0.0), (DUR, -12.0)]: cmp.inputs['Location'].default_value[2] = z; cmp.inputs['Location'].keyframe_insert('default_value', index=2, frame=F(t))
for (x, z) in [(98.4, SZ + 1.7), (100.8, SZ + 1.7), (102.6, SZ + 2.3), (106.0, SZ + 1.6)]:
    box((x, 3.05, z), (1.1, 0.1, 0.8), podMetal); box((x, 2.99, z), (1.0, 0.03, 0.7), code_mat)
point((100.5, 1.4, SZ + 2.4), 140, (0.35, 1.0, 0.5), 0.6); area((100.5, -1.0, SZ + 3.1), 180, (0.55, 0.65, 0.85), 4.0)
for k in range(14): cyl((93.5 + k * 1.15, random.uniform(-2.5, 2.8), SZ + 2.9), 0.05, random.uniform(0.6, 1.4), cableM, (random.uniform(-0.3, 0.3), 0, 0), 6)

# ================================================================== THE KITCHEN (warm, cookies in the oven) ==========
kb = span(92, 106, -6, 6, 0.0, 18.0, CITYM[1], 'kitchenBlock')
hole(kb, 93.0, 105.0, -5.6, 5.6, 0.0, 3.2); hole(kb, 95.0, 105.0, -6.6, -5.4, 0.9, 2.7)
span(93.0, 105.0, -5.6, 5.6, -0.05, 0.03, m_plain('kitchenTile', (0.55, 0.5, 0.38), 0.5), 'kitchenFloor')
for (x0, x1, y0, y1, z0, z1) in [(93.0, 93.1, -5.6, 5.6, 0, 3.2), (104.9, 105.0, -5.6, 5.6, 0, 3.2), (93.0, 105.0, 5.5, 5.6, 0, 3.2), (93.0, 105.0, -5.6, 5.6, 3.1, 3.2)]:
    span(x0, x1, y0, y1, z0, z1, m_noise('kitchenWall', (0.5, 0.45, 0.22), (0.6, 0.55, 0.3), 7.0, 0.85, 0.05), 'liner')
box((100.5, 5.1, 0.45), (6.0, 0.7, 0.9), m_plain('cabinet', (0.45, 0.32, 0.2), 0.6)); box((100.5, 5.1, 0.92), (6.1, 0.75, 0.05), m_plain('counterTop', (0.7, 0.68, 0.62), 0.4))
box((97.6, 5.05, 0.48), (0.95, 0.8, 0.96), m_plain('ovenWhite', (0.82, 0.8, 0.75), 0.35)); box((97.6, 4.64, 0.42), (0.6, 0.02, 0.36), m_emis('ovenWindow', (1.0, 0.55, 0.2), 4.0))
for k in range(8): cyl((101.0 + (k % 4) * 0.2, 4.95 + (k // 4) * 0.2, 0.98), 0.075, 0.02, m_plain('cookie', (0.45, 0.28, 0.12), 0.8), v=12)
box((101.3, 5.05, 0.955), (0.95, 0.5, 0.012), m_plain('tray', (0.55, 0.55, 0.58), 0.3, 0.8))
box((100.0, 1.6, 0.74), (1.4, 1.0, 0.05), m_plain('tableCloth', (0.75, 0.2, 0.2), 0.8)); cyl((100.0, 1.6, 0.36), 0.05, 0.72, woodD, v=8)
box((94.0, 4.5, 0.95), (0.9, 0.8, 1.9), m_plain('fridge', (0.8, 0.82, 0.78), 0.3))
cyl((100.0, 1.6, 2.9), 0.006, 0.4, iron, v=6); cone((100.0, 1.6, 2.65), 0.35, 0.22, m_plain('shadeGreen', (0.15, 0.3, 0.15), 0.5), 16); ball((100.0, 1.6, 2.55), 0.08, bulbW, 2)
point((100.0, 1.6, 2.45), 260, (1.0, 0.72, 0.38), 0.15); point((97.6, 4.2, 0.5), 30, (1.0, 0.55, 0.2), 0.2)
cyl((103.6, 4.9, 1.25), 0.14, 0.3, m_plain('pot', (0.6, 0.3, 0.15), 0.7), v=12); ball((103.6, 4.9, 1.55), 0.3, m_plain('plant', (0.15, 0.35, 0.12), 0.8), 1)

# ================================================================== THE RESTAURANT (the deal) ========================
rb = span(108, 122, -6, 6, 0.0, 16.0, CITYM[4], 'restaurantBlock')
hole(rb, 109.0, 121.0, -5.6, 5.6, 0.0, 3.6); hole(rb, 110.0, 120.0, -6.6, -5.4, 0.8, 3.0)
span(109.0, 121.0, -5.6, 5.6, -0.05, 0.03, m_plain('restFloor', (0.1, 0.06, 0.05), 0.4), 'restFloor')
for (x0, x1, y0, y1, z0, z1) in [(109.0, 109.1, -5.6, 5.6, 0, 3.6), (120.9, 121.0, -5.6, 5.6, 0, 3.6), (109.0, 121.0, 5.5, 5.6, 0, 3.6), (109.0, 121.0, -5.6, 5.6, 3.5, 3.6)]:
    span(x0, x1, y0, y1, z0, z1, m_noise('restWall', (0.2, 0.04, 0.04), (0.28, 0.07, 0.06), 6.0, 0.8, 0.05), 'liner')
for x, face in [(112.3, 1), (115.7, -1)]:
    box((x, 1.05, 0.25), (0.8, 1.6, 0.5), leather); box((x - face * 0.42, 1.05, 0.85), (0.2, 1.6, 1.2), leather)
box((114.0, 1.05, 0.74), (1.6, 1.0, 0.05), m_plain('whiteCloth', (0.85, 0.84, 0.8), 0.8)); cyl((114.0, 1.05, 0.36), 0.06, 0.72, iron, v=8)
for x in (113.55, 114.45): cyl((x, 1.0, 0.78), 0.16, 0.015, m_plain('plate', (0.9, 0.9, 0.88), 0.3), v=16); box((x, 1.0, 0.8), (0.18, 0.12, 0.03), m_plain('steak', (0.3, 0.12, 0.06), 0.6))
cyl((114.0, 1.3, 0.85), 0.025, 0.16, m_plain('candle', (0.9, 0.88, 0.8), 0.6), v=8); ball((114.0, 1.3, 0.96), 0.02, bulbW, 1); point((114.0, 1.25, 1.05), 45, (1.0, 0.65, 0.3), 0.05)
for x in (113.8, 114.2): cyl((x, 1.35, 0.85), 0.03, 0.18, m_plain('wineGlass', (0.4, 0.05, 0.08), 0.05), v=8)
cyl((114.0, 1.05, 3.2), 0.4, 0.15, brass, v=16); point((114.0, 1.05, 2.9), 120, (1.0, 0.6, 0.3), 0.4)
point((114.0, -4.0, 2.5), 60, (1.0, 0.5, 0.35), 1.0)
# the black car at the kerb (Morpheus is taken)
box((127.5, -10.4, 0.7), (4.8, 1.9, 0.75), black); box((127.3, -10.4, 1.36), (2.6, 1.7, 0.6), glassD)
for (dx, dy) in [(-1.6, -0.95), (1.6, -0.95), (-1.6, 0.95), (1.6, 0.95)]: cyl((127.5 + dx, -10.4 + dy, 0.36), 0.36, 0.25, m_plain('tyre', (0.02, 0.02, 0.02), 0.8), (math.pi / 2, 0, 0), 16)
for dy in (-0.6, 0.6): box((125.05, -10.4 + dy, 0.85), (0.04, 0.3, 0.12), m_emis('headlight', (0.9, 1.0, 0.9), 12))
point((124.5, -10.4, 1.0), 200, (0.85, 1.0, 0.9), 0.5)


# ================================================================== THE LOBBY (stormed) ==============================
lb = span(130, 150, -6, 14, 0.0, 40.0, CITYM[0], 'lobbyTower')
hole(lb, 130.6, 149.4, -5.4, 13.4, 0.0, 6.0); hole(lb, 131.0, 149.0, -6.6, -5.0, 0.2, 5.6)
marble = m_noise('marble', (0.55, 0.55, 0.52), (0.75, 0.74, 0.7), 1.5, 0.15, 0.02)
span(130.6, 149.4, -5.4, 13.4, -0.05, 0.03, marble, 'lobbyFloor')
for (x0, x1, y0, y1, z0, z1) in [(130.6, 130.7, -5.4, 13.4, 0, 6.0), (149.3, 149.4, -5.4, 13.4, 0, 6.0), (130.6, 149.4, 13.3, 13.4, 0, 6.0), (130.6, 149.4, -5.4, 13.4, 5.9, 6.0)]:
    span(x0, x1, y0, y1, z0, z1, m_plain('lobbyWall', (0.4, 0.4, 0.38), 0.4), 'liner')
COLS = [(x, y) for x in (133.0, 136.6, 142.6, 146.2) for y in (1.0, 7.0)]
for (x, y) in COLS: box((x, y, 3.0), (0.9, 0.9, 6.0), marble)
for x in (139.6,): box((x, -2.4, 1.15), (0.2, 0.5, 2.3), grey); box((x + 1.5, -2.4, 1.15), (0.2, 0.5, 2.3), grey); box((x + 0.75, -2.4, 2.35), (1.7, 0.5, 0.2), grey)
box((135.0, -1.0, 0.55), (2.6, 0.9, 1.1), m_plain('deskStone', (0.25, 0.24, 0.22), 0.4))
for x in (134.0, 140.0, 146.0): box((x, 4.0, 5.95), (3.0, 0.4, 0.05), fluor); point((x, 4.0, 5.4), 600, (0.9, 1.0, 0.95), 1.5)
point((140.0, -8.0, 4.0), 500, (0.8, 1.0, 0.85), 2.0)
SHOTS_L = [b['storm'] + 0.15 + 0.22 * k for k in range(8)]
lobL = point((139.4, -2.0, 1.4), 0, (1.0, 0.85, 0.5), 0.05)
for t0 in SHOTS_L:
    for (t, e) in [(t0 - 0.01, 0), (t0, 2500), (t0 + 0.05, 0)]: lobL.data.energy = e; lobL.data.keyframe_insert('energy', frame=F(t))
for k, t0 in enumerate(SHOTS_L):                                       # stone chips off the columns
    cx, cy = COLS[(k * 3) % len(COLS)]
    for j in range(5):
        o = box((cx, cy - 0.46, 1.0 + k * 0.4), (0.07, 0.07, 0.07), marble); vx, vy, vz = random.uniform(-2, 2), random.uniform(-3.5, -1.5), random.uniform(0.5, 3)
        for f in range(F(t0) - 1, F(t0) + 70, 5):
            u = max(0, f / FPS - t0); o.location = (cx + vx * u, cy - 0.46 + vy * u, max(0.04, 1.0 + k * 0.4 + vz * u - 4.9 * u * u)); o.keyframe_insert('location', frame=f)
        o.hide_render = True; o.keyframe_insert('hide_render', frame=0); o.hide_render = False; o.keyframe_insert('hide_render', frame=F(t0))

# ================================================================== THE HOTEL HALLWAY ================================
hb = span(154, 182, -6, 6, 0.0, 26.0, CITYM[3], 'hallBlock')
hole(hb, 155.0, 181.0, -3.0, 1.0, 0.0, 3.2)                                     # the corridor
hole(hb, 157.0, 159.0, -6.6, -2.9, 0.0, 2.7)                                    # the doorway from the street
span(155.0, 181.0, -3.0, 1.0, -0.05, 0.02, m_plain('hallFloor', (0.12, 0.08, 0.05), 0.7), 'hallFloor')
span(155.0, 181.0, -1.6, -0.4, 0.02, 0.03, m_noise('runner', (0.32, 0.05, 0.04), (0.42, 0.08, 0.06), 8, 0.95, 0.05), 'runner')
hallPaper = m_noise('hallPaper', (0.22, 0.2, 0.12), (0.3, 0.27, 0.16), 12.0, 0.85, 0.05)
for (x0, x1, y0, y1, z0, z1) in [(155.0, 157.0, -3.0, -2.9, 0, 3.2), (159.0, 181.0, -3.0, -2.9, 0, 3.2), (157.0, 159.0, -3.0, -2.9, 2.7, 3.2), (155.0, 181.0, 0.9, 1.0, 0, 3.2),
                                 (155.0, 155.1, -3.0, 1.0, 0, 3.2), (155.0, 181.0, -3.0, 1.0, 3.1, 3.2)]:
    span(x0, x1, y0, y1, z0, z1, hallPaper, 'liner')
for (x0, x1, y0, y1, z0, z1) in [(155.0, 181.0, -2.95, -2.85, 0, 0.18), (155.0, 181.0, 0.85, 0.95, 0, 0.18)]: span(x0, x1, y0, y1, z0, z1, woodD, 'skirting')
box((180.95, -1.0, 1.7), (0.05, 1.4, 1.6), m_emis('endWindow', (0.7, 0.9, 0.8), 2.0))
for x in range(161, 181, 3):
    for (y, s) in [(-2.88, 1), (0.88, -1)]:
        box((x, y, 1.05), (0.95, 0.06, 2.1), m_plain('door', (0.2, 0.11, 0.06), 0.6)); ball((x + 0.32, y + s * 0.06, 1.0), 0.04, brass, 1)
        box((x, y, 2.28), (0.3, 0.02, 0.1), brass)
for x in range(160, 181, 4):
    for y in (-2.85, 0.85): ball((x + 1.5, y, 2.2), 0.08, bulbW, 2)
    point((x + 1.5, -1.0, 2.6), 90, (1.0, 0.7, 0.4), 0.4)
point((157.8, -4.0, 2.2), 60, (1.0, 0.75, 0.45), 0.5)
gun = point((166.6, -0.6, 1.35), 0, (1.0, 0.85, 0.5), 0.05)
SHOTS_H = [b['shot'] + 0.12 * k for k in range(4)] + [b['stops'] - 0.25 + 0.1 * k for k in range(4)]
for t0 in SHOTS_H:
    for (t, e) in [(t0 - 0.01, 0), (t0, 2200), (t0 + 0.05, 0)]: gun.data.energy = e; gun.data.keyframe_insert('energy', frame=F(t))
# the bullets that stop in mid-air (with ripple rings), then drop
bulletM = m_plain('bulletBrass', (0.6, 0.45, 0.2), 0.2, 1.0); ringM = m_emis('ripple', (0.6, 1.0, 0.7), 2.0, (0.1, 0.2, 0.1))
for k in range(4):
    y0, z0 = -1.25 + 0.22 * k - 0.3, 1.25 + 0.12 * ((k * 2) % 3); ts = b['stops'] - 0.25 + 0.1 * k; xs = 162.4 + 0.25 * k
    bl = ball((166.4, y0, z0), 0.045, bulletM, 2, (2.0, 1.0, 1.0)); rg = bpy.data.objects.new('ring', None)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.008, major_segments=24, minor_segments=4, location=(xs, y0, z0), rotation=(0, math.pi / 2, 0)); rg = bpy.context.object; rg.data.materials.append(ringM)
    for (t, x, z) in [(0, 166.4, z0), (ts, 166.4, z0), (ts + 0.18, xs, z0), (b['freeze'] + 0.9, xs - 0.05, z0), (b['freeze'] + 1.25, xs - 0.1, 0.05), (DUR, xs - 0.1, 0.05)]:
        bl.location = (x, y0, z); bl.keyframe_insert('location', frame=F(t))
    for (t, s) in [(0, 0.001), (ts + 0.17, 0.001), (ts + 0.2, 1.0), (b['freeze'] + 0.85, 1.6), (b['freeze'] + 1.0, 0.001)]:
        rg.scale = (s, s, s); rg.keyframe_insert('scale', frame=F(t))
    bl.hide_render = True; bl.keyframe_insert('hide_render', frame=0); bl.hide_render = False; bl.keyframe_insert('hide_render', frame=F(ts))
burst = point((166.9, -0.45, 1.2), 0, (0.6, 1.0, 0.7), 0.3)
for (t, e) in [(0, 0), (b['smith2'] - 0.1, 0), (b['inside2'] - 0.1, 800), (b['burst'], 30000), (b['burst'] + 0.5, 1500), (b['burst'] + 1.0, 0)]:
    burst.data.energy = e; burst.data.keyframe_insert('energy', frame=F(t))

# ================================================================== THE CITY (filler blocks) =========================
KEEP = [(-9, 5, -7, 7), (5, 21, -7, 7), (21, 33, -7, 5), (35, 51, -7, 7), (91, 123, -7, 7), (129, 151, -7, 15), (153, 183, -7, 7), (-75, 205, -19, -5)]
def free(x0, x1, y0, y1): return not any(x0 < a1 and x1 > a0 and y0 < b1 and y1 > b0 for (a0, a1, b0, b1) in KEEP)
blocks = 0
for gx in range(-110, 230, 13):
    for gy in list(range(-80, -20, 13)) + list(range(-6, 200, 13)):
        wx, wy = random.uniform(7, 11), random.uniform(7, 11); x0, y0 = gx + random.uniform(0, 2), gy + random.uniform(0, 2)
        if not free(x0 - 1, x0 + wx + 1, y0 - 1, y0 + wy + 1): continue
        h = random.uniform(10, 30) if (gy < 30 and -60 < gx < 200) else random.uniform(16, 60)
        span(x0, x0 + wx, y0, y0 + wy, 0.0, h, random.choice(CITYM), 'blk'); blocks += 1
        if random.random() < 0.25: box((x0 + wx / 2, y0 + wy / 2, h + 1.2), (0.6, 0.6, 2.4), iron)
print('city blocks', blocks, flush=True)

# ================================================================== ENV: the green "code" look for the program world ==
envg = bpy.data.node_groups.new('ENV', 'ShaderNodeTree'); envg.interface.new_socket(name='code', in_out='OUTPUT', socket_type='NodeSocketFloat')
ev = envg.nodes.new('ShaderNodeValue'); ev.name = 'code'; eo = envg.nodes.new('NodeGroupOutput'); envg.links.new(ev.outputs[0], eo.inputs[0])
CODE_KEYS = [(0, 0.0), (b['computer'] - 0.05, 0.0), (b['program'] + 0.15, 1.0), (b['chose'] - 0.35, 1.0), (b['chose'] - 0.05, 0.0),
             (b['sees'] - 0.1, 0.0), (b['sees'] + 0.45, 1.0), (DUR, 1.0)]
for (t, v) in CODE_KEYS: ev.outputs[0].default_value = v; ev.outputs[0].keyframe_insert('default_value', frame=F(t))
def wrap_code(m):
    nt_ = m.node_tree; nn = nt_.nodes; Lk = nt_.links.new
    out = next((n for n in nn if n.type == 'OUTPUT_MATERIAL'), None)
    if out is None or not out.inputs['Surface'].is_linked: return
    src = out.inputs['Surface'].links[0].from_socket
    gi = nn.new('ShaderNodeGroup'); gi.node_tree = envg
    geo = nn.new('ShaderNodeNewGeometry'); sp_ = nn.new('ShaderNodeSeparateXYZ'); Lk(geo.outputs['Position'], sp_.inputs[0])
    def mth(op, a, v=0.0, c=None):
        mm = nn.new('ShaderNodeMath'); mm.operation = op; Lk(a, mm.inputs[0])
        if c is not None: Lk(c, mm.inputs[1])
        else: mm.inputs[1].default_value = v
        return mm.outputs[0]
    lines = None
    for ax in ('X', 'Y', 'Z'):
        f_ = mth('ABSOLUTE', mth('SUBTRACT', mth('FRACT', mth('DIVIDE', mth('ADD', sp_.outputs[ax], 0.137), 0.8)), 0.5), 0.0)
        l_ = mth('GREATER_THAN', f_, 0.465); lines = l_ if lines is None else mth('MAXIMUM', lines, c=l_)
    em = nn.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.25, 1.0, 0.42, 1); Lk(mth('ADD', mth('MULTIPLY', lines, 4.0), 0.03), em.inputs['Strength'])
    mx = nn.new('ShaderNodeMixShader'); Lk(gi.outputs[0], mx.inputs[0]); Lk(src, mx.inputs[1]); Lk(em.outputs[0], mx.inputs[2]); Lk(mx.outputs[0], out.inputs['Surface'])
wrapped = 0
for m in list(bpy.data.materials):
    if m.use_nodes and not m.name.startswith(('rw_', 'slot_', 'cutter')): wrap_code(m); wrapped += 1
print('code look on', wrapped, 'materials', flush=True)


# ------------------------------------------------------------------ interpolation tidy-up ---------------------------
for ob in bpy.data.objects:
    ad_ = ob.animation_data
    if ad_ and ad_.action:
        for fc in ad_.action.fcurves:
            if fc.data_path == 'hide_render':
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for owner in [o.data for o in bpy.data.objects if o.type == 'LIGHT']:
    if owner.animation_data and owner.animation_data.action:
        for fc in owner.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ camera ---------------------------------------
bpy.ops.object.camera_add(location=SEG_A[0][1]); cam = bpy.context.object; cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24; cam.data.clip_start = 0.04; cam.data.clip_end = 3000; sc.camera = cam
tgt = bpy.data.objects.new('camTarget', None); sc.collection.objects.link(tgt)
tc_ = cam.constraints.new('TRACK_TO'); tc_.target = tgt; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
for f in range(NF):
    t = f / FPS; p_, l_, lens = cam_at(t); cam.location = p_; tgt.location = l_; cam.data.lens = lens
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f); cam.data.keyframe_insert('lens', frame=f)
for ob in (cam, tgt, cam.data):
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

track, actors, vis, roll = [], {k: [] for k in TRACKS}, {k: [] for k in TRACKS}, []
for f in range(NF):
    sc.frame_set(f); M = cam.matrix_world; t = f / FPS
    track.append(dict(C=[round(v, 4) for v in M.translation], R=[[round(M[r][c], 5) for c in range(3)] for r in range(3)], tanh=round(12.0 / cam.data.lens, 6)))
    for k, fn_ in TRACKS.items(): p_, v = fn_(t); actors[k].append([round(c, 3) for c in p_]); vis[k].append(v)
    roll.append(round(roll_at(t), 4))
json.dump(dict(fps=FPS, frames=NF, track=track, actors=actors, vis=vis, roll=roll, beats=B), open(os.path.join(OUT, 'camera.json'), 'w'))
print('tracks written', NF, flush=True)

sc.frame_start, sc.frame_end = START, END; sc.render.use_persistent_data = True
LIST = [int(v) for v in arg('--list', '').split(',') if v]
if LIST:
    for f in LIST: sc.frame_set(f); sc.render.filepath = os.path.join(OUT, 'f%04d.jpg' % f); bpy.ops.render.render(write_still=True)
    print('list done', flush=True)
elif '--tracks-only' not in argv:
    sc.render.use_overwrite = False; sc.render.use_placeholder = True; sc.render.filepath = os.path.join(OUT, 'f####'); bpy.ops.render.render(animation=True); print('sequence done', flush=True)
