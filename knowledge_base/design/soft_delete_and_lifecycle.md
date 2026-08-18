# Deletion, Soft Delete and Data Lifecycle

## Deletion decision
Do not automatically add a `deleted_at` column to every table by default. Ask, per entity:
- Must the record be recoverable after deletion?
- Is a hard (permanent) deletion actually required — e.g. by a legal/privacy requirement like GDPR erasure?
- Are there retention requirements dictating how long data must be kept?
- Do other rows (foreign keys) depend on this row remaining referenceable?
- Should "deleted" records remain visible/searchable in any context (e.g. an admin audit view)?

## Soft delete trade-offs
Soft deletion (marking a row inactive rather than removing it) preserves history and supports recovery, but complicates:
- **Uniqueness** — a uniqueness constraint (e.g. on email) may need to account for soft-deleted rows, or use a partial/conditional unique constraint (see `schema_constraints.md`) scoped to active rows only.
- **Queries** — every query against the table must remember to filter out soft-deleted rows, or risk showing them by accident.
- **Indexes** — indexes may need to include the deletion-status column to stay efficient once filtering is applied everywhere.
- **Foreign keys** — related rows referencing a soft-deleted row need defined behavior (do they still resolve? are they also considered inactive?).
- **Storage growth** — soft-deleted rows never actually shrink the table, so storage keeps growing unless paired with an archival policy.

## Hard delete vs soft delete — a quick decision guide
- Choose **hard delete** when: no recovery/audit need exists, storage/compliance requires actual removal, and no other rows meaningfully depend on the row's continued existence.
- Choose **soft delete** when: recoverability or an audit trail of "this existed and was removed" is genuinely needed, and the added query/constraint complexity is worth that guarantee.

## Lifecycle and retention
For large or fast-growing tables, define an explicit lifecycle/retention policy (archive to cold storage, or drop old data by partition — see `partitioning_deep.md` for how range partitioning makes this cheap) rather than allowing indefinite, unmanaged growth.

## Relationship to audit/history data
Soft delete (marking a row inactive) is a different concern from maintaining an audit/history trail (recording *what changed and when*) — a table can need one, both, or neither depending on requirements. See `temporal_audit_data.md` for audit/history modeling specifically.

## Common mistakes
- Adding `deleted_at` to every table reflexively, without asking whether recovery is actually needed for that entity.
- Forgetting that a soft-deleted row can silently break a uniqueness constraint (e.g. can't re-register the same email because the old "deleted" row still holds it, unless the constraint is scoped correctly).
- No defined behavior for how related rows treat a soft-deleted parent.
- Allowing soft-deleted data to grow indefinitely with no retention/archival plan.

## Review questions
- Does this specific entity actually need recoverability, or is hard delete acceptable?
- If soft-deleted, does the uniqueness constraint correctly account for it?
- What happens to related rows when a parent is soft-deleted?
- Is there a retention/archival plan, or will soft-deleted rows accumulate indefinitely?

## Source / grounding
Curated database lifecycle knowledge.
