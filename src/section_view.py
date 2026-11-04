"""
section_view.py — horizontal slices of a part, plus exact contour metrics.

manifold3d can cut a true 2D cross-section, so we do not depend on trimesh's
section machinery: every contour comes straight out of the CSG kernel.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom as g  # noqa: E402
import model as M  # noqa: E402
import render as R  # noqa: E402


def contours(manifold, z):
    """Every closed loop at height z: area, centroid, bbox."""
    cs = manifold.slice(z)
    loops = []
    for poly in cs.to_polygons():
        pts = np.asarray(poly, dtype=float)
        if len(pts) < 3:
            continue
        x, y = pts[:, 0], pts[:, 1]
        area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
        loops.append(dict(area=area, cx=x.mean(), cy=y.mean(),
                          w=x.max() - x.min(), h=y.max() - y.min()))
    return loops


def report(manifold, z, min_area=1.0):
    loops = [l for l in contours(manifold, z) if l["area"] > min_area]
    loops.sort(key=lambda l: l["area"])
    holes = []
    print(f"  z={z}: {len(loops)} contours > {min_area} mm2")
    for l in loops:
        d_eq = 2 * np.sqrt(l["area"] / np.pi)
        kind = "hole" if d_eq < 20 else "pocket"
        if kind == "hole":
            holes.append(l)
        ratio = max(l["w"], l["h"]) / max(min(l["w"], l["h"]), 1e-6)
        print(f"    {kind:6s} area={l['area']:8.1f} centre=({l['cx']:7.2f},{l['cy']:7.2f})"
              f" bbox={l['w']:5.2f}x{l['h']:5.2f} equiv-d={d_eq:5.2f}"
              f"{'  ELONGATED' if ratio > 1.25 else ''}")
    for i in range(len(holes)):
        for j in range(i + 1, len(holes)):
            d = np.hypot(holes[i]["cx"] - holes[j]["cx"], holes[i]["cy"] - holes[j]["cy"])
            if d < 30:
                print(f"    -> holes {i}-{j}: centres {d:5.2f} mm")
    return loops


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "01_base"
    zs = [float(x) for x in sys.argv[2:]] or [22.0]
    part = M.build_all()[which]
    for z in zs:
        print(f"=== {which} @ z={z}")
        report(part, z)
        slab = g.box(-300, 300, -300, 300, z - 0.4, z + 0.4)
        sec = part ^ slab
        me = sec.to_mesh()
        scene = [(np.asarray(me.vert_properties)[:, :3],
                  np.asarray(me.tri_verts), (0.85, 0.35, 0.15))]
        out = os.path.join(R.RENDERS, f"section_{which}_z{z:.0f}.png")
        R.render(scene, out, az=-90, el=90, target=(0, 0, z), ortho=205,
                 size=(1500, 1000), shadow=False, floor=False, edge=0.7)
        print("  wrote", out)


if __name__ == "__main__":
    main()
