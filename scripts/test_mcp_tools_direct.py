# scripts/test_mcp_tools_direct.py
"""
Quick direct test of the MCP server's tool functions against real MySQL,
bypassing the MCP client/protocol layer entirely. Run this before wiring
up the full MCP client in Phase 11 -- proves the underlying SQL logic
works before adding protocol complexity on top.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp_server"))

from server import validate_sql, execute_sql, inspect_schema, explain_query

print("1. validate_sql with GOOD syntax (should be valid, no tables persisted):")
print(validate_sql("CREATE TABLE test_users (id INT PRIMARY KEY, name VARCHAR(50));"))

print("\n2. validate_sql with BAD syntax (should catch the error):")
print(validate_sql("CREATE TABLE test_bad (id INT PRIMARY, missing_type);"))

print("\n3. inspect_schema BEFORE execute_sql (should show no test_users table -- validate_sql never persisted):")
print(inspect_schema())

print("\n4. execute_sql (should actually create and persist the table):")
print(execute_sql("CREATE TABLE test_users (id INT PRIMARY KEY, name VARCHAR(50));"))

print("\n5. inspect_schema AFTER execute_sql (should now show test_users):")
print(inspect_schema())

print("\n6. explain_query on the new table:")
print(explain_query("SELECT * FROM test_users WHERE id = 1;"))

print("\n7. Cleanup:")
print(execute_sql("DROP TABLE test_users;"))