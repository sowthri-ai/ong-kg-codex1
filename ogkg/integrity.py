"""
Integrity layer for the Refinery Gamma model (v0.5), called from cdu_gamma.build().

1. Damage-mechanism screening (API 571 / API 941 / NACE SP0170) from material x temperature x environment,
   attached at the level where the damage occurs (item level for column tops, drum shells, injection quills),
   with susceptibility and a governing flag on each SUSCEPTIBLE_TO edge. Fouling and coking are phenomena (SUBJECT_TO).
2. Physics links (GOVERNED_BY) and rule-derived groupings over ALL equipment (fleets, fuel-gas users).
3. Condition-monitoring alert and danger limits on every vibration tag, by machine class.
4. RBI data on every pressure-containing item: install date, PoF / CoF / risk, governing mechanism, last inspection,
   interval and next due; minimum thickness and remaining life for piping; TMLs with thickness history.
5. Relief devices, SIF initiators and final elements, control valves and electrical distribution as equipment;
   SIF attributes (SIL, PFD, proof testing, voting, set points).
6. The 2027 turnaround and its scope, derived from what is due.
"""
from datetime import date

from .cdu_gamma import AS_OF, DESIGN_DATE, SITE, _build_equipment, jitter
from .refinery_units import INSTALL_YEAR

TA_END = "2027-04-15"
LAST_TA = {"CDU-A": "2023-10-15", "CDU-B": "2023-10-15", "CDU-COM": "2023-10-15", "TF-1": "2022-05-01",
           "FCC-1": "2022-03-20", "HCU-1": "2022-03-20", "DCU-1": "2024-05-10"}
STATIC = ("Heat exchanger", "Air cooler", "Fired heater", "Desalter", "Column", "Side stripper", "Vessel", "Piping circuit",
          "Storage tank", "Reactor", "FCC reactor", "FCC regenerator", "Coke drum", "Boiler", "Chemical injection package",
          "Slide valve", "Pump", "Decoking system")
AUSTENITIC = ("SS347", "SS316")
LOW_ALLOY_HTHA = ("CarbonSteel", "Cr125Mo", "Cr225Mo")
HC = ("crude", "residue", "gas oil", "ago", "vgo", "slurry", "pumparound", "diesel", "lco", "lcgo", "hcgo", "kerosene", "naphtha",
      "effluent", "feed", "oil", "hydrocarbon", "vapour", "coke")

MECHANISMS = [  # id, class, name, severity rank (for governing mechanism), inspection method
    ("DM-HTHA", "DamageMechanism", "High-temperature hydrogen attack (API 571 / API 941)", 9, "Advanced UT (TOFD / AUBT) per API 941"),
    ("DM-NH4HS", "DamageMechanism", "Ammonium bisulfide corrosion (API 571 / API 932-B)", 8, "IRIS / RFT tube inspection, UT scanning"),
    ("DM-HCL", "DamageMechanism", "Hydrochloric acid corrosion (API 571)", 8, "UT scanning and profile RT"),
    ("DM-NH4CL", "DamageMechanism", "Ammonium chloride corrosion (API 571)", 7, "UT scanning and profile RT"),
    ("DM-TFAT", "DamageMechanism", "Thermal fatigue (API 571)", 7, "Laser scan and WFMT of shell and skirt welds"),
    ("DM-H2H2S", "DamageMechanism", "High-temperature H2/H2S corrosion (API 571)", 7, "UT grid scanning"),
    ("DM-CREEP", "DamageMechanism", "Creep / stress rupture (API 571)", 6, "Tube OD strain gauging, IRIS, TMT survey"),
    ("DM-WETH2S", "DamageMechanism", "Wet H2S damage: blistering / HIC / SOHIC / SSC (API 571)", 6, "WFMT and UT scanning (A-scan / PAUT)"),
    ("DM-EROSION", "DamageMechanism", "Erosion / erosion-corrosion by catalyst or coke fines (API 571)", 6, "Internal visual and UT"),
    ("DM-SULF", "DamageMechanism", "High-temperature sulfidation (API 571)", 5, "UT grid scanning"),
    ("DM-CARB", "DamageMechanism", "Carbonate stress corrosion cracking (API 571)", 5, "WFMT of welds"),
    ("DM-CAUSTIC", "DamageMechanism", "Caustic stress corrosion cracking (API 571)", 5, "WFMT / PAUT of injection-point welds"),
    ("DM-PTA", "DamageMechanism", "Polythionic acid stress corrosion cracking (API 571)", 5, "Shutdown protection check (NACE SP0170), PT"),
    ("DM-TE", "DamageMechanism", "Temper embrittlement (API 571)", 4, "Minimum pressurisation temperature control; J-factor review"),
    ("DM-CUI", "DamageMechanism", "Corrosion under insulation (API 571)", 4, "Profile RT / pulsed eddy current"),
    ("DM-TANKFLOOR", "DamageMechanism", "Tank floor corrosion, soil- and product-side (API 571 / API 653)", 4, "MFL floor scan"),
    ("DM-FGDP", "DamageMechanism", "Flue-gas dew-point corrosion (API 571)", 3, "Visual and UT of convection / economiser"),
    ("DM-MIC", "DamageMechanism", "Microbiologically influenced corrosion (API 571)", 3, "UT scanning of low-flow zones"),
    ("DM-NAC", "DamageMechanism", "Naphthenic acid corrosion (API 571)", 3, "UT grid scanning"),
    ("DM-REFR", "DamageMechanism", "Refractory degradation (API 571)", 3, "Internal visual, external thermography"),
    ("PH-FOUL", "Phenomenon", "Fouling (heat-transfer surfaces)", 0, ""),
    ("PH-COKING", "Phenomenon", "Coke lay-down in heater coils", 0, ""),
]
SEVERITY = {m[0]: m[3] for m in MECHANISMS}
METHOD = {m[0]: m[4] for m in MECHANISMS}


def apply(b, reg_rows, tag_rows):
    for mid, cls, name, *_ in MECHANISMS:
        if mid not in b.nodes:
            b.node(mid, cls, name, "reference")
    eqs = {n["id"]: n for n in b.nodes.values() if n["cls"] == "EquipmentUnit"}
    _physics(b, eqs)
    _mechanisms(b, eqs)
    _groupings(b, eqs)
    _alert_limits(b)
    added = _safeguards(b, reg_rows, tag_rows)
    eqs.update(added)
    _rbi(b, eqs)
    _tanks(b, eqs)
    _turnaround(b, eqs)


# ----------------------------------------------------------------------------- helpers
def _fact(b, eq, key):
    return b.fact_value(eq, key)


def _material(b, eq, n):
    for k in ("shell_material", "coil_metallurgy", "tube_metallurgy", "material"):
        v = _fact(b, eq, k)
        if v:
            return v
    mc = _fact(b, eq, "material_class")
    return {"S-4": "CarbonSteel", "C-6": "SS410"}.get(mc, "CarbonSteel")


def _loops(b, eq):
    return {e["target"] for e in b.edges if e["source"] == eq and e["rel"] == "MEMBER_OF"}


def _item(b, eq, code):
    iid = f"{eq}-{code}"
    return iid if iid in b.nodes else eq


# ----------------------------------------------------------------------------- 1. physics
def _physics(b, eqs):
    for eid, n in eqs.items():
        onto = n["props"].get("onto_class")
        if onto in ("ShellAndTubeHX", "AirCooledHX"):
            b.edge(eid, "GOVERNED_BY", "EQ-DUTY"); b.edge(eid, "GOVERNED_BY", "EQ-FOUL")
        elif onto == "FiredHeater":
            b.edge(eid, "GOVERNED_BY", "EQ-HTREFF")
        elif onto == "CentrifugalPump":
            b.edge(eid, "GOVERNED_BY", "EQ-AFFINITY")
        elif onto == "FixedBedReactor":
            b.edge(eid, "GOVERNED_BY", "EQ-WABT")
    for pc in ("PC-102", "PC-202", "PC-302"):
        b.edge(pc, "GOVERNED_BY", "EQ-DEWPT")


# ----------------------------------------------------------------------------- 2. damage mechanisms
def _mechanisms(b, eqs):
    tan_max = max(b.fact_value(g, "tan") or 0 for g in ("CR-AL", "CR-BM", "CR-MUR"))
    ppH2 = {r: b.fact_value(next(n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint" and n["props"].get("equipment") == r
                                 and "partial pressure" in n["name"]), "latest_value") for r in ("R-401", "R-402")}
    hcu_ph2 = min(ppH2.values())
    b._gov = {}

    def link(target, dm, susceptibility, basis):
        b.edge(target, "SUBJECT_TO" if dm.startswith("PH-") else "SUSCEPTIBLE_TO", dm,
               source="RBI study 2024 (API 581)" if not dm.startswith("PH-") else "Energy review 2025",
               susceptibility=susceptibility, basis=basis)

    for eid, n in eqs.items():
        p = n["props"]
        cls = p["eq_class"]
        if cls not in STATIC:
            b.fact(eid, "rbi_scope", "Out of RBI scope (non-pressure-retaining equipment)", "", as_of=DESIGN_DATE,
                   src="RBI study 2024 (API 581)", owner="ROLE-CORR", method="declared")
            continue
        fluid = p["service_fluid"].lower()
        unit = p["plant_unit"]
        T = _fact(b, eid, "service_temperature") or 40
        mat = _material(b, eid, n)
        loops = _loops(b, eid)
        hydro = unit == "HCU-1" and any(k in fluid for k in ("hydrogen", "effluent", "feed", "recycle"))
        hc = any(k in fluid for k in HC)
        dms = []
        # overhead condensation: HCl / NH4Cl, wet H2S; FCC & coker overheads also NH4HS and carbonate
        ovh = {l for l in loops if l.endswith("-OVH")}
        if ovh:
            target = _item(b, eid, "TOPCLAD") if cls == "Column" and unit.startswith("CDU") else (
                _item(b, eid, "TR_TOP") if cls == "Column" else eid)
            if unit.startswith("CDU"):
                dms += [(target, "DM-HCL", "high"), (target, "DM-NH4CL", "high")]
            else:
                dms += [(target, "DM-NH4CL", "medium"), (target, "DM-NH4HS", "medium")]
            if mat == "CarbonSteel" and cls != "Column":
                dms.append((eid, "DM-WETH2S", "medium" if unit.startswith("CDU") else "high"))
            if unit == "FCC-1" and mat == "CarbonSteel":
                dms.append((eid, "DM-CARB", "medium"))
        if "CL-FCC-GCU" in loops and mat == "CarbonSteel":
            dms += [(eid, "DM-WETH2S", "high"), (eid, "DM-CARB", "medium")]
        if "CL-HCU-REAC" in loops:
            if cls == "Chemical injection package":
                dms.append((_item(b, eid, "QUILLI"), "DM-NH4HS", "high"))
            else:
                dms.append((_item(b, eid, "TUBES") if cls == "Air cooler" else eid, "DM-NH4HS", "high"))
                if mat == "CarbonSteel":
                    dms.append((eid, "DM-WETH2S", "high"))
        if "sour water" in fluid and mat == "CarbonSteel":
            dms.append((eid, "DM-WETH2S", "medium"))
        # hydrogen service
        if hydro and mat in LOW_ALLOY_HTHA and T >= 204 and hcu_ph2 >= 3.45:
            dms.append((eid, "DM-HTHA", "low" if mat == "Cr225Mo" else "high"))
        if hydro and T >= 260:
            dms.append((eid, "DM-H2H2S", "medium"))
        if mat in AUSTENITIC and (hydro or T >= 260):
            dms.append((eid, "DM-PTA", "medium"))
        if mat in ("Cr225Mo", "Cr125Mo") and 343 <= T <= 577:
            dms.append((eid, "DM-TE", "medium"))
        # hot hydrocarbon outside hydrogen service
        if not hydro and hc and T >= 260 and mat not in AUSTENITIC and cls not in ("FCC reactor", "FCC regenerator"):
            dms.append((eid, "DM-SULF", "medium" if mat in ("Cr5", "Cr9", "Cr125Mo", "SS410") else "high"))
        if unit.startswith("CDU") and hc and 220 <= T <= 400 and cls not in ("FCC reactor",):
            dms.append((eid, "DM-NAC", "low" if tan_max < 0.5 else "high"))
        if cls == "Fired heater":
            dms += [(eid, "DM-CREEP", "medium"), (_item(b, eid, "CTUBES"), "DM-FGDP", "low")]
            if unit == "DCU-1":
                dms.append((eid, "PH-COKING", "high"))
        if cls == "Boiler":
            dms.append((_item(b, eid, "ECOT"), "DM-FGDP", "medium"))
        if cls == "Coke drum":
            dms += [(_item(b, eid, "SHELL"), "DM-TFAT", "high"), (_item(b, eid, "SKIRT"), "DM-TFAT", "high")]
        if eid == "PC-502":
            dms.append((eid, "DM-TFAT", "medium"))
        if "CL-FCC-CAT" in loops or "slurry" in fluid or cls == "Decoking system":
            target = _item(b, eid, "NOZZ") if cls == "Decoking system" else eid
            dms.append((target, "DM-EROSION", "high" if "CL-FCC-CAT" in loops else "medium"))
        if cls in ("FCC reactor", "FCC regenerator"):
            dms.append((eid, "DM-REFR", "medium"))
        if "caustic" in fluid:
            dms.append((_item(b, eid, "QUILLI"), "DM-CAUSTIC", "medium"))
        if any(l.endswith("-DES") for l in loops) or "brine" in fluid or "wash water" in fluid:
            dms.append((eid, "DM-MIC", "low"))
        if cls == "Storage tank":
            dms.append((eid, "DM-TANKFLOOR", "medium"))
        if mat in ("CarbonSteel", "Cr125Mo", "Cr5") and 50 <= T <= 175 and cls in (
                "Vessel", "Column", "Heat exchanger", "Piping circuit", "Side stripper", "Desalter"):
            dms.append((eid, "DM-CUI", "medium"))
        if cls == "Heat exchanger" and any(k in fluid for k in ("crude", "residue", "slurry", "vacuum")):
            dms.append((eid, "PH-FOUL", "high" if eid[3:5] in ("09", "10", "11", "12") else "medium"))
        seen = set()
        dms = [x for x in dms if not (x in seen or seen.add(x))]
        real = [x for x in dms if not x[1].startswith("PH-")]
        for target, dm, sus in dms:
            link(target, dm, sus, f"material {mat}, {T:.0f} °C, {p['service_fluid']}")
        if real:
            gov = max(real, key=lambda x: (SEVERITY[x[1]], {"high": 3, "medium": 2, "low": 1}[x[2]]))
            b.fact(eid, "governing_mechanism", b.nodes[gov[1]]["name"], "", as_of=DESIGN_DATE, src="RBI study 2024 (API 581)",
                   owner="ROLE-CORR", method="declared")
            b._gov[eid] = gov
        else:
            b.fact(eid, "rbi_screening_result", "No credible active damage mechanism (screened)", "", as_of=DESIGN_DATE,
                   src="RBI study 2024 (API 581)", owner="ROLE-CORR", method="declared")


# ----------------------------------------------------------------------------- 3. rule-derived groupings
def _groupings(b, eqs):
    def grp(gid, cls, name, owner, members):
        if gid not in b.nodes:
            b.node(gid, cls, name, "grouping")
            b.edge(gid, "OWNED_BY", owner)
        for m in members:
            b.edge(m, "MEMBER_OF", gid)
    pumps = [e for e, n in eqs.items() if n["props"]["eq_class"] == "Pump"]
    grp("FLT-CHARGE", "Fleet", "Fleet: crude charge & transfer pumps", "ROLE-ROT",
        [p for p in pumps if "charge pump" in eqs[p]["name"].lower() and p.startswith("P-") and eqs[p]["props"]["plant_unit"].startswith("CDU")
         or "transfer pump" in eqs[p]["name"]])
    grp("FLT-HOT", "Fleet", "Fleet: hot-service pumps (≥ 260 °C, Plan 53B)", "ROLE-ROT",
        [p for p in pumps if (b.fact_value(p, "service_temperature") or 0) >= 260])
    grp("FLT-COMP", "Fleet", "Fleet: process compressors, expanders & steam turbines", "ROLE-ROT",
        [e for e, n in eqs.items() if n["props"]["eq_class"] in ("Compressor", "Expander", "Steam turbine")])
    grp("FLT-HVMOTOR", "Fleet", "Fleet: HV motors (≥ 300 kW)", "ROLE-ELEC",
        [e for e, n in eqs.items() if n["props"]["eq_class"] == "Electric motor" and (b.fact_value(e, "rated_power") or 0) >= 300])
    # criticality and sparing of rotating equipment (reliability strategy)
    for e, n in sorted(eqs.items()):
        cls = n["props"]["eq_class"]
        if cls not in ("Pump", "Compressor", "Expander", "Steam turbine"):
            continue
        base = e[:-1] if e[-1] in "ABC" else e
        spared = sum(1 for x in eqs if x != e and x[:-1] == base and x[-1] in "ABC") > 0
        T = b.fact_value(e, "service_temperature") or 40
        fluid = n["props"]["service_fluid"].lower()
        crit = "A" if (cls != "Pump" or not spared or T >= 260 or any(k in fluid for k in ("sour", "lpg", "hydrogen"))) else (
            "B" if any(k in fluid for k in HC) else "C")
        src = dict(as_of=DESIGN_DATE, src="Reliability strategy (criticality assessment 2025)", owner="ROLE-ROT", method="declared")
        b.fact(e, "criticality", crit, "", **src)
        b.fact(e, "sparing", "Installed spare" if spared else "Unspared — critical spares held", "", **src)
        b.fact(e, "critical_spares", "Seal cartridge x1, bearing set x1" if cls == "Pump" else "Rotor, dry gas seals, bearing set", "", **src)
    b.node("UT-FUELGAS", "Utility", "Utility: refinery fuel gas (fired equipment)", "grouping")
    b.edge("UT-FUELGAS", "OWNED_BY", "ROLE-ENERGY")
    for e, n in eqs.items():
        if n["props"]["eq_class"] in ("Fired heater",):
            b.edge(e, "MEMBER_OF", "UT-FUELGAS")


# ----------------------------------------------------------------------------- 4. condition-monitoring limits
def _alert_limits(b):
    for n in [n for n in b.nodes.values() if n["cls"] == "DataPoint" and n["props"].get("tag_type") == "VI"]:
        eq = b.nodes.get(n["props"].get("equipment"), {"props": {}})
        cls = eq["props"].get("eq_class", "")
        unit = n["props"]["unit"]
        if unit == "mm/s":
            alert, danger, std = (8.0, 11.2, "ISO 20816-8 (reciprocating)") if cls == "Compressor" else (
                (6.3, 9.5, "ISO 20816-3 (fans / gearboxes)") if cls in ("Air cooler", "Crusher") else
                (4.5, 7.1, "ISO 20816-3 zone B/C"))
        else:
            rpm = b.fact_value(eq.get("id", ""), "speed") or 9000
            accept = min(25.4, 25.4 * (12000 / rpm) ** 0.5)
            alert, danger, std = round(accept * 1.5, 0), round(accept * 2.5, 0), "API 617 acceptance x 1.5 / 2.5 (API 670)"
        b.fact(n["id"], "alert_limit", alert, unit, as_of=DESIGN_DATE, src=f"Condition monitoring standard ({std})", owner="ROLE-ROT",
               method="declared")
        b.fact(n["id"], "danger_limit", danger, unit, as_of=DESIGN_DATE, src=f"Condition monitoring standard ({std})", owner="ROLE-ROT",
               method="declared")


# ----------------------------------------------------------------------------- 5. relief, SIF, valves, electrical
ORIFICES = [("J", 1.287), ("K", 1.838), ("L", 2.853), ("M", 3.60), ("N", 4.34), ("P", 6.38), ("Q", 11.05), ("R", 16.0), ("T", 26.0)]


def _safeguards(b, reg_rows, tag_rows):
    N, E, F = b.node, b.edge, b.fact
    before = set(b.nodes)
    eqs = {n["id"]: n for n in b.nodes.values() if n["cls"] == "EquipmentUnit"}
    counters = {}
    # relief devices on columns, drums, desalters, coke drums and the FCC reactor
    for eid, n in sorted(eqs.items()):
        p = n["props"]
        if p["eq_class"] not in ("Column", "Vessel", "Desalter", "Coke drum", "FCC reactor"):
            continue
        unit = p["plant_unit"]
        t = {"CDU-A": "1", "CDU-B": "2", "CDU-COM": "9", "FCC-1": "3", "HCU-1": "4", "DCU-1": "5"}.get(unit)
        if not t:
            continue
        counters[t] = counters.get(t, 0) + 1
        pid = f"PSV-{t}{counters[t]:02d}"
        dp = b.fact_value(eid, "design_pressure") or 3.5
        size = (b.fact_value(eid, "diameter") or 3) * (b.fact_value(eid, "height") or b.fact_value(eid, "length") or 10)
        letter, area = ORIFICES[min(len(ORIFICES) - 1, int(size / 40))]
        fouling = any(k in p["service_fluid"].lower() for k in ("sour", "overhead", "residue", "coke", "crude"))
        case = "Fire" if p["eq_class"] in ("Vessel", "Desalter") else ("Reflux failure" if p["eq_class"] == "Column" else "Blocked outlet")
        section = next(e["target"] for e in b.edges if e["source"] == eid and e["rel"] == "PART_OF")
        e = dict(id=pid, name=f"{pid} Pressure relief valve for {eid}", section=section, tpl="psv", fluid=p["service_fluid"],
                 train=p.get("train"), ctx={},
                 design=dict(set_pressure=dp, relief_case=case, orifice=letter, relief_capacity=round(area * 11000 * (dp + 1) ** 0.5, -2),
                             discharge_to="Flare header", service_temperature=b.fact_value(eid, "service_temperature") or 40))
        _build_equipment(b, e, reg_rows, tag_rows)
        E(pid, "PROTECTS", eid)
        last = LAST_TA.get(unit, "2023-10-15")
        interval = 36 if fouling else 60
        F(pid, "last_test_date", last, "", as_of=last, src="PSV test records (CMMS)", owner="ROLE-INST", method="recorded")
        F(pid, "test_interval", interval, "months", as_of=DESIGN_DATE, src="PSV inspection programme (API 576)", owner="ROLE-INST",
          method="declared")
        nd = _add_months(last, interval)
        b.fact(pid, "next_test_due", nd, "", as_of=AS_OF, src="KG derived", owner="ROLE-INST", method="calculated",
               lineage=[b.fact_obj(pid, "last_test_date")["id"], b.fact_obj(pid, "test_interval")["id"]])
    # SIF initiators (transmitters), final elements and attributes
    sif_final = {"SIF-A-HTR": [("XV-101", "H-101", "CDU-A-HTR", "Heater fuel-gas shutdown valve")],
                 "SIF-B-HTR": [("XV-201", "H-201", "CDU-B-HTR", "Heater fuel-gas shutdown valve")],
                 "SIF-DCU-HTR": [("XV-501", "H-501", "DCU-1-HTR", "Heater fuel-gas shutdown valve"),
                                 ("XV-502", "H-502", "DCU-1-HTR", "Heater fuel-gas shutdown valve")],
                 "SIF-HCU-DEP": [("BDV-401", "V-402", "HCU-1-SEP", "Emergency depressuring valve (7 bar/min)")],
                 "SIF-FCC-SV": []}
    sif_attr = {"SIF-A-HTR": (2, 0.005, 24, "2oo3", "Pass flow low-low", 40, "% of normal", 3),
                "SIF-B-HTR": (2, 0.005, 24, "2oo3", "Pass flow low-low", 40, "% of normal", 3),
                "SIF-DCU-HTR": (2, 0.005, 24, "2oo3", "Pass flow low-low", 45, "% of normal", 3),
                "SIF-HCU-DEP": (3, 0.0005, 12, "2oo3", "Bed outlet temperature high-high", 440, "degC", 5),
                "SIF-FCC-SV": (2, 0.005, 36, "1oo2", "Slide-valve differential pressure low-low", 0.14, "bar", 2)}
    for sif, finals in sif_final.items():
        members = [e["source"] for e in b.edges if e["rel"] == "MEMBER_OF" and e["target"] == sif]
        for tag in [m for m in members if b.nodes[m]["cls"] == "DataPoint"]:
            tp = b.nodes[tag]["props"]
            letters = {"FIC": "FT", "FI": "FT", "TI": "TT", "PDI": "PDT"}.get(tp["tag_type"], "XT")
            tx = f"{letters}-{tag.split('-', 1)[1]}"
            section = next(e["target"] for e in b.edges if e["source"] == tp["equipment"] and e["rel"] == "PART_OF")
            _build_equipment(b, dict(id=tx, name=f"{tx} Transmitter for {tag}", section=section, tpl="tx", fluid="Instrument",
                                     train=b.nodes[tp["equipment"]]["props"].get("train"), ctx={},
                                     design=dict(measurement=tp["tag_type"], sil_capable="SIL 2 (IEC 61508 certified)",
                                                 service_temperature=40)), reg_rows, tag_rows)
            E(tx, "SENSES", tag)
            E(tx, "MEMBER_OF", sif)
        for vid, protected, section, name in finals:
            _build_equipment(b, dict(id=vid, name=f"{vid} {name} ({protected})", section=section, tpl="xv", fluid="Fuel gas"
                                     if vid.startswith("XV") else "Hydrogen / hydrocarbon", train=b.nodes[protected]["props"].get("train"),
                                     ctx={}, design=dict(size='8"' if vid.startswith("XV") else '6"', fail_action="Fail closed"
                                                         if vid.startswith("XV") else "Fail open", stroke_time=4, service_temperature=40,
                                                         design_pressure=10.0 if vid.startswith("XV") else 185.0)), reg_rows, tag_rows)
            E(vid, "MEMBER_OF", sif)
        sil, pfd, pti, vote, desc, sp, unit, resp = sif_attr[sif]
        last = LAST_TA.get(b.nodes[members[0]]["props"].get("plant_unit", "CDU-A"), "2023-10-15")
        for k, v, u in [("sil", sil, ""), ("pfd_avg_target", pfd, "fraction"), ("proof_test_interval", pti, "months"),
                        ("voting", vote, ""), ("trip_function", desc, ""), ("trip_setpoint", sp, unit), ("response_time", resp, "s")]:
            F(sif, k, v, u, as_of=DESIGN_DATE, src="SIL verification report (IEC 61511)", owner="ROLE-INST", method="declared")
        F(sif, "last_proof_test", last, "", as_of=last, src="Proof-test records (CMMS)", owner="ROLE-INST", method="recorded")
        b.fact(sif, "next_proof_test_due", _add_months(last, pti), "", as_of=AS_OF, src="KG derived", owner="ROLE-INST",
               method="calculated", lineage=[b.fact_obj(sif, "last_proof_test")["id"], b.fact_obj(sif, "proof_test_interval")["id"]])
    # heater pass-flow control valves
    for h in ("H-101", "H-201", "H-301", "H-401", "H-501", "H-502"):
        section = next(e["target"] for e in b.edges if e["source"] == h and e["rel"] == "PART_OF")
        for tag in [n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint" and n["props"].get("equipment") == h
                    and n["props"]["tag_type"] == "FIC"]:
            fv = f"FV-{tag.split('-', 1)[1]}"
            out = b.fact_value(tag, "controller_output") or 55
            _build_equipment(b, dict(id=fv, name=f"{fv} Pass flow control valve ({tag})", section=section, tpl="cv", fluid="Heater charge",
                                     train=b.nodes[h]["props"].get("train"), ctx=dict(pos=out),
                                     design=dict(size='6"', trim="Equal percentage, hardened", cv_rated=520, fail_action="Fail open",
                                                 design_pressure=40.0, service_temperature=b.fact_value(h, "service_temperature") or 300)),
                             reg_rows, tag_rows)
            E(fv, "CONTROLS", tag)
    # electrical distribution
    for unit, sid in [("CDU-COM", "SS-10"), ("FCC-1", "SS-31"), ("HCU-1", "SS-41"), ("DCU-1", "SS-22")]:
        sec = f"{unit}-ELE"
        N(sec, "SectionSystem", "Electrical distribution", "asset", 5, unit, onto_class="ElectricalSection")
        units = ("CDU-A", "CDU-B", "CDU-COM", "TF-1") if unit == "CDU-COM" else (unit,)
        mw = sum(b.fact_value(u, "power_demand") or 0 for u in units)
        _build_equipment(b, dict(id=sid, name=f"{sid} Substation ({unit})", section=sec, tpl="substation", fluid="Electric power",
                                 train=None, ctx=dict(kv=6.6, mw=round(mw * (1 + jitter(sid, 0.03)), 1)),
                                 design=dict(voltage=6.6, transformer_mva=round(max(mw, 5) * 2.2, 0), service_temperature=35)),
                         reg_rows, tag_rows)
    return {i: b.nodes[i] for i in set(b.nodes) - before if b.nodes[i]["cls"] == "EquipmentUnit"}


def _add_months(d, months):
    y, m, dd = (int(x) for x in d.split("-"))
    m += months
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return date(y, m, min(dd, 28)).isoformat()


# ----------------------------------------------------------------------------- 6. RBI data
RISK = lambda pof, cof: "High" if pof + "ABCDE".index(cof) + 1 >= 9 else ("Medium-high" if pof + "ABCDE".index(cof) + 1 >= 7
                                                                           else ("Medium" if pof + "ABCDE".index(cof) + 1 >= 5 else "Low"))
INTERVAL = {"High": 24, "Medium-high": 48, "Medium": 72, "Low": 96}


def _rbi(b, eqs):
    F = b.fact
    src = "RBI database (API 581 study 2024)"
    for eid, n in sorted(eqs.items()):
        p = n["props"]
        if p["eq_class"] not in STATIC or p["eq_class"] in ("Pump", "Slide valve", "Decoking system", "Storage tank"):
            continue
        unit = p["plant_unit"]
        inst = INSTALL_YEAR.get(unit, 2004)
        F(eid, "install_date", f"{inst}-06-01", "", as_of=DESIGN_DATE, src="Asset register (CMMS)", owner="ROLE-MECH", method="declared")
        gov = getattr(b, "_gov", {}).get(eid)
        sev = SEVERITY.get(gov[1], 2) if gov else 1
        sus = {"high": 2, "medium": 1, "low": 0}[gov[2]] if gov else 0
        cr = None
        probe = next((x["id"] for x in b.nodes.values() if x["cls"] == "DataPoint" and x["props"].get("equipment") == eid
                      and "Corrosion probe" in x["name"]), None)
        if probe:
            cr = b.fact_value(probe, "latest_value")
        pof = max(1, min(5, round(sev / 3 + sus + (1 if (cr or 0) > 0.15 else 0) + jitter(eid + "pof", 0.4))))
        fluid = p["service_fluid"].lower()
        T = b.fact_value(eid, "service_temperature") or 40
        ait_hot = T >= 260 and any(k in fluid for k in HC)
        cof = "E" if (ait_hot or "hydrogen" in fluid) else ("D" if ("sour" in fluid or "lpg" in fluid or "naphtha" in fluid) else
                                                           ("C" if any(k in fluid for k in HC) else "B"))
        pf = F(eid, "pof_category", pof, "", as_of="2024-06-30", src=src, owner="ROLE-CORR", method="recorded", conf="medium")
        cf = F(eid, "cof_category", cof, "", as_of="2024-06-30", src=src, owner="ROLE-CORR", method="recorded", conf="medium")
        risk = RISK(pof, cof)
        rf = b.fact(eid, "risk_category", risk, "", as_of=AS_OF, src="KG derived", owner="ROLE-CORR", method="calculated", lineage=[pf, cf])
        last = LAST_TA.get(unit, "2023-10-15")
        F(eid, "last_inspection_date", last, "", as_of=last, src="Inspection DB (RBI)", owner="ROLE-INSP", method="recorded")
        F(eid, "last_inspection_method", METHOD.get(gov[1], "External visual and UT spot readings") if gov else
          "External visual and UT spot readings", "", as_of=last, src="Inspection DB (RBI)", owner="ROLE-INSP", method="recorded")
        iv = F(eid, "inspection_interval", INTERVAL[risk], "months", as_of=AS_OF, src=src, owner="ROLE-INSP", method="recorded",
               conf="medium")
        b.fact(eid, "next_inspection_due", _add_months(last, INTERVAL[risk]), "", as_of=AS_OF, src="KG derived", owner="ROLE-INSP",
               method="calculated", lineage=[b.fact_obj(eid, "last_inspection_date")["id"], iv, rf])
        if p["eq_class"] == "Piping circuit":
            _piping_life(b, eid, inst, probe)


def _piping_life(b, eid, inst, probe):
    F = b.fact
    nominal, ca = b.fact_value(eid, "nominal_wall"), b.fact_value(eid, "corrosion_allowance") or 3.0
    tmin = round(nominal - ca, 1)
    tf = F(eid, "tmin", tmin, "mm", as_of=DESIGN_DATE, src="ASME B31.3 retirement thickness (EDMS calc)", owner="ROLE-MECH",
           method="declared")
    tml_tag = next(x["id"] for x in b.nodes.values() if x["cls"] == "DataPoint" and x["props"].get("equipment") == eid
                   and "Minimum wall" in x["name"])
    t_now = b.fact_value(tml_tag, "latest_value")
    age = 2026 - inst
    lt_rate = (nominal - t_now) / age
    ltf = b.fact(eid, "long_term_corrosion_rate", round(lt_rate, 3), "mm/y", as_of=AS_OF, src="KG derived", owner="ROLE-CORR",
                 method="calculated", lineage=[b.fact_obj(eid, "nominal_wall")["id"], b.fact_obj(tml_tag, "latest_value")["id"]])
    cr = max(lt_rate, b.fact_value(probe, "latest_value") if probe else 0)
    lin = [b.fact_obj(tml_tag, "latest_value")["id"], tf, ltf] + ([b.fact_obj(probe, "latest_value")["id"]] if probe else [])
    b.fact(eid, "remaining_life", round((t_now - tmin) / cr, 1) if cr > 0 else 99, "yr", as_of=AS_OF, src="KG derived",
           owner="ROLE-CORR", method="calculated", lineage=lin)
    # thickness monitoring locations with survey history (time-series facts, valid_from / valid_to)
    parent = f"{eid}-FITTINGS" if f"{eid}-FITTINGS" in b.nodes else eid
    surveys = [y for y in (2016, 2020, 2024) if y > inst] + [2026]
    for i, share in enumerate((1.0, 0.72, 0.5), start=1):
        tml = f"{eid}-TML{i}"
        b.node(tml, "Part", f"Thickness monitoring location {i}", "asset", 9, parent, onto_class="ThicknessMonitoringLocation")
        rate = lt_rate * share
        prev = None
        for y in surveys:
            d = f"{y}-10-01" if y != 2026 else "2026-09-15"
            nxt = None
            idx = surveys.index(y)
            if idx + 1 < len(surveys):
                nxt = f"{surveys[idx + 1]}-10-01" if surveys[idx + 1] != 2026 else "2026-09-15"
            v = round(nominal - rate * (y - inst) + (jitter(tml + str(y), 0.05) if i > 1 else 0), 2)
            f = b.fact(tml, "thickness", v, "mm", as_of=d, src="Inspection DB (RBI) — UT survey", ref=f"{tml}-{y}",
                       owner="ROLE-INSP", method="measured", valid_from=d, valid_to=nxt)
            prev = f


# ----------------------------------------------------------------------------- tanks (API 653)
def _tanks(b, eqs):
    for eid, n in sorted(eqs.items()):
        if n["props"]["eq_class"] != "Storage tank":
            continue
        crude = "Crude" in n["props"]["service_fluid"]
        last = "2019-05-01" if crude else "2021-03-01"
        interval = 120 if crude else 180
        rate = 0.12 if crude else 0.05
        yrs = 2026 - int(last[:4])
        F = b.fact
        F(eid, "floor_nominal_thickness", 8.0 if crude else 6.0, "mm", as_of=DESIGN_DATE, src="Equipment datasheet (EDMS)",
          owner="ROLE-MECH", method="declared")
        fl = F(eid, "floor_min_thickness", round((8.0 if crude else 6.0) - rate * 20 + jitter(eid, 0.3), 1), "mm", as_of=last,
               src="Inspection DB (API 653 internal)", owner="ROLE-INSP", method="measured")
        F(eid, "floor_corrosion_rate", rate, "mm/y", as_of=last, src="Inspection DB (API 653 internal)", owner="ROLE-INSP",
          method="measured", conf="medium")
        F(eid, "last_internal_inspection", last, "", as_of=last, src="Inspection DB (API 653 internal)", owner="ROLE-INSP", method="recorded")
        F(eid, "install_date", "2003-06-01", "", as_of=DESIGN_DATE, src="Asset register (CMMS)", owner="ROLE-MECH", method="declared")
        b.fact(eid, "next_internal_due", _add_months(last, interval), "", as_of=AS_OF, src="KG derived", owner="ROLE-INSP",
               method="calculated", lineage=[b.fact_obj(eid, "last_internal_inspection")["id"], fl])


# ----------------------------------------------------------------------------- 7. turnaround 2027
def _turnaround(b, eqs):
    N, E, F = b.node, b.edge, b.fact
    ta = "TA-2027"
    N(ta, "Turnaround", "TA-2027 FCC & hydrocracker complex turnaround", "event", date="2027-03-01")
    E(ta, "AT_SITE", SITE)
    for k, v, u in [("start_date", "2027-03-01", ""), ("end_date", TA_END, ""), ("duration", 45, "days"),
                    ("budget", 145_000_000, "USD")]:
        F(ta, k, v, u, as_of=AS_OF, src="Turnaround plan (TA-2027 rev B)", owner="ROLE-MAINT", method="declared", conf="medium")
    n = 0

    def scope(target, kind, driver, cost, days, lineage):
        nonlocal n
        n += 1
        sid = f"SI-2027-{n:03d}"
        N(sid, "ScopeItem", f"{sid} {kind}: {b.nodes[target]['name'].split(' ', 1)[0]}", "event", date="2027-03-01")
        E(sid, "IN_SCOPE_OF", ta)
        E(sid, "TARGETS", target)
        F(sid, "scope_type", kind, "", as_of=AS_OF, src="Turnaround plan (TA-2027 rev B)", owner="ROLE-MAINT", method="declared")
        F(sid, "scope_driver", driver, "", as_of=AS_OF, src="KG derived", owner="ROLE-MAINT", method="calculated", lineage=lineage)
        F(sid, "estimated_cost", cost, "USD", as_of=AS_OF, src="Turnaround plan (TA-2027 rev B)", owner="ROLE-MAINT", method="assumption",
          conf="low")
        F(sid, "estimated_duration", days, "days", as_of=AS_OF, src="Turnaround plan (TA-2027 rev B)", owner="ROLE-MAINT",
          method="assumption", conf="low")
    for eid, nd in sorted(eqs.items()):
        unit = nd["props"]["plant_unit"]
        if unit not in ("FCC-1", "HCU-1"):
            continue
        due = b.fact_obj(eid, "next_inspection_due") or b.fact_obj(eid, "next_test_due")
        if due and due["value"] <= TA_END:
            kind = "PSV overhaul & test" if eid.startswith("PSV") else "RBI inspection"
            scope(eid, kind, f"Due {due['value']}", 25_000 if eid.startswith("PSV") else 180_000, 4 if eid.startswith("PSV") else 12,
                  [due["id"]])
    scope("R-302", "Deferred repair", "FL-F01 secondary cyclone dipleg erosion (repair deferred)", 2_400_000, 30,
          [b.fact_obj("FL-F01", "repair_status")["id"]])
    for r in ("R-401", "R-402"):
        scope(r, "Catalyst replacement", "HCU catalyst end of run before TA-2027 window",
              9_500_000 if r == "R-402" else 6_800_000, 20, [b.fact_obj("HCU-1", "eor_wabt")["id"]])
    for sif in ("SIF-FCC-SV", "SIF-HCU-DEP"):
        due = b.fact_obj(sif, "next_proof_test_due")
        if due["value"] <= TA_END:
            member = next(e["source"] for e in b.edges if e["rel"] == "MEMBER_OF" and e["target"] == sif
                          and b.nodes[e["source"]]["cls"] == "EquipmentUnit")
            scope(member, "SIF proof test", f"{sif} due {due['value']}", 40_000, 2, [due["id"]])
