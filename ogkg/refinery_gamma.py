"""
Refinery Gamma — whole-refinery extension (v0.4.0), called at the end of cdu_gamma.build().

Adds, on top of the two-train CDU:
  Sector 1b  every other plant unit (L4) with its sections (L5); full-depth FCC-1, HCU-1 and DCU-1 (L6-L10);
             the refinery stream network; groupings (corrosion loops, compressor fleet, SIFs, networks);
             refinery-level process chains (planning, hydrogen, sulfur, conversion units, compressors)
  Sector 1a  new damage mechanisms, equations and equipment models
  Sector 2   capacities, Nelson factors and NCI contributions, stream rates, feed rates and utilisation,
             hydrogen and sulfur balances, conversion-unit KPIs, IOW limits, a year of conversion-unit events

Every derived number is a calculated fact with lineage to its inputs.
"""
from .cdu_gamma import AS_OF, DESIGN_DATE, SITE, TRAINS, _build_equipment, _tag
from .refinery_units import (ACID_GAS_SPLIT, CCR_H2_YIELD, CRUDE_DENSITY, DEEP, GASOLINE_UPGRADE_SPREAD, H2_CONSUMPTION, NELSON_SOURCE,
                             PLOTS, STREAMS, SULFUR_FATES, UNITS)

SKELETON_TAGS = 8           # tag counter key for unit-level tags outside the CDU (8001, 8002, ...)
PROCESSING = {"kbd"}        # capacity unit of units that take a liquid feed


def extend(b, reg_rows, tag_rows):
    N, E, F = b.node, b.edge, b.fact
    fid = lambda s, p: b.fact_obj(s, p)["id"]
    val = lambda s, p: b.fact_value(s, p)

    def utag(parent, ttype, desc, unit, value, kind="sensor"):
        _tag.counter[SKELETON_TAGS] = _tag.counter.get(SKELETON_TAGS, SKELETON_TAGS * 1000) + 1
        tid = f"{ttype}-{_tag.counter[SKELETON_TAGS]}"
        return tid, _tag(b, tag_rows, parent, tid, ttype, desc, unit, kind, value, None, parent)

    # ------------------------------------------------------------------ roles, enterprises, locations, reference (1a)
    N("ROLE-CONV", "Role", "Process Engineer (Conversion units)", "org")
    N("ROLE-ENV", "Role", "Environmental Engineer", "org")
    N("ENT-OEM-D", "Enterprise", "OEM-D Compressors & expanders (fictional manufacturer)", "enterprise")
    N("ENT-OEM-E", "Enterprise", "OEM-E Reciprocating compressors (fictional manufacturer)", "enterprise")
    for lid, ln in PLOTS.items():
        N(lid, "Plot", ln, "location")
        E(lid, "WITHIN", "LOC-SITE")
    for rid, cls, name in [
            ("DM-HTHA", "DamageMechanism", "High-temperature hydrogen attack (API 571 / API 941)"),
            ("DM-NH4HS", "DamageMechanism", "Ammonium bisulfide corrosion (API 571 / API 932-B)"),
            ("DM-PTA", "DamageMechanism", "Polythionic acid stress corrosion cracking (API 571)"),
            ("DM-EROSION", "DamageMechanism", "Erosion / erosion-corrosion by catalyst fines (API 571)"),
            ("DM-TFAT", "DamageMechanism", "Thermal fatigue (API 571)"),
            ("EQ-NCI", "Equation", "Nelson complexity  NCI = Σ fᵢ·Cᵢ / C_CDU"),
            ("EQ-WABT", "Equation", "Weighted average bed temperature  WABT = Σ wᵢ·(T_in,i + T_out,i)/2"),
            ("EQ-H2BAL", "Equation", "Hydrogen balance  Σ supply − Σ chemical consumption = headroom"),
            ("EQ-SBAL", "Equation", "Sulfur balance  S_crude = S_recovered + S_coke + S_residual + S_products + S_emitted"),
            ("APP-CAT-CEMS", "Application", "Continuous emissions monitoring")]:
        N(rid, cls, name, "reference")

    # equipment models for the deep units (pumps, compressors, expander)
    catalogues = {u: fn() for u, (_, fn) in DEEP.items()}
    for eq in catalogues.values():
        for e in eq:
            d = e["design"]
            mid = "MOD-" + d["model"].replace(" ", "-") if "model" in d else None
            if mid and mid not in b.nodes:
                N(mid, "EquipmentModel", d["model"], "reference")
                E(mid, "MANUFACTURED_BY", f"ENT-{d['oem']}")

    # ------------------------------------------------------------------ units (L4) and sections (L5)
    crude_cap = fid(SITE, "crude_capacity")
    for uid, name, onto, plot, cap, cap_unit, nelson, owner, sections, depth in UNITS:
        N(uid, "PlantUnit", name, "asset", 4, SITE, onto_class=onto, model_depth=depth)
        E(uid, "LOCATED_AT", plot)
        key = {"kbbl": "storage_capacity", "berths": "berths"}.get(cap_unit, "design_capacity")
        F(uid, key, cap, cap_unit, as_of=DESIGN_DATE, src="Process design basis", ref=f"DB-{uid}", owner=owner, method="declared")
        for code, sn, sonto in sections:
            N(f"{uid}-{code}", "SectionSystem", sn, "asset", 5, uid, onto_class=sonto)

    # ------------------------------------------------------------------ deep units: equipment L6-L10
    for uid, (tagbase, _) in DEEP.items():
        for e in catalogues[uid]:
            e["train"], e["tagbase"] = None, tagbase
            _build_equipment(b, e, reg_rows, tag_rows)

    # ------------------------------------------------------------------ streams and rates
    for tr, t in TRAINS.items():                  # CDU product streams: rate from the train's product meters
        for i, code in enumerate(("LPG", "NAP", "KERO", "DSL", "AGO", "AR")):
            tag = f"FI-{t}9{i + 1}0"
            F(f"STR-{tr}-{code}", "flow_rate", val(tag, "latest_value"), "kbd", as_of=AS_OF, src="KG derived", owner="ROLE-PLAN",
              method="calculated", lineage=[fid(tag, "latest_value")])
    for tr, off, sw in (("A", 0.9, 55.0), ("B", 0.9, 52.0)):    # CDU streams outside the liquid balance
        F(f"STR-{tr}-OFFGAS", "flow_rate", off, "kbd FOE", as_of=AS_OF, src="Hydrocarbon accounting (FY2026 yield accounting)",
          owner="ROLE-PLAN", method="measured", conf="medium")
        F(f"STR-{tr}-SW", "flow_rate", sw, "m3/h", as_of=AS_OF, src="PI historian", owner="ROLE-OPS", method="measured")
    for sid, name, src, dst, v, unit in STREAMS:
        N(sid, "Stream", name, "material")
        E(src, "PRODUCES", sid)
        E(sid, "FEEDS", dst)
        F(sid, "flow_rate", v, unit, as_of=AS_OF, src="Hydrocarbon accounting (FY2026 yield accounting)", ref=f"HA-{sid}",
          owner="ROLE-PLAN", method="measured", conf="medium")
    F("STR-VDU-VR-DCU", "density", 1.03, "t/m3", as_of=AS_OF, src="LIMS (monthly composite)", owner="ROLE-LAB", method="measured")

    def inflows(uid, unit="kbd"):
        return [e["source"] for e in b.edges if e["rel"] == "FEEDS" and e["target"] == uid
                and (b.fact_obj(e["source"], "flow_rate") or {}).get("unit") == unit]

    # feed rate, feed meter and utilisation for every liquid-feed unit
    for uid, name, onto, plot, cap, cap_unit, nelson, owner, sections, depth in UNITS:
        if cap_unit not in PROCESSING:
            continue
        ins = inflows(uid)
        feed = round(sum(val(s, "flow_rate") for s in ins), 1)
        F(uid, "feed_rate", feed, "kbd", as_of=AS_OF, src="KG derived", owner="ROLE-PLAN", method="calculated",
          lineage=[fid(s, "flow_rate") for s in ins])
        utag(uid, "FI", "Unit feed rate (DCS meter)", "kbd", feed)
        F(uid, "utilisation", round(100 * feed / cap, 1), "%", as_of=AS_OF, src="KG derived", owner="ROLE-PLAN", method="calculated",
          lineage=[fid(uid, "feed_rate"), fid(uid, "design_capacity")])
    for tr in TRAINS:
        u = f"CDU-{tr}"
        F(u, "utilisation", round(100 * val(u, "throughput_fy2026") / val(u, "design_capacity"), 1), "%", as_of=AS_OF, src="KG derived",
          owner="ROLE-PLAN", method="calculated", lineage=[fid(u, "throughput_fy2026"), fid(u, "design_capacity")])

    # ------------------------------------------------------------------ Nelson complexity
    contrib = []
    nelson_units = [(f"CDU-{tr}", ("Crude distillation", 1.0)) for tr in TRAINS] + [(u[0], u[6]) for u in UNITS if u[6]]
    for uid, (cat, factor) in nelson_units:
        F(uid, "nelson_factor", factor, "", as_of=DESIGN_DATE, src=NELSON_SOURCE, ref=cat, owner="ROLE-PLAN", method="indicative",
          conf="medium")
        c = round(factor * val(uid, "design_capacity") / val(SITE, "crude_capacity"), 4)
        contrib.append(F(uid, "nci_contribution", c, "", as_of=DESIGN_DATE, src="KG derived", owner="ROLE-PLAN", method="calculated",
                         lineage=[fid(uid, "nelson_factor"), fid(uid, "design_capacity"), crude_cap]))
    nci = round(sum(f["value"] for f in b.facts if f["id"] in set(contrib)), 2)
    F(SITE, "nelson_complexity_index", nci, "", as_of=DESIGN_DATE, src="KG derived", owner="ROLE-PLAN", method="calculated",
      lineage=contrib)
    E(SITE, "GOVERNED_BY", "EQ-NCI")

    # ------------------------------------------------------------------ hydrogen network
    demand = []
    for uid, rate in H2_CONSUMPTION.items():
        F(uid, "h2_consumption_rate", rate, "scf/bbl", as_of=DESIGN_DATE, src="Process design basis (licensor data)", owner="ROLE-PROC",
          method="declared", conf="medium")
        demand.append(F(uid, "h2_consumption", round(rate * val(uid, "feed_rate") / 1000, 1), "MMSCFD", as_of=AS_OF, src="KG derived",
                        owner="ROLE-PROC", method="calculated", lineage=[fid(uid, "h2_consumption_rate"), fid(uid, "feed_rate")]))
    F("CCR-1", "h2_yield", CCR_H2_YIELD, "scf/bbl", as_of=DESIGN_DATE, src="Process design basis (licensor data)", owner="ROLE-PROC",
      method="declared", conf="medium")
    F("CCR-1", "h2_production", round(CCR_H2_YIELD * val("CCR-1", "feed_rate") / 1000, 1), "MMSCFD", as_of=AS_OF, src="KG derived",
      owner="ROLE-PROC", method="calculated", lineage=[fid("CCR-1", "h2_yield"), fid("CCR-1", "feed_rate")])
    total = round(sum(f["value"] for f in b.facts if f["id"] in set(demand)), 1)
    hmu_tag, hmu_f = utag("HMU-1", "FI", "Hydrogen production (PSA product meter)", "MMSCFD", round(total - val("CCR-1", "h2_production"), 1))
    F("HMU-1", "h2_production", val(hmu_tag, "latest_value"), "MMSCFD", as_of=AS_OF, src="KG derived", owner="ROLE-PROC",
      method="calculated", lineage=[hmu_f])
    F("HMU-1", "utilisation", round(100 * val("HMU-1", "h2_production") / val("HMU-1", "design_capacity"), 1), "%", as_of=AS_OF,
      src="KG derived", owner="ROLE-PLAN", method="calculated", lineage=[fid("HMU-1", "h2_production"), fid("HMU-1", "design_capacity")])
    F(SITE, "h2_demand", total, "MMSCFD", as_of=AS_OF, src="KG derived", owner="ROLE-PROC", method="calculated", lineage=demand)
    cap_f = F(SITE, "h2_supply_capacity", round(val("CCR-1", "h2_production") + val("HMU-1", "design_capacity"), 1), "MMSCFD", as_of=AS_OF,
              src="KG derived", owner="ROLE-PROC", method="calculated", lineage=[fid("CCR-1", "h2_production"), fid("HMU-1", "design_capacity")])
    head = round(val(SITE, "h2_supply_capacity") - total, 1)
    F(SITE, "h2_headroom", head, "MMSCFD", as_of=AS_OF, src="KG derived", owner="ROLE-PROC", method="calculated",
      lineage=[cap_f, fid(SITE, "h2_demand")])
    for sid, name, src, dst, pred in [("STR-CCR-H2", "Reformer net hydrogen", "CCR-1", "UTL-H2", ("CCR-1", "h2_production")),
                                      ("STR-HMU-H2", "SMR hydrogen", "HMU-1", "UTL-H2", ("HMU-1", "h2_production"))] + \
                                     [(f"STR-H2-{u}", f"Hydrogen to {u}", "UTL-H2", u, (u, "h2_consumption")) for u in H2_CONSUMPTION]:
        N(sid, "Stream", name, "material")
        E(src, "PRODUCES", sid)
        E(sid, "FEEDS", dst)
        F(sid, "flow_rate", val(*pred), "MMSCFD", as_of=AS_OF, src="KG derived", owner="ROLE-PROC", method="calculated",
          lineage=[fid(*pred)])
    E("UTL-H2", "GOVERNED_BY", "EQ-H2BAL")

    # ------------------------------------------------------------------ sulfur balance
    grades = [("CR-AL", "CMP-A-AL"), ("CR-BM", "CMP-A-BM"), ("CR-MUR", "CMP-A-MUR")]
    s_avg = round(sum(val(g, "sulfur") * val(c, "slate_share") for g, c in grades), 3)
    F(SITE, "crude_sulfur_avg", s_avg, "wt%", as_of=AS_OF, src="KG derived", owner="ROLE-PLAN", method="calculated",
      lineage=[fid(g, "sulfur") for g, _ in grades] + [fid(c, "slate_share") for _, c in grades])
    F(SITE, "crude_density", CRUDE_DENSITY, "t/m3", as_of=AS_OF, src="Crude assay (blended slate, typical)", owner="ROLE-PLAN",
      method="indicative", conf="medium")
    kbd = val("CDU-A", "throughput_fy2026") + val("CDU-B", "throughput_fy2026")
    F(SITE, "crude_mass_rate", round(kbd * 1000 * 0.158987 * CRUDE_DENSITY), "t/d", as_of=AS_OF, src="KG derived", owner="ROLE-PLAN",
      method="calculated", lineage=[fid("CDU-A", "throughput_fy2026"), fid("CDU-B", "throughput_fy2026"), fid(SITE, "crude_density")])
    s_in = round(val(SITE, "crude_mass_rate") * s_avg / 100)
    F(SITE, "sulfur_in", s_in, "t/d", as_of=AS_OF, src="KG derived", owner="ROLE-ENV", method="calculated",
      lineage=[fid(SITE, "crude_mass_rate"), fid(SITE, "crude_sulfur_avg")])
    fates = [F(SITE, k, v, "t/d", as_of=AS_OF, src=f"Sulfur balance (monthly) — {how}", owner="ROLE-ENV", method="measured", conf="medium")
             for k, v, how in SULFUR_FATES]
    sru_tag, sru_f = utag("SRU-1", "WI", "Sulfur production (pit rundown / weighbridge)", "t/d", s_in - sum(v for _, v, _ in SULFUR_FATES))
    F("SRU-1", "sulfur_production", val(sru_tag, "latest_value"), "t/d", as_of=AS_OF, src="KG derived", owner="ROLE-ENV",
      method="calculated", lineage=[sru_f])
    F("SRU-1", "utilisation", round(100 * val("SRU-1", "sulfur_production") / val("SRU-1", "design_capacity"), 1), "%", as_of=AS_OF,
      src="KG derived", owner="ROLE-PLAN", method="calculated", lineage=[fid("SRU-1", "sulfur_production"), fid("SRU-1", "design_capacity")])
    F(SITE, "sulfur_balance_closure", round(val("SRU-1", "sulfur_production") + sum(v for _, v, _ in SULFUR_FATES) - s_in), "t/d",
      as_of=AS_OF, src="KG derived", owner="ROLE-ENV", method="calculated", lineage=[fid("SRU-1", "sulfur_production"), fid(SITE, "sulfur_in")] + fates)
    for sid, name, src, dst, share in [("STR-ARU-AG", "Amine acid gas (as S)", "ARU-1", "SRU-1", ACID_GAS_SPLIT["ARU-1"]),
                                       ("STR-SWS-AG", "Sour water stripper gas (as S)", "SWS-1", "SRU-1", ACID_GAS_SPLIT["SWS-1"]),
                                       ("STR-SRU-S", "Liquid sulfur", "SRU-1", "MT-1", 1.0)]:
        N(sid, "Stream", name, "material")
        E(src, "PRODUCES", sid)
        E(sid, "FEEDS", dst)
        F(sid, "flow_rate", round(val("SRU-1", "sulfur_production") * share), "t/d", as_of=AS_OF, src="KG derived", owner="ROLE-ENV",
          method="calculated", lineage=[fid("SRU-1", "sulfur_production")])
    E(SITE, "GOVERNED_BY", "EQ-SBAL")
    F(SITE, "reformate_upgrade_spread", GASOLINE_UPGRADE_SPREAD, "USD/bbl", as_of=AS_OF, src="Planning assumption", owner="ROLE-PLAN",
      method="assumption", conf="low")

    # ------------------------------------------------------------------ conversion-unit KPIs
    tagid = lambda eq, text: next(n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint"
                                  and n["props"].get("equipment") == eq and text in n["name"])
    lv = lambda t: fid(t, "latest_value")
    calc = dict(as_of=AS_OF, src="KG derived", method="calculated")
    feed = val("FCC-1", "feed_rate")
    F("FCC-1", "conversion", round(100 * (1 - (val("STR-FCC-LCO", "flow_rate") + val("STR-FCC-SLURRY", "flow_rate")) / feed), 1), "vol%",
      owner="ROLE-CONV", lineage=[fid("STR-FCC-LCO", "flow_rate"), fid("STR-FCC-SLURRY", "flow_rate"), fid("FCC-1", "feed_rate")], **calc)
    for k, eq, text, unit in [("riser_outlet_temperature", "R-301", "(ROT)", "degC"), ("catalyst_loss", "R-302", "Catalyst losses", "t/d"),
                              ("regenerator_afterburn", "R-302", "Afterburn", "degC")]:
        t = tagid(eq, text)
        F("FCC-1", k, val(t, "latest_value"), unit, owner="ROLE-CONV", lineage=[lv(t)], **calc)
    feed = val("HCU-1", "feed_rate")
    F("HCU-1", "conversion", round(100 * (1 - val("STR-HCU-UCO", "flow_rate") / feed), 1), "vol%", owner="ROLE-CONV",
      lineage=[fid("STR-HCU-UCO", "flow_rate"), fid("HCU-1", "feed_rate")], **calc)
    for k, eq in [("wabt_first_stage", "R-401"), ("wabt_cracking", "R-402")]:
        t = tagid(eq, "Weighted average bed")
        F("HCU-1", k, val(t, "latest_value"), "degC", owner="ROLE-CONV", lineage=[lv(t)], **calc)
    coke_feed_t = val("DCU-1", "feed_rate") * 1000 * 0.158987 * val("STR-VDU-VR-DCU", "density")
    F("DCU-1", "coke_yield", round(100 * val("STR-DCU-COKE", "flow_rate") / coke_feed_t, 1), "wt%", owner="ROLE-CONV",
      lineage=[fid("STR-DCU-COKE", "flow_rate"), fid("DCU-1", "feed_rate"), fid("STR-VDU-VR-DCU", "density")], **calc)
    cyc = [tagid(d, "Cycle time") for d in ("D-501A", "D-501B", "D-502A", "D-502B")]
    F("DCU-1", "drum_cycle_time", round(sum(val(t, "latest_value") for t in cyc) / 4, 1), "h", owner="ROLE-CONV",
      lineage=[lv(t) for t in cyc], **calc)

    _groupings(b, tagid)
    _process_chains(b)
    _applications(b)
    _events(b, tagid)


# ============================================================================ groupings and physics
def _groupings(b, tagid):
    N, E = b.node, b.edge

    def grp(gid, cls, name, owner, members):
        N(gid, cls, name, "grouping")
        E(gid, "OWNED_BY", owner)
        for m in members:
            E(m, "MEMBER_OF", gid)
    eq = {n["id"]: n for n in b.nodes.values() if n["cls"] == "EquipmentUnit" and n["props"].get("plant_unit") in DEEP}
    grp("CL-FCC-OVH", "CorrosionLoop", "Corrosion loop: FCC main fractionator overhead", "ROLE-CORR",
        ["PC-302", "E-310A", "E-310B", "E-311", "V-301", "P-305A", "P-305B", "P-307A", "P-307B", "C-301", "X-301"])
    grp("CL-FCC-CAT", "CorrosionLoop", "Corrosion loop: FCC catalyst circuit (erosion)", "ROLE-CORR",
        ["R-301", "R-302", "SV-301", "SV-302", "EX-301", "PC-301"])
    grp("CL-HCU-REAC", "CorrosionLoop", "Corrosion loop: HCU reactor effluent air coolers (NH4HS)", "ROLE-CORR",
        ["PC-401", "E-410A", "E-410B", "E-410C", "E-410D", "V-402", "V-403", "X-401", "P-402A", "P-402B"])
    grp("CL-HCU-HTHA", "CorrosionLoop", "Corrosion loop: HCU high-temperature hydrogen service (HTHA)", "ROLE-CORR",
        ["H-401", "R-401", "R-402", "E-401", "E-402", "V-401", "PC-402"])
    grp("CL-DCU-HOT", "CorrosionLoop", "Corrosion loop: coker heaters, drums & transfer lines", "ROLE-CORR",
        ["H-501", "H-502", "PC-501", "D-501A", "D-501B", "D-502A", "D-502B", "PC-502", "P-501A", "P-501B"])
    grp("FLT-COMP", "Fleet", "Fleet: process compressors & expanders", "ROLE-ROT",
        [e for e, n in eq.items() if n["props"]["eq_class"] in ("Compressor", "Expander")])
    grp("SIF-FCC-SV", "SafetyInstrumentedFunction", "SIF: slide-valve low differential pressure (reversal protection)", "ROLE-INST",
        ["SV-301", "SV-302", tagid("SV-301", "pressure drop"), tagid("SV-302", "pressure drop")])
    grp("SIF-HCU-DEP", "SafetyInstrumentedFunction", "SIF: HCU emergency depressuring on reactor temperature runaway", "ROLE-INST",
        ["R-401", "R-402"] + [n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint"
                              and n["props"].get("equipment") in ("R-401", "R-402") and "outlet temperature" in n["name"]])
    grp("SIF-DCU-HTR", "SafetyInstrumentedFunction", "SIF: coker heater low pass-flow trip", "ROLE-INST",
        ["H-501", "H-502"] + [n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint"
                              and n["props"].get("equipment") in ("H-501", "H-502") and "Pass" in n["name"] and "flow" in n["name"]])
    for u, name in [("FCC-1", "FCC"), ("HCU-1", "hydrocracker"), ("DCU-1", "delayed coker")]:
        grp(f"CC-{u[:3]}", "CostCentre", f"Cost centre: {name}", "ROLE-MAINT", [u])
    grp("NET-H2", "Grouping", "Network: hydrogen (producers, header, consumers)", "ROLE-PROC",
        ["HMU-1", "CCR-1", "UTL-H2"] + list(H2_CONSUMPTION))
    grp("NET-SULFUR", "Grouping", "Network: sulfur (amine, sour water, SRU)", "ROLE-ENV", ["ARU-1", "SWS-1", "SRU-1"])
    grp("GRP-GASOLINE", "Grouping", "Gasoline pool contributors", "ROLE-PLAN",
        sorted({s for sid, _, s, d, _, _ in STREAMS if d == "GBL-1"}))
    for h in ("H-301", "H-401", "H-501", "H-502"):
        E(h, "MEMBER_OF", "UT-FUELGAS")

    # physics and damage-mechanism links (Sector 1b -> 1a)
    loops = lambda e: set(b.targets(e, "MEMBER_OF"))
    for e, n in eq.items():
        onto, T = n["props"]["onto_class"], b.fact_value(e, "service_temperature") or 0
        fluid = n["props"]["service_fluid"].lower()
        if onto in ("ShellAndTubeHX", "AirCooledHX"):
            E(e, "GOVERNED_BY", "EQ-DUTY"); E(e, "GOVERNED_BY", "EQ-FOUL")
        if onto == "FiredHeater":
            E(e, "GOVERNED_BY", "EQ-HTREFF"); E(e, "SUSCEPTIBLE_TO", "DM-CREEP", source="RBI study 2024")
        if onto == "CentrifugalPump":
            E(e, "GOVERNED_BY", "EQ-AFFINITY")
        if onto == "FixedBedReactor":
            E(e, "GOVERNED_BY", "EQ-WABT")
        ls = loops(e)
        if "CL-HCU-HTHA" in ls:
            E(e, "SUSCEPTIBLE_TO", "DM-HTHA", source="API 941 review 2025")
        if "CL-HCU-REAC" in ls or "CL-FCC-OVH" in ls:
            E(e, "SUSCEPTIBLE_TO", "DM-NH4HS", source="RBI study 2024")
        if "CL-FCC-OVH" in ls:
            E(e, "SUSCEPTIBLE_TO", "DM-NH4CL", source="RBI study 2024")
        if "CL-FCC-CAT" in ls:
            E(e, "SUSCEPTIBLE_TO", "DM-EROSION", source="RBI study 2024")
        if onto == "CokeDrum" or e == "PC-502":
            E(e, "SUSCEPTIBLE_TO", "DM-TFAT", source="Coke drum fitness-for-service 2025")
        if any(b.fact_value(e, k) == "SS347" for k in ("coil_metallurgy", "material", "tube_metallurgy")):
            E(e, "SUSCEPTIBLE_TO", "DM-PTA", source="Shutdown protection procedure (NACE SP0170)")
        if T >= 230 and not any(k in fluid for k in ("air", "flue", "bfw", "catalyst", "steam")):
            E(e, "SUSCEPTIBLE_TO", "DM-SULF", source="RBI study 2024")



# ============================================================================ process spine
def _process_chains(b):
    N, E = b.node, b.edge

    def p(pid, cls, name, level, parent, owner=None, **props):
        N(pid, cls, name, "process", level, parent, **props)
        if owner:
            E(pid, "OWNED_BY", owner)
    for gid, gn, vs, owner in [("PG-PLAN", "Planning & Scheduling", "VS-C2P", "ROLE-PLAN"),
                               ("PG-NET", "Hydrogen & Sulfur Networks", "VS-C2P", "ROLE-PROC"),
                               ("PG-CONV", "Conversion Unit Operations", "VS-C2P", "ROLE-CONV")]:
        p(gid, "ProcessGroup", gn, 3, vs, owner)
    tags = [n for n in b.nodes.values() if n["cls"] == "DataPoint"]
    where = lambda pred: [n["id"] for n in tags if pred(n)]
    on = lambda eqs, text: where(lambda n: n["props"].get("equipment") in eqs and text in n["name"])
    liquid_units = [u[0] for u in UNITS if u[5] in PROCESSING]
    chains = [
        dict(proc=("P-PLAN", "Refinery planning & crude selection", "PG-PLAN", "ROLE-PLAN", [SITE]),
             steps=[("SP-PLAN", "Monthly planning cycle"), ("ACT-SLATE", "Evaluate crude slate and unit rates"),
                    ("TSK-CONSTR", "Check unit capacity, hydrogen and sulfur constraints"),
                    ("DEC-SLATE", "Select crude slate and unit rates"), ("DOB-PLAN", "Monthly operating plan")],
             governs=[SITE],
             des=[("DE-UNITFEED", "Unit feed rates", "throughput", on(liquid_units, "Unit feed rate"), None),
                  ("DE-CRUDESULF", "Crude slate sulfur", "crude quality", [], "crude_sulfur_avg"),
                  ("DE-H2HEAD", "Hydrogen headroom", "hydrogen", [], "h2_headroom"),
                  ("DE-SRULOAD", "SRU load", "sulfur", on(["SRU-1"], "Sulfur production"), 24),
                  ("DE-NCI", "Nelson complexity contribution", "economics", [], "nci_contribution")]),
        dict(proc=("P-H2", "Hydrogen network management", "PG-NET", "ROLE-PROC", ["HMU-1", "CCR-1", "UTL-H2"]),
             steps=[("SP-H2", "Hydrogen balance"), ("ACT-H2", "Balance producers and consumers"),
                    ("TSK-H2", "Review HMU load, reformer hydrogen and consumer demand"),
                    ("DEC-H2", "Set HMU rate and consumer priority"), ("DOB-H2BAL", "Daily hydrogen balance sheet")],
             governs=["HMU-1", "UTL-H2"],
             des=[("DE-H2PROD", "SMR hydrogen production", "hydrogen", on(["HMU-1"], "Hydrogen production"), None),
                  ("DE-H2CONS", "Hydrogen consumption by unit", "hydrogen", [], "h2_consumption"),
                  ("DE-H2MUC", "Make-up compressor discharge", "hydrogen", on(["K-402A", "K-402B"], "Stage 3 discharge pressure"), None)]),
        dict(proc=("P-SULF", "Sulfur management & emissions", "PG-NET", "ROLE-ENV", ["ARU-1", "SWS-1", "SRU-1"]),
             steps=[("SP-SULF", "Sulfur balance & SO2 compliance"), ("ACT-SULF", "Track sulfur in and out"),
                    ("TSK-SULF", "Review SRU load, acid-gas routing and stack SO2"),
                    ("DEC-SULF", "Limit crude sulfur or shed acid gas"), ("DOB-SBAL", "Monthly sulfur balance & emissions report")],
             governs=["SRU-1"],
             des=[("DE-SPROD", "Sulfur production", "sulfur", on(["SRU-1"], "Sulfur production"), None),
                  ("DE-SO2", "Stack SO2", "environment", on(["B-301"], "Stack SO2"), None),
                  ("DE-SEMIT", "Sulfur emitted as SO2", "environment", [], "sulfur_emitted_as_so2")]),
        dict(proc=("P-FCC", "FCC operation & catalyst management", "PG-CONV", "ROLE-CONV", ["FCC-1"]),
             steps=[("SP-FCC", "Reactor-regenerator optimisation"), ("ACT-FCC", "Tune ROT, cat/oil and catalyst additions"),
                    ("TSK-FCC", "Review ROT, regenerator temperatures and catalyst losses"),
                    ("DEC-FCC", "Set ROT and fresh catalyst rate"), ("DOB-FCCLOG", "FCC daily performance report")],
             governs=["R-301", "R-302"],
             des=[("DE-ROT", "Riser outlet temperature", "operations", on(["R-301"], "(ROT)"), None),
                  ("DE-CATLOSS", "Catalyst losses", "reliability", on(["R-302"], "Catalyst losses"), None),
                  ("DE-AFTERBURN", "Regenerator afterburn", "integrity", on(["R-302"], "Afterburn"), None)]),
        dict(proc=("P-HCU", "Hydrocracker operation & catalyst cycle", "PG-CONV", "ROLE-CONV", ["HCU-1"]),
             steps=[("SP-HCU", "Conversion & catalyst-cycle management"), ("ACT-HCU", "Adjust WABT and quench"),
                    ("TSK-HCU", "Review WABT, reactor dP, REAC wash water and H2 purity"),
                    ("DEC-HCU", "Set reactor temperatures and wash-water rate"), ("DOB-HCULOG", "HCU catalyst-cycle log")],
             governs=["R-401", "R-402", "E-410A", "E-410B", "E-410C", "E-410D"],
             des=[("DE-WABT", "Weighted average bed temperature", "operations", on(["R-401", "R-402"], "Weighted average bed"), None),
                  ("DE-RXDP", "Reactor pressure drop", "operations", on(["R-401", "R-402"], "Reactor pressure drop"), None),
                  ("DE-WASHW", "REAC wash-water rate", "integrity", on(["X-401"], "Injection rate"), None)]),
        dict(proc=("P-DCU", "Coker cycle & heater run-length management", "PG-CONV", "ROLE-CONV", ["DCU-1"]),
             steps=[("SP-DCU", "Drum cycle & heater management"), ("ACT-DCU", "Plan drum switches and heater spalling"),
                    ("TSK-DCU", "Review cycle times, heater TMT and drum cycle counts"),
                    ("DEC-DCU", "Set cycle time and spalling schedule"), ("DOB-DCULOG", "Coker drum-cycle log")],
             governs=["H-501", "H-502", "D-501A", "D-501B", "D-502A", "D-502B"],
             des=[("DE-CYCLE", "Drum cycle time", "operations", on(["D-501A", "D-501B", "D-502A", "D-502B"], "Cycle time"), None),
                  ("DE-CKTMT", "Coker heater TMT", "integrity", on(["H-501", "H-502"], "(TMT)"), None),
                  ("DE-DRUMCYC", "Cumulative drum cycles", "integrity", on(["D-501A", "D-501B", "D-502A", "D-502B"], "Cumulative"), None)]),
        dict(proc=("P-COMPREL", "Compressor reliability", "PG-REL", "ROLE-ROT", ["FCC-1", "HCU-1", "DCU-1"]),
             steps=[("SP-COMP", "Compressor condition monitoring"), ("ACT-COMP", "Review compressor condition"),
                    ("TSK-COMP", "Review vibration, surge margin and valve temperatures"),
                    ("DEC-COMP", "Raise repair priority / plan changeover"), ("DOB-COMPREC", "Compressor condition record")],
             governs=["K-301", "K-302", "K-401", "K-402A", "K-402B", "K-501"],
             des=[("DE-CVIB", "Compressor vibration", "reliability", where(lambda n: "Journal bearing vibration" in n["name"]), None),
                  ("DE-SURGE", "Surge margin", "reliability", where(lambda n: "Surge margin" in n["name"]), None),
                  ("DE-VALVET", "Recip valve temperature", "reliability", where(lambda n: "Valve cover temperature" in n["name"]), None)]),
    ]
    for ch in chains:
        pid, pn, pg, owner, acts = ch["proc"]
        p(pid, "Process", pn, 4, pg, owner)
        for a in acts:
            E(pid, "ACTS_ON", a)
        prev = pid
        for lvl, (sid, sn) in zip(range(5, 10), ch["steps"]):
            p(sid, {5: "SubProcess", 6: "Activity", 7: "Task", 8: "DecisionPoint", 9: "DataObject"}[lvl], sn, lvl, prev)
            prev = sid
        dec, dob = ch["steps"][3][0], ch["steps"][4][0]
        for g in ch["governs"]:
            E(dec, "GOVERNS", g)
        for did, dn, domain, inst, extra in ch["des"]:
            p(did, "DataElement", dn, 10, dob, owner, domain=domain, maps_to_predicate=extra if isinstance(extra, str) else None)
            if isinstance(extra, int):
                b.fact(did, "freshness_sla", extra, "h", as_of=DESIGN_DATE, src="Data governance catalogue", owner=owner, method="declared")
            for tg in inst:
                E(did, "INSTANTIATED_BY", tg)
            E(dec, "CONSUMES", did)


def _applications(b):
    N, E = b.node, b.edge
    for aid, an, cat, scope in [("APP-DCS-CONV", "DCS — conversion complex", "APP-CAT-DCS", ["FCC-1", "HCU-1", "DCU-1", "VGOHT-1"]),
                                ("APP-APC-FCC", "APC — FCC", "APP-CAT-APC", ["FCC-1"]),
                                ("APP-APC-HCU", "APC — hydrocracker", "APP-CAT-APC", ["HCU-1"]),
                                ("APP-CEMS", "CEMS — Gamma stacks & flares", "APP-CAT-CEMS", ["SRU-1", "UTL-FLR", "FCC-1"])]:
        N(aid, "ApplicationInstance", an, "application")
        E(aid, "INSTANCE_OF", cat)
        for s in scope:
            E(aid, "SCOPED_TO", s)
    for aid, procs in [("APP-DCS-CONV", ["P-FCC", "P-HCU", "P-DCU"]), ("APP-APC-FCC", ["P-FCC"]), ("APP-APC-HCU", ["P-HCU"]),
                       ("APP-CEMS", ["P-SULF"]), ("APP-LP", ["P-PLAN", "P-H2"]), ("APP-PI", ["P-H2", "P-SULF", "P-DCU"]),
                       ("APP-CMMS", ["P-COMPREL"]), ("APP-LIMS", ["P-PLAN"])]:
        for pr in procs:
            E(aid, "SUPPORTS", pr)
    for aid, dob in [("APP-LP", "DOB-PLAN"), ("APP-CEMS", "DOB-SBAL"), ("APP-PI", "DOB-H2BAL")]:
        E(aid, "SYSTEM_OF_RECORD_FOR", dob)


# ============================================================================ Sector 2: limits and events
def _events(b, tagid):
    N, E, F = b.node, b.edge, b.fact
    lim = lambda tag, key, v, u, owner="ROLE-CORR": F(tag, key, v, u, as_of=DESIGN_DATE, src="IOW register (API 584)", owner=owner,
                                                     method="declared")
    for h, std, crit in [("H-301", 520, 560), ("H-401", 560, 600), ("H-501", 650, 680), ("H-502", 650, 680)]:
        for pz in range(1, 5):
            t = tagid(h, f"Pass {pz} tube-metal")
            lim(t, "iow_limit_standard", std, "degC"); lim(t, "iow_limit_critical", crit, "degC")
    for r, beds in (("R-401", 3), ("R-402", 4)):
        for i in range(1, beds + 1):
            lim(tagid(r, f"Bed {i} outlet temperature"), "iow_limit_high", 425, "degC", "ROLE-CONV")
        lim(tagid(r, "Shell skin temperature"), "iow_limit_high", 425, "degC")
    lim(tagid("R-302", "Dilute-phase temperature"), "iow_limit_high", 740, "degC", "ROLE-CONV")
    lim(tagid("X-401", "Injection rate"), "iow_limit_low", 22000, "L/h")
    for pc in ("PC-301", "PC-302", "PC-401", "PC-402", "PC-501", "PC-502"):
        lim(tagid(pc, "Corrosion probe"), "iow_limit_standard", 0.25, "mm/y")
    lim(tagid("V-301", "chloride"), "iow_limit_standard", 20, "ppm")
    lim(tagid("PC-302", "dew-point margin"), "iow_limit_low", 14, "degC")
    for n in [n for n in b.nodes.values() if n["cls"] == "DataPoint" and n["props"].get("unit") == "um" and "vibration" in n["name"]]:
        F(n["id"], "alert_limit", 50, "um", as_of=DESIGN_DATE, src="Condition monitoring standard (API 617 / 670)", owner="ROLE-ROT",
          method="declared")

    def iow(iid, tag, d, peak, dur, u, owner="ROLE-CORR"):
        N(iid, "IOWExceedance", f"{iid} on {b.nodes[tag]['name']}", "event", date=d)
        E(iid, "ON_DATAPOINT", tag)
        F(iid, "peak_value", peak, u, as_of=d, src="PI historian / IOW monitor", ref=iid, owner=owner, method="measured")
        F(iid, "duration", dur, "days", as_of=d, src="PI historian / IOW monitor", ref=iid, owner=owner, method="measured")
    iow("IOW-D01", tagid("H-502", "Pass 3 tube-metal"), "2026-06-10", 663, 3, "degC")
    iow("IOW-D02", tagid("H-502", "Pass 3 tube-metal"), "2026-09-02", 671, 5, "degC")
    iow("IOW-H01", tagid("R-402", "Bed 4 outlet temperature"), "2026-07-09", 431, 0.2, "degC", "ROLE-CONV")
    iow("IOW-F01", tagid("R-302", "Dilute-phase temperature"), "2026-08-05", 752, 4, "degC", "ROLE-CONV")
    iow("IOW-H02", tagid("X-401", "Injection rate"), "2026-02-20", 17500, 9, "L/h")

    grm = b.fact_obj(SITE, "grm_fy2026")

    def failure(fid_, target, d, mode, mech, cost, wo, rate_cut=0, days=0, desc=""):
        N(fid_, "Failure", f"{fid_} {b.nodes[target]['name']}", "event", date=d, desc=desc)
        E(fid_, "FAILURE_OF", target)
        F(fid_, "failure_mode", mode, "", as_of=d, src="CMMS (ISO 14224 coding)", ref=wo, owner="ROLE-MAINT")
        F(fid_, "failure_mechanism", mech, "", as_of=d, src="CMMS (ISO 14224 coding)", ref=wo, owner="ROLE-MAINT")
        N(wo, "WorkOrder", f"{wo} repair", "event", date=d)
        E(wo, "REMEDIATES", fid_)
        F(wo, "actual_cost", cost, "USD", as_of=d, src="CMMS", ref=wo, owner="ROLE-MAINT")
        if rate_cut:
            fr = F(fid_, "rate_reduction", rate_cut, "kbd", as_of=d, src="Operations logbook", owner="ROLE-OPS")
            fd = F(fid_, "rate_reduction_days", days, "days", as_of=d, src="Operations logbook", owner="ROLE-OPS")
            F(fid_, "lost_margin", round(rate_cut * 1000 * days * grm["value"]), "USD", as_of=d, src="KG derived", owner="ROLE-PLAN",
              method="calculated", conf="medium", lineage=[fr, fd, grm["id"]])
    failure("FL-H01", "E-410C-TUBES", "2026-03-18", "External leakage – process medium (ELP)",
            "Corrosion (ISO 14224 2.2) — ammonium bisulfide, low wash-water period", 520000, "WO-H01", 40, 6,
            "REAC tube leak; bundle plugged, unit at reduced rate")
    failure("FL-H02", "K-401-SEALS_C", "2026-07-09", "Spurious stop (UST)", "Dry gas seal primary ring failure", 180000, "WO-H02",
            85.9, 2, "Recycle compressor trip; unit depressured and restarted")
    failure("FL-D01", "D-501B-SHELL", "2026-05-20", "Structural deficiency (STD)", "Thermal fatigue — shell bulging at course 3/4 weld",
            1100000, "WO-D01", 42, 12, "Laser scan found bulge; weld overlay repair; one drum pair out")
    failure("FL-F01", "R-302-CYC2", "2026-08-02", "Parameter deviation (PDE)", "Erosion (ISO 14224 2.x) — secondary cyclone dipleg",
            210000, "WO-F01", desc="Catalyst losses above 3 t/d; extra fresh catalyst until the turnaround")
    N("WO-D02", "WorkOrder", "WO-D02 online spalling (H-502)", "event", date="2026-06-14")
    E("WO-D02", "PERFORMED_ON", "H-502")
    F("WO-D02", "actual_cost", 85000, "USD", as_of="2026-06-14", src="CMMS", ref="WO-D02", owner="ROLE-MAINT")
    F("WO-D02", "work_type", "Corrective — online spalling", "", as_of="2026-06-14", src="CMMS", ref="WO-D02", owner="ROLE-MAINT")
