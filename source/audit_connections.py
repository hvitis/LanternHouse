"""Check actual solid contact within each movable furniture assembly."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

# Pieces that belong to another family's assembly, and loose display pieces that are not assemblies at all.
MERGE={'K7':'K2','N4':'N3','LG1':'LG','LG2':'LG','LG3':'LG','WP1':'WP','WP2':'WP','WP3':'WP'}
LOOSE=('BK_','WL1','GL01')

def family(design_part):
    """'GL1B' -> 'GL1', 'L2RA' -> 'L2R', 'K2A' -> 'K2', 'LG2' -> 'LG': the furniture item a piece belongs to."""
    fam=re.sub(r'(?<=..)[A-Z]$','',design_part)
    return MERGE.get(fam,fam)

def furniture_assemblies(data):
    """Group assembled pieces by item, keeping copies of complete bookcases separate."""
    families={}
    for inst in data['instances']:
        part=data['parts'][inst['part']]
        design=inst.get('design_part',inst['part'])
        if part['category']!='Furniture' or inst['group']!='Furniture':continue
        if inst['part']=='BK1' or design.startswith(LOOSE):continue
        key=inst['id'] if part.get('boxes') else family(design)
        families.setdefault(key,[]).append(inst)
    return families

def main():
    sys.path.insert(0,str(Path(sys.executable).resolve().parent.parent/'lib'))
    from build_cad import profile_shape, transformed
    data=json.loads((ROOT/'output/parts.json').read_text())
    # These solids check the visual assemblies; none is written into the CAD project.
    families=furniture_assemblies(data)
    items_all=[i for items in families.values() for i in items]
    profiles={pid:profile_shape(data['parts'][pid]) for pid in {i['part'] for i in items_all}}
    shapes={i['id']:transformed(profiles[i['part']],i) for i in items_all}
    checks=[]
    for fam,items in sorted(families.items()):
        parent=list(range(len(items)));contacts=[]
        def root(j):
            while parent[j]!=j:j=parent[j]
            return j
        for j,a in enumerate(items):
            for k,b in enumerate(items[j+1:],j+1):
                if shapes[a['id']].distToShape(shapes[b['id']])[0]<1e-5:
                    parent[root(j)]=root(k);contacts.append([a['id'],b['id']])
        components={}
        for j,i in enumerate(items):components.setdefault(root(j),[]).append(i['id'])
        checks.append({'family':fam,'pieces':len(items),'connected_assemblies':len(components),'pass':len(components)==1,'components':list(components.values()),'solid_contacts':contacts})
    report={'method':'OpenCASCADE minimum solid distance <= 0.00001 mm; one assembly per furniture item; floors, books, logs and lanterns excluded','checks':checks,'all_pass':bool(checks) and all(c['pass'] for c in checks)}
    (ROOT/'output/reports/furniture-connections.json').write_text(json.dumps(report,indent=2))
    print('Furniture contact audit:',report['all_pass'],f'({len(checks)} items)')
    for c in checks:
        if not c['pass']:print(c)
    if not report['all_pass']:raise RuntimeError('Disconnected furniture pieces')
if __name__=='__main__':main()
