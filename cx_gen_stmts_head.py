import sys
from cx_utils import read_source_file, derive_filename, write_json_file, load_json_file, get_token_stream
import tokenize

#def find_colon_after_start(tokens, start_line, start_col):
#    for tok in tokens:
#        if tok.start[0] == start_line and tok.start[1] >= start_col:
#            if tok.type == tokenize.OP and tok.string == ":":
#                return {"line": tok.start[0], "col": tok.start[1]}
#    return None
# revised 8/31/25 to replace above, to handle multi-line signatures
def find_colon_after_start(tokens, start_line, start_col):
    """Return (line,col) of the header-terminating ':' after (start_line,start_col).
    Handles multi-line headers and ignores colons inside (), [], {}."""
    started = False
    depth = 0  # bracket depth across () [] {}
    for tok in tokens:
        # wait until we reach the starting position
        if not started:
            if tok.start < (start_line, start_col):
                continue
            started = True
        tt, ts = tok.type, tok.string
        # skip non-structural tokens
        if tt in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT):
            continue
        if tt == tokenize.STRING:
            continue
        if tt == tokenize.OP:
            if ts in "([{":
                depth += 1
                continue
            if ts in ")]}":
                if depth > 0:
                    depth -= 1
                continue
            if ts == ":" and depth == 0:
                return {"line": tok.start[0], "col": tok.start[1]+1} # patch 9/3/25 - +1 , sto include the colon in stmt span
    return None

def cx_gen_stmts_head(tokens, stmt_real, stmt_synth):
    all_stmts = stmt_real + stmt_synth
    result = []
    for stmt in all_stmts:
        if stmt.get("is_compound"):
            start = stmt["start"]
            end_header = find_colon_after_start(tokens, start["line"], start["col"])
            if end_header:
                result.append({
                    "start": start,
                    "end_header": end_header
                })
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cx_gen_stmts_head.py <sourcefile.py>")
        sys.exit(1)

    filename = sys.argv[1]
    source_code = read_source_file(filename)
    real = load_json_file(derive_filename(filename, "stmts", "real"))
    synth = load_json_file(derive_filename(filename, "stmts", "synth"))

    tokens = get_token_stream(source_code) # get tokens from source

    headers = cx_gen_stmts_head(tokens, real, synth) # create header elements

    output_filename = derive_filename(filename, "stmts", "head")
    write_json_file(headers, output_filename)
    print(f"Wrote {len(headers)} statement headers info to {output_filename}")
