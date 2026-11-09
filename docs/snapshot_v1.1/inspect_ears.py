"""
inspect_ears.py — what exactly is at the fan-ear region of the base?

Takes horizontal sections through the pin bosses and lists every hole with its
centre, radius and the distance to its nearest neighbour.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M  # noqa: E402


def holes_at(manifold, z):
    import trimesh

    me = manifold.to_mesh()
    mesh = trimesh.Trimesh(
        vertices=np.asarray(me.vert_properties)[:, :3],
        faces=np.asarray(me.tri_verts), process=False)
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return []
    poly = sec.to_planar()[0].polygons_full
    out = []
    for p in poly:
        for ring in p.interiors:
            from shapely.geometry import Polygon
            g = Polygon(ring)
            c = g.centroid
            r = np.sqrt(g.area / np.pi)
            out.append((round(c.x, 2), round(c.y, 2), round(r, 2)))
    return sorted(out)


def main():
    base = M.build_base()
    for z in (19.5, 22.0, 24.5):
        hs = holes_at(base, z)
        print(f"--- z={z}: {len(hs)} holes")
        for x, y, r in hs:
            print(f"    ({x:8.2f}, {y:8.2f})  r={r:5.2f}  d={2*r:5.2f}")
        # nearest neighbours
        if hs:
            pts = np.array([[h[0], h[1]] for h in hs])
            for i in range(len(pts)):
                d = [np.hypot(*(pts[i] - pts[j])) for j in range(len(pts)) if j != i]
                if d:
                    k = int(np.argmin(d))
                    j = [jj for jj in range(len(pts)) if jj != i][k]
                    if i < j:
                        gap = np.hypot(*(pts[i] - pts[j])) - hs[i][2] - hs[j][2]
                        print(f"    closest pair: {i}-{j}  centres {np.hypot(*(pts[i]-pts[j])):.2f} mm"
                              f"  wall between holes {gap:.2f} mm")


if __name__ == "__main__":
    main()
