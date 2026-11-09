// The world: an outback wheat farm (Western Australia, 1932), the open paddock for the chase, the army truck and
// Lewis guns, the camp map table, a Defence office desk and the growing mountain of shell casings.
// Built from primitives with painted canvas textures. Returns handles the story animates.
import * as P from './paint.js';
import { hash } from './motion.js';

// layout (metres, y up)
export const ZONE = {
  farm: [0, 0, 0],            // gate at the origin, wheat field to -z, farmhouse behind it
  guns: [67, 0, -20],         // gun line just past the field's east edge (guns face -x)
  chase: [300, 0, 300],       // open paddock, the truck drives along +x
  desk: [0, 0, 900],          // Defence office desk (an interior set far from everything)
  table: [64, 0, 6],          // the camp map table
};

export function buildWorld(E) {
  const { THREE, scene, add, tbox, group, toon, flat, makeCard } = E;
  const W = { E, ZONE };
  const T = {
    dirt: P.dirt(), paddock: P.paddock(), road: P.road(), iron: P.corrugated('#c4cccf', '#7f8d94', 2),
    ironRed: P.corrugated('#b5543c', '#7a3021', 2), boards: P.planks('#efe3c6', '#b8a684', 8, true),
    wood: P.planks('#9c6b43', '#5e3b22', 4, true), bark: P.bark(), leaves: P.leaves(), brass: P.brass(),
    khaki: P.canvasPaint('#7c7f4c', 'rgba(50,55,25,0.18)', 160, 2), canvasTent: P.canvasPaint('#b9a877', 'rgba(90,75,40,0.3)', 600, 5),
  };
  const M = {
    ground: toon('#ffffff', T.paddock), dirt: toon('#ffffff', T.dirt), road: toon('#ffffff', T.road),
    iron: toon('#ffffff', T.iron), ironRed: toon('#ffffff', T.ironRed), boards: toon('#ffffff', T.boards),
    wood: toon('#ffffff', T.wood), bark: toon('#ffffff', T.bark), leaves: toon('#ffffff', T.leaves),
    brass: toon('#ffffff', T.brass), khaki: toon('#ffffff', T.khaki), tent: toon('#ffffff', T.canvasTent),
    black: toon('#2b2422'), steel: toon('#55595c'), gunmetal: toon('#3e4245'), tyre: toon('#2a2523'), hub: toon('#7d7f5a'),
    glass: toon('#9fc3d6'), dark: toon('#3a2a22'), cream: toon('#f0e6cf'), red: toon('#b83b2e'), post: toon('#8a6a48'),
    hill: toon('#c7a564'), hill2: toon('#b59a6c'), hill3: toon('#a7969a'), shrub: toon('#8b9a72'), shrub2: toon('#a2a77d'),
    green: toon('#5f6e3c'), leather: toon('#3f6b4a'), paper: toon('#f5efe0'),
  };
  W.M = M; W.T = T;

  // ---------- ground ----------
  const gnd = add(new THREE.PlaneGeometry(6000, 6000), M.ground, [0, 0, 0], [-Math.PI / 2, 0, 0]);
  gnd.castShadow = false;
  // dirt road: from the gate toward +z, curving east to the chase paddock
  for (let i = 0; i < 26; i++) {
    const z = 4 + i * 12;
    add(new THREE.PlaneGeometry(7, 12.4), M.road, [Math.sin(i / 5) * 3, 0.02, z], [-Math.PI / 2, 0, 0]).castShadow = false;
  }
  // the chase track across the paddock (worn dirt)
  add(new THREE.PlaneGeometry(900, 10), M.dirt, [ZONE.chase[0] + 200, 0.015, ZONE.chase[2]], [-Math.PI / 2, 0, 0]).castShadow = false;

  // ---------- distant hills + scattered scrub ----------
  const hillM = [M.hill, M.hill2, M.hill3];
  for (let i = 0; i < 40; i++) {
    const a = i / 40 * Math.PI * 2 + hash(i) * 0.1, r = 700 + hash(i * 3) * 500;
    const s = 80 + hash(i * 7) * 160;
    add(new THREE.SphereGeometry(1, 24, 12), hillM[i % 3], [Math.cos(a) * r + 150, -s * 0.72, Math.sin(a) * r + 150], [0, 0, 0], [s * 1.8, s, s * 1.4]).castShadow = false;
  }
  const shrubG = new THREE.IcosahedronGeometry(1, 1);
  const scrub = (cx, cz, n, spread, avoid) => {
    for (let i = 0; i < n; i++) {
      const x = cx + (hash(i * 1.7 + cx) - 0.5) * spread, z = cz + (hash(i * 2.9 + cz) - 0.5) * spread;
      if (avoid && avoid(x, z)) continue;
      const s = 0.5 + hash(i * 5.1) * 0.9;
      add(shrubG, i % 2 ? M.shrub : M.shrub2, [x, s * 0.35, z], [0, hash(i) * 3, 0], [s * 1.3, s * 0.7, s * 1.2]);
    }
  };
  scrub(ZONE.chase[0] + 200, ZONE.chase[2], 520, 700, (x, z) => Math.abs(z - ZONE.chase[2]) < 12);

  // ---------- gum trees ----------
  const tree = (x, z, s = 1) => {
    const g = group([x, 0, z], [0, hash(x + z) * 6, 0]);
    add(new THREE.CylinderGeometry(0.28 * s, 0.5 * s, 7 * s, 8), M.bark, [0, 3.5 * s, 0], [0, 0, 0.06], [1, 1, 1], g);
    add(new THREE.CylinderGeometry(0.12 * s, 0.22 * s, 4 * s, 6), M.bark, [1.1 * s, 7.2 * s, 0], [0, 0, -0.6], [1, 1, 1], g);
    add(new THREE.CylinderGeometry(0.12 * s, 0.22 * s, 4 * s, 6), M.bark, [-1.0 * s, 7.4 * s, 0.4 * s], [0.2, 0, 0.55], [1, 1, 1], g);
    for (let k = 0; k < 6; k++) {
      const r = (1.9 + hash(k + x) * 1.2) * s;
      add(new THREE.IcosahedronGeometry(1, 1), M.leaves, [(hash(k * 3 + z) - 0.5) * 5 * s, (8.5 + hash(k * 5) * 2.5) * s, (hash(k * 7 + x) - 0.5) * 4 * s], [0, k, 0], [r * 1.3, r * 0.8, r * 1.2], g);
    }
    return g;
  };
  for (const [x, z, s] of [[-34, -72, 1.3], [26, -80, 1.1], [-62, -30, 1.2], [58, -66, 1.0], [-18, 26, 0.9], [22, 34, 1.05],
    [ZONE.chase[0] + 80, ZONE.chase[2] - 60, 1.2], [ZONE.chase[0] + 260, ZONE.chase[2] - 90, 1.1], [ZONE.chase[0] + 160, ZONE.chase[2] + 70, 1.0],
    [ZONE.chase[0] + 420, ZONE.chase[2] - 40, 1.3], [ZONE.chase[0] - 30, ZONE.chase[2] + 50, 1.0], [80, 30, 1.1], [90, -40, 1.2]]) tree(x, z, s);

  // ---------- clouds ----------
  W.clouds = [];
  for (let i = 0; i < 14; i++) {
    const a = i / 14 * Math.PI * 2, r = 1400;
    const m = new THREE.MeshBasicMaterial({ map: P.cloud(i + 1), transparent: true, depthWrite: false, fog: false });
    const c = add(new THREE.PlaneGeometry(420, 210), m, [Math.cos(a) * r + 150, 260 + hash(i) * 200, Math.sin(a) * r + 150], [0, 0, 0], [1, 1, 1], scene, 'hide');
    c.castShadow = false; W.clouds.push(c);
  }

  // ---------- the farm ----------
  const farm = group(ZONE.farm);
  // fence along z = 0 with a gate at x = 0
  const postG = new THREE.BoxGeometry(0.16, 1.4, 0.16), wireG = new THREE.BoxGeometry(3.0, 0.035, 0.035);
  for (let x = -60; x <= 60; x += 3) {
    if (Math.abs(x) < 2) continue;
    add(postG, M.post, [x, 0.7, 0], [0, 0, (hash(x) - 0.5) * 0.08], [1, 1, 1], farm);
    if (x < 60 && Math.abs(x + 1.5) > 2.2) for (const y of [0.45, 0.85, 1.25]) add(wireG, M.steel, [x + 1.5, y, 0], [0, 0, 0], [1, 1, 1], farm);
  }
  // gate posts, timber gate (open) and the sign
  for (const x of [-2.2, 2.2]) tbox(0.3, 2.6, 0.3, M.wood, [x, 1.3, 0], [0, 0, 0], farm);
  const gate = group([2.2, 0, 0], [0, -1.2, 0], farm);
  for (const y of [0.4, 0.8, 1.2]) tbox(4.0, 0.14, 0.08, M.wood, [-2.0, y, 0], [0, 0, 0], gate);
  tbox(0.14, 1.2, 0.08, M.wood, [-3.9, 0.8, 0], [0, 0, 0], gate);
  tbox(4.4, 0.18, 0.18, M.wood, [0, 2.6, 0], [0, 0, 0], farm);       // cross-bar
  const signTex = P.textBoard(['WESTERN', 'AUSTRALIA', '1932'], { w: 768, h: 768, size: [118, 118, 200], bg: '#b47c49', ink: '#3a1f12', border: '#5e3b22' });
  W.sign = add(new THREE.BoxGeometry(1.9, 1.9, 0.08), [M.wood, M.wood, M.wood, M.wood, toon('#ffffff', signTex), M.wood], [0, 1.45, 0.12], [0, 0, 0], [1, 1, 1], farm);
  for (const x of [-0.8, 0.8]) add(new THREE.CylinderGeometry(0.02, 0.02, 0.75, 4), M.steel, [x, 2.45, 0.12], [0, 0, 0], [1, 1, 1], farm);

  // wheat field: crossed card clumps (alpha-tested, never inked)
  const wheatMat = new THREE.MeshToonMaterial({ map: P.wheatCard(1), alphaTest: 0.5, side: THREE.DoubleSide, gradientMap: null });
  wheatMat.map.wrapS = wheatMat.map.wrapT = THREE.ClampToEdgeWrapping;
  const clump = (() => {
    const gs = [];
    for (let k = 0; k < 3; k++) { const g = new THREE.PlaneGeometry(1.6, 1.15); g.translate(0, 0.55, 0); g.rotateY(k * Math.PI / 3); gs.push(g); }
    const pos = [], uv = [], idx = []; let off = 0;
    for (const g of gs) {
      pos.push(...g.attributes.position.array); uv.push(...g.attributes.uv.array);
      idx.push(...Array.from(g.index.array, v => v + off)); off += g.attributes.position.count;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    geo.setIndex(idx); geo.computeVertexNormals(); return geo;
  })();
  const field = { x0: -58, x1: 58, z0: -58, z1: -3 };
  W.field = field;
  const spots = [];
  for (let x = field.x0; x < field.x1; x += 1.25) for (let z = field.z0; z < field.z1; z += 1.25) {
    const jx = x + (hash(x * 3.1 + z) - 0.5) * 1.0, jz = z + (hash(z * 2.7 + x) - 0.5) * 1.0;
    spots.push([jx, jz]);
  }
  // trampled patches where the emus have been
  W.patches = [];
  for (let i = 0; i < 26; i++) W.patches.push([field.x0 + 6 + hash(i * 4.4) * (field.x1 - field.x0 - 12), field.z0 + 4 + hash(i * 6.6) * (field.z1 - field.z0 - 8), 2.2 + hash(i) * 2.8]);
  const wheat = new THREE.InstancedMesh(clump, wheatMat, spots.length);
  const m4 = new THREE.Matrix4(), q4 = new THREE.Quaternion(), e4 = new THREE.Euler();
  spots.forEach(([x, z], i) => {
    let flatten = 1;
    for (const [px, pz, pr] of W.patches) { const d = Math.hypot(x - px, z - pz); if (d < pr) flatten = Math.min(flatten, 0.2 + 0.8 * (d / pr) ** 2); }
    const s = 0.85 + hash(i * 1.3) * 0.35;
    e4.set((flatten < 0.6 ? (hash(i) - 0.5) * 1.2 : 0), hash(i * 2) * 3, (flatten < 0.6 ? (hash(i * 5) - 0.5) * 1.2 : 0));
    q4.setFromEuler(e4);
    m4.compose(new THREE.Vector3(x, 0, z), q4, new THREE.Vector3(s, s * flatten, s)); wheat.setMatrixAt(i, m4);
  });
  wheat.userData.kind = 'card'; wheat.castShadow = true; wheat.receiveShadow = false;
  scene.add(wheat);
  // golden ground under the wheat
  add(new THREE.PlaneGeometry(field.x1 - field.x0 + 2, field.z1 - field.z0 + 2), toon('#d9b15a'), [0, 0.01, (field.z0 + field.z1) / 2], [-Math.PI / 2, 0, 0]).castShadow = false;

  // farmhouse
  const house = group([-22, 0, -78], [0, 0.15, 0]);
  tbox(12, 3.6, 8, M.boards, [0, 1.8, 0], [0, 0, 0], house, 0.6);
  const roofG = new THREE.BoxGeometry(13.4, 0.16, 5.4);
  add(roofG, M.ironRed, [0, 4.75, -2.15], [0.55, 0, 0], [1, 1, 1], house);
  add(roofG, M.ironRed, [0, 4.75, 2.15], [-0.55, 0, 0], [1, 1, 1], house);
  add(new THREE.BoxGeometry(13.4, 0.12, 3.2), M.iron, [0, 3.2, 5.3], [-0.12, 0, 0], [1, 1, 1], house);        // veranda
  for (let x = -6; x <= 6; x += 3) tbox(0.16, 3.1, 0.16, M.wood, [x, 1.55, 6.7], [0, 0, 0], house);
  tbox(1.2, 2.2, 0.1, M.dark, [0, 1.1, 4.02], [0, 0, 0], house);
  for (const x of [-3.8, 3.8]) { tbox(1.6, 1.3, 0.1, M.glass, [x, 2.0, 4.02], [0, 0, 0], house); tbox(1.8, 0.14, 0.14, M.cream, [x, 1.3, 4.05], [0, 0, 0], house); }
  tbox(0.9, 2.4, 0.9, toon('#9a4e3a'), [3.5, 5.6, -1], [0, 0, 0], house);
  // water tank
  const tank = group([-33, 0, -70]);
  for (const [x, z] of [[-1.2, -1.2], [1.2, -1.2], [-1.2, 1.2], [1.2, 1.2]]) tbox(0.18, 3, 0.18, M.wood, [x, 1.5, z], [0, 0, 0], tank);
  add(new THREE.CylinderGeometry(2.0, 2.0, 3.0, 24, 1), M.iron, [0, 4.5, 0], [0, 0, 0], [1, 1, 1], tank);
  add(new THREE.ConeGeometry(2.15, 0.8, 24), M.iron, [0, 6.4, 0], [0, 0, 0], [1, 1, 1], tank);
  // windmill: lattice tower, fan, tail vane
  const mill = group([-8, 0, -84]);
  const H = 11;
  for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
    const leg = add(new THREE.BoxGeometry(0.14, H, 0.14), M.steel, [x * 0.65, H / 2, z * 0.65], [z * 0.09, 0, -x * 0.09], [1, 1, 1], mill);
  }
  for (let y = 1.5; y < H; y += 2.2) {
    const w = 1.3 * (1 - y / H * 0.85) + 0.25;
    for (const r of [0, Math.PI / 2]) {
      const b = group([0, y, 0], [0, r, 0], mill);
      tbox(w * 1.05, 0.08, 0.08, M.steel, [0, 0, w / 2], [0, 0, 0], b); tbox(w * 1.05, 0.08, 0.08, M.steel, [0, 0, -w / 2], [0, 0, 0], b);
    }
  }
  W.millHead = group([0, H + 0.3, 0], [0, 0.6, 0], mill);
  tbox(0.5, 0.5, 1.2, M.gunmetal, [0, 0, 0], [0, 0, 0], W.millHead);
  W.millFan = group([0, 0, 0.8], [0, 0, 0], W.millHead);
  for (let k = 0; k < 18; k++) {
    const b = group([0, 0, 0], [0, 0, k / 18 * Math.PI * 2], W.millFan);
    tbox(0.34, 2.1, 0.04, M.iron, [0, 1.45, 0], [0, 0.35, 0], b);
  }
  add(new THREE.TorusGeometry(2.3, 0.05, 6, 36), M.steel, [0, 0, 0], [0, 0, 0], [1, 1, 1], W.millFan);
  tbox(0.06, 1.6, 2.4, M.ironRed, [0, 0.3, -2.0], [0, 0, 0], W.millHead);

  // ---------- army camp: tent + map table ----------
  const camp = group(ZONE.table);
  const tent = group([6, 0, -4], [0, -0.4, 0], camp);
  add(new THREE.BoxGeometry(5.2, 0.06, 4.2), M.tent, [0, 1.35, -1.05], [0.68, 0, 0], [1, 1, 1], tent);
  add(new THREE.BoxGeometry(5.2, 0.06, 4.2), M.tent, [0, 1.35, 1.05], [-0.68, 0, 0], [1, 1, 1], tent);
  for (const x of [-2.6, 2.6]) add(new THREE.CylinderGeometry(0.05, 0.05, 2.9, 6), M.wood, [x, 1.45, 0], [0, 0, 0], [1, 1, 1], tent);
  W.table = group([0, 0, 0], [0, 0, 0], camp);
  tbox(1.6, 0.08, 2.4, M.wood, [0, 0.92, 0], [0, 0, 0], W.table);
  for (const [x, z] of [[-0.7, -1.05], [0.7, -1.05], [-0.7, 1.05], [0.7, 1.05]]) tbox(0.08, 0.9, 0.08, M.wood, [x, 0.45, z], [0, 0, 0], W.table);
  W.mapCanvas = P.canvas(1024, 1536);
  W.mapTex = P.tex(W.mapCanvas); W.mapTex.wrapS = W.mapTex.wrapT = THREE.ClampToEdgeWrapping;
  add(new THREE.PlaneGeometry(1.4, 2.1), toon('#ffffff', W.mapTex), [0, 0.965, 0], [-Math.PI / 2, 0, 0], [1, 1, 1], W.table).castShadow = false;
  W.mapStick = group([0, 1.2, 0], [0, 0, 0], W.table);
  add(new THREE.CylinderGeometry(0.012, 0.016, 1.1, 6), toon('#5b3920'), [0, 0, 0.55], [Math.PI / 2, 0, 0], [1, 1, 1], W.mapStick);
  add(new THREE.SphereGeometry(0.025, 8, 6), toon('#d7b452'), [0, 0, 0], [0, 0, 0], [1, 1, 1], W.mapStick);
  for (let k = 0; k < 3; k++) add(new THREE.CylinderGeometry(0.035, 0.035, 0.1, 10), M.brass, [0.55, 1.01, -0.9 + k * 0.08], [0, 0, 0], [1, 1, 1], W.table);   // a few rounds on the table
  tbox(0.3, 0.12, 0.2, M.khaki, [-0.5, 1.02, 1.0], [0, 0.3, 0], W.table);                                                        // binocular case

  // ---------- Lewis gun ----------
  W.lewis = (parent, pos, rot = [0, 0, 0]) => {
    const g = group(pos, rot, parent);
    add(new THREE.CylinderGeometry(0.085, 0.085, 0.95, 14), M.gunmetal, [0, 0, 0.35], [Math.PI / 2, 0, 0], [1, 1, 1], g);     // cooling shroud
    for (let k = 0; k < 4; k++) add(new THREE.TorusGeometry(0.087, 0.012, 4, 14), M.steel, [0, 0, 0.0 + k * 0.22], [0, 0, 0], [1, 1, 1], g);
    add(new THREE.CylinderGeometry(0.03, 0.03, 0.35, 8), M.black, [0, 0, 0.98], [Math.PI / 2, 0, 0], [1, 1, 1], g);            // muzzle
    add(new THREE.CylinderGeometry(0.2, 0.2, 0.07, 22), M.gunmetal, [0, 0.13, -0.05], [0, 0, 0], [1, 1, 1], g);                 // pan magazine
    add(new THREE.CylinderGeometry(0.05, 0.05, 0.08, 10), M.steel, [0, 0.18, -0.05], [0, 0, 0], [1, 1, 1], g);
    tbox(0.1, 0.12, 0.6, M.steel, [0, -0.02, -0.38], [0, 0, 0], g);                                                             // receiver
    tbox(0.08, 0.22, 0.42, M.wood, [0, -0.08, -0.82], [0.12, 0, 0], g);                                                         // stock
    tbox(0.05, 0.16, 0.06, M.wood, [0, -0.16, -0.52], [0.3, 0, 0], g);                                                          // grip
    g.userData.muzzle = [0, 0, 1.2];
    return g;
  };

  // ---------- the army truck ----------
  const truck = group([0, 0, 0]);
  W.truck = truck;
  W.truckBody = group([0, 0, 0], [0, 0, 0], truck);           // bounces on the springs
  const tb = W.truckBody;
  tbox(1.9, 0.25, 6.0, M.dark, [0, 0.75, 0], [0, 0, 0], tb);                     // chassis
  tbox(1.7, 1.0, 1.7, M.khaki, [0, 1.35, 2.15], [0, 0, 0], tb);                   // bonnet
  tbox(1.75, 0.95, 0.12, M.dark, [0, 1.3, 3.02], [0, 0, 0], tb);                  // grille
  for (let k = 0; k < 7; k++) tbox(0.06, 0.8, 0.04, M.steel, [-0.6 + k * 0.2, 1.3, 3.09], [0, 0, 0], tb);
  for (const x of [-0.7, 0.7]) add(new THREE.CylinderGeometry(0.16, 0.16, 0.14, 14), M.cream, [x, 1.75, 2.98], [Math.PI / 2, 0, 0], [1, 1, 1], tb);  // headlights
  tbox(1.95, 1.55, 1.5, M.khaki, [0, 1.75, 0.65], [0, 0, 0], tb);                 // cab
  tbox(1.6, 0.6, 0.06, M.glass, [0, 2.1, 1.42], [0, 0, 0], tb);                   // windscreen
  for (const x of [-0.99, 0.99]) tbox(0.06, 0.55, 0.9, M.glass, [x, 2.05, 0.7], [0, 0, 0], tb);
  tbox(2.05, 0.1, 1.6, M.khaki, [0, 2.55, 0.65], [0, 0, 0], tb);                  // cab roof
  // flatbed with plank sides
  tbox(2.1, 0.14, 3.2, M.wood, [0, 1.0, -1.55], [0, 0, 0], tb);
  for (const x of [-1.03, 1.03]) tbox(0.08, 0.5, 3.2, M.wood, [x, 1.3, -1.55], [0, 0, 0], tb);
  tbox(2.1, 0.5, 0.08, M.wood, [0, 1.3, -3.13], [0, 0, 0], tb);
  // mudguards and spare
  for (const [x, z] of [[-0.95, 2.1], [0.95, 2.1], [-1.0, -2.1], [1.0, -2.1]]) {
    add(new THREE.CylinderGeometry(0.62, 0.62, 0.42, 16, 1, true, 0, Math.PI), M.khaki, [x, 0.6, z], [0, 0, Math.PI / 2], [1, 1, 1], tb);
  }
  // gun post on the back
  tbox(0.12, 0.8, 0.12, M.steel, [0, 1.5, -2.3], [0, 0, 0], tb);
  W.truckGun = W.lewis(tb, [0, 1.95, -2.3], [0, Math.PI / 2, 0]);
  // two more guns + the ammo tower (only for the arrival shot)
  W.truckCargo = group([0, 0, 0], [0, 0, 0], tb);
  W.lewis(W.truckCargo, [-0.5, 1.25, -1.3], [0, 0.1, 0]);
  W.lewis(W.truckCargo, [0.5, 1.25, -1.6], [0, -0.1, 0]);
  const crateTex = P.textBoard(['.303 AMMO', '1000 ROUNDS'], { w: 512, h: 384, size: [92, 60], bg: '#7b7a45', ink: '#f2e8c8', border: '#4c4a28', planks: true });
  const crateM = toon('#ffffff', crateTex), crateSide = toon('#6e6c3c');
  W.crates = [];
  for (let k = 0; k < 10; k++) {
    const c = group([0, 1.33 + k * 0.46, -2.4], [0, (hash(k) - 0.5) * 0.25, 0], W.truckCargo);
    add(new THREE.BoxGeometry(0.9, 0.44, 0.6), [crateSide, crateSide, crateSide, crateSide, crateM, crateM], [0, 0, 0], [0, 0, 0], [1, 1, 1], c);
    W.crates.push(c);
  }
  // wheels
  W.wheels = [];
  for (const [x, z] of [[-0.95, 2.1], [0.95, 2.1], [-1.0, -2.1], [1.0, -2.1]]) {
    const w = group([x, 0.5, z], [0, 0, 0], truck);
    add(new THREE.CylinderGeometry(0.5, 0.5, 0.3, 18), M.tyre, [0, 0, 0], [0, 0, Math.PI / 2], [1, 1, 1], w);
    add(new THREE.CylinderGeometry(0.26, 0.26, 0.32, 12), M.hub, [0, 0, 0], [0, 0, Math.PI / 2], [1, 1, 1], w);
    for (let k = 0; k < 5; k++) tbox(0.34, 0.06, 0.06, M.steel, [x > 0 ? 0.17 : -0.17, 0, 0], [k * 1.2566, 0, 0], w);
    W.wheels.push(w);
  }

  // ---------- gun line on the field's east edge ----------
  W.gunLine = group(ZONE.guns, [0, -Math.PI / 2, 0]);
  W.lineGuns = [];
  for (const x of [-2.2, 2.2]) {
    const tri = group([x, 0, 0], [0, 0, 0], W.gunLine);
    for (const a of [0, 2.1, 4.2]) add(new THREE.CylinderGeometry(0.03, 0.03, 1.1, 6), M.steel, [Math.sin(a) * 0.25, 0.45, Math.cos(a) * 0.25 - 0.1], [Math.cos(a) * 0.45, 0, -Math.sin(a) * 0.45], [1, 1, 1], tri);
    W.lineGuns.push(W.lewis(tri, [0, 0.95, 0.1], [0, 0, 0]));
  }
  // sandbags
  for (let k = 0; k < 9; k++) add(new THREE.CapsuleGeometry(0.22, 0.5, 4, 8), M.tent, [-3.2 + k * 0.8, 0.22, 1.2], [0, 0, Math.PI / 2], [1, 0.7, 1], W.gunLine);
  // the casings mountain: a brass cone plus loose casings on its surface; grows during the montage
  W.pile = group([ZONE.guns[0] + 6.5, 0, ZONE.guns[2] + 1.5]);
  W.pileCone = add(new THREE.ConeGeometry(1, 1, 28, 1, true), M.brass, [0, 0.5, 0], [0, 0, 0], [1, 1, 1], W.pile);
  const casingG = new THREE.CylinderGeometry(0.03, 0.03, 0.12, 6);
  W.casings = new THREE.InstancedMesh(casingG, M.brass, 900);
  for (let i = 0; i < 900; i++) {
    const a = hash(i * 1.37) * Math.PI * 2, r = Math.sqrt(hash(i * 2.11));
    m4.compose(new THREE.Vector3(Math.cos(a) * r, 1 - r + 0.02, Math.sin(a) * r), q4.setFromEuler(e4.set(hash(i) * 3, hash(i * 3) * 3, hash(i * 5) * 3)), new THREE.Vector3(1, 1, 1));
    W.casings.setMatrixAt(i, m4);
  }
  W.casings.userData.kind = 'world'; W.casings.castShadow = true;
  W.pile.add(W.casings);

  // ---------- the Defence office desk ----------
  const office = group(ZONE.desk);
  tbox(14, 0.2, 14, toon('#7b5a3f'), [0, -0.1, 0], [0, 0, 0], office);                                     // floor
  tbox(14, 6, 0.3, toon('#d9cfae'), [0, 3, -3], [0, 0, 0], office);                                        // back wall
  tbox(14, 1.1, 0.34, toon('#5d4330'), [0, 0.55, -2.95], [0, 0, 0], office);                               // dado
  tbox(2.4, 1.8, 0.1, toon('#bfe0f2'), [2.6, 3.0, -2.82], [0, 0, 0], office);                              // window
  tbox(2.6, 0.12, 0.2, toon('#5d4330'), [2.6, 2.05, -2.78], [0, 0, 0], office);
  const plaqueTex = P.textBoard(['DEPARTMENT', 'OF DEFENCE'], { w: 1024, h: 512, size: 150, bg: '#2f4a38', ink: '#e9d9a0', border: '#c9a545', planks: false });
  add(new THREE.BoxGeometry(2.2, 1.1, 0.06), [M.wood, M.wood, M.wood, M.wood, toon('#ffffff', plaqueTex), M.wood], [-2.4, 3.2, -2.8], [0, 0, 0], [1, 1, 1], office);
  W.desk = group([0, 0, 0], [0, 0, 0], office);
  tbox(3.2, 0.12, 1.6, M.wood, [0, 0.86, 0], [0, 0, 0], W.desk);
  tbox(3.0, 0.02, 1.4, M.leather, [0, 0.93, 0], [0, 0, 0], W.desk);
  for (const x of [-1.2, 1.2]) tbox(0.7, 0.8, 1.5, M.wood, [x, 0.4, 0], [0, 0, 0], W.desk);
  add(new THREE.CylinderGeometry(0.07, 0.08, 0.1, 12), toon('#2a2a3a'), [1.1, 0.99, -0.4], [0, 0, 0], [1, 1, 1], W.desk);       // inkwell
  tbox(0.5, 0.04, 0.4, toon('#2a1f2a'), [-1.0, 0.95, 0.1], [0, 0.2, 0], W.desk);                                                   // ink pad
  // the farmer's letter on the desk and the NO stamp
  W.letter2Canvas = P.canvas(768, 1024); W.letter2Tex = P.tex(W.letter2Canvas);
  W.letter2Tex.wrapS = W.letter2Tex.wrapT = THREE.ClampToEdgeWrapping;
  W.letter2 = add(new THREE.PlaneGeometry(0.62, 0.83), toon('#ffffff', W.letter2Tex), [0, 0.945, 0.1], [-Math.PI / 2, 0, 0], [1, 1, 1], W.desk);
  W.letter2.castShadow = false;
  W.stamp = group([0, 1.4, 0], [0, 0, 0], W.desk);
  add(new THREE.CylinderGeometry(0.05, 0.07, 0.3, 12), toon('#5b3920'), [0, 0.3, 0], [0, 0, 0], [1, 1, 1], W.stamp);
  add(new THREE.SphereGeometry(0.09, 12, 8), toon('#5b3920'), [0, 0.48, 0], [0, 0, 0], [1, 1, 1], W.stamp);
  tbox(0.42, 0.08, 0.26, toon('#3a2a20'), [0, 0.12, 0], [0, 0, 0], W.stamp);
  tbox(0.4, 0.04, 0.24, toon('#a32626'), [0, 0.06, 0], [0, 0, 0], W.stamp);

  // ---------- held letter (farmer) and notepad (major): close-up props drawn as world planes ----------
  W.letterCanvas = P.canvas(768, 1024); W.letterTex = P.tex(W.letterCanvas);
  W.letterTex.wrapS = W.letterTex.wrapT = THREE.ClampToEdgeWrapping;
  W.letter = add(new THREE.PlaneGeometry(0.42, 0.56), toon('#ffffff', W.letterTex), [0, -50, 0], [0, 0, 0]);
  W.letter.castShadow = false;
  W.padCanvas = P.canvas(768, 1024); W.padTex = P.tex(W.padCanvas);
  W.padTex.wrapS = W.padTex.wrapT = THREE.ClampToEdgeWrapping;
  W.pad = add(new THREE.PlaneGeometry(0.3, 0.4), toon('#ffffff', W.padTex), [0, -50, 0], [0, 0, 0]);
  W.pad.castShadow = false;

  // ---------- cards ----------
  W.emus = [];
  for (let i = 0; i < 34; i++) W.emus.push(makeCard('emu' + i, 'emu', null, 1.9 + hash(i * 9.3) * 0.25));
  W.gunner = makeCard('gunner', 'human', 'soldier', 1.75);
  W.driver = makeCard('driver', 'human', 'soldier2', 1.7);
  W.soldier2 = makeCard('soldier2', 'human', 'soldier2', 1.72);
  W.major = makeCard('major', 'human', 'major', 1.8);
  W.farmer = makeCard('farmer', 'human', 'farmer', 1.78);
  W.hat = makeCard('hat', 'hat', null, 0.8);
  W.puffs = [];
  for (let i = 0; i < 10; i++) W.puffs.push(makeCard('puff' + i, 'puff', null, 1.6));
  W.cards = [...W.emus, W.gunner, W.driver, W.soldier2, W.major, W.farmer, W.hat, ...W.puffs];
  return W;
}
