# Moomin House: Comprehensive Risk Assessment & Safety Engineering Report

This document records the structural, mechanical, chemical, and child safety risks identified for the CNC birch plywood Moomin House. It incorporates findings from **CalculiX Finite Element Analysis (FEA)**, structural timber analytics (**Eurocode 5 / EN 1995-1-1**), and international toy safety compliance directives (**EN 71-1, EN 71-3, ASTM F963, and 16 CFR 1500/1501**) with specific emphasis on usage by a **3-year-old child**.

---

## 1. Executive Summary

| Risk Category | Total Identified | Critical (🔴) | High (🟡) | Medium (🔵) |
| :--- | :---: | :---: | :---: | :---: |
| **Child Safety & Biomechanical (3yo Usage)** | 8 | 5 | 2 | 1 |
| **Structural & Hardware Stress (FEA / Timber)** | 7 | 4 | 2 | 1 |
| **Total Identified Hazards** | **15** | **9** | **4** | **2** |

---

## 2. Child Safety & Regulatory Hazards (3-Year-Old Play)

### 🔴 RISK-01: High-Power Neodymium Magnet Ingestion & Bowel Perforation
- **Affected Parts / Code**: `MC1` (catch block), `GP1` (stop post), `config.json` (`magnets.magnet: [8.0, 3.0]`, `magnets.disc: [10.0, 1.0]`).
- **Standard Violated**: **EN 71-1 Clause 4.23**, **ASTM F963 Section 4.38** (Magnetic Toys).
- **Physical Mechanism**:
  - The model uses $\varnothing 8 \times 3\text{ mm}$ N35 neodymium magnets bonded with epoxy in shallow wooden pockets.
  - The calculated magnetic flux index is **$\approx 452\text{ kG}^2\cdot\text{mm}^2$**, which is **$9\times$ higher than the legal maximum limit ($50\text{ kG}^2\cdot\text{mm}^2$)** for ingestible magnets.
  - Seasonal humidity shifts cause plywood to expand and contract, degrading epoxy bonds. Toddlers chew surfaces and pick at seams with teeth.
- **Consequence**: Swallowing two magnets (or one magnet and one steel disc) causes them to attract through intestinal folds. The intense compression pinches blood flow, leading to tissue necrosis, gastrointestinal perforation, peritonitis, septic shock, and fatal internal injury.
- **Required Remediation**:
  - Eliminate loose or surface-epoxied high-power magnets.
  - If magnetic latching is required, magnets must be **fully enclosed inside permanently ultrasonic-welded or mechanically locked, non-accessible wooden/plastic housings** that pass EN 71-1 drop ($850\text{ mm}$), torque ($0.34\text{ N}\cdot\text{m}$), and tension ($90\text{ N}$) abuse tests.
  - Recommended alternative: Wooden friction detents or child-safe low-force spring catches.

---

### 🔴 RISK-02: Overturning & Tower Tip-Over Crush Hazard
- **Affected Parts / Code**: Full house assembly (`height = 838.4 mm`, `tower_diameter = 326.7 mm`, `base_diameter = 522.7 mm`, total mass $\approx 7.0\text{–}8.5\text{ kg}$).
- **Standard Violated**: **ASTM F963 Section 4.15** (Stability), **ISO 8124-1**.
- **Physical Mechanism**:
  - The house stands $84\text{ cm}$ tall—nearly the full height of a standing 3-year-old ($90\text{–}95\text{ cm}$).
  - When the two $1.2\text{ kg}$ wall shells swing open to $100^\circ$, the center of gravity shifts forward.
  - A toddler weighs $14\text{–}15\text{ kg}$ and frequently uses furniture to pull themselves up to stand. A horizontal pull of $35\text{ N}$ at the attic window or upper wall ($Z \approx 700\text{ mm}$) creates an overturning moment of $24.5\text{ N}\cdot\text{m}$, exceeding the base resisting moment ($15.1\text{ N}\cdot\text{m}$).
- **Consequence**: The $8\text{ kg}$ solid wood house overturns and collapses onto the child, causing concussions, facial fractures, or blunt impact trauma.
- **Required Remediation**:
  - Supply a rear wall-anchoring anti-tip safety bracket.
  - Widen the ground plinth footprint or install weighted low-profile steel ballast plates in the plinth base.

---

### 🔴 RISK-03: $8\text{ mm}$ Finger Trapping & Crushing Shear Zone
- **Affected Parts / Code**: `PT1` / `PT2` (`partition.front_gap = 8.0 mm`), `W01`–`W12` closing seams.
- **Standard Violated**: **EN 71-1 Clause 4.10** (Moving Parts & Finger Entrapment).
- **Physical Mechanism**:
  - Under toy safety standards, moving components must **not** create accessible gaps between **$5.0\text{ mm}$ and $12.0\text{ mm}$** if moving parts have substantial closing force or momentum.
  - The $8.0\text{ mm}$ gap between the internal room divider wall and the closing outer wall shell falls precisely into the dangerous pinch envelope.
- **Consequence**: A child resting their fingers on the divider frame while slamming the outer shell shut will suffer finger bone fractures or severe crush lacerations.
- **Required Remediation**:
  - Redesign partition gap to either **$\le 3.0\text{ mm}$ (finger exclusion)** or **$\ge 15.0\text{ mm}$ (free clearance)**.
  - Install soft elastomer/silicone edge dampers along the closing facet perimeter.

---

### 🔴 RISK-04: Eye Impalement & Puncture from Pointed Roof Finial
- **Affected Parts / Code**: `FN01` (`source/model.py`, apex at $Z = 838.4\text{ mm}$).
- **Standard Violated**: **EN 71-1 Clause 4.12** (Sharp Points & Protrusions).
- **Physical Mechanism**:
  - The spire tapers to a sharp wooden tip ($R < 1.5\text{ mm}$) positioned at $84\text{ cm}$ height—directly at eye level for a standing, seated, or kneeling toddler.
- **Consequence**: Stumbling, falling, or bending forward over the house risks ocular puncture, corneal tearing, or facial puncture wounds.
- **Required Remediation**:
  - Replace the tapered finial spire with a **smooth spherical wooden ball ($\varnothing \ge 35\text{ mm}$)** or a soft, deformable silicone finial.

---

### 🔴 RISK-05: Choking Hazards from Detachable Small Parts
- **Affected Parts / Code**: Door handles `E02` ($13.1 \times 7.5 \times 3.0\text{ mm}$), M3 washers and nuts (`FS-RoofPivot`), miniature balusters `C09`, shims `A06`, window bars `D01`/`D02`.
- **Standard Violated**: **16 CFR 1501**, **EN 71-1 Clause 4.11** (Small Parts Test Cylinder $\varnothing 31.7 \times 57.1\text{ mm}$).
- **Physical Mechanism**:
  - Door handles are small surface-glued wooden rectangles ($13\text{ mm}$ long). Toddler biting or pulling with $> 50\text{ N}$ force will shear the glue line.
  - If the roof captive bolt is unscrewed, small M3 washers ($\varnothing 6\text{ mm}$) and nuts become loose.
- **Consequence**: Inhalation or ingestion of small parts leading to airway obstruction and asphyxiation.
- **Required Remediation**:
  - Eliminate glued surface door handles; machine recessed finger pulls or through-tenoned handles.
  - Use captive, tamper-proof architectural hardware with permanent high-strength threadlocker.
  - Ensure all loose furniture pieces have minimum dimensions $\ge 35\text{ mm}$ in all axes.

---

### 🟡 RISK-06: Splintering & Mouth Laceration from Fragile Window Bars
- **Affected Parts / Code**: `D01`, `D02` ($3.6\text{ mm}$ wide, $3.0\text{ mm}$ thick birch veneer strips).
- **Standard Violated**: **EN 71-1 Clause 4.1** (Material Cleanliness & Integrity).
- **Physical Mechanism**:
  - $3.6 \times 3.0\text{ mm}$ strips are brittle and snap under $< 15\text{ N}$ finger pressure.
  - Fracture along veneer grain creates sharp, needle-like splinters.
- **Consequence**: Mouth and hand lacerations, embedded wood splinters.
- **Required Remediation**:
  - CNC-rout window frames as single unified cutouts directly in the $6\text{ mm}$ wall panels rather than gluing thin applied bars.

---

### 🟡 RISK-07: Toxicity & Fragility of Oven-Hardening Polymer Clay Figures
- **Affected Parts / Code**: `source/clay.py` (Moomintroll, Moominmamma, Moominpappa).
- **Standard Violated**: **EN 71-3** (Chemical Migration), **EN 71-1** (Drop & Impact Test).
- **Physical Mechanism**:
  - Home-baked polymer clay figures (e.g. PVC-based FIMO/Sculpey) are brittle when dropped on tile or hardwood floors, fracturing into small sharp shards.
  - Non-certified polymer clays may contain plasticizers and phthalates unsuitable for children who chew toys.
- **Consequence**: Ingestion of plastic shards; toxic chemical exposure during mouthing.
- **Required Remediation**:
  - Replace clay figures with **solid turned hardwood (beech/maple)** finished with non-toxic saliva-proof beeswax/oil, or **molded food-grade silicone**.

---

### 🔵 RISK-08: Plinth Drawer Foot Impact & Trapping
- **Affected Parts / Code**: `B02`, `B03` ($205.3\text{ mm}$ travel, no retention stop).
- **Standard Violated**: **EN 71-1 Clause 4.15**.
- **Physical Mechanism**:
  - The drawer pulls out $205\text{ mm}$ without a captive stop. An energetic pull removes the drawer entirely from the base.
- **Consequence**: Heavy wooden drawer loaded with accessories falls directly onto toddler's toes.
- **Required Remediation**:
  - Install a captive wooden stop dowel inside the plinth cavity preventing complete pull-out.

---

## 3. Structural, Fastener & FEA Stress Hotspots

The following structural red spots were pinpointed using **FreeCAD FEM** and **CalculiX (`ccx`)** static stress analysis under realistic usage scenarios:

```
[Roof Lifting Force: 32 N] ──> E08 Turn-Button (Stress: 53.9 MPa > 19.7 MPa) ──> 🔴 SNAP/TEAR-OUT (SF 0.37)
[Child Lean on Wall: 25 N] ──> HG-Wall Top Screw (Tension: 82.0 N > 31.0 N)  ──> 🔴 PULL-OUT (SF 0.38)
[Floor Rim Push: 40 N]    ──> F01 Seam Batten (Bending: 356 MPa > 19.7 MPa)  ──> 🔴 SEAM COLLAPSE (SF 0.06)
[Floor Notch Tension]     ──> P01 Pillar Slots (Kt = 3.2, Notch: 16.6 MPa)   ──> 🔴 GRAIN SPLITTING (SF 0.19)
```

### 🔴 RISK-09: Floor Seam Collapse Under Cantilever Live Load
- **Affected Parts**: `F01` (front floor), `F01B` (rear floor), `fabrication.floor_support: [4, 4]`.
- **FEA Result**: Bending stress on $4 \times 4\text{ mm}$ support strip: **$356.2\text{ MPa}$** (Allowable: $19.7\text{ MPa}$, **Safety Factor: $0.06$**).
- **Physical Mechanism**: When front walls are swung open, `F01` cantilevers forward without perimeter wall support. A child pressing down on the front rim ($40\text{ N}$) causes the tiny $4 \times 4\text{ mm}$ glue strip to snap instantly, collapsing the floor.
- **Remediation**: Replace $4 \times 4\text{ mm}$ strip with a **$6 \times 25\text{ mm}$ continuous birch plywood reinforcement batten** tied into the `P01` pillars, or CNC mill interlocking puzzle joints between `F01` and `F01B`.

---

### 🔴 RISK-10: Wall Hinge Fastener Prying & Screw Pull-Out
- **Affected Parts**: `HG-WallRight` / `HG-WallLeft`, `SC1` wood screws ($\varnothing 2.0 \times 12\text{ mm}$), `A02` backing block.
- **Stress Result**: Top hinge prying tension: **$82.0\text{ N}$** (Allowable pullout: $31.0\text{ N}$, **Safety Factor: $0.38$**).
- **Physical Mechanism**: A $12\text{ mm}$ screw through $1\text{ mm}$ hinge $+ 0.9\text{ mm}$ shim $+ 6\text{ mm}$ wall penetrates only $4.1\text{ mm}$ into backing block `A02`, leaving only $2.1\text{ mm}$ of effective full thread. Under door sagging and dynamic toddler tugging, the screw strips out.
- **Remediation**: Upgrade to **$\varnothing 2.5 \times 16\text{ mm}$ wood screws** or **M2.5 through-machine screws with dome cap nuts** on the interior.

---

### 🔴 RISK-11: Pillar Cutout Notch Stress Concentration & Delamination
- **Affected Parts**: `F01B`, `F02B`, `F00B` (rectangular slots for `P01` pillars).
- **Stress Result**: Notch stress: **$16.6\text{ MPa}$** (Allowable cross-grain tension: $3.2\text{ MPa}$, **Safety Factor: $0.19$**).
- **Physical Mechanism**: Sharp $90^\circ$ inside corners from CNC routing produce stress concentration ($K_t \approx 3.2$). Cross-grain tension exceeds the inter-veneer tensile limit, causing fatigue cracks to propagate along the wood grain.
- **Remediation**: Add CNC **dogbone relief fillets ($R \ge 2.0\text{ mm}$)** on all 4 corners of every slot.

---

### 🔴 RISK-12: Roof Turn-Button Fracture When Lifted by Roof
- **Affected Parts**: `E08` ($3\text{ mm}$ birch plywood turn-button).
- **FEA Result**: Peak von Mises stress: **$53.9\text{ MPa}$** (Allowable: $19.7\text{ MPa}$, **Safety Factor: $0.37$**).
- **Physical Mechanism**: Lifting the $7\text{ kg}$ house by the roof without releasing the turn-buttons concentrates $32\text{ N}$ vertical shear per button across a thin $3\text{ mm}$ net section around the $\varnothing 3.2\text{ mm}$ bolt.
- **Remediation**: Increase thickness from **$3.0\text{ mm}$ to $6.0\text{ mm}$**, widen the neck from $16\text{ mm}$ to $22\text{ mm}$, and fit a wide $\varnothing 12\text{ mm}$ steel washer under the screw head.

---

### 🟡 RISK-13: Miniature Door Hinge Screw Pull-Out
- **Affected Parts**: Entrance doors `E01`, `SC2` screws ($\varnothing 1.6 \times 8\text{ mm}$), backing strip `A03`.
- **Stress Result**: Pullout tension: **$86.2\text{ N}$** (Allowable: $47.3\text{ N}$, **Safety Factor: $0.55$**).
- **Physical Mechanism**: A toddler pushing or pulling the open door beyond $90^\circ$ levers against the miniature $1.6\text{ mm}$ screws, pulling them out of the narrow $8\text{ mm}$ strip.
- **Remediation**: Increase screw size to **$\varnothing 2.0 \times 10\text{ mm}$** and widen strip `A03` from $12\text{ mm}$ to $16\text{ mm}$.

---

### 🟡 RISK-14: Garden Stop Post End-Grain Screw Stripping
- **Affected Parts**: `GP1` garden stop post, `SC3` screw ($\varnothing 3.0 \times 16\text{ mm}$).
- **Stress Result**: Impact prying tension: **$54.0\text{ N}$** (End-grain fatigue capacity: $59.8\text{ N}$, **Safety Factor: $1.11$**).
- **Physical Mechanism**: A single screw driven upward into the end grain of a wooden post loses $55\%$ of its holding capacity under Eurocode 5. Repeated magnetic latching impacts strip the end-grain fibers.
- **Remediation**: CNC pocket a **$4\text{ mm}$ deep mortise** in base `B01` to capture the post foot in solid wood shear.

---

### 🔵 RISK-15: Plinth Drawer Stick-Slip Jamming
- **Affected Parts**: `B02`, `B03` (travel: $205.3\text{ mm}$, width: $149.3\text{ mm}$, aspect ratio: $1.38$).
- **Physical Mechanism**: High travel-to-width ratio ($> 1.0$) combined with bare birch-on-birch friction ($\mu \approx 0.38$) causes the drawer to jam when pulled off-center with one hand.
- **Remediation**: Add a central T-guide runner and apply beeswax or UHMWPE tape to runner interfaces.

---

## 4. Prioritized Action & Verification Plan

```
PHASE 1: FATAL HAZARD ELIMINATION (Before any child contact)
├── [ ] Remove all exposed/epoxied neodymium magnets (RISK-01)
├── [ ] Design anti-tip floor plate / wall strap (RISK-02)
├── [ ] Round roof apex into a smooth sphere; eliminate sharp spire (RISK-04)
└── [ ] Redesign partition gap from 8 mm to <= 3 mm or >= 15 mm (RISK-03)

PHASE 2: STRUCTURAL INTEGRITY & DURABILITY
├── [ ] Replace 4x4 mm floor seam strip with 6x25 mm plywood batten (RISK-09)
├── [ ] Add R2.0 mm dogbone fillets to all CNC pillar cutouts (RISK-11)
├── [ ] Upgrade E08 roof turn-buttons from 3 mm to 6 mm plywood (RISK-12)
└── [ ] Replace 12 mm wall hinge screws with 16 mm screws (RISK-10)

PHASE 3: FINISH, CHEMICAL & DETAIL UPGRADES
├── [ ] Remove fragile 3.6x3 mm window bars; rout solid frames (RISK-06)
├── [ ] Replace polymer clay figures with turned beech wood or silicone (RISK-07)
├── [ ] Recess door handles directly into door profiles (RISK-05)
└── [ ] Sand all CNC plywood edges to minimum R1.5 mm radius
```
