# B6 Problems and hypotheses

## B6.1 Problems are first-class entities

A problem isn't a free-text field on a work order. It is a node, linked through an explicit causal chain:

```
Symptom ──▶ Failure mode ──▶ Mechanism ──▶ Root cause ──▶ Contributing factors
(tube leak)  (ELP, ISO 14224)  (HCl / NH4Cl     (high-salt crude   (desalter efficiency,
                                corrosion)        processed)          wash-water rate)
```

| Relation | Connects a problem to | Example |
|---|---|---|
| `OBSERVED_ON` | The asset where it appeared | FL-002 observed on E-101B tubes |
| `CAUSED_BY` | Mechanism (physics backbone) | → overhead chloride corrosion (API 571) |
| `AFFECTS_KPI` | Performance | → CDU-1 availability, Alpha GRM |
| `COSTS` | Economics | → $160k repair + $1.64M lost margin |
| `DECIDED_BY` | The L8 decision that allowed or fixes it | → DEC-CRBUY, DEC-NEUT |
| `RESOLVED_BY` | Work order or MOC | → WO-002 |
| `RECURS_AT` / `SIMILAR_TO` | The same problem elsewhere | → E-101A (FL-001) |

## B6.2 Problem-pattern library

Patterns are class-level problems that every new incident is matched against. They are how lessons learned travel between sites.

| Pattern | Signature | Matched instances (demo) |
|---|---|---|
| HX-300 seal failure in hot service | Model HX-300 + service ≥ 340 °C + Plan 32 seal | 14 failures, 4 pumps, 2 sites |
| Overhead chloride corrosion | Salt > 20 PTB crude + carbon-steel overhead | FL-001, FL-002, FL-003 |
| Naphthenic acid corrosion | TAN > 0.5 crude + hot transfer line | FL-004 (PC-201) |
| Stale quality input to blend decision | Sampling interval > freshness SLA | Reformate RON at Alpha |

Signature thresholds are illustrative and must be confirmed by client integrity and reliability SMEs.

## B6.3 Six ways the graph connects the dots

| # | Method | O&G example | Analogy | Runs in |
|---|---|---|---|---|
| 1 | Multi-hop traversal | Crude → unit → failure → cost | Following the money | Property graph |
| 2 | Rule inference | Carbon steel + salt > 20 PTB ⇒ at risk of overhead corrosion | Known mechanism of action | Triplestore |
| 3 | Time + topology co-occurrence | Failures within 30 days on units the crude reached | Placing people at the scene | Property graph |
| 4 | DNA similarity | Same model and service at another site ⇒ at risk | Drug repurposing | Property graph |
| 5 | Link prediction (graph ML) | Predict missing crude → damage-mechanism links | Drug–target interaction prediction | Property graph + ML |
| 6 | Hidden-hub analysis | One lab schedule or chemical vendor behind several problems | The common contact | Property graph |

## B6.4 Hypothesis edges

Anything discovered (methods 2–6) is stored as a **hypothesis edge**, never as a fact.

| Property | Values | Example |
|---|---|---|
| `status` | proposed → validated / rejected | proposed |
| `confidence` | 0–1 | 0.8 |
| `inferred_by` | Rule or model ID | R-07 (triplestore) |
| `run_id` | When it was produced | 2026-09-30T02:00 |
| `evidence` | Event and fact IDs | FL-002, IOW-002 |
| `reviewed_by` / `reviewed_on` | Accountable SME | Corrosion Engineer, date |

**Lifecycle**

```
proposed ──(SME review)──▶ validated ──▶ used by insights, visible to AI as "validated hypothesis"
    │
    └──────────────────────▶ rejected ──▶ kept for audit; the rule's precision is tracked
```

## B6.5 Rules

| # | Rule |
|---|---|
| Hy1 | A hypothesis never changes a fact. It can only add a separate edge. |
| Hy2 | AI answers must label hypotheses ("proposed, confidence 0.8") and never state them as fact. |
| Hy3 | Each rule and model has an owner and a measured precision (validated ÷ reviewed). Rules below the agreed precision are retired. |
| Hy4 | Inferred edges are recomputed, not edited: drop the inferred graph and rerun ([C4](C4-reasoning-and-validation.md)). |
| Hy5 | Validated hypotheses feed the problem-pattern library. |

## B6.6 Example: the titanium counter-case

Rule R-07 flags E-101A and E-101B (carbon steel) when HSOB runs at CDU-1. A what-if HSOB campaign at Beta flags nothing, because E-401A has **titanium** tubes. The same crude gets a different risk result because the equipment's DNA differs. That's why the rule joins crude chemistry, topology and metallurgy rather than crude alone.
