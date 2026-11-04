"""
patch_project.py — repair an OrcaSlicer project exported by the CLI.

The CLI refuses to load user machine presets whose name is not pure ASCII, and
when it does load a raw system machine file its inheritance chain is ignored
(plate becomes 200x200x100). So we export with the system preset and then merge
the *flattened* machine settings straight into the project config.

Usage: python patch_project.py in.3mf out.3mf machine_flat.json "printer name"
"""
from __future__ import annotations

import json
import shutil
import sys
import zipfile

CONFIG = "Metadata/project_settings.config"
SKIP = {"name", "inherits", "from", "type", "instantiation", "setting_id",
        "printer_settings_id", "compatible_printers"}


def main():
    src, dst, machine_json, printer = sys.argv[1:5]
    with open(machine_json, encoding="utf-8") as fh:
        machine = json.load(fh)

    with zipfile.ZipFile(src) as zin:
        names = zin.namelist()
        data = {n: zin.read(n) for n in names}

    cfg = json.loads(data[CONFIG].decode("utf-8"))
    applied = 0
    for k, v in machine.items():
        if k in SKIP:
            continue
        cfg[k] = v
        applied += 1
    cfg["printer_settings_id"] = printer
    if "print_host" in machine:
        cfg["print_host"] = machine["print_host"]
    if "host_type" in machine:
        cfg["host_type"] = machine["host_type"]
    data[CONFIG] = json.dumps(cfg, ensure_ascii=False).encode("utf-8")

    shutil.copyfile(src, dst)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in names:
            zout.writestr(n, data[n])

    print(f"{dst}: merged {applied} machine keys, printer='{printer}', "
          f"area={cfg.get('printable_area')}, h={cfg.get('printable_height')}, "
          f"nozzle={cfg.get('nozzle_diameter')}")


if __name__ == "__main__":
    main()
