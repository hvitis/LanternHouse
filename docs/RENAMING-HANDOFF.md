# Lanternwood House: rename and human family handoff

Status: implementation plan only. Prepared on 2026-10-16.

## 1. Objective and boundaries

Replace the current project identity with **Lanternwood House** throughout the current source, links, viewer, documentation, and generated deliverables.
Replace the six existing character figures with four original human figures: an older father, his wife, and their two children.
Keep the soft polymer-clay appearance and the existing CAD, rendering, and clay-estimation functions.

**Lanternwood House is the working name from the previous recommendation. The owner has not explicitly selected a final name.**
Use the values below unless the owner supplies another name before implementation.
These names do not establish trademark availability or permission to use third-party designs.

The implementation agent owns code changes, local builds, checks, link updates, and review artifacts.
The owner will rename the GitHub repository manually.

### Required boundaries

- Do not rename the GitHub repository through the API, `gh`, or a connector.
- Do not rewrite Git history, amend existing commits, move existing tags, or force-push.
- Do not remove `.git`, initialize a replacement repository, or delete existing releases.
- Do not upload releases or publish changes as part of this implementation handoff.
- Do not rename the active checkout directory during implementation.
- Do not modify private reference images or unrelated local files.
- Preserve third-party license files and attribution.
- Preserve the project license. A new project name does not authorize a license change.
- Keep the house geometry, plywood dimensions, joints, furniture, and assembly step IDs stable.
- Change figure geometry, placement, colors, and estimates where the new family requires those changes.

The requested scope covers the current project and future builds.
Old commits, tags, public releases, workflow logs, forks, and downloaded copies can retain the former identity.
Report those remaining references separately. Do not claim that this work removes them.

## 2. Naming contract

Keep these values consistent across all implementations and documentation.

| Purpose | Target value |
| --- | --- |
| Display name, both languages | `Lanternwood House` |
| GitHub owner | `hvitis` |
| Repository slug | `lanternwood-house` |
| Repository URL | `https://github.com/hvitis/lanternwood-house` |
| Clone URL | `https://github.com/hvitis/lanternwood-house.git` |
| Pages URL | `https://hvitis.github.io/lanternwood-house/` |
| Latest release URL | `https://github.com/hvitis/lanternwood-house/releases/latest` |
| Download/archive prefix | `Lanternwood-House` |
| CAD document name and stem | `LanternwoodHouse` |
| npm package name | `lanternwood-house-viewer-checks` |
| Headless environment variable | `LANTERNWOOD_HEADLESS` |
| Export ownership marker | `.lanternwood-viewer-export` |
| Assembly progress key | `lanternwood-house:assembly:v1` |
| Instructions language key | `lanternwood-house:instructions:lang` |
| Font registration names | `LanternwoodSans`, `LanternwoodSans-Bold` |
| PDF inspection keys | `/LanternwoodPageRole`, `/LanternwoodSheetID`, `/LanternwoodOperation` |
| Figure collection label | `The Rowan family` / `Rodzina Rowan` |

Examples of output names:

- `output/cad/LanternwoodHouse.FCStd`
- `output/cad/LanternwoodHouse.step`
- `output/cad/LanternwoodHouse-open.step`
- `output/cad/LanternwoodHouse-exploded.step`
- `output/pdf/Lanternwood-House-Complete.pdf`
- `output/pdf/Lanternwood-House-Clay-Family.pdf`
- `output/Lanternwood-House-Supplier-Cut.dxf`
- `output/Lanternwood-House-Build-Kit.zip`
- `Lanternwood-House/` as the ZIP root directory

Apply the same prefix to every other project PDF, custom cut file, and generated filename that contains the former name.
Keep generic paths such as `data/parts.json`, `data/assembly.json`, `data/house.dxf`, and `clay-family.webp`.
Keep `source/clay.py` and `source/clay_render.py`. The word `clay` describes the material and appearance.

## 3. Starting inventory and baseline

The initial review found the former project name in more than 60 text files.
Polish descriptions and character identifiers require a separate search.
Some generated outputs are ignored, while `prints/` and preview images are tracked.

- [ ] Read applicable `AGENTS.md` instructions before implementation.
- [ ] Record `git status --short`, `git remote -v`, and the current commit.
- [ ] Preserve unrelated work in the checkout.
- [ ] Record baseline check results before source changes.
- [ ] Record the structural part IDs, quantities, dimensions, nesting inputs, and assembly step IDs.
- [ ] Inventory tracked text, filenames, images, and packaged assets.
- [ ] Inventory ignored `output/`, `_site/`, and `.build-work/` separately.

Start the text inventory with:

```sh
rg -n -i --hidden \
  --glob '!.git/**' --glob '!.venv/**' --glob '!node_modules/**' \
  --glob '!output/**' --glob '!_site/**' --glob '!.build-work/**' \
  'moomin|mumin|mumink|snufkin|snork|little[ _-]?my|pappa|mamma' .
```

Also inspect the exact figure key `troll` in project-owned files.
Do not replace that substring globally. It also occurs inside unrelated words and vendor code.
Search for character translations, franchise source URLs, and the Japanese franchise name in the documentation.
Include `Włóczykij`, `Panna Migotka`, `Mała Mi`, `Muminek`, and inflected Polish family names.
Inspect the names of tracked files as well as their contents.

## 4. Original human family design

### Visual reference

[Owner-supplied image: older man carrying a lantern](https://static.vecteezy.com/system/resources/previews/066/230/247/non_2x/old-man-holding-lantern-in-navy-blue-coat-and-hat-flat-illustration-vector.jpg)

The reference shows a gray beard, gray eyebrows, a navy coat, a flat-topped cap, boots, and a yellow lantern.
Use those broad cues to develop a new three-dimensional figure.
Create original proportions, facial details, clothing details, and a compact pose suitable for this house.
Do not trace the illustration or embed the downloaded preview in public artifacts.
Keep any downloaded reference in the ignored `original/` directory or a temporary directory.
The build and viewer must work without network access to the reference.

The following names and dimensions are implementation defaults, not additional owner decisions.
The family consists of the couple and their own two children. Do not reinterpret the children as grandchildren.

| Key | Display name | Role | Initial height | Original design brief |
| --- | --- | --- | --- | --- |
| `elias` | Elias Rowan | Older father | 72 mm | Human face, small nose, gray beard, navy work coat, short cap, sturdy boots, lantern |
| `mira` | Mira Rowan | His wife and the children's mother | 68 mm | Human face, gray bob haircut, sage cardigan, ochre trousers, sturdy shoes |
| `ada` | Ada Rowan | Their child | 60 mm | Human face, short brown hair, rust sweater, blue overalls, rounded shoes |
| `theo` | Theo Rowan | Their child | 58 mm | Human face, dark curls, mustard sweater, teal trousers, rounded shoes |

### Shape and material requirements

- [ ] Build human heads, ears, noses, hands, legs, and feet with rounded clay forms.
- [ ] Keep the matte finish and soft joins across all four figures.
- [ ] Give each figure a distinct silhouette at the viewer's normal scale.
- [ ] Remove the old snouts, tails, animal ears, pointed hat, striped apron, handbag, anklet, and character-specific hair shapes.
- [ ] Build Elias from original human anatomy, rather than recoloring an old character body.
- [ ] Keep his cap short and his coat distinct from the former costumes.
- [ ] Model the lantern as attached geometry with a dark frame and warm yellow center.
- [ ] Keep the lantern close to his body, supported by his hand and another unobtrusive contact.
- [ ] Include the whole lantern in his bounds, footprint, doorway checks, volume, and clay quantities.
- [ ] Give all four figures flat undersides and stable contact with the floor.
- [ ] Keep accessories attached. Do not introduce loose miniature lantern pieces.
- [ ] Use painted yellow clay for the lantern. Do not add an LED or electrical feature.

The initial heights include hats and hair.
Adjust proportions when existing fit or small-parts checks fail.
Do not weaken those checks or enlarge the house to make a figure pass.
Keep the children visibly smaller than the adults.
Passing the existing checks does not constitute physical toy certification.

### Placement and identifiers

Use one family member per level as the initial arrangement:

```json
{
  "levels": [["elias"], ["mira"], ["ada"], ["theo"]],
  "heights": {"elias": 72, "mira": 68, "ada": 60, "theo": 58}
}
```

This fragment belongs inside `figures`. Preserve the other figure configuration values unless a documented change is necessary.

Use `FG1` through `FG4` for Elias, Mira, Ada, and Theo respectively.
Remove `FG5`, `FG6`, and all six former character keys from active figure data.
Do not preserve two extra figures or relabel old geometry.
Use the existing placement algorithm to find free positions near the front.
Keep the complete figures clear of furniture, partitions, walls, and door sweeps.

## 5. AI implementation work

### A. Replace the project identity and output contracts

- [ ] Update `source/config.json` and the schema title.
- [ ] Update both README files, all project documentation, plans, risks, and TODO text.
- [ ] Update `package.json` and both package-name entries in `package-lock.json`.
- [ ] Update `Makefile`, subprocess environments, FreeCAD launch code, and the release workflow together.
- [ ] Replace project-specific temporary directory prefixes, CLI messages, report headings, and comments.
- [ ] Update the CAD document name, labels, save paths, reopen paths, and STEP paths together.
- [ ] Update PDF titles, authors, footers, font registration names, and PDF inspection keys together.
- [ ] Update all filename producers, consumers, assertions, release asset lists, and ZIP readers together.

Primary files:

| Area | Files to inspect |
| --- | --- |
| CAD and orchestration | `source/build_cad.py`, `decorate_cad.py`, `rebuild.py`, `verify.py`, `verify_gui.py`, `thickness_check.py`, `run_stress_tests.py`, `Makefile` |
| PDFs and cut files | `source/book.py`, `pdf_assembly.py`, `pdf_checks.py`, `supplier.py`, `cut_file.py`, `checklist_pdf.py`, `joint_sample_pdf.py`, `source/locales/en.json`, `source/locales/pl.json` |
| Packaging and releases | `source/package.py`, `source/release.py`, `.github/workflows/release.yml`, `tests/test_package.py`, `tests/test_build_pipeline.py` |
| Local tools | `source/serve.py`, `source/viewer_dxf.py`, `source/print_studio.py`, `source/stock_report.py`, `ops/stock.py`, `ops/custom_nesting_dxf.py` |
| Future architecture plans | `docs/REUSABLE-CAD-FRAMEWORK-PLAN.md`, including proposed package names such as `models.moomin_house` |

Paths in this table share the displayed directory when abbreviated.
Treat the table as a starting inventory. The final search determines completeness.

Use a small shared naming module where several Python producers and consumers need the same value.
Keep its values aligned with HTML, browser tests, and workflow literals.
Do not expand this task into the proposed multi-model framework refactor.

### B. Replace the figure implementation and all consumers

- [ ] Replace `NAMES` and `DESIGNS` in `source/clay.py` with exactly four new figures.
- [ ] Remove old figure builders and their costume-specific helpers.
- [ ] Preserve useful generic primitives, mesh functions, and exported interfaces.
- [ ] Update `source/config.schema.json` enums, height properties, and required height keys.
- [ ] Update `source/config_check.py` where necessary for the new registry.
- [ ] Update `FIGURE_CODES` in `source/model.py`.
- [ ] Update figure ordering in `source/book.py` and `source/clay_render.py`.
- [ ] Update all captions, room descriptions, instructions, and generated tables to four people.
- [ ] Update `source/build_cad.py`, `source/verify.py`, and `source/viewer/app.js` where they assume old figures or materials.

Resolve these implementation details explicitly:

1. **Sampling bounds.** `scale()` and `_grid()` currently start with fixed design-space bounds.
   Cover the cap, beard, hands, and lantern without clipping any geometry.
   Either keep every primitive inside verified bounds or derive conservative bounds from the primitives.
2. **Palette indices.** `PALETTE`, `MATERIAL_NAME`, packed meshes, and renderers share material assumptions.
   Add skin, navy, gray, yellow, sage, and clothing colors consistently.
   Remove dependencies on the current `APRON` and `STRIPE` behavior in both mesh colors and `clay_render.py`.
3. **Foil cores.** `stats()` currently restricts the estimated core to material `WHITE`.
   Replace this condition with explicit core regions inside the human torsos.
   Keep the configured clay wall thickness. Exclude heads, limbs, and the lantern from the default core.
4. **Color quantities.** Recompute volumes and grams per color from the new geometry.
   Keep total grams consistent with density and handling allowance.
   Keep the foil savings within the eligible body volume.
5. **CAD primitives.** `lumps_spec()` and `build_cad.lump_solid()` must describe the same shapes.
   Prefer existing supported primitives. Add matching CAD support for every new primitive type.
   Preserve the distinction between smooth clay meshes and exact unions used by the current volume checks.
6. **CAD appearance.** Replace default all-white figure styling where necessary.
   Show the new clothing, skin, hair, and lantern colors in native CAD and preview meshes.
7. **PDF layout.** `FIG_ORDER`, family composition, and figure pages currently expect six designs.
   Lay out four people without missing keys, empty pages, clipped labels, or old character instructions.

Retain generic data interfaces such as `data['clay']` unless the redesign requires a schema change.
Renaming these interfaces adds no branding benefit.

### C. Update code links and browser behavior

- [ ] Replace both old repository spellings: `MoominsHouse` and `moominshouse`.
- [ ] Update clone commands, repository links, issue links, release links, and Pages links.
- [ ] Update canonical, Open Graph, and Twitter URLs in `source/viewer/index.html`.
- [ ] Update visible branding, page titles, descriptions, accessibility labels, and image alternative text.
- [ ] Update `source/viewer/prints.html`, download names in `prints.js`, and DXF filenames in `dxf-viewer.js`.
- [ ] Replace the franchise-derived color explanation in `workspace.css` with the current palette description.
- [ ] Replace figure controls and labels with `Rowan family (four clay figures)` and an appropriate Polish equivalent.
- [ ] Replace the two browser storage keys in `source/viewer/instructions.js` and corresponding test expectations.
- [ ] Replace the export marker in `source/export_viewer.py` and marker expectations in its tests.
- [ ] Update repository prefixes in all browser smoke scripts to `/lanternwood-house/`.
- [ ] Preserve relative asset URLs and existing functional hash routes such as `#house` and `#printables`.

Use the new browser storage namespace without retaining old brand strings in runtime code.
Document that existing users start with fresh progress and language defaults.
Do not delete old browser storage entries. Keep assembly step IDs stable for the new namespace.

Keep the exporter's directory and symlink protections intact.
An external directory with only the old marker must remain protected after the marker change.
Require a new export directory for that case. Do not relax the ownership check.

During preparation, the future repository and Pages URLs can return 404.
Do not treat that expected result as a local implementation failure before the owner renames the repository.

### D. Replace documentation, imagery, and embedded metadata

- [ ] Rewrite English and Polish descriptions around the original house project and the four-person family.
- [ ] Update `README.md`, `README.pl.md`, `PLAN.md`, `IMPROVEMENTS.md`, `TODO.md`, `RISKS.md`, and `docs/*.md`.
- [ ] Replace old named-character narratives with descriptions of the new inhabitants and rooms.
- [ ] Remove obsolete franchise product links and kit comparisons from active product documentation.
- [ ] Describe the existing architecture directly without claiming that this rename establishes design ownership.
- [ ] Preserve attribution or provenance that remains factually or legally necessary.
- [ ] Keep third-party license text unchanged.
- [ ] Replace obsolete fan-project notices with accurate project and license descriptions.
- [ ] Update notice text in both locale files. The English locale currently contains Polish notice text.
- [ ] Update old character references in furniture descriptions, including the bathtub sizing note.
- [ ] Update `source/cover.py`, `source/social_preview.py`, and their layout for the longer project title.
- [ ] Render the new family from front, side, back, and three-quarter views.
- [ ] Regenerate `docs/images/clay-family.webp` and all house images that contain figures.
- [ ] Regenerate the cover and every social-preview copy.
- [ ] Update `docs/images/social-preview.png`, `.github/social-preview.png`, and `source/viewer/social-preview.png` consistently.

Generate technical images from the actual model.
Use those images to prove that the viewer, CAD, and instructions describe the same family.
Inspect images visually. Text searches cannot detect an old character or title inside a bitmap.

Historical plans can describe retained engineering decisions in neutral terms.
Do not invent a new historical origin for the house or erase attribution to justify the new name.
List necessary remaining references in the audit report.
This handoff document intentionally contains legacy identifiers for migration instructions.

### E. Regenerate tracked print assets and clean build products

- [ ] Update the descriptions in `source/prints/*.py` before publishing new print files locally.
- [ ] Regenerate `prints/manifest.json` from those sources.
- [ ] Rebuild tracked STL, STEP, and 3MF files where their metadata contains old branding.
- [ ] Inspect ZIP/XML metadata inside 3MF files and headers or labels inside STEP files.
- [ ] Build CAD, PDFs, cut files, reports, renders, and the kit from fresh inputs.
- [ ] Export a fresh `_site/` without `--reuse-data` for the first renamed build.
- [ ] Bump the viewer data cache namespace in `.github/workflows/ci.yml` for this migration.
- [ ] Prevent old cached models or checklist PDFs from restoring the previous identity or figures.
- [ ] Use the existing isolated build and publication safeguards.

Do not rename old binaries and call them regenerated deliverables.
Inspect the new files internally, including PDF metadata, PDF text, CAD labels, and ZIP entry names.
Do not clean `output/` indiscriminately. It can contain physical measurement logs in `joint-samples/`.
Preserve those logs and let a successful isolated build replace build products through the existing safeguards.
Report old ignored diagnostic workspaces and private reference filenames without deleting them.

`source/rebuild.py` copies inputs through its explicit `INPUTS` list.
Keep new runtime files inside copied directories, or update that list.
Generated-file publication currently updates existing baseline paths.
If this work introduces a new generated filename, update publication handling and its tests.

## 6. Validation and acceptance

### Automated checks

Run these commands after implementation, with the required environments installed:

```sh
make check
make lint
.venv/bin/python source/print_build.py --force
make all
make site
npm run test:viewer
npm run test:instructions
npm run test:prints
git diff --check
```

`make all` includes the full isolated build and thickness checks. FreeCAD is required.
The print build requires the existing print dependencies.
Install Node dependencies and Playwright Chromium if they are absent.
Do not use the configured `test:mobile` script without inspecting it first.
Its referenced `tests/mobile-smoke.mjs` file is absent in the reviewed checkout.
The existing viewer and prints smoke scripts already cover desktop and mobile viewports.

- [ ] Update existing tests for new filenames, archive roots, metadata keys, prefixes, and figure keys.
- [ ] Add meaningful coverage for exactly four unique family members and valid level assignments.
- [ ] Keep watertight meshes, positive volumes, and finite normals for all figures.
- [ ] Keep valid CAD solids and the existing agreement between CAD unions and clay estimates.
- [ ] Keep all four figures upright through every doorway with the configured clearance.
- [ ] Include Elias's attached lantern in fit, collision, and volume checks.
- [ ] Keep existing small-parts checks for every figure.
- [ ] Verify color totals, core savings, and clay quantities for the new human material palette.
- [ ] Keep placement checks against furniture, walls, partitions, and moving doors.
- [ ] Keep export directory protections and failed-build recovery coverage.
- [ ] Run the browser checks at `/lanternwood-house/` and smoke-check the export at `/`.
- [ ] Exercise `#house`, `#printables`, instructions, the standalone prints page, DXF, and actual downloads.
- [ ] Check both checklist PDF languages and all local module/data requests.
- [ ] Keep offline asset behavior and the existing visible error states.

Compare the structural baseline after the full build.
Part geometry, quantities, machining paths, and assembly step IDs must remain stable.
Explain metadata-only changes and expected figure-related changes separately.
Do not suppress a failed geometric check to complete the rename.

### Text, path, and binary audit

- [ ] Repeat the source search, including Polish names, character keys, URLs, comments, and documentation.
- [ ] Inspect tracked filenames and generated filenames.
- [ ] Inspect extracted PDF text and metadata from every generated PDF.
- [ ] Inspect CAD document names, labels, and reopen behavior.
- [ ] Inspect DXF comments, JSON descriptions, STEP metadata, 3MF metadata, and archive contents.
- [ ] Compare every kit entry against the expected new archive root and current build manifest.
- [ ] Inspect exported HTML for old absolute URLs and old social-image URLs.
- [ ] Visually inspect the cover, social previews, family sheet, PDF figure pages, and furnished house renders.

Record each remaining match with its path and reason.
Permit legacy names only in migration documentation, necessary provenance, and unchanged third-party material.
Exclude `.git`, local dependencies, and ignored diagnostics from the current-source acceptance count.
Do not treat this handoff's search patterns as an implementation failure.
Do not alter vendor code because an unrelated substring matches.

### Review artifacts to leave for the next person

- [ ] A change summary with all naming contract values.
- [ ] A complete list of changed files and generated deliverables.
- [ ] A four-person family sheet with names and dimensions.
- [ ] Individual front, side, back, and three-quarter renders.
- [ ] Desktop and mobile viewer screenshots with the human family visible.
- [ ] PDF samples with new titles, figures, and clay quantities.
- [ ] Check results, including failures or missing runtime dependencies.
- [ ] An audit of any remaining old references and external limitations.
- [ ] The owner checklist below, updated with the actual final repository name.

Do not report completion if a required CAD build or browser check remains unrun.
Report the completed work and the exact blocker instead.

## 7. Owner's manual GitHub rename and later checks

The AI prepares all source and local artifacts before this stage.
The owner controls when the code reaches `main`, which currently triggers Pages deployment.
Coordinate that timing with the repository rename to reduce broken-link time.

### Owner actions

1. Rename `hvitis/MoominsHouse` to `hvitis/lanternwood-house` in GitHub repository settings.
2. Tell the implementation agent the final repository name so it can update the local remote and verify links.
3. Merge or push the prepared changes through the normal workflow.
4. Run the Pages workflow from the renamed repository if deployment does not start automatically.
5. Review the GitHub description, About website URL, topics, and selected social-preview image.
6. Update external links under the owner's control.
7. Decide separately how to handle old releases and their branded downloads.

Renaming the local folder is optional and independent of the GitHub rename.
If the owner renames it later, recreate environments with absolute interpreter paths where necessary.
Do not make the code depend on either checkout folder name.

GitHub documents repository redirects and the exception for Pages project URLs:
[Renaming a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository).
Do not depend on the old Pages URL redirecting to the new one.

### AI checks after the owner reports that the rename is complete

- [ ] Update the local remote to the owner's confirmed repository URL.
- [ ] Read the updated remote and verify the selected final slug.
- [ ] Verify the new repository and Pages URLs.
- [ ] Verify deep links, canonical URLs, social images, checklist PDFs, and downloads on the live site.
- [ ] Inspect the renamed repository's workflow results and Pages artifact.
- [ ] Verify release links against an actually available renamed release.
- [ ] Report old release assets separately if the new release is not published yet.

Use these commands when the owner confirms `lanternwood-house`:

```sh
git remote set-url origin https://github.com/hvitis/lanternwood-house.git
git remote -v
```

Preparing a future release must use a new tag that targets the renamed implementation.
Do not rerun a historical release tag to replace its original assets.
A release dry run can report uncommitted or unpushed source before the owner's merge.
Report that expected prerequisite without bypassing release integrity checks.

## 8. Definition of done

The local implementation is complete when the current source, export, and fresh deliverables use the new identity.
All four original humans must appear consistently in the viewer, CAD, renders, and instructions.
All required checks must pass, with the house's structural behavior preserved.
The remaining external work must be explicit in the handoff.

The repository rename, live deployment verification, and old-release decisions have separate completion states.
Git history remains unchanged throughout this work.
