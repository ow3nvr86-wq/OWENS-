"""MOVIES IN A MINUTE: THE SHAWSHANK REDEMPTION. One continuous camera move (two white flashes hide the last two jumps).
  night cell, Andy by the poster -> dawn, the cell is empty -> pull back through the bars, out of the cell-block window, over
  the yard, turn to the gate: 1947, a banker in a suit walks in -> crane up over the prison -> swoop to Red at the
  bleachers: rock hammer, poster -> years pass: a cut-away of the guard office, library, warden's office (time-lapse sun)
  -> night, searchlights: the new inmate; up to the wall: the warden and a guard (muzzle flash) -> grey day: Andy and Red
  against the wall -> next morning: in through the window, roll call, the empty cell -> the warden throws a rock, the
  poster rips -> through the hole, down the tunnel, the sewer pipe, out into the storm -> flash: Red walks out of the gate
  -> flash: a turquoise beach at sunset, Andy sanding a boat.
Characters are 2D (engine); this script exports their 3D tracks in camera.json. Every time comes from a cue word.
Run: $BLENDER -b --factory-startup -P tools/shawshank_oneshot.py -- <out> --words <words.json> --assets <dir> [--scale 0.5]
     [--spp 6] [--list a,b,c] [--start A --end B] [--tracks-only]"""
import bpy, math, sys, os, json, random, re, importlib.util
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0]; arg = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
SCALE, SPP = arg('--scale', 0.5), arg('--spp', 6)
WORDS = json.load(open(arg('--words', ''))); ASSETS = arg('--assets', '')
FPS = 60; DUR = WORDS['duration'] + 1.2; NF = int(round(DUR * FPS))
START, END = arg('--start', 0), arg('--end', NF - 1)
HERE = os.path.dirname(os.path.abspath(__file__))
s_ = importlib.util.spec_from_file_location('presets_fn2', os.path.join(HERE, 'presets_fn2.py')); F2 = importlib.util.module_from_spec(s_); s_.loader.exec_module(F2)
ISL = F2.ISL; box, cyl, cone, ball = ISL.box, ISL.cyl, ISL.cone, ISL.ball; m_plain, m_noise, m_emis = F2.m_plain, F2.m_noise, ISL.m_emis
os.makedirs(OUT, exist_ok=True); random.seed(7)

# ------------------------------------------------------------------ beats from the voice ---------------------------
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
CUES = [('then', 'then'), ('empty', 'empty'), ('y1947', '1947'), ('two', 'two'), ('innocent', 'innocent'), ('shawshank', 'shawshank'), ('befriends', 'befriends'),
        ('anything', 'anything'), ('asks', 'asks'), ('rock', 'rock'), ('later', 'later'), ('poster', 'poster'), ('years', 'years'), ('taxes', 'taxes'),
        ('library', 'library'), ('launders', 'launders'), ('warden', 'warden'), ('then2', 'then'), ('inmate', 'inmate'), ('really', 'really'),
        ('warden2', 'warden'), ('killed', 'killed'), ('tells', 'tells'), ('mexico', 'mexico'), ('next', 'next'), ('roll', 'roll'), ('gone', 'gone'),
        ('furious', 'furious'), ('throws', 'throws'), ('rock2', 'rock'), ('rips', 'rips'), ('behind', 'behind'), ('tunnel', 'tunnel'),
        ('nineteen2', 'nineteen'), ('crawls', 'crawls'), ('sewer', 'sewer'), ('takes', 'takes'), ('money', 'money'), ('mails', 'mails'), ('newspaper', 'newspaper'),
        ('red2', 'red'), ('forty', 'forty'), ('follows', 'follows'), ('finds', 'finds'), ('beach2', 'beach'), ('would', 'would')]
B = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while j < len(ws) and norm(ws[j]['word']) != cue: j += 1
    if j == len(ws): raise SystemExit('cue word not found: ' + cue)
    B[key] = ws[j]['start']; wi = j + 1
B['end'] = DUR
B['vanish'] = B['then'] + 0.5            # flash: Andy is gone from the cell
B['shot'] = B['killed']                  # muzzle flash (night -> grey day)
B['dawn2'] = B['next'] + 0.1
B['hit'] = B['rips']                     # the rock hits the poster
B['flashC'] = B['red2'] - 0.12           # lightning: storm -> the gate (day)
B['flashD'] = B['finds'] - 0.2           # -> the beach
b = B
print('beats', json.dumps({k: round(v, 2) for k, v in B.items()}), flush=True)

def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def clamp(u, a=0.0, c=1.0): return min(c, max(a, u))
def lerp3(a, c, u): return tuple(x + (y - x) * u for x, y in zip(a, c))

# ------------------------------------------------------------------ layout (metres) ---------------------------------
CW, CD, CH = 2.2, 2.8, 2.7          # cell width (x), depth (y: 0 = bars .. 2.8 = back wall), height
PZ = 1.45; PW, PH_ = 0.72, 1.03     # poster centre height and size (on the back wall of Andy's cell, x = 0)
WIN_Y = -7.0                        # the cell block's south wall (tall windows); the yard is south of it
GATE_Y = -60.0                      # outer wall with the gate
NORTH_Y = 40.0                      # north outer wall (the pipe runs under it)
DH = (16.0, 23.0)                   # the cut-away building (x range), rooms along y
ROOMS = [('guard', -40.0, -33.5), ('library', -33.5, -26.5), ('office', -26.5, -20.0)]
TUN = [(0, 2.95, PZ), (0, 4.2, 1.35), (0, 6.2, 0.4), (0, 8.6, -1.9), (0, 10.8, -3.9), (0, 12.6, -5.0), (0, 13.6, -5.2)]
PIPE0, PIPE1, PR = 13.4, 50.0, 0.8  # sewer pipe along +y at z = PZP
PZP = -5.2
CREEK = -5.75                        # water level in the ditch outside the north wall
BX = 3000.0                          # the beach is far away (own set)

# ------------------------------------------------------------------ the 2D actors' tracks ---------------------------
def walk(t, t0, t1, p0, p1):
    u = clamp((t - t0) / (t1 - t0)); return lerp3(p0, p1, u)
def seg(t, table):                    # [(t0, t1, fn(t) -> pos)], vis 0 outside
    for t0, t1, fn in table:
        if t0 <= t < t1: return fn(t), 1
    return (0, 0, -50), 0
GATE_LINE = lambda dy: (lambda t: walk(t, b['y1947'] + 0.5, b['innocent'] - 0.2, (1.0, -63.5 - dy, 0), (1.0, -56.6 - dy, 0)))
YARD_ANDY = lambda t: walk(t, b['shawshank'] + 0.6, b['asks'] - 0.3, (1.8, -21.2, 0), (-4.2, -20.1, 0))
def dh_andy(t):                       # through the cut-away rooms
    pts = [(b['years'] - 0.2, (19.6, -37.4, 0)), (b['taxes'] + 0.3, (19.6, -37.2, 0)), (b['library'] + 0.2, (19.6, -30.2, 0)), (b['library'] + 0.8, (19.6, -30.0, 0)),
           (b['launders'] + 0.7, (19.4, -23.8, 0)), (b['warden'] + 1.2, (19.4, -23.6, 0))]
    for (t0, a), (t1, c) in zip(pts, pts[1:]):
        if t <= t1: return lerp3(a, c, ease((t - t0) / (t1 - t0)))
    return pts[-1][1]
def andy_pipe(t):
    t0, t1 = b['crawls'] - 0.75, b['takes'] - 0.25
    if t < t1: return (0.0, 36.0 + (49.7 - 36.0) * clamp((t - t0) / (t1 - t0)), PZP - PR + 0.1)
    u = ease((t - t1) / 0.5); return (0.0, 49.7 + 2.9 * u, (PZP - PR + 0.1) + (CREEK - (PZP - PR + 0.1)) * u)
TRACKS = {
    'andy': lambda t: seg(t, [(0, b['vanish'], lambda t: (0.42, 1.75, 0)), (b['shawshank'] + 0.25, b['years'] - 0.2, YARD_ANDY),
                              (b['years'] - 0.2, b['then2'] - 0.15, dh_andy), (b['then2'] - 0.15, b['shot'], lambda t: (-11.6, -40.4, 0)),
                              (b['shot'], b['dawn2'], lambda t: (-1.85, -8.15, 0)), (b['crawls'] - 0.75, b['flashC'], andy_pipe)]),
    'andy_suit': lambda t: seg(t, [(b['y1947'] - 0.2, b['shawshank'] + 0.25, GATE_LINE(0.0))]),
    'arr1': lambda t: seg(t, [(b['y1947'] - 0.2, b['shawshank'] + 0.25, GATE_LINE(1.7))]),
    'arr2': lambda t: seg(t, [(b['y1947'] - 0.2, b['shawshank'] + 0.25, GATE_LINE(3.4))]),
    'red': lambda t: seg(t, [(b['shawshank'] + 0.25, b['years'] + 0.6, lambda t: (-5.4, -19.3, 0)), (b['shot'], b['dawn2'], lambda t: (-1.1, -8.15, 0))]),
    'red_free': lambda t: seg(t, [(b['flashC'], b['flashD'], lambda t: walk(t, b['flashC'], b['flashD'] + 0.3, (0.6, -58.6, 0), (0.6, -66.5, 0))),
                                  (b['flashD'], DUR + 1, lambda t: walk(t, b['flashD'], b['beach2'] - 0.1, (BX - 5.2, -3.6, 0.12), (BX - 0.75, -0.1, 0.12)))]),
    'andy_beach': lambda t: seg(t, [(b['flashD'], DUR + 1, lambda t: (BX + 0.55, 0.25, 0.12))]),
    'warden': lambda t: seg(t, [(b['launders'] - 0.6, b['then2'] + 0.4, lambda t: (21.2, -22.3, 0)), (b['warden2'] - 1.0, b['shot'] + 0.2, lambda t: (-9.6, -59.0, 8.0)),
                                (b['furious'] - 0.4, b['tunnel'], lambda t: walk(t, b['furious'] - 0.4, b['throws'] - 0.2, (1.6, -1.4, 0), (0.2, 0.9, 0)))]),
    'guard1': lambda t: seg(t, [(b['y1947'] - 0.2, b['shawshank'] + 0.25, lambda t: (-2.6, -55.0, 0)), (b['years'] - 0.2, b['library'] + 0.2, lambda t: (17.6, -38.2, 0)),
                                (b['warden2'] - 1.0, b['shot'] + 0.2, lambda t: (-11.0, -59.0, 8.0)), (b['next'], b['rips'], lambda t: walk(t, b['next'], b['gone'] - 0.2, (-3.5, -1.6, 0), (1.35, -0.9, 0)))]),
    'guard2': lambda t: seg(t, [(b['years'] - 0.2, b['library'] + 0.2, lambda t: (20.9, -38.9, 0)), (b['next'], b['rips'], lambda t: walk(t, b['next'], b['gone'], (5.5, -1.9, 0), (2.3, -1.5, 0)))]),
    'tommy': lambda t: seg(t, [(b['then2'] - 0.15, b['shot'], lambda t: (-10.6, -40.7, 0))]),
    'inm1': lambda t: seg(t, [(b['shawshank'] + 0.25, b['years'] + 0.6, lambda t: (2.5, -31.0, 0)), (b['next'], b['rips'], lambda t: (-2.2, 0.35, 0))]),
    'inm2': lambda t: seg(t, [(b['shawshank'] + 0.25, b['years'] + 0.6, lambda t: (-12.0, -33.0, 0)), (b['next'], b['rips'], lambda t: (2.2, 0.35, 0))]),
    'inm3': lambda t: seg(t, [(b['shawshank'] + 0.25, b['years'] + 0.6, lambda t: (-8.0, -25.5, 0)), (b['next'], b['rips'], lambda t: (-4.4, 0.35, 0))]),
    'inm4': lambda t: seg(t, [(b['shawshank'] + 0.25, b['years'] + 0.6, lambda t: (6.5, -40.0, 0)), (b['next'], b['rips'], lambda t: (4.4, 0.35, 0))]),
}
def roll_at(t):                        # Andy lies flat while he crawls
    t0 = b['crawls'] - 0.75; t1 = b['takes'] - 0.25
    if t0 <= t < t1: return -1.45
    if t1 <= t < t1 + 0.5: return -1.45 * (1 - ease((t - t1) / 0.5))
    return 0.0

# ------------------------------------------------------------------ camera (t, position, look-at, lens) -------------
# keys inside one segment are joined with a Catmull-Rom spline (no stop-and-go); a segment starts at a hidden jump
SEG_A = [
    (0.0, (0.95, 0.12, 1.25), (0.2, 2.4, 1.15), 17),
    (b['then'] - 0.2, (0.85, 0.3, 1.3), (0.2, 2.4, 1.2), 17),
    (b['empty'] + 0.1, (0.3, 1.0, 1.5), (0.0, 2.8, 1.45), 22),
    (b['y1947'] - 0.3, (0.12, 0.7, 1.55), (0.0, 2.8, 1.45), 22),
    (b['y1947'] + 0.35, (0.0, -1.3, 1.95), (0.0, 2.6, 1.6), 20),
    (b['y1947'] + 0.95, (0.0, WIN_Y - 0.4, 3.55), (0.0, 1.5, 2.6), 20),
    (b['y1947'] + 1.65, (0.5, -16.0, 7.5), (0.3, -4.0, 3.5), 20),
    (b['y1947'] + 2.15, (1.5, -23.0, 8.0), (14.0, -26.0, 5.0), 21),
    (b['y1947'] + 2.65, (2.4, -30.0, 7.5), (1.5, -56.0, 2.0), 22),
    (b['y1947'] + 3.65, (2.9, -47.5, 2.8), (1.0, -59.0, 1.25), 24),
    (b['innocent'] - 0.1, (2.5, -53.2, 1.75), (0.9, -58.3, 1.3), 26),
    (b['shawshank'] + 0.15, (2.0, -55.8, 4.0), (0.0, -40.0, 2.0), 24),
    (b['befriends'] - 0.05, (-8.0, -66.0, 24.0), (-1.0, -22.0, 0.0), 22),
    (b['anything'] - 0.4, (-3.2, -25.0, 2.0), (-4.6, -20.2, 1.15), 24),
    (b['rock'], (-3.9, -24.3, 1.55), (-4.8, -19.7, 1.05), 24),
    (b['poster'], (-4.3, -24.2, 1.5), (-4.8, -19.7, 1.05), 24),
    (b['years'] + 0.3, (-0.5, -27.0, 3.6), (8.0, -30.0, 1.5), 24),
    (b['taxes'] - 0.2, (9.6, -38.4, 2.1), (19.6, -37.2, 1.2), 24),
    (b['library'] + 0.3, (10.0, -31.0, 2.1), (19.6, -30.2, 1.2), 24),
    (b['launders'] + 0.9, (10.4, -24.6, 2.1), (20.2, -23.2, 1.2), 24),
    (b['warden'] + 0.6, (10.8, -23.6, 2.0), (20.2, -22.9, 1.25), 25),
    (b['then2'] + 0.2, (0.0, -38.0, 3.2), (-9.0, -40.5, 1.0), 24),
    (b['inmate'] + 0.7, (-6.6, -45.4, 1.95), (-11.0, -40.4, 1.2), 26),
    (b['really'] + 0.7, (-7.3, -44.5, 1.75), (-11.1, -40.5, 1.2), 28),
    (b['warden2'] + 0.25, (-7.8, -47.6, 2.4), (-10.3, -58.8, 9.2), 30),
    (b['killed'] + 0.05, (-8.2, -49.5, 3.0), (-10.4, -58.8, 9.0), 32),
    (b['tells'] - 0.1, (-1.5, -13.0, 1.2), (-1.48, -8.2, 0.8), 26),
    (b['mexico'] + 0.4, (-1.5, -12.3, 1.1), (-1.48, -8.2, 0.8), 26),
    (b['next'] + 0.55, (0.0, -10.4, 3.6), (0.0, -7.0, 3.55), 22),
    (b['roll'] + 0.2, (0.0, WIN_Y + 0.5, 3.4), (0.0, 0.0, 2.0), 20),
    (b['gone'] - 0.1, (0.15, -2.7, 1.85), (0.0, 1.6, 1.25), 22),
    (b['throws'] - 0.3, (-0.3, -1.3, 1.75), (0.2, 2.8, 1.3), 17),
    (b['hit'] + 0.05, (-0.3, -0.7, 1.65), (0.05, 2.8, 1.4), 18),
    (b['hit'] + 0.7, (-0.1, 1.4, 1.47), (0.0, 3.6, 1.43), 21),
    (b['behind'] + 0.3, (0.0, 2.55, 1.45), (0.0, 4.6, 1.3), 22),
    (b['tunnel'] + 0.3, (0.0, 4.4, 1.3), (0.0, 6.4, 0.3), 20),
    (b['nineteen2'] + 1.0, (0.0, 6.9, -0.1), (0.0, 9.0, -2.2), 20),
    (b['crawls'] - 0.4, (0.0, 10.8, -3.75), (0.0, 14.0, -5.1), 20),
    (b['crawls'] - 0.15, (0.0, 13.4, -5.05), (0.0, 20.0, -5.2), 20),
    (b['crawls'] + 0.2, (0.0, 36.0, -5.0), (0.0, 44.0, -5.6), 20),
    (b['sewer'] + 0.35, (0.25, 44.6, -5.0), (0.0, 48.5, -5.65), 20),
    (b['takes'] + 0.35, (0.3, 48.6, -4.9), (0.0, 52.6, -4.9), 20),
    (b['money'] + 0.2, (1.6, 56.0, -4.6), (0.0, 52.6, -4.35), 22),
    (b['newspaper'] - 0.2, (1.2, 59.5, -2.4), (0.0, 52.0, -3.6), 22),
    (b['flashC'], (0.8, 61.5, 0.8), (0.0, 48.0, -0.8), 22),
]
SEG_B = [
    (b['flashC'], (1.7, -63.0, 1.6), (0.6, -59.2, 1.25), 24),
    (b['forty'] + 0.4, (2.0, -66.6, 1.8), (0.6, -61.8, 1.3), 24),
    (b['follows'] + 0.5, (2.6, -70.5, 2.6), (0.6, -64.5, 1.5), 24),
    (b['flashD'], (1.4, -74.0, 4.4), (0.4, -90.0, 2.5), 24),
]
SEG_C = [
    (b['flashD'], (BX - 6.8, -8.6, 1.55), (BX - 1.4, 0.0, 1.0), 24),
    (b['beach2'], (BX - 3.6, -6.2, 1.5), (BX - 0.1, 0.2, 1.1), 24),
    (b['would'] + 0.3, (BX - 2.2, -5.8, 2.3), (BX + 0.2, 0.6, 1.2), 24),
    (DUR, (BX - 0.6, -8.0, 7.2), (BX + 1.2, 12.0, 3.2), 24),
]
SEGS = [SEG_A, SEG_B, SEG_C]
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
def cam_at(t):
    if t < b['flashC']: return spline(SEG_A, t)
    if t < b['flashD']: return spline(SEG_B, t)
    return spline(SEG_C, t)

# ------------------------------------------------------------------ scene -------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True); ISL._T.clear()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4
sc.render.resolution_x, sc.render.resolution_y = int(1080 * SCALE), int(1920 * SCALE)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92; sc.render.fps = FPS
sc.cycles.light_sampling_threshold = 0.03; sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.45
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False; sc.cycles.blur_glossy = 1.0

SETS = {k: [] for k in ('prison', 'beach', 'dhfront', 'beams', 'poster', 'torn', 'rock', 'storm')}
class group:
    def __init__(s, name): s.name = name
    def __enter__(s): s.before = set(bpy.data.objects)
    def __exit__(s, *a): SETS[s.name] += [o for o in bpy.data.objects if o not in s.before]
def kf(owner, path, f, v, interp=None):
    setattr(owner, path, v); owner.keyframe_insert(path, frame=f)

# ---- world: Nishita sky mixed toward overcast grey and toward night blue, all keyed per frame
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']; L = nt.links.new
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'; sky.sun_disc = False; sky.altitude = 100; sky.air_density = 1.2; sky.dust_density = 1.6
ov = nt.nodes.new('ShaderNodeMix'); ov.data_type = 'RGBA'; L(sky.outputs['Color'], ov.inputs[6]); ov.inputs[7].default_value = (0.42, 0.45, 0.5, 1)
nb = nt.nodes.new('ShaderNodeMix'); nb.data_type = 'RGBA'; L(ov.outputs[2], nb.inputs[6]); nb.inputs[7].default_value = (0.012, 0.022, 0.06, 1)
L(nb.outputs[2], bg.inputs['Color'])
bpy.ops.object.light_add(type='SUN'); sun = bpy.context.object; sun.data.angle = math.radians(1.5)
bpy.ops.object.light_add(type='SUN'); moon = bpy.context.object; moon.data.angle = math.radians(4); moon.data.color = (0.55, 0.65, 1.0); moon.rotation_euler = (math.radians(62), 0, math.radians(15))
bpy.ops.object.light_add(type='SUN'); bolt = bpy.context.object; bolt.data.angle = math.radians(20); bolt.data.color = (0.8, 0.85, 1.0); bolt.rotation_euler = (math.radians(30), 0, math.radians(170))

# time of day: (t, elevation deg, azimuth deg [0 = from the south, i.e. light travelling +y], overcast, night, sky strength, sun energy, moon energy)
LIGHTKEYS = [
    (0.0, -12, 0, 0, 1.0, 0.3, 0.0, 0.5),
    (b['vanish'] - 0.01, -12, 0, 0, 1.0, 0.3, 0.0, 0.5),
    (b['vanish'], 11, -8, 0, 0.0, 0.9, 3.2, 0.0),
    (b['y1947'] + 0.6, 11, -8, 0, 0.0, 0.9, 3.2, 0.0),
    (b['y1947'] + 1.6, 30, 150, 0, 0.0, 1.0, 3.6, 0.0),
    (b['shawshank'] - 0.1, 30, 150, 0, 0.0, 1.0, 3.6, 0.0),
    (b['befriends'] + 0.4, 18, 30, 0, 0.0, 1.0, 3.6, 0.0),
    (b['years'], 18, 30, 0, 0.0, 1.0, 3.6, 0.0),
    (b['warden'] - 0.2, 30, 140, 0, 0.0, 1.0, 3.6, 0.0),
    (b['then2'] - 0.2, -4, 160, 0, 0.6, 0.5, 0.0, 0.2),
    (b['then2'] + 0.3, -12, 160, 0, 1.0, 0.3, 0.0, 0.45),
    (b['shot'] - 0.01, -12, 160, 0, 1.0, 0.3, 0.0, 0.45),
    (b['shot'], 34, -30, 0.85, 0.0, 0.8, 1.1, 0.0),
    (b['next'], 34, -30, 0.85, 0.0, 0.8, 1.1, 0.0),
    (b['roll'], 9, -6, 0.0, 0.0, 0.9, 3.4, 0.0),
    (b['behind'], 9, -6, 0.0, 0.0, 0.9, 3.4, 0.0),
    (b['crawls'], -12, 0, 1.0, 1.0, 0.4, 0.0, 0.35),
    (b['flashC'] - 0.01, -12, 0, 1.0, 1.0, 0.4, 0.0, 0.35),
    (b['flashC'], 40, -25, 0.0, 0.0, 1.0, 3.8, 0.0),
    (b['flashD'] - 0.01, 40, -25, 0.0, 0.0, 1.0, 3.8, 0.0),
    (b['flashD'], 6, 165, 0.0, 0.0, 1.0, 3.4, 0.0),
    (DUR, 4, 165, 0.0, 0.0, 1.0, 3.2, 0.0),
]
JUMPS = [b['vanish'], b['shot'], b['flashC'], b['flashD']]
def light_at(t):
    for a, c in zip(LIGHTKEYS, LIGHTKEYS[1:]):
        if t <= c[0]:
            if c[0] - a[0] < 0.02: return c[1:]
            u = ease((t - a[0]) / (c[0] - a[0])); return tuple(x + (y - x) * u for x, y in zip(a[1:], c[1:]))
    return LIGHTKEYS[-1][1:]
BOLTS = [b['takes'] - 0.05, b['money'] + 0.6, b['mails'] + 0.5, b['newspaper'] + 0.4, b['flashC'] - 0.2]
def bolt_at(t):
    if not (b['crawls'] < t < b['flashC']): return 0.0
    e = 0.0
    for t0 in BOLTS:
        u = t - t0
        if 0 <= u < 0.45: e = max(e, (1.0 if u < 0.07 else 0.25 if u < 0.13 else 0.8 if u < 0.2 else max(0, 1 - (u - 0.2) / 0.25)) * 9.0)
    return e

# ---- materials
stone = m_noise('stone', (0.36, 0.34, 0.31), (0.5, 0.47, 0.42), 2.5, 0.92, 0.25)
stone2 = m_noise('stoneDark', (0.25, 0.24, 0.23), (0.37, 0.35, 0.32), 3.0, 0.92, 0.2)
plaster = m_noise('plaster', (0.55, 0.57, 0.52), (0.66, 0.67, 0.61), 4.0, 0.9, 0.08)
cellwall = m_noise('cellWall', (0.47, 0.5, 0.44), (0.58, 0.6, 0.53), 5.0, 0.88, 0.1)
floorc = m_noise('floorConcrete', (0.3, 0.3, 0.29), (0.4, 0.39, 0.37), 3.0, 0.7, 0.08)
dirt = m_noise('yardDirt', (0.36, 0.3, 0.22), (0.47, 0.41, 0.31), 1.2, 0.95, 0.15)
grass = m_noise('grass', (0.15, 0.28, 0.08), (0.27, 0.42, 0.13), 0.6, 0.9, 0.0)
iron = m_plain('iron', (0.06, 0.065, 0.07), 0.38, 0.85); rust = m_plain('rust', (0.22, 0.1, 0.05), 0.7, 0.3)
wood = m_noise('wood', (0.3, 0.18, 0.09), (0.42, 0.27, 0.14), 6, 0.6, 0.05); woodL = m_plain('woodLight', (0.55, 0.38, 0.22), 0.55)
mattress = m_plain('mattress', (0.62, 0.62, 0.58), 0.9); blanket = m_plain('blanket', (0.22, 0.25, 0.32), 0.95)
whiteP = m_plain('porcelain', (0.86, 0.86, 0.84), 0.25); paper = m_plain('paper', (0.92, 0.9, 0.84), 0.8)
green = m_plain('lampGreen', (0.05, 0.32, 0.12), 0.3); brass = m_plain('brass', (0.72, 0.55, 0.22), 0.3, 0.9)
bulb = m_emis('bulb', (1.0, 0.75, 0.42), 12.0); winglow = m_emis('windowGlow', (1.0, 0.86, 0.6), 2.5)
roofm = m_plain('roof', (0.18, 0.18, 0.2), 0.8); redbrick = m_noise('brick', (0.34, 0.14, 0.09), (0.46, 0.2, 0.12), 3.0, 0.9, 0.2)

def text(body, loc, size, m, rot=(math.pi / 2, 0, 0), ext=0.01):
    bpy.ops.object.text_add(location=loc); tx = bpy.context.object; tx.rotation_euler = rot; tx.data.body = body; tx.data.size = size
    tx.data.align_x = 'CENTER'; tx.data.align_y = 'CENTER'; tx.data.extrude = ext; tx.data.materials.append(m); return tx
def cut(obj, cutter, solver='EXACT'):
    md = obj.modifiers.new('cut', 'BOOLEAN'); md.object = cutter; md.operation = 'DIFFERENCE'; md.solver = solver
    bpy.context.view_layer.objects.active = obj; bpy.ops.object.modifier_apply(modifier='cut'); bpy.data.objects.remove(cutter)
def solid_box(loc, size, m, name='box'):          # a real mesh (not instanced) so it can be cut
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = size; bpy.ops.object.transform_apply(scale=True); o.name = name
    o.data.materials.append(m); return o
def img_mat(name, path, emit=0.25):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; bsdf = n['Principled BSDF']
    tx = n.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(path); tx.interpolation = 'Cubic'
    m.node_tree.links.new(tx.outputs['Color'], bsdf.inputs['Base Color']); m.node_tree.links.new(tx.outputs['Alpha'], bsdf.inputs['Alpha'])
    m.node_tree.links.new(tx.outputs['Color'], bsdf.inputs['Emission Color']); bsdf.inputs['Emission Strength'].default_value = emit; bsdf.inputs['Roughness'].default_value = 0.7
    try: m.blend_method = 'HASHED'
    except Exception: pass
    return m

# ================================================================== THE PRISON ======================================
with group('prison'):
    # ---- cell block: a row of cells (two tiers) facing a tall corridor; Andy's cell is x in [-1.1, 1.1]
    NC = 6
    solid_box((0, -3.5, -0.1), (2 * NC * CW + 6, 12, 0.2), floorc, 'cbFloor')
    back = solid_box((0, CD + 0.2, 4.2), (2 * NC * CW + 6, 0.4, 8.6), cellwall, 'cbBack')
    hole_ = solid_box((0, CD + 0.2, PZ), (0.6, 1.2, 0.82), stone, 'holeCut'); cut(back, hole_)
    solid_box((0, -3.5, 8.5), (2 * NC * CW + 6, 12, 0.3), plaster, 'cbCeil')
    for sx in (-1, 1): solid_box((sx * (NC * CW + 3), -2.0, 4.2), (0.4, 10.4, 8.6), plaster, 'cbEnd')
    for k in range(-NC, NC + 1):                                    # partitions between cells
        x = k * CW + CW / 2
        if abs(x) <= NC * CW: box((x, CD / 2, 2.85), (0.16, CD, 5.7), cellwall)
    for tier in (0, 1):
        z0 = tier * 3.0
        box((0, CD / 2, z0 + 2.9), (2 * NC * CW + 2, CD, 0.2), plaster)            # cell ceilings / tier slab
        for k in range(-NC, NC + 1):
            cx = k * CW
            if tier == 0 and k == 0: continue                                         # Andy's door is its own object
            box((cx, 0.0, z0 + 0.06), (CW - 0.1, 0.06, 0.06), iron); box((cx, 0.0, z0 + 1.05), (CW - 0.1, 0.05, 0.05), iron); box((cx, 0.0, z0 + 2.62), (CW - 0.1, 0.07, 0.08), iron)
            for j in range(16):
                bx = cx - CW / 2 + 0.11 + j * 0.13
                cyl((bx, 0.0, z0 + 1.33), 0.022, 2.64, iron, v=8)
            # a cot and a dim bulb in every cell
            box((cx - 0.72, 1.5, z0 + 0.42), (0.7, 1.9, 0.08), mattress); box((cx - 0.72, 1.55, z0 + 0.48), (0.66, 1.4, 0.05), blanket)
            box((cx + 0.82, 2.45, z0 + 0.22), (0.36, 0.42, 0.44), whiteP)
    # tier-1 walkway + railing
    box((0, -0.7, 2.93), (2 * NC * CW + 2, 1.4, 0.12), iron)
    box((0, -1.38, 3.95), (2 * NC * CW + 2, 0.06, 0.06), iron)
    for k in range(-30, 31): cyl((k * 0.45, -1.38, 3.45), 0.02, 1.0, iron, v=6)
    # Andy's cell: bunk, shelf of rocks, chess pieces, a table, the bulb
    box((-0.72, 1.5, 0.42), (0.7, 1.9, 0.08), mattress); box((-0.72, 1.6, 0.48), (0.66, 1.3, 0.05), m_plain('blanketA', (0.32, 0.22, 0.18), 0.95))
    for (x, y) in [(-1.02, 0.6), (-0.42, 0.6), (-1.02, 2.4), (-0.42, 2.4)]: box((x, y, 0.2), (0.05, 0.05, 0.4), iron)
    box((0.86, 2.0, 1.25), (0.32, 1.1, 0.04), woodL)                                # shelf
    for k in range(7): ball((0.86 + random.uniform(-0.08, 0.08), 1.55 + k * 0.14, 1.31), random.uniform(0.03, 0.05), m_plain('pebble%d' % k, random.choice([(0.5, 0.45, 0.4), (0.3, 0.32, 0.34), (0.6, 0.5, 0.36), (0.2, 0.2, 0.22)]), 0.6), 2, (1.2, 1, 0.8))
    box((0.82, 1.2, 0.72), (0.4, 0.55, 0.04), woodL); box((0.82, 1.2, 0.36), (0.36, 0.5, 0.7), wood)        # little table
    for k in range(6): cyl((0.72 + (k % 3) * 0.08, 1.08 + (k // 3) * 0.2, 0.79), 0.018, 0.08 + 0.02 * (k % 2), whiteP if k < 3 else iron, v=10)
    box((0.82, 2.48, 0.22), (0.36, 0.4, 0.44), whiteP)
    cyl((0.0, 1.7, 2.66), 0.006, 0.12, iron, v=6); ball((0.0, 1.7, 2.56), 0.045, bulb, 2)
    bpy.ops.object.light_add(type='POINT', location=(0.0, 1.6, 2.45)); cellbulb = bpy.context.object; cellbulb.data.color = (1.0, 0.72, 0.42); cellbulb.data.shadow_soft_size = 0.05
    # Andy's cell door (hinged at x = -1.1)
    bpy.ops.object.empty_add(location=(-CW / 2 + 0.04, 0.0, 0.0)); hinge = bpy.context.object
    for j in range(16):
        o = cyl((-CW / 2 + 0.11 + j * 0.13, 0.0, 1.33), 0.022, 2.64, iron, v=8); o.parent = hinge; o.location = (0.07 + j * 0.13, 0, 1.33)
    for zz in (0.3, 1.05, 2.3): o = box((0, 0, zz), (CW - 0.15, 0.06, 0.06), iron); o.parent = hinge; o.location = (CW / 2 - 0.06, 0, zz)
    # the corridor: the south wall with tall windows (the camera flies through the middle one)
    sw = solid_box((0, WIN_Y - 0.25, 4.5), (2 * NC * CW + 6, 0.5, 9.0), stone, 'southWall')
    WINX = [-11.0, -5.5, 0.0, 5.5, 11.0]
    for x in WINX:
        c = solid_box((x, WIN_Y - 0.25, 3.7), (1.7, 1.2, 3.6), stone, 'winCut'); cut(sw, c)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=1.2, vertices=24, location=(x, WIN_Y - 0.25, 5.5), rotation=(math.pi / 2, 0, 0)); c2 = bpy.context.object; cut(sw, c2)
        for dx in (-0.42, 0.42): box((x + dx, WIN_Y - 0.25, 4.2), (0.05, 0.05, 4.4), iron)
        for zz in (2.95, 4.15, 5.25): box((x, WIN_Y - 0.25, zz), (1.7, 0.05, 0.05), iron)
        box((x, WIN_Y - 0.1, 1.87), (1.9, 0.25, 0.1), stone2)
    box((0, WIN_Y - 0.25, 9.6), (2 * NC * CW + 6.4, 11.5, 0.3), roofm).location = (0, -2.2, 9.0)
    for x in (-9, -3, 3, 9):                                                          # hanging corridor lamps
        cyl((x, -3.8, 7.6), 0.01, 1.8, iron, v=6); cone((x, -3.8, 6.65), 0.3, 0.22, green, 16); ball((x, -3.8, 6.55), 0.07, bulb, 2)
        bpy.ops.object.light_add(type='POINT', location=(x, -3.8, 6.3)); l = bpy.context.object; l.data.energy = 60; l.data.color = (1.0, 0.75, 0.45); l.data.shadow_soft_size = 0.3
    # cell block exterior: walls up to the roof line, side wings
    solid_box((0, WIN_Y - 0.25, 4.5), (2 * NC * CW + 6, 0.02, 0.02), stone, 'marker')
    for sx in (-1, 1): solid_box((sx * 24.0, -2.0, 6.0), (18.0, 10.6, 12.0), stone2, 'wing')
    for sx in (-1, 1):
        for k in range(4): box((sx * (18 + k * 3.4), WIN_Y - 0.31, 6.0), (1.1, 0.05, 2.4), m_emis('winW%d%d' % (sx, k), (0.9, 0.82, 0.62), 0.7, (0.2, 0.2, 0.2)))
    cone((0, -2.0, 11.4), 8.5, 3.6, roofm, 4, (0, 0, math.pi / 4)).scale = (11.0, 7.6, 3.6)
    # ---- yard, walls, gate, towers
    gnd = solid_box((0, -10.0, -0.06), (90, 140, 0.1), dirt, 'ground')
    gcut = solid_box((0, 31.0, -0.06), (14.0, 26.0, 0.6), dirt, 'ditchCut'); gcut.location = (0, 58.0, -0.06); cut(gnd, gcut)
    for (x0, x1, y0, y1) in [(-36, 36, GATE_Y - 0.8, GATE_Y + 0.8), (-36, 36, NORTH_Y - 0.8, NORTH_Y + 0.8), (-36.8, -35.2, GATE_Y, NORTH_Y), (35.2, 36.8, GATE_Y, NORTH_Y)]:
        o = solid_box(((x0 + x1) / 2, (y0 + y1) / 2, 4.0), (x1 - x0, y1 - y0, 8.0), stone, 'outerWall')
        if y0 < GATE_Y + 1 and y1 < GATE_Y + 2: gc = solid_box((0, GATE_Y, 2.6), (5.0, 3.0, 5.2), stone, 'gateCut'); cut(o, gc)
        if y1 > NORTH_Y - 2 and y0 > NORTH_Y - 2: pc = solid_box((0, NORTH_Y, -1.0), (2.0, 3.0, 2.0), stone, 'pipeCut'); cut(o, pc)
    for x in range(-34, 35, 4):
        box((x, GATE_Y, 8.15), (1.6, 1.8, 0.3), stone2); box((x, NORTH_Y, 8.15), (1.6, 1.8, 0.3), stone2)
    box((0, GATE_Y, 5.6), (5.6, 1.9, 0.8), stone2)
    text('SHAWSHANK STATE PRISON', (0, GATE_Y - 0.96, 5.6), 0.36, m_plain('signGold', (0.85, 0.7, 0.32), 0.35, 0.8), ext=0.02)
    for sx in (-1, 1):                                                                    # gate leaves, swung open inward
        bpy.ops.object.empty_add(location=(sx * 2.45, GATE_Y + 0.6, 0)); gh = bpy.context.object; gh.rotation_euler = (0, 0, sx * math.radians(78))
        for j in range(12):
            o = cyl((0, 0, 0), 0.03, 5.0, iron, v=8); o.parent = gh; o.location = (-sx * (0.12 + j * 0.2), 0, 2.5)
        for zz in (0.4, 2.5, 4.6): o = box((0, 0, 0), (2.4, 0.06, 0.1), iron); o.parent = gh; o.location = (-sx * 1.2, 0, zz)
    TOWERS = [(-33.0, GATE_Y + 2.5), (33.0, GATE_Y + 2.5), (-33.0, NORTH_Y - 2.5), (33.0, NORTH_Y - 2.5), (-14.0, GATE_Y + 1.6)]
    for (x, y) in TOWERS:
        cyl((x, y, 6.5), 1.7, 13.0, stone); cyl((x, y, 13.4), 2.3, 0.4, stone2); box((x, y, 14.6), (3.4, 3.4, 2.2), m_plain('towerHut', (0.3, 0.29, 0.27), 0.8))
        cone((x, y, 16.4), 2.9, 1.4, roofm, 4, (0, 0, math.pi / 4))
        box((x, y, 14.7), (3.42, 3.42, 0.7), m_emis('towerGlass', (1.0, 0.85, 0.55), 1.2, (0.1, 0.1, 0.1)))
    for k in range(-30, 31, 6):                                                           # wall lamps (sodium)
        ball((k, GATE_Y + 0.9, 6.6), 0.12, m_emis('sodium', (1.0, 0.62, 0.25), 25), 2)
    bpy.ops.object.light_add(type='AREA', location=(0, GATE_Y + 3, 7.5)); gl = bpy.context.object; gl.data.energy = 600; gl.data.size = 20; gl.data.color = (1.0, 0.65, 0.35); gl.rotation_euler = (math.radians(30), 0, 0)
    # bleachers, a water tower, crates
    for k in range(4): box((-7.6, -21.8 + k * 0.6, 0.2 + k * 0.4), (6.0, 0.6, 0.12), woodL)
    box((-1.5, -7.95, 0.22), (3.2, 0.45, 0.06), woodL); [box((x, -7.95, 0.1), (0.08, 0.4, 0.2), wood) for x in (-2.9, -0.1)]   # bench by the wall
    for k in range(4):
        for x in (-10.4, -4.8): box((x, -21.8 + k * 0.6, 0.1 + k * 0.2), (0.12, 0.12, 0.2 + k * 0.4), wood)
    for (x, y) in [(13.0, -12.0), (-20.0, -48.0), (-19.0, -46.6)]: box((x, y, 0.5), (1.0, 1.0, 1.0), wood)
    for (x, y) in [(-26.0, -14.0)]:
        for dx in (-1.2, 1.2):
            for dy in (-1.2, 1.2): cyl((x + dx, y + dy, 4.5), 0.12, 9.0, iron, v=8)
        cyl((x, y, 10.5), 2.4, 3.2, m_plain('tankRed', (0.45, 0.16, 0.1), 0.6), v=24); cone((x, y, 12.6), 2.6, 1.2, roofm, 24)
    # ---- the cut-away building (guard office, library, warden's office), open to the yard (west, x = DH[0])
    X0, X1 = DH
    solid_box(((X0 + X1) / 2, -30.0, -0.04), (X1 - X0, 20.0, 0.12), m_plain('woodFloor', (0.36, 0.22, 0.12), 0.45), 'dhFloor')
    solid_box(((X0 + X1) / 2, -30.0, 3.6), (X1 - X0 + 0.4, 20.4, 0.2), plaster, 'dhCeil')
    solid_box((X1, -30.0, 1.8), (0.25, 20.0, 3.6), m_plain('dhBackWall', (0.55, 0.48, 0.36), 0.85), 'dhBack')
    for yy in (-40.0, -20.0): solid_box(((X0 + X1) / 2, yy, 1.8), (X1 - X0, 0.25, 3.6), plaster, 'dhEnd')
    for yy in (-33.5, -26.5):
        pw = solid_box(((X0 + X1) / 2, yy, 1.8), (X1 - X0, 0.18, 3.6), m_plain('dhPart', (0.6, 0.55, 0.44), 0.85), 'dhPart')
        dc = solid_box((19.6, yy, 1.1), (1.2, 1.0, 2.2), stone, 'doorCut'); cut(pw, dc)
    solid_box((X0 - 3.0, -30.0, 6.0), (6.0, 20.4, 0.3), roofm, 'dhRoof').location = ((X0 + X1) / 2, -30.0, 4.3)
    for (name, y0, y1) in ROOMS:
        yc = (y0 + y1) / 2
        bpy.ops.object.light_add(type='POINT', location=(X0 + 3.0, yc, 3.1)); l = bpy.context.object; l.data.energy = 140; l.data.color = (1.0, 0.78, 0.5); l.data.shadow_soft_size = 0.4
        cyl((X0 + 3.0, yc, 3.45), 0.01, 0.3, iron, v=6); cone((X0 + 3.0, yc, 3.25), 0.28, 0.2, green, 16); ball((X0 + 3.0, yc, 3.15), 0.06, bulb, 2)
    # guard office: desk, papers, filing cabinets, a wall clock
    box((18.6, -37.0, 0.75), (1.6, 0.8, 0.06), wood); box((18.6, -37.0, 0.37), (1.5, 0.7, 0.74), wood)
    for k in range(5): box((18.3 + k * 0.12, -37.0, 0.8), (0.22, 0.3, 0.01 + k * 0.01), paper)
    for k in range(3): box((X1 - 0.4, -39.2 + k * 0.6, 0.7), (0.5, 0.55, 1.4), m_plain('cabinet', (0.32, 0.36, 0.3), 0.5, 0.4))
    cyl((X1 - 0.14, -35.0, 2.6), 0.28, 0.05, whiteP, (0, math.pi / 2, 0), 24)
    # library: tall shelves of books
    BOOKC = [(0.5, 0.12, 0.1), (0.12, 0.25, 0.42), (0.16, 0.36, 0.18), (0.6, 0.45, 0.15), (0.3, 0.12, 0.3), (0.75, 0.62, 0.42)]
    bmats = [m_plain('book%d' % k, c, 0.6) for k, c in enumerate(BOOKC)]
    for sy in (-32.6, -30.0, -27.6):
        box((X1 - 0.45, sy, 1.5), (0.5, 1.9, 3.0), wood)
        for sh in range(5):
            z = 0.25 + sh * 0.6; x0 = sy - 0.88
            while x0 < sy + 0.85:
                bw = random.uniform(0.04, 0.09); bh = random.uniform(0.3, 0.45)
                box((X1 - 0.55, x0 + bw / 2, z + bh / 2), (0.3, bw - 0.005, bh), random.choice(bmats)); x0 += bw
    box((18.4, -30.0, 0.72), (1.8, 0.9, 0.06), woodL); box((18.4, -30.0, 0.36), (1.7, 0.8, 0.7), wood)
    for k in range(4): box((18.0 + k * 0.25, -30.0, 0.8 + 0.04 * k), (0.2, 0.3, 0.08), random.choice(bmats))
    # warden's office: big desk, green banker's lamp, a safe, money stacks, a framed motto
    box((20.6, -23.2, 0.78), (2.2, 1.0, 0.07), m_plain('mahogany', (0.28, 0.1, 0.06), 0.35)); box((20.6, -23.2, 0.38), (2.1, 0.9, 0.76), m_plain('mahogany2', (0.22, 0.08, 0.05), 0.4))
    cyl((20.0, -23.4, 0.95), 0.015, 0.3, brass, v=8); box((20.0, -23.4, 1.12), (0.4, 0.14, 0.08), green); ball((20.0, -23.4, 1.06), 0.04, m_emis('bankLamp', (1.0, 0.8, 0.45), 10), 2)
    bpy.ops.object.light_add(type='POINT', location=(20.0, -23.4, 1.0)); l = bpy.context.object; l.data.energy = 25; l.data.color = (1.0, 0.85, 0.5); l.data.shadow_soft_size = 0.1
    cashm = m_plain('cash', (0.38, 0.55, 0.32), 0.7)
    for k in range(6): box((21.2 + (k % 3) * 0.22, -23.3 + (k // 3) * 0.16, 0.85 + 0.03 * (k % 2)), (0.18, 0.08, 0.06 + 0.03 * (k % 2)), cashm)
    box((X1 - 0.5, -21.0, 0.6), (0.8, 0.8, 1.2), m_plain('safe', (0.12, 0.13, 0.15), 0.35, 0.7)); cyl((X1 - 0.89, -21.0, 0.7), 0.12, 0.04, brass, (0, math.pi / 2, 0), 16)
    box((X1 - 0.14, -24.0, 2.0), (0.04, 1.1, 0.7), m_plain('frame', (0.5, 0.36, 0.14), 0.4, 0.6))
    text('DISCIPLINE', (X1 - 0.17, -24.0, 2.0), 0.15, m_plain('frameInk', (0.15, 0.1, 0.08), 0.5), rot=(math.pi / 2, 0, -math.pi / 2), ext=0.002)
    for k in range(2): box((20.6 + k * 0.5, -22.2, 0.45), (0.45, 0.45, 0.9), m_plain('chair', (0.3, 0.12, 0.08), 0.5))

# the cut-away's front wall (shown except while we look inside)
with group('dhfront'):
    fw = solid_box((DH[0], -30.0, 1.8), (0.25, 20.0, 3.6), plaster, 'dhFront')
    for yy in (-37.0, -30.0, -23.0):
        c = solid_box((DH[0], yy, 1.9), (1.0, 1.6, 1.1), stone, 'dhWin'); cut(fw, c)

# ---- the poster (intact / torn) on the back wall of Andy's cell
with group('poster'):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, CD - 0.002, PZ), rotation=(math.pi / 2, 0, 0)); po = bpy.context.object; po.scale = (PW, PH_, 1)
    po.data.materials.append(img_mat('posterImg', os.path.join(ASSETS, 'poster.png'), 0.15))
with group('torn'):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, CD - 0.002, PZ), rotation=(math.pi / 2, 0, 0)); pt = bpy.context.object; pt.scale = (PW, PH_, 1)
    pt.data.materials.append(img_mat('posterTorn', os.path.join(ASSETS, 'poster_torn.png'), 0.15))
    for k in range(9):                                                      # paper scraps falling from the hole
        sz = random.uniform(0.04, 0.09); o = box((0, CD - 0.03, PZ), (sz, 0.004, sz * 1.3), m_plain('scrap%d' % k, (0.95, 0.75, 0.55), 0.8))
        hf = int(round(b['hit'] * FPS)); a = random.uniform(0, 2 * math.pi); vx, vz = math.cos(a) * random.uniform(0.3, 0.8), random.uniform(0.2, 1.0)
        for f in range(hf, hf + 150, 6):
            u = (f - hf) / FPS; o.location = (vx * u * 0.6, CD - 0.05 - 0.35 * u, PZ + vz * u * 0.5 - 1.6 * u * u); o.rotation_euler = (u * 5 + k, u * 3, u * 4)
            o.keyframe_insert('location', frame=f); o.keyframe_insert('rotation_euler', frame=f)

# ---- the rock the warden throws
with group('rock'):
    rk = ball((0, 0, 0), 0.07, m_noise('rockStone', (0.35, 0.33, 0.3), (0.5, 0.47, 0.42), 20, 0.9, 0.3), 2, (1.2, 1.0, 0.85))
    t0, t1 = b['rock2'] - 0.05, b['hit']
    P0, P1 = Vector((0.38, 1.0, 1.62)), Vector((0.0, CD - 0.05, PZ + 0.02))
    for f in range(int(t0 * FPS), int(t1 * FPS) + 40):
        t = f / FPS; u = clamp((t - t0) / (t1 - t0))
        if t <= t1: p = P0.lerp(P1, u) + Vector((0, 0, 0.12 * math.sin(math.pi * u)))
        else: p = P1 + Vector((0, 0.6 * (t - t1), -0.4 * (t - t1)))
        rk.location = p; rk.rotation_euler = (t * 9, t * 6, 0); rk.keyframe_insert('location', frame=f); rk.keyframe_insert('rotation_euler', frame=f)

# ---- the tunnel (from the poster down to the sewer pipe) and the pipe
tunm = m_noise('tunnelRock', (0.24, 0.2, 0.16), (0.42, 0.36, 0.28), 3.5, 0.95, 0.6)
cd_ = bpy.data.curves.new('tunnelPath', 'CURVE'); cd_.dimensions = '3D'; sp = cd_.splines.new('POLY'); sp.points.add(len(TUN) - 1)
for k, p in enumerate(TUN): sp.points[k].co = (*p, 1)
sp.use_smooth = True; cd_.bevel_depth = 0.46; cd_.bevel_resolution = 6; cd_.use_fill_caps = False
tob = bpy.data.objects.new('tunnel', cd_); sc.collection.objects.link(tob); bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = tob; tob.select_set(True)
bpy.ops.object.convert(target='MESH'); tob = bpy.context.object
md = tob.modifiers.new('sub', 'SUBSURF'); md.levels = 1; md.render_levels = 1
md2 = tob.modifiers.new('disp', 'DISPLACE'); tx_ = bpy.data.textures.new('tunTex', 'CLOUDS'); tx_.noise_scale = 0.25; md2.texture = tx_; md2.strength = -0.12; md2.mid_level = 0.5
tob.data.materials.append(tunm); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
for o in tob.data.polygons: o.use_smooth = True
SETS['prison'].append(tob)
chalk = m_emis('chalk', (0.95, 0.92, 0.8), 0.6)
for k in range(14):                                                         # tally marks scratched on the tunnel wall
    y = 3.9 + (k // 5) * 0.55 + (k % 5) * 0.07; z = 1.45 - (y - 3.9) * 0.35
    o = box((0.4, y, z), (0.01, 0.012, 0.18), chalk, (0.0, 0.0, 0.0)); o.rotation_euler = (0.25 if k % 5 == 4 else 0, 0, 0)
    if k % 5 == 4: o.scale = (0.01, 0.012, 0.36); o.rotation_euler = (1.1, 0, 0); o.location = (0.4, y - 0.14, z)
    SETS['prison'].append(o)
for (y, z) in [(4.0, 1.25), (7.2, -0.6), (10.4, -3.4)]:                    # lanterns
    o = ball((0.3, y, z), 0.05, m_emis('lantern', (1.0, 0.6, 0.25), 18), 2); SETS['prison'].append(o)
    bpy.ops.object.light_add(type='POINT', location=(0.2, y, z)); l = bpy.context.object; l.data.energy = 9; l.data.color = (1.0, 0.6, 0.3); l.data.shadow_soft_size = 0.05; SETS['prison'].append(l)
pipem = bpy.data.materials.new('pipe'); pipem.use_nodes = True; pn = pipem.node_tree.nodes; pb = pn['Principled BSDF']; PL = pipem.node_tree.links.new
bk = pn.new('ShaderNodeTexBrick'); bk.inputs['Scale'].default_value = 3.0; bk.inputs['Color1'].default_value = (0.2, 0.22, 0.16, 1); bk.inputs['Color2'].default_value = (0.15, 0.18, 0.12, 1); bk.inputs['Mortar'].default_value = (0.06, 0.07, 0.05, 1)
gco = pn.new('ShaderNodeTexCoord'); PL(gco.outputs['Object'], bk.inputs['Vector']); PL(bk.outputs['Color'], pb.inputs['Base Color'])
pz_ = pn.new('ShaderNodeTexNoise'); pz_.inputs['Scale'].default_value = 1.5; PL(gco.outputs['Object'], pz_.inputs['Vector']); pr_ = pn.new('ShaderNodeMapRange'); PL(pz_.outputs['Fac'], pr_.inputs['Value']); pr_.inputs['To Min'].default_value = 0.08; pr_.inputs['To Max'].default_value = 0.6
PL(pr_.outputs['Result'], pb.inputs['Roughness']); pb.inputs['Emission Color'].default_value = (0.25, 0.5, 0.15, 1); pb.inputs['Emission Strength'].default_value = 0.04
bpy.ops.mesh.primitive_cylinder_add(radius=PR, depth=PIPE1 - PIPE0, vertices=32, end_fill_type='NOTHING', location=(0, (PIPE0 + PIPE1) / 2, PZP), rotation=(math.pi / 2, 0, 0))
pipe = bpy.context.object; pipe.data.materials.append(pipem); bpy.ops.object.shade_smooth()
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT'); SETS['prison'].append(pipe)
sludge = m_plain('sludge', (0.08, 0.1, 0.05), 0.08)
o = box((0, (PIPE0 + PIPE1) / 2, PZP - PR + 0.08), (1.1, PIPE1 - PIPE0, 0.02), sludge); SETS['prison'].append(o)
for y in range(16, 50, 6):
    bpy.ops.object.light_add(type='POINT', location=(0.0, y, PZP + 0.45)); l = bpy.context.object; l.data.energy = 6; l.data.color = (0.55, 0.9, 0.45); l.data.shadow_soft_size = 0.3; SETS['prison'].append(l)
# the outfall and the storm ditch outside the north wall
hw = solid_box((0, PIPE1 + 0.3, PZP + 0.6), (5.0, 0.6, 3.4), m_noise('headwall', (0.3, 0.3, 0.29), (0.42, 0.41, 0.39), 3, 0.9, 0.2), 'headwall')
pc2 = solid_box((0, PIPE1 + 0.3, PZP), (1.55, 1.6, 1.55), stone, 'outfallCut'); cut(hw, pc2); SETS['prison'].append(hw)
mud = m_noise('mud', (0.12, 0.09, 0.06), (0.22, 0.17, 0.11), 2.0, 0.35, 0.3)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=1, location=(0, 0, 0)); dg = bpy.context.object; dg.scale = (60, 60, 1); bpy.ops.object.transform_apply(scale=True)
for v in dg.data.vertices:
    x, y = v.co.x, v.co.y + 70.0; v.co.y = y
    dz = (CREEK - 0.2) * clamp(1 - (abs(x) - 2.5) / 5.0) if y > PIPE1 - 0.5 else 0
    v.co.z = dz + (0.15 * math.sin(x * 0.7) * math.cos(y * 0.5) if abs(x) > 7 else 0)
dg.data.materials.append(mud); bpy.ops.object.shade_smooth(); SETS['prison'].append(dg)
water = bpy.data.materials.new('creek'); water.use_nodes = True; wb = water.node_tree.nodes['Principled BSDF']; wb.inputs['Base Color'].default_value = (0.03, 0.05, 0.06, 1); wb.inputs['Roughness'].default_value = 0.05
o = box((0, 75.0, CREEK), (6.0, 50.0, 0.02), water); SETS['prison'].append(o)
for k in range(40):                                                         # dead trees on the field
    x = random.choice([-1, 1]) * random.uniform(9, 40); y = random.uniform(52, 110)
    o = cyl((x, y, 2.5), 0.18, 5.0, m_plain('deadTree', (0.1, 0.08, 0.07), 0.9), v=6); SETS['prison'].append(o)
    for j in range(3): o2 = cyl((x + 0.4 * (j - 1), y, 4.5 + j * 0.4), 0.06, 2.0, m_plain('deadTree', (0.1, 0.08, 0.07), 0.9), (0.6 * (j - 1), 0.3, 0), 5); SETS['prison'].append(o2)
# outside the gate: the road south
o = box((0.6, -130.0, -0.02), (5.0, 140.0, 0.04), m_noise('road', (0.2, 0.2, 0.2), (0.28, 0.28, 0.27), 4, 0.8, 0.05)); SETS['prison'].append(o)
o = solid_box((0, -130.0, -0.09), (300, 140, 0.1), grass, 'fieldS'); SETS['prison'].append(o)
for k in range(50):
    x = random.choice([-1, 1]) * random.uniform(8, 120); y = random.uniform(-200, -70); F2.tree(x, y, 0, random.uniform(7, 14), m_plain('trunk', (0.25, 0.15, 0.08), 0.9), m_plain('leaf1', (0.09, 0.3, 0.07), 0.8), m_plain('leaf2', (0.14, 0.4, 0.1), 0.8))
SETS['prison'] += [o for o in bpy.data.objects if o.name.startswith(('cone', 'cyl')) and o.location.y < -70 and o not in SETS['prison']]

# searchlight beams (night only): a soft additive cone + a real spot light, sweeping
beam_m = bpy.data.materials.new('beam'); beam_m.use_nodes = True; bn = beam_m.node_tree.nodes; out_ = bn['Material Output']
bn.remove(bn['Principled BSDF']); em = bn.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.9, 0.93, 1.0, 1); em.inputs['Strength'].default_value = 0.5
tr = bn.new('ShaderNodeBsdfTransparent'); ad = bn.new('ShaderNodeAddShader'); beam_m.node_tree.links.new(em.outputs[0], ad.inputs[0]); beam_m.node_tree.links.new(tr.outputs[0], ad.inputs[1]); beam_m.node_tree.links.new(ad.outputs[0], out_.inputs['Surface'])
BEAMS = []
with group('beams'):
    for k, (x, y) in enumerate([TOWERS[0], TOWERS[4], TOWERS[1]]):
        bpy.ops.object.empty_add(location=(x, y + 1.0, 14.8)); piv = bpy.context.object
        bpy.ops.mesh.primitive_cone_add(radius1=3.2, radius2=0.0, depth=40, vertices=24, end_fill_type='NOTHING', location=(0, 0, -20)); bc = bpy.context.object; bc.parent = piv; bc.location = (0, 0, -20)
        bc.data.materials.append(beam_m); bc.visible_shadow = False
        bpy.ops.object.light_add(type='SPOT', location=(0, 0, 0)); sl = bpy.context.object; sl.parent = piv; sl.location = (0, 0, 0); sl.data.energy = 9000; sl.data.spot_size = math.radians(9); sl.data.color = (0.9, 0.93, 1.0); sl.data.shadow_soft_size = 0.2
        BEAMS.append((piv, k))

# ================================================================== THE BEACH =======================================
with group('beach'):
    sand = m_noise('sand', (0.86, 0.76, 0.56), (0.95, 0.87, 0.68), 1.5, 0.9, 0.15)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=1, location=(BX, 0, 0)); sg = bpy.context.object; sg.scale = (220, 220, 1); bpy.ops.object.transform_apply(scale=True)
    for v in sg.data.vertices: v.co.z = 0.12 - 0.08 * (v.co.y - 3) if v.co.y > 3 else 0.12 + 0.04 * math.sin(v.co.x * 0.3) * math.cos(v.co.y * 0.4)
    sg.data.materials.append(sand); bpy.ops.object.shade_smooth()
    sea = bpy.data.materials.new('sea'); sea.use_nodes = True; sn = sea.node_tree.nodes; sb = sn['Principled BSDF']; SL = sea.node_tree.links.new
    sb.inputs['Base Color'].default_value = (0.0, 0.42, 0.48, 1); sb.inputs['Roughness'].default_value = 0.07
    sw_ = sn.new('ShaderNodeTexWave'); sw_.inputs['Scale'].default_value = 0.6; sw_.inputs['Distortion'].default_value = 4; sw_.bands_direction = 'X'
    sbm = sn.new('ShaderNodeBump'); sbm.inputs['Strength'].default_value = 0.08; SL(sw_.outputs['Fac'], sbm.inputs['Height']); SL(sbm.outputs['Normal'], sb.inputs['Normal'])
    o = box((BX, 1500.0, 0.02), (6000, 3000, 0.02), sea)
    o = box((BX, 4.6, 0.035), (400, 0.35, 0.01), m_emis('foam', (1.0, 1.0, 1.0), 0.6))
    hull = m_plain('hull', (0.92, 0.92, 0.9), 0.35); stripe = m_plain('stripe', (0.1, 0.35, 0.62), 0.4)
    o = ball((BX + 1.6, 1.6, 0.42), 1.0, hull, 3, (0.9, 2.4, 0.55)); o.rotation_euler = (0, 0.08, 0.25)
    o = ball((BX + 1.6, 1.6, 0.52), 1.0, stripe, 3, (0.92, 2.42, 0.12)); o.rotation_euler = (0, 0.08, 0.25)
    box((BX + 1.75, 2.2, 1.6), (0.07, 0.07, 2.4), woodL)
    for (x, y, h, lean) in [(BX - 7.5, 3.0, 7.0, 0.25), (BX - 9.0, -2.0, 8.0, -0.2), (BX + 8.0, 2.0, 7.5, -0.3), (BX + 11.0, -4.0, 9.0, 0.2), (BX - 16.0, 1.0, 6.5, 0.1)]:
        trunk = m_plain('palmTrunk', (0.42, 0.3, 0.18), 0.85)
        for j in range(8):
            u = j / 8; cyl((x + math.sin(lean) * h * u * u, y, h * u + h / 16), 0.22 - 0.1 * u, h / 8 + 0.05, trunk, (0, lean * u * 1.5, 0), 10)
        top = (x + math.sin(lean) * h, y, h)
        for j in range(8):
            a = j / 8 * 2 * math.pi; o = cone((top[0] + math.cos(a) * 1.4, top[1] + math.sin(a) * 1.4, top[2] - 0.3), 0.55, 3.2, m_plain('palmLeaf', (0.12, 0.42, 0.1), 0.6), 4, (math.pi / 2 + 0.35, 0, a + math.pi / 2))
            o.scale = (0.55, 0.12, 3.2)
    for k in range(6):                                                    # islands on the horizon
        ball((BX + random.uniform(-600, 600), random.uniform(500, 900), -20), random.uniform(60, 140), m_plain('island', (0.12, 0.22, 0.14), 0.9), 2, (1.6, 1.0, 0.45))
    ball((BX + 370.0, 1400.0, 150.0), 26.0, m_emis('sunDisc', (1.0, 0.72, 0.38), 30), 3)

# ------------------------------------------------------------------ visibility / animation keys ---------------------
def key_hide(objs, keys):
    for o in objs:
        for (t, h) in keys:
            o.hide_render = h; o.keyframe_insert('hide_render', frame=max(0, int(round(t * FPS))))
prison_objs = [o for o in bpy.data.objects if o not in SETS['beach'] and o.type in ('MESH', 'CURVE', 'FONT', 'LIGHT') and o not in (sun, moon, bolt)]
key_hide(SETS['beach'], [(0, True), (b['flashD'], False)])
key_hide(prison_objs, [(0, False), (b['flashD'], True)])
key_hide(SETS['dhfront'], [(0, False), (b['years'] - 0.3, True), (b['then2'] + 0.9, False), (b['flashD'], True)])
key_hide(SETS['beams'] + [c for p, _ in BEAMS for c in p.children], [(0, True), (b['then2'] - 0.3, False), (b['shot'], True)])
key_hide(SETS['poster'], [(0, False), (b['hit'], True)])
key_hide(SETS['torn'], [(0, True), (b['hit'], False), (b['flashD'], True)])
key_hide(SETS['rock'], [(0, True), (b['rock2'] - 0.05, False), (b['hit'] + 0.7, True)])
for ob in bpy.data.objects:
    ad_ = ob.animation_data
    if ad_ and ad_.action:
        for fc in ad_.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT' if fc.data_path == 'hide_render' else 'LINEAR'
# Andy's door swings open for roll call; the cell bulb is on at night
for (t, a) in [(0, 0.0), (b['gone'] - 0.6, 0.0), (b['gone'] - 0.1, -100.0)]: hinge.rotation_euler = (0, 0, math.radians(a)); hinge.keyframe_insert('rotation_euler', frame=int(round(t * FPS)))
for (t, e) in [(0, 30.0), (b['vanish'] - 0.01, 30.0), (b['vanish'], 0.0)]: cellbulb.data.energy = e; cellbulb.data.keyframe_insert('energy', frame=int(round(t * FPS)))
for f in range(NF):                                                        # sky, sun, moon, lightning, searchlights per frame
    t = f / FPS; el, az, ovc, nig, ss, se, me = light_at(t)
    sky.sun_elevation = math.radians(max(el, -6)); sky.sun_rotation = math.radians(az + 180); sky.keyframe_insert('sun_elevation', frame=f); sky.keyframe_insert('sun_rotation', frame=f)
    ov.inputs[0].default_value = ovc; ov.inputs[0].keyframe_insert('default_value', frame=f); nb.inputs[0].default_value = nig; nb.inputs[0].keyframe_insert('default_value', frame=f)
    bg.inputs['Strength'].default_value = ss; bg.inputs['Strength'].keyframe_insert('default_value', frame=f)
    sun.rotation_euler = (math.radians(90 - max(el, 0.5)), 0, math.radians(az)); sun.keyframe_insert('rotation_euler', frame=f)
    warm = clamp(1 - (el - 5) / 30); sun.data.color = (1.0, 0.93 - 0.25 * warm, 0.84 - 0.42 * warm); sun.data.keyframe_insert('color', frame=f)
    sun.data.energy = se if el > -1 else 0.0; sun.data.keyframe_insert('energy', frame=f)
    moon.data.energy = me; moon.data.keyframe_insert('energy', frame=f); bolt.data.energy = bolt_at(t); bolt.data.keyframe_insert('energy', frame=f)
    for piv, k in BEAMS:
        a = t * (0.55 + 0.17 * k) + k * 2.1; piv.rotation_euler = (math.radians(46 + 10 * math.sin(a * 1.3)), 0, math.radians([-30, 0, 30][k] + 28 * math.sin(a))); piv.keyframe_insert('rotation_euler', frame=f)
for idb in (sky, ov.inputs[0], nb.inputs[0], bg.inputs['Strength']): pass
for owner in (w.node_tree, sun, sun.data, moon.data, bolt.data, hinge, cellbulb.data):
    if owner.animation_data and owner.animation_data.action:
        for fc in owner.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ camera ---------------------------------------
bpy.ops.object.camera_add(location=SEG_A[0][1]); cam = bpy.context.object; cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24; cam.data.clip_start = 0.04; cam.data.clip_end = 9000; sc.camera = cam
tgt = bpy.data.objects.new('camTarget', None); sc.collection.objects.link(tgt)
tc_ = cam.constraints.new('TRACK_TO'); tc_.target = tgt; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
for f in range(NF):
    t = f / FPS; p_, l_, lens = cam_at(t); cam.location = p_; tgt.location = l_; cam.data.lens = lens
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f); cam.data.keyframe_insert('lens', frame=f)
for ob in (cam, tgt, cam.data):
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# camera + actor tracks + roll + beats for the engine
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
