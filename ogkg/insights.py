"""
Discovery insights: questions that need several domains joined at once. In a siloed
landscape each one needs weeks of spreadsheet work. Here each one is a graph traversal.

Every insight returns the same contract:
  id, title, question, headline, value_usd, domains, rows, path (node ids),
  evidence (fact ids), recommendation, decision_owner, caveat
"""
from datetime import date, timedelta

OBS_DAYS = 365
ATTRIBUTION_DAYS = 30


def _d(s):
    return date.fromisoformat(s)


def _usd(x):
    sign = "-" if x < 0 else ""
    x = abs(x)
    return f"{sign}${x/1e6:,.2f}M" if x >= 1e6 else f"{sign}${x/1e3:,.0f}k"


# ---------------------------------------------------------------------------- 1
def true_crude_value(kg):
    """LP-reported uplift of opportunity crudes vs. the asset consequences they caused."""
    windows = {}
    for n in kg.nodes.values():
        if n["cls"] == "CrudeCampaign" and n["props"].get("opportunity"):
            unit = kg.targets(n["id"], "PROCESSED_IN")[0]
            key = (unit, n["props"]["start"], n["props"]["end"])
            windows.setdefault(key, []).append(n["id"])

    rows, evidence, path = [], [], set()
    tot_up = tot_cost = 0
    for (unit, st, en), camps in sorted(windows.items(), key=lambda k: k[0][1]):
        # affected units = processing unit + units fed by its streams (one hop downstream)
        affected = {unit}
        for s in kg.targets(unit, "PRODUCES"):
            affected.update(kg.targets(s, "FEEDS"))
        scope = set()
        for u in affected:
            scope.update(kg.descendants(u))
        lo, hi = _d(st), _d(en) + timedelta(days=ATTRIBUTION_DAYS)

        uplift = treat = 0
        grades = []
        for c in camps:
            f = kg.fact(c, "lp_uplift_total"); uplift += f["value"]; evidence.append(f["id"])
            t = kg.fact(c, "incremental_treatment_cost")
            if t:
                treat += t["value"]; evidence.append(t["id"])
            g = kg.targets(c, "OF_GRADE")[0]
            grades.append(kg.nodes[g]["name"]); path.update([c, g, unit])

        exc = [e for e in kg.nodes.values() if e["cls"] == "IOWExceedance"
               and kg.targets(e["id"], "ON_DATAPOINT")[0] in scope and lo <= _d(e["props"]["date"]) <= hi]
        fails = [e for e in kg.nodes.values() if e["cls"] == "Failure"
                 and kg.targets(e["id"], "FAILURE_OF")[0] in scope and lo <= _d(e["props"]["date"]) <= hi
                 and "Corrosion" in kg.value(e["id"], "failure_mechanism", "")]
        repair = lost = 0
        for fl in fails:
            path.add(fl["id"]); path.add(kg.targets(fl["id"], "FAILURE_OF")[0])
            for wo in kg.sources(fl["id"], "REMEDIATES"):
                f = kg.fact(wo, "actual_cost"); repair += f["value"]; evidence.append(f["id"])
            lm = kg.fact(fl["id"], "lost_margin")
            if lm:
                lost += lm["value"]; evidence.append(lm["id"])
        for e in exc:
            path.add(e["id"]); evidence.extend(f["id"] for f in kg.facts(e["id"]))
        cost = repair + lost + treat
        tot_up += uplift; tot_cost += cost
        rows.append(dict(window=f"{st} → {en}", unit=unit, grades=" + ".join(grades),
                         lp_uplift_usd=uplift, iow_exceedances=len(exc), corrosion_failures=len(fails),
                         failures=[f"{kg.nodes[f['id']]['name']}" for f in fails],
                         repair_usd=repair, lost_margin_usd=lost, treatment_usd=treat,
                         net_usd=uplift - cost))
    net = tot_up - tot_cost
    return dict(
        id="true-crude-value",
        title="True value of opportunity crudes",
        question="Did the discounted crudes we bought actually make money once asset consequences are counted?",
        headline=(f"LP booked {_usd(tot_up)} uplift from opportunity crudes at CDU-1; after corrosion repairs, "
                  f"lost throughput and treatment ({_usd(tot_cost)}), the net is {_usd(net)}."),
        value_usd=net,
        domains=["Trading / CTRM", "LP planning", "Crude assay", "IOW / integrity", "Maintenance (SAP PM)", "Operations", "Economics"],
        rows=rows, path=sorted(path), evidence=sorted(set(evidence)),
        recommendation=("Feed a reliability-cost term (corrosion $/bbl by crude contaminant) into the crude buy decision; "
                        "cap HSOB at ≤15% of slate until desalter / overhead wash-water upgrade; confirm by RCA."),
        decision_owner="Crude & Planning Manager with Corrosion / Integrity Engineer",
        caveat=(f"Attribution is temporal + topological (events within {ATTRIBUTION_DAYS} days on units the crude "
                "reached, corrosion mechanism only). Treat as a hypothesis for RCA, not proof of causation."),
    )


# ---------------------------------------------------------------------------- 2
def fleet_bad_actors(kg):
    pumps = [n for n in kg.nodes.values() if n["cls"] == "EquipmentUnit" and n["props"].get("eq_class") == "Pump"
             and kg.fact(n["id"], "model")]
    groups, evidence, path = {}, [], set()
    for p in pumps:
        model = kg.value(p["id"], "model"); temp = kg.value(p["id"], "service_temperature")
        band = "hot (≥340 °C)" if temp >= 340 else "moderate (<340 °C)"
        site = next(a for a in kg.ancestors(p["id"]) if kg.nodes[a]["cls"] == "Installation")
        fails = kg.rollup(p["id"])
        cost = 0
        for fl in fails:
            for wo in kg.sources(fl["id"], "REMEDIATES"):
                f = kg.fact(wo, "actual_cost"); cost += f["value"]; evidence.append(f["id"])
        evidence += [kg.fact(p["id"], k)["id"] for k in ("model", "service_temperature", "seal_plan")]
        g = groups.setdefault((model, band), dict(model=model, service=band, pumps=[], sites=set(),
                                                  failures=0, cost_usd=0, seal_plan=kg.value(p["id"], "seal_plan")))
        g["pumps"].append(p["id"]); g["sites"].add(kg.nodes[site]["name"])
        g["failures"] += len(fails); g["cost_usd"] += cost
        if fails:
            path.update([p["id"], site])
    rows = []
    for g in groups.values():
        pump_days = len(g["pumps"]) * OBS_DAYS
        g["mtbf_days"] = round(pump_days / g["failures"]) if g["failures"] else None
        g["sites"] = sorted(g["sites"])
        rows.append(g)
    rows.sort(key=lambda r: -r["failures"])
    worst = rows[0]
    return dict(
        id="fleet-bad-actors",
        title="Cross-site bad actor: model × service condition",
        question="Is the seal problem a site problem, a pump problem, or a service-condition problem?",
        headline=(f"{worst['model']} in {worst['service']} service failed {worst['failures']} times across "
                  f"{len(worst['sites'])} sites (MTBF ≈ {worst['mtbf_days']} days, {_usd(worst['cost_usd'])} repairs). "
                  f"Same model in moderate service: no failures. A different model in the same hot service: 365-day MTBF."),
        value_usd=worst["cost_usd"],
        domains=["Asset register", "Process datasheets", "Maintenance (SAP PM)", "ISO 14224 failure coding", "Two sites"],
        rows=rows, path=sorted(path), evidence=sorted(set(evidence)),
        recommendation=("Fleet standard: hot-service (≥340 °C) pumps move to API 682 dual-seal plan (as on P-401B); "
                        "raise one fleet-level MOC instead of site-by-site RCAs."),
        decision_owner="Reliability Engineer (fleet) — equipment standard decision (DEC-STD)",
        caveat="Small sample (12 months, 6 pumps). Validate with OEM and extend observation window.",
    )


# ---------------------------------------------------------------------------- 3
def giveaway_root_cause(kg):
    prods = [n for n in kg.nodes.values() if n["cls"] == "Product" and kg.fact(n["id"], "ron_spec_min")]
    octane = kg.fact("PRD-GAS-1", "octane_value")
    base = []
    for p in prods:
        spec = kg.fact(p["id"], "ron_spec_min"); avg = kg.fact(p["id"], "ron_avg_12m"); rate = kg.fact(p["id"], "production_rate")
        base.append((p, spec, avg, rate, avg["value"] - spec["value"]))
    best = min(b[4] for b in base)
    rows, evidence, path = [], [octane["id"]], set()
    total = 0
    for p, spec, avg, rate, gw in base:
        excess = gw - best
        cost = excess * octane["value"] * rate["value"] * 1000 * OBS_DAYS
        total += cost
        evidence += [spec["id"], avg["id"], rate["id"]]
        signals = []
        for comp in kg.sources(p["id"], "COMPONENT_OF"):
            for unit in kg.sources(comp, "PRODUCES"):
                for d in kg.descendants(unit):
                    for f in kg.facts(d):
                        if f["predicate"].endswith("_std_dev_12m") or f["predicate"] == "fouling_resistance_trend":
                            signals.append(f"{kg.nodes[d]['name']}: {f['predicate']} = {f['value']} {f['unit']}".strip())
                            evidence.append(f["id"])
                            if excess > 0:
                                path.update([p["id"], comp, unit, d])
                    # process-side: is the data feeding the recipe decision fresh enough?
                    for de in kg.sources(d, "INSTANTIATED_BY"):
                        sla = kg.fact(de, "freshness_sla"); si = kg.fact(d, "sampling_interval")
                        if sla and si:
                            evidence += [sla["id"], si["id"]]
                            ok = si["value"] <= sla["value"]
                            signals.append(f"{kg.nodes[de]['name']} sampled every {si['value']} h vs SLA {sla['value']} h"
                                           + ("" if ok else " — STALE input to recipe decision"))
                            if not ok:
                                path.update([de, d, "DEC-RECIPE"])
        rows.append(dict(product=p["name"], ron_avg=avg["value"], spec=spec["value"], giveaway=round(gw, 2),
                         excess_vs_best=round(excess, 2), annual_cost_usd=round(cost), signals=signals))
    worst = max(rows, key=lambda r: r["annual_cost_usd"])
    return dict(
        id="giveaway-root-cause",
        title="Octane giveaway traced to asset and process causes",
        question="Why does one blender give away more octane than its peer, and what is it worth?",
        headline=(f"{worst['product']} gives away {worst['giveaway']} RON vs {min(r['giveaway'] for r in rows)} at the peer site — "
                  f"≈{_usd(worst['annual_cost_usd'])}/yr. Trace: reformer feed/effluent exchanger fouling → reactor temperature "
                  f"swings → volatile reformate RON, sampled 3× less often than the recipe needs."),
        value_usd=total,
        domains=["LIMS", "Historian", "Blending", "Reformer operations", "Data governance", "Planning economics"],
        rows=rows, path=sorted(path), evidence=sorted(set(evidence)),
        recommendation=("Raise reformate RON sampling to 8 h (or install online analyser) and schedule E-301 cleaning; "
                        "recipe to use real-time component quality."),
        decision_owner="Blending Planner with Process Engineer; Laboratory Manager for sampling frequency",
        caveat="Octane value ($/RON-bbl) is a planning assumption (low confidence) — replace with the site's LP marginal value.",
    )


# ---------------------------------------------------------------------------- 4
def ta_scope_gaps(kg):
    out = []
    for ta in [n for n in kg.nodes.values() if n["cls"] == "Turnaround"]:
        site = kg.targets(ta["id"], "AT_SITE")[0]
        scoped = {kg.targets(si, "TARGETS")[0] for si in kg.sources(ta["id"], "IN_SCOPE_OF")}
        equipment = [n for n in kg.descendants(site) if kg.nodes[n]["level"] == 6]
        rows, evidence, path = [], [], {ta["id"]}
        for eqid in equipment:
            ev, score = [], 0
            for fl in kg.rollup(eqid):
                if "Corrosion" in kg.value(fl["id"], "failure_mechanism", ""):
                    ev.append(f"corrosion failure {fl['props']['date']}"); score += 3
                    evidence.append(kg.fact(fl["id"], "failure_mechanism")["id"])
            for dp in [d for d in kg.descendants(eqid) if kg.nodes[d]["cls"] == "DataPoint"]:
                for x in kg.sources(dp, "ON_DATAPOINT"):
                    ev.append(f"direct IOW exceedance {x}"); score += 2
                    evidence.append(kg.fact(x, "peak_value")["id"])
            section = kg.parent(eqid)
            for dp in [c for c in kg.children(section) if kg.nodes[c]["cls"] == "DataPoint"]:
                for x in kg.sources(dp, "ON_DATAPOINT"):
                    ev.append(f"section IOW exceedance {x}"); score += 1
                    evidence.append(kg.fact(x, "peak_value")["id"])
            if ev:
                in_scope = eqid in scoped
                rows.append(dict(equipment=kg.nodes[eqid]["name"], id=eqid, section=kg.nodes[section]["name"],
                                 evidence=ev, risk_score=score, in_scope=in_scope))
                if not in_scope:
                    path.update([eqid, section])
        rows.sort(key=lambda r: (r["in_scope"], -r["risk_score"]))
        gaps = [r for r in rows if not r["in_scope"]]
        freeze = kg.fact(ta["id"], "scope_freeze_date")
        evidence.append(freeze["id"])
        out.append(dict(
            id="ta-scope-gaps",
            title="Turnaround scope vs live integrity threats",
            question="Is equipment that is actively corroding missing from the turnaround scope before it freezes?",
            headline=(f"{len(gaps)} of {len(rows)} equipment items with active integrity evidence are NOT in "
                      f"{ta['name']} scope; highest risk: {', '.join(g['equipment'].split(' ')[0] for g in gaps[:3])}. "
                      f"Scope freezes {freeze['value']}."),
            value_usd=None,
            domains=["TA planning", "IOW monitoring", "Maintenance history", "Asset hierarchy"],
            rows=rows, path=sorted(path), evidence=sorted(set(evidence)),
            recommendation="Add E-101B and PC-101 inspection; add PC-201 UT survey; review P-103 at scope challenge.",
            decision_owner="Turnaround Manager (DEC-SCOPEFRZ) with Corrosion / Integrity Engineer",
            caveat="Scoring is evidence-weighted (failure 3, direct IOW 2, section IOW 1) — a triage aid, not an RBI result.",
        ))
    return out[0]


# ---------------------------------------------------------------------------- 5
def decision_blind_spots(kg):
    rows, evidence, path = [], [], set()
    for dec in [n for n in kg.nodes.values() if n["cls"] == "DecisionPoint"]:
        governed = kg.targets(dec["id"], "GOVERNS")
        consumed = kg.targets(dec["id"], "CONSUMES")
        domains = sorted({kg.nodes[c]["props"].get("domain") for c in consumed})
        corr_fails = []
        for g in governed:
            corr_fails += [f for f in kg.rollup(g) if "Corrosion" in kg.value(f["id"], "failure_mechanism", "")]
        cost = sum(kg.value(f["id"], "lost_margin", 0) for f in corr_fails)
        cost += sum(kg.value(wo, "actual_cost", 0) for f in corr_fails for wo in kg.sources(f["id"], "REMEDIATES"))
        issues = []
        if corr_fails and not ({"reliability", "integrity"} & set(domains)):
            issues.append(f"governs assets with {len(corr_fails)} corrosion failures ({_usd(cost)}) "
                          f"but consumes no reliability/integrity data")
            path.update([dec["id"], "DE-CORRCOST"] + governed)
            evidence += [kg.fact(f["id"], "failure_mechanism")["id"] for f in corr_fails]
        for c in consumed:
            sla = kg.fact(c, "freshness_sla")
            for t in kg.targets(c, "INSTANTIATED_BY"):
                si = kg.fact(t, "sampling_interval")
                if sla and si and si["value"] > sla["value"]:
                    issues.append(f"input '{kg.nodes[c]['name']}' from {kg.nodes[t]['name']} ({kg.nodes[kg.ancestors(t)[3]]['name'] if len(kg.ancestors(t))>3 else ''}) "
                                  f"is {si['value']} h old vs {sla['value']} h SLA")
                    evidence += [sla["id"], si["id"]]; path.update([dec["id"], c, t])
            if not kg.targets(c, "INSTANTIATED_BY") and not kg.nodes[c]["props"].get("maps_to_predicate"):
                issues.append(f"input '{kg.nodes[c]['name']}' has no system of record in the graph")
                path.update([dec["id"], c])
        rows.append(dict(decision=dec["name"], id=dec["id"], owner_process=kg.nodes[kg.ancestors(dec["id"])[4]]["name"],
                         consumes_domains=domains, issues=issues, healthy=not issues))
    rows.sort(key=lambda r: r["healthy"])
    flagged = [r for r in rows if not r["healthy"]]
    return dict(
        id="decision-blind-spots",
        title="Decision blind spots across the process ↔ asset boundary",
        question="Which business decisions are made without data the organisation already has?",
        headline=(f"{len(flagged)} of {len(rows)} decision points have a blind spot. The crude buy and crude acceptance decisions "
                  f"never see the corrosion cost their crudes create — the data exists (DE-CORRCOST) but only feeds the corrosion budget."),
        value_usd=None,
        domains=["Process model (L2–L10)", "Asset model (L2–L10)", "Data governance catalogue"],
        rows=rows, path=sorted(path), evidence=sorted(set(evidence)),
        recommendation=("Wire DE-CORRCOST into DEC-CRBUY and DEC-CRACC (crude $/bbl reliability penalty); "
                        "fix reformate RON freshness; give TA scope inclusion a system of record."),
        decision_owner="Process owners of each decision point; sponsor: Refinery Manager",
        caveat="Decision inputs reflect the process model as documented; validate with process owners in workshops.",
    )


ALL = [true_crude_value, fleet_bad_actors, giveaway_root_cause, ta_scope_gaps, decision_blind_spots]
REGISTRY = {f.__name__: f for f in ALL}
ID_TO_FN = {}


def run_all(kg):
    res = [f(kg) for f in ALL]
    for f, r in zip(ALL, res):
        ID_TO_FN[r["id"]] = f
    return res


def run(kg, insight_id):
    for f in ALL:
        r = f(kg)
        if r["id"] == insight_id or f.__name__ == insight_id:
            return r
    raise KeyError(insight_id)
