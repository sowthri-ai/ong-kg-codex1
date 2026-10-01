"""Standards conformance: OWL 2 DL profile, alignment modules, conformance checks and mutation tests."""
import json
import tempfile
import unittest
from pathlib import Path

from ogkg import conformance, owl_profile, shacl_lite, standards

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cdu-gamma"
TTL = [DATA / "structure.ttl", DATA / "information.ttl"]
ROWS = conformance.run()


class OwlProfile(unittest.TestCase):
    def test_ontology_modules_are_owl2_dl(self):
        v, dev, stats = owl_profile.check()
        self.assertEqual(v, [])
        self.assertGreaterEqual(stats["modules"], 9)

    def test_site_data_is_owl2_dl(self):
        v, dev, stats = owl_profile.check(data_paths=TTL)
        self.assertEqual(v, [])
        self.assertTrue(all(d[0] == "D8" and d[2].endswith("#date") for d in dev), "only xsd:date may deviate (ADR-0012)")

    def test_profile_catches_violations(self):
        bad = ('@prefix ogkg: <https://example.org/ogkg/core#> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\n'
               '@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n'
               '<urn:x> a owl:Ontology .\n'                                   # D9 no versionIRI
               'ogkg:P a owl:ObjectProperty , owl:DatatypeProperty .\n'       # D2 punning
               'ogkg:T a owl:ObjectProperty , owl:TransitiveProperty , owl:FunctionalProperty .\n'   # D6
               'ogkg:a ogkg:undeclared ogkg:b .\n'                             # D1
               'ogkg:a a ogkg:NoSuchClass .\n')                                # D3
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "bad.ttl"
            f.write_text(bad)
            v, _, _ = owl_profile.check(paths=owl_profile.ONTOLOGY_MODULES + [f])
        self.assertEqual({x[0] for x in v}, {"D1", "D2", "D3", "D6", "D9"})


class Alignments(unittest.TestCase):
    def test_functional_vs_physical(self):
        self.assertIn("https://example.org/ogkg/core#FunctionalLocation", standards.ancestors("CentrifugalPump"))
        self.assertNotIn("https://example.org/ogkg/core#PhysicalAsset", standards.ancestors("CentrifugalPump"))
        self.assertIn("https://example.org/ogkg/core#PhysicalAsset", standards.ancestors("SerialItem"))

    def test_codes_resolve_through_the_class_hierarchy(self):
        self.assertEqual(standards.resolve("CentrifugalPump", "iso14224Code"), "PU")
        self.assertEqual(standards.resolve("ReliefDevice", "iso14224Code"), "VA")
        self.assertEqual(standards.resolve("Desalter", "iso14224Code"), "VE")
        self.assertEqual(standards.resolve("CrudeDistillationUnit", "isa95EquipmentLevel"), "ProductionUnit")
        self.assertEqual(standards.resolve("TankFarm", "isa95EquipmentLevel"), "StorageZone")
        self.assertEqual(standards.resolve("CentrifugalPump", "ccomEntity"), "Segment")
        self.assertEqual(standards.resolve("SerialItem", "ccomEntity"), "Asset")
        self.assertEqual(standards.resolve("SerialItem", "cfihosConcept"), "Equipment")
        self.assertEqual(standards.resolve("EquipmentUnit", "cfihosConcept"), "Tag")

    def test_external_superclasses(self):
        lis = standards.external_types("CentrifugalPump", "lis14")
        self.assertTrue(any(x.endswith("/FunctionalObject") for x in lis))
        iof = standards.external_types("Failure", "iof")
        self.assertTrue(any(x.endswith("/FailureEvent") for x in iof))

    def test_every_external_term_has_a_verification_status(self):
        m = standards.model()
        used = {x for xs in m["ext_super"].values() for x in xs if x.startswith(tuple(standards.EXTERNAL.values()))}
        self.assertEqual(sorted(u for u in used if u not in m["verification"]), [])

    def test_no_competitor_or_client_names_in_alignments(self):
        text = " ".join(p.read_text().lower() for p in standards.ALIGN_DIR.glob("*.ttl"))
        for word in ("mckinsey", "deloitte", "accenture", "kpmg", "pwc"):
            self.assertNotIn(word, text)


class Conformance(unittest.TestCase):
    def test_every_must_check_passes(self):
        bad = [(r["id"], r["measure"], r["detail"]) for r in ROWS if r["kind"] == "must" and not r["passed"]]
        self.assertEqual(bad, [])

    def test_every_coverage_check_meets_its_target(self):
        bad = [(r["id"], r["measure"], r["target"]) for r in ROWS if r["kind"] == "coverage" and not r["passed"]]
        self.assertEqual(bad, [])

    def test_all_eight_standards_are_checked(self):
        self.assertEqual({r["standard"] for r in ROWS}, set(conformance.STANDARDS))
        for std in conformance.STANDARDS:
            self.assertGreaterEqual(sum(1 for r in ROWS if r["standard"] == std and r["kind"] == "must"), 2, std)

    def test_report_matches_committed_file(self):
        self.assertEqual(json.loads((DATA / "conformance.json").read_text()), ROWS)

    def test_checks_catch_a_broken_failure_record_and_wrong_range(self):
        mut = ('@prefix gamma: <https://example.org/ogkg/data/gamma#> .\n@prefix ogkg: <https://example.org/ogkg/core#> .\n'
               'gamma:X-FAIL a ogkg:Failure ; ogkg:failureOf gamma:P-101A .\n'
               'gamma:X-SER a ogkg:SerialItem ; ogkg:installedAt gamma:FCC-1 .\n'
               'gamma:P-101A ogkg:protects gamma:FCC-1 .\n')
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "mut.ttl"
            f.write_text(mut)
            v, _ = shacl_lite.validate(TTL + [f])
        shapes = {x[0] for x in v}
        self.assertTrue({"FailureRecordShape", "SerialItemShape", "DomainShape", "RangeShape"} <= shapes, shapes)


if __name__ == "__main__":
    unittest.main()
