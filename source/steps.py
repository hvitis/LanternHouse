"""Which pieces each assembly step installs.

Every placed fabrication piece (not the display-only furniture, figures or garden) belongs to exactly one step.
The book prints each step's parts and quantities from this table, and verify.py fails the release if a piece is
in no step or in two, so the instructions cannot drift from the model.
"""
from collections import Counter

def _wall(p):return p['category']=='Walls' and p['id'].startswith('W')
def _panel(p):return p.get('assembly_panel')

# (key, selector(instance, part) -> bool), in building order. Keys match the step texts in book.py.
STEPS=[
    ('prepare',lambda i,p:i['group']=='Tools'),
    ('plinth',lambda i,p:i['group']=='Fixed' and (_panel(p) in ('B01','F00') or i['design_part'] in ('F00','B01') or p['id'] in ('PL1','DG1','DB1','A04','BL2'))),
    ('drawer',lambda i,p:i['group']=='Drawer' or p['id']=='DS1'),
    ('rear-shell',lambda i,p:i['group']=='Fixed' and (_wall(p) or p['id'] in ('J01','J02','J03','J04','A02','AB1'))),
    ('frame',lambda i,p:p['id']=='P01' or (i['group']=='Fixed' and (_panel(p) in ('F01','F02') or i['design_part'] in ('F01','F02')))),
    ('rooms',lambda i,p:p['id'] in ('PT1','PT2','PD1')),
    ('opening-shells',lambda i,p:i['group'] in ('WallRight','WallLeft') and (_wall(p) or p['id'] in ('J01','J02','J03','J04','A02'))),
    ('hang',lambda i,p:p['id']=='A06'),
    ('catches',lambda i,p:p['id'] in ('MC1','GP1')),
    ('doors',lambda i,p:p['id'] in ('E01','E04','A03','E10','E11','GD01','GD02','GD03','GD04','ES1') or (p['id']=='ET1' and i['group']=='Fixed')),
    ('windows',lambda i,p:p['id'] in ('WF1','GZ1','D03')),
    ('battens',lambda i,p:p['id'].startswith('BT') or p['id']=='RL1'),
    ('roof',lambda i,p:i['group']=='Roof' and not p['id'].startswith('CH') and p['id']!='E07'),
    ('chimney',lambda i,p:p['id'].startswith('CH') or p['id']=='E07'),
    ('locks',lambda i,p:False),
    ('veranda',lambda i,p:i['group']=='Porch'),
    ('woodpile',lambda i,p:p['id'] in ('WP1','WP2','WP3','HC1')),
    ('lighting',lambda i,p:False),
    ('paint',lambda i,p:False),
    ('check',lambda i,p:False),
]
KEYS=[k for k,_ in STEPS]

def assign(data):
    """(parts per step as {key: Counter(part id)}, instances in no step, instances in more than one)."""
    parts=data['parts'];per={k:Counter() for k in KEYS};missing=[];double=[]
    for inst in data['instances']:
        p=parts[inst['part']]
        if p.get('render_only'):continue
        hits=[k for k,sel in STEPS if sel(inst,p)]
        if not hits:missing.append(inst['id'])
        elif len(hits)>1:double.append((inst['id'],hits))
        else:per[hits[0]][inst['part']]+=1
    return per,missing,double

def listing(counter):
    """'W04 x2, J01 x18, P01 x4' in part-ID order."""
    return ', '.join(f'{pid} x{n}' if n>1 else pid for pid,n in sorted(counter.items()))
