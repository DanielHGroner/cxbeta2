import ast
import sys
from cx_utils import (
    read_source_file,
    parse_ast,
    load_json_file,
    derive_output_filename,
    write_json_file,
)


def extract_function_and_class_defs(tree):
    """Return:
    - func_defs: { name: { line, type, class (opt) } }
    - class_defs: { class_name: { line, has_init: bool } }
    """
    func_defs = {}
    class_defs = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            parent = getattr(node, 'parent', None)
            if isinstance(parent, ast.ClassDef):
                qualified_name = f"{parent.name}.{node.name}"
                #print('*** DEBUG: qualified_name:', qualified_name)
                kind = "constructor" if node.name == "__init__" else "method"
                #func_defs[node.name] = {"line": node.lineno, "type": kind, "class": parent.name}
                func_defs[qualified_name] = {"line": node.lineno, "type": kind, "class": parent.name}
            else:
                func_defs[node.name] = {"line": node.lineno, "type": "function"}

        elif isinstance(node, ast.ClassDef):
            has_init = any(
                isinstance(child, ast.FunctionDef) and child.name == "__init__"
                for child in node.body
            )
            class_defs[node.name] = {"line": node.lineno, "has_init": has_init}

    return func_defs, class_defs


def extract_calls(tree):
    """Return a list of (call_line, call_name, call_type)"""
    calls = []

    class CallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            name, call_type = self.get_call_target(node.func)
            if name:
                calls.append((node.lineno, name, call_type))
            self.generic_visit(node)

        def get_call_target(self, node):
            if isinstance(node, ast.Name):
                return node.id, "function"
            elif isinstance(node, ast.Attribute):
                return node.attr, "method"
            return None, None

    CallVisitor().visit(tree)
    return calls


def map_calls_to_defs(calls, func_defs, class_defs, stmt_lines):
    flows = []
    for call_line, name, call_type in calls:
        stmt_from = stmt_lines.get(call_line)
        stmt_to = None
        actual_type = call_type
        target_name = None

        # Try to match function or method
        matched_name = None
        for func_name in func_defs:
            if func_name == name or func_name.endswith(f".{name}"):
                matched_name = func_name
                break

        if matched_name:
            stmt_to = func_defs[matched_name]["line"]
            actual_type = func_defs[matched_name]["type"]
            target_name = matched_name

        # Try constructor
        elif name in class_defs and class_defs[name]["has_init"]:
            for fn, fd in func_defs.items():
                if fd["type"] == "constructor" and fd.get("class") == name:
                    stmt_to = fd["line"]
                    actual_type = "constructor"
                    target_name = fn  # this would already be like ClassName.__init__
                    break

        #print('*** DEBUG: name =', name, '→ target =', target_name)

        if stmt_from and stmt_to:
            flows.append({
                "stmt_from": stmt_from,
                "stmt_to": stmt_to,
                "type": "call",
                "call_type": actual_type,
                "target_name": target_name  # ← NEW field
            })

    return flows


def extract_stmt_line_map(stmt_list):
    line_map = {}
    for stmt in stmt_list:
        start = stmt["start"]["line"]
        end = stmt.get("end", {}).get("line", start)
        for line in range(start, end + 1):
            line_map[line] = start
    return line_map


def annotate_ast_parents(tree):
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node


def cx_gen_flows_call(tree, stmt_list):
    annotate_ast_parents(tree)
    func_defs, class_defs = extract_function_and_class_defs(tree)
    calls = extract_calls(tree)
    stmt_line_map = extract_stmt_line_map(stmt_list)
    return map_calls_to_defs(calls, func_defs, class_defs, stmt_line_map)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_flow_calls.py <source_file>")
        sys.exit(1)

    source_filename = sys.argv[1]
    source_code = read_source_file(source_filename)
    stmt_filename = derive_output_filename(source_filename, "stmts")
    stmt_list = load_json_file(stmt_filename)

    tree = parse_ast(source_code)
    flows = cx_gen_flows_call(tree, stmt_list)

    output_filename = derive_output_filename(source_filename, "flows_call")
    write_json_file(flows, output_filename)
    print(f"Wrote {len(flows)} flow call(s) to {output_filename}")
