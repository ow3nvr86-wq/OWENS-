"""Human-scale 3D sets for the Fortnite Chapter 1 Season 4 Short, styled like illustrated-history Shorts:
detailed textured 3D (brick, planks, asphalt, gravel, dense grass) under a dusk sky, warm key light, soft ink
outlines (Freestyle) so 2D characters sit in them naturally, and a little glow. Original designs.
  b2_bus     inside a flying bus: seat rows, poles, ceiling lights, dusk sky through the windows
  b2_town    street level in a tower town: brick buildings, shopfronts, awnings, lamps, cars, a clock tower
  b2_crater  inside the comet crater: big purple crystals, the meteor in scaffolding, lab domes, crates
  b2_field   a grassy field (real grass), boulders, pines, the mountain, the crack in the sky
  b2_drivein car level at the drive-in: gravel, cars, speaker posts, the big screen
Run: $BLENDER -b --factory-startup -P tools/bg_blender.py -- <out> b2_town ... --layers --extra tools/presets_fn2.py"""
import bpy, math, random, os, importlib.util
from mathutils import Vector

_spec = importlib.util.spec_from_file_location('presets_island', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'presets_island.py'))
ISL = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(ISL)
box, cyl, cone, ball, m_emis, dusk_world, sunlight, _T = ISL.box, ISL.cyl, ISL.cone, ISL.ball, ISL.m_emis, ISL.dusk_world, ISL.sunlight, ISL._T
NAMES = ['b2_bus', 'b2_town', 'b2_crater', 'b2_field', 'b2_drivein']


# ---------------- textured materials ----------------
def m_brick(name, c1, c2, mortar, scale=4.0, w=0.5, h=0.25):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = scale
    br.inputs['Color1'].default_value = (*c1, 1); br.inputs['Color2'].default_value = (*c2, 1); br.inputs['Mortar'].default_value = (*mortar, 1)
    br.inputs['Brick Width'].default_value = w; br.inputs['Row Height'].default_value = h; br.inputs['Mortar Size'].default_value = 0.018
    nt.links.new(tc.outputs['Object'], br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.35; nt.links.new(br.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.85; return m


def m_planks(name, c1, c2, scale=1.5):
    return m_brick(name, c1, c2, tuple(v * 0.45 for v in c1), scale, 2.4, 0.18)


def m_noise(name, c1, c2, scale=8.0, rough=0.85, bump=0.3, detail=8):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); tx = nt.nodes.new('ShaderNodeTexNoise'); tx.inputs['Scale'].default_value = scale; tx.inputs['Detail'].default_value = detail
    nt.links.new(tc.outputs['Object'], tx.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (*c1, 1); rp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tx.outputs['Fac'], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], b.inputs['Base Color'])
    if bump: bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = bump; nt.links.new(tx.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough; return m


def m_plain(name, c, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*c, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal; return m


def plane(loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.scale = (size[0], size[1], 1); o.data.materials.append(m); return o


def grass_patch(loc, size, density, height, mat_ground, seed=1, colors=((0.08, 0.3, 0.05), (0.28, 0.55, 0.12))):
    """a ground patch with real hair grass"""
    o = plane(loc, size, mat_ground); bpy.ops.object.modifier_add(type='PARTICLE_SYSTEM')
    ps = o.particle_systems[0].settings; ps.type = 'HAIR'; ps.count = int(density * size[0] * size[1]); ps.hair_length = height
    ps.use_advanced_hair = True; ps.brownian_factor = 0.04; ps.factor_random = 0.25; ps.use_rotations = True; ps.rotation_factor_random = 0.25
    ps.child_type = 'NONE'; ps.root_radius = 1.0; ps.tip_radius = 0.0; ps.radius_scale = 0.012; ps.length_random = 0.6
    o.particle_systems[0].seed = seed; ps.display_step = 2; ps.render_step = 3
    gm = bpy.data.materials.new('grassBlade'); gm.use_nodes = True; nt = gm.node_tree; b = nt.nodes['Principled BSDF']
    hi = nt.nodes.new('ShaderNodeHairInfo'); rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (*colors[0], 1); rp.color_ramp.elements[1].color = (*colors[1], 1)
    nt.links.new(hi.outputs['Intercept'], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.6
    o.data.materials.append(gm); ps.material = 2
    return o


def outlines(sc, thickness=2.2, col=(0.07, 0.05, 0.07)):
    """soft ink outlines on the 3D (Freestyle), like the hand-drawn characters"""
    sc.render.use_freestyle = True; sc.render.line_thickness_mode = 'RELATIVE'; sc.render.line_thickness = 1.0
    vl = sc.view_layers[0]; fs = vl.freestyle_settings; fs.crease_angle = math.radians(120)
    ls = fs.linesets.new('ink') if not fs.linesets else fs.linesets[0]
    ls.select_by_visibility = True; ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
    if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new('inkStyle')
    st = ls.linestyle; st.color = col; st.thickness = thickness; st.alpha = 0.85


def glow(sc, threshold=0.85, mix=-0.75):
    """compositor glare: a soft bloom on the bright bits (windows, lamps, crystals)"""
    sc.use_nodes = True; nt = sc.node_tree; nt.nodes.clear()
    rl = nt.nodes.new('CompositorNodeRLayers'); gl = nt.nodes.new('CompositorNodeGlare'); comp = nt.nodes.new('CompositorNodeComposite')
    gl.glare_type = 'FOG_GLOW'; gl.quality = 'MEDIUM'; gl.threshold = threshold; gl.mix = mix; gl.size = 8
    nt.links.new(rl.outputs['Image'], gl.inputs['Image']); nt.links.new(gl.outputs['Image'], comp.inputs['Image'])
    sc['glow'] = (threshold, mix)


def sky_bits(base=Vector((0, 1500, 0)), scale=1.0):
    """shooting streaks, the rocket and the glowing crack, placed relative to the camera's forward view"""
    star = m_emis('streak', (1.0, 0.92, 1.0), 12)
    for (dx, dz, L_, rot) in [(-260, 420, 70, 0.5), (-80, 520, 90, 0.55), (120, 600, 60, 0.5), (300, 470, 55, 0.45), (-420, 330, 45, 0.6)]:
        cyl(tuple(base + Vector((dx, 0, dz)) * scale), 0.9 * scale, L_ * scale, star, (math.radians(70), 0, rot + math.pi / 2), 6)
    crack = m_emis('crack', (0.55, 0.8, 1.0), 12); halo = ISL.m_glow('crackHalo', (0.3, 0.6, 1.0), 8, 0.45); halo2 = ISL.m_glow('crackHalo2', (0.25, 0.5, 1.0), 6, 0.25)
    pts = [(-260, -170), (-150, -110), (-90, -160), (40, -60), (120, -120), (250, -10), (320, -40), (430, 50)]
    b0 = base + Vector((380, 0, 640)) * scale
    for (a1, b1), (a2, b2) in zip(pts, pts[1:]):
        p1 = b0 + Vector((a1, 0, -b1)) * 0.9 * scale; p2 = b0 + Vector((a2, 0, -b2)) * 0.9 * scale; dv = p2 - p1
        for r, m in [(2.2, crack), (6, halo), (16, halo2)]: cyl(tuple((p1 + p2) / 2), r * scale, dv.length, m, (0, math.atan2(dv.x, dv.z), 0), 8)
    rk = base + Vector((330, 0, 260)) * scale; body = m_emis('rocketW', (1, 1, 1), 0.6, (0.95, 0.95, 0.97)); red = m_plain('rocketR', (0.8, 0.12, 0.08), 0.5)
    cyl(tuple(rk), 4 * scale, 26 * scale, body, (0, math.radians(18), 0)); cone(tuple(rk + Vector((5, 0, 15.5)) * scale), 4 * scale, 8 * scale, red, 16, (0, math.radians(18), 0))
    cone(tuple(rk - Vector((4.6, 0, 15)) * scale), 3 * scale, 8 * scale, m_emis('flame', (1.0, 0.75, 0.2), 25), 12, (math.pi + math.radians(18), 0, 0))
    sm = m_plain('smoke', (0.85, 0.82, 0.88), 1.0)
    for k in range(14): ball(tuple(rk - Vector((4.6 + k * 3.4, random.uniform(-2, 2), 22 + k * 11)) * scale), (6 + k * 1.6) * scale, sm, 2)


def tree(x, y, z, h, mt, ml, ml2):
    cyl((x, y, z + h * 0.08), h * 0.035, h * 0.18, mt, v=8)
    for k, (r, hh) in enumerate([(0.34, 0.32), (0.27, 0.52), (0.18, 0.72)]): cone((x, y, z + h * hh), r * h, h * 0.42, ml if k % 2 == 0 else ml2, v=9)


def car(x, y, rot, col, tire, glass):
    cm = m_plain('car%.0f%.0f' % (x, y), col, 0.3); c, s = math.cos(rot), math.sin(rot)
    box((x, y, 0.62), (1.9, 4.3, 0.7), cm, (0, 0, rot)); box((x - s * 0.25, y + c * 0.25, 1.22), (1.7, 2.3, 0.62), cm, (0, 0, rot))
    box((x - s * 0.25, y + c * 0.25, 1.25), (1.72, 2.0, 0.42), glass, (0, 0, rot))
    for dx in (-0.95, 0.95):
        for dy in (-1.35, 1.35): cyl((x + dx * c - dy * s, y + dx * s + dy * c, 0.36), 0.36, 0.28, tire, (0, math.pi / 2, rot), 16)


def town_building(x0, y0, w, d, floors, wall, win, roof, awning=None, face=-1):
    h = floors * 3.3 + 1.2; box((x0, y0, h / 2), (w, d, h), wall); box((x0, y0, h + 0.25), (w + 0.4, d + 0.4, 0.5), roof)
    fx = x0 + face * (w / 2 + 0.02)                                               # windows on the street facade (facing x)
    for f in range(1, floors):
        for k in range(int(d / 2.4)):
            box((fx, y0 - d / 2 + 1.3 + k * 2.4, 1.8 + f * 3.3), (0.12, 1.1, 1.6), win if random.random() < 0.7 else roof)
            box((fx + face * 0.06, y0 - d / 2 + 1.3 + k * 2.4, 1.8 + f * 3.3 - 0.9), (0.1, 1.35, 0.16), roof)
    box((fx, y0, 1.6), (0.14, d * 0.7, 2.2), win)                                 # shop window
    if awning: box((fx + face * 0.8, y0, 3.0), (1.6, d * 0.8, 0.12), awning, (0, face * 0.25, 0))


def build(preset, sc, M, Hh):
    if preset not in NAMES: return False
    _T.clear(); random.seed(21)
    cam = Hh['cam']; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = 0.45
    dusk_world(sc, 1.0); outlines(sc)
    trunk = m_plain('trunk', (0.16, 0.09, 0.05), 0.9); leaf = m_plain('leaf', (0.03, 0.13, 0.05), 0.85); leaf2 = m_plain('leaf2', (0.05, 0.18, 0.06), 0.85)
    win = m_emis('win', (1.0, 0.7, 0.25), 2.6, (0.9, 0.7, 0.3)); dark = m_plain('dark', (0.04, 0.035, 0.045), 0.7)
    crystal = m_emis('crystal', (0.45, 0.06, 1.0), 0.9, (0.32, 0.05, 0.68), 0.15)
    if preset == 'b2_bus':                         # inside a flying bus at dusk
        floor = m_noise('busFloor', (0.06, 0.07, 0.09), (0.11, 0.12, 0.15), 30, 0.7, 0.1)
        wallm = m_plain('busWall', (0.62, 0.7, 0.8), 0.5); seat = m_noise('seat', (0.08, 0.2, 0.55), (0.12, 0.28, 0.68), 40, 0.8, 0.15)
        pole = m_plain('pole', (0.95, 0.75, 0.15), 0.25, 0.8); trim = m_plain('trim', (0.2, 0.22, 0.26), 0.4)
        L_, Wd, Hgt = 12.0, 2.6, 2.3
        box((0, 0, -0.05), (Wd, L_, 0.1), floor); box((0, 0, Hgt + 0.05), (Wd, L_, 0.1), wallm)
        for sx in (-1, 1):                         # side walls with window gaps
            box((sx * Wd / 2, 0, 0.45), (0.08, L_, 0.9), wallm); box((sx * Wd / 2, 0, Hgt - 0.2), (0.08, L_, 0.4), wallm)
            for k in range(7): box((sx * Wd / 2, -L_ / 2 + 0.6 + k * 1.75, 1.4), (0.08, 0.22, 1.0), trim)
        box((0, L_ / 2, Hgt / 2), (Wd, 0.08, Hgt), wallm); box((0, L_ / 2 - 0.02, 1.45), (1.9, 0.06, 0.9), m_emis('frontWin', (0.55, 0.4, 0.8), 0.9))
        for k in range(6):
            yy = -L_ / 2 + 1.4 + k * 1.75
            for sx in (-1, 1):
                x = sx * 0.78; box((x, yy, 0.5), (0.95, 0.75, 0.16), seat); box((x, yy - 0.34, 0.92), (0.95, 0.14, 0.8), seat)
                cyl((x, yy, 0.2), 0.05, 0.4, trim, v=8)
            cyl((0.32, yy - 0.5, Hgt / 2), 0.03, Hgt, pole, v=10)
        for k in range(5): box((0, -L_ / 2 + 2 + k * 2.2, Hgt - 0.02), (0.5, 1.2, 0.04), m_emis('lamp%d' % k, (1.0, 0.9, 0.75), 6))
        cl = m_plain('cloudB', (0.6, 0.45, 0.66), 1.0)
        for k in range(26):
            sx = random.choice([-1, 1]); p = Vector((sx * random.uniform(18, 70), random.uniform(-40, 60), random.uniform(-25, -6)))
            for j in range(5): ball(tuple(p + Vector((random.uniform(-6, 6), random.uniform(-6, 6), random.uniform(-1, 2)))), random.uniform(3, 6), cl, 2, (1, 1, 0.6))
        sunlight(10, 120, 3.0, (1.0, 0.62, 0.4)); bpy.ops.object.light_add(type='AREA', location=(0, 0, Hgt - 0.1)); L = bpy.context.object; L.data.energy = 220; L.data.size = 1.5; L.data.color = (1.0, 0.9, 0.78)
        cam(sc, (0.0, -L_ / 2 + 0.7, 1.45), (0.0, L_ / 2, 1.2), lens=17, focus=4.0, fstop=4)
    elif preset == 'b2_town':                      # street level, looking down the main street to the clock tower
        asphalt = m_noise('asphalt', (0.05, 0.05, 0.06), (0.1, 0.1, 0.11), 60, 0.75, 0.12)
        walk = m_brick('sidewalk', (0.42, 0.4, 0.38), (0.36, 0.34, 0.33), (0.25, 0.24, 0.23), 1.2, 0.5, 0.5)
        line = m_emis('laneLine', (0.95, 0.85, 0.4), 0.15, (0.85, 0.75, 0.3))
        plane((0, 60, 0), (9, 160), asphalt)
        for k in range(30): box((0, -8 + k * 6, 0.005), (0.18, 2.6, 0.01), line)
        for sx in (-1, 1): box((sx * 6.0, 60, 0.08), (3.0, 160, 0.16), walk); box((sx * 4.55, 60, 0.09), (0.12, 160, 0.18), m_plain('curb', (0.5, 0.5, 0.5), 0.8))
        walls = [m_brick('brick%d' % i, c1, c2, (0.55, 0.52, 0.48), 3.2) for i, (c1, c2) in enumerate([((0.42, 0.14, 0.08), (0.36, 0.11, 0.07)), ((0.55, 0.4, 0.25), (0.48, 0.34, 0.2)), ((0.3, 0.32, 0.36), (0.26, 0.28, 0.31)), ((0.62, 0.5, 0.36), (0.55, 0.43, 0.3))])]
        roof = m_plain('roofT', (0.12, 0.07, 0.05), 0.8)
        awn = [m_brick('awn%d' % i, c, (0.92, 0.9, 0.85), (0.92, 0.9, 0.85), 2.0, 0.5, 4.0) for i, c in enumerate([(0.7, 0.12, 0.1), (0.1, 0.35, 0.25), (0.15, 0.25, 0.6)])]
        for sx in (-1, 1):
            y = -4.0
            while y < 120:
                d = random.uniform(7, 11); w = 10; floors = random.choice([3, 4, 5, 6]) + (3 if y > 50 else 0)
                town_building(sx * (7.5 + w / 2), y + d / 2, w, d, floors, random.choice(walls), win, roof, random.choice(awn) if y < 40 else None, face=-sx)
                y += d + 0.3
        for y in (4, 16, 28, 40, 52):              # lamps
            for sx in (-1, 1): cyl((sx * 4.9, y, 2.4), 0.07, 4.8, dark, v=10); ball((sx * 4.6, y, 4.85), 0.28, m_emis('lampT', (1.0, 0.85, 0.55), 6))
        for (x, y, c) in [(-3.3, 9, (0.7, 0.15, 0.1)), (3.3, 20, (0.15, 0.35, 0.65)), (-3.3, 33, (0.85, 0.7, 0.3))]: car(x, y, 0, c, dark, m_plain('glassT', (0.2, 0.3, 0.45), 0.1))
        for k in range(6): cyl((random.choice([-1, 1]) * 5.2, random.uniform(2, 40), 0.55), 0.3, 1.1, m_plain('bin', (0.18, 0.3, 0.2), 0.6), v=12)
        tw = m_brick('tower', (0.72, 0.6, 0.42), (0.66, 0.54, 0.38), (0.5, 0.45, 0.36), 2.4)
        box((0, 132, 24), (7, 7, 48), tw); box((0, 132, 48.5), (8, 8, 1.0), roof); cone((0, 132, 54), 5.6, 10, m_plain('twR', (0.36, 0.1, 0.06), 0.7), 4, (0, 0, math.pi / 4))
        cyl((0, 128.4, 42), 2.3, 0.3, m_emis('clockT', (1.0, 0.92, 0.75), 2.5), (math.pi / 2, 0, 0), 32)
        sky_bits(Vector((0, 1500, 0)), 0.6); sunlight(9, 30, 4.5, (1.0, 0.62, 0.4)); sunlight(30, 200, 1.6, (0.55, 0.42, 1.0))
        cam(sc, (2.6, -10, 1.7), (0.6, 40, 5.5), lens=22, focus=14, fstop=5.6)
    elif preset == 'b2_crater':                    # standing inside the crater
        dirt = m_noise('craterDirt', (0.2, 0.12, 0.07), (0.33, 0.22, 0.12), 3, 0.95, 0.5)
        rim = m_noise('rimDirt', (0.45, 0.3, 0.16), (0.58, 0.42, 0.24), 2, 0.95, 0.5)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=160, location=(0, 40, 0)); gnd = bpy.context.object
        for v in gnd.data.vertices:
            x, y = v.co.x, v.co.y + 40; r = math.hypot(x, y - 30)
            v.co.z = (0.35 * math.sin(x * 0.4) * math.cos(y * 0.33)) + (0 if r < 36 else (r - 36) * 0.55) + 2.2 * math.exp(-((r - 44) / 4) ** 2)
        gnd.data.materials.append(dirt); bpy.ops.object.shade_smooth()
        meteor = m_emis('meteor', (0.45, 0.08, 1.0), 0.8, (0.34, 0.06, 0.72), 0.2)
        o = ball((0, 46, 5.6), 1, meteor, 1, (6.5, 5.5, 5.8), smooth=False)
        bpy.ops.object.light_add(type='POINT', location=(0, 38, 6)); L = bpy.context.object; L.data.energy = 6000; L.data.color = (0.55, 0.25, 1.0); L.data.shadow_soft_size = 4
        metal = m_plain('scaff', (0.75, 0.77, 0.82), 0.35, 0.6)
        for sx in (-1, 1):
            for sy in (-1, 1): cyl((sx * 8, 46 + sy * 8, 6), 0.18, 12, metal, v=8)
        for zz in (1.5, 6, 11.8):
            for (a, b, c, d) in [(-8, -8, 8, -8), (-8, 8, 8, 8), (-8, -8, -8, 8), (8, -8, 8, 8)]:
                L_ = math.hypot(c - a, d - b); cyl(((a + c) / 2, 46 + (b + d) / 2, zz), 0.14, L_, metal, (0, math.pi / 2, math.atan2(d - b, c - a)), 8)
        white = m_plain('dome', (0.88, 0.89, 0.92), 0.3)
        for dx, dy, r in [(-15, 40, 4.4), (16, 44, 5.2)]: ball((dx, dy, 0), r, white, 3, (1, 1, 0.62))
        for dx, dy, c in [(-9, 32, (0.7, 0.18, 0.1)), (-3, 30, (0.12, 0.25, 0.65)), (8, 31, (0.85, 0.6, 0.15)), (12, 35, (0.7, 0.18, 0.1))]:
            box((dx, dy, 1.2), (5, 2.4, 2.4), m_plain('cont%d' % dx, c, 0.55), (0, 0, random.uniform(-0.3, 0.3)))
        for k in range(55):                        # crystals of every size, big ones close to the camera
            a = random.uniform(0, math.tau); r = random.uniform(4, 34); x, y = math.cos(a) * r, 40 + math.sin(a) * r
            if abs(x) < 9 and 37 < y < 55: continue
            s = random.uniform(0.4, 1.3); cone((x, y, s), s * 0.5, s * 2.4, crystal, 5, (random.uniform(-0.35, 0.35), random.uniform(-0.35, 0.35), random.random()))
        for (x, y, s) in [(-2.6, 4.5, 1.1), (3.4, 6.5, 0.9), (-4.2, 8.5, 0.7), (1.0, 10, 0.55), (4.8, 3.6, 1.3)]:
            for j in range(3): cone((x + j * 0.35 * s, y, s * 0.8), s * 0.45, s * 2.2, crystal, 5, (random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.random()))
        rock = m_noise('rockC', (0.22, 0.2, 0.24), (0.33, 0.31, 0.35), 3, 0.85, 0.6)
        for k in range(30): a = random.uniform(0, math.tau); r = random.uniform(5, 30); ball((math.cos(a) * r, 40 + math.sin(a) * r, 0.1), random.uniform(0.3, 1.0), rock, 2, (1.3, 1, 0.6))
        walls = [m_brick('cbrick%d' % i, c1, c2, (0.5, 0.47, 0.43), 3.0) for i, (c1, c2) in enumerate([((0.55, 0.4, 0.25), (0.48, 0.34, 0.2)), ((0.42, 0.14, 0.08), (0.36, 0.11, 0.07))])]
        for k in range(9): x = -40 + k * 10 + random.uniform(-2, 2); h = random.uniform(12, 30); box((x, 112, 8 + h / 2), (8, 8, h), random.choice(walls)); box((x, 107.9, 8 + h * 0.6), (6, 0.1, h * 0.7), win)
        for k in range(40): x = random.uniform(-90, 90); y = random.uniform(90, 130); tree(x, y, 6, random.uniform(7, 12), trunk, leaf, leaf2)
        sky_bits(Vector((0, 1500, 0)), 0.6); sunlight(24, 25, 4.6, (1.0, 0.66, 0.44)); sunlight(30, 200, 1.8, (0.55, 0.42, 1.0))
        cam(sc, (1.5, -1, 1.6), (0, 46, 4.5), lens=20, focus=10, fstop=4)
    elif preset == 'b2_field':                     # the final circle: real grass, boulders, the mountain
        soil = m_noise('soil', (0.08, 0.14, 0.04), (0.14, 0.22, 0.07), 6, 0.95, 0.2)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=120, size=600, location=(0, 280, 0)); gnd = bpy.context.object
        for v in gnd.data.vertices: x, y = v.co.x, v.co.y + 280; v.co.z = 1.2 * math.sin(x * 0.03) * math.cos(y * 0.025) + 0.02 * max(0, y - 40)
        gnd.data.materials.append(soil); bpy.ops.object.shade_smooth()
        grass_patch((0, 9, 0.02), (26, 24), 900, 0.28, soil, 3)
        grass_patch((0, 32, 0.05), (60, 26), 220, 0.35, soil, 4)
        rock = m_noise('boulder', (0.42, 0.4, 0.44), (0.55, 0.53, 0.56), 2.5, 0.85, 0.7)
        for k in range(12): ball((6 + k * 2.6 + random.uniform(-1, 1), 52 + random.uniform(-3, 3), 0.4), random.uniform(1.6, 3.4), rock, 3, (1.4, 1.1, 0.75))
        for (x, y, s) in [(-3.5, 6, 0.6), (4.6, 9, 0.45), (-6, 14, 0.8)]: ball((x, y, 0.1), s, rock, 3, (1.3, 1.1, 0.7))
        for k in range(50):
            x, y = random.uniform(-120, 120), random.uniform(30, 200)
            if -20 < x < 50 and y < 70: continue
            tree(x, y, 0.02 * max(0, y - 40), random.uniform(7, 13), trunk, leaf, leaf2)
        bpy.ops.mesh.primitive_cone_add(radius1=160, depth=140, vertices=48, location=(-120, 520, 60)); mtn = bpy.context.object
        mtn.data.materials.append(m_noise('mtn', (0.14, 0.09, 0.15), (0.24, 0.17, 0.24), 0.04, 0.9, 0.3))
        d = mtn.modifiers.new('S', 'SUBSURF'); d.levels = 2; d2 = mtn.modifiers.new('D', 'DISPLACE'); tx = bpy.data.textures.new('mt', 'CLOUDS'); tx.noise_scale = 0.4; d2.texture = tx; d2.strength = 16
        sky_bits(Vector((0, 1500, 0)), 0.6); sunlight(10, 30, 4.2, (1.0, 0.62, 0.4)); sunlight(30, 200, 1.8, (0.55, 0.42, 1.0))
        cam(sc, (0.5, -3, 1.4), (2.5, 50, 3.2), lens=22, focus=12, fstop=4)
    elif preset == 'b2_drivein':                   # car level at the drive-in
        gravel = m_noise('gravel', (0.22, 0.2, 0.18), (0.4, 0.37, 0.33), 90, 0.95, 0.6, 4)
        plane((0, 60, 0), (200, 200), gravel)
        stone = m_noise('stone', (0.32, 0.3, 0.28), (0.5, 0.47, 0.43), 10, 0.9, 0.3)
        for k in range(500): x, y = random.uniform(-8, 8), random.uniform(1, 14); ball((x, y, 0.02), random.uniform(0.03, 0.09), stone, 1, (1.3, 1, 0.6))
        screen = m_emis('screenD', (0.7, 0.72, 1.0), 0.35, (0.75, 0.76, 0.95)); frame = m_plain('frameD', (0.08, 0.06, 0.1), 0.6)
        box((0, 60, 14), (34, 0.8, 15), frame); box((0, 59.55, 14), (32, 0.3, 13), screen)
        cyl((-4, 59.3, 16.5), 2.6, 0.2, m_emis('ssun', (1.0, 0.75, 0.25), 0.9), (math.pi / 2, 0, 0), 32)
        bpy.ops.mesh.primitive_cone_add(radius1=7, depth=0.1, vertices=3, location=(5, 59.32, 11), rotation=(math.pi / 2, 0, 0)); bpy.context.object.data.materials.append(m_emis('smtn', (0.45, 0.35, 0.9), 0.5))
        wood = m_planks('postWood', (0.3, 0.18, 0.09), (0.24, 0.14, 0.07), 2)
        for dx in (-13, -5, 5, 13): box((dx, 60.6, 3.5), (0.7, 0.7, 7), wood)
        glass = m_plain('glassD', (0.2, 0.3, 0.45), 0.1)
        for (x, y, c) in [(-4.5, 12, (0.75, 0.2, 0.12)), (3.5, 16, (0.85, 0.75, 0.45)), (-8, 24, (0.2, 0.45, 0.65)), (6, 26, (0.35, 0.6, 0.35)), (-1, 30, (0.8, 0.5, 0.2))]: car(x, y, random.uniform(-0.1, 0.1), c, dark, glass)
        for k in range(12): x = -10 + (k % 4) * 6.5; y = 8 + (k // 4) * 9; cyl((x + 2.4, y + 1.6, 0.7), 0.06, 1.4, dark, v=8); box((x + 2.4, y + 1.6, 1.45), (0.35, 0.2, 0.25), dark)
        for k in range(12): cone((random.uniform(-15, 15), random.uniform(18, 56), 1.2), random.uniform(0.4, 1.0), random.uniform(2, 4.5), crystal, 6, (random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), 0))
        for k in range(40): tree(random.uniform(-80, 80), random.uniform(70, 140), 0, random.uniform(7, 11), trunk, leaf, leaf2)
        sky_bits(Vector((0, 1500, 0)), 0.6); sunlight(6, 20, 3.8, (1.0, 0.6, 0.38)); sunlight(30, 200, 1.8, (0.55, 0.42, 1.0))
        cam(sc, (1.0, -2, 1.5), (0, 40, 6), lens=22, focus=12, fstop=4)
    glow(sc)
    return True
