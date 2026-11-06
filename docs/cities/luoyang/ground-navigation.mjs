// Camera-only helpers. Scene coordinates and model transforms are never changed.
export function groundPose(pose) {
  if (!pose?.position || !pose?.target || ![...pose.position, ...pose.target].every(Number.isFinite)) return null;
  const dy = -pose.target[1];
  return { target: [pose.target[0], 0, pose.target[2]], position: [pose.position[0], Math.max(0.4, pose.position[1] + dy), pose.position[2]] };
}
export function groundMovement(position, target, keys, seconds) {
  let x = target[0] - position[0], z = target[2] - position[2];
  const length = Math.hypot(x, z) || 1; x /= length; z /= length;
  let forward = Number(keys.has('KeyW')) - Number(keys.has('KeyS'));
  let right = Number(keys.has('KeyD')) - Number(keys.has('KeyA'));
  const norm = Math.hypot(forward, right) || 1; forward /= norm; right /= norm;
  const distance = Math.hypot(...position.map((v,i) => v-target[i]));
  const step = Math.min(1800, Math.max(6, distance * 0.55)) * Math.min(0.05, Math.max(0, seconds));
  return [(x*forward-z*right)*step, 0, (z*forward+x*right)*step];
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
