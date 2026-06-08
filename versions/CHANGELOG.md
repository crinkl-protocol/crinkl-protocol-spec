# Changelog

This repository is being prepared for its **first public release**. Earlier internal iterations existed, but version numbers have been reset for the public SemVer track.

## v1.0.0-rc.2 GMV policy clarification (2026-06-08)

- Clarifies the Crinkl v1 Verified GMV inclusion guardrail for high-total spends: finalized spends over $500 are excluded from `verifiedGMV` until explicit high-total review approval is recorded.
- Documents the 14-day active GMV correction window used for cumulative aggregation, reflecting ordinary receipt, return, and dispute timing.
- Does not change `protocolVersion`, `tokenType`, `schemaVersion`, token hashing, Merkle construction, or signature verification rules.

## v1.0.0-rc.2 extension update (2026-06-01)

- Adds rc.2-compatible merchant authority extension artifacts for `MerchantClaimAttestationV1`, `MerchantClaimEventV1`, and `CampaignAuthorityV1`.
- Clarifies that verified merchant campaigns require a campaign authority binding, while Spend Attestation Token validity and operator/system campaign validity remain unchanged.
- Does not change the global `protocolVersion`; merchant authority uses artifact-level `schemaVersion` values.

## v1.0.0-rc.2 (2026-05-16)

- Adds CampaignEpoch as the append-only campaign amendment primitive.
- Defines Campaign, CampaignAmendment, FundingTranche, RuleSetHash, ClaimLevel, CandidateSet, TargetMerchantSet, EligibleMerchant, ProofOfMatch, and RewardCommitment campaign semantics.
- Adds experimental candidate schemas for CampaignEpoch, CampaignAmendment, and FundingTranche.
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
