# A1 Objective and value thesis

## A1.1 The problem

Downstream operators run dozens of systems: historian, CMMS, LIMS, LP planning, scheduling, trading, inspection and document stores. Each holds part of the truth. Every AI initiative then hits the same three walls:

| Wall | What happens today | Consequence |
|---|---|---|
| **Context is rebuilt every time** | Each pilot re-maps the asset hierarchy, tag meanings and KPI definitions | 30–60% of pilot effort goes on data plumbing, and nothing is reused |
| **Numbers are not grounded** | Language models recall or estimate figures | Plausible but wrong answers, and users stop trusting the tool |
| **Silos hide the money** | Trading sees crude margin; reliability sees failures; nobody sees both | Decisions optimise one domain at the expense of another |

The 30–60% range is an experience-based planning assumption, not a measured benchmark. Replace it with the client's own pilot data during Phase 2.

## A1.2 The objective

> **One governed knowledge layer for the O&G value chain that every AI solution uses for its facts, and that reveals insights no single system can.**

Three commitments follow from that sentence:

1. **One layer.** The same model serves copilots, agents, optimisers and analytics. There are no per-use-case graphs.
2. **Governed facts.** Every number has a source, date, owner, confidence and lineage (see [B5](B5-facts-provenance-and-identity.md)).
3. **Discovery.** The graph joins domains and proposes links for experts to validate (see [B6](B6-problems-and-hypotheses.md)).

## A1.3 Value thesis

| Value lever | Mechanism | Example on demo data |
|---|---|---|
| **Better commercial decisions** | Joins trading, LP, integrity and maintenance economics | Opportunity crudes: LP says +$6.98M; true net −$1.98M |
| **Less margin leakage** | Traces quality giveaway to asset and data causes | Octane giveaway ≈ $5.3M/yr at Alpha |
| **Higher availability** | Fleet-level bad-actor detection across sites | One pump model in hot service: MTBF ≈ 104 days vs 365 days for the alternative |
| **Safer turnarounds** | Links live integrity threats to TA scope before freeze | 4 exposed items missing from scope |
| **Better decisions overall** | Shows which decisions ignore data the organisation already holds | 4 of 7 decision points have blind spots |
| **Cheaper AI delivery** | Reuse of ontology, connectors and access layer | Target: ≥ 70% reuse from the second use case |

All dollar figures above come from synthetic demo data and illustrate the mechanism only. A client value case must be rebuilt from client data in Phase 2 (see [E1](E1-roadmap.md)).

## A1.4 What OGKG is not

| Not this | Because |
|---|---|
| A data lake or historian replacement | Time series stays at source; the graph federates (see [C3](C3-ingestion-and-federation.md)) |
| A single vendor platform | The ontology is platform-neutral and compiles to several runtimes (see [C1](C1-three-store-architecture.md)) |
| A chatbot | It is the layer chatbots and agents stand on |
| A one-off consulting model | It is designed as a reusable accelerator with versioned releases (see [D2](D2-change-control-and-release.md)) |

## A1.5 Success measures

| Measure | Target | Measured by |
|---|---|---|
| Grounded answers | 100% of figures cited with a fact ID | Answer-contract tests in UAT |
| Validated insights | ≥ 3 per pilot site, confirmed by client SMEs | Hypothesis review log |
| Adoption | Named users making at least one decision per week with an OGKG-grounded answer | Access-layer telemetry + decision log |
| Realised value | Value tracked against the decisions that used OGKG | Write-back of outcomes to L8 decision nodes |
| Reuse | ≥ 70% of layer reused by the second use case | Component inventory per release |
| Data quality | ≥ 95% of in-scope entities pass SHACL completeness | Nightly validation report |

The reuse and data-quality targets are proposals to be confirmed with the Executive Director before Phase 2.
