# Transactions and Concurrency — Deep Explanation

## Business invariant first
Before reaching for ACID/transactions as a checkbox, state explicitly what must never happen:
- What must never happen?
- Which operations must succeed together, or not at all?
- What happens if the process crashes midway through?

## Examples
- **Booking**: one seat must not be confirmed for two users.
- **Inventory**: available quantity must not become negative due to concurrent purchases.
- **Payment**: a financial state transition must not be left partially applied (debited but not credited, or vice versa).

## Transaction definition
A transaction groups database operations into a logical unit whose required changes must together satisfy the application's business invariants — either all of them happen, or none do.

## ACID
- **Atomicity** — all required changes commit together, or none do.
- **Consistency** — the database's declared constraints and business invariants remain valid before and after.
- **Isolation** — concurrent transactions don't observe each other's uncommitted intermediate state in ways that violate business rules.
- **Durability** — once committed, changes survive normal failure according to the database's durability guarantees.

## Pessimistic concurrency
Lock the relevant row/resource for the duration of the critical operation, preventing any other transaction from modifying it concurrently.

Benefit: direct, straightforward protection against concurrent modification.
Cost: other requests wait for the lock, creating contention; poor lock ordering across transactions can cause deadlocks.

## Optimistic concurrency
Use a version number or condition check, and detect conflicts after the fact rather than locking upfront.

Example:
```sql
UPDATE item SET version = version + 1 WHERE id = ? AND version = ?
```
If zero rows are affected, another transaction won the race first — the caller can retry or fail explicitly. Better suited to workloads where conflicts are rare, since it avoids the cost of holding locks for operations that usually don't actually conflict.

## Unique constraints as a concurrency tool
Database-level uniqueness is valuable specifically because two application instances can race even if both independently perform an "is this available?" check beforehand — see the seat-booking race example in `schema_constraints.md`. A unique constraint is the reliable backstop that an application-level check alone cannot be.

## Isolation levels
Choose isolation level based on which anomalies the business genuinely cannot tolerate (dirty reads, non-repeatable reads, phantom reads) — not by defaulting to the strictest option everywhere. Stronger isolation reduces the anomalies possible but also reduces concurrency/throughput, since it typically requires more locking or more conflict detection.

## Transaction duration
Long-running transactions hold locks/resources longer, increasing contention with other transactions. Keep critical transactions as short as possible — do work like calling external APIs or slow computations *outside* the transaction boundary where feasible, only wrapping the actual database writes that must be atomic.

## Deadlocks
Two transactions can each hold a lock the other needs, with neither able to proceed. The database typically detects this and aborts one transaction to break the cycle. Applications should be prepared to catch this and retry the aborted transaction where it's safe to do so.

## Idempotency and transactions — related but distinct
A transaction protects atomic database changes within one request. Idempotency (see `idempotency_deep.md`) protects against duplicate *logical requests* (e.g. a retried HTTP call). Booking and payment flows commonly need both together: a transaction to keep the database change atomic, and an idempotency key to prevent a retried request from repeating that change entirely.

## Common mistakes
- Reaching for "just wrap it in a transaction" without first stating the specific business invariant being protected.
- Using the strictest isolation level everywhere by default, unnecessarily reducing throughput.
- Holding a transaction open across a slow external call (e.g. a payment gateway API), increasing contention risk.
- Relying only on an application-level availability check for a race-prone invariant instead of a database constraint (see `schema_constraints.md`).
- Confusing idempotency with transactional atomicity — they solve different problems and are often both needed together.

## Review checklist
- What invariant is protected?
- What rows are read and written, and in what order?
- What happens under concurrent requests hitting the same rows?
- Is a database constraint needed in addition to (or instead of) the transaction?
- Can a deadlock occur, and is retry safe for the operations involved?
- Is the transaction as short as it can reasonably be?

## Source / grounding
https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-model.html
