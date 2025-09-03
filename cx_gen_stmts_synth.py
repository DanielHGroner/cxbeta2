import sys
import tokenize

from cx_utils import read_source_file, derive_filename, write_json_file, get_token_stream

# Target keywords for synthetic statements
SYNTHETIC_KEYWORDS = {"elif", "else", "except", "finally"}

# new helper function 9/2/25 to discern else in terse if/else
def _colon_ahead_same_logical_line(toks, i):
    depth = 0
    j = i + 1
    while j < len(toks):
        tt, ts = toks[j].type, toks[j].string
        if tt == tokenize.NEWLINE:          # logical line ends: no colon
            return False
        if tt in (tokenize.NL, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT):
            j += 1; continue
        if tt == tokenize.STRING:
            j += 1; continue
        if tt == tokenize.OP:
            if ts in '([{': depth += 1
            elif ts in ')]}': depth = max(0, depth - 1)
            elif ts == ':' and depth == 0:
                return True
        j += 1
    return False

def cx_gen_stmts_synth(tokens):
    toks = list(tokens)  # need indexing for the tiny lookahead
    results = []
    #for tok in tokens:
    for i, tok in enumerate(toks): # patch 9/2/25 - switching to enumerate to have index and token for terse/else fix
        if tok.type == tokenize.NAME and tok.string in SYNTHETIC_KEYWORDS:
            # patch 9/2/25 - handle else in terse if/else - don't need synthetic statement for that
            if tok.string == 'else' and not _colon_ahead_same_logical_line(tokens, i):
                continue
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
