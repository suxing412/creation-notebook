// Camera-only helpers. Scene coordinates and model transforms are never changed.
export function groundPose(pose) {
  if (!pose?.position || !pose?.target || ![...pose.position, ...pose.target].every(Number.isFinite)) return null;
  const dy = -pose.target[1];
  return { target: [pose.target[0], 0, pose.target[2]], position: [pose.position[0], Math.max(0.4, pose.position[1] + dy), pose.position[2]] };
}
// Direction is relative to the rendered view, including the south-up overview.
export function groundInputVelocity(position, target, keys) {
  let forward = Number(keys.has('KeyW')) - Number(keys.has('KeyS'));
  let right = Number(keys.has('KeyD')) - Number(keys.has('KeyA'));
  const norm = Math.hypot(forward, right) || 1; forward /= norm; right /= norm;
  const distance = Math.hypot(...position.map((v,i) => v-target[i]));
  const speed = Math.min(900, Math.max(2, distance * 0.22));
  return [right*speed, 0, forward*speed];
}

// Velocity lives in screen-relative axes so turning while holding W never carries
// a stale world direction into the next step. Bounds still operate in world space.
function groundAxes(position,target,fallback) {
  const x=target[0]-position[0], z=target[2]-position[2], length=Math.hypot(x,z);
  return length>1e-7 ? [x/length,z/length] : fallback;
}
export function groundToWorld(vector, position, target, fallback=[0,1]) {
  const [x,z]=groundAxes(position,target,fallback);
  return [-z*vector[0]+x*vector[2],0,x*vector[0]+z*vector[2]];
}
export function worldToGround(vector, position, target, fallback=[0,1]) {
  const [x,z]=groundAxes(position,target,fallback);
  return [-z*vector[0]+x*vector[2],0,x*vector[0]+z*vector[2]];
}

// Exact integral of exponential acceleration: no frame-count-dependent steps.
// 90% cruising speed in 173ms; 90% braking in 81ms. Focus loss hard-stops separately.
export function stepGroundVelocity(velocity, desired, seconds) {
  const dt = Math.min(0.25, Math.max(0, seconds));
  const tau = Math.hypot(...desired) > 0 ? 0.075 : 0.035;
  const decay = Math.exp(-dt / tau);
  const next = velocity.map((v,i) => desired[i] + (v-desired[i])*decay);
  const delta = velocity.map((v,i) => desired[i]*dt + (v-desired[i])*tau*(1-decay));
  if (!Math.hypot(...desired) && Math.hypot(...next) < 0.01) next.fill(0);
  return { velocity: next, delta };
}

export function constrainGroundStep(target, delta, velocity, bounds) {
  const move = [...delta], next = [...velocity];
  for (const [axis, min, max] of [[0,bounds[0],bounds[2]],[2,bounds[1],bounds[3]]]) {
    const clamped = Math.max(min, Math.min(max, target[axis]+move[axis]));
    if (Math.abs(clamped-target[axis]-move[axis]) > 1e-9) next[axis] = 0;
    move[axis] = clamped-target[axis];
  }
  move[1] = 0; next[1] = 0;
  return { velocity: next, delta: move };
}

// Smooth the actual view toward OrbitControls' input pose, using elapsed time.
// Log radius makes equal wheel distances feel proportional at city and courtyard scale.
export function smoothOrbitOffset(current, desired, seconds) {
  const spherical = v => ({ r: Math.max(1e-6,Math.hypot(...v)), yaw: Math.atan2(v[0],v[2]),
    pitch: Math.acos(Math.max(-1,Math.min(1,v[1]/Math.max(1e-6,Math.hypot(...v))))) });
  const a = spherical(current), b = spherical(desired);
  const dt = Math.min(0.25,Math.max(0,seconds));
  const turn = Math.atan2(Math.sin(b.yaw-a.yaw),Math.cos(b.yaw-a.yaw));
  const rotation = 1-Math.exp(-Math.LN2*dt/0.045);
  const zoom = 1-Math.exp(-Math.LN2*dt/0.065);
  const yaw = a.yaw + turn*rotation, pitch = a.pitch+(b.pitch-a.pitch)*rotation;
  const logRadius = Math.log(a.r)+(Math.log(b.r)-Math.log(a.r))*zoom;
  const pending = Math.abs(turn)*(1-rotation)>1e-5 || Math.abs(b.pitch-pitch)>1e-5 || Math.abs(Math.log(b.r)-logRadius)>1e-5;
  const r = Math.exp(logRadius);
  return { pending, offset: pending ? [r*Math.sin(pitch)*Math.sin(yaw),r*Math.cos(pitch),r*Math.sin(pitch)*Math.cos(yaw)] : [...desired] };
}
export function compassAngle(position, target) {
  return Math.atan2(position[0]-target[0], position[2]-target[2]) * 180 / Math.PI;
}
export function zoneRings(zone) {
  const g = zone?.planning_geometry;
  if (g?.type === 'Polygon') return g.coordinates;
  if (g?.type === 'MultiPolygon') return g.coordinates.flat();
  return [];
}
