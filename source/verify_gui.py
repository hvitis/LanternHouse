"""Optional native GUI restore check; run with FreeCAD's Python."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(sys.executable).resolve().parent.parent/'lib'))
import FreeCAD as App
import FreeCADGui as Gui
def main():
    Gui.showMainWindow();doc=App.openDocument(str(ROOT/'output/cad/LanternwoodHouse.FCStd'))
    data=json.loads((ROOT/'output/parts.json').read_text());samples={}
    ok=True
    for name,pid in [('W02_01','W02'),('R01_01','R01'),('F01_01','F01')]:
        obj=doc.getObject(name);actual=obj.ViewObject.ShapeColor
        wanted=tuple(int(data['parts'][pid]['color'][j:j+2],16)/255 for j in (1,3,5))
        samples[name]={'actual':actual,'expected':wanted,'visible':obj.ViewObject.Visibility}
        ok=ok and all(abs(a-b)<.001 for a,b in zip(actual,wanted)) and obj.ViewObject.Visibility
    report={'all_pass':ok,'opened_objects':len(doc.Objects),'samples':samples,'profile_hidden':not doc.getObject('W02_Profile').ViewObject.Visibility,'guide_hidden':not doc.getObject('FS_Base_1').ViewObject.Visibility}
    report['all_pass']=report['all_pass'] and report['profile_hidden'] and report['guide_hidden']
    (ROOT/'output/reports/gui-reopen.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));App.closeDocument(doc.Name)
    if not report['all_pass']:raise RuntimeError('Native GUI restore check failed')
if __name__=='__main__':main()
