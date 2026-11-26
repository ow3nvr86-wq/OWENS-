"""MOVIES IN A MINUTE: INTERSTELLAR. One continuous camera move in the bright cel-shaded cartoon style (flat colour
bands, ink outlines), now with a fully 3D cast (tools/toon_people.py) and motion driven by physics:
  * dust grains in Murph's room fall under gravity and air drag, and a sideways pull (the "gravity anomaly") sorts
    them into stripes on the floor (the code);
  * the dust storm is a gravity current: its front advances at U = 0.7 * sqrt(g' H) and its head rolls;
  * the book that falls off the shelf is integrated (slide, tip, free fall with spin, floor contact);
  * Miller's wave is a shallow-water solitary wave (KdV): eta = A sech^2((y - ct) / L), c = sqrt(g (h + A)),
    L = sqrt(4 h^3 / (3 A)); the lander floats on it (buoyancy spring + drag in the water velocity u = c eta / (h + eta))
    and Doyle is swept along by the same water velocity; the lander then lifts off with thrust minus gravity;
  * Cooper falls on Mann's planet as an inverted pendulum (theta'' = 3 g / (2 L) sin theta);
  * at Gargantua the ranger separates from the Endurance (momentum is conserved) and plunges on an orbit integrated in
    a pseudo-Newtonian black-hole potential; the accretion disk turns with Keplerian speed (omega ~ r^-3/2); the
    Endurance ring spins at omega = sqrt(g / r) (1 g);
  * in the tesseract Cooper drifts with constant velocity and spin (no gravity), and pushing the book gives him the
    equal and opposite push;
  * the ark lifts off with a = T/m - g; the station's cylinder spins at omega = sqrt(g / R) for 1 g on its floor.
Scales are compressed so everything fits in a minute (noted in sources.txt). All designs are original.
Run: $BLENDER -b --factory-startup -P tools/interstellar_oneshot.py -- <out> --words <words.json> [--scale 0.5]
     [--spp 6] [--list a,b,c] [--start A --end B] [--tracks-only]"""
import bpy, math, sys, os, json, random, re, importlib.util
import numpy as np
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0]; arg = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
SCALE, SPP = arg('--scale', 0.5), arg('--spp', 6)
WORDS = json.load(open(arg('--words', '')))
FPS = 60; DUR = WORDS['duration'] + 1.2; NF = int(round(DUR * FPS))
START, END = arg('--start', 0), arg('--end', NF - 1)
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
s_ = importlib.util.spec_from_file_location('presets_fn2', os.path.join(HERE, 'presets_fn2.py')); F2 = importlib.util.module_from_spec(s_); s_.loader.exec_module(F2)
ISL = F2.ISL; box, cyl, cone, ball = ISL.box, ISL.cyl, ISL.cone, ISL.ball
import toon_people as TP
os.makedirs(OUT, exist_ok=True); random.seed(11); RNG = np.random.default_rng(11)

# ------------------------------------------------------------------ beats from the voice ---------------------------
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
CUES = [('save', 'save'), ('humanity1', 'humanity'), ('leave', 'leave'), ('daughter1', 'daughter'), ('promised', 'promised'), ('back', 'back'),
        ('earth1', 'earth'), ('dying', 'dying'), ('dust1', 'dust'), ('storms', 'storms'), ('failing', 'failing'), ('crops', 'crops'),
        ('cooper1', 'cooper'), ('farmer', 'farmer'), ('exnasa', 'exnasa'), ('pilot', 'pilot'), ('finds', 'finds'), ('code1', 'code'),
        ('dust2', 'dust'), ('murphs1', 'murphs'), ('room', 'room'), ('calls', 'calls'), ('ghost1', 'ghost'), ('leads', 'leads'),
        ('secret', 'secret'), ('nasa', 'nasa'), ('base', 'base'), ('wormhole', 'wormhole'), ('saturn1', 'saturn'), ('murph2', 'murph'),
        ('begs', 'begs'), ('stay', 'stay'), ('cooper2', 'cooper'), ('watch1', 'watch'), ('goes', 'goes'), ('millers', 'millers'),
        ('planet', 'planet'), ('hour', 'hour'), ('seven', 'seven'), ('years1', 'years'), ('earth2', 'earth'), ('giant', 'giant'),
        ('wave', 'wave'), ('kills', 'kills'), ('doyle', 'doyle'), ('t23', 'twentythree'), ('gone', 'gone'), ('then', 'then'),
        ('mann', 'mann'), ('faked', 'faked'), ('data1', 'data'), ('rescued', 'rescued'), ('tries', 'tries'), ('kill', 'kill'),
        ('cooper3', 'cooper'), ('low', 'low'), ('fuel', 'fuel'), ('cooper4', 'cooper'), ('detaches', 'detaches'), ('falls', 'falls'),
        ('black', 'black'), ('hole', 'hole'), ('gargantua', 'gargantua'), ('brand1', 'brand'), ('make', 'make'), ('inside', 'inside'),
        ('sees', 'sees'), ('murphs2', 'murphs'), ('bedroom', 'bedroom'), ('time', 'time'), ('ghost2', 'ghost'), ('ticks', 'ticks'),
        ('data2', 'data'), ('watch2', 'watch'), ('morse', 'morse'), ('murph3', 'murph'), ('cracks', 'cracks'), ('gravity', 'gravity'),
        ('humanity2', 'humanity'), ('leaves', 'leaves'), ('earth3', 'earth'), ('cooper5', 'cooper'), ('wakes', 'wakes'),
        ('station', 'station'), ('saturn2', 'saturn'), ('murph4', 'murph'), ('old', 'old'), ('sends', 'sends'), ('find', 'find'),
        ('brand2', 'brand'), ('would', 'would'), ('stayed', 'stayed')]
B = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while j < len(ws) and norm(ws[j]['word']) != cue: j += 1
    if j == len(ws): raise SystemExit('cue word not found: ' + cue)
    B[key] = ws[j]['start']; wi = j + 1
B['end'] = DUR
B['space'] = B['goes'] + 0.55          # up out of the sky into space
B['miller0'] = B['millers'] - 0.05      # through the wormhole: Miller's planet
B['hit'] = B['doyle'] - 0.1             # the wave crest reaches the lander
B['lift'] = B['t23'] + 0.35             # the lander lifts off
B['mann0'] = B['then'] - 0.05
B['shove'] = B['tries'] + 0.12
B['garg0'] = B['low'] - 0.08
B['sep'] = B['detaches'] + 0.1
B['tes0'] = B['inside'] - 0.02
B['push'] = B['ghost2'] - 0.35
B['watch0'] = B['ticks'] - 0.2
B['ark0'] = B['murph3'] - 0.3           # the ark's engines light
B['sta0'] = B['cooper5'] - 0.12
B['room0'] = B['murph4'] - 0.55
b = B
print('beats', json.dumps({k: round(v, 2) for k, v in B.items()}), flush=True)


def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def clamp(u, a=0.0, c=1.0): return min(c, max(a, u))
def lerp(a, c, u): return a + (c - a) * u
def lerp3(a, c, u): return tuple(x + (y - x) * u for x, y in zip(a, c))
def F(t): return int(round(t * FPS))
def add(a, c): return tuple(x + y for x, y in zip(a, c))
FR = np.arange(NF) / FPS

# ------------------------------------------------------------------ layout (metres) ---------------------------------
# A  the farm at the origin (house x -6..6, y 6..14, Murph's room upstairs: x -6..0, y 6..11, z 3.2..6.2)
# C  the secret NASA base, a hangar dug into a hill at x = 400
# S  space above everything (z = 6000): Saturn, the wormhole, the station; G = Gargantua; T = the tesseract
# M  Miller's planet (y = +5000), N  Mann's planet (y = -5000), I  inside the station cylinder (x = 8000)
RZ = 3.2                                   # upstairs floor
BASE = Vector((400.0, 0.0, 0.0)); S = Vector((0.0, 0.0, 6000.0)); G = Vector((3000.0, 0.0, 6000.0)); T = Vector((-3000.0, 0.0, 6000.0))
M = Vector((0.0, 5000.0, 0.0)); N = Vector((0.0, -5000.0, 0.0)); I = Vector((8000.0, 0.0, 0.0))
WH = S + Vector((0.0, 320.0, 10.0)); WHR = 30.0
SAT = S + Vector((170.0, 980.0, -160.0)); SATR = 230.0
STA = S + Vector((-90.0, 560.0, 30.0)); STAR = 60.0

# ================================================================== PHYSICS (numpy, before the scene) =================
g0 = 9.81
# ---- dust grains through Murph's window: gravity, drag toward the room air, and the anomaly's sideways pull ---------
BITS = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1]            # stripe present (1) or gap (0): the binary code on the floor
STRIPE_X = [-5.1 + i * 0.36 for i in range(len(BITS))]
ND = 3600; D_T0, D_T1 = b['finds'] - 0.3, b['murphs1'] + 0.6
dust_p = np.zeros((NF, ND, 3), np.float32); dust_p[:] = (0, 0, -500)
p = np.stack([RNG.uniform(-4.1, -1.9, ND), RNG.uniform(5.7, 6.1, ND), RNG.uniform(4.1, 5.4, ND)], 1)
v = np.stack([RNG.normal(0, 0.15, ND), RNG.uniform(1.4, 2.6, ND), RNG.normal(0, 0.1, ND)], 1)
born = D_T0 + RNG.uniform(0, 1.4, ND); target = np.array([STRIPE_X[i] for i in RNG.choice([k for k, bt in enumerate(BITS) if bt], ND)]) + RNG.normal(0, 0.035, ND)
settled = np.zeros(ND, bool); dt = 1 / 240; k_drag = 3.0; vt = 0.25       # terminal speed of a fine grain ~ g / k
t = D_T0
for f in range(F(D_T0), NF):
    while t < f / FPS:
        live = (t >= born) & ~settled
        if live.any():
            a = np.zeros((live.sum(), 3)); vv = v[live]
            a[:, 2] -= g0 * 0.6                                  # weight minus buoyancy of a light grain
            a -= k_drag * vv                                     # drag toward still air
            a[:, 0] += 6.0 * (target[live] - p[live, 0]) * (p[live, 2] < RZ + 1.6)   # the anomaly sorts them sideways
            v[live] += a * dt; p[live] += v[live] * dt
            hit = live & (p[:, 2] <= RZ + 0.012); p[hit, 2] = RZ + 0.012; v[hit] = 0; settled |= hit
        t += dt
    q = p.copy(); q[t < born] = (0, 0, -500); dust_p[f] = q
print('dust settled', int(settled.sum()), 'of', ND, flush=True)

# ---- the book that falls (the "ghost"), twice: once in the room, once pushed in the tesseract -----------------------
def book_fall(t0, p0, push_v, floor_z, wall_dir=1.0):
    """slides off the shelf edge with speed push_v (along +x), tips and falls with spin; returns per-frame (pos, rotY)"""
    out = {}; x, z, vx, vz, ang, w = p0[0], p0[2], push_v, 0.0, 0.0, 0.0; edge = p0[0] + 0.12; dt = 1 / 600; t = t0; f = F(t0)
    on_shelf = True; done = False
    while f < NF:
        while t < f / FPS:
            if on_shelf:
                x += vx * dt; vx *= (1 - 1.5 * dt)
                if x > edge: on_shelf = False; w = 4.0 * wall_dir * vx / 0.12      # tipping over the edge gives it spin
            elif not done:
                vz -= g0 * dt; x += vx * dt; z += vz * dt; ang += w * dt
                if z <= floor_z + 0.03:
                    z = floor_z + 0.03; vz = -0.25 * vz; vx *= 0.4; w *= 0.3
                    if abs(vz) < 0.3: done = True; ang = round(ang / (math.pi / 2)) * (math.pi / 2)
            t += dt
        out[f] = ((x, p0[1], z), ang); f += 1
    return out
BOOK1 = book_fall(b['ghost1'] - 0.1, (-5.63, 8.06, RZ + 1.15), 1.1, RZ)
TB_OFF = Vector((-3.0, 8.5, RZ))           # room-local origin used by the tesseract copies

# ---- Miller's wave (KdV solitary wave) and what floats on it -------------------------------------------------------
gM = 1.3 * g0; hW, AW = 28.0, 21.0; cW = math.sqrt(gM * (hW + AW)); LW = math.sqrt(4 * hW ** 3 / (3 * AW))
def eta(y, t): return AW / np.cosh((y - cW * (b['hit'] - t)) / LW) ** 2               # crest moves toward -y
def uW(y, t): e = eta(y, t); return -cW * e / (hW + e)                                  # water velocity (toward -y)
print('wave: c = %.1f m/s, L = %.0f m' % (cW, LW), flush=True)
def float_on(t0, t1, y0, k_s, damp, drag, z_off, thrust=None):
    """a floating body: spring to the surface (buoyancy), damping, drag toward the water velocity; thrust(t) -> a_z"""
    dt = 1 / 600; t = t0; y, z, vy, vz = y0, z_off, 0.0, 0.0; out = {}; f = F(t0)
    while f <= F(t1):
        while t < f / FPS:
            e = float(eta(y, t)); u = float(uW(y, t)); az = -gM if thrust and thrust(t) else 0.0
            if thrust and thrust(t): az += thrust(t); vy += -0.6 * vy * dt
            else: az = k_s * (e + z_off - z) - damp * vz; vy += drag * (u - vy) * dt
            vz += az * dt; z += vz * dt; y += vy * dt; t += dt
        sl = float((eta(y + 2, t) - eta(y - 2, t)) / 4.0); out[f] = (y, z, math.atan(sl)); f += 1
    return out
LANDER = float_on(b['miller0'] - 0.1, DUR, 0.0, 14.0, 5.0, 0.9, -0.6, thrust=lambda t: 2.1 * gM if t > b['lift'] else 0.0)
DOYLE = float_on(b['miller0'] - 0.1, b['lift'] + 1.0, 7.0, 30.0, 8.0, 4.0, -0.25)

# ---- Gargantua: the ranger's plunge (pseudo-Newtonian potential), Endurance recoil -------------------------------
RS = 40.0                                          # event horizon radius of the model hole
E0 = Vector((-210.0, -150.0, 26.0)); E_V = Vector((14.0, -2.0, 0.0))      # Endurance near the hole, coasting
m_L, m_E, dv_sep = 1.0, 6.0, 6.0
def plunge(GM, t_end=8.0):
    pL = np.array(E0 + Vector((0, 7.0, -1.0))); r = np.linalg.norm(pL); rh = -pL / r
    tang = np.cross(np.array([0, 0, 1.0]), rh); tang /= np.linalg.norm(tang)
    vc = math.sqrt(GM * r) / (r - RS)
    vL = np.array(E_V) + rh * dv_sep * m_E / (m_L + m_E) + tang * 0.42 * vc
    dt = 1 / 600; t = 0.0; pts = [(0.0, pL.copy())]
    while t < t_end:
        r = np.linalg.norm(pL)
        if r < RS * 1.02: break
        a = -GM / (r - RS) ** 2 * pL / r; vL = vL + a * dt; pL = pL + vL * dt; t += dt
        if int(t * 600) % 10 == 0: pts.append((t, pL.copy()))
    return t, pts
lo, hi = 1e5, 1e8; want = (b['make'] + 0.25) - b['sep']
for _ in range(40):                                # choose the hole's mass so the plunge takes the narrated time
    mid = math.sqrt(lo * hi); tt, _p = plunge(mid)
    if tt > want: lo = mid
    else: hi = mid
GMh = math.sqrt(lo * hi); T_PL, PL_PTS = plunge(GMh)
print('gargantua GM %.3g, plunge %.2f s' % (GMh, T_PL), flush=True)
PLt = np.array([q[0] for q in PL_PTS]); PLp = np.array([q[1] for q in PL_PTS])
def ranger_at(t):
    if t < b['sep']: return tuple(G + E0 + E_V * (t - b['garg0']) + Vector((0, 7.0, -1.0)))
    u = t - b['sep']
    if u >= PLt[-1]: return tuple(G + Vector(PLp[-1]))
    return tuple(G + Vector([np.interp(u, PLt, PLp[:, i]) for i in range(3)]) + E_V * (b['sep'] - b['garg0']))
def endurance_at(t):
    p_ = E0 + E_V * (t - b['garg0'])
    if t > b['sep']: p_ = p_ + (Vector((0, -1.0, 0.2)) * dv_sep * m_L / (m_L + m_E)) * (t - b['sep'])       # recoil
    if t > b['brand1']: p_ = p_ + Vector((1.0, 0.15, 0.05)) * 0.5 * 9.0 * (t - b['brand1']) ** 2              # burn away
    return tuple(G + p_)

# ---- Mann's shove: Cooper falls as an inverted pendulum about his heels ----------------------------------------------
def pendulum(t0, th0, w0, L=1.8, g=g0):
    out = {}; th, w = th0, w0; dt = 1 / 600; t = t0; f = F(t0)
    while f < NF:
        while t < f / FPS:
            if th < math.pi / 2: w += 1.5 * g / L * math.sin(th) * dt; th += w * dt
            if th >= math.pi / 2: th = math.pi / 2 - 0.02 * math.exp(-(t - t0)); w = 0
            t += dt
        out[f] = th; f += 1
    return out
FALL = pendulum(b['shove'], 0.06, 1.2)

# ---- the ark: thrust minus gravity -----------------------------------------------------------------------------------
ARK_A = (1.6 - 1.0) * g0
def ark_z(t): u = max(0.0, t - b['ark0']); return 0.5 * ARK_A * u * u

# ------------------------------------------------------------------ the camera (t, position, look-at, lens) --------
A_ = lambda *v: tuple(v)
def LPOS(t): y, z, _ = LANDER.get(F(t), (0.0, -0.6, 0.0)); return M + Vector((0.0, y, z + 0.6))
def LK(t, off, look, lens=20): L_ = LPOS(t); return (t, tuple(L_ + Vector(off)), tuple(L_ + Vector(look)), lens)
def r_(base, x, y, z): return tuple(base + Vector((x, y, z)))
SEG_A = [
    (0.0, (0.55, -1.4, 1.05), (0.45, 2.7, 0.9), 32),                         # the porch: father and daughter
    (b['daughter1'], (0.5, -2.2, 1.2), (1.0, 2.6, 1.0), 30),
    (b['promised'], (-0.5, -5.6, 1.9), (3.4, 0.6, 1.2), 26),
    (b['back'], (-2.0, -8.4, 3.0), (5.4, 0.0, 1.4), 24),
    (b['dying'], (-5.0, -14.0, 9.0), (20.0, 20.0, 8.0), 22),                 # up: the dusty farm
    (b['storms'] + 0.2, (2.0, -16.0, 14.0), (120.0, 30.0, 40.0), 20),       # the dust storm rolling in
    (b['crops'], (16.0, -9.0, 3.2), (30.0, 14.0, 0.6), 22),                 # down over the dead corn
    (b['cooper1'] + 0.1, (14.6, -7.6, 2.0), (11.2, -1.4, 1.35), 26),         # Cooper by the truck
    (b['pilot'], (13.6, -5.8, 1.9), (11.5, -1.3, 1.45), 30),
    (b['finds'] + 0.15, (-3.0, -2.0, 5.0), (-3.0, 8.0, 4.5), 24),           # to Murph's window
    (b['code1'] + 0.15, (-3.0, 5.6, 4.8), (-3.0, 10.0, 3.9), 22),           # through it
    (b['dust2'] + 0.2, (-0.7, 10.2, 5.5), (-3.0, 7.6, 3.3), 20),            # dust settling in stripes
    (b['room'], (-0.8, 10.0, 5.3), (-3.1, 7.6, 3.3), 21),
    (b['calls'], (-1.8, 6.9, 4.7), (-5.5, 8.2, 4.3), 22),                   # the bookshelf: "a ghost"
    (b['ghost1'] + 0.5, (-2.0, 6.9, 4.5), (-5.4, 8.2, 3.8), 22),
    (b['leads'] - 0.05, (-3.0, 5.4, 4.8), (-3.0, -4.0, 4.0), 22),            # back out of the window
    (b['secret'], (60.0, -40.0, 40.0), (400.0, 20.0, 10.0), 22),             # off to the hill
    (b['nasa'] + 0.05, (400.0, -45.0, 12.0), (400.0, 20.0, 10.0), 22),
    (b['base'] + 0.2, (400.0, 0.0, 6.0), (400.0, 26.0, 13.0), 20),          # inside the hangar: the rocket
    (b['wormhole'] - 0.1, (401.2, 5.4, 2.7), (400.0, 12.0, 1.7), 26),       # the holo model
    (b['saturn1'] + 0.2, (400.5, 9.3, 2.15), (400.0, 12.0, 1.95), 32),
    (b['murph2'] - 0.097, (400.4, 10.2, 2.05), (400.0, 12.0, 1.95), 34),
    (b['murph2'] - 0.08, (-1.2, 7.0, 4.7), (-3.9, 9.3, 3.9), 24),           # (flash) back in Murph's room
    (b['stay'] + 0.2, (-1.3, 7.2, 4.6), (-3.9, 9.3, 3.9), 26),
    (b['watch1'] + 0.1, (-1.5, 7.3, 4.5), (-3.6, 9.0, 3.9), 28),
    (b['goes'] + 0.15, (-2.6, 6.4, 4.8), (-0.4, 9.6, 4.0), 24),
    (b['space'] - 0.25, (-3.0, 3.0, 9.0), (-3.0, 20.0, 400.0), 22),          # up into the sky
    (b['space'] - 0.017, (-3.0, 3.0, 400.0), (-3.0, 20.0, 1400.0), 20),
    (b['space'], r_(S, 6.0, 140.0, 4.0), tuple(WH), 22),                      # space: the Endurance at the wormhole
    (b['miller0'] - 0.10, r_(S, 0.0, 262.0, 8.0), tuple(WH), 24),
    (b['miller0'] - 0.017, r_(S, 0.0, 286.0, 9.0), tuple(WH), 26),
    (b['miller0'], r_(M, -6.0, -24.0, 5.0), r_(M, 6.0, 120.0, 24.0), 20),    # (flash) Miller's planet
    (b['hour'], r_(M, 2.5, -9.5, 2.3), r_(M, 0.4, 3.0, 1.6), 26),
    (b['years1'], r_(M, 1.5, -7.5, 2.0), r_(M, 0.6, 3.0, 1.5), 28),
    (b['earth2'], r_(M, -3.0, -12.0, 3.0), r_(M, 0.0, 70.0, 16.0), 22),     # the "mountains" are a wave
    (b['giant'] + 0.2, r_(M, -1.0, -17.0, 4.0), r_(M, 0.0, 45.0, 30.0), 18),
    (b['kills'], r_(M, 10.0, -15.0, 5.0), r_(M, 3.0, 8.0, 8.0), 20),
    LK(b['hit'] - 0.1, (16.0, -22.0, 6.0), (0.0, 4.0, 1.0)), LK(b['hit'] + 0.5, (18.0, -26.0, 8.0), (0.0, 0.0, 0.0)),
    LK(b['lift'], (18.0, -28.0, 6.0), (0.0, 0.0, 2.0)), LK(b['lift'] + 0.7, (16.0, -30.0, 0.0), (0.0, 0.0, 4.0)),
    LK(b['mann0'] - 0.017, (14.0, -30.0, -4.0), (0.0, 0.0, 6.0)),
    (b['mann0'], r_(N, -10.0, -26.0, 14.0), r_(N, 0.0, 10.0, 6.0), 20),     # (flash) Mann's ice planet
    (b['mann'] + 0.1, r_(N, -3.0, -6.4, 2.1), r_(N, -0.9, 0.0, 1.5), 28),
    (b['faked'] + 0.1, r_(N, -1.6, -2.7, 1.85), r_(N, -0.7, 0.0, 1.3), 32),
    (b['rescued'], r_(N, -1.4, -2.6, 1.8), r_(N, -0.6, 0.0, 1.3), 34),
    (b['tries'], r_(N, 0.2, -6.4, 2.0), r_(N, 0.2, 0.0, 1.1), 26),
    (b['cooper3'] + 0.3, r_(N, 1.6, -5.2, 1.6), r_(N, 1.4, 0.0, 0.6), 26),
    (b['garg0'] - 0.017, r_(N, 2.0, -5.0, 1.6), r_(N, 1.6, 0.0, 0.5), 26),
    (b['garg0'], r_(G, -250.0, -205.0, 52.0), r_(G, -40.0, 10.0, 0.0), 18),  # (flash) Gargantua
    (b['cooper4'], r_(G, -216.0, -176.0, 36.0), r_(G, -150.0, -100.0, 20.0), 24),
]
def chase(t, back=16.0, up=5.0, lens=22):           # a key behind the ranger, looking past it at the hole
    p_ = Vector(ranger_at(t)); d = (G - p_).normalized(); side = d.cross(Vector((0, 0, 1))).normalized()
    return (t, tuple(p_ - d * back + Vector((0, 0, up)) - side * 4.0), tuple(G * 0.5 + p_ * 0.5), lens)
SEG_A += [chase(b['sep'] + 0.35, 18.0, 6.0, 24), chase(b['falls'] + 0.2, 22.0, 6.0, 22), chase(b['hole'], 24.0, 7.0, 20),
          chase(b['brand1'] - 0.1, 22.0, 6.0, 20), chase(b['make'], 16.0, 4.0, 22)]
SEG_A += [
    (b['tes0'] - 0.017, tuple(G + (Vector(ranger_at(b['make'])) - G) * 0.6), tuple(G), 26),   # into the black
    (b['tes0'], r_(T, -34.0, -26.0, 12.0), r_(T, 0.0, 10.0, 0.0), 18),     # (flash) the tesseract
    (b['murphs2'], r_(T, -14.0, -11.0, 4.0), r_(T, -3.0, 1.0, 1.0), 20),
    (b['time'] - 0.2, r_(T, -8.6, -3.6, 2.4), r_(T, -3.6, -0.2, 1.3), 24),
    (b['ghost2'] - 0.2, r_(T, -7.2, -1.6, 2.1), r_(T, -3.2, 0.0, 1.2), 27),
    (b['push'] + 0.7, r_(T, -6.6, -1.2, 2.0), r_(T, -2.4, 0.2, 0.6), 27),
    (b['watch0'] - 0.017, r_(T, -6.4, -1.1, 2.0), r_(T, -2.2, 0.2, 0.5), 27),
    (b['watch0'], (-4.65, 8.08, 4.76), (-5.62, 8.06, 4.37), 42),                # (flash) the watch on the shelf
    (b['morse'] - 0.1, (-4.75, 8.07, 4.72), (-5.62, 8.06, 4.37), 48),
    (b['murph3'] - 0.1, (-2.6, 6.7, 4.7), (-4.8, 7.9, 4.3), 26),             # Murph has it
    (b['gravity'], (-2.0, 6.5, 4.8), (-4.6, 7.9, 4.4), 24),
    (b['humanity2'], (-3.0, 5.4, 5.0), (-3.0, -4.0, 6.0), 22),              # out of the window: the ark rises
    (b['leaves'] + 0.2, (-10.0, -24.0, 14.0), (140.0, 120.0, 60.0), 20),
    (b['sta0'] - 0.017, (-12.0, -30.0, 18.0), (140.0, 120.0, 110.0), 20),
    (b['sta0'], r_(STA, -160.0, -230.0, 40.0), tuple(STA), 22),              # (flash) the station by Saturn
    (b['station'] + 0.1, r_(STA, -120.0, -170.0, 30.0), tuple(STA + Vector((0, 120, -40))), 22),
    (b['saturn2'] + 0.3, r_(STA, -100.0, -150.0, 26.0), tuple(SAT * 0.4 + STA * 0.6), 20),
    (b['room0'] - 0.017, r_(STA, -90.0, -140.0, 25.0), tuple(SAT * 0.4 + STA * 0.6), 20),
    (b['room0'], r_(I, 0.4, -5.6, 2.0), r_(I, -0.3, 2.8, 1.0), 24),        # (flash) inside: old Murph
    (b['old'], r_(I, -0.6, -1.4, 1.75), r_(I, -0.9, 3.2, 0.95), 30),
    (b['sends'] + 0.2, r_(I, 0.4, -2.6, 1.8), r_(I, 0.0, 3.0, 1.1), 26),
    (b['brand2'] + 0.3, r_(I, 0.2, -6.0, 2.6), r_(I, 0.0, 4.0, 3.0), 22),
    (b['would'] + 0.6, r_(I, -8.0, -14.0, 9.0), r_(I, 30.0, 0.0, 28.0), 20),  # back: the world curving up all round
    (DUR, r_(I, -60.0, -6.0, 50.0), r_(I, 120.0, 0.0, 60.0), 16),
]
SEG_A.sort(key=lambda k: k[0])
assert all(a[0] < c[0] for a, c in zip(SEG_A, SEG_A[1:])), 'camera keys out of order'
FLASH_T = [b['murph2'] - 0.1, b['space'] - 0.01, b['miller0'] - 0.04, b['mann0'] - 0.03, b['garg0'] - 0.03, b['tes0'] - 0.03,
           b['watch0'] - 0.03, b['sta0'] - 0.03, b['room0'] - 0.03]

def spline(keys, t):
    T_ = [k[0] for k in keys]
    if t <= T_[0]: return Vector(keys[0][1]), Vector(keys[0][2]), keys[0][3]
    if t >= T_[-1]: return Vector(keys[-1][1]), Vector(keys[-1][2]), keys[-1][3]
    i = max(j for j in range(len(T_) - 1) if T_[j] <= t); h = T_[i + 1] - T_[i]; s = (t - T_[i]) / h
    h00 = 2 * s ** 3 - 3 * s ** 2 + 1; h10 = s ** 3 - 2 * s ** 2 + s; h01 = -2 * s ** 3 + 3 * s ** 2; h11 = s ** 3 - s ** 2
    jump = lambda j: any(abs(T_[j] - ft) < 0.12 for ft in FLASH_T)           # no overshoot across a flash cut
    def slope(vals, j):
        if j == 0 or j == len(T_) - 1 or jump(j) or (j + 1 < len(T_) and T_[j + 1] - T_[j] < 0.1) or (T_[j] - T_[j - 1] < 0.1): return 0.0
        d0 = (vals[j] - vals[j - 1]) / (T_[j] - T_[j - 1]); d1 = (vals[j + 1] - vals[j]) / (T_[j + 1] - T_[j])
        if d0 * d1 <= 0: return 0.0
        w0 = 2 * (T_[j + 1] - T_[j]) + (T_[j] - T_[j - 1]); w1 = (T_[j + 1] - T_[j]) + 2 * (T_[j] - T_[j - 1])
        return (w0 + w1) / (w0 / d0 + w1 / d1)
    def comp1(vals): return vals[i] * h00 + slope(vals, i) * h * h10 + vals[i + 1] * h01 + slope(vals, i + 1) * h * h11
    def comp(idx):
        if idx == 3: return comp1([k[3] for k in keys])
        return Vector([comp1([k[idx][c] for k in keys]) for c in range(3)])
    return comp(1), comp(2), comp(3)
def cam_at(t): return spline(SEG_A, t)

# ================================================================== SCENE =============================================
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
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True; sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.004, 0.004, 0.012, 1)

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
        elif pattern == 'zbands':                       # contour bands by height (shows the shape of a swell)
            zp = n.new('ShaderNodeSeparateXYZ'); Lk(geo.outputs['Position'], zp.inputs[0])
            f_ = math_('FRACT', math_('MULTIPLY', zp.outputs['Z'], None, vc=scale))
            col_sock = mixc(math_('MULTIPLY', math_('GREATER_THAN', f_, None, vc=0.5), math_('GREATER_THAN', zp.outputs['Z'], None, vc=0.6)), base, c2)
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

TP.setup(toon, flat)
_MC = {}
def T_(c, **k):
    key = (c, tuple(sorted(k.items())))
    if key not in _MC: _MC[key] = toon('m' + c.lstrip('#') + str(len(_MC)), c, **k)
    return _MC[key]
def FL(c, s=1.0):
    key = ('fl', c, s)
    if key not in _MC: _MC[key] = flat('f' + c.lstrip('#') + str(len(_MC)), c, s)
    return _MC[key]
def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
def move(objs, c):
    for o in objs:
        for c_ in list(o.users_collection): c_.objects.unlink(o)
        c.objects.link(o)
def mark(): return set(bpy.data.objects)
def since(m0): return [o for o in bpy.data.objects if o not in m0]
def hold(o, f0, f1):                                  # visible only from frame f0 to f1
    o.hide_render = True; o.keyframe_insert('hide_render', frame=0)
    if f0 > 0: o.keyframe_insert('hide_render', frame=f0 - 1)
    o.hide_render = False; o.keyframe_insert('hide_render', frame=f0); o.keyframe_insert('hide_render', frame=f1)
    o.hide_render = True; o.keyframe_insert('hide_render', frame=f1 + 1)
def dome(center, R, bottom, top, mid=None, name='skyDome'):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R, location=center, segments=48, ring_count=24); o = bpy.context.object; o.name = name
    for pl in o.data.polygons: pl.use_smooth = True
    o.data.materials.append(skygrad(name + 'M', center.z - R * 0.15, center.z + R * 0.7, bottom, top, mid)); return o
def disc(center, R, m, name='ground', z=0.0):
    bpy.ops.mesh.primitive_circle_add(radius=R, vertices=64, fill_type='NGON', location=(center.x, center.y, z)); o = bpy.context.object; o.name = name
    o.data.materials.append(m); return o
def scatter(name, pts, src, scales=None, rot=(0.0, 0.0, 6.283), c=None):
    """instances of the object `src` on points (geometry nodes); optional per-point scale"""
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(p_) for p_ in pts], [], [])
    if scales is not None: at = me.attributes.new('sc', 'FLOAT', 'POINT'); at.data.foreach_set('value', [float(s) for s in scales])
    ob = bpy.data.objects.new(name, me); (c or sc.collection).objects.link(ob)
    ng = bpy.data.node_groups.new(name + 'GN', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry'); ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n = ng.nodes; L = ng.links.new; gi = n.new('NodeGroupInput'); go = n.new('NodeGroupOutput')
    iop = n.new('GeometryNodeInstanceOnPoints'); oi = n.new('GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = src
    L(gi.outputs[0], iop.inputs['Points']); L(oi.outputs['Geometry'], iop.inputs['Instance'])
    rv = n.new('FunctionNodeRandomValue'); rv.data_type = 'FLOAT_VECTOR'; rv.inputs[0].default_value = (0, 0, 0); rv.inputs[1].default_value = rot
    L(rv.outputs[0], iop.inputs['Rotation'])
    if scales is not None:
        na = n.new('GeometryNodeInputNamedAttribute'); na.data_type = 'FLOAT'; na.inputs['Name'].default_value = 'sc'; L(na.outputs['Attribute'], iop.inputs['Scale'])
    L(iop.outputs['Instances'], go.inputs[0]); md = ob.modifiers.new('gn', 'NODES'); md.node_group = ng
    src.hide_render = True; src.hide_viewport = True
    return ob
def annulus(name, center, r0, r1, m, n=96):
    me = bpy.data.meshes.new(name); vs = []; fs = []
    for i in range(n):
        a = 2 * math.pi * i / n; vs += [(r0 * math.cos(a), r0 * math.sin(a), 0), (r1 * math.cos(a), r1 * math.sin(a), 0)]
    for i in range(n):
        j = (i + 1) % n; fs.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
    me.from_pydata(vs, [], fs); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = tuple(center); me.materials.append(m); return o
def setpts(me, co):                                    # replace a point cloud's points (count may change)
    co = np.asarray(co, np.float32).reshape(-1, 3)
    if len(me.vertices) != len(co): me.clear_geometry(); me.vertices.add(len(co))
    if len(co): me.vertices.foreach_set('co', co.ravel())
    me.update()
def src_ball(name, m, sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1.0, location=(0, 0, -2000)); o = bpy.context.object; o.name = name; o.data.materials.append(m)
    for pl in o.data.polygons: pl.use_smooth = True
    o.location = (0, 0, 0); return o
def nomb(o):
    try: o.cycles.use_motion_blur = False
    except Exception: pass
UPD = []                                               # per-frame updaters (handler-driven meshes)
def on_frame(scene, depsgraph=None):
    f = scene.frame_current
    for fn in UPD: fn(f)
bpy.app.handlers.frame_change_pre.append(on_frame)

INK_SKIP = []                                          # objects with no outlines (skies, water, glow)
PEOPLE = coll('people'); TRACKS = {}; TRK_H = {}

# ================================================================== A: THE FARM ======================================
m0 = mark()
dome(Vector((0, 0, 0)), 1500, '#f6c98a', '#7fa6cc', '#e8b67a', 'skyFarm'); INK_SKIP.append(bpy.context.object)
INK_SKIP.append(disc(Vector((0, 0, 0)), 1400, T_('#d9b27c'), 'groundFarm'))
WALL = T_('#f4eee0'); TRIM = T_('#8a5a3a'); ROOFM = T_('#7a6e7e'); WALLP = T_('#f6dfa8', pattern='stripes', col2='#f2d08a', scale=2.2)
FLOOR = T_('#c88c56', pattern='stripes', col2='#b87c48', scale=1.6); BLUEWIN = T_('#4a6a9a')
def slab(x0, x1, y0, y1, z0, z1, m, name='slab'):
    o = box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), m); o.name = name; return o
def solid(x0, x1, y0, y1, z0, z1, m, name='solid'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)); o = bpy.context.object
    o.scale = (x1 - x0, y1 - y0, z1 - z0); bpy.ops.object.transform_apply(scale=True); o.name = name; o.data.materials.append(m); return o
def cutbox(o, x0, x1, y0, y1, z0, z1):
    c_ = solid(x0, x1, y0, y1, z0, z1, FL('#ff0000'), 'cutter'); md = o.modifiers.new('cut', 'BOOLEAN'); md.object = c_; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier='cut'); bpy.data.objects.remove(c_)
# the house shell (front wall with the upstairs window open), floors, porch, gable roof
fw = solid(-6.0, 6.0, 5.8, 6.0, 0.0, 6.2, WALL, 'houseFront'); cutbox(fw, -4.2, -1.8, 5.7, 6.1, 4.0, 5.5)
slab(-4.3, -1.7, 5.72, 5.82, 3.9, 4.0, TRIM); slab(-4.3, -1.7, 5.72, 5.82, 5.5, 5.6, TRIM)
slab(-6.0, 6.0, 13.8, 14.0, 0.0, 6.2, WALL, 'houseBack'); slab(-6.0, -5.8, 6.0, 13.8, 0.0, 6.2, WALL, 'houseSideL'); slab(5.8, 6.0, 6.0, 13.8, 0.0, 6.2, WALL, 'houseSideR')
slab(-5.8, 5.8, 6.0, 13.8, RZ - 0.2, RZ, FLOOR, 'upFloor'); slab(-6.0, 6.0, 5.8, 14.0, 6.2, 6.35, WALL, 'attic')
for x in (-4.8, 2.2, 4.4): slab(x - 0.6, x + 0.6, 5.75, 5.79, 1.0, 2.4, BLUEWIN)
slab(2.4, 4.0, 5.75, 5.79, 4.0, 5.4, BLUEWIN); slab(-0.2, 1.1, 5.74, 5.79, 0.0, 2.3, TRIM)            # door
for sgn in (-1, 1):                                       # gable roof
    r_o = box((0.0, 9.9 + sgn * 2.1, 7.25), (12.8, 4.6, 0.2), ROOFM, rot=(sgn * 0.47, 0, 0))
slab(-6.0, 6.0, 9.85, 9.95, 6.35, 8.2, WALL, 'gableFill')
slab(-6.0, 6.0, 3.4, 5.8, 0.0, 0.35, T_('#b88a5e'), 'porch'); slab(-6.0, 6.0, 3.4, 5.8, 2.9, 3.05, ROOFM, 'porchRoof')
for x in (-5.7, -2.0, 2.0, 5.7): cyl((x, 3.6, 1.6), 0.09, 2.6, WALL)
for x in (-1.0, 0.0, 1.0): slab(x - 0.45, x + 0.45, 2.9 + x * 0, 3.4, 0.0, 0.18, T_('#a8784e'))
# the pickup truck (original design)
TRK = T_('#5a8a9a'); slab(6.0, 10.2, -3.0, -1.2, 0.55, 1.35, TRK); slab(6.0, 7.9, -2.95, -1.25, 1.35, 2.2, TRK); slab(6.1, 7.8, -2.97, -1.23, 1.5, 2.05, BLUEWIN)
for (x, y) in ((6.8, -3.0), (9.3, -3.0), (6.8, -1.2), (9.3, -1.2)): cyl((x, y, 0.45), 0.45, 0.3, T_('#2a2a30'), rot=(math.pi / 2, 0, 0))
ball((7.0, -2.0, 2.28), 0.2, T_('#f2f2ee'), scale=(1, 1, 0.8))                                       # an old flight helmet on the cab
# barn and silo
slab(-26, -14, 18, 30, 0, 7, T_('#c0503a')); [box((-20, 24 + s_ * 3.2, 8.6), (12.4, 7.0, 0.25), ROOFM, rot=(s_ * 0.55, 0, 0)) for s_ in (-1, 1)]
cyl((-30, 34, 6), 2.6, 12, T_('#b8bcc4')); ball((-30, 34, 12), 2.6, T_('#9aa0aa'))
# the corn: alive near the house, blighted further out (instanced)
bpy.ops.mesh.primitive_cone_add(radius1=0.22, depth=2.2, vertices=6, location=(0, 0, 1.1)); stalk = bpy.context.object; stalk.name = 'stalkSrc'
stalk.data.materials.append(T_('#a8b84a')); bpy.ops.object.transform_apply(location=True)
bpy.ops.mesh.primitive_cone_add(radius1=0.22, depth=1.6, vertices=6, location=(0, 0, 0.8), rotation=(0.35, 0.2, 0)); dead = bpy.context.object; dead.name = 'deadSrc'
dead.data.materials.append(T_('#9a7a4a')); bpy.ops.object.transform_apply(location=True, rotation=True)
alive, blight = [], []
for i in range(46):
    for j in range(34):
        x, y = 12.0 + i * 1.6 + random.uniform(-0.3, 0.3), -16.0 + j * 1.5 + random.uniform(-0.3, 0.3)
        if x < 14 and y < 2: continue
        (blight if random.random() < 0.35 + 0.012 * i else alive).append((x, y, 0.0))
scatter('cornAlive', alive, stalk, [random.uniform(0.8, 1.15) for _ in alive], rot=(0.15, 0.15, 6.283))
scatter('cornDead', blight, dead, [random.uniform(0.7, 1.05) for _ in blight], rot=(0.5, 0.5, 6.283))
for k in range(40):                                        # distant farms and hills
    a = random.uniform(0, 2 * math.pi); r = random.uniform(300, 900)
    hx, hy, hr = r * math.cos(a), r * math.sin(a), random.uniform(60, 140)
    if math.hypot(hx - BASE.x, hy - 40) < hr + 90: continue                  # keep the base's valley clear
    ball((hx, hy, -20), hr, T_('#c9a26e'), scale=(1, 1, 0.35))
# the dust storm (a gravity current: front speed U = 0.7 sqrt(g' H), head rolling)
HSTORM, GP = 220.0, 0.06 * g0; U_ST = 0.7 * math.sqrt(GP * HSTORM); NP = 420
puff_src = src_ball('puffSrc', T_('#b88a5a', ao=False), 2)
pa = np.stack([RNG.uniform(0, 1, NP), RNG.uniform(-420, 420, NP), RNG.uniform(0, 1, NP)], 1); pr = RNG.uniform(16, 42, NP)
storm = scatter('dustStorm', np.zeros((NP, 3)), puff_src, pr, rot=(6.283, 6.283, 6.283)); nomb(storm)
def storm_upd(f):
    t = f / FPS; xf = 330.0 - U_ST * t; ph = pa[:, 0] * 2 * math.pi + t * U_ST / (HSTORM * 0.35)
    body = pa[:, 2] > 0.45
    x = np.where(body, xf + 40 + pa[:, 2] * 260, xf + HSTORM * 0.35 * (1 + np.cos(ph)) * 0.6)
    z = np.where(body, pa[:, 0] * HSTORM * 0.9, HSTORM * 0.35 * (1 + np.sin(ph)))
    co = np.stack([x, pa[:, 1], z], 1).astype(np.float32)
    if t > b['finds'] + 0.3: co = co[:0]                 # gone once the camera leaves the farm (no geometry at all)
    setpts(storm.data, co)
UPD.append(storm_upd); storm_upd(0)
print('storm front speed %.1f m/s' % U_ST, flush=True)
FARM = since(m0)

# ---- Murph's room (also instanced in the tesseract): everything inside the upstairs room ---------------------------
m1 = mark()
slab(-5.8, -0.2, 10.85, 11.0, RZ, 6.2, WALLP, 'roomBack')
slab(-5.8, -0.05, 6.0, 10.85, RZ, RZ + 0.03, FLOOR, 'roomFloor')
slab(-5.6, -3.6, 9.3, 10.85, RZ, RZ + 0.45, TRIM, 'bedFrame'); slab(-5.55, -3.65, 9.35, 10.8, RZ + 0.45, RZ + 0.62, T_('#f2f0ea'), 'mattress')
slab(-5.5, -3.7, 9.35, 10.3, RZ + 0.62, RZ + 0.7, T_('#7fb0e0', pattern='checker', col2='#f6e7a8', scale=2.5), 'quilt')
ball((-5.0, 10.5, RZ + 0.75), 0.25, T_('#ffffff'), scale=(1.4, 0.8, 0.45)); slab(-5.62, -5.5, 9.3, 10.85, RZ, RZ + 1.1, TRIM)
slab(-1.4, -0.3, 10.2, 10.85, RZ, RZ + 0.8, T_('#c07a4a'), 'desk'); ball((-0.8, 10.5, RZ + 1.0), 0.18, T_('#4a90d8'), scale=(1, 1, 1))  # a globe
# the bookshelf against the left wall (x = -5.8): four shelves of books
SH = T_('#9a6a40')
slab(-5.8, -5.4, 7.0, 7.08, RZ, RZ + 2.3, SH); slab(-5.8, -5.4, 8.92, 9.0, RZ, RZ + 2.3, SH)
BOOKC = ['#d04a3a', '#3a7ad0', '#f0b030', '#3aa070', '#8a4ab0', '#e07a2a', '#2a5a8a', '#c03a6a']
for k in range(5):
    zs = RZ + 0.05 + k * 0.55; slab(-5.8, -5.4, 7.0, 9.0, zs - 0.04, zs, SH)
    if k == 4: continue
    y = 7.12
    while y < 8.85:
        w = random.uniform(0.05, 0.1); h = random.uniform(0.32, 0.46)
        if not (k == 2 and 7.95 < y < 8.18):             # the gap where the ghost book (and later the watch) sits
            slab(-5.76, -5.5, y, y + w, zs, zs + h, T_(random.choice(BOOKC)))
        y += w + 0.008
# toys: a model lander on the floor, a little rocket
slab(-1.6, -1.0, 7.2, 7.5, RZ, RZ + 0.18, T_('#f2f2ee')); cone((-2.5, 10.4, RZ + 0.35), 0.12, 0.7, T_('#e0503a'))
ROOMOBJ = since(m1)
ROOM = coll('ROOM'); move(ROOMOBJ, ROOM); ROOM.instance_offset = tuple(TB_OFF)
# the dust stripes: grains from the simulation (points + tiny instanced balls)
grain = src_ball('grainSrc', T_('#a8804e', ao=False), 1)
grain.data.transform(Matrix.Scale(0.011, 4)); dust = scatter('roomDust', np.zeros((0, 3)), grain, None, rot=(0, 0, 0)); nomb(dust); INK_SKIP.append(dust)
def dust_upd(f):                                       # only grains that exist (no stacked points: keeps the ink pass cheap)
    t = f / FPS; me = dust.data
    on = (D_T0 <= t < b['leads'] + 0.1) or (b['murph2'] - 0.12 <= t < b['space'] + 0.2)
    q = dust_p[min(f, NF - 1)] if on else np.zeros((0, 3), np.float32)
    q = q[q[:, 2] > -100]
    me.clear_geometry(); me.vertices.add(len(q))
    if len(q): me.vertices.foreach_set('co', q.astype(np.float32).ravel())
    me.update()
UPD.append(dust_upd)
# the ghost book (falls at "ghost", stays on the floor until the scene ends), the watch
gb = slab(-0.13, 0.13, -0.035, 0.035, -0.2, 0.2, T_('#d04a3a'), 'ghostBook')
def bake_obj(o, f0, f1, fn):                             # fn(t) -> (loc, rot)
    fr = list(range(f0, f1 + 1)); L = [[], [], []]; R = [[], [], []]
    for f in fr:
        lc, rt = fn(f / FPS)
        for i in range(3): L[i].append(lc[i]); R[i].append(rt[i])
    for i in range(3): TP.keys(o, 'location', i, fr, L[i]); TP.keys(o, 'rotation_euler', i, fr, R[i])
def book1_at(t):
    f = F(t)
    if f in BOOK1: (x, y, z), a = BOOK1[f]; return (x, y, z + 0.2), (0, a, 0)
    return (-5.63, 8.06, RZ + 1.15 + 0.2), (0, 0, 0)
bake_obj(gb, F(b['finds']), F(b['space']), book1_at); hold(gb, F(b['finds']), F(b['space']))
WATCH = coll('watch')
m2 = mark()
cyl((0, 0, 0.0), 0.06, 0.016, T_('#c8a050')); cyl((0, 0, 0.009), 0.052, 0.004, FL('#fbf6ea'))
for k in range(12):
    a = k * math.pi / 6; box((0.044 * math.sin(a), 0.044 * math.cos(a), 0.012), (0.004, 0.009 if k % 3 else 0.014, 0.003), FL('#2a2420'), rot=(0, 0, -a))
box((0, 0.012, 0.013), (0.005, 0.03, 0.003), FL('#2a2420'), rot=(0, 0, -0.9)); box((0, 0.008, 0.013), (0.005, 0.022, 0.003), FL('#2a2420'), rot=(0, 0, 1.9))
slab(-0.018, 0.018, 0.06, 0.16, -0.003, 0.003, T_('#6a4a30')); slab(-0.018, 0.018, -0.16, -0.06, -0.003, 0.003, T_('#6a4a30'))
watch_parts = since(m2); move(watch_parts, WATCH)
hand_m = bpy.data.objects.new('secHand', None); WATCH.objects.link(hand_m)
sh_ = box((0, 0.02, 0.016), (0.0025, 0.045, 0.002), FL('#d03a2a')); sh_.parent = hand_m; move([sh_], WATCH)
wroot = bpy.data.objects.new('watchRoot', None); WATCH.objects.link(wroot)
for o in watch_parts + [hand_m]: o.parent = wroot
# the watch: in Cooper's hand -> on the bed; later on the shelf (where the book was), ticking in Morse code
MORSE = '.-- .- - -.-. ....'     # dots and dashes as tick patterns (illustrative)
def watch_at(t):
    if t < b['goes'] + 0.6: return (-3.85, 9.6, RZ + 0.72), (0, 0, 0.6)
    return (-5.62, 8.06, RZ + 0.05 + 2 * 0.55 + 0.012), (0, 0, 1.2)
bake_obj(wroot, F(b['cooper2']), NF - 1, watch_at)
def morse_angle(t):
    u = t - b['watch0']
    if u < 0: return -t * 2 * math.pi / 60.0
    seq = [];
    for ch in MORSE:
        seq += [(0.18, 0.35)] if ch == '.' else [(0.5, 0.35)] if ch == '-' else [(0.0, 0.5)]
    tt = 0.0; ang = -b['watch0'] * 2 * math.pi / 60.0
    for hold_, gap in seq:
        if u < tt + hold_: return ang - (0.25 if hold_ > 0 else 0)
        tt += hold_ + gap
    return ang
fr = list(range(F(b['watch0']) - 2, F(b['sta0'])))
TP.keys(hand_m, 'rotation_euler', 2, fr, [morse_angle(f / FPS) for f in fr], interp='CONSTANT')
for o in watch_parts + [sh_]:
    o.hide_render = True; o.keyframe_insert('hide_render', frame=0)
    for (a_, c_) in ((b['watch1'] + 0.25, b['space']), (b['watch0'], b['sta0'])):
        o.hide_render = False; o.keyframe_insert('hide_render', frame=F(a_)); o.hide_render = True; o.keyframe_insert('hide_render', frame=F(c_))
# Murph's room is upstairs in the house: hide the porch roof etc. never; the room renders at the farm and is instanced

# ================================================================== C: THE SECRET NASA BASE ==========================
m3 = mark()
HILL = T_('#b8a070'); CONC = T_('#c8ccd4'); STEEL = T_('#8a94a4'); DARKM = T_('#3a3e4a')
ball(tuple(BASE + Vector((0, 112, -25))), 60, HILL, sub=3, scale=(2.2, 1.0, 0.9))
X0, X1 = BASE.x - 22, BASE.x + 22                       # the hangar shell from slabs: back, sides, roof, front around the door
slab(X0, X1, 44.0, 46.0, 0.0, 32.0, CONC, 'hangarBack'); slab(X0, X0 + 2, -2.0, 46.0, 0.0, 32.0, CONC, 'hangarL'); slab(X1 - 2, X1, -2.0, 46.0, 0.0, 32.0, CONC, 'hangarR')
slab(X0, X1, -2.0, 46.0, 30.0, 32.0, CONC, 'hangarRoof'); slab(X0, BASE.x - 10, -2.0, -0.5, 0.0, 30.0, CONC, 'hangarF1'); slab(BASE.x + 10, X1, -2.0, -0.5, 0.0, 30.0, CONC, 'hangarF2')
slab(BASE.x - 10, BASE.x + 10, -2.0, -0.5, 18.0, 30.0, CONC, 'hangarF3')
slab(BASE.x - 20, BASE.x + 20, 0.0, 44.0, 0.0, 0.2, T_('#9aa2ae', pattern='checker', col2='#aab2be', scale=0.25), 'hangarFloor')
for x in range(-18, 19, 6): slab(BASE.x + x - 0.3, BASE.x + x + 0.3, 43.0, 43.6, 0.0, 30.0, STEEL)
for z in (8, 16, 24): slab(BASE.x - 20, BASE.x + 20, 43.4, 43.8, z, z + 0.4, T_('#ffd23a'))
slab(BASE.x - 10.5, BASE.x - 10.0, -2.2, 0.6, 0, 18.5, T_('#ffd23a')); slab(BASE.x + 10.0, BASE.x + 10.5, -2.2, 0.6, 0, 18.5, T_('#ffd23a'))
# the rocket (original stack) and its tower
RW, RB = T_('#f4f4f0'), T_('#2a2c34')
for (z0, z1, r) in ((0.5, 10, 2.2), (10, 17, 2.2), (17, 22, 1.7), (22, 25.5, 1.3)):
    cyl((BASE.x, 30, (z0 + z1) / 2), r, z1 - z0, RW if (z0 // 5) % 2 == 0 else RB)
cone((BASE.x, 30, 27.2), 1.3, 3.4, RW, v=20)
for a in range(4): ang = a * math.pi / 2; cone((BASE.x + 2.6 * math.cos(ang), 30 + 2.6 * math.sin(ang), 1.8), 0.8, 3.0, RB, v=8)
for z in range(0, 26, 3): slab(BASE.x + 4.5, BASE.x + 7.0, 28.8, 31.2, z, z + 0.3, T_('#e0503a'))
for (x, y) in ((4.6, 28.9), (6.9, 28.9), (4.6, 31.1), (6.9, 31.1)): cyl((BASE.x + x, y, 13.5), 0.12, 27, T_('#e0503a'))
# the holo table: Saturn with Keplerian rings and the wormhole orbiting
cyl((BASE.x, 12, 0.5), 1.6, 1.0, STEEL); cyl((BASE.x, 12, 1.02), 1.5, 0.04, FL('#7ae8ff', 1.2))
HOLO = FL('#9af0ff', 1.6); HOLO2 = FL('#ffe08a', 1.6)
holo_sat = ball((BASE.x, 12, 1.95), 0.42, FL('#ffd8a0', 1.3), sub=3)
rings_h = []
for r0 in (0.6, 0.72, 0.84):
    bpy.ops.mesh.primitive_torus_add(major_radius=r0, minor_radius=0.025, location=(BASE.x, 12, 1.95), rotation=(0.45, 0, 0)); rg = bpy.context.object; rg.data.materials.append(HOLO); rings_h.append(rg)
whh = ball((BASE.x, 12, 1.95), 0.16, FL('#c8a0ff', 2.0)); INK_SKIP += [holo_sat, whh] + rings_h
def holo_wh(t): a = 0.9 * t; return (BASE.x + 1.1 * math.cos(a), 12 + 1.1 * math.sin(a) * 0.6, 1.95 + 0.25 * math.sin(a)), (0, 0, 0)
bake_obj(whh, F(b['leads']), F(b['murph2']), holo_wh)
for k, rg in enumerate(rings_h):                          # Keplerian: inner rings turn faster (omega ~ r^-3/2)
    w = 1.2 * (0.6 / (0.6 + 0.12 * k)) ** 1.5; fr = [F(b['leads']), F(b['murph2'])]
    rg.rotation_mode = 'ZXY'; TP.keys(rg, 'rotation_euler', 2, fr, [w * b['leads'], w * b['murph2']])
# screens on the hangar walls
for (x, y) in ((-12, 20), (12, 20)):
    slab(BASE.x + x - 3, BASE.x + x + 3, 43.0, 43.2, 6.0, 10.0, FL('#1a2a4a')); slab(BASE.x + x - 2.6, BASE.x + x + 2.6, 42.9, 43.0, 6.4, 9.6, FL('#3ac8ff', 0.9))
BASEOBJ = since(m3)

# ================================================================== S: SPACE (Saturn, the wormhole, the station) =====
m4 = mark()
starsrc = src_ball('starSrc', FL('#ffffff', 3.0), 1)
dirs = RNG.normal(size=(2600, 3)); dirs /= np.linalg.norm(dirs, axis=1)[:, None]
stars = scatter('stars', np.array(S) + dirs * 9500, starsrc, RNG.uniform(5, 16, 2600), rot=(0, 0, 0)); INK_SKIP.append(stars)
sat = ball(tuple(SAT), SATR, T_('#f0c890', pattern='stripes', col2='#e0a870', scale=0.012, ao=False), sub=4); sat.rotation_euler = (0.3, 0.2, 0)
SATRINGS = []
for k, (r0, r1, c) in enumerate(((300, 340, '#e8d4a8'), (345, 400, '#d8b888'), (410, 470, '#c8a878'))):
    o = annulus('satRing%d' % k, SAT, r0, r1, T_(c, pattern='dots', col2='#b89868', scale=0.03, ao=False))
    o.rotation_euler = (1.35, 0.3, 0.0); SATRINGS.append(o); INK_SKIP.append(o)
# the wormhole: a glowing sphere with a rim (its lensing is shown as rings of light)
wh = ball(tuple(WH), WHR, FL('#6a4ab8', 1.0), sub=4); INK_SKIP.append(wh)
for k, (r, c) in enumerate(((1.08, '#c8a0ff'), (1.18, '#8ae0ff'), (1.3, '#ffd8f0'))):
    bpy.ops.mesh.primitive_torus_add(major_radius=WHR * r, minor_radius=WHR * 0.02, location=tuple(WH), rotation=(math.pi / 2, 0, 0)); o = bpy.context.object
    o.data.materials.append(FL(c, 2.2)); INK_SKIP.append(o)
# the Endurance (an original ring ship): 12 modules round a hub, spinning at omega = sqrt(g / r) for 1 g
def endurance(name):
    m_ = mark(); root = bpy.data.objects.new(name, None); sc.collection.objects.link(root)
    ring = bpy.data.objects.new(name + 'Ring', None); sc.collection.objects.link(ring); ring.parent = root
    for k in range(12):
        a = k * math.pi / 6; o = box((10 * math.cos(a), 10 * math.sin(a), 0), (4.6, 2.2, 1.6), T_('#eeeae2') if k % 3 else T_('#c8ccd4'), rot=(0, 0, a + math.pi / 2)); o.parent = ring
        if k % 3 == 0: s_o = box((5 * math.cos(a), 5 * math.sin(a), 0), (9.0, 0.5, 0.5), T_('#9aa0aa'), rot=(0, 0, a)); s_o.parent = ring
    h_ = cyl((0, 0, 0), 2.2, 3.0, T_('#d8dce4')); h_.parent = root
    return root, ring, since(m_)
END1, END1R, END1P = endurance('endurance1')
def end1_at(t): u = t - b['space']; return tuple(WH + Vector((0, -120.0 + 70.0 * u, -6.0))), (0.3, 0, 0)
bake_obj(END1, F(b['space']) - 2, F(b['miller0']) + 2, end1_at)
W_RING = math.sqrt(g0 / 10.0)
TP.keys(END1R, 'rotation_euler', 2, [F(b['space']) - 2, F(b['miller0']) + 2], [W_RING * (b['space'] - 0.03), W_RING * (b['miller0'] + 0.03)])
# the station: a cylinder (radius 60 m) that spins at omega = sqrt(g / R) to give 1 g on its inner floor
m5 = mark(); staroot = bpy.data.objects.new('station', None); sc.collection.objects.link(staroot); staroot.location = tuple(STA)
o = cyl((0, 0, 0), STAR, 180, T_('#d8dce4', pattern='windows', col2='#6a7a9a', cell=(9.0, 6.0), lit=0.6), rot=(0, math.pi / 2, 0)); o.parent = staroot
for sgn in (-1, 1):
    o = cyl((sgn * 92, 0, 0), STAR * 1.04, 4, T_('#9aa0aa'), rot=(0, math.pi / 2, 0)); o.parent = staroot
    o = cone((sgn * 100, 0, 0), STAR * 0.5, 16, T_('#c8ccd4'), rot=(0, sgn * math.pi / 2, 0)); o.parent = staroot
for k in range(6):
    a = k * math.pi / 3; o = box((0, STAR * 1.12 * math.cos(a), STAR * 1.12 * math.sin(a)), (150, 6, 2), T_('#3a5aa8'), rot=(a, 0, 0)); o.parent = staroot
W_STA = math.sqrt(g0 / STAR); staroot.rotation_mode = 'XYZ'
TP.keys(staroot, 'rotation_euler', 0, [0, NF - 1], [0.0, W_STA * DUR])
SPACEOBJ = since(m4)

# ================================================================== M: MILLER'S PLANET ===============================
m6 = mark()
dome(M, 1500, '#d6ecf2', '#5f86b0', '#a8cce0', 'skyMiller'); INK_SKIP.append(bpy.context.object)
gx = np.arange(-150, 151, 3.0); gy = np.arange(-150, 361, 3.0); nx, ny = len(gx), len(gy)
GX, GY = np.meshgrid(gx, gy); vtx = np.stack([GX.ravel() + M.x, GY.ravel() + M.y, np.zeros(GX.size)], 1)
faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(ny - 1) for i in range(nx - 1)]
wme = bpy.data.meshes.new('wave'); wme.from_pydata([tuple(v_) for v_ in vtx], [], faces)
for pl in wme.polygons: pl.use_smooth = True
water = bpy.data.objects.new('waterMiller', wme); sc.collection.objects.link(water); wme.materials.append(T_('#3ab0c0', pattern='zbands', col2='#5ccad6', scale=0.33, ao=False)); nomb(water); INK_SKIP.append(water)
foam = cyl(tuple(M), 0.9, 300, FL('#f4fbff', 1.3), rot=(0, math.pi / 2, 0)); foam.name = 'foamCrest'; INK_SKIP.append(foam)
bake_obj(foam, F(b['miller0']), F(b['mann0']), lambda t: ((M.x, M.y + cW * (b['hit'] - t) - 2.0, AW + 0.2), (0, math.pi / 2, 0)))
INK_SKIP.append(disc(M, 1450, T_('#46bccb', ao=False), 'seaMiller', z=-0.05))
def wave_upd(f):
    t = f / FPS
    if not (b['miller0'] - 0.2 < t < b['mann0'] + 0.2): return
    z = eta(GY.ravel(), t); co = vtx.copy(); co[:, 2] = z; wme.vertices.foreach_set('co', co.astype(np.float32).ravel()); wme.update()
UPD.append(wave_upd)
# Gargantua hanging in the sky, debris of the earlier mission
gs = ball(tuple(M + Vector((420, 1250, 520))), 170, FL('#0a0610'), sub=3); INK_SKIP.append(gs)
for (r0, r1, c, s) in ((190, 260, '#fff0c0', 2.0), (260, 380, '#ffb050', 1.6), (380, 470, '#e0602a', 1.2)):
    bpy.ops.mesh.primitive_torus_add(major_radius=(r0 + r1) / 2, minor_radius=(r1 - r0) / 2, location=tuple(M + Vector((420, 1250, 520))), rotation=(1.42, 0, 0.25))
    o = bpy.context.object; o.scale = (1, 1, 0.06); o.data.materials.append(FL(c, s)); INK_SKIP.append(o)
for k in range(7): box(tuple(M + Vector((-9 + random.uniform(-3, 3), 18 + random.uniform(-3, 3), 0.2))), (random.uniform(0.6, 1.8), random.uniform(0.4, 1.2), random.uniform(0.3, 0.9)), T_('#c8ccd4'), rot=(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(0, 3)))
# the lander (original design): a chunky shuttle with a side hatch
def lander(name):
    m_ = mark(); root = bpy.data.objects.new(name, None); sc.collection.objects.link(root)
    parts = [box((0, 0, 0.9), (8.0, 3.6, 1.8), T_('#eeeae2')), box((3.4, 0, 1.2), (2.4, 3.0, 1.4), T_('#eeeae2'), rot=(0, 0.35, 0)),
             box((0, 0, 0.1), (8.2, 3.7, 0.25), T_('#2a2c34')), box((2.9, 0, 1.55), (1.2, 2.6, 0.5), T_('#3a4a6a'), rot=(0, 0.35, 0)),
             box((-2.0, 0, 2.0), (3.6, 2.4, 0.5), T_('#c8ccd4')), box((0.2, -1.82, 1.0), (1.2, 0.08, 1.4), T_('#3a3e4a')),
             box((-4.6, 1.0, 0.9), (1.2, 1.0, 1.0), T_('#8a94a4')), box((-4.6, -1.0, 0.9), (1.2, 1.0, 1.0), T_('#8a94a4')),
             box((-1.0, 2.6, 0.9), (3.0, 1.6, 0.18), T_('#c8ccd4')), box((-1.0, -2.6, 0.9), (3.0, 1.6, 0.18), T_('#c8ccd4'))]
    for p_ in parts: p_.parent = root
    flame = cone((-5.6, 0, 0.9), 0.8, 2.6, FL('#ffd27a', 2.5), rot=(0, -math.pi / 2, 0)); flame.parent = root; INK_SKIP.append(flame)
    return root, flame
LND, LFL = lander('lander')
def lander_at(t):
    f = F(t); y, z, pitch = LANDER.get(f, (0.0, -0.6, 0.0)); return tuple(M + Vector((0, y, z + 0.6))), (0.0, 0.0, 0.0) if t < b['lift'] else (0.0, -0.35 * ease((t - b['lift']) / 1.0), 0.0)
def lander_at2(t):
    f = F(t); y, z, pitch = LANDER.get(f, (0.0, -0.6, 0.0)); rx = -pitch * 0.8
    if t > b['lift']: rx = rx * (1 - ease((t - b['lift']) / 0.8))
    return tuple(M + Vector((0, y, z + 0.6))), (rx, -0.45 * ease((t - b['lift']) / 1.0) if t > b['lift'] else 0.0, 0.0)
bake_obj(LND, F(b['miller0']) - 2, F(b['mann0']) + 2, lander_at2)
LFL.hide_render = True; LFL.keyframe_insert('hide_render', frame=0); LFL.hide_render = False; LFL.keyframe_insert('hide_render', frame=F(b['lift'])); LFL.hide_render = True; LFL.keyframe_insert('hide_render', frame=F(b['mann0']) + 1)
MILLEROBJ = since(m6)

# ================================================================== N: MANN'S PLANET ==================================
m7 = mark()
dome(N, 1500, '#c8dcec', '#34466a', '#8aa4c8', 'skyMann'); INK_SKIP.append(bpy.context.object)
INK_SKIP.append(disc(N, 1450, T_('#eef6fb'), 'iceMann'))
ICE = T_('#cfe6f4'); ICE2 = T_('#a8cce4')
for k in range(60):
    a = random.uniform(0, 2 * math.pi); r = random.uniform(25, 400)
    if abs(math.cos(a) * r) < 25 and math.sin(a) * r < 40: continue
    cone(tuple(N + Vector((r * math.cos(a), r * math.sin(a), 0))), random.uniform(4, 22), random.uniform(6, 40), random.choice([ICE, ICE2]), v=5)
for k in range(26):                                     # the frozen clouds
    box(tuple(N + Vector((random.uniform(-260, 260), random.uniform(20, 420), random.uniform(45, 110)))), (random.uniform(30, 90), random.uniform(20, 60), random.uniform(4, 10)),
        T_('#f4fafe'), rot=(random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(0, 3)))
hab = cyl(tuple(N + Vector((-9, 16, 2.2))), 3.4, 4.4, T_('#e8e4dc')); ball(tuple(N + Vector((-9, 16, 4.4))), 3.4, T_('#e8e4dc'), scale=(1, 1, 0.6))
cyl(tuple(N + Vector((-4.6, 12, 3.0))), 0.12, 6, T_('#8a94a4')); beacon = ball(tuple(N + Vector((-4.6, 12, 6.2))), 0.4, FL('#ff4a3a', 3.0))
# Mann's tablet (true data -> fake data)
tab = bpy.data.objects.new('tablet', None); sc.collection.objects.link(tab)
tb1 = box((0, 0, 0), (0.32, 0.02, 0.22), T_('#2a2c34')); tb1.parent = tab
scr_ok = box((0, -0.012, 0), (0.28, 0.005, 0.18), FL('#5af0a0', 1.2)); scr_ok.parent = tab
scr_bad = box((0, -0.014, 0), (0.28, 0.005, 0.18), FL('#ff4a3a', 1.4)); scr_bad.parent = tab
hold(scr_ok, F(b['mann0']), F(b['data1'])); hold(scr_bad, F(b['data1']) + 1, F(b['tries']))
MANNOBJ = since(m7)

# ================================================================== G: GARGANTUA =====================================
m8 = mark()
hole = ball(tuple(G), RS, FL('#000000'), sub=4); INK_SKIP.append(hole)
DISK = []
for k, (r0, r1, c, s) in enumerate(((48, 62, '#fff6d8', 3.0), (62, 80, '#ffd890', 2.4), (80, 104, '#ffaa50', 1.9), (104, 132, '#f07030', 1.5), (132, 160, '#b84020', 1.1))):
    o = annulus('disk%d' % k, G, r0, r1, FL('#000000'), n=128); o.data.materials.clear()
    m_ = bpy.data.materials.new('disk%d' % k); m_.use_nodes = True; nt = m_.node_tree; nn = nt.nodes
    for x_ in list(nn): nn.remove(x_)
    out = nn.new('ShaderNodeOutputMaterial'); em = nn.new('ShaderNodeEmission'); tc = nn.new('ShaderNodeTexCoord'); nz = nn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.06; nz.inputs['Detail'].default_value = 2
    mp = nn.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 1, 1); nt.links.new(tc.outputs['Object'], mp.inputs[0]); nt.links.new(mp.outputs[0], nz.inputs['Vector'])
    rp = nn.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = 0.35; rp.color_ramp.elements[0].color = (*hexc(c), 1); rp.color_ramp.elements[1].color = (*[min(1, v * 1.6 + 0.1) for v in hexc(c)], 1)
    nt.links.new(nz.outputs['Fac'], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = s; nt.links.new(em.outputs[0], out.inputs['Surface'])
    o.data.materials.append(m_); o.rotation_mode = 'XYZ'; o.rotation_euler = (0.1, 0, 0); DISK.append((o, (r0 + r1) / 2)); INK_SKIP.append(o)
    w = 0.9 * (48.0 / ((r0 + r1) / 2)) ** 1.5                     # Keplerian
    TP.keys(o, 'rotation_euler', 2, [F(b['garg0']) - 2, F(b['tes0']) + 2], [w * b['garg0'], w * b['tes0']])
for k, (r, c) in enumerate(((44, '#fff6d8'), (50, '#ffc870'))):          # the lensed image of the far side and the photon ring
    bpy.ops.mesh.primitive_torus_add(major_radius=r + 14 * k, minor_radius=3 + 5 * k, location=tuple(G), rotation=(math.pi / 2 - 0.1, 0, 0)); o = bpy.context.object
    o.scale = (1, 1, 0.35); o.data.materials.append(FL(c, 2.6 - k)); INK_SKIP.append(o)
END2, END2R, END2P = endurance('endurance2')
bake_obj(END2, F(b['garg0']) - 2, F(b['tes0']) + 2, lambda t: (endurance_at(t), (0.4, 0.1, 0.3)))
TP.keys(END2R, 'rotation_euler', 2, [F(b['garg0']) - 2, F(b['tes0']) + 2], [W_RING * b['garg0'], W_RING * b['tes0']])
RNG2, RFL = lander('ranger'); RNG2.scale = (0.55, 0.55, 0.55)
def ranger_rot(t):
    p0 = Vector(ranger_at(t)); p1 = Vector(ranger_at(t + 0.05)); d = p1 - p0
    yaw = math.atan2(d.y, d.x) if d.length > 1e-4 else 0.0; return (0.0, 0.0, yaw)
bake_obj(RNG2, F(b['garg0']) - 2, F(b['tes0']) + 2, lambda t: (ranger_at(t), ranger_rot(t)))
RFL.hide_render = True; RFL.keyframe_insert('hide_render', frame=0)
GARGOBJ = since(m8)

# ================================================================== T: THE TESSERACT ==================================
m9 = mark()
TESS = []
for i in range(-2, 3):
    for j in range(0, 3):
        for k in range(-2, 3):
            if j == 0 and i == 0 and k == 0: pass
            o = bpy.data.objects.new('tess', None); o.instance_type = 'COLLECTION'; o.instance_collection = ROOM; sc.collection.objects.link(o)
            o.location = tuple(T + Vector((i * 7.4, j * 6.2, k * 3.6))); TESS.append(o)
GOLDL = FL('#ffcc5a', 1.8)
for i in range(-3, 4):
    for k in range(-3, 4):
        o = box(tuple(T + Vector((i * 7.4 - 3.7, 6.0, k * 3.6 - 0.05))), (0.05, 40, 0.05), GOLDL); INK_SKIP.append(o)
for j in range(0, 4):
    for k in range(-3, 4):
        o = box(tuple(T + Vector((0, j * 6.2 - 3.1, k * 3.6 - 0.05))), (44, 0.05, 0.05), GOLDL); INK_SKIP.append(o)
dome(T, 600, '#1a1440', '#05040e', '#2a1a50', 'skyTess'); INK_SKIP.append(bpy.context.object)
# the ghost book in the central copy (pushed out of the shelf at "ghost")
gb2 = slab(-0.13, 0.13, -0.035, 0.035, -0.2, 0.2, T_('#d04a3a'), 'ghostBook2')
BOOK2 = book_fall(b['push'], (-5.63, 8.06, RZ + 1.15), 1.3, RZ)
def book2_at(t):
    f = F(t); (x, y, z), a = BOOK2.get(f, ((-5.63, 8.06, RZ + 1.15), 0.0)) if t >= b['push'] else ((-5.63, 8.06, RZ + 1.15), 0.0)
    w = T + (Vector((x, y, z + 0.2)) - TB_OFF); return tuple(w), (0, a, 0)
bake_obj(gb2, F(b['tes0']), F(b['watch0']), book2_at); hold(gb2, F(b['tes0']), F(b['watch0']))
TESSOBJ = since(m9)

# ================================================================== the ark (from the farm, at the end) ===============
m10 = mark()
ark = bpy.data.objects.new('ark', None); sc.collection.objects.link(ark)
for (z0, z1, r, c) in ((0, 60, 26, '#eeeae2'), (60, 90, 22, '#c8ccd4'), (90, 110, 16, '#eeeae2')):
    o = cyl((0, 0, (z0 + z1) / 2), r, z1 - z0, T_(c, pattern='windows', col2='#3a4a6a', cell=(6.0, 5.0), lit=0.5)); o.parent = ark
o = cone((0, 0, 118), 16, 16, T_('#c8ccd4')); o.parent = ark
fl_ = cone((0, 0, -22), 20, 44, FL('#ffd27a', 2.6), rot=(math.pi, 0, 0)); fl_.parent = ark; INK_SKIP.append(fl_)
bake_obj(ark, F(b['ark0']) - 30, F(b['sta0']) + 2, lambda t: ((140.0, 120.0, 8.0 + ark_z(t)), (0, 0, 0)))
ARK_PARTS = [ark] + [c_ for c_ in bpy.data.objects if c_.parent == ark]
hold(fl_, F(b['ark0']), F(b['sta0']))
for o in [ark] + [c_ for c_ in bpy.data.objects if c_.parent == ark]: pass
# its dust cloud spreads out along the ground (puffs slowed by drag: r(t) = r_inf (1 - exp(-k t)))
NA = 90; aa = RNG.uniform(0, 2 * math.pi, NA); ar = RNG.uniform(20, 40, NA)
apuff = scatter('arkDust', np.zeros((NA, 3)), puff_src, RNG.uniform(8, 18, NA), rot=(6.283, 6.283, 6.283)); nomb(apuff)
def ark_dust_upd(f):
    t = f / FPS; u = t - b['ark0']
    if u < 0 or t > b['sta0'] + 0.1: co = np.zeros((0, 3))
    else:
        r = ar + 120 * (1 - np.exp(-0.8 * u)); co = np.stack([140 + r * np.cos(aa), 120 + r * np.sin(aa), np.full(NA, 6.0)], 1)
    setpts(apuff.data, co)
UPD.append(ark_dust_upd)
ARKOBJ = since(m10)

# ================================================================== I: INSIDE THE STATION =============================
m11 = mark()
CYC = I + Vector((0, 0, 60.0))                         # the cylinder's axis (along x); its floor at z = I.z
bpy.ops.mesh.primitive_cylinder_add(radius=60.0, depth=400, vertices=96, location=tuple(CYC), rotation=(0, math.pi / 2, 0)); cyl_in = bpy.context.object
for pl in cyl_in.data.polygons: pl.use_smooth = True
cyl_in.data.materials.append(T_('#8ccf6a', pattern='checker', col2='#7cc05a', scale=0.04))
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
for x in range(-190, 191, 16):                                                  # houses and trees round the inside
    for k in range(24):
        a = k * 2 * math.pi / 24 + (x % 32) * 0.02
        if abs(math.sin(a / 2)) < 0.14 and abs(x) < 20: continue                # keep the hospital lot clear
        down = Vector((0, math.sin(a), -math.cos(a))); base = CYC + down * 60.0 + Vector((x + random.uniform(-3, 3), 0, 0))
        up_ = -down; rot = (a, 0, 0)
        if random.random() < 0.55:
            box(tuple(base + up_ * 2.5), (random.uniform(5, 8), random.uniform(5, 8), 5.0), T_(random.choice(['#f4eee0', '#f6d6a8', '#cfe0f0', '#f0c8c0'])), rot=rot)
            box(tuple(base + up_ * 5.6), (6.0, 6.0, 1.2), T_(random.choice(['#c0503a', '#7a6e7e', '#3a6a9a'])), rot=rot)
        else:
            ball(tuple(base + up_ * 3.0), random.uniform(2.0, 3.2), T_('#4aa858'), scale=(1, 1, 1.2))
# the hospital room (open to -y)
room2 = solid(I.x - 4.0, I.x + 4.0, I.y - 0.2, I.y + 6.0, I.z - 0.2, I.z + 3.4, T_('#eef2f6'), 'hosp'); cutbox(room2, I.x - 3.8, I.x + 3.8, I.y - 1.0, I.y + 5.8, I.z, I.z + 3.2)
slab(I.x - 3.8, I.x + 3.8, I.y + 0.0, I.y + 5.8, I.z, I.z + 0.03, T_('#d8e4ec', pattern='checker', col2='#e8f0f6', scale=1.2))
slab(I.x - 2.0, I.x + 0.4, I.y + 2.6, I.y + 3.9, I.z, I.z + 0.5, T_('#c8ccd4')); slab(I.x - 2.0, I.x + 0.4, I.y + 2.6, I.y + 3.9, I.z + 0.5, I.z + 0.65, T_('#f6f4f0'))
slab(I.x - 2.1, I.x - 1.95, I.y + 2.6, I.y + 3.9, I.z, I.z + 1.1, T_('#c8ccd4'))
slab(I.x - 1.4, I.x + 0.3, I.y + 2.62, I.y + 3.88, I.z + 0.65, I.z + 0.78, T_('#a8d0f0', pattern='checker', col2='#d8ecfa', scale=2.0))
ball(tuple(I + Vector((-1.7, 3.25, 0.82))), 0.26, T_('#ffffff'), scale=(0.7, 1.4, 0.4))
slab(I.x + 1.4, I.x + 2.0, I.y + 3.0, I.y + 3.6, I.z, I.z + 0.8, T_('#9aa0aa')); ball(tuple(I + Vector((1.7, 3.3, 1.2))), 0.25, T_('#e04a6a'))     # flowers
slab(I.x - 1.0, I.x + 1.0, I.y + 5.75, I.y + 5.8, I.z + 1.0, I.z + 2.4, FL('#bfe6ff', 1.0))                                         # a window
INSIDEOBJ = since(m11)

# ================================================================== THE CAST (3D) ====================================
CAST = dict(
    cooper=dict(skin='#e2a782', hair='#5a3a22', style='short', top='#5a86bf', legs='#3e4a5e', boots='#6a4a30'),
    cooperS=dict(suit=True, skin='#e2a782', hair='#5a3a22', style='short', patch='#3a6ad8'),
    murphK=dict(kid=True, skin='#f2c29e', hair='#9a4f2a', style='bob', top='#7fb35a', legs='#5a6a8a', boots='#c0503a'),
    brandP=dict(skin='#f0c8a8', hair='#eeeae6', style='fringe', glasses=True, top='#6a6e7a', legs='#55596a', boots='#2a2a30', height=1.74),
    amelia=dict(suit=True, skin='#f3c9a7', hair='#6a4028', style='bun', patch='#3a6ad8', height=1.7),
    doyle=dict(suit=True, skin='#8a5638', hair='#1c1410', style='buzz', patch='#3a6ad8'),
    mann=dict(suit=True, skin='#e8b48f', hair='#c89a5a', style='short', patch='#3a6ad8', browtilt=-0.25),
    murphA=dict(skin='#f2c29e', hair='#9a4f2a', style='long', top='#c86a4a', legs='#3a3a4a', height=1.7),
    murphO=dict(skin='#f0c4a4', hair='#f2efea', style='bob', top='#cfe0f0', legs='#cfe0f0', height=1.6, brow=0.004),
)
P = {k: TP.Person(k, sp, PEOPLE) for k, sp in CAST.items()}
def face(dx, dy): return math.atan2(dx, -dy)          # yaw that turns the -y front toward (dx, dy)
def walk_to(t, t0, t1, p0, p1):
    u = clamp((t - t0) / (t1 - t0)); return lerp3(p0, p1, u), u
def gait(t, t0, t1, p0, p1, stride=1.3):
    (pos, u) = walk_to(t, t0, t1, p0, p1); d = math.dist(p0[:2], p1[:2]); moving = t0 <= t <= t1
    ph = (d * u) / stride * math.pi; pose = TP.walk_pose(ph, 1.0) if moving else TP.stand(t)
    z = TP.walk_bob(ph) if moving else 0.0
    return (pos[0], pos[1], pos[2] + z), face(p1[0] - p0[0], p1[1] - p0[1]), pose, moving
SPANS = {}
def span_bake(name, t0, t1, fn, track=True):
    f0, f1 = max(0, F(t0)), min(NF - 1, F(t1)); TP.bake(P[name], f0, f1, FPS, fn, hide_outside=False); SPANS.setdefault(name, []).append((f0, f1))
def finish_vis():
    for name, sp in SPANS.items():
        for o in P[name].parts:
            o.hide_render = True; o.keyframe_insert('hide_render', frame=0)
            for f0, f1 in sp:
                o.hide_render = False; o.keyframe_insert('hide_render', frame=f0); o.hide_render = True; o.keyframe_insert('hide_render', frame=f1 + 1)
        for o in P[name].parts:
            for kp in o.animation_data.action.fcurves.find('hide_render').keyframe_points: kp.interpolation = 'CONSTANT'
    for name in P:
        if name not in SPANS:
            for o in P[name].parts: o.hide_render = True
KNEEL = dict(hpL=(1.4,), knL=(-1.45,), anL=(0.1,), hpR=(-0.1,), knR=(-1.6,), anR=(0.9,), chest=(0.1,), shL=(0.2, 0.15), shR=(0.2, 0.15), elL=(0.4,), elR=(0.4,))
SIT = dict(hpL=(1.5,), hpR=(1.5,), knL=(-1.5,), knR=(-1.5,), shL=(0.2, 0.15), shR=(0.2, 0.15), elL=(0.6,), elR=(0.6,))
HUG = dict(shL=(0.95, -0.15), shR=(0.95, -0.15), elL=(0.9,), elR=(0.9,))
WAVE = dict(shR=(0.3, 2.6), elR=(0.6,))
POINT = dict(shR=(1.5, 0.1), elR=(0.05,))
HANDS_HIPS = dict(shL=(0.0, 0.5), shR=(0.0, 0.5), elL=(-1.6,), elR=(-1.6,))
REACH = dict(shL=(1.5, 0.1), shR=(1.45, -0.1), elL=(0.2,), elR=(0.3,))
FIST = dict(shR=(0.6, 0.4), elR=(2.4,), shL=(0.1, 0.1))
def P_(*ds):
    out = TP.stand()
    for d in ds: out.update(d)
    return out
def bl(t, t0, dur, a, c): return TP.blend(a, c, ease((t - t0) / dur))

# ---- Cooper (farm clothes): porch hug, walk to the truck, by the truck, in Murph's room, the base, then the station
CP_PORCH = (0.8, 2.6, 0.0); CP_TRUCK = (11.6, -1.4, 0.0)
def cooper_A(t):
    if t < b['leave'] + 0.1:
        return dict(loc=CP_PORCH, yaw=face(-1, 0.1), pose=P_(KNEEL, HUG))
    if t < b['leave'] + 0.6:
        return dict(loc=CP_PORCH, yaw=face(-1, 0.1), pose=bl(t, b['leave'] + 0.1, 0.5, P_(KNEEL, HUG), P_()))
    if t < b['promised']:
        pos, yaw, pose, mv = gait(t, b['leave'] + 0.6, b['promised'] - 0.05, CP_PORCH, (4.0, 0.8, 0.0)); return dict(loc=pos, yaw=yaw, pose=pose)
    if t < b['back'] + 0.6:
        return dict(loc=(4.0, 0.8, 0.0), yaw=face(-1, 0.5), pose=bl(t, b['promised'], 0.35, P_(), P_(WAVE)))
    pos, yaw, pose, mv = gait(t, b['back'] + 0.6, b['dying'] + 1.6, (4.0, 0.8, 0.0), CP_TRUCK); return dict(loc=pos, yaw=yaw, pose=pose)
span_bake('cooper', 0.0, b['dying'] + 1.7, cooper_A)
span_bake('cooper', b['cooper1'] - 0.5, b['finds'] + 0.3, lambda t: dict(loc=CP_TRUCK, yaw=face(-0.5, -1.0), pose=bl(t, b['farmer'], 0.4, P_(), P_(HANDS_HIPS))))
span_bake('cooper', b['finds'] + 0.31, b['leads'] + 0.2, lambda t: dict(loc=(-2.0, 7.6, RZ), yaw=face(-0.8, 0.6) if t < b['calls'] else face(-1, 0.2),
                                                                    pose=P_(KNEEL) if t < b['calls'] - 0.2 else bl(t, b['calls'] - 0.2, 0.4, P_(KNEEL), P_())))
span_bake('cooper', b['leads'] + 0.4, b['murph2'] - 0.11, lambda t: dict(loc=(BASE.x + 1.9, 10.2, 0.2), yaw=face(-0.6, 1.0), pose=P_()))
def cooper_go(t):
    if t < b['watch1'] - 0.3: return dict(loc=(-3.0, 7.8, RZ), yaw=face(-1.6, 1.4), pose=P_())
    if t < b['goes']: return dict(loc=(-3.0, 7.8, RZ), yaw=face(-1.6, 1.4), pose=bl(t, b['watch1'] - 0.3, 0.4, P_(), P_(dict(shR=(1.2, 0.1), elR=(0.4,)))))
    pos, yaw, pose, mv = gait(t, b['goes'], b['goes'] + 1.4, (-3.0, 7.8, RZ), (-0.2, 9.6, RZ)); return dict(loc=pos, yaw=yaw, pose=pose)
span_bake('cooper', b['murph2'] - 0.09, b['goes'] + 0.55, cooper_go)
span_bake('cooper', b['room0'] - 0.05, DUR, lambda t: (lambda g_: dict(loc=g_[0], yaw=g_[1] if t < b['old'] else face(-1, 0.3),
          pose=g_[2] if t < b['old'] else (bl(t, b['find'], 0.4, P_(), P_(dict(chest=(0.2,), neck=(0.3,)))) if t < b['brand2'] + 0.4 else P_())))(
          gait(t, b['room0'], b['old'] - 0.05, (I.x + 2.6, I.y + 0.6, I.z), (I.x + 0.6, I.y + 2.2, I.z))))
# ---- Murph as a child
MK_PORCH = (0.1, 2.7, 0.0)
def murph_A(t):
    if t < b['leave'] + 0.2: return dict(loc=MK_PORCH, yaw=face(1, -0.1), pose=P_(HUG))
    return dict(loc=MK_PORCH, yaw=face(1, -0.6), pose=bl(t, b['promised'], 0.4, P_(), P_(WAVE)) if t > b['promised'] else P_())
span_bake('murphK', 0.0, b['dying'] + 1.7, murph_A)
span_bake('murphK', b['finds'] + 0.31, b['leads'] + 0.2, lambda t: dict(loc=(-3.2, 7.2, RZ), yaw=face(-0.2, 1.0) if t < b['calls'] else face(-1, 0.3),
                                                                      pose=P_(KNEEL) if t < b['calls'] - 0.2 else (P_(POINT) if t > b['ghost1'] - 0.2 else P_())))
span_bake('murphK', b['murph2'] - 0.09, b['goes'] + 0.55, lambda t: dict(loc=(-4.6, 9.2, RZ + 0.05), yaw=face(-0.5, -1.0), pose=P_(SIT, dict(chest=(0.25,), neck=(0.3,)))))
# ---- Professor Brand at the base
span_bake('brandP', b['leads'] + 0.4, b['murph2'] - 0.11, lambda t: dict(loc=(BASE.x - 1.6, 10.6, 0.2), yaw=face(0.8, 0.6), pose=bl(t, b['wormhole'] - 0.3, 0.4, P_(), P_(POINT))))
# ---- Miller's planet: Cooper at the hatch, Brand at the wreck runs back, Doyle swept by the wave
span_bake('cooperS', b['miller0'] - 0.05, b['hit'] - 0.6, lambda t: dict(loc=tuple(M + Vector((1.2, -2.6, float(eta(-2.6, t)) - 0.35))), yaw=face(-0.4, -1.0),
                                                                        pose=bl(t, b['earth2'], 0.4, P_(), P_(WAVE)) if t > b['earth2'] else P_()))
def amelia_M(t):
    p0 = tuple(M + Vector((-8.0, 16.0, -0.35))); p1 = tuple(M + Vector((-0.6, -2.4, -0.35)))
    if t < b['giant']: return dict(loc=add(p0, (0, 0, float(eta(16.0, t)))), yaw=face(0.3, 1.0), pose=P_(dict(chest=(0.5,), shL=(0.9, 0.1), shR=(0.9, 0.1), elL=(0.8,), elR=(0.8,))))
    pos, yaw, pose, mv = gait(t, b['giant'], b['hit'] - 0.6, p0, p1, stride=1.8); pose.update(TP.walk_pose(math.dist(p0, p1) * clamp((t - b['giant']) / (b['hit'] - 0.6 - b['giant'])) / 1.8 * math.pi, 1.0, run=1.0))
    return dict(loc=(pos[0], pos[1], pos[2] + float(eta(pos[1] - M.y, t))), yaw=yaw, pose=pose)
span_bake('amelia', b['miller0'] - 0.05, b['hit'] - 0.6, amelia_M)
def doyle_M(t):
    f = F(t); y, z, sl = DOYLE.get(f, (7.0, -0.25, 0.0))
    if t < b['hit'] - 0.35:
        return dict(loc=tuple(M + Vector((4.0, y, z - 0.1))), yaw=face(-0.3, -1.0), pose=P_(POINT) if t > b['earth2'] else P_())
    u = t - (b['hit'] - 0.35); return dict(loc=tuple(M + Vector((4.0, y, z - 0.1))), yaw=face(-0.3, -1.0) + 0.8 * u, roll=(-2.4 * u, 0.6 * u),
                                           pose=P_(dict(shL=(1.6, 1.2), shR=(1.4, 1.4), hpL=(0.6,), knL=(-1.0,), hpR=(-0.3,))))
span_bake('doyle', b['miller0'] - 0.05, b['lift'] + 0.6, doyle_M)
# ---- Mann's planet: the tablet, the shove, the fall
MN = tuple(N + Vector((-0.75, 0.0, 0.0))); CN = tuple(N + Vector((0.75, 0.0, 0.0)))
def mann_N(t):
    if t < b['tries']: pose = P_(dict(shR=(1.0, 0.1), elR=(1.3,), shL=(0.6, 0.1), elL=(1.4,)))
    else: pose = bl(t, b['tries'], 0.22, P_(dict(shR=(1.0, 0.1), elR=(1.3,))), P_(dict(shL=(1.45, -0.1), shR=(1.45, 0.1), elL=(0.1,), elR=(0.1,), chest=(0.3,), hpL=(0.4,), knL=(-0.2,))))
    return dict(loc=MN if t < b['tries'] else lerp3(MN, add(MN, (0.35, 0, 0)), ease((t - b['tries']) / 0.25)), yaw=face(1, -0.15), pose=pose)
span_bake('mann', b['mann0'] - 0.05, b['garg0'] - 0.02, mann_N)
def cooper_N(t):
    th = FALL.get(F(t), 0.0) if t >= b['shove'] else 0.0
    return dict(loc=CN, yaw=face(-1, -0.15), roll=(-th, 0.0), pose=P_(dict(shL=(0.9 * min(1, th * 2), 0.8 * min(1, th * 2)), shR=(0.9 * min(1, th * 2), 0.8 * min(1, th * 2)))))
span_bake('cooperS', b['mann0'] - 0.05, b['garg0'] - 0.02, cooper_N)
# ---- the tesseract: Cooper drifts (constant velocity and spin), the push sends him back
CT0 = T + Vector((-4.3, -0.4, 0.35)); CV = Vector((0.06, 0.02, 0.01)); m_c, m_b, v_b = 120.0, 0.8, 1.3
def cooper_T(t):
    u = t - b['tes0']; p_ = CT0 + CV * u
    if t > b['push']: p_ = p_ + Vector((-1, 0, 0)) * (m_b * v_b / m_c) * (t - b['push'])          # recoil
    pose = P_(REACH, dict(hpL=(0.4,), knL=(-0.6,), hpR=(0.1,), knR=(-0.3,)))
    if b['push'] - 0.25 < t < b['push'] + 0.2: pose = P_(dict(shR=(1.6, 0.0), elR=(0.0,), shL=(1.2, 0.2), elL=(0.4,)))
    return dict(loc=tuple(p_), yaw=face(1, 0.05) + 0.03 * u, roll=(0.08 * math.sin(0.7 * u), 0.05 * u), pose=pose)
span_bake('cooperS', b['tes0'], b['watch0'] - 0.02, cooper_T)
# ---- Murph as an adult in her old room
def murphA_A(t):
    if t < b['murph3']: return dict(loc=(-4.6, 7.9, RZ), yaw=face(-1, 0.05), pose=P_(dict(shR=(0.9, 0.1), elR=(1.2,), chest=(0.1,))))
    if t < b['humanity2']: return dict(loc=(-4.6, 7.9, RZ), yaw=face(-1, -1.0 * ease((t - b['murph3']) / 0.4)), pose=bl(t, b['cracks'], 0.3, P_(), P_(FIST)))
    return dict(loc=(-4.6, 7.9, RZ), yaw=face(-1, -1.0), pose=P_(FIST))
span_bake('murphA', b['watch0'] + 0.4, b['sta0'] - 0.02, murphA_A)
# ---- Murph, old, in bed (lying on her back, head toward -x)
def murphO_I(t):
    pose = P_(dict(shR=(0.15, 0.1),))
    if t > b['sends'] - 0.2: pose = bl(t, b['sends'] - 0.2, 0.4, pose, P_(dict(shR=(1.1, 0.3), elR=(0.4,))))
    return dict(loc=tuple(I + Vector((-0.25, 3.25, 0.8))), yaw=math.pi / 2, roll=(-(math.pi / 2 - 0.25), 0.0), pose=pose)
span_bake('murphO', b['room0'] - 0.05, DUR, murphO_I)
finish_vis()
TP_PROPS = []
# props held: the watch in Cooper's hand before it is set on the bed (simply placed), the tablet in Mann's hand
tab.location = tuple(N + Vector((-0.42, -0.28, 1.22))); tab.rotation_euler = (0.25, 0, -0.35)
for o_ in (tb1,): hold(o_, F(b['mann0']), F(b['tries']))

# actor tracks for the compositor's tags (feet position + visibility per frame)
def track_of(name, size=1.0):
    root = P[name].root; sp = SPANS.get(name, []); out, vis_ = [], []
    return root, sp
ACTORS = ['cooper', 'murphK', 'brandP', 'amelia', 'doyle', 'mann', 'cooperS', 'murphA', 'murphO']

# ------------------------------------------------------------------ each set renders only while it is on screen ------
def region(objs, windows):
    for o in objs:
        if o.name not in bpy.data.objects or o.hide_render: continue
        ad_ = o.animation_data
        if ad_ and ad_.action and ad_.action.fcurves.find('hide_render'): continue
        o.hide_render = True; o.keyframe_insert('hide_render', frame=0)
        for a_, c_ in windows:
            o.hide_render = False; o.keyframe_insert('hide_render', frame=max(0, F(a_))); o.hide_render = True; o.keyframe_insert('hide_render', frame=min(NF + 1, F(c_) + 1))
TAIL = DUR + 1
region([o for o in FARM if o not in ROOMOBJ and o is not storm], [(0, b['space'] + 0.05), (b['watch0'] - 0.05, b['sta0'] + 0.05)])
region(BASEOBJ, [(b['leads'] - 0.1, b['murph2'])])
region(SPACEOBJ, [(b['space'] - 0.05, b['miller0'] + 0.05), (b['sta0'] - 0.05, b['room0'] + 0.05)])
region(MILLEROBJ, [(b['miller0'] - 0.05, b['mann0'] + 0.05)])
region(MANNOBJ, [(b['mann0'] - 0.05, b['garg0'] + 0.05)])
region(GARGOBJ, [(b['garg0'] - 0.05, b['tes0'] + 0.05)])
region(TESSOBJ, [(b['tes0'] - 0.05, b['watch0'] + 0.05)])
region(ARK_PARTS, [(b['ark0'] - 0.6, b['sta0'] + 0.05)]); region([apuff], [(b['ark0'] + 0.02, b['sta0'] + 0.05)])
region([storm], [(0, b['finds'] + 0.2)])
region([dust], [(D_T0, b['leads'] + 0.05), (b['murph2'] - 0.1, b['space'] - 0.2)])
region(INSIDEOBJ, [(b['room0'] - 0.05, TAIL)])
fs_.use_culling = True

# ------------------------------------------------------------------ inking rules ----------------------------------
for ob in list(bpy.data.objects):
    if ob.type == 'MESH' and (ob.name.startswith(('sky', 'sea', 'ground', 'water', 'ice', 'stars', 'roomDust', 'arkDust', 'dustStorm', 'corn'))): INK_SKIP.append(ob)
noink = bpy.data.collections.new('noink'); sc.collection.children.link(noink)
for ob in set(INK_SKIP):
    if ob.name in ROOM.objects: continue
    for c_ in list(ob.users_collection): c_.objects.unlink(ob)
    noink.objects.link(ob)
ls_ = sc.view_layers[0].freestyle_settings.linesets[0]; ls_.select_by_collection = True; ls_.collection = noink; ls_.collection_negation = 'EXCLUSIVE'
for ob in bpy.data.objects:
    ad_ = ob.animation_data
    if ad_ and ad_.action:
        for fc in ad_.action.fcurves:
            if fc.data_path == 'hide_render':
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# ------------------------------------------------------------------ camera ---------------------------------------
bpy.ops.object.camera_add(location=SEG_A[0][1]); cam = bpy.context.object; cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24; cam.data.clip_start = 0.03; cam.data.clip_end = 20000; sc.camera = cam
tgt = bpy.data.objects.new('camTarget', None); sc.collection.objects.link(tgt)
tc_ = cam.constraints.new('TRACK_TO'); tc_.target = tgt; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
fr = list(range(NF)); CP = [cam_at(f / FPS) for f in fr]
for i_ in fr:                                          # ride above the swell on Miller's planet
    t = i_ / FPS
    if b['miller0'] <= t < b['mann0']:
        p_, l_, ln_ = CP[i_]; e_ = float(eta(p_.y - M.y, t))
        if p_.z < e_ + 2.5: d_ = e_ + 2.5 - p_.z; CP[i_] = (p_ + Vector((0, 0, d_)), l_ + Vector((0, 0, d_ * 0.8)), ln_)
for i in range(3):
    TP.keys(cam, 'location', i, fr, [c_[0][i] for c_ in CP]); TP.keys(tgt, 'location', i, fr, [c_[1][i] for c_ in CP])
TP.keys(cam.data, 'lens', 0, fr, [c_[2] for c_ in CP])

track, actors, vis, roll = [], {k: [] for k in ACTORS}, {k: [] for k in ACTORS}, []
spans_f = {k: SPANS.get(k, []) for k in ACTORS}
for f in range(NF):
    sc.frame_set(f); Mx = cam.matrix_world
    track.append(dict(C=[round(v_, 4) for v_ in Mx.translation], R=[[round(Mx[r][c], 5) for c in range(3)] for r in range(3)], tanh=round(12.0 / cam.data.lens, 6)))
    for k in ACTORS:
        p_ = P[k].root.matrix_world.translation; on = any(a <= f <= c for a, c in spans_f[k])
        actors[k].append([round(p_.x, 3), round(p_.y, 3), round(p_.z, 3)]); vis[k].append(1 if on else 0)
    roll.append(0.0)
json.dump(dict(fps=FPS, frames=NF, track=track, actors=actors, vis=vis, roll=roll, beats=B, flashes=FLASH_T), open(os.path.join(OUT, 'camera.json'), 'w'))
print('tracks written', NF, flush=True)

sc.frame_start, sc.frame_end = START, END; sc.render.use_persistent_data = True
if '--noink' in argv: sc.render.use_freestyle = False
if '--drop' in argv:                                   # debugging: remove objects whose names start with these prefixes
    for pre in arg('--drop', '').split(','):
        for ob in [o for o in bpy.data.objects if o.name.startswith(pre)]: bpy.data.objects.remove(ob)
if '--diag' in argv:
    f = arg('--diag', 0); sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); stat = {}
    for inst in dg.object_instances:
        ob = inst.object
        if ob.type != 'MESH': continue
        if ob.original.hide_render: continue
        k = (inst.parent.original.name if inst.is_instance and inst.parent else ob.original.name)
        n = len(ob.data.polygons); stat[k] = stat.get(k, 0) + n
    for k, n in sorted(stat.items(), key=lambda x: -x[1])[:25]: print('DIAG', k, n)
    for nm in ('dustStorm', 'tess', 'skyMiller', 'cooper.skull', 'hangarBack'): print('DIAGHIDE', nm, bpy.data.objects[nm].hide_render if nm in bpy.data.objects else None)
    print('DIAG total', sum(stat.values())); raise SystemExit

LIST = [int(v_) for v_ in arg('--list', '').split(',') if v_]
if LIST:
    for f in LIST: sc.frame_set(f); on_frame(sc); sc.render.filepath = os.path.join(OUT, 'f%04d.jpg' % f); bpy.ops.render.render(write_still=True)
    print('list done', flush=True)
elif '--tracks-only' not in argv:
    sc.render.use_overwrite = False; sc.render.use_placeholder = True; sc.render.filepath = os.path.join(OUT, 'f####'); bpy.ops.render.render(animation=True); print('sequence done', flush=True)
