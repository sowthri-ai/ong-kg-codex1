# OGKG — Oil & Gas Value Chain Knowledge Graph

> **Status:** prototype v0.1 working · ontology v0.2 specified · Refinery Gamma CDU reference model complete (L0–L10, both sectors) · private repository · synthetic data only
> **Owner:** Sowthri (Principal Data & Industrial AI Architect) · **Licence:** proprietary, all rights reserved (see [LICENSE](LICENSE))

OGKG is a governed knowledge layer for the oil and gas value chain. Every AI solution (copilot, agent, optimiser, analytics app) queries it for facts and figures instead of recalling them, and uses it to find cross-domain insights that siloed systems cannot produce.

---

## 1. Objective

**Build once, reuse across every Industrial AI use case:** one semantic model of the O&G value chain, from L0 industry down to L10 data point. It links assets, processes, software, KPIs, economics, physics and problems, and each figure is cited with its source, date, owner and confidence.

| Outcome | How we'll know |
|---|---|
| AI answers are grounded and auditable | 100% of numbers in AI answers carry a fact ID; zero uncited figures in acceptance tests |
| Insights that siloed systems can't produce | At least 5 cross-domain insights live per client (prototype: 5 on demo data) |
| Each new use case costs less | Second and later use cases reuse ≥ 70% of the ontology, connectors and access layer |
| Portable across platforms | The same ontology runs on Neo4j, Cognite Data Fusion or a triplestore without remodelling |

**Why now:** AI pilots in refining keep rebuilding the same context (asset hierarchy, tag meaning, KPI definitions) and still hallucinate numbers. A shared knowledge layer fixes both, and turns individual pilots into an enterprise capability.

## 2. What it shows on the demo data

| Insight | Domains joined | Result (synthetic) |
|---|---|---|
| True value of opportunity crudes | Trading, LP, assay, IOW, maintenance, operations, economics | LP booked **+$6.98M**, net after asset consequences **−$1.98M** |
| Cross-site bad actor | Asset register, datasheets, maintenance, two sites | One pump model in hot service: 14 failures, MTBF ≈ 104 days |
| Octane giveaway root cause | LIMS, historian, blending, data governance | ≈ **$5.3M/yr**, traced to exchanger fouling plus stale lab data |
| Turnaround scope gaps | TA plan, IOW, maintenance, hierarchy | 4 corroding items missing before scope freeze |
| Decision blind spots | Process model, asset model, catalogue | 4 of 7 decisions lack data the organisation already holds |

## 3. Design principles

| # | Principle | In practice |
|---|---|---|
| P1 | **Business outcome first** | Every class, facet and insight must trace to a decision or value lever. Nothing is modelled "because it exists". |
| P2 | **Fixed meaning, variable depth** | L0–L10 levels mean the same everywhere; branches may skip levels but never reorder them. |
| P3 | **One home, many bindings** | Software, KPIs and other facets live once in their own backbone and bind to many levels. Never duplicate. |
| P4 | **Solid lineage, dotted branches** | Exactly one `PART_OF` parent; any number of typed `MEMBER_OF` groupings. Totals roll up only along solid lines unless a dotted roll-up is asked for explicitly. |
| P5 | **DNA is read through, never copied** | Traits inherit through three channels: lineage (part-of), type (is-a) and exposure (material flow). Each value shows where it was inherited from. |
| P6 | **Every number is a cited fact** | Value, unit, as-of date, source, owner, confidence, method and lineage are mandatory. Facts are nodes, not bare properties. |
| P7 | **Hypotheses are not facts** | Inferred and AI-discovered links carry a status (proposed → validated / rejected), confidence and evidence. |
| P8 | **OWL for meaning, LPG for motion** | The ontology is authored in OWL/SHACL/SKOS (git). The property-graph schema is compiled from it. A triplestore handles reasoning, validation and exchange. |
| P9 | **Federate, don't copy** | Time series and bulk data stay in source systems. The graph holds context, master facts, pointers and aggregates. |
| P10 | **Standards before invention** | Reuse ISO 14224, CFIHOS, ISO 15926, ISA-95, API 571/584, ISO 22400, QUDT, PROV-O, SKOS and BFO/IOF. Author only the linking layer. |
| P11 | **One door for AI** | All AI reads through one access layer (MCP) under one answer contract. No direct database access for models. |
| P12 | **Owned or it doesn't ship** | Every backbone, facet and fact domain has a named owner. SHACL completeness gates block unowned or incomplete data. |

## 4. Architecture at a glance

```
Git: OWL + SHACL + SKOS ──load──► TRIPLESTORE ◄──RDF sync── PROPERTY GRAPH ◄── source systems
  (the meaning, versioned)         reasoning · SHACL ·        (runtime: entities,  (SAP PM, PI, LIMS,
          │                        SPARQL · partner exchange   facts, events,       LP, CTRM, RBI)
          └──── compile schema ──────────────────────────────► hypotheses)
                                   inferred links ──────────►      │
                                                                   ▼
                                           AI access layer (MCP): get_context · run_insight · explain_fact
                                                                   ▼
                                                    Copilots · agents · optimisers
```

- **Model:** L0 Oil & Gas → L1 segment → an **asset spine** (ISO 14224, extended to L10 data points) and a **process spine** (value stream → decision point → data element).
- **Backbones:** location, enterprise, application, performance (KPI/KPF), material, physics, economics, problems and knowledge. Each binds to the spines.
- **Details:** [handbook](docs/handbook/README.md) · [decision log](docs/adr/decision-log.md) · interactive [storage blueprint](explorer/storage_blueprint.html)

## 5. Plan

| Phase | Scope | Exit criteria |
|---|---|---|
| **0. Prototype** ✅ | Synthetic 2-refinery dataset, 5 insights, MCP server, explorer, tests | Done (v0.1) |
| **1. Foundation** (≈ 8 weeks) | Ontology v0.2 in OWL/SHACL/SKOS, OWL→LPG compiler, triplestore + LPG runtime, facet bindings, `get_context` | SHACL passes on demo data; three-store sync proven; context packs served over MCP |
| **2. Pilot slice** (≈ 10–12 weeks) | One client site, one unit family (CDU overhead + hot pumps), real connectors (historian, CMMS, LIMS, LP) | ≥ 3 insights validated by client SMEs; answer contract met in user acceptance testing |
| **3. Scale** (≈ 3–6 months) | More units and sites, physics and economics facets, graph ML link prediction, second AI use case on the same layer | Second use case reuses ≥ 70% of the layer; adoption KPIs tracked |
| **4. Productise** | Packaged accelerator: ontology, connectors, insight library, delivery playbook | Approved as a reusable EY asset; reference client secured |

**Reference model:** a complete 500 kbpd, two-train CDU (157 equipment items, 950 tags, 3,293 cited facts) shows every design rule applied end to end. See [handbook F6](docs/handbook/F6-reference-model-gamma-cdu.md).

Detailed plan, team, risks and acceptance criteria: [Part E of the handbook](docs/handbook/README.md#part-e--how-it-is-delivered).

## 6. Repository map

| Path | Contents |
|---|---|
| `docs/handbook/` | MECE handbook (Parts A–F): why, model, architecture, governance, delivery, reference |
| `docs/adr/` | Architecture decision log |
| `ontology/` | `ogkg-core.ttl` (OWL), `ogkg-shapes.ttl` (SHACL), `ogkg-vocab.ttl` (SKOS), `mappings/` (OWL→LPG) |
| `examples/` | SPARQL and Cypher queries used in the handbook |
| `ogkg/` | Prototype engine: dataset builder, KG engine, insights, MCP server, exports |
| `data/` | Synthetic demo graph (`kg.json`) and the Refinery Gamma CDU reference model (`cdu-gamma/`: Turtle by sector, registers, JSON) |
| `exports/` | Generated Turtle and Neo4j CSV / Cypher |
| `explorer/` | Interactive explorers (demo and Gamma CDU) and storage blueprint (self-contained HTML) |
| `tests/` | Integrity, provenance, insight recalculation, ontology syntax, handbook claims, links and MCP end-to-end tests |
| `CLAUDE.md` | Working rules for coding agents implementing the backlog |

## 7. Quickstart (prototype)

```bash
python -m pip install -r requirements.txt   # Python 3.10+
python -m ogkg.build_dataset                # rebuild data/kg.json
python -m ogkg.exports                      # Turtle, Neo4j CSV, explorer HTML
python -m ogkg.catalogue                    # regenerate handbook F3 from the ontology
python -m ogkg.cdu_gamma && python -m ogkg.ttl_v02 && python -m ogkg.cdu_explorer   # Gamma CDU model
python -m unittest discover -s tests -v     # 52 tests
python -m ogkg.mcp_server                   # MCP server on stdio
```

MCP client configuration:

```json
{"mcpServers": {"ogkg": {"command": "python", "args": ["-m", "ogkg.mcp_server"], "cwd": "/path/to/ogkg"}}}
```

## 8. Data and confidentiality

- **All data in this repository is synthetic.** Refinery Alpha and Beta, their equipment, events and costs are fictional. Named crude grades carry indicative typical assay values only.
- **Never commit client names, client data, credentials or licensed content** (Perry's tables, API Technical Data Book, DIPPR, Platts/Argus prices). See [handbook D3](docs/handbook/D3-ip-confidentiality-responsible-ai.md).
- This repository is private while EY ownership and hosting are confirmed. Moving it to an EY-approved repository is an open decision (see Part E).
