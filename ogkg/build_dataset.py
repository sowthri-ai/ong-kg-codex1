"""
Builds the demonstration dataset for the O&G Value Chain Knowledge Graph.

ALL SITES, EQUIPMENT, EVENTS AND COSTS ARE SYNTHETIC (fictional Refinery Alpha / Beta).
Crude-grade assay values for named public grades are INDICATIVE typical values and are
tagged method='indicative', confidence='medium' so no AI treats them as contract-grade.

Run:  python -m ogkg.build_dataset      -> writes data/kg.json
"""
import json
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "kg.json"
DATASET_AS_OF = "2026-09-28"


class Builder:
    def __init__(self):
        self.nodes, self.edges, self.facts = {}, [], []
        self._fid = 0

    def node(self, id, cls, name, spine, level=None, parent=None, desc="", **props):
        assert id not in self.nodes, f"duplicate node {id}"
        self.nodes[id] = dict(id=id, cls=cls, name=name, spine=spine, level=level,
                              desc=desc, props=props)
        if parent:
            self.edge(id, "PART_OF", parent)
        return id

    def edge(self, s, rel, t, **props):
        self.edges.append(dict(source=s, rel=rel, target=t, props=props))

    def fact(self, subject, predicate, value, unit="", as_of=DATASET_AS_OF, src="",
             ref="", owner="", conf="high", method="recorded", lineage=None):
        self._fid += 1
        fid = f"F-{self._fid:05d}"
        self.facts.append(dict(id=fid, subject=subject, predicate=predicate, value=value,
                               unit=unit, as_of=as_of, source_system=src, source_ref=ref,
                               owner=owner, confidence=conf, method=method,
                               lineage=lineage or []))
        return fid


def build():
    b = Builder()
    N, E, F = b.node, b.edge, b.fact

    # ------------------------------------------------------------------ roles
    roles = {
        "ROLE-CRPLAN": "Crude & Planning Manager", "ROLE-CORR": "Corrosion / Integrity Engineer",
        "ROLE-REL": "Reliability Engineer", "ROLE-BLEND": "Blending Planner",
        "ROLE-TA": "Turnaround Manager", "ROLE-PROC": "Process Engineer",
        "ROLE-LAB": "Laboratory Manager", "ROLE-ECON": "Site Economist",
        "ROLE-OPS": "Operations Superintendent", "ROLE-MAINT": "Maintenance Manager",
    }
    for rid, rname in roles.items():
        N(rid, "Role", rname, "org")

    # ------------------------------------------------------------------ trunk L0-L1
    N("OG", "Industry", "Oil & Gas", "trunk", 0, desc="Root of the value-chain knowledge graph")
    for seg in ["Upstream", "Midstream", "Downstream"]:
        N(f"SEG-{seg.upper()}", "Segment", seg, "trunk", 1, "OG")

    # ================================================================== ASSET SPINE
    N("BC-REF", "BusinessCategory", "Refining", "asset", 2, "SEG-DOWNSTREAM")
    N("BC-EP", "BusinessCategory", "Exploration & Production", "asset", 2, "SEG-UPSTREAM")
    N("BC-PT", "BusinessCategory", "Pipelines & Terminals", "asset", 2, "SEG-MIDSTREAM")

    # --- upstream (thin slice)
    N("FIELD-F1", "Installation", "Field F1", "asset", 3, "BC-EP", desc="Onshore oil field (synthetic)")
    N("CPF-1", "PlantUnit", "Central Processing Facility 1", "asset", 4, "FIELD-F1")
    N("CPF-1-SEP", "SectionSystem", "Separation train", "asset", 5, "CPF-1")
    N("V-1001", "EquipmentUnit", "V-1001 HP separator", "asset", 6, "CPF-1-SEP", eq_class="Vessel")
    N("T-F1-OIL", "DataPoint", "FI-9001 Export oil rate", "asset", 10, "V-1001", kind="sensor")
    F("T-F1-OIL", "latest_value", 45.0, "kbd", src="Upstream Historian", ref="FI-9001", owner="ROLE-OPS", method="measured")

    # --- midstream (thin slice)
    N("TERM-T1", "Installation", "Crude Terminal T1", "asset", 3, "BC-PT", desc="Coastal import terminal (synthetic)")
    N("TFARM-1", "PlantUnit", "Crude tank farm", "asset", 4, "TERM-T1")
    N("TFARM-1-S", "SectionSystem", "Crude storage", "asset", 5, "TFARM-1")
    N("TK-01", "EquipmentUnit", "TK-01 Crude tank", "asset", 6, "TFARM-1-S", eq_class="Storage tank")
    N("T-TK01-LVL", "DataPoint", "LI-7001 Tank level", "asset", 10, "TK-01", kind="sensor")
    F("TK-01", "capacity", 1.0, "MMbbl", src="Asset Register", ref="TK-01", owner="ROLE-OPS", method="declared")
    F("T-TK01-LVL", "latest_value", 62.0, "%", src="Terminal SCADA", ref="LI-7001", owner="ROLE-OPS", method="measured")
    E("FIELD-F1", "SUPPLIES", "TERM-T1")

    # --- refineries
    sites = {
        "ALPHA": dict(name="Refinery Alpha", cap=200, grm=8.20, cx=9.5, desc="Coastal complex refinery (synthetic)"),
        "BETA": dict(name="Refinery Beta", cap=120, grm=6.90, cx=7.8, desc="Inland cracking refinery (synthetic)"),
    }
    for s, d in sites.items():
        N(f"SITE-{s}", "Installation", d["name"], "asset", 3, "BC-REF", desc=d["desc"])
        F(f"SITE-{s}", "crude_capacity", d["cap"], "kbd", src="Asset Register", ref=f"SITE-{s}", owner="ROLE-OPS", method="declared")
        F(f"SITE-{s}", "grm_fy2026", d["grm"], "USD/bbl", src="Site Economics (monthly close)", ref=f"GRM-{s}-FY26",
          owner="ROLE-ECON", method="calculated", conf="high")
        F(f"SITE-{s}", "nelson_complexity", d["cx"], "index", src="Asset Register", owner="ROLE-PROC", method="declared")
        E("TERM-T1", "SUPPLIES", f"SITE-{s}")

    def unit(uid, name, site, cap):
        N(uid, "PlantUnit", name, "asset", 4, f"SITE-{site}")
        F(uid, "design_capacity", cap, "kbd", src="Asset Register", ref=uid, owner="ROLE-PROC", method="declared")

    for n, site, cap in [("1", "ALPHA", 200), ("2", "BETA", 120)]:
        unit(f"CDU-{n}", f"CDU-{n} Crude distillation", site, cap)
        unit(f"VDU-{n}", f"VDU-{n} Vacuum distillation", site, round(cap * 0.45))
        unit(f"FCC-{n}", f"FCC-{n} Fluid catalytic cracker", site, round(cap * 0.30))
        unit(f"REF-{n}", f"REF-{n} Catalytic reformer", site, round(cap * 0.15))
        unit(f"GBL-{n}", f"GBL-{n} Gasoline blender", site, round(cap * 0.30))

    def sec(sid, name, parent):
        N(sid, "SectionSystem", name, "asset", 5, parent)

    for n in ["1", "2"]:
        sec(f"CDU-{n}-DS", "Desalter system", f"CDU-{n}")
        sec(f"CDU-{n}-PH", "Preheat train", f"CDU-{n}")
        sec(f"CDU-{n}-FR", "Atmospheric fractionation", f"CDU-{n}")
        sec(f"CDU-{n}-OVH", "Overhead system", f"CDU-{n}")
        sec(f"VDU-{n}-VR", "Vacuum resid system", f"VDU-{n}")
        sec(f"VDU-{n}-TL", "Transfer line & flash zone", f"VDU-{n}")
        sec(f"FCC-{n}-FR", "Main fractionator & slurry", f"FCC-{n}")
        sec(f"REF-{n}-RX", "Reactor & feed/effluent", f"REF-{n}")
        sec(f"REF-{n}-STB", "Stabiliser", f"REF-{n}")
        sec(f"GBL-{n}-HDR", "Blend header & analysers", f"GBL-{n}")

    def eq(eid, name, parent, eq_class, **props):
        N(eid, "EquipmentUnit", name, "asset", 6, parent, eq_class=eq_class, **props)

    # CDU-1 overhead (corrosion story)
    eq("E-101A", "E-101A Overhead condenser A", "CDU-1-OVH", "Heat exchanger", metallurgy="Carbon steel tubes")
    eq("E-101B", "E-101B Overhead condenser B", "CDU-1-OVH", "Heat exchanger", metallurgy="Carbon steel tubes")
    eq("V-102", "V-102 Overhead accumulator", "CDU-1-OVH", "Vessel")
    eq("P-103", "P-103 Reflux pump", "CDU-1-OVH", "Pump")
    eq("PC-101", "PC-101 Overhead piping circuit", "CDU-1-OVH", "Piping circuit")
    eq("V-110", "V-110 Desalter", "CDU-1-DS", "Vessel")
    eq("C-101", "C-101 Atmospheric column", "CDU-1-FR", "Column")
    eq("H-101", "H-101 Crude heater", "CDU-1-PH", "Fired heater")
    eq("PC-201", "PC-201 VDU transfer line circuit", "VDU-1-TL", "Piping circuit", metallurgy="5Cr")
    eq("E-301", "E-301 Combined feed/effluent exchanger", "REF-1-RX", "Heat exchanger")
    for eid, last, nxt, rank, cr in [("E-101A", "2021-03-10", "2027-03-01", "High", 0.35), ("E-101B", "2021-03-10", "2029-03-01", "Medium", 0.30),
                                      ("PC-101", "2023-09-18", "2028-09-18", "Medium", 0.40), ("V-102", "2021-03-12", "2027-03-01", "Medium", 0.12),
                                      ("P-103", "2022-06-01", "2028-06-01", "Low", None), ("PC-201", "2022-11-05", "2027-11-05", "Medium", 0.28)]:
        F(eid, "last_inspection", last, "", src="Inspection DB (RBI)", ref=f"INSP-{eid}", owner="ROLE-CORR")
        F(eid, "next_inspection_due", nxt, "", src="Inspection DB (RBI)", ref=f"INSP-{eid}", owner="ROLE-CORR", method="declared")
        F(eid, "rbi_risk_rank", rank, "", as_of="2025-06-30", src="Inspection DB (RBI)", ref=f"RBI-{eid}", owner="ROLE-CORR",
          method="calculated", conf="medium")
        if cr is not None:
            F(eid, "measured_corrosion_rate", cr, "mm/y", src="Inspection DB (RBI)", ref=f"UT-{eid}", owner="ROLE-CORR", method="measured")
    # CDU-2 equivalents (control group)
    eq("E-401A", "E-401A Overhead condenser", "CDU-2-OVH", "Heat exchanger", metallurgy="Titanium tubes")
    eq("V-402", "V-402 Overhead accumulator", "CDU-2-OVH", "Vessel")
    eq("E-601", "E-601 Combined feed/effluent exchanger", "REF-2-RX", "Heat exchanger")

    # Hot-service pumps (bad-actor story) — same OEM model across sites
    pumps = [
        # id, name, section, model, service temp C, seal plan
        ("P-201A", "P-201A Vacuum resid pump A", "VDU-1-VR", "HX-300 (OEM-A)", 365, "API 682 Plan 32 single seal"),
        ("P-201B", "P-201B Vacuum resid pump B", "VDU-1-VR", "HX-300 (OEM-A)", 365, "API 682 Plan 32 single seal"),
        ("P-501", "P-501 FCC slurry pump", "FCC-1-FR", "HX-300 (OEM-A)", 350, "API 682 Plan 32 single seal"),
        ("P-401A", "P-401A Vacuum resid pump A", "VDU-2-VR", "HX-300 (OEM-A)", 360, "API 682 Plan 32 single seal"),
        ("P-401B", "P-401B Vacuum resid pump B", "VDU-2-VR", "VS-450 (OEM-C)", 360, "API 682 Plan 53B dual seal"),
        ("P-306", "P-306 AGO pumparound pump", "CDU-2-FR", "HX-300 (OEM-A)", 260, "API 682 Plan 32 single seal"),
    ]
    for pid, pname, psec, model, temp, plan in pumps:
        eq(pid, pname, psec, "Pump")
        F(pid, "model", model, "", src="Asset Register", ref=pid, owner="ROLE-REL", method="declared")
        F(pid, "service_temperature", temp, "degC", src="Process Datasheet", ref=f"DS-{pid}", owner="ROLE-PROC", method="declared")
        F(pid, "seal_plan", plan, "", src="Asset Register", ref=pid, owner="ROLE-REL", method="declared")
        # L7-L9 decomposition (ISO 14224)
        N(f"{pid}-SS", "Subunit", "Seal system", "asset", 7, pid)
        N(f"{pid}-MS", "MaintainableItem", "Mechanical seal", "asset", 8, f"{pid}-SS")
        N(f"{pid}-SF", "Part", "Seal faces", "asset", 9, f"{pid}-MS")
        N(f"{pid}-OR", "Part", "O-rings", "asset", 9, f"{pid}-MS")
        N(f"{pid}-BH", "Subunit", "Bearing housing", "asset", 7, pid)
        N(f"{pid}-BRG", "MaintainableItem", "Bearings", "asset", 8, f"{pid}-BH")
    # tube bundle decomposition for the overhead condensers
    for ex in ["E-101A", "E-101B", "E-401A"]:
        N(f"{ex}-TB", "Subunit", "Tube bundle", "asset", 7, ex)
        N(f"{ex}-TU", "MaintainableItem", "Tubes", "asset", 8, f"{ex}-TB")

    # ---- L10 data points
    def tag(tid, name, parent, kind="sensor", **props):
        N(tid, "DataPoint", name, "asset", 10, parent, kind=kind, **props)

    for n, site in [("1", "ALPHA"), ("2", "BETA")]:
        tag(f"T-CDU{n}-CL", f"AI-{n}021 Overhead water chloride", f"CDU-{n}-OVH", "lab/online analyser")
        tag(f"T-CDU{n}-PH", f"AI-{n}022 Overhead water pH", f"CDU-{n}-OVH", "online analyser")
        tag(f"T-CDU{n}-FI", f"FI-{n}001 Crude charge rate", f"CDU-{n}", "sensor")
        tag(f"T-CDU{n}-DSS", f"AI-{n}010 Desalted crude salt", f"CDU-{n}-DS", "lab")
        tag(f"T-REF{n}-RON", f"LIMS Reformate RON", f"REF-{n}-STB", "lab")
        tag(f"T-REF{n}-TI", f"TI-{n}310 Reactor inlet temperature", f"REF-{n}-RX", "sensor")
        tag(f"T-GBL{n}-RON", f"LIMS Gasoline product RON", f"GBL-{n}-HDR", "lab")
        F(f"T-CDU{n}-CL", "iow_limit_standard", 20, "ppm", src="IOW Register (API 584)", ref=f"IOW-CDU{n}-CL",
          owner="ROLE-CORR", method="declared")
        F(f"T-CDU{n}-CL", "iow_limit_critical", 50, "ppm", src="IOW Register (API 584)", ref=f"IOW-CDU{n}-CL",
          owner="ROLE-CORR", method="declared")
        F(f"T-CDU{n}-PH", "iow_limit_low", 5.5, "pH", src="IOW Register (API 584)", ref=f"IOW-CDU{n}-PH",
          owner="ROLE-CORR", method="declared")
    tag("T-VDU1-CR", "CR-2011 Transfer line corrosion probe", "PC-201", "corrosion probe")
    F("T-VDU1-CR", "iow_limit_standard", 0.25, "mm/y", src="IOW Register (API 584)", ref="IOW-VDU1-CR",
      owner="ROLE-CORR", method="declared")
    tag("T-E301-RF", "E-301 Fouling resistance (calc)", "E-301", "calculated")
    tag("T-E601-RF", "E-601 Fouling resistance (calc)", "E-601", "calculated")

    F("T-CDU1-FI", "latest_value", 196.0, "kbd", src="PI Historian", ref="FI-1001", owner="ROLE-OPS", method="measured")
    F("T-CDU2-FI", "latest_value", 117.0, "kbd", src="PI Historian", ref="FI-2001", owner="ROLE-OPS", method="measured")
    # blending / reformer quality story
    F("T-REF1-RON", "sampling_interval", 24, "h", src="LIMS", ref="SP-REF1-RON", owner="ROLE-LAB", method="declared")
    F("T-REF2-RON", "sampling_interval", 8, "h", src="LIMS", ref="SP-REF2-RON", owner="ROLE-LAB", method="declared")
    F("T-REF1-RON", "ron_std_dev_12m", 1.4, "RON", src="LIMS", ref="REF1-RON-STATS", owner="ROLE-LAB", method="calculated")
    F("T-REF2-RON", "ron_std_dev_12m", 0.5, "RON", src="LIMS", ref="REF2-RON-STATS", owner="ROLE-LAB", method="calculated")
    F("T-REF1-TI", "temp_std_dev_12m", 4.8, "degC", src="PI Historian", ref="TI-1310", owner="ROLE-PROC", method="calculated")
    F("T-REF2-TI", "temp_std_dev_12m", 1.6, "degC", src="PI Historian", ref="TI-2310", owner="ROLE-PROC", method="calculated")
    F("T-E301-RF", "fouling_resistance_trend", "+62% vs clean (12 months)", "", src="PI Historian (calc)", ref="E-301-RF",
      owner="ROLE-PROC", method="calculated", conf="medium")
    F("T-E601-RF", "fouling_resistance_trend", "+14% vs clean (12 months)", "", src="PI Historian (calc)", ref="E-601-RF",
      owner="ROLE-PROC", method="calculated", conf="medium")
    F("T-E301-RF", "last_cleaned", "2024-04-15", "", src="SAP PM", ref="WO-E301-CLEAN", owner="ROLE-MAINT")

    # ================================================================== MATERIAL
    grades = [
        # id, name, api, sulfur, tan, salt_ptb, method
        ("CR-AL", "Arab Light", 33.0, 1.9, 0.1, 5, "indicative"),
        ("CR-BM", "Basrah Medium", 29.0, 2.9, 0.2, 8, "indicative"),
        ("CR-MUR", "Murban", 40.0, 0.8, 0.05, 2, "indicative"),
        ("CR-QM", "Qatar Marine", 36.0, 1.5, 0.1, 4, "indicative"),
        ("CR-DOBA", "Doba", 21.0, 0.1, 4.5, 10, "indicative"),
        ("CR-HSOB", "Heavy Sour Opportunity Blend", 22.0, 3.4, 1.2, 25, "synthetic"),
        ("CR-F1", "F1 Blend", 37.0, 0.6, 0.1, 3, "synthetic"),
    ]
    for gid, gname, api, s, tan, salt, m in grades:
        N(gid, "CrudeGrade", gname, "material")
        src = "Public assay (typical values)" if m == "indicative" else "Synthetic demo assay"
        conf = "medium" if m == "indicative" else "low"
        meth = "indicative" if m == "indicative" else "assumption"
        F(gid, "api_gravity", api, "degAPI", as_of="2026-06-30", src=src, owner="ROLE-CRPLAN", conf=conf, method=meth)
        F(gid, "sulfur", s, "wt%", as_of="2026-06-30", src=src, owner="ROLE-CRPLAN", conf=conf, method=meth)
        F(gid, "tan", tan, "mgKOH/g", as_of="2026-06-30", src=src, owner="ROLE-CRPLAN", conf=conf, method=meth)
        F(gid, "salt_content", salt, "PTB", as_of="2026-06-30", src="Synthetic demo assay", owner="ROLE-CRPLAN",
          conf="low", method="assumption")
    E("CR-F1", "PRODUCED_AT", "FIELD-F1")  # equity grade origin

    # campaigns = crude processed in a window (cargo(s) -> CDU)
    campaigns = [
        # id, grade, site, unit, start, end, slate share, lp uplift $/bbl, treatment cost $
        ("CMP-A1", "CR-HSOB", "ALPHA", "CDU-1", "2025-11-10", "2025-11-24", 0.30, 2.10, 90_000),
        ("CMP-A2H", "CR-HSOB", "ALPHA", "CDU-1", "2026-02-05", "2026-02-20", 0.25, 2.10, 140_000),
        ("CMP-A2D", "CR-DOBA", "ALPHA", "CDU-1", "2026-02-05", "2026-02-20", 0.15, 1.60, 0),
        ("CMP-A3", "CR-HSOB", "ALPHA", "CDU-1", "2026-06-01", "2026-06-18", 0.35, 2.10, 120_000),
    ]
    site_cap = {"ALPHA": 200, "BETA": 120}
    for cid, g, site, u, st, en, share, upl, treat in campaigns:
        days = (date.fromisoformat(en) - date.fromisoformat(st)).days + 1
        vol = share * site_cap[site] * days  # kbbl
        N(cid, "CrudeCampaign", f"{cid} {dict((x[0], x[1]) for x in grades)[g]} campaign", "material",
          start=st, end=en, opportunity=True)
        E(cid, "OF_GRADE", g); E(cid, "PROCESSED_IN", u); E(cid, "DELIVERED_VIA", "TERM-T1")
        f_vol = F(cid, "volume_processed", round(vol, 1), "kbbl", as_of=en, src="Hydrocarbon Accounting",
                  ref=f"HA-{cid}", owner="ROLE-CRPLAN", method="recorded")
        F(cid, "slate_share", share, "fraction", as_of=en, src="Crude Schedule", ref=f"SCH-{cid}", owner="ROLE-CRPLAN")
        f_upl = F(cid, "lp_uplift_per_bbl", upl, "USD/bbl", as_of=st, src="LP Planning Model", ref=f"LP-CASE-{cid}",
                  owner="ROLE-CRPLAN", method="calculated", conf="medium")
        F(cid, "lp_uplift_total", round(vol * 1000 * upl), "USD", as_of=en, src="KG derived",
          owner="ROLE-ECON", method="calculated", conf="medium", lineage=[f_vol, f_upl])
        if treat:
            F(cid, "incremental_treatment_cost", treat, "USD", as_of=en, src="Chemical Treatment Vendor Report",
              ref=f"CHEM-{cid}", owner="ROLE-CORR", method="recorded")
    # base slates (context)
    for cid, g, site, u, vol in [("CMP-AB-AL", "CR-AL", "ALPHA", "CDU-1", 28_000), ("CMP-AB-BM", "CR-BM", "ALPHA", "CDU-1", 16_000),
                                 ("CMP-AB-MUR", "CR-MUR", "ALPHA", "CDU-1", 12_000), ("CMP-AB-QM", "CR-QM", "ALPHA", "CDU-1", 10_000),
                                 ("CMP-BB-AL", "CR-AL", "BETA", "CDU-2", 18_000), ("CMP-BB-MUR", "CR-MUR", "BETA", "CDU-2", 9_000),
                                 ("CMP-BB-F1", "CR-F1", "BETA", "CDU-2", 14_000)]:
        N(cid, "CrudeCampaign", f"{site.title()} base slate — {dict((x[0], x[1]) for x in grades)[g]}", "material",
          start="2025-10-01", end="2026-09-30", opportunity=False)
        E(cid, "OF_GRADE", g); E(cid, "PROCESSED_IN", u)
        E(cid, "DELIVERED_VIA", "TERM-T1")
        F(cid, "volume_processed", vol, "kbbl", as_of="2026-09-28", src="Hydrocarbon Accounting",
          ref=f"HA-{cid}", owner="ROLE-CRPLAN")

    # streams & products
    for n, site in [("1", "ALPHA"), ("2", "BETA")]:
        s = site.title()
        for sid, sname, prod_by, feeds in [
            (f"STR-SRN-{n}", "Straight-run naphtha", f"CDU-{n}", f"REF-{n}"),
            (f"STR-AR-{n}", "Atmospheric residue", f"CDU-{n}", f"VDU-{n}"),
            (f"STR-AGO-{n}", "Atmospheric gasoil", f"CDU-{n}", None),
            (f"STR-VGO-{n}", "Vacuum gasoil", f"VDU-{n}", f"FCC-{n}"),
            (f"STR-VR-{n}", "Vacuum residue", f"VDU-{n}", None),
            (f"STR-FCCG-{n}", "FCC gasoline", f"FCC-{n}", f"GBL-{n}"),
            (f"STR-REFM-{n}", "Reformate", f"REF-{n}", f"GBL-{n}"),
        ]:
            N(sid, "Stream", f"{sname} ({s})", "material")
            E(prod_by, "PRODUCES", sid)
            if feeds:
                E(sid, "FEEDS", feeds)
        N(f"PRD-GAS-{n}", "Product", f"Gasoline RON95 ({s})", "material")
        N(f"PRD-DSL-{n}", "Product", f"Diesel ({s})", "material")
        N(f"PRD-FO-{n}", "Product", f"Fuel oil ({s})", "material")
        E(f"STR-FCCG-{n}", "COMPONENT_OF", f"PRD-GAS-{n}")
        E(f"STR-REFM-{n}", "COMPONENT_OF", f"PRD-GAS-{n}")
        E(f"STR-AGO-{n}", "COMPONENT_OF", f"PRD-DSL-{n}")
        E(f"STR-VR-{n}", "COMPONENT_OF", f"PRD-FO-{n}")
        E(f"PRD-GAS-{n}", "BLENDED_AT", f"GBL-{n}")
    N("MKT-DOM", "Market", "Domestic retail fuels", "material")
    N("MKT-EXP", "Market", "Export — Asia", "material")
    for n in ["1", "2"]:
        E(f"PRD-GAS-{n}", "SOLD_TO", "MKT-DOM"); E(f"PRD-DSL-{n}", "SOLD_TO", "MKT-DOM")
        E(f"PRD-FO-{n}", "SOLD_TO", "MKT-EXP")

    # gasoline quality / giveaway
    for n, prod_kbd, ron in [("1", 55, 95.62), ("2", 30, 95.18)]:
        F(f"PRD-GAS-{n}", "production_rate", prod_kbd, "kbd", src="Hydrocarbon Accounting", owner="ROLE-BLEND")
        F(f"PRD-GAS-{n}", "ron_spec_min", 95.0, "RON", src="Product Specification", ref="SPEC-GAS95",
          owner="ROLE-BLEND", method="declared")
        F(f"PRD-GAS-{n}", "ron_avg_12m", ron, "RON", src="LIMS", ref=f"GBL{n}-CERT-STATS", owner="ROLE-LAB",
          method="calculated")
    F("PRD-GAS-1", "octane_value", 0.60, "USD per RON-bbl", src="Planning assumption", owner="ROLE-CRPLAN",
      conf="low", method="assumption")

    # ================================================================== EVENTS
    iows = [
        ("IOW-001", "T-CDU1-CL", "2025-11-13", 9, 48, "ppm"),
        ("IOW-002", "T-CDU1-CL", "2026-02-08", 11, 65, "ppm"),
        ("IOW-003", "T-CDU1-CL", "2026-06-04", 13, 57, "ppm"),
        ("IOW-004", "T-CDU1-PH", "2026-02-10", 6, 4.9, "pH"),
        ("IOW-005", "T-VDU1-CR", "2026-02-12", 14, 0.45, "mm/y"),
        ("IOW-006", "T-CDU2-CL", "2026-04-02", 1, 24, "ppm"),
    ]
    for iid, t, d, dur, peak, u in iows:
        N(iid, "IOWExceedance", f"{iid} on {b.nodes[t]['name']}", "event", date=d)
        E(iid, "ON_DATAPOINT", t)
        F(iid, "peak_value", peak, u, as_of=d, src="PI Historian / IOW Monitor", ref=iid, owner="ROLE-CORR", method="measured")
        F(iid, "duration", dur, "days", as_of=d, src="PI Historian / IOW Monitor", ref=iid, owner="ROLE-CORR", method="measured")

    alpha_grm_fid = next(f["id"] for f in b.facts if f["subject"] == "SITE-ALPHA" and f["predicate"] == "grm_fy2026")

    def failure(fid, target, d, mode, mech, cost, wo, rate_cut=0, days=0, grm_fid=None, grm=0.0, desc=""):
        # qualify the name with the L6 equipment so L7-L9 failures read clearly
        eqn, cur = b.nodes[target]["name"], target
        while b.nodes[cur]["level"] and b.nodes[cur]["level"] > 6:
            cur = next(e["target"] for e in b.edges if e["source"] == cur and e["rel"] == "PART_OF")
        label = eqn if cur == target else f"{b.nodes[cur]['name'].split(' ')[0]} {eqn.lower()}"
        N(fid, "Failure", f"{fid} {label}", "event", date=d, desc=desc)
        E(fid, "FAILURE_OF", target)
        F(fid, "failure_mode", mode, "", as_of=d, src="SAP PM (ISO 14224 coding)", ref=wo, owner="ROLE-REL")
        F(fid, "failure_mechanism", mech, "", as_of=d, src="SAP PM (ISO 14224 coding)", ref=wo, owner="ROLE-REL")
        N(wo, "WorkOrder", f"{wo} repair", "event", date=d)
        E(wo, "REMEDIATES", fid)
        F(wo, "actual_cost", cost, "USD", as_of=d, src="SAP PM", ref=wo, owner="ROLE-MAINT")
        if rate_cut:
            fr = F(fid, "rate_reduction", rate_cut, "kbd", as_of=d, src="Operations Logbook", ref=fid, owner="ROLE-OPS")
            fd = F(fid, "rate_reduction_days", days, "days", as_of=d, src="Operations Logbook", ref=fid, owner="ROLE-OPS")
            F(fid, "lost_margin", round(rate_cut * 1000 * days * grm), "USD", as_of=d, src="KG derived",
              owner="ROLE-ECON", method="calculated", conf="medium", lineage=[fr, fd, grm_fid])

    corr = "Corrosion (ISO 14224 2.2) — HCl / ammonium chloride"
    failure("FL-001", "E-101A-TU", "2025-12-02", "External leakage – process medium (ELP)", corr, 420_000, "WO-001",
            50, 5, alpha_grm_fid, 8.20, "Tube leak; unit rate cut while isolating")
    failure("FL-002", "E-101B-TU", "2026-03-05", "External leakage – process medium (ELP)", corr, 160_000, "WO-002",
            50, 4, alpha_grm_fid, 8.20, "Tube leak; temporary tube plugging")
    failure("FL-003", "PC-101", "2026-06-28", "External leakage – process medium (ELP)", corr, 310_000, "WO-003",
            80, 6, alpha_grm_fid, 8.20, "Overhead line pinhole; clamp then spool replacement")
    failure("FL-004", "PC-201", "2026-03-20", "Structural deficiency (STD)",
            "Corrosion (ISO 14224 2.2) — naphthenic acid", 95_000, "WO-004", desc="Wall loss beyond corrosion allowance found by UT")

    seal_fail = {
        "P-201A": ["2025-10-20", "2026-01-15", "2026-04-22", "2026-08-10"],
        "P-201B": ["2025-12-18", "2026-04-01", "2026-07-19"],
        "P-501": ["2025-11-05", "2026-03-12", "2026-07-30"],
        "P-401A": ["2025-10-28", "2026-02-02", "2026-05-14", "2026-08-25"],
        "P-401B": ["2026-06-10"],
        "P-306": [],
    }
    k = 100
    for pid, dates in seal_fail.items():
        for d in dates:
            k += 1
            cost = 38_000 if pid.startswith(("P-2", "P-5")) else 35_000
            failure(f"FL-{k}", f"{pid}-MS", d, "External leakage – process medium (ELP)",
                    "Wear / thermal distortion (ISO 14224 1.x)", cost, f"WO-{k}")

    # turnaround
    N("TA-ALPHA-27", "Turnaround", "Refinery Alpha major turnaround 2027", "event", date="2027-03-01")
    E("TA-ALPHA-27", "AT_SITE", "SITE-ALPHA")
    F("TA-ALPHA-27", "scope_freeze_date", "2026-11-15", "", src="TA Planning System", owner="ROLE-TA", method="declared")
    F("TA-ALPHA-27", "start_date", "2027-03-01", "", src="TA Planning System", owner="ROLE-TA", method="declared")
    for sid, tgt, desc in [("SI-01", "E-101A", "Retube & inspect E-101A"), ("SI-02", "V-102", "Accumulator internal inspection"),
                           ("SI-03", "H-101", "Heater tube inspection"), ("SI-04", "C-101", "Column tray replacement"),
                           ("SI-05", "P-201A", "Pump overhaul")]:
        N(sid, "ScopeItem", desc, "event")
        E(sid, "IN_SCOPE_OF", "TA-ALPHA-27"); E(sid, "TARGETS", tgt)

    # ================================================================== PROCESS SPINE
    def p(pid, cls, name, level, parent, owner=None, **props):
        N(pid, cls, name, "process", level, parent, **props)
        if owner:
            E(pid, "OWNED_BY", owner)

    p("VS-PTS", "ValueStream", "Produce-to-Sell", 2, "SEG-UPSTREAM")
    p("VS-LOG", "ValueStream", "Crude Logistics", 2, "SEG-MIDSTREAM")
    p("PG-TERM", "ProcessGroup", "Terminal Operations", 3, "VS-LOG", "ROLE-OPS")
    E("PG-TERM", "ACTS_ON", "TERM-T1"); E("VS-PTS", "ACTS_ON", "FIELD-F1")

    p("VS-C2P", "ValueStream", "Crude-to-Product (Hydrocarbon Supply Chain)", 2, "SEG-DOWNSTREAM")
    p("VS-P2M", "ValueStream", "Plan-to-Maintain (Asset Reliability & Integrity)", 2, "SEG-DOWNSTREAM")
    p("PG-CSV", "ProcessGroup", "Crude Supply & Valuation", 3, "VS-C2P", "ROLE-CRPLAN")
    p("PG-PS", "ProcessGroup", "Planning & Scheduling", 3, "VS-C2P", "ROLE-CRPLAN")
    p("PG-OPS", "ProcessGroup", "Unit Operations", 3, "VS-C2P", "ROLE-OPS")
    p("PG-BLD", "ProcessGroup", "Blending & Product Quality", 3, "VS-C2P", "ROLE-BLEND")
    p("PG-REL", "ProcessGroup", "Reliability Management", 3, "VS-P2M", "ROLE-REL")
    p("PG-INT", "ProcessGroup", "Integrity Management", 3, "VS-P2M", "ROLE-CORR")
    p("PG-TA", "ProcessGroup", "Turnaround Management", 3, "VS-P2M", "ROLE-TA")
    p("PG-WM", "ProcessGroup", "Work Management", 3, "VS-P2M", "ROLE-MAINT")

    p("P-CRSEL", "Process", "Crude Selection & Valuation", 4, "PG-CSV", "ROLE-CRPLAN")
    p("P-LP", "Process", "Monthly LP Planning", 4, "PG-PS", "ROLE-CRPLAN")
    p("P-OPMON", "Process", "Unit Operations Monitoring", 4, "PG-OPS", "ROLE-OPS")
    p("P-BLEND", "Process", "Gasoline Blending", 4, "PG-BLD", "ROLE-BLEND")
    p("P-BADACT", "Process", "Bad Actor Management", 4, "PG-REL", "ROLE-REL")
    p("P-IOW", "Process", "IOW Management", 4, "PG-INT", "ROLE-CORR")
    p("P-CORR", "Process", "Corrosion Management", 4, "PG-INT", "ROLE-CORR")
    p("P-TAS", "Process", "Turnaround Scope Definition", 4, "PG-TA", "ROLE-TA")
    p("P-WO", "Process", "Work Order Execution", 4, "PG-WM", "ROLE-MAINT")
    for proc, assets in {"P-CRSEL": ["CDU-1", "CDU-2"], "P-LP": ["SITE-ALPHA", "SITE-BETA"],
                         "P-OPMON": ["SITE-ALPHA", "SITE-BETA"], "P-BLEND": ["GBL-1", "GBL-2"],
                         "P-BADACT": ["SITE-ALPHA", "SITE-BETA"], "P-IOW": ["CDU-1-OVH", "CDU-2-OVH", "VDU-1-TL"],
                         "P-CORR": ["CDU-1-OVH", "CDU-2-OVH"], "P-TAS": ["SITE-ALPHA"], "P-WO": ["SITE-ALPHA", "SITE-BETA"]}.items():
        for a in assets:
            E(proc, "ACTS_ON", a)

    # deep L5-L10 chains
    chains = [
        # (L4 parent, [(id, cls, name, level)...], governs, consumes-by-decision)
        ("P-CRSEL", [("SP-ASSAY", "SubProcess", "Assay Evaluation", 5),
                     ("ACT-SCREEN", "Activity", "Screen crude contaminants vs metallurgy limits", 6),
                     ("TSK-CONTAM", "Task", "Check TAN / salt / sulfur against unit corrosion envelope", 7),
                     ("DEC-CRACC", "DecisionPoint", "Accept crude into slate & set max blend %", 8),
                     ("DOB-ASSAY", "DataObject", "Crude Assay", 9)]),
        ("P-CRSEL", [("SP-CVAL", "SubProcess", "Crude Valuation (netback)", 5),
                     ("ACT-NETB", "Activity", "Compute crude netback in LP", 6),
                     ("TSK-LPCASE", "Task", "Run marginal-crude LP case", 7),
                     ("DEC-CRBUY", "DecisionPoint", "Buy / reject opportunity cargo", 8),
                     ("DOB-LPCASE", "DataObject", "LP Case", 9)]),
        ("P-IOW", [("SP-IOWMON", "SubProcess", "Exceedance Monitoring & Response", 5),
                   ("ACT-IOWREV", "Activity", "Review IOW exceedances", 6),
                   ("TSK-OVHCL", "Task", "Review overhead water chloride & pH daily", 7),
                   ("DEC-NEUT", "DecisionPoint", "Adjust neutraliser / wash-water rate", 8),
                   ("DOB-IOWREG", "DataObject", "IOW Register", 9)]),
        ("P-BLEND", [("SP-RECIPE", "SubProcess", "Blend Recipe Optimisation", 5),
                     ("ACT-RECIPE", "Activity", "Optimise blend recipe", 6),
                     ("TSK-COMPQ", "Task", "Update component qualities", 7),
                     ("DEC-RECIPE", "DecisionPoint", "Release blend recipe", 8),
                     ("DOB-RECIPE", "DataObject", "Blend Recipe", 9)]),
        ("P-TAS", [("SP-SCOPE", "SubProcess", "Scope Challenge & Freeze", 5),
                   ("ACT-SCOPECH", "Activity", "Challenge scope against integrity threats", 6),
                   ("TSK-RBI", "Task", "Link inspection items to active damage mechanisms", 7),
                   ("DEC-SCOPEFRZ", "DecisionPoint", "Freeze turnaround scope", 8),
                   ("DOB-TASCOPE", "DataObject", "TA Scope List", 9)]),
        ("P-BADACT", [("SP-RCA", "SubProcess", "Failure Analysis (RCA)", 5),
                      ("ACT-FLEET", "Activity", "Compare failure patterns across the fleet", 6),
                      ("TSK-MTBF", "Task", "Compute MTBF by model & service", 7),
                      ("DEC-STD", "DecisionPoint", "Set equipment / seal-plan standard", 8),
                      ("DOB-FAILREC", "DataObject", "Failure Record (ISO 14224)", 9)]),
        ("P-CORR", [("SP-CORRCOST", "SubProcess", "Corrosion Cost Tracking", 5),
                    ("ACT-CORRCOST", "Activity", "Aggregate corrosion repair cost & lost margin", 6),
                    ("TSK-CORRCOST", "Task", "Attribute failures to damage mechanism", 7),
                    ("DEC-CORRBUD", "DecisionPoint", "Set corrosion-control budget", 8),
                    ("DOB-CORRLOG", "DataObject", "Corrosion Cost Log", 9)]),
    ]
    for parent, steps in chains:
        prev = parent
        for sid, cls, name, lvl in steps:
            p(sid, cls, name, lvl, prev)
            prev = sid

    # L10 data elements (process spine) — linked to asset data points or to fact predicates
    def de(did, name, parent, owner, domain, maps_to=None, sla_h=None, measured_by=()):
        p(did, "DataElement", name, 10, parent, owner, domain=domain, maps_to_predicate=maps_to)
        if sla_h:
            F(did, "freshness_sla", sla_h, "h", src="Data Governance Catalogue", owner=owner, method="declared")
        for t in measured_by:
            E(did, "INSTANTIATED_BY", t)

    de("DE-TAN", "Total acid number", "DOB-ASSAY", "ROLE-CRPLAN", "crude quality", "tan")
    de("DE-SALT", "Salt content", "DOB-ASSAY", "ROLE-CRPLAN", "crude quality", "salt_content")
    de("DE-SULF", "Sulfur", "DOB-ASSAY", "ROLE-CRPLAN", "crude quality", "sulfur")
    de("DE-API", "API gravity", "DOB-ASSAY", "ROLE-CRPLAN", "crude quality", "api_gravity")
    de("DE-GRMUP", "LP GRM uplift", "DOB-LPCASE", "ROLE-CRPLAN", "economics", "lp_uplift_per_bbl")
    de("DE-CL", "Overhead water chloride", "DOB-IOWREG", "ROLE-CORR", "integrity", measured_by=["T-CDU1-CL", "T-CDU2-CL"])
    de("DE-PH", "Overhead water pH", "DOB-IOWREG", "ROLE-CORR", "integrity", measured_by=["T-CDU1-PH", "T-CDU2-PH"])
    de("DE-RONREF", "Reformate RON", "DOB-RECIPE", "ROLE-BLEND", "product quality", sla_h=8,
       measured_by=["T-REF1-RON", "T-REF2-RON"])
    de("DE-RONPROD", "Gasoline product RON", "DOB-RECIPE", "ROLE-BLEND", "product quality",
       measured_by=["T-GBL1-RON", "T-GBL2-RON"])
    de("DE-SCOPE", "Scope item inclusion", "DOB-TASCOPE", "ROLE-TA", "integrity")
    de("DE-MTBF", "MTBF by model & service", "DOB-FAILREC", "ROLE-REL", "reliability", "mtbf_days")
    de("DE-FMECH", "Failure mechanism", "DOB-FAILREC", "ROLE-REL", "reliability", "failure_mechanism")
    de("DE-CORRCOST", "Corrosion repair cost & lost margin", "DOB-CORRLOG", "ROLE-CORR", "reliability", "lost_margin")

    # decisions: what they govern and what they consume (as designed today)
    for d, gov, cons in [
        ("DEC-CRACC", ["CDU-1", "CDU-2"], ["DE-TAN", "DE-SALT", "DE-SULF", "DE-API"]),
        ("DEC-CRBUY", ["CDU-1", "CDU-2"], ["DE-GRMUP"]),
        ("DEC-NEUT", ["CDU-1-OVH", "CDU-2-OVH"], ["DE-CL", "DE-PH"]),
        ("DEC-RECIPE", ["GBL-1", "GBL-2"], ["DE-RONREF", "DE-RONPROD"]),
        ("DEC-SCOPEFRZ", ["SITE-ALPHA"], ["DE-SCOPE"]),
        ("DEC-STD", ["SITE-ALPHA", "SITE-BETA"], ["DE-MTBF", "DE-FMECH"]),
        ("DEC-CORRBUD", ["CDU-1-OVH", "CDU-2-OVH"], ["DE-CORRCOST"]),
    ]:
        for g in gov:
            E(d, "GOVERNS", g)
        for c in cons:
            E(d, "CONSUMES", c)

    return b


def main():
    b = build()
    data = dict(
        meta=dict(name="O&G Value Chain Knowledge Graph — demonstration dataset", as_of=DATASET_AS_OF,
                  disclaimer="Synthetic sites, equipment, events and costs. Named crude grades carry indicative "
                             "typical assay values only (method=indicative). Not for commercial decisions."),
        nodes=list(b.nodes.values()), edges=b.edges, facts=b.facts)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1))
    print(f"nodes={len(b.nodes)} edges={len(b.edges)} facts={len(b.facts)} -> {OUT}")


if __name__ == "__main__":
    main()
