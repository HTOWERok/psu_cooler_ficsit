import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import geom as g
from shapely.geometry import Polygon

# 1) extrusion with a hole
outer = g.rrect(40, 30, 5)
inner = g.rrect(20, 10, 3)
p = outer.difference(inner)
m = g.extrude(p, 0, 10)
print("plate 40x30 r5 minus 20x10 r3, h10")
print("  volume", round(m.volume(), 2), "(approx 1157 expected incl. corner rounding)")

# 2) text
t = g.text_poly("FICSIT", 12)
print("text bounds", [round(v, 2) for v in t.bounds], "area", round(t.area, 1))
ts = g.text_solid("FICSIT", 12, 1.5)
print("text solid volume", round(ts.volume(), 2), "bbox", ts.bounding_box())

# 3) hex
h = g.hex_prism_z(0, 0, 8, 0, 3)
print("hex 8AF x3 volume", round(h.volume(), 2), "expected", round(3 * 8 * 8 / (2 * 3**0.5) * 3, 2))

# 4) slab with chamfers
s = g.slab(g.rrect(60, 40, 4), 0, 10, chamfer=1.5, bottom_chamfer=1.0)
print("slab volume", round(s.volume(), 1), "genus", s.genus(), "bb", s.bounding_box())
print("is manifold-ish: genus>=0", s.genus())
