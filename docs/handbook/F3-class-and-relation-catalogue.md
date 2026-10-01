# F3 Class and relation catalogue

> Generated from `ontology/ogkg-core.ttl` by `python -m ogkg.catalogue`. Do not edit by hand; change the ontology and regenerate.

Ontology version 0.5.0 · 129 classes · 108 object properties · 37 datatype properties.

## F3.1 Spine classes by level

| Level | Class | Parent class | Aligned to |
|---|---|---|---|
| L0 | `Industry` | TrunkNode | ISO 14224 level 1 |
| L1 | `Segment` | TrunkNode | ISO 14224 level 2 |
| L2 | `BusinessCategory` | AssetSpineNode | ISO 14224 level 2 |
| L2 | `ValueStream` | ProcessSpineNode |  |
| L3 | `Installation` | AssetSpineNode, FunctionalLocation | ISO 14224 level 3 |
| L3 | `ProcessGroup` | ProcessSpineNode |  |
| L4 | `PlantUnit` | AssetSpineNode, FunctionalLocation | ISO 14224 level 4 |
| L4 | `Process` | ProcessSpineNode |  |
| L5 | `SectionSystem` | AssetSpineNode, FunctionalLocation | ISO 14224 level 5 |
| L5 | `SubProcess` | ProcessSpineNode |  |
| L6 | `Activity` | ProcessSpineNode |  |
| L6 | `EquipmentUnit` | AssetSpineNode, FunctionalLocation | ISO 14224 level 6 |
| L7 | `Subunit` | AssetSpineNode, FunctionalLocation | ISO 14224 level 7 |
| L7 | `Task` | ProcessSpineNode |  |
| L8 | `DecisionPoint` | ProcessSpineNode |  |
| L8 | `MaintainableItem` | AssetSpineNode, FunctionalLocation | ISO 14224 level 8 |
| L9 | `DataObject` | ProcessSpineNode, InformationObject |  |
| L9 | `Part` | AssetSpineNode, FunctionalLocation | ISO 14224 level 9 |
| L10 | `DataElement` | ProcessSpineNode, InformationObject |  |
| L10 | `DataPoint` | AssetSpineNode, InformationObject | OGKG extension (ISA-95 levels 1-2 data) |

## F3.2 Other classes

| Class | Parent class | Notes |
|---|---|---|
| `Entity` |  |  |
| `FacetBinding` |  | Reified binding between an entity and a backbone node, with level, scope and validity. |
| `Level` |  |  |
| `BusinessUnit` | Agent |  |
| `Enterprise` | Agent | W3C ORG FormalOrganization; LEI |
| `Role` | Agent | W3C ORG Role |
| `CostElement` | EconomicElement |  |
| `LPConstraint` | EconomicElement | Active LP constraint with a shadow price. |
| `PriceSeries` | EconomicElement | Licensed data: client tenancy only (D3). |
| `PriceSet` | EconomicElement | A consistent price scenario (e.g. plan, actual, stress). |
| `ValueCoefficient` | EconomicElement | Dollar value of moving a KPF, e.g. USD per RON-bbl. |
| `ValueDriver` | EconomicElement |  |
| `Agent` | Entity | W3C ORG / PROV agent |
| `Event` | Entity | BFO occurrent |
| `FunctionalLocation` | Entity | A position in the plant defined by the function it must perform, independent of the physical item installed there (ISO 14224 L3-L9 taxonomy; ISO 15926 functional object; CFIHOS tag; SAP functional location; MIMOSA CCOM Segment). Physical items are ogkg:SerialItem, linked by ogkg:installedAt. |
| `Grouping` | Entity | Target of dotted-branch MEMBER_OF links (B3). |
| `InformationObject` | Entity | IAO information content entity |
| `Location` | Entity | GeoSPARQL feature |
| `MaterialItem` | Entity | Crude grades, campaigns, streams, products, markets. |
| `PhysicalAsset` | Entity | BFO material entity |
| `ProcessElement` | Entity | IOF business process / plan specification |
| `SpineNode` | Entity |  |
| `ElectricalDistribution` | EquipmentUnit | ISO 14224 electrical equipment (switchgear / power transformers) |
| `InputDevice` | EquipmentUnit | ISO 14224 equipment class: Input devices |
| `RotatingEquipment` | EquipmentUnit |  |
| `StaticEquipment` | EquipmentUnit |  |
| `Valve` | EquipmentUnit | ISO 14224 equipment class: Valves |
| `Failure` | Event | ISO 14224 failure event |
| `IOWExceedance` | Event | API 584 |
| `ScopeItem` | Event |  |
| `Turnaround` | Event |  |
| `WorkOrder` | Event |  |
| `CorrosionLoop` | Grouping | API 580/581 corrosion loop |
| `CostCentre` | Grouping |  |
| `Fleet` | Grouping | Equipment of the same model and service band across sites. |
| `SafetyInstrumentedFunction` | Grouping | IEC 61511 |
| `Utility` | Grouping |  |
| `AirCooledHX` | HeatExchanger |  |
| `ShellAndTubeHX` | HeatExchanger | TEMA |
| `CorrectionRequest` | HypothesisAssertion | A proposed change to a fact, governed like a hypothesis. |
| `Application` | InformationObject | A software product or category, e.g. LIMS. |
| `ApplicationInstance` | InformationObject | A deployed instance, e.g. LIMS-Alpha. |
| `ApplicationModule` | InformationObject |  |
| `Document` | InformationObject |  |
| `DocumentChunk` | InformationObject |  |
| `EconomicElement` | InformationObject |  |
| `EquipmentModel` | InformationObject | A maker's design, e.g. OEM-A HX-300. |
| `IOWLimit` | InformationObject | API 584 integrity operating window limit |
| `InsightResult` | InformationObject | Snapshot of an insight run (headline, value with basis and range), linked to the entities it describes. |
| `Interface` | InformationObject |  |
| `LPModel` | InformationObject | Refinery planning linear programme. |
| `LPSubmodel` | InformationObject | Unit submodel (yield vectors, capacities) of an LP model. |
| `PerformanceMeasure` | InformationObject | ISO 22400 |
| `PhysicsElement` | InformationObject |  |
| `ProblemElement` | InformationObject |  |
| `Area` | Location |  |
| `Country` | Location | ISO 3166 |
| `Plot` | Location |  |
| `Region` | Location |  |
| `Bearing` | MaintainableItem |  |
| `MechanicalSeal` | MaintainableItem | API 682 |
| `TubeSet` | MaintainableItem |  |
| `CrudeCampaign` | MaterialItem | Crude processed in a unit over a time window (one or more cargoes). |
| `CrudeGrade` | MaterialItem |  |
| `Market` | MaterialItem |  |
| `Product` | MaterialItem |  |
| `Stream` | MaterialItem |  |
| `KPF` | PerformanceMeasure | Key performance factor: a controllable lever. |
| `KPI` | PerformanceMeasure |  |
| `Metric` | PerformanceMeasure |  |
| `DamageMechanism` | Phenomenon | API 571 |
| `SerialItem` | PhysicalAsset | A physical unit with a serial number, installed at a functional location. |
| `Discipline` | PhysicsElement |  |
| `Equation` | PhysicsElement |  |
| `Parameter` | PhysicsElement |  |
| `Phenomenon` | PhysicsElement |  |
| `BlendingUnit` | PlantUnit |  |
| `CatalyticReformer` | PlantUnit |  |
| `CrudeDistillationUnit` | PlantUnit |  |
| `FluidCatalyticCracker` | PlantUnit |  |
| `VacuumDistillationUnit` | PlantUnit |  |
| `DetectionMethod` | ProblemElement | ISO 14224:2016 Table B.4 detection method |
| `FailureMechanism` | ProblemElement | ISO 14224:2016 Table B.2 failure mechanism |
| `FailureMode` | ProblemElement | ISO 14224 failure mode |
| `ProblemPattern` | ProblemElement | Class-level problem signature (B6.2). |
| `RootCause` | ProblemElement |  |
| `CentrifugalPump` | Pump | API 610 |
| `Compressor` | RotatingEquipment |  |
| `ElectricMotor` | RotatingEquipment | ISO 14224 equipment class: Electric motors |
| `Pump` | RotatingEquipment | ISO 14224 equipment class: Pumps |
| `SteamTurbine` | RotatingEquipment | ISO 14224 equipment class: Steam turbines |
| `DesalterSystem` | SectionSystem |  |
| `OverheadSystem` | SectionSystem |  |
| `PreheatTrain` | SectionSystem |  |
| `ResidSystem` | SectionSystem |  |
| `AssetSpineNode` | SpineNode |  |
| `TrunkNode` | SpineNode |  |
| `ProcessSpineNode` | SpineNode, ProcessElement |  |
| `FiredHeater` | StaticEquipment |  |
| `HeatExchanger` | StaticEquipment |  |
| `PipingCircuit` | StaticEquipment | API 570 circuit |
| `StorageTank` | StaticEquipment |  |
| `Vessel` | StaticEquipment |  |
| `ControlValve` | Valve | IEC 60534 |
| `ReliefDevice` | Valve | API 520 / API 526 pressure-relief valve |
| `ShutdownValve` | Valve | IEC 61511 final element |
| `Column` | Vessel |  |
| `Fact` | prov:Entity | A cited value. All fields in FactShape are mandatory. |
| `HypothesisAssertion` | prov:Entity |  |

## F3.3 Object properties (relationships)

| Property | Property-graph type | Domain | Range | Facet | DNA channel | Characteristics |
|---|---|---|---|---|---|---|
| `actsOn` | `ACTS_ON` | ProcessSpineNode | AssetSpineNode |  |  |  |
| `affectsKPI` | `AFFECTS_KPI` | Event | KPI |  |  |  |
| `aggregationRule` | `AGGREGATES_BY` | PerformanceMeasure | skos:Concept |  |  |  |
| `applicableLevel` | `APPLIES_AT` | PerformanceMeasure | Level |  |  |  |
| `atRiskOf` | `AT_RISK_OF` | AssetSpineNode | ProblemPattern |  |  |  |
| `atSite` | `AT_SITE` | Turnaround | Installation |  |  |  |
| `bindingFacet` | `` | FacetBinding | skos:Concept |  |  |  |
| `bindingLevel` | `` | FacetBinding | Level |  |  |  |
| `bindsEntity` | `` | FacetBinding | Entity |  |  |  |
| `bindsTo` | `` | FacetBinding | Entity |  |  |  |
| `blendedAt` | `BLENDED_AT` | Product | PlantUnit |  |  |  |
| `causedBy` | `CAUSED_BY` | Event | Entity |  |  |  |
| `chunkOf` | `CHUNK_OF` | DocumentChunk | Document |  |  |  |
| `componentOf` | `COMPONENT_OF` | Stream | Product |  |  |  |
| `computedFrom` | `COMPUTED_FROM` | PerformanceMeasure | PerformanceMeasure |  |  |  |
| `confidence` | `` | Fact | skos:Concept |  |  |  |
| `constrains` | `CONSTRAINS` | LPConstraint | Entity |  |  |  |
| `consumes` | `CONSUMES` | DecisionPoint | DataElement |  |  |  |
| `controlledBy` | `CONTROLLED_BY` | KPF | DecisionPoint | vocab:PerformanceFacet |  |  |
| `controls` | `CONTROLS` | Valve | DataPoint |  |  |  |
| `costBooksTo` | `BOOKS_TO` | Event | CostElement | vocab:EconomicsFacet |  |  |
| `decidedBy` | `DECIDED_BY` | Event | DecisionPoint |  |  |  |
| `deliveredVia` | `DELIVERED_VIA` | CrudeCampaign | Installation |  |  |  |
| `derivedFrom` | `DERIVED_FROM` | Fact | Fact |  |  |  |
| `describes` | `DESCRIBES` | InformationObject | Entity | vocab:KnowledgeFacet |  |  |
| `detectedBy` | `DETECTED_BY` | Failure | DetectionMethod |  |  |  |
| `directPartOf` | `PART_OF` | SpineNode | SpineNode |  |  |  |
| `driverOf` | `DRIVER_OF` | RotatingEquipment | RotatingEquipment |  |  |  |
| `drives` | `DRIVES` | KPF | KPI | vocab:PerformanceFacet |  |  |
| `evidence` | `` | HypothesisAssertion | Entity |  |  |  |
| `exceeds` | `EXCEEDS` | IOWExceedance | IOWLimit |  |  |  |
| `factOwner` | `` | Fact | Role |  |  |  |
| `factStatus` | `` | Fact | skos:Concept |  |  |  |
| `failureOf` | `FAILURE_OF` | Failure | AssetSpineNode | vocab:ProblemsFacet |  |  |
| `feeds` | `FEEDS` | Stream | PlantUnit |  | vocab:ExposureChannel |  |
| `governedBy` | `GOVERNED_BY` | AssetSpineNode | Equation | vocab:PhysicsFacet | vocab:TypeChannel |  |
| `governs` | `GOVERNS` | DecisionPoint | AssetSpineNode |  |  |  |
| `hasFact` | `HAS_FACT` |  |  |  |  |  |
| `hasFailureCause` | `HAS_FAILURE_CAUSE` | Failure | RootCause |  |  |  |
| `hasFailureMechanism` | `HAS_FAILURE_MECHANISM` | Failure | FailureMechanism |  |  |  |
| `hasFailureMode` | `HAS_FAILURE_MODE` | Failure | FailureMode |  |  |  |
| `hasLevel` | `HAS_LEVEL` | SpineNode | Level |  |  | FunctionalProperty |
| `hasTag` | `HAS_TAG` | Entity | skos:Concept | vocab:IdentityFacet |  |  |
| `hasVariable` | `HAS_VARIABLE` | Equation | Parameter |  |  |  |
| `hostsDataPoint` | `HOSTS` | ApplicationInstance | DataPoint | vocab:ApplicationFacet |  |  |
| `hypObject` | `` | HypothesisAssertion | Entity |  |  |  |
| `hypSubject` | `` | HypothesisAssertion | Entity |  |  |  |
| `inPriceSet` | `IN_PRICE_SET` | PriceSeries | PriceSet |  |  |  |
| `inScopeOf` | `IN_SCOPE_OF` | ScopeItem | Turnaround |  |  |  |
| `inheritanceRule` | `` | FacetBinding | skos:Concept |  |  |  |
| `installedAt` | `INSTALLED_AT` | SerialItem | EquipmentUnit | vocab:DesignFacet |  |  |
| `instanceOf` | `INSTANCE_OF` | ApplicationInstance | Application |  |  |  |
| `instantiatedBy` | `INSTANTIATED_BY` | DataElement | DataPoint |  |  |  |
| `integratesWith` | `INTEGRATES_WITH` | ApplicationInstance | ApplicationInstance |  |  | SymmetricProperty |
| `isa95Function` | `` | ProcessSpineNode | skos:Concept |  |  |  |
| `kpiTier` | `HAS_TIER` | KPI | skos:Concept |  |  |  |
| `limits` | `LIMITS` | IOWLimit | DataPoint |  |  |  |
| `locatedAt` | `LOCATED_AT` | Entity | Location | vocab:LocationFacet | vocab:LineageChannel |  |
| `manufacturedBy` | `MANUFACTURED_BY` | EquipmentModel | Enterprise | vocab:DesignFacet |  |  |
| `matchesPattern` | `MATCHES_PATTERN` | Event | ProblemPattern |  |  |  |
| `measuredBy` | `MEASURED_BY` | PerformanceMeasure | DataPoint | vocab:PerformanceFacet |  |  |
| `measures` | `MEASURES` | PerformanceMeasure | Entity | vocab:PerformanceFacet |  |  |
| `memberOf` | `MEMBER_OF` | Entity | Grouping |  |  |  |
| `method` | `` | Fact | skos:Concept |  |  |  |
| `mitigatedBy` | `MITIGATED_BY` | DamageMechanism | DecisionPoint |  |  |  |
| `moduleOf` | `MODULE_OF` | ApplicationModule | Application |  |  |  |
| `occurredOnSerial` | `OCCURRED_ON_SERIAL` | Failure | SerialItem |  |  |  |
| `ofGrade` | `OF_GRADE` | CrudeCampaign | CrudeGrade |  |  |  |
| `ofModel` | `OF_MODEL` | Entity | EquipmentModel | vocab:DesignFacet | vocab:TypeChannel |  |
| `onDataPoint` | `ON_DATAPOINT` | IOWExceedance | DataPoint |  |  |  |
| `operatedBy` | `OPERATED_BY` |  | Enterprise | vocab:EnterpriseFacet | vocab:LineageChannel |  |
| `ownedBy` | `OWNED_BY` |  | Role | vocab:EnterpriseFacet |  |  |
| `ownedByEnterprise` | `OWNED_BY_ENTERPRISE` |  | Enterprise | vocab:EnterpriseFacet |  |  |
| `parameterMeasuredAs` | `MEASURED_AS` | Parameter | DataElement |  |  |  |
| `partOf` | `` | SpineNode | SpineNode |  |  | TransitiveProperty |
| `priceOf` | `PRICE_OF` | PriceSeries | MaterialItem | vocab:EconomicsFacet |  |  |
| `processedIn` | `PROCESSED_IN` | CrudeCampaign | PlantUnit |  | vocab:ExposureChannel |  |
| `producedAt` | `PRODUCED_AT` | CrudeGrade | Installation |  |  |  |
| `produces` | `PRODUCES` | PlantUnit | Stream |  | vocab:ExposureChannel |  |
| `protects` | `PROTECTS` | ReliefDevice | EquipmentUnit |  |  |  |
| `remediates` | `REMEDIATES` | WorkOrder | Failure |  |  |  |
| `represents` | `REPRESENTS` | LPSubmodel | PlantUnit |  |  |  |
| `resolvedBy` | `RESOLVED_BY` | Event | WorkOrder |  |  |  |
| `respondsTo` | `RESPONDS_TO` | WorkOrder | IOWExceedance |  |  |  |
| `reviewedBy` | `` | HypothesisAssertion | Role |  |  |  |
| `scopedTo` | `SCOPED_TO` | ApplicationInstance | SpineNode | vocab:ApplicationFacet | vocab:LineageChannel |  |
| `sealPlan` | `HAS_SEAL_PLAN` |  | skos:Concept | vocab:DesignFacet | vocab:TypeChannel |  |
| `senses` | `SENSES` | InputDevice | DataPoint |  |  |  |
| `sensitivity` | `HAS_SENSITIVITY` |  | skos:Concept |  |  |  |
| `similarTo` | `SIMILAR_TO` | Event | Event |  |  | SymmetricProperty |
| `soldTo` | `SOLD_TO` | Product | Market |  |  |  |
| `sourceSystem` | `` | Fact | ApplicationInstance |  |  |  |
| `staleInputTo` | `STALE_INPUT_TO` | DataElement | DecisionPoint |  |  |  |
| `status` | `` | HypothesisAssertion | skos:Concept |  |  |  |
| `subject` | `` | Fact | Entity |  |  | FunctionalProperty |
| `subjectTo` | `SUBJECT_TO` | AssetSpineNode | Phenomenon |  |  |  |
| `submodelOf` | `SUBMODEL_OF` | LPSubmodel | LPModel |  |  |  |
| `supersedes` | `` | Fact | Fact |  |  |  |
| `supplies` | `SUPPLIES` | Installation | Installation |  |  |  |
| `supports` | `SUPPORTS` | ApplicationInstance | ProcessSpineNode | vocab:ApplicationFacet |  |  |
| `susceptibleTo` | `SUSCEPTIBLE_TO` | AssetSpineNode | DamageMechanism | vocab:PhysicsFacet | vocab:TypeChannel |  |
| `systemOfRecordFor` | `SYSTEM_OF_RECORD_FOR` | ApplicationInstance | InformationObject | vocab:ApplicationFacet |  |  |
| `targets` | `TARGETS` | ScopeItem | AssetSpineNode |  |  |  |
| `tubeMetallurgy` | `HAS_TUBE_METALLURGY` |  | skos:Concept | vocab:DesignFacet | vocab:TypeChannel |  |
| `unit` | `` | Fact | qudt:Unit |  |  |  |
| `valueStatus` | `` |  | skos:Concept |  |  |  |
| `valuedAt` | `VALUED_AT` | KPF | ValueCoefficient | vocab:EconomicsFacet |  |  |
| `withinLocation` | `WITHIN` | Location | Location |  |  | TransitiveProperty |

## F3.4 Datatype properties

| Property | Domain | Range | Facet | Inheritable |
|---|---|---|---|---|
| `alias` | Entity | xsd:string | vocab:IdentityFacet | false |
| `apiGravity` | CrudeGrade | xsd:decimal | vocab:FlowFacet |  |
| `asOf` | Fact | xsd:date |  |  |
| `confidenceScore` | HypothesisAssertion | xsd:decimal |  |  |
| `designPressure` |  | xsd:decimal | vocab:DesignFacet | true |
| `designTemperature` |  | xsd:decimal | vocab:DesignFacet | true |
| `eqClass` | EquipmentUnit | xsd:string | vocab:DesignFacet |  |
| `eventDate` | Event | xsd:date |  |  |
| `expression` | Equation | xsd:string |  |  |
| `externalId` | Entity | xsd:string | vocab:IdentityFacet | false |
| `formula` | PerformanceMeasure | xsd:string |  |  |
| `freshnessSlaHours` | DataElement | xsd:decimal |  |  |
| `hypPredicate` | HypothesisAssertion | xsd:string |  |  |
| `inferredBy` | HypothesisAssertion | xsd:string |  |  |
| `isa95Layer` | Application | xsd:integer |  |  |
| `mapsToPredicate` | DataElement | xsd:string |  |  |
| `predicateKey` | Fact | xsd:string |  |  |
| `purdueLevel` |  | xsd:decimal |  |  |
| `reviewedOn` | HypothesisAssertion | xsd:date |  |  |
| `runId` | HypothesisAssertion | xsd:string |  |  |
| `saltContent` | CrudeGrade | xsd:decimal | vocab:FlowFacet |  |
| `samplingIntervalHours` | DataPoint | xsd:decimal |  |  |
| `servicePressure` |  | xsd:decimal | vocab:FlowFacet | true |
| `serviceTemperature` |  | xsd:decimal | vocab:FlowFacet | true |
| `sourceRef` | Fact | xsd:string |  |  |
| `sourceSystemName` | Fact | xsd:string |  |  |
| `sulfurContent` | CrudeGrade | xsd:decimal | vocab:FlowFacet |  |
| `tan` | CrudeGrade | xsd:decimal | vocab:FlowFacet |  |
| `validFrom` |  | xsd:date |  |  |
| `validTo` |  | xsd:date |  |  |
| `validityRange` | Equation | xsd:string |  |  |
| `value` | Fact |  |  |  |
| `valueBasis` | Fact | xsd:string |  |  |
| `valueHigh` | Fact | xsd:decimal |  |  |
| `valueLow` | Fact | xsd:decimal |  |  |
| `windowEnd` | CrudeCampaign | xsd:date |  |  |
| `windowStart` | CrudeCampaign | xsd:date |  |  |
