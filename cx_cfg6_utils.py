# cx_cfg6_utils.py

import sys
import os
import json
from typing import List, Dict, Any, Optional, Set

# Import necessary classes from cx_cfg6.py
from cx_cfg6 import CFG, CFGNode # Import CFGNode and CFGArc for type hints if needed

# TODO: detect constructor
def _scope_type(scope_name):
    if scope_name == '<global>':
        result = '<global>' #TODO - decide value here
    elif '.' in scope_name:
        result = 'method'
    else:
        result= 'function'
    return result

# --- Helper Function for Recursive Line Finding (Forward Traversal) ---
def _get_first_executable_line_forward(start_node: CFGNode, cfg: CFG, visited: Set[int]) -> Optional[int]:
    #print(f"DEBUG: _get_first_executable_line_forward called for Node ID: {start_node.node_id}, Type: {start_node.node_type}, Line: {start_node.start_line}")

    if start_node.node_id in visited:
        #print(f"DEBUG: Node {start_node.node_id} already visited. Returning None.")
        return None

    visited.add(start_node.node_id)

    if start_node.node_id == cfg.exit_node_id:
        #print(f"DEBUG: Node {start_node.node_id} is exit node. Returning -1.")
        return -1

    # Base Case 2: If it's an executable statement node with a valid line number.
    condition_check = (start_node.node_type in ('normal', 'if_condition', 'loop_condition', 'try_entry', 'with_entry',
                                 'except_handler_entry', 'return', 'iterator_init'))
    line_valid_check = (start_node.start_line is not None and start_node.start_line != -1)
    #print(f"DEBUG: Node {start_node.node_id}: Type check ({condition_check}), Line valid check ({line_valid_check})")

    if condition_check and line_valid_check:
        #print(f"DEBUG: Node {start_node.node_id}: Found direct executable line: {start_node.start_line}. Returning.")
        return start_node.start_line

    # Special Handling for 'loop_condition_for' nodes:
    # ... (rest of the function remains the same, no new prints needed in this block for now)
    if start_node.node_type == 'loop_condition_for' and (start_node.start_line is None or start_node.start_line == -1):
        #print(f"DEBUG: Node {start_node.node_id}: Handling loop_condition_for with no line.")
        for pred_id in cfg._graph.predecessors(start_node.node_id):
            pred_node = cfg.get_node(pred_id)
            if pred_node and pred_node.node_type == 'iterator_init' and \
               pred_node.start_line is not None and pred_node.start_line != -1:
                #print(f"DEBUG: Node {start_node.node_id}: Found iterator_init predecessor {pred_node.node_id} at line {pred_node.start_line}. Returning.")
                return pred_node.start_line

    # Recursive Step:
    #print(f"DEBUG: Node {start_node.node_id}: Traversing successors...")
    for succ_id in cfg._graph.successors(start_node.node_id):
        succ_node = cfg.get_node(succ_id)
        if succ_node:
            line = _get_first_executable_line_forward(succ_node, cfg, visited.copy())
            if line is not None:
                #print(f"DEBUG: Node {start_node.node_id}: Successor {succ_node.node_id} returned line {line}. Propagating.")
                return line
    #print(f"DEBUG: Node {start_node.node_id}: No executable line found down this path. Returning None.")
    return None


def _get_last_statement_lines_of_branch(node: CFGNode, cfg: CFG, visited: Optional[Set[int]] = None) -> List[int]:
    """
    Recursively finds the end_line of the last 'normal' or 'return' statement
    that eventually leads to the given 'node' in a branch's flow.
    Handles conceptual nodes like 'if_join' by looking at their predecessors.
    Returns a list of all such lines found.
    """
    if visited is None:
        visited = set()
    # Prevent infinite recursion for cycles in graphs
    if node.node_id in visited:
        return [] 

    visited.add(node.node_id)

    lines: List[int] = []

    # Case 1: Base case - a normal statement block or a return statement
    if node.node_type == 'normal' and node.end_line is not None and node.end_line != -1:
        lines.append(node.end_line)
    elif node.node_type == 'return' and node.start_line is not None and node.start_line != -1:
        lines.append(node.start_line)
    # NEW Base Case / Stop Condition: If it's an if_condition node, do NOT trace further back.
    # An if_condition node marks the *beginning* of a conditional path, not the end of a branch.
    elif node.node_type == 'if_condition':
        # print(f"DEBUG: _get_last_statement_lines_of_branch stopping at if_condition node {node.node_id} (line {node.start_line})")
        return [] # Stop tracing here, do not include lines before the if_condition
    # Case 2: Recursive case - for other conceptual nodes or those that need further tracing
    else:
        for pred_id in cfg._graph.predecessors(node.node_id):
            pred_node = cfg.get_node(pred_id)
            if pred_node:
                lines.extend(_get_last_statement_lines_of_branch(pred_node, cfg, visited))

    return list(set(lines)) # Return unique lines

def print_cfg(cfg_obj, cfg_name=''):
    print(f"\n--- CFG: {cfg_name} ---")
    print(f"  Entry Node ID: {cfg_obj.entry_node_id}")
    print(f"  Exit Node ID: {cfg_obj.exit_node_id}")
    print(f"  Total Nodes: {len(cfg_obj._nodes_by_id)}")
    print(f"  Total Arcs: {len(cfg_obj._graph.edges)}")

    print("  Nodes (ID, Type, Start Line, AST Node Types, Source Snippet):")
    for node_id, node in cfg_obj._nodes_by_id.items():
        ast_node_types = [type(n).__name__ for n in node.ast_nodes] if node.ast_nodes else []
        # Attempt to get a short source preview
        source_preview = (node.source_code.splitlines()[0][:50] + "..." if node.source_code and len(node.source_code) > 50 else node.source_code) if node.source_code else ""
        print(f"    - {node.node_id}: Type={node.node_type}, Line={node.start_line}, AST={ast_node_types}, Source='{source_preview}'")

    print("  Arcs (Source ID -> Target ID, Type, Condition):")
    for u, v, data in cfg_obj._graph.edges(data=True):
        arc = data['data']
        cond_str = f" (cond: '{arc.condition}')" if arc.condition else ""
        print(f"    - {u} -> {v}, Type={arc.arc_type}", end='')
        if cond_str != '':
           print(f"Condition={cond_str}")
        else:
           print()

def print_cfgs(cfg_mgr):
    for cfg_name, cfg_obj in cfg_mgr.get_all_cfgs().items():
        print_cfg(cfg_obj, cfg_name)
