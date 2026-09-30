# A2 Use cases, personas and insights

## A2.1 Personas and the levels they work at

| Persona | Works at | Typical question | What OGKG gives them |
|---|---|---|---|
| Refinery / portfolio executive | L2–L3 | "Where are we leaking margin?" | KPIs rolled up from L10 facts, ranked by value at stake |
| Crude & planning manager | L3–L4 | "Should we buy another HSOB cargo?" | Crude value net of asset consequences |
| Unit / process engineer | L4–L6 | "Why is reformate RON swinging?" | Signals traced across historian, LIMS and equipment condition |
| Reliability / integrity engineer | L6–L9 | "Which pumps share this failure DNA?" | Fleet patterns, damage mechanisms, hypothesis links |
| Turnaround manager | L3–L6 | "What is missing from scope before freeze?" | Integrity evidence compared with scope items |
| Data owner / governance lead | L9–L10 | "Which decisions run on stale data?" | Freshness and completeness checks tied to decision points |
| AI engineer | All | "What context should the agent get?" | `get_context` packs with cited facts |

## A2.2 Use-case catalogue by level band

| Band | Use case | AI pattern | Backbones used |
|---|---|---|---|
| Strategic (L0–L2) | Margin-leakage copilot | Grounded Q&A over roll-ups | Performance, economics |
| Strategic | Portfolio benchmarking | Cross-site comparison | Location, enterprise, performance |
| Operations (L3–L5) | Crude-selection advisor | Agent + LP + reliability penalty | Material, economics, problems |
| Operations | Blend-giveaway root cause | Graph traversal + anomaly | Process, application, performance |
| Operations | Energy and loss agent | Physics-informed analytics | Physics, performance |
| Engineering (L6–L8) | Bad-actor and fleet reliability | Similarity + link prediction | Design, problems |
| Engineering | Turnaround scope advisor | Rules + hypothesis review | Problems, physics, process |
| Engineering | Work-order copilot | GraphRAG over procedures | Knowledge, process |
| Evidence (L9–L10) | Data-freshness guardian | Rule monitoring | Application, process |
| Evidence | Soft sensors / anomaly detection | ML with graph features | Physics, performance |

## A2.3 The five reference insights (prototype)

Each insight is a stored query over the graph, returned in a fixed shape: headline, rows, path, evidence fact IDs, recommendation, owner and caveat. Details: [F5](F5-prototype-guide.md).

### 1. True value of opportunity crudes
- **Question:** did the discounted crudes make money once asset consequences are counted?
- **Path:** crude grade → campaign → CDU-1 → downstream units → IOW exceedances and corrosion failures → work-order cost + lost margin.
- **Result:** LP uplift $6.98M; repairs, lost throughput and treatment $8.96M; **net −$1.98M**.
- **Decision:** add a corrosion $/bbl penalty to the crude buy decision; cap HSOB until the desalter upgrade.
- **Caveat:** attribution is temporal and topological; confirm by root-cause analysis.

### 2. Cross-site bad actor
- **Question:** is the seal problem a site problem, a pump problem or a service-condition problem?
- **Result:** HX-300 pumps in ≥ 340 °C service failed 14 times across two sites (MTBF ≈ 104 days). The same model in cooler service had no failures; a dual-seal model in the same hot service had one.
- **Decision:** fleet standard for hot-service seals, raised once instead of site by site.

### 3. Octane giveaway root cause
- **Result:** Alpha gives away 0.62 RON against 0.18 at Beta, ≈ $5.3M/yr. Traced to E-301 fouling (+62%), reactor temperature swings and reformate RON sampled every 24 h against an 8 h freshness target.
- **Caveat:** octane value per RON-barrel is a low-confidence planning assumption.

### 4. Turnaround scope gaps
- **Result:** E-101B, PC-101, PC-201 and P-103 carry integrity evidence but are not in the 2027 TA scope; scope freezes 15 Nov 2026.

### 5. Decision blind spots
- **Result:** crude buy and crude acceptance decisions govern assets with $8.5M of corrosion consequences but consume no reliability data. The recipe decision uses stale data, and TA scope inclusion has no system of record.

## A2.4 Worked example: one question, end to end

**"Should we buy another HSOB cargo?"**

1. The access layer resolves the question to decision point `DEC-CRBUY` (L8, process spine).
2. `DEC-CRBUY` consumes only `DE-GRMUP` (LP uplift, L10). That's a blind spot.
3. The traversal follows `GOVERNS → CDU-1 (L4) → overhead system (L5) → E-101A/B, PC-101 (L6) → failures`, then the lost-margin and repair-cost facts.
4. The answer: *"LP shows +$2.10/bbl [F-…], but the last three HSOB campaigns lost $1.98M net after corrosion [F-…]. Cap at ≤ 15% of slate until the desalter upgrade. Owner: Crude & Planning Manager."*
5. The decision and its outcome are written back to `DEC-CRBUY`, so realised value can be tracked.
