// Procedural low-poly building kit for the overview town.
// One fixed town layout; every building typology is drawn in four eras: ancient, early-modern, modern, future.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const nightGlow = { v: 0 };

export const ERAS = [
  { id: 'ancient', zh: '古代', en: 'Ancient' },
  { id: 'early', zh: '近代', en: 'Early modern' },
  { id: 'modern', zh: '现代', en: 'Modern' },
  { id: 'future', zh: '未来', en: 'Future' },
];

const PALETTE = {
  ancient: { sky: [0xf3eee3, 0xe4dccb], ground: 0xd6ccb1, road: 0xb7a07a, pave: 0xe4d9c1, plaza: 0xd2c3a3, wall: 0xc6aa80, plaster: 0xe2d5ba, wood: 0x5f3f2a, roof: 0x4a4f53, stone: 0xb8a98d, leaf: 0x7d9168, trunk: 0x6a4f38, water: 0x8eaaa2, board: 0x5f3f2a, glow: 0xffc979 },
  early: { sky: [0xeeece6, 0xdcd8cf], ground: 0xcfd0c2, road: 0x8b8882, pave: 0xdcd6c8, plaza: 0xc4beb1, wall: 0xa9553e, plaster: 0xdcd2c0, wood: 0x4a3a30, roof: 0x5b4a43, stone: 0xd6ccbb, leaf: 0x6e8a5b, trunk: 0x5d4636, water: 0x88a7ae, board: 0x3d3f42, glow: 0xffd28a },
  modern: { sky: [0xeef0f1, 0xd9dde0], ground: 0xd3d8cc, road: 0x55585c, pave: 0xdcdcd6, plaza: 0xcfcfc9, wall: 0xdad8d2, plaster: 0xeceae5, wood: 0x8d7a64, roof: 0xc9c7c1, stone: 0xbfbdb6, leaf: 0x7b9a63, trunk: 0x6b5a48, water: 0x7ea4b6, board: 0x2c2e31, glow: 0xffffff },
  future: { sky: [0xe9eef3, 0xcfd9e3], ground: 0xdfe5ea, road: 0xbcc8d2, pave: 0xf0f3f6, plaza: 0xd6dee5, wall: 0xf4f6f8, plaster: 0xf7f8fa, wood: 0xb9c4cd, roof: 0xf1f4f6, stone: 0xd3dbe2, leaf: 0x93d2c6, trunk: 0xb9c4cd, water: 0x9cd6e6, board: 0xe9eef2, glow: 0x52d0ff },
};
export const palette = era => PALETTE[era];

// ---------- primitives ----------
function kit(era) {
  const p = PALETTE[era], cache = new Map(), anims = [], emitters = [];
  const mat = (color, o = {}) => {
    const key = color + JSON.stringify(o);
    if (!cache.has(key)) cache.set(key, new THREE.MeshStandardMaterial({ color, roughness: 0.85, metalness: 0, flatShading: true, ...o }));
    return cache.get(key);
  };
  const glass = () => mat(era === 'future' ? 0xb9d7e6 : 0x86a0ae, { roughness: 0.12, metalness: 0.35, transparent: era === 'future', opacity: era === 'future' ? 0.55 : 1 });
  const glow = (c = p.glow, i = 1.6) => mat(c, { emissive: c, emissiveIntensity: i, roughness: 0.4 });
  const add = (g, geo, m, x = 0, y = 0, z = 0, ry = 0) => { const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); o.rotation.y = ry; o.castShadow = o.receiveShadow = true; g.add(o); return o; };
  const box = (g, w, h, d, m, x = 0, y = 0, z = 0, ry = 0) => add(g, new THREE.BoxGeometry(w, h, d), m, x, y + h / 2, z, ry);
  const cyl = (g, rt, rb, h, m, x = 0, y = 0, z = 0, seg = 14) => add(g, new THREE.CylinderGeometry(rt, rb, h, seg), m, x, y + h / 2, z);
  const sphere = (g, r, m, x, y, z, seg = 10) => add(g, new THREE.IcosahedronGeometry(r, 1), m, x, y, z);
  const dome = (g, r, m, x = 0, y = 0, z = 0) => add(g, new THREE.SphereGeometry(r, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), m, x, y, z);
  const pyramid = (g, w, h, m, x = 0, y = 0, z = 0) => { const o = add(g, new THREE.ConeGeometry(w * 0.7071, h, 4), m, x, y + h / 2, z); o.rotation.y = Math.PI / 4; return o; };
  // hip roof (庑殿) with optional corner lift
  const hip = (g, w, d, h, over, m, x = 0, y = 0, z = 0, lift = 0) => {
    const W = w / 2 + over, D = d / 2 + over, r = Math.max(0, W - D);
    const v = [[-W, lift, -D], [W, lift, -D], [W, lift, D], [-W, lift, D], [-r, h, 0], [r, h, 0]];
    const f = [[3, 2, 5], [3, 5, 4], [1, 0, 4], [1, 4, 5], [0, 3, 4], [2, 1, 5]];
    const pos = []; f.forEach(t => t.forEach(i => pos.push(...v[i])));
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.computeVertexNormals();
    const o = add(g, geo, ds(m), x, y, z); return o;
  };
  // curved hip roof for the ancient era: gently concave slopes, a modest lift only at the four corners,
  // and a real thickness (tile surface on top, dark soffit below, a fascia band all round), plus ridge and chiwen.
  const curvedHip = (g, w, d, h, over, m, x = 0, y = 0, z = 0, lift = 0) => {
    const W = w / 2 + over, D = d / 2 + over, r = Math.max(0, W - D), T = Math.min(0.22, 0.08 + D * 0.03);
    const up = 0.18 + lift * 1.1; // corner lift
    const f = (px, pz) => {
      const dx = Math.max(0, W - Math.abs(px)), dz = Math.max(0, D - Math.abs(pz)), n = Math.min(1, Math.min(dx, dz) / D);
      const c = Math.pow(Math.abs(px) / W, 3) * Math.pow(Math.abs(pz) / D, 3); // 1 only at the corners
      return h * Math.pow(n, 1.3) + up * c * Math.pow(1 - n, 1.5);
    };
    const nx = Math.max(10, Math.round(W * 2.4)), nz = Math.max(8, Math.round(D * 2.4));
    const top = new THREE.PlaneGeometry(W * 2, D * 2, nx, nz); top.rotateX(-Math.PI / 2);
    const ta = top.attributes.position.array; for (let i = 0; i < ta.length; i += 3) ta[i + 1] = f(ta[i], ta[i + 2]);
    top.computeVertexNormals();
    add(g, top, m, x, y, z);
    // soffit (underside) follows the top surface, a little lower and drawn facing down
    const bot = new THREE.PlaneGeometry(W * 2, D * 2, nx, nz); bot.rotateX(Math.PI / 2);
    const ba = bot.attributes.position.array; for (let i = 0; i < ba.length; i += 3) ba[i + 1] = f(ba[i], ba[i + 2]) - T;
    bot.computeVertexNormals();
    add(g, bot, mat(0x3b2a20), x, y, z);
    // fascia band: quads round the perimeter between the two surfaces
    const ring = [];
    for (let i = 0; i <= nx; i++) ring.push([-W + 2 * W * i / nx, D]);
    for (let j = 1; j <= nz; j++) ring.push([W, D - 2 * D * j / nz]);
    for (let i = 1; i <= nx; i++) ring.push([W - 2 * W * i / nx, -D]);
    for (let j = 1; j < nz; j++) ring.push([-W, -D + 2 * D * j / nz]);
    const pos = [];
    for (let i = 0; i < ring.length; i++) {
      const [ax, az] = ring[i], [bx, bz] = ring[(i + 1) % ring.length], ha = f(ax, az), hb = f(bx, bz);
      pos.push(ax, ha, az, bx, hb, bz, bx, hb - T, bz, ax, ha, az, bx, hb - T, bz, ax, ha - T, az);
    }
    const fas = new THREE.BufferGeometry(); fas.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); fas.computeVertexNormals();
    add(g, fas, ds(mat(0x6b4a32)), x, y, z);
    // ridge cap and chiwen
    const dark = mat(0x34383b);
    box(g, r * 2 + 0.4, 0.24, 0.3, dark, x, y + h - 0.04, z);
    if (r > 0.3) for (const sx of [-1, 1]) { const c = box(g, 0.2, 0.5, 0.28, dark, x + sx * (r + 0.15), y + h + 0.08, z); c.rotation.z = -sx * 0.25; }
    // hip ridges: a dark bead that follows the curved surface down each diagonal crease (|x| = r + |z|)
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
      const N = 7, pts = [];
      for (let i = 0; i <= N; i++) { const u = i / N * 0.97, px = sx * (r + D * u), pz = sz * D * u; pts.push(new THREE.Vector3(px, f(px, pz) + 0.05, pz)); }
      for (let i = 0; i < N; i++) {
        const a = pts[i], b = pts[i + 1], len = a.distanceTo(b), mid = a.clone().add(b).multiplyScalar(0.5);
        const bead = add(g, new THREE.BoxGeometry(0.15, 0.12, len + 0.06), dark, x + mid.x, y + mid.y, z + mid.z);
        // orient in the roof's own (local) space; lookAt would need world coordinates
        bead.quaternion.setFromRotationMatrix(new THREE.Matrix4().lookAt(a, b, new THREE.Vector3(0, 1, 0))); // keeps the bead upright, no roll
      }
    }
    return top;
  };
  // gable roof along x
  const gable = (g, w, d, h, over, m, x = 0, y = 0, z = 0, ry = 0) => {
    const sh = new THREE.Shape(); sh.moveTo(-d / 2 - over, 0); sh.lineTo(0, h); sh.lineTo(d / 2 + over, 0); sh.lineTo(-d / 2 - over, 0);
    const geo = new THREE.ExtrudeGeometry(sh, { depth: w + over * 2, bevelEnabled: false }); geo.translate(0, 0, -(w + over * 2) / 2); geo.rotateY(Math.PI / 2);
    return add(g, geo, m, x, y, z, ry);
  };
  function ds(m) { if (!m.userData.ds) { m.userData.ds = m.clone(); m.userData.ds.side = THREE.DoubleSide; } return m.userData.ds; }
  const anim = fn => anims.push(fn), emit = (obj, x, y, z, kind = 'smoke') => emitters.push({ obj, local: new THREE.Vector3(x, y, z), kind });
  // waving cloth on a pole; the plane's vertices ripple every frame
  const flag = (g, x, y, z, { w = 1.6, h = 1, pole = 5, color = 0xa63a2b } = {}) => {
    cyl(g, 0.06, 0.08, pole, mat(era === 'ancient' ? p.wood : 0x3a3a3c), x, y, z, 6);
    const geo = new THREE.PlaneGeometry(w, h, 10, 4); geo.translate(w / 2, 0, 0);
    const base = geo.attributes.position.array.slice();
    const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, side: THREE.DoubleSide, roughness: 0.9 }));
    m.position.set(x, y + pole - h / 2 - 0.1, z); m.castShadow = true; g.add(m);
    const ph = x * 0.7 + z;
    anim(t => { const a = geo.attributes.position.array; for (let i = 0; i < a.length; i += 3) { const u = base[i] / w; a[i + 2] = Math.sin(t * 4 + base[i] * 2.4 + ph) * 0.22 * u; a[i + 1] = base[i + 1] - u * u * 0.12; } geo.attributes.position.needsUpdate = true; geo.computeVertexNormals(); });
  };
  // a lantern hanging from a pivot that swings
  const lantern = (g, x, y, z, color = 0xc23b2a) => {
    const piv = new THREE.Group(); piv.position.set(x, y, z); g.add(piv);
    box(piv, 0.03, 0.4, 0.03, mat(0x2b2622), 0, -0.4, 0);
    const lm = new THREE.MeshStandardMaterial({ color, emissive: 0xff7a3d, emissiveIntensity: 0.25, roughness: 0.6 });
    add(piv, new THREE.CylinderGeometry(0.22, 0.22, 0.42, 12), lm, 0, -0.62, 0);
    const ph = x + z; anim(t => { piv.rotation.z = Math.sin(t * 1.6 + ph) * 0.12; piv.rotation.x = Math.cos(t * 1.2 + ph) * 0.06; lm.emissiveIntensity = 0.25 + nightGlow.v * 2.2 + Math.sin(t * 9 + ph) * 0.05 * nightGlow.v; });
  };
  const fish = (g, cx, cz, r, n = 3) => {
    for (let i = 0; i < n; i++) {
      const f = add(g, new THREE.SphereGeometry(0.2, 8, 6), mat([0xe0632b, 0xf2efe6, 0xd9a032][i % 3]), cx, 0.1, cz); f.scale.set(1.3, 0.35, 0.55); f.castShadow = false;
      const sp = 0.5 + i * 0.17, ph = i * 2.1, rr = r * (0.45 + i * 0.15);
      anim(t => { const a = t * sp + ph; f.position.set(cx + Math.cos(a) * rr, 0.1 + Math.sin(t * 3 + i) * 0.02, cz + Math.sin(a) * rr); f.rotation.y = -a; });
    }
  };
  const fountain = (g, x, y, z, { n = 60, h = 1.6, color = 0xdceff5 } = {}) => {
    const pos = new Float32Array(n * 3), vel = new Float32Array(n * 3), life = new Float32Array(n);
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const pts = new THREE.Points(geo, new THREE.PointsMaterial({ color, size: 0.14, transparent: true, opacity: 0.85, depthWrite: false })); pts.position.set(x, y, z); g.add(pts);
    const spawn = i => { pos.set([0, 0, 0], i * 3); const a = Math.random() * Math.PI * 2, s = 0.4 + Math.random() * 0.5; vel.set([Math.cos(a) * s, h * (2.2 + Math.random() * 0.6), Math.sin(a) * s], i * 3); life[i] = Math.random(); };
    for (let i = 0; i < n; i++) spawn(i);
    anim((t, dt) => { for (let i = 0; i < n; i++) { vel[i * 3 + 1] -= 9.8 * dt; pos[i * 3] += vel[i * 3] * dt; pos[i * 3 + 1] += vel[i * 3 + 1] * dt; pos[i * 3 + 2] += vel[i * 3 + 2] * dt; if (pos[i * 3 + 1] < 0) spawn(i); } geo.attributes.position.needsUpdate = true; });
  };
  const FRAME = { ancient: 0x6b4a32, early: 0xefe8da, modern: 0x55585c, future: 0xe9eef2 }[era];
  // framed window facing +z, rotated by ry; every piece is a direct child so the baker can merge it
  const win = (g, x, y, z, w = 0.9, h = 1.3, ry = 0, { sill = true, mull = true } = {}) => {
    const sn = Math.sin(ry), cs = Math.cos(ry), at = d => [x + sn * d, z + cs * d];
    let [a, b] = at(0); box(g, w + 0.18, h + 0.18, 0.06, mat(FRAME), a, y - 0.09, b, ry);
    [a, b] = at(0.035); box(g, w, h, 0.04, glass(), a, y, b, ry);
    if (mull) { [a, b] = at(0.06); box(g, 0.05, h, 0.03, mat(FRAME), a, y, b, ry); box(g, w, 0.05, 0.03, mat(FRAME), a, y + h * 0.62, b, ry); }
    if (sill) { [a, b] = at(0.08); box(g, w + 0.3, 0.07, 0.16, mat(FRAME), a, y - 0.12, b, ry); }
  };
  const winRow = (g, x0, x1, n, y, z, w, h, ry = 0, o) => { for (let i = 0; i < n; i++) { const t = n === 1 ? 0.5 : i / (n - 1), x = x0 + (x1 - x0) * t; ry ? win(g, z, y, x, w, h, ry, o) : win(g, x, y, z, w, h, 0, o); } };
  const cornice = (g, w, d, y, x = 0, z = 0, m = mat(FRAME)) => { box(g, w + 0.5, 0.18, d + 0.5, m, x, y, z); box(g, w + 0.28, 0.12, d + 0.28, m, x, y - 0.12, z); };
  const railX = (g, x0, x1, z, y, m = mat(FRAME), h = 0.55, step = 0.9) => { const n = Math.max(1, Math.round((x1 - x0) / step)); for (let i = 0; i <= n; i++) box(g, 0.08, h, 0.08, m, x0 + (x1 - x0) * i / n, y, z); box(g, x1 - x0, 0.06, 0.1, m, (x0 + x1) / 2, y + h - 0.06, z); };
  const railZ = (g, z0, z1, x, y, m = mat(FRAME), h = 0.55, step = 0.9) => { const n = Math.max(1, Math.round((z1 - z0) / step)); for (let i = 0; i <= n; i++) box(g, 0.08, h, 0.08, m, x, y, z0 + (z1 - z0) * i / n); box(g, 0.1, 0.06, z1 - z0, m, x, y + h - 0.06, (z0 + z1) / 2); };
  const steps = (g, w, n, x, z, m, rise = 0.17, run = 0.3) => { for (let i = 0; i < n; i++) box(g, w, rise * (n - i), run, m, x, 0, z + i * run); };
  const ribs = (g, r, n, m, x = 0, y = 0, z = 0, t = 0.07) => { for (let i = 0; i < n; i++) { const o = add(g, new THREE.TorusGeometry(r, t, 4, 24, Math.PI), m, x, y, z); o.rotation.y = i * Math.PI / n; } };
  const door = (g, x, y, z, w, h, color, ry = 0) => { const sn = Math.sin(ry), cs = Math.cos(ry); box(g, w + 0.24, h + 0.12, 0.08, mat(FRAME), x, y, z, ry); box(g, w, h, 0.06, mat(color), x + sn * 0.04, y, z + cs * 0.04, ry); };
  return { p, mat, glass, glow, add, box, cyl, sphere, dome, pyramid, hip, gable, anim, emit, anims, emitters, flag, lantern, fish, fountain, curvedHip, era, FRAME, win, winRow, cornice, railX, railZ, steps, ribs, door };
}

// A hall: platform + body + columns + roof, styled by era. Returns top height.
function hall(k, g, era, { w, d, h, x = 0, z = 0, y = 0, roof = 'hip', storeys = 1 }) {
  const { p, mat, box, cyl, gable, glass } = k, hip = era === 'ancient' ? k.curvedHip : k.hip;
  box(g, w + 1.2, 0.5, d + 1.2, mat(p.stone), x, y, z);
  let top = y + 0.5;
  for (let s = 0; s < storeys; s++) {
    const sw = w * (1 - s * 0.18), sd = d * (1 - s * 0.18);
    box(g, sw, h, sd, mat(p.plaster), x, top, z);
    if (era === 'ancient') {
      const bays = Math.round(sw / 1.6), bw = sw / bays;
      for (let i = 0; i <= bays; i++) cyl(g, 0.16, 0.16, h, mat(p.wood), x - sw / 2 + i * bw, top, z + sd / 2 + 0.05, 8);
      // lattice doors in the middle bays, plain panels outside
      for (let i = 0; i < bays; i++) { const cx = x - sw / 2 + (i + 0.5) * bw, mid = Math.abs(i - (bays - 1) / 2) < 1.6;
        box(g, bw - 0.36, h * (mid ? 0.82 : 0.5), 0.06, mat(mid ? 0x7a3b2a : 0x8a5a3c), cx, top + (mid ? 0 : h * 0.3), z + sd / 2 + 0.02);
        if (mid) for (let j = 1; j < 4; j++) box(g, bw - 0.4, 0.04, 0.03, mat(0xc9a24a), cx, top + h * 0.82 * j / 4, z + sd / 2 + 0.06); }
      // dougong band under the eaves
      box(g, sw + 0.5, 0.34, sd + 0.5, mat(0x3f2c21), x, top + h - 0.05, z);
      for (let i = 0; i <= bays * 2; i++) box(g, 0.22, 0.2, 0.3, mat(0x4f7a6a), x - sw / 2 + i * bw / 2, top + h - 0.02, z + sd / 2 + 0.28);
    }
    top += h;
    if (s < storeys - 1) { hip(g, sw, sd, 0.6, 0.9, mat(p.roof), x, top, z); top += 0.3; }
  }
  const tw = w * (1 - (storeys - 1) * 0.18), td = d * (1 - (storeys - 1) * 0.18);
  if (roof === 'hip') hip(g, tw, td, Math.min(tw, td) * 0.45, era === 'ancient' ? 1.0 : 0.6, mat(p.roof), x, top, z, era === 'ancient' ? 0.18 : 0);
  if (roof === 'gable') gable(g, tw, td, td * 0.38, 0.4, mat(p.roof), x, top, z);
  if (roof === 'flat') box(g, tw + 0.3, 0.35, td + 0.3, mat(p.wall), x, top, z);
  return top + (roof === 'hip' ? Math.min(tw, td) * 0.45 : roof === 'gable' ? td * 0.38 : 0.35);
}

// ---------- typologies ----------
// Each returns the label height. Footprint is centred on the origin; the front faces +z.
const TYPES = {
  landmark(k, g, era) {
    const { p, mat, box, cyl, hip, pyramid, glass, glow, add } = k;
    if (era === 'ancient') {
      // palace: three-tier terrace, double-eave main hall, flanking halls, a pair of que towers in front
      for (const [w, d, y] of [[30, 18, 0], [25, 14, 0.8], [20, 10.5, 1.6]]) box(g, w, 0.8, d, mat(p.stone), 0, y, -1);
      for (let i = 0; i < 12; i++) box(g, 4.4, 0.2 * (i + 1), 0.32, mat(p.stone), 0, 0, 10.9 - i * 0.32); // front steps up to the top terrace
      for (const sx of [-1, 1]) box(g, 0.4, 2.6, 4, mat(0xd8cfbe), sx * 2.4, 0, 9.2);
      const rail = mat(0xece6da);
      for (const [w, dd, y] of [[25, 14, 1.6], [20, 10.5, 2.4]]) {
        const z0 = -1;
        for (const [ax, az, len, rot] of [[0, z0 - dd / 2, w, 0], [-w / 2, z0, dd, 1], [w / 2, z0, dd, 1]]) {
          const n = Math.round(len / 1.3);
          for (let i = 0; i <= n; i++) { const tt = -len / 2 + i * len / n; box(g, 0.16, 0.55, 0.16, rail, rot ? ax : tt, y, rot ? z0 + tt : az); }
          box(g, rot ? 0.1 : len, 0.08, rot ? len : 0.1, rail, ax, y + 0.46, az);
        }
        for (const sx of [-1, 1]) { const seg = (w / 2 - 2.4), cx = sx * (2.4 + seg / 2), n = Math.round(seg / 1.3);
          for (let i = 0; i <= n; i++) box(g, 0.16, 0.55, 0.16, rail, sx * (2.4 + i * seg / n), y, z0 + dd / 2);
          box(g, seg, 0.08, 0.1, rail, cx, y + 0.46, z0 + dd / 2); }
      }
      const y0 = 2.4;
      box(g, 15, 3.4, 6.5, mat(p.plaster), 0, y0, -1.6);
      for (let i = 0; i <= 8; i++) cyl(g, 0.22, 0.22, 3.4, mat(p.wood), -7.5 + i * 15 / 8, y0, 1.75, 8);
      k.curvedHip(g, 15, 6.5, 1.0, 1.4, mat(p.roof), 0, y0 + 3.4, -1.6, 0.2);
      box(g, 11, 1.6, 4.6, mat(p.plaster), 0, y0 + 3.9, -1.6);
      k.curvedHip(g, 11, 4.6, 2.6, 1.3, mat(p.roof), 0, y0 + 5.5, -1.6, 0.25);
      for (const sx of [-1, 1]) { box(g, 6, 2.4, 4, mat(p.plaster), sx * 12.5, 0.8, -1.5); k.curvedHip(g, 6, 4, 1.4, 0.8, mat(p.roof), sx * 12.5, 3.2, -1.5, 0.12); }
      for (const sx of [-1, 1]) { box(g, 2.2, 5.2, 2.2, mat(p.wall), sx * 6, 0, 11); box(g, 2.8, 1.2, 2.8, mat(p.plaster), sx * 6, 5.2, 11); k.curvedHip(g, 2.8, 2.8, 1.2, 0.6, mat(p.roof), sx * 6, 6.4, 11, 0.1); }
      for (const sx of [-1, 1]) { k.flag(g, sx * 11.5, 0, 8.6, { color: sx < 0 ? 0xa63a2b : 0xc9a24a, pole: 6.5, w: 1.8, h: 1.1 }); k.lantern(g, sx * 6 + sx * 1.5, 6.2, 11.4); k.lantern(g, sx * 6 - sx * 1.5, 6.2, 11.4); }
      return y0 + 8.4;
    }
    if (era === 'early') {
      box(g, 22, 1, 12, mat(p.stone), 0, 0, -1);
      box(g, 20, 5.5, 9, mat(p.wall), 0, 1, -1.5); box(g, 20.6, 0.6, 9.6, mat(p.stone), 0, 6.5, -1.5); box(g, 20.3, 0.25, 9.3, mat(p.stone), 0, 3.6, -1.5); box(g, 20.4, 0.4, 9.4, mat(p.stone), 0, 1, -1.5);
      for (let i = 0; i < 6; i++) cyl(g, 0.3, 0.3, 4.6, mat(p.stone), -5 + i * 2, 1, 3.6, 12);
      box(g, 12, 0.7, 2.2, mat(p.stone), 0, 5.6, 3.6); k.gable(g, 12, 2.2, 1.2, 0.2, mat(p.stone), 0, 6.3, 3.6);
      for (let r = 0; r < 2; r++) for (const sx of [-1, 1]) k.winRow(g, sx * 6.2, sx * 9, 3, 1.9 + r * 2.3, 3.02, 0.8, 1.4);
      for (const sx of [-1, 1]) for (let r = 0; r < 2; r++) k.winRow(g, -4.5, 1.5, 4, 1.9 + r * 2.3, sx * 10.02, 0.8, 1.4, sx * Math.PI / 2);
      for (const x of [-10, -5.6, 5.6, 10]) box(g, 0.5, 5.5, 0.3, mat(p.stone), x, 1, 3.05);       // pilasters
      k.steps(g, 10, 5, 0, 3.6, mat(p.stone), 0.2, 0.32); k.door(g, 0, 1, 3.03, 2, 3, 0x4a3a30);
      k.railX(g, -10, 10, 3.2, 7.1, mat(p.stone), 0.6, 0.8);
      for (const sx of [-1, 1]) { box(g, 0.35, 9, 0.35, mat(p.stone), sx * 2.2, 7.1, 0.2); box(g, 0.35, 9, 0.35, mat(p.stone), sx * 2.2, 7.1, -4.2); }
      for (let r = 0; r < 3; r++) k.win(g, 0, 8.4 + r * 2.4, 0.22, 0.7, 1.3);
      box(g, 4.4, 9, 4.4, mat(p.wall), 0, 7.1, -2); box(g, 4.8, 0.4, 4.8, mat(p.stone), 0, 16.1, -2);
      box(g, 3.8, 2.6, 3.8, mat(p.plaster), 0, 16.5, -2);
      for (const [rx, rz, ry] of [[0, 1.92, 0], [1.92, 0, Math.PI / 2], [0, -1.92, 0], [-1.92, 0, Math.PI / 2]]) { const c = add(g, new THREE.CylinderGeometry(1.1, 1.1, 0.08, 24), mat(0xf6f1e6), rx, 17.8, rz - 2); c.rotation.set(Math.PI / 2, 0, ry); }
      pyramid(g, 4.6, 3.4, mat(p.roof), 0, 19.1, -2); k.cyl(g, 0.05, 0.12, 1.6, mat(0x3a3a3c), 0, 22.4, -2, 6); k.sphere(g, 0.16, mat(0xc9a24a), 0, 24.1, -2);
      k.cornice(g, 3.8, 3.8, 19.1, 0, -2, mat(p.stone));
      for (const [rx, rz] of [[0, 1.98], [1.98, 0], [0, -1.98], [-1.98, 0]]) {
        const face = new THREE.Group(); face.position.set(rx, 17.8, rz - 2); face.rotation.y = Math.atan2(rx, rz); g.add(face);
        const hh = new THREE.Group(), mh = new THREE.Group(), sh = new THREE.Group(); face.add(hh, mh, sh);
        box(hh, 0.1, 0.55, 0.04, mat(0x2b2622), 0, 0, 0.02); box(mh, 0.07, 0.85, 0.04, mat(0x2b2622), 0, 0, 0.05); box(sh, 0.03, 0.9, 0.03, mat(0xa63a2b), 0, 0, 0.08);
        k.anim(() => { const d = new Date(), s = d.getSeconds() + d.getMilliseconds() / 1000, m = d.getMinutes() + s / 60, h = (d.getHours() % 12) + m / 60;
          sh.rotation.z = -s / 60 * Math.PI * 2; mh.rotation.z = -m / 60 * Math.PI * 2; hh.rotation.z = -h / 12 * Math.PI * 2; });
      }
      return 22.6;
    }
    if (era === 'modern') {
      box(g, 20, 3, 11, mat(p.wall), 0, 0, 0); box(g, 21, 0.4, 12, mat(p.roof), 0, 3, 0); box(g, 16, 2.4, 0.1, k.glass(), 0, 0.3, 5.52); box(g, 4.6, 16, 4.6, k.glass(), 0, 2.4, -0.6);
      for (let i = 1; i < 16; i += 2) box(g, 4.72, 0.12, 4.72, mat(p.roof), 0, 2.4 + i, -0.6);
      box(g, 4.8, 0.5, 4.8, mat(p.wall), 0, 18.4, -0.6);
      box(g, 3.4, 1.6, 3.4, mat(p.wall), 0, 18.9, -0.6); box(g, 3.6, 0.25, 3.6, mat(p.roof), 0, 20.5, -0.6);           // crown
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(g, 0.25, 16, 0.25, mat(p.wall), sx * 2.3, 2.4, -0.6 + sz * 2.3);  // corner fins
      box(g, 8, 0.3, 3, mat(p.wall), 0, 2.6, 6.6); for (const sx of [-1, 1]) box(g, 0.2, 2.6, 0.2, mat(p.wall), sx * 3.8, 0, 7.9);  // entrance canopy
      k.door(g, 0, 0, 5.54, 3, 2.3, 0x2c3a44); for (const x of [-7, -4.5, 4.5, 7]) { box(g, 1.4, 0.6, 1.4, mat(p.stone), x, 0, 7.4); k.sphere(g, 0.55, mat(p.leaf), x, 1.0, 7.4); }
      { const car = box(g, 0.9, 1.1, 0.3, mat(0xf4f1e8, { emissive: 0xfff1cf, emissiveIntensity: 0.3 }), 1.2, 3, 1.86); k.anim(t => { const u = (Math.sin(t * 0.35) + 1) / 2; car.position.y = 3.2 + u * 14; });
        const bm = new THREE.MeshStandardMaterial({ color: 0xff3b2f, emissive: 0xff2a1a, emissiveIntensity: 0 }); add(g, new THREE.SphereGeometry(0.22, 10, 8), bm, 0, 19.4, -0.6); box(g, 0.06, 1, 0.06, mat(0x3a3a3c), 0, 18.9, -0.6);
        k.anim(t => { bm.emissiveIntensity = (t % 1.6) < 0.2 ? 3 : 0.05; }); }
      return 19.4;
    }
    // future
    cyl(g, 9, 10, 0.6, mat(p.stone), 0, 0, 0, 64); cyl(g, 3.6, 4.4, 0.8, mat(p.wall), 0, 0.6, 0, 40); { const r0 = add(g, new THREE.TorusGeometry(9.5, 0.1, 8, 96), glow(), 0, 0.62, 0); r0.rotation.x = Math.PI / 2; k.anim(t => r0.scale.setScalar(1 + Math.sin(t * 1.6) * 0.015)); }
    cyl(g, 0.6, 2.2, 15, mat(p.wall), 0, 0.8, 0, 32);
    [[6, 3.2], [10, 2.5], [13.6, 1.8]].forEach(([y, r], i) => { const ring = add(g, new THREE.TorusGeometry(r, 0.12, 8, 48), glow(), 0, y, 0); ring.rotation.x = Math.PI / 2;
      k.anim(t => { ring.rotation.z = t * (0.5 + i * 0.3) * (i % 2 ? -1 : 1); ring.rotation.x = Math.PI / 2 + Math.sin(t * 0.7 + i) * 0.12; ring.position.y = y + Math.sin(t * 1.1 + i * 2) * 0.25; }); });
    for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2, f = box(g, 0.3, 6, 2.2, mat(p.wall), Math.cos(a) * 2.4, 0.6, Math.sin(a) * 2.4, Math.PI / 2 - a); }  // buttress fins
    for (let i = 0; i < 6; i++) { const a = (i + 0.5) / 6 * Math.PI * 2; box(g, 0.9, 1.6, 0.08, k.glass(), Math.cos(a) * 3.62, 1.4, Math.sin(a) * 3.62, Math.PI / 2 - a); }
    { const orb = k.sphere(g, 0.7, glow(p.glow, 2.2), 0, 16.6, 0); k.anim(t => { const s = 1 + Math.sin(t * 2.2) * 0.12; orb.scale.setScalar(s); orb.position.y = 16.6 + Math.sin(t * 1.3) * 0.3; }); k.emit(g, 0, 17, 0, 'spark'); }
    return 18;
  },

  workshop(k, g, era) {
    const { p, mat, box, cyl, hip, gable, dome, glow, add } = k;
    if (era === 'ancient') {
      const top = hall(k, g, era, { w: 12, d: 6, h: 2.6 });
      cyl(g, 1.4, 1.9, 2.2, mat(p.wall), 5.6, 0, -5.4); add(g, new THREE.ConeGeometry(1.5, 1.4, 14), mat(p.wall), 5.6, 2.9, -5.4);
      cyl(g, 0.35, 0.35, 1.6, mat(p.stone), 5.6, 3.4, -5.4, 8); k.emit(g, 5.6, 5.2, -5.4);
      { const fm = new THREE.MeshStandardMaterial({ color: 0x3a1b0e, emissive: 0xff6a1f, emissiveIntensity: 1 }); box(g, 0.8, 0.7, 0.12, fm, 5.6, 0.2, -3.58); k.anim(t => { fm.emissiveIntensity = 0.9 + Math.sin(t * 13) * 0.25 + Math.sin(t * 7.3) * 0.2 + nightGlow.v * 1.5; }); }
      return top;
    }
    if (era === 'early') {
      box(g, 13.6, 0.5, 7.6, mat(p.stone), 0, 0, 0);
      box(g, 13, 4.2, 7, mat(p.wall), 0, 0.5, 0); gable(g, 13, 7, 2.4, 0.3, mat(p.roof), 0, 4.7, 0);
      box(g, 4, 1.1, 2.2, mat(p.wall), 0, 6.1, 0); gable(g, 4, 2.2, 0.7, 0.2, mat(p.roof), 0, 7.2, 0); k.winRow(g, -1.4, 1.4, 3, 6.25, 1.12, 0.6, 0.6, 0, { sill: false });
      for (let i = -3; i <= 3; i++) box(g, 0.4, 4.2, 0.2, mat(0x8f4632), i * 2.1, 0.5, 3.55);                         // brick pilasters
      for (let i = -2; i <= 2; i++) if (i) k.win(g, i * 2.1 + (i > 0 ? -1.05 : 1.05), 1.6, 3.52, 1.1, 2); k.door(g, 0, 0.5, 3.52, 1.8, 2.6, 0x3d4a52);
      k.cornice(g, 13, 7, 4.55, 0, 0, mat(p.stone));
      cyl(g, 0.55, 0.8, 12, mat(p.wall), 5, 0, -5, 12); box(g, 1.7, 0.3, 1.7, mat(p.stone), 5, 12, -5); k.emit(g, 5, 12.6, -5);
      for (const y of [3, 6.5, 10]) cyl(g, 0.66, 0.7, 0.25, mat(p.stone), 5, y, -5, 12);
      for (const [x, z] of [[-4.6, -4.6], [-4.6, -6], [-6, -4.6], [-6, -6]]) box(g, 0.14, 3.4, 0.14, mat(0x3a3a3c), x, 0, z);
      cyl(g, 1.1, 1.1, 1.6, mat(0x6b5a4a), -5.3, 3.4, -5.3, 12); k.pyramid(g, 1.6, 0.8, mat(p.roof), -5.3, 5, -5.3);
      return 12.5;
    }
    if (era === 'modern') {
      box(g, 14, 4, 8, mat(p.wall), 0, 0, 0);
      for (let i = 0; i < 5; i++) { const s = new THREE.Shape(); s.moveTo(0, 0); s.lineTo(0, 1.6); s.lineTo(2.8, 0); s.lineTo(0, 0);
        const geo = new THREE.ExtrudeGeometry(s, { depth: 8, bevelEnabled: false }); geo.translate(-1.4, 0, -4);
        add(g, geo, mat(p.roof), -5.6 + i * 2.8, 4, 0); box(g, 0.08, 1.5, 8, k.glass(), -7 + i * 2.8 + 0.06, 4, 0); }
      box(g, 6, 2.6, 0.1, k.glass(), 0, 0.3, 4.02);
      for (const [x, z, w, dd] of [[-5, -2.6, 2, 1.4], [-2.6, -2.8, 1.2, 1.2], [5.4, -2.4, 1.6, 2]]) { box(g, w, 0.9, dd, mat(0xa9aaa6), x, 5.6, z); box(g, w * 0.7, 0.12, dd * 0.7, mat(0x6d6f72), x, 6.5, z); }
      for (let i = -6; i <= 6; i += 1.5) box(g, 0.05, 4, 0.04, mat(0xb9b7b1), i, 0, 4.02);                               // panel joints
      for (const x of [-5, 5]) { box(g, 2.4, 2.8, 0.06, mat(0x8d8f92), x, 0, 4.03); for (let j = 1; j < 7; j++) box(g, 2.4, 0.04, 0.03, mat(0x6d6f72), x, j * 0.4, 4.07); }  // roller doors
      box(g, 7, 0.2, 1.8, mat(p.wall), 0, 3, 4.9); box(g, 14.2, 0.25, 8.2, mat(0xc9c7c1), 0, 3.9, 0);
      return 6;
    }
    dome(g, 5, mat(p.wall), 0, 0, 0); cyl(g, 5.2, 5.2, 0.4, mat(p.stone), 0, 0, 0, 40);
    const ring = add(g, new THREE.TorusGeometry(5.1, 0.09, 8, 64), glow(), 0, 0.8, 0); ring.rotation.x = Math.PI / 2; k.anim(t => { ring.position.y = 0.8 + (t * 1.2 % 4); ring.scale.setScalar(1 - (t * 1.2 % 4) * 0.08); });
    box(g, 3.2, 2.6, 0.2, k.glass(), 0, 0.4, 4.6);
    k.ribs(g, 5.04, 6, mat(p.stone), 0, 0, 0, 0.09); add(g, new THREE.TorusGeometry(1.9, 0.12, 6, 20, Math.PI), mat(p.stone), 0, 0.4, 4.66);
    for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2; if (Math.abs(Math.sin(a) - 1) < 0.4) continue; box(g, 0.8, 0.35, 0.08, glow(), Math.cos(a) * 5.2, 0.1, Math.sin(a) * 5.2, Math.PI / 2 - a); }
    for (const s of [-1, 1]) { const arm = new THREE.Group(); arm.position.set(s * 6.6, 0, -1.5); g.add(arm);
      box(arm, 0.35, 6, 0.35, mat(p.stone), 0, 0, 0); box(arm, 3, 0.35, 0.35, mat(p.stone), -s * 1.4, 5.8, 0); const tip = k.sphere(arm, 0.35, glow(), -s * 2.8, 5.8, 0);
      k.anim(t => { arm.rotation.y = Math.sin(t * 0.6 + s) * 0.5; tip.scale.setScalar(1 + Math.max(0, Math.sin(t * 3 + s * 2)) * 0.5); }); }
    return 6.2;
  },

  press(k, g, era) {
    const { p, mat, box, cyl, hip, glass, glow, add } = k;
    if (era === 'ancient') return hall(k, g, era, { w: 8, d: 6, h: 2.4, storeys: 2 });
    if (era === 'early') {
      box(g, 10, 7.5, 6, mat(p.plaster), 0, 0, -0.6);
      for (let i = 0; i <= 4; i++) { box(g, 0.5, 3, 0.5, mat(p.stone), -4.75 + i * 2.375, 0, 2.6); box(g, 0.7, 0.25, 0.7, mat(p.stone), -4.75 + i * 2.375, 2.75, 2.6); }
      box(g, 10, 0.5, 1.6, mat(p.stone), 0, 3, 2.0);
      for (let i = 0; i < 4; i++) k.door(g, -3.56 + i * 2.375, 0, 2.42, 1.3, 2.2, i % 2 ? 0x5a6e7a : 0x4a3a30);           // shopfronts under the arcade
      for (let r = 0; r < 2; r++) k.winRow(g, -3.6, 3.6, 4, 4 + r * 1.9, 2.42, 0.95, 1.3);
      k.railX(g, -4.9, 4.9, 2.75, 3.5, mat(p.stone), 0.55, 0.7);
      k.cornice(g, 10, 6, 7.5, 0, -0.6, mat(p.stone));
      for (const sx of [-1, 1]) for (let r = 0; r < 2; r++) k.winRow(g, -2.6, 1.4, 2, 4 + r * 1.9, sx * 5.02, 0.9, 1.3, sx * Math.PI / 2);
      box(g, 10.4, 0.8, 6.4, mat(p.stone), 0, 7.5, -0.6); box(g, 3, 1.2, 0.4, mat(p.stone), 0, 8.3, 2.3); k.flag(g, 4.4, 8.3, -2.6, { color: 0x3c5a7a, pole: 3.2, w: 1.4, h: 0.85 });
      return 9.6;
    }
    if (era === 'modern') {
      box(g, 9, 10, 7, k.glass(), 0, 0, 0);
      for (let i = 0; i <= 5; i++) box(g, 0.14, 10, 7.1, mat(p.wall), -4.5 + i * 1.8, 0, 0);
      box(g, 9.4, 0.6, 7.4, mat(p.wall), 0, 10, 0); box(g, 11, 0.4, 2.8, mat(p.wall), 0, 3.2, 4.8); box(g, 2.2, 1.2, 1.6, mat(0xa9aaa6), -3, 10.6, -2); box(g, 1.2, 1.6, 1.2, mat(0x8d8f92), 3.2, 10.6, -2.4);
      for (let f = 1; f < 5; f++) box(g, 9.06, 0.18, 7.06, mat(p.wall), 0, f * 2, 0);                                    // floor slabs
      box(g, 2.6, 10.6, 2.6, mat(p.stone), -5, 0, -1.8); k.door(g, 0, 0, 3.54, 3, 2.4, 0x2c3a44);
      { const sm = new THREE.MeshStandardMaterial({ color: 0x111111, emissive: 0xffffff, emissiveIntensity: 0.9 }); box(g, 4.2, 1.8, 0.15, sm, 0, 10.6, 3.2); const c = new THREE.Color(); k.anim(t => { c.setHSL((t * 0.06) % 1, 0.65, 0.55); sm.emissive.copy(c); }); }
      return 11;
    }
    for (let i = 0; i < 5; i++) {
      const y = 1.2 + i * 2.2, w = 8 - i * 0.6;
      const slab = new THREE.Group(); g.add(slab);
      box(slab, w, 0.4, 6 - i * 0.3, mat(p.wall), Math.sin(i * 1.3) * 0.8, y, 0);
      box(slab, w + 0.05, 0.06, 6.05 - i * 0.3, glow(), Math.sin(i * 1.3) * 0.8, y - 0.06, 0);
      k.anim(t => { slab.position.y = Math.sin(t * 0.9 + i * 0.8) * 0.18; slab.rotation.y = Math.sin(t * 0.25 + i) * 0.06; });
    }
    cyl(g, 0.7, 0.7, 11.6, k.glass(), 0, 0, 0, 16);
    cyl(g, 4.2, 4.6, 0.8, mat(p.stone), 0, 0, 0, 32); box(g, 2.6, 2.2, 0.2, k.glass(), 0, 0.8, 4.1); add(g, new THREE.TorusGeometry(1.5, 0.1, 6, 20, Math.PI), glow(), 0, 0.8, 4.2);
    { const hm = new THREE.MeshBasicMaterial({ color: p.glow, transparent: true, opacity: 0.35, side: THREE.DoubleSide, depthWrite: false });
      [3.4, 6.6, 9.8].forEach((y, i) => { const piv = new THREE.Group(); piv.position.y = y; g.add(piv); const pl = new THREE.Mesh(new THREE.PlaneGeometry(1.8, 1.1), hm); pl.position.set(5.6, 0, 0); pl.rotation.y = Math.PI / 2; piv.add(pl);
        const fr = new THREE.Mesh(new THREE.EdgesGeometry(pl.geometry), new THREE.LineBasicMaterial({ color: p.glow })); pl.add(fr);
        k.anim(t => { piv.rotation.y = t * (0.35 + i * 0.12) + i * 2; pl.position.y = Math.sin(t * 1.5 + i) * 0.2; hm.opacity = 0.28 + Math.sin(t * 3) * 0.07; }); }); }
    return 12.4;
  },

  garden(k, g, era) {
    const { p, mat, box, cyl, hip, dome, glass, glow, add, sphere } = k;
    const tree = (x, z, s = 1) => { const tg = new THREE.Group(); tg.position.set(x, 0, z); treeParts(k, tg, s); tg.children.slice().forEach(o => { o.position.add(tg.position); g.add(o); }); };
    const pond = (x, z, r) => { const m = new THREE.MeshStandardMaterial({ color: p.water, roughness: 0.15, metalness: 0.1, emissive: 0xffffff, emissiveIntensity: 0 });
      const o = add(g, new THREE.CylinderGeometry(r, r, 0.06, 28), m, x, 0.06, z); o.receiveShadow = true; k.anim(t => { m.emissiveIntensity = 0.04 + Math.max(0, Math.sin(t * 1.7 + x)) * 0.12; }); };
    if (era === 'ancient') {
      for (const [w, d, x, z] of [[14, 0.5, 0, -5], [0.5, 10, -7, 0], [0.5, 10, 7, 0], [5.5, 0.5, -4.25, 5], [5.5, 0.5, 4.25, 5]]) { box(g, w, 2, d, mat(p.wall), x, 0, z); box(g, w + 0.3, 0.14, d + 0.3, mat(p.roof), x, 2, z); box(g, w + 0.1, 0.12, d + 0.1, mat(0x34383b), x, 2.14, z); }
      { // gatehouse (门楼) filling the 3 m gap in the south wall
        const GZ = 5, pier = mat(p.wall), red = mat(0x8e2f22), gold = mat(0xc9a24a);
        for (const sx of [-1, 1]) { box(g, 0.55, 2.7, 0.8, pier, sx * 1.62, 0, GZ); box(g, 0.75, 0.16, 1, mat(p.stone), sx * 1.62, 0, GZ); }
        box(g, 3.8, 0.3, 0.55, mat(p.wood), 0, 2.35, GZ);                       // lintel
        box(g, 3.5, 0.2, 0.7, mat(0x3f2c21), 0, 2.65, GZ);                      // bracket band
        for (let i = 0; i < 5; i++) box(g, 0.18, 0.16, 0.3, mat(0x4f7a6a), -1.4 + i * 0.7, 2.62, GZ + 0.4);
        k.curvedHip(g, 3.6, 1.1, 0.75, 0.5, mat(p.roof), 0, 2.85, GZ, 0.06);
        box(g, 3.1, 0.14, 0.7, mat(p.stone), 0, 0, GZ); box(g, 3.6, 0.18, 0.7, mat(p.stone), 0, 0, GZ + 0.7);  // threshold + step
        const th = 0.6, L = 1.32; // two leaves swung 34° into the court
        for (const sx of [-1, 1]) {
          const hx = sx * 1.32, cx = hx - sx * (L / 2) * Math.cos(th), cz = GZ - (L / 2) * Math.sin(th), ry = sx * -th;
          box(g, L, 2.15, 0.09, red, cx, 0.12, cz, ry);
          const ux = -sx * Math.cos(th), uz = -Math.sin(th), nx = Math.sin(th) * -sx * -1, nz = Math.cos(th);
          for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) { const along = 0.25 + c * 0.38; box(g, 0.07, 0.07, 0.05, gold, hx + ux * along + nx * 0.05 * 0, 0.6 + r * 0.45, GZ + uz * along + 0.06 * nz, ry); }
          k.add(g, new THREE.TorusGeometry(0.07, 0.018, 4, 10), gold, hx + ux * (L - 0.18), 1.2, GZ + uz * (L - 0.18) + 0.07, ry);
        }
      }
      const top = hall(k, g, era, { w: 7, d: 3.4, h: 2.2, z: -2.6 });
      cyl(g, 0.12, 0.12, 2, mat(p.wood), 3.6, 0, 2.4, 6); k.curvedHip(g, 1.6, 1.6, 1.1, 0.4, mat(p.roof), 3.6, 2, 2.4, 0.1);
      pond(-3, 2.2, 1.6); k.fish(g, -3, 2.2, 1.6, 3); tree(-5.4, 3.6, 0.8); tree(5.4, -3.6, 0.8);
      return top;
    }
    if (era === 'early') {
      box(g, 8.6, 0.5, 6.6, mat(p.stone), 0, 0, -1.5);
      box(g, 8, 4.5, 6, mat(p.plaster), 0, 0.5, -1.5); hip(g, 8, 6, 2.6, 0.5, mat(p.roof), 0, 5, -1.5); k.cornice(g, 8, 6, 4.85, 0, -1.5, mat(p.stone));
      box(g, 8.4, 0.3, 2.2, mat(p.stone), 0, 2.6, 2.6); for (let i = 0; i < 5; i++) cyl(g, 0.16, 0.16, 2.6, mat(p.stone), -3.8 + i * 1.9, 0, 3.4, 10);
      k.railX(g, -4.1, 4.1, 3.6, 2.9, mat(p.stone), 0.5, 0.6);
      for (const r of [0, 1]) k.winRow(g, -2.6, 2.6, 3, 1.2 + r * 2.1, 1.52, 0.8, 1.2);
      for (const x of [-2.6, 2.6]) for (const r of [0, 1]) { box(g, 0.3, 1.3, 0.06, mat(0x4a6a52), x - 0.6, 1.15 + r * 2.1, 1.56); box(g, 0.3, 1.3, 0.06, mat(0x4a6a52), x + 0.6, 1.15 + r * 2.1, 1.56); }
      box(g, 0.8, 2, 0.8, mat(p.wall), 2.4, 6.4, -2.8); k.steps(g, 2.4, 3, 0, 1.6, mat(p.stone), 0.17, 0.3);
      for (const sx of [-1, 1]) { k.railX(g, sx * 7.5, sx * 1.5, 7.5, 0, mat(0xefe8da), 0.6, 0.5); }
      cyl(g, 1.3, 1.5, 0.5, mat(p.stone), 0, 0, 6); cyl(g, 0.2, 0.3, 1.4, mat(p.stone), 0, 0.5, 6, 10); pond(0, 6, 1.1); k.fountain(g, 0, 1.9, 6, { n: 70, h: 0.75 });
      tree(-5.5, 4.5); tree(5.5, 4.5); tree(-5.5, -4.5, 0.9);
      return 8;
    }
    if (era === 'modern') {
      box(g, 14, 3.4, 6, mat(p.wall), 0, 0, -2); box(g, 18, 0.5, 8, mat(p.wall), 1.5, 3.4, -1.4);
      box(g, 12, 2.6, 0.1, k.glass(), 0, 0.4, 1.02); box(g, 4, 0.4, 4, mat(p.stone), -4, 0, 4.5);
      for (let i = 0; i < 6; i++) box(g, 0.25, 3.4, 0.25, mat(p.wall), -6 + i * 2.4 + 1.2, 0, 2.4);                   // pilotis under the cantilever
      box(g, 18.2, 0.12, 8.2, mat(0x55585c), 1.5, 3.9, -1.4); k.door(g, 2, 0.4, 1.05, 2.2, 2.4, 0x2c3a44);
      for (let i = 0; i < 6; i++) box(g, 0.05, 2.6, 0.06, mat(0x55585c), -6 + i * 2.4, 0.4, 1.08);
      { const sc = add(g, new THREE.TorusGeometry(0.9, 0.22, 8, 16), mat(0xc9a24a, { metalness: 0.4, roughness: 0.4 }), -4, 1.6, 4.5); sc.rotation.y = 0.6; }
      pond(3.5, 4.6, 1.8); k.fountain(g, 3.5, 0.1, 4.6, { n: 50, h: 0.9 }); tree(-7.5, 4.5, 0.9); tree(7.8, 5, 0.9);
      return 4.4;
    }
    dome(g, 5.6, k.glass(), 0, 0, 0); cyl(g, 5.8, 5.8, 0.35, mat(p.stone), 0, 0, 0, 48);
    const ring = add(g, new THREE.TorusGeometry(5.7, 0.08, 8, 64), glow(), 0, 0.5, 0); ring.rotation.x = Math.PI / 2; k.anim(t => { ring.rotation.z = t * 0.2; });
    for (const [x, z, s] of [[-2, -1, 1.2], [1.8, -1.8, 1], [0.4, 1.6, 0.8], [-2.6, 2.2, 0.7]]) { cyl(g, 0.12 * s, 0.16 * s, 1.4 * s, mat(p.trunk), x, 0.35, z, 6); { const c = add(g, new THREE.OctahedronGeometry(0.9 * s, 0), mat(p.leaf, { emissive: p.leaf, emissiveIntensity: 0.25 }), x, 2.2 * s + 0.35, z); k.anim(t => { c.rotation.y = t * 0.6 + x; c.position.y = 2.2 * s + 0.35 + Math.sin(t * 1.4 + z) * 0.12; }); } }
    pond(2.4, 1.4, 1.2);
    k.ribs(g, 5.62, 8, mat(p.wall), 0, 0, 0, 0.06); add(g, new THREE.TorusGeometry(2.9, 0.06, 4, 32, Math.PI), mat(p.wall), 0, 0, 0).rotation.set(0, 0, 0);
    box(g, 2.4, 2.6, 2.4, k.glass(), 0, 0, 5.4); box(g, 2.6, 0.2, 2.6, mat(p.wall), 0, 2.6, 5.4);
    return 6;
  },

  plot(k, g, era) {
    const { p, mat, box } = k;
    for (const [w, d, x, z] of [[12, 0.25, 0, -5], [12, 0.25, 0, 5], [0.25, 10, -6, 0], [0.25, 10, 6, 0]]) box(g, w, 0.25, d, mat(p.stone), x, 0, z);
    for (const [x, z] of [[-6, -5], [6, -5], [-6, 5], [6, 5]]) box(g, 0.25, 1.4, 0.25, mat(p.wood), x, 0, z);
    return 2;
  },
};

// ---------- town ----------
// Typology per category id. Unknown (future) categories take the next free plot.
export const TYPOLOGY = { projects: 'landmark', models: 'workshop', web: 'press', spaces: 'garden' };
export const TYPOLOGY_ZH = { landmark: '地标', workshop: '工坊', press: '书局', garden: '园', plot: '待建' };
export const BUILDING_NAME = {
  landmark: { ancient: '宫殿', early: '钟楼会堂', modern: '玻璃高楼', future: '光环塔' },
  workshop: { ancient: '匠作坊与窑', early: '红砖厂房', modern: '锯齿屋顶厂房', future: '穹顶制造舱' },
  press: { ancient: '两层书楼', early: '骑楼报馆', modern: '玻璃幕墙媒体楼', future: '悬浮信息层塔' },
  garden: { ancient: '院落与池亭', early: '花园洋房', modern: '低平美术馆', future: '生态穹顶' },
};
// Plot centres (building footprint centred here, front facing +z / south). The landmark sits on the axis, behind the centre.
export const PLOTS = {
  landmark: { x: 0, z: -13, r: 17 },
  workshop: { x: -20, z: 5, r: 11 },
  press: { x: 20, z: 5, r: 10 },
  garden: { x: -15, z: 21, r: 10 },
  extra: [{ x: 15, z: 21, r: 9 }],
};

// one tree vocabulary for the whole town: trunk + two stacked low-poly crowns (crystal crowns in the future)
export function treeParts(k, g, s = 1) {
  const { p, mat, cyl, add } = k, fut = k.era === 'future';
  cyl(g, 0.11 * s, 0.17 * s, 1.2 * s, mat(p.trunk), 0, 0, 0, 6);
  const leaf = fut ? mat(p.leaf, { emissive: p.leaf, emissiveIntensity: 0.25 }) : mat(p.leaf), leaf2 = fut ? leaf : mat(new THREE.Color(p.leaf).multiplyScalar(0.85).getHex());
  const a = add(g, fut ? new THREE.OctahedronGeometry(0.85 * s, 0) : new THREE.IcosahedronGeometry(0.95 * s, 0), leaf2, 0, 1.6 * s, 0);
  const b = add(g, fut ? new THREE.OctahedronGeometry(0.6 * s, 0) : new THREE.IcosahedronGeometry(0.68 * s, 0), leaf, 0.12 * s, 2.3 * s, 0.05 * s);
  return [a, b];
}
function trees(k, g, era, spots) {
  for (const [x, z, s] of spots) {
    const tg = new THREE.Group(); tg.position.set(x, 0, z); g.add(tg);
    const [a, b] = treeParts(k, tg, s), ph = x * 0.37 + z * 0.21;
    k.anim(t => { tg.rotation.z = Math.sin(t * 0.9 + ph) * 0.035; tg.rotation.x = Math.cos(t * 0.7 + ph) * 0.025; if (era === 'future') { a.rotation.y = t * 0.4 + x; b.rotation.y = -t * 0.6 + z; } });
  }
}

function bake(root, anims, { band = 0, skip = new Set() } = {}) {
  const cand = root.children.filter(o => o.isMesh && !skip.has(o));
  const snap = () => cand.map(o => [o.position.clone(), o.quaternion.clone(), o.scale.clone(), o.geometry.attributes.position.version]);
  anims.forEach(f => f(1.1, 0.016)); const a = snap(); anims.forEach(f => f(2.7, 0.016)); const b = snap();
  const buckets = new Map();
  cand.forEach((o, i) => {
    if (!(a[i][0].equals(b[i][0]) && a[i][1].equals(b[i][1]) && a[i][2].equals(b[i][2]) && a[i][3] === b[i][3])) return; // animated: keep
    o.updateMatrix();
    const c = new THREE.Vector3().setFromMatrixPosition(o.matrix), dist = Math.hypot(c.x, c.z - 1);
    const key = o.material.uuid + (band ? '|' + Math.floor(dist / band) : '');
    if (!buckets.has(key)) buckets.set(key, { m: o.material, list: [], dist: band ? (Math.floor(dist / band) + 0.5) * band : null });
    buckets.get(key).list.push(o);
  });
  for (const { m, list, dist } of buckets.values()) {
    if (list.length < 2) continue;
    const geos = list.map(o => { let g = o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone(); for (const n of Object.keys(g.attributes)) if (n !== 'position' && n !== 'normal') g.deleteAttribute(n); if (!g.attributes.normal) g.computeVertexNormals(); g.applyMatrix4(o.matrix); return g; });
    const merged = mergeGeometries(geos); geos.forEach(g => g.dispose()); if (!merged) continue;
    const mesh = new THREE.Mesh(merged, m); mesh.castShadow = mesh.receiveShadow = true; mesh.userData = { ...list[0].userData, dist };
    list.forEach(o => { root.remove(o); o.geometry.dispose(); });
    root.add(mesh);
  }
}

// Street network shared by every era: rectangles are painted onto a 0.5 m grid (later layers win),
// then emitted as non-overlapping strips, so no two surfaces are ever coplanar.
export const NET = {
  road: [ // carriageway
    [-30.5, 30.5, 10, 14],            // main east–west street
    [-3, 3, 14, 31.5],                // axis to the south gate
    [-30.5, -15.4, -10, -8], [15.4, 30.5, -10, -8],   // back streets of the residential blocks
  ],
  ringRoad: [[-35, 35, 32, 35], [-35, 35, -35, -32], [-35, -32, -35, 35], [32, 35, -35, 35], [-30.5, -32, 10, 14], [30.5, 32, 10, 14], [-3, 3, 31.5, 32]],
  pave: [ // plazas, pavements, lanes, aprons
    [-12, 12, -4, 10],                // ceremonial plaza
    [-30.5, 30.5, 9, 10], [-30.5, 30.5, 14, 15],      // pavements of the main street
    [-4, -3, 15, 31.5], [3, 4, 15, 31.5],             // pavements of the axis
    [-17.2, -15.6, -30, -10], [15.6, 17.2, -30, -10], // lanes beside the palace precinct
    [-30.5, -17.2, -24.4, -23], [17.2, 30.5, -24.4, -23], [-30.5, -17.2, -17.9, -16.5], [17.2, 30.5, -17.9, -16.5], // lanes between house rows
    [-30.9, -29.7, -8, 9], [29.7, 30.9, -8, 9],       // wall lanes joining back streets to the main street
    [-25.1, -23.9, 15, 29], [23.9, 25.1, 15, 29],     // south lanes beside the wall houses
    [-21, -9, 26.4, 29.4], [9, 21, 26.4, 29.4], [-9, -4, 27.4, 28.6], [4, 9, 27.4, 28.6], // forecourts of the garden / reserve and paths to the axis
    [-23, -17, 8.6, 9], [17, 23, 8.6, 9],             // aprons in front of workshop and press
  ],
};
function surfaces(k, town, era) {
  const { p, mat, box, glow } = k, C = 0.5, N = 160, O = -40;
  const grid = new Uint8Array(N * N);
  const paint = (rects, id) => rects.forEach(([x0, x1, z0, z1]) => {
    const a = Math.max(0, Math.round((Math.min(x0, x1) - O) / C)), b = Math.min(N, Math.round((Math.max(x0, x1) - O) / C));
    const c = Math.max(0, Math.round((Math.min(z0, z1) - O) / C)), d = Math.min(N, Math.round((Math.max(z0, z1) - O) / C));
    for (let j = c; j < d; j++) for (let i = a; i < b; i++) grid[j * N + i] = id;
  });
  paint(NET.road, 1);
  if (era !== 'ancient') paint(NET.ringRoad, 1);
  paint(NET.pave, 2);
  const mats = [null, mat(p.road), mat(p.pave)], H = 0.06;
  // greedy: horizontal runs, then grow each run downwards while the rows below match
  const used = new Uint8Array(N * N);
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
    const id = grid[j * N + i]; if (!id || used[j * N + i]) continue;
    let w = 1; while (i + w < N && grid[j * N + i + w] === id && !used[j * N + i + w]) w++;
    let h = 1; grow: while (j + h < N) { for (let q = 0; q < w; q++) if (grid[(j + h) * N + i + q] !== id || used[(j + h) * N + i + q]) break grow; h++; }
    for (let r = 0; r < h; r++) for (let q = 0; q < w; q++) used[(j + r) * N + i + q] = 1;
    box(town, w * C, H, h * C, mats[id], O + (i + w / 2) * C, 0, O + (j + h / 2) * C);
  }
  // paving joints on the ceremonial plaza (just above the slab)
  const joint = mat(new THREE.Color(p.pave).multiplyScalar(0.9).getHex());
  for (let x = -12; x <= 12; x += 2) box(town, 0.05, 0.075, 14, joint, x, 0, 3);
  for (let z = -4; z <= 10; z += 2) box(town, 24, 0.075, 0.05, joint, 0, 0, z);
  // kerb lines where carriageway meets pavement
  const kerb = mat(new THREE.Color(p.pave).multiplyScalar(0.82).getHex());
  for (const z of [10, 14]) { box(town, 26.5, 0.08, 0.1, kerb, -17.25, 0, z); box(town, 26.5, 0.08, 0.1, kerb, 17.25, 0, z); }
  for (const x of [-3, 3]) box(town, 0.1, 0.08, 17, kerb, x, 0, 23);
  if (era === 'future') { for (const x of [-2.9, 2.9]) box(town, 0.12, 0.085, 17, glow(), x, 0, 23); for (const z of [10.1, 13.9]) box(town, 61, 0.085, 0.12, glow(), 0, 0, z); }
}

function house(k, g, era, X, Z, i) {
  const { p, mat, box, cyl, gable } = k, v = (i * 7919) % 5;
  const W = 4.6, D = 3.4;
  if (era === 'ancient') {
    box(g, W + 0.5, 0.35, D + 0.5, mat(p.stone), X, 0, Z);
    box(g, W, 1.9, D, mat(v % 2 ? p.plaster : 0xd9c7a4), X, 0.35, Z);
    for (const dx of [-1.6, -0.55, 0.55, 1.6]) box(g, 0.12, 1.9, 0.12, mat(p.wood), X + dx, 0.35, Z + D / 2 + 0.03);
    box(g, 0.9, 1.4, 0.05, mat(0x7a3b2a), X, 0.35, Z + D / 2 + 0.04);
    for (const dx of [-1.1, 1.1]) { box(g, 0.8, 0.6, 0.05, mat(0x5a3a2a), X + dx, 1.2, Z + D / 2 + 0.04); box(g, 0.8, 0.04, 0.06, mat(0xc9a24a), X + dx, 1.48, Z + D / 2 + 0.06); }
    gable(g, W, D, 1.15, 0.38, mat(p.roof), X, 2.25, Z);
    box(g, W + 0.9, 0.16, 0.24, mat(0x34383b), X, 3.34, Z);
    if (v % 3 === 0) { for (const dx of [-W / 2 - 0.1, W / 2 + 0.1]) box(g, 0.25, 1, 2.2, mat(p.wall), X + dx, 0, Z + D / 2 + 1.1); }
    return;
  }
  if (era === 'early') {
    const col = [p.wall, p.plaster, 0xb86b4a, 0xd8cdb4, 0x9e5a42][v];
    box(g, W + 0.3, 0.4, D + 0.3, mat(p.stone), X, 0, Z);
    box(g, W, 4, D, mat(col), X, 0.4, Z); k.cornice(g, W, D, 4.3, X, Z, mat(p.stone));
    gable(g, W, D, 1.2, 0.25, mat(p.roof), X, 4.4, Z);
    for (const r of [0, 1]) for (const dx of [-1.3, 1.3]) k.win(g, X + dx, 1 + r * 1.75, Z + D / 2 + 0.02, 0.7, 1.05);
    k.door(g, X, 0.4, Z + D / 2 + 0.02, 0.8, 1.5, 0x3d4a52);
    box(g, 0.5, 1.3, 0.5, mat(p.wall), X + 1.4, 5, Z - 0.6);
    return;
  }
  if (era === 'modern') {
    const H = [5.5, 8, 6.5, 10, 7][v], col = [p.wall, 0xe7e4dc, 0xcfccc4, 0xd9d2c4, 0xbfc4c8][v];
    box(g, W, H, D, mat(col), X, 0, Z);
    for (let f = 1; f * 1.6 < H - 0.6; f++) box(g, W + 0.04, 0.55, D + 0.04, k.glass(), X, f * 1.6 - 0.5, Z);
    box(g, W + 0.2, 0.3, D + 0.2, mat(0x9a9a96), X, H, Z); box(g, 1.2, 0.7, 1, mat(0xa9aaa6), X - 0.9, H + 0.3, Z - 0.4);
    k.door(g, X, 0, Z + D / 2 + 0.02, 1.1, 1.3, 0x2c3a44);
    return;
  }
  // future: round habitation pods with a glowing band
  const r = 1.8, H = [2.6, 3.4, 2.2, 4, 3][v];
  cyl(g, r + 0.3, r + 0.4, 0.3, mat(p.stone), X, 0, Z, 20);
  cyl(g, r, r, H, mat(p.wall), X, 0.3, Z, 20);
  k.add(g, new THREE.SphereGeometry(r, 20, 8, 0, Math.PI * 2, 0, Math.PI / 2), mat(p.wall), X, H + 0.3, Z);
  const band = k.add(g, new THREE.TorusGeometry(r + 0.03, 0.07, 4, 32), k.glow(), X, H * 0.65 + 0.3, Z); band.rotation.x = Math.PI / 2;
  box(g, 1, 1.6, 0.12, k.glass(), X, 0.3, Z + r - 0.02);
  if (v % 2) cyl(g, 0.04, 0.04, 1.4, mat(p.stone), X + 0.6, H + r * 0.7, Z, 6);
}

/** Build the whole town for an era. Returns { group, buildings: [{type, group, labelY}] }. */
export function buildTown(era, types) {
  const k = kit(era), { p, mat, box, glow } = k;
  const town = new THREE.Group();
  // ground, roads and plazas
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), mat(p.ground)); // floor of the box
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; town.add(ground);
  surfaces(k, town, era);
  // perimeter
  if (era === 'ancient') {
    const w = mat(p.wall), H = 3.2;
    box(town, 64, H, 1.4, w, 0, 0, -31); box(town, 1.4, H, 62, w, -32, 0, 0); box(town, 1.4, H, 62, w, 32, 0, 0);
    box(town, 28, H, 1.4, w, -18, 0, 31); box(town, 28, H, 1.4, w, 18, 0, 31);
    // battlements on the outer edge of the wall walk
    for (let x = -30.5; x <= 30.5; x += 1.6) { box(town, 0.8, 0.6, 0.35, w, x, H, -31.55); if (Math.abs(x) > 4.6) box(town, 0.8, 0.6, 0.35, w, x, H, 31.55); }
    for (let z = -29.5; z <= 29.5; z += 1.6) { box(town, 0.35, 0.6, 0.8, w, -32.55, H, z); box(town, 0.35, 0.6, 0.8, w, 32.55, H, z); }
    // south gate: twin blocks with a gate tower (an entrance, not a category)
    box(town, 3, 4.4, 4, w, -3.4, 0, 31); box(town, 3, 4.4, 4, w, 3.4, 0, 31); box(town, 3.8, 1.2, 4, w, 0, 3.2, 31);
    box(town, 9, 2, 3.2, mat(p.plaster), 0, 4.4, 31); k.curvedHip(town, 9, 3.2, 1.6, 0.8, mat(p.roof), 0, 6.4, 31, 0.15);
    { const lg = new THREE.Group(); town.add(lg); for (const x of [-3.2, -1, 1, 3.2]) k.lantern(lg, x, 6.3, 33.2); }
    for (const [x, z] of [[-32, -31], [32, -31], [-32, 31], [32, 31]]) { box(town, 3, 4.4, 3, w, x, 0, z); k.curvedHip(town, 3, 3, 1.2, 0.6, mat(p.roof), x, 4.4, z, 0.08); }
  } else {
    // entrance markers at the south end of the axis
    if (era === 'early') for (const sx of [-1, 1]) { box(town, 1.2, 4.5, 1.2, mat(p.stone), sx * 4.2, 0, 30); box(town, 1.6, 0.5, 1.6, mat(p.stone), sx * 4.2, 4.5, 30); }
    if (era === 'modern') box(town, 10, 0.3, 1.2, mat(p.wall), 0, 2.8, 30) && box(town, 0.4, 2.8, 1.2, mat(p.wall), -4.8, 0, 30) && box(town, 0.4, 2.8, 1.2, mat(p.wall), 4.8, 0, 30);
    if (era === 'future') { const a = k.add(town, new THREE.TorusGeometry(4.6, 0.18, 10, 64, Math.PI), glow(), 0, 0, 30); }
  }
  // street lamps (lit at night): one shared emissive head material per era
  const lampHead = new THREE.MeshStandardMaterial({ color: { ancient: 0xb23a2a, early: 0xf2d9a0, modern: 0xf4f4f0, future: p.glow }[era], emissive: { ancient: 0xff7a3d, early: 0xffc46b, modern: 0xfff3d6, future: p.glow }[era], emissiveIntensity: era === 'future' ? 0.6 : 0, roughness: 0.5 });
  const post = mat(era === 'ancient' ? p.wood : era === 'future' ? p.stone : 0x3a3a3c);
  const lampSpots = [];
  for (let x = -27; x <= 27; x += 6) if (Math.abs(x) > 4.5) lampSpots.push([x, 9.15], [x, 14.85]);
  for (let z = 18; z <= 30; z += 6) lampSpots.push([-3.85, z], [3.85, z]);
  for (const [x, z] of lampSpots) {
    if (era === 'ancient') { k.cyl(town, 0.07, 0.07, 2.2, post, x, 0, z, 6); box(town, 0.7, 0.07, 0.07, post, x + 0.3, 2.1, z); k.add(town, new THREE.SphereGeometry(0.24, 10, 8), lampHead, x + 0.6, 1.8, z); }
    else if (era === 'future') { k.cyl(town, 0.06, 0.06, 2.6, post, x, 0, z, 8); k.add(town, new THREE.CylinderGeometry(0.1, 0.1, 1.1, 8), lampHead, x, 2.9, z); }
    else { k.cyl(town, 0.06, 0.08, 3, post, x, 0, z, 8); k.add(town, new THREE.SphereGeometry(era === 'early' ? 0.26 : 0.2, 10, 8), lampHead, x, 3.15, z); }
  }
  // ---- urban fabric: rows of houses fill the blocks around the five category buildings ----
  const HOUSES = [];
  for (const sx of [-1, 1]) {
    for (const [x, z] of [[27, -27], [21.5, -27], [27, -20.5], [21.5, -20.5], [27, -14], [21.5, -14]]) HOUSES.push([sx * x, z]);   // north-west / north-east blocks
    for (const [x, z] of [[27.6, 18], [27.6, 24.5]]) HOUSES.push([sx * x, z]);                                                 // along the south walls
    for (const x of [6.2, 11.6]) HOUSES.push([sx * x, -27.6]);                                                                    // behind the landmark
  }
  HOUSES.forEach(([x, z], i) => house(k, town, era, x, z, i));
  trees(k, town, era, [[-14.2, -27, 0.8], [14.2, -27, 0.8], [-17.2, -12, 0.9], [17.2, -12, 0.9], [-13.2, -1.5, 0.8], [13.2, -1.5, 0.8], [-13.2, 7.4, 0.7], [13.2, 7.4, 0.7],
    [-6.5, 18.5, 0.8], [6.5, 18.5, 0.8], [-6.5, 24.5, 0.7], [6.5, 24.5, 0.7], [-22.6, 29.4, 0.8], [22.6, 29.4, 0.8], [-25.5, -11.6, 0.8], [25.5, -11.6, 0.8], [-3.6, -29, 0.7], [3.6, -29, 0.7]]);

  const buildings = [];
  const extras = [...PLOTS.extra];
  for (const t of types) {
    const plot = t.type === 'plot' ? extras.shift() : PLOTS[t.type] ?? extras.shift();
    if (!plot) continue;
    const g = new THREE.Group(); g.position.set(plot.x, 0, plot.z);
    const labelY = TYPES[t.type](k, g, era);
    bake(g, k.anims);
    g.traverse(o => { if (o.isMesh) o.userData.building = t.key; });
    town.add(g);
    buildings.push({ key: t.key, type: t.type, group: g, labelY, plot });
  }
  bake(town, k.anims, { band: 9, skip: new Set([ground]) });
  const glassMats = [];
  town.traverse(o => { if (o.material && o.material.metalness === 0.35 && !glassMats.includes(o.material)) glassMats.push(o.material); });
  return { group: town, buildings, palette: p, anims: k.anims, emitters: k.emitters, lampHead, glassMats };
}
