"""
Phase 6 + Phase G (merged): Requirement Agent.

Converts a natural-language application description into a structured
requirement representation (JSON), which downstream agents consume.
Single call, single schema -- the two-call base/extended split was a
false-start (kept the old 9-field version alive alongside a new one for
no real reason); this is the one version going forward.

Uses the raw `ollama` Python client directly rather than langchain_ollama's
ChatOllama -- there are open bugs in langchain-ollama where `reasoning=False`
doesn't reliably disable Qwen3's thinking mode, which silently burned 4-5
minutes per call on hidden reasoning tokens during testing. The raw client's
think=False is honored correctly and verified fast.

Assumption-flagging: if the description doesn't state something (scale,
latency, availability, etc.), the agent must either mark that field
"unstated"/"unknown" or record an entry in "assumptions" explaining exactly
what it assumed and why -- never silently invent a confident-sounding value.
"""

import json
import re
import time

import ollama
from pydantic import BaseModel, Field, ValidationError
from langsmith import traceable

MODEL_NAME = "qwen3:4b"

SYSTEM_PROMPT = """You are a Requirement Analysis Agent for a database architecture advisor.

Given a natural-language application description, extract a structured requirement
representation. Respond with ONLY a JSON object — no explanation, no markdown
fences, no text before or after the JSON.

The JSON must have exactly these fields:
{
  "application": "<short name for the application>",
  "entities": ["<entity1>", "<entity2>", ...],
  "consistency": "<one of: strong, eventual, mixed>",
  "concurrency": "<one of: low, medium, high>",
  "critical_invariant": "<the single most important rule that must never be violated, or null>",
  "workload": "<one of: transactional, analytical, mixed>",
  "read_write_ratio": "<one of: read-heavy, write-heavy, balanced>",
  "search_required": <true or false>,
  "expected_scale": "<short free-text estimate, e.g. 'thousands of users' or 'unknown'>",
  "actors": [{"role": "<e.g. Customer>", "description": "<what this actor does>"}],
  "features": ["<feature1>", "<feature2>", ...],
  "read_operations": ["<e.g. search events>", ...],
  "write_operations": ["<e.g. create booking>", ...],
  "peak_traffic": "<short free-text estimate of peak load, or 'unknown'>",
  "data_growth": "<short free-text estimate of data growth over time, or 'unknown'>",
  "availability_requirement": "<short free-text, e.g. 'best-effort' or '99.9% uptime', or 'unstated'>",
  "latency_requirement": "<short free-text, e.g. 'sub-200ms reads', or 'unstated'>",
  "transaction_requirements": "<what must be atomic/transactional, or 'none beyond standard CRUD'>",
  "idempotency_requirements": "<which operations must be safe to retry, or 'none identified'>",
  "pagination_requirements": "<which lists need pagination and any ordering need, or 'none identified'>",
  "lifecycle_requirements": "<soft-delete, audit trail, or history needs, or 'none identified'>",
  "other_invariants": ["<any business rule besides the single critical_invariant already captured>"],
  "assumptions": [
    {"field": "<name of the field you had to assume rather than derive from the text>",
     "assumption": "<the value you assumed>",
     "reason": "<why you assumed it — e.g. 'not stated in the description'>"}
  ]
}

IMPORTANT: if the description does not state something (e.g. exact scale, latency
target, or whether an operation must be idempotent), do NOT silently invent a
confident-sounding value with no explanation. Either write "unstated"/"unknown"/
"none identified" for that field, OR make a reasonable assumption AND add an
entry to "assumptions" explaining exactly what you assumed and why.

Every entity object in "actors" MUST have both "role" and "description" keys.
Every entry in "assumptions" MUST have "field", "assumption", and "reason" keys.
Never omit a key on any array item, no matter how many items there are.

Only output the JSON object.
"""


class Actor(BaseModel):
    role: str
    description: str


class Assumption(BaseModel):
    field: str
    assumption: str
    reason: str


class RequirementOutput(BaseModel):
    application: str
    entities: list[str] = Field(default_factory=list)
    consistency: str
    concurrency: str
    critical_invariant: str | None = None
    workload: str
    read_write_ratio: str
    search_required: bool
    expected_scale: str
    actors: list[Actor] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    read_operations: list[str] = Field(default_factory=list)
    write_operations: list[str] = Field(default_factory=list)
    peak_traffic: str = "unknown"
    data_growth: str = "unknown"
    availability_requirement: str = "unstated"
    latency_requirement: str = "unstated"
    transaction_requirements: str = "none beyond standard CRUD"
    idempotency_requirements: str = "none identified"
    pagination_requirements: str = "none identified"
    lifecycle_requirements: str = "none identified"
    other_invariants: list[str] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)


def _strip_code_fences(text: str) -> str:
    """Defensive: strip stray <think> tags or markdown fences if they leak through."""
    text = text.strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


def _salvage_list_items(items: list, required_keys: list[str], list_label: str) -> list:
    """Same pattern as schema_agent.py: if qwen3:4b drops or mis-names a key on
    a later array item, try to recover the value from a stray key before
    falling back to an empty string. actors/assumptions are the two array-of-
    object fields here, so they're the ones at risk of this failure mode."""
    for item in items:
        if not isinstance(item, dict):
            continue
        missing = [k for k in required_keys if k not in item]
        if not missing:
            continue
        print(f"    [salvage] {list_label} item missing {missing}: {item}")
        for key in missing:
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


def _repair_and_validate(raw: dict) -> RequirementOutput:
    if "actors" in raw and isinstance(raw["actors"], list):
        _salvage_list_items(raw["actors"], ["role", "description"], "actors")
    if "assumptions" in raw and isinstance(raw["assumptions"], list):
        _salvage_list_items(raw["assumptions"], ["field", "assumption", "reason"], "assumptions")
    return RequirementOutput(**raw)


@traceable(name="requirement_agent", run_type="chain")
def run_requirement_agent(user_requirements: str, max_retries: int = 2) -> RequirementOutput:
    last_error = None
    for attempt in range(1, max_retries + 2):
        start = time.time()
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_requirements},
            ],
            think=False,
            format="json",
            options={"temperature": 0, "num_predict": 1500},
        )
        elapsed = time.time() - start
        raw = _strip_code_fences(response["message"]["content"])
        print(f"  [attempt {attempt}] {elapsed:.1f}s, eval_count={response.get('eval_count')}")

        try:
            data = json.loads(raw)
            return _repair_and_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            print(f"  [attempt {attempt}] failed to parse/validate: {e}")
            print(f"  raw output (last 300 chars): ...{raw[-300:]}")
            continue

    raise RuntimeError(
        f"Requirement Agent failed after {max_retries + 1} attempts. Last error: {last_error}"
    )


if __name__ == "__main__":
    example = (
        "Design a database for an online ticket booking system. Users should be able "
        "to search events, select seats and book tickets. Multiple users may try to "
        "book the same seat simultaneously. Double booking must never occur."
    )
    result = run_requirement_agent(example)
    print(json.dumps(result.model_dump(), indent=2))