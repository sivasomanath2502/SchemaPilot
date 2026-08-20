MongoDB — Full Selection Profile

Role

Document-oriented database storing BSON documents in collections.

Core Selection Summary

Definition: MongoDB is a document-oriented database in which application data is represented as BSON documents organized in collections.

Why it exists: It is a strong fit when the application's natural data boundaries are document-shaped, related data is commonly read together, attributes vary, and schema evolution is frequent.

When to use: Prefer MongoDB when access patterns map cleanly to document boundaries and the workload benefits from document-oriented modeling and horizontal scaling.

When NOT to use: Do not select MongoDB merely because the data is JSON-like. Complex relational joins, strict relational integrity, deep graph traversal, dedicated relevance search, or embedded key-value storage may point to another system.

Primary selection rule: Choose MongoDB because the workload and access patterns fit document modeling—not simply because MongoDB supports flexible schemas.

Advantages: Natural document modeling, flexible schema evolution, embedding of bounded related data, and first-class horizontal scaling capabilities.

Disadvantages: Poorly chosen document boundaries can create duplication or awkward updates; multi-document transactions add coordination cost; sharding requires careful shard-key design.

Review questions:

Is the data naturally document-shaped?

Which related data is always read or updated together?

Which relationships are shared, independently updated, or unbounded?

Does the workload actually benefit from document boundaries?

Would relational joins or strict integrity be a dominant requirement?

If sharding is needed, what are the cardinality, distribution, hotspot, and routing properties of the shard key?

Strong selection signals

Data is naturally document-shaped.

Nested data is commonly read together.

Attributes vary substantially.

Schema evolution is frequent.

Access patterns map cleanly to document boundaries.

Horizontal scaling is important.

Modeling

Embedding is useful when related data is bounded and commonly accessed together. References are useful when data is shared, independently updated or unbounded.

Do not mechanically transform every relational table into a collection.

Modeling Boundary

Embedding is sufficient when the related data is bounded and the access/update pattern genuinely fits one document.

It is not a general replacement for relationships or joins. If related data is independently updated, shared across many parents, or unbounded, references or another modeling approach may be required.

Do not infer that MongoDB's flexible document model removes the need to reason about cardinality, update patterns, or consistency requirements.

Atomicity and transactions

A single-document model can make related updates atomic by keeping them in one document. Multi-document transactions are available, but they introduce coordination cost and should not replace thoughtful schema design.

Atomicity Boundary

When all required state for an operation is correctly modeled inside one document, a single-document write provides the document-level atomicity needed for that operation.

This does not mean that every business invariant can be solved by embedding. If an invariant spans multiple documents, collections, or independently owned entities, the design must explicitly address that coordination requirement.

Multi-document transactions are an available mechanism for such cases, but they do not make an otherwise unsuitable document model automatically well-designed.

Indexing

Index common query/filter/sort paths. Composite indexes should match real access patterns. Every index has storage and write cost.

Scaling

Sharding is a first-class capability. The shard key must be evaluated for cardinality, distribution, hotspots and query routing.

Sharding Boundary

MongoDB's sharding capability can provide horizontal distribution when the workload requires it, but sharding is not required merely because MongoDB supports it.

A shard key must fit the actual workload. Cardinality, distribution, hotspot risk, and query-routing behavior must be evaluated before selecting the key.

Do not infer that choosing MongoDB automatically solves horizontal scaling; poor shard-key selection can still create hotspots or inefficient routing.

Weak-fit signals

Complex relational joins and strict relational integrity -> MySQL/PostgreSQL.
Deep graph traversal -> Neo4j.
Dedicated search/relevance -> OpenSearch.
Embedded storage -> RocksDB.

Source / grounding

https://www.mongodb.com/docs/

Common Mistakes

Choosing MongoDB solely because the application exchanges JSON.

Embedding every related entity without checking cardinality and update patterns.

Assuming flexible schema means schema design is unnecessary.

Assuming a single-document write solves invariants that actually span multiple documents.

Treating multi-document transactions as a substitute for good document boundaries.

Choosing a shard key without evaluating distribution, hotspots, and query routing.

Using MongoDB for complex relational joins or deep graph traversal without a workload-based reason.