"""Generate a 2-page A4 double-sided (duplex) printable checklist with checkboxes.

Uses ReportLab Platypus flowable architecture to guarantee:
- Exactly 2 pages A4 duplex with balanced content density.
- Zero text overlaps, automatic paragraph height calculation and clean word wraps.
- Crisp vector checkboxes, subtle zebra striping and clear typography.
"""
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

import naming

ROOT = Path(__file__).resolve().parents[1]

def register_fonts():
    fonts_dir = ROOT / 'source/fonts'
    if naming.FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(naming.FONT_REGULAR, str(fonts_dir / 'DejaVuSans.ttf')))
    if naming.FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(naming.FONT_BOLD, str(fonts_dir / 'DejaVuSans-Bold.ttf')))
    # Also register DejaVuSans aliases for backward compatibility if needed
    if 'DejaVuSans' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DejaVuSans', str(fonts_dir / 'DejaVuSans.ttf')))
    if 'DejaVuSans-Bold' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', str(fonts_dir / 'DejaVuSans-Bold.ttf')))


class Checkbox(Flowable):
    """Clean vector checkbox for manual pen check-offs."""
    def __init__(self, size=9.5, stroke_color=colors.HexColor('#2d4041'), fill_color=colors.white):
        super().__init__()
        self.size = size
        self.stroke_color = stroke_color
        self.fill_color = fill_color

    def wrap(self, availWidth, availHeight):
        return self.size + 4, self.size + 2

    def draw(self):
        self.canv.saveState()
        self.canv.setLineWidth(0.8)
        self.canv.setStrokeColor(self.stroke_color)
        self.canv.setFillColor(self.fill_color)
        self.canv.roundRect(1, 1, self.size, self.size, 1.5, fill=1, stroke=1)
        self.canv.restoreState()


def format_qty(qty, lang='pl'):
    if not qty:
        return ''
    q = str(qty).strip()
    q = q.replace(' szt.', '').replace(' pcs', '').replace(' pc', '').strip()
    if q.isdigit():
        if lang == 'pl':
            return f"{q} szt."
        return f"{q} pc" if q == '1' else f"{q} pcs"

    translations = {
        '1 m each': ('po 1 m', '1 m each'),
        '1 sheet': ('1 arkusz', '1 sheet'),
        'about 500 ml': ('ok. 500 ml', 'about 500 ml'),
        '1 pack': ('1 opakowanie', '1 pack'),
        'about 5 m': ('ok. 5 m', 'about 5 m'),
        '1 set': ('1 zestaw', '1 set'),
        'Choose quantities and fixings for the actual fit': ('wg potrzeb', 'as required'),
        'Dobrać ilości i mocowania do wykonania': ('wg potrzeb', 'as required'),
    }
    if q in translations:
        return translations[q][0] if lang == 'pl' else translations[q][1]
    return q


def make_page_decorations(lang='pl'):
    def draw_decorations(canvas, doc):
        canvas.saveState()
        page_w, page_h = A4
        page_num = canvas._pageNumber
        total_pages = 2
        is_pl = lang == 'pl'

        margin = 32
        content_w = page_w - 2 * margin

        NAVY = colors.HexColor('#13292a')
        TEAL = colors.HexColor('#1f6b6b')
        MUTED = colors.HexColor('#52696a')
        LINE = colors.HexColor('#cfd8d2')
        BG_PILL = colors.HexColor('#f5f7f5')

        # Top banner stripe
        canvas.setFillColor(TEAL)
        canvas.rect(margin, page_h - 18, content_w, 3, fill=1, stroke=0)

        if page_num == 1:
            eyebrow = "PRZEWODNIK WARSZTATOWY · ZANIM ZACZNIESZ" if is_pl else "WORKSHOP COMPANION · BEFORE YOU START"
            title = "Lista kontrolna: Przygotowanie warsztatu i elementy" if is_pl else "Checklist: Workshop Preparation & Fittings"
            subtitle = "Wydrukuj dwustronnie (A4 dupleks). Sprawdź i zaznacz wszystkie pozycje przed montażem." if is_pl else "Print double-sided (A4 duplex). Verify and check off all items before starting assembly."
            footer_note = "Strona 1 z 2 · Druga strona: Elementy specjalne, formatki sklejki i zasady montażu" if is_pl else "Page 1 of 2 · Reverse: Specialties, Plywood cut parts & Workshop rules"
        else:
            eyebrow = "PRZEWODNIK WARSZTATOWY · DRUGA STRONA ARKUSZA" if is_pl else "WORKSHOP COMPANION · SHEET BACK SIDE"
            title = "Lista kontrolna: Formatki sklejki i kontrola jakości" if is_pl else "Checklist: Plywood Cut Parts & Quality Control"
            subtitle = "Weryfikacja wymiarów formatek, przygotowanie podzespołów i krytyczne punkty kontroli." if is_pl else "Stock dimensions check, subassembly prep and critical quality control checks."
            footer_note = "Strona 2 z 2 · Format A4 zoptymalizowany do druku dwustronnego (dupleks)" if is_pl else "Page 2 of 2 · A4 format optimized for double-sided (duplex) printing"

        # Eyebrow
        canvas.setFont('DejaVuSans-Bold', 7)
        canvas.setFillColor(TEAL)
        canvas.drawString(margin, page_h - 29, eyebrow.upper())

        # Main title
        canvas.setFont('DejaVuSans-Bold', 14)
        canvas.setFillColor(NAVY)
        canvas.drawString(margin, page_h - 45, title)

        # Subtitle
        canvas.setFont('DejaVuSans', 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(margin, page_h - 56, subtitle)

        # Duplex badge
        badge_text = f"A4 DUPLEX · {page_num} / {total_pages}"
        canvas.setFont('DejaVuSans-Bold', 7.5)
        bw = canvas.stringWidth(badge_text, 'DejaVuSans-Bold', 7.5)
        canvas.setFillColor(BG_PILL)
        canvas.roundRect(page_w - margin - bw - 14, page_h - 50, bw + 14, 16, 3, fill=1, stroke=0)
        canvas.setFillColor(NAVY)
        canvas.drawString(page_w - margin - bw - 7, page_h - 43, badge_text)

        # Header dividing line
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.6)
        canvas.line(margin, page_h - 63, page_w - margin, page_h - 63)

        # Footer dividing line
        canvas.line(margin, 28, page_w - margin, 28)

        # Footer note
        canvas.setFont('DejaVuSans', 7.2)
        canvas.setFillColor(MUTED)
        canvas.drawString(margin, 18, footer_note)

        # Footer right
        right_text = f"{naming.NAME} · {page_num} / {total_pages}"
        rw = canvas.stringWidth(right_text, 'DejaVuSans', 7.2)
        canvas.drawString(page_w - margin - rw, 18, right_text)

        # Duplex center alignment mark
        canvas.setStrokeColor(TEAL)
        canvas.setLineWidth(0.5)
        canvas.line(page_w / 2 - 8, 9, page_w / 2 + 8, 9)

        canvas.restoreState()

    return draw_decorations


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

    # Styles
    styles = getSampleStyleSheet()

    style_builder = ParagraphStyle(
        'BuilderInfo',
        parent=styles['Normal'],
        fontName='DejaVuSans',
        fontSize=7.2,
        leading=9,
        textColor=colors.HexColor('#13292a'),
    )

    style_sec_hdr_left = ParagraphStyle(
        'SecHdrLeft',
        parent=styles['Normal'],
        fontName='DejaVuSans-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#13292a'),
    )

    style_sec_hdr_right = ParagraphStyle(
        'SecHdrRight',
        parent=styles['Normal'],
        fontName='DejaVuSans',
        fontSize=7.2,
        leading=9,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#52696a'),
    )

    style_code = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='DejaVuSans-Bold',
        fontSize=7.8,
        leading=9.5,
        textColor=colors.HexColor('#1f6b6b'),
    )

    style_desc = ParagraphStyle(
        'DescStyle',
        parent=styles['Normal'],
        fontName='DejaVuSans',
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor('#13292a'),
    )

    style_qty = ParagraphStyle(
        'QtyStyle',
        parent=styles['Normal'],
        fontName='DejaVuSans-Bold',
        fontSize=7.2,
        leading=9,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#13292a'),
    )

    CONTENT_W = 531
    COL_CHECK = 16
    COL_CODE = 44
    COL_QTY = 78
    COL_DESC = CONTENT_W - COL_CHECK - COL_CODE - COL_QTY  # 393 pt

    def make_section_header(title, count_text):
        t = Table(
            [[
                Paragraph(f"<b>{title.upper()}</b>", style_sec_hdr_left),
                Paragraph(count_text, style_sec_hdr_right)
            ]],
            colWidths=[CONTENT_W - 90, 90]
        )
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eef3f1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 6),
            ('RIGHTPADDING', (-1, -1), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LINEBEFORE', (0, 0), (0, 0), 3, colors.HexColor('#1f6b6b')),
        ]))
        return t

    def make_table(rows):
        t = Table(rows, colWidths=[COL_CHECK, COL_CODE, COL_DESC, COL_QTY])
        style = [
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 1.8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.35, colors.HexColor('#e8edea')),
        ]
        for i in range(len(rows)):
            bg = colors.HexColor('#ffffff') if i % 2 == 0 else colors.HexColor('#fbfcfb')
            style.append(('BACKGROUND', (0, i), (-1, i), bg))
        t.setStyle(TableStyle(style))
        return t

    def make_item_row(code, desc, qty, note=None):
        chk = Checkbox()
        code_p = Paragraph(code, style_code) if code else Paragraph('', style_code)
        
        # Build description paragraph
        if note:
            prefix = "Zastosowanie: " if is_pl else "Application: "
            # Check if note already starts with part description or application
            note_text = note if note.startswith(('Cztery', 'Jeden', 'Kołek', 'Szklenie', 'Klocki', 'Sztywne', 'Dwa', 'Sześć', 'Toczona', 'Dwanaście', 'Wytnij', 'Four', 'One', 'Cut', 'Buy', 'Twelve', 'Two', 'Six', 'Glue')) else f"{prefix}{note}"
            html = f"<b>{desc}</b><br/><font color='#52696a' size='6.4'>{note_text}</font>"
        else:
            html = f"<b>{desc}</b>"
            
        desc_p = Paragraph(html, style_desc)
        qty_str = format_qty(qty, lang)
        qty_p = Paragraph(qty_str, style_qty)
        return [chk, code_p, desc_p, qty_p]

    story = []

    # ================= PAGE 1 =================
    # Builder info banner
    info_text = (
        "<b>Wykonawca:</b> ___________________________    "
        "<b>Data:</b> ____________    "
        "<b>Status:</b> [ ] Gotowy do montażu"
    ) if is_pl else (
        "<b>Builder:</b> ___________________________    "
        "<b>Date:</b> ____________    "
        "<b>Status:</b> [ ] Ready to build"
    )
    b_table = Table([[Paragraph(info_text, style_builder)]], colWidths=[CONTENT_W])
    b_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f7f5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(b_table)
    story.append(Spacer(1, 4))

    # Categorize supplies
    g_tools = [s for s in supplies if s['group'] == 'Tools']
    g_adh = [s for s in supplies if s['group'] == 'Adhesives and finish']
    g_mat = [s for s in supplies if s['group'] == 'Materials']
    g_hw = [s for s in supplies if s['group'] == 'Hardware']
    g_cut = [s for s in supplies if s['group'] == 'Materials to cut']

    # Page 1: Fasteners (5) + Movable Hardware & Roof Assembly Fittings (8)
    fastener_ids = {'SC1', 'SC2', 'SC3', 'SP2', 'floor-supports'}
    g_fasteners = [s for s in g_hw if s['id'] in fastener_ids]
    
    movable_ids = {'HG1', 'HG2', 'MG1', 'SD1', 'DW1', 'FB1', 'CB1', 'PG1'}
    g_movable = [s for s in g_hw if s['id'] in movable_ids]

    # Page 2: Auxiliary hardware & specialty items (5) + Cut stock (13) + Rules (6)
    specialty_ids = {'TP1', 'FT1', 'BL2', 'AT1', 'LT1'}
    g_specialty = [s for s in g_hw if s['id'] in specialty_ids]

    # Section 1: Tools & Equipment (5 items)
    s1_title = "1. Narzędzia i przyrządy pomiarowe" if is_pl else "1. Tools & Measuring Equipment"
    s1_cnt = f"{len(g_tools)} pozycji" if is_pl else f"{len(g_tools)} items"
    story.append(make_section_header(s1_title, s1_cnt))
    s1_rows = []
    for s in g_tools:
        desc = s.get('description_pl' if is_pl else 'description', s['description'])
        qty = s.get('quantity_pl' if is_pl else 'quantity', s['quantity'])
        s1_rows.append(make_item_row('', desc, qty))
    story.append(make_table(s1_rows))
    story.append(Spacer(1, 4))

    # Section 2: Adhesives, Sealants & Finishes (7 items)
    s2_title = "2. Kleje, taśmy i powłoki wykończeniowe" if is_pl else "2. Adhesives, Tapes & Finishes"
    s2_items = g_adh + g_mat
    s2_cnt = f"{len(s2_items)} pozycji" if is_pl else f"{len(s2_items)} items"
    story.append(make_section_header(s2_title, s2_cnt))
    s2_rows = []
    for s in s2_items:
        desc = s.get('description_pl' if is_pl else 'description', s['description'])
        qty = s.get('quantity_pl' if is_pl else 'quantity', s['quantity'])
        s2_rows.append(make_item_row('', desc, qty))
    story.append(make_table(s2_rows))
    story.append(Spacer(1, 4))

    # Section 3: Screws, Shims & Brackets (5 items)
    s3_title = "3. Wkręty, podkładki i kątowniki konstrukcyjne" if is_pl else "3. Fasteners, Shims & Structural Brackets"
    s3_cnt = f"{len(g_fasteners)} pozycji" if is_pl else f"{len(g_fasteners)} items"
    story.append(make_section_header(s3_title, s3_cnt))
    s3_rows = []
    for s in g_fasteners:
        code = s['id'] if s['id'] != 'floor-supports' else 'KAT'
        desc = s.get('description_pl' if is_pl else 'description', s['description'])
        qty = s.get('quantity_pl' if is_pl else 'quantity', s['quantity'])
        use = s.get('use_pl' if is_pl else 'use', s.get('use', ''))
        s3_rows.append(make_item_row(code, desc, qty, use))
    story.append(make_table(s3_rows))
    story.append(Spacer(1, 4))

    # Section 4: Movable Hardware, Magnets & Roof Assemblies (8 items)
    s4_title = "4. Okucia ruchome, magnesy i osprzęt dachu" if is_pl else "4. Hinges, Magnets & Roof Assemblies"
    s4_cnt = f"{len(g_movable)} pozycji" if is_pl else f"{len(g_movable)} items"
    story.append(make_section_header(s4_title, s4_cnt))
    s4_rows = []
    for s in g_movable:
        code = s['id']
        desc = s.get('description_pl' if is_pl else 'description', s['description'])
        qty = s.get('quantity_pl' if is_pl else 'quantity', s['quantity'])
        use = s.get('use_pl' if is_pl else 'use', s.get('use', ''))
        s4_rows.append(make_item_row(code, desc, qty, use))
    story.append(make_table(s4_rows))

    # Hard page break to ensure Page 1 -> Page 2 duplex integrity
    story.append(PageBreak())

    # ================= PAGE 2 =================
    # Section 5: Auxiliary Hardware, Ballast & Lighting (5 items)
    s5_title = "5. Taśmy, filce, balast i oświetlenie" if is_pl else "5. Tapes, Felt Pads, Ballast & Lighting"
    s5_cnt = f"{len(g_specialty)} pozycji" if is_pl else f"{len(g_specialty)} items"
    story.append(make_section_header(s5_title, s5_cnt))
    s5_rows = []
    for s in g_specialty:
        code = s['id']
        desc = s.get('description_pl' if is_pl else 'description', s['description'])
        qty = s.get('quantity_pl' if is_pl else 'quantity', s['quantity'])
        use = s.get('use_pl' if is_pl else 'use', s.get('use', ''))
        s5_rows.append(make_item_row(code, desc, qty, use))
    story.append(make_table(s5_rows))
    story.append(Spacer(1, 4))

    # Section 6: Materials to Cut & Stock Parts
    s6_title = "6. Formatki i materiały do wycięcia" if is_pl else "6. Plywood Cut Parts & Trim Stock"
    s6_cnt = f"{len(g_cut)} pozycji" if is_pl else f"{len(g_cut)} items"
    story.append(make_section_header(s6_title, s6_cnt))
    s6_rows = []
    for s in g_cut:
        pid = s['id'].replace('material-', '')
        desc = s.get('description_pl' if is_pl else 'description', s['description'])
        qty = s.get('quantity_pl' if is_pl else 'quantity', s['quantity'])
        use = s.get('use_pl' if is_pl else 'use', s.get('use', ''))
        s6_rows.append(make_item_row(pid, desc, qty, use))
    story.append(make_table(s6_rows))
    story.append(Spacer(1, 4))

    # Section 7: Workshop Rules & Quality Checks
    s7_title = "7. Zasady warsztatowe i kontrola jakości" if is_pl else "7. Workshop Rules & Quality Control"
    s7_cnt = "6 wytycznych" if is_pl else "6 guidelines"
    story.append(make_section_header(s7_title, s7_cnt))

    field_rules_pl = [
        ("Przymiarka na sucho", "Przed nałożeniem kleju złóż każdy zespół na sucho. Sprawdź kąty prostoliniowe i swobodę ruchu."),
        ("Oznaczenia części", "Oznacz ołówkiem identyfikatory części (B01, DR1, W01) na niewidocznych po montażu powierzchniach."),
        ("Grubość sklejki", "Zmierz rzeczywistą grubość suwmiarką i przetestuj połączenia na próbkach T01/T02 przed klejeniem."),
        ("Ogranicznik wiercenia", "Przy wierceniu gniazd magnesów i otworów wkrętów zawsze stosuj ogranicznik głębokości (taśmę na wiertle)."),
        ("Czas schnięcia spoin", "Odczekaj pełen czas wiązania kleju podany przez producenta przed obciążeniem konstrukcji i stropów."),
        ("Czyste powierzchnie robocze", "Utrzymuj prowadnice szuflady, gniazda zawiasów i styki magnesów wolne od wycieków kleju i farby."),
    ]
    field_rules_en = [
        ("Dry-fit first", "Test every joint and subassembly without glue to verify squareness and clearance before committing adhesive."),
        ("Transfer part IDs", "Mark piece IDs (B01, DR1, W01) with pencil on faces that remain hidden after final assembly."),
        ("Verify plywood thickness", "Measure actual stock with calipers and test coupon joints T01/T02 before assembling structural parts."),
        ("Drilling depth stops", "Always use a depth collar or tape flag when boring blind magnet pockets and pilot screw holes."),
        ("Respect adhesive cure", "Allow full curing time recommended by glue manufacturer before loading floors or hanging shells."),
        ("Keep sliding seams clear", "Keep drawer tracks, hinge knuckles and magnet contact faces strictly clear of glue squeeze-out and paint."),
    ]
    rules = field_rules_pl if is_pl else field_rules_en
    s7_rows = []
    for r_title, r_desc in rules:
        chk = Checkbox()
        desc_p = Paragraph(f"<b>{r_title}:</b> <font color='#52696a'>{r_desc}</font>", style_desc)
        s7_rows.append([chk, Paragraph('', style_code), desc_p, Paragraph('', style_qty)])
    story.append(make_table(s7_rows))

    # Doc template with exact margins
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=32,
        rightMargin=32,
        topMargin=64,
        bottomMargin=28,
    )

    decorations = make_page_decorations(lang=lang)
    doc.build(story, onFirstPage=decorations, onLaterPages=decorations)
    print(f"Checklist PDF generated at: {output_path} ({output_path.stat().st_size} bytes)")
    return output_path


if __name__ == '__main__':
    generate(ROOT / 'output/viewer/checklist-pl.pdf', lang='pl')
    generate(ROOT / 'output/viewer/checklist-en.pdf', lang='en')
