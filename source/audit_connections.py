"""Check actual solid contact within each movable furniture assembly."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(sys.executable).resolve().parent.parent/'lib'))
from build_cad import profile_shape, transformed

def main():
    data=json.loads((ROOT/'output/parts.json').read_text())
    # These solids check the visual assemblies; none is written into the CAD project.
    profiles={pid:profile_shape(p) for pid,p in data['parts'].items() if p['category']=='Furniture'}
    shapes={i['id']:transformed(profiles[i['part']],i) for i in data['instances'] if i['part'] in profiles}
    checks=[]
    families=[('K1',1),('K2',1),('K3',1),('K4',4),('K5',1),('V1',1),('V2',1),('V3',1),('V4',1),('V5',1),('V6',1),('U1',2),('U2',1),('U3',2),('U4',1),('U5',1),('N1',1),('N2',1),('N3',1),('PC',1)]
    for family,expected in families:
        prefixes=[family]+({'K2':['K7'],'K5':['K6'],'N3':['N4']}.get(family,[]))
        items=[i for i in data['instances'] if any(i.get('design_part',i['part']).startswith(p) for p in prefixes)]
        parent=list(range(len(items)));contacts=[]
        def root(j):
            while parent[j]!=j:j=parent[j]
            return j
        for j,a in enumerate(items):
            for k,b in enumerate(items[j+1:],j+1):
                sa,sb=shapes[a['id']],shapes[b['id']]
                if sa.distToShape(sb)[0]<1e-5:
                    parent[root(j)]=root(k);contacts.append([a['id'],b['id']])
        components={}
        for j,i in enumerate(items):components.setdefault(root(j),[]).append(i['id'])
        checks.append({'family':family,'expected_assemblies':expected,'connected_assemblies':len(components),'pass':len(components)==expected,'components':list(components.values()),'solid_contacts':contacts})
    report={'method':'OpenCASCADE minimum solid distance <= 0.00001 mm; floors excluded from furniture contact graph','checks':checks,'all_pass':all(c['pass'] for c in checks)}
    (ROOT/'output/reports/furniture-connections.json').write_text(json.dumps(report,indent=2))
    print('Furniture contact audit:',report['all_pass'])
    for c in checks:
        if not c['pass']:print(c)
    if not report['all_pass']:raise RuntimeError('Disconnected furniture pieces')
if __name__=='__main__':main()
