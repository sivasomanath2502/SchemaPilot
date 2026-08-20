Transactions and Concurrency — Deep Explanation

Core Reasoning Summary

Definition: Transactions and concurrency controls coordinate concurrent database operations so that the application's business invariants remain valid.

Why it exists: Concurrent requests can race even when each request is individually correct. A transaction provides atomicity for related database changes, while concurrency controls determine how conflicting operations are coordinated.

When to use: Use a transaction when multiple database changes must succeed or fail together. Use pessimistic or optimistic concurrency control when concurrent operations can conflict and the business rule requires a specific winner/conflict behavior.

When NOT to use: Do not wrap every operation in a transaction automatically, use the strictest isolation level everywhere, or hold transactions open across slow external calls without a concrete reason.

Primary rule: Start with the business invariant. Then determine whether the invariant requires atomicity, uniqueness enforcement, locking, optimistic conflict detection, an isolation guarantee, or some combination.

Advantages: Protects correctness under concurrent requests and partial failures.

Disadvantages: Transactions and stronger concurrency controls can increase contention, latency, deadlocks, conflict retries, and throughput costs.

Review questions:

What invariant is being protected?

Which operations must succeed together?

Can concurrent requests race?

Is a database constraint sufficient?

Is locking required?

Would optimistic concurrency be sufficient?

What isolation level is actually required?

Can the transaction be kept short?

Is retry safe after a deadlock or conflict?

Is idempotency also required?

Business invariant first

Invariant-First Boundary

A transaction is not itself the business rule. First identify the invariant and the operations that must preserve it.

A transaction is sufficient for atomicity among its database operations, but it does not automatically prevent every concurrency anomaly or enforce invariants that require a database constraint or a specific locking strategy.

Before reaching for ACID/transactions as a checkbox, state explicitly what must never happen:

What must never happen?

Which operations must succeed together, or not at all?

What happens if the process crashes midway through?

Examples

Booking: one seat must not be confirmed for two users.

Inventory: available quantity must not become negative due to concurrent purchases.

Payment: a financial state transition must not be left partially applied (debited but not credited, or vice versa).

Transaction definition

Transaction Boundary

A transaction guarantees atomic commit/rollback for the operations included in that transaction according to the database's transaction semantics.

It does not automatically make external API calls atomic with the database, prevent all concurrent races, or make repeated client requests idempotent.

A transaction groups database operations into a logical unit whose required changes must together satisfy the application's business invariants — either all of them happen, or none do.

ACID

Atomicity — all required changes commit together, or none do.

Consistency — the database's declared constraints and business invariants remain valid before and after.

Isolation — concurrent transactions don't observe each other's uncommitted intermediate state in ways that violate business rules.

Durability — once committed, changes survive normal failure according to the database's durability guarantees.

Pessimistic concurrency

Pessimistic-Locking Boundary

A lock protects the locked resource only for the scope and semantics defined by the database and transaction.

Locking is not automatically required for every concurrency-sensitive operation. If a database constraint or optimistic condition check completely enforces the invariant, additional locking may be unnecessary.

Lock the relevant row/resource for the duration of the critical operation, preventing any other transaction from modifying it concurrently.

Benefit: direct, straightforward protection against concurrent modification.
Cost: other requests wait for the lock, creating contention; poor lock ordering across transactions can cause deadlocks.

Optimistic concurrency

Optimistic-Concurrency Boundary

Optimistic concurrency detects that another transaction changed the expected version or condition.

It does not automatically resolve the conflict. The application must define whether to retry, reject, merge, or otherwise handle the conflict, and retry must be safe for the operation.

Use a version number or condition check, and detect conflicts after the fact rather than locking upfront.

Example:

UPDATE item SET version = version + 1 WHERE id = ? AND version = ?

If zero rows are affected, another transaction won the race first — the caller can retry or fail explicitly. Better suited to workloads where conflicts are rare, since it avoids the cost of holding locks for operations that usually don't actually conflict.

Unique constraints as a concurrency tool

Unique-Constraint Boundary

For an exact single-column or composite uniqueness invariant, the UNIQUE constraint is the database-level enforcement mechanism.

A transaction or SELECT ... FOR UPDATE is not required merely to make that uniqueness rule hold.

However, if the operation also includes other changes that must succeed atomically, a transaction may still be required for those additional changes.

Database-level uniqueness is valuable specifically because two application instances can race even if both independently perform an "is this available?" check beforehand — see the seat-booking race example in schema_constraints.md. A unique constraint is the reliable backstop that an application-level check alone cannot be.

Isolation levels

Isolation-Level Boundary

Choose isolation based on the anomalies the business cannot tolerate.

The strictest isolation level is not automatically the safest architectural choice because stronger isolation can reduce concurrency/throughput and increase contention.

Isolation also does not replace constraints that directly express a business invariant.

Choose isolation level based on which anomalies the business genuinely cannot tolerate (dirty reads, non-repeatable reads, phantom reads) — not by defaulting to the strictest option everywhere. Stronger isolation reduces the anomalies possible but also reduces concurrency/throughput, since it typically requires more locking or more conflict detection.

Transaction duration

Transaction-Duration Boundary

Keeping a transaction short reduces lock/resource contention, but work should be moved outside the transaction only when doing so does not break the required atomicity.

External work performed outside the transaction is not automatically coordinated with the database commit and may require an outbox, retry, compensation, or another explicit pattern.

Long-running transactions hold locks/resources longer, increasing contention with other transactions. Keep critical transactions as short as possible — do work like calling external APIs or slow computations outside the transaction boundary where feasible, only wrapping the actual database writes that must be atomic.

Deadlocks

Deadlock Boundary

A deadlock aborts at least one transaction; it does not mean the application's logical operation has automatically succeeded or failed permanently.

Retrying the aborted transaction can be appropriate only when the operation is safe to retry and its transaction is designed to be repeatable.

Two transactions can each hold a lock the other needs, with neither able to proceed. The database typically detects this and aborts one transaction to break the cycle. Applications should be prepared to catch this and retry the aborted transaction where it's safe to do so.

Idempotency and transactions — related but distinct

Separation Boundary

A transaction protects atomic database changes within one request.

Idempotency protects against duplicate logical requests.

Neither mechanism automatically replaces the other. A booking or payment flow may require both when it must handle retries safely and keep its database changes atomic.

A transaction protects atomic database changes within one request. Idempotency (see idempotency_deep.md) protects against duplicate logical requests (e.g. a retried HTTP call). Booking and payment flows commonly need both together: a transaction to keep the database change atomic, and an idempotency key to prevent a retried request from repeating that change entirely.

Common mistakes

Reaching for "just wrap it in a transaction" without first stating the specific business invariant being protected.

Using the strictest isolation level everywhere by default, unnecessarily reducing throughput.

Holding a transaction open across a slow external call (e.g. a payment gateway API), increasing contention risk.

Relying only on an application-level availability check for a race-prone invariant instead of a database constraint (see schema_constraints.md).

Confusing idempotency with transactional atomicity — they solve different problems and are often both needed together.

Review checklist

What invariant is protected?

What rows are read and written, and in what order?

What happens under concurrent requests hitting the same rows?

Is a database constraint needed in addition to (or instead of) the transaction?

Can a deadlock occur, and is retry safe for the operations involved?

Is the transaction as short as it can reasonably be?

Source / grounding

https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-model.html

Common Review Mistakes

Starting with "use a transaction" before identifying the business invariant.

Assuming a transaction prevents every concurrency race.

Adding SELECT ... FOR UPDATE when a UNIQUE constraint already completely enforces the exact uniqueness invariant.

Using the strictest isolation level everywhere.

Holding a transaction open across slow external calls.

Treating optimistic concurrency as automatic conflict resolution.

Retrying deadlocked transactions without checking retry safety.

Assuming transaction atomicity extends to external services.

Confusing idempotency with transactional atomicity.

Using application-level availability checks without a database-level enforcement mechanism for race-prone invariants.

Review Questions

What invariant must never be violated?

Which operations must commit together?

What happens if the process crashes midway?

What concurrent requests can race?

Is a UNIQUE constraint sufficient?

If not, what locking or optimistic mechanism is required?

What isolation level is actually needed?

What is the transaction boundary?

Can the operation be safely retried?

Does the operation also require idempotency?