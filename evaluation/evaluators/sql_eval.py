# evaluation/evaluators/sql_eval.py
"""
Metric D: SQL Execution Success Rate.

Does NOT re-implement validation -- reuses schema_agent_validated's own
MCP-backed validate_and_fix_sql, run as part of a normal graph.py pipeline
call per scenario. This metric reads the validation.final_valid field that
every schema-generation call already produces via real MySQL execution
(never an LLM claiming "the SQL is valid" -- that field is only set true
after mcp_server.validate_sql actually ran it against MySQL).
"""

import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from graph import build_graph

SCENARIOS_PATH = Path(__file__).resolve().parent.parent / "requirement_ground_truth.json"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def run_sql_eval() -> dict:
    scenarios = json.loads(SCENARIOS_PATH.read_text())
    app = build_graph()
    results = []

    for i, (app_key, gt) in enumerate(scenarios.items(), 1):
        print(f"[{i}/{len(scenarios)}] running full pipeline for: {app_key}")
        final_state = app.invoke({
            "user_input": gt["description"],
            "requirement": {}, "selection": {}, "schema": {}, "review": {},
            "cycle_count": 0, "er_diagram": "", "report": {},
        })

        validation = final_state.get("schema", {}).get("validation", {})
        results.append({
            "application": app_key,
            "final_valid": validation.get("final_valid", False),
            "attempts": validation.get("attempts"),
            "errors_seen": [
                err for log_entry in validation.get("log", [])
                for err in log_entry.get("result", {}).get("errors", [])
            ],
        })

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = RESULTS_DIR / f"{app_key}_{time.strftime('%Y%m%d_%H%M%S')}.json"
        out_path.write_text(json.dumps(final_state, indent=2), encoding="utf-8")
        print(f"  -> saved full state to {out_path.name}")

    successes = sum(1 for r in results if r["final_valid"])
    return {
        "sql_execution_success_rate": round(successes / len(results), 3) if results else 0,
        "successful": successes,
        "total": len(results),
        "per_application": results,
    }


if __name__ == "__main__":
    result = run_sql_eval()
    print(json.dumps(result, indent=2))