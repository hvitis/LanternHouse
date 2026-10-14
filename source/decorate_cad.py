"""Attach native FreeCAD GUI materials/visibility to a headless-generated document."""
import json,math,struct,zipfile,xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def rgba(hexval):return int(hexval[1:]+'ff',16)
def main():
    data=json.loads((ROOT/'output/parts.json').read_text());path=ROOT/'output/cad/MoominHouse.FCStd'
    with zipfile.ZipFile(path) as z:entries={n:z.read(n) for n in z.namelist() if n!='GuiDocument.xml' and not n.startswith('MoominMaterial_')}
    native=ET.fromstring(entries['Document.xml']);root=ET.Element('Document',SchemaVersion='1',HasExpansion='1');ET.SubElement(root,'Expand');views=ET.SubElement(root,'ViewProviderData',Count='0')
    inst={i['id'].replace('-','_'):i for i in data['instances'] if not data['parts'][i['part']].get('render_only')};count=0
    figures={f['id'].replace('-','_') for f in data['derived']['figures']}   # thermo-clay solids, white clay
    for obj in native.find('Objects').findall('Object'):
        name=obj.attrib['name'];typ=obj.attrib.get('type','');count+=1
        vp=ET.SubElement(views,'ViewProvider',name=name,expanded='0',treeRank='-1',Extensions='True')
        ET.SubElement(vp,'Extensions',Count='0')
        props=ET.SubElement(vp,'Properties',Count='1',TransientCount='0')
        item=inst.get(name);visible=bool(item and item['group'] not in ('Tools','Accessories')) or name in ('Fixed','WallLeft','WallRight','Porch','Roof','RoofLocks','Furniture','Figures','Drawer') or name in figures
        prop=ET.SubElement(props,'Property',name='Visibility',type='App::PropertyBool',status='1');ET.SubElement(prop,'Bool',value=str(visible).lower())
        if typ.startswith('Part::'):
            hexval=(item.get('color') or data['parts'][item['part']]['color']) if item else '#BD8B5D'
            if name in figures:hexval=data['clay'][next(f['key'] for f in data['derived']['figures'] if f['id'].replace('-','_')==name)]['mesh']['palette'][0]
            if name.startswith('FS_'):hexval='#C19A55'
            if name.startswith('J_'):hexval='#B56535'
            filename='MoominMaterial_'+name
            # Native PropertyMaterialList version 3: count, four colors, floats, three empty strings.
            entries[filename]=struct.pack('<IIIIIffIII',1,0x555555ff,rgba(hexval),0x777777ff,0xff,.25,0,0,0,0)
            prop=ET.SubElement(props,'Property',name='ShapeAppearance',type='App::PropertyMaterialList',status='1');ET.SubElement(prop,'MaterialList',file=filename,version='3')
            prop=ET.SubElement(props,'Property',name='ShapeColor',type='App::PropertyColor',status='1');ET.SubElement(prop,'PropertyColor',value=str(rgba(hexval)))
            linecolor='#B56535' if name.startswith('J_') else '#197F98' if name.startswith('FS_') else '#284849'
            prop=ET.SubElement(props,'Property',name='LineColor',type='App::PropertyColor',status='1');ET.SubElement(prop,'PropertyColor',value=str(rgba(linecolor)))
            prop=ET.SubElement(props,'Property',name='LineWidth',type='App::PropertyFloatConstraint',status='1');ET.SubElement(prop,'Float',value='1.0')
            props.set('Count','5')
    views.set('Count',str(count))
    # Orthographic view from the front-right, looking toward the middle of the tower.
    matrix=[[math.sqrt(3)/2,-.25,math.sqrt(3)/4],[.5,math.sqrt(3)/4,-.75],[0,math.sqrt(3)/2,.5]]
    qw=math.sqrt(1+sum(matrix[i][i] for i in range(3)))/2;qx=(matrix[2][1]-matrix[1][2])/(4*qw);qy=(matrix[0][2]-matrix[2][0])/(4*qw);qz=(matrix[1][0]-matrix[0][1])/(4*qw);angle=2*math.acos(qw);s=math.sin(angle/2)
    ET.SubElement(root,'Camera',settings=f'OrthographicCamera {{ position 519.615 -900 950 orientation {qx/s} {qy/s} {qz/s} {angle} focalDistance 1200 height 950 }}')
    entries['GuiDocument.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    preview=ROOT/'output/previews/house-closed.png'
    if preview.exists():entries['thumbnails/Thumbnail.png']=preview.read_bytes()
    temp=path.with_suffix('.styled.FCStd')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for n,b in entries.items():z.writestr(n,b)
    temp.replace(path)
    (ROOT/'output/reports/native-materials.json').write_text(json.dumps({'view_providers':count,'visible_assembly_parts':sum(i['group'] not in ('Tools','Accessories') for i in inst.values()),'colors':'Native PropertyMaterialList v3 and ShapeColor compatibility property','construction_profiles':'Hidden; editable in ProfileLibrary','guides':'Toggle Fasteners and JointGuides to inspect outlined geometry and axes'},indent=2))
    print('Native CAD colors and visibility saved')
if __name__=='__main__':main()
