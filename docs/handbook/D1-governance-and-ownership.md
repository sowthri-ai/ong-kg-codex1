# D1 Governance and ownership

## D1.1 Principle

**Owned or it doesn't ship.** Every backbone, facet, fact domain, rule and insight has a named owner. The enforcement mechanisms (SHACL gates, entitlements) are described in [C4](C4-reasoning-and-validation.md) and [C6](C6-security-and-nfr.md).

## D1.2 Ownership map

| Asset | Owner role (client side) | Custodian (delivery side) |
|---|---|---|
| Ontology (core classes, relations) | Enterprise data architect | OGKG ontology lead |
| Asset spine and design facet | Reliability / engineering data owner | Domain modeller |
| Process spine and decision points | Process owners (per L4 process) | Business analyst |
| Application backbone | IT/OT architecture | Solution architect |
| Performance backbone (KPI / KPF) | Performance management lead | Domain modeller |
| Material and economics | Planning & economics | Domain modeller |
| Physics and damage mechanisms | Integrity / corrosion lead | Engineering SME |
| Problems and pattern library | Reliability lead | Reliability SME |
| Each fact domain (e.g. lab results) | System owner (e.g. Laboratory Manager) | Data engineer |
| Rules and their precision | Rule owner named in the rule register | Knowledge engineer |
| Insights | Business owner of the decision the insight informs | Insight developer |
| Access layer and answer contract | AI product owner | Platform engineer |

## D1.3 RACI for key activities

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Change a core class or relation | Ontology lead | Enterprise data architect | Domain owners | All consumers |
| Add a facet or backbone | Domain modeller | Enterprise data architect | Facet owner, AI product owner | Consumers |
| Validate a hypothesis | Named SME | Domain owner | Rule owner | Insight owners |
| Approve a new insight | Insight developer | Business owner of the decision | SMEs, data owners | Users |
| Onboard a source system | Data engineer | System owner | Security, ontology lead | Consumers |
| Release a version | Ontology lead | AI product owner | All owners | All users |

## D1.4 Governance forums

| Forum | Cadence | Decides |
|---|---|---|
| Ontology change board | Fortnightly | Class, relation, facet and vocabulary changes; ADR entries |
| Hypothesis review | Weekly per domain | Validate / reject proposed links; rule precision |
| Data-quality review | Monthly | SHACL conformance trends, freshness breaches, remediation owners |
| Value review | Quarterly | Realised value from decisions that used OGKG; next use cases |

## D1.5 Health metrics

| Metric | Owner | Threshold |
|---|---|---|
| % entities conforming to SHACL | Data owners | ≥ 95% in scope |
| Data elements breaching freshness SLA | Data owners | 0 feeding L8 decisions |
| Hypothesis backlog age | Domain owners | Median < 14 days |
| Rule precision | Rule owners | ≥ 70% or the rule is reviewed |
| Uncited figures in sampled AI answers | AI product owner | 0 |

Thresholds are starting proposals, to be agreed with the client governance lead.
