"""
Phase 9: verify connectivity to the local MySQL validation database
before building the MCP server on top of it.

Run from the project root:
    python scripts/test_mysql_connection.py
"""

import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def main() -> None:
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }

    missing = [k for k, v in config.items() if v is None and k != "port"]
    if missing:
        raise RuntimeError(
            f"Missing .env values: {missing}. Check your .env file at project root."
        )

    print(f"Connecting to {config['user']}@{config['host']}:{config['port']}/{config['database']} ...")
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # sanity check: create, insert, select, drop -- proves the scoped user
    # actually has the privileges the MCP server will need
    cursor.execute("DROP TABLE IF EXISTS _connection_test;")
    cursor.execute("CREATE TABLE _connection_test (id INT PRIMARY KEY, note VARCHAR(50));")
    cursor.execute("INSERT INTO _connection_test VALUES (1, 'connection ok');")
    conn.commit()

    cursor.execute("SELECT * FROM _connection_test;")
    row = cursor.fetchone()
    print(f"  Round-trip read: {row}")

    cursor.execute("DROP TABLE _connection_test;")
    conn.commit()

    cursor.close()
    conn.close()
    print("MySQL connection, CREATE/INSERT/SELECT/DROP privileges: all OK")


if __name__ == "__main__":
    main()