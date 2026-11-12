// The blocky world for "Trapped in Minecraft", in the cartoon engine's style: toon-shaded, ink-outlined cubes with
// original pixel textures (16x16, nearest filtering). 1 block = 1 metre. Built once; story.js animates it.
import * as P from './paint.js';
import { hash } from './motion.js';

export const Z = {
  meadow: [0, 0, 0],          // wake-up spot; the tree is at x = 3
  tree: [3, 0, -2],
  mountain: [11, 0, -3],
  house: [-9, 0, -4],          // front wall at z = -4, door at x = -9
  room: [0, 0, 300],           // the bedroom interior (a separate set)
};

export function buildWorld(E) {
  const { THREE, scene, add, group, toon, makeCard } = E;
  const W = { E, Z };
  // ---------- pixel textures ----------
  const PAL = {
    grass: ['#5aae3e', '#4b9934', '#6cbf4a'], dirt: ['#8a5a36', '#76482a', '#9e6b42'], stone: ['#8f9298', '#7a7d84', '#a3a6ac'],
    log: ['#6e4a2a', '#57391f', '#83603c'], logTop: ['#b58a55', '#9a7244', '#c79c63'], leaves: ['#3f9e3a', '#2f8030', '#56b44c'],
    planks: ['#c48b4e', '#a87339', '#d69d5c'], cobble: ['#8a8d92', '#6c6f74', '#a6a9ae'], wool: ['#d23a3a', '#b42e2e', '#e35151'],
  };
  function pix(kind, seed = 0, fn = null) {
    const c = P.canvas(16, 16), g = c.getContext('2d'), p = PAL[kind];
    for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) {
      const h = hash(x * 13.1 + y * 7.7 + seed * 31 + kind.length * 3);
      let col = h < 0.22 ? p[1] : h > 0.85 ? p[2] : p[0];
      if (fn) col = fn(x, y, h, col) || col;
      g.fillStyle = col; g.fillRect(x, y, 1, 1);
    }
    const t = new THREE.CanvasTexture(c); t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestMipmapLinearFilter;
    t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
  }
  const dirtC = (x, y, h) => (h < 0.25 ? PAL.dirt[1] : h > 0.85 ? PAL.dirt[2] : PAL.dirt[0]);
  const T = {
    grassTop: pix('grass', 1), dirt: pix('dirt', 2),
    grassSide: pix('grass', 3, (x, y, h) => y > 3 + (hash(x * 5.1) > 0.55 ? 1 : 0) ? dirtC(x, y, h) : null),
    stone: pix('stone', 4), log: pix('log', 5, (x, y, h) => (x % 4 === 1 ? PAL.log[1] : null)), logTop: pix('logTop', 6, (x, y) => (Math.hypot(x - 7.5, y - 7.5) % 3 < 1 ? PAL.logTop[1] : null)),
    leaves: pix('leaves', 7), planks: pix('planks', 8, (x, y) => (y % 4 === 3 ? PAL.planks[1] : (y % 8 < 4 ? (x === 5 ? PAL.planks[1] : null) : (x === 12 ? PAL.planks[1] : null)))),
    cobble: pix('cobble', 9, (x, y, h) => ((x * 3 + y * 5) % 7 === 0 ? PAL.cobble[1] : null)), wool: pix('wool', 10),
  };
  const M = {
    grass: [toon('#fff', T.grassSide), toon('#fff', T.grassSide), toon('#fff', T.grassTop), toon('#fff', T.dirt), toon('#fff', T.grassSide), toon('#fff', T.grassSide)],
    dirt: toon('#fff', T.dirt), stone: toon('#fff', T.stone), leaves: toon('#fff', T.leaves), planks: toon('#fff', T.planks), cobble: toon('#fff', T.cobble),
    log: [toon('#fff', T.log), toon('#fff', T.log), toon('#fff', T.logTop), toon('#fff', T.logTop), toon('#fff', T.log), toon('#fff', T.log)],
    wool: toon('#fff', T.wool), white: toon('#f2efe6'), dark: toon('#1a1d2a'), iron: toon('#4a4f5c'), stick: toon('#8a5a36'),
  };
  W.M = M; W.T = T;
  const cube = new THREE.BoxGeometry(1, 1, 1);
  W.cube = cube;
  // instanced cube field helper
  function field(mat, cells, kind = 'world') {
    const im = new THREE.InstancedMesh(cube, mat, cells.length);
    const m4 = new THREE.Matrix4();
    cells.forEach(([x, y, z], i) => { m4.makeTranslation(x + 0.5, y + 0.5, z + 0.5); im.setMatrixAt(i, m4); });
    im.castShadow = true; im.receiveShadow = true; im.userData.kind = kind; scene.add(im); return im;
  }
  W.field = field;

  // ---------- terrain: grass blocks with a few raised steps; dirt under; far ground as a plane ----------
  const grassCells = [], dirtCells = [];
  const height = (x, z) => {
    if (x >= -16 && x <= 22 && z >= -10 && z <= 8) return 0;     // keep the whole play area flat
    const h = hash(Math.floor(x / 3) * 7.1 + Math.floor(z / 3) * 3.3);
    return h > 0.82 ? 1 : 0;
  };
  for (let x = -30; x < 34; x++) for (let z = -34; z < 14; z++) {
    const h = height(x, z);
    grassCells.push([x, h - 1, z]);
    if (h > 0) dirtCells.push([x, h - 2, z]);
  }
  field(M.grass, grassCells); field(M.dirt, dirtCells);
  const far = add(new THREE.PlaneGeometry(4000, 4000), toon('#fff', (() => { const t = T.grassTop.clone(); t.needsUpdate = true; t.repeat.set(4000, 4000); return t; })()), [0, -0.001, 0], [-Math.PI / 2, 0, 0]);
  far.castShadow = false;
  // distant blocky hills
  for (let i = 0; i < 24; i++) {
    const a = i / 24 * Math.PI * 2, r = 80 + hash(i) * 60, cx = Math.round(Math.cos(a) * r), cz = Math.round(Math.sin(a) * r) - 20;
    const cells = []; const hh = 4 + Math.floor(hash(i * 3) * 8);
    for (let k = 0; k < hh; k++) for (let dx = -hh + k; dx <= hh - k; dx++) for (let dz = -hh + k; dz <= hh - k; dz++) if (k === hh - 1 || Math.abs(dx) === hh - k || Math.abs(dz) === hh - k) cells.push([cx + dx, k, cz + dz]);
    field(M.grass, cells);
  }

  // ---------- the tree: 4 logs (separate meshes so they can pop) + a leaf crown that stays floating ----------
  const [tx, , tz] = Z.tree;
  W.logs = [];
  for (let i = 0; i < 4; i++) { const m = add(cube, M.log, [tx + 0.5, i + 0.5, tz + 0.5]); W.logs.push(m); }
  const leafCells = [];
  for (let y = 3; y < 6; y++) for (let dx = -2; dx <= 2; dx++) for (let dz = -2; dz <= 2; dz++) {
    if (y === 5 && (Math.abs(dx) > 1 || Math.abs(dz) > 1)) continue;
    if (y === 3 && dx === 0 && dz === 0) continue;
    if (Math.abs(dx) === 2 && Math.abs(dz) === 2) continue;
    leafCells.push([tx + dx, y + 1, tz + dz]);
  }
  W.leaves = field(M.leaves, leafCells);
  // more trees around (decor)
  for (const [x, z] of [[-18, -14], [22, -16], [-24, -2], [26, 6], [-4, -20], [16, -24]]) {
    for (let i = 0; i < 5; i++) add(cube, M.log, [x + 0.5, i + 0.5, z + 0.5]);
    const c = [];
    for (let y = 4; y < 7; y++) for (let dx = -2; dx <= 2; dx++) for (let dz = -2; dz <= 2; dz++) if (!(Math.abs(dx) === 2 && Math.abs(dz) === 2) && !(y === 6 && (Math.abs(dx) > 1 || Math.abs(dz) > 1))) c.push([x + dx, y, z + dz]);
    field(M.leaves, c);
  }

  // ---------- the mountain: stepped stone with a grassy top; mined blocks are a separate field we hide ----------
  const [mx, , mz] = Z.mountain;
  const mcells = [];
  for (let y = 0; y < 6; y++) for (let x = y; x < 12 - y; x++) for (let z = -4 + Math.floor(y / 2); z < 3 - Math.floor(y / 2); z++) mcells.push([mx + x, y, mz + z]);
  // blocks facing the hero (x = mx, low rows) are mineable singles
  W.mineable = [];
  const rest = [];
  for (const c of mcells) {
    const [x, y, z] = c;
    if (x <= mx + 1 && y <= 2 && Math.abs(z - Z.mountain[2]) <= 2) { const m = add(cube, y === 5 ? M.grass : M.stone, [x + 0.5, y + 0.5, z + 0.5]); W.mineable.push(m); }
    else rest.push(c);
  }
  W.mineable.sort((a, b) => (a.position.x - b.position.x) || (a.position.y - b.position.y));
  field(M.stone, rest.filter(c => c[1] < 5)); field(M.grass, rest.filter(c => c[1] === 5));

  // ---------- the house: front + side + back walls (5 x 4 x 4) + a roof row; each block is its own mesh ----------
  const [hx, , hz] = Z.house;
  W.houseBlocks = [];
  for (let y = 0; y < 4; y++) for (let x = -2; x <= 2; x++) for (let z = 0; z >= -3; z--) {
    const edge = Math.abs(x) === 2 || z === 0 || z === -3;
    if (!edge) continue;
    if (z === 0 && x === 0 && y < 2) continue;                 // the door opening
    const frame = Math.abs(x) === 2 || y === 3;
    W.houseBlocks.push({ m: add(cube, frame ? M.cobble : M.planks, [hx + x + 0.5, y + 0.5, hz + z + 0.5]), y, x, z });
  }
  for (let x = -3; x <= 3; x++) for (let z = 1; z >= -4; z--) W.houseBlocks.push({ m: add(cube, M.cobble, [hx + x + 0.5, 4.5, hz + z + 0.5]), y: 4, x, z });
  // build order: bottom row first, front to back, left to right
  W.houseBlocks.sort((a, b) => (a.y - b.y) || (b.z - a.z) || (a.x - b.x));
  W.houseBlocks.forEach(b => { b.home = b.m.position.clone(); });
  // the door (pivot at its hinge)
  W.doorPivot = group([hx + 0.0, 0, hz + 1.0]);
  W.door = add(new THREE.BoxGeometry(0.98, 1.96, 0.14), M.planks, [0.49, 0.98, -0.07], [0, 0, 0], [1, 1, 1], W.doorPivot);
  add(new THREE.SphereGeometry(0.06, 8, 6), toon('#e0b13a'), [0.82, 1.0, 0.04], [0, 0, 0], [1, 1, 1], W.doorPivot);

  // ---------- the bedroom interior (separate set): plank walls, cobble floor, bed, torch, one missing block -------
  const [rx, , rz] = Z.room;
  const room = [];
  W.gap = [rx + 2, 3, rz - 3];                                  // the one gap in the back wall
  for (let x = -4; x <= 4; x++) for (let y = 0; y < 6; y++) { if (x === W.gap[0] - rx && y === W.gap[1]) continue; room.push([rx + x, y, rz - 3]); }
  for (let z = -3; z <= 3; z++) for (let y = 0; y < 6; y++) { room.push([rx - 5, y, rz + z]); room.push([rx + 5, y, rz + z]); }
  field(M.planks, room);
  const floor = []; for (let x = -5; x <= 5; x++) for (let z = -3; z <= 4; z++) floor.push([rx + x, -1, rz + z]); field(M.cobble, floor);
  const ceil = []; for (let x = -5; x <= 5; x++) for (let z = -3; z <= 4; z++) ceil.push([rx + x, 6, rz + z]); field(M.planks, ceil);
  // bed: two blocks wide, along the back wall
  W.bed = group([rx - 2.6, 0, rz - 1.6]);
  add(new THREE.BoxGeometry(2.2, 0.45, 1.05), M.white, [0, 0.38, 0], [0, 0, 0], [1, 1, 1], W.bed);
  add(new THREE.BoxGeometry(1.5, 0.12, 1.07), M.wool, [0.35, 0.66, 0], [0, 0, 0], [1, 1, 1], W.bed);
  add(new THREE.BoxGeometry(0.5, 0.18, 0.8), toon('#ffffff'), [-0.78, 0.68, 0], [0, 0, 0], [1, 1, 1], W.bed);
  for (const dx of [-1.0, 1.0]) for (const dz of [-0.45, 0.45]) add(new THREE.BoxGeometry(0.12, 0.2, 0.12), M.stick, [dx, 0.1, dz], [0, 0, 0], [1, 1, 1], W.bed);
  // torch on the left wall + its light
  W.torch = group([rx - 4.5, 2.6, rz - 0.5]);
  add(new THREE.BoxGeometry(0.1, 0.55, 0.1), M.stick, [0, 0, 0], [0, 0, -0.35], [1, 1, 1], W.torch);
  W.flame = add(new THREE.ConeGeometry(0.1, 0.25, 8), new THREE.MeshBasicMaterial({ color: '#ffb02e' }), [0.1, 0.38, 0], [0, 0, 0], [1, 1, 1], W.torch, 'hide');
  W.torchLight = new THREE.PointLight('#ffb070', 0, 18, 1.6); W.torchLight.position.set(rx - 4.1, 3.1, rz - 0.4); W.torchLight.castShadow = false; scene.add(W.torchLight);
  W.blanket = add(new THREE.BoxGeometry(1.3, 0.16, 1.1), M.wool, [0, -50, 0]);
  W.sunDisc = add(new THREE.PlaneGeometry(40, 40), new THREE.MeshBasicMaterial({ fog: false, map: (() => { const c = P.canvas(16, 16), g = c.getContext('2d'); g.fillStyle = '#ffcf2e'; g.fillRect(0, 0, 16, 16); g.fillStyle = '#ffe766'; g.fillRect(2, 2, 12, 12); g.fillStyle = '#fff6b8'; g.fillRect(5, 5, 6, 6); const t = new THREE.CanvasTexture(c); t.magFilter = THREE.NearestFilter; t.colorSpace = THREE.SRGBColorSpace; return t; })() }), [0, -500, 0], [0, 0, 0], [1, 1, 1], scene, 'hide');
  // the dark night outside the gap
  add(new THREE.PlaneGeometry(30, 20), new THREE.MeshBasicMaterial({ color: '#05060d' }), [rx, 4, rz - 9], [0, 0, 0], [1, 1, 1], scene, 'hide');

  // ---------- props: the weight, mini blocks, the moon, the notice ----------
  W.weight = group([0, -50, 0]);
  add(new THREE.CylinderGeometry(1.15, 1.6, 2.2, 4, 1), M.iron, [0, 1.1, 0], [0, Math.PI / 4, 0], [1, 1, 1], W.weight);
  add(new THREE.TorusGeometry(0.45, 0.16, 8, 20), M.iron, [0, 2.45, 0], [0, 0, 0], [1, 1, 1], W.weight);
  const wt = P.canvas(512, 256); { const g = wt.getContext('2d'); g.fillStyle = '#4a4f5c'; g.fillRect(0, 0, 512, 256); g.fillStyle = '#ffffff'; g.font = '170px Anton'; g.textAlign = 'center'; g.textBaseline = 'middle'; W.weightCanvas = wt; }
  W.weightLabelTex = P.tex(wt); W.weightLabelTex.wrapS = W.weightLabelTex.wrapT = THREE.ClampToEdgeWrapping;
  W.weightLabel = add(new THREE.PlaneGeometry(1.5, 0.75), new THREE.MeshBasicMaterial({ map: W.weightLabelTex }), [0, 1.05, 1.07], [-0.17, 0, 0], [1, 1, 1], W.weight, 'hide');
  W.minis = [];
  for (let i = 0; i < 10; i++) { const m = add(new THREE.BoxGeometry(0.32, 0.32, 0.32), M.stone, [0, -50, 0]); m.castShadow = true; W.minis.push(m); }
  W.miniMats = { stone: M.stone, log: M.log, planks: M.planks };
  W.moon = add(new THREE.PlaneGeometry(14, 14), new THREE.MeshBasicMaterial({ color: '#eef0f6', fog: false }), [0, -500, 0], [0, 0, 0], [1, 1, 1], scene, 'hide');
  W.stars = [];
  for (let i = 0; i < 70; i++) { const s = add(new THREE.PlaneGeometry(1.4, 1.4), new THREE.MeshBasicMaterial({ color: '#ffffff', fog: false, transparent: true }), [0, -500, 0], [0, 0, 0], [1, 1, 1], scene, 'hide'); W.stars.push(s); }
  // the update notes he tears in half: two halves of one canvas
  W.noteCanvas = P.canvas(768, 512);
  W.noteTex = P.tex(W.noteCanvas); W.noteTex.wrapS = W.noteTex.wrapT = THREE.ClampToEdgeWrapping;
  const halfGeo = (u0, u1) => { const g = new THREE.PlaneGeometry(0.42, 0.56); const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setX(i, u0 + uv.getX(i) * (u1 - u0)); g.translate((u0 + u1 - 1) * 0.42, 0, 0); return g; };
  const noteMat = new THREE.MeshBasicMaterial({ map: W.noteTex, color: '#d8d4cc', side: THREE.DoubleSide });
  W.noteL = add(halfGeo(0, 0.5), noteMat, [0, -50, 0]); W.noteR = add(halfGeo(0.5, 1), noteMat, [0, -50, 0]);
  W.noteL.castShadow = W.noteR.castShadow = false;
  W.drawNote = () => {
    const g = W.noteCanvas.getContext('2d');
    g.fillStyle = '#f6f1e3'; g.fillRect(0, 0, 768, 512); g.strokeStyle = '#2b2233'; g.lineWidth = 10; g.strokeRect(5, 5, 758, 502);
    g.fillStyle = '#2b2233'; g.font = '84px Anton'; g.textAlign = 'center'; g.fillText('UPDATE NOTES', 384, 110);
    g.textAlign = 'left'; g.font = '56px "Courier Prime"'; g.fillStyle = '#4a4458'; g.fillText('- fixed some bugs', 60, 220); g.fillText('- added more blocks', 60, 300);
    g.fillStyle = '#c0392b'; g.fillText('- removed Herobrine', 60, 390);
    W.noteTex.needsUpdate = true;
    const w = W.weightCanvas.getContext('2d'); w.fillStyle = '#4a4f5c'; w.fillRect(0, 0, 512, 256); w.fillStyle = '#ffffff'; w.font = '170px Anton'; w.textAlign = 'center'; w.textBaseline = 'middle'; w.fillText('150 t', 256, 136);
    W.weightLabelTex.needsUpdate = true;
  };
  W.afterFonts = W.drawNote;

  // ---------- cards ----------
  W.hero = makeCard('hero', 'human', 'player', 1.8);
  W.hero2 = makeCard('hero2', 'human', 'player', 1.8);         // used for the in-bed pose
  W.hb = makeCard('herobrine', 'human', 'herobrine', 1.85);
  W.puffs = []; for (let i = 0; i < 6; i++) W.puffs.push(makeCard('puff' + i, 'puff', null, 1.4));
  W.cards = [W.hero, W.hero2, W.hb, ...W.puffs];
  return W;
}
