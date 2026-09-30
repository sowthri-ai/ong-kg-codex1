"""Build explorer/refinery_gamma_kg.html for the Refinery Gamma model.  Run: python -m ogkg.cdu_explorer"""
import json
from pathlib import Path

from . import refinery_insights
from .kg import KG
from .ontology import RELATIONS

ROOT = Path(__file__).resolve().parent.parent


def main():
    kg = KG(ROOT / "data" / "cdu-gamma" / "kg.json")
    insights = refinery_insights.run_all(kg)
    for i in insights:
        if i["id"] == "preheat-energy-penalty":
            i["value_label"] = "fuel per year"
        i.setdefault("value_label", "")
    meta = dict(kg.meta)
    meta.update(
        title="Refinery Gamma",
        subtitle=("Reference model of a 500 kbpd refinery with Nelson complexity ≈ 15: every plant unit and section, the stream network, "
                  "hydrogen and sulfur balances, and full L0–L10 depth for the two-train CDU, FCC, hydrocracker and delayed coker — "
                  "equipment, parts and instrument tags (Sector 1) with design data, live values, limits, KPIs and a year of events "
                  "as cited facts (Sector 2)."),
        eyebrow="OGKG reference model · Whole refinery · Fictional site",
        open=["OG", "SEG-DOWNSTREAM", "BC-REF", "SITE-GAMMA", "HCU-1", "VS-C2P", "PG-NET"],
        suggestions=[
            "What happens to our hydrogen balance if the reformer trips?",
            "How much more sour crude can we run before the SRU is the limit?",
            "Which conversion-unit failures were signalled by an IOW exceedance first?",
            "How is our Nelson complexity of 15 built up, unit by unit?",
            "What is Train B's preheat fouling costing per year, and which exchangers should we clean?",
            "Show me everything under R-402, including its WABT and temperature limits.",
            "Which decisions use the SRU sulfur production data, and who owns them?",
        ])
    bundle = dict(meta=meta, levels=kg.level_summary(), relations=RELATIONS, nodes=list(kg.nodes.values()),
                  edges=kg.edges, facts=kg.fact_list, insights=insights)
    payload = json.dumps(bundle, default=list, separators=(",", ":")).replace("</", "<\\/")
    tpl = (ROOT / "explorer" / "template.html").read_text()
    html = tpl.replace("<title>O&amp;G Value Chain KG</title>", "<title>Refinery Gamma</title>", 1).replace("__KG_BUNDLE__", payload)
    out = ROOT / "explorer" / "refinery_gamma_kg.html"
    out.write_text(html)
    print(f"wrote {out.relative_to(ROOT)} ({len(html)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
