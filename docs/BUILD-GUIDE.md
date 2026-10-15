# Build guide

This guide is for the person with the jigsaw. It explains what you are building, how to print and cut it, what to buy and how it goes together.

Every file it mentions under `output/` is **generated**: it is not in the repository. Run the build first (see [Generate the build files](../README.md#generate-the-build-files) in the README). Paths are relative to the repository root. All dimensions are in millimetres.

## What you are building

A real plywood house, 838.4 mm tall. It has three main floors, an attic under a steep spire roof, opening front walls, a permanent veranda, a stone plinth with a hidden drawer, and a round Ø522.7 grey base. The tower uses twelve flat facets so it can be built with a jigsaw.

The ground floor has five windows, the middle and bedroom floors have six each, and the attic has one dormer window. The veranda has a 149.3 × 84 deck and stands on the fixed back-left facet W07, so it never has to be removed: both front walls swing open past it. It has:

- a red hipped roof with hip and ridge caps;
- shaped cream columns;
- a front railing and an angled side railing with balusters;
- side steps.

Its door opens outward onto the deck. The main entrance on W12 has a separate small gabled canopy.

The house stands on a 61.6 mm stone plinth on a 6 mm base, so the ground floor is at Z71.6. A drawer hidden in the plinth is about 46 mm deep inside and slides 205.3 mm out to the back-right; its front is two stone plinth panels with a finger notch underneath. Each storey has one room divider with a 38 × 93.3 doorway at its front end, next to the opening walls, giving two rooms per floor (no door leaves; add them later if wanted). The two front wall shells click shut on magnetic catches under the attic floor and stop at 100° against two small garden posts on the base, whose magnets hold them open. One thermo-clay (oven-hardening polymer clay) Moomin stands on each floor: Moominmamma in the kitchen, Moominpappa in the living room and Moomintroll in the bedrooms. The veranda deck is level with the ground floor, on a blue skirt with a 4-step side stair, and the main entrance has 4 stone steps. Both entrance doors open outward on the right-hand jamb (seen from outside).

The F01 floors have four pillar openings each. There are no stairs inside. Play access is through the opening walls and the lift-off roof. The furniture appears in the 3D viewer and renders only. It has no CAD plans, printouts or cutting sheets.

## Open these files first

| File | Contents |
| --- | --- |
| `output/pdf/Moomin-House-Complete.pdf` | Cover, clickable contents, dimensioned plan, clay figures, hardware shopping list, illustrated instructions, dimensioned parts, full-size cutting printouts, decor, clay family and the supplier appendix at the end. Use the contents for page numbers. |
| `output/pdf/Moomin-House-Instructions.pdf` | Assembly sequence, screw sections, hinge axes, glue joints, tools and workshop hints |
| `output/pdf/Moomin-House-Cutting-Templates.pdf` | Calibration page, packed sheet layouts, overlapping A4 tiles, white 3 mm template headers and solid wood templates |
| `output/pdf/Moomin-House-3mm-Hand-Templates.pdf` | House 3 mm parts only. Each large part uses two A4 pages with a 10 mm overlap. |
| `output/pdf/Moomin-House-Supplier.pdf` | Polish specification, inventory, reference maps, and clean A3 production pages grouped by thickness and operation. Separate from the A4 complete book. |
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

- **Base:** Ø522.7, four 6 mm sections over 4 mm underside supports. The horizontal seam is 4 mm below the centre.
- **Plinth:** 61.6 mm above the base, with a divided 6 mm ground-floor plate.
- **Tower:** 326.7 mm across vertices. Fixed walls are 420 mm tall. Opening walls are 418 mm tall.
- **Floors:** 6 mm plywood. Tops are Z71.6, Z211.6, Z351.6, and Z491.6. Clear room height is 134 mm.
- **Pillars:** four continuous 8 mm P01 parts, 402 mm long. Both F01 levels have matching through-openings.
- **Floor joints:** straight seams over 4 mm thick, 4 mm wide strips. Each half has 2 mm bearing.
- **Roof:** about 373.3 mm across, with an eave at Z491.6. The reinforcement ring uses two joined halves.
- **Veranda:** 149.3 × 84 mm deck, with its top at Z77.6.
- **Figures:** Pappa 60.7 mm, Mamma 50.4 mm, and Troll 42.9 mm target heights. All pass the 38 mm divider doorways.
- **Height:** 838.4 mm, including the finial and base supports.

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
- Identical pieces share one build ID on the templates and in the viewer. All 54 wall gussets use `J01`. The inventory gives the total quantity for each ID. Parts with different holes, openings or thicknesses have different IDs.
- Label each piece with its build ID. Sort the pieces by ID before assembly.
- The main nesting keeps at least 12 mm between profiles and a 15 mm margin at sheet edges.
- Cut openings while the sheet is still intact.
- Drill the S-marked starter holes in waste, insert the jigsaw blade there, and finish sharp corners with a precise file. H-marked holes stay in the finished part.
- Use a drill stop for blind holes and follow the marked entry face. Every hole schedule gives the diameter and coordinates from the local lower-left datum.
- Cut the round base with a jigsaw or a router trammel, then sand the edge fair.

- Save window and roof-ring offcuts for clamping pads and painting samples.

**A3 CNC sheets and A4 hand templates**

All plywood stock has the A3 dimensions 297 × 420 mm. Separate sheets cover 3, 4, 6, and 8 mm thicknesses. Fixed walls retain the supplied end edges. Moving walls have 1 mm end allowances. P01 pillars have 5 mm end margins. Other parts use 10 mm margins.

1. Send `Moomin-House-Supplier.pdf` and its operation CSV, DXF, and SVG files to the company.
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
- Number the roof panels 1–12 in pencil, starting with the dormer panel R06 and counting to the right. The mark in each strip's hidden glue band (for example 7·3) is course 7 on panel 3. Start at the eave and glue only the top 5 mm band; each course goes 9 mm higher, its tile tips on the dark line of the course below.

## Stock and hardware

The stock tables below are regenerated from `output/nesting.json` on every build. The default config assumes five 400 × 600 × 6 sheets you already own (`stock.main.6` with `"existing": true` in `source/config.json`). Change `count`, `primary` and `extra` to match your own stock, then rebuild.

The packed house uses this plywood:

<!-- stock:main:start -->
| Thickness | Sheet size | Quantity |
| --- | --- | --- |
| 8 mm | 297 × 420 | 1 |
| 6 mm | 297 × 420 | 20 |
| 4 mm | 297 × 420 | 2 |
| 3 mm | 297 × 420 | 5 |
<!-- stock:main:end -->

Furniture and miniature accessories appear only in the 3D view and use no plywood stock.

The book also lists:
- solid wood backing strips;
- foot blocks;
- roof cleats and the two MC1 catch blocks (12 mm board);
- the two GP1 garden stop posts (20 × 20 mm square strip);
- twelve rigid 0.9 mm hinge shims.

The current design requires A3 stock. Larger-stock fallbacks are disabled.

Measure your plywood before cutting. `make tolerance` rebuilds the house from the nominal templates with the thinnest and thickest sheets in `thickness_tolerance` (about −0.5/+0.4 mm on 6 and 8 mm, ±0.3 mm on 3 and 4 mm) and fails if any clearance closes. Parts that only touch, such as glue faces or floors on posts, just move a fraction of a millimetre. If your sheets fall outside that band, change `thickness` or the band in `source/config.json` and rebuild.

Installed metal hardware (the instruction book starts with exact specifications, purchase examples and spare-pack quantities):

| Item | Quantity |
| --- | --- |
| Nominal 25 × 40 wall butt hinges | 6 |
| Nominal 20 × 20 door butt hinges | 4 |
| Countersunk D2 × 12 wood screws | 24 |
| Countersunk D1.6 × 8 wood screws | 16 |
| Countersunk D3 × 16 wood screws | 6 |
| M3 × 25 pan-head bolts | 2 |
| M3 cap nuts | 2 |
| 0.5 mm steel washers | 16 |
| 0.5 mm nylon washers | 2 |
| 8 mm nylon spacers | 2 |
| D8 × 3 neodymium disc magnets (N35–N42, axially magnetised) | 4 |
| D10 × 1 plain steel discs (magnet counter plates) | 4 |

Countersunk screw length includes the head; bolt length is measured below the head.

**Magnets.** Two magnets sit in blind pockets in the underside of the attic floor F02 and hold the shells shut against steel discs in the MC1 catch blocks. Two more sit in the wall-side faces of the GP1 garden posts and hold the opened shells against steel discs low on the hinge facets. The steel discs ride on the walls, so no pair can be fitted the wrong way round. Bed each magnet in slow 2-part epoxy 0.5 mm below the surface and fill the recess with epoxy. Swallowed magnets are dangerous: check that all four are buried and firm before every play session.

**Paint.** Use only primer, paint and clear finish whose maker declares EN 71-3, the European toy-safety standard for elements that can leach from a toy that is sucked or swallowed. Water-based acrylic furniture paint is the best choice for the solid colours. The book's "Toy-safe paint" page lists paint types and example products. Check the current tin or data sheet before you buy.

**Compare purchased hinges with the printed checking templates before drilling.** Nominal hinge sizes do not specify their hole patterns or barrel geometry. The design uses measured target footprints and 0.9 mm wall-leaf packing. Your actual hardware must match, or the plan must be regenerated.

The hinge hole patterns, centers, pilots and packing all come from `config.json`, so the printed template and the drilled CAD holes always agree. Wood screws go into solid backing; they never rely on the edge of a thin plywood sheet.

## Assembly and play access

1. **Base and plinth.** Join the four base quarters over the underside supports on a flat board. Then glue the ten stone panels, the two drawer guide walls and the back stop onto the grey base. Screw the four foot blocks to the ground-floor plate F00 from below, then glue F00 on top.
2. **Drawer.** Build the drawer box with its stone front and slide it in from the back-right.
3. **Fixed rear shell.** Glue up the six rear facets and glue them to F00. Identical walls share one ID, so the rear reads W04, W05, W06, W07, W06, W09; the wall map in the book shows each facet.
4. **Floors and pillars.** Join the 6 mm floor sections over their 4 × 4 mm supports. Use the positioning maps. Make a physical joint sample first. Install four continuous P01 pillars on the foot blocks. Slide both F01 levels over the rectangular openings. Seat F02 on the pillar tops. Fit the rear ledges under the floors.
5. **Opening shells.** Build the two front wall shells.
   - Square-edge wall corners use internal J01 gussets, blunt and wide with about 20 mm of glue face on each wall. Beside both doors the ground-floor low gussets sit just above the door openings. Fill the small exterior seams where the walls are fixed; keep them clear where they move.
   - Glue backing blocks before drilling for hinges.
   - Follow the blue fastener borders and dashed drilling axes, and the orange glue-face outlines in the assembly diagrams.
   - Magnetic catches and stops: glue one MC1 block inside each shell near the front seam, just under F02. Fit the four magnets and four steel discs, then stand the two GP1 posts on the base: glue each one and screw it from below.
6. **Room dividers.** Glue PT2 on the ground floor and PT1 on each upper storey along the house axis; each doorway sits at the front end. PT2 has a raised rear notch to clear the gusset above the veranda door.
7. **Doors and entrance steps.** Fit the two doors (main door W12, veranda door W07). Both open outward and keep a 2 mm gap above their thresholds. Glue the stone steps below the main door.
   - Window trim: each window has three D01 horizontal bars and three D02 vertical bars. The frame is two of each; the third D02 fits inside the frame in the middle, touching the top and bottom bars, and the third D01 is glued across it outside at mid-height.
8. **Roof.** Assemble the cone over its supplied angle gauges.
   - Cloth tape reinforces the interior roof seams.
   - The dormer has dedicated sloped bearing supports and a crossbeam.
   - Fit the chimney, cap and finial permanently to the roof assembly.
   - Two captive turn-buttons retain the roof over its ring; the book shows the complete M3 washer and spacer stack.
9. **Veranda.** Glue the skirt and joists onto the base against the plinth, then the deck on top, level with the veranda door threshold. Add the side stair.
   - Stand the four columns.
   - Glue the rear header flat to W07; this ties the veranda roof to the fixed shell.
   - Add the angled side headers, the crossframe, the roof panels and the hip caps, then the railings and steps.

To play, swing both walls open until they rest against the garden posts at 100°, where the magnets hold them. The veranda stays in place, and the hidden drawer pulls out to the back-right. Release the two attic turn-buttons before lifting the roof, and close in the reverse order. Lift the house by its base. The catches, door sweeps and hinge gaps must stay clear of furniture and paint buildup.

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

The heights come from `figures.heights`. They are sized so each figure passes upright through every doorway with `figures.door_clearance` to spare: 4 mm in width and 6 mm in height. The narrowest doorways are the 40 × 100 room-divider doorways, and the widest figure is Moominmamma at 36 mm across her handbag. Every build checks this. Weigh a block of your own brand and change `figures.clay` in `source/config.json` if it differs. That setting also holds the block size, the handling allowance and the foil-core wall.

`figures.levels` chooses which Moomin stands on which floor. The build puts each one in the front-most free spot, clear of furniture and the divider. The viewer and the renders use the smooth clay surface. The CAD files use an exact solid made from the same lumps without the smoothed joins, so the clearance checks stay fast. Their volumes are compared in the release checks. Keep these small figures and accessories in a separate box for supervised play. Structural trim and hardware must remain securely attached.

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
- **Closed assembly:** no overlaps, with exact Ø522.666667 × 838.4 bounds.
- **Wall motion:** sampled every 5° from 0° to the 100° stop, with the veranda, the garden posts and the example furniture in place. The catches, the stops and their four magnets are counted.
- **Doors:** both doors swing 0–90° clear of everything.
- **Windows:** the veranda keeps 10 mm clear in front of every window.
- **Drawer and figures:**
  - the drawer slides its full 220 mm clear;
  - exactly one clay Moomin stands on each floor, clear of furniture, walls and dividers, and the walls swing past them;
  - the clay meshes are closed and match the volume estimate, and the CAD solids match their lumps;
  - every figure passes upright through every doorway with the configured clearance.
- **Roof lift:** clear at selected heights with the catches released.
- **Cutting:**
  - starter holes stay inside waste;
  - layout bounds and spacing are respected (12 mm between parts on A3 CNC sheets);
  - every plywood part is on an A3 sheet with separate CNC operation files;
  - identical house parts share one ID;
  - every part has a cut source, and copy numbers are unique;
  - furniture and miniature accessories have no cutting sheets or CAD plans.
- **Furniture:** every furniture piece connects into its assembly.
- **Counts:** design-rule part quantities and hardware counts match.
- **Finish:** saved native colors.
- **PDFs:** A4 workshop pages and native A3 supplier sheets, with a contents page in the Complete PDF, and a true-scale 100 mm calibration square.
- **Real plywood** (`make tolerance`): the thinnest and thickest measured sheets close no clearance.

## Before you cut, and before anyone plays

This design still requires a physical dry fit with your measured plywood, actual hinges and printed test coupons. Sampling does not prove continuous movement. The CAD checks do not establish glue strength, load capacity, stability or toy certification. This is not a certified toy. For ages 3–5:

- round exposed edges;
- check attached trim and fasteners;
- supervise the separate small accessories and the clay figures;
- keep fingers clear of moving gaps;
- check that the four magnets are buried in epoxy and firm;
- use only EN 71-3 primer, paint and varnish, and let them cure fully.

Test door movement and base stability before play.
