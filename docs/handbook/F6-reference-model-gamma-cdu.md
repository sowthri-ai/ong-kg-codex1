# F6 Reference model: Refinery Gamma CDU

A complete, fictional crude distillation unit modelled end to end, from L0 to L10, in both sectors. It is the worked example of every design rule in Parts B and C, and the acceptance template for loading a real site.

> Fictional refinery, synthetic engineering data. Values are plausible estimates for demonstration, not design data. Crude assays are indicative typical values.

## F6.1 Design basis

| Item | Value |
|---|---|
| Site | Refinery Gamma (fictional), 500 kbpd nameplate |
| CDU configuration | Two identical trains, A and B, 250 kbpd each; common facilities; crude tank farm |
| Crude slate (FY2026) | Arab Light 45%, Basrah Medium 35%, Murban 20% |
| Train sections | Crude charge · cold preheat · 2-stage electrostatic desalting · hot preheat · preflash · fired heater · atmospheric fractionation with 3 side strippers · 3 pumparounds · overhead · product rundown · chemical injection · naphtha stabiliser |
| Products (vol%) | LPG 1 · naphtha 20 · kerosene 12 · diesel 20 · AGO 7 · atmospheric residue 40 |
| Key operating points | Desalter 135 °C · CIT 272 °C (A) / 258 °C (B) · COT 365 °C · column top 128–130 °C, 1.0 barg |
| Heater | 150 MW design absorbed duty, 4 passes, 9Cr coils, TMT limit 620 °C (critical 650 °C) |
| Seal-plan rule | ≥ 260 °C → API 682 Plan 53B; naphtha/LPG → Plan 52; otherwise Plan 11 |

## F6.2 What's in the model

**Levels**

| Level | Asset spine | Count | Process spine | Count |
|---|---|---|---|---|
| L0–L1 | Oil & Gas › Downstream | 1 + 1 | shared | |
| L2 | Refining | 1 | Value streams | 2 |
| L3 | Refinery Gamma | 1 | Process groups | 5 |
| L4 | CDU-A, CDU-B, CDU-COM, TF-1 + 7 downstream placeholders | 11 | Processes | 7 |
| L5 | Sections (12 per train + 4 common) | 28 | Sub-processes | 7 |
| L6 | Equipment | 157 | Activities | 7 |
| L7 | Subunits | 605 | Tasks | 7 |
| L8 | Maintainable items | 1,337 | Decision points | 7 |
| L9 | Parts | 376 | Data objects | 7 |
| L10 | Instrument, lab and calculated tags | 950 | Data elements | 25 |

**Equipment by class**

| Class | Train A | Train B | Common / tank farm |
|---|---|---|---|
| Pumps | 31 | 31 | 6 |
| Shell-and-tube exchangers | 19 | 19 | — |
| Air coolers | 2 | 2 | — |
| Desalters | 2 | 2 | — |
| Drums / vessels | 3 | 3 | 1 |
| Atmospheric column + stabiliser | 2 | 2 | — |
| Side strippers | 3 | 3 | — |
| Fired heater | 1 | 1 | — |
| Piping circuits | 3 | 3 | — |
| Chemical injection packages | 5 | 5 | — |
| Storage tanks | — | — | 8 |

**Sector 2 information**

| Kind | Count |
|---|---|
| Facts | 3,293 (2,256 declared design/config · 880 measured · 111 calculated with lineage · 33 recorded · 13 indicative or assumption) |
| Integrity operating window limits | 50 |
| Events (Oct 2025 – Sep 2026) | 6 IOW exceedances, 5 failures, 6 work orders |
| Crude campaigns | 6 (3 grades × 2 trains) |

**Also modelled:** 25 dotted-branch groupings (8 corrosion loops, 6 pumparound circuits, 2 fleets, 3 utilities, 2 SIFs, 3 cost centres, the CDU complex), 9 application instances, 11 roles, the operating enterprise, 3 fictional pump makers and 4 models, 5 equations, 5 damage mechanisms, and plots and areas.

## F6.3 How each template decomposes (L6 → L10)

| Class | L7 subunits | Example L8 / L9 | Typical L10 tags |
|---|---|---|---|
| Pump | Driver, pump unit, power transmission, lubrication, control & monitoring | Mechanical seal → seal faces, O-rings, springs | Flow, discharge pressure, bearing vibration ×2, bearing temperature, motor current, seal-pot pressure (Plan 52/53B only) |
| Shell-and-tube exchanger | Shell, tube bundle, channel & heads | Tubes → tube-to-tubesheet joints | 4 temperatures, pressure drop, duty (calc), fouling resistance (calc) |
| Fired heater | Radiant, convection, burners, stack & draft, fuel gas | Pass 1–4 coils → return bends | Pass flow, COT and TMT ×4, CIT, O2, draft, stack temperature, fuel gas, absorbed duty and efficiency (calc) |
| Desalter | Vessel, electrical grid, mixing valve, internals, mud wash | Transformer, electrode grids | Temperature, pressure, interface level, grid kV and A, mix-valve dP, oil-in-brine, lab salt and BS&W |
| Atmospheric column | Shell & lining, internals, nozzles | Trays by section → tray valves | Top T/P, draw temperatures, flash-zone T/P, dP, level, stripping steam |
| Overhead receiver | Shell, internals, water boot | Boot | Levels, P, T, boot chloride (lab), pH, iron (lab) |
| Piping circuit | Piping, supports (+ injection points on the overhead line) | Straight runs, fittings | Corrosion probe, minimum wall thickness (TML), dew-point margin (calc, overhead) |

Templates live in `ogkg/cdu_templates.py`. Adding an equipment class means adding one template.

## F6.4 What the model shows (insights)

| Insight | Result |
|---|---|
| Train B preheat fouling energy penalty | Train B runs 14 °C colder into the heater (CIT 258 vs 272 °C) and uses 7.3 MMBtu more per kbbl: ≈ $3.8M/yr fuel and ≈ 34 kt CO2/yr. Fouled: E-209 to E-212 |
| Train A overhead corrosion exposure | 4 IOW exceedances and 1 corrosion failure (E-120A tubes) vs none on Train B; corrosion rate 0.18 vs 0.08 mm/y; E-120B shares the failed cooler's design and service |
| Model completeness scorecard | 100% of equipment decomposed, with design data and complete tags; trains symmetric |

Fuel price is a low-confidence planning assumption; the CO2 figure uses a natural-gas factor as an indicative proxy.

## F6.5 Files

| File | Sector | Purpose |
|---|---|---|
| `ontology/ext/ogkg-cdu.ttl` | 1a | CDU classes, section types, tag attributes |
| `data/cdu-gamma/structure.ttl` | 1b | Entities, hierarchy, cross-links, groupings, reference links (v0.2 vocabulary) |
| `data/cdu-gamma/information.ttl` | 2 | Facts, events, campaigns, cached design values |
| `data/cdu-gamma/kg.json` | both | Prototype engine / MCP / explorer format |
| `data/cdu-gamma/equipment_register.csv` | — | Equipment list with design data, for engineering review |
| `data/cdu-gamma/tag_register.csv` | — | Tag list with units, attachment and latest values |
| `explorer/gamma_cdu_kg.html` | — | Interactive explorer for this model |

## F6.6 Checks

| Check | Result |
|---|---|
| Every spine node has one parent, levels decrease, all reach L0 | Pass |
| Every equipment item decomposed to maintainable items, ≥ 3 design facts, ≥ 1 tag | Pass (157 / 157) |
| Every tag has a unit, a latest value and a source; calculated values cite their inputs | Pass (950 / 950) |
| Train B mirrors Train A item for item | Pass |
| Turtle exports parse and pass the SHACL-equivalent checks (`ogkg/shacl_lite.py`) | Pass: 0 violations on ≈ 55k triples |
| Checks catch a deliberately removed seal plan | Pass |

`ogkg/shacl_lite.py` mirrors `ontology/ogkg-shapes.ttl` shape by shape. Running pySHACL on the shapes file itself is still backlog item E1-P1-01.

## F6.7 Rebuild and use

```bash
python -m ogkg.cdu_gamma           # data/cdu-gamma/kg.json + registers
python -m ogkg.ttl_v02             # structure.ttl + information.ttl
python -m ogkg.shacl_lite data/cdu-gamma/structure.ttl data/cdu-gamma/information.ttl
python -m ogkg.cdu_explorer        # explorer/gamma_cdu_kg.html
OGKG_DATASET=gamma python -m ogkg.mcp_server    # serve this model to any MCP client
```
