"""Model-derived instructions and purchasing list shared by the book and web companion.

This module does not import PDF, CAD or generated files.
"""
from collections import Counter
import hashlib
import json
import steps as steplib


def content(data):
    DATA=data;P=data['parts'];CFG=data['config'];DER=data['derived']
    DOORS=CFG['doors'];VER=CFG['veranda'];VER_FACET=int(VER['facet'][1:])-1
    TOPS=DER['floor_tops'];G0=TOPS[0];PITCH=CFG['floor_pitch'];EAVE=DER['roof_eave']
    GUSSETS=(26*CFG['wall_height']/450,PITCH-CFG['thickness']['floor']-20*CFG['wall_height']/450)
    HINGES=[G0+c for c in CFG['wall_hinge']['centers']];DRAWER=CFG['plinth']['drawer']
    MAG,CATCH,STOP=CFG['magnets'],CFG['wall_catch'],CFG['wall_stop'];OPEN=DER['views']['open_angle'];SIDE=DER['drawer']['side']
    BL1=next((f for f in DATA['fasteners'] if f['type']=='BL1'),None);SC1=next(f for f in DATA['fasteners'] if f['type']=='SC1')
    WS1=(1+len(BL1['stack_mm'])-8) if BL1 else 0;LOCK=(P.get('E08',{}).get('thickness',0)+P.get('E09',{}).get('thickness',0));PT=P['P01']['thickness']
    STOPWALLS=' and '.join(k for k,v in P.items() if any('garden stop' in h['purpose'] for h in v['holes']))
    CATCHHOLES=' and '.join(f"{pid}/{h['id']}" for pid,p in P.items() if p.get('assembly_panel')=='F02' for h in p['holes'] if 'catch' in h['purpose'])
    FACETS=DER['facets']
    def zl(values):return ', '.join(f'Z{v:g}' for v in values[:-1])+f' and Z{values[-1]:g}'
    def facet_ref(i):
        f=FACETS[i];return f['part']+(f' (facet {i+1})' if sum(g['part']==f['part'] for g in FACETS)>1 else '')
    def shell(group):return [f['part'] for f in FACETS if f['group']==group]

    def hardware_rows():
        counts=Counter(f['type'] for f in DATA['fasteners']);kinds=Counter(h['kind'] for h in DATA['hardware'])
        WH,DH=CFG['wall_hinge'],CFG['door_hinge'];sd,sl=DH['screw'];doors=kinds['Door butt hinge']//2;fin=CFG['finial']
        magnets=kinds['Catch magnet']+kinds['Stop magnet'];ST=CFG['stability'];bars=ST['ballast'][0]
        return [
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

    vd,md,bd=DOORS['veranda'],DOORS['main'],DOORS['back'];wpf=DER['windows_per_floor'];bal=P['C09']['quantity']
    pl=CFG['plinth'];bt=DRAWER['travel'];st=CFG['stairs'];sd,sl=CFG['door_hinge']['screw'];dmr=CFG['dormer']
    gap=CFG['partition']['front_gap']
    divider_end=f'{gap:g} mm short of the front seam' if gap>0 else 'the front seam'
    divider_gap_note=(f"The {gap:g} mm front gap is wider than a child's finger (5-12 mm gaps pinch)."
                      if gap>0 else 'The divider reaches the front seam with no pinch gap.')
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
    # The roof attachment is a builder preference, not installed hardware in this model.
    if not any(i['group']=='RoofLocks' for i in DATA['instances']):
        roof=texts['roof'];texts['roof']=(*roof[:3],roof[3]+' Optional roof attachment: leave it removable, use magnets, or make a hinge-style connection. Check the actual fit and opening clearance first.')
        check=texts['check'];texts['check']=(check[0],check[1],check[2].replace('rotate the roof catches inward, and ', '').replace('rotate the catches outward and ', ''),check[3])
        texts['locks']=('Optional roof attachment','roof','The roof can remain removable. Magnets or a hinge-style attachment are optional builder choices.','Check the fit and opening clearance with the actual hardware before making a permanent connection.')
    hardware=hardware_rows()
    if not any(i['group']=='RoofLocks' for i in DATA['instances']):
        hardware=[row for row in hardware if row[0] not in ('BL1','NT1','WS1','WS2','WS3','SP1')]
    return {'chapters':texts,'hardware':hardware}

# Explicit operation boundaries. Patterns refer to part IDs, not array positions.
# Parts are installed once; later inspection steps reference them without reinstalling them.
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

FIELD_HINTS = {}  # Stable step ID -> [{"text": verified field note, "author": optional attribution}].

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


def manifest(data):
    """A validated, deterministic browser contract, generated from the current model."""
    import fnmatch
    source=content(data);parts=data['parts']
    _,missing,double=steplib.assign(data)
    if missing or double:raise ValueError(f'Assembly coverage: missing={missing}, duplicate={double}')
    supplies=[]
    for pid,description,quantity,spares,use in source['hardware']:
        if pid in ('BL1','NT1','WS1','WS2','WS3','SP1') and not any(i['group']=='RoofLocks' for i in data['instances']):continue
        supplies.append(dict(id=pid,group='Hardware',description=description,quantity=str(quantity),purchase=str(spares),use=use,optional=pid=='LT1'))
    for pid,p in parts.items():
        if p.get('render_only') or p['category'] not in ('Purchased wood','Purchased packing'):continue
        supplies.append(dict(id='material-'+pid,group='Materials to cut',description=f"{pid} · {p['name']} · {p['width']:g} × {p['height']:g} × {p['thickness']:g} mm",quantity=str(p['quantity']),purchase='',use=p.get('note',''),optional=p.get('optional',False)))
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
        supplies.append(dict(id=pid,group=group,description=description,quantity=quantity,purchase='',use='',optional=False))
    result=[];chapters=[];installed=set();previous=None
    for key,selector in steplib.STEPS:
        title,image,reference,hint=source['chapters'][key]
        candidates=[i for i in data['instances'] if not parts[i['part']].get('render_only') and selector(i,parts[i['part']])]
        if key=='locks' and not any(i['group']=='RoofLocks' for i in data['instances']):continue
        chapters.append(dict(id=key,title=title))
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
            if key=='frame':warning='Support the floors with small metal angle brackets. Check bracket fit, screw length and clearance on the actual parts before fixing.'
            optional=key=='lighting'
            result.append(dict(id=stepid,chapter=key,title=label,instruction=instruction,reference=reference,hint=hint,check=CHECKS[key] if suffix==OPERATIONS[key][-1][0] else "Check the part IDs, orientation and joint fit against the chapter details before the next operation.",
                installs=sorted(selected),context=sorted(installed),focus=sorted(focus),parts=dict(sorted(counts.items())),
                partInfo={pid:dict(name=parts[pid]['name'],thickness=parts[pid]['thickness'],note=parts[pid].get('note','')) for pid in counts},
                joints=joints,fasteners=fasteners,supplies=SUPPLIES[key],repeat=repeat,optional=optional,warning=warning,
                motion=motion,hints=FIELD_HINTS.get(stepid,[]),prerequisite=previous,approach=[0,0,70] if key in ('plinth','frame','roof','veranda') else [0,-70,15]))
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
        temporary=[i['id'] for i in data['instances'] if i['group']=='Tools'])
