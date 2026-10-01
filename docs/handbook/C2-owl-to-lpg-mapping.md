# C2 OWL to property-graph mapping

The compiler reads `ontology/ogkg-core.ttl` and emits the property-graph schema. The authoritative mapping table is [`ontology/mappings/owl-to-lpg.md`](../../ontology/mappings/owl-to-lpg.md); this chapter explains the choices with examples.

## C2.1 Mapping rules

| OWL / RDF construct | Property-graph construct | Example |
|---|---|---|
| `owl:Class` | Node label | `ogkg:ShellAndTubeHX` → `:ShellAndTubeHX` |
| `rdfs:subClassOf` chain | All ancestor labels on the node, **plus** an `IS_A` edge to a class node | `(:Equipment:StaticEquipment:HeatExchanger:ShellAndTubeHX)` and `-[:IS_A]->(:Class {iri:'ogkg:ShellAndTubeHX'})` |
| `owl:ObjectProperty` | Relationship type, upper snake case | `ogkg:directPartOf` → `PART_OF` |
| `owl:DatatypeProperty` | Node property with a declared type and unit | `ogkg:serviceTemperature` → `serviceTemperature: float` (unit in schema metadata) |
| `owl:TransitiveProperty` | Variable-length pattern in queries; optional closure edges | `[:PART_OF*]` |
| `owl:inverseOf` | Not materialised; queries traverse in the other direction | `hasPart` ≡ `<-[:PART_OF]-` |
| `owl:FunctionalProperty` | Uniqueness constraint / SHACL `maxCount 1` | one `PART_OF` per node |
| Annotation `ogkg:dnaChannel`, `ogkg:inheritable` | Resolver metadata used by `get_context` | `serviceTemperature` inherits along lineage |
| Annotation `ogkg:facet` | Facet registry entry | `sealPlan` → design facet |
| Reified `ogkg:Fact` | `(:Fact)` node + `HAS_FACT` edge | see [B5](B5-facts-provenance-and-identity.md) |
| RDF-star statement about a triple | Properties on the edge | `<< E-101B atRiskOf P >> confidence 0.8` → `[:AT_RISK_OF {confidence:0.8}]` |
| `skos:Concept` | `(:Concept)` node; tags as `HAS_TAG` edges | `vocab:HotService` |
| SHACL shape | Validation job (Cypher or pySHACL on the RDF mirror) | `PumpShape` |

## C2.2 Why labels **and** `IS_A` edges

- **Labels** give fast filtering: `MATCH (e:HeatExchanger)`.
- **`IS_A` edges** keep Type DNA queryable and let the class tree change without relabelling millions of nodes. The compiler refreshes labels in a background job after a class-tree change.

## C2.3 Round trip: property graph → RDF

The mirror job writes one named graph per site:

```turtle
alpha:E-101B a ogkg:ShellAndTubeHX ;
    rdfs:label "E-101B Overhead condenser B" ;
    ogkg:directPartOf alpha:CDU-1-OVH ;
    ogkg:tubeMetallurgy vocab:CarbonSteel .
alpha:F-00110 a ogkg:Fact ;
    ogkg:subject alpha:CMP-A1 ; ogkg:predicateKey "lp_uplift_total" ;
    ogkg:value "1890000"^^xsd:decimal ; ogkg:unit unit:USD ;
    ogkg:asOf "2025-11-24"^^xsd:date ; ogkg:confidence vocab:Medium ;
    prov:wasDerivedFrom alpha:F-00107 , alpha:F-00109 .
```

The prototype emits a close variant of this shape (`python -m ogkg.exports` → `exports/og_vckg_data.ttl`), using `ogkg:derivedFrom` (declared as a sub-property of `prov:wasDerivedFrom`) and plain-literal units. Aligning it to QUDT units and SKOS confidence terms is Phase 1 backlog item E1-P1-04.

## C2.4 Compiler outputs (Phase 1 backlog)

| Output | Purpose |
|---|---|
| `schema.cypher` | Constraints and indexes (unique `id`, unique `iri`, indexes on `level`, `cls`) |
| `labels.json` | Class → label set, for ingestion |
| `relationships.json` | Allowed (source label, type, target label) triples, for ingestion checks |
| `facet-registry.json` | Facet → properties, depth, owner, question types ([C5](C5-ai-access-graphrag.md)) |
| `resolver.json` | Inheritance rules per property ([B4](B4-entity-dna-inheritance.md)) |
| Cognite DM YAML (optional) | Spaces, containers and views for Cognite runtimes |

A starter `schema.cypher` is in [`examples/cypher/schema.cypher`](../../examples/cypher/schema.cypher).
