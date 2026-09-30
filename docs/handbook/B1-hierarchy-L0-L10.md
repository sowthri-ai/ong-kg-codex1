# B1 The L0–L10 hierarchy

## B1.0 Building blocks of the model

Part B describes the model in five building blocks. Organising principles (the ontology) are reusable across clients; instance data is client-specific.

| Block | What it is | Example | Defined in |
|---|---|---|---|
| **Nodes** | The things | P-201A, HCl corrosion, Refinery Alpha | B1, B2 |
| **Edges** | Typed relationships, which can carry properties | `FAILURE_OF` (date), `AT_RISK_OF` (confidence) | B3 |
| **Properties** | Attributes of nodes and edges, with unit, date and source | service temperature = 365 °C | B5 |
| **Organising principles** | Classes, levels, inheritance rules, constraints | "every pump has a model and a seal plan" | B1–B6, `ontology/` |
| **Instance data** | The actual assets, events and values | P-201A's four seal failures | `data/kg.json` (demo) |

## B1.1 The idea

Eleven zoom levels, from the whole industry (L0) to one measured number (L10). L0 and L1 are a **shared trunk**. From L2 the graph splits into two spines:

- the **asset spine**: what physically exists (ISO 14224 levels 1–9, plus L0 and L10);
- the **process spine**: what the business does and decides.

## B1.2 Level definitions

| Level | Abstract meaning | Asset spine | Example | Process spine | Example |
|---|---|---|---|---|---|
| **L0** | Domain | Industry (shared) | Oil & Gas | ← same | |
| **L1** | Value-chain segment | Segment (shared) | Downstream | ← same | |
| **L2** | Line of business | Business category | Refining | Value stream | Crude-to-Product |
| **L3** | Operating entity / capability | Installation (site) | Refinery Alpha | Process group | Crude Supply & Valuation |
| **L4** | Production unit / owned process | Plant / unit | CDU-1 | Process | Crude Selection & Valuation |
| **L5** | Functional block | Section / system | CDU-1 overhead system | Sub-process | Assay Evaluation |
| **L6** | The thing you point at / assign | Equipment unit | E-101B condenser | Activity | Screen crude contaminants |
| **L7** | Major part / one person's step | Subunit | Tube bundle | Task | Check TAN / salt vs limits |
| **L8** | What fails / what gets decided | Maintainable item | Tubes | **Decision point** | Accept crude & set max % |
| **L9** | What it's made of / what informs it | Part | Seal faces | Data object | Crude assay |
| **L10** | The atomic fact | **Data point** (tag, lab result, KPI value) | AI-1021 overhead chloride | **Data element** | Salt content |

**Level bands**

| Band | Levels | Purpose |
|---|---|---|
| Strategic context | L0–L2 | Where value is created |
| Operations | L3–L5 | How value is produced and managed |
| Engineering & work | L6–L8 | What fails, what is fixed, what is decided |
| Evidence | L9–L10 | The facts that prove it |

## B1.3 Where the spines meet

| Meeting point | Relation | Example |
|---|---|---|
| L4 process ↔ L4–L5 asset | `ACTS_ON` | Crude Selection acts on CDU-1 |
| L8 decision → asset | `GOVERNS` | "Adjust neutraliser rate" governs CDU-1 overhead |
| L8 decision → L10 data element | `CONSUMES` | Crude buy decision consumes LP uplift |
| L10 data element → L10 data point | `INSTANTIATED_BY` | "Overhead water chloride" is measured by tag AI-1021 |

The L10-to-L10 link lets an AI trace any business decision down to a sensor.

## B1.4 Why these levels (and not 8 or 12)

A level earns its place only if it passes all four tests:

1. A different **owner or decision** sits there.
2. A different **system of record** captures data there.
3. **Roll-ups** mean something different there.
4. Engineers at different sites would place the same thing there **consistently**.

- **Fewer levels lose decisions.** Merging subunit and maintainable item blurs "the seal system failed" into "which seal part was replaced", which weakens MTBF, root-cause analysis and spares planning.
- **More levels break consistency.** Train, stage, skid or nozzle don't exist in every plant, so they go into properties, dotted groupings ([B3](B3-relationships-and-dotted-branches.md)) or facets ([B2](B2-backbones-and-facets.md)).
- **L0** gives upstream, midstream, downstream and the process spine one root. **L10** has its own systems of record (historian, LIMS) and is where AI gets its evidence.

## B1.5 Rules

| Rule | Detail |
|---|---|
| H1 Fixed meaning | A level means the same in every site and client. |
| H2 Variable depth | A branch may skip levels (pipeline: L3 → L6; tag on a section: L5 → L10), never reorder them. |
| H3 One solid parent | Every node except L0 has exactly one `PART_OF` parent with a lower level number. |
| H4 Data points attach where measured | A tag's parent is the entity it measures (section, equipment or item). |
| H5 Levels are not hops | The hierarchy depth is not a traversal limit; useful inference is usually 2–4 hops ([C5](C5-ai-access-graphrag.md)). |

Rules H2 and H3 are enforced by SHACL ([C4](C4-reasoning-and-validation.md)) and by the prototype tests `test_levels_strictly_decrease_upwards` and `test_single_parent`.

## B1.6 Coverage in the prototype

| Spine | L0 | L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | L9 | L10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Asset | 1 | 3 | 3 | 4 | 12 | 22 | 21 | 15 | 15 | 12 | 19 |
| Process | (shared) | (shared) | 4 | 9 | 9 | 7 | 7 | 7 | 7 | 7 | 13 |

Counts come from `kg.level_summary()` on the demo data.
