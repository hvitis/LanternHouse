"""Nominal A3 machining geometry, split by operation, entry face and depth.

No cutter compensation or machine-specific toolpaths are applied here. Through holes are drilled from the top,
whatever face their screw enters from. Features the supplier is not asked for (config cnc: holes below min_drill,
and blind underside features unless two_sided) are listed for the builder to drill by hand instead.
"""
from collections import defaultdict
from pathlib import Path
import math
from dxf_r12 import DXF


def transform(part,item,x,y):
    a=math.radians(item['angle']);c,s=math.cos(a),math.sin(a)
    points=[(px*c-py*s,px*s+py*c) for px,py in part['outer']]
    return (x*c-y*s-min(px for px,py in points)+item['x'],x*s+y*c-min(py for px,py in points)+item['y'])


def features(data,sheet,retain_edges=True):
    """(operations {name: [(kind, geometry)]}, hand-drilled features [dict]) for one sheet. With retain_edges=False
    every outline is closed, including the factory blank edges a fixed wall keeps on its own A3 blank."""
    cnc=data.get('config',{}).get('cnc',{});two_sided=cnc.get('two_sided',True);min_drill=cnc.get('min_drill',0)
    result=defaultdict(list);hand=[]
    for item in sheet['items']:
        p=data['parts'][item['part']];xy=lambda point:transform(p,item,*point)
        if p.get('outercircle'):
            x,y,r=p['outercircle'];result['cut'].append(('circle',(*xy((x,y)),r)))
        elif p.get('retained_edges') and retain_edges:
            for a,b in zip(p['outer'],p['outer'][1:]+p['outer'][:1]):
                if any(abs(a[0 if edge['axis']=='x' else 1]-edge['value'])<1e-6 and abs(b[0 if edge['axis']=='x' else 1]-edge['value'])<1e-6 for edge in p['retained_edges']):continue
                result['cut'].append(('line',[xy(a),xy(b)]))
        else:result['cut'].append(('polygon',[xy(v) for v in p['outer']]))
        for cut in p['cuts']:result['cut'].append(('polygon',[xy(v) for v in cut]))
        for h in p['holes']:
            depth=min(h.get('depth') or p['thickness'],p['thickness']);through=depth>=p['thickness']
            face='top' if through else h.get('entry','top')
            kind='drill' if through else 'pocket' if 'pocket' in h.get('purpose','').lower() or 'recess' in h.get('purpose','').lower() else 'drill'
            centre=xy((h['x'],h['y']))
            def by_hand(what,d,z,f,why):hand.append({'sheet':sheet['id'],'part':item['part'],'copy':item['copy'],'hole':h['id'],'feature':what,'diameter':d,'depth':z,'face':f,'x':round(centre[0],2),'y':round(centre[1],2),'reason':why,'reason_code':'small' if why.startswith('smaller') else 'underside','purpose':h.get('purpose','')})
            if h['diameter']<min_drill:by_hand(kind,h['diameter'],depth,face,f'smaller than the D{min_drill:g} minimum drill')
            elif face=='bottom' and not two_sided:by_hand(kind,h['diameter'],depth,face,'underside feature; the sheet is not flipped')
            else:result[f'{kind}-{face}-d{h["diameter"]:g}-z{depth:g}'].append(('circle',(*centre,h['diameter']/2)))
            if h.get('countersink'):
                cs_face=h.get('entry','top')
                if cs_face=='bottom' and not two_sided:by_hand('countersink',h['countersink'],h['countersink_depth'],cs_face,'underside feature; the sheet is not flipped')
                else:result[f'countersink-{cs_face}-d{h["countersink"]:g}-z{h["countersink_depth"]:g}'].append(('circle',(*centre,h['countersink']/2)))
    return dict(result),hand


def operations(data,sheet):
    return features(data,sheet)[0]


def is_through(operation,thickness):
    """The profile cut and the holes drilled right through from the top; everything else stops inside the board."""
    return operation=='cut' or operation.startswith('drill-top-') and operation.endswith(f'-z{thickness:g}')


def through_cuts(data,sheet):
    """Every path that goes right through the sheet: closed outlines, openings and through holes. Blind pockets and
    blind holes are left out, because a laser would cut them through."""
    ops=features(data,sheet,retain_edges=False)[0]
    return [curve for name,curves in ops.items() if is_through(name,sheet['thickness']) for curve in curves]


def draw(c,curves,scale,ox=0,oy=0):
    c.setStrokeColorRGB(0,0,0);c.setLineWidth(.01*scale)
    for kind,curve in curves:
        if kind=='circle':
            x,y,r=curve;c.circle(ox+x*scale,oy+y*scale,r*scale,stroke=1,fill=0)
        else:
            path=c.beginPath();path.moveTo(ox+curve[0][0]*scale,oy+curve[0][1]*scale)
            for x,y in curve[1:]:path.lineTo(ox+x*scale,oy+y*scale)
            if kind=='polygon':path.close()
            c.drawPath(path,stroke=1,fill=0)


def _add(d,curves,layer):
    for kind,curve in curves:
        if kind=='circle':d.circle(*curve,layer)
        else:d.polyline(curve,layer,closed=kind=='polygon')


def export(data,sheet,directory):
    """One DXF and SVG per operation, plus one DXF per sheet with every operation on its own layer."""
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    index=[];ops,hand=features(data,sheet);combined=DXF()
    for operation,curves in ops.items():
        stem=f'{sheet["id"]}-cnc-{operation}';d=DXF();_add(d,curves,'CUT' if operation=='cut' else operation);_add(combined,curves,'CUT' if operation=='cut' else operation)
        svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{sheet["width"]}mm" height="{sheet["height"]}mm" viewBox="0 0 {sheet["width"]} {sheet["height"]}">',f'<g transform="translate(0 {sheet["height"]}) scale(1 -1)" fill="none" stroke="black" stroke-width="0.01">']
        for kind,curve in curves:
            if kind=='circle':x,y,r=curve;svg.append(f'<circle cx="{x}" cy="{y}" r="{r}"/>')
            else:svg.append(f'<{"polygon" if kind=="polygon" else "polyline"} points="'+ ' '.join(f'{x},{y}' for x,y in curve)+'"/>')
        svg+=['</g>','</svg>']
        d.save(directory/f'{stem}.dxf');(directory/f'{stem}.svg').write_text('\n'.join(svg)+'\n')
        index.append({'operation':operation,'dxf':stem+'.dxf','svg':stem+'.svg','count':len(curves)})
    combined.save(directory/f'{sheet["id"]}-cnc-all-layers.dxf')
    sheet['hand_drilling']=hand
    return index
