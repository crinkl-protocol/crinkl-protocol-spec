---
status: draft
layer: reward-settlement
version: v1
normative: true
---

# Reward Layer (Non-Protocol)

The Reward Layer operates above the protocol. It consumes Attestation Ledger events to compute economic outputs but does NOT define verification, normalization, or canonical truth.

The separation between attestation (epistemic commitment) and rewards (economic commitment) is intentional: economic action bears the cost of epistemic error while canonical truth remains protocol-defined and replayable. See the Economic Reinforcement Invariant in ../protocol/purpose/what-crinkl-proves.md.

Terms are defined in ../../../governance/glossary.md and used normatively throughout this specification.

## Reward Ledger Entry

```text
RewardLedgerEntry {
    wallet: WalletRef,
    rewardId?: Identifier,
    spendId: Identifier,
    policyVersion: Version,
    deltaPoints: Points,
    deltaBTCsats: Satoshis,
    timestamp: Timestamp
}
```

Reward entries are immutable once written. The protocol does not claw back or adjust rewards after issuance; fraud does not modify the Reward Ledger.

## Reward State Machine

```
NO_REWARD ──→ PROVISIONAL_REWARD_ISSUED ──→ FINAL_REWARD_ISSUED
     │                                              ▲
     └──────────────────────────────────────────────┘
```

| State | Definition |
|-------|------------|
| NO_REWARD | Default; no reward issued |
| PROVISIONAL_REWARD_ISSUED | Reward issued on SOFT_VERIFIED |
| FINAL_REWARD_ISSUED | Reward issued on HARD_VERIFIED |

### Allowed Transitions

| From | To | Preconditions |
|------|-----|---------------|
| NO_REWARD | PROVISIONAL_REWARD_ISSUED | At issuance time, current spend head class is `SOFT_VERIFIED`, `HARD_VERIFIED`, or `CORRECTED` (and not `INVALIDATED`) |
| NO_REWARD | FINAL_REWARD_ISSUED | At issuance time, current spend head class is `HARD_VERIFIED` or `CORRECTED` (skip provisional) |
| PROVISIONAL_REWARD_ISSUED | FINAL_REWARD_ISSUED | At issuance time, current spend head class is `HARD_VERIFIED` or `CORRECTED` |

**Issuance binding (normative):** reward issuance events are spend-stream events. `REWARD_*_ISSUED.prevHash` MUST equal the then-current spend-stream head `eventHash` for the `spendId` (see `../../core/spend-event.md#cross-fsm-ordering-constraints-normative`).

Reward entries are immutable: no clawbacks, no adjustments, even for fraud.

## Cross-Ledger Rules

1. Provisional reward requires spend >= SOFT_VERIFIED.
2. Final reward requires spend >= HARD_VERIFIED.
3. Spend invalidation does not alter prior rewards.
4. Corrections do not automatically trigger rewards; any additional rewards require explicit issuance events.

**Immutability:** Reward Ledger entries are never deleted or modified, even if the underlying spend is invalidated or corrected. This separation preserves reward finality independent of attestation corrections.

**Normative scope note:** any MUST/SHOULD/MAY in this file applies only to reward-layer implementations that claim conformance with this interface. These requirements MUST NOT be interpreted as affecting protocol event validity, token validity, or portable verification.

## Boundary

| Reward Layer Owns | Protocol Owns |
|-------------------|---------------|
| Reward amounts, formulas | Receipt verification |
| Payout timing, thresholds | Spend normalization |
| Policy rules, multipliers | Attestation Ledger state |
| Campaigns, bonuses | State machine transitions |

## Protocol Constraints on Rewards

1. **Provisional rewards** may issue after SOFT_VERIFIED (not before)
2. **Final rewards** may issue after HARD_VERIFIED (not before)
3. **Risk-flag gating (reward-layer)** — reward implementations MAY suppress provisional issuance when `riskFlags` indicate elevated risk (e.g., `potential_duplicate`); this MUST NOT affect verification validity.
4. **Reward Ledger is append-only** — entries are never deleted or modified
5. **No clawback** — once issued, rewards MUST NOT be revoked or adjusted by the protocol. This constraint applies only to protocol-level actions. Application-layer systems MAY implement independent recovery, offsetting, or account-level controls outside the protocol.
6. **policyVersion** MUST be recorded with every reward for auditability. This refers to the reward policy version, not the protocol version. Deployments SHOULD treat `policyVersion` as an audit pointer to a stable policy snapshot artifact (see `policy-layer.md`).
7. **Unique identity (reward-layer)** — reward-layer implementations SHOULD assign a unique `rewardId` for internal idempotency and reconciliation. If a deployment chooses to carry it in protocol artifacts, it MAY include `rewardId` in `REWARD_*_ISSUED` payloads (see `../../core/spend-event.md`) and in derived reward ledger views.

## Provisional vs Final Rewards

The relationship between provisional and final rewards (replacement, supplementation, or equivalence) is policy-defined and outside protocol scope. Both MAY exist as independent ledger entries for the same `spendId`.

## Reward Ledger Immutability

Attestation Ledger corrections (SPEND_CORRECTED, SPEND_INVALIDATED) do NOT alter prior Reward Ledger entries.

FRAUD_FLAGGED exists to preserve historical accuracy and enable downstream policy responses; it does not imply protocol-level economic reversal. Application-layer systems MAY use FRAUD_FLAGGED events to trigger out-of-band recovery mechanisms.

## Commitment Layer Integration

The optional Commitment Layer publishes Merkle roots of reward batches on-chain:

| Without Commitment | With Commitment |
|--------------------|-----------------|
| Off-chain attestation only | On-chain cryptographic proof |
| Operator trust assumed | Publicly verifiable commitment |
| Rewards disputable | Issuance non-repudiable |

When enabled, the `REWARD_BATCH_COMMITTED` event links off-chain rewards to their on-chain anchor. See settlement-bindings.md for full specification.

Commitments MAY use a linkable leaf schema (`schemaVersion = 2`) to support compact proofs that a specific `spendId`’s reward issuance is included in a committed batch.

## Non-Normative Notes

- Reward engines may run as independent services
- Multi-wallet aggregation, fees, and token mechanics are implementation decisions
