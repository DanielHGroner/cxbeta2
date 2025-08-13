import json
import sys
from cx_utils import load_json_file, derive_filename, write_json_file

ACTION_PREFIX_MAP = {
    "get": "<",
    "set": ">",
    "getset": "*",
    "input": "<",
    "output": ">"
}

def cx_gen_allhilites(var_actions, io_actions):
    """
    Builds a symmetric highlight map from variable and I/O actions.
    Returns a dictionary suitable for allhilite2.
    """
    hilite_map = {}

    def add_link(a, b, prefix=''):
        hilite_map.setdefault(a, []).append(prefix+b)
        hilite_map.setdefault(b, []).append(a)

    # Handle variable actions
    for scope, actions in var_actions.items():
        scope_prefix = '' if scope == '<global>' else scope+'.'
        #print(scope, scope_prefix)
        for entry in actions:
            stmt = str(entry["stmt"])
            varname = scope_prefix + entry["var"]
            #print(varname)
            action = entry["action"]
            prefix = ACTION_PREFIX_MAP.get(action, '')
            add_link(stmt, varname, prefix)

    # Handle I/O actions
    for scope, actions in io_actions.items():
        for entry in actions:
            stmt = str(entry["stmt"])
            item = entry["item"]  # like "-display", "-keyboard"
            action = entry["action"]
            prefix = ACTION_PREFIX_MAP.get(action, '')
            add_link(stmt, item, prefix)

    # Optionally deduplicate and sort
    #for k in hilite_map:
    #    hilite_map[k] = sorted(set(hilite_map[k]), key=lambda x: (x[0], x))

    return hilite_map

"""
def write_hilite_js(output_path, hilite_data):
    #Writes the hilite data to a JS file with a const declaration.
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("const allhilite2 = ")
        json.dump(hilite_data, f, indent=2)
        f.write(";\n")
"""


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python cx_gen_allhilites.py <source_file.py>")
        sys.exit(1)

    source_file = sys.argv[1]
    var_actions_file = derive_filename(source_file, "actions_var")
    io_actions_file = derive_filename(source_file, "actions_io")
    output_filename = derive_filename(source_file, "allhilites")

    var_actions = load_json_file(var_actions_file)
    io_actions = load_json_file(io_actions_file)

    hilite_data = cx_gen_allhilites(var_actions, io_actions)

    #base_dir = os.path.dirname(source_file)
    #filename_root = os.path.splitext(os.path.basename(source_file))[0]
    #output_dir = os.path.join(base_dir, "html")
    #output_path = os.path.join(output_dir, f"{filename_root}-hilite.js")
    #print(output_path)
    #write_hilite_js(output_path, hilite_data)

    write_json_file(hilite_data, output_filename)

    print(f"Wrote {len(hilite_data)} items to {output_filename}")
