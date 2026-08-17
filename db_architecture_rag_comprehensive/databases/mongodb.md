# MongoDB — Full Selection Profile


## Role
Document-oriented database storing BSON documents in collections.

## Strong selection signals
- Data is naturally document-shaped.
- Nested data is commonly read together.
- Attributes vary substantially.
- Schema evolution is frequent.
- Access patterns map cleanly to document boundaries.
- Horizontal scaling is important.

## Modeling
Embedding is useful when related data is bounded and commonly accessed together. References are useful when data is shared, independently updated or unbounded.

Do not mechanically transform every relational table into a collection.

## Atomicity and transactions
A single-document model can make related updates atomic by keeping them in one document. Multi-document transactions are available, but they introduce coordination cost and should not replace thoughtful schema design.

## Indexing
Index common query/filter/sort paths. Composite indexes should match real access patterns. Every index has storage and write cost.

## Scaling
Sharding is a first-class capability. The shard key must be evaluated for cardinality, distribution, hotspots and query routing.

## Weak-fit signals
Complex relational joins and strict relational integrity -> MySQL/PostgreSQL.
Deep graph traversal -> Neo4j.
Dedicated search/relevance -> OpenSearch.
Embedded storage -> RocksDB.


## Source / grounding
https://www.mongodb.com/docs/
