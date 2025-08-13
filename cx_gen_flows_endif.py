# cx_gen_flows_endif.py

import sys
import os
import json
from typing import List, Dict, Any, Optional, Set
import argparse
from cx_cfg6_utils import _get_last_statement_lines_of_branch, _get_first_executable_line_forward, _scope_type, print_cfgs
# Import necessary classes from cx_cfg6.py
# Assuming cx_cfg6.py is in the same directory or accessible via PYTHONPATH
try:
    from cx_cfg6 import CFG, CFGManager, CFGNode, CFGArc # Import CFGNode and CFGArc for type hints if needed
    import ast # ast is needed for type hints in CFGNode/CFGArc
except ImportError:
    print("Error: Could not import CFG and CFGManager from cx_cfg6.py.")
    print("Please ensure cx_cfg6.py is in the same directory or your PYTHONPATH is configured.")
    sys.exit(1)

# --- Standalone Query Function ---
# --- Standalone Query Function ---
def get_end_if_info(cfg: CFG) -> List[Dict[str, Any]]:
    results = []
    display_scope_name = cfg.name 

    for node_id, node in cfg._nodes_by_id.items():
        if node.node_type == 'if_join':
            successors_of_join = cfg.get_successors(node_id)
            
            if successors_of_join:
                succ_node_from_join = successors_of_join[0]
                
                # --- ADD THIS NEW FILTER ---
                # If the successor of this if_join is another if_join,
                # it means this is an intermediate join in an if/elif/else chain.
                # The 'end_if' will be captured by the final if_join.
                if succ_node_from_join.node_type == 'if_join':
                    continue # Skip this intermediate if_join
                # --- END OF NEW FILTER ---

                resolved_to_line = _get_first_executable_line_forward(succ_node_from_join, cfg, set())
                
                to_line_id_for_this_join = -1
                if resolved_to_line is not None:
                    to_line_id_for_this_join = resolved_to_line
                
                # Existing filter (keep this, it handles different cases)
                if to_line_id_for_this_join == -1 and successors_of_join and successors_of_join[0].node_id != cfg.exit_node_id:
                    continue

                predecessor_nodes = cfg.get_predecessors(node_id)
                
                for pred_node in predecessor_nodes:
                    from_line_ids_for_branch = _get_last_statement_lines_of_branch(pred_node, cfg)
                    
                    for from_line_id in from_line_ids_for_branch:
                        results.append({
                            'stmt_from': from_line_id,
                            'stmt_to': to_line_id_for_this_join,
                            'type': 'end_if',
                            'scope': display_scope_name,
                            'scope_type': _scope_type(display_scope_name)
                        })
    return results


# top level API
def cx_gen_flows_endif(cfg_mgr):
    end_if_results = []
    for cfg_name, cfg in cfg_mgr.get_all_cfgs().items():
        results = get_end_if_info(cfg) # find end_ifs for a given CFG
        end_if_results += results # cumulate the results
    return end_if_results

# --- Test Code for if __name__ == '__main__': ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Identify end_if flow connections in Python code CFGs.")
    parser.add_argument("input_filename", help="Path to the Python source file.")
    parser.add_argument("--scope", default="*", help="Optional: CFG scope to query (e.g., '<global>', 'my_function'). Use '*' for all scopes.")
    parser.add_argument("--debug", action="store_true", help="Enable debug print statements.") # New argument
    
    args = parser.parse_args()

    input_filename = args.input_filename
    cfg_to_query_name = args.scope
    debug_mode = args.debug # Get debug_mode from args

    if debug_mode:
        print("--- Testing cx_gen_flows_endif.py (End If Query) ---")
    
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
        
        # With cx_cfg6.py updated, cfg_to_query_name should now directly match CFG names
        target_cfg = manager.get_all_cfgs().get(cfg_to_query_name)

        if cfg_to_query_name != '*' and not target_cfg:
            print(f"Error: CFG '{cfg_to_query_name}' not found in '{input_filename}'.", file=sys.stderr)
            print("Available CFGs:", list(manager.get_all_cfgs().keys()))
            sys.exit(1)

        if cfg_to_query_name != '*':
           print(f"\n--- Running 'get_end_if_info' for CFG: {target_cfg.name} ---")
           end_if_results = get_end_if_info(target_cfg)

        else: # handle name = * (all cfgs)
            #end_if_results = []
            #for cfg_name, cfg in manager.get_all_cfgs().items():
            #    results = get_end_if_info(cfg)
            #    end_if_results += results
            end_if_results = cx_gen_flows_endif(manager)

        if debug_mode:
            if end_if_results:
                print("Found 'end_if' connections:")
                for res in end_if_results:
                    print(f"  Type: {res['type']}, Scope: {res['scope']}, From Line: {res['stmt_from']}, To Line: {res['stmt_to']}")
            else:
                print("No 'end_if' connections found for this CFG.")
        base_name, _ = os.path.splitext(input_filename)
        output_filename = base_name + ".flows_endif.json" 
        with open(output_filename, 'w', encoding='utf-8') as f:
           json.dump(end_if_results, f, indent=4)
        print('Wrote', len(end_if_results), 'endifs to', output_filename)

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)

    if debug_mode:
        print("\n--- End of cx_gen_flows_endif.py execution ---")
