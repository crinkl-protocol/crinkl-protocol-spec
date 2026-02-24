# Reward Layer (Non-Protocol)

The Reward Layer operates above the protocol. It consumes Attestation Ledger events to compute economic outputs but does NOT define verification, normalization, or canonical truth.

The separation between attestation (epistemic commitment) and rewards (economic commitment) is intentional: economic action bears the cost of epistemic error while canonical truth remains protocol-defined and replayable. See the Economic Reinforcement Invariant in ABSTRACT.md.

Terms are defined in GLOSSARY.md and used normatively throughout this specification.

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
6. **policyVersion** MUST be recorded with every reward for auditability. This refers to the reward policy version, not the protocol version. Deployments SHOULD treat `policyVersion` as an audit pointer to a stable policy snapshot artifact (see `POLICY_LAYER.md`).
7. **Unique identity (reward-layer)** — reward-layer implementations SHOULD assign a unique `rewardId` for internal idempotency and reconciliation. If a deployment chooses to carry it in protocol artifacts, it MAY include `rewardId` in `REWARD_*_ISSUED` payloads (see `EVENTS.md`) and in derived reward ledger views.

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
| Operator trust assumed | Trustless verification |
| Rewards disputable | Issuance non-repudiable |

When enabled, the `REWARD_BATCH_COMMITTED` event links off-chain rewards to their on-chain anchor. See COMMITMENT_LAYER.md for full specification.

Commitments MAY use a linkable leaf schema (`schemaVersion = 2`) to support compact proofs that a specific `spendId`’s reward issuance is included in a committed batch.

## Non-Normative Notes

- Reward engines may run as independent services
- Multi-wallet aggregation, fees, and token mechanics are implementation decisions
