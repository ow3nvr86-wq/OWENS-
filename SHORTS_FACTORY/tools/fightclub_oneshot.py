"""MOVIES IN A MINUTE: FIGHT CLUB. One continuous camera move through one rainy night city (no cuts):
  the bar basement (two men under one bulb; one of them flickers out) -> up the cellar steps, across the street, in at
  an office window (3 AM, fluorescent green) -> down into a church hall (a support-group circle) -> straight up through
  the clouds into a plane's cut-away cabin -> dive to a condo tower as one apartment explodes -> the payphone below ->
  the bar's parking lot (the first fight) -> back down the cellar steps (a ring of men) -> along the street to a
  crumbling house, in at the kitchen window (pink soap) -> out to the street (an army in black) -> police lights, a
  man falls -> up a high-rise to the top floor (the truth; a flash) -> through the north windows, the credit-card
  towers blow and fall -> the camera floats out over the skyline.
Characters are 2D (engine); this script exports their 3D tracks in camera.json. Every time comes from a cue word.
Run: $BLENDER -b --factory-startup -P tools/fightclub_oneshot.py -- <out> --words <words.json> [--scale 0.5]
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
CUES = [('fight1', 'fight'), ('problem', 'problem'), ('exist', 'exist'), ('lonely', 'lonely'), ('sleep', 'sleep'), ('so', 'so'), ('support', 'support'),
        ('finally', 'finally'), ('sleeps', 'sleeps'), ('marla', 'marla'), ('faker', 'faker'), ('ruins', 'ruins'), ('flight', 'flight'), ('meets', 'meets'),
        ('tyler1', 'tyler'), ('soap1', 'soap'), ('then', 'then'), ('explodes', 'explodes'), ('calls', 'calls'), ('bar1', 'bar'), ('hit', 'hit'),
        ('fight2', 'fight'), ('soon', 'soon'), ('basement', 'basement'), ('rule', 'rule'), ('talk', 'talk'), ('move', 'move'), ('crumbling', 'crumbling'),
        ('tyler3', 'tyler'), ('soap2', 'soap'), ('fat', 'fat'), ('then2', 'then'), ('army', 'army'), ('project', 'project'), ('police', 'police'),
        ('kill', 'kill'), ('bob', 'bob'), ('shut', 'shut'), ('discovers', 'discovers'), ('truth', 'truth'), ('heis', 'he'), ('tyler4', 'tyler'),
        ('stop', 'stop'), ('shoots', 'shoots'), ('cheek', 'cheek'), ('gone', 'tylers'), ('bombs', 'bombs'), ('holds', 'holds'), ('hand', 'hand'),
        ('towers', 'towers'), ('fall', 'fall'), ('would', 'would')]
B = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while j < len(ws) and norm(ws[j]['word']) != cue: j += 1
    if j == len(ws): raise SystemExit('cue word not found: ' + cue)
    B[key] = ws[j]['start']; wi = j + 1
B['end'] = DUR
B['vanish'] = B['exist'] + 0.25          # Tyler flickers out of the hook shot
B['boom'] = B['explodes'] + 0.08         # the apartment blows
B['shotB'] = B['kill'] + 0.06            # police shoot Bob
B['glitch'] = B['heis'] - 0.05           # "He is Tyler"
B['bang'] = B['cheek'] + 0.12            # the flash in the top floor
B['bomb0'] = B['bombs'] + 0.12           # first charge
B['crash'] = B['towers'] - 0.5           # the towers start to fall
b = B
print('beats', json.dumps({k: round(v, 2) for k, v in B.items()}), flush=True)

def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def clamp(u, a=0.0, c=1.0): return min(c, max(a, u))
def lerp3(a, c, u): return tuple(x + (y - x) * u for x, y in zip(a, c))

# ------------------------------------------------------------------ layout (metres) ---------------------------------
# main street runs along x (road y -16..-8, sidewalks to -6 / -18); north side: the bar (x -7..7), the lot, the condo
# tower; far east: the crumbling house and the high-rise.  South side: the office tower and the church hall.
BZ = -4.0                                # basement floor
OFZ = 9.0                                # office floor (3rd floor of the office tower)
PLZ = 108.4                              # plane cabin floor
KZ = 0.4                                 # house kitchen floor
TZ = 58.2                                # high-rise top floor
APT = (24.0, 6.0, 28.5)                  # the exploding apartment window (south face of the condo tower)

# ------------------------------------------------------------------ the 2D actors' tracks ---------------------------
def walk(t, t0, t1, p0, p1):
    u = clamp((t - t0) / (t1 - t0)); return lerp3(p0, p1, u)
def seg(t, table):                        # [(t0, t1, fn(t) -> pos)], vis 0 outside
    for t0, t1, fn in table:
        if t0 <= t < t1: return fn(t), 1
    return (0, 0, -80), 0
C_ = lambda p: (lambda t: p)
RING = [(-3.3, 0.6), (-2.9, 1.6), (-2.0, 2.4), (3.3, 0.6), (2.9, 1.6), (2.2, 2.2), (-1.3, 3.0), (2.1, 3.1)]
HOOK, CLUB = (0.0, b['vanish'] + 0.45), (b['soon'] + 0.3, b['move'] + 0.2)
def glitch_slide(t):                      # Tyler lurches into the narrator and back
    g0 = b['glitch']
    if t < g0: return (87.2, 9.4, TZ)
    if t < g0 + 0.25: return lerp3((87.2, 9.4, TZ), (85.3, 9.15, TZ), ease((t - g0) / 0.25))
    if t < g0 + 0.6: return (85.3, 9.15, TZ)
    return lerp3((85.3, 9.15, TZ), (87.2, 9.4, TZ), ease((t - g0 - 0.6) / 0.35))
def bob_street(t):
    if t < b['shotB']: return (72.2, -9.4, 0.0)
    return (72.2, -9.4, -0.8 * ease((t - b['shotB']) / 0.35))
TRACKS = {
    'narr': lambda t: seg(t, [(*HOOK, C_((-0.62, 0.6, BZ))), (HOOK[1], b['so'] + 0.25, C_((-18.5, -27.6, OFZ))),
                              (b['so'] + 0.25, b['ruins'] + 0.6, C_((-37.0, -29.7, 0.0))), (b['ruins'] + 0.6, b['then'] - 0.2, C_((-20.85, 20.35, PLZ))),
                              (b['then'] - 0.2, b['soon'] + 0.3, lambda t: walk(t, b['calls'] + 0.45, b['bar1'] + 0.35, (20.4, -7.15, 0.12), (13.3, -3.7, 0.0))),
                              (*CLUB, C_((2.0, -0.95, BZ))), (b['move'] + 0.2, b['then2'] + 0.4, C_((54.6, 2.15, KZ))),
                              (b['shut'] - 0.6, b['bang'], C_((85.1, 9.1, TZ)))]),
    'narr_b': lambda t: seg(t, [(b['bang'], DUR + 1, C_((85.1, 9.1, TZ)))]),
    'tyler': lambda t: seg(t, [((0.0), b['vanish'], C_((0.62, 0.6, BZ))), (b['ruins'] + 0.6, b['then'] - 0.2, C_((-19.75, 20.35, PLZ))),
                               (b['bar1'] - 0.6, b['soon'] + 0.3, C_((12.0, -3.5, 0.0))), (*CLUB, C_((1.3, 2.3, BZ))),
                               (b['move'] + 0.2, b['then2'] + 0.4, C_((56.0, 2.05, KZ))), (b['discovers'] - 0.05, b['gone'] - 0.05, glitch_slide)]),
    'bob': lambda t: seg(t, [(b['so'] + 0.25, b['ruins'] + 0.6, C_((-35.65, -29.38, 0.0))), (*CLUB, C_((-2.0, -0.95, BZ))),
                             (b['then2'] + 1.6, b['shut'] - 0.3, bob_street)]),
    'marla': lambda t: seg(t, [(b['marla'] - 0.3, b['ruins'] + 0.6, lambda t: walk(t, b['marla'] - 0.3, b['marla'] + 0.9, (-42.6, -28.6, 0.0), (-39.19, -28.53, 0.0))),
                               (b['holds'] - 0.55, DUR + 1, lambda t: walk(t, b['holds'] - 0.55, b['holds'] + 0.4, (81.6, 9.5, TZ), (86.25, 9.25, TZ)))]),
    'sg1': lambda t: seg(t, [(b['so'] + 0.25, b['ruins'] + 0.6, C_((-38.35, -29.38, 0.0)))]),
    'sg2': lambda t: seg(t, [(b['so'] + 0.25, b['ruins'] + 0.6, C_((-34.81, -28.53, 0.0)))]),
    'pat1': lambda t: seg(t, [(b['fight2'] - 0.2, b['soon'] + 0.3, lambda t: walk(t, b['fight2'] - 0.2, b['soon'] + 0.2, (7.6, -1.6, 0.0), (10.6, -2.4, 0.0)))]),
    'pat2': lambda t: seg(t, [(b['fight2'] - 0.1, b['soon'] + 0.3, lambda t: walk(t, b['fight2'] - 0.1, b['soon'] + 0.3, (7.6, -0.6, 0.0), (11.0, -1.2, 0.0)))]),
    'f1': lambda t: seg(t, [(*CLUB, C_((-0.9, 0.4, BZ)))]),
    'f2': lambda t: seg(t, [(*CLUB, C_((0.2, 0.45, BZ)))]),
    'cop': lambda t: seg(t, [(b['then2'] + 1.6, b['shut'] - 0.3, C_((75.3, -10.9, 0.0)))]),
}
for k, (x, y) in enumerate(RING):
    TRACKS['c%d' % k] = (lambda p: (lambda t: seg(t, [(*HOOK, C_(p)), (*CLUB, C_(p))])))((x, y, BZ))
ARMY = [(52.6 + 2.15 * c, -9.2 + 1.55 * r) for r in range(3) for c in range(4)]
for k, (x, y) in enumerate(ARMY):
    TRACKS['m%d' % k] = (lambda p: (lambda t: seg(t, [(b['then2'] - 0.2, b['police'] - 0.3, lambda t: walk(t, b['then2'] - 0.2, b['police'] - 0.3, (p[0], p[1], 0.0), (p[0], p[1] - 1.6, 0.0)))])))((x, y))
def roll_at(t):                           # Bob falls flat when he is shot
    if t < b['shotB'] or t > b['shut']: return 0.0
    return -1.5 * ease((t - b['shotB']) / 0.35)

# ------------------------------------------------------------------ camera (t, position, look-at, lens) -------------
SEG_A = [
    (0.0, (0.0, -3.5, -2.72), (0.0, 0.6, -3.05), 20),
    (b['exist'], (0.0, -2.75, -2.78), (0.0, 0.6, -3.05), 20),
    (b['exist'] + 0.34, (-0.35, -3.6, -2.6), (-3.0, -4.0, -2.5), 20),
    (b['exist'] + 0.6, (-0.8, -5.2, -2.4), (-0.8, -9.0, -1.6), 20),
    (b['exist'] + 0.8, (-0.8, -7.1, -1.8), (-1.0, -9.5, 0.5), 20),
    (b['exist'] + 1.0, (-1.0, -7.7, 0.4), (-4.0, -12.0, 3.0), 20),
    (b['lonely'] + 0.35, (-7.0, -13.0, 6.5), (-18.0, -21.0, 10.4), 20),
    (b['lonely'] + 0.75, (-15.5, -17.5, 10.6), (-18.3, -25.0, 10.2), 22),
    (b['lonely'] + 1.05, (-18.1, -20.8, 10.6), (-18.5, -27.6, 9.9), 22),
    (b['sleep'] + 0.1, (-18.2, -23.6, 10.45), (-18.5, -27.6, 9.9), 24),
    (b['so'], (-18.2, -24.0, 10.4), (-18.5, -27.6, 9.9), 24),
    (b['so'] + 0.27, (-18.3, -21.2, 10.6), (-21.0, -17.0, 9.0), 22),
    (b['so'] + 0.42, (-19.3, -19.3, 10.3), (-28.0, -17.0, 6.0), 22),
    (b['so'] + 0.72, (-25.0, -17.6, 6.0), (-37.0, -24.0, 2.0), 22),
    (b['support'] + 0.01, (-36.0, -18.4, 2.2), (-37.0, -29.0, 1.1), 22),
    (b['support'] + 0.41, (-37.0, -22.6, 1.85), (-37.0, -29.5, 0.95), 24),
    (b['sleeps'], (-37.2, -24.3, 1.7), (-37.2, -29.6, 0.9), 24),
    (b['marla'] + 0.3, (-37.6, -24.4, 1.7), (-38.4, -29.3, 0.95), 24),
    (b['ruins'], (-37.4, -24.8, 1.65), (-37.8, -29.5, 0.95), 25),
    (b['ruins'] + 0.35, (-37.0, -21.8, 2.0), (-37.0, -17.0, 6.0), 22),
    (b['ruins'] + 0.5, (-37.0, -20.0, 2.6), (-35.0, -12.0, 20.0), 22),
    (b['ruins'] + 0.7, (-37.0, -18.6, 5.0), (-33.0, -8.0, 40.0), 22),
    (b['ruins'] + 1.1, (-31.0, -6.0, 40.0), (-22.0, 18.0, 105.0), 22),
    (b['ruins'] + 1.55, (-22.5, 10.0, 104.5), (-20.4, 20.4, 109.2), 22),
    (b['ruins'] + 1.95, (-20.6, 15.2, 109.7), (-20.3, 20.5, 109.2), 22),
    (b['tyler1'], (-20.4, 15.8, 109.6), (-20.3, 20.5, 109.2), 22),
    (b['soap1'] + 0.6, (-20.0, 16.1, 109.6), (-20.0, 20.5, 109.25), 23),
    (b['then'] - 0.48, (-19.5, 13.5, 108.0), (-5.0, 0.0, 80.0), 22),
    (b['then'] - 0.03, (5.0, -6.0, 62.0), (24.0, 6.0, 32.0), 22),
    (b['then'] + 0.47, (23.4, -9.0, 31.5), (24.0, 6.0, 28.6), 24),
    (b['explodes'], (23.5, -9.6, 31.0), (24.0, 6.0, 28.6), 24),
    (b['explodes'] + 0.56, (22.6, -11.0, 24.0), (23.6, 6.0, 25.0), 24),
    (b['calls'] - 0.08, (20.0, -13.6, 2.4), (21.2, -6.5, 3.2), 24),
    (b['calls'] + 0.57, (19.8, -13.0, 1.6), (20.6, -7.0, 1.1), 24),
    (b['bar1'], (15.6, -11.5, 1.8), (13.0, -3.5, 1.4), 24),
    (b['hit'], (13.0, -9.4, 1.6), (12.7, -3.5, 1.2), 24),
    (b['fight2'], (12.9, -8.8, 1.55), (12.6, -3.5, 1.2), 25),
    (b['soon'], (12.4, -9.4, 1.9), (9.0, -6.0, 1.0), 24),
    (b['soon'] + 0.47, (4.0, -11.6, 2.6), (-1.0, -7.0, -1.0), 22),
    (b['soon'] + 0.87, (-0.9, -8.4, 1.6), (-0.8, -6.0, -2.2), 22),
    (b['soon'] + 1.17, (-0.8, -7.0, -1.6), (-0.6, -3.0, -2.6), 22),
    (b['soon'] + 1.52, (-0.6, -5.3, -2.4), (0.0, 0.0, -2.9), 20),
    (b['basement'] + 0.55, (0.6, -3.2, -2.5), (0.1, 0.6, -3.0), 20),
    (b['rule'], (0.6, -2.7, -2.55), (0.8, 1.8, -2.8), 20),
    (b['talk'] + 0.55, (0.6, -2.4, -2.55), (0.9, 2.0, -2.8), 21),
    (b['move'] - 0.25, (-0.3, -3.6, -2.5), (-3.0, -4.2, -2.5), 20),
    (b['move'], (-0.8, -5.2, -2.4), (-0.8, -9.0, -1.6), 20),
    (b['move'] + 0.2, (-0.8, -7.1, -1.6), (-1.0, -9.5, 0.5), 20),
    (b['move'] + 0.4, (-0.9, -7.7, 0.5), (6.0, -12.0, 3.0), 20),
    (b['move'] + 0.9, (25.0, -15.0, 9.0), (56.0, -6.0, 4.0), 22),
    (b['tyler3'] - 0.43, (55.6, -14.5, 4.2), (55.6, -4.0, 2.5), 22),
    (b['tyler3'], (55.3, -8.0, 2.0), (55.2, -3.8, 1.8), 22),
    (b['soap2'] - 0.15, (55.2, -4.8, 1.85), (55.3, 0.0, 1.45), 22),
    (b['soap2'] + 0.35, (55.2, -2.4, 1.75), (55.3, 2.2, 1.2), 22),
    (b['fat'], (55.2, -1.7, 1.7), (55.3, 2.2, 1.2), 23),
    (b['then2'] - 0.15, (55.2, -3.2, 1.85), (55.3, 0.0, 1.6), 22),
    (b['then2'] + 0.35, (55.4, -9.5, 2.6), (56.0, -4.0, 2.4), 22),
    (b['army'], (56.0, -15.2, 2.2), (56.0, -7.6, 1.5), 22),
    (b['project'] + 0.8, (56.4, -16.2, 2.3), (56.6, -7.6, 1.5), 23),
    (b['police'] - 0.58, (60.0, -19.5, 2.3), (68.0, -12.0, 1.6), 23),
    (b['police'] - 0.18, (69.6, -16.9, 1.8), (73.7, -10.2, 1.1), 21),
    (b['bob'], (70.3, -16.4, 1.8), (73.6, -10.0, 0.9), 21),
    (b['shut'] - 0.64, (72.0, -16.0, 3.5), (84.0, -4.0, 20.0), 22),
    (b['shut'] - 0.09, (82.0, -15.0, 26.0), (86.0, -4.0, 50.0), 22),
    (b['shut'] + 0.46, (86.2, -12.0, 59.6), (86.0, 0.0, 59.4), 22),
    (b['shut'] + 0.86, (86.0, -5.0, 59.9), (86.0, 8.0, 59.2), 22),
    (b['discovers'], (86.0, -0.5, 59.8), (86.1, 9.4, 59.0), 22),
    (b['truth'], (86.0, 1.2, 59.7), (86.1, 9.4, 59.0), 23),
    (b['heis'], (86.0, 2.4, 59.65), (86.0, 9.4, 59.0), 24),
    (b['stop'], (85.6, 2.8, 59.6), (86.0, 9.4, 59.0), 24),
    (b['cheek'], (85.4, 3.2, 59.6), (85.8, 9.4, 59.0), 24),
    (b['gone'], (85.4, 3.4, 59.6), (85.8, 9.4, 59.05), 24),
    (b['bombs'], (85.8, 2.4, 59.9), (88.0, 40.0, 62.0), 22),
    (b['holds'], (85.6, 4.2, 59.8), (86.5, 14.0, 60.0), 22),
    (b['towers'], (85.6, 5.0, 59.9), (86.8, 30.0, 62.0), 22),
    (b['would'], (85.6, 7.5, 60.9), (88.0, 40.0, 63.0), 22),
    (DUR, (86.4, 19.0, 61.35), (90.0, 100.0, 50.0), 22),
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

# ------------------------------------------------------------------ scene -------------------------------------------
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

# ---- world: a deep teal night with an amber city glow on the horizon
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']; L = nt.links.new
tco = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L(tco.outputs['Generated'], sep.inputs[0])
ramp = nt.nodes.new('ShaderNodeValToRGB'); L(sep.outputs['Z'], ramp.inputs['Fac'])
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.16, 0.085, 0.05, 1)
ramp.color_ramp.elements[1].position = 0.4; ramp.color_ramp.elements[1].color = (0.008, 0.026, 0.042, 1)
e_ = ramp.color_ramp.elements.new(0.08); e_.color = (0.05, 0.07, 0.08, 1)
L(ramp.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0
bpy.ops.object.light_add(type='SUN'); moon = bpy.context.object; moon.data.angle = math.radians(3); moon.data.color = (0.55, 0.72, 0.95); moon.data.energy = 0.22
moon.rotation_euler = (math.radians(58), 0, math.radians(200))

# ---- materials
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
WALLS = [(0.16, 0.15, 0.15), (0.22, 0.17, 0.13), (0.12, 0.13, 0.15), (0.25, 0.22, 0.19), (0.1, 0.11, 0.1)]
CITYM = [m_city('city%d' % k, WALLS[k], lit=[0.3, 0.22, 0.35, 0.26, 0.3][k]) for k in range(5)]
asph = bpy.data.materials.new('wetAsphalt'); asph.use_nodes = True; an_ = asph.node_tree.nodes; ab = an_['Principled BSDF']; AL = asph.node_tree.links.new
anz = an_.new('ShaderNodeTexNoise'); anz.inputs['Scale'].default_value = 0.35; anz.inputs['Detail'].default_value = 6
amr = an_.new('ShaderNodeMapRange'); AL(anz.outputs['Fac'], amr.inputs['Value']); amr.inputs['From Min'].default_value = 0.45; amr.inputs['From Max'].default_value = 0.6
amr.inputs['To Min'].default_value = 0.08; amr.inputs['To Max'].default_value = 0.6; AL(amr.outputs['Result'], ab.inputs['Roughness'])
ab.inputs['Base Color'].default_value = (0.03, 0.032, 0.035, 1)
concrete = m_noise('concrete', (0.2, 0.2, 0.19), (0.32, 0.31, 0.29), 3.0, 0.85, 0.15)
concD = m_noise('concreteDark', (0.12, 0.12, 0.12), (0.2, 0.2, 0.19), 2.5, 0.9, 0.2)
brick = m_noise('brick', (0.26, 0.09, 0.06), (0.4, 0.15, 0.09), 4.0, 0.88, 0.25)
iron = m_plain('iron', (0.05, 0.05, 0.055), 0.4, 0.8); woodD = m_noise('woodDark', (0.14, 0.08, 0.05), (0.24, 0.15, 0.09), 5, 0.7, 0.05)
siding = m_noise('peelingSiding', (0.22, 0.25, 0.27), (0.38, 0.38, 0.35), 2.0, 0.9, 0.35)
bulbW = m_emis('bulbWarm', (1.0, 0.68, 0.36), 14.0); sodiumM = m_emis('sodium', (1.0, 0.55, 0.2), 18.0)
neonR = m_emis('neonRed', (1.0, 0.12, 0.2), 22.0); neonB = m_emis('neonBlue', (0.25, 0.6, 1.0), 16.0)
fluor = m_emis('fluorGreen', (0.78, 1.0, 0.86), 9.0); paper = m_plain('paper', (0.85, 0.84, 0.78), 0.8)
chairM = m_plain('chairOrange', (0.55, 0.22, 0.06), 0.5); grey = m_plain('greyPlastic', (0.35, 0.36, 0.38), 0.5)
pink = m_plain('pinkSoap', (0.95, 0.42, 0.58), 0.35); pinkE = m_emis('pinkGlow', (1.0, 0.45, 0.65), 2.5, (0.9, 0.4, 0.55))
white = m_plain('planeWhite', (0.82, 0.83, 0.85), 0.35); navy = m_plain('navy', (0.04, 0.07, 0.2), 0.4)
seatM = m_plain('seatBlue', (0.08, 0.14, 0.3), 0.7); dirt = m_noise('yardDirt', (0.09, 0.07, 0.05), (0.17, 0.13, 0.09), 1.2, 0.95, 0.15)
fireM = m_emis('fire', (1.0, 0.4, 0.1), 9.0); fireC = m_emis('fireCore', (1.0, 0.7, 0.35), 14.0); smokeM = m_plain('smoke', (0.05, 0.045, 0.045), 1.0)
cloudM = m_noise('cloud', (0.32, 0.35, 0.42), (0.5, 0.53, 0.6), 0.08, 1.0, 0.0)

# ================================================================== GROUND, STREET, LAMPS ============================
gb_ = span(-160, 220, -160, 420, -0.32, -0.12, dirt, 'groundBase'); hole(gb_, -6.25, 0.25, -8.25, -6.0, -1.0, 1.0)
gnd = span(-70, 120, -40, 30, -0.1, 0.0, asph, 'streetGround')
hole(gnd, -6.25, 0.25, -8.25, -6.0, -1.0, 1.0)                                  # the bar's cellar steps (areaway)
for (y0, y1) in [(-8.0, -6.0), (-18.0, -16.0)]:                                  # sidewalks (curbs)
    for (x0, x1) in [(-70, -6.3), (0.3, 120)] if y0 == -8.0 else [(-70, 120)]:
        span(x0, x1, y0, y1, 0.0, 0.12, concrete, 'sidewalk')
for x in range(-66, 118, 6): box((x, -12.0, 0.004), (2.6, 0.14, 0.01), m_emis('laneLine', (0.85, 0.7, 0.3), 0.15, (0.6, 0.5, 0.25)))
LAMPS = [(x, -7.4) for x in (-30, -16, 24, 38, 66, 80)] + [(x, -16.6) for x in (-44, -6, 30, 62, 90)]
for (x, y) in LAMPS:
    cyl((x, y, 2.9), 0.08, 5.8, iron, v=8); box((x, y + (0.6 if y < -12 else -0.6), 5.85), (0.12, 1.3, 0.1), iron)
    ly = y + (1.2 if y < -12 else -1.2); box((x, ly, 5.75), (0.5, 0.3, 0.14), iron); box((x, ly, 5.66), (0.36, 0.2, 0.03), sodiumM)
    l = point((x, ly, 5.4), 320, (1.0, 0.56, 0.24), 0.25)

# ================================================================== THE BAR + BASEMENT ===============================
bar = span(-7, 7, -6, 6, -4.4, 8.0, brick, 'bar')
hole(bar, -6.6, 6.6, -5.6, 5.6, BZ, -0.25)                                        # the basement room
hole(bar, -1.6, 0.0, -6.5, -5.5, BZ, -1.2)                                        # basement door at the foot of the steps
hole(bar, 7.0 - 0.6, 7.6, -2.6, -1.4, 0.0, 2.3)                                  # side door to the lot
for x in (-4.5, 4.5): box((x, -6.05, 2.0), (2.6, 0.06, 1.8), m_emis('barWindow', (1.0, 0.6, 0.3), 2.2, (0.3, 0.2, 0.1)))
box((-3.3, -6.05, 1.15), (1.2, 0.06, 2.3), m_emis('barDoor', (0.9, 0.5, 0.25), 1.2, (0.2, 0.1, 0.05)))
box((7.05, -2.0, 1.15), (0.06, 1.1, 2.25), m_emis('sideDoorLight', (1.0, 0.62, 0.3), 3.0, (0.3, 0.2, 0.1)))
text('BAR', (1.6, -6.2, 5.4), 1.6, neonR, ext=0.05); text('BAR', (7.2, 0.6, 5.0), 1.3, neonR, rot=(math.pi / 2, 0, math.pi / 2), ext=0.05)
box((1.6, -6.12, 5.4), (4.0, 0.08, 2.0), m_plain('signBack', (0.05, 0.04, 0.05), 0.5))
point((1.6, -7.2, 5.4), 160, (1.0, 0.15, 0.25), 0.8); point((8.0, 0.6, 5.0), 120, (1.0, 0.15, 0.25), 0.8)
for k in range(6): box((-6.25 + k * 0.72 + 0.36, -7.1, -0.33 - k * 0.66), (0.72, 2.1, 0.66 + 0.0), concD)  # cellar steps along x
span(-6.25, 0.25, -8.25, -8.0, -4.4, 0.0, concD, 'areawayWall'); span(-6.45, -6.25, -8.25, -6.0, -4.4, 0.0, concD, 'areawayEnd')
span(0.25, 0.45, -8.25, -6.0, -4.4, 0.0, concD, 'areawayEnd2'); span(-1.75, 0.25, -8.0, -6.0, BZ - 0.2, BZ + 0.012, concD, 'landing')
cyl((-6.2, -8.15, 0.55), 0.03, 1.1, iron, v=6); box((-3.0, -8.15, 1.05), (6.4, 0.05, 0.05), iron)
ball((-0.8, -6.25, -1.6), 0.07, m_emis('cellarBulb', (1.0, 0.7, 0.4), 18), 2); point((-0.8, -6.9, -1.7), 25, (1.0, 0.62, 0.32), 0.1)
# basement interior: pillars, pipes, one bulb over the ring, a red exit glow, crates
bfl = m_noise('basementFloor', (0.22, 0.23, 0.21), (0.34, 0.34, 0.31), 1.6, 0.55, 0.12)
span(-6.6, 6.6, -5.6, 5.6, BZ - 0.1, BZ + 0.012, bfl, 'basementFloor')
bwall = m_noise('basementWall', (0.2, 0.24, 0.21), (0.3, 0.33, 0.28), 2.2, 0.9, 0.2)          # sickly green-grey paint
for (x0, x1, y0, y1) in [(-6.6, -6.5, -5.6, 5.6), (6.5, 6.6, -5.6, 5.6), (-6.6, 6.6, 5.5, 5.6), (-6.6, -1.6, -5.6, -5.5), (0.0, 6.6, -5.6, -5.5)]:
    span(x0, x1, y0, y1, BZ, -0.25, bwall, 'basementLiner')
span(-1.6, 0.0, -5.6, -5.5, -1.2, -0.25, bwall, 'basementLiner')
span(-6.6, 6.6, -5.6, 5.6, -0.35, -0.25, m_plain('basementCeil', (0.1, 0.1, 0.1), 0.9), 'basementCeil')
for (x, y) in [(-3.6, -2.6), (3.6, -2.6), (-3.6, 3.4), (3.6, 3.4)]: box((x, y, BZ / 2), (0.45, 0.45, -BZ), concrete)
for y in (-3.5, 1.0, 4.5): cyl((0, y, -0.5), 0.09, 13.0, iron, (0, math.pi / 2, 0), 10)
cyl((0.0, 0.6, -0.75), 0.006, 0.5, iron, v=6); cone((0.0, 0.6, -1.0), 0.32, 0.22, m_plain('shade', (0.08, 0.1, 0.08), 0.5), 16); ball((0.0, 0.6, -1.1), 0.07, bulbW, 2)
hookbulb = point((0.0, 0.6, -1.25), 380, (1.0, 0.66, 0.36), 0.12)
box((5.5, 5.55, -1.0), (0.8, 0.05, 0.3), m_emis('exitSign', (1.0, 0.1, 0.1), 5)); point((5.5, 5.0, -1.2), 20, (1.0, 0.1, 0.1), 0.3)
for (x, y, s) in [(-5.6, 4.6, 0.8), (-4.8, 4.8, 0.6), (5.4, -4.6, 0.9), (-5.5, -4.5, 0.7)]: box((x, y, BZ + s / 2), (s, s, s), woodD)
for k in range(10): box((-6.55, -5.0 + k * 1.0, -2.4 + 0.3 * math.sin(k)), (0.04, 0.6, 0.9), m_plain('poster%d' % k, [(0.4, 0.1, 0.08), (0.12, 0.1, 0.1), (0.3, 0.28, 0.2)][k % 3], 0.8))
area((0, 0.6, -0.45), 140, (1.0, 0.7, 0.4), 2.0)

# the parking lot + a car + one lamp
span(7.0, 17.5, -6.0, 5.0, 0.0, 0.02, asph, 'lot')
for x in (9.0, 11.6, 14.2, 16.8): box((x, 2.6, 0.03), (0.1, 4.4, 0.01), m_plain('lotLine', (0.6, 0.58, 0.5), 0.6))
car = m_plain('carPaint', (0.28, 0.06, 0.05), 0.25, 0.4)
box((15.4, 2.2, 0.75), (1.9, 4.4, 0.8), car); box((15.4, 2.0, 1.45), (1.7, 2.3, 0.65), m_plain('carGlass', (0.02, 0.03, 0.04), 0.05))
for (dx, dy) in [(-0.95, 0.7), (0.95, 0.7), (-0.95, 3.6), (0.95, 3.6)]: cyl((15.4 + dx, dy, 0.36), 0.36, 0.25, m_plain('tyre', (0.02, 0.02, 0.02), 0.8), (0, math.pi / 2, 0), 16)
box((15.4, -0.02, 0.8), (1.5, 0.05, 0.16), m_emis('tail', (1.0, 0.1, 0.06), 3))
cyl((10.6, -0.8, 3.0), 0.08, 6.0, iron, v=8); box((10.6, -1.5, 5.95), (0.5, 0.3, 0.14), iron); box((10.6, -1.5, 5.86), (0.36, 0.2, 0.03), sodiumM)
point((10.6, -1.6, 5.6), 420, (1.0, 0.55, 0.22), 0.3)

# ================================================================== THE CONDO TOWER + PAYPHONE =======================
condo = span(18, 30, 6, 18, 0.0, 48.0, CITYM[2], 'condo')
hole(condo, 22.6, 25.4, 5.5, 6.6, 27.4, 29.6)
span(22.4, 25.6, 6.6, 9.6, 27.0, 27.412, concD, 'aptFloor'); span(22.4, 25.6, 9.6, 9.9, 27.0, 30.0, concD, 'aptBack')
for x in (22.4, 25.6): span(x - 0.15, x + 0.15, 6.6, 9.9, 27.0, 30.0, concD, 'aptSide')
span(22.4, 25.6, 6.6, 9.9, 29.6, 30.0, concD, 'aptCeil')
cyl((21.2, -7.6, 1.2), 0.07, 2.4, iron, v=8); box((21.2, -7.55, 1.6), (0.55, 0.32, 0.75), m_plain('payphone', (0.55, 0.58, 0.6), 0.3, 0.6))
box((21.2, -7.72, 1.75), (0.3, 0.02, 0.2), m_emis('payScreen', (0.4, 1.0, 0.6), 2)); box((21.2, -7.55, 2.15), (0.6, 0.4, 0.12), m_emis('payTop', (0.85, 0.9, 1.0), 2.5, (0.3, 0.3, 0.3)))
point((21.0, -8.6, 2.4), 60, (0.75, 0.9, 1.0), 0.3)
# the explosion: a fireball out of the window, a light, smoke, glass and debris, then the room keeps burning
f0 = F(b['boom'])
fb = ball(APT, 1.0, fireC, 3); fo = ball(APT, 1.0, fireM, 3)
for (t, s1, s2) in [(0, 0.001, 0.001), (b['boom'] - 0.01, 0.001, 0.001), (b['boom'] + 0.12, 1.4, 2.0), (b['boom'] + 0.45, 2.4, 3.6), (b['boom'] + 1.0, 0.8, 2.2), (b['boom'] + 1.6, 0.001, 0.001)]:
    fb.scale = (s1, s1 * 0.8, s1); fb.keyframe_insert('scale', frame=F(t)); fo.scale = (s2, s2 * 0.8, s2); fo.keyframe_insert('scale', frame=F(t))
for (t, y) in [(b['boom'], 5.8), (b['boom'] + 0.45, 4.2), (b['boom'] + 1.6, 3.6)]:
    fb.location = (APT[0], y, APT[2]); fb.keyframe_insert('location', frame=F(t)); fo.location = (APT[0], y - 0.3, APT[2] + 0.3); fo.keyframe_insert('location', frame=F(t))
boomL = point((APT[0], 3.0, APT[2]), 0, (1.0, 0.5, 0.18), 1.5)
for (t, e) in [(0, 0), (b['boom'] - 0.01, 0), (b['boom'] + 0.06, 9e4), (b['boom'] + 0.5, 4e4), (b['boom'] + 1.6, 1.6e4), (DUR, 1.2e4)]:
    boomL.data.energy = e; boomL.data.keyframe_insert('energy', frame=F(t))
for k in range(26):                                              # debris + glass
    o = box(APT, (random.uniform(0.08, 0.3),) * 3, random.choice([concD, iron, fireM, m_plain('glass', (0.6, 0.75, 0.8), 0.05)]))
    vx, vy, vz = random.uniform(-6, 6), random.uniform(-10, -4), random.uniform(-1, 6)
    for f in range(f0 - 2, f0 + 150, 4):
        u = max(0, (f - f0) / FPS); o.location = (APT[0] + vx * u, APT[1] - 0.2 + vy * u, APT[2] + vz * u - 4.9 * u * u); o.rotation_euler = (u * 7 + k, u * 5, u * 3)
        o.keyframe_insert('location', frame=f); o.keyframe_insert('rotation_euler', frame=f)
    o.hide_render = True; o.keyframe_insert('hide_render', frame=0); o.hide_render = False; o.keyframe_insert('hide_render', frame=f0); o.hide_render = True; o.keyframe_insert('hide_render', frame=f0 + 150)
for k in range(8):                                               # the room burns on: flames in the window + rising smoke
    o = ball((APT[0] - 1.1 + k * 0.32, 7.0 + (k % 2) * 0.5, 27.6), 0.35, fireM, 2, (1, 1, 1.6))
    o.hide_render = True; o.keyframe_insert('hide_render', frame=0); o.hide_render = False; o.keyframe_insert('hide_render', frame=f0 + 20)
for k in range(9):
    o = ball((APT[0] + random.uniform(-1, 1), 5.4, 30.0), 1.0, smokeM, 2)
    for f in range(f0, NF, 30):
        u = (f - f0) / FPS + k * 0.7; o.location = (APT[0] + math.sin(u + k) * 0.8, 5.0 - 0.15 * u, 30.0 + (u % 6.3) * 2.2); o.scale = (0.6 + (u % 6.3) * 0.45,) * 3
        o.keyframe_insert('location', frame=f); o.keyframe_insert('scale', frame=f)
    o.hide_render = True; o.keyframe_insert('hide_render', frame=0); o.hide_render = False; o.keyframe_insert('hide_render', frame=f0 + 10)
fireL = point((APT[0], 7.4, 28.2), 0, (1.0, 0.5, 0.18), 0.6)
for f in range(0, NF, 6):
    t = f / FPS; fireL.data.energy = 0 if t < b['boom'] else 1800 + 700 * math.sin(t * 17) * math.sin(t * 5.3); fireL.data.keyframe_insert('energy', frame=f)

# ================================================================== THE OFFICE TOWER ==================================
ofc = span(-26, -10, -34, -20, 0.0, 40.0, CITYM[0], 'office')
hole(ofc, -25.4, -10.6, -33.4, -20.6, OFZ, OFZ + 3.6)                             # the 3rd floor interior
hole(ofc, -25.0, -11.0, -20.8, -19.4, OFZ + 0.6, OFZ + 3.2)                        # window band (no glass)
for x in range(-25, -10, 2): box((x + 0.0, -20.05, OFZ + 1.9), (0.12, 0.3, 2.6), concrete)
for x in (-23.0, -18.5, -14.0):                                                     # fluorescent strips, green-white
    box((x, -27.0, OFZ + 3.52), (0.3, 6.0, 0.06), fluor)
    area((x, -27.0, OFZ + 3.45), 220, (0.8, 1.0, 0.86), 1.2, (0, 0, 0)).data.shape = 'RECTANGLE'
for (x, y) in [(-22.6, -27.4), (-14.4, -27.4), (-22.6, -31.2), (-18.5, -31.2), (-14.4, -31.2), (-22.6, -23.8), (-14.4, -23.8)]:   # cubicles
    box((x, y - 0.9, OFZ + 0.65), (2.6, 0.06, 1.3), m_plain('cubicle', (0.35, 0.37, 0.4), 0.9)); box((x - 1.3, y, OFZ + 0.65), (0.06, 1.8, 1.3), m_plain('cubicle', (0.35, 0.37, 0.4), 0.9))
    box((x, y - 0.35, OFZ + 0.74), (2.4, 0.7, 0.05), grey); box((x, y - 0.25, OFZ + 1.0), (0.45, 0.06, 0.34), m_emis('screenOff', (0.1, 0.2, 0.25), 0.6, (0.02, 0.02, 0.03)))
box((-18.5, -28.5, OFZ + 0.74), (2.2, 0.8, 0.05), grey); box((-18.5, -28.5, OFZ + 0.36), (2.1, 0.7, 0.72), m_plain('deskBody', (0.2, 0.2, 0.22), 0.7))   # desk behind him
box((-17.6, -28.6, OFZ + 1.02), (0.5, 0.05, 0.36), m_emis('monitor', (0.55, 0.9, 1.0), 2.6, (0.05, 0.08, 0.1)))
point((-17.9, -27.9, OFZ + 1.25), 18, (0.6, 0.9, 1.0), 0.2)
for k in range(5): box((-19.3 + k * 0.08, -28.4, OFZ + 0.78 + k * 0.02), (0.32, 0.42, 0.02), paper)
box((-18.5, -27.7, OFZ + 0.45), (0.5, 0.5, 0.07), m_plain('officeChair', (0.06, 0.06, 0.07), 0.6)); cyl((-18.5, -27.7, OFZ + 0.22), 0.04, 0.44, iron, v=8)
for (x0, x1, y0, y1, z0, z1) in [(-25.4, -25.3, -33.4, -20.6, OFZ, OFZ + 3.6), (-10.7, -10.6, -33.4, -20.6, OFZ, OFZ + 3.6), (-25.4, -10.6, -33.4, -33.3, OFZ, OFZ + 3.6), (-25.4, -10.6, -33.4, -20.6, OFZ + 3.5, OFZ + 3.6)]:
    span(x0, x1, y0, y1, z0, z1, m_plain('officeWall', (0.3, 0.33, 0.31), 0.85), 'liner')
box((-18.5, -33.35, OFZ + 2.6), (1.4, 0.06, 0.6), m_plain('clockBack', (0.02, 0.02, 0.02), 0.4))
text('3:00', (-18.5, -33.3, OFZ + 2.6), 0.45, m_emis('clockRed', (1.0, 0.12, 0.08), 12), rot=(math.pi / 2, 0, math.pi), ext=0.005)
span(-25.4, -10.6, -33.4, -20.6, OFZ - 0.2, OFZ + 0.012, m_plain('officeCarpet', (0.2, 0.22, 0.24), 0.9), 'officeFloor')

# ================================================================== THE CHURCH HALL (support group) ==================
hall = span(-44, -30, -34, -20, 0.0, 7.0, m_noise('hallStone', (0.3, 0.26, 0.22), (0.42, 0.37, 0.3), 2.5, 0.9, 0.2), 'hall')
hole(hall, -43.4, -30.6, -33.4, -20.6, 0.0, 4.6)
hole(hall, -40.0, -34.0, -20.8, -19.4, 0.8, 3.8)                                  # the big front window
hole(hall, -44.6, -43.0, -29.6, -28.0, 0.0, 2.5)                                  # side door (Marla)
cone((-37.0, -27.0, 8.6), 9.6, 3.2, m_plain('hallRoof', (0.12, 0.1, 0.1), 0.8), 4, (0, 0, math.pi / 4)).scale = (6.8, 9.8, 3.2)
cyl((-31.5, -21.0, 10.0), 0.6, 6.0, m_noise('hallStone', (0.3, 0.26, 0.22), (0.42, 0.37, 0.3), 2.5, 0.9, 0.2), v=4)   # a small bell tower
cone((-31.5, -21.0, 14.2), 1.0, 2.4, m_plain('hallRoof', (0.12, 0.1, 0.1), 0.8), 4)
span(-43.4, -30.6, -33.4, -20.6, 0.0, 0.04, m_plain('hallFloor', (0.3, 0.2, 0.12), 0.45), 'hallFloor')
for k in range(10):                                                              # the circle of chairs
    if k == 5: continue
    a = k / 10 * 2 * math.pi; x, y = -37.0 + 2.3 * math.sin(a), -28.0 - 1.7 * math.cos(a)
    box((x, y, 0.45), (0.46, 0.46, 0.05), chairM); box((x + 0.21 * math.sin(a), y - 0.21 * math.cos(a), 0.72), (0.44, 0.05, 0.5), chairM)
    for (dx, dy) in [(-0.2, -0.2), (0.2, -0.2), (-0.2, 0.2), (0.2, 0.2)]: box((x + dx, y + dy, 0.22), (0.03, 0.03, 0.44), iron)
box((-37.0, -33.35, 3.2), (5.0, 0.05, 0.9), m_plain('banner', (0.86, 0.8, 0.62), 0.8))
text('SUPPORT GROUP TONIGHT', (-37.0, -33.3, 3.2), 0.36, m_plain('bannerInk', (0.3, 0.12, 0.08), 0.6), rot=(math.pi / 2, 0, math.pi), ext=0.005)
box((-32.0, -32.6, 0.45), (1.6, 0.6, 0.9), woodD); cyl((-32.2, -32.6, 1.1), 0.18, 0.45, m_plain('urn', (0.7, 0.7, 0.72), 0.25, 0.9), v=16)
for x in (-40.0, -34.0): ball((x, -27.0, 4.35), 0.12, bulbW, 2); point((x, -27.0, 4.1), 330, (1.0, 0.7, 0.42), 0.4)
point((-37.0, -24.0, 3.4), 160, (1.0, 0.8, 0.55), 1.0)
for x in (-41.5, -32.5): box((x, -20.05, 2.3), (1.6, 0.06, 2.8), m_emis('stained', (0.9, 0.5, 0.25), 1.4, (0.3, 0.15, 0.1)))

# ================================================================== THE PLANE (cut-away cabin) =========================
PX, PY = -20.0, 20.6
bpy.ops.mesh.primitive_cylinder_add(radius=2.3, depth=34, vertices=40, location=(PX, PY, PLZ + 1.6), rotation=(0, math.pi / 2, 0)); fus = bpy.context.object
fus.data.materials.append(white); bpy.ops.object.shade_smooth()
mdS = fus.modifiers.new('solid', 'SOLIDIFY'); mdS.thickness = 0.12; bpy.context.view_layer.objects.active = fus; bpy.ops.object.modifier_apply(modifier='solid')
hole(fus, PX - 4.2, PX + 4.2, PY - 3.0, PY - 0.9, PLZ - 0.5, PLZ + 3.4)            # the cut-away
box((PX, PY - 2.26, PLZ + 0.9), (33.0, 0.06, 0.25), navy).location = (PX + 8.6, PY - 2.25, PLZ + 0.9)
ball((PX + 17.0, PY, PLZ + 1.6), 2.3, white, 3, (1.4, 1, 1)); ball((PX - 17.0, PY, PLZ + 1.8), 2.3, white, 3, (2.2, 1, 0.8))
box((PX - 18.5, PY, PLZ + 5.0), (3.0, 0.25, 4.6), white); box((PX - 18.5, PY, PLZ + 1.9), (2.6, 9.0, 0.2), white)
box((PX + 1.5, PY + 9.0, PLZ + 0.5), (5.0, 14.0, 0.35), white); box((PX + 1.5, PY - 9.0, PLZ + 0.5), (5.0, 14.0, 0.35), white)
for sy in (-1, 1): cyl((PX + 2.0, PY + sy * 6.0, PLZ - 0.3), 0.9, 3.6, m_plain('engine', (0.6, 0.62, 0.65), 0.3, 0.6), (0, math.pi / 2, 0), 24)
span(PX - 16.5, PX + 16.5, PY - 1.9, PY + 1.9, PLZ - 0.25, PLZ, m_plain('cabinFloor', (0.12, 0.13, 0.18), 0.8), 'cabinFloor')
for k in range(-6, 7):                                                            # seats in pairs + windows
    x = PX + k * 1.0
    for sy in (0.0, 0.62): box((x, PY + 0.4 + sy, PLZ + 0.45), (0.55, 0.5, 0.12), seatM); box((x + 0.27, PY + 0.4 + sy, PLZ + 0.85), (0.1, 0.5, 0.8), seatM)
    ball((x, PY + 2.12, PLZ + 1.6), 0.16, m_emis('planeWin', (0.25, 0.4, 0.75), 2.0), 2, (1.0, 0.3, 1.4))
box((PX, PY + 1.3, PLZ + 2.75), (16.0, 1.0, 0.4), m_plain('bins', (0.75, 0.76, 0.78), 0.5))
for k in range(-6, 7, 2): box((PX + k, PY + 0.9, PLZ + 2.53), (0.3, 0.15, 0.03), m_emis('readLight', (1.0, 0.85, 0.6), 6))
area((PX, PY + 0.4, PLZ + 2.4), 100, (1.0, 0.86, 0.66), 3.0)
point((PX - 0.6, PY - 1.2, PLZ + 1.7), 60, (1.0, 0.8, 0.55), 0.8)
for sy in (-1, 1): ball((PX + 2.0 + 0.0, PY + sy * 13.0, PLZ + 0.5), 0.12, m_emis('navLight', (1.0, 0.1, 0.1) if sy < 0 else (0.1, 1.0, 0.2), 30), 2)
# clouds below the plane, drifting past while we sit in the cabin
bpy.ops.object.empty_add(location=(0, 0, 0)); cloudRig = bpy.context.object
for k in range(70):
    x, y, z = random.uniform(-160, 120), random.uniform(-60, 120), random.uniform(62, 98)
    if abs(x - PX) < 14 and abs(y - PY) < 12 and z > 92: continue
    o = ball((x, y, z), random.uniform(5, 13), cloudM, 2, (1.6, 1.2, 0.55)); o.parent = cloudRig
for (t, x) in [(0, 0.0), (b['ruins'] + 1.6, 0.0), (b['then'] - 0.4, -110.0)]: cloudRig.location = (x, 0, 0); cloudRig.keyframe_insert('location', frame=F(t))

# ================================================================== THE CRUMBLING HOUSE ===============================
hs = span(52, 60, -4, 4, KZ - 0.4, 6.4, siding, 'house')
hole(hs, 52.3, 59.7, -3.7, 3.7, KZ, 3.3); hole(hs, 52.3, 59.7, -3.7, 3.7, 3.5, 6.2)
hole(hs, 54.1, 56.5, -4.5, -3.5, KZ + 0.9, KZ + 2.3)                                # the kitchen window
for x in (52.9, 57.6): hole(hs, x, x + 1.3, -4.5, -3.5, 4.2, 5.5)                  # upstairs windows (dark, broken)
span(52.3, 59.7, -3.7, 3.7, 3.3, 3.5, woodD, 'houseMidFloor')
bpy.ops.mesh.primitive_cone_add(radius1=6.2, depth=3.0, vertices=4, location=(56, 0, 7.9), rotation=(0, 0, math.pi / 4)); rf = bpy.context.object; rf.scale = (1.0, 0.75, 1.0)
rf.data.materials.append(m_plain('roofShingle', (0.08, 0.07, 0.07), 0.9))
span(51.2, 60.8, -6.4, -4.0, KZ - 0.4, KZ - 0.15, woodD, 'porch'); box((56.0, -6.2, 3.2), (9.6, 2.6, 0.12), woodD).location = (56.0, -5.2, 3.2)
for x in (51.5, 54.0, 58.0, 60.5): box((x, -6.2, 1.6), (0.14, 0.14, 2.9), woodD)
for k in range(9): box((51.6 + k * 1.1, -4.04, 2.0 + 0.6 * math.sin(k * 2.1)), (0.6, 0.02, 0.35), m_plain('peel%d' % (k % 3), [(0.52, 0.5, 0.42), (0.18, 0.2, 0.2), (0.4, 0.36, 0.3)][k % 3], 0.95))
for x in (53.55, 58.25): box((x, -4.02, 4.85), (1.25, 0.03, 1.25), m_plain('boardUp', (0.24, 0.17, 0.1), 0.9)); box((x, -4.05, 4.85), (1.4, 0.04, 0.12), woodD)
span(52.3, 59.7, -3.7, 3.7, KZ - 0.05, KZ + 0.012, m_plain('linoleum', (0.3, 0.33, 0.26), 0.55), 'kitchenFloor')
box((56.9, 3.2, KZ + 0.45), (1.2, 0.7, 0.9), m_plain('stove', (0.55, 0.54, 0.5), 0.4, 0.3))
cyl((56.9, 3.15, KZ + 1.15), 0.42, 0.5, iron, v=24); cyl((56.9, 3.15, KZ + 1.38), 0.38, 0.04, pinkE, v=24)
point((56.9, 3.0, KZ + 1.6), 40, (1.0, 0.45, 0.65), 0.3)
for k in range(3):                                                                # steam
    o = ball((56.9, 3.1, KZ + 1.8), 0.25, m_plain('steam', (0.6, 0.6, 0.62), 1.0), 2)
    for f in range(0, NF, 20):
        u = (f / FPS + k * 0.6) % 1.8; o.location = (56.9 + 0.1 * math.sin(u * 3 + k), 3.1, KZ + 1.6 + u * 0.6); o.scale = (0.15 + u * 0.12,) * 3; o.keyframe_insert('location', frame=f); o.keyframe_insert('scale', frame=f)
box((53.2, 3.0, KZ + 0.42), (1.4, 1.2, 0.84), woodD)                              # table with stacks of soap (to the side)
for k in range(18): box((52.8 + (k % 3) * 0.3, 2.55 + ((k // 3) % 3) * 0.36, KZ + 0.9 + (k // 9) * 0.13), (0.26, 0.36, 0.12), pink)
for k in range(12): box((59.45, -2.0 + k * 0.34, KZ + 1.4 + (k % 3) * 0.3), (0.3, 0.26, 0.12), pink)   # shelf of soap
box((59.5, -0.2, KZ + 1.3), (0.4, 4.4, 0.04), woodD); box((59.5, -0.2, KZ + 1.95), (0.4, 4.4, 0.04), woodD)
cyl((55.3, 1.0, 3.0), 0.006, 0.5, iron, v=6); ball((55.3, 1.0, 2.7), 0.07, bulbW, 2); point((55.3, 0.9, 2.55), 220, (1.0, 0.66, 0.36), 0.12)
span(46, 66, -6.4, -4.0, 0.0, 0.02, dirt, 'yard')
ball((56.0, -4.3, 3.0), 0.09, bulbW, 2); point((56.0, -5.0, 2.9), 260, (1.0, 0.66, 0.36), 0.2)        # porch light
point((56.0, -12.0, 6.5), 900, (0.55, 0.65, 1.0), 2.5)                                                  # cold fill over the army
point((71.0, -13.0, 5.5), 1400, (1.0, 0.6, 0.3), 1.5); point((74.5, -7.5, 4.0), 700, (0.6, 0.7, 1.0), 1.5)                                                    # a street light at the police stop
for k in range(8): cyl((random.uniform(46, 66), random.uniform(-6.2, -4.5), 0.4), 0.02, random.uniform(0.4, 0.9), m_plain('weed', (0.15, 0.2, 0.08), 0.9), (random.uniform(-0.3, 0.3), 0, 0), 4)

# police car (Bob's last mission)
pcB = m_plain('policeBlack', (0.03, 0.03, 0.035), 0.25, 0.4); pcW = m_plain('policeWhite', (0.8, 0.8, 0.82), 0.3)
box((77.2, -12.0, 0.7), (4.6, 1.9, 0.75), pcB); box((77.2, -12.0, 0.7), (1.8, 1.92, 0.5), pcW); box((77.4, -12.0, 1.38), (2.4, 1.7, 0.6), m_plain('carGlass', (0.02, 0.03, 0.04), 0.05))
for (dx, dy) in [(-1.5, -0.95), (1.5, -0.95), (-1.5, 0.95), (1.5, 0.95)]: cyl((77.2 + dx, -12.0 + dy, 0.36), 0.36, 0.25, m_plain('tyre', (0.02, 0.02, 0.02), 0.8), (math.pi / 2, 0, 0), 16)
redM = m_emis('sirenRed', (1.0, 0.05, 0.05), 0.0); bluM = m_emis('sirenBlue', (0.1, 0.3, 1.0), 0.0)
box((77.0, -12.3, 1.75), (0.4, 0.5, 0.16), redM); box((77.0, -11.7, 1.75), (0.4, 0.5, 0.16), bluM)
sR = point((77.0, -13.2, 2.2), 0, (1.0, 0.05, 0.05), 0.4); sB = point((77.0, -10.8, 2.2), 0, (0.1, 0.3, 1.0), 0.4)
for f in range(0, NF, 3):
    t = f / FPS; on = b['then2'] + 1.6 <= t < b['shut'] + 0.5; ph = int(t * 6) % 2
    redM.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 30.0 if on and ph else 0.0; redM.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
    bluM.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 30.0 if on and not ph else 0.0; bluM.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
    sR.data.energy = 900 if on and ph else 0; sR.data.keyframe_insert('energy', frame=f); sB.data.energy = 1100 if on and not ph else 0; sB.data.keyframe_insert('energy', frame=f)
muzzle = point((74.9, -10.5, 1.4), 0, (1.0, 0.8, 0.4), 0.05)
for (t, e) in [(0, 0), (b['shotB'] - 0.01, 0), (b['shotB'], 3000), (b['shotB'] + 0.06, 0)]: muzzle.data.energy = e; muzzle.data.keyframe_insert('energy', frame=F(t))

# ================================================================== THE HIGH-RISE (top floor) =========================
hr = span(78, 96, -4, 14, 0.0, 63.0, CITYM[4], 'highrise')
hole(hr, 78.4, 95.6, -3.6, 13.6, TZ, 61.8)
hole(hr, 79.0, 95.0, -4.5, -3.4, TZ + 0.4, 61.6)                                   # south band: the camera comes in here
hole(hr, 79.0, 95.0, 13.4, 14.5, TZ + 0.1, 61.75)                                  # north windows: the view of the skyline
for x in range(79, 96, 2):
    if abs(x - 86.4) > 1.2: box((x, 14.0, (TZ + 61.75) / 2), (0.14, 0.4, 61.75 - TZ), concrete)
    box((x, -4.0, (TZ + 61.6) / 2), (0.14, 0.4, 61.6 - TZ), concrete)
span(78.4, 95.6, -3.6, 13.6, TZ - 0.05, TZ + 0.012, m_plain('carpet', (0.16, 0.17, 0.2), 0.9), 'topCarpet')
for (x0, x1, y0, y1, z0, z1) in [(78.4, 78.5, -3.6, 13.6, TZ, 61.8), (95.5, 95.6, -3.6, 13.6, TZ, 61.8), (78.4, 95.6, -3.6, 13.6, 61.7, 61.8)]:
    span(x0, x1, y0, y1, z0, z1, m_plain('topWall', (0.16, 0.17, 0.19), 0.85), 'liner')
for (x, y) in [(81.0, 0.5), (91.5, 0.5), (81.0, 6.0), (91.5, 6.0)]: box((x, y, TZ + 0.37), (1.6, 0.8, 0.05), grey); box((x, y, TZ + 0.18), (1.5, 0.7, 0.36), m_plain('deskBody', (0.2, 0.2, 0.22), 0.7))
for x in (82.5, 90.0): box((x, 4.0, (TZ + 61.8) / 2), (0.5, 0.5, 61.8 - TZ), concrete)
area((86.5, 12.8, 61.4), 120, (0.55, 0.7, 1.0), 6.0, (math.radians(-60), 0, 0))     # cold window light
area((86.5, 4.0, 61.6), 110, (0.6, 0.72, 0.9), 8.0)
flashL = point((85.3, 8.6, TZ + 1.3), 0, (1.0, 0.85, 0.6), 0.05)
for (t, e) in [(0, 0), (b['bang'] - 0.01, 0), (b['bang'], 9000), (b['bang'] + 0.08, 0)]: flashL.data.energy = e; flashL.data.keyframe_insert('energy', frame=F(t))
boomGlow = area((86.5, 30.0, 70.0), 0, (1.0, 0.5, 0.2), 30.0, (math.radians(100), 0, math.radians(180)))

# ================================================================== THE CITY + THE CREDIT-CARD TOWERS =================
KEEP = [(-8, 8, -7, 7), (6, 32, -7, 20), (-27, -9, -35, -19), (-45, -29, -35, -19), (44, 68, -8, 6), (76, 98, -6, 16), (-75, 125, -19, -5), (68, 82, -14, -6)]
def free(x0, x1, y0, y1): return not any(x0 < a1 and x1 > a0 and y0 < b1 and y1 > b0 for (a0, a1, b0, b1) in KEEP)
blocks = 0
for gx in range(-110, 170, 13):
    for gy in list(range(-80, -20, 13)) + list(range(10, 240, 13)):
        wx, wy = random.uniform(7, 11), random.uniform(7, 11); x0, y0 = gx + random.uniform(0, 2), gy + random.uniform(0, 2)
        if not free(x0 - 1, x0 + wx + 1, y0 - 1, y0 + wy + 1): continue
        near = abs(gy) < 60 and -60 < gx < 120
        h = random.uniform(8, 26) if near else random.uniform(12, 46)
        if gy > 14 and -40 < gx < 165: h = min(h, 30)                                # keep the view from the top floor open
        span(x0, x0 + wx, y0, y0 + wy, 0.0, h, random.choice(CITYM), 'blk'); blocks += 1
        if random.random() < 0.25: box((x0 + wx / 2, y0 + wy / 2, h + 1.2), (0.6, 0.6, 2.4), iron)
print('city blocks', blocks, flush=True)
TOWERS = [(45.0, 250.0, 112.0, 16.0), (72.0, 280.0, 150.0, 20.0), (100.0, 245.0, 128.0, 17.0), (128.0, 275.0, 96.0, 15.0), (20.0, 290.0, 88.0, 14.0)]
TOW = []
for k, (x, y, h, s) in enumerate(TOWERS):
    tm = m_city('tower%d' % k, (0.08, 0.09, 0.11), lit=0.55, strength=4.0, cell=(2.6, 3.2), warm=(0.85, 0.92, 1.0), cool=(1.0, 0.75, 0.45))
    o = span(x - s / 2, x + s / 2, y - s / 2, y + s / 2, 0.0, h, tm, 'cctower%d' % k)
    cr = box((x, y, h + 2.0), (s * 0.8, s * 0.8, 4.0), m_emis('crown%d' % k, [(1.0, 0.3, 0.2), (0.3, 0.7, 1.0), (1.0, 0.8, 0.3), (0.5, 1.0, 0.6), (1.0, 0.4, 0.8)][k], 6.0))
    sp_ = cyl((x, y, h + 10.0), 0.3, 12.0, iron, v=6); bl = ball((x, y, h + 16.2), 0.8, m_emis('beacon%d' % k, (1.0, 0.1, 0.1), 40), 2)
    TOW.append((o, [cr, sp_, bl], x, y, h, s))
# charges: orange flashes on each tower (bottom floors and mid floors), then the fall with dust
BOMBS = [b['bomb0'] + k * 0.32 for k in range(len(TOWERS))]
dustM = m_plain('dust', (0.3, 0.27, 0.24), 1.0)
for k, (o, parts, x, y, h, s) in enumerate(TOW):
    t0 = BOMBS[k]; tf0 = b['crash'] + [0.0, 0.5, 0.25, 0.8, 1.1][k]; tf1 = tf0 + 2.6
    for j, zz in enumerate([4.0, h * 0.35, h * 0.6]):
        fbk = ball((x, y - s / 2 - 0.5, zz), 1.0, fireM, 2)
        tt = t0 + j * 0.09
        for (t, sc_) in [(0, 0.001), (tt - 0.01, 0.001), (tt + 0.1, s * 0.55), (tt + 0.6, s * 0.35), (tt + 1.4, 0.001)]: fbk.scale = (sc_,) * 3; fbk.keyframe_insert('scale', frame=F(t))
    for ob in [o] + parts:
        z0 = ob.location.z
        for (t, dz) in [(0, 0.0), (tf0, 0.0), (tf0 + 0.6, -h * 0.12), (tf1, -h * 1.05)]: ob.location.z = z0 + dz; ob.keyframe_insert('location', frame=F(t))
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'QUAD'; kp.easing = 'EASE_IN'
    for j in range(7):
        d = ball((x + random.uniform(-s, s) * 0.6, y - s * 0.4 + random.uniform(-s, s) * 0.5, 6.0), 1.0, dustM, 2, (1.3, 1.3, 0.8))
        for (t, r_, zz) in [(0, 0.001, 4.0), (tf0 + 0.2, 0.001, 4.0), (tf0 + 1.2, s * 0.7, 10.0 + j * 3), (tf1 + 1.5, s * 1.4, 22.0 + j * 5), (DUR, s * 1.7, 30.0 + j * 6)]:
            d.scale = (r_, r_, r_ * 0.7); d.keyframe_insert('scale', frame=F(t)); d.location.z = zz; d.keyframe_insert('location', frame=F(t))
for (t, e) in [(0, 0), (b['bomb0'] - 0.01, 0), (b['bomb0'] + 0.1, 9000), (b['bomb0'] + 1.8, 4000), (b['crash'] + 1.0, 6000), (DUR, 2500)]:
    boomGlow.data.energy = e; boomGlow.data.keyframe_insert('energy', frame=F(t))

# ------------------------------------------------------------------ interpolation tidy-up ---------------------------
for ob in bpy.data.objects:
    ad_ = ob.animation_data
    if ad_ and ad_.action:
        for fc in ad_.action.fcurves:
            if fc.data_path == 'hide_render':
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for owner in [o.data for o in bpy.data.objects if o.type == 'LIGHT'] + [redM.node_tree, bluM.node_tree]:
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
