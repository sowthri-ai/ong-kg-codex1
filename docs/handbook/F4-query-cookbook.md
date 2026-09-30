# F4 Query cookbook

Ready-to-run queries, grouped by the question they answer. The files are in [`examples/`](../../examples/). Cypher examples assume the compiled schema ([C2](C2-owl-to-lpg-mapping.md)), with latest fact values cached as node properties.

| # | Question | Store | File | Expected on demo data |
|---|---|---|---|---|
| Q1 | List every heat exchanger at Refinery Alpha | Triplestore | [`sparql/inference-heat-exchangers.rq`](../../examples/sparql/inference-heat-exchangers.rq) | E-101A, E-101B, E-301 |
| Q2 | Which equipment is at risk from high-salt crude? (rule R-07) | Triplestore | [`sparql/rule-r07-overhead-chloride.rq`](../../examples/sparql/rule-r07-overhead-chloride.rq) | E-101A, E-101B (not E-401A: titanium) |
| Q3 | Which hot circuits are susceptible to naphthenic acid? (rule R-08) | Triplestore | [`sparql/rule-r08-naphthenic-acid.rq`](../../examples/sparql/rule-r08-naphthenic-acid.rq) | PC-201 once `serviceTemperature` is loaded for it (backlog E1-P1-03) |
| Q4 | Which pumps are incomplete for AI reasoning? | Triplestore | [`sparql/shacl-gap-pumps.rq`](../../examples/sparql/shacl-gap-pumps.rq) | P-103 (3 gaps) |
| Q5 | Query a partner's assays in place | Triplestore | [`sparql/federated-partner-assay.rq`](../../examples/sparql/federated-partner-assay.rq) | Requires a partner endpoint |
| Q6 | Recompute inferences for a new run | Triplestore | [`sparql/recompute-inferred.ru`](../../examples/sparql/recompute-inferred.ru) | Drops and refills the inferred graph |
| Q7 | Create constraints and indexes | Property graph | [`cypher/schema.cypher`](../../examples/cypher/schema.cypher) | — |
| Q8 | Did opportunity crudes cause corrosion failures? | Property graph | [`cypher/true-crude-value.cypher`](../../examples/cypher/true-crude-value.cypher) | FL-001 … FL-004 against three campaign windows |
| Q9 | Write rule results back as hypotheses | Property graph | [`cypher/hypothesis-writeback.cypher`](../../examples/cypher/hypothesis-writeback.cypher) | Two `AT_RISK_OF` edges, status proposed |
| Q10 | Which pumps share a failed pump's DNA? | Property graph | [`cypher/fleet-dna-similarity.cypher`](../../examples/cypher/fleet-dna-similarity.cypher) | For P-201A: P-201B, P-501, P-401A |
| Q11 | Which decisions ignore reliability data? | Property graph | [`cypher/decision-blind-spots.cypher`](../../examples/cypher/decision-blind-spots.cypher) | DEC-CRACC, DEC-CRBUY |

## Prototype equivalents (no database needed)

Every question above has a Python equivalent in the prototype engine, so it can be demonstrated without installing a store:

```python
from ogkg.kg import KG
from ogkg import insights
kg = KG()
kg.find_path("CR-HSOB", "DEC-CRBUY")        # explainable path across spines
kg.rollup("CDU-1")                          # failures beneath CDU-1
insights.run(kg, "true-crude-value")        # insight 1 with evidence fact IDs
kg.explain_fact("F-00157")                  # lineage of a lost-margin figure
```

## Patterns to reuse

| Pattern | SPARQL | Cypher |
|---|---|---|
| Everything under a node | `?x ogkg:partOf+ alpha:CDU-1` | `(x)-[:PART_OF*]->(:Entity {id:'CDU-1'})` |
| Everything of a kind | `?x a/rdfs:subClassOf* ogkg:Pump` | `(x:Pump)` (labels compiled from the class tree) |
| One hop downstream in material flow | `?u0 ogkg:produces/ogkg:feeds ?u1` | `(u0)-[:PRODUCES]->()-[:FEEDS]->(u1)` |
| Facts with provenance | `?f ogkg:subject ?x ; ogkg:asOf ?d` | `(x)-[:HAS_FACT]->(f:Fact)` |
| Only validated hypotheses | via `ogkg:HypothesisAssertion` + `ogkg:status vocab:Validated` | `[h:AT_RISK_OF {status:'validated'}]` |
