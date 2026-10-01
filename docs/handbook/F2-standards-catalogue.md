# F2 Standards catalogue

Standards are referenced by name and scope only. No licensed text or tables are reproduced ([D3](D3-ip-confidentiality-responsible-ai.md)). How each standard is aligned and checked is in [B7](B7-standards-conformance.md).

| Standard | Publisher | Used for in OGKG | Where |
|---|---|---|---|
| ISO 14224 | ISO | Asset taxonomy levels 1–9, equipment class codes, equipment boundary, failure and maintenance records (modes, mechanisms, causes, detection methods) | Asset spine, problems backbone; `ontology/alignments/iso14224.ttl` |
| ISO 15926-14 (LIS-14) | ISO / POSC Caesar | OWL profile of ISO 15926: functional vs physical objects, systems, activities, streams, information objects | `ontology/alignments/iso15926-14.ttl` |
| CFIHOS | IOGP / JIP36 | Tag / equipment / model-part data model; standard classes and property lists for handover data | Design facet, EPC ingestion; `ontology/alignments/cfihos.ttl` |
| DEXPI | DEXPI initiative | P&ID data exchange and plant topology | Topology ingestion |
| ISA-95 (IEC 62264) | ISA / IEC | Role-based equipment hierarchy; functional levels and MOM activity models | Asset spine, process spine, application backbone; `ontology/alignments/isa95-purdue.ttl` |
| Purdue reference model / IEC 62443 | ISA / IEC | Levels 0–5 of systems and devices; security zones | Application backbone, [C6](C6-security-and-nfr.md) |
| MIMOSA OpenO&M CCOM | MIMOSA | O&M exchange model: Segment, Asset, Model, MeasurementLocation, Measurement, Event, WorkOrder | Exchange profile; `ontology/alignments/mimosa-ccom.ttl` |
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
| BFO (ISO/IEC 21838-2) / IOF Core and Maintenance | ISO / Industrial Ontologies Foundry | Upper ontology; failure events, failure-mode codes, work-order records, maintenance processes | `ontology/alignments/iof-bfo.ttl` |
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
