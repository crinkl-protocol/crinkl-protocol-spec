---
status: draft
layer: lifecycle
version: v1
normative: true
---

# Correction and Revocation

Crinkl v1 expresses correction and rejection through append-only spend-stream events. The requested lifecycle term `revoked` maps to later invalidating/correction semantics only when a future protocol version defines a revocation event; v1 does not silently invent one.

## Correction and Invalidation

- **Correction:** Replaces prior Spend interpretation via a new `SPEND_CORRECTED` event, preserving the same `spendId` and maintaining ledger append-only semantics (original events remain; corrections add new events).
- **Invalidation:** No valid Spend can be derived at the head. Does not alter Reward Ledger entries.

Both transitions append to the Attestation Ledger; they do not modify or delete prior entries.

**Fraud flagging (normative):** `FRAUD_FLAGGED` is a spend-stream event that is observational and MUST NOT participate in attestation state transitions (see `../01-core/spend-event.md#fraud_flagged-event`).

**Terminality (normative):** `SPEND_INVALIDATED` is terminal for spend truth for a given `spendId` (no reinstatement without a new protocol concept/version). `SPEND_CORRECTED` supersedes by moving the head; it is not a retroactive edit.
