"""
flatten.py — turn an OrcaSlicer preset (with its inheritance chain) into a
single self-contained JSON.

Orca's CLI resolves preset inheritance inconsistently for machine presets
(the parent chain silently falls back to defaults), which corrupts the plate
size and nozzle diameter in exported projects. A flattened preset has nothing
to resolve, so what we verify is what the slicer gets.

Usage:  python flatten.py "preset name" out.json [override.json]
"""
from __future__ import annotations

import json
import os
import sys

PROFILES = r"C:\Program Files\OrcaSlicer\resources\profiles"
USER = os.path.join(os.environ["APPDATA"], "OrcaSlicer", "user", "default")


def build_index():
    idx = {}
    roots = [PROFILES, USER]
    for root in roots:
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                if not f.endswith(".json"):
                    continue
                path = os.path.join(dirpath, f)
                try:
                    with open(path, encoding="utf-8") as fh:
                        data = json.load(fh)
                except Exception:
                    continue
                name = data.get("name")
                if not name:
                    continue
                kind = data.get("type")
                if kind is None:                     # user presets carry no type
                    low = dirpath.lower()
                    kind = ("machine" if "machine" in low else
                            "process" if "process" in low else
                            "filament" if "filament" in low else None)
                idx[(name, kind)] = data
                idx.setdefault((name, None), data)
    return idx


def resolve(name, kind, idx, seen=None):
    seen = seen or []
    if name in seen:
        raise RuntimeError("inheritance loop: " + " -> ".join(seen + [name]))
    data = idx.get((name, kind)) or idx.get((name, None))
    if data is None:
        raise KeyError(f"preset not found: {name!r} ({kind})")
    parent = data.get("inherits")
    out = resolve(parent, kind, idx, seen + [name]) if parent else {}
    merged = dict(out)
    for k, v in data.items():
        if k in ("inherits",):
            continue
        merged[k] = v
    return merged


def main():
    name, out = sys.argv[1], sys.argv[2]
    override = sys.argv[3] if len(sys.argv) > 3 else None
    idx = build_index()
    # find the kind of the requested preset
    kind = None
    for (n, k), _d in idx.items():
        if n == name and k:
            kind = k
            break
    flat = resolve(name, kind, idx)
    if override:
        with open(override, encoding="utf-8") as fh:
            ov = json.load(fh)
        for k, v in ov.items():
            flat[k] = v
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(flat, fh, ensure_ascii=False, indent=2)
    print(f"{name} -> {out}: {len(flat)} keys, type={flat.get('type')}, name={flat.get('name')}")


if __name__ == "__main__":
    main()
