from __future__ import annotations
import json, os, subprocess, sys
from typing import Dict, Any

def validate_with_schema(plan: Dict[str, Any], schema_path: str) -> bool:
    """Try to validate using jsonschema if available; otherwise return True (defer to external validator)."""
    try:
        from jsonschema import Draft202012Validator
    except Exception:
        return True  # Defer to run.sh validator step
    with open(schema_path) as f:
        schema = json.load(f)
    v = Draft202012Validator(schema)
    errors = sorted(v.iter_errors(plan), key=lambda e: e.path)
    return len(errors) == 0