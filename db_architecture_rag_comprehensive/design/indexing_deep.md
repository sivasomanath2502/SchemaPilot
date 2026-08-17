# Indexing — Deep Explanation

## Definition
An index is an auxiliary data structure that helps the database find rows without scanning the entire table for suitable query patterns.

## Common purposes
- equality lookups
- range queries
- joins
- sorting
- uniqueness
- pagination

## Composite indexes
A composite index contains multiple columns. Column order matters because it determines which query predicates can efficiently use the index.

Example:
Query: `WHERE user_id=? ORDER BY created_at DESC LIMIT 20`
Candidate: `(user_id, created_at)`

## Selectivity
Selectivity describes how well a predicate narrows the result set. Low-selectivity columns are not automatically useless; their value depends on the full query and index design.

## Covering index
An index may contain enough information for a query to be answered without fetching the full table row. This can reduce I/O but increases index size.

## Costs
Indexes consume storage/memory and add work to inserts, updates and deletes.

## Over-indexing
Adding an index for every column or query creates maintenance cost and can confuse optimization.

## Validation
Use query plans such as EXPLAIN and real workload measurements when available.

## Review rule
Every important index should answer: "Which query does this improve, and what is the expected trade-off?"
