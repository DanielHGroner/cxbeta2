# cx_gen_tokens_bs.py
from __future__ import annotations

import io
import json
import os
import sys
import tokenize
from typing import List, Dict

# fins the line-continue \ tokens in the source code (since the Python tokenizer skips these)
def cx_gen_tokens_bs(s: str) -> List[Dict]:
    """
    Return a list of dicts for each explicit line continuation backslash found.
    Each item: {"line": int, "col": int, "pre_ws": str}
      - line: 1-based physical line number containing the backslash
      - col:  0-based column index of the backslash on that line
      - pre_ws: the exact whitespace (spaces/tabs) immediately preceding the backslash
    Backslashes that occur inside STRING or COMMENT tokens are ignored.
    """
    lines = s.splitlines(keepends=True)  # preserve newlines per line
    nlines = len(lines)

    # Build per-line coverage ranges for STRING and COMMENT tokens so we can exclude \ inside them
    covered: List[List[tuple[int, int]]] = [[] for _ in range(nlines + 1)]  # 1-based index

    try:
        for tok in tokenize.generate_tokens(io.StringIO(s).readline):
            if tok.type not in (tokenize.STRING, tokenize.COMMENT):
                continue
            (srow, scol) = tok.start
            (erow, ecol) = tok.end
            for row in range(srow, erow + 1):
                if row == srow and row == erow:
                    start, end = scol, ecol
                elif row == srow:
                    start = scol
                    # up to end of this physical line (excluding newline chars)
                    end = len(lines[row - 1].rstrip("\r\n"))
                elif row == erow:
                    start, end = 0, ecol
                else:
                    start = 0
                    end = len(lines[row - 1].rstrip("\r\n"))
                covered[row].append((start, end))
    except tokenize.TokenError:
        # If tokenization fails (e.g., incomplete file), fall back to no exclusions
        covered = [[] for _ in range(nlines + 1)]

    results: List[Dict] = []

    for i, raw in enumerate(lines, start=1):
        # Remove only newline characters; preserve trailing spaces/tabs
        line_wo_nl = raw.rstrip("\r\n")

        if not line_wo_nl:
            continue

        # Must end with a backslash to be a candidate
        if not line_wo_nl.endswith("\\"):
            continue

        col = len(line_wo_nl) - 1  # position of the backslash (0-based)

        # Exclude if backslash is inside a STRING/COMMENT token coverage on this line
        is_covered = any(start <= col < end for (start, end) in covered[i])
        if is_covered:
            continue

        # Capture the exact whitespace immediately preceding the backslash
        j = col - 1
        while j >= 0 and line_wo_nl[j] in (" ", "\t"):
            j -= 1
        pre_ws = line_wo_nl[j + 1 : col]  # may be "" if no whitespace directly before "\"

        results.append({"line": i, "col": col, "pre_ws": pre_ws})

    # Sort for determinism
    results.sort(key=lambda d: (d["line"], d["col"]))
    return results


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python cx_gen_tokens_bs.py <example.py>", file=sys.stderr)
        sys.exit(2)

    src_path = sys.argv[1]
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            src = f.read()
    except OSError as e:
        print(f"error: cannot read {src_path}: {e}", file=sys.stderr)
        sys.exit(1)

    items = cx_gen_tokens_bs(src)

    base, _ = os.path.splitext(src_path)
    out_path = f"{base}.tokens_bs.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"error: cannot write {out_path}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {len(items)} tokens_bs entries to {out_path}")
