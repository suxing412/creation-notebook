// Miniature look for the overview: a tilt-shift band (sharp across the focus line, softening toward the top and bottom
// of the frame) and a touch more colour — the cues that make a photo read as a small model on a table.
// The scene renders into an HDR target; two blur passes whose radius grows with the distance from the focus band;
// tone mapping and the output colour space are applied in the last pass, as they would be on a direct render.
import * as THREE from 'three';

const VERT = 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }';
const BLUR = /* glsl */`
  uniform sampler2D tex; uniform vec2 dir; uniform float radius, focus, band, ramp, aspectUp;
  varying vec2 vUv;
  vec4 blur() {
    float dy = vUv.y - focus;
    // above the focus line (the far side of the table) softens a little sooner than below it
    float k = smoothstep(band, band + ramp, dy > 0.0 ? dy * aspectUp : -dy);
    vec2 st = dir * radius * k * 0.25;
    vec4 s = texture2D(tex, vUv) * 0.18;
    s += (texture2D(tex, vUv + st) + texture2D(tex, vUv - st)) * 0.15;
    s += (texture2D(tex, vUv + st * 2.0) + texture2D(tex, vUv - st * 2.0)) * 0.12;
    s += (texture2D(tex, vUv + st * 3.0) + texture2D(tex, vUv - st * 3.0)) * 0.09;
    s += (texture2D(tex, vUv + st * 4.0) + texture2D(tex, vUv - st * 4.0)) * 0.05;
    return s;
  }`;

export function createMiniature(renderer, opts = {}) {
  const P = { radius: 3.5, band: 0.2, ramp: 0.5, aspectUp: 1.15, saturation: 1.08, ...opts };
  const mk = samples => new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, samples, depthBuffer: samples > 0 });
  const rtScene = mk(4), rtH = mk(0);
  const uni = () => ({ tex: { value: null }, dir: { value: new THREE.Vector2() }, radius: { value: P.radius }, focus: { value: 0.5 },
    band: { value: P.band }, ramp: { value: P.ramp }, aspectUp: { value: P.aspectUp } });
  const passH = new THREE.ShaderMaterial({ uniforms: uni(), vertexShader: VERT, toneMapped: false, depthTest: false, depthWrite: false,
    fragmentShader: BLUR + 'void main() { gl_FragColor = blur(); }' });
  const passV = new THREE.ShaderMaterial({ uniforms: { ...uni(), saturation: { value: P.saturation } }, vertexShader: VERT, depthTest: false, depthWrite: false,
    blending: THREE.NoBlending,
    // the target holds colour over a transparent clear (premultiplied): un-premultiply, grade, tone-map, convert, premultiply again
    fragmentShader: BLUR + `uniform float saturation;
      void main() {
        vec4 s = blur(); float a = clamp(s.a, 0.0, 1.0);
        vec3 c = a > 1e-4 ? s.rgb / s.a : vec3(0.0);
        float l = dot(c, vec3(0.2126, 0.7152, 0.0722)); c = max(mix(vec3(l), c, saturation), 0.0);
        gl_FragColor = vec4(c, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
        gl_FragColor = vec4(gl_FragColor.rgb * a, a);
      }` });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), passH); quad.frustumCulled = false;
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const size = new THREE.Vector2(), v = new THREE.Vector3();
  let enabled = true;

  return {
    params: P,
    get enabled() { return enabled; }, set enabled(on) { enabled = !!on; },
    setSize() {
      renderer.getDrawingBufferSize(size);
      rtScene.setSize(size.x, size.y); rtH.setSize(size.x, size.y);
    },
    // focusAt: a world point that should sit on the sharp line (the orbit target)
    render(scene, camera, focusAt) {
      if (!enabled) { renderer.setRenderTarget(null); renderer.render(scene, camera); return; }
      const focus = focusAt ? THREE.MathUtils.clamp(v.copy(focusAt).project(camera).y * 0.5 + 0.5, 0.2, 0.8) : 0.5;
      const dpr = renderer.getPixelRatio();
      for (const m of [passH, passV]) {
        const u = m.uniforms; u.focus.value = focus; u.radius.value = P.radius * dpr; u.band.value = P.band; u.ramp.value = P.ramp; u.aspectUp.value = P.aspectUp;
      }
      passV.uniforms.saturation.value = P.saturation;
      renderer.setRenderTarget(rtScene); renderer.clear(); renderer.render(scene, camera);
      passH.uniforms.tex.value = rtScene.texture; passH.uniforms.dir.value.set(1 / size.x, 0);
      quad.material = passH; renderer.setRenderTarget(rtH); renderer.render(quad, cam);
      passV.uniforms.tex.value = rtH.texture; passV.uniforms.dir.value.set(0, 1 / size.y);
      quad.material = passV; renderer.setRenderTarget(null); renderer.render(quad, cam);
    },
    dispose() { rtScene.dispose(); rtH.dispose(); passH.dispose(); passV.dispose(); quad.geometry.dispose(); },
  };
}
