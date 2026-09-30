"""
Performance measures, facet bindings and hypotheses for Refinery Gamma (v0.5), called from cdu_gamma.build().

- KPIs (with formula, aggregation rule, applicable level, tier and owner) and the KPFs that drive them, each
  controlled by a decision point and measured by a tag
- Facet bindings: backbone nodes bound to entities at a level, with an inheritance rule and validity
- Hypothesis assertions from rules / AI with status (proposed / validated / rejected), confidence, evidence and review
"""
from .cdu_gamma import DESIGN_DATE

KPIS = [  # id, name, formula, aggregation, level, tier, owner, measures, maps_to_predicate
    ("KPI-GRM", "Gross refining margin", "(product revenue − feedstock cost − variable opex) / crude processed", "PooledRate", 3,
     "Strategic", "ROLE-PLAN", ["SITE-GAMMA"], "grm_fy2026"),
    ("KPI-CO2", "CO2 intensity (scope 1)", "scope-1 CO2 / crude processed", "PooledRate", 3, "Strategic", "ROLE-ENV", ["SITE-GAMMA"],
     "co2_intensity"),
    ("KPI-H2-HEAD", "Hydrogen headroom", "(reformer H2 + SMR capacity) − make-up demand", "Minimum", 3, "Tactical", "ROLE-PROC",
     ["UTL-H2"], "h2_headroom"),
    ("KPI-EII", "Energy intensity", "fired duty / throughput", "CapacityWeighted", 4, "Tactical", "ROLE-ENERGY", ["CDU-A", "CDU-B"],
     "energy_intensity"),
    ("KPI-AVAIL", "Unit availability", "operating hours / calendar hours", "TimeWeighted", 4, "Tactical", "ROLE-OPS", ["CDU-A", "CDU-B"],
     "availability_fy2026"),
    ("KPI-MTBF", "Pump fleet MTBF", "installed pump-days / failures", "PooledRate", 3, "Tactical", "ROLE-ROT", ["SITE-GAMMA"], "mtbf_days"),
    ("KPI-FCC-CONV", "FCC conversion", "1 − (LCO + slurry) / fresh feed", "PooledRate", 4, "Operational", "ROLE-CONV", ["FCC-1"],
     "conversion"),
    ("KPI-HCU-CONV", "Hydrocracker conversion", "1 − unconverted oil / feed", "PooledRate", 4, "Operational", "ROLE-CONV", ["HCU-1"],
     "conversion"),
    ("KPI-GIVEAWAY", "Octane giveaway", "measured pool RON − specification", "TimeWeighted", 4, "Operational", "ROLE-PROC",
     ["PRD-GASOLINE"], "octane_giveaway"),
]
KPFS = [  # id, name, drives, controlled by, measured by (equipment, tag text)
    ("KPF-ROT", "Riser outlet temperature", "KPI-FCC-CONV", "DEC-FCC", ("R-301", "(ROT)")),
    ("KPF-WABT", "Cracking-reactor WABT", "KPI-HCU-CONV", "DEC-HCU", ("R-402", "Weighted average bed")),
    ("KPF-CIT", "Heater inlet temperature (preheat)", "KPI-EII", "DEC-CLEAN", ("H-201", "(CIT)")),
    ("KPF-POOLRON", "Gasoline pool RON", "KPI-GIVEAWAY", "DEC-BLEND", ("GBL-1", "Finished gasoline RON")),
    ("KPF-H2MAKEUP", "Hydrogen make-up demand", "KPI-H2-HEAD", "DEC-H2", ("HMU-1", "Hydrogen production")),
    ("KPF-CHLORIDE", "Overhead chloride", "KPI-AVAIL", "DEC-NEUT", ("V-102", "chloride")),
    ("KPF-SEAL", "Pump seal and bearing health", "KPI-MTBF", "DEC-SWITCH", ("P-101A", "Radial bearing vibration")),
]
FACETS = [  # id, entity, backbone node, facet, level, inheritance
    ("FB-APP-PI", "SITE-GAMMA", "APP-PI", "ApplicationFacet", 3, "InheritDown"),
    ("FB-APP-LIMS", "SITE-GAMMA", "APP-LIMS", "ApplicationFacet", 3, "InheritDown"),
    ("FB-APP-DCSCONV", "FCC-1", "APP-DCS-CONV", "ApplicationFacet", 4, "InheritDown"),
    ("FB-PRICE-ACT", "SITE-GAMMA", "PS-ACT26", "EconomicsFacet", 3, "NoInherit"),
    ("FB-KPI-EII-A", "CDU-A", "KPI-EII", "PerformanceFacet", 4, "NoInherit"),
    ("FB-KPI-FCC", "FCC-1", "KPI-FCC-CONV", "PerformanceFacet", 4, "NoInherit"),
    ("FB-LOC-FCC", "FCC-1", "LOC-PLOT-3", "LocationFacet", 4, "InheritDown"),
    ("FB-LOC-HCU", "HCU-1", "LOC-PLOT-4", "LocationFacet", 4, "InheritDown"),
    ("FB-PHYS-WABT", "R-402", "EQ-WABT", "PhysicsFacet", 6, "NoInherit"),
    ("FB-ENT-GAMMA", "SITE-GAMMA", "ENT-GAMMA", "EnterpriseFacet", 3, "InheritDown"),
]
HYPOTHESES = [  # id, subject, relation, object, status, confidence, rule, run, evidence, reviewer, reviewed on, note
    ("HYP-001", "E-120B", "AT_RISK_OF", "DM-NH4CL", "Proposed", 0.72, "R-07 shared-service failure propagation", "RUN-2026-09-28",
     ["FL-A01", "E-120A", "CL-A-OVH"], None, None, "Same design, service and loop as the failed E-120A"),
    ("HYP-002", "FL-H01", "CAUSED_BY", "IOW-H02", "Validated", 0.81, "R-12 loop precursor within 60 days", "RUN-2026-04-01",
     ["IOW-H02", "CL-HCU-REAC", "X-401"], "ROLE-CORR", "2026-04-02", "Wash-water shortfall 26 days before the REAC tube leak"),
    ("HYP-003", "FL-H02", "CAUSED_BY", "IOW-H01", "Rejected", 0.55, "R-12 loop precursor within 60 days", "RUN-2026-07-10",
     ["IOW-H01", "K-401"], "ROLE-CONV", "2026-07-11", "Reverse causality: the bed excursion followed the compressor trip"),
    ("HYP-004", "D-501A", "AT_RISK_OF", "DM-TFAT", "Proposed", 0.64, "R-15 cycle-count similarity to failed drum", "RUN-2026-09-28",
     ["FL-D01", "D-501B", "CL-DCU-HOT"], None, None, "Second-highest cumulative cycles after the bulged D-501B"),
]


def apply(b):
    N, E = b.node, b.edge
    tag = lambda eq, text: next(n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint" and n["props"].get("equipment") == eq
                                and text in n["name"])
    for kid, name, formula, agg, lvl, tier, owner, measures, pred in KPIS:
        N(kid, "KPI", name, "performance", formula=formula, aggregation=agg, applicable_level=lvl, tier=tier, maps_to_predicate=pred)
        E(kid, "OWNED_BY", owner)
        for m in measures:
            E(kid, "MEASURES", m)
    for fid, name, drives, dec, (eq, text) in KPFS:
        N(fid, "KPF", name, "performance")
        E(fid, "DRIVES", drives)
        E(fid, "CONTROLLED_BY", dec)
        E(fid, "MEASURED_BY", tag(eq, text))
    for fb, ent, to, facet, lvl, rule in FACETS:
        N(fb, "FacetBinding", f"{facet}: {to} → {ent}", "facet", binds_entity=ent, binds_to=to, facet=facet, binding_level=lvl,
          valid_from=DESIGN_DATE, inheritance_rule=rule)
    for hid, s, rel, o, status, conf, rule, run, evidence, reviewer, on, note in HYPOTHESES:
        props = dict(hyp_subject=s, hyp_predicate=rel, hyp_object=o, status=status, confidence_score=conf, inferred_by=rule, run_id=run,
                     evidence=evidence)
        if reviewer:
            props.update(reviewed_by=reviewer, reviewed_on=on)
        N(hid, "HypothesisAssertion", f"{hid} {s} {rel} {o} ({status.lower()})", "event", desc=note, **props)
