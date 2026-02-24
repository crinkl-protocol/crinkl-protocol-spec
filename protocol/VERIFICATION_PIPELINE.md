# Verification Pipeline

The Crinkl Protocol transforms a ReceiptUpload into a canonical Spend through a two-tier verification pipeline. The protocol defines **event schemas, state transitions, and normalization rules**—not OCR models, confidence thresholds, or extraction heuristics (those are implementation details).

Terms are defined in GLOSSARY.md and used normatively throughout this specification.

## Ingestion Validation

Every incoming event MUST pass before any verification logic executes:

1. Recompute `eventHash` from RFC 8785 canonical serialization; reject on mismatch.
2. Verify `prevHash` chaining per `EVENTS.md#ordering-rules`; reject forks, and treat missing history as `IncompleteHistory` for verification purposes.
3. Verify Ed25519 `signature` against the spend-stream trust root for that `protocolVersion` (see `SECURITY_MODEL.md#trust-roots`).
4. Validate schema for `eventName` and `protocolVersion` support.

**Rejection semantics:** If any check fails, the event is dropped and does not enter the stream. No state transition occurs.

## Authority model (normative)

Events are only meaningful if emitted by an authorized signer:

- **Spend-stream events** (including `RECEIPT_UPLOADED`, verification events, reward issuance events, and `FRAUD_FLAGGED`) MUST be signed by the spend-stream trust root(s) for the event’s `protocolVersion` (operator/verifier authority in v1).
- **System-stream events** MUST be signed by a registered authority for the `chainId` at the event-effective time (Authority Registry; see `COMMITMENT_LAYER.md`).

Wallet addresses (`wallet: WalletRef`) are carried as data to scope spends and (optionally) recipient binding, but wallets are not assumed to be event signers in protocol v1.

## Soft Verification

Low-latency preliminary assessment producing provisional values for user feedback and optional provisional rewards. Does not produce canonical Spend records.

**Input:** ReceiptUpload  
**Output:** SoftSpend

| Field | Description |
|-------|-------------|
| spendId | Stable identifier (same across Soft → Hard transitions) |
| softVerificationStatus | `SOFT_VERIFIED` \| `REJECTED` \| `PENDING` (see `DATA_STRUCTURES.md`) |
| softExtractedFields | Approximate values (store, total, timestamp) |
| riskFlags | Optional diagnostic indicators |

**Invariant:** SoftSpend values MAY be approximate but MUST NOT be contradictory. If Hard Verification produces materially different values, the delta MUST be explainable as an extraction refinement, not arbitrary reassignment.

*A SoftSpend field is non-contradictory if the Hard-verified value can be derived via refinement (e.g., precision increase, store disambiguation) rather than categorical reversal (e.g., different merchant class, different currency).*

**Duplicate suspicion (normative):** If duplicate suspicion exists at Hard Verification time (e.g., `riskFlags` contains `potential_duplicate`), the verifier MUST NOT emit `SPEND_HARD_VERIFIED` or a spend token. The verifier MUST emit either:
- `SPEND_INVALIDATED` with `reason` indicating duplicate suspicion (e.g., `POTENTIAL_DUPLICATE`), or
- `SPEND_CORRECTED` if the spend is being explicitly linked to a canonical prior spend (duplicate resolution).

Implementations MAY surface `potential_duplicate` earlier in `SPEND_SOFT_VERIFIED` for UX and reward gating, but the hard-verification outcome MUST reflect the duplicate finding (invalidation/correction, not acceptance).

## Hard Verification

Comprehensive evaluation producing the canonical Spend.

**Input:** ReceiptUpload, optional SoftSpend (present if Soft Verification was performed first; absent for direct Hard Verification)  
**Output:** Spend with `verificationStatus` = `HARD_VERIFIED`, `INVALIDATED`, or `CORRECTED`

*If SoftSpend is present, Hard Verification MAY use it as a hint but MUST be able to derive canonical Spend from ReceiptUpload alone.*

Hard verification produces the canonical Spend record, which can be packaged as a Spend Attestation Token for downstream verification (see TOKENS.md).

**Requirements:**
- Derive all required Spend fields (storeId, totalCents, currency, timestamp)
- Record `verificationVersion` used
- Emit Attestation Ledger entry for the state transition

## Normalization

Converts extracted receipt content to canonical form. Rules MUST be deterministic for a given `verificationVersion` to ensure reproducible verification and cross-operator compatibility.

| Field | Normalization |
|-------|---------------|
| storeId | See DATA_STRUCTURES.md storeId rules |
| totalCents | Base-10 integer string cents, non-negative |
| currency | ISO 4217 uppercase |
| timestamp | ISO 8601 UTC |
| geoRegion (optional) | ISO 3166-2 subdivision code or ISO 3166-1 alpha-2 country code |
| cbsaCode (optional) | CBSA metro area code or non-metro fallback — derived from store location, not receipt text (see `DATA_STRUCTURES.md#cbsacode`) |

**Constraint:** Transformations MUST NOT introduce data not present in the submission or derivable from explicit rules (e.g., currency inference from storeId). Synthetic data (e.g., randomly generated timestamps) is forbidden.

**LLM determinism constraint (normative):** If an implementation uses an LLM for normalization, it MUST constrain the model to a closed-choice output space (or an equivalent deterministic mapping) and MUST ensure the resulting canonical fields are reproducible given the same inputs and `verificationVersion`.

## Correction and Invalidation

- **Correction:** Replaces prior Spend interpretation via a new `SPEND_CORRECTED` event, preserving the same `spendId` and maintaining ledger append-only semantics (original events remain; corrections add new events).
- **Invalidation:** No valid Spend can be derived at the head. Does not alter Reward Ledger entries.

Both transitions append to the Attestation Ledger; they do not modify or delete prior entries.

**Fraud flagging (normative):** `FRAUD_FLAGGED` is a spend-stream event that is observational and MUST NOT participate in attestation state transitions (see `EVENTS.md#fraud_flagged-event`).

**Terminality (normative):** `SPEND_INVALIDATED` is terminal for spend truth for a given `spendId` (no reinstatement without a new protocol concept/version). `SPEND_CORRECTED` supersedes by moving the head; it is not a retroactive edit.

## Verification Versioning

Each verification pass MUST record a `verificationVersion` identifier that binds the Spend to:
- Normalization rules in effect at verification time
- Store resolution logic
- Currency inference heuristics (if any)
 - If LLMs are used: the exact model identifier, prompt hash, and choice-set (or output schema) hash used to produce canonical fields

When verification rules change, the protocol increments `verificationVersion`. Old Spends are not re-verified automatically; operators MAY emit `SPEND_CORRECTED` events to apply new rules, preserving original events in the ledger.

**Registry guidance (non-normative):** deployments SHOULD publish a verification registry that maps `verificationVersion` to concrete artifacts (prompt hash, model version, choice-set hash) so auditors can reproduce canonical outputs deterministically.

### protocolVersion vs verificationVersion (normative)

- `protocolVersion` is carried on every event envelope and gates event schema and verification semantics.
- `verificationVersion` is carried in hard verification/correction payloads and gates normalization/resolution semantics for canonical Spend fields.

**Version skew handling (normative):**
- Verifiers MUST reject events whose `protocolVersion` they do not support (`VersionMismatch`).
- Within a single spend-stream (`spendId`) or system-stream (`chainId`), `protocolVersion` SHOULD be non-decreasing over time; downgrades SHOULD be rejected as `VersionMismatch` to avoid ambiguous semantics.

See PROTOCOL_EVOLUTION.md for upgrade semantics.

## Idempotency

**Event-level idempotency (normative):** Idempotency is defined by `eventId` (see `EVENTS.md#eventid-derivation-normative`).

- Replaying the same semantic event produces the same `eventId` and MUST be treated as a no-op if all fields match.
- If the same `eventId` is observed with mismatched content, the event MUST be rejected with `DuplicateEventConflict`.

**Receipt-level deduplication (non-normative):** Implementations MAY deduplicate uploads (e.g., by image hash) for operational reasons, but deduplication strategy is not a protocol requirement and MUST NOT change the canonical event ordering or verification semantics.
