# Handbook C1.6 rule S3 — recompute inferences, never edit them
DROP SILENT GRAPH <urn:ogkg:inferred:2026-09-29> ;
INSERT { GRAPH <urn:ogkg:inferred:2026-09-30> { ?s ?p ?o } }
WHERE  { GRAPH <urn:ogkg:staging:rule-output> { ?s ?p ?o } }
