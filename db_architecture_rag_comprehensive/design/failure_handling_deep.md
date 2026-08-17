# Failure Handling — Deep Explanation

## Failure types
- timeout
- connection failure
- database outage
- deadlock
- application crash
- cache failure
- search failure
- replica lag
- disk/storage exhaustion

## Timeout ambiguity
A timeout does not prove that the server did not execute the operation. It may have committed before the client timed out.

## Retry
Retries should be bounded and use backoff. Only retry operations that are known to be retryable. Side-effecting operations should use idempotency where necessary.

## Deadlocks
Two transactions can each hold a lock the other needs. The database may abort one transaction. Applications should be prepared to retry suitable transactions.

## Cache failure
If cache is derived state, the application may fall back to the source database if capacity permits. If it cannot, the architecture must define degraded behavior.

## Search failure
If search is derived state, transactions can often continue while indexing catches up. The system should support retries and reindexing.

## Database failure
The design should cover failover, recovery, backups and user-visible behavior.

## Partial failure
One service/database can fail while other components remain healthy. Good architecture defines each dependency's failure behavior instead of assuming everything fails together.
