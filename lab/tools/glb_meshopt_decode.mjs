// Private repair candidate: only decode validated EXT_meshopt buffer views.
// Uses the repository's existing vendored decoder, never downloads or installs.
import fs from 'node:fs';
const MAX_INPUT = 72 * 1024 * 1024;
const MAX_OUTPUT = 128 * 1024 * 1024;
function check(ok, message) { if (!ok) throw new Error(message); }
try {
  let size = 0; const chunks = [];
  for await (const chunk of process.stdin) {
    size += chunk.length; check(size <= MAX_INPUT, 'input limit'); chunks.push(chunk);
  }
  const input = Buffer.concat(chunks);
  check(input.length >= 4, 'header missing');
  const headerLength = input.readUInt32LE(0);
  check(headerLength <= 8 * 1024 * 1024 && 4 + headerLength <= input.length, 'header length');
  const jobs = JSON.parse(input.subarray(4, 4 + headerLength).toString('utf8'));
  check(Array.isArray(jobs) && jobs.length <= 100000, 'jobs');
  const binary = input.subarray(4 + headerLength); let total = 0;
  for (const j of jobs) {
    for (const k of ['byteOffset', 'byteLength', 'byteStride', 'count']) check(Number.isSafeInteger(j[k]) && j[k] >= 0, k);
    check(j.byteLength > 0 && j.count > 0 && j.byteStride > 0 && j.byteStride <= 256, 'layout');
    check(j.byteOffset + j.byteLength <= binary.length, 'source bounds');
    check(['ATTRIBUTES', 'TRIANGLES', 'INDICES'].includes(j.mode), 'mode');
    check(['NONE', 'OCTAHEDRAL', 'QUATERNION', 'EXPONENTIAL'].includes(j.filter), 'filter');
    check(j.mode === 'ATTRIBUTES' ? j.byteStride % 4 === 0 : [2, 4].includes(j.byteStride) && j.filter === 'NONE', 'stride');
    check(j.mode !== 'TRIANGLES' || j.count % 3 === 0, 'triangle count');
    check(j.filter !== 'OCTAHEDRAL' || [4, 8].includes(j.byteStride), 'octahedral stride');
    check(j.filter !== 'QUATERNION' || j.byteStride === 8, 'quaternion stride');
    check(j.filter !== 'EXPONENTIAL' || j.byteStride % 4 === 0, 'exponential stride');
    total += j.count * j.byteStride; check(Number.isSafeInteger(total) && total <= MAX_OUTPUT, 'output limit');
  }
  // A data URL makes the fixed .js ES module work without changing package.json
  // or requiring Node's newer module-type detection. Decoder source is trusted
  // repository code, not supplied by the GLB or by the protocol.
  const source = fs.readFileSync(new URL('../../docs/vendor/meshopt_decoder.module.js', import.meta.url));
  const { MeshoptDecoder } = await import('data:text/javascript;base64,' + source.toString('base64'));
  check(MeshoptDecoder?.supported === true, 'decoder unavailable');
  await MeshoptDecoder.ready;
  for (const j of jobs) {
    const target = new Uint8Array(j.count * j.byteStride);
    MeshoptDecoder.decodeGltfBuffer(target, j.count, j.byteStride,
      binary.subarray(j.byteOffset, j.byteOffset + j.byteLength), j.mode, j.filter);
    // Synchronous write avoids unbounded queued buffers; output has a hard cap.
    fs.writeFileSync(1, target);
  }
} catch (error) {
  fs.writeSync(2, String(error?.message ?? error).slice(0, 1000) + '\n');
  process.exitCode = 1;
}
