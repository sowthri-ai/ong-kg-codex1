"""
Standards layer: reads the alignment modules in ontology/alignments/ and resolves, for any node,
the code or concept it carries in each standard (ISO 14224, ISA-95, CFIHOS, MIMOSA CCOM, ISO 15926-14,
IOF / BFO). The TTL files are the master; nothing here restates a mapping.

Class-derived codes are resolved on demand (not stored on every node). Instance-level standard data
that no class implies is set by `apply(b)` during the build:
  * purdue_level   on application instances and field devices (Purdue / IEC 62443)
  * isa95_function on process-spine L4 processes (IEC 62264 functional level / MOM activity model)
"""
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from .turtle_lite import RDF, parse_file

ROOT = Path(__file__).resolve().parent.parent
C = "https://example.org/ogkg/core#"
V = "https://example.org/ogkg/vocab#"
SUB = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
SUBP = "http://www.w3.org/2000/01/rdf-schema#subPropertyOf"
SKOS = "http://www.w3.org/2004/02/skos/core#"
ALIGN_DIR = ROOT / "ontology" / "alignments"
MODULES = [ROOT / "ontology" / "ogkg-core.ttl", ROOT / "ontology" / "ext" / "ogkg-cdu.ttl"] + sorted(ALIGN_DIR.glob("*.ttl"))

# annotation -> short key used in reports and the LPG export
ANNOTATIONS = {"iso14224Code": "iso14224_class", "iso14224Level": "iso14224_level", "isa95EquipmentLevel": "isa95_level",
               "cfihosConcept": "cfihos_concept", "cfihosClassName": "cfihos_class_name", "ccomEntity": "ccom_entity"}
EXTERNAL = {"lis14": "http://rds.posccaesar.org/ontology/lis14/rdl/",
            "iof": "https://spec.industrialontologies.org/ontology/construct/",
            "bfo": "http://purl.obolibrary.org/obo/BFO_"}

# Purdue level by application category (instance data: a deployment decides the zone)
PURDUE_BY_CATEGORY = {"APP-CAT-DCS": 2, "APP-CAT-APC": 2, "APP-CAT-HIST": 3, "APP-CAT-LIMS": 3, "APP-CAT-CEMS": 3,
                      "APP-CAT-CMMS": 4, "APP-CAT-RBI": 4, "APP-CAT-LP": 4, "APP-CAT-EDMS": 4}
PURDUE_DEVICE_CLASSES = {"InputDevice", "ControlValve", "ShutdownValve"}          # Purdue level 0: sensors and final elements
# IEC 62264 functional level / MOM activity model of each L4 business process
ISA95_FUNCTION = {
    "P-THRU": "ProductionOperations", "P-DESALT": "ProductionOperations", "P-HTR": "ProductionOperations",
    "P-CUT": "ProductionOperations", "P-ENERGY": "ProductionOperations", "P-H2": "ProductionOperations",
    "P-SULF": "ProductionOperations", "P-FCC": "ProductionOperations", "P-HCU": "ProductionOperations",
    "P-DCU": "ProductionOperations", "P-BLEND": "ProductionOperations",
    "P-OVHCORR": "MaintenanceOperations", "P-ROTREL": "MaintenanceOperations", "P-COMPREL": "MaintenanceOperations",
    "P-PLAN": "BusinessPlanningLogistics",
}


@lru_cache(maxsize=1)
def model():
    """Parse core + extension + alignment modules once."""
    parents, ann, ext_super, verification, prop_super, related = (defaultdict(set), defaultdict(dict), defaultdict(set),
                                                                  {}, defaultdict(set), defaultdict(set))
    for path in MODULES:
        for s, p, o in parse_file(path).triples:
            if p == SUB and isinstance(o, str):
                if o.startswith(C):
                    parents[s].add(o)
                else:
                    ext_super[s].add(o)
            elif p == SUBP and isinstance(o, str) and not o.startswith(C):
                prop_super[s].add(o)
            elif p.startswith(C) and p[len(C):] in ANNOTATIONS:
                ann[s][p[len(C):]] = o[1] if isinstance(o, tuple) else o
            elif p == C + "verificationStatus":
                verification[s] = o[1]
            elif p in (SKOS + "closeMatch", SKOS + "relatedMatch", SKOS + "exactMatch"):
                related[s].add((p[len(SKOS):], o))
    return dict(parents=parents, ann=ann, ext_super=ext_super, verification=verification, prop_super=prop_super,
                related=related)


def ancestors(cls):
    """Class and its OGKG superclasses, most specific first (breadth-first)."""
    m = model()
    start = cls if cls.startswith("http") else C + cls
    out, frontier, seen = [], [start], {start}
    while frontier:
        out += frontier
        nxt = []
        for c in frontier:
            for q in sorted(m["parents"].get(c, ())):
                if q not in seen:
                    seen.add(q)
                    nxt.append(q)
        frontier = nxt
    return out


def resolve(cls, annotation):
    """Most specific value of an alignment annotation for a class, or None."""
    ann = model()["ann"]
    for c in ancestors(cls):
        if annotation in ann.get(c, {}):
            return ann[c][annotation]
    return None


def external_types(cls, scheme):
    """External superclasses (logical axioms only) of a class in one scheme: 'lis14', 'iof' or 'bfo'."""
    m, ns, out = model(), EXTERNAL[scheme], []
    for c in ancestors(cls):
        out += sorted(x for x in m["ext_super"].get(c, ()) if x.startswith(ns))
    return list(dict.fromkeys(out))


def codes_for(node):
    """All class-derived standard codes for a kg.json node."""
    cls = node["props"].get("onto_class") or node["cls"]
    out = {key: resolve(cls, a) for a, key in ANNOTATIONS.items()}
    out["lis14"] = [x.rsplit("/", 1)[-1] for x in external_types(cls, "lis14")]
    out["iof_bfo"] = [x.rsplit("/", 1)[-1] for x in external_types(cls, "iof") + external_types(cls, "bfo")]
    if "purdue_level" in node["props"]:
        out["purdue_level"] = node["props"]["purdue_level"]
    if "isa95_function" in node["props"]:
        out["isa95_function"] = node["props"]["isa95_function"]
    return {k: v for k, v in out.items() if v not in (None, [], "")}


def apply(b):
    """Set instance-level standard data on the Gamma builder (Purdue levels, ISA-95 functions)."""
    cat = {e["source"]: e["target"] for e in b.edges if e["rel"] == "INSTANCE_OF"}
    for nid, n in b.nodes.items():
        oc = n["props"].get("onto_class") or n["cls"]
        if n["cls"] == "ApplicationInstance" and cat.get(nid) in PURDUE_BY_CATEGORY:
            n["props"]["purdue_level"] = PURDUE_BY_CATEGORY[cat[nid]]
        elif oc in PURDUE_DEVICE_CLASSES:
            n["props"]["purdue_level"] = 0
        if n["cls"] == "Process" and nid in ISA95_FUNCTION:
            n["props"]["isa95_function"] = ISA95_FUNCTION[nid]
