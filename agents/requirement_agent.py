"""
Phase 6: Requirement Agent.

Converts a natural-language application description into a structured
workload representation (JSON), which downstream agents consume.

Uses the raw `ollama` Python client directly rather than langchain_ollama's
ChatOllama — there are open bugs in langchain-ollama where `reasoning=False`
doesn't reliably disable Qwen3's thinking mode, which silently burned 4-5
minutes per call on hidden reasoning tokens during testing. The raw client's
think=False is honored correctly and verified fast.
"""

import json
import re
import time

import ollama
from pydantic import BaseModel, Field, ValidationError
from langsmith import traceable
MODEL_NAME = "qwen3:4b"

SYSTEM_PROMPT = """You are a Requirement Analysis Agent for a database architecture advisor.

Given a natural-language application description, extract a structured workload
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
  "expected_scale": "<short free-text estimate, e.g. 'thousands of users' or 'unknown'>"
}

Only output the JSON object.
"""


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


def _strip_code_fences(text: str) -> str:
    """Defensive: strip stray <think> tags or markdown fences if they leak through."""
    text = text.strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text

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
            options={"temperature": 0},
        )
        elapsed = time.time() - start
        raw = _strip_code_fences(response["message"]["content"])
        print(f"  [attempt {attempt}] {elapsed:.1f}s, eval_count={response.get('eval_count')}")

        try:
            data = json.loads(raw)
            return RequirementOutput(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            print(f"  [attempt {attempt}] failed to parse/validate: {e}")
            print(f"  raw output was: {raw[:300]}")
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