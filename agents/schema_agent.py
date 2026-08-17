"""
Phase 8: Schema Design Agent.

Split into two smaller calls rather than one large one — testing showed
qwen3:4b gets confused and echoes input fields back when asked for a single
large, deeply-nested schema. Two focused calls, each comparable in
complexity to the working Selection Agent schema, are more reliable.

Call 1: entities, relationships, transaction_strategy (conceptual design)
Call 2: sql_ddl, indexes, important_queries (concrete SQL, built on call 1)

No RAG here, per the proposal's architecture (Section 21) — only Agent 2
(Selection) consumes FAISS/RAG directly.

UPDATE: added retry-on-validation-error (not just JSON-parse-error), and
a "salvage" repair step for list items where qwen3:4b drops or mis-names a
required key on the 2nd+ item in an array — a known small-model failure
mode. Applied to entities, relationships, indexes, and important_queries,
since all four are arrays the model has to repeat structure across.
"""

import json
import re
import time
from langsmith import traceable
import ollama
from pydantic import BaseModel, Field, ValidationError

MODEL_NAME = "qwen3:4b"

CONCEPTUAL_SYSTEM_PROMPT = """You are a Schema Design Agent for a database architecture advisor.

You will be given a plain-English description of an application's requirements
and its chosen primary database. Design the conceptual data model.

Regardless of the stated primary database, write the DDL using MySQL 8.0-compatible syntax (e.g. use CHAR(36) for UUID-style ids, not a native UUID type; use TIMESTAMP or DATETIME, not "WITH TIME ZONE"). This SQL will be validated against a real MySQL instance.

Respond with ONLY a JSON object in exactly this shape — no explanation, no
markdown fences, nothing else:
{
  "entities": [
    {"name": "<EntityName>", "description": "<one sentence on what it represents>"}
  ],
  "relationships": [
    {"from": "<EntityName>", "to": "<EntityName>", "type": "<one-to-one|one-to-many|many-to-many>", "description": "<one sentence>"}
  ],
  "transaction_strategy": "<2-4 sentences on how transactions/locking protect the critical invariant>"
}

Example output shape (follow this exact structure for EVERY entity and EVERY
relationship, including the 2nd, 3rd, etc. — do not drop keys on later items):
{
  "entities": [
    {"name": "User", "description": "A registered user of the system."},
    {"name": "Event", "description": "A ticketed event with multiple seats available for booking."}
  ],
  "relationships": [
    {"from": "User", "to": "Booking", "type": "one-to-many", "description": "A user can make many bookings."},
    {"from": "Event", "to": "Seat", "type": "one-to-many", "description": "An event has many seats."}
  ],
  "transaction_strategy": "Use a database transaction with row-level locking on the seat record during booking to ensure only one booking can claim a given seat."
}

Every entity object MUST have both "name" and "description" keys.
Every relationship object MUST have "from", "to", "type", and "description" keys.
Never omit a key on any array item, no matter how many items there are.

Keep the entity list minimal — only entities clearly implied by the description.
Do NOT repeat or copy the input description into your output. Output ONLY the
JSON object described above.
"""

SQL_SYSTEM_PROMPT = """You are a Schema Design Agent for a database architecture advisor.

You will be given a list of entities, their relationships, and the chosen
primary database. Generate the concrete SQL schema.

Respond with ONLY a JSON object in exactly this shape — no explanation, no
markdown fences, nothing else:
{
  "sql_ddl": "<complete SQL CREATE TABLE statements for all entities, including primary keys, foreign keys, and constraints, as a single string with real newlines>",
  "indexes": [
    {"table": "<table name>", "columns": ["<col1>", "<col2>"], "reason": "<why this index is needed>"}
  ],
  "important_queries": [
    {"description": "<what this query does>", "sql": "<the SQL query>"}
  ]
}

Example output shape (follow this exact structure for EVERY index and EVERY
query, including the 2nd, 3rd, etc. — do not drop keys on later items):
{
  "sql_ddl": "CREATE TABLE users (...);\\nCREATE TABLE bookings (...);",
  "indexes": [
    {"table": "bookings", "columns": ["user_id", "created_at"], "reason": "Speeds up user booking-history queries sorted by recency."},
    {"table": "bookings", "columns": ["seat_id"], "reason": "Enforces fast lookup to prevent double-booking a seat."}
  ],
  "important_queries": [
    {"description": "Get a user's booking history", "sql": "SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC;"},
    {"description": "Check if a seat is already booked", "sql": "SELECT * FROM bookings WHERE seat_id = ? AND status = 'confirmed';"}
  ]
}

Every index object MUST have "table", "columns", and "reason" keys.
Every important_queries object MUST have "description" and "sql" keys.
Never omit a key on any array item, no matter how many items there are.

Do NOT repeat or copy the input entity list into your output as-is — use it to
write real SQL. Output ONLY the JSON object described above.
"""


class Entity(BaseModel):
    name: str
    description: str


class Relationship(BaseModel):
    from_: str = Field(alias="from")
    to: str
    type: str
    description: str

    class Config:
        populate_by_name = True


class Index(BaseModel):
    table: str
    columns: list[str]
    reason: str


class ImportantQuery(BaseModel):
    description: str
    sql: str


class ConceptualOutput(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship] = Field(default_factory=list)
    transaction_strategy: str


class SqlOutput(BaseModel):
    sql_ddl: str
    indexes: list[Index] = Field(default_factory=list)
    important_queries: list[ImportantQuery] = Field(default_factory=list)


class SchemaOutput(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship] = Field(default_factory=list)
    sql_ddl: str
    indexes: list[Index] = Field(default_factory=list)
    transaction_strategy: str
    important_queries: list[ImportantQuery] = Field(default_factory=list)


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


def _requirement_to_prose(requirement: dict, selection: dict) -> str:
    """Plain-English description instead of raw JSON — avoids the model
    pattern-matching on 'JSON already in context' and echoing it back."""
    entities = ", ".join(requirement.get("entities", [])) or "unspecified entities"
    invariant = requirement.get("critical_invariant") or "no single critical invariant stated"
    return (
        f"Application: {requirement.get('application')}. "
        f"It involves these entities: {entities}. "
        f"It requires {requirement.get('consistency')} consistency and must handle "
        f"{requirement.get('concurrency')} concurrency. "
        f"The most important rule to protect is: {invariant}. "
        f"Workload type is {requirement.get('workload')}, "
        f"read/write pattern is {requirement.get('read_write_ratio')}. "
        f"Full-text search is {'required' if requirement.get('search_required') else 'not required'}. "
        f"Expected scale: {requirement.get('expected_scale')}. "
        f"Chosen primary database: {selection.get('primary_database')}, because "
        f"{selection.get('primary_reasoning')}"
    )


# ---------------------------------------------------------------------------
# Salvage / repair helpers
# ---------------------------------------------------------------------------

def _salvage_list_items(items: list, required_keys: list[str], list_label: str) -> list:
    """For each dict in `items`, if any required_key is missing, try to
    recover it from a stray/mis-named key of the same expected type
    (string keys assumed here, which covers all our cases) before giving up
    and filling an empty-string fallback. Mutates and returns the list.

    This handles the exact failure mode seen in production: qwen3:4b drops
    the intended key name on a later array item and instead emits something
    like {"name": "Event", ": ": "...the actual description text..."} —
    the value is usually still the correct content, just under a broken key.
    """
    for item in items:
        if not isinstance(item, dict):
            continue
        missing = [k for k in required_keys if k not in item]
        if not missing:
            continue
        print(f"    [salvage] {list_label} item missing {missing}: {item}")
        for key in missing:
            # look for a stray key not in required_keys whose value is a
            # plausible string replacement (non-empty, not already used)
            candidate_key = None
            for k, v in item.items():
                if k in required_keys:
                    continue
                if isinstance(v, str) and v.strip():
                    candidate_key = k
                    break
            if candidate_key is not None:
                item[key] = item.pop(candidate_key).strip()
                print(f"    [salvage] recovered '{key}' from stray key '{candidate_key}'")
            else:
                item[key] = ""
                print(f"    [salvage] no recoverable value for '{key}', set to empty string")
    return items


def _repair_and_validate(raw: dict, model_cls):
    if "entities" in raw and isinstance(raw["entities"], list):
        _salvage_list_items(raw["entities"], ["name", "description"], "entities")
    if "relationships" in raw and isinstance(raw["relationships"], list):
        _salvage_list_items(raw["relationships"], ["from", "to", "type", "description"], "relationships")
    if "indexes" in raw and isinstance(raw["indexes"], list):
        _salvage_list_items(raw["indexes"], ["table", "columns", "reason"], "indexes")
    if "important_queries" in raw and isinstance(raw["important_queries"], list):
        _salvage_list_items(raw["important_queries"], ["description", "sql"], "important_queries")
    return model_cls(**raw)


# ---------------------------------------------------------------------------
# LLM call + validation, both retried independently
# ---------------------------------------------------------------------------

def _call_llm(system_prompt: str, user_message: str, label: str, max_retries: int = 2) -> dict:
    """Retries only on JSON parse failure. Returns a raw dict."""
    last_error = None
    for attempt in range(1, max_retries + 2):
        start = time.time()
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            think=False,
            format="json",
            options={"temperature": 0, "num_predict": 900},
        )
        elapsed = time.time() - start
        raw = _strip_code_fences(response["message"]["content"])
        print(f"  [{label} attempt {attempt}] {elapsed:.1f}s, "
              f"eval_count={response.get('eval_count')}, done_reason={response.get('done_reason')}")

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            last_error = e
            print(f"  [{label} attempt {attempt}] JSON parse failed: {e}")
            print(f"  raw output (last 300 chars): ...{raw[-300:]}")
            continue

    raise RuntimeError(f"{label} failed to produce valid JSON after {max_retries + 1} attempts. Last error: {last_error}")


def _call_with_validation(system_prompt: str, user_message: str, label: str, model_cls,
                           max_retries: int = 2):
    """Calls the LLM, attempts salvage + Pydantic validation. On
    ValidationError, retries the WHOLE LLM call (not just re-parsing),
    since a fresh generation is more likely to fix a structural mistake
    than trying to repair the same bad output further."""
    last_error = None
    for attempt in range(1, max_retries + 2):
        raw = _call_llm(system_prompt, user_message, f"{label}", max_retries=1)
        try:
            return _repair_and_validate(raw, model_cls)
        except ValidationError as e:
            last_error = e
            print(f"  [{label} attempt {attempt}] validation failed after salvage attempt:\n{e}")
            continue

    raise RuntimeError(f"{label} failed validation after {max_retries + 1} attempts. Last error: {last_error}")

@traceable(name="schema_agent")
def run_schema_agent(requirement: dict, selection: dict) -> SchemaOutput:
    prose = _requirement_to_prose(requirement, selection)

    print("  Step 1/2: conceptual design (entities, relationships, transaction strategy)...")
    conceptual = _call_with_validation(
        CONCEPTUAL_SYSTEM_PROMPT, prose, "conceptual", ConceptualOutput
    )

    print("  Step 2/2: SQL schema (DDL, indexes, queries)...")
    entity_list = ", ".join(f"{e.name} ({e.description})" for e in conceptual.entities)
    rel_list = "; ".join(
        f"{r.from_} -> {r.to} ({r.type}: {r.description})" for r in conceptual.relationships
    )
    sql_user_message = (
        f"Primary database: {selection.get('primary_database')}\n"
        f"Entities: {entity_list}\n"
        f"Relationships: {rel_list}\n"
        f"Critical invariant to protect: {requirement.get('critical_invariant')}"
    )
    sql_part = _call_with_validation(
        SQL_SYSTEM_PROMPT, sql_user_message, "sql", SqlOutput
    )

    return SchemaOutput(
        entities=conceptual.entities,
        relationships=conceptual.relationships,
        transaction_strategy=conceptual.transaction_strategy,
        sql_ddl=sql_part.sql_ddl,
        indexes=sql_part.indexes,
        important_queries=sql_part.important_queries,
    )


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
    result = run_schema_agent(example_requirement, example_selection)
    print(json.dumps(result.model_dump(by_alias=True), indent=2))