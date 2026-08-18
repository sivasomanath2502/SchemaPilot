# Pagination — Deep Explanation

## Definition
Pagination divides a large result set into smaller responses. It affects API design, query performance, consistency and indexes.

## Offset pagination
`LIMIT 20 OFFSET 10000` returns 20 rows after skipping 10,000 rows.

Advantages:
- simple implementation
- supports arbitrary page numbers
- convenient for small datasets and admin UIs

Problems:
- deep offsets can become expensive
- rows inserted/deleted between requests can shift page boundaries
- database may need to locate and skip many rows

## Cursor pagination
The server returns an opaque cursor representing the position in the result set. The client sends the cursor for the next page.

Good for:
- feeds
- APIs
- infinite scrolling
- large result sets

## Keyset pagination
Keyset pagination uses ordered column values as the continuation position.

Example:
`WHERE (created_at, id) < (?, ?)`
`ORDER BY created_at DESC, id DESC`
`LIMIT 20`

A unique tie-breaker such as id makes ordering deterministic.

## Index design
Pagination must be designed with the query index. For:
`WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT 20`
an index beginning with `(user_id, created_at, id)` is a candidate.

## Choosing a method
Offset:
- small/moderate datasets
- page-number UX
- occasional administrative queries

Cursor/keyset:
- large datasets
- high-volume APIs
- feeds
- infinite scrolling
- stable sequential traversal

## Common mistakes
- no deterministic ORDER BY
- deep offset on huge tables
- cursor based on mutable/non-unique values
- cursor exposing sensitive internal information
- assuming cursor pagination eliminates all consistency concerns
