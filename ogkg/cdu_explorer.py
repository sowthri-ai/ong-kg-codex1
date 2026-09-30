"""Build explorer/gamma_cdu_kg.html for the Refinery Gamma CDU model.  Run: python -m ogkg.cdu_explorer"""
import json
from pathlib import Path

from . import cdu_insights
from .kg import KG
from .ontology import RELATIONS

ROOT = Path(__file__).resolve().parent.parent


def main():
    kg = KG(ROOT / "data" / "cdu-gamma" / "kg.json")
    insights = cdu_insights.run_all(kg)
    for i in insights:
        if i["id"] == "preheat-energy-penalty":
            i["value_label"] = "fuel per year"
    meta = dict(kg.meta)
    meta.update(
        title="Refinery Gamma CDU",
        subtitle=("Complete reference model of a 500 kbpd crude distillation unit with two 250 kbpd trains: every section, "
                  "equipment item, subunit, maintainable item, part and instrument tag from L0 to L10 (Sector 1), with design "
                  "data, live values, limits, KPIs and a year of events attached as cited facts (Sector 2)."),
        eyebrow="OGKG reference model · Crude distillation · Fictional site",
        open=["OG", "SEG-DOWNSTREAM", "BC-REF", "SITE-GAMMA", "CDU-A", "VS-C2P", "VS-P2M"],
        suggestions=[
            "What is Train B's preheat fouling costing per year, and which exchangers should we clean?",
            "Which Train A overhead equipment is most exposed to corrosion?",
            "Show me everything under H-201, including its TMT limits and exceedances.",
            "Which decisions use the overhead chloride data, and who owns them?",
            "What seal plan and model does P-208A have, and what failed on it?",
            "Compare Train A and Train B yields and energy intensity.",
        ])
    bundle = dict(meta=meta, levels=kg.level_summary(), relations=RELATIONS, nodes=list(kg.nodes.values()),
                  edges=kg.edges, facts=kg.fact_list, insights=insights)
    payload = json.dumps(bundle, default=list, separators=(",", ":")).replace("</", "<\\/")
    tpl = (ROOT / "explorer" / "template.html").read_text()
    html = tpl.replace("<title>O&amp;G Value Chain KG</title>", "<title>Refinery Gamma CDU</title>", 1).replace("__KG_BUNDLE__", payload)
    out = ROOT / "explorer" / "gamma_cdu_kg.html"
    out.write_text(html)
    print(f"wrote {out.relative_to(ROOT)} ({len(html)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
