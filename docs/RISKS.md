# Lanternwood House: Risk Assessment & Mitigation Record

This document records the structural, mechanical, chemical and child-safety risks of the CNC birch-plywood Lanternwood House, with emphasis on use by a **3-year-old**, and what revision 7 (2026-10-15) did about each. The original findings came from CalculiX FEA (`make stress`), Eurocode 5 hand checks and the toy-safety standards EN 71-1, EN 71-3, ASTM F963 and 16 CFR 1500/1501.

Every mitigation below is in the model and checked on each build: `make check` (model tests), `make all` (CAD collision, swing, door, drawer and roof-lift checks, release checks), `make stackup` (`source/stackup.py`, joint tolerance chains; `source/risk_audit.py`, tip-over, small parts, magnets) and `make stress` (FEA and fastener checks). Physical checks the CAD cannot make are a printed page in the instructions ("Dry-fit and safety checks").

> **Status:** this is a CAD-verified design, not a certified toy. Revision 7 removes or reduces every hazard listed; five residual risks remain and are marked **Residual**, and one open item (RISK-26).

---

## 1. Summary

| Risk | Was | Now | Residual |
| :--- | :---: | :---: | :--- |
| RISK-01 Magnet ingestion | 🔴 | 🔵 | Steel discs are flush-bedded, not enclosed |
| RISK-02 Tip-over | 🔴 | 🟡 | Free-standing it tips at 28.6 N at the eave; strap required |
| RISK-03 8 mm pinch gap | 🔴 | ✅ | — |
| RISK-04 Pointed finial | 🔴 | ✅ | — |
| RISK-05 Small parts | 🔴 | 🔵 | 28 glued pieces would be small parts if pulled off |
| RISK-06 Fragile window bars | 🟡 | ✅ | — |
| RISK-07 Clay figures | 🟡 | 🔵 | Baked polymer clay can still chip |
| RISK-08 Drawer pull-out | 🔵 | ✅ | — |
| RISK-09 Floor seam collapse | 🔴 | ✅ | — |
| RISK-10 Wall hinge screws | 🔴 | ✅ | — |
| RISK-11 Pillar slot notches | 🔴 | ✅ | — |
| RISK-12 Roof turn-button | 🔴 | ✅ (FEA rerun) | — |
| RISK-13 Door hinge screws | 🟡 | ✅ | — |
| RISK-14 Stop-post end grain | 🟡 | ✅ | — |
| RISK-15 Drawer jamming | 🔵 | ✅ | — |
| RISK-16 … RISK-26 (new, section 5) | — | see below | — |

---

## 2. Child safety (3-year-old play)

### RISK-01: Neodymium magnet ingestion — 🔴 → 🔵
- **Was:** four D8 × 3 N35 magnets bedded in epoxy in shallow pockets (flux index far above the 50 kG²·mm² limit of EN 71-1 4.23 / ASTM F963 4.38); epoxy alone holding them in.
- **Now:** every magnet sits in solid hardwood (MC1 catch blocks, GP1 posts), dropped into a blind bore from the **hidden** face against a **1 mm skin of wood** on the working face, and a glued D8 hardwood dowel plug closes the bore behind it (`config magnets.skin`, `.bore`, `.plug`). No magnet surface is exposed and none can be picked out without breaking the block. The plain steel discs now sit opposite (F02 underside, wall outer faces), so a magnet is never on a moving thin plate.
- **Verified:** `test_every_magnet_is_enclosed_in_solid_wood`, release check "Every magnet enclosed in solid wood", risk audit `magnets_enclosed`.
- **Residual:** the four steel discs (D10 × 1) are flush-bedded in epoxy. A disc alone is a small part but not a magnet hazard while the magnets stay enclosed. Pull-test them at dry fit (instructions page).

### RISK-02: Tip-over with the walls open — 🔴 → 🟡
- **Was:** the base touched the table only along its support cross, so it tipped about lines at 0.71 of the radius; no anchoring.
- **Now:** eight BP1 rim pads under the base edge (footprint edge 231 mm from the centre of gravity instead of about 180 mm), two steel ballast bars inside the plinth (0.75 kg), and an AB1 hardwood anchor block inside the fixed shell for an AT1 furniture anti-tip strap to the room wall.
- **Measured (risk audit, walls open, roof on):** 6.2 kg, centre of gravity 200 mm up. It tips free-standing at **28.6 N pushed at the eave (494 mm)**, **20.1 N at 700 mm** (15.6 N without the rim pads). The 3 mm parts (RISK-25) took 1.05 kg off: with 6 mm walls it was 7.25 kg, 33 N and 23.5 N. Two 150 × 40 × 15 mm ballast bars instead of × 8 bring it back to 31.8 N at the eave (6.86 kg), with 3 × 20 mm screws in place of 3 × 12.
- **Residual:** the RISK target (35 N at 700 mm, free-standing) would need about 4.6 kg more ballast. The book therefore makes the **anti-tip strap mandatory** for floor play and adds a 35 N tip test to the dry-fit page.

### RISK-03: 8 mm finger pinch gap — 🔴 → ✅
- **Now:** the divider front gap is **16 mm** (`partition.front_gap`), outside the 5–12 mm crush range of EN 71-1 4.10; the doorway moved back with it so its front post stays 12.6 mm wide. The closed front seam stays at about 1 mm (finger exclusion).
- **Verified:** `test_room_divider_front_gap_is_outside_the_pinch_range`, release check, stack-up chain "Opening wall past the floor edges".

### RISK-04: Pointed roof finial — 🔴 → ✅
- **Now:** FN01 is a smooth **D35 turned beech ball** on a D6 dowel (`config finial`); the cone is 7 mm lower so the overall height stays 838.4 mm.
- **Verified:** `test_finial_is_a_blunt_ball`, release check.

### RISK-05: Choking hazards from small parts — 🔴 → 🔵
- **Now:** glued door handles removed (recessed finger slot cut in each door); the loose miniature accessory set removed; window bars replaced by one 44 × 78 mm surround per window; chimney cap enlarged to 33.6 mm; the roof-pivot nuts locked with permanent threadlocker; the drawer is captive.
- **Audit:** `risk_audit.py` lists every fabricated piece that would fit the EN 71-1 small-parts cylinder if pulled off (28 profiles: hidden blocks, shims, stair treads, balusters, caps). All are glued over their whole face or hidden; the only loose pieces, the clay figures, do not fit.
- **Residual:** pull-test glued trim with 90 N at dry fit and recheck regularly (instructions).

### RISK-06: Fragile window bars — 🟡 → ✅
- **Now:** each window is four panes cut in the wall with a **solid 4 mm cross of wall** between them; the cream WF1 surround's cross is glued straight onto it, so no bar is unsupported. PET glazing inside. The same in the dormers (DM01 front + DM06 frame).

### RISK-07: Clay figures (toxicity, fragility) — 🟡 → 🔵
- **Now:** the book specifies a phthalate-free oven clay whose maker states EN 71 conformity, full baking, an EN 71-3 varnish and a five-drop test from 85 cm (discard any figure that chips); arms and ears stay pressed to the body. Every figure (six now) is checked against the small-parts cylinder (`clay.small_part`) and the doorways.
- **Residual:** polymer clay stays more brittle than turned wood. For a child who chews toys, turn the figures in beech instead (shapes in the book are a guide).

### RISK-08: Drawer pulled out onto feet — 🔵 → ✅
- **Now:** captive stop. A D6 hardwood dowel (DS1), pushed up through B01 after the drawer is in, rides in a slot in the drawer bottom; the drawer stops at 200 mm with 56 mm still in its guides. The CAD drawer check runs to the stop.

---

## 3. Structure, fasteners and FEA

### RISK-09: Floor seam collapse — 🔴 → ✅
- **Now:** both F01 and F02 halves join by CNC finger joints with 0.1 mm fit clearance and cutter relief in every inside corner (a router could not have assembled the old zero-clearance, sharp-cornered joint), plus four 6 × 12 mm strips under each seam (were 4 × 4). Each floor's front is now two pieces locked on the house axis by a CNC puzzle joint; stress test 4 loads one front piece on its half of the seam alone: 8.6 MPa against 19.7 MPa allowable.

### RISK-10: Wall hinge screw pull-out — 🔴 → ✅
- **Now:** 2.5 × 12 mm wood screws through the 3 mm wall with 7 mm of thread in hardwood A02 blocks, into D1.8 pilots (the previous drawing bored the blocks D2.5, which a 2.5 mm wood screw cannot grip). The screw is the longest stock length whose tip stays inside the 8 mm block, and the bolt option (M2.5 × 16 with a dome cap nut) keeps 3 mm of thread for the nut; both follow the wall thickness. Stress test 3 computes the capacity from the model: 129.2 N against 75.2 N (SF 1.72) for a 0.29 kg shell taken as 0.72 kg (with 6 mm walls: 2.5 × 16 screws, 147.7 N against 82 N, SF 1.8).

### RISK-11: Pillar slot notch splitting — 🔴 → ✅
- **Now:** R2 dogbone relief at all four corners of every pillar slot (stress test 5: SF 3.0).

### RISK-12: Roof turn-button fracture — 🔴 → ✅
- **Now:** each turn-button is two plies glued face to face, a 6 mm E08 under a 3 mm E09 (9 mm; the design uses only 3 and 6 mm sheets), with a 22 mm neck round the pivot tapering to 16 mm so it still clears the ring when turned; a D12 fender washer on each face; M3 × 30 pivot; one packing washer fewer keeps the 26.5 mm stack (3.5 mm of thread for the cap nut, checked across both plies' thickness bands by the stack-up).
- **FEA (`make stress`, same 32 N load at the tab tip):** 3 mm: 53.9 MPa, SF 0.37 → 6 mm: 15.7 MPa, SF 1.26 (a 26–30 mm neck does not help: 16–16.5 MPa) → 8 mm: 9.6 MPa, SF 2.04 → 6 + 3 mm glued (9 mm): 7.9 MPa, SF 2.49 (pass).

### RISK-13: Door hinge screw pull-out — 🟡 → ✅
- **Now:** 2.0 × 10 mm screws into 16 mm hardwood A03 strips; hole positions are now computed from the hinge axis (the old code placed them right only for 12 mm strips). Stress test 8: 76.8 N against 40 N per screw (SF 1.9).

### RISK-14: Stop-post end-grain stripping — 🟡 → ✅
- **Now:** each GP1 stands on two D4 dowels in blind B01 holes beside the SC3 screw, glued, with a felt dot on its face; the screw only holds it down. Stress test 7: 77 N dowel capacity against 39 N (SF 2.0).

### RISK-15: Drawer stick-slip jamming — 🔵 → ✅
- **Now:** waxed runners and slot; the stop dowel in its slot also centres the drawer; at the stop 56 mm stay in the guides. Stress test 9: jamming ratio 0.36 (< 0.7).

---

## 4. Verification commands

| Command | What it proves |
| :--- | :--- |
| `make check` | config rules, geometry invariants, magnets enclosed, dormers inside one panel, shells lifted, gap and finial rules, figures |
| `make all` | solid overlaps, wall swing 0–100°, six door sweeps, drawer to its stop, roof lift with catches released, windows clear of the veranda, 53 release checks, every piece in exactly one assembly step |
| `make stackup` | eleven tolerance chains at both ends of every thickness band; tip-over, small parts and magnet audit |
| `make tolerance` | the whole house rebuilt at the thinnest and thickest measured plywood |
| `make stress` | FEA of E08 and E03, Eurocode 5 fastener and joint checks, tip-over |

---

## 5. New risks found in this review

| ID | Risk | Status |
| :--- | :--- | :--- |
| RISK-16 | **Release build blocked by the model itself:** bookcases intersected the room dividers and each other, and the furniture contact audit still listed deleted furniture. Both failed the CAD checks in CI. | Fixed: bookcase builder rewritten; audit derives its families from the model |
| RISK-17 | **Dividers jam with thick floors:** they were exactly floor-to-ceiling; a 6.4 mm floor left −0.4 mm. | Fixed: 1 mm top play (`partition.top_gap`); stack-up chain |
| RISK-18 | **Finger joints not machinable as drawn:** zero clearance and sharp inside corners on a router. | Fixed: 0.1 mm clearance, R1.5 relief |
| RISK-19 | **Supplier PDF had no specification:** material, tolerances, process and edge rules were defined but never printed. | Fixed: specification, checklist, hand-drilling and file pages |
| RISK-20 | **DXF strictness:** R12 header with R2000 entities; strict importers reject the files. | Fixed: clean R12 writer, strict-read test |
| RISK-21 | **Underside machining and sub-2 mm drills** in the CNC files, which most shops will not do. | Fixed: drilled from the top or listed for the customer |
| RISK-22 | **Fixed walls rely on factory sheet ends** (420 mm, retained edges): out-of-square or short blanks tilt the roof. | **Open:** confirm 420.0 ± 0.3 square blanks or use 440 mm stock (TODO 23) |
| RISK-23 | **True 6 mm birch** can be hard to buy in A3; 6.5 / 9 mm boards fall outside the bands. 4 and 8 mm are no longer used: the design takes 3 and 6 mm only. | **Open:** measure; change config before cutting |
| RISK-24 | **Opening shells rubbing the plinth** (TODO 2). | Fixed: shells hang 1 mm above F00 |
| RISK-25 | **3 mm tower walls.** To save 6 mm plywood (17 → 11 A3 sheets, 3 mm 6 → 13, about 12 % of the plywood cost) the twelve walls, the room dividers, the corner braces, the drawer sides and back and the drawer back stop are 3 mm; the R05 roof jigs are 2 mm card. A 3 mm panel is 8 times less stiff in bending, its edge glue lines are half as thick and the house is 0.93 kg lighter. | Mitigated, see below |
| RISK-26 | **No floor ledges in the kit.** The twelve L01 rear floor ledges were removed: both F01 levels (and F02 besides its pillar tops) rest on metal supports fitted after production, which the model neither contains nor checks. | **Open:** set the supports so the floor undersides land at the drawn heights (the stack-up chains assume them), and load-test each floor at dry fit |

### RISK-25: 3 mm tower walls — mitigation and residual risk
- **Corner braces:** the 54 two-wall 6 mm gussets became wide 3 mm ribs. A J01 rib lies across a whole facet and ~75 % (~62 mm) onto both neighbours, only ~10 mm into the room, so one rib holds two corners; two bands per storey (low below the windows, high just under each floor / under F01B on the ground floor), with ribs spaced so long legs do not share an edge wall. No J02/J04 two-wall brackets; one leftover fixed-shell corner stays open; dividers are plain PT1 with no rear notches. The longer legs raise each corner's glue-line moment capacity (t × L² / 6) well above the six 6 mm gussets with 20 mm legs. Door-raised short legs (J03) keep ~20 mm reach where a raised rib would clear windows. Stress test 6: re-check after rebuild.
- **Drawer:** the box sides, back and back stop only slide and stop the drawer, so they are 3 mm (`thickness.detail`); the bottom, its stop slot and the DS1 dowel follow the 6 mm wider, 3 mm longer inside, and the 6 mm guide walls still end flush behind the back stop. The stone DR4 front and the DG1 guide walls, which carry F00, stay 6 mm. Stress test 9: jamming ratio unchanged (SF 1.94).
- **Other fixes:** the veranda deck, skirts, joists and stair stringers, which used the wall thickness, stay 6 mm (`thickness.structure`); the door threshold height follows the deck, not the wall; hinge screws follow the wall (RISK-10). Display furniture moved 2.3 mm clear of a rib.
- **Verified:** all CAD collision, wall-swing, door and drawer checks, 54 release checks, the thickness band rebuild, stack-up chains and all ten stress tests pass (rebuild after the J02/J04 removal).
- **Residual:** the window crosses are 4 × 3 mm until the WF1 surround is glued over them; the latch-side stile beside the W12 main door is 17.6 × 3 mm, held by the seam batten, the raised rib and the threshold; 3 mm panels warp more in storage, so keep them flat and glue the ribs soon after cutting. Tip-over: see RISK-02.

See [SUPPLIER-READINESS.md](SUPPLIER-READINESS.md) for the manufacturing review.
