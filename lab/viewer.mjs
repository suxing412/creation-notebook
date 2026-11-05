// Lightweight GLB viewer with studio lighting (environment map + filmic tone mapping + contact shadow).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export async function createViewer(host) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute('aria-label', '3D 模型，拖动旋转，R 复位');
  host.append(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x2a2926);
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.9;

  const key = new THREE.DirectionalLight(0xfff4e6, 2.2);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.02;
  scene.add(key, key.target);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShadowMaterial({ opacity: 0.28 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);

  const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.dampingFactor = 0.08; controls.autoRotate = true; controls.autoRotateSpeed = 0.6;
  controls.addEventListener('start', () => { controls.autoRotate = false; });

  let root = null, home = null, raf = 0, token = 0, fit = { c: new THREE.Vector3(), r: 1 };
  const look = { view: 'shaded', key: 2.2, az: 35, el: 52, env: 0.9, bg: '#2a2926' };
  const loader = new GLTFLoader();
  const size = () => { const { clientWidth: w, clientHeight: h } = host; if (!w || !h) return; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); };
  const ro = new ResizeObserver(size); ro.observe(host); size();
  const reset = () => { if (!home) return; camera.position.copy(home.pos); controls.target.copy(home.target); controls.update(); };
  renderer.domElement.addEventListener('keydown', e => { if (e.key === 'r' || e.key === 'R') reset(); });

  const disposeTree = o => o?.traverse(n => { n.geometry?.dispose(); [].concat(n.userData.orig || n.material || []).filter(m => !Object.values(VIEW).includes(m)).forEach(m => { Object.values(m).forEach(t => t?.isTexture && t.dispose()); m.dispose(); }); });

  async function load(url) {
    const my = ++token;
    const gltf = await loader.loadAsync(url);
    if (my !== token) { disposeTree(gltf.scene); return; }
    if (root) { scene.remove(root); disposeTree(root); }
    root = gltf.scene;
    root.traverse(n => { if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; } });
    scene.add(root);
    const box = new THREE.Box3().setFromObject(root), c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3());
    const r = Math.max(s.length() / 2, 0.01);
    ground.position.set(c.x, box.min.y - r * 0.002, c.z); ground.scale.setScalar(r * 8);
    fit = { c: c.clone(), r }; placeKey(); key.target.position.copy(c);
    const sc = key.shadow.camera; sc.left = sc.bottom = -r * 1.6; sc.right = sc.top = r * 1.6; sc.near = r * 0.1; sc.far = r * 8; sc.updateProjectionMatrix();
    camera.near = r / 200; camera.far = r * 60; camera.updateProjectionMatrix();
    const dist = r / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2)) * 1.05;
    home = { target: c.clone(), pos: c.clone().add(new THREE.Vector3(0.75, 0.42, 1).normalize().multiplyScalar(dist)) };
    controls.minDistance = r * 0.3; controls.maxDistance = r * 8; controls.autoRotate = true;
    applyView(); reset(); renderer.render(scene, camera);
  }

  // ---- inspection: view modes, light, background ----
  const VIEW = {
    clay: new THREE.MeshStandardMaterial({ color: 0xd9d4ca, roughness: 0.82, metalness: 0 }),
    wire: new THREE.MeshBasicMaterial({ color: 0x26221e, wireframe: true }),
    normal: new THREE.MeshNormalMaterial(),
  };
  function placeKey() {
    const { c, r } = fit, az = THREE.MathUtils.degToRad(look.az), el = THREE.MathUtils.degToRad(look.el), d = r * 3.2;
    key.position.set(c.x + Math.sin(az) * Math.cos(el) * d, c.y + Math.sin(el) * d, c.z + Math.cos(az) * Math.cos(el) * d);
  }
  function applyView() {
    root?.traverse(n => {
      if (!n.isMesh) return;
      n.userData.orig ??= n.material;
      n.material = look.view === 'shaded' ? n.userData.orig : VIEW[look.view];
    });
    ground.visible = look.view === 'shaded' || look.view === 'clay';
    scene.background.set(look.bg);
    VIEW.wire.color.set(isDark(look.bg) ? 0xe9e2d3 : 0x26221e); // wire lines contrast with whatever background is chosen
  }
  const isDark = hex => { const c = new THREE.Color(hex); return c.r * 0.3 + c.g * 0.59 + c.b * 0.11 < 0.45; };
  function set(opts = {}) {
    Object.assign(look, opts);
    key.intensity = look.key; scene.environmentIntensity = look.env; placeKey(); applyView();
    return { ...look };
  }

  (function frame() { raf = requestAnimationFrame(frame); if (!document.hidden) { controls.update(); renderer.render(scene, camera); } })();

  return {
    load, reset, set, get look() { return { ...look }; },
    dispose() { token++; Object.values(VIEW).forEach(m => m.dispose()); cancelAnimationFrame(raf); ro.disconnect(); controls.dispose(); disposeTree(root); pmrem.dispose(); scene.environment?.dispose(); renderer.dispose(); renderer.domElement.remove(); },
  };
}
