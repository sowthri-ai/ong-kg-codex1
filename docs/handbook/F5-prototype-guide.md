# F5 Prototype guide

The prototype (v0.1) proves the design on synthetic data without any database. Phase 1 moves it onto real stores ([E1](E1-roadmap.md)).

## F5.1 Components

| Module | Purpose |
|---|---|
| `ogkg/ontology.py` | Levels, relations and fact contract used by the prototype (v0.1 subset of `ontology/ogkg-core.ttl`) |
| `ogkg/build_dataset.py` | Builds the synthetic two-refinery dataset → `data/kg.json` |
| `ogkg/kg.py` | Engine: hierarchy, traversal, paths, roll-ups, cited facts, lineage |
| `ogkg/insights.py` | The five reference insights, each returning the insight contract |
| `ogkg/mcp_server.py` | MCP server: 11 tools + the answer contract |
| `ogkg/exports.py` | Turtle, Neo4j CSV + Cypher, explorer HTML |
| `ogkg/turtle_lite.py` | Dependency-free Turtle syntax checker for CI |
| `ogkg/catalogue.py` | Generates [F3](F3-class-and-relation-catalogue.md) from the ontology |
| `ogkg/cdu_gamma.py`, `ogkg/cdu_templates.py` | Builds the Refinery Gamma reference model: CDU trains and equipment templates ([F6](F6-reference-model-refinery-gamma.md)) |
| `ogkg/refinery_units.py`, `ogkg/refinery_gamma.py` | Whole-refinery units, streams, hydrogen and sulfur balances, and the FCC, hydrocracker and coker at full depth |
| `ogkg/ttl_v02.py`, `ogkg/shacl_lite.py` | Sector-split Turtle export in the v0.2 vocabulary, and SHACL-equivalent checks |
| `ogkg/cdu_insights.py`, `ogkg/refinery_insights.py`, `ogkg/cdu_explorer.py` | CDU and refinery-wide insights (8) and the explorer page |
| `explorer/` | Interactive explorer (insights, L0–L10 trees, ask-the-graph) and storage blueprint |
| `tests/` | Integrity, provenance, insight recalculation, handbook claims, Turtle syntax, MCP end-to-end |

## F5.2 Dataset at a glance

| Item | Count |
|---|---|
| Entities | 297 (asset and process spines, 40 material, 50 event, 10 roles) |
| Facts | 220, all with source, as-of date, owner, confidence and method |
| Links | 413 |
| Sites | Refinery Alpha, Refinery Beta, Terminal T1, Field F1 (all fictional) |

## F5.3 Insight contract

Every insight returns the same shape, so any AI or UI can render it:

```json
{
  "id": "true-crude-value",
  "title": "True value of opportunity crudes",
  "question": "...",
  "headline": "LP booked $6.98M uplift ...; the net is -$1.98M.",
  "value_usd": -1977000,
  "domains": ["Trading / CTRM", "LP planning", "..."],
  "rows": [ { "window": "2025-11-10 → 2025-11-24", "net_usd": -670000, "...": "..." } ],
  "path": ["CMP-A1", "CDU-1", "FL-001", "..."],
  "evidence": ["F-00110", "F-00157", "..."],
  "recommendation": "...",
  "decision_owner": "...",
  "caveat": "..."
}
```

## F5.4 Run it

```bash
python -m pip install -r requirements.txt
python -m ogkg.build_dataset
python -m ogkg.exports
python -m ogkg.catalogue
python -m unittest discover -s tests -v
python -m ogkg.mcp_server          # connect any MCP client (config in the README)
```

Open `explorer/og_value_chain_kg.html` and `explorer/storage_blueprint.html` in a browser; both are self-contained.

## F5.5 Known limitations (v0.1)

| Limitation | Resolved by |
|---|---|
| In-memory JSON graph, no database | E1-P1-03 |
| Prototype ontology (`ogkg/ontology.py`) is a subset of `ontology/ogkg-core.ttl` and uses string values for some design data | E1-P1-02 compiler |
| No facet bindings or DNA resolver yet; inherited values aren't labelled | E1-P1-06 |
| Dotted-branch groupings are computed inside insights instead of stored | E1-P1-08 |
| Turtle checked for syntax only; no SHACL engine run | E1-P1-01 |
| `PC-201` has no service temperature fact, so rule R-08 cannot fire on demo data | E1-P1-03 data load |
| Octane value is a low-confidence assumption | Replace with client LP marginal value in Phase 2 |
