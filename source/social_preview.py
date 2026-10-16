"""Generate GitHub repository social media preview (1280x640 px).

Displays the 3D-rendered opened Lanternwood House with the project title set in DejaVuSans-Bold
(the font used on the supplier/specification PDF first page).
"""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import naming

ROOT = Path(__file__).resolve().parents[1]
W, H = 1280, 640

def generate(output=None, dark=True, furnished=True):
    # Load fonts (font from PDF first page: DejaVuSans-Bold)
    font_bold = ROOT / 'source/fonts/DejaVuSans-Bold.ttf'
    font_reg = ROOT / 'source/fonts/DejaVuSans.ttf'
    f_title = ImageFont.truetype(str(font_bold), 52)
    f_sub = ImageFont.truetype(str(font_reg), 22)
    f_badge = ImageFont.truetype(str(font_bold), 15)
    f_tag = ImageFont.truetype(str(font_bold), 12)

    if dark:
        img = Image.new('RGBA', (W, H), (18, 28, 33, 255))
        d = ImageDraw.Draw(img)
        # Ambient teal glow behind 3D house
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([680, 70, 1320, 690], fill=(25, 90, 110, 75))
        gd.ellipse([780, 140, 1220, 560], fill=(35, 125, 145, 55))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(60)))
        # Top brand accent stripe
        d.rectangle([0, 0, W, 4], fill=(25, 127, 152, 255))
        
        text_color = (255, 255, 255, 255)
        sub_color = (180, 205, 215, 255)
        badge_bg = (28, 48, 56, 255)
        badge_text = (100, 200, 220, 255)
        badge_border = (40, 75, 88, 255)
    else:
        img = Image.new('RGBA', (W, H), (247, 249, 248, 255))
        d = ImageDraw.Draw(img)
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([750, 120, 1250, 620], fill=(215, 230, 235, 120))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(50)))
        d.rectangle([0, 0, W, 4], fill=(25, 127, 152, 255))
        
        text_color = (30, 45, 50, 255)
        sub_color = (80, 105, 110, 255)
        badge_bg = (235, 242, 240, 255)
        badge_text = (25, 127, 152, 255)
        badge_border = (200, 218, 215, 255)

    # 3D Render of Opened House
    candidates = []
    if furnished:
        candidates += [ROOT / 'output/previews/house-open-furnished.png', ROOT / 'output/previews/house-open.png']
    else:
        candidates += [ROOT / 'output/previews/house-open.png', ROOT / 'output/previews/house-open-furnished.png']
    candidates.append(ROOT / 'docs/images/house-open.webp')

    house_path = next((p for p in candidates if p.exists()), None)
    if house_path:
        house_raw = Image.open(house_path).convert('RGBA')
        bbox = house_raw.getbbox()
        house_crop = house_raw.crop(bbox) if bbox else house_raw
        
        target_h = 560
        scale = target_h / house_crop.height
        target_w = int(house_crop.width * scale)
        house_scaled = house_crop.resize((target_w, target_h), Image.LANCZOS)
        
        hx = W - target_w - 50
        hy = (H - target_h) // 2 + 10
        
        # Soft ambient shadow underneath
        shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.ellipse([hx + 40, hy + target_h - 45, hx + target_w - 40, hy + target_h + 15], fill=(0, 0, 0, 110 if dark else 50))
        img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)))
        
        # Composite house model
        img.alpha_composite(house_scaled, (hx, hy))

    # Left content area: Category tag, Title, Subtitle, Feature Badges
    draw = ImageDraw.Draw(img)
    tx, ty = 80, 140

    tag_text = 'OPEN-SOURCE CAD & WOODWORKING'
    tag_w = f_tag.getlength(tag_text)
    draw.rounded_rectangle([tx, ty - 45, tx + tag_w + 24, ty - 17], radius=6, fill=badge_bg, outline=badge_border, width=1)
    draw.text((tx + 12, ty - 42), tag_text, font=f_tag, fill=badge_text)

    # Main Title using font from PDF first page
    draw.text((tx, ty), naming.NAME, font=f_title, fill=text_color)

    # Subtitle
    sub_lines = [
        'Complete FreeCAD workshop, cutting templates,',
        'A3 CNC sheets & 4-storey building guide'
    ]
    sy = ty + 75
    for sline in sub_lines:
        draw.text((tx, sy), sline, font=f_sub, fill=sub_color)
        sy += 32

    # Feature badges
    by = sy + 35
    bx = tx
    badges = [
        'FreeCAD 1.1+ 3D Model',
        'A3 CNC Cutting Sheets',
        '224-Page Workshop Manual'
    ]
    for b in badges:
        bw = f_badge.getlength(b)
        draw.rounded_rectangle([bx, by, bx + bw + 22, by + 34], radius=6, fill=badge_bg, outline=badge_border, width=1)
        draw.text((bx + 11, by + 8), b, font=f_badge, fill=text_color)
        bx += bw + 34
        if bx > 600:
            bx = tx
            by += 44

    # Save output image(s)
    out_paths = [Path(output)] if output else [
        ROOT / 'docs/images/social-preview.png',
        ROOT / '.github/social-preview.png'
    ]
    if not output and (ROOT / 'output').exists():
        out_paths.append(ROOT / 'output/social-preview.png')

    final_rgb = img.convert('RGB')
    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        final_rgb.save(p, 'PNG', optimize=True)
    return out_paths[0]

def main():
    p = argparse.ArgumentParser(description='Generate GitHub repository social media preview (1280x640 px)')
    p.add_argument('--output', '-o', help='Output file path (default: docs/images/social-preview.png and .github/social-preview.png)')
    p.add_argument('--light', action='store_true', help='Use light background palette')
    p.add_argument('--unfurnished', action='store_true', help='Use unfurnished architectural render')
    args = p.parse_args()
    out = generate(output=args.output, dark=not args.light, furnished=not args.unfurnished)
    print(f'Social preview saved: {out}')

if __name__ == '__main__':
    main()
