# A3 cutting files: readiness review for the manufacturer

Review of the A3 laser/CNC preparation (revision 9 / SUP-004, 2026-10-15: 3 mm laser spacing and grade 2/2 birch): what was verified, what was wrong and is now fixed, what still blocks sending the files, and what would make the package better. Numbers come from the last `make build` (reports in `output/reports/`).

**Verdict:** the package is now complete enough to **ask for a quotation**, not to order production. Two questions must be answered by the shop first (blockers B1 and B2 below), and four settings must be confirmed (section 3).

## 1. What was verified

| Check | Result | How |
| :--- | :--- | :--- |
| Every fabricated piece fits one A3 blank, whole | pass: 266 pieces, 101 profiles | `supplier.sheets_for`, release check |
| Nesting inside the sheet window, 3 mm laser lanes, 10 mm side margins | pass on all 23 sheets | `nest.validate` |
| Production pages exactly 297 × 420 mm, vector only, no text, no images | pass | `pdf_checks` |
| PDF production geometry = per-operation DXF | pass, within 0.0002 mm | `pdf_checks` |
| Units | mm: DXF `$INSUNITS 4`, SVG sizes in mm, PDF 1:1 | |
| DXF readable by a strict reader | pass after the fix below | `test_dxf_files_are_strict_r12` (ezdxf recover) |
| Inventory on sheets = parts list | pass | `supplier.sheets_for` |
| Sheet thickness never mixed | pass | `supplier.sheets_for` |
| No display-only furniture on any sheet | pass | release check |

Stock (23 A3 sheets): 3 mm × 12, 6 mm × 11. Every sheet uses grade 2/2 birch. Average outline use is 62.6 %.

## 2. Problems found and fixed in this revision

1. **The supplier PDF printed no specification.** Material, thickness, process, tolerances, retained edges, flip registration, packing and "only the production pages are machine input" were defined in `source/locales/*.json` but never drawn; the shop would have received pictures, maps and cut pages with no requirements. Now pages 2–4 print the specification, a "confirm before quoting" checklist, the features the customer drills, and the list of files to send. Test: `test_supplier_states_its_specification`.
2. **DXF files were not strictly valid.** They carried an R12 header with R2000 `LWPOLYLINE` entities; ezdxf's normal reader accepts them but its strict/recover reader rejects them (`missing 'AcDbPolyline' subclass`), and so can CAM importers. All DXF output now goes through `source/dxf_r12.py`: R12 `POLYLINE/VERTEX/SEQEND` and `CIRCLE`, a layer table, mm units. One more file per sheet, `PLY*-cnc-all-layers.dxf`, has every operation on its own layer.
3. **Finger joints could not be assembled from a router.** F01/F01B shared one zero-clearance path with sharp inside corners; a cutter leaves a radius in every inside corner, so the square tabs would not seat. Both F01 and F02 joints now have 0.1 mm clearance per side and R1.5 relief at every inside corner (`cnc.joint_clearance`, `cnc.tool_diameter`).
4. **Underside (flipped) machining and micro-drills were in the files.** Through holes were labelled `drill-bottom`; countersinks and the F02 disc recesses were underside operations; door hinge pilots were D1.2–1.4. Most laser and hobby CNC shops neither flip sheets nor drill under 2 mm. Now every through hole is drilled from the top, and underside features and holes under D2 are left out of the files and listed on page 4 for the customer (`cnc.two_sided: false`, `cnc.min_drill: 2`): 6 underside countersinks, 2 disc recesses, 24 hinge pilots D1.4.
5. **Two 6 mm sheets each held one roof-ring half (6 % used).** Nesting placed parts by outline area, so thin rings went last. Ordering by bounding box first saves two sheets (29 → 27).
6. **Wrong or missing text:** pillar end margins said 5 mm (now whatever is left of 10 mm), 30+ new part names had no Polish translation, the obsolete window bars and handle were still named.
7. **Four plywood thicknesses, two of them hard to buy.** 4 mm (doors, railings, drawer bottom, seam strips, base supports) and 8 mm (pillars, turn-buttons) each needed their own sheets. Now only 3 and 6 mm: the 4 mm parts are 3 mm, except the base supports and rim pads, which are 6 mm (the base lift is 6 mm, so the battery hatch keeps 3 mm off the table); the pillars are 6 mm in 6.6 mm openings; each roof turn-button is a 6 mm and a 3 mm ply glued into 9 mm, because one 6 mm ply fails stress test E08 (SF 1.26; 9 mm gives 2.49). The schema and `config_check.py` reject any other thickness.
8. **Nesting wasted the hollows of rings and quarter circles.** Parts were placed by their bounding box, in one order. Now each part is placed by its true footprint, and `nest.py` keeps the best of 24 part orders run through the `make stock` packer with its merge and squeeze passes: 27 → 23 sheets.

9. **Laser layout and grade 2 birch (SUP-004).** Both thicknesses now use 3 mm lanes and grade 2/2 birch. Router cutting needs a separate layout. The PDF specification and the saved purchase profile use the same choices.

## 3. Blockers and confirmations before ordering

**B1 — Fixed walls rely on the sheet's factory ends.** Five fixed wall profiles (6 pieces) are exactly 420 mm, the full A3 length; their top and bottom edges are the factory edges and are not machined (`retained_edges`). Retail A3 plywood is often ±0.5–1 mm and not square, and the fixed walls carry the roof ring. Ask for 420.0 ± 0.3 mm square blanks, or cut those walls from 440 mm stock (then the files need all four edges cut; TODO 23 proposes a 400 mm wall height for this).

**B2 — Thickness availability.** Every sheet must use grade 2/2 birch (grade 2 on both faces), in 3 or 6 mm, inside the measured bands (3 mm ±0.3; 6 mm −0.5/+0.4). Common "6 mm" birch is often 6.5 mm, which falls outside: 6.5 mm pillars would leave 0.1 mm in their 6.6 mm openings. Ask what they stock and measure it; if needed, change `thickness` and the band and rebuild before cutting.

Confirm (all on the checklist page):
- **Process per thickness.** Both 3 and 6 mm use laser cutting with 3 mm spacing. Confirm edge taper and charring. Drill or route the blind features separately: wall disc recesses D10.2 × 1.2 and base dowel holes D4 × 4. They are absent from the laser cut file.
- **Router alternative.** Router cutting requires wider lanes and new nesting. Router files assume an end mill of at most D3. Existing R1.5 corner relief remains in the design.
- **Hold-down.** Long 3 mm strips (battens up to 412 × 8, the 260 mm ladder) and small trim (C09 balusters, C12, R03, GD04, 3 × 4 seam strips) need a part-retention method agreed with the laser shop.
- **Tolerances.** `cutting_tolerance_mm` is still unset; ±0.2 mm is proposed on the spec page.

## 4. Remaining risks when sending the files

- **Part identification.** 266 pieces from 101 profiles and no engraving; sorting errors are likely. Ask for parts bagged per sheet with its reference map, or allow light ID engraving on hidden faces (the layout SVGs already carry the IDs).
- **Face grain.** The DXFs do not carry grain direction. The spec page asks for grain along 420 mm and no re-nesting across it for walls, pillars, battens and roof panels.
- **Re-nesting on large boards.** A shop cutting from 1250 × 2500 boards will re-nest; that is cheaper, but then the walls cannot use factory edges (B1) and must be cut on all sides. The per-part DXFs in `output/dxf/<ID>.dxf` support re-nesting.
- **Small offcuts and parts going missing** (the 3 × 4 mm seam strips, caps): the spec asks for them to be counted and returned.
- **Board safety.** For a toy, ask for E1 (or lower) formaldehyde class and the EN 71-3 statement of the board; the spec page asks.
- **Scale in PDF-driven shops.** Production pages are A3 at 1:1; any "fit to page" import shrinks them. The DXFs are the safer input.

## 5. Improvements worth making next

1. **Laser lanes and material — done.** `nest_spacing` and the saved supplier profile use 3 mm for both thicknesses. Every sheet specifies grade 2/2 birch. The purchase planner selects grade 2 only. The supplier specification and checklist read spacing from the generated layout. Router cutting requires wider lanes and new nesting.
2. **Wall height option without factory edges** (TODO 23), so a shop can cut every edge and re-nest freely.
3. **Nest inside openings on CNC sheets.** Done for hollows (TODO 24): small parts now fill the inside of the R02 ring halves and the quarter-circle sections. The jigsaw rule "no parts inside openings" still applies to real openings, but the largest (the R06 dormer and the B01 battery hatch) are under 50 × 50 mm.
4. **Fit-test coupon first.** Ask the shop to cut T01/T02 from each thickness before the rest, extended with one finger-joint pair, one pillar slot and one blind pocket, and check them before the full run.
5. **Machined purchased-wood parts.** A04 feet, MC1 catch blocks, AB1, R04 cleats and the A02/A03 strips could be machined by the shop from 12 mm hardwood or plywood (A02/A03 must be hardwood for the screws), sparing the customer the most fiddly hand work.
6. **Optional ID marking layer** in the combined DXF (off by default), and a sheet-orientation mark in a waste corner.
7. **Fill in the supplier settings** in `config.json` (`supplier.cutting_tolerance_mm`, `thickness_tolerance_mm`, `revision`) once the shop answers, and rebuild, so the PDF states agreed values instead of "to be confirmed".

## 6. What to send

`output/pdf/Lanternwood-House-Supplier.pdf` and `output/Lanternwood-House-Supplier-Cut.dxf`. The shop asked for "the whole job in one vector file, only what needs to be cut", and this is that file (also attached to every GitHub release):

- DXF R12 in millimetres, 1:1. Only `POLYLINE` and `CIRCLE` entities: no sheet frames, labels or engraving.
- One layer and colour per thickness: `CUT_3MM` red, `CUT_6MM` green. Laser software maps each colour to its own power.
- All A3 sheets keep their nesting, each in its own 297 × 420 mm slot, 20 mm apart. They run in rows by thickness, thinnest at the top, left to right in the order of the reference maps. `output/reports/supplier-cut-file.json` gives each sheet's slot origin.
- Every outline is closed. The fixed walls' factory blank ends are included, so the file still works if the shop re-nests onto larger boards; on a 420 mm A3 blank those two lines lie on the factory edge (B1).
- Not in the file, because a laser would cut them through: the blind pockets and holes (base dowel holes D4 × 4, wall disc recesses D10.2 × 1.2), and the features page 4 leaves to the customer. If the shop has no router for the blind features, drill them by hand.

`make cutfile` rewrites it from the current nesting without a full rebuild. A router shop that will machine the blind pockets also gets the `.csv` and, from `output/dxf/`, `PLY*-cnc-all-layers.dxf` (one per sheet) and `PLY*-cnc-<operation>.dxf/.svg`. Keep `PLY*-layout.svg` as reference only. Everything else (instructions, templates, decor) is for the builder.
