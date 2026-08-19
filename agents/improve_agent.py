"""
Phase 13 component: Improve step.

Applies the Review Agent's critical/warning issues to the current SQL DDL
and indexes, then re-validates through Phase 11's validate_and_fix_sql --
a revised DDL could introduce a new syntax error, so this isn't optional.
"""

import json
import sys
from pathlib import Path
from langsmith import traceable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from schema_agent import SqlOutput, _call_llm, _repair_and_validate
from schema_agent_validated import validate_and_fix_sql

IMPROVE_SYSTEM_PROMPT = """You are a Schema Design Agent revising a schema based
on a review. You will be given the current SQL DDL, current indexes, and a
list of issues found by a review. Revise the DDL and indexes to resolve the
issues -- especially any "critical" severity issues, which MUST be fixed.

Respond with ONLY a JSON object in exactly this shape:
{
  "sql_ddl": "<the complete revised SQL DDL as a single string with real newlines>",
  "indexes": [
    {"table": "<table name>", "columns": ["<col1>"], "reason": "<why>"}
  ]
}

Keep everything that wasn't flagged as an issue unchanged. Output ONLY the
JSON object.
"""

SCHEMA_ACTIONABLE_CATEGORIES = {"constraints", "indexes", "concurrency"}

def apply_review_fixes(sql_ddl: str, indexes: list[dict], issues: list[dict]) -> dict:
    if not issues:
        return {"sql_ddl": sql_ddl, "indexes": indexes}

    issues_text = "\n".join(
        f"- [{i['severity']}/{i['category']}] {i['description']} "
        f"Suggested fix: {i['suggested_fix']}"
        for i in issues
    )
    indexes_text = "; ".join(
        f"{i['table']}({', '.join(i['columns'])})" for i in indexes
    ) or "none"

    user_message = (
        f"Current SQL DDL:\n{sql_ddl}\n\n"
        f"Current indexes: {indexes_text}\n\n"
        f"Issues found by review:\n{issues_text}"
    )

    raw = _call_llm(IMPROVE_SYSTEM_PROMPT, user_message, "improve", max_retries=2)
    fixed = _repair_and_validate(raw, SqlOutput)
    return {
        "sql_ddl": fixed.sql_ddl,
        "indexes": [i.model_dump() for i in fixed.indexes],
    }

@traceable(name="run_improve_step", run_type="tool")
def run_improve_step(schema: dict, review: dict) -> dict:
    actionable = [
        i for i in review["issues"]
        if i["severity"] in ("critical", "warning")
        and i["category"] in SCHEMA_ACTIONABLE_CATEGORIES
    ]

    print(f"  Applying fixes for {len(actionable)} schema-actionable critical/warning issue(s) "
          f"(of {len(review['issues'])} total issues found)...")
    revised = apply_review_fixes(schema["sql_ddl"], schema["indexes"], actionable)

    print("  Re-validating revised DDL against MySQL...")
    validation = validate_and_fix_sql(revised["sql_ddl"])

    updated_schema = dict(schema)
    updated_schema["sql_ddl"] = validation["sql_ddl"]
    updated_schema["indexes"] = revised["indexes"]
    from er_diagram_agent import parse_ddl
    parsed_tables = parse_ddl(validation["sql_ddl"])
    updated_schema["constraints"] = [
        {"type": "primary_key", "table": t["table"], "columns": t["primary_key"],
         "description": "auto-derived from revised DDL"}
        for t in parsed_tables if t["primary_key"]
    ] + [
        {"type": "foreign_key", "table": t["table"], "columns": [fk["column"]],
         "description": f"references {fk['ref_table']}({fk['ref_column']})"}
        for t in parsed_tables for fk in t["foreign_keys"]
    ] + [
        {"type": "unique", "table": t["table"], "columns": uc,
         "description": "auto-derived from revised DDL"}
        for t in parsed_tables for uc in t["unique_constraints"]
    ]
    updated_schema["validation"] = {
        "final_valid": validation["final_valid"],
        "attempts": validation["attempts"],
        "log": validation["log"],
    }
    return updated_schema