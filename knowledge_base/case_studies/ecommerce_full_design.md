Case Study: E-commerce Platform — Full 23-Section Design

Use this example to teach order, inventory, payment, catalog, search, and consistency reasoning.

1. Requirements / Scope

Customers browse products, search/filter the catalog, manage carts, place orders, pay, and track orders. Sellers/admins manage products and inventory.

Critical invariants:

an order cannot be confirmed without a valid order state

inventory must not become negative due to concurrent purchases

payment retries must not create duplicate charges

Core Reasoning Summary

Definition: This architecture uses a relational transactional core for authoritative order, inventory, and payment state, with cache and search systems serving derived read workloads.

Why it exists: E-commerce combines high-volume reads with correctness-sensitive inventory, order, and payment operations. The architecture separates those concerns without allowing derived systems to become authoritative.

When to use: Use this pattern when inventory cannot become negative, orders require valid state transitions, and payment retries must not create duplicate charges.

When NOT to use: Do not require strong consistency for every catalog, search, recommendation, or cached read when the product semantics permit eventual consistency.

Primary architectural rule: The transactional database owns authoritative order, inventory, and payment state. Redis and OpenSearch improve derived workloads but do not authorize correctness-sensitive operations.

Advantages: Strong transactional integrity, clear ownership of critical state, and independent scaling of catalog/search workloads.

Disadvantages: Maintaining cache and search projections introduces invalidation, synchronization, retry, and operational complexity.

Review questions:

Which state is authoritative?

What prevents two buyers from taking the last unit?

What prevents a payment retry from charging twice?

Which reads may be stale?

What happens if payment succeeds but the application times out?

2. Scale

Illustrative assumptions:
20M users, 2M DAU, 10K average requests/sec, 40K peak during campaigns, millions of products, high read volume on catalog and high write contention on popular inventory.

3. Features & Roles

Customer, seller, administrator, warehouse/fulfillment system, payment provider.

4. Read vs Write

Catalog is extremely read-heavy. Cart and order paths mix reads/writes. Inventory writes are correctness-sensitive.

5. Concurrency

Two customers may purchase the last unit simultaneously. Inventory update must be conditional/transactional.

Inventory Concurrency Boundary

For inventory owned by the authoritative transactional database, a correctly designed conditional/transactional inventory update is the mechanism that prevents concurrent purchases from reducing authoritative inventory below the allowed quantity.

A cache, search engine, or application-level read check is not additionally required to establish that invariant.

A stale availability read may affect what the user sees, but the authoritative database write must make the final decision.

6. Entities

User, Product, ProductVariant, Category, Inventory, Warehouse, Cart, CartItem, Order, OrderItem, Payment, Shipment.

7. Relationships / Cardinality

Category 1 Product; Product 1 ProductVariant; Warehouse 1 Inventory; User 1 Order; Order 1 OrderItem; Order 1 PaymentAttempt; Order 1 Shipment as business rules require.

8. Schema

Relational core for users, products, inventory, orders, payments and shipments. Inventory can be keyed by (warehouse_id, product_variant_id). Order items should preserve purchase-time price rather than relying on the current product price.

9. SQL vs NoSQL + Trade-offs

MySQL/PostgreSQL fit orders, inventory and payments. MongoDB may fit some catalog aggregates, but introducing it only for flexible product attributes is optional. Search belongs in OpenSearch if relevance/fuzzy search is needed.

10. Important Queries

Product discovery, product detail, cart retrieval, order history, inventory decrement, order state lookup, shipment tracking.

11. Indexes

Examples:

products(category_id, status)

inventory(warehouse_id, product_variant_id) unique

orders(user_id, created_at)

order_items(order_id)
Search-specific fields belong in OpenSearch if used.

12. Cache

Cache product details, category metadata and hot catalog data. Do not use stale cache to authorize an inventory decrement.

Cache Boundary

Cache is an optimization for data whose staleness is acceptable. It is not required to establish inventory or order correctness.

A cache failure may reduce performance or availability of cached reads, but it must not determine whether an inventory decrement or other correctness-sensitive operation is authorized.

13. Replication

Catalog reads may use replicas. Critical order/inventory reads may require primary consistency.

14. Search

OpenSearch is justified when product search requires text relevance, fuzzy matching, autocomplete and faceting.

15. Partitioning

Large order/event history can eventually be partitioned by time or another lifecycle-aligned dimension.

16. Sharding

Do not shard initially. If required, tenant/region or another ownership key must be evaluated carefully. Inventory and order transactions that frequently cross shards are a warning sign.

17. Pagination

Cursor/keyset pagination suits product feeds and order history. Admin arbitrary-page views can use offset where scale permits.

18. Transactions

Order creation, order-item creation and inventory reservation should use carefully defined transaction boundaries. External payment calls are separate and require state reconciliation.

Transaction Boundary

A database transaction is sufficient to make the authoritative database operations inside its boundary atomic.

It is not a transaction boundary for an external payment provider. Do not assume that rolling back the database automatically rolls back an external payment.

External payment outcomes require separate state management and reconciliation.

19. Failure Handling

Payment timeout is ambiguous. Inventory decrement failure must not leave an apparently confirmed order. Search indexing can retry independently.

20. Idempotency

Order creation and payment initiation should use idempotency keys. Provider transaction references should be unique.

Payment Idempotency Boundary

An idempotency key or unique provider transaction reference prevents repeated processing of the same logical payment request within its defined scope.

It does not by itself guarantee that an external payment provider completed the payment, nor does it make the external provider part of the database transaction.

Payment state therefore still requires explicit state handling and reconciliation.

21. Consistency

Strong for inventory/order/payment state; eventual for search, recommendations and caches.

22. Final Architecture

MySQL/PostgreSQL transactional core + Redis cache + OpenSearch search + optional replicas.

23. Trade-offs

Relational core preserves correctness. Search/cache are deliberately derived systems. A single primary is preferred until measurements justify distribution.

Common Mistakes

Checking cached inventory and assuming the cached value authorizes the purchase.

Assuming an order transaction automatically includes an external payment provider.

Treating search results as authoritative product or order state.

Adding MongoDB solely because product attributes are flexible when the relational model already satisfies the requirement.

Introducing sharding before measuring the workload.

Treating payment retries and payment settlement as the same problem.