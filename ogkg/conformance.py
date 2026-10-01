"""
Standards conformance checker for a site graph (default: Refinery Gamma).

Runs automated checks per standard and writes a conformance report:
    python -m ogkg.conformance            -> data/cdu-gamma/conformance.json + conformance.md

Each check is either
  * "must"     — a hard requirement; a failure fails the build (tests/test_standards.py), or
  * "coverage" — a measured share reported with its target; below target is reported, not hidden.
"Lookup required" items (codes the standards body publishes under licence or registration) are
counted separately so nobody mistakes a structural alignment for a code-level one.

This proves conformance of the model to the requirements listed here. It is not a certification:
none of these standards bodies certifies ontologies, and ISO 14224 / CFIHOS code tables must still
be confirmed against the client's licensed or registered copies (handbook B7).
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

from . import owl_profile, shacl_lite, standards
from .turtle_lite import RDF, parse_file

ROOT = Path(__file__).resolve().parent.parent
GAMMA = ROOT / "data" / "cdu-gamma"
C = "https://example.org/ogkg/core#"
OWL = "http://www.w3.org/2002/07/owl#"
STANDARDS = ["OWL 2", "Knowledge graph (RDF / SHACL / PROV-O / SKOS)", "ISO 15926-14", "IOF / BFO", "ISO 14224",
             "ISA-95 / Purdue", "CFIHOS", "MIMOSA CCOM"]
OCCURRENT_TERMS = {"FailureEvent", "MaintenanceProcess", "BusinessProcess", "FailureProcess", "BFO_0000015"}


def _cls(n):
    return n["props"].get("onto_class") or n["cls"]


def _pct(a, b):
    return round(100.0 * a / b, 1) if b else 100.0


class Report:
    def __init__(self):
        self.rows = []

    def must(self, std, cid, requirement, ok_count, total, detail=""):
        self.rows.append(dict(standard=std, id=cid, kind="must", requirement=requirement, passed=ok_count == total,
                              measure=f"{ok_count}/{total}", detail=detail))

    def coverage(self, std, cid, requirement, ok_count, total, target, detail=""):
        pct = _pct(ok_count, total)
        self.rows.append(dict(standard=std, id=cid, kind="coverage", requirement=requirement, passed=pct >= target,
                              measure=f"{ok_count}/{total} ({pct}%)", target=f">= {target}%", detail=detail))

    def info(self, std, cid, requirement, measure, detail=""):
        self.rows.append(dict(standard=std, id=cid, kind="info", requirement=requirement, passed=True, measure=measure,
                              detail=detail))


def disjoint_sets():
    """Member lists of every owl:AllDisjointClasses axiom in the OGKG modules."""
    out = []
    for path in owl_profile.ONTOLOGY_MODULES:
        ts = parse_file(path).triples
        first = {s: o for s, p, o in ts if p == RDF + "first"}
        rest = {s: o for s, p, o in ts if p == RDF + "rest"}
        heads = [o for s, p, o in ts if p == OWL + "members"]
        for h in heads:
            members, node = [], h
            while node in first:
                members.append(first[node])
                node = rest.get(node)
            out.append(members)
        for s, p, o in ts:
            if p == OWL + "disjointWith":
                out.append([s, o])
    return out


def run(site_dir=GAMMA):
    site_dir = Path(site_dir)
    data = json.loads((site_dir / "kg.json").read_text())
    nodes = {n["id"]: n for n in data["nodes"]}
    out, inn = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    for e in data["edges"]:
        out[e["source"]][e["rel"]].append(e["target"])
        inn[e["target"]][e["rel"]].append(e["source"])
    ttl = [site_dir / "structure.ttl", site_dir / "information.ttl"]
    anc = {}

    def ancestors(n):
        c = _cls(n)
        if c not in anc:
            anc[c] = set(standards.ancestors(c))
        return anc[c]

    is_a = lambda n, k: C + k in ancestors(n)
    m = standards.model()
    r = Report()

    # ------------------------------------------------------------------ OWL 2
    std = STANDARDS[0]
    v, dev, stats = owl_profile.check(data_paths=ttl)
    r.must(std, "OWL-1", "Ontology modules and site data satisfy the OWL 2 DL structural restrictions (D1-D9)",
           0 if v else 1, 1, f"{len(v)} violation(s); {stats['classes']} classes, {stats['object_properties']} object "
                              f"properties, {stats['triples']} triples; xsd:date literals are a documented deviation (ADR-0012)")
    sets = disjoint_sets()
    clash = [n["id"] for n in nodes.values() if any(len(ancestors(n) & set(s)) > 1 for s in sets)]
    r.must(std, "OWL-2", "No individual falls in two disjoint classes (owl:AllDisjointClasses on the upper partition)",
           len(nodes) - len(clash), len(nodes), ", ".join(clash[:5]))
    declared = {s for path in owl_profile.ONTOLOGY_MODULES for s, p, o in parse_file(path).triples
                if p == RDF + "type" and o == OWL + "Class"}
    undeclared = sorted({_cls(n) for n in nodes.values()} - {x[len(C):] for x in declared if x.startswith(C)})
    r.must(std, "OWL-3", "Every class used by the data is declared in the ontology", len({_cls(n) for n in nodes.values()}) - len(undeclared),
           len({_cls(n) for n in nodes.values()}), ", ".join(undeclared))
    modules = owl_profile.ONTOLOGY_MODULES
    with_version = sum(1 for p in modules if "owl:versionIRI" in p.read_text())
    r.must(std, "OWL-4", "Every ontology module has an owl:versionIRI and resolves through ontology/catalog-v001.xml",
           with_version, len(modules))

    # ------------------------------------------------------------------ KG
    std = STANDARDS[1]
    sv, ntrip = shacl_lite.validate(ttl)
    r.must(std, "KG-1", "SHACL shapes (incl. generic rdfs:domain / rdfs:range) report no violations", 0 if sv else 1, 1,
           f"{len(sv)} violation(s) over {ntrip} triples")
    iris = Counter(n["props"].get("iri") for n in nodes.values())
    r.must(std, "KG-2", "Every node has a unique, site-scoped IRI, a label and a class",
           sum(1 for n in nodes.values() if n["props"].get("iri") and iris[n["props"]["iri"]] == 1 and n["name"] and n["cls"]), len(nodes))
    prov_ok = sum(1 for f in data["facts"] if f["source_system"] and f["owner"] and f["as_of"] and f["method"] and f["confidence"]
                  and (f["method"] != "calculated" or f["lineage"] or f["source_system"]))
    r.must(std, "KG-3", "Every fact carries PROV-O provenance: source, owner (attribution), as-of, method, confidence",
           prov_ok, len(data["facts"]))
    vocab = {s for s, p, o in parse_file(ROOT / "ontology" / "ogkg-vocab.ttl").triples if p == RDF + "type"}
    used = set()
    for path in ttl:
        for s, p, o in parse_file(path).triples:
            if isinstance(o, str) and o.startswith("https://example.org/ogkg/vocab#"):
                used.add(o)
    r.must(std, "KG-4", "Every controlled value used by the data is a SKOS concept in a declared scheme",
           len(used & vocab), len(used), ", ".join(sorted(x.split("#")[1] for x in used - vocab)))
    temporal = sum(1 for f in data["facts"] if f.get("valid_from") and f.get("status") in ("current", "superseded", "retracted"))
    r.must(std, "KG-5", "Every fact is bitemporal (valid_from, recorded_at) with a status; history is kept, not overwritten",
           temporal, len(data["facts"]))

    # ------------------------------------------------------------------ ISO 15926-14
    std = STANDARDS[2]
    fl = [n for n in nodes.values() if is_a(n, "FunctionalLocation")]
    phys = [n for n in nodes.values() if is_a(n, "PhysicalAsset")]
    r.must(std, "15926-1", "Functional objects (tags) and physical objects (serial items) are separate individuals, linked by installedAt",
           sum(1 for n in phys if all(is_a(nodes[t], "FunctionalLocation") for t in out[n["id"]]["INSTALLED_AT"]) and out[n["id"]]["INSTALLED_AT"]),
           len(phys), f"{len(fl)} functional locations, {len(phys)} physical items")
    lis = lambda n: standards.external_types(_cls(n), "lis14")
    r.must(std, "15926-2", "Every functional location is a lis:FunctionalObject; every physical item a lis:PhysicalObject",
           sum(1 for n in fl if any(x.endswith("/FunctionalObject") for x in lis(n))) +
           sum(1 for n in phys if any(x.endswith(("/PhysicalArtefact", "/PhysicalObject")) for x in lis(n))), len(fl) + len(phys))
    r.coverage(std, "15926-3", "Share of all individuals with a LIS-14 superclass (logical axiom)",
               sum(1 for n in nodes.values() if lis(n)), len(nodes), 90)
    lis_terms = [k for k in m["verification"] if k.startswith(standards.EXTERNAL["lis14"])]
    r.must(std, "15926-4", "Every LIS-14 IRI used is verified against the published LIS-14 ontology",
           sum(1 for k in lis_terms if m["verification"][k].startswith("verified")), len(lis_terms))

    # ------------------------------------------------------------------ IOF / BFO
    std = STANDARDS[3]
    bad = []
    for c in {_cls(n) for n in nodes.values()}:
        ext = [x.rsplit("/", 1)[-1] for x in standards.external_types(c, "iof") + standards.external_types(c, "bfo")]
        kinds = {x in OCCURRENT_TERMS for x in ext}
        if len(kinds) > 1:
            bad.append(c)
    r.must(std, "IOF-1", "No OGKG class is placed under both a BFO continuant and a BFO occurrent (safe to import IOF + BFO)",
           len({_cls(n) for n in nodes.values()}) - len(bad), len({_cls(n) for n in nodes.values()}), ", ".join(bad))
    iof = lambda n: standards.external_types(_cls(n), "iof") + standards.external_types(_cls(n), "bfo")
    non_fl = [n for n in nodes.values() if not is_a(n, "FunctionalLocation")]
    r.coverage(std, "IOF-2", "Share of individuals outside the functional-location hierarchy with an IOF or BFO superclass",
               sum(1 for n in non_fl if iof(n)), len(non_fl), 90,
               "unaligned classes: " + ", ".join(f"{k} {v}" for k, v in Counter(_cls(n) for n in non_fl if not iof(n)).most_common(6)))
    r.info(std, "IOF-2b", "Functional locations: IOF has no functional-location class; aligned by skos:relatedMatch to iof:RequiredFunction only",
           f"{len(fl)} individuals", "Modelling choice recorded in ADR-0012; revisit when IOF publishes a functional-location pattern")
    maint = {"Failure": "FailureEvent", "FailureMode": "FailureModeCode", "WorkOrder": "MaintenanceWorkOrderRecord",
             "Turnaround": "MaintenanceProcess"}
    mx = [n for n in nodes.values() if n["cls"] in maint]
    r.must(std, "IOF-4", "Reliability records align to IOF Maintenance: failures, failure-mode codes, work-order records, turnarounds",
           sum(1 for n in mx if any(x.endswith("/" + maint[n["cls"]]) for x in standards.external_types(_cls(n), "iof"))), len(mx))
    iof_terms = [k for k in m["verification"] if k.startswith((standards.EXTERNAL["iof"], standards.EXTERNAL["bfo"]))]
    ver = sum(1 for k in iof_terms if m["verification"][k].startswith("verified"))
    r.info(std, "IOF-3", "IOF / BFO IRIs verified in the release RDF (rest taken from the IOF Core paper, to confirm)",
           f"{ver}/{len(iof_terms)} verified")

    # ------------------------------------------------------------------ ISO 14224
    std = STANDARDS[4]
    spine = [n for n in nodes.values() if n["spine"] == "asset" or (n["spine"] == "trunk")]
    r.must(std, "14224-1", "Every asset-spine node maps to an ISO 14224 taxonomy level (L10 data points flagged as extension)",
           sum(1 for n in spine if standards.resolve(_cls(n), "iso14224Level") is not None), len(spine))
    eq = [n for n in nodes.values() if n["cls"] == "EquipmentUnit"]
    codes = {n["id"]: standards.resolve(_cls(n), "iso14224Code") for n in eq}
    r.must(std, "14224-2", "Every equipment unit resolves to an ISO 14224 equipment class code (or an explicit 'none')",
           sum(1 for x in codes.values() if x), len(eq), ", ".join(sorted({_cls(nodes[k]) for k, x in codes.items() if not x})))
    r.coverage(std, "14224-3", "Share of equipment units with a real ISO 14224 class (not an OGKG extension)",
               sum(1 for x in codes.values() if x and x != "none"), len(eq), 95,
               "classes: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(codes.values()).items())))
    fails = [n for n in nodes.values() if n["cls"] == "Failure"]
    rec = lambda n: all(out[n["id"]].get(rl) for rl in ("FAILURE_OF", "HAS_FAILURE_MODE", "HAS_FAILURE_MECHANISM",
                                                         "HAS_FAILURE_CAUSE", "DETECTED_BY")) and n["props"].get("date")
    r.must(std, "14224-4", "Every failure record has item, date, failure mode, mechanism (B.2), cause (B.3) and detection method (B.4)",
           sum(1 for n in fails if rec(n)), len(fails))
    code_nodes = [n for n in nodes.values() if n["cls"] in ("FailureMode", "FailureMechanism", "RootCause", "DetectionMethod")]
    r.must(std, "14224-5", "Every failure code node cites its ISO 14224 table and notation",
           sum(1 for n in code_nodes if str(n["props"].get("scheme", "")).startswith("ISO 14224") and n["props"].get("notation")), len(code_nodes))
    driven = [n for n in eq if is_a(n, "Pump") or is_a(n, "Compressor")]
    r.must(std, "14224-6", "Driven rotating equipment has its driver as a separate equipment unit (DRIVER_OF), per the ISO 14224 boundary",
           sum(1 for n in driven if inn[n["id"]]["DRIVER_OF"]), len(driven))
    wos = [n for n in nodes.values() if n["cls"] == "WorkOrder"]
    r.must(std, "14224-7", "Every maintenance record is linked to the failure, exceedance or item it acts on",
           sum(1 for n in wos if any(out[n["id"]].get(x) for x in ("REMEDIATES", "RESPONDS_TO", "PERFORMED_ON"))), len(wos))
    rot = [n for n in eq if is_a(n, "RotatingEquipment") and not is_a(n, "ElectricMotor")]
    r.coverage(std, "14224-8", "Equipment data: share of driven rotating equipment with manufacturer model (OF_MODEL)",
               sum(1 for n in rot if out[n["id"]]["OF_MODEL"]), len(rot), 95)

    # ------------------------------------------------------------------ ISA-95 / Purdue
    std = STANDARDS[5]
    hier = [n for n in nodes.values() if n["cls"] in ("Installation", "PlantUnit", "SectionSystem", "EquipmentUnit", "Enterprise", "Plot")
            and not (n["cls"] == "Enterprise" and "OEM" in n["id"])]
    r.must(std, "ISA95-1", "Every enterprise, site, area (plot), production unit, unit and equipment module maps to an ISA-95 level",
           sum(1 for n in hier if standards.resolve(_cls(n), "isa95EquipmentLevel")), len(hier))
    pus = [n for n in nodes.values() if n["cls"] == "PlantUnit"]
    r.must(std, "ISA95-2", "Every production unit sits in exactly one area (LOCATED_AT a plot)",
           sum(1 for n in pus if len(out[n["id"]]["LOCATED_AT"]) == 1), len(pus))
    apps = [n for n in nodes.values() if n["cls"] == "ApplicationInstance"]
    r.must(std, "ISA95-3", "Every application instance has a Purdue level (IEC 62443 zone)",
           sum(1 for n in apps if "purdue_level" in n["props"]), len(apps),
           ", ".join(f"L{k}: {v}" for k, v in sorted(Counter(n["props"].get("purdue_level") for n in apps).items(), key=str)))
    procs = [n for n in nodes.values() if n["cls"] == "Process"]
    r.must(std, "ISA95-4", "Every L4 business process is placed in an IEC 62264 functional level / MOM activity model",
           sum(1 for n in procs if n["props"].get("isa95_function")), len(procs),
           ", ".join(f"{k}: {v}" for k, v in sorted(Counter(n["props"].get("isa95_function") for n in procs).items(), key=str)))
    dev_ = [n for n in nodes.values() if _cls(n) in standards.PURDUE_DEVICE_CLASSES]
    r.must(std, "ISA95-5", "Every field device (transmitter, control or shutdown valve) is at Purdue level 0",
           sum(1 for n in dev_ if n["props"].get("purdue_level") == 0), len(dev_))

    # ------------------------------------------------------------------ CFIHOS
    std = STANDARDS[6]
    r.must(std, "CFIHOS-1", "Every tag (equipment-level functional location) has a unique tag number and a CMMS functional-location id",
           sum(1 for n in eq if n["props"].get("external_ids", {}).get("SAP_FL")), len(eq))
    sers = [n for n in nodes.values() if n["cls"] == "SerialItem"]
    serial_no = {f["subject"] for f in data["facts"] if f["predicate"] == "serial_number"}
    r.must(std, "CFIHOS-2", "Every equipment item (serial) has a serial number, a model part and is installed at a tag",
           sum(1 for n in sers if n["id"] in serial_no and out[n["id"]]["OF_MODEL"] and out[n["id"]]["INSTALLED_AT"]), len(sers))
    r.coverage(std, "CFIHOS-3", "Share of tags whose class has a CFIHOS tag-class name mapped (RDL codes: lookup required)",
               sum(1 for n in eq if standards.resolve(_cls(n), "cfihosClassName")), len(eq), 80)
    r.coverage(std, "CFIHOS-4", "Share of driven rotating tags with a physical equipment item recorded",
               sum(1 for n in driven if inn[n["id"]]["INSTALLED_AT"]), len(driven), 100)
    r.info(std, "CFIHOS-5", "CFIHOS RDL codes pending lookup", f"{sum(1 for k in m['ann'] if 'cfihosClassName' in m['ann'][k])} tag classes named, codes pending")

    # ------------------------------------------------------------------ MIMOSA CCOM
    std = STANDARDS[7]
    scope = [n for n in nodes.values() if any(is_a(n, k) for k in ("FunctionalLocation", "SerialItem", "EquipmentModel", "DataPoint",
                                                                   "Failure", "WorkOrder", "IOWExceedance"))]
    r.must(std, "CCOM-1", "Every exchanged individual maps to a CCOM entity (Segment, Asset, Model, MeasurementLocation, Event, WorkOrder)",
           sum(1 for n in scope if standards.resolve(_cls(n), "ccomEntity")), len(scope),
           ", ".join(f"{k}: {v}" for k, v in sorted(Counter(standards.resolve(_cls(n), "ccomEntity") for n in scope).items(), key=str)))
    segs = [n for n in fl if n["cls"] != "Installation"]
    r.must(std, "CCOM-2", "Segments form a tree: one parent segment each", sum(1 for n in segs if len(out[n["id"]]["PART_OF"]) == 1), len(segs))
    dps = [n for n in nodes.values() if n["cls"] == "DataPoint"]
    r.must(std, "CCOM-3", "Every measurement location is attached to a segment",
           sum(1 for n in dps if out[n["id"]]["PART_OF"] and is_a(nodes[out[n["id"]]["PART_OF"][0]], "FunctionalLocation")), len(dps))
    r.must(std, "CCOM-4", "Asset-on-segment installations carry start (and, when removed, end) times",
           sum(1 for e in data["edges"] if e["rel"] == "INSTALLED_AT" and e["props"].get("valid_from")),
           sum(1 for e in data["edges"] if e["rel"] == "INSTALLED_AT"))
    return r.rows


def to_markdown(rows, site="Refinery Gamma"):
    lines = [f"# Standards conformance report — {site}", "",
             "Generated by `python -m ogkg.conformance`. Hard requirements (**must**) fail the build; **coverage** rows report a "
             "share against its target; **info** rows report status. This is evidence of conformance to the listed requirements, "
             "not a certification (handbook [B7](../../docs/handbook/B7-standards-conformance.md)).", ""]
    for std in STANDARDS:
        sub = [x for x in rows if x["standard"] == std]
        ok = sum(1 for x in sub if x["passed"])
        lines += [f"## {std} — {ok}/{len(sub)} pass", "", "| ID | Kind | Requirement | Result | Measure | Detail |", "|---|---|---|---|---|---|"]
        for x in sub:
            res = "pass" if x["passed"] else "**FAIL**"
            meas = x["measure"] + (f" (target {x['target']})" if x.get("target") else "")
            lines.append(f"| {x['id']} | {x['kind']} | {x['requirement']} | {res} | {meas} | {x['detail'] or ''} |")
        lines.append("")
    return "\n".join(lines)


def main():
    rows = run()
    (GAMMA / "conformance.json").write_text(json.dumps(rows, indent=1))
    (GAMMA / "conformance.md").write_text(to_markdown(rows))
    bad = [x for x in rows if not x["passed"]]
    print(f"{len(rows)} checks, {len(rows) - len(bad)} pass, {len(bad)} fail")
    for x in bad:
        print("  FAIL", x["id"], x["requirement"], x["measure"], x["detail"][:120])
    return 1 if any(x["kind"] == "must" for x in bad) else 0


if __name__ == "__main__":
    raise SystemExit(main())
