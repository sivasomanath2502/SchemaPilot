# evaluation/evaluators/requirement_eval.py
"""
Metric B: Requirement Coverage.

Scores run_requirement_agent_full's structured output against a ground-truth
checklist per application scenario. Distinguishes "correctly identified"
from "correctly flagged as unstated/assumed" -- per the spec, both count
as correct; inventing a confident value for something not in the input
does not, even if the invented value happens to look plausible.
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "agents"))
from requirement_agent import run_requirement_agent

GROUND_TRUTH_PATH = Path(__file__).resolve().parent.parent / "requirement_ground_truth.json"


def _keyword_hit(text: str | None, keywords: list[str]) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _entity_coverage(actual_entities: list[str], expected_entities: list[str]) -> tuple[int, int]:
    actual_lower = [e.lower() for e in actual_entities]
    hits = 0
    for exp in expected_entities:
        exp_lower = exp.lower()
        if any(exp_lower in act or act in exp_lower for act in actual_lower):
            hits += 1
    return hits, len(expected_entities)


def _assumption_coverage(output_dict: dict, not_stated_fields: list[str]) -> tuple[int, int]:
    """A field in not_stated_fields is 'correctly handled' if EITHER:
    - its value is a known 'unstated' sentinel ('unknown', 'unstated', 'none identified'), OR
    - it appears in the assumptions list.
    Silently inventing a specific value with no assumption entry is a miss."""
    UNSTATED_SENTINELS = {"unknown", "unstated", "none identified", "none beyond standard crud"}
    assumed_fields = {a["field"] for a in output_dict.get("assumptions", [])}
    hits = 0
    for field in not_stated_fields:
        value = str(output_dict.get(field, "")).strip().lower()
        if value in UNSTATED_SENTINELS or field in assumed_fields:
            hits += 1
    return hits, len(not_stated_fields)


def score_scenario(app_key: str, ground_truth: dict) -> dict:
    output = run_requirement_agent(ground_truth["description"])
    output_dict = output.model_dump()

    entity_hits, entity_total = _entity_coverage(
        output_dict.get("entities", []), ground_truth["expected_entities"]
    )
    invariant_ok = _keyword_hit(
        output_dict.get("critical_invariant"), ground_truth["expected_critical_invariant_keywords"]
    )
    features_ok = _keyword_hit(
        " ".join(output_dict.get("features", [])), ground_truth["expected_features_keywords"]
    )
    assumption_hits, assumption_total = _assumption_coverage(
        output_dict, ground_truth["not_stated_should_be_flagged"]
    )

    total_checks = entity_total + 2 + assumption_total
    total_hits = entity_hits + int(invariant_ok) + int(features_ok) + assumption_hits

    return {
        "application": app_key,
        "coverage": round(total_hits / total_checks, 3) if total_checks else None,
        "entity_coverage": f"{entity_hits}/{entity_total}",
        "critical_invariant_correct": invariant_ok,
        "features_correct": features_ok,
        "not_stated_correctly_flagged": f"{assumption_hits}/{assumption_total}",
        "raw_output": output_dict,
    }


def run_requirement_coverage_eval() -> dict:
    ground_truth_data = json.loads(GROUND_TRUTH_PATH.read_text())
    results = []
    for i, (app_key, gt) in enumerate(ground_truth_data.items(), 1):
        print(f"[{i}/{len(ground_truth_data)}] evaluating: {app_key}")
        results.append(score_scenario(app_key, gt))

    avg_coverage = sum(r["coverage"] for r in results if r["coverage"] is not None) / len(results)
    return {"average_coverage": round(avg_coverage, 3), "per_application": results}


if __name__ == "__main__":
    result = run_requirement_coverage_eval()
    print(json.dumps(result, indent=2))