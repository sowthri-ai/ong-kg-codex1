// Option A (bulk): neo4j-admin database import full --nodes=nodes.csv --relationships=edges.csv og-kg
// Option B (LOAD CSV, files in the import dir):
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS r
CALL apoc.create.node(split(r[':LABEL'], ';'), {id: r['id:ID'], name: r.name, spine: r.spine,
     level: toIntegerOrNull(r['level:int']), props: r.props_json}) YIELD node RETURN count(node);
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS r
MATCH (a {id: r[':START_ID']}), (b {id: r[':END_ID']})
CALL apoc.create.relationship(a, r[':TYPE'], {}, b) YIELD rel RETURN count(rel);

// Example: L0 -> L10 path for a sensor tag
// MATCH p=(t {id:'T-CDU1-CL'})-[:PART_OF*]->(root {id:'OG'}) RETURN p;
// Example: decisions governing assets with failures but consuming no reliability/integrity data
// MATCH (d:DecisionPoint)-[:GOVERNS]->(a)<-[:PART_OF*0..6]-(x)<-[:FAILURE_OF]-(f:Failure)
// WHERE NOT EXISTS { MATCH (d)-[:CONSUMES]->(de) WHERE de.props CONTAINS '"domain": "reliability"'
//                    OR de.props CONTAINS '"domain": "integrity"' }
// RETURN d.name, count(DISTINCT f);
