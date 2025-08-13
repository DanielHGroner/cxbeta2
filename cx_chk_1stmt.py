import ast
import sys
from collections import defaultdict
from cx_utils import read_source_file
from cx_errors import CxUnsupportedSyntaxError

def is_ignorable_stmt(node):
    """Ignore docstrings and `pass`."""
    if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant):
        return isinstance(node.value.value, str)  # Likely a docstring
    if isinstance(node, ast.Pass):
        return True
    return False

def cx_chk_1stmt(tree: ast.AST) -> list:
    """
    Checks for multiple non-ignorable statements on a single source line.
    Returns a list of CxUnsupportedSyntaxError.
    """
    errors = []
    line_to_stmts = defaultdict(list)

    def collect_body_statements(node):
        for field_name in ("body", "orelse", "finalbody"):
            if hasattr(node, field_name):
                for stmt in getattr(node, field_name):
                    if not is_ignorable_stmt(stmt):
                        line_to_stmts[stmt.lineno].append(stmt)
                    collect_body_statements(stmt)  # Recursive descent

    collect_body_statements(tree)

    for lineno, stmts in line_to_stmts.items():
        if len(stmts) > 1:
            errors.append(CxUnsupportedSyntaxError(
                errtype="MultiStatementLine",
                message="Multiple statements on a single line",
                line=lineno,
                col=0,
                severity="error"
            ))

    return errors

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cx_chk_1stmt.py <example.py>")
        sys.exit(1)

    path = sys.argv[1]
    source = read_source_file(path)

    try:
        tree = ast.parse(source, filename=path)
    except Exception as e:
        print(f"Could not parse AST for {path}: {e}")
        exit(1)

    errors = cx_chk_1stmt(tree)
    if errors:
        print(f"Found {len(errors)} multi-statement line(s):")
        for err in errors:
            print(f"- Line {err.line}: {err.message}")
        exit(1)
    else:
        print("No multi-statement lines found.")

