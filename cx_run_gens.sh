#!/bin/bash

# Run all the cx generators in batch, for testing, to generatoe HTML from ex source code
# Usage: ./cx_run_gens.sh example.py

if [ $# -ne 1 ]; then
  echo "Usage: $0 <source_file.py>"
  exit 1
fi

SOURCE=$1
BASE="${SOURCE%.py}"

# Check if the file exists and is a regular file
if [ ! -f "$SOURCE" ]; then
    echo "Error: File '$SOURCE' not found."
    exit 1
fi

echo "Running generators for $SOURCE..."

python cx_gen_tokens_core.py "$SOURCE"
python cx_gen_tokens_name.py "$SOURCE"

python cx_gen_stmts_real.py "$SOURCE"
python cx_gen_stmts_synth.py "$SOURCE"
python cx_gen_stmts_head.py "$SOURCE"
python cx_gen_stmts.py "$SOURCE"

python cx_gen_actions_var.py "$SOURCE"
python cx_gen_actions_io.py "$SOURCE"

python cx_gen_flows_call.py "$SOURCE"
python cx_gen_flows_loopback.py "$SOURCE"
# Retired:
#python cx_gen_flows_cond.py "$SOURCE"

python cx_gen_flows_return_explicit.py "$SOURCE"
python cx_gen_flows_return_implicit.py "$SOURCE"
python cx_gen_combine.py "${BASE}.flows_return_from.json" "${BASE}.flows_return_explicit.json" "${BASE}.flows_return_implicit.json"
# temporary, retired:
#cp "${BASE}.flows_return_explicit.json" "${BASE}.flows_return_from.json"
python cx_gen_flows_return.py "$SOURCE"

python cx_gen_flows_endif.py "$SOURCE"
python cx_gen_flows_loop.py "$SOURCE"
python cx_gen_flows_if.py "$SOURCE"
python cx_gen_flows_break.py "$SOURCE"

# New - consolidate all flow items
python cx_gen_flows_all.py "$SOURCE"

python cx_gen_allhilites.py "$SOURCE"

# TODO: superceded by cx_gen_flows_all.py - can remove
python cx_gen_allarrows.py "$SOURCE"

python cx_gen_html.py "$SOURCE"

echo "✅ All generators completed for $SOURCE"
