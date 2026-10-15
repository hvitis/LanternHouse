"""Joint-aware plywood stack-up: worst-case gaps along each assembly chain with measured sheet thicknesses.

    .venv/bin/python source/stackup.py        (reads output/parts.json, writes output/reports/stackup.json)

thickness_check.py rebuilds the whole house with every sheet at the ends of its band and looks for lost
clearances, but it grows each part about its mid-plane, so it cannot say which face a joint references. Here each
chain names its datum and the parts whose thickness adds up along it (a floor resting on supports gains its own
thickness on top; three floors on one pillar share the pillar's length), and the gap is evaluated at both ends of
every thickness band in config thickness_tolerance. Cut dimensions (heights, widths, slot sizes) are taken as exact:
those depend on the cutter, not on the sheet. Solid-wood parts keep their size.
"""
from __future__ import annotations
import itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def band(cfg,t):
    lo,hi=cfg['thickness_tolerance'].get(f'{t:g}',(0,0));return lo,hi

def chain(name,datum,nominal,terms,need,note,cfg):
    """terms: [(sign, nominal thickness, what)] whose deviations add to the gap. Worst cases over all band ends."""
    devs=[band(cfg,t) for _,t,_ in terms]
    values=[nominal+sum(sign*d for (sign,_,_),d in zip(terms,combo)) for combo in itertools.product(*devs)] if terms else [nominal]
    lo,hi=min(values),max(values)
    return {'chain':name,'datum':datum,'nominal_mm':round(nominal,3),'min_mm':round(lo,3),'max_mm':round(hi,3),'need_mm':need,'pass':lo>=need[0]-1e-9 and (need[1] is None or hi<=need[1]+1e-9),
            'parts':[f'{"+" if s>0 else "-"}{what} ({t:g} mm)' for s,t,what in terms],'note':note}

def analyse(data):
    cfg=data['config'];T=cfg['thickness'];PT=cfg['partition'];pitch=cfg['floor_pitch'];fab=cfg['fabrication']
    fl=T['floor'];out=[]
    clear=pitch-fl;div=clear-PT['top_gap']
    # Floors: F00 on the plinth, F01 on metal supports fixed at set heights above F00, F02 on the pillar tops. A room's
    # height is its ceiling underside minus its floor top, so the floor below it eats into the room.
    out.append(chain('Ground-floor divider under F01','F00 top; F01 underside set by its metal supports',clear-div,[],(.2,None),'PT2 stands on F00 and must slide in under F01.',cfg))
    for k in (1,2):
        out.append(chain(f'Divider on storey {k+1}','support or pillar top under the ceiling',clear-div,[(-1,fl,'F01 floor it stands on')],(.2,None),'The floor plate rests on its supports: a thick plate raises the floor top and lowers the room.',cfg))
    # Pillar slots in F01 (cut 0.6 mm wider than the nominal pillar) and divider notches over the corner ribs.
    out.append(chain('P01 pillar in its F01 slot','slot width (cut)',fab['pillar_clearance'],[(-1,T['structure'],'P01 pillar')],(.1,None),'The floors slide down the pillars.',cfg))
    rib=data['parts']['J01']['thickness']
    out.append(chain('Rib in its divider notch',f'notch height {rib+1:g} mm (cut)',1.0,[(-1,rib,'J01 corner rib')],(.2,None),'The divider\'s rear notches slip over the corner ribs.',cfg))
    # Moving parts.
    out.append(chain('Opening wall past the floor edges','wall inner face',cfg['moving_clearance'],[(-1,T['wall'],'wall, if built to its outer face')],(1.0,None),'Floor plates keep moving_clearance from the inside of the closed walls.',cfg))
    out.append(chain('Opening shell under the roof ring','F00 top',2.0-cfg['shell_lift'],[],(.5,None),'Opening walls are 2 mm shorter than the fixed walls and hang shell_lift above F00; retained 420 mm sheet ends add their own tolerance.',cfg))
    out.append(chain('Veranda door over the deck','door bottom 2 mm above the threshold',2,[(-1,data['parts']['E03']['thickness'],'E03 deck')],(1.0,None),'The skirt and joists set the deck underside; the deck top is flush with the threshold.',cfg))
    ps,_=fab['plinth_floor_support'];dr=cfg['plinth']['drawer']
    out.append(chain('Drawer under the F00 seam strip','B01 top',cfg['plinth']['height']-fl-dr['height']-ps,[(-1,ps,'F00 seam support strip')],(.5,None),'The strip under F00 crosses the drawer bay; the drawer must still slide.',cfg))
    return out

def main():
    data=json.loads((ROOT/'output/parts.json').read_text());chains=analyse(data)
    report={'all_pass':all(c['pass'] for c in chains),'bands':data['config']['thickness_tolerance'],'chains':chains}
    out=ROOT/'output/reports';out.mkdir(parents=True,exist_ok=True);(out/'stackup.json').write_text(json.dumps(report,indent=2))
    for c in chains:print(f'{"PASS" if c["pass"] else "FAIL"}  {c["chain"]}: {c["min_mm"]:g} .. {c["max_mm"]:g} mm (need {c["need_mm"][0]:g}{"" if c["need_mm"][1] is None else " .. "+format(c["need_mm"][1],"g")})')
    if not report['all_pass']:raise SystemExit('Stack-up fails: see output/reports/stackup.json')

if __name__=='__main__':main()
