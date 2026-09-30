"""
Mint each insight's result as cited Sector 2 facts (council finding AC-W2): an InsightResult node per insight with
its headline and value, whose lineage is the insight's evidence. AI answers can then cite the insight value itself.
"""
import json
import tempfile
from pathlib import Path

from .cdu_gamma import AS_OF, BUILD_TS


def snapshot(b, to_json):
    from . import refinery_insights
    from .kg import KG
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "kg.json"
        p.write_text(json.dumps(to_json(b), default=str))
        kg = KG(p)
        results = refinery_insights.run_all(kg)
    for r in results:
        nid = f"INS-{r['id']}"
        b.node(nid, "InsightResult", r["title"], "event", insight_id=r["id"], run_id=f"RUN-{BUILD_TS[:10]}")
        lineage = [x for x in r["evidence"] if x in b._by_id]
        if lineage:
            b.fact(nid, "headline", r["headline"], "", as_of=AS_OF, src="KG derived (insight run)", owner="ROLE-STEWARD",
                   method="calculated", lineage=lineage)
        else:       # structural insight (counts over the graph), not derived from facts
            b.fact(nid, "headline", r["headline"], "", as_of=AS_OF, src="KG structural check (insight run)", owner="ROLE-STEWARD",
                   method="recorded")
        if r.get("value_usd") is not None:
            b.fact(nid, "value_usd", r["value_usd"], "USD", as_of=AS_OF, src="KG derived (insight run)", owner="ROLE-PLAN",
                   method="calculated", lineage=lineage, basis=r.get("value_basis"), value_low=r.get("value_low"),
                   value_high=r.get("value_high"))
        for p_ in r["path"]:
            if p_ in b.nodes:
                b.edge(nid, "DESCRIBES", p_)
