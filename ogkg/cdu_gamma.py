"""
Refinery Gamma — complete CDU reference model (500 kbpd, two 250 kbpd trains).

Fictional site, synthetic data. Builds both sectors:
  Sector 1 (structure): L0-L10 asset hierarchy for both trains and common facilities,
      ISO 14224 decomposition of every equipment item, instrument tags, process spine,
      groupings (corrosion loops, pumparound circuits, fleets, utilities, SIFs),
      roles, enterprise, location, applications, reference physics and models.
  Sector 2 (information): design data, tag configuration and latest values, IOW limits,
      crude slate, KPIs per train, 12-month event history.

Run:  python -m ogkg.cdu_gamma        -> data/cdu-gamma/{kg.json, *.csv}
"""
import csv
import json
from pathlib import Path

from .build_dataset import Builder
from .cdu_templates import ITEM_ONTO, TEMPLATES
from .refinery_units import CDU_DEST

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cdu-gamma"
AS_OF = "2026-09-28"
DESIGN_DATE = "2024-06-30"
SITE = "SITE-GAMMA"
TRAINS = {"A": 1, "B": 2}
CRUDE_KG_H = 1.42e6          # per train at 250 kbpd, ~860 kg/m3
CRUDE_M3_H = 1656            # per train


class GBuilder(Builder):
    SECTOR2 = {"CrudeCampaign", "Failure", "WorkOrder", "IOWExceedance"}

    def node(self, id, cls, name, spine, level=None, parent=None, desc="", **props):
        props.setdefault("sector", "2" if cls in self.SECTOR2 else ("1a" if spine == "reference" else "1b"))
        return super().node(id, cls, name, spine, level, parent, desc, **props)


# ----------------------------------------------------------------------------- equipment catalogue
def seal_plan(T, fluid):
    if T >= 260:
        return "Plan53B"
    if any(k in fluid.lower() for k in ("naphtha", "lpg")):
        return "Plan52"
    return "Plan11"


def pump_model(api_type, T):
    if api_type == "BB5":
        return ("OEM-C BB5-200H", "OEM-C")
    if api_type == "BB2":
        return ("OEM-A BB2-300", "OEM-A") if T < 200 else ("OEM-C BB2-250H", "OEM-C")
    return ("OEM-B OH2-150", "OEM-B") if T < 200 else ("OEM-B OH2-150H", "OEM-B")


def train_catalogue(tr):
    """Return (sections, equipment) for one train. tr = 'A' or 'B'."""
    t = str(TRAINS[tr])
    B = tr == "B"
    sec = lambda code: f"CDU-{tr}-{code}"
    sections = [
        ("CHG", "Crude charge system", "CrudeChargeSystem"),
        ("CPH", "Cold preheat train", "ColdPreheatTrain"),
        ("DES", "Desalting system (2-stage electrostatic)", "DesalterSystem"),
        ("HPH", "Hot preheat train", "HotPreheatTrain"),
        ("PFL", "Preflash system", "PreflashSystem"),
        ("HTR", "Crude heater system", "HeaterSystem"),
        ("FRC", "Atmospheric fractionation", "AtmosphericFractionation"),
        ("PAR", "Pumparound circuits", "PumparoundSystem"),
        ("OVH", "Overhead system", "OverheadSystem"),
        ("RDN", "Product rundown & cooling", "ProductRundownSystem"),
        ("CHM", "Chemical injection", "ChemicalInjectionSystem"),
        ("STB", "Naphtha stabiliser", "NaphthaStabiliserSystem"),
    ]
    eq = []

    # pumps: nn, letters, name, section, fluid, T, flow each (m3/h), head (m), API type, running letters, extra ctx
    pumps = [
        ("01", "ABC", "Crude charge pump", "CHG", "Crude", 40, 830, 260, "BB2", "AB"),
        ("02", "AB", "Desalter wash-water pump", "DES", "Wash water", 95, 110, 120, "OH2", "A"),
        ("03", "AB", "Desalted crude booster pump", "HPH", "Desalted crude", 135, 1660, 180, "BB2", "A"),
        ("04", "AB", "Preflash bottoms pump", "PFL", "Topped crude", 272, 1550, 220, "BB2", "A"),
        ("05", "AB", "Kerosene product pump", "FRC", "Kerosene", 190, 200, 120, "OH2", "A"),
        ("06", "AB", "Diesel product pump", "FRC", "Diesel", 255, 330, 130, "OH2", "A"),
        ("07", "AB", "AGO product pump", "FRC", "Atmospheric gas oil", 330, 116, 140, "OH2", "A"),
        ("08", "AB", "Atmospheric residue pump", "FRC", "Atmospheric residue", 350, 660, 160, "BB2", "A"),
        ("09", "AB", "Top pumparound pump", "PAR", "Top pumparound", 150, 700, 90, "OH2", "A"),
        ("10", "AB", "Diesel pumparound pump", "PAR", "Diesel pumparound", 240, 900, 100, "BB2", "A"),
        ("11", "AB", "Bottom pumparound pump", "PAR", "Bottom pumparound", 300, 800, 110, "BB2", "A"),
        ("12", "AB", "Overhead reflux pump", "OVH", "Naphtha reflux", 40, 600, 90, "OH2", "A"),
        ("13", "AB", "Naphtha product pump", "OVH", "Unstabilised naphtha", 40, 350, 120, "OH2", "A"),
        ("14", "AB", "Sour water pump", "OVH", "Sour water", 40, 60, 60, "OH2", "A"),
        ("15", "AB", "Stabiliser reflux pump", "STB", "LPG", 45, 80, 110, "OH2", "A"),
    ]
    for nn, letters, name, s, fluid, T, flow, head, api, running in pumps:
        for L in letters:
            pid = f"P-{t}{nn}{L}"
            model, oem = pump_model(api, T)
            plan = seal_plan(T, fluid)
            motor_kw = int(round(850 * 9.81 * flow / 3600 * head / 0.72 / 1000 / 10.0) * 10 + 20)
            vib = 2.4
            if pid == "P-101C":
                vib = 3.9      # bad actor after two seal failures
            if pid == "P-208A":
                vib = 3.4
            op_T = 258 if (B and nn == "04") else T      # Train B runs colder after the fouled hot preheat
            eq.append(dict(id=pid, name=f"{pid} {name} {L}", section=sec(s), tpl="pump", fluid=fluid,
                           ctx=dict(T=op_T, flow=flow, head=head, running=L in running, seal_plan=plan,
                                    motor_kw=motor_kw, vib=vib, suction_barg=2.0),
                           design=dict(model=model, oem=oem, api_610_type=api, rated_flow=flow, rated_head=head,
                                       service_temperature=T, seal_plan=plan, motor_power=motor_kw,
                                       material_class="S-4" if T < 200 else "C-6")))

    # shell-and-tube exchangers on the crude side (cold then hot preheat)
    crude_out_A = [65, 90, 110, 125, 135]
    hot_A = [170, 205, 225, 245, 260, 272]
    hot_B = [167, 199, 217, 234, 247, 258]
    cold = [("01", "Crude / kerosene product exchanger", "Kerosene product", 190, 110),
            ("02", "Crude / top pumparound exchanger", "Top pumparound", 150, 95),
            ("03", "Crude / diesel product exchanger", "Diesel product", 255, 150),
            ("04", "Crude / AGO product exchanger", "AGO product", 330, 180),
            ("05", "Crude / residue exchanger (cold end)", "Atmospheric residue", 205, 170)]
    tin = 40
    for (nn, name, hot, thin, thout), tout in zip(cold, crude_out_A):
        eq.append(_hx(t, nn, name, sec("CPH"), hot, tin, tout, thin, thout, "CarbonSteel", rf=0.18))
        tin = tout
    hot = [("07", "Crude / diesel pumparound exchanger", "Diesel pumparound", 240, 185, "CarbonSteel"),
           ("08", "Crude / bottom pumparound exchanger", "Bottom pumparound", 300, 225, "CarbonSteel"),
           ("09", "Crude / residue exchanger 1", "Atmospheric residue", 280, 245, "Cr5"),
           ("10", "Crude / residue exchanger 2", "Atmospheric residue", 300, 280, "Cr5"),
           ("11", "Crude / residue exchanger 3", "Atmospheric residue", 320, 300, "Cr5"),
           ("12", "Crude / residue exchanger 4", "Atmospheric residue", 350, 320, "Cr5")]
    tin = 135
    outs = hot_B if B else hot_A
    rf_B = [0.25, 0.32, 0.55, 0.62, 0.68, 0.71]
    for i, ((nn, name, hotf, thin, thout, met), tout) in enumerate(zip(hot, outs)):
        eq.append(_hx(t, nn, name, sec("HPH"), hotf, tin, tout, thin, thout, met, rf=rf_B[i] if B else 0.2))
        tin = tout
    eq.append(_hx(t, "06", "Wash-water / brine exchanger", sec("DES"), "Desalter brine", 30, 95, 135, 70, "CarbonSteel",
                  duty=7.5, cold_fluid="Wash water"))
    eq.append(_hx(t, "21", "Overhead trim cooler", sec("OVH"), "Overhead naphtha / water", 30, 38, 55, 40, "Titanium",
                  duty=9.0, cold_fluid="Cooling water"))
    for nn, name, hotf, thin, thout in [("30", "Kerosene rundown cooler", "Kerosene", 110, 45),
                                        ("31", "Diesel rundown cooler", "Diesel", 150, 55),
                                        ("32", "AGO rundown cooler", "AGO", 180, 70),
                                        ("33", "Residue rundown cooler", "Atmospheric residue", 245, 150)]:
        eq.append(_hx(t, nn, name, sec("RDN"), hotf, 30, 40, thin, thout, "CarbonSteel", duty=6.0, cold_fluid="Cooling water"))
    eq.append(_hx(t, "40", "Stabiliser reboiler", sec("STB"), "MP steam", 150, 160, 190, 185, "CarbonSteel", duty=6.5,
                  cold_fluid="Stabiliser bottoms"))
    eq.append(_hx(t, "41", "Stabiliser overhead condenser", sec("STB"), "LPG vapour", 30, 38, 62, 42, "CarbonSteel",
                  duty=5.0, cold_fluid="Cooling water"))

    # air coolers
    for L in "AB":
        eq.append(dict(id=f"E-{t}20{L}", name=f"E-{t}20{L} Overhead air cooler {L}", section=sec("OVH"), tpl="aircooler",
                       fluid="Overhead vapour", ctx=dict(Thin=128 if not B else 130, Thout=55),
                       design=dict(tube_metallurgy="CarbonSteel", bays=4, duty=38.0, service_temperature=128,
                                   design_temperature=180, design_pressure=5.0)))

    # desalters
    for nn, stage, salt in [("01", "1st-stage", 4.0), ("02", "2nd-stage", 0.8 if not B else 0.6)]:
        eq.append(dict(id=f"D-{t}{nn}", name=f"D-{t}{nn} {stage} desalter", section=sec("DES"), tpl="desalter",
                       fluid="Crude / wash water",
                       ctx=dict(T=135, P=12.0, salt_out=salt, grid_a=60.0 if not B else 55.0),
                       design=dict(diameter=4.3, length=33.0, design_temperature=160, design_pressure=16.0,
                                   transformer_kva=300, stage=stage, service_temperature=135)))

    # drums and columns
    eq.append(dict(id=f"V-{t}01", name=f"V-{t}01 Preflash drum", section=sec("PFL"), tpl="drum", fluid="Topped crude / vapour",
                   ctx=dict(T=272 if not B else 258, P=3.5),
                   design=dict(diameter=4.0, length=12.0, design_temperature=320, design_pressure=6.0,
                               shell_material="CarbonSteel", service_temperature=272)))
    eq.append(dict(id=f"V-{t}02", name=f"V-{t}02 Overhead receiver", section=sec("OVH"), tpl="receiver",
                   fluid="Naphtha / sour water",
                   ctx=dict(T=40, P=0.8, chloride=18.0 if not B else 9.0, ph=5.9 if not B else 6.2, iron=0.8 if not B else 0.4),
                   design=dict(diameter=4.5, length=14.0, design_temperature=90, design_pressure=5.0,
                               shell_material="CarbonSteel", service_temperature=40)))
    eq.append(dict(id=f"V-{t}03", name=f"V-{t}03 Stabiliser reflux drum", section=sec("STB"), tpl="drumboot", fluid="LPG",
                   ctx=dict(T=42, P=10.0),
                   design=dict(diameter=2.4, length=7.0, design_temperature=90, design_pressure=16.0,
                               shell_material="CarbonSteel", service_temperature=42)))
    eq.append(dict(id=f"C-{t}01", name=f"C-{t}01 Atmospheric column", section=sec("FRC"), tpl="atmcolumn", fluid="Crude fractions",
                   ctx=dict(top_t=128 if not B else 130, fz_t=362),
                   design=dict(diameter=9.5, height=58.0, trays=50, design_temperature=400, design_pressure=3.5,
                               shell_material="SS410", top_cladding="Alloy400", service_temperature=362)))
    for nn, name, T in [("02", "Kerosene side stripper", 190), ("03", "Diesel side stripper", 255), ("04", "AGO side stripper", 330)]:
        eq.append(dict(id=f"C-{t}{nn}", name=f"C-{t}{nn} {name}", section=sec("FRC"), tpl="stripper", fluid=name.split()[0],
                       ctx=dict(T=T), design=dict(diameter=2.2, height=12.0, trays=6, design_temperature=T + 40,
                                                  design_pressure=3.5, service_temperature=T)))
    eq.append(dict(id=f"C-{t}05", name=f"C-{t}05 Naphtha stabiliser", section=sec("STB"), tpl="stabiliser", fluid="Naphtha / LPG",
                   ctx=dict(T=160, P=10.0), design=dict(diameter=2.8, height=30.0, trays=30, design_temperature=200,
                                                        design_pressure=16.0, service_temperature=160)))

    # heater
    absorbed = 142.0 if not B else 155.0
    eff = 88.5 if not B else 87.9
    eq.append(dict(id=f"H-{t}01", name=f"H-{t}01 Crude heater", section=sec("HTR"), tpl="heater", fluid="Crude",
                   ctx=dict(flow=CRUDE_M3_H, cot=365.0, cit=272.0 if not B else 258.0,
                            tmt=[582, 586, 590, 584] if not B else [596, 601, 612, 598],
                            o2=2.8 if not B else 3.4, stack_t=160 if not B else 175,
                            absorbed_mw=absorbed, eff=eff, fired_mw=round(absorbed / (eff / 100), 1)),
                   design=dict(absorbed_duty=150.0, passes=4, coil_metallurgy="Cr9", design_tmt=650,
                               burners=24, design_efficiency=89.0, service_temperature=365)))

    # piping circuits
    eq.append(dict(id=f"PC-{t}01", name=f"PC-{t}01 Transfer line (heater to column)", section=sec("FRC"), tpl="piping",
                   fluid="Partially vaporised crude", ctx=dict(cr=0.05, wall=13.1),
                   design=dict(line_size='36"', material="Cr9", corrosion_allowance=3.0, nominal_wall=14.3,
                               service_temperature=365)))
    eq.append(dict(id=f"PC-{t}02", name=f"PC-{t}02 Overhead line circuit", section=sec("OVH"), tpl="ovhline",
                   fluid="Overhead vapour", ctx=dict(cr=0.18 if not B else 0.08, wall=7.2 if not B else 8.6,
                                                    dpm=16.0 if not B else 24.0),
                   design=dict(line_size='42"', material="CarbonSteel", corrosion_allowance=3.0, nominal_wall=9.5,
                               service_temperature=128)))
    eq.append(dict(id=f"PC-{t}03", name=f"PC-{t}03 Residue rundown circuit", section=sec("RDN"), tpl="piping",
                   fluid="Atmospheric residue", ctx=dict(cr=0.07, wall=10.9),
                   design=dict(line_size='16"', material="Cr5", corrosion_allowance=3.0, nominal_wall=12.7,
                               service_temperature=350)))

    # chemical injection packages
    for nn, name, chem, rate in [("01", "Neutraliser injection package", "Neutralising amine", 45.0 if not B else 38.0),
                                 ("02", "Filming inhibitor injection package", "Filming corrosion inhibitor", 8.0),
                                 ("03", "Overhead wash-water injection", "Wash water", 12000.0),
                                 ("04", "Caustic injection package", "Dilute caustic", 30.0),
                                 ("05", "Demulsifier injection package", "Demulsifier", 25.0)]:
        eq.append(dict(id=f"X-{t}{nn}", name=f"X-{t}{nn} {name}", section=sec("CHM"), tpl="chem", fluid=chem,
                       ctx=dict(rate=rate), design=dict(chemical=chem, design_rate=round(rate * 1.5, 1), service_temperature=40)))
    return sections, eq


def _hx(t, nn, name, section, hot, tin, tout, thin, thout, met, rf=0.2, duty=None, cold_fluid="Crude"):
    if duty is None:
        duty = round(CRUDE_KG_H * 2.3 * (tout - tin) / 3.6e6, 1)
    return dict(id=f"E-{t}{nn}", name=f"E-{t}{nn} {name}", section=section, tpl="shelltube", fluid=f"{cold_fluid} / {hot}",
                ctx=dict(Tin=tin, Tout=tout, Thin=thin, Thout=thout, duty=duty, rf=rf),
                design=dict(tema_type="AES" if cold_fluid == "Crude" else "BEM", duty=duty, tube_metallurgy=met,
                            design_temperature=max(thin, tout) + 30, design_pressure=25.0 if cold_fluid == "Crude" else 10.0,
                            service_temperature=thin, area=round(duty * 55, 0)))


def common_catalogue():
    eq = []
    for L in "ABCD":
        pid = f"P-001{L}"
        eq.append(dict(id=pid, name=f"{pid} Crude transfer pump {L}", section="CDU-COM-CFD", tpl="pump", fluid="Crude",
                       ctx=dict(T=35, flow=1100, head=90, running=L != "D", seal_plan="Plan11", motor_kw=390, vib=2.2),
                       design=dict(model="OEM-A BB2-300", oem="OEM-A", api_610_type="BB2", rated_flow=1100, rated_head=90,
                                   service_temperature=35, seal_plan="Plan11", motor_power=390, material_class="S-4")))
    eq.append(dict(id="V-901", name="V-901 Flare knock-out drum", section="CDU-COM-RLF", tpl="drumboot", fluid="Relief vapour / liquid",
                   ctx=dict(T=45, P=0.2), design=dict(diameter=4.5, length=15.0, design_temperature=200, design_pressure=3.5,
                                                      shell_material="CarbonSteel", service_temperature=45)))
    for L in "AB":
        pid = f"P-901{L}"
        eq.append(dict(id=pid, name=f"{pid} Flare KO drum pump {L}", section="CDU-COM-RLF", tpl="pump", fluid="Slop oil",
                       ctx=dict(T=45, flow=40, head=60, running=L == "A", seal_plan="Plan11", motor_kw=20, vib=2.0),
                       design=dict(model="OEM-B OH2-150", oem="OEM-B", api_610_type="OH2", rated_flow=40, rated_head=60,
                                   service_temperature=45, seal_plan="Plan11", motor_power=20, material_class="S-4")))
    for tid, name, chem in [("TK-901", "Neutraliser bulk storage tank", "Neutralising amine"),
                            ("TK-902", "Corrosion inhibitor bulk storage tank", "Filming corrosion inhibitor")]:
        eq.append(dict(id=tid, name=f"{tid} {name}", section="CDU-COM-CST", tpl="tank", fluid=chem, ctx=dict(level=70.0),
                       design=dict(capacity=0.35, capacity_unit="kbbl", diameter=4.0, height=4.5, roof_type="Fixed cone roof",
                                   service_temperature=35)))
    for i in range(1, 7):
        tid = f"TK-00{i}"
        eq.append(dict(id=tid, name=f"{tid} Crude storage tank {i}", section="TF-1-CRS", tpl="tank", fluid="Crude",
                       ctx=dict(level=[62, 48, 75, 30, 55, 81][i - 1]),
                       design=dict(capacity=600, capacity_unit="kbbl", diameter=78.0, height=20.0,
                                   roof_type="External floating roof", service_temperature=35)))
    return eq


# ----------------------------------------------------------------------------- build
def build():
    b = GBuilder()
    N, E, F = b.node, b.edge, b.fact
    reg_rows, tag_rows = [], []

    roles = {"ROLE-OPS": "Operations Superintendent (CDU)", "ROLE-PROC": "Process Engineer (CDU)",
             "ROLE-MECH": "Static Equipment Engineer", "ROLE-ROT": "Rotating Equipment Engineer",
             "ROLE-CORR": "Corrosion / Integrity Engineer", "ROLE-INSP": "Inspection Lead",
             "ROLE-LAB": "Laboratory Manager", "ROLE-PLAN": "Planning & Economics Lead",
             "ROLE-ENERGY": "Energy Engineer", "ROLE-MAINT": "Maintenance Manager",
             "ROLE-INST": "Instrument & Control Engineer"}
    for rid, rn in roles.items():
        N(rid, "Role", rn, "org")

    # --- enterprise, location, OEMs
    N("ENT-GAMMA", "Enterprise", "Gamma Refining Company (fictional)", "enterprise")
    for oem in ("OEM-A", "OEM-B", "OEM-C"):
        N(f"ENT-{oem}", "Enterprise", f"{oem} Pumps (fictional manufacturer)", "enterprise")
    N("LOC-REGION", "Region", "Coastal Region (fictional)", "location")
    for lid, ln in [("LOC-SITE", "Refinery Gamma site"), ("LOC-PLOT-A", "Plot 1A — CDU Train A"),
                    ("LOC-PLOT-B", "Plot 1B — CDU Train B"), ("LOC-PLOT-C", "Plot 1C — CDU common facilities"),
                    ("LOC-PLOT-TF", "Plot 9 — crude tank farm")]:
        N(lid, "Area" if lid == "LOC-SITE" else "Plot", ln, "location")
        E(lid, "WITHIN", "LOC-REGION" if lid == "LOC-SITE" else "LOC-SITE")

    # --- reference (Sector 1a): models, equations, damage mechanisms, application products
    for model, oem in [("OEM-A BB2-300", "OEM-A"), ("OEM-C BB2-250H", "OEM-C"), ("OEM-B OH2-150", "OEM-B"), ("OEM-B OH2-150H", "OEM-B")]:
        mid = "MOD-" + model.replace(" ", "-")
        N(mid, "EquipmentModel", model, "reference")
        E(mid, "MANUFACTURED_BY", f"ENT-{oem}")
    refs = [("EQ-DUTY", "Equation", "Heat duty  Q = U·A·ΔT_lm"), ("EQ-FOUL", "Equation", "Fouling resistance  R_f = 1/U_dirty − 1/U_clean"),
            ("EQ-HTREFF", "Equation", "Heater efficiency  η = Q_absorbed / Q_fired"), ("EQ-AFFINITY", "Equation", "Pump affinity  Q2/Q1 = N2/N1"),
            ("EQ-DEWPT", "Equation", "Overhead water dew point from water partial pressure"),
            ("DM-HCL", "DamageMechanism", "Hydrochloric acid corrosion (API 571)"),
            ("DM-NH4CL", "DamageMechanism", "Ammonium chloride corrosion (API 571)"),
            ("DM-NAC", "DamageMechanism", "Naphthenic acid corrosion (API 571)"),
            ("DM-SULF", "DamageMechanism", "High-temperature sulfidation (API 571)"),
            ("DM-CREEP", "DamageMechanism", "Creep / stress rupture (API 571)"),
            ("PH-FOUL", "Phenomenon", "Crude preheat fouling"),
            ("APP-CAT-HIST", "Application", "Process historian"), ("APP-CAT-DCS", "Application", "Distributed control system"),
            ("APP-CAT-APC", "Application", "Advanced process control"), ("APP-CAT-LIMS", "Application", "LIMS"),
            ("APP-CAT-CMMS", "Application", "CMMS / EAM"), ("APP-CAT-RBI", "Application", "Inspection / RBI database"),
            ("APP-CAT-LP", "Application", "LP planning model"), ("APP-CAT-EDMS", "Application", "Engineering document management")]
    for rid, cls, name in refs:
        N(rid, cls, name, "reference")

    # --- trunk and site
    N("OG", "Industry", "Oil & Gas", "trunk", 0)
    N("SEG-DOWNSTREAM", "Segment", "Downstream", "trunk", 1, "OG")
    N("BC-REF", "BusinessCategory", "Refining", "asset", 2, "SEG-DOWNSTREAM")
    N(SITE, "Installation", "Refinery Gamma", "asset", 3, "BC-REF", desc="Fictional 500 kbpd coastal refinery")
    E(SITE, "OPERATED_BY", "ENT-GAMMA"); E(SITE, "LOCATED_AT", "LOC-SITE")
    F(SITE, "crude_capacity", 500, "kbd", as_of=DESIGN_DATE, src="Asset register (CMMS)", ref=SITE, owner="ROLE-PLAN", method="declared")
    F(SITE, "cdu_trains", 2, "count", as_of=DESIGN_DATE, src="Asset register (CMMS)", owner="ROLE-PLAN", method="declared")
    F(SITE, "grm_fy2026", 7.40, "USD/bbl", src="Site economics (monthly close)", ref="GRM-GAMMA-FY26", owner="ROLE-PLAN",
      method="calculated", conf="medium")
    F(SITE, "fuel_price", 6.0, "USD/MMBtu", src="Planning assumption", owner="ROLE-PLAN", method="assumption", conf="low")

    # --- units (L4)
    units = [("CDU-A", "CDU Train A (250 kbpd)", "CrudeDistillationUnit", "LOC-PLOT-A", 250),
             ("CDU-B", "CDU Train B (250 kbpd)", "CrudeDistillationUnit", "LOC-PLOT-B", 250),
             ("CDU-COM", "CDU common facilities", "CommonFacilities", "LOC-PLOT-C", None),
             ("TF-1", "Crude tank farm", "TankFarm", "LOC-PLOT-TF", None)]
    for uid, un, onto, loc, cap in units:
        N(uid, "PlantUnit", un, "asset", 4, SITE, onto_class=onto, train=uid[-1] if uid in ("CDU-A", "CDU-B") else None)
        E(uid, "LOCATED_AT", loc)
        if cap:
            F(uid, "design_capacity", cap, "kbd", as_of=DESIGN_DATE, src="Process design basis", ref=f"DB-{uid}",
              owner="ROLE-PROC", method="declared")
    F("TF-1", "storage_capacity", 3600, "kbbl", as_of=DESIGN_DATE, src="Asset register (CMMS)", owner="ROLE-OPS", method="declared")

    # --- sections (L5) and equipment
    common_sections = [("CDU-COM-CFD", "Crude feed system", "CrudeFeedSystem", "CDU-COM"),
                       ("CDU-COM-RLF", "Relief & flare knock-out", "ReliefSystem", "CDU-COM"),
                       ("CDU-COM-CST", "Chemical storage", "ChemicalStorageSystem", "CDU-COM"),
                       ("TF-1-CRS", "Crude storage", "CrudeStorageSystem", "TF-1")]
    for sid, sn, onto, parent in common_sections:
        N(sid, "SectionSystem", sn, "asset", 5, parent, onto_class=onto)
    all_eq = []
    for tr in TRAINS:
        sections, eq = train_catalogue(tr)
        for code, sn, onto in sections:
            N(f"CDU-{tr}-{code}", "SectionSystem", f"{sn} (Train {tr})", "asset", 5, f"CDU-{tr}", onto_class=onto, train=tr)
        for e in eq:
            e["train"] = tr
        all_eq += eq
    for e in common_catalogue():
        e["train"] = None
        all_eq.append(e)

    loops = {}
    for e in all_eq:
        _build_equipment(b, e, reg_rows, tag_rows)

    # unit-level data points (L10 directly under L4) and lab product quality points
    for tr in TRAINS:
        u = f"CDU-{tr}"
        t = TRAINS[tr]
        kbd = 246 if tr == "A" else 238
        _tag(b, tag_rows, u, f"FI-{t}900", "FI", "Train crude charge (total)", "kbd", "sensor", kbd, tr, u)
        yields = dict(LPG=1.0, NAP=20.0, KERO=12.0, DSL=20.0, AGO=7.0, AR=40.0)
        for code, frac in yields.items():
            v = round(kbd * frac / 100, 1)
            _tag(b, tag_rows, u, f"FI-{t}9{list(yields).index(code) + 1}0", "FI", f"{code} product rate", "kbd", "sensor", v, tr, u)
        frc = f"CDU-{tr}-FRC"
        _tag(b, tag_rows, frc, f"LAB-{t}901", "AL", "Kerosene flash point (lab)", "degC", "lab", 43.0, tr, frc)
        _tag(b, tag_rows, frc, f"LAB-{t}902", "AL", "Diesel D86 T95 (lab)", "degC", "lab", 356.0 if tr == "A" else 352.0, tr, frc)
        _tag(b, tag_rows, frc, f"LAB-{t}903", "AL", "Naphtha final boiling point (lab)", "degC", "lab", 178.0, tr, frc)

    _material(b)
    _groupings(b)
    _process_spine(b)
    _applications(b)
    _information(b)
    from . import refinery_gamma          # whole refinery (v0.4.0): appended so CDU fact IDs stay stable
    refinery_gamma.extend(b, reg_rows, tag_rows)
    return b, reg_rows, tag_rows


def _build_equipment(b, e, reg_rows, tag_rows):
    N, E, F = b.node, b.edge, b.fact
    tpl = TEMPLATES[e["tpl"]]
    eid = e["id"]
    plant_unit = e["section"].rsplit("-", 1)[0]
    N(eid, "EquipmentUnit", e["name"], "asset", 6, e["section"], eq_class=tpl["eq_class"], onto_class=tpl["onto"],
      train=e["train"], service_fluid=e["fluid"], plant_unit=plant_unit)
    # design data (Sector 2 facts, declared)
    d = e["design"]
    rotating = tpl["eq_class"] in ("Pump", "Compressor", "Expander", "Crusher")
    src_ds, owner = "Equipment datasheet (EDMS)", ("ROLE-ROT" if rotating else "ROLE-MECH")
    units = dict(rated_flow="m3/h", rated_head="m", service_temperature="degC", motor_power="kW", duty="MW",
                 design_temperature="degC", design_pressure="barg", diameter="m", length="m", height="m",
                 transformer_kva="kVA", absorbed_duty="MW", design_tmt="degC", design_efficiency="%", area="m2",
                 corrosion_allowance="mm", nominal_wall="mm", design_rate="L/h", capacity=d.get("capacity_unit", ""),
                 rated_power="kW", rated_capacity="kNm3/h", catalyst_volume="m3", catalyst_inventory="t", design_wabt="degC",
                 power_rating="MW", steam_rating="t/h", drum_cycle_design="h", throughput_rating="t/h")
    for k, v in d.items():
        if k in ("oem", "capacity_unit"):
            continue
        src = "Asset register (CMMS)" if k in ("model", "api_610_type") else src_ds
        F(eid, k, v, units.get(k, ""), as_of=DESIGN_DATE, src=src, ref=f"DS-{eid}", owner=owner, method="declared")
    if "model" in d:
        E(eid, "OF_MODEL", "MOD-" + d["model"].replace(" ", "-"))
    # decomposition L7-L9
    codes = {}
    for scode, sname, items in tpl["subunits"]:
        sid = f"{eid}-{scode}"
        N(sid, "Subunit", sname, "asset", 7, eid)
        codes[scode] = sid
        for icode, iname, parts in items:
            iid = f"{eid}-{icode}"
            N(iid, "MaintainableItem", iname, "asset", 8, sid, onto_class=ITEM_ONTO.get(icode, "MaintainableItem"))
            codes[icode] = iid
            for pcode, pname in parts:
                pid = f"{eid}-{pcode}"
                N(pid, "Part", pname, "asset", 9, iid)
                codes[pcode] = pid
    # tags L10
    ctx = e["ctx"]
    t = e.get("tagbase") or TRAINS.get(e["train"], 0)
    measured = []          # latest-value facts of this equipment's measured tags (inputs to its calculations)
    for ttype, desc, unit, attach, kind, fn, cond in tpl["tags"]:
        if cond and not cond(ctx):
            continue
        value = fn(ctx)
        prefix = {"lab": "LAB", "calculated": "CALC", "inspection": "TML", "corrosion probe": "CR"}.get(kind, ttype)
        _tag.counter[t] = _tag.counter.get(t, t * 1000 if t else 9000) + 1
        tag_id = f"{prefix}-{_tag.counter[t]}"
        lineage = None
        if kind == "calculated":
            if "dew-point" in desc:     # from the column top temperature and pressure
                col = f"C-{t}01"
                lineage = [b.fact_obj(n["id"], "latest_value")["id"] for n in b.nodes.values()
                           if n["cls"] == "DataPoint" and n["props"].get("equipment") == col and "Column top" in n["name"]]
            else:
                lineage = list(measured)
        fid = _tag(b, tag_rows, codes.get(attach, eid), tag_id, ttype, f"{desc}", unit, kind, value, e["train"], eid, lineage)
        if kind not in ("calculated", "inspection", "corrosion probe"):
            measured.append(fid)
    reg_rows.append(dict(tag=eid, description=e["name"].split(" ", 1)[1], unit=plant_unit,
                         train=e["train"] or ("Common" if plant_unit in ("CDU-COM", "TF-1") else "-"),
                         section=b.nodes[e["section"]]["name"], equipment_class=tpl["eq_class"], ontology_class=tpl["onto"],
                         service=e["fluid"], **{k: v for k, v in d.items() if k not in ("oem", "capacity_unit")}))


def _tag(b, tag_rows, parent, tag_id, ttype, desc, unit, kind, value, train, eq, lineage=None):
    b.node(tag_id, "DataPoint", f"{tag_id} {desc}" + (f" ({eq})" if eq and eq != parent else ""),
           "asset", 10, parent, kind=kind, tag_type=ttype, unit=unit, train=train, equipment=eq)
    src = {"lab": "LIMS", "calculated": "KG derived (calculated)", "inspection": "Inspection DB (RBI)",
           "corrosion probe": "Corrosion monitoring system"}.get(kind, "PI historian")
    method = {"lab": "measured", "calculated": "calculated", "inspection": "measured"}.get(kind, "measured")
    b.fact(tag_id, "engineering_unit", unit, "", as_of=DESIGN_DATE, src="DCS / historian tag configuration", ref=tag_id,
           owner="ROLE-INST", method="declared")
    fid = b.fact(tag_id, "latest_value", round(float(value), 2), unit, as_of=AS_OF, src=src, ref=tag_id,
                 owner="ROLE-LAB" if kind == "lab" else "ROLE-OPS", method=method,
                 conf="high" if method == "measured" else "medium", lineage=lineage)
    if kind == "lab":
        b.fact(tag_id, "sampling_interval", 24 if "chloride" in desc.lower() or "iron" in desc.lower() else 8, "h",
               as_of=DESIGN_DATE, src="LIMS sampling schedule", owner="ROLE-LAB", method="declared")
    tag_rows.append(dict(tag=tag_id, description=desc, type=ttype, kind=kind, unit=unit, attached_to=parent,
                         equipment=eq, train=train or "Common", latest_value=round(float(value), 2), source=src))
    return fid


_tag.counter = {}


def _material(b):
    N, E, F = b.node, b.edge, b.fact
    grades = [("CR-AL", "Arab Light", 33.0, 1.9, 0.1, 5), ("CR-BM", "Basrah Medium", 29.0, 2.9, 0.2, 8),
              ("CR-MUR", "Murban", 40.0, 0.8, 0.05, 2)]
    for gid, gn, api, s, tan, salt in grades:
        N(gid, "CrudeGrade", gn, "material")
        for k, v, u in [("api_gravity", api, "degAPI"), ("sulfur", s, "wt%"), ("tan", tan, "mgKOH/g")]:
            F(gid, k, v, u, as_of="2026-06-30", src="Public assay (typical values)", owner="ROLE-PLAN", conf="medium", method="indicative")
        F(gid, "salt_content", salt, "PTB", as_of="2026-06-30", src="Synthetic demo assay", owner="ROLE-PLAN", conf="low", method="assumption")
    N("STR-CRUDE", "Stream", "Crude charge (blended)", "material")
    E("TF-1", "PRODUCES", "STR-CRUDE")
    for tr in TRAINS:
        E("STR-CRUDE", "FEEDS", f"CDU-{tr}")
        for code, name in [("LPG", "LPG"), ("OFFGAS", "Off-gas"), ("NAP", "Stabilised naphtha"), ("KERO", "Kerosene"),
                           ("DSL", "Diesel"), ("AGO", "Atmospheric gas oil"), ("AR", "Atmospheric residue"), ("SW", "Sour water")]:
            dest = CDU_DEST[code]
            sid = f"STR-{tr}-{code}"
            N(sid, "Stream", f"{name} (Train {tr})", "material", train=tr)
            E(f"CDU-{tr}", "PRODUCES", sid)
            E(sid, "FEEDS", dest)


def _groupings(b):
    N, E = b.node, b.edge
    def grp(gid, cls, name, owner, members):
        N(gid, cls, name, "grouping")
        E(gid, "OWNED_BY", owner)
        for m in members:
            E(m, "MEMBER_OF", gid)
    grp("GRP-CDU-COMPLEX", "Grouping", "CDU complex (2 trains + common)", "ROLE-OPS", ["CDU-A", "CDU-B", "CDU-COM"])
    for tr, t in TRAINS.items():
        grp(f"CL-{tr}-OVH", "CorrosionLoop", f"Corrosion loop: overhead (Train {tr})", "ROLE-CORR",
            [f"PC-{t}02", f"E-{t}20A", f"E-{t}20B", f"E-{t}21", f"V-{t}02", f"P-{t}12A", f"P-{t}12B",
             f"P-{t}13A", f"P-{t}13B", f"P-{t}14A", f"P-{t}14B", f"C-{t}01"])
        grp(f"CL-{tr}-HOT", "CorrosionLoop", f"Corrosion loop: hot crude & transfer line (Train {tr})", "ROLE-CORR",
            [f"H-{t}01", f"PC-{t}01", f"V-{t}01", f"P-{t}04A", f"P-{t}04B"] + [f"E-{t}{n}" for n in ("09", "10", "11", "12")])
        grp(f"CL-{tr}-RES", "CorrosionLoop", f"Corrosion loop: atmospheric residue (Train {tr})", "ROLE-CORR",
            [f"P-{t}08A", f"P-{t}08B", f"PC-{t}03", f"E-{t}33", f"C-{t}01"])
        grp(f"CL-{tr}-DES", "CorrosionLoop", f"Corrosion loop: desalter & brine (Train {tr})", "ROLE-CORR",
            [f"D-{t}01", f"D-{t}02", f"E-{t}06", f"P-{t}02A", f"P-{t}02B"])
        for code, name, pumps, ex in [("TOP", "top", "09", "02"), ("DSL", "diesel", "10", "07"), ("BTM", "bottom", "11", "08")]:
            grp(f"PA-{tr}-{code}", "Grouping", f"Pumparound circuit: {name} (Train {tr})", "ROLE-PROC",
                [f"P-{t}{pumps}A", f"P-{t}{pumps}B", f"E-{t}{ex}"])
        grp(f"SIF-{tr}-HTR", "SafetyInstrumentedFunction", f"SIF: heater low pass-flow trip (Train {tr})", "ROLE-INST",
            [f"H-{t}01"] + [n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint"
                            and n["props"].get("equipment") == f"H-{t}01" and "Pass" in n["name"] and "flow" in n["name"]])
        grp(f"CC-{tr}", "CostCentre", f"Cost centre: CDU Train {tr}", "ROLE-MAINT", [f"CDU-{tr}"])
    grp("CC-COM", "CostCentre", "Cost centre: CDU common & tank farm", "ROLE-MAINT", ["CDU-COM", "TF-1"])
    pumps = [n for n in b.nodes.values() if n["cls"] == "EquipmentUnit" and n["props"].get("eq_class") == "Pump"]
    grp("FLT-CHARGE", "Fleet", "Fleet: crude charge & transfer pumps", "ROLE-ROT",
        [p["id"] for p in pumps if "charge pump" in p["name"] or "transfer pump" in p["name"]])
    hot = [p["id"] for p in pumps if b.fact_value(p["id"], "service_temperature") >= 260]
    grp("FLT-HOT", "Fleet", "Fleet: hot-service pumps (≥ 260 °C, Plan 53B)", "ROLE-ROT", hot)
    grp("UT-STEAM", "Utility", "Utility: MP stripping steam", "ROLE-ENERGY",
        [f"C-{t}0{n}" for t in (1, 2) for n in (1, 2, 3, 4)] + ["E-140", "E-240"])
    grp("UT-FUELGAS", "Utility", "Utility: refinery fuel gas", "ROLE-ENERGY", ["H-101", "H-201"])
    grp("UT-CW", "Utility", "Utility: cooling water", "ROLE-ENERGY",
        [f"E-{t}{n}" for t in (1, 2) for n in ("21", "30", "31", "32", "33", "41")])

    # physics links (Sector 1b structure links to Sector 1a reference)
    for n in list(b.nodes.values()):
        if n["cls"] != "EquipmentUnit":
            continue
        eid, onto = n["id"], n["props"].get("onto_class")
        if onto in ("ShellAndTubeHX", "AirCooledHX"):
            E(eid, "GOVERNED_BY", "EQ-DUTY"); E(eid, "GOVERNED_BY", "EQ-FOUL")
        if onto == "FiredHeater":
            E(eid, "GOVERNED_BY", "EQ-HTREFF"); E(eid, "SUSCEPTIBLE_TO", "DM-CREEP", source="RBI study 2024")
        if onto == "CentrifugalPump":
            E(eid, "GOVERNED_BY", "EQ-AFFINITY")
        T = b.fact_value(eid, "service_temperature") or 0
        if any(m in (f"CL-A-OVH", f"CL-B-OVH") for m in b.targets(eid, "MEMBER_OF")):
            E(eid, "SUSCEPTIBLE_TO", "DM-HCL", source="RBI study 2024"); E(eid, "SUSCEPTIBLE_TO", "DM-NH4CL", source="RBI study 2024")
        if T >= 230 and any(k in n["props"].get("service_fluid", "") for k in ("crude", "Crude", "residue", "AGO", "gas oil", "pumparound", "Diesel")):
            E(eid, "SUSCEPTIBLE_TO", "DM-SULF", source="RBI study 2024")
        if eid.startswith(("PC-101", "PC-201", "PC-103", "PC-203", "H-")):
            E(eid, "SUSCEPTIBLE_TO", "DM-NAC", source="RBI study 2024")
        if eid[3:5] in ("09", "10", "11", "12") and onto == "ShellAndTubeHX":
            E(eid, "SUSCEPTIBLE_TO", "PH-FOUL", source="Energy review 2025")
    for t in (1, 2):
        E(f"PC-{t}02", "GOVERNED_BY", "EQ-DEWPT")


def _process_spine(b):
    N, E, F = b.node, b.edge, b.fact
    def p(pid, cls, name, level, parent, owner=None, **props):
        N(pid, cls, name, "process", level, parent, **props)
        if owner:
            E(pid, "OWNED_BY", owner)
    p("VS-C2P", "ValueStream", "Crude-to-Product (Hydrocarbon Supply Chain)", 2, "SEG-DOWNSTREAM")
    p("VS-P2M", "ValueStream", "Plan-to-Maintain (Asset Reliability & Integrity)", 2, "SEG-DOWNSTREAM")
    for gid, gn, vs, owner in [("PG-OPS", "Unit Operations", "VS-C2P", "ROLE-OPS"), ("PG-QUAL", "Product Quality", "VS-C2P", "ROLE-PROC"),
                               ("PG-EN", "Energy Management", "VS-C2P", "ROLE-ENERGY"), ("PG-INT", "Integrity Management", "VS-P2M", "ROLE-CORR"),
                               ("PG-REL", "Reliability Management", "VS-P2M", "ROLE-ROT")]:
        p(gid, "ProcessGroup", gn, 3, vs, owner)

    tags = [n for n in b.nodes.values() if n["cls"] == "DataPoint"]
    def tags_where(pred):
        return [n["id"] for n in tags if pred(n)]
    both = lambda s: [f"CDU-{tr}-{s}" for tr in TRAINS]

    chains = [
        dict(proc=("P-THRU", "Crude charge & throughput management", "PG-OPS", "ROLE-OPS", ["CDU-A", "CDU-B"]),
             steps=[("SP-RATE", "Charge-rate setting"), ("ACT-RATE", "Balance charge between trains"),
                    ("TSK-RATE", "Check heater, column and desalter limits"), ("DEC-RATE", "Set train charge rates"),
                    ("DOB-RATEPLAN", "Daily operating plan")],
             governs=["CDU-A", "CDU-B"],
             des=[("DE-CHARGE", "Train crude charge", "throughput", tags_where(lambda n: "Train crude charge" in n["name"]), None),
                  ("DE-TMTMARGIN", "Heater TMT margin", "integrity", tags_where(lambda n: "(TMT)" in n["name"]), None),
                  ("DE-COLDP", "Column pressure drop", "operations", tags_where(lambda n: "Column pressure drop" in n["name"]), None)]),
        dict(proc=("P-DESALT", "Desalter management", "PG-OPS", "ROLE-PROC", both("DES")),
             steps=[("SP-DESOP", "Desalter optimisation"), ("ACT-DES", "Tune wash water and mix-valve dP"),
                    ("TSK-DES", "Review salt, BS&W and oil-in-brine"), ("DEC-DES", "Adjust wash-water rate and mix-valve dP"),
                    ("DOB-DESLOG", "Desalter performance log")],
             governs=[f"D-{t}0{n}" for t in (1, 2) for n in (1, 2)],
             des=[("DE-SALTOUT", "Desalted crude salt", "crude quality", tags_where(lambda n: "Desalted crude salt" in n["name"]), 8),
                  ("DE-BSW", "Desalted crude BS&W", "crude quality", tags_where(lambda n: "BS&W" in n["name"]), 8),
                  ("DE-OIB", "Oil in brine", "environment", tags_where(lambda n: "Oil in brine" in n["name"]), None),
                  ("DE-GRIDAMP", "Desalter grid current", "operations", tags_where(lambda n: "Grid current" in n["name"]), None)]),
        dict(proc=("P-HTR", "Fired heater management", "PG-OPS", "ROLE-OPS", both("HTR")),
             steps=[("SP-HTROP", "Heater operation"), ("ACT-PASS", "Balance pass flows"), ("TSK-TMT", "Review TMT, COT and O2"),
                    ("DEC-COT", "Set COT and pass flows"), ("DOB-HTRLOG", "Heater operating log")],
             governs=["H-101", "H-201"],
             des=[("DE-COT", "Coil outlet temperature", "operations", tags_where(lambda n: "(COT)" in n["name"]), None),
                  ("DE-TMT", "Tube-metal temperature", "integrity", tags_where(lambda n: "(TMT)" in n["name"]), None),
                  ("DE-O2", "Flue-gas oxygen", "energy", tags_where(lambda n: "Flue-gas oxygen" in n["name"]), None),
                  ("DE-PASSFLOW", "Heater pass flow", "operations", tags_where(lambda n: n["name"].split(" ", 1)[1].startswith("Pass") and "flow" in n["name"]), None)]),
        dict(proc=("P-CUT", "Product cut-point control", "PG-QUAL", "ROLE-PROC", both("FRC")),
             steps=[("SP-CUT", "Cut-point optimisation"), ("ACT-CUT", "Adjust draws and pumparound duties"),
                    ("TSK-QUAL", "Review lab cut properties"), ("DEC-CUT", "Set cut-point targets"), ("DOB-SPEC", "Product specification sheet")],
             governs=["C-101", "C-201"],
             des=[("DE-KEROFLASH", "Kerosene flash point", "product quality", tags_where(lambda n: "Kerosene flash" in n["name"]), 8),
                  ("DE-DSLT95", "Diesel D86 T95", "product quality", tags_where(lambda n: "D86 T95" in n["name"]), 8),
                  ("DE-NAPFBP", "Naphtha final boiling point", "product quality", tags_where(lambda n: "Naphtha final" in n["name"]), 8)]),
        dict(proc=("P-ENERGY", "Preheat energy & fouling management", "PG-EN", "ROLE-ENERGY", both("CPH") + both("HPH")),
             steps=[("SP-ENG", "Preheat performance monitoring"), ("ACT-FOUL", "Track exchanger fouling"),
                    ("TSK-FOUL", "Rank exchangers by fouling penalty"), ("DEC-CLEAN", "Schedule exchanger cleaning"),
                    ("DOB-CLEANPLAN", "Exchanger cleaning plan")],
             governs=both("CPH") + both("HPH"),
             des=[("DE-CIT", "Heater inlet temperature (CIT)", "energy", tags_where(lambda n: "(CIT)" in n["name"]), None),
                  ("DE-RF", "Exchanger fouling resistance", "energy", tags_where(lambda n: "Fouling resistance" in n["name"]), None),
                  ("DE-FUELPRICE", "Fuel price", "economics", [], "fuel_price")]),
        dict(proc=("P-OVHCORR", "Overhead corrosion control (IOW)", "PG-INT", "ROLE-CORR", both("OVH")),
             steps=[("SP-IOW", "IOW monitoring & response"), ("ACT-IOW", "Review overhead IOWs"),
                    ("TSK-OVH", "Review chloride, pH, iron and dew-point margin daily"),
                    ("DEC-NEUT", "Adjust neutraliser, inhibitor and wash water"), ("DOB-IOWREG", "IOW register")],
             governs=both("OVH"),
             des=[("DE-CL", "Overhead water chloride", "integrity", tags_where(lambda n: "chloride" in n["name"]), 24),
                  ("DE-PH", "Overhead water pH", "integrity", tags_where(lambda n: "Boot water pH" in n["name"]), None),
                  ("DE-FE", "Overhead water iron", "integrity", tags_where(lambda n: "iron" in n["name"]), 24),
                  ("DE-DPM", "Water dew-point margin", "integrity", tags_where(lambda n: "dew-point margin" in n["name"]), None),
                  ("DE-CORRRATE", "Overhead corrosion rate", "integrity",
                   tags_where(lambda n: "Corrosion probe" in n["name"] and n["props"].get("equipment") in ("PC-102", "PC-202")), None)]),
        dict(proc=("P-ROTREL", "Rotating equipment reliability", "PG-REL", "ROLE-ROT", ["CDU-A", "CDU-B", "CDU-COM"]),
             steps=[("SP-ROT", "Condition monitoring"), ("ACT-COND", "Review pump condition"),
                    ("TSK-VIB", "Review vibration and bearing temperatures"), ("DEC-SWITCH", "Switch to standby / raise repair priority"),
                    ("DOB-FAILREC", "Failure record (ISO 14224)")],
             governs=["CDU-A", "CDU-B", "CDU-COM"],
             des=[("DE-VIB", "Pump vibration", "reliability", tags_where(lambda n: "bearing vibration" in n["name"]), None),
                  ("DE-BRGT", "Pump bearing temperature", "reliability", tags_where(lambda n: "Thrust bearing temperature" in n["name"]), None),
                  ("DE-MTBF", "MTBF by pump service", "reliability", [], "mtbf_days")]),
    ]
    for ch in chains:
        pid, pn, pg, owner, acts = ch["proc"]
        p(pid, "Process", pn, 4, pg, owner)
        for a in acts:
            E(pid, "ACTS_ON", a)
        prev = pid
        for lvl, (sid, sn) in zip(range(5, 10), ch["steps"]):
            cls = {5: "SubProcess", 6: "Activity", 7: "Task", 8: "DecisionPoint", 9: "DataObject"}[lvl]
            p(sid, cls, sn, lvl, prev)
            prev = sid
        dec, dob = ch["steps"][3][0], ch["steps"][4][0]
        for g in ch["governs"]:
            E(dec, "GOVERNS", g)
        for did, dn, domain, inst, extra in ch["des"]:
            maps = extra if isinstance(extra, str) else None
            p(did, "DataElement", dn, 10, dob, owner, domain=domain, maps_to_predicate=maps)
            if isinstance(extra, int):
                F(did, "freshness_sla", extra, "h", as_of=DESIGN_DATE, src="Data governance catalogue", owner=owner, method="declared")
            for tg in inst:
                E(did, "INSTANTIATED_BY", tg)
            E(dec, "CONSUMES", did)


def _applications(b):
    N, E = b.node, b.edge
    apps = [("APP-PI", "PI historian — Gamma", "APP-CAT-HIST", [SITE]), ("APP-DCS", "DCS — CDU complex", "APP-CAT-DCS", ["CDU-A", "CDU-B", "CDU-COM", "TF-1"]),
            ("APP-APC-A", "APC — CDU Train A", "APP-CAT-APC", ["CDU-A"]), ("APP-APC-B", "APC — CDU Train B", "APP-CAT-APC", ["CDU-B"]),
            ("APP-LIMS", "LIMS — Gamma", "APP-CAT-LIMS", [SITE]), ("APP-CMMS", "CMMS — Gamma", "APP-CAT-CMMS", [SITE]),
            ("APP-RBI", "Inspection / RBI — Gamma", "APP-CAT-RBI", [SITE]), ("APP-LP", "LP planning model — Gamma", "APP-CAT-LP", [SITE]),
            ("APP-EDMS", "Engineering documents — Gamma", "APP-CAT-EDMS", [SITE])]
    for aid, an, cat, scope in apps:
        N(aid, "ApplicationInstance", an, "application")
        E(aid, "INSTANCE_OF", cat)
        for s in scope:
            E(aid, "SCOPED_TO", s)
    for aid, procs in [("APP-DCS", ["P-THRU", "P-HTR", "P-DESALT"]), ("APP-APC-A", ["P-THRU", "P-CUT"]), ("APP-APC-B", ["P-THRU", "P-CUT"]),
                       ("APP-LIMS", ["P-CUT", "P-DESALT", "P-OVHCORR"]), ("APP-CMMS", ["P-ROTREL"]), ("APP-RBI", ["P-OVHCORR"]),
                       ("APP-PI", ["P-ENERGY", "P-HTR", "P-OVHCORR"]), ("APP-LP", ["P-THRU"])]:
        for pr in procs:
            E(aid, "SUPPORTS", pr)
    for aid, dob in [("APP-LIMS", "DOB-SPEC"), ("APP-CMMS", "DOB-FAILREC"), ("APP-RBI", "DOB-IOWREG"), ("APP-PI", "DOB-HTRLOG")]:
        E(aid, "SYSTEM_OF_RECORD_FOR", dob)


# ----------------------------------------------------------------------------- Sector 2 extras
def _information(b):
    N, E, F = b.node, b.edge, b.fact
    tagid = lambda eq, text: next(n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint"
                                  and n["props"].get("equipment") == eq and text in n["name"])
    # IOW limits
    for t in (1, 2):
        for text, key, v, u in [("chloride", "iow_limit_standard", 20, "ppm"), ("chloride", "iow_limit_critical", 50, "ppm")]:
            F(tagid(f"V-{t}02", text), key, v, u, as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-CORR", method="declared")
        F(tagid(f"V-{t}02", "Boot water pH"), "iow_limit_low", 5.5, "pH", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-CORR", method="declared")
        F(tagid(f"V-{t}02", "Boot water pH"), "iow_limit_high", 7.0, "pH", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-CORR", method="declared")
        F(tagid(f"V-{t}02", "iron"), "iow_limit_standard", 1.0, "ppm", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-CORR", method="declared")
        F(tagid(f"PC-{t}02", "dew-point margin"), "iow_limit_low", 14, "degC", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-CORR", method="declared")
        F(tagid(f"D-{t}02", "Desalted crude salt"), "iow_limit_standard", 1.0, "PTB", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-CORR", method="declared")
        F(tagid(f"D-{t}01", "Desalter temperature"), "iow_limit_low", 120, "degC", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-PROC", method="declared")
        F(tagid(f"D-{t}01", "Desalter temperature"), "iow_limit_high", 150, "degC", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-PROC", method="declared")
        for pz in range(1, 5):
            F(tagid(f"H-{t}01", f"Pass {pz} tube-metal"), "iow_limit_standard", 620, "degC", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-CORR", method="declared")
            F(tagid(f"H-{t}01", f"Pass {pz} tube-metal"), "iow_limit_critical", 650, "degC", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-CORR", method="declared")
            F(tagid(f"H-{t}01", f"Pass {pz} outlet"), "iow_limit_high", 370, "degC", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-PROC", method="declared")
        F(tagid(f"H-{t}01", "Flue-gas oxygen"), "iow_limit_low", 1.5, "vol%", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-PROC", method="declared")
        for pc in ("01", "02", "03"):
            F(tagid(f"PC-{t}{pc}", "Corrosion probe"), "iow_limit_standard", 0.25, "mm/y", as_of=DESIGN_DATE, src="IOW register (API 584)", owner="ROLE-CORR", method="declared")
    # pump vibration alert limits (condition monitoring, not IOW)
    for n in [n for n in b.nodes.values() if n["cls"] == "DataPoint" and "bearing vibration" in n["name"]]:
        F(n["id"], "alert_limit", 4.5, "mm/s", as_of=DESIGN_DATE, src="Condition monitoring standard", owner="ROLE-ROT", method="declared")

    # crude slate (campaigns) per train
    shares = {"CR-AL": 0.45, "CR-BM": 0.35, "CR-MUR": 0.20}
    for tr, kbd in (("A", 246), ("B", 238)):
        for g, sh in shares.items():
            cid = f"CMP-{tr}-{g[3:]}"
            N(cid, "CrudeCampaign", f"FY2026 slate — {b.nodes[g]['name']} (Train {tr})", "material",
              start="2025-10-01", end="2026-09-30", opportunity=False)
            E(cid, "OF_GRADE", g); E(cid, "PROCESSED_IN", f"CDU-{tr}"); E(cid, "DELIVERED_VIA", SITE)
            F(cid, "volume_processed", round(kbd * 365 * sh), "kbbl", as_of=AS_OF, src="Hydrocarbon accounting", ref=f"HA-{cid}",
              owner="ROLE-PLAN")
            F(cid, "slate_share", sh, "fraction", as_of=AS_OF, src="Crude schedule", owner="ROLE-PLAN")

    # KPIs per train (derived from tag facts, with lineage)
    fid = lambda tag, pred="latest_value": b.fact_obj(tag, pred)["id"]
    for tr, t in TRAINS.items():
        u = f"CDU-{tr}"
        charge_tag = f"FI-{t}900"
        cit_tag = tagid(f"H-{t}01", "(CIT)")
        eff_tag = tagid(f"H-{t}01", "Thermal efficiency")
        abs_tag = tagid(f"H-{t}01", "Absorbed duty")
        kbd = b.fact_value(charge_tag, "latest_value")
        absorbed, eff = b.fact_value(abs_tag, "latest_value"), b.fact_value(eff_tag, "latest_value")
        fired = round(absorbed / (eff / 100), 1)
        ei = round(fired * 3.412 * 24 / kbd, 1)
        F(u, "throughput_fy2026", kbd, "kbd", as_of=AS_OF, src="KG derived", owner="ROLE-OPS", method="calculated", conf="high", lineage=[fid(charge_tag)])
        F(u, "cit_fy2026", b.fact_value(cit_tag, "latest_value"), "degC", as_of=AS_OF, src="KG derived", owner="ROLE-ENERGY", method="calculated", lineage=[fid(cit_tag)])
        F(u, "heater_fired_duty", fired, "MW", as_of=AS_OF, src="KG derived", owner="ROLE-ENERGY", method="calculated", lineage=[fid(abs_tag), fid(eff_tag)])
        F(u, "energy_intensity", ei, "MMBtu/kbbl", as_of=AS_OF, src="KG derived", owner="ROLE-ENERGY", method="calculated",
          lineage=[fid(abs_tag), fid(eff_tag), fid(charge_tag)])
        F(u, "desalter_salt_removal", 96.5 if tr == "A" else 97.2, "%", as_of=AS_OF, src="LIMS monthly report", owner="ROLE-LAB", method="calculated")
        F(u, "overhead_chloride_avg_12m", 18.0 if tr == "A" else 9.0, "ppm", as_of=AS_OF, src="LIMS", owner="ROLE-CORR", method="calculated")
        F(u, "availability_fy2026", 98.9 if tr == "A" else 99.3, "%", as_of=AS_OF, src="Operations logbook", owner="ROLE-OPS", method="calculated")
        for code in ("LPG", "NAP", "KERO", "DSL", "AGO", "AR"):
            tg = next(n["id"] for n in b.nodes.values() if n["cls"] == "DataPoint" and n["name"].startswith(f"FI-{t}9") and f" {code} product rate" in n["name"])
            F(u, f"yield_{code.lower()}", round(b.fact_value(tg, "latest_value") / kbd * 100, 1), "vol%", as_of=AS_OF, src="KG derived",
              owner="ROLE-PROC", method="calculated", lineage=[fid(tg), fid(charge_tag)])

    # event history (Oct 2025 - Sep 2026)
    def iow(iid, tag, d, peak, dur, u):
        N(iid, "IOWExceedance", f"{iid} on {b.nodes[tag]['name']}", "event", date=d)
        E(iid, "ON_DATAPOINT", tag)
        F(iid, "peak_value", peak, u, as_of=d, src="PI historian / IOW monitor", ref=iid, owner="ROLE-CORR", method="measured")
        F(iid, "duration", dur, "days", as_of=d, src="PI historian / IOW monitor", ref=iid, owner="ROLE-CORR", method="measured")
    iow("IOW-A01", tagid("V-102", "chloride"), "2026-01-12", 42, 5, "ppm")
    iow("IOW-A02", tagid("V-102", "chloride"), "2026-04-03", 55, 8, "ppm")
    iow("IOW-A03", tagid("V-102", "chloride"), "2026-07-21", 38, 3, "ppm")
    iow("IOW-A04", tagid("PC-102", "dew-point margin"), "2026-04-05", 8, 6, "degC")
    iow("IOW-B01", tagid("H-201", "Pass 3 tube-metal"), "2026-06-02", 635, 4, "degC")
    iow("IOW-B02", tagid("H-201", "Pass 3 tube-metal"), "2026-08-15", 628, 2, "degC")

    grm = b.fact_obj(SITE, "grm_fy2026")
    def failure(fid_, target, d, mode, mech, cost, wo, rate_cut=0, days=0, desc=""):
        N(fid_, "Failure", f"{fid_} {b.nodes[target]['name']}", "event", date=d, desc=desc)
        E(fid_, "FAILURE_OF", target)
        F(fid_, "failure_mode", mode, "", as_of=d, src="CMMS (ISO 14224 coding)", ref=wo, owner="ROLE-MAINT")
        F(fid_, "failure_mechanism", mech, "", as_of=d, src="CMMS (ISO 14224 coding)", ref=wo, owner="ROLE-MAINT")
        N(wo, "WorkOrder", f"{wo} repair", "event", date=d)
        E(wo, "REMEDIATES", fid_)
        F(wo, "actual_cost", cost, "USD", as_of=d, src="CMMS", ref=wo, owner="ROLE-MAINT")
        if rate_cut:
            fr = F(fid_, "rate_reduction", rate_cut, "kbd", as_of=d, src="Operations logbook", owner="ROLE-OPS")
            fd = F(fid_, "rate_reduction_days", days, "days", as_of=d, src="Operations logbook", owner="ROLE-OPS")
            F(fid_, "lost_margin", round(rate_cut * 1000 * days * grm["value"]), "USD", as_of=d, src="KG derived", owner="ROLE-PLAN",
              method="calculated", conf="medium", lineage=[fr, fd, grm["id"]])
    failure("FL-A01", "E-120A-TUBES", "2026-05-02", "External leakage – process medium (ELP)",
            "Corrosion (ISO 14224 2.2) — ammonium chloride under-deposit", 240000, "WO-A01", 30, 3, "Air-cooler tube leak")
    failure("FL-A02", "P-101C-SEAL", "2025-12-10", "External leakage – process medium (ELP)", "Wear (ISO 14224 1.x)", 45000, "WO-A02")
    failure("FL-A03", "P-101C-SEAL", "2026-06-18", "External leakage – process medium (ELP)", "Wear (ISO 14224 1.x)", 45000, "WO-A03")
    failure("FL-A04", "D-102-TRAFO", "2026-02-14", "Loss of function (electrical field)",
            "Electrical — emulsion carry-over short", 30000, "WO-A04", desc="Grid trip; salt carry-over for 2 days")
    failure("FL-B01", "P-208A-SEAL", "2026-01-25", "External leakage – process medium (ELP)", "Wear / thermal distortion (ISO 14224 1.x)",
            60000, "WO-B01", 20, 1, "Hot residue seal leak; switched to standby")
    for wo, eqs, d, cost in [("WO-B02", ["E-207", "E-208"], "2026-03-10", 380000)]:
        N(wo, "WorkOrder", f"{wo} exchanger cleaning (E-207, E-208)", "event", date=d)
        for e_ in eqs:
            E(wo, "PERFORMED_ON", e_)
        F(wo, "actual_cost", cost, "USD", as_of=d, src="CMMS", ref=wo, owner="ROLE-MAINT")
        F(wo, "work_type", "Preventive — hydro-jet cleaning", "", as_of=d, src="CMMS", ref=wo, owner="ROLE-MAINT")


# ----------------------------------------------------------------------------- helpers on Builder
def _fact_obj(self, subject, predicate):
    for f in reversed(self.facts):
        if f["subject"] == subject and f["predicate"] == predicate:
            return f
    return None


def _fact_value(self, subject, predicate):
    f = _fact_obj(self, subject, predicate)
    return f["value"] if f else None


def _targets(self, nid, rel):
    return [e["target"] for e in self.edges if e["source"] == nid and e["rel"] == rel]


Builder.fact_obj = _fact_obj
Builder.fact_value = _fact_value
Builder.targets = _targets


def main():
    _tag.counter.clear()
    b, reg, tags = build()
    OUT.mkdir(parents=True, exist_ok=True)
    data = dict(meta=dict(name="Refinery Gamma — reference model (500 kbpd, Nelson complexity ≈ 15)", as_of=AS_OF,
                          disclaimer="Fictional refinery and synthetic engineering data for demonstration. Crude assays are "
                                     "indicative typical values. Not for design or operating decisions."),
                nodes=list(b.nodes.values()), edges=b.edges, facts=b.facts)
    (OUT / "kg.json").write_text(json.dumps(data, indent=1, default=str))
    keys = sorted({k for r in reg for k in r}, key=lambda k: (k not in ("tag", "description", "train", "section", "equipment_class",
                                                                       "ontology_class", "service"), k))
    with open(OUT / "equipment_register.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(reg)
    with open(OUT / "tag_register.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(tags[0].keys())); w.writeheader(); w.writerows(tags)
    print(f"nodes={len(b.nodes)} edges={len(b.edges)} facts={len(b.facts)} equipment={len(reg)} tags={len(tags)} -> {OUT}")


if __name__ == "__main__":
    main()
