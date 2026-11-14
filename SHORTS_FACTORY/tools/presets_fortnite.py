"""Locations for the 'teleported into a battle royale' episode. Original designs (no game assets copied):
fn_sky (high above an island), fn_town (a street of tall towers), fn_crater (a fresh comet crater with a research
lab and glowing purple rocks), fn_field (rolling hills, final circle), fn_drivein (a wrecked drive-in cinema),
fn_lobby (a stage platform under lights).  Used by tools/bg_blender.py --extra tools/presets_fortnite.py"""
import bpy, math, random
from mathutils import Vector

NAMES = ['fn_sky', 'fn_town', 'fn_crater', 'fn_field', 'fn_drivein', 'fn_lobby']


def emis(name, col, strength=4.0, base=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(base or col), 1); b.inputs['Roughness'].default_value = 0.35
    b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = strength
    return m


def box(loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object
    o.scale = size; o.data.materials.append(m); return o


def cyl(loc, r, d, m, rot=(0, 0, 0), v=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=v); o = bpy.context.object
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o


def ball(loc, r, m, sub=3, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc); o = bpy.context.object
    o.scale = scale; o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o


def cloud(x, y, z, r, m):
    for k in range(7):
        ball((x + random.uniform(-1.2, 1.2) * r, y + random.uniform(-0.5, 0.5) * r, z + random.uniform(-0.2, 0.35) * r),
             r * random.uniform(0.55, 1.0), m, 2, (1, 0.8, 0.62))


def shaped_ground(size, sub, m, fn, loc=(0, 0, 0)):
    """a grid whose height is fn(x, y) in world space"""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=sub, y_subdivisions=sub, size=size, location=loc); o = bpy.context.object
    for v in o.data.vertices:
        wx, wy = v.co.x + loc[0], v.co.y + loc[1]; v.co.z = fn(wx, wy)
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o


def car(x, y, rot, col, M, H):
    body = H['mat']('car%.0f%.0f' % (x, y), col, 0.35)
    box((x, y, 0.75), (1.0, 2.1, 0.45), body, (0, 0, rot))
    box((x - math.sin(rot) * -0.2, y + math.cos(rot) * -0.2, 1.35), (0.85, 1.1, 0.35), body, (0, 0, rot))
    for sx in (-1, 1):
        for sy in (-1, 1):
            dx, dy = sx * 0.95, sy * 1.35; c, s = math.cos(rot), math.sin(rot)
            cyl((x + dx * c - dy * s, y + dx * s + dy * c, 0.38), 0.38, 0.3, M['dark'], (0, math.pi / 2, rot))


def build(preset, sc, M, H):
    if preset not in NAMES: return False
    mat, sky, cam, tree, terrain = H['mat'], H['sky'], H['cam'], H['tree'], H['terrain']
    white = mat('cloud', (0.95, 0.95, 0.97), 1.0)
    purple = emis('purple', (0.45, 0.05, 1.0), 2.2, (0.3, 0.04, 0.55))
    concrete = mat('concrete', (0.2, 0.19, 0.18), 0.85, True, (0.27, 0.26, 0.25), 9.0, 0.15)
    asphalt = mat('asphalt', (0.07, 0.07, 0.08), 0.8, True, (0.12, 0.12, 0.13), 30.0, 0.1)
    metal = mat('metal', (0.62, 0.64, 0.68), 0.3)
    if preset == 'fn_sky':                       # high above the island, clouds at every depth
        sky(sc, 32, 40, 1.15, dust=0.4)
        sea = mat('sea', (0.02, 0.16, 0.3), 0.12)
        bpy.ops.mesh.primitive_plane_add(size=9000, location=(0, 900, -420)); bpy.context.object.data.materials.append(sea)
        sand = mat('sand', (0.62, 0.52, 0.34), 0.9)
        ball((0, 900, -432), 1, sand, 4, (430, 360, 18))
        isl = ball((0, 900, -425), 1, M['grass'], 5, (400, 330, 22))
        d = isl.modifiers.new('D', 'DISPLACE'); tx = bpy.data.textures.new('isl', 'CLOUDS'); tx.noise_scale = 0.25; d.texture = tx; d.strength = 0.25
        lake = mat('lake', (0.04, 0.22, 0.34), 0.1); cyl((-120, 980, -403.5), 45, 1, lake, v=48)
        crater = mat('crater', (0.16, 0.12, 0.1), 0.95); cyl((110, 800, -403.6), 28, 1, crater, v=40); ball((110, 800, -403), 7, purple, 2, (1, 1, 0.25))
        town_cols = [(0.55, 0.22, 0.16), (0.75, 0.7, 0.6), (0.3, 0.5, 0.55), (0.8, 0.8, 0.78)]
        for k in range(26):
            box((random.uniform(-30, 30) + 20, 1020 + random.uniform(-25, 25), -400 + 2), (random.uniform(4, 8), random.uniform(4, 8), random.uniform(4, 22)), mat('tw%d' % k, random.choice(town_cols), 0.8))
        for k in range(40): tree(random.uniform(-300, 300), 900 + random.uniform(-250, 250), -404, random.uniform(10, 16), M['trunk'], M['leaf'])
        for (dist, n, r) in [(28, 3, 5), (60, 4, 9), (130, 6, 18), (300, 7, 35), (600, 8, 60)]:
            for k in range(n):
                a = random.uniform(-0.9, 0.9); cloud(math.sin(a) * dist * 1.1, dist * math.cos(a) + 10, random.uniform(-0.45, -0.05) * dist, r, white)
        cam(sc, (0, 0, 0), (0, 700, -175), lens=30, focus=120, fstop=16)
    elif preset == 'fn_town':                    # a street between tall towers
        sky(sc, 40, 125, 1.1, dust=0.8)
        bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 100, 0)); bpy.context.object.data.materials.append(asphalt)
        box((0, 40, 0.06), (10, 90, 0.06), concrete)
        win = emis('window', (0.25, 0.42, 0.6), 0.6, (0.08, 0.12, 0.2))
        cols = [(0.5, 0.2, 0.14), (0.78, 0.72, 0.6), (0.24, 0.45, 0.5), (0.85, 0.84, 0.8), (0.62, 0.42, 0.26)]
        for side in (-1, 1):
            y = 2.0
            while y < 110:
                w = random.uniform(8, 13); h = random.choice([9, 12, 15, 22, 30, 38]) * (1.3 if y > 25 else 1); x = side * (11 + w / 2)
                bm = mat('b%.0f%d' % (y, side), random.choice(cols), 0.85, True, (0.3, 0.28, 0.26), 4.0, 0.2)
                box((x, y + w / 2, h / 2), (w, w, h), bm)
                box((x, y + w / 2, h + 0.25), (w + 0.4, w + 0.4, 0.5), M['dark'])
                fx = side * 11 - side * 0.02
                for fy in range(1, int(h / 3.2)):
                    for wy in range(int(w / 2.4)):
                        box((fx, y + 1.2 + wy * 2.4, fy * 3.2), (0.12, 1.1, 1.5), win)
                y += w + random.uniform(1, 4)
        for y in (6, 20, 34, 50, 68):
            for sx in (-1, 1): cyl((sx * 8.5, y, 2.5), 0.09, 5, M['dark']); ball((sx * 8.5 - sx * 0.5, y, 5.0), 0.25, emis('lamp', (1, 0.85, 0.6), 3))
        for y in (10, 28, 44): tree(-7.5, y, 0, 5.5, M['trunk'], M['leaf']); tree(7.5, y + 6, 0, 5.5, M['trunk'], M['leaf'])
        terrain(1500, 60, 60, 300, M['mount'], (0, 1250, -10), seed=3)
        cam(sc, (0.5, -8, 2.0), (0, 30, 7.5), lens=24, focus=22, fstop=8)
    elif preset == 'fn_crater':                  # a fresh comet crater, a small lab in the middle, purple rocks
        sky(sc, 22, 210, 1.1, dust=1.2)
        R, D, cy = 34.0, 10.0, 46.0
        def hgt(x, y):
            r = math.hypot(x, y - cy); n = math.sin(x * 0.23) * math.cos(y * 0.19) * 0.4
            if r < R: return -D * (1 - (r / R) ** 2) + 1.6 * math.exp(-((r - R) / 3.5) ** 2) + n
            return 1.6 * math.exp(-((r - R) / 6.0) ** 2) + n * 2 + 0.002 * (y - cy) * 3
        dirtgrass = mat('dg', (0.12, 0.08, 0.05), 0.95, True, (0.12, 0.2, 0.06), 0.35, 0.35)
        shaped_ground(260, 200, dirtgrass, hgt, (0, cy, 0))
        cyl((0, cy, -D + 1.2), 4.5, 2.4, metal, v=40); ball((0, cy, -D + 2.4), 4.4, mat('dome', (0.85, 0.86, 0.88), 0.25), 4, (1, 1, 0.6))
        ball((7, cy + 3, -D + 1.6), 2.5, mat('dome2', (0.85, 0.86, 0.88), 0.25), 4, (1, 1, 0.6)); cyl((-6, cy - 2, -D + 4), 0.9, 8, metal)
        box((-6, cy - 2, -D + 8.4), (2.6, 2.6, 0.5), M['dark']); box((5, cy - 5, -D + 1.6), (4, 2.5, 2.4), mat('lab', (0.7, 0.72, 0.75), 0.4))
        for k in range(90):
            a = random.uniform(0, math.tau); r = R * math.sqrt(random.uniform(0.04, 1.0)) * 0.95
            x, y = math.cos(a) * r, cy + math.sin(a) * r
            if math.hypot(x, y - cy) < 9: continue
            s = random.uniform(0.6, 1.9); o = ball((x, y, hgt(x, y) + s * 0.4), s, purple, 1, (1, random.uniform(0.7, 1.2), random.uniform(0.6, 0.9)))
            o.rotation_euler = (random.random(), random.random(), random.random())
        for k in range(30): tree(random.uniform(-90, 90), cy + R + random.uniform(10, 80), 0.5, random.uniform(5, 8), M['trunk'], M['leaf'])
        terrain(1500, 60, 50, 300, M['mount'], (0, 1250, -6), seed=8)
        cam(sc, (0, 6, 13), (0, 44, -7), lens=22, focus=36, fstop=11)
    elif preset == 'fn_field':                   # rolling hills, a rocky hill in the distance (the final circle)
        sky(sc, 28, 70, 1.15, dust=0.7)
        hill = lambda x, y: 0.9 * math.sin(x * 0.07) * math.cos(y * 0.05) + 7 * math.exp(-((x - 14) ** 2 + (y - 70) ** 2) / 300) + 0.02 * max(0, y - 20)
        shaped_ground(400, 180, M['grass'], hill, (0, 80, 0))
        for k in range(8): ball((14 + random.uniform(-6, 6), 70 + random.uniform(-5, 5), hill(14, 70) + random.uniform(-1, 1)), random.uniform(1.5, 3), M['rock'], 2, (1.3, 1, 0.7))
        for k in range(60):
            x, y = random.uniform(-80, 80), random.uniform(25, 160)
            if abs(x) < 12 and y < 60: continue
            tree(x, y, hill(x, y) - 0.3, random.uniform(5, 9), M['trunk'], M['leaf'])
        for k in range(14): ball((random.uniform(-6, 6), random.uniform(6, 22), 0.1), random.uniform(0.3, 0.7), M['rock'], 2, (1.2, 1, 0.6))
        terrain(1600, 60, 70, 350, M['mount'], (0, 1300, -10), seed=5)
        cam(sc, (0, -6, 1.9), (0, 40, 3.2), lens=26, focus=26, fstop=8)
    elif preset == 'fn_drivein':                 # a wrecked drive-in cinema at dusk, purple comet shards
        sky(sc, 6, 250, 1.0, dust=2.0)
        gravel = mat('gravel', (0.3, 0.27, 0.23), 0.95, True, (0.4, 0.36, 0.3), 25.0, 0.3)
        bpy.ops.mesh.primitive_plane_add(size=500, location=(0, 100, 0)); bpy.context.object.data.materials.append(gravel)
        screen = emis('screen', (0.9, 0.9, 0.85), 0.8, (0.85, 0.85, 0.82))
        box((0, 48, 11), (26, 0.4, 12), screen); box((0, 48.4, 11), (27.2, 0.6, 13.2), M['wood'])
        for x in (-11, -4, 4, 11): box((x, 48.8, 2.5), (0.6, 0.6, 5), M['wood'])
        for row, y in enumerate((14, 22, 30)):
            for x in (-12, -6, 0, 6, 12):
                cyl((x + 2.6, y + 1.5, 0.7), 0.06, 1.4, M['dark'])
                if random.random() < 0.6: car(x + random.uniform(-0.6, 0.6), y, random.uniform(-0.15, 0.15), random.choice([(0.7, 0.2, 0.15), (0.2, 0.45, 0.6), (0.85, 0.75, 0.4), (0.4, 0.6, 0.35)]), M, H)
        for k in range(9):
            bpy.ops.mesh.primitive_cone_add(radius1=random.uniform(0.4, 1.2), depth=random.uniform(2, 5), vertices=6,
                                            location=(random.uniform(-14, 14), random.uniform(18, 46), 1.0), rotation=(random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), 0))
            bpy.context.object.data.materials.append(purple)
        for k in range(30): tree(random.uniform(-80, 80), random.uniform(60, 140), 0, random.uniform(6, 10), M['trunk'], M['leaf'])
        cam(sc, (0, -6, 2.6), (0, 40, 7), lens=24, focus=22, fstop=8)
    elif preset == 'fn_lobby':                   # a round stage platform under coloured lights
        w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
        w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.03, 0.09, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
        floor = mat('floor', (0.05, 0.06, 0.12), 0.3)
        bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0)); bpy.context.object.data.materials.append(floor)
        cyl((0, 0, 0.25), 3.2, 0.5, mat('plat', (0.75, 0.78, 0.85), 0.2), v=64)
        bpy.ops.mesh.primitive_torus_add(major_radius=3.2, minor_radius=0.06, location=(0, 0, 0.5)); bpy.context.object.data.materials.append(emis('ring', (0.2, 0.7, 1.0), 8))
        back = mat('back', (0.06, 0.08, 0.2), 0.6)
        bpy.ops.mesh.primitive_cylinder_add(radius=22, depth=30, location=(0, 0, 10), vertices=64); o = bpy.context.object; o.data.materials.append(back)
        for k in range(40):
            box((random.uniform(-16, 16), random.uniform(6, 20), random.uniform(2, 16)), (random.uniform(0.3, 1.2),) * 3,
                emis('fl%d' % k, random.choice([(0.25, 0.5, 1.0), (0.7, 0.3, 1.0), (1.0, 0.75, 0.25)]), 2.5), (random.random(), random.random(), random.random()))
        for (x, c, e) in [(-6, (0.4, 0.5, 1.0), 900), (6, (0.8, 0.4, 1.0), 900), (0, (1.0, 0.9, 0.8), 600)]:
            bpy.ops.object.light_add(type='SPOT', location=(x, -6, 9)); L = bpy.context.object; L.data.energy = e; L.data.color = c
            L.data.spot_size = 0.7; L.rotation_euler = (Vector((0, 0, 1)) - Vector((x, -6, 9))).to_track_quat('-Z', 'Y').to_euler()
        cam(sc, (0, -15, 3.2), (0, 0, 2.2), lens=35, focus=15, fstop=5.6)
        bpy.ops.object.light_add(type='AREA', location=(0, -3, 7)); L = bpy.context.object; L.data.energy = 900; L.data.size = 5
    return True
