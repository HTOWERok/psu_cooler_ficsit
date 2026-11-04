"""
install_presets.py — copy the DSH presets into the OrcaSlicer user profile so
they show up in the slicer's dropdowns, and keep a portable copy next to the
project (loadable via "Load preset from file").

The files are written verbatim from the flattened JSON, so what the slicer reads
is exactly what was validated by the CLI slice.
"""
from __future__ import annotations

import json
import os
import shutil
import time

HERE = os.path.dirname(os.path.abspath(__file__))
USER = os.path.join(os.environ["APPDATA"], "OrcaSlicer", "user", "default")
KEEP = os.path.join(HERE, "presets")

FILAMENT_NAME = "DSH_JAMG-HE ABS"
PROCESS_NAME = "DSH ABS 0.6 0.2mm"


def write_pair(folder, name, src_json, base_id=""):
    os.makedirs(folder, exist_ok=True)
    dst_json = os.path.join(folder, f"{name}.json")
    with open(src_json, encoding="utf-8") as fh:
        data = json.load(fh)
    data["name"] = name
    if data.get("type") == "filament":
        data["filament_settings_id"] = [name]
    elif data.get("type") == "process":
        data["print_settings_id"] = name
    with open(dst_json, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(folder, f"{name}.info"), "w", encoding="utf-8") as fh:
        fh.write("sync_info = create\nuser_id = \nsetting_id = \n"
                 f"base_id = {base_id}\nupdated_time = {int(time.time())}\n")
    return dst_json


def main():
    # portable copies next to the project
    os.makedirs(KEEP, exist_ok=True)
    f_keep = write_pair(KEEP, FILAMENT_NAME, os.path.join(HERE, "filament_flat.json"), "FFGP01")
    p_keep = write_pair(KEEP, PROCESS_NAME, os.path.join(HERE, "process_flat.json"))
    print("portable:", f_keep)
    print("portable:", p_keep)

    # live copies for the slicer
    f_live = write_pair(os.path.join(USER, "filament"), FILAMENT_NAME,
                        os.path.join(HERE, "filament_flat.json"), "FFGP01")
    p_live = write_pair(os.path.join(USER, "process"), PROCESS_NAME,
                        os.path.join(HERE, "process_flat.json"))
    print("installed:", f_live)
    print("installed:", p_live)


if __name__ == "__main__":
    main()
