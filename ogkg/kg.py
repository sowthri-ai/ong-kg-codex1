"""Knowledge-graph engine: indexing, hierarchy navigation, traversal and cited fact retrieval."""
import json
from collections import defaultdict, deque
from pathlib import Path

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "kg.json"


class KG:
    def __init__(self, path=DEFAULT_DATA):
        data = json.loads(Path(path).read_text())
        self.meta = data["meta"]
        self.nodes = {n["id"]: n for n in data["nodes"]}
        self.edges = data["edges"]
        self.fact_list = data["facts"]
        self.facts_by_id = {f["id"]: f for f in self.fact_list}
        self.out, self.inc = defaultdict(list), defaultdict(list)
        for e in self.edges:
            self.out[e["source"]].append(e)
            self.inc[e["target"]].append(e)
        self.facts_by_subject = defaultdict(list)
        for f in self.fact_list:
            self.facts_by_subject[f["subject"]].append(f)

    # ------------------------------------------------------------ facts
    @staticmethod
    def cite(f):
        return f"[{f['id']} | {f['source_system']} | as of {f['as_of']} | {f['confidence']} | {f['method']}]"

    def facts(self, subject, predicate=None):
        return [f for f in self.facts_by_subject.get(subject, []) if predicate in (None, f["predicate"])]

    def fact(self, subject, predicate, as_of=None):
        """Current fact: status 'current', valid at `as_of` (default: latest valid_from). Data contract v0.5 time semantics."""
        fs = [f for f in self.facts(subject, predicate) if f.get("status", "current") == "current"]
        if as_of:
            fs = [f for f in fs if f.get("valid_from", f["as_of"]) <= as_of and (not f.get("valid_to") or f["valid_to"] > as_of)]
        return max(fs, key=lambda f: f.get("valid_from", f["as_of"])) if fs else None

    def value(self, subject, predicate, default=None, as_of=None):
        f = self.fact(subject, predicate, as_of)
        return f["value"] if f else default

    def history(self, subject, predicate):
        """All facts for (subject, predicate), oldest first, including superseded ones."""
        return sorted(self.facts(subject, predicate), key=lambda f: (f.get("valid_from", f["as_of"]), f.get("recorded_at", "")))

    def explain_fact(self, fid, _depth=0):
        f = self.facts_by_id[fid]
        return dict(fact=f, citation=self.cite(f), subject_name=self.nodes[f["subject"]]["name"],
                    derived_from=[self.explain_fact(x, _depth + 1) for x in f["lineage"]] if _depth < 5 else [])

    # ------------------------------------------------------------ graph navigation
    def targets(self, nid, rel):
        return [e["target"] for e in self.out.get(nid, []) if e["rel"] == rel]

    def sources(self, nid, rel):
        return [e["source"] for e in self.inc.get(nid, []) if e["rel"] == rel]

    def parent(self, nid):
        p = self.targets(nid, "PART_OF")
        return p[0] if p else None

    def ancestors(self, nid):
        """Path from the node up to L0 (node first)."""
        path, cur = [nid], self.parent(nid)
        while cur:
            path.append(cur)
            cur = self.parent(cur)
        return path

    def children(self, nid):
        return self.sources(nid, "PART_OF")

    def descendants(self, nid, include_self=True):
        out, q = ([nid] if include_self else []), deque([nid])
        while q:
            for c in self.children(q.popleft()):
                out.append(c)
                q.append(c)
        return out

    def is_under(self, nid, ancestor):
        return ancestor in self.ancestors(nid)

    def neighbours(self, nid, rel=None):
        res = []
        for e in self.out.get(nid, []):
            if rel in (None, e["rel"]):
                res.append(dict(direction="out", rel=e["rel"], id=e["target"], name=self.nodes[e["target"]]["name"]))
        for e in self.inc.get(nid, []):
            if rel in (None, e["rel"]):
                res.append(dict(direction="in", rel=e["rel"], id=e["source"], name=self.nodes[e["source"]]["name"]))
        return res

    def find_path(self, a, b, max_depth=8, avoid=("OG",)):
        """Shortest undirected path; avoids routing through the root so paths stay meaningful."""
        prev, q = {a: None}, deque([(a, 0)])
        while q:
            cur, d = q.popleft()
            if cur == b:
                break
            if d >= max_depth:
                continue
            for e in self.out.get(cur, []) + self.inc.get(cur, []):
                nxt = e["target"] if e["source"] == cur else e["source"]
                if nxt in prev or (nxt in avoid and nxt != b):
                    continue
                arrow = f"-{e['rel']}->" if e["source"] == cur else f"<-{e['rel']}-"
                prev[nxt] = (cur, arrow)
                q.append((nxt, d + 1))
        if b not in prev:
            return None
        steps, cur = [], b
        while prev[cur]:
            p, arrow = prev[cur]
            steps.append((p, arrow, cur))
            cur = p
        steps.reverse()
        return [dict(from_id=s, rel=r, to_id=t, from_name=self.nodes[s]["name"], to_name=self.nodes[t]["name"])
                for s, r, t in steps]

    # ------------------------------------------------------------ lookup
    def search(self, text="", cls=None, spine=None, level=None, limit=25):
        t = text.lower()
        res = []
        for n in self.nodes.values():
            if cls and n["cls"] != cls:
                continue
            if spine and n["spine"] != spine:
                continue
            if level is not None and n["level"] != level:
                continue
            if t and t not in n["name"].lower() and t not in n["id"].lower() and t not in n.get("desc", "").lower():
                continue
            res.append(dict(id=n["id"], name=n["name"], cls=n["cls"], spine=n["spine"], level=n["level"]))
            if len(res) >= limit:
                break
        return res

    def entity(self, nid):
        n = self.nodes[nid]
        return dict(
            node=n,
            hierarchy=[dict(id=a, name=self.nodes[a]["name"], level=self.nodes[a]["level"]) for a in self.ancestors(nid)],
            facts=[dict(**f, citation=self.cite(f)) for f in self.facts(nid)],
            relations=[r for r in self.neighbours(nid) if r["rel"] != "PART_OF"],
            children=[dict(id=c, name=self.nodes[c]["name"], level=self.nodes[c]["level"]) for c in self.children(nid)],
        )

    def level_summary(self):
        from .ontology import LEVELS
        counts = defaultdict(int)
        for n in self.nodes.values():
            counts[(n["spine"], n["level"])] += 1
        out = {}
        for spine in ("asset", "process"):
            out[spine] = []
            for lvl, (cls, desc, std) in LEVELS[spine].items():
                c = counts[("trunk", lvl)] if lvl <= 1 else counts[(spine, lvl)]
                out[spine].append(dict(level=f"L{lvl}", cls=cls, description=desc, standard=std, count=c))
        out["context"] = {s: sum(v for (sp, _), v in counts.items() if sp == s) for s in ("material", "event", "org")}
        return out

    def rollup(self, nid, cls="Failure", rel="FAILURE_OF"):
        """Count events of a class attached anywhere beneath a node — hierarchy roll-up."""
        under = set(self.descendants(nid))
        return [e for e in self.nodes.values() if e["cls"] == cls and any(t in under for t in self.targets(e["id"], rel))]
