# Case Study: Social Network — Full 23-Section Design

## 1. Requirements / Scope
Users create profiles, follow other users, publish posts, like/comment, view feeds, and search users/posts.

## 2. Scale
Illustrative assumptions: 50M users, 10M DAU, high read traffic, high fan-out for popular creators, large post/interaction volume.

## 3. Features & Roles
User, moderator, administrator, automated moderation/notification systems.

## 4. Read vs Write
Feed reads are extremely high. Post creation and social interactions are write-heavy but usually less correctness-sensitive than payments.

## 5. Concurrency
Likes, follows and counters can receive concurrent writes. The system must define whether exact counters or eventually consistent counters are required.

## 6. Entities
User, Follow, Post, Comment, Like, Media, FeedEntry/FeedProjection, Notification.

## 7. Relationships / Cardinality
User N:M User through Follow; User 1:N Post; Post 1:N Comment; User N:M Post through Like.

## 8. Schema
Relational modeling can represent identity and social relationships. Feed projections may be separately stored for high-volume read access.

## 9. SQL vs NoSQL + Trade-offs
Relational DB is viable for core identity/social relationships. A graph database may be useful if variable-depth relationship traversal is central. A key-value/document store may support feed projections at very high scale.

## 10. Important Queries
Home feed, follower list, following list, post detail, comments, mutual connections, user/post search.

## 11. Indexes
Follow `(follower_id, followed_id)` and reverse access `(followed_id, follower_id)`. Posts by author/time. Comments by post/time. Likes by post/user with uniqueness as required.

## 12. Cache
Cache hot profiles, posts and feed fragments. Define invalidation/freshness carefully.

## 13. Replication
Read replicas can serve profile/post/history reads. Feed systems may use dedicated read models.

## 14. Search
OpenSearch may support user/post full-text search and relevance.

## 15. Partitioning
Large interaction/history tables can be partitioned based on lifecycle or access patterns.

## 16. Sharding
At very high scale, user-based sharding can distribute social data. But follower/following queries and celebrity fan-out can create cross-shard/hotspot challenges.

## 17. Pagination
Cursor/keyset pagination is strongly preferred for feeds, posts and comments at scale.

## 18. Transactions
Use transactions for operations that must update multiple authoritative records atomically. Avoid unnecessarily long transactions for feed generation.

## 19. Failure Handling
Feed generation, cache and search can degrade independently. A failed projection should be rebuildable from authoritative data.

## 20. Idempotency
Post creation, interaction commands and notification processing should define duplicate handling where retries can occur.

## 21. Consistency
Strong enough for identity and critical relationship constraints. Eventual consistency is acceptable for feeds, counters, search and notifications if product semantics permit.

## 22. Final Architecture
Relational core + cache + search + scalable feed projection. Graph DB is optional and justified only by actual traversal requirements.

## 23. Trade-offs
The design accepts eventual consistency for high-scale derived views to keep the authoritative model manageable.
