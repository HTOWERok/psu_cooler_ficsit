"""ascii_map.py — text map of solid/void around a point, from a real CSG slice."""
from __future__ import annotations

import os
import sys

import numpy as np
from shapely.geometry import Point, Polygon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M  # noqa: E402


def solid_at(cs_polys, x, y):
    """even-odd fill test against all section loops"""
    inside = False
    p = Point(x, y)
    for poly in cs_polys:
        if Polygon(poly).contains(p):
            inside = not inside
    return inside


def main():
    cx = float(sys.argv[1]) if len(sys.argv) > 1 else 78.0
    cy = float(sys.argv[2]) if len(sys.argv) > 2 else 37.0
    half = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
    z = float(sys.argv[4]) if len(sys.argv) > 4 else 22.0
    step = float(sys.argv[5]) if len(sys.argv) > 5 else 0.4

    part = M.build_all()["01_base"]
    cs = part.slice(z)
    polys = [np.asarray(p, float) for p in cs.to_polygons() if len(p) >= 3]

    ys = np.arange(cy + half, cy - half - 1e-9, -step)
    xs = np.arange(cx - half, cx + half + 1e-9, step)
    print(f"map around ({cx},{cy}) z={z}  step={step}mm  "
          f"x {xs[0]:.1f}..{xs[-1]:.1f}  y {ys[0]:.1f}..{ys[-1]:.1f}")
    header = "     " + "".join("|" if abs((x - round(x))) < step / 2 else " " for x in xs)
    print(header)
    for y in ys:
        row = "".join("#" if solid_at(polys, x, y) else "." for x in xs)
        mark = "<" if abs(y - round(y)) < step / 2 else " "
        print(f"{y:6.1f}{mark}{row}")


if __name__ == "__main__":
    main()
