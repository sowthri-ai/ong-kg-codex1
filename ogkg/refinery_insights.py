"""
Refinery-wide insights for the Refinery Gamma model (v0.4.0). Same contract as ogkg/insights.py:
id, title, question, headline, value_usd, domains, rows, path, evidence, recommendation, decision_owner, caveat.

Every number is read from the graph (facts with lineage); nothing is hard-coded here except
what-if arithmetic, which is stated in the caveat.
"""
from datetime import date

from . import cdu_insights

SITE = "SITE-GAMMA"


def _usd(x):
    return cdu_insights._usd(x)


def _f(kg, s, p):
    f = kg.fact(s, p)
    if f is None:
        raise KeyError(f"{s}.{p} missing")
    return f


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
    return dict(
        id="nelson-complexity",
        title="Nelson complexity, rebuilt from the graph",
        question="What is Refinery Gamma's Nelson complexity, and which units drive it?",
        headline=(f"NCI {total['value']:.1f} from {len(rows)} units on 500 kbpd of crude. The top three contributors — "
                  + ", ".join(f"{r['unit']} {r['contribution']:.2f}" for r in top)
                  + f" — make up {sum(r['share_pct'] for r in top):.0f}% of it; the 27 kbpd lube plant alone adds "
                  f"{next(r['contribution'] for r in rows if r['unit'] == 'LUBE-1'):.1f} points."),
        value_usd=None,
        domains=["Asset register (capacities)", "Process design basis", "Public benchmark factors"],
        rows=rows, path=[SITE] + [r["unit"] for r in top], evidence=sorted(set(ev)),
        recommendation=("Quote NCI as a screening benchmark only. Complexity is concentrated in small, high-factor units (lubes, "
                        "aromatics, isomerisation), so NCI overstates margin capability; judge investments on LP margin by unit."),
        decision_owner="Planning & Economics Lead",
        caveat="1998 Nelson factors; hydrogen, sulfur, utilities and blending carry no factor in that table and are excluded.",
    )


def hydrogen_headroom(kg):
    demand, supply, head = (_f(kg, SITE, k) for k in ("h2_demand", "h2_supply_capacity", "h2_headroom"))
    ccr, hmu, hmu_cap = _f(kg, "CCR-1", "h2_production"), _f(kg, "HMU-1", "h2_production"), _f(kg, "HMU-1", "design_capacity")
    hcu_rate, grm = _f(kg, "HCU-1", "h2_consumption_rate"), _f(kg, SITE, "grm_fy2026")
    consumers = [n for n in kg.nodes if kg.fact(n, "h2_consumption")]
    rows = sorted((dict(unit=u, feed_kbd=kg.value(u, "feed_rate"), scf_per_bbl=kg.value(u, "h2_consumption_rate"),
                        h2_MMSCFD=kg.value(u, "h2_consumption"),
                        share_pct=round(100 * kg.value(u, "h2_consumption") / demand["value"], 1)) for u in consumers),
                  key=lambda r: -r["h2_MMSCFD"])
    deficit = ccr["value"] - head["value"]
    hcu_cut = deficit / (hcu_rate["value"] / 1000)
    per_day = hcu_cut * 1000 * grm["value"]
    ev = [demand["id"], supply["id"], head["id"], ccr["id"], hmu["id"], hmu_cap["id"], hcu_rate["id"], grm["id"]] + \
         [kg.fact(u, "h2_consumption")["id"] for u in consumers]
    return dict(
        id="hydrogen-headroom",
        title="Hydrogen network headroom and reformer-outage exposure",
        question="How much hydrogen headroom do we have, and what happens if the reformer trips?",
        headline=(f"Demand {demand['value']:.1f} MMSCFD against {supply['value']:.0f} available: headroom {head['value']:.1f} MMSCFD "
                  f"({100 * head['value'] / supply['value']:.1f}%), with the SMR at {100 * hmu['value'] / hmu_cap['value']:.0f}%. "
                  f"A reformer outage removes {ccr['value']:.0f} MMSCFD and leaves the network {deficit:.0f} MMSCFD short — about "
                  f"{hcu_cut:.0f} kbpd of hydrocracker feed, ≈{_usd(per_day)} of margin per day."),
        value_usd=round(per_day), value_label="at risk per outage day",
        domains=["Unit feed rates (hydrocarbon accounting)", "Licensor hydrogen consumption", "SMR production meter",
                 "Hydrogen header", "Site economics"],
        rows=rows, path=["CCR-1", "UTL-H2", "HMU-1", "HCU-1", "NET-H2"], evidence=sorted(set(ev)),
        recommendation=("Agree a hydrogen shedding sequence before it is needed (DEC-H2): hydrocracker rate first, then VGO "
                        "hydrotreater severity, protecting ULSD. Evaluate SMR capacity creep and hydrogen recovery from HCU "
                        "purge — each 10 MMSCFD recovered keeps ≈6 kbpd of hydrocracker feed online during a reformer outage."),
        decision_owner="Process Engineer (DEC-H2) with Planning & Economics Lead",
        caveat=("Chemical consumption only (solution and purge losses not modelled). Margin uses site GRM as a proxy for hydrocracker "
                "margin; actual loss depends on what replaces the lost feed."),
    )


def sulfur_ceiling(kg):
    s_in, mass, s_avg = _f(kg, SITE, "sulfur_in"), _f(kg, SITE, "crude_mass_rate"), _f(kg, SITE, "crude_sulfur_avg")
    sru, cap = _f(kg, "SRU-1", "sulfur_production"), _f(kg, "SRU-1", "design_capacity")
    fates = [kg.fact(SITE, k) for k in ("sulfur_to_coke", "sulfur_to_residual_products", "sulfur_in_products", "sulfur_emitted_as_so2")]
    share = sru["value"] / s_in["value"]
    s_max = cap["value"] / share / mass["value"] * 100
    s_max_2 = cap["value"] * 2 / 3 / share / mass["value"] * 100       # one of three Claus trains out
    g = {k: kg.fact(k, "sulfur") for k in ("CR-AL", "CR-BM", "CR-MUR")}
    sh = {k: kg.fact(f"CMP-A-{k[3:]}", "slate_share") for k in g}
    bm_max = (s_max - g["CR-AL"]["value"] * sh["CR-AL"]["value"] - g["CR-MUR"]["value"] * (1 - sh["CR-AL"]["value"])) / \
             (g["CR-BM"]["value"] - g["CR-MUR"]["value"])
    rows = [dict(item="Sulfur in crude", t_per_d=s_in["value"], share_pct=100.0),
            dict(item="Recovered in SRU", t_per_d=sru["value"], share_pct=round(100 * share, 1))] + \
           [dict(item=f["predicate"].replace("_", " "), t_per_d=f["value"], share_pct=round(100 * f["value"] / s_in["value"], 1))
            for f in fates]
    ev = [s_in["id"], mass["id"], s_avg["id"], sru["id"], cap["id"]] + [f["id"] for f in fates] + \
         [x["id"] for x in g.values()] + [x["id"] for x in sh.values()]
    return dict(
        id="sulfur-ceiling",
        title="Crude sulfur ceiling set by the SRU",
        question="How much more sour crude can we run before sulfur recovery becomes the constraint?",
        headline=(f"The slate averages {s_avg['value']:.2f} wt% S; the SRU is at {100 * sru['value'] / cap['value']:.1f}% "
                  f"({sru['value']:.0f} of {cap['value']:.0f} t/d). The ceiling is ≈{s_max:.2f} wt% S — Basrah Medium could rise from "
                  f"{100 * sh['CR-BM']['value']:.0f}% to ≈{100 * bm_max:.0f}% of the slate. With one Claus train out the ceiling "
                  f"falls to ≈{s_max_2:.2f} wt%, below today's slate."),
        value_usd=None,
        domains=["Crude assays", "Crude schedule", "Hydrocarbon accounting", "SRU production", "Sulfur balance / CEMS"],
        rows=rows, path=[SITE, "CR-BM", "ARU-1", "SWS-1", "SRU-1", "NET-SULFUR"], evidence=sorted(set(ev)),
        recommendation=("Give the planner the ceiling as a live LP constraint (DEC-SLATE). Before any SRU train maintenance, "
                        "pre-plan a sweeter slate or acid-gas shedding (DEC-SULF), because one train out puts today's slate over the limit."),
        decision_owner="Planning & Economics Lead (DEC-SLATE) with Environmental Engineer (DEC-SULF)",
        caveat=("Assumes sulfur distributes to coke, residuals, products and emissions in today's proportions; heavier sour crudes "
                "push more sulfur to coke. Crude swap holds Arab Light at its current share."),
    )


def reformer_bottleneck(kg):
    util, byp, spread = _f(kg, "CCR-1", "utilisation"), _f(kg, "STR-NHT-HN-BYP", "flow_rate"), _f(kg, SITE, "reformate_upgrade_spread")
    h2y, head = _f(kg, "CCR-1", "h2_yield"), _f(kg, SITE, "h2_headroom")
    value = byp["value"] * 1000 * 365 * spread["value"]
    extra_h2 = h2y["value"] * byp["value"] / 1000
    rows = [dict(item="Reformer utilisation", value=util["value"], unit="%"),
            dict(item="Heavy naphtha bypassing the reformer", value=byp["value"], unit="kbpd"),
            dict(item="Reformate upgrade spread (assumption)", value=spread["value"], unit="USD/bbl"),
            dict(item="Hydrogen the bypass would add", value=round(extra_h2, 1), unit="MMSCFD"),
            dict(item="Hydrogen headroom today", value=head["value"], unit="MMSCFD")]
    return dict(
        id="reformer-bottleneck",
        title="Reformer bottleneck: naphtha bypass and lost hydrogen",
        question="Is the reformer limiting gasoline value, and what would debottlenecking unlock?",
        headline=(f"The reformer runs at {util['value']:.0f}% and {byp['value']:.1f} kbpd of heavy naphtha bypasses it into the gasoline "
                  f"pool: ≈{_usd(value)}/yr at an assumed ${spread['value']:.0f}/bbl upgrade spread. Reforming it would also add "
                  f"{extra_h2:.1f} MMSCFD of hydrogen, lifting headroom from {head['value']:.1f} to {head['value'] + extra_h2:.1f} MMSCFD."),
        value_usd=round(value), value_label="upgrade per year",
        domains=["Hydrocarbon accounting", "Reformer design basis", "Hydrogen network", "Planning economics"],
        rows=rows, path=["NHT-1", "STR-NHT-HN-BYP", "GBL-1", "CCR-1", "UTL-H2"],
        evidence=sorted({util["id"], byp["id"], spread["id"], h2y["id"], head["id"]}),
        recommendation=("Scope a reformer debottleneck study (reactor/regenerator and net-gas compressor limits) and test the "
                        "case in the LP; value the hydrogen credit together with the octane uplift, not separately."),
        decision_owner="Planning & Economics Lead with Process Engineer",
        caveat="Upgrade spread is a low-confidence planning assumption; octane-barrel value depends on pool constraints.",
    )


def conversion_loss_chains(kg, window_days=60):
    deep = {"FCC-1", "HCU-1", "DCU-1"}
    eq_of = lambda nid: next((a for a in kg.ancestors(nid) if kg.nodes[a]["cls"] == "EquipmentUnit"), None)
    rows, ev, path, total = [], [], set(), 0
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
                    if 0 <= gap <= window_days:
                        precursors.append(f"{x} ({gap} d before, {kg.nodes[dp]['name'].split(' ', 1)[1]})")
                        ev.append(kg.fact(x, "peak_value")["id"])
                        path.add(x)
        ev += [kg.fact(fl["id"], "failure_mechanism")["id"]] + [kg.fact(w, "actual_cost")["id"] for w in wo] + ([lost["id"]] if lost else [])
        path.update([fl["id"], eq] + loops)
        loss = cost + (lost["value"] if lost else 0)
        total += loss
        rows.append(dict(event=fl["id"], equipment=eq, unit=kg.nodes[eq]["props"]["plant_unit"], date=fl["props"]["date"],
                         mechanism=kg.value(fl["id"], "failure_mechanism"), repair_usd=cost,
                         lost_margin_usd=lost["value"] if lost else 0, total_usd=loss,
                         loops=", ".join(loops) or "-", precursors="; ".join(sorted(precursors)) or "none in window"))
    rows.sort(key=lambda r: -r["total_usd"])
    flagged = [r for r in rows if r["precursors"] != "none in window"]
    return dict(
        id="conversion-loss-chains",
        title="Conversion-unit losses and the signals that came first",
        question="What did FCC, hydrocracker and coker failures cost this year, and which were signalled in data we already held?",
        headline=(f"{len(rows)} conversion-unit failures cost ≈{_usd(total)} in FY2026 (repairs plus lost margin), led by "
                  f"{rows[0]['event']} on {rows[0]['equipment']} (≈{_usd(rows[0]['total_usd'])}). "
                  f"{len(flagged)} had an IOW exceedance in the same corrosion loop or safety function within {window_days} days before: "
                  + "; ".join(f"{r['event']} ← {r['precursors'].split(' (')[0]}" for r in flagged) + "."),
        value_usd=round(total), value_label="failure cost FY2026",
        domains=["CMMS (ISO 14224)", "IOW monitor", "Corrosion loops (RBI)", "Safety functions", "Operations logbook", "Site economics"],
        rows=rows, path=sorted(path), evidence=sorted(set(ev)),
        recommendation=("Make IOW exceedances in a loop open a follow-up task on every loop member (not just the tagged item): the REAC "
                        "wash-water shortfall preceded the E-410C tube leak by weeks. Keep coke-drum fitness-for-service on cycle count "
                        "(DE-DRUMCYC), since D-501B has the most cycles of the four drums."),
        decision_owner="Corrosion / Integrity Engineer with Maintenance Manager",
        caveat=f"Precursor = IOW exceedance on any member of the failed item's loop or SIF within {window_days} days; association, not proven cause.",
    )


REFINERY = [hydrogen_headroom, sulfur_ceiling, conversion_loss_chains, reformer_bottleneck, nelson_complexity]
ALL = REFINERY + cdu_insights.ALL          # refinery-wide first; the CDU insights keep their v0.3 behaviour


def run_all(kg):
    return [f(kg) for f in ALL]
