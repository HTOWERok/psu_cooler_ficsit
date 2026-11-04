"""
check_holes.py — integrity check for every fastener hole in the printed parts.

For a list of expected holes it slices the solid and verifies that each hole is
a *separate* contour of the right size at the right place. A hole that has
merged with a neighbouring hole or with an opening shows up as an oversized or
shifted contour — exactly the defect that made the M3 and M4 holes collide.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M  # noqa: E402

TOL_POS = 0.6      # mm
TOL_DIA = 0.35     # mm


def loops_at(manifold, z):
    out = []
    for poly in manifold.slice(z).to_polygons():
        p = np.asarray(poly, float)
        if len(p) < 3:
            continue
        a = 0.5 * abs(np.dot(p[:, 0], np.roll(p[:, 1], -1))
                      - np.dot(p[:, 1], np.roll(p[:, 0], -1)))
        if a < 0.5:
            continue
        out.append((p[:, 0].mean(), p[:, 1].mean(),
                    2 * np.sqrt(a / np.pi), a, np.ptp(p[:, 0]), np.ptp(p[:, 1])))
    return out


def solid_at(polys, x, y):
    from shapely.geometry import Point, Polygon
    inside = False
    p = Point(x, y)
    for poly in polys:
        if Polygon(poly).contains(p):
            inside = not inside
    return inside


def wall_thickness(part, expected, z, min_wall=(1.0, 1.5)):
    """March outwards from every hole edge and find the thinnest material."""
    polys = [np.asarray(p, float) for p in part.slice(z).to_polygons() if len(p) >= 3]
    bad = 0
    print(f"-- wall thickness around holes @ z={z}")
    for (x, y, d, name) in expected:
        r = d / 2
        worst = 99.0
        worst_ang = 0
        for k in range(72):
            a = 2 * np.pi * k / 72
            step = 0.1
            t = 0.15                      # start just off the hole wall
            while t < 12.0:
                px = x + (r + t) * np.cos(a)
                py = y + (r + t) * np.sin(a)
                if not solid_at(polys, px, py):
                    break
                t += step
            if t < worst:
                worst, worst_ang = t, np.degrees(a)
        limit = min_wall[0] if d > 5 else min_wall[1]
        ok = worst >= limit
        print(f"   {'ok ' if ok else 'THIN'} {name:6s} ({x:7.2f},{y:7.2f}) "
              f"min wall {worst:4.2f} mm at {worst_ang:5.0f} deg (limit {limit})")
        if not ok:
            bad += 1
    return bad


def check(part, expected, z, label):
    loops = loops_at(part, z)
    bad = 0
    print(f"-- {label}: {len(expected)} expected holes @ z={z}")
    for (x, y, d, name) in expected:
        cand = [l for l in loops if np.hypot(l[0] - x, l[1] - y) < TOL_POS]
        if not cand:
            print(f"   MISSING  {name} at ({x:7.2f},{y:7.2f}) d={d}")
            bad += 1
            continue
        cx, cy, d_eq, area, w, h = cand[0]
        ok = abs(d_eq - d) < TOL_DIA and max(w, h) < d + TOL_DIA
        flag = "ok " if ok else "BAD"
        print(f"   {flag} {name:6s} ({x:7.2f},{y:7.2f}) d={d:4.2f} -> measured "
              f"d={d_eq:5.2f} bbox={w:5.2f}x{h:5.2f} centre=({cx:7.2f},{cy:7.2f})")
        if not ok:
            bad += 1
    return bad


def main():
    parts = M.build_all()
    base = parts["01_base"]
    exp = []
    for sx in (-1, 1):
        for ax in (-1, 1):
            for ay in (-1, 1):
                exp.append((sx * 44 + ax * 35.75, ay * 35.75, 5.5, "M4 fan"))
        for sy in (-1, 1):
            exp.append((sx * 70, sy * 36.5, 4.4, "M3 wall"))
    bad = check(base, exp, 22.0, "01_base")
    bad += wall_thickness(base, exp, 22.0)
    # wall: the M3 clearance must pass through the bracket shelf
    wall = parts["03_wall_rear"]
    exp_w = [(sx * 70, 36.5, 3.6, "M3 clear") for sx in (-1, 1)]
    bad += check(wall, exp_w, 38.0, "03_wall_rear (through the shelf)")
    print("\nRESULT:", "OK — no merged holes, walls thick enough" if bad == 0 else f"{bad} problem(s)")


if __name__ == "__main__":
    main()
