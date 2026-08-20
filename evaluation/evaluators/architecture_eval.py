"""
Metric C: 23-Section Architecture Quality Score.

Hybrid scorer per architecture_rubric.json -- deterministic checks read
directly from structured pipeline state (no LLM call, fully reproducible);
llm_judge checks call the model once per section to assess genuine
engineering-judgment questions (is this decision actually justified, not
just present). Never rewards technology count -- per spec Section 7,
"MySQL only" scores on justification quality, not on using fewer/more
components than an alternative design.

Also folds in Section 8 (ER diagram consistency) as part of the
"entities" section score, per the spec's instruction not to make it a
separate metric.
"""

import json
import re
from pathlib import Path

import ollama

RUBRIC_PATH = Path(__file__).resolve().parent.parent / "architecture_rubric.json"
MODEL_NAME = "qwen3:4b"


# ---------- deterministic checks ----------

def _score_requirements_scope(state: dict, weight: int) -> tuple[float, str]:
    req = state.get("requirement", {})
    ok = bool(req.get("critical_invariant")) and bool(req.get("features"))
    return (weight if ok else 0, "critical_invariant and features present" if ok else "missing critical_invariant or features")


def _score_scale(state: dict, weight: int) -> tuple[float, str]:
    """Per spec: don't require invented scale numbers -- score whether
    unstated fields are honestly flagged (assumptions present), not
    whether a specific number was guessed."""
    req = state.get("requirement", {})
    unstated_fields = ["expected_scale", "peak_traffic", "data_growth"]
    assumed = {a["field"] for a in req.get("assumptions", [])}
    sentinels = {"unknown", "unstated", "none identified"}
    honest = sum(
        1 for f in unstated_fields
        if str(req.get(f, "")).lower() in sentinels or f in assumed
    )
    ratio = honest / len(unstated_fields) if unstated_fields else 1
    return (round(weight * ratio, 2), f"{honest}/{len(unstated_fields)} scale fields honestly flagged")


def _score_features_roles(state: dict, weight: int) -> tuple[float, str]:
    actors = state.get("requirement", {}).get("actors", [])
    ok = len(actors) > 0 and all(a.get("role") and a.get("description") for a in actors)
    return (weight if ok else 0, f"{len(actors)} actor(s), all complete" if ok else "missing or incomplete actors")


def _score_read_vs_write(state: dict, weight: int) -> tuple[float, str]:
    req = state.get("requirement", {})
    ok = bool(req.get("read_operations")) and bool(req.get("write_operations"))
    return (weight if ok else 0, "read and write operations both present" if ok else "missing read or write operations")


def _score_concurrency(state: dict, weight: int) -> tuple[float, str]:
    """Deterministic proxy: does the Review Agent -- which explicitly checks
    the DDL against the critical invariant -- report zero CRITICAL
    concurrency issues, AND did the schema pass MySQL validation. Reuses
    Review Agent's own judgment rather than re-deriving it independently."""
    review = state.get("review", {})
    schema = state.get("schema", {})
    concurrency_critical = [
        i for i in review.get("issues", [])
        if i.get("category") == "concurrency" and i.get("severity") == "critical"
    ]
    validated = schema.get("validation", {}).get("final_valid", False)
    if not validated:
        return (0, "schema failed MySQL validation")
    if concurrency_critical:
        return (0, f"{len(concurrency_critical)} unresolved critical concurrency issue(s)")
    return (weight, "schema MySQL-validated, no unresolved critical concurrency issues")


def _parse_ddl_table_names(sql_ddl: str) -> set[str]:
    return {m.group(1) for m in re.finditer(r"CREATE\s+TABLE\s+(\w+)", sql_ddl, re.IGNORECASE)}


def _score_entities(state: dict, weight: int) -> tuple[float, str]:
    """Folds in Section 8 (ER diagram consistency) per spec instruction --
    not a separate metric. Checks schema entities exist AND that the ER
    diagram's table set matches the DDL's actual table set (protects
    against the ER generator drifting from a later-revised schema)."""
    schema = state.get("schema", {})
    entities = schema.get("entities", [])
    if not entities:
        return (0, "no entities defined")

    er_diagram = state.get("er_diagram", "")
    ddl_tables = _parse_ddl_table_names(schema.get("sql_ddl", ""))
    er_tables = set(re.findall(r"^\s*(\w+)\s*\{", er_diagram, re.MULTILINE))

    if not ddl_tables:
        return (weight * 0.5, "entities present but DDL unparseable for ER consistency check")

    consistent = ddl_tables == er_tables
    if consistent:
        return (weight, f"{len(entities)} entities; ER diagram matches DDL tables exactly ({len(ddl_tables)})")
    missing_from_er = ddl_tables - er_tables
    extra_in_er = er_tables - ddl_tables
    return (
        weight * 0.5,
        f"ER/DDL mismatch -- missing from ER: {missing_from_er or 'none'}, "
        f"extra in ER: {extra_in_er or 'none'}"
    )


def _score_relationships(state: dict, weight: int) -> tuple[float, str]:
    rels = state.get("schema", {}).get("relationships", [])
    ok = len(rels) > 0 and all(r.get("from") and r.get("to") and r.get("type") for r in rels)
    return (weight if ok else 0, f"{len(rels)} relationship(s), all complete" if ok else "missing or incomplete relationships")


def _score_schema(state: dict, weight: int) -> tuple[float, str]:
    """Fully deterministic and objective -- MySQL either validated the DDL
    or it didn't; no judgment needed."""
    validation = state.get("schema", {}).get("validation", {})
    ok = validation.get("final_valid", False)
    return (weight if ok else 0, f"MySQL validation: {'passed' if ok else 'FAILED'} ({validation.get('attempts', '?')} attempt(s))")


def _score_important_queries(state: dict, weight: int) -> tuple[float, str]:
    queries = state.get("schema", {}).get("important_queries", [])
    ok = len(queries) > 0
    return (weight if ok else 0, f"{len(queries)} important quer(y/ies)" if ok else "no important queries")


def _score_indexes(state: dict, weight: int) -> tuple[float, str]:
    """Cross-checks index columns actually appear in at least one important
    query's SQL -- catches indexes that don't match real access patterns,
    per the spec's own Review Agent checklist for this category."""
    schema = state.get("schema", {})
    indexes = schema.get("indexes", [])
    queries_sql = " ".join(q.get("sql", "") for q in schema.get("important_queries", [])).lower()
    if not indexes:
        return (0, "no indexes defined")
    matched = sum(
        1 for idx in indexes
        if any(col.lower() in queries_sql for col in idx.get("columns", []))
    )
    ratio = matched / len(indexes)
    return (round(weight * ratio, 2), f"{matched}/{len(indexes)} indexes match a column used in important_queries")


def _score_decision_presence(state: dict, field: str, weight: int) -> tuple[float, str]:
    """Used for pagination/transactions/failure_handling/idempotency/
    consistency -- deterministic presence+completeness check only. The
    JUSTIFICATION quality of these is not separately weighted heavily
    enough in the rubric to warrant an LLM call each; cache/replication/
    search/partitioning/sharding get the LLM-judged treatment instead
    since they're more prone to unjustified-complexity errors per spec."""
    d = state.get("selection", {}).get(field)
    if not d:
        return (0, f"no {field} decision recorded")
    required = ["decision", "reason", "evidence", "trade_off"]
    complete = all(d.get(k) for k in required)
    return (weight if complete else weight * 0.5, "complete" if complete else "missing one or more of decision/reason/evidence/trade_off")


def _score_transactions(state: dict, weight: int) -> tuple[float, str]:
    ok = bool(state.get("schema", {}).get("transaction_strategy"))
    return (weight if ok else 0, "transaction_strategy present" if ok else "no transaction_strategy")


def _score_trade_offs(state: dict, weight: int) -> tuple[float, str]:
    """Every one of the 9 selection decisions must have a non-empty
    trade_off -- per spec, every decision has one, even 'no X' choices."""
    selection = state.get("selection", {})
    fields = ["caching", "replication", "search", "partitioning", "sharding",
              "pagination", "failure_handling", "idempotency", "consistency_strategy"]
    present = [f for f in fields if selection.get(f)]
    with_tradeoff = [f for f in present if selection[f].get("trade_off")]
    ratio = len(with_tradeoff) / len(fields) if fields else 0
    return (round(weight * ratio, 2), f"{len(with_tradeoff)}/{len(fields)} decisions have a stated trade-off")


# ---------- LLM-judged checks ----------

def _llm_judge(prompt: str) -> tuple[float, str]:
    """Returns (score_0_to_1, reasoning). Single-call, low num_predict --
    this is a focused judgment, not a long analysis."""
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        think=False,
        format="json",
        options={"temperature": 0, "num_predict": 300},
    )
    raw = response["message"]["content"]
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    try:
        data = json.loads(raw)
        return float(data.get("score", 0)), data.get("reasoning", "")
    except (json.JSONDecodeError, ValueError):
        return 0.0, f"LLM judge returned unparseable output: {raw[:150]}"


JUDGE_PROMPT_TEMPLATE = """Score this architectural decision from 0.0 to 1.0 on
whether it is CORRECTLY JUSTIFIED given the stated requirements -- NOT on
whether it uses more or fewer technologies. A decision to NOT add a
component (Redis, OpenSearch, replicas, etc.) scores just as high as
adding one, IF the reasoning is sound given the requirements. Penalize
only: (a) a decision whose stated evidence contradicts or doesn't support
it, (b) added complexity with no real justification, (c) a clearly wrong
call given the requirements.

Requirements summary: {req_summary}

Decision under review ({decision_area}):
{decision_json}

Respond with ONLY JSON: {{"score": <0.0-1.0>, "reasoning": "<one sentence>"}}
"""


def _req_summary(req: dict) -> str:
    return (
        f"consistency={req.get('consistency')}, concurrency={req.get('concurrency')}, "
        f"workload={req.get('workload')}, read_write_ratio={req.get('read_write_ratio')}, "
        f"search_required={req.get('search_required')}, expected_scale={req.get('expected_scale')}, "
        f"peak_traffic={req.get('peak_traffic')}"
    )


def _score_decision_llm(state: dict, field: str, weight: int) -> tuple[float, str]:
    d = state.get("selection", {}).get(field)
    if not d:
        return (0, f"no {field} decision recorded")
    req_summary = _req_summary(state.get("requirement", {}))
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        req_summary=req_summary, decision_area=field, decision_json=json.dumps(d)
    )
    ratio, reasoning = _llm_judge(prompt)
    return (round(weight * ratio, 2), reasoning)


def _score_sql_vs_nosql(state: dict, weight: int) -> tuple[float, str]:
    selection = state.get("selection", {})
    req_summary = _req_summary(state.get("requirement", {}))
    prompt = f"""Score this database selection decision from 0.0 to 1.0 on
whether the primary database choice is well-justified given the requirements,
and whether the rejected alternatives are rejected for sound reasons (not
generic reasons that could apply to any database).

Requirements: {req_summary}

Primary database: {selection.get('primary_database')}
Reasoning: {selection.get('primary_reasoning')}
Rejected: {json.dumps(selection.get('rejected', []))}

Respond with ONLY JSON: {{"score": <0.0-1.0>, "reasoning": "<one sentence>"}}
"""
    ratio, reasoning = _llm_judge(prompt)
    return (round(weight * ratio, 2), reasoning)


def _score_final_architecture(state: dict, weight: int) -> tuple[float, str]:
    selection = state.get("selection", {})
    prompt = f"""Score this final architecture summary from 0.0 to 1.0 on
whether it is COHERENT -- does the architecture_summary match the actual
supporting_components listed, and is the overall shape sensible given
the primary database and components chosen? Do NOT reward more components
as inherently better.

Architecture summary: {selection.get('architecture_summary')}
Supporting components: {json.dumps(selection.get('supporting_components', []))}

Respond with ONLY JSON: {{"score": <0.0-1.0>, "reasoning": "<one sentence>"}}
"""
    ratio, reasoning = _llm_judge(prompt)
    return (round(weight * ratio, 2), reasoning)


# ---------- orchestration ----------

DETERMINISTIC_SCORERS = {
    "requirements_scope": _score_requirements_scope,
    "scale": _score_scale,
    "features_roles": _score_features_roles,
    "read_vs_write": _score_read_vs_write,
    "concurrency": _score_concurrency,
    "entities": _score_entities,
    "relationships_cardinality": _score_relationships,
    "schema": _score_schema,
    "important_queries": _score_important_queries,
    "indexes": _score_indexes,
    "pagination": lambda s, w: _score_decision_presence(s, "pagination", w),
    "transactions": _score_transactions,
    "failure_handling": lambda s, w: _score_decision_presence(s, "failure_handling", w),
    "idempotency": lambda s, w: _score_decision_presence(s, "idempotency", w),
    "consistency": lambda s, w: _score_decision_presence(s, "consistency_strategy", w),
    "trade_offs": _score_trade_offs,
}

LLM_JUDGE_SCORERS = {
    "sql_vs_nosql": _score_sql_vs_nosql,
    "cache": lambda s, w: _score_decision_llm(s, "caching", w),
    "replication": lambda s, w: _score_decision_llm(s, "replication", w),
    "search": lambda s, w: _score_decision_llm(s, "search", w),
    "partitioning": lambda s, w: _score_decision_llm(s, "partitioning", w),
    "sharding": lambda s, w: _score_decision_llm(s, "sharding", w),
    "final_architecture": _score_final_architecture,
}


def score_architecture(final_state: dict) -> dict:
    rubric = json.loads(RUBRIC_PATH.read_text())["sections"]
    results = []
    total_score = 0.0
    total_weight = 0

    for section in rubric:
        key, weight, method = section["key"], section["weight"], section["method"]
        scorer = DETERMINISTIC_SCORERS.get(key) if method == "deterministic" else LLM_JUDGE_SCORERS.get(key)
        if scorer is None:
            results.append({"section": key, "weight": weight, "method": method, "score": 0, "reasoning": "no scorer implemented"})
            continue
        score, reasoning = scorer(final_state, weight)
        results.append({"section": key, "weight": weight, "method": method, "score": score, "reasoning": reasoning})
        total_score += score
        total_weight += weight

    return {
        "total_score": round(total_score, 2),
        "max_possible": total_weight,
        "percentage": round(100 * total_score / total_weight, 1) if total_weight else 0,
        "per_section": results,
    }


if __name__ == "__main__":
    import sys
    # Usage: python architecture_eval.py path/to/saved_final_state.json
    state_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not state_path or not state_path.exists():
        print("Usage: python architecture_eval.py <path to a saved final_state JSON>")
        sys.exit(1)
    final_state = json.loads(state_path.read_text())
    result = score_architecture(final_state)
    print(json.dumps(result, indent=2))