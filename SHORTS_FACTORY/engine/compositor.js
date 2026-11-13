// Episode compositor: background -> crowd -> characters -> effects -> captions, with a camera move on every shot and
// whip/zoom/cut transitions. Everything is driven by <episode>/script.json, work/words.json and work/amp.json.
// Open as engine/index.html?ep=episodes/<name>. window.renderFrame(f) draws frame f (f / 30 s).
const cv = document.getElementById('c'), X = cv.getContext('2d');
const mk = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return [c, c.getContext('2d')]; };
const [A, AX] = mk(), [B, BX] = mk();
const EP = new URLSearchParams(location.search).get('ep');
let SCRIPT, WORDS, AMP, SCENES = [], CHUNKS = [], BG = {}, NORM = [];

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
    for (const ch of s.characters || []) { for (const k of ch.keys || []) k.t = T(k.cue); if (ch.talk) ch.talkT = ch.talk.map(T); if (ch.move) { ch.move.t0 = T(ch.move.from) ?? s.start; ch.move.t1 = T(ch.move.to) ?? s.end; } }
    for (const fx of s.fx || []) { fx.t0 = T(fx.at) ?? s.start; fx.seed = fx.seed ?? (s.wi % 97); }
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
  const age = (t - ch.start) * FPS, sc = age >= 4 ? 1 : 0.85 + 0.15 * eOut(age / 4);
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
  const u = ease(clamp((t - s.start) / Math.max(0.3, s.end - s.start)));
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
function amp(t) { return AMP[Math.min(AMP.length - 1, Math.max(0, Math.round(t * FPS)))] || 0; }
function charState(ch, s, t) {
  const st = { x: ch.x * W, y: ch.y * H, scale: ch.scale || 1, flip: !!ch.flip, mood: ch.mood, action: ch.action || 'idle', prop: ch.prop, look: ch.look || 0, headTilt: 0 };
  for (const k of ch.keys || []) if (t >= k.t) Object.assign(st, Object.fromEntries(Object.entries(k).filter(([n]) => !['cue', 't'].includes(n))), k.x != null ? { x: k.x * W } : {}, k.y != null ? { y: k.y * H } : {});
  if (ch.move) { const u = ease(clamp((t - ch.move.t0) / Math.max(0.2, ch.move.t1 - ch.move.t0))); st.x = lerp(ch.x, ch.move.x ?? ch.x, u) * W; st.y = lerp(ch.y, ch.move.y ?? ch.y, u) * H; st.phase = (t - ch.move.t0) * 9; }
  if (st.action === 'march' || st.action === 'run' || st.action === 'walk') st.phase = st.phase ?? t * (st.action === 'run' ? 14 : 8);
  // blink every 2-4 s; brow/mood changes happen inside a blink
  const seed = (ch.id || '').length * 7.3;
  const per = 2.2 + hash(seed) * 1.8; st.blink = ((t + hash(seed + 1) * per) % per) < 0.1;
  for (const k of ch.keys || []) if (k.mood && Math.abs(t - k.t) < 0.05) st.blink = true;
  if (ch.talkT && t >= ch.talkT[0] && t <= ch.talkT[1]) { st.talk = amp(t); if (st.action === 'idle') st.action = 'talk'; }
  st.t = t; return st;
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
      action, phase: t * (action === 'run' ? 13 : 7.5) + hash(p.i * 4.4) * 6.28, blink: ((t + hash(p.i) * 3) % 3) < 0.1, look: cr.look || 0, lean: action === 'run' ? (cr.flip ? 0.12 : -0.12) : 0 });
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
function renderShot(g, i, t) {
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
function renderFrame(f) {
  const t = f / FPS, i = shotIndex(t), s = SCENES[i], next = SCENES[i + 1], prev = SCENES[i - 1];
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
  // vignette + light grain
  const vg = X.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.75); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.38)');
  X.fillStyle = vg; X.fillRect(0, 0, W, H);
  captions(t);
  return true;
}
window.renderFrame = renderFrame;
(async () => {
  SCRIPT = await (await fetch('../' + EP + '/script.json')).json();
  const wj = await (await fetch('../' + EP + '/work/words.json')).json(); WORDS = wj.words; SCRIPT._duration = wj.duration;
  AMP = await (await fetch('../' + EP + '/work/amp.json')).json();
  window.FRAMES = Math.round(wj.duration * FPS);
  resolve(); buildCaptions();
  const bgs = [...new Set(SCRIPT.scenes.map(s => s.bg))];
  const names = bgs.concat(bgs.map(n => n.replace(/(\.\w+)$/, '_fg$1')));   // optional foreground layer: <bg>_fg.png
  await Promise.all(names.map(n => new Promise(res => { const im = new Image(); im.onload = () => { BG[n] = im; res(); }; im.onerror = () => res(); im.src = '../' + EP + '/backgrounds/' + n; })));
  await document.fonts.load('800 90px Poppins');
  window.SCENES = SCENES; window.CHUNKS = CHUNKS; window.ready = true;
})().catch(e => { console.error('compositor error: ' + e.message); window.loadError = e.message; });
