# C6 Security and non-functional requirements

## C6.1 Security mechanisms

The controls themselves are set in [D1](D1-governance-and-ownership.md) and [D3](D3-ip-confidentiality-responsible-ai.md); this section covers the mechanisms that enforce them.

| Concern | Mechanism |
|---|---|
| Who can see what | Entitlements on the node and fact, by **site scope** (lineage), **facet** (e.g. economics restricted) and **sensitivity tag** (SKOS) |
| Commercially sensitive data (JV equity, prices, contracts) | Facts tagged `vocab:Restricted`; access layer filters them before building a context pack |
| Licensed market data (e.g. Platts, Argus) | Stored only in client tenancies with licence tags; never in the accelerator repository |
| AI access | Service identity per AI application; per-tool scopes; every call logged with user, tool, entities and fact IDs returned |
| Prompt-injection via documents | Document chunks are passed as data, never as instructions; the answer contract is set by the server, not by retrieved text |
| Write access | Only connectors, rule jobs and SME review screens can write; each writes to its own label set ([C1](C1-three-store-architecture.md), rule S1) |
| Secrets | In the platform's secret store; never in git (pre-commit scan) |
| OT boundary | Read-only replication from historian and OT systems via the site DMZ; no write path back to control systems |

## C6.2 Non-functional requirements (pilot targets)

| Area | Requirement | Target (pilot) |
|---|---|---|
| Performance | `get_entity` / `get_facts` latency | p95 < 300 ms |
| Performance | `get_context` pack assembly | p95 < 2 s |
| Performance | Insight query (multi-hop, one site) | < 10 s |
| Scale | Entities per site | 10^5 – 10^6 nodes; 10^6 – 10^7 facts |
| Freshness | Events (IOW exceedances, failures) | < 15 min from source |
| Freshness | Master data (equipment, tags) | Daily |
| Availability | Access layer | 99.5% business hours (pilot) |
| Auditability | Every AI answer reproducible from logged fact IDs | 100% |
| Portability | Ontology compiles to at least 2 runtimes | Neo4j + one of Cognite DM / triplestore |
| Recoverability | Rebuild LPG from sources + git | < 24 h |

Targets are proposals to be confirmed against client IT standards in Phase 1.

## C6.3 Runtime selection criteria

| Criterion | Weight | Questions |
|---|---|---|
| Client platform alignment | High | Is the client standardised on Cognite, Azure, AWS or on-premises? |
| Graph capability | High | Variable-length traversal, algorithms library, vector index |
| Semantic capability | Medium | RDF import/export, SHACL, SPARQL endpoint |
| Security | High | Fine-grained access control, audit, tenancy |
| Operability | Medium | Managed service, backup, monitoring |
| Cost and licensing | Medium | Licence model at 10^6–10^7 facts |
| Skills | Medium | Client and EY team familiarity |
