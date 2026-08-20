History, Audit and Temporal Data

Core Reasoning Summary

Definition: History, audit, and temporal modeling preserve information about changes or about what value was valid during a particular period.

Why it exists: A current-state row normally preserves only the latest value. If the business must know who changed what, reconstruct historical state, or determine what was true at a past time, that information must be preserved explicitly.

When to use: Use an audit table for change traceability, an append-only event log when event history/reconstruction is central, a status-history table for state transitions, and effective-dated or transaction-captured values when historical validity matters.

When NOT to use: Do not create a full audit log for every table by default. Do not assume current-state columns provide history, and do not store only a mutable reference when a historical transaction requires the value that existed at that time.

Primary rule: Choose the smallest history model that preserves the historical fact the business actually needs.

Advantages: Preserves traceability, historical correctness, and the ability to answer time-based questions.

Disadvantages: Adds storage, lifecycle, retention, query, and operational complexity.

Review questions:

Is historical data actually required?

Is the requirement auditability, state-transition history, event reconstruction, or point-in-time validity?

What exact fact must remain recoverable?

How long must it be retained?

Can current state reconstruct the required history?

What happens when the main row is deleted?

Does the history data need its own lifecycle?

Current state vs history

Current-State Boundary

A current-state table is sufficient only when the business requires the current value and does not need prior values or change traceability.

Overwriting a value destroys the previous value unless another mechanism explicitly preserves it.

A table holding only current status is not automatically an audit log — once a value is overwritten, the previous value is gone unless something explicitly preserved it.

If requirements include "who changed what and when" (a genuine audit/compliance need), history must be modeled explicitly — it does not fall out of a normal current-state table for free.

Modeling options

Audit-Table Boundary

An audit table is appropriate when the requirement is primarily "who changed what and when." It does not automatically provide a complete point-in-time reconstruction of the entire domain unless the captured changes contain enough information to do so.

Event-Log Boundary

An append-only event log can support historical reconstruction when events contain sufficient information and ordering semantics are well defined. It introduces more read-side complexity because current state may need to be derived or projected.

Status-History Boundary

A status-history table is appropriate for state transitions. It does not automatically preserve arbitrary field-level changes that occur alongside those transitions.

Effective-Date Boundary

Effective-dated fields answer questions about when a fact was valid. They do not automatically provide a complete audit trail of who changed the fact or every intermediate value.

Audit table — a separate table recording each change (old value, new value, who, when) alongside the main table.

Append-only event log — every change is recorded as a new event row; current state is derived by replaying/aggregating events rather than stored directly.

Status history table — specifically tracks state transitions (e.g. order_status_history: order_id, status, changed_at) rather than generic field-level changes.

Effective-dated fields (effective_from / effective_to) — useful when a fact is valid for a time range (e.g. a price that was in effect from one date to another), letting queries ask "what was true at time X."

Choosing an approach

Selection Boundary

Choose the history mechanism from the exact question the system must answer.

"Who changed what and when," "what state did this entity have at time X," "what status transitions occurred," and "what price was valid when the transaction happened" are different requirements and may require different modeling.

Need only "who changed what, when," for compliance/debugging → an audit table is usually simplest.

Need to reconstruct full historical state at any point, or the domain is inherently event-driven → an append-only event log fits better, at the cost of more complex read-side logic to derive current state.

Need to answer "what was the price/rate at the time of this specific transaction" → effective-dated fields, or capturing the relevant historical value directly on the transaction row itself (e.g. storing the price on the order_item row at order time, not just referencing the current product.price).

Review questions

Is history/audit actually mandatory here, or assumed without a stated requirement?

Can the affected records be deleted, and if so, does that conflict with a retention/audit requirement?

Is legal or compliance traceability genuinely required for this entity?

Is current state sufficient, or does the business explicitly need "what was true at time X"?

How large will the history data become, and does it need its own lifecycle/retention plan (see soft_delete_and_lifecycle.md and partitioning_deep.md for how range partitioning supports cheap archival of historical data)?

Relationship to soft delete

Soft-Delete Boundary

Soft delete preserves the current row while marking it inactive. It does not automatically preserve the sequence of historical changes.

Audit/history and soft delete can coexist, but neither implies the other.

Audit/history (what changed and when) is a distinct concern from soft delete (marking a row inactive rather than removing it) — see soft_delete_and_lifecycle.md. A table may need one, both, or neither.

Common mistakes

Assuming a current-state table implicitly provides history, when no change actually preserves prior values.

Building a full audit log for every table by default, regardless of whether any requirement actually needs it.

Storing only a foreign key reference to a mutable value (like product_id) on a transaction row when the historically-accurate value (the price at that time) needs to be preserved directly.

Source / grounding

Curated data lifecycle knowledge.

Common Review Mistakes

Assuming current-state columns automatically provide historical information.

Building a full audit log for every table without a stated requirement.

Treating soft delete as a substitute for audit/history.

Using an audit table when the real requirement is full point-in-time reconstruction without checking whether enough information is captured.

Using an event log without defining event ordering and reconstruction semantics.

Using a status-history table when arbitrary field-level history is required.

Storing only a mutable foreign-key reference when a transaction requires the historical value itself.

Ignoring retention, storage growth, and lifecycle requirements for history data.

Review Questions

What exact historical question must the system answer?

Is the requirement audit, event reconstruction, state history, or effective-dated validity?

What information must be captured at write time?

Can the chosen model reconstruct the required historical state?

What retention period applies?

How does history interact with deletion and soft delete?