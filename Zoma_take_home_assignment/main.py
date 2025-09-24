#!/usr/bin/env python3
from __future__ import annotations
import json, sys, os
from typing import Any, Dict
from src.similarity import load_dataset, load_new_opportunity, hybrid_similarity
from src.generator import generate_plan, harden_if_needed
from src.validation import validate_with_schema

DATASET_PATH = "dataset.json"
NEW_OPP_PATH = "new_opportunity.json"
SCHEMA_PATH = "output_schema.json"
PLAN_PATH = "plan.json"
TOP3_PATH = "top3.json"

def main() -> int:
    dataset = load_dataset(DATASET_PATH)
    new_opp = load_new_opportunity(NEW_OPP_PATH)
    top3 = hybrid_similarity(dataset, new_opp)

    # Persist top3 (exactly 3 items with id, title, relevance score)
    export_top3 = [{"id": t["id"], "title": t["title"], "relevance_score": t["relevance_score"]} for t in top3]
    with open(TOP3_PATH, "w") as f:
        json.dump(export_top3, f, indent=2)
    print("Top-3 similar opportunities:")
    print(json.dumps(export_top3, indent=2))

    # Generation with up to 3 attempts (guardrails on retries)
    attempts = 0
    max_attempts = 3
    plan: Dict[str, Any] = {}
    while attempts < max_attempts:
        attempts += 1
        if attempts == 1:
            plan = generate_plan(new_opp, top3)
        else:
            plan = harden_if_needed(plan)
        ok = validate_with_schema(plan, SCHEMA_PATH)
        if ok:
            break

    with open(PLAN_PATH, "w") as f:
        json.dump(plan, f, indent=2)

    # Print a summary
    print(f"\nWrote {PLAN_PATH} and {TOP3_PATH}. Attempts: {attempts}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())