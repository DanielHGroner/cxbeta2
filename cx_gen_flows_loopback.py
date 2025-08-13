import sys
import ast
from cx_utils import read_source_file, derive_output_filename, write_json_file

class LoopbackFlowExtractor(ast.NodeVisitor):
    def __init__(self):
        self.results = []
        self.parent_stack = []

    def visit_For(self, node):
        self._handle_loop(node)

    def visit_While(self, node):
        self._handle_loop(node)

    def _handle_loop(self, node):
        loop_header_line = node.lineno
        self.parent_stack.append(loop_header_line)

        # Find all terminal statements in the loop body
        for term_node in self._find_terminal_stmts(node.body):
            self.results.append({
                "stmt_from": term_node.lineno,
                "stmt_to": loop_header_line,
                "type": "loop_back"
            })

        # Visit nested nodes
        self.generic_visit(node)
        self.parent_stack.pop()

    def visit_Continue(self, node):
        stmt_from = node.lineno
        header_line = self._find_enclosing_loop_header()
        if header_line:
            self.results.append({
                "stmt_from": stmt_from,
                "stmt_to": header_line,
                "type": "continue"
            })

    def _find_enclosing_loop_header(self):
        return self.parent_stack[-1] if self.parent_stack else None

    def _find_terminal_stmts(self, body):
        """
        Recursively collect all terminal (last-in-branch) statements in a block,
        excluding continue/break which are handled separately.

        A terminal statement is:
        - the last statement in the block, OR
        - the last statement in each branch of a compound (if/with/try),
        but only if that compound is itself the last in the block.
        """
        terminals = []

        for idx, stmt in enumerate(body):
            is_last_stmt = (idx == len(body) - 1)

            if isinstance(stmt, (ast.If, ast.With, ast.Try)):
                if is_last_stmt:
                    # Only explore branches of compound if it's the final statement
                    branches = []
                    if hasattr(stmt, 'body') and stmt.body:
                        branches.append(stmt.body)
                    if hasattr(stmt, 'orelse') and stmt.orelse:
                        branches.append(stmt.orelse)
                    if hasattr(stmt, 'finalbody') and stmt.finalbody:
                        branches.append(stmt.finalbody)
                    for branch in branches:
                        terminals.extend(self._find_terminal_stmts(branch))
            elif is_last_stmt:
                if not isinstance(stmt, (ast.Continue, ast.Break)):
                    terminals.append(stmt)

        return terminals

def cx_gen_flows_loopback(tree):
    extractor = LoopbackFlowExtractor()
    extractor.visit(tree)
    return extractor.results

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_flows_loopback.py <example.py>")
        sys.exit(1)

    filename = sys.argv[1]
    source_code = read_source_file(filename)
    tree = ast.parse(source_code)

    flows = cx_gen_flows_loopback(tree)

    output_file = derive_output_filename(filename, "flows", variant="loopback", sep="_")
    #print(flows)
    write_json_file(flows, output_file)
    print(f"Wrote {len(flows)} flow_loopback entries to {output_file}")
