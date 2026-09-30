# F2 Standards catalogue

Standards are referenced by name and scope only. No licensed text or tables are reproduced ([D3](D3-ip-confidentiality-responsible-ai.md)).

| Standard | Publisher | Used for in OGKG | Where |
|---|---|---|---|
| ISO 14224 | ISO | Asset taxonomy levels 1–9, equipment classes, failure modes and mechanisms | Asset spine, problems backbone |
| ISO 15926 | ISO | Lifecycle integration of process-plant data; reference data concepts | Type & design backbone |
| CFIHOS | IOGP / JIP36 | Standard classes and property lists for handover data | Design facet, EPC ingestion |
| DEXPI | DEXPI initiative | P&ID data exchange and plant topology | Topology ingestion |
| ISA-95 (IEC 62264) | ISA / IEC | Enterprise–control integration; functional model for applications | Application backbone |
| ISO 22400 | ISO | KPI definitions for manufacturing operations management | Performance backbone |
| API 571 | API | Damage mechanisms affecting fixed equipment in refining | Physics backbone, problem patterns |
| API 584 | API | Integrity operating windows | IOW data points, rules |
| API 580 / 581 | API | Risk-based inspection | Corrosion loops, inspection facts |
| API 570 | API | Piping inspection; circuits | Dotted-branch groupings |
| API 610 / 682 | API | Centrifugal pumps; shaft seals and seal plans | Type & design facet |
| TEMA | TEMA | Shell-and-tube exchanger construction classes | Type & design facet |
| ASME BPVC Section VIII | ASME | Pressure-vessel design | Type & design facet |
| ArchiMate | The Open Group | Application and business-process modelling | Application backbone |
| OSDU | The Open Group OSDU Forum | Upstream data-platform alignment | Upstream extension |
| BFO (ISO/IEC 21838-2) / IOF Core | ISO / Industrial Ontologies Foundry | Upper ontology: things, processes, qualities, roles, information | Top of `ogkg-core.ttl` |
| OWL 2, RDF, RDFS | W3C | Ontology and data model | `ontology/` |
| SHACL | W3C | Validation | `ogkg-shapes.ttl` |
| SKOS | W3C | Vocabularies and tags | `ogkg-vocab.ttl` |
| PROV-O | W3C | Provenance and lineage | Fact model |
| QUDT | QUDT.org | Units of measure | Fact units |
| OWL-Time | W3C | Dates, intervals, validity | Bindings, exposure windows |
| GeoSPARQL | OGC | Locations and geometry | Location backbone |
| W3C ORG | W3C | Organisations and roles | Enterprise backbone |
| GQL (ISO/IEC 39075) | ISO / IEC | Property-graph query language | LPG runtime |
| SPARQL 1.1 | W3C | RDF query and federation | Triplestore |
| Model Context Protocol | Open specification | AI tool access | Access layer |
