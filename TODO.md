# Moomin House — TODO

Open improvements to the house, **in priority order**. Safety and fit come first, then the details that make it read as the Moominhouse, then play value, extras, and the book and tooling. Most items come from the comparison with the DeAgostini / Fanhome *Moominhouse* kit and the design review of 2026-10-14.

Already done:
- stone plinth with a hidden drawer; room dividers with doorways; veranda at ground-floor level, with stairs; entrance steps (revisions 3 and 4);
- steeper roof and printable fish-scale shingles, cut per course so they wrap the round roof; new cover (revisions 3 and 4);
- thermo-clay Moominpappa, Moominmamma and Moomintroll, one per floor; 3 mm parts on A4 / A3 laser sheets; identical parts share one ID (revision 5);
- magnetic catches and garden stop posts for the opening walls (four magnets), drawer turned to 150°, smaller figures that pass every doorway, EN 71-3 paint guidance, build gates, `make all` and the plywood thickness check (revision 6).

## 1. Before the first build: safety and fit

1. - [ ] **Physical checks at dry fit.** CAD proves clearances, not strength.
   - Measure every plywood sheet. If any is outside `thickness_tolerance`, update `thickness` or the band in `source/config.json`, then run `make all`.
   - Press-test the cantilevered front edge of each floor.
   - Check how much F00 bends over the drawer bay under the rear-frame foot near the drawer.
   - Push each opened shell hard against its GP1 post. The post sits about 80 mm from the hinge, so check the post's glue and screw and the hinge screws. A self-adhesive felt dot on the post face saves the paint.
   - With both walls open, press down on a shell's free edge and check that the house does not tip.
   - Pull each magnet with pliers after the epoxy has cured. None may move (EN 71-1 asks that magnets cannot come loose).
2. - [ ] **Lift the opening shells 1 mm off F00.** The moving walls stand on F00 with no gap, so their bottom edges rub the plinth top and its paint on every swing; the thickness check counts this as touching. Either hang the shells 1 mm higher (hinge centres and the walls' 2 mm roof clearance allow it) or glue thin felt glides under them.
3. - [ ] **Laser bed and 3 mm stock.** The 387 mm roof panels are on A3 laser sheets (three A3 and one A4). Check that the laser service takes A3 (420 × 297), or split the roof sheets. Without a laser, the roof panels need a larger primary 3 mm sheet, or a sheet of their own.
4. - [ ] **Clay density.** The clay estimate assumes 1.7 g/cm³. Weigh a block of the clay you buy, and set `figures.clay.density` if it differs.
5. - [ ] **Drawer stop.** Decide whether the drawer should be removable (as now) or stop at about 200 mm. A stop needs a cleat that can be fitted after the drawer is in.

## 2. The most recognisable missing details

6. - [ ] **Rope ladder from the attic dormer to the veranda roof.** It appears in every reference picture.
   - Move the dormer from the front-right roof facet (−45°) to the facet above the veranda (+45°), and the chimney from that facet, for example to the back-left (135°).
   - Model the ladder as cord plus D3 dowel rungs, glued at the dormer sill and resting on the veranda ridge. Keep it short and closed, with no loop a child could put a head through.
   - Add the ladder to the roof-lift check: it must lift with the roof.
7. - [ ] **Window detail.**
   - Clear 0.5 mm PET glazing behind each frame.
   - Arched or pediment window hoods and a sill for each window, as in the reference photos.
   - About 3 small parts per window, nested on the 3 mm laser sheets.
8. - [ ] **Exterior seams and plank texture.** Square-edged facets leave a V-gap at every outside corner, about 4.2 mm wide outside and 1 mm inside.
   - Glue a 3 × 8 mm vertical batten over each of the nine seams that do not move (not the two hinge seams or the front closing seam). The battens hide the gaps, stiffen the shells and give the board-and-batten look of the reference house.
   - Optionally add scored vertical plank grooves between them, with a knife jig. (Printed textures were dropped from the decor book on purpose.)

## 3. Play value

9. - [ ] **More clay figures.** Little My, Snufkin and the Snork Maiden, modelled like the family in `source/clay.py`. The attic is still free for one of them. Each must pass the doorway check (`figures.door_clearance`).
10. - [ ] **Room door leaves (optional).** The dividers have 40 × 100 doorways at their front ends. If wanted, add 3 mm leaves hung on cotton-tape hinges, and check that their swing clears the figures and furniture.
11. - [ ] **Back door.**
    - A second door on the kitchen side, with its own small canopy and a 4-riser stair.
    - A woodpile shelter beside it (a small open box with a lean-to roof). Keep both clear of the GP1 stop posts and the drawer's pull-out path at 150°.
12. - [ ] **Optional LED lighting.**
    - A wire channel in the rear posts, plus a battery box in the plinth's drawer bay or behind the drawer stop.
    - Neither our design nor the reference kit has lighting, and the reference builders regret that.
13. - [ ] **Faux cellar hatch.** A painted or printed hatch on the plinth beside the drawer front.

## 4. Extras (renders and the appendix)

14. - [ ] **More example furniture (renders only):** a chandelier in the living room, a bathtub, a tiled stove (kakelugn) for the living room, and an attic bed and desk.
15. - [ ] **Garden extras.** Bathing hut, rowing boat, well, small bridge, mailbox and Snufkin's tent, on separate FUR sheets like the furniture. A lantern on each GP1 garden post would suit them.

## 5. Book and tooling

16. - [ ] **Assembly-step coverage check.** Each assembly step should declare its part IDs. The book would then print each step's parts and quantities from `parts.json`, and `verify.py` would fail if a house part is in no step or in two. This stops the step text drifting from the model.
17. - [ ] **SC3 section for the stop posts.** The screw page draws SC3 through F00 into a foot block. The two stop-post screws go through the 6 mm B01 into end grain; add their section.
18. - [ ] **No-laser option for the 3 mm trim.** Offer the window bars and fascias as bought 5 × 3 and 8 × 3 mm basswood strip, cut to length with a knife and mitre box, as an alternative to the laser sheets.
19. - [ ] **Shingle paper.** The 177 roof shingle strips fill 12 pages at about 55 %; their area would fit on 7. Smarter nesting of the curved strips, for example interleaving courses of different sizes, could save 3–4 pages.
20. - [ ] **Joint-aware thickness check.** `thickness_check.py` grows every part about its mid-plane and treats parts that touch at nominal size as shifts. A stack-up model per joint (which face is the datum) would also catch tolerance build-up, such as three floors on posts, and loose slots in thin sheets.
21. - [ ] **Clean Python environment.** `.venv/lib/python3.12/site-packages/moomin_local.pth` adds two other projects' site-packages to the path. Install `requirements-dev.txt` into `.venv` and remove the `.pth`, so `make check` no longer needs `PYTEST_DISABLE_PLUGIN_AUTOLOAD`.
22. - [x] **CI and GitHub Pages.** `.github/workflows/ci.yml` runs the model tests and browser checks, then deploys the static viewer from `main`. See `docs/PUBLISHING.md`.
