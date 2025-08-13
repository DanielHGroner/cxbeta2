import sys
from cx_utils import load_json_file, derive_filename, write_json_file

def extract_flows_from_pairs(data, from_key, to_key, only_first=False):
    """
    Extracts (from, to) pairs from a list of dicts using specified keys.
    If only_first is True, only the first to_key value is used (for lists).
    Returns a list of (from, to) string pairs.
    """
    flows = []
    for entry in data:
        stmt_from = str(entry[from_key])
        stmt_to_val = entry[to_key]

        if isinstance(stmt_to_val, list):
            if stmt_to_val:
                stmt_to = str(stmt_to_val[0]) if only_first else [str(v) for v in stmt_to_val]
                if isinstance(stmt_to, list):
                    for t in stmt_to:
                        flows.append((stmt_from, t))
                else:
                    flows.append((stmt_from, stmt_to))
        else:
            stmt_to = str(stmt_to_val)
            flows.append((stmt_from, stmt_to))
    return flows

def extract_flows_from_conditionals(data):
    """
    Extracts (from, [to_true, to_false]) flows from conditional flow data.
    Ensures to_true is always first in the output list.
    """
    flows = []
    for entry in data:
        stmt_from = str(entry["stmt_from"])
        to_true = str(entry["stmt_to_true"])
        to_false = str(entry["stmt_to_false"])
        flows.append((stmt_from, [to_true, to_false]))
    return flows

def build_arrow_map(calls, returns, loopbacks, endifs, breaks, ifs, loops):
    """
    Builds the complete allarrows map from various flow edges.
    """
    arrow_map = {}

    # Add simple pair flows
    for stmt_from, stmt_to in calls + returns + loopbacks + endifs + breaks:
        #arrow_map.setdefault(stmt_from, []).append(stmt_to)
        #arrow_map.setdefault(stmt_from, set()).add(stmt_to)
        arrow_map[stmt_from] = stmt_to # assuming there is just 1 distinct from/to pair
        #TODO: error check if multiple tos for a given from

    # Add conditionals (stmt_from → [true, false])
    for stmt_from, targets in ifs + loops:
        #arrow_map.setdefault(stmt_from, []).extend(targets)
        #arrow_map.setdefault(stmt_from, set()).update(targets)
        arrow_map[stmt_from] = targets
        #TODO: error check if multiple tos for a given from

    return arrow_map

def cx_gen_allarrows(calls_data, returns_data, loopbacks_data, endifs_data, breaks_data, ifs_data, loops_data):
    # Extract flows for different cases
    call_flows = extract_flows_from_pairs(calls_data, "stmt_from", "stmt_to")
    return_flows = extract_flows_from_pairs(returns_data, "stmt_from", "stmt_to", only_first=True)
    loopback_flows = extract_flows_from_pairs(loopbacks_data, "stmt_from", "stmt_to")
    endifs_flows = extract_flows_from_pairs(endifs_data, "stmt_from", "stmt_to")
    breaks_flows = extract_flows_from_pairs(breaks_data, "stmt_from", "stmt_to")
    if_flows = extract_flows_from_conditionals(ifs_data)
    loop_flows = extract_flows_from_conditionals(loops_data)
    # Build and return output
    arrows_map = build_arrow_map(call_flows, return_flows, loopback_flows, endifs_flows, breaks_flows, if_flows, loop_flows)
    return arrows_map


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_js_arrows.py <source_file.py>")
        sys.exit(1)

    source_file = sys.argv[1]

    # Derive JSON filenames
    calls_file = derive_filename(source_file, "flows_call")
    returns_file = derive_filename(source_file, "flows_return")
    loopbacks_file = derive_filename(source_file, "flows_loopback")
    endifs_file = derive_filename(source_file, "flows_endif")
    breaks_file = derive_filename(source_file, "flows_break")
    ifs_file = derive_filename(source_file, "flows_if")
    loops_file = derive_filename(source_file, "flows_loop")
    output_filename = derive_filename(source_file, "allarrows")

    # Read JSON data
    calls_data = load_json_file(calls_file)
    returns_data = load_json_file(returns_file)
    loopbacks_data = load_json_file(loopbacks_file)
    endifs_data = load_json_file(endifs_file)
    breaks_data = load_json_file(breaks_file)
    ifs_data = load_json_file(ifs_file)
    loops_data = load_json_file(loops_file)

    # build arrows map for all cases
    arrows_map = cx_gen_allarrows(calls_data, returns_data, loopbacks_data, endifs_data, breaks_data, ifs_data, loops_data)

    # write output
    write_json_file(arrows_map, output_filename)

    print(f"Wrote {len(arrows_map)} items to {output_filename}")
