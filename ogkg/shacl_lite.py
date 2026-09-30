"""
Dependency-free evaluation of the core constraints in ontology/ogkg-shapes.ttl.

This mirrors the SHACL shapes shape by shape so the model can be checked where pySHACL
cannot be installed. It is not a general SHACL engine; backlog item E1-P1-01 replaces it
with pySHACL running the shapes file itself.
"""
from collections import defaultdict
from pathlib import Path

from .turtle_lite import RDF, parse_file

ROOT = Path(__file__).resolve().parent.parent
C = "https://example.org/ogkg/core#"
V = "https://example.org/ogkg/vocab#"
TYPE = RDF + "type"
SUB = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
LABEL = "http://www.w3.org/2000/01/rdf-schema#label"


def load(*paths):
    triples = []
    for p in paths:
        triples += parse_file(p).triples
    return triples


def validate(data_paths):
    onto = load(ROOT / "ontology" / "ogkg-core.ttl", ROOT / "ontology" / "ext" / "ogkg-cdu.ttl")
    parents = defaultdict(set)
    for s, p, o in onto:
        if p == SUB:
            parents[s].add(o)

    def supers(c, seen=None):
        seen = seen or set()
        for q in parents.get(c, ()):
            if q not in seen:
                seen.add(q)
                supers(q, seen)
        return seen

    triples = load(*data_paths)
    out = defaultdict(lambda: defaultdict(list))
    types = defaultdict(set)
    for s, p, o in triples:
        out[s][p].append(o)
        if p == TYPE:
            types[s].add(o)
    closure = {s: set(ts) | set().union(*(supers(t) for t in ts)) for s, ts in types.items()}
    is_a = lambda s, cls: C + cls in closure.get(s, ())
    violations = []

    def need(shape, s, path, n_min=1, n_max=None, pred=None, msg=""):
        vals = out[s].get(path, [])
        if len(vals) < n_min or (n_max is not None and len(vals) > n_max) or (pred and not all(pred(v) for v in vals)):
            violations.append((shape, s, path.split("#")[-1], msg or f"{len(vals)} value(s)"))

    dec = lambda v: isinstance(v, tuple) and v[2].endswith("#decimal")
    for s in closure:
        if any(is_a(s, c) for c in ("AssetSpineNode", "ProcessSpineNode", "Segment")):
            need("SpineNodeShape", s, C + "partOf", 1, 1)
            need("SpineNodeShape", s, C + "hasLevel", 1, 1)
            need("SpineNodeShape", s, LABEL, 1)
        if is_a(s, "EquipmentUnit"):
            need("EquipmentUnitShape", s, C + "eqClass", 1)
            need("EquipmentUnitShape", s, C + "partOf", 1, 1,
                 pred=lambda o: any(is_a(o, k) for k in ("SectionSystem", "PlantUnit", "Installation")))
        if is_a(s, "Pump"):
            need("PumpShape", s, C + "ofModel", 1, pred=lambda o: is_a(o, "EquipmentModel"))
            need("PumpShape", s, C + "sealPlan", 1)
            need("PumpShape", s, C + "serviceTemperature", 1, pred=dec)
        if is_a(s, "Fact"):
            need("FactShape", s, C + "subject", 1, 1)
            need("FactShape", s, C + "predicateKey", 1)
            need("FactShape", s, C + "value", 1, 1)
            need("FactShape", s, C + "asOf", 1, pred=lambda v: v[2].endswith("#date"))
            if not (out[s].get(C + "sourceSystem") or out[s].get(C + "sourceSystemName")):
                violations.append(("FactShape", s, "sourceSystem", "no source"))
            need("FactShape", s, C + "factOwner", 1, pred=lambda o: is_a(o, "Role"))
            need("FactShape", s, C + "confidence", 1, pred=lambda o: o in (V + "High", V + "Medium", V + "Low"))
            need("FactShape", s, C + "method", 1)
            if V + "Calculated" in out[s].get(C + "method", []) and not out[s].get(C + "derivedFrom"):
                src = [x[1] for x in out[s].get(C + "sourceSystemName", [])]
                if all(x.startswith("KG derived") for x in src):
                    violations.append(("DerivedFactShape", s, "derivedFrom", "calculated in the KG without inputs"))
        if is_a(s, "DataElement"):
            need("DataElementShape", s, C + "ownedBy", 1, pred=lambda o: is_a(o, "Role"))
            if not (out[s].get(C + "instantiatedBy") or out[s].get(C + "mapsToPredicate")):
                violations.append(("DataElementShape", s, "instantiatedBy|mapsToPredicate", "no system of record"))
        if is_a(s, "Grouping"):
            need("GroupingShape", s, C + "ownedBy", 1, pred=lambda o: is_a(o, "Role"))
        if is_a(s, "ApplicationInstance"):
            need("ApplicationInstanceShape", s, C + "instanceOf", 1, 1)
            need("ApplicationInstanceShape", s, C + "scopedTo", 1)
    return violations, len(triples)


if __name__ == "__main__":
    import sys
    v, n = validate(sys.argv[1:])
    print(f"{n} triples checked, {len(v)} violations")
    for x in v[:50]:
        print("  ", x)
