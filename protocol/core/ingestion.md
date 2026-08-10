---
status: draft
layer: lifecycle
version: v1
normative: true
---

# Ingestion

## Verification Pipeline Boundary

The Crinkl Protocol transforms a ReceiptUpload into a canonical Spend through a two-tier verification pipeline. The protocol defines **event schemas, state transitions, and normalization rules**—not OCR models, confidence thresholds, or extraction heuristics (those are implementation details).

Terms are defined in ../08-governance/glossary.md and used normatively throughout this specification.

## Ingestion Validation

Every incoming event MUST pass before any verification logic executes:

1. Recompute `eventHash` from RFC 8785 canonical serialization; reject on mismatch.
2. Verify `prevHash` chaining per `../protocol/core/spend-event.md#ordering-rules`; reject forks, and treat missing history as `IncompleteHistory` for verification purposes.
3. Verify Ed25519 `signature` against the spend-stream trust root for that `protocolVersion` (see `../00-purpose/threat-model.md#trust-roots`).
4. Validate schema for `eventName` and `protocolVersion` support.

**Rejection semantics:** If any check fails, the event is dropped and does not enter the stream. No state transition occurs.

## Authority model (normative)

Events are only meaningful if emitted by an authorized signer:

- **Spend-stream events** (including `RECEIPT_UPLOADED`, verification events, reward issuance events, and `FRAUD_FLAGGED`) MUST be signed by the spend-stream trust root(s) for the event’s `protocolVersion` (operator/verifier authority in v1).
- **System-stream events** MUST be signed by a registered authority for the `chainId` at the event-effective time (Authority Registry; see `../protocol/applications/economics/settlement-bindings.md`).

Wallet addresses (`wallet: WalletRef`) are carried as data to scope spends and (optionally) recipient binding, but wallets are not assumed to be event signers in protocol v1.

This wallet scope is internal to the spend-stream envelope. Hard verification may produce a portable Spend Attestation Token from the wallet-scoped stream, but that token SHOULD omit `wallet` for external verification unless recipient binding is explicitly required.

## Idempotency

**Event-level idempotency (normative):** Idempotency is defined by `eventId` (see `../protocol/core/spend-event.md#eventid-derivation-normative`).

- Replaying the same semantic event produces the same `eventId` and MUST be treated as a no-op if all fields match.
- If the same `eventId` is observed with mismatched content, the event MUST be rejected with `DuplicateEventConflict`.

**Receipt-level deduplication (non-normative):** Implementations MAY deduplicate uploads (e.g., by image hash) for operational reasons, but deduplication strategy is not a protocol requirement and MUST NOT change the canonical event ordering or verification semantics.
