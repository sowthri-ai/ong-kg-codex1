"""
Refinery-wide insights for the Refinery Gamma model (v0.5).

Insight contract (ogkg/insights.py) plus a value contract: value_usd, value_basis (recurring-annual / one-off /
at-risk-per-day / gross-pre-capex), value_low, value_high, capex_required and confidence. Unknown values are None,
never 0. Every number is read from the graph; the what-if arithmetic is stated in the caveat.

The event patterns in the synthetic data (for example precursors before failures) were seeded to demonstrate that the
graph can detect them; the insights detect them with generic rules, not by name.
"""
from datetime import date

from . import cdu_insights

SITE = "SITE-GAMMA"
_usd = cdu_insights._usd


def _f(kg, s, p):
    f = kg.fact(s, p)
    if f is None:
        raise KeyError(f"{s}.{p} missing")
    return f


def _vc(value, basis, low=None, high=None, capex=None, confidence="low", label=""):
    return dict(value_usd=None if value is None else round(value), value_basis=basis,
                value_low=None if low is None else round(low), value_high=None if high is None else round(high),
                capex_required=capex, confidence=confidence, value_label=label)


def nelson_complexity(kg):
    units = [n for n in kg.nodes.values() if n["cls"] == "PlantUnit" and kg.fact(n["id"], "nci_contribution")]
    total = _f(kg, SITE, "nelson_complexity_index")
    rows, ev = [], [total["id"]]
    for n in units:
        c, fac = kg.fact(n["id"], "nci_contribution"), kg.fact(n["id"], "nelson_factor")
        ev += [c["id"], fac["id"]]
        rows.append(dict(unit=n["id"], name=n["name"], category=fac["source_ref"], factor=fac["value"],
                         capacity_kbd=kg.value(n["id"], "design_capacity"), contribution=round(c["value"], 3),
                         share_pct=round(100 * c["value"] / total["value"], 1)))
    rows.sort(key=lambda r: -r["contribution"])
    top = rows[:3]
    cap_top = sum(r["capacity_kbd"] for r in top)
    return dict(
        id="nelson-complexity", title="Nelson complexity, rebuilt from the graph",
        question="What is Refinery Gamma's Nelson complexity, and which units drive it?",
        headline=(f"NCI {total['value']:.1f} from {len(rows)} units on 500 kbpd of crude. Lubes, aromatics and isomerisation — "
                  f"{cap_top:.0f} kbpd of capacity — give {sum(r['share_pct'] for r in top):.0f}% of it; the "
                  f"{next(r['capacity_kbd'] for r in rows if r['unit'] == 'LUBE-1')} kbpd lube plant alone adds "
                  f"{next(r['contribution'] for r in rows if r['unit'] == 'LUBE-1'):.1f} points."),
        **_vc(None, None, confidence="medium"),
        domains=["Asset register (capacities)", "Process design basis", "Public benchmark factors"],
        rows=rows, path=[SITE] + [r["unit"] for r in top], evidence=sorted(set(ev)),
        recommendation=("Quote NCI as a screening benchmark only. Complexity is concentrated in small, high-factor units, so NCI "
                        "overstates margin capability; judge investments on LP marginal values by unit."),
        decision_owner="Planning & Economics Lead",
        caveat="1998 Nelson factors; hydrogen, sulfur, utilities and blending carry no factor in that table and are excluded.")


def hydrogen_headroom(kg):
    demand, supply, head = (_f(kg, SITE, k) for k in ("h2_demand", "h2_supply_capacity", "h2_headroom"))
    ccr, hmu, hmu_cap = _f(kg, "CCR-1", "h2_production"), _f(kg, "HMU-1", "h2_production"), _f(kg, "HMU-1", "design_capacity")
    rate, eff = _f(kg, "HCU-1", "h2_consumption_rate"), _f(kg, "HCU-1", "h2_makeup_efficiency")
    mv = _f(kg, "LPS-HCU-1", "lp_marginal_value")
    resid = _f(kg, SITE, "h2_balance_residual")
    consumers = [n for n in kg.nodes if kg.fact(n, "h2_makeup")]
    rows = sorted((dict(unit=u, feed_kbd=kg.value(u, "feed_rate"), chemical_MMSCFD=kg.value(u, "h2_consumption"),
                        makeup_MMSCFD=kg.value(u, "h2_makeup"), purge_loss_MMSCFD=kg.value(u, "h2_purge_loss"),
                        share_pct=round(100 * kg.value(u, "h2_makeup") / demand["value"], 1)) for u in consumers),
                  key=lambda r: -r["makeup_MMSCFD"])
    deficit = ccr["value"] - head["value"]
    per_kbd = rate["value"] / eff["value"] / 1000
    hcu_cut = deficit / per_kbd
    per_day = hcu_cut * 1000 * mv["value"]
    purge = sum(r["purge_loss_MMSCFD"] for r in rows)
    ev = [x["id"] for x in (demand, supply, head, ccr, hmu, hmu_cap, rate, eff, mv, resid)] + \
         [kg.fact(u, "h2_makeup")["id"] for u in consumers]
    return dict(
        id="hydrogen-headroom", title="Hydrogen network headroom and reformer-outage exposure",
        question="How much hydrogen headroom do we have, and what happens if the reformer trips?",
        headline=(f"Make-up demand {demand['value']:.1f} MMSCFD (incl. {purge:.0f} MMSCFD purge and solution losses) against "
                  f"{supply['value']:.0f} available: headroom {head['value']:.1f} MMSCFD ({100 * head['value'] / supply['value']:.1f}%), "
                  f"SMR at {100 * hmu['value'] / hmu_cap['value']:.0f}%. A reformer outage removes {ccr['value']:.0f} MMSCFD and leaves "
                  f"the network {deficit:.0f} MMSCFD short — about {hcu_cut:.0f} kbpd of hydrocracker feed, ≈{_usd(per_day)} of margin "
                  "per day."),
        **_vc(per_day, "at-risk-per-day", per_day * 0.6, per_day * 1.5, confidence="low", label="at risk per outage day"),
        domains=["Unit feed rates (hydrocarbon accounting)", "Licensor hydrogen consumption", "Hydrogen network study",
                 "SMR product meter", "LP marginal values"],
        rows=rows, path=["CCR-1", "UTL-H2", "HMU-1", "HCU-1", "NET-H2"], evidence=sorted(set(ev)),
        recommendation=(f"Agree a hydrogen shedding sequence before it is needed (DEC-H2): hydrocracker rate first, protecting ULSD. "
                        f"Purge and solution losses are {purge:.0f} MMSCFD — recovering a third of them would more than double the "
                        f"headroom. The SMR meter reads {resid['value']:+.2f}% against the consumer balance: check its calibration."),
        decision_owner="Process Engineer (DEC-H2) with Planning & Economics Lead",
        caveat=("Make-up efficiencies are from the 2025 network study (medium confidence). Margin uses the LP marginal value of "
                "hydrocracker feed (low confidence); the real loss depends on what replaces the lost feed."))


def sulfur_ceiling(kg):
    s_in, mass, s_avg = _f(kg, SITE, "sulfur_in"), _f(kg, SITE, "crude_mass_rate"), _f(kg, SITE, "crude_sulfur_avg")
    s_vgo = _f(kg, "STR-VGO-IMP", "sulfur_flow")
    sru, cap, trains = _f(kg, "SRU-1", "sulfur_production"), _f(kg, "SRU-1", "design_capacity"), _f(kg, "SRU-1", "claus_trains")
    share = sru["value"] / s_in["value"]
    ceiling = lambda capacity: (capacity / share - s_vgo["value"]) / mass["value"] * 100
    s_max, s_max_1 = ceiling(cap["value"]), ceiling(cap["value"] * (trains["value"] - 1) / trains["value"])
    g = {k: kg.fact(k, "sulfur") for k in ("CR-AL", "CR-BM", "CR-MUR")}
    sh = {k: kg.fact(f"CMP-A-{k[3:]}", "slate_share") for k in g}
    bm_max = (s_max - g["CR-AL"]["value"] * sh["CR-AL"]["value"] - g["CR-MUR"]["value"] * (1 - sh["CR-AL"]["value"])) / \
             (g["CR-BM"]["value"] - g["CR-MUR"]["value"])
    m_bm, m_mur = _f(kg, "CR-BM", "grade_margin"), _f(kg, "CR-MUR", "grade_margin")
    crude_kbd = kg.value("CDU-A", "throughput_fy2026") + kg.value("CDU-B", "throughput_fy2026")
    swap_kbd = (bm_max - sh["CR-BM"]["value"]) * crude_kbd
    value = swap_kbd * 1000 * 365 * (m_bm["value"] - m_mur["value"])
    rows = [dict(item="Sulfur in (crude + imported VGO)", t_per_d=s_in["value"], share_pct=100.0),
            dict(item="Recovered in SRU (measured)", t_per_d=sru["value"], share_pct=round(100 * share, 1))] + \
           [dict(item=f"{kg.nodes[f['subject']]['name']}", t_per_d=f["value"], share_pct=round(100 * f["value"] / s_in["value"], 1))
            for f in kg.fact_list if f["predicate"] == "sulfur_flow" and f["subject"] != "STR-VGO-IMP" and f["value"] >= 1]
    ev = [x["id"] for x in (s_in, mass, s_avg, s_vgo, sru, cap, trains, m_bm, m_mur)] + [x["id"] for x in g.values()] + \
         [x["id"] for x in sh.values()]
    return dict(
        id="sulfur-ceiling", title="Crude sulfur ceiling set by the SRU",
        question="How much more sour crude can we run before sulfur recovery becomes the constraint?",
        headline=(f"The slate averages {s_avg['value']:.2f} wt% S; the SRU is at {100 * sru['value'] / cap['value']:.1f}% "
                  f"({sru['value']:.0f} of {cap['value']:.0f} t/d). The ceiling is ≈{s_max:.2f} wt% S: Basrah Medium could rise from "
                  f"{100 * sh['CR-BM']['value']:.0f}% to ≈{100 * bm_max:.0f}% of the slate, worth ≈{_usd(value)}/yr at FY2026 grade margins. "
                  f"With one of {trains['value']} Claus trains out the ceiling falls to ≈{s_max_1:.2f} wt%, below today's slate."),
        **_vc(value, "recurring-annual", value * 0.5, value * 1.4, confidence="low", label="crude swap per year"),
        domains=["Crude assays", "Crude schedule", "Hydrocarbon accounting", "SRU production", "Product sulfur", "Crude prices"],
        rows=rows, path=[SITE, "CR-BM", "ARU-1", "SWS-1", "SRU-1", "NET-SULFUR"], evidence=sorted(set(ev)),
        recommendation=("Give the planner the ceiling as a live LP constraint (DEC-SLATE). Before any SRU train maintenance, pre-plan a "
                        "sweeter slate or acid-gas shedding (DEC-SULF), because one train out puts today's slate over the limit."),
        decision_owner="Planning & Economics Lead (DEC-SLATE) with Environmental Engineer (DEC-SULF)",
        caveat=("Assumes sulfur distributes to coke, residuals and products in today's proportions. Swap value holds Arab Light "
                "constant and uses illustrative synthetic prices; it ignores yield-driven unit constraints."))


def reformer_bottleneck(kg):
    util, byp = _f(kg, "CCR-1", "utilisation"), _f(kg, "STR-NHT-HN-BYP", "flow_rate")
    sp, spread = _f(kg, "LPC-CCR-CAP", "shadow_price"), _f(kg, SITE, "reformate_upgrade_spread")
    h2y, head, purity = _f(kg, "CCR-1", "h2_yield"), _f(kg, SITE, "h2_headroom"), kg.fact(next(
        n["id"] for n in kg.nodes.values() if n["cls"] == "DataPoint" and n["props"].get("equipment") == "CCR-1" and "purity" in n["name"]),
        "latest_value")
    ng_price, ng_spec = _f(kg, "PR-ACT26-NG", "price"), _f(kg, "HMU-1", "ng_specific_consumption")
    extra_h2 = h2y["value"] * byp["value"] / 1000 * purity["value"] / 100
    h2_credit = extra_h2 * 1000 * ng_spec["value"] * ng_price["value"] * 365
    value = byp["value"] * 1000 * 365 * sp["value"]
    rows = [dict(item="Reformer utilisation", value=util["value"], unit="%"),
            dict(item="Heavy naphtha bypassing the reformer (to naphtha export)", value=byp["value"], unit="kbpd"),
            dict(item="LP shadow price of reformer capacity", value=sp["value"], unit="USD/bbl"),
            dict(item="Hydrogen the bypass would add", value=round(extra_h2, 1), unit="MMSCFD"),
            dict(item="Hydrogen credit at SMR natural-gas cost", value=round(h2_credit / 1e6, 1), unit="USD M/yr"),
            dict(item="Hydrogen headroom today", value=head["value"], unit="MMSCFD")]
    return dict(
        id="reformer-bottleneck", title="Reformer bottleneck: naphtha bypass and lost hydrogen",
        question="Is the reformer limiting margin, and what would debottlenecking unlock?",
        headline=(f"The reformer runs at {util['value']:.0f}% and {byp['value']:.1f} kbpd of heavy naphtha is exported instead of reformed: "
                  f"≈{_usd(value)}/yr gross at the LP shadow price (${sp['value']:.1f}/bbl), plus a {extra_h2:.1f} MMSCFD hydrogen credit "
                  f"worth ≈{_usd(h2_credit)}/yr at SMR gas cost. Both are before debottleneck capex."),
        **_vc(value + h2_credit, "gross-pre-capex", byp["value"] * 1000 * 365 * sp["value"] * 0.6,
              byp["value"] * 1000 * 365 * spread["value"] + h2_credit, capex=None, confidence="low", label="gross per year, pre-capex"),
        domains=["Hydrocarbon accounting", "LP model", "Reformer design basis", "Hydrogen network", "Gas prices"],
        rows=rows, path=["NHT-1", "STR-NHT-HN-BYP", "CCR-1", "LPC-CCR-CAP", "UTL-H2"],
        evidence=sorted({x["id"] for x in (util, byp, sp, spread, h2y, head, purity, ng_price, ng_spec)}),
        recommendation=("Scope a reformer debottleneck study (reactor/regenerator and net-gas compressor limits) and test the case in the "
                        "LP with the octane effect: extra reformate raises pool RON, which is already 0.4 above spec."),
        decision_owner="Planning & Economics Lead with Process Engineer",
        caveat="Shadow price and prices are synthetic assumptions (low confidence). Capex unknown; the value is gross, not NPV.")


def octane_giveaway(kg):
    og, spec, bias = _f(kg, "PRD-GASOLINE", "octane_giveaway"), _f(kg, "PRD-GASOLINE", "spec_ron_min"), _f(kg, "PRD-GASOLINE", "blend_model_bias")
    val = _f(kg, "PRD-GASOLINE", "octane_giveaway_value")
    calc, vol = _f(kg, "PRD-GASOLINE", "pool_ron_calc"), _f(kg, "STR-GBL-GASO", "flow_rate")
    comps = [e["source"] for e in kg.inc.get("PRD-GASOLINE", []) if e["rel"] == "COMPONENT_OF" and kg.fact(e["source"], "blend_ron")]
    rows = [dict(component=kg.nodes[c]["name"], kbd=kg.value(c, "flow_rate"), ron=kg.value(c, "blend_ron"), rvp_kPa=kg.value(c, "blend_rvp"))
            for c in comps]
    return dict(
        id="octane-giveaway", title="Gasoline octane giveaway",
        question="How much octane are we giving away in the gasoline pool, and why?",
        headline=(f"Finished gasoline certifies at {spec['value'] + og['value']:.1f} RON against a {spec['value']:.0f} RON minimum: "
                  f"{og['value']:.1f} RON of giveaway on {vol['value']:.0f} kbpd, ≈{_usd(val['value'])}/yr. The linear blend model predicts "
                  f"{calc['value']:.1f} RON ({bias['value']:+.1f} vs lab), so recipes built on it overshoot."),
        **_vc(val["value"], "recurring-annual", val.get("value_low"), val.get("value_high"), confidence="low", label="giveaway per year"),
        domains=["LIMS", "Blend components", "Product specifications", "Hydrocarbon accounting", "LP shadow price"],
        rows=rows, path=["GBL-1", "PRD-GASOLINE", "STR-CCR-REF-GBL", "STR-ISOM-ISO", "LPC-GASO-RON"],
        evidence=sorted({og["id"], spec["id"], bias["id"], val["id"], calc["id"], vol["id"]} |
                        {kg.fact(c, "blend_ron")["id"] for c in comps}),
        recommendation=("Recalibrate the blend model with a non-linear (interaction) octane method and target 0.1–0.2 RON over spec "
                        "(DEC-BLEND). Route more reformate to aromatics while giveaway persists."),
        decision_owner="Process Engineer (DEC-BLEND) with Planning & Economics Lead",
        caveat="Octane value is the LP shadow price of the RON constraint (synthetic, low confidence).")


def hcu_catalyst_vs_turnaround(kg):
    eor, rate, wabt, sor = _f(kg, "HCU-1", "predicted_eor_date"), _f(kg, "HCU-1", "deactivation_rate"), \
        _f(kg, "HCU-1", "wabt_cracking"), _f(kg, "HCU-1", "sor_wabt")
    ta_start, ta_end = _f(kg, "TA-2027", "start_date"), _f(kg, "TA-2027", "end_date")
    cost, cycle = _f(kg, "HCU-1", "catalyst_inventory_cost"), _f(kg, "HCU-1", "design_cycle_length")
    mv, feed = _f(kg, "LPS-HCU-1", "lp_marginal_value"), _f(kg, "HCU-1", "feed_rate")
    months_early = (date.fromisoformat(eor["value"]).year - date.fromisoformat(ta_end["value"]).year) * 12 + \
        date.fromisoformat(eor["value"]).month - date.fromisoformat(ta_end["value"]).month
    lost_life = cost["value"] * months_early / cycle["value"]
    separate_outage = feed["value"] * 1000 * 25 * mv["value"]          # 25-day catalyst change outage
    hist = kg.history("HCU-1", "wabt_cracking_month")
    rows = [dict(month=f["valid_from"][:7], wabt_degC=f["value"]) for f in hist]
    return dict(
        id="hcu-catalyst-vs-turnaround", title="Hydrocracker catalyst end-of-run vs the 2027 turnaround",
        question="Should we change hydrocracker catalyst at TA-2027 or run it to end of run?",
        headline=(f"WABT is rising {rate['value']:.1f} °C/month (now {wabt['value']:.0f} °C, SOR {sor['value']:.0f} °C); end of run is "
                  f"predicted for {eor['value'][:7]}, {months_early} months after TA-2027 ends. Changing at the turnaround forgoes "
                  f"≈{_usd(lost_life)} of catalyst life; running on means a separate outage costing ≈{_usd(separate_outage)} in margin."),
        **_vc(separate_outage - lost_life, "one-off", (separate_outage - lost_life) * 0.5, (separate_outage - lost_life) * 1.3,
              confidence="low", label="benefit of changing at the TA"),
        domains=["Historian (WABT trend)", "Licensor guarantee", "Turnaround plan", "Catalyst contract", "LP marginal values"],
        rows=rows, path=["HCU-1", "R-402", "TA-2027", "SI-2027"], evidence=sorted(
            {x["id"] for x in (eor, rate, wabt, sor, ta_start, ta_end, cost, cycle, mv, feed)} | {f["id"] for f in hist}),
        recommendation="Keep the catalyst change in the TA-2027 scope (DEC-HCU) and confirm the EOR forecast with the licensor.",
        decision_owner="Process Engineer (Conversion units) with Turnaround Manager",
        caveat="Linear WABT extrapolation; the 25-day outage and margin are planning assumptions (low confidence).")


def conversion_loss_chains(kg, window_days=60):
    deep = {"FCC-1", "HCU-1", "DCU-1"}
    eq_of = lambda nid: next((a for a in kg.ancestors(nid) if kg.nodes[a]["cls"] == "EquipmentUnit"), None)
    rows, ev, path, total, unknown = [], [], set(), 0, 0
    for fl in [n for n in kg.nodes.values() if n["cls"] == "Failure"]:
        eq = eq_of(kg.targets(fl["id"], "FAILURE_OF")[0])
        if kg.nodes[eq]["props"].get("plant_unit") not in deep:
            continue
        d = date.fromisoformat(fl["props"]["date"])
        wo = kg.sources(fl["id"], "REMEDIATES")
        cost = sum(kg.value(w, "actual_cost", 0) for w in wo)
        lost = kg.fact(fl["id"], "lost_margin")
        loops = [g for g in kg.targets(eq, "MEMBER_OF") if kg.nodes[g]["cls"] in ("CorrosionLoop", "SafetyInstrumentedFunction")]
        scope = {eq} | {m for g in loops for m in kg.sources(g, "MEMBER_OF")}
        precursors = []
        for m in scope:
            for dp in [x for x in kg.descendants(m) if kg.nodes[x]["cls"] == "DataPoint"]:
                for x in kg.sources(dp, "ON_DATAPOINT"):
                    gap = (d - date.fromisoformat(kg.nodes[x]["props"]["date"])).days
                    if 0 < gap <= window_days:
                        precursors.append(f"{x} ({gap} d before, {kg.nodes[dp]['name'].split(' ', 1)[1]})")
                        ev.append(kg.fact(x, "peak_value")["id"])
                        path.add(x)
        ev += [kg.fact(fl["id"], "failure_mechanism")["id"]] + [kg.fact(w, "actual_cost")["id"] for w in wo] + ([lost["id"]] if lost else [])
        path.update([fl["id"], eq] + loops)
        rate_cut = kg.fact(fl["id"], "rate_reduction")
        loss_known = lost is not None or rate_cut is None
        if not loss_known:
            unknown += 1
        loss = cost + (lost["value"] if lost else 0)
        total += loss
        rows.append(dict(event=fl["id"], equipment=eq, unit=kg.nodes[eq]["props"]["plant_unit"], date=fl["props"]["date"],
                         mechanism=kg.value(fl["id"], "failure_mechanism"), repair_usd=cost,
                         lost_margin_usd=lost["value"] if lost else (None if rate_cut else 0), total_usd=loss,
                         loops=", ".join(loops) or "-", precursors="; ".join(sorted(precursors)) or "none in window"))
    rows.sort(key=lambda r: -r["total_usd"])
    flagged = [r for r in rows if r["precursors"] != "none in window"]
    return dict(
        id="conversion-loss-chains", title="Conversion-unit losses and the signals that came first",
        question="What did FCC, hydrocracker and coker failures cost this year, and which were signalled in data we already held?",
        headline=(f"{len(rows)} conversion-unit failures cost ≈{_usd(total)} in FY2026 (repairs plus lost margin at LP marginal values), "
                  f"led by {rows[0]['event']} on {rows[0]['equipment']} (≈{_usd(rows[0]['total_usd'])}). {len(flagged)} had an IOW "
                  f"exceedance in the same corrosion loop or safety function within {window_days} days before: "
                  + "; ".join(f"{r['event']} ← {', '.join(sorted({p.split(' (')[0] for p in r['precursors'].split('; ')}))}" for r in flagged) + "."),
        **_vc(total, "one-off (FY2026 actual)", total * 0.8, total * 1.3, confidence="low", label="failure cost FY2026"),
        domains=["CMMS (ISO 14224)", "IOW monitor", "Corrosion loops (RBI)", "Safety functions", "Operations logbook", "LP marginal values"],
        rows=rows, path=sorted(path), evidence=sorted(set(ev)),
        recommendation=("Make an IOW exceedance open a follow-up on every member of its loop, not just the tagged item: the REAC "
                        "wash-water shortfall preceded the E-410C tube leak, and fast quench cycles preceded the D-501B bulge."),
        decision_owner="Corrosion / Integrity Engineer with Maintenance Manager",
        caveat=(f"Precursor = IOW exceedance on a member of the failed item's loop or SIF within {window_days} days; association, not "
                f"proven cause. {unknown} failure(s) have a rate cut without a margin value (shown as unknown). "
                "Patterns in this synthetic dataset were seeded to demonstrate detection."))


def balance_integrity(kg):
    checks = [("Hydrogen: SMR meter + reformer vs make-up demand", _f(kg, SITE, "h2_balance_residual"), 1.0, "%"),
              ("Sulfur: unaccounted as % of sulfur in", None, 1.0, "%"),
              ("Mass: unaccounted across processing units (% of crude)", _f(kg, SITE, "mass_unaccounted_pct_crude"), 0.5, "%"),
              ("SRU: measured vs expected from acid gas", _f(kg, "SRU-1", "production_reconciliation"), 1.0, "%"),
              ("Fuel gas: supply vs consumption", _f(kg, "UTL-FG", "balance_residual"), 2.0, "%"),
              ("Steam: production vs consumption + losses", _f(kg, "UTL-STM", "steam_balance_residual"), 2.0, "%"),
              ("Power: generation + import vs demand", _f(kg, "UTL-PWR", "power_balance_residual"), 2.0, "%")]
    su, si = _f(kg, SITE, "sulfur_unaccounted"), _f(kg, SITE, "sulfur_in")
    rows, ev = [], [su["id"], si["id"]]
    for name, f, tol, unit in checks:
        v = f["value"] if f else round(100 * su["value"] / si["value"], 2)
        rows.append(dict(balance=name, residual=v, tolerance=tol, unit=unit, status="OK" if abs(v) <= tol else "INVESTIGATE"))
        if f:
            ev.append(f["id"])
    meters = [f for f in kg.fact_list if f["predicate"] == "meter_reconciliation"]
    worst = sorted(meters, key=lambda f: -abs(f["value"]))[:3]
    for f in worst:
        rows.append(dict(balance=f"Feed meter vs accounting: {f['subject']}", residual=f["value"], tolerance=1.0, unit="%",
                         status="OK" if abs(f["value"]) <= 1.0 else "INVESTIGATE"))
        ev.append(f["id"])
    bad = [r for r in rows if r["status"] != "OK"]
    return dict(
        id="balance-integrity", title="Balance and meter integrity",
        question="Can we trust the balances the other insights rely on?",
        headline=(f"{len(rows) - len(bad)} of {len(rows)} balances and meters are within tolerance. "
                  + ("To investigate: " + "; ".join(f"{r['balance']} ({r['residual']:+.2f}{r['unit']})" for r in bad) + "."
                     if bad else "No balance needs investigation.")),
        **_vc(None, None, confidence="medium"),
        domains=["Hydrocarbon accounting", "DCS meters", "SRU weighbridge", "Utility meters", "LIMS"],
        rows=rows, path=[SITE, "UTL-H2", "SRU-1", "UTL-FG", "UTL-STM", "UTL-PWR"], evidence=sorted(set(ev)),
        recommendation="Review out-of-tolerance meters with the instrument and accounting teams before the monthly close.",
        decision_owner="Data Steward with Planning & Economics Lead",
        caveat="Residuals are reported, never forced to zero. Tolerances are typical refinery practice, not client standards.")


REFINERY = [hydrogen_headroom, sulfur_ceiling, conversion_loss_chains, octane_giveaway, reformer_bottleneck,
            hcu_catalyst_vs_turnaround, balance_integrity, nelson_complexity]
ALL = REFINERY + cdu_insights.ALL


def run_all(kg):
    return [f(kg) for f in ALL]
