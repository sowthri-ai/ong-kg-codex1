# F6 Reference model: Refinery Gamma

A fictional 500 kbpd refinery with a Nelson complexity of about 15, modelled in both sectors. It is the worked example of every design rule in Parts B and C, and the acceptance template for loading a real site.

Depth follows the build-for-a-decision rule ([ADR-0011](../adr/decision-log.md#adr-0011-model-depth-follows-the-decision)):

- **Full depth (L0–L10):** the two-train CDU, the FCC, the hydrocracker and the delayed coker. Every equipment item, subunit, part and tag is modelled.
- **Skeleton (L4–L5):** every other unit. Each has its sections, capacity, feed rate, utilisation, Nelson factor and network role.

> Fictional refinery, synthetic engineering data. Values are plausible estimates for demonstration, not design data. Crude assays are indicative typical values. Nelson factors are the public 1998 values.

## F6.1 Design basis

| Item | Value |
|---|---|
| Site | Refinery Gamma (fictional), 500 kbpd crude; FY2026 run 484 kbpd |
| Crude slate (FY2026) | Arab Light 45%, Basrah Medium 35%, Murban 20%; 2.03 wt% S average |
| Nelson complexity | **15.0** (1998 factors); built from 17 unit capacities in the graph |
| Deep units | CDU trains A/B (2 × 250 kbpd), FCC-1 (90), HCU-1 (95), DCU-1 (100, 2 heaters, 4 drums) |
| Hydrogen | Reformer 99 MMSCFD + SMR 200 MMSCFD (2 × 100) against 283 MMSCFD chemical demand |
| Sulfur | SRU 3 × 400 t/d Claus + tail-gas treating; 1,090 t/d recovered |
| Seal-plan rule | ≥ 260 °C → API 682 Plan 53B; naphtha/LPG → Plan 52; otherwise Plan 11 |

## F6.2 Units (L4)

| Unit | Capacity | FY2026 feed | Utilisation | Nelson factor | Depth |
|---|---|---|---|---|---|
| CDU-A / CDU-B | 250 / 250 kbpd | 246 / 238 kbpd | 98.4 / 95.2% | 1.0 | Full |
| VDU-1 Vacuum distillation | 220 kbpd | 193.6 | 88.0% | 2.0 | Skeleton |
| DCU-1 Delayed coker | 100 kbpd | 84.8 | 84.8% | 2.75 | **Full** |
| VGOHT-1 VGO hydrotreater | 90 kbpd | 74.0 | 82.2% | 3.0 | Skeleton |
| FCC-1 Fluid catalytic cracker | 90 kbpd | 74.0 | 82.2% | 6.0 | **Full** |
| HCU-1 Hydrocracker | 95 kbpd | 85.9 (incl. 30 imported VGO) | 90.4% | 6.0 | **Full** |
| DHT-1 / KHT-1 / NHT-1 Hydrotreaters | 140 / 65 / 115 kbpd | 124.9 / 58.1 / 109.5 | 89.2 / 89.4 / 95.2% | 3.0 | Skeleton |
| CCR-1 Continuous reformer | 90 kbpd | 90.0 | **100%** | 5.0 | Skeleton |
| ISOM-1 / ARO-1 | 45 / 60 kbpd | 35.0 / 48.0 | 77.8 / 80.0% | 15.0 | Skeleton |
| ALKY-1 / MTBE-1 | 25 / 5 kbpd | 17.9 / 4.5 | 71.6 / 90.0% | 10.0 | Skeleton |
| LUBE-1 / ASPH-1 | 27 / 15 kbpd | 22.0 / 12.0 | 81.5 / 80.0% | 60.0 / 1.5 | Skeleton |
| HMU-1 Hydrogen plant | 200 MMSCFD | 184.1 produced | 92.0% | — | Skeleton |
| SRU-1, ARU-1, SWS-1 | 1,200 t/d; 900 m3/h; 250 m3/h | 1,090 t/d S | 90.8% (SRU) | — | Skeleton |
| LPG-1, GBL-1, DBL-1 | 20 / 180 / 260 kbpd | 13.5 / 148.4 / 244.0 | 67.5 / 82.4 / 93.8% | — | Skeleton |
| TF-1, TF-2, TF-3, MT-1 | Tankage 3,600 / 2,400 / 1,200 kbbl; 4 berths + SPM | — | — | — | TF-1 full, rest skeleton |
| Utilities (steam & power, cooling water, fuel gas, flare, nitrogen, water, hydrogen header) | per unit | — | — | — | Skeleton |

Every feed rate is a calculated fact whose lineage lists the stream-rate facts feeding it. Every utilisation fact lists the feed rate and design capacity it comes from.

## F6.3 Networks and balances

| Network | What is in the graph | Closure |
|---|---|---|
| Liquid streams | 76 streams (`PRODUCES` / `FEEDS`) with FY2026 rates; CDU product streams read from the trains' product meters | Each unit's feed = sum of its inflows; gasoline and distillate pools = their product exports |
| Hydrogen | Consumption rate (scf/bbl) × feed for 7 consumers; reformer yield × feed; SMR product meter; header streams | SMR + reformer = demand (283.1 MMSCFD); headroom 15.9 MMSCFD |
| Sulfur | Crude S from grade assays × slate shares; crude mass from throughput × density; 4 measured fates; SRU production | 1,359 t/d in = 1,090 recovered + 269 to coke, residuals, products and emissions (closure 0) |
| Complexity | Nelson factor and contribution per unit; site NCI with lineage to all 17 contributions | Σ contributions = NCI |

## F6.4 What's in the model

**Levels**

| Level | Asset spine | Count | Process spine | Count |
|---|---|---|---|---|
| L0–L1 | Oil & Gas › Downstream | 1 + 1 | shared | |
| L2 | Refining | 1 | Value streams | 2 |
| L3 | Refinery Gamma | 1 | Process groups | 8 |
| L4 | Plant units (all real, no placeholders) | 36 | Processes | 14 |
| L5 | Sections | 131 | Sub-processes | 14 |
| L6 | Equipment | 261 | Activities | 14 |
| L7 | Subunits | 976 | Tasks | 14 |
| L8 | Maintainable items | 2,158 | Decision points | 14 |
| L9 | Parts | 584 | Data objects | 14 |
| L10 | Instrument, lab, calculated and unit-level tags | 1,624 | Data elements | 48 |

**Equipment by class**

| Class | CDU A | CDU B | CDU common / TF-1 | FCC-1 | HCU-1 | DCU-1 |
|---|---|---|---|---|---|---|
| Pumps | 31 | 31 | 6 | 14 | 10 | 10 |
| Shell-and-tube exchangers | 19 | 19 | — | 6 | 2 | 2 |
| Air coolers | 2 | 2 | — | 2 | 4 (REAC) | 2 |
| Fired heaters | 1 | 1 | — | 1 | 1 | 2 |
| Columns / side strippers | 2 / 3 | 2 / 3 | — | 4 | 2 | 2 |
| Drums / vessels | 3 | 3 | 1 | 3 | 4 | 2 |
| Reactors | — | — | — | Riser/reactor, regenerator | 2 fixed-bed (3 + 4 beds) | 4 coke drums |
| Compressors / expander | — | — | — | 2 / 1 | 3 (1 centrifugal, 2 recip) | 1 |
| Other | 2 desalters, 5 chemical packages, 3 piping circuits | same | 8 tanks | 2 slide valves, CO boiler, 2 chemical, 2 piping | 2 chemical, 2 piping | Decoking, crusher, 1 chemical, 2 piping |

**Sector 2 information**

| Kind | Count |
|---|---|
| Facts | 5,656 (3,729 declared · 1,572 measured · 270 calculated with lineage · 53 recorded · 27 indicative · 5 assumption) |
| Integrity operating window limits | 101 |
| Events (Oct 2025 – Sep 2026) | 11 IOW exceedances, 9 failures, 11 work orders |
| Crude campaigns | 6 (3 grades × 2 trains) |

**Also modelled:** 40 dotted-branch groupings (13 corrosion loops including REAC NH4HS and HTHA, 6 pumparound circuits, 3 fleets, 3 utilities, 5 SIFs, 6 cost centres, the CDU complex, hydrogen and sulfur networks, gasoline pool), 13 application instances, 13 roles, 5 fictional equipment makers and 11 models, 9 equations, 10 damage mechanisms, 13 plots.

## F6.5 How each template decomposes (L6 → L10)

| Class | L7 subunits | Example L8 / L9 | Typical L10 tags |
|---|---|---|---|
| Pump | Driver, pump unit, power transmission, lubrication, control & monitoring | Mechanical seal → seal faces, O-rings, springs | Flow, discharge pressure, bearing vibration ×2, bearing temperature, motor current, seal-pot pressure (Plan 52/53B only) |
| Shell-and-tube exchanger | Shell, tube bundle, channel & heads | Tubes → tube-to-tubesheet joints | 4 temperatures, pressure drop, duty (calc), fouling resistance (calc) |
| Fired heater | Radiant, convection, burners, stack & draft, fuel gas | Pass 1–4 coils → return bends | Pass flow, COT and TMT ×4, CIT, O2, draft, stack temperature, fuel gas, absorbed duty and efficiency (calc) |
| Fixed-bed reactor | Shell, internals | Catalyst beds → support grids; quench decks | Bed inlet/outlet temperatures, quench H2, pressure, dP, skin temperature, WABT (calc) |
| FCC reactor / regenerator | Riser, reactor vessel, stripper / regenerator vessel, standpipes | Feed nozzles → tips; cyclones → diplegs | ROT, feed, steam, cat/oil (calc) / bed and dilute temperatures, O2, CO, afterburn and catalyst losses (calc) |
| Centrifugal / reciprocating compressor | Driver, compressor, lube & seal oil, anti-surge / frame, cylinders, capacity control | Dry gas seals → seal rings; valves → plates | Pressures, temperature, flow, speed, vibration, axial displacement, surge margin (calc) / stage pressures and temperatures, valve temperature, rod load (calc) |
| Coke drum | Shell, unheading devices, switch valves | Shell courses, skirt weld | Overhead temperature, pressure, skin temperatures ×3, level, cycle time and cumulative cycles (calc) |
| Desalter, column, drums, piping, chemical packages, tanks, expander, boiler, slide valve, decoking, crusher | See `ogkg/cdu_templates.py` | | |

Templates live in `ogkg/cdu_templates.py` (28 classes). Adding an equipment class means adding one template.

## F6.6 What the model shows (insights)

| Insight | Result |
|---|---|
| Hydrogen headroom and reformer-outage exposure | Headroom 15.9 MMSCFD (5.3%) with the SMR at 92%. A reformer outage leaves the network 83 MMSCFD short, about 46 kbpd of hydrocracker feed, ≈ $342k of margin per day |
| Crude sulfur ceiling set by the SRU | SRU at 90.8%; ceiling ≈ 2.23 wt% S (Basrah Medium could rise from 35% to ≈ 45%). With one Claus train out the ceiling falls to ≈ 1.49 wt%, below today's slate |
| Conversion-unit losses and the signals that came first | 4 failures cost ≈ $8.8M (repairs + lost margin), led by the D-501B drum bulge (≈ $4.8M). The E-410C REAC tube leak followed a REAC wash-water IOW shortfall in the same corrosion loop 26 days earlier |
| Reformer bottleneck | Reformer at 100%; 10.3 kbpd heavy naphtha bypasses to gasoline, ≈ $30.1M/yr at an assumed $8/bbl spread, plus 11.3 MMSCFD of hydrogen forgone |
| Nelson complexity rebuilt from the graph | NCI 15.0; lubes, aromatics and isomerisation give 42% of it from 132 kbpd of capacity |
| Train B preheat fouling energy penalty | CIT 258 vs 272 °C; 7.3 MMBtu/kbbl more; ≈ $3.8M/yr fuel and ≈ 34 kt CO2/yr. Fouled: E-209 to E-212 |
| Train A overhead corrosion exposure | 4 IOW exceedances and 1 corrosion failure vs none on Train B; corrosion rate 0.18 vs 0.08 mm/y |
| Model completeness scorecard | 100% of 261 equipment items decomposed, with design data and complete tags; CDU trains symmetric |

Low-confidence assumptions are flagged on each insight: fuel price, upgrade spread, and site GRM used as a proxy for unit margin.

## F6.7 Files

| File | Sector | Purpose |
|---|---|---|
| `ontology/ext/ogkg-cdu.ttl` | 1a | Refinery extension: unit, section and equipment classes, tag attributes, `nelsonFactor`, `modelDepth` |
| `ogkg/refinery_units.py` | — | Units, streams, hydrogen and sulfur configuration; FCC, HCU and DCU equipment catalogues |
| `data/cdu-gamma/structure.ttl` | 1b | Entities, hierarchy, cross-links, groupings, reference links (v0.2 vocabulary) |
| `data/cdu-gamma/information.ttl` | 2 | Facts, events, campaigns, cached design values |
| `data/cdu-gamma/kg.json` | both | Prototype engine / MCP / explorer format |
| `data/cdu-gamma/equipment_register.csv` | — | Equipment list with unit and design data, for engineering review |
| `data/cdu-gamma/tag_register.csv` | — | Tag list with units, attachment and latest values |
| `explorer/refinery_gamma_kg.html` | — | Interactive explorer for this model |

## F6.8 Checks

| Check | Result |
|---|---|
| Every spine node has one parent, levels decrease, all reach L0 | Pass |
| Every equipment item decomposed to maintainable items, ≥ 3 design facts, ≥ 1 tag | Pass (261 / 261) |
| Every tag has a unit, a latest value and a source; calculated values cite their inputs | Pass (1,624 / 1,624) |
| CDU Train B mirrors Train A item for item | Pass |
| Every unit's feed equals its inflows; no unit above 100% | Pass |
| Hydrogen and sulfur balances close; NCI recomputes from capacities and factors | Pass |
| Turtle exports parse and pass the SHACL-equivalent checks (`ogkg/shacl_lite.py`) | Pass: 0 violations on ≈ 93k triples |
| Checks catch a deliberately removed seal plan | Pass |

`ogkg/shacl_lite.py` mirrors `ontology/ogkg-shapes.ttl` shape by shape. Running pySHACL on the shapes file itself is still backlog item E1-P1-01.

## F6.9 Rebuild and use

```bash
python -m ogkg.cdu_gamma           # data/cdu-gamma/kg.json + registers (whole refinery)
python -m ogkg.ttl_v02             # structure.ttl + information.ttl
python -m ogkg.shacl_lite data/cdu-gamma/structure.ttl data/cdu-gamma/information.ttl
python -m ogkg.cdu_explorer        # explorer/refinery_gamma_kg.html
OGKG_DATASET=gamma python -m ogkg.mcp_server    # serve this model to any MCP client
```

Module and folder names keep their v0.3 `cdu` names so existing scripts keep working.
