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
  whether they're used appropriately.
- Category checklist expanded from 5 categories to the 14 below, covering
  every checklist item in the proposal's Section 16.
- _design_to_prose (renamed from _schema_to_prose) now also surfaces
  constraints, the requirement's fuller field set, and the selection's
  9 structured architectural decisions (Phase J(b)).

Phase J(b) fixes (this version):
- Retrieval added (retrieve_review_context) -- previously this agent had
  zero RAG grounding despite the spec's Section 21 explicitly listing it
  as a retrieval consumer.
- Concurrency section rewritten with an explicit step-by-step procedure
  after repeated false positives where the model treated "transaction_
  strategy mentions row-level locking but the DDL doesn't show it
  explicitly" as proof the invariant was unenforced, when a correctly-
  scoped UNIQUE constraint is sufficient on its own.
- Output-shape drift fixes: the model was twice observed producing wrong
  JSON shapes under load -- once re-serializing the entire input under
  input-derived keys (fixed via the CRITICAL OUTPUT RULE + end-of-prompt
  reminder), and once emitting a bare string instead of an issue object
  inside "issues" (fixed via the salvage logic in run_review_agent).
"""

import json
import re
import time
from pathlib import Path

from langsmith import traceable
import ollama
from pydantic import BaseModel, Field, ValidationError
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"
EMBEDDING_MODEL = "qwen3-embedding:0.6b"
CHUNKS_PER_QUERY = 3
MAX_TOTAL_CHUNKS = 10
MODEL_NAME = "qwen3:4b"

CATEGORIES = [
    "entities_relationships",
    "constraints",
    "indexes",                   # missing or badly chosen indexes
    "queries",                   # missing important queries, queries that don't use available indexes
    "concurrency",                # race conditions, unenforced critical invariant
    "transactions",               # missing/incorrect transaction boundaries, isolation
    "consistency",                 # consistency requirement not matched by design
    "caching",                    # inappropriate caching, cache used as source of truth
    "search",                     # inappropriate or unjustified search component use
    "replication",                 # unnecessary or missing replication
    "partitioning_sharding",       # unnecessary/premature partitioning or sharding, poor shard key, hotspots, cross-shard txn problems
    "pagination",                  # missing pagination, wrong pagination strategy for the access pattern
    "idempotency",                 # missing idempotency keys, retry problems, timeout ambiguity
    "reliability",                 # failure handling, backup/recovery gaps
    "architecture",                # overengineering, unjustified complexity, unnecessary components
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
  not just whether transaction_strategy text CLAIMS it does. If the retrieved
  reference material describes the correct constraint pattern for this kind
  of invariant, check the actual DDL against that pattern specifically.
- A UNIQUE constraint covering exactly the right columns is, BY ITSELF,
  SUFFICIENT to enforce a "no two rows with the same X" invariant at the
  database level -- MySQL rejects the second conflicting INSERT
  unconditionally, regardless of whether any transaction, lock, or
  application-level check exists around it. Follow this exact procedure:
  1. Identify the invariant's key columns (e.g. "no seat booked twice" ->
     the columns that together identify a unique seat-in-context).
  2. Find the UNIQUE constraint in the DDL covering exactly those columns.
  3. If it exists and covers the right columns: the invariant IS enforced
     at the database level. This is true even if transaction_strategy's
     prose separately mentions row-level locking and the DDL has no
     explicit locking statement -- locking is an optional efficiency
     technique (avoiding wasted work under contention), NOT a requirement
     for correctness once the constraint exists. Do NOT raise a critical
     issue solely because prose describes a mechanism (locking, explicit
     transactions) that the DDL doesn't literally show -- DDL never
     contains that kind of session-level logic in the first place; check
     the constraint, not the prose's completeness.
  4. Only if the constraint is MISSING, or covers the WRONG columns (state
     exactly which columns it actually covers vs. which it should), is
     this a "critical" issue.
- Could double-booking, overselling, lost updates, or other race conditions
  still occur under concurrent access despite the stated strategy? Answer
  this by checking the constraint per steps 1-4 above, not by checking
  whether the prose is complete.

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
- If the CHOSEN ARCHITECTURE section states a specific pagination decision
  (e.g. "keyset pagination"), check whether important_queries actually
  implements it. A stated decision that the schema never implements is a
  real issue -- category "pagination", typically "warning" severity.

[idempotency]
- Do operations named in idempotency_requirements actually have a mechanism
  (idempotency key column, unique constraint, etc.) to be safely retried? Is
  there ambiguity about what happens on a client timeout/retry?
- If the idempotency decision claims a UNIQUE constraint enforces safety,
  verify that exact constraint actually exists in the DDL with the exact
  columns claimed -- don't take the claim at face value, check it the same
  way you check the critical invariant in [concurrency].

[reliability]
- Is there any handling for partial failure, backups, or recovery where the
  requirements call for it (e.g. lifecycle_requirements, availability_requirement)?
- Check the failure_handling decision (in CHOSEN ARCHITECTURE) against this --
  if it defers something (e.g. "no multi-region failover") because
  availability_requirement is unstated, that is a sound, non-critical
  decision; don't flag it as an issue merely for choosing the simpler option
  under missing information.

[architecture]
- Is any supporting component (Redis, OpenSearch, replicas, partitioning,
  sharding) present in the design without being justified by the stated
  requirements? Flag overengineering explicitly -- this is as real a problem
  as a missing feature.
- Cross-check every decision under CHOSEN ARCHITECTURE (caching, replication,
  search, partitioning, sharding): is the stated "reason"/"evidence"
  actually supported by the requirement fields shown above, or does it
  contradict them (e.g. a decision citing "read-heavy workload" when
  read_write_ratio is "balanced")? A decision whose own stated evidence
  doesn't match the requirements belongs in this [architecture] category,
  not the category the decision itself is about.

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

CRITICAL OUTPUT RULE: your JSON response must contain EXACTLY these two
top-level keys -- "issues" and "overall_assessment" -- and NO OTHERS. The
material you are given (labeled REQUIREMENTS, CHOSEN ARCHITECTURE, SCHEMA,
Actual SQL DDL, Important queries, RETRIEVED REFERENCE MATERIAL) is INPUT
for you to analyze, not a template for your output's structure. Do NOT
create JSON keys named "schema", "requirements", "actual_sql_ddl",
"transaction_strategy", or anything else derived from the input's section
headers. Do NOT copy, restate, or re-serialize the schema, DDL, or
requirements back into your response in any form -- your job is to output
findings ABOUT that material, never the material itself.

If you find no issues in a category, simply don't report one for it -- do not
pad the list. If you find no issues at all, return an empty "issues" list,
but still explain why in overall_assessment.

Every item in "issues" MUST be a JSON object with all four keys shown above
-- never a bare string. If you have only one finding, it still must be
wrapped as {"category": ..., "severity": ..., "description": ..., "suggested_fix": ...},
not a plain string in the array.

Only output the JSON object described above.
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


def _design_to_prose(requirement: dict, selection: dict, schema: dict, retrieved_context: str) -> str:
    """Prose, not raw JSON -- avoids the model echoing input structure back,
    same lesson learned in the Schema Agent (Phase 8). Phase J: surfaces
    constraints, the requirement's fuller field set, and the selection's
    chosen architecture. Phase J(b): also surfaces the 9 structured
    architectural decisions, and retrieved RAG context."""
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

    decision_fields = [
        "caching", "replication", "search", "partitioning", "sharding",
        "pagination", "failure_handling", "idempotency", "consistency_strategy",
    ]
    decisions = "\n".join(
        f"- {field}: {d['decision']} (reason: {d['reason']}; trade-off: {d['trade_off']})"
        for field in decision_fields
        if (d := selection.get(field))
    ) or "none recorded"

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
        f"Supporting components: {supporting}\n"
        f"Structured architectural decisions (Selection Agent's own stated reasoning "
        f"-- check both whether each is internally justified AND whether the schema "
        f"below actually implements it):\n{decisions}\n\n"
        f"SCHEMA\n"
        f"Entities: {entities}\n"
        f"Relationships: {relationships}\n"
        f"Constraints: {constraints}\n"
        f"Indexes defined: {indexes}\n"
        f"Transaction strategy claimed by the Schema Agent: {schema.get('transaction_strategy')}\n\n"
        f"Actual SQL DDL:\n{schema.get('sql_ddl')}\n\n"
        f"Important queries:\n{queries}\n\n"
        f"RETRIEVED REFERENCE MATERIAL (verify your critique against this -- "
        f"e.g. if a source states how a constraint should be structured to "
        f"enforce an invariant, check the actual DDL against that source's "
        f"stated pattern, not just your own reasoning):\n{retrieved_context}\n\n"
        f"---\n"
        f"REMINDER: respond with ONLY the two-key JSON object described in the "
        f"system prompt ('issues' and 'overall_assessment'). Do not create a key "
        f"for any section above (schema, actual_sql_ddl, requirements, etc.) -- "
        f"those are the input you are critiquing, not your output's shape. Every "
        f"item in 'issues' must be a full object, never a bare string."
    )


def build_review_queries(requirement: dict, selection: dict) -> list[str]:
    """Targeted retrieval per the spec's Section 21 Review Agent list:
    transactions, concurrency, consistency, caching, replication,
    partitioning, sharding, failure handling, idempotency, case studies.
    Grounded in the ACTUAL invariant/decisions, not generic topic names --
    same principle as selection_agent's build_queries."""
    queries = []

    if requirement.get("critical_invariant"):
        queries.append(
            f"how to enforce with a database constraint: {requirement['critical_invariant']}"
        )
    queries.append(
        f"transaction isolation concurrency for {requirement.get('concurrency', '')} "
        f"concurrency and {requirement.get('consistency', '')} consistency"
    )

    for field in ("caching", "replication", "partitioning", "sharding",
                  "pagination", "idempotency", "failure_handling"):
        d = selection.get(field)
        if d and d.get("decision"):
            queries.append(f"{field.replace('_', ' ')}: {d['decision']}")

    queries.append(f"case study design for application: {requirement.get('application', '')}")

    return queries


def retrieve_review_context(requirement: dict, selection: dict) -> list:
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(
        str(VECTORSTORE_DIR), embeddings, allow_dangerous_deserialization=True
    )
    queries = build_review_queries(requirement, selection)
    seen, collected = set(), []
    for q in queries:
        for doc in vectorstore.similarity_search(q, k=CHUNKS_PER_QUERY):
            key = (doc.metadata.get("source"), doc.page_content[:80])
            if key in seen:
                continue
            seen.add(key)
            collected.append(doc)
            if len(collected) >= MAX_TOTAL_CHUNKS:
                return collected
    return collected


def format_review_context(chunks: list) -> str:
    parts = []
    for doc in chunks:
        parts.append(f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def _synthesize_overall_assessment(issues: list[dict]) -> str:
    """Fallback when the model structurally omits overall_assessment --
    observed cause: folds the assessment sentence into the last issue's
    suggested_fix instead of emitting the separate top-level key, once the
    issues list has more than one entry. Deterministic at temperature=0, so
    retrying without repair just reproduces the same omission every time.
    This is a backfill, not a substitute for the model's own judgment --
    logged clearly so a backfilled run is distinguishable from a real one."""
    if not issues:
        return "No issues found."
    critical = [i for i in issues if i.get("severity") == "critical"]
    if critical:
        return (
            f"{len(critical)} critical issue(s) found (auto-summarized -- "
            f"the model omitted its own overall_assessment field): "
            + "; ".join(i.get("description", "")[:120] for i in critical)
        )
    return (
        f"{len(issues)} non-critical issue(s) found, no critical issues "
        f"(auto-summarized -- the model omitted its own overall_assessment field)."
    )


def _normalize_issues(raw_issues: list) -> list[dict]:
    """Guards against the model emitting an 'issues' array item as a bare
    string instead of the required object -- observed once when the model
    had only a single simple finding and skipped the full object shape.
    Salvage rather than discard, same philosophy as _normalize_category.
    Severity defaults to 'warning', never 'critical' -- an ambiguous
    salvaged finding must never auto-trigger the improve loop."""
    normalized = []
    for issue in raw_issues:
        if isinstance(issue, str):
            print(f"    [salvage] issue was a bare string, wrapping: {issue[:100]}")
            issue = {
                "category": "architecture",
                "severity": "warning",
                "description": issue,
                "suggested_fix": "unspecified -- model returned this issue as plain text",
            }
        elif not isinstance(issue, dict):
            print(f"    [salvage] issue had unexpected type {type(issue)}, skipping: {issue}")
            continue
        issue["category"] = _normalize_category(issue.get("category", ""))
        issue.setdefault("severity", "warning")
        issue.setdefault("description", "")
        issue.setdefault("suggested_fix", "")
        normalized.append(issue)
    return normalized


@traceable(name="review_agent", run_type="chain")
def run_review_agent(requirement: dict, selection: dict, schema: dict, max_retries: int = 2) -> ReviewOutput:
    chunks = retrieve_review_context(requirement, selection)
    print(f"  Retrieved {len(chunks)} unique chunks for review grounding")
    for doc in chunks:
        print(f"    - {doc.metadata.get('source')}")
    retrieved_context = format_review_context(chunks)

    user_message = _design_to_prose(requirement, selection, schema, retrieved_context)

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
            options={"temperature": 0, "num_predict": 1400},
        )
        elapsed = time.time() - start
        raw = _strip_code_fences(response["message"]["content"])
        print(f"  [attempt {attempt}] {elapsed:.1f}s, eval_count={response.get('eval_count')}, "
              f"done_reason={response.get('done_reason')}")

        try:
            data = json.loads(raw)
            data["issues"] = _normalize_issues(data.get("issues", []))
            if not data.get("overall_assessment"):
                print(f"  [attempt {attempt}] model omitted overall_assessment -- backfilling from issues")
                data["overall_assessment"] = _synthesize_overall_assessment(data["issues"])
            return ReviewOutput(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            print(f"  [attempt {attempt}] failed to parse/validate: {e}")
            debug_path = f"review_agent_failure_attempt{attempt}.txt"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(raw)
            print(f"  [attempt {attempt}] full raw output written to {debug_path}")
            continue

    raise RuntimeError(f"Review Agent failed after {max_retries + 1} attempts. Last error: {last_error}")


if __name__ == "__main__":
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