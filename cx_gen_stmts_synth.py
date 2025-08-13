import sys
from cx_utils import read_source_file, derive_filename, write_json_file, get_token_stream

# Target keywords for synthetic statements
SYNTHETIC_KEYWORDS = {"elif", "else", "except", "finally"}

def cx_gen_stmts_synth(tokens):
    import tokenize

    results = []
    for tok in tokens:
        if tok.type == tokenize.NAME and tok.string in SYNTHETIC_KEYWORDS:
            stmt = {
                "start": {"line": tok.start[0], "col": tok.start[1]},
                "end": {"line": tok.end[0], "col": tok.end[1]},
                "type": tok.string,
                "is_compound": True,  # These always introduce a block
                "is_synthetic": True
            }
            results.append(stmt)
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cx_gen_stmt_synth.py <sourcefile.py>")
        sys.exit(1)

    filename = sys.argv[1]
    source = read_source_file(filename)
    tokens = get_token_stream(source) # get tokens from source

    stmts = cx_gen_stmts_synth(tokens) # from tokens, generate synthetic statements

    output_filename = derive_filename(filename, "stmts", "synth")
    write_json_file(stmts, output_filename)
    print(f"Wrote {len(stmts)} statements to {output_filename}")
