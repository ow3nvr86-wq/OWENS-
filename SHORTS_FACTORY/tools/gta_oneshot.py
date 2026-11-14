"""One continuous camera shot through an original sunny Los Santos-style city (no game assets copied):
Grove-Street-style cul-de-sac -> palm boulevard -> stunt ramp over a sunken freeway -> police station plaza.
Animated in Blender: the hero's convertible (launch, flight, barrel roll, skid), the player's bike, chasing police cars.
Writes a 60 fps image sequence + camera.json with, for every frame: the camera, and the world positions of every 2D actor
(hero, player, mailman, NPC clones, ten cops) so the engine can pin the 2D cast to the 3D world.
Run: $BLENDER -b --factory-startup -P tools/gta_oneshot.py -- <out> [--scale 0.5] [--spp 5] [--only F] [--start A --end B]"""
import bpy, math, sys, os, json, random, importlib.util
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0]; arg = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
SCALE, SPP, ONLY = arg('--scale', 0.5), arg('--spp', 5), arg('--only', -1)
FPS, DUR = 60, 54.76; NF = int(round(DUR * FPS))
START, END = arg('--start', 0), arg('--end', NF - 1)
HERE = os.path.dirname(os.path.abspath(__file__))
s_ = importlib.util.spec_from_file_location('presets_fn2', os.path.join(HERE, 'presets_fn2.py')); F2 = importlib.util.module_from_spec(s_); s_.loader.exec_module(F2)
ISL = F2.ISL; box, cyl, cone, ball = ISL.box, ISL.cyl, ISL.cone, ISL.ball; m_plain, m_noise, m_brick, m_emis = F2.m_plain, F2.m_noise, F2.m_brick, ISL.m_emis
os.makedirs(OUT, exist_ok=True); random.seed(12)


# ------------------------------------------------------------------ choreography (seconds, metres) --------
def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def ease5(u): u = min(1, max(0, u)); return u * u * u * (u * (u * 6 - 15) + 10)
def keyed(keys, t, fn=ease):
    """keys: [(t, value tuple)] -> eased interpolation"""
    if t <= keys[0][0]: return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1: u = fn((t - t0) / max(1e-6, t1 - t0)); return tuple(x + (y - x) * u for x, y in zip(a, b))
    return keys[-1][1]

CAR0 = (4.0, 32.0); RAMP0, RAMP1, LIP_Z = 225.0, 238.0, 3.6; LAND_Y, STOP_Y = 320.0, 338.0
T_GO, T_RAMP, T_LIP, T_LAND, T_STOP = 27.6, 38.3, 38.6, 42.75, 43.8
def car_state(t):
    """the hero's convertible: position, heading (z), roll (y)"""
    if t < T_GO: return (CAR0[0], CAR0[1], 0.0), 0.0, 0.0
    if t < T_RAMP:
        u = (t - T_GO) / (T_RAMP - T_GO); s = u ** 1.55; y = CAR0[1] + (RAMP0 - CAR0[1]) * s
        x = CAR0[0] + (3.0 - CAR0[0]) * ease(u * 4)
        return (x, y, 0.0), 0.0, 0.0
    if t < T_LIP:
        u = (t - T_RAMP) / (T_LIP - T_RAMP); return (3.0, RAMP0 + (RAMP1 - RAMP0) * u, LIP_Z * u), 0.0, 0.0
    if t < T_LAND:                                                   # cartoon flight: a slow-mo parabola, then a barrel roll
        u = (t - T_LIP) / (T_LAND - T_LIP); y = RAMP1 + (LAND_Y - RAMP1) * u; z = LIP_Z * (1 - u) + 4 * 12.5 * u * (1 - u)
        roll = 2 * math.pi * ease5((t - 41.2) / 1.4) if t > 41.2 else 0.0
        return (3.0, y, max(0.0, z)), 0.0, roll
    u = min(1.0, (t - T_LAND) / (T_STOP - T_LAND)); y = LAND_Y + (STOP_Y - LAND_Y) * (1 - (1 - u) ** 2.4)
    return (3.0 - 0.8 * ease(u), y, 0.0), 0.32 * ease(u), 0.0
def bike_state(t):
    """the player's bike: parked across the street, then on the car's tail, jumps after it, stops near the station"""
    if t < 27.0: return (-3.0, 47.0, 0.0), 0.0, 0.0
    lag = 1.5; (cx, cy, cz), hd, rl = car_state(max(T_GO, t - lag))
    blend = ease((t - 27.0) / 2.5); x = -3.0 + (cx - 2.2 - -3.0) * blend; y = max(47.0, 47.0 + (cy - 47.0) * blend) if t - lag < T_LAND else cy - 9
    if t - lag >= T_LAND:
        u = min(1.0, (t - lag - T_LAND) / 1.2); x = cx - 2.2 - 4.0 * ease(u); y = LAND_Y + 6 * ease(u)
    return (x, y, cz), 0.25 * math.sin(t * 1.3) * (1 if T_GO < t - lag < T_RAMP else 0), 0.0
COPCARS = [(-1.0, -14.0), (6.5, -19.0)]                              # chasing police cars (x, distance behind the bike)
def copcar_state(i, t):
    x, back = COPCARS[i]
    if t < 30.4: return (x, 40.0 + back * 0.0 - 60, 0.0), 0.0
    (bx, by, bz), _, _ = bike_state(t); y = min(by + back, RAMP0 - 6 - 4 * i)
    if by + back >= RAMP0 - 6 - 4 * i: y = RAMP0 - 6 - 4 * i
    return (x, y, 0.0), 0.0

# 2D actors (world positions per frame)
HERO_PATH = [(0.0, (6.3, 8.0, 0.0)), (8.3, (6.3, 8.0, 0.0)), (21.5, (6.3, 22.5, 0.0)), (26.0, (6.3, 23.0, 0.0)), (26.9, (5.4, 30.6, 0.0))]
def hero_pos(t):
    if t < 27.0: return keyed(HERO_PATH, t, lambda u: u), 1
    if t < 44.1: return (0, 0, 0), 0                                  # in the car (drawn from the seat track)
    (cx, cy, cz), hd, rl = car_state(t); return (cx - 1.6, cy - 0.6, 0.0), 1
def hero_seat(t):
    (cx, cy, cz), hd, rl = car_state(t); return (cx - 0.4, cy - 0.3, cz + 0.55), (1 if 27.0 <= t < 44.1 and not (41.15 < t < 42.65) else 0)
PLAYER_PATH = [(0.0, (-4.0, 42.0, 0.0)), (21.9, (-4.0, 42.0, 0.0)), (23.3, (-3.0, 46.3, 0.0))]
def player_pos(t):
    if t < 20.4: return (0, 0, 0), 0
    if t < 23.3: return keyed(PLAYER_PATH, t), 1
    (bx, by, bz), _, _ = bike_state(t)
    if t < 46.0: return (bx, by - 0.1, bz + 0.62), 1                 # riding
    return (-6.2, 326.5, 0.0), 1
def mailman_pos(t):
    return keyed([(0.0, (-7.5, 40.0, 0.0)), (21.6, (-5.2, 43.2, 0.0))], t, lambda u: u), 1
CLONES = [((7.4, 40.0), -1.1, 0.0), ((7.6, 2.0), 1.05, 2.0), ((-6.5, 30.0), -0.9, 0.5), ((-6.8, 6.0), 1.0, 1.0), ((7.2, 60.0), -1.2, 4.0)]
def clone_pos(i, t):
    (x, y), v, t0 = CLONES[i]; return (x, y + v * max(0.0, t - t0), 0.0), (1 if t < 26.5 else 0)
STATION_DOOR = (0.0, 351.0); PILE = (-6.2, 326.5)
def cop_pos(i, t):
    a = (-4.5 + i * 1.0, STATION_DOOR[1] - 0.5 - (i % 3) * 0.8, 0.0)
    ring = (PILE[0] + math.cos(i * 0.63) * (0.9 + 0.35 * (i % 3)), PILE[1] + math.sin(i * 0.63) * (0.7 + 0.3 * (i % 3)), 0.0)
    aim = (a[0] * 1.6, a[1] - 7.0 - (i % 2) * 1.5, 0.0)
    if t < 45.2: return a, 0
    return keyed([(45.2, a), (46.3, aim), (47.4, aim), (48.95, ring)], t), 1
ACTORS = dict(hero=hero_pos, heroSeat=hero_seat, player=player_pos, mailman=mailman_pos)
for i in range(len(CLONES)): ACTORS['clone%d' % i] = (lambda i: lambda t: clone_pos(i, t))(i)
for i in range(10): ACTORS['cop%d' % i] = (lambda i: lambda t: cop_pos(i, t))(i)

# camera keys: (t, position, look-at, lens) - one continuous move, eased between keys
def follow(t, dx, dy, dz, lx=0.0, ly=4.0, lz=1.2):
    (cx, cy, cz), _, _ = car_state(t); return (t, (cx + dx, cy + dy, cz + dz), (cx + lx, cy + ly, cz + lz))
def hero_follow(t, dx, dy, dz, ly=0.8, lz=1.5):
    (hx, hy, hz), _ = hero_pos(t); return (t, (hx + dx, hy + dy, dz), (hx, hy + ly, lz))
CAM = [(0.0, (34, -70, 78), (4, 24, 0), 28), (2.6, (20, -22, 32), (6, 10, 2), 26), (4.6, (9.6, 4.6, 1.9), (6.3, 8.8, 1.6), 24), (7.6, (8.7, 6.3, 1.7), (6.3, 8.9, 1.7), 24),
       hero_follow(8.6, 3.9, -1.6, 1.6) + (24,), hero_follow(11.6, 3.9, -1.4, 1.6) + (24,), hero_follow(14.6, 3.9, -1.4, 1.65) + (24,),
       hero_follow(16.6, 4.4, -4.2, 3.4, 0.5, 2.0) + (24,), (19.3, (8.4, 22.0, 2.3), (-4.0, 42.0, 1.4), 24), (21.4, (2.0, 35.5, 1.8), (-4.6, 43.0, 1.2), 24),
       (23.4, (1.0, 41.0, 1.7), (-3.0, 46.4, 1.2), 24), (25.5, (0.4, 40.6, 1.6), (-3.0, 46.6, 1.5), 26), (26.1, (9.6, 21.0, 1.7), (6.3, 25.0, 1.3), 24),
       (27.2, (8.8, 26.5, 1.8), (4.5, 33.0, 1.1), 24)]
CAM += [follow(t, dx, dy, dz) + (24,) for (t, dx, dy, dz) in [(28.6, 6.0, -7.5, 2.4), (30.6, 5.5, -9.0, 2.2), (32.4, 6.5, -6.0, 2.0), (34.0, 4.5, -11.0, 2.6)]]
CAM += [(35.6, follow(35.6, 0, 0, 0)[1][:2] + (7.5,), (-1.0, 236.0, 2.5), 24), follow(37.6, 5.0, -6.0, 2.8, 0, 18, 1.5) + (24,), (38.6, (8.0, 226.0, 4.0), (3.0, 238.0, 3.6), 24),
        follow(40.3, 9.0, -2.0, 1.0, 0, 1.5, 0.6) + (24,), follow(41.9, 7.0, -6.5, 2.2, 0, 2.0, 0.5) + (24,), (42.75, (12.0, 314.0, 3.2), (3.0, 322.0, 1.0), 24),
        (44.2, (10.0, 327.0, 2.2), (2.0, 337.0, 1.4), 24), (45.7, (8.5, 321.0, 1.7), (0.0, 350.0, 2.6), 22), (47.4, (7.0, 329.0, 1.8), (-2.0, 337.0, 1.4), 22),
        (48.9, (-0.8, 316.5, 2.3), (-6.0, 327.0, 0.8), 22), (50.4, (-2.6, 320.0, 1.6), (-6.2, 327.0, 0.6), 24), (51.6, (-2.2, 321.2, 1.7), (-5.0, 328.0, 1.6), 26),
        (DUR, (-3.3, 323.6, 1.7), (-5.0, 328.2, 1.75), 30)]


# ------------------------------------------------------------------ the city -------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True); ISL._T.clear()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 3
sc.render.resolution_x, sc.render.resolution_y = int(1080 * SCALE), int(1920 * SCALE)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = -0.45
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92; sc.render.fps = FPS
w = bpy.data.worlds.new('sun'); sc.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'; sky.sun_elevation = math.radians(28); sky.sun_rotation = math.radians(200); sky.dust_density = 1.2
nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.22
bpy.ops.object.light_add(type='SUN'); sun = bpy.context.object; sun.data.energy = 3.8; sun.data.angle = math.radians(2.0); sun.data.color = (1.0, 0.9, 0.78)
sun.rotation_euler = (math.radians(62), 0, math.radians(200 + 180 - 90))

asphalt = m_noise('asph', (0.07, 0.07, 0.08), (0.12, 0.12, 0.13), 40, 0.75, 0.08)
walk = m_brick('walk', (0.62, 0.6, 0.56), (0.55, 0.53, 0.5), (0.4, 0.39, 0.37), 1.0, 0.5, 0.5)
lawn = m_noise('lawn', (0.25, 0.4, 0.1), (0.36, 0.5, 0.16), 3, 0.9, 0.1)
dirt = m_noise('lotDirt', (0.55, 0.47, 0.35), (0.62, 0.55, 0.42), 6, 0.95, 0.1)
yellow = m_plain('yellowLine', (0.95, 0.75, 0.15), 0.5); white = m_plain('whiteLine', (0.92, 0.92, 0.9), 0.5)
dark = m_plain('dark', (0.04, 0.04, 0.05), 0.6); glass = m_plain('glass', (0.25, 0.4, 0.55), 0.08); trim = m_plain('trim', (0.85, 0.83, 0.78), 0.6)
stucco = [m_plain('stucco%d' % i, c, 0.85) for i, c in enumerate([(0.38, 0.62, 0.4), (0.85, 0.66, 0.3), (0.85, 0.45, 0.32), (0.45, 0.58, 0.78), (0.82, 0.78, 0.66)])]
shopw = [m_brick('shop%d' % i, c, tuple(v * 0.88 for v in c), (0.7, 0.68, 0.64), 2.5) for i, c in enumerate([(0.72, 0.42, 0.22), (0.3, 0.42, 0.6), (0.78, 0.7, 0.5), (0.6, 0.25, 0.2), (0.25, 0.5, 0.45)])]
trunk = m_plain('palmTrunk', (0.42, 0.3, 0.2), 0.9); frond = m_plain('frond', (0.16, 0.4, 0.12), 0.8)


def ground(y0, y1, x0, x1, m, z=0.0): box(((x0 + x1) / 2, (y0 + y1) / 2, z - 0.05), (x1 - x0, y1 - y0, 0.1), m)
def palm(x, y, h=9.0):
    for k in range(6): cyl((x + math.sin(k * 0.5) * 0.15 * k, y, h * (k + 0.5) / 6), 0.22 - 0.02 * k, h / 6 + 0.05, trunk, v=10)
    tx = x + 0.6
    for k in range(9):
        a = k * 2 * math.pi / 9; cone((tx + math.cos(a) * 1.5, y + math.sin(a) * 1.5, h - 0.5), 0.5, 3.4, frond, 4, (math.pi / 2 - 0.35, 0, a + math.pi / 2))
def house(x, y, w, d, h, m, face):
    box((x, y, h / 2), (w, d, h), m); box((x, y, h + 0.15), (w + 0.6, d + 0.6, 0.3), trim)
    fx = x + face * (w / 2 + 0.02)
    box((fx, y - d * 0.15, 1.05), (0.1, 1.0, 2.1), m_plain('door%d' % int(abs(x * y)), random.choice([(0.5, 0.2, 0.15), (0.2, 0.3, 0.5), (0.3, 0.3, 0.3)]), 0.6))
    for dy in (-d * 0.35, d * 0.25): box((fx, y + dy, 1.6), (0.1, 1.6, 1.2), glass)
    for k in range(int(d / 0.6)): box((x + face * (w / 2 + 3.2), y - d / 2 + k * 0.6, 0.6), (0.04, 0.04, 1.2), dark)        # chain-link fence posts
    box((x + face * (w / 2 + 3.2), y, 1.15), (0.03, d, 0.05), dark)
chrome = m_plain('chrome', (0.85, 0.86, 0.88), 0.15, 1.0); rim = m_plain('rim', (0.7, 0.72, 0.75), 0.25, 0.9); seatm = m_plain('seat', (0.45, 0.08, 0.06), 0.6)
headl = m_emis('headlight', (1.0, 0.95, 0.85), 4.0); taill = m_emis('taillight', (1.0, 0.08, 0.05), 3.0)
def bev(o, w=0.12):
    m = o.modifiers.new('B', 'BEVEL'); m.width = w; m.segments = 3; m.limit_method = 'ANGLE'; return o
def car(x, y, rot, col, convertible=False, lights=False):
    """a cartoon muscle car: rounded body, hood, seats or cabin, chrome bumpers, glowing lights, wheels with rims"""
    cm = m_plain('car%.0f%.0f' % (x, y), col, 0.22); c, s = math.cos(rot), math.sin(rot); parts = []
    P = lambda dx, dy, z: (x + dx * c - dy * s, y + dx * s + dy * c, z)
    parts.append(bev(box(P(0, 0, 0.6), (1.95, 4.5, 0.62), cm, (0, 0, rot)), 0.18))
    parts.append(bev(box(P(0, 1.35, 0.95), (1.8, 1.6, 0.14), cm, (math.radians(-4), 0, rot)), 0.06))           # hood
    if convertible:
        for dx in (-0.45, 0.45): parts.append(bev(box(P(dx, -0.2, 1.0), (0.7, 0.6, 0.3), seatm, (0, 0, rot)), 0.08)); parts.append(bev(box(P(dx, -0.45, 1.3), (0.7, 0.14, 0.6), seatm, (0, 0, rot)), 0.06))
        parts.append(box(P(0, 0.62, 1.22), (1.75, 0.06, 0.5), glass, (math.radians(-25), 0, rot)))
        parts.append(box(P(0, 0.66, 1.48), (1.8, 0.06, 0.06), chrome, (math.radians(-25), 0, rot)))
    else:
        parts.append(bev(box(P(0, -0.25, 1.25), (1.7, 2.2, 0.62), glass, (0, 0, rot)), 0.15))
        parts.append(bev(box(P(0, -0.25, 1.58), (1.72, 1.7, 0.08), cm, (0, 0, rot)), 0.05))
    for dy in (2.27, -2.27): parts.append(bev(box(P(0, dy, 0.48), (2.0, 0.14, 0.2), chrome, (0, 0, rot)), 0.05))
    for dx in (-0.7, 0.7):
        parts.append(cyl(P(dx, 2.3, 0.68), 0.13, 0.06, headl, (math.pi / 2, 0, rot), 16)); parts.append(box(P(dx, -2.3, 0.7), (0.4, 0.06, 0.14), taill, (0, 0, rot)))
    for dx in (-0.97, 0.97):
        for dy in (-1.45, 1.45):
            parts.append(cyl(P(dx, dy, 0.38), 0.38, 0.3, dark, (0, math.pi / 2, rot), 20)); parts.append(cyl(P(dx * 1.02, dy, 0.38), 0.22, 0.31, rim, (0, math.pi / 2, rot), 12))
    if lights:
        parts.append(box(P(0, -0.25, 1.68), (1.2, 0.3, 0.14), dark, (0, 0, rot)))
        parts.append(box(P(-0.33, -0.25, 1.78), (0.5, 0.28, 0.14), m_emis('lightR%.0f%.0f' % (x, y), (1.0, 0.08, 0.08), 9), (0, 0, rot)))
        parts.append(box(P(0.33, -0.25, 1.78), (0.5, 0.28, 0.14), m_emis('lightB%.0f%.0f' % (x, y), (0.1, 0.3, 1.0), 9), (0, 0, rot)))
        parts.append(bev(box(P(0, 0.0, 0.72), (1.97, 1.7, 0.4), white, (0, 0, rot)), 0.05))
    return parts
def rig(parts, name, center=(0, 0, 0)):
    """parent loose parts under an empty at the vehicle's centre so it can be moved and spun in place"""
    e = bpy.data.objects.new(name, None); sc.collection.objects.link(e); e.location = center; bpy.context.view_layer.update()
    for p in parts:
        mw = p.matrix_world.copy(); p.parent = e; p.matrix_world = mw
    return e

box((0, 200, -0.14), (3000, 3000, 0.1), m_noise('dryGrass', (0.42, 0.42, 0.2), (0.5, 0.48, 0.26), 0.2, 0.95, 0.1))
# Grove-Street-style cul-de-sac (y -30..62): two-lane street, sidewalks, little stucco houses, palms, power lines
ground(-40, 64, -4.5, 4.5, asphalt); ground(-40, 64, 4.5, 8.0, walk); ground(-40, 64, -8.0, -4.5, walk); ground(-40, 64, 8.0, 30, lawn); ground(-40, 64, -30, -8.0, lawn)
for k in range(12): box((0, -36 + k * 8.5, 0.006), (0.14, 3.0, 0.01), yellow)
for side in (1, -1):
    y = -36
    while y < 60:
        d = random.uniform(9, 12); house(side * random.uniform(16, 18), y + d / 2, 8, d - 1.5, random.choice([3.4, 3.8, 6.4]), random.choice(stucco), -side); y += d
    for y in range(-30, 64, 14): palm(side * 9.2, y + random.uniform(-2, 2), random.uniform(8, 11))
    for y in range(-34, 64, 18): cyl((side * 8.6, y, 4.5), 0.13, 9, m_plain('pole', (0.35, 0.25, 0.18), 0.8), v=8); box((side * 8.6, y, 8.6), (1.6, 0.1, 0.1), dark)
for (x, y, col) in [(-3.4, 12, (0.7, 0.15, 0.12)), (-3.4, 54, (0.85, 0.85, 0.82)), (3.4, -6, (0.25, 0.45, 0.7))]:
    rig(car(x, y, 0, col), 'parked%.0f' % y)
# the hero's convertible and the player's bike (animated below)
hero_car = rig(car(CAR0[0], CAR0[1], 0, (0.95, 0.35, 0.12), convertible=True), 'heroCar', (CAR0[0], CAR0[1], 0.8))
bk = m_plain('bike', (0.1, 0.55, 0.85), 0.35)
def bar(a, b, r, m):
    a, b = Vector(a), Vector(b); d = b - a; return cyl(tuple((a + b) / 2), r, d.length, m, d.to_track_quat('Z', 'Y').to_euler(), 8)
bx, by = -3.0, 47.0
bparts = [cyl((bx, by - 0.62, 0.34), 0.34, 0.05, dark, (0, math.pi / 2, 0), 20), cyl((bx, by + 0.62, 0.34), 0.34, 0.05, dark, (0, math.pi / 2, 0), 20),
          cyl((bx, by - 0.62, 0.34), 0.06, 0.07, chrome, (0, math.pi / 2, 0), 10), cyl((bx, by + 0.62, 0.34), 0.06, 0.07, chrome, (0, math.pi / 2, 0), 10),
          bar((bx, by - 0.62, 0.34), (bx, by - 0.1, 0.4), 0.025, bk), bar((bx, by - 0.1, 0.4), (bx, by - 0.22, 0.86), 0.025, bk), bar((bx, by - 0.22, 0.86), (bx, by + 0.45, 0.82), 0.025, bk),
          bar((bx, by - 0.1, 0.4), (bx, by + 0.45, 0.82), 0.028, bk), bar((bx, by + 0.45, 0.82), (bx, by + 0.62, 0.34), 0.022, chrome), bar((bx, by - 0.62, 0.34), (bx, by - 0.22, 0.86), 0.02, bk),
          bar((bx - 0.3, by + 0.4, 1.02), (bx + 0.3, by + 0.4, 1.02), 0.018, dark), bar((bx, by + 0.45, 0.82), (bx, by + 0.4, 1.02), 0.02, chrome),
          box((bx, by - 0.24, 0.92), (0.14, 0.28, 0.06), dark), cyl((bx, by - 0.1, 0.4), 0.09, 0.05, chrome, (0, math.pi / 2, 0), 12)]
bike = rig(bparts, 'bike', (-3.0, 47.0, 0.5))
# palm boulevard (y 62..225): four lanes + median palms, shops, billboards, hills behind
ground(62, 232, -8.0, 8.0, asphalt); ground(62, 232, 8.0, 12.0, walk); ground(62, 232, -12.0, -8.0, walk)
box((0, 147, 0.08), (1.6, 170, 0.16), lawn)
for y in range(66, 226, 12): palm(0, y, random.uniform(10, 13)); [box((sx * 4.0, y - 3, 0.006), (0.14, 3.0, 0.01), white) for sx in (-1, 1)]
for side in (1, -1):
    y = 64
    while y < 228:
        d = random.uniform(10, 16); h = random.choice([6, 8, 10, 14]); x = side * (12 + 8)
        box((x, y + d / 2, h / 2), (16, d - 0.6, h), random.choice(shopw)); box((x - side * 8.02, y + d / 2, 1.6), (0.1, d * 0.75, 2.4), glass)
        box((x - side * 8.7, y + d / 2, 3.1), (1.4, d * 0.8, 0.12), m_plain('awn%.0f' % y, random.choice([(0.8, 0.15, 0.12), (0.12, 0.45, 0.4), (0.95, 0.75, 0.2)]), 0.6), (0, -side * 0.3, 0))
        y += d
    for y in range(70, 226, 16): cyl((side * 8.7, y, 3.5), 0.1, 7, dark, v=8); box((side * 7.9, y, 7.0), (1.6, 0.12, 0.12), dark); box((side * 7.2, y, 6.85), (0.5, 0.3, 0.12), m_emis('streetlamp', (1.0, 0.9, 0.7), 1.5))
    for y in range(70, 226, 22): box((side * 11.7, y, 4.2), (0.25, 5.0, 1.0), m_emis('sign%.0f%d' % (y, side), random.choice([(0.95, 0.3, 0.2), (0.2, 0.7, 0.95), (0.98, 0.8, 0.2), (0.6, 0.3, 0.9)]), 1.2))
    for y in (110, 175): box((side * 13, y, 11), (0.3, 9, 4.5), m_emis('bill%.0f%d' % (y, side), random.choice([(0.9, 0.5, 0.2), (0.3, 0.6, 0.95)]), 0.7, (0.9, 0.9, 0.9))); cyl((side * 13, y, 4.5), 0.25, 9, dark, v=8)
hill = m_noise('hills', (0.42, 0.45, 0.25), (0.55, 0.52, 0.32), 0.05, 0.9, 0.2)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=30, size=1, location=(0, 650, 0)); hl = bpy.context.object; hl.scale = (1400, 500, 1)
for v in hl.data.vertices: v.co.z = (90 + 70 * math.sin(v.co.x * 9) * math.cos(v.co.y * 5)) * min(1, (v.co.y + 0.5) * 2) / 1.0
hl.data.materials.append(hill); bpy.ops.object.shade_smooth()
# stunt ramp and the sunken freeway (y 240..290)
rampm = m_brick('ramp', (0.2, 0.65, 0.25), (0.95, 0.95, 0.9), (0.15, 0.15, 0.15), 1.4, 1.0, 0.5)
L = math.hypot(RAMP1 - RAMP0, LIP_Z); box((3.0, (RAMP0 + RAMP1) / 2, LIP_Z / 2), (5.0, L, 0.3), rampm, (math.atan2(LIP_Z, RAMP1 - RAMP0), 0, 0))
for sx in (-1, 1): box((3.0 + sx * 2.5, (RAMP0 + RAMP1) / 2, LIP_Z / 2 - 0.4), (0.3, L, LIP_Z * 0.6), dark, (math.atan2(LIP_Z, RAMP1 - RAMP0), 0, 0))
concrete = m_noise('concrete', (0.36, 0.35, 0.34), (0.45, 0.44, 0.42), 4, 0.9, 0.1)
ground(232, 240, -60, 60, concrete); ground(290, 300, -60, 60, concrete)
box((0, 265, -8.05), (400, 50, 0.1), asphalt)
for sy in (240, 290): box((0, sy, -4), (400, 0.8, 8), concrete)
for k in range(40): box((-200 + k * 10, 265, -7.99), (3.0, 0.16, 0.01), white)
for k in range(10): rig(car(random.uniform(-80, 80), random.choice([250, 258, 272, 280]), math.pi / 2, random.choice([(0.8, 0.8, 0.8), (0.2, 0.2, 0.25), (0.6, 0.1, 0.1), (0.2, 0.4, 0.7)])), 'fw%d' % k).location.z = -8
# police station plaza (y 300..400)
ground(300, 400, -60, 60, asphalt); ground(345, 352, -24, 24, concrete)
station = m_brick('station', (0.78, 0.76, 0.72), (0.72, 0.7, 0.66), (0.6, 0.58, 0.55), 2.2)
box((0, 372, 6.5), (44, 40, 13), station); box((0, 351.9, 2.0), (6, 0.2, 4), glass); box((0, 351.5, 4.6), (8, 1.4, 0.3), trim)
for x in (-14, -7, 7, 14):
    for z in (3, 7, 10.5): box((x, 351.95, z), (3.0, 0.1, 1.6), glass)
bpy.ops.object.text_add(location=(-6.3, 351.7, 8.6), rotation=(math.pi / 2, 0, 0)); tx = bpy.context.object; tx.data.body = 'POLICE'; tx.data.size = 2.6; tx.data.extrude = 0.12
tx.data.materials.append(m_plain('policeTxt', (0.1, 0.18, 0.45), 0.4))
for k in range(16): box((-30 + k * 4, 342, 0.01), (0.12, 5.0, 0.02), white)
for (x, y) in [(-22, 330), (22, 330), (-22, 312), (22, 312)]: box((x, y, 0.4), (3.0, 3.0, 0.8), concrete); palm(x, y, 9)
for (x, y) in [(-16, 320), (16, 320), (-16, 305), (16, 305)]: cyl((x, y, 3.0), 0.1, 6, dark, v=8); box((x, y, 6.0), (0.6, 0.6, 0.2), m_emis('plazaLamp', (1.0, 0.92, 0.75), 1.2))
cyl((26, 350, 7), 0.08, 14, chrome, v=8); box((26.9, 350, 12.8), (1.8, 0.04, 1.1), m_plain('flag', (0.8, 0.15, 0.15), 0.7))
for k in range(4): box((0, 350.6 - k * 0.45, 0.12 + k * 0.12), (10, 0.45, 0.24), concrete)
for (x, y) in [(-12, 344), (12, 343)]: rig(car(x, y, 0.2 if x < 0 else -0.2, (0.08, 0.08, 0.1), lights=True), 'pcar%d' % x)
cops = [rig(car(0, 0, 0, (0.08, 0.08, 0.1), lights=True), 'chase%d' % i, (0, 0, 0.8)) for i in range(2)]
for k in range(8): palm(random.choice([-1, 1]) * random.uniform(24, 40), random.uniform(305, 345), random.uniform(9, 12))

# ------------------------------------------------------------------ animation ------------------------------
for f in range(NF):
    t = f / FPS
    (x, y, z), hd, rl = car_state(t); hero_car.location = (x, y, z + 0.8); hero_car.rotation_euler = (0, rl, -hd)
    hero_car.keyframe_insert('location', frame=f); hero_car.keyframe_insert('rotation_euler', frame=f)
    (x, y, z), hd, rl = bike_state(t); bike.location = (x, y, z + 0.5); bike.rotation_euler = (0, 0, -hd); bike.keyframe_insert('location', frame=f); bike.keyframe_insert('rotation_euler', frame=f)
    for i, cc in enumerate(cops): (x, y, z), hd = copcar_state(i, t); cc.location = (x, y, z + 0.8); cc.keyframe_insert('location', frame=f)
for ob in [hero_car, bike] + cops:
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

bpy.ops.object.camera_add(location=CAM[0][1]); cam = bpy.context.object; cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24; cam.data.clip_end = 5000; sc.camera = cam
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 6.0
tgt = bpy.data.objects.new('camTarget', None); sc.collection.objects.link(tgt)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'; cam.data.dof.focus_object = tgt
CAM.sort(key=lambda k: k[0])
def cam_at(t):
    p = keyed([(k[0], k[1]) for k in CAM], t, ease); l = keyed([(k[0], k[2]) for k in CAM], t, ease); lens = keyed([(k[0], (k[3],)) for k in CAM], t, ease)[0]; return p, l, lens
for f in range(NF):
    p, l, lens = cam_at(f / FPS); cam.location = p; tgt.location = l; cam.data.lens = lens
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f); cam.data.keyframe_insert('lens', frame=f)
for ob in (cam, tgt, cam.data):
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# camera + actor tracks for the engine
track, actors, vis = [], {k: [] for k in ACTORS}, {k: [] for k in ACTORS}
for f in range(NF):
    sc.frame_set(f); M = cam.matrix_world; t = f / FPS
    track.append(dict(C=[round(v, 4) for v in M.translation], R=[[round(M[r][c], 5) for c in range(3)] for r in range(3)], tanh=round(12.0 / cam.data.lens, 6)))
    for k, fn in ACTORS.items(): p, v = fn(t); actors[k].append([round(c, 3) for c in p]); vis[k].append(v)
json.dump(dict(fps=FPS, frames=NF, track=track, actors=actors, vis=vis, door=[[round(c, 3) for c in car_state(f / FPS)[0]] for f in range(NF)]), open(os.path.join(OUT, 'camera.json'), 'w'))
print('tracks written', NF, flush=True)

sc.frame_start, sc.frame_end = START, END; sc.render.use_persistent_data = True
LIST = [int(v) for v in arg('--list', '').split(',') if v]
if LIST:
    for f in LIST: sc.frame_set(f); sc.render.filepath = os.path.join(OUT, 'f%04d.jpg' % f); bpy.ops.render.render(write_still=True)
    print('list done', flush=True)
elif ONLY >= 0:
    sc.frame_set(ONLY); sc.render.filepath = os.path.join(OUT, 'f%04d.jpg' % ONLY); bpy.ops.render.render(write_still=True); print('frame', ONLY, flush=True)
else:
    sc.render.use_overwrite = False; sc.render.use_placeholder = True; sc.render.filepath = os.path.join(OUT, 'f####'); bpy.ops.render.render(animation=True); print('sequence done', flush=True)
