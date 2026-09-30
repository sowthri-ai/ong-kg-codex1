# Council review of OGKG v0.4.0 (Refinery Gamma)

**Date:** 2026-10-01 · **Scope:** repository at tag `v0.4.0` · **Method:** six independent reviewers, each with a fixed seat, read the code and data and ran checks in Python. The chair then re-verified the high-severity findings against the repository.

> The reviewers are AI agents playing expert seats. This review does not replace a review by human process, integrity and instrumentation SMEs before any client use.

## 1. Conclusion

The **structure is sound**: the L0–L10 hierarchy is clean, every fact carries provenance, the lineage chains work end to end, and the deep-unit operating envelopes are credible. The **information layer is not yet trustworthy enough to be "the fact source every AI uses"**, for three reasons:

1. **Some numbers are presented as measured when they were constructed.** The hydrogen and sulfur balances and the unit feed meters close because the closing value was back-calculated and then labelled a meter reading. Derived facts also claim higher confidence than their inputs.
2. **An SME would spot errors within minutes.**
   - The FCC loses 9% of its volume, when a real FCC gains volume.
   - The MTBE unit creates mass.
   - HTHA is assigned to stainless steel.
   - Idle pumps show vibration readings.
   - Some ISO 14224 codes are wrong.
3. **Whole layers that named decisions need are missing:**
   - economics and product quality (planner, executive);
   - inspection and RBI, relief devices, and SIF data (integrity, turnaround);
   - time history (any "trend" or "since when" question).

**Recommendation:** fix the trust issues and SME-visible errors first. This is mostly small effort, and it must happen before Gamma is shown to anyone outside the team. Then add a time model and stable identifiers, then the economics or integrity layer, whichever the pilot decision calls for.

## 2. What each seat concluded

| Seat | Verdict | Findings |
|---|---|---|
| Process engineer | Deep-unit equipment is credible. The refinery process layer isn't fit as a fact source: the balances close by construction, the FCC and MTBE break mass balance, and there is no mass basis, product quality, or sour-water or amine network. | 12 (P-1 … P-12) |
| Reliability & integrity | Hierarchy sound, CDU overhead story coherent. It can't support inspection or turnaround decisions: there is no RBI, PSVs or SIF data, some mechanism assignments are wrong, and ISO 14224 coding is wrong. | 12 (R-1 … R-12) |
| Ontology architect | 0 domain violations and a clean hierarchy. Facts sit outside the ontology: 117 of 126 predicates are strings, units are free text, and there is no temporal model. | 12 (O-1 … O-12) |
| AI consumer | **11 of 22** realistic questions fully answerable, 8 partial, 3 not at all. Screening questions cost 25–49 tool calls. Search is substring-only, and several tools fail silently. | 10 (A-1 … A-10) |
| Planning & economics | The insight arithmetic is correct, but only 19 of 5,656 facts are economic. Site GRM is applied to conversion-unit barrels. 70% of modelled value rests on one low-confidence assumption. | 11 (E-1 … E-11) |
| Skeptic (client CDO) | A well-documented design and a synthetic generator. The handbook describes controls (entitlements, audit, pre-commit scans, crosswalk, portability) that the code doesn't implement. | 12 (S-1 … S-12) |

## 3. Findings the chair re-verified

| Check | Result |
|---|---|
| The SMR hydrogen meter, SRU sulfur production and unit feed meters are set from the balance they are meant to close, but labelled measured / PI historian | Confirmed (`ogkg/refinery_gamma.py`, `extend()`) |
| FCC liquid products 67.2 kbd from 74.0 kbd of feed | Confirmed (`STREAMS`) |
| MTBE unit: 4.5 kbd in, 6.5 kbd out, no methanol stream | Confirmed |
| HTHA applied to 347SS items (H-401 coil, E-401, PC-402) through loop membership | Confirmed |
| Calculated facts rated above their weakest direct input | Confirmed: 56 of 270. The AI seat counted 76 using a transitive measure |
| Calculated facts with empty lineage | Confirmed: 7 (site GRM; the CDU salt removal, overhead chloride average and availability facts) |
| FLT-HOT has 16 members, but 28 pumps meet its definition | Confirmed (the grouping is built before the conversion units are added) |
| `rollup_events(event_class="WorkOrder")`, `traverse(relation="susceptible_to")` and unknown IDs all return empty instead of an error | Confirmed |
| `partOf` is `owl:TransitiveProperty` while `SpineNodeShape` sets `sh:maxCount 1` | Confirmed: it would fail under OWL RL inference |
| `search_entities("D-501B bulge")` returns 0; "HTHA" matches "naphtha" | Confirmed |
| ISO 14224 Table B.2 codes: wear 2.4, erosion 2.3, fatigue 2.6 | Confirmed: the data uses "1.x" / "2.x" |

No high-severity finding was rejected on re-check.

## 4. Themes and prioritised backlog

### Now: trust and SME-visible errors (before any external demo; mostly S effort)

| # | Action | Findings | Effort |
|---|---|---|---|
| N1 | Stop constructing "measured" values. Give meters independent values and put the residual into an explicit `unaccounted` fact, or relabel those tags as calculated with lineage. | P-1, E-7 | S |
| N2 | Propagate confidence as the minimum over lineage. Add `basis` to value facts. Give the 7 lineage-less calculated facts inputs or re-label them as recorded. | A-2, A-7, E-2 | S |
| N3 | Fix process errors. Re-yield the FCC to a volume gain. Add methanol to MTBE, plus reformer, coker and HCU light ends and a saturated gas plant. Add imported-VGO sulfur and a realistic residual-sulfur fate. Correct coke drum sizing and the E-401 inlet temperature. | P-3, P-4, P-5, P-8, P-9, P-12, E-6 | S–M |
| N4 | Fix integrity errors. Screen damage mechanisms on material × temperature × H2 partial pressure (no HTHA on austenitic steel, H2/H2S corrosion in hydroprocessing), and attach them at L7/L8 rather than whole columns. Correct the ISO 14224 codes. Fix the seal-plan rule for autoignition temperature and toxic service. Zero out idle-pump readings. Set alert limits on all pumps. | R-2, R-4, R-7, R-8 | S–M |
| N5 | Derive groupings from rules after all equipment exists (FLT-HOT), and require an `alert_limit` on every vibration tag. | A-3, R-7 | S |
| N6 | Make MCP tools fail loudly: unknown-ID errors, enum schemas for `event_class` and `relation`, and case-insensitive relations. Add negative tests. | A-6, S-2, S-11 | S |
| N7 | State honestly that the insight patterns were seeded, and show "unknown" instead of $0 for missing values. | S-5, A-7 | S |
| N8 | Correct overclaims in the handbook. `shacl_lite` covers 8 of 13 shapes. Controls described in C6/D3 are designed, not built. Portability is specified, not demonstrated. | S-1, S-8, S-9, O-7 | S |

### Next: Phase 1 foundations (make it a real fact source)

| # | Action | Findings | Effort |
|---|---|---|---|
| X1 | **Time model.** Add valid-time and record-time on facts, `supersedes`, multi-valued history, and `value(as_of=)`. Add a synthetic historian series behind `federated_read`. | O-3, A-4, S-6, S-7 | L |
| X2 | **Stable, multi-site identifiers.** Site-scoped IRIs, content-derived fact IDs, and a crosswalk to source-system tags (raw tags kept as literals). | O-4, S-3, S-4 | M |
| X3 | **Facts inside the ontology.** Predicates become IRIs with datatype and quantity kind, units become QUDT IRIs, PROV-O is fully mapped, and edge provenance is exported. | O-1, O-2, O-5, O-11 | M |
| X4 | **Real validation.** Split `directPartOf` from transitive `partOf`, add disjointness axioms, run pySHACL in CI with fixtures for every shape, and add a pre-commit scan. | O-6, O-7, O-10, S-8 | M |
| X5 | **AI access that scales.** Add `query_facts` and a bulk read, ranked search with aliases, `get_context(entity, intent, budget)`, compact payloads with pagination, relation-constrained `find_path`, and a `verify_answer` check. | A-1, A-5, A-7, A-8, A-9 | M |
| X6 | **Security baseline.** Caller identity, a sensitivity filter, an append-only call log, and a server-side citation check. | S-1 | M |
| X7 | **Scale and portability proof.** Load Gamma into Neo4j and one RDF store, run the cookbook queries against both in CI, and load-test at 150k tags. | S-9, S-10 | M |

### Then: the decision layers (choose by pilot)

| Layer | What it adds | Serves | Findings |
|---|---|---|---|
| **Economics & product quality** | Price sets (plan, actual, stress); unit margins and variable opex; carbon price; product specs and component blend qualities with giveaway; crude assay cut yields; an LP backbone (submodels, constraints, shadow prices); value contract on every insight | Planner, executive value case; reprices the $30M reformer and $8.8M failure figures credibly | E-1, E-3, E-4, E-5, E-8, E-9, E-11, P-7, P-10 |
| **Integrity & turnaround** | RBI (PoF/CoF, damage factors, inspection dates, tmin, remaining life); TMLs as series; relief devices; SIF attributes and final elements; API 584 IOW levels and response; turnaround scope; ISO 14224 code nodes; MTBF and spares | Inspection lead, reliability engineer, turnaround planner | R-1, R-3, R-5, R-6, R-8, R-9, R-12 |
| **Networks & utilities** | Sour water and rich amine per unit (H2S, NH3); hydrogen losses, purge and purity; fuel gas, steam, power and flare balances | Technical services, energy engineer, environmental | P-2, P-6, P-11 |
| **Semantic depth** | DNA inheritance resolver (class-level axioms or SHACL rules), IOF / CFIHOS / ISO 15926 alignment by IRI, functional location vs serial item | Portability, CFIHOS handover | O-8, O-9, O-12 |

## 5. Decisions required

| Decision | Options | Recommendation | Owner |
|---|---|---|---|
| Show Gamma to the Executive Director or clients before the "Now" fixes? | Show now with caveats / hold until fixed | **Hold** until N1–N8 are done. An SME would find the FCC volume loss and the constructed meters quickly, and that damages trust in the whole accelerator. | Sowthri |
| Which decision layer to build first | Economics & product quality / Integrity & turnaround | Tie it to the Phase 2 pilot. The current pilot (CDU overhead + hot pumps) needs **integrity**; a planning-led client needs **economics**. Offer both as pilot options in E4. | Sowthri with the ED |
| Human SME review | Process, integrity and instrumentation SMEs, one session each | Book after the "Now" fixes; use this report as the agenda. | Sowthri |

## 6. What to keep

- A clean hierarchy: one parent per node, levels always decrease, 0 domain violations on 93k triples.
- Facts as nodes with mandatory provenance. `explain_fact` traces a derived number down to PI tags.
- Credible deep-unit envelopes: ROT, regenerator, HCU pressure and WABT, coker COT and TMT against IOWs.
- Honest labelling of assumptions and caveats on insights. The hydrogen headroom and sulfur ceiling are the right planner questions.
- The deterministic build, and v0.3 fact IDs preserved in v0.4 (by build order, not by design; see X2).

## Appendix: all findings

Severity: C critical · H high · M medium · L low. Effort: S / M / L.

| ID | Sev | Finding | Effort |
|---|---|---|---|
| P-1 | C | Balances close by construction; closing values are labelled measured | S–M |
| P-2 | H | Hydrogen counts chemical consumption only. At 85% efficiency, make-up hydrogen exceeds supply (headroom about −34 MMSCFD) | M |
| P-3 | H | The FCC shows a 9.2 vol% liquid loss; implied coke 16 wt% and dry gas 7.4 wt% | S |
| P-4 | H | No mass basis: 4.5% of site mass unaccounted, light ends not routed, no saturated gas plant | M |
| P-5 | H | Sulfur in leaves out imported VGO; residual-product sulfur too low; SRU figure absorbs ±100 t/d | S–M |
| P-6 | H | Sour water and amine network almost empty; implied SWS H2S concentration is implausible; no NH3 | M |
| P-7 | M | No product quality; pool RON about 87.6; no FCC naphtha post-treater | M |
| P-8 | M | MTBE creates mass (4.5 → 6.5 kbd), with no methanol | S |
| P-9 | M | Coke drums need an 88% fill for 4,300 t/d | S |
| P-10 | M | Missing process KPIs (FCC delta coke and e-cat, HCU ppH2 and deactivation, DCU recycle, reformer RONC); CDU yields fixed | M–L |
| P-11 | M | Utility units hold capacity only; no steam, fuel gas or power balance | M |
| P-12 | L | E-401 hot inlet (420 °C) hotter than R-402 outlet (412 °C) | S |
| R-1 | C | No RBI or inspection layer; Turnaround and ScopeItem classes have no instances | L |
| R-2 | H | HTHA on 347SS; generic sulfidation in H2 service; clean wash water tagged NH4HS; whole columns tagged HCl | M |
| R-3 | H | 115 of 261 items have no damage mechanism; no loop on the DCU overhead or FCC gas plant; wet H2S, CUI, carbonate SCC, caustic SCC and temper embrittlement missing | M |
| R-4 | H | ISO 14224 codes wrong (wear 2.4, erosion 2.3, fatigue 2.6); no cause, detection, severity or TTR; FailureMode unused | M |
| R-5 | H | No relief devices; SIFs have no SIL, PFD, proof test or final element | M–L |
| R-6 | H | Missing IOWs (HCU ppH2, MPT, REAC Kp, FCC overhead pH, coke drum quench); 32 of 101 limits have no API 584 level; no response times | M |
| R-7 | M | 49 idle pumps show vibration; the bad actor is the standby; no alert limits on 68 conversion-unit pump tags | S |
| R-8 | M | No MTBF, spares or criticality; single seals in sour or above-autoignition service; motor inside the pump boundary | M |
| R-9 | M | Too few failures (fleet MTBF about 34 pump-years); IOW-A02 critical exceedance has no response; causal links unused | M |
| R-10 | M | Nominal wall = wall + 1.8 for every circuit; process temperature stored as metal design temperature | S |
| R-11 | L | TEMA type rule gives BEM to slurry, vacuum residue and high-pressure services; shell material missing | S |
| R-12 | L | No instruments, control valves or electrical items as assets; tanks have no API 653 data | M |
| O-1 | C | 117 of 126 fact predicates are undefined strings; mixed datatypes per predicate | M |
| O-2 | C | QUDT declared but unused; 53 free-text unit labels; 77 numeric facts without a unit | M |
| O-3 | H | No temporal model; `value()` returns insertion order; no named graphs or TriG | L |
| O-4 | H | Counter-based fact IDs; site-local reference nodes; no crosswalk | M |
| O-5 | H | Shallow PROV-O; free-text source systems; edge provenance dropped on export | S–M |
| O-6 | H | Transitive `partOf` conflicts with `maxCount 1` under inference | S |
| O-7 | H | `shacl_lite` covers 8 of 13 shapes; misses a range violation (`susceptibleTo` → Phenomenon) | M |
| O-8 | M | DNA inheritance neither computable nor materialised | L |
| O-9 | M | Standards alignment is string literals only; functional location conflated with the physical asset | M |
| O-10 | M | No disjointness axioms; `causedBy` domain misclassifies problem patterns | S |
| O-11 | L | Cached values duplicated; seal plan held as a string, not a concept | S |
| O-12 | L | No version IRIs; missing `owl:imports` | S |
| A-1 | H | No attribute filter or bulk read; screening costs 25–49 calls | M |
| A-2 | H | Confidence not propagated from inputs | S |
| A-3 | H | Fleet and alert-limit gaps give answers that look complete but aren't | S |
| A-4 | H | No history, so trend questions fail | M–L |
| A-5 | M | Substring search, no ranking or aliases | M |
| A-6 | M | Tools fail silently (WorkOrder rollup, relation case, unknown IDs) | S |
| A-7 | M | Insight numbers have no fact ID; missing values shown as $0; contract not enforceable | M |
| A-8 | M | No `get_context`; bloated payloads; no pagination | M |
| A-9 | M | `find_path` routes through the site hub | S |
| A-10 | L | Explorer fallback dumps every fact into the prompt; silent truncation | S |
| E-1 | C | No economic layer (prices, opex, carbon, cost centres empty) | M |
| E-2 | H | Site GRM applied to conversion-unit barrels (coker loss understated about 5×) | M |
| E-3 | H | $30.1M reformer value (70% of the total) rests on a low-confidence spread; no capex, basis or octane check | S–M |
| E-4 | H | No product specs, blending or giveaway | M |
| E-5 | H | Crude assays too shallow; crude swap unvalued | M–L |
| E-6 | M | 8.2% site liquid loss; not a Nelson-15 profile | M |
| E-7 | M | Sulfur closure by construction; hard-coded two-thirds Claus capacity | S |
| E-8 | M | No carbon price or site CO2; the fouling attribution overstates the gap | S–M |
| E-9 | M | Insight values sit on incompatible bases | S |
| E-10 | H | README value case lacks a baseline and $/bbl target; pilot can't show commercial levers | S–M |
| E-11 | M | No LP backbone, plan vs actual, turnaround or catalyst-cycle economics | M–L |
| S-1 | C | MCP has no auth, sensitivity filter or audit log, despite the C6/D3 claims | M |
| S-2 | C | Unknown IDs return empty results that look like real answers | S |
| S-3 | H | No onboarding path: no crosswalk, connectors or mappings; IDs reject real tag formats | L |
| S-4 | H | IDs collide across sites (44 node and 220 fact collisions when merged) | M |
| S-5 | H | Insight patterns are seeded; completeness test only ever sees perfect data | M |
| S-6 | H | No MOC or serial history; no process to correct a fact | M |
| S-7 | H | Stale snapshots cited as current, with high confidence | M |
| S-8 | M | SHACL coverage overstated; hypotheses absent from data and code | S–M |
| S-9 | M | Portability not demonstrated; Neo4j export only for the demo and not index-friendly | M |
| S-10 | M | In-memory design: about 495 MB at 25× Gamma; will not reach 10⁶–10⁷ facts | M |
| S-11 | M | Tests largely recompute the builder's own formulas; 3 negative tests | S |
| S-12 | M | Tag numbering not ISA-style; 96% of facts rated high confidence; pump model named "HX-300" | S |
