"""
Integrity operating windows, exceedances and failure events for the Refinery Gamma model (v0.5).

- IOW limits are nodes (IOWLimit) with an API 584 level (critical / standard / informational), a direction,
  a limit value, a response time and a required action — not bare numbers on a tag.
- Exceedances link to the tag (ON_DATAPOINT) and to the limit they breached (EXCEEDS).
- Failures are coded against ISO 14224:2016 Annex B code nodes: failure mode (Table B.15 family),
  failure mechanism (B.2), failure cause (B.3) and detection method (B.4), with severity, downtime,
  time to repair and man-hours. Lost margin is computed in a final pass (refinery_economics) from the
  marginal value of the unit that lost throughput, not from site GRM.
"""
DESIGN_DATE = "2024-06-30"

IOW_SRC = "IOW register (API 584)"
RESPONSE = {"critical": (1, "Immediate: reduce severity or shut in per procedure; notify integrity engineer and shift superintendent"),
            "standard": (24, "Restore within 24 h; integrity engineer reviews cause and damage-rate impact"),
            "informational": (168, "Trend and review at the weekly IOW meeting")}

# ISO 14224:2016 Annex B code lists (subset used by the reference model)
FAILURE_MODES = {"ELP": "External leakage – process medium", "ELU": "External leakage – utility medium",
                 "INL": "Internal leakage", "VIB": "Vibration", "UST": "Spurious stop", "FTS": "Fail to start on demand",
                 "BRD": "Breakdown", "STD": "Structural deficiency", "PDE": "Parameter deviation", "HIO": "High output",
                 "LOO": "Low output", "PLU": "Plugged / choked", "ERO": "Erratic output", "FTC": "Fail to close on demand",
                 "SER": "Minor in-service problems", "OTH": "Other"}
FAILURE_MECHANISMS = {"1.0": "Mechanical failure – general", "1.1": "Leakage", "1.2": "Vibration", "1.3": "Clearance / alignment failure",
                      "1.4": "Deformation", "1.5": "Looseness", "1.6": "Sticking", "2.0": "Material failure – general",
                      "2.1": "Cavitation", "2.2": "Corrosion", "2.3": "Erosion", "2.4": "Wear", "2.5": "Breakage", "2.6": "Fatigue",
                      "2.7": "Overheating", "2.8": "Burst", "3.0": "Instrument failure – general", "3.1": "Control failure",
                      "3.2": "No signal / indication / alarm", "3.3": "Faulty signal / indication / alarm", "3.4": "Out of adjustment",
                      "4.0": "Electrical failure – general", "4.1": "Short circuiting", "4.2": "Open circuit", "4.3": "No power / voltage",
                      "4.5": "Earth / isolation fault", "5.1": "Blockage / plugged", "5.2": "Contamination"}
FAILURE_CAUSES = {"1.1": "Improper capacity", "1.2": "Improper material", "2.1": "Fabrication error", "2.2": "Installation error",
                  "3.1": "Off-design service", "3.2": "Operating error", "3.3": "Maintenance error", "3.4": "Expected wear and tear",
                  "4.1": "Documentation error", "4.2": "Management error", "5.1": "No cause found", "5.3": "Common cause / mode"}
DETECTION_METHODS = {"1": "Periodic maintenance", "2": "Functional testing", "3": "Inspection", "4": "Periodic condition monitoring",
                     "5": "Continuous condition monitoring", "6": "Production interference", "7": "Casual observation",
                     "8": "Corrective maintenance", "9": "On demand", "10": "Other"}


def iso14224_codes(b):
    """Create the code nodes once (Sector 1a reference)."""
    if "FM-ELP" in b.nodes:
        return
    for code, name in FAILURE_MODES.items():
        b.node(f"FM-{code}", "FailureMode", f"{name} ({code})", "reference", notation=code, scheme="ISO 14224:2016 Table B.15")
    for code, name in FAILURE_MECHANISMS.items():
        b.node(f"FMECH-{code}", "FailureMechanism", f"{code} {name}", "reference", notation=code, scheme="ISO 14224:2016 Table B.2")
    for code, name in FAILURE_CAUSES.items():
        b.node(f"FCAUSE-{code}", "RootCause", f"{code} {name}", "reference", notation=code, scheme="ISO 14224:2016 Table B.3")
    for code, name in DETECTION_METHODS.items():
        b.node(f"DET-{code}", "DetectionMethod", f"{code} {name}", "reference", notation=code, scheme="ISO 14224:2016 Table B.4")


def iow_limit(b, tag, level, direction, value, unit, owner="ROLE-CORR", src=IOW_SRC):
    lid = f"IOWL-{tag}-{level[:4].upper()}-{direction.upper()}"
    b.node(lid, "IOWLimit", f"{level.title()} {direction} limit on {b.nodes[tag]['name']}", "event", iow_level=level, direction=direction)
    b.edge(lid, "LIMITS", tag)
    hrs, action = RESPONSE[level]
    b.fact(lid, "limit_value", value, unit, as_of=DESIGN_DATE, src=src, ref=lid, owner=owner, method="declared")
    b.fact(lid, "response_time", hrs, "h", as_of=DESIGN_DATE, src=src, ref=lid, owner=owner, method="declared")
    b.fact(lid, "required_action", action, "", as_of=DESIGN_DATE, src=src, ref=lid, owner=owner, method="declared")
    return lid


def limits_on(b, tag):
    return [e["source"] for e in b.edges if e["rel"] == "LIMITS" and e["target"] == tag]


def exceedance(b, iid, tag, d, peak, dur, unit, owner="ROLE-CORR"):
    b.node(iid, "IOWExceedance", f"{iid} on {b.nodes[tag]['name']}", "event", date=d)
    b.edge(iid, "ON_DATAPOINT", tag)
    b.fact(iid, "peak_value", peak, unit, as_of=d, src="PI historian / IOW monitor", ref=iid, owner=owner, method="measured")
    b.fact(iid, "duration", dur, "days", as_of=d, src="PI historian / IOW monitor", ref=iid, owner=owner, method="measured")
    rank = {"informational": 0, "standard": 1, "critical": 2}
    breached = []
    for lid in limits_on(b, tag):
        n = b.nodes[lid]["props"]
        v = b.fact_value(lid, "limit_value")
        if (n["direction"] == "high" and peak > v) or (n["direction"] == "low" and peak < v):
            breached.append((rank[n["iow_level"]], lid))
    if breached:
        b.edge(iid, "EXCEEDS", max(breached)[1])
    return iid


def failure(b, fid, target, d, mode, mech, cause, detection, text, cost, wo, severity="Degraded", downtime_h=0, ttr_h=8,
            man_hours=16, rate_cut=0, days=0, desc="", work_type="Corrective repair"):
    """mode/mech/cause/detection are ISO 14224 codes (e.g. 'ELP', '2.4', '3.4', '5')."""
    iso14224_codes(b)
    b.node(fid, "Failure", f"{fid} {b.nodes[target]['name']}", "event", date=d, desc=desc)
    b.edge(fid, "FAILURE_OF", target)
    b.edge(fid, "HAS_FAILURE_MODE", f"FM-{mode}")
    b.edge(fid, "HAS_FAILURE_MECHANISM", f"FMECH-{mech}")
    b.edge(fid, "HAS_FAILURE_CAUSE", f"FCAUSE-{cause}")
    b.edge(fid, "DETECTED_BY", f"DET-{detection}")
    src = dict(as_of=d, src="CMMS (ISO 14224 coding)", ref=wo, owner="ROLE-MAINT")
    b.fact(fid, "failure_mode", f"{FAILURE_MODES[mode]} ({mode})", "", **src)
    b.fact(fid, "failure_mechanism", f"{mech} {FAILURE_MECHANISMS[mech]} — {text}", "", **src)
    b.fact(fid, "failure_cause", f"{cause} {FAILURE_CAUSES[cause]}", "", **src)
    b.fact(fid, "detection_method", f"{detection} {DETECTION_METHODS[detection]}", "", **src)
    b.fact(fid, "severity", severity, "", **src)
    b.fact(fid, "downtime", downtime_h, "h", **src)
    b.node(wo, "WorkOrder", f"{wo} {work_type.lower()}", "event", date=d)
    b.edge(wo, "REMEDIATES", fid)
    b.fact(wo, "actual_cost", cost, "USD", as_of=d, src="CMMS", ref=wo, owner="ROLE-MAINT")
    b.fact(wo, "work_type", work_type, "", as_of=d, src="CMMS", ref=wo, owner="ROLE-MAINT")
    b.fact(wo, "time_to_repair", ttr_h, "h", as_of=d, src="CMMS", ref=wo, owner="ROLE-MAINT")
    b.fact(wo, "man_hours", man_hours, "h", as_of=d, src="CMMS", ref=wo, owner="ROLE-MAINT")
    if rate_cut:
        b.fact(fid, "rate_reduction", rate_cut, "kbd", as_of=d, src="Operations logbook", owner="ROLE-OPS")
        b.fact(fid, "rate_reduction_days", days, "days", as_of=d, src="Operations logbook", owner="ROLE-OPS")
    return fid
