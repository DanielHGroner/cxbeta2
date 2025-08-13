import sys
import os
from cx_utils import read_source_file, parse_ast, derive_basename
from cx_errors import CxParseError

# cfg support
from cx_cfg6 import CFGManager

# Import top-level functions from each generator
from cx_gen_tokens_core import cx_gen_tokens_core
from cx_gen_tokens_name import cx_gen_tokens_name
from cx_gen_stmts_real import cx_gen_stmts_real
from cx_gen_stmts_synth import cx_gen_stmts_synth
from cx_gen_stmts_head import cx_gen_stmts_head
from cx_gen_stmts import cx_gen_stmts
from cx_gen_actions_var import cx_gen_actions_var
from cx_gen_actions_io import cx_gen_actions_io
from cx_gen_flows_call import cx_gen_flows_call
from cx_gen_flows_loopback import cx_gen_flows_loopback
from cx_gen_flows_return_explicit import cx_gen_flows_return_explicit
from cx_gen_flows_return_implicit import cx_gen_flows_return_implicit
#from cx_gen_combine import cx_gen_combine
from cx_gen_flows_return import cx_gen_flows_return
from cx_gen_flows_endif import cx_gen_flows_endif
from cx_gen_flows_loop import cx_gen_flows_loop
from cx_gen_flows_if import cx_gen_flows_if
from cx_gen_flows_break import cx_gen_flows_break
from cx_gen_allhilites import cx_gen_allhilites
from cx_gen_allarrows import cx_gen_allarrows
from cx_gen_html import cx_gen_html

def print_status(name, items=None):
    if isinstance(items, list):
        count = len(items)
        print(f'Generated {count} {name}.')
    elif isinstance(items, dict):
        count = sum(len(v) for v in items.values())
        print(f'Generated {count} {name}.')
    else:
        print(f'Generated {name}.')

def cx_gen_src2html(source_code, filename='CodeXplorer'):
    print('Entering cx_gen_src2html()')
    print(source_code)

    # === The basics: ast tree and cfg graph ===

    # the ast tree
    try:
       print('calling parse_ast()')
       tree = parse_ast(source_code) #, filename=source_path)
       print('after calling parse_ast()')
    except Exception as e:
        print('Exception during call of parse_ast()')
        # Construct a CxError with useful info
        err = CxParseError("SyntaxError", e.msg,
            line=e.lineno or 0,
            col=e.offset or 0,
            severity="error"
        )
        raise err
    except Exception as e:
    # Catch-all fallback in case it's not a SyntaxError (e.g., internal failure)
        print('Exception during call of parse_ast()')
        raise CxParseError("InternalError",str(e),
            severity="fatal"
        ) from e

    print_status('tree')
    #print(tree)

    # create the cfgs
    cfg_mgr = CFGManager()
    cfg_mgr.load_from_ast(tree, source_code)
    print_status('cfg_mgr')
    #print(cfg_mgr)

    # === Tokenization ===
    tokens_core, tokens_from_tokenizer = cx_gen_tokens_core(source_code)
    print_status('tokens_core', tokens_core)
    tokens = cx_gen_tokens_name(tokens_core, tree)
    print_status('tokens_name', tokens)

    # === Statements ===
    stmts_real = cx_gen_stmts_real(tree)
    print_status('stmts_real', stmts_real)
    stmts_synth = cx_gen_stmts_synth(tokens_from_tokenizer)
    print_status('stmts_synth', stmts_synth)
    stmts_head = cx_gen_stmts_head(tokens_from_tokenizer, stmts_real, stmts_synth)
    print_status('stmts_head', stmts_head)
    stmts = cx_gen_stmts(stmts_real, stmts_synth, stmts_head)
    print_status('stmts', stmts)
    #print(stmts)

    # === Actions ===
    actions_var = cx_gen_actions_var(tree, tokens, stmts)
    print_status('actions_var', actions_var)
    actions_io  = cx_gen_actions_io(tree, tokens, stmts)
    print_status('actions_io', actions_io)
    
    # === Flows ===
    flows_call = cx_gen_flows_call(tree, stmts)
    print_status('flows_call', flows_call)
    flows_loopback = cx_gen_flows_loopback(tree)
    print_status('flows_loopback', flows_loopback)
    flows_return_explicit = cx_gen_flows_return_explicit(tree)
    print_status('flows_return_explicit', flows_return_explicit)
    flows_return_implicit = cx_gen_flows_return_implicit(cfg_mgr)
    print_status('flows_return_implicit', flows_return_implicit)
    flows_return_from = flows_return_explicit + flows_return_implicit
    print_status('flows_return_from', flows_return_from)
    flows_return = cx_gen_flows_return(flows_return_from, flows_call)
    print_status('flows_return', flows_return)
    flows_endif = cx_gen_flows_endif(cfg_mgr)
    print_status('flows_endif', flows_endif)
    flows_loop = cx_gen_flows_loop(cfg_mgr)
    print_status('flows_loop', flows_loop)
    flows_if = cx_gen_flows_if(cfg_mgr)
    print_status('flows_if', flows_if)
    flows_break = cx_gen_flows_break(cfg_mgr)
    print_status('flows_break', flows_break)

    # === Variables for html ===
    allhilites = cx_gen_allhilites(actions_var, actions_io)
    print_status('allhilites', allhilites)    
    allarrows = cx_gen_allarrows(
        flows_call,
        flows_return,
        flows_loopback,
        flows_endif,
        flows_break,
        flows_if,
        flows_loop
    )
    print_status('allarrows', allarrows)
    html_output = cx_gen_html(filename, tokens, stmts, actions_var, allhilites, allarrows)
    print_status('html_output')

    return html_output


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_src2html.py <source.py>")
        sys.exit(1)

    source_path = sys.argv[1]
    source_code = read_source_file(source_path)

    try:
       html_output = cx_gen_src2html(source_code, filename=source_path)
       #print(html_output)
    except Exception as e:
        print('Error during cx_gen_src2html()')
        print(e)
        exit(1)

    base = derive_basename(source_path)
    output_dir = os.path.join(os.path.dirname(base), "html")
    out_file = os.path.join(output_dir, f"{os.path.basename(base)}.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"Wrote HTML to {out_file}")
