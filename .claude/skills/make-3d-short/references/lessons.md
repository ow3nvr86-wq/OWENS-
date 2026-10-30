# Lessons from "The Wave of Molasses" (first video)

Each item is a real problem hit while building `youtube_short_molasses/`, with the fix. Skim the headings; read the details for the stage you're working on.

## Contents
1. Render budget and settings
2. Blender 4.2 API traps
3. Scene, camera and materials
4. Physics simulation
5. Voice, audio and licensing
6. Post-production and delivery
7. Process / workflow

## 1. Render budget and settings

- Measured on 4 vCPU, no GPU, Cycles CPU, 540x960, 8 spp adaptive (threshold 0.05), OIDN with albedo+normal: **~8.5 s/frame** for day shots, **~15 s** for night shots with point lights and lit windows. ~1,780 frames took ~5 h.
- What was tested and rejected: 40 spp at 1080p (~60 s/frame), EEVEE Next on Mesa llvmpipe (17-23 s/frame at half res, plus a ~100 s shader compile), motion blur with handler-driven geometry (extra sub-frame evaluations; ~30 % slower).
- Biggest per-sample costs: Bump nodes (removing them from facades/slabs saved ~30 %), Voronoi textures, many procedural math nodes on large screen areas. Emissive-mesh light sampling was *not* a significant cost.
- Settings that worked: max bounces 4, diffuse 1, glossy 1, transmission 4, transparent 4, `sample_clamp_indirect=4`, caustics off, `blur_glossy=1`, `use_animated_seed=False` (steadier denoising), `use_persistent_data=True`, `use_overwrite=False` + `use_placeholder=True` (resumable).
- Rendering in the background: one Blender process already uses all cores - render chunks sequentially. A background Bash command is killed after 2 h, so size chunks to ~600 day frames / ~400 night frames, or start the render detached and poll for completion with an `until ...; do sleep 30; done` waiter.
- Don't run other CPU-heavy work (audio synthesis, test renders) while a chunk renders - it slows both.

## 2. Blender 4.2 API traps

- `MeshPolygon.loop_total` is read-only in 4.x: build big meshes with `mesh.from_pydata(verts, [], faces)`.
- Principled BSDF input names in 4.x: `Base Color`, `Roughness`, `Metallic`, `Coat Weight`, `Coat Roughness`, `Subsurface Weight`, `Subsurface Radius`, `Subsurface Scale`, `Specular IOR Level`, `Emission Color`, `Emission Strength`, `Transmission Weight`.
- `ShaderNodeMix` socket indices: factor = input 0; FLOAT A/B = inputs 2/3, output 0; RGBA A/B = inputs 6/7, output 2.
- Node-group sockets: `group.interface.new_socket(name, in_out='OUTPUT', socket_type='NodeSocketFloat')`. Keyframing a Value node *inside* a group animates every material that uses the group - handy for global "night", "frost", "paint wipe" values.
- Drivers with expression `frame/45` work without enabling Python auto-exec (simple expression).
- A custom ShaderMaterial-style world/sky isn't needed: Nishita sky with `sun_disc=False` plus a separate Sun lamp gives controllable shadows; keyframe `sky.sun_elevation` on the node.
- `sc.view_settings.keyframe_insert('exposure')` and compositor node inputs are keyframable.
- AgX view transform with look `AgX - Medium High Contrast` looked good.
- Instancing on vertices (`instance_type='VERTS'`) is cheap for thousands of rivets/bolts/windows; the template child is not rendered itself. A Solidify modifier can bury instances - use `offset=0` and put instances proud of the surface.
- `frame_change_pre` handlers run during `bpy.ops.render.render(animation=True)` when started from the same `-P` script. Use `scene.frame_current` (int) to pick the shot so sub-frame evaluations never straddle a cut.
- Keyframed properties override values set in a handler (depsgraph evaluates animation after the handler). Don't toggle `hide_render` in a handler on an object that also has hide_render keys - scale it to 0 instead.
- **Keyframe collision**: when making an object visible in several *adjacent* shots, the "hide at end of shot A" key and "show at start of shot B" key land on the same frame and one wins. Merge adjacent/overlapping ranges before inserting keys (see `vis_key` in the reference).
- `world_to_camera_view` (bpy_extras) after `scene.frame_set(f)` gives normalized screen coords - export them so 2D graphics (e.g. a "50 FT" bracket) stay locked to 3D objects.
- Headless EEVEE needs `libegl1`; Cycles doesn't.

## 3. Scene, camera and materials

- **Dark glossy liquids read as chrome** against a bright sky (Fresnel at grazing angles). Fix: roughness ~0.3, coat ~0.18, Specular IOR Level ~0.3, and a base colour that's dark *brown*, not near-black. Add large-scale noise bump so the surface isn't a perfect mirror.
- Subsurface on the liquid looked orange/translucent and cost time - keep it at 0.
- Bright, uniform procedural cobbles look like cartoon tiles: darken, add grime noise, smaller stones (Voronoi scale ~6.5), softer bump.
- Brick colours that look right in the node editor render pink under AgX - go darker and redder than you think.
- **Cameras inside the simulated fluid** render black frames. Check the fluid height along each camera path (especially with any visual height exaggeration) and keep the lens above it, or end the shot just before impact.
- Cameras placed by coordinates often end up inside buildings or behind a column. Preview every shot; foreground obstructions (columns, crates, walls) were the most common framing bug. Moving one debris object fixed one shot; moving the camera fixed most.
- Very large objects (a 27 m tank roof) falling slowly look like a mushroom cap - make them collapse fast or break up.
- Glowing "smell wisps" made of transparent emissive spheres read as floating discs - dropped. Prefer light, colour and on-screen text for abstract ideas.
- People: simple articulated mannequins (capsule limbs on joint hierarchy, bowler hat) read fine stylized. When partially submerged, raise them enough that torso + arms show; a head alone looks like a ball.
- Keep visual identity consistent: palette per act (steel-blue winter noon -> golden -> blue night -> warm summer), period tags for flashbacks (year labels), a single accent colour for every number.

## 4. Physics simulation

- 2D shallow water (MUSCL + HLL, Heun RK2, 1 m grid, reflective building walls) ran in ~1 min of numpy for 42 s of sim time.
- Bugs hit: velocity blow-up at the wet/dry front (fix: zero velocities below h=0.02 m, cap |u|), and an output-time bookkeeping bug that made `dt` collapse to 1e-6 (record the output frame *before* stepping when `t >= t_out`). Print progress with `python -u` and don't pipe through `tail`/`grep` while debugging, or you see nothing until the end.
- Dam-break fronts are thin wedges, not walls; the sim gave ~15 ft / 24 mph vs. eyewitness 25 ft / 35 mph. The fix was a documented render-time steepening + up to 1.5x height gain in wave shots only - and the on-screen numbers came from sources, not the sim.
- One-way-coupled rigid bodies (debris advected by local velocity with a relaxation time; a house pushed by integrated drag) and a "damage" scalar (momentum flux on columns -> shape-key bend) add a lot of life cheaply.
- Make shot -> sim-time mappings explicit (`('lin', a, b)` / `('hold', t)`), so slow motion, replays and freezes are easy.

## 5. Voice, audio and licensing

- Piper TTS: `PiperVoice.load(model)`, `voice.synthesize_wav(text, wave_file, syn_config=SynthesisConfig(length_scale=...))`. Different voices speak at very different speeds: switching from ryan to ljspeech added ~10 s; `length_scale` 0.77 plus 35 % shorter pauses brought it back under 60 s.
- **Check the voice's MODEL_CARD license** before using it. ryan = CC BY-NC-SA (avoid). ljspeech, bryce, john, norman = public domain; joe = CC0.
- No word-level alignments from Piper: captions use character-weighted timing within each line, which looked right.
- All music/SFX synthesized with numpy/scipy: saw pads + low-pass, plucked ostinato, sine-sweep "taiko", noise risers (block-wise swept band-pass), boom = pitch-dropping sine + low-passed noise + tanh, rivet ping = inharmonic partials + click, flood roar = brown noise + gurgles. FFT-convolution reverb with exponentially decaying noise IRs.
- Sync SFX to animation events exported from Blender (`build/events.json`), not to hand-typed times.
- A 0.1-0.15 s hard silence right before the biggest impact makes it land.
- The first mix measured -9.7 LUFS (too hot); normalize the delivery with ffmpeg `loudnorm=I=-14:TP=-1.5:LRA=11`.
- You cannot listen to the result. Say so, and ask the user to listen before publishing.

## 6. Post-production and delivery

- Upscale 540x960 -> 1080x1920 with Lanczos + unsharp mask; add grain and a vignette; draw all text natively at 1080x1920.
- Transitions that worked: white flash (6 frames) on the main impact, horizontal whip smear (+-2 frames) on fast cuts, 8-frame dip to black for a time jump, short camera shake after impacts.
- Caption bugs: the shadow must fade in with the text; don't let a chunk carry across a pause longer than ~0.35 s or it bleeds into the next scene; end time-labels exactly at the cut so they don't ghost into the next shot's flash.
- Counters should start climbing when the shot starts, not when the number is spoken, or they sit at 0.
- Film grain is expensive to encode: CRF 18 produced 253 MB for 59 s. Cap with `-maxrate 9M -bufsize 18M` (-> 69 MB) for GitHub's 100 MB limit; keep the high-quality master out of git.
- QC from the encoded MP4 itself: ffprobe, decoded-frame contact sheet, `ebur128` loudness.

## 7. Process / workflow

- Build the cheapest checks first: preview stills per shot (~5 s each) -> fix -> final-quality stills -> full render.
- Stop a running render as soon as a sample frame shows a look problem; fixing the shader cost 10 minutes, re-rendering everything later would have cost hours.
- Commit and push after each stage (scripts/docs first, MP4 last). Keep `renders/frames/`, `build/` and `__pycache__/` git-ignored.
- Give the user honest time estimates up front (the full render is hours) and short status notes while long jobs run.
