"""
Economics, products and planning layer for Refinery Gamma (v0.5), called from cdu_gamma.build().

- Products and markets; component streams COMPONENT_OF products; specifications; component blend properties;
  measured product quality; pool calculations and giveaway (with value, basis and range)
- Price sets (actual FY2026, plan FY2027, stress) as PriceSeries nodes. ALL PRICES ARE SYNTHETIC AND ILLUSTRATIVE,
  not market data (handbook D3: no licensed price content in the repository)
- Crude assays with cut yields, metals and nitrogen; assay-predicted CDU yields vs actual; gross product worth
  and margin by grade
- LP backbone: model, submodels per unit with plan rates and marginal values, constraints with shadow prices
- Gross-margin model reconciled to the recorded GRM; variable opex; energy, CO2 and carbon cost
- Maintenance and energy cost by cost centre; catalyst economics
- Lost margin for every failure, from the marginal value of the unit that lost throughput (council IN-W5)
"""
from .cdu_gamma import AS_OF, DESIGN_DATE, SITE, TRAINS, _tag
from .refinery_units import BBL_M3, FIRED_DUTY, GRID_IMPORT_MEASURED, NG_TO_FG_MEASURED

SYN = "Synthetic price set (illustrative, not market data)"
LP = "LP model FY2027 plan run (synthetic)"
SKELETON_TAGS = 8

PRODUCTS = [  # id, name, unit of price, export streams, market
    ("PRD-GASOLINE", "Gasoline (RON 92 grade)", "USD/bbl", ["STR-GBL-GASO"], "MKT-DOMESTIC"),
    ("PRD-JET", "Jet fuel", "USD/bbl", ["STR-DBL-JET"], "MKT-EXPORT"),
    ("PRD-ULSD", "Diesel (ULSD, 10 ppm)", "USD/bbl", ["STR-DBL-ULSD"], "MKT-DOMESTIC"),
    ("PRD-LPG", "LPG", "USD/bbl", ["STR-LPG-PROD"], "MKT-DOMESTIC"),
    ("PRD-NAPHTHA", "Naphtha (petrochemical feed)", "USD/bbl", ["STR-NHT-HN-BYP", "STR-ARO-RAF"], "MKT-EXPORT"),
    ("PRD-BTX", "BTX aromatics", "USD/bbl", ["STR-ARO-BTX"], "MKT-EXPORT"),
    ("PRD-BASEOIL", "Lube base oils", "USD/bbl", ["STR-LUBE-BO"], "MKT-EXPORT"),
    ("PRD-ASPHALT", "Asphalt", "USD/bbl", ["STR-ASPH-PROD"], "MKT-DOMESTIC"),
    ("PRD-FUELOIL", "Fuel oil (high sulfur)", "USD/bbl", ["STR-TF3-FO"], "MKT-EXPORT"),
    ("PRD-COKE", "Petroleum coke (fuel grade)", "USD/t", ["STR-DCU-COKE"], "MKT-EXPORT"),
    ("PRD-SULFUR", "Sulfur", "USD/t", ["STR-SRU-S"], "MKT-EXPORT"),
]
INPUTS = [("MAT-VGO", "Imported vacuum gas oil", "USD/bbl"), ("MAT-MEOH", "Methanol", "USD/t"),
          ("MAT-NG", "Natural gas", "USD/MMBtu"), ("MAT-POWER", "Grid electricity", "USD/MWh"),
          ("MAT-CO2", "CO2 allowance", "USD/tCO2")]
PRICES = {  # material: (actual FY2026, plan FY2027, stress)
    "CR-AL": (80.5, 78.0, 78.0), "CR-BM": (78.0, 75.5, 75.5), "CR-MUR": (83.0, 80.5, 80.5), "MAT-VGO": (81.0, 79.0, 79.0),
    "MAT-MEOH": (360, 340, 340), "MAT-NG": (6.0, 5.5, 5.5), "MAT-POWER": (90, 85, 85), "MAT-CO2": (70, 80, 80),
    "PRD-GASOLINE": (92.0, 90.0, 82.0), "PRD-JET": (96.0, 94.0, 87.0), "PRD-ULSD": (98.5, 96.0, 89.0), "PRD-LPG": (48.0, 46.0, 42.0),
    "PRD-NAPHTHA": (70.0, 68.0, 66.0), "PRD-BTX": (96.0, 93.0, 85.0), "PRD-BASEOIL": (118.0, 115.0, 108.0),
    "PRD-ASPHALT": (58.0, 56.0, 55.0), "PRD-FUELOIL": (66.0, 64.0, 63.0), "PRD-COKE": (95, 90, 80), "PRD-SULFUR": (110, 100, 60),
}
PRICE_SETS = [("PS-ACT26", "Actual FY2026 average", "recorded"), ("PS-PLAN27", "Plan FY2027", "assumption"),
              ("PS-STRESS", "Stress case (compressed cracks)", "assumption")]
SPECS = {"PRD-GASOLINE": [("spec_ron_min", 92.0, "RON"), ("spec_rvp_max", 60.0, "kPa"), ("spec_benzene_max", 1.0, "vol%"),
                          ("spec_sulfur_max", 10.0, "ppmw")],
         "PRD-ULSD": [("spec_cetane_min", 51.0, "cetane"), ("spec_sulfur_max", 10.0, "ppmw"), ("spec_density_max", 0.845, "t/m3"),
                      ("spec_flash_min", 55.0, "degC")],
         "PRD-JET": [("spec_flash_min", 38.0, "degC"), ("spec_freeze_max", -47.0, "degC"), ("spec_sulfur_max", 3000.0, "ppmw")]}
BLEND_PROPS = {   # component stream: properties (LIMS monthly composite)
    "STR-GHT-GASO": dict(ron=91.0, rvp=58.0, benzene=0.8, sulfur_ppm=8.0),
    "STR-CCR-REF-GBL": dict(ron=100.5, rvp=35.0, benzene=3.0, sulfur_ppm=0.5),
    "STR-ISOM-ISO": dict(ron=88.0, rvp=88.0, benzene=0.1, sulfur_ppm=0.5),
    "STR-ALKY-ALK": dict(ron=95.5, rvp=32.0, benzene=0.0, sulfur_ppm=2.0),
    "STR-MTBE-PROD": dict(ron=117.0, rvp=55.0, benzene=0.0, sulfur_ppm=5.0),
    "STR-HCU-DSL": dict(cetane=62.0, sulfur_ppm=3.0, flash=68.0),
    "STR-DHT-ULSD": dict(cetane=50.0, sulfur_ppm=8.0, flash=60.0),
    "STR-HCU-JET": dict(flash=45.0, freeze=-52.0, sulfur_ppm=5.0),
    "STR-KHT-JET": dict(flash=42.0, freeze=-48.0, sulfur_ppm=60.0),
}
LAB_QUALITY = [("GBL-1", "AL", "Finished gasoline RON (lab)", "RON", 92.4), ("GBL-1", "AL", "Finished gasoline RVP (lab)", "kPa", 59.1),
               ("GBL-1", "AL", "Finished gasoline benzene (lab)", "vol%", 0.9), ("GBL-1", "AL", "Finished gasoline sulfur (lab)", "ppmw", 4.9),
               ("DBL-1", "AL", "Finished diesel cetane index (lab)", "cetane", 52.3), ("DBL-1", "AL", "Finished diesel sulfur (lab)", "ppmw", 6.9),
               ("DBL-1", "AL", "Finished diesel flash point (lab)", "degC", 61.0), ("DBL-1", "AL", "Finished jet flash point (lab)", "degC", 43.0),
               ("DBL-1", "AL", "Finished jet freeze point (lab)", "degC", -49.0)]
ASSAYS = {  # cut yields vol%: LPG, NAP, KERO, DSL, AGO, VGO, VR; nickel, vanadium (ppmw), nitrogen (ppmw), VR CCR (wt%)
    "CR-AL": dict(LPG=1.2, NAP=20.5, KERO=12.5, DSL=20.3, AGO=7.2, VGO=19.5, VR=18.8, ni=5, v=14, n=900, vr_ccr=20.0),
    "CR-BM": dict(LPG=0.9, NAP=17.5, KERO=11.2, DSL=19.2, AGO=6.9, VGO=21.0, VR=23.3, ni=12, v=42, n=1400, vr_ccr=24.0),
    "CR-MUR": dict(LPG=1.0, NAP=25.5, KERO=12.8, DSL=21.0, AGO=6.8, VGO=18.5, VR=14.4, ni=1, v=1, n=300, vr_ccr=10.0),
}
CUT_VALUES = dict(LPG=48.0, NAP=70.0, KERO=96.0, DSL=98.5, AGO=95.0, VGO=86.0, VR=62.0)      # USD/bbl, LP cut values (PS-ACT26 basis)
MARGINAL_VALUES = {"CDU-A": 8.5, "CDU-B": 8.5, "VDU-1": 3.0, "DCU-1": 14.0, "FCC-1": 9.0, "HCU-1": 12.0, "CCR-1": 6.5, "NHT-1": 2.0,
                   "DHT-1": 3.0, "KHT-1": 1.5, "VGOHT-1": 2.5, "GHT-1": 1.0, "ISOM-1": 4.0, "ALKY-1": 11.0, "ARO-1": 5.0,
                   "LUBE-1": 22.0, "MTBE-1": 15.0, "ASPH-1": -2.0, "LPG-1": 1.0}
PLAN_FEED = {"CDU-A": 247, "CDU-B": 247, "VDU-1": 196, "DCU-1": 88, "VGOHT-1": 76, "FCC-1": 75, "HCU-1": 92, "CCR-1": 90,
             "NHT-1": 113, "DHT-1": 130, "ISOM-1": 42, "ALKY-1": 27, "ARO-1": 48, "LUBE-1": 22}
CONSTRAINTS = [  # id, name, constrained entity, limit, activity (predicate on the entity or number), unit, shadow price, price unit
    ("LPC-CCR-CAP", "Reformer feed capacity", "CCR-1", 90.0, ("CCR-1", "feed_rate"), "kbd", 6.5, "USD/bbl"),
    ("LPC-HCU-CAP", "Hydrocracker feed capacity", "HCU-1", 95.0, ("HCU-1", "feed_rate"), "kbd", 0.0, "USD/bbl"),
    ("LPC-SRU-CAP", "Sulfur recovery capacity", "SRU-1", 1200.0, ("SRU-1", "sulfur_production"), "t/d", 0.0, "USD/t"),
    ("LPC-H2", "Hydrogen supply", "UTL-H2", None, ("SITE-GAMMA", "h2_supply_capacity"), "MMSCFD", 1.9, "USD/kscf"),
    ("LPC-GASO-RON", "Gasoline RON minimum", "PRD-GASOLINE", 92.0, None, "RON", 0.55, "USD/RON-bbl"),
    ("LPC-ULSD-S", "Diesel sulfur maximum", "PRD-ULSD", 10.0, None, "ppmw", 0.0, "USD/ppm-bbl"),
    ("LPC-CDU-CAP", "Crude capacity", "SITE-GAMMA", 500.0, None, "kbd", 0.0, "USD/bbl"),
]
EF = [("ef_fuel_gas", 57.0, "kgCO2/GJ", "Site fuel-gas carbon factor (analyser-based, synthetic)"),
      ("ef_natural_gas", 56.1, "kgCO2/GJ", "IPCC 2006 default (natural gas)"),
      ("emission_factor_fuel", 53.06, "kgCO2/MMBtu", "IPCC 2006 default (natural gas), per MMBtu"),
      ("ef_fcc_coke", 3.3, "t/t", "Stoichiometric (coke ~90 wt% carbon)"),
      ("ef_grid", 0.45, "t/MWh", "Grid operator average (synthetic)")]


def apply(b, tag_rows):
    N, E, F = b.node, b.edge, b.fact
    fid = lambda s, p: b.fact_obj(s, p)["id"]
    val = lambda s, p: b.fact_value(s, p)
    calc = lambda subj, pred, v, unit, lineage, owner="ROLE-PLAN", **kw: F(subj, pred, v, unit, as_of=AS_OF, src="KG derived",
                                                                          owner=owner, method="calculated", lineage=lineage, **kw)

    def utag(parent, ttype, desc, unit, value, kind):
        _tag.counter[SKELETON_TAGS] = _tag.counter.get(SKELETON_TAGS, SKELETON_TAGS * 1000) + 1
        tid = f"LAB-{_tag.counter[SKELETON_TAGS]}" if kind == "lab" else f"{ttype}-{_tag.counter[SKELETON_TAGS]}"
        return tid, _tag(b, tag_rows, parent, tid, ttype, desc, unit, kind, value, None, parent, plant_unit=parent)

    # ------------------------------------------------------------------ products, markets, inputs
    N("MKT-DOMESTIC", "Market", "Domestic market (fictional)", "material")
    N("MKT-EXPORT", "Market", "Export market (fictional)", "material")
    for pid, name, pu, streams, mkt in PRODUCTS:
        N(pid, "Product", name, "material")
        E(pid, "SOLD_TO", mkt)
        for s in streams:
            E(s, "COMPONENT_OF", pid)
    for mid, name, pu in INPUTS:
        N(mid, "MaterialItem", name, "material")
    E("PRD-GASOLINE", "BLENDED_AT", "GBL-1"); E("PRD-JET", "BLENDED_AT", "DBL-1"); E("PRD-ULSD", "BLENDED_AT", "DBL-1")
    comps = {"PRD-GASOLINE": [s for s in BLEND_PROPS if "ron" in BLEND_PROPS[s]],
             "PRD-ULSD": ["STR-HCU-DSL", "STR-DHT-ULSD"], "PRD-JET": ["STR-HCU-JET", "STR-KHT-JET"]}
    for prod, cs in comps.items():
        for s in cs:
            E(s, "COMPONENT_OF", prod)
    for prod, specs in SPECS.items():
        for k, v, u in specs:
            F(prod, k, v, u, as_of=DESIGN_DATE, src="Product specification (illustrative limits)", owner="ROLE-PROC", method="declared")
    for s, props in BLEND_PROPS.items():
        for k, v in props.items():
            unit = {"ron": "RON", "rvp": "kPa", "benzene": "vol%", "sulfur_ppm": "ppmw", "cetane": "cetane", "flash": "degC",
                    "freeze": "degC"}[k]
            F(s, f"blend_{k}", v, unit, as_of=AS_OF, src="LIMS (monthly composite)", owner="ROLE-LAB", method="measured", conf="medium")
    lab = {}
    for unit, tt, desc, u, v in LAB_QUALITY:
        tid, f = utag(unit, tt, desc, u, v, "lab")
        lab[desc] = (tid, f)

    def pool(prod, key):
        cs = comps[prod]
        vol = sum(val(s, "flow_rate") for s in cs)
        v = sum(val(s, "flow_rate") * val(s, f"blend_{key}") for s in cs) / vol
        return round(v, 2), [fid(s, "flow_rate") for s in cs] + [fid(s, f"blend_{key}") for s in cs]
    for prod, key, pred, unit in [("PRD-GASOLINE", "ron", "pool_ron_calc", "RON"), ("PRD-GASOLINE", "rvp", "pool_rvp_calc", "kPa"),
                                  ("PRD-GASOLINE", "benzene", "pool_benzene_calc", "vol%"), ("PRD-ULSD", "cetane", "pool_cetane_calc", "cetane"),
                                  ("PRD-ULSD", "sulfur_ppm", "pool_sulfur_calc", "ppmw")]:
        v, lin = pool(prod, key)
        calc(prod, pred, v, unit, lin, owner="ROLE-PROC")
    ron_lab = lab["Finished gasoline RON (lab)"]
    og = calc("PRD-GASOLINE", "octane_giveaway", round(val(ron_lab[0], "latest_value") - val("PRD-GASOLINE", "spec_ron_min"), 2), "RON",
              [ron_lab[1], fid("PRD-GASOLINE", "spec_ron_min")], owner="ROLE-PROC")
    calc("PRD-GASOLINE", "blend_model_bias", round(val("PRD-GASOLINE", "pool_ron_calc") - val(ron_lab[0], "latest_value"), 2), "RON",
         [fid("PRD-GASOLINE", "pool_ron_calc"), ron_lab[1]], owner="ROLE-PROC")
    F(SITE, "octane_value", 0.55, "USD/RON-bbl", as_of=AS_OF, src=LP + " — gasoline RON constraint shadow price", owner="ROLE-PLAN",
      method="assumption", conf="low")
    gv = val("PRD-GASOLINE", "octane_giveaway") * val("STR-GBL-GASO", "flow_rate") * 1000 * 365 * 0.55
    calc("PRD-GASOLINE", "octane_giveaway_value", round(gv), "USD/yr",
         [og, fid("STR-GBL-GASO", "flow_rate"), fid(SITE, "octane_value")], basis="recurring-annual",
         value_low=round(gv * 0.5), value_high=round(gv * 1.4))
    cet = lab["Finished diesel cetane index (lab)"]
    calc("PRD-ULSD", "cetane_giveaway", round(val(cet[0], "latest_value") - val("PRD-ULSD", "spec_cetane_min"), 2), "cetane",
         [cet[1], fid("PRD-ULSD", "spec_cetane_min")], owner="ROLE-PROC")
    sul = lab["Finished diesel sulfur (lab)"]
    calc("PRD-ULSD", "sulfur_giveaway", round(val("PRD-ULSD", "spec_sulfur_max") - val(sul[0], "latest_value"), 2), "ppmw",
         [sul[1], fid("PRD-ULSD", "spec_sulfur_max")], owner="ROLE-PROC")
    rvp = lab["Finished gasoline RVP (lab)"]
    calc("PRD-GASOLINE", "rvp_giveaway", round(val("PRD-GASOLINE", "spec_rvp_max") - val(rvp[0], "latest_value"), 2), "kPa",
         [rvp[1], fid("PRD-GASOLINE", "spec_rvp_max")], owner="ROLE-PROC")
    jf = lab["Finished jet flash point (lab)"]
    calc("PRD-JET", "flash_giveaway", round(val(jf[0], "latest_value") - val("PRD-JET", "spec_flash_min"), 1), "degC",
         [jf[1], fid("PRD-JET", "spec_flash_min")], owner="ROLE-PROC")

    # ------------------------------------------------------------------ price sets
    for ps, name, method in PRICE_SETS:
        N(ps, "PriceSet", name, "material")
    for mat, prices in PRICES.items():
        unit = next((p[2] for p in PRODUCTS if p[0] == mat), None) or next((i[2] for i in INPUTS if i[0] == mat), "USD/bbl")
        for (ps, name, method), v in zip(PRICE_SETS, prices):
            sid = f"PR-{ps[3:]}-{mat.split('-', 1)[1]}"
            N(sid, "PriceSeries", f"{b.nodes[mat]['name']} — {name}", "material")
            E(sid, "PRICE_OF", mat)
            E(sid, "IN_PRICE_SET", ps)
            F(sid, "price", v, unit, as_of=AS_OF if ps == "PS-ACT26" else "2026-09-30", src=SYN, owner="ROLE-PLAN", method=method, conf="low")
    price = lambda mat, ps="ACT26": fid(f"PR-{ps}-{mat.split('-', 1)[1]}", "price")
    pval = lambda mat, ps="ACT26": val(f"PR-{ps}-{mat.split('-', 1)[1]}", "price")

    # ------------------------------------------------------------------ crude assays, CDU prediction vs actual, grade margins
    for g, a in ASSAYS.items():
        for cut in ("LPG", "NAP", "KERO", "DSL", "AGO", "VGO", "VR"):
            F(g, f"cut_yield_{cut.lower()}", a[cut], "vol%", as_of="2026-06-30", src="Crude assay (synthetic, representative of grade)",
              owner="ROLE-PLAN", method="indicative", conf="medium")
        for k, u in (("ni", "ppmw"), ("v", "ppmw"), ("n", "ppmw"), ("vr_ccr", "wt%")):
            F(g, {"ni": "nickel", "v": "vanadium", "n": "nitrogen", "vr_ccr": "vacuum_residue_ccr"}[k], a[k], u, as_of="2026-06-30",
              src="Crude assay (synthetic, representative of grade)", owner="ROLE-PLAN", method="indicative", conf="medium")
    for c in ("LPG", "NAP", "KERO", "DSL", "AGO", "VGO", "VR"):
        F("LP-GAMMA" if "LP-GAMMA" in b.nodes else SITE, f"cut_value_{c.lower()}", CUT_VALUES[c], "USD/bbl", as_of=AS_OF, src=LP,
          owner="ROLE-PLAN", method="assumption", conf="low")
    for tr in TRAINS:
        u = f"CDU-{tr}"
        shares = [(g, f"CMP-{tr}-{g[3:]}") for g in ASSAYS]
        for cut, key in (("LPG", "lpg"), ("NAP", "nap"), ("KERO", "kero"), ("DSL", "dsl"), ("AGO", "ago")):
            pred = round(sum(val(g, f"cut_yield_{cut.lower()}") * val(c, "slate_share") for g, c in shares), 2)
            pf = calc(u, f"yield_{key}_assay", pred, "vol%", [fid(g, f"cut_yield_{cut.lower()}") for g, _ in shares] +
                      [fid(c, "slate_share") for _, c in shares], owner="ROLE-PROC")
            calc(u, f"yield_{key}_deviation", round(val(u, f"yield_{key}") - pred, 2), "vol%", [fid(u, f"yield_{key}"), pf], owner="ROLE-PROC")
        pred = round(sum((val(g, "cut_yield_vgo") + val(g, "cut_yield_vr")) * val(c, "slate_share") for g, c in shares), 2)
        pf = calc(u, "yield_ar_assay", pred, "vol%", [fid(g, "cut_yield_vgo") for g, _ in shares] + [fid(g, "cut_yield_vr") for g, _ in shares] +
                  [fid(c, "slate_share") for _, c in shares], owner="ROLE-PROC")
        calc(u, "yield_ar_deviation", round(val(u, "yield_ar") - pred, 2), "vol%", [fid(u, "yield_ar"), pf], owner="ROLE-PROC")
    for g in ASSAYS:
        cv = [fid(SITE, f"cut_value_{c.lower()}") for c in CUT_VALUES]
        gpw = sum(val(g, f"cut_yield_{c.lower()}") / 100 * CUT_VALUES[c] for c in CUT_VALUES)
        gp = calc(g, "gross_product_worth", round(gpw, 2), "USD/bbl", [fid(g, f"cut_yield_{c.lower()}") for c in CUT_VALUES] + cv)
        calc(g, "grade_margin", round(gpw - pval(g), 2), "USD/bbl", [gp, price(g)], basis="per bbl crude, before processing costs")

    # ------------------------------------------------------------------ LP backbone
    N("LP-GAMMA", "LPModel", "Refinery Gamma LP model (FY2027 plan)", "application", system="APP-LP")
    for u, mv in MARGINAL_VALUES.items():
        sm = f"LPS-{u}"
        N(sm, "LPSubmodel", f"LP submodel {u}", "application")
        E(sm, "SUBMODEL_OF", "LP-GAMMA")
        E(sm, "REPRESENTS", u)
        F(sm, "lp_marginal_value", mv, "USD/bbl", as_of=AS_OF, src=LP, owner="ROLE-PLAN", method="assumption", conf="low",
          basis="per bbl of unit feed")
        if u in PLAN_FEED:
            pf = F(sm, "plan_feed_rate", PLAN_FEED[u], "kbd", as_of="2026-09-30", src=LP, owner="ROLE-PLAN", method="assumption", conf="medium")
            actual = b.fact_obj(u, "feed_rate") or b.fact_obj(u, "throughput_fy2026")
            calc(u, "plan_variance", round(actual["value"] - PLAN_FEED[u], 1), "kbd", [actual["id"], pf])
    for cid, name, ent, limit, act, unit, sp, spu in CONSTRAINTS:
        N(cid, "LPConstraint", name, "material")
        E(cid, "CONSTRAINS", ent)
        lim = F(cid, "limit", limit if limit is not None else val(*act), unit, as_of=AS_OF, src=LP, owner="ROLE-PLAN", method="assumption",
                conf="medium")
        if act:
            a = calc(cid, "activity", val(*act), unit, [fid(*act)])
            calc(cid, "slack", round(val(cid, "limit") - val(*act), 1), unit, [lim, a])
        F(cid, "shadow_price", sp, spu, as_of=AS_OF, src=LP, owner="ROLE-PLAN", method="assumption", conf="low")

    # ------------------------------------------------------------------ gross margin model (PS-ACT26), opex, carbon
    rev_lin, rev = [], 0.0
    for pid, name, pu, streams, mkt in PRODUCTS:
        for s in streams:
            q = b.fact_obj(s, "flow_rate")
            v = q["value"] * (1000 if pu == "USD/bbl" else 1) * pval(pid)
            rev += v
            rev_lin += [q["id"], price(pid)]
    rv = calc(SITE, "product_revenue", round(rev), "USD/d", rev_lin, basis="recurring-daily")
    crude_lin, crude = [], 0.0
    for tr in TRAINS:
        for g in ASSAYS:
            cmp_ = f"CMP-{tr}-{g[3:]}"
            v = val(f"CDU-{tr}", "throughput_fy2026") * val(cmp_, "slate_share") * 1000 * pval(g)
            crude += v
            crude_lin += [fid(f"CDU-{tr}", "throughput_fy2026"), fid(cmp_, "slate_share"), price(g)]
    cc = calc(SITE, "crude_cost", round(crude), "USD/d", crude_lin, basis="recurring-daily")
    other = [(val("STR-VGO-IMP", "flow_rate") * 1000 * pval("MAT-VGO"), [fid("STR-VGO-IMP", "flow_rate"), price("MAT-VGO")]),
             (val("STR-MEOH-IMP", "mass_rate") * pval("MAT-MEOH"), [fid("STR-MEOH-IMP", "mass_rate"), price("MAT-MEOH")])]
    oc = calc(SITE, "other_feedstock_cost", round(sum(x for x, _ in other)), "USD/d", sum((l for _, l in other), []), basis="recurring-daily")
    ng_mmbtu = val("HMU-1", "natural_gas_consumption") + NG_TO_FG_MEASURED * 44.6
    ec = calc(SITE, "energy_cost", round(ng_mmbtu * pval("MAT-NG") + GRID_IMPORT_MEASURED * 24 * pval("MAT-POWER")), "USD/d",
              [fid("HMU-1", "natural_gas_consumption"), fid("STR-NG-FG", "flow_rate"), price("MAT-NG"), fid("UTL-PWR", "grid_import"),
               price("MAT-POWER")], basis="recurring-daily")
    F("FCC-1", "fresh_catalyst_price", 2800, "USD/t", as_of=AS_OF, src="Catalyst supply contract (synthetic)", owner="ROLE-CONV",
      method="recorded", conf="medium")
    F("FCC-1", "baseline_fresh_catalyst_rate", 6.5, "t/d", as_of=DESIGN_DATE, src="FCC design basis", owner="ROLE-CONV", method="declared")
    fcat = calc("FCC-1", "catalyst_cost", round(val("FCC-1", "fresh_catalyst_rate") * 2800 * 365), "USD/yr",
                [fid("FCC-1", "fresh_catalyst_rate"), fid("FCC-1", "fresh_catalyst_price")], basis="recurring-annual")
    calc("FCC-1", "excess_catalyst_cost", round((val("FCC-1", "fresh_catalyst_rate") - 6.5) * 2800 * 365), "USD/yr",
         [fid("FCC-1", "fresh_catalyst_rate"), fid("FCC-1", "baseline_fresh_catalyst_rate"), fid("FCC-1", "fresh_catalyst_price")],
         basis="recurring-annual")
    oth = F(SITE, "chemicals_and_other_catalysts_cost", 21_000_000, "USD/yr", as_of=AS_OF, src="Site economics (monthly close)",
            owner="ROLE-PLAN", method="recorded", conf="medium")
    vo = calc(SITE, "variable_opex", round(val(SITE, "energy_cost") + (val("FCC-1", "catalyst_cost") + 21_000_000) / 365), "USD/d",
              [ec, fcat, oth], basis="recurring-daily")
    crude_kbd = val("CDU-A", "throughput_fy2026") + val("CDU-B", "throughput_fy2026")
    gm = calc(SITE, "gross_margin_model", round((rev - crude - val(SITE, "other_feedstock_cost") - val(SITE, "variable_opex")) /
                                                (crude_kbd * 1000), 2), "USD/bbl",
              [rv, cc, oc, vo, fid("CDU-A", "throughput_fy2026"), fid("CDU-B", "throughput_fy2026")], basis="per bbl crude")
    calc(SITE, "grm_model_variance", round(val(SITE, "gross_margin_model") - val(SITE, "grm_fy2026"), 2), "USD/bbl",
         [gm, fid(SITE, "grm_fy2026")], basis="model minus recorded (fixed costs, inventory and pricing lags not modelled)")
    # CO2
    for k, v, u, src in EF:
        F(SITE, k, v, u, as_of=DESIGN_DATE, src=src, owner="ROLE-ENV", method="declared" if "IPCC" in src else "indicative", conf="medium")
    fired_mw = sum(b._by_id[x]["value"] for u in list(FIRED_DUTY) + ["CDU-A", "CDU-B", "FCC-1", "HCU-1", "DCU-1"]
                   for x in [f["id"] for f in b.facts if f["subject"] in (u,) and f["predicate"] in ("fired_duty", "heater_fired_duty")])
    fired_lin = [f["id"] for f in b.facts if f["predicate"] in ("fired_duty", "heater_fired_duty")]
    heater_mw = sum(b._by_id[x]["value"] for x in fired_lin)
    c1 = calc(SITE, "co2_combustion", round(heater_mw * 86.4 * 365 * 57.0 / 1e6, 1), "ktCO2/yr", fired_lin + [fid(SITE, "ef_fuel_gas")],
              owner="ROLE-ENV")
    c2 = calc(SITE, "co2_smr", round(val("HMU-1", "h2_production") * 2.41 * 365 * 9.0 / 1000, 1), "ktCO2/yr",
              [fid("HMU-1", "h2_production"), fid("HMU-1", "co2_intensity")], owner="ROLE-ENV")
    c3 = calc(SITE, "co2_fcc_coke", round(val("FCC-1", "coke_make") * 3.3 * 365 / 1000, 1), "ktCO2/yr",
              [fid("FCC-1", "coke_make"), fid(SITE, "ef_fcc_coke")], owner="ROLE-ENV")
    c4 = calc(SITE, "co2_scope2", round(GRID_IMPORT_MEASURED * 8760 * 0.45 / 1000, 1), "ktCO2/yr",
              [fid("UTL-PWR", "grid_import"), fid(SITE, "ef_grid")], owner="ROLE-ENV")
    tot = sum(val(SITE, k) for k in ("co2_combustion", "co2_smr", "co2_fcc_coke"))
    ct = calc(SITE, "co2_scope1", round(tot, 1), "ktCO2/yr", [c1, c2, c3], owner="ROLE-ENV")
    calc(SITE, "co2_intensity", round(tot * 1e6 / (crude_kbd * 1000 * 365), 1), "kgCO2/bbl", [ct, fid("CDU-A", "throughput_fy2026"),
                                                                                              fid("CDU-B", "throughput_fy2026")], owner="ROLE-ENV")
    calc(SITE, "carbon_cost", round(tot * 1000 * pval("MAT-CO2")), "USD/yr", [ct, price("MAT-CO2")], basis="recurring-annual (if priced)")

    # ------------------------------------------------------------------ cost centres
    ccs = [n["id"] for n in b.nodes.values() if n["cls"] == "CostCentre"]
    for cc in ccs:
        units = [e["source"] for e in b.edges if e["rel"] == "MEMBER_OF" and e["target"] == cc]
        scope = set()
        for u in units:
            stack = [u]
            while stack:
                x = stack.pop()
                scope.add(x)
                stack += [e["source"] for e in b.edges if e["rel"] == "PART_OF" and e["target"] == x]
        wos = set()
        for e in b.edges:
            if e["rel"] == "PERFORMED_ON" and e["target"] in scope:
                wos.add(e["source"])
            if e["rel"] == "FAILURE_OF" and e["target"] in scope:
                wos.update(x["source"] for x in b.edges if x["rel"] == "REMEDIATES" and x["target"] == e["source"])
        costs = [fid(w, "actual_cost") for w in sorted(wos) if b.fact_obj(w, "actual_cost")]
        if costs:
            calc(cc, "maintenance_cost_fy2026", round(sum(b._by_id[c]["value"] for c in costs)), "USD", costs, owner="ROLE-MAINT",
                 basis="FY2026 actual (corrective and preventive work orders in the graph)")
        else:
            F(cc, "maintenance_cost_fy2026", 0, "USD", as_of=AS_OF, src="CMMS (no work orders booked in FY2026)", owner="ROLE-MAINT",
              method="recorded", basis="FY2026 actual")

    # ------------------------------------------------------------------ catalyst cycle economics
    for k, v, u, m in [("catalyst_inventory_cost", 16_300_000, "USD", "recorded"), ("design_cycle_length", 36, "months", "declared"),
                       ("sor_wabt", 382, "degC", "recorded")]:
        F("HCU-1", k, v, u, as_of=DESIGN_DATE, src="Catalyst supply contract / licensor guarantee (synthetic)", owner="ROLE-CONV",
          method=m, conf="medium")

    # ------------------------------------------------------------------ blending decision chain
    _blend_chain(b, lab)
    # ------------------------------------------------------------------ lost margin (final pass over all failures)
    _lost_margins(b)


def _blend_chain(b, lab):
    N, E = b.node, b.edge

    def p(pid, cls, name, level, parent, owner=None, **props):
        N(pid, cls, name, "process", level, parent, **props)
        if owner:
            E(pid, "OWNED_BY", owner)
    p("P-BLEND", "Process", "Gasoline & distillate blending", 4, "PG-QUAL", "ROLE-PROC")
    for a in ("GBL-1", "DBL-1"):
        E("P-BLEND", "ACTS_ON", a)
    prev = "P-BLEND"
    for lvl, (sid, sn) in zip(range(5, 10), [("SP-BLEND", "Blend optimisation"), ("ACT-BLEND", "Set blend recipes"),
                                             ("TSK-BLEND", "Review pool qualities, giveaway and component availability"),
                                             ("DEC-BLEND", "Approve blend recipe and reformate routing"), ("DOB-BLEND", "Blend certificate")]):
        p(sid, {5: "SubProcess", 6: "Activity", 7: "Task", 8: "DecisionPoint", 9: "DataObject"}[lvl], sn, lvl, prev)
        prev = sid
    E("DEC-BLEND", "GOVERNS", "GBL-1"); E("DEC-BLEND", "GOVERNS", "DBL-1")
    for did, dn, tag_desc, maps in [("DE-POOLRON", "Gasoline RON", "Finished gasoline RON (lab)", None),
                                    ("DE-POOLRVP", "Gasoline RVP", "Finished gasoline RVP (lab)", None),
                                    ("DE-CETANE", "Diesel cetane index", "Finished diesel cetane index (lab)", None),
                                    ("DE-ULSD-S", "Diesel sulfur", "Finished diesel sulfur (lab)", None),
                                    ("DE-GIVEAWAY", "Octane giveaway", None, "octane_giveaway")]:
        p(did, "DataElement", dn, 10, "DOB-BLEND", "ROLE-PROC", domain="product quality", maps_to_predicate=maps)
        if tag_desc:
            E(did, "INSTANTIATED_BY", lab[tag_desc][0])
        E("DEC-BLEND", "CONSUMES", did)
    E("APP-LIMS", "SUPPORTS", "P-BLEND")
    E("APP-LIMS", "SYSTEM_OF_RECORD_FOR", "DOB-BLEND")


def _lost_margins(b):
    for fnode in [n for n in b.nodes.values() if n["cls"] == "Failure"]:
        fl = fnode["id"]
        rc, rd = b.fact_obj(fl, "rate_reduction"), b.fact_obj(fl, "rate_reduction_days")
        if not rc:
            continue
        target = next(e["target"] for e in b.edges if e["source"] == fl and e["rel"] == "FAILURE_OF")
        x = target
        while b.nodes[x]["level"] != 4:
            x = next(e["target"] for e in b.edges if e["source"] == x and e["rel"] == "PART_OF")
        mv = b.fact_obj(f"LPS-{x}", "lp_marginal_value")
        v = round(rc["value"] * 1000 * rd["value"] * mv["value"])
        b.fact(fl, "lost_margin", v, "USD", as_of=fnode["props"]["date"], src="KG derived", owner="ROLE-PLAN", method="calculated",
               lineage=[rc["id"], rd["id"], mv["id"]], basis=f"one-off; {x} feed lost x LP marginal value of {x}",
               value_low=round(v * 0.6), value_high=round(v * 1.5))
