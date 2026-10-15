# Physical joint samples

The sample pack contains production geometry for a trial with real plywood and hardware.
The default pack uses laser cutting and 3 mm and 6 mm plywood.
The pack does not establish physical strength or toy safety.
All physical results start as pending.

## Generate the pack

1. Run `make joints`.
2. Open `Workshop-Joint-Samples.pdf` in the printed output directory.
3. Read the materials page and the procedure for each sample.
4. Send the two `*-through.dxf` files to the laser supplier.
5. Give the supplier the plywood thickness for each file.
6. Use the same plywood batch and cutting settings as the house.

The PDF contains full-size cutting templates, assembly maps and separate templates for hardwood and hinge shims.
The SVG files contain the same nominal through contours as the DXF files.
Neither file format includes compensation or machine toolpaths.
The laser supplier applies kerf compensation once.
The hardwood parts and shims do not occur on the plywood layouts.

`drilling.csv` gives hole coordinates, diameter, depth and entry face.
Coordinates use the lower-left datum in the top reference view.
Blind bores and recesses stay out of the laser files.
The hand preparation templates give their drilling details.

## Record the physical results

1. Measure each plywood thickness at five positions.
2. Record the batch, machine settings and compensation in `physical-results.csv`.
3. Measure both calibration squares and their holes before sanding.
4. Print the PDF at 100% actual size.
5. Measure the 100 mm reference bar before using a paper template.
6. Write each sample ID on its cut piece.
7. Complete the procedures in the PDF.
8. Enter the measurements, operator, date and observations in the CSV.
9. Mark a test as passed only after its physical acceptance conditions are met.
10. Copy the completed CSV and photographs into `ops/joint-validation/` before a full rebuild.

The output directory includes a fingerprint of the model and the cutting process.
Regeneration preserves an existing measurement log for that model.
A full rebuild replaces `output/`, including old sample packs.
The copies in `ops/joint-validation/` remain outside generated output.

## Coverage and limits

| Sample | Physical observation | Remaining work |
| --- | --- | --- |
| Upper-floor finger seam | Hand fit, face alignment, support bond after cure | Full-floor bending and load |
| Ground-floor puzzle seam | Fit of one unchanged knob and its thin support | Complete floor and drawer bay |
| Ground-floor straight seam | Face alignment and 3 × 4 mm support bond | Full seam and drawer clearance |
| Pillar slot | Fit before and after the planned finish | Alignment through both floors |
| Wall hinge mount | Actual hardware, enclosed screw tips, 20 opening cycles | Full shell angle, weight and pull-out load |
| Magnetic catch | Remaining skin, enclosed magnet, disc bond, opening force | Destructive abuse and full assembly |
| Roof ring and cleat | Flat contact and bond after cure | Complete cone and roof lifting |
| Roof turn-button catch | Unavailable in the current model | Reconcile the old documentation with the design |

The spare `CATCH-SKIN` block contains no magnet.
Its section exposes the bore depth and remaining wood for measurement.
The second block contains the enclosed magnet for the closure trial.
The opening-force field records an observation, not a certified acceptance threshold.
