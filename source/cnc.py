"""Nominal A3 machining geometry, split by operation, entry face and depth.

No cutter compensation or machine-specific toolpaths are applied here.
"""
from collections import defaultdict
from pathlib import Path
import math


def transform(part,item,x,y):
    a=math.radians(item['angle']);c,s=math.cos(a),math.sin(a)
    points=[(px*c-py*s,px*s+py*c) for px,py in part['outer']]
    return (x*c-y*s-min(px for px,py in points)+item['x'],x*s+y*c-min(py for px,py in points)+item['y'])


def operations(data,sheet):
    result=defaultdict(list)
    for item in sheet['items']:
        p=data['parts'][item['part']];xy=lambda point:transform(p,item,*point)
        if p.get('outercircle'):
            x,y,r=p['outercircle'];result['cut'].append(('circle',(*xy((x,y)),r)))
        elif p.get('retained_edges'):
            for a,b in zip(p['outer'],p['outer'][1:]+p['outer'][:1]):
                if any(abs(a[0 if edge['axis']=='x' else 1]-edge['value'])<1e-6 and abs(b[0 if edge['axis']=='x' else 1]-edge['value'])<1e-6 for edge in p['retained_edges']):continue
                result['cut'].append(('line',[xy(a),xy(b)]))
        else:result['cut'].append(('polygon',[xy(v) for v in p['outer']]))
        for cut in p['cuts']:result['cut'].append(('polygon',[xy(v) for v in cut]))
        for h in p['holes']:
            depth=min(h.get('depth') or p['thickness'],p['thickness']);face=h.get('entry','top')
            kind='drill' if depth>=p['thickness'] else 'pocket' if 'pocket' in h.get('purpose','').lower() or 'recess' in h.get('purpose','').lower() else 'drill'
            key=f'{kind}-{face}-d{h["diameter"]:g}-z{depth:g}'
            result[key].append(('circle',(*xy((h['x'],h['y'])),h['diameter']/2)))
            if h.get('countersink'):
                key=f'countersink-{face}-d{h["countersink"]:g}-z{h["countersink_depth"]:g}'
                result[key].append(('circle',(*xy((h['x'],h['y'])),h['countersink']/2)))
    return dict(result)


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


def export(data,sheet,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    index=[]
    for operation,curves in operations(data,sheet).items():
        stem=f'{sheet["id"]}-cnc-{operation}';lines=['0','SECTION','2','HEADER','9','$INSUNITS','70','4','0','ENDSEC','0','SECTION','2','ENTITIES']
        svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{sheet["width"]}mm" height="{sheet["height"]}mm" viewBox="0 0 {sheet["width"]} {sheet["height"]}">',f'<g transform="translate(0 {sheet["height"]}) scale(1 -1)" fill="none" stroke="black" stroke-width="0.01">']
        for kind,curve in curves:
            if kind=='circle':
                x,y,r=curve;lines+=['0','CIRCLE','100','AcDbEntity','8','CUT','100','AcDbCircle','10',f'{x:.8f}','20',f'{y:.8f}','30','0','40',f'{r:.8f}'];svg.append(f'<circle cx="{x}" cy="{y}" r="{r}"/>')
            else:
                lines+=['0','LWPOLYLINE','100','AcDbEntity','8','CUT','100','AcDbPolyline','90',str(len(curve)),'70','1' if kind=='polygon' else '0']
                for x,y in curve:lines+=['10',f'{x:.8f}','20',f'{y:.8f}']
                svg.append(f'<{"polygon" if kind=="polygon" else "polyline"} points="'+ ' '.join(f'{x},{y}' for x,y in curve)+'"/>')
        lines+=['0','ENDSEC','0','EOF'];svg+=['</g>','</svg>']
        (directory/f'{stem}.dxf').write_text('\n'.join(lines)+'\n');(directory/f'{stem}.svg').write_text('\n'.join(svg)+'\n')
        index.append({'operation':operation,'dxf':stem+'.dxf','svg':stem+'.svg'})
    return index
