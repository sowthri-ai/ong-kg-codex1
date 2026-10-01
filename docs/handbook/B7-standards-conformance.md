# B7 Standards alignment and conformance

**Conclusion first.** OGKG now conforms, by automated check, to the structural and data requirements of eight standards families: OWL 2 DL, W3C knowledge-graph practice (RDF, SHACL, PROV-O, SKOS), ISO 15926-14, IOF / BFO, ISO 14224, ISA-95 / Purdue, CFIHOS and MIMOSA CCOM. Refinery Gamma passes 40 of 40 checks (`data/cdu-gamma/conformance.md`). Two things remain outside our control and are stated openly: code tables published under licence or registration (ISO 14224 Table A.4, the CFIHOS reference data library, the CCOM XML schema) must be confirmed against the client's copies, and no standards body certifies an ontology, so this is evidence of conformance, not a certificate.

The decision this chapter supports: **can a client architect accept OGKG as standards-aligned without remodelling?** Yes for structure. Code-level alignment for CFIHOS and CCOM needs the lookups listed in B7.5 as part of mobilisation.

## B7.1 What "follows a standard" means here

A standard can be followed at five depths. Each mapping in `ontology/alignments/` states which depth it uses, and every external identifier carries an `ogkg:verificationStatus`.

| Depth | Mechanism | Used for |
|---|---|---|
| 1. Logical axiom | `rdfs:subClassOf` / `rdfs:subPropertyOf` to the standard's own OWL IRIs | ISO 15926-14 (LIS-14), IOF, BFO |
| 2. Mapping annotation | `skos:closeMatch` / `skos:relatedMatch` (no OWL semantics) | Correspondences that are close but not subsumption |
| 3. Code annotation | `ogkg:iso14224Code`, `ogkg:isa95EquipmentLevel`, `ogkg:cfihosConcept`, `ogkg:ccomEntity` on classes, inherited down the hierarchy | Standards with no official OWL (ISO 14224, ISA-95, CFIHOS, CCOM) |
| 4. Instance data | `ogkg:purdueLevel`, `ogkg:isa95Function` on individuals | Facts that depend on the deployment, not the class |
| 5. Data requirement | SHACL shapes and `ogkg/conformance.py` checks | The records each standard requires (e.g. an ISO 14224 failure record) |

Logical axioms are used only where subsumption is clean. The test for IOF / BFO is stricter: importing IOF and BFO must not be able to make OGKG inconsistent, so no OGKG class sits under both a BFO continuant and a BFO occurrent (check IOF-1).

## B7.2 Conformance matrix

| Standard | What OGKG takes from it | Module | Automated checks | Status |
|---|---|---|---|---|
| **OWL 2 (W3C)** | Ontology language, DL profile | all `ontology/*.ttl` | OWL-1 structural DL restrictions on ontology and data; OWL-2 disjointness consistency; OWL-3 every used class declared; OWL-4 version IRIs and XML catalog | Pass. `xsd:date` is a documented deviation (ADR-0012) |
| **Knowledge graph (RDF, SHACL, PROV-O, SKOS)** | Stable IRIs, validation, provenance, controlled vocabularies, bitemporal facts | `ogkg-core.ttl`, `ogkg-shapes.ttl`, `ogkg-vocab.ttl` | KG-1 SHACL incl. domain / range; KG-2 IRIs, labels, classes; KG-3 PROV fields; KG-4 SKOS coverage; KG-5 bitemporal facts | Pass |
| **ISO 15926-14 (LIS-14)** | Functional object vs physical object; systems, activities, events, streams, information objects | `alignments/iso15926-14.ttl` | 15926-1 functional / physical split with installation links; 15926-2 type alignment; 15926-3 coverage ≥ 90 %; 15926-4 all LIS-14 IRIs verified | Pass. 21 LIS-14 terms, all verified against the published ontology |
| **IOF Core + Maintenance, BFO** | Upper-ontology commitments; failure events, failure-mode codes, work-order records, maintenance processes | `alignments/iof-bfo.ttl` | IOF-1 BFO-safe; IOF-4 failures, failure-mode codes, work orders and turnarounds under IOF Maintenance classes; IOF-2 coverage ≥ 90 % outside functional locations; IOF-3 verification status | Pass. 19 of 23 IRIs verified in release 202602; 4 from the IOF Core paper, to confirm |
| **ISO 14224:2016** | Taxonomy levels 1–9; equipment class codes; equipment boundary (driver separate); failure record (mode, mechanism, cause, detection); maintenance records | `alignments/iso14224.ttl` | 14224-1 levels; 14224-2 class code for every equipment unit; 14224-3 real class ≥ 95 %; 14224-4 complete failure records; 14224-5 code tables cited; 14224-6 drivers separate; 14224-7 maintenance links; 14224-8 model data | Pass. Codes to confirm against the licensed Table A.4 |
| **ISA-95 (IEC 62264) / Purdue** | Role-based equipment hierarchy; functional levels and MOM activity models; Purdue zones for systems and devices | `alignments/isa95-purdue.ttl`, `ogkg/standards.py` | ISA95-1 hierarchy level for every enterprise, site, area, unit, equipment; ISA95-2 each production unit in one area; ISA95-3 Purdue level per application; ISA95-4 activity model per process; ISA95-5 field devices at level 0 | Pass |
| **CFIHOS** | Tag / equipment / model-part separation; company, document, property value | `alignments/cfihos.ttl` | CFIHOS-1 tag numbers and FL ids; CFIHOS-2 equipment with serial, model and tag; CFIHOS-3 tag-class names ≥ 80 %; CFIHOS-4 equipment recorded for driven rotating tags | Pass structurally. RDL codes: lookup required |
| **MIMOSA OpenO&M CCOM** | Segment / Asset / Model / MeasurementLocation / Measurement / Event / WorkOrder exchange profile | `alignments/mimosa-ccom.ttl` | CCOM-1 every exchanged individual has a CCOM type; CCOM-2 segments form a tree; CCOM-3 measurement locations on segments; CCOM-4 install / removal times | Pass structurally. Element names: confirm against the CCOM XSD |

## B7.3 Modelling decisions the standards forced

**Functional location vs physical item (ISO 15926, CFIHOS, CCOM, ISO 14224).** Until v0.4, L3–L9 spine classes were `PhysicalAsset`. That conflated the position (tag P-101A, SAP functional location) with the pump fitted there (serial S…). v0.5 introduces `ogkg:FunctionalLocation`: every L3–L9 class sits under it, `ogkg:SerialItem` sits under `PhysicalAsset`, the two are disjoint, and `ogkg:installedAt` (with validity dates) links them. All four standards make the same split, so one change aligns all four: LIS-14 `FunctionalObject` / `PhysicalObject`, CFIHOS tag / equipment, CCOM Segment / Asset.

**Direct vs transitive part-of (OWL 2 DL).** `ogkg:partOf` is transitive, and OWL 2 DL forbids cardinality constraints on transitive properties; SHACL's "exactly one parent" would also count inferred ancestors. The asserted edge is now `ogkg:directPartOf ⊑ ogkg:partOf`. Queries without reasoning use `ogkg:directPartOf+`; with reasoning, `ogkg:partOf`. The property graph is unchanged (`PART_OF`).

**Disjoint upper partition (OWL 2).** Functional locations, physical assets, material, events, information, agents and locations are pairwise disjoint (two `owl:AllDisjointClasses` axioms; process elements may also be information objects). Check OWL-2 proves no individual violates them.

**ISA-95 placement.** Refinery units are continuous production, so plant units are ISA-95 `ProductionUnit`, sections are `Unit`, equipment are ISA-88 `EquipmentModule`, instruments and tags are `ControlModule`, tank farms `StorageZone` and tanks `StorageUnit`. ISA-95 areas are modelled as plots (`LOCATED_AT`), because OGKG keeps location separate from the functional hierarchy.

**Purdue levels.** Purdue level is a property of a deployment, so it is instance data: DCS and APC at level 2; historian, LIMS and CEMS at 3; CMMS, RBI, LP and EDMS at 4; transmitters and final elements at 0. They are the input to security zoning in [C6](C6-security-and-nfr.md).

**IOF has no functional-location class.** OGKG maps functional locations to IOF only by `skos:relatedMatch iof:RequiredFunction`. Coverage for IOF is therefore measured outside the functional-location hierarchy (IOF-2), and the 5,356 functional locations are reported separately (IOF-2b).

## B7.4 Known modelling debt

| Item | Why it matters | Plan |
|---|---|---|
| `ogkg:Agent` holds organisations and roles | IOF treats roles as realizable entities, not agents, so `ogkg:Agent` is only `closeMatch iof:Agent` | Split `Role` out of `Agent` in v0.6 |
| `ogkg:Event` holds failures (occurrents) and work-order records (information) | Only subclasses are aligned to IOF / BFO | Keep; documented in `iof-bfo.ttl` |
| Process-spine nodes are process definitions | They map to IOF `BusinessProcess` and LIS-14 `Activity` only by `closeMatch` | Model executions as events when run history is ingested |
| `xsd:date` literals | Outside the OWL 2 datatype map | ADR-0012: keep for SPARQL / SHACL; reasoners run with unsupported-datatype tolerance |

## B7.5 Lookups required before production use

| Standard | Lookup | Owner |
|---|---|---|
| ISO 14224 | Confirm equipment class codes (Table A.4), especially storage tanks (TA) and switchgear (SG) vs power transformers (PT) | Reliability lead, client's licensed copy |
| CFIHOS | Fill RDL tag-class and equipment-class codes for the 16 named classes; confirm plant-breakdown entity names | Information-management lead, project's CFIHOS release |
| MIMOSA CCOM | Confirm XML element names and event, measurement and work-management subtypes against the CCOM XSD in use | Integration architect |
| IOF | Confirm 4 class names taken from the IOF Core paper in the current release RDF | Ontologist |

## B7.6 How to run

```bash
python -m ogkg.cdu_gamma && python -m ogkg.ttl_v02      # build and export
python -m ogkg.owl_profile data/cdu-gamma/structure.ttl data/cdu-gamma/information.ttl
python -m ogkg.conformance                                # writes data/cdu-gamma/conformance.{json,md}
python -m unittest tests.test_standards -v
```

`ogkg/owl_profile.py` is a structural checker, not a reasoner. Running HermiT or ELK over the modules with the upstream LIS-14, IOF and BFO ontologies imported (resolved through `ontology/catalog-v001.xml`) is part of backlog item E1-P1-01 (rdflib, pySHACL and a reasoner in CI).
