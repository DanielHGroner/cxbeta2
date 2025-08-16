import sys
from cx_utils import load_json_file, derive_filename, write_json_file

# TODO - for new arrow generation, migrate to this instead of using cx_gen_allarrows

# build a consolidate flows dict, keyed on from stmt, with value as a list of each flow item
def build_flows_map(flows_list):
    flows_map = {}
    for flows in flows_list:
        for flow_item in flows:
            from_stmt = flow_item['stmt_from']
            if from_stmt in flows_map:
                flows_map[from_stmt].append(flow_item)
            else:
                flows_map[from_stmt] = [flow_item]
    return flows_map

# Top-level call, to consolidate to dict w/ from stmt as key
def cx_gen_flows_all(calls_data, returns_data, loopbacks_data, endifs_data, breaks_data, ifs_data, loops_data):
    flows_map = build_flows_map([calls_data, returns_data, loopbacks_data, endifs_data, breaks_data, ifs_data, loops_data])
    return flows_map

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_flows_all.py <source_file.py>")
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
    output_filename = derive_filename(source_file, "flows_all")

    # Read JSON data
    calls_data = load_json_file(calls_file)
    returns_data = load_json_file(returns_file)
    loopbacks_data = load_json_file(loopbacks_file)
    endifs_data = load_json_file(endifs_file)
    breaks_data = load_json_file(breaks_file)
    ifs_data = load_json_file(ifs_file)
    loops_data = load_json_file(loops_file)

    # build arrows map for all cases
    flows_all = cx_gen_flows_all(calls_data, returns_data, loopbacks_data, endifs_data, breaks_data, ifs_data, loops_data)

    # write output
    write_json_file(flows_all, output_filename)

    print(f"Wrote {len(flows_all)} items to {output_filename}")
