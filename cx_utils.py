import sys
import json
import tokenize
import token
import ast

def read_source_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def write_json_file(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def derive_output_filename(source_filename, list_name, variant=None, sep='_', filetype='json'):
    base = source_filename.rsplit('.', 1)[0]
    suffix = f".{list_name}"
    if variant:
        suffix += f"{sep}{variant}"
    return base + suffix + "." + filetype

# a better function name for above
def derive_filename(source_filename, list_name, variant=None, sep='_', filetype='json'):
    return derive_output_filename(source_filename, list_name, variant, sep, filetype)

# drop '.py' from the filename, to use as base for other filenmaes
def derive_basename(source_filename):
    return source_filename[:-3]

def parse_ast(source_code, filename="<unknown>"):
    #try:
        return ast.parse(source_code, filename=filename)
    #except SyntaxError as e:
        #print(f"Syntax error in file {filename}: {e}")
        #sys.exit(1)

def get_token_stream(source_code):
    from io import StringIO
    return list(tokenize.generate_tokens(StringIO(source_code).readline))

def location_dict(line, col):
    return {"line": line, "col": col}

def get_node_start(node):
    return location_dict(node.lineno, node.col_offset)

def get_node_end(node):
    end_line = getattr(node, 'end_lineno', node.lineno)
    end_col = getattr(node, 'end_col_offset', node.col_offset)
    return location_dict(end_line, end_col)

def get_node_range(node):
    return get_node_start(node), get_node_end(node)

def stmt_id(line, index=0):
    return float(f"{line}.{index}")
