Replication — Deep Explanation

Core Reasoning Summary

Definition: Replication maintains additional database copies that can support availability, failover, and read scaling.

Why it exists: Replication can provide alternate copies for read traffic and failure recovery, but the consistency and durability behavior depends on how replication acknowledgements and failover are configured.

When to use: Consider replication when read load, availability, or failover requirements justify additional database copies.

When NOT to use: Do not add replicas merely because the system has many users, and do not treat replication as a substitute for backups or a solution to primary write-capacity limits.

Primary rule: Replication creates copies; it does not automatically make those copies current, writable, strongly consistent, or sufficient for backup/recovery.

Advantages: Read scaling, additional availability/failover options, and additional copies of data.

Disadvantages: Replication lag, stale reads, network sensitivity, failover complexity, split-brain risks, and additional operational cost.

Review questions:

Is the goal read scaling, availability, failover, or durability?

Is asynchronous lag acceptable?

Which reads must observe the primary immediately?

What happens during failover?

How is split-brain prevented?

What happens to stale replicas?

Are backups still required?

Does the architecture actually need more read capacity or more write capacity?

Replication creates additional database copies. It is mainly used for availability, failover and read scaling.

Primary/replica

A primary accepts writes. Replicas receive changes and may serve reads.

Asynchronous replication

The primary does not wait for every replica before acknowledging. This can reduce write latency but introduces replication lag and a potential loss window during failure.

Asynchronous-Replication Boundary

Asynchronous replication is sufficient only when the application can tolerate the resulting lag and potential loss window for the relevant failure scenarios.

It does not guarantee that a committed write is already present on every replica when the primary acknowledges it.

Synchronous replication

The write waits for required replica acknowledgement according to the configured protocol. This can improve durability characteristics but may increase latency and sensitivity to network/replica failures.

Synchronous-Replication Boundary

Synchronous replication improves durability characteristics only to the extent defined by the configured acknowledgement and failure protocol.

It does not automatically provide application-level transaction semantics, eliminate every failure mode, or guarantee that all replicas are equivalent in every operational state.

Read-after-write problem

A write reaches the primary. The next read goes to a lagging replica. The client sees stale data.

Read-Consistency Boundary

Replication does not automatically provide read-after-write consistency.

If a user-facing operation must immediately observe its own write, the architecture must explicitly route or coordinate that read using an appropriate strategy such as primary reads, session stickiness, consistency-aware routing, or a supported replication-position mechanism.

Possible strategies:

read critical paths from primary

session stickiness

consistency-aware routing

wait for an appropriate replication position where supported

Failover

A replica can be promoted after primary failure. Automated failover improves availability but must handle stale replicas, split-brain risks and recovery procedures.

Failover Boundary

Promoting a replica can restore service only when the promoted replica is a safe candidate and the failover protocol correctly handles stale state, concurrent primaries, client routing, and recovery.

Automated failover improves availability; it does not eliminate the need for backup/recovery planning or prove that no committed data can be lost.

What replication does NOT solve

Replication does not automatically increase write capacity. It does not replace backups. It does not remove consistency concerns.

Capacity and Recovery Boundary

Read replicas can reduce read load when reads can be served from replicas.

They do not automatically increase the capacity of the primary write path. If writes are the bottleneck, the architecture must evaluate the actual write-capacity problem rather than adding read replicas by default.

Replication also does not replace backups because a replicated error, deletion, or corruption can propagate to replicas.



Common Review Mistakes

Adding replicas because user count is large without identifying read load or availability requirements.

Treating asynchronous replicas as immediately consistent.

Treating synchronous replication as a complete guarantee of durability or correctness.

Routing every read to replicas without considering read-after-write requirements.

Treating failover as proof that no data can be lost.

Using replicas to solve a primary write-capacity bottleneck.

Treating replication as a backup strategy.

Ignoring stale replicas, split-brain risks, or recovery procedures.