# OGKG Handbook

The complete reference for the Oil & Gas Value Chain Knowledge Graph: why it exists, what the model is, how it is built, how it is run and how it is delivered.

## How the handbook is organised (MECE)

The six parts answer six separate questions. Together they cover the whole plan, and each topic lives in exactly one chapter; other chapters link to it rather than repeat it.

| Part | Question it answers | Audience |
|---|---|---|
| **A. Why** | What outcome does OGKG change, and for whom? | Executives, sponsors, pursuit teams |
| **B. What (the model)** | What is modelled, and how do entities connect? | Architects, ontologists, domain SMEs |
| **C. How it is built** | Which stores, pipelines and interfaces implement the model? | Engineers, platform teams |
| **D. How it is run** | Who owns it, how does it change, and how is it kept safe? | Data owners, governance leads |
| **E. How it is delivered** | In what phases, with which team, risks and commercial model? | Delivery leads, AD / partner |
| **F. Reference** | Terms, standards, catalogues, queries and the prototype | Everyone |

**Boundary rules that keep it MECE**
- Part B defines concepts; Part C says where and how they are stored and served. The same concept is never defined in both.
- Part C is technology; Part D is people and process. A control appears in D, and the mechanism that enforces it appears in C.
- Part E is time-bound (phases, staffing, risks); A–D stay true across phases.
- Part F holds only lookup material (glossaries, catalogues, cookbooks). It introduces no new design.

## Contents

### Part A — Why
- [A1 Objective and value thesis](A1-objective-and-value.md)
- [A2 Use cases, personas and insights](A2-use-cases-and-personas.md)

### Part B — What (the model)
- [B1 The L0–L10 hierarchy](B1-hierarchy-L0-L10.md)
- [B2 Backbones and facets](B2-backbones-and-facets.md)
- [B3 Relationships and dotted branches](B3-relationships-and-dotted-branches.md)
- [B4 Entity DNA and inheritance](B4-entity-dna-inheritance.md)
- [B5 Facts, provenance and identity](B5-facts-provenance-and-identity.md)
- [B6 Problems and hypotheses](B6-problems-and-hypotheses.md)

### Part C — How it is built
- [C1 Three-store architecture](C1-three-store-architecture.md)
- [C2 OWL to property-graph mapping](C2-owl-to-lpg-mapping.md)
- [C3 Ingestion and federation](C3-ingestion-and-federation.md)
- [C4 Reasoning and validation](C4-reasoning-and-validation.md)
- [C5 AI access and GraphRAG](C5-ai-access-graphrag.md)
- [C6 Security and non-functional requirements](C6-security-and-nfr.md)

### Part D — How it is run
- [D1 Governance and ownership](D1-governance-and-ownership.md)
- [D2 Change control and release](D2-change-control-and-release.md)
- [D3 IP, confidentiality and responsible AI](D3-ip-confidentiality-responsible-ai.md)

### Part E — How it is delivered
- [E1 Roadmap and phase plan](E1-roadmap.md)
- [E2 Team and operating model](E2-team-and-operating-model.md)
- [E3 Risks and mitigations](E3-risks-and-mitigations.md)
- [E4 Commercial packaging and decisions required](E4-commercial-packaging.md)

### Part F — Reference
- [F1 Glossary](F1-glossary.md)
- [F2 Standards catalogue](F2-standards-catalogue.md)
- [F3 Class and relation catalogue](F3-class-and-relation-catalogue.md)
- [F4 Query cookbook](F4-query-cookbook.md)
- [F5 Prototype guide](F5-prototype-guide.md)
- [F6 Reference model: Refinery Gamma CDU](F6-reference-model-gamma-cdu.md)

## Running example

Every chapter uses the same synthetic slice so ideas can be traced end to end:

- **Refinery Alpha** (coastal, 200 kbd) and **Refinery Beta** (inland, 120 kbd), both fictional.
- **CDU-1 overhead system** at Alpha: condensers E-101A/B, accumulator V-102, reflux pump P-103, overhead piping PC-101.
- **Hot-service pumps** P-201A/B, P-501 (Alpha) and P-401A/B, P-306 (Beta).
- **Opportunity crudes** HSOB (synthetic, high salt) and Doba (indicative values, high TAN).
- Fact IDs such as `F-00110` refer to `data/kg.json` (regenerate with `python -m ogkg.build_dataset`; IDs are stable for a given dataset version).
