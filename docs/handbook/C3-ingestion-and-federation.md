# C3 Ingestion and federation

## C3.1 Principle

**Federate, don't copy.** The graph holds context, agreed master facts, pointers and aggregates. Time series and bulk records stay in their systems of record and are fetched on demand.

## C3.2 Source-system map

| Source (category) | Brings into the graph | Stays at source | Typical cadence |
|---|---|---|---|
| CMMS / EAM (e.g. SAP PM, Maximo) | Functional locations, equipment, work orders, failure coding, costs | Full work-order text, attachments | Daily CDC |
| Historian (e.g. PI, IP.21) | Tag list, units, IOW limits, aggregates (daily mean, std dev), exceedance events | Raw time series | Tag list weekly; aggregates daily; events near-real-time |
| LIMS | Sample points, specs, result aggregates, sampling intervals | Individual results older than the window | Daily |
| LP planning model | Marginal values, crude uplift per case | Full model | Per planning cycle |
| CTRM / crude scheduling | Cargoes, grades, volumes, windows | Contracts, prices beyond agreed fields | Per cargo |
| RBI / inspection database | Corrosion loops, inspection dates, measured rates, risk rank | Raw UT grids | Weekly |
| Engineering data (CFIHOS, DEXPI, datasheets) | Classes, models, design data, P&ID connectivity | Drawings | At handover and MOC |
| Document management | Document metadata + chunks (to vector index) | Originals | On change |
| TA planning | Scope items, freeze dates | Schedules | Weekly |

System names are examples; the application backbone records the client's actual systems ([B2](B2-backbones-and-facets.md)).

## C3.3 Ingestion pipeline

```
source ──extract (CDC / API)──▶ landing ──map to ontology──▶ staging graph ──SHACL gate──▶ LPG
                                      │                            │ fail
                                      └── identity resolution ──── └──▶ data-quality queue (owner notified)
```

| Step | What happens | Example |
|---|---|---|
| Extract | Change data capture or API pull | SAP PM notifications changed since last run |
| Map | Source fields → ontology classes and properties using a versioned mapping file | `QMEL-QMNUM` → `Failure.id`; damage code → `failure_mechanism` |
| Resolve identity | Match to existing IRIs through the tag crosswalk ([B5](B5-facts-provenance-and-identity.md)) | `ALP-CDU1-OVH-E101B` → `ogkg-alpha:E-101B` |
| Stage | Write to a staging graph as RDF or staging labels | `urn:ogkg:staging:sap-2026-09-30` |
| Validate | SHACL shapes for the affected classes ([C4](C4-reasoning-and-validation.md)) | A failure without a mechanism code → quality queue |
| Promote | Merge into the LPG as nodes, edges and `Fact` nodes with provenance | `HAS_FACT` with `source_system = SAP PM` |
| Mirror | Selected changes to the triplestore ([C1](C1-three-store-architecture.md)) | `urn:ogkg:data:alpha` |

## C3.4 Federated reads

When an AI needs detail the graph doesn't hold, the access layer calls the source through the pointer on the node:

| Need | Pointer in graph | Federated call |
|---|---|---|
| Last 24 h of overhead chloride | `T-CDU1-CL.external_id = AI-1021` | Historian API for AI-1021, returned with a citation to the source |
| Full text of a work order | `WO-002.external_id` | CMMS API |
| Partner assay | Partner IRI | SPARQL `SERVICE` to the partner endpoint |

Federated values are returned to the AI with a citation marked `federated: true` and a retrieval timestamp. They aren't stored unless promoted as facts.

## C3.5 Data-quality controls at ingestion

| Control | Enforced by |
|---|---|
| Mandatory provenance on every fact | `FactShape` |
| Exactly one `PART_OF` parent, level order respected | `SpineNodeShape` |
| Units valid and convertible | QUDT unit check |
| Freshness within SLA for data elements feeding decisions | Freshness monitor (the rule that caught the stale reformate RON) |
| No client data in the synthetic repository | Pre-commit scan ([D3](D3-ip-confidentiality-responsible-ai.md)) |
