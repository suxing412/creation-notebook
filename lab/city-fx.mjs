// Ambient life for the overview town: smoke, clouds with moving shadows, birds, traffic, future sparks, click ripples.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const rand = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();

let puffTex = null;
function puffTexture() {
  if (puffTex) return puffTex;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  puffTex = new THREE.CanvasTexture(c); puffTex.colorSpace = THREE.SRGBColorSpace;
  return puffTex;
}

// Polyline helper: position + heading at distance s along a closed or open path.
function path(points, closed) {
  const pts = points.map(p => new THREE.Vector3(p[0], 0, p[1])), segs = [];
  let len = 0;
  for (let i = 0; i < pts.length - (closed ? 0 : 1); i++) { const a = pts[i], b = pts[(i + 1) % pts.length], l = a.distanceTo(b); segs.push({ a, b, l, s: len }); len += l; }
  return { len, closed, at(s, out) {
    s = closed ? ((s % len) + len) % len : Math.max(0, Math.min(len, s));
    const g = segs.find(q => s <= q.s + q.l) || segs[segs.length - 1];
    out.lerpVectors(g.a, g.b, (s - g.s) / g.l);
    return Math.atan2(g.b.x - g.a.x, g.b.z - g.a.z);
  } };
}

export function createFx(scene, era, town, { reduce = false } = {}) {
  const root = new THREE.Group(); scene.add(root);
  const updates = [], disposables = [];
  const keep = o => (disposables.push(o), o);
  const v = new THREE.Vector3();
  let ft = 0, mode = 'enter', m0 = 1e9, scatter = 0, birdsRoot = null, night = false, fwTimer = 3;
  const clamp01 = x => Math.max(0, Math.min(1, x));
  const outBack = x => { const c = 1.6; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  // 0 → 1 while entering (after `delay`), 1 → 0 while exiting; items exit faster than they enter
  const pres = (delay = 0, dur = 0.8) => mode === 'enter' ? clamp01((ft - m0 - delay) / dur) : mode === 'exit' ? 1 - clamp01((ft - m0 - delay * 0.35) / (dur * 0.6)) : 1;
  const EXIT_TOTAL = 1.7;

  // ---- smoke & sparks from emitters ----
  const puffs = [];
  const smokeMat = keep(new THREE.SpriteMaterial({ map: puffTexture(), color: era === 'early' ? 0x8e8a84 : 0xcfc8bb, transparent: true, depthWrite: false, opacity: 0 }));
  const sparkMat = keep(new THREE.SpriteMaterial({ map: puffTexture(), color: town.palette.glow, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0 }));
  const emitters = town.emitters.map(e => ({ ...e, acc: rand() }));
  updates.push((t, dt) => {
    const sp = pres(1.0, 0.4);
    for (const e of emitters) {
      if (sp < 1) { e.acc = 0; continue; }
      e.acc += dt;
      const every = e.kind === 'spark' ? 0.12 : 0.32;
      while (e.acc > every) {
        e.acc -= every;
        const s = new THREE.Sprite((e.kind === 'spark' ? sparkMat : smokeMat).clone());
        root.worldToLocal(e.obj.localToWorld(s.position.copy(e.local))); // root sits on the raised plate: keep puffs in its frame
        s.userData = { kind: e.kind, age: 0, life: e.kind === 'spark' ? 2.2 : 4.5, vx: (rand() - 0.5) * 0.6 + (e.kind === 'spark' ? 0 : 0.35), vz: (rand() - 0.5) * 0.6, vy: e.kind === 'spark' ? 1.6 + rand() : 1.1 + rand() * 0.4 };
        root.add(s); puffs.push(s);
      }
    }
    for (let i = puffs.length - 1; i >= 0; i--) {
      const s = puffs[i], u = s.userData; u.age += dt * (mode === 'exit' ? 3 : 1); const k = u.age / u.life;
      if (k >= 1) { root.remove(s); s.material.dispose(); puffs.splice(i, 1); continue; }
      s.position.x += u.vx * dt; s.position.y += u.vy * dt * (1 - k * 0.5); s.position.z += u.vz * dt;
      const sc = u.kind === 'spark' ? 0.35 * (1 - k) + 0.05 : 0.8 + k * 3.2; s.scale.setScalar(sc);
      s.material.opacity = (u.kind === 'spark' ? 0.9 : 0.55) * Math.sin(Math.min(1, k * 1.15) * Math.PI);
    }
  });

  // ---- clouds (their shadows drift across the town) ----
  if (era !== 'future') {
    const cloudMat = keep(new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, flatShading: true, transparent: true, opacity: 0.92 }));
    const geo = keep(new THREE.IcosahedronGeometry(1, 1));
    for (let i = 0; i < 7; i++) {
      const c = new THREE.Group();
      for (let j = 0; j < 5; j++) { const m = new THREE.Mesh(geo, cloudMat); m.position.set((j - 2) * 1.7 + rand(), rand() * 0.8, (rand() - 0.5) * 2); m.scale.set(1.8 + rand() * 1.4, 1 + rand() * 0.6, 1.5 + rand()); m.castShadow = true; c.add(m); }
      c.position.set(-70 + i * 22 + rand() * 8, 30 + rand() * 8, -40 + rand() * 70); c.userData.speed = 1 + rand() * 0.8; c.userData.y = c.position.y;
      root.add(c);
      updates.push((t, dt) => { const p = pres(0.1 + i * 0.12, 1.6); c.position.x += c.userData.speed * dt * (1 + (1 - p) * 3); if (c.position.x > 75) c.position.x = -75;
        c.position.y = c.userData.y + (1 - p) * 14; c.visible = p > 0.001; if (i === 0) cloudMat.opacity = 0.92 * Math.max(p, 0); });
    }
  }

  // ---- birds circling the landmark ----
  if (era === 'ancient' || era === 'early') {
    const wing = keep(new THREE.BufferGeometry()); wing.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 0.9, 0, -0.25, 0.25, 0, 0.35], 3)); wing.computeVertexNormals();
    const bm = keep(new THREE.MeshBasicMaterial({ color: 0x3b3833, side: THREE.DoubleSide }));
    for (let i = 0; i < 11; i++) {
      if (i === 0) birdsRoot = new THREE.Group(), root.add(birdsRoot);
      const b = new THREE.Group(), l = new THREE.Mesh(wing, bm), r = new THREE.Mesh(wing, bm); r.scale.x = -1; b.add(l, r); b.scale.setScalar(0.7 + rand() * 0.3); birdsRoot.add(b);
      const hit = new THREE.Mesh(keep(new THREE.SphereGeometry(1.6, 6, 4)), keep(new THREE.MeshBasicMaterial({ visible: false }))); b.add(hit);
      const R = 16 + rand() * 9, h = 15 + rand() * 6, w = 0.18 + rand() * 0.08, ph = rand() * Math.PI * 2;
      updates.push(t => { const p = pres(0.5 + i * 0.08, 2.0), q = p * p * (3 - 2 * p), sc = scatter * (0.6 + (i % 4) * 0.25), far = 1 + (1 - q) * 2.4 + sc * 1.4, a = t * w * (1 + sc * 2) + ph + sc * (i - 5) * 0.4;
        b.position.set(Math.cos(a) * R * far, h + (1 - q) * 26 + sc * 14 + Math.sin(t * 0.8 + ph) * 1.2, -12 + Math.sin(a) * R * 0.8 * far); b.rotation.y = -a; b.visible = p > 0.001;
        const f = Math.sin(t * (9 + (1 - q) * 6 + sc * 14) + ph) * 0.7; l.rotation.z = f; r.rotation.z = -f; });
    }
  }

  // ---- traffic ----
  // every lane is a closed loop (out along one side, back along the other), so nothing ever teleports
  const street = path([[-29.5, 11.1], [29.5, 11.1], [29.5, 12.9], [-29.5, 12.9]], true);
  const axis = path([[-1.2, 12.9], [-1.2, 30.5], [1.2, 30.5], [1.2, 11.1]], true);
  const lanes = [street, axis, street];
  if (era !== 'ancient') lanes.push(path([[-34.2, -34.2], [34.2, -34.2], [34.2, 34.2], [-34.2, 34.2]], true), path([[-32.8, 32.8], [32.8, 32.8], [32.8, -32.8], [-32.8, -32.8]], true));
  // ---- people and vehicles: one low-poly vocabulary for every era ----
  // Static parts of each figure are merged into one vertex-coloured mesh; only limbs and wheels move on their own.
  const VC = keep(new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.75 }));
  const GLOWV = keep(new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, emissive: town.palette.glow, emissiveIntensity: 1.4 }));
  const tmpM = new THREE.Matrix4(), tmpQ = new THREE.Quaternion(), tmpE = new THREE.Euler(), tmpS = new THREE.Vector3(), tmpP = new THREE.Vector3(), tmpC = new THREE.Color();
  // part(geometry, colour, [x,y,z], [rx,ry,rz], [sx,sy,sz])
  const part = (geo, color, p = [0, 0, 0], r = [0, 0, 0], sc = [1, 1, 1]) => {
    let g = geo.index ? geo.toNonIndexed() : geo.clone(); geo.dispose();
    for (const n of Object.keys(g.attributes)) if (n !== 'position' && n !== 'normal') g.deleteAttribute(n);
    tmpC.set(color); const c = new Float32Array(g.attributes.position.count * 3); for (let i = 0; i < c.length; i += 3) { c[i] = tmpC.r; c[i + 1] = tmpC.g; c[i + 2] = tmpC.b; }
    g.setAttribute('color', new THREE.BufferAttribute(c, 3));
    g.applyMatrix4(tmpM.compose(tmpP.set(...p), tmpQ.setFromEuler(tmpE.set(...r)), tmpS.set(...sc)));
    return g;
  };
  const mesh = (parts, m = VC) => { const g = keep(mergeGeometries(parts)); parts.forEach(q => q.dispose()); const o = new THREE.Mesh(g, m); o.castShadow = true; return o; };
  const B = (w, h, d) => new THREE.BoxGeometry(w, h, d), C = (rt, rb, h, n = 8) => new THREE.CylinderGeometry(rt, rb, h, n), S = (r, d = 0) => new THREE.IcosahedronGeometry(r, d);
  const pick = a => a[Math.floor(rand() * a.length)];
  const SKIN = [0xe8c4a0, 0xd9a77e, 0xc48b62, 0xf0d2b4];
  const OUTFIT = {
    ancient: { top: [0x9c3b2b, 0x3f5a6e, 0x7a6a3a, 0xd8cdb4, 0x55674f], low: [0x3b3228, 0x5a4a3a] },
    early: { top: [0x2b2f3a, 0x4a3b30, 0x6b6f72, 0x3c4a3a, 0x7b3a2a], low: [0x22252b, 0x3a332c] },
    modern: { top: [0xe9e6df, 0xd9b44a, 0x3c6e8f, 0xb2362b, 0x6b8f6a, 0x2c2e31], low: [0x34465e, 0x2c2e31, 0x8a7d6a] },
    future: { top: [0xf2f5f8, 0xdde5ec, 0xb9c4cd], low: [0xe3e9ee, 0xcfd6dc] },
  }[era];

  function person() {
    const g = new THREE.Group(), top = pick(OUTFIT.top), low = pick(OUTFIT.low), skin = pick(SKIN);
    const body = [part(B(0.34, 0.4, 0.2), top, [0, 0.62, 0]), part(S(0.13), skin, [0, 0.98, 0]), part(B(0.36, 0.06, 0.22), low, [0, 0.43, 0])];
    if (era === 'ancient') body.push(part(C(0.17, 0.27, 0.42, 8), top, [0, 0.3, 0]), part(B(0.1, 0.12, 0.1), 0x2b2622, [0, 1.13, -0.02]), part(B(0.36, 0.04, 0.24), 0xc9a24a, [0, 0.5, 0]));
    if (era === 'early') body.push(part(C(0.18, 0.18, 0.025, 10), 0x22252b, [0, 1.06, 0]), part(C(0.11, 0.12, 0.14, 10), 0x22252b, [0, 1.13, 0]), part(B(0.06, 0.18, 0.21), 0xf2efe6, [0, 0.72, 0]));
    if (era === 'modern') body.push(part(B(0.3, 0.26, 0.12), pick([0xd9b44a, 0x2c2e31, 0xb2362b]), [0, 0.66, -0.15]), part(S(0.135), 0x3b3228, [0, 1.03, -0.02], [0, 0, 0], [1, 0.6, 1]));
    if (era === 'future') body.push(part(B(0.36, 0.05, 0.22), town.palette.glow, [0, 0.66, 0]), part(B(0.22, 0.07, 0.04), 0x1b2a36, [0, 1.0, 0.12]));
    const torso = mesh(body); g.add(torso);
    const limb = (geo, color, x, y) => { const piv = new THREE.Group(); piv.position.set(x, y, 0); const l = mesh([part(geo, color, [0, -geo.parameters.height / 2, 0])]); piv.add(l); g.add(piv); return piv; };
    const legC = era === 'ancient' ? 0x2b2622 : low, armC = era === 'future' ? 0xe3e9ee : top;
    const L = limb(B(0.11, 0.42, 0.12), legC, -0.08, 0.43), R = limb(B(0.11, 0.42, 0.12), legC, 0.08, 0.43);
    const AL = limb(B(0.08, 0.36, 0.09), armC, -0.22, 0.8), AR = limb(B(0.08, 0.36, 0.09), armC, 0.22, 0.8);
    let ph = rand() * 6;
    g.userData = { walk: true, kind: 'person', animate(dist, dt, held, t) {
      ph += dist * 6.5; const sw = held ? Math.sin(t * 16) * 0.9 : Math.sin(ph) * 0.55 * Math.min(1, dist / (dt || 1) / 1.2 + 0.0001);
      L.rotation.x = sw; R.rotation.x = -sw; AL.rotation.x = -sw * 0.8; AR.rotation.x = sw * 0.8;
      if (held) { AL.rotation.z = -1.2 - Math.sin(t * 9) * 0.4; AR.rotation.z = 1.2 + Math.sin(t * 9) * 0.4; } else { AL.rotation.z = AR.rotation.z = 0; }
    } };
    return g;
  }

  // wheels on an axle (one mesh per axle) so they can spin
  const axle = (r, track, color = 0x24262a, hub = 0xbfb8a8) => mesh([
    part(C(r, r, 0.14, 10), color, [-track / 2, 0, 0], [0, 0, Math.PI / 2]), part(C(r, r, 0.14, 10), color, [track / 2, 0, 0], [0, 0, Math.PI / 2]),
    part(C(r * 0.45, r * 0.45, 0.16, 8), hub, [-track / 2, 0, 0], [0, 0, Math.PI / 2]), part(C(r * 0.45, r * 0.45, 0.16, 8), hub, [track / 2, 0, 0], [0, 0, Math.PI / 2])]);
  function vehicle(kind) {
    const g = new THREE.Group(), axles = [], legs = [];
    let r = 0.22;
    if (kind === 'oxcart') {
      r = 0.42;
      g.add(mesh([part(B(0.95, 0.12, 1.3), 0x7a5a3c, [0, 0.62, -0.3]), part(B(0.06, 0.3, 1.3), 0x6a4a32, [-0.46, 0.8, -0.3]), part(B(0.06, 0.3, 1.3), 0x6a4a32, [0.46, 0.8, -0.3]),
        part(B(0.7, 0.35, 0.8), pick([0xc9a24a, 0x8a9a4b, 0xd8cdb4]), [0, 0.86, -0.35]), part(B(0.05, 0.05, 1.4), 0x5a3f2a, [-0.2, 0.62, 0.9]), part(B(0.05, 0.05, 1.4), 0x5a3f2a, [0.2, 0.62, 0.9]),
        part(B(0.5, 0.42, 0.95), 0x5b4636, [0, 0.72, 1.75]), part(B(0.3, 0.3, 0.34), 0x4b3a2c, [0, 0.82, 2.35]), part(B(0.5, 0.05, 0.05), 0xe7dcc6, [0, 1.0, 2.3], [0, 0, 0]), part(B(0.07, 0.07, 0.3), 0x2b2622, [0, 0.98, 0.95])]));
      for (const [x, z] of [[-0.17, 1.4], [0.17, 1.4], [-0.17, 2.1], [0.17, 2.1]]) { const piv = new THREE.Group(); piv.position.set(x, 0.55, z); piv.add(mesh([part(B(0.1, 0.5, 0.1), 0x4b3a2c, [0, -0.25, 0])])); g.add(piv); legs.push(piv); }
      const a = axle(r, 1.08, 0x5a3f2a, 0x8a6a4a); a.position.set(0, r, -0.4); g.add(a); axles.push(a);
    } else if (kind === 'vintage') {
      const col = pick([0x2f3a36, 0x5a2b24, 0x2b2f3a, 0x6b5a3a, 0x1f2a3a]); r = 0.26;
      g.add(mesh([part(B(0.86, 0.36, 1.9), col, [0, 0.46, 0]), part(B(0.8, 0.42, 0.9), col, [0, 0.85, -0.25]), part(B(0.72, 0.3, 0.86), 0x9fb2bd, [0, 0.88, -0.25]),
        part(B(0.96, 0.08, 0.5), 0x24262a, [0, 0.36, 0.72]), part(B(0.96, 0.08, 0.5), 0x24262a, [0, 0.36, -0.72]), part(S(0.09), 0xffe7a8, [-0.3, 0.52, 0.96]), part(S(0.09), 0xffe7a8, [0.3, 0.52, 0.96]),
        part(C(0.2, 0.2, 0.1, 10), 0x24262a, [0, 0.6, -1.0], [Math.PI / 2, 0, 0]), part(B(0.5, 0.18, 0.06), 0xbfb8a8, [0, 0.46, 0.96])]));
      for (const z of [0.62, -0.62]) { const a = axle(r, 0.92); a.position.set(0, r, z); g.add(a); axles.push(a); }
    } else if (kind === 'sedan' || kind === 'bus') {
      const bus = kind === 'bus', col = bus ? pick([0xd9b44a, 0x3c6e8f, 0xb2362b]) : pick([0xf2f1ec, 0x2c2e31, 0xb2362b, 0x3c6e8f, 0xd9b44a, 0x9aa0a6]); r = bus ? 0.3 : 0.22;
      const L = bus ? 4.2 : 1.9, H = bus ? 1.2 : 0.38;
      const parts = [part(B(0.9, H, L), col, [0, r + H / 2 + 0.05, 0]), part(B(0.92, 0.04, L + 0.02), 0x24262a, [0, r + 0.08, 0]),
        part(B(0.06, 0.06, 0.06), 0xfff3d6, [-0.32, r + 0.3, L / 2]), part(B(0.06, 0.06, 0.06), 0xfff3d6, [0.32, r + 0.3, L / 2]), part(B(0.06, 0.06, 0.04), 0xd8352b, [-0.32, r + 0.3, -L / 2]), part(B(0.06, 0.06, 0.04), 0xd8352b, [0.32, r + 0.3, -L / 2])];
      if (bus) parts.push(part(B(0.92, 0.42, L - 0.5), 0x7f99a8, [0, r + 0.9, 0.1]), part(B(0.92, 0.1, L), 0xf2f1ec, [0, r + 1.27, 0]));
      else parts.push(part(B(0.8, 0.34, 1.0), col, [0, r + 0.6, -0.12]), part(B(0.82, 0.24, 0.94), 0x7f99a8, [0, r + 0.6, -0.12]));
      g.add(mesh(parts));
      for (const z of bus ? [1.4, -1.4] : [0.62, -0.62]) { const a = axle(r, 0.86); a.position.set(0, r, z); g.add(a); axles.push(a); }
    } else { // pod
      g.add(mesh([part(new THREE.CapsuleGeometry(0.42, 1.1, 3, 8), 0xf4f6f8, [0, 0, 0], [Math.PI / 2, 0, 0]), part(S(0.36, 1), 0x9cc8dc, [0, 0.26, 0.2], [0, 0, 0], [1, 0.7, 1.4]),
        part(B(0.05, 0.36, 0.5), 0xdde5ec, [0, 0.42, -0.6], [0.4, 0, 0]), part(B(0.9, 0.04, 0.4), 0xdde5ec, [0, 0, -0.55])]));
      const glow = mesh([part(B(0.7, 0.05, 1.2), 0xffffff, [0, -0.4, 0]), part(S(0.1), 0xffffff, [-0.25, -0.02, -0.85]), part(S(0.1), 0xffffff, [0.25, -0.02, -0.85])], GLOWV); glow.castShadow = false; g.add(glow);
      g.userData.thruster = glow;
    }
    let roll = 0;
    g.userData = { ...g.userData, hover: kind === 'pod', kind: kind === 'pod' ? 'pod' : kind === 'oxcart' ? 'cart' : 'car', animate(dist, dt, held, t) {
      roll += dist / r; axles.forEach(a => { a.rotation.x = held ? t * 12 : roll; });
      legs.forEach((l, i) => { l.rotation.x = Math.sin(roll * 1.6 + (i % 2 ? Math.PI : 0) + (i > 1 ? Math.PI / 2 : 0)) * 0.45; });
      if (g.userData.thruster) g.userData.thruster.scale.y = 1 + Math.sin(t * 20) * 0.3;
    } };
    return g;
  }

  // who walks and what drives, per era (people keep to the pavements, vehicles to the carriageway)
  const crowd = {
    ancient: { people: 7, vehicles: ['oxcart', 'oxcart', 'oxcart', 'oxcart'], speed: [1.3, 2] },
    early: { people: 6, vehicles: ['vintage', 'vintage', 'vintage', 'vintage', 'vintage', 'vintage', 'vintage'], speed: [4, 6] },
    modern: { people: 7, vehicles: ['sedan', 'sedan', 'sedan', 'bus', 'sedan', 'sedan', 'sedan', 'sedan', 'bus', 'sedan'], speed: [6, 9] },
    future: { people: 6, vehicles: ['pod', 'pod', 'pod', 'pod', 'pod', 'pod', 'pod', 'pod', 'pod'], speed: [7, 11] },
  }[era];
  const pavement = [path([[-29.5, 9.5], [29.5, 9.5], [29.5, 14.5], [-29.5, 14.5]], true), path([[-3.5, 14.5], [-3.5, 29.4], [3.5, 29.4], [3.5, 14.5]], true)];
  const roster = [...Array.from({ length: crowd.people }, () => ({ make: person, lanes: pavement, speed: [1.1, 1.8] })),
    ...crowd.vehicles.map(v => ({ make: () => vehicle(v), lanes, speed: v === 'bus' ? [4.5, 5.5] : crowd.speed }))];
  const spec = { n: roster.length };

  const movers = [];
  for (let i = 0; i < spec.n; i++) {
    const R = roster[i], lane = R.lanes[i % R.lanes.length], o = R.make(), sp = R.speed[0] + rand() * (R.speed[1] - R.speed[0]);
    const m = { o, lane, s: rand() * lane.len, sp, ph: rand() * 10, mode: 'path', hold: new THREE.Vector3(), vy: 0, boost: 0, jump: 0, px: 0, pz: 0, kind: o.userData.kind };
    o.traverse(n => { n.userData.mover = m; }); root.add(o); movers.push(m);
    const tmp = new THREE.Vector3();
    updates.push((t, dt) => {
      const p = pres(0.9 + i * 0.07, 0.7);
      m.boost = Math.max(0, m.boost - dt * 0.6); m.jump = Math.max(0, m.jump - dt * 1.6);
      if (m.mode === 'path') {
        m.s += m.sp * (1 + m.boost * 2.5) * dt;
        if (!lane.closed && m.s > lane.len) m.s = 0;
        o.rotation.y = lane.at(m.s, o.position); o.rotation.z = 0;
      } else if (m.mode === 'held') {
        o.position.lerp(m.hold, Math.min(1, dt * 14)); o.rotation.z = Math.sin(t * 12 + m.ph) * 0.35; o.rotation.y += dt * 1.5;
      } else if (m.mode === 'drop') {
        m.vy -= 30 * dt; o.position.y += m.vy * dt; o.rotation.z *= 0.9;
        if (o.position.y <= 0) { o.position.y = 0; if (Math.abs(m.vy) > 3) m.vy = -m.vy * 0.38; else { m.vy = 0; m.mode = 'return'; } }
      } else if (m.mode === 'return') { // walk / drive back to where it left the lane
        lane.at(m.s, tmp); const dx = tmp.x - o.position.x, dz = tmp.z - o.position.z, dd = Math.hypot(dx, dz);
        if (dd < 0.15) m.mode = 'path'; else { const st = Math.min(dd, (m.sp * 0.8 + 1) * dt); o.position.x += dx / dd * st; o.position.z += dz / dd * st; o.rotation.y = Math.atan2(dx, dz); }
      }
      const moved = Math.hypot(o.position.x - m.px, o.position.z - m.pz); m.px = o.position.x; m.pz = o.position.z;
      o.userData.animate?.(moved < 2 ? moved : 0, dt, m.mode === 'held', t);
      const free = m.mode === 'path' || m.mode === 'return';
      if (free) {
        if (o.userData.hover) o.position.y = 1.1 + Math.sin(t * 2 + m.ph) * 0.15;
        else if (o.userData.walk) o.position.y = Math.abs(Math.sin(t * 7 + m.ph)) * 0.06;
        else o.position.y = 0;
        o.position.y += Math.sin(Math.min(1, 1 - m.jump) * Math.PI) * (m.jump > 0 ? 1.2 : 0);
      }
      o.scale.setScalar(Math.max(0.001, mode === 'enter' ? outBack(p) : p) * (m.mode === 'held' ? 1.15 : 1));
      if (free) o.position.y += mode === 'enter' ? (1 - p) * 4 : -(1 - p) * 1.2;
      o.visible = p > 0.001;
    });
  }

  // ---- fireworks ----
  const bursts = [];
  const FW = { ancient: [0xff5a3c, 0xffc65c, 0xff8fb1], early: [0xffd27a, 0xff6b5b, 0xffffff], modern: [0xffffff, 0x6ec6ff, 0xffd166], future: [0x52d0ff, 0xb388ff, 0x7dffcf] }[era];
  function firework(at) {
    const N = 90, pos = new Float32Array(N * 3), vel = [];
    const c = FW[Math.floor(rand() * FW.length)];
    for (let j = 0; j < N; j++) { pos.set([at.x, at.y, at.z], j * 3); const u = rand() * 2 - 1, th = rand() * Math.PI * 2, r = Math.sqrt(1 - u * u), spd = 7 + rand() * 4; vel.push([r * Math.cos(th) * spd, u * spd, r * Math.sin(th) * spd]); }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const pts = new THREE.Points(geo, new THREE.PointsMaterial({ color: c, size: 0.6, map: puffTexture(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
    root.add(pts); bursts.push({ pts, vel, age: 0, rocket: null });
  }
  function launch(from) {
    const rk = new THREE.Sprite(sparkMat.clone()); rk.material.opacity = 1; rk.scale.setScalar(0.5); rk.position.copy(from); root.add(rk);
    bursts.push({ rocket: rk, vy: 22 + rand() * 6, vx: (rand() - 0.5) * 3, age: 0 });
  }
  updates.push((t, dt) => {
    if (night && mode !== 'exit') { fwTimer -= dt; if (fwTimer < 0) { fwTimer = 2.5 + rand() * 4; launch(new THREE.Vector3((rand() - 0.5) * 30, 2, -14 + (rand() - 0.5) * 20)); } }
    for (let i = bursts.length - 1; i >= 0; i--) {
      const b = bursts[i]; b.age += dt;
      if (b.rocket) { b.vy -= 14 * dt; b.rocket.position.y += b.vy * dt; b.rocket.position.x += b.vx * dt; if (b.vy < 3) { firework(b.rocket.position); root.remove(b.rocket); b.rocket.material.dispose(); bursts.splice(i, 1); } continue; }
      const k = b.age / 2.4; if (k >= 1) { root.remove(b.pts); b.pts.geometry.dispose(); b.pts.material.dispose(); bursts.splice(i, 1); continue; }
      const a = b.pts.geometry.attributes.position.array;
      b.vel.forEach((v, j) => { v[1] -= 6 * dt; v[0] *= 0.985; v[1] *= 0.985; v[2] *= 0.985; a[j * 3] += v[0] * dt; a[j * 3 + 1] += v[1] * dt; a[j * 3 + 2] += v[2] * dt; });
      b.pts.geometry.attributes.position.needsUpdate = true; b.pts.material.opacity = 1 - k * k; b.pts.material.size = 0.6 * (1 - k * 0.5);
    }
  });

  // ---- future: floating light motes ----
  if (era === 'future') {
    const N = 360, pos = new Float32Array(N * 3), sp = new Float32Array(N);
    for (let i = 0; i < N; i++) { pos[i * 3] = (rand() - 0.5) * 80; pos[i * 3 + 1] = rand() * 22; pos[i * 3 + 2] = (rand() - 0.5) * 80; sp[i] = 0.4 + rand() * 0.9; }
    const geo = keep(new THREE.BufferGeometry()); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const pts = new THREE.Points(geo, keep(new THREE.PointsMaterial({ color: town.palette.glow, size: 0.28, map: puffTexture(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.85 })));
    root.add(pts);
    updates.push(() => { const p = pres(0.4, 1.8); pts.material.opacity = 0.85 * p; pts.visible = p > 0.001; });
    updates.push((t, dt) => { for (let i = 0; i < N; i++) { pos[i * 3 + 1] += sp[i] * dt; pos[i * 3] += Math.sin(t * 0.5 + i) * dt * 0.2; if (pos[i * 3 + 1] > 24) pos[i * 3 + 1] = 0; } geo.attributes.position.needsUpdate = true; });
  }

  // ---- night sky: twinkling stars on a dome ----
  {
    const N = 420, pos = new Float32Array(N * 3), tw = new Float32Array(N);
    for (let i = 0; i < N; i++) { const a = rand() * Math.PI * 2, e = 0.12 + rand() * 1.35, R = 160; pos.set([Math.cos(a) * Math.cos(e) * R, Math.sin(e) * R * 0.8 + 10, Math.sin(a) * Math.cos(e) * R], i * 3); tw[i] = rand() * 10; }
    const geo = keep(new THREE.BufferGeometry()); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const sm = keep(new THREE.PointsMaterial({ color: 0xfff6e0, size: 1.6, map: puffTexture(), transparent: true, depthWrite: false, opacity: 0, sizeAttenuation: true, fog: false }));
    const stars = new THREE.Points(geo, sm); root.add(stars);
    let nk = 0;
    updates.push((t, dt) => { nk += ((night ? 1 : 0) - nk) * Math.min(1, dt * 1.5); sm.opacity = nk * 0.9 * pres(0, 1) * (0.85 + Math.sin(t * 2.3) * 0.15); stars.visible = sm.opacity > 0.01; stars.rotation.y = t * 0.004; });
  }

  // ---- ancient: drifting leaves ----
  if (era === 'ancient' || era === 'early') {
    const N = era === 'ancient' ? 70 : 36, lg = keep(new THREE.PlaneGeometry(0.28, 0.18));
    const lms = [0xc9772f, 0xd9a441, 0x8a9a4b].map(c => keep(new THREE.MeshStandardMaterial({ color: c, side: THREE.DoubleSide, roughness: 0.9 })));
    const leaves = [];
    for (let i = 0; i < N; i++) { const m = new THREE.Mesh(lg, lms[i % 3]); m.position.set((rand() - 0.5) * 70, rand() * 18, (rand() - 0.5) * 70); m.userData = { sp: 0.6 + rand() * 0.8, ph: rand() * 10, spin: 1 + rand() * 3 }; root.add(m); leaves.push(m); }
    updates.push((t, dt) => { const p = pres(0.5, 1.5); for (const m of leaves) { const u = m.userData; m.position.y -= u.sp * dt; m.position.x += (Math.sin(t * 0.8 + u.ph) * 0.8 + 0.9) * dt; m.position.z += Math.cos(t * 0.6 + u.ph) * 0.5 * dt;
      m.rotation.set(t * u.spin + u.ph, t * u.spin * 0.7, Math.sin(t + u.ph)); if (m.position.y < 0.05) { m.position.y = 16 + rand() * 6; m.position.x = (rand() - 0.5) * 70 - 10; } m.visible = p > 0.01; m.scale.setScalar(Math.max(0.001, p)); } });
  }

  // ---- modern: a helicopter circling the tower ----
  if (era === 'modern') {
    const h = new THREE.Group(), body = keep(new THREE.MeshStandardMaterial({ color: 0xb2362b, roughness: 0.4, metalness: 0.2 })), dark = keep(new THREE.MeshStandardMaterial({ color: 0x2c2e31 }));
    const cab = new THREE.Mesh(keep(new THREE.SphereGeometry(0.9, 14, 10)), body); cab.scale.set(1, 0.8, 1.5); cab.castShadow = true;
    const tail = new THREE.Mesh(keep(new THREE.BoxGeometry(0.18, 0.18, 2.4)), body); tail.position.z = -1.9;
    const rotor = new THREE.Group(); rotor.position.y = 0.95; for (let i = 0; i < 2; i++) { const b = new THREE.Mesh(keep(new THREE.BoxGeometry(5, 0.04, 0.22)), dark); b.rotation.y = i * Math.PI / 2; rotor.add(b); }
    const tr = new THREE.Mesh(keep(new THREE.BoxGeometry(0.04, 1, 0.12)), dark); tr.position.set(0.12, 0, -3.1);
    const blink = keep(new THREE.MeshStandardMaterial({ color: 0xff3b2f, emissive: 0xff2a1a, emissiveIntensity: 0 })), bl = new THREE.Mesh(keep(new THREE.SphereGeometry(0.1, 6, 4)), blink); bl.position.set(0, -0.7, 0);
    h.add(cab, tail, rotor, tr, bl); root.add(h);
    updates.push(t => { const p = pres(1.4, 2), a = t * 0.22; h.position.set(Math.cos(a) * 26, 22 + Math.sin(t * 0.7) * 1.5 + (1 - p) * 40, -12 + Math.sin(a) * 20); h.rotation.y = -a; h.rotation.z = -0.12; rotor.rotation.y = t * 28; tr.rotation.x = t * 30; blink.emissiveIntensity = (t % 1.2) < 0.15 ? 3 : 0; h.visible = p > 0.01; });
  }

  // ---- future: a drone swarm weaving above the town ----
  if (era === 'future') {
    const N = 22, dm = keep(new THREE.MeshStandardMaterial({ color: 0xf4f6f8, roughness: 0.3, metalness: 0.4 })), gm = keep(new THREE.MeshBasicMaterial({ color: town.palette.glow }));
    const dg = keep(new THREE.OctahedronGeometry(0.32, 0)), lgeo = keep(new THREE.SphereGeometry(0.1, 6, 4));
    const drones = [];
    for (let i = 0; i < N; i++) { const d = new THREE.Group(), b = new THREE.Mesh(dg, dm), l = new THREE.Mesh(lgeo, gm); b.scale.y = 0.5; l.position.y = -0.18; d.add(b, l); root.add(d); drones.push({ d, ph: i / N * Math.PI * 2, r: 10 + (i % 3) * 3, y: 12 + (i % 5) * 1.2 }); }
    updates.push(t => { const p = pres(1.2, 1.8); for (const q of drones) { const a = t * 0.35 + q.ph, w = Math.sin(t * 0.5 + q.ph * 3) * 3;
      q.d.position.set(-21 + Math.cos(a) * (q.r + w), q.y + Math.sin(t * 1.3 + q.ph * 2) * 1.2 + (1 - p) * 30, 5 + Math.sin(a * 2) * (q.r * 0.6)); q.d.rotation.y = t * 2; q.d.visible = p > 0.01; } });
  }

  // ---- click ripples ----
  const ripples = [];
  const rippleGeo = keep(new THREE.RingGeometry(0.9, 1, 64));
  function ripple(point, color = 0xa63a2b) {
    const m = new THREE.Mesh(rippleGeo, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.8, depthWrite: false, side: THREE.DoubleSide }));
    m.rotation.x = -Math.PI / 2; m.position.copy(point).y = 0.12; root.add(m); ripples.push({ m, age: 0 });
  }
  updates.push((t, dt) => { for (let i = ripples.length - 1; i >= 0; i--) { const r = ripples[i]; r.age += dt; const k = r.age / 1.2; if (k >= 1) { root.remove(r.m); r.m.material.dispose(); ripples.splice(i, 1); continue; } r.m.scale.setScalar(0.5 + k * 6); r.m.material.opacity = 0.8 * (1 - k); } });

  return {
    enter(delay = 0) { mode = 'enter'; m0 = ft + delay; if (reduce) mode = 'idle'; },
    exit() { mode = 'exit'; m0 = ft; return reduce ? 0 : EXIT_TOTAL; },
    get done() { return mode === 'exit' && (reduce || ft - m0 > EXIT_TOTAL + 0.2); },
    update(t, dt) { ft += dt; scatter = Math.max(0, scatter - dt * 0.22); if (reduce) return; for (const f of town.anims) f(t, dt); for (const f of updates) f(t, dt); },
    ripple,
    /** Movers and birds the pointer can grab or poke. */
    pickables() { return [...movers.map(m => m.o), ...(birdsRoot ? [birdsRoot] : [])]; },
    moverOf(obj) { return obj?.userData?.mover ?? null; },
    isBird(obj) { let n = obj; while (n) { if (n === birdsRoot) return true; n = n.parent; } return false; },
    grab(m) { m.mode = 'held'; m.hold.copy(m.o.position).y = 2.4; },
    carry(m, point) { m.hold.set(point.x, 2.4, point.z); },
    drop(m) { m.mode = 'drop'; m.vy = 0; },
    poke(m) { m.jump = 1; m.boost = m.kind === 'person' ? 0.3 : 1; return m.kind; },
    scatter() { scatter = 1; },
    firework(at) { launch(at.clone()); setTimeout(() => launch(at.clone().add(new THREE.Vector3(3, 0, -2))), 260); setTimeout(() => launch(at.clone().add(new THREE.Vector3(-3, 0, 1))), 520); },
    setNight(n) { night = n; fwTimer = 1.5; },
    setOpacity(a) { root.traverse(o => { if (o.material && 'opacity' in o.material && !o.isSprite) { o.material.transparent = true; o.material.opacity = Math.min(o.material.userData.base ??= o.material.opacity, a * (o.material.userData.base)); } }); },
    dispose() { scene.remove(root); puffs.forEach(s => s.material.dispose()); ripples.forEach(r => r.m.material.dispose()); disposables.forEach(o => o.dispose?.()); },
  };
}
