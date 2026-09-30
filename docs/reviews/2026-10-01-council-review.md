# Council review of OGKG v0.4.0 (Refinery Gamma)

**Date:** 2026-10-01 · **Scope:** repository at tag `v0.4.0` · **Method:** six independent reviewers, each with a fixed seat, read the code and data and ran checks in Python. The chair re-verified the high-severity findings, merged overlaps into 33 unique issues, and placed each issue in exactly one cell of the issue tree (§4).

> The reviewers are AI agents playing expert seats. This review does not replace a review by human process, integrity and instrumentation SMEs before any client use.

## 1. Conclusion

Gamma's **skeleton is sound, but its content is not yet trustworthy enough to be "the fact source every AI uses"**. By layer:

| Layer | Verdict | Wrong | Missing |
|---|---|---|---|
| 1 Ontology & semantics | Class model sound; facts sit outside it | 2 | 4 |
| 2 Structure | Hierarchy clean; some links wrong; networks and asset classes incomplete | 2 | 3 |
| 3 Information | **Weakest layer**: constructed values labelled measured, SME-visible errors, no time dimension | 5 | 4 |
| 4 Access | Citation plumbing works; tools fail silently and don't scale to screening questions | 4 | 3 |
| 5 Platform & governance | Deterministic build; identity, security, scale and validation not production-grade | 1 | 3 |
| 6 Proposition | Claims run ahead of evidence; value case has no baseline | 1 | 1 |
| **Total** | | **15** | **18** |

**Recommendation:** fix the 11 "Now" issues before Gamma is shown outside the team; most are small effort. Then build the 14 "Next" foundations. Then build one of the two decision tracks ("Then"), whichever the pilot calls for.

## 2. What each seat concluded

| Seat | Verdict | Findings |
|---|---|---|
| Process engineer | Deep-unit equipment is credible. The refinery process layer isn't fit as a fact source: the balances close by construction, the FCC and MTBE break mass balance, and there is no mass basis, product quality, or sour-water or amine network. | 12 (P-1 … P-12) |
| Reliability & integrity | Hierarchy sound, CDU overhead story coherent. It can't support inspection or turnaround decisions: there is no RBI, PSVs or SIF data, some mechanism assignments are wrong, and ISO 14224 coding is wrong. | 12 (R-1 … R-12) |
| Ontology architect | 0 domain violations and a clean hierarchy. Facts sit outside the ontology: 117 of 126 predicates are strings, units are free text, and there is no temporal model. | 12 (O-1 … O-12) |
| AI consumer | **11 of 22** realistic questions fully answerable, 8 partial, 3 not at all. Screening questions cost 25–49 tool calls, search is substring-only, and several tools fail silently. | 10 (A-1 … A-10) |
| Planning & economics | The insight arithmetic is correct, but only 19 of 5,656 facts are economic. Site GRM is applied to conversion-unit barrels. 70% of modelled value rests on one low-confidence assumption. | 11 (E-1 … E-11) |
| Skeptic (client CDO) | A well-documented design and a synthetic generator. The handbook describes controls (entitlements, audit, pre-commit scans, crosswalk, portability) that the code doesn't implement. | 12 (S-1 … S-12) |

The seats are sources, not the structure of this review. Their 69 findings overlap, so §4 regroups them.

## 3. Findings the chair re-verified

| Check | Result | Issue |
|---|---|---|
| SMR hydrogen meter, SRU sulfur production and unit feed meters are set from the balance they close, but labelled measured / PI historian | Confirmed (`ogkg/refinery_gamma.py`, `extend()`) | IN-W1 |
| Calculated facts rated above their weakest direct input | Confirmed: 56 of 270 (the AI seat counted 76 transitively) | IN-W2 |
| Calculated facts with empty lineage | Confirmed: 7 (site GRM; CDU salt removal, chloride average, availability) | IN-W2 |
| FCC liquid products 67.2 kbd from 74.0 kbd of feed; MTBE 4.5 kbd in, 6.5 kbd out, no methanol | Confirmed (`STREAMS`) | IN-W3 |
| ISO 14224 Table B.2 codes: wear 2.4, erosion 2.3, fatigue 2.6 | Confirmed: the data uses "1.x" / "2.x" | IN-W4 |
| HTHA applied to 347SS items (H-401 coil, E-401, PC-402) via loop membership | Confirmed | ST-W1 |
| FLT-HOT has 16 members; 28 pumps meet its definition | Confirmed (grouping built before the conversion units) | ST-W2 |
| `rollup_events(event_class="WorkOrder")`, `traverse(relation="susceptible_to")` and unknown IDs return empty, not an error | Confirmed | AC-W1 |
| `search_entities("D-501B bulge")` returns 0; "HTHA" matches "naphtha" | Confirmed | AC-M2 |
| `partOf` is `owl:TransitiveProperty` while `SpineNodeShape` sets `sh:maxCount 1` | Confirmed: fails under OWL RL inference | ON-W1 |

No high-severity finding was rejected on re-check.

## 4. Issue tree

### 4.1 How issues are classified

Each issue is placed by two questions:

1. **Layer: where does the fix live?** The six layers cover the whole repository and do not overlap:

   | # | Layer | Scope |
   |---|---|---|
   | 1 | Ontology & semantics (Sector 1a) | `ontology/*.ttl`: classes, properties, axioms, vocabularies |
   | 2 | Structure (Sector 1b) | Entities, hierarchy, links and groupings in the reference model |
   | 3 | Information (Sector 2) | Fact values and fact metadata |
   | 4 | Access | MCP tools, insights as tools, explorer |
   | 5 | Platform & governance | Identity, security, runtime store, validation, tests |
   | 6 | Proposition | README and handbook claims, value case, pilot offer |

2. **Type: is the content present but incorrect or overstated (Wrong), or absent (Missing)?**

A finding that touches several layers goes to the layer where the first change must be made. Priority (Now / Next / Then) is an attribute of each issue, not a separate list.

### 4.2 Issues by layer

**1 · Ontology & semantics**

| ID | Type | Issue | Findings | Effort | Priority |
|---|---|---|---|---|---|
| ON-W1 | Wrong | Axioms conflict or are too weak: transitive `partOf` against the one-parent shape; no disjointness; `causedBy` domain misclassifies problem patterns | O-6, O-10 | S | Next |
| ON-W2 | Wrong | Standards alignment is nominal (string literals); functional location conflated with physical asset | O-9 | M | Then |
| ON-M1 | Missing | Fact predicates, values and units are not defined in the ontology (string predicates, free-text units, concepts stored as strings) | O-1, O-2, O-11 | M | Next |
| ON-M2 | Missing | Provenance vocabulary incomplete: shallow PROV-O mapping, free-text source systems, edge provenance dropped | O-5 | S–M | Next |
| ON-M3 | Missing | DNA inheritance is neither computable nor materialised | O-8 | L | Then |
| ON-M4 | Missing | No version IRIs or imports | O-12 | S | Next |

**2 · Structure**

| ID | Type | Issue | Findings | Effort | Priority |
|---|---|---|---|---|---|
| ST-W1 | Wrong | Damage-mechanism links wrong: HTHA on austenitic steel, generic sulfidation in H2 service, clean wash water tagged NH4HS, whole columns tagged HCl | R-2 | M | Now |
| ST-W2 | Wrong | Rule-based groupings built before all equipment exists (FLT-HOT has 16 of 28 members) | A-3 | S | Now |
| ST-M1 | Missing | Process networks incomplete: sour water and rich amine by unit; steam, fuel gas, power and flare networks | P-6, P-11 | M | Then |
| ST-M2 | Missing | Integrity-critical asset classes absent: relief devices, SIF final elements, instruments, control valves, electrical; tanks without API 653 data | R-5, R-12 | M–L | Then |
| ST-M3 | Missing | Mechanism and loop coverage gaps: 115 of 261 items with no mechanism; no loop on the DCU overhead or FCC gas plant; wet H2S, CUI, carbonate SCC, caustic SCC, temper embrittlement | R-3 | M | Then |

**3 · Information**

| ID | Type | Issue | Findings | Effort | Priority |
|---|---|---|---|---|---|
| IN-W1 | Wrong | Constructed values labelled measured: balances and feed meters close by construction | P-1, E-7 | S–M | Now |
| IN-W2 | Wrong | Fact metadata overstates certainty: confidence not propagated, calculated facts without lineage, stale snapshots cited as current | A-2, S-7 | S–M | Now |
| IN-W3 | Wrong | Process values and balances wrong: FCC volume loss, MTBE mass creation, hydrogen chemical-only, sulfur inputs and fates, no mass basis, coke drum fill, E-401 temperature | P-2, P-3, P-4, P-5, P-8, P-9, P-12, E-6 | S–M | Now |
| IN-W4 | Wrong | Asset, instrument and reliability data wrong or implausible: ISO 14224 codes, idle-pump readings, missing alert limits, seal-plan rule, event realism, design data, TEMA types, tag numbering | R-4, R-7, R-8, R-9, R-10, R-11, S-12 | S–M | Now |
| IN-W5 | Wrong | Valuations on wrong or mixed bases: site GRM on unit barrels, reformer spread basis, incompatible insight value bases | E-2, E-3, E-9 | S–M | Now |
| IN-M1 | Missing | Commercial and planning data: prices, opex, carbon, product specs and quality, crude assay cut yields, LP backbone, turnaround and catalyst economics | E-1, E-4, E-5, E-8, E-11, P-7 | M–L | Then |
| IN-M2 | Missing | Process performance data: unit KPIs (delta coke, ppH2, deactivation rate, RONC, …) and crude-dependent yields | P-10 | M–L | Then |
| IN-M3 | Missing | Integrity data: RBI and inspection records, turnaround scope, missing IOWs and API 584 levels | R-1, R-6 | L | Then |
| IN-M4 | Missing | No time dimension: fact history and validity, MOC and serial changes, fact correction | O-3, A-4, S-6 | L | Next |

**4 · Access**

| ID | Type | Issue | Findings | Effort | Priority |
|---|---|---|---|---|---|
| AC-W1 | Wrong | Tools fail silently on unknown IDs, relation case or event class | A-6, S-2 | S | Now |
| AC-W2 | Wrong | Insight outputs carry no fact ID; missing values shown as $0 | A-7 | M | Now |
| AC-W3 | Wrong | `find_path` returns meaningless routes through the site hub | A-9 | S | Next |
| AC-W4 | Wrong | Explorer fallback dumps every fact into the prompt; silent truncation | A-10 | S | Now |
| AC-M1 | Missing | No attribute query or bulk read (screening costs 25–49 calls) | A-1 | M | Next |
| AC-M2 | Missing | Search has no tokenisation, ranking or aliases | A-5 | M | Next |
| AC-M3 | Missing | No context packs; bloated payloads; no pagination | A-8 | M | Next |

**5 · Platform & governance**

| ID | Type | Issue | Findings | Effort | Priority |
|---|---|---|---|---|---|
| PL-W1 | Wrong | Validation and tests weaker than needed: `shacl_lite` covers 8 of 13 shapes and skips ranges; tests mostly recompute the builder's own formulas | O-7, S-11 | M | Next |
| PL-M1 | Missing | Identity and onboarding: counter-based fact IDs, cross-site collisions, no crosswalk or connectors, real tag formats rejected | O-4, S-3, S-4 | L | Next |
| PL-M2 | Missing | Security and audit: no caller identity, sensitivity filter or call log | S-1 | M | Next |
| PL-M3 | Missing | Runtime store and scale: in-memory design will not reach 10⁶–10⁷ facts | S-10 | M | Next |

**6 · Proposition**

| ID | Type | Issue | Findings | Effort | Priority |
|---|---|---|---|---|---|
| PR-W1 | Wrong | Claims exceed evidence: seeded patterns presented as discovered; SHACL "mirrors shape by shape"; portability and controls described as built | S-5, S-8, S-9 | S | Now |
| PR-M1 | Missing | Value case has no baseline, no $/bbl target, and no pilot option that shows commercial levers | E-10 | S–M | Next |

### 4.3 Priority view

Every issue appears once.

| Priority | Definition | Issues |
|---|---|---|
| **Now** (11) | Would damage trust in any demo; fix before Gamma leaves the team | ST-W1, ST-W2, IN-W1, IN-W2, IN-W3, IN-W4, IN-W5, AC-W1, AC-W2, AC-W4, PR-W1 |
| **Next** (14) | Foundations every use case needs (Phase 1) | ON-W1, ON-M1, ON-M2, ON-M4, IN-M4, AC-W3, AC-M1, AC-M2, AC-M3, PL-W1, PL-M1, PL-M2, PL-M3, PR-M1 |
| **Then** (8) | Decision layers, built by the pilot track chosen | *Economics track:* IN-M1, IN-M2, ST-M1 · *Integrity track:* IN-M3, ST-M2, ST-M3 · *Either track:* ON-W2, ON-M3 |

### 4.4 MECE check

- **Mutually exclusive:** each of the 69 findings maps to exactly one issue (appendix), and each issue sits in one layer, one type and one priority.
- **Collectively exhaustive:** the six layers cover every folder in the repository. Wrong and Missing together cover any defect. All 69 findings are mapped, so none is dropped.

## 5. Decisions required

| Decision | Options | Recommendation | Owner |
|---|---|---|---|
| Show Gamma to the ED or clients before the "Now" issues are fixed? | Show now with caveats / hold | **Hold.** An SME would find IN-W1 and IN-W3 quickly, and that damages trust in the whole accelerator. | Sowthri |
| Which "Then" track to build first | Economics / Integrity | Tie it to the Phase 2 pilot. The current pilot (CDU overhead + hot pumps) needs **Integrity**; a planning-led client needs **Economics**. Offer both as pilot options in E4 (PR-M1). | Sowthri with the ED |
| Human SME review | Process, integrity, instrumentation | Book after the "Now" issues are fixed; use §4 as the agenda. | Sowthri |

## 6. What to keep

| Layer | Keep |
|---|---|
| Ontology & semantics | Facts as nodes with mandatory provenance fields and SKOS confidence and method terms; hypotheses kept separate from facts |
| Structure | Clean hierarchy: one parent per node, levels always decrease, 0 domain violations on 93k triples; failures anchored at L8 |
| Information | Credible deep-unit envelopes (ROT, regenerator, HCU pressure and WABT, coker COT and TMT against IOWs); assumptions labelled low confidence |
| Access | `explain_fact` traces a derived number down to PI tags; insights run in about 20 ms with evidence lists |
| Platform & governance | Deterministic build; v0.3 fact IDs preserved in v0.4 (by build order, not by design, see PL-M1); concrete governance design |
| Proposition | Hydrogen headroom and sulfur ceiling are the right planner questions; insight caveats are honest |

## Appendix: findings mapped to issues

Severity: C critical · H high · M medium · L low.

| Finding | Sev | Summary | Issue |
|---|---|---|---|
| P-1 | C | Balances close by construction; closing values labelled measured | IN-W1 |
| P-2 | H | Hydrogen counts chemical consumption only; at 85% efficiency make-up exceeds supply | IN-W3 |
| P-3 | H | FCC shows a 9.2 vol% liquid loss; implied coke 16 wt% and dry gas 7.4 wt% | IN-W3 |
| P-4 | H | No mass basis; 4.5% of site mass unaccounted; light ends not routed | IN-W3 |
| P-5 | H | Sulfur in leaves out imported VGO; residual-product sulfur too low | IN-W3 |
| P-6 | H | Sour water and amine network almost empty; no NH3 | ST-M1 |
| P-7 | M | No product quality; pool RON about 87.6; no FCC naphtha post-treater | IN-M1 |
| P-8 | M | MTBE creates mass (4.5 → 6.5 kbd), no methanol | IN-W3 |
| P-9 | M | Coke drums need an 88% fill for 4,300 t/d | IN-W3 |
| P-10 | M | Missing process KPIs; CDU yields fixed | IN-M2 |
| P-11 | M | Utility units hold capacity only; no steam, fuel gas or power balance | ST-M1 |
| P-12 | L | E-401 hot inlet (420 °C) hotter than R-402 outlet (412 °C) | IN-W3 |
| R-1 | C | No RBI or inspection layer; no Turnaround or ScopeItem instances | IN-M3 |
| R-2 | H | HTHA on 347SS; generic sulfidation in H2 service; wash water tagged NH4HS; whole columns tagged HCl | ST-W1 |
| R-3 | H | 115 of 261 items without mechanism; missing loops and mechanisms | ST-M3 |
| R-4 | H | ISO 14224 codes wrong; no cause, detection, severity or TTR | IN-W4 |
| R-5 | H | No relief devices; SIFs without SIL, proof test or final element | ST-M2 |
| R-6 | H | Missing IOWs; 32 of 101 limits have no API 584 level; no response times | IN-M3 |
| R-7 | M | Idle pumps show vibration; bad actor is the standby; missing alert limits | IN-W4 |
| R-8 | M | No MTBF, spares or criticality; seal-plan rule misfires; motor inside pump boundary | IN-W4 |
| R-9 | M | Too few failures; critical exceedance without response; causal links unused | IN-W4 |
| R-10 | M | Nominal wall = wall + 1.8 everywhere; process temperature stored as metal design temperature | IN-W4 |
| R-11 | L | TEMA-type rule wrong for slurry, residue and high-pressure services | IN-W4 |
| R-12 | L | No instruments, control valves or electrical items as assets; no tank API 653 data | ST-M2 |
| O-1 | C | 117 of 126 fact predicates are undefined strings | ON-M1 |
| O-2 | C | QUDT unused; 53 free-text unit labels | ON-M1 |
| O-3 | H | No temporal model; no named graphs | IN-M4 |
| O-4 | H | Counter-based fact IDs; site-local reference nodes; no crosswalk | PL-M1 |
| O-5 | H | Shallow PROV-O; edge provenance dropped on export | ON-M2 |
| O-6 | H | Transitive `partOf` conflicts with `maxCount 1` | ON-W1 |
| O-7 | H | `shacl_lite` covers 8 of 13 shapes; misses a range violation | PL-W1 |
| O-8 | M | DNA inheritance not computable | ON-M3 |
| O-9 | M | Standards alignment nominal; functional location conflated | ON-W2 |
| O-10 | M | No disjointness axioms; `causedBy` domain | ON-W1 |
| O-11 | L | Cached values duplicated; seal plan held as string | ON-M1 |
| O-12 | L | No version IRIs or imports | ON-M4 |
| A-1 | H | No attribute filter or bulk read | AC-M1 |
| A-2 | H | Confidence not propagated from inputs | IN-W2 |
| A-3 | H | Fleet membership incomplete (FLT-HOT) | ST-W2 |
| A-4 | H | No history, so trend questions fail | IN-M4 |
| A-5 | M | Substring search, no ranking or aliases | AC-M2 |
| A-6 | M | Tools fail silently | AC-W1 |
| A-7 | M | Insight numbers without fact ID; missing shown as $0 | AC-W2 |
| A-8 | M | No `get_context`; bloated payloads; no pagination | AC-M3 |
| A-9 | M | `find_path` routes through the site hub | AC-W3 |
| A-10 | L | Explorer fallback dumps all facts; silent truncation | AC-W4 |
| E-1 | C | No economic layer | IN-M1 |
| E-2 | H | Site GRM applied to conversion-unit barrels | IN-W5 |
| E-3 | H | Reformer value rests on a low-confidence spread; no basis, capex or octane check | IN-W5 |
| E-4 | H | No product specs, blending or giveaway | IN-M1 |
| E-5 | H | Crude assays too shallow; crude swap unvalued | IN-M1 |
| E-6 | M | 8.2% site liquid loss | IN-W3 |
| E-7 | M | Sulfur closure by construction; hard-coded two-thirds Claus capacity | IN-W1 |
| E-8 | M | No carbon price or site CO2 | IN-M1 |
| E-9 | M | Insight values on incompatible bases | IN-W5 |
| E-10 | H | Value case lacks baseline and $/bbl target | PR-M1 |
| E-11 | M | No LP backbone, plan vs actual, turnaround or catalyst economics | IN-M1 |
| S-1 | C | MCP has no auth, sensitivity filter or audit log | PL-M2 |
| S-2 | C | Unknown IDs return empty results that look like answers | AC-W1 |
| S-3 | H | No onboarding path; IDs reject real tag formats | PL-M1 |
| S-4 | H | IDs collide across sites | PL-M1 |
| S-5 | H | Insight patterns seeded but presented as discovered | PR-W1 |
| S-6 | H | No MOC or serial history; no fact-correction process | IN-M4 |
| S-7 | H | Stale snapshots cited as current, high confidence | IN-W2 |
| S-8 | M | SHACL coverage overstated in the handbook | PR-W1 |
| S-9 | M | Portability not demonstrated | PR-W1 |
| S-10 | M | In-memory design will not scale | PL-M3 |
| S-11 | M | Tests largely tautological; 3 negative tests | PL-W1 |
| S-12 | M | Tag numbering not ISA-style; 96% of facts rated high; pump model named "HX-300" | IN-W4 |
