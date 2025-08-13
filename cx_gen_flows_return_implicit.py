# cx_gen_flows_implicit_return.py

import sys
import os
import json
import argparse
from typing import List, Dict, Any, Optional

# Import necessary classes from cx_cfg6.py
try:
    from cx_cfg6 import CFG, CFGManager, CFGNode, CFGArc
except ImportError:
    print("Error: Could not import CFG and CFGManager from cx_cfg6.py.")
    print("Please ensure cx_cfg6.py is in the same directory or your PYTHONPATH is configured.")
    sys.exit(1)

# Import helper functions from cx_cfg6_utils.py
try:
    from cx_cfg6_utils import _get_last_statement_lines_of_branch, _scope_type, print_cfgs
except ImportError:
    print("Error: Could not import helper functions from cx_cfg6_utils.py.")
    print("Please ensure cx_cfg6_utils.py is in the same directory or your PYTHONPATH is configured.")
    sys.exit(1)


# --- Standalone Query Function ---
def get_implicit_returns_info(cfg: CFG) -> List[Dict[str, Any]]:
    """
    Identifies and returns information about implicit return points within a given CFG.
    An implicit return is any statement in a function (or method/global scope) that
    may be the last executing statement but is not an explicit 'return' statement.

    Args:
        cfg: The CFG object to query.

    Returns:
        A list of dictionaries, each containing:
        - 'from_line_id': The end line of the last statement in the implicit return path.
        - 'type': 'implicit_return'
        - 'scope': The name of the CFG (function name or '<global>').
    """
    results = []
    
    # The display scope name is simply the CFG's name, as cx_cfg6.py handles '<global>'
    display_scope_name = cfg.name 

    if cfg.exit_node_id is None:
        # A CFG without an exit node (e.g., empty function) cannot have implicit returns
        return []

    # Get all direct predecessors of the CFG's exit node
    exit_predecessor_nodes = cfg.get_predecessors(cfg.exit_node_id)
    
    for pred_node in exit_predecessor_nodes:
        # We are looking for implicit returns, so we explicitly exclude 'return' nodes
        if pred_node.node_type == 'return':
            continue # This is an explicit return, not an implicit one

        # For any other node type that directly precedes the exit,
        # it represents an implicit return path. We use the helper to find
        # the actual source line(s) that comprise this implicit return.
        from_line_ids_for_branch = _get_last_statement_lines_of_branch(pred_node, cfg)
        
        # Each line returned by the helper corresponds to a distinct "from" point
        for from_line_id in from_line_ids_for_branch:
            # Ensure we have a valid line number to report
            if from_line_id is not None and from_line_id != -1:
                results.append({
                    'stmt_from': from_line_id,
                    'return_type': 'implicit_return',
                    'is_raise': False,
                    'scope': display_scope_name,
                    'scope_type': _scope_type(display_scope_name)
                })
    return results

# top level API
def cx_gen_flows_return_implicit(cfg_mgr):
    target_cfgs = cfg_mgr.get_all_cfgs()
    implicit_returns_results = []
    #print(target_cfgs)
    for target_cfg_name in target_cfgs:
        #print(target_cfg_name)
        target_cfg = target_cfgs[target_cfg_name]
        #print(f"--- Running 'get_implicit_returns_info' for CFG: {target_cfg.name} ---")
        implicit_returns_results += get_implicit_returns_info(target_cfg) # get & cumulate implicit returns
        #print(f'Found {len(implicit_returns_result)} implicit returns')
    return implicit_returns_results


# --- Test Code for if __name__ == '__main__': ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Identify return_implicit statements in Python code CFGs.")
    parser.add_argument("input_filename", help="Path to the Python source file.")
    parser.add_argument("--scope", default="*", help="Optional: CFG scope to query (e.g., '<global>', 'my_function'). Use '*' for all scopes.")
    parser.add_argument("--debug", action="store_true", help="Enable debug print statements.") # New argument
    
    args = parser.parse_args()

    input_filename = args.input_filename
    cfg_to_query_name = args.scope
    debug_mode = args.debug # Get debug_mode from args

    if debug_mode:
        print("--- Testing cx_gen_flows_implicit_return.py (Implicit Return Query) ---")

    if not os.path.exists(input_filename):
        print(f"\nError: File not found at '{input_filename}'. Exiting.")
        sys.exit(1)

    if debug_mode:
        print(f"\nAttempting to load and query CFGs from '{input_filename}' for scope '{cfg_to_query_name}'...")

    manager = CFGManager()
    try:
        manager.load_from_file(input_filename)

        # Display the CFGs
        if debug_mode:
            print_cfgs(manager)
        
        target_cfg = manager.get_all_cfgs().get(cfg_to_query_name)

        if cfg_to_query_name != '*' and not target_cfg:
            print(f"Error: CFG '{cfg_to_query_name}' not found in '{input_filename}'.", file=sys.stderr)
            print("Available CFGs:", list(manager.get_all_cfgs().keys()))
            sys.exit(1)

        #print(f"\n--- Running 'get_implicit_returns_info' for CFG: {target_cfg.name} ---")
        implicit_returns_results = []
        if cfg_to_query_name != '*':
            if debug_mode:
                print(f"--- Running 'get_implicit_returns_info' for CFG: {target_cfg.name} ---")
            implicit_returns_results = get_implicit_returns_info(target_cfg)
        else:
            implicit_returns_results = cx_gen_flows_return_implicit(manager)

        if debug_mode:
            if implicit_returns_results:
                print("\nFound 'implicit_return' connections:")
                for res in implicit_returns_results:
                    print(f"  Scope Type: {res['scope_type']}, Scope: {res['scope']}, From Line: {res['stmt_from']}")
            else:
                print("No 'implicit_return' connections found for this CFG.")

        base_name, _ = os.path.splitext(input_filename)
        output_filename = base_name + ".flows_return_implicit.json" 
        with open(output_filename, 'w', encoding='utf-8') as f:
           json.dump(implicit_returns_results, f, indent=4)
        print(f'Wrote {len(implicit_returns_results)} implicit returns to {output_filename}')

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)

    if debug_mode:
        print("\n--- End of cx_gen_flows_implicit_return.py execution ---")
