"""LY-091 prep: minimal read-only GLB reader (numpy only).

Decodes node hierarchy, mesh primitives (POSITION + indices), materials and
embedded images. Refuses (raises) on EXT_meshopt_compression / KHR_draco, so a
compressed candidate cannot silently pass geometry checks.
"""
import hashlib
import json
import struct

import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
COMPRESSED = {"EXT_meshopt_compression", "KHR_draco_mesh_compression", "KHR_meshopt_compression"}


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


class GLB:
    def __init__(self, path):
        self.path = path
        raw = open(path, "rb").read()
        self.raw = raw
        self.bytes = len(raw)
        self.sha256 = sha256_bytes(raw)
        magic, ver, length = struct.unpack("<4sII", raw[:12])
        if magic != b"glTF" or ver != 2:
            raise ValueError("not glTF2 binary: %s" % path)
        if length != len(raw):
            raise ValueError("GLB header length %d != file length %d" % (length, len(raw)))
        off = 12
        self.json = None
        self.bin = b""
        while off < len(raw):
            clen, ctype = struct.unpack("<II", raw[off:off + 8])
            data = raw[off + 8: off + 8 + clen]
            if ctype == 0x4E4F534A:
                self.json = json.loads(data.decode("utf-8"))
            elif ctype == 0x004E4942:
                self.bin = data
            off += 8 + clen
        j = self.json
        used = set(j.get("extensionsUsed", []))
        self.compressed = sorted(used & COMPRESSED)

    # ---------------------------------------------------------------- accessors
    def accessor(self, idx):
        j = self.json
        a = j["accessors"][idx]
        if "sparse" in a:
            raise ValueError("sparse accessor not supported")
        n = a["count"]
        comps = NC[a["type"]]
        dt = np.dtype(CT[a["componentType"]])
        if "bufferView" not in a:
            return np.zeros((n, comps), dt)
        bv = j["bufferViews"][a["bufferView"]]
        if bv.get("buffer", 0) != 0:
            raise ValueError("external buffer not supported")
        start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride", 0) or dt.itemsize * comps
        if stride == dt.itemsize * comps:
            arr = np.frombuffer(self.bin, dt, n * comps, start).reshape(n, comps)
        else:
            rows = [np.frombuffer(self.bin, dt, comps, start + i * stride) for i in range(n)]
            arr = np.stack(rows) if rows else np.zeros((0, comps), dt)
        return arr

    # ---------------------------------------------------------------- scene
    @staticmethod
    def node_local(node):
        if "matrix" in node:
            return np.array(node["matrix"], float).reshape(4, 4).T
        t = np.array(node.get("translation", [0, 0, 0]), float)
        q = np.array(node.get("rotation", [0, 0, 0, 1]), float)
        s = np.array(node.get("scale", [1, 1, 1]), float)
        x, y, z, w = q
        R = np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ])
        M = np.eye(4)
        M[:3, :3] = R * s
        M[:3, 3] = t
        return M

    def mesh_instances(self, root=np.eye(4)):
        """Yield (node_index, node_name, world_matrix, mesh_index)."""
        j = self.json
        scene = j.get("scenes", [{}])[j.get("scene", 0)] if j.get("scenes") else {"nodes": list(range(len(j.get("nodes", []))))}
        out = []

        def walk(i, parent):
            nd = j["nodes"][i]
            M = parent @ self.node_local(nd)
            if "mesh" in nd:
                out.append((i, nd.get("name", ""), M, nd["mesh"]))
            for c in nd.get("children", []):
                walk(c, M)

        for i in scene.get("nodes", []):
            walk(i, root)
        return out

    def primitive_arrays(self, mesh_index):
        if self.compressed:
            raise ValueError("compressed GLB (%s): decode before geometry checks" % self.compressed)
        res = []
        for p in self.json["meshes"][mesh_index]["primitives"]:
            pos = self.accessor(p["attributes"]["POSITION"]).astype(np.float64)
            mode = p.get("mode", 4)
            if "indices" in p:
                idx = self.accessor(p["indices"]).reshape(-1).astype(np.int64)
            else:
                idx = np.arange(len(pos), dtype=np.int64)
            res.append({"pos": pos, "idx": idx, "mode": mode, "material": p.get("material"),
                        "attrs": sorted(p["attributes"].keys())})
        return res

    def world_triangles(self, root=np.eye(4), name_filter=None):
        """Return (tris[N,3,3] world, owner list of node names per tri)."""
        tris, owners = [], []
        for ni, name, M, mi in self.mesh_instances(root):
            if name_filter and not name_filter(name):
                continue
            for pr in self.primitive_arrays(mi):
                if pr["mode"] != 4:
                    continue
                P = np.c_[pr["pos"], np.ones(len(pr["pos"]))] @ M.T
                t = P[:, :3][pr["idx"].reshape(-1, 3)]
                tris.append(t)
                owners += [name] * len(t)
        if not tris:
            return np.zeros((0, 3, 3)), []
        return np.concatenate(tris), owners

    # ---------------------------------------------------------------- fingerprints
    def fingerprint(self):
        """Per mesh-node fingerprint: geometry hash, tri count, material names, local matrix."""
        j = self.json
        mats = j.get("materials", [])
        nodes = []
        for ni, name, M, mi in self.mesh_instances():
            h = hashlib.sha256()
            tri = 0
            mnames = []
            lo = np.full(3, np.inf)
            hi = np.full(3, -np.inf)
            finite = True
            for pr in self.primitive_arrays(mi):
                h.update(pr["pos"].astype(np.float32).tobytes())
                h.update(pr["idx"].astype(np.uint32).tobytes())
                tri += len(pr["idx"]) // 3 if pr["mode"] == 4 else 0
                m = pr["material"]
                mnames.append(mats[m].get("name", "#%d" % m) if m is not None else None)
                if len(pr["pos"]):
                    finite &= bool(np.isfinite(pr["pos"]).all())
                    P = np.c_[pr["pos"], np.ones(len(pr["pos"]))] @ M.T
                    lo = np.minimum(lo, P[:, :3].min(0))
                    hi = np.maximum(hi, P[:, :3].max(0))
            nodes.append({
                "node": name,
                "mesh": j["meshes"][mi].get("name", ""),
                "triangles": int(tri),
                "materials": mnames,
                "geomSha256": h.hexdigest(),
                "matrixInFile": [round(float(x), 6) for x in M.T.reshape(-1)],
                "fileAabb": [[round(float(x), 4) for x in lo], [round(float(x), 4) for x in hi]],
                "finite": finite,
            })
        imgs = j.get("images", [])
        return {
            "bytes": self.bytes,
            "sha256": self.sha256,
            "generator": j.get("asset", {}).get("generator"),
            "extensionsUsed": j.get("extensionsUsed", []),
            "meshNodes": nodes,
            "triangles": int(sum(n["triangles"] for n in nodes)),
            "materials": [m.get("name") for m in mats],
            "images": len(imgs),
            "externalImageUris": [im["uri"] for im in imgs if "uri" in im and not im["uri"].startswith("data:")],
        }
