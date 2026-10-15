"""Render 3D-printable designs from their STL files to clean, high-resolution PNGs for the PDF book."""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PRINTS = ROOT / 'prints'
OUT = ROOT / 'output/previews'

def render_print(name, color_hex='#e0d8c3', size=(600, 600), out_dir=OUT):
    stl_path = PRINTS / f'{name}.stl'
    if not stl_path.exists():
        raise FileNotFoundError(f'STL file not found: {stl_path}')

    import print_mesh, render
    V, F = print_mesh.read_stl(stl_path)
    camera = render.camera(-40, 24)
    proj = V @ camera.T
    pts = proj[:, :2]
    lo, hi = pts.min(0), pts.max(0)
    pad = 40
    scale = min((size[0] - 2 * pad) / (hi[0] - lo[0]), (size[1] - 2 * pad) / (hi[1] - lo[1]))
    center = (lo + hi) / 2

    def screen(p):
        return ((p[0] - center[0]) * scale + size[0] / 2, size[1] / 2 - (p[1] - center[1]) * scale)

    # Lighting: main key light + gentle ambient fill
    light = np.array([-.35, -.5, 0.85])
    light /= np.linalg.norm(light)
    T = V[F]
    cross = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    twice = np.linalg.norm(cross, axis=1)
    norm = np.maximum(twice, 1e-12)
    normals = cross / norm[:, None]
    diffuse = np.clip(normals @ light, 0, 1)
    shades = 0.68 + 0.32 * diffuse

    # Base color from hex
    hexrgb = lambda h: np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], dtype=float)
    base_col = hexrgb(color_hex) if color_hex.startswith('#') else np.array([230, 225, 210], dtype=float)

    # Sort triangles back-to-front
    depths = proj[F, 2].mean(1)
    order = np.argsort(depths)

    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for idx in order:
        poly = [screen(proj[v, :2]) for v in F[idx]]
        c = tuple(np.clip(base_col * shades[idx], 0, 255).astype(int)) + (255,)
        draw.polygon(poly, fill=c)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'print-{name}.png'
    img.save(out_path)
    return out_path

def render_all():
    manifest_path = PRINTS / 'manifest.json'
    if not manifest_path.exists():
        print('prints/manifest.json not found; skipping print rendering')
        return {}
    manifest = json.loads(manifest_path.read_text())
    results = {}
    for name, entry in manifest.get('parts', {}).items():
        color = entry.get('color', '#e0d8c3')
        p = render_print(name, color_hex=color)
        results[name] = p
        print(f'Rendered print design {name} -> {p.name}')
    return results

if __name__ == '__main__':
    render_all()
