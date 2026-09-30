"""
O&G Value Chain Knowledge Graph — core ontology.

Design
------
* One shared trunk:      L0 Oil & Gas  ->  L1 Segment (Upstream / Midstream / Downstream)
* Two spines from L2:    ASSET spine   (ISO 14224 taxonomy, extended to L10 data points)
                         PROCESS spine (value stream -> ... -> data element)
* Cross-cutting context: MATERIAL (crude grades, cargoes, streams, products, markets)
                         EVENT    (IOW exceedances, failures, work orders, turnarounds)
* Every number is a FACT with provenance (source, as-of, owner, confidence, method, lineage),
  so any AI that answers from the graph can cite and be audited.

The ontology is platform-neutral: it serialises to OWL/Turtle and to a labelled
property graph (Neo4j CSV / Cypher), and maps to Cognite DM, OSDU, GraphDB, etc.
"""

LEVELS = {
    "asset": {
        0: ("Industry", "Oil & Gas", "ISO 14224 L1"),
        1: ("Segment", "Upstream / Midstream / Downstream", "ISO 14224 L2"),
        2: ("BusinessCategory", "Refining, Petrochemicals, E&P, Pipelines & Terminals", "ISO 14224 L2/L3"),
        3: ("Installation", "Refinery, field, terminal (site)", "ISO 14224 L3"),
        4: ("PlantUnit", "Process unit: CDU, VDU, FCC, Reformer, Blender", "ISO 14224 L4"),
        5: ("SectionSystem", "Section / system: overhead, preheat, resid system", "ISO 14224 L5"),
        6: ("EquipmentUnit", "Equipment: pump, exchanger, vessel, piping circuit", "ISO 14224 L6"),
        7: ("Subunit", "Subunit: seal system, tube bundle, bearing housing", "ISO 14224 L7"),
        8: ("MaintainableItem", "Maintainable item: mechanical seal, tubes, bearing", "ISO 14224 L8"),
        9: ("Part", "Part: seal face, O-ring", "ISO 14224 L9"),
        10: ("DataPoint", "Sensor tag, LIMS result, calculated KPI (time series)", "Extension (ISA-95 L1/L2)"),
    },
    "process": {
        0: ("Industry", "Oil & Gas", "Shared trunk"),
        1: ("Segment", "Upstream / Midstream / Downstream", "Shared trunk"),
        2: ("ValueStream", "Crude-to-Product, Plan-to-Maintain", "APQC-style L1"),
        3: ("ProcessGroup", "Crude supply, planning, operations, integrity", "APQC-style L2"),
        4: ("Process", "Crude selection, LP planning, blending, IOW management", "APQC-style L3"),
        5: ("SubProcess", "Assay evaluation, recipe optimisation", "APQC-style L4"),
        6: ("Activity", "Screen contaminants, optimise recipe", "APQC-style L5"),
        7: ("Task", "Check TAN/salt vs limits, update component qualities", "Task"),
        8: ("DecisionPoint", "Accept crude, release recipe, freeze TA scope", "Decision / control point"),
        9: ("DataObject", "Assay, LP case, blend recipe, IOW register", "Business object"),
        10: ("DataElement", "TAN, chloride ppm, reformate RON", "Data element / fact"),
    },
}

# Context classes (not on a spine, linked into both)
CONTEXT_CLASSES = {
    "material": ["CrudeGrade", "CrudeCampaign", "Stream", "Product", "Market"],
    "event": ["IOWExceedance", "Failure", "WorkOrder", "Turnaround", "ScopeItem"],
    "org": ["Role"],
}

RELATIONS = {
    # hierarchy
    "PART_OF": "child -> parent within a spine (level strictly decreasing)",
    # cross-spine
    "ACTS_ON": "process-spine node -> asset-spine node it operates on",
    "GOVERNS": "decision point (L8) -> asset it controls",
    "INSTANTIATED_BY": "process data element (L10) -> asset data point (L10) that measures it",
    "CONSUMES": "decision point (L8) -> data element it uses as input",
    "OWNED_BY": "process / data element -> accountable role",
    # material flow
    "OF_GRADE": "campaign -> crude grade",
    "DELIVERED_VIA": "campaign -> terminal / installation",
    "PRODUCED_AT": "crude grade -> producing installation",
    "PROCESSED_IN": "campaign -> plant unit",
    "PRODUCES": "plant unit -> stream",
    "FEEDS": "stream -> plant unit",
    "COMPONENT_OF": "stream -> product",
    "SOLD_TO": "product -> market",
    "BLENDED_AT": "product -> blending unit",
    "SUPPLIES": "installation -> installation (e.g. field/terminal -> refinery)",
    # events
    "ON_DATAPOINT": "IOW exceedance -> data point",
    "FAILURE_OF": "failure -> equipment / item",
    "REMEDIATES": "work order -> failure",
    "AT_SITE": "turnaround -> installation",
    "IN_SCOPE_OF": "scope item -> turnaround",
    "TARGETS": "scope item -> equipment",
}

# Fact contract — every value an AI may quote
FACT_FIELDS = [
    "id", "subject", "predicate", "value", "unit", "as_of",
    "source_system", "source_ref", "owner", "confidence", "method", "lineage",
]
CONFIDENCE = ["high", "medium", "low"]
METHODS = ["measured", "recorded", "calculated", "declared", "indicative", "assumption"]

STANDARDS = [
    ("ISO 14224", "Asset taxonomy L1-L9, failure modes & mechanisms"),
    ("ISO 15926 / CFIHOS", "Engineering data & equipment class library"),
    ("DEXPI", "P&ID exchange"),
    ("ISA-95", "Enterprise-control integration levels"),
    ("IOF / BFO", "Industrial Ontologies Foundry upper ontology"),
    ("API 584", "Integrity operating windows"),
    ("API 580/581", "Risk-based inspection"),
    ("OSDU", "Upstream data platform alignment"),
]
