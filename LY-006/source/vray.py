# Vertical ray sampler: for each (x,z) return all surface heights y of a triangle soup
# whose XZ projection contains the point (both windings), with upward/downward facing flag.
import numpy as np


class VSampler:
    def __init__(self, tris, cell=8.0):
        # tris: (M,3,3) float64 world coords
        self.t = tris
        self.cell = cell
        xmin = tris[:, :, 0].min(1); xmax = tris[:, :, 0].max(1)
        zmin = tris[:, :, 2].min(1); zmax = tris[:, :, 2].max(1)
        self.grid = {}
        for i in range(len(tris)):
            for gx in range(int(np.floor(xmin[i] / cell)), int(np.floor(xmax[i] / cell)) + 1):
                for gz in range(int(np.floor(zmin[i] / cell)), int(np.floor(zmax[i] / cell)) + 1):
                    self.grid.setdefault((gx, gz), []).append(i)
        for k in self.grid:
            self.grid[k] = np.array(self.grid[k], dtype=np.int64)

    def heights(self, x, z, eps=1e-9):
        key = (int(np.floor(x / self.cell)), int(np.floor(z / self.cell)))
        ids = self.grid.get(key)
        if ids is None:
            return []
        T = self.t[ids]
        a, b, c = T[:, 0], T[:, 1], T[:, 2]
        # 2D barycentric in XZ
        v0x, v0z = c[:, 0] - a[:, 0], c[:, 2] - a[:, 2]
        v1x, v1z = b[:, 0] - a[:, 0], b[:, 2] - a[:, 2]
        v2x, v2z = x - a[:, 0], z - a[:, 2]
        den = v0x * v1z - v1x * v0z
        ok = np.abs(den) > 1e-12
        den = np.where(ok, den, 1.0)
        u = (v2x * v1z - v1x * v2z) / den
        v = (v0x * v2z - v2x * v0z) / den
        inside = ok & (u >= -eps) & (v >= -eps) & (u + v <= 1 + eps)
        y = a[:, 1] + u * (c[:, 1] - a[:, 1]) + v * (b[:, 1] - a[:, 1])
        n = np.cross(b - a, c - a)
        nl = np.linalg.norm(n, axis=1)
        ny = np.where(nl > 0, n[:, 1] / np.where(nl > 0, nl, 1), 0)
        out = sorted(zip(y[inside].tolist(), ny[inside].tolist()))
        return out
