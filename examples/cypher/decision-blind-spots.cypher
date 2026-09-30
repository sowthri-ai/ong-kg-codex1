// Handbook A2.3 insight 5 — decisions governing assets with corrosion failures
// that consume no reliability or integrity data
MATCH (d:DecisionPoint)-[:GOVERNS]->(a)<-[:PART_OF*0..6]-(x)<-[:FAILURE_OF]-(f:Failure)
WHERE f.failure_mechanism CONTAINS 'Corrosion'
  AND NOT EXISTS {
    MATCH (d)-[:CONSUMES]->(de:DataElement) WHERE de.domain IN ['reliability','integrity']
  }
RETURN d.id AS decision, d.name AS name, count(DISTINCT f) AS corrosion_failures;
