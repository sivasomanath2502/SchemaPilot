"""
Phase 11: Schema Agent + MCP validate_sql integration.

Exposes validate_and_fix_sql() as a reusable function -- used both for the
initial DDL from Schema Agent, and again in Phase 13's Improve step after
the Review Agent's feedback has been applied, since a revised DDL could
introduce a new syntax error.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp_server"))

from schema_agent import (
    MODEL_NAME,
    SchemaOutput,
    SqlOutput,
    _call_llm,
    _repair_and_validate,
    run_schema_agent,
)
from server import validate_sql

MAX_FIX_ATTEMPTS = 2

SQL_FIX_SYSTEM_PROMPT = """You are a Schema Design Agent fixing a SQL error.

You will be given SQL DDL that failed validation against MySQL, and the exact
error MySQL returned. Fix ONLY what the error describes -- do not redesign the
schema, do not add new tables or columns beyond what's needed to fix the error.

Respond with ONLY a JSON object in exactly this shape:
{
  "sql_ddl": "<the corrected, complete SQL DDL as a single string with real newlines>"
}

Output ONLY the JSON object.
"""


def normalize_mysql_dialect(sql: str) -> str:
    """Deterministically fix known Postgres-isms qwen3:4b defaults to
    regardless of dialect instructions -- more reliable than a natural-
    language retry, which testing showed just regenerates the same broken
    SQL since MySQL's raw error text doesn't explain why."""
    sql = re.sub(r'\bUUID\b', 'CHAR(36)', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bTIMESTAMPTZ\b', 'TIMESTAMP', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bTIMESTAMP\s+WITH\s+TIME\s+ZONE\b', 'TIMESTAMP', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bSERIAL\b', 'INT AUTO_INCREMENT', sql, flags=re.IGNORECASE)
    return sql


def _attempt_sql_fix(broken_sql: str, error_message: str) -> str:
    user_message = (
        f"This SQL failed validation:\n{broken_sql}\n\n"
        f"MySQL returned this error:\n{error_message}\n\n"
        f"Fix only what the error describes."
    )
    raw = _call_llm(SQL_FIX_SYSTEM_PROMPT, user_message, "sql_fix", max_retries=1)
    return normalize_mysql_dialect(raw["sql_ddl"])


def validate_and_fix_sql(sql_ddl: str) -> dict:
    """Runs the validate-then-fix loop against MySQL. Returns the (possibly
    fixed) sql_ddl plus a validation report. Reusable by both the initial
    Schema Agent generation and the Improve step in Phase 13."""
    sql_ddl = normalize_mysql_dialect(sql_ddl)
    validation_log = []

    for attempt in range(1, MAX_FIX_ATTEMPTS + 2):
        print(f"    Validating DDL against MySQL (attempt {attempt})...")
        result = validate_sql(sql_ddl)
        validation_log.append({"attempt": attempt, "result": result})

        if result["valid"]:
            print(f"    Valid on attempt {attempt}.")
            break

        error_text = "; ".join(result["errors"])
        print(f"    Invalid: {error_text}")

        if attempt > MAX_FIX_ATTEMPTS:
            print("    Max fix attempts reached, giving up on syntax repair.")
            break

        print("    Asking the LLM to fix the DDL based on the MySQL error...")
        try:
            sql_ddl = _attempt_sql_fix(sql_ddl, error_text)
        except Exception as e:
            print(f"    Fix attempt itself failed ({e}); treating this cycle as still-invalid "
                  f"and continuing rather than crashing the pipeline.")
            continue

    return {
        "sql_ddl": sql_ddl,
        "final_valid": validation_log[-1]["result"]["valid"],
        "attempts": len(validation_log),
        "log": validation_log,
    }


def run_schema_agent_validated(requirement: dict, selection: dict) -> dict:
    schema = run_schema_agent(requirement, selection)
    validation = validate_and_fix_sql(schema.sql_ddl)

    return {
        "entities": [e.model_dump() for e in schema.entities],
        "relationships": [r.model_dump(by_alias=True) for r in schema.relationships],
        "sql_ddl": validation["sql_ddl"],
        "indexes": [i.model_dump() for i in schema.indexes],
        "transaction_strategy": schema.transaction_strategy,
        "important_queries": [q.model_dump() for q in schema.important_queries],
        "validation": {
            "final_valid": validation["final_valid"],
            "attempts": validation["attempts"],
            "log": validation["log"],
        },
    }


if __name__ == "__main__":
    example_requirement = {
        "application": "TicketBooking",
        "entities": ["User", "Event", "Seat", "Booking"],
        "consistency": "strong",
        "concurrency": "high",
        "critical_invariant": "A seat cannot be booked more than once.",
        "workload": "transactional",
        "read_write_ratio": "balanced",
        "search_required": True,
        "expected_scale": "thousands of users",
    }
    example_selection = {
        "primary_database": "PostgreSQL",
        "primary_reasoning": "Strong consistency and ACID transactions needed to prevent double booking.",
        "supporting_components": [
            {"component": "Redis", "purpose": "caching", "required": False}
        ],
    }
    result = run_schema_agent_validated(example_requirement, example_selection)
    print()
    print(json.dumps(result, indent=2))