# B4 Entity DNA and inheritance

## B4.1 The idea

The graph works like a family tree with DNA. A part at L9 still carries traits from its great-grandparents, from its kind and from what flows through it. The AI can then reason about the part without anyone copying data onto it.

## B4.2 Three DNA channels

| Channel | Inherited along | What a descendant picks up | Example |
|---|---|---|---|
| **Lineage DNA** | `PART_OF` (L0 → L10) | Site location, operator, regulatory regime, unit service conditions | P-201A seal faces inherit "vacuum residue, 365 °C" from VDU-1-VR |
| **Type DNA** | `IS_A` and `OF_MODEL` (class tree) | Failure modes, damage mechanisms, physics, maintenance strategy, KPIs, design limits | Mechanical seal › Plan 32 single seal › ISO 14224 seal failure modes |
| **Exposure DNA** | Material flow (`PROCESSED_IN`, `PRODUCES`, `FEEDS`) | Contaminants and conditions of what reached it | Doba crude (TAN 4.5) reached VDU-1 in February 2026 |

## B4.3 Worked example: P-201A seal faces (L9)

```
entity:   P-201A-SF  Seal faces (L9)
lineage:  Oil & Gas › Downstream › Refining › Refinery Alpha › VDU-1
          › Vacuum resid system › P-201A › Seal system › Mechanical seal
lineage DNA:   site = Refinery Alpha · service = vacuum residue · 365 °C  (from VDU-1-VR, P-201A)
type DNA:      model = HX-300 (OEM-A) · seal plan = API 682 Plan 32       (from P-201A)
               failure modes = ISO 14224 seal modes                        (from class MechanicalSeal)
exposure DNA:  Doba campaign CMP-A2D, TAN 4.5, Feb 2026                    (via CDU-1 → STR-AR-1 → VDU-1)
own facts:     none. Every trait above is inherited, and each one names its source.
```

## B4.4 Inheritance rules

| # | Rule |
|---|---|
| D1 | **Read through, never copy.** Inherited values are resolved at query time (or cached with invalidation) and shown as "inherited from X". There is one source of truth. |
| D2 | **Declared per property.** The ontology marks each property with `ogkg:inheritable`, `ogkg:dnaChannel` (lineage / type / exposure) and `ogkg:overridable`. |
| D3 | **Nearest wins, own beats inherited.** Resolution order: own value → nearest ancestor on the channel → class default. |
| D4 | **Exposure is time-bound.** Exposure DNA carries the campaign window; it expires unless the material keeps flowing. |
| D5 | **Not everything inherits.** Costs, failure counts and identity never inherit downward; they roll up instead ([B2.4](B2-backbones-and-facets.md#b24-how-performance-spreads-across-levels)). |
| D6 | **Explainable.** Every inherited value returned to an AI includes its channel and source entity ([C5](C5-ai-access-graphrag.md)). |

## B4.5 Which properties inherit

| Property | Channel | Inherits? | Why |
|---|---|---|---|
| Site, operator, country, regulatory regime | Lineage | Yes | True for everything on site |
| Service fluid, temperature, pressure | Lineage | Yes, overridable | A section's service applies to its equipment unless the equipment says otherwise |
| Metallurgy | Type (model) | Yes, overridable | From the model datasheet; as-built may differ |
| Failure modes, damage mechanisms | Type | Yes | Class knowledge |
| Crude contaminants seen | Exposure | Yes, time-bound | Depends on campaign windows |
| Cost, failure count, MTBF | — | No (they roll up) | Aggregates, not traits |
| Name, tag, serial | — | No | Identity is always own |

## B4.6 The DNA fingerprint

The full set of an entity's resolved traits forms a **DNA fingerprint** (a feature vector). It powers:

- **Similarity search:** "find every asset with the same DNA as the one that just failed";
- **Link prediction:** graph ML proposes missing `SUSCEPTIBLE_TO` links ([B6](B6-problems-and-hypotheses.md));
- **Transfer learning:** a reliability model trained on one site initialises for a sister site with matching DNA.

**Example:** a fingerprint match of P-401A (Beta) with P-201A (Alpha) on model, seal plan and service band explains why both fail about every 90 days.
