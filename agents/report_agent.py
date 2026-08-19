"""
Phase M: Final 23-section report synthesis.

Deterministic assembly from accumulated GraphState -- no new LLM calls, per
the spec's explicit instruction that the 23 sections must be synthesized
from state, not independently generated. Every field referenced here is
taken from confirmed real output shapes (requirement_agent, selection_agent,
schema_agent_validated, review_agent, er_diagram_agent) observed across
actual pipeline runs, not assumed.
"""

from langsmith import traceable


DECISION_FIELDS = [
    "caching", "replication", "search", "partitioning", "sharding",
    "pagination", "failure_handling", "idempotency", "consistency_strategy",
]


def _decision_block(label: str, d: dict | None) -> str:
    if not d:
        return f"### {label}\nNot addressed by current pipeline output.\n"
    lines = [f"### {label}", f"**Decision:** {d.get('decision', 'unspecified')}"]
    lines.append(f"**Reason:** {d.get('reason', '')}")
    lines.append(f"**Evidence:** {d.get('evidence', '')}")
    if d.get("alternative"):
        lines.append(f"**Alternative considered:** {d['alternative']}")
        lines.append(f"**Why rejected:** {d.get('why_alternative_rejected', '')}")
    lines.append(f"**Trade-off:** {d.get('trade_off', '')}")
    return "\n".join(lines) + "\n"


def _issues_summary(review: dict) -> str:
    issues = review.get("issues", [])
    if not issues:
        return "No issues raised by the Review Agent."
    critical = [i for i in issues if i.get("severity") == "critical"]
    lines = []
    if critical:
        lines.append(
            f"**{len(critical)} critical issue(s) remain unresolved after the "
            f"revision loop.** These are reported honestly rather than hidden:\n"
        )
    for i in issues:
        lines.append(
            f"- **[{i.get('severity', '?').upper()}/{i.get('category', '?')}]** "
            f"{i.get('description', '')}\n  *Suggested fix:* {i.get('suggested_fix', '')}"
        )
    lines.append(f"\n**Overall assessment:** {review.get('overall_assessment', '')}")
    return "\n".join(lines)


def _all_trade_offs(selection: dict, schema: dict) -> str:
    lines = []
    for field in DECISION_FIELDS:
        d = selection.get(field)
        if d and d.get("trade_off"):
            lines.append(f"- **{field}:** {d['trade_off']}")
    if schema.get("transaction_strategy"):
        lines.append(
            "- **transactions:** strong consistency via database-level constraint "
            "enforcement trades write-time contention for correctness guarantees "
            "(see Section 18 for the specific strategy)."
        )
    return "\n".join(lines) or "No trade-offs recorded."

@traceable(name="report_agent", run_type="chain")
def run_report_agent(requirement: dict, selection: dict, schema: dict,
                      review: dict, er_diagram: str) -> dict:
    entities = schema.get("entities", [])
    relationships = schema.get("relationships", [])
    constraints = schema.get("constraints", [])
    indexes = schema.get("indexes", [])
    queries = schema.get("important_queries", [])
    assumptions = requirement.get("assumptions", [])

    sections = {}

    sections["1_requirements_scope"] = (
        f"**Application:** {requirement.get('application', 'unspecified')}\n\n"
        f"**Critical invariant:** {requirement.get('critical_invariant', 'none stated')}\n\n"
        f"**Other invariants:** {', '.join(requirement.get('other_invariants', [])) or 'none stated'}\n\n"
        f"**Features:** {', '.join(requirement.get('features', []))}\n\n"
        f"**Transaction requirements:** {requirement.get('transaction_requirements', 'unstated')}"
    )

    sections["2_scale"] = (
        f"**Expected scale:** {requirement.get('expected_scale', 'unknown')}\n"
        f"**Peak traffic:** {requirement.get('peak_traffic', 'unknown')}\n"
        f"**Data growth:** {requirement.get('data_growth', 'unknown')}\n\n"
        f"**Assumptions made (explicitly, not silently invented):**\n" +
        "\n".join(f"- {a.get('field')}: {a.get('assumption')} ({a.get('reason')})" for a in assumptions)
    )

    sections["3_features_roles"] = "\n".join(
        f"- **{a.get('role', 'User')}:** {a.get('description', '')}"
        for a in requirement.get("actors", [])
    ) or "No actors recorded."

    sections["4_read_vs_write"] = (
        f"**Workload:** {requirement.get('workload', 'unspecified')}\n"
        f"**Read/write ratio:** {requirement.get('read_write_ratio', 'unspecified')}\n\n"
        f"**Read operations:** {', '.join(requirement.get('read_operations', []))}\n"
        f"**Write operations:** {', '.join(requirement.get('write_operations', []))}"
    )

    sections["5_concurrency"] = (
        f"**Concurrency level:** {requirement.get('concurrency', 'unspecified')}\n\n"
        f"**Enforcement strategy:** {schema.get('transaction_strategy', 'unspecified')}\n\n"
        f"See Section 23 (Review Findings) for whether this enforcement was validated as sufficient."
    )

    sections["6_entities"] = "\n".join(
        f"- **{e.get('name')}:** {e.get('description', '')}" for e in entities
    ) or "No entities recorded."

    sections["7_relationships_cardinality"] = "\n".join(
        f"- {r.get('from')} → {r.get('to')} ({r.get('type')}): {r.get('description', '')}"
        for r in relationships
    ) or "No relationships recorded."

    sections["8_schema"] = (
        f"**Constraints:**\n" +
        "\n".join(f"- {c.get('type')} on {c.get('table')}({', '.join(c.get('columns', []))}): {c.get('description', '')}"
                  for c in constraints) +
        f"\n\n**Full DDL:**\n```sql\n{schema.get('sql_ddl', '')}\n```"
    )

    sections["9_sql_vs_nosql"] = (
        f"**Primary database:** {selection.get('primary_database', 'unspecified')}\n\n"
        f"**Reasoning:** {selection.get('primary_reasoning', '')}\n\n"
        f"**Alternatives considered:**\n" +
        "\n".join(f"- {a.get('database')}: {a.get('reasoning')}" for a in selection.get("alternatives", [])) +
        f"\n\n**Rejected:**\n" +
        "\n".join(f"- {r.get('database')}: {r.get('reason')}" for r in selection.get("rejected", []))
    )

    sections["10_important_queries"] = "\n".join(
        f"- **{q.get('description')}**\n  ```sql\n  {q.get('sql')}\n  ```" for q in queries
    ) or "No queries recorded."

    sections["11_indexes"] = "\n".join(
        f"- {i.get('table')}({', '.join(i.get('columns', []))}): {i.get('reason', '')}"
        for i in indexes
    ) or "No indexes recorded."

    sections["12_cache"] = _decision_block("Cache", selection.get("caching"))
    sections["13_replication"] = _decision_block("Replication", selection.get("replication"))
    sections["14_search"] = _decision_block("Search", selection.get("search"))
    sections["15_partitioning"] = _decision_block("Partitioning", selection.get("partitioning"))
    sections["16_sharding"] = _decision_block("Sharding", selection.get("sharding"))
    sections["17_pagination"] = _decision_block("Pagination", selection.get("pagination"))

    sections["18_transactions"] = (
        f"**Strategy:** {schema.get('transaction_strategy', 'unspecified')}"
    )

    sections["19_failure_handling"] = _decision_block("Failure Handling", selection.get("failure_handling"))
    sections["20_idempotency"] = _decision_block("Idempotency", selection.get("idempotency"))
    sections["21_consistency"] = _decision_block("Consistency", selection.get("consistency_strategy"))

    sections["22_final_architecture"] = (
        f"**Architecture summary:** {selection.get('architecture_summary', 'unspecified')}\n\n"
        f"**Supporting components:**\n" +
        "\n".join(f"- {c.get('component')} ({c.get('purpose')}, "
                  f"{'required' if c.get('required') else 'optional'})"
                  for c in selection.get("supporting_components", [])) +
        f"\n\n**ER Diagram:**\n```mermaid\n{er_diagram}\n```"
    )

    sections["23_trade_offs_and_review"] = (
        f"**Trade-offs across all decisions:**\n{_all_trade_offs(selection, schema)}\n\n"
        f"**Review findings:**\n{_issues_summary(review)}"
    )

    markdown = "\n\n---\n\n".join(
        f"## {i+1}. {name.split('_', 1)[1].replace('_', ' ').title()}\n\n{body}"
        for i, (name, body) in enumerate(sections.items())
    )

    return {
        "application": requirement.get("application", "unspecified"),
        "sections": sections,
        "markdown": markdown,
        "unresolved_critical_issues": len(
            [i for i in review.get("issues", []) if i.get("severity") == "critical"]
        ),
    }