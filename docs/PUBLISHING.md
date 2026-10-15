# Publish on GitHub

The public repository contains source files, documentation, original preview images and the third-party files with their licenses.
Git excludes the reference photos, local credentials, virtual environments and generated files.
GitHub Pages serves the exported 3D viewer. It does not need Python or FreeCAD on the server.

## Check the source and the static viewer

1. Install Python 3.12 or later.
2. Create the virtual environment:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements-dev.txt
   ```

3. Run the source checks:

   ```sh
   make check
   ```

4. Export the static viewer:

   ```sh
   make site
   ```

5. Serve the export:

   ```sh
   .venv/bin/python -m http.server 8765 --bind 127.0.0.1 --directory _site
   ```

6. Open <http://127.0.0.1:8765/> in a browser with JavaScript and WebGL.

On Windows, use `.venv\Scripts\python` in place of `.venv/bin/python`.
Without Make, run `python source/config_check.py`, `python -m pytest` and `python source/export_viewer.py _site` with the virtual environment interpreter.
Opening `index.html` directly from the filesystem does not support the module and model requests. Use an HTTP server.

The `_site/` folder contains HTML, JavaScript, local three.js files, license files, `data/parts.json` and `data/assembly.json`.
The assembly manifest is regenerated on every export, including exports that reuse cached geometry.
Every asset URL is relative, so the site works at `/` and at `/moominshouse/`.
The export builds the model from the source. It does not use the existing `output/parts.json`.
The export replaces `_site/`. Outside the repository, it replaces only folders that contain its export marker.

## Run the browser checks

Node.js 22 and Playwright are needed only for these checks. The viewer itself needs neither.

```sh
npm ci
npx playwright install chromium
make site
npm run test:viewer
npm run test:instructions
```

On Linux, use `npx playwright install --with-deps chromium` to install the browser and its system dependencies.
The checks serve `_site/` under `/moominshouse/` and block external requests.
They check the model request, local JavaScript modules, rendered WebGL pixels and the opening controls at desktop and mobile sizes.
They also check the visible error message when the model file is missing.
Screenshots appear in `output/viewer-smoke/` and stay outside Git.

## Create the public repository

1. If this folder has no Git repository, initialize it:

   ```sh
   git init -b main
   ```

2. Stage the files:

   ```sh
   git add .
   ```

3. Review the staged files:

   ```sh
   git diff --cached --stat
   git diff --cached --check
   git ls-files
   ```

   The file list must exclude `.venv/`, `node_modules/`, `output/`, `_site/`, `.env` files and the reference photos.
   Only `original/README.md` belongs in Git from the reference folder.

4. Create the first commit:

   ```sh
   git commit -m "Prepare Moomin House source and static 3D viewer"
   ```

5. Create an empty public repository named `moominshouse` on GitHub.
6. Connect the remote:

   ```sh
   git remote add origin https://github.com/hvitis/moominshouse.git
   ```

7. In GitHub, select **Settings → Pages → Build and deployment → Source → GitHub Actions**.
8. Push the source:

   ```sh
   git push -u origin main
   ```

9. Wait for the **CI** workflow to finish in **Actions**.
10. Open <https://hvitis.github.io/MoominsHouse/>.

If you use another owner or repository name, change the remote and the links in both README files.
The static asset URLs need no change.
If the first deployment starts before Pages is configured, configure Pages and run **Actions → CI → Run workflow**.
See the [GitHub Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) for the publishing source and permissions.

The workflow exports only the static viewer on `main` and on pull requests. Tests run locally with the commands above.
It caches pip downloads and generated model/DXF data. Web assets and published prints are copied fresh for every export.
Only the release workflow builds the complete CAD files, PDFs, and build kit.
Only pushes to `main` and manual runs on `main` upload and deploy the Pages artifact.
The deployment uses the `github-pages` environment and the built-in `GITHUB_TOKEN`. No personal token is needed.
Only the deployment job receives `pages: write` and `id-token: write`.

## Publish the building book

The full CAD build runs locally with FreeCAD. GitHub Pages publishes only the interactive viewer.
Generated PDFs and the build kit belong in GitHub Releases.

```sh
make all
.venv/bin/python source/release.py v1 --dry-run
.venv/bin/python source/release.py v1 --draft
```

If the build changes source or documentation, commit and push those changes before you run the release command.
Review the draft assets on GitHub before you publish the release.
The README download link becomes available after the first published release.

## Maintain the build companion

The Instructions tab uses the same chapter descriptions and purchasing list as the PDF book.
`source/assembly.py` defines the individual operations, part references and repeat batches.
The export checks that each physical model instance belongs to one operation.

Keep step IDs stable when editing text. Progress uses these IDs rather than step numbers.
A changed manifest revision shows an update notice. Incompatible saved progress requires an explicit restart.
Progress stays in local storage for this browser and site origin. It does not sync between devices.

Add verified field notes to `FIELD_HINTS` in `source/assembly.py`, keyed by stable step ID.
Each note has a `text` field and an optional `author` field.
The HINTS area shows these notes below the current instructions. No public submission service is included.
Do not add simulated field reports. The current build has not been glued yet.

The 3D assembly view is separate from the main preview. Play animates only the current step.
Next browses ahead. Mark complete records the whole operation or repeat batch.
The elevated floors use small metal angle brackets. The builder checks their fit and fixings during the dry fit.
Roof magnets or a hinge-style attachment remain optional builder choices.
