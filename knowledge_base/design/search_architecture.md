Search Architecture — Deep Explanation

Core Reasoning Summary

Definition: A search architecture keeps the transactional database as the source of truth while maintaining a derived, search-optimized projection in a dedicated search engine such as OpenSearch.

Why it exists: Search engines provide capabilities such as relevance ranking, fuzzy matching, full-text retrieval, faceting, and autocomplete that are not the primary purpose of ordinary transactional database indexes.

When to use: Use a dedicated search engine when a concrete product requirement needs dedicated search behavior such as relevance, fuzzy matching, large-scale full-text search, faceting, autocomplete, or search analytics.

When NOT to use: Do not introduce a search engine merely because the application has a search box, stores text, or performs exact/prefix lookups that the primary database can serve efficiently.

Primary rule: The search engine is a derived projection unless the architecture explicitly establishes another source-of-truth model. Business-critical facts must remain authoritative in the transactional system when that is the chosen architecture.

Advantages: Specialized search capabilities and search-oriented query performance.

Disadvantages: Added indexing pipeline, eventual staleness, synchronization/failure handling, storage, operational complexity, and rebuild requirements.

Review questions:

What specific search capability requires a dedicated engine?

What is the source of truth?

How does data reach the search index?

What is the acceptable indexing lag?

What happens when indexing fails?

Can the index be rebuilt from the source?

What happens to the application when search is unavailable?

A search architecture pairs a transactional database (source of truth) with a dedicated search engine (e.g. OpenSearch) that maintains a derived, denormalized index optimized for full-text relevance, fuzzy matching, and faceted queries — capabilities a relational database's indexes aren't designed for.

Transactional DB vs search engine

Source-of-Truth Boundary

The transactional database remains authoritative for business data in this architecture. The search engine is a derived projection optimized for search.

A search index can contain copies of business fields, but the presence of those fields does not make the search engine authoritative for transactional decisions such as price, stock, payment state, or booking state.

A relational/document database remains the authoritative source of truth for the actual data. The search engine holds a derived projection of that data, reshaped and indexed specifically for search-style queries. This is the same "source of truth vs derived state" principle as consistency_deep.md — the search index is never the place a business fact is created or considered authoritative.

When to use a search engine

Selection Boundary

The presence of searchable text is not sufficient evidence for a dedicated search engine.

A dedicated search engine becomes justified when its specialized capabilities materially satisfy an actual requirement that the primary database's supported access paths do not adequately satisfy.

Relevance ranking matters (results should be ordered by how well they match, not just filtered).

Fuzzy matching / typo tolerance matters.

Full-text queries across large text fields are central to the feature (product search, document search).

Faceting, autocomplete, or search analytics are genuine product requirements.

A search requirement does not automatically mean replacing the primary database — most applications keep the primary database for everything except the specific search-heavy queries.

Required design decisions

Pipeline Boundary

Choosing an indexing pipeline solves how changes are propagated; it does not automatically guarantee zero lag, exactly-once indexing, or that every search result is immediately current.

The architecture must explicitly define retry behavior, failed-event handling, acceptable staleness, and rebuild behavior.

Source of truth — which database owns the real data (always the primary DB, not the search engine).

Indexing pipeline — how data gets from the primary DB into the search index. Common patterns:

Dual write — the application writes to both the primary DB and the search index in the same request. Simple, but risks the two falling out of sync if one write succeeds and the other fails.

Boundary: Writing to both systems in one application request does not make the two writes one atomic transaction unless the architecture explicitly provides such coordination.

Change Data Capture (CDC) — a process reads the primary database's write log (e.g. MySQL binlog) and streams changes to the search index asynchronously. More reliable than dual-write since it's driven by what actually committed, not by application code remembering to do both writes.

Boundary: CDC reduces the risk of missing application-triggered dual writes, but it does not eliminate indexing lag, downstream failure, duplicate delivery, ordering concerns, or the need for retry/rebuild handling.

Outbox pattern — the application writes the intended change to an "outbox" table in the same transaction as the primary write, and a separate process reliably publishes those outbox entries to the search index. Avoids the dual-write inconsistency risk while staying transactionally safe.

Boundary: The outbox makes recording the intended event atomic with the primary database transaction. It does not make the later search-index update atomic with that transaction; the search index can still temporarily lag or require retry/reconciliation.

Update latency — how quickly must the search index reflect a new/changed record? Near-real-time is achievable but not instantaneous.

Retry / dead-letter behavior — if an update to the search index fails, does it retry, and where do permanently-failed updates go for investigation?

Index rebuild strategy — how to fully rebuild the search index from the source of truth if it becomes corrupted or the mapping changes (schema change in the search index).

Stale-result tolerance — how much lag between a primary-DB write and its visibility in search is acceptable for the product?

Example

Example Boundary

The example assumes search is a derived capability and that checkout/browsing correctness remains backed by MySQL. If search results become a correctness-critical dependency for a business operation, the architecture must explicitly address that requirement rather than assuming the derived index is authoritative.

An e-commerce product catalog: MySQL is the source of truth for product data (price, stock, description). An outbox-pattern process publishes product changes to OpenSearch, which powers the product search bar with fuzzy matching and relevance ranking. If OpenSearch is briefly unavailable, product browsing/checkout (backed by MySQL) continues to work; only the search feature degrades.

When NOT to introduce a search engine

Non-Selection Boundary

A search engine is unnecessary when the primary database can satisfy the required search semantics and workload adequately.

The existence of a search endpoint, text column, or filtering requirement alone is not enough to justify OpenSearch.

Simple exact-match or prefix lookups that a regular database index already serves well (WHERE sku = ? doesn't need OpenSearch).

The dataset is small enough that in-database LIKE queries or a full-text index built into the primary database are sufficient.

No requirement actually involves relevance ranking, fuzzy matching, or faceting — adding a search engine "because search sounds important" without those specific needs is unjustified complexity.

Common mistakes

Treating the search index as if it were the source of truth (e.g. reading stock levels from the search index for a purchase decision).

Dual-write without any reconciliation mechanism, letting the two stores silently drift apart over time.

No defined behavior for what happens to reads/writes when the search engine is down.

Introducing a search engine for a simple exact-match query that a regular index would serve.

Review rule

Review Boundary

Before recommending a search engine, identify the exact search capability that requires it and the source of truth that remains authoritative.

After recommending one, verify the indexing pipeline, acceptable staleness, failure behavior, and rebuild path.

A search requirement does not automatically mean replacing the primary database. The search engine should be a derived, disposable projection with a clear rebuild path — never the authoritative store for business-critical fields.

Review questions

What specific search capability (relevance, fuzzy match, faceting) actually requires a dedicated search engine?

What is the indexing pipeline, and how does it handle a failed update?

Could the source of truth be rebuilt into the search engine from scratch if needed?

What is the acceptable staleness window between a write and its visibility in search?

Source / grounding

https://docs.opensearch.org/latest/

Common Review Mistakes

Treating a search box as automatic evidence for OpenSearch.

Treating the search index as the source of truth.

Assuming dual writes are atomic because they happen in one application request.

Assuming CDC eliminates all synchronization and ordering problems.

Assuming the outbox makes the search index transactionally atomic with the primary database.

Ignoring acceptable indexing lag.

Introducing OpenSearch for simple exact-match queries that a database index can handle.

Failing to define what happens when OpenSearch is unavailable.

Failing to define a rebuild path from the source of truth.

Reading correctness-critical transactional values from a potentially stale search projection.