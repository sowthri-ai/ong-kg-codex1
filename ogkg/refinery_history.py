"""
Time dimension for Refinery Gamma (v0.5), called from cdu_gamma.build().

- Monthly histories (Oct 2025 - Sep 2026) as facts with valid_from / valid_to, so value(as_of=...) and trends work
- Fact corrections: a superseded fact stays in the graph (status 'superseded'), the correction points to it
  (supersedes) and a CorrectionRequest records who asked, who approved and why
- Serial items installed at functional locations with validity dates, including a pump replacement (MOC);
  failures record the serial item they occurred on
- A realistic twelve-month failure history for the pump fleet (fleet MTBF about 4-6 pump-years) and fleet MTBF facts
- Synthetic historian series (hourly, 30 days) for key tags, written by cdu_gamma.main() to data/cdu-gamma/historian/
"""
import math
from datetime import datetime, timedelta

from . import gamma_events as ev
from .cdu_gamma import AS_OF, DESIGN_DATE, SITE, jitter

MONTHS = ["2025-10-01", "2025-11-01", "2025-12-01", "2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01", "2026-05-01",
          "2026-06-01", "2026-07-01", "2026-08-01", "2026-09-01"]
NEXT = MONTHS[1:] + [None]


def apply(b):
    _monthly(b)
    _corrections(b)
    _serials(b)
    _failure_history(b)
    _fleet_mtbf(b)


def _series(b, subj, pred, values, unit, src, owner, method="measured", conf="medium", lineage=None):
    ids = []
    for d, nd, v in zip(MONTHS, NEXT, values):
        ids.append(b.fact(subj, pred, round(v, 2), unit, as_of=nd or AS_OF, src=src, owner=owner, method=method, conf=conf,
                          valid_from=d, valid_to=nd, lineage=lineage))
    return ids


def _monthly(b):
    val = lambda s, p: b.fact_value(s, p)
    # unit feed rates by month (hydrocarbon accounting): FY average preserved, with seasonal and outage effects
    for n in [n for n in b.nodes.values() if n["cls"] == "PlantUnit" and b.fact_obj(n["id"], "feed_rate")]:
        u = n["id"]
        avg = val(u, "feed_rate")
        raw = [avg * (1 + jitter(f"{u}{m}", 0.025)) for m in MONTHS]
        if u == "DCU-1":
            raw[7] *= 0.62                                  # May: one drum pair out (FL-D01)
        if u == "HCU-1":
            raw[5] *= 0.93; raw[9] *= 0.94                  # Mar REAC leak, Jul compressor trip
        k = avg * 12 / sum(raw)
        _series(b, u, "feed_rate_month", [x * k for x in raw], "kbd", "Hydrocarbon accounting (monthly yield accounting)", "ROLE-PLAN")
    # hydrocracker catalyst deactivation: WABT rises ~2 degC/month
    wabt = [377 + 2.0 * i + jitter(f"wabt{i}", 0.4) for i in range(11)] + [val("HCU-1", "wabt_cracking")]
    ids = _series(b, "HCU-1", "wabt_cracking_month", wabt, "degC", "PI historian (monthly average)", "ROLE-CONV")
    slope = (wabt[-1] - wabt[0]) / 11
    dr = b.fact("HCU-1", "deactivation_rate", round(slope, 2), "degC/month", as_of=AS_OF, src="KG derived", owner="ROLE-CONV",
                method="calculated", lineage=ids)
    months_left = (val("HCU-1", "eor_wabt") - wabt[-1]) / slope
    y, m = 2026 + (9 + round(months_left) - 1) // 12, (9 + round(months_left) - 1) % 12 + 1
    b.fact("HCU-1", "predicted_eor_date", f"{y}-{m:02d}-01", "", as_of=AS_OF, src="KG derived", owner="ROLE-CONV", method="calculated",
           lineage=[dr, b.fact_obj("HCU-1", "eor_wabt")["id"], ids[-1]])
    # FCC: conversion and catalyst losses (cyclone erosion from July)
    conv = val("FCC-1", "conversion")
    _series(b, "FCC-1", "conversion_month", [conv + jitter(f"conv{i}", 0.6) for i in range(11)] + [conv], "vol%",
            "KG derived (monthly yield accounting)", "ROLE-CONV")
    loss = [2.3 + jitter(f"cl{i}", 0.15) for i in range(9)] + [2.9, 3.4, val("FCC-1", "catalyst_loss")]
    _series(b, "FCC-1", "catalyst_loss_month", loss, "t/d", "Catalyst loader log / e-cat inventory balance", "ROLE-CONV")
    # CDU: energy intensity (Train B fouling, partial recovery after the March cleaning) and overhead chloride
    for tr, base, trend in (("A", val("CDU-A", "energy_intensity"), 0.0), ("B", val("CDU-B", "energy_intensity"), 0.5)):
        ei = [base - trend * (11 - i) * 0.35 + jitter(f"ei{tr}{i}", 0.3) for i in range(11)] + [base]
        if tr == "B":
            ei[5] -= 1.5; ei[6] -= 1.0
        _series(b, f"CDU-{tr}", "energy_intensity_month", ei, "MMBtu/kbbl", "KG derived (monthly energy balance)", "ROLE-ENERGY")
    cl = [14, 16, 17, 31, 19, 17, 36, 18, 16, 27, 17, 18]
    _series(b, "CDU-A", "overhead_chloride_month", cl, "ppm", "LIMS (monthly average)", "ROLE-CORR")
    _series(b, "CDU-B", "overhead_chloride_month", [9 + jitter(f"clb{i}", 1.5) for i in range(12)], "ppm", "LIMS (monthly average)",
            "ROLE-CORR")
    tmt = [628, 631, 634, 636, 638, 640, 642, 645, 652, 646, 649, 638]
    _series(b, "H-502", "max_tmt_month", tmt, "degC", "PI historian (monthly maximum)", "ROLE-CORR")


def _corrections(b):
    N, E, F = b.node, b.edge, b.fact
    orig = b.fact_obj("CDU-B", "availability_fy2026")
    orig["status"] = "superseded"
    orig["valid_to"] = "2026-09-29"
    new = F("CDU-B", "availability_fy2026", 99.1, "%", as_of="2026-09-29", src="Operations logbook (corrected)", owner="ROLE-OPS",
            method="recorded", valid_from="2026-09-29", supersedes=orig["id"])
    N("CR-001", "CorrectionRequest", "CR-001 CDU-B availability booked 12 h of planned outage as unplanned", "event",
      corrects_fact=orig["id"], proposed_value=99.1, reason="Outage hours on 2026-03-10 exchanger cleaning were booked as unplanned",
      status="Validated", requested_by="ROLE-OPS", reviewed_by="ROLE-STEWARD", reviewed_on="2026-09-29",
      hyp_subject="CDU-B", hyp_predicate="availability_fy2026", hyp_object="CDU-B", confidence_score=0.95, inferred_by="manual",
      run_id="CR-001", evidence=["WO-B02"])
    E("CR-001", "OWNED_BY", "ROLE-STEWARD")
    psv = next(n["id"] for n in b.nodes.values() if n["id"].startswith("PSV-3"))
    N("CR-002", "CorrectionRequest", f"CR-002 {psv} set pressure differs from the latest test certificate", "event",
      corrects_fact=b.fact_obj(psv, "set_pressure")["id"], proposed_value=round(b.fact_value(psv, "set_pressure") * 0.97, 1),
      reason="Bench-test certificate shows 3% lower cold differential test pressure; datasheet not updated",
      status="Proposed", requested_by="ROLE-INST", hyp_subject=psv, hyp_predicate="set_pressure", hyp_object=psv,
      confidence_score=0.7, inferred_by="manual", run_id="CR-002", evidence=[psv])
    E("CR-002", "OWNED_BY", "ROLE-STEWARD")


def _serials(b):
    N, E, F = b.node, b.edge, b.fact
    rot = [n for n in b.nodes.values() if n["cls"] == "EquipmentUnit" and n["props"].get("eq_class") in ("Pump", "Compressor")]
    for n in sorted(rot, key=lambda x: x["id"]):
        eid = n["id"]
        unit = n["props"]["plant_unit"]
        inst = {"FCC-1": "2008-05-01", "HCU-1": "2011-04-01", "DCU-1": "2012-09-01"}.get(unit, "2004-03-01")
        swaps = [inst] + (["2026-02-10"] if eid == "P-208A" else [])
        for i, start in enumerate(swaps, start=1):
            sn = f"SN-{eid}-{i}"
            end = swaps[i] if i < len(swaps) else None
            N(sn, "SerialItem", f"{sn} {n['name'].split(' ', 1)[1]} (serial {i})", "serial", aliases=[f"{eid}/{i}"])
            E(sn, "INSTALLED_AT", eid, valid_from=start, valid_to=end, source="CMMS equipment history")
            model = b.fact_value(eid, "model")
            if model:
                E(sn, "OF_MODEL", "MOD-" + model.replace(" ", "-"))
            F(sn, "serial_number", f"S{int(jitter(sn, 0.5) * 1e7) + 50_000_000:08d}", "",
              as_of=start, src="CMMS equipment history", owner="ROLE-MAINT", method="recorded")
            F(sn, "install_date", start, "", as_of=start, src="CMMS equipment history", owner="ROLE-MAINT", method="recorded")
    N("WO-B04", "WorkOrder", "WO-B04 MOC-2026-011 replace P-208A with refurbished unit (dual seal retrofit)", "event", date="2026-02-10")
    E("WO-B04", "PERFORMED_ON", "P-208A")
    F("WO-B04", "actual_cost", 95000, "USD", as_of="2026-02-10", src="CMMS", ref="WO-B04", owner="ROLE-MAINT")
    F("WO-B04", "work_type", "MOC — equipment replacement", "", as_of="2026-02-10", src="CMMS", ref="WO-B04", owner="ROLE-MAINT")
    F("WO-B04", "moc_reference", "MOC-2026-011", "", as_of="2026-02-10", src="MOC register", ref="WO-B04", owner="ROLE-MAINT")
    # failures record the serial item they happened on
    for fl in [n for n in b.nodes.values() if n["cls"] == "Failure"]:
        _link_serial(b, fl)


def _link_serial(b, fl):
    target = next(e["target"] for e in b.edges if e["source"] == fl["id"] and e["rel"] == "FAILURE_OF")
    x = target
    while b.nodes[x]["cls"] != "EquipmentUnit":
        x = next(e["target"] for e in b.edges if e["source"] == x and e["rel"] == "PART_OF")
    d = fl["props"]["date"]
    for e in b.edges:
        if e["rel"] == "INSTALLED_AT" and e["target"] == x and e["props"]["valid_from"] <= d and \
                (e["props"].get("valid_to") is None or d < e["props"]["valid_to"]):
            b.edge(fl["id"], "OCCURRED_ON_SERIAL", e["source"])


FAILURE_PATTERNS = [  # item code, mode, mechanism, cause, detection, text, cost, ttr, man-hours, severity
    ("SEAL", "ELP", "2.4", "3.4", "5", "seal face wear", 42000, 14, 40, "Degraded"),
    ("SEAL", "ELP", "1.1", "3.3", "7", "secondary seal (O-ring) leak after overhaul", 28000, 10, 30, "Degraded"),
    ("TBRG", "VIB", "2.4", "3.4", "4", "thrust bearing wear (vibration trend)", 35000, 18, 50, "Incipient"),
    ("RBRG", "VIB", "1.3", "2.2", "4", "misalignment after coupling work", 22000, 8, 24, "Incipient"),
    ("IMP", "LOO", "2.1", "3.1", "6", "impeller cavitation at low NPSH margin", 58000, 30, 90, "Degraded"),
    ("CPLG", "BRD", "2.5", "3.4", "6", "coupling element breakage", 18000, 6, 16, "Critical"),
]


def _failure_history(b):
    pumps = sorted(n["id"] for n in b.nodes.values() if n["props"].get("eq_class") == "Pump")
    picks = [p for p in pumps if int(jitter("pick" + p, 1000) + 1000) % 5 == 0][:18]
    for i, p in enumerate(picks, start=1):
        code, mode, mech, cause, det, text, cost, ttr, mh, sev = FAILURE_PATTERNS[i % len(FAILURE_PATTERNS)]
        target = f"{p}-{code}" if f"{p}-{code}" in b.nodes else p
        month = MONTHS[(i * 5) % 12]
        d = month[:8] + f"{(i * 7) % 26 + 2:02d}"
        fid = f"FL-P{i:02d}"
        ev.failure(b, fid, target, d, mode, mech, cause, det, text, round(cost * (1 + jitter(fid, 0.3)), -2), f"WO-P{i:02d}",
                   severity=sev, downtime_h=0, ttr_h=ttr, man_hours=mh, desc="Pump failure (history import from CMMS)")
        _link_serial(b, b.nodes[fid])
    for fid, target, d, mode, mech, cause, det, text, cost in [
            ("FL-I01", "TI-1052" if "TI-1052" in b.nodes else None, "2026-05-14", "ERO", "3.3", "3.4", "4", "thermocouple drift", 6000),
            ("FL-E01", "E-120B-FAN", "2026-08-09", "BRD", "2.5", "3.4", "7", "fan belt breakage", 9000),
            ("FL-E02", "PM-208A-WIND" if "PM-208A-WIND" in b.nodes else None, "2026-06-30", "BRD", "4.5", "3.4", "6",
             "stator winding insulation fault", 64000)]:
        if target is None or target not in b.nodes:
            continue
        ev.failure(b, fid, target, d, mode, mech, cause, det, text, cost, "WO-" + fid[3:], severity="Degraded", ttr_h=12, man_hours=30)
        _link_serial(b, b.nodes[fid])


def _fleet_mtbf(b):
    pumps = [n["id"] for n in b.nodes.values() if n["props"].get("eq_class") == "Pump"]

    def failures_on(eqs):
        out = []
        for fl in [n["id"] for n in b.nodes.values() if n["cls"] == "Failure"]:
            x = next(e["target"] for e in b.edges if e["source"] == fl and e["rel"] == "FAILURE_OF")
            while b.nodes[x]["cls"] != "EquipmentUnit":
                x = next(e["target"] for e in b.edges if e["source"] == x and e["rel"] == "PART_OF")
            if x in eqs:
                out.append(b.fact_obj(fl, "failure_mode")["id"])
        return out
    for grp, eqs in [("FLT-HOT", [e["source"] for e in b.edges if e["rel"] == "MEMBER_OF" and e["target"] == "FLT-HOT"]),
                     ("FLT-CHARGE", [e["source"] for e in b.edges if e["rel"] == "MEMBER_OF" and e["target"] == "FLT-CHARGE"]),
                     (SITE, pumps)]:
        fl = failures_on(set(eqs))
        pop = b.fact(grp, "pump_population", len(eqs), "count", as_of=AS_OF, src="Asset register (CMMS)", owner="ROLE-ROT", method="recorded")
        cnt = b.fact(grp, "pump_failures_12m", len(fl), "count", as_of=AS_OF, src="KG derived", owner="ROLE-ROT", method="calculated",
                     lineage=fl or [pop])
        mt = round(len(eqs) * 365 / max(len(fl), 1))
        b.fact(grp, "mtbf_days", mt, "days", as_of=AS_OF, src="KG derived", owner="ROLE-ROT", method="calculated", lineage=[pop, cnt],
               basis="installed pump-days / failures, last 12 months (standby pumps included)")


# ----------------------------------------------------------------------------- historian series
KEY_TAGS = [("H-201", "Pass 3 tube-metal"), ("H-101", "Pass 3 tube-metal"), ("H-502", "Pass 3 tube-metal"), ("V-102", "Boot water pH"),
            ("V-202", "Boot water pH"), ("R-402", "Bed 4 outlet temperature"), ("R-401", "Bed 3 outlet temperature"),
            ("K-401", "Journal bearing vibration"), ("R-301", "(ROT)"), ("R-302", "Dense-bed temperature"),
            ("X-401", "Injection rate"), ("D-501B", "Quench water rate"), ("P-101A", "Radial bearing vibration"),
            ("P-208B", "Radial bearing vibration"), ("H-201", "(CIT)"), ("H-101", "(CIT)"), ("PC-102", "dew-point margin")]


def timeseries(b):
    out = {}
    for eq, text in KEY_TAGS:
        tag = next((n for n in b.nodes.values() if n["cls"] == "DataPoint" and n["props"].get("equipment") == eq and text in n["name"]), None)
        if not tag or "PI" not in tag["props"].get("external_ids", {}):
            continue
        last = b.fact_value(tag["id"], "latest_value")
        rows = []
        for h in range(720):
            ts = (datetime(2026, 8, 29, 1) + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
            v = last * (1 + 0.01 * math.sin(h / 24 * 2 * math.pi) + jitter(f"{tag['id']}{h}", 0.006))
            if h == 719:
                v = last
            rows.append((ts, round(v, 3), "Good"))
        out[tag["props"]["external_ids"]["PI"]] = dict(tag=tag["id"], rows=rows)
    return out
