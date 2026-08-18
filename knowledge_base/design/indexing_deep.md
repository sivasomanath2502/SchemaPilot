# Indexing — Deep Explanation

## Definition
An index is an auxiliary data structure that helps the database find rows without scanning the entire table for a given query pattern. It trades extra storage and write overhead for faster reads on specific access paths.

## Why it exists
Without an index, satisfying `WHERE user_id = ?` requires scanning every row (a full table scan) to check which ones match — fine for a few hundred rows, prohibitively slow at millions. An index (commonly a B-tree) lets the database jump directly to matching rows.

## Common purposes
- equality lookups (`WHERE id = ?`)
- range queries (`WHERE created_at > ?`)
- joins (matching foreign keys efficiently)
- sorting (`ORDER BY` can use an index's existing order instead of sorting in memory)
- enforcing uniqueness
- supporting pagination (see `pagination_deep.md`)

## How to decide what to index
Analyze real query patterns, not the schema in isolation:
- WHERE clauses (equality and range filters)
- JOIN conditions
- ORDER BY columns
- uniqueness requirements
- frequency of the query (a rare admin report doesn't justify the same investment as a hot user-facing query)
- selectivity of the column

## Selectivity
Selectivity describes how well a predicate narrows the result set. A column like `status` with only 3 possible values is low-selectivity — an index on it alone rarely helps much, since a query still matches a large fraction of rows. A column like `email` is high-selectivity — an index narrows results dramatically. Low-selectivity columns aren't automatically useless, though: their value depends on the full query and index design (e.g. as a secondary column in a composite index).

## Composite indexes
A composite index spans multiple columns, and **column order matters** — it determines which query predicates can efficiently use the index (leftmost-prefix rule: an index on `(a, b, c)` can serve queries filtering on `a`, on `a and b`, or on `a and b and c`, but not efficiently on `b` alone).

Example:
Query: `WHERE user_id = ? ORDER BY created_at DESC LIMIT 20`
Candidate index: `(user_id, created_at)` — the equality column first, then the sort column.

## Covering index
An index may contain enough columns that a query can be answered entirely from the index, without fetching the full table row (no extra I/O to the table itself). This can meaningfully reduce I/O but increases index size and write cost, since more columns must be kept updated in the index.

## Costs
Every index:
- consumes additional storage
- must be updated on every INSERT/UPDATE/DELETE affecting its columns, slowing writes
- adds planning overhead for the query optimizer choosing between multiple indexes

## Over-indexing
Adding an index for every column, or defensively indexing "just in case," is a common mistake. It raises write cost and storage without proportional read benefit, and can even confuse the query optimizer into choosing a worse plan. Every index recommendation should be traceable to a concrete, real query.

## When NOT to add an index
- The table is small enough that a full scan is cheap regardless (a few hundred rows).
- The column is write-heavy and rarely queried by itself.
- A composite index already covers the access pattern — a redundant single-column index adds cost without benefit.

## Validation
Use the database's query plan tool (`EXPLAIN` in MySQL/PostgreSQL) to confirm an index is actually being used for a given query, rather than assuming from the schema alone. In this project, `explain_query()` via MCP performs this check against real MySQL.

## Common mistakes
- Indexing every column defensively.
- Wrong column order in a composite index (not matching the leftmost-prefix of actual queries).
- Adding an index but never verifying with EXPLAIN that it's actually used.
- Assuming an index on `status` alone will help when `status` has very few distinct values.
- Forgetting that indexes slow down writes — over-indexing a write-heavy table.

## Review questions
- Which specific query does this index improve?
- Is the column order in a composite index aligned with the leftmost-prefix of real queries?
- Has EXPLAIN confirmed the index is actually used?
- Does the write cost of maintaining this index outweigh its read benefit given the table's read/write ratio?

## Source / grounding
https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html
