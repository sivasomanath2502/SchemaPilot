"""
Phase 7 + Phase H: Database Selection Agent.

Primary RAG consumer. Takes the Requirement Agent's structured output,
runs multiple targeted FAISS queries, and produces a structured database
recommendation with explicit alternative/rejection reasoning.

Phase H changes: consumes the richer Requirement Agent fields added in
Phase G (peak_traffic, latency_requirement, availability_requirement,
data_growth) so the primary/alternative reasoning is grounded in scale and
latency, not just consistency/concurrency/workload. Also adds two retrieval
queries covering replication and partitioning/sharding -- this is grounding
for the agent's reasoning, NOT a bias toward recommending them; the prompt
still explicitly requires justification and forbids adding them just
because the application "sounds large" (the anti_patterns_deep.md doc this
now also has a chance to retrieve makes that same point explicitly).
Added "architecture_summary" -- a one-line conclusion like "MySQL only" or
"MySQL + Redis", since downstream (Review Agent, and eventually the report)
wants that exact concise verdict rather than having to re-derive it from
primary_database + supporting_components every time.
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
MAX_TOTAL_CHUNKS = 10

SYSTEM_PROMPT = """You are a Database Selection Agent for a database architecture advisor.

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
Only output the JSON object.

A database must appear in only ONE of "alternatives" or "rejected" — never both.

Do NOT recommend a supporting component (Redis, OpenSearch, read replicas, partitioning,
sharding) merely because the application has many users or "sounds large." Only include
a supporting component in "supporting_components" if the retrieved context and the
stated requirements (workload, read/write pattern, latency, scale) actually justify it.
If the retrieved material discusses replication, partitioning, or sharding but the
requirements don't justify them yet, say so in "primary_reasoning" and leave them out
of "supporting_components" rather than adding them speculatively.
"""


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


class SelectionOutput(BaseModel):
    primary_database: str
    primary_reasoning: str
    architecture_summary: str = ""
    alternatives: list[Alternative] = Field(default_factory=list)
    supporting_components: list[SupportingComponent] = Field(default_factory=list)
    rejected: list[Rejected] = Field(default_factory=list)


def _requirement_to_prose(requirement: dict) -> str:
    """Prose, not raw JSON -- avoids the model echoing input structure back.
    Same lesson learned in Schema Agent (Phase 8), which apparently applies
    here too: this agent worked in isolated testing but failed under real
    pipeline conditions with different retrieved context.

    Phase H: now also surfaces peak_traffic, latency_requirement,
    availability_requirement, and data_growth -- these exist on the
    Requirement Agent's output since Phase G but were previously ignored
    here, so scale/latency-sensitive database choices had no grounding."""
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
        f"Availability requirement: {requirement.get('availability_requirement', 'unstated')}."
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
    """Turn the Requirement Agent's JSON into several targeted retrieval queries.

    Phase H additions: a replication query (grounds read-scaling reasoning
    for read-heavy/high-peak-traffic cases) and a partitioning/sharding
    query (grounds large-scale/high-growth reasoning) -- always run, since
    retrieving evidence about a topic is not the same as recommending it;
    the prompt above still requires justification before including either
    in supporting_components."""
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

    return queries


def retrieve_context(requirement: dict) -> list:
    """Run multiple targeted queries against FAISS, dedupe, cap total chunks."""
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(
        str(VECTORSTORE_DIR), embeddings, allow_dangerous_deserialization=True
    )

    queries = build_queries(requirement)
    seen_sources_and_offsets = set()
    collected = []

    for q in queries:
        results = vectorstore.similarity_search(q, k=CHUNKS_PER_QUERY)
        for doc in results:
            key = (doc.metadata.get("source"), doc.page_content[:80])
            if key in seen_sources_and_offsets:
                continue
            seen_sources_and_offsets.add(key)
            collected.append(doc)
            if len(collected) >= MAX_TOTAL_CHUNKS:
                break
        if len(collected) >= MAX_TOTAL_CHUNKS:
            break

    return collected


def format_context(chunks: list) -> str:
    parts = []
    for doc in chunks:
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Source: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


@traceable(name="selection_agent", run_type="chain")
def run_selection_agent(requirement: dict, max_retries: int = 2) -> SelectionOutput:
    chunks = retrieve_context(requirement)
    context_text = format_context(chunks)

    print(f"  Retrieved {len(chunks)} unique chunks from {len(build_queries(requirement))} queries")
    for doc in chunks:
        print(f"    - {doc.metadata.get('source')}")

    user_message = (
        f"Requirement summary:\n{_requirement_to_prose(requirement)}\n\n"
        f"Retrieved reference material:\n{context_text}"
    )

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
            options={"temperature": 0},
        )
        elapsed = time.time() - start
        raw = _strip_code_fences(response["message"]["content"])
        print(f"  [attempt {attempt}] {elapsed:.1f}s, eval_count={response.get('eval_count')}")

        try:
            data = json.loads(raw)
            return SelectionOutput(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            print(f"  [attempt {attempt}] failed to parse/validate: {e}")
            print(f"  raw output was: {raw[:400]}")
            continue

    raise RuntimeError(
        f"Selection Agent failed after {max_retries + 1} attempts. Last error: {last_error}"
    )


if __name__ == "__main__":
    # Feed in a requirement dict shaped like the current (Phase G) Requirement
    # Agent's actual output -- includes the new fields Phase H now consumes.
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
    }
    result = run_selection_agent(example_requirement)
    print(json.dumps(result.model_dump(), indent=2))