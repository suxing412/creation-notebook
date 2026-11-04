import * as THREE from '../../fusions/F01/vendor/three.module.js';
import { GLTFLoader } from '../../fusions/F01/vendor/addons/loaders/GLTFLoader.js';
import { OrbitControls } from '../../fusions/F01/vendor/addons/controls/OrbitControls.js';
import {
  surfaceVertex, surfaceFragment, normalFragment,
  hullVertex, hullFragment, pageVertex, pageFragment
} from './shaders.mjs';

const DEFAULT_MODEL = new URL('../../cities/luoyang/assets/r01/R01-A-LOD0-prototype.glb', import.meta.url);
const PALETTE = {
  C_yard: '#d5c49e',
  C_compacted_activity_ground: '#c6b48d',
  C_whitebox_earth_wall: '#c2a17d',
  C_roof_rhythm_not_glaze_copy: '#879e98',
  C_plain_timber: '#846349',
  C_floor_plinth: '#afa58c'
};

function outlineGeometry(original) {
  const geometry = original.clone();
  const positions = geometry.getAttribute('position');
  const normals = geometry.getAttribute('normal');
  const combined = new Map();
  const keys = [];
  // The GLB has hard-normal vertex splits. A separate smooth extrusion normal
  // closes hull corner seams without changing the source or its flat shading.
  for (let i = 0; i < positions.count; i++) {
    const key = [positions.getX(i), positions.getY(i), positions.getZ(i)]
      .map(value => Math.round(value * 10000)).join(',');
    keys.push(key);
    if (!combined.has(key)) combined.set(key, new THREE.Vector3());
    combined.get(key).add(new THREE.Vector3(normals.getX(i), normals.getY(i), normals.getZ(i)));
  }
  for (const normal of combined.values()) normal.normalize();
  const smooth = new Float32Array(positions.count * 3);
  for (let i = 0; i < positions.count; i++) combined.get(keys[i]).toArray(smooth, i * 3);
  geometry.setAttribute('outlineNormal', new THREE.BufferAttribute(smooth, 3));
  return geometry;
}

export async function createPrototype({
  canvas, modelUrl = DEFAULT_MODEL, onMetrics = () => {}, onStatus = () => {}, signal
}) {
  const options = { brush: 'ink', method: 'compare', lineWidth: 1.4, paperStrength: 0.35 };
  const controller = new AbortController();
  const resources = new Set();
  const bitmaps = new Set();
  const flatMaterials = [];
  let renderer;
  let controls;
  let resizeObserver;
  let pendingFrame = 0;
  let disposed = false;
  let contextLost = false;
  let lastMetrics = {};
  let downloadBytes = 0;
  let width = 0;
  let height = 0;
  let panelWidth = 0;
  let camera;
  let center;
  let sphereRadius;
  let root;
  let colourTarget;
  let geometryTarget;
  let hullMaterial;
  let paperMaterial;
  let scene;
  let hulls;
  let normalMaterial;
  let paperScene;
  const paperCamera = new THREE.Camera();
  const light = new THREE.Vector3(-0.6, 1, 0.75).normalize();
  const viewLight = new THREE.Vector3();
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);

  function trackObject(object) {
    object.traverse(node => {
      if (node.geometry) resources.add(node.geometry);
      for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
        if (!material) continue;
        resources.add(material);
        for (const value of Object.values(material)) {
          if (!value?.isTexture) continue;
          resources.add(value);
          const images = [value.source?.data, value.image].flat();
          for (const image of images) {
            if (typeof ImageBitmap !== 'undefined' && image instanceof ImageBitmap) bitmaps.add(image);
          }
        }
      }
    });
  }

  function dispose() {
    disposed = true;
    controller.abort();
    cancelAnimationFrame(pendingFrame);
    resizeObserver?.disconnect();
    controls?.dispose();
    document.removeEventListener('visibilitychange', requestRender);
    window.removeEventListener('resize', resize);
    canvas.removeEventListener('keydown', onKeyDown);
    canvas.removeEventListener('webglcontextlost', onContextLost);
    signal?.removeEventListener('abort', onAbort);
    for (const resource of resources) resource.dispose();
    resources.clear();
    for (const bitmap of bitmaps) bitmap.close();
    bitmaps.clear();
    if (renderer) {
      renderer.dispose();
      renderer.forceContextLoss();
      renderer = null;
    }
  }

  function onAbort() { dispose(); }
  function onContextLost(event) {
    event.preventDefault();
    contextLost = true;
    cancelAnimationFrame(pendingFrame);
    onStatus('三维画面已中断，可以重新打开原型。');
    onMetrics({ ...lastMetrics, contextLost: true });
  }

  function fitDistance(aspect) {
    const vertical = THREE.MathUtils.degToRad(camera.fov * 0.5);
    const horizontal = Math.atan(Math.tan(vertical) * aspect);
    return sphereRadius / Math.sin(Math.min(vertical, horizontal)) * 1.04;
  }

  function reset() {
    if (disposed || !controls) return;
    controls.target.copy(center);
    camera.position.copy(center).add(
      new THREE.Vector3(0.85, 0.8, 1.05).normalize().multiplyScalar(fitDistance(camera.aspect))
    );
    camera.lookAt(center);
    controls.update();
    requestRender();
  }

  function replaceTargets(bufferWidth, bufferHeight) {
    const samples = Math.min(4, renderer.capabilities.maxSamples || 0);
    const nextColour = new THREE.WebGLRenderTarget(bufferWidth, bufferHeight, {
      minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, samples
    });
    const nextGeometry = new THREE.WebGLRenderTarget(bufferWidth, bufferHeight, {
      minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, samples
    });
    nextColour.texture.colorSpace = THREE.NoColorSpace;
    nextGeometry.texture.colorSpace = THREE.NoColorSpace;
    nextGeometry.depthTexture = new THREE.DepthTexture(bufferWidth, bufferHeight, THREE.UnsignedIntType);

    // r180 setSize disposes GPU attachments while retaining texture objects.
    // Fresh targets and sampler identities also refresh the resolved MSAA depth
    // attachments when moving between split/single views or browser sizes.
    renderer.setRenderTarget(null);
    const oldTargets = [colourTarget, geometryTarget];
    colourTarget = nextColour;
    geometryTarget = nextGeometry;
    resources.add(colourTarget);
    resources.add(geometryTarget);
    paperMaterial.uniforms.colourMap.value = colourTarget.texture;
    paperMaterial.uniforms.normalMap.value = geometryTarget.texture;
    paperMaterial.uniforms.depthMap.value = geometryTarget.depthTexture;
    paperMaterial.uniformsNeedUpdate = true;
    for (const target of oldTargets) {
      if (!target) continue;
      resources.delete(target);
      target.dispose();
    }
  }

  function resize() {
    if (disposed || !renderer || !camera) return;
    const nextWidth = Math.round(canvas.parentElement.clientWidth);
    const nextHeight = Math.round(canvas.parentElement.clientHeight);
    if (!nextWidth || !nextHeight) return;
    const nextPanel = Math.max(1, options.method === 'compare' ? Math.floor(nextWidth / 2) : nextWidth);
    if (width === nextWidth && height === nextHeight && panelWidth === nextPanel) return;
    const oldDistance = fitDistance(camera.aspect);
    width = nextWidth;
    height = nextHeight;
    panelWidth = nextPanel;
    camera.aspect = panelWidth / height;
    camera.updateProjectionMatrix();
    const offset = camera.position.clone().sub(controls.target);
    camera.position.copy(controls.target).add(offset.multiplyScalar(fitDistance(camera.aspect) / oldDistance));
    renderer.setSize(width, height, false);
    const bufferWidth = Math.max(1, Math.round(panelWidth * pixelRatio));
    const bufferHeight = Math.max(1, Math.round(height * pixelRatio));
    replaceTargets(bufferWidth, bufferHeight);
    hullMaterial.uniforms.resolution.value.set(bufferWidth, bufferHeight);
    paperMaterial.uniforms.resolution.value.set(bufferWidth, bufferHeight);
    requestRender();
  }

  function drawMethod(method, x, viewportWidth) {
    renderer.info.reset();
    hulls.visible = method === 'hull';
    scene.overrideMaterial = null;
    renderer.setRenderTarget(colourTarget);
    renderer.setScissorTest(false);
    renderer.setClearColor(0x000000, 0);
    renderer.clear();
    renderer.render(scene, camera);
    if (method === 'edge') {
      hulls.visible = false;
      scene.overrideMaterial = normalMaterial;
      renderer.setRenderTarget(geometryTarget);
      renderer.setClearColor(0x000000, 0);
      renderer.clear();
      renderer.render(scene, camera);
      scene.overrideMaterial = null;
    }
    paperMaterial.uniforms.detectEdges.value = method === 'edge';
    renderer.setRenderTarget(null);
    renderer.setViewport(x, 0, viewportWidth, height);
    renderer.setScissor(x, 0, viewportWidth, height);
    renderer.setScissorTest(true);
    renderer.render(paperScene, paperCamera);
    return { drawCalls: renderer.info.render.calls, triangles: renderer.info.render.triangles };
  }

  function render() {
    pendingFrame = 0;
    if (disposed || contextLost || document.hidden || !root || !width || !height) return;
    const started = performance.now();
    camera.updateMatrixWorld();
    viewLight.copy(light).transformDirection(camera.matrixWorldInverse);
    for (const material of flatMaterials) material.uniforms.lightDirection.value.copy(viewLight);
    const methods = {};
    if (options.method === 'compare') {
      methods.hull = drawMethod('hull', 0, panelWidth);
      methods.edge = drawMethod('edge', panelWidth, width - panelWidth);
    } else {
      methods[options.method] = drawMethod(options.method, 0, width);
    }
    renderer.setScissorTest(false);
    renderer.setViewport(0, 0, width, height);
    lastMetrics = {
      methods, downloadBytes, renderMs: performance.now() - started,
      pixelRatio, bufferWidth: canvas.width, bufferHeight: canvas.height,
      brush: options.brush, method: options.method, contextLost: false
    };
    onMetrics(lastMetrics);
  }

  function requestRender() {
    if (!disposed && !contextLost && !document.hidden && !pendingFrame && root) {
      pendingFrame = requestAnimationFrame(render);
    }
  }

  function setOptions(changes) {
    if (disposed) return;
    if (['ink', 'pencil'].includes(changes.brush)) options.brush = changes.brush;
    if (['compare', 'hull', 'edge'].includes(changes.method)) options.method = changes.method;
    if (Number.isFinite(changes.lineWidth)) options.lineWidth = THREE.MathUtils.clamp(changes.lineWidth, 0.4, 3.5);
    if (Number.isFinite(changes.paperStrength)) options.paperStrength = THREE.MathUtils.clamp(changes.paperStrength, 0, 1);
    hullMaterial.uniforms.lineWidth.value = options.lineWidth * pixelRatio;
    paperMaterial.uniforms.lineWidth.value = options.lineWidth * pixelRatio;
    paperMaterial.uniforms.paperStrength.value = options.paperStrength;
    paperMaterial.uniforms.pencil.value = options.brush === 'pencil';
    resize();
    requestRender();
  }

  function onKeyDown(event) {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '=', '-', 'r', 'R'].includes(event.key)) return;
    event.preventDefault();
    if (event.key.toLowerCase() === 'r') return reset();
    const offset = camera.position.clone().sub(controls.target);
    if (event.key.startsWith('Arrow')) {
      const spherical = new THREE.Spherical().setFromVector3(offset);
      spherical.theta += ({ ArrowLeft: 0.1, ArrowRight: -0.1 }[event.key] || 0);
      spherical.phi = THREE.MathUtils.clamp(
        spherical.phi + ({ ArrowUp: -0.1, ArrowDown: 0.1 }[event.key] || 0), 0.15, Math.PI * 0.48
      );
      offset.setFromSpherical(spherical);
    } else {
      offset.multiplyScalar(event.key === '-' ? 1.1 : 1 / 1.1);
    }
    camera.position.copy(controls.target).add(offset);
    controls.update();
    requestRender();
  }

  try {
    signal?.throwIfAborted();
    signal?.addEventListener('abort', onAbort, { once: true });
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
    renderer.setPixelRatio(pixelRatio);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.autoClear = false;
    renderer.info.autoReset = false;
    canvas.addEventListener('webglcontextlost', onContextLost);
    onStatus('正在打开院落模型…');
    const response = await fetch(modelUrl, { signal: controller.signal });
    if (!response.ok) throw new Error(`院落模型加载失败（HTTP ${response.status}）`);
    const bytes = await response.arrayBuffer();
    downloadBytes = bytes.byteLength;
    controller.signal.throwIfAborted();
    const gltf = await new GLTFLoader().parseAsync(bytes, new URL('.', new URL(modelUrl, location.href)).href);
    root = gltf.scene;
    trackObject(root);
    if (disposed) {
      dispose();
      throw new DOMException('Rendering cancelled', 'AbortError');
    }
    scene = new THREE.Scene();
    scene.add(root);
    root.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(root);
    center = box.getCenter(new THREE.Vector3());
    sphereRadius = Math.max(box.getSize(new THREE.Vector3()).length() * 0.5, 0.1);
    camera = new THREE.PerspectiveCamera(36, 1, sphereRadius / 100, sphereRadius * 20);
    controls = new OrbitControls(camera, canvas);
    controls.enableDamping = false;
    controls.minPolarAngle = 0.15;
    controls.maxPolarAngle = Math.PI * 0.48;
    controls.minDistance = sphereRadius * 0.6;
    controls.maxDistance = sphereRadius * 12;
    controls.addEventListener('change', requestRender);
    controls.target.copy(center);
    camera.position.copy(center).add(new THREE.Vector3(1, 1, 1).normalize().multiplyScalar(fitDistance(1)));

    hullMaterial = new THREE.ShaderMaterial({
      vertexShader: hullVertex, fragmentShader: hullFragment, side: THREE.BackSide,
      uniforms: {
        resolution: { value: new THREE.Vector2(1, 1) },
        lineWidth: { value: options.lineWidth * pixelRatio },
        ink: { value: new THREE.Color('#4b5148') }
      }
    });
    resources.add(hullMaterial);
    hulls = new THREE.Group();
    const meshes = [];
    root.traverse(node => { if (node.isMesh) meshes.push(node); });
    for (const mesh of meshes) {
      const originals = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      const replacements = originals.map(material => {
        const flat = new THREE.ShaderMaterial({
          vertexShader: surfaceVertex, fragmentShader: surfaceFragment, side: THREE.DoubleSide,
          uniforms: {
            pigment: { value: new THREE.Color(PALETTE[material.name] || '#bba98c') },
            lightDirection: { value: light.clone() }
          }
        });
        resources.add(flat);
        flatMaterials.push(flat);
        return flat;
      });
      mesh.material = Array.isArray(mesh.material) ? replacements : replacements[0];
      const geometry = outlineGeometry(mesh.geometry);
      resources.add(geometry);
      const shell = new THREE.Mesh(geometry, hullMaterial);
      shell.matrixAutoUpdate = false;
      shell.matrix.copy(mesh.matrixWorld);
      shell.renderOrder = -1;
      hulls.add(shell);
    }
    scene.add(hulls);
    normalMaterial = new THREE.ShaderMaterial({
      vertexShader: surfaceVertex, fragmentShader: normalFragment, side: THREE.DoubleSide
    });
    resources.add(normalMaterial);
    paperMaterial = new THREE.ShaderMaterial({
      vertexShader: pageVertex, fragmentShader: pageFragment, depthTest: false, depthWrite: false,
      uniforms: {
        colourMap: { value: null },
        normalMap: { value: null },
        depthMap: { value: null },
        resolution: { value: new THREE.Vector2(1, 1) },
        pixelRatio: { value: pixelRatio },
        lineWidth: { value: options.lineWidth * pixelRatio },
        paperStrength: { value: options.paperStrength },
        cameraNear: { value: camera.near }, cameraFar: { value: camera.far },
        cameraProjectionInverse: { value: camera.projectionMatrixInverse },
        detectEdges: { value: false }, pencil: { value: false },
        paper: { value: new THREE.Color('#f2ead7') }, ink: { value: new THREE.Color('#4b5148') }
      }
    });
    resources.add(paperMaterial);
    const paperGeometry = new THREE.PlaneGeometry(2, 2);
    resources.add(paperGeometry);
    paperScene = new THREE.Scene();
    paperScene.add(new THREE.Mesh(paperGeometry, paperMaterial));
    resize();
    reset();
    resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas.parentElement);
    window.addEventListener('resize', resize);
    document.addEventListener('visibilitychange', requestRender);
    canvas.addEventListener('keydown', onKeyDown);
    canvas.tabIndex = 0;
    onStatus('院落已打开。拖动比较角度，方向键旋转，＋／－缩放，R 复位。');
    render();
    return { setOptions, reset, resize, dispose };
  } catch (error) {
    dispose();
    throw error;
  }
}
