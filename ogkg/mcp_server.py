"""
AI access layer — MCP server.

Any MCP-capable AI (Claude, Copilot Studio, custom LangGraph / Semantic Kernel agents)
connects here to get GROUNDED, CITED facts about the O&G value chain.

Run (stdio):   python -m ogkg.mcp_server
Claude Desktop / Code config:
  {"mcpServers": {"og-kg": {"command": "python", "args": ["-m", "ogkg.mcp_server"], "cwd": "<repo>"}}}
"""
from mcp.server.fastmcp import FastMCP

from . import insights as ins
from .kg import KG
from .ontology import LEVELS, RELATIONS, STANDARDS

ANSWER_CONTRACT = """You are connected to the O&G Value Chain Knowledge Graph (the governed source of facts).
Answer contract:
1. Only state a number, date or attribute if a tool returned it. Never estimate a value the graph does not hold.
2. Cite every figure with its fact citation, e.g. [F-00012 | LIMS | as of 2026-09-28 | high | measured].
3. Surface confidence: flag 'indicative', 'assumption' or 'low' facts explicitly.
4. For derived figures, call explain_fact to show lineage when asked 'how was this calculated'.
5. If the graph lacks the fact, say so and name the likely system of record — do not fill the gap.
Navigation: L0 Oil & Gas → L1 segment → two spines. Asset spine (ISO 14224, L2 business category … L10 data point)
and process spine (L2 value stream … L8 decision point, L9 data object, L10 data element). Spines link through
ACTS_ON, GOVERNS, CONSUMES and INSTANTIATED_BY; materials and events link into both."""

mcp = FastMCP("og-value-chain-kg", instructions=ANSWER_CONTRACT)
kg = KG()


@mcp.tool()
def describe_model() -> dict:
    """Ontology overview: L0-L10 levels for both spines with node counts, relation types, and standards alignment."""
    return dict(levels=kg.level_summary(), relations=RELATIONS, standards=STANDARDS, dataset=kg.meta)


@mcp.tool()
def search_entities(text: str = "", cls: str | None = None, spine: str | None = None,
                    level: int | None = None, limit: int = 25) -> list:
    """Find entities by name/id text, class (e.g. EquipmentUnit, DecisionPoint, CrudeGrade), spine
    (trunk|asset|process|material|event|org) or level (0-10)."""
    return kg.search(text, cls, spine, level, limit)


@mcp.tool()
def get_entity(entity_id: str) -> dict:
    """Full entity card: node, its L0..Ln hierarchy path, all facts with citations, relations and children."""
    if entity_id not in kg.nodes:
        return dict(error=f"Unknown entity '{entity_id}'. Use search_entities first.")
    return kg.entity(entity_id)


@mcp.tool()
def get_facts(entity_id: str, predicate: str | None = None) -> list:
    """Cited facts for an entity, optionally filtered to one predicate (e.g. 'tan', 'grm_fy2026', 'actual_cost')."""
    return [dict(**f, citation=kg.cite(f)) for f in kg.facts(entity_id, predicate)]


@mcp.tool()
def get_hierarchy(entity_id: str, direction: str = "up", depth: int = 2) -> dict:
    """Navigate the L0-L10 hierarchy. direction='up' returns the path to L0; 'down' returns the subtree to `depth`."""
    if direction == "up":
        return dict(path=[dict(id=a, name=kg.nodes[a]["name"], level=kg.nodes[a]["level"]) for a in kg.ancestors(entity_id)])

    def sub(n, d):
        node = dict(id=n, name=kg.nodes[n]["name"], level=kg.nodes[n]["level"], cls=kg.nodes[n]["cls"])
        if d > 0:
            node["children"] = [sub(c, d - 1) for c in kg.children(n)]
        return node
    return sub(entity_id, depth)


@mcp.tool()
def traverse(entity_id: str, relation: str | None = None) -> list:
    """One-hop neighbours of an entity, optionally filtered by relation type (see describe_model)."""
    return kg.neighbours(entity_id, relation)


@mcp.tool()
def find_path(from_id: str, to_id: str, max_depth: int = 8) -> dict:
    """Shortest explainable path between two entities across spines, materials and events."""
    p = kg.find_path(from_id, to_id, max_depth)
    return dict(path=p) if p else dict(error="No path within depth")


@mcp.tool()
def rollup_events(entity_id: str, event_class: str = "Failure") -> dict:
    """Roll events up the hierarchy: all Failures (or IOWExceedance via ON_DATAPOINT) beneath an entity."""
    rel = "FAILURE_OF" if event_class == "Failure" else "ON_DATAPOINT"
    ev = kg.rollup(entity_id, event_class, rel)
    return dict(count=len(ev), events=[dict(id=e["id"], name=e["name"], date=e["props"].get("date")) for e in ev])


@mcp.tool()
def explain_fact(fact_id: str) -> dict:
    """Lineage of a fact: source system, owner, confidence and — for derived facts — the facts it was calculated from."""
    if fact_id not in kg.facts_by_id:
        return dict(error="Unknown fact id")
    return kg.explain_fact(fact_id)


@mcp.tool()
def list_insights() -> list:
    """Cross-domain discovery insights available (questions that siloed systems cannot answer)."""
    return [dict(id=r["id"], title=r["title"], question=r["question"]) for r in ins.run_all(kg)]


@mcp.tool()
def run_insight(insight_id: str) -> dict:
    """Run a discovery insight. Returns headline, rows, graph path, evidence fact ids, recommendation, owner and caveat."""
    r = ins.run(kg, insight_id)
    r["evidence_citations"] = [kg.cite(kg.facts_by_id[f]) for f in r["evidence"]]
    return r


if __name__ == "__main__":
    mcp.run()
