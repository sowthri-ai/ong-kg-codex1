"""
Equipment-class templates for the Gamma CDU reference model.

Each template gives the ISO 14224-style decomposition below an equipment unit
(L7 subunits -> L8 maintainable items -> L9 parts) and the instrument tags (L10)
normally found on that class, with the node they attach to and a function that
returns a representative operating value from the equipment's service context.

All values are synthetic engineering estimates for a demonstration model.
"""
import math

# item code -> ontology class (anything not listed is a generic MaintainableItem)
ITEM_ONTO = {"SEAL": "MechanicalSeal", "RBRG": "Bearing", "TBRG": "Bearing", "MBRG": "Bearing",
             "TUBES": "TubeSet", "CTUBES": "TubeSet", "PASS1": "TubeSet", "PASS2": "TubeSet",
             "PASS3": "TubeSet", "PASS4": "TubeSet"}


def _amps(c):
    kw = c["motor_kw"]
    volts = 6600 if kw > 300 else 415
    running = c.get("running", True)
    return round(kw * 1000 * 0.85 / (math.sqrt(3) * volts * 0.9), 0) if running else 0.0


def _pump_dp(c):
    return round(c["head"] * 850 * 9.81 / 1e5 + c.get("suction_barg", 2.0), 1)


# (type, description, unit, attach_code, kind, value_fn, condition_fn or None)
PUMP = dict(
    onto="CentrifugalPump", eq_class="Pump",
    subunits=[
        ("DRV", "Driver (electric motor)", [("STATOR", "Stator windings", []), ("ROTOR", "Rotor", []),
                                            ("MBRG", "Motor bearings", [])]),
        ("PMP", "Pump unit", [("IMP", "Impeller", [("WR", "Wear rings")]), ("SHF", "Shaft", []),
                              ("SEAL", "Mechanical seal", [("SF", "Seal faces"), ("OR", "O-rings / secondary seals"),
                                                           ("SPR", "Springs")]),
                              ("RBRG", "Radial bearing", []), ("TBRG", "Thrust bearing", []),
                              ("CSG", "Casing", [])]),
        ("CPL", "Power transmission", [("CPLG", "Coupling", [])]),
        ("LUB", "Lubrication system", [("OILR", "Oil sump / reservoir", [])]),
        ("CM", "Control & monitoring", [("VPROBE", "Vibration probes", []), ("TSEN", "Bearing temperature sensors", [])]),
    ],
    tags=[
        ("FI", "Discharge flow", "m3/h", "PMP", "sensor", lambda c: float(c["flow"]) if c.get("running", True) else 0.0, None),
        ("PI", "Discharge pressure", "barg", "PMP", "sensor", _pump_dp, None),
        ("VI", "Radial bearing vibration", "mm/s", "RBRG", "sensor", lambda c: c.get("vib", 2.4), None),
        ("VI", "Thrust bearing vibration", "mm/s", "TBRG", "sensor", lambda c: round(c.get("vib", 2.4) * 0.8, 1), None),
        ("TI", "Thrust bearing temperature", "degC", "TBRG", "sensor", lambda c: 62.0 + min(c["T"], 350) * 0.06, None),
        ("II", "Motor current", "A", "DRV", "sensor", _amps, None),
        ("PI", "Seal pot / barrier pressure", "barg", "SEAL", "sensor",
         lambda c: 14.0 if c["seal_plan"] == "Plan53B" else 0.6, lambda c: c["seal_plan"] != "Plan11"),
    ],
)

SHELL_TUBE = dict(
    onto="ShellAndTubeHX", eq_class="Heat exchanger",
    subunits=[
        ("SHL", "Shell", [("SHELL", "Shell body", []), ("BAF", "Baffles", [])]),
        ("TB", "Tube bundle", [("TUBES", "Tubes", [("TTJ", "Tube-to-tubesheet joints")]), ("TSH", "Tubesheet", [])]),
        ("CH", "Channel & heads", [("CHC", "Channel cover", []), ("GSK", "Gaskets", [("SWG", "Spiral-wound gaskets")])]),
    ],
    tags=[
        ("TI", "Cold-side inlet temperature", "degC", "TB", "sensor", lambda c: c["Tin"], None),
        ("TI", "Cold-side outlet temperature", "degC", "TB", "sensor", lambda c: c["Tout"], None),
        ("TI", "Hot-side inlet temperature", "degC", "SHL", "sensor", lambda c: c["Thin"], None),
        ("TI", "Hot-side outlet temperature", "degC", "SHL", "sensor", lambda c: c["Thout"], None),
        ("PDI", "Cold-side pressure drop", "bar", "TB", "sensor", lambda c: c.get("dp", 0.7), None),
        ("UY", "Duty (calculated)", "MW", "TB", "calculated", lambda c: c["duty"], None),
        ("UY", "Fouling resistance (calculated)", "m2K/kW", "TUBES", "calculated", lambda c: c.get("rf", 0.2), None),
    ],
)

AIR_COOLER = dict(
    onto="AirCooledHX", eq_class="Air cooler",
    subunits=[
        ("TB", "Tube bundle", [("TUBES", "Finned tubes", []), ("PLUGS", "Header plugs", [])]),
        ("FAN", "Fan & drive", [("BLADES", "Fan blades", []), ("FMOTOR", "Fan motor", []), ("BELT", "Drive belts", [])]),
        ("HDR", "Headers", [("HBOX", "Header boxes", [])]),
    ],
    tags=[
        ("TI", "Process inlet temperature", "degC", "HDR", "sensor", lambda c: c["Thin"], None),
        ("TI", "Process outlet temperature", "degC", "HDR", "sensor", lambda c: c["Thout"], None),
        ("II", "Fan motor current", "A", "FMOTOR", "sensor", lambda c: 48.0, None),
        ("VI", "Fan vibration", "mm/s", "FAN", "sensor", lambda c: 2.8, None),
    ],
)

FIRED_HEATER = dict(
    onto="FiredHeater", eq_class="Fired heater",
    subunits=[
        ("RAD", "Radiant section", [("PASS1", "Radiant coil pass 1", [("RB1", "Return bends pass 1")]),
                                    ("PASS2", "Radiant coil pass 2", [("RB2", "Return bends pass 2")]),
                                    ("PASS3", "Radiant coil pass 3", [("RB3", "Return bends pass 3")]),
                                    ("PASS4", "Radiant coil pass 4", [("RB4", "Return bends pass 4")]),
                                    ("REF", "Refractory lining", [])]),
        ("CONV", "Convection section", [("CTUBES", "Convection tubes", []), ("SOOT", "Soot blowers", [])]),
        ("BRN", "Burner system", [("BURNERS", "Burners (24)", [("TIPS", "Burner tips")]), ("PILOTS", "Pilot burners", [])]),
        ("STK", "Stack & draft", [("DAMPER", "Stack damper", [])]),
        ("FUEL", "Fuel gas system", [("FGV", "Fuel gas control valve", [])]),
    ],
    tags=[
        *[("FI", f"Pass {p} flow", "m3/h", f"PASS{p}", "sensor", (lambda p: lambda c: round(c["flow"] / 4, 0))(p), None) for p in range(1, 5)],
        *[("TI", f"Pass {p} outlet temperature (COT)", "degC", f"PASS{p}", "sensor", (lambda p: lambda c: c["cot"])(p), None) for p in range(1, 5)],
        *[("TI", f"Pass {p} tube-metal temperature (TMT)", "degC", f"PASS{p}", "sensor", (lambda p: lambda c: c["tmt"][p - 1])(p), None) for p in range(1, 5)],
        ("TI", "Heater inlet temperature (CIT)", "degC", "RAD", "sensor", lambda c: c["cit"], None),
        ("AI", "Flue-gas oxygen", "vol%", "STK", "analyser", lambda c: c["o2"], None),
        ("PI", "Arch draft", "mmH2O", "STK", "sensor", lambda c: -2.5, None),
        ("TI", "Stack temperature", "degC", "STK", "sensor", lambda c: c["stack_t"], None),
        ("FI", "Fuel gas flow", "Nm3/h", "FUEL", "sensor", lambda c: round(c["fired_mw"] * 3600 / 38.0, 0), None),
        ("PI", "Fuel gas pressure", "barg", "FUEL", "sensor", lambda c: 2.4, None),
        ("UY", "Absorbed duty (calculated)", "MW", "RAD", "calculated", lambda c: c["absorbed_mw"], None),
        ("UY", "Thermal efficiency (calculated)", "%", "STK", "calculated", lambda c: c["eff"], None),
    ],
)

DESALTER = dict(
    onto="Desalter", eq_class="Desalter",
    subunits=[
        ("VES", "Vessel", [("SHELL", "Shell", [])]),
        ("GRID", "Electrical grid system", [("TRAFO", "Transformer", []), ("ELEC", "Electrode grids", []),
                                            ("BUSH", "Entrance bushings", [])]),
        ("MIX", "Mixing valve", [("MIXV", "Mix valve", [("TRIM", "Valve trim")])]),
        ("INT", "Internals", [("DIST", "Inlet distributor", []), ("COLL", "Oil collector", [])]),
        ("MUD", "Mud wash system", [("MUDH", "Mud wash headers", [])]),
    ],
    tags=[
        ("TI", "Desalter temperature", "degC", "VES", "sensor", lambda c: c["T"], None),
        ("PI", "Desalter pressure", "barg", "VES", "sensor", lambda c: c["P"], None),
        ("LI", "Oil-water interface level", "%", "INT", "sensor", lambda c: 45.0, None),
        ("EI", "Grid voltage", "kV", "TRAFO", "sensor", lambda c: 18.0, None),
        ("II", "Grid current", "A", "TRAFO", "sensor", lambda c: c.get("grid_a", 60.0), None),
        ("PDI", "Mix-valve pressure drop", "bar", "MIXV", "sensor", lambda c: 1.0, None),
        ("AI", "Oil in brine", "ppm", "VES", "analyser", lambda c: c.get("oib", 150.0), None),
        ("AL", "Desalted crude salt (lab)", "PTB", "VES", "lab", lambda c: c["salt_out"], None),
        ("AL", "Desalted crude BS&W (lab)", "vol%", "VES", "lab", lambda c: 0.1, None),
    ],
)

ATM_COLUMN = dict(
    onto="Column", eq_class="Column",
    subunits=[
        ("SHL", "Shell & lining", [("SHELL", "Shell (410SS clad)", []), ("TOPCLAD", "Top-section cladding (Alloy 400)", [])]),
        ("INT", "Internals", [("TR_TOP", "Trays: top section", [("VALVES", "Tray valves")]), ("TR_KERO", "Trays: kerosene section", []),
                              ("TR_DSL", "Trays: diesel section", []), ("TR_AGO", "Trays: AGO section", []),
                              ("TR_FZ", "Trays: wash & flash zone", []), ("TR_STR", "Trays: stripping section", []),
                              ("DRAWS", "Draw-off pans", [])]),
        ("NOZ", "Nozzles", [("FEEDNOZ", "Feed nozzle & vapour horn", [])]),
    ],
    tags=[
        ("TI", "Column top temperature", "degC", "TR_TOP", "sensor", lambda c: c["top_t"], None),
        ("PI", "Column top pressure", "barg", "SHL", "sensor", lambda c: 1.0, None),
        ("TI", "Kerosene draw temperature", "degC", "TR_KERO", "sensor", lambda c: 190.0, None),
        ("TI", "Diesel draw temperature", "degC", "TR_DSL", "sensor", lambda c: 255.0, None),
        ("TI", "AGO draw temperature", "degC", "TR_AGO", "sensor", lambda c: 330.0, None),
        ("TI", "Flash-zone temperature", "degC", "TR_FZ", "sensor", lambda c: c["fz_t"], None),
        ("PI", "Flash-zone pressure", "barg", "TR_FZ", "sensor", lambda c: 1.6, None),
        ("PDI", "Column pressure drop", "bar", "INT", "sensor", lambda c: 0.35, None),
        ("LI", "Bottoms level", "%", "SHL", "sensor", lambda c: 50.0, None),
        ("FI", "Bottom stripping steam", "t/h", "TR_STR", "sensor", lambda c: 9.0, None),
    ],
)

SIDE_STRIPPER = dict(
    onto="SideStripper", eq_class="Side stripper",
    subunits=[("SHL", "Shell", [("SHELL", "Shell", [])]), ("INT", "Internals", [("TRAYS", "Trays", [])])],
    tags=[
        ("LI", "Level", "%", "SHL", "sensor", lambda c: 50.0, None),
        ("TI", "Bottoms temperature", "degC", "SHL", "sensor", lambda c: c["T"], None),
        ("FI", "Stripping steam", "t/h", "INT", "sensor", lambda c: 1.5, None),
    ],
)

STABILISER = dict(
    onto="Column", eq_class="Column",
    subunits=[("SHL", "Shell", [("SHELL", "Shell", [])]), ("INT", "Internals", [("TRAYS", "Trays", [("VALVES", "Tray valves")])])],
    tags=[
        ("TI", "Stabiliser top temperature", "degC", "INT", "sensor", lambda c: 62.0, None),
        ("TI", "Stabiliser bottom temperature", "degC", "SHL", "sensor", lambda c: c["T"], None),
        ("PI", "Stabiliser top pressure", "barg", "SHL", "sensor", lambda c: c["P"], None),
        ("LI", "Bottoms level", "%", "SHL", "sensor", lambda c: 50.0, None),
    ],
)


def _drum(boot=False, analysers=False):
    subs = [("SHL", "Shell", [("SHELL", "Shell", [])]), ("INT", "Internals", [("DEMIST", "Mist eliminator", [])])]
    tags = [
        ("LI", "Hydrocarbon level", "%", "SHL", "sensor", lambda c: 50.0, None),
        ("PI", "Pressure", "barg", "SHL", "sensor", lambda c: c["P"], None),
        ("TI", "Temperature", "degC", "SHL", "sensor", lambda c: c["T"], None),
    ]
    if boot:
        subs.append(("BOOT", "Water boot", [("BOOTV", "Boot", [])]))
        tags.append(("LI", "Boot interface level", "%", "BOOTV", "sensor", lambda c: 40.0, None))
    if analysers:
        tags += [
            ("AL", "Boot water chloride (lab)", "ppm", "BOOTV", "lab", lambda c: c["chloride"], None),
            ("AI", "Boot water pH", "pH", "BOOTV", "analyser", lambda c: c["ph"], None),
            ("AL", "Boot water iron (lab)", "ppm", "BOOTV", "lab", lambda c: c["iron"], None),
        ]
    return dict(onto="Drum", eq_class="Vessel", subunits=subs, tags=tags)


DRUM = _drum()
DRUM_BOOT = _drum(boot=True)
RECEIVER = _drum(boot=True, analysers=True)

PIPING = dict(
    onto="PipingCircuit", eq_class="Piping circuit",
    subunits=[("PIPE", "Piping", [("STRAIGHT", "Straight runs", []), ("FITTINGS", "Elbows & tees", [])]),
              ("SUPP", "Supports", [("HANGERS", "Hangers & guides", [])])],
    tags=[
        ("CR", "Corrosion probe", "mm/y", "PIPE", "corrosion probe", lambda c: c["cr"], None),
        ("UT", "Minimum wall thickness (TML survey)", "mm", "FITTINGS", "inspection", lambda c: c["wall"], None),
    ],
)

OVH_LINE = dict(onto="PipingCircuit", eq_class="Piping circuit",
                subunits=PIPING["subunits"] + [("INJ", "Injection points", [("QUILLS", "Injection quills", [])])],
                tags=PIPING["tags"] + [
                    ("UY", "Water dew-point margin (calculated)", "degC", "PIPE", "calculated", lambda c: c["dpm"], None)])

CHEM_PACKAGE = dict(
    onto="ChemicalInjectionPackage", eq_class="Chemical injection package",
    subunits=[("TANK", "Day tank", [("TANKSH", "Tank shell", [])]),
              ("MPUMP", "Metering pumps", [("MPA", "Metering pump A", [("DIAPH", "Diaphragm")]), ("MPB", "Metering pump B", [])]),
              ("QUILL", "Injection point", [("QUILLI", "Injection quill", [])])],
    tags=[
        ("FI", "Injection rate", "L/h", "MPUMP", "sensor", lambda c: c["rate"], None),
        ("LI", "Day-tank level", "%", "TANK", "sensor", lambda c: 62.0, None),
    ],
)

TANK = dict(
    onto="StorageTank", eq_class="Storage tank",
    subunits=[("SHELL", "Shell & bottom", [("PLATES", "Shell plates", []), ("FLOOR", "Floor plates", [])]),
              ("ROOF", "Floating roof", [("SEALR", "Rim seal", [])]),
              ("MIX", "Side-entry mixers", [("MIXER", "Mixer", [])])],
    tags=[
        ("LI", "Tank level", "%", "SHELL", "sensor", lambda c: c.get("level", 55.0), None),
        ("TI", "Tank temperature", "degC", "SHELL", "sensor", lambda c: 35.0, None),
        ("AL", "Water & sediment (lab)", "vol%", "SHELL", "lab", lambda c: 0.3, None),
    ],
)

TEMPLATES = {
    "pump": PUMP, "shelltube": SHELL_TUBE, "aircooler": AIR_COOLER, "heater": FIRED_HEATER,
    "desalter": DESALTER, "atmcolumn": ATM_COLUMN, "stripper": SIDE_STRIPPER, "stabiliser": STABILISER,
    "drum": DRUM, "drumboot": DRUM_BOOT, "receiver": RECEIVER, "piping": PIPING, "ovhline": OVH_LINE,
    "chem": CHEM_PACKAGE, "tank": TANK,
}
