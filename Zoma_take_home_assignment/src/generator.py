from __future__ import annotations
import math
from typing import List, Dict, Any
import json
import re

def _allocate_days(total_days: int, weights: List[float]) -> List[int]:
    """Allocate total_days across buckets by weights, rounding and fixing drift deterministically."""
    total_w = sum(weights) or 1.0
    raw = [total_days * (w / total_w) for w in weights]
    days = [max(1, int(round(x))) for x in raw]
    # Fix sum drift
    diff = total_days - sum(days)
    # Deterministically adjust from largest fractional part
    fracs = [(i, raw[i] - int(round(raw[i]))) for i in range(len(raw))]
    fracs.sort(key=lambda t: (abs(t[1]), -t[0]), reverse=True)
    i = 0
    while diff != 0 and len(fracs) > 0:
        idx = fracs[i % len(fracs)][0]
        days[idx] += 1 if diff > 0 else -1
        if days[idx] < 1: days[idx] = 1
        diff = total_days - sum(days)
        i += 1
    return days

def _safe_phase_id(n: int) -> str:
    return f"PH-{n:03d}"

def generate_plan(new_opp: Dict[str, Any], top3: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Deterministic "mock LLM" that creates a compliant plan calibrated by similar opportunities."""
    # Weighted average effort from top3 to calibrate
    num = sum(t['relevance_score'] * t['estimated_effort_hours'] for t in top3) or 1.0
    den = sum(t['relevance_score'] for t in top3) or 1.0
    avg_hours = num / den

    # Convert to calendar days; assume ~8 productive hours/day with some parallelism (factor 1.3)
    base_days = max(10, int(math.ceil((avg_hours / 8.0) / 1.3)))
    # Cap to reasonable project size for this scope
    total_days = min(max(base_days, 18), 45)

    # Weights by scope components present in new opportunity
    comps = [c.lower() for c in (new_opp.get("required_components") or [])]
    # Ensure phases cover the required components + guardrails
    phase_defs = [
        ("Discovery & Requirements",    0.10),
        ("Salesforce Trigger & Data Mapping", 0.22),
        ("Docxtemplater Template & Merge",    0.24),
        ("Bottom-Up Estimation Table Integration", 0.16),
        ("Similarity Service for Calibration", 0.14),
        ("S3 Upload & Salesforce Linkback",   0.07),
        ("QA, Guardrails & UAT",        0.07),
    ]
    weights = [w for _, w in phase_defs]
    days_alloc = _allocate_days(total_days, weights)

    phases = []
    for idx, ((name, _w), d) in enumerate(zip(phase_defs, days_alloc), start=1):
        phases.append({
            "id": _safe_phase_id(idx),
            "name": name,
            "duration_days": int(max(1, min(60, d))),
            "dependencies": [_safe_phase_id(idx-1)] if idx > 1 else []
        })

    # Recompute total_days as sum since phases are sequential via dependencies
    total_duration_days = sum(p["duration_days"] for p in phases)

    # Compose concise notes (<= 2000 chars)
    top_ids = ", ".join([f"{t['id']} ({t['relevance_score']})" for t in top3])
    top_titles = "; ".join([t['title'] for t in top3])
    notes = (
        "Calibrated durations from top-3 similar opportunities "
        f"[{top_ids}]: {top_titles}. "
        "Weights emphasize overlapping components: Docxtemplater, Salesforce integration, vector similarity, "
        "and S3 linking. Phases are sequential to simplify dependency management; guardrails and UAT ensure "
        "strict JSON outputs and linkage integrity."
    )
    plan = {
        "opportunity_id": new_opp.get("id", ""),
        "phases": phases,
        "total_duration_days": int(total_duration_days),
        "notes": notes[:1900]
    }
    return plan

def harden_if_needed(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Make minor deterministic adjustments to satisfy the schema if needed (retry strategy)."""
    # Ensure phase ids unique and pattern
    seen = set()
    for i, p in enumerate(plan.get("phases", []), start=1):
        pid = p.get("id", "") or f"PH-{i:03d}"
        pid = pid if re.match(r"^PH-[0-9]{3}$", pid) else f"PH-{i:03d}"
        # Ensure uniqueness
        while pid in seen:
            i += 1
            pid = f"PH-{i:03d}"
        p["id"] = pid
        seen.add(pid)
        # Clamp duration
        d = int(p.get("duration_days", 1))
        p["duration_days"] = max(1, min(60, d))
        # Dependencies refer only to seen ids (DAG-like chain fallback)
        deps = [dep for dep in p.get("dependencies", []) if dep in seen]
        p["dependencies"] = list(dict.fromkeys(deps))  # unique
        if i > 1 and not p["dependencies"]:
            # ensure at least depends on previous
            prev = sorted(list(seen))[-2]
            p["dependencies"] = [prev]
    plan["total_duration_days"] = int(sum(p["duration_days"] for p in plan.get("phases", [])))
    plan["notes"] = str(plan.get("notes",""))[:1900]
    plan["opportunity_id"] = str(plan.get("opportunity_id",""))
    return plan