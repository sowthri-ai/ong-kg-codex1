"""
Generates handbook chapter F3 (class and relation catalogue) from ontology/ogkg-core.ttl,
so the catalogue can never drift from the ontology.

Run:  python -m ogkg.catalogue
"""
from collections import defaultdict
from pathlib import Path

from .turtle_lite import RDF, parse_file

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "ontology" / "ogkg-core.ttl"
OUT = ROOT / "docs" / "handbook" / "F3-class-and-relation-catalogue.md"

NS = "https://example.org/ogkg/core#"
VNS = "https://example.org/ogkg/vocab#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"

SHORT = {NS: "", VNS: "vocab:", RDFS: "rdfs:", OWL: "owl:", "http://www.w3.org/2004/02/skos/core#": "skos:",
         "http://www.w3.org/2001/XMLSchema#": "xsd:", "http://www.w3.org/ns/prov#": "prov:",
         "http://qudt.org/schema/qudt/": "qudt:", RDF: "rdf:"}


def short(x):
    if isinstance(x, tuple):
        return x[1]
    for ns, p in SHORT.items():
        if x.startswith(ns):
            return p + x[len(ns):]
    return x


def build():
    t = parse_file(CORE).triples
    props = defaultdict(lambda: defaultdict(list))
    for s, p, o in t:
        props[s][p].append(o)
    types = {s: {short(o) for o in v[RDF + "type"]} for s, v in props.items()}

    def one(s, p):
        v = props[s].get(p)
        return ", ".join(short(x) for x in v) if v else ""

    classes = sorted(s for s, ty in types.items() if "owl:Class" in ty and s.startswith(NS))
    objprops = sorted(s for s, ty in types.items() if "owl:ObjectProperty" in ty and s.startswith(NS))
    dataprops = sorted(s for s, ty in types.items() if "owl:DatatypeProperty" in ty and s.startswith(NS))

    # order classes by upper partition then level
    def level(s):
        v = props[s].get(NS + "levelNumber")
        return int(v[0][1]) if v else 99

    lines = [
        "# F3 Class and relation catalogue",
        "",
        "> Generated from `ontology/ogkg-core.ttl` by `python -m ogkg.catalogue`. Do not edit by hand; change the ontology and regenerate.",
        "",
        f"Ontology version {one('https://example.org/ogkg/core', OWL + 'versionInfo')} · "
        f"{len(classes)} classes · {len(objprops)} object properties · {len(dataprops)} datatype properties.",
        "",
        "## F3.1 Spine classes by level",
        "",
        "| Level | Class | Parent class | Aligned to |",
        "|---|---|---|---|",
    ]
    for s in sorted([c for c in classes if level(c) < 99], key=lambda c: (level(c), short(c))):
        lines.append(f"| L{level(s)} | `{short(s)}` | {one(s, RDFS + 'subClassOf')} | {one(s, NS + 'alignedTo')} |")

    lines += ["", "## F3.2 Other classes", "", "| Class | Parent class | Notes |", "|---|---|---|"]
    for s in sorted([c for c in classes if level(c) == 99], key=lambda c: (one(c, RDFS + 'subClassOf'), short(c))):
        note = one(s, NS + "alignedTo") or one(s, RDFS + "comment")
        lines.append(f"| `{short(s)}` | {one(s, RDFS + 'subClassOf')} | {note} |")

    lines += ["", "## F3.3 Object properties (relationships)", "",
              "| Property | Property-graph type | Domain | Range | Facet | DNA channel | Characteristics |",
              "|---|---|---|---|---|---|---|"]
    for s in objprops:
        chars = ", ".join(sorted(x for x in types[s] if x in ("owl:TransitiveProperty", "owl:SymmetricProperty", "owl:FunctionalProperty")))
        lines.append(f"| `{short(s)}` | `{one(s, NS + 'lpgType')}` | {one(s, RDFS + 'domain')} | {one(s, RDFS + 'range')} | "
                     f"{one(s, NS + 'facet')} | {one(s, NS + 'dnaChannel')} | {chars.replace('owl:', '')} |")

    lines += ["", "## F3.4 Datatype properties", "",
              "| Property | Domain | Range | Facet | Inheritable |", "|---|---|---|---|---|"]
    for s in dataprops:
        lines.append(f"| `{short(s)}` | {one(s, RDFS + 'domain')} | {one(s, RDFS + 'range')} | {one(s, NS + 'facet')} | {one(s, NS + 'inheritable')} |")
    lines.append("")
    return "\n".join(lines)


def main():
    OUT.write_text(build())
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
