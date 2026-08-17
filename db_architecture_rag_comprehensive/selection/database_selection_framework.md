# Database Selection Framework


## Goal
Select the simplest architecture satisfying actual requirements.

## Step 1 — Data model
Structured relational -> MySQL/PostgreSQL.
Document-shaped -> MongoDB.
Key/value/cache -> Redis.
Embedded KV -> RocksDB.
Relationship traversal -> Neo4j.
Full-text/relevance -> OpenSearch.

## Step 2 — Business invariants
Identify operations that cannot tolerate inconsistency.

## Step 3 — Query model
Identify joins, document reads, key lookups, graph traversal, search and analytics.

## Step 4 — Workload
Estimate:
- read/write ratio
- requests/sec
- concurrency
- data size
- growth
- latency
- availability

## Step 5 — Operational constraints
Consider team skills, cost, deployment complexity and failure handling.

## Step 6 — Architecture
Select one primary database first. Add supporting databases only for distinct requirements.

## Step 7 — Alternatives
Always explain:
- winner
- runner-up
- why winner fits
- why runner-up loses for this requirement set
- assumptions
- trade-offs

## Complexity penalty
More databases mean more synchronization, monitoring, deployment, failure modes and operational burden.

## Uncertainty
If a missing requirement can change the decision, ask for it rather than inventing a confident answer.


## Source / grounding
Curated synthesis of the database-specific and design documents.
