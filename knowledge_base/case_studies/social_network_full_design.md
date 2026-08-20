Case Study: Social Network — Full 23-Section Design

1. Requirements / Scope

Users create profiles, follow other users, publish posts, like/comment, view feeds, and search users/posts.

Core Reasoning Summary

Definition: This architecture uses a relational core for authoritative identity and social relationships, while scalable feed projections, caches, and search systems serve high-volume derived reads.

Why it exists: Social networks have extremely high read volume and fan-out, making it useful to separate authoritative relationships from derived feed and discovery workloads.

When to use: Use this pattern when identity and relationship constraints require authoritative storage but feeds, counters, search, and notifications can tolerate controlled eventual consistency.

When NOT to use: Do not introduce a graph database merely because the data contains relationships. Use it when variable-depth traversal is a central requirement that the relational model does not handle adequately.

Primary architectural rule: Derived feed/search/cache systems may be rebuilt or refreshed from authoritative data and must not silently become the authoritative identity or relationship store.

Advantages: Strong core integrity while allowing high-scale derived read models.

Disadvantages: Feed projections, caches, and search introduce synchronization, rebuild, freshness, and fan-out complexity.

Review questions:

Which relationships are authoritative?

Which data can be eventually consistent?

When would a graph database actually be justified?

How is a failed feed projection recovered?

What happens when a celebrity causes extreme fan-out?

2. Scale

Illustrative assumptions: 50M users, 10M DAU, high read traffic, high fan-out for popular creators, large post/interaction volume.

3. Features & Roles

User, moderator, administrator, automated moderation/notification systems.

4. Read vs Write

Feed reads are extremely high. Post creation and social interactions are write-heavy but usually less correctness-sensitive than payments.

5. Concurrency

Likes, follows and counters can receive concurrent writes. The system must define whether exact counters or eventually consistent counters are required.

6. Entities

User, Follow, Post, Comment, Like, Media, FeedEntry/FeedProjection, Notification.

7. Relationships / Cardinality

User N User through Follow; User 1 Post; Post 1 Comment; User N Post through Like.

8. Schema

Relational modeling can represent identity and social relationships. Feed projections may be separately stored for high-volume read access.

9. SQL vs NoSQL + Trade-offs

Relational DB is viable for core identity/social relationships. A graph database may be useful if variable-depth relationship traversal is central. A key-value/document store may support feed projections at very high scale.

Graph Database Boundary

A graph database is justified when variable-depth relationship traversal is a central workload and provides a meaningful advantage over the relational model.

A graph-shaped data model alone is not sufficient justification for introducing a graph database.

Simple identity, direct follow/follower relationships, and ordinary relationship constraints can remain in the relational core when relational queries satisfy the actual workload.

10. Important Queries

Home feed, follower list, following list, post detail, comments, mutual connections, user/post search.

11. Indexes

Follow (follower_id, followed_id) and reverse access (followed_id, follower_id). Posts by author/time. Comments by post/time. Likes by post/user with uniqueness as required.

12. Cache

Cache hot profiles, posts and feed fragments. Define invalidation/freshness carefully.

13. Replication

Read replicas can serve profile/post/history reads. Feed systems may use dedicated read models.

14. Search

OpenSearch may support user/post full-text search and relevance.

15. Partitioning

Large interaction/history tables can be partitioned based on lifecycle or access patterns.

16. Sharding

At very high scale, user-based sharding can distribute social data. But follower/following queries and celebrity fan-out can create cross-shard/hotspot challenges.

17. Pagination

Cursor/keyset pagination is strongly preferred for feeds, posts and comments at scale.

18. Transactions

Use transactions for operations that must update multiple authoritative records atomically. Avoid unnecessarily long transactions for feed generation.

Feed Projection Boundary

A feed projection is a derived read model and may be rebuilt from authoritative data when the projection design supports rebuilding.

The projection is therefore not required to be the authoritative source of identity, posts, or social relationships.

A failed feed projection can reduce feed freshness or availability without corrupting the authoritative relational data.

19. Failure Handling

Feed generation, cache and search can degrade independently. A failed projection should be rebuildable from authoritative data.

20. Idempotency

Post creation, interaction commands and notification processing should define duplicate handling where retries can occur.

21. Consistency

Strong enough for identity and critical relationship constraints. Eventual consistency is acceptable for feeds, counters, search and notifications if product semantics permit.

Eventual Consistency Boundary

Eventual consistency is sufficient for a derived view only when temporary staleness is allowed by the product semantics.

It is not a blanket rule that feeds, counters, search, or notifications must always be eventually consistent.

If a particular feature requires an immediately authoritative value, that feature's authoritative state must use the appropriate consistency mechanism.

22. Final Architecture

Relational core + cache + search + scalable feed projection. Graph DB is optional and justified only by actual traversal requirements.

23. Trade-offs

The design accepts eventual consistency for high-scale derived views to keep the authoritative model manageable.

Common Mistakes

Choosing a graph database solely because the domain contains relationships.

Treating a feed projection as authoritative social data.

Assuming eventual consistency is acceptable without checking product semantics.

Ignoring celebrity fan-out and hotspot behavior.

Treating cached counters as exact when exact counters are actually required.

Introducing sharding without considering cross-shard follower/following queries.