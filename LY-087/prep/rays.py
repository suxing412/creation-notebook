# LY-087 prep: vectorised ray helpers (numpy), glTF frame (+Y up).
import numpy as np


def tri_soup(V, F):
    return V[F]  # (M,3,3)


def vertical_hits(T, x, z, eps=1e-9):
    """All surface crossings of the vertical line through (x, z). Returns sorted y list."""
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    v0x, v0z = c[:, 0] - a[:, 0], c[:, 2] - a[:, 2]
    v1x, v1z = b[:, 0] - a[:, 0], b[:, 2] - a[:, 2]
    v2x, v2z = x - a[:, 0], z - a[:, 2]
    den = v0x * v1z - v1x * v0z
    ok = np.abs(den) > eps
    den = np.where(ok, den, 1.0)
    u = (v2x * v1z - v1x * v2z) / den
    v = (v0x * v2z - v2x * v0z) / den
    m = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
    y = a[:, 1] + u * (c[:, 1] - a[:, 1]) + v * (b[:, 1] - a[:, 1])
    return np.sort(y[m])


def ray_first(T, o, d, tmax=np.inf, eps=1e-12):
    """Moller-Trumbore. Returns (t, tri_index) of nearest hit with t>1e-7, or (None, None)."""
    o = np.asarray(o, float); d = np.asarray(d, float)
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    e1, e2 = b - a, c - a
    p = np.cross(d, e2)
    det = np.einsum('ij,ij->i', e1, p)
    ok = np.abs(det) > eps
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = o - a
    u = np.einsum('ij,ij->i', s, p) * inv
    q = np.cross(s, e1)
    v = (q @ d) * inv
    t = np.einsum('ij,ij->i', e2, q) * inv
    m = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-7) & (t <= tmax)
    if not m.any():
        return None, None
    idx = np.where(m)[0]
    k = idx[np.argmin(t[idx])]
    return float(t[k]), int(k)
