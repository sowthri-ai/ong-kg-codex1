# Working in this repository (for Claude Code and other coding agents)

## Ground rules
- **Synthetic data only.** Never add client names, client data, credentials or licensed content (see `docs/handbook/D3-ip-confidentiality-responsible-ai.md`).
- **The ontology is the master.** Change `ontology/*.ttl` first, then code. After any change to `ontology/ogkg-core.ttl`, run `python -m ogkg.catalogue` to regenerate handbook F3.
- **Keep the handbook MECE.** Each topic lives in one chapter (map in `docs/handbook/README.md`). Link, don't repeat.
- **Record principle-level changes** in `docs/adr/decision-log.md`.

## Commands
```bash
python -m ogkg.build_dataset      # data/kg.json
python -m ogkg.exports            # exports/ + explorer/og_value_chain_kg.html
python -m ogkg.catalogue          # docs/handbook/F3-class-and-relation-catalogue.md
python -m ogkg.cdu_gamma && python -m ogkg.ttl_v02 && python -m ogkg.cdu_explorer && python -m ogkg.hierarchy_view   # Refinery Gamma
python -m ogkg.owl_profile && python -m ogkg.conformance   # OWL 2 DL profile + standards conformance (B7)
python -m unittest discover -s tests -v
```
All tests must pass before committing. `tests/test_cdu_gamma.py` asserts the counts quoted in handbook F6; update both together. `tests/test_ontology_and_handbook.py` recomputes numbers quoted in the handbook; if you change the dataset, update the handbook and those tests together.

## What to build next
The Phase 1 backlog is in `docs/handbook/E1-roadmap.md` (items E1-P1-01 … 12). Start with E1-P1-01 (rdflib + pySHACL in CI) and E1-P1-02 (OWL→LPG compiler, spec in `ontology/mappings/owl-to-lpg.md`).
