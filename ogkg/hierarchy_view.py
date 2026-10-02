"""
Build explorer/refinery_gamma_hierarchy.html: the whole L0-L10 hierarchy of a site graph (asset and process
spines) with each node's place in every aligned standard, its links beyond the hierarchy and its cited facts.

    python -m ogkg.hierarchy_view                       # standalone page in explorer/
    python -m ogkg.hierarchy_view --artifact OUT.html   # same page without the document skeleton (claude.ai artifact)

Standards columns are resolved from ontology/alignments/ through ogkg.standards, so the page never restates a mapping.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from . import standards

ROOT = Path(__file__).resolve().parent.parent
KG_JSON = ROOT / "data" / "cdu-gamma" / "kg.json"
TEMPLATE = ROOT / "explorer" / "hierarchy_template.html"
OUT = ROOT / "explorer" / "refinery_gamma_hierarchy.html"
LADDER_CLASSES = ["Industry", "Segment", "BusinessCategory", "Installation", "PlantUnit", "SectionSystem", "EquipmentUnit",
                  "Subunit", "MaintainableItem", "Part", "DataPoint"]
FACTS_PER_NODE = 12


def build_data(kg_json=KG_JSON):
    d = json.loads(Path(kg_json).read_text())
    nodes = d["nodes"]
    idx = {n["id"]: i for i, n in enumerate(nodes)}
    par = {e["source"]: e["target"] for e in d["edges"] if e["rel"] == "PART_OF"}
    oc = lambda n: n["props"].get("onto_class") or n["cls"]
    rows = []
    for n in nodes:
        p = n["props"]
        rows.append([n["id"], n["name"], oc(n), n["level"] if n["level"] is not None else -1, n["spine"],
                     idx.get(par.get(n["id"]), -1), p.get("external_ids", {}), p.get("purdue_level"), p.get("isa95_function")])
    rels = sorted({e["rel"] for e in d["edges"] if e["rel"] != "PART_OF"})
    ri = {r: i for i, r in enumerate(rels)}
    edges = [[idx[e["source"]], ri[e["rel"]], idx[e["target"]]] for e in d["edges"] if e["rel"] != "PART_OF"]
    latest = {}
    for f in d["facts"]:                                  # latest current value per (subject, predicate)
        if f.get("status", "current") != "current":
            continue
        k = (f["subject"], f["predicate"])
        if k not in latest or latest[k]["valid_from"] <= f["valid_from"]:
            latest[k] = f
    facts = defaultdict(list)
    for (s, pr), f in latest.items():
        if s in idx:
            v = f["value"]
            if isinstance(v, float):
                v = round(v, 3)
            if isinstance(v, (list, dict)):
                v = json.dumps(v)[:60]
            facts[idx[s]].append([pr, v, f["unit"], f["source_system"], f["as_of"], f["method"], f["confidence"]])
    facts = {k: sorted(v, key=lambda x: x[0])[:FACTS_PER_NODE] for k, v in sorted(facts.items())}
    std = {c: standards.codes_for({"cls": c, "props": {"onto_class": c}})
           for c in sorted({oc(n) for n in nodes} | set(LADDER_CLASSES))}
    stats = {"nodes": len(nodes), "edges": len(d["edges"]), "facts": len(d["facts"])}
    return dict(nodes=rows, rels=rels, edges=edges, facts=facts, std=std), stats


def render(kg_json=KG_JSON, standalone=True):
    data, stats = build_data(kg_json)
    tpl = TEMPLATE.read_text()
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    page = (tpl.replace("__N_NODES__", f"{stats['nodes']:,}").replace("__N_EDGES__", f"{stats['edges']:,}")
               .replace("__N_FACTS__", f"{stats['facts']:,}").replace("__DATA__", payload))
    if not standalone:
        return page                                       # the artifact host adds the document skeleton
    head, body = page.split('<div class="wrap">', 1)
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<style>body{margin:0}[hidden]{display:none!important}</style>\n'
            + head + '</head>\n<body>\n<div class="wrap">' + body + "\n</body>\n</html>\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--artifact", help="also write a skeleton-less copy for publishing as a claude.ai artifact")
    a = ap.parse_args(argv)
    OUT.write_text(render())
    print("wrote", OUT.relative_to(ROOT))
    if a.artifact:
        Path(a.artifact).write_text(render(standalone=False))
        print("wrote", a.artifact)


if __name__ == "__main__":
    main()
