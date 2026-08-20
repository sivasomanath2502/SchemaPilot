MySQL — Full Selection Profile

Role

Relational SQL database and a strong default candidate for transactional application systems.

Core Selection Summary

Definition: MySQL is a relational SQL database and a strong default candidate for transactional application systems.

Why it exists: It is designed for structured entities and relationships, transactional invariants, referential integrity, SQL joins and aggregations, and predictable CRUD workloads.

When to use: Prefer MySQL when structured relational data, strong transactional invariants, foreign-key integrity, and SQL query patterns dominate the workload.

When NOT to use: Do not select MySQL merely because it is familiar. Document-shaped flexible data, deep relationship traversal, dedicated relevance search, pure cache/key-value access, or embedded key-value storage may point to another system.

Primary selection rule: Select MySQL from the workload's consistency, query, data-model, scale, and operational requirements—not from familiarity or default preference alone.

Advantages: Mature relational modeling, transactions, constraints, joins, indexes, and a well-understood scaling progression.

Disadvantages: Some document, graph, search, cache, and embedded-storage workloads are better served by specialized systems; horizontal distribution can add complexity.

Review questions:

What business invariants must be transactional?

Are foreign keys and relational joins important?

What are the dominant query patterns?

Can simpler scaling steps satisfy the workload before sharding?

Is another database a materially better fit for the actual access pattern?

Data model

Tables, rows, columns, primary keys, foreign keys, unique constraints, indexes and transactions. InnoDB is the key engine to consider for ordinary transactional workloads.

Strong selection signals

Structured entities and relationships.

Strong transactional invariants.

Referential integrity.

SQL joins and aggregations.

Orders, payments, inventory, booking, accounting and user/account data.

Predictable operational CRUD.

Transaction and concurrency

Use transactions around business invariants. Examples:

reserve a seat and create a booking

decrement inventory and create an order

update payment and order state atomically

Concurrency can involve row locks, unique constraints, atomic updates and appropriate isolation levels.

Transaction Boundary

A MySQL transaction is sufficient to make the database operations inside its transaction boundary atomic and consistent according to the chosen isolation and constraint rules.

It is not automatically a transaction with an external service such as a payment provider, message broker, or third-party API.

External operations require their own failure, retry, idempotency, and reconciliation strategy when applicable.

Indexing

Design from actual queries. Consider WHERE, JOIN, ORDER BY, range predicates and composite access patterns. Validate with EXPLAIN. Indexes improve reads but add storage and write-maintenance cost.

Index Boundary

An index is sufficient to accelerate a query when its structure matches the query's actual access path and the resulting cost is justified.

An index does not replace a constraint or transaction. A performance optimization should not be treated as the mechanism that establishes business correctness.

Do not add indexes merely because a column is frequently mentioned; evaluate the actual query, selectivity, ordering, storage cost, and write-maintenance cost.

Scaling

Prefer:

Correct schema

Query optimization

Indexes

Vertical scaling

Read replicas/caching where justified

Partitioning for suitable large tables

Sharding only when simpler approaches cannot satisfy the workload

Scaling Boundary

The earlier scaling steps are sufficient when measured workload requirements can be met without distributing writes or data across shards.

Sharding is not required merely because traffic is high. It becomes a candidate when simpler approaches cannot satisfy the measured capacity, storage, or availability requirements.

Read replicas and caches improve read scaling but do not automatically solve primary-write contention.

Supporting systems

Redis can handle caching/session/rate-limiting workloads. OpenSearch can handle dedicated full-text/relevance search. These should normally remain derived/supporting systems when MySQL is the source of truth.

Supporting-System Boundary

Redis or OpenSearch is sufficient for a specialized workload when that workload's access pattern actually requires caching, low-latency key access, or dedicated search/relevance capabilities.

They are not additionally required for ordinary relational CRUD, transactions, joins, or integrity constraints that MySQL already satisfies.

When MySQL is the source of truth, supporting systems must not silently become authoritative for the transactional invariant.

Weak-fit signals

Document-shaped flexible data -> MongoDB.
Embedded KV storage engine -> RocksDB.
Deep relationship traversal -> Neo4j.
Dedicated search -> OpenSearch.
Pure cache/key-value -> Redis.

Selection warning

Do not recommend MySQL merely because it is familiar. Compare workload, consistency, query model, scale and operational complexity.

Source / grounding

https://dev.mysql.com/doc/refman/8.4/en/

Common Mistakes

Choosing MySQL solely because it is familiar.

Assuming a transaction includes external services.

Treating indexes as a substitute for constraints or transactional correctness.

Adding Redis or OpenSearch without a distinct workload requirement.

Sharding before simpler scaling steps have been measured.

Assuming read replicas solve primary-write contention.

Treating all workloads in an application as requiring the same consistency or query model.