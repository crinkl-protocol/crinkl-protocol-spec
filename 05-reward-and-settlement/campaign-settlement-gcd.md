---
status: draft
layer: reward-settlement
version: v1
normative: true
---

# Campaign Settlement GCD

Campaign settlement on-chain means public commitments, not full campaign
operations.

The public can prove that Crinkl did not silently change the campaign rule after
the fact, did not publish a settlement root detached from that rule, did not
expose private buyer data on-chain, and did not let random actors mutate the
record.

The minimum primitive is:

```text
frozen campaign rule -> verified conversions -> settlement leaves -> settlement root -> public settlement anchor
```

This GCD is not the verifier. It is the public object that the verifier,
signature system, or future proof system MUST bind to.

## Scope

This document freezes the public settlement commitment standard for campaign
settlement. It relies on:

- `CampaignRuleV1` and `CampaignEpochV1` from
  `../04-condition-layer/campaign-commitment.md`
- reward and commitment conventions from `settlement-bindings.md`
- system-stream event envelope rules from `../01-core/spend-event.md`
- chain-specific anchoring rules from extension bindings such as
  `../06-extensions/solana-campaign-settlement-binding.md`

It does not define:

- platform workflows for campaign creation permissions
- sponsor pricing or campaign funding mechanics
- FIFO or promoter matching policy
- private creator eligibility review procedures
- payout execution rails
- raw conversion storage
- arbitrary campaign DSL composition

When a campaign includes `CampaignAuthorityV1` from
`../06-extensions/merchant-authority.md`, this GCD does define the public hash
binding required to prove the frozen campaign rule carried that authority. It
does not define how the private evidence behind a merchant claim was reviewed.

## Canonical Public Objects

The campaign settlement GCD is composed from these named objects:

```text
CampaignRuleV1
CampaignEpochV1
CampaignSettlementLeafV1
CampaignSettlementBatchV1
CAMPAIGN_SETTLEMENT_COMMITTED
```

`CampaignRuleV1.hashes` MUST include:

```text
hashes: {
  audienceHash: "sha256:" + Hash,
  conversionHash: "sha256:" + Hash,
  rewardPolicyHash?: "sha256:" + Hash,
  campaignAuthorityHash?: "sha256:" + Hash,
  ruleSetHash: "sha256:" + Hash,
  campaignParamsHash: "sha256:" + Hash
}
```

`CampaignEpochV1.ruleSetHash` MUST equal
`CampaignRuleV1.hashes.ruleSetHash` for the rule that created the epoch.

## Settlement Leaf

`CampaignSettlementLeafV1` is the stable public commitment shape for one
approved conversion settlement.

```text
CampaignSettlementLeafV1 {
  schemaVersion: 1,
  leafType: "CAMPAIGN_SETTLEMENT_LEAF",
  settlementId: Identifier,
  campaignId: Identifier,
  epochId: Identifier,
  ruleSetHash: "sha256:" + Hash,
  campaignParamsHash: "sha256:" + Hash,
  qualificationHash: "sha256:" + Hash,
  conversionHash: "sha256:" + Hash,
  conversionSpendTokenHash: "sha256:" + Hash,
  conversionHeadEventHash: Hash,
  approvalHash: "sha256:" + Hash,
  campaignAuthorityHash?: "sha256:" + Hash,
  payout: {
    amount: String(Integer >= 0),
    asset: "POINTS" | "BTC" | "CRINKL" | String
  },
  settlementScopeId: "sha256:" + Hash,
  settlementNullifier: "sha256:" + Hash,
  clearedAt: TimestampISO
}
```

The leaf MUST NOT contain raw receipt data, wallet identity, OCR text, line-item
details, or private buyer history.

For merchant-official campaigns, `campaignAuthorityHash` is REQUIRED and MUST
match the `CampaignRuleV1.hashes.campaignAuthorityHash` value. The referenced
authority proof material MAY be carried out-of-band with the settlement proof
bundle, but the public leaf MUST bind to the hash.

## Settlement Batch

`CampaignSettlementBatchV1` anchors a Merkle root for one or more settlement
leaves.

```text
CampaignSettlementBatchV1 {
  schemaVersion: "campaign-settlement-v1",
  settlementBatchId: Identifier,
  campaignId: Identifier,
  epochId: Identifier,
  ruleSetHash: "sha256:" + Hash,
  campaignParamsHash: "sha256:" + Hash,
  campaignAuthorityHash?: "sha256:" + Hash,
  root: Hash,
  leafCount: Integer > 0,
  totalPayoutAmount: String(Integer >= 0),
  payoutAsset: "POINTS" | "BTC" | "CRINKL" | String,
  txRef?: String,
  committedAt?: TimestampISO
}
```

The settlement root MUST be computed over `CampaignSettlementLeafV1` leaf hashes.
A settlement batch MUST be rejected if its `campaignId`, `epochId`,
`ruleSetHash`, or `campaignParamsHash` does not match the frozen campaign rule
and epoch.

For merchant-official campaigns, a settlement batch MUST also bind the same
`campaignAuthorityHash` as the frozen campaign rule.

## System Event

When a settlement root is anchored, the system-stream event is:

```text
CAMPAIGN_SETTLEMENT_COMMITTED {
  settlementBatchId: Identifier,
  campaignId: Identifier,
  epochId: Identifier,
  ruleSetHash: "sha256:" + Hash,
  campaignParamsHash: "sha256:" + Hash,
  campaignAuthorityHash?: "sha256:" + Hash,
  root: Hash,
  leafCount: Integer > 0,
  totalPayoutAmount: String(Integer >= 0),
  payoutAsset: String,
  schemaVersion: "campaign-settlement-v1",
  txRef: String,
  committedAt: TimestampISO
}
```

The event signer MUST be authorized for the campaign settlement commitment
surface at `committedAt`.

## Verification Requirements

A verifier MUST:

1. Recompute `campaignParamsHash` from `CampaignRuleV1`.
2. Recompute `ruleSetHash` from the selected `CampaignEpochV1` rule material.
3. Verify `CampaignRuleV1.hashes.ruleSetHash` matches the selected epoch.
4. If the campaign carries `CampaignAuthorityV1`, verify the authority proof
   hash and merchant claim attestation under
   `../06-extensions/merchant-authority.md`.
5. Verify each `CampaignSettlementLeafV1` binds to the same campaign, epoch,
   rule set, and campaign params.
6. Verify the settlement root from the included leaf hashes.
7. Verify the settlement batch matches the frozen campaign rule and epoch.
8. Verify the `CAMPAIGN_SETTLEMENT_COMMITTED` signer authority and `txRef`.
9. Reject private buyer data in public commitment artifacts.

## Required Security Test Classes

Implementations SHOULD maintain tests for:

- rule immutability: changed rule fields produce changed hashes
- epoch binding: settlement roots cannot attach to the wrong epoch
- rule-set binding: settlement roots cannot attach to the wrong rule
- campaign-params binding: settlement roots cannot attach to changed params
- campaign-authority binding: merchant-official settlements cannot attach to a campaign rule without the matching authority hash
- authority: unauthorized committers cannot publish or mutate commitments
- replay: duplicate settlement batch identifiers are rejected
- privacy: public artifacts contain hashes and commitments, not raw buyer data
- chain binding: `txRef` resolves to the expected deployment and instruction

If a campaign has no extra security concern beyond these GCD checks, the
implementation SHOULD state that explicitly and explain why.
