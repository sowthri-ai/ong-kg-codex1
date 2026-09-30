# E3 Risks and mitigations

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| 1 | **Boil-the-ocean scope.** "One-stop shop" becomes an attempt to model everything | High | High | Slice-first delivery (one unit family); every class must trace to a decision ([P1](../../README.md#3-design-principles)) | Delivery lead |
| 2 | **Data quality too poor for insights** (missing failure coding, inconsistent tags) | High | High | SHACL completeness reports in week 3 of the pilot; insights return completeness warnings; remediation owned by data owners | Data owners |
| 3 | **Correlation read as causation** (crude → failure) | Medium | High | Caveats on every insight; SME validation before action; RCA required for commercial decisions | Domain SMEs |
| 4 | **Two stores drift apart** | Medium | Medium | One writer per data kind; CI gate; drop-and-recompute inferences ([C1](C1-three-store-architecture.md)) | Ontology lead |
| 5 | **Ontology over-engineering** (full OWL-DL, too many classes) | Medium | Medium | OWL 2 RL profile; standards first; change board challenges each class | Ontology lead |
| 6 | **No named owners on the client side** | Medium | High | Ownership map signed off in pilot week 2 ([D1](D1-governance-and-ownership.md)); no owner means out of scope | Client sponsor |
| 7 | **Platform lock-in or platform politics** (client already on one platform) | Medium | Medium | Platform-neutral ontology; compile to the client's runtime ([C2](C2-owl-to-lpg-mapping.md)) | Solution architect |
| 8 | **Licensed content leaks into the asset** | Low | High | D3 rules; pre-commit scan; licensed data only in client tenancy | Delivery lead |
| 9 | **IP ownership unclear** (personal repository) | Medium | High | Private repository, synthetic data only; move to an employer-approved repository after the ED decision ([E4](E4-commercial-packaging.md)) | Author |
| 10 | **Low adoption.** Insights delivered but not used in decisions | Medium | High | Anchor on L8 decisions with named owners; write-back and value tracking; quarterly value review | AI product owner |
| 11 | **LLM ignores the answer contract** | Medium | Medium | Answer-contract test harness per release; server-side citation checks | AI engineer |
| 12 | **Performance at scale** (deep traversals, large fact volumes) | Low | Medium | Traversal budgets; facet summaries; cached latest values; load test in Phase 1 | Graph engineer |
