---
status: draft
layer: reward-settlement
version: v1
normative: true
---

# Reward Commitment

Reward Commitment is downstream of valid spend proof. It records economic consequence and recipient-scoped inclusion; it does not define spend truth.

## Reward Commitment Token

### Claim

The claim is that a recipient has a **leaf included under a committed batch root**:
- the provided `leaf` (recipient-scoped aggregate for `batch.batchId`) is included under `batch.root` via `proof`, and
- `batch.root` is authenticated by the included system-stream commitment history (`systemEvents` + Authority Registry rules).

#### Explicit non-claims (normative)

A Reward Commitment Token:
- does NOT prove current wallet balance (it proves inclusion in a specific batch, not cumulative balance),
- does NOT prove funds custody, redemption availability, solvency, reserves, or “already paid out”,
- does NOT claw back or negate previously issued rewards when spends are later invalidated or corrected,
- does NOT prove spend truth beyond the protocol semantics that gated issuance.

Reward commitments are batch-level, recipient-scoped, and derive from Reward Ledger events (REWARD_*_ISSUED) plus a system-stream commitment event (REWARD_BATCH_COMMITTED and related).

## Campaign Epoch Binding

For campaign flows, a Reward Commitment is produced only after a valid ProofOfMatch for exactly one CampaignEpoch. The Reward Commitment or campaign settlement leaf MUST bind directly or by hash reference to the selected `campaignId`, `epochId`, `ruleSetHash`, approval artifact, and payout terms.

A CampaignAmendment MUST NOT lower, remove, or invalidate rewards already earned under an earlier epoch. Earned rewards are immutable once committed. Later epochs may change reward rules only prospectively through a new `rewardRuleHash`; they do not alter prior Reward Commitment validity.

**Recipient scoping:** Reward Commitment Tokens require recipient binding for verification of economic issuance. The `recipientId` field is REQUIRED. The representation of `recipientId` is schema-defined:
- `WalletRef` (transparent, schema v1a/v2a)
- `Commitment` (blinded, schema v1b/v2b)

See settlement-bindings.md for schema definitions and recipient blinding.

**Linkability note (normative intent):**
- If `recipientId` is a `WalletRef` (transparent schemas), third parties can link the same recipient across batches by wallet address.
- If `recipientId` is a blinded `Commitment` (blinded schemas), the identifier is intentionally per-batch and does not create a stable public identifier across batches; recipients may selectively disclose underlying wallet/blinder to prove inclusion (see `settlement-bindings.md#recipient-blinding`).

### Portable shape (normative)

```text
RewardCommitmentTokenV1 {
  tokenType: "REWARD_COMMITMENT",
  schemaVersion: 1,
  chainId: String,
  economicTier: "COMMITTED" | "COMMITTED_BACKED",
  commitmentEvent: SystemStreamEvent, // eventName = REWARD_BATCH_COMMITTED
  backingEvent?: SystemStreamEvent,   // eventName = REWARD_BATCH_BACKING_ATTESTED (required when economicTier = COMMITTED_BACKED)
  systemEvents: [SystemStreamEvent],  // ordered, prevHash-linked; MUST include commitmentEvent and authority events needed to validate its signer at effective time
  batch: { batchId: Identifier, root: Hash, schemaVersion: String, txRef: String, committedAt: Timestamp }, // schemaVersion: "1a"|"1b"|"2a"|"2b"
  recipientId: RecipientRef,          // WalletRef or Commitment per batch.schemaVersion
  leaf: AggregatedRewardLeaf | LinkableAggregatedRewardLeaf, // schemaVersion-defined
  proof: InclusionProof,          // Merkle proof from leaf to batch.root
  // audit-only attachments:
  // rewardEvents?: [SpendStreamEvent] // supporting REWARD_*_ISSUED events (audit / reconciliation)
  rewardInclusionProof?: RewardInclusionProof // optional when batch.schemaVersion is "2a" or "2b": spend↔reward linkage
}
```

**Derivation rules (normative):**
- `commitmentEvent` MUST be a valid `REWARD_BATCH_COMMITTED` system-stream event for `chainId`.
- `batch` MUST equal `commitmentEvent.payload`.
- `systemEvents` MUST be a contiguous, fork-free system-stream segment for `chainId` that includes `commitmentEvent` and is sufficient to validate:
  - integrity + `prevHash` linkage for the included segment, and
  - authority validity for `commitmentEvent.signedBy` at the event-effective time (typically `committedAt`) per `settlement-bindings.md#authority-registry`.
  If the included segment does not start at genesis (`prevHash = null`), a verifier MUST treat authority validation as **indeterminate** until it obtains any missing publicly replicable system-stream history and validates it cryptographically.
- `economicTier` MUST be:
  - `"COMMITTED"` when only the commitment proof material is present, or
  - `"COMMITTED_BACKED"` when a valid `REWARD_BATCH_BACKING_ATTESTED` is also included.
- If `economicTier = "COMMITTED_BACKED"`, then:
  - `backingEvent` MUST be present and MUST be a valid `REWARD_BATCH_BACKING_ATTESTED` for the same `chainId`.
  - `backingEvent.payload.batchId` MUST equal `batch.batchId`.
- `proof` MUST conform to the Merkle proof structure and hashing rules defined in `settlement-bindings.md#proof-structure` and `settlement-bindings.md#merkle-tree` (canonical leaf bytes, `0x00` leaf prefix, `0x01` internal prefix, sorted-pair hashing).

### Verification procedure (normative)

To verify a Reward Commitment Token, a verifier MUST:

1. Verify `systemEvents` as a contiguous, fork-free system-stream for `chainId` (integrity envelope + `prevHash` chaining) and verify authority validity per `../../core/spend-event.md` and `settlement-bindings.md#authority-registry`.
2. Verify `commitmentEvent` is included in `systemEvents`, and verify `batch` equals `commitmentEvent.payload`.
3. Verify the Merkle inclusion proof (`proof`) against `batch.root` per `settlement-bindings.md#verification-algorithm` (including leaf canonicalization and domain separation).
4. If `economicTier = "COMMITTED_BACKED"`, verify `backingEvent` integrity + authority validity and verify it references the same `batch.batchId`.
5. Apply local chain acceptance policy:
   - verifiers MAY rely solely on the signed system-stream history as authenticity for `batch.root`, and/or
   - verifiers MAY additionally verify `batch.txRef` on-chain and apply chain-specific finality thresholds (reorg handling is defined by chain bindings; see `settlement-bindings.md#chain-bindings`).
6. If audit attachments are provided (e.g., `rewardEvents`), verify their envelopes and ensure they are consistent with the committed leaf semantics (e.g., totals and/or linkage roots).

### Corrections and reorgs (normative interpretation)

- **Batch corrections:** correction batches are additional commitment-layer artifacts that adjust balances without negating historical issuance. A Reward Commitment Token for an original batch remains a valid proof of inclusion in that batch. It MUST NOT be interpreted as “current balance”; current balance requires processing correction batches and/or snapshots (see `settlement-bindings.md#correction-batches` and `settlement-bindings.md#cumulative-snapshots`).
- **Chain reorg / probabilistic finality:** verifiers SHOULD treat non-finalized on-chain anchoring as indeterminate/pending according to chain bindings and finality thresholds. This does not change the token’s signed system-stream validity, but may change whether a verifier accepts the anchoring as stable.

## Linking Spend ↔ Reward (Optional)

Reward commitments are recipient-scoped and may be **optionally linkable to per-spend reward issuance**.

When the Commitment Layer uses a linkable leaf schema (`schemaVersion` 2a or 2b, see settlement-bindings.md), a verifier can prove that:

- a specific reward issuance (identified by `spendId` + policy output) is included in the committed batch for a recipient, and
- that inclusion is bound to the on-chain root via a compact proof.

This produces a portable “spend ↔ reward” linkage without requiring the verifier to fetch and sum every reward event in the batch.

**Bounded claim (normative):** when present, `rewardInclusionProof` proves only that a `(spendId, rewardEventHash)` reference is included under the aggregated leaf’s `rewardEventsRoot`, and that the aggregated leaf is included in the batch root. Verifying the underlying reward event envelope (and therefore the meaning of `rewardEventHash`) is optional audit material and may be provided out-of-band.
