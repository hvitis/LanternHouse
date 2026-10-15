# Moominhouse Ornament & Architectural Improvements

This document catalogs potential decorative and architectural ornament additions to the wooden Moominhouse model, derived from a detailed comparison with the official **DeAgostini / Fanhome *Moominhouse*** subscription build (*週刊 ムーミンハウスをつくる*) and original reference artwork.

---

## 0. The Literary Moominhouse: Library, Scriptorium & Archive System (CNC-Fabricated)

This design framework reorients the Moominhouse around **libraries, books, manuscript creation, and archival cartography**—celebrating Moominpappa’s lifelong memoir-writing and scholarly domesticity.

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
                             | [===] | | ==-== | FLOOR 2: PAPPA'S MEMOIR STUDY & SCRIPTORIUM (Z = 280 - 420 mm)
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

The hidden sliding plinth drawer (`DR1`) is transformed into a museum-grade archival flat-file repository for oversized maps, architectural elevations, and rare Moominvalley folios.

| CNC Component | Material | Joinery & Construction | Function & Real-World Play Value |
| :--- | :--- | :--- | :--- |
| **Archival Flat-File Grid (`AF-01`–`AF-06`)** | 3 mm birch ply | Interlocking egg-crate half-lap comb slots (6 mm pitch). | Divides the drawer into 6 shallow compartments tailored for flat miniature parchment maps and accordion-folded Leporello books. |
| **Roll-Top Scroll Tubes Caddy (`AF-07`)** | 4 mm sides, 3 mm base | Scalloped cradle rack with 5 semi-circular saddles. | Holds rolled miniature maritime charts tied with linen thread; drops directly into the front drawer bay. |
| **Secret False-Bottom Document Cache (`AF-08`)** | 3 mm ply plate | Flush drop-in plate with a 6 mm circular CNC finger-pull hole. | Conceals a 6 mm secret cavity at the rear of the drawer for Moominpappa’s confidential royal correspondence and private diary. |

---

#### B. Ground Floor: Bookbindery & Literary Tea Parlour ($Z = 0\text{ to }140\text{ mm}$)

Replaces the standard culinary kitchen with an artisanal bookcraft workshop where bookbinding, hot tea, and lively philosophical debates occur simultaneously.

| CNC Component | Material | Joinery & Construction | Function & Real-World Play Value |
| :--- | :--- | :--- | :--- |
| **Heavy Screw Book Press (`BP-01`–`BP-05`)** | 6 mm base/top, 4 mm posts | Heavy slotted uprights; twin laminated 6 mm press platens; top cross-arm capped with an interlocking 4-point turn wheel. | Authentic tabletop bookbinder’s press used to flatten sewn signatures. Solid, chunky, and instantly recognizable. |
| **16-Drawer Card Catalog Cabinet (`CC-01`–`CC-07`)** | 4 mm carcase, 3 mm face | Box carcase with a 3 mm front plate routed with a 4×4 grid of faux drawer pockets and center mounting holes for brass pin-pulls. | The grand card index of the Moominhouse library. Sits against the rear wall facet `W02`. |
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

#### D. Floor 2: Moominpappa’s Memoir Study & Scriptorium ($Z = 280\text{ to }420\text{ mm}$)

The dedicated creative workshop of the family memoirist, designed with scholarly comfort and functional writing surfaces.

| CNC Component | Material | Joinery & Construction | Function & Real-World Play Value |
| :--- | :--- | :--- | :--- |
| **Slanted Bureau Secretary Desk (`SC-01`–`SC-08`)** | 4 mm carcase, 3 mm interior | Drop-front angled writing slant with an interior egg-crate matrix of 6 miniature pigeonholes and 2 drawer pockets. | Moominpappa’s primary writing desk. Positioned facing the prominent 2nd-floor center window. |
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
High Visual Impact / Low Complexity:
  1. Window architraves, sills & broken-pediment hoods
  2. Attic rope ladder & chimney spark cowl
  3. Vertical exterior seam battens (board-and-batten look)

Medium Complexity / High Play Value:
  4. Veranda corner spandrels & stair handrail
  5. Cellar bulkhead hatch door & kitchen woodshed
  6. Attic Gothic roof truss

Detailed Interior Finishes:
  7. Swedish tiled stove (kakelugn)
  8. Hanging chandeliers & interior door leaves
```
