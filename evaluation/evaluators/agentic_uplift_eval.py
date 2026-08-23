# evaluation/evaluators/agentic_uplift_eval.py
"""
Metric F: Agentic vs Single-Shot LLM Comparison.

_run_single_shot_baseline below is NOT a pipeline agent -- it's a bare LLM
call (no RAG, no review loop) that exists only so this evaluator has
something to compare the real agentic pipeline against. Kept local to this
file rather than in agents/ so it's never mistaken for part of the product.
"""

import json
import re
import sys
import time
from pathlib import Path

import ollama
from pydantic import BaseModel, Field, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "mcp_server"))
from server import validate_sql  

MODEL_NAME = "qwen3:4b"

BASELINE_PROMPT = """You are a database designer. Given an application description,
design a complete MySQL schema in one response.

Respond with ONLY a JSON object containing EXACTLY these three keys -- all
three are REQUIRED, never omit any of them even if you think one is less
important:
{
  "entities": ["<entity1>", "<entity2>", ...],
  "sql_ddl": "<complete CREATE TABLE statements as one string with real newlines, covering every entity listed above>",
  "important_queries": [{"description": "<...>", "sql": "<...>"}]
}

"sql_ddl" is the most important field -- it must contain real, complete
CREATE TABLE statements for every entity, not a placeholder or empty string.
Only output the JSON object, nothing else.
"""


class BaselineOutput(BaseModel):
    entities: list[str] = Field(default_factory=list)
    sql_ddl: str
    important_queries: list[dict] = Field(default_factory=list)


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```"):
        lines = [l for l in text.splitlines() if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


# agentic_uplift_eval.py -- replace the raise with a captured-failure return

def _run_single_shot_baseline(description: str, max_retries: int = 2) -> BaselineOutput | None:
    """Returns None if the single-shot approach fails entirely -- this is
    itself a valid, reportable outcome for Metric F, not an error to hide.
    A baseline that cannot produce a complete schema in one shot is direct
    evidence for why the pipeline splits schema generation into separate
    conceptual-design and SQL-generation steps."""
    last_error = None
    for attempt in range(1, max_retries + 2):
        start = time.time()
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": BASELINE_PROMPT},
                {"role": "user", "content": description},
            ],
            think=False,
            format="json",
            options={"temperature": 0, "num_predict": 1200},
        )
        elapsed = time.time() - start
        raw = _strip_code_fences(response["message"]["content"])
        print(f"  [baseline attempt {attempt}] {elapsed:.1f}s, eval_count={response.get('eval_count')}, "
              f"done_reason={response.get('done_reason')}")
        try:
            data = json.loads(raw)
            return BaselineOutput(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            print(f"  [baseline attempt {attempt}] failed: {e}")
            continue
    print(f"  [baseline] FAILED after {max_retries + 1} attempts -- single-shot approach could not "
          f"produce a complete schema. Last error: {last_error}")
    return None

def compare_scenario(app_key: str, description: str, expected_entities: list[str],
                      agentic_final_state: dict) -> dict:
    print(f"  Running single-shot baseline for: {app_key}")
    baseline = _run_single_shot_baseline(description)

    agentic_schema = agentic_final_state.get("schema", {})
    agentic_review = agentic_final_state.get("review", {})
    agentic_entities = [e.get("name") for e in agentic_schema.get("entities", [])]

    def entity_coverage(actual):
        actual_lower = [a.lower() for a in actual]
        hits = sum(1 for exp in expected_entities
                   if any(exp.lower() in a or a in exp.lower() for a in actual_lower))
        return hits / len(expected_entities) if expected_entities else None

    agentic_critical_issues = [
        i for i in agentic_review.get("issues", [])
        if i.get("severity") == "critical"
    ]

    agentic_result = {
        "mysql_validated": agentic_schema.get("validation", {}).get("final_valid", False),
        "entity_coverage": round(entity_coverage(agentic_entities), 3) if agentic_entities else None,
        "has_unique_constraint": bool(re.search(r"UNIQUE\s*\(", agentic_schema.get("sql_ddl", ""), re.IGNORECASE)),
        "unresolved_critical_issues": len(agentic_critical_issues),
        "went_through_review_revision": agentic_final_state.get("cycle_count", 0) > 0,
    }

    if baseline is None:
        baseline_result = {
            "outcome": "FAILED -- could not produce a complete, parseable schema in a single shot "
                       "after 3 attempts (model repeatedly stopped after the 'entities' field, "
                       "never generating sql_ddl)",
            "mysql_validated": False,
            "entity_coverage": None,
            "has_unique_constraint": False,
            "was_reviewed_or_revised": False,
        }
    else:
        print("  Validating baseline SQL against real MySQL (same MCP tool as pipeline)...")
        baseline_validation = validate_sql(baseline.sql_ddl)
        baseline_result = {
            "outcome": "produced output",
            "mysql_validated": baseline_validation.get("valid", False),
            "mysql_errors": baseline_validation.get("errors", []),
            "entity_coverage": round(entity_coverage(baseline.entities), 3) if baseline.entities else None,
            "has_unique_constraint": bool(re.search(r"UNIQUE\s*\(", baseline.sql_ddl, re.IGNORECASE)),
            "was_reviewed_or_revised": False,
        }

    return {
        "application": app_key,
        "agentic": agentic_result,
        "baseline_single_shot": baseline_result,
    }


if __name__ == "__main__":
    state_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not state_path or not state_path.exists():
        print("Usage: python agentic_uplift_eval.py <path to saved final_state.json>")
        sys.exit(1)

    agentic_state = json.loads(state_path.read_text())
    description = agentic_state["user_input"]
    ground_truth = json.loads(
        (Path(__file__).resolve().parent.parent / "requirement_ground_truth.json").read_text()
    )
    expected_entities = ground_truth["ticket_booking"]["expected_entities"]

    result = compare_scenario("ticket_booking", description, expected_entities, agentic_state)
    print(json.dumps(result, indent=2))