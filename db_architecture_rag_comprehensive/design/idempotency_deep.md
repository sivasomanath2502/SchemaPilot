# Idempotency — Deep Explanation

## Definition
An idempotent operation can be repeated without producing additional unintended effects.

## Why retries create problems
HTTP requests can time out even after the server commits the transaction. A client cannot always distinguish "operation failed" from "operation succeeded but response was lost."

## Example
A user clicks Pay.
1. Payment request reaches server.
2. Payment succeeds.
3. Response is lost.
4. Client retries.
5. Without idempotency, a second charge may occur.

## Idempotency key
The client supplies a unique key for one logical operation.
Example: `Idempotency-Key: 8f2...`

The server stores enough information to recognize the request and replay the previous result.

## Typical storage
- key
- user/client identity
- request hash
- status
- result/reference
- created_at
- expires_at

## Same key + same request
Return the original result.

## Same key + different request
Reject the request because one idempotency key should identify one logical operation.

## State handling
Possible states:
NEW -> PROCESSING -> SUCCESS
                       -> FAILED
The exact retry semantics must be defined.

## Idempotency and transactions
They solve different problems.

Transaction: protects atomic database changes.
Idempotency: protects against duplicate logical requests.

Booking/payment flows may require both.

## Database enforcement
A unique constraint on the idempotency key is useful, but it must be combined with a correct transaction boundary and result persistence.

## Expiration
Idempotency records do not necessarily need to live forever. The retention period should cover the realistic retry window.

## Review question
What happens if the client retries after the server committed but before receiving the response?
