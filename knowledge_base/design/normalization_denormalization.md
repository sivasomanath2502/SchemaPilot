# Normalization and Denormalization — Deep Explanation

## Definition
Normalization is the process of organizing relational data to reduce redundancy and avoid update anomalies, by separating independent facts into their own tables and relating them via keys. Denormalization is the deliberate reverse — duplicating or reshaping data to optimize a specific read path, at the cost of reintroducing some redundancy.

## Why normalization exists — update anomalies
Without normalization, the same fact can be duplicated across many rows. Example: storing a customer's email directly on every `order` row instead of in a `customers` table.

This creates three classic anomaly types:
- **Update anomaly** — changing the customer's email requires updating every order row; missing one leaves inconsistent data.
- **Insert anomaly** — you can't record a new customer until they place an order, if customer data only exists embedded in orders.
- **Delete anomaly** — deleting the last order for a customer accidentally deletes all record of that customer too.

## Normal forms (brief, practical framing)
- **1NF** — each column holds atomic (indivisible) values; no repeating groups in a single column (e.g. no comma-separated list of phone numbers in one field).
- **2NF** — (for tables with composite keys) every non-key column depends on the *whole* key, not just part of it.
- **3NF** — every non-key column depends only on the key, not on another non-key column (no transitive dependency — e.g. don't store both `zip_code` and `city` derived from zip in the same table redundantly without a reason).

Most practical schema design aims for 3NF as a reasonable default, deviating deliberately (denormalizing) only when a specific, justified read pattern needs it.

## Denormalization
Denormalization intentionally reintroduces duplication to optimize a specific, high-value query — for example, storing a `total_price` on an `order` row (computed from `order_items`) so a listing query doesn't need to join and sum every time.

## Safe denormalization requires
- A clear, single owner of the authoritative value (which table/column is the source of truth).
- An explicit update-propagation strategy (how does the denormalized copy stay in sync — application code, a trigger, an event pipeline?).
- Defined failure/retry behavior if propagation fails partway.
- An explicit acceptable-staleness window if propagation isn't synchronous.
- A concrete reason tied to a real, measured or clearly-anticipated performance gain — not a guess.

## Example
An e-commerce `orders` table stores `total_amount` directly (denormalized from summing `order_items`), because the order-listing page is queried far more often than order items change after creation. The source of truth for individual item prices remains `order_items`; `total_amount` is recalculated and stored at order-creation time and is immutable afterward (orders aren't edited after placement in this example), which keeps the sync problem simple and bounded.

## Common mistake
"Denormalize because joins are slow" is not sufficient justification on its own. Joins on properly indexed foreign keys are usually fast; the actual bottleneck should be identified (a specific slow, high-frequency query) before denormalizing, since denormalization has a real ongoing cost (sync complexity, staleness risk).

## When NOT to denormalize
- No specific query has been shown to be a bottleneck.
- The data changes frequently enough that keeping the denormalized copy in sync would be complex or error-prone relative to the benefit.
- A simpler fix (an index, a cache) would solve the same problem with less complexity.

## Interaction with other decisions
- Denormalization interacts directly with **consistency** (`consistency_deep.md`) — a denormalized copy is, by definition, a derived value with its own staleness question.
- It interacts with **transactions** (`transactions_concurrency_deep.md`) — if a denormalized value must always match its source within the same transaction, that constrains which database and consistency model are appropriate.

## Common mistakes
- Denormalizing prematurely without a measured bottleneck.
- No defined synchronization mechanism for the duplicated data.
- Losing track of which table is actually the source of truth after denormalizing.
- Denormalizing frequently-changing data, creating a constant sync burden for little benefit.

## Review questions
- What specific query motivated this denormalization?
- What is the source of truth for this value?
- How does the duplicated value stay in sync, and what happens if sync fails?
- Would an index or cache solve the same problem with less complexity?

## Source / grounding
Curated relational modeling knowledge.
