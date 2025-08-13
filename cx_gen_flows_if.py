import ast
import sys
import os
import json
import argparse
from typing import List, Dict, Any, Optional, Set, Tuple

# Import necessary classes from cx_cfg6.py
try:
    from cx_cfg6 import CFG, CFGManager, CFGNode, CFGArc
except ImportError:
    print("Error: Could not import CFG and CFGManager from cx_cfg6.py.")
    print("Please ensure cx_cfg6.py is in the same directory or your PYTHONPATH is configured.")
    sys.exit(1)

# Import helper functions from cx_cfg6_utils.py
try:
    from cx_cfg6_utils import _get_first_executable_line_forward, _scope_type, print_cfgs
except ImportError:
    print("Error: Could not import helper functions from cx_cfg6_utils.py.")
    print("Please ensure cx_cfg6_utils.py is in the same directory or your PYTHONPATH is configured.")
    sys.exit(1)


# --- Helper Functions for get_if_info ---

def _resolve_target_line(target_node: Optional[CFGNode], cfg: CFG) -> int:
    """
    Resolves a target CFGNode to its corresponding executable line number.
    Uses start_line if available, otherwise traverses using _get_first_executable_line_forward.
    Returns -1 if no executable line is found.
    """
    if target_node is None:
        return -1

    if target_node.start_line is not None and target_node.start_line != -1:
        # Direct line for normal statements, if_condition, etc.
        return target_node.start_line
    elif target_node.node_type in ('if_join', 'loop_exit', 'loop_exit_for'):
        # For join/exit nodes, find the next executable statement *after* them
        resolved_line = _get_first_executable_line_forward(target_node, cfg, set())
        return resolved_line if resolved_line is not None else -1
    else:
        # Fallback for other conceptual nodes that don't have a direct line
        resolved_line = _get_first_executable_line_forward(target_node, cfg, set())
        return resolved_line if resolved_line is not None else -1


def _find_if_branch_targets(node: CFGNode, cfg: CFG) -> Tuple[Optional[CFGNode], Optional[CFGNode], Optional[CFGNode]]:
    true_target_node: Optional[CFGNode] = None
    elif_target_node: Optional[CFGNode] = None
    else_or_join_target_node: Optional[CFGNode] = None

    # First pass: Identify explicit true_branch and false_branch
    for u, v, data in cfg._graph.edges(data=True):
        if u == node.node_id:
            arc = data['data']
            target_node_obj = cfg.get_node(v)

            if target_node_obj:
                if arc.arc_type == 'true_branch':
                    # Only accept true_branch if it leads to an executable statement,
                    # not directly to a join/exit node (CFG anomaly)
                    if target_node_obj.node_type not in ('if_join', 'exit_point'):
                        true_target_node = target_node_obj
                elif arc.arc_type == 'false_branch':
                    else_or_join_target_node = target_node_obj

    # Second pass: Handle 'normal' arcs. These are tricky.
    # They can be the TRUE path into a nested structure OR an ELIF.
    for u, v, data in cfg._graph.edges(data=True):
        if u == node.node_id:
            arc = data['data']
            target_node_obj = cfg.get_node(v)

            if target_node_obj and arc.arc_type == 'normal':
                # Rule 1: If true_target_node is still None (no valid true_branch found yet),
                # AND this 'normal' arc leads to a non-join/exit node,
                # it's a strong candidate for the TRUE path.
                # This covers `if A: if B:` where A->B is 'normal'.
                # This also covers `if A: for B:` where A->B is 'normal'.
                if true_target_node is None and target_node_obj.node_type not in ('if_join', 'exit_point'):
                    true_target_node = target_node_obj

                # Rule 2: If we have a 'normal' arc to an 'if_condition' node,
                # AND this 'if_condition' is *NOT* the same as our *already determined* true_target_node,
                # THEN it must be an 'elif'.
                elif target_node_obj.node_type == 'if_condition':
                    if true_target_node is None or true_target_node.node_id != target_node_obj.node_id:
                        elif_target_node = target_node_obj
                        # If we found an elif, it takes precedence for the false path
                        # over any false_branch leading to an 'else' block or 'if_join'.
                        else_or_join_target_node = None # Clear it if set by false_branch

    return true_target_node, elif_target_node, else_or_join_target_node

# --- Standalone Query Function for IF statements ---
def get_if_info(cfg: CFG) -> List[Dict[str, Any]]:
    """
    Identifies and returns information about 'if', 'elif', and 'else' statements
    within a given CFG, including their true and false branch targets.
    """
    if_details: List[Dict[str, Any]] = []
    scope_name = cfg.name
    scope_type = _scope_type(scope_name)

    for node_id, node in cfg._nodes_by_id.items():
        if node.node_type == 'if_condition' and node.start_line is not None and node.start_line != -1:
            stmt_from = node.start_line
            stmt_to_true: int = -1
            stmt_to_false: int = -1

            # Use helper to find the raw target nodes
            true_target_node, elif_target_node, else_or_join_target_node = _find_if_branch_targets(node, cfg)

            # Resolve stmt_to_true
            stmt_to_true = _resolve_target_line(true_target_node, cfg)

            # Resolve stmt_to_false with strict priority
            if elif_target_node:
                stmt_to_false = _resolve_target_line(elif_target_node, cfg)
            elif else_or_join_target_node:
                stmt_to_false = _resolve_target_line(else_or_join_target_node, cfg)
            # If neither elif nor else/join target is found, it defaults to -1 (already initialized)

            if_details.append({
                'stmt_from': stmt_from,
                'stmt_to_true': stmt_to_true,
                'stmt_to_false': stmt_to_false,
                'type': 'if_stmt',
                'scope': scope_name,
                'scope_type': scope_type
            })

    return if_details

def cx_gen_flows_if(cfg_manager: CFGManager) -> List[Dict[str, Any]]:
    """
    Generates if/elif/else control flow connections for all CFGs managed by the CFGManager.
    """
    all_cfgs = cfg_manager.get_all_cfgs()
    all_if_results: List[Dict[str, Any]] = []

    for cfg_name, cfg_obj in all_cfgs.items():
        if_results_for_cfg = get_if_info(cfg_obj)
        all_if_results.extend(if_results_for_cfg)

    return all_if_results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Identify if/elif/else flow connections in Python code CFGs.")
    parser.add_argument("input_filename", help="Path to the Python source file.")
    parser.add_argument("--debug", action="store_true", help="Enable debug print statements.")

    args = parser.parse_args()

    input_filename = args.input_filename
    debug_mode = args.debug

    if not os.path.exists(input_filename):
        print(f"Error: File not found: {input_filename}", file=sys.stderr)
        sys.exit(1)

    try:
        manager = CFGManager()
        manager.load_from_file(input_filename)

        if debug_mode:
            print_cfgs(manager)

        all_if_results = cx_gen_flows_if(manager)

        if debug_mode:
            if all_if_results:
                print(f"\nFound {len(all_if_results)} if/elif/else connections:")
                for res in all_if_results:
                    print(f"  Type: {res['type']}, Scope: {res['scope']}, From Line: {res['stmt_from']}, True To: {res['stmt_to_true']}, False To: {res['stmt_to_false']}")
            else:
                print("No if/elif/else connections found for this CFG.")

        base_name, _ = os.path.splitext(input_filename)
        output_filename = base_name + ".flows_if.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
           json.dump(all_if_results, f, indent=4)
        print(f"Wrote {len(all_if_results)} flows_if to {output_filename}")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)