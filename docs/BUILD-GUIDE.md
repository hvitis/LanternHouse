# Build guide

This guide is for the person with the jigsaw. It explains what you are building, how to print and cut it, what to buy and how it goes together.

Every file it mentions under `output/` is **generated**: it is not in the repository. Run the build first (see [Generate the build files](../README.md#generate-the-build-files) in the README). Paths are relative to the repository root. All dimensions are in millimetres.

## What you are building

A plywood house with the dimensions listed in the generated table below. It has three main floors, an attic under a steep cone roof with a ball finial and two dormers, opening front walls, a permanent veranda, a stone plinth with a hidden drawer, and a round base. The tower uses twelve flat facets so it can be built with a jigsaw.

The ground floor has five windows, the middle and bedroom floors have six each, and the attic has two dormer windows: one over W06, beside the veranda and next to the chimney, and one over W12 on the opposite side, above the main door. Both sit just above the eave cleats, each inside one roof panel. Every window keeps a solid cross of wall between four panes, with a one-piece cream surround and clear PET glazing. The veranda has a 149.3 × 84 deck and stands on the fixed back-left facet W07, so it never has to be removed: both front walls swing open past it. It has:

- a red hipped roof with hip and ridge caps;
- shaped cream columns;
- a front railing and an angled side railing with balusters;
- side steps.

Its door opens outward onto the deck. The main entrance on W12 has a separate small gabled canopy.

The house stands on a 61.6 mm stone plinth on a 6 mm base, with the floor levels listed below. A drawer hidden in the plinth is about 46 mm deep inside and slides 200 mm out to the back-right, where a dowel in its bottom slot stops it; its front is two stone plinth panels with a finger notch underneath. Each storey has one room divider with a 38 × 93.3 doorway at its front end, reaching the edge of the floors to the opening walls, with a 3 mm door leaf on cotton-tape hinges. The two front wall shells hang 1 mm above the plinth, click shut on wall catches under the attic floor and stop at 100° against two small garden posts on the base; the four magnets are sealed inside hardwood. Six thermo-clay (oven-hardening polymer clay) figures live in the house: Moominmamma and Snufkin on the ground floor, Moominpappa and the Snork Maiden in the living room, Moomintroll in the bedrooms and Little My in the attic. The veranda deck is level with the ground floor, on a blue skirt with a 4-step side stair, and a rope ladder runs from its roof to the eave beside the dormer. The main entrance and the back door (W09, kitchen side, with a lean-to canopy and a woodpile beside it) have 4 stone steps each. All three doors open outward.

The F01 floors have four pillar openings each. There are no stairs inside. Play access is through the opening walls and the lift-off roof. The furniture appears in the 3D viewer and renders only. It has no CAD plans, printouts or cutting sheets.

## Open these files first

| File | Contents |
| --- | --- |
| `output/pdf/Moomin-House-Complete.pdf` | Cover, clickable contents, dimensioned plan, clay figures, hardware shopping list, illustrated instructions, dimensioned parts, full-size cutting printouts, decor, clay family and the supplier appendix at the end. Use the contents for page numbers. |
| `output/pdf/Moomin-House-Instructions.pdf` | Assembly sequence, screw sections, hinge axes, glue joints, tools and workshop hints |
| `output/pdf/Moomin-House-Cutting-Templates.pdf` | Calibration page, packed sheet layouts, overlapping A4 tiles, white 3 mm template headers and solid wood templates |
| `output/pdf/Moomin-House-3mm-Hand-Templates.pdf` | House 3 mm parts only. Each large part uses two A4 pages with a 10 mm overlap. |
| `output/pdf/Moomin-House-Supplier.pdf` | Polish specification, inventory, reference maps, and clean A3 production pages grouped by thickness and operation. Separate from the A4 complete book. |
| `output/Moomin-House-Supplier-Cut.dxf` | Everything the supplier cuts in one DXF R12 file (mm, 1:1): closed outlines, openings and through holes, one layer and colour per thickness, no frames or text. Blind pockets and holes are not in it. |
| `output/pdf/Moomin-House-Dimensioned-Parts.pdf` | House part inventory with page numbers; every profile dimensioned, several scaled references per page; hole diameter, depth and local coordinates; hinge checking templates |
| `output/pdf/Moomin-House-Decor.pdf` | Paint palette, stone plinth panels, and fish-scale roof shingle strips cut one course at a time so they wrap the 12-facet roof |
| `output/pdf/Moomin-House-Clay-Family.pdf` | Instructions for the clay family |
| `output/cad/MoominHouse.FCStd` | Editable native FreeCAD document: colored assembly, construction profiles, screw solids and glue/axis guides |
| `output/cad/MoominHouse.step` | Closed house as solids, without furniture |
| `output/cad/MoominHouse-open.step` | Walls opened to the 100° stop posts and roof lifted; the veranda stays in place |
| `output/cad/MoominHouse-exploded.step` | Separated structural assemblies |
| `output/cad/parts/` | Individual solid STEP files |
| `output/dxf/` | Millimetre DXF profiles, A3 sheet maps, and separate CNC operation files for all plywood thicknesses (`PLY*-cnc-*.dxf`, `.svg`). |
| `output/previews/` | CAD-derived closed (front and veranda side), open, furnished and assembly illustrations, each with a projection sidecar (`.json`); `clay-*.png` are the clay Moomin renders (front, side, back, three-quarter) |
| `output/reports/parts.csv`, `hardware.csv`, `stock.csv` | Spreadsheet shopping and cutting lists |
| `output/reports/template-index.json` | Template page ranges and tile row/column counts, per PDF |
| `output/reports/release-validation.json` | Automated checks for the delivered files |
| `output/reports/thickness-tolerance.json` | The house rebuilt with the thinnest and thickest measured plywood (`make tolerance`) |
| `output/Moomin-House-Build-Kit.zip` | Portable package of the complete project |

## Main dimensions

<!-- specifications:start -->
| Specification | Value |
| --- | --- |
| Finished height | 778.4 mm |
| Base diameter / plywood | 522.7 mm / 6 mm |
| Plinth height | 61.6 mm |
| Tower diameter / wall plywood | 326.7 mm / 3 mm |
| Fixed / opening wall height | 420 mm / 418 mm |
| Floor plywood / floor tops | 6 mm / Z73.6, Z213.6, Z353.6, Z493.6 |
| Clear room height | 134 mm |
| Pillars: quantity / section / length | 4 / 6 × 16.8 mm / 402 mm |
| Pillar slot clearance | 0.6 mm |
| Roof diameter / eave height | 373.3 mm / Z493.6 |
| Roof ring: sections / plywood | 3 / 3 mm |
| Base sections | 8 |
| Veranda deck / facet | 149.3 × 84 mm / W07 |
| Drawer travel | 200 mm |
| Opening wall stop | 100° |
| Floor support strips: ground / upper | 3 × 4 mm / 3 × 12 mm |
| Floor joint clearance | 0.1 mm |
<!-- specifications:end -->

These are the values for the default `source/config.json`. The book and the 3D viewer always show the values for your current config.

## Print and cut

Print the cutting-template calibration page at **100% / Actual size**, single-sided on A4.

1. Turn off Fit, Shrink and borderless enlargement.
2. Measure the 100 mm square in both directions. The permitted print error is at most 0.5 mm.
3. Repeat the calibration whenever your settings or printer change.

Every 1:1 paper template carries a 100 mm reference bar, so you can re-check the scale on the page you are about to glue down. That covers template tiles, solid-wood outlines, hinge checking templates, stone panels and shingle strips. Supplier production pages contain cutting paths only; their PDF page dimensions define the physical sheet size.

The dimensioned reference pages are scaled illustrations, several per page, so cut from the separate cutting templates.

Interior pages have white backgrounds for economical printing. CAD diagrams have transparent backgrounds, and tables use thin lines without colored row fills. The cover, model colors and printable textures keep their original colors.

**Tiles**
- Each plywood sheet has an overview followed by every tile it needs. Row 1 is the bottom row.
- Tiles cover 190 × 260 mm with 10 mm overlap. Match repeated crosshairs and long contour lines.
- Tiles with no cut line or hole are not printed. Each sheet overview shows the tile map with those tiles greyed out.
- Tape the joins on the back, then apply removable paper adhesive to the wood.
- Use the template index to print a single sheet at a time.

**Cutting**
- Identical pieces share one build ID on the templates and in the viewer. All 22 three-wall corner ribs use `J01`. The inventory gives the total quantity for each ID. Parts with different holes, openings or thicknesses have different IDs.
- Label each piece with its build ID. Sort the pieces by ID before assembly.
- The laser layout keeps at least 3 mm between profiles and 10 mm side margins. Long parts use the end allowances on their reference maps.
- Every plywood sheet is grade 2/2 birch, in 3 or 6 mm.
- Router or jigsaw cutting requires wider lanes and new nesting.
- Cut openings while the sheet is still intact.
- Drill the S-marked starter holes in waste, insert the jigsaw blade there, and finish sharp corners with a precise file. H-marked holes stay in the finished part.
- Use a drill stop for blind holes and follow the marked entry face. Every hole schedule gives the diameter and coordinates from the local lower-left datum.
- Cut the round base with a jigsaw or a router trammel, then sand the edge fair.

- Save window and roof-ring offcuts for clamping pads and painting samples.

**A3 CNC sheets and A4 hand templates**

All plywood stock has the A3 dimensions 297 × 420 mm and only two thicknesses, 3 and 6 mm, on separate sheets. The tower walls, corner ribs, room dividers, doors, railings, drawer bottom, veranda deck, skirts, headers, roof crossframe and seam strips are 3 mm; the floors, base, plinth, pillars and the supports under the base are 6 mm. Fixed walls retain the supplied end edges. Moving walls have 1 mm end allowances. P01 pillars have 5 mm end margins. Other parts use 10 mm margins.

1. Send `Moomin-House-Supplier.pdf` and `Moomin-House-Supplier-Cut.dxf` (everything to cut, in one file) to the company. Both come with every release, or from `make build`; `make cutfile` rewrites the DXF from the last build's nesting. A shop that machines blind pockets also needs the operation CSV, DXF and SVG files.
2. Use the operation schedule to identify each production page.
3. Confirm cutter sizes, hold-down, corner relief, compensation, and tolerances with the company.
4. Confirm registration before machining the underside of a sheet.
5. Compare delivered parts with the reference maps before assembly.

Production pages contain unfilled vector paths without labels or backgrounds. Each page represents one machining operation. Operation names identify the face, diameter, and depth. The company applies cutter compensation once. These files contain nominal geometry, not machine-specific toolpaths.

For DIY work, use `Moomin-House-Cutting-Templates.pdf`. Large individual parts use two A4 pages with 10 mm overlap. Some pages use landscape orientation. Print at 100% without automatic scaling. The separate 3 mm template PDF contains only thin parts. Use the dimensioned drawings for drilling faces and depths.

The complete book contains an A4 supplier summary. The A3 production pages remain in the separate supplier PDF. Supplier text is Polish by default. `--lang en` selects English without changing the machining geometry.

**Roof shingle strips (decor PDF)**
- The roof is a cone of 12 flat panels, so a straight strip cannot follow a level course. Each strip is one course unrolled flat: it bends at the hips, where you crease it on the dotted line, and its ends are cut along the hips.
- Low courses are split into strips of one or two panels; near the top a single strip wraps the whole roof. The dormer and chimney holes are printed on the strips that meet them.
- Number the roof panels 1–12 in pencil, starting with the first dormer panel R06 and counting to the right. The mark in each strip's hidden glue band (for example 7·3) is course 7 on panel 3. Start at the eave and glue only the top 5 mm band; each course goes 9 mm higher, its tile tips on the dark line of the course below.

## Stock and hardware

The stock tables below are regenerated from `output/nesting.json` on every build. The default config assumes five 400 × 600 × 6 sheets you already own (`stock.main.6` with `"existing": true` in `source/config.json`). Change `count`, `primary` and `extra` to match your own stock, then rebuild.

The packed house uses this plywood:

<!-- stock:main:start -->
| Thickness | Sheet size | Quantity |
| --- | --- | --- |
| 6 mm | 297 × 420 | 9 |
| 3 mm | 297 × 420 | 12 |
<!-- stock:main:end -->

Furniture and the garden scene appear only in the 3D view and use no plywood stock.

The book also lists:
- solid wood backing strips;
- foot blocks;
- roof cleats and the two MC1 catch blocks (12 mm board);
- the two GP1 garden stop posts (20 × 20 mm square strip);
- twelve rigid 0.9 mm hinge shims.

The current design requires A3 stock. Larger-stock fallbacks are disabled.

Measure your plywood before cutting. `make tolerance` rebuilds the house from the nominal templates with the thinnest and thickest sheets in `thickness_tolerance` (about −0.5/+0.4 mm on 6 mm, ±0.3 mm on 3 mm) and fails if any clearance closes. Parts that only touch, such as glue faces or floors on posts, just move a fraction of a millimetre. If your sheets fall outside that band, change `thickness` or the band in `source/config.json` and rebuild.

Installed metal hardware (the instruction book starts with exact specifications, purchase examples and spare-pack quantities):

<!-- assembly-hardware:start -->
| ID | Hardware or material | Required | Purchase allowance |
| --- | --- | --- | --- |
| HG1 | Small butt hinge, 25 mm high; nominal 40 mm open width. Two countersunk D2.5 screw holes per leaf; compare actual hole centers. | 6 | 8 |
| HG2 | Miniature butt hinge, 20 mm high; nominal 20 mm open width. Two countersunk holes per leaf for D2 screws. | 6 | 8 |
| SC1 | D2.5 x 12 mm countersunk wood screw, head D5 (bolt option: M2.5 x 16 countersunk machine screw with an M2.5 dome cap nut). | 24 | 30 |
| SC2 | D2 x 10 mm countersunk wood screw, head about D4. | 24 | 30 |
| SC3 | D3 x 16 mm countersunk wood screw; head about D6. | 6 | 10 |
| SP2 | Rigid 0.9 mm packing sheet; cut A06 x12, 10 x25 mm. Card, veneer or plastic. | 12 | 1 A4 sheet |
| MG1 | Neodymium disc magnet D8 x 3 mm, N35-N42, nickel plated, axially magnetised. Only ever fitted enclosed in wood. | 4 | 4 |
| SD1 | Plain steel disc D10 x 1 mm, sold as a magnet counter plate; not a magnet itself. | 4 | 6 |
| DW1 | Hardwood dowel rod D8: plugs behind the magnets; D4: stop-post dowels; D6: drawer stop and finial. | 1 m each | - |
| FB1 | Turned beech ball D35 mm with one flat (craft bead without a through hole, or drill blind). | 1 | 1 |
| CB1 | Greyboard (bookbinding board) 2 mm, A3. Glue the 1:1 template on and cut with a knife. | 1 sheet | 1 |
| PG1 | Clear PET or PETG sheet 0.5 mm, A4. Never glass or acrylic. | 1 sheet | 1 |
| TP1 | Cotton tape 15 mm, about 1 m. | 1 m | 1 m |
| FT1 | Self-adhesive felt dots D10-12 mm, about 1 mm thick. | 10 | 12 |
| BL2 | Flat steel bar 150 x 40 x 8 mm, drilled D3.5 twice; two 3 x 12 wood screws each. | 2 | 2 |
| AT1 | Furniture anti-tip strap kit (strap, screw eye, wall plug and screw). | 1 | 1 |
| LT1 | Optional: warm-white LED string or 3 mm LEDs with resistors; thin wire. | 1 set | - |
<!-- assembly-hardware:end -->

Countersunk screw length includes the head; bolt length is measured below the head.

**Magnets.** Every magnet is sealed inside hardwood: two in the MC1 catch blocks inside the opening shells, pulling up on steel discs in the F02 underside, and two in the GP1 garden posts, holding the opened shells by steel discs low on the hinge facets. Drill each bore from the hidden face with a depth stop, leaving 1 mm of wood over the magnet, drop the magnet in and glue a D8 hardwood plug behind it with epoxy. No magnet surface is ever exposed; if one shows, make a new block.

**Paint.** Use only primer, paint and clear finish whose maker declares EN 71-3, the European toy-safety standard for elements that can leach from a toy that is sucked or swallowed. Water-based acrylic furniture paint is the best choice for the solid colours. The book's "Toy-safe paint" page lists paint types and example products. Check the current tin or data sheet before you buy.

**Compare purchased hinges with the printed checking templates before drilling.** Nominal hinge sizes do not specify their hole patterns or barrel geometry. The design uses measured target footprints and 0.9 mm wall-leaf packing. Your actual hardware must match, or the plan must be regenerated.

The hinge hole patterns, centers, pilots and packing all come from `config.json`, so the printed template and the drilled CAD holes always agree. Wood screws go into solid backing; they never rely on the edge of a thin plywood sheet.

## Assembly and play access

The elevated floors use small metal angle brackets fitted after production. Check bracket fit, screw length and clearance during the dry fit.
The roof can remain removable. Magnets or a hinge-style attachment are optional choices. Check their fit before a permanent connection.
The build is not glued yet. The web companion reserves a HINTS area for future notes from real builds.

1. **Base and plinth.** Join the eight base sections over the underside supports on a flat board. Then glue the ten stone panels, the two drawer guide walls and the back stop onto the grey base. Screw the four foot blocks to the ground-floor plate F00 from below, then glue F00 on top.
2. **Drawer.** Build the drawer box with its stone front and slide it in from the back-right.
3. **Fixed rear shell.** Glue up the six rear facets and glue them to F00. Identical walls share one ID, so the rear reads W04, W05, W06, W07, W06, W09; the wall map in the book shows each facet.
4. **Floors and pillars.** Join the 6 mm floor sections over their seam strips (3 × 4 mm under the ground floor, 3 × 12 mm under the others). Use the positioning maps. Make the [physical joint samples](JOINT-VALIDATION.md) first. Install four continuous P01 pillars on the foot blocks. Slide both F01 levels over the rectangular openings. Seat F02 on the pillar tops. Fit small metal angle brackets under both F01 levels and F02; they are added after production and are not part of the kit.
5. **Opening shells.** Build the two front wall shells.
   - Square-edge wall corners use flat 3 mm corner ribs inside. A J01 rib lies across a whole facet and reaches about 30 mm onto both neighbours, so one rib holds two corners; dry-fit it, then glue all three walls to it at once so it sets both 150° angles. The one fixed-shell corner no rib can take gets a J02 bracket. Beside the three doors the ground-floor low braces sit just above the door openings and use the short-legged J03 and J04, which clear the windows beside the doors. Fill the small exterior seams where the walls are fixed; keep them clear where they move.
   - Glue backing blocks before drilling for hinges.
   - Follow the blue fastener borders and dashed drilling axes, and the orange glue-face outlines in the assembly diagrams.
   - Magnetic catches and stops: seal the magnets in the MC1 blocks and GP1 posts, glue one MC1 inside each shell near the front seam just under F02, epoxy the four steel discs, then stand the two GP1 posts on their two dowels each: glue and screw from below, felt dot on the face.
6. **Room dividers.** Glue PT2 on the ground floor and PT1 on each upper storey along the house axis; each doorway sits at the front end. PT2 has a raised rear notch to clear the rib above the veranda door. Glue the notches to the ribs.
7. **Doors and entrance steps.** Fit the three doors (main door W12, veranda door W07, back door W09) on 2.0 × 10 mm screws into hardwood strips. All open outward, have a recessed finger slot and keep a 2 mm gap above their thresholds. Glue the stone steps below the main and back doors.
   - Window trim: glue one WF1 surround over each window, its cross on the wall's solid cross, and a GZ1 PET pane inside. Then the nine seam battens and the rope ladder.
8. **Roof.** Assemble the cone over its supplied angle gauges.
   - Cloth tape reinforces the interior roof seams.
   - Each dormer is glued onto its R06 panel round the opening; its window gets a DM06 frame and a GZ2 pane.
   - Fit the chimney, cap and finial ball permanently to the roof assembly.
   - The current model has no roof turn-button catches. The roof ring lifts off with the cone.
9. **Veranda.** Glue the skirt and joists onto the base against the plinth, then the deck on top, level with the veranda door threshold. Add the side stair.
   - Glue eight 3 mm C01 pieces in pairs to make four 6 mm columns. Align the profiles and clamp flat.
   - After the glue cures, stand the four columns.
   - Glue the rear header flat to W07; this ties the veranda roof to the fixed shell.
   - Add the angled side headers, the crossframe, the roof panels and the hip caps, then the railings and steps.

To play, swing both walls open until they rest against the garden posts at 100°, where the sealed magnets hold them. Strap the house to the room wall with the anti-tip kit. The veranda stays in place, and the hidden drawer pulls out to the back-right. Lift the roof clear of the tower before reaching into the attic. Lift the house by its base. The catches, door sweeps and hinge gaps must stay clear of furniture and paint buildup.

## Example furniture

The 3D viewer and preview images show example furniture:

- the kitchen and dining set;
- the living room, bookcase, writing desk and stove;
- two beds, a wardrobe, bedside tables, a dresser and a washstand;
- an attic chest, a bench and a decorative telescope.

Furniture models share IDs when their dimensions match. Several close dimensions use standard sizes after adjustments of 1–3 mm. The furniture appears only in the 3D view. CAD plans, parts lists, supplier sheets and printouts cover the house and clay family. Clearance checks still include the furniture models.

## Thermo-clay Moomins

The family is modelled in 3D as clay, not plywood. `source/clay.py` builds each figure from rounded lumps (body, chest, head, snout, legs, feet, arms, hands, tail, ears and eyes, plus Pappa's top hat, Mamma's handbag and her striped apron), pressed together with smoothed joins the way real clay is. The flat underside lets each figure stand without a stand.

Page 3 of the instructions shows all three from the front, side, back and three-quarter at 1:2, with:

- each figure's floor and position in the 3D plan;
- its height, length and width;
- the clay it needs per colour, and how much a foil core saves;
- a list of the lumps to roll, with their sizes.

The appendix page "Model the family in thermo-clay" walks through modelling and baking.

| Figure | Floor | Size H × L × W | Volume | Clay to buy |
| --- | --- | --- | --- | --- |
| Moominpappa | Floor 1, living room | 65 × 54 × 35 | 27.0 cm³ | about 50 g (white 43, black 7) |
| Moominmamma | Ground floor, kitchen | 54 × 53 × 36 | 23.4 cm³ | about 44 g (white 41, red 3, black 1) |
| Moomintroll | Floor 2, bedrooms | 46 × 45 × 30 | 13.8 cm³ | about 26 g (white) |

The whole family needs about 120 g: two 56 g blocks of white, one of black and one of red. The volume comes from the closed 3D mesh. Grams assume 1.7 g/cm³ (a typical polymer clay) plus 10 % for handling. A foil core with 6 mm of clay all round brings the total down to about 104 g.

The heights come from `figures.heights`. They are sized so each figure passes upright through every doorway with `figures.door_clearance` to spare: 4 mm in width and 6 mm in height. The narrowest doorways are the 38 × 93.3 room-divider doorways; every figure's narrow side is at most 34 mm. Every build checks this. Weigh a block of your own brand and change `figures.clay` in `source/config.json` if it differs. That setting also holds the block size, the handling allowance and the foil-core wall.

`figures.levels` chooses which figures stand on which floor. The build puts each one in the front-most free spot, clear of furniture and the divider. The viewer and the renders use the smooth clay surface. The CAD files use an exact solid made from the same lumps without the smoothed joins, so the clearance checks stay fast. Their volumes are compared in the release checks. Every figure is too big for the EN 71-1 small-parts cylinder (checked on every build). Use a phthalate-free clay declared to EN 71, bake fully, varnish with an EN 71-3 varnish and drop-test each figure. Structural trim and hardware must remain securely attached.

## Native CAD and design changes

Open `output/cad/MoominHouse.FCStd` in FreeCAD 1.1 or later.
- The native CAD project contains the house and clay figures. Furniture solids only support renders and clearance checks.
- `ProfileLibrary` contains hidden local sketches, plywood extrusions and drilling cuts.
- Sketch geometry is fully constrained using Block constraints. Remove the relevant constraint before editing its geometry.
- Assembly instances reference the canonical extrusion/cut objects.
- Toggle `Fasteners` and `JointGuides` to inspect screw geometry, outlined glue faces and axes.

The Parameters spreadsheet drives extrusion thickness classes. Overall dimensions in the spreadsheet record the design; they do not drive every assembly placement.

For coordinated changes, edit `source/config.json` and rebuild **all** CAD, layouts and PDFs (see [docs/PIPELINE.md](PIPELINE.md#the-config-file)). Changing thickness alone in FreeCAD can leave supports and drilled depths inconsistent. Existing PDF exports never update automatically after a native edit.

The native assembly has material colors; the two-colour step treads keep their own paint per copy. The printable stone panels and roof shingle strips in the decor PDF are physical finishing details, not bitmap UV textures on STEP solids. STEP exports contain the wood assembly. Screw reference solids and joint guides are kept separately in the native document. Purchased hinges are specified by their target footprint and axes; their manufacturer-specific metal geometry is not modeled as a certified fit.

## What has been checked

Every build writes `output/reports/cad-validation.json` and `release-validation.json`. The build stops at the first failed check, so nesting, the book and the kit are never made from a failing model. The checks cover:

- **Parts and profiles:** valid one-solid profiles; native sketch features agree with the independent solids.
- **Files:** the native document and the STEP files reopen correctly.
- **Closed assembly:** no overlaps, with bounds matching the generated specifications.
- **Wall motion:** sampled every 5° from 0° to the 100° stop, with the veranda, the garden posts and the example furniture in place. The catches, the stops and their four sealed magnets are counted.
- **Doors:** all three entrance doors and three room doors swing 0–90° clear of everything.
- **Windows:** the veranda keeps 10 mm clear in front of every window.
- **Drawer and figures:**
  - the drawer slides its full 220 mm clear;
  - exactly one clay Moomin stands on each floor, clear of furniture, walls and dividers, and the walls swing past them;
  - the clay meshes are closed and match the volume estimate, and the CAD solids match their lumps;
  - every figure passes upright through every doorway with the configured clearance.
- **Roof lift:** clear at selected heights with the catches released.
- **Cutting:**
  - starter holes stay inside waste;
  - layout bounds and spacing are respected (3 mm between parts on A3 laser sheets);
  - every plywood part is on an A3 sheet with separate CNC operation files;
  - identical house parts share one ID;
  - every part has a cut source, and copy numbers are unique;
  - furniture and the garden have no cutting sheets or CAD plans;
  - every piece belongs to exactly one assembly step, and the stack-up and risk audit pass.
- **Furniture:** every furniture piece connects into its assembly.
- **Counts:** design-rule part quantities and hardware counts match.
- **Finish:** saved native colors.
- **PDFs:** A4 workshop pages and native A3 supplier sheets, with a contents page in the Complete PDF, and a true-scale 100 mm calibration square.
- **Real plywood** (`make tolerance`): the thinnest and thickest measured sheets close no clearance.

## Before you cut, and before anyone plays

This design still requires a physical dry fit with your measured plywood, actual hinges and printed test coupons. Sampling does not prove continuous movement. The CAD checks do not establish glue strength, load capacity, stability or toy certification. This is not a certified toy. For ages 3–5:

- round exposed edges;
- check attached trim and fasteners;
- supervise play with the clay figures and fit the anti-tip strap;
- keep fingers clear of moving gaps;
- check that no magnet is ever visible and the catch blocks and posts are firm;
- use only EN 71-3 primer, paint and varnish, and let them cure fully.

Test door movement and base stability before play.
