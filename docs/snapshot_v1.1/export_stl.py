"""Export STL (print orientation + assembly) and a manifest."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import trimesh
import manifold3d as m3

import model

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STL = os.path.join(ROOT, "stl")


def to_mesh(m: m3.Manifold) -> trimesh.Trimesh:
    me = m.to_mesh()
    v = np.asarray(me.vert_properties, dtype=np.float64)[:, :3]
    f = np.asarray(me.tri_verts, dtype=np.int64)
    mesh = trimesh.Trimesh(vertices=v, faces=f, process=False)
    # hygiene pass: weld float noise, drop zero-area slivers from CSG junctions
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def main():
    os.makedirs(STL, exist_ok=True)
    parts = model.build_all()
    manifest = {}

    for name, m in parts.items():
        mesh = to_mesh(m)
        mesh.export(os.path.join(ROOT, "renders", f"{name}.stl"))
        pm, note = model.to_print(name, m)
        pmesh = to_mesh(pm)
        bb = pmesh.bounds
        size = (bb[1] - bb[0]).round(1)
        path = os.path.join(STL, f"{name}.stl")
        pmesh.export(path)
        manifest[name] = dict(
            volume_cm3=round(float(m.volume()) / 1000.0, 1),
            size_mm=[float(round(v, 1)) for v in size],
            orientation=note,
            watertight=bool(pmesh.is_watertight),
            file=os.path.relpath(path, ROOT).replace("\\", "/"),
        )
        print(f"{name:16s} {size[0]:6.1f} x {size[1]:6.1f} x {size[2]:6.1f}  "
              f"{manifest[name]['volume_cm3']:6.1f} cm3  watertight={pmesh.is_watertight}")

    with open(os.path.join(ROOT, "stl", "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
