# D3 IP, confidentiality and responsible AI

## D3.1 Intellectual property

| Item | Position | Action |
|---|---|---|
| Ontology, handbook, code, insight library | Intended as a reusable asset of the author's employer | Confirm ownership and approved hosting with the Executive Director before any external use ([E4](E4-commercial-packaging.md)) |
| This repository | Private, personal account, synthetic data only | Move to an employer-approved repository once ownership is confirmed |
| Client-specific bindings, data and mappings | Belong to the client engagement | Never merged back into the accelerator |
| Standards (ISO, API, CFIHOS, ISA) | Owned by their publishers | Referenced by name and clause only; no text or tables copied |
| Engineering handbooks and property databases (e.g. Perry's, API Technical Data Book, DIPPR) | Copyrighted or licensed | Equations from general engineering knowledge may be encoded; tables and text only under licence, stored in client tenancy |
| Market price data (e.g. Platts, Argus) | Licensed | Client tenancy only, with licence tags and entitlements |

## D3.2 Confidentiality rules for this repository

1. **Synthetic data only.** No client names, sites, tags, equipment lists, costs or documents.
2. **No credentials** or connection strings.
3. **No licensed content** (see D3.1).
4. **Pre-commit scan** for client names on a maintained deny-list, e-mail addresses, keys and large binary files.
5. **Public crude-grade values** are marked `method=indicative` and `confidence=medium`.

## D3.3 Responsible AI

| Risk | Control | Where enforced |
|---|---|---|
| Hallucinated numbers | Answer contract: cite or don't state | Access layer ([C5](C5-ai-access-graphrag.md)) |
| Hypotheses presented as facts | Status labels mandatory in answers | Access layer + UAT tests |
| Correlation mistaken for causation (e.g. crude → failure) | Caveat attached to every insight; SME validation before action | Insight contract ([A2](A2-use-cases-and-personas.md)) |
| Stale data driving decisions | Freshness SLAs on data elements feeding L8 decisions | Rule R-20 ([C4](C4-reasoning-and-validation.md)) |
| Over-reliance on AI in safety decisions | OGKG informs; accountable humans decide. Safety-critical changes still follow MOC | Governance ([D1](D1-governance-and-ownership.md)) |
| Access beyond need | Entitlements by site, facet and sensitivity | [C6](C6-security-and-nfr.md) |
| Bias toward well-instrumented assets | Completeness warnings attached to insight results | SHACL-before-insight check |

## D3.4 Human accountability

The graph records who decided, not only what the AI proposed. Every validated hypothesis, approved insight and decision write-back carries a named reviewer and a date.
