Pagination — Deep Explanation

Core Reasoning Summary

Definition: Pagination divides a potentially large result set into bounded responses and requires coordination between API semantics, query ordering, indexes, and consistency behavior.

Why it exists: Returning every matching row can create excessive database work, response size, memory use, and latency. Pagination bounds the amount of data processed or returned per request.

When to use: Use pagination when result sets can become large or when an API/UI needs bounded responses.

When NOT to use: Do not assume cursor/keyset pagination is required for every endpoint. Small datasets and administrative interfaces may reasonably use offset pagination.

Primary rule: The pagination method must match the ordering, workload, user experience, and consistency requirements. Pagination itself does not guarantee stable results across requests.

Advantages: Bounded responses, lower per-request resource usage, and scalable sequential traversal when the query and index are aligned.

Disadvantages: Offset can become expensive at deep positions; cursor/keyset requires deterministic continuation semantics and careful handling of changing data.

Review questions:

What ordering defines the result sequence?

Is that ordering deterministic?

Can the ordering columns change between requests?

What happens when rows are inserted or deleted?

Is the cursor opaque and safely scoped?

Does the index support the pagination query?

Is offset actually a problem for this workload?

Pagination divides a large result set into smaller responses. It affects API design, query performance, consistency and indexes.

Offset pagination

LIMIT 20 OFFSET 10000 returns 20 rows after skipping 10,000 rows.

Offset Boundary

Offset pagination is sufficient when arbitrary page-number navigation is useful and the dataset/workload makes the offset cost acceptable.

It does not guarantee that page boundaries remain stable when rows are inserted or deleted between requests.

Advantages:

simple implementation

supports arbitrary page numbers

convenient for small datasets and admin UIs

Problems:

deep offsets can become expensive

rows inserted/deleted between requests can shift page boundaries

database may need to locate and skip many rows

Cursor pagination

The server returns an opaque cursor representing the position in the result set. The client sends the cursor for the next page.

Cursor Boundary

A cursor provides a continuation token, but it does not automatically guarantee stable results.

The cursor must encode enough ordering state to continue the intended sequence, and the API must define behavior when the underlying data changes.

Good for:

feeds

APIs

infinite scrolling

large result sets

Keyset pagination

Keyset pagination uses ordered column values as the continuation position.

Keyset Boundary

Keyset pagination is effective when the ordering columns provide a stable, deterministic continuation position and the query can use an appropriate index.

It does not eliminate consistency concerns when rows are inserted, deleted, or updated between requests.

Example:
WHERE (created_at, id) < (?, ?)
ORDER BY created_at DESC, id DESC
LIMIT 20

A unique tie-breaker such as id makes ordering deterministic.

Deterministic-Ordering Boundary

A unique tie-breaker makes equal primary ordering values deterministic for the query's ordering rule. It does not freeze the dataset across multiple requests.

If rows can be inserted, deleted, or have their ordering values changed, the application still needs an explicit consistency expectation for pagination.

Index design

Pagination must be designed with the query index. For:

Index Boundary

An aligned index is a candidate to reduce sorting/scanning cost; it does not guarantee that the optimizer will use it or that the query will be faster.

Validate the actual query plan for representative data and workload.

WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT 20
an index beginning with (user_id, created_at, id) is a candidate.

Choosing a method

Method-Selection Boundary

Offset, cursor, and keyset pagination are not mutually exclusive at the architectural level. Different endpoints may legitimately use different methods.

Choose based on page-number requirements, result-set size, ordering stability, workload, and consistency semantics rather than treating cursor/keyset as universally superior.

Offset:

small/moderate datasets

page-number UX

occasional administrative queries

Cursor/keyset:

large datasets

high-volume APIs

feeds

infinite scrolling

stable sequential traversal

Common mistakes

no deterministic ORDER BY

deep offset on huge tables

cursor based on mutable/non-unique values

cursor exposing sensitive internal information

assuming cursor pagination eliminates all consistency concerns

Common Review Mistakes

Treating cursor pagination as automatically consistent.

Using a mutable or non-unique cursor position without defining its behavior.

Assuming a unique tie-breaker freezes the underlying dataset.

Choosing keyset pagination without an index that supports the actual ordering/filtering path.

Treating deep offset cost as a reason to replace offset pagination for every endpoint.

Exposing sensitive internal database values directly as cursors.

Ignoring inserts, deletes, or updates between page requests.

Assuming pagination solves database scalability by itself.