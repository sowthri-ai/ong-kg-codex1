"""Smoke test: start the MCP server over stdio as an AI client would, list tools, and call them."""
import asyncio, json, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent

async def main():
    params = StdioServerParameters(command=sys.executable, args=["-m", "ogkg.mcp_server"], cwd=str(ROOT))
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            init = await s.initialize()
            assert "Answer contract" in (init.instructions or ""), "answer contract missing"
            tools = [t.name for t in (await s.list_tools()).tools]
            print("tools:", tools)
            async def call(name, **kw):
                res = await s.call_tool(name, kw)
                assert not res.isError, res
                return json.loads(res.content[0].text) if len(res.content) == 1 else [json.loads(c.text) for c in res.content]
            e = await call("get_entity", entity_id="P-201A")
            print("P-201A path:", " > ".join(h["name"] for h in reversed(e["hierarchy"])))
            f = await call("get_facts", entity_id="CR-DOBA", predicate="tan")
            f = f if isinstance(f, dict) else f[0]
            print("Doba TAN:", f["value"], f["unit"], f["citation"])
            p = await call("find_path", from_id="CR-HSOB", to_id="DEC-CRBUY")
            print("path HSOB -> DEC-CRBUY:", " ".join(f"{x['from_id']} {x['rel']}" for x in p["path"]), p["path"][-1]["to_id"])
            i = await call("run_insight", insight_id="true-crude-value")
            print("insight:", i["headline"]); print("first citation:", i["evidence_citations"][0])
            x = await call("explain_fact", fact_id=next(fid for fid in i["evidence"]))
            print("lineage ok:", x["citation"])
            print("MCP SMOKE TEST PASSED")

asyncio.run(main())
