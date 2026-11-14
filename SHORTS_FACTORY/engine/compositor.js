// Episode compositor: background -> crowd -> characters -> effects -> captions, with a camera move on every shot and
// whip/zoom/cut transitions. Everything is driven by <episode>/script.json, work/words.json and work/amp.json.
// Open as engine/index.html?ep=episodes/<name>. window.renderFrame(f) draws frame f (f / FPS s; FPS = script.json fps, default 60).
const cv = document.getElementById('c'), X = cv.getContext('2d');
const mk = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return [c, c.getContext('2d')]; };
const [A, AX] = mk(), [B, BX] = mk();
const QS = new URLSearchParams(location.search), EP = QS.get('ep');
// render mode: 'final' (full quality) or 'draft' (no motion blur, half-resolution output)
const MODE = QS.get('mode') === 'draft' ? 'draft' : 'final';
// debug overlays: ?debug=depth,rig,lipsync,crowd,blur
const DEBUG = new Set((QS.get('debug') || '').split(',').filter(Boolean));
// feature flags (script.json "features"); every upgrade is OFF unless the episode turns it on
let FEAT = { depth: false, motionBlur: false, rigV2: false, lipSync: false, crowdFX: false };
let AFPS = 30, SCRIPT, WORDS, AMP, SCENES = [], CHUNKS = [], BG = {}, NORM = [];

const norm = s => s.toLowerCase().replace(/[^a-z0-9' ]/g, ' ').replace(/'/g, '').trim();
// find the time of a cue phrase (first occurrence at or after word index `from`)
function cueIndex(cue, from = 0) {
  const toks = norm(String(cue)).split(/\s+/);
  for (let i = from; i < NORM.length; i++) if (toks.every((tk, k) => NORM[i + k] === tk)) return i;
  throw new Error('cue not found: "' + cue + '" after word ' + from);
}
function cueTime(cue, from = 0) { if (typeof cue === 'number') return cue; return WORDS[cueIndex(cue, from)].start; }

function resolve() {
  NORM = WORDS.map(w => norm(w.word).replace(/\s+/g, ''));
  let ptr = 0;
  SCENES = SCRIPT.scenes.map((sc, i) => {
    const idx = i === 0 ? 0 : cueIndex(sc.cue, ptr); ptr = idx;
    return Object.assign({}, sc, { start: i === 0 ? 0 : WORDS[idx].start - 0.06, wi: idx });
  });
  SCENES.forEach((s, i) => { s.end = i + 1 < SCENES.length ? SCENES[i + 1].start : SCRIPT._duration + 0.5; });
  // resolve every cue inside a scene relative to its own words
  for (const s of SCENES) {
    const T = c => (c == null ? null : (typeof c === 'number' ? s.start + c : cueTime(c, s.wi)));
    for (const ch of s.characters || []) { for (const k of ch.keys || []) k.t = T(k.cue); if (ch.talk) ch.talkT = ch.talk.map(T); if (ch.move) { ch.move.t0 = T(ch.move.from) ?? s.start; ch.move.t1 = T(ch.move.to) ?? s.end; } if (ch.enterAt) ch.enterT = T(ch.enterAt); }
    for (const fx of s.fx || []) { fx.t0 = T(fx.at) ?? s.start; fx.seed = fx.seed ?? (s.wi % 97); }
    // v2 extras: props on cues, height keyframes, blasts that knock characters back and shake the camera
    for (const p of s.props || []) { if (p.at != null) p.t0 = T(p.at); if (p.move) { p.move.t0 = T(p.move.from) ?? s.start; p.move.t1 = T(p.move.to) ?? s.end; } }
    for (const ch of s.characters || []) for (const k of ch.air || []) k.t = T(k.cue ?? k.at);
    s._impacts = []; s._shakes = [];
    for (const fx of s.fx || []) if (fx.type === 'blast') {
      const z = typeof zOf === 'function' ? zOf(fx.z ?? fx.layer) : 150;
      s._impacts.push({ x: fx.x * W, y: fx.y * H, t0: fx.t0, r: fx.r || 260, force: fx.force || 1, z });
      s._shakes.push({ t0: fx.t0, amp: (fx.shake ?? 24) * clamp(150 / z, 0.4, 2.5) });
    }
  }
}
// ---------------- captions: 1-2 words, synced to word times ----------------
function buildCaptions() {
  const swaps = Object.entries(SCRIPT.caption_swaps || {}).map(([k, v]) => [norm(k).split(/\s+/), v]);
  const toks = []; let i = 0;
  while (i < WORDS.length) {
    let hit = null;
    for (const [seq, rep] of swaps) if (seq.every((s, k) => NORM[i + k] === s)) { hit = [seq.length, rep]; break; }
    if (hit) { const last = WORDS[i + hit[0] - 1]; toks.push({ word: hit[1] + (/[.,?!]$/.test(last.word) ? '.' : ''), start: WORDS[i].start, end: last.end }); i += hit[0]; }
    else { toks.push(WORDS[i]); i++; }
  }
  const phrases = []; let cur = [];
  for (const w of toks) { cur.push(w); if (/[.,?!:;]$|\.\.\.$/.test(w.word)) { phrases.push(cur); cur = []; } }
  if (cur.length) phrases.push(cur);
  const out = [];
  for (const p of phrases) { let j = 0; while (j < p.length) { const rest = p.length - j; let take = rest === 3 ? 1 : Math.min(2, rest);
    if (take === 2 && (clean(p[j].word) + clean(p[j + 1].word)).length > 14) take = 1; out.push(p.slice(j, j + take)); j += take; } }
  CHUNKS = out.map((c, k) => ({ text: c.map(w => clean(w.word)).join(' '), start: c[0].start - 0.03, end: Math.min(c[c.length - 1].end + 0.35, out[k + 1] ? out[k + 1][0].start - 0.03 : 1e9) }));
}
function clean(s) { return s.toUpperCase().replace(/(\d),(?=\d)/g, '$1\u0001').replace(/(\d):(?=\d)/g, '$1\u0002').replace(/\.\.\.|[.,?!:;"]/g, '').replace(/\u0001/g, ',').replace(/\u0002/g, ':').replace(/'/g, '’'); }
function captions(t) {
  const ch = CHUNKS.find(c => t >= c.start && t < c.end); if (!ch) return;
  const age = (t - ch.start) * 30, sc = age >= 4 ? 1 : 0.85 + 0.15 * eOut(age / 4);
  const cy = H * (SCRIPT.caption_y ?? 0.68);
  X.save(); X.translate(W / 2, cy); X.scale(sc, sc);
  X.font = '800 90px Poppins'; X.textAlign = 'center'; X.textBaseline = 'middle'; X.lineJoin = 'round'; X.miterLimit = 2;
  X.shadowColor = 'rgba(0,0,0,0.55)'; X.shadowBlur = 22; X.shadowOffsetY = 8;
  X.lineWidth = 20; X.strokeStyle = '#000'; X.strokeText(ch.text, 0, 0);
  X.shadowColor = 'transparent'; X.fillStyle = '#ffffff'; X.fillText(ch.text, 0, 0);
  X.restore();
}

// ---------------- camera ----------------
const MOVES = {            // [scale0, scale1, dx0, dx1, dy0, dy1] (dx/dy in frame px at the end of the shot)
  push: [1.0, 1.12, 0, 10, 0, -8], pull: [1.12, 1.0, 0, -10, -8, 0], pan_left: [1.1, 1.12, 60, -60, 0, 0], pan_right: [1.1, 1.12, -60, 60, 0, 0],
  tilt_up: [1.1, 1.12, 0, 0, 70, -50], tilt_down: [1.1, 1.12, 0, 0, -60, 60], drift: [1.04, 1.08, -20, 20, 0, 0], punch: [1.0, 1.25, 0, 0, 0, 0],
};
function camAt(s, t) {
  const m = s.camera || {}; const base = MOVES[m.move || 'push'];
  const v = clamp((t - s.start) / Math.max(0.3, s.end - s.start)), u = lerp(v, ease(v), 0.55);
  const k = m.amount ?? 1;
  const sc = lerp(1, lerp(base[0], base[1], u), k) * (m.zoom || 1);
  const fx = (m.focus || [0.5, 0.5]);
  let dx = lerp(base[2], base[3], u) * k, dy = lerp(base[4], base[5], u) * k;
  // gentle handheld drift + impact shakes
  dx += noise(t * 0.4, 1) * 4; dy += noise(t * 0.35, 2) * 4;
  for (const fx2 of s.fx || []) if (fx2.shake && t > fx2.t0 && t < fx2.t0 + 0.5) { const a = fx2.shake * Math.exp(-(t - fx2.t0) * 8); dx += Math.sin(t * 90) * a; dy += Math.cos(t * 77) * a; }
  return { sc, cx: fx[0] * W, cy: fx[1] * H, dx, dy };
}

// ---------------- one shot ----------------
const CAST = () => SCRIPT.cast;
function amp(t) { const x = Math.max(0, t * AFPS), i = Math.min(AMP.length - 2, Math.floor(x)); return Math.max(0, lerp(AMP[i] || 0, AMP[i + 1] || 0, x - i)); }
// smooth blinks: eyelid closes and opens over ~0.14 s every 2-4 s (0 = open, 1 = shut)
function blinkAt(t, seed) { const per = 2.2 + hash(seed) * 1.8, u = (t + hash(seed + 1) * per) % per; return u < 0.14 ? Math.sin(Math.PI * u / 0.14) : 0; }
function charState(ch, s, t) {
  const st = { x: ch.x * W, y: ch.y * H, scale: ch.scale || 1, flip: !!ch.flip, mood: ch.mood, action: ch.action || 'idle', prop: ch.prop, look: ch.look || 0, headTilt: 0 };
  // keys switch pose/mood on a word; remember the previous ones so the change blends instead of snapping
  st.prevAction = st.action; st.actionT = -9; st.prevMood = st.mood; st.moodT = -9;
  for (const k of ch.keys || []) if (t >= k.t) {
    if (k.action && k.action !== st.action) { st.prevAction = st.action; st.actionT = k.t; }
    if (k.mood && k.mood !== st.mood) { st.prevMood = st.mood; st.moodT = k.t; }
    Object.assign(st, Object.fromEntries(Object.entries(k).filter(([n]) => !['cue', 't', 'x', 'y'].includes(n))));
    if (k.x != null || k.y != null) { st.keyFrom = [st.x, st.y]; st.keyT = k.t; if (k.x != null) st.x = k.x * W; if (k.y != null) st.y = k.y * H; }
  }
  if (st.keyFrom) { const u = ease5((t - st.keyT) / 0.45); st.x = lerp(st.keyFrom[0], st.x, u); st.y = lerp(st.keyFrom[1], st.y, u); }
  if (ch.move) {
    const d = Math.max(0.2, ch.move.t1 - ch.move.t0), u = ease5((t - ch.move.t0) / d);
    const x0 = ch.x * W, y0 = ch.y * H, x1 = (ch.move.x ?? ch.x) * W, y1 = (ch.move.y ?? ch.y) * H;
    st.x = lerp(x0, x1, u); st.y = lerp(y0, y1, u);
    // feet step in time with the distance travelled (no skating); idle characters walk while they move
    const dist = Math.hypot(st.x - x0, st.y - y0), strideP = 95 * st.scale;
    st.phase = dist / strideP * Math.PI;
    if (t > ch.move.t0 && t < ch.move.t1 && st.action === 'idle') st.action = 'walk';
    st.lean = (st.action === 'run' ? 0.1 : 0.04) * Math.sign(x1 - x0) * (st.flip ? -1 : 1) * Math.sin(Math.PI * clamp((t - ch.move.t0) / d));
  }
  if (st.action === 'march' || st.action === 'run' || st.action === 'walk') st.phase = st.phase ?? t * (st.action === 'run' ? 14 : st.action === 'walk' ? 7 : 8);
  // entrance: pop (springs up from the ground) or slide (in from the nearest side), on a cue or at the shot start
  if (ch.enter) {
    const t0 = ch.enterT ?? s.start, u = clamp((t - t0) / 0.42);
    if (ch.enter === 'pop') st.pop = u;
    if (ch.enter === 'slide') { const from = st.x < W / 2 ? -260 * st.scale : W + 260 * st.scale; st.x = lerp(from, st.x, eOut(u)); if (u < 1) { st.action = st.action === 'idle' ? 'walk' : st.action; st.phase = t * 10; } }
  }
  const seed = (ch.id || '').length * 7.3 + ch.x * 13;
  st.blink = blinkAt(t, seed);
  for (const k of ch.keys || []) if (k.mood && t >= k.t && t < k.t + 0.14) st.blink = Math.max(st.blink, Math.sin(Math.PI * (t - k.t) / 0.14));
  if (ch.talkT && t >= ch.talkT[0] - 0.05 && t <= ch.talkT[1] + 0.25) { st.talk = amp(t); if (st.action === 'idle') st.action = 'talk'; }
  st.t = t; st.seed = seed;
  if (FEAT.rigV2) {
    if (ch.move && GAIT[st.action]) {
      const d = Math.max(0.2, ch.move.t1 - ch.move.t0), x0 = ch.x * W, y0 = ch.y * H, x1 = (ch.move.x ?? ch.x) * W, y1 = (ch.move.y ?? ch.y) * H;
      const at = tau => Math.hypot(x1 - x0, y1 - y0) * ease5((tau - ch.move.t0) / d) / st.scale;
      st.dist = at(t); st.speedL = (at(t + 0.01) - at(t - 0.01)) / 0.02;
    } else if (GAIT[st.action]) { st.speedL = ch.speed ?? (st.action === 'run' ? 520 : 260); st.dist = (t - s.start) * st.speedL; }
    st.cycle = hash(seed * 1.3); st.air = 0;
    if (ch.air) { let prev = { t: -1e9, h: 0 }; for (const k of ch.air) { if (t < k.t) { const u = (t - prev.t) / Math.max(0.05, k.t - prev.t); st.air = lerp(prev.h, k.h, k.ease === 'linear' ? clamp(u) : ease5(u)) * H / st.scale; prev = null; break; } prev = k; } if (prev) st.air = prev.h * H / st.scale; }
    st.blinkKey = 0; for (const k of ch.keys || []) if (k.mood && t >= k.t && t < k.t + 0.14) st.blinkKey = Math.sin(Math.PI * (t - k.t) / 0.14);
    lookState(ch, s, t, st);
    if (FEAT.lipSync && window.lipAt) lipAt(ch, s, t, st);
  }
  return st;
}
function crowdMembers(cr, s, t) {
  const n = cr.count || 40, [x0, y0, x1, y1] = cr.area, defs = [].concat(cr.cast).map(id => CAST()[id]);
  const out = [];
  for (let i = 0; i < n; i++) {
    const rx = hash(i * 3.71 + (cr.seed || 1)), ry = hash(i * 9.13 + (cr.seed || 1));
    const vary = FEAT.crowdFX ? crowdVariation(cr, i) : null;
    const tt = vary ? Math.max(0, t - s.start - vary.delay) : t - s.start;
    let x = lerp(x0, x1, rx), y = lerp(y0, y1, ry);
    const spd = (cr.speed || 0) * (vary ? vary.speed : (0.85 + hash(i * 5.5) * 0.3)), dyv = (cr.dy || 0) * (vary ? vary.speed : (0.85 + hash(i * 2.2) * 0.3));
    x += spd * tt; y += dyv * tt;
    if (cr.wrap) { const w = x1 - x0; x = x0 + ((((x - x0) % w) + w) % w); }
    if (cr.wrapY) { const h = y1 - y0; y = y0 + ((((y - y0) % h) + h) % h); }
    const depth = clamp((y - y0) / Math.max(0.001, y1 - y0));
    if (cr.taper != null) x = (x0 + x1) / 2 + (x - (x0 + x1) / 2) * lerp(cr.taper, 1, depth);
    const sc = lerp(cr.scale[0], cr.scale[1], depth) * (vary ? vary.height : 1);
    const z = Array.isArray(cr.z) ? lerp(zOf(cr.z[0]), zOf(cr.z[1]), depth) : zOf(cr.z ?? cr.layer);
    const action = cr.action || 'march', def = Object.assign({ seed: i }, defs[i % defs.length], vary ? vary.def : {});
    const dist = Math.hypot(spd * W, dyv * H) * tt / Math.max(0.01, sc);  // distance walked (body units), drives planted feet
    const st = { x: x * W, y: y * H, scale: sc, flip: !!cr.flip, t: t + i * 0.13, mood: cr.mood || def.mood, action,
      phase: t * (action === 'run' ? 13 : 7.5) * (vary ? vary.speed : 1) + hash(i * 4.4) * 6.28, blink: blinkAt(t, i * 3.3 + 1), seed: i, look: cr.look || 0,
      lean: action === 'run' ? (cr.flip ? 0.12 : -0.12) : 0, prop: cr.prop, id: (cr.seed || 1) * 1000 + i, dist: (spd || dyv) ? dist : undefined, speedL: Math.hypot(spd * W, dyv * H) / Math.max(0.01, sc), vel: [spd * W, dyv * H], cycle: vary ? vary.phase : hash(i * 4.4), crowd: true };
    out.push({ i, x, y, z, def, st });
  }
  return out.sort((a, b) => a.y - b.y);
}
function crowd(g, cr, s, t) {
  const n = cr.count || 40, [x0, y0, x1, y1] = cr.area, defs = [].concat(cr.cast).map(id => CAST()[id]);
  const list = [];
  for (let i = 0; i < n; i++) {
    const rx = hash(i * 3.71 + (cr.seed || 1)), ry = hash(i * 9.13 + (cr.seed || 1));
    let x = lerp(x0, x1, rx), y = lerp(y0, y1, ry);
    const spd = (cr.speed || 0) * (0.85 + hash(i * 5.5) * 0.3);
    x += spd * (t - s.start); if (cr.dy) y += cr.dy * (t - s.start) * (0.85 + hash(i * 2.2) * 0.3);
    if (cr.wrap) { const w = x1 - x0; x = x0 + ((((x - x0) % w) + w) % w); }
    if (cr.wrapY) { const h = y1 - y0; y = y0 + ((((y - y0) % h) + h) % h); }          // endless waves down a lane
    const depth = clamp((y - y0) / Math.max(0.001, y1 - y0));
    if (cr.taper != null) x = (x0 + x1) / 2 + (x - (x0 + x1) / 2) * lerp(cr.taper, 1, depth);   // lane narrows with distance
    const sc = lerp(cr.scale[0], cr.scale[1], depth);
    list.push({ i, x, y, sc, def: defs[i % defs.length] });
  }
  list.sort((a, b) => a.y - b.y);
  for (const p of list) {
    const action = cr.action || 'march';
    drawCharacter(g, Object.assign({ seed: p.i }, p.def), { x: p.x * W, y: p.y * H, scale: p.sc, flip: !!cr.flip, t: t + p.i * 0.13, mood: cr.mood || p.def.mood,
      action, phase: t * (action === 'run' ? 13 : 7.5) + hash(p.i * 4.4) * 6.28, blink: blinkAt(t, p.i * 3.3 + 1), seed: p.i, look: cr.look || 0, lean: action === 'run' ? (cr.flip ? 0.12 : -0.12) : 0 });
  }
}
function drawBg(g, s, t, layer = '') {
  const img = BG[layer ? s.bg.replace(/(\.\w+)$/, layer + '$1') : s.bg];
  if (layer) { if (!img) return; g.setTransform(1, 0, 0, 1, 0, 0); g.save(); g.globalAlpha = 1; }
  else { g.save(); g.fillStyle = '#000'; g.fillRect(0, 0, W, H); }
  const c = camAt(s, t);
  g.translate(c.cx + c.dx, c.cy + c.dy); g.scale(c.sc, c.sc); g.translate(-c.cx, -c.cy);
  if (img) {
    const r = Math.max(W / img.width, H / img.height), w = img.width * r, h = img.height * r;
    const grade = SCRIPT.grade || 'saturate(1.08) contrast(1.05)';
    g.filter = grade + (s.bgFilter ? ' ' + s.bgFilter : '') + (s.bgBlur ? ` blur(${s.bgBlur}px)` : '');
    g.drawImage(img, (W - w) / 2, (H - h) / 2, w, h); g.filter = 'none';
  }
  return c;
}
function fxDraw(g, fx, s, t) {
  if (fx.type === 'rockets') rocketVolley(g, Object.assign({}, fx, { from: [fx.from[0] * W, fx.from[1] * H], to: [fx.to[0] * W, fx.to[1] * H] }), t);
  if (fx.type === 'puff') puffs(g, fx.x * W, fx.y * H, fx.t0, t, fx.n || 7, fx.size || 70, fx.col);
  if (fx.type === 'sparks' && t >= fx.t0) sparks(g, fx.x * W, fx.y * H, t, 1);
  if (fx.type === 'impact') impactBurst(g, fx.x * W, fx.y * H, fx.t0, t, fx.r || 220);
  if (window.FX2 && FX2[fx.type]) FX2[fx.type](g, fx, s, t);
}
const SCREEN_FX = new Set(['glow', 'flash', 'tint', 'storm_tint', 'confetti', 'hud']);
let CUR_CAM = null;
function renderShotDepth(g, i, t) {
  const s = SCENES[i], L = LOC[s.loc], cam = cam3At(s, t); CUR_CAM = { s, cam };
  g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = L.sky; g.fillRect(0, 0, W, H);
  const items = [];
  L.layers.forEach((ly, k) => items.push({ z: ly.z, o: 0, y: 0, draw: () => drawLayer(g, L, cam, ly) }));
  for (const cr of s.crowds || []) for (const m of crowdMembers(cr, s, t)) {
    const st = FEAT.crowdFX ? crowdReact(m.st, s, t, m.z) : m.st;
    items.push({ z: m.z, o: 1, y: m.y, draw: () => { setPlane(g, cam, m.z); if (FEAT.crowdFX) crowdDust(g, m, s, t); st._def = m.def; drawCharacter(g, m.def, st); if (st._post) st._post(g); } });
  }
  for (const ch of s.characters || []) {
    let st = charState(ch, s, t); const z = zOf(ch.z ?? ch.layer); st.id = ch.id;
    if (FEAT.crowdFX) st = crowdReact(st, s, t, z);
    const def = Object.assign({ seed: ch.id.length }, CAST()[ch.cast || ch.id]);
    items.push({ z: z - 0.001, o: 2, y: st.y, draw: () => { setPlane(g, cam, z); if (FEAT.crowdFX) crowdDust(g, { st, def, z }, s, t); st._def = def; drawCharacter(g, def, st); if (st._post) st._post(g); } });
  }
  for (const pr of s.props || []) { const z = zOf(pr.z ?? pr.layer); items.push({ z: z - 0.002, o: pr.front ? 3 : 1, y: (pr.y || 0) * H, draw: () => { setPlane(g, cam, z); window.drawProp && drawProp(g, pr, s, t); } }); }
  for (const fx of s.fx || []) if (!SCREEN_FX.has(fx.type)) { const z = zOf(fx.z ?? fx.layer); items.push({ z: z - 0.003, o: 4, y: 0, draw: () => { setPlane(g, cam, z); fxDraw(g, fx, s, t); } }); }
  items.sort((a, b) => (b.z - a.z) || (a.o - b.o) || (a.y - b.y));
  for (const it of items) { g.save(); it.draw(); g.restore(); }
  g.setTransform(1, 0, 0, 1, 0, 0);
  for (const fx of s.fx || []) if (SCREEN_FX.has(fx.type)) { if (fx.type === 'glow') fireGlow(g, clamp((t - fx.t0) / 0.6) * (fx.amount ?? 1), fx.col); else if (window.FX2 && FX2[fx.type]) FX2[fx.type](g, fx, s, t); }
  if (s.tint) { g.fillStyle = s.tint; g.fillRect(0, 0, W, H); }
}
function renderShot(g, i, t) {
  if (FEAT.depth && SCENES[i].loc && LOC[SCENES[i].loc]) return renderShotDepth(g, i, t);
  const s = SCENES[i]; g.setTransform(1, 0, 0, 1, 0, 0);
  const c = drawBg(g, s, t);
  for (const cr of s.crowds || []) crowd(g, cr, s, t);
  const chars = (s.characters || []).map(ch => [ch, charState(ch, s, t)]).sort((a, b) => a[1].y - b[1].y);
  for (const [ch, st] of chars) drawCharacter(g, Object.assign({ seed: ch.id.length }, CAST()[ch.cast || ch.id]), st);
  if (s.fg !== false) drawBg(g, s, t, '_fg');                                 // foreground layer (walls, branches) in front of the cast
  for (const fx of s.fx || []) {
    if (fx.type === 'rockets') rocketVolley(g, Object.assign({}, fx, { from: [fx.from[0] * W, fx.from[1] * H], to: [fx.to[0] * W, fx.to[1] * H] }), t);
    if (fx.type === 'puff') puffs(g, fx.x * W, fx.y * H, fx.t0, t, fx.n || 7, fx.size || 70, fx.col);
    if (fx.type === 'sparks' && t >= fx.t0) sparks(g, fx.x * W, fx.y * H, t, 1);
    if (fx.type === 'impact') impactBurst(g, fx.x * W, fx.y * H, fx.t0, t, fx.r || 220);
  }
  g.setTransform(1, 0, 0, 1, 0, 0);
  for (const fx of s.fx || []) if (fx.type === 'glow') fireGlow(g, clamp((t - fx.t0) / 0.6) * (fx.amount ?? 1), fx.col);
  if (s.tint) { g.fillStyle = s.tint; g.fillRect(0, 0, W, H); }
}
function shotIndex(t) { for (let i = 0; i < SCENES.length; i++) if (t < SCENES[i].end) return i; return SCENES.length - 1; }
function blurDraw(dst, src, x, y, amt, sc = 1) {
  dst.save(); dst.globalAlpha = 1; dst.translate(W / 2 + x, H / 2 + y); dst.scale(sc, sc); dst.drawImage(src, -W / 2, -H / 2);
  if (amt > 1) for (let k = 0; k < 8; k++) { dst.globalAlpha = 0.15; dst.drawImage(src, -W / 2 + (k / 7 - 0.5) * amt, -H / 2); }
  dst.restore();
}
const TR = 0.15;
function compose(t) {
  const i = shotIndex(t), s = SCENES[i], next = SCENES[i + 1], prev = SCENES[i - 1];
  X.setTransform(1, 0, 0, 1, 0, 0); X.fillStyle = '#000'; X.fillRect(0, 0, W, H);
  let p = null, a = i, b = i + 1, kind = null;
  if (next && (s.transition === 'whip' || s.transition === 'zoom') && t > s.end - TR) { p = (t - (s.end - TR)) / (2 * TR); kind = s.transition; }
  else if (prev && (prev.transition === 'whip' || prev.transition === 'zoom') && t < s.start + TR) { p = (t - (s.start - TR)) / (2 * TR); kind = prev.transition; a = i - 1; b = i; }
  if (p == null) { renderShot(AX, i, t); X.drawImage(A, 0, 0); }
  else {
    renderShot(AX, a, Math.min(t, SCENES[a].end - 0.001)); renderShot(BX, b, Math.max(t, SCENES[b].start));
    const e = ease5(p), amt = Math.sin(p * Math.PI) * 150;
    if (kind === 'whip') { blurDraw(X, A, -e * W, 0, amt); blurDraw(X, B, W - e * W, 0, amt); }
    else { X.globalAlpha = 1; blurDraw(X, A, 0, 0, 0, 1 + e * 0.6); X.globalAlpha = e; X.drawImage(B, 0, 0); X.globalAlpha = 1; }
  }
}
function renderFrame(f) {
  const t = f / FPS;
  if (FEAT.motionBlur && MODE === 'final') motionBlurFrame(t); else compose(t);
  X.setTransform(1, 0, 0, 1, 0, 0); X.globalAlpha = 1; X.filter = 'none';
  // vignette (after the blur, so it stays put), then sharp captions and debug overlays
  const vg = X.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.75); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.38)');
  X.fillStyle = vg; X.fillRect(0, 0, W, H);
  captions(t);
  if (DEBUG.has('depth') && FEAT.depth && CUR_CAM) depthDebug(X, CUR_CAM.s, CUR_CAM.cam);
  if (DEBUG.size && window.drawDebug) window.drawDebug(X, t);
  return true;
}
// ---------------- motion blur: N sub-frames across a 180-degree shutter, averaged in linear light ----------------
const S2L = new Float32Array(256).map((_, i) => { const c = i / 255; return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); });
const L2S = new Uint8ClampedArray(4096).map((_, i) => { const c = i / 4095; return Math.round(255 * (c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 1 / 2.4) - 0.055)); });
let ACC = null, MBSTAT = { frames: 0, reused: 0 };
const [TINY, TX] = (() => { const c = document.createElement('canvas'); c.width = 135; c.height = 240; return [c, c.getContext('2d', { willReadFrequently: true })]; })();
function subTime(t, k, n, shutter) {
  let ts = t + (n === 1 ? 0 : (k / (n - 1) - 0.5)) * shutter / FPS;
  const i = shotIndex(t), j = shotIndex(ts), s = SCENES[i];
  // never blend across a hard cut (whip/zoom transitions are continuous, so they may blur across)
  if (j !== i) { const a = Math.min(i, j), cutT = SCENES[a].end, tr = SCENES[a].transition;
    if (tr !== 'whip' && tr !== 'zoom') ts = j > i ? Math.min(ts, s.end - 1e-4) : Math.max(ts, s.start); }
  return Math.max(0, ts);
}
function tinySnap() { TX.drawImage(cv, 0, 0, 135, 240); return TX.getImageData(0, 0, 135, 240).data; }
function motionBlurFrame(t) {
  const mb = SCRIPT.motion_blur || {}, n = Math.max(1, mb.samples || 8), shutter = mb.shutter ?? 0.5;
  MBSTAT.frames++;
  if (n === 1) return compose(t);
  // speed-up: if nothing moved more than ~1 px across the shutter, reuse the sharp frame
  compose(subTime(t, 0, n, shutter)); const a = tinySnap().slice();
  compose(subTime(t, n - 1, n, shutter)); const b = tinySnap();
  let moved = 0; for (let i = 0; i < a.length; i += 4) if (Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]) > 24) moved++;
  if (moved < 6) { MBSTAT.reused++; return compose(t); }
  if (!ACC) ACC = new Float32Array(W * H * 3);
  ACC.fill(0);
  const add = () => { const d = X.getImageData(0, 0, W, H).data;
    for (let p = 0, q = 0; p < d.length; p += 4, q += 3) { ACC[q] += S2L[d[p]]; ACC[q + 1] += S2L[d[p + 1]]; ACC[q + 2] += S2L[d[p + 2]]; } };
  add();                                                   // the last sub-frame is already on the canvas
  for (let k = 0; k < n - 1; k++) { compose(subTime(t, k, n, shutter)); add(); }
  const img = X.createImageData(W, H), o = img.data, kN = 4095 / n;
  for (let p = 0, q = 0; p < o.length; p += 4, q += 3) { o[p] = L2S[Math.min(4095, (ACC[q] * kN) | 0)]; o[p + 1] = L2S[Math.min(4095, (ACC[q + 1] * kN) | 0)]; o[p + 2] = L2S[Math.min(4095, (ACC[q + 2] * kN) | 0)]; o[p + 3] = 255; }
  X.setTransform(1, 0, 0, 1, 0, 0); X.putImageData(img, 0, 0);
}
// export: FINAL = full 1080x1920, DRAFT = half resolution
const [HALF, HX] = (() => { const c = document.createElement('canvas'); c.width = W / 2; c.height = H / 2; return [c, c.getContext('2d')]; })();
window.exportFrame = (f, q = 0.94) => { renderFrame(f); if (MODE === 'draft') { HX.drawImage(cv, 0, 0, W / 2, H / 2); return HALF.toDataURL('image/jpeg', q); } return cv.toDataURL('image/jpeg', q); };
window.MBSTAT = MBSTAT;
window.renderFrame = renderFrame;
(async () => {
  SCRIPT = await (await fetch('../' + EP + '/script.json')).json();
  const wj = await (await fetch('../' + EP + '/work/words.json')).json(); WORDS = wj.words; SCRIPT._duration = wj.duration;
  AMP = await (await fetch('../' + EP + '/work/amp.json')).json(); AFPS = wj.fps || 30;
  { let e = 0; AMP = AMP.map(v => (e = v > e ? lerp(e, v, 0.75) : lerp(e, v, 0.35))); }
  FPS = SCRIPT.fps || 60; FEAT = Object.assign(FEAT, SCRIPT.features || {}); window.FEAT = FEAT; window.MODE = MODE;
  window.FPS = FPS; window.FRAMES = Math.round(wj.duration * FPS);
  resolve(); buildCaptions();
  const bgs = [...new Set(SCRIPT.scenes.map(s => s.bg).filter(Boolean))];
  const names = bgs.concat(bgs.map(n => n.replace(/(\.\w+)$/, '_fg$1')));   // optional foreground layer: <bg>_fg.png
  await Promise.all(names.map(n => new Promise(res => { const im = new Image(); im.onload = () => { BG[n] = im; res(); }; im.onerror = () => res(); im.src = '../' + EP + '/backgrounds/' + n; })));
  if (FEAT.depth) await loadLocations(EP, SCRIPT);
  if (FEAT.lipSync) { try { VISKEYS = (await (await fetch('../' + EP + '/work/visemes.json')).json()).keys; } catch (e) { console.error('no visemes.json: run tools/visemes.py'); } }
  await document.fonts.load('800 90px Poppins');
  window.SCENES = SCENES; window.CHUNKS = CHUNKS; window.ready = true;
})().catch(e => { console.error('compositor error: ' + e.message); window.loadError = e.message; });
