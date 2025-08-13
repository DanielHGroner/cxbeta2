# cx_gen_flows_break.py

import sys
import os
import json
import argparse
import traceback # For conditional traceback printing
from typing import List, Dict, Any, Optional, Set

# Import necessary classes from cx_6.py
try:
    from cx_cfg6 import CFG, CFGManager, CFGNode, CFGArc
except ImportError:
    print("Error: Could not import CFG and CFGManager from cx_cfg6.py.", file=sys.stderr)
    print("Please ensure cx_cfg6.py is in the same directory or your PYTHONPATH is configured.", file=sys.stderr)
    sys.exit(1)

# Import helper functions from cx_cfg6_utils.py
try:
    from cx_cfg6_utils import _get_first_executable_line_forward, _scope_type, print_cfgs
except ImportError:
    print("Error: Could not import helper functions from cx_cfg6_utils.py.", file=sys.stderr)
    print("Please ensure cx_cfg6_utils.py is in the same directory or your PYTHONPATH is configured.", file=sys.stderr)
    sys.exit(1)


# --- Standalone Query Function ---
def get_break_info(cfg: CFG) -> List[Dict[str, Any]]:
    """
    Identifies and returns information about 'break' statements within a given CFG,
    including their 'from' line and their 'to' (next executed) line.

    Args:
        cfg: The CFG object to query.

    Returns:
        A list of dictionaries, each containing:
        - 'stmt_from': The line number where the 'break' statement begins.
        - 'stmt_to': The line number of the statement executed immediately after the break,
                     or -1 if the break leads to the scope's exit.
        - 'type': 'break'
        - 'scope': The name of the scope (e.g., function name, '<global>').
        - 'scope_type': The type of the scope (e.g., 'function', 'method', '<global>').
    """
    results = []
    display_scope_name = cfg.name

    for node_id, node in cfg._nodes_by_id.items():
        if node.node_type == 'break':
            stmt_from = node.end_line  # or node.start_line, depending on preference for single-line statements

            # A break node should have exactly one successor, which represents the jump target
            successors = cfg.get_successors(node_id)
            if not successors:
                # This shouldn't happen for a valid break, but handle defensively
                continue

            # The successor of a 'break' node is typically a 'loop_exit' or 'loop_exit_for'
            # conceptual node, which then points to the actual code after the loop.
            succ_node_from_break = successors[0]

            # Use the helper function to find the first executable line reachable from the successor
            # Pass an empty set for 'visited' as we start a new traversal from this point
            resolved_to_line = _get_first_executable_line_forward(succ_node_from_break, cfg, set())

            stmt_to = -1 # Default to -1 (scope exit)

            if resolved_to_line is not None:
                stmt_to = resolved_to_line

            # Ensure we correctly interpret -1 as exit, and actual line numbers
            # If resolved_to_line indicates the CFG's exit node, ensure stmt_to is -1
            if resolved_to_line == cfg.exit_node_id:
                 stmt_to = -1

            results.append({
                'stmt_from': stmt_from,
                'stmt_to': stmt_to,
                'type': 'break',
                'scope': display_scope_name,
                'scope_type': _scope_type(display_scope_name)
            })
    return results

# --- Aggregation Function for Multiple CFGs (if scope is '*') ---
def cx_gen_flows_break(manager: CFGManager) -> List[Dict[str, Any]]:
    """
    Aggregates 'break' information from all CFGs managed by the CFGManager.
    """
    all_break_results = []
    for cfg_name, cfg in manager.get_all_cfgs().items():
        # You can add a debug print here if you decide to pass debug_mode to this function
        # Or just rely on the main block's prints for all scopes
        results = get_break_info(cfg)
        all_break_results.extend(results)
    return all_break_results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Identify 'break' statement flow connections in Python code CFGs."
    )
    parser.add_argument(
        "input_filename",
        help="Path to the Python source file."
    )
    parser.add_argument(
        "--scope",
        default="*",
        help="Optional: CFG scope to query (e.g., '<global>', 'my_function'). Use '*' for all scopes. Default: '*'"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug print statements."
    )

    args = parser.parse_args()

    input_filename = args.input_filename
    cfg_to_query_name = args.scope
    debug_mode = args.debug

    if not os.path.exists(input_filename):
        print(f"Error: File not found: {input_filename}", file=sys.stderr)
        sys.exit(1)

    try:
        manager = CFGManager()
        manager.load_from_file(input_filename)

        # Display the CFGs in debug mode
        if debug_mode:
            print_cfgs(manager)

        break_flow_results = []
        if cfg_to_query_name != '*':
            # Handle specific scope query
            target_cfg = manager.get_all_cfgs().get(cfg_to_query_name)
            if not target_cfg:
                print(f"Error: CFG '{cfg_to_query_name}' not found in '{input_filename}'.", file=sys.stderr)
                print("Available CFGs:", list(manager.get_all_cfgs().keys()), file=sys.stderr)
                sys.exit(1)
            
            # Print for single scope (consistent with your existing pattern)
            print(f"--- Running 'get_break_info' for CFG: {target_cfg.name} ---")
            break_flow_results = get_break_info(target_cfg)
        else:
            # Handle all scopes query
            break_flow_results = cx_gen_flows_break(manager)

        if debug_mode:
            if break_flow_results:
                print("\nFound 'break' flow connections:")
                for res in break_flow_results:
                    print(f"  Type: {res['type']}, Scope: {res['scope']}, From Line: {res['stmt_from']}, To Line: {res['stmt_to']}")
            else:
                print("No 'break' flow connections found for this CFG or scopes.")

        base_name, _ = os.path.splitext(input_filename)
        output_filename = base_name + ".flows_break.json"

        with open(output_filename, 'w', encoding='utf-8') as f:
           json.dump(break_flow_results, f, indent=4)
        print(f"Wrote {len(break_flow_results)} 'break' flow connections to {output_filename}")

    except ImportError as ie:
        print(f"Import Error: {ie}. Make sure all required CX-CFG files are in place.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        if debug_mode: # Conditional traceback printing
            traceback.print_exc()
        sys.exit(1)