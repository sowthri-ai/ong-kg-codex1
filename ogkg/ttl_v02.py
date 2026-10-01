"""
Export a prototype graph (kg.json) to RDF in the v0.2 ontology vocabulary, split by sector:
  <out>/structure.ttl    Sector 1b — entities, hierarchy, cross-links, groupings, reference links
  <out>/information.ttl  Sector 2  — facts, events, campaigns, cached design values

Relationship names are mapped through the ogkg:lpgType annotations in the ontology, so the
export fails loudly if the data uses a relationship the ontology does not define.
"""
import json
import re
from pathlib import Path

from .turtle_lite import parse_file

ROOT = Path(__file__).resolve().parent.parent
CORE = "https://example.org/ogkg/core#"
ONTOLOGY_FILES = [ROOT / "ontology" / "ogkg-core.ttl", ROOT / "ontology" / "ext" / "ogkg-cdu.ttl"]
STATUS = {"current": "vocab:Current", "superseded": "vocab:Superseded", "retracted": "vocab:Retracted"}
SENS = {"public": "vocab:Public", "internal": "vocab:Internal", "confidential": "vocab:Confidential", "restricted": "vocab:Restricted"}

CONF = {"high": "vocab:High", "medium": "vocab:Medium", "low": "vocab:Low"}
METHOD = {m: "vocab:" + m.title() for m in ("measured", "recorded", "calculated", "declared", "indicative", "assumption")}
METALLURGY = {"CarbonSteel": "vocab:CarbonSteel", "Cr5": "vocab:Cr5", "Cr9": "vocab:Cr9", "Titanium": "vocab:Titanium",
              "SS410": "vocab:SS410", "Alloy400": "vocab:Alloy400", "SS316": "vocab:SS316", "Cr225Mo": "vocab:Cr225Mo",
              "Cr125Mo": "vocab:Cr125Mo", "SS347": "vocab:SS347", "Alloy825": "vocab:Alloy825"}


def lpg_map():
    m = {}
    for f in ONTOLOGY_FILES:
        for s, p, o in parse_file(f).triples:
            if p == CORE + "lpgType":
                m[o[1]] = "ogkg:" + s[len(CORE):]
    return m


def lit(v):
    if isinstance(v, bool):
        return f'"{str(v).lower()}"^^xsd:boolean'
    if isinstance(v, int):
        return f'"{v}"^^xsd:integer'
    if isinstance(v, float):
        return f'"{v}"^^xsd:decimal'
    s = str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return f'"{s}"'


def export(kg_json, out_dir, ns_prefix, ns_iri):
    data = json.loads(Path(kg_json).read_text())
    nodes = {n["id"]: n for n in data["nodes"]}
    rel = lpg_map()
    missing = sorted({e["rel"] for e in data["edges"]} - set(rel))
    if missing:
        raise ValueError(f"relationships not defined in the ontology: {missing}")
    for n in nodes.values():
        if not re.fullmatch(r"[A-Za-z0-9_\-]+(?:\.[A-Za-z0-9_\-]+)*", n["id"]):
            raise ValueError(f"id not IRI-safe: {n['id']}")
    iri = lambda x: f"{ns_prefix}:{x}"
    head = (f"@prefix {ns_prefix}: <{ns_iri}> .\n@prefix ogkg: <{CORE}> .\n@prefix vocab: <https://example.org/ogkg/vocab#> .\n"
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
            "@prefix prov: <http://www.w3.org/ns/prov#> .\n\n")
    s2 = {nid for nid, n in nodes.items() if n["props"].get("sector") == "2"}

    S, I = [head + "# Sector 1b — structure\n"], [head + "# Sector 2 — information\n"]
    for n in nodes.values():
        cls = n["props"].get("onto_class") or n["cls"]
        parts = [f"{iri(n['id'])} a ogkg:{cls}", f"rdfs:label {lit(n['name'])}"]
        if n["level"] is not None and n["spine"] in ("asset", "process", "trunk"):
            parts.append(f"ogkg:hasLevel ogkg:L{n['level']}")
        p = n["props"]
        if n["cls"] == "EquipmentUnit":
            parts.append(f"ogkg:eqClass {lit(p.get('eq_class', ''))}")
        if n["cls"] == "PlantUnit" and p.get("model_depth"):
            parts.append(f"ogkg:modelDepth {lit(p['model_depth'])}")
        if p.get("train"):
            parts.append(f"ogkg:trainId {lit(p['train'])}")
        if n["cls"] == "DataPoint":
            parts += [f"ogkg:tagType {lit(p.get('tag_type', ''))}", f"ogkg:dataPointKind {lit(p.get('kind', ''))}",
                      f"ogkg:unitLabel {lit(p.get('unit', ''))}"]
        if n["cls"] == "DataElement" and p.get("maps_to_predicate"):
            parts.append(f"ogkg:mapsToPredicate {lit(p['maps_to_predicate'])}")
        if n["cls"] in ("Failure", "WorkOrder", "IOWExceedance") and p.get("date"):
            parts.append(f'ogkg:eventDate "{p["date"]}"^^xsd:date')
        if "purdue_level" in p:
            parts.append(f"ogkg:purdueLevel {lit(float(p['purdue_level']))}")
        if p.get("isa95_function"):
            parts.append(f"ogkg:isa95Function vocab:{p['isa95_function']}")
        if n["cls"] == "CrudeCampaign":
            parts += [f'ogkg:windowStart "{p["start"]}"^^xsd:date', f'ogkg:windowEnd "{p["end"]}"^^xsd:date']
        (I if n["id"] in s2 else S).append(" ;\n    ".join(parts) + " .")

    for e in data["edges"]:
        line = f"{iri(e['source'])} {rel[e['rel']]} {iri(e['target'])} ."
        (I if e["source"] in s2 or e["target"] in s2 else S).append(line)

    # cached design values on structure nodes (values are Sector 2)
    facts_by = {}
    for f in data["facts"]:
        facts_by.setdefault(f["subject"], {})[f["predicate"]] = f["value"]
    for nid, fs in facts_by.items():
        c = []
        if "seal_plan" in fs:
            c.append(f"ogkg:sealPlan vocab:{fs['seal_plan']}")
        if "service_temperature" in fs:
            c.append(f"ogkg:serviceTemperature {lit(float(fs['service_temperature']))}")
        if fs.get("tube_metallurgy") in METALLURGY:
            c.append(f"ogkg:tubeMetallurgy {METALLURGY[fs['tube_metallurgy']]}")
        if "design_temperature" in fs:
            c.append(f"ogkg:designTemperature {lit(float(fs['design_temperature']))}")
        if "design_pressure" in fs:
            c.append(f"ogkg:designPressure {lit(float(fs['design_pressure']))}")
        if "tan" in fs:
            c.append(f"ogkg:tan {lit(float(fs['tan']))}")
        if "salt_content" in fs:
            c.append(f"ogkg:saltContent {lit(float(fs['salt_content']))}")
        if "nelson_factor" in fs:
            c.append(f"ogkg:nelsonFactor {lit(float(fs['nelson_factor']))}")
        if "freshness_sla" in fs:
            c.append(f"ogkg:freshnessSlaHours {lit(float(fs['freshness_sla']))}")
        if "sampling_interval" in fs:
            c.append(f"ogkg:samplingIntervalHours {lit(float(fs['sampling_interval']))}")
        if c:
            I.append(f"{iri(nid)} " + " ;\n    ".join(c) + " .")

    for f in data["facts"]:
        parts = [f"{iri(f['id'])} a ogkg:Fact", f"ogkg:subject {iri(f['subject'])}", f"ogkg:predicateKey {lit(f['predicate'])}",
                 f"ogkg:value {lit(f['value'])}", f'ogkg:asOf "{f["as_of"]}"^^xsd:date',
                 f"ogkg:sourceSystemName {lit(f['source_system'])}", f"ogkg:confidence {CONF[f['confidence']]}",
                 f"ogkg:method {METHOD[f['method']]}"]
        if f["unit"]:
            parts.append(f"ogkg:unitLabel {lit(f['unit'])}")
        if f["source_ref"]:
            parts.append(f"ogkg:sourceRef {lit(f['source_ref'])}")
        if f["owner"]:
            parts.append(f"ogkg:factOwner {iri(f['owner'])}")
        parts += [f"ogkg:derivedFrom {iri(x)}" for x in f["lineage"]]
        if f.get("valid_from"):
            parts.append(f'ogkg:validFrom "{f["valid_from"]}"^^xsd:date')
        if f.get("valid_to"):
            parts.append(f'ogkg:validTo "{f["valid_to"]}"^^xsd:date')
        if f.get("recorded_at"):
            parts.append(f'prov:generatedAtTime "{f["recorded_at"]}"^^xsd:dateTime')
        parts.append(f"ogkg:factStatus {STATUS[f.get('status', 'current')]}")
        if f.get("supersedes"):
            parts.append(f"ogkg:supersedes {iri(f['supersedes'])}")
        if f.get("sensitivity"):
            parts.append(f"ogkg:sensitivity {SENS[f['sensitivity']]}")
        if f.get("basis"):
            parts.append(f"ogkg:valueBasis {lit(f['basis'])}")
        if f.get("value_low") is not None:
            parts += [f"ogkg:valueLow {lit(float(f['value_low']))}", f"ogkg:valueHigh {lit(float(f['value_high']))}"]
        I.append(" ;\n    ".join(parts) + " .")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "structure.ttl").write_text("\n".join(S) + "\n")
    (out / "information.ttl").write_text("\n".join(I) + "\n")
    return out / "structure.ttl", out / "information.ttl"


if __name__ == "__main__":
    for p in export(ROOT / "data" / "cdu-gamma" / "kg.json", ROOT / "data" / "cdu-gamma", "gamma",
                    "https://example.org/ogkg/data/gamma#"):
        print("wrote", p.relative_to(ROOT))
