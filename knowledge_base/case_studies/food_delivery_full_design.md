Case Study: Food Delivery Platform — Full 23-Section Design

1. Requirements / Scope

Customers discover restaurants, browse menus, place orders, pay, and track order status. Restaurants manage menus and accept/reject orders. Delivery agents receive and update delivery tasks.

Core Reasoning Summary

Definition: This architecture uses a relational transactional core for authoritative order and payment state while allowing discovery, location display, search, and other derived workloads to use specialized or eventually consistent systems.

Why it exists: Food delivery combines correctness-sensitive order/payment transitions with high-volume restaurant discovery and frequent delivery-state updates.

When to use: Use this pattern when order state and payment state must remain correct while discovery and tracking workloads can tolerate controlled staleness.

When NOT to use: Do not force every restaurant, location, search, or recommendation read through the strongest consistency model when the product semantics permit eventual consistency.

Primary architectural rule: The relational transactional system owns authoritative order/payment state. Redis, OpenSearch, replicas, and projections are supporting systems.

Advantages: Strong transactional correctness for orders while allowing independent scaling of discovery and derived workloads.

Disadvantages: Eventual consistency introduces freshness concerns, and multiple derived systems increase operational complexity.

Review questions:

Which state is authoritative?

Which order transitions must be atomic?

What prevents duplicate order/payment creation?

Which data can safely be stale?

What happens when a payment callback is duplicated or delayed?

2. Scale

Illustrative assumptions: 5M DAU, 3K average RPS, 15K peak RPS, concentrated peaks at meal times, high location/status update frequency.

3. Features & Roles

Customer, restaurant, delivery agent, administrator, payment provider.

4. Read vs Write

Restaurant/menu discovery is read-heavy. Order creation and status transitions are write-sensitive. Delivery location/status can be high-frequency.

5. Concurrency

Avoid accepting the same order twice, avoid conflicting restaurant order transitions, and prevent duplicate payment/order creation.

6. Entities

User, Restaurant, RestaurantBranch, Menu, MenuItem, Cart, Order, OrderItem, Payment, DeliveryTask, DeliveryAgent, OrderStatusHistory.

7. Relationships / Cardinality

Restaurant 1 branches; branch 1 menu/menu items; user 1 orders; order 1 items; order 1:1 or 1 delivery task depending on reassignment design.

8. Schema

Use relational tables for order/payment correctness. Preserve order-time item name/price in OrderItem because menu values can change later.

9. SQL vs NoSQL + Trade-offs

MySQL/PostgreSQL for transactional order state. Redis for short-lived cache/location state where appropriate. OpenSearch for restaurant/menu discovery if search becomes advanced.

10. Important Queries

Nearby/available restaurants, restaurant menu, customer order history, active delivery tasks, order state transitions.

11. Indexes

Index restaurant status/location lookup as appropriate, orders(user_id, created_at), delivery_task(agent_id, status), and order status/time queries.

12. Cache

Cache menus and restaurant metadata. Location/state caches require explicit freshness rules.

Cache Boundary

A cache is sufficient for a read optimization when stale data is acceptable under the product's freshness requirements.

It is not required to establish authoritative order correctness, and stale cached state must not override the authoritative transactional state.

The freshness requirement must be defined separately for menus, restaurant availability, and delivery location/state.

13. Replication

Read replicas can serve discovery and historical reads. Critical order-state transitions should use the authoritative primary.

14. Search

OpenSearch may support restaurant/menu text search, cuisine filtering and relevance.

15. Partitioning

Large order/status history can eventually be partitioned by time.

16. Sharding

Avoid initially. Geographic sharding may eventually fit a globally distributed service, but cross-region order/payment semantics must remain clear.

17. Pagination

Cursor pagination for restaurant lists and order feeds. Offset can remain for small administrative lists.

18. Transactions

Order creation and order items should be atomic. Payment state is reconciled separately. Restaurant acceptance and order transitions should use valid state transitions.

Transaction Boundary

A database transaction is sufficient to make the authoritative order and order-item changes within that transaction atomic.

It is not an atomic transaction with the external payment provider. Payment state therefore remains a separate state machine and must be reconciled independently.

Do not infer that eventual consistency in payment-provider integration makes the local order transaction unnecessary.

19. Failure Handling

Payment timeout, restaurant service outage, delivery-agent reassignment, cache failure and duplicate callbacks need explicit behavior.

20. Idempotency

Order creation and payment commands need idempotency. External payment/webhook references should be unique.

Idempotency Boundary

An idempotency key or unique external reference prevents duplicate processing of the same logical command within its defined scope.

It does not by itself guarantee successful payment, valid order-state transitions, or completion of an external operation.

Those concerns still require transaction boundaries, state validation, and reconciliation where applicable.

21. Consistency

Strong for order/payment state; eventual for search, location display and recommendations.

22. Final Architecture

Relational transactional core + optional Redis + optional OpenSearch + async/event-driven projections as scale demands.

23. Trade-offs

Favor transactional correctness for orders while allowing eventual consistency for discovery and tracking projections.

Common Mistakes

Treating cached restaurant or delivery state as authoritative.

Assuming a database transaction includes the payment provider.

Treating duplicate callbacks as successful payment confirmation.

Applying strong consistency to every discovery and tracking read without a product requirement.

Introducing geographic sharding without defining cross-region order/payment semantics.