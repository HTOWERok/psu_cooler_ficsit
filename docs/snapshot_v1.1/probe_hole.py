"""probe_hole.py вЂ” dump the exact contour of the corner hole and test variants."""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom as g  # noqa: E402
import model as M  # noqa: E402


def hole_near(manifold, z, cx, cy, rmax=5.0):
    cs = manifold.slice(z)
    best = None
    for poly in cs.to_polygons():
        pts = np.asarray(poly, float)
        if len(pts) < 3:
            continue
        mx, my = pts[:, 0].mean(), pts[:, 1].mean()
        d = np.hypot(mx - cx, my - cy)
        if d < rmax:
            area = 0.5 * abs(np.dot(pts[:, 0], np.roll(pts[:, 1], -1))
                             - np.dot(pts[:, 1], np.roll(pts[:, 0], -1)))
            best = dict(pts=pts, area=area, cx=mx, cy=my)
    return best


def describe(tag, manifold, z, cx, cy):
    h = hole_near(manifold, z, cx, cy)
    if not h:
        print(f"{tag:22s} z={z}: no contour near ({cx},{cy})")
        return
    pts = h["pts"]
    w, hh = np.ptp(pts[:, 0]), np.ptp(pts[:, 1])
    print(f"{tag:22s} z={z}: area={h['area']:7.2f} bbox={w:5.2f}x{hh:5.2f} "
          f"centre=({h['cx']:6.2f},{h['cy']:6.2f}) verts={len(pts)}")


def main():
    base = M.build_all()["01_base"]
    for z in (19.0, 21.0, 23.0, 25.0):
        describe("base", base, z, 79.75, 35.75)
    print()
    # where is the second lobe? print extreme points of the contour
    h = hole_near(base, 22.0, 79.75, 35.75)
    if h:
        p = h["pts"]
        print("xs", p[:, 0].min().round(2), p[:, 0].max().round(2),
              "ys", p[:, 1].min().round(2), p[:, 1].max().round(2))
    # candidate features near the corner
    print("\ngeometry near the corner:")
    print("  pocket rrect 81.6 @ (44,0) r=4  -> corner arc centre (80.8, 36.8), r 4")
    print("  opening 69 @ (44,0) r=8          -> corner arc centre (70.5, 26.5), r 8")
    print("  ear dia 10 @ (79.75, 35.75), insert hole dia 5.5")
    for name, (x, y, r) in {"pocket arc": (80.8, 36.8, 4.0), "opening arc": (70.5, 26.5, 8.0)}.items():
        d = np.hypot(79.75 - x, 35.75 - y)
        print(f"  dist hole->{name} centre {d:.2f}, boundary {abs(d - r):.2f} "
              f"({'CUTS the hole' if abs(d - r) < 2.75 else 'clear'})")


if __name__ == "__main__":
    main()

