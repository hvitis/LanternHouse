"""A chair for the Moomin House, sized for Moomintroll, that prints upright with no supports.

The four legs are what is left of a solid block after two pointed tunnels are cut through it, front to back and
side to side. Their roofs lean 45°, the most an FDM printer prints without support, so the seat needs none. The
back is a slab with an arched top. The outer corners, the seat and the back are rounded; the bottom edges stay
sharp, because a rounded bottom edge would overhang.
"""
from build123d import Axis, Box, Ellipse, Plane, Polygon, Pos, Rectangle, Rotation, extrude, fillet

TITLE='Chair'
NOTES='Print upright, as shown. PLA, 0.2 mm layers, 3 walls, 15 % infill, no supports.'
COLOR='wood'
PARAMS={
    'width':(34,32,50,.5),
    'depth':(32,32,45,.5),
    'seat_height':(17,12,30,.5),
    'seat':(3,1.5,6,.25),           # seat thickness above the tunnel roofs
    'leg':(5,3,10,.25),
    'back_height':(30,15,50,.5),    # above the seat
    'back':(3.5,2,6,.25),
    'round':(1,0,1.5,.25),
}

def tunnel(span,spring,length):
    """A doorway-shaped prism along Y: straight sides `spring` high under a 45° pointed roof."""
    outline=Polygon((-span/2,-1),(span/2,-1),(span/2,spring),(0,spring+span/2),(-span/2,spring),align=None)
    return extrude(Plane.XZ*outline,length/2+1,both=True)

def build(width,depth,seat_height,seat,leg,back_height,back,round):
    spans={'front to back':width-2*leg,'side to side':depth-2*leg}
    springs={k:seat_height-seat-s/2 for k,s in spans.items()}
    for k,spring in springs.items():
        if spring<0:raise ValueError(f'The {k} arch is {spans[k]:g} mm wide, so its 45° roof needs the seat at least '
                                     f'{seat_height-spring:g} mm high: raise seat_height, thin the seat or widen the legs.')
    chair=Pos(0,0,seat_height/2)*Box(width,depth,seat_height)
    chair-=tunnel(spans['front to back'],springs['front to back'],depth)
    chair-=Rotation(0,0,90)*tunnel(spans['side to side'],springs['side to side'],width)
    # The back: a slab across the rear edge with an elliptical arch on top.
    arch=min(width/2,back_height/2);straight=back_height-arch
    outline=Pos(0,seat_height+straight/2)*Rectangle(width,straight)+Pos(0,seat_height+straight)*Ellipse(width/2,arch)
    chair+=extrude(Plane.XZ.offset(-depth/2)*outline,back)
    if round>0:
        top=seat_height-1e-6
        upper=[e for e in chair.edges() if min(v.Z for v in e.vertices())>top]   # the seat top and everything above it
        corners=chair.edges().filter_by(Axis.Z).filter_by(lambda e:abs(abs(e.center().X)-width/2)<1e-6 and abs(abs(e.center().Y)-depth/2)<1e-6)
        chair=fillet(corners+upper,round)
    return chair
