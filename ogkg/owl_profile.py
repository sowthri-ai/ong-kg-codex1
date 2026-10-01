"""
OWL 2 DL structural profile check for the OGKG ontology modules and, optionally, exported data.

It checks the RDF graph against the parts of the OWL 2 DL restrictions (OWL 2 Structural
Specification §3–5 and the RDF-to-structure mapping) that matter for this model:

  D1  every non-built-in predicate is declared as exactly one property type
  D2  no property punning (object / datatype / annotation on the same IRI)
  D3  every IRI used as a class (rdf:type object, subClassOf, domain, object-property range,
      disjointness, equivalence) is declared owl:Class (or is a built-in class)
  D4  object-property values are IRIs or blank nodes; datatype-property values are literals
  D5  datatype-property ranges are datatypes; object-property ranges are classes
  D6  non-simple (transitive) properties are not functional, inverse-functional, irreflexive,
      asymmetric or used in cardinality restrictions
  D7  reserved vocabulary (rdf:, rdfs:, owl:, xsd:) is not redefined
  D8  literal datatypes are in the OWL 2 datatype map
  D9  every ontology document has an owl:Ontology header with owl:versionIRI

Known, documented deviation (ADR-0012): xsd:date literals are outside the OWL 2 datatype map.
They are reported as `deviations`, not `violations`; DL reasoners are run with
unsupported-datatype tolerance (HermiT `ignoreUnsupportedDatatypes`, ELK ignores datatypes).

This is a structural checker, not a reasoner. CI also runs a DL reasoner (see
.github/workflows/ci.yml) where one can be installed.
"""
from collections import defaultdict
from pathlib import Path

from .turtle_lite import RDF, XSD, parse_file

ROOT = Path(__file__).resolve().parent.parent
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
TYPE = RDF + "type"

RESERVED = (RDF, RDFS, OWL, XSD)
BUILTIN_CLASSES = {OWL + "Thing", OWL + "Nothing", RDFS + "Literal"}
BUILTIN_PREDICATES = {
    TYPE, RDFS + "subClassOf", RDFS + "subPropertyOf", RDFS + "domain", RDFS + "range", RDFS + "label",
    RDFS + "comment", RDFS + "seeAlso", RDFS + "isDefinedBy", OWL + "equivalentClass", OWL + "equivalentProperty",
    OWL + "disjointWith", OWL + "inverseOf", OWL + "imports", OWL + "versionIRI", OWL + "versionInfo",
    OWL + "priorVersion", OWL + "deprecated", OWL + "members", OWL + "onProperty", OWL + "someValuesFrom",
    OWL + "allValuesFrom", OWL + "hasValue", OWL + "cardinality", OWL + "minCardinality", OWL + "maxCardinality",
    OWL + "qualifiedCardinality", OWL + "minQualifiedCardinality", OWL + "maxQualifiedCardinality",
    OWL + "onClass", OWL + "unionOf", OWL + "intersectionOf", OWL + "complementOf", OWL + "oneOf",
    OWL + "propertyDisjointWith", OWL + "sameAs", OWL + "differentFrom", OWL + "distinctMembers",
    RDF + "first", RDF + "rest", OWL + "annotatedSource", OWL + "annotatedProperty", OWL + "annotatedTarget",
    OWL + "backwardCompatibleWith", OWL + "incompatibleWith",
}
# OWL 2 datatype map (Structural Specification §4) — the subset that can occur here
DATATYPE_MAP = {RDF + "PlainLiteral", RDF + "XMLLiteral", RDFS + "Literal", OWL + "real", OWL + "rational"} | {
    XSD + t for t in ("decimal", "integer", "nonNegativeInteger", "nonPositiveInteger", "positiveInteger",
                      "negativeInteger", "long", "int", "short", "byte", "unsignedLong", "unsignedInt",
                      "unsignedShort", "unsignedByte", "double", "float", "string", "normalizedString", "token",
                      "language", "Name", "NCName", "NMTOKEN", "boolean", "hexBinary", "base64Binary", "anyURI",
                      "dateTime", "dateTimeStamp")}
DEVIATION_DATATYPES = {XSD + "date"}
CARDINALITY = {OWL + p for p in ("cardinality", "minCardinality", "maxCardinality", "qualifiedCardinality",
                                 "minQualifiedCardinality", "maxQualifiedCardinality")}

ONTOLOGY_MODULES = [ROOT / "ontology" / "ogkg-core.ttl", ROOT / "ontology" / "ogkg-vocab.ttl",
                    ROOT / "ontology" / "ext" / "ogkg-cdu.ttl"] + sorted((ROOT / "ontology" / "alignments").glob("*.ttl"))


def _is_lit(o):
    return isinstance(o, tuple)


def _is_res(o):
    return isinstance(o, str)


def check(paths=None, data_paths=()):
    """Return (violations, deviations, stats). Each violation is (rule, subject, detail)."""
    paths = [Path(p) for p in (paths or ONTOLOGY_MODULES)]
    triples, headers = [], {}
    for p in list(paths) + [Path(x) for x in data_paths]:
        ts = parse_file(p).triples
        triples += ts
        if p in paths:
            onts = [s for s, pr, o in ts if pr == TYPE and o == OWL + "Ontology"]
            headers[p.name] = (onts, any(pr == OWL + "versionIRI" and s in onts for s, pr, o in ts))
    types = defaultdict(set)
    for s, p, o in triples:
        if p == TYPE and _is_res(o):
            types[s].add(o)
    kinds = {k: {s for s, ts in types.items() if OWL + k in ts}
             for k in ("ObjectProperty", "DatatypeProperty", "AnnotationProperty", "Class", "TransitiveProperty",
                       "FunctionalProperty", "InverseFunctionalProperty", "IrreflexiveProperty", "AsymmetricProperty")}
    datatypes = {s for s, ts in types.items() if RDFS + "Datatype" in ts} | DATATYPE_MAP | DEVIATION_DATATYPES
    classes = kinds["Class"] | BUILTIN_CLASSES
    obj, dat, ann = kinds["ObjectProperty"], kinds["DatatypeProperty"], kinds["AnnotationProperty"]
    v, dev = [], []

    # D9 headers
    for name, (onts, has_version) in headers.items():
        if not onts:
            v.append(("D9", name, "no owl:Ontology header"))
        elif not has_version:
            v.append(("D9", name, "owl:Ontology has no owl:versionIRI"))

    # D2 punning between property types; class/datatype punning
    for a, b, an, bn in ((obj, dat, "object", "datatype"), (obj, ann, "object", "annotation"), (dat, ann, "datatype", "annotation")):
        for x in sorted(a & b):
            v.append(("D2", x, f"declared both {an} and {bn} property"))
    for x in sorted(classes & (datatypes - DATATYPE_MAP - DEVIATION_DATATYPES)):
        v.append(("D2", x, "declared both class and datatype"))

    # D7 reserved vocabulary redefined
    for s, ts in types.items():
        if _is_res(s) and s.startswith(RESERVED) and ts & {OWL + "Class", OWL + "ObjectProperty", OWL + "DatatypeProperty", OWL + "AnnotationProperty", RDFS + "Datatype"}:
            v.append(("D7", s, "reserved vocabulary redeclared"))

    reported = set()
    for s, p, o in triples:
        # D1 predicate declared
        if p not in BUILTIN_PREDICATES and p not in obj | dat | ann and (p, "D1") not in reported:
            reported.add((p, "D1"))
            v.append(("D1", p, "predicate not declared as an object, datatype or annotation property"))
        # D3 class usage
        cls_slots = []
        if p == TYPE and _is_res(o) and not o.startswith(RESERVED):
            cls_slots.append(o)
        if p in (RDFS + "subClassOf", OWL + "equivalentClass", OWL + "disjointWith"):
            cls_slots += [x for x in (s, o) if _is_res(x) and not x.startswith("_:")]
        if p == RDFS + "domain" and _is_res(o) and not o.startswith("_:"):
            cls_slots.append(o)
        if p == RDFS + "range" and s in obj and _is_res(o) and not o.startswith("_:"):
            cls_slots.append(o)
        for c in cls_slots:
            if c not in classes and (c, "D3") not in reported:
                reported.add((c, "D3"))
                v.append(("D3", c, f"used as a class (via {p.split('#')[-1]}) but not declared owl:Class"))
        # D4 value kinds
        if p in obj and _is_lit(o):
            v.append(("D4", s, f"{p.split('#')[-1]} is an object property but has literal {o[0]!r}"))
        if p in dat and not _is_lit(o):
            v.append(("D4", s, f"{p.split('#')[-1]} is a datatype property but has IRI {o}"))
        # D5 ranges
        if p == RDFS + "range" and s in dat and _is_res(o) and o not in datatypes:
            v.append(("D5", s, f"datatype property range {o} is not a datatype"))
        if p == RDFS + "range" and s in obj and _is_res(o) and o in datatypes:
            v.append(("D5", s, f"object property range {o} is a datatype"))
        # D8 literal datatypes
        if _is_lit(o) and len(o) > 2 and o[2]:
            if o[2] in DEVIATION_DATATYPES:
                dev.append(("D8", s, o[2]))
            elif o[2] not in datatypes and not o[2].startswith(("@", "lang:")):
                v.append(("D8", s, f"literal datatype {o[2]} not in the OWL 2 datatype map"))
        if p == RDFS + "range" and o in DEVIATION_DATATYPES:
            dev.append(("D8", s, o))

    # D6 non-simple properties: transitive, or with a transitive sub-property chain
    subprops = defaultdict(set)
    for s, p, o in triples:
        if p == RDFS + "subPropertyOf":
            subprops[o].add(s)
    nonsimple = set(kinds["TransitiveProperty"])
    changed = True
    while changed:
        changed = False
        for sup, subs in subprops.items():
            if sup not in nonsimple and subs & nonsimple:
                nonsimple.add(sup)
                changed = True
    for x in sorted(nonsimple):
        for k in ("FunctionalProperty", "InverseFunctionalProperty", "IrreflexiveProperty", "AsymmetricProperty"):
            if x in kinds[k]:
                v.append(("D6", x, f"non-simple (transitive) property declared {k}"))
    restr_on = {s: o for s, p, o in triples if p == OWL + "onProperty"}
    for s, p, o in triples:
        if p in CARDINALITY and restr_on.get(s) in nonsimple:
            v.append(("D6", restr_on[s], "non-simple property used in a cardinality restriction"))

    stats = {"triples": len(triples), "classes": len(kinds["Class"]), "object_properties": len(obj),
             "datatype_properties": len(dat), "annotation_properties": len(ann), "modules": len(paths)}
    return v, dev, stats


def main(argv=None):
    import sys
    argv = sys.argv[1:] if argv is None else argv
    v, dev, stats = check(data_paths=argv)
    print(f"OWL 2 DL profile: {stats}")
    print(f"  {len(v)} violation(s); {len(dev)} documented deviation(s) (xsd:date, ADR-0012)")
    for x in v[:60]:
        print("  ", x)
    return 1 if v else 0


if __name__ == "__main__":
    raise SystemExit(main())
