"""A classic hanging chandelier for the Moomin House, printed upright with no supports.

Features a drop finial base on the printer bed, a flared 45° gallery bowl, four candle holders
with tapered candles and flame finials, a central stem, and a self-supporting top suspension loop.
All overhangs are 45° or steeper, allowing clean printing without supports.
"""
import math
from build123d import Align, Axis, Cylinder, Location, Plane, Polygon, Pos, extrude, revolve

TITLE = 'Chandelier'
NOTES = 'Print upright, as shown, with no supports: the standard Ender 3 PLA profile (0.2 mm layers, 20 % infill) is fine.'
COLOR = 'ochre'
PARAMS = {
    'diameter': (46, 36, 60, 1),        # outer diameter of the candle gallery ring
    'height': (54, 40, 70, 1),          # total height from base to top loop
    'base_diameter': (15, 12, 22, 1),   # drop finial base diameter
    'candle_height': (10, 6, 16, 1),    # height of candle shafts
    'stem': (9, 6, 14, .5),             # central column diameter
}

def build(diameter, height, base_diameter, candle_height, stem):
    r_base = base_diameter / 2
    r_ring = diameter / 2
    h_flair = r_ring - r_base
    h_rim = 3.5
    r_stem = stem / 2

    # Central body: revolve profile in XZ
    pts = [
        (0, 0),
        (r_base, 0),
        (r_base, 2),
        (r_ring, 2 + h_flair),
        (r_ring, 2 + h_flair + h_rim),
        (r_ring - 5.5, 2 + h_flair + h_rim),
        (r_stem, 2 + h_flair + h_rim - (r_ring - 5.5 - r_stem)),
        (r_stem, height - 10),
        (0, height - 10),
    ]
    body = revolve(Plane.XZ * Polygon(*pts, align=None), Axis.Z)

    # Top loop: self-supporting pointed diamond hole
    outer_loop = Polygon(
        (0, height - 14),
        (-r_stem - 1.5, height - 6),
        (0, height),
        (r_stem + 1.5, height - 6),
        align=None,
    )
    inner_hole = Polygon(
        (0, height - 8.5),
        (-2.0, height - 5.5),
        (0, height - 2.5),
        (2.0, height - 5.5),
        align=None,
    )
    loop = extrude(Plane.XZ * (outer_loop - inner_hole), r_stem * 0.7, both=True)
    chand = body + loop

    # Four candles on the ring
    r_candle_pos = r_ring - 2.8
    z_start = 2 + h_flair + h_rim
    for angle in (0, 90, 180, 270):
        rad = math.radians(angle)
        cx, cy = r_candle_pos * math.cos(rad), r_candle_pos * math.sin(rad)
        socket = Pos(cx, cy, z_start) * Cylinder(2.5, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        shaft = Pos(cx, cy, z_start + 3.0) * Cylinder(1.8, candle_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        flame_pts = [
            (0, 0),
            (1.8, 0),
            (1.8, 1.5),
            (1.2, 3.0),
            (0, 4.0),
        ]
        flame = Pos(cx, cy, z_start + 3.0 + candle_height) * revolve(Plane.XZ * Polygon(*flame_pts, align=None), Axis.Z)
        chand += socket + shaft + flame

    box = chand.bounding_box()
    return chand.moved(Location((-(box.min.X + box.max.X) / 2, -(box.min.Y + box.max.Y) / 2, -box.min.Z)))
