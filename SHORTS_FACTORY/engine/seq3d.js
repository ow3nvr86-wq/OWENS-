// 3D SHOTS: a pre-rendered moving-camera background (tools/fight_blender.py: image sequence + camera.json) with 2D
// characters and effects pinned to 3D world points (metres). Every frame the engine projects those points through the
// interpolated camera, so the 2D cast stays locked to the world while the camera orbits, cranes and pushes around it.
// scene: { "bgseq": {"dir": "fightseq"}, characters: [{..., "world": [x,y,z], "airW": [{at, h}], "size": 1}],
//          fx: [{type, "world": [x,y,z]} | {type: "tracer", "fromW": [..], "toW": [..]} | {type: "blast", "world": [..], "rW": m}] }
const SEQ = {};
async function loadSeq(ep, dir) {
  if (SEQ[dir]) return;
  const meta = await (await fetch('../' + ep + '/' + dir + '/camera.json')).json(), imgs = new Array(meta.frames);
  await Promise.all([...Array(meta.frames).keys()].map(f => new Promise(res => { const im = new Image(); im.onload = () => { imgs[f] = im; res(); }; im.onerror = () => res(); im.src = '../' + ep + '/' + dir + '/f' + String(f).padStart(4, '0') + '.jpg'; })));
  SEQ[dir] = { meta, imgs };
}
function seqFrame(S, s, t) { return clamp((t - s.start - (s.bgseq.offset || 0)) * S.meta.fps, 0, S.meta.frames - 1); }
function seqCam(S, x) {                                   // camera at a fractional frame (linear between rendered frames)
  const tr = S.meta.track, i = Math.min(tr.length - 2, Math.floor(x)), u = x - i, a = tr[i], b = tr[i + 1] || a;
  const C = a.C.map((v, k) => lerp(v, b.C[k], u)), R = a.R.map((row, r) => row.map((v, c) => lerp(v, b.R[r][c], u)));
  return { C, R, f: (H / 2) / lerp(a.tanh, b.tanh, u) };
}
function seqProject(cam, P) {                             // world point -> [screen x, screen y, px per metre, depth]
  const d = [P[0] - cam.C[0], P[1] - cam.C[1], P[2] - cam.C[2]], R = cam.R;
  const xc = R[0][0] * d[0] + R[1][0] * d[1] + R[2][0] * d[2], yc = R[0][1] * d[0] + R[1][1] * d[1] + R[2][1] * d[2], zc = R[0][2] * d[0] + R[1][2] * d[1] + R[2][2] * d[2];
  const depth = Math.max(0.05, -zc), k = cam.f / depth;
  return [W / 2 + xc * k, H / 2 - yc * k, k, depth];
}
function keyedH(keys, t, dflt = 0) {                      // eased height keys [{t, h}] (metres)
  if (!keys || !keys.length) return dflt; let prev = { t: -1e9, h: keys[0].h };
  for (const k of keys) { if (t < k.t) return lerp(prev.h, k.h, ease5((t - prev.t) / Math.max(0.05, k.t - prev.t))); prev = k; }
  return prev.h;
}
function renderShotSeq(g, i, t) {
  const s = SCENES[i], S = SEQ[s.bgseq.dir], x = seqFrame(S, s, t), cam = seqCam(S, x), img = S.imgs[Math.round(x)];
  g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  // handheld + impact shake on top of the rendered camera move
  let hx = noise(t * 0.45, 1) * 3, hy = noise(t * 0.4, 2) * 3;
  for (const sh of s._shakes || []) if (t > sh.t0 && t < sh.t0 + 0.7) { const a = sh.amp * Math.exp(-(t - sh.t0) * 7); hx += Math.sin(t * 83 + sh.t0) * a; hy += Math.cos(t * 71 + sh.t0) * a; }
  const Z = 1.04; g.setTransform(Z, 0, 0, Z, W / 2 * (1 - Z) + hx, H / 2 * (1 - Z) + hy);
  if (img) { g.filter = (SCRIPT.grade || '') + (s.bgFilter ? ' ' + s.bgFilter : ''); g.drawImage(img, 0, 0, W, H); g.filter = 'none'; }
  // pinned effects: world points -> screen fractions for this frame
  for (const fx of s.fx || []) {
    if (fx.world) { const p = seqProject(cam, fx.world); fx.x = p[0] / W; fx.y = p[1] / H; if (fx.rW) fx.r = fx.rW * p[2]; }
    if (fx.fromW) { const a = seqProject(cam, fx.fromW), b = seqProject(cam, fx.toW); fx.from = [a[0] / W, a[1] / H]; fx.to = [b[0] / W, b[1] / H]; }
  }
  for (const im of s._impacts || []) if (im.fx && im.fx.world) { im.x = im.fx.x * W; im.y = im.fx.y * H; im.r = im.fx.r || im.r; }
  const items = [];
  for (const ch of s.characters || []) {
    let st = charState(ch, s, t); st.id = ch.id;
    const P = [ch.world[0], ch.world[1], ch.world[2] + keyedH(ch.airW, t)], p = seqProject(cam, P), g0 = seqProject(cam, [ch.world[0], ch.world[1], ch.world[2]]);
    st.x = p[0]; st.y = p[1]; st.scale = p[2] * 1.8 / 555 * (ch.size || 1); st.air = 0; st.vel = null;
    st.shadowY = g0[1];
    if (FEAT.crowdFX) st = crowdReact(st, s, t, 150);
    const def = Object.assign({ seed: ch.id.length }, CAST()[ch.cast || ch.id]);
    items.push({ d: p[3], draw: () => { st._def = def; drawCharacter(g, def, st); if (st._post) st._post(g); } });
  }
  items.sort((a, b) => b.d - a.d);
  for (const it of items) { g.save(); it.draw(); g.restore(); }
  for (const fx of s.fx || []) if (!SCREEN_FX.has(fx.type)) { g.save(); fxDraw(g, fx, s, t); g.restore(); }
  g.setTransform(1, 0, 0, 1, 0, 0);
  for (const fx of s.fx || []) if (SCREEN_FX.has(fx.type)) { if (fx.type === 'glow') fireGlow(g, clamp((t - fx.t0) / 0.6) * (fx.amount ?? 1), fx.col); else if (window.FX2 && FX2[fx.type]) FX2[fx.type](g, fx, s, t); }
  if (s.tint) { g.fillStyle = s.tint; g.fillRect(0, 0, W, H); }
}

// ---- extra punch: speed lines and an impact frame ----
FX2.speedlines = function (g, fx, s, t) { const u = (t - fx.t0) / (fx.dur || 0.6); if (u < 0 || u > 1) return; speedLines(g, (fx.x ?? 0.5) * W, (fx.y ?? 0.5) * H, t, 34, 300, 1400, 0.55 * Math.sin(Math.PI * u)); };
FX2.impactframe = function (g, fx, s, t) {                // 2-3 frames of high-contrast flash, the classic hit frame
  const u = t - fx.t0; if (u < 0 || u > 0.07) return;
  g.save(); g.globalCompositeOperation = 'difference'; g.fillStyle = 'rgba(255,255,255,0.9)'; g.fillRect(0, 0, W, H); g.restore();
};
