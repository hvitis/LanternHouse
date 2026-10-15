"""Update README images in docs/images/ from rendered outputs in output/previews/.

Whenever CAD models, clay figures, or book covers are rerendered locally,
this module updates the corresponding web-optimised images displayed in README.md:
- docs/images/cover.jpg (JPEG, 720px wide) from output/previews/cover.png
- docs/images/house-closed.webp (WebP, 600px wide) from output/previews/house-closed-veranda.png
- docs/images/house-open.webp (WebP, 700px wide) from output/previews/house-open-furnished.png
- docs/images/house-exploded.webp (WebP, 600px wide) from output/previews/house-exploded.png
- docs/images/clay-family.webp (WebP, 800px wide) from output/previews/clay-family.png
- docs/images/social-preview.png (PNG, 1280x640) via source/social_preview.py
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'source') not in sys.path:
    sys.path.insert(0, str(ROOT / 'source'))

IMAGE_SPECS = [
    {
        'target': 'cover.jpg',
        'sources': ['cover.png'],
        'format': 'JPEG',
        'width': 720,
        'crop': False,
        'mode': 'RGB',
        'save_kwargs': {'quality': 90, 'optimize': True},
    },
    {
        'target': 'house-closed.webp',
        'sources': ['house-closed-veranda.png', 'house-closed.png'],
        'format': 'WEBP',
        'width': 600,
        'crop': True,
        'mode': 'RGBA',
        'save_kwargs': {'quality': 90, 'method': 6},
    },
    {
        'target': 'house-open.webp',
        'sources': ['house-open-furnished.png', 'house-open.png'],
        'format': 'WEBP',
        'width': 700,
        'crop': True,
        'mode': 'RGBA',
        'save_kwargs': {'quality': 90, 'method': 6},
    },
    {
        'target': 'house-exploded.webp',
        'sources': ['house-exploded.png'],
        'format': 'WEBP',
        'width': 600,
        'crop': True,
        'mode': 'RGBA',
        'save_kwargs': {'quality': 90, 'method': 6},
    },
    {
        'target': 'clay-family.webp',
        'sources': ['clay-family.png'],
        'format': 'WEBP',
        'width': 800,
        'crop': True,
        'mode': 'RGBA',
        'save_kwargs': {'quality': 90, 'method': 6},
    },
]


def crop_and_resize(im: Image.Image, target_width: int, crop: bool = True) -> Image.Image:
    """Optionally crop whitespace/transparent border and resize proportionally to target_width."""
    if crop:
        bbox = im.getbbox()
        if bbox:
            im = im.crop(bbox)
    target_height = max(1, round(im.height * target_width / im.width))
    return im.resize((target_width, target_height), Image.LANCZOS)


def sync_furniture_mesh(root: Path = ROOT, quiet: bool = False):
    """Sync furniture instances from source/model.py into output/parts.json and output/previews/mesh.json."""
    from model import build
    data = build()
    out = root / 'output'
    out.mkdir(exist_ok=True)
    previews = out / 'previews'
    previews.mkdir(exist_ok=True)

    parts_path = out / 'parts.json'
    parts_path.write_text(json.dumps(data, indent=2))

    mesh_path = previews / 'mesh.json'
    if not mesh_path.exists():
        return

    mesh = json.loads(mesh_path.read_text())
    # Keep non-furniture meshes (house, fixtures, figures)
    mesh = [m for m in mesh if m.get('group') != 'Furniture']

    parts = data['parts']
    furn_instances = [i for i in data['instances'] if i['group'] == 'Furniture']

    for inst in furn_instances:
        pid = inst['part']
        p = parts[pid]
        outer = p['outer']
        thickness = p['thickness']
        n = len(outer)
        origin = np.array(inst['origin'], dtype=float)
        u = np.array(inst['u'], dtype=float)
        v = np.array(inst['v'], dtype=float)
        w = np.array(inst['w'], dtype=float)

        pts0 = [origin + x * u + y * v for x, y in outer]
        pts1 = [origin + x * u + y * v + thickness * w for x, y in outer]
        verts = [pt.tolist() for pt in (pts0 + pts1)]
        faces = []
        for k in range(1, n - 1):
            faces.append([0, k + 1, k])
        for k in range(1, n - 1):
            faces.append([n, n + k, n + k + 1])
        for k in range(n):
            nxt = (k + 1) % n
            faces.append([k, nxt, n + nxt])
            faces.append([k, n + nxt, n + k])

        mesh.append({
            'id': inst['id'],
            'part': pid,
            'design_part': inst['design_part'],
            'group': 'Furniture',
            'color': inst.get('color') or p['color'],
            'vertices': verts,
            'faces': faces
        })

    mesh_path.write_text(json.dumps(mesh, separators=(',', ':')))
    if not quiet:
        print(f"Synced {len(furn_instances)} furniture instances into previews/mesh.json")


def rerender_readme_previews(root: Path = ROOT, quiet: bool = False):
    """Rerender the CAD and cover previews needed for the README."""
    sync_furniture_mesh(root=root, quiet=quiet)

    import render
    # Reload DATA and MESH in render module
    render.DATA = json.loads((root / 'output/parts.json').read_text())
    render.MESH = json.loads((root / 'output/previews/mesh.json').read_text())
    render.VIEWS = render.DATA['derived']['views']

    house = lambda m: m['group'] not in ('Furniture', 'Figures')
    veranda_angle = -75 + (int(render.DATA['config']['veranda']['facet'][1:]) - 1) * 30

    if not quiet:
        print("Rerendering README views from updated model...")
    render.render('house-closed-veranda', house, size=(1800, 2400), view=render.camera(veranda_angle + 15))
    render.render('cover-house', house, size=(2000, 2600), view=render.camera(-25, 16))
    render.render('house-open-furnished', mode='open', size=(2200, 2400))
    render.render('house-exploded', house, mode='exploded', overlay=True, size=(2200, 2800))

    import clay_render
    clay_render.family()

    import cover
    cover.main()


def update_readme_images(root: Path = ROOT, quiet: bool = False) -> list[Path]:
    """Generate and update web-optimised README images from output/previews/."""
    previews = root / 'output/previews'
    docs_images = root / 'docs/images'
    docs_images.mkdir(parents=True, exist_ok=True)
    updated: list[Path] = []

    for spec in IMAGE_SPECS:
        src_path = None
        for candidate in spec['sources']:
            p = previews / candidate
            if p.exists():
                src_path = p
                break

        if not src_path:
            continue

        with Image.open(src_path) as im:
            if spec.get('mode') and im.mode != spec['mode']:
                im = im.convert(spec['mode'])
            processed = crop_and_resize(im, spec['width'], crop=spec['crop'])
            out_path = docs_images / spec['target']
            processed.save(out_path, spec['format'], **spec['save_kwargs'])
            updated.append(out_path)
            if not quiet:
                print(f"Updated README image: {out_path.relative_to(root)} ({processed.size[0]}x{processed.size[1]})")

    # Also update social preview (which embeds the opened house render)
    try:
        import social_preview
        sp_path = social_preview.generate()
        if sp_path:
            updated.append(Path(sp_path))
            if not quiet:
                print(f"Updated README image: {Path(sp_path).relative_to(root)}")
    except Exception as e:
        if not quiet:
            print(f"Note: social preview update skipped ({e})")

    return updated


def main():
    p = argparse.ArgumentParser(description='Update README images from rendered previews')
    p.add_argument('--rerender', '-r', action='store_true', help='Rerender previews from model before updating docs/images')
    p.add_argument('--quiet', '-q', action='store_true', help='Suppress non-error output')
    args = p.parse_args()

    if args.rerender:
        rerender_readme_previews(quiet=args.quiet)
    update_readme_images(quiet=args.quiet)


if __name__ == '__main__':
    main()
