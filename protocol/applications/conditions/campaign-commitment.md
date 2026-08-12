---
status: deprecated
layer: applications
version: legacy-v1
normative: false
---

# Legacy Campaign commitment vocabulary

This path is retained as a compatibility redirect. The canonical target is the
[`Campaign protocol architecture`](../campaigns/README.md).

## Deprecation decision

`CampaignCommitment` is not a second canonical Campaign-definition object.
`CampaignEpoch` is the immutable signed version of Campaign rules and economic
terms. Generic prose that formerly assigned committed Campaign state to both a
`CampaignRuleV1`/`CampaignCommitment` and a `CampaignEpochV1` is deprecated.

The target composition is:

```text
SpendToken(s)
+ CampaignEpoch
-> optional ProofOfMatch(AUDIENCE)
-> optional assignment and exposure
-> ProofOfMatch(CONVERSION)
-> optional economic admission
-> CampaignOutcome
-> optional RewardObligation
-> SettlementRecord
```

## Preserved historical artifacts

No published bytes are changed by this redirect.

The complete pre-refactor draft prose remains retrievable at the exact source
baseline
[`700be7942efecb5863acb764f004b122f9e3c5fa`](https://github.com/crinkl-protocol/crinkl-protocol-spec/blob/700be7942efecb5863acb764f004b122f9e3c5fa/protocol/applications/conditions/campaign-commitment.md).
That historical text is evidence for legacy meaning only; it is not the target
Campaign architecture.

| Historical artifact or term | Preserved location | Compatibility meaning |
|---|---|---|
| public experimental `CampaignEpochV1` | [`../../../schemas/experimental/campaign-epoch.v1.schema.json`](../../../schemas/experimental/campaign-epoch.v1.schema.json) | earlier draft shape with `epochId`, `ruleSetHash`, `fundingTrancheId`, and `claimLevel`; not wire-compatible with the signed adopted V1 Epoch |
| experimental `CampaignAmendmentV1` | [`../../../schemas/experimental/campaign-amendment.v1.schema.json`](../../../schemas/experimental/campaign-amendment.v1.schema.json) | historical forward-amendment candidate |
| experimental `FundingTrancheV1` | [`../../../schemas/experimental/funding-tranche.v1.schema.json`](../../../schemas/experimental/funding-tranche.v1.schema.json) | historical funding candidate |
| released direct-reward `CampaignEpochV1` | [`../../../conformance/profiles/campaign-direct-buyer-reward-v1/protocol/schemas/campaign_epoch_v1.schema.json`](../../../conformance/profiles/campaign-direct-buyer-reward-v1/protocol/schemas/campaign_epoch_v1.schema.json) | immutable released V1 bytes pinned by exact ID and digest |
| `CampaignRuleV1` | historical prose and legacy implementations | deprecated composition description; its rule/economic meaning moves into content-addressed references on `CampaignEpochV2` |
| Solana `CampaignCommitment` account | [`../../extensions/solana-campaign-settlement-binding.md`](../../extensions/solana-campaign-settlement-binding.md) | legacy implementation account name, not a canonical Campaign object |
| `CampaignSettlementLeafV1` and settlement root | [`../economics/campaign-settlement-gcd.md`](../economics/campaign-settlement-gcd.md) | legacy supporting settlement evidence, not a Campaign Outcome or Settlement Record |

The two incompatible `CampaignEpochV1` byte sets remain distinguishable only by
exact schema ID, source, and content digest. Title-only or filename-only
resolution is prohibited.

[`CampaignEpochV2`](../../../schemas/experimental/campaigns/campaign_epoch_v2.schema.json) is an
additive, unreleased successor. It does not mutate, supersede at runtime, or
silently upgrade either V1 object.

## Legacy terms

| Legacy term | Canonical mapping | Rule |
|---|---|---|
| Audience Qualification / Eligibility Proof | `ProofOfMatch(purpose = AUDIENCE)` | business role, not a second proof type |
| Verified Conversion / Conversion Proof | `ProofOfMatch(purpose = CONVERSION)` | business role, not a second proof type |
| Conversion Approval | accepted conversion match plus any required economic admission, composed into `CampaignOutcome` | deprecated as a discretionary payout state |
| Campaign Qualified Conversion | no canonical object | eliminate unless a distinct consumer, authority, security, dispute, or lifecycle is later proven |
| Reward Commitment | `RewardObligation` for liability meaning | preserve exact adopted `RewardCommitmentV1` and token families as legacy objects |
| Finality Certificate | exact legacy certificate only | target ProofOfMatch quorum result is `ValidatorCertificate` |
| Settlement Receipt | `SettlementRecord` for liability-resolution meaning | preserve profile-specific escrow receipts as supporting evidence |

## Rule privacy and binding

Private Campaign rules may remain hidden, but the Epoch and proof profile MUST
bind the exact canonical rule used by the prover:

```text
commitment(rule actually evaluated)
=
rule commitment bound by CampaignEpoch
```

A hash alone does not provide confidentiality. The applicable rule-resolution
profile must define canonicalization, commitment construction, authorization,
and hiding properties where needed.

## Qualification, conversion, and economics

Qualification and conversion are separate purposes of `ProofOfMatch`; neither
is a reward or settlement decision. An uncapped Campaign can make accepted
conversion directly entitling under its signed terms. A constrained Campaign
must apply the Epoch's deterministic economic-admission policy before creating
a Reward Obligation.

FIFO, queue selection, budget reservation, inventory, concurrency, and slot
consumption are not ZK primitives. They remain auditable runtime or ledger
behavior unless a profile proves a need for a separate serialized artifact.

## Absence conditions

Omitting a Spend Token does not prove nonexistence. Any absence rule must bind a
defined observable-history or completeness boundary, including source/issuer
coverage, cutoff or snapshot, interval, accepted statuses, correction rules,
and unavailable-source behavior.

## Maturity

The canonical vNext Campaign architecture and schemas are
`SPECIFIED_NOT_IMPLEMENTED`. This redirect does not change the latest released
public package, adopted engineering schemas, Platform behavior, Proof Validator
procedures, escrow runtime, Reward Ledger, or production state.
