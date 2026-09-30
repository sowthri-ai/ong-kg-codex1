// Handbook C2.4 — starter schema (the Phase 1 compiler generates this from ogkg-core.ttl)
CREATE CONSTRAINT entity_iri IF NOT EXISTS FOR (n:Entity) REQUIRE n.iri IS UNIQUE;
CREATE CONSTRAINT entity_id  IF NOT EXISTS FOR (n:Entity) REQUIRE n.id  IS UNIQUE;
CREATE CONSTRAINT fact_id    IF NOT EXISTS FOR (f:Fact)   REQUIRE f.id  IS UNIQUE;
CREATE CONSTRAINT class_iri  IF NOT EXISTS FOR (c:Class)  REQUIRE c.iri IS UNIQUE;
CREATE CONSTRAINT concept_iri IF NOT EXISTS FOR (c:Concept) REQUIRE c.iri IS UNIQUE;
CREATE INDEX entity_level IF NOT EXISTS FOR (n:Entity) ON (n.level);
CREATE INDEX fact_predicate IF NOT EXISTS FOR (f:Fact) ON (f.predicateKey, f.asOf);
CREATE FULLTEXT INDEX entity_names IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.id];
