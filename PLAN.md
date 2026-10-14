# Moomin House — Revision 2 plan

Status: **implemented** · 2026-10-14 (see §11 for implementation notes and deviations)
Scope: (A) remove stairs and floor openings, (B) circular foundation, (C) move, enlarge and improve the veranda, (D) furniture becomes an optional appendix at the end of the PDF, plus (E) fixes for inconsistencies found in the current release.

All geometry is generated from `source/` (`model.py`, `architecture.py`), so every change below is a source change followed by a full rebuild. Never hand-edit `output/`.

---

## 0. Decisions

| Topic | Decision | Notes |
| --- | --- | --- |
| Base | **B01 becomes a Ø560 circle**, centred on the tower, 8 mm | Fits the existing 600×900×8 sheet (570 usable inside the 15 mm margins) |
| Veranda facet | **W05, back-right, normal 45°** (fixed shell, no hinge, no windows at any level) | Opened walls at 110° reach only y ≤ +8 mm behind the hinge line, leaving ≥ 50 mm to the veranda |
| Veranda size | **Deck 160 × 90** (was 110 × 60), about 2.2× the area | Outer deck corner at r ≈ 271, so a Ø560 base leaves a ~9 mm rim |
| Old W02 door | **Restored as a standard window** | Ground floor: 5 windows + main door (W12) + veranda door (W05) |
| Veranda mounting | **Permanent** (default; say so if you want it removable) | Glued to B01 and to a W05 wall ledger; the two D6 dowels stay as glued alignment pins; the removal steps are deleted |
| Furniture | **Optional appendix** at the end of the Complete PDF, plus its own PDF | Includes the veranda chair, the X01–X04 accessories and textile/miniature decor |
| Stairs | **Removed**, together with every floor opening and the L02 opening rails | Attic access stays via roof lift |

---

## 1. Prerequisites (do first)

1. **Put the project under git.** `moominshouse/` is *not* a git repository, despite what the harness reports. Run `git init`, then commit `source/`, `README.md`, `assets/`, `original/` and the current `output/` as the baseline. That gives a diffable record of `parts.json`, `nesting.json` and the reports for every phase.
2. **Install FreeCAD 1.1.x.** It is absent from this Mac, but `cad-validation.json` shows the last build ran on FreeCAD 1.1.4. Install with `brew install --cask freecad`, then use the runtime at `/Applications/FreeCAD.app/Contents/Resources/bin/python`.
3. **Baseline rebuild.** `rebuild.py` must reproduce today's `release-validation.json` (all_pass) before any change, so the toolchain is proven.

---

## 2. Change A — Remove stairs and floor openings

**Model (`model.py`)**
- Delete `floor_hole` (`:78`) and the `[floor_hole]` cut lists on F01 and F02 (`:79`, `:83`). F01 becomes a plain 12-gon. F02 keeps only its two D3.2 pivot holes. Update the F01 note.
- Delete the L02 "stair opening support rail" (`:148-150`).
- Delete the staircase block S01–S04 (`:151-163`). The `Stairs` category then disappears.

**Pipeline**
- `render.py:102`: drop the `stairs` render. Its filter `startswith('S')` would also catch any future S-part.
- `book.py`:
  - Delete the page "Stair and ledge placement" (`:241-246`) and move its L01 ledge paragraph onto the frame page.
  - Delete step 05 (`:252`).
  - Remove the stair opening outline and its "164 stair opening" dimension from the frame-placement plan (`:233-236`).
  - Fix the remaining stair text:
    - step 04 "keep each stair opening aligned";
    - offcuts "stair-opening rectangles" (`:196`);
    - furniture text "keep stairs accessible" and "rear staircase passage" (`:263`, `:293`);
    - palette "Tables, stairs and chest" (`:475`);
    - plywood "Walls, stairs, veranda" (`:170`);
    - validation page "landing bridges";
    - floor-skin footer "Keep stair … openings clear" (`:511`) and its comment (`:487`).
- README: remove "Make three stair flights", "stair … offcuts" and "The stairs, catches…".

**Knock-on effects**
- 6 mm demand drops by 36 stair pieces (S01 ×6, S02 ×30). The extra 500×600 sheet PLY6-06 currently holds only R05 plus five S01 stringers, so it should disappear. The 8 mm sheet loses S03, S04 and L02.
- Observation, not a new problem: every floor is supported only at y ≥ 0 (posts and the rear L01 ledges). The front half cantilevers about 160 mm in 8 mm ply. Removing the openings makes the floors stiffer. Keep the "press-test the front floor edge" item in the dry-fit checklist.

---

## 3. Change B — Circular foundation Ø560

**Model**
- Add `"base_diameter": 560` to `config.json` and delete the unused `base_size`.
- B01 outline:
  - Use a 180-segment polygon for nesting and templates (max chord error 0.04 mm).
  - Add `outercircle = [280, 280, 280]` so FreeCAD builds a true circle. `build_cad.profile_shape` and the sketch writer already support this.
- Replace every hard-coded `225` and `450` with the radius from config:
  - `model.py:66` (feet holes), `:71` (veranda sockets), `:72-73` (B01 outline and placement);
  - `book.py:201` and `:226`;
  - `verify.py:19`.
- Replace the note "Round corners to R10" with "Cut the circle with a jigsaw or a router trammel; sand the edge fair."
- **DXF:** `build_cad.dxf()` writes `outer` as a polyline even for `outercircle` parts; today the A05 dowels export as 24-gons. Emit a `CIRCLE` on `CUT_OUTER` when `outercircle` is set.

**Stock**
- B01 nearly fills the width of PLY8-01. The F01, F01 and F02 floors (about 333 across each) re-nest, so expect one more 8 mm piece (about 400×400). Let the nest decide.
- Generate the README stock table from `nesting.json` instead of maintaining it by hand.

**Book**
- "Overall dimensions" shows "Ø560 base".
- The frame-placement plan draws the circle.
- The feet table is unchanged; the feet sit at r ≤ 150.

---

## 4. Change C — Veranda on W05: larger, permanent, improved

### 4.1 Placement (parameterised, not hard-coded)
- Add a config block:
  ```json
  "veranda": {"facet": "W05", "width": 160, "depth": 90, "column_height": 126, "permanent": true}
  ```
  plus `"doors": {"main": "W12", "veranda": "W05"}`.
- Derive `pn`, `pu`, `pv` and `po` (`model.py:67-68`) from the facet angle. Today they are hard-coded to −45°.
- Every `'W02'` literal becomes `doors.veranda`:
  - `architecture.py:26`, `model.py:239`;
  - `book.py:220-221`, `:255`, `:330`, `:523`.
- Door notch rule: `model.py:91` (`i in (1,11) and level==0`) is derived from `doors`.
- **W02 ground floor:** it gets a normal 40×60 window with D01/D02/D04/D05 trim. Windows per floor become **[5, 6, 6, 1]**.

### 4.2 Geometry and structure improvements
- **Deck E03:** 160 × 90 × 6 mm at Z8–14. Its rear edge is shaped to the W04, W05 and W06 outer faces, so it butts the tower with no gap. Delete **E12** (the 9 mm threshold bridge, no longer needed). Move the two B01 socket holes and dowels to the new deck.
- **Columns C01:** stretched to about 126 tall (Z14–140); keep the minimum neck at 6 mm or more.
  - Front corner columns sit at the deck front corners.
  - Rear columns stand **on the W05 face** (tangential ≈ ±38), **not** at the deck rear corners. Rear corner columns would sit directly in front of the W04 and W06 ground-floor windows: the deck side line meets W04 about 40 mm from the corner, and that window spans about 26–66 mm.
- **Headers:** C02 front and rear, C03 sides, Z140–150. The rear header is also glued to a new **6 mm wall ledger (L03) on W05**, which ties the veranda to the fixed shell.
- **Railings and balusters:**
  - Front rail, plus a closed side rail on the W06 end.
  - The side rails run from the front corner columns to the rear columns, so they are slightly angled in plan and do not cross the W04/W06 windows.
  - The steps side (W04 end, facing front-right) stays open.
  - About 9 front balusters and 3–4 per closed side; the CAD sets the exact counts.
- **Steps:** on the W04-facing end, two treads Z8–11 and Z11–14, 56 wide, glued to the deck edge and to B01. They replace the 10×40 and 20×40 3 mm wafers.
- **Roof:** hipped, about 168 × 98 including 4 mm overhang, 45° pitch, peak around Z200.
  - The whole roof stays below Z215, under the W04/W06 first-floor window frames at Z217.
  - Add **hip cap strips** (3 mm, about 5 wide). They cover the 2 mm seam insets that show as open gaps in today's `porch.png`.
  - The rear eave stays at least 3 mm clear of the wall.
- **Chair PC01–03:** moves to the furniture appendix (§5). In the furnished assembly it must sit outside the door sweep. Today the chair back is struck at ~60° of door opening.
- **Decor:** add a printable deck-board texture (160×90 with the shaped rear edge) to the decor PDF.

### 4.3 Doors, walls and gussets (knock-on effects)
- **Threshold clearance (both doors):** E10 goes from 8 to 6 mm tall, so its top is at Z14 and flush with the deck. The door bottom stays at Z16, which gives a real 2 mm gap. Today the threshold top is Z16 and the door bottom is Z16, so the clearance is 0 (see §8 I1).
- **Gussets:** the door-adjacent ground gusset rule `j in (8,10)` (`model.py:220`) is derived from the door facets on the hinge side.
  - W05 hinge side is corner j = 1 (30°), which moves to Z8.
  - j = 10 reverts to the normal Z34, because W02 no longer has a door.
  - j = 8 (W12) is unchanged.
- The veranda door opens outward onto the deck; its sweep radius is about 47 mm and the deck is 90 deep.

### 4.4 Validation that becomes mandatory once the veranda is fixed
- The wall-swing obstacles must include **`Porch`** (`build_cad.py:211`), as must the roof-lift check (`:233`).
- New **door-sweep check:** both doors, 0–90° in 5° steps, against every other installed group.
- New **window-occlusion check:** no veranda solid within 10 mm in front of any window opening.
- In the CAD STEP, the open and exploded views no longer translate the porch (`build_cad.py:146`). In the preview renders (`render.py:30`), the open view no longer hides it.
- Update or remove the text that assumed a removable veranda:
  - steps 13 and 20 ("lift off the porch");
  - README "Remove the veranda…";
  - `wall_swing_configuration` (`build_cad.py:242`);
  - DW1 wording ("glued alignment pins");
  - "Redesign from your photos" page (`book.py:206-210`);
  - `architecture.py:48` comment, `derived.reference_style`, `derived.veranda_size`.

---

## 5. Change D — Furniture becomes an optional appendix

**What moves:** K1–K7, V1–V6, U1–U5, N1–N4 (Furniture), PC01–PC03 (veranda chair) and X01–X04 (Accessories). That is 61 profiles and 142 pieces. The rugs/quilts/towels page and the miniature pictures/books page move with them.

**Model and data**
- Add a part flag `optional: true`. The chair moves from group `Porch` to group `Furniture`.
- Main and optional parts are never nested on the same sheet. Today PLY4-01 mixes E01 doors, C06 and C09 with furniture, and PLY3-01 mixes the roof with furniture backs and accessories.

**Nesting (`nest.py`)**
- Run two passes and write `nesting.json` (main) and `nesting-furniture.json` (optional).
- Optional sheets use the IDs `FUR4-xx` and `FUR3-xx`.
- The main 4 mm need shrinks to the E01 doors, rails, balusters and FN01, so it may fit an A4 or 400×400 piece.

**CAD (`build_cad.py`, `decorate_cad.py`)**
- `MoominHouse.step` contains the house without furniture.
- New `MoominHouse-furnished.step` contains the house with furniture.
- In the FCStd, the furniture sits in a group labelled "Optional furniture".
- Collision and wall-swing checks still run *with* the furniture, so the optional furniture can never block the walls or catches.

**Renders**
- `house-open` and `house-exploded` are rendered without furniture for the main book.
- New `house-open-furnished` serves as the appendix cover.
- The kitchen, living, bedroom and attic renders move to the appendix.

**Book (`book.py`)**
- The main book excludes optional parts from the part inventory, dimensioned pages, templates and stock table.
- Main assembly steps are renumbered:
  01 prepare · 02 base feet · 03 rear shell · 04 floor frame · 05 opening shells · 06 hang walls · 07 doors · 08 window trim · 09 roof and dormer · 10 chimney · 11 roof catches · 12 build and fix the veranda · 13 paint and paper · 14 open, close and check.
- New `appendix()` produces `Moomin-House-Furniture-Appendix.pdf`. It contains, in order:
  - an intro (optional, small parts, supervision for ages 3–5);
  - the furniture stock table;
  - the part inventory and dimensioned pages;
  - its own calibration page and cutting templates;
  - steps A1 kitchen, A2 living, A3 bedrooms, A4 attic, A5 veranda chair, A6 accessory set;
  - the "Furniture assembly diagrams" and "Furniture measurements" pages;
  - the textile and miniature decor pages.
- `main()` appends the appendix **last** in `Moomin-House-Complete.pdf`, with the outline entry "Appendix — Optional furniture".
- The J5 joint is renamed "glued edge-to-face (veranda, trim, optional furniture)".

**README:** the furniture paragraph becomes "Optional furniture appendix"; add the new PDF and STEP files to the file table.

---

## 6. Validation changes (`verify.py`, `build_cad.validate`, `audit_connections.py`)

| Check | Today | Change |
| --- | --- | --- |
| Bounds | literal 450×450×700 | from config: **560×560×700** |
| Windows per floor | compares a literal `[4,6,6,1]` (cannot fail) | count real wall cut-outs per level; expect **[5,6,6,1]** |
| CAD instance quantities | quantities derived from the same instances (cannot fail) | compare against an expected-quantity table in source |
| Original 6 mm sheets | `== 5` | `≤ 5`, and extras only when all 5 are used |
| PDFs | `== 5` | `== 6` (adds the Furniture Appendix) |
| Main and optional separation | — | no optional part on a main sheet or in a main book section, and every optional part is covered by the furniture nest |
| Wall swing / roof lift | Porch excluded | Porch included (§4.4) |
| Door sweep / window occlusion | — | new (§4.4) |
| Trim carrier | — | carrier height ≤ printable A4 (~268 mm), or split into two carriers (see I3) |
| No stairs | — | no `Stairs` category, F01 has no cuts, F02 has only its 2 pivot holes |
| Hardware | SC1 24 / SC2 16 / SC3 4 / BL1 2 | unchanged; HG2 ×4, DW1 ×2 |
| Furniture audit | families include `PC` | unchanged, but reported in the appendix |

---

## 7. Docs to rewrite after the rebuild

- **README:**
  - intro (veranda on W05, circular base, no stairs);
  - "Open these files first" (new PDF and STEP);
  - the dimensions line;
  - stock table (generated);
  - hardware dowel wording;
  - "Assembly and play access" (no veranda removal, no stairs);
  - furniture paragraph;
  - "What has been checked" (door sweep, veranda in the swing check).
- `pdf-report.json` veranda string; `derived` fields.
- Cover (optional): `assets/cover-prompt.txt` asks for a "charming front porch". Regenerate it if the back-right veranda should appear.

---

## 8. Inconsistencies found in the current release

Severity: **H** gives a wrong physical result or breaks the build; **M** means misleading validation or docs; **L** is cosmetic or dead code.

| # | Sev | Where | Finding | Resolution |
| --- | --- | --- | --- | --- |
| I1 | H | `architecture.py:25-29`, book step 08 | Both doors rest **directly on their thresholds**: E10 top is Z16 and the E01 bottom is Z16, so the gap is 0 mm. The book says the door "clears" (it cites the deck at Z14, not the threshold). The collision check passes only because touching faces have zero volume. | E10 6 mm tall (§4.3) |
| I2 | H | `architecture.py:84-95`; `build_cad.validate` | The veranda door **strikes the chair back PC03 at ~60°** of opening. Door swing is never simulated. | Chair moves to the appendix outside the sweep; add a door-sweep check |
| I3 | H | `fabrication.py:10`, `book.py:427` | The trim carrier is a single 190-wide blank, now 261 mm tall. Adding the W02 window makes it **275 mm**, which no longer fits the A4 page (about 268 mm printable). | Split into two carriers, or widen them; add a check |
| I4 | H | `architecture.py:20-34`, `model.py:95`, `:109-114`, `config.json` | **Config does not drive the hinge geometry**, although the README says it does. `door_hinge` feeds only the printed checking template; the CAD hard-codes door holes x5 / y10, 22, 58, 70 and hinge Z32/80. The wall hole hx=12 and the 0.9 packing are hard-coded, and `packing_thickness`, `leaf_thickness`, `barrel_radius`, `assembly_allowance` and `base_size` are unused. After a config edit the template would no longer match the drilled holes. | Derive holes, offsets and packing from config; remove unused keys |
| I5 | M | `model.py:244` → `verify.py:20-21` | Tautological checks: `windows_per_floor`, `floor_tops` and `clear_room_height` are literals, and the instance-quantity check compares a list with itself. | §6 |
| I6 | M | `verify.py:41` | "Uses five original 6 mm sheets" demands exactly 5. Removing the stairs reduces demand, so the check would fail on an improvement. | `≤ 5` rule |
| I7 | M | `build_cad.py:211`, `:233`, `:242` | Wall-swing and roof-lift checks ignore `Porch`. That was valid only for a removable veranda. | Include Porch |
| I8 | M | `book.py:170` | The stock "Use" column is guessed from thickness: 4 mm reads "Furniture" although it also carries the doors, railings, balusters and finial; 6 mm says "stairs". | Generate from the parts on each sheet |
| I9 | M | `nest.py:17-24` | Furniture and accessories share sheets with structural parts, so the furniture cannot be skipped. | Two nests (§5) |
| I10 | M | `architecture.py:84-95` | The chair has category `Furniture` but group `Porch`. It is rendered, joined and nested as veranda structure. | Group `Furniture`, optional |
| I11 | M | `model.py:72` | The B01 note says "Round corners to R10", but the CAD, DXF and templates have sharp corners. | Superseded by the circle |
| I12 | M | `render.py:19-30` vs `build_cad.py:140-147` | Previews and STEP disagree on the open and exploded offsets: roof +230 vs +250, walls −50 vs −40, porch hidden vs moved +500 mm. | One shared offset table |
| I13 | M | `build_cad.py:51-62` | The DXF exports `outercircle` parts (A05 dowels) as 24-gon polylines. | Emit a `CIRCLE` (needed for B01) |
| I14 | M | repo | No git history, and no FreeCAD on this machine, although the reports came from FreeCAD 1.1.4. | §1 |
| I15 | L | `model.py:136-138`, `:209-211` | Dead code: P01 and A01 are created then deleted. The A01 note promises "thirty 152 mm lengths" that are never built. | Delete |
| I16 | L | `model.py:100` | The wall note says "paint seam covers outside", but no such part exists. | Reword |
| I17 | L | `book.py:479` | Comment says "Nine interior panels per level"; the code generates 12. | Fix comment |
| I18 | L | `model.py:244` | `derived.veranda_size` and `reference_style` are literals, so they drift from the geometry. | Derive from config |
| I19 | L | `assets/cover-prompt.txt:5` | The cover art shows a front porch. | Optional regeneration |

These were checked and are consistent:
- The wall-hinge hole sits 15.14 mm from the barrel axis along the leaf, matching the template.
- There are 54 J01 gussets, with a 12/12/30 split.
- Screw counts are SC1 24, SC2 16, SC3 4 and BL1 2.
- The roof-pivot stack is 21.5 mm with 3.5 mm of thread; the turn-button gap is 3 mm.
- Floor tops are at Z8/168/328/488 and the finial reaches 700.
- The chimney box is square, and the hinge backing and shim holes align.
- Opened walls at 110° stay at y ≤ +8.

---

## 9. Implementation order

Each phase ends with a full `rebuild.py`, a `parts.json` and `nesting.json` diff against the previous commit, and a commit.

1. **Refactor only** (I4, I5, I15–I18, door and gusset rules derived from config). The geometry must come out **identical**: `parts.json` unchanged except for metadata.
2. **Change A:** stairs out.
3. **Change B:** circular base and the DXF circle.
4. **Change C:** veranda on W05, W02 window, thresholds, gussets, new checks (I1–I3, I7, I12).
5. **Change D:** optional furniture split (nest, CAD, renders, appendix, I8–I10).
6. **Validation and docs** (§6, §7). Review the regenerated `house-closed.png`, `porch.png`, `house-open.png` and the Complete PDF page by page.

**Done when**
- `release-validation.json` is all_pass with the new checks.
- Bounds are 560×560×700, with zero collisions, zero swing/lift/door-sweep hits and zero window occlusion.
- The main book and main sheets contain no optional parts, and the appendix is the last section of the Complete PDF.
- No S01–S04 or L02 parts remain and the floors have no openings.
- The README stock table matches `nesting.json`.

## 10. Open items to confirm during CAD review

- Exact baluster counts and spacing on the angled side rails.
- Hip-cap colour: red (blends in) or cream (accent).
- Whether to add a printable garden or path ring for the wider Ø560 base rim (decor only).

---

## 11. Implementation notes (2026-10-14)

Commits: baseline `5a2f0d9`, Phase 1 refactor (geometry verified identical), Phase 2 stairs, Phase 3 round base, Phase 4 veranda, Phase 5 furniture appendix, Phase 6 docs. Release validation: **27 / 27 checks pass**.

**Deviations from the plan**
- **Veranda frame.** The rear header **C10 is the W05 wall ledger** (glued flat to the wall); there is no separate L03 part.
- **Veranda sides.** The side headers and railing are **angled**: they run from the front corner columns to rear columns standing on the W05 face. This canted plan keeps the roof and railing clear of the W04/W06 windows, which a rectangular frame would cross.
- **Veranda roof.**
  - The roof is a front triangle plus two mirrored side panels meeting at a ridge that runs to the wall (no rear slope against the wall).
  - It is carried by one central crossframe C07, plus line contact on the header edges.
  - The apex sits at about Z204 on the inner face and Z208 on the outer face.
- **Veranda layout.** Only the W06 side has a railing: 9 front and 6 side balusters. The W04 side is open above the steps.
- **Trim carriers.** There are **two balanced 190 × 138 trim carriers** rather than one 275 mm blank.
- **Stock.**
  - Each new board is the smallest extra stock that fits.
  - The R05 roof jigs are now 8 mm and share the base sheet, which removed the extra 500 × 600 × 6 board.
  - The house 4 mm parts fit one A4 sheet.
  - Furniture uses 4 mm (400 × 600 + 2 × A4) and 3 mm (A3).
- **Build cleanup.** FreeCAD `.FCBak` backups are deleted after each build and ignored by git.
- **Bounding boxes.** Validation now uses exact bounding boxes. The default ones follow the 0.8 mm display tessellation and under-report curved parts.
- **Not done: the cover art.** `assets/summer-cover.png` still shows a front porch; regenerating it needs the image tool.

---

## 12. Revision 3 (2026-10-14): DeAgostini-style base, rooms, spire roof

Requested:
- a stone plinth with a hidden drawer, incorporated by raising the total height 20 mm and lowering each storey 10 mm;
- a grey base;
- one room divider with a door per floor;
- the veranda at ground-floor level, with stairs;
- dimensions and changes shown in the 3D viewer;
- a spikier roof made by adding height above the walls;
- printable fish-scale shingles.

Remaining comparison items moved to `TODO.md`.

**What was built**
- **Heights:** floor pitch 150 (was 160) and walls 450 (was 480). A 50 mm plinth puts the ground floor at Z58 (floor tops Z58/208/358/508). The roof rises 339 mm at about 61°, for a total of **880**.
- **Plinth:**
  - ten 6 mm stone panels between the grey B01 disc and a new 12-sided F00 plate (354 across flats, with an 8 mm rim outside the walls);
  - two guide walls and a back stop around the drawer bay;
  - the foot blocks are now screwed through F00.
- **Drawer:** 160 × 275 × 36, sliding 220 mm toward -X (the left side). Its front is the two plinth facets at the 180° corner, with a finger notch under the corner, so it reads as plinth stone.
- **Room dividers:** one 6 mm divider per storey along X0, with a 40 × 100 door on a cloth-tape hinge that opens into the right-hand room. Its rear notches clear the corner gussets. Furniture that crossed X0 was moved.
- **Veranda:** the deck top is at Z64, flush with the threshold. It sits on a blue skirt and joists down to B01, with a 4-riser stair on the open W04 end.

**Added by me as consequences (beyond the brief)**
- **Main entrance steps.** The door threshold rose to Z64, so the main door got 4 stone steps up to the plinth ledge.
- **Upper corner gussets.** They moved from 132 to 122 above each floor; at the lower pitch they collided with the floor ledges.
- **Wall hinges.** Re-centred at Z98/283/468, because the old top hinge would overhang the shorter moving wall.
- **Dormer.** Rebuilt parametrically for any roof pitch: triangular sides on the slope, roof panels meeting the main roof, and the R06 opening derived from the dormer itself.
- **Chimney.** Its height now follows the roof.
- **Stock.** The R05 roof jigs went back to 6 mm. The nester now falls back to extra boards when a part does not fit the primary sheet.

**New checks**
- The drawer travels its full distance clear of everything.
- Five doors sweep clear (two entrance doors, three room doors).
- Bounds are Ø560 × 880.
- Design-rule quantities cover the plinth, drawer, dividers, skirt and stairs.

---

## 13. Revision 4 (2026-10-14): deeper drawer, door hinges, doorways, figures, cover

- **Drawer:** 50 mm deep inside (a 54 mm box). The plinth rises 50 → 64 mm, so the ground floor moves to Z72 and the total to **894**. The roof and everything else keep their sizes.
- **Entrance doors:** they still open outward, but now hinge on the opposite (right-hand) jamb seen from outside.
  - Hinges, backing strips, pilot holes and handles are mirrored.
  - The W05 low gusset beside the hinge jamb sits at 96 mm, above the backing strip. Dropping it to the floor would have hit a rear foot block.
  - The W12 door now hinges at the front seam, where there are no gussets.
- **Room doors:** the leaves and tape hinges are removed. Each divider keeps a 40 × 100 doorway, now at its front end next to the opening walls.
- **Figures:** Moominpappa 82, Moominmamma 66 and Moomintroll 56, as 4 mm plywood side silhouettes on 34 × 16 stands.
  - They are generated in `source/figures.py`: rounded shapes, a traced outline, then line simplification.
  - There is one set per floor including the attic, placed automatically in the front-most free spots.
  - They are optional parts (FUR sheets, appendix step A7).
  - Instructions page 3 shows them at 1:1, with measurements and their 3D-plan positions.
  - They are included in every collision and motion check, and in the viewer.
- **Cover:** `source/cover.py` paints the scene around a dedicated CAD render and hand-letters the title in Chalkboard SE. The old AI cover and its prompt were removed (they remain in git history).
- **Veranda chair:** moved to the front-left corner, clear of the veranda door's new swing.

---

## 14. Revision 5 (2026-10-14): thermo-clay Moomins, one per floor

- **Request:** make the Moomins 3D and clay-like, because they will be modelled in thermo-clay (oven-hardening polymer clay); show example views on one PDF page; estimate each figure's volume to see how much clay it needs; place one Moomin on each floor.
- **Model:** `source/clay.py` replaces the plywood `figures.py`.
  - Each figure is a smooth union of signed-distance lumps (ellipsoids, rolls, rounded cylinders and boxes, a half-ring handle), cut flat at z=0 so it stands.
  - Pappa has a top hat and no ears. Mamma has a black handbag and a 1 mm red/white striped apron layer.
  - Target heights: Pappa 80 (with hat), Mamma 66, Troll 56.
- **Meshes:**
  - Surface nets (vertices projected onto the surface) give the light display meshes for the viewer and the renders.
  - Marching tetrahedra (Kuhn split) give the closed 2-manifold used for the volume. Surface nets can pinch an edge at saddle faces, so they are not used for volume.
- **Clay estimate:** volume from the closed 1 mm mesh. Colour shares and the foil core (white clay deeper than 6 mm) come from a 0.5 mm grid. Grams = volume × 1.7 g/cm³ + 10 %; blocks are 56 g. All of these are in config `figures.clay`.
  - Pappa 50.3 cm³ / about 94 g (white 81, black 14).
  - Mamma 42.8 cm³ / about 80 g (white 74, red 5, black 1).
  - Troll 24.9 cm³ / about 47 g.
  - The family needs 4 white + 1 black + 1 red block, or about 174 g with foil cores.
  - The density is an assumption: no published figure was found, so the book tells the builder to weigh a block of their brand.
- **Placement:** config `figures.levels` = mamma / pappa / troll on the ground floor / floor 1 / floor 2. Nothing goes in the attic: "each floor" means the three storeys.
  - Each figure takes the front-most free spot, facing the front and turned 25° toward the middle (straight ahead if that is all that fits).
  - Pappa ends up mid-room in the living room: the coffee table leaves no space in front for his 66 mm length.
- **CAD:** the FreeCAD solid is the plain union of the same lumps (28–56 exact faces, within 0.2 % of the numpy plain-union volume). The smoothed clay is 2–6 % larger. A decimated mesh solid was tried and rejected: decimation was unreliable (non-manifold or self-intersecting results), and the full mesh made validation take about 10 minutes and the furnished STEP 233 MB.
- **Book:** instructions page 3 is now "Moomin family in thermo-clay".
  - Front, side, back and three-quarter renders at 1:2, from `clay_render.py`: a numpy G-buffer rasteriser with wrapped diffuse light, SDF ambient occlusion and a satin highlight.
  - Per-figure size, volume and clay; the "How much clay" table; notes; and a "Lumps to roll" size list.
  - Appendix step A6 "Model the family in thermo-clay" uses the new `clay-family.png`.
- **Removed:** FG1–FG4 plywood parts, their STEP/DXF files and FUR layouts. The appendix is 10 pages shorter.
- **Checks:** the clay solids take part in the closed-assembly, wall-swing, door-sweep and roof-lift checks. New release checks:
  - one Moomin on each floor;
  - closed clay meshes;
  - viewer mesh volume within 2 % of the estimate;
  - CAD solid within 2 % of the plain-union volume.
  - There are 31 checks, all passing.

## 15. Revision 5, continued (2026-10-14): lighter book, laser sheets, shared IDs

- **Requests:**
  - remove the furniture diagrams, part drawings, templates, rugs, textiles and books from the PDF, keeping only the example furniture renders;
  - remove the wallpaper and floor textures, keeping the palette, the stone plinth and the roof textures;
  - make the shingle strips single strips that can be cut out and glued to the round roof;
  - make the corner gussets less pointy and wider;
  - pack the 3 mm parts tightly on A4 sheets marked for laser cutting;
  - make the base from 6 mm plywood;
  - join the two half crossbars into one bar inside the window;
  - give identical parts one ID and one name.
- **Base:** B01 is `thickness.base` = 6 mm. `plinth.height` (B01 top to ground-floor top) is 66, so every floor stays at Z72 / 222 / 372 / 522, and PL1, DG1 and DB1 grow to 58 mm (DR4 to 57). B01 needs a 600 × 600 × 6 board (new 6 mm extra stock). The 8 mm stock drops from 4 to 2 extra 400 × 400 boards.
- **Gussets:** J01 has a blunt inner edge at radius 150 (half-width 10) and reaches 22 mm along each wall: 42.5 × 18.8, with 21.5 mm of glue face (was 17.5). The inner edge stays 5 mm clear of the rear posts. On the ground floor, the low gussets beside both jambs of each door sit 96 mm up, above the opening; previously only the hinge side moved. The divider notch follows the new inner edge.
- **Windows:** D04 and D05 are gone. Each window has D01 50 × 5 three times (bottom and top frame bars, plus the crossbar glued across the outside) and D02 5 × 60 three times (side bars, plus the middle bar inside the frame touching both horizontal bars).
- **Shared IDs:** `merge_identical()` in `model.py` folds identical house parts into the first ID. It compares thickness, outline, cut-outs and holes, and skips furniture, accessories and figures.
  - Each copy keeps its assembly label and its own paint (`instance.color`, used by CAD, renders, viewer and checks), and instance IDs are renumbered.
  - Walls are named by what they carry (for example "Fixed wall with windows"). W11 becomes a second W01 and W08 a second W06. The veranda treads VT1 become ET1, painted cream.
  - `derived.facets` maps facet 1–12 to its part, and the wall map shows facet numbers.
- **Laser sheets:** config `laser` makes all 3 mm parts laser sheets, with 2 mm spacing on a 0.5 mm grid.
  - An A4 sheet keeps its parts in the window 10–200 × 13–273, so its 1:1 template is a single page laid flush with the plywood.
  - The 387 mm roof panels need A3: PLY3-01 to PLY3-03 are A3, PLY3-04 is A4, and FUR3-01 is A4.
  - `nest.py` writes `<sheet>-laser.dxf` (layers CUT and ENGRAVE_IDS) and `-laser.svg` (red cuts, blue optional IDs). Laser sheets have no starter holes.
  - Their template pages carry an orange LASER CUT header. The trim carriers (TC01, `fabrication.py`) are removed.
- **Shingles:** `source/shingles.py`. Each course is one ring of tiles unrolled from the 12-facet cone (the development): straight on each panel, turned by the facet angle (14.7°) at each hip, where it is creased. Its ends are cut along the hips.
  - There are 42 courses at 9 mm, each with a 5 mm glue band, up to the R03 cap. Each course uses the widest whole number of panels per strip that fits the page (1, 2, 3, 4, 6 or 12), with seams staggered.
  - That gives 177 strips on 12 pages. Packing uses a skyline: alternate courses nest concentrically, single-panel strips stand on end, and each strip takes the first page with room.
  - Tiles are whole at the hips on one course and centred on them on the next. Labels "course·panel" sit in the hidden band.
  - Dormer and chimney cut-outs come from slicing their plates just above the panel surface.
- **Book:**
  - The appendix keeps the title render, five example rooms and the clay family: 7 pages (was 52).
  - The decor book keeps the palette, 2 stone pages and 13 shingle pages: 16 pages (was 51).
  - Templates: 128 pages (was 140). Complete PDF: 212 pages (was 305).
- **Checks:** 32. The trim-carrier check was dropped. New checks: identical house parts share one ID; every 3 mm part is on an A4/A3 laser sheet with laser files. The quantity rules now cover D01/D02 × 3 per window, 12 wall facets and ET1 × 6.

## 16. Revision 6 (2026-10-14): magnetic catches and stops, figures through the doors, build gates

- **Requests:**
  - a catch and a stop for the opening walls, magnetic, with four tiny neodymium magnets;
  - fail the build on errors, empty the output folders on each build, and one `make all`;
  - test the house against real plywood thickness;
  - say the paint must meet EN 71-3, with example makers and paint types;
  - check the figures against the door sizes and shrink the Moomins if they don't fit;
  - write the remaining review fixes into TODO.md, in priority order.
- **Catches:** MC1 is a 24 × 22 × 12 solid-wood block glued inside each shell, on W01 and W12, 12 mm from the front seam, with its top 0.5 mm under F02.
  - A D8 × 3 magnet in a blind D8.2 × 3.5 pocket in the F02 underside (H03, H04) holds a D10 × 1 steel disc in the block's top.
  - The disc sits 4 mm from the block's inner edge, so the pocket keeps 5.6 mm of plywood to the F02 edge. The block keeps 3.4 mm clear of the room divider.
  - Under the attic floor is the only place clear of the dividers, which run to the front seam on every storey; a seam-to-seam catch would have needed a notch in each divider.
- **Stops:** GP1 is a 20 × 20 × 96 solid-wood garden post on B01, glued and screwed from below (SC3, now 6 in all).
  - Each shell's hinge facet (W03, W10) meets its post at `wall_stop.angle` = 100°, 12 mm from the facet's far end, with a 0.3 mm gap.
  - The magnet is in the post's wall-side face; the steel disc is in a recess low on the facet's outer face.
  - The posts stand at about (±257, 0); their outer corners are at r 268 on the Ø560 base.
  - `views.open_angle` now comes from `wall_stop.angle`, so the open STEP, the renders, the viewer slider and the swing check (every 5° plus the stop itself) all open to 100°. The walls used to swing freely past 110°, until the right shell would have reached the veranda.
  - The steel discs ride on the walls, so no magnet pair can be fitted the wrong way round.
- **Drawer:** `plinth.drawer.direction` 180 → 150 (back-left). At 180° the left shell sweeps only over the drawer's pull-out corridor, so a left post would have blocked the drawer at any angle from 60° to 110°.
- **Figures:** heights move to config `figures.heights`: Moominpappa 80 → 65, Moominmamma 66 → 54, Moomintroll 56 → 46. The whole family shrinks by the same ratio.
  - At the old size, Mamma (43.7 mm across her handbag) and Pappa (43.6) did not pass the 40 mm room-divider doorways.
  - The rule: a figure must pass upright through every doorway, turned to its narrowest side, with `figures.door_clearance` 4 mm of width and 6 mm of height to spare. The exterior doors count as 50 × 90, the notch minus the threshold.
  - `derived.figure_fit` lists every figure–doorway pair; the narrowest margin is now Mamma's 4.2 mm. Clay drops from about 221 g to 120 g.
- **Build gates:**
  - `build_cad.failures()` stops the build after the CAD report, before nesting, on any overlap, swing, door, drawer, roof-lift, window, starter-hole, reopen or figure–door failure.
  - `rebuild.py` empties `output/` first (`--clean-only` does just that).
  - The `Makefile` has `all` (= `check` + `build` + `tolerance`), plus `clean`, `viewer` and `help`. `check` sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, because the venv's `moomin_local.pth` exposes another project's pytest plugins.
- **Thickness check:** `source/thickness_check.py` (FreeCAD) rebuilds each plywood part at the thin and thick end of `thickness_tolerance`, about its mid-plane: −0.5/+0.4 mm on 6 and 8 mm, ±0.3 mm on 3 and 4 mm. It then reruns `validate()`.
  - Overlaps between parts that touch at nominal size count as shifts.
  - An overlap where the design had a gap fails the check.
  - The first run found W05 against the veranda's rear columns C01 and header C10: a 0.3 mm gap that 6.4 mm sheets close. `veranda.wall_gap` is now 0.5.
  - I could not confirm the EN 315 tolerance formula, so the band is a plain measured spread and is not cited as a standard.
- **Book:** MG1 and SD1 hardware rows, epoxy in the supplies, and a new "Toy-safe paint (EN 71-3)" page. It lists paint types (water-based acrylic recommended, primer, hardwax oil, water-based stain, clear finish, what to avoid) and example products whose makers state EN 71-3. A new assembly step, "Fit the magnetic catches and stops", has a `catches` render. The drawer side and the open angle in the book text come from the model.
- **Checks:** 34 release checks. New: the magnets and stops, and figures through doorways. The F02 hole rule counts the pivot holes only. Two new model tests.
