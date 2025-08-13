import sys
from cx_utils import (
    load_json_file,
    derive_output_filename,
    write_json_file,
)

def cx_gen_flows_return(returns_data, calls_data):
    """Adds 'stmt_to' list to each return item based on scope/target_name match."""
    # Build a mapping: target_name → list of stmt_froms
    call_map = {}
    for call in calls_data:
        target = call.get("target_name")
        if target:
            call_map.setdefault(target, []).append(call["stmt_from"])

    # Enhance return entries with 'stmt_to', 'type'
    for ret in returns_data:
        scope = ret.get("scope")
        ret["stmt_to"] = sorted(call_map.get(scope, []))
        ret["type"] = "return"

    return returns_data

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_flow_returns.py <source_file.py>")
        sys.exit(1)

    source_file = sys.argv[1]
    base_file = source_file.replace(".py", "")

    returns_from_file = derive_output_filename(source_file, "flows_return_from")
    calls_file = derive_output_filename(source_file, "flows_call")
    output_file = derive_output_filename(source_file, "flows_return")

    returns_data = load_json_file(returns_from_file)
    calls_data = load_json_file(calls_file)

    enhanced_data = cx_gen_flows_return(returns_data, calls_data)

    write_json_file(enhanced_data, output_file)
    print(f"Wrote {len(enhanced_data)} return flow(s) to {output_file}")
