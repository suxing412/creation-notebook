import { bindDetailTabs } from './detail-tabs.mjs';
import { bindBackground, applySceneBackground } from './background-ui.mjs';
import { bindViewerUI } from './viewer-ui.mjs';

const select = document.getElementById('asset-select');
const host = document.getElementById('viewer');
const badge = document.getElementById('scene-badge');
const ui = bindViewerUI();
let generation = 0;
let active = null;
let request = null;
const background = bindBackground(color => active?.setBackground?.(color));
bindDetailTabs();

function disposeObject(object) {
  const resources = new Set();
  const bitmaps = new Set();
  object?.traverse(node => {
    if (node.geometry) resources.add(node.geometry);
    if (node.skeleton) resources.add(node.skeleton);
    const materials = Array.isArray(node.material) ? node.material : [node.material];
    for (const material of materials) {
      if (!material) continue;
      resources.add(material);
      for (const texture of Object.values(material)) {
        if (texture?.isTexture) resources.add(texture);
      }
    }
  });
  for (const resource of resources) {
    if (!resource.isTexture) continue;
    const images = [resource.source?.data, resource.image].flat();
    for (const image of images) {
      if (typeof ImageBitmap !== 'undefined' && image instanceof ImageBitmap) {
        bitmaps.add(image);
      }
    }
  }
  for (const resource of resources) resource.dispose();
  // Texture.dispose() frees GPU storage. Decoded ImageBitmap storage is separate.
  for (const bitmap of bitmaps) bitmap.close();
}

function close(message = '已切回模型预览图，随时可以重新打开三维模型。') {
  generation++;
  request?.abort();
  request = null;
  active?.dispose();
  active = null;
  host.hidden = true;
  host.replaceChildren();
  badge.textContent = '模型预览图';
  ui('closed', message);
}

async function load() {
  close();
  ui('preparing');
  const token = generation;
  const modelURL = new URL(select.value, location.href);
  const modelLabel = select.selectedOptions[0].textContent;
  const controller = new AbortController();
  request = controller;
  let renderer;
  let controls;
  let root;
  let scene;
  let environment;
  let ground;
  let keyLight;
  let frameId;
  let resize;

  function onContextLost(event) {
    event.preventDefault();
    if (token === generation) {
      close('三维画面已中断，当前显示模型预览图。可以重新加载。');
    }
  }

  function cleanup() {
    cancelAnimationFrame(frameId);
    resize?.disconnect();
    controls?.dispose();
    disposeObject(root);
    disposeObject(ground);
    keyLight?.shadow.dispose();
    if (scene) scene.environment = null;
    environment?.dispose();
    if (renderer) {
      renderer.domElement.removeEventListener('webglcontextlost', onContextLost);
      renderer.domElement.onkeydown = null;
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
    }
    // A cancelled parse may still return a model later. Clearing each resource
    // lets the stale-result path release that late model on a second cleanup.
    resize = controls = root = ground = keyLight = environment = renderer = scene = null;
  }

  try {
    const [T, { GLTFLoader }, { OrbitControls }, { RoomEnvironment }] = await Promise.all([
      import('three'),
      import('../fusions/F01/vendor/addons/loaders/GLTFLoader.js'),
      import('../fusions/F01/vendor/addons/controls/OrbitControls.js'),
      import('../fusions/F01/vendor/addons/environments/RoomEnvironment.js')
    ]);
    if (token !== generation) return;

    renderer = new T.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
    renderer.outputColorSpace = T.SRGBColorSpace;
    renderer.toneMapping = T.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.85;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = T.PCFSoftShadowMap;
    // Model geometry and lights stay fixed while the user orbits the camera.
    renderer.shadowMap.autoUpdate = false;
    renderer.shadowMap.needsUpdate = true;
    renderer.domElement.tabIndex = 0;
    renderer.domElement.setAttribute('aria-label', '实时模型。方向键旋转，正负号缩放，R复位，Esc关闭');
    renderer.domElement.addEventListener('webglcontextlost', onContextLost);
    active = { dispose: cleanup };

    ui('downloading');
    const response = await fetch(modelURL, { signal: controller.signal });
    if (!response.ok) throw new Error('模型资源 HTTP ' + response.status);
    const bytes = await response.arrayBuffer();
    if (token !== generation) {
      cleanup();
      return;
    }

    ui('parsing');
    const gltf = await new GLTFLoader().parseAsync(bytes, new URL('.', modelURL).href);
    root = gltf.scene;
    if (token !== generation) {
      cleanup();
      return;
    }

    scene = new T.Scene();
    applySceneBackground(scene, T.Color, background.value);
    scene.add(root);
    const box = new T.Box3().setFromObject(root);
    const center = box.getCenter(new T.Vector3());
    const radius = Math.max(box.getSize(new T.Vector3()).length(), 0.1);
    const camera = new T.PerspectiveCamera(42, 1, Math.max(radius / 10000, 0.001), radius * 100);
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    const viewDirection = new T.Vector3(0.8, 0.55, 0.8).normalize();
    function getFitDistance(aspect) {
      const verticalHalfFov = T.MathUtils.degToRad(camera.fov) / 2;
      const horizontalHalfFov = Math.atan(Math.tan(verticalHalfFov) * aspect);
      const limitingHalfFov = Math.min(verticalHalfFov, horizontalHalfFov);
      return (radius * 0.5 / Math.sin(limitingHalfFov)) * 1.08;
    }
    let fitDistance = getFitDistance(camera.aspect);
    function reset() {
      camera.position.copy(center).addScaledVector(viewDirection, fitDistance);
      controls.target.copy(center);
      controls.update();
    }
    reset();

    // Studio reflections give metals readable highlights without changing the
    // model's materials. The chosen background remains independent of lighting.
    const pmrem = new T.PMREMGenerator(renderer);
    let room;
    try {
      room = new RoomEnvironment();
      environment = pmrem.fromScene(room, 0.04);
      scene.environment = environment.texture;
      scene.environmentIntensity = 0.75;
    } finally {
      room?.dispose();
      pmrem.dispose();
    }

    scene.add(new T.HemisphereLight(0xfff6e8, 0x4b555b, 0.35));
    keyLight = new T.DirectionalLight(0xfff3df, 2);
    keyLight.position.copy(center).add(new T.Vector3(-radius * 0.8, radius * 1.4, radius * 0.65));
    keyLight.target.position.copy(center);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(1024, 1024);
    const shadowCamera = keyLight.shadow.camera;
    shadowCamera.left = shadowCamera.bottom = -radius * 0.65;
    shadowCamera.right = shadowCamera.top = radius * 0.65;
    shadowCamera.near = radius * 0.1;
    shadowCamera.far = radius * 4;
    shadowCamera.updateProjectionMatrix();
    keyLight.shadow.normalBias = radius * 0.001;
    keyLight.shadow.bias = -0.0001;
    scene.add(keyLight, keyLight.target);
    const fill = new T.DirectionalLight(0xdce8ff, 0.5);
    fill.position.copy(center).add(new T.Vector3(radius, radius * 0.4, -radius));
    fill.target.position.copy(center);
    scene.add(fill, fill.target);
    root.traverse(node => {
      if (node.isMesh) {
        node.castShadow = true;
        node.receiveShadow = true;
      }
    });

    ground = new T.Mesh(
      new T.PlaneGeometry(radius * 2, radius * 2),
      new T.ShadowMaterial({ color: 0x1d251f, opacity: 0.26, depthWrite: false })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.set(center.x, box.min.y - radius * 0.002, center.z);
    ground.receiveShadow = true;
    scene.add(ground);

    host.hidden = false;
    host.append(renderer.domElement);
    let previousWidth = 0;
    let previousHeight = 0;
    function size() {
      const width = host.clientWidth;
      const height = host.clientHeight;
      if (!width || !height || !renderer) return;
      if (width === previousWidth && height === previousHeight) return;
      previousWidth = width;
      previousHeight = height;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      const nextFitDistance = getFitDistance(camera.aspect);
      // Keep the user's orbit, pan and relative zoom while fitting a new viewport.
      camera.position.sub(controls.target).multiplyScalar(nextFitDistance / fitDistance).add(controls.target);
      fitDistance = nextFitDistance;
      controls.update();
    }
    resize = new ResizeObserver(size);
    resize.observe(host);
    size();
    active = {
      dispose: cleanup,
      reset,
      setBackground: color => applySceneBackground(scene, T.Color, color)
    };

    renderer.domElement.onkeydown = event => {
      const keys = ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '=', '-', 'r', 'R', 'Escape'];
      if (!keys.includes(event.key)) return;
      event.preventDefault();
      if (event.key === 'Escape') {
        close();
        document.getElementById('load3d').focus();
        return;
      }
      if (event.key.toLowerCase() === 'r') {
        reset();
        return;
      }
      const offset = camera.position.clone().sub(controls.target);
      if (event.key.startsWith('Arrow')) {
        const spherical = new T.Spherical().setFromVector3(offset);
        const horizontal = { ArrowLeft: 0.12, ArrowRight: -0.12 };
        const vertical = { ArrowUp: -0.12, ArrowDown: 0.12 };
        spherical.theta += horizontal[event.key] || 0;
        spherical.phi = Math.max(0.08, Math.min(Math.PI - 0.08, spherical.phi + (vertical[event.key] || 0)));
        offset.setFromSpherical(spherical);
      } else {
        offset.multiplyScalar(event.key === '-' ? 1.12 : 0.88);
      }
      camera.position.copy(controls.target).add(offset);
      controls.update();
    };

    badge.textContent = '三维模型 · ' + modelLabel;
    request = null;
    ui('ready');
    function frame() {
      if (token !== generation) return;
      if (!document.hidden && !host.closest('[hidden]')) {
        controls.update();
        renderer.render(scene, camera);
      }
      frameId = requestAnimationFrame(frame);
    }
    frame();
  } catch (error) {
    cleanup();
    if (token !== generation || error.name === 'AbortError') return;
    active = null;
    request = null;
    host.hidden = true;
    badge.textContent = '模型预览图 · 可重新加载三维模型';
    const message = /WebGL|context/i.test(error.message)
      ? '当前浏览器无法显示三维模型。作品介绍里可以查看预览图和下载模型。'
      : '模型加载失败，请重新加载。原因 ' + error.message;
    ui('error', message);
  }
}

document.getElementById('load3d').onclick = load;
document.getElementById('close3d').onclick = () => close();
document.getElementById('reset3d').onclick = () => active?.reset();
select.onchange = load;
addEventListener('pagehide', () => close());
load();
