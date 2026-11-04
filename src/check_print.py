"""
check_print.py — printability audit for the export STL set.

For every part (in its recommended print orientation) it reports:
  * bounding box vs. the 220x220x250 build volume of the Adventurer 5M,
  * volume and estimated mass for PLA/PETG/ABS at 15% infill + 3 walls,
  * first-layer contact area (bed adhesion),
  * overhang area (> 45 deg from vertical, i.e. normal.z < -0.5) that hangs in
    the air and would need supports.
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STL = os.path.join(ROOT, "stl")
BED = (220.0, 220.0, 250.0)

DENSITY = {"PLA": 1.24, "PETG": 1.27, "ABS": 1.04}


def shell_mass_estimate(volume_mm3: float):
    """Rough print mass: 3 perimeters + 15% infill, 0.75 solid-shell factor."""
    return {k: round(volume_mm3 * v / 1000.0 * 0.45, 1) for k, v in DENSITY.items()}


def main():
    rows = []
    for path in sorted(glob.glob(os.path.join(STL, "*.stl"))):
        name = os.path.basename(path)[:-4]
        m = trimesh.load(path)          # merges the STL's duplicated vertices
        v = np.asarray(m.vertices, float)
        f = np.asarray(m.faces, np.int64)
        tri = v[f]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        area = 0.5 * np.linalg.norm(n, axis=1)
        nz = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-9)
        cz = tri[:, :, 2].mean(1)

        over = (nz < -0.5) & (cz > 0.6)
        bed = (cz <= 0.6) & (nz < -0.5)
        bb = v.max(0) - v.min(0)

        rows.append(dict(
            name=name,
            size=[round(float(x), 1) for x in bb],
            fits=bool(bb[0] <= BED[0] and bb[1] <= BED[1] and bb[2] <= BED[2]),
            volume_cm3=round(float(m.volume) / 1000.0, 1),
            mass_g=shell_mass_estimate(float(m.volume)),
            overhang_cm2=round(float(area[over].sum()) / 100.0, 2),
            bed_contact_cm2=round(float(area[bed].sum()) / 100.0, 2),
            watertight=bool(m.is_watertight),
        ))

    for r in rows:
        print(f"{r['name']:16s} {r['size'][0]:6.1f}x{r['size'][1]:6.1f}x{r['size'][2]:6.1f} "
              f"fits={r['fits']!s:5s} vol={r['volume_cm3']:6.1f}cm3 "
              f"mass~{r['mass_g']['PLA']:5.1f}g(PLA) "
              f"overhang={r['overhang_cm2']:5.2f}cm2 bed={r['bed_contact_cm2']:5.1f}cm2")

    with open(os.path.join(ROOT, "stl", "print_check.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
