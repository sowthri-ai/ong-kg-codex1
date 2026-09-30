# Data contract for `kg.json` (v0.5)

This is the interface between the builders (`ogkg/cdu_gamma.py`, `ogkg/refinery_*.py`), the RDF exporter and validator (`ogkg/ttl_v02.py`, `ogkg/shacl_lite.py`), the access layer (`ogkg/kg.py`, `ogkg/store.py`, `ogkg/mcp_server.py`) and the onboarding connectors (`ogkg/connectors/`). Every field added in v0.5 is **optional**, so readers must tolerate its absence.

## 1. Top level

```json
{"meta": {...}, "nodes": [...], "edges": [...], "facts": [...]}
```

`meta` adds `site` (e.g. `"gamma"`), `version` (e.g. `"0.5.0"`) and `build_id`.

## 2. Nodes

`{id, cls, name, spine, level, desc, props}`. The `id` is unique within a site; the global identity is `props.iri` = `ogkg.identity.iri(id, site)`.

| `props` key | Type | Meaning |
|---|---|---|
| `sector` | `"1a"`, `"1b"` or `"2"` | Existing |
| `onto_class` | string | Most specific OWL class (local name); otherwise `cls` is used |
| `iri` | string | Site-scoped IRI |
| `site` | string | e.g. `"gamma"` |
| `aliases` | list of strings | Other names people and systems use (search and entity resolution) |
| `external_ids` | object | `{system: id}`; systems are `PI`, `SAP_FL`, `SAP_EQ`, `LIMS`, `RBI`, `CMS` (see `ogkg/identity.py`) |
| `sensitivity` | string | `public`, `internal`, `confidential` or `restricted`; default `internal` |
| `plant_unit` | string | Equipment only: the owning L4 unit |
| `running` | bool | Rotating equipment only: running or standby |

Node-class-specific props that the RDF exporter maps:

| `cls` | props → RDF |
|---|---|
| `KPI` | `formula` → `ogkg:formula`; `aggregation` → `ogkg:aggregationRule vocab:<X>`; `level` (int) → `ogkg:applicableLevel ogkg:L<n>`; `tier` (`Strategic`, `Tactical` or `Operational`) → `ogkg:kpiTier vocab:<tier>`. `ownedBy` comes from an `OWNED_BY` edge |
| `KPF` | `DRIVES` and `CONTROLLED_BY` edges |
| `HypothesisAssertion` | `hyp_subject`, `hyp_predicate` (LPG relation name), `hyp_object`, `status` (`Proposed`, `Validated` or `Rejected`), `confidence_score`, `inferred_by`, `run_id`, `reviewed_by` (role id), `reviewed_on` (date), `evidence` (list of node ids) |
| `FacetBinding` | `binds_entity`, `binds_to`, `facet` (vocab concept local name, e.g. `EconomicsFacet`), `binding_level` (int), `valid_from` (date), `inheritance_rule` (optional concept) |
| `CorrectionRequest` | `corrects_fact` (fact id), `proposed_value`, `reason`, `status` (`Proposed`, `Validated` or `Rejected`), `requested_by` (role), `reviewed_by`, `reviewed_on` |
| `IOWLimit` | `level` (`critical`, `standard` or `informational`), `direction` (`high` or `low`); the value, response time and action are facts |

## 3. Edges

`{source, rel, target, props}`. `rel` must be a relation with an `ogkg:lpgType` in the ontology. Optional `props`: `source` (provenance text), `valid_from`, `valid_to`, `confidence`. The exporter reifies an edge that has props as an `ogkg:LinkAssertion`.

### New relations in v0.5

| LPG name | Domain → range | Use |
|---|---|---|
| `DRIVER_OF` | ElectricMotor / driver → EquipmentUnit | Motor or turbine drives a pump or compressor (ISO 14224 boundary: the driver is its own equipment) |
| `PROTECTS` | ReliefDevice → EquipmentUnit | PSV protects equipment |
| `SENSES` | InputDevice → DataPoint | Transmitter produces the tag |
| `CONTROLS` | Valve → DataPoint | Final element of a control loop (controller tag) |
| `SUBJECT_TO` | AssetSpineNode → Phenomenon | e.g. fouling (not a damage mechanism) |
| `RESPONDS_TO` | WorkOrder → IOWExceedance | Response to an exceedance |
| `LIMITS` | IOWLimit → DataPoint | Limit applies to a tag |
| `EXCEEDS` | IOWExceedance → IOWLimit | Which limit was breached |
| `HAS_FAILURE_MECHANISM` | Failure → FailureMechanism | ISO 14224 Table B.2 code node |
| `HAS_FAILURE_CAUSE` | Failure → RootCause | ISO 14224 Table B.3 code node |
| `DETECTED_BY` | Failure → DetectionMethod | ISO 14224 Table B.4 code node |
| `IN_PRICE_SET` | PriceSeries → PriceSet | Scenario membership |
| `SUBMODEL_OF` | LPSubmodel → LPModel | |
| `REPRESENTS` | LPSubmodel → PlantUnit | |
| `CONSTRAINS` | LPConstraint → Entity | Unit, product or network constrained |

Existing relations used more widely in v0.5 include `INSTALLED_AT` (SerialItem → EquipmentUnit, with `valid_from` and `valid_to`), `HAS_FAILURE_MODE`, `CAUSED_BY`, `IN_SCOPE_OF`, `TARGETS`, `AT_SITE`, `PRICE_OF`, `COMPONENT_OF`, `BLENDED_AT`, `SOLD_TO`, `MEASURES`, `MEASURED_BY`, `DRIVES` (KPF → KPI) and `CONTROLLED_BY` (KPF → DecisionPoint).

### New classes in v0.5

- **Equipment:** `ElectricMotor` ⊑ RotatingEquipment; `SteamTurbine` ⊑ RotatingEquipment; `Valve` ⊑ EquipmentUnit; `ReliefDevice`, `ControlValve` and `ShutdownValve` ⊑ Valve; `InputDevice` ⊑ EquipmentUnit; `ElectricalDistribution` ⊑ EquipmentUnit.
- **Asset position:** `FunctionalLocation`, with EquipmentUnit ⊑ FunctionalLocation. SerialItem stays the physical unit.
- **Integrity:** `IOWLimit` ⊑ InformationObject; `FailureMechanism` and `DetectionMethod` ⊑ ProblemElement (FailureMode and RootCause already exist).
- **Economics and planning:** `PriceSet` ⊑ EconomicElement; `LPModel` and `LPSubmodel` ⊑ InformationObject; `LPConstraint` ⊑ EconomicElement.
- **Governance:** `CorrectionRequest` ⊑ HypothesisAssertion (a proposed change to a fact).
- **Sections:** `SaturatedGasPlant` and similar are just new `onto_class` values for sections and units, and must be declared in `ontology/ext/`.

## 4. Facts

Existing fields: `{id, subject, predicate, value, unit, as_of, source_system, source_ref, owner, confidence, method, lineage}`.

| New field | Type | Meaning |
|---|---|---|
| `valid_from` | date | Start of validity. Defaults to `as_of` |
| `valid_to` | date or null | End of validity; null means open |
| `recorded_at` | datetime | When the KG recorded it (build time for synthetic data) |
| `status` | `current`, `superseded` or `retracted` | Default `current` |
| `supersedes` | fact id or null | The fact this one replaces |
| `sensitivity` | as for nodes | Default by predicate family (economics → `confidential`) |
| `basis` | string | Value facts only: `recurring-annual`, `one-off`, `at-risk-per-day`, `snapshot` or `gross-pre-capex` |
| `value_low`, `value_high` | number | Optional range around `value` |

**Time semantics.**
- There may be several facts for the same (subject, predicate), such as a monthly history. The current value is the `status == current` fact with the latest `valid_from`.
- `value(s, p, as_of=D)` picks the current fact with `valid_from <= D` and a null `valid_to` or a `valid_to > D`.

**Confidence rule.** A calculated fact's confidence is never higher than its weakest lineage input.

**Fact IDs** come from `ogkg.identity.fact_id`. Consumers must treat them as opaque strings.

**Units.** Every numeric fact has a unit label from the set mapped in `ontology/mappings/units.ttl`. Labels in use: `%`, `% of rating`, `A`, `L/h`, `MMBtu/kbbl`, `MMSCFD`, `MW`, `MWh`, `Nm3/h`, `PTB`, `USD`, `USD/MMBtu`, `USD/bbl`, `USD/t`, `USD/tCO2`, `USD/MWh`, `USD/d`, `USD/yr`, `USD/m3`, `bar`, `barg`, `berths`, `count`, `days`, `degAPI`, `degC`, `degC/month`, `fraction`, `h`, `kNm3/h`, `kV`, `kVA`, `kW`, `kbbl`, `kbd`, `kg/m3`, `kgCO2/bbl`, `kgCO2/GJ`, `kt/yr`, `ktCO2/yr`, `m`, `m2`, `m2K/kW`, `m3`, `m3/h`, `mg/Nm3`, `mgKOH/g`, `mm`, `mm/s`, `mm/y`, `mmH2O`, `months`, `pH`, `ppm`, `ppmv`, `ppmw`, `rpm`, `scf/bbl`, `state`, `t`, `t/d`, `t/h`, `t/m3`, `um`, `vol%`, `wt%`, `wt/wt`, `yr`, `MPa`, `bara`, `RON`, `cetane`, `GJ/t`. The label is `""` for non-numeric facts.

## 5. Sources and freshness

`source_system` stays a human-readable name. Where a fact comes from a modelled application, an edge from the ApplicationInstance with `SYSTEM_OF_RECORD_FOR` to the data object is enough; the exporter maps the name to the instance through `SOURCE_TO_APP` in `ogkg/ttl_v02.py`.

Freshness SLAs by source family live in `ogkg/policy.py`:

| Source family | SLA |
|---|---|
| PI historian | 1 h |
| LIMS | 24 h |
| CMMS | 24 h |
| Hydrocarbon accounting | 31 d |
| Design (EDMS, design basis) | never stale |
| Planning | 31 d |
