# Transactions and Concurrency


## Business invariant first
A transaction is useful because a business rule must remain true despite failure and concurrency.

Ask:
- What must never happen?
- Which operations must succeed together?
- What happens if the process crashes midway?

## Examples
Booking: one seat must not be confirmed twice.
Inventory: available quantity must not become negative due to concurrent purchases.
Payment: financial state transitions must not become partially applied.

## Tools
Depending on the database:
- transaction
- row-level locking
- unique constraint
- optimistic version check
- atomic update
- appropriate isolation level

## Isolation
Isolation level should be selected based on anomalies the business cannot tolerate. Stronger isolation can reduce concurrency.

## Review rule
Every critical invariant should map to an explicit transaction/concurrency strategy.


## Source / grounding
https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-model.html
