# C4 Reasoning and validation

## C4.1 Reasoning profile

Keep the ontology practical, at roughly the **OWL 2 RL** level of complexity: class hierarchies, transitive and inverse properties, domains and ranges. Full OWL-DL reasoning over millions of plant entities isn't needed and doesn't scale. Domain logic lives in **rules** (SPARQL CONSTRUCT or SHACL-AF), and completeness lives in **SHACL shapes**.

| Mechanism | Used for | Runs in |
|---|---|---|
| RDFS / OWL-RL entailment | Class membership, transitive part-of | Triplestore |
| SPARQL property paths | The same, without a reasoner | Triplestore |
| Rules (CONSTRUCT) | Susceptibility, at-risk, pattern matching | Triplestore → hypothesis edges in LPG |
| SHACL shapes | Completeness, cardinality, datatypes, units | Triplestore (pySHACL / engine) and ingestion gate |
| Graph algorithms | Similarity, centrality, communities, link prediction | LPG |

## C4.2 Example: inference

"List every heat exchanger at Refinery Alpha." No statement says E-101B is a heat exchanger or part of the site.

```sparql
SELECT ?eq WHERE {
  ?eq a/rdfs:subClassOf* ogkg:HeatExchanger ;
      ogkg:directPartOf+ alpha:SITE-ALPHA .   # ogkg:partOf with reasoning
}
```

Returns E-101A, E-101B, E-301. File: [`examples/sparql/inference-heat-exchangers.rq`](../../examples/sparql/inference-heat-exchangers.rq).

## C4.3 Example: rule R-07 creates hypotheses

```sparql
CONSTRUCT { ?eq ogkg:atRiskOf pattern:OverheadChlorideCorrosion . }
WHERE {
  ?camp ogkg:ofGrade ?g ; ogkg:processedIn ?unit .
  ?g    ogkg:saltContent ?salt .  FILTER(?salt > 20)
  ?sec  ogkg:directPartOf ?unit ; a ogkg:OverheadSystem .
  ?eq   ogkg:directPartOf ?sec ; ogkg:tubeMetallurgy vocab:CarbonSteel .
}
```

The result (E-101A, E-101B) is written to the LPG as `AT_RISK_OF` edges with `status='proposed'` ([B6](B6-problems-and-hypotheses.md)). File: [`examples/sparql/rule-r07-overhead-chloride.rq`](../../examples/sparql/rule-r07-overhead-chloride.rq).

## C4.4 Rule register

| ID | Rule | Output | Owner | Status |
|---|---|---|---|---|
| R-07 | High-salt crude + carbon-steel overhead ⇒ at risk of overhead chloride corrosion | `AT_RISK_OF` | Corrosion engineer | Specified |
| R-08 | TAN > 0.5 crude reaching a hot (> 220 °C) circuit not in Mo-bearing stainless (e.g. 316 / 317L) ⇒ susceptible to naphthenic acid corrosion | `SUSCEPTIBLE_TO` | Corrosion engineer | Specified |
| R-12 | Pump model + service band matches a validated failure pattern ⇒ at risk | `AT_RISK_OF` | Fleet reliability engineer | Specified |
| R-20 | Data element sampling interval > freshness SLA ⇒ stale input to decision | `STALE_INPUT_TO` | Data owner | Implemented (prototype insight 5) |
| R-21 | Decision governs assets with corrosion failures but consumes no reliability data ⇒ blind spot | `BLIND_SPOT` | Process owner | Implemented (prototype insight 5) |

Thresholds are illustrative until confirmed by client SMEs. Each rule's precision is tracked (validated ÷ reviewed).

## C4.5 SHACL shapes

The shapes live in [`ontology/ogkg-shapes.ttl`](../../ontology/ogkg-shapes.ttl).

| Shape | Target | Key constraints |
|---|---|---|
| `SpineNodeShape` | Asset and process spine nodes | exactly one `directPartOf` (except L0); `hasLevel` present |
| `EquipmentUnitShape` | `EquipmentUnit` | parent is a section or unit; `eqClass` present |
| `PumpShape` | `Pump` | `model`, `sealPlan`, `serviceTemperature` (decimal) |
| `FactShape` | `Fact` | subject, predicate, value, asOf, sourceSystem, owner, confidence, method |
| `KPIShape` | `KPI` | formula, unit, owner, aggregation rule, applicable levels |
| `ApplicationInstanceShape` | `ApplicationInstance` | `instanceOf`, `scopedTo` |
| `HypothesisShape` | `HypothesisAssertion` | status, confidence 0–1, inferredBy, runId |
| `FacetBindingShape` | `FacetBinding` | entity, target, level, validFrom |
| `DataElementShape` | `DataElement` | owner; either `instantiatedBy` or `mapsToPredicate` |

**Example result on the prototype:** `PumpShape` flags **P-103** (missing model, seal plan and service temperature). Without the shape, P-103 silently drops out of the bad-actor analysis.

## C4.6 When validation runs

| Trigger | Scope | On failure |
|---|---|---|
| Ingestion | Affected staging graph | Record goes to the data-quality queue; not promoted |
| Nightly | All in-scope data | Report to data owners; KPI "% conforming" tracked ([A1](A1-objective-and-value.md)) |
| Ontology release | Sample graph + all shapes | Release blocked ([D2](D2-change-control-and-release.md)) |
| Before an insight runs | Entities the insight reads | Insight returns a completeness warning with its result |
