# Case Study: Money Transfer / Banking Ledger — Full 23-Section Design

## 1. Requirements / Scope
Customers view accounts and balances, initiate transfers, and receive transaction history. The system must prevent duplicate transfers and preserve financial correctness.

## 2. Scale
Illustrative assumptions: 2M active users, 2K average requests/sec, 10K peak, high correctness requirements, large immutable transaction history.

## 3. Features & Roles
Customer, operations/admin, compliance/auditor, payment/transfer network.

## 4. Read vs Write
Balance reads and transaction history are read-heavy. Transfers are lower-volume but extremely correctness-sensitive.

## 5. Concurrency
Concurrent withdrawals/transfers must not produce invalid balances. Atomic updates, transactions and proper locking/isolation are essential.

## 6. Entities
Customer, Account, LedgerEntry, Transfer, TransferAttempt, Beneficiary, AuditEvent.

## 7. Relationships / Cardinality
Customer 1:N Account; Account 1:N LedgerEntry; Transfer references source and destination accounts; transfer may have multiple processing attempts.

## 8. Schema
Use immutable ledger entries for financial movements rather than overwriting historical facts. Store transaction status and external references with uniqueness constraints.

## 9. SQL vs NoSQL + Trade-offs
A relational database is the strongest primary choice because constraints, transactions and consistency dominate. NoSQL may support secondary workloads but should not replace the authoritative ledger without a strong reason.

## 10. Important Queries
Current account balance, transaction history, transfer status, duplicate external reference detection, audit lookup.

## 11. Indexes
Account history: `(account_id, created_at, id)`. Unique external transaction/reference IDs. Transfer status/time indexes for operational processing.

## 12. Cache
Cache can accelerate non-critical profile/configuration reads. Do not use a stale cache as authoritative account balance.

## 13. Replication
Read replicas may serve reports, but balance reads after writes may need primary consistency.

## 14. Search
A search engine may support operational/audit search but should not become the source of truth.

## 15. Partitioning
Ledger history can become an excellent candidate for time-based partitioning because data grows continuously and old periods may have different lifecycle requirements.

## 16. Sharding
Sharding is a later-stage decision. Account ownership can provide a candidate shard key, but cross-account transfers create cross-shard transaction complexity.

## 17. Pagination
Keyset pagination is appropriate for long transaction histories.

## 18. Transactions
A transfer must atomically enforce its financial invariant. Ledger entries and transfer state require carefully defined transaction boundaries.

## 19. Failure Handling
Timeouts, deadlocks, duplicate callbacks, partial external transfer failures and recovery/reconciliation require explicit state machines.

## 20. Idempotency
Transfer requests and external provider callbacks require idempotency keys/reference uniqueness.

## 21. Consistency
Strong consistency is required for authoritative balances and ledger state. Reporting/search projections may be eventually consistent.

## 22. Final Architecture
Relational transactional ledger + controlled read/reporting projections + audited operational processes.

## 23. Trade-offs
The design prioritizes correctness and auditability over low latency at every path. It deliberately avoids cache-as-source-of-truth and premature sharding.
