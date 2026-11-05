"""Minimal read-only GLB reader for LY-050 prep measurements.

No third-party glTF library; numpy only. Reads node hierarchy, mesh
primitives (POSITION + indices), returns world-space triangles per node.
Never writes to the input file.
"""
import hashlib
import json
import struct

import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    data = open(path, "rb").read()
    magic, ver, length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, "not GLB"
    off = 12
    js, binc = None, b""
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            binc = chunk
        off += 8 + clen
    return js, binc, len(data)


def accessor(js, binc, i):
    a = js["accessors"][i]
    bv = js["bufferViews"][a["bufferView"]]
    dt = CT[a["componentType"]]
    n = NC[a["type"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride")
    item = np.dtype(dt).itemsize * n
    if stride and stride != item:
        raw = np.frombuffer(binc, dtype=np.uint8, count=stride * (a["count"] - 1) + item, offset=start)
        rows = np.lib.stride_tricks.as_strided(raw, shape=(a["count"], item), strides=(stride, 1))
        return np.frombuffer(rows.copy().tobytes(), dtype=dt).reshape(a["count"], n)
    return np.frombuffer(binc, dtype=dt, count=a["count"] * n, offset=start).reshape(a["count"], n)


def local_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=float).reshape(4, 4).T
    t = np.array(node.get("translation", [0, 0, 0]), float)
    q = node.get("rotation", [0, 0, 0, 1])
    s = np.array(node.get("scale", [1, 1, 1]), float)
    x, y, z, w = q
    r = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])
    m = np.eye(4)
    m[:3, :3] = r * s
    m[:3, 3] = t
    return m


def world_nodes(js):
    """Yield (node_index, node_name, path_names, world_matrix)."""
    out = []
    scene = js.get("scenes", [{}])[js.get("scene", 0)]

    def walk(i, parent, names):
        n = js["nodes"][i]
        m = parent @ local_matrix(n)
        nm = names + [n.get("name", f"node{i}")]
        out.append((i, n.get("name", f"node{i}"), nm, m))
        for c in n.get("children", []):
            walk(c, m, nm)

    for r in scene.get("nodes", []):
        walk(r, np.eye(4), [])
    return out


def node_triangles(path):
    """Return dict name -> dict(tris=(N,3,3) world, path=[...]) for mesh nodes."""
    js, binc, size = load(path)
    res = {}
    for i, name, names, m in world_nodes(js):
        n = js["nodes"][i]
        if "mesh" not in n:
            continue
        tris = []
        for p in js["meshes"][n["mesh"]]["primitives"]:
            if p.get("mode", 4) != 4:
                continue
            pos = accessor(js, binc, p["attributes"]["POSITION"]).astype(float)
            idx = accessor(js, binc, p["indices"]).reshape(-1).astype(np.int64) if "indices" in p else np.arange(len(pos))
            pw = (np.c_[pos, np.ones(len(pos))] @ m.T)[:, :3]
            tris.append(pw[idx].reshape(-1, 3, 3))
        t = np.concatenate(tris) if tris else np.zeros((0, 3, 3))
        key = name if name not in res else f"{name}#{i}"
        res[key] = {"tris": t, "path": names}
    return res, js, size


def bounds(tris):
    if len(tris) == 0:
        return None
    v = tris.reshape(-1, 3)
    return [v.min(0).round(6).tolist(), v.max(0).round(6).tolist()]


def apply(m16_colmajor, tris):
    m = np.array(m16_colmajor, float).reshape(4, 4).T
    v = tris.reshape(-1, 3)
    w = (np.c_[v, np.ones(len(v))] @ m.T)[:, :3]
    return w.reshape(tris.shape)
