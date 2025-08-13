import sys
import ast
from cx_utils import read_source_file, parse_ast, derive_filename, write_json_file, get_node_start, get_node_end

def is_real_stmt(node):
    return isinstance(node, (
        ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Return,
        ast.Delete, ast.Assign, ast.AugAssign, ast.AnnAssign, ast.For,
        ast.AsyncFor, ast.While, ast.If, ast.With, ast.AsyncWith, ast.Raise,
        ast.Try, ast.Assert, ast.Import, ast.ImportFrom, ast.Global,
        ast.Nonlocal, ast.Expr, ast.Pass, ast.Break, ast.Continue
    ))

def cx_gen_stmts_real(tree):
    statements = []

    class RealStmtVisitor(ast.NodeVisitor):
        def visit(self, node):
            if is_real_stmt(node):
                start = get_node_start(node)
                end = get_node_end(node)
                stmt = {
                    "start": start,
                    "end": end,
                    "type": type(node).__name__,
                    "is_compound": hasattr(node, 'body'),
                    "is_synthetic": False
                }
                statements.append(stmt)
            self.generic_visit(node)

    RealStmtVisitor().visit(tree)
    return statements

    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cx_gen_stmts_real.py <sourcefile.py>")
        sys.exit(1)

    filename = sys.argv[1]
    source = read_source_file(filename)
    tree = parse_ast(source, filename)
    stmts = cx_gen_stmts_real(tree)
    output_filename = derive_filename(filename, "stmts", "real")
    write_json_file(stmts, output_filename)
    print(f"Wrote {len(stmts)} statements to {output_filename}")
