"""Whole-refinery tests for Refinery Gamma (v0.4.0): units, stream balance, NCI, hydrogen and sulfur balances, insights."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ogkg import refinery_insights                      # noqa: E402
from ogkg.kg import KG                                  # noqa: E402
from ogkg.refinery_units import DEEP, H2_CONSUMPTION, STREAMS, UNITS   # noqa: E402

kg = KG(ROOT / "data" / "cdu-gamma" / "kg.json")
SITE = "SITE-GAMMA"
LIQUID = [u[0] for u in UNITS if u[5] == "kbd"]


def inflow(uid, unit="kbd"):
    return [s for s in kg.sources(uid, "FEEDS") if (kg.fact(s, "flow_rate") or {}).get("unit") == unit]


class Units(unittest.TestCase):
    def test_every_unit_is_real_and_sectioned(self):
        units = [n for n in kg.nodes.values() if n["cls"] == "PlantUnit"]
        self.assertEqual(len(units), 36)
        for n in units:
            with self.subTest(u=n["id"]):
                self.assertNotEqual(n["props"].get("onto_class"), "OutOfScopeUnit")
                self.assertTrue(any(kg.nodes[c]["cls"] == "SectionSystem" for c in kg.children(n["id"])))

    def test_deep_units_reach_L10(self):
        for u in DEEP:
            levels = {kg.nodes[d]["level"] for d in kg.descendants(u)}
            self.assertEqual(levels, {4, 5, 6, 7, 8, 9, 10}, u)   # descendants include the unit itself

    def test_every_edge_endpoint_exists(self):
        self.assertEqual([e for e in kg.edges if e["source"] not in kg.nodes or e["target"] not in kg.nodes], [])

    def test_every_stream_runs_between_plant_units(self):
        for s in [n["id"] for n in kg.nodes.values() if n["cls"] == "Stream" and n["id"] != "STR-CRUDE"]:
            with self.subTest(s=s):
                for rel, ends in (("PRODUCES", kg.sources(s, "PRODUCES")), ("FEEDS", kg.targets(s, "FEEDS"))):
                    self.assertEqual(len(ends), 1, rel)
                    self.assertEqual(kg.nodes[ends[0]]["cls"], "PlantUnit", rel)
                self.assertIsNotNone(kg.fact(s, "flow_rate"))


class Balances(unittest.TestCase):
    def test_feed_rate_is_the_sum_of_inflows_and_within_capacity(self):
        for u in LIQUID:
            with self.subTest(u=u):
                self.assertAlmostEqual(kg.value(u, "feed_rate"), sum(kg.value(s, "flow_rate") for s in inflow(u)), places=1)
                self.assertLessEqual(kg.value(u, "utilisation"), 100.0)

    def test_crude_units_feed_the_rest_of_the_refinery(self):
        self.assertAlmostEqual(kg.value("VDU-1", "feed_rate"),
                               kg.value("STR-A-AR", "flow_rate") + kg.value("STR-B-AR", "flow_rate"), places=1)

    def test_nelson_complexity_recomputes(self):
        nci = sum(kg.value(u, "nelson_factor") * kg.value(u, "design_capacity")
                  for u in kg.nodes if kg.fact(u, "nelson_factor")) / kg.value(SITE, "crude_capacity")
        self.assertAlmostEqual(kg.value(SITE, "nelson_complexity_index"), nci, delta=0.01)
        self.assertAlmostEqual(nci, 15.0, delta=0.1)

    def test_hydrogen_balance_closes(self):
        demand = sum(kg.value(u, "h2_consumption") for u in H2_CONSUMPTION)
        self.assertAlmostEqual(kg.value(SITE, "h2_demand"), demand, places=1)
        self.assertAlmostEqual(kg.value("HMU-1", "h2_production") + kg.value("CCR-1", "h2_production"), demand, places=1)
        self.assertAlmostEqual(kg.value(SITE, "h2_headroom"), kg.value(SITE, "h2_supply_capacity") - demand, places=1)
        self.assertAlmostEqual(kg.value("STR-H2-HCU-1", "flow_rate"), 1800 * kg.value("HCU-1", "feed_rate") / 1000, places=1)

    def test_sulfur_balance_closes(self):
        out = kg.value("SRU-1", "sulfur_production") + sum(kg.value(SITE, k) for k in (
            "sulfur_to_coke", "sulfur_to_residual_products", "sulfur_in_products", "sulfur_emitted_as_so2"))
        self.assertEqual(out, kg.value(SITE, "sulfur_in"))
        self.assertEqual(kg.value(SITE, "sulfur_balance_closure"), 0)

    def test_blend_pools_close(self):
        for pool, out in (("GBL-1", "STR-GBL-GASO"), ("DBL-1", "STR-DBL-DIST")):
            self.assertAlmostEqual(kg.value(pool, "feed_rate"), kg.value(out, "flow_rate"), places=1)


class RefineryInsights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = {x["id"]: x for x in refinery_insights.run_all(kg)}

    def test_all_eight_insights_run_with_evidence(self):
        self.assertEqual(len(self.r), 8)
        for i in self.r.values():
            for fid in i["evidence"]:
                self.assertIn(fid, kg.facts_by_id)

    def test_reformer_outage_exposure(self):
        deficit = kg.value("CCR-1", "h2_production") - kg.value(SITE, "h2_headroom")
        per_day = deficit / 1.8 * 1000 * kg.value(SITE, "grm_fy2026")
        self.assertAlmostEqual(self.r["hydrogen-headroom"]["value_usd"], per_day, delta=1)

    def test_sulfur_ceiling(self):
        share = kg.value("SRU-1", "sulfur_production") / kg.value(SITE, "sulfur_in")
        ceiling = kg.value("SRU-1", "design_capacity") / share / kg.value(SITE, "crude_mass_rate") * 100
        self.assertIn(f"≈{ceiling:.2f} wt% S", self.r["sulfur-ceiling"]["headline"])
        self.assertAlmostEqual(ceiling, 2.23, delta=0.01)

    def test_reformer_bottleneck_value(self):
        v = kg.value("STR-NHT-HN-BYP", "flow_rate") * 1000 * 365 * kg.value(SITE, "reformate_upgrade_spread")
        self.assertAlmostEqual(self.r["reformer-bottleneck"]["value_usd"], v, delta=1)

    def test_loss_chain_links_wash_water_shortfall_to_reac_leak(self):
        rows = {x["event"]: x for x in self.r["conversion-loss-chains"]["rows"]}
        self.assertEqual(set(rows), {"FL-H01", "FL-H02", "FL-D01", "FL-F01"})
        self.assertTrue(rows["FL-H01"]["precursors"].startswith("IOW-H02 (26 d before"))
        self.assertEqual(self.r["conversion-loss-chains"]["value_usd"], sum(x["total_usd"] for x in rows.values()))


if __name__ == "__main__":
    unittest.main()
