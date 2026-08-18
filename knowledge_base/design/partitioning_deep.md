# Partitioning — Deep Explanation

(For replication, see `replication_deep.md`. For sharding, see `sharding_deep.md`. This document covers partitioning specifically, and the escalation order across all three at the end.)

## Definition
Partitioning divides one logical table into multiple physical segments **within the same database instance**, based on a partitioning key. Unlike sharding, all partitions still live on the same server and are managed by the same database engine — partitioning is a storage/query-optimization technique, not a horizontal-scaling technique across nodes.

## Why it exists
A very large table can become slow to scan, back up, or maintain (e.g. rebuilding an index) even on capable hardware, especially when queries only ever touch a recent or specific subset of the data. Partitioning lets the database skip irrelevant partitions entirely for a given query (partition pruning) and manage large tables in smaller physical chunks.

## How it works — partition pruning
If a table is partitioned by `created_at` (monthly ranges) and a query filters `WHERE created_at >= '2026-01-01'`, the database can skip scanning partitions for all earlier months entirely — this is partition pruning, and it's the main performance benefit.

## Partitioning types
- **Range partitioning** — rows are placed by a value range (e.g. `created_at` by month/year). Good fit for time-series or naturally ordered data, and for archival/retention (dropping an old partition is far cheaper than a bulk DELETE).
- **List partitioning** — rows are placed by an explicit set of values (e.g. `region IN ('US', 'EU', 'APAC')`). Good fit when a column has a small, known set of categories that queries commonly filter by.
- **Hash partitioning** — a hash function distributes rows relatively evenly across a fixed number of partitions. Useful when there's no natural range/list split but you still want to break up a huge table for maintenance purposes.

## Example
A `bookings` table partitioned by `RANGE (YEAR(created_at))`:
```
bookings_2024, bookings_2025, bookings_2026
```
A query for "bookings this year" only scans the current year's partition. Archiving old bookings becomes `DROP PARTITION bookings_2024` instead of a slow, lock-heavy `DELETE`.

## When partitioning helps
- A single table has grown large enough that full scans, index maintenance, or backups are noticeably slow.
- Queries naturally filter on the partitioning key (date ranges, region, tenant), so pruning actually applies.
- Data lifecycle naturally isolates subsets — old data can be archived/dropped by partition rather than row-by-row.

## When NOT to partition
- The table is not actually large enough for scan/maintenance cost to matter yet.
- Queries don't filter on a column that could serve as a sensible partition key — partitioning without pruning benefit adds complexity for no gain.
- The real problem is a missing index, not table size — check indexing first (see `indexing_deep.md`).

## Partitioning vs sharding — the key distinction
Partitioning splits a table into pieces **on one server**; it does not increase total CPU/RAM/disk capacity across nodes. Sharding splits data **across multiple servers**, which does increase aggregate capacity but adds real operational complexity (routing, cross-shard queries, rebalancing — see `sharding_deep.md`). Partitioning is almost always the simpler, lower-risk step to try first if the actual problem is single-table size or maintenance cost, rather than total server capacity.

## Trade-offs
- Cheap to introduce relative to sharding — no application-level routing logic needed, the database handles it internally.
- Only helps if queries align with the partition key; queries that don't filter on it may need to scan all partitions (no pruning benefit, sometimes even a small overhead).
- Some constraints and indexes may need to include the partitioning key depending on the database engine's rules (e.g. MySQL requires the partitioning key to be part of any unique key).

## Common mistakes
- Partitioning a table that isn't actually large enough to need it.
- Choosing a partition key that queries don't filter on, gaining no pruning benefit.
- Treating partitioning as a substitute for proper indexing.
- Confusing partitioning with sharding when discussing how a system will scale write capacity — partitioning does not add write capacity across nodes.

## Review questions
- Is the table actually large enough for partitioning to matter?
- Do the dominant queries filter on the proposed partition key (will pruning actually apply)?
- Is this solving a genuine scan/maintenance/archival problem, or is it being added for its own sake?
- Would a missing index solve the same problem more simply?

## Escalation path (partitioning, replication, sharding together)
When performance/scale concerns come up, evaluate techniques in this order — each is progressively more operationally complex:

1. Correct schema and query design
2. Proper indexing
3. Vertical scaling (more CPU/RAM/disk on one node)
4. Caching and/or read replicas (see `caching.md`, `replication_deep.md`) — replication helps read scaling and availability, but does not inherently increase write capacity
5. Partitioning (this document) — helps manage a large table's scan/maintenance cost on one node
6. Sharding (see `sharding_deep.md`) — only once a single node's total capacity, not just one table's manageability, is genuinely the bottleneck

Do not reach for partitioning or sharding simply because a user count or data volume "sounds large." Identify the actual bottleneck first.

## Source / grounding
https://dev.mysql.com/doc/refman/8.4/en/partitioning.html
