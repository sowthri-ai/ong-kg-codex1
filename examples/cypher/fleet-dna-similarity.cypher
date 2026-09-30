// Handbook B4.6 — pumps sharing a failed pump's DNA (model + seal plan + service band)
MATCH (p:Pump {id:$failedPump})
MATCH (q:Pump) WHERE q <> p
  AND q.model = p.model AND q.seal_plan = p.seal_plan
  AND (q.service_temperature >= 340) = (p.service_temperature >= 340)
OPTIONAL MATCH (f:Failure)-[:FAILURE_OF]->()-[:PART_OF*0..3]->(q)
RETURN q.id AS pump, count(f) AS failures_12m
ORDER BY failures_12m DESC;
