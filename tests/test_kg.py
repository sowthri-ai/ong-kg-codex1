"""Integrity, provenance and insight-correctness tests.  Run:  python -m unittest discover -s tests -v"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ogkg.kg import KG                       # noqa: E402
from ogkg import insights as ins             # noqa: E402
from ogkg.ontology import RELATIONS, CONFIDENCE, METHODS, LEVELS  # noqa: E402

kg = KG()


class Hierarchy(unittest.TestCase):
    def test_every_spine_node_reaches_L0(self):
        for n in kg.nodes.values():
            if n["spine"] in ("asset", "process", "trunk") and n["id"] != "OG":
                self.assertEqual(kg.ancestors(n["id"])[-1], "OG", n["id"])

    def test_levels_strictly_decrease_upwards(self):
        for n in kg.nodes.values():
            p = kg.parent(n["id"])
            if p:
                self.assertLess(kg.nodes[p]["level"], n["level"], f"{n['id']} -> {p}")

    def test_single_parent(self):
        for nid in kg.nodes:
            self.assertLessEqual(len(kg.targets(nid, "PART_OF")), 1, nid)

    def test_all_levels_L0_to_L10_populated_on_both_spines(self):
        for spine in ("asset", "process"):
            for lvl in LEVELS[spine]:
                sp = "trunk" if lvl <= 1 else spine
                self.assertTrue(any(n["spine"] == sp and n["level"] == lvl for n in kg.nodes.values()), f"{spine} L{lvl}")


class EdgesAndFacts(unittest.TestCase):
    def test_edges_valid(self):
        for e in kg.edges:
            self.assertIn(e["source"], kg.nodes); self.assertIn(e["target"], kg.nodes)
            self.assertIn(e["rel"], RELATIONS, e["rel"])

    def test_cross_spine_links_point_the_right_way(self):
        for e in kg.edges:
            s, t = kg.nodes[e["source"]], kg.nodes[e["target"]]
            if e["rel"] in ("ACTS_ON", "GOVERNS"):
                self.assertEqual(s["spine"], "process"); self.assertEqual(t["spine"], "asset")
            if e["rel"] == "INSTANTIATED_BY":
                self.assertEqual((s["cls"], t["cls"]), ("DataElement", "DataPoint"))
            if e["rel"] == "CONSUMES":
                self.assertEqual((s["cls"], t["cls"]), ("DecisionPoint", "DataElement"))

    def test_every_fact_has_provenance(self):
        for f in kg.fact_list:
            self.assertIn(f["subject"], kg.nodes)
            self.assertTrue(f["source_system"], f["id"]); self.assertTrue(f["as_of"], f["id"])
            self.assertRegex(f["as_of"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertIn(f["confidence"], CONFIDENCE); self.assertIn(f["method"], METHODS)
            for x in f["lineage"]:
                self.assertIn(x, kg.facts_by_id)

    def test_derived_facts_recompute(self):
        for f in kg.fact_list:
            if f["predicate"] == "lost_margin":
                rate, days, grm = (kg.facts_by_id[x]["value"] for x in f["lineage"])
                self.assertEqual(f["value"], round(rate * 1000 * days * grm))
            if f["predicate"] == "lp_uplift_total":
                vol, upl = (kg.facts_by_id[x]["value"] for x in f["lineage"])
                self.assertEqual(f["value"], round(vol * 1000 * upl))


class Insights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = {x["id"]: x for x in ins.run_all(kg)}

    def test_contract_and_evidence_resolve(self):
        for r in self.r.values():
            for k in ("headline", "rows", "path", "evidence", "recommendation", "decision_owner", "caveat"):
                self.assertIn(k, r)
            for fid in r["evidence"]:
                self.assertIn(fid, kg.facts_by_id)
            for nid in r["path"]:
                self.assertIn(nid, kg.nodes)

    def test_true_crude_value_independent_recalc(self):
        uplift = (0.30 * 200 * 15 + 0.25 * 200 * 16 + 0.35 * 200 * 18) * 1000 * 2.10 + 0.15 * 200 * 16 * 1000 * 1.60
        repairs = 420_000 + 160_000 + 310_000 + 95_000
        lost = (50 * 5 + 50 * 4 + 80 * 6) * 1000 * 8.20
        treat = 90_000 + 140_000 + 120_000
        self.assertAlmostEqual(self.r["true-crude-value"]["value_usd"], uplift - repairs - lost - treat, delta=1)
        # the Beta exceedance (no opportunity crude) must not be attributed
        self.assertNotIn("IOW-006", self.r["true-crude-value"]["path"])

    def test_bad_actor(self):
        top = self.r["fleet-bad-actors"]["rows"][0]
        self.assertEqual((top["model"], top["failures"], top["mtbf_days"]), ("HX-300 (OEM-A)", 14, round(4 * 365 / 14)))
        self.assertEqual(len(top["sites"]), 2)

    def test_giveaway(self):
        self.assertAlmostEqual(self.r["giveaway-root-cause"]["value_usd"], (0.62 - 0.18) * 0.60 * 55_000 * 365, delta=1)

    def test_ta_gaps(self):
        gaps = {x["id"] for x in self.r["ta-scope-gaps"]["rows"] if not x["in_scope"]}
        self.assertEqual(gaps, {"E-101B", "PC-101", "PC-201", "P-103"})

    def test_blind_spots(self):
        flagged = {x["id"] for x in self.r["decision-blind-spots"]["rows"] if not x["healthy"]}
        self.assertEqual(flagged, {"DEC-CRBUY", "DEC-CRACC", "DEC-RECIPE", "DEC-SCOPEFRZ"})


class Exports(unittest.TestCase):
    def test_turtle_sanity(self):
        for name in ("og_vckg_ontology.ttl", "og_vckg_data.ttl"):  # syntax fully checked in test_ontology_and_handbook
            txt = (ROOT / "exports" / name).read_text()
            declared = set(re.findall(r"@prefix (\w+):", txt))
            used = set(re.findall(r"(?<![\w\"/#])([a-z]+):(?=[A-Za-z_])", re.sub(r'"[^"]*"', '""', txt)))
            self.assertTrue(used <= declared | {"http", "https", "file"}, used - declared)
            stmts = re.sub(r'"(?:[^"\\]|\\.)*"', '""', txt).split(" .\n")
            self.assertGreater(len(stmts), 10)
            self.assertEqual(txt.count('"') % 2 - txt.count('\\"') % 2, 0)

    def test_explorer_bundle_embedded(self):
        html = (ROOT / "explorer" / "og_value_chain_kg.html").read_text()
        self.assertNotIn("__KG_BUNDLE__", html)
        self.assertIn('"insights"', html)


class MCP(unittest.TestCase):
    def test_mcp_server_end_to_end(self):
        out = subprocess.run([sys.executable, str(ROOT / "tests" / "mcp_smoke.py")], capture_output=True, text=True,
                             timeout=90, cwd=ROOT)
        self.assertIn("MCP SMOKE TEST PASSED", out.stdout, out.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()
