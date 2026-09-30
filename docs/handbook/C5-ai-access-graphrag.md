# C5 AI access and GraphRAG

## C5.1 One door for AI

Every AI solution reads through one access layer, exposed as an **MCP server** (with GraphQL/REST equivalents for non-MCP clients). Models never query databases directly.

| Tool | Returns | Status |
|---|---|---|
| `describe_model` | Levels, relations, standards, dataset notes | Prototype |
| `search_entities` | Entities by text, class, spine or level | Prototype |
| `get_entity` | Entity card: hierarchy path, cited facts, relations, children | Prototype |
| `get_facts` | Cited facts for one entity / predicate | Prototype |
| `get_hierarchy` | Path to L0 or subtree | Prototype |
| `traverse` | One-hop neighbours by relation | Prototype |
| `find_path` | Shortest explainable path between two entities | Prototype |
| `rollup_events` | Failures / exceedances beneath an entity | Prototype |
| `explain_fact` | Lineage tree of a fact | Prototype |
| `list_insights` / `run_insight` | Cross-domain insights with evidence | Prototype |
| **`get_context(entity, intent)`** | Facet-aware context pack (below) | Phase 1 |
| **`query_hypotheses(entity)`** | Proposed / validated hypotheses with evidence | Phase 1 |
| **`federated_read(entity, measure, window)`** | Values fetched live from the source system ([C3](C3-ingestion-and-federation.md)) | Phase 2 |

## C5.2 The answer contract

Sent to every connected AI as server instructions:

1. State a number, date or attribute only if a tool returned it. Never estimate.
2. Cite each figure with its fact ID, source and as-of date.
3. Flag indicative, assumption and low-confidence facts, and label hypotheses as hypotheses.
4. Show lineage for derived figures when asked.
5. If the graph lacks a fact, say so and name the likely system of record.

## C5.3 GraphRAG with facets: the pipeline

| Step | What happens | Driven by |
|---|---|---|
| 1. Resolve entities | Question words → entity IRIs, via names, tags and aliases | Identity crosswalk ([B5](B5-facts-provenance-and-identity.md)) |
| 2. Classify intent | Choose which facets the question needs | Facet registry ([B2](B2-backbones-and-facets.md)) |
| 3. Assemble context pack | Lineage path + selected facets (own / inherited / derived / hypothesis) + 1–3-hop neighbours on facet-relevant edges + cited facts + document chunks filtered by entity and facet | Resolver ([B4](B4-entity-dna-inheritance.md)) |
| 4. Broad questions | Use pre-computed **facet summaries** per level ("Problems summary: CDU-1") instead of raw nodes | Summary job |
| 5. Answer | Model writes the answer under the answer contract | Answer contract |
| 6. Write back | Decision and outcome recorded on the L8 decision node | Adoption tracking |

**Intent → facets**

| Question type | Facets |
|---|---|
| Why is it failing? | Design, physics, flow, problems |
| What is it worth? | Economics, performance |
| Who decides / who owns it? | Process, enterprise |
| Where does this number come from? | Application, lineage |
| What changed recently? | Problems, flow, performance (time-filtered) |

## C5.4 Example context pack

```yaml
entity:   P-201A-SF (L9 Seal faces)
lineage:  Oil & Gas › Downstream › Refining › Refinery Alpha › VDU-1 › Vacuum resid system
          › P-201A › Seal system › Mechanical seal
intent:   why_failing
facets:
  design:
    - model: HX-300 (OEM-A)            status: inherited (P-201A)      cite: F-…
    - seal_plan: API 682 Plan 32       status: inherited (P-201A)      cite: F-…
  flow:
    - service: vacuum residue, 365 °C  status: inherited (VDU-1-VR)    cite: F-…
    - exposure: Doba campaign, TAN 4.5 status: exposure (Feb 2026)     cite: F-00097
  problems:
    - 4 seal failures in 12 months     status: own                     cite: F-…
    - pattern: HX-300 hot service      status: hypothesis (validated)
  performance:
    - MTBF 91 days vs 104 group avg    status: derived
documents:
  - chunk: "Seal plan 53B selection guide §4" tagged [P-201A, design]
```

`F-00097` is Doba's TAN fact in the demo data.

## C5.5 Traversal budget

- Useful inference paths are usually **2–4 hops**. With about 10 links per node, 4 blind hops reach about 10,000 nodes.
- Context packs therefore expand only along facet-relevant edge types, with a token budget per facet.
- Detail priority: own facts in full, inherited facts summarised, hypotheses with status and confidence.
