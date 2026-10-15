// Movement conventions shared by both model views (CAD coordinates, millimetres).
export function hingeRadians(degrees,sign=1){return sign*degrees*Math.PI/180;}
export function drawerOffset(direction,travel){return [direction[0]*travel,direction[1]*travel,0];}
