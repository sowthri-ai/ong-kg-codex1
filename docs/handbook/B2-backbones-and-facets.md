# B2 Backbones and facets

## B2.1 The problem this solves

ISO 14224 is asset-centric. Software, KPIs, KPFs, economics and physics aren't parts of equipment, and they apply at many levels at once. Forcing them into the asset tree duplicates them and breaks roll-ups.

## B2.2 The design: several backbones in one graph

A **backbone** is a small taxonomy with its own natural depth. Entities on the two spines **bind** to backbone nodes. A **facet** is the set of bindings between one entity and one backbone.

| Backbone | Describes | Its own levels | Depth | Standard |
|---|---|---|---|---|
| Asset (spine) | What physically exists | L0–L10 ([B1](B1-hierarchy-L0-L10.md)) | 11 | ISO 14224, CFIHOS |
| Process (spine) | What we do and decide | L0–L10 ([B1](B1-hierarchy-L0-L10.md)) | 11 | APQC-style levels |
| Location | Where it is | Country › Region › Site › Area › Plot | 5 | ISO 3166, WGS84 |
| Enterprise | Who owns and operates it | Group › Company › Business unit › Operator / Role | 4 | W3C ORG, LEI |
| Type & design | What kind of thing it is, who made it | Category › Class › Type › Model › Serial | 5 | ISO 14224 classes, CFIHOS, API 610/682, TEMA |
| Application | Which software supports or records it | Portfolio › Application › Module › Interface › Data object | 5 | ISA-95 functional model, ArchiMate |
| Performance | How it is measured and steered | Strategic KPI › Tactical KPI › Operational KPI › KPF › Metric | 5 | ISO 22400 |
| Material | What flows through it | Grade › Campaign › Stream › Product › Market | 5 | Assay conventions |
| Physics | Why it behaves as it does | Discipline › Phenomenon › Mechanism › Equation › Parameter | 5 | API 571/584, first principles |
| Economics | What it is worth | Value driver › Cost/revenue element › Cost item › Rate or coefficient | 4 | Site economics, LP marginal values |
| Problems | What goes wrong | Problem class › Failure mode › Mechanism › Root cause › Incident | 5 | ISO 14224 failure modes |
| Knowledge | What is written about it | Collection › Document › Section › Chunk | 4 | Document control |

Every entity also always carries two core facets: **identity** (names, tags, aliases) and **lineage** (its path from L0). See [B5](B5-facts-provenance-and-identity.md) and [B4](B4-entity-dna-inheritance.md).

## B2.3 One home, many bindings

Separate three things for every cross-cutting item:

| | Definition | Binding | Value |
|---|---|---|---|
| **What it is** | Defined once, in its own backbone | Where it applies: a link to an entity with level, scope and validity | The actual number, as a fact on the entity where measured |
| **KPI example** | MTBF: formula, unit, owner, aggregation rule | Applies at L4–L8 | P-201A = 91 days; rolled up to VDU-1 and Refinery Alpha |
| **Software example** | LIMS as a product category | Instance "LIMS–Alpha" scoped to Refinery Alpha (L3) | System of record for all lab data points at Alpha |

## B2.4 How performance spreads across levels

| Level band | Typical KPIs / KPFs | How values arrive |
|---|---|---|
| L2–L3 | GRM, energy intensity, OPEX $/bbl, mechanical availability | Rolled up by rule (capacity- or time-weighted) |
| L4–L5 | Throughput, yield, conversion, unit availability | Calculated from L10 data and rolled up from equipment |
| L6–L8 | MTBF, efficiency, fouling factor | Calculated from events and tags |
| L10 | Raw metrics and KPF readings | Measured |

**The KPF loop:** a KPF `DRIVES` a KPI and is `CONTROLLED_BY` an L8 decision, and it is `MEASURED_BY` an L10 tag.

> Overhead chloride (KPF) → drives corrosion rate and availability (KPI) → controlled by "Adjust neutraliser / wash-water rate" (L8) → measured by AI-1021 (L10).

## B2.5 How software spreads across levels

| Binding level | Example | Effect |
|---|---|---|
| L3 site | Historian, CMMS, LIMS for Alpha | Inherited by every descendant; one binding covers thousands of entities |
| L4 unit | Advanced process control on CDU-1 | Applies to CDU-1 only |
| L6 equipment | Vibration monitoring on P-201A | Own binding on that pump |
| L4–L5 process | `SUPPORTS` "Work Order Execution" | Links software to the process it serves |
| L9–L10 data | `SYSTEM_OF_RECORD_FOR` "Work order" | Tells the AI where a number comes from |

## B2.6 Facet rules

| # | Rule |
|---|---|
| F1 | Facets are nodes and edges, not flat properties. Only identity attributes (name, tag, serial) stay as properties. |
| F2 | Each binding edge carries level, scope, valid-from / valid-to, source, owner, confidence, aggregation rule and inheritance rule. |
| F3 | Attach at the most specific facet level that applies; higher facet levels come free. |
| F4 | Every facet value is labelled **own, inherited, derived or hypothesis**. |
| F5 | Conflict resolution order: own → nearest ancestor → type default → derived. Always show the source. |
| F6 | Facets are separate from each other: one fact lives in exactly one facet. |
| F7 | Each backbone uses a controlled vocabulary (SKOS) and has a named owner ([D1](D1-governance-and-ownership.md)). |
| F8 | Facet depth is set by the same four tests as levels ([B1.4](B1-hierarchy-L0-L10.md#b14-why-these-levels-and-not-8-or-12)); never pad to a magic number. |
| F9 | A **facet registry** records each facet's depth, owner and the question types it serves. GraphRAG reads it ([C5](C5-ai-access-graphrag.md)). |
| F10 | People see entities through **lenses** (reliability, economics, IT/OT, operations). A lens is a saved facet selection, not a separate model. |

## B2.7 Example: P-201A resolved through its facets

| Facet | Value | Status |
|---|---|---|
| Lineage | Oil & Gas › Downstream › Refining › Refinery Alpha › VDU-1 › Vacuum resid system | own |
| Type & design | Pump › HX-300 (OEM-A) › API 682 Plan 32 single seal | own |
| Application | PI historian (Alpha), SAP PM (Alpha) | inherited from Refinery Alpha (L3) |
| Performance | MTBF 91 days (group average 104) | derived from 4 failure events |
| Material / flow | Vacuum residue, 365 °C | inherited from VDU-1-VR |
| Economics | Seal repair $38k per event | own (SAP PM) |
| Problems | Matches pattern "HX-300 seal failure in hot service" | hypothesis → validated |
