import ast
import sys
from cx_utils import read_source_file
from cx_errors import CxParseError

def cx_chk_ast(source_code):
    """
    Validates that the source code is syntactically correct by attempting to parse it with ast.
    Returns an empty list if no error, otherwise returns a list with one CXError.
    """
    try:
        tree = ast.parse(source_code)
        return tree, []
    except SyntaxError as e:
        # Construct a CXError with useful info
        err = CxParseError("SyntaxError", e.msg,
            line=e.lineno or 0,
            col=e.offset or 0,
            severity="error"
        )
        return None, [err]

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python cx_chk_ast.py <filename.py>")
        sys.exit(1)

    filename = sys.argv[1]
    try:
        source_code = read_source_file(filename)
    except Exception as e:
        print(f"Error reading file: {e}")
        exit(1)

    tree, errors = cx_chk_ast(source_code)
    if errors:
        for err in errors:
            print(f"{err.severity.upper()}: {err.errtype} at line {err.line}, col {err.col}: {err.message}")
        exit(1)
    else:
        print("No syntax errors found.")
        exit(0)
