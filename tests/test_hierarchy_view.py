"""The hierarchy page is generated from the graph and the alignment modules, and the committed copy is current."""
import json
import re
import unittest
from pathlib import Path

from ogkg import hierarchy_view

ROOT = Path(__file__).resolve().parent.parent
DATA, STATS = hierarchy_view.build_data()


class HierarchyView(unittest.TestCase):
    def test_every_spine_node_reaches_the_root(self):
        n = DATA["nodes"]
        root = next(i for i, r in enumerate(n) if r[0] == "OG")
        for i, r in enumerate(n):
            if r[4] in ("asset", "process", "trunk"):
                j, hops = i, 0
                while n[j][5] >= 0 and hops < 20:
                    j, hops = n[j][5], hops + 1
                self.assertEqual(j, root, r[0])

    def test_ladder_classes_carry_standards(self):
        s = DATA["std"]
        self.assertEqual(s["EquipmentUnit"]["isa95_level"], "EquipmentModule")
        self.assertEqual(s["PlantUnit"]["isa95_level"], "ProductionUnit")
        self.assertEqual(s["CentrifugalPump"]["iso14224_class"], "PU")
        self.assertEqual(s["DataPoint"]["ccom_entity"], "MeasurementLocation")

    def test_sample_path_exists(self):
        ids = {r[0] for r in DATA["nodes"]}
        self.assertTrue({"P-101A", "P-101A-PMP", "P-101A-RBRG", "P-101A-TBRG", "P-101A-SEAL"} <= ids)

    def test_committed_page_is_current(self):
        self.assertEqual((ROOT / "explorer" / "refinery_gamma_hierarchy.html").read_text(), hierarchy_view.render())

    def test_page_is_self_contained(self):
        page = hierarchy_view.render()
        self.assertIn("<title>Refinery Gamma Hierarchy</title>", page)
        self.assertNotIn("__DATA__", page)
        self.assertNotIn("__N_", page)
        srcs = re.findall(r'<script[^>]+src="([^"]+)"', page)
        self.assertEqual(srcs, [])                                    # no external scripts
        payload = re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S).group(1)
        self.assertEqual(len(json.loads(payload)["nodes"]), STATS["nodes"])

    def test_artifact_variant_has_no_skeleton(self):
        page = hierarchy_view.render(standalone=False)
        self.assertFalse(page.lstrip().lower().startswith("<!doctype"))
        self.assertTrue(page.startswith("<title>"))


if __name__ == "__main__":
    unittest.main()
