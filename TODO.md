# Lanternwood House — TODO

Open improvements to the house, **in priority order**. Safety and fit come first, then play value, extras, and the book and tooling.

Already done:
- stone plinth with a hidden drawer; room dividers with doorways; veranda at ground-floor level, with stairs; entrance steps (revisions 3 and 4);
- steeper roof and printable fish-scale shingles, cut per course so they wrap the round roof; new cover (revisions 3 and 4);
- thermo-clay Rowan family (Elias, Mira, Ada and Theo), one per floor; 3 mm parts on A4 / A3 laser sheets; identical parts share one ID (revision 5);
- magnetic catches and garden stop posts for the opening walls (four magnets), drawer turned to 150°, smaller figures that pass every doorway, EN 71-3 paint guidance, build gates, `make all` and the plywood thickness check (revision 6);
- revision 7 (2026-10-15): two lower, bigger dormers (over W06 beside the veranda, next to the chimney, and over W12 on the opposite side), rope ladder, one-piece window surrounds with glazing, seam battens, back door with canopy and woodpile, room door leaves, Rowan family figures, LED provisions, cellar hatch, extra furniture and a garden scene, and every item of RISKS.md mitigated (see there). Details per item below.

## 1. Before the first build: safety and fit

1. - [ ] **Physical checks at dry fit.** CAD proves clearances, not strength. *The checks are now a printed page in the instructions ("Dry-fit and safety checks"); they still have to be done by hand.*
   - Measure every plywood sheet. If any is outside `thickness_tolerance`, update `thickness` or the band in `source/config.json`, then run `make all`. `make stackup` shows the joint chains that matter.
   - Press-test the cantilevered front edge of each floor.
   - Check how much F00 bends over the drawer bay under the rear-frame foot near the drawer.
   - Push each opened shell hard against its GP1 post (now on two dowels, felt dot on its face).
   - With both walls open, push sideways at the eave with 35 N: the house must not lift a rim pad. Fit the anti-tip strap.
   - Pull each catch block and post with pliers after the epoxy has cured. No magnet may show or move.
2. - [x] **Lift the opening shells 1 mm off F00.** `shell_lift` (1 mm): both leaves of every wall hinge, the A02 blocks and the opening shells' gussets, doors and trim sit 1 mm higher; the shells clear the plinth top and keep 1 mm under the roof ring. Checked by `test_opening_shells_hang_clear_of_the_plinth` and the stack-up.
3. - [ ] **A3 CNC supplier confirmation.** *Prepared, needs the shop:* the supplier PDF now prints its specification, a "confirm before quoting" checklist, the features the customer drills by hand, and the files to send; see [docs/SUPPLIER-READINESS.md](docs/SUPPLIER-READINESS.md) for the open blockers (420 mm factory edges, process per thickness).
4. - [ ] **Clay density.** The clay estimate assumes 1.7 g/cm³. Weigh a block of the clay you buy, and set `figures.clay.density` if it differs. *(Physical; listed on the dry-fit page.)*
5. - [x] **Drawer stop.** Decided: captive. A D6 hardwood dowel (DS1), pushed up through B01 after the drawer is in, rides in a slot in the drawer bottom and stops it at 200 mm (`plinth.drawer.stop`, travel 200). The slot also keeps the drawer running straight.

## 2. The most recognisable missing details

6. - [x] **Rope ladder from the attic dormer to the veranda roof.** The dormer moved to the panel over W06, between the veranda and the chimney (the chimney stays). The ladder (RL1) is one 3 mm plywood piece glued flat on the seam batten at the W06 / W07 corner, from the veranda roof up to the eave beside the dormer: no cord, no loops, no loose rungs. It is part of the house, so the roof lifts clear of it (roof-lift check).
7. - [x] **Window detail.** The wall keeps a solid 4 mm cross between four panes (RISK-06); one WF1 surround per window combines frame, sill band and pediment hood in one 44 × 78 mm piece (too big to swallow); GZ1 / GZ2 clear PET glazing inside. Dormers get a DM06 frame and GZ2 glazing.
8. - [x] **Exterior seams and plank texture.** Nine 3 × 8 mm battens (BT1 × 9, 411.5 mm) over the seams that do not move (single uniform element based on the longest seam under the fascia). Scored plank grooves stay optional (not modelled).

## 3. Play value

9. - [x] **Thermo-clay figures.** The Rowan family (Elias, Mira, Ada, Theo) in `source/clay.py`; Theo lives in the attic. Every figure passes every doorway and none fits the small-parts cylinder (`clay.small_part`).
10. - [x] **Room door leaves.** PD1, 3 mm, on two cotton-tape strips at each doorway's rear jamb, swinging into the right-hand room; the door-sweep check covers them and figures are placed clear of their swing.
11. - [x] **Back door.** E04 on W09 (kitchen side, 38 mm notch, hinged on its clockwise jamb to clear the wall-hinge blocks), lean-to canopy GD03 on GD04 brackets, 4-riser stone steps, and a woodpile shelter (WP1–WP3) beside it; clear of the GP1 posts, the veranda and the drawer.
12. - [x] **Optional LED lighting.** D6 wire holes through F00, both F01 levels and F02 behind the left rear pillar; wire route to the plinth bay behind the drawer back stop (adult access only, no coin cells; BH1 hatch cover removed).
13. - [x] **Faux cellar hatch.** HC1, an arched plank door glued flat on the plinth panel beside the drawer.

## 4. Extras (renders and the appendix)

14. - [x] **More example furniture (renders only):** tiled stove (kakelugn) and chandelier in the living room, a footed bathtub, an attic bed and desk. The furniture contact audit now derives its families from the model (the old list still named deleted furniture and failed).
15. - [x] **Garden extras.** Well, bathing hut, rowing boat, small bridge, mailbox and garden tent in a display-only `Garden` group on the lawn beyond the base, plus a lantern on each GP1 post; new `garden` render. (There are no FUR cutting sheets any more: all furniture is display-only.)

## 5. Book and tooling

16. - [x] **Assembly-step coverage check.** `source/steps.py` assigns every placed piece to one step; each step page prints its parts and quantities, and `verify.py` fails if a piece is in no step or in two.
17. - [x] **SC3 section for the stop posts.** Added to the screw page: SC3 through B01 into the post's end grain, with the two D4 dowels that take the side load.
18. - [x] **No-laser option for the 3 mm trim.** A book page lists every thin strip part by bought strip size (3 × 8 fascias and battens, 3 × 4 surround frames) with lengths and totals.
19. - [ ] **Shingle paper.** *Tried, no saving yet.* A raster first-fit packer (FFT overlap search, drops strips into the hollows under arcs) now competes with the skyline packer and the book takes the better one. Both give 10 pages for the current 138 strips (was 177 strips on 12): the area alone would fit 5.8 pages, but the two-panel eave arcs are nearly as wide as the page. Fewer pages would need a different split of the low courses or landscape pages with a different strip split.
20. - [x] **Joint-aware thickness check.** `source/stackup.py` (`make stackup`) evaluates eleven assembly chains at both ends of every thickness band (divider play per storey, turn-button gap, BL1 thread, pillar slots, gusset notches, moving clearances, drawer under the seam strip). It found the dividers were exactly floor-to-ceiling, so a thick floor jammed them: they now have 1 mm top play (`partition.top_gap`).
21. - [x] **Clean Python environment.** The `.pth` that pulled another project's site-packages into `.venv` is gone; `requirements-dev.txt` (now with `ezdxf` for the strict DXF test) is installed, and neither `make check` nor CI needs `PYTEST_DISABLE_PLUGIN_AUTOLOAD`.
22. - [x] **CI and GitHub Pages.** `.github/workflows/ci.yml` runs the model tests and browser checks, then deploys the static viewer from `main` (not from tags: the `github-pages` environment rejects them). `release.yml` builds everything on a `v*` tag, keeps the check reports as an artifact when the build fails, and creates or updates the release.

## 6. Next

23. - [ ] **Walls without factory edges.** The fixed walls use the full 420 mm A3 length, so their ends are the sheet's factory edges. Offer a `wall_height` of 400 mm (cut on all sides) or 440 mm stock if the supplier cannot guarantee square 420.0 mm blanks.
24. - [x] **Ring and floor sections.** The roof eave reinforcement ring is split into 2x3 mm thickness and divided into three 120-degree pieces per layer (staggered by 60 degrees into a rigid composite ring without seam bridges, eliminating 6 mm plywood for the roof ring). `nest.py` places parts by their true footprint, so small parts fill hollows, and it keeps the best part orders run through `make stock` (2026-10-15).
25. - [ ] **Free-standing stability.** Free-standing with the walls open the house tips at about 27 N at the eave (19 N at 700 mm) per the current risk audit. The anti-tip strap is required; more ballast would be needed to stand 35 N at 700 mm on its own.
26. - [x] **3 and 6 mm plywood only** (2026-10-15). 4 and 8 mm were hard to buy and cost two more sheet types. Doors, veranda railings, the drawer bottom and the ground-floor and roof-ring seam strips are now 3 mm; the pillars (6.6 mm floor openings) and the supports and pads under the base (base lift 6 mm) are 6 mm; each roof turn-button is a 6 mm E08 and a 3 mm E09 ply glued into 9 mm (one 6 mm ply fails stress test E08). The schema and `config_check.py` reject any other thickness.
27. - [x] **Lowered roof height by 40 mm** (2026-10-15). Roof height decreased by 4 cm (finished total height 798.4 mm, roof peak 754.4 mm, roof cone height 266.8 mm) with the Round green base kept at D522.7 mm so the veranda and entrance stairs keep full ground support. Roof triangular panels (R01, R06), support cleats (R04), dormers (DM01–DM06), chimney sloped sides (CH1–CH4), angle jigs (R05), and fish-scale shingles all recalculated and verified clash-free in the FreeCAD CAD solid model.
28. - [x] **Laser spacing and grade 2 birch** (2026-10-15, SUP-004). Both thicknesses now use 3 mm lanes. Every sheet specifies grade 2/2 birch. The saved supplier profile selects grade 2 only. Router cutting requires wider lanes and new nesting.

## 7. Corner ribs (done for print)

35. - [x] **Shallower, wider J01 ribs** (2026-03-26). Depth into the room ~10 mm (was ~17); legs ~75 % of each edge wall (~62 mm, was ~30); ribs spaced so long legs do not share an edge wall.
36. - [x] **Drop J02/J04; high band under F01B** (2026-03-26). Removed two-wall brackets and the PT1 rear notches they needed. Two bands per storey (low + high under each floor / under F01B on the ground floor). One leftover fixed-shell corner stays open. Count: J01×22, J03×1.

## 8. Before sending DXFs to print (2026-03-26 review)

Authoritative nesting today: **21 A3 sheets** (12 × 3 mm, 9 × 6 mm), ~265 cut pieces. CAD release checks, stack-up, thickness bands and supplier DXF R12 all pass. Full fidelity notes: [IMPROVEMENTS.md §7](IMPROVEMENTS.md).

29. - [ ] **Shop confirmations (blockers).** Measure real 3 / 6 mm birch into the config bands; agree 420.0 ±0.3 square blanks for factory-edge walls **or** switch to all-sides-cut walls (item 23); confirm laser kerf, hold-down for long 3 mm strips, and who drills the blind pockets.
30. - [ ] **Align docs with the model.** Update sheet counts in supplier docs to 21; resolve veranda deck `E03` (code = 3 mm, `RISKS.md` still says 6 mm) and either restore 6 mm or add underside cleats; align `partition.front_gap` narrative (config = 0.0, risks text still mentions 16 mm).
31. - [ ] **Fit-test coupon first.** One small 3 mm and one 6 mm coupon: finger joint, pillar slot, thickness tags, optional blind pocket. Approve kerf and fit before the full nest.
32. - [ ] **P1 Moomin silhouette parts (3 mm).** Chimney spark-cowl crown on `E07`; scalloped eave lambrequin under `D03`; veranda corner spandrels at the column heads. Highest visual return per new piece; re-nest aiming to stay ≤22 sheets.
33. - [ ] **P2 entrance / veranda hero angle.** Stair handrail + newel; gable cartouche in `GD01`; porch posts under the main canopy; broken-pediment hoods on the featured upper windows only.
34. - [ ] **P3 secondary ornament.** Door panel relief overlays; dormer bargeboards; storey belt courses (stop at hinge seams); carriage-lantern silhouettes; printed thermometer strip beside the front door (decor, no plywood).
