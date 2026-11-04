"""
test_variants.py — A/B checks on the print settings, using the real slicer.

  A: supports ON (the user's original process) vs OFF  -> what would they cost?
  B: filament_shrink 100.4 % vs 100 %                  -> is the compensation live?
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXE = r"C:\Program Files\OrcaSlicer\orca-slicer.exe"
SYS_MACHINE = r"C:\Program Files\OrcaSlicer\resources\profiles\Flashforge\machine\Flashforge Adventurer 5M 0.6 Nozzle.json"
PROCESS = os.path.join(HERE, "process_flat.json")
FILAMENT = os.path.join(HERE, "filament_flat.json")
GCODE = os.path.join(HERE, "_gcode")

sys.path.insert(0, HERE)
from build_projects import gcode_stats, patch  # noqa: E402


def variant(tag, proc_over=None, fil_over=None, stl="stl/05_filter_tray.stl"):
    proc, fil = PROCESS, FILAMENT
    if proc_over:
        d = json.load(open(PROCESS, encoding="utf-8"))
        d.update(proc_over)
        proc = os.path.join(HERE, f"_proc_{tag}.json")
        json.dump(d, open(proc, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if fil_over:
        d = json.load(open(FILAMENT, encoding="utf-8"))
        d.update(fil_over)
        fil = os.path.join(HERE, f"_fil_{tag}.json")
        json.dump(d, open(fil, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    raw = os.path.join(HERE, f"_raw_{tag}.3mf")
    p = subprocess.run(
        [EXE, "--load-settings", f"{SYS_MACHINE};{proc}", "--load-filaments", fil,
         "--export-3mf", raw, os.path.join(ROOT, stl)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print(tag, "export failed", p.stdout[-400:])
        return None

    prj = os.path.join(HERE, f"_var_{tag}.3mf")
    patch(raw, prj, "Flashforge Adventurer 5M 0.6 Nozzle")

    for f in os.listdir(GCODE):
        if f.endswith(".gcode"):
            os.remove(os.path.join(GCODE, f))
    p = subprocess.run([EXE, "--slice", "1", "--outputdir", GCODE, prj],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print(tag, "slice failed", p.stdout[-400:])
        return None
    g = [os.path.join(GCODE, f) for f in os.listdir(GCODE) if f.endswith(".gcode")]
    st = gcode_stats(g[0])
    print(f"{tag:22s} weight={st.get('weight_g')} g  time={st.get('time')}  "
          f"support_markers={st.get('support_markers')}")
    for f in (raw, prj):
        if os.path.exists(f):
            os.remove(f)
    return st


if __name__ == "__main__":
    print("baseline (as delivered):")
    variant("baseline")
    print("A: supports ON (tree auto, 55 deg):")
    variant("supports_on", proc_over={"enable_support": "1"})
    print("B: no shrink compensation:")
    variant("shrink_100", fil_over={"filament_shrink": ["100"]})
