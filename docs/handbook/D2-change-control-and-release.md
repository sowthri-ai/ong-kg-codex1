# D2 Change control and release

## D2.1 Versioning

| Artefact | Scheme | Example | Breaking change means |
|---|---|---|---|
| Ontology | Semantic versioning in `owl:versionInfo` and `owl:versionIRI` | 1.0.0 | A class or relation removed, renamed or re-parented |
| Named graph | `urn:ogkg:ontology:v<major>.<minor>` | `urn:ogkg:ontology:v1.0` | New major or minor |
| Access-layer tools | Tool schema version | `get_context@1` | Response fields removed or renamed |
| Insights | ID + version | `true-crude-value@1` | Logic change that alters results |
| Dataset (demo) | Tied to repository tag | `v1.0.0` | Fact IDs renumbered |

**Baseline.** 1.0.0 (tag `v1.0.0`, 2026-10-02) is the base version (ADR-0013). Releases before it (0.x) were pre-baseline and carried no compatibility promise. From 1.0.0: **major** = a breaking change as defined above, with a migration note; **minor** = additive classes, relations, data or features; **patch** = fixes, documentation and data corrections that change no schema.

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
