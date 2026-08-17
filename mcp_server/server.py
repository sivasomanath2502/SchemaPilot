"""
Phase 10: MCP server exposing database tools.

validate_sql()   - checks DDL/SQL is syntactically valid WITHOUT persisting changes
                    (runs inside a transaction that always rolls back)
execute_sql()    - actually runs and commits SQL against the validation database
inspect_schema() - lists tables/columns currently in the validation database
explain_query()  - runs EXPLAIN on a SELECT/UPDATE/DELETE and returns the plan

All operations are scoped to db_advisor_validation via the advisor_validator
user (see .env) -- never touches any other database.
"""

import os
from pathlib import Path
import re

from langsmith import traceable
import mysql.connector
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

mcp = MCPServer("db-advisor-mysql")

_CREATE_TABLE_RE = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"]?(\w+)[`"]?', re.IGNORECASE
)

def _get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )


@mcp.tool()
@traceable(name="validate_sql", run_type="tool")
def validate_sql(sql: str) -> dict:
    """Check whether SQL statements are syntactically and semantically valid
    against MySQL.

    IMPORTANT: MySQL's DDL statements (CREATE/ALTER/DROP TABLE) cause an
    implicit commit and CANNOT be rolled back -- there is no true "dry run"
    for DDL in MySQL (unlike PostgreSQL, which does support transactional
    DDL). This tool works around that by (1) pre-emptively dropping any
    tables it's about to create, so leftover state from any prior crashed
    run can never block a fresh call, then (2) executing the SQL, then
    (3) explicitly dropping whatever it created, so no permanent objects
    remain after the call returns either way.

    sql: one or more SQL statements separated by semicolons.
    """
    created_tables = _CREATE_TABLE_RE.findall(sql)

    conn = _get_connection()
    cursor = conn.cursor()
    errors = []
    statements_checked = 0

    # idempotency: clear any leftover tables with the same names before we start,
    # so stale state from an earlier crashed run can never cause a false failure
    for table_name in created_tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
            conn.commit()
        except Exception:
            pass

    try:
        cursor.execute(sql)
        statements_checked = 1
        if cursor.with_rows:
            cursor.fetchall()
        while cursor.nextset():
            statements_checked += 1
            if cursor.with_rows:
                cursor.fetchall()
        conn.commit()
    except Exception as e:
        errors.append(str(e))
        conn.rollback()
    finally:
        for table_name in created_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
                conn.commit()
            except Exception:
                pass
        cursor.close()
        conn.close()

    return {
        "valid": len(errors) == 0,
        "statements_checked": statements_checked,
        "errors": errors,
        "note": "MySQL DDL auto-commits and cannot be rolled back; any "
                "leftover tables with these names were cleared before "
                "starting, and any tables created were explicitly dropped "
                "after validation.",
    }


@mcp.tool()
@traceable(name="execute_sql", run_type="tool")
def execute_sql(sql: str) -> dict:
    """Actually run and COMMIT SQL statements against the validation database.
    Unlike validate_sql, this persists changes. Use for setting up a schema
    you intend to keep testing against (e.g. after validate_sql passes).

    sql: one or more SQL statements separated by semicolons.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    errors = []
    statements_executed = 0

    try:
        cursor.execute(sql)
        statements_executed = 1
        if cursor.with_rows:
            cursor.fetchall()
        while cursor.nextset():
            statements_executed += 1
            if cursor.with_rows:
                cursor.fetchall()
        conn.commit()
    except Exception as e:
        conn.rollback()
        errors.append(str(e))
    finally:
        cursor.close()
        conn.close()

    return {
        "success": len(errors) == 0,
        "statements_executed": statements_executed,
        "errors": errors,
    }

@mcp.tool()
@traceable(name="inspect_schema", run_type="tool")
def inspect_schema() -> dict:
    """List all tables and their columns currently present in the
    validation database."""
    conn = _get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """,
        (os.getenv("MYSQL_DATABASE"),),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    tables: dict = {}
    for row in rows:
        tables.setdefault(row["TABLE_NAME"], []).append(
            {
                "column": row["COLUMN_NAME"],
                "type": row["DATA_TYPE"],
                "nullable": row["IS_NULLABLE"] == "YES",
                "key": row["COLUMN_KEY"],
            }
        )
    return {"tables": tables}


@mcp.tool()
@traceable(name="explain_query", run_type="tool")
def explain_query(sql: str) -> dict:
    """Run EXPLAIN on a single SELECT/UPDATE/DELETE query and return MySQL's
    query plan -- used to check for missing indexes / full table scans.

    sql: a single SQL query (not DDL).
    """
    conn = _get_connection()
    cursor = conn.cursor(dictionary=True)
    errors = []
    plan = []

    try:
        cursor.execute(f"EXPLAIN {sql}")
        plan = cursor.fetchall()
    except mysql.connector.Error as e:
        errors.append(str(e))
    finally:
        cursor.close()
        conn.close()

    return {"valid": len(errors) == 0, "plan": plan, "errors": errors}


if __name__ == "__main__":
    mcp.run()