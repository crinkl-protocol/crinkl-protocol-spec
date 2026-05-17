---
status: draft
layer: reward-settlement
version: v1
normative: true
---

# Commitment Layer

The Commitment Layer publishes cryptographic proofs of reward issuance to an immutable blockchain. Once committed, rewards become **publicly verifiable** and **non-repudiable** — the operator cannot deny issuance or claw back rewards.

Terms are defined in ../08-governance/glossary.md and used normatively throughout this specification.

## Purpose

| Problem | Solution |
|---------|----------|
| Off-chain rewards could be disputed | On-chain Merkle root proves issuance |
| Operator could deny issuing reward | Recipient holds proof includable in public root |
| Centralized ledger could be altered | Blockchain provides immutability |
| Individual reward txs are expensive | Batch aggregation amortizes cost |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Off-Chain (Reward Ledger)                    │
│                                                                  │
│  REWARD_FINAL_ISSUED events (per-spend granularity)             │
│                                                                  │
│    recipient-A: spend-1 → +50pts, spend-2 → +100pts             │
│    recipient-B: spend-3 → +200pts                                │
│    recipient-C: spend-4 → +30pts, spend-5 → +80pts              │
└────────────────────────────────────────┬────────────────────────┘
                                         │
                                         │ Batch interval (hourly/daily/threshold)
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Commitment Batcher                           │
│                                                                  │
│  Aggregates per-recipient totals for the batch:                 │
│    recipient-A: 150pts                                           │
│    recipient-B: 200pts                                           │
│    recipient-C: 110pts                                           │
└────────────────────────────────────────┬────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     On-Chain (Commitment Layer)                  │
│                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐ │
│   │ Leaf₁...Leafₙ│───▶│ Merkle Tree  │───▶│  Commitment Root │ │
│   │(per recip.)  │    │   (SHA-256)  │    │  (batch, root)   │ │
│   └──────────────┘    └──────────────┘    └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Two-Tier Design

The commitment layer uses a **two-tier** model:

| Tier | Location | Granularity | Purpose |
|------|----------|-------------|---------|
| Reward Ledger | Off-chain | Per-spend | Full audit trail, signed events |
| Commitment | On-chain | Per-recipient-per-batch | Efficient verification, non-repudiation |

This design provides:
- **Full auditability** off-chain (every spend is recorded)
- **Efficient proofs** on-chain (one leaf per recipient per batch)
- **Privacy** (batch totals reveal less than itemized lists)

## Commitment Model

### Batch Aggregation

Rewards are committed in **batches** rather than individually:

| Approach | Gas Cost | Latency | Proof Size |
|----------|----------|---------|------------|
| Individual tx per reward | O(n) | Immediate | None needed |
| **Batch Merkle root** | O(1) | Batch interval | O(log n) |

Batch interval is implementation-defined (e.g., hourly, daily, or threshold-based).

### Aggregated Leaf Structure

Each leaf represents a recipient's **aggregated reward total** for the batch.

**Recipient scoping:** Reward commitment leaves MUST be scoped to a unique recipient identifier to ensure deterministic aggregation and verifiable issuance.

**Protocol boundary:** The Commitment Layer proves that rewards were issued and economically committed; it does not define who a user is or how value is routed, only that issuance occurred under a verifiable recipient scope.

**RecipientRef (normative):** in protocol v1, `RecipientRef` is one of:
- `WalletRef` — transparent wallet address (schemas `1a`, `2a`)
- `Commitment` — blinded per-batch recipient commitment (schemas `1b`, `2b`)

Wallet semantics (address routing, ownership verification) are application-layer concerns.

Leaf structure is versioned by `schemaVersion` in the on-chain commitment record and in the `REWARD_BATCH_COMMITTED` event payload.

#### Schema family (normative, closed set)

The `schemaVersion` for reward batch commitments is a **string** in the closed set: `"1a"`, `"1b"`, `"2a"`, `"2b"`.

- A single batch MUST use exactly one `schemaVersion` for all leaves under `root` (mixed schemas within a batch are forbidden).
- Verifiers MUST reject unknown `schemaVersion` values.

| schemaVersion | Leaf type | Fields (exact) | Recipient representation | Adds spend linkage |
|---|---|---|---|---|
| `1a` | `AggregatedRewardLeaf` | `batchId`, `recipientId`, `totalPoints` | `WalletRef` | no |
| `1b` | `AggregatedRewardLeaf` | `batchId`, `recipientId`, `totalPoints` | `Commitment` | no |
| `2a` | `LinkableAggregatedRewardLeaf` | `batchId`, `recipientId`, `totalPoints`, `rewardEventsRoot` | `WalletRef` | yes |
| `2b` | `LinkableAggregatedRewardLeaf` | `batchId`, `recipientId`, `totalPoints`, `rewardEventsRoot` | `Commitment` | yes |

All leaf objects MUST be serialized using RFC 8785 canonical JSON (see `../01-core/canonicalization.md#serialization`), and leaf hashes MUST follow the Merkle rules in `#merkle-tree`.

#### Schema v1a (Aggregated totals, transparent recipient)

```
AggregatedRewardLeaf {
    recipientId: WalletRef,    // Transparent wallet address
    totalPoints: Points,       // Sum of all deltaPoints for this recipient in this batch
    batchId: Identifier        // Batch identifier for disambiguation
}
```

#### Schema v1b (Aggregated totals, blinded recipient)

```
AggregatedRewardLeaf {
    recipientId: Commitment,   // Blinded commitment (see Recipient Blinding)
    totalPoints: Points,
    batchId: Identifier
}
```

**Why aggregated?**
- A recipient with 50 receipts in a batch gets **1 leaf**, not 50
- Smaller tree = smaller proofs in practice
- Users typically care about balance, not individual transactions

**Serialization:** RFC 8785 (JSON Canonicalization Scheme), consistent with all protocol events.

**Leaf hash:** `SHA-256(0x00 || canonicalize(AggregatedRewardLeaf))`, lowercase hex.

Note: Field order in canonical form is `batchId`, `recipientId`, `totalPoints` (alphabetical per RFC 8785).

#### Schema v2a (Aggregated totals + spend linkage, transparent recipient)

Schema v2 preserves the aggregated leaf model (one leaf per recipient per batch) while adding a commitment to the set of per-spend reward issuance events that produced the aggregate.

```
LinkableAggregatedRewardLeaf {
    recipientId: WalletRef,    // Transparent wallet address
    totalPoints: Points,
    batchId: Identifier,
    rewardEventsRoot: Hash     // Merkle root of RewardIssuanceLeaf values for this recipient+batch
}
```

#### Schema v2b (Aggregated totals + spend linkage, blinded recipient)

```
LinkableAggregatedRewardLeaf {
    recipientId: Commitment,   // Blinded commitment
    totalPoints: Points,
    batchId: Identifier,
    rewardEventsRoot: Hash
}
```

`rewardEventsRoot` enables compact proofs that a specific spend's reward issuance is included in a committed batch, without requiring a verifier to fetch and sum every reward event in the batch.

The batcher MUST compute `rewardEventsRoot` from the reward issuance events included in the batch for that recipient:

```
RewardIssuanceLeaf {
    spendId: Identifier,
    rewardEventHash: Hash       // eventHash of the corresponding REWARD_*_ISSUED spend-stream event
}
```

Rules:
- Leaves MUST be sorted deterministically by `spendId` (lexicographic by UTF-8 byte order of the `spendId` string).
- Duplicate `spendId` values within the same recipient+batch MUST be rejected by the batcher. If a verifier observes evidence of duplication (e.g., two distinct inclusion proofs for the same `(recipientId, batchId, spendId)` under the same `rewardEventsRoot`), the verifier MUST treat the linkage root as invalid/ambiguous.
- Leaf bytes MUST be `RFC8785_canonicalize(RewardIssuanceLeaf)`.
- Leaf hash and internal node hashing MUST use the same domain separation and Merkle rules as the batch tree (`0x00` leaf prefix, `0x01` internal prefix, sorted-pair internal hashing).
- `rewardEventHash` MUST equal the `eventHash` of the included reward event, recomputed per ../01-core/canonicalization.md.

### Per-Spend Detail (Off-Chain)

The off-chain Reward Ledger retains per-spend granularity:

```
RewardLedgerEntry {
    recipientId: RecipientRef, // Scoped to recipient (wallet or commitment)
    spendId: Identifier,       // Links to specific spend
    policyVersion: Version,
    deltaPoints: Points,
    awardedAt: Timestamp
}
```

To verify per-spend breakdown:
1. Request signed Reward Ledger events from operator
2. Sum `deltaPoints` for all events where `recipientId` matches
3. Verify sum equals on-chain `AggregatedRewardLeaf.totalPoints`

### Merkle Tree

| Property | Specification |
|----------|---------------|
| Hash function | SHA-256 (protocol standard) |
| Tree type | Binary, leaves padded to power of 2 |
| Leaf ordering | Sorted by `recipientId` (lexicographic by UTF-8 byte order of the `recipientId` string) |
| Domain separation | Leaf prefix: `0x00`, Internal prefix: `0x01` |
| Empty leaf | `emptyLeafHash = SHA-256(0x00 || "") = 6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d` (padding only) |
| Encoding | Lowercase hex throughout |

**Domain separation** prevents second-preimage attacks:
- Leaf hash: `SHA-256(0x00 || canonicalize(leaf))`
- Internal hash: `SHA-256(0x01 || left || right)` where left < right (sorted)

#### Deterministic ordering and duplicate handling (normative)

- The batcher MUST sort leaves by `recipientId` in ascending lexicographic order of UTF-8 bytes of the `recipientId` string.
- Duplicate `recipientId` values within a batch MUST be rejected (one leaf per recipient per batch). If a verifier observes evidence of duplicate recipients under the same `root`, the commitment MUST be treated as invalid/ambiguous.

#### Padding and empty leaves (normative)

- Let `leafCount` be the number of real recipient leaves committed for a batch.
- The Merkle tree MUST pad the leaf list to `paddedLeafCount = 2^ceil(log2(max(1, leafCount)))` by appending `emptyLeafHash` values.
- `emptyLeafHash` MUST NOT be treated as an admissible “real leaf”; it is padding only.

Implementations MAY publish `leafIndex` in proofs for debugging/audit, but proof verification MUST NOT depend on `leafIndex` (sorted-pair hashing makes direction bits unnecessary).

If included, `leafIndex` MUST be the 0-based index of the real leaf within the sorted (by `recipientId`) leaf list, and verifiers MAY validate it for sanity (range checks) but MUST NOT require it for proof validity.

### Commitment Record

The on-chain commitment stores the Merkle root and batch metadata:

```
CommitmentRecord {
    batchId: Identifier,       // Unique batch identifier
    root: Hash,                // Merkle root (SHA-256, hex)
    leafCount: Integer,        // Number of recipients in batch
    totalPoints: Points,       // Sum of all points in batch
    schemaVersion: String,     // Leaf schema version: "1a" | "1b" | "2a" | "2b"
    committedAt: Timestamp     // On-chain confirmation time
}
```

The on-chain representation is chain-specific; this structure defines the logical content.

For third-party verification of root origin, the commitment record MUST be authenticated via the system stream:
- `REWARD_BATCH_COMMITTED` provides the canonical `{batchId, root, leafCount, totalPoints, schemaVersion, txRef, committedAt}` and `chainId` (via the system envelope).
- Authority validity for that event is verified via the Authority Registry (see `#authority-registry`).

## Events

Commitment Layer events are published as **SystemStreamEvents** (see ../01-core/spend-event.md). The system envelope supplies:
- `chainId` (system stream key)
- `signedBy` (authority signer)

### REWARD_BATCH_COMMITTED

Emitted when a batch is successfully committed on-chain:

```
REWARD_BATCH_COMMITTED {
    batchId: Identifier,
    root: Hash,
    leafCount: Integer,
    totalPoints: Points,
    schemaVersion: String,       // "1a" | "1b" | "2a" | "2b"
    txRef: String,             // On-chain transaction reference (chain-specific format)
    committedAt: Timestamp
}
```

This event is recorded in the off-chain event stream to link rewards to their on-chain proof.

#### Deterministic event representation (normative)

Commitment layer events are carried as `SystemStreamEvent` envelopes (see `../01-core/spend-event.md`). The canonical, hashable representation is the RFC 8785 canonical JSON of the **system event envelope** (excluding `eventHash` and `signature`) as defined in `../01-core/canonicalization.md#integrity-envelope`.

On-chain logs/transactions are used for anchoring (`txRef`, `committedAt`) and finality, but are not the canonical bytes for `eventHash` unless a chain binding explicitly defines such a mapping.

### REWARD_BATCH_BACKING_ATTESTED

Emitted when the operator attests that **economic backing** has been performed for a committed reward batch (e.g., moving cbBTC/USDC into a designated vault).

This event provides *economic* assurance about reward liabilities. It MUST NOT be interpreted as independent verification of spend attestation.

```
REWARD_BATCH_BACKING_ATTESTED {
    batchId: Identifier,       // References REWARD_BATCH_COMMITTED.batchId
    backingAsset: {
        chainId: String,       // Chain where backing transfer occurred (e.g., 'solana-mainnet')
        mint: String,          // Asset identifier on that chain (e.g., SPL mint)
        decimals: Integer      // Minor units for backingAmount
    },
    backingAmount: String,     // Integer minor units (e.g., sats for 8-decimal assets)
    backingVault: String,      // Vault destination (chain-specific address)
    backingTxRef: String,      // Transfer tx reference (chain-specific format)
    backedAt: Timestamp
}
```

**Normative constraints:**
- `batchId` MUST reference an existing committed batch (a valid `REWARD_BATCH_COMMITTED` for the same `chainId`).
- `backingTxRef` MUST refer to a publicly verifiable transaction on `backingAsset.chainId`.
- The protocol does not require that backing occurs synchronously with commitment; backing MAY occur after `REWARD_BATCH_COMMITTED` (and MAY be absent).

## Verification

### Commitment verification oracle (normative)

To verify that a claimed reward inclusion is anchored to an authentic committed batch, a verifier MUST be able to complete the following checks using only:
- the commitment proof material (`InclusionProof` and the referenced leaf),
- the relevant system-stream commitment events (`REWARD_BATCH_COMMITTED`, and optionally `REWARD_BATCH_BACKING_ATTESTED`),
- the Authority Registry history for the `chainId`, and
- public chain data when the verifier chooses to validate `txRef` anchoring/finality.

**Unknown versions (normative):** verifiers MUST reject unknown `schemaVersion` values.

### Recipient Verification Flow (portable)

A recipient can verify their reward inclusion:

1. **Obtain commitment header:** Obtain a valid `REWARD_BATCH_COMMITTED` system-stream event (and, if present/required by policy, a `REWARD_BATCH_BACKING_ATTESTED` event).
2. **Verify authority + integrity:** Verify the commitment event’s integrity envelope and verify the signer is authorized for `chainId` at `committedAt` (Authority Registry).
3. **Check schema version:** Verify `schemaVersion` is one of `"1a" | "1b" | "2a" | "2b"`; reject otherwise.
4. **Reconstruct leaf:** Build the schema-appropriate leaf object (`AggregatedRewardLeaf` for `"1a"/"1b"`, `LinkableAggregatedRewardLeaf` for `"2a"/"2b"`).
5. **Compute leaf hash:** `SHA-256(0x00 || RFC8785_canonicalize(leaf))`.
6. **Walk proof:** For each sibling, compute the next parent hash using sorted-pair hashing with `0x01` prefix.
7. **Compare root:** The resulting root MUST equal `REWARD_BATCH_COMMITTED.payload.root`.
8. **Optional chain anchoring:** If validating anchoring/finality, resolve `txRef` and apply chain-specific finality thresholds (chain bindings).

### Proof Structure

```
InclusionProof {
    batchId: Identifier,
    leaf: AggregatedRewardLeaf | LinkableAggregatedRewardLeaf,
    leafHash: Hash,            // Pre-computed for convenience
    siblings: [Hash],          // Sibling hashes from leaf to root
    leafIndex?: Integer        // OPTIONAL 0-based index of the real leaf in the sorted leaf list (debug/audit only)
}
```

### Verification Algorithm

```
function verify(proof: InclusionProof, expectedRoot: Hash) -> bool:
    // Recompute leaf hash with domain separation
    canonical = canonicalize(proof.leaf)
    hash = sha256(0x00 || canonical)
    
    if hash != proof.leafHash:
        return false
    
    // Walk up tree with domain separation
    for sibling in proof.siblings:
        // Sort for deterministic ordering
        if hash < sibling:
            hash = sha256(0x01 || hash || sibling)
        else:
            hash = sha256(0x01 || sibling || hash)
    
    return hash == expectedRoot
```

### Long-term verifiability (normative)

To enable verification years later without private operator databases, the following fields MUST be durably available via public chain data and/or the publicly replicable system stream:

- `chainId` (system-stream key)
- `signedBy` and the Authority Registry history needed to validate it at the effective time
- `batchId`
- `root`
- `schemaVersion` (leaf schema family identifier)
- `leafCount`
- `txRef` (anchoring reference) and `committedAt` (effective time / as-of anchor)

If a deployment stores only `root` on-chain, it MUST still make the corresponding system-stream event history publicly replicable so third parties can recover schemaVersion, authority, and effective time.

## Spend ↔ Reward Link Proofs (Optional)

When `schemaVersion` is `"2a"` or `"2b"`, a verifier can prove that a specific reward event for a specific `spendId` is included in a committed batch for a recipient.

This requires two proofs:

1. A **batch inclusion proof**: proves the recipient's `LinkableAggregatedRewardLeaf` is included under the committed batch root.
2. A **reward inclusion proof**: proves a `RewardIssuanceLeaf` is included under `rewardEventsRoot` inside that aggregated leaf.

### Reward inclusion proof structure

```
RewardInclusionProof {
    batchId: Identifier,
    recipientId: RecipientRef,
    rewardEventsRoot: Hash,
    leaf: RewardIssuanceLeaf,
    leafHash: Hash,
    siblings: [Hash]            // Sibling hashes from leaf to rewardEventsRoot
}
```

### Spend↔reward verification (high-level)

A verifier MUST:

1. Verify the reward event (`REWARD_*_ISSUED`) integrity envelope and recompute its `eventHash`.
2. Verify the reward inclusion proof against `rewardEventsRoot`, where `leaf.rewardEventHash` MUST equal the reward event’s `eventHash`.
3. Verify the batch inclusion proof for the recipient aggregated leaf against the on-chain `CommitmentRecord.root`.
4. Verify that the aggregated leaf’s `rewardEventsRoot` equals the `rewardEventsRoot` used in step 2.

## Security Properties

### Non-Repudiation

Once a commitment is written on-chain:
- The operator cannot deny the batch existed
- Anyone can verify the root matches published proofs
- Blockchain finality prevents alteration

### No Clawback

The commitment layer enforces reward immutability:
- Commitments are append-only; no deletion mechanism
- Fraud determinations do not modify reward commitments; fraud is signaled via `FRAUD_FLAGGED` without protocol-level reward adjustments (see reward-layer.md)
- The commitment proves issuance *occurred*, not current balance

### Authority Model

Only a designated authority can create commitments:
- Authority identity is chain-specific (key, multisig, governance contract)
- Schema version prevents client/server drift
- Implementations SHOULD support authority rotation

## Timing Guarantees

| Guarantee | Mechanism |
|-----------|-----------|
| No backdating | `committedAt` reflects on-chain confirmation |
| Monotonic batches | `batchId` must be unique per commitment |
| Finality | Depends on chain; verifiers SHOULD apply chain binding finality thresholds |
| Liveness | Not guaranteed by the protocol; batch interval is deployment-defined and MUST NOT be assumed by verifiers |

## Schema Versioning

Leaf schema is versioned to support evolution. Recipient representation (transparent vs blinded) is a schema choice, not an optional mode.

| Version | Structure | Recipient |
|---------|-----------|----------|
| 1a | recipientId, totalPoints, batchId | WalletRef (transparent) |
| 1b | recipientId, totalPoints, batchId | Commitment (blinded) |
| 2a | recipientId, totalPoints, batchId, rewardEventsRoot | WalletRef (transparent) |
| 2b | recipientId, totalPoints, batchId, rewardEventsRoot | Commitment (blinded) |

New schema versions MUST be introduced by adding a new `schemaVersion` identifier and a fully specified leaf schema. Verifiers MUST reject unknown `schemaVersion` values unless they explicitly implement that schema.

## Integration with Reward Layer

The Commitment Layer is an **optional extension** to the Reward Layer:

| Without Commitment | With Commitment |
|--------------------|-----------------|
| Rewards stored off-chain only | Rewards anchored on-chain |
| Operator attestation | Cryptographic proof |
| Trust required | Publicly verifiable commitment |

Implementations MAY operate without the Commitment Layer, but SHOULD use it for production deployments where recipient trust is paramount.

## Correction Batches

Committed batches are immutable, but errors may occur. The protocol handles corrections via **correction batches** rather than modifying existing commitments.

### Append-only rule (normative)

- A committed batch root MUST NOT be replaced, rewritten, or “updated in place”.
- A correction MUST be represented as a new committed root (`REWARD_BATCH_CORRECTION`) that references a specific target batch and adds compensating deltas.

### REWARD_BATCH_CORRECTION Event

```
REWARD_BATCH_CORRECTION {
    correctionBatchId: Identifier,    // This correction's batch ID
    targetBatchId: Identifier,        // The batch being corrected
    reason: String,                   // Human-readable justification
    adjustments: [CorrectionLeaf],    // Leaf-level adjustments
    root: Hash,                       // Merkle root of correction leaves
    txRef: String,
    committedAt: Timestamp
}
```

**Normative constraints:**
- `correctionBatchId` MUST be globally unique (MUST NOT equal any `batchId` or other `correctionBatchId`).
- `targetBatchId` MUST reference an existing committed batch (`REWARD_BATCH_COMMITTED`) for the same `chainId`.
- `reason` MUST be non-empty (verifiers may ignore semantics, but the correction must be attributable).

### CorrectionLeaf Structure

```
CorrectionLeaf {
    recipientId: RecipientRef, // Same representation as target batch schema
    deltaPoints: Points,       // Non-negative; corrections MUST NOT reduce balances (no clawback)
    correctionType: 'adjust' | 'add_missing',
    targetBatchId: Identifier  // Which batch is being corrected
}
```

**Recipient representation (normative):** `recipientId` in a correction leaf MUST match the recipient representation of the target batch’s `schemaVersion` (`WalletRef` for `"1a"/"2a"`, `Commitment` for `"1b"/"2b"`).

### Correction Rules

| Rule | Rationale |
|------|-----------|
| Original batch remains on-chain | Immutability preserved |
| Correction references target batch | Audit trail maintained |
| Net balance = original + corrections | Wallet sums all relevant batches |
| Corrections are also committed | Same non-repudiation guarantees |

**No clawback:** `deltaPoints` MUST be non-negative. Over-issuance (whether from operational error or fraud determination) is not corrected by reducing recipient balances; operators MUST absorb losses or handle remediation off-protocol.

### Correction root construction (normative)

`REWARD_BATCH_CORRECTION.payload.root` MUST be computed as a Merkle root over the set of `CorrectionLeaf` objects using the same Merkle conventions as batch roots:

- Leaf bytes: `RFC8785_canonicalize(CorrectionLeaf)`
- Leaf hash: `SHA-256(0x00 || leafBytes)`
- Internal hash: `SHA-256(0x01 || sort(left,right))`
- Leaf ordering: sort by `recipientId` (lexicographic by UTF-8 bytes of the `recipientId` string)
- Duplicate rule: duplicate `recipientId` values within the same correction batch MUST be rejected
- Padding: use `emptyLeafHash` as defined in `#merkle-tree`

### Recipient Balance Calculation

```
function recipientBalance(recipientId, batches, corrections) -> Points:
    total = 0
    for batch in batches:
        leaf = findLeafForRecipient(batch, recipientId)
        if leaf:
            total += leaf.totalPoints
    for correction in corrections:
        leaf = findCorrectionLeafForRecipient(correction, recipientId)
        if leaf:
            total += leaf.deltaPoints
    return total
```

### Deterministic balance oracle (normative)

To compute a recipient’s **current balance** as-of a specific commitment history point, a verifier MUST define the history point and the set of system events included.

Recommended as-of definition:
- “as-of” a system-stream head event hash `H` (the verifier has a contiguous, fork-free system stream for `chainId` from genesis up to `H`).

Balance computation over that as-of history:
- Include every `REWARD_BATCH_COMMITTED` event up to `H` and sum `leaf.totalPoints` for the recipient.
- Include every `REWARD_BATCH_CORRECTION` event up to `H` and sum `CorrectionLeaf.deltaPoints` for the recipient.

**Double-count protection (normative):**
- `batchId` values MUST be unique across the chain’s history; verifiers MUST treat duplicate `batchId` roots as invalid/ambiguous.
- `correctionBatchId` values MUST be unique across the chain’s history; verifiers MUST treat duplicates as invalid/ambiguous.
- Multiple correction batches MAY target the same `targetBatchId`; all such corrections are additive and MUST be included (there is no precedence override since deltas are non-negative).

## Cumulative Snapshots

For recipients with many rewards across batches, verifying each batch is expensive. **Cumulative snapshots** provide O(1) total balance proofs.

### Snapshot scope and privacy (normative)

Cumulative snapshots require a recipient identifier that is stable across the set of included batches.

In protocol v1, cumulative snapshots are defined only for deployments that use **transparent recipient schemas** (`"1a"` / `"2a"`, where `recipientId` is a `WalletRef`) across the included history.

Deployments that use blinded recipient schemas (`"1b"` / `"2b"`) MUST NOT publish cumulative snapshots unless/until a snapshot-specific privacy scheme is specified.

### Snapshot Structure

```
CumulativeSnapshot {
    snapshotId: Identifier,
    snapshotRoot: Hash,            // Merkle root of all recipient balances
    leafCount: Integer,            // Number of recipients in snapshot
    throughBatchId: Identifier,    // Last batch included
    throughEventHash: Hash,        // System-stream head eventHash included (recommended: equals snapshot event.prevHash)
}
```

### SnapshotLeaf Structure

```
SnapshotLeaf {
    recipientId: RecipientRef,     // Same representation as underlying batches
    cumulativePoints: Points,      // Total balance through this snapshot
    batchCount: Integer,           // Number of batches included
    lastBatchId: Identifier        // Most recent batch in this snapshot
}
```

### CUMULATIVE_SNAPSHOT_COMMITTED Event

```
CUMULATIVE_SNAPSHOT_COMMITTED {
    snapshotId: Identifier,
    snapshotRoot: Hash,
    leafCount: Integer,
    throughBatchId: Identifier,
    throughEventHash: Hash,        // MUST equal this event envelope's prevHash
    txRef: String,
    committedAt: Timestamp
}
```

**Normative constraints:**
- `snapshotId` MUST be globally unique.
- `throughEventHash` MUST equal the system-stream event envelope’s `prevHash` for the snapshot event. This binds the snapshot to an explicit commitment history point and makes omissions of earlier corrections auditable.

### Snapshot Properties

| Property | Guarantee |
|----------|-----------|
| Deterministic | Same batches → same snapshot |
| Incremental | New snapshot = prev snapshot + new batches |
| Verifiable | Wallet proves inclusion with O(log n) proof |
| Efficient | One proof covers entire history |

### Snapshot root construction (normative)

`snapshotRoot` MUST be computed as a Merkle root over `SnapshotLeaf` objects using the same Merkle conventions as batch roots (leaf bytes canonicalized via RFC 8785, `0x00`/`0x01` domain separation, sorted-pair hashing, leaves sorted by `recipientId`, duplicates rejected, padded with `emptyLeafHash`).

### Balance Verification with Snapshots

1. Obtain latest `CumulativeSnapshot` that includes recipient
2. Get `SnapshotLeaf` for recipient with inclusion proof
3. Verify proof against on-chain `snapshotRoot`
4. For rewards after snapshot: verify individual batch proofs
5. Total = `SnapshotLeaf.cumulativePoints` + post-snapshot rewards

### Snapshot trust and supersession (normative)

Snapshots are **performance checkpoints**, not independent sources of truth:
- Snapshot inclusion proofs are bounded (O(log n)).
- Correctness of `cumulativePoints` relies on trusting the snapshot issuer authority; independent audit may require replaying underlying batch + correction roots up to `throughEventHash`.

If multiple snapshots exist:
- A verifier MUST accept only snapshots committed by an authorized authority for `chainId`.
- Among accepted snapshots, a verifier SHOULD prefer the snapshot with the greatest `committedAt` (or, equivalently, the snapshot that appears latest in the canonical system-stream chain).
- If two accepted snapshots have the same `throughEventHash` but different `snapshotRoot`, the verifier MUST treat snapshot history as invalid/ambiguous (issuer equivocation) and MUST NOT pick a winner.

## Recipient Blinding

Blinded schemas (v1b, v2b) hide recipient identity while preserving verifiability. This is a **schema choice**, not an optional mode—recipient representation is determined by `schemaVersion`.

### Commitment Computation

For blinded schemas, `recipientId` is a domain-separated commitment:

```
recipientId = SHA-256(
    UTF-8("crinkl.recipient.v1:") ||
    UTF-8(wallet) ||
    UTF-8(":") ||
    UTF-8(batchId) ||
    UTF-8(":") ||
    blinder
)
```

Where:
- Domain prefix: `"crinkl.recipient.v1:"` (literal ASCII)
- `wallet`: Underlying wallet address as a canonical string per chain bindings (known only to recipient)
- `batchId`: Batch identifier as string
- `blinder`: 32 random bytes (stored privately by recipient)

The SHA-256 output MUST be encoded as lowercase hex (64 chars) to form the `recipientId` string stored in leaf payloads.

#### Entropy and determinism (normative)

- `blinder` MUST be generated using a cryptographically secure random number generator (CSPRNG) and MUST have at least 128 bits of entropy (32 bytes RECOMMENDED; protocol v1 uses 32 bytes).
- `blinder` MUST be unique per `(wallet, batchId)` and MUST NOT be reused across batches. Reuse creates cross-batch linkability if any blinder is compromised.
- The computation is deterministic given the same `(wallet, batchId, blinder)` inputs.

#### Small-domain resistance (normative)

The blinded `recipientId` MUST be infeasible to reverse or enumerate offline.

This construction resists small-domain enumeration because `blinder` is high-entropy secret material; hashing a low-entropy identifier without a secret blinder is forbidden.

### Blinder Management

```
Blinder {
    wallet: WalletRef,             // Underlying wallet (private)
    batchId: Identifier,
    blinder: bytes[32],            // Random 32-byte value
    createdAt: Timestamp
}
```

The recipient stores blinders privately. To prove inclusion:
1. Reveal `(wallet, batchId, blinder)` to verifier (`blinder` encoded as base64 over 32 bytes)
2. Verifier recomputes `recipientId` using formula above
3. Verifier checks leaf's `recipientId` matches
4. Proceed with standard Merkle proof verification

### Blinder provisioning (out-of-protocol, required for interoperability)

Blinded recipient schemas (`"1b"`, `"2b"`) require the batcher to construct leaves containing a blinded `recipientId`. This specification defines *how* `recipientId` is computed, but the transport of blinders is **out-of-protocol**.

Implementations that claim support for blinded schemas MUST provide an interoperable way for a recipient to supply a per-batch blinder (or an already-derived `recipientId`) to the issuer/batcher **before** the batch is committed.

Minimum interoperable registration object (transport may be API, wallet message, etc.):

```text
RecipientBlindingRegistrationV1 {
  schemaVersion: 1,
  wallet: WalletRef,
  batchId: Identifier,
  blinder: Base64,           // 32 bytes
  recipientId: Commitment    // lowercase hex; MUST equal compute(wallet,batchId,blinder)
}
```

**Issuer/batcher requirements (normative):**
- MUST verify `recipientId` equals the `recipientId` computed per `#commitment-computation`.
- MUST bind the registration to the correct wallet (authentication is out-of-protocol; deployments MUST ensure attackers cannot register blinders for wallets they do not control).
- MUST NOT reuse a blinder across different `(wallet, batchId)` pairs.
- If no valid registration exists for a wallet that would otherwise receive rewards in a blinded-schema batch, the deployment MUST either:
  - exclude that recipient from the blinded batch and defer issuance, or
  - use a transparent-schema batch for that issuance.

This preserves the protocol’s “identity minimization on-chain” goal while keeping blinded schema commitments implementable across deployments.

#### Compromise impact (normative)

- If a specific `(wallet, batchId, blinder)` is disclosed, it de-anonymizes that recipient **for that batch only**.
- Because `batchId` is included in the commitment input and blinders MUST be per-batch, disclosure does not enable linking across other batches unless blinders were reused (forbidden).
- Blinded recipient mode remains verifiable for recipients: they can recompute `recipientId` privately and produce/verify inclusion proofs without relying on issuer-secret salts.

### Privacy Guarantees

| Guarantee | Mechanism |
|-----------|-----------|
| Unlinkability | Without blinder, `recipientId` reveals nothing |
| Selective disclosure | Recipient chooses which rewards to prove |
| Forward secrecy | Compromised blinder affects only that batch |
| Public auditability | Total points per batch still visible |

### Schema Selection

Recipient representation is encoded in `schemaVersion`:

| Schema | Recipient | Use Case |
|--------|-----------|----------|
| 1a, 2a | WalletRef | Public transparency, simple verification |
| 1b, 2b | Commitment | Privacy-preserving, selective disclosure |

Implementations MAY use different schemas for different batches. Verifiers MUST parse `recipientId` according to the declared `schemaVersion`.

## Authority Registry

To verify commitments, recipients must know which authority was valid at commitment time. The **Authority Registry** provides this.

### AuthorityRecord Structure

```
AuthorityRecord {
    authorityId: Identifier,       // Unique authority identifier
    publicKey: PublicKey,          // Ed25519 public key
    validFrom: Timestamp,          // When authority became active
    validUntil: Timestamp | null,  // When revoked (null if current)
    revokedBy: Identifier | null,  // Successor authority that revoked this one
    chainId: String,
    txRef: String                  // On-chain registration transaction
}
```

### AUTHORITY_REGISTERED Event

```
AUTHORITY_REGISTERED {
    authorityId: Identifier,
    publicKey: PublicKey,
    validFrom: Timestamp,
    predecessorId: Identifier | null,  // Previous authority (for rotation)
    txRef: String,
    registeredAt: Timestamp
}
```

### AUTHORITY_REVOKED Event

```
AUTHORITY_REVOKED {
    authorityId: Identifier,
    validUntil: Timestamp,
    revokedBy: Identifier,         // New authority that performed revocation
    reason: String,
    txRef: String,
    revokedAt: Timestamp
}
```

### Authority Verification

To verify a commitment-layer event (e.g., `REWARD_BATCH_COMMITTED`, `REWARD_BATCH_CORRECTION`, `CUMULATIVE_SNAPSHOT_COMMITTED`):

1. Determine the event-effective time (for commitment artifacts, this is `committedAt`).
2. Reconstruct the Authority Registry state for the event’s `chainId` at that effective time by replaying the system stream (fork-free `prevHash` chain).
3. Verify that `signedBy` refers to an authority that is valid at the effective time (within `[validFrom, validUntil)`).
4. Verify the event envelope signature using that authority’s `publicKey`.

**Revocation semantics (normative):**
- Events/commitments signed by an authority during its validity window remain valid historical artifacts.
- Verifiers MUST reject any event whose effective time is outside the signer’s validity window (including after revocation).

### Authority Chain

```
Authority₀ ──(rotation)──▶ Authority₁ ──(rotation)──▶ Authority₂
   │                           │                           │
validFrom: T₀              validFrom: T₁               validFrom: T₂
validUntil: T₁             validUntil: T₂              validUntil: null
```

Each authority signs commitments only during its validity window. The on-chain registry provides an immutable audit trail of authority changes.

#### No delegation (normative, protocol v1)

The Authority Registry is a **rotation log**, not a general delegation graph:
- `predecessorId` indicates the prior authority for rotation/audit only.
- There is no transitive delegation rule in protocol v1; verifiers MUST NOT accept signatures from an authority unless it is explicitly valid at the event-effective time.
- If multiple authorities appear simultaneously valid for the same `chainId` and time window, verifiers MUST treat the registry as invalid/ambiguous for that interval.

### Security Considerations

| Threat | Mitigation |
|--------|------------|
| Key compromise | Immediate rotation; old commitments remain valid |
| Rogue authority | Revocation propagates; recipients reject future commits |
| Backdated commits | `committedAt` comes from chain, not authority |
| Split-brain | Single on-chain registry is source of truth |

## Chain Bindings

This specification is chain-agnostic. Implementations define chain-specific bindings:

| Aspect | Chain Binding Defines |
|--------|----------------------|
| Wallet format | Address encoding (e.g., base58 for Solana, 0x-prefixed for Ethereum) |
| Commitment storage | Contract/program structure, account model |
| Transaction format | How `txRef` is encoded |
| Finality rules | When `committedAt` is considered immutable |

### Anti-replay requirements (normative)

To prevent cross-chain replay/ambiguity of commitments, chain bindings MUST define:

- **`chainId` encoding:** a canonical identifier that includes network/environment (recommended: CAIP-2 style such as `eip155:1` or `solana:mainnet-beta`).
- **Commitment location:** the contract/program identifier (and, if applicable, event/log name) that defines where commitment artifacts live on that chain.
- **`txRef` encoding:** a canonical reference that uniquely identifies the anchoring location on that chain and includes (directly or by implication) the commitment location (e.g., `(chainId, contractAddress, blockHeight, txIndex, logIndex)` on EVM-like chains or `(chainId, programId, slot, txIndex, instructionIndex)` on Solana-like chains).

Verifiers SHOULD reject commitment artifacts whose `txRef` cannot be parsed or does not match the expected commitment location for the deployment.

Campaign settlement commitment requirements are defined in
`campaign-settlement-gcd.md`. The Solana campaign settlement binding is defined
in `../06-extensions/solana-campaign-settlement-binding.md`.

Chain bindings are documented separately from this core specification.

## Implementation Notes

- **Batch sizing:** Balance latency vs. cost (e.g., 100-10,000 recipients/batch)
- **Proof storage:** Off-chain proofs stored in database, served via API
- **Proof lookup:** Query by `(recipientId, batchId)` — simpler than per-spend
- **Optimization:** Implementations MAY use faster hashes (e.g., Blake3) internally if they produce equivalent proofs when serialized per this spec
- **Claiming:** Commitment proves entitlement; token distribution is separate
