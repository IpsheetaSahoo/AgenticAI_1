#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo ">> Generating plan.json ..."
$PYTHON_BIN -u main.py

echo ">> Validating with JSON Schema via validator.py ..."
$PYTHON_BIN -u validator.py plan.json output_schema.json
echo "All good. Artifacts: plan.json, top3.json"