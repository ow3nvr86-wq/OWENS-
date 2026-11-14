// REAL 3D DEPTH (feature flag "depth"): a multiplane camera over depth layers.
// A location is a stack of layer images, each at a distance z from the camera (sky 1000, far 400, mid 150, fg 50,
// near 20). Layer images are authored ~30 % larger than the frame. The camera has a position (x, y, z), a focal
// length f and a roll. Every plane at depth z projects with
//     screen = centre + (P - C) * f / (z - Cz),   P = rest-pixel offset * z / F0
// so a DOLLY (Cz) gives parallax and a ZOOM (f) does not. Characters, crowds and effects carry a z too and are
// drawn with the same projection, sorted far to near. Everything is a pure function of time.
const F0 = 1000;                         // rest focal length (world units are arbitrary; mid ground sits at z = 150)
const LAYER_Z = { sky: 1000, far: 400, mid: 150, fg: 50, near: 20 };
const OVERSCAN = 1.3;
const LOC = {};                          // name -> { layers: [{img, z, name, dof, baked}], sky }

function zOf(v, dflt = LAYER_Z.mid) { if (v == null) return dflt; return typeof v === 'number' ? v : (LAYER_Z[v] ?? dflt); }

// ---- load + bake: atmosphere (farther = lower contrast/saturation, tinted toward the sky) and lens blur ----
function bakeLayer(img, z, sky, grade, opts = {}) {
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; const g = c.getContext('2d');
  const atmo = (opts.atmosphere ?? 1) * Math.pow(clamp((z - 60) / 940), 0.8);
  g.filter = `${grade || ''} contrast(${1 - 0.32 * atmo}) saturate(${1 - 0.3 * atmo})` + (opts.blur ? ` blur(${opts.blur}px)` : '');
  g.drawImage(img, 0, 0); g.filter = 'none';
  if (atmo > 0.01) { g.globalCompositeOperation = 'source-atop'; g.globalAlpha = 0.42 * atmo; g.fillStyle = sky; g.fillRect(0, 0, c.width, c.height); }
  return c;
}
async function loadLocations(ep, script) {
  const locs = script.locations || {};
  const loadImg = src => new Promise(res => { const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null); im.src = src; });
  for (const [name, L] of Object.entries(locs)) {
    const sky = L.sky || '#a9c6e0', focusZ = zOf(L.focus, LAYER_Z.mid), layers = [];
    for (const ly of L.layers) {
      const img = await loadImg('../' + ep + '/backgrounds/' + ly.img); if (!img) { console.error('missing layer ' + ly.img); continue; }
      const z = zOf(ly.z ?? ly.name);
      // depth of field: the near overlay (or any layer marked dof) gets a soft blur from its distance to the focus plane
      const blur = (ly.dof ?? z <= 25) ? clamp(600 * Math.abs(1 / z - 1 / focusZ), 0, 16) * (MODE === 'draft' ? 0.5 : 1) : 0;
      layers.push({ name: ly.name || String(z), z, img, baked: bakeLayer(img, z, sky, script.grade, { atmosphere: L.atmosphere, blur: Math.round(blur) }), opaque: !!ly.opaque });
    }
    layers.sort((a, b) => b.z - a.z);
    LOC[name] = { layers, sky, focusZ };
  }
}

// ---- camera ----
// preset moves are written as what they do to the mid ground (scale, px) and turned into real 3D camera motion:
//   push/pull = dolly toward/away from the focus point, pan_* = truck, tilt_* = pedestal, drift = small truck,
//   punch = focal-length zoom (no parallax), roll via camera.roll ([from, to] degrees).
function cam3At(s, t) {
  const m = s.camera || {}, base = MOVES[m.move || 'push'], L = LOC[s.loc];
  const v = clamp((t - s.start) / Math.max(0.3, s.end - s.start)), u = ease5(lerp(v, ease(v), 0.4));
  const k = m.amount ?? 1, zf = zOf(m.focusZ, L ? L.focusZ : LAYER_Z.mid);
  const foc = m.focus || [0.5, 0.5], pfx = (foc[0] - 0.5) * W, pfy = (foc[1] - 0.5) * H;
  let f = F0 * (m.zoom || 1), Cx = 0, Cy = 0, Cz = 0;
  const move = m.move || 'push';
  if (move === 'punch') f *= lerp(1, lerp(base[0], base[1], u), k);
  else {
    const sMid = lerp(1, lerp(base[0], base[1], u), k);              // wanted scale of the focus plane
    Cz = zf * (1 - 1 / sMid);                                          // dolly that gives it
    const kf = zf * f / (F0 * (zf - Cz));
    Cx = pfx * (kf - 1) * (zf - Cz) / f; Cy = pfy * (kf - 1) * (zf - Cz) / f;   // along the ray, so the focus point holds still
    Cx -= lerp(base[2], base[3], u) * k * (zf - Cz) / f;                       // truck / pedestal (px at the focus plane)
    Cy -= lerp(base[4], base[5], u) * k * (zf - Cz) / f;
  }
  if (m.from || m.to) {                                                // explicit 3D move: {x, y, z, f, roll}
    const a = Object.assign({ x: 0, y: 0, z: 0, f: 1, roll: 0 }, m.from), b = Object.assign({}, a, m.to);
    Cx += lerp(a.x, b.x, u); Cy += lerp(a.y, b.y, u); Cz += lerp(a.z, b.z, u); f *= lerp(a.f, b.f, u);
  }
  const roll = Array.isArray(m.roll) ? lerp(m.roll[0], m.roll[1], u) : (m.roll || 0);
  // tiny seeded handheld drift (< 4 px) + impact shakes, applied after projection
  const hs = m.handheld ?? 1, sd = (s.wi || 0) * 0.37;
  let hx = noise(t * 0.45 + sd, 1) * 3.5 * hs, hy = noise(t * 0.4 + sd, 2) * 3.5 * hs;
  for (const fx2 of s.fx || []) if (fx2.shake && t > fx2.t0 && t < fx2.t0 + 0.6) { const a = fx2.shake * Math.exp(-(t - fx2.t0) * 8); hx += Math.sin(t * 90) * a; hy += Math.cos(t * 77) * a; }
  for (const sh of s._shakes || []) if (t > sh.t0 && t < sh.t0 + 0.7) { const a = sh.amp * Math.exp(-(t - sh.t0) * 7); hx += Math.sin(t * 83 + sh.t0) * a; hy += Math.cos(t * 71 + sh.t0) * a; }
  return { x: Cx, y: Cy, z: Cz, f, roll: roll * Math.PI / 180, hx, hy };
}
// the 2D affine of the plane at depth z: translate(c - C*f/(z-Cz)) . scale(k) . translate(-c)
function planeK(cam, z) { const d = Math.max(1, z - cam.z); return { k: z * cam.f / (F0 * d), ox: -cam.x * cam.f / d, oy: -cam.y * cam.f / d }; }
function setPlane(g, cam, z) {
  const { k, ox, oy } = planeK(cam, z), c = Math.cos(cam.roll), sn = Math.sin(cam.roll);
  // post: roll about the centre + handheld; then the plane projection
  const a = k * c, b = k * sn, cc = -k * sn, d = k * c;
  const tx0 = W / 2 + ox - k * W / 2, ty0 = H / 2 + oy - k * H / 2;            // plane transform (no roll)
  const px = tx0 - W / 2, py = ty0 - H / 2;                                      // rotate that about the centre
  g.setTransform(a, b, cc, d, W / 2 + c * px - sn * py + cam.hx, H / 2 + sn * px + c * py + cam.hy);
}
// where a rest-frame point on plane z lands on screen (used by impacts / shakes / debug)
function projectPt(cam, z, x, y) { const { k, ox, oy } = planeK(cam, z); return [W / 2 + ox + (x - W / 2) * k + cam.hx, H / 2 + oy + (y - H / 2) * k + cam.hy]; }

function drawLayer(g, L, cam, layer) {
  setPlane(g, cam, layer.z);
  const w = W * OVERSCAN, h = H * OVERSCAN, x0 = (W - w) / 2, y0 = (H - h) / 2;
  // edge guard: if a move would reveal the layer's border, scale it up about the frame centre just enough
  const { k, ox, oy } = planeK(cam, layer.z);
  const l = W / 2 + ox + (x0 - W / 2) * k, r = W / 2 + ox + (x0 + w - W / 2) * k, t_ = H / 2 + oy + (y0 - H / 2) * k, b = H / 2 + oy + (y0 + h - H / 2) * k;
  const need = Math.max(1, (W / 2 + 12) / Math.max(1, W / 2 - l), (W / 2 + 12) / Math.max(1, r - W / 2), (H / 2 + 12) / Math.max(1, H / 2 - t_), (H / 2 + 12) / Math.max(1, b - H / 2));
  if (need > 1) { g.translate(W / 2, H / 2); g.scale(need, need); g.translate(-W / 2, -H / 2); }
  g.drawImage(layer.baked, x0, y0, w, h);
  if (DEBUG.has('depth')) { g.strokeStyle = 'hsl(' + (layer.z % 360) + ',90%,60%)'; g.lineWidth = 6 / k; g.strokeRect(x0 + 8, y0 + 8, w - 16, h - 16); }
}
// debug labels drawn in screen space after everything else
function depthDebug(g, s, cam) {
  const L = LOC[s.loc]; if (!L) return;
  g.setTransform(1, 0, 0, 1, 0, 0); g.font = '700 30px monospace'; g.textAlign = 'left';
  L.layers.forEach((ly, i) => { const [x, y] = projectPt(cam, ly.z, 40, 140 + i * 46); g.fillStyle = '#000a'; g.fillRect(24, 112 + i * 46, 470, 40);
    g.fillStyle = 'hsl(' + (ly.z % 360) + ',90%,65%)'; g.fillText(`${ly.name}  z=${ly.z}  k=${planeK(cam, ly.z).k.toFixed(3)}`, 36, 142 + i * 46); });
  g.fillStyle = '#fff'; g.fillText(`cam x=${cam.x.toFixed(1)} y=${cam.y.toFixed(1)} z=${cam.z.toFixed(1)} f=${cam.f.toFixed(0)}`, 36, 112 + L.layers.length * 46 + 36);
}
