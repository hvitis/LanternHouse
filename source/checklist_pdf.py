"""Generate a 2-page A4 double-sided (duplex) printable checklist with checkboxes."""
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

ROOT = Path(__file__).resolve().parents[1]

def register_fonts():
    fonts_dir = ROOT / 'source/fonts'
    if 'DejaVuSans' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DejaVuSans', str(fonts_dir / 'DejaVuSans.ttf')))
    if 'DejaVuSans-Bold' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', str(fonts_dir / 'DejaVuSans-Bold.ttf')))

def draw_checkbox(c, x, y, size=10):
    c.saveState()
    c.setLineWidth(0.8)
    c.setStrokeColor(colors.HexColor('#2d4041'))
    c.setFillColor(colors.HexColor('#ffffff'))
    c.roundRect(x, y - size + 2, size, size, 1.5, fill=1, stroke=1)
    c.restoreState()

def generate(output_path, lang='pl', manifest_data=None):
    register_fonts()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if manifest_data is None:
        import assembly
        parts_data = json.loads((ROOT / 'output/parts.json').read_text())
        manifest_data = assembly.manifest(parts_data)

    supplies = manifest_data['supplies']
    is_pl = lang == 'pl'

    # Dimensions
    page_w, page_h = A4
    margin = 36  # ~12.7 mm
    content_w = page_w - 2 * margin

    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle('Moomin House Checklist' if not is_pl else 'Domek Muminków - Lista kontrolna')
    c.setAuthor('MoominsHouse')

    # Color palette matching viewer workspace
    NAVY = colors.HexColor('#13292a')
    TEAL = colors.HexColor('#1f6b6b')
    MUTED = colors.HexColor('#52696a')
    LINE = colors.HexColor('#cfd8d2')
    BG_BOX = colors.HexColor('#f5f7f5')
    ACCENT = colors.HexColor('#e8ece5')

    def draw_header(page_num, total_pages, title, eyebrow, subtitle):
        c.saveState()
        # Top banner line
        c.setFillColor(TEAL)
        c.rect(margin, page_h - 22, content_w, 3, fill=1, stroke=0)

        # Eyebrow
        c.setFont('DejaVuSans-Bold', 7)
        c.setFillColor(TEAL)
        c.drawString(margin, page_h - 34, eyebrow.upper())

        # Main title
        c.setFont('DejaVuSans-Bold', 16)
        c.setFillColor(NAVY)
        c.drawString(margin, page_h - 52, title)

        # Subtitle
        c.setFont('DejaVuSans', 8.5)
        c.setFillColor(MUTED)
        c.drawString(margin, page_h - 64, subtitle)

        # Duplex / Page badge (top right)
        badge_text = f"A4 DUPLEX · {page_num} / {total_pages}"
        c.setFont('DejaVuSans-Bold', 8)
        bw = c.stringWidth(badge_text, 'DejaVuSans-Bold', 8)
        c.setFillColor(BG_BOX)
        c.roundRect(page_w - margin - bw - 14, page_h - 56, bw + 14, 18, 3, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.drawString(page_w - margin - bw - 7, page_h - 48, badge_text)

        # Header dividing line
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(margin, page_h - 72, page_w - margin, page_h - 72)
        c.restoreState()

    def draw_footer(page_num, total_pages, footer_note):
        c.saveState()
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(margin, 36, page_w - margin, 36)

        c.setFont('DejaVuSans', 7.5)
        c.setFillColor(MUTED)
        c.drawString(margin, 24, footer_note)

        right_text = f"MoominsHouse · {page_num} / {total_pages}"
        rw = c.stringWidth(right_text, 'DejaVuSans', 7.5)
        c.drawString(page_w - margin - rw, 24, right_text)

        # Duplex alignment tick mark
        c.setStrokeColor(TEAL)
        c.setLineWidth(0.5)
        c.line(page_w / 2 - 8, 12, page_w / 2 + 8, 12)
        c.restoreState()

    def draw_section_hdr(y, title, count_text):
        c.saveState()
        c.setFillColor(BG_BOX)
        c.roundRect(margin, y - 4, content_w, 16, 2, fill=1, stroke=0)
        c.setFont('DejaVuSans-Bold', 9)
        c.setFillColor(NAVY)
        c.drawString(margin + 6, y, title.upper())
        if count_text:
            c.setFont('DejaVuSans', 7.5)
            c.setFillColor(MUTED)
            cw = c.stringWidth(count_text, 'DejaVuSans', 7.5)
            c.drawString(page_w - margin - cw - 6, y, count_text)
        c.restoreState()
        return y - 18

    # ================= PAGE 1 =================
    eyebrow_p1 = "Przewodnik warsztatowy · Zanim zaczniesz" if is_pl else "Workshop companion · Before you start"
    title_p1 = "Lista kontrolna: Narzędzia, kleje i okucia" if is_pl else "Checklist: Tools, Adhesives & Hardware"
    subtitle_p1 = "Wydrukuj dwustronnie (dupleks). Sprawdź i zaznacz wszystkie pozycje przed rozpoczęciem montażu." if is_pl else "Print double-sided (duplex). Verify and check off all items before starting assembly."

    draw_header(1, 2, title_p1, eyebrow_p1, subtitle_p1)
    footer_p1 = "Strona 1 z 2 · Druga strona arkusza zawiera wykaz materiałów i części do wycięcia" if is_pl else "Page 1 of 2 · Turn sheet over for Materials to cut and Plywood parts"
    draw_footer(1, 2, footer_p1)

    # Builder info bar
    info_y = page_h - 86
    c.saveState()
    c.setFillColor(ACCENT)
    c.roundRect(margin, info_y - 3, content_w, 15, 2, fill=1, stroke=0)
    c.setFont('DejaVuSans', 7.5)
    c.setFillColor(NAVY)
    b_label = "Wykonawca: _______________________    Data: ____________    Status: [ ] Kompletny" if is_pl else "Builder: _______________________    Date: ____________    Status: [ ] Ready to build"
    c.drawString(margin + 8, info_y, b_label)
    c.restoreState()

    cur_y = info_y - 20

    # Group supplies for Page 1: Tools, Adhesives & finish, Materials, Hardware
    g_tools = [s for s in supplies if s['group'] == 'Tools']
    g_adh = [s for s in supplies if s['group'] == 'Adhesives and finish']
    g_mat = [s for s in supplies if s['group'] == 'Materials']
    g_hw = [s for s in supplies if s['group'] == 'Hardware']

    # --- Section: Tools ---
    cur_y = draw_section_hdr(cur_y, "1. Narzędzia i przyrządy" if is_pl else "1. Tools & Workshop Equipment", f"{len(g_tools)} pozycji" if is_pl else f"{len(g_tools)} items")
    for s in g_tools:
        draw_checkbox(c, margin + 4, cur_y)
        desc = s.get('description_pl' if is_pl else 'description', s['description'])
        qty = s.get('quantity_pl' if is_pl else 'quantity', s['quantity'])
        c.setFont('DejaVuSans-Bold', 8)
        c.setFillColor(NAVY)
        c.drawString(margin + 20, cur_y - 6, desc)
        c.setFont('DejaVuSans', 7.5)
        c.setFillColor(MUTED)
        qw = c.stringWidth(qty, 'DejaVuSans', 7.5)
        c.drawString(page_w - margin - qw - 4, cur_y - 6, qty)
        cur_y -= 14

    cur_y -= 4

    # --- Section: Adhesives & Finish ---
    cur_y = draw_section_hdr(cur_y, "2. Kleje, materiały i preparaty wykończeniowe" if is_pl else "2. Adhesives, Materials & Finishes", f"{len(g_adh)+len(g_mat)} pozycji" if is_pl else f"{len(g_adh)+len(g_mat)} items")
    for s in (g_adh + g_mat):
        draw_checkbox(c, margin + 4, cur_y)
        desc = s.get('description_pl' if is_pl else 'description', s['description'])
        qty = s.get('quantity_pl' if is_pl else 'quantity', s['quantity'])
        c.setFont('DejaVuSans-Bold', 8)
        c.setFillColor(NAVY)
        c.drawString(margin + 20, cur_y - 6, desc)
        c.setFont('DejaVuSans', 7.5)
        c.setFillColor(MUTED)
        qw = c.stringWidth(qty, 'DejaVuSans', 7.5)
        c.drawString(page_w - margin - qw - 4, cur_y - 6, qty)
        cur_y -= 14

    cur_y -= 4

    # --- Section: Hardware & Fasteners ---
    cur_y = draw_section_hdr(cur_y, "3. Okucia, magnesy i łączniki mechaniczne" if is_pl else "3. Hardware, Magnets & Fasteners", f"{len(g_hw)} pozycji" if is_pl else f"{len(g_hw)} items")
    for s in g_hw:
        draw_checkbox(c, margin + 4, cur_y)
        pid = s['id']
        desc = s.get('description_pl' if is_pl else 'description', s['description'])
        qty = s.get('quantity_pl' if is_pl else 'quantity', s['quantity'])
        use = s.get('use_pl' if is_pl else 'use', s.get('use', ''))

        c.setFont('DejaVuSans-Bold', 8)
        c.setFillColor(TEAL)
        c.drawString(margin + 20, cur_y - 6, pid)

        # Description text
        c.setFont('DejaVuSans', 7.2)
        c.setFillColor(NAVY)
        # truncate or fit
        avail_w = content_w - 140
        lines = simpleSplit(desc, 'DejaVuSans', 7.2, avail_w)
        c.drawString(margin + 52, cur_y - 6, lines[0] if lines else '')

        # Qty and use
        c.setFont('DejaVuSans-Bold', 7.5)
        c.setFillColor(NAVY)
        c.drawString(page_w - margin - 85, cur_y - 6, f"{qty} szt." if is_pl else f"{qty} pcs")

        if len(lines) > 1 or use:
            cur_y -= 9
            sub = use or (lines[1] if len(lines) > 1 else '')
            c.setFont('DejaVuSans', 6.5)
            c.setFillColor(MUTED)
            c.drawString(margin + 52, cur_y - 6, sub[:75])
            cur_y -= 6
        else:
            cur_y -= 13

    c.showPage()

    # ================= PAGE 2 =================
    eyebrow_p2 = "Przewodnik warsztatowy · Arkusz 2 (Druga strona)" if is_pl else "Workshop companion · Sheet 2 (Back side)"
    title_p2 = "Lista kontrolna: Materiały do cięcia i formatki" if is_pl else "Checklist: Materials to Cut & Sheet Stock"
    subtitle_p2 = "Sprawdź wymiary, grubość i oznaczenia elementów przed przystąpieniem do montażu." if is_pl else "Verify dimensions, thickness and piece IDs before assembly."

    draw_header(2, 2, title_p2, eyebrow_p2, subtitle_p2)
    footer_p2 = "Strona 2 z 2 · Format A4 zoptymalizowany do druku dwustronnego (dupleks)" if is_pl else "Page 2 of 2 · A4 format optimized for double-sided (duplex) printing"
    draw_footer(2, 2, footer_p2)

    cur_y = page_h - 86

    # --- Section: Materials to cut ---
    g_cut = [s for s in supplies if s['group'] == 'Materials to cut']
    cur_y = draw_section_hdr(cur_y, "4. Materiały do wycięcia i formatki sklejki" if is_pl else "4. Materials to Cut & Plywood Stock", f"{len(g_cut)} pozycji" if is_pl else f"{len(g_cut)} items")

    for s in g_cut:
        draw_checkbox(c, margin + 4, cur_y)
        desc = s.get('description_pl' if is_pl else 'description', s['description'])
        qty = s.get('quantity_pl' if is_pl else 'quantity', s['quantity'])
        use = s.get('use_pl' if is_pl else 'use', s.get('use', ''))

        c.setFont('DejaVuSans-Bold', 8)
        c.setFillColor(NAVY)
        c.drawString(margin + 20, cur_y - 6, desc)

        c.setFont('DejaVuSans-Bold', 8)
        c.setFillColor(TEAL)
        qw = c.stringWidth(f"{qty} szt." if is_pl else f"{qty} pcs", 'DejaVuSans-Bold', 8)
        c.drawString(page_w - margin - qw - 4, cur_y - 6, f"{qty} szt." if is_pl else f"{qty} pcs")

        if use:
            cur_y -= 9
            c.setFont('DejaVuSans', 7)
            c.setFillColor(MUTED)
            c.drawString(margin + 20, cur_y - 6, f"Zastosowanie: {use}" if is_pl else f"Use: {use}")
            cur_y -= 8
        else:
            cur_y -= 15

    cur_y -= 8

    # --- Section: Workshop Field Rules & Checks ---
    cur_y = draw_section_hdr(cur_y, "5. Zasady warsztatowe i kontrola jakości" if is_pl else "5. Workshop Rules & Quality Control", "Zalecenia" if is_pl else "Guidelines")

    field_rules_pl = [
        ("Zawsze przymierzaj na sucho", "Przed nałożeniem kleju złóż każdy zespół na sucho. Sprawdź kąty i swobodę ruchu elementów."),
        ("Przenieś oznaczenia części", "Oznacz ołówkiem identyfikatory części (np. B01, DR1, W01) na niewidocznych po montażu powierzchniach."),
        ("Kontroluj grubość sklejki", "Zmierz rzeczywistą grubość suwmiarką i przetestuj połączenia na próbkach T01/T02 przed montażem."),
        ("Ogranicznik głębokości wiercenia", "Przy wierceniu gniazd magnesów i otworów wkrętów zawsze stosuj ogranicznik głębokości (np. taśmę na wiertle)."),
        ("Czas schnięcia spoin", "Odczekaj pełen czas wiązania kleju podany przez producenta przed obciążeniem konstrukcji lub montażem zawiasów."),
        ("Swoboda ruchu", "Utrzymuj powierzchnie ślizgowe szuflady, gniazda zawiasów i styki magnesów wolne od wycieków kleju i farby."),
    ]
    field_rules_en = [
        ("Always dry-fit first", "Test every joint and subassembly without glue to verify angles and clearance before committing adhesive."),
        ("Transfer part IDs", "Mark piece IDs (e.g. B01, DR1, W01) with pencil on faces that remain hidden after final assembly."),
        ("Verify plywood thickness", "Measure actual stock with calipers and test coupon joints T01/T02 before cutting or assembling structural parts."),
        ("Use depth stops when drilling", "Always use a depth collar or tape flag when boring blind magnet pockets and pilot screw holes."),
        ("Respect adhesive cure times", "Allow full curing time recommended by the glue manufacturer before loading floors or hanging wall shells."),
        ("Keep sliding seams clear", "Keep drawer tracks, hinge knuckles and magnet contact faces strictly clear of glue squeeze-out and paint."),
    ]
    rules = field_rules_pl if is_pl else field_rules_en

    for title, desc in rules:
        draw_checkbox(c, margin + 4, cur_y)
        c.setFont('DejaVuSans-Bold', 8)
        c.setFillColor(NAVY)
        c.drawString(margin + 20, cur_y - 6, f"{title}:")
        tw = c.stringWidth(f"{title}:", 'DejaVuSans-Bold', 8)
        c.setFont('DejaVuSans', 7.5)
        c.setFillColor(MUTED)
        c.drawString(margin + 24 + tw, cur_y - 6, desc)
        cur_y -= 14

    c.save()
    print(f"Checklist PDF generated at: {output_path} ({output_path.stat().st_size} bytes)")
    return output_path

if __name__ == '__main__':
    generate(ROOT / 'output/viewer/checklist-pl.pdf', lang='pl')
    generate(ROOT / 'output/viewer/checklist-en.pdf', lang='en')
