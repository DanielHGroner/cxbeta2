import sys
from cx_utils import load_json_file, write_json_file, derive_filename

def build_header_map(header_list):
    return {tuple(h["start"].values()): h["end_header"] for h in header_list}

def cx_gen_stmts(real, synth, headers):
    combined = real + synth
    header_map = build_header_map(headers)

    for stmt in combined:
        key = tuple(stmt["start"].values())
        if key in header_map:
            stmt["end_header"] = header_map[key]

    return combined

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cx_gen_stmt.py <sourcefile.py>")
        sys.exit(1)

    filename = sys.argv[1]
    real = load_json_file(derive_filename(filename, "stmts", "real"))
    synth = load_json_file(derive_filename(filename, "stmts", "synth"))
    headers = load_json_file(derive_filename(filename, "stmts", "head"))

    full_stmt_list = cx_gen_stmts(real, synth, headers)
    output_filename = derive_filename(filename, "stmts")
    write_json_file(full_stmt_list, output_filename)
    print(f"Wrote {len(full_stmt_list)} statements to {output_filename}")
