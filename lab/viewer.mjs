// GLB inspection viewer: studio lighting (environment map + filmic tone mapping + contact shadow) plus review tools —
// view modes, light presets and colours, exposure, background, grid, bounding box, camera presets, screenshots.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export const DEFAULT_LOOK = {
  view: 'shaded', preset: 'studio',
  key: 2.2, keyColor: '#fff4e6', az: 35, el: 52,
  fill: 0, fillColor: '#cfd9ea', env: 0.9, exposure: 1,
  bg: '#2a2926', shadow: true, grid: false, bbox: false, spin: true,
};
export const LIGHT_PRESETS = {
  studio: { label: '影棚', key: 2.2, keyColor: '#fff4e6', az: 35, el: 52, fill: 0, fillColor: '#cfd9ea', env: 0.9, exposure: 1 },
  noon: { label: '正午', key: 3.2, keyColor: '#ffffff', az: 10, el: 78, fill: 0.45, fillColor: '#cfe3ff', env: 0.55, exposure: 1 },
  dusk: { label: '黄昏', key: 2.6, keyColor: '#ffb06a', az: 250, el: 12, fill: 0.4, fillColor: '#6d7fb8', env: 0.35, exposure: 1.05 },
  night: { label: '夜晚', key: 1, keyColor: '#9fb7ff', az: 140, el: 40, fill: 0.3, fillColor: '#34406b', env: 0.12, exposure: 1.25 },
  flat: { label: '平光', key: 0.5, keyColor: '#ffffff', az: 35, el: 60, fill: 0.7, fillColor: '#ffffff', env: 1.4, exposure: 1 },
};
export const VIEWS = [['shaded', '实体'], ['clay', '白模'], ['wire', '线框'], ['solidwire', '实体+线'], ['normal', '法线'], ['uv', 'UV']];

function checker() {
  const c = document.createElement('canvas'); c.width = c.height = 512; const x = c.getContext('2d');
  for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) { x.fillStyle = (i + j) % 2 ? '#2b2b2b' : '#e8e3d8'; x.fillRect(i * 64, j * 64, 64, 64); }
  x.fillStyle = '#c8412f'; x.font = '600 22px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
  for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) x.fillText(String.fromCharCode(65 + i) + (j + 1), i * 64 + 32, j * 64 + 32);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8; return t;
}

export async function createViewer(host) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute('aria-label', '3D 模型：拖动旋转，右键平移，滚轮缩放');
  host.append(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  const key = new THREE.DirectionalLight(0xffffff, 2);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.02;
  const fill = new THREE.HemisphereLight(0xffffff, 0x2a2622, 0);
  scene.add(key, key.target, fill);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShadowMaterial({ opacity: 0.28 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  let grid = null, bbox = null;

  const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.dampingFactor = 0.08; controls.autoRotateSpeed = 0.6;
  controls.addEventListener('start', () => { if (look.spin) { look.spin = false; controls.autoRotate = false; onChange?.({ ...look }); } });

  const MAT = {
    clay: new THREE.MeshStandardMaterial({ color: 0xd9d4ca, roughness: 0.82, metalness: 0 }),
    wire: new THREE.MeshBasicMaterial({ color: 0x26221e, wireframe: true }),
    normal: new THREE.MeshNormalMaterial(),
    uv: new THREE.MeshBasicMaterial({ map: checker() }),
    overlay: new THREE.MeshBasicMaterial({ color: 0x111111, wireframe: true, transparent: true, opacity: 0.35, depthTest: true, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 }),
  };
  const look = { ...DEFAULT_LOOK };
  let root = null, home = null, raf = 0, token = 0, fit = { c: new THREE.Vector3(), r: 1, s: new THREE.Vector3(), min: new THREE.Vector3() }, onChange = null, info = null;
  const loader = new GLTFLoader();
  const size = () => { const { clientWidth: w, clientHeight: h } = host; if (!w || !h) return; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); };
  const ro = new ResizeObserver(size); ro.observe(host); size();

  const disposeTree = o => o?.traverse(n => { n.geometry?.dispose(); [].concat(n.userData.orig || n.material || []).filter(m => !Object.values(MAT).includes(m)).forEach(m => { Object.values(m).forEach(t => t?.isTexture && t.dispose()); m.dispose(); }); });
  const isDark = hex => { const c = new THREE.Color(hex); return c.r * 0.3 + c.g * 0.59 + c.b * 0.11 < 0.45; };

  function placeKey() {
    const { c, r } = fit, az = THREE.MathUtils.degToRad(look.az), el = THREE.MathUtils.degToRad(look.el), d = r * 3.2;
    key.position.set(c.x + Math.sin(az) * Math.cos(el) * d, c.y + Math.sin(el) * d, c.z + Math.cos(az) * Math.cos(el) * d);
    key.target.position.copy(c);
  }
  function helpers() {
    grid?.removeFromParent(); grid?.geometry.dispose(); grid?.material.dispose(); grid = null;
    bbox?.removeFromParent(); bbox?.geometry.dispose(); bbox?.material.dispose(); bbox = null;
    if (!root) return;
    const dark = isDark(look.bg);
    if (look.grid) {
      const span = Math.pow(10, Math.ceil(Math.log10(fit.r * 4))); // round metres
      grid = new THREE.GridHelper(span, 20, dark ? 0x8a857c : 0x6d675e, dark ? 0x4a4741 : 0xbdb6a8);
      grid.position.set(fit.c.x, fit.min.y + fit.r * 0.001, fit.c.z); scene.add(grid);
    }
    if (look.bbox) { bbox = new THREE.Box3Helper(new THREE.Box3().setFromObject(root), dark ? 0xe0b86a : 0xa8402f); scene.add(bbox); }
  }
  function apply() {
    key.intensity = look.key; key.color.set(look.keyColor); key.castShadow = look.shadow;
    fill.intensity = look.fill; fill.color.set(look.fillColor);
    scene.environmentIntensity = look.env; renderer.toneMappingExposure = look.exposure;
    scene.background.set(look.bg);
    placeKey();
    const mat = { clay: MAT.clay, wire: MAT.wire, normal: MAT.normal, uv: MAT.uv }[look.view];
    root?.traverse(n => { if (!n.isMesh) return; n.userData.orig ??= n.material; n.material = mat || n.userData.orig; });
    ground.visible = look.shadow && ['shaded', 'clay', 'solidwire'].includes(look.view);
    MAT.wire.color.set(isDark(look.bg) ? 0xe9e2d3 : 0x26221e);
    MAT.overlay.color.set(isDark(look.bg) ? 0xffffff : 0x111111);
    controls.autoRotate = look.spin;
    helpers();
  }

  async function load(url) {
    const my = ++token;
    const gltf = await loader.loadAsync(url);
    if (my !== token) { disposeTree(gltf.scene); return; }
    if (root) { scene.remove(root); disposeTree(root); }
    root = gltf.scene;
    const st = { triangles: 0, vertices: 0, meshes: 0, materials: new Set(), textures: new Set() };
    root.traverse(n => {
      if (!n.isMesh) return;
      n.castShadow = true; n.receiveShadow = true; st.meshes++;
      const g = n.geometry, count = g.index ? g.index.count : g.attributes.position.count;
      st.triangles += count / 3 * (n.isInstancedMesh ? n.count : 1); st.vertices += g.attributes.position.count;
      [].concat(n.material).forEach(m => { st.materials.add(m); Object.values(m).forEach(t => t?.isTexture && st.textures.add(t)); });
    });
    scene.add(root);
    const box = new THREE.Box3().setFromObject(root), c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3());
    const r = Math.max(s.length() / 2, 0.01);
    fit = { c: c.clone(), r, s, min: box.min.clone() };
    info = { triangles: Math.round(st.triangles), vertices: st.vertices, meshes: st.meshes, materials: st.materials.size, textures: st.textures.size, size: [s.x, s.y, s.z] };
    ground.position.set(c.x, box.min.y - r * 0.002, c.z); ground.scale.setScalar(r * 8);
    const sc = key.shadow.camera; sc.left = sc.bottom = -r * 1.6; sc.right = sc.top = r * 1.6; sc.near = r * 0.1; sc.far = r * 8; sc.updateProjectionMatrix();
    camera.near = r / 200; camera.far = r * 60; camera.updateProjectionMatrix();
    controls.minDistance = r * 0.3; controls.maxDistance = r * 8;
    home = view3('persp', true);
    apply(); reset(); renderer.render(scene, camera);
    return info;
  }

  // camera presets: front / side / top / three-quarter; always framing the whole model
  function view3(kind, only) {
    const dist = fit.r / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2)) * 1.05;
    const dir = { front: [0, 0.08, 1], side: [1, 0.08, 0], top: [0.0001, 1, 0.0001], back: [0, 0.08, -1], persp: [0.75, 0.42, 1] }[kind] || [0.75, 0.42, 1];
    const v = { target: fit.c.clone(), pos: fit.c.clone().add(new THREE.Vector3(...dir).normalize().multiplyScalar(dist)) };
    if (!only) { fly = { from: { pos: camera.position.clone(), target: controls.target.clone() }, to: v, t: 0 }; }
    return v;
  }
  let fly = null;
  const reset = () => { if (!home) return; fly = null; camera.position.copy(home.pos); controls.target.copy(home.target); controls.update(); };
  renderer.domElement.addEventListener('keydown', e => {
    const k = e.key.toLowerCase();
    if (k === 'r') reset();
    else if (k === 'f') view3('front'); else if (k === 's') view3('side'); else if (k === 't') view3('top');
    else if (k === 'g') { look.grid = !look.grid; apply(); onChange?.({ ...look }); }
    else if (k === 'b') { look.bbox = !look.bbox; apply(); onChange?.({ ...look }); }
    else if (/^[1-6]$/.test(k)) { look.view = VIEWS[+k - 1][0]; apply(); onChange?.({ ...look }); }
  });

  function render() {
    renderer.render(scene, camera);
    if (look.view === 'solidwire' && root) { // second pass: wire overlay on top of the shaded model
      const vis = [ground.visible, grid?.visible, bbox?.visible];
      ground.visible = false; if (grid) grid.visible = false; if (bbox) bbox.visible = false;
      const bg = scene.background; scene.background = null; scene.overrideMaterial = MAT.overlay; renderer.autoClear = false;
      renderer.render(scene, camera);
      renderer.autoClear = true; scene.overrideMaterial = null; scene.background = bg;
      [ground.visible] = vis; if (grid) grid.visible = vis[1]; if (bbox) bbox.visible = vis[2];
    }
  }
  (function frame() {
    raf = requestAnimationFrame(frame);
    if (document.hidden) return;
    if (fly) { fly.t = Math.min(1, fly.t + 1 / 40); const k = fly.t * fly.t * (3 - 2 * fly.t); camera.position.lerpVectors(fly.from.pos, fly.to.pos, k); controls.target.lerpVectors(fly.from.target, fly.to.target, k); if (fly.t >= 1) fly = null; }
    controls.update(); render();
  })();

  return {
    load, reset,
    set(opts = {}) { Object.assign(look, opts); apply(); return { ...look }; },
    get look() { return { ...look }; },
    get info() { return info; },
    view: kind => { view3(kind); },
    onChange: fn => { onChange = fn; },
    screenshot(scale = 2) { // PNG at up to 2× the canvas size
      const w = renderer.domElement.width, h = renderer.domElement.height, pr = renderer.getPixelRatio();
      renderer.setPixelRatio(Math.min(pr * scale, 4)); size(); render();
      const url = renderer.domElement.toDataURL('image/png');
      renderer.setPixelRatio(pr); size(); render();
      return { url, w: w * scale, h: h * scale };
    },
    dispose() { token++; cancelAnimationFrame(raf); ro.disconnect(); controls.dispose(); look.grid = look.bbox = false; helpers(); disposeTree(root); Object.values(MAT).forEach(m => { m.map?.dispose(); m.dispose(); }); pmrem.dispose(); scene.environment?.dispose(); renderer.dispose(); renderer.domElement.remove(); },
  };
}
