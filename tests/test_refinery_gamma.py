"""Whole-refinery tests for Refinery Gamma (v0.4.0): units, stream balance, NCI, hydrogen and sulfur balances, insights."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ogkg import refinery_insights                      # noqa: E402
from ogkg.kg import KG                                  # noqa: E402
from ogkg.refinery_units import DEEP, H2_CONSUMPTION, STREAMS, SULFUR_CONTENT, UNITS   # noqa: E402

SULFUR_STREAMS = set(SULFUR_CONTENT)

kg = KG(ROOT / "data" / "cdu-gamma" / "kg.json")
SITE = "SITE-GAMMA"
LIQUID = [u[0] for u in UNITS if u[5] == "kbd"]


def inflow(uid, unit="kbd"):
    return [s for s in kg.sources(uid, "FEEDS") if (kg.fact(s, "flow_rate") or {}).get("unit") == unit]


class Units(unittest.TestCase):
    def test_every_unit_is_real_and_sectioned(self):
        units = [n for n in kg.nodes.values() if n["cls"] == "PlantUnit"]
        self.assertEqual(len(units), 39)
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

    def test_hydrogen_balance_reports_its_residual(self):
        demand = sum(kg.value(u, "h2_makeup") for u in H2_CONSUMPTION)
        self.assertAlmostEqual(kg.value(SITE, "h2_demand"), demand, places=0)
        for u in H2_CONSUMPTION:      # make-up = chemical consumption / efficiency (purge and solution losses)
            self.assertGreater(kg.value(u, "h2_makeup"), kg.value(u, "h2_consumption"))
        supply = kg.value("HMU-1", "h2_production") + kg.value("CCR-1", "h2_production")
        self.assertNotAlmostEqual(supply, demand, places=0, msg="the SMR meter must be independent of the balance")
        self.assertAlmostEqual(kg.value(SITE, "h2_balance_residual"), 100 * (supply - demand) / demand, delta=0.02)
        self.assertLess(abs(kg.value(SITE, "h2_balance_residual")), 1.0)
        self.assertAlmostEqual(kg.value(SITE, "h2_headroom"), kg.value(SITE, "h2_supply_capacity") - demand, places=0)
        self.assertAlmostEqual(kg.value("STR-H2-HCU-1", "flow_rate"), 1800 * kg.value("HCU-1", "feed_rate") / 1000 / 0.90, places=0)

    def test_sulfur_balance_reports_unaccounted_sulfur(self):
        fates = sum(f["value"] for f in kg.fact_list if f["predicate"] == "sulfur_flow" and f["subject"] != "STR-VGO-IMP"
                    and f["subject"] in SULFUR_STREAMS)
        fates += kg.value("FCC-1", "sulfur_to_flue_gas") + kg.value(SITE, "sulfur_emitted_other")
        out = kg.value("SRU-1", "sulfur_production") + fates
        self.assertAlmostEqual(kg.value(SITE, "sulfur_unaccounted"), kg.value(SITE, "sulfur_in") - out, delta=0.2)
        self.assertNotEqual(kg.value(SITE, "sulfur_unaccounted"), 0)
        self.assertLess(abs(100 - kg.value(SITE, "sulfur_balance_closure")), 1.0)
        # imported VGO sulfur is an input: 30 kbd x 0.158987 x 930 kg/m3 x 2.1 wt% = 93.2 t/d
        self.assertAlmostEqual(kg.value("STR-VGO-IMP", "sulfur_flow"), 93.2, delta=0.2)

    def test_every_processing_unit_closes_on_mass(self):
        for u in [x for x in kg.nodes if kg.fact(x, "mass_closure")]:
            with self.subTest(u=u):
                self.assertTrue(99.0 <= kg.value(u, "mass_closure") <= 101.0, kg.value(u, "mass_closure"))
        self.assertLess(kg.value(SITE, "mass_unaccounted_pct_crude"), 0.5)

    def test_fcc_gains_volume_and_mtbe_conserves_mass(self):
        fcc_out = sum(kg.value(s, "flow_rate") for s in kg.targets("FCC-1", "PRODUCES") if kg.fact(s, "flow_rate")["unit"] == "kbd")
        self.assertGreater(fcc_out / kg.value("FCC-1", "feed_rate"), 1.03)
        self.assertLess(abs(100 - kg.value("MTBE-1", "mass_closure")), 1.0)

    def test_blend_pools_close(self):
        self.assertAlmostEqual(kg.value("GBL-1", "feed_rate"), kg.value("STR-GBL-GASO", "flow_rate"), places=1)
        self.assertAlmostEqual(kg.value("DBL-1", "feed_rate"), kg.value("STR-DBL-JET", "flow_rate") + kg.value("STR-DBL-ULSD", "flow_rate"),
                               places=1)


class RefineryInsights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = {x["id"]: x for x in refinery_insights.run_all(kg)}

    def test_all_insights_run_with_evidence_and_a_value_contract(self):
        self.assertEqual(len(self.r), 11)
        for i in self.r.values():
            with self.subTest(i=i["id"]):
                for fid in i["evidence"]:
                    self.assertIn(fid, kg.facts_by_id)
                for k in ("value_usd", "value_basis", "value_low", "value_high", "capex_required", "confidence"):
                    self.assertIn(k, i)
                if i["value_usd"] is not None:
                    self.assertTrue(i["value_basis"])
                    self.assertLessEqual(i["value_low"], i["value_usd"])
                    self.assertGreaterEqual(i["value_high"], i["value_usd"])

    def test_reformer_outage_exposure_uses_hcu_marginal_value(self):
        # independent: deficit = 91.1 - 13.9 = 77.2 MMSCFD; HCU make-up 1800/0.90 = 2.0 MMSCFD per kbd -> 38.6 kbd x $12 = $463k/d
        self.assertAlmostEqual(self.r["hydrogen-headroom"]["value_usd"], 463_000, delta=2_000)

    def test_sulfur_ceiling(self):
        share = kg.value("SRU-1", "sulfur_production") / kg.value(SITE, "sulfur_in")
        ceiling = (kg.value("SRU-1", "design_capacity") / share - kg.value("STR-VGO-IMP", "sulfur_flow")) / kg.value(SITE, "crude_mass_rate") * 100
        self.assertIn(f"≈{ceiling:.2f} wt% S", self.r["sulfur-ceiling"]["headline"])
        self.assertIn("one of 3 Claus trains", self.r["sulfur-ceiling"]["headline"])

    def test_reformer_bottleneck_value_is_gross_pre_capex(self):
        r = self.r["reformer-bottleneck"]
        self.assertEqual(r["value_basis"], "gross-pre-capex")
        self.assertIsNone(r["capex_required"])
        self.assertAlmostEqual(r["value_usd"], 10.1 * 1000 * 365 * 6.5 + 10.2e6 * 0, delta=10e6)

    def test_loss_chains_find_the_seeded_precursors(self):
        rows = {x["event"]: x for x in self.r["conversion-loss-chains"]["rows"]}
        self.assertTrue(rows["FL-H01"]["precursors"].startswith("IOW-H02 (26 d before"))
        self.assertIn("IOW-D03", rows["FL-D01"]["precursors"])
        self.assertNotIn("IOW-H01", rows["FL-H02"]["precursors"])       # the excursion came after the trip (same day)
        self.assertEqual(self.r["conversion-loss-chains"]["value_usd"], sum(x["total_usd"] for x in rows.values()))

    def test_octane_giveaway(self):
        self.assertAlmostEqual(kg.value("PRD-GASOLINE", "octane_giveaway"), 0.4, places=2)
        # 0.4 RON x 130.6 kbd x 1000 x 365 x $0.55 = $10.49M/yr
        self.assertAlmostEqual(self.r["octane-giveaway"]["value_usd"], 10_487_000, delta=2_000)

    def test_balance_integrity_flags_meters_beyond_tolerance(self):
        rows = self.r["balance-integrity"]["rows"]
        self.assertTrue(any(r["status"] == "INVESTIGATE" for r in rows))
        self.assertTrue(all(abs(r["residual"]) <= r["tolerance"] for r in rows if r["status"] == "OK"))


if __name__ == "__main__":
    unittest.main()
