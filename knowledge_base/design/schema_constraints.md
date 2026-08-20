Keys, Constraints and Integrity — Deep Explanation

Core Reasoning Summary

Definition: Database constraints are rules enforced by the database engine that guarantee specific invariants independently of application code paths and concurrent requests.

Why it exists: Constraints provide authoritative enforcement for invariants that the database can express, preventing application-level checks from being bypassed by concurrent or alternate writers.

When to use: Use constraints whenever a business rule can be expressed as a database-level primary key, foreign key, unique constraint, check constraint, or supported conditional constraint.

When NOT to use: Do not assume every business rule can be expressed by a simple constraint. Multi-row aggregate invariants may require transactions, locking, atomic conditional updates, or another explicit concurrency strategy.

Primary rule: First classify the invariant. A single-key uniqueness rule is completely enforced by the corresponding UNIQUE constraint; a multi-row aggregate invariant is a different problem and may require additional transactional/concurrency mechanisms.

Advantages: Centralized, concurrency-safe enforcement for expressible invariants.

Disadvantages: Constraints cannot express every business rule, and some constraint designs can introduce operational or schema-management trade-offs.

Review questions:

What exact business invariant does this constraint protect?

Is the invariant single-row/key-based or multi-row/aggregate?

Is a UNIQUE constraint alone sufficient for the exact rule?

Does the rule require a transaction or locking mechanism?

Could application validation still be useful for user-friendly errors?

Are foreign-key and lifecycle semantics intentional?

Database constraints are rules enforced by the database engine itself (not application code) that guarantee certain invariants always hold, regardless of which application, code path, or concurrent request is writing the data.

Primary keys

Identify rows/entities reliably and uniquely. Should be stable (not something that legitimately changes, like an email address) — prefer a surrogate key (auto-increment integer or UUID) over a natural key unless the natural key is truly immutable.

Foreign keys

Enforce that a reference always points to a row that actually exists (e.g. orders.user_id must reference a real users.id). Prevents orphaned references and enforces relational integrity at the database level rather than trusting every application code path to check this correctly.

Unique constraints

Enforce business uniqueness rules such as:

email address per user

external payment reference

booking reference number

a composite uniqueness rule, e.g. (show_id, seat_id) for a seat booking — one seat can only be booked once per show

When a single-column or composite unique constraint IS sufficient (no locking needed)

Sufficiency Boundary

For the exact invariant "no two rows may contain the same constrained key value", the UNIQUE constraint itself is the correctness mechanism. No additional application-side lock or SELECT ... FOR UPDATE is required merely to make that uniqueness invariant hold.

A transaction may still be required for other business operations performed together with the insert. That is a separate atomicity requirement.

For a "no two rows can share this exact key" invariant — like (show_id, seat_id)
above — the UNIQUE constraint is COMPLETE on its own. Nothing else is required:

No explicit SELECT ... FOR UPDATE or row lock is needed.

No explicit transaction wrapping the INSERT is needed for correctness (though
a transaction may still be used for other reasons, e.g. inserting a booking
and a payment record together atomically — that's a different concern, not
what makes the uniqueness invariant hold).

The database rejects the conflicting INSERT unconditionally, the instant it
is attempted, regardless of what any concurrent request's application code
believed to be true when it ran its own check.

Do not confuse this with the "When constraints alone aren't enough" case below.
That section is about a DIFFERENT kind of invariant — one that spans MULTIPLE
rows and requires a computed aggregate (e.g. "total booked seats ≤ venue
capacity," which no single row's uniqueness can express). A single-row
uniqueness rule like "this exact key can only appear once" is fully solved by
the constraint alone. Before flagging a missing locking/transaction mechanism
as a problem, first classify which case applies: single-key uniqueness (solved
by UNIQUE alone) vs. multi-row aggregate invariant (needs a transaction/lock in
addition to or instead of a constraint).

Check constraints

Enforce simple domain invariants directly in the schema where the database supports them — e.g. CHECK (price >= 0), CHECK (status IN ('pending', 'confirmed', 'cancelled')). Not a substitute for complex business logic, but useful for simple, always-true rules.

Why database-level enforcement matters — the concurrency argument

Application-Check Boundary

An application-level availability or uniqueness check can improve user-facing validation, but it is not sufficient as the sole enforcement mechanism when concurrent writers can violate the rule.

For an exact single-key uniqueness invariant that is represented by a UNIQUE constraint, the database constraint is the authoritative protection. The application does not need to perform a locking read before the insert merely to enforce uniqueness.

Application-level validation (checking "is this seat already booked?" in code before inserting) is not sufficient on its own when multiple requests can run concurrently. Two concurrent requests can both pass the application check (seat appears available to both) before either has committed its booking — both then proceed to insert, and without a database constraint, both bookings succeed, violating the business rule.

Concrete example: two users simultaneously try to book ShowSeat(show_id=5, seat_id=12).

Request A checks: is this seat booked? No (application logic).

Request B checks: is this seat booked? No (also passes, before A has inserted).

Both proceed to INSERT a booking for the same seat.

A UNIQUE (show_id, seat_id) constraint on the bookings table makes the second insert fail at the database level, regardless of what the application-level check concluded — this is the only reliable way to prevent this race, because the database serializes the actual write attempts even when application logic ran concurrently.

Application vs database validation

Important integrity rules — anything that must hold true even under concurrent access — should be protected at the database layer, not only through application code. Application-level validation is still useful for early, user-friendly error messages, but it cannot be trusted as the sole enforcement mechanism for concurrency-sensitive invariants.

Composite and partial constraints

A composite unique constraint spans multiple columns (as in the seat-booking example above).

Some databases support partial/conditional unique constraints (e.g. "unique only where status = 'active'"), useful when a rule like uniqueness should only apply to non-deleted or currently-active rows.

When constraints alone aren't enough

Multi-Row Boundary

This section applies only when the invariant depends on multiple rows or a computed aggregate.

Examples include:

total booked seats ≤ venue capacity

total allocated quantity ≤ available quantity

aggregate balance or quota constraints across multiple records

A UNIQUE constraint cannot express these aggregate rules. They require an appropriate transaction/concurrency strategy, such as locking or an atomic conditional update, according to the database and workload.

Do not apply this section to a simple "this exact key may occur only once" invariant; that case is already completely enforced by the corresponding UNIQUE constraint.

Some invariants span multiple rows or require a computed check that a simple constraint can't express (e.g. "total booked seats for a show must not exceed venue capacity" across many rows). These typically require a transaction with appropriate locking or an atomic conditional update, in addition to or instead of a simple constraint — see transactions_concurrency_deep.md.

Common mistakes

Relying solely on application-level checks for concurrency-sensitive uniqueness rules.

Forgetting to add a composite unique constraint when the real uniqueness rule spans multiple columns, not just one.

Assuming a check constraint can express a multi-row business invariant it fundamentally can't.

Treating foreign keys as optional "for performance," losing referential integrity guarantees without a deliberate, documented reason.

Review rule

Review Boundary

For every important business rule, first classify what the rule actually says.

If it is an exact single-column or composite uniqueness rule covered by a UNIQUE constraint, the constraint alone is sufficient for that invariant.

If it spans multiple rows, depends on an aggregate, or requires coordination across separate operations, identify the additional transaction/concurrency mechanism explicitly.

For every important business rule, ask: "Can concurrent requests violate this rule?" If yes, application-only validation is insufficient — an appropriate database-level constraint or transaction strategy is required.

Review questions

Which business rule does this constraint protect?

Could concurrent requests bypass an application-only check for this rule?

Is the uniqueness rule single-column or composite?

Does this invariant span multiple rows, requiring a transaction rather than (or in addition to) a constraint?

If a single-row UNIQUE constraint already covers the exact invariant, is
there evidence the invariant is actually multi-row (an aggregate/count
across rows), or is the constraint alone already sufficient?

Source / grounding

Curated database integrity knowledge.

Common Review Mistakes

Treating every concurrency-sensitive rule as requiring SELECT ... FOR UPDATE.

Treating every important rule as requiring an explicit transaction when a UNIQUE constraint already completely enforces the exact invariant.

Confusing single-key uniqueness with multi-row aggregate constraints.

Relying only on application-level uniqueness checks.

Forgetting composite uniqueness when the real business key spans multiple columns.

Assuming a CHECK constraint can express arbitrary multi-row business logic.

Removing foreign keys for performance without documenting the resulting integrity trade-off.

Applying the "constraints alone aren't enough" caveat to a simple uniqueness rule that is already completely enforced by UNIQUE.