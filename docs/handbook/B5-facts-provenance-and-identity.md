# B5 Facts, provenance and identity

## B5.1 The fact contract

Every value an AI may quote is a **Fact** with these fields:

| Field | Meaning | Example (`F-00110`) |
|---|---|---|
| `id` | Stable fact ID, used in citations | F-00110 |
| `subject` | Entity the fact is about | CMP-A1 (HSOB campaign) |
| `predicate` | What is stated | `lp_uplift_total` |
| `value` + `unit` | The figure and its unit (QUDT) | 1,890,000 USD |
| `as_of` | When it was true | 2025-11-24 |
| `source_system` + `source_ref` | Where it came from | KG derived (inputs from Hydrocarbon Accounting and the LP model) |
| `owner` | Accountable role | Site Economist |
| `confidence` | high / medium / low | medium |
| `method` | measured, recorded, calculated, declared, indicative, assumption | calculated |
| `lineage` | Fact IDs a derived value was calculated from | F-00107 (volume 900 kbbl), F-00109 (uplift $2.10/bbl) |

The fields are mandatory; SHACL `FactShape` enforces them ([C4](C4-reasoning-and-validation.md)).

## B5.2 Why facts are nodes

| Option | Problem |
|---|---|
| Value as a bare property on the entity | Source, date, confidence and history are lost |
| Value as a property with a metadata map | Cannot be cited, versioned or linked to lineage |
| **Fact node + `HAS_FACT` edge** ✅ | Citable, versioned, lineage-linked. The latest value is also cached on the entity for fast queries |

## B5.3 Confidence and method, used honestly

| Method | Typical source | Default confidence | AI must say |
|---|---|---|---|
| measured | Historian, analyser, lab | high | — |
| recorded | CMMS, accounting, logbook | high | — |
| calculated | KG-derived or LP | medium–high | "calculated from …" when asked |
| declared | Design data, registers | high | — |
| indicative | Public typical values | medium | "indicative, not contract-grade" |
| assumption | Planning assumptions | low | "assumption; replace with site value" |

**Example:** octane value $0.60 per RON-bbl (`F-00139`) is `method=assumption, confidence=low`, so every answer using the $5.3M giveaway figure must flag it.

## B5.4 Lineage

Derived facts point to their inputs, so any AI can explain a number:

```
F-00157 lost_margin (FL-001) = 50 kbd × 5 days × $8.20/bbl = $2.05M
   └── derived from: F-00155 rate_reduction (Operations Logbook)
                     F-00156 rate_reduction_days (Operations Logbook)
                     F-00005 grm_fy2026 (Site Economics)
```

The MCP tool `explain_fact` returns this tree ([C5](C5-ai-access-graphrag.md)).

## B5.5 Identity: one entity, many names

**Plant and instrument tags** differ by system. One node keeps a **crosswalk** of all of them:

| System | Identifier for E-101B |
|---|---|
| OGKG IRI | `ogkg-alpha:E-101B` |
| P&ID tag | E-101B |
| SAP functional location | ALP-CDU1-OVH-E101B |
| Historian asset | ALPHA.CDU1.E101B |
| Inspection DB | INSP-E-101B |

**Classification tags** (hot service, sour service, safety-critical) come from a SKOS vocabulary ([ontology/ogkg-vocab.ttl](../../ontology/ogkg-vocab.ttl)), never free text.

## B5.6 Four identities of a physical asset

| Layer | Meaning | Example |
|---|---|---|
| Class | The generic kind | Centrifugal pump, OH2 (API 610) |
| Model | The maker's design | OEM-A HX-300: rated flow, head, design temperature, metallurgy |
| Serial | The physical unit | S/N 44718, as built, install date |
| Functional location | The position in the plant | Slot P-201A. The serial can be swapped; the position stays. |

Design details (datasheet fields, design vs operating envelope, standards compliance) live on the model and serial layers and flow down as Type DNA ([B4](B4-entity-dna-inheritance.md)). Property lists per class follow CFIHOS.

## B5.7 IRIs

- Pattern: `https://<namespace>/<site-or-scope>/<local-id>`. The prototype uses `ogkg-alpha:E-101B`.
- The same IRI is stored on the property-graph node (`iri` property) and used as the RDF subject, so the two stores stay joined ([C1](C1-three-store-architecture.md)).
- IRIs never change. Renames update labels and aliases, not IRIs.
- The production namespace domain is a decision for Phase 1 ([E4](E4-commercial-packaging.md)).
