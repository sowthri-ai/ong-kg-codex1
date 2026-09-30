# C1 Three-store architecture

## C1.1 Decision

**OWL is the master for meaning. The property graph (LPG) is the master for instance data and runtime. A triplestore handles reasoning, validation and exchange.** No schema is hand-maintained twice: the LPG schema is compiled from OWL, and selected graph data is mirrored back to RDF. Recorded as ADR-0003 in the [decision log](../adr/decision-log.md).

A visual version is in [`explorer/storage_blueprint.html`](../../explorer/storage_blueprint.html).

```
Git: OWL + SHACL + SKOS ──load──► TRIPLESTORE ◄──RDF sync (selected)── PROPERTY GRAPH ◄── source systems
          │                       reasoning, SHACL,                     entities, facts,
          │                       SPARQL, partner exchange              events, hypotheses
          └──── compile schema ──────────────────────────────────────►      ▲
                                   inferred links (hypothesis edges) ────────┘
```

## C1.2 What each store is for

| | OWL / SHACL / SKOS (git) | Triplestore (RDF) | Property graph (LPG) |
|---|---|---|---|
| Holds | Classes, relations, inheritance rules, shapes, vocabularies | Ontology + reference data + mirrored instances + inferred graphs | Instances, facet bindings, facts, events, problems, hypotheses |
| Best at | Being the single definition of meaning | Inference, SHACL validation, federation, standards exchange | Deep traversal, algorithms, GraphRAG, event scale |
| Query | — | SPARQL | Cypher / GQL (ISO/IEC 39075) |
| Written by | Ontology owner (pull requests) | Load from git; sync from LPG; rule jobs | Source connectors; rule write-back; SME validation |
| Identity | IRIs | IRIs | Local ID + `iri` property |

## C1.3 RDF and LPG compared

| | RDF / OWL | Labelled property graph |
|---|---|---|
| Basic unit | Triple | Node and edge, each with properties |
| Identity | Global IRIs | Local IDs |
| Meaning | Formal, machine-reasonable | In the schema or application layer |
| Properties on edges | RDF-star (being standardised as RDF 1.2) | Native |
| Validation | SHACL, strong | Constraints + custom checks |

## C1.4 Storage layers

| Layer | Holds | Where it lives |
|---|---|---|
| Semantic | OWL, SHACL, SKOS, facet registry | Git (`ontology/`); portable IP |
| Reference | Standard classes, failure modes, mechanisms, KPI definitions, equation library, application catalogue | LPG, mirrored in the triplestore |
| Instance | Entities L0–L10, bindings, dotted branches, events, problems, hypotheses | **LPG runtime** |
| Facts | Cited values with provenance | `Fact` nodes + `HAS_FACT`; latest value cached on the entity |
| Time series & bulk | Historian, raw lab, logs | Source systems (federated; see [C3](C3-ingestion-and-federation.md)) |
| Documents & vectors | P&IDs, procedures, reports as chunks | Vector index, chunks tagged with entity ID and facet |
| Access | `get_context`, `run_insight`, `explain_fact` | MCP / GraphQL / REST ([C5](C5-ai-access-graphrag.md)) |

## C1.5 Named graphs in the triplestore

| Named graph | Holds | Lifecycle |
|---|---|---|
| `urn:ogkg:ontology:v0.2` | OWL, SHACL, SKOS | Replaced per release |
| `urn:ogkg:reference` | Standard classes, patterns, KPI definitions | Versioned with the ontology |
| `urn:ogkg:data:<site>` | Mirrored instance data | Synced on change |
| `urn:ogkg:inferred:<run>` | Rule output | Dropped and recomputed each run |
| `urn:ogkg:staging:<batch>` | Contractor or partner inbound data | Deleted after promotion |

## C1.6 Sync rules

| # | Rule |
|---|---|
| S1 | **One writer per kind of data.** Sources → LPG. Ontology → git only. Rules → hypothesis edges only. |
| S2 | **Mirror selectively.** Entities, relations and facts go to RDF; time series, raw logs and document text do not. |
| S3 | **Recompute inferences, never edit them.** Stable IRIs make drop-and-rerun safe. |
| S4 | **Continuous-integration gate.** An ontology change regenerates the LPG schema; a sample graph is exported to RDF and validated with SHACL; a failure blocks the release ([D2](D2-change-control-and-release.md)). |

## C1.7 Runtime options per client

| Situation | Primary runtime |
|---|---|
| Default: operational AI, GraphRAG, analytics | LPG (e.g. Neo4j) + triplestore sidecar |
| Client on Cognite | Cognite Data Fusion data models as the LPG runtime (OWL compiles to spaces, containers and views) |
| JV / partner data sharing, CFIHOS or ISO 15926 handover | Add a triplestore SPARQL endpoint (e.g. GraphDB, Stardog, Apache Jena Fuseki) |
| Heavy formal reasoning on a small curated domain | Triplestore as primary |

Product names are examples to evaluate per client, not endorsements. The selection criteria are in [C6](C6-security-and-nfr.md).

## C1.8 Which store answers which question

| Question | Store |
|---|---|
| All rotating equipment at Alpha without a seal plan | Triplestore (class inference + SHACL) |
| Is E-401A at risk if Beta runs HSOB? | Triplestore rule → LPG hypothesis |
| Send partner X our export crude assays in standard form | Triplestore SPARQL endpoint |
| Did the opportunity crudes make money? | LPG |
| Context pack for P-201A | LPG + vector index |
| Which pumps share the failed pump's DNA? | LPG (similarity) |
