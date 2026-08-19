"""
Phase L: Deterministic ER diagram generation.

Parses the VALIDATED sql_ddl string from schema_agent_validated.py --
not the LLM-narrated "relationships" array. Those two can disagree:
in the ticket_booking run, transaction_strategy claimed a
UNIQUE(event_id, seat_id, user_id) constraint that isn't actually in
the DDL (review_agent caught this). The DDL is the ground truth the
MCP+MySQL validator already checked, so it's the only safe source
for a diagram meant to "remain consistent with the generated schema
and SQL" (spec Section 5).
"""

import re
from langsmith import traceable

def _parse_create_table(stmt: str) -> dict | None:
    m = re.search(r"CREATE TABLE\s+(\w+)\s*\((.*)\)\s*;?\s*$", stmt, re.S | re.I)
    if not m:
        return None
    table_name, body = m.group(1), m.group(2)

    parts, depth, current = [], 0, ""
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current.strip())

    columns, primary_key, foreign_keys, unique_constraints = [], [], [], []

    for part in parts:
        p = part.strip()
        pu = p.upper()

        if pu.startswith("PRIMARY KEY"):
            cols = re.findall(r"\((.*?)\)", p)
            if cols:
                primary_key.extend(c.strip() for c in cols[0].split(","))
            continue

        if pu.startswith("FOREIGN KEY"):
            fk = re.search(r"FOREIGN KEY\s*\((\w+)\)\s*REFERENCES\s+(\w+)\s*\((\w+)\)", p, re.I)
            if fk:
                foreign_keys.append({"column": fk.group(1), "ref_table": fk.group(2), "ref_column": fk.group(3)})
            continue

        if pu.startswith("UNIQUE"):
            cols = re.findall(r"\((.*?)\)", p)
            if cols:
                unique_constraints.append([c.strip() for c in cols[0].split(",")])
            continue

        col_match = re.match(r"(\w+)\s+([\w\(\),\s]+)", p)
        if col_match:
            col_name, col_def = col_match.group(1), col_match.group(2).strip()
            is_pk_inline = "PRIMARY KEY" in col_def.upper()
            columns.append({"name": col_name, "type": col_def})
            if is_pk_inline:
                primary_key.append(col_name)

    return {
        "table": table_name, "columns": columns,
        "primary_key": list(dict.fromkeys(primary_key)),
        "foreign_keys": foreign_keys, "unique_constraints": unique_constraints,
    }


def parse_ddl(sql_ddl: str) -> list[dict]:
    statements = [s.strip() for s in sql_ddl.split(";") if s.strip()]
    return [t for s in statements if (t := _parse_create_table(s + ";"))]


def generate_mermaid_er(sql_ddl: str) -> str:
    tables = parse_ddl(sql_ddl)
    lines = ["erDiagram"]

    for t in tables:
        fk_cols = {fk["column"] for fk in t["foreign_keys"]}
        lines.append(f"    {t['table']} {{")
        for col in t["columns"]:
            simple_type = re.split(r"[\s(]", col["type"])[0].lower()
            marker = "PK" if col["name"] in t["primary_key"] else ("FK" if col["name"] in fk_cols else "")
            lines.append(f"        {simple_type} {col['name']} {marker}".rstrip())
        lines.append("    }")

    for t in tables:
        for fk in t["foreign_keys"]:
            # FK column also covered by a single-column UNIQUE => 1:1, else 1:many.
            # Composite uniques (like seat_id+event_id here) can't be reduced to a
            # clean cardinality symbol -- that nuance belongs in the report's
            # prose Section 7, not forced into the diagram.
            is_1to1 = any(fk["column"] in uc and len(uc) == 1 for uc in t["unique_constraints"])
            rel = "||--||" if is_1to1 else "||--o{"
            lines.append(f'    {fk["ref_table"]} {rel} {t["table"]} : "{fk["column"]}"')

    return "\n".join(lines)

@traceable(name="er_diagram_agent", run_type="tool")
def run_er_diagram_agent(schema: dict) -> str:
    sql_ddl = schema.get("sql_ddl", "")
    if not sql_ddl:
        return "erDiagram\n    %% no sql_ddl in schema state"
    return generate_mermaid_er(sql_ddl)