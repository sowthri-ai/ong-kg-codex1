# E4 Commercial packaging and decisions required

## E4.1 What the accelerator contains

| Component | Reusable across clients? | Notes |
|---|---|---|
| Ontology (OWL / SHACL / SKOS) + handbook | Yes | Core IP; versioned |
| OWL→LPG compiler and runtime templates | Yes | Neo4j, Cognite DM and triplestore targets |
| Connector patterns (CMMS, historian, LIMS, LP, CTRM, RBI) | Yes (patterns); client-specific mappings | Mapping files per client |
| Insight library (5 reference insights, growing) | Yes | Parameterised per client |
| Rule register and problem-pattern library | Yes (grows with every client) | Anonymised patterns only |
| Access layer (MCP) + answer-contract harness | Yes | |
| Explorer and lenses | Yes | |
| Client bindings, data, value case | No | Belong to the engagement |

## E4.2 How it can be offered

These are options for the Executive Director and Partner to decide; no pricing is implied.

| Option | Shape | When it fits |
|---|---|---|
| A. Diagnostic | 4–6 weeks: slice model + 3 insights on client data + value case | Opening a new account; proving value quickly |
| B. Pilot | Phase 2 scope ([E1](E1-roadmap.md)) | Sponsor with a funded AI programme |
| C. Enterprise knowledge layer | Phase 3 scale-out as the foundation for several AI use cases | Clients with multiple AI pilots rebuilding context |
| D. Alliance-embedded | Delivered on a partner platform (e.g. Cognite, SymphonyAI) with the ontology as the EY layer | Clients already committed to a platform |

## E4.3 Where it links to current work

| Initiative | How OGKG connects |
|---|---|
| OGC AI hub accelerator catalogue | OGKG as a catalogue entry and the foundation other accelerators reuse |
| Value-chain optimisation pursuits (molecule-level) | Material and economics backbones support molecule-level value-chain reasoning |
| Cognite FDE enablement | Cognite DM as a compiled runtime (backlog E1-P1-12) |
| SymphonyAI connector validation | Connector patterns and application backbone |
| Enterprise Digital Twin lab | OGKG as the semantic layer under the twin |

## E4.4 Decisions required

| # | Decision | Options | Recommended | Decision owner |
|---|---|---|---|---|
| 1 | Invest in Phase 1 as a reusable asset | Yes / defer | Yes: 8 weeks, small core team | Executive Director |
| 2 | Ownership and hosting of this repository | Keep private / move to an employer-approved repository | Move after decision 1 | Executive Director + IP / risk |
| 3 | Reference runtime for Phase 1 | Neo4j / Cognite DM / both | Neo4j first for speed, Cognite DM generator in parallel | Solution architect with ED |
| 4 | First pilot client and slice | Pipeline candidates | Account with an active AI programme and a willing reliability sponsor | ED / account lead |
| 5 | Production IRI namespace | Employer domain / client domain per engagement | Employer namespace for the core ontology; client namespace for instances | Enterprise architect |
| 6 | Licence for the asset | Proprietary / internal / partner-shareable | Proprietary until decision 2 | Executive Director + legal |
