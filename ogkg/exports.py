"""
Platform-neutral exports.
  exports/og_vckg_ontology.ttl  — OWL classes, levels, relations (T-Box)
  exports/og_vckg_data.ttl      — instances + reified facts with provenance (A-Box)
  exports/neo4j/*.csv + load.cypher — labelled property graph
  explorer/kg_bundle.json       — graph + insights for the explorer UI

Run:  python -m ogkg.exports
"""
import csv
import json
import re
from pathlib import Path

from . import insights as ins
from .kg import KG
from .ontology import LEVELS, RELATIONS, CONTEXT_CLASSES

ROOT = Path(__file__).resolve().parent.parent
NS = "https://example.org/og-vckg#"


def _lit(v):
    if isinstance(v, bool):
        return f'"{str(v).lower()}"^^xsd:boolean'
    if isinstance(v, int):
        return f'"{v}"^^xsd:integer'
    if isinstance(v, float):
        return f'"{v}"^^xsd:decimal'
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def _iri(x):
    return "ogkg:" + re.sub(r"[^A-Za-z0-9_\-]", "_", x)


PREFIX = f"""@prefix ogkg: <{NS}> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
"""


def ontology_ttl():
    L = [PREFIX, "ogkg: a owl:Ontology ; rdfs:label \"O&G Value Chain Knowledge Graph ontology\" .\n",
         "ogkg:Level a owl:Class .", "ogkg:Fact a owl:Class ; rdfs:subClassOf prov:Entity .",
         "ogkg:level a owl:DatatypeProperty .", "ogkg:spine a owl:DatatypeProperty .", ""]
    for spine, lv in LEVELS.items():
        L.append(f"ogkg:{spine.title()}SpineNode a owl:Class .")
        for n, (cls, desc, std) in lv.items():
            L.append(f"ogkg:{cls} a owl:Class ; rdfs:subClassOf ogkg:{spine.title()}SpineNode ; "
                     f"rdfs:comment {_lit(desc)} ; ogkg:level {n} ; ogkg:alignedTo {_lit(std)} .")
    for grp, classes in CONTEXT_CLASSES.items():
        for c in classes:
            L.append(f"ogkg:{c} a owl:Class ; ogkg:contextGroup {_lit(grp)} .")
    for rel, desc in RELATIONS.items():
        L.append(f"ogkg:{rel} a owl:ObjectProperty ; rdfs:comment {_lit(desc)} .")
    L.append("ogkg:PART_OF a owl:TransitiveProperty .")
    for p in ["subject", "predicate", "value", "unit", "asOf", "sourceSystem", "sourceRef", "owner", "confidence", "method"]:
        L.append(f"ogkg:{p} a owl:DatatypeProperty ; rdfs:domain ogkg:Fact .")
    L.append("ogkg:derivedFrom rdfs:subPropertyOf prov:wasDerivedFrom .")
    return "\n".join(L) + "\n"


def data_ttl(kg):
    L = [PREFIX]
    for n in kg.nodes.values():
        parts = [f"{_iri(n['id'])} a ogkg:{n['cls']}", f"rdfs:label {_lit(n['name'])}", f"ogkg:spine {_lit(n['spine'])}"]
        if n["level"] is not None:
            parts.append(f"ogkg:level {n['level']}")
        for k, v in n["props"].items():
            if v is not None:
                parts.append(f"ogkg:{k} {_lit(v)}")
        L.append(" ;\n    ".join(parts) + " .")
    for e in kg.edges:
        L.append(f"{_iri(e['source'])} ogkg:{e['rel']} {_iri(e['target'])} .")
    for f in kg.fact_list:
        parts = [f"{_iri(f['id'])} a ogkg:Fact", f"ogkg:subject {_iri(f['subject'])}", f"ogkg:predicate {_lit(f['predicate'])}",
                 f"ogkg:value {_lit(f['value'])}", f"ogkg:unit {_lit(f['unit'])}", f"ogkg:asOf \"{f['as_of']}\"^^xsd:date",
                 f"ogkg:sourceSystem {_lit(f['source_system'])}", f"ogkg:sourceRef {_lit(f['source_ref'])}",
                 f"ogkg:owner {_iri(f['owner'])}" if f["owner"] else "ogkg:owner \"\"",
                 f"ogkg:confidence {_lit(f['confidence'])}", f"ogkg:method {_lit(f['method'])}"]
        parts += [f"ogkg:derivedFrom {_iri(x)}" for x in f["lineage"]]
        L.append(" ;\n    ".join(parts) + " .")
    return "\n".join(L) + "\n"


def neo4j(kg, out):
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "nodes.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id:ID", "name", "spine", "level:int", ":LABEL", "props_json"])
        for n in kg.nodes.values():
            w.writerow([n["id"], n["name"], n["spine"], "" if n["level"] is None else n["level"],
                        f"Entity;{n['cls']}", json.dumps(n["props"])])
        for f in kg.fact_list:
            w.writerow([f["id"], f["predicate"], "fact", "", "Fact", json.dumps(f)])
    with open(out / "edges.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([":START_ID", ":END_ID", ":TYPE"])
        for e in kg.edges:
            w.writerow([e["source"], e["target"], e["rel"]])
        for f in kg.fact_list:
            w.writerow([f["subject"], f["id"], "HAS_FACT"])
            for x in f["lineage"]:
                w.writerow([f["id"], x, "DERIVED_FROM"])
    (out / "load.cypher").write_text("""// Option A (bulk): neo4j-admin database import full --nodes=nodes.csv --relationships=edges.csv og-kg
// Option B (LOAD CSV, files in the import dir):
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS r
CALL apoc.create.node(split(r[':LABEL'], ';'), {id: r['id:ID'], name: r.name, spine: r.spine,
     level: toIntegerOrNull(r['level:int']), props: r.props_json}) YIELD node RETURN count(node);
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS r
MATCH (a {id: r[':START_ID']}), (b {id: r[':END_ID']})
CALL apoc.create.relationship(a, r[':TYPE'], {}, b) YIELD rel RETURN count(rel);

// Example: L0 -> L10 path for a sensor tag
// MATCH p=(t {id:'T-CDU1-CL'})-[:PART_OF*]->(root {id:'OG'}) RETURN p;
// Example: decisions governing assets with failures but consuming no reliability/integrity data
// MATCH (d:DecisionPoint)-[:GOVERNS]->(a)<-[:PART_OF*0..6]-(x)<-[:FAILURE_OF]-(f:Failure)
// WHERE NOT EXISTS { MATCH (d)-[:CONSUMES]->(de) WHERE de.props CONTAINS '"domain": "reliability"'
//                    OR de.props CONTAINS '"domain": "integrity"' }
// RETURN d.name, count(DISTINCT f);
""")


def bundle(kg):
    results = ins.run_all(kg)
    return dict(meta=kg.meta, levels=kg.level_summary(), relations=RELATIONS,
                nodes=list(kg.nodes.values()), edges=kg.edges, facts=kg.fact_list, insights=results)


def main():
    kg = KG()
    ex = ROOT / "exports"; ex.mkdir(exist_ok=True)
    (ex / "og_vckg_ontology.ttl").write_text(ontology_ttl())
    (ex / "og_vckg_data.ttl").write_text(data_ttl(kg))
    neo4j(kg, ex / "neo4j")
    (ROOT / "explorer").mkdir(exist_ok=True)
    payload = json.dumps(bundle(kg), default=list, separators=(",", ":"))
    (ROOT / "explorer" / "kg_bundle.json").write_text(payload)
    tpl = (ROOT / "explorer" / "template.html").read_text()
    safe = payload.replace("</", "<\\/")
    (ROOT / "explorer" / "og_value_chain_kg.html").write_text(tpl.replace("__KG_BUNDLE__", safe))
    print("exports written:", sorted(str(p.relative_to(ROOT)) for p in ex.rglob("*") if p.is_file()))


if __name__ == "__main__":
    main()
