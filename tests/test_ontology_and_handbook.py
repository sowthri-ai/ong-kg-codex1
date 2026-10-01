"""Ontology syntax/consistency and handbook-claim tests.  Run: python -m unittest discover -s tests -v"""
import glob
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ogkg.kg import KG                                   # noqa: E402
from ogkg.turtle_lite import RDF, TurtleError, parse, parse_file  # noqa: E402
from ogkg import catalogue                                # noqa: E402

NS = "https://example.org/ogkg/core#"
VNS = "https://example.org/ogkg/vocab#"
kg = KG()


class Turtle(unittest.TestCase):
    def test_all_turtle_files_parse(self):
        files = glob.glob(str(ROOT / "ontology" / "*.ttl")) + glob.glob(str(ROOT / "exports" / "*.ttl"))
        self.assertGreaterEqual(len(files), 6)
        for f in files:
            with self.subTest(f=f):
                self.assertGreater(len(parse_file(f).triples), 50)

    def test_parser_rejects_bad_turtle(self):
        for bad in ["@prefix a: <x#> .\na:s a:p a:o", "@prefix a: <x#> .\nb:s a:p a:o .",
                    "@prefix a: <x#> .\na:s a:p [ a:q a:r ."]:
            with self.assertRaises(TurtleError):
                parse(bad)

    def test_every_term_used_is_declared(self):
        declared = set()
        for f in ("ogkg-core.ttl", "ogkg-vocab.ttl", "ogkg-shapes.ttl"):
            declared |= {s for s, p, o in parse_file(ROOT / "ontology" / f).triples if p == RDF + "type"}
        for f in glob.glob(str(ROOT / "ontology" / "*.ttl")):
            used = {x for t in parse_file(f).triples for x in t
                    if isinstance(x, str) and (x.startswith(NS) or x.startswith(VNS))}
            with self.subTest(f=f):
                self.assertEqual(sorted(used - declared), [])

    def test_every_object_property_has_lpg_type(self):
        t = parse_file(ROOT / "ontology" / "ogkg-core.ttl").triples
        objprops = {s for s, p, o in t if p == RDF + "type" and o == "http://www.w3.org/2002/07/owl#ObjectProperty" and s.startswith(NS)}
        typed = {s for s, p, o in t if p == NS + "lpgType"}
        # properties used only on reified Facts / hypotheses / bindings are exempt
        exempt = {NS + x for x in ("subject", "unit", "sourceSystem", "factOwner", "confidence", "method", "valueStatus",
                                   "hypSubject", "hypPredicate", "hypObject", "status", "evidence", "reviewedBy",
                                   "bindsEntity", "bindsTo", "bindingFacet", "bindingLevel", "inheritanceRule",
                                   "factStatus", "supersedes", "isa95Function",   # fact fields / node property in the LPG
                                   "partOf")}                                       # inferred closure of directPartOf, never asserted
        self.assertEqual(sorted(x.split("#")[1] for x in objprops - typed - exempt), [])

    def test_spine_levels_declared_0_to_10(self):
        t = parse_file(ROOT / "ontology" / "ogkg-core.ttl").triples
        lv = {int(o[1]) for s, p, o in t if p == NS + "levelNumber"}
        self.assertEqual(lv, set(range(11)))

    def test_catalogue_is_current(self):
        self.assertEqual((ROOT / "docs" / "handbook" / "F3-class-and-relation-catalogue.md").read_text(), catalogue.build())


class HandbookClaims(unittest.TestCase):
    """Numbers and lists quoted in the handbook must match the demo data."""

    def _hx_at(self, site):
        out = []
        for n in kg.nodes.values():
            if n["cls"] == "EquipmentUnit" and n["props"].get("eq_class") == "Heat exchanger" and kg.is_under(n["id"], site):
                out.append(n["id"])
        return sorted(out)

    def test_C4_inference_heat_exchangers_at_alpha(self):
        self.assertEqual(self._hx_at("SITE-ALPHA"), ["E-101A", "E-101B", "E-301"])

    def test_C4_rule_r07(self):
        flagged = set()
        for c in [n for n in kg.nodes.values() if n["cls"] == "CrudeCampaign"]:
            g = kg.targets(c["id"], "OF_GRADE")[0]
            if kg.value(g, "salt_content", 0) > 20:
                unit = kg.targets(c["id"], "PROCESSED_IN")[0]
                for sec in kg.children(unit):
                    if kg.nodes[sec]["name"] == "Overhead system":
                        for eq in kg.children(sec):
                            if "Carbon steel" in kg.nodes[eq]["props"].get("metallurgy", ""):
                                flagged.add(eq)
        self.assertEqual(flagged, {"E-101A", "E-101B"})
        self.assertIn("Titanium", kg.nodes["E-401A"]["props"]["metallurgy"])

    def test_C4_pump_shape_gap_is_p103_only(self):
        pumps = [n["id"] for n in kg.nodes.values() if n["props"].get("eq_class") == "Pump"]
        gaps = sorted(p for p in pumps if not all(kg.fact(p, k) for k in ("model", "seal_plan", "service_temperature")))
        self.assertEqual(gaps, ["P-103"])

    def test_B1_level_counts(self):
        s = kg.level_summary()
        self.assertEqual([r["count"] for r in s["asset"]], [1, 3, 3, 4, 12, 22, 21, 15, 15, 12, 19])
        self.assertEqual([r["count"] for r in s["process"]][2:], [4, 9, 9, 7, 7, 7, 7, 7, 13])

    def test_B5_cited_fact_ids(self):
        f = kg.facts_by_id["F-00110"]
        self.assertEqual((f["subject"], f["predicate"], f["value"], f["lineage"]), ("CMP-A1", "lp_uplift_total", 1890000, ["F-00107", "F-00109"]))
        f = kg.facts_by_id["F-00157"]
        self.assertEqual((f["subject"], f["value"], f["lineage"]), ("FL-001", 2050000, ["F-00155", "F-00156", "F-00005"]))
        self.assertEqual(kg.facts_by_id["F-00139"]["method"], "assumption")
        self.assertEqual((kg.facts_by_id["F-00097"]["subject"], kg.facts_by_id["F-00097"]["predicate"]), ("CR-DOBA", "tan"))

    def test_F4_dna_similarity_for_p201a(self):
        p = "P-201A"
        hot = lambda x: kg.value(x, "service_temperature") >= 340
        same = sorted(q for q in [n["id"] for n in kg.nodes.values() if kg.fact(n["id"], "model")]
                      if q != p and kg.value(q, "model") == kg.value(p, "model")
                      and kg.value(q, "seal_plan") == kg.value(p, "seal_plan") and hot(q) == hot(p))
        self.assertEqual(same, ["P-201B", "P-401A", "P-501"])

    def test_no_client_names_in_repo_docs(self):
        deny = re.compile(r"qatarenergy|aramco|adnoc|shell plc|exxon", re.I)
        for f in list((ROOT / "docs").rglob("*.md")) + [ROOT / "README.md"]:
            with self.subTest(f=str(f)):
                self.assertIsNone(deny.search(f.read_text()))


class Links(unittest.TestCase):
    def test_relative_links_and_anchors_resolve(self):
        def slug(h):
            h = h.strip().lower()
            h = re.sub(r"[^\w\- ]", "", h)
            return h.replace(" ", "-")
        md_files = list((ROOT / "docs").rglob("*.md")) + list(ROOT.glob("*.md")) + list((ROOT / "ontology").rglob("*.md"))
        for f in md_files:
            text = f.read_text()
            for target in re.findall(r"\]\(([^)\s]+)\)", text):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                path, _, anchor = target.partition("#")
                dest = (f.parent / path).resolve() if path else f
                with self.subTest(file=f.name, link=target):
                    self.assertTrue(dest.exists(), f"missing {dest}")
                    if anchor and dest.suffix == ".md":
                        heads = [slug(h) for h in re.findall(r"^#+ (.+)$", dest.read_text(), re.M)]
                        self.assertIn(anchor, heads)


if __name__ == "__main__":
    unittest.main()
