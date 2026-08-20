Case Study: Money Transfer / Banking Ledger — Full 23-Section Design

1. Requirements / Scope

Customers view accounts and balances, initiate transfers, and receive transaction history. The system must prevent duplicate transfers and preserve financial correctness.

Core Reasoning Summary

Definition: This architecture treats the relational database as the authoritative transactional system for accounts, transfers, and immutable ledger state.

Why it exists: Financial transfers require correctness, auditability, duplicate protection, and well-defined transaction boundaries. These requirements are more important than minimizing latency on every path.

When to use: Use this pattern when the system must preserve authoritative financial state, prevent invalid concurrent updates, and provide an auditable transaction history.

When NOT to use: Do not apply the same strong-consistency requirement to every derived workload. Reporting, search, and other non-authoritative projections may use eventually consistent systems when the product semantics allow it.

Primary architectural rule: The relational transactional ledger is the source of truth. Cache, search, replicas, and reporting projections may improve read performance but must not replace authoritative financial state.

Advantages: Strong integrity, transactional correctness, auditability, and clear ownership of financial state.

Disadvantages: Strong consistency and transactional coordination can reduce scalability and increase latency compared with fully asynchronous or eventually consistent designs.

Review questions:

What data is authoritative?

Which invariants must hold inside one transaction?

What prevents duplicate transfer requests?

Which reads may safely use replicas or eventual consistency?

What happens when an external transfer provider times out or retries?

2. Scale

Illustrative assumptions: 2M active users, 2K average requests/sec, 10K peak, high correctness requirements, large immutable transaction history.

3. Features & Roles

Customer, operations/admin, compliance/auditor, payment/transfer network.

4. Read vs Write

Balance reads and transaction history are read-heavy. Transfers are lower-volume but extremely correctness-sensitive.

5. Concurrency

Concurrent withdrawals/transfers must not produce invalid balances. Atomic updates, transactions and proper locking/isolation are essential.

6. Entities

Customer, Account, LedgerEntry, Transfer, TransferAttempt, Beneficiary, AuditEvent.

7. Relationships / Cardinality

Customer 1 Account; Account 1 LedgerEntry; Transfer references source and destination accounts; transfer may have multiple processing attempts.

8. Schema

Use immutable ledger entries for financial movements rather than overwriting historical facts. Store transaction status and external references with uniqueness constraints.

9. SQL vs NoSQL + Trade-offs

A relational database is the strongest primary choice because constraints, transactions and consistency dominate. NoSQL may support secondary workloads but should not replace the authoritative ledger without a strong reason.

10. Important Queries

Current account balance, transaction history, transfer status, duplicate external reference detection, audit lookup.

11. Indexes

Account history: (account_id, created_at, id). Unique external transaction/reference IDs. Transfer status/time indexes for operational processing.

12. Cache

Cache can accelerate non-critical profile/configuration reads. Do not use a stale cache as authoritative account balance.

13. Replication

Read replicas may serve reports, but balance reads after writes may need primary consistency.

14. Search

A search engine may support operational/audit search but should not become the source of truth.

Derived-System Boundary

A cache, read replica, or search projection may satisfy a read-performance or reporting requirement when stale data is acceptable.

It is not additionally required for authoritative balance or ledger correctness. The authoritative relational database alone can provide the correctness boundary.

If a derived system is introduced, failure or staleness of that system must not make its data authoritative over the ledger.

15. Partitioning

Ledger history can become an excellent candidate for time-based partitioning because data grows continuously and old periods may have different lifecycle requirements.

16. Sharding

Sharding is a later-stage decision. Account ownership can provide a candidate shard key, but cross-account transfers create cross-shard transaction complexity.

17. Pagination

Keyset pagination is appropriate for long transaction histories.

18. Transactions

A transfer must atomically enforce its financial invariant. Ledger entries and transfer state require carefully defined transaction boundaries.

Transaction Boundary

A database transaction is sufficient to make the authoritative database changes within its transaction boundary atomic and consistent.

It is not sufficient to atomically control an external payment or transfer network that does not participate in the database transaction. External operations therefore require explicit state, retry behavior, idempotency, and reconciliation.

For purely internal database state, do not add an external distributed-transaction mechanism merely because external transfers require reconciliation.

19. Failure Handling

Timeouts, deadlocks, duplicate callbacks, partial external transfer failures and recovery/reconciliation require explicit state machines.

20. Idempotency

Transfer requests and external provider callbacks require idempotency keys/reference uniqueness.

Idempotency Boundary

A unique idempotency key or external reference is sufficient to prevent multiple accepted requests with the same key/reference from creating multiple logical results within the defined uniqueness scope.

It does not by itself make the financial transfer atomic, guarantee successful external settlement, or resolve ambiguous provider failures. Transaction boundaries, transfer state, and reconciliation are still required for those cases.

Do not generalize the external-failure caveat to ordinary duplicate-request handling: when the same request is presented with the same correctly scoped idempotency key, the uniqueness/idempotency mechanism is the mechanism that prevents duplicate processing.

21. Consistency

Strong consistency is required for authoritative balances and ledger state. Reporting/search projections may be eventually consistent.

22. Final Architecture

Relational transactional ledger + controlled read/reporting projections + audited operational processes.

23. Trade-offs

The design prioritizes correctness and auditability over low latency at every path. It deliberately avoids cache-as-source-of-truth and premature sharding.

Common Mistakes

Treating a cache or search projection as authoritative balance state.

Assuming a database transaction automatically includes an external payment network.

Treating a unique reference as a complete solution to external failure and reconciliation.

Using eventual consistency for an authoritative financial invariant.

Sharding before the workload requires it without accounting for cross-account transfer complexity.

Treating duplicate callbacks as equivalent to successful external settlement.