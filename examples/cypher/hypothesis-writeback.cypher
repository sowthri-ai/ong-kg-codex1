// Handbook B6.4 — write a rule result (R-07) back as a governed hypothesis edge
// $rows = [{eq:'E-101A', evidence:['FL-001','IOW-001']}, {eq:'E-101B', evidence:['FL-002','IOW-002']}]
UNWIND $rows AS r
MATCH (e:Entity {id:r.eq}), (p:ProblemPattern {id:'OverheadChlorideCorrosion'})
MERGE (e)-[h:AT_RISK_OF]->(p)
  ON CREATE SET h.status = 'proposed'
SET h.confidence = 0.8, h.inferredBy = 'R-07', h.runId = $runId, h.evidence = r.evidence;

// SME review (validated or rejected), always with reviewer and date
// MATCH (:Entity {id:'E-101B'})-[h:AT_RISK_OF]->(:ProblemPattern {id:'OverheadChlorideCorrosion'})
// SET h.status = 'validated', h.reviewedBy = 'Corrosion Engineer', h.reviewedOn = date();
