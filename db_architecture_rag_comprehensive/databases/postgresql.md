# PostgreSQL — Full Selection Profile


## Role
Advanced relational SQL database with strong transactional semantics, constraints, indexes, rich data types and extensibility.

## Strong selection signals
- Complex SQL and query logic.
- Strong integrity constraints.
- Rich relational modeling.
- JSONB/semi-structured data while retaining relational structure.
- Specialized extensions such as geospatial workloads.

## Strengths
- SQL and relational integrity
- CTEs and window functions
- Recursive queries
- Multiple index types
- Rich data types
- Extension ecosystem

## MySQL comparison
Both are strong for OLTP. Prefer PostgreSQL only when a concrete requirement benefits from its capabilities. Do not claim a universal winner.

## Scaling
Use the same progression as other relational systems: schema/query/index optimization, vertical scaling, replication/read scaling, then partitioning or sharding where justified.

## Weak-fit signals
Primarily document-shaped workload -> MongoDB.
Deep relationship traversal -> Neo4j.
Search relevance -> OpenSearch.
Cache/session -> Redis.
Embedded storage engine -> RocksDB.


## Source / grounding
https://www.postgresql.org/docs/current/
