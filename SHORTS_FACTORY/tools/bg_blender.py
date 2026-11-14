"""Placeholder 3D backgrounds (realistic lighting, soft shadows, depth of field) rendered with Blender Cycles.
Each preset is a small procedural scene. Output: 1242x2208 PNG (15 % bigger than 1080x1920, room for camera pushes).
Run:  $BLENDER -b --factory-startup -P tools/bg_blender.py -- <out_dir> [preset ...] [--spp 48] [--scale 1.0] [--fg-only] [--layers] [--extra presets.py]
--layers renders depth layers (sky/far/mid/fg/near + location.json) for the multiplane camera instead of one image.
Presets: valley_dawn, fort_wall, hillside_down, hwacha_closeup, battle_sunset
Swap these for your own images: put PNG/JPGs in <episode>/backgrounds/ and name them in script.json."""
import bpy, math, random, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else 'backgrounds'
SPP = int(argv[argv.index('--spp') + 1]) if '--spp' in argv else 48
SCALE = float(argv[argv.index('--scale') + 1]) if '--scale' in argv else 1.0
ALL = ['valley_dawn', 'fort_wall', 'hillside_down', 'hwacha_closeup', 'battle_sunset']
_VAL = {'--spp', '--scale', '--extra'}
_names = [a for i, a in enumerate(argv[1:], 1) if not a.startswith('--') and argv[i - 1] not in _VAL]
PRESETS = _names or ALL
# extra preset modules (e.g. tools/presets_fortnite.py) define build(preset, sc, M, helpers) -> True if handled
EXTRA = []
if '--extra' in argv:
    import importlib.util
    for path in argv[argv.index('--extra') + 1].split(','):
        spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); EXTRA.append(mod)
os.makedirs(OUT, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP
    sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4
    sc.render.resolution_x, sc.render.resolution_y = int(1242 * SCALE), int(2208 * SCALE)
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = -0.3
    sc.render.image_settings.file_format = 'PNG'
    return sc


def mat(name, base, rough=0.8, noise=None, noise_col=None, scale=8.0, bump=0.2):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = rough
    if noise_col:
        tex = nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = scale; tex.inputs['Detail'].default_value = 8
        ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (*base, 1); ramp.color_ramp.elements[1].color = (*noise_col, 1)
        nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        if bump:
            bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = bump
            nt.links.new(tex.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    return m


def sky(sc, elev, rot, strength=1.0, dust=1.0, air=1.0):
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    s = nt.nodes.new('ShaderNodeTexSky'); s.sky_type = 'NISHITA'
    s.sun_elevation = math.radians(elev); s.sun_rotation = math.radians(rot); s.dust_density = dust; s.air_density = air
    nt.links.new(s.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.22 * strength   # Nishita is physically bright
    bpy.ops.object.light_add(type='SUN'); sun = bpy.context.object
    sun.data.energy = 2.6 * strength; sun.data.angle = math.radians(2.5)
    sun.rotation_euler = (math.radians(90 - elev), 0, math.radians(rot + 180 - 90))
    sun.data.color = (1.0, 0.92, 0.82) if elev > 12 else (1.0, 0.72, 0.5)
    return sun


def terrain(size, sub, height, nscale, m, loc=(0, 0, 0), seed=1):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=sub, y_subdivisions=sub, size=size, location=loc)
    o = bpy.context.object
    tex = bpy.data.textures.new('T%d' % seed, 'CLOUDS'); tex.noise_scale = nscale; tex.noise_depth = 4
    d = o.modifiers.new('D', 'DISPLACE'); d.texture = tex; d.strength = height; d.texture_coords = 'GLOBAL'
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o


def cam(sc, loc, look, lens=32, focus=None, fstop=4.0):
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object
    d = Vector(look) - Vector(loc); c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens; c.data.sensor_fit = 'VERTICAL'; c.data.sensor_height = 24
    c.data.clip_end = 5000
    if focus:
        c.data.dof.use_dof = True; c.data.dof.focus_distance = focus; c.data.dof.aperture_fstop = fstop
    sc.camera = c; return c


def tree(x, y, z, h, m_trunk, m_leaf):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12 * h / 4, depth=h * 0.35, location=(x, y, z + h * 0.17)); bpy.context.object.data.materials.append(m_trunk)
    for k, (r, hh) in enumerate([(0.42, 0.45), (0.33, 0.62), (0.22, 0.8)]):
        bpy.ops.mesh.primitive_cone_add(radius1=r * h, depth=h * 0.45, location=(x, y, z + h * hh), vertices=10)
        bpy.context.object.data.materials.append(m_leaf); bpy.ops.object.shade_smooth()


def palisade(x0, x1, y, z, m, h=3.2, r=0.17, rot=0.0, fg=False):
    """fg=True: also written to <preset>_fg.png (alpha) so the compositor can draw it in front of the characters."""
    before = set(bpy.data.objects); x = x0; k = 0
    while x < x1:
        hh = h * (0.92 + 0.12 * random.random())
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=hh, location=(x, y, z + hh / 2), vertices=12)
        o = bpy.context.object; o.data.materials.append(m); o.rotation_euler = (random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), 0)
        bpy.ops.mesh.primitive_cone_add(radius1=r, depth=0.45, location=(x, y, z + hh + 0.22), vertices=12); bpy.context.object.data.materials.append(m)
        x += r * 2.05; k += 1
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, y - 0.2, z + h * 0.62)); o = bpy.context.object
    o.scale = ((x1 - x0) / 2 + 0.2, 0.06, 0.08); o.data.materials.append(m)
    if fg:
        for ob in set(bpy.data.objects) - before: ob['fg'] = True


def hwacha(loc, m_wood, m_dark, m_iron, scale=1.0, rotz=0.0):
    """A wheeled cart carrying a launcher box: a grid of tubes with rocket arrows sticking out."""
    root = bpy.data.objects.new('hwacha', None); bpy.context.scene.collection.objects.link(root)
    root.location = loc; root.rotation_euler = (0, 0, rotz); root.scale = (scale,) * 3
    def add(o): o.parent = root; return o
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.75)); o = add(bpy.context.object); o.scale = (0.55, 0.9, 0.06); o.data.materials.append(m_wood)
    for sx in (-0.75, 0.75):        # wheels with spokes
        bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.05, location=(sx, 0, 0.6), rotation=(0, math.pi / 2, 0)); add(bpy.context.object).data.materials.append(m_wood)
        for k in range(8):
            a = k / 8 * math.pi
            bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=1.08, location=(sx, 0, 0.6), rotation=(a, 0, 0)); add(bpy.context.object).data.materials.append(m_wood)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.18, location=(sx, 0, 0.6), rotation=(0, math.pi / 2, 0)); add(bpy.context.object).data.materials.append(m_iron)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=1.6, location=(0, 0, 0.6), rotation=(0, math.pi / 2, 0)); add(bpy.context.object).data.materials.append(m_iron)
    for sx in (-0.35, 0.35):        # shafts
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx, 1.35, 0.55)); o = add(bpy.context.object); o.scale = (0.04, 0.8, 0.04); o.rotation_euler = (math.radians(-12), 0, 0); o.data.materials.append(m_wood)
    # launcher box, tilted up, 10 x 10 holes with arrows
    box = bpy.data.objects.new('box', None); bpy.context.scene.collection.objects.link(box); box.parent = root
    box.location = (0, -0.05, 1.25); box.rotation_euler = (math.radians(-28), 0, 0)
    def addb(o): o.parent = box; return o
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); o = addb(bpy.context.object); o.scale = (0.55, 0.5, 0.42); o.data.materials.append(m_wood)
    for i in range(10):
        for j in range(8):
            x, z = -0.47 + i * 0.105, -0.34 + j * 0.097
            bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.04, location=(x, -0.51, z), rotation=(math.pi / 2, 0, 0), vertices=10); addb(bpy.context.object).data.materials.append(m_dark)
            if (i + j) % 3 != 0:
                bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.5, location=(x, -0.7, z), rotation=(math.pi / 2, 0, 0), vertices=6); addb(bpy.context.object).data.materials.append(m_wood)
                bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.12, location=(x, -0.5, z), rotation=(math.pi / 2, 0, 0), vertices=8); addb(bpy.context.object).data.materials.append(m_iron)
    return root


def common_mats():
    return dict(
        grass=mat('grass', (0.18, 0.32, 0.09), 0.9, True, (0.32, 0.42, 0.14), 3.0, 0.3),
        dirt=mat('dirt', (0.24, 0.16, 0.09), 0.95, True, (0.34, 0.24, 0.14), 6.0, 0.4),
        rock=mat('rock', (0.36, 0.35, 0.34), 0.85, True, (0.5, 0.48, 0.45), 2.0, 0.6),
        mount=mat('mount', (0.22, 0.27, 0.24), 0.9, True, (0.38, 0.4, 0.36), 1.0, 0.2),
        wood=mat('wood', (0.2, 0.11, 0.05), 0.75, True, (0.32, 0.19, 0.09), 14.0, 0.3),
        dark=mat('dark', (0.04, 0.03, 0.03), 0.9), iron=mat('iron', (0.15, 0.15, 0.16), 0.45),
        trunk=mat('trunk', (0.2, 0.13, 0.08), 0.9), leaf=mat('leaf', (0.07, 0.17, 0.06), 0.85, True, (0.13, 0.25, 0.08), 5.0, 0.2),
        water=mat('water', (0.12, 0.22, 0.28), 0.08), cloth=mat('cloth', (0.62, 0.1, 0.08), 0.8),
        smoke=None,
    )


def build(preset):
    random.seed(7)
    sc = reset(); M = common_mats()
    for mod in EXTRA:
        if mod.build(preset, sc, M, globals()): return sc
    if preset == 'valley_dawn':          # wide establishing: a mountain valley, river, a road winding toward a hill
        sky(sc, 9, 70, 1.0, dust=2.0)
        terrain(400, 160, 8, 30, M['grass'], seed=1)
        for i, (x, y, s) in enumerate([(-160, 420, 140), (60, 520, 190), (240, 460, 150), (-300, 300, 120), (300, 260, 110)]):
            terrain(s * 2.4, 90, s, s * 0.45, M['mount'], (x, y, -10), seed=10 + i)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(10, 120, 0.35)); o = bpy.context.object; o.scale = (6, 140, 1); o.rotation_euler = (0, 0, 0.25); o.data.materials.append(M['water'])
        bpy.ops.mesh.primitive_plane_add(size=1, location=(-12, 60, 0.4)); o = bpy.context.object; o.scale = (2.4, 140, 1); o.rotation_euler = (0, 0, -0.08); o.data.materials.append(M['dirt'])
        for _ in range(260):
            x, y = random.uniform(-160, 160), random.uniform(10, 300)
            if abs(x + 12 + (y - 60) * 0.08) < 6 or abs(x - 10 + (y - 120) * -0.25) < 9: continue
            tree(x, y, 0, random.uniform(5, 9), M['trunk'], M['leaf'])
        terrain(120, 60, 30, 25, M['grass'], (-30, 260, 0), seed=3)   # the fort hill in the distance
        cam(sc, (-6, -14, 7), (-14, 80, 8), lens=28, focus=60, fstop=8)
    elif preset == 'fort_wall':          # inside the hilltop fort: a palisade behind, packed earth, a banner
        sky(sc, 22, 200, 1.0)
        bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0)); bpy.context.object.data.materials.append(M['dirt'])
        palisade(-14, 14, 6, 0, M['wood']); palisade(-14, 14, 6.4, 0, M['wood'], h=3.6, r=0.19)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=7, location=(3.5, 4.5, 3.5)); bpy.context.object.data.materials.append(M['wood'])
        bpy.ops.mesh.primitive_plane_add(size=1, location=(4.3, 4.5, 5.6)); o = bpy.context.object; o.scale = (0.8, 1.2, 1); o.rotation_euler = (math.pi / 2, 0, 0); o.data.materials.append(M['cloth'])
        for x in (-6, -1.5, 7):
            hwacha((x, 4.4, 0), M['wood'], M['dark'], M['iron'], 0.9, math.pi)
        for _ in range(40):
            tree(random.uniform(-90, 90), random.uniform(40, 120), random.uniform(-8, 4), random.uniform(6, 10), M['trunk'], M['leaf'])
        terrain(500, 80, 40, 60, M['mount'], (0, 260, -30), seed=4)
        cam(sc, (0.6, -7.5, 1.6), (0.2, 6, 2.3), lens=30, focus=8.5, fstop=5.6)
    elif preset == 'hillside_down':      # from the wall, looking down the steep slope to the valley
        sky(sc, 18, 20, 1.0, dust=1.5)
        slope = math.radians(14)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=80, size=1, location=(0, 60, -60 * math.tan(slope) - 1.6))
        o = bpy.context.object; o.scale = (220, 130, 1); o.rotation_euler = (-slope, 0, 0)
        tx = bpy.data.textures.new('slope', 'CLOUDS'); tx.noise_scale = 6; d = o.modifiers.new('D', 'DISPLACE'); d.texture = tx; d.strength = 1.5
        o.data.materials.append(M['grass']); bpy.ops.object.shade_smooth()
        terrain(900, 160, 8, 40, M['grass'], (0, 330, -32.6), seed=5)
        for _ in range(240):
            y = random.uniform(13, 110); z = -y * math.tan(slope) - 1.6
            x = random.uniform(-70, 70) if random.random() < 0.5 else random.uniform(-14, 14)
            if abs(x) < 2.2 + y * 0.05 and y < 60: continue                      # leave the charge lane open
            tree(x, y, z - 0.5, random.uniform(5, 8), M['trunk'], M['leaf'])
        for i in range(6): terrain(320, 80, 90, 100, M['mount'], (-400 + i * 160, 620, -60), seed=20 + i)
        palisade(-6, 6, -1.6, -1.64, M['wood'], h=2.3, fg=True)
        cam(sc, (0.4, -4.8, 3.4), (0, 40, -21), lens=26, focus=30, fstop=11)
    elif preset == 'hwacha_closeup':     # the mechanism, close: a hwacha on the packed earth, wall behind
        sky(sc, 30, 230, 1.0)
        bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0)); bpy.context.object.data.materials.append(M['dirt'])
        hwacha((0, 0, 0), M['wood'], M['dark'], M['iron'], 1.0, math.radians(-25))
        palisade(-8, 8, 4.5, 0, M['wood'], h=3.6, r=0.2)
        cam(sc, (1.9, -3.4, 1.35), (0.05, -0.2, 1.15), lens=34, focus=3.8, fstop=2.4)
    elif preset == 'battle_sunset':      # smoke and sunset over the hill after the battle
        sky(sc, 2.5, 260, 1.2, dust=4.0, air=1.4)
        terrain(400, 140, 6, 30, M['grass'], seed=6)
        terrain(140, 70, 34, 30, M['grass'], (10, 120, 0), seed=7)
        for _ in range(120): tree(random.uniform(-120, 120), random.uniform(20, 90), 0, random.uniform(5, 9), M['trunk'], M['leaf'])
        cam(sc, (0, -10, 3.5), (6, 120, 26), lens=30, focus=80, fstop=8)
    return sc


def render_layers(sc, p):
    """Depth layers for the multiplane camera: the scene is cut into 5 distance bands with the camera clip range
    (sky / far / mid / fg / near). Each band's far edge is feathered with the mist pass so seams blend. Images are
    30 % larger than the frame (same focal length, wider field of view). Writes <out>/<p>/<band>.png + location.json."""
    import json
    cam = sc.camera; d = cam.data.dof.focus_distance if cam.data.dof.use_dof else 20.0
    B = [0.01, 0.21 * d, 0.58 * d, 1.63 * d, 4.2 * d, 1.0e6]
    names, zs = ['near', 'fg', 'mid', 'far', 'sky'], [20, 50, 150, 400, 1000]
    od = os.path.join(OUT, p); os.makedirs(od, exist_ok=True)
    cam.data.sensor_height = 24 * 1.3; cam.data.clip_end = 1.0e6
    sc.render.resolution_x, sc.render.resolution_y = int(1404 * SCALE), int(2496 * SCALE)
    sc.view_layers[0].use_pass_mist = True; sc.world.mist_settings.falloff = 'LINEAR'
    sc.render.image_settings.color_mode = 'RGBA'; sc.render.use_compositing = True
    layers = []
    for k, name in enumerate(names):
        lo, hi = B[k], B[k + 1]
        cam.data.clip_start = max(0.01, lo * 0.97)
        sc.use_nodes = True; nt = sc.node_tree; nt.nodes.clear()
        rl = nt.nodes.new('CompositorNodeRLayers'); comp = nt.nodes.new('CompositorNodeComposite')
        img = rl.outputs['Image']
        if sc.get('glow'):                          # keep the preset's bloom in every band
            gl = nt.nodes.new('CompositorNodeGlare'); gl.glare_type = 'FOG_GLOW'; gl.quality = 'MEDIUM'; gl.threshold, gl.mix = sc['glow'][0], sc['glow'][1]; gl.size = 8
            nt.links.new(img, gl.inputs['Image']); img = gl.outputs['Image']
        if name == 'sky':
            sc.render.film_transparent = False; nt.links.new(img, comp.inputs['Image'])
        else:
            sc.render.film_transparent = True
            sc.world.mist_settings.start = hi; sc.world.mist_settings.depth = 0.25 * hi; cam.data.clip_end = hi * 1.25
            inv = nt.nodes.new('CompositorNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
            nt.links.new(rl.outputs['Mist'], inv.inputs[1])
            sa = nt.nodes.new('CompositorNodeSetAlpha'); sa.mode = 'APPLY'
            nt.links.new(img, sa.inputs['Image']); nt.links.new(inv.outputs[0], sa.inputs['Alpha'])
            nt.links.new(sa.outputs['Image'], comp.inputs['Image'])
        f = os.path.join(od, name + '.png'); sc.render.filepath = f
        bpy.ops.render.render(write_still=True); cam.data.clip_end = 1.0e6
        im = bpy.data.images.load(f); px = im.pixels[:]; w, h = im.size
        cover = sum(1 for i in range(3, len(px), 4 * 97) if px[i] > 0.02) / (len(px) / (4 * 97))
        if name == 'sky':   # sky colour for the atmosphere tint: average of the top 6 % rows
            n = 0; acc = [0, 0, 0]
            for y in range(int(h * 0.94), h, 3):
                for x in range(0, w, 7): i = (y * w + x) * 4; acc[0] += px[i]; acc[1] += px[i + 1]; acc[2] += px[i + 2]; n += 1
            skyhex = '#%02x%02x%02x' % tuple(int(255 * min(1, c / n)) for c in acc)
        bpy.data.images.remove(im)
        if name != 'sky' and cover < 0.002: os.remove(f); print('empty band', p, name, flush=True); continue
        layers.append(dict(name=name, img=p + '/' + name + '.png', z=zs[k]))
        print('rendered', p, name, 'cover %.2f' % cover, flush=True)
    sc.use_nodes = False
    json.dump(dict(layers=layers[::-1], sky=skyhex, focus='mid', focus_m=d), open(os.path.join(od, 'location.json'), 'w'), indent=1)


for p in PRESETS:
    sc = build(p)
    if '--layers' in argv:
        render_layers(sc, p); continue
    if '--fg-only' not in argv:
        sc.render.filepath = os.path.join(OUT, p + '.png')
        bpy.ops.render.render(write_still=True)
        print('rendered', p, flush=True)
    fg = [o for o in sc.objects if o.get('fg')]
    if fg:                       # foreground layer: same camera, everything else held out, transparent film
        sc.render.film_transparent = True
        for o in sc.objects:
            if o.type == 'MESH' and not o.get('fg'): o.is_holdout = True
        sc.render.image_settings.color_mode = 'RGBA'
        sc.render.filepath = os.path.join(OUT, p + '_fg.png')
        bpy.ops.render.render(write_still=True)
        print('rendered', p + '_fg', flush=True)
