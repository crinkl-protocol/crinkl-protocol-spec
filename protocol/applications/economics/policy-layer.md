---
status: draft
layer: reward-settlement
version: v1
normative: true
---

# Policy Layer (Issuer / Application Layer, Protocol-Aligned Artifacts)

Crinkl separates **truth formation** (Attestation Ledger) from **economic action** (Reward Ledger).
This is a core invariant of the protocol (see `../protocol/purpose/what-crinkl-proves.md` and `reward-layer.md`).

However, deployments still need a *standard* way to describe and audit the **policy knobs** that:
- determine reward issuance outputs (`deltaPoints`, `deltaBTCsats`), and
- describe (optionally) any issuer-side economic posture (e.g. backing operations).

This document defines **policy artifacts** that are:
- **protocol-aligned** (canonical JSON + stable hashes),
- **portable** (can be shared/audited across participant apps),
- but **not protocol validity rules** (they do not change what makes an event/token cryptographically valid).

## 1) Why policy artifacts exist

The protocol requires that reward issuance records the `policyVersion` used at issuance time for auditability:
- `reward-layer.md`: `policyVersion` MUST be recorded with every reward.

The protocol does **not** define:
- reward formulas, multipliers, tiers, thresholds, campaigns (`reward-layer.md`),
- redemption availability, solvency, or reserves (`../../portability/spend-attestation-token.md` explicit non-claims),
- clawbacks/reversals (protocol has no clawback events).

Policy artifacts bridge this gap by making the issuer’s policy knobs **auditable** without making them protocol truth.

## 2) Terminology

- **Policy artifact**: a canonical JSON object that can be hashed and referenced.
- **Policy ID**: a stable identifier derived from hashing a policy artifact.
- **policyVersion (reward events)**: a string recorded on reward issuance events. In Crinkl deployments, this SHOULD be a stable policy ID or a human-friendly alias that resolves to a stable policy ID.

## 3) Canonicalization and hashing (normative)

Policy artifacts MUST be hashed using:
- RFC 8785 canonical JSON serialization (`../../core/canonicalization.md#serialization`)
- SHA-256 over the UTF-8 bytes of that canonical JSON
- Lowercase hex output (64 chars)

Recommended string form:
- `policyId = "sha256:" + <64 hex>`

> Note: Many legacy deployments have historically used raw 64-hex as a policy hash. That remains interoperable as a string, but new artifacts SHOULD prefer the `sha256:` prefix to reduce ambiguity across hash families.

## 3a) Recommendation: use the hash as `policyVersion`

For maximum audit stability, deployments SHOULD set:
- `policyVersion` (on reward issuance events) = the stable `policyId` (hash form), and
- keep any human-readable policy name as metadata (e.g. `policyVersionLabel`) inside the policy snapshot artifact.

This avoids drift when admins rename versions while preserving a friendly display label.

## 4) Reward Policy Snapshot (artifact)

The **Reward Policy Snapshot** is an issuer-defined artifact that captures the knobs used to compute reward issuance outputs.

This artifact is intended to back the `policyVersion` string recorded in `REWARD_*_ISSUED` payloads.

### RewardPolicySnapshotV1 (non-normative shape)

The exact reward math remains app/issuer-defined, but for interoperability the snapshot SHOULD include:
- identifiers: `policyId`, `policyVersion`, `policyVersionLabel`, `effectiveFrom`
- reserve checkpoint references (if used): `reserveCheckpointId`
- rule references (if used): `rulesetId`, `coinMultiplierRulesetId`
- scalar parameters used by the reward engine (e.g. base points, streak knobs, min-claim knobs)
- a policy hash (if the deployment uses a secondary hash such as `crinklPolicyHash`)

See JSON schema: `schemas/reward_policy_snapshot_v1.schema.json`.

## 4a) Campaign funding and reward rule references

CampaignEpochs reference reward policy by hash; they do not move reward math into Core.

- `rewardRuleHash` identifies the reward rule used by one CampaignEpoch.
- `FundingTranche` identifies a budget allocation committed to that CampaignEpoch.
- `RuleSetHash` binds the predicate, TargetMerchantSet reference/root, reward rule, claim level, effective window, timing rule, and funding reference.

Reward rules MAY change only by creating a new CampaignEpoch with a new `rewardRuleHash`. Budget increases MUST NOT mutate the original FundingTranche amount. If `ruleSetHash` is unchanged, a budget top-up MAY attach to the same CampaignEpoch through a child FundingTranche record with `parentFundingTrancheId`. If `ruleSetHash` changes, the campaign MUST append a new epoch. Unspent budget MAY roll forward only when the prior epoch funding policy permits it.

## 5) Reserve / backing artifacts (issuer claims, not protocol truth)

Crinkl tokens and events are explicit about non-claims:
- Reward commitments do NOT prove solvency, reserves, or redemption availability (`../../portability/spend-attestation-token.md`).

If a deployment wants to make issuer-side economic posture auditable, it SHOULD do so via:

### A) Backing attestations for committed batches (protocol-defined)

The protocol already defines an *operator attestation* event:
- `REWARD_BATCH_BACKING_ATTESTED` (`settlement-bindings.md`)

This event is signed and can be carried in Reward Commitment Tokens to claim an `economicTier` of `"COMMITTED_BACKED"` without asserting redemption availability for any specific user.

### B) Reserve snapshots (policy artifact, optional)

Deployments MAY publish a reserve snapshot artifact that describes:
- reserve parameter values,
- checkpoint identifiers,
- timestamping/effective windows,
- and (optionally) links to backing transactions.

Reserve snapshots remain issuer claims, not protocol truth.

## 6) Publication and discovery (out-of-protocol transport)

How policy artifacts are distributed is out-of-protocol. Common patterns include:
- a service-only database table (`policy.*` in the platform deployment),
- an admin API that serves the current policy snapshot,
- a signed system-stream publication event (future/optional; must not change protocol validity rules).

Recipients/verifiers SHOULD treat `policyVersion` as an **audit pointer**:
- it does not change event validity,
- but it enables deterministic replay of the issuer’s reward logic when combined with policy artifact retrieval.
