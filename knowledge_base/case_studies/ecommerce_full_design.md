# Case Study: E-commerce Platform — Full 23-Section Design

Use this example to teach order, inventory, payment, catalog, search, and consistency reasoning.

## 1. Requirements / Scope
Customers browse products, search/filter the catalog, manage carts, place orders, pay, and track orders. Sellers/admins manage products and inventory.

Critical invariants:
- an order cannot be confirmed without a valid order state
- inventory must not become negative due to concurrent purchases
- payment retries must not create duplicate charges

## 2. Scale
Illustrative assumptions:
20M users, 2M DAU, 10K average requests/sec, 40K peak during campaigns, millions of products, high read volume on catalog and high write contention on popular inventory.

## 3. Features & Roles
Customer, seller, administrator, warehouse/fulfillment system, payment provider.

## 4. Read vs Write
Catalog is extremely read-heavy. Cart and order paths mix reads/writes. Inventory writes are correctness-sensitive.

## 5. Concurrency
Two customers may purchase the last unit simultaneously. Inventory update must be conditional/transactional.

## 6. Entities
User, Product, ProductVariant, Category, Inventory, Warehouse, Cart, CartItem, Order, OrderItem, Payment, Shipment.

## 7. Relationships / Cardinality
Category 1:N Product; Product 1:N ProductVariant; Warehouse 1:N Inventory; User 1:N Order; Order 1:N OrderItem; Order 1:N PaymentAttempt; Order 1:N Shipment as business rules require.

## 8. Schema
Relational core for users, products, inventory, orders, payments and shipments. Inventory can be keyed by `(warehouse_id, product_variant_id)`. Order items should preserve purchase-time price rather than relying on the current product price.

## 9. SQL vs NoSQL + Trade-offs
MySQL/PostgreSQL fit orders, inventory and payments. MongoDB may fit some catalog aggregates, but introducing it only for flexible product attributes is optional. Search belongs in OpenSearch if relevance/fuzzy search is needed.

## 10. Important Queries
Product discovery, product detail, cart retrieval, order history, inventory decrement, order state lookup, shipment tracking.

## 11. Indexes
Examples:
- products(category_id, status)
- inventory(warehouse_id, product_variant_id) unique
- orders(user_id, created_at)
- order_items(order_id)
Search-specific fields belong in OpenSearch if used.

## 12. Cache
Cache product details, category metadata and hot catalog data. Do not use stale cache to authorize an inventory decrement.

## 13. Replication
Catalog reads may use replicas. Critical order/inventory reads may require primary consistency.

## 14. Search
OpenSearch is justified when product search requires text relevance, fuzzy matching, autocomplete and faceting.

## 15. Partitioning
Large order/event history can eventually be partitioned by time or another lifecycle-aligned dimension.

## 16. Sharding
Do not shard initially. If required, tenant/region or another ownership key must be evaluated carefully. Inventory and order transactions that frequently cross shards are a warning sign.

## 17. Pagination
Cursor/keyset pagination suits product feeds and order history. Admin arbitrary-page views can use offset where scale permits.

## 18. Transactions
Order creation, order-item creation and inventory reservation should use carefully defined transaction boundaries. External payment calls are separate and require state reconciliation.

## 19. Failure Handling
Payment timeout is ambiguous. Inventory decrement failure must not leave an apparently confirmed order. Search indexing can retry independently.

## 20. Idempotency
Order creation and payment initiation should use idempotency keys. Provider transaction references should be unique.

## 21. Consistency
Strong for inventory/order/payment state; eventual for search, recommendations and caches.

## 22. Final Architecture
MySQL/PostgreSQL transactional core + Redis cache + OpenSearch search + optional replicas.

## 23. Trade-offs
Relational core preserves correctness. Search/cache are deliberately derived systems. A single primary is preferred until measurements justify distribution.
