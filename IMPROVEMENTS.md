# Lanternwood House Ornament & Architectural Improvements

This document catalogs potential decorative and architectural ornament additions to the wooden Lanternwood House model, celebrating literary craftsmanship and original architectural reference artwork.

---

## 0. The Literary Archive: Library, Scriptorium & Archive System (CNC-Fabricated)

This design framework reorients Lanternwood House around **libraries, books, manuscript creation, and archival cartography**—celebrating Elias's lifelong writing, cartography, and scholarly domesticity.

All proposed elements are strictly engineered for **flat-sheet 2.5D CNC machining and laser cutting** (using 3 mm, 4 mm, and 6 mm birch plywood). To ensure robust real-world production and playability, the design avoids fragile turned spindles, ultra-thin rungs (such as wire/string ladders), and non-machinable 3D spheres (such as solid globes). Instead, all pieces employ **interlocking mortise-and-tenon joints, slot-and-tab grids, half-lap comb joints, stepped solid profiles, and face-laminated reliefs**.

---

### Architectural Elevation & Floor Layout Schematics

```
                                      ▲ Z = 838.4 mm (Spire Apex)
                                     / \
                                    /   \
                                   /  *  \  ATTIC / CARTOGRAPHER'S GARRET (Z = 420.0 - 700.0 mm)
                                  /       \ · A-frame chart drafting trestle with chart shelf
                                 /  [===]  \ · Honeycomb hexagonal scroll & map bin
                                /  /|   |\  \ · Slotted archival document chest with curved ribs
                               /___||___||___\ · Interlocking triangular telescope observation pylon
                              /===============\ Z = 420.0 mm (Attic Floor Level)
                             |       | |       |
                             | [===] | | ==-== | FLOOR 2: ELIAS'S MEMOIR STUDY & SCRIPTORIUM (Z = 280 - 420 mm)
                             | |___| | | |===| | · Slanted bureau secretary desk with 3mm pigeonholes
                             |       | |       | · Portable desk-top writing slope with ink recess
                             |_______|_|_______| · Reader's daybed with integrated book-trough end boards
                             |=======| |=======| Z = 280.0 mm (Floor 2 Level)
                             |       | |       |
                             | [|||] | | [===] | FLOOR 1: THE GRAND CIRCULAR LIBRARY (Z = 140 - 280 mm)
                             | [|||] | | [ O ] | · Facet-fit perimeter bookcases (15° miter tabs)
                             |       | |       | · Sturdy 2-step library step-stool (oval hand-holes)
                             |_______|_|_______| · Hexagonal revolving bookcase table (cross-lap plates)
                             |=======| |=======| Z = 140.0 mm (Floor 1 Level)
                             |       | |       |
         +---VERANDA---------| [===] | | [T=T] | GROUND FLOOR: BOOKBINDERY & LITERARY PARLOUR (Z = 0 - 140 mm)
         | Outdoor reading   | [===] | |  | |  | · Heavy book press with slotted cross-screw wheel
         | lending cabinet & |       | |       | · 16-drawer card catalog cabinet with relief drawer faces
         | sturdy bench seat |_______|_|_______| · Trestle refectory reading table (6mm keyed tenons)
      ===+===================|=======| |=======| Z = 0.0 mm (Ground Floor Level)
      |   [===============================>    | STONE PLINTH ARCHIVAL DRAWER (Travel = 205.3 mm)
      +----------------------------------------+ · Slotted 3mm comb-joint flat-file grid for maps & folios
                                                 · Hidden false-bottom document cache with finger notch
      |<----------- Tower Base Diameter: 522.7 mm ----------->|
```

```
       TYPICAL FLOOR PLAN (Dodecagon Tower Ø 326.7 mm, 12 Facets W01–W12)
       Showing Library Zone Allocations & Wall Swing Envelopes

                         [Rear Fixed Wall Facet W01]
                       /-----------------------------\
                      /   FACET BOOKCASE CARRELS      \
                     /    [|||||||||||||||||||||]      \
     [Fixed W02]    /                                   \   [Fixed W12]
                   /   [Desk / Book Press]  Partition    \
                  |    +-----------------+    Divider     |
                  |    |  STUDY / WORK   |     PT1/PT2    |
     [Fixed W03]  |    +-----------------+        |       |  [Fixed W11]
                  |                               | [Door]|
                  |    Reading Salon / Lounge     | Swing |
     [Fixed W04]  |    [Revolving Carousel]       |-----> |  [Fixed W10]
                   \                             /       /
                    \                           /       /
      [WallLeft W05] \                         /       / [WallRight W09]
       (Hinged Shell, \                       /       /  (Hinged Shell,
        swings 100°)   \---------------------/       /    swings 100°)
                        [Front Facet W06] [Front W07/W08]
                         (Main Opening Reveal - Clear of all Fixed Joinery)
```

---

### CNC Machining & Fabrication Rules for Miniature Furniture

To ensure all elements cut cleanly on a desktop or light-industrial CNC mill (using 1.5 mm, 2.0 mm, or 3.175 mm [1/8"] flat endmills) or laser cutter:

1. **No Fragile Thin Profiles**: All vertical posts, legs, and ladders have a minimum cross-section of **4.0 mm × 4.0 mm** (or 6.0 mm in structural ply). Narrow wire-like rungs are replaced with solid interlocking step stringers.
2. **2.5D Mortise-and-Tenon Joinery**: All joints use slotted tabs with **dogbone / T-bone corner fillets** (radius $R \ge 1.0\text{ mm}$) to accommodate circular rotary cutters without manual chisel squaring.
3. **Layered Lamination (No Spheres)**: Round objects (such as globes or balusters) are engineered as **orthogonal interlocking slotted discs** or layered stepped concentric relief rings.
4. **Wall Swing Envelope**: All floor-mounted bookcases, desks, and presses placed against walls $W05$–$W09$ must honor the clearance swept by the opening front wall gussets (`J01`) between $0^\circ$ and $100^\circ$.

---

### Floor-by-Floor CNC Elements Planning

#### A. Plinth Archive Drawer ($Z = 0\text{ to }61.6\text{ mm}$, Travel $= 205.3\text{ mm}$)

The hidden sliding plinth drawer (`DR1`) is transformed into a museum-grade archival flat-file repository for oversized maps, architectural elevations, and rare folios.

| CNC Component | Material | Joinery & Construction | Function & Real-World Play Value |
| :--- | :--- | :--- | :--- |
| **Archival Flat-File Grid (`AF-01`–`AF-06`)** | 3 mm birch ply | Interlocking egg-crate half-lap comb slots (6 mm pitch). | Divides the drawer into 6 shallow compartments tailored for flat miniature parchment maps and accordion-folded Leporello books. |
| **Roll-Top Scroll Tubes Caddy (`AF-07`)** | 4 mm sides, 3 mm base | Scalloped cradle rack with 5 semi-circular saddles. | Holds rolled miniature maritime charts tied with linen thread; drops directly into the front drawer bay. |
| **Secret False-Bottom Document Cache (`AF-08`)** | 3 mm ply plate | Flush drop-in plate with a 6 mm circular CNC finger-pull hole. | Conceals a 6 mm secret cavity at the rear of the drawer for Elias's confidential correspondence and private journal. |

---

#### B. Ground Floor: Bookbindery & Literary Tea Parlour ($Z = 0\text{ to }140\text{ mm}$)

Replaces the standard culinary kitchen with an artisanal bookcraft workshop where bookbinding, hot tea, and lively philosophical debates occur simultaneously.

| CNC Component | Material | Joinery & Construction | Function & Real-World Play Value |
| :--- | :--- | :--- | :--- |
| **Heavy Screw Book Press (`BP-01`–`BP-05`)** | 6 mm base/top, 4 mm posts | Heavy slotted uprights; twin laminated 6 mm press platens; top cross-arm capped with an interlocking 4-point turn wheel. | Authentic tabletop bookbinder’s press used to flatten sewn signatures. Solid, chunky, and instantly recognizable. |
| **16-Drawer Card Catalog Cabinet (`CC-01`–`CC-07`)** | 4 mm carcase, 3 mm face | Box carcase with a 3 mm front plate routed with a 4×4 grid of faux drawer pockets and center mounting holes for brass pin-pulls. | The grand card index of the Lanternwood House library. Sits against the rear wall facet `W02`. |
| **Trestle Refectory Reading Table (`RT-01`–`RT-04`)** | 4 mm top (100×48 mm), 6 mm legs | Chamfered top resting on two slotted A-frame trestle legs, braced by a central stretcher with wedged tenon keys. | Broad communal reading table accommodating open folios, tea mugs, and stacked volumes. Replaces `K3`. |
| **Reading Bench with Book Trough (`RB-01`–`RB-04`)** | 4 mm seat & legs, 3 mm trough | Interlocking leg panels supporting a seat bench, with a sloped V-trough shelf slotted beneath for quick book storage. | Sits along the partition wall `PT1` opposite the refectory table. |
| **Wall-Mounted Paper Drying Rack (`PR-01`–`PR-03`)** | 3 mm birch ply | Slotted comb side brackets holding 4 horizontal paper-hanging slats. | Mounted above the bindery bench for drying marbled endpapers and fresh manuscript pages. |

---

#### C. Floor 1: The Grand Circular Library & Reading Salon ($Z = 140\text{ to }280\text{ mm}$)

The primary high-ceilinged library room, lined with modular perimeter shelving and study equipment.

| CNC Component | Material | Joinery & Construction | Function & Real-World Play Value |
| :--- | :--- | :--- | :--- |
| **Dodecagon Facet Perimeter Bookcases (`LB-01`–`LB-06`)** | 4 mm carcase, 3 mm shelves | Modular 5-tier shelving units whose side uprights are beveled at 15° to sit flush against wall facets `W01`, `W02`, and `W03`. Arched top pediments. | Forms a continuous wall of books following the round tower curvature without blocking door swings. |
| **Sturdy 2-Step Library Step-Stool (`SS-01`–`SS-04`)** | 4 mm ply sides & treads | A rigid pyramid step-stool with two broad 12 mm treads and CNC-routed oval finger hand-holes through both side stringers. | Replaces flimsy ladders. Allows figures to "reach" the high shelves; highly durable for handling. |
| **Hexagonal Revolving Book Carousel (`BC-01`–`BC-05`)** | 3 mm shelves & dividers, 6 mm pivot base | Two hexagonal tiered plates slotted together with 6 vertical radial dividers, pivoting on a 6 mm circular base boss. | Central 360° spinning book carousel holding 18 miniature volumes. Sits in the reading lounge center. |
| **Standing Reference Lectern / Reading Carrel (`LC-01`–`LC-04`)** | 4 mm legs, 3 mm sloped deck | Sloped 30° reading deck with a 3 mm retaining ledge, mounted on an interlocking pedestal with side book shelves. | Used for open dictionary or atlas display beside the window aperture. |
| **Scored Plywood Book Comb Rows (`BK-01`–`BK-12`)** | 3 mm birch ply | 48 mm long comb strips with CNC-engraved vertical grooves simulating varied book heights, widths, and titles. | Slide straight into bookcase bays in single sturdy blocks—eliminates handling dozens of loose miniature pieces while providing deep texture. |

---

#### D. Floor 2: Elias's Memoir Study & Scriptorium ($Z = 280\text{ to }420\text{ mm}$)

The dedicated creative workshop of the family memoirist, designed with scholarly comfort and functional writing surfaces.

| CNC Component | Material | Joinery & Construction | Function & Real-World Play Value |
| :--- | :--- | :--- | :--- |
| **Slanted Bureau Secretary Desk (`SC-01`–`SC-08`)** | 4 mm carcase, 3 mm interior | Drop-front angled writing slant with an interior egg-crate matrix of 6 miniature pigeonholes and 2 drawer pockets. | Elias's primary writing desk. Positioned facing the prominent 2nd-floor center window. |
| **Portable Desk-Top Writing Slope (`WS-01`–`WS-04`)** | 3 mm ply assembly | Sloped lap desk with finger-jointed corners, a shallow internal paper cavity, and an engraved circular inkwell recess. | Can sit on the secretary desk, dining table, or veranda rocking chair. |
| **Tiered Chapter Sorting Tower (`ST-01`–`ST-05`)** | 3 mm birch ply | Stepped vertical sorter with 4 ascending slots for sorting manuscript chapters and incoming letters. | Sits on the side credenza; keeps paper sheets organized without risk of bending. |
| **Scriptorium Daybed (`DB-01`–`DB-05`)** | 4 mm frame, 6 mm end-boards | Slatted daybed frame with high scrolled head- and foot-boards, featuring a built-in book trough along the back wall rail. | Replaces domestic bed `U1`; provides a philosopher’s reading couch for late-night inspiration. |
| **Plywood Quill & Ink Stand (`IS-01`–`IS-02`)** | 3 mm ply laminate | Stepped base with 2 small circular cutter recesses (inkpots) and an angled slot holding a flat-profile silhouette quill. | Chunky, durable desk accessory that will not roll away or snap. |

---

#### E. Attic: Cartographer’s Garret & Archival Observation ($Z = 420\text{ to }700\text{ mm}$)

Under the red spire roof, where sea navigation, astronomy, and rare document preservation converge.

| CNC Component | Material | Joinery & Construction | Function & Real-World Play Value |
| :--- | :--- | :--- | :--- |
| **A-Frame Chart Drafting Trestle (`DT-01`–`DT-05`)** | 4 mm board (75×50 mm), 6 mm A-legs | Wide sloped drafting board with twin A-frame trestle supports and a full-width lower shelf for rolled navigational charts. | Serves as the central mapmaking and astronomical plotting table under the dormer window. |
| **Honeycomb Scroll Storage Bin (`SB-01`–`SB-06`)** | 3 mm birch ply | Vertical open-topped hexagonal bin with interlocking 3-way slotted dividers, creating 7 vertical tubular scroll bays. | Stores rolled sea charts, celestial maps, and weather logs upright and accessible. |
| **Slotted Archival Document Chest (`AC-01`–`AC-07`)** | 4 mm box, 3 mm curved lid ribs | Sturdy rectangular box with tab-and-slot corners, topped with 3 curved segmental ribs holding an engraved barrel lid. | Storage for antique leather journals and heavy family ledgers. Replaces basic chest `N1`. |
| **Triangular Pylon Telescope Mount (`TP-01`–`TP-03`)** | 4 mm ply tripod pylon | Three interlocking vertical triangular pylons forming a broad, tip-resistant observation base for the telescope silhouette (`N3`). | Replaces flat pedestal `N4` with a three-dimensional, highly stable architectural pylon. |

---

## 1. Roof, Spire & Attic Exterior

| Ornament / Feature | Original DeAgostini Build | Current Project Status | Proposed Implementation & Fabrication |
| :--- | :--- | :--- | :--- |
| **Chimney Crown & Spark Cowl** | Cylindrical terracotta chimney pot topped with a decorative metallic **5-prong flower/palmette smoke cowl**. | Plain hollow rectangular box chimney (`CH01`–`CH04` + `E07` flat cap). | Interlocking 3 mm birch plywood petal/crown crest slotted into `E07`, or a 3D turned dowel with a flared palmette cowl. |
| **3D Turned Spire Finial** | Multitiered bulbous 3D turned spindle finial with a fine needle tip. | Flat 2D silhouette cutout in 4 mm ply (`FN01`). | Two interlocking orthogonal 3 mm laser pieces creating a 3D cross-profile, or a turned wooden finial. |
| **Attic Escape Rope Ladder** | Cord ladder with ~16–18 wooden dowel rungs draped from the dormer sill down to the veranda roof ridge. | Listed in `TODO.md #6`, not yet modeled. | 1 mm linen cord knotted/glued around 3 mm dowel rungs (cut to 14 mm width), anchored at the `DM01` dormer sill. |
| **Scalloped Eave Trim (Lambrequin)** | Continuous decorative fish-scale / scalloped fascia strip along the circular roof overhang rim. | Plain straight lower edges on faceted roof panels `R01`–`R12`. | Laser-cut 3 mm scalloped trim strips or scored/printed decor borders under the eave perimeter. |
| **Dormer Gable Bargeboard & Fretwork** | Contoured white bargeboard framing the dormer roof gable with an ornamental crest. | Plain angled triangular gable plate `DM04`. | Laser-cut 3 mm ornamental scrollwork bargeboard glued flush to the front of `DM04` and `DM05`. |

---

## 2. Window Casings & Façade Trims

| Ornament / Feature | Original DeAgostini Build | Current Project Status | Proposed Implementation & Fabrication |
| :--- | :--- | :--- | :--- |
| **Ornate Broken-Pediment Hood** | The prominent 2nd-floor center window features a **baroque curved broken pediment** with a central urn/finial. | Bare rectangular wall cutouts with no exterior frames or moldings. | Layered 3 mm laser-cut hood assembly with curved cyma scrolls and center crest mounted above window. |
| **Segmental & Triangular Window Hoods** | All other windows have arched (segmental) or peaked triangular pediment hoods. | Plain wall cutouts in `W01`–`W12`. | 3 mm laser-cut arched hoods glued directly above the window apertures. |
| **Projecting Window Sills & Aprons** | Molded projecting sills with sloped wash and underside drip grooves under every window. | No exterior sills. | 3 mm bevelled rectangular strips glued below each window cut-out. |
| **Glazing & Window Mullion Grids** | Molded white 4-pane and 6-pane divided window sashes over clear acrylic panes. | Open apertures through wall plywood. | 0.5 mm clear PET sheet sandwiched behind laser-cut 1.5–3 mm muntin cross grids. |
| **Vertical Seam Battens** | Blue tower features fine vertical wooden tongue-and-groove planking and joint battens. | Open V-grooves at the 12 polygon wall facet seams (~4.2 mm outer gap). | 3 × 8 mm half-round or flat battens glued over the 9 stationary facet seams (hides gaps and provides Scandinavian board-and-batten look). |
| **Storey Belt Courses (Belly Bands)** | Horizontal molded white or navy stringcourses defining floor levels on the exterior. | Continuous smooth vertical facets. | Thin 2 × 4 mm horizontal trim strips circling the tower at floor heights $Z=140, 280, 420\text{ mm}$. |

---

## 3. Entrances & Veranda Ornaments

| Ornament / Feature | Original DeAgostini Build | Current Project Status | Proposed Implementation & Fabrication |
| :--- | :--- | :--- | :--- |
| **Front Entrance Gable Cartouche** | Carved relief medallion / sunburst fretwork insert in the entrance pediment apex. | Flat triangular plywood panel `GD01`. | Laser-etched or pierced 3 mm filigree insert mounted within the gable triangle. |
| **Front Porch Spindle Columns** | Turned classical baluster columns flanking the entrance steps supporting the canopy. | Canopy cantilevers directly from the wall facet without support posts. | Pair of miniature shaped columns mirroring the veranda posts (`C01`) resting on step stringers. |
| **Veranda Spandrel / Corner Brackets** | Delicate gingerbread fretwork brackets / scroll spandrels where columns meet roof headers. | Square $90^\circ$ joints between columns `C01` and headers `C02`/`C03`. | 3 mm laser-cut openwork corner brackets glued beneath the header beams. |
| **Veranda Stair Handrail & Newel Post** | Shaped newel post with ball cap and sloped balustrade down the side steps. | Steps `VS3`/`VT1` have open outer edges without railings. | Angled handrail with matching baluster `C09` and shaped newel post along outer stair stringer. |
| **Veranda Spindle Rocking Chair** | White Victorian spindle rocking chair with curved runners resting on the veranda deck. | Geometric block chair (`PC01`–`PC03`). | Curved rocking chair runners and shaped back spindles cut from 3 mm laser plywood. |
| **Paneled Front Door Relief** | Raised diagonal coffered panels (herringbone/chevron) with brass knocker and escutcheon plate. | Flat 4 mm door panel `E01` with simple block handle `E02`. | Laser-scored or double-layered herringbone panel facing with a filigree ring knocker. |

---

## 4. Foundation, Plinth & Exterior Accessories

| Ornament / Feature | Original DeAgostini Build | Current Project Status | Proposed Implementation & Fabrication |
| :--- | :--- | :--- | :--- |
| **Cellar Bulkhead Hatch Door** | Slanted rustic wooden cellar trapdoor with black iron strap hinges set into the stone foundation. | Plain stone plinth covering the hidden drawer bay. | Applied 3 mm timber doors with etched plank grooves and faux strap hinges on drawer face or side plinth panel. |
| **Kitchen Back Door & Woodpile Shed** | Rear kitchen door canopy, 4-riser stair, and adjacent lean-to woodshed with stacked logs. | Absent. Only main entrance and veranda door exist. | Lean-to shelter with pitched roof on kitchen facet, housing laser-cut stacked wood rounds. |
| **Exterior Carriage Lanterns** | Hanging black coach lanterns under porch eaves and beside entrance portals. | None. | Pierced 3 mm lantern silhouettes or miniature 3D lanterns mounted on wall brackets. |
| **Doorway Weather Barometer / Thermometer** | Tove Jansson's signature vertical outdoor thermometer mounted on the door frame. | None. | Printed or etched miniature gauge strip applied beside front door casing. |

---

## 5. Interior Architectural & Built-in Ornaments

*(Visible when the hinged walls swing open)*

| Ornament / Feature | Original DeAgostini Build | Current Project Status | Proposed Implementation & Fabrication |
| :--- | :--- | :--- | :--- |
| **Attic Gothic Roof Truss** | Openwork pierced Gothic fretwork truss with arched openings under the roof apex. | Open hollow cone under the roof panels. | Laser-cut 4 mm decorative openwork tie-beam and king-post arch resting on attic floor cleats. |
| **Swedish Tiled Stove (*Kakelugn*)** | Tall cylindrical/semicircular tiled heating stove with crown moulding and brass damper door. | Simple cubic block box stove `V6`. | Multi-tiered stepped column stove with brass hatch in 4 mm ply or thermo-clay. |
| **Ceiling Chandeliers & Pendants** | Glass/brass multi-arm chandelier in dining room; hanging star lantern in Papa's study. | Plain bare plywood ceiling undersides. | Hanging filigree star/candelabra silhouettes suspended from floor undersides. |
| **Kitchen Masonry Hearth & Plate Rack** | Bell-hood chimney breast over stove; wall-mounted plate delft rack with miniature plates. | Open ground floor kitchen partition. | Curved mantel hood and slotted plate rack in 3 mm ply. |
| **Doorway Architraves & Interior Leaves** | Molded casings around interior room doorways with operable paneled door leaves. | Open rectangular cutouts in dividers `PT1`/`PT2`. | 3 mm door leaves with cotton-tape hinges and molded casing trim. |

---

## 6. Implementation Priority Matrix

```
Already in the cut kit (revision 7+):
  ✓ Window surrounds WF1 (frame + sill + triangular hood) + PET glazing
  ✓ Attic rope ladder RL1 (one 3 mm piece on the seam batten)
  ✓ Vertical exterior seam battens BT1–BT4
  ✓ Cellar hatch HC1, back-door canopy, woodpile WP1–WP3
  ✓ Room door leaves PD1
  ✓ Kakelugn / chandelier / bathtub as display-only prints (not plywood)

Still high visual impact on 3 mm / 6 mm plywood only:
  1. Chimney spark-cowl crown on E07
  2. Scalloped eave lambrequin under D03
  3. Veranda corner spandrels + stair handrail
  4. Entrance gable cartouche in GD01 + porch posts under the canopy
  5. Broken-pediment upgrade for the prominent 2nd-floor window
  6. Door panel relief overlays + dormer bargeboard fretwork
  7. Storey belt courses + carriage lantern silhouettes
```

---

## 7. Pre-print readiness review (2026-03-26)

Review of the current DXF cut package against the classic blue round tower reference (red cone roof, stone plinth, side veranda, entrance canopy, dormers, rope ladder). Goal: keep only **3 mm and 6 mm birch plywood**, stay cuttable on laser/CNC, and make the finished house read clearly as that house.

### 7.1 Consistency status (CAD / files)

| Check | Result | Source |
| :--- | :--- | :--- |
| Model / config / part-ID / stock / supplier / DXF R12 tests | pass | `pytest` core suite |
| Closed assembly collisions | none | `cad-validation.json` |
| Wall swing 0–100°, six door sweeps, drawer 200 mm, roof lift | clear | same |
| Thickness bands (3 ±0.3, 6 −0.5/+0.4) | pass, no lost clearances | `thickness-tolerance.json` |
| Joint stack-up chains (9) | all pass | `stackup.json` |
| Release validation (incl. supplier cut DXF) | all pass | `release-validation.json` |
| Tip-over / magnets / small parts audit | pass with residuals | `risk-audit.json` |
| Nesting bounds + 3 mm lanes | pass on every sheet | `nesting.json` |

**Current cut stock (authoritative nesting, not older docs):**

| Thickness | Sheets (A3 297×420) | Cut pieces | Outer util (avg) |
| :---: | :---: | :---: | :---: |
| 3 mm | 12 | 209 | ~72 % |
| 6 mm | 9 | 54–56 | ~60 % |
| **Total** | **21** | **~265** | |

Supplier file: `output/Lanternwood-House-Supplier-Cut.dxf` — DXF R12, layers `CUT_3MM` / `CUT_6MM`, cutting paths only.

### 7.2 Doc / model drift to fix before quoting

These do not fail the automated gates, but they will confuse a shop or a future rebuild:

1. **Sheet count in docs is stale.** `TODO.md` / `SUPPLIER-READINESS.md` still say 23 sheets (12×3 + 11×6). Nesting and the supplier cut file are **21** (12×3 + 9×6).
2. **Veranda deck thickness.** `architecture.py` hard-codes `deck_t, skirt_t = 3, 3` for `E03` / `VS1` / `VS2`. `RISKS.md` still says the deck stays 6 mm. The E03 stress-test helper still labels the material as “6 mm” while the part is 3 mm. Decide: keep 3 mm + underside cleats, or restore `E03` to `thickness.structure` (6 mm) before cutting.
3. **Divider front gap.** `partition.front_gap` is **0.0** (closed seam / finger exclusion). `RISKS.md` still describes a 16 mm gap. The pinch test only forbids 5–12 mm, so 0 passes — but the safety narrative and the model disagree. Align the text with the model (or restore the 16 mm gap if that is still intended).
4. **Factory-edge walls (blocker B1)** and **true 6 mm availability (blocker B2)** remain open: confirm with the shop before ordering. See `docs/SUPPLIER-READINESS.md`.

### 7.3 What already reads as the Moomin house

From the closed / veranda / open renders against the reference:

- Blue dodecagon tower on a green lawn disc and stone plinth with hidden drawer
- Red conical roof with fish-scale shingle decor, two dormers, chimney, blunt ball finial
- Side veranda: white twin-ply columns, railings, balusters, hipped red roof, stairs
- Main entrance canopy + gable, back door with lean-to and woodpile, faux cellar hatch
- Cream window surrounds with sill and triangular hood, four-pane crosses left in the wall
- Nine blue seam battens, rope ladder from veranda roof to the dormer eave
- Opening front shells, room dividers with door leaves, clay family figures

That silhouette is already recognisable. The remaining gap is **ornament density**: the reference is rich in gingerbread, curved pediments, chimney cowl, scalloped eaves and door relief; the kit is still mostly clean planes with one-piece surrounds.

### 7.4 Highest-value extra parts (3 mm / 6 mm only)

All proposals stay flat-sheet: interlocking tabs, face lamination, or glue-on overlays. No 4 mm stock. Prefer nesting into existing 3 mm sheet hollows so sheet count stays at 21 or grows by at most one A3.

| Priority | New parts | Thickness | How it improves fidelity | Notes |
| :---: | :--- | :---: | :--- | :--- |
| **P1** | `CH05` chimney spark-cowl / 5-petal crown, slots into `E07` | 3 | The reference chimney ends in a flower/palmette cowl; flat `E07` is the most obvious missing silhouette on the skyline | Keep outline ≥4 mm min feature; glue or slot on cap |
| **P1** | `D04` scalloped lambrequin strips under each `D03` fascia (12) | 3 | Continuous fish-scale / scallop trim under the eave is a strong Moomin read | Same length family as `D03`; paint cream |
| **P1** | `C13` veranda corner spandrels (8–12 openwork brackets) | 3 | Square column–header joints look unfinished next to the reference gingerbread | Glue under `C02`/`C03` at each column |
| **P2** | `VR1`/`VR2` veranda stair handrail + newel (match `C09` language) | 3 | Open stair edge is a clear miss on the veranda hero angle | Keep section ≥4×3; glue to `VS3` |
| **P2** | `GD05` pierced sunburst / cartouche inset for `GD01` | 3 | Entrance pediment is flat; reference has a medallion in the gable | Drop into a pocket cut in `GD01`, or face-glue |
| **P2** | `EP1` entrance porch posts (pair) under the canopy | 3×2 laminate or 6 | Canopy currently cantilevers; reference has classical posts on the step stringers | Seat on `ES1` / tread stack |
| **P2** | `WF2` broken-pediment hood (1–3 featured windows) | 3 layered | Simple triangular `WF1` hoods are weak vs the baroque centre window | Keep `WF1` for the rest; swap only the hero windows |
| **P3** | `E01A` door panel relief overlays (herringbone / coffer) | 3 | Flat doors; reference has diagonal raised panels | Face-glue; finger slot stays clear |
| **P3** | `DM07` dormer bargeboard fretwork on `DM04` | 3 | Plain dormer gables | Cream, glued to gable front |
| **P3** | `BC1` storey belt courses at Z≈140 / 280 / 420 | 3×4 strips | Horizontal stringcourses break the tall blue shaft | Stop at hinge seams; do not bridge moving shells |
| **P3** | `LN1` carriage-lantern silhouettes on `GP1` posts / porch | 3 | Reference hangs coach lanterns under eaves | Optional; already hinted in garden renders |
| **P3** | Engraved / printed thermometer strip beside front door | — | Signature Jansson outdoor gauge | Decor PDF, no new plywood |

**Structural add-ons worth nesting with the beauty parts:**

| Part | Thickness | Why |
| :--- | :---: | :--- |
| `E03C` deck underside cleats (2–4) under the front lip of `E03` | 6 or 3×2 | Stress note for the 3 mm deck: reinforce if deck stays 3 mm |
| Fit-test coupon sheet: finger joint + pillar slot + blind pocket + 3/6 thickness tags | 3 + 6 | Cut first; validate kerf and thickness before the full run |

### 7.5 Corner ribs revised for print (2026-03-26, updated)

Implemented in the model:

| | Before (narrow ribs) | After (print kit) |
| :--- | :--- | :--- |
| Depth into the room (`RD`) | ~17 mm | ~10 mm |
| Leg onto each edge wall (`GR`) | ~30 mm (~39 %) | ~62 mm (**~75 %**) |
| Two-wall brackets | J02 / J04 fill leftover corners | **Removed** — one fixed-shell corner stays open |
| PT1 rear notches | Cleared J02 at the divider corner | **Removed** — plain PT1 doorway panel |
| Bands per storey | 1 (≥10 mm above floor) then briefly 1 again | **2** — low below windows + high under each floor (under F01B on the ground floor) |
| Piece count | 30 → 16 with J02/J04 | **23** three-wall ribs (J01×22, J03×1) |

Rib midpoints are spaced so 75 % legs do not share an edge wall. Door-raised short legs (`J03`) stay ~20 mm when a raised rib clears windows; a raised rib that would cross a window middle is skipped (no J04 split).

### 7.6 What not to change for this print

- **Ball finial `FN01`** — keep the blunt D35 ball (toy safety). A pointed spire matches the reference but reopens RISK-04.
- **Cord rope ladder** — keep one-piece `RL1` plywood; cord rungs fail small-parts and roof-lift rules.
- **Wall thickness 3 mm** — already mitigated with long `J01` ribs; reverting walls to 6 mm costs several sheets and tip-over mass changes.
- **Display-only furniture / garden** — leave off the cut DXF; they are prints or clay.

### 7.7 Suggested sequence before sending DXFs

1. Measure the shop’s actual 3 mm and 6 mm birch; update `thickness` / bands if needed; rebuild.
2. Resolve B1 (420 mm factory ends vs all-sides cut) with the shop.
3. Decide `E03` 3 vs 6 mm and align `RISKS.md` + stress-test labels.
4. Align `front_gap` documentation with `config.json`.
5. Optionally add P1 ornament parts and re-nest (target: still ≤22 A3 sheets).
6. Ask for a fit-test coupon cut first; then release the full `Supplier-Cut.dxf` + supplier PDF.
