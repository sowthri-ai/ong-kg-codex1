"""
Refinery Gamma — whole-refinery configuration (v0.4.0).

Everything outside the CDU that the reference model needs, as data:
  UNITS      every plant unit at L4 with its L5 sections, design capacity and Nelson factor
  STREAMS    inter-unit streams with FY2026 average rates (the refinery volume balance)
  H2_*       hydrogen consumption / yield per unit (the hydrogen network)
  SULFUR_*   sulfur fates (the sulfur balance)
  fcc_catalogue(), hcu_catalogue(), dcu_catalogue()
             full-depth (L6-L10) equipment for FCC-1, HCU-1 and DCU-1

Refinery Gamma is fictional and all numbers are synthetic engineering estimates.
Nelson factors are the 1998 values as published in public references (see NELSON_SOURCE).
"""

NELSON_SOURCE = "Nelson complexity factors, 1998 edition (public reference: Wikipedia 'Nelson complexity index')"
KBD_TO_M3H = 6.624          # 1 kbd = 158.99 m3/d = 6.624 m3/h

# plots (location backbone)
PLOTS = {
    "LOC-PLOT-2": "Plot 2 — Vacuum distillation & delayed coker",
    "LOC-PLOT-3": "Plot 3 — FCC complex (VGO hydrotreater, FCC)",
    "LOC-PLOT-4": "Plot 4 — Hydroprocessing (hydrocracker, diesel & kerosene HT)",
    "LOC-PLOT-5": "Plot 5 — Naphtha complex (NHT, reformer, isomerisation, aromatics)",
    "LOC-PLOT-6": "Plot 6 — Alkylation, MTBE & LPG",
    "LOC-PLOT-7": "Plot 7 — Lubes & asphalt",
    "LOC-PLOT-8": "Plot 8 — Sulfur complex (amine, sour water, SRU)",
    "LOC-PLOT-10": "Plot 10 — Utilities & hydrogen plant",
    "LOC-PLOT-11": "Plot 11 — Marine terminal",
}

_HT = [("FEED", "Feed & charge", "FeedSection"), ("RXN", "Reaction", "ReactionSection"),
       ("SEP", "High / low-pressure separation", "SeparationSection"), ("FRC", "Product stripping", "FractionationSection"),
       ("TRT", "Recycle-gas amine scrubbing", "TreatingSection")]

# id, name, ontology class, plot, capacity, capacity unit, (Nelson category, factor) or None, owner, sections, depth
UNITS = [
    ("VDU-1", "Vacuum distillation unit", "VacuumDistillationUnit", "LOC-PLOT-2", 220, "kbd", ("Vacuum distillation", 2.0), "ROLE-PROC",
     [("HTR", "Vacuum heater", "HeaterSystem"), ("FRC", "Vacuum column", "FractionationSection"),
      ("EJC", "Ejector & vacuum system", "CompressionSection"), ("RDN", "VGO & residue rundown", "ProductRundownSystem")], "skeleton"),
    ("DCU-1", "Delayed coker unit (2 heaters, 4 drums)", "DelayedCoker", "LOC-PLOT-2", 100, "kbd", ("Thermal processes", 2.75), "ROLE-CONV",
     [("FEED", "Feed surge & heater charge", "FeedSection"), ("HTR", "Coker heaters", "HeaterSystem"),
      ("DRM", "Coke drums", "CokeDrumSection"), ("FRC", "Combination fractionator", "FractionationSection"),
      ("OVH", "Fractionator overhead", "OverheadSystem"), ("WGC", "Wet gas compression", "CompressionSection"),
      ("BLD", "Blowdown system", "ReliefSystem"), ("DCK", "Decoking & coke handling", "DecokingSection")], "deep"),
    ("VGOHT-1", "VGO hydrotreater (FCC pretreat)", "Hydrotreater", "LOC-PLOT-3", 90, "kbd", ("Catalytic hydrorefining", 3.0), "ROLE-CONV",
     _HT, "skeleton"),
    ("FCC-1", "Fluid catalytic cracking unit", "FluidCatalyticCracker", "LOC-PLOT-3", 90, "kbd", ("Catalytic cracking", 6.0), "ROLE-CONV",
     [("FEED", "Feed preheat & injection", "FeedSection"), ("RXN", "Reactor & regenerator", "ReactionSection"),
      ("FGS", "Flue gas & power recovery", "FlueGasSection"), ("FRC", "Main fractionator", "FractionationSection"),
      ("OVH", "Main fractionator overhead", "OverheadSystem"), ("WGC", "Wet gas compression", "CompressionSection"),
      ("GCU", "Gas concentration", "SeparationSection")], "deep"),
    ("HCU-1", "Hydrocracker (single stage, two reactors, recycle)", "Hydrocracker", "LOC-PLOT-4", 95, "kbd", ("Catalytic hydrocracking", 6.0),
     "ROLE-CONV",
     [("FEED", "Feed & reactor charge", "FeedSection"), ("RXN", "Reaction (heater, reactors, feed/effluent)", "ReactionSection"),
      ("SEP", "High / low-pressure separation (REAC)", "SeparationSection"), ("RCY", "Recycle gas compression", "CompressionSection"),
      ("MUC", "Make-up hydrogen compression", "CompressionSection"), ("FRC", "Product fractionation", "FractionationSection"),
      ("CHM", "Wash water & chemical injection", "ChemicalInjectionSystem")], "deep"),
    ("DHT-1", "Diesel hydrotreater", "Hydrotreater", "LOC-PLOT-4", 140, "kbd", ("Catalytic hydrorefining", 3.0), "ROLE-PROC", _HT, "skeleton"),
    ("KHT-1", "Kerosene hydrotreater", "Hydrotreater", "LOC-PLOT-4", 65, "kbd", ("Catalytic hydrorefining", 3.0), "ROLE-PROC", _HT[:4],
     "skeleton"),
    ("NHT-1", "Naphtha hydrotreater & splitter", "Hydrotreater", "LOC-PLOT-5", 115, "kbd", ("Catalytic hydrorefining", 3.0), "ROLE-PROC",
     _HT[:3] + [("FRC", "Stripper & naphtha splitter", "FractionationSection")], "skeleton"),
    ("CCR-1", "Continuous catalytic reformer", "CatalyticReformer", "LOC-PLOT-5", 90, "kbd", ("Catalytic reforming", 5.0), "ROLE-PROC",
     [("FEED", "Feed & combined feed exchanger", "FeedSection"), ("RXN", "Reactors & interheaters", "ReactionSection"),
      ("REG", "Continuous catalyst regeneration", "CatalystRegenerationSection"),
      ("SEP", "Separator & net-gas compression", "SeparationSection"), ("FRC", "Reformate stabiliser", "FractionationSection")], "skeleton"),
    ("ISOM-1", "Light naphtha isomerisation", "IsomerisationUnit", "LOC-PLOT-5", 45, "kbd", ("Aromatics / isomerisation", 15.0), "ROLE-PROC",
     [("FEED", "Feed drying", "FeedSection"), ("RXN", "Isomerisation reactors", "ReactionSection"),
      ("FRC", "Stabiliser & deisohexaniser", "FractionationSection")], "skeleton"),
    ("ARO-1", "Aromatics complex (BTX extraction)", "AromaticsComplex", "LOC-PLOT-5", 60, "kbd", ("Aromatics / isomerisation", 15.0),
     "ROLE-PROC",
     [("EXT", "Solvent extraction", "ExtractionSection"), ("FRC", "BTX fractionation", "FractionationSection"),
      ("TRT", "Clay treating", "TreatingSection")], "skeleton"),
    ("ALKY-1", "Alkylation unit", "AlkylationUnit", "LOC-PLOT-6", 25, "kbd", ("Alkylation / polymerisation", 10.0), "ROLE-PROC",
     [("FEED", "Feed treating & drying", "FeedSection"), ("RXN", "Contactors / reactors", "ReactionSection"),
      ("SEP", "Acid settlers", "SeparationSection"), ("FRC", "Deisobutaniser", "FractionationSection"),
      ("TRT", "Effluent treating", "TreatingSection")], "skeleton"),
    ("MTBE-1", "MTBE unit", "OxygenatesUnit", "LOC-PLOT-6", 5, "kbd", ("Oxygenates", 10.0), "ROLE-PROC",
     [("RXN", "Etherification reactors", "ReactionSection"), ("FRC", "Catalytic distillation", "FractionationSection"),
      ("EXT", "Methanol recovery", "ExtractionSection")], "skeleton"),
    ("LUBE-1", "Lube base-oil plant", "LubeBaseOilPlant", "LOC-PLOT-7", 27, "kbd", ("Lubricants", 60.0), "ROLE-PROC",
     [("EXT", "Solvent extraction", "ExtractionSection"), ("DWX", "Solvent dewaxing", "SeparationSection"),
      ("HFN", "Hydrofinishing", "ReactionSection"), ("STO", "Base-oil storage", "StorageSection")], "skeleton"),
    ("ASPH-1", "Asphalt unit", "AsphaltUnit", "LOC-PLOT-7", 15, "kbd", ("Asphalt", 1.5), "ROLE-PROC",
     [("RXN", "Asphalt air blowing", "ReactionSection"), ("STO", "Asphalt storage & loading", "StorageSection")], "skeleton"),
    ("HMU-1", "Hydrogen plant (SMR, 2 × 100 MMSCFD)", "HydrogenPlant", "LOC-PLOT-10", 200, "MMSCFD", None, "ROLE-PROC",
     [("FEED", "Feed pretreatment", "FeedSection"), ("RXN", "Steam reformers (2 trains)", "ReactionSection"),
      ("SEP", "Shift & PSA", "SeparationSection"), ("GEN", "Steam generation", "GenerationSection")], "skeleton"),
    ("ARU-1", "Amine regeneration unit", "AmineRegenerationUnit", "LOC-PLOT-8", 900, "m3/h", None, "ROLE-PROC",
     [("TRT", "Amine regenerators", "TreatingSection"), ("STO", "Amine storage", "StorageSection")], "skeleton"),
    ("SWS-1", "Sour water stripper", "SourWaterStripper", "LOC-PLOT-8", 250, "m3/h", None, "ROLE-PROC",
     [("FRC", "Sour water strippers", "FractionationSection"), ("STO", "Sour water tankage", "StorageSection")], "skeleton"),
    ("SRU-1", "Sulfur recovery unit (3 × 400 t/d Claus + TGTU)", "SulfurRecoveryUnit", "LOC-PLOT-8", 1200, "t/d", None, "ROLE-ENV",
     [("RXN", "Claus trains", "ReactionSection"), ("TRT", "Tail gas treating", "TreatingSection"),
      ("STO", "Sulfur pit & degassing", "StorageSection")], "skeleton"),
    ("LPG-1", "LPG recovery & treating", "TreatingUnit", "LOC-PLOT-6", 20, "kbd", None, "ROLE-PROC",
     [("TRT", "Amine & caustic treating", "TreatingSection"), ("FRC", "Depropaniser & deisobutaniser", "FractionationSection"),
      ("STO", "LPG spheres", "StorageSection")], "skeleton"),
    ("GBL-1", "Gasoline blending", "BlendingUnit", "LOC-PLOT-TF", 180, "kbd", None, "ROLE-PLAN",
     [("BLD", "In-line gasoline blender", "BlendingSection"), ("STO", "Gasoline component tanks", "StorageSection")], "skeleton"),
    ("DBL-1", "Distillate blending", "BlendingUnit", "LOC-PLOT-TF", 260, "kbd", None, "ROLE-PLAN",
     [("BLD", "In-line distillate blender", "BlendingSection"), ("STO", "Distillate component tanks", "StorageSection")], "skeleton"),
    ("TF-2", "Intermediate tank farm", "TankFarm", "LOC-PLOT-TF", 2400, "kbbl", None, "ROLE-OPS",
     [("STO", "Intermediate storage", "StorageSection")], "skeleton"),
    ("TF-3", "Fuel oil & residue tank farm", "TankFarm", "LOC-PLOT-TF", 1200, "kbbl", None, "ROLE-OPS",
     [("STO", "Fuel oil storage", "StorageSection")], "skeleton"),
    ("MT-1", "Marine terminal (4 berths + SPM)", "MarineTerminal", "LOC-PLOT-11", 4, "berths", None, "ROLE-OPS",
     [("CRX", "Crude receipt (single-point mooring)", "LoadingSection"), ("PRL", "Product loading berths", "LoadingSection"),
      ("CKL", "Coke & sulfur export", "LoadingSection")], "skeleton"),
    ("UTL-STM", "Steam & power (cogeneration)", "UtilityUnit", "LOC-PLOT-10", 900, "t/h", None, "ROLE-ENERGY",
     [("GEN", "Boilers & HRSGs", "GenerationSection"), ("DST", "HP / MP / LP steam headers", "DistributionSection")], "skeleton"),
    ("UTL-CW", "Cooling water system", "UtilityUnit", "LOC-PLOT-10", 60000, "m3/h", None, "ROLE-ENERGY",
     [("GEN", "Cooling towers", "GenerationSection"), ("DST", "Cooling water network", "DistributionSection")], "skeleton"),
    ("UTL-FG", "Refinery fuel gas system", "UtilityUnit", "LOC-PLOT-10", 1800, "t/d", None, "ROLE-ENERGY",
     [("TRT", "Fuel gas amine treating", "TreatingSection"), ("DST", "Fuel gas header", "DistributionSection")], "skeleton"),
    ("UTL-FLR", "Flare system", "UtilityUnit", "LOC-PLOT-10", 2500, "t/h", None, "ROLE-OPS",
     [("FLR", "Flare stacks & gas recovery", "ReliefSystem")], "skeleton"),
    ("UTL-N2", "Nitrogen system", "UtilityUnit", "LOC-PLOT-10", 6000, "Nm3/h", None, "ROLE-ENERGY",
     [("GEN", "Air separation", "GenerationSection")], "skeleton"),
    ("UTL-WTR", "Raw, demineralised & boiler feed water", "UtilityUnit", "LOC-PLOT-10", 1500, "m3/h", None, "ROLE-ENERGY",
     [("GEN", "Water treatment", "GenerationSection"), ("DST", "Water distribution", "DistributionSection")], "skeleton"),
    ("UTL-H2", "Hydrogen header", "UtilityUnit", "LOC-PLOT-10", 320, "MMSCFD", None, "ROLE-PROC",
     [("DST", "Hydrogen distribution header", "DistributionSection")], "skeleton"),
]

# CDU train product destinations (were out-of-scope placeholders in v0.3)
CDU_DEST = dict(LPG="LPG-1", OFFGAS="UTL-FG", NAP="NHT-1", KERO="KHT-1", DSL="DHT-1", AGO="HCU-1", AR="VDU-1", SW="SWS-1")

# id, name, from, to, FY2026 average rate, unit  (kbd unless stated; kbd FOE and t/d are not in the liquid balance)
STREAMS = [
    ("STR-CRUDE-RCPT", "Crude receipt", "MT-1", "TF-1", 484.0, "kbd"),
    ("STR-VGO-IMP", "Imported VGO receipt", "MT-1", "TF-2", 30.0, "kbd"),
    ("STR-TF2-HCU", "Imported VGO to hydrocracker", "TF-2", "HCU-1", 30.0, "kbd"),
    ("STR-VDU-VGO-HT", "Vacuum gas oil to VGO hydrotreater", "VDU-1", "VGOHT-1", 56.0, "kbd"),
    ("STR-VDU-VGO-HCU", "Heavy VGO to hydrocracker", "VDU-1", "HCU-1", 18.8, "kbd"),
    ("STR-VDU-VGO-LUBE", "Lube distillates", "VDU-1", "LUBE-1", 22.0, "kbd"),
    ("STR-VDU-VR-DCU", "Vacuum residue to coker", "VDU-1", "DCU-1", 84.8, "kbd"),
    ("STR-VDU-VR-ASPH", "Vacuum residue to asphalt", "VDU-1", "ASPH-1", 12.0, "kbd"),
    ("STR-DCU-NAP", "Coker naphtha", "DCU-1", "NHT-1", 12.7, "kbd"),
    ("STR-DCU-LCGO", "Light coker gas oil", "DCU-1", "DHT-1", 17.0, "kbd"),
    ("STR-DCU-HCGO-HT", "Heavy coker gas oil to VGO hydrotreater", "DCU-1", "VGOHT-1", 18.0, "kbd"),
    ("STR-DCU-HCGO-HCU", "Heavy coker gas oil to hydrocracker", "DCU-1", "HCU-1", 3.2, "kbd"),
    ("STR-DCU-GAS", "Coker gas to fuel gas", "DCU-1", "UTL-FG", 8.5, "kbd FOE"),
    ("STR-DCU-COKE", "Petroleum coke", "DCU-1", "MT-1", 4300, "t/d"),
    ("STR-VGOHT-FCC", "Hydrotreated VGO", "VGOHT-1", "FCC-1", 74.0, "kbd"),
    ("STR-FCC-C3C4", "FCC C3/C4 olefins", "FCC-1", "ALKY-1", 9.4, "kbd"),
    ("STR-FCC-C4", "FCC mixed C4s (isobutylene)", "FCC-1", "MTBE-1", 4.5, "kbd"),
    ("STR-FCC-GASO", "FCC gasoline", "FCC-1", "GBL-1", 37.0, "kbd"),
    ("STR-FCC-LCO", "Light cycle oil", "FCC-1", "DHT-1", 11.1, "kbd"),
    ("STR-FCC-SLURRY", "Slurry oil", "FCC-1", "TF-3", 5.2, "kbd"),
    ("STR-FCC-DRYGAS", "FCC dry gas to fuel gas", "FCC-1", "UTL-FG", 6.2, "kbd FOE"),
    ("STR-HCU-NAP", "Hydrocracked heavy naphtha", "HCU-1", "CCR-1", 25.8, "kbd"),
    ("STR-HCU-JET", "Hydrocracked jet", "HCU-1", "DBL-1", 30.1, "kbd"),
    ("STR-HCU-DSL", "Hydrocracked diesel", "HCU-1", "DBL-1", 34.4, "kbd"),
    ("STR-HCU-LPG", "Hydrocracker LPG", "HCU-1", "LPG-1", 8.6, "kbd"),
    ("STR-HCU-UCO", "Unconverted oil bleed", "HCU-1", "TF-3", 3.0, "kbd"),
    ("STR-NHT-LN", "Light naphtha to isomerisation", "NHT-1", "ISOM-1", 35.0, "kbd"),
    ("STR-NHT-HN", "Heavy naphtha to reformer", "NHT-1", "CCR-1", 64.2, "kbd"),
    ("STR-NHT-HN-BYP", "Heavy naphtha bypassing the reformer", "NHT-1", "GBL-1", 10.3, "kbd"),
    ("STR-CCR-REF-ARO", "Reformate to aromatics", "CCR-1", "ARO-1", 48.0, "kbd"),
    ("STR-CCR-REF-GBL", "Reformate to gasoline pool", "CCR-1", "GBL-1", 28.5, "kbd"),
    ("STR-ISOM-ISO", "Isomerate", "ISOM-1", "GBL-1", 34.3, "kbd"),
    ("STR-LPG-IC4", "Isobutane to alkylation", "LPG-1", "ALKY-1", 5.0, "kbd"),
    ("STR-LPG-PROD", "LPG product", "LPG-1", "MT-1", 8.5, "kbd"),
    ("STR-MTBE-RAF", "C4 raffinate to alkylation", "MTBE-1", "ALKY-1", 3.5, "kbd"),
    ("STR-MTBE-PROD", "MTBE", "MTBE-1", "GBL-1", 3.0, "kbd"),
    ("STR-ALKY-ALK", "Alkylate", "ALKY-1", "GBL-1", 16.1, "kbd"),
    ("STR-ARO-BTX", "BTX aromatics", "ARO-1", "MT-1", 28.8, "kbd"),
    ("STR-ARO-RAF", "Aromatics raffinate", "ARO-1", "GBL-1", 19.2, "kbd"),
    ("STR-KHT-JET", "Hydrotreated jet", "KHT-1", "DBL-1", 57.5, "kbd"),
    ("STR-DHT-ULSD", "Ultra-low-sulfur diesel", "DHT-1", "DBL-1", 122.0, "kbd"),
    ("STR-LUBE-BO", "Lube base oils", "LUBE-1", "MT-1", 14.5, "kbd"),
    ("STR-LUBE-EXT", "Lube extracts & slack wax", "LUBE-1", "TF-3", 7.5, "kbd"),
    ("STR-ASPH-PROD", "Asphalt", "ASPH-1", "MT-1", 12.0, "kbd"),
    ("STR-GBL-GASO", "Finished gasoline", "GBL-1", "MT-1", 148.4, "kbd"),
    ("STR-DBL-DIST", "Finished jet & diesel", "DBL-1", "MT-1", 244.0, "kbd"),
    ("STR-TF3-FO", "Fuel oil export", "TF-3", "MT-1", 15.7, "kbd"),
]

# hydrogen network: chemical consumption (scf/bbl of feed), and reformer net hydrogen yield
H2_CONSUMPTION = {"HCU-1": 1800, "DHT-1": 400, "VGOHT-1": 600, "NHT-1": 150, "KHT-1": 150, "ISOM-1": 100, "LUBE-1": 250}
CCR_H2_YIELD = 1100          # scf/bbl net

# sulfur balance (t/d as S); SRU recovery closes the balance
CRUDE_DENSITY = 0.870        # t/m3, blended slate (indicative)
SULFUR_FATES = [("sulfur_to_coke", 170, "Coke assay × coke make"), ("sulfur_to_residual_products", 45, "Asphalt & fuel oil assays"),
                ("sulfur_in_products", 30, "Product certificates"), ("sulfur_emitted_as_so2", 24, "CEMS (stacks & flares)")]
ACID_GAS_SPLIT = {"ARU-1": 0.9, "SWS-1": 0.1}   # share of recovered sulfur arriving via each acid-gas source
GASOLINE_UPGRADE_SPREAD = 8.0                    # USD/bbl reformate vs heavy naphtha in the pool (planning assumption)


# ============================================================================ deep units (L6-L10)
def _pumps(t, section, rows):
    """rows: (nn, letters, name, fluid, T, flow m3/h, head m, API type, running letters, vib by letter)"""
    from .cdu_gamma import pump_model, seal_plan
    eq = []
    for nn, letters, name, fluid, T, flow, head, api, running, vib in rows:
        for L in letters:
            pid = f"P-{t}{nn}{L}"
            model, oem = pump_model(api, T)
            plan = seal_plan(T, fluid)
            motor_kw = int(round(850 * 9.81 * flow / 3600 * head / 0.72 / 1000 / 10.0) * 10 + 20)
            eq.append(dict(id=pid, name=f"{pid} {name} {L}", section=section, tpl="pump", fluid=fluid,
                           ctx=dict(T=T, flow=flow, head=head, running=L in running, seal_plan=plan, motor_kw=motor_kw,
                                    vib=vib.get(L, 2.4), suction_barg=2.0),
                           design=dict(model=model, oem=oem, api_610_type=api, rated_flow=flow, rated_head=head,
                                       service_temperature=T, seal_plan=plan, motor_power=motor_kw,
                                       material_class="S-4" if T < 200 else "C-6")))
    return eq


def _heater(eid, name, section, fluid, flow, cot, cit, tmt, o2, stack, absorbed, eff, design):
    return dict(id=eid, name=f"{eid} {name}", section=section, tpl="heater", fluid=fluid,
                ctx=dict(flow=flow, cot=cot, cit=cit, tmt=tmt, o2=o2, stack_t=stack, absorbed_mw=absorbed, eff=eff,
                         fired_mw=round(absorbed / (eff / 100), 1)),
                design=design)


def _vessel(eid, name, section, tpl, fluid, ctx, D, L, dT, dP, mat, T):
    return dict(id=eid, name=f"{eid} {name}", section=section, tpl=tpl, fluid=fluid, ctx=ctx,
                design=dict(diameter=D, length=L, design_temperature=dT, design_pressure=dP, shell_material=mat, service_temperature=T))


def _column(eid, name, section, fluid, top_t, P, T, reflux, D, H, trays, dT, dP, mat):
    return dict(id=eid, name=f"{eid} {name}", section=section, tpl="column", fluid=fluid,
                ctx=dict(top_t=top_t, P=P, T=T, reflux=reflux),
                design=dict(diameter=D, height=H, trays=trays, design_temperature=dT, design_pressure=dP,
                            shell_material=mat, service_temperature=T))


def _air(eid, name, section, fluid, Thin, Thout, met, duty, dT, dP):
    return dict(id=eid, name=f"{eid} {name}", section=section, tpl="aircooler", fluid=fluid, ctx=dict(Thin=Thin, Thout=Thout),
                design=dict(tube_metallurgy=met, bays=2, duty=duty, service_temperature=Thin, design_temperature=dT, design_pressure=dP))


def _comp(eid, name, section, tpl, fluid, ctx, model, oem, driver, kw, cap, dP, dT, T):
    return dict(id=eid, name=f"{eid} {name}", section=section, tpl=tpl, fluid=fluid, ctx=ctx,
                design=dict(model=model, oem=oem, driver=driver, rated_power=kw, rated_capacity=cap, design_pressure=dP,
                            design_temperature=dT, service_temperature=T))


def _pipe(eid, name, section, tpl, fluid, ctx, size, mat, T):
    return dict(id=eid, name=f"{eid} {name}", section=section, tpl=tpl, fluid=fluid, ctx=ctx,
                design=dict(line_size=size, material=mat, corrosion_allowance=3.0, nominal_wall=ctx["wall"] + 1.8, service_temperature=T))


def _chem(eid, name, section, chem, rate):
    return dict(id=eid, name=f"{eid} {name}", section=section, tpl="chem", fluid=chem, ctx=dict(rate=rate),
                design=dict(chemical=chem, design_rate=round(rate * 1.5, 1), service_temperature=40))


def fcc_catalogue():
    from .cdu_gamma import _hx
    s = lambda c: f"FCC-1-{c}"
    feed_m3h = round(74.0 * KBD_TO_M3H)
    eq = [
        _heater("H-301", "FCC feed preheater", s("FEED"), "Hydrotreated VGO", feed_m3h, 290.0, 225.0, [455, 461, 458, 452], 3.0, 185,
                24.0, 86.5, dict(absorbed_duty=28.0, passes=4, coil_metallurgy="Cr5", design_tmt=560, burners=10,
                                 design_efficiency=87.0, service_temperature=290)),
        dict(id="R-301", name="R-301 FCC reactor, riser & stripper", section=s("RXN"), tpl="fccreactor", fluid="VGO / catalyst",
             ctx=dict(rot=532.0, feed_m3h=feed_m3h, cat_oil=7.1),
             design=dict(diameter=5.2, height=48.0, design_temperature=565, design_pressure=3.5, shell_material="CarbonSteel",
                         lining="Abrasion-resistant refractory", service_temperature=532)),
        dict(id="R-302", name="R-302 FCC regenerator", section=s("RXN"), tpl="regen", fluid="Catalyst / air / flue gas",
             ctx=dict(bed_t=712.0, afterburn=19.0, cat_loss=3.6),
             design=dict(diameter=12.5, height=35.0, design_temperature=760, design_pressure=3.5, shell_material="CarbonSteel",
                         catalyst_inventory=420, service_temperature=712)),
        dict(id="SV-301", name="SV-301 Regenerated catalyst slide valve", section=s("RXN"), tpl="slidevalve", fluid="Regenerated catalyst",
             ctx=dict(pos=46.0, dp=0.42), design=dict(line_size='48"', design_temperature=760, design_pressure=3.5, service_temperature=712)),
        dict(id="SV-302", name="SV-302 Spent catalyst slide valve", section=s("RXN"), tpl="slidevalve", fluid="Spent catalyst",
             ctx=dict(pos=41.0, dp=0.38), design=dict(line_size='42"', design_temperature=565, design_pressure=3.5, service_temperature=532)),
        _comp("K-302", "Main air blower", s("FGS"), "compressor", "Air",
              dict(ps=0.0, pd=2.6, td=215, flow=290, rpm=4800, vib_um=24, surge=21), "OEM-D AV-56", "OEM-D",
              "Expander + motor-generator train", 28000, 320, 3.5, 260, 215),
        dict(id="EX-301", name="EX-301 Flue-gas power recovery expander", section=s("FGS"), tpl="expander", fluid="Flue gas",
             ctx=dict(mw=21.5), design=dict(model="OEM-D EXP-50", oem="OEM-D", power_rating=26.0, design_temperature=760,
                                            design_pressure=3.5, service_temperature=705)),
        dict(id="B-301", name="B-301 CO boiler / waste-heat boiler", section=s("FGS"), tpl="whb", fluid="Flue gas / BFW",
             ctx=dict(steam=175.0, so2=220.0), design=dict(steam_rating=200, design_pressure=45.0, design_temperature=450,
                                                           service_temperature=705)),
        _column("C-301", "FCC main fractionator", s("FRC"), "Reactor vapour", 125.0, 1.1, 350.0, 380.0, 8.0, 50.0, 32, 400, 3.5, "Cr5"),
        _column("C-302", "Primary absorber", s("GCU"), "Wet gas / naphtha", 40.0, 14.0, 50.0, 60.0, 2.4, 30.0, 30, 90, 18.0, "CarbonSteel"),
        _column("C-303", "Debutaniser", s("GCU"), "Naphtha / LPG", 60.0, 10.0, 180.0, 140.0, 3.2, 36.0, 40, 220, 14.0, "CarbonSteel"),
        _column("C-304", "C3/C4 splitter", s("GCU"), "LPG", 50.0, 18.0, 100.0, 120.0, 2.6, 45.0, 60, 130, 22.0, "CarbonSteel"),
        _vessel("V-301", "Main fractionator overhead receiver", s("OVH"), "receiver", "Naphtha / sour water",
                dict(T=40, P=0.8, chloride=6.0, ph=8.2, iron=0.3), 4.2, 13.0, 90, 5.0, "CarbonSteel", 40),
        _vessel("V-302", "Wet gas compressor interstage drum", s("WGC"), "drumboot", "Wet gas / condensate",
                dict(T=40, P=5.0), 2.8, 8.0, 90, 8.0, "CarbonSteel", 40),
        _vessel("V-303", "High-pressure separator", s("GCU"), "drumboot", "Gas / naphtha / water",
                dict(T=40, P=14.0), 3.0, 9.0, 90, 18.0, "CarbonSteel", 40),
        _comp("K-301", "Wet gas compressor", s("WGC"), "compressor", "FCC wet gas",
              dict(ps=0.6, pd=16.0, td=118, flow=95, rpm=7200, vib_um=31, surge=13), "OEM-D MCL-806", "OEM-D",
              "Steam turbine", 11500, 105, 20.0, 160, 118),
        _hx("3", "01", "Feed / slurry pumparound exchanger", s("FEED"), "Slurry pumparound", 150, 225, 350, 280, "Cr5", duty=20.0,
            cold_fluid="Hydrotreated VGO"),
        _hx("3", "02", "Slurry steam generator", s("FRC"), "Slurry pumparound", 150, 155, 350, 270, "Cr5", duty=25.0, cold_fluid="BFW"),
        _hx("3", "03", "Feed / LCO exchanger", s("FEED"), "LCO product", 90, 150, 230, 160, "CarbonSteel", duty=9.0,
            cold_fluid="Hydrotreated VGO"),
        _air("E-310A", "Main fractionator overhead air cooler A", s("OVH"), "Overhead vapour", 125, 55, "CarbonSteel", 30.0, 180, 5.0),
        _air("E-310B", "Main fractionator overhead air cooler B", s("OVH"), "Overhead vapour", 125, 55, "CarbonSteel", 30.0, 180, 5.0),
        _hx("3", "11", "Overhead trim cooler", s("OVH"), "Overhead naphtha / water", 30, 38, 55, 40, "Titanium", duty=8.0,
            cold_fluid="Cooling water"),
        _hx("3", "12", "Wet gas compressor interstage cooler", s("WGC"), "Wet gas", 30, 38, 110, 40, "CarbonSteel", duty=7.0,
            cold_fluid="Cooling water"),
        _hx("3", "13", "Debutaniser reboiler", s("GCU"), "LCO pumparound", 170, 180, 230, 190, "CarbonSteel", duty=12.0,
            cold_fluid="Debutaniser bottoms"),
        _pipe("PC-301", "Reactor overhead vapour line", s("FRC"), "piping", "Reactor vapour", dict(cr=0.06, wall=13.9), '48"', "Cr5", 532),
        _pipe("PC-302", "Main fractionator overhead line", s("OVH"), "ovhline", "Overhead vapour", dict(cr=0.12, wall=8.1, dpm=22.0),
              '36"', "CarbonSteel", 125),
        _chem("X-301", "Overhead wash-water injection", s("OVH"), "Wash water", 9000.0),
        _chem("X-302", "Antimony (nickel passivation) injection", s("FEED"), "Antimony passivator", 6.0),
    ]
    eq += _pumps("3", s("FEED"), [("01", "AB", "FCC feed pump", "Hydrotreated VGO", 150, 490, 180, "BB2", "A", {})])
    eq += _pumps("3", s("FRC"), [("02", "AB", "Slurry pumparound pump", "Slurry pumparound", 350, 600, 90, "BB2", "A", {"A": 3.1}),
                                 ("03", "AB", "HCO pumparound pump", "HCO pumparound", 300, 300, 90, "BB2", "A", {}),
                                 ("04", "AB", "LCO product pump", "LCO", 230, 75, 110, "OH2", "A", {})])
    eq += _pumps("3", s("OVH"), [("05", "AB", "Main fractionator reflux pump", "Unstabilised naphtha", 40, 400, 90, "OH2", "A", {}),
                                 ("07", "AB", "FCC sour water pump", "Sour water", 40, 30, 60, "OH2", "A", {})])
    eq += _pumps("3", s("GCU"), [("06", "AB", "Debutaniser reflux pump", "LPG", 45, 120, 110, "OH2", "A", {})])
    return eq


def hcu_catalogue():
    from .cdu_gamma import _hx
    s = lambda c: f"HCU-1-{c}"
    feed_m3h = round(85.9 * KBD_TO_M3H)
    eq = [
        _heater("H-401", "Reactor charge heater", s("RXN"), "Feed / hydrogen", feed_m3h, 378.0, 345.0, [512, 518, 524, 515], 3.2, 175,
                21.5, 89.0, dict(absorbed_duty=26.0, passes=4, coil_metallurgy="SS347", design_tmt=600, burners=12,
                                 design_efficiency=89.5, service_temperature=378)),
        dict(id="R-401", name="R-401 Hydrotreating (first-stage) reactor", section=s("RXN"), tpl="reactor3", fluid="VGO / hydrogen",
             ctx=dict(t_in=375.0, step=8, dt=16, quench=30.0, P=165.0, dp=2.4, skin=385.0, wabt=391.0),
             design=dict(diameter=4.8, height=32.0, design_temperature=454, design_pressure=185.0, shell_material="Cr225Mo",
                         catalyst_volume=380, design_wabt=400, service_temperature=400)),
        dict(id="R-402", name="R-402 Hydrocracking reactor", section=s("RXN"), tpl="reactor4", fluid="Hydrotreated VGO / hydrogen",
             ctx=dict(t_in=386.0, step=4, dt=14, quench=35.0, P=160.0, dp=3.1, skin=395.0, wabt=399.0),
             design=dict(diameter=4.8, height=38.0, design_temperature=454, design_pressure=185.0, shell_material="Cr225Mo",
                         catalyst_volume=520, design_wabt=410, service_temperature=410)),
        _hx("4", "01", "Feed / effluent exchanger", s("RXN"), "Reactor effluent", 180, 340, 420, 270, "SS347", duty=60.0,
            cold_fluid="Reactor feed"),
        _hx("4", "02", "Hot separator vapour / recycle gas exchanger", s("SEP"), "Hot separator vapour", 70, 230, 260, 150, "Cr225Mo",
            duty=35.0, cold_fluid="Recycle gas"),
        _vessel("V-401", "Hot high-pressure separator", s("SEP"), "drum", "Effluent / hydrogen", dict(T=260, P=155.0),
                3.2, 10.0, 300, 185.0, "Cr225Mo", 260),
        _vessel("V-402", "Cold high-pressure separator", s("SEP"), "drumboot", "Hydrocarbon / sour water / hydrogen",
                dict(T=50, P=152.0), 3.4, 12.0, 90, 185.0, "CarbonSteel", 50),
        _vessel("V-403", "Cold low-pressure separator", s("SEP"), "drumboot", "Hydrocarbon / sour water", dict(T=50, P=25.0),
                3.6, 12.0, 90, 35.0, "CarbonSteel", 50),
        _vessel("V-404", "Recycle compressor knock-out drum", s("RCY"), "drum", "Recycle hydrogen", dict(T=55, P=150.0),
                2.4, 6.0, 90, 185.0, "CarbonSteel", 55),
        _comp("K-401", "Recycle gas compressor", s("RCY"), "compressor", "Recycle hydrogen",
              dict(ps=150.0, pd=172.0, td=72, flow=420, rpm=10400, vib_um=41, surge=10), "OEM-D BCL-405", "OEM-D",
              "Steam turbine", 9500, 460, 190.0, 120, 72),
        _comp("K-402A", "Make-up hydrogen compressor A", s("MUC"), "recip", "Make-up hydrogen", dict(pd=178.0, valve_t=149.0),
              "OEM-E 3HE-3", "OEM-E", "Electric motor", 6500, 95, 190.0, 160, 45),
        _comp("K-402B", "Make-up hydrogen compressor B", s("MUC"), "recip", "Make-up hydrogen", dict(pd=178.0, valve_t=141.0),
              "OEM-E 3HE-3", "OEM-E", "Electric motor", 6500, 95, 190.0, 160, 45),
        _column("C-401", "Product stripper", s("FRC"), "Hydrocracked product", 110.0, 8.0, 250.0, 90.0, 3.6, 30.0, 20, 300, 12.0,
                "CarbonSteel"),
        _column("C-402", "Main fractionator", s("FRC"), "Hydrocracked product", 115.0, 1.2, 340.0, 260.0, 6.4, 48.0, 40, 380, 3.5,
                "Cr5"),
        _pipe("PC-401", "REAC inlet circuit (NH4HS service)", s("SEP"), "piping", "Reactor effluent / wash water",
              dict(cr=0.21, wall=16.4), '20"', "CarbonSteel", 150),
        _pipe("PC-402", "Hot reactor effluent circuit", s("RXN"), "piping", "Reactor effluent / hydrogen", dict(cr=0.02, wall=38.6),
              '16"', "SS347", 420),
        _chem("X-401", "REAC wash-water injection", s("CHM"), "Wash water", 25000.0),
        _chem("X-402", "Fractionator overhead corrosion inhibitor", s("CHM"), "Filming corrosion inhibitor", 5.0),
    ]
    for L in "ABCD":
        eq.append(_air(f"E-410{L}", f"Reactor effluent air cooler (REAC) {L}", s("SEP"), "Reactor effluent / wash water",
                       150, 50, "Alloy825", 18.0, 200, 185.0))
    for e in eq:
        if e["id"] in ("E-401", "E-402"):
            e["design"]["design_pressure"] = 185.0
    eq += _pumps("4", s("FEED"), [("01", "AB", "Reactor feed pump", "VGO feed", 180, 570, 1900, "BB5", "A", {})])
    eq += _pumps("4", s("CHM"), [("02", "AB", "Wash-water injection pump", "Wash water", 40, 25, 1850, "BB5", "A", {})])
    eq += _pumps("4", s("FRC"), [("03", "AB", "Fractionator bottoms pump", "Unconverted oil", 330, 120, 150, "BB2", "A", {}),
                                 ("04", "AB", "Diesel product pump", "Hydrocracked diesel", 265, 230, 120, "OH2", "A", {}),
                                 ("05", "AB", "Fractionator reflux pump", "Naphtha reflux", 40, 300, 90, "OH2", "A", {})])
    return eq


def dcu_catalogue():
    from .cdu_gamma import _hx
    s = lambda c: f"DCU-1-{c}"
    per_heater = round(84.8 * KBD_TO_M3H / 2)
    htr = lambda: dict(absorbed_duty=36.0, passes=4, coil_metallurgy="Cr9", design_tmt=680, burners=16,
                       design_efficiency=89.0, service_temperature=496)
    eq = [
        _heater("H-501", "Coker heater 1", s("HTR"), "Vacuum residue", per_heater, 496.0, 335.0, [610, 615, 622, 618], 3.1, 205,
                30.5, 88.5, htr()),
        _heater("H-502", "Coker heater 2", s("HTR"), "Vacuum residue", per_heater, 496.0, 335.0, [632, 641, 648, 636], 3.4, 215,
                31.0, 87.2, htr()),
        dict(id="DK-501", name="DK-501 Hydraulic decoking system", section=s("DCK"), tpl="decoking", fluid="Cutting water",
             ctx={}, design=dict(design_pressure=300.0, design_temperature=60, cutting_tool="Combination drilling / cutting tool",
                                 service_temperature=40)),
        dict(id="CR-501", name="CR-501 Coke crusher", section=s("DCK"), tpl="crusher", fluid="Petroleum coke", ctx={},
             design=dict(throughput_rating=600, motor_power=450, design_temperature=100, service_temperature=60)),
        _column("C-501", "Combination fractionator", s("FRC"), "Coke drum vapour", 120.0, 1.0, 360.0, 300.0, 7.0, 42.0, 30, 430, 3.5, "Cr5"),
        _column("C-502", "Blowdown tower", s("BLD"), "Blowdown vapour / oil", 90.0, 0.3, 200.0, 40.0, 3.0, 18.0, 10, 450, 3.5,
                "CarbonSteel"),
        _vessel("V-501", "Fractionator overhead receiver", s("OVH"), "receiver", "Naphtha / sour water",
                dict(T=40, P=0.8, chloride=4.0, ph=8.6, iron=0.5), 3.8, 12.0, 90, 5.0, "CarbonSteel", 40),
        _vessel("V-502", "Feed surge drum", s("FEED"), "drum", "Vacuum residue", dict(T=300, P=3.0), 4.5, 14.0, 340, 6.0, "CarbonSteel", 300),
        _comp("K-501", "Coker wet gas compressor", s("WGC"), "compressor", "Coker wet gas",
              dict(ps=0.5, pd=14.0, td=120, flow=70, rpm=8200, vib_um=30, surge=15), "OEM-D MCL-705", "OEM-D",
              "Steam turbine", 8000, 80, 18.0, 160, 120),
        _hx("5", "01", "Feed / HCGO exchanger", s("FEED"), "HCGO pumparound", 250, 300, 360, 300, "Cr5", duty=18.0,
            cold_fluid="Vacuum residue"),
        _hx("5", "11", "LCGO rundown cooler", s("FRC"), "LCGO", 30, 40, 250, 60, "CarbonSteel", duty=7.0, cold_fluid="Cooling water"),
        _air("E-510A", "Fractionator overhead air cooler A", s("OVH"), "Overhead vapour", 120, 55, "CarbonSteel", 26.0, 180, 5.0),
        _air("E-510B", "Fractionator overhead air cooler B", s("OVH"), "Overhead vapour", 120, 55, "CarbonSteel", 26.0, 180, 5.0),
        _pipe("PC-501", "Heater outlet transfer lines", s("HTR"), "piping", "Cracked residue", dict(cr=0.08, wall=12.2), '8"', "Cr9", 496),
        _pipe("PC-502", "Coke drum overhead vapour line", s("DRM"), "piping", "Coke drum vapour", dict(cr=0.05, wall=11.4), '24"',
              "Cr125Mo", 440),
        _chem("X-501", "Antifoam injection package", s("DRM"), "Silicone antifoam", 12.0),
    ]
    for eid, name, level, cycles in [("D-501A", "Coke drum 1A", 72.0, 5200), ("D-501B", "Coke drum 1B", 68.0, 5900),
                                     ("D-502A", "Coke drum 2A", 75.0, 4800), ("D-502B", "Coke drum 2B", 70.0, 5100)]:
        eq.append(dict(id=eid, name=f"{eid} {name}", section=s("DRM"), tpl="cokedrum", fluid="Cracked residue / coke",
                       ctx=dict(level=level, cycle_h=18.0, cycles=cycles),
                       design=dict(diameter=8.5, height=36.0, design_temperature=490, design_pressure=4.5, shell_material="Cr125Mo",
                                   drum_cycle_design=18, service_temperature=470)))
    eq += _pumps("5", s("FEED"), [("01", "AB", "Heater charge pump", "Vacuum residue", 300, 570, 350, "BB2", "A", {})])
    eq += _pumps("5", s("DCK"), [("02", "AB", "Decoking jet pump", "Cutting water", 40, 250, 3000, "BB5", "A", {})])
    eq += _pumps("5", s("FRC"), [("03", "AB", "HCGO product pump", "Heavy coker gas oil", 320, 140, 120, "OH2", "A", {}),
                                 ("04", "AB", "LCGO product pump", "Light coker gas oil", 250, 120, 110, "OH2", "A", {})])
    eq += _pumps("5", s("OVH"), [("05", "AB", "Fractionator reflux pump", "Coker naphtha", 40, 280, 90, "OH2", "A", {})])
    return eq


DEEP = {"FCC-1": (3, fcc_catalogue), "HCU-1": (4, hcu_catalogue), "DCU-1": (5, dcu_catalogue)}
