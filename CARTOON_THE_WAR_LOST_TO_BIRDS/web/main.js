// Cartoon engine: toon materials, ink contract, cards, render targets and post (colour -> normal/depth -> ink+grade
// -> depth of field). Exposes window.renderFrame(f) and window.ready. The world and story live in world.js/story.js.
import * as THREE from './vendor/three.module.js';
import { DRAW } from './cast.js';
import { buildWorld } from './world.js';
import { applyFrame, FRAMES } from './story.js';

const params = new URLSearchParams(location.search);
const SCALE = parseFloat(params.get('scale') || '1');
export const W = Math.round(1080 * SCALE), H = Math.round(1920 * SCALE);
const FAR = 1.0e5;

// ---------- renderer ----------
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, W / H, 0.05, 6000);
scene.add(camera);

// ---------- toon materials ----------
const grad = new THREE.DataTexture(new Uint8Array([120, 120, 120, 255, 255, 255, 255, 255]), 2, 1);
grad.minFilter = grad.magFilter = THREE.NearestFilter; grad.needsUpdate = true;
export function toon(color = '#ffffff', map = null, opt = {}) {
  const m = new THREE.MeshToonMaterial(Object.assign({ color: new THREE.Color(color), gradientMap: grad }, opt));
  if (map) m.map = map;
  return m;
}
export function flat(color, map = null, opt = {}) {
  const m = new THREE.MeshBasicMaterial(Object.assign({ color: new THREE.Color(color) }, opt));
  if (map) m.map = map; return m;
}

// ---------- add helpers ----------
// add(geom, mat, pos, rot, scale, parent) ; kind: 'world' (inked) | 'card' (alpha-tested, never inked) | 'hide'
export function add(geom, mat, pos = [0, 0, 0], rot = [0, 0, 0], scl = [1, 1, 1], parent = scene, kind = 'world') {
  const m = new THREE.Mesh(geom, mat);
  m.position.set(...pos); m.rotation.set(...rot); m.scale.set(...scl);
  m.castShadow = kind === 'world' || kind === 'card'; m.receiveShadow = kind === 'world';
  m.userData.kind = kind;
  parent.add(m); return m;
}
// box with UVs scaled to its size so textures keep a constant density (texel per metre = d)
export function tbox(w, h, d, mat, pos, rot = [0, 0, 0], parent = scene, density = 0.5) {
  const g = new THREE.BoxGeometry(w, h, d);
  const uv = g.attributes.uv, nrm = g.attributes.normal;
  for (let i = 0; i < uv.count; i++) {
    const nx = Math.abs(nrm.getX(i)), ny = Math.abs(nrm.getY(i));
    const sx = nx > 0.5 ? d : w, sy = ny > 0.5 ? d : h;
    uv.setXY(i, uv.getX(i) * sx * density, uv.getY(i) * sy * density);
  }
  return add(g, mat, pos, rot, [1, 1, 1], parent);
}
export function group(pos = [0, 0, 0], rot = [0, 0, 0], parent = scene) {
  const g = new THREE.Group(); g.position.set(...pos); g.rotation.set(...rot); parent.add(g); return g;
}

// ---------- sky ----------
const skyUni = { top: { value: new THREE.Color('#5aa7e8') }, mid: { value: new THREE.Color('#a8d4f2') }, bot: { value: new THREE.Color('#f3e3c0') } };
const sky = new THREE.Mesh(new THREE.SphereGeometry(4500, 32, 16), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false, uniforms: skyUni,
  vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
  fragmentShader: `uniform vec3 top, mid, bot; varying vec3 vP;
    void main(){ float h = normalize(vP).y; vec3 c = h > 0.08 ? mix(mid, top, smoothstep(0.08, 0.6, h)) : mix(bot, mid, smoothstep(-0.05, 0.08, h));
      gl_FragColor = vec4(c, 1.0); }`,
}));
sky.userData.kind = 'sky'; sky.renderOrder = -10; scene.add(sky);

// ---------- lights ----------
const hemi = new THREE.HemisphereLight('#cfe6ff', '#b08a5a', 1.2); scene.add(hemi);
const sun = new THREE.DirectionalLight('#fff1d6', 2.6);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0015; sun.shadow.normalBias = 0.06;
scene.add(sun); scene.add(sun.target);
scene.fog = new THREE.Fog('#f3e3c0', 120, 900);

export const LIGHTS = {
  day:    { az: 140, el: 52, sun: '#fff1d6', sunI: 2.6, hemiTop: '#d6ebff', hemiBot: '#b58d5c', hemiI: 1.25, sky: ['#4f9fe6', '#a9d6f4', '#f4e4c2'], fog: '#efdfbd', fogN: 120, fogF: 950, cardTint: '#ffffff', sat: 1.12, gain: 1.0, lift: 0.0 },
  golden: { az: 250, el: 14, sun: '#ffb064', sunI: 2.9, hemiTop: '#ffd7a8', hemiBot: '#8f5a3a', hemiI: 1.0, sky: ['#5f7fc6', '#f0a874', '#ffd08a'], fog: '#f2b780', fogN: 90, fogF: 800, cardTint: '#ffe2c4', sat: 1.18, gain: 1.02, lift: 0.0 },
  night:  { az: 200, el: 40, sun: '#9fb8ff', sunI: 0.9, hemiTop: '#4a5f9c', hemiBot: '#1c2238', hemiI: 0.9, sky: ['#0d1638', '#24366e', '#3d4f86'], fog: '#2a3866', fogN: 60, fogF: 600, cardTint: '#8ea2d6', sat: 0.95, gain: 1.0, lift: 0.02 },
  tent:   { az: 100, el: 60, sun: '#ffe0b0', sunI: 2.0, hemiTop: '#ffe8c8', hemiBot: '#7a5a3a', hemiI: 1.3, sky: ['#8aa0b8', '#c8c2b0', '#e0d0b0'], fog: '#d8c8a8', fogN: 60, fogF: 400, cardTint: '#fff0dc', sat: 1.08, gain: 1.0, lift: 0.0 },
};
const C = c => new THREE.Color(c);
function mixLight(a, b, t) {
  const o = {};
  for (const k in a) {
    if (typeof a[k] === 'number') o[k] = a[k] + (b[k] - a[k]) * t;
    else if (Array.isArray(a[k])) o[k] = a[k].map((v, i) => '#' + C(v).lerp(C(b[k][i]), t).getHexString());
    else o[k] = '#' + C(a[k]).lerp(C(b[k]), t).getHexString();
  }
  return o;
}
let cardTint = new THREE.Color('#ffffff');
let grade = { sat: 1.1, gain: 1, lift: 0 };
function applyLight(L, focus) {
  const az = THREE.MathUtils.degToRad(L.az), el = THREE.MathUtils.degToRad(L.el);
  const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
  const c = new THREE.Vector3(...focus.center);
  sun.position.copy(c).addScaledVector(dir, 120); sun.target.position.copy(c);
  const r = focus.radius || 30, sc = sun.shadow.camera;
  sc.left = -r; sc.right = r; sc.top = r; sc.bottom = -r; sc.near = 1; sc.far = 400; sc.updateProjectionMatrix();
  sun.color.set(L.sun); sun.intensity = L.sunI;
  hemi.color.set(L.hemiTop); hemi.groundColor.set(L.hemiBot); hemi.intensity = L.hemiI;
  skyUni.top.value.set(L.sky[0]); skyUni.mid.value.set(L.sky[1]); skyUni.bot.value.set(L.sky[2]);
  scene.fog.color.set(L.fog); scene.fog.near = L.fogN; scene.fog.far = L.fogF;
  cardTint.set(L.cardTint);
  grade = { sat: L.sat, gain: L.gain, lift: L.lift };
}

// ---------- cards ----------
// A card is a vertical plane, origin at the soles, turned to the camera on yaw only. Its canvas is redrawn only when
// its pose key changes; textures are shared between cards with the same key (an LRU keeps memory bounded).
const DESIGN = [600, 1000];
const texCache = new Map();
function cardTexture(kind, outfit, pose, res, flip) {
  const key = kind + '|' + outfit + '|' + res + '|' + (flip ? 1 : 0) + '|' + JSON.stringify(pose);
  let e = texCache.get(key);
  if (e) { texCache.delete(key); texCache.set(key, e); return e.tex; }
  const cw = Math.round(DESIGN[0] * res), ch = Math.round(DESIGN[1] * res);
  const cv = document.createElement('canvas'); cv.width = cw; cv.height = ch;
  const g = cv.getContext('2d');
  g.scale(res, res);
  if (flip) { g.translate(DESIGN[0], 0); g.scale(-1, 1); }
  DRAW[kind](g, outfit, pose);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter;
  e = { tex: t }; texCache.set(key, e);
  while (texCache.size > 140) { const [k, v] = texCache.entries().next().value; v.tex.dispose(); texCache.delete(k); }
  return t;
}
const cards = [];
const blobTex = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  const gr = g.createRadialGradient(64, 64, 4, 64, 64, 62); gr.addColorStop(0, 'rgba(40,25,20,0.55)'); gr.addColorStop(1, 'rgba(40,25,20,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128); const t = new THREE.CanvasTexture(c); return t;
})();
export function makeCard(name, kind, outfit, height) {
  const w = height * DESIGN[0] / DESIGN[1];
  const geo = new THREE.PlaneGeometry(w, height); geo.translate(0, height / 2 - height * 25 / 1000, 0);
  const mat = new THREE.MeshBasicMaterial({ alphaTest: 0.5, side: THREE.DoubleSide, fog: true });
  const mesh = new THREE.Mesh(geo, mat); mesh.userData.kind = 'card'; mesh.castShadow = true;
  mesh.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, alphaTest: 0.5 });
  const blob = new THREE.Mesh(new THREE.PlaneGeometry(w * 0.9, w * 0.5), new THREE.MeshBasicMaterial({ map: blobTex, transparent: true, depthWrite: false }));
  blob.rotation.x = -Math.PI / 2; blob.userData.kind = 'hide';
  scene.add(mesh); scene.add(blob);
  const c = { name, kind, outfit, height, mesh, blob, pose: {}, visible: false, pos: [0, 0, 0], flip: false, lean: 0, ground: 0, hiRes: 1 };
  cards.push(c); return c;
}
const q = (v, s = 0.02) => typeof v === 'number' ? Math.round(v / s) * s : v;
function drawActors() {
  const camPos = camera.position;
  for (const c of cards) {
    c.mesh.visible = c.blob.visible = c.visible;
    if (!c.visible) continue;
    c.mesh.position.set(...c.pos);
    const dx = camPos.x - c.pos[0], dz = camPos.z - c.pos[2];
    c.mesh.rotation.set(0, Math.atan2(dx, dz), c.lean || 0);
    c.mesh.scale.setScalar(c.scale || 1);
    c.blob.visible = c.visible && c.blobOn !== false;
    c.blob.position.set(c.pos[0], (c.ground ?? 0) + 0.03, c.pos[2]);
    const lift = Math.max(0, c.pos[1] - (c.ground ?? 0));
    c.blob.scale.setScalar((c.scale || 1) * Math.max(0.4, 1 - lift * 0.25));
    // texture resolution from projected size
    const d = Math.max(0.5, Math.hypot(dx, camPos.y - c.pos[1], dz));
    const px = (c.height * (c.scale || 1)) / (2 * d * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) * H;
    const res = px > 1300 ? 2.0 : px > 650 ? 1.2 : px > 300 ? 0.6 : 0.3;
    const pose = {};
    for (const k in c.pose) pose[k] = k === 'f' ? Math.round(c.pose[k]) : q(c.pose[k]);
    if (pose.run != null) pose.run = Math.round(pose.run * 12) / 12 % 1;     // 12 run drawings per stride
    // the camera-facing yaw flips which way the character faces; flip keeps screen direction consistent
    const t = cardTexture(c.kind, c.outfit, pose, res, c.flip);
    if (c.mesh.material.map !== t) {
      c.mesh.material.map = t; c.mesh.material.needsUpdate = true;
      c.mesh.customDepthMaterial.map = t; c.mesh.customDepthMaterial.needsUpdate = true;
    }
    c.mesh.material.color.copy(cardTint).multiplyScalar(c.tint ?? 1);
  }
}

// ---------- normal + depth pass ----------
const ndWorld = new THREE.ShaderMaterial({
  vertexShader: `varying vec3 vN; varying float vZ;
    #include <common>
    void main(){
      #include <beginnormal_vertex>
      #include <defaultnormal_vertex>
      #include <begin_vertex>
      #include <project_vertex>
      vN = normalize(transformedNormal); vZ = -mvPosition.z; }`,
  uniforms: {},
  fragmentShader: `varying vec3 vN; varying float vZ; void main(){ gl_FragColor = vec4(normalize(vN)*0.5+0.5, vZ); }`,
  side: THREE.DoubleSide,
});
const ndSky = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false,
  vertexShader: 'void main(){ gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
  uniforms: { far: { value: FAR } },
  fragmentShader: 'uniform float far; void main(){ gl_FragColor = vec4(0.5, 0.5, 1.0, far); }' });
const ndCardMats = new Map();
function ndCard(map) {
  let m = ndCardMats.get(map);
  if (!m) {
    m = new THREE.ShaderMaterial({
      uniforms: { map: { value: map } }, side: THREE.DoubleSide,
      vertexShader: `varying vec2 vUv; varying float vZ;
        #include <common>
        void main(){ vUv = uv;
          #include <begin_vertex>
          #include <project_vertex>
          vZ = -mvPosition.z; }`,
      fragmentShader: `uniform sampler2D map; varying vec2 vUv; varying float vZ;
        void main(){ if (texture2D(map, vUv).a < 0.5) discard; gl_FragColor = vec4(0.0, 0.0, 0.0, vZ); }`,
    });
    ndCardMats.set(map, m);
  }
  return m;
}
const saved = new Map();
function swapForNd(on) {
  scene.traverse(o => {
    if (!o.isMesh) return;
    if (on) {
      saved.set(o, [o.material, o.visible]);
      const k = o.userData.kind;
      if (k === 'hide') o.visible = false;
      else if (k === 'sky') o.material = ndSky;
      else if (k === 'card') { const map = (Array.isArray(o.material) ? o.material[0] : o.material).map; o.material = ndCard(map); }
      else o.material = ndWorld;
    } else { const s = saved.get(o); if (s) { o.material = s[0]; o.visible = s[1]; } }
  });
  if (!on) saved.clear();
}

// ---------- render targets and post ----------
const rtColor = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
const rtND = new THREE.WebGLRenderTarget(W, H, { type: THREE.FloatType, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
const rtInk = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const quadScene = new THREE.Scene();
const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2)); quadScene.add(quad);

const inkMat = new THREE.ShaderMaterial({
  uniforms: {
    tColor: { value: rtColor.texture }, tND: { value: rtND.texture }, res: { value: new THREE.Vector2(W, H) },
    inkR: { value: 4.0 * SCALE }, inkCol: { value: new THREE.Color('#1f1219') }, far: { value: FAR },
    sat: { value: 1.1 }, gain: { value: 1.0 }, lift: { value: 0.0 }, vig: { value: 0.22 }, flash: { value: 0 }, fade: { value: 0 },
    flashCol: { value: new THREE.Color('#ffffff') },
  },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
  fragmentShader: `uniform sampler2D tColor, tND; uniform vec2 res; uniform float inkR, far, sat, gain, lift, vig, flash, fade;
    uniform vec3 inkCol, flashCol; varying vec2 vUv;
    bool isCard(vec4 s){ return dot(s.rgb, s.rgb) < 0.0001 && s.a < far * 0.5; }
    void main(){
      vec3 col = texture2D(tColor, vUv).rgb;
      vec4 c = texture2D(tND, vUv);
      float d = c.a;
      float ink = 0.0;
      if (!isCard(c) && d < far * 0.5) {
        vec3 n = c.rgb * 2.0 - 1.0;
        for (int i = 0; i < 16; i++) {
          float a = float(i) * 0.7853982 + (i >= 8 ? 0.3927 : 0.0);
          vec2 o = vec2(cos(a), sin(a)) * inkR * (i >= 8 ? 0.55 : 1.0) / res;
          vec4 s = texture2D(tND, vUv + o);
          if (isCard(s)) continue;
          // depth jump: ink only on the near side
          if (s.a - d > max(0.06, d * 0.035)) ink = 1.0;
          else if (s.a < far * 0.5) {
            vec3 m = s.rgb * 2.0 - 1.0;
            if (dot(n, m) < 0.72 && abs(s.a - d) < d * 0.06 + 0.1) ink = max(ink, 0.85);
          }
        }
        ink *= 1.0 - smoothstep(140.0, 520.0, d);
      }
      col = mix(col, inkCol, ink);
      // grade
      float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
      col = mix(vec3(l), col, sat);
      col = col * gain + lift;
      vec2 v = vUv - 0.5; v.x *= 0.75;
      col *= 1.0 - vig * smoothstep(0.25, 0.75, length(v));
      col = mix(col, flashCol, flash);
      col *= 1.0 - fade;
      gl_FragColor = vec4(col, 1.0);
    }`,
});
// depth of field: golden-angle gather with a per-sample CoC test so a sharp subject never bleeds blur onto itself
const dofMat = new THREE.ShaderMaterial({
  uniforms: { tIn: { value: rtInk.texture }, tND: { value: rtND.texture }, res: { value: new THREE.Vector2(W, H) },
    focus: { value: 5 }, cInf: { value: 0 }, far: { value: FAR } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
  fragmentShader: `uniform sampler2D tIn, tND; uniform vec2 res; uniform float focus, cInf, far; varying vec2 vUv;
    float coc(float d){ return cInf * clamp(abs(d - focus) / max(d, 0.01), 0.0, 1.0) * (d < focus ? 1.6 : 1.0); }
    void main(){
      vec4 base = texture2D(tIn, vUv);
      if (cInf < 0.25) { gl_FragColor = vec4(base.rgb, 1.0);
        #include <colorspace_fragment>
        return; }
      float dc = min(texture2D(tND, vUv).a, 3000.0);
      float cc = coc(dc);
      vec3 acc = base.rgb; float wsum = 1.0;
      for (int i = 1; i < 48; i++) {
        float r = sqrt(float(i) / 48.0) * cInf * 1.6;
        float a = float(i) * 2.39996;
        vec2 uv = vUv + vec2(cos(a), sin(a)) * r / res;
        float ds = min(texture2D(tND, uv).a, 3000.0);
        float cs = coc(ds);
        if (ds > dc) cs = min(cs, cc);          // background can't blur over a nearer pixel
        float w = smoothstep(r - 1.5, r + 0.5, cs);
        acc += texture2D(tIn, uv).rgb * w; wsum += w;
      }
      gl_FragColor = vec4(acc / wsum, 1.0);
      #include <colorspace_fragment>
    }`,
});

// ---------- frame ----------
const world = buildWorld({ THREE, scene, add, tbox, group, toon, flat, makeCard, camera });
let lastF = -1;
function renderFrame(f) {
  const st = applyFrame(f, world);      // sets every object, card and the camera for frame f
  camera.position.set(...st.cam.pos); camera.up.set(0, 1, 0); camera.lookAt(...st.cam.look);
  camera.rotateZ(THREE.MathUtils.degToRad(st.cam.roll || 0));
  camera.fov = st.cam.fov; camera.updateProjectionMatrix();
  const L = st.lightMix ? mixLight(LIGHTS[st.lightMix[0]], LIGHTS[st.lightMix[1]], st.lightMix[2]) : LIGHTS[st.light];
  if (st.lightOverride) Object.assign(L, st.lightOverride);
  applyLight(L, st.shadow || { center: st.cam.look, radius: 30 });
  sky.position.copy(camera.position);
  drawActors();
  // colour
  renderer.setRenderTarget(rtColor); renderer.setClearColor(0x000000, 1); renderer.clear(); renderer.render(scene, camera);
  // normal + depth (fog and shadows off)
  const fog = scene.fog; scene.fog = null; renderer.shadowMap.autoUpdate = false;
  swapForNd(true);
  renderer.setRenderTarget(rtND); renderer.setClearColor(new THREE.Color(0.5, 0.5, 1.0), 1); renderer.clear();
  renderer.render(scene, camera);
  swapForNd(false); scene.fog = fog; renderer.shadowMap.autoUpdate = true;
  // ink + grade
  const u = inkMat.uniforms;
  u.sat.value = grade.sat * (st.fx?.sat ?? 1); u.gain.value = grade.gain; u.lift.value = grade.lift;
  u.flash.value = st.fx?.flash || 0; u.fade.value = st.fx?.fade || 0; u.vig.value = st.fx?.vig ?? 0.22;
  quad.material = inkMat; renderer.setRenderTarget(rtInk); renderer.render(quadScene, quadCam);
  // dof to screen
  dofMat.uniforms.focus.value = st.dof?.focus || 5; dofMat.uniforms.cInf.value = (st.dof?.cInf || 0) * SCALE;
  quad.material = dofMat; renderer.setRenderTarget(null); renderer.setClearColor(0x000000, 1); renderer.render(quadScene, quadCam);
  lastF = f;
  return true;
}
window.renderFrame = renderFrame;
window.FRAMES = FRAMES;
document.fonts.load('100px Anton').then(() => document.fonts.load('60px "Covered By Your Grace"'))
  .then(() => document.fonts.load('40px "Courier Prime"')).then(() => { world.afterFonts && world.afterFonts(); window.ready = true; });
