// 3D overview as a small town. Each category tab is a building.
// - Default overview view; left-drag orbits and the wheel dollies around the town centre (no pan, no auto-rotate).
// - People and vehicles can be picked up and dropped; click them for a line of dialogue; click birds to scatter them;
//   double-click the landmark for fireworks; the day/night switch lights lamps and windows.
// - Click a building: the camera pushes in, then the page fades in an overview card (onZone).
//   Deselect: the camera always returns to the default overview view.
// - Era switch: the old town sinks ring by ring, the new one rises. Ambient life lives in city-fx.mjs.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { esc } from './lib.js';
import { ERAS, TYPOLOGY, TYPOLOGY_ZH, BUILDING_NAME, buildTown, palette, nightGlow } from './city-kit.mjs';
import { createFx } from './city-fx.mjs';

const inOut = t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const outBack = t => { const c = 1.4; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
const inCubic = t => t * t * t;
const CENTER = new THREE.Vector3(0, 0, 1);
const PLATE_Y = 17.4; // town floor on the wooden stand, ~5 below the box rim (the town sits inside the box)

export async function mountOverview(root, d, { onZone, onEra, onTime, onBusy, era: era0 = 'ancient', tod: tod0 = 0.5 } = {}) {
  let switching = false, boxStyle = null, dressSwap = null, dressTick = null; // an era transition is playing: further switches are refused until it settles
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const host = root.querySelector('.ov-canvas');
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.setAttribute('aria-hidden', 'true');
  host.append(renderer.domElement);
  const el = renderer.domElement;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environment = envTex; scene.environmentIntensity = 0.55;
  const sun = new THREE.DirectionalLight(0xfffaf2, 2.0);
  sun.position.set(-30, 48, 34); sun.target.position.set(0, 0, 0);
  sun.castShadow = true; sun.shadow.mapSize.set(4096, 4096); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.04;
  Object.assign(sun.shadow.camera, { left: -62, right: 62, top: 62, bottom: -62, near: 1, far: 190 }); sun.shadow.camera.updateProjectionMatrix();
  const hemi = new THREE.HemisphereLight(0xffffff, 0xcfc6b4, 0.35);
  scene.add(sun, sun.target, hemi);
  const pools = [[-8, 6], [8, 6], [0, 18], [0, -2]].map(([x, z]) => { const l = new THREE.PointLight(0xffb56b, 0, 26, 1.6); l.position.set(x, 4 + PLATE_Y, z); scene.add(l); return l; });

  const cats = d.categories.map(c => ({ c, n: d.assets.filter(a => a.category === c.id).length, type: TYPOLOGY[c.id] ?? 'plot' }));
  const types = [...cats.map(x => ({ key: x.c.id, type: x.type })), { key: '__reserve', type: 'plot' }];

  // ---- camera: orbit pivots on the town centre ----
  const camera = new THREE.PerspectiveCamera(30, 1, 0.5, 700);
  const controls = new OrbitControls(camera, el);
  controls.enableDamping = true; controls.dampingFactor = 0.08; controls.enableZoom = true; controls.zoomSpeed = 0.7; controls.enablePan = false;
  controls.minPolarAngle = 0.35; controls.maxPolarAngle = 1.5; // low enough to look under the floating island controls.rotateSpeed = 0.6;
  controls.addEventListener('start', () => { if (fly && active < 0) { fly = null; limits(); } });
  const tanH = () => Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  const fit = r => r / tanH() / Math.min(1, camera.aspect);
  const HOME_DIR = new THREE.Vector3(-0.4, 0.52, 1).normalize(); // lower, more frontal default view
  let home, active = -1, fly = null, pendingZone = null, town = null, fx = null, era = era0, basePos = [];
  const fading = []; // ambient layers of the previous era, still playing their exit
  // time of day: 0 midnight, .25 sunrise, .5 noon, .75 sunset. One full day lasts DAY seconds.
  const DAY = 180;
  let tod = tod0, nightK = 0, warm = 0, ffTarget = null, nightFlag = null;
  const sunCol = new THREE.Color(), hemiSky = new THREE.Color(), hemiGround = new THREE.Color();
  const applyNight = k => {
    if (town) { town.lampHead.emissiveIntensity = (era === 'future' ? 0.6 : 0) + k * 2.4; town.glassMats.forEach(m => { m.emissive.setHex(0xffc98a); m.emissiveIntensity = k * 0.9; }); }
    pools.forEach(l => { l.intensity = 34 * k; }); nightGlow.v = k;
  };
  const applyTime = () => {
    const th = (tod - 0.25) * Math.PI * 2, elev = Math.sin(th);
    nightK = THREE.MathUtils.clamp((0.1 - elev) / 0.3, 0, 1);
    warm = elev > -0.3 ? THREE.MathUtils.clamp(1 - Math.abs(elev - 0.02) / 0.3, 0, 1) : 0;
    const day = nightK < 1, a = day ? th : th + Math.PI, up = Math.max(Math.sin(a), 0);
    sun.position.set(Math.cos(a) * 60, up * 62 + 6, 30);
    const base = era === 'future' ? 1.6 : 2.0;
    sun.intensity = base * (1 - nightK) * (0.4 + 0.6 * THREE.MathUtils.clamp(elev * 2.2, 0, 1)) + 0.22 * nightK;
    sunCol.setRGB(1, 0.97, 0.93).lerp(new THREE.Color(1, 0.62, 0.38), warm).lerp(new THREE.Color(0.62, 0.72, 1), nightK); sun.color.copy(sunCol);
    hemi.intensity = 0.35 * (1 - nightK) + 0.14 * nightK;
    hemiSky.setRGB(1, 1, 1).lerp(new THREE.Color(1, 0.8, 0.65), warm * 0.6).lerp(new THREE.Color(0.35, 0.45, 0.8), nightK); hemi.color.copy(hemiSky);
    hemiGround.setRGB(0.81, 0.78, 0.71).lerp(new THREE.Color(0.12, 0.13, 0.18), nightK); hemi.groundColor.copy(hemiGround);
    scene.environmentIntensity = (era === 'future' ? 0.75 : 0.55) * (1 - nightK * 0.8) * (1 - warm * 0.15);
    renderer.toneMappingExposure = 1 - nightK * 0.12;
    applyNight(nightK);
    const nf = nightK > 0.5; if (nf !== nightFlag) { nightFlag = nf; fx?.setNight(nf); }
    onTime?.(tod, nightK, warm);
  };
  const bboxOf = {};
  const homeView = () => ({ target: new THREE.Vector3(0, 3 + PLATE_Y, -1), pos: new THREE.Vector3(0, 3 + PLATE_Y, -1).addScaledVector(HOME_DIR, fit(34)) });
  const zoneView = i => {
    const box = bboxOf[cats[i].c.id], c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3());
    const r = Math.max(s.x, s.z * 0.8, s.y * 1.1) * 0.62 + 2;
    const dir = new THREE.Vector3(c.x * 0.012 - 0.16, 0.5, 1).normalize();
    const wide = camera.aspect > 1.05;
    const dist = wide ? r / tanH() / camera.aspect * 2.1 : fit(r) * 1.2;
    const right = new THREE.Vector3().crossVectors(new THREE.Vector3(0, 1, 0), dir).normalize();
    const target = c.clone(); target.y = s.y * 0.38 + PLATE_Y; c.y += PLATE_Y;
    if (wide) target.addScaledVector(right, -dist * tanH() * camera.aspect * 0.26); else target.y -= dist * tanH() * 0.28;
    return { target, pos: target.clone().addScaledVector(dir, dist) };
  };
  // Flights follow a gentle arc (lifted midpoint) instead of a straight line.
  // zoom limits: the default range around the town; a focused building may sit closer than it. While flying there are no limits,
  // otherwise OrbitControls clamps the camera mid-flight and it looks like it hits the building and bounces back.
  let minD = 0, maxD = Infinity;
  const limits = () => { const d = camera.position.distanceTo(controls.target); controls.minDistance = active >= 0 ? Math.min(minD, d * 0.9) : minD; controls.maxDistance = Math.max(maxD, d * 1.05); };
  const flyTo = (to, dur = 1.3, arc = 0, ctrl = null) => { controls.minDistance = 0; controls.maxDistance = Infinity; fly = { from: { pos: camera.position.clone(), target: controls.target.clone() }, to: { pos: to.pos.clone(), target: to.target.clone() }, t: 0, dur, arc, ctrl }; return fly; };
  const resize = () => {
    const w = host.clientWidth, h = host.clientHeight; if (!w || !h) return;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    home = homeView(); minD = fit(34) * 0.42; maxD = fit(34) * 1.35; if (!fly) limits();
  };
  resize();

  // ---- tweens + town rise / sink ----
  const tweens = [];
  const tween = (dur, delay, fn, done) => tweens.push({ t: -delay, dur, fn, done });
  function stage(group, rising, base = 0) {
    let last = 0;
    group.children.slice(1).forEach(o => { // everything except the ground; ring by ring from the centre
      const b = new THREE.Box3().setFromObject(o), c = b.getCenter(new THREE.Vector3());
      const depth = Math.max(0.6, b.max.y - Math.min(0, b.min.y)) + 0.8, dist = o.userData.dist ?? Math.hypot(c.x - CENTER.x, c.z - CENTER.z);
      const y0 = o.position.y, delay = base + (rising ? dist : 46 - dist) * 0.016, dur = rising ? 0.95 : 0.55;
      last = Math.max(last, delay + dur);
      if (rising) o.position.y = y0 - depth;
      tween(dur, delay, k => { o.position.y = rising ? y0 - depth * (1 - outBack(k)) : y0 - depth * inCubic(k); }, () => { o.position.y = rising ? y0 : y0 - depth; });
    });
    return last;
  }
  const disposeGroup = g => { g.parent?.remove(g); const mats = new Set(); g.traverse(o => { o.geometry?.dispose(); o.material && mats.add(o.material); }); mats.forEach(m => m.dispose()); };
  function setEra(id, { instant = false, wait = 0 } = {}) {
    switching = true; onBusy?.(true);
    era = id;
    const old = town;
    if (fx) { fx.exit(); fading.push(fx); } fx = null;
    town = buildTown(id, types);
    town.buildings.forEach(b => { bboxOf[b.key] = new THREE.Box3().setFromObject(b.group); });
    basePos = town.buildings.map(b => b.group.position.clone());
    onEra?.(id, palette(id));
    boxStyle?.(id, instant || reduce || !old);
    dressSwap?.(id, instant || reduce || !old);
    applyTime();
    const quick = instant || reduce;
    let delay = wait;
    if (old) { if (quick) disposeGroup(old.group); else { delay = stage(old.group, false, 0.45) * 0.8; tween(0.01, delay + 0.6, () => {}, () => disposeGroup(old.group)); } }
    plate.add(town.group);
    const end = quick ? 0 : stage(town.group, true, delay);
    tween(0.01, quick ? 0 : end + 0.25, () => {}, () => { switching = false; onBusy?.(false); }); // unlock once the new town has settled
    fx = createFx(plate, id, town, { reduce }); fx.enter(quick ? 0 : delay); fx.setNight(nightK > 0.5);
    if (active >= 0) { onZone?.(null); pendingZone = active; flyTo(zoneView(active), Math.max(0.9, end * 0.7), 0); }
  }

  // ---- hover / focus rings ----
  const ringMat = new THREE.MeshBasicMaterial({ color: 0xa63a2b, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide });
  const ringGeo = new THREE.RingGeometry(0.94, 1, 96);
  const ring = new THREE.Mesh(ringGeo, ringMat), ring2 = new THREE.Mesh(ringGeo, ringMat.clone());
  for (const r of [ring, ring2]) { r.rotation.x = -Math.PI / 2; r.position.y = 0.14; }
  const ringFor = i => { const b = bboxOf[cats[i].c.id], s = b.getSize(new THREE.Vector3()), c = b.getCenter(new THREE.Vector3()); return { c, r: Math.max(s.x, s.z) * 0.62 + 1.2 }; };

  // ---------- 造物之匣: a lacquered keepsake box (推光漆, 描金 double frames, 白铜 fittings, 如意 feet) ----------
  // The town sits on a stand inside it. Walls (and the lid) that come between the camera and the town fade to translucent.
  const A = 40, WT = 1.5, TOP = 22, BASE = -1.6; // 80 × 80 inside, ~23.6 tall
  const M = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.7, flatShading: true, transparent: true, ...o });
  const wood = M(0x2c1a14, { roughness: 0.32 });                       // lacquer body (kept as "wood" for the stand)
  const woodDark = M(0x1f120e, { roughness: 0.36 });                   // darker lacquer for rims and mouldings
  const lining = M(0xefe7d6, { roughness: 0.95 });                     // pale silk lining
  const brass = M(0xc8a96a, { roughness: 0.3, metalness: 0.85 });      // gold for the painted lines
  const baitong = M(0xd9d0bb, { roughness: 0.28, metalness: 0.85 });   // white brass fittings
  const boxG = new THREE.Group(); scene.add(boxG);
  const slab = (w, h, d, m, x, y, z, g = boxG) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y + h / 2, z); o.castShadow = o.receiveShadow = true; g.add(o); return o; };
  const O = A + WT;
  slab(O * 2, -BASE - 0.03, O * 2, wood, 0, BASE, 0);                                 // box floor
  // a rectangular frame of thin bars on a wall face (u along the wall, v up), used for the 描金 lines
  const frame = (g, m, along, sgn, off, u0, u1, v0, v1, t) => {
    const cu = (u0 + u1) / 2, cv = (v0 + v1) / 2, lu = u1 - u0, lv = v1 - v0, out = sgn * (off + 0.04);
    const put = (w, h, u, v) => along === 'x' ? slab(w, h, 0.06, m, u, v - h / 2, out, g) : slab(0.06, h, w, m, out, v - h / 2, u, g);
    put(lu, t, cu, v1); put(lu, t, cu, v0); put(t, lv, u0, cv); put(t, lv, u1, cv);
  };
  // each era dresses the same shell differently: ornaments, feet, lid and stand are per-era groups that swap on era change
  const dress = { ancient: [], early: [], modern: [], future: [] };
  const dg = (era, parent) => { const g = new THREE.Group(); g.userData.era = era; parent.add(g); dress[era].push(g); return g; };
  // each side wall has its own materials so it can fade on its own
  const sides = [[0, 1], [0, -1], [1, 0], [-1, 0]].map(([nx, nz]) => {
    const mats = [wood.clone(), lining.clone(), woodDark.clone(), brass.clone(), baitong.clone()], g = new THREE.Group(); boxG.add(g);
    const along = nz ? 'x' : 'z', sgn = nz || nx, L = O * 2, off = A + WT / 2, face = A + WT;
    if (along === 'x') { slab(L, TOP - BASE, WT, mats[0], 0, BASE, nz * off, g); slab(A * 2, TOP - 0.05, 0.08, mats[1], 0, 0, nz * (A - 0.04), g); slab(L + 0.2, 0.28, WT + 0.2, mats[2], 0, TOP, nz * off, g); slab(L + 0.22, 0.06, 0.12, mats[3], 0, TOP + 0.28, nz * (face + 0.04), g); }
    else { slab(WT, TOP - BASE, A * 2, mats[0], nx * off, BASE, 0, g); slab(0.08, TOP - 0.05, A * 2, mats[1], nx * (A - 0.04), 0, 0, g); slab(WT + 0.2, 0.28, L + 0.2, mats[2], nx * off, TOP, 0, g); slab(0.12, 0.06, L + 0.22, mats[3], nx * (face + 0.04), TOP + 0.28, 0, g); }
    // 描金: a double frame inset on the outer face
    const ga = dg('ancient', g);
    frame(ga, mats[3], along, sgn, face, -O + 2.4, O - 2.4, BASE + 2.2, TOP - 1.6, 0.22);
    frame(ga, mats[3], along, sgn, face, -O + 3.4, O - 3.4, BASE + 3.2, TOP - 2.6, 0.09);
    if (nz === 1) { // round 面叶 with a pull ring at the front
      const plateM = mats[4], disc = new THREE.Mesh(new THREE.CylinderGeometry(1.7, 1.7, 0.12, 28), plateM); disc.rotation.x = Math.PI / 2; disc.position.set(0, TOP - 2.6, face + 0.1); ga.add(disc);
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.75, 0.1, 6, 24), plateM); ring.position.set(0, TOP - 3.45, face + 0.24); ga.add(ring);
      slab(0.5, 0.5, 0.25, plateM, 0, TOP - 2.85, face + 0.16, ga);
    }
    if (nz === -1) for (const sx of [-1, 1]) slab(6, 0.5, 0.16, mats[4], sx * 22, TOP - 0.6, -face - 0.08, ga);   // slim hinges
    return { n: new THREE.Vector3(nx, 0, nz), nx, nz, along, sgn, g, mats, k: 1 };
  });
  // 白铜 corner caps at the top and bottom of each vertical edge, and low 如意 feet
  const caA = dg('ancient', boxG);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    for (const y of [TOP - 1.6, BASE]) slab(WT * 2 + 0.3, 1.9, WT * 2 + 0.3, baitong, sx * (O - WT + 0.15), y, sz * (O - WT + 0.15), caA);
    const foot = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 2.2, 1.1, 10), woodDark); foot.position.set(sx * (O - 3.5), BASE - 0.55, sz * (O - 3.5)); foot.castShadow = true; caA.add(foot);
    slab(7, 0.5, 1.4, woodDark, sx * (O - 6), BASE - 0.5, sz * (O - 1.2), caA); slab(1.4, 0.5, 7, woodDark, sx * (O - 1.2), BASE - 0.5, sz * (O - 6), caA);
  }

  // the plate the town stands on, with brass posts underneath
  const plate = new THREE.Group(); plate.position.y = reduce ? PLATE_Y : 0; scene.add(plate);
  for (const r of [ring, ring2]) plate.add(r);
  const pm = [woodDark.clone(), brass.clone(), wood.clone()]; pm.forEach(m => { m.transparent = false; });
  slab(80.4, 0.7, 80.4, pm[0], 0, -0.76, 0, plate);                                   // plate (top just under the town floor)
  slab(80.9, 0.16, 80.9, pm[1], 0, -0.4, 0, plate);                                   // brass edge band
  slab(80.6, 0.5, 80.6, pm[2], 0, -1.3, 0, plate);                                    // lower moulding
  // ---- a classical wooden stand (明式炕桌式底座) under the plate: waist, shaped aprons, horse-hoof legs, braces, base frame ----
  const rose = new THREE.MeshStandardMaterial({ color: 0x2c1a14, roughness: 0.32, flatShading: true }); // same lacquer as the box
  const roseDk = new THREE.MeshStandardMaterial({ color: 0x1f120e, roughness: 0.36, flatShading: true });
  const capM = pm[1];
  const SH0 = PLATE_Y - 1.3;         // stand height below the moulding, so its feet meet the box floor when risen
  const LEG = 2.4, IN0 = 37.2;       // leg section and leg centre offset from the middle
  const stA = dg('ancient', plate);
  slab(77, 0.9, 77, roseDk, 0, -2.2, 0, stA);                                                     // 束腰 waist
  slab(78.4, 0.35, 78.4, rose, 0, -2.55, 0, stA);                                                 // thin moulding under the waist
  // aprons with a 壸门 (cusped arch) lower edge and cloud curls by the legs
  const apronGeo = (() => {
    const L = IN0 * 2 - LEG, H = 3.4, sh = new THREE.Shape();
    sh.moveTo(-L / 2, 0); sh.lineTo(L / 2, 0); sh.lineTo(L / 2, -H);
    const N = 40;
    for (let i = 0; i <= N; i++) {
      const u = i / N, x = L / 2 - u * L, e = Math.abs(u - 0.5) * 2;           // e: 0 at the middle, 1 at the ends
      const arch = Math.pow(1 - e, 0.55) * 1.7, curl = Math.max(0, Math.sin((e - 0.78) / 0.22 * Math.PI)) * 0.55 * (e > 0.78 ? 1 : 0);
      sh.lineTo(x, -H + arch + curl);
    }
    sh.lineTo(-L / 2, 0);
    const g = new THREE.ExtrudeGeometry(sh, { depth: 0.7, bevelEnabled: false }); g.translate(0, 0, -0.35); return g;
  })();
  for (const [x, z, ry] of [[0, IN0, 0], [0, -IN0, Math.PI], [IN0, 0, Math.PI / 2], [-IN0, 0, -Math.PI / 2]]) {
    const ap = new THREE.Mesh(apronGeo, rose); ap.position.set(x, -2.6, z); ap.rotation.y = ry; ap.castShadow = ap.receiveShadow = true; stA.add(ap);
    // a carved line just inside the apron edge
    const bead = new THREE.Mesh(new THREE.BoxGeometry(IN0 * 2 - LEG - 2, 0.12, 0.2), capM); bead.position.set(x, -2.9, z); bead.rotation.y = ry;
    bead.position.x += Math.sin(ry) * 0.36; bead.position.z += Math.cos(ry) * 0.36; stA.add(bead);
  }
  // four tapering square legs ending in inward-turned horse-hoof feet with brass caps
  const legGeo = new THREE.CylinderGeometry(LEG * 0.62, LEG * 0.5, SH0 - 2.6, 4); legGeo.rotateY(Math.PI / 4);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const x = sx * IN0, z = sz * IN0;
    const leg = new THREE.Mesh(legGeo, rose); leg.position.set(x, -2.2 - (SH0 - 2.6) / 2, z); leg.castShadow = true; stA.add(leg);
    const hoof = new THREE.Mesh(new THREE.BoxGeometry(LEG * 1.05, 1.5, LEG * 1.05), rose); hoof.position.set(x - sx * 0.55, -SH0 + 0.55, z - sz * 0.55); hoof.castShadow = true; stA.add(hoof);
    const cap = new THREE.Mesh(new THREE.BoxGeometry(LEG * 1.15, 0.35, LEG * 1.15), capM); cap.position.set(x - sx * 0.6, -SH0 - 0.05, z - sz * 0.6); stA.add(cap);
    // 霸王枨: a brace from each leg up under the aprons, in both directions
    for (const [dx, dz] of [[-sx, 0], [0, -sz]]) {
      const p0 = new THREE.Vector3(x, -SH0 * 0.42, z), p1 = new THREE.Vector3(x + dx * 14, -3.4, z + dz * 14);
      const len = p0.distanceTo(p1), br = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.7, len), roseDk);
      br.position.copy(p0).add(p1).multiplyScalar(0.5); br.quaternion.setFromRotationMatrix(new THREE.Matrix4().lookAt(p0, p1, new THREE.Vector3(0, 1, 0))); br.castShadow = true; stA.add(br);
    }
  }
  // 托泥 base frame joining the feet
  for (const [w, d, x, z] of [[IN0 * 2 + 1.6, 1.6, 0, IN0 - 0.4], [IN0 * 2 + 1.6, 1.6, 0, -IN0 + 0.4], [1.6, IN0 * 2 - 1.6, IN0 - 0.4, 0], [1.6, IN0 * 2 - 1.6, -IN0 + 0.4, 0]])
    slab(w, 0.9, d, roseDk, x, -SH0, z, stA);
  const islandTick = () => {};
  const syncPosts = () => {}; // kept for the opening sequence; the island needs no posts
  syncPosts();
  const table = new THREE.Mesh(new THREE.PlaneGeometry(700, 700), new THREE.MeshStandardMaterial({ color: 0xe6dccb, /* recoloured per era */ roughness: 1 }));
  table.rotation.x = -Math.PI / 2; table.position.y = BASE - 1.1; table.receiveShadow = true; scene.add(table);
  // lid: lacquer with a 描金 double frame and a vertical title slip (题签); silk lining inside
  const lid = new THREE.Group(); lid.position.set(0, TOP + 0.34, -O); boxG.add(lid);
  const LW = O * 2 + 0.4;
  const lw = wood.clone(), lwd = woodDark.clone(), lln = lining.clone(), lbr = brass.clone(), lbt = baitong.clone();
  const lidMats = [lw, lwd, lln, lbr, lbt];
  slab(LW, 1.0, LW, lw, 0, 0, LW / 2 - 0.2, lid);
  for (const s2 of [-1, 1]) { slab(LW, 1.1, 0.5, lwd, 0, -1.1, s2 < 0 ? 0 : LW - 0.5, lid); slab(0.5, 1.1, LW, lwd, s2 * (LW / 2 - 0.25), -1.1, LW / 2 - 0.2, lid); } // skirt over the walls
  slab(LW - 0.4, 0.06, LW - 0.4, lln, 0, -0.06, LW / 2 - 0.2, lid);                    // silk lining under the lid
  const laA = dg('ancient', lid);
  const lidFrame = (inset, t, m = lbr, g = laA) => { const a = LW / 2 - inset, cz = LW / 2 - 0.2;
    slab(a * 2, 0.05, t, m, 0, 1.0, cz - a, g); slab(a * 2, 0.05, t, m, 0, 1.0, cz + a, g); slab(t, 0.05, a * 2, m, -a, 1.0, cz, g); slab(t, 0.05, a * 2, m, a, 1.0, cz, g); };
  lidFrame(2.4, 0.26); lidFrame(3.5, 0.1);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) slab(3, 0.08, 3, lbt, sx * (LW / 2 - 1.5), 1.0, LW / 2 - 0.2 + sz * (LW / 2 - 1.5), laA); // white-brass corner plates
  const slip = (lines, w, h, ink, bg, gold, vertical) => { const c = document.createElement('canvas'); c.width = vertical ? 384 : 1024; c.height = Math.round(c.width * h / w); const x = c.getContext('2d');
    x.fillStyle = bg; x.fillRect(0, 0, c.width, c.height); x.strokeStyle = gold; x.lineWidth = 6; x.strokeRect(14, 14, c.width - 28, c.height - 28); x.lineWidth = 2; x.strokeRect(26, 26, c.width - 52, c.height - 52);
    x.fillStyle = ink; x.textAlign = 'center'; x.textBaseline = 'middle';
    if (vertical) { const chars = [...lines[0]], fs = Math.round(c.width * 0.5); x.font = `600 ${fs}px "Noto Serif SC", "Songti SC", serif`; chars.forEach((ch, i) => x.fillText(ch, c.width / 2, c.height * (0.16 + i * 0.2)));
      x.fillStyle = '#a8402f'; x.fillRect(c.width / 2 - c.width * 0.16, c.height * 0.9 - c.width * 0.16, c.width * 0.32, c.width * 0.32); x.fillStyle = '#f7ece4'; x.font = `600 ${Math.round(c.width * 0.2)}px "Noto Serif SC", serif`; x.fillText('造', c.width / 2, c.height * 0.9); }
    else { x.font = `600 ${Math.round(c.height * 0.3)}px "Noto Serif SC", "Songti SC", serif`; x.fillText(lines[0], c.width / 2, c.height * 0.44); x.fillStyle = gold; x.font = `500 ${Math.round(c.height * 0.1)}px "Noto Serif SC", serif`; x.fillText(lines[1], c.width / 2, c.height * 0.74); }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
  const mkTitle = () => slip(['造物之匣'], 6, 20, '#2a2420', '#efe6d3', '#b09461', true);
  // the note inside the lid follows the era's lining
  const NOTE = { ancient: ['#2a2420', '#f1e9d8', '#b09461'], early: ['#efe3c6', '#2e4a3b', '#c49a4c'], modern: ['#1c1c1c', '#fbfbf9', '#1c1c1c'], future: ['#2a8fc4', '#f2f8fc', '#52d0ff'] };
  let noteEra = 'ancient';
  const mkNote = () => slip(['造物之匣', '收藏想法的小匣子'], 24, 7.5, ...NOTE[noteEra], false);
  const lidTitle = new THREE.Mesh(new THREE.PlaneGeometry(6, 20), new THREE.MeshStandardMaterial({ map: mkTitle(), roughness: 0.85, transparent: true }));
  lidMats.push(lidTitle.material); lidTitle.rotation.x = -Math.PI / 2; lidTitle.position.set(-LW / 2 + 10, 1.07, LW / 2 - 0.2 + LW / 2 - 16); laA.add(lidTitle);
  const lidNote = new THREE.Mesh(new THREE.PlaneGeometry(24, 7.5), new THREE.MeshStandardMaterial({ map: mkNote(), roughness: 0.9, transparent: true }));
  lidMats.push(lidNote.material); lidNote.rotation.x = Math.PI / 2; lidNote.position.set(0, -0.12, LW / 2 - 9); lid.add(lidNote);
  const glowLight = new THREE.PointLight(0xffd9a0, 0, 120, 1.1); glowLight.position.set(0, TOP * 0.6, 0); scene.add(glowLight);
  const LID_OPEN = -2.72; // leaning back on the table behind the box
  document.fonts?.ready.then(() => { lidTitle.material.map.dispose(); lidTitle.material.map = mkTitle(); lidTitle.material.needsUpdate = true; lidNote.material.map.dispose(); lidNote.material.map = mkNote(); lidNote.material.needsUpdate = true; });


  // ---------- the other three dresses ----------
  const CZ = LW / 2 - 0.2;                                   // lid centre (lid local z)
  const onWall = (sd, g, m, u, v, w, h, t, out = 0) => { const c = sd.sgn * (O + out + t / 2); return sd.along === 'x' ? slab(w, h, t, m, u, v, c, g) : slab(t, h, w, m, c, v, u, g); };
  const atWall = (sd, o, u, v, out) => { if (sd.along === 'x') { o.position.set(u, v, sd.sgn * (O + out)); if (sd.sgn < 0) o.rotation.y = Math.PI; } else { o.position.set(sd.sgn * (O + out), v, u); o.rotation.y = sd.sgn * Math.PI / 2; } return o; };
  const mesh = (geo, m, g) => { const o = new THREE.Mesh(geo, m); o.castShadow = true; g.add(o); return o; };
  const lathe = (prof, H, seg = 14) => new THREE.LatheGeometry(prof.map(([r, y]) => new THREE.Vector2(r, y * H)), seg);
  const label = (lines, w, h, ink, font, bg = null) => { const c = document.createElement('canvas'); c.width = 1024; c.height = Math.round(1024 * h / w); const x = c.getContext('2d');
    if (bg) { x.fillStyle = bg; x.fillRect(0, 0, c.width, c.height); }
    x.fillStyle = ink; x.textBaseline = 'middle'; x.font = `600 ${Math.round(c.height * 0.4)}px ${font}`; x.fillText(lines[0], c.height * 0.14, c.height * 0.38);
    x.font = `500 ${Math.round(c.height * 0.15)}px ${font}`; x.fillText(lines[1], c.height * 0.16, c.height * 0.8);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
  const tagMesh = (mk, w, h, g, x, y, z) => { const m = new THREE.MeshStandardMaterial({ map: mk(), roughness: 0.6, transparent: true }); lidMats.push(m);
    const o = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); o.rotation.x = -Math.PI / 2; o.position.set(x, y, z); g.add(o);
    document.fonts?.ready.then(() => { m.map.dispose(); m.map = mk(); m.needsUpdate = true; }); return o; };
  const SH = PLATE_Y - 1.3, IN = 37.2;

  // 近代 · a steamer trunk: battens, brass corners and rivets, leather straps with buckles, a lock plate, ball feet; turned-leg stand with an X stretcher
  {
    for (const sd of sides) {
      const g = dg('early', sd.g), leather = M(0x5b3320, { roughness: 0.75 }); sd.mats.push(leather);
      for (const v of [BASE + 3.2, TOP - 4.2]) onWall(sd, g, sd.mats[2], 0, v, O * 2, 1.3, 0.45);
      for (const u of [-16, 16]) { onWall(sd, g, sd.mats[2], u, BASE + 0.6, 1.3, TOP - BASE - 1.2, 0.4); for (const v of [BASE + 3.2, TOP - 4.2]) onWall(sd, g, sd.mats[3], u, v + 0.45, 0.42, 0.42, 0.2, 0.45); }
      if (sd.nz === 1) {
        for (const u of [-9, 9]) { onWall(sd, g, leather, u, BASE + 0.4, 2.2, TOP - BASE - 0.5, 0.22, 0.45); onWall(sd, g, sd.mats[3], u, TOP - 8, 2.8, 2.2, 0.28, 0.67); onWall(sd, g, leather, u, TOP - 7.6, 1.6, 1.4, 0.1, 0.95); }
        onWall(sd, g, sd.mats[3], 0, TOP - 6.2, 3.8, 4.4, 0.35, 0.45); onWall(sd, g, sd.mats[2], 0, TOP - 4.9, 0.5, 1.3, 0.08, 0.8); onWall(sd, g, sd.mats[3], 0, TOP - 1.9, 1.6, 2.4, 0.3, 0.45);
      } else if (sd.nz === -1) for (const u of [-20, 20]) onWall(sd, g, sd.mats[3], u, TOP - 2.4, 5, 2.4, 0.3, 0.45);
      else { atWall(sd, mesh(new THREE.TorusGeometry(2.6, 0.38, 6, 18, Math.PI), leather, g), 0, TOP - 7.4, 0.9); for (const u of [-2.6, 2.6]) onWall(sd, g, sd.mats[3], u, TOP - 8.1, 1.4, 1.4, 0.3, 0.45); }
    }
    const g = dg('early', boxG);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
      for (const y of [TOP - 3.4, BASE]) slab(3.6, 3.4, 3.6, brass, sx * (O - 1.2), y, sz * (O - 1.2), g);
      mesh(new THREE.SphereGeometry(1.2, 14, 10), brass, g).position.set(sx * (O - 3.2), BASE - 0.1, sz * (O - 3.2));
    }
    const lg = dg('early', lid), strap = M(0x5b3320, { roughness: 0.75 }); lidMats.push(strap);
    for (const zz of [CZ - LW / 2 + 0.7, CZ + LW / 2 - 0.7]) slab(LW, 0.35, 1.4, lwd, 0, 1.0, zz, lg);
    for (const xx of [-LW / 2 + 0.7, LW / 2 - 0.7, -16, 16]) slab(1.4, 0.35, LW, lwd, xx, 1.0, CZ, lg);
    for (const xx of [-9, 9]) slab(2.2, 0.14, LW, strap, xx, 1.36, CZ, lg);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) slab(3.8, 0.5, 3.8, lbr, sx * (LW / 2 - 1.7), 0.9, CZ + sz * (LW / 2 - 1.7), lg);
    tagMesh(() => label(['造物之匣', 'CABINET OF MAKING · 1902'], 14, 4.4, '#3a2410', '"Noto Serif SC", serif', '#c9a35a'), 14, 4.4, lg, 0, 1.4, CZ + 10);
    // stand: plain apron boards with a brass bead, lathe-turned legs, an X stretcher with a turned urn, brass ferrules
    const st = dg('early', plate), H = SH - 4.4;
    slab(IN * 2 - 1, 2.6, IN * 2 - 1, roseDk, 0, -4.2, 0, st);
    for (const sz of [-1, 1]) { slab(IN * 2 + 2.8, 2.85, 1.0, rose, 0, -4.4, sz * IN, st); slab(1.0, 2.85, IN * 2 + 2.8, rose, sz * IN, -4.4, 0, st);
      slab(IN * 2, 0.22, 1.1, capM, 0, -4.55, sz * IN, st); slab(1.1, 0.22, IN * 2, capM, sz * IN, -4.55, 0, st); }
    const legG = lathe([[0, 0], [1.05, 0], [1.4, 0.04], [1.45, 0.08], [1.05, 0.13], [0.78, 0.18], [0.72, 0.44], [1.0, 0.47], [1.0, 0.5], [0.72, 0.53], [0.82, 0.62], [1.3, 0.75], [1.36, 0.82], [0.98, 0.9], [1.05, 0.93], [1.3, 0.95], [1.3, 1], [0, 1]], H);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
      mesh(legG, rose, st).position.set(sx * IN, -SH, sz * IN);
      slab(2.8, 2.85, 2.8, rose, sx * IN, -4.4, sz * IN, st);
      mesh(new THREE.CylinderGeometry(1.5, 1.5, 0.4, 14), capM, st).position.set(sx * IN, -SH - 0.05, sz * IN);
    }
    const ys = -SH + H * 0.3, len = Math.hypot(IN * 2, IN * 2);
    for (const r of [Math.PI / 4, -Math.PI / 4]) { const b = mesh(new THREE.BoxGeometry(1.1, 0.9, len), roseDk, st); b.position.set(0, ys, 0); b.rotation.y = r; }
    mesh(lathe([[0, 0], [2.4, 0], [2.6, 0.08], [1.4, 0.2], [2.2, 0.45], [2.4, 0.6], [1.2, 0.85], [0.6, 0.92], [0.9, 1], [0, 1]], 4.2), rose, st).position.set(0, ys + 0.4, 0);
    mesh(new THREE.SphereGeometry(0.7, 12, 8), capM, st).position.set(0, ys + 4.9, 0);
  }

  // 现代 · a matte archive box: shadow-gap line, slot pull, an orange tab, recessed plinth; black steel frame with a white monolith
  {
    for (const sd of sides) {
      const g = dg('modern', sd.g);
      onWall(sd, g, sd.mats[3], 0, TOP - 5.5, O * 2 + 0.1, 0.16, 0.05);
      if (sd.nz === 1) { const orange = M(0xff4a1c, { roughness: 0.6 }); sd.mats.push(orange);
        onWall(sd, g, sd.mats[3], 0, TOP - 3.4, 12, 0.7, 0.05); onWall(sd, g, orange, O - 8, TOP - 6.7, 2.6, 1.2, 0.3);
        onWall(sd, g, sd.mats[3], -O + 6, BASE + 3, 7, 0.08, 0.04); onWall(sd, g, sd.mats[3], -O + 6, BASE + 4.2, 4, 0.08, 0.04); }
    }
    const g = dg('modern', boxG), plinth = new THREE.MeshStandardMaterial({ color: 0x2f2f2f, roughness: 0.85, flatShading: true });
    slab(O * 2 - 4, 1.1, O * 2 - 4, plinth, 0, BASE - 1.1, 0, g);
    const lg = dg('modern', lid), orangeL = M(0xff4a1c, { roughness: 0.6 }); lidMats.push(orangeL);
    lidFrame(3.0, 0.08, lbr, lg);
    slab(1.8, 0.12, 1.8, orangeL, LW / 2 - 5.5, 1.0, CZ + LW / 2 - 5.5, lg);
    tagMesh(() => label(['造物之匣', 'ARCHIVE BOX — 01'], 22, 6.4, '#1c1c1c', '"Noto Sans SC", sans-serif'), 22, 6.4, lg, -LW / 2 + 15.5, 1.04, CZ + LW / 2 - 8);
    const st = dg('modern', plate);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) slab(0.9, SH - 1.55, 0.9, capM, sx * IN, -SH, sz * IN, st);
    for (const y of [-2.45, -SH]) for (const sz of [-1, 1]) { slab(IN * 2, 0.8, 0.9, capM, 0, y, sz * IN, st); slab(0.9, 0.8, IN * 2, capM, sz * IN, y, 0, st); }
    slab(34, SH - 2.6, 34, rose, 0, -SH, 0, st);
  }

  // 未来 · a frosted glass case: glowing edge lines and ticks, an emblem ring, hover pads and a halo; a single light stem with orbiting rings
  const orbit = [];
  let beam = null;
  {
    for (const sd of sides) {
      const g = dg('future', sd.g);
      for (const v of [BASE + 2.4, TOP - 2.4]) onWall(sd, g, sd.mats[3], 0, v, O * 2 - 4, 0.14, 0.06);
      for (let i = -4; i <= 4; i++) onWall(sd, g, sd.mats[3], i * 5.6, BASE + 2.54, 0.1, i % 2 ? 0.6 : 1.4, 0.06);
      if (sd.nz === 1) { atWall(sd, mesh(new THREE.TorusGeometry(2.8, 0.12, 6, 48), sd.mats[3], g), 0, TOP - 8, 0.12); atWall(sd, mesh(new THREE.CylinderGeometry(0.7, 0.7, 0.12, 24).rotateX(Math.PI / 2), sd.mats[3], g), 0, TOP - 8, 0.08); }
    }
    const g = dg('future', boxG);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
      slab(0.36, TOP - BASE - 0.6, 0.36, brass, sx * (O + 0.05), BASE + 0.3, sz * (O + 0.05), g);
      mesh(new THREE.CylinderGeometry(2.2, 2.6, 0.5, 24), baitong, g).position.set(sx * (O - 5), BASE - 0.45, sz * (O - 5));
      const pr = mesh(new THREE.TorusGeometry(2.5, 0.12, 6, 32), brass, g); pr.rotation.x = Math.PI / 2; pr.position.set(sx * (O - 5), BASE - 0.75, sz * (O - 5));
    }
    const halo = mesh(new THREE.TorusGeometry(O + 4, 0.18, 6, 120), brass, g); halo.rotation.x = Math.PI / 2; halo.position.y = BASE - 1.02;
    const lg = dg('future', lid);
    const lr = mesh(new THREE.TorusGeometry(13, 0.14, 6, 96), lbr, lg); lr.rotation.x = Math.PI / 2; lr.position.set(0, 1.04, CZ);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) { const cx = sx * (LW / 2 - 3), cz = CZ + sz * (LW / 2 - 3); slab(6, 0.06, 0.3, lbr, cx - sx * 3, 1.0, cz, lg); slab(0.3, 0.06, 6, lbr, cx, 1.0, cz - sz * 3, lg); }
    tagMesh(() => label(['造物之匣', 'ARCHIVE // ∞'], 18, 5.2, '#52d0ff', '"IBM Plex Mono", "Noto Sans SC", monospace'), 18, 5.2, lg, 0, 1.06, CZ);
    const st = dg('future', plate);
    mesh(new THREE.CylinderGeometry(14, 10, 1.2, 48), rose, st).position.y = -2.15;
    const rim = mesh(new THREE.TorusGeometry(14, 0.22, 6, 64), capM, st); rim.rotation.x = Math.PI / 2; rim.position.y = -1.6;
    mesh(new THREE.CylinderGeometry(2.2, 3.2, SH - 3.6, 24), rose, st).position.y = (-SH + 0.8 - 2.75) / 2;
    mesh(new THREE.CylinderGeometry(9, 10, 0.8, 48), roseDk, st).position.y = -SH + 0.4;
    const br = mesh(new THREE.TorusGeometry(9.5, 0.2, 6, 64), capM, st); br.rotation.x = Math.PI / 2; br.position.y = -SH + 0.85;
    [[6, -5], [8.5, -8.5], [11, -12]].forEach(([r, y], i) => { const o = mesh(new THREE.TorusGeometry(r, 0.24, 6, 72), capM, st); o.position.y = y; o.rotation.x = Math.PI / 2 + (i - 1) * 0.12; o.userData.spin = (i % 2 ? -1 : 1) * (0.5 + i * 0.2); orbit.push(o); });
    beam = mesh(new THREE.CylinderGeometry(4, 6.5, SH - 4, 24, 1, true), new THREE.MeshBasicMaterial({ color: 0x52d0ff, transparent: true, opacity: 0.1, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide }), st);
    beam.castShadow = false; beam.position.y = (-SH - 2.75) / 2 + 0.6;
  }
  dressTick = (t, dt) => {
    if (!dress.future[0].visible) return;
    orbit.forEach((o, i) => { o.rotation.z += o.userData.spin * dt; o.position.y += Math.sin(t * 1.3 + i * 2) * dt * 0.4; });
    beam.material.opacity = 0.08 + Math.sin(t * 2.2) * 0.03;
  };

  // swap dresses: the old one folds away, the new one grows in piece by piece while the town lifts a little off its stand
  const parts = era => dress[era].flatMap(g => g.children);
  for (const e in dress) parts(e).forEach(o => { o.userData.s0 = o.scale.clone(); });
  let dressNow = null;
  const renote = id => { if (noteEra === id) return; noteEra = id; lidNote.material.map.dispose(); lidNote.material.map = mkNote(); lidNote.material.needsUpdate = true; };
  dressSwap = (id, instant) => {
    const old = dressNow; dressNow = id;
    if (instant || !old) renote(id); else tween(0.01, 0.6, () => {}, () => { if (dressNow === id) renote(id); });
    if (instant || !old) { for (const e in dress) { dress[e].forEach(g => { g.visible = e === id; }); parts(e).forEach(o => o.scale.copy(o.userData.s0)); } return; }
    if (old === id) return;
    const out = parts(old);
    out.forEach((o, i) => tween(0.34, (i / out.length) * 0.35, k => o.scale.copy(o.userData.s0).multiplyScalar(Math.max(0.001, 1 - inCubic(k)))));
    tween(0.01, 0.75, () => {}, () => { if (dressNow !== old) dress[old].forEach(g => { g.visible = false; }); out.forEach(o => o.scale.copy(o.userData.s0)); });
    const inn = parts(id); inn.forEach(o => o.scale.setScalar(0.001)); dress[id].forEach(g => { g.visible = true; });
    inn.forEach((o, i) => tween(0.6, 0.6 + (i / inn.length) * 0.75, k => o.scale.copy(o.userData.s0).multiplyScalar(Math.max(0.001, outBack(k)))));
    tween(1.9, 0.2, k => { plate.position.y = PLATE_Y + Math.sin(k * Math.PI) * 1.8; }, () => { plate.position.y = PLATE_Y; });
  };

  // ---------- one box, four finishes: lacquer / mahogany & brass / matte white / frosted glass ----------
  const ROLE = {
    body: [wood, ...sides.map(x => x.mats[0]), lw, rose],
    dark: [woodDark, ...sides.map(x => x.mats[2]), lwd, roseDk, pm[0], pm[2]],
    lining: [lining, ...sides.map(x => x.mats[1]), lln],
    line: [brass, ...sides.map(x => x.mats[3]), lbr, pm[1]],
    metal: [baitong, ...sides.map(x => x.mats[4]), lbt],
  };
  const BOX_STYLE = {
    ancient: { body: [0xffffff, 0.48, 0], dark: [0xc9a07a, 0.5, 0], lining: [0xefe7d6, 0.95, 0], line: [0x2e1c12, 0.5, 0], metal: [0xd9d0bb, 0.28, 0.85], glass: 1, glow: 0, table: 0xe6dccb, grain: 'huanghuali' }, // 黄花梨 with ebony stringing and white-brass fittings
    early: { grain: 'mahogany', body: [0xffffff, 0.42, 0], dark: [0xa8857a, 0.45, 0], lining: [0x2e4a3b, 0.9, 0], line: [0xbb8b3e, 0.3, 0.8], metal: [0xc49a4c, 0.3, 0.82], glass: 1, glow: 0, table: 0xdccfb8 },
    modern: { body: [0xe9e9e5, 0.78, 0], dark: [0xd3d3cf, 0.72, 0], lining: [0xf8f8f6, 0.9, 0], line: [0x262626, 0.6, 0], metal: [0xc2c6ca, 0.32, 0.7], glass: 1, glow: 0, table: 0xececea },
    future: { body: [0xd6e6f0, 0.12, 0.2], dark: [0xbcd2e0, 0.14, 0.25], lining: [0xf4f9fc, 0.4, 0], line: [0x52d0ff, 0.2, 0], metal: [0xeef4f8, 0.15, 0.9], glass: 0.42, glow: 1.6, table: 0xe1eaf0 },
  };
  // procedural wood grain: long wavy streaks, a few 鬼脸 knots for huanghuali
  const grains = {};
  const grainTex = kind => {
    if (!kind) return null; if (grains[kind]) return grains[kind];
    const P = kind === 'huanghuali' ? { base: '#c48d55', dark: 'rgba(120, 70, 36, ', light: 'rgba(232, 184, 120, ', knots: 5 } : { base: '#70321f', dark: 'rgba(52, 18, 10, ', light: 'rgba(150, 72, 44, ', knots: 0 };
    const c = document.createElement('canvas'); c.width = c.height = 512; const x = c.getContext('2d');
    x.fillStyle = P.base; x.fillRect(0, 0, 512, 512);
    let sd = kind.length * 97; const r = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < 90; i++) {
      const y0 = r() * 512, amp = 4 + r() * 14, f = 0.004 + r() * 0.01, ph = r() * 6, w = 0.6 + r() * 2.6, dark = r() < 0.6;
      x.strokeStyle = (dark ? P.dark : P.light) + (0.12 + r() * 0.3) + ')'; x.lineWidth = w; x.beginPath();
      for (let px = -10; px <= 522; px += 8) { const py = y0 + Math.sin(px * f + ph) * amp + Math.sin(px * f * 3.1 + ph * 2) * amp * 0.3; px < 0 ? x.moveTo(px, py) : x.lineTo(px, py); }
      x.stroke();
    }
    for (let k = 0; k < P.knots; k++) { const cx = r() * 512, cy = r() * 512; for (let j = 0; j < 7; j++) { x.strokeStyle = P.dark + (0.18 + j * 0.03) + ')'; x.lineWidth = 1.4; x.beginPath(); x.ellipse(cx, cy, 10 + j * 7, 4 + j * 3, r() * 0.3, 0, Math.PI * 2); x.stroke(); } }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8; grains[kind] = t; return t;
  };
  const cA = new THREE.Color(), cB = new THREE.Color();
  boxStyle = (id, instant) => {
    const st = BOX_STYLE[id] ?? BOX_STYLE.ancient;
    const jobs = [];
    const tex = grainTex(st.grain);
    for (const [role, list] of Object.entries(ROLE)) for (const m of list) {
      if ((role === 'body' || role === 'dark') && m.map !== tex) jobs.push(k => { if (k >= 0.5 && m.map !== tex) { m.map = tex; m.needsUpdate = true; } }); // grain swaps halfway through the blend
      const [col, rough, metal] = st[role], from = { c: m.color.clone(), r: m.roughness, me: m.metalness, b: m.userData.base ?? 1, e: m.emissiveIntensity ?? 0 };
      const toB = role === 'body' || role === 'dark' ? (m.transparent ? st.glass : 1) : 1, toE = role === 'line' ? st.glow : 0;
      if (role === 'line') m.emissive.setHex(col);
      jobs.push(k => { m.color.copy(from.c).lerp(cB.setHex(col), k); m.roughness = from.r + (rough - from.r) * k; m.metalness = from.me + (metal - from.me) * k; m.userData.base = from.b + (toB - from.b) * k; if (role === 'line') m.emissiveIntensity = from.e + (toE - from.e) * k; });
    }
    const t0 = table.material.color.clone();
    jobs.push(k => table.material.color.copy(t0).lerp(cA.setHex(st.table), k));
    if (instant) jobs.forEach(f => f(1)); else tween(1.4, 0.15, k => { const e = k * k * (3 - 2 * k); jobs.forEach(f => f(e)); });
  };

  // ---------- opening sequence ----------
  let intro = !reduce, timeScale = 1;
  const INTRO = { hold: 0.6, open: 1.5, dive: 3.2, float: 1.7 };
  const FLOAT_AT = INTRO.hold + INTRO.open * 0.6;
  setEra(era0, { wait: reduce ? 0 : FLOAT_AT + INTRO.float * 0.7 });
  // intro: drop in from high above while the town rises
  let opened = !intro, devFade = true; // walls may fade only once the box is open
  if (!intro) { lid.rotation.x = LID_OPEN; plate.position.y = PLATE_Y; syncPosts(); camera.position.copy(home.pos); controls.target.copy(home.target); }
  else {
    // outside the box, lid shut, then: lid swings open, a warm glow spills out, the camera dives in to the default view
    camera.position.set(86, 74, 150); controls.target.set(0, TOP * 0.45, 0); controls.enabled = false;
    tween(INTRO.open, INTRO.hold, k => { lid.rotation.x = -1.98 * (1 - Math.pow(1 - k, 3)) - Math.sin(k * Math.PI) * 0.12; glowLight.intensity = Math.sin(Math.min(1, k * 1.2) * Math.PI) * 900; });
    tween(1.4, INTRO.hold + INTRO.open, k => { lid.rotation.x = -1.98 + (LID_OPEN + 1.98) * (1 - Math.pow(1 - k, 2)); });
    tween(INTRO.float, FLOAT_AT, k => { plate.position.y = PLATE_Y * outBack(k); syncPosts(); }, () => { plate.position.y = PLATE_Y; syncPosts(); });
    tween(0.01, FLOAT_AT + 0.4, () => {}, () => { opened = true; });
    tween(0.01, INTRO.hold + INTRO.open * 0.7, () => {}, () => { flyTo(home, INTRO.dive, 0, new THREE.Vector3(18, 104, 52)); });
    tween(0.01, INTRO.hold + INTRO.open * 0.7 + INTRO.dive, () => {}, () => { intro = false; timeScale = 1; controls.enabled = true; });
    camera.position.set(86, 74, 150); controls.target.set(0, TOP * 0.45, 0);
    const skip = () => { if (intro) timeScale = 6; };
    el.addEventListener('pointerdown', skip); el.addEventListener('wheel', skip, { passive: true }); addEventListener('keydown', skip);
  }
  const ro = new ResizeObserver(() => { resize(); const want = active >= 0 ? zoneView(active) : home; if (fly) fly.to = want; else if (active >= 0) { camera.position.copy(want.pos); controls.target.copy(want.target); } }); ro.observe(host);

  // ---- labels ----
  const labelLayer = root.querySelector('.ov-labels');
  labelLayer.innerHTML = cats.map((x, i) => `<button class="zone-label" data-i="${i}" style="--i:${i}"><span class="meta">${esc(TYPOLOGY_ZH[x.type])}</span>${esc(x.c.zh)}<small>${x.n}</small></button>`).join('')
    + `<span class="zone-label reserve" aria-hidden="true" style="--i:${cats.length}">待建 · 新分类</span>`;
  const labels = [...labelLayer.querySelectorAll('button')], reserveLabel = labelLayer.querySelector('.reserve');
  let hoverZone = -1;
  labels.forEach((l, i) => { l.onclick = () => focus(i); l.onmouseenter = () => { hoverZone = i; }; l.onmouseleave = () => { hoverZone = -1; }; });

  function focus(i) {
    if (i === active && i >= 0) return;
    active = i;
    root.classList.toggle('focused', i >= 0);
    controls.enableRotate = controls.enableZoom = i < 0; // orbit + wheel only in the overview
    onZone?.(null);
    if (i < 0) { pendingZone = null; flyTo(home, 1.3, 0); return; } // straight pull-back
    pendingZone = i; flyTo(zoneView(i), 1.3, 0); // straight push-in
  }

  // ---- speech bubbles ----
  const LINES = {
    ancient: { person: ['听说宫里在修大殿', '今日市上新到一批陶器', '借过借过～', '去书楼抄书咯', '窑火烧了三天了', '天色不早，快回坊里'], cart: ['驾——', '粮车进城咯', '慢些慢些'] },
    early: { person: ['号外！号外！', '钟楼又敲了三下', '去报馆投稿', '厂里今天加班', '借个火？'], car: ['叭叭！', '让一让，赶电报！', '这车新到的'] },
    modern: { person: ['美术馆新展开幕了', '外卖到了吗', '周末去看展？', '这栋楼好高', '下一站，书局'], car: ['嘀嘀！', '堵车了…', '导航说右转'] },
    future: { person: ['你好，访客', '路径已重新规划', '穹顶湿度 62%'], pod: ['悬浮高度已校准', '正在为你让路', '信息层板更新中', '嗡——'] },
  };
  const bubbles = [];
  const say = (obj, text) => {
    const n = document.createElement('div'); n.className = 'bubble'; n.textContent = text; labelLayer.append(n);
    bubbles.forEach(b => b.obj === obj && (b.until = 0)); bubbles.push({ n, obj, until: t + 2.4 });
  };
  let grab = null;
  const groundHit = e => { cast(e); const p = new THREE.Vector3(); return ray.ray.intersectPlane(new THREE.Plane(new THREE.Vector3(0, 1, 0), -plate.position.y), p) ? p : null; };
  // capture phase so OrbitControls never sees a press that lands on a person, vehicle or bird
  el.addEventListener('pointerdown', e => {
    if (intro || active >= 0 || !fx || e.button !== 0) return;
    cast(e); const hit = ray.intersectObjects(fx.pickables(), true)[0]; if (!hit) return;
    e.stopImmediatePropagation(); el.setPointerCapture(e.pointerId);
    if (fx.isBird(hit.object)) { fx.scatter(); grab = { bird: true, x: e.clientX, y: e.clientY }; return; }
    const m = fx.moverOf(hit.object); if (m) grab = { m, x: e.clientX, y: e.clientY, lifted: false };
  }, { capture: true });
  el.addEventListener('pointermove', e => {
    if (!grab?.m) return;
    if (!grab.lifted && Math.hypot(e.clientX - grab.x, e.clientY - grab.y) > 5) { grab.lifted = true; fx.grab(grab.m); }
    if (grab.lifted) { const p = groundHit(e); if (p) fx.carry(grab.m, p); }
  });
  const release = e => {
    if (!grab) return false;
    const g = grab; grab = null;
    if (g.bird) return true;
    if (g.lifted) { fx.drop(g.m); say(g.m.o, ['哎呀！', '放我下来～', '好高！', '晕…'][Math.floor(Math.random() * 4)]); }
    else { const kind = fx.poke(g.m), pool = LINES[era][kind] ?? LINES[era].person; say(g.m.o, pool[Math.floor(Math.random() * pool.length)]); }
    return true;
  };
  el.addEventListener('pointerup', e => { if (release(e)) e.stopImmediatePropagation(); }, { capture: true });
  el.addEventListener('dblclick', e => {
    const z = pick(e); if (z < 0 || cats[z].type !== 'landmark') return;
    const b = bboxOf[cats[z].c.id]; fx?.firework(new THREE.Vector3((b.min.x + b.max.x) / 2, b.max.y, (b.min.z + b.max.z) / 2));
  });

  // ---- custom cursor: a dot plus a lagging ring whose state follows what is under the pointer ----
  const fine = matchMedia('(pointer: fine)').matches;
  const cur = document.createElement('div'); cur.className = 'ov-cursor'; cur.setAttribute('aria-hidden', 'true'); cur.dataset.state = 'idle';
  cur.innerHTML = '<i class="ring"></i><i class="dot"></i>';
  if (fine) root.append(cur);
  const cp = { x: 0, y: 0, rx: 0, ry: 0, on: false, state: 'idle', down: null };
  const setCursor = st => { if (cp.state !== st) { cp.state = st; cur.dataset.state = st; } };
  el.addEventListener('pointerenter', e => { if (e.pointerType === 'mouse') { cp.on = true; cur.classList.add('on'); } });
  el.addEventListener('pointerleave', () => { cp.on = false; cur.classList.remove('on'); });
  el.addEventListener('pointerdown', e => { cp.down = { x: e.clientX, y: e.clientY }; cur.classList.add('press'); });
  addEventListener('pointerup', () => { cp.down = null; cur.classList.remove('press'); });
  el.addEventListener('pointermove', e => {
    const r = root.getBoundingClientRect(); cp.x = e.clientX - r.left; cp.y = e.clientY - r.top;
    if (!cp.on && e.pointerType === 'mouse') { cp.on = true; cur.classList.add('on'); cp.rx = cp.x; cp.ry = cp.y; }
    if (grab?.lifted) return setCursor('hold');
    if (cp.down && active < 0 && Math.hypot(e.clientX - cp.down.x, e.clientY - cp.down.y) > 4) return setCursor('rotate');
    if (cp.down) return;
    cast(e);
    if (active < 0 && fx && ray.intersectObjects(fx.pickables(), true).length) return setCursor('grab');
    const z = pick(e);
    setCursor(z >= 0 && z !== active ? 'enter' : active >= 0 ? 'back' : 'idle');
  });

  // ---- picking ----
  const ray = new THREE.Raycaster(), ptr = new THREE.Vector2();
  let down = null;
  const cast = e => { const r = el.getBoundingClientRect(); ptr.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1); ray.setFromCamera(ptr, camera); };
  const pick = e => { cast(e); const hit = ray.intersectObjects(town.buildings.map(b => b.group), true)[0]; return hit ? cats.findIndex(x => x.c.id === hit.object.userData.building) : -1; };
  el.addEventListener('pointermove', e => { if (e.pointerType !== 'mouse' || e.buttons) return; hoverZone = pick(e); });
  el.addEventListener('pointerleave', () => { hoverZone = -1; });
  el.addEventListener('pointerdown', e => { down = { x: e.clientX, y: e.clientY }; });
  el.addEventListener('pointerup', e => {
    if (intro || !down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 6) return;
    const z = pick(e);
    if (z >= 0) { focus(z); return; }
    const g = ray.intersectObject(town.group.children[0], false)[0]; if (g) fx?.ripple(g.point);
    if (active >= 0) focus(-1);
  });
  const onKey = e => {
    if (e.target.closest?.('input, select, textarea')) return;
    if (e.key === 'Escape') focus(-1);
    if (e.key === 'ArrowRight') focus((active + 1) % cats.length);
    if (e.key === 'ArrowLeft') focus((active - 1 + cats.length) % cats.length);
  };
  addEventListener('keydown', onKey);

  // ---- loop ----
  const clock = new THREE.Clock(); let raf = 0, t = 0; const v = new THREE.Vector3();
  const place = (node, world) => { v.copy(world).project(camera); const r = el.getBoundingClientRect(); node.style.left = ((v.x + 1) / 2 * r.width) + 'px'; node.style.top = ((1 - v.y) / 2 * r.height) + 'px'; return v.z < 1; };
  function step(dt) {
    t += dt;
    for (let i = tweens.length - 1; i >= 0; i--) { const w = tweens[i]; w.t += dt; if (w.t < 0) continue; const k = Math.min(1, w.t / w.dur); w.fn(k); if (k >= 1) { tweens.splice(i, 1); w.done?.(); } }
    const settled = !tweens.length;
    if (fly) {
      fly.t = Math.min(1, fly.t + dt / (reduce ? 0.01 : fly.dur)); const k = inOut(fly.t);
      if (fly.ctrl) { const a = fly.from.pos, c = fly.ctrl, b = fly.to.pos, u = 1 - k; camera.position.set(u * u * a.x + 2 * u * k * c.x + k * k * b.x, u * u * a.y + 2 * u * k * c.y + k * k * b.y, u * u * a.z + 2 * u * k * c.z + k * k * b.z); }
      else camera.position.lerpVectors(fly.from.pos, fly.to.pos, k);
      camera.position.y += Math.sin(Math.PI * k) * fly.from.pos.distanceTo(fly.to.pos) * fly.arc;
      controls.target.lerpVectors(fly.from.target, fly.to.target, k);
      if (fly.t >= 1) {
        fly = null; limits();
        if (pendingZone !== null && pendingZone === active) { const x = cats[active]; onZone?.(x.c, { typology: TYPOLOGY_ZH[x.type], building: BUILDING_NAME[x.type]?.[era], era: ERAS.find(e => e.id === era) }); pendingZone = null; }
      }
    }
    // hover lift
    town.buildings.forEach((b, bi) => {
      const i = cats.findIndex(x => x.c.id === b.key), want = i >= 0 && (i === hoverZone || i === active) ? 1 : 0;
      b.lift = (b.lift ?? 0) + (want - (b.lift ?? 0)) * Math.min(1, dt * 8);
      if (settled) b.group.scale.setScalar(1 + b.lift * 0.06); // hover: grow in place, never lift
    });
    // rings: hover / selection glow and an expanding pulse under the selected building
    const ri = hoverZone >= 0 ? hoverZone : active;
    if (ri >= 0 && settled) { const { c, r } = ringFor(ri); ring.position.x = c.x; ring.position.z = c.z; ring.scale.setScalar(r * (1 + Math.sin(t * 3) * 0.02)); ringMat.opacity += (0.85 - ringMat.opacity) * Math.min(1, dt * 8); }
    else ringMat.opacity += (0 - ringMat.opacity) * Math.min(1, dt * 8);
    if (active >= 0 && settled) { const { c, r } = ringFor(active), k = (t * 0.6) % 1; ring2.position.x = c.x; ring2.position.z = c.z; ring2.scale.setScalar(r * (1 + k * 0.6)); ring2.material.opacity = 0.6 * (1 - k); }
    else ring2.material.opacity = 0;
    // clock: normal speed, or fast-forward towards a requested time
    if (ffTarget !== null) { const left = ((ffTarget - tod) % 1 + 1) % 1, stepK = Math.min(left, dt * 0.45); tod = (tod + stepK) % 1; if (left - stepK < 1e-4) ffTarget = null; }
    else if (!reduce) tod = (tod + dt / DAY) % 1;
    applyTime();
    if (cp.on) { cp.rx += (cp.x - cp.rx) * Math.min(1, dt * 16); cp.ry += (cp.y - cp.ry) * Math.min(1, dt * 16); cur.style.setProperty('--x', cp.x + 'px'); cur.style.setProperty('--y', cp.y + 'px'); cur.style.setProperty('--rx', cp.rx + 'px'); cur.style.setProperty('--ry', cp.ry + 'px'); }
    { const cdir = v.copy(camera.position).sub(controls.target).setY(0).normalize();
      for (const sd of sides) { const want = opened && devFade && cdir.dot(sd.n) > 0.3 ? 0.16 : 1; sd.k += (want - sd.k) * Math.min(1, dt * 5); sd.mats.forEach(m => { m.opacity = sd.k * (m.userData.base ?? 1); m.depthWrite = m.opacity > 0.95; }); }
      const lw = opened && cdir.z < -0.3 ? 0.16 : 1; lidMats.forEach(m => { const want = lw * (m.userData.base ?? 1); m.opacity += (want - m.opacity) * Math.min(1, dt * 5); m.depthWrite = m.opacity > 0.95; }); }
    dressTick?.(t, dt);
    fx?.update(t, dt);
    for (let i = fading.length - 1; i >= 0; i--) { const f = fading[i]; f.update(t, dt); if (f.done) { f.dispose(); fading.splice(i, 1); } }
    controls.update(); renderer.render(scene, camera);
    for (let k = bubbles.length - 1; k >= 0; k--) {
      const b = bubbles[k]; b.obj.getWorldPosition(v);
      const jumped = b.last && b.last.distanceToSquared(v) > 9; // the speaker moved too far in one frame: drop the bubble
      if (jumped || !b.obj.visible || b.obj.scale.x < 0.5) b.until = Math.min(b.until, t);
      (b.last ??= new THREE.Vector3()).copy(v);
      if (t >= b.until) { b.n.classList.add('out'); if (t > b.until + 0.35 || jumped || !b.obj.visible) { b.n.remove(); bubbles.splice(k, 1); } continue; }
      v.y += 2.2; place(b.n, v);
    }
    town.buildings.forEach((b, bi) => {
      const i = cats.findIndex(x => x.c.id === b.key), node = i >= 0 ? labels[i] : reserveLabel;
      const visible = place(node, v.set(b.group.position.x, bboxOf[b.key].max.y + 1.4 + plate.position.y + Math.sin(t * 1.6 + bi) * 0.25, b.group.position.z));
      node.classList.toggle('hover', i >= 0 && i === hoverZone);
      node.classList.toggle('shown', visible && active < 0 && settled);
      node.style.pointerEvents = active >= 0 ? 'none' : '';
    });
  }
  function tick() { raf = requestAnimationFrame(tick); step(Math.min(clock.getDelta(), 0.05) * timeScale); }
  tick();
  root.querySelector('.ov-loading')?.remove();
  window.__ov = { settle: (n = 80) => { for (let i = 0; i < n; i++) step(0.05); }, camera, controls, get fx() { return fx; }, get lid() { return lid; }, get intro() { return intro; }, get info() { return renderer.info.render; }, get scene() { return scene; }, set tod(v) { tod = v; applyTime(); }, set fade(v) { devFade = v; } }; // dev hook: advance frames when the tab is hidden

  return {
    eras: ERAS, setEra: id => { if (switching || intro || id === era) return false; setEra(id); return true; }, get busy() { return switching || intro; }, get tod() { return tod; }, skipTo(target) { if (reduce) { tod = target; applyTime(); } else ffTarget = target; }, home: () => focus(-1), focus: id => focus(cats.findIndex(x => x.c.id === id)),
    dispose() { cancelAnimationFrame(raf); ro.disconnect(); removeEventListener('keydown', onKey); controls.dispose(); fx?.dispose(); fading.forEach(f => f.dispose()); if (town) disposeGroup(town.group); pmrem.dispose(); envTex.dispose(); ringGeo.dispose(); ringMat.dispose(); ring2.material.dispose(); renderer.dispose(); el.remove(); cur.remove(); },
  };
}
