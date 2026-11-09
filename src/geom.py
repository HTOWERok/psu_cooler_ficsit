"""
geom.py — parametric geometry toolkit on top of manifold3d + shapely.

Units: millimetres, Z up, model sits on z=0.

Conventions
-----------
* 2D profiles are shapely Polygons (may contain holes).
* `extrude` normalises ring winding so manifold3d resolves holes.
* One ring = one closed loop, no repeated last point.
"""
from __future__ import annotations

import os

import manifold3d as m3
import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union

# --------------------------------------------------------------------------- #
#  solids
# --------------------------------------------------------------------------- #


def box(x0, x1, y0, y1, z0, z1):
    """Axis aligned box; argument order does not matter."""
    x0, x1 = (x0, x1) if x0 <= x1 else (x1, x0)
    y0, y1 = (y0, y1) if y0 <= y1 else (y1, y0)
    z0, z1 = (z0, z1) if z0 <= z1 else (z1, z0)
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cbox(cx, cy, cz, sx, sy, sz):
    return m3.Manifold.cube([sx, sy, sz], True).translate([cx, cy, cz])


def cyl_z(cx, cy, r, z0, z1, seg=96, r_top=None):
    return m3.Manifold.cylinder(z1 - z0, r, r if r_top is None else r_top, seg).translate([cx, cy, z0])


def cyl_y(cx, cz, r, y0, y1, seg=96):
    """Cylinder whose axis runs along +Y, from y0 to y1."""
    return m3.Manifold.cylinder(y1 - y0, r, r, seg).rotate([-90, 0, 0]).translate([cx, y0, cz])


def cyl_x(cx_y, cx_z, r, x0, x1, seg=96):
    """Cylinder whose axis runs along +X, from x0 to x1."""
    return m3.Manifold.cylinder(x1 - x0, r, r, seg).rotate([0, 90, 0]).translate([x0, cx_y, cx_z])


def poly_prism_z(pts, z0, z1):
    return m3.Manifold.extrude(m3.CrossSection([np.asarray(pts, float)]), z1 - z0).translate([0, 0, z0])


def prism_xz(pts_xz, y0, y1):
    """Prism whose 2D profile lives in the XZ plane, extruded along Y."""
    y0, y1 = (y0, y1) if y0 <= y1 else (y1, y0)
    cs = m3.CrossSection([np.asarray(pts_xz, float)])
    return m3.Manifold.extrude(cs, y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def prism_yz(pts_yz, x0, x1):
    """Prism whose 2D profile lives in the YZ plane, extruded along X.

    (u, v) -> (y, z) exactly, extrusion runs from x0 to x1.
    """
    x0, x1 = (x0, x1) if x0 <= x1 else (x1, x0)
    cs = m3.CrossSection([np.asarray(pts_yz, float)])
    return (m3.Manifold.extrude(cs, x1 - x0)
            .rotate([0, 90, 0]).rotate([90, 0, 0]).translate([x0, 0, 0]))


def _hex_pts(cx, cz, af, rot=0.0):
    r = af / np.sqrt(3.0)
    return [
        (cx + r * np.cos(np.pi / 3 * i + np.pi / 6 + rot),
         cz + r * np.sin(np.pi / 3 * i + np.pi / 6 + rot))
        for i in range(6)
    ]


def hex_hole_xz(cx, cz, af, y_in, y_out, chamfer=0.7, flare=1.1):
    """Through hole in a wall whose outer face is at y_out, with an outer chamfer.

    The chamfer flares the hole open towards +Y (the visible face).
    """
    out = hex_xz(cx, cz, af, y_in, y_out)
    if chamfer > 0:
        base = af - 0.4          # slightly smaller than the bore: no coincident faces
        pts = _hex_pts(0.0, 0.0, base)
        cs = m3.CrossSection([np.asarray(pts, float)])
        k = (af + 2.0 * flare) / base
        fr = (m3.Manifold.extrude(cs, chamfer, 0, 0.0, (k, k))
              .rotate([-90, 0, 0]).translate([cx, y_out - chamfer, cz]))
        out = out + fr
    return out


def bevel_extrude(poly, z0, z1, bevel=0.35):
    """Prism with a 45-degree bevel on the top edge (keeps the footprint exact)."""
    h = z1 - z0
    if bevel <= 0 or bevel >= h:
        return extrude(poly, z0, z1)
    body = extrude(poly, z0, z1 - bevel)
    top = extrude(poly.buffer(-bevel, join_style=2, quad_segs=6), z1 - bevel, z1)
    return body + top


def hex_xz(cx, cz, across_flats, y0, y1, rot=0.0):
    r = across_flats / np.sqrt(3.0)
    pts = [
        (cx + r * np.cos(np.pi / 3 * i + np.pi / 6 + rot), cz + r * np.sin(np.pi / 3 * i + np.pi / 6 + rot))
        for i in range(6)
    ]
    return prism_xz(pts, y0, y1)


def teardrop_z(cx, cy, r, z0, z1, up=-1, n=24):
    """Cylinder with a 45-degree relief roof (a 'teardrop').

    A horizontal hole prints with an unsupported bridge on top; adding a 45
    degree peak in the `up` direction turns that bridge into two slopes.
    """
    ang = np.radians(np.linspace(-45.0, 225.0, n)) if up < 0 else np.radians(np.linspace(135.0, 405.0, n))
    pts = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in ang]
    pts.append((cx, cy + up * np.sqrt(2.0) * r))
    return poly_prism_z(pts, z0, z1)


def hex_yz(cy, cz, across_flats, x0, x1, rot=0.0):
    """Hex prism whose axis runs along X (profile in the YZ plane)."""
    x0, x1 = (x0, x1) if x0 <= x1 else (x1, x0)
    r = across_flats / np.sqrt(3.0)
    pts = [
        (cy + r * np.cos(np.pi / 3 * i + np.pi / 6 + rot), cz + r * np.sin(np.pi / 3 * i + np.pi / 6 + rot))
        for i in range(6)
    ]
    return m3.Manifold.extrude(m3.CrossSection([np.asarray(pts, float)]), x1 - x0).rotate(
        [0, 90, 0]
    ).translate([x1, 0, 0])


def hex_prism_z(cx, cy, across_flats, z0, z1, rot=0.0):
    r = across_flats / np.sqrt(3.0)
    pts = [
        (cx + r * np.cos(np.pi / 3 * i + np.pi / 6 + rot), cy + r * np.sin(np.pi / 3 * i + np.pi / 6 + rot))
        for i in range(6)
    ]
    return poly_prism_z(pts, z0, z1)


# --------------------------------------------------------------------------- #
#  2D profiles
# --------------------------------------------------------------------------- #


def rrect(w, d, r=0.0, cx=0.0, cy=0.0):
    """Rounded rectangle centred on (cx, cy)."""
    if r <= 0:
        g = sbox(cx - w / 2.0, cy - d / 2.0, cx + w / 2.0, cy + d / 2.0)
    else:
        r = min(r, w / 2.0 - 0.01, d / 2.0 - 0.01)
        g = sbox(-w / 2.0, -d / 2.0, w / 2.0, d / 2.0).buffer(
            -r, join_style=1, quad_segs=8
        ).buffer(r, join_style=1, quad_segs=8)
        g = affinity.translate(g, cx, cy)
    return Polygon(g.exterior.coords)


def chamfer_rect(w, d, c, cx=0.0, cy=0.0):
    """Rectangle with 45-degree corner chamfers (c = chamfer leg)."""
    x, y = w / 2.0, d / 2.0
    pts = [
        (cx - x + c, cy - y), (cx + x - c, cy - y), (cx + x, cy - y + c),
        (cx + x, cy + y - c), (cx + x - c, cy + y), (cx - x + c, cy + y),
        (cx - x, cy + y - c), (cx - x, cy - y + c),
    ]
    return Polygon(pts)


def poly_extent(poly):
    minx, miny, maxx, maxy = poly.bounds
    return maxx - minx, maxy - miny


# --------------------------------------------------------------------------- #
#  extrusion
# --------------------------------------------------------------------------- #


def _ring(coords, ccw=True):
    pts = np.asarray(coords, dtype=np.float64)
    if np.allclose(pts[0], pts[-1]):
        pts = pts[:-1]
    area = 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
    if (area > 0) != ccw:
        pts = pts[::-1].copy()
    return pts


def _profiles(poly):
    """All contours of a (multi)polygon with outer CCW / holes CW."""
    rings = []
    geoms = list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]
    for g in geoms:
        if g.is_empty:
            continue
        rings.append(_ring(g.exterior.coords, ccw=True))
        for hole in g.interiors:
            rings.append(_ring(hole.coords, ccw=False))
    return rings


def extrude(poly, z0, z1, scale_top=1.0):
    cs = m3.CrossSection(_profiles(poly))
    if scale_top != 1.0:
        return m3.Manifold.extrude(cs, z1 - z0, 0, 0.0, (scale_top, scale_top)).translate([0, 0, z0])
    return m3.Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])


def slab(poly, z0, z1, chamfer=1.2, bottom_chamfer=0.0):
    """Prism with a chamfered top edge (and optionally a chamfered bottom edge)."""
    if chamfer <= 0 and bottom_chamfer <= 0:
        return extrude(poly, z0, z1)

    w, d = poly_extent(poly)
    cx, cy = poly.centroid.x, poly.centroid.y
    local = affinity.translate(poly, -cx, -cy)

    def sx(v):
        return 1.0 - 2.0 * v / max(w, 1e-6)

    def sy(v):
        return 1.0 - 2.0 * v / max(d, 1e-6)

    parts = []
    z = z0
    if bottom_chamfer > 0:
        inner = local.buffer(-bottom_chamfer, join_style=2, quad_segs=8)
        kx = w / max(w - 2.0 * bottom_chamfer, 1e-6)
        ky = d / max(d - 2.0 * bottom_chamfer, 1e-6)
        seg = m3.Manifold.extrude(
            m3.CrossSection(_profiles(inner)), bottom_chamfer, 0, 0.0, (kx, ky)
        )
        parts.append(seg.translate([0, 0, z0]))
        z = z0 + bottom_chamfer
    body_top = z1 - chamfer
    if body_top > z:
        parts.append(extrude(local, z, body_top))
        z = body_top
    if chamfer > 0:
        crown = m3.Manifold.extrude(
            m3.CrossSection(_profiles(local)), z1 - z, 0, 0.0, (sx(chamfer), sy(chamfer))
        )
        parts.append(crown.translate([0, 0, z]))
    out = parts[0]
    for p in parts[1:]:
        out = out + p
    return out.translate([cx, cy, 0])


def shell_ring(poly, z0, z1, thickness):
    inner = poly.buffer(-thickness, join_style=2, quad_segs=6)
    return extrude(poly, z0, z1) - extrude(inner, z0 - 1, z1 + 1)


# --------------------------------------------------------------------------- #
#  text
# --------------------------------------------------------------------------- #

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\bahnschrift.ttf",
    r"C:\Windows\Fonts\seguisb.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
]


def font_path(prefer=None):
    for p in ([prefer] if prefer else []) + FONT_CANDIDATES:
        if p and os.path.exists(p):
            return p
    raise FileNotFoundError("no usable TTF font")


def text_poly(text, size, font=None):
    """Outline of `text` as a shapely polygon, baseline on y=0, starts at x=0."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath

    prop = FontProperties(fname=font or font_path())
    tp = TextPath((0, 0), text, size=size, prop=prop, usetex=False)
    raw = [Polygon(p).buffer(0) for p in tp.to_polygons() if len(p) >= 3]
    raw = [p for p in raw if not p.is_empty and p.area > 0.01]
    polys, holes = [], []
    for p in raw:
        if any(q.contains(p) for q in raw if q is not p and q.area > p.area):
            holes.append(p)
        else:
            polys.append(p)
    g = unary_union(polys)
    if holes:
        g = g.difference(unary_union(holes))
    return g


def text_solid(text, size, height, font=None, z0=0.0):
    return extrude(text_poly(text, size, font), z0, z0 + height)


# --------------------------------------------------------------------------- #
#  misc
# --------------------------------------------------------------------------- #


def mirror_x(m):
    return m.mirror([1, 0, 0])


def bbox(m):
    return m.bounding_box()


def stats(m):
    return dict(volume=round(m.volume(), 1), genus=m.genus(), bbox=bbox(m))
