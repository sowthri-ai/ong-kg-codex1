# OWL → property-graph mapping (authoritative)

Input: `ontology/ogkg-core.ttl` (+ `ogkg-vocab.ttl`, `ogkg-reference.ttl`).
Output: see handbook [C2.4](../../docs/handbook/C2-owl-to-lpg-mapping.md#c24-compiler-outputs-phase-1-backlog).

## 1. Naming

| OWL | LPG | Rule |
|---|---|---|
| Class `ogkg:ShellAndTubeHX` | Label `ShellAndTubeHX` | Local name, PascalCase, unchanged |
| Object property `ogkg:partOf` | Relationship `PART_OF` | Use `ogkg:lpgType` annotation; else local name → UPPER_SNAKE |
| Datatype property `ogkg:serviceTemperature` | Property `serviceTemperature` | Local name, camelCase |
| Individual IRI | Node property `iri` (unique) + `id` (local, unique per site) | IRI never changes |
| `skos:Concept` | Node `:Concept {iri, prefLabel, scheme}` | Tags via `HAS_TAG` |

## 2. Structure

| OWL construct | LPG construct |
|---|---|
| `rdfs:subClassOf` | All ancestor labels on each instance node + `(:Class)` nodes linked by `SUBCLASS_OF`; instance `-[:IS_A]->(:Class)` for its most specific class |
| `owl:TransitiveProperty` | Not materialised; queries use `[:TYPE*]`. Optional closure cache for `PART_OF` depth > 6 |
| `owl:SymmetricProperty` | Stored once; queries ignore direction |
| `owl:inverseOf` | Not stored; traverse in reverse |
| `owl:FunctionalProperty` | Cardinality check in the ingestion validator |
| `rdfs:domain` / `rdfs:range` | Allowed (source label, type, target label) triple in `relationships.json`; ingestion rejects others |
| `ogkg:Fact` | `(:Fact {id, predicateKey, value, unit, asOf, sourceSystemName, sourceRef, confidence, method})`, with `(subject)-[:HAS_FACT]->(:Fact)` and `(:Fact)-[:DERIVED_FROM]->(:Fact)`; latest value cached on the subject as `<predicateKey>` |
| `ogkg:HypothesisAssertion` | Edge `(s)-[:<PREDICATE> {status, confidence, inferredBy, runId, evidence, reviewedBy, reviewedOn}]->(o)` |
| `ogkg:FacetBinding` | Edge `(entity)-[:<BINDING TYPE> {facet, level, validFrom, validTo, inheritanceRule, scope}]->(backboneNode)` |
| Annotations `ogkg:facet`, `ogkg:dnaChannel`, `ogkg:inheritable`, `ogkg:overridable` | Entries in `facet-registry.json` and `resolver.json` |
| `ogkg:levelNumber` on a class | Property `level` on each instance (integer) |

## 3. Reverse mapping (LPG → RDF mirror)

| LPG | RDF |
|---|---|
| Node with labels | `<iri> a <most specific class>` (others inferred) |
| Edge | `<s> ogkg:<camelCase of type> <o>` |
| Edge properties (hypothesis) | `ogkg:HypothesisAssertion` node (portable) or RDF-star annotation where supported |
| `(:Fact)` | `ogkg:Fact` resource with the same fields; `ogkg:derivedFrom` for lineage |
| Cached latest values | Not mirrored (the Fact is the source of truth) |

## 4. Worked example

```turtle
# OWL + instance
alpha:E-101B a ogkg:ShellAndTubeHX ; rdfs:label "E-101B Overhead condenser B" ;
    ogkg:partOf alpha:CDU-1-OVH ; ogkg:hasLevel ogkg:L6 ; ogkg:tubeMetallurgy vocab:CarbonSteel .
```

```cypher
// compiled property graph
MERGE (e:Entity:AssetSpineNode:EquipmentUnit:StaticEquipment:HeatExchanger:ShellAndTubeHX
       {iri:'https://example.org/ogkg/data/alpha#E-101B'})
  SET e.id = 'E-101B', e.name = 'E-101B Overhead condenser B', e.level = 6
MERGE (s {iri:'https://example.org/ogkg/data/alpha#CDU-1-OVH'})
MERGE (e)-[:PART_OF]->(s)
MERGE (c:Concept {iri:'https://example.org/ogkg/vocab#CarbonSteel'})
MERGE (e)-[:HAS_TUBE_METALLURGY]->(c)
MERGE (k:Class {iri:'https://example.org/ogkg/core#ShellAndTubeHX'})
MERGE (e)-[:IS_A]->(k)
```
