Failure Handling — Deep Explanation

Core Reasoning Summary

Definition: Failure handling defines how an architecture behaves when databases, dependencies, networks, caches, search systems, replicas, or application components fail.

Why it exists: Failures can be ambiguous and partial. A timeout may occur after a server has already committed an operation, while one dependency can fail while others remain healthy.

When to use: Apply explicit failure behavior to every important dependency and to operations whose retries can create side effects.

When NOT to use: Do not blindly retry every failure or automatically fall back to another system. The correct response depends on whether the operation is retryable, whether it is idempotent, and whether the fallback can safely handle the additional load.

Primary rule: Failure behavior must be defined per dependency and per operation. Timeout, retry, fallback, failover, recovery, and degraded operation solve different failure scenarios.

Advantages: Prevents ambiguous outcomes, duplicate side effects, and cascading failures.

Disadvantages: Explicit failure handling adds implementation and operational complexity and requires capacity and recovery planning.

Review questions:

Can a timeout occur after the operation committed?

Is this operation safe to retry?

Is idempotency required before retrying?

What happens if a cache or search system fails?

Can the source database safely absorb fallback traffic?

What happens during partial failure?

How are failover and recovery handled?

Failure types

timeout

connection failure

database outage

deadlock

application crash

cache failure

search failure

replica lag

disk/storage exhaustion

Timeout ambiguity

A timeout does not prove that the server did not execute the operation. It may have committed before the client timed out.

Timeout Boundary

A timeout establishes only that the client did not receive a response within the expected period. It does not establish whether the server committed, failed, or is still processing the operation.

Therefore, a client must not blindly retry a side-effecting operation unless the retry semantics are known to be safe, typically through idempotency or another explicit deduplication mechanism.

Retry

Retries should be bounded and use backoff. Only retry operations that are known to be retryable. Side-effecting operations should use idempotency where necessary.

Retry Boundary

Bounded retries and backoff reduce repeated load during transient failures, but they do not make a non-idempotent operation safe to repeat.

An operation should be retried only when its failure semantics are understood and duplicate execution cannot create an unacceptable side effect.

Deadlocks

Two transactions can each hold a lock the other needs. The database may abort one transaction. Applications should be prepared to retry suitable transactions.

Cache failure

If cache is derived state, the application may fall back to the source database if capacity permits. If it cannot, the architecture must define degraded behavior.

Cache-Fallback Boundary

Falling back to the source database is sufficient only when the source has enough capacity and the resulting latency/availability behavior is acceptable.

A cache outage does not automatically imply that every request should hit the source database. If fallback could overload the source, the architecture must define a degraded or failed response.

Search failure

If search is derived state, transactions can often continue while indexing catches up. The system should support retries and reindexing.

Search-Failure Boundary

Transactions can continue independently of search failure only when search is genuinely non-critical to the transaction's correctness or completion.

Retry and reindexing are sufficient only when the authoritative source remains available and the search projection is reconstructable.

Database failure

The design should cover failover, recovery, backups and user-visible behavior.

Database-Failure Boundary

Failover addresses continued service when an alternate database instance can safely take over; backup/recovery addresses restoration after data loss or corruption.

Failover alone is not a substitute for backups, and backups alone do not provide continuous service during an outage.

Partial failure

One service/database can fail while other components remain healthy. Good architecture defines each dependency's failure behavior instead of assuming everything fails together.

Partial-Failure Boundary

A dependency failure should be isolated only when the dependent operation can safely continue without violating correctness.

Continuing the rest of the system is not automatically preferable to failing the operation. For correctness-sensitive operations, refusing or degrading the operation may be the correct behavior.



Common Review Mistakes

Treating a timeout as proof that the operation failed.

Retrying side-effecting operations without idempotency or deduplication.

Assuming every transient error is retryable.

Falling back to the database without checking source capacity.

Assuming search failure is always non-critical.

Treating failover as a substitute for backup and recovery.

Assuming partial failure should always be hidden from the user.

Retrying indefinitely and creating a retry storm.