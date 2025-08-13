import sys
import ast
from collections import defaultdict
from cx_utils import load_json_file, write_json_file, read_source_file, derive_filename, parse_ast

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

def build_variable_lookup(tokens):
    var_positions = set()
    for tok in tokens:
        if tok.get('type_name') == 'variable':
            var_positions.add((tok['start']['line'], tok['start']['col'], tok['text']))
    return var_positions

class VarActionExtractor(ast.NodeVisitor):
    def __init__(self, stmt_map, var_positions):
        self.stmt_map = stmt_map
        self.var_positions = var_positions
        self.scope_stack = ['global']
        self.results = defaultdict(lambda: defaultdict(set))  # scope -> (var, stmt) -> set(actions)
        self.scope_vars = defaultdict(set)  # scope -> set of variable names
        self.global_declared_vars = defaultdict(set)

    def current_scope(self):
        if len(self.scope_stack) == 1:
            return "<global>"
        return '.'.join(self.scope_stack[1:])

    def visit_ClassDef(self, node):
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node):
        self.scope_stack.append(node.name)
        self._register_function_params(node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self.scope_stack.append(node.name)
        self._register_function_params(node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def _register_function_params(self, node):
        stmt = node.lineno
        scope = self.current_scope()

        args = node.args
        param_names = [arg.arg for arg in args.args + args.kwonlyargs]
        if args.vararg:
            param_names.append(args.vararg.arg)
        if args.kwarg:
            param_names.append(args.kwarg.arg)

        self.scope_vars[scope].update(param_names)
        for param in param_names:
            self.results[scope][(param, stmt)].add("set")

    def visit_Name(self, node):
        pos = (node.lineno, node.col_offset, node.id)
        if pos not in self.var_positions:
            return
        stmt = self.stmt_map.get(node.lineno)
        if stmt is None:
            return

        varname = node.id
        action = 'get' if isinstance(node.ctx, ast.Load) else 'set' if isinstance(node.ctx, ast.Store) else None
        if not action:
            return

        scope = self.current_scope()

        ''' replace w/ code below, to handle global declared vars
        # Check if variable is declared in current scope
        if action == 'get' and varname not in self.scope_vars[scope]:
            # Read from outer scope (assumed <global> here)
            target_scope = "<global>"
        else:
            # Write or local read
            target_scope = scope
            self.scope_vars[scope].add(varname)
        '''

        # Check if variable is declared global in current scope
        if varname in self.global_declared_vars.get(scope, set()):
            target_scope = "<global>"
        elif action == 'get' and varname not in self.scope_vars[scope]:
            # Read from outer scope (assumed <global>)
            target_scope = "<global>"
        else:
            target_scope = scope
            self.scope_vars[scope].add(varname)

        self.results[target_scope][(varname, stmt)].add(action)

    def visit_Global(self, node):
        stmt = node.lineno
        scope = self.current_scope()
        #print('visit_Global', stmt, scope)
        for name in node.names:
            self.global_declared_vars[scope].add(name)
            self.results['<global>'][(name, stmt)].add("declare")
            #print(self.results)


def cx_gen_actions_var(tree, tokens, stmts):
    stmt_map = build_stmt_line_map(stmts)
    var_positions = build_variable_lookup(tokens)
    extractor = VarActionExtractor(stmt_map, var_positions)
    extractor.visit(tree)

    final = defaultdict(list)
    count = 0
    for scope, var_stmt_map in extractor.results.items():
        for (var, stmt), actions in var_stmt_map.items():
            if 'get' in actions and 'set' in actions:
                action = 'getset'
            elif 'get' in actions:
                action = 'get'
            elif 'set' in actions:
                action = 'set'
            else:
                action = '' #continue TODO: could record 'initialize' action
            final[scope].append({"var": var, "stmt": stmt, "action": action})
            count += 1

    return final

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_actions_var.py <example.py>")
        sys.exit(1)

    filename = sys.argv[1]
    source_code = read_source_file(filename)
    tokens = load_json_file(derive_filename(filename, 'tokens'))
    stmts = load_json_file(derive_filename(filename, 'stmts'))

    tree = parse_ast(source_code)
    var_actions = cx_gen_actions_var(tree, tokens, stmts)

    output_path = derive_filename(filename, 'actions_var')
    write_json_file(var_actions, output_path)

    count = sum(len(v) for v in var_actions.values())
    print(f"Wrote {count} actions_var to {output_path}")
