// Handbook A2.3 insight 1 — opportunity campaigns and the corrosion failures that followed
// on the unit they were processed in or one hop downstream, within 30 days of the window end.
MATCH (c:CrudeCampaign {opportunity:true})-[:PROCESSED_IN]->(u0:PlantUnit)
OPTIONAL MATCH (u0)-[:PRODUCES]->(:Stream)-[:FEEDS]->(u1:PlantUnit)
WITH c, [u0] + collect(DISTINCT u1) AS units
UNWIND units AS u
MATCH (f:Failure)-[:FAILURE_OF]->(x)-[:PART_OF*0..6]->(u)
WHERE date(f.date) >= date(c.start)
  AND date(f.date) <= date(c.end) + duration('P30D')
  AND f.failure_mechanism CONTAINS 'Corrosion'
OPTIONAL MATCH (wo:WorkOrder)-[:REMEDIATES]->(f)
RETURN c.id AS campaign, u.id AS unit, f.id AS failure,
       coalesce(wo.actual_cost, 0) AS repair_usd, coalesce(f.lost_margin, 0) AS lost_margin_usd
ORDER BY campaign, failure;
