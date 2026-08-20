Idempotency — Deep Explanation

Core Reasoning Summary

Definition: Idempotency means repeating the same logical operation does not create additional unintended effects.

Why it exists: Requests can time out after the server has committed, so a client retry cannot always distinguish failure from a successful operation with a lost response.

When to use: Use idempotency for retryable operations whose duplicate execution could create an unacceptable side effect, especially payments, bookings, orders, and other externally visible state changes.

When NOT to use: Do not add an idempotency key to every operation automatically. It is unnecessary when duplicate execution is already harmless or when the operation cannot meaningfully be retried.

Primary rule: Idempotency prevents duplicate logical processing; it does not provide transaction atomicity, concurrency control, or external-service consistency.

Advantages: Makes retries safe for appropriately designed operations and resolves timeout ambiguity.

Disadvantages: Requires key storage, request/result handling, retention policy, scope definition, and careful concurrency behavior.

Review questions:

What is one logical operation?

What is the idempotency-key scope?

What happens with the same key and same request?

What happens with the same key and different request?

How long is the key retained?

Does the operation also require a transaction or concurrency mechanism?

What happens if the external provider succeeded but the local response was lost?

An idempotent operation can be repeated without producing additional unintended effects.

Why retries create problems

HTTP requests can time out even after the server commits the transaction. A client cannot always distinguish "operation failed" from "operation succeeded but response was lost."

Example

A user clicks Pay.

Payment request reaches server.

Payment succeeds.

Response is lost.

Client retries.

Without idempotency, a second charge may occur.

Idempotency key

The client supplies a unique key for one logical operation.
Example: Idempotency-Key: 8f2...

The server stores enough information to recognize the request and replay the previous result.

Key-Scope Boundary

An idempotency key is meaningful only within its defined scope, such as a client, user, endpoint, or operation type.

The key must identify one logical operation within that scope. Reusing the same key across unrelated operations can incorrectly collapse distinct requests.

Typical storage

key

user/client identity

request hash

status

result/reference

created_at

expires_at

Same key + same request

Return the original result.

Same key + different request

Reject the request because one idempotency key should identify one logical operation.

Request-Identity Boundary

Comparing the key alone is not sufficient when the same key could be reused with different request payloads.

The system should bind the key to the relevant operation identity and request semantics so that a retry of the same logical request can replay the prior result while a different request using the same key is rejected.

State handling

Possible states:
NEW -> PROCESSING -> SUCCESS
-> FAILED
The exact retry semantics must be defined.

Idempotency and transactions

They solve different problems.

Transaction: protects atomic database changes.
Idempotency: protects against duplicate logical requests.

Booking/payment flows may require both.

Separation Boundary

Idempotency is sufficient to prevent duplicate logical processing when the idempotency record and operation are designed and persisted correctly.

It is not sufficient to make multiple database changes atomic.

Likewise, a transaction does not automatically make two repeated client requests the same logical operation.

When both duplicate retries and multi-step database correctness matter, both mechanisms may be required.

Database enforcement

A unique constraint on the idempotency key is useful, but it must be combined with a correct transaction boundary and result persistence.

Unique-Constraint Boundary

A unique constraint prevents two stored idempotency records from using the same key within the constraint's defined scope.

It does not by itself guarantee that the business operation was executed exactly once, that the result was persisted, or that a concurrent retry will correctly replay the original result.

The uniqueness constraint protects key storage; the transaction and result-persistence design protects the logical operation.

Expiration

Idempotency records do not necessarily need to live forever. The retention period should cover the realistic retry window.

Retention Boundary

Expiration is safe only when the retention period covers the realistic window in which the same logical operation can be retried.

If a key expires while a client may still retry the original operation, the system may process the retry as a new operation and lose the intended idempotency guarantee.

Review question

What happens if the client retries after the server committed but before receiving the response?

Common Review Mistakes

Treating idempotency as a substitute for transactions.

Treating idempotency as a substitute for concurrency control.

Assuming a unique idempotency-key constraint alone guarantees exactly-once business execution.

Failing to define key scope.

Accepting the same key with materially different request data.

Expiring keys before the realistic retry window ends.

Assuming idempotency automatically makes an external provider participate in a local database transaction.