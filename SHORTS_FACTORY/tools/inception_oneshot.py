"""MOVIES IN A MINUTE: INCEPTION. One continuous camera move, no cuts, in a bright cel-shaded cartoon style: flat
candy colours in two or three shading bands (no textures), soft contact shading, black ink outlines (Freestyle) and a
different colour scheme per dream level. The dream levels are stacked UNDER the top world, each with its own sky:
  top    a pastel dream street (the far end folds up into the sky), a vault room full of glowing ideas, a rooftop with a
         helicopter, a plum office tower that splits in two, a workshop (maze plans, flasks)
  L1     a rain-blue city street with a yellow van and a pursuer
  L2     a warm hotel corridor with things floating
  L3     a mint-and-white snowy mountain with a fortress (courtyard + a vault room)
  limbo  a sunset sea with crumbling towers, a little beach house, a tall roof, a seaside hall
  then up through every level to a plane above the clouds, and down to a house with a kitchen table (the top).
All set and character designs are original. Characters are 2D (engine); this script exports their 3D tracks in
camera.json. Every time comes from a cue word.
Run: $BLENDER -b --factory-startup -P tools/inception_oneshot.py -- <out> --words <words.json> [--scale 0.5]
     [--spp 6] [--list a,b,c] [--start A --end B] [--tracks-only]"""
import bpy, math, sys, os, json, random, re, importlib.util
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0]; arg = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
SCALE, SPP = arg('--scale', 0.5), arg('--spp', 6)
WORDS = json.load(open(arg('--words', '')))
FPS = 60; DUR = WORDS['duration'] + 1.2; NF = int(round(DUR * FPS))
START, END = arg('--start', 0), arg('--end', NF - 1)
HERE = os.path.dirname(os.path.abspath(__file__))
s_ = importlib.util.spec_from_file_location('presets_fn2', os.path.join(HERE, 'presets_fn2.py')); F2 = importlib.util.module_from_spec(s_); s_.loader.exec_module(F2)
ISL = F2.ISL; box, cyl, cone, ball = ISL.box, ISL.cyl, ISL.cone, ISL.ball
os.makedirs(OUT, exist_ok=True); random.seed(7)

# ------------------------------------------------------------------ beats from the voice ---------------------------
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
CUES = [('dreams', 'dreams'), ('steal', 'steal'), ('secrets', 'secrets'), ('time', 'time'), ('leave', 'leave'), ('behind', 'behind'),
        ('dom', 'dom'), ('cobb1', 'cobb'), ('ideas', 'ideas'), ('minds', 'minds'), ('dream', 'dream'), ('client', 'client'), ('saito1', 'saito'),
        ('home1', 'home'), ('kids', 'kids'), ('plants', 'plants'), ('robert', 'robert'), ('fischer1', 'fischer'), ('break', 'break'),
        ('dying1', 'dying'), ('company', 'company'), ('team', 'team'), ('architect', 'architect'), ('ariadne1', 'ariadne'), ('forger', 'forger'),
        ('chemist', 'chemist'), ('three', 'three'), ('deep', 'deep'), ('van', 'van'), ('hotel', 'hotel'), ('snowy', 'snowy'), ('fortress', 'fortress'),
        ('sedative', 'sedative'), ('dying2', 'dying'), ('limbo1', 'limbo'), ('dead', 'dead'), ('wife', 'wife'), ('mal1', 'mal'),
        ('planted1', 'planted'), ('world', 'world'), ('real', 'real'), ('killed', 'killed'), ('mal2', 'mal'), ('shoots', 'shoots'),
        ('fischer2', 'fischer'), ('ariadne2', 'ariadne'), ('dive', 'dive'), ('limbo2', 'limbo'), ('back', 'back'), ('father', 'father'),
        ('live', 'live'), ('life', 'life'), ('idea', 'idea'), ('planted2', 'planted'), ('saito2', 'saito'), ('dies', 'dies'), ('finds', 'finds'),
        ('limbo3', 'limbo'), ('old', 'old'), ('wake', 'wake'), ('plane', 'plane'), ('saito3', 'saito'), ('call', 'call'), ('home2', 'home'),
        ('spins', 'spins'), ('top', 'top'), ('wait', 'wait'), ('falls', 'falls'), ('fall', 'fall')]
B = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while j < len(ws) and norm(ws[j]['word']) != cue: j += 1
    if j == len(ws): raise SystemExit('cue word not found: ' + cue)
    B[key] = ws[j]['start']; wi = j + 1
B['end'] = DUR
B['fold'] = B['dreams'] - 0.1          # the far street starts folding up into the sky
B['drop1'] = B['three'] + 0.1          # down through the workshop floor into level 1
B['bang'] = B['shoots'] + 0.12         # Mal fires
B['kick'] = B['back'] - 0.05           # Fischer is pushed off the limbo roof
B['up'] = B['wake'] - 0.25             # the big kick: up through every level to the plane
b = B
print('beats', json.dumps({k: round(v, 2) for k, v in B.items()}), flush=True)


def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def clamp(u, a=0.0, c=1.0): return min(c, max(a, u))
def lerp3(a, c, u): return tuple(x + (y - x) * u for x, y in zip(a, c))
def walk(t, t0, t1, p0, p1): return lerp3(p0, p1, clamp((t - t0) / (t1 - t0)))
def seg(t, table):
    for t0, t1, fn in table:
        if t0 <= t < t1: return fn(t), 1
    return (0, 0, -900), 0
C_ = lambda p: (lambda t: p)

# ------------------------------------------------------------------ layout (metres) ---------------------------------
# Top world on z = 0, street along x (road y -16..-8), sets on the north side facing south. Dream levels below.
ROOFZ = 26.0                  # Saito's rooftop
TZ = 20.0                     # the terrace on Fischer's tower
ZL1 = -40.0                   # level 1 street
ZL2 = -70.0                   # level 2 hotel corridor floor
ZL3 = -130.0                  # level 3 snow
ZLB = -200.0                  # limbo sea level
LROOF = ZLB + 28.0            # the tall limbo roof
CASZ = ZLB + 1.2              # the seaside hall floor
PLZ = 39.0                    # plane cabin floor
SKY1, SKY2, SKY3, SKYB = (-1.0, -12.0), (-41.0, -44.0), (-80.0, -84.0), (-150.0, -154.0)   # (slab top, slab bottom) above each band

HOOK = (0.0, b['dom'] - 0.25)
SAFE = (b['dom'] - 0.25, b['client'] - 0.15)
ROOF = (b['client'] - 0.15, b['robert'] - 0.45)
TERR = (b['robert'] - 0.45, b['team'] - 0.3)
WORK = (b['team'] - 0.3, b['drop1'] + 0.35)
HOTEL = (b['hotel'] - 0.2, b['snowy'] + 0.1)
HOUSE = (b['dead'] - 0.75, b['mal2'] - 0.15)
COURT = (b['mal2'] - 0.25, b['ariadne2'] - 0.2)
LROOFT = (b['ariadne2'] - 0.3, b['father'] - 0.35)
VAULT = (b['father'] - 0.45, b['saito2'] - 0.2)
CASTLE = (b['saito2'] - 0.3, b['up'] + 0.1)
PLANE = (b['up'] + 0.3, b['home2'] - 0.25)
HOME = (b['home2'] - 0.45, DUR + 1)
def fischer_fall(t):          # pushed off the limbo roof: he drops past the edge
    if t < b['kick']: return (124.4, 7.0, LROOF)
    u = t - b['kick']; return (124.4 + min(u, 0.5) * 2.2, 7.0 - min(u, 0.5) * 1.6, LROOF - 9.0 * u * u)
def cobb_home(t): return walk(t, b['wait'] - 0.1, b['falls'] + 0.9, (176.9, 0.6, 0.0), (179.6, 8.6, 0.0))
TRACKS = {
    'cobb': lambda t: seg(t, [(*HOOK, lambda t: walk(t, 0.0, HOOK[1], (-3.6, -11.6, 0.0), (1.2, -11.7, 0.0))), (*SAFE, C_((17.9, 1.4, 0.0))),
                              (*ROOF, C_((35.4, -1.4, ROOFZ))), (*WORK, C_((68.6, 0.6, 0.0))), (*HOUSE, C_((96.8, -4.3, ZLB))),
                              (*LROOFT, C_((121.0, 6.2, LROOF))), (*CASTLE, C_((146.9, 1.2, CASZ))), (*PLANE, C_((151.0, 0.85, PLZ))),
                              (*HOME, cobb_home)]),
    'saito': lambda t: seg(t, [(*ROOF, C_((32.2, -1.2, ROOFZ))), (*CASTLE, C_((150.4, 3.0, CASZ))), (*PLANE, C_((155.0, -0.85, PLZ)))]),
    'fischer': lambda t: seg(t, [(*TERR, C_((51.0, -2.6, TZ))), (*COURT, C_((107.2, 6.4, ZL3))), (*LROOFT, fischer_fall), (*VAULT, C_((109.4, 18.6, ZL3)))]),
    'mal': lambda t: seg(t, [(HOUSE[0], b['killed'] + 0.55, C_((100.2, -3.5, ZLB))), (*COURT, C_((103.0, 5.6, ZL3)))]),
    'ariadne': lambda t: seg(t, [(*WORK, C_((70.8, 1.0, 0.0))), (*LROOFT, C_((118.8, 6.0, LROOF)))]),
    'eames': lambda t: seg(t, [(*WORK, C_((73.0, 1.4, 0.0)))]),
    'yusuf': lambda t: seg(t, [(*WORK, C_((75.2, 1.0, 0.0)))]),
    'arthur': lambda t: seg(t, [(*WORK, C_((66.4, 1.6, 0.0))), (*HOTEL, lambda t: (96.6, 0.2, ZL2 + 0.9 + 0.25 * math.sin(t * 3.0)))]),
    'father': lambda t: seg(t, [(*VAULT, C_((112.4, 19.4, ZL3 + 0.35)))]),
    'mark': lambda t: seg(t, [(*SAFE, C_((14.6, 0.6, 0.0)))]),
    'walker1': lambda t: seg(t, [(*HOOK, lambda t: walk(t, 0.0, HOOK[1], (-9.0, -7.0, 0.12), (-2.0, -7.1, 0.12)))]),
    'walker2': lambda t: seg(t, [(*HOOK, lambda t: walk(t, 0.0, HOOK[1], (-1.0, -17.0, 0.12), (-8.0, -16.9, 0.12)))]),
    'kid1': lambda t: seg(t, [(*HOME, C_((178.6, 10.6, 0.0)))]),
    'kid2': lambda t: seg(t, [(*HOME, C_((181.0, 10.2, 0.0)))]),
}
def roll_at(t):                           # Fischer drops when Mal fires, and again when he falls off the roof
    if COURT[0] <= t < COURT[1] and t > b['bang']: return -1.5 * ease((t - b['bang']) / 0.35)
    return 0.0

# ------------------------------------------------------------------ camera (t, position, look-at, lens) -------------
SEG_A = [
    (0.0, (7.4, -12.4, 1.55), (-6.0, -11.4, 2.4), 22),                    # down the pastel street
    (b['steal'], (7.0, -12.3, 1.5), (-14.0, -11.0, 6.0), 21),               # the far end folds up into the sky
    (b['secrets'] + 0.2, (6.6, -12.2, 1.45), (-14.0, -11.0, 9.0), 20),
    (b['time'] - 0.05, (5.4, -12.2, 1.55), (0.5, -11.6, 1.6), 22),          # back on him
    (b['leave'] + 0.1, (3.6, -12.1, 1.55), (1.2, -11.6, 1.6), 24),
    (b['dom'] - 0.25, (9.0, -11.6, 2.0), (17.0, -2.0, 1.8), 22),            # into the vault room
    (b['cobb1'] + 0.2, (16.6, -7.6, 1.9), (16.4, 1.0, 1.55), 22),
    (b['minds'], (16.8, -5.6, 1.8), (16.6, 1.0, 1.5), 23),
    (b['dream'] + 0.3, (17.0, -5.1, 1.75), (16.6, 1.5, 1.5), 24),
    (b['client'] - 0.1, (26.0, -11.0, 6.0), (34.0, -2.0, 18.0), 22),        # up the tower face
    (b['saito1'] - 0.1, (33.6, -9.4, ROOFZ + 2.6), (33.8, -1.0, ROOFZ + 1.3), 22),
    (b['kids'], (33.8, -8.0, ROOFZ + 2.2), (33.8, -1.0, ROOFZ + 1.3), 23),
    (b['plants'] + 0.4, (34.0, -7.6, ROOFZ + 2.1), (34.0, -1.0, ROOFZ + 1.3), 24),
    (b['robert'] - 0.1, (42.0, -14.0, TZ + 6.0), (51.0, -2.0, TZ + 6.0), 20),  # over to the plum tower
    (b['fischer1'] + 0.2, (50.4, -16.0, TZ + 3.0), (51.0, -2.0, TZ + 6.0), 17),
    (b['dying1'], (50.4, -18.0, TZ + 3.0), (51.0, -2.0, TZ + 7.5), 16),
    (b['company'] + 0.4, (50.6, -18.4, TZ + 3.0), (51.0, -2.0, TZ + 7.0), 16),
    (b['team'] - 0.25, (62.0, -14.0, 6.0), (70.0, 0.0, 1.6), 20),           # down into the workshop
    (b['architect'], (69.8, -7.6, 1.9), (70.4, 1.0, 1.35), 21),
    (b['forger'], (71.6, -7.4, 1.9), (72.2, 1.0, 1.35), 21),
    (b['chemist'] + 0.2, (72.2, -7.8, 1.95), (72.0, 1.0, 1.35), 20),
    (b['drop1'], (72.0, -5.6, 2.6), (72.0, -1.0, -6.0), 21),               # down through the floor
    (b['drop1'] + 0.45, (74.0, -10.0, ZL1 + 8.0), (82.0, -12.0, ZL1 + 0.8), 21),
    (b['van'] - 0.15, (80.0, -18.2, ZL1 + 2.4), (86.0, -12.0, ZL1 + 1.1), 21),   # level 1: chase the van
    (b['van'] + 0.45, (85.0, -18.0, ZL1 + 2.2), (91.0, -12.0, ZL1 + 1.1), 21),
    (b['hotel'] - 0.15, (92.0, -4.0, ZL1 - 6.0), (96.0, 0.0, ZL2 + 1.0), 21),    # down into the hotel
    (b['hotel'] + 0.35, (92.8, -0.3, ZL2 + 1.6), (100.0, 0.4, ZL2 + 1.2), 20),
    (b['snowy'] - 0.1, (95.0, -1.0, ZL2 - 10.0), (104.0, 14.0, ZL3 + 2.0), 21),  # down to the snowy mountain
    (b['fortress'] + 0.3, (101.0, -12.0, ZL3 + 5.0), (108.0, 18.0, ZL3 + 4.0), 20),
    (b['sedative'] + 0.3, (102.0, -9.0, ZL3 + 4.0), (108.0, 18.0, ZL3 + 3.5), 21),
    (b['dying2'] + 0.3, (100.0, -16.0, ZL3 + 1.0), (100.0, -6.0, ZL3 - 30.0), 21), # over the edge, down
    (b['limbo1'] - 0.2, (96.0, -34.0, ZLB + 9.0), (110.0, 6.0, ZLB + 10.0), 20),  # limbo: a sunset sea
    (b['limbo1'] + 0.5, (96.0, -30.0, ZLB + 7.0), (110.0, 6.0, ZLB + 9.0), 20),
    (b['dead'] - 0.1, (98.2, -12.6, ZLB + 2.0), (98.6, 0.0, ZLB + 1.4), 21),     # the beach house
    (b['mal1'] + 0.2, (98.6, -12.6, ZLB + 2.2), (99.0, 0.0, ZLB + 1.6), 20),
    (b['planted1'], (98.4, -10.6, ZLB + 1.7), (98.5, 0.0, ZLB + 1.0), 21),
    (b['real'] + 0.2, (98.4, -9.8, ZLB + 1.55), (98.5, 0.0, ZLB + 1.0), 22),
    (b['killed'] + 0.4, (97.0, -11.0, ZLB + 2.6), (112.0, 4.0, ZLB + 6.0), 20),  # away, out to sea
    (b['mal2'] - 0.15, (103.0, -5.0, ZL3 + 2.6), (105.0, 6.0, ZL3 + 1.3), 21),   # up: the fortress courtyard
    (b['fischer2'] + 0.25, (105.0, -4.2, ZL3 + 2.0), (105.0, 6.0, ZL3 + 1.2), 22),
    (b['ariadne2'] - 0.1, (114.0, -10.0, LROOF + 6.0), (121.5, 6.0, LROOF + 1.0), 21),   # down: the limbo roof
    (b['dive'] + 0.1, (121.6, -4.4, LROOF + 2.2), (121.8, 6.0, LROOF + 1.2), 21),
    (b['back'], (122.4, -3.6, LROOF + 2.0), (123.8, 6.0, LROOF + 0.4), 21),
    (b['back'] + 0.45, (123.4, -2.6, LROOF + 1.8), (125.0, 6.0, LROOF - 6.0), 21),  # he drops: look down after him
    (b['father'] - 0.3, (110.6, 8.4, ZL3 + 2.6), (110.8, 20.0, ZL3 + 1.2), 21),     # up: the vault room
    (b['live'], (110.8, 10.8, ZL3 + 2.0), (110.8, 20.0, ZL3 + 1.0), 22),
    (b['idea'], (110.8, 12.2, ZL3 + 1.6), (110.8, 20.0, ZL3 + 0.8), 23),
    (b['planted2'] + 0.5, (110.8, 13.4, ZL3 + 1.4), (110.8, 20.0, ZL3 + 0.9), 24),
    (b['saito2'] - 0.2, (148.6, -9.0, CASZ + 3.0), (148.6, 4.0, CASZ + 1.4), 21),     # down: the seaside hall
    (b['finds'], (148.6, -7.4, CASZ + 2.0), (148.6, 4.0, CASZ + 1.2), 22),
    (b['old'] + 0.3, (149.0, -5.6, CASZ + 1.8), (149.4, 4.0, CASZ + 1.2), 24),
    (b['up'], (149.0, -5.4, CASZ + 3.0), (149.0, -4.0, CASZ + 40.0), 22),            # the kick: straight up
    (b['up'] + 0.5, (148.0, -0.2, PLZ + 1.5), (156.0, 0.0, PLZ + 1.1), 20),          # the plane cabin
    (b['saito3'], (148.6, -0.1, PLZ + 1.45), (156.0, 0.0, PLZ + 1.05), 21),
    (b['call'] + 0.3, (149.4, 0.0, PLZ + 1.4), (156.0, -0.4, PLZ + 1.0), 22),
    (b['home2'] - 0.05, (170.0, -12.0, 14.0), (176.0, 2.0, 1.0), 20),               # out and down to the house
    (b['home2'] + 0.4, (176.0, -6.8, 1.8), (176.4, 2.0, 1.0), 21),
    (b['spins'], (176.2, -5.0, 1.6), (176.2, 1.0, 0.85), 22),
    (b['top'] + 0.3, (176.2, -2.4, 1.3), (176.2, 1.0, 0.95), 24),
    (b['wait'], (176.2, -1.2, 1.15), (176.2, 2.0, 0.95), 26),
    (b['fall'], (176.2, -0.25, 1.02), (176.2, 2.0, 0.9), 28),
    (DUR, (176.2, -0.05, 1.0), (176.2, 2.0, 0.9), 30),
]

def spline(keys, t):
    T = [k[0] for k in keys]
    if t <= T[0]: return Vector(keys[0][1]), Vector(keys[0][2]), keys[0][3]
    if t >= T[-1]: return Vector(keys[-1][1]), Vector(keys[-1][2]), keys[-1][3]
    i = max(j for j in range(len(T) - 1) if T[j] <= t); h = T[i + 1] - T[i]; s = (t - T[i]) / h
    h00 = 2 * s ** 3 - 3 * s ** 2 + 1; h10 = s ** 3 - 2 * s ** 2 + s; h01 = -2 * s ** 3 + 3 * s ** 2; h11 = s ** 3 - s ** 2
    def slope(vals, j):
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
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 2; sc.cycles.diffuse_bounces = 1; sc.cycles.glossy_bounces = 0; sc.cycles.transparent_max_bounces = 4
sc.render.resolution_x, sc.render.resolution_y = int(1080 * SCALE), int(1920 * SCALE)
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92; sc.render.fps = FPS
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.4
F2.outlines(sc, thickness=2.6, col=(0.09, 0.06, 0.12))
fs_ = sc.view_layers[0].freestyle_settings; fs_.crease_angle = math.radians(140)

def kf(owner, path, f, v): setattr(owner, path, v); owner.keyframe_insert(path, frame=f)
def F(t): return int(round(t * FPS))
def lin(c): return tuple((v / 255.0) ** 2.2 for v in c)
def hexc(h): h = h.lstrip('#'); return lin((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))

# ------------------------------------------------------------------ the toon material --------------------------------
# Cel shading without lights: N.L against a fixed key direction picks one of three flat bands (shadow / base / light),
# a short-range ambient-occlusion pass darkens contact areas, and the result is emitted as-is (Standard view: the
# colours on screen are the colours written here). Optional flat patterns: windows, checker, stripes, dots.
KEY = Vector((0.42, -0.62, 0.66)).normalized()
SHADOW_TINT = hexc('#5a4a8a')
def toon(name, col, pattern=None, col2=None, scale=1.0, cell=(3.0, 3.4), lit=0.35, glow=None, ao=True):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; n = nt.nodes; Lk = nt.links.new
    for nn in list(n): n.remove(nn)
    out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission'); Lk(em.outputs[0], out.inputs['Surface'])
    base = hexc(col) if isinstance(col, str) else col
    geo = n.new('ShaderNodeNewGeometry')
    def math_(op, a=None, c=None, va=0.0, vc=0.0):
        mm = n.new('ShaderNodeMath'); mm.operation = op
        if a is not None: Lk(a, mm.inputs[0])
        else: mm.inputs[0].default_value = va
        if c is not None: Lk(c, mm.inputs[1])
        else: mm.inputs[1].default_value = vc
        return mm.outputs[0]
    def mixc(fac, a, c):
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        if isinstance(fac, (int, float)): mx.inputs[0].default_value = fac
        else: Lk(fac, mx.inputs[0])
        for idx, v in ((6, a), (7, c)):
            if isinstance(v, tuple): mx.inputs[idx].default_value = (*v, 1)
            else: Lk(v, mx.inputs[idx])
        return mx.outputs[2]
    col_sock = base
    if pattern:
        c2 = hexc(col2) if isinstance(col2, str) else (col2 or tuple(min(1, v * 1.4 + 0.05) for v in base))
        tc = n.new('ShaderNodeTexCoord'); src = tc.outputs['Object']
        if pattern == 'checker':
            ck = n.new('ShaderNodeTexChecker'); ck.inputs['Scale'].default_value = scale; Lk(src, ck.inputs['Vector']); col_sock = mixc(ck.outputs['Fac'], base, c2)
        elif pattern == 'stripes':
            sp = n.new('ShaderNodeSeparateXYZ'); Lk(src, sp.inputs[0]); f_ = math_('FRACT', math_('MULTIPLY', math_('ADD', sp.outputs['X'], sp.outputs['Z']), None, vc=scale))
            col_sock = mixc(math_('GREATER_THAN', f_, None, vc=0.5), base, c2)
        elif pattern == 'dots':
            vo = n.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = scale; Lk(src, vo.inputs['Vector'])
            col_sock = mixc(math_('LESS_THAN', vo.outputs['Distance'], None, vc=0.22), base, c2)
        elif pattern == 'windows':                      # a grid of windows on building sides, some lit
            wp = n.new('ShaderNodeSeparateXYZ'); Lk(geo.outputs['Position'], wp.inputs[0]); sn = n.new('ShaderNodeSeparateXYZ'); Lk(geo.outputs['Normal'], sn.inputs[0])
            u = math_('DIVIDE', math_('ADD', wp.outputs['X'], wp.outputs['Y']), None, vc=cell[0]); v = math_('DIVIDE', wp.outputs['Z'], None, vc=cell[1])
            fu = math_('ABSOLUTE', math_('SUBTRACT', math_('FRACT', u), None, vc=0.5)); fv = math_('ABSOLUTE', math_('SUBTRACT', math_('FRACT', v), None, vc=0.5))
            win = math_('MULTIPLY', math_('LESS_THAN', fu, None, vc=0.3), math_('LESS_THAN', fv, None, vc=0.28))
            side = math_('LESS_THAN', math_('ABSOLUTE', sn.outputs['Z']), None, vc=0.5); win = math_('MULTIPLY', win, side)
            hsh = math_('FRACT', math_('MULTIPLY', math_('SINE', math_('ADD', math_('MULTIPLY', math_('FLOOR', u), None, vc=12.9898), math_('MULTIPLY', math_('FLOOR', v), None, vc=78.233))), None, vc=43758.5))
            wincol = mixc(math_('LESS_THAN', hsh, None, vc=lit), c2, hexc('#fff1a8'))
            col_sock = mixc(win, base, wincol)
    # cel bands from N.L
    dp = n.new('ShaderNodeVectorMath'); dp.operation = 'DOT_PRODUCT'; Lk(geo.outputs['Normal'], dp.inputs[0]); dp.inputs[1].default_value = KEY
    fac = math_('ADD', math_('MULTIPLY', dp.outputs['Value'], None, vc=0.5), None, vc=0.5)
    band_s = math_('LESS_THAN', fac, None, vc=0.42); band_h = math_('GREATER_THAN', fac, None, vc=0.8)
    shadow = mixc(0.32, (0, 0, 0), SHADOW_TINT)                     # a cool purple shadow, multiplied in
    sh = n.new('ShaderNodeMix'); sh.data_type = 'RGBA'; sh.blend_type = 'MULTIPLY'; Lk(band_s, sh.inputs[0])
    if isinstance(col_sock, tuple): sh.inputs[6].default_value = (*col_sock, 1)
    else: Lk(col_sock, sh.inputs[6])
    sh.inputs[7].default_value = (0.62, 0.58, 0.78, 1)
    hl = n.new('ShaderNodeMix'); hl.data_type = 'RGBA'; hl.blend_type = 'SCREEN'; Lk(math_('MULTIPLY', band_h, None, vc=0.22), hl.inputs[0]); Lk(sh.outputs[2], hl.inputs[6])
    hl.inputs[7].default_value = (1.0, 0.97, 0.9, 1)
    cel = hl.outputs[2]
    if ao:
        aon = n.new('ShaderNodeAmbientOcclusion'); aon.samples = 6; aon.inputs['Distance'].default_value = 0.9; Lk(cel, aon.inputs['Color'])
        cel = mixc(0.55, cel, aon.outputs['Color'])
    Lk(cel, em.inputs['Color']); em.inputs['Strength'].default_value = 1.0
    if glow is not None: em.inputs['Strength'].default_value = glow
    return m
def flat(name, col, strength=1.0):             # unshaded flat colour (glowing things, skies)
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes
    for nn in list(n): n.remove(nn)
    out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission'); m.node_tree.links.new(em.outputs[0], out.inputs['Surface'])
    em.inputs['Color'].default_value = (*(hexc(col) if isinstance(col, str) else col), 1); em.inputs['Strength'].default_value = strength; return m
def skygrad(name, z0, z1, bottom, top, mid=None):  # an emissive gradient over world height (a level's own sky)
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; Lk = m.node_tree.links.new
    for nn in list(n): n.remove(nn)
    out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission'); Lk(em.outputs[0], out.inputs['Surface'])
    geo = n.new('ShaderNodeNewGeometry'); sp = n.new('ShaderNodeSeparateXYZ'); Lk(geo.outputs['Position'], sp.inputs[0])
    mr = n.new('ShaderNodeMapRange'); Lk(sp.outputs['Z'], mr.inputs['Value']); mr.inputs['From Min'].default_value = z0; mr.inputs['From Max'].default_value = z1
    rp = n.new('ShaderNodeValToRGB'); Lk(mr.outputs['Result'], rp.inputs['Fac'])
    rp.color_ramp.elements[0].color = (*hexc(bottom), 1); rp.color_ramp.elements[1].color = (*hexc(top), 1)
    if mid: e_ = rp.color_ramp.elements.new(0.35); e_.color = (*hexc(mid), 1)
    Lk(rp.outputs['Color'], em.inputs['Color']); return m

def solid_box(loc, size, m, name='box'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = size; bpy.ops.object.transform_apply(scale=True); o.name = name
    o.data.materials.append(m); return o
def span(x0, x1, y0, y1, z0, z1, m, name='box'): return solid_box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), m, name)
def cut(obj, cutter):
    md = obj.modifiers.new('cut', 'BOOLEAN'); md.object = cutter; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    bpy.context.view_layer.objects.active = obj; bpy.ops.object.modifier_apply(modifier='cut'); bpy.data.objects.remove(cutter)
def hole(obj, x0, x1, y0, y1, z0, z1): cut(obj, span(x0, x1, y0, y1, z0, z1, flat('cutter', (1, 0, 0)), 'cutter'))
def room(x0, x1, y0, y1, z0, z1, wall, floor, ceil=None, front_open=True, name='room'):
    """an open-fronted box room (front = low y side)"""
    span(x0, x1, y0, y1, z0 - 0.2, z0, floor, name + 'Floor')
    span(x0, x0 + 0.15, y0, y1, z0, z1, wall, name + 'Wall'); span(x1 - 0.15, x1, y0, y1, z0, z1, wall, name + 'Wall')
    span(x0, x1, y1 - 0.15, y1, z0, z1, wall, name + 'Wall')
    if ceil is not None: span(x0, x1, y0, y1, z1, z1 + 0.15, ceil, name + 'Ceil')
def text(body, loc, size, m, rot=(math.pi / 2, 0, 0), ext=0.02):
    bpy.ops.object.text_add(location=loc); tx = bpy.context.object; tx.rotation_euler = rot; tx.data.body = body; tx.data.size = size
    tx.data.align_x = 'CENTER'; tx.data.align_y = 'CENTER'; tx.data.extrude = ext; tx.data.materials.append(m); return tx
def keyhide(o, t_on=None, t_off=None):          # visible only between t_on and t_off
    if t_on is not None: o.hide_render = True; o.keyframe_insert('hide_render', frame=0); o.hide_render = False; o.keyframe_insert('hide_render', frame=max(1, F(t_on)))
    if t_off is not None: o.hide_render = True; o.keyframe_insert('hide_render', frame=F(t_off))

# ---- palette (candy colours; each level has its own)
INK = flat('ink', '#1c1424')
WHITE = toon('white', '#fbf6ee'); CREAM = toon('cream', '#f6e7c8'); MINT = toon('mint', '#9ee8cf'); PINK = toon('pink', '#ff9ec4')
SKYBLUE = toon('skyblue', '#8fd3ff'); LEMON = toon('lemon', '#ffe066'); CORAL = toon('coral', '#ff7a6b'); LILAC = toon('lilac', '#b9a2ff')
TEAL = toon('teal', '#38c6b8'); NAVY = toon('navy', '#3a4a8f'); WOOD = toon('wood', '#c98b52'); WOODD = toon('woodDark', '#8f5a34')
GRASS = toon('grass', '#7fd36a'); ROAD = toon('road', '#6c6f8e'); SIDEW = toon('sidewalk', '#d9d4e8'); METAL = toon('metal', '#aab4c8')
BLACKT = toon('blackToon', '#33304a'); RED = toon('red', '#ff4f5e'); ORANGE = toon('orange', '#ff9c47'); PLUM = toon('plum', '#7a4a9a')
GOLD = toon('gold', '#ffc23a'); GLASS = toon('glass', '#bfe9ff'); LAMPG = flat('lampGlow', '#fff3b0', 1.4)
TOWN = [toon('town%d' % k, c, 'windows', c2, lit=0.4) for k, (c, c2) in enumerate([('#ff9ec4', '#7fd0ff'), ('#9ee8cf', '#6aa8ff'), ('#ffe066', '#7fb8ff'),
                                                                                    ('#b9a2ff', '#8ae0ff'), ('#ffb38a', '#7fc8ff'), ('#8fd3ff', '#5a8aff')])]

# ---- top world sky (pastel: blue to pink at the horizon) and soft clouds
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']; L = nt.links.new
tco = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L(tco.outputs['Generated'], sep.inputs[0])
ramp = nt.nodes.new('ShaderNodeValToRGB'); L(sep.outputs['Z'], ramp.inputs['Fac'])
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (*hexc('#ffd3e6'), 1)
ramp.color_ramp.elements[1].position = 0.45; ramp.color_ramp.elements[1].color = (*hexc('#6cc0ff'), 1)
e_ = ramp.color_ramp.elements.new(0.12); e_.color = (*hexc('#ffe9c9'), 1)
L(ramp.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0
w.cycles_visibility.diffuse = False
CLOUD = toon('cloud', '#ffffff', ao=False)
def cloud(x, y, z, s):
    for k in range(5): ball((x + (k - 2) * 1.3 * s, y + random.uniform(-0.5, 0.5) * s, z + (0.4 if k in (1, 2, 3) else 0) * s + (0.4 if k == 2 else 0) * s), (1.2 + (0.5 if k == 2 else 0)) * s, CLOUD, 2, (1, 0.8, 0.75))

# ================================================================== TOP WORLD: THE PASTEL DREAM STREET =================
span(-24, 230, -80, 120, -0.4, -0.1, GRASS, 'ground')
span(-24, 230, -16, -8, -0.12, 0.0, ROAD, 'road')
for (y0, y1) in [(-8.0, -6.0), (-18.0, -16.0)]: span(-24, 230, y0, y1, 0.0, 0.12, SIDEW, 'sidewalk')
for x in range(-22, 228, 6): box((x, -12.0, 0.006), (2.6, 0.18, 0.012), WHITE)
for x in range(-20, 228, 16):                                  # candy lamp posts
    for y in (-7.4, -16.6):
        cyl((x, y, 1.9), 0.07, 3.8, NAVY, v=10); ball((x, y, 3.95), 0.26, LAMPG, 2)
for x in range(-16, 228, 22): cloud(x, random.uniform(40, 90), random.uniform(26, 40), random.uniform(1.6, 2.6))
# the fold: the street beyond x = -24 hinges up into the sky (with its buildings)
bpy.ops.object.empty_add(location=(-24.0, -12.0, 0.0)); fold = bpy.context.object; fold.name = 'foldPivot'
FOLD_OBJS = [span(-110, -24, -60, 40, -0.4, -0.1, GRASS, 'fGround'), span(-110, -24, -16, -8, -0.12, 0.0, ROAD, 'fRoad')]
for (y0, y1) in [(-8.0, -6.0), (-18.0, -16.0)]: FOLD_OBJS.append(span(-110, -24, y0, y1, 0.0, 0.12, SIDEW, 'fSide'))
for x in range(-104, -26, 6): FOLD_OBJS.append(box((x, -12.0, 0.006), (2.6, 0.18, 0.012), WHITE))
for gx in range(-106, -26, 10):
    for (y0, y1) in [(-5.0, 4.0), (-28.0, -19.0)]:
        h = random.uniform(8, 22); FOLD_OBJS.append(span(gx, gx + random.uniform(7, 9), y0, y1, 0.0, h, random.choice(TOWN), 'fBlk'))
def adopt(o, pv): o.parent = pv; o.matrix_parent_inverse = Matrix.Translation(-pv.location)
for o in FOLD_OBJS: adopt(o, fold)
for (t, a) in [(0, 0.0), (b['fold'], 0.0), (b['secrets'] + 0.6, 2.2), (b['time'] + 0.4, 2.35), (b['dom'], 2.35)]:
    fold.rotation_euler = (0, a, 0); fold.keyframe_insert('rotation_euler', frame=F(t))
# street buildings near the hook (north and south)
for (x0, x1, h, k) in [(-24, -16, 14, 0), (-15, -8, 20, 2), (-7, 0, 12, 4), (1, 8, 16, 1)]:
    span(x0, x1, -5.0, 4.0, 0.0, h, TOWN[k], 'nBlk'); box(((x0 + x1) / 2, -5.3, 3.3), (x1 - x0 - 1.0, 0.7, 0.12), random.choice([CORAL, TEAL, LEMON, LILAC]))
for (x0, x1, h, k) in [(-24, -15, 18, 3), (-14, -6, 11, 5), (-5, 4, 15, 0), (5, 14, 22, 2), (15, 26, 13, 4)]:
    span(x0, x1, -28.0, -19.0, 0.0, h, TOWN[k], 'sBlk')

# ================================================================== THE VAULT ROOM (stealing an idea) ================
vb = span(10, 24, -6, 6, 0.0, 12.0, TOWN[1], 'vaultBlock'); hole(vb, 10.4, 23.6, -6.6, 5.6, 0.0, 4.0)
span(10.4, 23.6, -5.8, 5.6, -0.05, 0.02, toon('vaultFloor', '#7a6ad8', 'checker', '#9a8af0', scale=0.9), 'vaultFloor')
span(10.4, 23.6, 5.4, 5.6, 0.0, 4.0, toon('vaultWall', '#5a4ab8'), 'vaultWall')
cyl((17.6, 5.2, 2.0), 1.75, 0.35, GOLD, (math.pi / 2, 0, 0), 32)                    # the round vault door frame
cyl((19.6, 4.0, 2.0), 1.55, 0.25, toon('vaultDoor', '#ffd86a'), (math.pi / 2, 0, -1.0), 32)   # the door, swung open
cyl((17.6, 5.3, 2.0), 1.45, 0.3, toon('vaultInside', '#2a1f5a', ao=False), (math.pi / 2, 0, 0), 32)
for k in range(7):                                                                     # glowing ideas on shelves
    a = k / 7 * 2 * math.pi; ball((17.6 + 0.85 * math.cos(a), 5.05, 2.0 + 0.85 * math.sin(a)), 0.18, flat('ideaGlow%d' % k, ['#fff07a', '#7af0ff', '#ff9af0', '#a8ff7a'][k % 4], 1.6), 2)
box((14.6, 1.2, 0.45), (1.4, 1.4, 0.9), CORAL); box((14.6, 1.8, 1.2), (1.4, 0.25, 1.0), CORAL)  # the dreamer's armchair
box((21.6, 2.6, 0.5), (1.6, 0.8, 1.0), WOOD)
for (x, c) in [(11.4, PINK), (12.2, MINT)]: cyl((x, 5.0, 0.6), 0.3, 1.2, c, v=12)

# ================================================================== SAITO'S ROOFTOP (helicopter) =====================
tw = span(28, 40, -6, 6, 0.0, ROOFZ, TOWN[3], 'saitoTower')
span(28.2, 39.8, -5.8, 5.8, ROOFZ, ROOFZ + 0.15, toon('roofDeck', '#e8e2f6'), 'roofDeck')
cyl((34.0, 2.0, ROOFZ + 0.17), 3.0, 0.04, toon('helipad', '#ffb347'), v=40); cyl((34.0, 2.0, ROOFZ + 0.19), 2.4, 0.04, toon('helipadIn', '#3a4a8f'), v=40)
bpy.ops.object.empty_add(location=(34.0, 2.6, ROOFZ + 1.4)); heli = bpy.context.object
for (o_) in [ball((0, 0, 0), 1.1, RED, 2, (1.5, 1.0, 0.95)), ball((-0.7, 0.0, 0.15), 0.62, GLASS, 2, (1.0, 1.15, 0.95)),
             cyl((2.4, 0, 0.25), 0.18, 2.6, RED, (0, math.pi / 2, 0), 12), box((3.6, 0, 0.7), (0.4, 0.12, 0.9), RED),
             box((0, -0.7, -1.05), (2.4, 0.12, 0.1), METAL), box((0, 0.7, -1.05), (2.4, 0.12, 0.1), METAL), cyl((0, 0, 1.15), 0.12, 0.4, METAL, v=10)]:
    o_.parent = heli
bpy.ops.object.empty_add(location=(34.0, 2.6, ROOFZ + 2.75)); rotor = bpy.context.object
for a in (0, math.pi / 2): box((0, 0, 0), (6.0, 0.24, 0.05), BLACKT, (0, 0, a)).parent = rotor
for f in range(0, NF, 4): rotor.rotation_euler = (0, 0, f * 0.35); rotor.keyframe_insert('rotation_euler', frame=f)
for x in (28.4, 39.6): span(x - 0.1, x + 0.1, -5.8, 5.8, ROOFZ, ROOFZ + 0.9, WHITE, 'rail')
span(28.2, 39.8, -5.9, -5.7, ROOFZ, ROOFZ + 0.9, WHITE, 'rail')

# ================================================================== FISCHER'S TOWER (it splits in two) ===============
span(44, 58, -4, 10, 0.0, TZ, toon('fischerBase', '#7a4a9a', 'windows', '#c9a8ff', cell=(2.4, 3.0)), 'fischerBase')
span(48.6, 53.4, -3.4, -1.6, TZ, TZ + 0.18, toon('terrace', '#f6e7c8'), 'terrace'); span(48.6, 53.4, -3.5, -3.3, TZ, TZ + 0.9, GOLD, 'terraceRail')
TOWER_M = toon('fischerTop', '#9a5ac4', 'windows', '#ffd86a', cell=(2.2, 2.8), lit=0.55)
for (side, x0, x1) in [(-1, 44.6, 51.0), (1, 51.0, 57.4)]:
    bpy.ops.object.empty_add(location=(51.0 + side * 6.4, 3.0, TZ)); pv = bpy.context.object
    adopt(span(x0, x1, -3.0, 9.0, TZ, TZ + 26.0, TOWER_M, 'fischerHalf'), pv)
    adopt(cone(((x0 + x1) / 2, 3.0, TZ + 28.5), 3.6, 5.0, GOLD, 4, (0, 0, math.pi / 4)), pv)
    for (t, a) in [(0, 0.0), (b['break'] - 0.05, 0.0), (b['break'] + 0.5, side * 0.22), (b['dying1'] + 0.3, side * 0.2), (DUR, side * 0.2)]:
        pv.rotation_euler = (0, a, 0); pv.keyframe_insert('rotation_euler', frame=F(t))
text('F', (51.0, -3.06, TZ + 22.0), 3.0, GOLD, ext=0.1)

# ================================================================== THE WORKSHOP (the team) ===========================
wb = span(62, 82, -6, 8, 0.0, 9.0, toon('workshopShell', '#ffb38a'), 'workshop'); hole(wb, 62.4, 81.6, -6.6, 7.6, 0.0, 5.0)
span(62.4, 81.6, -5.8, 7.6, -0.05, 0.02, toon('workFloor', '#d8c8a8', 'checker', '#e8dcc0', scale=0.5), 'workFloor')
span(62.4, 81.6, 7.4, 7.6, 0.0, 5.0, toon('workWall', '#f6d6a8', 'stripes', '#f0c890', scale=0.8), 'workWall')
box((71.0, 3.4, 0.82), (5.0, 2.2, 0.08), WOOD); [cyl((71.0 + dx, 3.4 + dy, 0.4), 0.07, 0.8, WOODD, v=8) for dx in (-2.3, 2.3) for dy in (-0.9, 0.9)]
box((71.0, 3.4, 0.87), (4.4, 1.8, 0.01), toon('blueprint', '#3a6ad8', 'checker', '#4a7ae8', scale=3.0, ao=False))
for k in range(9):                                                                                    # the maze model on the plan
    cx, cy = 69.4 + (k % 3) * 1.6, 2.9 + (k // 3) * 0.5; box((cx, cy, 0.97), (random.choice([0.6, 1.2]), 0.07, 0.18), WHITE, (0, 0, random.choice([0, math.pi / 2])))
for k in range(4): box((68.6 + k * 0.4, 3.9, 1.05 + 0.15 * k), (0.3, 0.3, 0.3 + 0.3 * k), random.choice(TOWN))        # little model buildings
box((76.6, 6.8, 1.0), (3.2, 0.8, 0.08), WOOD); box((76.6, 6.8, 0.5), (3.0, 0.7, 1.0), WOODD)
for k in range(6): cyl((75.4 + k * 0.45, 6.8, 1.22), 0.12, 0.36, flat('flask%d' % k, ['#7affb0', '#ff8ad8', '#7ad8ff', '#ffe07a'][k % 4], 1.3), v=12)
box((65.0, 7.3, 2.6), (3.2, 0.1, 1.8), toon('chalk', '#2f5a4a')); box((65.0, 7.25, 2.6), (2.8, 0.02, 1.4), toon('chalkLines', '#4a8a70', 'stripes', '#e8f6ee', scale=4.0, ao=False))
for (x, c) in [(66.4, PINK), (68.6, MINT), (70.8, LEMON), (73.0, LILAC), (75.2, SKYBLUE)]:
    box((x, 0.2, 0.25), (0.8, 0.8, 0.5), c)                                                 # stools / dream chairs

# ================================================================== LEVEL 1: THE RAIN-BLUE CITY (van chase) =========
span(-40, 240, -100, 140, SKY1[1], SKY1[0], skygrad('sky1Ceil', ZL1, SKY1[1], '#bfe3ff', '#6fa8e8'), 'sky1Ceil')
for (x0, x1, y0, y1) in [(-40, -38, -100, 140), (238, 240, -100, 140), (-40, 240, 138, 140), (-40, 240, -100, -98)]:
    span(x0, x1, y0, y1, ZL1 - 2, SKY1[1], skygrad('sky1Wall', ZL1, SKY1[1], '#d8f0ff', '#6fa8e8', '#a8d4ff'), 'sky1Wall')
span(30, 160, -60, 60, ZL1 - 0.4, ZL1 - 0.1, toon('l1Ground', '#5aa8a0'), 'l1Ground')
span(30, 160, -16, -8, ZL1 - 0.12, ZL1, toon('l1Road', '#4a5a8a'), 'l1Road')
for (y0, y1) in [(-8.0, -6.0), (-18.0, -16.0)]: span(30, 160, y0, y1, ZL1, ZL1 + 0.12, toon('l1Side', '#a8c8e8'), 'l1Side')
for x in range(32, 158, 6): box((x, -12.0, ZL1 + 0.006), (2.6, 0.18, 0.012), LEMON)
L1TOWN = [toon('l1town%d' % k, c, 'windows', '#3a5aa8', lit=0.5) for k, c in enumerate(['#4ac0d8', '#5a8ae8', '#38b8a0', '#7a9af0'])]
for gx in range(30, 158, 10):
    for (y0, y1) in [(-5.0, 6.0), (-30.0, -19.0)]:
        span(gx, gx + random.uniform(7.5, 9.0), y0, y1, ZL1, ZL1 + random.uniform(9, 20), random.choice(L1TOWN), 'l1Blk')
for x in range(34, 158, 14):
    for y in (-7.4, -16.6): cyl((x, y, ZL1 + 1.9), 0.07, 3.8, NAVY, v=10); ball((x, y, ZL1 + 3.95), 0.26, LAMPG, 2)
def vehicle(body_m, length, width, height, cab=True):
    bpy.ops.object.empty_add(location=(0, 0, 0)); root = bpy.context.object
    parts = [box((0, 0, 0.75), (length, width, height * 0.75), body_m), box((-length * 0.05, 0, 0.75 + height * 0.5), (length * 0.7, width * 0.96, height * 0.42), body_m)]
    parts += [box((length * 0.32, 0, 0.75 + height * 0.45), (0.06, width * 0.84, height * 0.32), GLASS, (0, -0.4, 0))]
    for sx in (-1, 1):
        parts.append(box((-length * 0.05, sx * width * 0.49, 0.75 + height * 0.5), (length * 0.6, 0.04, height * 0.28), GLASS))
        for fx in (-0.32, 0.32): parts.append(cyl((fx * length, sx * width * 0.5, 0.42), 0.42, 0.3, BLACKT, (math.pi / 2, 0, 0), 14))
    parts.append(box((length * 0.5, 0, 0.62), (0.06, width * 0.7, 0.18), LAMPG))
    for p_ in parts: p_.parent = root
    return root
van = vehicle(toon('vanYellow', '#ffd23a'), 4.6, 2.0, 2.0); car2 = vehicle(toon('chaser', '#ff4f8a'), 4.2, 1.9, 1.5)
for (t, x) in [(0, 70.0), (b['drop1'] + 0.2, 72.0), (b['van'] + 0.6, 92.0), (b['hotel'] + 0.4, 100.0), (DUR, 104.0)]:
    van.location = (x, -10.2, ZL1); van.keyframe_insert('location', frame=F(t)); car2.location = (x - 8.5, -13.6, ZL1); car2.keyframe_insert('location', frame=F(t))
for o_ in (van, car2):
    for fc in o_.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ================================================================== LEVEL 2: THE WARM HOTEL (floating) ===============
span(-40, 240, -100, 140, SKY2[1], SKY2[0], skygrad('sky2Ceil', ZL2 - 10, SKY2[1], '#ffd0a8', '#ff8a7a'), 'sky2Ceil')
for (x0, x1, y0, y1) in [(-40, -38, -100, 140), (238, 240, -100, 140), (-40, 240, 138, 140), (-40, 240, -100, -98)]:
    span(x0, x1, y0, y1, SKY3[0], SKY2[1], skygrad('sky2Wall', ZL2 - 10, SKY2[1], '#ffe6b8', '#ff8a7a', '#ffb89a'), 'sky2Wall')
hb = span(86, 118, -6, 8, ZL2 - 6.0, ZL2 + 10.0, toon('hotelShell', '#e86a5a', 'windows', '#ffd08a', cell=(2.6, 3.2), lit=0.7), 'hotelShell')
hole(hb, 86.4, 117.6, -2.2, 2.2, ZL2, ZL2 + 3.2)
span(86.4, 117.6, -2.2, 2.2, ZL2 - 0.05, ZL2 + 0.02, toon('hotelCarpet', '#8a3a8a', 'checker', '#ffb347', scale=0.7), 'hotelCarpet')
hp = toon('hotelPaper', '#ffcf8a', 'stripes', '#ffb870', scale=1.4)
span(86.4, 117.6, 2.0, 2.2, ZL2, ZL2 + 3.2, hp, 'hotelWallN'); span(86.4, 117.6, -2.2, -2.0, ZL2, ZL2 + 3.2, hp, 'hotelWallS')
for x in range(90, 117, 4):
    for (y, s) in [(1.96, 1), (-1.96, -1)]:
        box((x, y, ZL2 + 1.05), (1.0, 0.06, 2.1), toon('hotelDoor', '#b8563a')); ball((x + 0.34, y - s * 0.06, ZL2 + 1.0), 0.05, GOLD, 1)
        box((x, y - s * 0.02, ZL2 + 2.3), (0.36, 0.02, 0.16), GOLD)
    ball((x + 2.0, 1.95, ZL2 + 2.3), 0.12, LAMPG, 2); ball((x + 2.0, -1.95, ZL2 + 2.3), 0.12, LAMPG, 2)
FLOAT = [box((99.0, 0.6, ZL2 + 1.4), (0.6, 0.35, 0.45), toon('suitcase', '#38c6b8')), box((102.4, -0.8, ZL2 + 2.2), (0.5, 0.5, 0.5), toon('cushion', '#ffe066')),
         cyl((104.6, 0.4, ZL2 + 1.1), 0.22, 0.5, toon('lampF', '#ff9ec4'), v=12), box((107.0, -0.5, ZL2 + 1.8), (0.9, 0.5, 0.08), WOOD)]
for k, o_ in enumerate(FLOAT):
    z0 = o_.location.z
    for f in range(0, NF, 12):
        t = f / FPS; o_.location.z = z0 + 0.25 * math.sin(t * 1.6 + k); o_.rotation_euler = (t * 0.4 + k, t * 0.3, t * 0.5 * (1 if k % 2 else -1))
        o_.keyframe_insert('location', index=2, frame=f); o_.keyframe_insert('rotation_euler', frame=f)

# ================================================================== LEVEL 3: THE SNOWY MOUNTAIN + FORTRESS ===========
span(-40, 240, -100, 140, SKY3[1], SKY3[0], skygrad('sky3Ceil', ZL3, SKY3[1], '#e8fff6', '#8ae0d0'), 'sky3Ceil')
for (x0, x1, y0, y1) in [(-40, -38, -100, 140), (238, 240, -100, 140), (-40, 240, 138, 140), (-40, 240, -100, -98)]:
    span(x0, x1, y0, y1, SKYB[0], SKY3[1], skygrad('sky3Wall', ZL3 - 10, SKY3[1], '#f6fffb', '#8ae0d0', '#c8f6ea'), 'sky3Wall')
SNOW = toon('snow', '#f6fbff'); SNOWB = toon('snowBlue', '#cfe6ff'); ICE = toon('fortMint', '#7ad8c0', 'windows', '#2f6a8a', cell=(2.0, 2.4), lit=0.5)
span(60, 170, -6, 90, SKYB[0], ZL3, SNOW, 'l3Plateau')                                 # the snow plateau (ends at a cliff, y -6)
for (x, y, r, h) in [(70, 60, 22, 36), (98, 70, 26, 44), (130, 66, 24, 40), (155, 50, 18, 30), (62, 30, 12, 20), (150, 26, 12, 18)]:
    cone((x, y, ZL3 + h / 2 - 0.5), r, h, SNOWB if (x + y) % 2 else SNOW, 7); cone((x, y, ZL3 + h * 0.78), r * 0.38, h * 0.45, SNOW, 7)
for (x, y) in [(88, 6), (92, 14), (126, 8), (130, 16), (84, 20), (134, 24), (96, 4), (122, 4)]:   # candy pines
    cyl((x, y, ZL3 + 0.5), 0.2, 1.0, WOODD, v=8); cone((x, y, ZL3 + 2.0), 1.3, 2.6, toon('pine', '#2fae7a'), 9); cone((x, y, ZL3 + 3.4), 0.9, 1.8, toon('pineL', '#4ac88a'), 9)
fort = span(100, 122, 14, 34, ZL3, ZL3 + 11.0, ICE, 'fortress')
hole(fort, 105.0, 117.0, 15.0, 23.0, ZL3, ZL3 + 4.0); hole(fort, 105.4, 116.6, 13.4, 15.2, ZL3, ZL3 + 3.6)           # the vault room, open to the south
span(105.0, 117.0, 15.0, 23.0, ZL3 - 0.05, ZL3 + 0.02, toon('vaultRoomFloor', '#e8f6ff', 'checker', '#cfe6ff', scale=0.8), 'fortFloor')
span(105.0, 117.0, 22.8, 23.0, ZL3, ZL3 + 4.0, toon('vaultRoomWall', '#d8f0ff'), 'fortWall')
for (x, y) in [(100, 14), (122, 14), (100, 34), (122, 34)]:
    cyl((x, y, ZL3 + 7.0), 2.2, 14.0, ICE, v=12); cone((x, y, ZL3 + 15.5), 2.8, 3.2, toon('fortRoof', '#ff7a9a'), 12)
span(102, 120, 4.0, 13.8, ZL3 - 0.02, ZL3 + 0.04, toon('courtyard', '#dfeaf6', 'checker', '#eef6ff', scale=0.6), 'courtyard')
# the hospital bed (the father) and the idea that grows
box((112.4, 19.4, ZL3 + 0.35), (1.1, 2.2, 0.5), WHITE); box((112.4, 20.4, ZL3 + 0.9), (1.1, 0.12, 0.9), METAL); box((112.4, 19.7, ZL3 + 0.62), (1.0, 1.4, 0.06), toon('blanket', '#9ab8e0'))
box((114.4, 21.0, ZL3 + 0.8), (0.5, 0.4, 1.6), METAL); box((114.4, 20.85, ZL3 + 1.3), (0.36, 0.04, 0.26), flat('monitorBeat', '#7affb0', 1.2))
bpy.ops.object.empty_add(location=(110.6, 17.6, ZL3)); sap = bpy.context.object
for p_ in [cyl((0, 0, 0.4), 0.07, 0.8, WOODD, v=8), ball((0, 0, 1.0), 0.5, flat('ideaTree', '#ffe873', 1.3), 2), ball((0.32, 0.1, 0.78), 0.3, flat('ideaTree2', '#a8ff7a', 1.2), 2),
           ball((-0.3, -0.05, 0.85), 0.32, flat('ideaTree3', '#ffd0f0', 1.2), 2)]: p_.parent = sap
cyl((110.6, 17.6, ZL3 + 0.12), 0.35, 0.24, toon('plantPot', '#ff7a6b'), v=16)
for (t, s) in [(0, 0.001), (b['idea'] - 0.1, 0.001), (b['planted2'] + 0.35, 1.15), (b['planted2'] + 0.6, 1.0), (DUR, 1.0)]:
    sap.scale = (s, s, s); sap.keyframe_insert('scale', frame=F(t))

# ================================================================== LIMBO: THE SUNSET SEA ===========================
span(-40, 240, -100, 140, SKYB[1], SKYB[0], skygrad('skyBCeil', ZLB, SKYB[1], '#ffb86a', '#c86ad8'), 'skyBCeil')
for (x0, x1, y0, y1) in [(-40, -38, -100, 140), (238, 240, -100, 140), (-40, 240, 138, 140), (-40, 240, -100, -98)]:
    span(x0, x1, y0, y1, ZLB - 4, SKYB[1], skygrad('skyBWall', ZLB, SKYB[1] - 20, '#ffd27a', '#b05ad0', '#ff8a7a'), 'skyBWall')
span(-40, 240, -100, 140, ZLB - 1.0, ZLB - 0.05, toon('sea', '#2ab8c8', 'stripes', '#5ad8e0', scale=0.18, ao=False), 'sea')
span(86, 162, -8, 14, ZLB - 0.4, ZLB + 0.15, toon('sand', '#ffd9a0'), 'beach')
SUN = ball((110, 130, ZLB + 22), 12.0, flat('limboSun', '#fff0a0', 1.3), 3); SUN.name = 'limboSun'
CRUMBLE = [toon('crumble%d' % k, c, 'windows', '#5a3a8a', lit=0.3) for k, c in enumerate(['#ff8a6a', '#ffb06a', '#e86aa8', '#c88af0'])]
for k in range(16):                                                                       # crumbling towers out at sea
    x, y = random.uniform(60, 170), random.uniform(30, 110); h = random.uniform(16, 42); tilt = random.uniform(-0.18, 0.18)
    o_ = box((x, y, ZLB + h / 2 - 3), (random.uniform(6, 10), random.uniform(6, 10), h), random.choice(CRUMBLE), (tilt, random.uniform(-0.12, 0.12), 0))
    for j in range(2):                                                                    # chunks breaking off and sinking
        c_ = box((x + random.uniform(-3, 3), y - 4, ZLB + h - 4), (random.uniform(1.5, 3), random.uniform(1.5, 3), random.uniform(1.5, 3)), o_.data.materials[0] if o_.data.materials else CRUMBLE[0])
        t0 = random.uniform(b['limbo1'] - 1.0, b['saito2']); z0 = c_.location.z
        for (t, z) in [(0, z0), (t0, z0), (t0 + 5.0, ZLB - 3)]: c_.location.z = z; c_.keyframe_insert('location', index=2, frame=F(t))
# the little beach house (Mal), with the top on a pedestal
hs = span(94, 102, -2, 4, ZLB + 0.15, ZLB + 4.0, toon('houseWall', '#fff3e0'), 'beachHouse')
cone((98, 1, ZLB + 5.4), 6.2, 2.8, toon('houseRoof', '#ff6a7a'), 4, (0, 0, math.pi / 4))
box((98.0, -2.05, ZLB + 1.2), (1.0, 0.06, 2.1), toon('houseDoor', '#38c6b8')); box((95.6, -2.05, ZLB + 2.2), (1.2, 0.06, 1.0), GLASS); box((100.4, -2.05, ZLB + 2.2), (1.2, 0.06, 1.0), GLASS)
cyl((98.4, -3.5, ZLB + 0.55), 0.22, 0.8, WHITE, v=14)
def spinning_top(loc, t_spin, t_end, wobble_t=None, scale=1.0):
    bpy.ops.object.empty_add(location=loc); root = bpy.context.object
    bpy.ops.object.empty_add(location=(0, 0, 0)); spin = bpy.context.object; spin.parent = root
    tm = toon('topMetal', '#c8d2e0'); tm2 = toon('topBand', '#ff6a7a')
    for p_ in [cone((0, 0, 0.055 * scale), 0.06 * scale, 0.11 * scale, tm, 16, (math.pi, 0, 0)), cyl((0, 0, 0.115 * scale), 0.062 * scale, 0.02 * scale, tm2, v=16),
               cyl((0, 0, 0.15 * scale), 0.012 * scale, 0.07 * scale, tm, v=8)]:
        p_.parent = spin
    ang = 0.0
    for f in range(0, NF, 2):
        t = f / FPS
        if t >= t_spin: ang += 2 * math.pi * 6.0 * 2 / FPS
        spin.rotation_euler = (0, 0, ang); spin.keyframe_insert('rotation_euler', frame=f)
        tilt = 0.0
        if wobble_t is not None and t > wobble_t: tilt = 0.05 * min(1.0, (t - wobble_t) / 1.2)
        root.rotation_euler = (tilt * math.sin(t * 9.0), tilt * math.cos(t * 9.0), 0); root.keyframe_insert('rotation_euler', frame=f)
    return root
spinning_top((98.4, -3.5, ZLB + 0.95), b['planted1'] - 0.2, DUR, scale=1.6)

# the tall limbo building (Fischer is pushed off the roof)
span(114, 130, 2, 14, ZLB - 1, LROOF, toon('limboTower', '#ff9a6a', 'windows', '#6a3a9a', cell=(2.4, 3.0), lit=0.3), 'limboTower')
span(114.2, 129.8, 2.2, 13.8, LROOF, LROOF + 0.12, toon('limboRoof', '#ffd9a0'), 'limboRoof')
for x in (114.3, 129.7): span(x - 0.1, x + 0.1, 2.2, 13.8, LROOF, LROOF + 0.8, WHITE, 'rail')
box((118.0, 11.0, LROOF + 1.0), (1.8, 1.8, 2.0), toon('waterTank', '#38c6b8'))
# the seaside hall (old Saito): pillars, a long table, lanterns, the sea behind
span(138, 160, -6, 10, ZLB - 1, CASZ, toon('rocks', '#c8865a'), 'hallRock')
span(140, 158, -4, 9, CASZ, CASZ + 0.08, toon('hallFloor', '#b8563a', 'checker', '#d86a4a', scale=0.6), 'hallFloor')
span(140, 158, 8.8, 9.0, CASZ, CASZ + 6.0, toon('hallScreen', '#fff3d8', 'stripes', '#f0dcb8', scale=1.2), 'hallBack')
keyhide(span(139.6, 158.4, -4.4, 9.4, CASZ + 6.0, CASZ + 6.6, toon('hallRoof', '#d84a4a'), 'hallRoof'), None, b['old'] + 0.3)   # gone before the kick rises through it
for x in (140.4, 144.6, 153.4, 157.6): cyl((x, -3.6, CASZ + 3.0), 0.3, 6.0, toon('pillar', '#e84a4a'), v=12)
box((148.6, 3.0, CASZ + 0.72), (6.0, 1.4, 0.08), WOODD); box((148.6, 3.0, CASZ + 0.35), (5.6, 1.2, 0.7), toon('tableBody', '#6a3a2a'))
for x in (146.0, 148.6, 151.2): box((x, 3.0, CASZ + 0.82), (0.5, 0.3, 0.12), GOLD)
for x in (142.0, 146.0, 151.0, 155.0): ball((x, -3.4, CASZ + 4.6), 0.42, flat('lantern', '#ffb347', 1.4), 2, (1, 1, 1.3))

# ================================================================== THE PLANE (above the clouds) ======================
bpy.ops.mesh.primitive_cylinder_add(radius=2.3, depth=34.0, vertices=28, location=(155.0, 0.0, PLZ + 1.3), rotation=(0, math.pi / 2, 0)); fus = bpy.context.object
fus.data.materials.append(toon('fuselage', '#f6f2ff'))
sl = fus.modifiers.new('s', 'SOLIDIFY'); sl.thickness = 0.12; bpy.context.view_layer.objects.active = fus; bpy.ops.object.modifier_apply(modifier='s')
for x in range(141, 170, 2):                                                          # windows (cut through the hull)
    for s in (-1, 1): hole(fus, x - 0.3, x + 0.3, s * 2.6 - 0.4, s * 2.6 + 0.4, PLZ + 1.3, PLZ + 1.9)
span(138.2, 171.8, -1.9, 1.9, PLZ - 0.1, PLZ, toon('cabinCarpet', '#4a5ab8', 'stripes', '#5a6ac8', scale=1.0), 'cabinFloor')
SEAT = toon('seat', '#38c6b8'); SEATH = toon('seatHead', '#fff3e0')
for x in range(141, 170, 2):
    for y in (-1.3, -0.85, 0.85, 1.3):
        box((x, y, PLZ + 0.35), (0.6, 0.44, 0.12), SEAT); box((x + 0.27, y, PLZ + 0.8), (0.12, 0.44, 0.95), SEAT); box((x + 0.27, y, PLZ + 1.25), (0.13, 0.36, 0.14), SEATH)
cone((137.0, 0, PLZ + 1.3), 2.3, 3.0, toon('noseCone', '#f6f2ff'), 28, (0, math.pi / 2, 0))
box((156.0, 0, PLZ + 0.4), (5.0, 22.0, 0.25), toon('wing', '#dcd6ff'))
for k in range(22): cloud(random.uniform(120, 200), random.uniform(-40, 50), PLZ + random.uniform(-14, -6), random.uniform(1.8, 3.4))

# ================================================================== HOME: THE KITCHEN TABLE (the top) =================
hm = span(170, 186, -6, 6, 0.0, 7.0, toon('homeShell', '#ffe0b0'), 'home'); hole(hm, 170.4, 185.6, -6.6, 5.6, 0.0, 3.4)
hole(hm, 175.0, 181.0, 5.4, 6.6, 0.0, 3.0)                                              # big glass doors to the garden
cone((178.0, 0, 8.4), 11.6, 3.0, toon('homeRoof', '#ff7a6b'), 4, (0, 0, math.pi / 4))
span(170.4, 185.6, -5.8, 5.6, -0.05, 0.02, toon('homeFloor', '#f6d6a8', 'checker', '#fbe6c4', scale=0.7), 'homeFloor')
box((176.2, 1.0, 0.74), (2.2, 1.3, 0.06), WOOD); [cyl((176.2 + dx, 1.0 + dy, 0.36), 0.05, 0.72, WOODD, v=8) for dx in (-0.95, 0.95) for dy in (-0.5, 0.5)]
for (x, y) in [(175.2, 2.1), (177.2, 2.1)]: box((x, y, 0.45), (0.5, 0.5, 0.06), WOOD); box((x, y + 0.24, 0.8), (0.5, 0.06, 0.7), WOOD)
cyl((177.3, 0.8, 0.82), 0.14, 0.1, toon('bowl', '#38c6b8'), v=16)
for (x, c) in [(171.6, LEMON), (184.4, MINT)]: box((x, 4.8, 1.0), (1.2, 0.7, 2.0), c)
spinning_top((176.2, 1.0, 0.77), b['spins'] + 0.1, DUR, wobble_t=b['fall'] - 0.6, scale=1.4)
span(166, 196, 6.0, 30.0, -0.05, 0.02, GRASS, 'garden')
for (x, y) in [(173, 16), (184, 14), (190, 20)]: cyl((x, y, 1.2), 0.25, 2.4, WOODD, v=10); ball((x, y, 3.2), 1.8, toon('treeTop', '#5ac86a'), 2)
box((182.6, 13.0, 0.9), (0.1, 0.1, 1.8), PINK); box((179.6, 13.0, 0.9), (0.1, 0.1, 1.8), PINK); box((181.1, 13.0, 1.8), (3.1, 0.12, 0.12), PINK)   # a little swing frame

# ================================================================== FILLER: THE TOP-WORLD TOWN ========================
KEEP = [(-30, 27, -30, 7), (27, 60, -8, 12), (60, 84, -8, 10), (86, 120, -8, 12), (136, 200, -8, 32), (-30, 240, -20, -4)]
def free(x0, x1, y0, y1): return not any(x0 < a1 and x1 > a0 and y0 < b1 and y1 > b0 for (a0, a1, b0, b1) in KEEP)
blocks = 0
for gx in range(-30, 230, 12):
    for gy in list(range(-60, -20, 12)) + list(range(6, 90, 12)):
        wx, wy = random.uniform(7, 10), random.uniform(7, 10); x0, y0 = gx + random.uniform(0, 2), gy + random.uniform(0, 2)
        if not free(x0 - 1, x0 + wx + 1, y0 - 1, y0 + wy + 1): continue
        h = random.uniform(8, 24) if gy < 40 else random.uniform(14, 40)
        span(x0, x0 + wx, y0, y0 + wy, 0.0, h, random.choice(TOWN), 'blk'); blocks += 1
        if random.random() < 0.3: cone((x0 + wx / 2, y0 + wy / 2, h + 1.4), min(wx, wy) * 0.4, 2.8, random.choice([CORAL, GOLD, TEAL, LILAC]), 4, (0, 0, math.pi / 4))
print('town blocks', blocks, flush=True)

# ------------------------------------------------------------------ interpolation tidy-up ---------------------------
for ob in bpy.data.objects:
    ad_ = ob.animation_data
    if ad_ and ad_.action:
        for fc in ad_.action.fcurves:
            if fc.data_path == 'hide_render':
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for fc in rotor.animation_data.action.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
# no ink on the skies and the sea (their box edges would draw lines across the horizon)
noink = bpy.data.collections.new('noink'); sc.collection.children.link(noink)
for ob in list(bpy.data.objects):
    if ob.name.startswith(('sky', 'sea', 'limboSun')):
        for c_ in list(ob.users_collection): c_.objects.unlink(ob)
        noink.objects.link(ob)
ls_ = sc.view_layers[0].freestyle_settings.linesets[0]; ls_.select_by_collection = True; ls_.collection = noink; ls_.collection_negation = 'EXCLUSIVE'

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
