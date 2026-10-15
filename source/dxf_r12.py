"""Minimal, standards-clean DXF R12 (AC1009) writer for cutting files.

R12 with POLYLINE/VERTEX/SEQEND and CIRCLE entities is the format every laser and CNC importer reads (LightBurn,
VCarve/Aspire, Fusion, LibreCAD, Inkscape, RDWorks). The earlier files mixed an R12 header with R2000 LWPOLYLINE
entities, which lenient readers accept but strict ones reject. Units are millimetres ($INSUNITS 4, $MEASUREMENT 1);
every entity sits on a named layer declared in the LAYER table. No extra dependency, so FreeCAD's Python can run it.
"""
from __future__ import annotations
from pathlib import Path

COLOURS={'CUT':1,'CUT_OUTER':1,'CUT_INNER':5,'DRILL_FINISHED':3,'DRILL_STARTER_WASTE':8,'ENGRAVE_IDS':5,
         # One colour per plywood thickness in the single supplier cut file, so laser software can map each to its own power.
         'CUT_3MM':1,'CUT_6MM':3}
# AutoCAD Color Index primary colours, also used by the web preview.
ACI_RGB={1:'#ff0000',2:'#ffff00',3:'#00ff00',4:'#00ffff',5:'#0000ff',6:'#ff00ff',7:'#ffffff'}

def thickness_layer(thickness):return f'CUT_{thickness:g}MM'

class DXF:
    def __init__(self):self.entities=[];self.layers={}

    def layer(self,name):
        name=''.join(ch if ch.isalnum() or ch in '_-' else '_' for ch in name.upper())
        self.layers.setdefault(name,COLOURS.get(name,7 if not self.layers else 1+len(self.layers)%6));return name

    def polyline(self,points,layer='CUT',closed=True):
        layer=self.layer(layer);e=['0','POLYLINE','8',layer,'66','1','10','0.0','20','0.0','30','0.0','70','1' if closed else '0']
        for x,y in points:e+=['0','VERTEX','8',layer,'10',f'{x:.6f}','20',f'{y:.6f}','30','0.0']
        e+=['0','SEQEND','8',layer];self.entities+=e

    def circle(self,x,y,r,layer='CUT'):
        layer=self.layer(layer);self.entities+=['0','CIRCLE','8',layer,'10',f'{x:.6f}','20',f'{y:.6f}','30','0.0','40',f'{r:.6f}']

    def text(self,x,y,height,value,layer='ENGRAVE_IDS'):
        layer=self.layer(layer);self.entities+=['0','TEXT','8',layer,'10',f'{x:.4f}','20',f'{y:.4f}','30','0.0','40',f'{height:.3f}','1',str(value),'72','1','11',f'{x:.4f}','21',f'{y:.4f}','31','0.0']

    def lines(self):
        head=['0','SECTION','2','HEADER','9','$ACADVER','1','AC1009','9','$INSUNITS','70','4','9','$MEASUREMENT','70','1','0','ENDSEC']
        table=['0','SECTION','2','TABLES','0','TABLE','2','LAYER','70',str(len(self.layers))]
        for name,colour in self.layers.items():table+=['0','LAYER','2',name,'70','0','62',str(colour),'6','CONTINUOUS']
        table+=['0','ENDTAB','0','ENDSEC']
        return head+table+['0','SECTION','2','ENTITIES']+self.entities+['0','ENDSEC','0','EOF']

    def save(self,path):Path(path).write_text('\n'.join(self.lines())+'\n')
