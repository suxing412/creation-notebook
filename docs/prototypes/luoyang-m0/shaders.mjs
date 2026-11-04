// Intermediate targets store linear colour or raw geometry data. Only the
// presentation pass applies Three's output colour-space conversion.
export const surfaceVertex = /* glsl */ `
  varying vec3 vNormal;
  void main() {
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

export const surfaceFragment = /* glsl */ `
  uniform vec3 pigment;
  uniform vec3 lightDirection;
  varying vec3 vNormal;
  void main() {
    vec3 n = normalize(vNormal);
    if (!gl_FrontFacing) n = -n;
    float light = dot(n, lightDirection);
    float band = light > 0.55 ? 1.08 : (light > -0.12 ? 0.90 : 0.69);
    gl_FragColor = vec4(pigment * band, 1.0);
  }
`;

export const normalFragment = /* glsl */ `
  varying vec3 vNormal;
  void main() {
    vec3 n = normalize(vNormal);
    if (!gl_FrontFacing) n = -n;
    gl_FragColor = vec4(n * 0.5 + 0.5, 1.0);
  }
`;

export const hullVertex = /* glsl */ `
  attribute vec3 outlineNormal;
  uniform vec2 resolution;
  uniform float lineWidth;
  void main() {
    vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
    vec4 clip = projectionMatrix * viewPosition;
    vec3 viewNormal = normalize(normalMatrix * outlineNormal);
    vec2 direction = (projectionMatrix * vec4(viewNormal, 0.0)).xy;
    float lengthSquared = dot(direction, direction);
    if (lengthSquared > 0.000001) {
      direction *= inversesqrt(lengthSquared);
      clip.xy += direction * (2.0 * lineWidth / resolution) * clip.w;
    }
    gl_Position = clip;
  }
`;

export const hullFragment = /* glsl */ `
  uniform vec3 ink;
  void main() { gl_FragColor = vec4(ink, 1.0); }
`;

export const pageVertex = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

export const pageFragment = /* glsl */ `
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
  uniform bool detectEdges;
  uniform bool pencil;
  uniform vec3 paper;
  uniform vec3 ink;
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
    vec4 position = cameraProjectionInverse * vec4(uv * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    return position.xyz / position.w;
  }
  vec3 decodeNormal(vec4 sampleValue) {
    return normalize(sampleValue.rgb / max(sampleValue.a, 0.0001) * 2.0 - 1.0);
  }
  float boundary(vec4 centerNormal, vec3 centerPosition, float centerDepth, vec2 offset) {
    vec2 uv = clamp(vUv + offset / resolution, vec2(0.0), vec2(1.0));
    vec4 neighbour = texture2D(normalMap, uv);
    float silhouette = abs(centerNormal.a - neighbour.a);
    float bothCovered = step(0.5, centerNormal.a) * step(0.5, neighbour.a);
    vec3 a = decodeNormal(centerNormal);
    vec3 b = decodeNormal(neighbour);
    float normalJump = length(a - b);
    // Probe half a CSS pixel beyond the edge. This identifies near-horizontal
    // slivers without vetoing periodic roof ribs that repeat the same normal.
    vec2 support = normalize(offset) * max(0.5 * pixelRatio, 1.0);
    vec4 farA = texture2D(normalMap, clamp(vUv - support / resolution, vec2(0.0), vec2(1.0)));
    vec4 farB = texture2D(normalMap, clamp(uv + support / resolution, vec2(0.0), vec2(1.0)));
    float supportedFaces = step(0.95, farA.a) * step(0.95, farB.a);
    float supportedJump = length(decodeNormal(farA) - decodeNormal(farB));
    vec3 neighbourPosition = viewPosition(uv, texture2D(depthMap, uv).r);
    // A sloping face has a depth gradient but remains in the centre tangent
    // plane. Its plane residual stays zero, avoiding black ground at low angles.
    bool broadSurface = supportedFaces > 0.5 && supportedJump < 0.25;
    vec3 planeNormal = broadSurface ? decodeNormal(farA) : a;
    float planeDistance = abs(dot(neighbourPosition - centerPosition, planeNormal));
    float pixelFootprint = 2.0 * centerDepth * cameraProjectionInverse[1][1] / resolution.y;
    float depthLow = max(centerDepth * 0.0008, pixelFootprint * 0.6);
    float depthHigh = max(centerDepth * 0.0025, pixelFootprint * 1.8);
    float crease = smoothstep(0.25, 0.6, normalJump);
    if (broadSurface && dot(decodeNormal(farA), upDirection) > 0.97) crease = 0.0;
    float stepEdge = smoothstep(depthLow, depthHigh, planeDistance);
    return max(silhouette, max(crease, stepEdge) * bothCovered);
  }
  void main() {
    vec4 colour = texture2D(colourMap, vUv);
    vec2 paperPosition = vUv * resolution / pixelRatio;
    float grain = paperGrain(paperPosition);
    vec3 paperColour = paper * (1.0 + grain * paperStrength * 0.10);
    // A transparent pigment layer over paper keeps the nearest-surface
    // occlusion intact. It deliberately does not reveal hidden room interiors.
    float pigmentOpacity = pencil ? 0.56 : 1.0;
    // Filtering an opaque pixel against transparent black premultiplies RGB
    // by coverage already; multiplying by colour.a again creates dark fringes.
    vec3 outputColour = paperColour * (1.0 - colour.a * pigmentOpacity) + colour.rgb * pigmentOpacity;
    if (detectEdges) {
      vec4 normal = texture2D(normalMap, vUv);
      float depth = viewDistance(texture2D(depthMap, vUv).r);
      vec3 position = viewPosition(vUv, texture2D(depthMap, vUv).r);
      float radius = max(lineWidth * 0.5, 0.5);
      float edge = 0.0;
      edge = max(edge, boundary(normal, position, depth, vec2(radius, 0.0)));
      edge = max(edge, boundary(normal, position, depth, vec2(-radius, 0.0)));
      edge = max(edge, boundary(normal, position, depth, vec2(0.0, radius)));
      edge = max(edge, boundary(normal, position, depth, vec2(0.0, -radius)));
      float strokeOpacity = pencil ? 0.44 + grain * 0.24 : 0.86;
      outputColour = mix(outputColour, ink, edge * strokeOpacity);
    }
    // Grain is anchored to paper coordinates and never uses frame time.
    outputColour *= 1.0 + grain * paperStrength * (pencil ? 0.075 : 0.035);
    gl_FragColor = vec4(outputColour, 1.0);
    #include <colorspace_fragment>
  }
`;

// Supersampled edge compositing is resolved in linear space. The tap positions
// cover the final output pixel, including non-integer source/output DPR ratios.
export const resolveFragment = /* glsl */ `
  uniform sampler2D imageMap;
  uniform vec2 outputResolution;
  varying vec2 vUv;
  void main() {
    vec2 quarterPixel = 0.25 / outputResolution;
    vec3 colour = texture2D(imageMap, vUv + vec2(-quarterPixel.x, -quarterPixel.y)).rgb;
    colour += texture2D(imageMap, vUv + vec2(quarterPixel.x, -quarterPixel.y)).rgb;
    colour += texture2D(imageMap, vUv + vec2(-quarterPixel.x, quarterPixel.y)).rgb;
    colour += texture2D(imageMap, vUv + vec2(quarterPixel.x, quarterPixel.y)).rgb;
    gl_FragColor = vec4(colour * 0.25, 1.0);
    #include <colorspace_fragment>
  }
`;
