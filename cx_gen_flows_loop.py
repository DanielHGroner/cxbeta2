# cx_gen_flows_loop.py

import ast
import sys
import os
import json
import argparse
from typing import List, Dict, Any, Optional, Set

# Import necessary classes from cx_cfg6.py
try:
    from cx_cfg6 import CFG, CFGManager, CFGNode, CFGArc
except ImportError:
    print("Error: Could not import CFG and CFGManager from cx_cfg6.py.")
    print("Please ensure cx_cfg6.py is in the same directory or your PYTHONPATH is configured.")
    sys.exit(1)

# Import helper functions from cx_cfg6_utils.py as requested
try:
    from cx_cfg6_utils import _get_first_executable_line_forward, _scope_type, print_cfgs
except ImportError:
    print("Error: Could not import helper functions from cx_cfg6_utils.py.")
    print("Please ensure cx_cfg6_utils.py is in the same directory or your PYTHONPATH is configured.")
    sys.exit(1)

def get_to_true_line(loop_node: CFGNode, cfg: CFG) -> int:
    """
    Given a loop_condition node, return the first reachable line in the loop body.

    Rules:
    - Follow successors that are NOT marked as 'false_branch' or 'no_more_items'.
    - Return the first successor with a valid start_line (e.g., even if it's an if_condition or iterator_init).
    - Skip placeholders like loop_exit or if_join.
    - Return -1 if no such line is found (e.g., degenerate or empty loop).
    """
    disallowed_arc_types = {'false_branch', 'no_more_items'}
    disallowed_node_types = {'loop_exit', 'loop_exit_for', 'if_join', 'exit_point'}

    for succ_node in cfg.get_successors(loop_node.node_id):
        arc = cfg.get_arc(loop_node.node_id, succ_node.node_id)
        #print(loop_node.node_id, succ_node.node_id, arc)
        if arc.arc_type in disallowed_arc_types:
            continue  # Skip the false/exit arc

        if succ_node is None:
            continue

        if succ_node.node_type not in disallowed_node_types and succ_node.start_line is not None:
            return succ_node.start_line

    # Nothing usable found
    return -1

def get_to_false_line(loop_node: CFGNode, cfg: CFG) -> int:
    """
    For a loop_condition node, find the statement executed when the loop condition is false.
    - Follows the 'false_branch' or 'no_more_items' arc.
    - Then uses _get_first_executable_line_forward() to skip over placeholders.
    - Returns -1 if nothing reachable.
    """
    false_arc_types = {'false_branch', 'no_more_items'}

    for succ_node in cfg.get_successors(loop_node.node_id):
        arc = cfg.get_arc(loop_node.node_id, succ_node.node_id)
        if arc.arc_type in false_arc_types:
            succ_node = cfg.get_node(succ_node.node_id)
            if succ_node:
                result = _get_first_executable_line_forward(succ_node, cfg, visited=set())
                return result if result is not None else -1

    return -1  # No false branch arc found

# --- Standalone Query Function ---
def get_loop_info(cfg: CFG, cfg_name: str) -> List[Dict[str, int]]:
    """
    Scans the CFG for loop head nodes and records their control flow branches.

    Returns:
        List of dicts with keys:
            - 'stmt_from': line of loop head
            - 'stmt_to_true': line executed when loop condition is true
            - 'stmt_to_false': line executed when loop condition is false
    """
    results = []

    for node_id, node in cfg._nodes_by_id.items():
        if node.node_type in {'loop_condition', 'loop_condition_for'}:
            #from_line = node.start_line or -1
            #if from_line == -1:
            #    from_line = get_real_stmt_line(cfg, node)
            from_line = node.getStartLine()
            to_true = get_to_true_line(node, cfg)
            to_false = get_to_false_line(node, cfg)
            loop_type = 'for' if node.node_type == 'loop_condition_for' else 'while'
            scope_type = _scope_type(cfg_name)
            results.append({
                "stmt_from": from_line,
                "stmt_to_true": to_true,
                "stmt_to_false": to_false,
                "type": loop_type,
                "scope": cfg_name,
                "scope_type": scope_type
            })

    return results

def cx_gen_flows_loop(cfg_manager):
    
    all_cfgs = cfg_manager.get_all_cfgs()
    all_loop_results: List[Dict[str, Any]] = []

    #print(f"--- Analyzing loops for {input_filename} ---")
    for cfg_name, cfg_obj in all_cfgs.items():
        #print(f"  Processing CFG: {cfg_name}")
        loop_results_for_cfg = get_loop_info(cfg_obj, cfg_name)
        all_loop_results.extend(loop_results_for_cfg)

    return all_loop_results

def check_loop_results(all_loop_results):
    for loop_result in all_loop_results:
        if 'stmt_from' not in loop_result or 'stmt_to_true' not in loop_result or 'stmt_to_false' not in loop_result:
            print(loop_result)        
        elif loop_result['stmt_from'] == -1 or loop_result['stmt_to_true'] == -1:
            print(loop_result)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Identify loop flow connections in Python code CFGs.")
    parser.add_argument("input_filename", help="Path to the Python source file.")
    parser.add_argument("--debug", action="store_true", help="Enable debug print statements.") # New argument
    
    args = parser.parse_args()

    input_filename = args.input_filename
    debug_mode = args.debug # Get debug_mode from args

    if not os.path.exists(input_filename):
        print(f"Error: File not found: {input_filename}", file=sys.stderr)
        sys.exit(1)

    try:
        manager = CFGManager()
        manager.load_from_file(input_filename)

        # Display the CFGs
        if debug_mode:
            print_cfgs(manager)

        all_loop_results = cx_gen_flows_loop(manager)

        check_loop_results(all_loop_results)

        #if debug_mode:
        #    if all_loop_results:
        #        print(f"\nFound {len(all_loop_results)} loop connections:")
        #        for res in all_loop_results:
        #            #print(f"  Type: {res['type']}, Scope: {res['scope']}, From Line: {res['stmt_from']}, True To: {res['stmt_to_true']}, False To: {res['stmt_to_false']}")
        #            print(f"  Scope: {res['scope']}, From Line: {res['stmt_from']}, True To: {res['stmt_to_true']}, False To: {res['stmt_to_false']}")
        #    else:
        #        print("No loop connections found for this CFG.")

        base_name, _ = os.path.splitext(input_filename)
        output_filename = base_name + ".flows_loop.json" 
        with open(output_filename, 'w', encoding='utf-8') as f:
           json.dump(all_loop_results, f, indent=4)
        print(f"Wrote {len(all_loop_results)} flows_loop to {output_filename}")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
