#!/usr/bin/env python3
# cx_gen_scopes.py — emit minimal, line-oriented scope info for collapse/expand.
#
# Usage:
#   python cx_gen_scopes.py path/to/example.py [path/to/example.stmts.json]
#
# Output:
#   path/to/example.scopes.json
#
# JSON shape:
# {
#   "scopes": {
#     "10": {
#       "id": "fun:total:10",
#       "kind": "function",           # "function" | "method" | "class"
#       "qname": "total",
#       "parent_id": "mod:<global>:1",
#       "header_start_line": 8,       # earliest decorator or def line
#       "header_end_line": 12,        # colon line of the signature (from stmts.json or tokenizer)
#       "docstring_span": [13, 15],   # or null if no docstring
#       "last_stmt_line": 35          # last top-level stmt in the body
#     },
#     ...
#   }
# }

from __future__ import annotations

import ast
import io
import json
import os
import re
import sys
import tokenize
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

MOD_ID = "mod:<global>:1"

# ---------------- Helpers ----------------

def _docstring_span(body: List[ast.stmt]) -> Tuple[Optional[int], Optional[int]]:
    """
    Return (start_line, end_line) for a docstring if the first body statement is a string literal.
    Otherwise (None, None). Uses ast.Constant(str) (Py3.8+).
    """
    if not body:
        return None, None
    first = body[0]
    if isinstance(first, ast.Expr):
        val = getattr(first, "value", None)
        if isinstance(val, ast.Constant) and isinstance(val.value, str):
            start = getattr(first, "lineno", None)
            if start is None:
                return None, None
            end = getattr(first, "end_lineno", start)
            return int(start), int(end if end is not None else start)
    return None, None

def compute_header_end_with_tokenize(source: str, def_line: int) -> int:
    """
    Fallback: find the physical line that contains the ':' ending a def/class header.
    Scans forward from def_line, tracking (), [], {} depth; returns def_line on failure.
    """
    lines = source.splitlines()
    text = "\n".join(lines[def_line - 1 :])
    depth = 0
    try:
        for tok_type, tok_str, (sline, _), _, _ in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok_type == tokenize.OP:
                if tok_str in "([{":
                    depth += 1
                elif tok_str in ")]}":
                    depth -= 1
                elif tok_str == ":" and depth == 0:
                    return def_line + sline - 1
    except tokenize.TokenError:
        pass
    return def_line

def _norm_type(t: str) -> str:
    """Normalize CamelCase types (e.g., 'FunctionDef') to snake ('function_def')."""
    t = str(t or "").strip()
    tl = t.lower()
    if "_" in tl:
        return tl
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", t).lower()

def load_header_end_map_from_stmts_list(stmts_list: List[dict]) -> Dict[int, int]:
    """
    Your stmts.json is a list of objects like:
      { "type": "FunctionDef", "start": {"line":8,"col":0}, "end_header": {"line":8,"col":17}, ... }
    Return a map: def_line -> header_end_line
    """
    out: Dict[int, int] = {}
    for st in stmts_list:
        t = _norm_type(st.get("type"))
        if t not in {"function_def", "async_function_def", "class_def"}:
            continue
        start = st.get("start") or {}
        dl = start.get("line")
        if dl is None:
            continue
        eh = (st.get("end_header") or {}).get("line")
        if eh is None:
            # no explicit header end; leave missing so tokenizer can compute
            continue
        out[int(dl)] = int(eh)
    return out

# ---------------- AST traversal ----------------

@dataclass
class Owner:
    id: str
    kind: str                 # "function" | "method" | "class"
    qname: str
    def_line: int
    last_stmt_line: int
    parent_id: str
    header_start_line: int    # earliest decorator or def line
    docstring_span: Optional[Tuple[int, int]]  # (start, end) or None

class OwnerBuilder(ast.NodeVisitor):
    def __init__(self): #, source: str):
        #self.source = source
        self.owners: List[Owner] = []
        self._node_stack: List[ast.AST] = []
        self._qname_stack: List[str] = []
        self._scope_id_stack: List[str] = [MOD_ID]  # default parent at module level

    @staticmethod
    def _abbr(kind: str) -> str:
        return {"function": "fun", "method": "mth", "class": "cls"}[kind]

    def _make_id(self, kind: str, qname: str, def_line: int) -> str:
        return f"{self._abbr(kind)}:{qname}:{def_line}"

    def _qual(self, name: str) -> str:
        return f"{self._qname_stack[-1]}.{name}" if self._qname_stack else name

    @staticmethod
    def _first_last_stmt_lines(body: List[ast.stmt], fallback_def: int) -> Tuple[Optional[int], int]:
        if not body:
            return None, fallback_def
        first_ln = int(getattr(body[0], "lineno", fallback_def))
        # Use the physical END of the last top-level stmt (handles if/for/try/with/match, etc.)
        last_end_ln = max(
            int(getattr(s, "end_lineno", getattr(s, "lineno", fallback_def)))
            for s in body
        )
        return first_ln, last_end_ln

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._handle_owner(node, kind="class", name=node.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_owner(node, kind="function", name=node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_owner(node, kind="function", name=node.name)

    def _handle_owner(self, node: ast.AST, kind: str, name: str) -> None:
        parent_is_class = bool(self._node_stack and isinstance(self._node_stack[-1], ast.ClassDef))
        real_kind = "method" if (kind == "function" and parent_is_class) else kind

        def_line = int(getattr(node, "lineno", 1))
        body: List[ast.stmt] = list(getattr(node, "body", []))
        _first, last = self._first_last_stmt_lines(body, def_line)
        doc_start, doc_end = _docstring_span(body)

        # decorators → header_start_line (single-line start is fine even for multi-line decorator expressions)
        deco_list = getattr(node, "decorator_list", []) if hasattr(node, "decorator_list") else []
        deco_starts = [int(getattr(d, "lineno", def_line)) for d in deco_list if hasattr(d, "lineno")]
        header_start = min([def_line] + deco_starts) if deco_starts else def_line

        qn = self._qual(name)
        oid = self._make_id(real_kind, qn, def_line)
        parent_id = (self._scope_id_stack[-1] if self._scope_id_stack else MOD_ID) or MOD_ID

        self.owners.append(Owner(
            id=oid,
            kind=real_kind,
            qname=qn,
            def_line=def_line,
            last_stmt_line=int(last),
            parent_id=parent_id,
            header_start_line=int(header_start),
            docstring_span=(int(doc_start), int(doc_end)) if doc_start is not None else None
        ))

        # descend for nested owners
        self._node_stack.append(node)
        self._qname_stack.append(qn)
        self._scope_id_stack.append(oid)
        self.generic_visit(node)
        self._scope_id_stack.pop()
        self._qname_stack.pop()
        self._node_stack.pop()

# ---------------- Orchestration ----------------

def cx_gen_scopes(tree: ast.AST, stmts_list: Optional[List[dict]]) -> Dict[str, dict]:
    ob = OwnerBuilder() #py_source)
    ob.visit(tree)

    header_end_map = load_header_end_map_from_stmts_list(stmts_list or [])
    scopes: Dict[str, dict] = {}

    for o in ob.owners:
        he = header_end_map.get(o.def_line)
        #if he is None:
        #    he = compute_header_end_with_tokenize(py_source, o.def_line)

        scopes[str(o.def_line)] = {
            "id": o.id,
            "kind": o.kind,
            "qname": o.qname,
            "parent_id": o.parent_id or MOD_ID,
            "header_start_line": int(o.header_start_line),
            "header_end_line": int(he),
            "docstring_span": [int(o.docstring_span[0]), int(o.docstring_span[1])] if o.docstring_span else None,
            "last_stmt_line": int(o.last_stmt_line),
        }

    return scopes

def main_gen_scopes(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: python cx_gen_scopes.py path/to/example.py [path/to/example.stmts.json]", file=sys.stderr)
        return 2

    py_path = argv[1]
    try:
        with open(py_path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"Error reading {py_path}: {e}", file=sys.stderr)
        return 1

    base = os.path.splitext(os.path.basename(py_path))[0]
    # Optional stmts path (your format is a LIST of objects)
    if len(argv) >= 3:
        stmts_path = argv[2]
    else:
        cand = [
            os.path.join(os.path.dirname(py_path), f"{base}.stmts.json"),
            os.path.join(os.path.dirname(py_path), f"{base}_stmts.json"),
        ]
        stmts_path = next((p for p in cand if os.path.exists(p)), "")

    stmts_list: Optional[List[dict]] = None
    if stmts_path:
        try:
            with open(stmts_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    stmts_list = data
                else:
                    # Be forgiving if someone wrapped it as {"statements":[...]}
                    stmts_list = data.get("statements") or data.get("stmts") or []
        except OSError as e:
            print(f"Warning: could not read stmts.json ({stmts_path}): {e}", file=sys.stderr)

    # gen tree here, and pass to top level API
    tree = ast.parse(source, type_comments=True)
    scopes = cx_gen_scopes(tree, stmts_list)

    out_path = os.path.join(os.path.dirname(py_path), f"{base}.scopes.json")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            #json.dump({"scopes": scopes}, f, indent=2)
            json.dump(scopes, f, indent=2)
    except OSError as e:
        print(f"Error writing {out_path}: {e}", file=sys.stderr)
        return 1

    n = len(scopes)
    print(f"Wrote {n} scope{'s' if n != 1 else ''} to {out_path}")
    
    # sanity warning if any range is inverted
    bad = [d for d, v in scopes.items() if int(v["header_end_line"]) > int(v["last_stmt_line"])]
    if bad:
        print(f"Warning: {len(bad)} scope(s) have header_end_line > last_stmt_line (defs: {bad[:5]})", file=sys.stderr)

    return 0

if __name__ == "__main__":
    sys.exit(main_gen_scopes(sys.argv))
