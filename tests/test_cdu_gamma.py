"""Completeness, symmetry and validity tests for the Refinery Gamma reference model (CDU and full-depth units)."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ogkg import cdu_gamma, cdu_insights, shacl_lite, ttl_v02  # noqa: E402
from ogkg.insight_snapshot import snapshot                    # noqa: E402
from ogkg.kg import KG                                         # noqa: E402
from ogkg.ontology import RELATIONS                            # noqa: E402

DATA = ROOT / "data" / "cdu-gamma"
kg = KG(DATA / "kg.json")
EQ = [n for n in kg.nodes.values() if n["cls"] == "EquipmentUnit"]
TAGS = [n for n in kg.nodes.values() if n["cls"] == "DataPoint"]


class Reproducible(unittest.TestCase):
    def test_committed_model_matches_builder(self):
        cdu_gamma._tag.counter.clear()
        b, reg, tags = cdu_gamma.build()
        snapshot(b, cdu_gamma.to_json)
        self.assertEqual((len(b.nodes), len(b.edges), len(b.facts)), (len(kg.nodes), len(kg.edges), len(kg.fact_list)))
        self.assertEqual({f["id"] for f in b.facts}, set(kg.facts_by_id), "fact IDs must be stable across rebuilds")


class Hierarchy(unittest.TestCase):
    def test_every_spine_node_reaches_L0_with_levels_decreasing(self):
        for n in kg.nodes.values():
            if n["spine"] in ("asset", "process", "trunk") and n["id"] != "OG":
                with self.subTest(n=n["id"]):
                    self.assertEqual(len(kg.targets(n["id"], "PART_OF")), 1)
                    self.assertEqual(kg.ancestors(n["id"])[-1], "OG")
                    self.assertLess(kg.nodes[kg.parent(n["id"])]["level"], n["level"])

    def test_capacity_is_two_250_kbpd_trains(self):
        self.assertEqual(kg.value("SITE-GAMMA", "crude_capacity"), 500)
        self.assertEqual([kg.value(u, "design_capacity") for u in ("CDU-A", "CDU-B")], [250, 250])

    def test_each_train_has_all_twelve_sections(self):
        for tr in ("A", "B"):
            secs = [c for c in kg.children(f"CDU-{tr}") if kg.nodes[c]["cls"] == "SectionSystem"]
            self.assertEqual(len(secs), 12, tr)

    def test_all_relations_are_registered(self):
        self.assertEqual(sorted({e["rel"] for e in kg.edges} - set(RELATIONS)), [])


class Completeness(unittest.TestCase):
    def test_every_equipment_is_decomposed_to_items(self):
        for e in EQ:
            with self.subTest(e=e["id"]):
                subs = [c for c in kg.children(e["id"]) if kg.nodes[c]["cls"] == "Subunit"]
                self.assertGreaterEqual(len(subs), 2)
                for s in subs:
                    self.assertTrue(any(kg.nodes[i]["cls"] == "MaintainableItem" for i in kg.children(s)), s)

    def test_every_equipment_has_design_data_and_tags(self):
        passive = ("Pressure relief valve", "Transmitter")      # no instrument tags of their own
        for e in EQ:
            with self.subTest(e=e["id"]):
                declared = [f for f in kg.facts(e["id"]) if f["method"] == "declared"]
                self.assertGreaterEqual(len(declared), 3)
                if e["props"]["eq_class"] not in passive:
                    self.assertTrue(any(kg.nodes[d]["cls"] == "DataPoint" for d in kg.descendants(e["id"])))

    def test_every_tag_has_unit_value_and_source(self):
        for t in TAGS:
            with self.subTest(t=t["id"]):
                self.assertTrue(kg.fact(t["id"], "engineering_unit"))
                lv = kg.fact(t["id"], "latest_value")
                self.assertTrue(lv and lv["source_system"] and lv["as_of"])
                if t["props"]["kind"] == "calculated":
                    self.assertTrue(lv["lineage"], "calculated values must cite their inputs")

    def test_every_pump_has_model_seal_plan_and_service_temperature(self):
        for e in [x for x in EQ if x["props"]["eq_class"] == "Pump"]:
            with self.subTest(e=e["id"]):
                for k in ("model", "seal_plan", "service_temperature"):
                    self.assertIsNotNone(kg.fact(e["id"], k), k)
                self.assertEqual(len(kg.targets(e["id"], "OF_MODEL")), 1)

    def test_hot_pumps_use_plan_53b(self):
        for e in [x for x in EQ if x["props"]["eq_class"] == "Pump"]:
            if kg.value(e["id"], "service_temperature") >= 260:
                self.assertEqual(kg.value(e["id"], "seal_plan"), "Plan53B", e["id"])


class Symmetry(unittest.TestCase):
    def test_train_b_mirrors_train_a(self):
        a = {e["id"] for e in EQ if e["props"]["train"] == "A"}
        for ea in a:
            eb = re.sub(r"^([A-Z]+-)1", r"\g<1>2", ea)
            with self.subTest(e=ea):
                self.assertIn(eb, kg.nodes)
                self.assertEqual(kg.nodes[eb]["props"]["eq_class"], kg.nodes[ea]["props"]["eq_class"])
                self.assertEqual(len(kg.descendants(ea)), len(kg.descendants(eb)))
        self.assertEqual(Counter(e["props"]["train"] for e in EQ)["A"], Counter(e["props"]["train"] for e in EQ)["B"])


class HandbookF6(unittest.TestCase):
    def test_numbers_quoted_in_f6(self):
        s = kg.level_summary()
        self.assertEqual([r["count"] for r in s["asset"]][4:], [39, 140, 463, 1484, 2608, 621, 1929])
        self.assertEqual([r["count"] for r in s["process"]][2:], [2, 8, 15, 15, 15, 15, 15, 15, 55])
        self.assertEqual(len(kg.fact_list), 12570)
        self.assertEqual(sum(1 for n in kg.nodes.values() if n["cls"] == "IOWLimit"), 116)
        self.assertEqual(sum(1 for n in kg.nodes.values() if n["spine"] == "grouping"), 44)


class Sectors(unittest.TestCase):
    def test_sector_labels(self):
        for n in kg.nodes.values():
            expected = "2" if n["cls"] in cdu_gamma.GBuilder.SECTOR2 else ("1a" if n["spine"] == "reference" else "1b")
            self.assertEqual(n["props"]["sector"], expected, n["id"])

    def test_every_fact_hangs_off_the_structure(self):
        for f in kg.fact_list:
            self.assertIn(f["subject"], kg.nodes)
            for x in f["lineage"]:
                self.assertIn(x, kg.facts_by_id)


class RDF(unittest.TestCase):
    def test_turtle_exports_pass_shape_checks(self):
        v, n = shacl_lite.validate([DATA / "structure.ttl", DATA / "information.ttl"])
        self.assertGreater(n, 90000)
        self.assertEqual(v, [])

    def test_shape_checks_catch_a_missing_seal_plan(self):
        info = (DATA / "information.ttl").read_text()
        broken = info.replace("gamma:P-101A ogkg:sealPlan vocab:Plan11 ;", "gamma:P-101A ", 1)
        self.assertNotEqual(broken, info)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "info.ttl"
            p.write_text(broken)
            v, _ = shacl_lite.validate([DATA / "structure.ttl", p])
        self.assertIn(("PumpShape", "https://example.org/ogkg/data/gamma#P-101A", "sealPlan", "0 value(s)"), v)

    def test_exporter_rejects_unknown_relationships(self):
        data = json.loads((DATA / "kg.json").read_text())
        data["edges"].append(dict(source="CDU-A", rel="NOT_IN_ONTOLOGY", target="CDU-B", props={}))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "kg.json"
            p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                ttl_v02.export(p, d, "gamma", "https://example.org/ogkg/data/gamma#")


class Insights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = {x["id"]: x for x in cdu_insights.run_all(kg)}

    def test_energy_penalty_recalculates_from_physics(self):
        # independent hand calculation: 238 kbd x 0.158987 m3/bbl x 870 kg/m3 = 381.0 kg/s; x 2.3 kJ/kgK x 14 K = 12.27 MW absorbed;
        # / 0.879 = 13.96 MW fired; x 3.412 MMBtu/MWh x 8760 h = 417,300 MMBtu/yr; x $6 = $2.50M/yr
        self.assertAlmostEqual(self.r["preheat-energy-penalty"]["value_usd"], 2_503_000, delta=5_000)
        self.assertEqual(self.r["preheat-energy-penalty"]["value_basis"], "recurring-annual")
        self.assertIn("E-209, E-210, E-211, E-212", self.r["preheat-energy-penalty"]["headline"])

    def test_overhead_exposure_counts(self):
        self.assertIn("4 IOW exceedances and 1 corrosion failure", self.r["overhead-corrosion-exposure"]["headline"])

    def test_completeness_is_total(self):
        for row in self.r["model-completeness"]["rows"]:
            self.assertEqual((row["decomposed_pct"], row["design_data_pct"], row["tags_complete_pct"]), (100, 100, 100), row)


class MCP(unittest.TestCase):
    def test_server_serves_gamma_dataset(self):
        code = ("from ogkg import mcp_server as m;"
                "print(m.get_entity('H-201')['node']['name']);"
                "print(len(m.list_insights()))")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, timeout=60,
                             env={**os.environ, "OGKG_DATASET": "gamma"})
        self.assertEqual(out.stdout.split(), ["H-201", "Crude", "heater", "11"], out.stderr[-500:])


if __name__ == "__main__":
    unittest.main()
