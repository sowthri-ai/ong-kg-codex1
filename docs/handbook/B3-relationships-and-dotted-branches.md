# B3 Relationships and dotted branches

## B3.1 Relationship families

Every edge belongs to exactly one family. The full catalogue is in [F3](F3-class-and-relation-catalogue.md).

| Family | Purpose | Examples |
|---|---|---|
| **Hierarchy (solid)** | The one home of each node | `PART_OF` |
| **Grouping (dotted)** | Secondary memberships | `MEMBER_OF` → corrosion loop, fleet, utility, cost centre |
| **Cross-spine** | Joins process to asset | `ACTS_ON`, `GOVERNS`, `CONSUMES`, `INSTANTIATED_BY` |
| **Type & design** | Links an instance to its kind | `IS_A`, `OF_MODEL`, `MANUFACTURED_BY`, `INSTALLED_AT` |
| **Material flow** | What moves between assets | `PROCESSED_IN`, `PRODUCES`, `FEEDS`, `COMPONENT_OF`, `SOLD_TO` |
| **Facet binding** | Entity ↔ backbone | `LOCATED_AT`, `OPERATED_BY`, `SUPPORTED_BY`, `SYSTEM_OF_RECORD_FOR`, `DRIVES`, `CONTROLLED_BY` |
| **Event** | What happened | `FAILURE_OF`, `ON_DATAPOINT`, `REMEDIATES`, `IN_SCOPE_OF`, `TARGETS` |
| **Causal / problem** | Why it happened | `OBSERVED_ON`, `CAUSED_BY`, `AFFECTS_KPI`, `RESOLVED_BY`, `SIMILAR_TO` |
| **Evidence** | Where a number came from | `HAS_FACT`, `DERIVED_FROM` |
| **Hypothesis** | Proposed, not yet true | `AT_RISK_OF`, `SUSCEPTIBLE_TO` (with status) |

## B3.2 Solid lines and dotted lines

**The rule:** every node keeps **one solid parent**, its home in L0–L10. It may have **any number of dotted branches** to typed grouping nodes. The solid line answers "where does this sit?"; a dotted line answers "what else does it belong to?"

```
Solid:   Oil & Gas › Downstream › Refining › Refinery Alpha › VDU-1 › Vacuum resid system › P-201A
Dotted:  P-201A ┄┄ Fleet: HX-300 hot-service pumps (4 pumps, 2 sites)
         P-201A ┄┄ Cost centre: Alpha maintenance, VDU area
         P-201A ┄┄ Criticality class: A (production-critical)
```

## B3.3 Where dotted branches belong

| Grouping type | Attaches at | Why it matters | Example |
|---|---|---|---|
| Corrosion loop / integrity circuit (API 570, RBI) | L5–L6 | One damage mechanism across several items | CL-01: E-101A/B, V-102, PC-101 |
| Equipment fleet (model × service) | L6 | Cross-site comparison | HX-300 in ≥ 340 °C service |
| Shared utility (steam, flare, cooling water) | L4–L6 | One utility serves many units | Flare header FL-A |
| Safety instrumented function / SIL loop | L6–L10 | A trip spans sensor, logic and valve | SIF-101 CDU heater trip |
| SAP functional location / cost centre / maintenance plant | L3–L6 | Finance and maintenance views | ALP-CDU1-OVH |
| Shared process step | L6–L7 | One activity used by two processes | "Review IOW exceedances" |
| Shared data element | L10 | One tag feeds several decisions | Chloride used by dosing and crude acceptance |

## B3.4 Rules

| # | Rule |
|---|---|
| R1 | `PART_OF` is exactly one per node; `MEMBER_OF` is zero to many. |
| R2 | Every grouping node has a type (`CorrosionLoop`, `Fleet`, `Utility`, `SIF`, `CostCentre`, …) and a named owner. |
| R3 | Totals roll up along `PART_OF` by default. A dotted roll-up ("failures in loop CL-01") must be requested explicitly, to avoid double counting. |
| R4 | Dotted branches may skip levels and cross spines; solid lines may not. |
| R5 | A grouping that proves universal across clients becomes a backbone ([B2](B2-backbones-and-facets.md)); record that as a decision in the ADR log. |

## B3.5 Worked example: why the fleet grouping matters

In the prototype the bad-actor insight had to rebuild the "HX-300 in hot service" group on the fly by joining model and service-temperature facts. With a stored `Fleet` grouping:

- the group has an owner (the fleet reliability engineer);
- new pumps join automatically when a SHACL rule matches the model and service band;
- the problem-pattern library ([B6](B6-problems-and-hypotheses.md)) links directly to the fleet, so a failure at one site raises a hypothesis for every other member.

## B3.6 Visual convention

| Line | Meaning |
|---|---|
| Solid | Home hierarchy (`PART_OF`) and asserted relations |
| Dotted | Grouping membership (`MEMBER_OF`) |
| Dashed, rust colour | Inferred or hypothesis edge |

The explorer currently draws `PART_OF` dashed in its evidence map. Switching to this convention is backlog item E1-P1-09 ([E1](E1-roadmap.md)).
