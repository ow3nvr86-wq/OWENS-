"""One 3D island at dusk (original design, after the user's reference picture): a purple starry sky with shooting
stars, a rocket climbing toward a glowing crack in the sky, a clock-tower town with water towers on a hill, a comet
crater with a purple meteor held in scaffolding (lab domes, containers, crystals), a drive-in cinema screen, a
mountain, rolling green hills and pines. Each preset is a camera on that same world:
  b_town, b_crater, b_field, b_drivein, b_sky   (+ b_lobby, a separate stage)
Run: $BLENDER -b --factory-startup -P tools/bg_blender.py -- <out> b_town ... --layers --extra tools/presets_island.py"""
import bpy, math, random
from mathutils import Vector

NAMES = ['b_town', 'b_crater', 'b_field', 'b_drivein', 'b_sky', 'b_lobby']
CR = (0.0, 60.0)                                   # crater centre
TOWN = (0.0, 150.0)


def m_emis(name, col, strength, base=None, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or col), 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = strength; return m


def m_glow(name, col, strength, alpha):          # soft additive-looking halo: emission mixed with transparency
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    e.inputs['Color'].default_value = (*col, 1); e.inputs['Strength'].default_value = strength; mx.inputs['Fac'].default_value = alpha
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m


def dusk_world(sc, strength=1.0):
    w = bpy.data.worlds.new('dusk'); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    cr = ramp.color_ramp; cr.elements[0].position = 0.0; cr.elements[0].color = (0.02, 0.03, 0.05, 1)
    cr.elements[1].position = 1.0; cr.elements[1].color = (0.006, 0.004, 0.03, 1)
    for p, c in [(0.495, (0.05, 0.03, 0.06)), (0.5, (1.0, 0.42, 0.16)), (0.52, (0.75, 0.16, 0.32)), (0.56, (0.26, 0.07, 0.36)), (0.66, (0.07, 0.025, 0.17)), (0.8, (0.02, 0.012, 0.07))]:
        e = cr.elements.new(p); e.color = (*c, 1)
    # stars: tiny Voronoi cells above the horizon
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 420; vor.feature = 'F1'
    nt.links.new(tc.outputs['Generated'], vor.inputs['Vector'])
    thr = nt.nodes.new('ShaderNodeMath'); thr.operation = 'LESS_THAN'; thr.inputs[1].default_value = 0.045; nt.links.new(vor.outputs['Distance'], thr.inputs[0])
    rnd = nt.nodes.new('ShaderNodeMath'); rnd.operation = 'MULTIPLY'; nt.links.new(thr.outputs[0], rnd.inputs[0]); nt.links.new(vor.outputs['Color'], rnd.inputs[1])
    hi = nt.nodes.new('ShaderNodeMath'); hi.operation = 'GREATER_THAN'; hi.inputs[1].default_value = 0.55; nt.links.new(sep.outputs['Z'], hi.inputs[0])
    st = nt.nodes.new('ShaderNodeMath'); st.operation = 'MULTIPLY'; nt.links.new(rnd.outputs[0], st.inputs[0]); nt.links.new(hi.outputs[0], st.inputs[1])
    st2 = nt.nodes.new('ShaderNodeMath'); st2.operation = 'MULTIPLY'; st2.inputs[1].default_value = 2.5; nt.links.new(st.outputs[0], st2.inputs[0])
    add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'; add.inputs['Factor'].default_value = 1.0
    nt.links.new(ramp.outputs['Color'], add.inputs[6]); nt.links.new(st2.outputs[0], add.inputs[7])
    nt.links.new(add.outputs[2], bg.inputs['Color']); bg.inputs['Strength'].default_value = strength; nt.links.new(bg.outputs[0], out.inputs['Surface'])


def sunlight(elev, rot, energy, col):
    bpy.ops.object.light_add(type='SUN'); s = bpy.context.object; s.data.energy = energy; s.data.color = col; s.data.angle = math.radians(3)
    s.rotation_euler = (math.radians(90 - elev), 0, math.radians(rot)); return s


def H(x, y):                                       # terrain height (metres)
    h = 2.6 * math.sin(x * 0.012 + 0.4) * math.cos(y * 0.0095) + 1.8 * math.sin((x + y) * 0.021) + 0.9 * math.sin(x * 0.05 - y * 0.03)
    h += 9 * math.exp(-((x - TOWN[0]) ** 2 + (y - TOWN[1]) ** 2) / 70 ** 2)          # the town hill
    h += 7 * math.exp(-((x - 160) ** 2 + (y - 75) ** 2) / 30 ** 2)                   # the rocky hill (final circle)
    h += 0.02 * max(0, y - 250) + 0.0
    r = math.hypot(x - CR[0], y - CR[1])
    if r < 34: h = h * (r / 34) ** 2 - 7.5 * (1 - (r / 34) ** 2) * 1.0
    h += 2.2 * math.exp(-((r - 34) / 5.0) ** 2)                                        # crater rim
    return h


def grid(size, sub, mat, loc=(0, 0), fn=H):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=sub, y_subdivisions=sub, size=size, location=(loc[0], loc[1], 0)); o = bpy.context.object
    for v in o.data.vertices: v.co.z = fn(v.co.x + loc[0], v.co.y + loc[1])
    o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o


def box(loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.scale = size; o.data.materials.append(m); return o


def cyl(loc, r, d, m, rot=(0, 0, 0), v=20):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=v); o = bpy.context.object; o.data.materials.append(m); return o


def cone(loc, r, d, m, v=12, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r, depth=d, location=loc, vertices=v, rotation=rot); o = bpy.context.object; o.data.materials.append(m); return o


def ball(loc, r, m, sub=2, scale=(1, 1, 1), smooth=True):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc); o = bpy.context.object; o.scale = scale; o.data.materials.append(m)
    if smooth: bpy.ops.object.shade_smooth()
    return o


def pine(x, y, h, mt, ml, ml2):
    z = H(x, y); cyl((x, y, z + h * 0.08), h * 0.035, h * 0.18, mt, v=8)
    for k, (r, hh) in enumerate([(0.34, 0.32), (0.27, 0.52), (0.18, 0.72)]): cone((x, y, z + h * hh), r * h, h * 0.42, ml if k % 2 == 0 else ml2, v=9)


def building(x, y, w, d, h, wall, win, roof, rotz=0.0, tank=False, sign=None):
    z = H(x, y) - 1.0
    box((x, y, z + h / 2), (w, d, h), wall); box((x, y, z + h + 0.3), (w + 0.6, d + 0.6, 0.6), roof)
    nx, ny = int(w / 2.6), int((h - 2) / 3.2)
    for i in range(nx):
        for j in range(ny):
            if random.random() < 0.82: box((x - w / 2 + 1.3 + i * (w - 2.0) / max(1, nx - 1) * (1 if nx > 1 else 0), y - d / 2 - 0.06, z + 2.2 + j * 3.2), (1.0, 0.12, 1.5), win if random.random() < 0.72 else roof)
    if tank:
        tz = z + h + 0.6
        for sx in (-1, 1):
            for sy in (-1, 1): cyl((x + sx * 1.2, y + sy * 1.2, tz + 1.4), 0.12, 2.8, roof, v=6)
        cyl((x, y, tz + 4.2), 2.0, 3.2, wall_tank, v=18); cone((x, y, tz + 6.4), 2.3, 1.6, roof, v=18)
    if sign: box((x, y - d / 2 - 0.3, z + h + 2.2), (w * 0.7, 0.3, 2.2), sign)


def build_world(M, Hh, view):
    global wall_tank
    mat = Hh['mat']
    grass = mat('grassD', (0.07, 0.24, 0.06), 0.9, True, (0.16, 0.36, 0.08), 0.08, 0.15)
    dirt = mat('dirtD', (0.42, 0.27, 0.13), 0.95, True, (0.55, 0.38, 0.2), 0.5, 0.3)
    floor = mat('floorD', (0.12, 0.065, 0.04), 0.95, True, (0.2, 0.11, 0.06), 0.8, 0.3)
    trunk = mat('trunkD', (0.16, 0.09, 0.05), 0.9); leaf = mat('leafD', (0.03, 0.12, 0.05), 0.85); leaf2 = mat('leafD2', (0.05, 0.16, 0.06), 0.85)
    rock = mat('rockD', (0.22, 0.2, 0.25), 0.85, True, (0.32, 0.3, 0.35), 2.0, 0.5)
    meteor = m_emis('meteor', (0.55, 0.18, 1.0), 4.5, (0.4, 0.12, 0.8), 0.25)
    crystal = m_emis('crystal', (0.5, 0.12, 1.0), 3.0, (0.35, 0.08, 0.7), 0.2)
    metal = mat('scaff', (0.75, 0.77, 0.82), 0.35); white = mat('domeW', (0.85, 0.86, 0.9), 0.3)
    walls = [mat('wall%d' % i, c, 0.85, True, tuple(v * 0.8 for v in c), 3.0, 0.15) for i, c in enumerate([(0.55, 0.36, 0.2), (0.42, 0.26, 0.15), (0.62, 0.43, 0.24), (0.36, 0.22, 0.13)])]
    win = m_emis('winD', (1.0, 0.72, 0.28), 5.0, (0.9, 0.7, 0.3)); roof = mat('roofD', (0.16, 0.08, 0.05), 0.8)
    wall_tank = mat('tank', (0.38, 0.2, 0.1), 0.8)
    # ground
    grid(900, 300, grass, (0, 120))
    grid(80, 120, dirt, CR, fn=lambda x, y: H(x, y) + 0.02 if math.hypot(x - CR[0], y - CR[1]) < 39 else H(x, y) - 3)
    grid(56, 90, floor, CR, fn=lambda x, y: H(x, y) + 0.05 if math.hypot(x - CR[0], y - CR[1]) < 26 else H(x, y) - 3)
    # the meteor in scaffolding, lab domes, containers, crystals
    mz = H(*CR)
    o = ball((CR[0], CR[1], mz + 4.2), 1, meteor, 1, (6.0, 5.0, 5.4), smooth=False); o.rotation_euler = (0.3, 0.2, 0.5)
    bpy.ops.object.light_add(type='POINT', location=(CR[0], CR[1] - 6, mz + 6)); L = bpy.context.object; L.data.energy = 9000; L.data.color = (0.6, 0.3, 1.0); L.data.shadow_soft_size = 4
    for sx in (-1, 1):
        for sy in (-1, 1): cyl((CR[0] + sx * 7.5, CR[1] + sy * 7.5, mz + 5.5), 0.18, 11, metal, v=8)
    for zz in (mz + 2, mz + 6, mz + 10.8):
        for (a, b, c, d) in [(-7.5, -7.5, 7.5, -7.5), (-7.5, 7.5, 7.5, 7.5), (-7.5, -7.5, -7.5, 7.5), (7.5, -7.5, 7.5, 7.5)]:
            x0, y0, x1, y1 = CR[0] + a, CR[1] + b, CR[0] + c, CR[1] + d; L_ = math.hypot(x1 - x0, y1 - y0)
            cyl(((x0 + x1) / 2, (y0 + y1) / 2, zz), 0.14, L_, metal, (0, math.pi / 2, math.atan2(y1 - y0, x1 - x0)), v=8)
    for dx, dy, r in [(-16, -4, 4.2), (16, 2, 5.0)]: ball((CR[0] + dx, CR[1] + dy, H(CR[0] + dx, CR[1] + dy)), r, white, 3, (1, 1, 0.62))
    for dx, dy, c in [(-12, -12, (0.7, 0.18, 0.1)), (-4, -15, (0.12, 0.25, 0.65)), (9, -13, (0.85, 0.6, 0.15)), (13, -9, (0.7, 0.18, 0.1))]:
        box((CR[0] + dx, CR[1] + dy, H(CR[0] + dx, CR[1] + dy) + 1.2), (5, 2.4, 2.4), mat('cont%d' % dx, c, 0.6), (0, 0, random.uniform(-0.3, 0.3)))
    for k in range(70):
        a = random.uniform(0, math.tau); r = random.choice([random.uniform(10, 26), random.uniform(30, 40)])
        x, y = CR[0] + math.cos(a) * r, CR[1] + math.sin(a) * r; s = random.uniform(0.5, 1.4)
        cone((x, y, H(x, y) + s), s * 0.5, s * 2.4, crystal, 5, (random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), random.random()))
    # town on the hill: buildings around a clock tower
    tz = H(*TOWN)
    random.seed(11)
    for x, y, w, d, h, ci, kw in [(-30, 158, 10, 10, 18, 0, {}), (-19, 152, 9, 9, 26, 1, {'tank': True}), (-9, 160, 10, 9, 32, 2, {}),
                                   (11, 156, 11, 10, 30, 3, {'sign': True}), (22, 150, 9, 9, 24, 0, {}), (32, 158, 9, 9, 18, 1, {'tank': True}),
                                   (-40, 166, 9, 9, 14, 2, {}), (42, 166, 9, 9, 13, 3, {}), (-4, 176, 12, 10, 20, 1, {}), (20, 178, 10, 10, 16, 2, {})]:
        sign = m_emis('sign', (0.9, 0.12, 0.08), 1.5, (0.8, 0.1, 0.08)) if kw.get('sign') else None
        building(x, y, w, d, h, walls[ci], win, roof, tank=kw.get('tank', False), sign=sign)
    cz = H(1, 150) - 1
    box((1, 150, cz + 22), (4.6, 4.6, 44), mat('tower', (0.72, 0.6, 0.42), 0.8)); box((1, 150, cz + 44.4), (5.4, 5.4, 0.8), roof)
    cone((1, 150, cz + 48.5), 3.9, 7.5, mat('towerRoof', (0.36, 0.1, 0.06), 0.7), 4, (0, 0, math.pi / 4))
    cyl((1, 147.6, cz + 39), 1.6, 0.3, m_emis('clock', (1.0, 0.92, 0.75), 2.5), (math.pi / 2, 0, 0), 32)
    for zz, lit in [(32, True), (26, False), (20, True)]: box((1, 147.65, cz + zz), (1.1, 0.12, 2.4), win if lit else roof)
    # drive-in cinema
    sx, sy = -85.0, 110.0; sz = H(sx, sy)
    for dx in (-11, -4, 4, 11): cyl((sx + dx, sy + 0.6, sz + 4), 0.35, 8, roof, v=8)
    box((sx, sy + 0.4, sz + 13.5), (31, 0.8, 12), mat('screenFrame', (0.08, 0.06, 0.1), 0.6))
    box((sx, sy, sz + 13.5), (29, 0.4, 10.4), m_emis('screen', (0.75, 0.78, 1.0), 0.9, (0.8, 0.8, 1.0)))
    cyl((sx, sy - 0.3, sz + 15.5), 2.2, 0.2, m_emis('ssun', (1.0, 0.8, 0.3), 2.0), (math.pi / 2, 0, 0), 32)
    bpy.ops.mesh.primitive_cone_add(radius1=8, depth=0.1, vertices=3, location=(sx - 3, sy - 0.32, sz + 11.0), rotation=(math.pi / 2, 0, 0)); bpy.context.object.data.materials.append(m_emis('smtn', (0.5, 0.42, 0.95), 1.2))
    for row, yy in enumerate((78, 88, 98)):
        for xx in (-98, -90, -82, -74):
            if random.random() < 0.65:
                x, y = xx + random.uniform(-1, 1), yy; z = H(x, y); c = random.choice([(0.7, 0.15, 0.1), (0.15, 0.35, 0.7), (0.85, 0.65, 0.2), (0.3, 0.55, 0.3)])
                cm = mat('car%d%d' % (xx, yy), c, 0.35); box((x, y, z + 0.8), (2.0, 4.2, 0.9), cm); box((x, y + 0.3, z + 1.55), (1.7, 2.2, 0.7), cm)
                for wx in (-1, 1):
                    for wy in (-1.3, 1.3): cyl((x + wx * 0.95, y + wy, z + 0.4), 0.4, 0.3, roof, (0, math.pi / 2, 0), 12)
            cyl((xx + 2.5, yy + 2, H(xx + 2.5, yy + 2) + 0.7), 0.06, 1.4, roof, v=6)
    # the mountain and the rocky hill
    bpy.ops.mesh.primitive_cone_add(radius1=170, depth=150, vertices=48, location=(240, 470, 50)); mtn = bpy.context.object; mtn.data.materials.append(mat('mtn', (0.12, 0.08, 0.14), 0.9, True, (0.2, 0.14, 0.2), 0.05, 0.3))
    d = mtn.modifiers.new('S', 'SUBSURF'); d.levels = 2; d2 = mtn.modifiers.new('D', 'DISPLACE'); tx = bpy.data.textures.new('mt', 'CLOUDS'); tx.noise_scale = 0.4; d2.texture = tx; d2.strength = 18
    for k in range(10): x, y = 160 + random.uniform(-9, 9), 75 + random.uniform(-9, 9); ball((x, y, H(x, y) + random.uniform(0, 1.5)), random.uniform(1.5, 3.5), rock, 2, (1.3, 1, 0.8))
    # pines everywhere except the crater, town and drive-in
    random.seed(5)
    for k in range(420):
        x, y = random.uniform(-250, 260), random.uniform(-80, 380)
        if math.hypot(x - CR[0], y - CR[1]) < 44 or (abs(x) < 52 and 135 < y < 190) or math.hypot(x - sx, y - 95) < 30 or math.hypot(x - 160, y - 75) < 14: continue
        if view == 'b_town' and abs(x) < 10 and 90 < y < 135: continue
        pine(x, y, random.uniform(7, 14), trunk, leaf, leaf2)
    # sky: shooting stars, the rocket and the crack
    star = m_emis('streak', (1.0, 0.92, 1.0), 12)
    for (az, el, L_, rot) in [(-30, 38, 70, 0.5), (-12, 48, 90, 0.55), (8, 54, 60, 0.5), (24, 44, 55, 0.45), (-38, 26, 45, 0.6)]:
        a, e = math.radians(az), math.radians(el); D = 1500
        p = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * D + Vector((0, 60, 0))
        cyl(tuple(p), 0.9, L_, star, (math.radians(70), 0, rot + math.pi / 2), 6)
    rk = Vector((330, 900, 620))
    body = m_emis('rocketW', (1, 1, 1), 0.6, (0.95, 0.95, 0.97)); red = mat('rocketR', (0.8, 0.12, 0.08), 0.5)
    cyl(tuple(rk), 4, 26, body, (0, math.radians(18), 0)); cone(tuple(rk + Vector((math.sin(math.radians(18)) * 16, 0, 16 * math.cos(math.radians(18))))), 4, 8, red, 16, (0, math.radians(18), 0))
    cone(tuple(rk - Vector((math.sin(math.radians(18)) * 15, 0, 15))), 3, 8, m_emis('flame', (1.0, 0.75, 0.2), 25), 12, (math.pi + math.radians(18), 0, 0))
    smoke = mat('smoke', (0.85, 0.82, 0.88), 1.0)
    for k in range(14): ball(tuple(rk - Vector((math.sin(math.radians(18)) * (22 + k * 11), random.uniform(-2, 2), 22 + k * 11))), 6 + k * 1.6, smoke, 2)
    crack = m_emis('crack', (0.6, 0.85, 1.0), 30); halo = m_glow('crackHalo', (0.5, 0.75, 1.0), 6, 0.35)
    pts = [(-260, -170), (-150, -110), (-90, -160), (40, -60), (120, -120), (250, -10), (320, -40), (430, 50)]
    base = Vector((300, 1000, 880))
    for (a1, b1), (a2, b2) in zip(pts, pts[1:]):
        p1 = base + Vector((a1 * 0.9, 0, -b1 * 0.9)); p2 = base + Vector((a2 * 0.9, 0, -b2 * 0.9)); dv = p2 - p1
        for r, m in [(2.2, crack), (9, halo)]:
            cyl(tuple((p1 + p2) / 2), r, dv.length, m, (0, math.atan2(dv.x, dv.z), 0), 8)
    # dusk lighting: warm low sun from the camera side, cool purple sky fill
    sunlight(9, 200, 3.2, (1.0, 0.62, 0.38)); sunlight(40, 20, 0.5, (0.45, 0.4, 1.0))
    return grass


def build(preset, sc, M, Hh):
    if preset not in NAMES: return False
    cam = Hh['cam']
    sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = 0.2
    if preset == 'b_lobby':
        dusk_world(sc, 0.6)
        mat = Hh['mat']; floor = mat('lfloor', (0.04, 0.03, 0.09), 0.25)
        bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, 0)); bpy.context.object.data.materials.append(floor)
        cyl((0, 0, 0.3), 3.4, 0.6, mat('plat', (0.75, 0.78, 0.88), 0.2), v=64)
        bpy.ops.mesh.primitive_torus_add(major_radius=3.42, minor_radius=0.07, location=(0, 0, 0.6)); bpy.context.object.data.materials.append(m_emis('ring', (0.35, 0.7, 1.0), 12))
        for k in range(40):
            box((random.uniform(-18, 18), random.uniform(8, 30), random.uniform(1, 18)), (random.uniform(0.3, 1.1),) * 3,
                m_emis('fl%d' % k, random.choice([(0.3, 0.45, 1.0), (0.65, 0.3, 1.0), (1.0, 0.75, 0.3)]), 3), (random.random(), random.random(), random.random()))
        for (x, c, e) in [(-7, (0.45, 0.5, 1.0), 2500), (7, (0.75, 0.4, 1.0), 2500), (0, (1.0, 0.85, 0.75), 1500)]:
            bpy.ops.object.light_add(type='SPOT', location=(x, -7, 11)); L = bpy.context.object; L.data.energy = e; L.data.color = c; L.data.spot_size = 0.6
            L.rotation_euler = (Vector((0, 0, 1)) - Vector((x, -7, 11))).to_track_quat('-Z', 'Y').to_euler()
        cam(sc, (0, -15, 3.4), (0, 0, 2.4), lens=35, focus=15, fstop=4)
        return True
    dusk_world(sc, 1.0)
    build_world(M, Hh, preset)
    if preset == 'b_town':
        cam(sc, (4, 92, 3.2), (0, 150, 17), lens=24, focus=38, fstop=8)
    elif preset == 'b_crater':
        cam(sc, (0, 14, 12), (0, 64, 0), lens=22, focus=48, fstop=11)
    elif preset == 'b_field':
        cam(sc, (128, 18, 3.4), (162, 90, 8), lens=26, focus=55, fstop=8)
    elif preset == 'b_drivein':
        cam(sc, (-85, 62, 3.2), (-85, 112, 10), lens=24, focus=36, fstop=8)
    elif preset == 'b_sky':
        cam(sc, (0, -230, 230), (0, 150, 30), lens=30, focus=300, fstop=22)
        cl = Hh['mat']('cloudD', (0.55, 0.42, 0.62), 1.0)
        for (d, n, r) in [(60, 3, 14), (120, 4, 26), (220, 5, 40), (380, 5, 60)]:
            for k in range(n):
                a = random.uniform(-0.5, 0.5); p = Vector((0, -230, 230)) + Vector((math.sin(a) * d * 1.1, d, -d * 0.45 + random.uniform(-0.12, 0.12) * d))
                for j in range(6): ball(tuple(p + Vector((random.uniform(-1.2, 1.2) * r, random.uniform(-0.4, 0.4) * r, random.uniform(-0.2, 0.3) * r))), r * random.uniform(0.5, 0.9), cl, 2, (1, 0.8, 0.6))
    return True
