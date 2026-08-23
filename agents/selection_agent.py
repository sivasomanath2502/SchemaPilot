"""
Phase 7 + Phase H: Database Selection Agent.

Primary RAG consumer. Takes the Requirement Agent's structured output,
runs multiple targeted FAISS queries, and produces a structured database
recommendation with explicit alternative/rejection reasoning, PLUS a
Decision/Reason/Evidence/Alternative/Why-rejected/Trade-off block for each
of caching, replication, search, partitioning, sharding, pagination,
failure_handling, idempotency, and consistency_strategy -- these map
directly onto report sections 12-21 (minus 18, Transactions, which is
Schema Agent's job).

Phase H(b) v1 split into TWO calls (core + all 9 decisions in one call).
Real test run: the 9-decision call took 682.6s and STILL silently dropped
an entire top-level key (consistency_strategy never appeared, despite
done_reason="stop" -- not a token-budget truncation, the model just omitted
it). A full retry on a 682s call is far too expensive to pay for one
dropped key.

Phase H(b) v2: split the 9 decisions into TWO smaller groups of ~5 and ~4,
each its own call with its own worked example. This roughly halves the
leaf-field count per call (was 54, now ~30 and ~24) -- and if one group
drops a key or fails validation, only that smaller group is retried.

Renamed the 9th decision from "consistency" to "consistency_strategy" --
the Requirement Agent already has a top-level "consistency" field (a
plain string like "strong"), and having a *different, nested* field with
the identical name on Selection's output was a landmine for whatever
consumes both dicts later.

Phase H(b) v3 (this version): fixed a real bug found via full raw-output
dumps -- decisions-B was consistently failing with "Expecting ',' delimiter"
at the same byte offset every run. The dump showed 3 of the 4 required
keys were complete, well-formed JSON, and generation simply stopped mid-
object with eval_count=None, done_reason=None (never seen on a successful
call, which always reports real values). That combination -- clean partial
JSON + no proper stop reason -- is the signature of a context-window
overflow, not a formatting mistake: decisions-B's prompt (3 worked examples
+ 16 retrieved chunks + core's carried-forward reasoning) is the longest of
the three calls, and num_ctx was never set explicitly, so it was silently
using Ollama's model default (often 2048-4096), too small for this prompt.
Fixed by setting num_ctx explicitly and generously for all three calls.
Also fixed: the core call's exception handler was mislabeled "decisions-B"
in its debug output (copy-paste leftover), and _run_group_call (which is
what decisions-A/decisions-B actually run through) had no full-raw-output
dump at all -- only a raw[:400] truncation, which is why decisions-B's
real failure was invisible for three consecutive debugging rounds. Every
LLM call now dumps its full raw text on failure, correctly labeled.
"""

import json
import re
import time
from pathlib import Path

from langsmith import traceable
import ollama
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"

MODEL_NAME = "qwen3:4b"
EMBEDDING_MODEL = "qwen3-embedding:0.6b"

CHUNKS_PER_QUERY = 4
MAX_TOTAL_CHUNKS = 16

# Context window for all three LLM calls in this agent. Previously unset
# (relying on Ollama's model default, often 2048-4096), which was silently
# truncating decisions-B mid-generation -- see module docstring.
NUM_CTX = 8192

CORE_SYSTEM_PROMPT = """You are a Database Selection Agent for a database architecture advisor.

You are given:
1. A structured requirement summary for an application.
2. Retrieved reference material about relevant databases and design patterns.

Using ONLY the retrieved reference material as your factual basis (do not invent
facts about databases not present in the context), recommend a database
architecture. Respond with ONLY a JSON object — no explanation outside the JSON.

The JSON must have exactly these fields:
{
  "primary_database": "<name of the recommended primary database>",
  "primary_reasoning": "<2-4 sentences explaining why, grounded in the retrieved context>",
  "architecture_summary": "<one concise line, e.g. 'MySQL only' or 'MySQL + Redis' or 'MySQL + OpenSearch'>",
  "alternatives": [
    {"database": "<n>", "reasoning": "<why this could also work, and its tradeoff vs primary>"}
  ],
  "supporting_components": [
    {"component": "<e.g. Redis, OpenSearch>", "purpose": "<what role it plays, e.g. caching, search>", "required": <true or false>}
  ],
  "rejected": [
    {"database": "<n>", "reason": "<why it was NOT chosen>"}
  ]
}

Include at least 2 entries in "rejected" — explicit rejection reasoning is required.
A database must appear in only ONE of "alternatives" or "rejected" — never both.

Do NOT recommend a supporting component (Redis, OpenSearch, read replicas, partitioning,
sharding) merely because the application has many users or "sounds large." Only include
a supporting component in "supporting_components" if the retrieved context and the
stated requirements (workload, read/write pattern, latency, scale) actually justify it.

Only output the JSON object.
"""

DECISION_OBJECT_SPEC = """Each <decision object> has exactly these fields:
{
  "decision": "<what you decided, e.g. 'No read replicas' or 'Cursor-based pagination'>",
  "reason": "<why, in your own words>",
  "evidence": "<cite the specific requirement field or retrieved source that supports this>",
  "alternative": "<a real alternative approach, or null if none is meaningful>",
  "why_alternative_rejected": "<why the alternative was not chosen, or null if alternative is null>",
  "trade_off": "<the trade-off of the decision you made, stated honestly>"
}

IMPORTANT anti-overengineering rule: if a requirement field is "unknown" or "unstated"
(e.g. expected_scale, peak_traffic, availability_requirement), that is NOT license to
assume worst-case scale — it means you do not have grounds to justify the more complex
option. In that case "decision" should be the simpler option (e.g. "No sharding —
insufficient scale information to justify it"), and "evidence" should say exactly that
the relevant requirement field is unknown. Do not silently upgrade "unknown" into an
assumed large number.

Every decision must have a real "trade_off" even when the decision is to NOT adopt
something — e.g. declining replication trades off read-scaling headroom and failover
for lower operational complexity.

Only output the JSON object."""

DECISIONS_GROUP_A_KEYS = ["caching", "replication", "search", "partitioning", "sharding"]
DECISIONS_GROUP_B_KEYS = ["pagination", "failure_handling", "idempotency", "consistency_strategy"]

DECISIONS_PROMPT_A = f"""You are a Database Selection Agent for a database architecture advisor,
now reasoning about FIVE specific architectural decisions for an application whose
primary database has already been chosen.

You are given the requirement summary, the chosen primary database, and retrieved
reference material. Respond with ONLY a JSON object — no explanation outside the JSON.

The JSON must have exactly these 5 top-level keys, each an object with exactly the
6 fields shown below:
{{
  "caching": <decision object>,
  "replication": <decision object>,
  "search": <decision object>,
  "partitioning": <decision object>,
  "sharding": <decision object>
}}

{DECISION_OBJECT_SPEC}

Worked example (follow this exact structure for ALL FIVE keys above, including the
3rd, 4th, 5th — do not drop any key):
{{
  "replication": {{
    "decision": "No read replicas",
    "reason": "The requirement's read/write ratio is balanced and peak traffic is unstated, giving no evidence of a read bottleneck a single primary can't handle.",
    "evidence": "requirement field read_write_ratio is 'balanced' and peak_traffic is 'unknown'",
    "alternative": "Add one read replica for reporting queries",
    "why_alternative_rejected": "No reporting/analytics workload was described, so there is nothing for a replica to offload yet",
    "trade_off": "If read traffic grows unexpectedly, the single primary becomes a bottleneck sooner than it would with replicas in place"
  }},
  "caching": {{
    "decision": "No caching layer",
    "reason": "Workload is transactional with a balanced read/write ratio and no stated latency requirement, so there is no demonstrated need to reduce database load via caching.",
    "evidence": "requirement field latency_requirement is 'unstated' and workload is 'transactional'",
    "alternative": "Add Redis for read-through caching of hot lookups",
    "why_alternative_rejected": "No specific hot-read pattern or latency target was described that a cache would need to satisfy",
    "trade_off": "Without a cache, every read hits the primary database directly; simpler to operate but no headroom against read spikes"
  }}
}}

Remember: your output MUST contain all 5 keys — caching, replication, search,
partitioning, sharding — each fully filled in, not just the two shown above."""

DECISIONS_PROMPT_B = f"""You are a Database Selection Agent for a database architecture advisor,
now reasoning about FOUR specific architectural decisions for an application whose
primary database has already been chosen.

You are given the requirement summary, the chosen primary database, and retrieved
reference material. Respond with ONLY a JSON object — no explanation outside the JSON.

The JSON must have exactly these 4 top-level keys, each an object with exactly the
6 fields shown below:
{{
  "pagination": <decision object>,
  "failure_handling": <decision object>,
  "idempotency": <decision object>,
  "consistency_strategy": <decision object>
}}

{DECISION_OBJECT_SPEC}

Worked example (follow this exact structure for ALL FOUR keys above, including the
3rd and 4th — do not drop any key):
{{
  "pagination": {{
    "decision": "Keyset (cursor-based) pagination for event/seat listing queries",
    "reason": "Offset pagination degrades on large tables as the offset grows, and the retrieved pagination guidance recommends keyset pagination for this case.",
    "evidence": "retrieved design/pagination_deep.md recommends keyset pagination to avoid deep-offset cost on large tables",
    "alternative": "Simple offset/limit pagination",
    "why_alternative_rejected": "Offset pagination has known performance degradation at scale and no strong reason (e.g. need for 'jump to page N') favors it here",
    "trade_off": "Cursor pagination cannot jump to an arbitrary page number, only step forward/backward"
  }},
  "failure_handling": {{
    "decision": "Daily automated backups with point-in-time recovery, no multi-region failover",
    "reason": "Availability requirement is unstated, giving no evidence of a need for the operational complexity of multi-region failover; but data loss from any single-node failure must still be bounded, which backups address regardless of availability target.",
    "evidence": "requirement field availability_requirement is 'unstated' — this is about DATA DURABILITY/RECOVERY (backups, RPO/RTO), a separate concern from replication (which is about READ SCALING, already decided separately)",
    "alternative": "Multi-region active-passive failover",
    "why_alternative_rejected": "No stated availability target (e.g. '99.9% uptime') justifies the operational cost of maintaining a failover region",
    "trade_off": "Recovery from a full node loss takes longer (restore-from-backup time) than an automatic failover would, in exchange for much lower operational complexity"
  }},
  "idempotency": {{
    "decision": "Idempotency key required on booking-creation requests",
    "reason": "The critical invariant (no double booking) means a retried request must not create a second booking, so the write path needs a way to detect and safely ignore duplicates.",
    "evidence": "requirement field idempotency_requirements combined with the critical_invariant about double booking",
    "alternative": "Rely on the UNIQUE constraint alone with no explicit idempotency key",
    "why_alternative_rejected": "A UNIQUE constraint prevents a second seat claim, but a client retry could still surface a confusing duplicate-error rather than safely returning the original booking result",
    "trade_off": "Requires the client to generate and pass an idempotency key, adding a small amount of API surface complexity"
  }}
}}

IMPORTANT: "failure_handling" is about DATA DURABILITY AND RECOVERY (backups, RPO/RTO,
what happens if a node is lost) -- it is NOT about read replicas or read-scaling. Do
not reuse or restate the "replication" decision's content here; they are different
concerns even though both relate to availability.

Remember: your output MUST contain all 4 keys — pagination, failure_handling,
idempotency, consistency_strategy — each fully filled in, not just the two shown above."""


class Alternative(BaseModel):
    database: str
    reasoning: str


class SupportingComponent(BaseModel):
    component: str
    purpose: str
    required: bool


class Rejected(BaseModel):
    database: str
    reason: str


class ArchitecturalDecision(BaseModel):
    decision: str
    reason: str
    evidence: str
    alternative: str | None = None
    why_alternative_rejected: str | None = None
    trade_off: str


class SelectionCore(BaseModel):
    primary_database: str
    primary_reasoning: str
    architecture_summary: str = ""
    alternatives: list[Alternative] = Field(default_factory=list)
    supporting_components: list[SupportingComponent] = Field(default_factory=list)
    rejected: list[Rejected] = Field(default_factory=list)


class SelectionDecisionsA(BaseModel):
    caching: ArchitecturalDecision
    replication: ArchitecturalDecision
    search: ArchitecturalDecision
    partitioning: ArchitecturalDecision
    sharding: ArchitecturalDecision


class SelectionDecisionsB(BaseModel):
    pagination: ArchitecturalDecision
    failure_handling: ArchitecturalDecision
    idempotency: ArchitecturalDecision
    consistency_strategy: ArchitecturalDecision


class SelectionOutput(SelectionCore, SelectionDecisionsA, SelectionDecisionsB):
    """Merged shape -- everything downstream code should read from."""
    pass


def _requirement_to_prose(requirement: dict) -> str:
    """Prose, not raw JSON -- avoids the model echoing input structure back."""
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
        f"Expected scale: {requirement.get('expected_scale', 'unknown')}. "
        f"Peak traffic: {requirement.get('peak_traffic', 'unknown')}. "
        f"Data growth: {requirement.get('data_growth', 'unknown')}. "
        f"Latency requirement: {requirement.get('latency_requirement', 'unstated')}. "
        f"Availability requirement: {requirement.get('availability_requirement', 'unstated')}. "
        f"Transaction requirements: {requirement.get('transaction_requirements', 'unstated')}. "
        f"Idempotency requirements: {requirement.get('idempotency_requirements', 'none identified')}. "
        f"Pagination requirements: {requirement.get('pagination_requirements', 'none identified')}. "
        f"Lifecycle requirements: {requirement.get('lifecycle_requirements', 'none identified')}."
    )


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


def build_queries(requirement: dict) -> list[str]:
    """One shared retrieval pass, reused by all three calls (core +
    decisions A + decisions B) -- avoids retrieving three times for what
    is fundamentally one reasoning task split across calls."""
    entities = ", ".join(requirement.get("entities", [])) or "the application's data"

    queries = [
        f"database consistency {requirement.get('consistency', '')} "
        f"concurrency {requirement.get('concurrency', '')} transactions",
        f"workload {requirement.get('workload', '')} "
        f"read/write ratio {requirement.get('read_write_ratio', '')}",
    ]

    if requirement.get("critical_invariant"):
        queries.append(f"preventing violation of: {requirement['critical_invariant']}")

    if requirement.get("search_required"):
        queries.append("full-text search architecture search-required applications")

    queries.append(f"which database fits an application with entities: {entities}")

    queries.append(
        f"read replica and replication strategy for read/write ratio "
        f"{requirement.get('read_write_ratio', '')} and peak traffic "
        f"{requirement.get('peak_traffic', 'unknown')}"
    )
    queries.append(
        f"when is partitioning or sharding justified for scale "
        f"{requirement.get('expected_scale', 'unknown')} and data growth "
        f"{requirement.get('data_growth', 'unknown')}"
    )
    queries.append(
        f"caching strategy cache invalidation for read/write ratio "
        f"{requirement.get('read_write_ratio', '')} and workload "
        f"{requirement.get('workload', '')}"
    )
    queries.append(
        "pagination strategy offset cursor keyset pagination for list queries"
    )
    queries.append(
        f"idempotency retries duplicate request handling for "
        f"{requirement.get('critical_invariant', 'write operations')}"
    )
    queries.append(
        f"failure handling backup recovery RPO RTO for availability "
        f"{requirement.get('availability_requirement', 'unstated')}"
    )

    return queries


def retrieve_context(requirement: dict) -> list:
    """Round-robin across all queries' top results rather than filling
    from query 1's results first -- guarantees diversity across all 11
    topic areas instead of letting the first couple queries' hits crowd
    out the rest."""
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(
        str(VECTORSTORE_DIR), embeddings, allow_dangerous_deserialization=True
    )

    queries = build_queries(requirement)
    seen_sources_and_offsets = set()
    collected = []

    per_query_results = [vectorstore.similarity_search(q, k=CHUNKS_PER_QUERY) for q in queries]

    for round_idx in range(CHUNKS_PER_QUERY):
        for results in per_query_results:
            if round_idx >= len(results):
                continue
            doc = results[round_idx]
            key = (doc.metadata.get("source"), doc.page_content[:80])
            if key in seen_sources_and_offsets:
                continue
            seen_sources_and_offsets.add(key)
            collected.append(doc)
            if len(collected) >= MAX_TOTAL_CHUNKS:
                return collected

    return collected


def format_context(chunks: list) -> str:
    parts = []
    for doc in chunks:
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Source: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


REQUIRED_DECISION_KEYS = ["decision", "reason", "evidence", "trade_off"]


def _salvage_object(obj: dict, required_keys: list[str], label: str) -> dict:
    missing = [k for k in required_keys if k not in obj]
    if not missing:
        return obj
    print(f"    [salvage] {label} missing {missing}: {obj}")
    for key in missing:
        candidate_key = None
        for k, v in obj.items():
            if k in required_keys:
                continue
            if isinstance(v, str) and v.strip():
                candidate_key = k
                break
        if candidate_key is not None:
            obj[key] = obj.pop(candidate_key).strip()
            print(f"    [salvage] recovered '{key}' from stray key '{candidate_key}'")
        else:
            obj[key] = ""
            print(f"    [salvage] no recoverable value for '{key}', set to empty string")
    return obj


def _repair_and_validate_group(raw: dict, expected_keys: list[str], model_cls):
    missing_top_level = [k for k in expected_keys if k not in raw]
    if missing_top_level:
        raise ValueError(f"model omitted top-level key(s) entirely: {missing_top_level}")
    for key in expected_keys:
        if isinstance(raw.get(key), dict):
            _salvage_object(raw[key], REQUIRED_DECISION_KEYS, key)
    return model_cls(**raw)


# ---------------------------------------------------------------------------
# LLM calls
# ---------------------------------------------------------------------------

def _call_llm(system_prompt: str, user_message: str, label: str, num_predict: int) -> str:
    start = time.time()
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        think=False,
        format="json",
        options={
            "temperature": 0,
            "num_predict": num_predict,
            "num_ctx": NUM_CTX,
        },
    )
    elapsed = time.time() - start
    raw = _strip_code_fences(response["message"]["content"])
    print(f"  [{label}] {elapsed:.1f}s, eval_count={response.get('eval_count')}, "
          f"done_reason={response.get('done_reason')}")
    if response.get("done_reason") == "length":
        print(f"  [{label}] WARNING: hit num_predict cap ({num_predict}), output may be truncated")
    if response.get("eval_count") is None:
        print(f"  [{label}] WARNING: eval_count/done_reason are None -- possible context-window "
              f"overflow (num_ctx={NUM_CTX}) or an aborted generation, not a normal stop")
    return raw


def _run_group_call(system_prompt: str, user_message: str, label: str, expected_keys: list[str],
                     model_cls, num_predict: int, max_retries: int = 2):
    last_error = None
    for attempt in range(1, max_retries + 2):
        raw = _call_llm(system_prompt, user_message, f"{label} attempt {attempt}", num_predict)
        try:
            parsed = json.loads(raw)
            return _repair_and_validate_group(parsed, expected_keys, model_cls)
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            last_error = e
            print(f"  [{label} attempt {attempt}] failed: {e}")
            debug_path = f"selection_{label.replace('-', '_')}_failure_attempt{attempt}.txt"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(raw)
            print(f"  [{label} attempt {attempt}] full raw output written to {debug_path}")
    raise RuntimeError(f"{label} failed after {max_retries + 1} attempts. Last error: {last_error}")


@traceable(name="selection_agent", run_type="chain")
def run_selection_agent(requirement: dict, max_retries: int = 2) -> SelectionOutput:
    chunks = retrieve_context(requirement)
    context_text = format_context(chunks)

    print(f"  Retrieved {len(chunks)} unique chunks from {len(build_queries(requirement))} queries")
    for doc in chunks:
        print(f"    - {doc.metadata.get('source')}")

    req_prose = _requirement_to_prose(requirement)

    core_user_message = (
        f"Requirement summary:\n{req_prose}\n\n"
        f"Retrieved reference material:\n{context_text}"
    )
    core = None
    last_error = None
    for attempt in range(1, max_retries + 2):
        raw = _call_llm(CORE_SYSTEM_PROMPT, core_user_message, f"core attempt {attempt}", num_predict=1200)
        try:
            core = SelectionCore(**json.loads(raw))
            break
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            print(f"  [core attempt {attempt}] failed: {e}")
            debug_path = f"selection_core_failure_attempt{attempt}.txt"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(raw)
            print(f"  [core attempt {attempt}] full raw output written to {debug_path}")
            continue
    if core is None:
        raise RuntimeError(f"Selection Agent (core) failed after {max_retries + 1} attempts. Last error: {last_error}")

    decisions_user_message = (
        f"Requirement summary:\n{req_prose}\n\n"
        f"Chosen primary database: {core.primary_database}\n"
        f"Reasoning for that choice: {core.primary_reasoning}\n\n"
        f"Retrieved reference material:\n{context_text}"
    )

    decisions_a = _run_group_call(
        DECISIONS_PROMPT_A, decisions_user_message, "decisions-A",
        DECISIONS_GROUP_A_KEYS, SelectionDecisionsA, num_predict=1500, max_retries=max_retries,
    )
    decisions_b = _run_group_call(
        DECISIONS_PROMPT_B, decisions_user_message, "decisions-B",
        DECISIONS_GROUP_B_KEYS, SelectionDecisionsB, num_predict=1500, max_retries=max_retries,
    )

    required_components = [c.component for c in core.supporting_components if c.required]
    architecture_summary = core.primary_database
    if required_components:
        architecture_summary += " + " + " + ".join(required_components)
    core.architecture_summary = architecture_summary

    return SelectionOutput(**core.model_dump(), **decisions_a.model_dump(), **decisions_b.model_dump())


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
        "peak_traffic": "unknown",
        "data_growth": "unknown",
        "latency_requirement": "unstated",
        "availability_requirement": "unstated",
        "transaction_requirements": "atomic seat booking",
        "idempotency_requirements": "none identified",
        "pagination_requirements": "none identified",
        "lifecycle_requirements": "none identified",
    }
    result = run_selection_agent(example_requirement)
    print(json.dumps(result.model_dump(), indent=2))