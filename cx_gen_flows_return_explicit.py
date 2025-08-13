import ast
import sys
import json
from cx_utils import read_source_file, derive_filename, parse_ast


def cx_gen_flows_return_explicit(tree):
    results = []

    class ReturnRaiseVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_class = None
            self.current_function = None

        def visit_ClassDef(self, node):
            prev_class = self.current_class
            self.current_class = node.name
            self.generic_visit(node)
            self.current_class = prev_class

        def visit_FunctionDef(self, node):
            prev_function = self.current_function
            self.current_function = node.name

            if self.current_class:
                call_type = "method" if node.name != "__init__" else "constructor"
                function_name = f"{self.current_class}.{node.name}"
            else:
                call_type = "function"
                function_name = node.name

            for child in ast.walk(node):
                if isinstance(child, (ast.Return, ast.Raise)):
                    results.append({
                        "stmt_from": child.lineno,
                        "return_type": "explicit_return",
                        "is_raise": isinstance(child, ast.Raise),
                        "scope": function_name,
                        "scope_type": call_type
                    })

            self.generic_visit(node)
            self.current_function = prev_function

        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)

    ReturnRaiseVisitor().visit(tree)
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cx_gen_explicit_returns.py <sourcefile.py>")
        sys.exit(1)

    source_filename = sys.argv[1]
    source_code = read_source_file(source_filename)

    tree = parse_ast(source_code, source_filename)
    explicit_returns = cx_gen_flows_return_explicit(tree)

    output_filename = derive_filename(source_filename, "flows_return_explicit")
    with open(output_filename, "w") as f:
        json.dump(explicit_returns, f, indent=2)
    print(f"Wrote {len(explicit_returns)} items to {output_filename}")
