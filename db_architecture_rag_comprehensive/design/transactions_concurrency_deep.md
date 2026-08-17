# Transactions and Concurrency — Deep Explanation

## Transaction definition
A transaction groups database operations into a logical unit whose required changes must satisfy the application's business invariants.

## ACID
Atomicity: all required changes commit or roll back.
Consistency: constraints and business invariants remain valid.
Isolation: concurrent operations do not create prohibited anomalies.
Durability: committed changes survive normal failure according to the database's durability guarantees.

## Business invariant first
Instead of saying "we need ACID," state what must never happen.

Examples:
- a seat must not be confirmed for two users
- inventory must not become negative
- a payment must not be recorded twice
- a transfer must not debit one account without crediting the other

## Pessimistic concurrency
Lock the relevant row/resource while the critical operation executes.

Benefit: direct protection against concurrent modification.
Cost: waiting, contention and possible deadlocks.

## Optimistic concurrency
Use a version/check condition and detect conflicts.

Example:
`UPDATE item SET version=version+1 WHERE id=? AND version=?`

If zero rows change, another operation won and the caller can retry/fail.

## Unique constraints
Database uniqueness is valuable because two application instances can race even if both perform an availability check.

## Isolation
Isolation level should be selected based on the anomaly that must be prevented. Stronger isolation can increase contention and reduce concurrency.

## Transaction duration
Long transactions hold resources longer and increase contention. Keep critical transactions short where possible.

## Review checklist
- What invariant is protected?
- What rows are read and written?
- What happens under concurrent requests?
- Is a constraint needed?
- Can deadlock occur?
- Is retry safe?
