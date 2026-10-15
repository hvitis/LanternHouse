"""Tests for README image generation and automatic updates."""
from pathlib import Path
from PIL import Image
import pytest

import readme_images

ROOT = Path(__file__).resolve().parents[1]


def test_crop_and_resize_crops_and_scales():
    # Create an image with transparent border
    im = Image.new('RGBA', (200, 100), (0, 0, 0, 0))
    # Fill center (50, 25) to (150, 75) => 100x50 box (2:1 aspect)
    for x in range(50, 150):
        for y in range(25, 75):
            im.putpixel((x, y), (255, 0, 0, 255))

    # Cropped and resized to width 50
    out = readme_images.crop_and_resize(im, target_width=50, crop=True)
    assert out.size == (50, 25)

    # Without cropping
    out_uncropped = readme_images.crop_and_resize(im, target_width=100, crop=False)
    assert out_uncropped.size == (100, 50)


def test_update_readme_images_graceful_on_empty_dir(tmp_path):
    # If no output/previews exist, update_readme_images should not crash
    updated = readme_images.update_readme_images(root=tmp_path, quiet=True)
    assert isinstance(updated, list)


def test_readme_specs_cover_all_readme_images():
    readme_en = (ROOT / 'README.md').read_text()
    readme_pl = (ROOT / 'README.pl.md').read_text()

    # Required target images in docs/images/
    expected_images = {
        'cover.jpg',
        'house-closed.webp',
        'house-open.webp',
        'house-exploded.webp',
        'clay-family.webp',
        'social-preview.png',
    }

    for img_name in expected_images:
        assert f'docs/images/{img_name}' in readme_en, f"Missing {img_name} in README.md"
        assert f'docs/images/{img_name}' in readme_pl, f"Missing {img_name} in README.pl.md"
        img_path = ROOT / 'docs/images' / img_name
        assert img_path.exists(), f"Image file {img_path} does not exist"
        assert img_path.stat().st_size > 0, f"Image file {img_path} is empty"

        with Image.open(img_path) as im:
            assert im.width > 0 and im.height > 0
            if img_name.endswith('.webp'):
                assert im.format == 'WEBP'
            elif img_name.endswith('.jpg'):
                assert im.format == 'JPEG'
            elif img_name.endswith('.png'):
                assert im.format == 'PNG'


def test_update_readme_images_creates_files(tmp_path):
    # Setup mock previews
    previews = tmp_path / 'output/previews'
    previews.mkdir(parents=True)

    # Mock PNG files
    sample = Image.new('RGBA', (100, 100), (200, 100, 50, 255))
    sample.save(previews / 'cover.png', 'PNG')
    sample.save(previews / 'house-closed-veranda.png', 'PNG')
    sample.save(previews / 'house-open-furnished.png', 'PNG')
    sample.save(previews / 'house-exploded.png', 'PNG')
    sample.save(previews / 'clay-family.png', 'PNG')

    updated = readme_images.update_readme_images(root=tmp_path, quiet=True)
    assert len(updated) >= 5

    docs_images = tmp_path / 'docs/images'
    assert (docs_images / 'cover.jpg').exists()
    assert (docs_images / 'house-closed.webp').exists()
    assert (docs_images / 'house-open.webp').exists()
    assert (docs_images / 'house-exploded.webp').exists()
    assert (docs_images / 'clay-family.webp').exists()
