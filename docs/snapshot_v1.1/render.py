"""
render.py — software renderer (numpy z-buffer + normal buffer + edge pass) for
presentation shots. No GPU, deterministic, no external rendering engine.
"""
from __future__ import annotations

import glob
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders")

ORANGE = (0.80, 0.30, 0.10)
GRAPHITE = (0.14, 0.16, 0.18)
STEEL = (0.45, 0.47, 0.50)
DARK = (0.07, 0.08, 0.09)
PSU_GREY = (0.28, 0.29, 0.30)


# --------------------------------------------------------------------------- #
#  geometry helpers
# --------------------------------------------------------------------------- #


def load(path):
    m = trimesh.load(path, process=False)
    return np.asarray(m.vertices, float), np.asarray(m.faces, np.int64)


def box_mesh(cx, cy, cz, sx, sy, sz):
    m = trimesh.creation.box(extents=(sx, sy, sz))
    m.apply_translation([cx, cy, cz])
    return np.asarray(m.vertices, float), np.asarray(m.faces, np.int64)


def merge(items):
    vs, fs, cols, start = [], [], [], 0
    for v, f, c in items:
        vs.append(v)
        fs.append(f + start)
        start += len(v)
        cols.append(np.tile(np.asarray(c, float), (len(f), 1)))
    return np.vstack(vs), np.vstack(fs), np.vstack(cols)


class Cam:
    def __init__(self, az, el, target, ortho):
        az, el = math.radians(az), math.radians(el)
        d = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
        f = -d
        r = np.cross(f, np.array([0.0, 0.0, 1.0]))
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        self.r, self.u, self.f = r, u, f
        self.target = np.asarray(target, float)
        self.ortho = ortho
        self.d = d

    def project(self, v):
        p = v - self.target
        return np.stack([p @ self.r, p @ self.u, p @ self.f], 1)


def rasterize(p2, depth, faces, colors, normals, W, H, bgc):
    img = np.empty((H, W, 3), np.float32)
    img[:] = bgc
    zbuf = np.full((H, W), np.inf, np.float32)
    nbuf = np.zeros((H, W, 3), np.float32)

    tri_x = p2[faces]
    tri_d = depth[faces]
    minx = np.clip(np.floor(tri_x[..., 0].min(1)).astype(int), 0, W - 1)
    maxx = np.clip(np.ceil(tri_x[..., 0].max(1)).astype(int), 0, W - 1)
    miny = np.clip(np.floor(tri_x[..., 1].min(1)).astype(int), 0, H - 1)
    maxy = np.clip(np.ceil(tri_x[..., 1].max(1)).astype(int), 0, H - 1)

    for fi in np.argsort(-(maxy - miny) * (maxx - minx)):
        x0, x1, y0, y1 = minx[fi], maxx[fi], miny[fi], maxy[fi]
        if x1 < x0 or y1 < y0:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = tri_x[fi]
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den
        w1 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den
        w2 = 1.0 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not m.any():
            continue
        z = w0 * tri_d[fi, 0] + w1 * tri_d[fi, 1] + w2 * tri_d[fi, 2]
        sub_z = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = m & (z < sub_z)
        if not upd.any():
            continue
        sub_z[upd] = z[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = colors[fi]
        nbuf[y0:y1 + 1, x0:x1 + 1][upd] = normals[fi]
    return img, zbuf, nbuf


def render(pieces, path, az=36, el=22, target=(0, 0, 72), ortho=300.0,
           size=(1600, 1120), ss=2, exposure=1.0, floor=True, shadow=True,
           edge=0.6, vignette=0.12):
    verts, faces, cols = merge(pieces)
    cam = Cam(az, el, target, ortho)
    p = cam.project(verts)
    W, H = size[0] * ss, size[1] * ss
    scale = min(W, H) * 0.94 / cam.ortho
    p2 = np.stack([p[:, 0] * scale + W / 2, -p[:, 1] * scale + H * 0.5], 1)

    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    n = np.cross(v1 - v0, v2 - v0)
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-9)[:, None]

    key = np.array([0.42, -0.72, 0.55]); key /= np.linalg.norm(key)
    fill = np.array([-0.65, 0.30, 0.25]); fill /= np.linalg.norm(fill)
    rim = np.array([-0.15, 0.88, 0.40]); rim /= np.linalg.norm(rim)

    dk = np.clip(n @ key, 0, 1) ** 0.85
    df = np.clip(n @ fill, 0, 1)
    dr = np.clip(n @ rim, 0, 1) ** 2
    hemi = 0.62 + 0.38 * (n[:, 2] * 0.5 + 0.5)

    base = (cols * (0.50 * hemi)[:, None]
            + cols * (0.68 * dk)[:, None]
            + cols * (0.20 * df)[:, None]
            + np.array([1.0, 0.96, 0.90]) * (0.14 * dr)[:, None])
    base = np.clip(base * exposure, 0, 1) ** (1 / 1.06)

    bg = np.array([1.0, 1.0, 1.0], np.float32)
    img, zbuf, nbuf = rasterize(p2, p[:, 2], faces, base.astype(np.float32), n, W, H, bg)

    # ---- background / floor / shadow -------------------------------------
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    grad = (np.array([0.975, 0.976, 0.982]) * (1 - yy)
            + np.array([0.845, 0.855, 0.875]) * yy)
    grad = np.repeat(grad, W, axis=1).astype(np.float32)

    if floor:
        fy = np.arange(H, dtype=np.float32)[:, None]
        contact = H * 0.58
        fm = np.clip((fy - contact) / (H * 0.10) + 1.0, 0, 1)
        fcol = np.array([0.905, 0.910, 0.920]) * (1 - (fy / H) * 0.22)
        fcol = np.repeat(fcol[:, None, :], W, axis=1)
        grad = grad * (1 - fm[..., None]) + fcol * fm[..., None]

    if shadow:
        t = np.where(verts[:, 2] > 1e-6, verts[:, 2] / key[2], 0.0)
        gv = verts.copy()
        gv[:, 0] -= key[0] * t
        gv[:, 1] -= key[1] * t
        gv[:, 2] = 0.0
        gp = cam.project(gv)
        gp2 = np.stack([gp[:, 0] * scale + W / 2, -gp[:, 1] * scale + H * 0.5], 1)
        sh, _, _ = rasterize(gp2, gp[:, 2], faces,
                             np.ones((len(faces), 3), np.float32),
                             np.zeros((len(faces), 3), np.float32), W, H,
                             np.zeros(3, np.float32))
        alpha = np.asarray(Image.fromarray((np.clip(sh.mean(2), 0, 1) * 255).astype(np.uint8))
                           .filter(ImageFilter.GaussianBlur(radius=10 * ss)), np.float32) / 255.0
        grad = grad * (1 - 0.30 * alpha[..., None])

    mask = np.isfinite(zbuf)

    # ---- edge / crevice pass ---------------------------------------------
    if edge > 0:
        z = np.where(mask, zbuf, np.nan)
        dzx = np.nan_to_num(np.abs(np.diff(z, axis=1)))
        dzy = np.nan_to_num(np.abs(np.diff(z, axis=0)))
        dnx = 1.0 - np.abs(np.sum(nbuf[:, 1:] * nbuf[:, :-1], 2))
        dny = 1.0 - np.abs(np.sum(nbuf[1:] * nbuf[:-1], 2))
        ex = np.zeros((H, W), np.float32)
        ey = np.zeros((H, W), np.float32)
        ex[:, :-1] = dzx / 3.0 * 6.0 + dnx * 1.1
        ey[:-1] = dzy / 3.0 * 6.0 + dny * 1.1
        e = np.clip(np.maximum(ex, ey) * 1.5, 0, 1)
        e = np.asarray(Image.fromarray((e * 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(radius=0.7 * ss)), np.float32) / 255.0
        img = img * (1 - edge * e[..., None])

    out = np.where(mask[..., None], img, grad)

    if vignette > 0:
        gx = (np.arange(W, dtype=np.float32) / W - 0.5) * 2
        gy = (np.arange(H, dtype=np.float32) / H - 0.5) * 2
        r2 = gx[None, :] ** 2 + gy[:, None] ** 2
        out = out * (1 - vignette * np.clip(r2 - 0.35, 0, 1)[..., None] * 0.9)

    out = np.clip(out, 0, 1)
    im = Image.fromarray((out * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    im.save(path)
    print("wrote", os.path.basename(path), im.size)
    return path


# --------------------------------------------------------------------------- #
#  scenes
# --------------------------------------------------------------------------- #


def fan_mesh(cx, cy, z0, z1):
    """Simplified 80 mm fan ghost: frame disc, hub and ring."""
    out = []
    body = trimesh.creation.cylinder(radius=77 / 2, height=z1 - z0, sections=64)
    body.apply_translation([cx, cy, (z0 + z1) / 2])
    out.append((np.asarray(body.vertices, float), np.asarray(body.faces, np.int64), (0.06, 0.065, 0.075)))
    hub = trimesh.creation.cylinder(radius=14, height=z1 - z0 + 4, sections=32)
    hub.apply_translation([cx, cy, (z0 + z1) / 2 + 0.5])
    out.append((np.asarray(hub.vertices, float), np.asarray(hub.faces, np.int64), (0.30, 0.31, 0.33)))
    ring = trimesh.creation.cylinder(radius=36, height=2.0, sections=48)
    ring.apply_translation([cx, cy, z1 - 3.0])
    out.append((np.asarray(ring.vertices, float), np.asarray(ring.faces, np.int64), (0.10, 0.105, 0.115)))
    return out


def assembly(extra_brick=False, explode=0.0, hide=(), fans=True):
    parts = []
    for p in sorted(glob.glob(os.path.join(RENDERS, "*.stl"))):
        name = os.path.basename(p)[:-4]
        if not name[:2].isdigit() or name in hide:
            continue
        v, f = load(p)
        color = ORANGE
        if "wall" in name:
            color = GRAPHITE
        elif "roof" in name:
            color = ORANGE
        elif "filter" in name:
            color = DARK
        if explode:
            if "wall_front" in name:
                v = v + np.array([0, -explode, 0])
            elif "wall_rear" in name:
                v = v + np.array([0, explode, 0])
            elif "roof" in name:
                v = v + np.array([0, 0, explode * 1.7])
            elif "filter" in name:
                v = v + np.array([0, 0, -explode * 0.85])
        parts.append((v, f, color))
    if fans:
        for sx in (-1, 1):
            parts.extend(fan_mesh(sx * 44, 0, 6.2, 16.2))
    if extra_brick:
        parts.append((*box_mesh(0, 0, 40 + 82 / 2, 165, 35, 82), PSU_GREY))
        for sx in (-1, 1):
            parts.append((*box_mesh(sx * 84, 0, 86, 10, 26, 18), (0.10, 0.10, 0.11)))
    return parts


def main():
    render(assembly(extra_brick=True), os.path.join(RENDERS, "01_hero.png"), az=34, el=20, ortho=310)
    render(assembly(hide=("04_roof",)), os.path.join(RENDERS, "02_open.png"), az=32, el=34,
           ortho=300)
    render(assembly(explode=62, extra_brick=True), os.path.join(RENDERS, "03_exploded.png"),
           az=44, el=26, ortho=370)
    render(assembly(extra_brick=True), os.path.join(RENDERS, "04_front.png"), az=-90, el=4,
           ortho=250, size=(1500, 1050), target=(0, 0, 75))
    render(assembly(), os.path.join(RENDERS, "05_detail.png"), az=16, el=12, ortho=170,
           target=(0, -25, 50), size=(1500, 1050))
    render(assembly(extra_brick=True), os.path.join(RENDERS, "06_top.png"), az=30, el=62,
           ortho=310, target=(0, 0, 60))


if __name__ == "__main__":
    main()
