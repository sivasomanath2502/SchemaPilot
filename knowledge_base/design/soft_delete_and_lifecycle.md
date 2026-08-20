Deletion, Soft Delete and Data Lifecycle

Core Reasoning Summary

Definition: Data lifecycle design determines whether records are hard-deleted, soft-deleted, archived, retained, or permanently removed, based on business, recovery, dependency, storage, and compliance requirements.

Why it exists: Different entities have different deletion and retention needs. A blanket deletion strategy can create unnecessary complexity or fail to satisfy recovery, audit, dependency, or removal requirements.

When to use: Decide lifecycle behavior per entity when deletion, recovery, retention, auditability, storage growth, or regulatory removal matters.

When NOT to use: Do not add deleted_at or soft delete to every table by default. Do not treat soft delete as a substitute for an audit/history model or as proof that data has been permanently removed.

Primary rule: Choose hard delete, soft delete, archival, or another lifecycle strategy from the entity's actual requirements.

Advantages: Explicit lifecycle decisions prevent accidental retention and avoid unnecessary soft-delete complexity.

Disadvantages: Soft delete adds query, uniqueness, foreign-key, indexing, and storage complexity; hard delete can remove recovery or historical visibility.

Review questions:

Does this entity need recovery?

Must the data actually be removed?

Is there a retention requirement?

What happens to dependent rows?

Should deleted data remain visible in any context?

Does soft delete affect uniqueness?

How is old data archived or purged?

Is audit/history required separately?

Deletion decision

Deletion-Selection Boundary

The decision is entity-specific. There is no universal requirement to use either hard delete or soft delete for every table.

A retention, recovery, dependency, visibility, or compliance requirement should be identified before selecting the lifecycle strategy.

Do not automatically add a deleted_at column to every table by default. Ask, per entity:

Must the record be recoverable after deletion?

Is a hard (permanent) deletion actually required — e.g. by a legal/privacy requirement like GDPR erasure?

Are there retention requirements dictating how long data must be kept?

Do other rows (foreign keys) depend on this row remaining referenceable?

Should "deleted" records remain visible/searchable in any context (e.g. an admin audit view)?

Soft delete trade-offs

Soft-Delete Boundary

Soft delete is sufficient for making a record inactive while retaining the row, but it does not mean the data has been physically removed.

If permanent removal is required, soft delete alone is insufficient; the lifecycle must include an appropriate purge or deletion process.

Soft deletion (marking a row inactive rather than removing it) preserves history and supports recovery, but complicates:

Uniqueness — a uniqueness constraint (e.g. on email) may need to account for soft-deleted rows, or use a partial/conditional unique constraint (see schema_constraints.md) scoped to active rows only.

Boundary: The uniqueness rule must match the business meaning. If a deleted value may be reused, the constraint must exclude inactive rows where the database supports that mechanism. If deleted values must remain reserved, the original uniqueness rule may be correct.

Queries — every query against the table must remember to filter out soft-deleted rows, or risk showing them by accident.

Boundary: A soft-delete column does not automatically hide rows. The application/query layer must consistently apply the active-row predicate, or another database/view mechanism must enforce that visibility rule.

Indexes — indexes may need to include the deletion-status column to stay efficient once filtering is applied everywhere.

Foreign keys — related rows referencing a soft-deleted row need defined behavior (do they still resolve? are they also considered inactive?).

Boundary: Soft deletion does not automatically cascade lifecycle semantics to related rows. The relationship behavior must be explicitly defined.

Storage growth — soft-deleted rows never actually shrink the table, so storage keeps growing unless paired with an archival policy.

Boundary: Soft delete preserves the row until a separate archival or purge process removes or relocates it. It therefore does not solve indefinite storage growth by itself.

Hard delete vs soft delete — a quick decision guide

Hard-Delete Boundary

Hard delete is sufficient when the record should no longer exist in the operational database and no recovery, audit, dependency, or retention requirement requires it to remain.

It does not automatically remove copies held in backups, caches, search indexes, exports, or other systems; those lifecycle requirements must be handled separately when applicable.

Choose hard delete when: no recovery/audit need exists, storage/compliance requires actual removal, and no other rows meaningfully depend on the row's continued existence.

Choose soft delete when: recoverability or an audit trail of "this existed and was removed" is genuinely needed, and the added query/constraint complexity is worth that guarantee.

Lifecycle and retention

Retention Boundary

A retention period defines how long data should remain available under the applicable lifecycle policy. It does not automatically determine whether operational deletion, archival, backup expiration, or search/cache cleanup has occurred.

For systems with multiple copies, the lifecycle policy should define how those copies are handled when required.

For large or fast-growing tables, define an explicit lifecycle/retention policy (archive to cold storage, or drop old data by partition — see partitioning_deep.md for how range partitioning makes this cheap) rather than allowing indefinite, unmanaged growth.

Relationship to audit/history data

Audit Boundary

Soft delete records that a row was marked inactive; it does not by itself record who changed it, what fields changed, or when each historical change occurred.

If the business needs a history of changes, an explicit audit/history model is required.

Soft delete (marking a row inactive) is a different concern from maintaining an audit/history trail (recording what changed and when) — a table can need one, both, or neither depending on requirements. See temporal_audit_data.md for audit/history modeling specifically.

Common mistakes

Adding deleted_at to every table reflexively, without asking whether recovery is actually needed for that entity.

Forgetting that a soft-deleted row can silently break a uniqueness constraint (e.g. can't re-register the same email because the old "deleted" row still holds it, unless the constraint is scoped correctly).

No defined behavior for how related rows treat a soft-deleted parent.

Allowing soft-deleted data to grow indefinitely with no retention/archival plan.

Review questions

Does this specific entity actually need recoverability, or is hard delete acceptable?

If soft-deleted, does the uniqueness constraint correctly account for it?

What happens to related rows when a parent is soft-deleted?

Is there a retention/archival plan, or will soft-deleted rows accumulate indefinitely?

Source / grounding

Curated database lifecycle knowledge.

Common Review Mistakes

Adding deleted_at to every table automatically.

Assuming soft delete means the data is permanently removed.

Assuming soft deletion automatically hides rows from every query.

Forgetting to define uniqueness behavior for deleted values.

Assuming related rows automatically become inactive when a parent is soft-deleted.

Using soft delete as a replacement for audit/history tracking.

Allowing soft-deleted data to grow indefinitely.

Treating hard delete as automatically removing every copy in backups, caches, search indexes, or exports.

Ignoring retention or compliance requirements when choosing a deletion strategy.