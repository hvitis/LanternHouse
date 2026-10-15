"""The 3D-print checks, and the published prints in prints/: complete, current and printable.

No CAD kernel is needed. The checks run on small hand-made meshes, and every published STL is read and checked
again with print_mesh (numpy), the same code the generator used.
"""
import json, zipfile
import numpy as np
import pytest

import print_build, print_mesh

PRINTER=print_mesh.printer()
HEX=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]

def hexahedron(bottom,top,height):
    """A closed box-like solid: a bottom rectangle (w, d) at z=0 and a top rectangle at z=height, both centred."""
    (bw,bd),(tw,td)=bottom,top
    V=[(-bw/2,-bd/2,0),(bw/2,-bd/2,0),(bw/2,bd/2,0),(-bw/2,bd/2,0),(-tw/2,-td/2,height),(tw/2,-td/2,height),(tw/2,td/2,height),(-tw/2,td/2,height)]
    return np.array(V,float),np.array(HEX)

def statuses(V,F,**kw):
    return {c['id']:c['status'] for c in print_mesh.analyse(V,F,PRINTER,**kw)['checks']}

def test_a_block_passes_and_is_measured():
    V,F=hexahedron((40,40),(40,40),40)
    report=print_mesh.analyse(V,F,PRINTER)
    assert report['status']=='pass',report['checks']
    assert report['volume']==pytest.approx(64000) and report['size']==[40,40,40]
    wall=next(c for c in report['checks'] if c['id']=='wall');assert 'Thinnest wall 40.00 mm' in wall['detail']
    assert report['grams']['solid']==pytest.approx(64*PRINTER['material']['density'],rel=1e-3)

def test_an_open_mesh_fails():
    V,F=hexahedron((40,40),(40,40),40)
    assert statuses(V,F[:-1])['closed']=='fail'

def test_two_pieces_fail():
    V,F=hexahedron((40,40),(40,40),40)
    V2=V+[60,0,0];assert statuses(np.vstack([V,V2]),np.vstack([F,F+8]))['pieces']=='fail'

def test_a_45_degree_slope_needs_no_support_but_a_wider_one_does():
    V,F=hexahedron((40,40),(80,80),20)    # leans out 45 degrees on every side
    assert statuses(V,F)['overhang']=='pass'
    V,F=hexahedron((40,40),(90,90),20)    # 51 degrees
    assert statuses(V,F)['overhang']=='warn'

def test_a_thin_plate_fails_the_wall_check():
    V,F=hexahedron((60,60),(60,60),.8)
    assert statuses(V,F)['wall']=='fail'

def test_a_part_that_fits_the_small_parts_cylinder_fails_unless_it_is_not_a_toy():
    V,F=hexahedron((20,20),(20,20),20)
    assert statuses(V,F)['small_parts']=='fail'
    assert 'small_parts' not in statuses(V,F,toy=False)

def test_too_big_for_the_bed_fails():
    V,F=hexahedron((300,40),(300,40),40)
    assert statuses(V,F)['bed']=='fail'

def test_stl_and_3mf_carry_the_same_triangles(tmp_path):
    V,F=hexahedron((40,30),(40,30),20)
    T=V[F].astype('<f4');record=np.zeros(len(F),print_mesh.STL_RECORD);record['corners']=T
    stl=bytes(80)+np.uint32(len(F)).tobytes()+record.tobytes()
    V2,F2=print_mesh.read_stl(stl);assert len(V2)==8 and len(F2)==12
    print_mesh.write_3mf(tmp_path/'a.3mf',V2,F2,'A & B')
    first=(tmp_path/'a.3mf').read_bytes();print_mesh.write_3mf(tmp_path/'a.3mf',V2,F2,'A & B')
    assert (tmp_path/'a.3mf').read_bytes()==first,'3MF output changes between identical builds'
    with zipfile.ZipFile(tmp_path/'a.3mf') as z:model=z.read('3D/3dmodel.model').decode()
    assert model.count('<vertex ')==8 and model.count('<triangle ')==12 and 'A &amp; B' in model

# ---------- the published prints ----------
MANIFEST=json.loads(print_build.manifest_path().read_text()) if print_build.manifest_path().exists() else None
PUBLISHED=sorted((MANIFEST or {}).get('parts',{}).items())

def test_every_design_is_published():
    assert MANIFEST is not None,'prints/manifest.json is missing: run `make prints` on the Mac'
    assert sorted(MANIFEST['parts'])==print_build.designs(),'Run `make prints` on the Mac to publish the designs in source/prints/'

@pytest.mark.parametrize('name,entry',PUBLISHED,ids=[n for n,_ in PUBLISHED])
def test_published_print_is_current(name,entry):
    assert entry['hash']==print_build.source_hash(name),f'prints/ is older than source/prints/{name}.py or printer.json: run `make prints` on the Mac'

@pytest.mark.parametrize('name,entry',PUBLISHED,ids=[n for n,_ in PUBLISHED])
def test_published_print_checks_again_from_its_stl(name,entry):
    for f in entry['files'].values():
        assert (print_build.PUBLISHED/f['path']).stat().st_size==f['bytes'],f'{f["path"]} does not match the manifest'
    V,F=print_mesh.read_stl(print_build.PUBLISHED/entry['files']['stl']['path'])
    toy=any(c["id"]=="small_parts" for c in entry["checks"])
    again=print_mesh.analyse(V,F,MANIFEST['printer'],toy=toy,small=MANIFEST['small_parts'])
    assert {c['id']:c['status'] for c in again['checks']}=={c['id']:c['status'] for c in entry['checks']}
    assert again['status']!='fail',[c for c in again['checks'] if c['status']=='fail']
