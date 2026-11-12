// Painted canvas textures: flat colour fields with darker seams and a little hand-made speckle.
import * as THREE from './vendor/three.module.js';
import { hash } from './motion.js';

export function canvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
export function tex(c, rep = [1, 1], srgb = true) {
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep[0], rep[1]);
  t.anisotropy = 4; if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.needsUpdate = true; return t;
}
function speckle(g, w, h, n, cols, r0 = 1, r1 = 3, seed = 1) {
  for (let i = 0; i < n; i++) {
    g.fillStyle = cols[i % cols.length];
    const x = hash(i * 3.1 + seed) * w, y = hash(i * 7.7 + seed * 2) * h, r = r0 + hash(i + seed * 5) * (r1 - r0);
    g.beginPath(); g.ellipse(x, y, r * 1.6, r, hash(i * 1.3) * 3, 0, 7); g.fill();
  }
}

export function dirt() {
  const c = canvas(512, 512), g = c.getContext('2d');
  g.fillStyle = '#c98d55'; g.fillRect(0, 0, 512, 512);
  speckle(g, 512, 512, 900, ['#b87a45', '#d9a067', '#a96d3d', '#e0ad75'], 1, 4, 2);
  g.strokeStyle = 'rgba(120,70,35,0.35)'; g.lineWidth = 2;
  for (let i = 0; i < 40; i++) {
    g.beginPath(); const x = hash(i * 9.1) * 512, y = hash(i * 4.3) * 512;
    g.moveTo(x, y); g.quadraticCurveTo(x + 20, y + 8, x + 40 + hash(i) * 30, y + hash(i * 2) * 20); g.stroke();
  }
  return tex(c, [40, 40]);
}

export function paddock() {           // dry grass between the wheat
  const c = canvas(512, 512), g = c.getContext('2d');
  g.fillStyle = '#c9a85a'; g.fillRect(0, 0, 512, 512);
  speckle(g, 512, 512, 1400, ['#b8964a', '#d8bb6c', '#a98a40', '#e2c77d', '#9c8a4a'], 1, 3, 5);
  g.strokeStyle = 'rgba(110,85,35,0.5)'; g.lineWidth = 2;
  for (let i = 0; i < 260; i++) {
    const x = hash(i * 2.3) * 512, y = hash(i * 5.9) * 512;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + (hash(i) - 0.5) * 8, y - 10 - hash(i * 3) * 10); g.stroke();
  }
  return tex(c, [60, 60]);
}

export function road() {
  const c = canvas(256, 1024), g = c.getContext('2d');
  g.fillStyle = '#b9764a'; g.fillRect(0, 0, 256, 1024);
  speckle(g, 256, 1024, 700, ['#a86a40', '#c98657', '#9a5f38'], 1, 4, 9);
  g.fillStyle = 'rgba(90,50,30,0.35)';
  for (const x of [70, 186]) for (let y = 0; y < 1024; y += 4) g.fillRect(x - 10 + Math.sin(y / 60) * 3, y, 20, 3);
  return tex(c, [1, 30]);
}

// wheat clump card: golden stalks with ears, alpha cut-out
export function wheatCard(seed = 1, ripe = 1) {
  const c = canvas(256, 256), g = c.getContext('2d');
  const cols = ['#e8b84a', '#d9a63a', '#f2c95e', '#c8952f'];
  for (let i = 0; i < 34; i++) {
    const x = 20 + hash(i * 3.7 + seed) * 216, top = 30 + hash(i * 1.9 + seed) * 70, lean = (hash(i * 5.3 + seed) - 0.5) * 30;
    g.strokeStyle = cols[i % 4]; g.lineWidth = 3;
    g.beginPath(); g.moveTo(x, 256); g.quadraticCurveTo(x + lean * 0.3, 160, x + lean, top); g.stroke();
    g.fillStyle = cols[(i + 1) % 4];
    g.beginPath(); g.ellipse(x + lean, top - 8, 5, 15, lean / 80, 0, 7); g.fill();
    g.strokeStyle = 'rgba(120,80,20,0.6)'; g.lineWidth = 1.5;
    g.beginPath(); g.ellipse(x + lean, top - 8, 5, 15, lean / 80, 0, 7); g.stroke();
  }
  return tex(c, [1, 1]);
}

export function corrugated(base = '#b9c2c6', seam = '#7d8b92', rows = 1) {
  const c = canvas(256, 256), g = c.getContext('2d');
  g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  for (let x = 0; x < 256; x += 16) {
    const gr = g.createLinearGradient(x, 0, x + 16, 0);
    gr.addColorStop(0, seam); gr.addColorStop(0.5, base); gr.addColorStop(1, seam);
    g.fillStyle = gr; g.globalAlpha = 0.55; g.fillRect(x, 0, 16, 256); g.globalAlpha = 1;
  }
  g.fillStyle = 'rgba(150,80,40,0.25)';
  speckle(g, 256, 256, 60, ['rgba(150,80,40,0.3)', 'rgba(120,70,40,0.25)'], 2, 7, 4);
  return tex(c, [1, rows]);
}

export function planks(base = '#9c6b43', seam = '#5e3b22', n = 6, horizontal = true) {
  const c = canvas(256, 256), g = c.getContext('2d');
  g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  const s = 256 / n;
  for (let i = 0; i < n; i++) {
    g.fillStyle = i % 2 ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';
    horizontal ? g.fillRect(0, i * s, 256, s) : g.fillRect(i * s, 0, s, 256);
    g.fillStyle = seam;
    horizontal ? g.fillRect(0, i * s, 256, 3) : g.fillRect(i * s, 0, 3, 256);
    g.strokeStyle = 'rgba(70,40,20,0.35)'; g.lineWidth = 1.5;
    for (let k = 0; k < 3; k++) {
      g.beginPath();
      if (horizontal) { const y = i * s + 8 + k * s / 3; g.moveTo(0, y); g.bezierCurveTo(80, y + 4, 160, y - 4, 256, y + 2); }
      else { const x = i * s + 8 + k * s / 3; g.moveTo(x, 0); g.bezierCurveTo(x + 4, 80, x - 4, 160, x + 2, 256); }
      g.stroke();
    }
  }
  return tex(c);
}

export function canvasPaint(base, seam, n = 900, seed = 3) {     // army canvas, khaki paint
  const c = canvas(256, 256), g = c.getContext('2d');
  g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  speckle(g, 256, 256, n, [seam, 'rgba(255,255,255,0.06)'], 1, 3, seed);
  return tex(c);
}

export function bark() {
  const c = canvas(256, 512), g = c.getContext('2d');
  g.fillStyle = '#e4ddd0'; g.fillRect(0, 0, 256, 512);
  for (let i = 0; i < 26; i++) {
    g.fillStyle = ['#cfc3ad', '#b9ab92', '#efe8dc', '#a89a82'][i % 4];
    const x = hash(i * 3.3) * 256, y = hash(i * 8.1) * 512;
    g.beginPath(); g.ellipse(x, y, 10 + hash(i) * 22, 30 + hash(i * 2) * 60, 0, 0, 7); g.fill();
  }
  return tex(c);
}

export function leaves() {
  const c = canvas(256, 256), g = c.getContext('2d');
  g.fillStyle = '#7c8f55'; g.fillRect(0, 0, 256, 256);
  speckle(g, 256, 256, 500, ['#6a7d47', '#93a566', '#5b6d3e', '#a3b273'], 3, 9, 11);
  return tex(c);
}

export function skyTex(top, mid, bottom) {
  const c = canvas(4, 512), g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, 512);
  gr.addColorStop(0, top); gr.addColorStop(0.55, mid); gr.addColorStop(1, bottom);
  g.fillStyle = gr; g.fillRect(0, 0, 4, 512);
  const t = tex(c); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; return t;
}

export function cloud(seed = 1) {
  const c = canvas(512, 256), g = c.getContext('2d');
  const blobs = [];
  for (let i = 0; i < 9; i++) blobs.push([80 + hash(i + seed) * 350, 150 - hash(i * 2 + seed) * 60, 40 + hash(i * 3 + seed) * 50]);
  g.fillStyle = '#c9d6e6';
  for (const [x, y, r] of blobs) { g.beginPath(); g.arc(x + 6, y + 10, r, 0, 7); g.fill(); }
  g.fillStyle = '#ffffff';
  for (const [x, y, r] of blobs) { g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); }
  return tex(c);
}

// wooden sign / crate stencil text
export function textBoard(lines, opt = {}) {
  const w = opt.w || 1024, h = opt.h || 512;
  const c = canvas(w, h), g = c.getContext('2d');
  g.fillStyle = opt.bg || '#a87445'; g.fillRect(0, 0, w, h);
  if (opt.planks !== false) {
    for (let i = 1; i < 4; i++) { g.fillStyle = 'rgba(60,30,15,0.5)'; g.fillRect(0, i * h / 4, w, 4); }
    speckle(g, w, h, 300, ['rgba(80,45,20,0.25)', 'rgba(255,230,190,0.12)'], 2, 6, 7);
  }
  if (opt.border) { g.strokeStyle = opt.border; g.lineWidth = 18; g.strokeRect(9, 9, w - 18, h - 18); }
  g.fillStyle = opt.ink || '#2b1a10'; g.textAlign = 'center'; g.textBaseline = 'middle';
  const size = opt.size || 120;
  lines.forEach((l, i) => {
    g.font = `${opt.weight || 'bold'} ${Array.isArray(size) ? size[i] : size}px ${opt.font || 'Anton, Impact, sans-serif'}`;
    g.fillText(l, w / 2, h * (i + 1) / (lines.length + 1));
  });
  return tex(c);
}

export function brass() {
  const c = canvas(64, 64), g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 64, 0);
  gr.addColorStop(0, '#9a6a1c'); gr.addColorStop(0.4, '#f1c45a'); gr.addColorStop(0.7, '#d29a34'); gr.addColorStop(1, '#8a5c18');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  return tex(c);
}
