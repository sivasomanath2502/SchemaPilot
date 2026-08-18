# Case Study: Food Delivery Platform — Full 23-Section Design

## 1. Requirements / Scope
Customers discover restaurants, browse menus, place orders, pay, and track order status. Restaurants manage menus and accept/reject orders. Delivery agents receive and update delivery tasks.

## 2. Scale
Illustrative assumptions: 5M DAU, 3K average RPS, 15K peak RPS, concentrated peaks at meal times, high location/status update frequency.

## 3. Features & Roles
Customer, restaurant, delivery agent, administrator, payment provider.

## 4. Read vs Write
Restaurant/menu discovery is read-heavy. Order creation and status transitions are write-sensitive. Delivery location/status can be high-frequency.

## 5. Concurrency
Avoid accepting the same order twice, avoid conflicting restaurant order transitions, and prevent duplicate payment/order creation.

## 6. Entities
User, Restaurant, RestaurantBranch, Menu, MenuItem, Cart, Order, OrderItem, Payment, DeliveryTask, DeliveryAgent, OrderStatusHistory.

## 7. Relationships / Cardinality
Restaurant 1:N branches; branch 1:N menu/menu items; user 1:N orders; order 1:N items; order 1:1 or 1:N delivery task depending on reassignment design.

## 8. Schema
Use relational tables for order/payment correctness. Preserve order-time item name/price in OrderItem because menu values can change later.

## 9. SQL vs NoSQL + Trade-offs
MySQL/PostgreSQL for transactional order state. Redis for short-lived cache/location state where appropriate. OpenSearch for restaurant/menu discovery if search becomes advanced.

## 10. Important Queries
Nearby/available restaurants, restaurant menu, customer order history, active delivery tasks, order state transitions.

## 11. Indexes
Index restaurant status/location lookup as appropriate, orders(user_id, created_at), delivery_task(agent_id, status), and order status/time queries.

## 12. Cache
Cache menus and restaurant metadata. Location/state caches require explicit freshness rules.

## 13. Replication
Read replicas can serve discovery and historical reads. Critical order-state transitions should use the authoritative primary.

## 14. Search
OpenSearch may support restaurant/menu text search, cuisine filtering and relevance.

## 15. Partitioning
Large order/status history can eventually be partitioned by time.

## 16. Sharding
Avoid initially. Geographic sharding may eventually fit a globally distributed service, but cross-region order/payment semantics must remain clear.

## 17. Pagination
Cursor pagination for restaurant lists and order feeds. Offset can remain for small administrative lists.

## 18. Transactions
Order creation and order items should be atomic. Payment state is reconciled separately. Restaurant acceptance and order transitions should use valid state transitions.

## 19. Failure Handling
Payment timeout, restaurant service outage, delivery-agent reassignment, cache failure and duplicate callbacks need explicit behavior.

## 20. Idempotency
Order creation and payment commands need idempotency. External payment/webhook references should be unique.

## 21. Consistency
Strong for order/payment state; eventual for search, location display and recommendations.

## 22. Final Architecture
Relational transactional core + optional Redis + optional OpenSearch + async/event-driven projections as scale demands.

## 23. Trade-offs
Favor transactional correctness for orders while allowing eventual consistency for discovery and tracking projections.
