# E1 Roadmap and phase plan

Durations are indicative planning estimates for a core team (see [E2](E2-team-and-operating-model.md)). Confirm them after pilot scoping.

## E1.1 Phases

| Phase | Duration | Objective | Exit criteria |
|---|---|---|---|
| **0. Prototype** ✅ | Done | Prove the idea on synthetic data | 5 insights, MCP server, explorer, 17 tests passing |
| **1. Foundation** | ≈ 8 weeks | Make the design implementable and portable | Ontology v0.2 validated; OWL→LPG compiler; triplestore + LPG running; `get_context` live; SHACL gates in CI |
| **2. Pilot slice** | ≈ 10–12 weeks | Prove value on one client site | Real connectors for 4+ systems; ≥ 3 insights validated by client SMEs; answer contract met in UAT; value case rebuilt on client data |
| **3. Scale** | ≈ 3–6 months | More units, sites and one more AI use case on the same layer | Second use case reuses ≥ 70% of the layer; physics and economics facets live; adoption metrics tracked |
| **4. Productise** | Ongoing | Packaged accelerator | Approved reusable asset; delivery playbook; reference client |

## E1.2 Phase 1 backlog (Foundation)

| ID | Item | Output | Depends on |
|---|---|---|---|
| E1-P1-01 | Validate `ontology/*.ttl` with an RDF parser and pySHACL in CI | Green CI pipeline | — |
| E1-P1-02 | OWL→LPG compiler | `schema.cypher`, `labels.json`, `relationships.json`, `resolver.json`, `facet-registry.json` ([C2](C2-owl-to-lpg-mapping.md)) | 01 |
| E1-P1-03 | Load demo data into Neo4j and a triplestore; RDF mirror job | Two running stores, one IRI space | 02 |
| E1-P1-04 | Align RDF export to QUDT units and SKOS confidence terms | Updated `exports.py` | 01 |
| E1-P1-05 | Rules R-07, R-08, R-12 as SPARQL CONSTRUCT; hypothesis write-back | `AT_RISK_OF` / `SUSCEPTIBLE_TO` edges with status | 03 |
| E1-P1-06 | Facet bindings + DNA resolver | Own / inherited / derived / hypothesis labels on every value | 02 |
| E1-P1-07 | `get_context(entity, intent)` and `query_hypotheses` MCP tools | Context packs ([C5](C5-ai-access-graphrag.md)) | 06 |
| E1-P1-08 | Dotted-branch groupings (corrosion loop, fleet) in the demo data | `MEMBER_OF` edges, fleet insight rewritten to use them | 03 |
| E1-P1-09 | Explorer: solid / dotted / dashed line convention; facet lens view | Updated explorer ([B3.6](B3-relationships-and-dotted-branches.md#b36-visual-convention)) | 06 |
| E1-P1-10 | Answer-contract test harness (LLM-in-the-loop, sampled questions) | Pass/fail report per release | 07 |
| E1-P1-11 | Pre-commit confidentiality scan ([D3](D3-ip-confidentiality-responsible-ai.md)) | Hook + deny-list | — |
| E1-P1-12 | Cognite Data Fusion data-model generation (optional) | Spaces, containers and views YAML | 02 |

## E1.3 Phase 2 plan (Pilot slice)

| Weeks | Workstream | Activities |
|---|---|---|
| 1–2 | Scoping & value | Pick the slice (e.g. CDU overhead + hot pumps); confirm value hypotheses with the sponsor; baseline the metrics |
| 1–4 | Connectors | CMMS, historian (aggregates + events), LIMS, LP; identity crosswalk |
| 3–6 | Model binding | Bind client entities to spines and facets; SHACL remediation with data owners |
| 5–8 | Insights | Adapt 3–5 reference insights; run hypothesis review with SMEs |
| 7–10 | AI use case | One copilot or agent on `get_context`; UAT against the answer contract |
| 9–12 | Value & handover | Value case on client data; adoption plan; Phase 3 proposal |

## E1.4 Milestones and decisions

| Milestone | Decision required | By whom |
|---|---|---|
| End of Phase 0 | Invest in Phase 1 as a reusable asset? | Executive Director / Partner |
| Phase 1 week 2 | Runtime(s) for the reference build (Neo4j, Cognite DM, triplestore) | Solution architect + ED |
| End of Phase 1 | Pilot client and slice | ED / account lead |
| End of Phase 2 | Scale scope and commercial model | Client sponsor + Partner |
