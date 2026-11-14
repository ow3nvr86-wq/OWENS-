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

// ---- actors that follow tracks exported by the Blender shot (camera.json "actors"/"vis") ----
// character {track: 'hero', autoGait: true, clipDoor: true, size: 1.2}: position per frame from the track, walk/run
// chosen from its speed, facing from its screen motion, feet planted from the distance it has covered.
const ACT = {};                                             // last screen position of each actor (for tags, look-ats)
function trackAt(S, name, x) {
  const A = S.meta.actors[name]; if (!A) return null; const i = Math.min(A.length - 2, Math.floor(x)), u = x - i, a = A[i], b = A[i + 1] || a;
  return [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
}
function trackVis(S, name, x) { const V = S.meta.vis[name]; return !V || V[Math.min(V.length - 1, Math.round(x))] !== 0; }
function trackDist(S, name) {                               // cumulative metres along a track (cached)
  S._dist = S._dist || {}; if (S._dist[name]) return S._dist[name];
  const A = S.meta.actors[name], D = [0]; for (let i = 1; i < A.length; i++) D.push(D[i - 1] + Math.hypot(A[i][0] - A[i - 1][0], A[i][1] - A[i - 1][1]));
  return (S._dist[name] = D);
}
function seqActorState(ch, s, t, S, x, cam) {
  let st = charState(ch, s, t); st.id = ch.id;
  const P = ch.track ? trackAt(S, ch.track, x) : [ch.world[0], ch.world[1], ch.world[2]];
  if (ch.track && !trackVis(S, ch.track, x)) return null;
  P[2] += keyedH(ch.airW, t);
  const p = seqProject(cam, P); st.x = p[0]; st.y = p[1]; st.scale = p[2] * 1.8 / 555 * (ch.size || 1); st.air = 0; st.vel = null;
  if (ch.track) {
    const D = trackDist(S, ch.track), i = Math.min(D.length - 1, Math.floor(x)), d = lerp(D[i], D[Math.min(D.length - 1, i + 1)], x - i);
    const sp = (D[Math.min(D.length - 1, i + 3)] - D[Math.max(0, i - 3)]) / (6 / S.meta.fps);
    if (ch.autoGait && !(POSES2[st.action] && POSES2[st.action](0, 0).feet)) st.action = sp > 3.2 ? 'run' : sp > 0.25 ? 'walk' : (ch.action || 'idle');
    st.dist = d * 555 / 1.8 / (ch.size || 1); st.speedL = sp * 555 / 1.8; st.cycle = st.cycle || hash(ch.id.length * 3.3);
    if (ch.autoFlip !== false && sp > 0.25) { const q = seqProject(cam, trackAt(S, ch.track, Math.min(S.meta.frames - 1, x + 4))); if (Math.abs(q[0] - p[0]) > 1.5) st.flip = q[0] < p[0]; }
  }
  st.depth = p[3];
  if (ch.nodAt) for (const c of [].concat(ch.nodT || [])) st.headTilt = (st.headTilt || 0) + 0.16 * pulse(t, c, 0.35) + 0.12 * pulse(t, c + 0.35, 0.3);
  ACT[ch.id] = { x: st.x, y: st.y, h: 555 * st.scale, s: st.scale };
  return st;
}
// replace the character pass of renderShotSeq with the track-aware one (also handles the car-door clip)
renderShotSeq = (function (orig) {
  return function (g, i, t) {
    const s = SCENES[i]; if (!(s.characters || []).some(c => c.track)) return orig(g, i, t);
    const S = SEQ[s.bgseq.dir], x = seqFrame(S, s, t), cam = seqCam(S, x), img = S.imgs[Math.round(x)];
    g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    let hx = noise(t * 0.45, 1) * 2.5, hy = noise(t * 0.4, 2) * 2.5;
    for (const sh of s._shakes || []) if (t > sh.t0 && t < sh.t0 + 0.7) { const a = sh.amp * Math.exp(-(t - sh.t0) * 7); hx += Math.sin(t * 83 + sh.t0) * a; hy += Math.cos(t * 71 + sh.t0) * a; }
    const Z = 1.03; g.setTransform(Z, 0, 0, Z, W / 2 * (1 - Z) + hx, H / 2 * (1 - Z) + hy);
    if (img) { g.filter = (SCRIPT.grade || '') + (s.bgFilter ? ' ' + s.bgFilter : ''); g.drawImage(img, 0, 0, W, H); g.filter = 'none'; }
    for (const fx of s.fx || []) {
      if (fx.actor) { const P = trackAt(S, fx.actor, x); if (P) { const p = seqProject(cam, [P[0] + (fx.off || [0, 0, 0])[0], P[1] + (fx.off || [0, 0, 0])[1], P[2] + (fx.off || [0, 0, 0])[2]]); fx.x = p[0] / W; fx.y = p[1] / H; if (fx.rW) fx.r = fx.rW * p[2]; } }
      else if (fx.world) { const p = seqProject(cam, fx.world); fx.x = p[0] / W; fx.y = p[1] / H; if (fx.rW) fx.r = fx.rW * p[2]; }
      if (fx.fromW) { const a = seqProject(cam, fx.fromW), b = seqProject(cam, fx.toW); fx.from = [a[0] / W, a[1] / H]; fx.to = [b[0] / W, b[1] / H]; }
    }
    for (const im of s._impacts || []) if (im.fx && (im.fx.world || im.fx.actor)) { im.x = im.fx.x * W; im.y = im.fx.y * H; im.r = im.fx.r || im.r; im.only = im.fx.only; }
    const items = [];
    for (const ch of s.characters || []) {
      let st = seqActorState(ch, s, t, S, x, cam); if (!st) continue;
      if (FEAT.crowdFX) st = crowdReact(st, s, t, 150);
      const def = Object.assign({ seed: ch.id.length }, CAST()[ch.cast || ch.id]);
      let clipY = null; if (ch.clipDoor) { const d = S.meta.door[Math.min(S.meta.door.length - 1, Math.round(x))]; clipY = seqProject(cam, [d[0], d[1], d[2] + 1.02])[1]; }
      items.push({ d: st.depth, draw: () => { if (clipY != null) { g.beginPath(); g.rect(-W, -H, W * 3, clipY + H); g.clip(); } st._def = def; drawCharacter(g, def, st); if (st._post) st._post(g); } });
    }
    items.sort((a, b) => b.d - a.d);
    for (const it of items) { g.save(); it.draw(); g.restore(); }
    for (const fx of s.fx || []) if (!SCREEN_FX.has(fx.type)) { g.save(); fxDraw(g, fx, s, t); g.restore(); }
    g.setTransform(1, 0, 0, 1, 0, 0);
    for (const fx of s.fx || []) if (SCREEN_FX.has(fx.type)) { if (window.FX2 && FX2[fx.type]) FX2[fx.type](g, fx, s, t); }
  };
})(renderShotSeq);

// ---- one-shot effects ----
FX2.tag = function (g, fx, s, t) {                         // a floating tag over an actor's head ("NPC")
  const A = ACT[fx.of]; if (!A || t < fx.t0 || (fx.until && t > fx.until)) return; const k = popScale(t, fx.t0, 0.35);
  g.save(); g.translate(A.x, A.y - A.h * 1.12 + Math.sin(t * 3) * 6); g.scale(k, k);
  g.font = '800 64px Poppins'; g.textAlign = 'center'; g.textBaseline = 'middle'; const w = g.measureText(fx.text).width + 44;
  g.beginPath(); g.roundRect(-w / 2, -42, w, 84, 22); g.fillStyle = fx.bg || '#ffd23a'; g.fill(); g.lineWidth = 7; g.strokeStyle = '#1d1719'; g.stroke();
  g.beginPath(); g.moveTo(-14, 40); g.lineTo(0, 64); g.lineTo(14, 40); g.closePath(); g.fillStyle = fx.bg || '#ffd23a'; g.fill(); g.stroke();
  g.fillStyle = '#1d1719'; g.fillText(fx.text, 0, 4); g.restore();
};
FX2.spawn = function (g, fx, s, t) {                       // a player spawning in: a light column and rings
  const u = t - fx.t0; if (u < -0.2 || u > 1.6) return; const x = fx.x * W, y = fx.y * H, k = Math.max(0, 1 - Math.max(0, u - 0.6));
  const gr = g.createLinearGradient(x - 70, 0, x + 70, 0); gr.addColorStop(0, 'rgba(120,220,255,0)'); gr.addColorStop(0.5, `rgba(200,245,255,${0.85 * k})`); gr.addColorStop(1, 'rgba(120,220,255,0)');
  g.fillStyle = gr; g.fillRect(x - 70, -100, 140, y + 100);
  for (let r = 0; r < 3; r++) { const v = ((u * 1.4 + r / 3) % 1); g.save(); g.translate(x, y); g.scale(1, 0.3); g.beginPath(); g.arc(0, 0, 40 + v * 260, 0, 7); g.lineWidth = 10 * (1 - v); g.strokeStyle = `rgba(160,235,255,${(1 - v) * k})`; g.stroke(); g.restore(); }
};
FX2.stars = function (g, fx, s, t) {                       // a wanted-level row of five stars (original design), filling on cues
  let n = 0; for (const k of fx.keys) if (t >= k.t) n = k.n; if (!n) return;
  const x0 = W - 90, y = 150;
  for (let i = 0; i < 5; i++) { const on = 4 - i < n, k = on ? popScale(t, (fx.keys.find(q => q.n === 5 - i) || {}).t, 0.3) : 1;
    g.save(); g.translate(x0 - i * 92, y); g.scale(k || 1, k || 1); star5(g, 0, 0, 38, on ? '#ffffff' : 'rgba(0,0,0,0.35)'); g.restore(); }
};
FX2.title = function (g, fx, s, t) {                       // a big punchy title (e.g. BUSTED) with a shake
  const k = popScale(t, fx.t0, 0.3); if (!k || (fx.until && t > fx.until)) return; const sh = Math.max(0, 1 - (t - fx.t0) * 3) * 14;
  g.save(); g.translate(W / 2 + Math.sin(t * 70) * sh, H * (fx.y ?? 0.4)); g.scale(k, k); g.rotate(-0.04);
  g.font = `800 ${fx.size || 190}px Poppins`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineJoin = 'round';
  const gr = g.createLinearGradient(0, -90, 0, 90); (fx.grad || ['#fff2b0', '#ff8a1e', '#c8240c']).forEach((c, i, a) => gr.addColorStop(i / (a.length - 1), c));
  g.shadowColor = 'rgba(0,0,0,0.6)'; g.shadowBlur = 30; g.shadowOffsetY = 12; g.lineWidth = 34; g.strokeStyle = '#120a0a'; g.strokeText(fx.text, 0, 0);
  g.shadowColor = 'transparent'; g.fillStyle = gr; g.fillText(fx.text, 0, 0); g.restore();
};
