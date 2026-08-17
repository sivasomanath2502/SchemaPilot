# MySQL — Full Selection Profile


## Role
Relational SQL database and a strong default candidate for transactional application systems.

## Data model
Tables, rows, columns, primary keys, foreign keys, unique constraints, indexes and transactions. InnoDB is the key engine to consider for ordinary transactional workloads.

## Strong selection signals
- Structured entities and relationships.
- Strong transactional invariants.
- Referential integrity.
- SQL joins and aggregations.
- Orders, payments, inventory, booking, accounting and user/account data.
- Predictable operational CRUD.

## Transaction and concurrency
Use transactions around business invariants. Examples:
- reserve a seat and create a booking
- decrement inventory and create an order
- update payment and order state atomically

Concurrency can involve row locks, unique constraints, atomic updates and appropriate isolation levels.

## Indexing
Design from actual queries. Consider WHERE, JOIN, ORDER BY, range predicates and composite access patterns. Validate with EXPLAIN. Indexes improve reads but add storage and write-maintenance cost.

## Scaling
Prefer:
1. Correct schema
2. Query optimization
3. Indexes
4. Vertical scaling
5. Read replicas/caching where justified
6. Partitioning for suitable large tables
7. Sharding only when simpler approaches cannot satisfy the workload

## Supporting systems
Redis can handle caching/session/rate-limiting workloads. OpenSearch can handle dedicated full-text/relevance search. These should normally remain derived/supporting systems when MySQL is the source of truth.

## Weak-fit signals
Document-shaped flexible data -> MongoDB.
Embedded KV storage engine -> RocksDB.
Deep relationship traversal -> Neo4j.
Dedicated search -> OpenSearch.
Pure cache/key-value -> Redis.

## Selection warning
Do not recommend MySQL merely because it is familiar. Compare workload, consistency, query model, scale and operational complexity.


## Source / grounding
https://dev.mysql.com/doc/refman/8.4/en/
