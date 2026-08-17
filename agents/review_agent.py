"""
Phase 12: Review & Optimization Agent.

Acts as a database architect reviewing the Schema Agent's output. Checks
schema correctness, integrity constraints, performance (indexes), transaction
soundness (especially whether the critical invariant is ACTUALLY enforced,
not just claimed), and architectural fit of supporting components.

Per the proposal's Section 10 diagram, the "Improve" loop (re-invoking Schema
Agent with this critique) is wired in Phase 13's LangGraph orchestration --
this agent's job is just to produce the structured critique.
"""

import json
import re
import time
from langsmith import traceable
import ollama
from pydantic import BaseModel, Field, ValidationError

MODEL_NAME = "qwen3:4b"

SYSTEM_PROMPT = """You are a Review Agent acting as a senior database architect.
You are reviewing a generated database schema for correctness and soundness.

Check specifically for:
- Whether the SQL schema actually enforces the stated critical invariant
  (not just whether the transaction_strategy text CLAIMS it does -- check
  whether a real UNIQUE constraint or equivalent mechanism exists in the DDL)
- Missing or incorrect primary/foreign keys
- Missing indexes on columns used in important queries
- Concurrency problems: could double-booking, overselling, or lost updates
  still occur under concurrent access despite the stated transaction strategy?
- Whether supporting components (e.g. Redis, OpenSearch) are used appropriately
  and are not being treated as a source of truth for critical data
- Unnecessary complexity: components or tables not justified by the requirements

Respond with ONLY a JSON object in exactly this shape:
{
  "issues": [
    {
      "category": "<schema|integrity|performance|transactions|architecture>",
      "severity": "<critical|warning|suggestion>",
      "description": "<what is wrong, specifically>",
      "suggested_fix": "<a concrete fix>"
    }
  ],
  "overall_assessment": "<2-3 sentences: is this design sound enough to use?>"
}

A critical invariant that is claimed but not actually enforced in the DDL is
ALWAYS a "critical" severity issue in the "transactions" category -- check
this specifically before anything else. If you find no issues, return an
empty "issues" list, but still explain why in overall_assessment.

Do NOT repeat or copy the input schema into your output. Output ONLY the
JSON object described above.
"""


class Issue(BaseModel):
    category: str
    severity: str
    description: str
    suggested_fix: str


class ReviewOutput(BaseModel):
    issues: list[Issue] = Field(default_factory=list)
    overall_assessment: str


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


def _schema_to_prose(requirement: dict, schema: dict) -> str:
    """Prose, not raw JSON -- avoids the model echoing input structure back,
    same lesson learned in the Schema Agent (Phase 8)."""
    entities = ", ".join(e["name"] for e in schema.get("entities", []))
    relationships = "; ".join(
        f"{r['from']} -> {r['to']} ({r['type']})" for r in schema.get("relationships", [])
    )
    indexes = "; ".join(
        f"{i['table']}({', '.join(i['columns'])})" for i in schema.get("indexes", [])
    ) or "none defined"

    return (
        f"Critical invariant that MUST be enforced: {requirement.get('critical_invariant')}\n\n"
        f"Entities: {entities}\n\n"
        f"Relationships: {relationships}\n\n"
        f"Indexes defined: {indexes}\n\n"
        f"Transaction strategy claimed by the Schema Agent: {schema.get('transaction_strategy')}\n\n"
        f"Actual SQL DDL:\n{schema.get('sql_ddl')}\n\n"
        f"Important queries:\n"
        + "\n".join(f"- {q['description']}: {q['sql']}" for q in schema.get("important_queries", []))
    )

@traceable(name="review_agent", run_type="chain")
def run_review_agent(requirement: dict, schema: dict, max_retries: int = 2) -> ReviewOutput:
    user_message = _schema_to_prose(requirement, schema)

    last_error = None
    for attempt in range(1, max_retries + 2):
        start = time.time()
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            think=False,
            format="json",
            options={"temperature": 0, "num_predict": 900},
        )
        elapsed = time.time() - start
        raw = _strip_code_fences(response["message"]["content"])
        print(f"  [attempt {attempt}] {elapsed:.1f}s, eval_count={response.get('eval_count')}, "
              f"done_reason={response.get('done_reason')}")

        try:
            data = json.loads(raw)
            return ReviewOutput(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            print(f"  [attempt {attempt}] failed to parse/validate: {e}")
            print(f"  raw output (last 300 chars): ...{raw[-300:]}")
            continue

    raise RuntimeError(f"Review Agent failed after {max_retries + 1} attempts. Last error: {last_error}")


if __name__ == "__main__":
    # Using the ACTUAL output from the real Phase 11 run -- including the
    # known bug (claimed uniqueness constraint that doesn't exist in the DDL)
    # as a real test of whether this agent catches it.
    example_requirement = {
        "application": "TicketBooking",
        "critical_invariant": "A seat cannot be booked more than once.",
    }
    example_schema = {
        "entities": [
            {"name": "User", "description": "..."},
            {"name": "Event", "description": "..."},
            {"name": "Seat", "description": "..."},
            {"name": "Booking", "description": "..."},
        ],
        "relationships": [
            {"from": "User", "to": "Booking", "type": "one-to-many"},
            {"from": "Event", "to": "Seat", "type": "one-to-many"},
            {"from": "Event", "to": "Booking", "type": "one-to-many"},
            {"from": "Seat", "to": "Booking", "type": "one-to-one"},
        ],
        "sql_ddl": (
            "CREATE TABLE users (\n  id CHAR(36) PRIMARY KEY,\n  email VARCHAR(255) UNIQUE NOT NULL,\n"
            "  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n);\n"
            "CREATE TABLE events (\n  id CHAR(36) PRIMARY KEY,\n  name VARCHAR(100) NOT NULL,\n"
            "  description TEXT,\n  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n);\n"
            "CREATE TABLE seats (\n  id CHAR(36) PRIMARY KEY,\n  event_id CHAR(36) NOT NULL,\n"
            "  seat_number VARCHAR(20) NOT NULL,\n  status VARCHAR(20) NOT NULL DEFAULT 'available',\n"
            "  FOREIGN KEY (event_id) REFERENCES events(id)\n);\n"
            "CREATE TABLE bookings (\n  id CHAR(36) PRIMARY KEY,\n  user_id CHAR(36) NOT NULL,\n"
            "  event_id CHAR(36) NOT NULL,\n  seat_id CHAR(36) NOT NULL,\n"
            "  booking_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
            "  status VARCHAR(20) NOT NULL DEFAULT 'confirmed',\n"
            "  FOREIGN KEY (user_id) REFERENCES users(id),\n"
            "  FOREIGN KEY (event_id) REFERENCES events(id),\n"
            "  FOREIGN KEY (seat_id) REFERENCES seats(id)\n);"
        ),
        "indexes": [
            {"table": "seats", "columns": ["event_id"]},
            {"table": "bookings", "columns": ["seat_id"]},
        ],
        "transaction_strategy": (
            "Use a database transaction with row-level locking on the seat record during "
            "booking to ensure only one booking can claim a given seat. Additionally, "
            "implement a unique constraint on the combination of event_id, seat_id, and "
            "user_id to prevent double bookings across concurrent transactions."
        ),
        "important_queries": [
            {"description": "Check if a seat is already booked",
             "sql": "SELECT * FROM bookings WHERE seat_id = ? AND status = 'confirmed';"},
        ],
    }
    result = run_review_agent(example_requirement, example_schema)
    print()
    print(json.dumps(result.model_dump(), indent=2))