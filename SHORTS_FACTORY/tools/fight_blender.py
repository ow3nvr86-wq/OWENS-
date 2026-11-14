"""The 3D fight shot: the field world with a moving camera (orbit, crane, whip, push), rendered as a 60 fps image
sequence, plus camera.json (camera position, rotation and field of view for every frame) so the engine can pin 2D
characters to 3D positions while the camera moves around them.
Run: $BLENDER -b --factory-startup -P tools/fight_blender.py -- <out_dir> [--frames 241] [--scale 0.6] [--spp 10] [--only N]"""
import bpy, math, sys, os, json, importlib.util
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0]; arg = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
NF, SCALE, SPP, ONLY = arg('--frames', 241), arg('--scale', 0.6), arg('--spp', 10), arg('--only', -1)
FREESTYLE = '--no-lines' not in argv
FPS = 60
HERE = os.path.dirname(os.path.abspath(__file__))
s_ = importlib.util.spec_from_file_location('presets_fn2', os.path.join(HERE, 'presets_fn2.py')); F2 = importlib.util.module_from_spec(s_); s_.loader.exec_module(F2)
os.makedirs(OUT, exist_ok=True)

# the cast in world space (metres): the hero in the grass, the sniper on a boulder
HERO = Vector((0.0, 8.0, 0.0)); SNIPER = Vector((5.0, 20.0, 1.15))
# camera keys: (time s, camera position, look-at point, lens mm)
KEYS = [(0.00, (-2.6, 3.2, 0.7), (0.0, 8.0, 1.0), 20),
        (0.95, (-3.0, 4.2, 0.6), (0.0, 8.0, 1.1), 20),
        (1.60, (-3.3, 5.0, 1.1), (0.2, 8.0, 3.0), 19),
        (2.30, (-1.7, 3.6, 3.8), (4.0, 18.0, 2.2), 20),
        (3.20, (-0.6, 5.4, 4.1), (5.0, 20.0, 1.5), 22),
        (4.02, (-0.2, 6.4, 4.0), (5.0, 20.0, 1.8), 24)]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 4
sc.render.resolution_x, sc.render.resolution_y = int(1080 * SCALE), int(1920 * SCALE)
sc.view_settings.view_transform = 'AgX'; sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 0, NF - 1


def camfn(sc_, loc, look, lens=32, focus=None, fstop=4.0):
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; c.data.lens = lens; c.data.sensor_fit = 'VERTICAL'; c.data.sensor_height = 24
    c.data.clip_end = 1e6; sc_.camera = c; return c


F2.build('b2_field', sc, {}, {'cam': camfn})
soil = bpy.data.materials.get('soil')                              # the ground between grass patches reads as short lawn
if soil:
    rp = [n for n in soil.node_tree.nodes if n.type == 'VALTORGB'][0]; rp.color_ramp.elements[0].color = (0.1, 0.22, 0.05, 1); rp.color_ramp.elements[1].color = (0.18, 0.33, 0.08, 1)
    F2.grass_patch((14, 16, 0.03), (22, 26), 300, 0.3, soil, 7)
    F2.grass_patch((-14, 14, 0.03), (16, 22), 240, 0.3, soil, 8)
rock = F2.m_noise('boulderS', (0.42, 0.4, 0.44), (0.55, 0.53, 0.56), 2.5, 0.85, 0.7)
F2.ball((SNIPER.x, SNIPER.y, 0.0), 1.6, rock, 3, (1.4, 1.1, 0.75))
F2.ball((SNIPER.x + 2.2, SNIPER.y + 1.0, 0.0), 1.1, rock, 3, (1.3, 1.1, 0.7))
sc.render.use_freestyle = FREESTYLE
cam = sc.camera; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 5.6
tgt = bpy.data.objects.new('camTarget', None); sc.collection.objects.link(tgt)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
cam.data.dof.focus_object = tgt
for (t, p, l, lens) in KEYS:
    f = round(t * FPS); cam.location = p; cam.keyframe_insert('location', frame=f); tgt.location = l; tgt.keyframe_insert('location', frame=f)
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
for ob in (cam, tgt, cam.data):                                   # ease every move in and out
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.easing = 'AUTO'
# camera track for the engine
track = []
for f in range(NF):
    sc.frame_set(f); M = cam.matrix_world
    track.append(dict(C=[round(v, 5) for v in M.translation], R=[[round(M[r][c], 6) for c in range(3)] for r in range(3)], tanh=round(12.0 / cam.data.lens, 6)))
json.dump(dict(fps=FPS, frames=NF, hero=list(HERO), sniper=list(SNIPER), track=track), open(os.path.join(OUT, 'camera.json'), 'w'))
print('camera track written', flush=True)
sc.render.use_persistent_data = True                               # build the scene (grass, BVH) once, not every frame
if ONLY >= 0:
    sc.frame_set(ONLY); sc.render.filepath = os.path.join(OUT, 'f%04d.jpg' % ONLY); bpy.ops.render.render(write_still=True); print('frame', ONLY, flush=True)
else:
    sc.render.use_overwrite = False; sc.render.use_placeholder = True    # resumable: skips frames already on disk
    sc.render.filepath = os.path.join(OUT, 'f####'); bpy.ops.render.render(animation=True)
    print('sequence done', flush=True)
