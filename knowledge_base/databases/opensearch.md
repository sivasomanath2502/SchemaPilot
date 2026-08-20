OpenSearch — Full Selection Profile

Role

Distributed search and analytics engine for full-text search, relevance, filtering, faceting and search-oriented analytics.

Core Selection Summary

Definition: OpenSearch is a distributed search and analytics engine for full-text search, relevance, filtering, faceting, and search-oriented analytics.

Why it exists: It is designed for search workloads where ordinary database indexes are not enough for capabilities such as relevance ranking, fuzzy matching, autocomplete, faceting, or large-scale document search.

When to use: Prefer OpenSearch when search relevance, full-text retrieval, fuzzy matching, autocomplete, faceting, or search-oriented analytics are central requirements.

When NOT to use: Do not select OpenSearch for ordinary exact indexed lookup, transactional OLTP, caching/session storage, or embedded key-value persistence when the primary database already satisfies the requirement.

Primary architectural rule: OpenSearch is normally a derived search projection. The primary database remains authoritative for transactional business state unless the architecture explicitly defines a different source of truth.

Advantages: Specialized search capabilities, relevance ranking, fuzzy matching, autocomplete, filtering, faceting, and search analytics.

Disadvantages: Search projections introduce indexing latency, staleness, failure recovery, and rebuild requirements; using search as a transactional system creates correctness risks for OLTP invariants.

Review questions:

Is search relevance actually required?

Would ordinary database indexes satisfy the query?

What is the source of truth?

What indexing latency and staleness are acceptable?

How is the index rebuilt after failure or corruption?

Is the workload search-oriented or transactional?

Strong selection signals

Full-text search

Relevance ranking

Fuzzy matching

Autocomplete

Faceting/filtering

Large-scale document search

Logs and search analytics

Architecture role

Usually a derived search projection:
Primary database -> indexing pipeline -> OpenSearch.

The design should specify indexing latency, failure recovery, rebuild strategy and acceptable staleness.

Search Projection Boundary

OpenSearch is sufficient for a search workload when the required capabilities are search-oriented and the index can tolerate the defined indexing latency and staleness.

It is not required for ordinary exact lookup when a normal database index already satisfies the requirement.

When OpenSearch is used as a derived projection, indexing failure or staleness must not corrupt the authoritative transactional data.

Source of truth

Do not use a search index as the authoritative payment, booking or inventory store merely because it can store those documents.

Source-of-Truth Boundary

A search index can contain representations of transactional data without becoming authoritative for that data.

For payment, booking, inventory, or similar correctness-sensitive state, the authoritative transactional system remains the source of truth unless the architecture explicitly establishes another correctness mechanism.

Search availability or search freshness must not be confused with transactional correctness.

Weak-fit signals

Exact indexed lookup -> normal database index may be enough.
Transactional OLTP -> MySQL/PostgreSQL.
Cache/session -> Redis.
Embedded KV -> RocksDB.

Source / grounding

https://docs.opensearch.org/latest/

Common Mistakes

Choosing OpenSearch when a normal database index already satisfies the query.

Treating OpenSearch as the source of truth for payment, booking, or inventory state.

Ignoring indexing latency and stale search results.

Failing to define index rebuild and recovery behavior.

Assuming successful indexing means the transactional write itself is durable.

Using search capabilities to solve a transactional invariant that belongs in the authoritative database.