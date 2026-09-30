"""
Insights for the Refinery Gamma CDU model. Same contract as ogkg/insights.py:
id, title, question, headline, value_usd, domains, rows, path, evidence, recommendation, decision_owner, caveat.
"""
from collections import Counter, defaultdict

CO2_KG_PER_MMBTU = 53.06   # natural-gas factor; refinery fuel gas differs (indicative)


def _usd(x):
    return f"${x/1e6:,.1f}M" if abs(x) >= 1e6 else f"${x/1e3:,.0f}k"


def preheat_energy_penalty(kg):
    """Physics-based attribution: the fouling penalty is the extra heater duty needed to make up Train B's lower
    heater inlet temperature (m * cp * dCIT / efficiency), not the whole energy-intensity gap between trains."""
    A, B = "CDU-A", "CDU-B"
    f = lambda u, k: kg.fact(u, k)
    ev, rows = [], []
    for u in (A, B):
        facts = [f(u, k) for k in ("throughput_fy2026", "cit_fy2026", "heater_fired_duty", "energy_intensity")]
        ev += [x["id"] for x in facts]
        rows.append(dict(train=u[-1], throughput_kbd=facts[0]["value"], cit_degC=facts[1]["value"],
                         fired_duty_MW=facts[2]["value"], energy_intensity_MMBtu_per_kbbl=facts[3]["value"]))
    price, cp, rho = kg.fact("SITE-GAMMA", "fuel_price"), kg.fact("SITE-GAMMA", "crude_heat_capacity"), kg.fact("SITE-GAMMA", "crude_density")
    ef = kg.fact("SITE-GAMMA", "emission_factor_fuel")
    co2p = kg.fact("PR-ACT26-CO2", "price")
    eff_b = next(kg.fact(d, "latest_value") for d in kg.descendants("H-201") if "Thermal efficiency" in kg.nodes[d]["name"])
    ev += [x["id"] for x in (price, cp, rho, ef, eff_b) + ((co2p,) if co2p else ())]
    cit_gap = rows[0]["cit_degC"] - rows[1]["cit_degC"]
    m_kg_s = rows[1]["throughput_kbd"] * 1000 * 0.158987 * rho["value"] * 1000 / 86400
    absorbed_mw = m_kg_s * cp["value"] * cit_gap / 1000
    fired_mw = absorbed_mw / (eff_b["value"] / 100)
    mmbtu_yr = fired_mw * 3.412 * 8760
    usd_yr = mmbtu_yr * price["value"]
    co2_kt = mmbtu_yr * ef["value"] / 1e6
    carbon = co2_kt * 1000 * (co2p["value"] if co2p else 0)
    total_gap_mw = rows[1]["fired_duty_MW"] - rows[0]["fired_duty_MW"]
    ex_rows, path = [], {A, B, "H-101", "H-201"}
    for nA in ("07", "08", "09", "10", "11", "12"):
        ea, eb = f"E-1{nA}", f"E-2{nA}"
        rf = lambda e: next(kg.fact(d, "latest_value") for d in kg.descendants(e)
                            if kg.nodes[d]["cls"] == "DataPoint" and "Fouling resistance" in kg.nodes[d]["name"])
        fa, fb = rf(ea), rf(eb)
        ev += [fa["id"], fb["id"]]
        cleaned = [w for w in kg.sources(eb, "PERFORMED_ON")]
        ex_rows.append(dict(exchanger=f"{ea} / {eb}", rf_train_A=fa["value"], rf_train_B=fb["value"],
                            cleaned_fy2026=", ".join(cleaned) or "no"))
        if fb["value"] >= 0.5:
            path.add(eb)
    worst = [r["exchanger"].split(" / ")[1] for r in ex_rows if r["rf_train_B"] >= 0.5]
    return dict(
        id="preheat-energy-penalty",
        title="Train B preheat fouling energy penalty",
        question="What is Train B's hot-preheat fouling costing us, and which exchangers should be cleaned?",
        headline=(f"Train B runs {cit_gap:.0f} °C colder into the heater (CIT {rows[1]['cit_degC']:.0f} vs {rows[0]['cit_degC']:.0f} °C). "
                  f"Making that up takes {fired_mw:.1f} MW of extra firing: ≈{_usd(usd_yr)}/yr fuel and ≈{co2_kt:,.0f} kt CO2/yr"
                  + (f" (≈{_usd(carbon)}/yr more if CO2 is priced)" if carbon else "") +
                  f". Fouled exchangers: {', '.join(worst)}."),
        value_usd=round(usd_yr), value_label="fuel per year", value_basis="recurring-annual",
        value_low=round(usd_yr * 0.7), value_high=round(usd_yr * 1.3 + carbon), capex_required=None, confidence="low",
        domains=["Historian", "Heater performance", "Exchanger monitoring", "Maintenance (CMMS)", "Planning economics", "Emissions"],
        rows=rows + ex_rows, path=sorted(path), evidence=sorted(set(ev)),
        recommendation=(f"Schedule hydro-jet cleaning of {', '.join(worst)} at the next window; E-207/E-208 were cleaned in March and "
                        f"are recovering. Of the {total_gap_mw:.1f} MW fired-duty gap between trains, fouling explains {fired_mw:.1f} MW; "
                        "check Train B heater efficiency and O2 for the rest."),
        decision_owner="Energy Engineer (DEC-CLEAN) with Operations Superintendent",
        caveat=("Fuel price is a planning assumption (low confidence). Crude heat capacity and density are typical assay values. "
                "CO2 uses a natural-gas emission factor as a proxy for refinery fuel gas."),
    )


def overhead_corrosion_exposure(kg):
    rows, ev, path = [], [], set()
    summary = {}
    for tr in ("A", "B"):
        loop = f"CL-{tr}-OVH"
        members = kg.sources(loop, "MEMBER_OF")
        exc_n, fail_n = 0, 0
        for m in members:
            dps = [d for d in kg.descendants(m) if kg.nodes[d]["cls"] == "DataPoint"]
            exc = [x for d in dps for x in kg.sources(d, "ON_DATAPOINT")]
            fails = [x for x in kg.rollup(m) if "Corrosion" in kg.value(x["id"], "failure_mechanism", "")]
            corr = [kg.fact(d, "latest_value") for d in dps if "Corrosion probe" in kg.nodes[d]["name"]]
            met = kg.fact(m, "tube_metallurgy") or kg.fact(m, "material") or kg.fact(m, "shell_material")
            score = 3 * len(fails) + 2 * len(exc) + (1 if met and met["value"] == "CarbonSteel" else 0)
            exc_n += len(exc); fail_n += len(fails)
            ev += [x["id"] for x in corr] + ([met["id"]] if met else [])
            for x in exc:
                ev += [kg.fact(x, "peak_value")["id"]]
            if tr == "A":
                rows.append(dict(equipment=m, name=kg.nodes[m]["name"], metallurgy=met["value"] if met else "per datasheet",
                                 failures=len(fails), iow_exceedances=len(exc),
                                 corrosion_rate_mm_y=corr[0]["value"] if corr else None, exposure_score=score))
                if score >= 2:
                    path.add(m)
        summary[tr] = (exc_n, fail_n)
    # the loop's analyser exceedances belong to the receiver and the overhead line
    rows.sort(key=lambda r: -r["exposure_score"])
    cr = {tr: kg.value(next(d for d in kg.descendants(f"PC-{t}02") if "Corrosion probe" in kg.nodes[d]["name"]), "latest_value")
          for tr, t in (("A", 1), ("B", 2))}
    path.update(["CL-A-OVH", "V-102", "PC-102"])
    return dict(
        id="overhead-corrosion-exposure",
        title="Train A overhead corrosion exposure",
        question="Which Train A overhead equipment is most exposed, and how does it compare with Train B?",
        headline=(f"Train A's overhead loop had {summary['A'][0]} IOW exceedances and {summary['A'][1]} corrosion failure (E-120A tubes) "
                  f"against {summary['B'][0]} and {summary['B'][1]} on Train B; corrosion rate {cr['A']} vs {cr['B']} mm/y. "
                  "E-120B shares E-120A's carbon-steel tubes and service."),
        value_usd=None, value_basis=None, value_low=None, value_high=None, capex_required=None, confidence="medium",
        domains=["LIMS", "Historian / IOW monitor", "Corrosion monitoring", "RBI / inspection", "CMMS", "Asset hierarchy"],
        rows=rows, path=sorted(path), evidence=sorted(set(ev)),
        recommendation=("Inspect E-120B tubes and the PC-102 overhead line at the next opportunity; restore dew-point margin above 14 °C "
                        "by raising wash-water rate; review neutraliser rate (Train A 45 L/h vs Train B 38 L/h at twice the chloride)."),
        decision_owner="Corrosion / Integrity Engineer (DEC-NEUT)",
        caveat="Exposure score is a triage aid (failure 3, exceedance 2, carbon steel 1), not an RBI result.",
    )


def model_completeness(kg):
    eq = [n for n in kg.nodes.values() if n["cls"] == "EquipmentUnit"]
    by = defaultdict(list)
    for n in eq:
        by[n["props"]["eq_class"]].append(n)
    rows, gaps = [], []
    for cls, items in sorted(by.items()):
        dec = sum(1 for n in items if any(kg.nodes[c]["cls"] == "Subunit" for c in kg.children(n["id"])))
        des = sum(1 for n in items if len([f for f in kg.facts(n["id"]) if f["method"] == "declared"]) >= 3)
        tags = [d for n in items for d in kg.descendants(n["id"]) if kg.nodes[d]["cls"] == "DataPoint"]
        tag_ok = sum(1 for t in tags if kg.fact(t, "engineering_unit") and kg.fact(t, "latest_value"))
        per_train = Counter(n["props"].get("train") or "Common" for n in items)
        units = Counter(n["props"].get("plant_unit") for n in items if not n["props"].get("train"))
        rows.append(dict(equipment_class=cls, items=len(items), train_A=per_train.get("A", 0), train_B=per_train.get("B", 0),
                         other_units=", ".join(f"{u} {c}" for u, c in sorted(units.items())) or "-",
                         decomposed_pct=round(100 * dec / len(items)),
                         design_data_pct=round(100 * des / len(items)), tags=len(tags),
                         tags_complete_pct=round(100 * tag_ok / len(tags)) if tags else 100))
        if dec < len(items) or des < len(items) or tag_ok < len(tags):
            gaps.append(cls)
    total_tags = sum(r["tags"] for r in rows)
    other_tags = sum(1 for n in kg.nodes.values() if n["cls"] == "DataPoint") - total_tags
    sym = all(r["train_A"] == r["train_B"] for r in rows if r["train_A"] or r["train_B"])
    return dict(
        id="model-completeness",
        title="Model completeness scorecard",
        question="Is every full-depth equipment item modelled from L6 down to L10, and are the CDU trains symmetric?",
        headline=(f"{len(eq)} equipment items with {total_tags} equipment tags (+{other_tags} unit-level and lab tags) across the two CDU "
                  f"trains, CDU common facilities, crude tank farm and the three full-depth conversion units (FCC-1, HCU-1, DCU-1), "
                  f"including drivers, relief valves, SIF devices, control valves and substations. "
                  f"{'All' if not gaps else 'Not all'} classes are fully decomposed with design data and tag values; "
                  f"the two trains are {'symmetric' if sym else 'NOT symmetric'}."),
        value_usd=None, value_basis=None, value_low=None, value_high=None, capex_required=None, confidence="high",
        domains=["Asset hierarchy (L0–L10)", "Equipment datasheets", "Tag configuration", "Historian / LIMS"],
        rows=rows, path=["SITE-GAMMA", "CDU-A", "CDU-B", "CDU-COM", "TF-1", "FCC-1", "HCU-1", "DCU-1"], evidence=[],
        recommendation="Use this scorecard as the acceptance gate when a real site's data replaces the synthetic model.",
        decision_owner="Ontology lead with data owners",
        caveat="Completeness is structural; it does not check that values are correct.",
    )


ALL = [preheat_energy_penalty, overhead_corrosion_exposure, model_completeness]


def run_all(kg):
    return [f(kg) for f in ALL]
