"""
patch_3mf.py — post-process an OrcaSlicer project so it references the user's
own printer preset (the CLI cannot match non-ASCII preset names).

Usage: python patch_3mf.py in.3mf out.3mf "preset name" [key=value ...]
"""
from __future__ import annotations

import json
import shutil
import sys
import zipfile

CONFIG = "Metadata/project_settings.config"


def main():
    src, dst, printer = sys.argv[1], sys.argv[2], sys.argv[3]
    extra = {}
    for arg in sys.argv[4:]:
        k, _, v = arg.partition("=")
        extra[k] = v

    with zipfile.ZipFile(src) as zin:
        names = zin.namelist()
        data = {n: zin.read(n) for n in names}

    cfg = json.loads(data[CONFIG].decode("utf-8"))
    cfg["printer_settings_id"] = printer
    for k, v in extra.items():
        cfg[k] = v
    data[CONFIG] = json.dumps(cfg, ensure_ascii=False).encode("utf-8")

    shutil.copyfile(src, dst)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in names:
            zout.writestr(n, data[n])

    print(f"{dst}: printer_settings_id={printer}, +{len(extra)} overrides, "
          f"{len(data)} entries")


if __name__ == "__main__":
    main()
