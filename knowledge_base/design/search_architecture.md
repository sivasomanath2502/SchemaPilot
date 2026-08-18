# Search Architecture — Deep Explanation

## Definition
A search architecture pairs a transactional database (source of truth) with a dedicated search engine (e.g. OpenSearch) that maintains a derived, denormalized index optimized for full-text relevance, fuzzy matching, and faceted queries — capabilities a relational database's indexes aren't designed for.

## Transactional DB vs search engine
A relational/document database remains the authoritative source of truth for the actual data. The search engine holds a **derived projection** of that data, reshaped and indexed specifically for search-style queries. This is the same "source of truth vs derived state" principle as `consistency_deep.md` — the search index is never the place a business fact is created or considered authoritative.

## When to use a search engine
- Relevance ranking matters (results should be ordered by how well they match, not just filtered).
- Fuzzy matching / typo tolerance matters.
- Full-text queries across large text fields are central to the feature (product search, document search).
- Faceting, autocomplete, or search analytics are genuine product requirements.

A search requirement does **not** automatically mean replacing the primary database — most applications keep the primary database for everything except the specific search-heavy queries.

## Required design decisions
- **Source of truth** — which database owns the real data (always the primary DB, not the search engine).
- **Indexing pipeline** — how data gets from the primary DB into the search index. Common patterns:
  - **Dual write** — the application writes to both the primary DB and the search index in the same request. Simple, but risks the two falling out of sync if one write succeeds and the other fails.
  - **Change Data Capture (CDC)** — a process reads the primary database's write log (e.g. MySQL binlog) and streams changes to the search index asynchronously. More reliable than dual-write since it's driven by what actually committed, not by application code remembering to do both writes.
  - **Outbox pattern** — the application writes the intended change to an "outbox" table in the same transaction as the primary write, and a separate process reliably publishes those outbox entries to the search index. Avoids the dual-write inconsistency risk while staying transactionally safe.
- **Update latency** — how quickly must the search index reflect a new/changed record? Near-real-time is achievable but not instantaneous.
- **Retry / dead-letter behavior** — if an update to the search index fails, does it retry, and where do permanently-failed updates go for investigation?
- **Index rebuild strategy** — how to fully rebuild the search index from the source of truth if it becomes corrupted or the mapping changes (schema change in the search index).
- **Stale-result tolerance** — how much lag between a primary-DB write and its visibility in search is acceptable for the product?

## Example
An e-commerce product catalog: MySQL is the source of truth for product data (price, stock, description). An outbox-pattern process publishes product changes to OpenSearch, which powers the product search bar with fuzzy matching and relevance ranking. If OpenSearch is briefly unavailable, product browsing/checkout (backed by MySQL) continues to work; only the search feature degrades.

## When NOT to introduce a search engine
- Simple exact-match or prefix lookups that a regular database index already serves well (`WHERE sku = ?` doesn't need OpenSearch).
- The dataset is small enough that in-database `LIKE` queries or a full-text index built into the primary database are sufficient.
- No requirement actually involves relevance ranking, fuzzy matching, or faceting — adding a search engine "because search sounds important" without those specific needs is unjustified complexity.

## Common mistakes
- Treating the search index as if it were the source of truth (e.g. reading stock levels from the search index for a purchase decision).
- Dual-write without any reconciliation mechanism, letting the two stores silently drift apart over time.
- No defined behavior for what happens to reads/writes when the search engine is down.
- Introducing a search engine for a simple exact-match query that a regular index would serve.

## Review rule
A search requirement does not automatically mean replacing the primary database. The search engine should be a derived, disposable projection with a clear rebuild path — never the authoritative store for business-critical fields.

## Review questions
- What specific search capability (relevance, fuzzy match, faceting) actually requires a dedicated search engine?
- What is the indexing pipeline, and how does it handle a failed update?
- Could the source of truth be rebuilt into the search engine from scratch if needed?
- What is the acceptable staleness window between a write and its visibility in search?

## Source / grounding
https://docs.opensearch.org/latest/
