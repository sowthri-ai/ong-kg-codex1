# Changelog

## Unreleased

## 1.0.0 — 2026-10-02 (base version)
OGKG 1.0.0 is the baseline release. From here, changes follow semantic versioning ([D2](docs/handbook/D2-change-control-and-release.md), ADR-0013): every later version is described as a change against 1.0.0.

What 1.0.0 contains:
- **Ontology 1.0.0:** dual L0–L10 spine; functional locations separate from physical items; asserted `directPartOf` with transitive `partOf`; disjoint upper partition; every class and relation used by the data declared with domain and range; version IRIs and XML catalog for all modules; OWL 2 DL (checked).
- **Standards:** alignment modules for ISO 15926-14, IOF / BFO, ISO 14224, ISA-95 / Purdue, CFIHOS and MIMOSA CCOM; 40 automated conformance checks (handbook B7).
- **Reference model:** Refinery Gamma, 39 units, NCI ≈ 15, full L6–L10 depth for CDU, FCC, hydrocracker and coker; 8,299 nodes, 10,896 edges, 12,570 bitemporal facts with provenance; independent meter balances with residuals; integrity (IOW limits, damage mechanisms, RBI, TMLs, PSVs, SIFs); economics (prices, assays, LP, CO2, margins); failure history coded to ISO 14224.
- **Insights:** 11 refinery insights with value basis and range, degrading gracefully on missing data.
- **Validation:** SHACL-equivalent shapes incl. domain / range, OWL 2 DL profile check, conformance report; 116 tests.
- **Views:** refinery explorer and the L0–L10 hierarchy page.

Known limitations carried into 1.x (council issues still open): access-layer security, audit, freshness and answer verification; onboarding connectors and entity resolution; QUDT unit mapping and named graphs; rdflib / pySHACL / reasoner runs in CI; code tables still to confirm against licensed copies (ISO 14224, CFIHOS RDL, CCOM XSD).

Changes since 0.4.0 that make up this release:
- v0.5 data contract and identity module; data layer (independent balances, mass basis, networks, integrity, economics, time model, identity); insights degrade gracefully on missing data.
- Hierarchy page `explorer/refinery_gamma_hierarchy.html` (`python -m ogkg.hierarchy_view`): the whole L0–L10 asset and process hierarchy with a level ladder, each node's ISO 14224 / ISA-95 / Purdue / CCOM / CFIHOS / ISO 15926-14 / IOF placement resolved from the alignment modules, links beyond the hierarchy and latest cited facts. A test keeps the committed page in sync with the graph.
- Standards alignment and conformance (ADR-0012, handbook B7): functional locations separated from physical items (`ogkg:FunctionalLocation`, disjoint from `ogkg:PhysicalAsset`); asserted hierarchy is `ogkg:directPartOf`; 16 relations and 19 classes declared with domain and range; upper partition made disjoint; version IRIs and an XML catalog for all modules.
- Six alignment modules in `ontology/alignments/`: ISO 15926-14 (LIS-14), IOF Core + Maintenance / BFO, ISO 14224, ISA-95 / Purdue, CFIHOS, MIMOSA CCOM, each external identifier with a verification status.
- `ogkg/owl_profile.py` (OWL 2 DL structural checker), `ogkg/standards.py` (resolves codes from the alignment modules; sets Purdue levels and ISA-95 functions), `ogkg/conformance.py` (40 checks across 8 standards; report in `data/cdu-gamma/conformance.md`); `shacl_lite` adds ISO 14224 failure-record, serial-item, Purdue and ISA-95 shapes and a generic domain / range check; facts export valid-from, recorded-at (PROV), status, supersedes, sensitivity and value range.
- Council review of v0.4.0 (`docs/reviews/2026-10-01-council-review.md`): 69 findings from six reviewer seats, re-verified and merged into 33 issues on a MECE tree (6 layers × Wrong / Missing), each with one priority (Now / Next / Then).

## 0.4.0 — 2026-10-01 (whole refinery)
- Refinery Gamma extended from the CDU to the whole refinery (Nelson complexity 15.0, 1998 factors): 36 real units replace the out-of-scope placeholders, each with sections, capacity, feed rate, utilisation, Nelson factor and NCI contribution.
- Full L0–L10 depth for FCC-1, HCU-1 and DCU-1: 104 more equipment items, 13 new equipment templates (reactors, FCC reactor/regenerator, slide valves, compressors, expander, waste-heat boiler, coke drums, decoking, crusher).
- Refinery stream network (76 streams) with FY2026 rates; hydrogen network and sulfur balance that close by construction; conversion-unit KPIs with lineage.
- 15 new groupings (REAC NH4HS and HTHA loops, compressor fleet, 3 SIFs, hydrogen and sulfur networks), 7 new decision chains (planning, hydrogen, sulfur, FCC, HCU, coker, compressors), conversion-unit IOW limits and a year of events.
- Five refinery insights (`ogkg/refinery_insights.py`): hydrogen headroom and reformer-outage exposure, SRU-limited crude sulfur ceiling, conversion-unit loss chains with precursor signals, reformer bottleneck, Nelson complexity from the graph.
- Ontology extension 0.4.0: unit, section and equipment classes, `nelsonFactor`, `modelDepth`; new metallurgy terms. ADR-0011 (model depth follows the decision).
- Explorer renamed `explorer/refinery_gamma_kg.html`; handbook F6 rewritten for the whole refinery; 67 tests.

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
