"""v0.5 data-layer tests for Refinery Gamma: identity, confidence rule, time model, integrity, safeguards, economics.

Where a number is asserted, the expected value is an independent hand calculation written in the comment, not a re-run
of the builder's own formula (council finding S-11)."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ogkg.identity import normalise_tag  # noqa: E402
from ogkg.kg import KG                    # noqa: E402

kg = KG(ROOT / "data" / "cdu-gamma" / "kg.json")
RANK = {"high": 3, "medium": 2, "low": 1}
EQ = {n["id"]: n for n in kg.nodes.values() if n["cls"] == "EquipmentUnit"}
TAGS = [n for n in kg.nodes.values() if n["cls"] == "DataPoint"]
out_ = lambda s, rel: kg.targets(s, rel)
in_ = lambda t, rel: kg.sources(t, rel)


class Identity(unittest.TestCase):
    def test_fact_ids_are_content_derived_and_unique(self):
        ids = [f["id"] for f in kg.fact_list]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(re.fullmatch(r"F-[0-9a-f]{12}", i) for i in ids))

    def test_nodes_carry_site_scoped_iris(self):
        for n in kg.nodes.values():
            self.assertEqual(n["props"]["iri"], f"https://example.org/ogkg/data/gamma#{n['id']}")

    def test_equipment_and_tags_carry_source_system_identifiers(self):
        sap = [n["props"]["external_ids"]["SAP_EQ"] for n in EQ.values()]
        self.assertEqual(len(sap), len(set(sap)))
        for t in TAGS:
            if t["props"]["kind"] in ("sensor", "analyser"):
                pi = t["props"]["external_ids"]["PI"]
                with self.subTest(t=t["id"]):
                    self.assertRegex(pi, r"^[0-9U][0-9][A-Z]+\d+\.PV$")
                    self.assertEqual(normalise_tag(pi), t["id"])


class Confidence(unittest.TestCase):
    def test_no_derived_fact_is_more_certain_than_its_inputs(self):
        for f in kg.fact_list:
            if f["lineage"]:
                worst = min(RANK[kg.facts_by_id[x]["confidence"]] for x in f["lineage"])
                self.assertLessEqual(RANK[f["confidence"]], worst, f["id"])

    def test_kg_derived_facts_always_cite_inputs(self):
        for f in kg.fact_list:
            if f["method"] == "calculated" and f["source_system"].startswith("KG derived"):
                self.assertTrue(f["lineage"], (f["subject"], f["predicate"]))

    def test_economic_facts_are_confidential_and_sif_setpoints_restricted(self):
        self.assertEqual(kg.fact("PR-ACT26-GASOLINE", "price")["sensitivity"], "confidential")
        self.assertEqual(kg.fact("SIF-HCU-DEP", "trip_setpoint")["sensitivity"], "restricted")
        self.assertEqual(kg.fact("CDU-A", "nelson_factor")["sensitivity"], "public")


class TimeModel(unittest.TestCase):
    def test_monthly_history_and_as_of(self):
        h = kg.history("HCU-1", "wabt_cracking_month")
        self.assertEqual(len(h), 12)
        self.assertEqual(kg.value("HCU-1", "wabt_cracking_month", as_of="2026-01-15"), h[3]["value"])
        self.assertEqual(kg.value("HCU-1", "wabt_cracking_month"), h[-1]["value"])

    def test_superseded_fact_is_kept_but_not_current(self):
        facts = kg.history("CDU-B", "availability_fy2026")
        old = [f for f in facts if f["status"] == "superseded"]
        new = [f for f in facts if f["status"] == "current"]
        self.assertEqual((len(old), len(new)), (1, 1))
        self.assertEqual(new[0]["supersedes"], old[0]["id"])
        self.assertEqual(kg.value("CDU-B", "availability_fy2026"), 99.1)
        self.assertEqual(kg.nodes["CR-001"]["props"]["corrects_fact"], old[0]["id"])

    def test_serial_items_and_moc(self):
        inst = [e for e in kg.edges if e["rel"] == "INSTALLED_AT" and e["target"] == "P-208A"]
        self.assertEqual(len(inst), 2)
        self.assertEqual(sorted(e["props"]["valid_from"] for e in inst)[1], "2026-02-10")
        self.assertEqual(out_("FL-B01", "OCCURRED_ON_SERIAL"), ["SN-P-208A-1"])

    def test_tml_thickness_history_decreases(self):
        h = kg.history("PC-102-TML1", "thickness")
        self.assertGreaterEqual(len(h), 3)
        self.assertTrue(all(a["value"] >= b["value"] for a, b in zip(h, h[1:])))


class Integrity(unittest.TestCase):
    def test_iow_limits_have_api584_level_response_and_action(self):
        lims = [n for n in kg.nodes.values() if n["cls"] == "IOWLimit"]
        self.assertGreater(len(lims), 100)
        for n in lims:
            with self.subTest(n=n["id"]):
                self.assertIn(n["props"]["iow_level"], ("critical", "standard", "informational"))
                for k in ("limit_value", "response_time", "required_action"):
                    self.assertIsNotNone(kg.fact(n["id"], k))

    def test_exceedances_point_at_a_limit_they_breach(self):
        for x in [n["id"] for n in kg.nodes.values() if n["cls"] == "IOWExceedance"]:
            lim = out_(x, "EXCEEDS")[0]
            peak, v, d = kg.value(x, "peak_value"), kg.value(lim, "limit_value"), kg.nodes[lim]["props"]["direction"]
            self.assertTrue(peak > v if d == "high" else peak < v, x)
        self.assertTrue(kg.nodes[out_("IOW-A02", "EXCEEDS")[0]]["props"]["iow_level"] == "critical")   # 55 ppm > 50 ppm critical

    def test_failures_are_iso14224_coded(self):
        for f in [n["id"] for n in kg.nodes.values() if n["cls"] == "Failure"]:
            for rel in ("HAS_FAILURE_MODE", "HAS_FAILURE_MECHANISM", "HAS_FAILURE_CAUSE", "DETECTED_BY"):
                self.assertEqual(len(out_(f, rel)), 1, (f, rel))
        self.assertEqual(out_("FL-A02", "HAS_FAILURE_MECHANISM"), ["FMECH-2.4"])     # wear
        self.assertEqual(out_("FL-F01", "HAS_FAILURE_MECHANISM"), ["FMECH-2.3"])     # erosion
        self.assertEqual(out_("FL-D01", "HAS_FAILURE_MECHANISM"), ["FMECH-2.6"])     # fatigue
        self.assertEqual(out_("FL-F01", "FAILURE_OF"), ["R-302-DIPLEG2"])           # secondary cyclone dipleg

    def test_standby_pumps_read_as_standby(self):
        for e, n in EQ.items():
            if n["props"]["eq_class"] == "Pump" and not n["props"]["running"]:
                for d in kg.descendants(e):
                    if kg.nodes[d]["cls"] == "DataPoint" and "vibration" in kg.nodes[d]["name"]:
                        self.assertEqual(kg.value(d, "latest_value"), 0.0, d)
        self.assertTrue(EQ["P-101C"]["props"]["running"])         # the bad actor is a running pump

    def test_drivers_are_separate_equipment(self):
        for e, n in EQ.items():
            if n["props"]["eq_class"] == "Pump":
                self.assertEqual(len(in_(e, "DRIVER_OF")), 1, e)
        self.assertEqual(in_("K-401", "DRIVER_OF"), ["KT-401"])
        self.assertIn("EX-301", in_("K-302", "DRIVER_OF"))

    def test_mechanism_screening_rules(self):
        sus = lambda x: {e["target"] for e in kg.out.get(x, []) if e["rel"] == "SUSCEPTIBLE_TO"}
        for e in ("H-401", "E-401", "PC-402"):                 # 347 stainless: no HTHA, but polythionic SCC
            self.assertNotIn("DM-HTHA", sus(e))
            self.assertIn("DM-PTA", sus(e))
        self.assertIn("DM-HTHA", sus("R-402"))
        self.assertIn("DM-H2H2S", sus("R-402"))
        self.assertNotIn("DM-SULF", sus("R-402"))
        self.assertNotIn("DM-NH4HS", sus("X-401"))              # clean wash water ...
        self.assertIn("DM-NH4HS", sus("X-401-QUILLI"))          # ... but the injection quill is at risk
        self.assertNotIn("DM-HCL", sus("C-101"))                # attached to the top section, not the whole column
        self.assertIn("DM-HCL", sus("C-101-TOPCLAD"))
        self.assertIn("DM-WETH2S", sus("V-303"))
        self.assertIn("DM-TFAT", sus("D-501B-SHELL"))
        self.assertEqual([e["target"] for e in kg.out["E-209"] if e["rel"] == "SUBJECT_TO"], ["PH-FOUL"])

    def test_every_rbi_item_has_a_screening_outcome_and_inspection_plan(self):
        for e, n in EQ.items():
            if kg.fact(e, "pof_category"):
                with self.subTest(e=e):
                    self.assertTrue(kg.fact(e, "governing_mechanism") or kg.fact(e, "rbi_screening_result"))
                    for k in ("cof_category", "risk_category", "last_inspection_date", "next_inspection_due", "install_date"):
                        self.assertIsNotNone(kg.fact(e, k), k)
        # PC-102: (7.2 mm surveyed - 6.5 mm retirement) / 0.18 mm/y probe rate = 3.9 years
        self.assertAlmostEqual(kg.value("PC-102", "remaining_life"), 3.9, places=1)

    def test_vibration_tags_have_alert_and_danger_limits(self):
        for t in TAGS:
            if t["props"]["tag_type"] == "VI":
                self.assertIsNotNone(kg.fact(t["id"], "alert_limit"), t["id"])
                self.assertIsNotNone(kg.fact(t["id"], "danger_limit"), t["id"])
        k401 = next(t["id"] for t in TAGS if t["props"]["equipment"] == "K-401" and "Journal" in t["name"])
        self.assertGreater(kg.value(k401, "latest_value"), kg.value(k401, "alert_limit"))


class Safeguards(unittest.TestCase):
    def test_relief_devices_protect_equipment_at_design_pressure(self):
        psvs = [e for e, n in EQ.items() if n["props"]["eq_class"] == "Pressure relief valve"]
        self.assertGreaterEqual(len(psvs), 35)
        for p in psvs:
            prot = out_(p, "PROTECTS")
            self.assertEqual(len(prot), 1)
            self.assertLessEqual(kg.value(p, "set_pressure"), kg.value(prot[0], "design_pressure"))
            self.assertIsNotNone(kg.fact(p, "next_test_due"))

    def test_sifs_have_attributes_initiators_and_final_elements(self):
        for sif in [n["id"] for n in kg.nodes.values() if n["cls"] == "SafetyInstrumentedFunction"]:
            with self.subTest(sif=sif):
                for k in ("sil", "pfd_avg_target", "proof_test_interval", "voting", "trip_setpoint", "next_proof_test_due"):
                    self.assertIsNotNone(kg.fact(sif, k), k)
                members = in_(sif, "MEMBER_OF")
                self.assertTrue(any(EQ.get(m, {}).get("props", {}).get("eq_class") == "Transmitter" for m in members))
                self.assertTrue(any(EQ.get(m, {}).get("props", {}).get("eq_class") in ("Shutdown valve", "Slide valve") for m in members))

    def test_turnaround_scope_is_derived_from_what_is_due(self):
        items = in_("TA-2027", "IN_SCOPE_OF")
        self.assertGreater(len(items), 10)
        targets = {out_(i, "TARGETS")[0] for i in items}
        self.assertIn("R-302", targets)                          # deferred cyclone repair
        self.assertTrue({"R-401", "R-402"} <= targets)           # catalyst change


class Economics(unittest.TestCase):
    def test_every_product_is_priced_in_every_price_set(self):
        for p in [n["id"] for n in kg.nodes.values() if n["cls"] == "Product"]:
            sets = {out_(s, "IN_PRICE_SET")[0] for s in in_(p, "PRICE_OF")}
            self.assertEqual(sets, {"PS-ACT26", "PS-PLAN27", "PS-STRESS"}, p)

    def test_lost_margin_uses_the_unit_marginal_value(self):
        f = kg.fact("FL-D01", "lost_margin")
        # 42 kbd x 12 days x 1000 x $14/bbl (coker marginal value) = $7.056M
        self.assertEqual(f["value"], 7_056_000)
        self.assertIn(kg.fact("LPS-DCU-1", "lp_marginal_value")["id"], f["lineage"])

    def test_gross_margin_model_is_reconciled_to_recorded_grm(self):
        self.assertAlmostEqual(kg.value("SITE-GAMMA", "grm_model_variance"),
                               kg.value("SITE-GAMMA", "gross_margin_model") - kg.value("SITE-GAMMA", "grm_fy2026"), places=2)

    def test_assay_predicted_cdu_yields(self):
        # naphtha: 0.45 x 20.5 + 0.35 x 17.5 + 0.20 x 25.5 = 20.45 vol%
        self.assertAlmostEqual(kg.value("CDU-A", "yield_nap_assay"), 20.45, places=2)

    def test_insight_results_are_cited_facts(self):
        f = kg.fact("INS-hydrogen-headroom", "value_usd")
        self.assertTrue(f["lineage"])
        self.assertEqual(f["basis"], "at-risk-per-day")


if __name__ == "__main__":
    unittest.main()
