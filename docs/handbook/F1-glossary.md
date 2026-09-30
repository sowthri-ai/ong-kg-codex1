# F1 Glossary

| Term | Meaning in OGKG |
|---|---|
| **Answer contract** | Rules every connected AI must follow: cite or don't state, flag low confidence, label hypotheses ([C5](C5-ai-access-graphrag.md)) |
| **Backbone** | A taxonomy with its own levels (location, application, performance, …) that spine entities bind to ([B2](B2-backbones-and-facets.md)) |
| **Binding** | An edge from an entity to a backbone node, carrying level, scope, validity and inheritance rule |
| **Context pack** | Facet-aware bundle of lineage, facts, neighbours and document chunks returned by `get_context` |
| **Data element (L10, process)** | A business data item a decision uses, e.g. "salt content" |
| **Data point (L10, asset)** | A measured or recorded value source: tag, lab result, KPI value |
| **Decision point (L8, process)** | Where someone commits to a choice, e.g. "buy / reject opportunity cargo" |
| **DNA** | Traits an entity inherits through lineage, type or exposure channels ([B4](B4-entity-dna-inheritance.md)) |
| **Dotted branch** | A `MEMBER_OF` link to a typed grouping (fleet, corrosion loop, utility) ([B3](B3-relationships-and-dotted-branches.md)) |
| **Exposure DNA** | Traits inherited from material that flowed through an asset during a time window |
| **Facet** | The set of bindings between one entity and one backbone |
| **Facet registry** | Catalogue of facets: depth, owner, question types served |
| **Fact** | A cited value with source, as-of date, owner, confidence, method and lineage ([B5](B5-facts-provenance-and-identity.md)) |
| **Federation** | Reading from a source system on demand instead of copying its data ([C3](C3-ingestion-and-federation.md)) |
| **GraphRAG** | Retrieval-augmented generation that uses graph structure (entities, paths, facets) as well as text chunks |
| **Hypothesis edge** | A proposed link with status, confidence, method and evidence; never a fact until validated ([B6](B6-problems-and-hypotheses.md)) |
| **IOW** | Integrity operating window (API 584): limits on process variables that protect equipment integrity |
| **IRI** | Internationalised resource identifier; the global ID shared by all stores |
| **KPF** | Key performance factor: a controllable lever that drives a KPI |
| **KPI** | Key performance indicator: a metric chosen to track performance against a target |
| **Lens** | A saved facet selection for a persona (reliability, economics, IT/OT) |
| **Lineage DNA** | Traits inherited along `PART_OF` from ancestors |
| **LPG** | Labelled property graph: nodes and edges with labels and properties |
| **MCP** | Model Context Protocol; the standard interface AI applications use to call OGKG tools |
| **MECE** | Mutually exclusive, collectively exhaustive |
| **Metric** | Any measured or calculated number (an L10 fact) |
| **Named graph** | A labelled subset of triples in a triplestore, used for lifecycle and provenance |
| **OWL** | Web Ontology Language; the formal definition of OGKG classes and relations |
| **Problem pattern** | A class-level problem signature that incidents are matched against |
| **RDF** | Resource Description Framework; data as subject–predicate–object triples |
| **SHACL** | Shapes Constraint Language; validates RDF data against rules |
| **SKOS** | Simple Knowledge Organization System; controlled vocabularies and tags |
| **Spine** | One of the two L0–L10 hierarchies: asset or process |
| **Triplestore** | A database for RDF with SPARQL querying and, often, reasoning |
| **Type DNA** | Traits inherited from an entity's class, model and design |
