# Events

Crinkl has two event streams:

Terms are defined in GLOSSARY.md and used normatively throughout this specification.

- **Spend-stream events**: per-`spendId`, represent state transitions in the Verification and Reward state machines.
- **System-stream events**: per-`chainId`, represent protocol-level commitments and governance transitions (Commitment Layer + Authority Registry).

## Event Envelopes

Both envelopes use the same Integrity Envelope (`eventHash`, `prevHash`, `signature`). See DATA_STRUCTURES.md for cryptographic specifications.

### eventId derivation (normative)

`eventId` is a deterministic identifier used for idempotency and duplicate detection. For protocol v1, producers MUST compute:

- Spend-stream:  
  `eventId = "sha256:" + SHA-256(RFC8785_canonicalize({spendId, eventName, payload, protocolVersion}))`
- System-stream:  
  `eventId = "sha256:" + SHA-256(RFC8785_canonicalize({chainId, eventName, payload, protocolVersion}))`

Verifiers MUST treat an event as a replay/no-op if `eventId` already exists **and** all envelope fields match (including `eventHash`). If `eventId` exists with mismatched fields, verifiers MUST reject with `DuplicateEventConflict`.

### Spend-Stream Event Envelope

Spend-stream events are ordered per `spendId`.

```text
SpendStreamEvent {
    eventId: Identifier,
    eventName: EventName,
    spendId: Identifier,
    wallet: WalletRef,
    payload: EventPayload,
    timestamp: Timestamp,
    protocolVersion: Version,
    eventHash: Hash,
    prevHash: Hash | null,
    signature: Signature
}
```

**Required fields:** All fields above are REQUIRED.

**Signer (normative):** spend-stream events MUST be signed by a spend-stream trust root authorized for the event’s `protocolVersion` (operator/verifier authority in v1). The `wallet` field is data (scoping) and MUST NOT be interpreted as the event signer unless a future protocol version explicitly defines wallet-signing.

**eventId uniqueness:** `eventId` MUST be deterministically derived from `(spendId, eventName, payload, protocolVersion)`. Replaying an event with an existing `eventId` MUST be treated as a no-op if all fields match; mismatched fields with the same `eventId` MUST be rejected with `DuplicateEventConflict`.

### System-Stream Event Envelope

System-stream events are ordered per `chainId` and MUST be signed by a registered authority.

```text
SystemStreamEvent {
    eventId: Identifier,
    eventName: EventName,
    chainId: String,
    signedBy: Identifier,
    payload: EventPayload,
    timestamp: Timestamp,
    protocolVersion: Version,
    eventHash: Hash,
    prevHash: Hash | null,
    signature: Signature
}
```

**Required fields:** All fields above are REQUIRED.

**Authority verification:** `signedBy` MUST be valid for `chainId` at `timestamp` (or the on-chain `committedAt` / `registeredAt` / `revokedAt` time, depending on the event). For events that include an on-chain `committedAt` timestamp, authority validity MUST be evaluated at `committedAt`, not envelope `timestamp`. See COMMITMENT_LAYER.md.

**Hash computation:** `eventHash` = SHA-256 of RFC 8785 canonical JSON excluding `eventHash` and `signature` fields.

## Event Types

### Spend-Stream Events

#### Attestation Ledger Events

| Event | Payload |
|-------|---------|
| RECEIPT_UPLOADED | `{ uploadId, imageDataRef, metadata? }` |
| SPEND_SOFT_VERIFIED | `{ softVerificationStatus, softExtractedFields, riskFlags }` |
| SPEND_REVIEW_REQUESTED | `{ reason, requestedAt, source }` |
| SPEND_HARD_VERIFIED | `{ storeId, totalCents, currency, timestamp, geoRegion, cbsaCode?, verificationVersion }` |
| SPEND_INVALIDATED | `{ reason, riskFlags }` |
| SPEND_CORRECTED | `{ correctedFields, verificationVersion }` |
| FRAUD_FLAGGED | `{ fraudType, evidenceRef? }` |

*FRAUD_FLAGGED is observational and MUST NOT participate in attestation state transitions.*

**Hard verification duplicate rule (normative):** If duplicate suspicion is present (e.g., `riskFlags` includes `potential_duplicate`), producers MUST NOT emit `SPEND_HARD_VERIFIED`. They MUST emit `SPEND_INVALIDATED` (e.g., `reason = "POTENTIAL_DUPLICATE"`) or `SPEND_CORRECTED` if explicitly linking to a canonical prior spend.

**Appeals after hard rejection (not yet defined):** The spend FSM treats `REJECTED`/`INVALIDATED` as sealed. The protocol currently defines no event to re-open a rejected spend for another review. Introducing an appeal would require a new spend-stream event + state transition (e.g., `SPEND_APPEAL_REQUESTED`) with clear ordering/prevHash rules. Until such an event is added, clients MUST NOT promise a “request review” action after hard rejection, though they MAY append informational tokens to the spend-stream history.

#### Reward Ledger Events

| Event | Payload |
|-------|---------|
| REWARD_PROVISIONAL_ISSUED | `{ rewardId?, policyVersion, deltaPoints, deltaBTCsats }` |
| REWARD_FINAL_ISSUED | `{ rewardId?, policyVersion, deltaPoints, deltaBTCsats }` |

### System-Stream Events

#### Commitment Layer Events

| Event | Payload |
|-------|---------|
| REWARD_BATCH_COMMITTED | `{ batchId, root, leafCount, totalPoints, schemaVersion, txRef, committedAt }` |
| REWARD_BATCH_BACKING_ATTESTED | `{ batchId, backingAsset, backingAmount, backingVault, backingTxRef, backedAt }` |
| REWARD_BATCH_CORRECTION | `{ correctionBatchId, targetBatchId, reason, adjustments, root, txRef, committedAt }` |
| CUMULATIVE_SNAPSHOT_COMMITTED | `{ snapshotId, snapshotRoot, leafCount, throughBatchId, throughEventHash, txRef, committedAt }` |
| AUTHORITY_REGISTERED | `{ authorityId, publicKey, validFrom, predecessorId?, txRef, registeredAt }` |
| AUTHORITY_REVOKED | `{ authorityId, validUntil, revokedBy, reason, txRef, revokedAt }` |

`REWARD_BATCH_COMMITTED.payload.schemaVersion` identifies the commitment leaf schema (see COMMITMENT_LAYER.md). Schema v2 enables compact spend↔reward linkage proofs.

`REWARD_BATCH_BACKING_ATTESTED` is an operator attestation about economic backing for a reward batch. It MUST NOT be interpreted as independent verification of spend attestation; it only provides a verifiable reference (`backingTxRef`) to an external asset movement intended to back reward liabilities for `batchId`.

See COMMITMENT_LAYER.md for full specification.

## FRAUD_FLAGGED Event

Signals application-layer fraud determination for a spend.

**Reward immutability:** The protocol does **not** adjust or claw back previously issued rewards. `FRAUD_FLAGGED` MUST NOT cause a Reward Ledger change.

```text
FRAUD_FLAGGED {
    fraudType: 'duplicate_submission' | 'synthetic_receipt' | 'collusion' | 'other',
    evidenceRef: String?           // Optional reference to fraud investigation evidence
}
```

FRAUD_FLAGGED does NOT delete or modify prior Reward Ledger entries.

## Ordering Rules

### Spend-Stream Ordering (per spendId)

Canonical order is defined **only** by the `prevHash` chain. Timestamps MUST NOT be used for ordering.

1. Events for a `spendId` form a single append-only stream linked by `prevHash` from a unique bootstrap event where `prevHash = null`.
2. For any non-bootstrap event, `prevHash` MUST equal the `eventHash` of exactly one prior event for the same `spendId`.
3. **Fork rule:** if two distinct events claim the same `prevHash` for the same `spendId`, the spend-stream history is forked and verifiers MUST treat the stream as invalid/ambiguous (`OrderingViolation`).
4. **Gap rule:** if an event references a `prevHash` that is unknown to the verifier, the verifier MUST treat history as incomplete (`IncompleteHistory`) and MUST NOT assume missing links.
5. Replaying the canonical chain from bootstrap to head MUST produce identical final state.

**Out-of-order arrival:** storage layers MAY accept events out of order, but verifiers MUST reconstruct canonical order via the `prevHash` chain. If the chain cannot be reconstructed (fork or gap), verification MUST fail or return indeterminate (implementation-defined, but MUST NOT accept as valid).

### Cross-FSM Ordering Constraints (normative)

- `REWARD_PROVISIONAL_ISSUED` MUST NOT occur before `SPEND_SOFT_VERIFIED`.
- `REWARD_FINAL_ISSUED` MUST NOT occur before `SPEND_HARD_VERIFIED`.
- `REWARD_*_ISSUED` events MUST be appended to the current spend-stream head at issuance time: their `prevHash` MUST equal the then-current spend-stream head `eventHash` for the `spendId`. This binds reward issuance to a specific spend-stream state without adding extra payload fields.

**Cross-stream coupling boundary (normative):**
- Spend-stream validation MUST NOT depend on system-stream availability or commitment-layer state.
- System-stream artifacts (commitments, snapshots) MAY reference spend-stream or reward issuance events by hash (e.g., `rewardEventHash`), but that linkage is additive and MUST NOT change spend truth semantics.

### Version monotonicity (normative intent)

Within a single spend-stream (`spendId`) or system-stream (`chainId`), `protocolVersion` SHOULD be non-decreasing over time. Producers SHOULD NOT emit version downgrades, and verifiers SHOULD reject downgrades as `VersionMismatch` to avoid ambiguous semantics.

### System-Stream Ordering (per chainId)

`chainId` is a deployment-defined identifier for a single system stream (non-empty string). It SHOULD be stable and unambiguous across deployments (recommended formats include CAIP-2 style identifiers such as `eip155:1` or `solana:mainnet-beta`).

1. Events for a `chainId` form a single append-only stream linked by `prevHash` from a unique bootstrap event where `prevHash = null`.
2. `prevHash` MUST equal the prior canonical system event’s `eventHash` for the same `chainId`. Fork and gap rules mirror the spend-stream rules above.
3. Replaying all canonical system events for a `chainId` MUST produce identical final system state (authority registry + commitment history).

**On-chain anchoring and reorgs (normative intent):**
- Some system events reference an on-chain `txRef` and an effective time such as `committedAt`/`registeredAt`/`revokedAt`.
- For deployments where system-stream events are derived from on-chain logs, chain bindings MUST define a deterministic on-chain ordering key (e.g., `(blockHeight, txIndex, logIndex)` on EVM-like chains or `(slot, txIndex, instructionIndex)` on Solana-like chains). Producers MUST construct the system-stream `prevHash` chain in that deterministic order.
- Verifiers SHOULD apply chain-specific finality thresholds before treating those events as stable; finality rules are part of chain bindings (see `COMMITMENT_LAYER.md#chain-bindings`).

## Error Types

Error codes are normative and intended to be stable for client integrations. Producers/servers MAY include a human-readable `message`, but clients SHOULD branch on `code`.

| Code | Retryable | Meaning |
|---|:---:|---|
| HashMismatch | no | Recomputed `eventHash` ≠ supplied value |
| SignatureInvalid | no | Signature missing or fails verification |
| UnknownAuthority | no | `signedBy` unknown/invalid for `chainId` at event-effective time |
| UnauthorizedSigner | no | Signer key is not authorized for this stream/domain |
| InvalidTransition | no | State machine violation |
| OrderingViolation | no | `prevHash` mismatch or stream fork detected |
| IncompleteHistory | yes | Missing prior events referenced by `prevHash` (cannot decide yet) |
| MalformedPayload | no | Schema validation failure |
| VersionMismatch | no | Unsupported `protocolVersion` / `schemaVersion` |
| UnknownEventName | no | Unknown `eventName` |
| DuplicateEventConflict | no | `eventId` exists with different content |

**Versioning:** adding new codes MUST be additive; clients MUST treat unknown codes as non-retryable unless explicitly documented otherwise.

## Offline verifier minimum storage (normative)

To support offline verification/replay, an implementation MUST be able to retain (or export) at minimum:
- the full event envelope (including `eventHash`, `prevHash`, `signature`, `protocolVersion`, and the stream key `spendId`/`chainId`),
- the typed `payload` needed for state machine replay, and
- for system events that depend on on-chain effective time, the referenced effective timestamp (`committedAt`/`registeredAt`/`revokedAt`) and `txRef` when present.
