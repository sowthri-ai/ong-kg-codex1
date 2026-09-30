# Contributing

## Ground rules
1. **Synthetic data only.** No client names, client data, credentials or licensed content.
2. **The ontology is the master.** Change classes and relations in `ontology/*.ttl` first; code and the property-graph schema follow.
3. **Record decisions.** Any change to a design principle, level, backbone or store adds an entry to `docs/adr/decision-log.md`.
4. **Keep the handbook MECE.** Each topic lives in exactly one chapter; other chapters link to it. See `docs/handbook/README.md`.

## Change workflow
| Change | Where | Review by |
|---|---|---|
| New class, relation or facet | `ontology/ogkg-core.ttl` + handbook Part B / F3 | Ontology owner |
| New constraint | `ontology/ogkg-shapes.ttl` | Ontology owner + data owner of that domain |
| New vocabulary term (tag, status) | `ontology/ogkg-vocab.ttl` | Facet owner |
| New insight | `ogkg/insights.py` + test + handbook A2 | Domain SME |
| Architecture change | `docs/adr/decision-log.md` + handbook Part C | Solution architect |

## Before you open a pull request
```bash
python -m ogkg.build_dataset && python -m ogkg.exports
python -m unittest discover -s tests -v
```
All tests must pass. Branch names: `feat/…`, `fix/…`, `onto/…`, `docs/…`.
