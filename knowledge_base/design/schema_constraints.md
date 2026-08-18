# Keys, Constraints and Integrity — Deep Explanation

## Definition
Database constraints are rules enforced by the database engine itself (not application code) that guarantee certain invariants always hold, regardless of which application, code path, or concurrent request is writing the data.

## Primary keys
Identify rows/entities reliably and uniquely. Should be stable (not something that legitimately changes, like an email address) — prefer a surrogate key (auto-increment integer or UUID) over a natural key unless the natural key is truly immutable.

## Foreign keys
Enforce that a reference always points to a row that actually exists (e.g. `orders.user_id` must reference a real `users.id`). Prevents orphaned references and enforces relational integrity at the database level rather than trusting every application code path to check this correctly.

## Unique constraints
Enforce business uniqueness rules such as:
- email address per user
- external payment reference
- booking reference number
- a composite uniqueness rule, e.g. `(show_id, seat_id)` for a seat booking — one seat can only be booked once per show

## Check constraints
Enforce simple domain invariants directly in the schema where the database supports them — e.g. `CHECK (price >= 0)`, `CHECK (status IN ('pending', 'confirmed', 'cancelled'))`. Not a substitute for complex business logic, but useful for simple, always-true rules.

## Why database-level enforcement matters — the concurrency argument
Application-level validation (checking "is this seat already booked?" in code before inserting) is **not sufficient on its own** when multiple requests can run concurrently. Two concurrent requests can both pass the application check (seat appears available to both) before either has committed its booking — both then proceed to insert, and without a database constraint, both bookings succeed, violating the business rule.

**Concrete example:** two users simultaneously try to book `ShowSeat(show_id=5, seat_id=12)`.
1. Request A checks: is this seat booked? No (application logic).
2. Request B checks: is this seat booked? No (also passes, before A has inserted).
3. Both proceed to INSERT a booking for the same seat.

A `UNIQUE (show_id, seat_id)` constraint on the bookings table makes the *second* insert fail at the database level, regardless of what the application-level check concluded — this is the only reliable way to prevent this race, because the database serializes the actual write attempts even when application logic ran concurrently.

## Application vs database validation
Important integrity rules — anything that must hold true even under concurrent access — should be protected at the database layer, not only through application code. Application-level validation is still useful for early, user-friendly error messages, but it cannot be trusted as the sole enforcement mechanism for concurrency-sensitive invariants.

## Composite and partial constraints
- A composite unique constraint spans multiple columns (as in the seat-booking example above).
- Some databases support partial/conditional unique constraints (e.g. "unique only where `status = 'active'`"), useful when a rule like uniqueness should only apply to non-deleted or currently-active rows.

## When constraints alone aren't enough
Some invariants span multiple rows or require a computed check that a simple constraint can't express (e.g. "total booked seats for a show must not exceed venue capacity" across many rows). These typically require a transaction with appropriate locking or an atomic conditional update, in addition to or instead of a simple constraint — see `transactions_concurrency_deep.md`.

## Common mistakes
- Relying solely on application-level checks for concurrency-sensitive uniqueness rules.
- Forgetting to add a composite unique constraint when the real uniqueness rule spans multiple columns, not just one.
- Assuming a check constraint can express a multi-row business invariant it fundamentally can't.
- Treating foreign keys as optional "for performance," losing referential integrity guarantees without a deliberate, documented reason.

## Review rule
For every important business rule, ask: "Can concurrent requests violate this rule?" If yes, application-only validation is insufficient — an appropriate database-level constraint or transaction strategy is required.

## Review questions
- Which business rule does this constraint protect?
- Could concurrent requests bypass an application-only check for this rule?
- Is the uniqueness rule single-column or composite?
- Does this invariant span multiple rows, requiring a transaction rather than (or in addition to) a constraint?

## Source / grounding
Curated database integrity knowledge.
