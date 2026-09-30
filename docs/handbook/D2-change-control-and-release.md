# D2 Change control and release

## D2.1 Versioning

| Artefact | Scheme | Example | Breaking change means |
|---|---|---|---|
| Ontology | Semantic versioning in `owl:versionInfo` | 0.2.0 | A class or relation removed, renamed or re-parented |
| Named graph | `urn:ogkg:ontology:v<major>.<minor>` | `urn:ogkg:ontology:v0.2` | New major or minor |
| Access-layer tools | Tool schema version | `get_context@1` | Response fields removed or renamed |
| Insights | ID + version | `true-crude-value@1` | Logic change that alters results |
| Dataset (demo) | Tied to repository tag | `v0.2.0` | Fact IDs renumbered |

IRIs never change between versions. Deprecated classes keep their IRI with `owl:deprecated true` and an `rdfs:seeAlso` pointing to the replacement.

## D2.2 Change workflow

```
proposal (issue) → ADR if principle-level → branch onto/… → edit ontology/*.ttl
   → CI: compile LPG schema · export sample RDF · SHACL · unit tests · insight regression
   → change board review → merge → tag release → deploy to runtimes → release notes
```

| Gate | Blocks release when |
|---|---|
| SHACL on sample graph | Any violation in core shapes |
| Insight regression | Any reference insight result changes without an approved note |
| Answer-contract test | Any sampled answer contains an uncited number |
| Backward compatibility | A breaking change is not in the release notes and has no migration script |

## D2.3 Environments

| Environment | Data | Purpose |
|---|---|---|
| `repo` (this repository) | Synthetic only | Design, prototype, tests |
| `dev` (client tenancy) | Masked client sample | Connector build |
| `test` | Client data, restricted | UAT, SME validation |
| `prod` | Client data | Live AI use cases |

## D2.4 Release notes template

```
## ogkg vX.Y.Z — YYYY-MM-DD
Ontology:   added / changed / deprecated classes and relations (with ADR links)
Shapes:     new or tightened constraints; expected conformance impact
Access:     tool changes
Insights:   new / changed insights and result deltas on the reference dataset
Migration:  scripts and steps
```
