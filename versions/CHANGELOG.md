# Changelog

This repository is being prepared for its **first public release**. Earlier internal iterations existed, but version numbers have been reset for the public SemVer track.

## v1.0.0-rc.2 (2026-05-16)

- Adds CampaignEpoch as the append-only campaign amendment primitive.
- Defines Campaign, CampaignAmendment, FundingTranche, RuleSetHash, ClaimLevel, CandidateSet, TargetMerchantSet, EligibleMerchant, ProofOfMatch, and RewardCommitment campaign semantics.
- Adds experimental candidate schemas for CampaignRule, CampaignSettlementLeaf, CampaignEpoch, CampaignAmendment, and FundingTranche.
- Freezes the GCD candidate schemas for `CampaignRuleV1` and `CampaignSettlementLeafV1`, and defines campaign settlement authority requirements through the System-Stream Authority Registry.
- Documents `CAMPAIGN_EPOCH_APPENDED` as a future candidate system-stream event.
- Clarifies that campaign eligibility, TargetMerchantSet changes, reward rule changes, and budget top-ups are downstream condition/reward-layer behavior and do not alter Core Spend Attestation validity.
- Bumps current documentation and binding version markers to `1.0.0-rc.2`.

## v1.0.0-rc.1 (2025-12-21)

- First public release candidate for Crinkl Protocol v1.
- `protocolVersion` is `1.0.0-rc.1` across:
  - `/protocol` normative docs
  - `/bindings` schemas and bindings
  - `/conformance` vectors
  - `/reference` examples
