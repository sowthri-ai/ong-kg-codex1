"""
Refinery Gamma — whole-refinery process layer (v0.5), called from cdu_gamma.build().

Adds, on top of the two-train CDU:
  Sector 1b  every other plant unit (L4) with its sections (L5); full-depth FCC-1, HCU-1 and DCU-1 (L6-L10);
             the stream network on a volume AND mass basis; hydrogen, sulfur, sour-water, amine, fuel-gas, steam,
             power and cooling-water networks; corrosion loops, SIFs and cost centres; refinery process chains
  Sector 2   capacities, Nelson factors, stream rates and densities, feed rates, independent feed meters with
             reconciliation, unit mass closures, hydrogen and sulfur balances with their residuals, utility balances,
             process KPIs, IOW limits and a year of conversion-unit events

Rule for balances (council finding IN-W1): meters and accounting are independent sources, and every balance
reports its residual as a calculated fact. Nothing is back-calculated and then labelled as a measurement.
"""
from . import gamma_events as ev
from .cdu_gamma import AS_OF, DESIGN_DATE, SITE, TRAINS, _build_equipment, _tag, jitter
from .refinery_units import (ARU_ACID_GAS_S_MEASURED, BBL_M3, CCR_H2_PURITY, CCR_H2_YIELD, CDU_DENSITY, CDU_OFFGAS_TD, CRUDE_DENSITY,
                             CW_USE, DEEP, FCC_COKE_SULFUR, FCC_COKE_TD, FIRED_DUTY, FLARE_NORMAL_TD, FUEL_GAS_LHV,
                             GASOLINE_UPGRADE_SPREAD, GRID_IMPORT_MEASURED, H2_CONSUMPTION, H2_EFFICIENCY, H2_T_PER_MMSCF,
                             HMU_FUEL_GAS_TD, HMU_METER_BIAS, HMU_PURITY, NELSON_SOURCE, NG_TO_FG_MEASURED, PLOTS,
                             POWER_BASE_LOADS, POWER_SOURCES, RICH_AMINE, SMR_CO2_T_PER_T_H2, SMR_NG_PER_MSCF, SOUR_WATER,
                             SRU_PRODUCTION_MEASURED, SRU_RECOVERY, SRU_TRAINS, STEAM_CONSUMERS, STEAM_LOSSES_DECLARED,
                             STEAM_PRODUCERS, STREAMS, SULFUR_CONTENT, SULFUR_EMITTED_OTHER, UNIT_GAS, UNITS,
                             VGO_IMPORT_SULFUR)

SKELETON_TAGS = 8           # tag counter key for unit-level tags outside the CDU (8001, 8002, ...)
PROCESSING = {"kbd"}        # capacity unit of units that take a liquid feed
ACC = "Hydrocarbon accounting (FY2026 yield accounting)"


def extend(b, reg_rows, tag_rows):
    N, E, F = b.node, b.edge, b.fact
    fid = lambda s, p: b.fact_obj(s, p)["id"]
    val = lambda s, p: b.fact_value(s, p)
    calc = lambda subj, pred, v, unit, lineage, owner="ROLE-PROC", **kw: F(subj, pred, v, unit, as_of=AS_OF, src="KG derived",
                                                                          owner=owner, method="calculated", lineage=lineage, **kw)

    def utag(parent, ttype, desc, unit, value, kind="sensor"):
        _tag.counter[SKELETON_TAGS] = _tag.counter.get(SKELETON_TAGS, SKELETON_TAGS * 1000) + 1
        tid = f"{ttype if kind != 'lab' else 'LAB'}-{_tag.counter[SKELETON_TAGS]}"
        return tid, _tag(b, tag_rows, parent, tid, ttype, desc, unit, kind, value, None, parent, plant_unit=parent)

    # ------------------------------------------------------------------ roles, enterprises, locations, reference (1a)
    N("ROLE-CONV", "Role", "Process Engineer (Conversion units)", "org")
    N("ROLE-ENV", "Role", "Environmental Engineer", "org")
    N("ENT-OEM-D", "Enterprise", "OEM-D Compressors & expanders (fictional manufacturer)", "enterprise")
    N("ENT-OEM-E", "Enterprise", "OEM-E Reciprocating compressors (fictional manufacturer)", "enterprise")
    for lid, ln in PLOTS.items():
        N(lid, "Plot", ln, "location")
        E(lid, "WITHIN", "LOC-SITE")
    for rid, cls, name in [
            ("EQ-NCI", "Equation", "Nelson complexity  NCI = Σ fᵢ·Cᵢ / C_CDU"),
            ("EQ-WABT", "Equation", "Weighted average bed temperature  WABT = Σ wᵢ·(T_in,i + T_out,i)/2"),
            ("EQ-H2BAL", "Equation", "Hydrogen balance  Σ supply − Σ make-up demand = residual"),
            ("EQ-SBAL", "Equation", "Sulfur balance  S_in − (S_recovered + S_in products + S_emitted) = unaccounted"),
            ("EQ-MASS", "Equation", "Unit mass balance  Σ m_out / (Σ m_in + m_H2) = closure"),
            ("APP-CAT-CEMS", "Application", "Continuous emissions monitoring")]:
        N(rid, cls, name, "reference")

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
        from .identity import UNIT_CODES
        N(uid, "PlantUnit", name, "asset", 4, SITE, onto_class=onto, model_depth=depth,
          aliases=[uid.replace("-", ""), name], external_ids={"SAP_FL": f"GAM-{uid}", "PI_AREA": UNIT_CODES.get(uid, "")})
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
    E("EX-301", "DRIVER_OF", "K-302")

    # ------------------------------------------------------------------ streams: volume and mass basis
    def density(sid, v, how="LIMS (monthly composite)"):
        F(sid, "density", v, "t/m3", as_of=AS_OF, src=how, owner="ROLE-LAB", method="measured", conf="medium")

    def mass_rate(sid):
        f = b.fact_obj(sid, "flow_rate")
        if f["unit"] == "t/d":
            return fid(sid, "flow_rate")
        return calc(sid, "mass_rate", round(f["value"] * 1000 * BBL_M3 * val(sid, "density")), "t/d",
                    [f["id"], fid(sid, "density")], owner="ROLE-PLAN")

    for tr, t in TRAINS.items():                  # CDU product streams: rate from the train's product meters
        for i, code in enumerate(("LPG", "NAP", "KERO", "DSL", "AGO", "AR")):
            tag = f"FI-{t}9{i + 1}0"
            sid = f"STR-{tr}-{code}"
            F(sid, "flow_rate", val(tag, "latest_value"), "kbd", as_of=AS_OF, src="KG derived", owner="ROLE-PLAN",
              method="calculated", lineage=[fid(tag, "latest_value")])
            density(sid, CDU_DENSITY[code])
            mass_rate(sid)
        F(f"STR-{tr}-OFFGAS", "flow_rate", CDU_OFFGAS_TD[tr], "t/d", as_of=AS_OF, src=ACC, owner="ROLE-PLAN", method="measured",
          conf="medium")
    for sid, name, src, dst, v, unit, dens in STREAMS:
        N(sid, "Stream", name, "material", aliases=[name])
        E(src, "PRODUCES", sid)
        E(sid, "FEEDS", dst)
        F(sid, "flow_rate", v, unit, as_of=AS_OF, src=ACC, ref=f"HA-{sid}", owner="ROLE-PLAN", method="measured", conf="medium")
        if dens:
            density(sid, dens)
            mass_rate(sid)
    for uid, td in UNIT_GAS.items():             # measured off-gas / light ends to the fuel-gas system
        sid = f"STR-GAS-{uid}"
        N(sid, "Stream", f"Off-gas & light ends from {uid}", "material")
        E(uid, "PRODUCES", sid)
        E(sid, "FEEDS", "UTL-FG")
        F(sid, "flow_rate", td, "t/d", as_of=AS_OF, src="PI historian (gas meter, density-compensated)", owner="ROLE-OPS",
          method="measured", conf="medium")
    F("FCC-1", "coke_make", FCC_COKE_TD, "t/d", as_of=AS_OF, src="KG derived (air-rate coke burn)", owner="ROLE-CONV",
      method="measured", conf="medium")

    def inflows(uid, unit="kbd"):
        return [e["source"] for e in b.edges if e["rel"] == "FEEDS" and e["target"] == uid
                and (b.fact_obj(e["source"], "flow_rate") or {}).get("unit") == unit]

    def outflows(uid):
        return [e["target"] for e in b.edges if e["rel"] == "PRODUCES" and e["source"] == uid and b.fact_obj(e["target"], "flow_rate")]

    # feed rate (accounting), feed meter (DCS, independent) and utilisation for every liquid-feed unit
    for uid, name, onto, plot, cap, cap_unit, nelson, owner, sections, depth in UNITS:
        if cap_unit not in PROCESSING:
            continue
        ins = inflows(uid)
        feed = round(sum(val(s, "flow_rate") for s in ins), 1)
        F(uid, "feed_rate", feed, "kbd", as_of=AS_OF, src="KG derived", owner="ROLE-PLAN", method="calculated",
          lineage=[fid(s, "flow_rate") for s in ins])
        meter = round(feed * (1 + jitter(uid + "meter", 0.012)), 1)        # meter bias vs accounting, up to ±1.2%
        tid, mf = utag(uid, "FI", "Unit feed rate (DCS meter)", "kbd", meter)
        calc(uid, "meter_reconciliation", round(100 * (meter - feed) / feed, 2), "%", [mf, fid(uid, "feed_rate")], owner="ROLE-PLAN")
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
    F(SITE, "nelson_complexity_index", round(sum(b._by_id[x]["value"] for x in contrib), 2), "", as_of=DESIGN_DATE, src="KG derived",
      owner="ROLE-PLAN", method="calculated", lineage=contrib)
    E(SITE, "GOVERNED_BY", "EQ-NCI")

    # ------------------------------------------------------------------ hydrogen network (pure-H2 basis)
    makeup, chem_mass = [], {}
    for uid, rate in H2_CONSUMPTION.items():
        F(uid, "h2_consumption_rate", rate, "scf/bbl", as_of=DESIGN_DATE, src="Process design basis (licensor data)", owner="ROLE-PROC",
          method="declared", conf="medium")
        F(uid, "h2_makeup_efficiency", H2_EFFICIENCY[uid], "fraction", as_of=DESIGN_DATE,
          src="Hydrogen network study 2025 (purge & solution losses)", owner="ROLE-PROC", method="declared", conf="medium")
        chem = calc(uid, "h2_consumption", round(rate * val(uid, "feed_rate") / 1000, 1), "MMSCFD",
                    [fid(uid, "h2_consumption_rate"), fid(uid, "feed_rate")])
        chem_mass[uid] = calc(uid, "h2_chemical_mass", round(val(uid, "h2_consumption") * H2_T_PER_MMSCF, 1), "t/d", [chem])
        mk = calc(uid, "h2_makeup", round(val(uid, "h2_consumption") / H2_EFFICIENCY[uid], 1), "MMSCFD",
                  [chem, fid(uid, "h2_makeup_efficiency")])
        calc(uid, "h2_purge_loss", round(val(uid, "h2_makeup") - val(uid, "h2_consumption"), 1), "MMSCFD", [mk, chem])
        makeup.append(mk)
    F("CCR-1", "h2_yield", CCR_H2_YIELD, "scf/bbl", as_of=DESIGN_DATE, src="Process design basis (licensor data)", owner="ROLE-PROC",
      method="declared", conf="medium")
    ng = calc("CCR-1", "net_gas_production", round(CCR_H2_YIELD * val("CCR-1", "feed_rate") / 1000, 1), "MMSCFD",
              [fid("CCR-1", "h2_yield"), fid("CCR-1", "feed_rate")])
    ptag, pf = utag("CCR-1", "AI", "Net gas hydrogen purity", "mol%", CCR_H2_PURITY, kind="analyser")
    ccr_h2 = calc("CCR-1", "h2_production", round(val("CCR-1", "net_gas_production") * CCR_H2_PURITY / 100, 1), "MMSCFD", [ng, pf])
    h2_mass_frac = 0.92 * 2.016 / (0.92 * 2.016 + 0.08 * 22.0)
    total = round(sum(b._by_id[x]["value"] for x in makeup), 1)
    demand = calc(SITE, "h2_demand", total, "MMSCFD", makeup)
    hmu_meter = round((total - val("CCR-1", "h2_production")) * (1 + HMU_METER_BIAS), 1)
    hmu_tag, hmu_f = utag("HMU-1", "FI", "Hydrogen production (PSA product meter)", "MMSCFD", hmu_meter)
    utag("HMU-1", "AI", "PSA product hydrogen purity", "mol%", HMU_PURITY, kind="analyser")
    hmu_p = calc("HMU-1", "h2_production", hmu_meter, "MMSCFD", [hmu_f])
    F("HMU-1", "utilisation", round(100 * hmu_meter / val("HMU-1", "design_capacity"), 1), "%", as_of=AS_OF, src="KG derived",
      owner="ROLE-PLAN", method="calculated", lineage=[hmu_p, fid("HMU-1", "design_capacity")])
    F("HMU-1", "ng_specific_consumption", SMR_NG_PER_MSCF, "MMBtu/Mscf", as_of=DESIGN_DATE, src="Process design basis (licensor data)",
      owner="ROLE-PROC", method="declared", conf="medium")
    calc("HMU-1", "natural_gas_consumption", round(hmu_meter * 1000 * SMR_NG_PER_MSCF), "MMBtu/d",
         [hmu_p, fid("HMU-1", "ng_specific_consumption")], owner="ROLE-ENERGY")
    F("HMU-1", "co2_intensity", SMR_CO2_T_PER_T_H2, "t/t", as_of=DESIGN_DATE, src="Process design basis (licensor data)",
      owner="ROLE-ENV", method="declared", conf="medium")
    cap_f = calc(SITE, "h2_supply_capacity", round(val("CCR-1", "h2_production") + val("HMU-1", "design_capacity"), 1), "MMSCFD",
                 [ccr_h2, fid("HMU-1", "design_capacity")])
    calc(SITE, "h2_headroom", round(val(SITE, "h2_supply_capacity") - total, 1), "MMSCFD", [cap_f, demand])
    calc(SITE, "h2_balance_residual", round(100 * (hmu_meter + val("CCR-1", "h2_production") - total) / total, 2), "%",
         [hmu_p, ccr_h2, demand])
    for sid, name, src, dst, pred, mass in [("STR-CCR-H2", "Reformer net gas (hydrogen)", "CCR-1", "UTL-H2", ("CCR-1", "net_gas_production"),
                                             val("CCR-1", "h2_production") * H2_T_PER_MMSCF / h2_mass_frac),
                                            ("STR-HMU-H2", "SMR / PSA hydrogen", "HMU-1", "UTL-H2", ("HMU-1", "h2_production"),
                                             hmu_meter * H2_T_PER_MMSCF)] + \
                                           [(f"STR-H2-{u}", f"Make-up hydrogen to {u}", "UTL-H2", u, (u, "h2_makeup"),
                                             val(u, "h2_makeup") * H2_T_PER_MMSCF) for u in H2_CONSUMPTION]:
        N(sid, "Stream", name, "material")
        E(src, "PRODUCES", sid)
        E(sid, "FEEDS", dst)
        f1 = F(sid, "flow_rate", val(*pred), "MMSCFD", as_of=AS_OF, src="KG derived", owner="ROLE-PROC", method="calculated",
               lineage=[fid(*pred)])
        calc(sid, "mass_rate", round(mass, 1), "t/d", [f1])
    E("UTL-H2", "GOVERNED_BY", "EQ-H2BAL")

    # ------------------------------------------------------------------ unit mass closure
    loss_facts = []
    for uid in [u[0] for u in UNITS if u[5] in PROCESSING and u[0] not in ("GBL-1", "DBL-1")] + ["CDU-A", "CDU-B"]:
        ins = [s for s in inflows(uid)] if not uid.startswith("CDU") else []
        outs = [s for s in outflows(uid) if b.fact_obj(s, "mass_rate") or b.fact_obj(s, "flow_rate")["unit"] == "t/d"]
        mf = lambda s: b.fact_obj(s, "mass_rate") or b.fact_obj(s, "flow_rate")
        lin_in = [mf(s)["id"] for s in ins]
        m_in = sum(mf(s)["value"] for s in ins)
        if uid.startswith("CDU"):
            cm = calc(uid, "crude_mass_rate", round(val(uid, "throughput_fy2026") * 1000 * BBL_M3 * CRUDE_DENSITY), "t/d",
                      [fid(uid, "throughput_fy2026")], owner="ROLE-PLAN")
            lin_in, m_in = [cm], val(uid, "crude_mass_rate")
        if uid in chem_mass:
            lin_in.append(chem_mass[uid])
            m_in += b._by_id[chem_mass[uid]]["value"]
        m_out = sum(mf(s)["value"] for s in outs if not s.startswith("STR-H2") and s != "STR-CCR-H2")
        lin_out = [mf(s)["id"] for s in outs if not s.startswith("STR-H2") and s != "STR-CCR-H2"]
        if uid == "CCR-1":
            m_out += b.fact_obj("STR-CCR-H2", "mass_rate")["value"]
            lin_out.append(fid("STR-CCR-H2", "mass_rate"))
        if uid == "FCC-1":
            m_out += FCC_COKE_TD
            lin_out.append(fid("FCC-1", "coke_make"))
        calc(uid, "mass_closure", round(100 * m_out / m_in, 2), "%", lin_in + lin_out, owner="ROLE-PLAN")
        loss_facts.append(calc(uid, "mass_unaccounted", round(m_in - m_out, 1), "t/d", lin_in + lin_out, owner="ROLE-PLAN"))
        E(uid, "GOVERNED_BY", "EQ-MASS")
    unacc = round(sum(b._by_id[x]["value"] for x in loss_facts), 1)
    lf = calc(SITE, "mass_unaccounted", unacc, "t/d", loss_facts, owner="ROLE-PLAN")
    calc(SITE, "mass_unaccounted_pct_crude", round(100 * unacc / (val("CDU-A", "crude_mass_rate") + val("CDU-B", "crude_mass_rate")), 2),
         "%", [lf, fid("CDU-A", "crude_mass_rate"), fid("CDU-B", "crude_mass_rate")], owner="ROLE-PLAN")

    # ------------------------------------------------------------------ sulfur balance (stream based, measured SRU)
    grades = [("CR-AL", "CMP-A-AL"), ("CR-BM", "CMP-A-BM"), ("CR-MUR", "CMP-A-MUR")]
    s_avg = round(sum(val(g, "sulfur") * val(c, "slate_share") for g, c in grades), 3)
    F(SITE, "crude_sulfur_avg", s_avg, "wt%", as_of=AS_OF, src="KG derived", owner="ROLE-PLAN", method="calculated",
      lineage=[fid(g, "sulfur") for g, _ in grades] + [fid(c, "slate_share") for _, c in grades])
    F(SITE, "crude_density", CRUDE_DENSITY, "t/m3", as_of=AS_OF, src="Crude assay (blended slate, typical)", owner="ROLE-PLAN",
      method="indicative", conf="medium")
    cmr = calc(SITE, "crude_mass_rate", round(val("CDU-A", "crude_mass_rate") + val("CDU-B", "crude_mass_rate")), "t/d",
               [fid("CDU-A", "crude_mass_rate"), fid("CDU-B", "crude_mass_rate")], owner="ROLE-PLAN")
    s_crude = calc(SITE, "sulfur_in_crude", round(val(SITE, "crude_mass_rate") * s_avg / 100, 1), "t/d",
                   [cmr, fid(SITE, "crude_sulfur_avg")], owner="ROLE-ENV")
    F("STR-VGO-IMP", "sulfur_content", VGO_IMPORT_SULFUR, "wt%", as_of=AS_OF, src="Cargo certificate / LIMS", owner="ROLE-LAB",
      method="measured", conf="medium")
    s_vgo = calc("STR-VGO-IMP", "sulfur_flow", round(val("STR-VGO-IMP", "mass_rate") * VGO_IMPORT_SULFUR / 100, 1), "t/d",
                 [fid("STR-VGO-IMP", "mass_rate"), fid("STR-VGO-IMP", "sulfur_content")], owner="ROLE-ENV")
    s_in = calc(SITE, "sulfur_in", round(val(SITE, "sulfur_in_crude") + val("STR-VGO-IMP", "sulfur_flow"), 1), "t/d", [s_crude, s_vgo],
                owner="ROLE-ENV")
    fates = []
    for sid, wt in SULFUR_CONTENT.items():
        F(sid, "sulfur_content", wt, "wt%", as_of=AS_OF, src="LIMS / product certificates", owner="ROLE-LAB", method="measured",
          conf="medium")
        base = b.fact_obj(sid, "mass_rate") or b.fact_obj(sid, "flow_rate")
        fates.append(calc(sid, "sulfur_flow", round(base["value"] * wt / 100, 2), "t/d", [base["id"], fid(sid, "sulfur_content")],
                          owner="ROLE-ENV"))
    F("FCC-1", "coke_sulfur", FCC_COKE_SULFUR, "wt%", as_of=AS_OF, src="LIMS (spent catalyst carbon & sulfur)", owner="ROLE-LAB",
      method="measured", conf="medium")
    fates.append(calc("FCC-1", "sulfur_to_flue_gas", round(FCC_COKE_TD * FCC_COKE_SULFUR / 100, 1), "t/d",
                      [fid("FCC-1", "coke_make"), fid("FCC-1", "coke_sulfur")], owner="ROLE-ENV"))
    fates.append(F(SITE, "sulfur_emitted_other", SULFUR_EMITTED_OTHER, "t/d", as_of=AS_OF,
                   src="CEMS (fuel-gas combustion, SRU tail gas, flare)", owner="ROLE-ENV", method="measured", conf="medium"))
    sru_tag, sru_f = utag("SRU-1", "WI", "Sulfur production (pit rundown / weighbridge)", "t/d", SRU_PRODUCTION_MEASURED)
    sru_p = calc("SRU-1", "sulfur_production", SRU_PRODUCTION_MEASURED, "t/d", [sru_f], owner="ROLE-ENV")
    F("SRU-1", "claus_trains", SRU_TRAINS, "count", as_of=DESIGN_DATE, src="Process design basis", owner="ROLE-ENV", method="declared")
    F("SRU-1", "train_capacity", 400, "t/d", as_of=DESIGN_DATE, src="Process design basis", owner="ROLE-ENV", method="declared")
    F("SRU-1", "recovery_efficiency", SRU_RECOVERY, "%", as_of=DESIGN_DATE, src="Performance test 2025 (Claus + TGTU)", owner="ROLE-ENV",
      method="measured", conf="medium")
    F("SRU-1", "utilisation", round(100 * SRU_PRODUCTION_MEASURED / val("SRU-1", "design_capacity"), 1), "%", as_of=AS_OF,
      src="KG derived", owner="ROLE-PLAN", method="calculated", lineage=[sru_p, fid("SRU-1", "design_capacity")])
    out = SRU_PRODUCTION_MEASURED + sum(b._by_id[x]["value"] for x in fates)
    calc(SITE, "sulfur_unaccounted", round(val(SITE, "sulfur_in") - out, 1), "t/d", [s_in, sru_p] + fates, owner="ROLE-ENV")
    calc(SITE, "sulfur_balance_closure", round(100 * out / val(SITE, "sulfur_in"), 2), "%", [s_in, sru_p] + fates, owner="ROLE-ENV")
    calc(SITE, "sulfur_recovery_share", round(100 * SRU_PRODUCTION_MEASURED / val(SITE, "sulfur_in"), 1), "%", [sru_p, s_in],
         owner="ROLE-ENV")
    E(SITE, "GOVERNED_BY", "EQ-SBAL")
    F(SITE, "reformate_upgrade_spread", GASOLINE_UPGRADE_SPREAD, "USD/bbl", as_of=AS_OF, src="Planning assumption", owner="ROLE-PLAN",
      method="assumption", conf="low", basis="per bbl of heavy naphtha reformed")

    # ------------------------------------------------------------------ sour water and amine networks -> SRU
    sw_s = []
    for uid, m3h, h2s, nh3 in SOUR_WATER:
        sid = f"STR-{uid[-1]}-SW" if uid.startswith("CDU") else f"STR-SW-{uid}"
        if sid not in b.nodes:
            N(sid, "Stream", f"Sour water from {uid}", "material")
            E(uid, "PRODUCES", sid)
            E(sid, "FEEDS", "SWS-1")
        F(sid, "flow_rate", m3h, "m3/h", as_of=AS_OF, src="PI historian", owner="ROLE-OPS", method="measured")
        F(sid, "h2s_content", h2s, "ppmw", as_of=AS_OF, src="LIMS", owner="ROLE-LAB", method="measured", conf="medium")
        F(sid, "nh3_content", nh3, "ppmw", as_of=AS_OF, src="LIMS", owner="ROLE-LAB", method="measured", conf="medium")
        sw_s.append(calc(sid, "sulfur_flow", round(m3h * 24 * h2s / 1e6 * 32 / 34, 2), "t/d",
                         [fid(sid, "flow_rate"), fid(sid, "h2s_content")], owner="ROLE-ENV"))
    sws_in = [s for s in inflows("SWS-1", "m3/h")]
    swf = F("SWS-1", "feed_rate", sum(val(s, "flow_rate") for s in sws_in), "m3/h", as_of=AS_OF, src="KG derived", owner="ROLE-PLAN",
            method="calculated", lineage=[fid(s, "flow_rate") for s in sws_in])
    F("SWS-1", "utilisation", round(100 * val("SWS-1", "feed_rate") / val("SWS-1", "design_capacity"), 1), "%", as_of=AS_OF,
      src="KG derived", owner="ROLE-PLAN", method="calculated", lineage=[swf, fid("SWS-1", "design_capacity")])
    ra_in = []
    for uid, m3h, load in RICH_AMINE:
        sid = f"STR-RA-{uid}"
        N(sid, "Stream", f"Rich amine from {uid}", "material")
        E(uid, "PRODUCES", sid)
        E(sid, "FEEDS", "ARU-1")
        F(sid, "flow_rate", m3h, "m3/h", as_of=AS_OF, src="PI historian", owner="ROLE-OPS", method="measured")
        F(sid, "rich_loading", load, "mol/mol", as_of=AS_OF, src="LIMS", owner="ROLE-LAB", method="measured", conf="medium")
        ra_in.append(fid(sid, "flow_rate"))
    raf = F("ARU-1", "feed_rate", sum(r[1] for r in RICH_AMINE), "m3/h", as_of=AS_OF, src="KG derived", owner="ROLE-PLAN",
            method="calculated", lineage=ra_in)
    F("ARU-1", "utilisation", round(100 * val("ARU-1", "feed_rate") / val("ARU-1", "design_capacity"), 1), "%", as_of=AS_OF,
      src="KG derived", owner="ROLE-PLAN", method="calculated", lineage=[raf, fid("ARU-1", "design_capacity")])
    for sid, name, src, dst in [("STR-ARU-AG", "Amine acid gas (as S)", "ARU-1", "SRU-1"),
                                ("STR-SWS-AG", "Sour water stripper gas (as S)", "SWS-1", "SRU-1"),
                                ("STR-SRU-S", "Liquid sulfur", "SRU-1", "MT-1")]:
        N(sid, "Stream", name, "material")
        E(src, "PRODUCES", sid)
        E(sid, "FEEDS", dst)
    F("STR-ARU-AG", "flow_rate", ARU_ACID_GAS_S_MEASURED, "t/d", as_of=AS_OF, src="PI historian (acid-gas flow x H2S analyser)",
      owner="ROLE-ENV", method="measured", conf="medium")
    swag = calc("STR-SWS-AG", "flow_rate", round(sum(b._by_id[x]["value"] for x in sw_s), 1), "t/d", sw_s, owner="ROLE-ENV")
    calc("SWS-1", "ammonia_to_sru", round(sum(m * 24 * n / 1e6 for _, m, _, n in SOUR_WATER), 1), "t/d",
         [fid(f"STR-{u[-1]}-SW" if u.startswith("CDU") else f"STR-SW-{u}", "nh3_content") for u, *_ in SOUR_WATER], owner="ROLE-ENV")
    feed_s = calc("SRU-1", "sulfur_feed", round(ARU_ACID_GAS_S_MEASURED + val("STR-SWS-AG", "flow_rate"), 1), "t/d",
                  [fid("STR-ARU-AG", "flow_rate"), swag], owner="ROLE-ENV")
    exp_p = calc("SRU-1", "expected_production", round(val("SRU-1", "sulfur_feed") * SRU_RECOVERY / 100, 1), "t/d",
                 [feed_s, fid("SRU-1", "recovery_efficiency")], owner="ROLE-ENV")
    calc("SRU-1", "production_reconciliation", round(100 * (SRU_PRODUCTION_MEASURED - val("SRU-1", "expected_production")) /
                                                     val("SRU-1", "expected_production"), 2), "%", [sru_p, exp_p], owner="ROLE-ENV")
    calc("STR-SRU-S", "flow_rate", SRU_PRODUCTION_MEASURED, "t/d", [sru_p], owner="ROLE-ENV")

    # ------------------------------------------------------------------ utilities: fuel gas, steam, power, cooling water
    fired = {}
    for tr, t in TRAINS.items():
        fired[f"CDU-{tr}"] = [fid(f"CDU-{tr}", "heater_fired_duty")]
    tagv = lambda eq, text: next(n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint"
                                 and n["props"].get("equipment") == eq and text in n["name"])
    for h, uid in [("H-301", "FCC-1"), ("H-401", "HCU-1"), ("H-501", "DCU-1"), ("H-502", "DCU-1")]:
        a, e_ = tagv(h, "Absorbed duty"), tagv(h, "Thermal efficiency")
        fd = calc(h, "fired_duty", round(val(a, "latest_value") / (val(e_, "latest_value") / 100), 1), "MW",
                  [fid(a, "latest_value"), fid(e_, "latest_value")], owner="ROLE-ENERGY")
        fired.setdefault(uid, []).append(fd)
    for uid, mw in FIRED_DUTY.items():
        fired.setdefault(uid, []).append(F(uid, "fired_duty", mw, "MW", as_of=AS_OF, src="PI historian (fuel-gas meters x LHV)",
                                           owner="ROLE-ENERGY", method="measured", conf="medium"))
    F("UTL-FG", "fuel_gas_lhv", FUEL_GAS_LHV, "GJ/t", as_of=AS_OF, src="Fuel-gas analyser (calorimeter)", owner="ROLE-ENERGY",
      method="measured", conf="medium")
    cons = []
    for uid, lin in fired.items():
        mw = sum(b._by_id[x]["value"] for x in lin)
        sid = f"STR-FG-{uid}"
        N(sid, "Stream", f"Fuel gas to {uid}", "material")
        E("UTL-FG", "PRODUCES", sid)
        E(sid, "FEEDS", uid)
        cons.append(calc(sid, "flow_rate", round(mw * 86.4 / FUEL_GAS_LHV, 1), "t/d", lin + [fid("UTL-FG", "fuel_gas_lhv")],
                         owner="ROLE-ENERGY"))
    for sid, name, dst, v in [("STR-FG-HMU-1", "Fuel gas to SMR furnace", "HMU-1", HMU_FUEL_GAS_TD),
                              ("STR-FG-FLARE", "Normal flaring", "UTL-FLR", FLARE_NORMAL_TD)]:
        N(sid, "Stream", name, "material")
        E("UTL-FG", "PRODUCES", sid)
        E(sid, "FEEDS", dst)
        cons.append(F(sid, "flow_rate", v, "t/d", as_of=AS_OF, src="PI historian", owner="ROLE-ENERGY", method="measured", conf="medium"))
    N("STR-NG-FG", "Stream", "Natural gas make-up to fuel gas", "material")
    E("UTL-NG", "PRODUCES", "STR-NG-FG"); E("STR-NG-FG", "FEEDS", "UTL-FG")
    ngf = F("STR-NG-FG", "flow_rate", NG_TO_FG_MEASURED, "t/d", as_of=AS_OF, src="Custody-transfer meter", owner="ROLE-ENERGY",
            method="measured")
    prod = [fid(s, "flow_rate") for s in inflows("UTL-FG", "t/d") if s != "STR-NG-FG"]
    h2s_rm = calc("UTL-FG", "h2s_removed", round(ARU_ACID_GAS_S_MEASURED * 34 / 32, 1), "t/d", [fid("STR-ARU-AG", "flow_rate")],
                  owner="ROLE-ENERGY")
    supply = sum(b._by_id[x]["value"] for x in prod) + NG_TO_FG_MEASURED - val("UTL-FG", "h2s_removed")
    demand_fg = sum(b._by_id[x]["value"] for x in cons)
    calc("UTL-FG", "balance_residual", round(100 * (supply - demand_fg) / demand_fg, 2), "%", prod + [ngf, h2s_rm] + cons,
         owner="ROLE-ENERGY")
    calc("UTL-FG", "utilisation", round(100 * demand_fg / val("UTL-FG", "design_capacity"), 1), "%",
         cons + [fid("UTL-FG", "design_capacity")], owner="ROLE-ENERGY")
    # steam
    sp, sc = [], []
    for uid, th in STEAM_PRODUCERS.items():
        sp.append(F(uid, "steam_production", th, "t/h", as_of=AS_OF, src="PI historian (steam meters)", owner="ROLE-ENERGY",
                    method="measured", conf="medium"))
    for uid, th in STEAM_CONSUMERS.items():
        if th < 0:
            sp.append(F(uid, "steam_production", -th, "t/h", as_of=AS_OF, src="PI historian (steam meters)", owner="ROLE-ENERGY",
                        method="measured", conf="medium"))
        else:
            sc.append(F(uid, "steam_consumption", th, "t/h", as_of=AS_OF, src="PI historian (steam meters)", owner="ROLE-ENERGY",
                        method="measured", conf="medium"))
    sl = F("UTL-STM", "steam_losses", STEAM_LOSSES_DECLARED, "t/h", as_of=DESIGN_DATE, src="Steam-trap survey 2025",
           owner="ROLE-ENERGY", method="declared", conf="low")
    ps, cs = sum(b._by_id[x]["value"] for x in sp), sum(b._by_id[x]["value"] for x in sc) + STEAM_LOSSES_DECLARED
    calc("UTL-STM", "steam_balance_residual", round(100 * (ps - cs) / cs, 2), "%", sp + sc + [sl], owner="ROLE-ENERGY")
    # power: motor loads from the equipment register (running motors x 75% load) + base loads, against generation + import
    motors = {}
    for n in b.nodes.values():
        if n["props"].get("eq_class") == "Electric motor" and n["props"].get("running"):
            motors.setdefault(n["props"]["plant_unit"], []).append(fid(n["id"], "rated_power"))
    loads = []
    for uid, lin in motors.items():
        loads.append(calc(uid, "power_demand", round(sum(b._by_id[x]["value"] for x in lin) * 0.75 / 1000, 1), "MW", lin,
                          owner="ROLE-ELEC"))
    for uid, mw in POWER_BASE_LOADS.items():
        loads.append(F(uid, "power_demand", mw, "MW", as_of=AS_OF, src="Substation meters", owner="ROLE-ELEC", method="measured",
                       conf="medium"))
    gens = [F(uid, "power_generation", mw, "MW", as_of=AS_OF, src="Substation meters", owner="ROLE-ELEC", method="measured")
            for uid, mw in POWER_SOURCES.items()]
    gi = F("UTL-PWR", "grid_import", GRID_IMPORT_MEASURED, "MW", as_of=AS_OF, src="Utility revenue meter", owner="ROLE-ELEC",
           method="measured")
    tot_load = sum(b._by_id[x]["value"] for x in loads)
    tot_gen = sum(b._by_id[x]["value"] for x in gens) + GRID_IMPORT_MEASURED
    calc("UTL-PWR", "site_power_demand", round(tot_load, 1), "MW", loads, owner="ROLE-ELEC")
    calc("UTL-PWR", "power_balance_residual", round(100 * (tot_gen - tot_load) / tot_load, 2), "%", gens + [gi] + loads,
         owner="ROLE-ELEC")
    cw = [F(uid if uid != "other" else "UTL-CW", "cooling_water_use" if uid != "other" else "cooling_water_use_other", m3, "m3/h",
            as_of=AS_OF, src="Design heat & material balance (CW users)", owner="ROLE-ENERGY", method="declared", conf="medium")
          for uid, m3 in CW_USE.items()]
    calc("UTL-CW", "utilisation", round(100 * sum(CW_USE.values()) / val("UTL-CW", "design_capacity"), 1), "%",
         cw + [fid("UTL-CW", "design_capacity")], owner="ROLE-ENERGY")

    # ------------------------------------------------------------------ conversion-unit and process KPIs
    lv = lambda t: fid(t, "latest_value")
    feed = val("FCC-1", "feed_rate")
    calc("FCC-1", "conversion", round(100 * (1 - (val("STR-FCC-LCO", "flow_rate") + val("STR-FCC-SLURRY", "flow_rate")) / feed), 1),
         "vol%", [fid("STR-FCC-LCO", "flow_rate"), fid("STR-FCC-SLURRY", "flow_rate"), fid("FCC-1", "feed_rate")], owner="ROLE-CONV")
    for k, eq, text, unit in [("riser_outlet_temperature", "R-301", "(ROT)", "degC"), ("catalyst_loss", "R-302", "Catalyst losses", "t/d"),
                              ("regenerator_afterburn", "R-302", "Afterburn", "degC"), ("cat_to_oil", "R-301", "Catalyst-to-oil", "wt/wt")]:
        t = tagv(eq, text)
        calc("FCC-1", k, val(t, "latest_value"), unit, [lv(t)], owner="ROLE-CONV")
    fm = b.fact_obj("STR-VGOHT-FCC", "mass_rate")
    cy = calc("FCC-1", "coke_yield", round(100 * FCC_COKE_TD / fm["value"], 2), "wt%", [fid("FCC-1", "coke_make"), fm["id"]],
              owner="ROLE-CONV")
    calc("FCC-1", "delta_coke", round(val("FCC-1", "coke_yield") / val("FCC-1", "cat_to_oil"), 2), "wt%",
         [cy, fid("FCC-1", "cat_to_oil")], owner="ROLE-CONV")
    for k, v, u, src in [("ecat_mat_activity", 70.5, "wt%", "LIMS (equilibrium catalyst, weekly)"), ("ecat_nickel", 1850, "ppmw", "LIMS (equilibrium catalyst, weekly)"),
                         ("ecat_vanadium", 2600, "ppmw", "LIMS (equilibrium catalyst, weekly)"), ("fresh_catalyst_rate", 8.2, "t/d", "Catalyst loader log")]:
        F("FCC-1", k, v, u, as_of=AS_OF, src=src, owner="ROLE-CONV", method="measured", conf="medium")
    feed = val("HCU-1", "feed_rate")
    calc("HCU-1", "conversion", round(100 * (1 - val("STR-HCU-UCO", "flow_rate") / feed), 1), "vol%",
         [fid("STR-HCU-UCO", "flow_rate"), fid("HCU-1", "feed_rate")], owner="ROLE-CONV")
    for k, eq, text, unit in [("wabt_first_stage", "R-401", "Weighted average bed", "degC"), ("wabt_cracking", "R-402", "Weighted average bed", "degC"),
                              ("h2_partial_pressure", "R-401", "hydrogen partial pressure", "bara"),
                              ("recycle_gas_purity", "R-401", "Recycle gas hydrogen purity", "mol%"), ("reac_kp", "PC-401", "REAC Kp", "fraction")]:
        t = tagv(eq, text)
        calc("HCU-1", k, val(t, "latest_value"), unit, [lv(t)], owner="ROLE-CONV")
    for k, v, u, src in [("days_on_stream", 420, "days", "Operations logbook"), ("nitrogen_slip", 8.0, "ppmw", "LIMS"),
                         ("eor_wabt", 425, "degC", "Licensor catalyst cycle guarantee")]:
        F("HCU-1", k, v, u, as_of=AS_OF, src=src, owner="ROLE-CONV", method="measured" if src == "LIMS" else "declared", conf="medium")
    coke_feed_t = b.fact_obj("STR-VDU-VR-DCU", "mass_rate")
    calc("DCU-1", "coke_yield", round(100 * val("STR-DCU-COKE", "flow_rate") / coke_feed_t["value"], 1), "wt%",
         [fid("STR-DCU-COKE", "flow_rate"), coke_feed_t["id"]], owner="ROLE-CONV")
    cyc = [tagv(d, "Cycle time") for d in ("D-501A", "D-501B", "D-502A", "D-502B")]
    calc("DCU-1", "drum_cycle_time", round(sum(val(t, "latest_value") for t in cyc) / 4, 1), "h", [lv(t) for t in cyc], owner="ROLE-CONV")
    for k, v, u, src in [("recycle_ratio", 1.08, "fraction", "Operations logbook"), ("feed_ccr", 22.5, "wt%", "LIMS"),
                         ("velocity_steam", 1.2, "t/h", "PI historian")]:
        F("DCU-1", k, v, u, as_of=AS_OF, src=src, owner="ROLE-CONV", method="measured", conf="medium")
    for uid, k, v, u, src in [("CCR-1", "reformate_ronc", 101.0, "RON", "LIMS"), ("CCR-1", "spent_catalyst_coke", 4.8, "wt%", "LIMS"),
                              ("CCR-1", "catalyst_circulation", 1000, "kg/h", "PI historian"), ("VDU-1", "hvgo_ccr", 0.6, "wt%", "LIMS"),
                              ("VDU-1", "hvgo_ni_v", 2.5, "ppmw", "LIMS"), ("VDU-1", "overflash", 3.0, "vol%", "Operations logbook")]:
        F(uid, k, v, u, as_of=AS_OF, src=src, owner="ROLE-PROC", method="measured", conf="medium")
    calc("CCR-1", "c5_plus_yield", round(100 * (val("STR-CCR-REF-ARO", "flow_rate") + val("STR-CCR-REF-GBL", "flow_rate")) /
                                         val("CCR-1", "feed_rate"), 1), "vol%",
         [fid("STR-CCR-REF-ARO", "flow_rate"), fid("STR-CCR-REF-GBL", "flow_rate"), fid("CCR-1", "feed_rate")])

    _groupings(b)
    _process_chains(b)
    _applications(b)
    _events(b, tagv)


# ============================================================================ groupings
def _groupings(b):
    N, E = b.node, b.edge

    def grp(gid, cls, name, owner, members):
        N(gid, cls, name, "grouping")
        E(gid, "OWNED_BY", owner)
        for m in members:
            E(m, "MEMBER_OF", gid)
    grp("CL-FCC-OVH", "CorrosionLoop", "Corrosion loop: FCC main fractionator overhead", "ROLE-CORR",
        ["PC-302", "E-310A", "E-310B", "E-311", "V-301", "P-305A", "P-305B", "P-307A", "P-307B", "C-301"])
    grp("CL-FCC-GCU", "CorrosionLoop", "Corrosion loop: FCC wet gas & gas concentration (wet H2S, carbonate)", "ROLE-CORR",
        ["V-302", "V-303", "C-302", "C-303", "C-304", "E-312", "E-313", "P-306A", "P-306B"])
    grp("CL-FCC-CAT", "CorrosionLoop", "Corrosion loop: FCC catalyst circuit (erosion)", "ROLE-CORR",
        ["R-301", "R-302", "SV-301", "SV-302", "EX-301", "PC-301"])
    grp("CL-HCU-REAC", "CorrosionLoop", "Corrosion loop: HCU reactor effluent air coolers (NH4HS)", "ROLE-CORR",
        ["PC-401", "E-410A", "E-410B", "E-410C", "E-410D", "V-402", "V-403", "X-401"])
    grp("CL-HCU-HTHA", "CorrosionLoop", "Corrosion loop: HCU high-temperature hydrogen service", "ROLE-CORR",
        ["H-401", "R-401", "R-402", "E-401", "E-402", "V-401", "PC-402"])
    grp("CL-DCU-HOT", "CorrosionLoop", "Corrosion loop: coker heaters, drums & transfer lines", "ROLE-CORR",
        ["H-501", "H-502", "PC-501", "D-501A", "D-501B", "D-502A", "D-502B", "PC-502", "P-501A", "P-501B"])
    grp("CL-DCU-OVH", "CorrosionLoop", "Corrosion loop: coker fractionator overhead", "ROLE-CORR",
        ["V-501", "E-510A", "E-510B", "P-505A", "P-505B", "C-501"])
    tags = lambda eqs, pred: [n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint" and n["props"].get("equipment") in eqs
                              and pred(n["name"])]
    grp("SIF-FCC-SV", "SafetyInstrumentedFunction", "SIF: slide-valve low differential pressure (reversal protection)", "ROLE-INST",
        ["SV-301", "SV-302"] + tags(("SV-301", "SV-302"), lambda s: "pressure drop" in s))
    grp("SIF-HCU-DEP", "SafetyInstrumentedFunction", "SIF: HCU emergency depressuring on reactor temperature runaway", "ROLE-INST",
        ["R-401", "R-402"] + tags(("R-401", "R-402"), lambda s: "outlet temperature" in s))
    grp("SIF-DCU-HTR", "SafetyInstrumentedFunction", "SIF: coker heater low pass-flow trip", "ROLE-INST",
        ["H-501", "H-502"] + tags(("H-501", "H-502"), lambda s: "Pass" in s and "flow" in s))
    for u, name in [("FCC-1", "FCC"), ("HCU-1", "hydrocracker"), ("DCU-1", "delayed coker")]:
        grp(f"CC-{u[:3]}", "CostCentre", f"Cost centre: {name}", "ROLE-MAINT", [u])
    grp("NET-H2", "Grouping", "Network: hydrogen (producers, header, consumers)", "ROLE-PROC",
        ["HMU-1", "CCR-1", "UTL-H2"] + list(H2_CONSUMPTION))
    grp("NET-SULFUR", "Grouping", "Network: sulfur (sour water, amine, SRU)", "ROLE-ENV", ["ARU-1", "SWS-1", "SRU-1"])
    grp("NET-FG", "Grouping", "Network: fuel gas (producers, header, consumers)", "ROLE-ENERGY",
        sorted({e["source"] for e in b.edges if e["rel"] == "PRODUCES" and e["target"].startswith("STR-GAS-")}) + ["UTL-FG", "UTL-NG"])
    grp("GRP-GASOLINE", "Grouping", "Gasoline pool contributors", "ROLE-PLAN",
        sorted({s for sid, _, s, d, *_ in STREAMS if d == "GBL-1"}))


# ============================================================================ process spine
def _process_chains(b):
    N, E = b.node, b.edge

    def p(pid, cls, name, level, parent, owner=None, **props):
        N(pid, cls, name, "process", level, parent, **props)
        if owner:
            E(pid, "OWNED_BY", owner)
    for gid, gn, vs, owner in [("PG-PLAN", "Planning & Scheduling", "VS-C2P", "ROLE-PLAN"),
                               ("PG-NET", "Hydrogen, Sulfur & Utility Networks", "VS-C2P", "ROLE-PROC"),
                               ("PG-CONV", "Conversion Unit Operations", "VS-C2P", "ROLE-CONV")]:
        p(gid, "ProcessGroup", gn, 3, vs, owner)
    tags = [n for n in b.nodes.values() if n["cls"] == "DataPoint"]
    where = lambda pred: [n["id"] for n in tags if pred(n)]
    on = lambda eqs, text: where(lambda n: n["props"].get("equipment") in eqs and text in n["name"])
    liquid_units = [u[0] for u in UNITS if u[5] in PROCESSING]
    drums = ["D-501A", "D-501B", "D-502A", "D-502B"]
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
                  ("DE-SHADOW", "LP constraint shadow prices", "economics", [], "shadow_price")]),
        dict(proc=("P-H2", "Hydrogen network management", "PG-NET", "ROLE-PROC", ["HMU-1", "CCR-1", "UTL-H2"]),
             steps=[("SP-H2", "Hydrogen balance"), ("ACT-H2", "Balance producers and consumers"),
                    ("TSK-H2", "Review HMU load, reformer hydrogen, purge losses and consumer demand"),
                    ("DEC-H2", "Set HMU rate and consumer priority"), ("DOB-H2BAL", "Daily hydrogen balance sheet")],
             governs=["HMU-1", "UTL-H2"],
             des=[("DE-H2PROD", "SMR hydrogen production", "hydrogen", on(["HMU-1"], "Hydrogen production"), None),
                  ("DE-H2CONS", "Hydrogen make-up by unit", "hydrogen", [], "h2_makeup"),
                  ("DE-H2MUC", "Make-up compressor discharge", "hydrogen", on(["K-402A", "K-402B"], "Stage 3 discharge pressure"), None)]),
        dict(proc=("P-SULF", "Sulfur management & emissions", "PG-NET", "ROLE-ENV", ["ARU-1", "SWS-1", "SRU-1"]),
             steps=[("SP-SULF", "Sulfur balance & SO2 compliance"), ("ACT-SULF", "Track sulfur in and out"),
                    ("TSK-SULF", "Review SRU load, acid-gas routing, sour water and stack SO2"),
                    ("DEC-SULF", "Limit crude sulfur or shed acid gas"), ("DOB-SBAL", "Monthly sulfur balance & emissions report")],
             governs=["SRU-1"],
             des=[("DE-SPROD", "Sulfur production", "sulfur", on(["SRU-1"], "Sulfur production"), None),
                  ("DE-SO2", "Stack SO2", "environment", on(["B-301"], "Stack SO2"), None),
                  ("DE-SUNACC", "Sulfur unaccounted", "environment", [], "sulfur_unaccounted")]),
        dict(proc=("P-FCC", "FCC operation & catalyst management", "PG-CONV", "ROLE-CONV", ["FCC-1"]),
             steps=[("SP-FCC", "Reactor-regenerator optimisation"), ("ACT-FCC", "Tune ROT, cat/oil and catalyst additions"),
                    ("TSK-FCC", "Review ROT, regenerator temperatures, e-cat and catalyst losses"),
                    ("DEC-FCC", "Set ROT and fresh catalyst rate"), ("DOB-FCCLOG", "FCC daily performance report")],
             governs=["R-301", "R-302"],
             des=[("DE-ROT", "Riser outlet temperature", "operations", on(["R-301"], "(ROT)"), None),
                  ("DE-CATLOSS", "Catalyst losses", "reliability", on(["R-302"], "Catalyst losses"), None),
                  ("DE-AFTERBURN", "Regenerator afterburn", "integrity", on(["R-302"], "Afterburn"), None)]),
        dict(proc=("P-HCU", "Hydrocracker operation & catalyst cycle", "PG-CONV", "ROLE-CONV", ["HCU-1"]),
             steps=[("SP-HCU", "Conversion & catalyst-cycle management"), ("ACT-HCU", "Adjust WABT and quench"),
                    ("TSK-HCU", "Review WABT, reactor dP, REAC Kp and wash water, H2 partial pressure"),
                    ("DEC-HCU", "Set reactor temperatures and wash-water rate"), ("DOB-HCULOG", "HCU catalyst-cycle log")],
             governs=["R-401", "R-402", "E-410A", "E-410B", "E-410C", "E-410D"],
             des=[("DE-WABT", "Weighted average bed temperature", "operations", on(["R-401", "R-402"], "Weighted average bed"), None),
                  ("DE-RXDP", "Reactor pressure drop", "operations", on(["R-401", "R-402"], "Reactor pressure drop"), None),
                  ("DE-WASHW", "REAC wash-water rate", "integrity", on(["X-401"], "Injection rate"), None),
                  ("DE-KP", "REAC Kp", "integrity", on(["PC-401"], "REAC Kp"), None)]),
        dict(proc=("P-DCU", "Coker cycle & heater run-length management", "PG-CONV", "ROLE-CONV", ["DCU-1"]),
             steps=[("SP-DCU", "Drum cycle & heater management"), ("ACT-DCU", "Plan drum switches, quench and heater spalling"),
                    ("TSK-DCU", "Review cycle times, quench rates, heater TMT and drum cycle counts"),
                    ("DEC-DCU", "Set cycle time, quench profile and spalling schedule"), ("DOB-DCULOG", "Coker drum-cycle log")],
             governs=["H-501", "H-502"] + drums,
             des=[("DE-CYCLE", "Drum cycle time", "operations", on(drums, "Cycle time"), None),
                  ("DE-CKTMT", "Coker heater TMT", "integrity", on(["H-501", "H-502"], "(TMT)"), None),
                  ("DE-QUENCH", "Coke drum quench rate", "integrity", on(drums, "Quench water rate"), None),
                  ("DE-DRUMCYC", "Cumulative drum cycles", "integrity", on(drums, "Cumulative"), None)]),
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
    L = ev.iow_limit
    for h, std, crit in [("H-301", 520, 560), ("H-401", 560, 600), ("H-501", 650, 680), ("H-502", 650, 680)]:
        for pz in range(1, 5):
            t = tagid(h, f"Pass {pz} tube-metal")
            L(b, t, "standard", "high", std, "degC"); L(b, t, "critical", "high", crit, "degC")
    for r, beds in (("R-401", 3), ("R-402", 4)):
        for i in range(1, beds + 1):
            L(b, tagid(r, f"Bed {i} outlet temperature"), "critical", "high", 425, "degC", "ROLE-CONV")
        L(b, tagid(r, "Shell skin temperature"), "critical", "high", 425, "degC")
        L(b, tagid(r, "Shell skin temperature"), "critical", "low", 93, "degC")          # minimum pressurisation temperature
        L(b, tagid(r, "hydrogen partial pressure"), "informational", "high", 160, "bara")
    L(b, tagid("R-302", "Dilute-phase temperature"), "standard", "high", 740, "degC", "ROLE-CONV")
    L(b, tagid("X-401", "Injection rate"), "critical", "low", 22000, "L/h")
    L(b, tagid("PC-401", "REAC Kp"), "standard", "high", 0.5, "fraction")
    L(b, tagid("PC-401", "REAC tube velocity"), "standard", "low", 3.0, "m/s")
    L(b, tagid("PC-401", "REAC tube velocity"), "standard", "high", 6.0, "m/s")
    L(b, tagid("PC-401", "Cold separator water NH4HS"), "standard", "high", 8.0, "wt%")
    for pc in ("PC-301", "PC-302", "PC-401", "PC-402", "PC-501", "PC-502"):
        L(b, tagid(pc, "Corrosion probe"), "standard", "high", 0.25, "mm/y")
    L(b, tagid("V-301", "chloride"), "standard", "high", 20, "ppm")
    L(b, tagid("V-301", "Boot water pH"), "standard", "high", 9.0, "pH")
    L(b, tagid("V-301", "cyanide"), "standard", "high", 20, "ppm")
    L(b, tagid("V-501", "Boot water pH"), "standard", "high", 9.0, "pH")
    L(b, tagid("PC-302", "dew-point margin"), "critical", "low", 14, "degC")
    for d in ("D-501A", "D-501B", "D-502A", "D-502B"):
        L(b, tagid(d, "Quench water rate"), "critical", "high", 120, "m3/h", "ROLE-CONV")

    X = ev.exceedance
    X(b, "IOW-D01", tagid("H-502", "Pass 3 tube-metal"), "2026-06-10", 663, 3, "degC")
    X(b, "IOW-D02", tagid("H-502", "Pass 3 tube-metal"), "2026-09-02", 671, 5, "degC")
    X(b, "IOW-D03", tagid("D-501B", "Quench water rate"), "2026-03-28", 148, 0.1, "m3/h", "ROLE-CONV")
    X(b, "IOW-D04", tagid("D-501B", "Quench water rate"), "2026-04-22", 141, 0.1, "m3/h", "ROLE-CONV")
    X(b, "IOW-H01", tagid("R-402", "Bed 4 outlet temperature"), "2026-07-09", 431, 0.2, "degC", "ROLE-CONV")
    X(b, "IOW-F01", tagid("R-302", "Dilute-phase temperature"), "2026-08-05", 752, 4, "degC", "ROLE-CONV")
    X(b, "IOW-H02", tagid("X-401", "Injection rate"), "2026-02-20", 17500, 9, "L/h")

    FL = ev.failure
    FL(b, "FL-H01", "E-410C-TUBES", "2026-03-18", "ELP", "2.2", "3.1", "5", "ammonium bisulfide corrosion after low wash-water period",
       520000, "WO-H01", severity="Critical", downtime_h=144, ttr_h=96, man_hours=820, rate_cut=40, days=6,
       desc="REAC tube leak; bundle plugged, unit at reduced rate")
    FL(b, "FL-H02", "K-401-SEALS_C", "2026-07-09", "UST", "5.2", "3.3", "5", "dry gas seal contaminated (seal-gas filter overdue)",
       180000, "WO-H02", severity="Critical", downtime_h=48, ttr_h=36, man_hours=160, rate_cut=89.6, days=2,
       desc="Recycle compressor trip on high primary vent flow; unit depressured and restarted")
    E("IOW-H01", "CAUSED_BY", "FL-H02")
    FL(b, "FL-D01", "D-501B-SHELL", "2026-05-20", "STD", "2.6", "3.1", "3", "shell bulging at course 3/4 weld (fast quench cycles)",
       1100000, "WO-D01", severity="Degraded", downtime_h=288, ttr_h=260, man_hours=3400, rate_cut=42, days=12,
       desc="Laser scan found bulge; weld overlay repair; one drum pair out")
    FL(b, "FL-F01", "R-302-DIPLEG2", "2026-08-02", "PDE", "2.3", "3.4", "4", "secondary cyclone dipleg erosion", 210000, "WO-F01",
       severity="Degraded", ttr_h=0, man_hours=40, work_type="Operational mitigation — increased fresh catalyst addition",
       desc="Catalyst losses above 3 t/d; repair deferred to the 2027 turnaround")
    F("FL-F01", "repair_status", "Deferred to TA-2027", "", as_of="2026-08-02", src="CMMS", ref="WO-F01", owner="ROLE-MAINT")
    for wo, iid, d, what, cost in [("WO-H03", "IOW-H02", "2026-02-21", "Wash-water pump P-402B restored; injection rate raised", 12000),
                                   ("WO-D03", "IOW-D03", "2026-03-29", "Quench profile reviewed; ramp-rate interlock tuned", 8000),
                                   ("WO-D02", "IOW-D02", "2026-09-03", "Online spalling of H-502", 85000)]:
        N(wo, "WorkOrder", f"{wo} IOW response: {what}", "event", date=d)
        E(wo, "RESPONDS_TO", iid)
        F(wo, "actual_cost", cost, "USD", as_of=d, src="CMMS", ref=wo, owner="ROLE-MAINT")
        F(wo, "work_type", "IOW response", "", as_of=d, src="CMMS", ref=wo, owner="ROLE-MAINT")
    E("WO-D02", "PERFORMED_ON", "H-502")
