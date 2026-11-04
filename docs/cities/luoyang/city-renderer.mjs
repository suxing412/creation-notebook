import * as THREE from '../../fusions/F01/vendor/three.module.js';
import { GLTFLoader } from '../../fusions/F01/vendor/addons/loaders/GLTFLoader.js';
import { OrbitControls } from '../../fusions/F01/vendor/addons/controls/OrbitControls.js';
import { mergeGeometries } from '../../fusions/F01/vendor/addons/utils/BufferGeometryUtils.js';
import { pageVertex, resolveFragment } from '../../prototypes/luoyang-m0/shaders.mjs';

const surfaceVertex = /* glsl */ `
  varying vec3 vNormal;
  void main() {
    vec3 objectNormal = normal;
    vec4 objectPosition = vec4(position, 1.0);
    #ifdef USE_INSTANCING
      mat3 basis = mat3(instanceMatrix);
      objectNormal /= vec3(dot(basis[0], basis[0]), dot(basis[1], basis[1]), dot(basis[2], basis[2]));
      objectNormal = basis * objectNormal;
      objectPosition = instanceMatrix * objectPosition;
    #endif
    vNormal = normalize(normalMatrix * objectNormal);
    gl_Position = projectionMatrix * modelViewMatrix * objectPosition;
  }
`;

const surfaceFragment = /* glsl */ `
  uniform vec3 pigment;
  uniform vec3 lightDirection;
  uniform bool evidenceVisible;
  uniform bool inferred;
  varying vec3 vNormal;
  void main() {
    vec3 n = normalize(vNormal);
    if (!gl_FrontFacing) n = -n;
    float light = dot(n, lightDirection);
    float band = light > 0.55 ? 1.08 : (light > -0.12 ? 0.90 : 0.69);
    float opacity = evidenceVisible && inferred ? 0.74 : 1.0;
    // Alpha stores pigment strength. Depth still describes the nearest surface.
    gl_FragColor = vec4(pigment * band * opacity, opacity);
  }
`;

const normalFragment = /* glsl */ `
  varying vec3 vNormal;
  void main() {
    vec3 n = normalize(vNormal);
    if (!gl_FrontFacing) n = -n;
    gl_FragColor = vec4(n * 0.5 + 0.5, 1.0);
  }
`;

// M0's depth/normal edge detector, with per-surface evidence rather than a
// global brush. Geometry coverage remains separate from pigment strength.
const cityPageFragment = /* glsl */ `
  uniform sampler2D colourMap;
  uniform sampler2D normalMap;
  uniform sampler2D depthMap;
  uniform vec2 resolution;
  uniform float pixelRatio;
  uniform float lineWidth;
  uniform float paperStrength;
  uniform float cameraNear;
  uniform float cameraFar;
  uniform mat4 cameraProjectionInverse;
  uniform vec3 paper;
  uniform vec3 ink;
  uniform vec3 pencilInk;
  uniform vec3 upDirection;
  varying vec2 vUv;
  float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
  }
  float paperGrain(vec2 p) {
    float fine = hash(floor(p * 1.7)) - 0.5;
    float fibres = hash(vec2(floor(p.x * 0.24), floor(p.y * 1.6))) - 0.5;
    return fine * 0.7 + fibres * 0.3;
  }
  float viewDistance(float depth) {
    return cameraNear * cameraFar / (cameraFar - depth * (cameraFar - cameraNear));
  }
  vec3 viewPosition(vec2 uv, float depth) {
    vec4 p = cameraProjectionInverse * vec4(uv * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    return p.xyz / p.w;
  }
  vec3 decodeNormal(vec4 sampleValue) {
    return normalize(sampleValue.rgb / max(sampleValue.a, 0.0001) * 2.0 - 1.0);
  }
  vec2 boundary(vec4 centerNormal, vec3 centerPosition, float centerDepth, vec2 offset) {
    vec2 uv = clamp(vUv + offset / resolution, vec2(0.0), vec2(1.0));
    vec4 neighbour = texture2D(normalMap, uv);
    float silhouette = abs(centerNormal.a - neighbour.a);
    float bothCovered = step(0.5, centerNormal.a) * step(0.5, neighbour.a);
    vec3 a = decodeNormal(centerNormal);
    vec3 b = decodeNormal(neighbour);
    vec2 support = normalize(offset) * max(0.5 * pixelRatio, 1.0);
    vec4 farA = texture2D(normalMap, clamp(vUv - support / resolution, vec2(0.0), vec2(1.0)));
    vec4 farB = texture2D(normalMap, clamp(uv + support / resolution, vec2(0.0), vec2(1.0)));
    bool broadSurface = farA.a > 0.95 && farB.a > 0.95 && length(decodeNormal(farA) - decodeNormal(farB)) < 0.25;
    float neighbourDepth = texture2D(depthMap, uv).r;
    vec3 neighbourPosition = viewPosition(uv, neighbourDepth);
    vec3 planeNormal = broadSurface ? decodeNormal(farA) : a;
    float planeDistance = abs(dot(neighbourPosition - centerPosition, planeNormal));
    float pixelFootprint = 2.0 * centerDepth * cameraProjectionInverse[1][1] / resolution.y;
    float depthLow = max(centerDepth * 0.0008, pixelFootprint * 0.6);
    float depthHigh = max(centerDepth * 0.0025, pixelFootprint * 1.8);
    float crease = smoothstep(0.25, 0.6, length(a - b));
    if (broadSurface && dot(decodeNormal(farA), upDirection) > 0.97) crease = 0.0;
    float edge = max(silhouette, max(crease, smoothstep(depthLow, depthHigh, planeDistance)) * bothCovered);
    // The closer covered surface owns the line, including its exterior half.
    bool neighbourOwns = neighbour.a > 0.5 && (centerNormal.a < 0.5 || viewDistance(neighbourDepth) < centerDepth);
    float opacity = texture2D(colourMap, neighbourOwns ? uv : vUv).a;
    return vec2(edge, opacity > 0.01 && opacity < 0.87 ? 1.0 : 0.0);
  }
  void main() {
    vec4 colour = texture2D(colourMap, vUv);
    float grain = paperGrain(vUv * resolution / pixelRatio);
    vec3 paperColour = paper * (1.0 + grain * paperStrength * 0.10);
    vec3 outputColour = paperColour * (1.0 - colour.a) + colour.rgb;
    vec4 normal = texture2D(normalMap, vUv);
    float rawDepth = texture2D(depthMap, vUv).r;
    float depth = viewDistance(rawDepth);
    vec3 position = viewPosition(vUv, rawDepth);
    float radius = max(lineWidth * 0.5, 0.5);
    vec2 stroke = boundary(normal, position, depth, vec2(radius, 0.0));
    vec2 candidate = boundary(normal, position, depth, vec2(-radius, 0.0));
    if (candidate.x > stroke.x) stroke = candidate;
    candidate = boundary(normal, position, depth, vec2(0.0, radius));
    if (candidate.x > stroke.x) stroke = candidate;
    candidate = boundary(normal, position, depth, vec2(0.0, -radius));
    if (candidate.x > stroke.x) stroke = candidate;
    float strokeOpacity = mix(0.86, 0.65 + grain * 0.24, stroke.y);
    outputColour = mix(outputColour, mix(ink, pencilInk, stroke.y), stroke.x * strokeOpacity);
    outputColour *= 1.0 + grain * paperStrength * 0.035;
    gl_FragColor = vec4(outputColour, 1.0);
    #include <colorspace_fragment>
  }
`;

function isInferred(tier) {
  return ['C', 'inferred', '推测'].includes(tier);
}

function isUnlocated(tier) {
  return ['U', 'X', 'unknown', 'excluded', '未知', '排除'].includes(tier);
}

function pigmentFor(material) {
  const name = material?.name || '';
  if (/roof|tile|瓦|屋面/i.test(name)) return '#879e98';
  if (/timber|wood|door|柱|木/i.test(name)) return '#846349';
  if (/earth|wall|夯土|墙/i.test(name)) return '#c2a17d';
  if (/floor|plinth|stone|台基|石/i.test(name)) return '#afa58c';
  if (/water|river|渠|水/i.test(name)) return '#a5b9b4';
  if (/ground|yard|terrain|road|soil|site|地面|道路/i.test(name)) return '#d0bf9a';
  const projectedPigment = material?.userData?.notebookPigment;
  if (/^#[0-9a-f]{6}$/i.test(projectedPigment) && projectedPigment.toLowerCase() !== '#ffffff') return projectedPigment;
  const colour = material?.color;
  // A textured glTF material often has an implicit white baseColorFactor.
  // The flat renderer cannot use that white as the material's visible pigment.
  const hasPigment = colour && Math.min(colour.r, colour.g, colour.b) < 0.999;
  return hasPigment ? `#${colour.getHexString(THREE.SRGBColorSpace)}` : '#bba98c';
}

function fitOverviewPose(box, aspect, fov, direction) {
  if (box.isEmpty()) return null;
  const center = box.getCenter(new THREE.Vector3());
  const backward = direction.clone().normalize();
  const right = new THREE.Vector3(0, 1, 0).cross(backward).normalize();
  const up = backward.clone().cross(right).normalize();
  // Keep 6.5% of the frame free on each side. Fit all eight corners in
  // perspective, including their different distances from the camera.
  const usableFrame = 1 - 2 * 0.065;
  const verticalSlope = Math.tan(THREE.MathUtils.degToRad(fov) / 2) * usableFrame;
  const horizontalSlope = verticalSlope * aspect;
  let distance = 1;
  for (const x of [box.min.x, box.max.x]) {
    for (const y of [box.min.y, box.max.y]) {
      for (const z of [box.min.z, box.max.z]) {
        const offset = new THREE.Vector3(x, y, z).sub(center);
        const depth = offset.dot(backward);
        distance = Math.max(distance,
          depth + Math.abs(offset.dot(right)) / horizontalSlope,
          depth + Math.abs(offset.dot(up)) / verticalSlope);
      }
    }
  }
  return { target: center.toArray(), position: center.clone().addScaledVector(backward, distance).toArray() };
}

function releaseSource(root) {
  const resources = new Set();
  const bitmaps = new Set();
  root?.traverse(object => {
    if (object.geometry) resources.add(object.geometry);
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
      if (!material) continue;
      resources.add(material);
      for (const texture of Object.values(material)) {
        if (!texture?.isTexture) continue;
        resources.add(texture);
        for (const image of [texture.source?.data, texture.image].flat()) {
          if (typeof ImageBitmap !== 'undefined' && image instanceof ImageBitmap) bitmaps.add(image);
        }
      }
    }
  });
  for (const resource of resources) resource.dispose();
  for (const bitmap of bitmaps) bitmap.close();
}

/** Render only the source assets and placements supplied by the city manifest. */
export async function createCityRenderer({
  canvas, manifest, onSelect = () => {}, onMetrics = () => {},
  onReady = () => {}, onStatus = () => {}, signal
}) {
  if (!manifest?.assets || !manifest?.nodes) throw new Error('缺少城市资产清单');
  const assets = new Map(manifest.assets.map(asset => [asset.id, asset]));
  const nodes = new Map([...manifest.nodes, ...(manifest.researchModels || [])].map(node => [node.id, node]));
  const chapters = new Map((manifest.chapters || []).map(chapter => [chapter.id, chapter]));
  const effectiveTier = node => node.tier ?? assets.get(node.asset)?.tier;
  let loadedIds = new Set(manifest.nodes.filter(node => node.initial !== false && !isUnlocated(effectiveTier(node))).map(node => node.id));
  let cityIds = loadedIds;
  const cache = new Map();
  const materialCache = new Map();
  const resources = new Set();
  const controller = new AbortController();
  const evidenceVisible = { value: true };
  const lightDirection = { value: new THREE.Vector3() };
  const worldLight = new THREE.Vector3(-0.6, 1, 0.75).normalize();
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 60000);
  const postScene = new THREE.Scene();
  const postCamera = new THREE.Camera();
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let renderer;
  let controls;
  let observer;
  let modelGroup = new THREE.Group();
  let targets = [];
  let width = 0;
  let height = 0;
  let frame = 0;
  let disposed = false;
  let contextLost = false;
  let generation = 0;
  let downloadBytes = 0;
  let selectedId = null;
  let nearId = null;
  let activeChapter = 'city';
  let overviewActive = false;
  let studyId = null;
  let pointerStart = null;
  let flight = null;
  let lastMetrics = {};
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);
  let internalPixelRatio = 2;

  const normalMaterial = new THREE.ShaderMaterial({ vertexShader: surfaceVertex, fragmentShader: normalFragment, side: THREE.DoubleSide });
  const paperMaterial = new THREE.ShaderMaterial({
    vertexShader: pageVertex, fragmentShader: cityPageFragment, depthTest: false, depthWrite: false,
    uniforms: {
      colourMap: { value: null }, normalMap: { value: null }, depthMap: { value: null },
      resolution: { value: new THREE.Vector2(1, 1) }, pixelRatio: { value: 2 },
      lineWidth: { value: 2.8 }, paperStrength: { value: 0.35 },
      cameraNear: { value: camera.near }, cameraFar: { value: camera.far },
      cameraProjectionInverse: { value: camera.projectionMatrixInverse },
      paper: { value: new THREE.Color('#f2ead7') }, ink: { value: new THREE.Color('#4b5148') },
      pencilInk: { value: new THREE.Color('#5b5147') }, upDirection: { value: new THREE.Vector3(0, 1, 0) }
    }
  });
  const resolveMaterial = new THREE.ShaderMaterial({
    vertexShader: pageVertex, fragmentShader: resolveFragment, depthTest: false, depthWrite: false,
    uniforms: { imageMap: { value: null }, outputResolution: { value: new THREE.Vector2(1, 1) } }
  });
  const postGeometry = new THREE.PlaneGeometry(2, 2);
  const postQuad = new THREE.Mesh(postGeometry, paperMaterial);
  postScene.add(postQuad);
  for (const resource of [normalMaterial, paperMaterial, resolveMaterial, postGeometry]) resources.add(resource);

  function checkActive() {
    controller.signal.throwIfAborted();
    if (disposed) throw new DOMException('Rendering cancelled', 'AbortError');
  }

  async function loadAsset(id, near = false) {
    const asset = assets.get(id);
    if (!asset) throw new Error(`资产清单缺少 ${id}`);
    const useNear = near && Boolean(asset.nearUrl);
    const key = `${id}:${useNear ? 'near' : 'far'}`;
    if (cache.has(key)) return cache.get(key);
    const promise = (async () => {
      const url = new URL(useNear ? asset.nearUrl : asset.url, location.href).href;
      const response = await fetch(url, { signal: controller.signal });
      if (!response.ok) throw new Error(`模型加载失败（${response.status}）`);
      const bytes = await response.arrayBuffer();
      downloadBytes += bytes.byteLength;
      checkActive();
      const parsed = await new GLTFLoader().parseAsync(bytes, new URL('.', url).href);
      // External glTF buffers/images are requested by GLTFLoader. Their exact
      // source-file total is recorded in the projection manifest.
      const bundleBytes = useNear ? asset.nearBundleBytes : asset.bundleBytes;
      if (Number.isFinite(bundleBytes)) downloadBytes += Math.max(0, bundleBytes - bytes.byteLength);
      const parts = [];
      const buckets = new Map();
      try {
        checkActive();
        parsed.scene.updateMatrixWorld(true);
        const excluded = new Set(asset.excludeNodes || asset.removable_site_nodes || []);
        const matchedExclusions = new Set();
        parsed.scene.traverse(object => {
          if (!object.isMesh) return;
          for (let ancestor = object; ancestor; ancestor = ancestor.parent) {
            const originalName = ancestor.userData?.name || ancestor.name;
            const excludedName = excluded.has(originalName) ? originalName : ancestor.name;
            if (excluded.has(excludedName)) {
              matchedExclusions.add(excludedName);
              return;
            }
          }
          if (object.isSkinnedMesh || object.morphTargetInfluences?.length) throw new Error('城市资产需要静态网格');
          const source = object.geometry.index ? object.geometry.toNonIndexed() : object.geometry.clone();
          source.applyMatrix4(object.matrixWorld);
          if (!source.getAttribute('normal')) source.computeVertexNormals();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          const groups = Array.isArray(object.material) ? source.groups : [{ start: 0, count: source.getAttribute('position').count, materialIndex: 0 }];
          for (const group of groups) {
            const pigment = pigmentFor(materials[group.materialIndex]);
            const geometry = new THREE.BufferGeometry();
            for (const name of ['position', 'normal']) {
              const attribute = source.getAttribute(name);
              const values = new Float32Array(group.count * 3);
              for (let i = 0; i < group.count; i++) {
                const index = group.start + i;
                values[i * 3] = attribute.getX(index);
                values[i * 3 + 1] = attribute.getY(index);
                values[i * 3 + 2] = attribute.getZ(index);
              }
              geometry.setAttribute(name, new THREE.BufferAttribute(values, 3));
            }
            if (!buckets.has(pigment)) buckets.set(pigment, []);
            buckets.get(pigment).push(geometry);
          }
          source.dispose();
        });
        if (matchedExclusions.size !== excluded.size) throw new Error(`模型替换节点不完整 ${id}`);
        for (const [pigment, geometries] of buckets) {
          const geometry = mergeGeometries(geometries, false);
          if (!geometry) throw new Error('模型材质合并失败');
          geometry.computeBoundingBox();
          geometry.computeBoundingSphere();
          resources.add(geometry);
          parts.push({ geometry, pigment });
        }
        return { parts, url };
      } catch (error) {
        for (const part of parts) {
          resources.delete(part.geometry);
          part.geometry.dispose();
        }
        throw error;
      } finally {
        for (const geometries of buckets.values()) for (const geometry of geometries) geometry.dispose();
        releaseSource(parsed.scene);
      }
    })();
    cache.set(key, promise);
    try { return await promise; }
    catch (error) { cache.delete(key); throw error; }
  }

  function transformFor(node) {
    const transform = node.transform || node;
    const matrix = new THREE.Matrix4();
    const position = new THREE.Vector3().fromArray(transform.position || [0, 0, 0]);
    const quaternion = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), transform.rotationY || 0);
    const scale = new THREE.Vector3().fromArray(transform.scale || [1, 1, 1]);
    if (node.matrix) matrix.fromArray(node.matrix);
    else matrix.compose(position, quaternion, scale);
    const axes = [0, 1, 2].map(index => new THREE.Vector3().setFromMatrixColumn(matrix, index));
    if (!matrix.elements.every(Number.isFinite) || axes.some(axis => axis.lengthSq() < 1e-12) || matrix.determinant() <= 0) {
      throw new Error(`模型变换无效 ${node.id}`);
    }
    for (const [a, b] of [[0, 1], [0, 2], [1, 2]]) {
      if (Math.abs(axes[a].dot(axes[b])) > 1e-5 * axes[a].length() * axes[b].length()) throw new Error(`模型变换包含剪切 ${node.id}`);
    }
    return matrix;
  }

  function getMaterial(pigment, inferred) {
    const key = `${pigment}:${inferred}`;
    if (!materialCache.has(key)) {
      const material = new THREE.ShaderMaterial({
        vertexShader: surfaceVertex, fragmentShader: surfaceFragment, side: THREE.DoubleSide,
        uniforms: { pigment: { value: new THREE.Color(pigment) }, lightDirection, evidenceVisible, inferred: { value: inferred } }
      });
      materialCache.set(key, material);
      resources.add(material);
    }
    return materialCache.get(key);
  }

  function releaseInstances(group) {
    group.traverse(object => { if (object.isInstancedMesh) object.dispose(); });
    group.removeFromParent();
    group.clear();
  }

  async function rebuild(nextNearId = null, nextIds = loadedIds) {
    const token = ++generation;
    const activeNodes = [...nextIds].map(id => nodes.get(id)).filter(node => node && !isUnlocated(effectiveTier(node)));
    const replaced = new Set(activeNodes.flatMap(node => node.replaces || []));
    const batches = new Map();
    for (const node of activeNodes) {
      if (replaced.has(node.id)) continue;
      const near = node.id === nextNearId && Boolean(assets.get(node.asset)?.nearUrl);
      const inferred = isInferred(effectiveTier(node));
      const key = `${node.asset}:${near}:${inferred}`;
      if (!batches.has(key)) batches.set(key, { asset: node.asset, near, inferred, nodes: [] });
      batches.get(key).nodes.push(node);
    }
    const loaded = await Promise.all([...batches.values()].map(async batch => ({ ...batch, prototype: await loadAsset(batch.asset, batch.near) })));
    if (disposed || token !== generation) return false;
    const fresh = new THREE.Group();
    try {
      for (const batch of loaded) {
        const matrices = batch.nodes.map(transformFor);
        for (const part of batch.prototype.parts) {
          const mesh = new THREE.InstancedMesh(part.geometry, getMaterial(part.pigment, batch.inferred), batch.nodes.length);
          fresh.add(mesh);
          matrices.forEach((matrix, index) => mesh.setMatrixAt(index, matrix));
          mesh.instanceMatrix.needsUpdate = true;
          mesh.computeBoundingBox();
          mesh.computeBoundingSphere();
          mesh.userData.nodes = batch.nodes;
          mesh.name = batch.asset;
        }
      }
    } catch (error) {
      releaseInstances(fresh);
      throw error;
    }
    releaseInstances(modelGroup);
    modelGroup = fresh;
    scene.add(modelGroup);
    loadedIds = nextIds;
    nearId = nextNearId;
    requestRender();
    return true;
  }

  function resize() {
    if (disposed || !renderer) return;
    const bounds = canvas.parentElement.getBoundingClientRect();
    const nextWidth = Math.max(0, Math.floor(bounds.width));
    const nextHeight = Math.max(0, Math.floor(bounds.height));
    if (!nextWidth || !nextHeight || (nextWidth === width && nextHeight === height)) return;
    width = nextWidth;
    height = nextHeight;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    if (overviewActive) applyPose(overviewPose(), true);
    internalPixelRatio = Math.min(2, Math.min(4096, renderer.capabilities.maxTextureSize) / Math.max(width, height));
    const targetWidth = Math.max(1, Math.round(width * internalPixelRatio));
    const targetHeight = Math.max(1, Math.round(height * internalPixelRatio));
    // Fresh targets keep depth/normal bindings coherent after every resize.
    const colour = new THREE.WebGLRenderTarget(targetWidth, targetHeight, { minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
    const geometry = new THREE.WebGLRenderTarget(targetWidth, targetHeight, { minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
    geometry.depthTexture = new THREE.DepthTexture(targetWidth, targetHeight, THREE.UnsignedIntType);
    const composition = new THREE.WebGLRenderTarget(targetWidth, targetHeight, { depthBuffer: false, stencilBuffer: false });
    for (const target of [colour, geometry, composition]) target.texture.colorSpace = THREE.NoColorSpace;
    renderer.setRenderTarget(null);
    const previous = targets;
    targets = [colour, geometry, composition];
    paperMaterial.uniforms.colourMap.value = colour.texture;
    paperMaterial.uniforms.normalMap.value = geometry.texture;
    paperMaterial.uniforms.depthMap.value = geometry.depthTexture;
    paperMaterial.uniforms.resolution.value.set(targetWidth, targetHeight);
    paperMaterial.uniforms.pixelRatio.value = internalPixelRatio;
    paperMaterial.uniforms.lineWidth.value = 1.4 * internalPixelRatio;
    paperMaterial.uniformsNeedUpdate = true;
    resolveMaterial.uniforms.imageMap.value = composition.texture;
    resolveMaterial.uniforms.outputResolution.value.set(Math.round(width * pixelRatio), Math.round(height * pixelRatio));
    resolveMaterial.uniformsNeedUpdate = true;
    previous.forEach(target => target.dispose());
    requestRender();
  }

  function requestRender() {
    if (!disposed && !contextLost && !document.hidden && !frame) frame = requestAnimationFrame(render);
  }

  function render(now = performance.now()) {
    frame = 0;
    if (disposed || contextLost || document.hidden || !width || !height) return;
    if (flight) {
      const progress = Math.min(1, (now - flight.started) / flight.duration);
      const eased = progress * progress * (3 - 2 * progress);
      camera.position.lerpVectors(flight.fromPosition, flight.position, eased);
      controls.target.lerpVectors(flight.fromTarget, flight.target, eased);
      if (progress === 1) flight = null;
      controls.update();
    }
    const started = performance.now();
    const distance = camera.position.distanceTo(controls.target);
    camera.near = Math.max(0.08, distance / 2000);
    camera.far = Math.max(8000, distance * 6);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
    lightDirection.value.copy(worldLight).transformDirection(camera.matrixWorldInverse);
    paperMaterial.uniforms.upDirection.value.set(0, 1, 0).transformDirection(camera.matrixWorldInverse);
    paperMaterial.uniforms.cameraNear.value = camera.near;
    paperMaterial.uniforms.cameraFar.value = camera.far;
    renderer.info.reset();
    renderer.setScissorTest(false);
    renderer.setClearColor(0, 0);
    scene.overrideMaterial = null;
    renderer.setRenderTarget(targets[0]);
    renderer.clear();
    renderer.render(scene, camera);
    scene.overrideMaterial = normalMaterial;
    renderer.setRenderTarget(targets[1]);
    renderer.clear();
    renderer.render(scene, camera);
    scene.overrideMaterial = null;
    postQuad.material = paperMaterial;
    renderer.setRenderTarget(targets[2]);
    renderer.render(postScene, postCamera);
    postQuad.material = resolveMaterial;
    renderer.setRenderTarget(null);
    renderer.setViewport(0, 0, width, height);
    renderer.render(postScene, postCamera);
    lastMetrics = {
      drawCalls: renderer.info.render.calls, triangles: renderer.info.render.triangles,
      renderMs: performance.now() - started, downloadBytes,
      modelByteBasis: 'root-response-bytes-plus-declared-external-bundle',
      representedNodes: new Set(modelGroup.children.flatMap(mesh => mesh.userData.nodes.map(node => node.id))).size,
      chapter: activeChapter, nearId, studyId, evidenceVisible: evidenceVisible.value,
      pixelRatio, internalPixelRatio, bufferWidth: canvas.width, bufferHeight: canvas.height,
      contextLost: false
    };
    onMetrics(lastMetrics);
    if (flight) requestRender();
  }

  function fitPose(box, direction = new THREE.Vector3(0.8, 1.2, 1)) {
    const sphere = box.getBoundingSphere(new THREE.Sphere());
    const fov = THREE.MathUtils.degToRad(camera.fov);
    const horizontal = 2 * Math.atan(Math.tan(fov / 2) * camera.aspect);
    const distance = Math.max(sphere.radius, 1) / Math.sin(Math.min(fov, horizontal) / 2) * 1.08;
    return { target: sphere.center.toArray(), position: sphere.center.clone().add(direction.normalize().multiplyScalar(distance)).toArray() };
  }

  function overviewPose() {
    const box = new THREE.Box3().setFromObject(modelGroup);
    const sourcePose = manifest.overview?.camera;
    const direction = sourcePose?.position && sourcePose?.target
      ? new THREE.Vector3().fromArray(sourcePose.position).sub(new THREE.Vector3().fromArray(sourcePose.target))
      : new THREE.Vector3(0.8, 1.2, 1);
    return fitOverviewPose(box, camera.aspect, camera.fov, direction);
  }

  function applyPose(pose, immediate = false) {
    if (!pose?.position || !pose?.target) return false;
    const position = new THREE.Vector3().fromArray(pose.position);
    const target = new THREE.Vector3().fromArray(pose.target);
    if (overviewActive) controls.maxDistance = Math.max(20000, position.distanceTo(target) * 1.1);
    if (immediate || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      flight = null;
      camera.position.copy(position);
      controls.target.copy(target);
      controls.update();
    } else {
      flight = { fromPosition: camera.position.clone(), fromTarget: controls.target.clone(), position, target, started: performance.now(), duration: 900 };
    }
    requestRender();
    return true;
  }

  function nodeBounds(ids) {
    const wanted = new Set(ids);
    const box = new THREE.Box3();
    const matrix = new THREE.Matrix4();
    for (const mesh of modelGroup.children) {
      mesh.userData.nodes.forEach((node, index) => {
        if (!wanted.has(node.id)) return;
        mesh.getMatrixAt(index, matrix);
        box.union(mesh.geometry.boundingBox.clone().applyMatrix4(matrix));
      });
    }
    return box;
  }

  async function focusChapter(id) {
    if (id === 'city' || id === 'overview') return resetView();
    const chapter = chapters.get(id);
    if (!chapter) return false;
    if (chapter.defaultResearchModel) return focusResearchModel(chapter.defaultResearchModel, id);
    const nextIds = new Set(cityIds);
    for (const nodeId of chapter.loadNodeIds || []) nextIds.add(nodeId);
    onStatus(`正在打开${chapter.title || chapter.name || '这一章'}…`);
    const ready = await rebuild(null, nextIds);
    if (!ready) return false;
    cityIds = nextIds;
    studyId = null;
    overviewActive = false;
    activeChapter = id;
    const ids = chapter.nodeIds || manifest.nodes.filter(node => node.chapter === id).map(node => node.id);
    const bounds = nodeBounds(ids);
    const pose = chapter.camera || (!bounds.isEmpty() ? fitPose(bounds) : null);
    onStatus(pose ? '拖动环顾，滚轮拉近，点选已有建筑查看手记。' : '这一章的资料尚未与城市坐标配准。');
    return applyPose(pose);
  }

  async function focusCourtyard(id = selectedId) {
    const node = nodes.get(id);
    if (!node || isUnlocated(effectiveTier(node))) return false;
    if (node.space === 'local-study') return focusResearchModel(id);
    const nextIds = new Set(cityIds);
    nextIds.add(id);
    onStatus('正在打开已有近景模型…');
    if (!await rebuild(id, nextIds)) return false;
    cityIds = nextIds;
    studyId = null;
    overviewActive = false;
    selectedId = id;
    activeChapter = node.chapter || activeChapter;
    const box = nodeBounds([id]);
    if (box.isEmpty()) return false;
    onStatus('已进入近景。拖动环顾，R 返回鸟瞰。');
    return applyPose(node.camera || fitPose(box, new THREE.Vector3(1, 0.8, 1)));
  }

  async function resetView(immediate = false) {
    if (!await rebuild(null, cityIds)) return false;
    studyId = null;
    activeChapter = 'city';
    overviewActive = true;
    const moved = applyPose(overviewPose(), immediate);
    if (moved) onStatus('拖动环顾，滚轮拉近，点选已有建筑查看手记。');
    return moved;
  }

  async function focusResearchModel(id, chapterId = 'ritual') {
    const node = nodes.get(id);
    if (!node || node.space !== 'local-study') return false;
    onStatus('正在打开独立研究模型…');
    if (!await rebuild(id, new Set([id]))) return false;
    studyId = id;
    overviewActive = false;
    activeChapter = chapterId;
    selectedId = id;
    const bounds = nodeBounds([id]);
    if (bounds.isEmpty()) return false;
    onStatus('独立模型研究视图。城市位置尚未配准。');
    onSelect(node);
    return applyPose(fitPose(bounds), true);
  }

  function setEvidenceVisible(value) {
    evidenceVisible.value = Boolean(value);
    requestRender();
  }

  function onPointerDown(event) {
    pointerStart = { x: event.clientX, y: event.clientY, id: event.pointerId };
  }

  function onPointerUp(event) {
    const start = pointerStart;
    pointerStart = null;
    if (!start || start.id !== event.pointerId || Math.hypot(start.x - event.clientX, start.y - event.clientY) > 5) return;
    const rect = canvas.getBoundingClientRect();
    pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, 1 - (event.clientY - rect.top) / rect.height * 2);
    camera.updateMatrixWorld();
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(modelGroup.children);
    const hit = hits.find(result => result.object.userData.nodes?.[result.instanceId]?.selectable !== false);
    if (!hit) return;
    const node = hit.object.userData.nodes[hit.instanceId];
    selectedId = node.id;
    onSelect(node);
  }

  function onKeyDown(event) {
    if (event.key.toLowerCase() === 'r') { event.preventDefault(); resetView(); return; }
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '=', '-'].includes(event.key)) return;
    event.preventDefault();
    overviewActive = false;
    flight = null;
    const offset = camera.position.clone().sub(controls.target);
    if (event.key.startsWith('Arrow')) {
      const spherical = new THREE.Spherical().setFromVector3(offset);
      spherical.theta += ({ ArrowLeft: 0.1, ArrowRight: -0.1 }[event.key] || 0);
      spherical.phi = THREE.MathUtils.clamp(spherical.phi + ({ ArrowUp: -0.1, ArrowDown: 0.1 }[event.key] || 0), 0.1, Math.PI * 0.48);
      offset.setFromSpherical(spherical);
    } else offset.multiplyScalar(event.key === '-' ? 1.12 : 1 / 1.12);
    offset.clampLength(controls.minDistance, controls.maxDistance);
    camera.position.copy(controls.target).add(offset);
    controls.update();
    requestRender();
  }

  function onControlStart() { flight = null; overviewActive = false; }
  function onAbort() { dispose(); }
  function onContextLost(event) {
    event.preventDefault();
    contextLost = true;
    cancelAnimationFrame(frame);
    frame = 0;
    onMetrics({ ...lastMetrics, contextLost: true });
    onStatus('三维画面已暂停，可重新打开。');
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    generation++;
    controller.abort();
    cancelAnimationFrame(frame);
    observer?.disconnect();
    controls?.dispose();
    releaseInstances(modelGroup);
    targets.forEach(target => target.dispose());
    targets = [];
    for (const resource of resources) resource.dispose();
    resources.clear();
    cache.clear();
    materialCache.clear();
    canvas.removeEventListener('pointerdown', onPointerDown);
    canvas.removeEventListener('pointerup', onPointerUp);
    canvas.removeEventListener('keydown', onKeyDown);
    canvas.removeEventListener('webglcontextlost', onContextLost);
    document.removeEventListener('visibilitychange', requestRender);
    window.removeEventListener('resize', resize);
    signal?.removeEventListener('abort', onAbort);
    renderer?.dispose();
    renderer?.forceContextLoss();
  }

  try {
    signal?.throwIfAborted();
    signal?.addEventListener('abort', onAbort, { once: true });
    renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false });
    renderer.setPixelRatio(pixelRatio);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.autoClear = false;
    renderer.info.autoReset = false;
    controls = new OrbitControls(camera, canvas);
    controls.enableDamping = false;
    controls.minDistance = 5;
    controls.maxDistance = 20000;
    controls.minPolarAngle = 0.08;
    controls.maxPolarAngle = Math.PI * 0.48;
    controls.addEventListener('change', requestRender);
    controls.addEventListener('start', onControlStart);
    canvas.addEventListener('webglcontextlost', onContextLost);
    canvas.addEventListener('pointerdown', onPointerDown);
    canvas.addEventListener('pointerup', onPointerUp);
    canvas.addEventListener('keydown', onKeyDown);
    canvas.tabIndex = 0;
    scene.add(modelGroup);
    onStatus('正在打开已经建好的城市模型…');
    await rebuild();
    checkActive();
    resize();
    await resetView(true);
    if (manifest.initialCamera) {
      overviewActive = false;
      applyPose(manifest.initialCamera, true);
    }
    observer = new ResizeObserver(resize);
    observer.observe(canvas.parentElement);
    window.addEventListener('resize', resize);
    document.addEventListener('visibilitychange', requestRender);
    render();
    onStatus('拖动环顾，滚轮拉近，点选已有建筑查看手记。');
    onReady(lastMetrics);
    return { focusChapter, focusCourtyard, focusResearchModel, resetView, setEvidenceVisible, resize, dispose };
  } catch (error) {
    dispose();
    throw error;
  }
}
