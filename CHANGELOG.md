# Changelog

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
