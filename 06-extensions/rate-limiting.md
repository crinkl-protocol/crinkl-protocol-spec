---
status: experimental
layer: extension
version: v1
normative: true
---

# Rate Limiting

Rate limiting is an **operational** concern. It is **out-of-protocol**: it MUST NOT affect event validity, token validity, hash/signature verification, or any protocol truth/economic semantics.

This document is **non-normative guidance** for implementers and operators. Offline verifiers MUST ignore rate-limiting policy and MUST NOT treat rate-limit outcomes as protocol signals.

## Limits by Operation

> Non-normative examples; values are deployment-specific.

| Operation | Limit | Window | Scope |
|-----------|-------|--------|-------|
| Receipt upload | 10 | 1 minute | Per wallet |
| Receipt upload | 100 | 1 day | Per wallet |
| Batch upload | 3 | 1 minute | Per wallet |
| Batch size | 50 items | Per request | Per batch |
| Event query | 100 | 1 minute | Per wallet |
| Trust root fetch | 10 | 1 minute | Per IP |

## Batch Limits

> Non-normative examples; values are deployment-specific.

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Max items per batch | 50 | Prevent memory exhaustion |
| Max image size | 10 MB | Storage efficiency |
| Max batch payload | 500 MB | Network/processing limits |
| Batch timeout | 5 minutes | Processing SLA |

## Rate Limit Headers

Responses include rate limit state:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1705312800
```

## Exceeded Rate Limit Response

```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Upload limit exceeded",
  "retryAfter": 47,
  "limit": 10,
  "window": "1m"
}
```

HTTP status: `429 Too Many Requests`

## Burst Allowance

Short bursts permitted up to 2x limit within 10-second window, after which standard limits apply.

Example: 10/minute limit allows burst of 20 in 10 seconds, then blocked until minute resets.

## Wallet Reputation Multipliers

Wallets with verified history may receive higher limits:

| Reputation Level | Multiplier | Criteria |
|------------------|------------|----------|
| New | 1.0x | < 30 days, < 10 verified receipts |
| Established | 1.5x | ≥ 30 days, ≥ 10 verified, 0 fraud flags |
| Trusted | 2.0x | ≥ 90 days, ≥ 50 verified, 0 fraud flags |

## Global Circuit Breakers

System-wide protection when anomalies detected:

| Trigger | Action | Duration |
|---------|--------|----------|
| Error rate > 50% | Reject new uploads | 5 minutes |
| Queue depth > 10,000 | Reject new uploads | Until queue < 5,000 |
| Fraud spike > 10% | Manual review all | Until operator clears |

## Implementation Notes

- Rate limits are local policy; implementers MAY enforce.
- Limits apply to signed requests (wallet-scoped) or IP (unauthenticated endpoints).
- Rate limits MUST be enforced without creating new protocol-visible identifiers (avoid stable, public “wallet reputation” identifiers).
- Any “clock skew tolerance” is purely API policy; protocol hashing/signatures use canonical timestamps only when included in signed artifacts.
