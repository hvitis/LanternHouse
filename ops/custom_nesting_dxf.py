"""Custom plywood stock calculation and DXF cut generator for 500x300 (3mm) and 400x300 (6mm).

Uses existing MoominsHouse calculation pipeline, stock optimizer (source/stock.py),
nesting engine (source/nest.py), CNC cutting path extractor (source/cnc.py), and DXF R12 writer (source/dxf_r12.py).
"""
import copy, json, math, os, sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))

import cnc, model, nest, stock
from dxf_r12 import DXF, COLOURS, thickness_layer as layer
from shapely.geometry import Polygon, box

OUTPUT_DIR = ROOT / 'output/custom_500x300_400x300'
MASTER_DXF = OUTPUT_DIR / 'Moomin-House-Custom-Cut-500x300-400x300.dxf'
REPORT_JSON = OUTPUT_DIR / 'custom-stock-report.json'

COLUMNS = 5
GAP = 20
THICKNESS_GAP = 60

def prepare_model():
    """Build model and adjust elements that exceed sheet dimensions."""
    data = model.build()
    parts = data['parts']
    
    # P01 is 402.0 mm, exceeding 400 mm stock for 6mm.
    # Split P01 into two functional sections at Floor 2 level:
    # Lower section: 268.0 mm (Z=12 to Z=280)
    # Upper section: 134.0 mm (Z=280 to Z=414)
    # Total: 402.0 mm
    if 'P01' in parts:
        orig = parts['P01']
        del parts['P01']
        
        # P01A - Lower pillar
        parts['P01A'] = {
            'id': 'P01A',
            'name': 'Lower frame pillar (foot to floor 2)',
            'thickness': 6.0,
            'outer': [[0, 0], [orig['width'], 0], [orig['width'], 268.0], [0, 268.0]],
            'cuts': [],
            'holes': [],
            'quantity': 4,
            'category': 'Structure',
            'width': orig['width'],
            'height': 268.0,
            'origin_shift': [0, 0],
            'note': 'Lower pillar section (bottom Z12 to underside of floor 2). Fits 400x300 stock.'
        }
        
        # P01B - Upper pillar
        parts['P01B'] = {
            'id': 'P01B',
            'name': 'Upper frame pillar (floor 2 to attic)',
            'thickness': 6.0,
            'outer': [[0, 0], [orig['width'], 0], [orig['width'], 134.0], [0, 134.0]],
            'cuts': [],
            'holes': [],
            'quantity': 4,
            'category': 'Structure',
            'width': orig['width'],
            'height': 134.0,
            'origin_shift': [0, 0],
            'note': 'Upper pillar section (floor 2 top to attic floor underside). Fits 400x300 stock.'
        }
    
    return data

def optimize_placement(data):
    """Run multi-order nesting optimization using ProcessPoolExecutor."""
    cfg = data['config']
    spacing = cfg.get('nest_spacing', 3.0)
    margin = cfg.get('stock_margin', 10.0)
    
    # 3mm on 500x300, 6mm on 400x300
    target_stocks = {
        3.0: {'size': [300, 500], 'key': '500x300', 'prefix': 'PLY3-CUST'},
        6.0: {'size': [300, 400], 'key': '400x300', 'prefix': 'PLY6-CUST'}
    }
    
    all_sheets = []
    stats = {}
    
    for t, spec in target_stocks.items():
        units = [
            (pid, q + 1, Polygon(p['outer']))
            for pid, p in data['parts'].items()
            if p['thickness'] == t and not p.get('render_only') and p['category'] not in model.BOUGHT
            for q in range(p['quantity'])
        ]
        
        print(f'Optimizing {t:g} mm ({len(units)} pieces) on {spec["key"]}...', flush=True)
        jobs = [
            (t, order, spacing, margin, spec['key'], 999, [])
            for order in nest.orders(units)
        ]
        
        workers = max(1, min(len(jobs), (os.cpu_count() or 2) - 1))
        with ProcessPoolExecutor(workers) as pool:
            plans = list(pool.map(nest.pack_order, jobs))
        
        best = nest.best_plan(plans)
        print(f'-> {t:g} mm won with {len(best)} sheets (out of {len(plans)} order variants)', flush=True)
        
        total_part_area = sum(u[2].area for u in units)
        sheet_w, sheet_h = sorted(spec['size'], reverse=True)
        total_sheet_area = len(best) * (sheet_w * sheet_h)
        utilization = total_part_area / total_sheet_area * 100
        
        for idx, s in enumerate(best, 1):
            s['id'] = f'{spec["prefix"]}-{idx:02d}'
            area_used = sum(Polygon(item['outer']).area for item in s['items'])
            s['outer_profile_utilization_percent'] = round(area_used / (s['width'] * s['height']) * 100, 1)
            all_sheets.append(s)
            
        stats[f'{t:g}mm'] = {
            'sheet_size': f'{sheet_w}x{sheet_h}',
            'sheet_count': len(best),
            'parts_count': len(units),
            'total_part_area_m2': round(total_part_area / 1e6, 4),
            'total_sheet_area_m2': round(total_sheet_area / 1e6, 4),
            'material_utilization_percent': round(utilization, 1),
            'sheets': [
                {
                    'id': s['id'],
                    'parts': len(s['items']),
                    'utilization_percent': s['outer_profile_utilization_percent'],
                    'unique_parts': sorted(set(i['part'] for i in s['items']))
                }
                for s in best
            ]
        }
        
    return all_sheets, stats

def layout_slots(sheets):
    """Lower-left corner of each sheet's slot for DXF export."""
    rows = []
    for s in sheets:
        if not rows or rows[-1][0]['thickness'] != s['thickness'] or len(rows[-1]) == COLUMNS:
            rows.append([])
        rows[-1].append(s)
    slots = {}
    y = 0
    for i in range(len(rows) - 1, -1, -1):
        x = 0
        for s in rows[i]:
            slots[s['id']] = (x, y)
            x += s['width'] + GAP
        if i:
            y += max(s['height'] for s in rows[i]) + (GAP if rows[i-1][0]['thickness'] == rows[i-1][0]['thickness'] else THICKNESS_GAP)
    return slots

def export_dxfs(data, sheets, stats):
    """Export master DXF and individual sheet DXFs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dxf_single_dir = OUTPUT_DIR / 'sheets'
    dxf_single_dir.mkdir(parents=True, exist_ok=True)
    
    slots = layout_slots(sheets)
    master_dxf = DXF()
    sheet_records = []
    
    for s in sheets:
        ox, oy = slots[s['id']]
        lname = layer(s['thickness'])
        curves = cnc.through_cuts(data, s)
        
        # Individual sheet DXF
        indiv_dxf = DXF()
        # Add sheet boundary box
        sw, sh = s['width'], s['height']
        indiv_dxf.polyline([[0, 0], [sw, 0], [sw, sh], [0, sh]], 'STOCK_OUTLINE', closed=True)
        # Add label text
        indiv_dxf.text(10, sh - 15, 8.0, f'{s["id"]} ({s["thickness"]:g}mm {sw}x{sh})', 'ENGRAVE_IDS')
        
        for kind, curve in curves:
            if kind == 'circle':
                x, y, r = curve
                # Master DXF
                master_dxf.circle(x + ox, y + oy, r, lname)
                # Individual DXF
                indiv_dxf.circle(x, y, r, lname)
            else:
                # Master DXF
                master_dxf.polyline([(x + ox, y + oy) for x, y in curve], lname, closed=kind == 'polygon')
                # Individual DXF
                indiv_dxf.polyline([(x, y) for x, y in curve], lname, closed=kind == 'polygon')
                
        # Also draw sheet boundary on master DXF on a FRAME layer
        master_dxf.polyline([[ox, oy], [ox + sw, oy], [ox + sw, oy + sh], [ox, oy + sh]], f'FRAME_{s["thickness"]:g}MM', closed=True)
        master_dxf.text(ox + 10, oy + sh - 15, 8.0, s['id'], 'ENGRAVE_IDS')
        
        indiv_path = dxf_single_dir / f'{s["id"]}.dxf'
        indiv_dxf.save(indiv_path)
        
        sheet_records.append({
            'id': s['id'],
            'thickness_mm': s['thickness'],
            'size_mm': [s['width'], s['height']],
            'parts': len(s['items']),
            'paths': len(curves),
            'origin_mm': [ox, oy]
        })
        
    master_dxf.save(MASTER_DXF)
    
    # Save report JSON
    report = {
        'title': 'Moomin House Custom Plywood Optimization (500x300 3mm & 400x300 6mm)',
        'summary': {
            'plywood_3mm_500x300': stats['3mm']['sheet_count'],
            'plywood_6mm_400x300': stats['6mm']['sheet_count'],
            'total_sheets': stats['3mm']['sheet_count'] + stats['6mm']['sheet_count']
        },
        'statistics': stats,
        'master_dxf': str(MASTER_DXF.relative_to(ROOT)),
        'sheets_count': len(sheets)
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2))
    print(f'Master DXF written to: {MASTER_DXF}')
    print(f'Report written to: {REPORT_JSON}')
    return report

def main():
    print('1. Preparing model and adjusting elements...')
    data = prepare_model()
    
    print('2. Running multi-order nesting optimization to save space...')
    sheets, stats = optimize_placement(data)
    
    print('3. Exporting DXF files...')
    report = export_dxfs(data, sheets, stats)
    
    print('\n================ RESULTS ================')
    print(f'3mm (500x300): {stats["3mm"]["sheet_count"]} sheets (utilization: {stats["3mm"]["material_utilization_percent"]}%)')
    print(f'6mm (400x300): {stats["6mm"]["sheet_count"]} sheets (utilization: {stats["6mm"]["material_utilization_percent"]}%)')
    print(f'Total sheets: {report["summary"]["total_sheets"]} sheets')
    print('=========================================')

if __name__ == '__main__':
    main()
