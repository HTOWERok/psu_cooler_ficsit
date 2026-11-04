# FICSIT-Style PSU Cooling Tower — listing text (EN)

> Готовый текст для Thingiverse / Printables / MakerWorld. Скопировать целиком,
> заменить только ссылку на видео/фото, если появится.

---

## Title

**FICSIT-Style Cooling Tower for 165 × 82 × 35 mm Laptop Power Brick (2 × 80 mm fans)**

## Summary

A desk-side cooling tower that turns a passively cooled laptop power brick into a
properly ventilated unit: the brick stands on edge inside a hex-perforated
industrial housing, two 80 mm USB fans blow up from a filtered plinth, and the
warm air leaves through the perforated walls and the carry slot in the roof.

## Tags

`power supply` `psu` `cooling` `fan` `80mm` `laptop` `satisfactory` `ficsit`
`desk` `organizer` `functional` `no supports` `parametric`

---

## Description

### The problem

Laptop power bricks are sealed, fanless and usually sit flat on a desk with a
rubber foot on the hot side. Under load they run 55–65 °C, and every degree of
that shortens the life of the electrolytic capacitors inside.

### The idea

Stand the brick **on its narrow 35 mm edge**, hang it in the air over two
80 mm fans, and let the airflow climb along both large faces inside a
perforated chimney. That way the whole surface is washed by air — not just the
face the brick happens to be lying on.

The tower is deliberately *not* a sealed box: the perforated walls give a large,
low-resistance exhaust, the fans never fight back-pressure, and the fans stay
quiet.

### What you get

* **Plinth** with two 80 × 80 × 10 mm fan pockets sunk in from below — the fans
  sit 2.6 mm under the deck, out of sight, and are held by M4 heat-set inserts.
* **Snap-on filter tray** under the plinth with a 80 × 80 foam pocket per fan.
  Removes without tools for washing.
* **Two perforated walls** with 66 hexagonal holes each (9 mm across flats),
  framed panels and a solid mid-band. They carry the brick on two grooved
  gusset brackets, so the brick hangs free with 22.5 mm of clearance to each
  wall.
* **Removable roof** with a 70 × 22 mm carry slot and engraved FICSIT
  nameplate; four M3 screws, no supports needed to print it.
* **Cable dock** at the rear: two bottom channels, tie-down grooves and a
  130 × 22 mm shelf for a USB hub or a small DC-DC.

### Dimensions

| | |
|---|---|
| Assembled | 190 × 132 × 148 mm |
| PSU seat | 165 × 35.6 mm, bottom at 40 mm, 2 mm locator groove |
| Fans | 2 × 80 × 80 × 10 mm, 71.5 mm hole pitch |
| Filament | ≈ 230 g ABS / 270 g PLA |

### Printing

No supports on any part. Everything fits a 220 × 220 mm bed.

| Part | Orientation | Notes |
|---|---|---|
| `01_base` | **upside down**, deck on the bed | 134 cm² first-layer contact |
| `02_wall_front` | **outer face down** | 0.16 mm layers look great in the hexes |
| `03_wall_rear` | **outer face down** | mirror of the front |
| `04_roof` | **top face down** | engraving lands on the first layer |
| `05_filter_tray` | flat | clips up |

* 0.2 mm layers (0.16 for walls), 3 perimeters, 4–5 solid layers, 15–20 % gyroid.
* ABS or ASA strongly recommended: the brick reaches 50–60 °C and PLA creeps.
  PETG-CF works too. PLA only for a cold brick.
* ABS: 100–110 °C bed, 5 mm brim, enclosure, 0–20 % fan.

### Hardware

| Item | Qty |
|---|---|
| M4 heat-set insert, OD 5.5–6 × 6 mm | 8 |
| M4 × 16–20 pan head screw | 8 |
| M3 heat-set insert, OD 4.5 × 5–6 mm | 8 |
| M3 × 20 countersunk screw (walls) | 4 |
| M3 × 18–20 countersunk screw (roof) | 4 |
| Silicone foot Ø10 × 2 mm | 4 |
| Filter foam 80 × 80 × 2 mm | 2 |
| Zip ties 2.5 mm | 2–3 |

### Assembly

1. Press the 8 × M4 inserts into the fan ears **from below** (through the fan
   pockets), 4 × M3 into the plinth deck and 2 × M3 into the top rail of each
   wall. Soldering iron at 240 °C.
2. Drop the fans into the pockets from below, route the cable through the side
   notch, screw M4 from underneath.
3. Cut two 80 × 80 foam squares, seat them in the tray, snap the tray onto the
   plinth's lower rim.
4. Stand the walls on the plinth, brackets on their pads, 2 × M3 × 20 each,
   driven from above.
5. Remove the roof (4 screws), slide the brick in from the open end, let it drop
   into the locator grooves of the brackets. Both cables exit through the open
   ends — nothing gets pinched.
6. Roof back on, 4 × M3.
7. Route the two USB cables through the bottom channels into the rear dock,
   secure with zip ties.

### Notes

* The plinth side windows (7 hexes per end) feed extra air if the filter clogs.
* Bottom cable channels are 8 × 4 mm — enough for two USB cables side by side.
* The roof's underside has room for a 5 V LED strip if you want the interior lit.
* All dimensions are parametric in `src/model.py` (dictionary `P`) — remix by
  changing four numbers for a different brick.

### Fan choice

Any 80 × 80 × 10 mm fan with a 71.5 mm hole pattern works. USB fans are ideal
because they need no extra power supply. Two 80 mm fans move 20–35 CFM total,
which is plenty for a 90–180 W brick: it needs airflow, not static pressure.

---

## License

**CC BY-NC-SA 4.0** — print, modify, share with attribution, no commercial use.

## Disclaimer

Fan art in the visual style of *Satisfactory*. **FICSIT** and *Satisfactory* are
trademarks of Coffee Stain Studios. This model is not affiliated with or endorsed
by Coffee Stain Studios. If you want to sell prints, remove the FICSIT lettering
and list it as a generic "Industrial Cooling Tower".

---

## Короткое описание (RU)

Охлаждающая башня для блока питания ноутбука 165 × 82 × 35 мм. Блок стоит на
ребре внутри перфорированного корпуса, два 80-мм USB-кулера дуют снизу через
фильтр, воздух выходит через соты в стенках и проём в крышке. Печать без
поддержек, всё влезает в 220 × 220. Нужны 8 × M4 и 8 × M3 термовставок,
4 силиконовые ножки, поролон 80 × 80. ABS/PETG-CF.
