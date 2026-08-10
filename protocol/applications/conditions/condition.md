---
status: draft
layer: predicate
version: v1
normative: true
---

# Spend Predicate

A Spend Predicate is a rule over one or more Spend Attestations. Spend Predicates are downstream of attestations: they do not create spend truth and they do not mint Spend Attestation Tokens.

Examples include threshold, merchant, category, market, new-buyer, repeat-spender, and time-window rules. Implementations SHOULD express Spend Predicates as parameterized rules over finite proof primitives rather than custom campaign logic.

CampaignEpochs MAY reference a Spend Predicate by `predicateId` and `predicateHash`, but the epoch owns the effective window, timing rule, TargetMerchantSet binding, reward rule reference, funding tranche, and claim level for campaign evaluation. CandidateSet discovery is not campaign eligibility; only the reviewed TargetMerchantSet bound to the selected CampaignEpoch participates in predicate evaluation.

Spend Predicates remain downstream of Core Spend Attestation validity. A Spend Predicate MUST NOT rewrite Spend Attestation Token fields, change verification state, or move reward logic into Core.
