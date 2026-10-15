"""A round table for the Moomin House on one flared pedestal, printed upright with no supports.

The column widens into the table top in a 45° cone, the most an FDM printer prints without support, so the
underside of the top needs none. The top's upper edge and the foot are rounded.
"""
from build123d import Axis, Plane, Polygon, fillet, revolve

TITLE='Round table'
NOTES='Print upright, as shown. PLA, 0.2 mm layers, 3 walls, 15 % infill, no supports.'
COLOR='cream'
PARAMS={
    'diameter':(52,40,90,1),
    'height':(30,20,50,.5),
    'top':(3,2,6,.25),          # thickness of the rim
    'column':(10,6,20,.5),      # column diameter
    'foot':(34,20,60,1),        # foot diameter
    'foot_height':(3,2,8,.25),
    'round':(1,0,1.5,.25),
}

def build(diameter,height,top,column,foot,foot_height,round):
    R,r,f=diameter/2,column/2,foot/2
    cone=R-r;start=height-top-cone   # where the column starts to flare
    if start<foot_height:raise ValueError(f'A {diameter:g} mm top on a {column:g} mm column needs a {cone:g} mm high 45° flare: '
                                          f'make the table at least {foot_height+cone+top:g} mm high, the top smaller or the column wider.')
    # Half the outline in (radius, height), turned about the vertical axis.
    outline=Polygon((0,0),(f,0),(f,foot_height),(r,foot_height),(r,start),(R,start+cone),(R,height),(0,height),align=None)
    table=revolve(Plane.XZ*outline,Axis.Z)
    if round>0:
        rims=[e for e in table.edges() if e.geom_type.name=='CIRCLE' and (abs(e.center().Z-height)<1e-6 or abs(e.center().Z-foot_height)<1e-6) and e.radius>r+1e-6]
        table=fillet(rims,round)
    return table
