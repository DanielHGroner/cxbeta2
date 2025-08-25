import sys
import os
import json
from cx_utils import load_json_file, derive_basename


# Token types to CSS classes
TOKEN_CLASSES = {
    "COMMENT": "cx-com",
    "NAME_KEYWORD": "cx-key",
    "NAME": {
        "variable": "cx-var",
        "parameter": "cx-var",
        "function": "cx-fun",
        "method": "cx-fun",
        "function_call": "cx-fun",
        "function_def": "cx-fun"
    },
    "NUMBER": "cx-num",
    "STRING": "cx-str"
}

def trim_blank_end_lines(lines):
    """Remove trailing lines that are entirely empty (whitespace or '')"""
    while lines and lines[-1].strip() == "":
        lines.pop()
    return lines

def remove_newline_end(line):
    """Remove trailing newline character from the final HTML code string"""
    if line.endswith("\n"):
        return line[:-1]
    return line


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_token_class(tok):
    ttype = tok["type"]
    tname = tok.get("type_name")

    if ttype == "NAME":
        return TOKEN_CLASSES.get(ttype, {}).get(tname)
    return TOKEN_CLASSES.get(ttype)


def wrap_token(tok):
    text = escape_html(tok["text"])
    cls = get_token_class(tok)
    if cls:
        return f'<span class="{cls}">{text}</span>'
    return text


def build_statement_map(stmt_list):
    stmt_map = {}  # (line, col) -> stmt_id
    for stmt in stmt_list:
        stmt_id = stmt['start']['line'] # stmt["id"]
        start = (stmt["start"]["line"], stmt["start"]["col"])
        endattr = "end_header" if "end_header" in stmt else "end" # choose from "end" or "end_header"
        end = (stmt[endattr]["line"], stmt[endattr]["col"])
        stmt_map[start] = {"id": stmt_id, "start": True}
        stmt_map[end] = {"id": stmt_id, "end": True}
    return stmt_map


def generate_code_section(tokens, stmt_list):
    stmt_map = build_statement_map(stmt_list)
    output_lines = []

    grouped_tokens = {}
    for tok in tokens:
        grouped_tokens.setdefault(tok["start"]["line"], []).append(tok)

    # for wrapping physical lines, we need to track if there is an open (in-progress) multi-line statement
    stmt_level = 0

    max_line = max(grouped_tokens.keys(), default=0)
    for line in range(1, max_line + 1):
        line_tokens = grouped_tokens.get(line, [])
        col = 0
        line_fragments = []

        # new for wrapping each physical line
        if stmt_level == 0:
           line_fragments.append(f'<span class="cx_srcline" id="{line}s">')

        for tok in line_tokens:
            if not tok["text"]: # skip over empty tokens like DEDENT, EOF
                continue
            tok_start_col = tok["start"]["col"]
            if tok_start_col > col:
                line_fragments.append(" " * (tok_start_col - col))

            coord = (line, tok_start_col)
            if coord in stmt_map and stmt_map[coord].get("start"):
                stmt_id = stmt_map[coord]["id"]
                line_fragments.append(f'<span class="cx-statement cx-hilitable help-span" id="{stmt_id}">')
                stmt_level += 1

            line_fragments.append(wrap_token(tok))

            tok_end_col = tok["end"]["col"]
            col = tok_end_col

            coord_end = (line, tok_end_col)
            if coord_end in stmt_map and stmt_map[coord_end].get("end"):
                line_fragments.append('</span>')
                stmt_level -=1

        # new for wrapping each physical line
        # the assumption is we want the \n to be inside the closing </span>, so just append the </span>
        # also we can interupt a statement span in progress, so conditionally close line span if no open stmt span
        if stmt_level == 0:
            line_fragments.append('</span>')

        output_lines.append(''.join(line_fragments))

    trim_blank_end_lines(output_lines)
    code_html = ''.join(output_lines)
    code_html = remove_newline_end(code_html)
    return code_html

def generate_help_choice_html():
    return \
    """
        <!-- Button + Toggle Row -->
        <div class="button-row inline-row" style="margin-top: 1em;">
            <input type="checkbox" id="help-toggle" title="display help for CodeXplorer" checked> <span style="margin-right:35px; font-size: 80%;">Show Help</span>
            <label><input type="checkbox" id="showSettings" onchange="toggleSettings()"><span style="font-size: 80%; margin-right:32px;">Show Help Settings</span></label>
            <button id="aihelp-button" onclick="fetchAndSetAiHelp()" class='cx-button' >💡 Get AI Help</button>
            <span id="aihelp-status" style="margin-left: 1em; font-style: italic;"></span>
        </div>

        <!-- Hidden Settings Row 1 -->
        <div id="ai-settings" class="inline-row" style="margin-top:1em; font-size: 80%;">
            <label>Language:&nbsp;</label><input type="text" id="aihelp-language" value="english" style="margin-right: 1.5em;">

            <label for="aihelp-apikeyInput" onclick="toggle_ai_settings2()">Gemini API Key:&nbsp;</label>
            <input type="text" id="aihelp-apikeyInput" placeholder="Enter Gemini API Key" size="45" style="margin-right:5px" />
            <button onclick="saveGeminiKey()" style="margin-right: 1.5em;">💾 Save Key</button>
        </div>
        <!-- Hidden Settings Row 2 -->
        <div id="ai-settings2" class="inline-row" style="margin-top:1em; font-size: 80%; display: none">
            <label>Provider: 
                <select id="aihelp-provider">
                    <option value="gemini">gemini</option>
                    <option value="dummy">dummy</option>
                </select>
            </label>
            <label style="margin-left:1.5em;">Model:&nbsp;</label><input type="text" id="aihelp-modelName" value="gemini-2.5-flash-lite" style="margin-right: 1.5em;">
            <input type="checkbox" id="aihelp-includeLong" checked><label style="margin-right: 1.5em;">Long&nbsp;Help</label>
            <input type="checkbox" id="aihelp-dryrun"><label style="margin-right: 1.5em;">Dry&nbsp;Run</label>
            <label>Help host:&nbsp;</label><input type="text" id="aihelp-host" value="DanielGroner.pythonanywhere.com" size="34" style="margin-right: 1.5em;">            
        </div>
    """

def generate_variable_section(var_data):
    """
    Generates the HTML for the variable section based on var_actions.json.
    Preserves scope and variable ordering. Includes <none> placeholder for empty scopes.
    """
    lines = []
    lines.append('<span class="cx-varheading">VARIABLES:</span><p><code>')

    scopes = list(var_data.keys())
    show_global_label = not (len(scopes) == 1 and "<global>" in scopes)

    for scope in scopes:
        actions = var_data[scope]
        seen_vars = set()
        ordered_vars = []

        for action in actions:
            var = action["var"]
            if var not in seen_vars:
                seen_vars.add(var)
                ordered_vars.append(var)

        # Add scope label, unless it's <global> and we want to suppress it
        if scope != "<global>" or show_global_label:
            label = "&nbsp;<u>{}</u>:".format(scope if scope != "<global>" else "global")
            lines.append(label)

        lines.append("<table>")
        if ordered_vars:
            for var in ordered_vars:
                full_id = f"{scope}.{var}" if scope != "<global>" else var
                lines.append(
                    f'<tr><td></td><td></td><td><span id="{full_id}" class="cx-var cx-hilitable help-span">{var}</span></td></tr>'
                )
        else:
            lines.append('<tr><td></td><td></td><td>&lt;none&gt;</td></tr>')
        lines.append("</table><p>")

    return "\n".join(lines)

def generate_html(title, code_html, var_html, allhilites, allarrows, allflows, allscopes):
    full_html = f"""<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <link rel="stylesheet" href="static/css/cxbase.css">
        <link rel="stylesheet" href="static/css/cxcopy.css">
        <link rel="stylesheet" href="static/css/cxhelp.css">
        <link rel="stylesheet" href="static/css/cxhilite.css">
        <link rel="stylesheet" href="static/css/cxlayout.css">
        <link rel="stylesheet" href="static/css/cxlinenums.css">
        <link rel="stylesheet" href="static/css/cxcollapse.css">
    </head>
    <body>
        <header><span id="-title" class="help-span"><b>{title} - Static Visualizer</b></span></header>
        <div id="help-container"></div>
        <div id="copy-message">Code copied to clipboard</div>
        <div class="container">
<section class="left">
<div class="linenums-and-code">
<div id="line-numbers-container"></div>
<pre><code id="code">{code_html}</code></pre>
</div>
<br>
<input type="checkbox" id="toggle-line-numbers" title="show/hide line numbers"><span id='toggle-line-numbers-text' style="margin-right:25px">Show Line #s</span> 
<button id="copy-button" class='cx-button' style="margin-right:20px" title="copy code to clipboard">⧉ Copy to Clipboard</button>
<button id="editCodeBtn" class='cx-button' style="margin-right:20px" >✏️ Edit Code&nbsp;&nbsp;</button>
<button id="newCodeBtn" class='cx-button' >📄 New Code&nbsp;&nbsp;</button>
<!--input type="checkbox" id="help-toggle" title="display help for CodeXplorer" checked-->
{generate_help_choice_html()}
</section>
<section class="right">
{var_html}
<span class="cx-varheading">INPUT / OUTPUT:</span><p>
<code><table>    
<tr><td></td><td><img src="static/png/console-display.png"/></td><td><span id="-display" class="cx-hilitable help-span">[display]</span></td></tr>
<tr><td></td><td><img src="static/png/console-keyboard.png"/></td><td><span id="-keyboard" class="cx-hilitable help-span">[keyboard]</span></td></tr>
</table></code>    
</section>
</div>
<span id='-deselect' class='cx-hilitable help-span'></span>
<svg id="svgElem"></svg>
        <footer id="footer">
            <!-- when ready, add back label below for show help-->
            <!--input type="checkbox" id="help-toggle" title="display help for CodeXplorer" checked-->
            <span id="logo">Code<span style="color:green"><i>Xplorer</i></span></span>
            <span id="copyright">(c) 2025 Rose River Software, LLC</span> &nbsp;&nbsp;&nbsp;
            <a href="static/pages/cx-terms.html" target="_blank" title="display Terms of Use for CodeXplorer">Terms of Use</a>&nbsp;&nbsp;&nbsp;
            <a href="static/docs/cx-help.pdf" target="_blank" title="display Overview for CodeXplorer">Overview</a>
        </footer>
        <script src="static/js/cxcopy.js"></script>
        <script src="static/js/cxhelp.js" defer></script>
        <script src="static/js/cxaihelp.js"></script>
        <script src="static/js/cxaihelpcb.js"></script>
        <script src="static/js/cxaihelpkey.js"></script>
        <script src="static/js/cxhilite.js"></script>
        <script src="static/js/cxhide.js"></script>

        <script src="static/js/cxarrows.js"></script>
        <script src="static/js/cxarrowcbnew.js" defer></script>

        <script src="static/js/cxlinenums.js"></script>

        <script src="static/js/cxcollapse.js" defer></script>

        <script src="static/js/cxcentral.js"></script>
        
        <script>
            let allhelp = {{ }};
            const allhilite2 = {json.dumps(allhilites, indent=2)};
            const allhilite3 = {{ }};
            const allarrows = {json.dumps(allarrows, indent=2)};
            const allflows = {json.dumps(allflows, indent=2)};
            const allscopes = {json.dumps(allscopes, indent=2)};
        </script>      
        <script>
            const lineNumbers = new LineNumbers('line-numbers-container', 'code', false, 'toggle-line-numbers');
        </script>        
        <script>
            document.getElementById('editCodeBtn').addEventListener('click', () => {{
                window.location.href = '/';
            }});

            function toggleSettings() {{
                const show = document.getElementById("showSettings").checked;
                document.getElementById("ai-settings").style.display = show ? "flex" : "none";
                if (!show) document.getElementById("ai-settings2").style.display = "none";
            }}
            window.onload = () => {{
                toggleSettings();  // Will hide or show based on checkbox default
            }};
            function toggle_ai_settings2() {{
                console.log('In toggle_ai_settings2()');
                elem = document.getElementById("ai-settings2");
                if (elem.style.display == "none") elem.style.display = "flex";
                else elem.style.display = "none";
            }};
        </script>
        <script defer>
        document.getElementById('newCodeBtn').addEventListener('click', () => {{
            // Optional safety net:
            if (!confirm('Start a new program? This will clear the editor.')) return;
            sessionStorage.setItem('cxSourceCode', '');   // blank program
            window.location.href = '/';                   // go to editor (same tab), including access to sessionStorage
        }});
        </script>
        
    </body>
</html>"""
    return full_html

def cx_gen_html(py_filename, tokens, stmt_list, var_actions, allhilites, allarrows, allflows, allscopes):
    code_html_output = generate_code_section(tokens, stmt_list)
    var_html_output = generate_variable_section(var_actions)
    html_output = generate_html(py_filename, code_html_output, var_html_output, allhilites, allarrows, allflows, allscopes)
    return html_output


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cx_gen_html.py example.py")
        sys.exit(1)

    py_filename = sys.argv[1]
    base = derive_basename(py_filename)

    tokens = load_json_file(f"{base}.tokens.json")
    stmt_list = load_json_file(f"{base}.stmts.json")
    var_actions = load_json_file(f"{base}.actions_var.json")
    allhilites = load_json_file(f"{base}.allhilites.json")
    #print(allhilites)
    allarrows = load_json_file(f"{base}.allarrows.json")
    #print(allarrows)
    allflows = load_json_file(f"{base}.flows_all.json")
    #print(allflows)
    allscopes = load_json_file(f"{base}.scopes.json")
    #print(allscopes)

    html_output = cx_gen_html(py_filename, tokens, stmt_list, var_actions, allhilites, allarrows, allflows, allscopes)

    output_dir = os.path.join(os.path.dirname(base), "html")
    os.makedirs(output_dir, exist_ok=True)

    out_file = os.path.join(output_dir, f"{os.path.basename(base)}.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"Wrote HTML to {out_file}")
