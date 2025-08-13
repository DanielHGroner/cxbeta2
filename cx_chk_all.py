# cx_chk_all.py

import sys
from cx_utils import read_source_file
from cx_chk_ast import cx_chk_ast
from cx_chk_1stmt import cx_chk_1stmt
from cx_errors import CxError


def cx_chk_all(source_code: str) -> list[CxError]:
    # Step 1: AST check
    tree, errors = cx_chk_ast(source_code)
    if errors:
        return errors

    # Step 2: Multi-statement line check
    errors = cx_chk_1stmt(tree)
    if errors:
        return errors

    # All checks passed
    return []


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cx_chk_all.py <source_file.py>")
        exit(1)

    source_path = sys.argv[1]
    source_code = read_source_file(source_path)
    errors = cx_chk_all(source_code)

    if errors:
        print(f"Validation failed for: {source_path}")
        for err in errors:
            print(f"{err.__class__.__name__} at line {err.line}, col {err.col}: {err.message}")
        exit(1)
    else:
        print(f"No errors found in {source_path}.")
        exit(0)
