"""ear_test.py — build the pocket+ear+hole trio in isolation and compare."""
from __future__ import annotations

import os
import sys

import numpy as np
from shapely.geometry import Point, Polygon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom as g  # noqa: E402
import model as M  # noqa: E402


def solid_at(polys, x, y):
    inside = False
    p = Point(x, y)
    for poly in polys:
        if Polygon(poly).contains(p):
            inside = not inside
    return inside


def ascii_map(part, z, cx, cy, half=7.0, step=0.4):
    cs = part.slice(z)
    polys = [np.asarray(p, float) for p in cs.to_polygons() if len(p) >= 3]
    ys = np.arange(cy + half, cy - half - 1e-9, -step)
    xs = np.arange(cx - half, cx + half + 1e-9, step)
    for y in ys:
        print(f"{y:6.1f} " + "".join("#" if solid_at(polys, x, y) else "." for x in xs))


def build_test():
    body = g.box(-100, 100, -60, 60, 18.0, 26.0)
    pocket = g.extrude(g.rrect(81.6, 81.6, 4.0, 44.0, 0.0), 18.5, 26.0)
    ear = g.cyl_z(79.75, 35.75, 5.0, 18.5, 26.0, 24)
    hole = g.cyl_z(79.75, 35.75, 2.75, 18.5, 25.2, 32)
    return body - pocket + ear - hole


if __name__ == "__main__":
    print("isolated pocket+ear+hole, z=22")
    ascii_map(build_test(), 22.0, 79.75, 35.75)
    print()
    print("real base, same window, z=22")
    ascii_map(M.build_all()["01_base"], 22.0, 79.75, 35.75)
