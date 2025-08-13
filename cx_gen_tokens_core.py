import sys
import tokenize
import keyword
from io import BytesIO
from cx_utils import derive_filename, write_json_file, read_source_file

def cx_gen_tokens_core(source_code):
    token_list = []
    tokens = []
    g = tokenize.tokenize(BytesIO(source_code.encode('utf-8')).readline)
    for token in g:
        tokens.append(token)
        if token.type == tokenize.ENCODING or token.type == tokenize.ENDMARKER:
            continue
        tok_info = {
            "start": {"line": token.start[0], "col": token.start[1]},
            "end": {"line": token.end[0], "col": token.end[1]},
            "text": token.string,
            "type": tokenize.tok_name[token.type]
        }
        # vary from tokenizer - we can recognize keywords here
        if keyword.iskeyword(tok_info["text"]):
            tok_info["type"] = "NAME_KEYWORD" # this is not a pure tokenizer type
        token_list.append(tok_info)
    return token_list, tokens

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cx_gen_tokens_core.py <sourcefile.py>")
        sys.exit(1)

    filename = sys.argv[1]
    source = read_source_file(filename)
    token_list, tokens = cx_gen_tokens_core(source)
    output_filename = derive_filename(filename, "tokens","core", sep='_')
    write_json_file(token_list, output_filename)
    print(f"Wrote {len(token_list)} tokens to {output_filename}")
    #print(tokens)
