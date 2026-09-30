"""
Minimal Turtle parser used for CI syntax checks and catalogue generation when rdflib
is not available. It covers the Turtle subset used in this repository:
@prefix / PREFIX, IRIs, prefixed names, 'a', literals (short and long strings,
language tags, datatypes), numbers, booleans, blank-node property lists [ ... ],
collections ( ... ), and the ; , . separators.

It is a checker, not a full RDF library. Phase 1 replaces it with rdflib + pySHACL
(backlog E1-P1-01).
"""
import re

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
XSD = "http://www.w3.org/2001/XMLSchema#"


class TurtleError(ValueError):
    pass


_TOKEN = re.compile(r'''
    (?P<ws>\s+|\#[^\n]*)
  | (?P<long>"""(?:[^"\\]|\\.|"(?!""))*""")
  | (?P<str>"(?:[^"\\\n]|\\.)*")
  | (?P<iri><[^<>"{}|^`\\\s]*>)
  | (?P<dtype>\^\^)
  | (?P<lang>@[a-zA-Z]+(?:-[a-zA-Z0-9]+)*)
  | (?P<num>[+-]?(?:\d+\.\d+|\.\d+|\d+)(?:[eE][+-]?\d+)?(?![\w:]))
  | (?P<pname>(?:[A-Za-z][\w\-.]*)?:(?:[\w\-]+(?:[\w\-.]*[\w\-])?)?)
  | (?P<kw>[A-Za-z_][\w]*)
  | (?P<punct>[;,.\[\]()])
''', re.X)


def tokenize(text):
    pos, out = 0, []
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            line = text.count("\n", 0, pos) + 1
            raise TurtleError(f"line {line}: cannot tokenise near {text[pos:pos+40]!r}")
        kind = m.lastgroup
        if kind != "ws":
            out.append((kind, m.group(), text.count("\n", 0, pos) + 1))
        pos = m.end()
    return out


class Parser:
    def __init__(self, text):
        self.toks = tokenize(text)
        self.i = 0
        self.prefixes = {}
        self.triples = []
        self._bn = 0

    # -- helpers
    def peek(self, k=0):
        return self.toks[self.i + k] if self.i + k < len(self.toks) else (None, None, -1)

    def take(self, value=None):
        tok = self.peek()
        if tok[0] is None:
            raise TurtleError("unexpected end of file")
        if value is not None and tok[1] != value:
            raise TurtleError(f"line {tok[2]}: expected {value!r}, found {tok[1]!r}")
        self.i += 1
        return tok

    def bnode(self):
        self._bn += 1
        return f"_:b{self._bn}"

    def expand(self, tok):
        kind, val, line = tok
        if kind == "iri":
            return val[1:-1]
        if kind == "pname":
            pfx, local = val.split(":", 1)
            if pfx not in self.prefixes:
                raise TurtleError(f"line {line}: undeclared prefix {pfx!r}")
            return self.prefixes[pfx] + local
        raise TurtleError(f"line {line}: expected IRI, found {val!r}")

    # -- grammar
    def parse(self):
        while self.peek()[0] is not None:
            kind, val, line = self.peek()
            if val in ("@prefix", "PREFIX") or (kind == "lang" and val == "@prefix"):
                self.take()
                name = self.take()[1]
                if not name.endswith(":"):
                    raise TurtleError(f"line {line}: bad prefix name {name!r}")
                self.prefixes[name[:-1]] = self.take()[1][1:-1]
                if val == "@prefix":
                    self.take(".")
                continue
            subj = self.subject()
            self.predicate_object_list(subj)
            self.take(".")
        return self

    def subject(self):
        kind, val, line = self.peek()
        if val == "[":
            return self.blank_node_list()
        if val == "(":
            return self.collection()
        return self.expand(self.take())

    def predicate_object_list(self, subj):
        while True:
            kind, val, line = self.peek()
            if val == "a":
                self.take()
                pred = RDF + "type"
            else:
                pred = self.expand(self.take())
            self.object_list(subj, pred)
            if self.peek()[1] == ";":
                while self.peek()[1] == ";":
                    self.take()
                if self.peek()[1] in (".", "]", None):
                    return
                continue
            return

    def object_list(self, subj, pred):
        while True:
            self.triples.append((subj, pred, self.obj()))
            if self.peek()[1] == ",":
                self.take()
                continue
            return

    def obj(self):
        kind, val, line = self.peek()
        if kind in ("iri", "pname"):
            return self.expand(self.take())
        if val == "[":
            return self.blank_node_list()
        if val == "(":
            return self.collection()
        if kind in ("str", "long"):
            self.take()
            text = val[3:-3] if kind == "long" else val[1:-1]
            nxt = self.peek()
            if nxt[0] == "lang":
                self.take()
                return ("literal", text, "lang:" + nxt[1][1:])
            if nxt[0] == "dtype":
                self.take()
                return ("literal", text, self.expand(self.take()))
            return ("literal", text, XSD + "string")
        if kind == "num":
            self.take()
            dt = "decimal" if ("." in val or "e" in val.lower()) else "integer"
            return ("literal", val, XSD + dt)
        if kind == "kw" and val in ("true", "false"):
            self.take()
            return ("literal", val, XSD + "boolean")
        raise TurtleError(f"line {line}: unexpected object {val!r}")

    def blank_node_list(self):
        self.take("[")
        node = self.bnode()
        if self.peek()[1] != "]":
            self.predicate_object_list(node)
        self.take("]")
        return node

    def collection(self):
        self.take("(")
        head = prev = None
        while self.peek()[1] != ")":
            cell = self.bnode()
            self.triples.append((cell, RDF + "first", self.obj()))
            if prev:
                self.triples.append((prev, RDF + "rest", cell))
            head = head or cell
            prev = cell
        self.take(")")
        if prev:
            self.triples.append((prev, RDF + "rest", RDF + "nil"))
        return head or RDF + "nil"


def parse(text):
    return Parser(text).parse()


def parse_file(path):
    with open(path, encoding="utf-8") as fh:
        return parse(fh.read())
