# For NAME tokens, determine a more specific type_name

# TODO: @decorator - the decorator is tagged as a variable - fine for now
# TODO: from <module> import importable - the <module> name is tagged as unknown - fine for now

import sys
import ast
from cx_utils import (
    read_source_file,
    write_json_file,
    load_json_file,
    derive_filename,
    parse_ast
)

VALID_TYPE_NAMES = {
    "variable",
    "parameter",
    "function_def",
    "function_call",
    "class_def",
    "class_reference",
    "attribute",
    "imported_name",
    "method_def",
    "exception",
    "unknown"
}

def get_token_lookup(tokens):
    return {
        (t['start']['line'], t['start']['col']): t
        for t in tokens
        if t.get('type') == 'NAME'
    }

class NameClassifier(ast.NodeVisitor):
    def __init__(self, token_lookup):
        self.token_lookup = token_lookup

    def _mark_by_text(self, lineno, name_text, type_name):
        for (line, col), token in self.token_lookup.items():
            if line == lineno and token.get('text') == name_text:
                token['type_name'] = type_name
                return

    def visit_FunctionDef(self, node):
        self._mark_by_text(node.lineno, node.name, 'function_def')
        for arg in node.args.args:
            if hasattr(arg, 'lineno') and hasattr(arg, 'col_offset'):
                self._mark_by_text(arg.lineno, arg.arg, 'parameter')
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        self._mark_by_text(node.lineno, node.name, 'class_def')
        self.generic_visit(node)

    def visit_Call(self, node):
        func = node.func
        if isinstance(func, ast.Name):
            self._mark_by_text(func.lineno, func.id, 'function_call')
        elif isinstance(func, ast.Attribute):
            if hasattr(func, 'attr_node'):
                self._mark_by_text(func.attr_node.lineno, func.attr_node.id, 'function_call')
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if hasattr(node, 'attr_node'):
            self._mark_by_text(node.attr_node.lineno, node.attr_node.id, 'attribute')
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self._mark_by_text(node.lineno, name, 'imported_name')
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self._mark_by_text(node.lineno, name, 'imported_name')
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.name and isinstance(node.name, str):
            self._mark_by_text(node.lineno, node.name, 'exception')
        if node.type and isinstance(node.type, ast.Name):
            self._mark_by_text(node.type.lineno, node.type.id, 'class_reference')
        self.generic_visit(node)

    def visit_Name(self, node):
        key = (node.lineno, node.col_offset)
        if key in self.token_lookup and 'type_name' not in self.token_lookup[key]:
            self.token_lookup[key]['type_name'] = 'variable'
        self.generic_visit(node)

def enrich_ast_nodes(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            node.attr_node = ast.Name(id=node.attr, ctx=node.ctx, lineno=node.lineno, col_offset=node.col_offset)

# augment the NAME tokens with their type (via utility functions and ast tree walk)
def cx_gen_tokens_name(tokens, ast_tree):
    token_lookup = get_token_lookup(tokens)
    enrich_ast_nodes(ast_tree)
    classifier = NameClassifier(token_lookup)
    classifier.visit(ast_tree)

    for token in tokens:
        if token.get('type') == 'NAME' and 'type_name' not in token:
            token['type_name'] = 'unknown'

    return tokens


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_tokens_name.py <example.py>")
        sys.exit(1)

    source_filename = sys.argv[1]
    source_code = read_source_file(source_filename) # get source code
    tokens = load_json_file(derive_filename(source_filename, 'tokens', 'core')) # read tokens_core json

    tree = parse_ast(source_code, filename=source_filename) # create ast tree

    cx_gen_tokens_name(tokens, tree) # augment token json with name types

    output_path = derive_filename(source_filename, 'tokens')
    write_json_file(tokens, output_path)
    print(f"Wrote {len(tokens)} tokens to {output_path}")
