"""
model.py вЂ” FICSIT-style cooling tower for a 165x82x35 laptop power brick.

Assembly coordinates:
    X = along the brick (165), Y = across the brick (35), Z = up, z=0 = table.
Units: mm.

Design intent
-------------
* plinth with two 80 mm fans sunk in from below, air intake through a bottom
  filter tray, exhaust up the tower through perforated walls;
* brick stands on edge between the walls, slid in from the end and seated in
  grooved gusset brackets;
* removable roof with a carry slot;
* every part prints without supports (see to_print()).
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import manifold3d as m3
from shapely import affinity
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union

import geom as g

# --------------------------------------------------------------------------- #
#  parameters
# --------------------------------------------------------------------------- #

P = dict(
    psu_l=165.0, psu_w=35.0, psu_h=82.0,
    fan=80.0, fan_t=11.0, fan_holes=71.5,
    base_x=190.0, base_y=108.0, base_corner=10.0,
    foot_h=6.0, base_h=20.0, base_chamfer=1.5,
    fan_cx=44.0,
    pocket=81.6, pocket_z1=18.6,
    opening=69.0,
    wing_x=130.0, wing_y0=54.0, wing_y1=76.0,
    wall_y=40.0, wall_t=3.2, wall_l=176.0, wall_h=110.0,
    seat_z=40.0,
    roof_t=7.0,
)

Z_DECK = P["foot_h"] + P["base_h"]            # 26
Z_TOP = Z_DECK + P["wall_h"]                  # 136
Z_SEAT = P["seat_z"]                          # 40
Z_ROOF = Z_TOP + P["roof_t"]                  # 143

FONT = r"C:\Windows\Fonts\arialbd.ttf"


# --------------------------------------------------------------------------- #
#  small helpers
# --------------------------------------------------------------------------- #


def _parts(geom):
    """Flatten a shapely result into a list of polygons."""
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    out = []
    for gp in getattr(geom, "geoms", []):
        out.extend(_parts(gp))
    return out


def _center_on_face(solid, x_center, z_center, y_face):
    bb = solid.bounding_box()
    return solid.translate(
        [x_center - 0.5 * (bb[0] + bb[3]), y_face, z_center - 0.5 * (bb[2] + bb[5])]
    )


def text_front(text, size, depth, y_face, z_center, x_center=0.0, font=FONT, bevel=0.45):
    """Raised, bevelled text on a face whose outward normal is -Y."""
    poly = g.text_poly(text, size, font)
    s = g.bevel_extrude(poly, 0.0, depth, bevel=bevel).rotate([90, 0, 0])
    return _center_on_face(s, x_center, z_center, y_face)


def text_top(text, size, depth, z_face, y_center, x_center=0.0, font=FONT):
    """Text engraved into / raised on a +Z face."""
    s = g.text_solid(text, size, depth, font=font)
    bb = s.bounding_box()
    return s.translate([x_center - 0.5 * (bb[0] + bb[3]), y_center - 0.5 * (bb[1] + bb[4]), z_face])


def hazard_band(poly_region, pitch=8.0, width=3.0, angle=45.0):
    minx, miny, maxx, maxy = poly_region.bounds
    diag = math.hypot(maxx - minx, maxy - miny)
    bars = []
    for i in range(-int(diag / pitch) - 2, int(diag / pitch) + 3):
        r = sbox(-diag, -width / 2, diag, width / 2)
        r = affinity.rotate(r, angle, origin=(0, 0))
        r = affinity.translate(r, (minx + maxx) / 2 + i * pitch, (miny + maxy) / 2)
        bars.append(r)
    return unary_union(bars).intersection(poly_region)


def plinth_outline():
    return unary_union(
        [
            g.rrect(P["base_x"], P["base_y"], P["base_corner"]),
            g.rrect(P["wing_x"], P["wing_y1"] - P["wing_y0"], 6.0, 0,
                    (P["wing_y0"] + P["wing_y1"]) / 2),
        ]
    )


# --------------------------------------------------------------------------- #
#  01 PLINTH
# --------------------------------------------------------------------------- #


def build_base():
    z0, z1 = P["foot_h"], Z_DECK
    outline = plinth_outline()
    body = g.slab(outline, z0, z1, chamfer=P["base_chamfer"], bottom_chamfer=1.0)

    # ---- feet ------------------------------------------------------------
    feet = [g.cbox(sx * 84, sy * 46, z0 / 2, 16, 16, z0)
            for sx in (-1, 1) for sy in (-1, 1)]
    body = body + m3.Manifold.batch_boolean(feet, m3.OpType.Add)
    pads = [g.cyl_z(sx * 84, sy * 46, 5.0, -0.5, 2.0, 48)
            for sx in (-1, 1) for sy in (-1, 1)]
    body = body - m3.Manifold.batch_boolean(pads, m3.OpType.Add)

    # ---- fan pockets (open at the bottom) --------------------------------
    pockets = [g.extrude(g.rrect(P["pocket"], P["pocket"], 4.0, sx * P["fan_cx"], 0.0),
                         z0 - 0.5, P["pocket_z1"]) for sx in (-1, 1)]
    body = body - m3.Manifold.batch_boolean(pockets, m3.OpType.Add)

    # ---- cable gutters along the pocket sides ---------------------------
    # the fan wire leaves the frame at a corner, not at the middle: a 7 mm
    # wide, 4 mm deep gutter along the front and rear side of each pocket
    # (hidden under the filter tray) lets it reach the channels at x = +-44.
    # It stops at the pocket ends, otherwise it would undercut the 5.6 mm
    # wall between the two fans.
    gutters = []
    for sx in (-1, 1):
        cx = sx * P["fan_cx"]
        half = P["pocket"] / 2
        pocket = g.rrect(P["pocket"], P["pocket"], 4.0, cx, 0.0)
        ring = pocket.buffer(7.0, join_style=1).difference(pocket)
        ring = ring.intersection(g.sbox(cx - half, -50.0, cx + half, 50.0))
        for poly in _parts(ring):
            gutters.append(g.extrude(poly, z0 - 0.2, z0 + 4.0))
    body = body - m3.Manifold.batch_boolean(gutters, m3.OpType.Add)

    # ---- deck openings, screw ears, M4 heat-set holes --------------------
    holes, ears, ins = [], [], []
    for sx in (-1, 1):
        cx = sx * P["fan_cx"]
        holes.append(g.extrude(g.rrect(P["opening"], P["opening"], 8.0, cx, 0.0),
                               P["pocket_z1"], z1 + 0.5))
        for ax in (-1, 1):
            for ay in (-1, 1):
                x, y = cx + ax * P["fan_holes"] / 2, ay * P["fan_holes"] / 2
                ears.append(g.cyl_z(x, y, 5.0, P["pocket_z1"] - 0.1, z1, 24))
                ins.append(g.cyl_z(x, y, 5.5 / 2, P["pocket_z1"] - 0.1, z1 - 0.8, 32))
    body = body - m3.Manifold.batch_boolean(holes, m3.OpType.Add)
    body = body + m3.Manifold.batch_boolean(ears, m3.OpType.Add)

    # ---- deck lip pads for the wall screws -------------------------------
    # The 69 mm opening leaves a 6.3 mm lip; the M3 seat for the wall bracket
    # does not fit there without colliding with the M4 fan boss, so the lip is
    # thickened locally (this tab sits outside the fan blade circle).
    pads = [g.box(sx * 70 - 9, sx * 70 + 9, sy * 29.0, sy * 40.6, P["pocket_z1"] - 0.1, z1)
            for sx in (-1, 1) for sy in (-1, 1)]
    body = body + m3.Manifold.batch_boolean(pads, m3.OpType.Add)

    body = body - m3.Manifold.batch_boolean(ins, m3.OpType.Add)

    # ---- M3 heat-set seats for the wall brackets -------------------------
    # 4.0 mm modelled: a 3.6 mm hole printed as 4.0 on the real part (holes
    # come out ~0.4 smaller), and the insert (OD 4.0) needs 3.6 to bite
    wseats = [g.cyl_z(sx * 70, sy * 36.5, 4.0 / 2, z1 - 6.5, z1 + 0.5, 32)
              for sx in (-1, 1) for sy in (-1, 1)]
    body = body - m3.Manifold.batch_boolean(wseats, m3.OpType.Add)

    # ---- perimeter groove = filter clip rail -----------------------------
    body = body - (g.extrude(outline.buffer(0.15), z0 + 0.5, z0 + 3.5)
                   - g.extrude(outline.buffer(-2.0), z0 + 0.5, z0 + 3.5))

    # ---- side vents feeding the fan pockets ------------------------------
    vents = [g.hex_yz(y, 12.0, 6.0, sx * 87.0, sx * 96.0)
             for sx in (-1, 1) for y in [-33 + 11 * i for i in range(7)]]
    body = body - m3.Manifold.batch_boolean(vents, m3.OpType.Add)

    # ---- bottom cable channels to the rear wing --------------------------
    chans = [g.box(sx * 44 - 4, sx * 44 + 4, 42.0, P["wing_y1"] + 0.5, z0 - 0.5, z0 + 4.0)
             for sx in (-1, 1)]
    body = body - m3.Manifold.batch_boolean(chans, m3.OpType.Add)

    # ---- wing: two through slots for zip ties ---------------------------
    # (the old 2 mm closed grooves held nothing, and the cable runs below)
    slots = [g.box(sx * 44 - 9, sx * 44 + 9, 63.0, 67.0, -1.0, z1 + 0.5)
             for sx in (-1, 1)]
    body = body - m3.Manifold.batch_boolean(slots, m3.OpType.Add)

    # ---- front name plate -----------------------------------------------
    body = body + text_front("FICSIT", 17.0, 1.6, -P["base_y"] / 2 + 0.02, 15.6, bevel=0.45)

    # ---- hazard stripes (engraved into the front face) -------------------
    for band in (sbox(-87.0, 7.2, -51.0, 20.0), sbox(51.0, 7.2, 87.0, 20.0)):
        st = hazard_band(band, pitch=9.0, width=3.4)
        if not st.is_empty:
            cut = (g.extrude(st, 0.0, 2.3)
                   .rotate([90, 0, 0])
                   .translate([0, -P["base_y"] / 2 + 1.3, 0]))
            body = body - cut

    return body


# --------------------------------------------------------------------------- #
#  02/03 TOWER WALL  (built at y=+40, front wall = mirror in Y)
# --------------------------------------------------------------------------- #


def build_wall():
    yi = P["wall_y"]
    yo = P["wall_y"] + P["wall_t"]
    z0, z1 = Z_DECK, Z_TOP
    L, H = P["wall_l"], P["wall_h"]
    zc = z0 + H / 2

    plate = g.extrude(g.chamfer_rect(L, H, 3.5, 0, 0), 0, P["wall_t"], scale_top=0.984)
    plate = plate.rotate([90, 0, 0]).translate([0, yo, zc])

    # ---- raised inner frame (adds stiffness, invisible from outside) -----
    frame = g.rrect(L - 20, H - 20, 6.0) - g.rrect(L - 34, H - 34, 4.0)
    plate = plate + g.extrude(frame, 0, 2.4).rotate([90, 0, 0]).translate([0, yi, zc])

    # ---- framed panel groove on the outer face ---------------------------
    ring = g.rrect(L - 16, H - 16, 5.0) - g.rrect(L - 27, H - 27, 4.0)
    plate = plate - g.extrude(ring, -1.0, 1.3).rotate([90, 0, 0]).translate([0, yo, zc])

    # ---- hex perforation (two panels) ------------------------------------
    # web 3.1 mm = exactly five 0.62 mm passes: the top surface stops being
    # over-filled by gap fill on a 3.3 mm web
    af, web = 9.0, 3.1
    px = af + web
    py = px * math.sqrt(3) / 2
    nx = int((L / 2 - 25) / px)
    ny = int((H / 2 - 20) / py)
    holes = []
    for iy in range(-ny, ny + 1):
        for ix in range(-nx, nx + 1):
            x = ix * px + (px / 2 if iy % 2 else 0.0)
            zz = zc + iy * py
            if abs(x) > L / 2 - 26 or zz < z0 + 20 or zz > z1 - 20:
                continue
            if abs(zz - (z0 + H / 2)) < 9.5:      # solid mid band
                continue
            holes.append(g.hex_xz(x, zz, af, yi - 1, yo + 0.2))
    plate = plate - m3.Manifold.batch_boolean(holes, m3.OpType.Add)

    # ---- brick feet: solid blocks that stand on the base deck ------------
    # (the old 4 mm cantilever shelf printed as a 28 mm thin tower and warped)
    feet = []
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 64, sx * 86))
        feet.append(g.box(x0, x1, 12.0, yi, z0, Z_SEAT))
    plate = plate + m3.Manifold.batch_boolean(feet, m3.OpType.Add)

    # brick locator groove in the foot top
    gro = []
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 64, sx * 86))
        gro.append(g.box(x0 - 0.5, x1 + 0.5, -18.2, 18.2, Z_SEAT - 2.0, Z_SEAT + 0.5))
    plate = plate - m3.Manifold.batch_boolean(gro, m3.OpType.Add)

    # ---- M3 clearance, through the foot, with a printable teardrop -------
    # the hole runs horizontally while printing, so its top is a bridge:
    # a 45-degree relief roof above it keeps the tunnel from sagging
    scr = []
    for sx in (-1, 1):
        scr.append(g.cyl_z(sx * 70, 36.5, 3.6 / 2, z0 - 0.5, Z_SEAT + 0.5, 32))
        scr.append(g.teardrop_z(sx * 70, 36.5, 1.8, z0 - 0.5, Z_SEAT + 0.5, up=-1))
    plate = plate - m3.Manifold.batch_boolean(scr, m3.OpType.Add)

    # ---- top rail + roof screw pads -------------------------------------
    # 8 mm rail: the M3 hole keeps >=2.3 mm of material on both sides
    plate = plate + g.box(-72, 72, yi - 8.0, yo, z1 - 8.0, z1)
    th = []
    for sx in (-1, 1):
        th.append(g.cyl_z(sx * 60, yi - 3.5, 2.0, z1 - 8.2, z1 + 1, 32))
        th.append(g.teardrop_z(sx * 60, yi - 3.5, 2.0, z1 - 8.2, z1 + 1, up=-1))
    plate = plate - m3.Manifold.batch_boolean(th, m3.OpType.Add)

    # ---- engraved hex "bolt heads" on the outer face ---------------------
    hexes = []
    for x in (-82, 82):
        for zz in (33.0, 129.0):
            hexes.append(g.hex_xz(x, zz, 11.0, yo - 0.1, yo + 0.9))
    plate = plate - m3.Manifold.batch_boolean(hexes, m3.OpType.Add)

    return plate


# --------------------------------------------------------------------------- #
#  04 ROOF
# --------------------------------------------------------------------------- #


def build_roof():
    z0 = Z_TOP
    top = z0 + P["roof_t"]
    plate = g.slab(g.rrect(176.0, 96.0, 6.0), top, top + 5.0, chamfer=1.2)
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 33.0, sy * 40.0))
        plate = plate + g.box(-72, 72, y0, y1, z0, z0 + P["roof_t"])
    plate = plate - g.extrude(g.rrect(70.0, 22.0, 11.0), z0 - 1, top + 20)
    sc = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            sc.append(g.cyl_z(sx * 60, sy * 36.5, 3.6 / 2, z0 - 1, top + 16, 32))
            sc.append(g.cyl_z(sx * 60, sy * 36.5, 3.3, top + 2.0, top + 6.2, 32, r_top=3.3))
    plate = plate - m3.Manifold.batch_boolean(sc, m3.OpType.Add)
    # engraved name plate (roof is printed top-face down, so engraving is safe)
    tf = top + 5.0
    plate = plate - text_top("FICSIT", 20.0, 0.9, tf - 0.9, -30.0, 0.0)
    plate = plate - text_top("COOLING UNIT 2x80", 6.5, 0.7, tf - 0.7, 30.0, 0.0)
    return plate


# --------------------------------------------------------------------------- #
#  05 FILTER TRAY
# --------------------------------------------------------------------------- #


def build_filter():
    W, D = 196.0, 116.0
    h = 4.0
    tray = g.extrude(g.rrect(W, D, 8.0), 0.0, h)
    for sx in (-1, 1):
        tray = tray - g.extrude(g.rrect(70, 70, 6.0, sx * P["fan_cx"], 0.0), -1, h + 1)
        tray = tray - g.extrude(g.rrect(80, 80, 6.0, sx * P["fan_cx"], 0.0), h - 1.2, h + 1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tray = tray - g.box(sx * 84 - 9, sx * 84 + 9, sy * 46 - 9, sy * 46 + 9, -1, h + 1)

    clips, teeth = [], []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = sx * (W / 2 - 1.0)
            yy = sy * 40.0
            clips.append(g.box(x - 1.1, x + 1.1, yy - 6, yy + 6, h - 0.1, h + 8.0))
            t0, t1 = sorted((x - 3.2 * sx, x - 0.4 * sx))
            teeth.append(g.box(t0, t1, yy - 5, yy + 5, h + 0.4, h + 2.6))
    tray = tray + m3.Manifold.batch_boolean(clips, m3.OpType.Add)
    tray = tray + m3.Manifold.batch_boolean(teeth, m3.OpType.Add)
    return tray.translate([0, 0, 2.0])


# --------------------------------------------------------------------------- #
#  assembly / print orientation
# --------------------------------------------------------------------------- #


def clean(m):
    """Drop zero-volume sliver shells left behind by chamfer booleans."""
    parts = [p for p in m.decompose() if p.volume() > 0.5]
    if not parts:
        return m
    return parts[0] if len(parts) == 1 else m3.Manifold.batch_boolean(parts, m3.OpType.Add)


def build_all():
    rear = build_wall()
    raw = {
        "01_base": build_base(),
        "02_wall_front": rear.mirror([0, 1, 0]),
        "03_wall_rear": rear,
        "04_roof": build_roof(),
        "05_filter_tray": build_filter(),
    }
    return {k: clean(v) for k, v in raw.items()}


def to_print(name, m):
    # NB: a flip must be a *rotation*. `mirror([0,0,1])` reflects the part and
    # silently turns every asymmetric feature (lettering, dock side) into a
    # mirror image вЂ” that is what printed the FICSIT logo backwards.
    if name == "01_base":
        r, note = m.rotate([180, 0, 0]), "deck down (rotate 180 about X)"
    elif name == "02_wall_front":
        r, note = m.rotate([90, 0, 0]), "outer face down, features up"
    elif name == "03_wall_rear":
        r, note = m.rotate([-90, 0, 0]), "outer face down, features up"
    elif name == "04_roof":
        r, note = m.rotate([180, 0, 0]), "top face down (rotate 180 about X)"
    else:
        r, note = m, "as modelled"
    # centre on the plate (x/y) and drop it onto the bed (z = 0)
    bb = r.bounding_box()
    return r.translate([-0.5 * (bb[0] + bb[3]), -0.5 * (bb[1] + bb[4]), -bb[2]]), note


if __name__ == "__main__":
    for name, m in build_all().items():
        bb = m.bounding_box()
        print(f"{name:16s} vol={m.volume()/1000:7.1f} cm3  "
              f"{bb[3]-bb[0]:6.1f} x {bb[4]-bb[1]:6.1f} x {bb[5]-bb[2]:6.1f}  genus={m.genus()}")

