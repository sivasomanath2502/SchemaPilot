"""
Phase 12 + Phase J: Review & Optimization Agent.

Acts as a database architect reviewing the Schema Agent's output. Checks
schema correctness, integrity constraints, performance (indexes), transaction
soundness (especially whether the critical invariant is ACTUALLY enforced,
not just claimed), and architectural fit of supporting components.

Phase J changes:
- Now also receives `selection` (Database Selection Agent output) -- without
  it the agent had no visibility into which supporting components (Redis,
  OpenSearch, replicas) were actually recommended, so it could not judge
  whether they're used appropriately. This was a real gap found during the
  Phase J audit, not a hypothetical one: graph.py's review_step was calling
  run_review_agent(requirement, schema) with no selection argument at all.
- Category checklist expanded from 5 categories to the 14 below, covering
  every checklist item in the proposal's Section 16.
- _design_to_prose (renamed from _schema_to_prose) now also surfaces
  constraints, and the requirement's idempotency/pagination/lifecycle/
  consistency/concurrency/search fields, and the selection's
  architecture_summary + supporting_components -- all of which existed
  upstream since Phase G/H/11 but were never passed into this agent's context.

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

# Fixed category taxonomy. Kept as a documented convention rather than a
# strict Pydantic Literal -- earlier agents (requirement_agent, schema_agent)
# showed qwen3:4b occasionally drifts on exact string matches, and a
# ValidationError here would burn a retry over a label mismatch rather than
# a real content problem. _normalize_category() below maps common drift
# (case, near-synonyms) back onto the canonical set instead of rejecting it.
CATEGORIES = [
    "entities_relationships",  # missing entities, missing relationships, wrong cardinality
    "constraints",              # missing/incorrect PK, FK, unique, check constraints
    "indexes",                  # missing or badly chosen indexes
    "queries",                  # missing important queries, queries that don't use available indexes
    "concurrency",              # race conditions, unenforced critical invariant
    "transactions",             # missing/incorrect transaction boundaries, isolation
    "consistency",               # consistency requirement not matched by design
    "caching",                  # inappropriate caching, cache used as source of truth
    "search",                   # inappropriate or unjustified search component use
    "replication",               # unnecessary or missing replication
    "partitioning_sharding",     # unnecessary/premature partitioning or sharding, poor shard key, hotspots, cross-shard txn problems
    "pagination",                # missing pagination, wrong pagination strategy for the access pattern
    "idempotency",               # missing idempotency keys, retry problems, timeout ambiguity
    "reliability",                # failure handling, backup/recovery gaps
    "architecture",              # overengineering, unjustified complexity, unnecessary components
]

SYSTEM_PROMPT = """You are a Review Agent acting as a senior database architect.
You are reviewing a generated database design (schema + chosen supporting
components) for correctness and soundness.

You must check ALL of the following, organized by category. Use the category
name shown in brackets when you report an issue in that area.

[entities_relationships]
- Are any entities implied by the requirements missing from the schema?
- Are any relationships missing, or is a relationship's cardinality wrong
  (e.g. modeled one-to-many when the requirements imply many-to-many)?

[constraints]
- Missing or incorrect primary/foreign keys.
- Missing unique or check constraints that the requirements imply.

[indexes]
- Missing indexes on columns actually used in "important queries" or in
  WHERE/JOIN/ORDER BY clauses of the DDL's queries.
- Indexes that exist but don't match real access patterns.

[queries]
- Important queries implied by the requirements' read/write operations that
  are missing from important_queries.

[concurrency]
- THE MOST IMPORTANT CHECK: does the SQL DDL actually enforce the stated
  critical invariant via a real UNIQUE constraint or equivalent mechanism --
  not just whether transaction_strategy text CLAIMS it does. Check this
  specifically before anything else, and if the invariant is claimed but not
  actually enforced in the DDL, this is ALWAYS a "critical" severity issue.
- Could double-booking, overselling, lost updates, or other race conditions
  still occur under concurrent access despite the stated strategy?

[transactions]
- Are transaction boundaries and isolation level appropriate for the stated
  concurrency and consistency requirements?

[consistency]
- Does the design actually deliver the consistency level the requirements
  state (strong/eventual/mixed)? E.g. does a "strong consistency" requirement
  get undermined by an eventually-consistent supporting component being used
  for data that must be immediately correct?

[caching]
- Is caching used at all, and if so, is it ever treated as the source of
  truth for data that must be authoritative? Cache invalidation strategy
  present and sane?

[search]
- Is a search component (e.g. OpenSearch) included without search being
  required, or omitted despite search_required being true?

[replication]
- Is replication recommended without justification from read/write ratio or
  peak traffic? Is it missing despite a stated read-heavy, high-availability
  need?

[partitioning_sharding]
- Is partitioning or sharding used without justification from scale/data
  growth (premature)? If sharding is used: is the shard key reasonable, or
  does it create hotspots or force cross-shard transactions/queries for
  common operations?

[pagination]
- Do list-returning important queries have a pagination strategy consistent
  with pagination_requirements? Offset pagination on a large, frequently
  changing table is usually wrong -- flag it if so.

[idempotency]
- Do operations named in idempotency_requirements actually have a mechanism
  (idempotency key column, unique constraint, etc.) to be safely retried? Is
  there ambiguity about what happens on a client timeout/retry?

[reliability]
- Is there any handling for partial failure, backups, or recovery where the
  requirements call for it (e.g. lifecycle_requirements, availability_requirement)?

[architecture]
- Is any supporting component (Redis, OpenSearch, replicas, partitioning,
  sharding) present in the design without being justified by the stated
  requirements? Flag overengineering explicitly -- this is as real a problem
  as a missing feature.

SEVERITY GUIDANCE:
- "critical": the critical invariant is unenforced, data can be lost/
  corrupted, or a stated hard requirement is structurally violated.
- "warning": a real gap that should be fixed but doesn't corrupt data or
  violate the critical invariant (e.g. missing pagination, missing index,
  unjustified supporting component).
- "suggestion": a genuine improvement that isn't a gap against the stated
  requirements.
Do NOT mark architectural taste calls (e.g. "premature sharding" when scale
is genuinely unstated) as "critical" merely because they involve a scaling
component -- reserve "critical" for correctness/data-integrity problems.

Respond with ONLY a JSON object in exactly this shape:
{
  "issues": [
    {
      "category": "<one of: entities_relationships, constraints, indexes, queries, concurrency, transactions, consistency, caching, search, replication, partitioning_sharding, pagination, idempotency, reliability, architecture>",
      "severity": "<critical|warning|suggestion>",
      "description": "<what is wrong, specifically>",
      "suggested_fix": "<a concrete fix>"
    }
  ],
  "overall_assessment": "<2-3 sentences: is this design sound enough to use?>"
}

If you find no issues in a category, simply don't report one for it -- do not
pad the list. If you find no issues at all, return an empty "issues" list,
but still explain why in overall_assessment.

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


def _normalize_category(raw_category: str) -> str:
    """Maps drift (case, near-synonyms) back onto CATEGORIES rather than
    rejecting the whole issue -- same philosophy as the salvage layer in
    requirement_agent.py/schema_agent.py: recover, don't fail loud on
    cosmetic mismatches from a small model."""
    c = (raw_category or "").strip().lower().replace(" ", "_").replace("-", "_")
    if c in CATEGORIES:
        return c
    synonyms = {
        "schema": "entities_relationships",
        "integrity": "constraints",
        "performance": "indexes",
        "sharding": "partitioning_sharding",
        "partitioning": "partitioning_sharding",
        "cache": "caching",
        "retry": "idempotency",
        "retries": "idempotency",
        "failure_handling": "reliability",
        "backup": "reliability",
        "overengineering": "architecture",
    }
    return synonyms.get(c, c if c else "architecture")


def _design_to_prose(requirement: dict, selection: dict, schema: dict) -> str:
    """Prose, not raw JSON -- avoids the model echoing input structure back,
    same lesson learned in the Schema Agent (Phase 8). Phase J: now surfaces
    constraints, the requirement's fuller field set, and the selection's
    chosen architecture -- previously invisible to this agent."""
    entities = ", ".join(e["name"] for e in schema.get("entities", []))
    relationships = "; ".join(
        f"{r['from']} -> {r['to']} ({r['type']})" for r in schema.get("relationships", [])
    )
    indexes = "; ".join(
        f"{i['table']}({', '.join(i['columns'])})" for i in schema.get("indexes", [])
    ) or "none defined"
    constraints = "; ".join(
        f"{c.get('type')} on {c.get('table')}({', '.join(c.get('columns', []))})"
        for c in schema.get("constraints", [])
    ) or "none recorded"
    queries = "\n".join(
        f"- {q['description']}: {q['sql']}" for q in schema.get("important_queries", [])
    ) or "none recorded"

    supporting = "; ".join(
        f"{c.get('component')} ({c.get('purpose')}, "
        f"{'required' if c.get('required') else 'optional'})"
        for c in selection.get("supporting_components", [])
    ) or "none"

    return (
        f"REQUIREMENTS\n"
        f"Critical invariant that MUST be enforced: {requirement.get('critical_invariant')}\n"
        f"Other invariants: {', '.join(requirement.get('other_invariants', [])) or 'none stated'}\n"
        f"Consistency requirement: {requirement.get('consistency')}\n"
        f"Concurrency level: {requirement.get('concurrency')}\n"
        f"Search required: {requirement.get('search_required')}\n"
        f"Transaction requirements: {requirement.get('transaction_requirements', 'none beyond standard CRUD')}\n"
        f"Idempotency requirements: {requirement.get('idempotency_requirements', 'none identified')}\n"
        f"Pagination requirements: {requirement.get('pagination_requirements', 'none identified')}\n"
        f"Lifecycle requirements: {requirement.get('lifecycle_requirements', 'none identified')}\n"
        f"Availability requirement: {requirement.get('availability_requirement', 'unstated')}\n\n"
        f"CHOSEN ARCHITECTURE\n"
        f"Primary database: {selection.get('primary_database', 'unspecified')}\n"
        f"Architecture summary: {selection.get('architecture_summary', 'unspecified')}\n"
        f"Supporting components: {supporting}\n\n"
        f"SCHEMA\n"
        f"Entities: {entities}\n"
        f"Relationships: {relationships}\n"
        f"Constraints: {constraints}\n"
        f"Indexes defined: {indexes}\n"
        f"Transaction strategy claimed by the Schema Agent: {schema.get('transaction_strategy')}\n\n"
        f"Actual SQL DDL:\n{schema.get('sql_ddl')}\n\n"
        f"Important queries:\n{queries}"
    )


@traceable(name="review_agent", run_type="chain")
def run_review_agent(requirement: dict, selection: dict, schema: dict, max_retries: int = 2) -> ReviewOutput:
    user_message = _design_to_prose(requirement, selection, schema)

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
            # Bumped from 900 -- the expanded 14-category checklist can
            # legitimately surface more issues than the old 5-category one.
            options={"temperature": 0, "num_predict": 1400},
        )
        elapsed = time.time() - start
        raw = _strip_code_fences(response["message"]["content"])
        print(f"  [attempt {attempt}] {elapsed:.1f}s, eval_count={response.get('eval_count')}, "
              f"done_reason={response.get('done_reason')}")

        try:
            data = json.loads(raw)
            for issue in data.get("issues", []):
                issue["category"] = _normalize_category(issue.get("category", ""))
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
        "other_invariants": [],
        "consistency": "strong",
        "concurrency": "high",
        "search_required": True,
        "transaction_requirements": "booking creation must be atomic",
        "idempotency_requirements": "booking creation must be safe to retry",
        "pagination_requirements": "user booking history should be paginated",
        "lifecycle_requirements": "none identified",
        "availability_requirement": "unstated",
    }
    example_selection = {
        "primary_database": "MySQL",
        "architecture_summary": "MySQL + OpenSearch",
        "supporting_components": [
            {"component": "OpenSearch", "purpose": "event search", "required": True},
        ],
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
        "constraints": [],
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
    result = run_review_agent(example_requirement, example_selection, example_schema)
    print()
    print(json.dumps(result.model_dump(), indent=2))