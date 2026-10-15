"""A clawfoot bathtub for the Moomin House, wide enough for Moomintroll to sit in, printed upright with no supports.

The sides flare outward as they rise and the rim rolls out over a 45° lip, so no surface leans out more than 45°.
Underneath, the tub narrows at 45° to an oval plinth, and four cone feet stand on the bed at its corners. The
inside is one smooth shell with a curved floor and a plug hole. It has no taps on purpose: a thin tap could snap
off and become a part small enough to swallow.
"""
import math
from build123d import Cone, Cylinder, Plane, Pos, SlotOverall, extrude, fillet, loft

TITLE='Bathtub'
NOTES='Print upright, as shown, with no supports: the standard Ender 3 PLA profile (0.2 mm layers, 20 % infill) is fine.'
COLOR='cream'
PARAMS={
    'length':(76,60,110,1),        # outside, over the rim
    'width':(44,36,60,1),
    'height':(30,22,45,.5),
    'wall':(2,1.2,3,.1),
    'flare':(10,0,30,1,'°'),       # how far the sides lean out from vertical
    'lift':(6,3,10,.5),            # the underside's height above the bed
    'lip':(1.2,0,2,.1),            # how far the rolled rim sticks out
    'round':(.8,0,1.2,.1),         # rim rounding
    'curve':(4,0,6,.5),            # radius where the inside floor meets the sides
}

def stadium(length,width,z):
    """A bathtub plan at height z: a rectangle with semicircular ends."""
    return Plane.XY.offset(z)*SlotOverall(length,width)

def build(length,width,height,wall,flare,lift,lip,round,curve):
    lean=math.tan(math.radians(flare));band=1.5   # the rim's upright band above its 45° lip
    top=height-band-lip                           # where the flaring side meets the lip
    L,W=length-2*lip,width-2*lip                  # the side's size at `top`
    def side(z,inset=0):                          # the flaring side's outline at height z, moved in by `inset`
        grow=2*(z-top)*lean;return stadium(L+grow-2*inset,W+grow-2*inset,z)
    bottom=(L-2*(top-lift)*lean,W-2*(top-lift)*lean)   # the side's size at the underside
    under=lift-1                                  # the 45° underside rises this much, so it steps in as much
    plinth=(bottom[0]-2*under,bottom[1]-2*under)
    if plinth[1]<8:raise ValueError(f'The tub is {bottom[1]:.1f} mm wide at the bottom, too narrow for a {lift:g} mm lift on a 45° '
                                    'underside: lower the lift or the flare, or make the tub wider.')
    floor=lift+wall
    if floor+curve+4>top:raise ValueError('The tub is too shallow for its floor, lift and curve: make it taller.')

    tub=loft([side(lift),side(top)],ruled=True)                                   # the flaring sides
    if lip>0:tub+=loft([side(top),stadium(length,width,top+lip)],ruled=True)       # the 45° lip
    tub+=extrude(stadium(length,width,top+lip),band)                              # the rim band
    tub+=loft([stadium(*plinth,1),side(lift)],ruled=True)                         # the 45° underside
    tub+=extrude(stadium(*plinth,0),1)                                            # the plinth on the bed
    for sx in (-1,1):                     # cone feet where the straight sides meet the round ends
        for sy in (-1,1):tub+=Pos(sx*(bottom[0]-bottom[1])/2,sy*(bottom[1]/2-2.4),0)*Cone(3.4,2.2,lift+1,align=None)
    tub-=loft([side(floor,inset=wall),side(height+1,inset=wall)],ruled=True)     # the inside, flaring with the sides
    if round>0:tub=fillet([e for e in tub.edges() if abs(e.center().Z-height)<1e-6],round)
    if curve>0:tub=fillet([e for e in tub.edges() if abs(e.center().Z-floor)<1e-6],curve)
    inside=L-2*(top-floor)*lean-2*wall            # the inside length at the floor
    return tub-Pos(-inside/2+curve+3,0,floor-.6)*Cylinder(2.2,1.2,align=None)    # a shallow plug hole at the foot end
