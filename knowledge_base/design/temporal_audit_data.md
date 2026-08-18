# History, Audit and Temporal Data

## Current state vs history
A table holding only current status is not automatically an audit log — once a value is overwritten, the previous value is gone unless something explicitly preserved it.

If requirements include "who changed what and when" (a genuine audit/compliance need), history must be modeled explicitly — it does not fall out of a normal current-state table for free.

## Modeling options
- **Audit table** — a separate table recording each change (old value, new value, who, when) alongside the main table.
- **Append-only event log** — every change is recorded as a new event row; current state is derived by replaying/aggregating events rather than stored directly.
- **Status history table** — specifically tracks state transitions (e.g. `order_status_history: order_id, status, changed_at`) rather than generic field-level changes.
- **Effective-dated fields** (`effective_from` / `effective_to`) — useful when a fact is valid for a time range (e.g. a price that was in effect from one date to another), letting queries ask "what was true at time X."

## Choosing an approach
- Need only "who changed what, when," for compliance/debugging → an audit table is usually simplest.
- Need to reconstruct full historical state at any point, or the domain is inherently event-driven → an append-only event log fits better, at the cost of more complex read-side logic to derive current state.
- Need to answer "what was the price/rate at the time of this specific transaction" → effective-dated fields, or capturing the relevant historical value directly on the transaction row itself (e.g. storing the price on the `order_item` row at order time, not just referencing the current `product.price`).

## Review questions
- Is history/audit actually mandatory here, or assumed without a stated requirement?
- Can the affected records be deleted, and if so, does that conflict with a retention/audit requirement?
- Is legal or compliance traceability genuinely required for this entity?
- Is current state sufficient, or does the business explicitly need "what was true at time X"?
- How large will the history data become, and does it need its own lifecycle/retention plan (see `soft_delete_and_lifecycle.md` and `partitioning_deep.md` for how range partitioning supports cheap archival of historical data)?

## Relationship to soft delete
Audit/history (what changed and when) is a distinct concern from soft delete (marking a row inactive rather than removing it) — see `soft_delete_and_lifecycle.md`. A table may need one, both, or neither.

## Common mistakes
- Assuming a current-state table implicitly provides history, when no change actually preserves prior values.
- Building a full audit log for every table by default, regardless of whether any requirement actually needs it.
- Storing only a foreign key reference to a mutable value (like `product_id`) on a transaction row when the historically-accurate value (the price *at that time*) needs to be preserved directly.

## Source / grounding
Curated data lifecycle knowledge.
