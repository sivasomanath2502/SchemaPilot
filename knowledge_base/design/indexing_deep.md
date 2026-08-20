Indexing — Deep Explanation

Core Reasoning Summary

Definition: An index is an auxiliary data structure that can accelerate specific access paths by avoiding or reducing the need to scan the full table. It trades storage and write-maintenance cost for potential read benefit.

Why it exists: Indexes make repeated lookup, range, join, ordering, and uniqueness operations more efficient when the index matches the actual query pattern.

When to use: Add an index when a concrete workload contains a sufficiently important access path and the expected read benefit justifies the storage and write-maintenance cost.

When NOT to use: Do not add indexes defensively, index every column, or assume every filtered column needs its own index. Small tables, low-value queries, redundant indexes, and write-heavy workloads may not justify one.

Primary rule: An index is an optimization and, in the case of a unique index/constraint, can also enforce a specific uniqueness invariant. An index does not automatically make a query fast, guarantee that the optimizer will use it, or enforce unrelated business rules.

Advantages: Faster access for matching query patterns, efficient ordering/range access, and support for uniqueness enforcement.

Disadvantages: Extra storage, write overhead, maintenance cost, and possible plan/optimizer trade-offs.

Review questions:

Which exact query or invariant justifies this index?

Is the index order aligned with the real query?

Is the index redundant with an existing index?

Is the table large enough for the benefit to matter?

What is the read/write trade-off?

Has the actual query plan been checked?

Is the index being relied on for performance or for correctness?

An index is an auxiliary data structure that helps the database find rows without scanning the entire table for a given query pattern. It trades extra storage and write overhead for faster reads on specific access paths.

Why it exists

Without an index, satisfying WHERE user_id = ? may require scanning many or all rows to check which ones match. An index (commonly a B-tree) can let the database locate matching rows more efficiently.

Performance Boundary

An index provides a candidate access path; it does not guarantee that the database will use it or that using it will be faster than a scan.

The optimizer may choose a table scan when the table is small, the predicate is not selective, statistics favor a scan, or the indexed access path has a higher estimated cost.

Common purposes

equality lookups (WHERE id = ?)

range queries (WHERE created_at > ?)

joins (matching foreign keys efficiently)

sorting (ORDER BY can use an index's existing order instead of sorting in memory)

enforcing uniqueness

supporting pagination (see pagination_deep.md)

How to decide what to index

Analyze real query patterns, not the schema in isolation:

Index-Selection Boundary

A column appearing in WHERE, JOIN, or ORDER BY is a reason to evaluate an index, not proof that an index is required.

The decision must consider the complete query shape, selectivity, frequency, table size, existing indexes, read/write ratio, and optimizer behavior.

WHERE clauses (equality and range filters)

JOIN conditions

ORDER BY columns

uniqueness requirements

frequency of the query (a rare admin report doesn't justify the same investment as a hot user-facing query)

selectivity of the column

Selectivity

Selectivity describes how well a predicate narrows the result set. A column like status with only 3 possible values is low-selectivity — an index on it alone rarely helps much, since a query still matches a large fraction of rows. A column like email is high-selectivity — an index narrows results dramatically. Low-selectivity columns aren't automatically useless, though: their value depends on the full query and index design (e.g. as a secondary column in a composite index).

Composite indexes

A composite index spans multiple columns, and column order matters — it determines which query predicates can efficiently use the index (leftmost-prefix rule: an index on (a, b, c) can serve queries filtering on a, on a and b, or on a and b and c, but not efficiently on b alone).

Composite-Index Boundary

The leftmost-prefix rule is a selection guideline, not a statement that a query using b alone can never benefit from an index containing (a, b, c) under every database or query plan.

For this project, use the actual database's query plan to validate whether the chosen index supports the intended access path.

Example:
Query: WHERE user_id = ? ORDER BY created_at DESC LIMIT 20
Candidate index: (user_id, created_at) — the equality column first, then the sort column.

Covering index

An index may contain enough columns that a query can be answered entirely from the index, without fetching the full table row (no extra I/O to the table itself). This can meaningfully reduce I/O but increases index size and write cost, since more columns must be kept updated in the index.

Covering-Index Boundary

A covering index can avoid the need to fetch the base table for a query when the database can satisfy all required columns and predicates from the index.

It does not guarantee that the optimizer will choose an index-only/covering plan, and it does not eliminate the cost of maintaining the larger index.

Costs

Every index:

Cost Boundary

The benefit of an index must be evaluated against its maintenance cost. An index that improves one read query can still be a poor architectural choice if it materially increases write cost, storage, or operational complexity for a write-heavy workload.

consumes additional storage

must be updated on every INSERT/UPDATE/DELETE affecting its columns, slowing writes

adds planning overhead for the query optimizer choosing between multiple indexes

Over-indexing

Adding an index for every column, or defensively indexing "just in case," is a common mistake. It raises write cost and storage without proportional read benefit, and can even confuse the query optimizer into choosing a worse plan. Every index recommendation should be traceable to a concrete, real query.

When NOT to add an index

The table is small enough that a full scan is cheap regardless (a few hundred rows).

The column is write-heavy and rarely queried by itself.

A composite index already covers the access pattern — a redundant single-column index adds cost without benefit.

Validation

Use the database's query plan tool (EXPLAIN in MySQL/PostgreSQL) to confirm an index is actually being used for a given query, rather than assuming from the schema alone. In this project, explain_query() via MCP performs this check against real MySQL.

Validation Boundary

EXPLAIN validates the optimizer's chosen or estimated access plan for the tested query and environment. It does not prove that the index is optimal for every query, data distribution, or future workload.

Validation should therefore use representative queries and data, especially when the recommendation depends on selectivity, cardinality, or workload frequency.

Common mistakes

Indexing every column defensively.

Wrong column order in a composite index (not matching the leftmost-prefix of actual queries).

Adding an index but never verifying with EXPLAIN that it's actually used.

Assuming an index on status alone will help when status has very few distinct values.

Forgetting that indexes slow down writes — over-indexing a write-heavy table.

Review questions

Which specific query does this index improve?

Is the column order in a composite index aligned with the leftmost-prefix of real queries?

Has EXPLAIN confirmed the index is actually used?

Does the write cost of maintaining this index outweigh its read benefit given the table's read/write ratio?

Source / grounding

https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html

Common Review Mistakes

Treating an index as a guarantee of faster execution.

Assuming the optimizer must use an available index.

Adding an index merely because a column appears in a WHERE clause.

Treating low selectivity as an absolute prohibition on indexing.

Treating the leftmost-prefix rule as a guarantee about every possible query plan.

Assuming a covering index eliminates all index-maintenance cost.

Using EXPLAIN on one query and treating the result as proof for every workload.

Treating a unique index as a general business-rule enforcement mechanism.

Ignoring existing indexes and creating redundant ones.