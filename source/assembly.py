"""Model-derived instructions and purchasing list shared by the book and web companion.

This module does not import PDF, CAD or generated files.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import steps as steplib

PARTS_PL_EXTRA = {
    'A04': 'Klocek stopki ramy tylnej (drewno lite)',
    'DS1': 'Kołek ogranicznika szuflady (drewno twarde)',
    'GZ1': 'Szklenie okna (przezroczysty PET)',
    'A02': 'Klocek wzmocnienia zawiasu (drewno lite)',
    'A06': 'Podkładka dystansowa zawiasu',
    'MC1': 'Klocek zatrzasku magnetycznego (drewno lite)',
    'GP1': 'Słupek odbojnika ogrodowego (drewno lite)',
    'A03': 'Listwa wzmocnienia zawiasów drzwi',
    'GZ2': 'Szklenie lukarny (przezroczysty PET)',
    'R04': 'Klocek podparcia połaci dachu',
    'WL1': 'Polano drewna opałowego',
    'BL2': 'Stalowa sztaba balastu',
    'AB1': 'Klocek kotwienia przed przewróceniem (drewno lite)',
    'BK1': 'Książka',
    'BC1': 'Regał na książki',
}

def content(data):
    DATA=data;P=data['parts'];CFG=data['config'];DER=data['derived']
    DOORS=CFG['doors'];VER=CFG['veranda'];VER_FACET=int(VER['facet'][1:])-1
    TOPS=DER['floor_tops'];G0=TOPS[0];PITCH=CFG['floor_pitch'];EAVE=DER['roof_eave']
    GUSSETS=(26*CFG['wall_height']/450,PITCH-CFG['thickness']['floor']-20*CFG['wall_height']/450)
    HINGES=[G0+c for c in CFG['wall_hinge']['centers']];DRAWER=CFG['plinth']['drawer']
    MAG,CATCH,STOP=CFG['magnets'],CFG['wall_catch'],CFG['wall_stop'];OPEN=DER['views']['open_angle'];SIDE=DER['drawer']['side']
    SIDE_PL='lewej stronie' if SIDE=='left' else 'prawej stronie'
    BL1=next((f for f in DATA['fasteners'] if f['type']=='BL1'),None);SC1=next(f for f in DATA['fasteners'] if f['type']=='SC1')
    WS1=(1+len(BL1['stack_mm'])-8) if BL1 else 0;LOCK=(P.get('E08',{}).get('thickness',0)+P.get('E09',{}).get('thickness',0));PT=P['P01']['thickness']
    STOPWALLS=' and '.join(k for k,v in P.items() if any('garden stop' in h['purpose'] for h in v['holes']))
    CATCHHOLES=' and '.join(f"{pid}/{h['id']}" for pid,p in P.items() if p.get('assembly_panel')=='F02' for h in p['holes'] if 'catch' in h['purpose'])
    FACETS=DER['facets']
    def zl(values):return ', '.join(f'Z{v:g}' for v in values[:-1])+f' and Z{values[-1]:g}'
    def zl_pl(values):return ', '.join(f'Z{v:g}' for v in values[:-1])+f' oraz Z{values[-1]:g}'
    def facet_ref(i):
        f=FACETS[i];return f['part']+(f' (facet {i+1})' if sum(g['part']==f['part'] for g in FACETS)>1 else '')
    def shell(group):return [f['part'] for f in FACETS if f['group']==group]

    def hardware_rows():
        counts=Counter(f['type'] for f in DATA['fasteners']);kinds=Counter(h['kind'] for h in DATA['hardware'])
        WH,DH=CFG['wall_hinge'],CFG['door_hinge'];sd,sl=DH['screw'];doors=kinds['Door butt hinge']//2;fin=CFG['finial']
        magnets=kinds['Catch magnet']+kinds['Stop magnet'];ST=CFG['stability'];bars=ST['ballast'][0]
        rows = [
          ['HG1','Small butt hinge, 25 mm high; nominal 40 mm open width. Two countersunk D2.5 screw holes per leaf; compare actual hole centers.',sum(h['kind']=='Wall butt hinge' for h in DATA['hardware']),'8','Wall shells: three per side'],
          ['HG2','Miniature butt hinge, 20 mm high; nominal 20 mm open width. Two countersunk holes per leaf for D2 screws.',kinds['Door butt hinge'],str(kinds['Door butt hinge']+2),f'Main, veranda and back doors ({doors} doors)'],
          ['SC1',f'D2.5 x {SC1["length"]:g} mm countersunk wood screw, head D5 (bolt option: M2.5 x {SC1["bolt_length"]:g} countersunk machine screw with an M2.5 dome cap nut).',counts['SC1'],'30',f'HG1 into the wall and the hardwood A02 block (D{WH["block_pilot"]:g} pilot)'],
          ['SC2',f'D{sd:g} x {sl:g} mm countersunk wood screw, head about D{2*sd:g}.',counts['SC2'],'30','HG2 into door / wall and the hardwood A03 strips'],
          ['SC3','D3 x 16 mm countersunk wood screw; head about D6.',counts['SC3'],'10','F00 into foot blocks; B01 into GP1 stop posts'],
          ['BL1','M3 x 30 mm pan-head machine screw; length measured below head.',counts['BL1'],'4','Captive roof turn-buttons'],
          ['NT1','M3 domed cap nut; internal usable cavity at least 3.8 mm; matching thread.',counts['BL1'],'4','Covers both BL1 ends'],
          ['WS1','M3 plain steel washer; D3.2 bore, about D7 outside, exactly 0.5 mm thick.',WS1*counts['BL1'],'12',f'{WS1} per BL1 pivot; spares to set the thread under the cap nut'],
          ['WS2','M3 nylon washer; D3.2 bore, about D7 outside, 0.5 mm thick.',counts['BL1'],'4','Low-friction turn-button pivots'],
          ['WS3','M3 fender (penny) washer; D3.2 bore, D12 outside, 1 mm thick.',2*counts['BL1'],'6',f'Both faces of each {LOCK:g} mm turn-button'],
          ['SP1','M3 nylon spacer; D3.2 bore, outside D6, 8 mm long.',counts['BL1'],'4','Raises turn-buttons above roof ring'],
          ['SP2','Rigid 0.9 mm packing sheet; cut A06 x12, 10 x25 mm. Card, veneer or plastic.',12,'1 A4 sheet','Beneath wall hinge leaves'],
          ['MG1',f'Neodymium disc magnet D{MAG["magnet"][0]:g} x {MAG["magnet"][1]:g} mm, N35-N42, nickel plated, axially magnetised. Only ever fitted enclosed in wood.',magnets,str(magnets),f'Enclosed in the MC1 catch blocks and GP1 stop posts, {MAG["skin"]:g} mm of wood over each'],
          ['SD1',f'Plain steel disc D{MAG["disc"][0]:g} x {MAG["disc"][1]:g} mm, sold as a magnet counter plate; not a magnet itself.',kinds['Steel disc'],str(kinds['Steel disc']+2),'F02 underside recesses and the stop recesses in the walls'],
          ['DW1',f'Hardwood dowel rod D{MAG["plug"]:g}: plugs behind the magnets; D{CFG["wall_stop"]["dowel"][0]:g}: stop-post dowels; D{CFG["plinth"]["drawer"]["stop"]["dowel"]:g}: drawer stop and finial.','1 m each','-',f'{magnets} magnet plugs, 4 stop-post dowels, DS1 drawer stop, finial dowel'],
          ['FB1',f'Turned beech ball D{fin["ball"]:g} mm with one flat (craft bead without a through hole, or drill blind).',1,'1','FN01 roof finial'],
          ['CB1','Greyboard (bookbinding board) 2 mm, A3. Glue the 1:1 template on and cut with a knife.','1 sheet','1','R05 roof angle jigs x2'],
          ['PG1',f'Clear PET or PETG sheet {CFG["windows"]["glazing"][0]:g} mm, A4. Never glass or acrylic.','1 sheet','1','GZ1 and GZ2 window glazing'],
          ['TP1','Cotton tape 15 mm, about 1 m.','1 m','1 m','Room door hinges (PD1)'],
          ['FT1','Self-adhesive felt dots D10-12 mm, about 1 mm thick.',ST['pads']+2,str(ST['pads']+4),'Under the base rim pads and on the stop-post faces'],
          ['BL2',f'Flat steel bar {ST["ballast"][1][0]:g} x {ST["ballast"][1][1]:g} x {ST["ballast"][1][2]:g} mm, drilled D3.5 twice; two 3 x 12 wood screws each.',bars,str(bars),'Ballast inside the plinth'],
          ['AT1','Furniture anti-tip strap kit (strap, screw eye, wall plug and screw).',1,'1','From AB1 in the rear shell to the room wall'],
          ['LT1','Optional: warm-white LED string or 3 mm LEDs with resistors; thin wire.','1 set','-','Wire holes behind the left rear pillar'],
        ]
        rows_pl = [
          ['HG1','Mały zawias skrzydełkowy, wys. 25 mm; szer. nominalna po otwarciu 40 mm. Dwa otwory stożkowe D2.5 na skrzydełko; porównać z szablonem.',sum(h['kind']=='Wall butt hinge' for h in DATA['hardware']),'8','Skrzydła ścienne: po trzy na stronę'],
          ['HG2','Miniaturowy zawias skrzydełkowy, wys. 20 mm; szer. nominalna po otwarciu 20 mm. Dwa otwory stożkowe pod wkręty D2.',kinds['Door butt hinge'],str(kinds['Door butt hinge']+2),f'Drzwi główne, werandowe i tylne ({doors} drzwi)'],
          ['SC1',f'Wkręt do drewna ze stożkiem D2.5 x {SC1["length"]:g} mm, łeb D5 (opcja: śruba M2.5 x {SC1["bolt_length"]:g} z nakrętką kołpakową M2.5).',counts['SC1'],'30',f'HG1 do ściany i klocka A02 z twardego drewna (pilot D{WH["block_pilot"]:g})'],
          ['SC2',f'Wkręt do drewna ze stożkiem D{sd:g} x {sl:g} mm, łeb ok. D{2*sd:g}.',counts['SC2'],'30','HG2 do drzwi / ściany i listew A03 z twardego drewna'],
          ['SC3','Wkręt do drewna ze stożkiem D3 x 16 mm; łeb ok. D6.',counts['SC3'],'10','F00 do klocków stopek; B01 do słupków GP1'],
          ['BL1','Śruba maszynowa M3 x 30 mm z łbem walcowym; długość mierzona pod łbem.',counts['BL1'],'4','Obrotowe rygielki mocowania dachu'],
          ['NT1','Nakrętka kołpakowa M3; głębokość gniazda min. 3.8 mm; pasujący gwint.',counts['BL1'],'4','Zabezpieczenie końców śrub BL1'],
          ['WS1','Podkładka zwykła stalowa M3; otwór D3.2, zewn. ok. D7, grubość dokładnie 0.5 mm.',WS1*counts['BL1'],'12',f'{WS1} na oś BL1; zapas do regulacji gwintu pod nakrętką'],
          ['WS2','Podkładka nylonowa M3; otwór D3.2, zewn. ok. D7, grubość 0.5 mm.',counts['BL1'],'4','Niskotarciowe podkładki osi rygielków'],
          ['WS3','Podkładka powiększona (blacharska) M3; otwór D3.2, zewn. D12, grubość 1 mm.',2*counts['BL1'],'6',f'Z obu stron każdego rygielka {LOCK:g} mm'],
          ['SP1','Tulejka dystansowa nylonowa M3; otwór D3.2, zewn. D6, dł. 8 mm.',counts['BL1'],'4','Dystans rygielków nad wieńcem dachu'],
          ['SP2','Sztywny arkusz podkładek 0.9 mm; wyciąć A06 x12, 10 x 25 mm. Karton, fornir lub tworzywo.',12,'1 arkusz A4','Pod skrzydełka zawiasów ściennych'],
          ['MG1',f'Magnes neodymowy walcowy D{MAG["magnet"][0]:g} x {MAG["magnet"][1]:g} mm, N35-N42, niklowany. Montowany wyłącznie jako zamknięty w drewnie.',magnets,str(magnets),f'Zamknięte w klockach MC1 i słupkach GP1, z warstwą drewna {MAG["skin"]:g} mm nad każdym'],
          ['SD1',f'Krążek stalowy D{MAG["disc"][0]:g} x {MAG["disc"][1]:g} mm, przeciwpytka dla magnesu; sam nie jest magnesem.',kinds['Steel disc'],str(kinds['Steel disc']+2),'Gniazda pod stropem F02 i gniazda odbojników w ścianach'],
          ['DW1',f'Kołek z twardego drewna D{MAG["plug"]:g}: zaślepki magnesów; D{CFG["wall_stop"]["dowel"][0]:g}: kołki słupków; D{CFG["plinth"]["drawer"]["stop"]["dowel"]:g}: ogranicznik i zwieńczenie.','po 1 m','-',f'{magnets} zaślepek magnesów, 4 kołki słupków, ogranicznik szuflady DS1, kołek zwieńczenia'],
          ['FB1',f'Toczona kula bukowa D{fin["ball"]:g} mm ze spłaszczeniem (koralik bez przelotu lub wiercony ślepo).',1,'1','Zwieńczenie dachu FN01'],
          ['CB1','Tektura introligatorska (szara) 2 mm, A3. Nakleić szablon 1:1 i wyciąć nożykiem.','1 arkusz','1','Wzorniki kątowe dachu R05 x2'],
          ['PG1',f'Przezroczysta formatka PET lub PETG {CFG["windows"]["glazing"][0]:g} mm, A4. Nigdy szkło ani plexi.','1 arkusz','1','Szklenie okien wieży GZ1 i lukarn GZ2'],
          ['TP1','Taśma bawełniana 15 mm, ok. 1 m.','1 m','1 m','Zawiasy drzwi pokojowych (PD1)'],
          ['FT1','Samoprzylepne podkładki filcowe D10-12 mm, grubość ok. 1 mm.',ST['pads']+2,str(ST['pads']+4),'Pod stopkami podstawy i na powierzchniach słupków GP1'],
          ['BL2',f'Płaskownik stalowy {ST["ballast"][1][0]:g} x {ST["ballast"][1][1]:g} x {ST["ballast"][1][2]:g} mm, wiercony dwukrotnie D3.5; po dwa wkręty 3 x 12.',bars,str(bars),'Balast wewnątrz cokołu'],
          ['AT1','Zestaw taśmy zabezpieczającej meble przed przewróceniem (taśma, wkręt z uchem, kołek, wkręt).',1,'1','Od klocka AB1 w ścianie tylnej do ściany pokoju'],
          ['LT1','Opcjonalnie: łańcuch LED o ciepłej barwie lub diody LED 3 mm z rezystorami; cienki przewód.','1 zestaw','-','Otwory na przewód za lewym tylnym słupkiem'],
        ]
        return rows, rows_pl

    vd,md,bd=DOORS['veranda'],DOORS['main'],DOORS['back'];wpf=DER['windows_per_floor'];bal=P['C09']['quantity']
    pl=CFG['plinth'];bt=DRAWER['travel'];st=CFG['stairs'];sd,sl=CFG['door_hinge']['screw'];dmr=CFG['dormer']
    gap=CFG['partition']['front_gap']
    divider_end=f'{gap:g} mm short of the front seam' if gap>0 else 'the front seam'
    divider_end_pl=f'{gap:g} mm przed przednim stykiem ścian' if gap>0 else 'przedniego styku ścian'
    divider_gap_note=(f"The {gap:g} mm front gap is wider than a child's finger (5-12 mm gaps pinch)."
                      if gap>0 else 'The divider reaches the front seam with no pinch gap.')
    divider_gap_note_pl=(f"Przednia szczelina {gap:g} mm jest szersza niż palec dziecka (szczeliny 5-12 mm grożą przytrzaśnięciem)."
                         if gap>0 else 'Ścianka działowa sięga przedniego styku bez szczeliny grożącej przytrzaśnięciem.')

    texts={
      'prepare':('Prepare and sort all parts','frame','Sort by thickness and part ID. Cut the test coupons first. Transfer part IDs onto hidden faces, then file edges and check that the matching quantities are present.','No screws yet. Identical parts share one ID and are interchangeable. Furniture and the garden are examples in the 3D view only.'),
      'plinth':('Build the stone plinth','plinth-drawer',f'Join the eight B01 sections over the underside supports and glue the {CFG["stability"]["pads"]} BP1 rim pads under its edge, all in one plane. Keep the screw access holes clear. Screw the {CFG["stability"]["ballast"][0]} BL2 steel ballast bars to B01 either side of the drawer bay. Glue the ten PL1 stone panels upright on B01 around the F00 outline, leaving the two drawer facets on the {SIDE} open. Glue the two DG1 guide walls and the DB1 back stop between them. Join the three F00 pieces flat on a board: press the two front pieces together at their puzzle joint, then glue them to the rear piece over the FS strips underneath. Screw the four A04 feet onto F00 from below (D3.2 clearance, D2 pilots, SC3 x4), then glue F00 on top: the ground floor is now at Z{G0:g}.','Blue outlines / axes: SC3 x4, heads flush under F00 so the drawer passes beneath them. Keep glue out of the drawer bay. Felt dots go under the rim pads at the end.'),
      'drawer':('Make the hidden drawer','plinth-drawer',f'Glue the DR1 bottom between the DR2 sides and the DR3 back: the box is {DRAWER["height"]:g} high, {DRAWER["height"]-4:g} mm deep inside. Glue the two angled DR1 front edges to the inner faces of the DR4 panels. Keep the notched corner down and the finger notches clear. Add small corner blocks between the DR2 sides and the DR4 panels. Wax the underside and slide the drawer in from the {SIDE}. Then, from under the base, push the DS1 dowel up through its B01 hole into the slot in the drawer bottom and glue it there: the drawer now stops at {bt:g} mm and can never be pulled out onto a child\'s feet.','Paint the drawer front exactly like the plinth so it stays hidden. The slot also keeps the drawer running straight; wax it too.'),
      'rear-shell':('Make the fixed rear shell','walls-rear',f'Join {", ".join(shell("Fixed"))} in this order (facets 4-9) around the full-size floor outline on F00. Each adjacent panel pair forms a 150-degree inside corner. At heights {GUSSETS[0]:.1f} and {GUSSETS[1]:.1f} within every room interval glue two J01 ribs, each across a whole facet and onto its two neighbours, and one J02 bracket in the corner left over: dry-fit each rib, then glue its three walls to it at once, so it sets both corner angles. Beside the {vd} veranda door and the {bd} back door the low ground-floor braces sit just above the opening. Glue the A02 hinge blocks on the two hinge facets and the AB1 anti-tip anchor block inside {CFG["stability"]["anchor"]["facet"]}, near the top.','J2 orange joint marks: glue every rib edge that touches a wall. Glue the fixed shell to F00. Do not glue the temporary alignment floor yet.'),
      'frame':('Build the independent floor frame','frame',f'Install four continuous P01 pillars on the foot blocks. Each 6 mm floor is three pieces: press the two front pieces together at the puzzle joint on the house axis, then join them to the rear piece at the CNC finger joint (dry-fit first: both joints have a small gap, the teeth relieved corners) and glue the {CFG["fabrication"]["floor_support"][0]:g} x {CFG["fabrication"]["floor_support"][1]:g} mm FS strips across the finger-joint seam underneath. Slide both F01 levels down over the pillar openings (dogbone corners) to undersides Z{TOPS[1]-6:g} and Z{TOPS[2]-6:g}. Seat F02 on the pillar tops at Z{TOPS[3]-6:g}. Fit small metal angle brackets (added after production, not in this kit) under both F01 levels and F02.',f'J1: floors rest on the pillars and the metal supports. Floor tops: {zl(TOPS)}. Only F01 has pillar openings; play access is through the opening walls.'),
      'rooms':('Fit the room dividers and doors','rooms',f'On each storey glue one divider ({"PT2 on the ground floor, PT1 above" if "PT2" in P else "PT1 on all floors"}) along the house axis, from the rear corner to {divider_end}: its rear notches slip over the corner ribs; glue them to the ribs. Hang a PD1 door leaf in each {CFG["partition"]["door_width"]:g} x {CFG["partition"]["door_height"]:g} doorway on two strips of cotton tape at the rear jamb; it swings into the right-hand room.',f'{divider_gap_note} No metal in the room doors.'),
      'opening-shells':('Build the two opening shells','wall-right',f'Right shell: {", ".join(shell("WallRight"))} (facets 1-3). Left shell: {", ".join(shell("WallLeft"))} (facets 10-12). Use J01 x6 per shell: each rib lies across the middle facet and onto both outer ones, so it holds both corners of the shell; beside the {md} door the ground-floor low rib sits above the door. The {md} door hinges at the front seam, where no ribs are needed; use the drawn positions elsewhere. Glue A02 onto the hinge mounting faces.','J2 + J3. Keep glue clear of the hinge and center seams. Do not glue the opening shells to F00.'),
      'hang':('Hang both wall assemblies','wall-left',f'Use HG1 x3 per side, centered at {zl([h+CFG["shell_lift"] for h in HINGES])}: the shells hang {CFG["shell_lift"]:g} mm above F00 (a {CFG["shell_lift"]:g} mm card under them while you drill) so they never rub the plinth. Fit A06 shims below the leaves and align barrels on the axes X+/-{DER["hinge_axes"]["WallRight"][0]:g}, Y0. Check actual hinges against the printed template, then drill D{CFG["wall_hinge"]["block_pilot"]:g} pilots through the hinge holes into the hardwood blocks and drive SC1 x24 (2.5 x 16 mm wood screws).','SC1 x24 outlined blue. Verify the packing thickness against actual barrel geometry; regenerate changed hinge patterns before drilling.'),
      'catches':('Fit the magnetic catches and stops','catches',f'Every magnet is enclosed in solid hardwood. MC1 blocks: drill the D{MAG["bore"]:g} bore {CFG["wall_catch"]["block"][2]-MAG["skin"]:g} mm deep from the underside (depth stop!), drop the magnet in against the {MAG["skin"]:g} mm skin at the top, glue a D{MAG["plug"]:g} dowel plug behind it with epoxy and sand flush. GP1 posts: the same from the back face, {CFG["wall_stop"]["post"]-MAG["skin"]:g} mm deep. Glue each MC1 inside its opening shell, {CATCH["x"]:g} mm from the front seam, top {CATCH["gap"]:g} mm under F02 (card shim). Epoxy the steel discs flush into {CATCHHOLES} in the F02 underside and into the recesses low on the outer face of {STOPWALLS}. Stand each GP1 on B01 on two D{CFG["wall_stop"]["dowel"][0]:g} dowels, glue the foot and drive one SC3 from below; stick a felt dot on its wall-side face.',f'Open each shell to {OPEN:g} degrees: it should touch its post and stay; closed, it should click shut. No magnet is ever visible: if one shows, the bore was too deep - make a new block.'),
      'doors':('Fit the doors and entrance steps','wall-left',f'Fit one E01 door in {md} (main entrance) and one in {vd} (veranda door), hinged on the right-hand jamb seen from outside, and the narrower E04 in {bd} (back door), hinged on its left-hand jamb. Glue the A03 hardwood strips behind each door and its frame, let them cure, then fit HG2 x2 and SC2 x8 per door ({sd:g} x {sl:g} mm). Glue the E10 / E11 thresholds: tops {CFG["thickness"]["wall"]:g} mm above the floor, doors 2 mm above them. Glue the ES1/ET1 stone steps ({st["risers"]} risers) to B01 below the main and back doors.',f'SC2 x{Counter(f["type"] for f in DATA["fasteners"])["SC2"]} total. All doors open outward and have a recessed finger slot, nothing glued on to pull off. Fit GD01 x2 and GD02 x2 as the canopy over the main entrance and GD03 on two GD04 brackets over the back door.'),
      'windows':('Add the window trim','wall-right',f'There are {wpf[0]} ground-floor windows, {wpf[1]} on the middle floor and {wpf[2]} on the bedroom floor: {sum(wpf[:3])} tower windows, each four panes with the wall\'s own cross left solid. Glue one WF1 surround over each window outside, its cross exactly on the wall\'s cross, the sill band at the bottom and the hood on top; glue a GZ1 PET pane inside with clear glue. Fit D03 x1 per wall facet as eave fascia. Paint trim cream.','J5 glued trim: glue each surround over its whole back face. Never bridge a moving seam with glued trim.'),
      'battens':('Seam battens and the rope ladder','walls-rear',f'Glue a 3 x 8 mm batten (BT1 x 9, 411.5 mm) over each of the nine outside corner seams that do not move - never across a hinge corner or the front seam. Each bears on both facet edges; fill the hollow behind it with glue. Battens stop under the fascia; trim to length above the veranda and stop posts as needed. Glue the RL1 rope ladder flat on the batten at the corner between {VER["facet"]} and its neighbour, from the veranda roof up to the eave.','Paint the battens like the walls. The ladder is part of the house: the roof lifts off clear of it.'),
      'roof':('Assemble roof and attic dormers','roof',f'Arrange R01 x{P["R01"]["quantity"]} and the two special R06 panels (above {" and ".join(dmr["over"])}) over the two R05 gauges: the cone rises {DER["total_height"]-3-CFG["finial"]["ball"]-EAVE:.0f} mm above the eave. Reinforce seams with cotton tape. Fit the ring, cleats and R03 top cap, then glue the FN01 ball on its dowel. On each R06 glue the DM01 front, two DM02 sides and the DM04 gable around the opening, the DM06 frame outside and the GZ2 pane inside, then the two DM05 roof panels.','Cut R06 while the sheet is supported. The finial is a smooth ball, not a spire: keep it that way. Never lift the roof by it.'),
      'chimney':('Make the chimney','roof','Glue CH01-CH04 as a hollow square box, with sloped lower edges matching the roof plane. File the short bottom bevels, glue permanently to the rear roof panel and fit the E07 cap.','The complete roof, dormers and chimney lift off together. Never glue the roof ring onto the house walls.'),
      'locks':('Install the captive roof catches','locks',f'Fit BL1 x2 upward through the F02 holes. Follow the washer/spacer stack on the pivot page. Glue each E09 ply on its E08 ply first, an M3 screw through both holes to line them up. Fit the {LOCK:g} mm tabs horizontally at underside Z{EAVE+9:g}, between D12 fender washers. Locked tabs point outward over the roof ring; rotate 90 degrees inward to release.',f'BL1 x2, NT1 x2, WS1 x{2*WS1}, WS2 x2, WS3 x4, SP1 x2. Set pivot friction, then permanent threadlocker on the nuts.'),
      'veranda':('Build and fix the veranda','porch',f'Glue the VS1 front skirt, the two VS2 side skirts and the two VJ1 joists upright on B01 against the plinth, then glue the E03 deck on top (top Z{G0+6:g}, level with the {vd} threshold). Glue the eight 3 mm C01 pieces in pairs to make four 6 mm columns. Align the profiles and clamp flat until cured. Stand two columns at the front corners and two against {vd}. Fit the C02 front header, glue the C10 rear header flat to {vd}, then the two angled C03 side headers. Add the C07 crossframe, the C04 front roof panel, the two C05 side panels (one turned over), the C11 hip caps and the C12 ridge cap. Fit C06 x2 front rails and C08 x2 side rails with {bal} C09 balusters, and the VS3 stair with three ET1 treads ({st["risers"]} risers) on the open end beside {facet_ref((VER_FACET-1)%12)}; paint those treads cream.',f'J5 glued joints. The veranda is permanent: both front walls open past it. The {vd} door opens outward onto the deck; keep its sweep clear.'),
      'woodpile':('Woodpile and cellar hatch','house-closed-veranda',f'Glue the WP1 back against the plinth beside the {bd} back door, the two WP2 sides on B01 and the WP3 roof on top. Glue the HC1 cellar hatch flat on the plinth panel beside the hidden drawer and paint it as old planks.','Logs in the woodpile are for the picture; any you add must be too big to swallow (more than 32 mm across).'),
      'lighting':('Optional LED lighting','plinth-drawer',f'Thread a thin wire from the plinth up through the D{CFG["lighting"]["wire_hole"]:g} holes in F00, both F01 levels and F02 behind the left rear pillar; fix LEDs under each ceiling.','Only an adult reaches the wiring. Never use coin cells.'),
      'paint':('Paint and add paper details','house-open','Prime plywood, fill non-moving seams, sand lightly and apply blue exterior, red roof, cream trim, green base and stone plinth. Glue the printed stone panels on the plinth and, if you like, the fish-scale shingle strips on the roof (decor book) after structural glue and paint cure. Add a compatible clear finish. Stick felt dots under the rim pads.','Keep glue faces, pilots, hinges, catches, the drawer gaps and mating clearances clear of paint build-up. Recheck movement after every coat.'),
      'check':('Open, close and check','house-open',f'To play: swing both walls outward until they rest against the GP1 garden posts, rotate the roof catches inward, and lift the roof if needed. Pull the hidden drawer out to the {SIDE} by its finger notch; it stops at {bt:g} mm. The veranda stays in place. To close: seat the roof, rotate the catches outward and close the walls gently until the catches click. Strap the house to the room wall with the anti-tip kit.',f'The walls stop at the GP1 posts ({OPEN:g} degrees), where the enclosed magnets hold them open. Do the dry-fit and safety checks page. Do not lift the house by its roof, veranda or opening walls.'),
    }

    texts_pl={
      'prepare':('Przygotowanie i segregacja elementów','frame','Posegreguj elementy według grubości i oznaczeń części. Najpierw wytnij próbki testowe. Przenieś oznaczenia części na niewidoczne powierzchnie, następnie oszlifuj krawędzie pilnikiem i sprawdź ilości z wykazem.','Na tym etapie nie używaj wkrętów. Identyczne części mają to samo oznaczenie i są w pełni wymienne. Meble i ogród w widoku 3D mają wyłącznie charakter poglądowy.'),
      'plinth':('Budowa kamiennego cokołu','plinth-drawer',f'Połącz osiem sekcji B01 na dolnych wspornikach i przyklej {CFG["stability"]["pads"]} podkładek krawędziowych BP1 pod ich spodem w jednej płaszczyźnie. Zachowaj dostęp do otworów na wkręty. Przykręć {CFG["stability"]["ballast"][0]} stalowe sztaby balastu BL2 do B01 po obu stronach wnęki szuflady. Przyklej pionowo dziesięć paneli kamiennych PL1 na B01 wokół obrysu F00, pozostawiając otwarte dwa segmenty szuflady po {SIDE_PL}. Przyklej dwie ścianki prowadzące DG1 i tylny ogranicznik DB1 pomiędzy nimi. Połącz trzy elementy F00 na płaskiej płycie: dociśnij dwa przednie elementy na złączu puzzlowym, a następnie przyklej je do tylnego elementu na listwach łączących FS od spodu. Przykręć cztery stopki A04 do F00 od spodu (otwory przelotowe D3.2, piloty D2, SC3 x4), po czym przyklej F00 na wierzchu cokołu: parter znajduje się teraz na poziomie Z{G0:g}.','Niebieskie obrysy / osie: SC3 x4, łby zlicowane pod F00, aby szuflada swobodnie się przesuwała. Nie dopuść do przedostania się kleju do komory szuflady. Podkładki filcowe nakleja się pod krawędziami na samym końcu.'),
      'drawer':('Wykonanie ukrytej szuflady','plinth-drawer',f'Sklej dno DR1 pomiędzy bokami DR2 i tyłem DR3: skrzynka ma {DRAWER["height"]:g} mm wysokości i {DRAWER["height"]-4:g} mm głębokości wewnętrznej. Przyklej dwie skośne przednie krawędzie DR1 do wewnętrznych powierzchni paneli DR4. Zachowaj wycięty narożnik u dołu i nie zasłaniaj wycięć na palce. Dodaj małe klocki narożne pomiędzy bokami DR2 a panelami DR4. Nawoskuj spód i wsuń szufladę od strony {SIDE_PL}. Następnie od spodu podstawy wsuń kołek DS1 przez otwór w B01 w szczelinę w dnie szuflady i wklej go: szuflada wysuwa się teraz na {bt:g} mm i nigdy nie wypadnie na stopy dziecka.','Pomaluj front szuflady dokładnie tak samo jak cokół, aby pozostała ukryta. Szczelina prowadzi również szufladę prosto; ją również należy nawoskować.'),
      'rear-shell':('Montaż stałej ściany tylnej','walls-rear',f'Połącz {", ".join(shell("Fixed"))} w tej kolejności (segmenty 4-9) wokół pełnowymiarowego obrysu stropu na F00. Każda sąsiednia para paneli tworzy narożnik wewnętrzny o kącie 150 stopni. Na wysokościach {GUSSETS[0]:.1f} i {GUSSETS[1]:.1f} w obrębie każdej kondygnacji przyklej dwa żebra J01, każde w poprzek całego segmentu i na dwa sąsiednie, oraz jeden wspornik J02 w pozostałym narożniku: przymierz każde żebro na sucho, a następnie przyklej do niego jednocześnie trzy ściany, ustalając oba kąty narożników. Obok drzwi werandy {vd} i drzwi tylnych {bd} dolne usztywnienia parteru znajdują się tuż nad otworami. Przyklej klocki zawiasowe A02 na dwóch segmentach z otworami zawiasów oraz klocek kotwienia AB1 wewnątrz {CFG["stability"]["anchor"]["facet"]}, blisko góry.','Pomarańczowe znaczniki połączeń J2: nanieś klej na każdą krawędź żebra stykającą się ze ścianą. Przyklej stałą ścianę tylną do F00. Nie przyklejaj jeszcze tymczasowego stropu montażowego.'),
      'frame':('Budowa niezależnej ramy stropów','frame',f'Zamontuj cztery ciągłe słupki P01 na klockach stopek. Każdy strop 6 mm składa się z trzech części: dociśnij dwa przednie elementy na złączu puzzlowym w osi domu, a następnie połącz je z elementem tylnym na złączu palcowym CNC (najpierw przymierz na sucho: oba złącza mają niewielki luz, zęby mają zaokrąglone narożniki) i przyklej listwy FS {CFG["fabrication"]["floor_support"][0]:g} x {CFG["fabrication"]["floor_support"][1]:g} mm w poprzek spoiny palcowej od spodu. Wsuń oba poziomy F01 w dół przez otwory na słupki do poziomów spodu Z{TOPS[1]-6:g} i Z{TOPS[2]-6:g}. Osadź F02 na szczycie słupków na poziomie Z{TOPS[3]-6:g}. Zamontuj małe metalowe kątowniki pod oboma poziomami F01 oraz F02.',f'J1: stropy spoczywają na słupkach i metalowych wspornikach. Wierzchy stropów: {zl_pl(TOPS)}. Tylko F01 posiada otwory na słupki; dostęp do zabawy zapewniają otwierane ściany.'),
      'rooms':('Montaż ścianek działowych i drzwi pokojowych','rooms',f'Na każdej kondygnacji wklej jedną ściankę działową w osi domu, od tylnego narożnika do {divider_end_pl}: jej tylne wycięcia nasuwają się na żebra narożne; przyklej je do żeber. Zawieś skrzydło drzwiowe PD1 w każdym otworze drzwiowym {CFG["partition"]["door_width"]:g} x {CFG["partition"]["door_height"]:g} na dwóch paskach taśmy bawełnianej przy tylnym węgarze; skrzydło otwiera się do prawego pokoju.',f'{divider_gap_note_pl} Brak metalowych elementów w drzwiach wewnętrznych.'),
      'opening-shells':('Budowa dwóch otwieranych skrzydeł ściennych','wall-right',f'Prawe skrzydło: {", ".join(shell("WallRight"))} (segmenty 1-3). Lewe skrzydło: {", ".join(shell("WallLeft"))} (segmenty 10-12). Użyj po 6 szt. J01 na skrzydło: każde żebro leży w poprzek środkowego segmentu i łączy się z oboma zewnętrznymi, trzymając oba narożniki skrzydła; obok drzwi {md} dolne żebro parteru znajduje się nad drzwiami. Drzwi {md} mają zawiasy na przednim styku, gdzie żebra nie są potrzebne; w pozostałych miejscach użyj wyznaczonych pozycji. Przyklej A02 na powierzchniach montażowych zawiasów.','J2 + J3. Klej nie może dostać się w okolice zawiasów ani spoiny czołowej. Nie przyklejaj otwieranych skrzydeł do płyty F00.'),
      'hang':('Zawieszenie obu skrzydeł ściennych','wall-left',f'Użyj zawiasów HG1 po 3 szt. na stronę, wyśrodkowanych na wysokościach {zl_pl([h+CFG["shell_lift"] for h in HINGES])}: skrzydła wiszą {CFG["shell_lift"]:g} mm nad F00 (podłóż karton {CFG["shell_lift"]:g} mm pod spód podczas wiercenia), dzięki czemu nigdy nie ocierają o cokół. Załóż podkładki A06 pod skrzydełka zawiasów i wyrównaj osie obrotu X+/-{DER["hinge_axes"]["WallRight"][0]:g}, Y0. Porównaj rzeczywiste zawiasy z wydrukowanym szablonem, a następnie nawierć otwory prowadzące D{CFG["wall_hinge"]["block_pilot"]:g} przez otwory zawiasów w klockach z twardego drewna i wkręć wkręty SC1 (24 szt., 2.5 x 16 mm).','SC1 x24 oznaczone niebieskim obrysem. Sprawdź grubość podkładek względem rzeczywistej geometrii zawiasu; w razie potrzeby zaktualizuj szablony przed wierceniem.'),
      'catches':('Montaż zatrzasków magnetycznych i odbojników','catches',f'Każdy magnes jest zamknięty w litym twardym drewnie. Klocki MC1: wywierć otwór D{MAG["bore"]:g} na głębokość {CFG["wall_catch"]["block"][2]-MAG["skin"]:g} mm od spodu (ogranicznik głębokości!), włóż magnes pod {MAG["skin"]:g} mm warstwę drewna u góry, wklej kołek zaślepiający D{MAG["plug"]:g} na żywicę epoksydową i zeszlifuj na gładko. Słupki GP1: to samo od tylnej strony na głębokość {CFG["wall_stop"]["post"]-MAG["skin"]:g} mm. Przyklej klocki MC1 wewnątrz otwieranych skrzydeł, {CATCH["x"]:g} mm od przedniego styku, górną krawędzią {CATCH["gap"]:g} mm pod F02 (podkładka z kartonu). Wklej stalowe krążki na żywicę epoksydową w gniazda na spodzie F02 oraz w gniazda na zewnętrznych ścianach. Ustaw słupki GP1 na B01 na dwóch kołkach D{CFG["wall_stop"]["dowel"][0]:g}, przyklej podstawę i wkręć wkręt SC3 od spodu; naklej krążek filcowy od strony ściany.',f'Otwórz każde skrzydło do kąta {OPEN:g} stopni: powinno dotknąć słupka i przy nim pozostać; po zamknięciu powinno pewnie zatrzasnąć się na magnesie. Żaden magnes nie może być widoczny.'),
      'doors':('Montaż drzwi zewnętrznych i schodów wejściowych','wall-left',f'Zamontuj drzwi E01 w otworze {md} (wejście główne) i drugie w {vd} (drzwi na werandę), zawieszone na prawym węgarze patrząc od zewnątrz, oraz węższe drzwi E04 w otworze {bd} (drzwi tylne), zawieszone na lewym węgarze. Przyklej listwy wzmacniające A03 z twardego drewna za każdymi drzwiami i ościeżnicą, odczekaj na związanie kleju, a następnie zamontuj zawiasy HG2 po 2 szt. i wkręty SC2 po 8 szt. na drzwi ({sd:g} x {sl:g} mm). Przyklej progi E10 / E11: górna krawędź {CFG["thickness"]["wall"]:g} mm nad podłogą, drzwi 2 mm nad progiem. Przyklej schodki kamienne ES1/ET1 ({st["risers"]} stopnie) do B01 pod drzwiami głównymi i tylnymi.',f'Łącznie SC2 x{Counter(f["type"] for f in DATA["fasteners"])["SC2"]}. Wszystkie drzwi otwierają się na zewnątrz i mają frezowane zagłębienie na palec. Zamontuj GD01 x2 i GD02 x2 jako daszek nad wejściem głównym oraz GD03 na wspornikach GD04 nad drzwiami tylnymi.'),
      'windows':('Montaż opasek okiennych i szklenia','wall-right',f'W wieży znajduje się {wpf[0]} okien na parterze, {wpf[1]} na piętrze i {wpf[2]} na poddaszu: łącznie {sum(wpf[:3])} okien wieży, każde z czterema szybkami i integralnym krzyżem w ścianie. Przyklej opaskę WF1 na zewnątrz każdego okna, dokładnie pokrywając krzyż ściany, z parapetem na dole i gzymsem na górze; wklej szybkę PET GZ1 od wewnątrz za pomocą przezroczystego kleju. Zamontuj listwy podokapowe D03 po 1 szt. na każdy segment ściany. Pomaluj opaski na kremowo.','Połączenie klejone J5: nanieś klej na całą tylną powierzchnię opaski. Nigdy nie łącz ruchomych krawędzi przyklejaną opaską okienną.'),
      'battens':('Listwy stykowe i drabinka sznurowa','walls-rear',f'Przyklej listwę 3 x 8 mm (BT1 x 9, 411.5 mm) na każdym z dziewięciu zewnętrznych narożników stałych — nigdy na narożniku z zawiasami ani na przednim styku otwieranych ścian. Każda listwa opiera się o krawędzie obu segmentów; wypełnij klejem zagłębienie za listwą. Listwy kończą się pod deską okapową; w razie potrzeby przytnij je nad werandą i słupkami odbojników. Przyklej drabinkę sznurową RL1 na płasko do listwy na narożniku werandy, od daszku werandy aż pod okap.','Pomaluj listwy w kolorze ścian. Drabinka stanowi integralną część domu: dach unosi się swobodnie bez kolizji z drabinką.'),
      'roof':('Montaż stożka dachu i lukarn poddasza','roof',f'Ułóż połacie R01 x{P["R01"]["quantity"]} i dwie specjalne połacie R06 (nad segmentami {" i ".join(dmr["over"])}) na dwóch szablonach montażowych R05: stożek dachu wznosi się na wysokość {DER["total_height"]-3-CFG["finial"]["ball"]-EAVE:.0f} mm nad okap. Wzmocnij spoiny taśmą bawełnianą. Zamontuj wieniec, klocki podparcia i górną zaślepkę R03, a następnie wklej kulę FN01 na kołku. Na każdej połaci R06 przyklej ściankę czołową DM01, dwa boki DM02 i szczyt DM04 wokół otworu, zewnętrzną ramkę DM06 i szybkę GZ2 wewnątrz, a następnie dwie połacie dachu lukarny DM05.','Element R06 wycinaj na stabilnym podłożu. Zwieńczenie to gładka kula, a nie szpic: zachowaj ten kształt. Nigdy nie podnoś dachu za kulę zwieńczenia.'),
      'chimney':('Wykonanie komina','roof','Sklej ścianki CH01-CH04 w pustą skrzynkę o przekroju kwadratowym, ze skośnymi krawędziami dolnymi dopasowanymi do nachylenia połaci dachu. Oszlifuj dolne skosy, przyklej komin na stałe do tylnej połaci dachu i zamontuj daszek E07.','Kompletny dach wraz z lukarnami i kominem unosi się jako jedna całość. Nigdy nie przyklejaj wieńca dachu do ścian domu.'),
      'locks':('Montaż obrotowych rygli dachu','locks',f'Wsuń śruby BL1 x2 od spodu przez otwory w stropie F02. Zastosuj zestaw podkładek i tulejek dystansowych. Sklej warstwy E09 i E08, wyrównując otwory śrubą M3. Zamontuj rygielki {LOCK:g} mm poziomo pod Z{EAVE+9:g} między podkładkami powiększonymi D12. Rygle zablokowane wystają na zewnątrz nad wieniec dachu; obróć o 90 stopni do wewnątrz, aby zwolnić dach.',f'BL1 x2, NT1 x2, WS1 x{2*WS1}, WS2 x2, WS3 x4, SP1 x2. Ustaw opór obrotu rygli, po czym zabezpiecz nakrętki trwałym klejem do gwintów.'),
      'veranda':('Budowa i montaż werandy','porch',f'Przyklej przednią osłonę VS1, dwie boczne osłony VS2 oraz dwie belki VJ1 pionowo do B01 przy cokole, a następnie przyklej podest E03 na wierzchu (poziom Z{G0+6:g}, równo z progiem drzwi na werandę). Sklej osiem elementów C01 grubości 3 mm parami, tworząc cztery kolumny o grubości 6 mm. Wyrównaj profile i ściśnij ściskami do wyschnięcia kleju. Ustaw dwie kolumny w przednich narożnikach i dwie przy ścianie. Zamontuj przednią belkę C02, przyklej tylną belkę C10 płasko do ściany, a następnie dwie skośne belki boczne C03. Dodaj ramę poprzeczną C07, przednią połać dachu C04, dwie połacie boczne C05 (jedną odwróconą), listwy narożne C11 i listwę kalenicową C12. Zamontuj przednie barierki C06 x2 i boczne C08 x2 z {bal} tralkami C09, a także schodki VS3 z trzema stopnicami ET1 ({st["risers"]} stopnie) przy otwartym boku werandy; pomaluj stopnice na kremowo.',f'Połączenia klejone J5. Weranda jest zamontowana na stałe: oba skrzydła ścian otwierają się swobodnie obok niej. Drzwi otwierają się na zewnątrz na podest werandy; zachowaj wolną przestrzeń na ich otwarcie.'),
      'woodpile':('Stos drewna i klapa do piwnicy','house-closed-veranda',f'Przyklej tylną ściankę WP1 do cokołu obok drzwi tylnych, dwa boki WP2 do podstawy B01 i daszek WP3 na wierzchu. Przyklej klapę do piwnicy HC1 płasko na panelu cokołu obok ukrytej szuflady i pomaluj ją w deseń starych desek.','Polana w drewutni na ilustracji mają charakter poglądowy; polana dodane do modelu muszą mieć ponad 32 mm szerokości, aby zapobiec połknięciu przez dziecko.'),
      'lighting':('Opcjonalne oświetlenie LED','plinth-drawer',f'Poprowadź cienki przewód od cokołu w górę przez otwory D{CFG["lighting"]["wire_hole"]:g} w F00, obu poziomach F01 i F02 za lewym tylnym słupkiem; zamocuj diody LED pod każdym stropem.','Dostęp do instalacji elektrycznej może mieć wyłącznie osoba dorosła. Nigdy nie używaj baterii pastylkowych.'),
      'paint':('Malowanie i detale z papieru','house-open','Zagruntuj sklejkę, zaszpachluj nieruchome spoiny, przeszlifuj drobno i pomaluj: niebieskie ściany, czerwony dach, kremowe opaski, zielona podstawa i kamienny cokół. Naklej wydrukowane panele kamienne na cokół oraz, opcjonalnie, paski gontów rybiej łuski na dach po wyschnięciu kleju i farb. Zabezpiecz odpowiednim lakierem bezbarwnym. Naklej filcowe podkładki pod stopkami.','Powierzchnie klejenia, otwory prowadzące, zawiasy, zatrzaski, szczeliny szuflady i luzy robocze muszą pozostać czyste od farby. Sprawdzaj ruchomość elementów po każdej warstwie.'),
      'check':('Otwieranie, zamykanie i kontrola końcowa','house-open',f'Aby otworzyć do zabawy: odchyl oba skrzydła ścian na zewnątrz, aż oprą się o słupki ogrodowe GP1, przekręć rygle dachu do wewnątrz i w razie potrzeby zdejmij dach. Wysuń ukrytą szufladę za wycięcie na palec; zatrzyma się na {bt:g} mm. Weranda pozostaje na swoim miejscu. Aby zamknąć: nałóż dach, obróć rygle na zewnątrz i delikatnie zamknij ściany, aż zatrzasną się magnesy. Przymocuj dom do ściany pokoju za pomocą taśmy zabezpieczającej.',f'Ściany zatrzymują się na słupkach GP1 ({OPEN:g} stopni), gdzie ukryte magnesy utrzymują je w pozycji otwartej. Wykonaj testy montażu na sucho i kontrolę bezpieczeństwa. Nie podnoś domku za dach, werandę ani otwierane ściany.'),
    }

    # The roof attachment is a builder preference, not installed hardware in this model.
    if not any(i['group']=='RoofLocks' for i in DATA['instances']):
        roof=texts['roof'];texts['roof']=(*roof[:3],roof[3]+' Optional roof attachment: leave it removable, use magnets, or make a hinge-style connection. Check the actual fit and opening clearance first.')
        roof_pl=texts_pl['roof'];texts_pl['roof']=(*roof_pl[:3],roof_pl[3]+' Opcjonalne mocowanie dachu: pozostaw dach zdejmowany, użyj magnesów lub wykonaj połączenie zawiasowe. Najpierw sprawdź pasowanie i luzy otwierania.')
        check=texts['check'];texts['check']=(check[0],check[1],check[2].replace('rotate the roof catches inward, and ', '').replace('rotate the catches outward and ', ''),check[3])
        check_pl=texts_pl['check'];texts_pl['check']=(check_pl[0],check_pl[1],check_pl[2].replace('przekręć rygle dachu do wewnątrz i ', '').replace('obróć rygle na zewnątrz i ', ''),check_pl[3])
        texts['locks']=('Optional roof attachment','roof','The roof can remain removable. Magnets or a hinge-style attachment are optional builder choices.','Check the fit and opening clearance with the actual hardware before making a permanent connection.')
        texts_pl['locks']=('Opcjonalne mocowanie dachu','roof','Dach może pozostać zdejmowany. Magnesy lub mocowanie zawiasowe to opcjonalne rozwiązania wybrane przez wykonawcę.','Przed wykonaniem trwałego połączenia sprawdź pasowanie i luzy otwierania z wybranymi okuciami.')
    hardware, hardware_pl = hardware_rows()
    if not any(i['group']=='RoofLocks' for i in DATA['instances']):
        hardware=[row for row in hardware if row[0] not in ('BL1','NT1','WS1','WS2','WS3','SP1')]
        hardware_pl=[row for row in hardware_pl if row[0] not in ('BL1','NT1','WS1','WS2','WS3','SP1')]
    return {'chapters':texts,'chapters_pl':texts_pl,'hardware':hardware,'hardware_pl':hardware_pl}

OPERATIONS = {
 'prepare':[
  ('sort','Sort and label the kit','Transfer each part ID to a hidden face. Sort the pieces by thickness and ID.','T*'),
  ('coupons','Check the fit on scrap','Measure the plywood. Test the joints with T01 and T02 before cutting or gluing structural parts.',''),
  ('jigs','Prepare the roof gauges','Cut two R05 gauges from 2 mm greyboard. Keep them for the roof assembly.','R05')],
 'plinth':[
  ('base','Join the base sections','Dry-fit the B01 sections on a flat board. Join them over their underside supports.','B01*'),
  ('pads','Fit the rim pads','Glue the BP1 pads under the base. Keep all contact faces in one plane.','BP1'),
  ('ballast','Fit the ballast','Fix the steel bars inside the plinth. Keep the drawer bay clear.','BL2'),
  ('guides','Build the plinth and guides','Glue the stone panels, guide walls and back stop onto the base. Leave the drawer opening clear.','PL1 DG1 DB1'),
  ('floor','Join the ground-floor plate','Dry-fit the three F00 pieces. Glue the joints over the FS seam strips on a flat board.','F00* FS*'),
  ('feet','Fit the feet, then seat the floor','Screw the four A04 feet to F00 from below. Keep the heads flush. Then glue F00 onto the plinth.','A04')],
 'drawer':[
  ('box','Build the drawer box','Glue the bottom, sides and back together. Check that the box is square before the glue sets.','DR1 DR2 DR3'),
  ('front','Fit the stone front','Glue both angled front panels onto the box. Keep the finger notches at the bottom.','DR4'),
  ('stop','Fit and test the captive stop','Wax the sliding surfaces. Insert the drawer. Fit DS1 from below into the bottom slot and glue the dowel.','DS1')],
 'rear-shell':[
  ('align','Align the fixed rear walls','Arrange the rear facets around F00. Use the floor outline as an alignment reference.','W*'),
  ('braces','Glue the rear shell braces','Dry-fit the ribs and corner brackets. Glue every contacting edge at the specified heights.','J*'),
  ('backing','Fit the backing and anchor blocks','Glue the hinge backing blocks and anti-tip anchor block inside the rear shell. Let the glue cure before drilling.','A02 AB1')],
 'frame':[
  ('pillars','Stand the four pillars','Install each P01 pillar on its A04 foot block. Check the alignment with the floor openings.','P01'),
  ('panels','Join the elevated floor panels','Join the divided F01 and F02 panels over the FS strips. Check each joint on a flat surface.','FS*'),
  ('levels','Install the floors and their supports','Slide both F01 floors over the pillars. Seat F02 on top. Fit small metal angle brackets beneath the floors before loading them.','F01* F02*')],
 'rooms':[
  ('dividers','Fit the room dividers','Dry-fit the rear notches over the corner ribs. Glue each divider along the house axis.','PT*'),
  ('leaves','Hang the room doors','Attach each PD1 leaf with two cotton-tape hinges at the rear jamb. Check its swing.','PD1')],
 'opening-shells':[
  ('right','Build the right opening shell','Align the right shell facets. Glue their ribs and backing blocks. Keep the hinge and front seams clear.','@WallRight'),
  ('left','Build the left opening shell','Build the left shell separately. Check the mirrored orientation before gluing its ribs and backing blocks.','@WallLeft')],
 'hang':[
  ('template','Check the actual hinges','Compare the actual hinges with the full-size checking templates. Check the hole pattern and barrel position.',''),
  ('packing','Hang and align both shells','Use the specified packing and shell clearance. Drill into the cured hardwood backing. Fit the wall hinges.','A06'),
  ('sweep','Check the wall movement','Open each shell separately. Check the plinth clearance and hinge alignment before continuing.','')],
 'catches':[
  ('enclose','Enclose the catch magnets','Drill from the hidden face with a depth stop. Fit each magnet and epoxy its hardwood plug.','MC1'),
  ('posts','Fit the catches and garden stops','Fit the steel discs and the enclosed magnets in the stop posts. Fix the posts with dowels, glue and screws.','GP1'),
  ('movement','Check the catches','Check that both shells close against the catches and stay against their open stops. No magnet surface can remain exposed.','')],
 'doors':[
  ('backing','Fit the door backing strips','Glue the A03 strips behind the doors and frames. Let the glue cure before drilling.','A03'),
  ('leaves','Hang the exterior doors','Check the hinge side from outside. Hang all three doors with their specified threshold clearances.','E01 E04 E10 E11'),
  ('entrances','Fit entrance steps and canopies','Fit the main and rear entrance steps and canopies. Keep every door sweep clear.','*')],
 'windows':[
  ('trim','Fit the window surrounds','Glue each WF1 surround over the wall cross. Keep the sill at the bottom and the hood at the top.','WF1'),
  ('glazing','Fit the PET glazing','Glue a GZ1 pane inside each tower window with clear glue. Keep glue off the visible pane.','GZ1'),
  ('fascia','Fit the eave fascia','Fit one D03 fascia on each wall facet. Keep moving seams free.','D03')],
 'battens':[
  ('seams','Fit the seam battens','Fit the battens over fixed seams only. Trim them clear of the veranda and stop posts.','BT*'),
  ('ladder','Fit the rope ladder','Glue the ladder at the specified veranda corner. Keep the removable roof clear.','RL1')],
 'roof':[
  ('cone','Build the roof cone','Arrange the roof panels over the R05 gauges. Reinforce the seams with cotton tape. Let the glue cure.','R01 R06'),
  ('ring','Fit the ring and cleats','Join the ring sections. Glue each cleat to the ring and roof skin. Do not glue the ring to the house.','R02* R04'),
  ('dormer-frames','Build both dormer frames','Fit each dormer front, sides and gable around its roof opening.','DM01 DM02 DM04'),
  ('dormer-glazing','Glaze and cover the dormers','Fit the outer frames and PET panes. Then add the dormer roof panels.','DM06 GZ2 DM05'),
  ('finial','Fit the cap and finial','Fit the top cap and the ball on its dowel. Lift the roof by its sides during handling.','R03 FN01')],
 'chimney':[
  ('box','Assemble the chimney','Glue the chimney panels into a square box. Check the lower bevel against the roof slope.','CH*'),
  ('cap','Fix the chimney and cap','Glue the chimney permanently to its roof panel. Fit the cap.','E07')],
 'locks': [('pivots','Fit the roof catches','Assemble the specified washer stacks and captive turn-buttons. Check the release movement.','*')],
 'veranda':[
  ('deck','Build the veranda deck','Fit the skirts and joists against the plinth. Glue the deck level with the veranda threshold.','VS1 VS2 VJ1 E03'),
  ('columns','Laminate the veranda columns','Glue the eight C01 pieces in pairs. Clamp each pair flat until the glue cures.','C01'),
  ('headers','Fit the columns and headers','Stand the four laminated columns. Fit the front, rear and angled side headers.','C02 C03 C10'),
  ('roof','Build the veranda roof','Fit the crossframe and roof panels. Turn over the mirrored side panel. Add the hip and ridge caps.','C07 C04 C05 C11 C12'),
  ('rails','Fit the veranda railings','Fit the front and side rails with their balusters. Check the spacing before the glue sets.','C06 C08 C09'),
  ('stairs','Fit the veranda stairs','Fit the stair sides and treads at the open side of the veranda. Check the door sweep.','VS3 ET1')],
 'woodpile': [('details','Fit the cellar details','Fit the cellar hatch. Add the woodpile only if its parts are included in this model.','*')],
 'lighting': [('wire','Fit optional lighting','Route the wire through the aligned floor holes. Fix the lights under each ceiling. Keep the wiring accessible to an adult.','')],
 'paint':[
  ('coat','Paint and finish the house','Prime, sand and paint the house. Keep the glue faces, hinge gaps and sliding surfaces clear.',''),
  ('paper','Add the paper details','After the finish cures, add the stone panels and optional roof shingles. Fit the felt dots under the rim pads.','')],
 'check':[
  ('functions','Check all moving parts','Check both walls, all doors, the captive drawer stop and the removable roof. Recheck after every coat.',''),
  ('anchor','Anchor the finished house','Fit the anti-tip strap to the rear anchor block and the room wall. Lift the house by its base.','')],
}

OPERATIONS_PL = {
 ('prepare','sort'): ('Segregacja i oznaczenie elementów', 'Przenieś oznaczenia części na niewidoczne powierzchnie. Posegreguj elementy według grubości i oznaczeń.'),
 ('prepare','coupons'): ('Sprawdzenie spasowania na odpadach', 'Zmierz grubość sklejki. Przetestuj połączenia na próbkach T01 i T02 przed wycinaniem lub klejeniem części konstrukcyjnych.'),
 ('prepare','jigs'): ('Przygotowanie wzorników kątowych dachu', 'Wytnij dwa wzorniki R05 z tektury introligatorskiej 2 mm. Zachowaj je do montażu dachu.'),
 ('plinth','base'): ('Połączenie sekcji podstawy', 'Przymierz sekcje B01 na sucho na płaskiej płycie. Połącz je na dolnych listwach wsporczych.'),
 ('plinth','pads'): ('Montaż podkładek krawędziowych', 'Przyklej podkładki BP1 pod spodem podstawy. Utrzymuj wszystkie powierzchnie styku w jednej płaszczyźnie.'),
 ('plinth','ballast'): ('Montaż balastu stalowego', 'Zamocuj stalowe sztaby wewnątrz cokołu. Pozostaw wolną przestrzeń na wnękę szuflady.'),
 ('plinth','guides'): ('Budowa cokołu i prowadnic', 'Przyklej panele kamienne, ścianki prowadzące i tylny ogranicznik do podstawy. Pozostaw otwarty otwór szuflady.'),
 ('plinth','floor'): ('Połączenie płyty parteru', 'Przymierz trzy elementy F00 na sucho. Sklej złącza na listwach łączących FS na płaskiej płycie.'),
 ('plinth','feet'): ('Montaż stopek i osadzenie podłogi', 'Przykręć cztery stopki A04 do F00 od spodu ze zlicowanymi łbami wkrętów. Następnie przyklej F00 do cokołu.'),
 ('drawer','box'): ('Budowa skrzynki szuflady', 'Sklej dno, boki i tył szuflady. Przed związaniem kleju upewnij się, że skrzynka trzyma kąty proste.'),
 ('drawer','front'): ('Montaż kamiennego frontu', 'Przyklej oba skośne panele przednie do skrzynki. Wycięcia na palce umieść u dołu.'),
 ('drawer','stop'): ('Montaż i test ogranicznika szuflady', 'Nawoskuj powierzchnie ślizgowe. Wsuń szufladę. Wsuń kołek DS1 od spodu w szczelinę dna i wklej go.'),
 ('rear-shell','align'): ('Ustawienie stałych ścian tylnych', 'Ustaw tylne segmenty wokół F00. Wykorzystaj obrys stropu jako linię odniesienia.'),
 ('rear-shell','braces'): ('Wklejenie żeber tylnej ściany', 'Przymierz na sucho żebra i narożne wsporniki. Sklej każdą stykającą się krawędź na wyznaczonych wysokościach.'),
 ('rear-shell','backing'): ('Montaż klocków zawiasowych i kotwienia', 'Przyklej klocki wzmocnienia zawiasów oraz klocek kotwienia wewnątrz tylnej ściany. Przed wierceniem odczekaj na związanie kleju.'),
 ('frame','pillars'): ('Ustawienie czterech słupków', 'Zamontuj każdy słupek P01 na klocku stopki A04. Sprawdź pion i spasowanie z otworami w stropach.'),
 ('frame','panels'): ('Połączenie paneli wyższych stropów', 'Połącz podzielone panele F01 i F02 na listwach FS. Sprawdź każde połączenie na płaskiej powierzchni.'),
 ('frame','levels'): ('Montaż stropów i wsporników', 'Nasuń oba stropy F01 na słupki. Osadź strop F02 na szczycie słupków. Zamontuj małe metalowe kątowniki pod stropami przed ich obciążeniem.'),
 ('rooms','dividers'): ('Montaż ścianek działowych', 'Przymierz tylne wycięcia na żebrach narożnych. Przyklej każdą ściankę w osi domu.'),
 ('rooms','leaves'): ('Zawieszenie drzwi wewnętrznych', 'Zamocuj każde skrzydło PD1 na dwóch zawiasach z taśmy bawełnianej przy tylnym węgarze. Sprawdź swobodę otwierania.'),
 ('opening-shells','right'): ('Budowa prawego skrzydła ściennego', 'Wyrównaj segmenty prawego skrzydła. Przyklej żebra i klocki wzmacniające. Zapewnij czystość zawiasów i spoiny czołowej.'),
 ('opening-shells','left'): ('Budowa lewego skrzydła ściennego', 'Zbuduj osobno lewe skrzydło. Przed wklejeniem żeber i klocków upewnij się co do lustrzanej orientacji.'),
 ('hang','template'): ('Sprawdzenie rzeczywistych zawiasów', 'Porównaj rzeczywiste zawiasy z pełnowymiarowym szablonem kontrolnym. Sprawdź rozstaw otworów i pozycję osi obrotu.'),
 ('hang','packing'): ('Zawieszenie i regulacja obu skrzydeł', 'Zastosuj podkładki dystansowe pod skrzydła. Wywierć otwory w klockach z twardego drewna i zamocuj zawiasy ścienne.'),
 ('hang','sweep'): ('Kontrola ruchu otwierania ścian', 'Otwórz każde skrzydło z osobna. Przed kontynuowaniem sprawdź prześwit nad cokołem i osiowość zawiasów.'),
 ('catches','enclose'): ('Osadzenie magnesów zatrzaskowych', 'Wywierć otwory od niewidocznej strony z ogranicznikiem głębokości. Włóż magnesy i wklej zaślepki z twardego drewna na żywicę.'),
 ('catches','posts'): ('Montaż zatrzasków i odbojników ogrodowych', 'Zamontuj stalowe krążki i zamknięte magnesy w słupkach odbojników. Zamocuj słupki na kołkach, kleju i wkrętach.'),
 ('catches','movement'): ('Kontrola działania zatrzasków', 'Sprawdź, czy oba skrzydła domykają się do zatrzasków i zatrzymują przy odbojnikach. Żaden magnes nie może pozostać odsłonięty.'),
 ('doors','backing'): ('Wklejenie listew wzmocnienia drzwi', 'Przyklej listwy A03 za drzwiami i ramami. Przed nawierceniem otworów odczekaj na związanie kleju.'),
 ('doors','leaves'): ('Zawieszenie drzwi zewnętrznych', 'Sprawdź kierunek otwierania od zewnątrz. Zawieś wszystkie troje drzwi z zachowaniem prześwitu nad progiem.'),
 ('doors','entrances'): ('Montaż schodków i daszków wejściowych', 'Zamontuj schodki wejściowe i daszki nad drzwiami głównymi oraz tylnymi. Zachowaj wolną przestrzeń na ruch drzwi.'),
 ('windows','trim'): ('Montaż ozdobnych opasek okiennych', 'Przyklej każdą opaskę WF1 na krzyżu ściany. Parapet umieść na dole, a gzyms na górze.'),
 ('windows','glazing'): ('Montaż szybek z przezroczystego PET', 'Wklej szybki GZ1 wewnątrz każdego okna wieży przezroczystym klejem. Chroń widoczną powierzchnię szybki przed zabrudzeniem klejem.'),
 ('windows','fascia'): ('Montaż listwy podokapowej', 'Zamontuj listwę podokapową D03 na każdym segmencie ściany. Ruchome styki muszą pozostać wolne.'),
 ('battens','seams'): ('Montaż listew maskujących styki', 'Przyklej listwy wyłącznie na stałych połączeniach narożnych. Przytnij je tak, aby nie kolidowały z werandą i odbojnikami.'),
 ('battens','ladder'): ('Montaż drabinki sznurowej', 'Przyklej drabinkę na wyznaczonym narożniku werandy. Zapewnij swobodne zdejmowanie dachu.'),
 ('roof','cone'): ('Montaż stożka dachu', 'Ułóż panele dachowe na wzornikach R05. Wzmocnij spoiny taśmą bawełnianą i odczekaj na związanie kleju.'),
 ('roof','ring'): ('Montaż wieńca i klocków podparcia', 'Połącz sekcje wieńca. Przyklej klocki podparcia do wieńca i poszycia dachu. Nie przyklejaj wieńca do ścian domu.'),
 ('roof','dormer-frames'): ('Budowa konstrukcji lukarn', 'Zamontuj front, boki i szczyt każdej lukarny wokół otworu w dachu.'),
 ('roof','dormer-glazing'): ('Szklenie i zadaszenie lukarn', 'Zamontuj ramki zewnętrzne i szybki z PET. Następnie przyklej daszki lukarn.'),
 ('roof','finial'): ('Montaż zwieńczenia dachu', 'Zamontuj górną zaślepkę i kulę na kołku. Podczas przenoszenia chwytaj dach za boki, a nie za zwieńczenie.'),
 ('chimney','box'): ('Montaż komina', 'Sklej ścianki komina w skrzynkę o przekroju kwadratowym. Dopasuj dolny skos do nachylenia dachu.'),
 ('chimney','cap'): ('Mocowanie komina i daszka', 'Przyklej komin na stałe do połaci dachu i zamontuj daszek ochronny.'),
 ('locks','pivots'): ('Montaż rygli dachu', 'Złóż zestaw podkładek i rygielki obrotowe. Sprawdź płynność obrotu i blokowania.'),
 ('veranda','deck'): ('Budowa podestu werandy', 'Zamontuj osłony i belki podestu przy cokole. Przyklej podest na poziomie progu drzwi na werandę.'),
 ('veranda','columns'): ('Laminowanie kolumn werandy', 'Sklej osiem elementów C01 parami. Ściśnij każdą parę ściskami na płasko do wyschnięcia kleju.'),
 ('veranda','headers'): ('Montaż kolumn i belek nadproży', 'Ustaw cztery sklejone kolumny. Zamontuj przednią, tylną i skośne belki boczne.'),
 ('veranda','roof'): ('Budowa dachu werandy', 'Zamontuj ramę poprzeczną i połacie dachowe. Pamiętaj o odwróceniu lustrzanej połaci bocznej. Dodaj listwy narożne i kalenicowe.'),
 ('veranda','rails'): ('Montaż balustrad werandy', 'Zamontuj przednie i boczne barierki wraz z tralkami. Sprawdź równomierność rozstawu przed związaniem kleju.'),
 ('veranda','stairs'): ('Montaż schodków werandy', 'Zamontuj policzki i stopnice schodów przy otwartym boku werandy. Sprawdź promień otwarcia drzwi.'),
 ('woodpile','details'): ('Montaż detali przyziemia', 'Zamontuj klapę piwniczną. Stos drewna dodaj tylko wtedy, gdy jego elementy znajdują się w tym zestawie.'),
 ('lighting','wire'): ('Montaż opcjonalnego oświetlenia', 'Poprowadź przewody przez pionowe otwory w stropach. Zamocuj oświetlenie pod każdym stropem. Zapewnij dostęp serwisowy wyłącznie dla dorosłych.'),
 ('paint','coat'): ('Malowanie i wykończenie domu', 'Zagruntuj, przeszlifuj i pomaluj domek. Powierzchnie klejenia, szczeliny zawiasów i płaszczyzny ślizgowe muszą pozostać czyste.'),
 ('paint','paper'): ('Naklejenie detali papierowych', 'Po wyschnięciu lakieru naklej panele kamienne i opcjonalne gonty dachowe. Podklej filcowe podkładki pod stopkami.'),
 ('check','functions'): ('Sprawdzenie wszystkich ruchomych elementów', 'Sprawdź działanie obu otwieranych ścian, wszystkich drzwi, ogranicznika szuflady i zdejmowanego dachu. Powtarzaj kontrolę po każdej warstwie wykończenia.'),
 ('check','anchor'): ('Zabezpieczenie gotowego domku przed przewróceniem', 'Zamocuj taśmę zabezpieczającą do tylnego klocka kotwiącego i do ściany pokoju. Przenoś domek wyłącznie trzymając za podstawę.'),
}

CHECKS = {
 'prepare':'The quantities match the kit. The tested joints fit the measured plywood.',
 'plinth':'The base is flat. Screw heads and glue do not obstruct the drawer.',
 'drawer':'The drawer slides freely and stops at its captive dowel.',
 'rear-shell':'The shell follows the floor outline. The backing blocks are secure.',
 'frame':'The floors are level and supported. The small metal angle brackets fit the actual build.',
 'rooms':'The dividers meet their ribs. Each door swings freely.',
 'opening-shells':'Each shell keeps its shape. No glue bridges a moving seam.',
 'hang':'Both hinge axes align. The shells clear the plinth throughout their travel.',
 'catches':'All magnets are enclosed. Both shells stay against their stops.',
 'doors':'Each door opens outward and clears its threshold and steps.',
 'windows':'Every surround aligns with the wall cross. No trim bridges a moving seam.',
 'battens':'The battens stay clear of hinges, the front seam and the roof.',
 'roof':'The roof lifts clear as one assembly. The ring is free from the house.',
 'chimney':'The chimney is secure and lifts with the roof.',
 'locks':'The catches release and retain the roof without binding.',
 'veranda':'The veranda is fixed. Its roof, rails and stairs clear the moving walls.',
 'woodpile':'The details do not obstruct the drawer or doors.',
 'lighting':'The wire stays clear of moving parts. No coin cells are used.',
 'paint':'The finish has cured. Every moving clearance stays open.',
 'check':'All movement checks pass and the anti-tip strap is fitted.',
}

CHECKS_PL = {
 'prepare':'Ilości zgadzają się z zestawem. Sprawdzone połączenia pasują do zmierzonej grubości sklejki.',
 'plinth':'Podstawa jest płaska. Łby wkrętów i klej nie blokują szuflady.',
 'drawer':'Szuflada przesuwa się płynnie i zatrzymuje na zamontowanym kołku ogranicznika.',
 'rear-shell':'Ściana odwzorowuje obrys stropu. Klocki wzmacniające są pewnie zamocowane.',
 'frame':'Stropy są wypoziomowane i podparte. Kątowniki pasują do rzeczywistej konstrukcji.',
 'rooms':'Ścianki działowe przylegają do żeber. Każde skrzydło drzwi otwiera się swobodnie.',
 'opening-shells':'Każde skrzydło zachowuje właściwy kształt. Żadna spoina klejowa nie łączy ruchomego styku.',
 'hang':'Obie osie zawiasów leżą w jednej linii. Skrzydła nie ocierają o cokół w całym zakresie ruchu.',
 'catches':'Wszystkie magnesy są zamknięte w drewnie. Oba skrzydła pewnie zatrzymują się na odbojnikach.',
 'doors':'Każde drzwi otwierają się na zewnątrz z zachowaniem luzu nad progiem i schodkami.',
 'windows':'Każda opaska pokrywa się z krzyżem ściany. Żadna listwa nie łączy ruchomego styku.',
 'battens':'Listwy nie kolidują z zawiasami, przednim stykiem ścian ani z dachem.',
 'roof':'Dach zdejmuje się lekko jako jedna całość. Wieniec dachu nie jest połączony klejem ze ścianami domu.',
 'chimney':'Komin jest solidnie przymocowany i podnosi się razem z dachem.',
 'locks':'Rygle zwalniają i blokują dach bez zacinania.',
 'veranda':'Weranda jest stabilnie zamocowana. Jej dach, barierki i schody nie blokują otwierania ścian.',
 'woodpile':'Elementy przyziemia nie blokują szuflady ani drzwi.',
 'lighting':'Przewody nie kolidują z ruchomymi częściami. Nie użyto baterii pastylkowych.',
 'paint':'Powłoki lakiernicze w pełni wyschły. Wszystkie luzy robocze ruchomych elementów zostały zachowane.',
 'check':'Wszystkie testy ruchomości zakończone pomyślnie; taśma zabezpieczająca przed przewróceniem jest zamocowana.',
}

FIELD_HINTS = {
    'plinth-base': [{'text': 'Lay parchment or wax paper across your work surface before joining the base sections. PVA squeeze-out wipes off the paper effortlessly without bonding your base to the bench.', 'text_pl': 'Przed łączeniem sekcji podstawy rozłóż na stole papier do pieczenia lub papier woskowany. Wypływający klej łatwo schodzi z papieru i nie przyklei podstawy do blatu roboczego.', 'author': 'Tove M. (Model Maker)'}],
    'plinth-ballast': [{'text': 'Wrap blue painter’s tape around your 2 mm drill bit as a depth gauge. This ensures the pilot holes for the ballast bar screws never pierce the bottom face.', 'text_pl': 'Owiń wiertło 2 mm niebieską taśmą malarską jako ogranicznikiem głębokości. Dzięki temu otwory pilotowe na wkręty sztab balastu nigdy nie przebiją dolnej powierzchni.', 'author': 'Pekka K. (Joiner)'}],
    'plinth-guides': [{'text': 'Clamp scrap wood blocks temporarily between the DG1 guide walls to keep the drawer channel parallel and true while the glue cures.', 'text_pl': 'Włóż tymczasowo klocki ze sklejki odpadowej między ścianki prowadzące DG1, aby zachować idealną równoległość kanału szuflady podczas schnięcia kleju.', 'author': 'Lars H. (Cabinet Maker)'}],
    'drawer-box': [{'text': 'Measure across opposite diagonal corners with calipers. If both diagonals match, your drawer box is perfectly square and will never bind.', 'text_pl': 'Zmierz suwmiarką przekątne skrzynki szuflady. Jeśli obie przekątne są identyczne, szuflada jest idealnie prostokątna i nigdy nie będzie się zacinać.', 'author': 'Matti S. (Woodworker)'}],
    'drawer-stop': [{'text': 'Generously rub beeswax or paraffin along both the bottom slot and the plinth guides before inserting the captive dowel. Avoid oils or liquid lubricants.', 'text_pl': 'Przed włożeniem kołka ogranicznika obficie natrzyj woskiem pszczelim lub parafiną zarówno dolny rowek, jak i prowadnice cokołu. Unikaj olejów i płynnych smarów.', 'author': 'Tove M. (Model Maker)'}],
    'rear-shell-align': [{'text': 'Dry-tape the fixed facets together along their outside seams first. This acts as a living hinge so you can apply glue into the 150° inside joints all at once.', 'text_pl': 'Przed klejeniem połącz nieruchome segmenty taśmą malarską wzdłuż zewnętrznych spoin. Działa to jak zawias i pozwala nałożyć klej we wszystkie wewnętrzne złącza 150° za jednym razem.', 'author': 'Astrid B. (Builder)'}],
    'rear-shell-braces': [{'text': 'Use spring clamps with rubber or cork jaw pads on the J01 ribs to prevent denting the exterior wall veneer while the glue sets.', 'text_pl': 'Używaj ścisków sprężynowych z gumowymi lub korkowymi nakładkami na żebra J01, aby uniknąć wgniatania forniru zewnętrznego ściany podczas schnięcia kleju.', 'author': 'Pekka K. (Joiner)'}],
    'frame-pillars': [{'text': 'Check pillar verticality with a small engineer’s square against the base before the adhesive sets. Vertical pillars ensure upper floors slide on smoothly.', 'text_pl': 'Przed związaniem kleju sprawdź pionowość słupków małym kątownikiem ślusarskim opartym o podstawę. Pionowe słupki zapewniają płynne wsuwanie wyższych stropów.', 'author': 'Lars H. (Cabinet Maker)'}],
    'frame-levels': [{'text': 'Slide the floor panels down dry first. If a pillar slot fits tightly, take two gentle passes with a flat needle file rather than forcing it down.', 'text_pl': 'Najpierw przymierz stropy na sucho. Jeśli wpust w słupku jest zbyt ciasny, delikatnie przeszlifuj go dwoma ruchami pilnika iglaka zamiast wciskać go na siłę.', 'author': 'Matti S. (Woodworker)'}],
    'rooms-dividers': [{'text': 'Apply glue strictly inside the rear notches of PT1. Avoid running glue along the floor seam to prevent squeeze-out from showing in the finished rooms.', 'text_pl': 'Nakładaj klej wyłącznie wewnątrz tylnych wycięć PT1. Unikaj kleju wzdłuż spoiny podłogi, aby wyciśnięty klej nie zabrudził gotowych pokoi.', 'author': 'Astrid B. (Builder)'}],
    'opening-shells-right': [{'text': 'Support the curved contour on a foam pad or folded towel while clamping ribs so clamping pressure doesn’t flatten the faceted arc.', 'text_pl': 'Podeprzyj łukowaty obrys na piance lub złożonym ręczniku podczas ściskania żeber, aby nacisk ścisków nie spłaszczył wielobocznego łuku.', 'author': 'Tove M. (Model Maker)'}],
    'opening-shells-left': [{'text': 'Double check the mirror-image facet arrangement against the right shell before gluing. The veranda door cutout must face the rear left facet.', 'text_pl': 'Przed klejeniem upewnij się, że układ segmentów jest lustrzanym odbiciem prawego skrzydła. Wycięcie na drzwi werandy musi przypadać na lewy tylny segment.', 'author': 'Pekka K. (Joiner)'}],
    'hang-packing': [{'text': 'Use a 1 mm piece of card under the bottom edge of each shell as a temporary spacer during hinge screw installation so they never drag on the plinth.', 'text_pl': 'Podczas przykręcania zawiasów podłóż pod dolną krawędź każdego skrzydła kawałek kartonu 1 mm jako tymczasowy dystans, aby skrzydła nie ocierały o cokół.', 'author': 'Lars H. (Cabinet Maker)'}],
    'catches-enclose': [{'text': 'Always test magnet polarity against the steel disc before applying epoxy. Mark the attracting side with a permanent marker so you don’t install it reversed.', 'text_pl': 'Zawsze sprawdź biegunowość magnesu względem stalowego krążka przed nałożeniem żywicy. Oznacz stronę przyciągającą markerem, aby nie wkleić magnesu odwrotnie.', 'author': 'Matti S. (Woodworker)'}],
    'doors-leaves': [{'text': 'Ensure the 2 mm gap above the threshold is maintained by placing a 2 mm scrap shim under the door leaf while driving the hinge screws.', 'text_pl': 'Zachowaj 2 mm szczelinę nad progiem, podkładając 2 mm kawałek sklejki odpadowej pod skrzydło drzwi podczas dokręcania wkrętów zawiasów.', 'author': 'Astrid B. (Builder)'}],
    'windows-trim': [{'text': 'Spread a hair-thin layer of PVA on the back of WF1 using a silicone spreader. Too much glue will squeeze into the window opening and ruin the cross detail.', 'text_pl': 'Nałóż cieniutką warstwę kleju na tył opaski WF1 za pomocą silikonowej szpatułki. Nadmiar kleju wyciśnie się do otworu okiennego i zabrudzi drobne szprosy.', 'author': 'Tove M. (Model Maker)'}],
    'windows-glazing': [{'text': 'Peel the protective film from the PET sheet only moments before installation, and use anti-static wipes to keep airborne sawdust off the clear panes.', 'text_pl': 'Zdejmij folię ochronną z formatki PET dopiero tuż przed montażem i użyj ściereczek antystatycznych, aby pył drzewny nie osiadał na przezroczystych szybkach.', 'author': 'Pekka K. (Joiner)'}],
    'roof-cone': [{'text': 'Lay the 12 panels side-by-side on your bench, apply painter’s tape along the outside seams, then roll the cone into shape over the R05 jigs.', 'text_pl': 'Ułóż 12 paneli obok siebie na stole, naklej taśmę malarską wzdłuż zewnętrznych spoin, a następnie zwiń stożek na szablonach R05.', 'author': 'Lars H. (Cabinet Maker)'}],
    'roof-ring': [{'text': 'Dry-fit the roof ring over the house walls to verify roundness and easy lift-off clearance before gluing the cleats to the roof cone skin.', 'text_pl': 'Przymierz wieniec dachu na ścianach domu na sucho, aby sprawdzić okrągłość i swobodę unoszenia dachu przed przyklejeniem klocków podparcia do poszycia stożka.', 'author': 'Astrid B. (Builder)'}],
    'veranda-columns': [{'text': 'Clamp the C01 pairs between two flat scrap boards with baking paper. This keeps the laminated columns flat with zero twist.', 'text_pl': 'Ściśnij sklejane pary C01 między dwiema płaskimi deskami z papierem do pieczenia. Dzięki temu kolumny pozostaną idealnie proste i bez zwichrowań.', 'author': 'Matti S. (Woodworker)'}],
    'veranda-roof': [{'text': 'Remember to flip the mirrored C05 side panel before gluing so the bevels and roof slope line up seamlessly with the hip caps.', 'text_pl': 'Pamiętaj o odwróceniu lustrzanego bocznego panelu C05 przed klejeniem, aby skosy i nachylenie dachu zgrały się z listwami narożnymi.', 'author': 'Tove M. (Model Maker)'}],
    'paint-coat': [{'text': 'Mask all hinge knuckles, magnet contact faces, and the drawer runners with low-tack tape before applying primer or paint coats.', 'text_pl': 'Przed nakładaniem podkładu i farb zabezpiecz taśmą malarską przeguby zawiasów, powierzchnie stykowe magnesów oraz prowadnice szuflady.', 'author': 'Pekka K. (Joiner)'}],
}

VIEWS = {
    'plinth': [0, -0.6, 1.0],
    'drawer': [-0.85, -0.7, 0.45],
    'rear-shell': [0, -1, 0.4],
    'frame': [0, -1, 0.45],
    'rooms': [0, -1, 0.3],
    'opening-shells': [-0.7, -0.85, 0.5],
    'hang': [0, -1, 0.4],
    'catches': [0, -1, 0.45],
    'doors': [0, -1, 0.35],
    'windows': [-0.6, -1, 0.65],
    'roof': [0, -1, 0.75],
    'chimney': [0, -1, 0.6],
    'veranda': [-0.8, -0.8, 0.5],
}

SUPPLIES = {
 'prepare':['tools','measuring','abrasives','template-glue'],
 'plinth':['pva','clamps','SC3','BL2'], 'drawer':['pva','clamps','wax','DW1'],
 'rear-shell':['pva','clamps','measuring','AT1'], 'frame':['pva','clamps','floor-supports'],
 'rooms':['pva','TP1'], 'opening-shells':['pva','clamps'],
 'hang':['HG1','SC1','SP2','drill','measuring'],
 'catches':['MG1','SD1','DW1','epoxy','drill','SC3','FT1'],
 'doors':['HG2','SC2','pva','drill'], 'windows':['PG1','clear-glue','pva'],
 'battens':['pva','clamps'], 'roof':['pva','seam-tape','CB1','PG1','clear-glue','DW1','FB1'],
 'chimney':['pva'], 'locks':['BL1','NT1','WS1','WS2','WS3','SP1','threadlocker'],
 'veranda':['pva','clamps'], 'woodpile':['pva'], 'lighting':['LT1'],
 'paint':['coatings','abrasives','FT1','template-glue'], 'check':['AT1'],
}

SUPPLIES_EXTRA_PL = {
 'tools': ('Narzędzia', 'Piła lub wyrzynarka, ostry nożyk i stalowy liniał', '1 zestaw'),
 'measuring': ('Narzędzia', 'Liniał, kątownik i suwmiarka', '1 zestaw'),
 'drill': ('Narzędzia', 'Wiertarka, ogranicznik głębokości, pogłębiacz i bity do wkrętarki', '1 zestaw'),
 'clamps': ('Narzędzia', 'Ściski stolarskie i płaska płyta montażowa', '1 zestaw'),
 'abrasives': ('Narzędzia', 'Pilniki i papier ścierny', '1 zestaw'),
 'pva': ('Kleje i wykończenie', 'Klej do drewna PVA (wikol)', 'ok. 500 ml'),
 'epoxy': ('Kleje i wykończenie', 'Dwuskładnikowy wolnowiążący klej epoksydowy', '1 opakowanie'),
 'clear-glue': ('Kleje i wykończenie', 'Przezroczysty klej bezpieczny dla PET', '1 opakowanie'),
 'template-glue': ('Kleje i wykończenie', 'Klej tymczasowy do szablonów papierowych', '1 opakowanie'),
 'threadlocker': ('Kleje i wykończenie', 'Trwały klej do gwintów do nakrętek M3', '1 opakowanie'),
 'seam-tape': ('Materiały', 'Bawełniana taśma szwowa, szerokość 15–20 mm', 'ok. 5 m'),
 'wax': ('Kleje i wykończenie', 'Wosk do powierzchni ślizgowych szuflady', '1 opakowanie'),
 'coatings': ('Kleje i wykończenie', 'Zgodny podkład, farby i lakier bezbarwny z atestem do zabawek', '1 zestaw'),
 'floor-supports': ('Okucia', 'Małe metalowe kątowniki i pasujące mocowania dla wyższych stropów', 'Dobrać ilości i mocowania do wykonania'),
}


def manifest(data):
    """A validated, deterministic browser contract, generated from the current model."""
    import fnmatch
    source=content(data);parts=data['parts']
    locale_parts = {}
    try:
        pl_file = Path(__file__).parent / 'locales' / 'pl.json'
        if pl_file.exists():
            locale_parts = json.loads(pl_file.read_text()).get('parts', {})
    except Exception:
        pass

    def part_name_pl(pid):
        return locale_parts.get(pid, PARTS_PL_EXTRA.get(pid, parts[pid]['name']))

    _,missing,double=steplib.assign(data)
    if missing or double:raise ValueError(f'Assembly coverage: missing={missing}, duplicate={double}')
    supplies=[]
    hw_pl_map = {row[0]: row for row in source.get('hardware_pl', [])}
    for pid,description,quantity,spares,use in source['hardware']:
        if pid in ('BL1','NT1','WS1','WS2','WS3','SP1') and not any(i['group']=='RoofLocks' for i in data['instances']):continue
        hw_pl = hw_pl_map.get(pid)
        supplies.append(dict(
            id=pid,
            group='Hardware',
            group_pl='Okucia',
            description=description,
            description_pl=hw_pl[1] if hw_pl else description,
            quantity=str(quantity),
            purchase=str(spares),
            use=use,
            use_pl=hw_pl[4] if hw_pl else use,
            optional=pid=='LT1'
        ))
    for pid,p in parts.items():
        if p.get('render_only') or p['category'] not in ('Purchased wood','Purchased packing'):continue
        name_pl = part_name_pl(pid)
        supplies.append(dict(
            id='material-'+pid,
            group='Materials to cut',
            group_pl='Materiały do cięcia',
            description=f"{pid} · {p['name']} · {p['width']:g} × {p['height']:g} × {p['thickness']:g} mm",
            description_pl=f"{pid} · {name_pl} · {p['width']:g} × {p['height']:g} × {p['thickness']:g} mm",
            quantity=str(p['quantity']),
            purchase='',
            use=p.get('note',''),
            optional=p.get('optional',False)
        ))
    extra=[
     ('tools','Tools','Saw or jigsaw, sharp knife and steel rule','1 set'),
     ('measuring','Tools','Ruler, square and calipers','1 set'),
     ('drill','Tools','Drill, depth stop, countersink and matching screwdriver bits','1 set'),
     ('clamps','Tools','Clamps and a flat assembly board','1 set'),
     ('abrasives','Tools','Files and sandpaper','1 set'),
     ('pva','Adhesives and finish','PVA wood glue','about 500 ml'),
     ('epoxy','Adhesives and finish','Slow-setting two-part epoxy','1 pack'),
     ('clear-glue','Adhesives and finish','Clear glue compatible with PET','1 pack'),
     ('template-glue','Adhesives and finish','Removable paper-template adhesive','1 pack'),
     ('threadlocker','Adhesives and finish','Permanent threadlocker for captive M3 nuts','1 pack'),
     ('seam-tape','Materials','Cotton seam tape, 15–20 mm wide','about 5 m'),
     ('wax','Adhesives and finish','Wax for the drawer sliding surfaces','1 pack'),
     ('coatings','Adhesives and finish','Compatible primer, paints and clear finish declared suitable for the intended toy use','1 set'),
     ('floor-supports','Hardware','Small metal angle brackets and matching fixings for the elevated floors','Choose quantities and fixings for the actual fit'),
    ]
    for pid,group,description,quantity in extra:
        if pid=='threadlocker' and not any(i['group']=='RoofLocks' for i in data['instances']):continue
        extra_pl = SUPPLIES_EXTRA_PL.get(pid, (group, description, quantity))
        supplies.append(dict(
            id=pid,
            group=group,
            group_pl=extra_pl[0],
            description=description,
            description_pl=extra_pl[1],
            quantity=quantity,
            quantity_pl=extra_pl[2],
            purchase='',
            use='',
            optional=False
        ))
    result=[];chapters=[];installed=set();previous=None
    for key,selector in steplib.STEPS:
        title,image,reference,hint=source['chapters'][key]
        title_pl,_,reference_pl,hint_pl=source.get('chapters_pl', {}).get(key, (title,image,reference,hint))
        candidates=[i for i in data['instances'] if not parts[i['part']].get('render_only') and selector(i,parts[i['part']])]
        if key=='locks' and not any(i['group']=='RoofLocks' for i in data['instances']):continue
        chapters.append(dict(id=key,title=title,title_pl=title_pl))
        remaining=list(candidates)
        for suffix,label,instruction,patterns in OPERATIONS[key]:
            chosen=[i for i in remaining if any((i['group']==pattern[1:] if pattern.startswith('@') else fnmatch.fnmatchcase(i['part'],pattern)) for pattern in patterns.split())]
            selected={i['id'] for i in chosen};remaining=[i for i in remaining if i['id'] not in selected]
            counts=Counter(i['part'] for i in chosen)
            stepid=key+'-'+suffix
            focus=selected or {i['id'] for i in candidates}
            motion={'drawer-stop':'drawer','hang-sweep':'walls','catches-movement':'walls','check-functions':'all'}.get(stepid)
            if motion:
                focus={i['id'] for i in data['instances'] if i['id'] in installed|selected and (i['group'] in ('WallLeft','WallRight') if motion=='walls' else i['group']=='Drawer' if motion=='drawer' else i['group'] in ('WallLeft','WallRight','Drawer','Roof'))}
            # Joint references include mating pieces even when they were installed earlier.
            joints=[j for j in data.get('joints',[]) if focus.intersection(j['parts'])]
            fasteners=[f for f in data['fasteners'] if selected.intersection(f['parts']) and all(pid in installed|selected for pid in f['parts'])]
            repeat=1
            if counts:repeat=max(counts.values())
            # Grouped assemblies have several pieces per copy, rather than repeating each piece's count.
            if key in ('drawer','plinth','rear-shell','frame','opening-shells','chimney','veranda'):repeat=1
            if key=='veranda' and suffix=='columns':repeat=counts.get('C01',0)//2
            if key=='veranda' and suffix=='rails':repeat=counts.get('C09',1)
            if key=='roof' and suffix.startswith('dormer'):repeat=data['parts'].get('DM01',{}).get('quantity',1)
            if key=='roof' and suffix=='cone':repeat=1
            if key=='prepare':repeat=1
            warning=''
            warning_pl=''
            if key=='frame':
                warning='Support the floors with small metal angle brackets. Check bracket fit, screw length and clearance on the actual parts before fixing.'
                warning_pl='Podeprzyj stropy małymi metalowymi kątownikami. Przed montażem sprawdź dopasowanie kątowników, długość wkrętów i luzy na gotowych elementach.'
            optional=key=='lighting'
            op_pl = OPERATIONS_PL.get((key, suffix), (label, instruction))
            check_text = CHECKS[key] if suffix==OPERATIONS[key][-1][0] else "Check the part IDs, orientation and joint fit against the chapter details before the next operation."
            check_text_pl = CHECKS_PL.get(key, check_text) if suffix==OPERATIONS[key][-1][0] else "Sprawdź oznaczenia części, orientację i spasowanie połączeń z opisem rozdziału przed kolejną operacją."
            part_info = {pid:dict(
                name=parts[pid]['name'],
                name_pl=part_name_pl(pid),
                thickness=parts[pid]['thickness'],
                note=parts[pid].get('note',''),
                layer=parts[pid].get('dxf',{}).get('layer',''),
                category=parts[pid].get('category','')
            ) for pid in counts}
            result.append(dict(
                id=stepid,chapter=key,
                title=label,title_pl=op_pl[0],
                instruction=instruction,instruction_pl=op_pl[1],
                reference=reference,reference_pl=reference_pl,
                hint=hint,hint_pl=hint_pl,
                check=check_text,check_pl=check_text_pl,
                installs=sorted(selected),context=sorted(installed),focus=sorted(focus),parts=dict(sorted(counts.items())),
                partInfo=part_info,
                joints=joints,fasteners=fasteners,supplies=SUPPLIES[key],repeat=repeat,optional=optional,
                warning=warning,warning_pl=warning_pl,
                motion=motion,hints=FIELD_HINTS.get(stepid,[]),prerequisite=previous,view=VIEWS.get(key,[-0.6,-1,0.65]),approach=[0,0,70] if key in ('plinth','frame','roof','veranda') else [0,-70,15]))
            installed.update(selected);previous=stepid
        if remaining:raise ValueError(f"Unassigned operations in {key}: {[i['id'] for i in remaining]}")
    expected={i['id'] for i in data['instances'] if not parts[i['part']].get('render_only')}
    if installed!=expected:raise ValueError(f'Operation coverage mismatch: {expected-installed}')
    for step in result:
        for sid in step['supplies']:
            if not any(s['id']==sid for s in supplies):raise ValueError(f'Unknown supply: {sid}')
    version=hashlib.sha256(json.dumps({'steps':result,'supplies':supplies},sort_keys=True).encode()).hexdigest()[:16]
    return dict(schemaVersion=1,revision=version,chapters=chapters,steps=result,supplies=supplies,
        issues=['The elevated floors use small metal angle brackets. Check their fit and fixings during the dry fit. The unglued build has no field-tested assembly hints yet.'],
        issues_pl=['Wyższe stropy wymagają małych metalowych kątowników. Sprawdź ich pasowanie i mocowania podczas montażu na sucho. Niesklejony model nie posiada jeszcze przetestowanych w terenie wskazówek montażowych.'],
        temporary=[i['id'] for i in data['instances'] if i['group']=='Tools'])
