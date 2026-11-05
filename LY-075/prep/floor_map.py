# LY-075 prep: build floor/clearance maps from raycast_columns.py output (glTF frame, metres).
# Usage: python floor_map.py <cols.npz> <out_prefix>
# Writes <out_prefix>-floor.png (classes) and <out_prefix>-floor.npz (Z floor, C clearance).
import sys, numpy as np
from PIL import Image

def floor_clearance(npz):
    d = np.load(npz)
    H, NU = d['H'], d['NU']
    nx, nz, K = H.shape
    Z = np.full((nx, nz), np.nan); C = np.zeros((nx, nz))
    for i in range(nx):
        for j in range(nz):
            h = H[i, j]; nu = NU[i, j]
            ok = ~np.isnan(h)
            h = h[ok]; nu = nu[ok]
            if len(h) == 0:
                continue
            # walkable candidate = lowest-but-highest up-facing surface whose clearance >= 0.30 m,
            # scanning from the bottom so roofs are never chosen when a floor below exists.
            order = np.argsort(h)
            h = h[order]; nu = nu[order]
            for k in range(len(h)):
                if nu[k] != 1:
                    continue
                # next hit above: if it is an up-face, the span (h[k], h[k+1]) is inside a solid whose
                # bottom face coincides with this floor (wall/column standing on the platform) -> blocked.
                coinc = np.any((np.abs(h - h[k]) < 2e-3) & (nu == -1))
                if k + 1 < len(h):
                    clr = 0.0 if (coinc or nu[k + 1] == 1) else h[k + 1] - h[k]
                else:
                    clr = 0.0 if coinc else 99.0
                if clr >= 0.30 or np.isnan(Z[i, j]):
                    Z[i, j] = h[k]; C[i, j] = clr
                if clr >= 0.30:
                    break
            # prefer the lowest surface with real clearance
    return d, Z, C

if __name__ == '__main__':
    npz, pre = sys.argv[1], sys.argv[2]
    d, Z, C = floor_clearance(npz)
    np.savez_compressed(pre + '-floor.npz', Z=Z, C=C, xs=d['xs'], zs=d['zs'], step=d['step'])
    img = np.zeros(Z.shape + (3,), np.uint8) + 255
    plat = np.nanmax(Z[np.abs(Z - np.nanmedian(Z)) < 1e-3]) if np.any(~np.isnan(Z)) else 0
    lvl = np.round(Z, 3)
    img[np.isnan(Z)] = (240, 240, 240)
    img[(~np.isnan(Z)) & (C < 1.0)] = (40, 40, 40)          # wall / column / solid
    img[(~np.isnan(Z)) & (C >= 1.0) & (C < 2.0)] = (200, 60, 60)   # low headroom
    img[(~np.isnan(Z)) & (C >= 2.0) & (C < 2.6)] = (230, 160, 40)  # door-head band
    img[(~np.isnan(Z)) & (C >= 2.6) & (C < 50)] = (90, 160, 90)    # roofed interior
    img[(~np.isnan(Z)) & (C >= 50)] = (150, 200, 240)              # open sky
    img[(~np.isnan(Z)) & (np.abs(Z - plat) > 1e-3) & (C >= 1.0)] = (160, 120, 200)  # stairs / other level
    img[(~np.isnan(Z)) & (Z - plat > 0.5)] = (40, 40, 40)   # only a high surface (wall top) -> solid at floor level
    # gltf: x to the right, z down the image (north = -z at top)
    im = Image.fromarray(np.transpose(img, (1, 0, 2))[::-1, :, :] if False else np.transpose(img, (1, 0, 2)))
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(pre + '-floor.png')
    print('platform', plat, 'shape', Z.shape, 'zs range', d['zs'].min(), d['zs'].max())
