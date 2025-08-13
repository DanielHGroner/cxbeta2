import sys
import ast
from collections import defaultdict
from cx_utils import (
    read_source_file,
    load_json_file,
    write_json_file,
    derive_filename,
    parse_ast
)

def build_stmt_line_map(statements):
    line_to_stmt = {}
    for stmt in statements:
        start = stmt['start']['line']
        if stmt.get('is_compound'):
            end = stmt['end_header']['line']
        else:
            end = stmt['end']['line']
        for line in range(start, end + 1):
            line_to_stmt[line] = start  # using start.line as stmt ID
    return line_to_stmt

def build_io_lookup(tokens):
    io_positions = {}
    for tok in tokens:
        if tok.get('type') == 'NAME' and tok.get('type_name') == 'function_call':
            key = (tok['start']['line'], tok['start']['col'])
            io_positions[key] = tok['text']
    return io_positions

class IOActionExtractor(ast.NodeVisitor):
    def __init__(self, stmt_map, io_lookup):
        self.stmt_map = stmt_map
        self.io_lookup = io_lookup
        self.scope_stack = ['global']
        self.results = defaultdict(list)
        self.count = 0

    def current_scope(self):
        if len(self.scope_stack) == 1:
            return "<global>"
        return ".".join(self.scope_stack[1:])
    
    def visit_FunctionDef(self, node):
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_ClassDef(self, node):
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Call(self, node):
        stmt = self.stmt_map.get(node.lineno)
        if stmt is None:
            return

        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            key = (node.func.lineno, node.func.col_offset)
            if key not in self.io_lookup or self.io_lookup[key] != func_name:
                return  # not an I/O call, or unconfirmed

        if func_name == 'print':
            self.results[self.current_scope()].append({
                "item": "-display",
                "stmt": stmt,
                "action": "output",
                "channel": "stdout"
            })
            self.count += 1
        elif func_name == 'input':
            self.results[self.current_scope()].append({
                "item": "-display",
                "stmt": stmt,
                "action": "output",
                "channel": "stdout"
            })
            self.results[self.current_scope()].append({
                "item": "-keyboard",
                "stmt": stmt,
                "action": "input",
                "channel": "stdin"
            })
            self.count += 2

        self.generic_visit(node)

def cx_gen_actions_io(tree, tokens, stmts):
    stmt_map = build_stmt_line_map(stmts)
    io_lookup = build_io_lookup(tokens)
    extractor = IOActionExtractor(stmt_map, io_lookup)
    extractor.visit(tree)

    return extractor.results

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_actions_io.py <example.py>")
        sys.exit(1)

    filename = sys.argv[1]
    source_code = read_source_file(filename)
    tokens = load_json_file(derive_filename(filename, 'tokens'))
    stmts = load_json_file(derive_filename(filename, 'stmts'))

    tree = parse_ast(source_code) # get ast tree from source
    
    io_actions = cx_gen_actions_io(tree, tokens, stmts) # generate io actions

    output_path = derive_filename(filename, 'actions_io')
    write_json_file(io_actions, output_path)

    count = sum(len(v) for v in io_actions.values())
    print(f"Wrote {count} actions_io to {output_path}")
