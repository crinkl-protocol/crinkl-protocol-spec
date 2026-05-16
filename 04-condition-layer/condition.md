---
status: draft
layer: condition
version: v1
normative: true
---

# Condition

A Condition is a rule over one or more Spend Attestations. Conditions are downstream of attestations: they do not create spend truth and they do not mint Spend Attestation Tokens.

Examples include threshold, merchant, category, market, new-buyer, repeat-spender, and time-window rules. Implementations SHOULD express Conditions as parameterized rules over finite proof primitives rather than custom campaign logic.

CampaignEpochs MAY reference a Condition by `conditionId` and `conditionHash`, but the epoch owns the effective window, timing rule, TargetMerchantSet binding, reward rule reference, funding tranche, and claim level for campaign evaluation. CandidateSet discovery is not campaign eligibility; only the reviewed TargetMerchantSet bound to the selected CampaignEpoch participates in condition evaluation.

Conditions remain downstream of Core Spend Attestation validity. A Condition MUST NOT rewrite Spend Attestation Token fields, change verification state, or move reward logic into Core.
