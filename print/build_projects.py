"""
build_projects.py — turn the print-ready STLs into Orca project files.

Pipeline per part:
  1. orca-slicer CLI exports a 3MF with the system machine preset (the CLI
     refuses non-ASCII preset names) and the flattened process/filament;
  2. the project config is patched with the *flattened* machine settings and the
     user's own printer preset name;
  3. the object transform is normalised to the origin (the CLI places objects
     for its 200x200 fallback plate, not for the 220x220 AD5M);
  4. optionally slice, to read back the real print statistics.

Usage: python build_projects.py [--slice] [--only NAME]
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STL_DIR = os.path.join(ROOT, "stl")
OUT_DIR = os.path.join(HERE, "projects")
GCODE_DIR = os.path.join(HERE, "_gcode")

EXE = r"C:\Program Files\OrcaSlicer\orca-slicer.exe"
# NB: the CLI only accepts the *system* machine file for the compatibility
# check; machine values are merged in afterwards from machine_flat.json.
MACHINE_EXPORT = r"C:\Program Files\OrcaSlicer\resources\profiles\Flashforge\machine\Flashforge Adventurer 5M 0.6 Nozzle.json"
PROCESS = os.path.join(HERE, "process_flat.json")
FILAMENT = os.path.join(HERE, "filament_flat.json")
MACHINE_FLAT = os.path.join(HERE, "machine_flat.json")

PRINTER_NAME = "Flashforge Adventurer 5M 0.6 Nozzle - Копировать"

PARTS = [
    ("01_base", "stl/01_base.stl"),
    ("02_wall_front", "stl/02_wall_front.stl"),
    ("03_wall_rear", "stl/03_wall_rear.stl"),
    ("04_roof", "stl/04_roof.stl"),
    ("05_filter_tray", "stl/05_filter_tray.stl"),
]


def run(args, wait=True):
    print("  $", " ".join(a if " " not in a else f'"{a}"' for a in args[1:3]), "...")
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print(p.stdout[-2000:])
        print(p.stderr[-2000:])
        raise SystemExit(f"orca exited {p.returncode}")
    return p


def export(part, stl, dst):
    args = [EXE, "--load-settings", f"{MACHINE_EXPORT};{PROCESS}",
            "--load-filaments", FILAMENT, "--export-3mf", dst, stl]
    run(args)


def patch(src, dst, printer):
    with open(MACHINE_FLAT, encoding="utf-8") as fh:
        machine = json.load(fh)
    with zipfile.ZipFile(src) as zin:
        names = zin.namelist()
        data = {n: zin.read(n) for n in names}

    cfg = json.loads(data["Metadata/project_settings.config"].decode("utf-8"))
    skip = {"name", "inherits", "from", "type", "instantiation", "setting_id",
            "printer_settings_id", "compatible_printers"}
    for k, v in machine.items():
        if k not in skip:
            cfg[k] = v
    cfg["printer_settings_id"] = printer
    # the CLI defaults to the Cool Plate (35 °C) — force the textured PEI plate
    cfg["curr_bed_type"] = "Textured PEI Plate"
    for k in ("print_host", "host_type"):
        if k in machine:
            cfg[k] = machine[k]
    data["Metadata/project_settings.config"] = json.dumps(cfg, ensure_ascii=False).encode("utf-8")

    # put the single object at the plate origin, upright
    model = data["3D/3dmodel.model"].decode("utf-8")
    model = re.sub(r'(<item\b[^>]*?transform=")[^"]*(")',
                   r"\g<1>1 0 0 0 1 0 0 0 1 0 0 0\g<2>", model, count=1)
    data["3D/3dmodel.model"] = model.encode("utf-8")

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in names:
            zout.writestr(n, data[n])
    return cfg


def slice_project(path):
    os.makedirs(GCODE_DIR, exist_ok=True)
    args = [EXE, "--slice", "1", "--outputdir", GCODE_DIR, path]
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p


def gcode_stats(gcode):
    """Read the real numbers Orca puts into the gcode (header + config block)."""
    size = os.path.getsize(gcode)
    with open(gcode, encoding="utf-8", errors="replace") as fh:
        head = fh.read(40000)
        fh.seek(max(0, size - 400000))
        tail = fh.read()
    txt = head + tail

    def grab(pat):
        m = re.search(pat, txt)
        return m.group(1).strip() if m else None

    out = {
        "layers": grab(r";\s*total layer number:\s*(\d+)"),
        "weight_g": grab(r";\s*total filament used \[g\]\s*=\s*([0-9.]+)"),
        "volume_cm3": grab(r";\s*total filament used \[cm3\]\s*=\s*([0-9.]+)"),
        "time": grab(r";\s*estimated printing time \(normal mode\)\s*=\s*(.+)"),
        "bed_first": grab(r"^M190 S([0-9.]+)"),
        "nozzle_first": grab(r"^M104 S([0-9.]+)"),
    }
    # support material present? count the type markers in chunks
    markers = 0
    with open(gcode, "rb") as fh:
        while True:
            chunk = fh.read(8 << 20)
            if not chunk:
                break
            markers += chunk.count(b";TYPE:Support")
    out["support_markers"] = markers
    return {k: v for k, v in out.items() if v is not None}


def main():
    do_slice = "--slice" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(GCODE_DIR, exist_ok=True)

    report = {}
    for name, rel in PARTS:
        if only and only not in name:
            continue
        stl = os.path.join(ROOT, rel)
        tmp = os.path.join(HERE, f"_tmp_{name}.3mf")
        final = os.path.join(OUT_DIR, f"{name}.3mf")
        print(f"[{name}] export")
        export(name, stl, tmp)
        cfg = patch(tmp, final, PRINTER_NAME)
        print(f"  -> {final}")

        if do_slice:
            cand = os.path.join(HERE, f"_slice_{name}.3mf")
            patch(tmp, cand, "Flashforge Adventurer 5M 0.6 Nozzle")
            p = slice_project(cand)
            if p.returncode != 0:
                print("  slice failed:", p.stdout[-800:], p.stderr[-800:])
                report[name] = {"slice": "failed"}
                continue
            gcodes = sorted(
                (os.path.join(GCODE_DIR, f) for f in os.listdir(GCODE_DIR) if f.endswith(".gcode")),
                key=os.path.getmtime)
            if not gcodes:
                report[name] = {"slice": "no gcode"}
                continue
            st = gcode_stats(gcodes[-1])
            st["gcode"] = os.path.basename(gcodes[-1])
            report[name] = st
            print("  ", st)
        os.remove(tmp)

    with open(os.path.join(HERE, "build_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
