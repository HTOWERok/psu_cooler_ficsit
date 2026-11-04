import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
for f in ("machine_export.json", "machine_flat.json", "process_flat.json", "filament_flat.json"):
    p = os.path.join(HERE, f)
    d = json.load(open(p, encoding="utf-8"))
    print(f)
    print("  name:", ascii(d.get("name")))
    print("  type:", d.get("type"), "| settings_id:", ascii(d.get("printer_settings_id") or d.get("print_settings_id") or d.get("filament_settings_id")))
    if "compatible_printers" in d:
        print("  compat:", ascii(d["compatible_printers"]))
    print("  nozzle:", d.get("nozzle_diameter"), "| area:", d.get("printable_area"), "| h:", d.get("printable_height"))
