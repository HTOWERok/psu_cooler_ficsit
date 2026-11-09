THE PROBLEM

Laptop power bricks are sealed, fanless and usually sit flat on a desk with a rubber foot on the hot side. Under load they run 55–65 °C, and every degree of that shortens the life of the electrolytic capacitors inside.

THE IDEA

Stand the brick on its narrow 35 mm edge, hang it in the air over two 80 mm fans, and let the airflow climb along both large faces inside a perforated chimney. That way the whole surface is washed by air — not just the face the brick happens to be lying on.

The tower is deliberately not a sealed box: the perforated walls give a large, low-resistance exhaust, the fans never fight back-pressure, and they stay quiet. The brick does not rest on the floor of the plinth — it hangs on two grooved brackets with 22.5 mm of clearance to each wall, so air reaches both wide faces and the bottom.

WHAT YOU GET

• Plinth with two 80 × 80 mm fan pockets sunk in from below (12.6 mm deep, so anything from 10 to 12 mm thick fits) — the fans sit just under the deck, out of sight, and are held by M4 heat-set inserts.
• Snap-on filter tray under the plinth with an 80 × 80 mm foam pocket per fan. Removes without tools for washing.
• Two perforated walls with 66 hexagonal holes each (9 mm across flats), framed panels and a solid mid-band. They carry the brick on two grooved brackets, so it hangs free.
• Removable roof with a 70 × 22 mm carry slot and engraved FICSIT nameplate; four M3 screws.
• Cable dock at the rear: two bottom cable channels, tie-down grooves and a 130 × 22 mm shelf for a USB hub or a small DC-DC.
• Keyhole-shaped (teardrop) M3/M4 holes and solid corner boots, so the screw bosses print without sagging and the brackets do not curl.

DIMENSIONS

• Assembled: 190 × 132 × 148 mm
• PSU seat: 165 × 35.6 mm, bottom at 40 mm, 2 mm locator groove
• Fans: 2 × 80 × 80 × 10–12 mm (11 mm in the photos), 71.5 mm hole pitch
• Filament: ≈ 359 g ABS (≈ 428 g PLA, not recommended)
• Print time: ≈ 11 h 30 min for all five parts on a 0.6 mm nozzle

PRINTING

No supports on any part. Everything fits a 220 × 220 mm bed. 0.2 mm layers (0.16 mm for the walls looks great in the hexes), 3 perimeters, 4–5 solid layers, 15–20 % gyroid.

Orientation matters:

• 01_base — upside down, deck on the bed, rotate about the LONG axis. Deck-down gives 137 cm² of first-layer contact and all fan pockets open upwards, nothing overhangs.
• 02_wall_front and 03_wall_rear — outer face down, all brackets, rails and ribs grow upwards, the hexes become vertical holes.
• 04_roof — top face down, also about the long axis, so the engraving lands on the first layer and reads correctly after printing.
• 05_filter_tray — flat, clips up.

ABS or ASA strongly recommended: the brick reaches 50–60 °C and PLA creeps under load. PETG-CF works too. For ABS: 100–110 °C bed, 5 mm brim, enclosure, 0–20 % part cooling, pressure advance ~0.045.

HARDWARE

• M4 heat-set insert, OD 5.5–6 × 6 mm — 8
• M4 × 18 pan head screw (M4 × 16 also works) — 8
• M3 heat-set insert, OD 4.0 × 5–6 mm (the socket prints at ~3.6 mm) — 8
• M3 × 20 countersunk screw (walls to plinth) — 4
• M3 × 18–20 countersunk screw (roof) — 4
• Silicone foot Ø10 × 2 mm — 4
• Filter foam 80 × 80 × 2 mm — 2
• Zip ties 2.5 mm — 2–3

ASSEMBLY

1. Press the 8 × M4 inserts into the fan boots from below (through the fan pockets), 4 × M3 into the plinth deck and 2 × M3 into the top rail of each wall. Soldering iron at 240 °C.
2. Drop the fans into the pockets from below, route the cable through the side groove into the cable channel, screw M4 from underneath.
3. Cut two 80 × 80 mm foam squares, seat them in the tray, snap the tray onto the plinth's lower rim.
4. Stand the walls on the plinth, brackets on their pads, 2 × M3 × 20 each, driven from above.
5. Remove the roof (4 screws), slide the brick in from the open end, let it drop into the locator grooves of the brackets. Both cables exit through the open ends — nothing gets pinched.
6. Roof back on, 4 × M3.
7. Route the two USB cables through the bottom channels into the rear dock and secure them with zip ties.

NOTES

• The plinth side windows (7 hexes per end) feed extra air if the filter clogs.
• Bottom cable channels are 8 × 4 mm — enough for two USB cables side by side.
• The roof's underside has room for a 5 V LED strip if you want the interior lit.
• Every dimension is parametric in src/model.py (dictionary P) — remix by changing four numbers for a different brick.
• Any 80 × 80 mm fan with a 71.5 mm hole pattern works. USB fans need no extra power supply. Two 80 mm fans move 20–35 CFM total, which is plenty for a 90–180 W brick: it needs airflow, not static pressure.

FILES

01_base.stl, 02_wall_front.stl, 03_wall_rear.stl, 04_roof.stl, 05_filter_tray.stl — print one of each, plus 02/03 as a pair.

SOURCES

Full parametric source, print presets (OrcaSlicer, ABS), reports and changelog: https://github.com/HTOWERok/psu_cooler_ficsit

LICENSE

CC BY-NC-SA 4.0 — print, modify and share with attribution, no commercial use.

DISCLAIMER

Fan art in the visual style of Satisfactory. FICSIT and Satisfactory are trademarks of Coffee Stain Studios. This model is not affiliated with or endorsed by Coffee Stain Studios. If you want to sell prints, remove the FICSIT lettering and list it as a generic "Industrial Cooling Tower".
