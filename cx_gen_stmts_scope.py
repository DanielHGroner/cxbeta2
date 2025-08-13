import ast
import sys
import json
from cx_utils import read_source_file, derive_filename, parse_ast

class ScopeCollector(ast.NodeVisitor):
    def __init__(self):
        self.scopes = {
            "<global>": {
                "type": None,
                "statement_ids": []
            }
        }
        self.current_class = None
        self.current_function = None

    def _add_stmt_to_scope(self, lineno):
        scope = self._current_scope_name()
        if lineno is not None:
            self.scopes[scope]["statement_ids"].append(lineno)

    def _current_scope_name(self):
        if self.current_function:
            return f"{self.current_class}.{self.current_function}" if self.current_class else self.current_function
        return "<global>"

    def visit_ClassDef(self, node):
        self._add_stmt_to_scope(getattr(node, 'lineno', None))
        class_name = node.name
        self.scopes[class_name] = {
            "type": "class",
            "statement_ids": []
        }
        prev_class = self.current_class
        self.current_class = class_name
        for stmt in node.body:
            self.visit(stmt)
        self.current_class = prev_class

    def visit_FunctionDef(self, node):
        self._add_stmt_to_scope(getattr(node, 'lineno', None))
        func_name = node.name
        scope_name = f"{self.current_class}.{func_name}" if self.current_class else func_name
        self.scopes[scope_name] = {
            "type": "method" if self.current_class else "function",
            "statement_ids": []
        }
        prev_function = self.current_function
        self.current_function = func_name
        for stmt in node.body:
            self.visit(stmt)
        self.current_function = prev_function

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def generic_visit(self, node):
        if isinstance(node, ast.stmt):
            self._add_stmt_to_scope(getattr(node, 'lineno', None))
        super().generic_visit(node)

def cx_gen_stmts_scope(source_code):
    tree = parse_ast(source_code)
    collector = ScopeCollector()
    collector.visit(tree)
    return collector.scopes

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_stmts_scope.py <sourcefile.py>")
        sys.exit(1)

    filename = sys.argv[1]
    source = read_source_file(filename)
    scope_map = cx_gen_stmts_scope(source)

    outname = derive_filename(filename, "stmts_scope")
    with open(outname, "w") as f:
        json.dump(scope_map, f, indent=2)

    print(f"Wrote {len(scope_map)} scopes to {outname}")
