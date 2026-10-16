"""A traditional Nordic tiled stove (kakelugn) for Lanternwood House, printed upright with no supports.

The kakelugn features a sturdy round plinth on the printer bed, an arched firebox door with raised
moulding on the lower drum, a flared waist shelf, an upper cylindrical tiled column, and an ornate
flared crown cornice. All transitions and overhangs are 45° or steeper, so it prints cleanly without
any support structures.
"""
from build123d import Align, Axis, Box, Location, Plane, Polygon, Pos, revolve

TITLE = 'Tiled stove'
NOTES = 'Print upright, as shown, with no supports: the standard Ender 3 PLA profile (0.2 mm layers, 20 % infill) is fine.'
COLOR = 'cream'
PARAMS = {
    'diameter': (40, 32, 50, 1),        # plinth diameter
    'height': (95, 75, 115, 1),         # total height to flue top
    'plinth_height': (6, 4, 10, .5),    # height of the base plinth
    'shelf_height': (40, 30, 55, 1),    # height of the waist moulding
    'crown_diameter': (39, 32, 48, 1),  # crown cornice outer diameter
    'door_width': (14, 10, 20, 1),      # firebox door width
    'door_height': (16, 12, 24, 1),     # firebox door height
}

def build(diameter, height, plinth_height, shelf_height, crown_diameter, door_width, door_height):
    r_base = diameter / 2
    r_lower = r_base - 2.0
    r_shelf = r_lower + 1.5
    h_shelf = 2.0
    r_upper = r_lower - 2.0
    z_mid = shelf_height
    z_crown = height - 13.0
    r_crown = crown_diameter / 2
    h_crown = 2.5
    z_top = height - 5.0
    r_flue = 7.0

    dz1 = r_base - r_lower
    dz_shelf = r_shelf - r_lower
    dz_in = r_shelf - r_upper
    dz_crown = r_crown - r_upper

    pts = [
        (0, 0),
        (r_base, 0),
        (r_base, plinth_height),
        (r_lower, plinth_height + dz1),
        (r_lower, z_mid),
        (r_shelf, z_mid + dz_shelf),
        (r_shelf, z_mid + dz_shelf + h_shelf),
        (r_upper, z_mid + dz_shelf + h_shelf + dz_in),
        (r_upper, z_crown),
        (r_crown, z_crown + dz_crown),
        (r_crown, z_crown + dz_crown + h_crown),
        (r_upper, z_crown + dz_crown + h_crown + dz_crown),
        (r_flue, z_top),
        (r_flue, height),
        (0, height),
    ]

    body = revolve(Plane.XZ * Polygon(*pts, align=None), Axis.Z)

    # Arched firebox door in front (-Y):
    # Cross-section in YZ plane with 45° bottom chamfer so it needs no support
    z_door_base = plinth_height + dz1 + 2.5
    z_door_top = z_door_base + door_height
    door_yz = Polygon(
        (-r_lower + 1.0, z_door_base - 1.5),
        (-r_lower - 1.5, z_door_base + 1.0),
        (-r_lower - 1.5, z_door_top),
        (-r_lower + 1.0, z_door_top),
        align=None,
    )
    door = revolve(Plane.XZ * Polygon([(-door_width/2, z_door_base), (door_width/2, z_door_base), (0, z_door_top)], align=None), Axis.Z) if False else None

    # Extrude door profile along X with 45° arched top
    from build123d import extrude
    door = extrude(Plane.YZ * door_yz, door_width / 2, both=True)
    # Cut top arch at 45° roof
    roof_poly = Polygon(
        (-door_width / 2, z_door_top),
        (0, z_door_top + 4.0),
        (door_width / 2, z_door_top),
        (door_width / 2 + 5, z_door_top),
        (door_width / 2 + 5, z_door_top + 10),
        (-door_width / 2 - 5, z_door_top + 10),
        (-door_width / 2 - 5, z_door_top),
        align=None,
    )
    roof_cut = extrude(Plane.XZ * roof_poly, 25, both=True)
    door -= roof_cut

    stove = body + door
    box = stove.bounding_box()
    return stove.moved(Location((-(box.min.X + box.max.X) / 2, -(box.min.Y + box.max.Y) / 2, -box.min.Z)))
