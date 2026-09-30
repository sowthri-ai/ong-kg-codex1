# Architecture decision log

Each entry records a decision that shapes the design. Changes to these decisions need a new entry that supersedes the old one ([CONTRIBUTING](../../CONTRIBUTING.md)).

Format: **Context · Decision · Consequences · Status**

---

## ADR-0001 Dual-spine L0–L10 hierarchy with a shared trunk
- **Context:** ISO 14224 gives an asset taxonomy (levels 1–9) but no process view and no data level. AI needs to trace business decisions down to sensors.
- **Decision:** L0 (industry) and L1 (segment) are shared. From L2 there are two spines: asset (ISO 14224 + L10 data point) and process (value stream → L8 decision point → L10 data element). They are joined by `ACTS_ON`, `GOVERNS`, `CONSUMES` and `INSTANTIATED_BY`.
- **Consequences:** Decision-to-sensor traceability; fixed level meaning; branches may skip levels. See [B1](../handbook/B1-hierarchy-L0-L10.md).
- **Status:** Accepted (2026-09-29)

## ADR-0002 Cross-cutting knowledge as backbones and facets, not extra levels
- **Context:** Software, KPIs, economics, physics and locations apply at many levels at once.
- **Decision:** Each gets its own backbone with its natural depth. Entities bind to backbones through typed, levelled, time-bound bindings. The principle is "one home, many bindings".
- **Consequences:** No duplication; the asset spine stays standards-compliant; a facet registry drives GraphRAG. See [B2](../handbook/B2-backbones-and-facets.md).
- **Status:** Accepted (2026-09-30)

## ADR-0003 OWL master for meaning, LPG runtime, triplestore for reasoning and exchange
- **Context:** Needs span formal semantics and standards exchange (RDF strengths) as well as fast traversal, algorithms and GraphRAG (LPG strengths).
- **Decision:** The ontology is authored in OWL / SHACL / SKOS in git. The LPG schema is compiled from it. The LPG holds instances. A triplestore holds the ontology, reference data, a selective RDF mirror and inferred graphs. There is one IRI per entity across stores.
- **Consequences:** No hand-maintained second schema; a CI gate prevents drift; runtime choice per client. See [C1](../handbook/C1-three-store-architecture.md).
- **Status:** Accepted (2026-09-30)

## ADR-0004 Facts are nodes with mandatory provenance
- **Context:** AI answers must be citable and auditable.
- **Decision:** Every quotable value is an `ogkg:Fact` with source, as-of date, owner, confidence, method and lineage. The latest value is also cached on the entity.
- **Consequences:** Larger graph; complete audit trail; the answer contract becomes enforceable. See [B5](../handbook/B5-facts-provenance-and-identity.md).
- **Status:** Accepted (2026-09-29)

## ADR-0005 One solid parent, many dotted branches
- **Context:** Corrosion loops, fleets, utilities and cost centres cut across the hierarchy.
- **Decision:** Exactly one `PART_OF` parent per node; any number of `MEMBER_OF` links to typed, owned grouping nodes. Default roll-ups follow `PART_OF` only.
- **Consequences:** No double counting; groupings become first-class and owned. See [B3](../handbook/B3-relationships-and-dotted-branches.md).
- **Status:** Accepted (2026-09-29)

## ADR-0006 DNA inheritance is read through, never copied
- **Context:** Descendants need ancestors' traits (service conditions, model design, exposure) without data duplication.
- **Decision:** Three channels (lineage, type, exposure). Inheritability is declared per property in the ontology; values are resolved at read time and labelled with their source.
- **Consequences:** One source of truth; explainable inheritance; a resolver component is needed. See [B4](../handbook/B4-entity-dna-inheritance.md).
- **Status:** Accepted (2026-09-30)

## ADR-0007 Discovered links are governed hypotheses
- **Context:** Rules, similarity and graph ML propose links that may be wrong.
- **Decision:** Inferred and discovered links are stored as hypothesis edges with status, confidence, method, run and evidence. SMEs validate or reject them; they never overwrite facts.
- **Consequences:** Discovery without eroding trust; rule precision becomes measurable. See [B6](../handbook/B6-problems-and-hypotheses.md).
- **Status:** Accepted (2026-09-30)

## ADR-0008 Federate time series and bulk data
- **Context:** Copying historian and document data would make the graph stale and expensive.
- **Decision:** The graph holds context, master facts, pointers and aggregates. Detail is fetched live through federated reads and returned with citations.
- **Consequences:** Smaller graph; freshness at source; federated-read latency must be managed. See [C3](../handbook/C3-ingestion-and-federation.md).
- **Status:** Accepted (2026-09-29)

## ADR-0009 One access layer for AI (MCP) with an answer contract
- **Context:** Many AI clients; the risk of uncited or invented numbers.
- **Decision:** All AI access goes through MCP tools (GraphQL/REST equivalents for others). The server sets the answer contract.
- **Consequences:** Consistent grounding; auditable calls; no direct database access for models. See [C5](../handbook/C5-ai-access-graphrag.md).
- **Status:** Accepted (2026-09-29)

## ADR-0010 Repository hosting and licence
- **Context:** The repository lives on a personal GitHub account; the asset is intended for the author's employer.
- **Decision:** Private repository, synthetic data only, proprietary notice. Revisit after the Executive Director decision ([E4](../handbook/E4-commercial-packaging.md), decisions 2 and 6).
- **Consequences:** No client data or licensed content in the repository; migration planned.
- **Status:** Accepted, temporary (2026-09-30)

## ADR-0011 Model depth follows the decision
- **Context:** Extending the reference model from the CDU to a whole refinery. Modelling every unit to L10 would multiply effort without serving more decisions.
- **Decision:** Every unit is modelled at L4–L5 with its capacity, feed, utilisation, Nelson factor and network role. Full L6–L10 depth is built only where a named decision needs equipment and tag data: the CDU, FCC, hydrocracker and delayed coker (heater run length, catalyst cycle, corrosion loops, compressor reliability). Each unit records its depth (`ogkg:modelDepth`).
- **Consequences:** Refinery-wide questions (hydrogen, sulfur, complexity, bottlenecks) are answerable now. Equipment-level questions on skeleton units return "not modelled" rather than an invented answer. Deepening a unit is a catalogue addition in `ogkg/refinery_units.py`. See [F6](../handbook/F6-reference-model-refinery-gamma.md).
- **Status:** Accepted (2026-10-01)
