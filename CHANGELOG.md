# Changelog

## 0.3.0 — 2026-09-30 (reference model)
- Refinery Gamma CDU reference model: 500 kbpd, two 250 kbpd trains, common facilities and tank farm; 157 equipment items decomposed L6-L9, 950 tags, process spine with 7 decision chains, 25 groupings, 3,293 cited facts, 12-month event history.
- CDU ontology extension (`ontology/ext/ogkg-cdu.ttl`), new metallurgy and seal-plan vocabulary terms.
- Sector-split Turtle export in the v0.2 vocabulary (`ogkg/ttl_v02.py`) and SHACL-equivalent checks (`ogkg/shacl_lite.py`): 0 violations.
- Three CDU insights, explorer page, equipment and tag registers; MCP server serves the model with `OGKG_DATASET=gamma`.
- Turtle checker is now linear-time; 52 tests.

## 0.2.0 — 2026-09-30 (design)
- Ontology v0.2 specified in OWL, SHACL and SKOS (`ontology/`): backbones, facets, DNA channels, problems, hypothesis edges, facts.
- MECE handbook (Parts A–F) and architecture decision log.
- Three-store architecture (OWL master, property-graph runtime, triplestore for reasoning and exchange).
- Storage blueprint page and SPARQL / Cypher examples.
- `ogkg/turtle_lite.py` Turtle checker and `ogkg/catalogue.py` (F3 generated from the ontology).
- 31 tests: ontology syntax and declared-term checks, handbook claims recomputed from data, link and anchor checks.

## 0.1.0 — 2026-09-29 (prototype)
- Synthetic two-refinery dataset: 297 entities, 220 facts, 413 links.
- Five cross-domain insights, MCP server with 11 tools and an answer contract.
- Turtle and Neo4j exports, interactive explorer, 17 tests.
