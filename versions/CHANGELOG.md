# Changelog

This repository is being prepared for its **first public release**. Earlier internal iterations existed, but version numbers have been reset for the public SemVer track.

## Unreleased governance update

- Requires every spec or requirements change to classify business policy,
  protocol artifacts, offchain state and computation, optional onchain
  commitment or execution, verification/dispute handling, and maturity.
- Adds a pull-request template and CI boundary check. This governance update
  does not change protocol object semantics or the global `protocolVersion`.

## Unreleased Campaign Experiment publication draft

- Publishes the cross-vertical Campaign Experiment Profile at explicit `publication-draft` maturity, anchored to the adopted engineering source at `crinkl-protocol` commit `40dc0e8c23826a48d579cae1c30ca0dbefba13ef`.
- Defines the protocol/business split, exact artifact relationships, pre-exposure exclusive assignment contract, assignment/exposure/outcome/incrementality boundaries, CPG/restaurant acceptance matrix, runtime gate, and public release gate.
- Disambiguates the earlier public experimental `CampaignEpochV1` candidate from the exact signed adopted engineering object and states that legacy `claimLevel = "INCREMENTAL"` does not make an individual receipt or conversion causal.
- Adds no schema bytes or public conformance vectors, does not change the global `protocolVersion`, is not released `v1.0.0-rc.2` conformance, and declares no runtime or production availability.

## v1.0.0-rc.3 (2026-07-17)

- Publishes sponsor-neutral direct buyer-reward semantics at explicit `released` maturity, anchored to adopted engineering `crinkl-protocol` commit `8c641f57201c75bac12819a0f903ae6105c7f3c3`.
- Publishes a self-contained six-artifact byte-pinned profile package containing the strict direct buyer-reward schema, adopted-engineering Epoch dependency, vector, generator, checker and release-reconciliation contract.
- Adds `campaign.directBuyerReward.profileV1` to conformance suite version `2` with an executable manifest-bound verifier while leaving the default Crinkl Platform binding `protocolVersion` at `1.0.0-rc.2` and preserving the profile objects' signed `1.0.0-rc.1` bytes.
- Keeps affiliate link/coupon use and commission separate from buyer reward qualification, and keeps target merchant, payer/funder, sponsor and representation as separate roles.
- Keeps Campaign product lifecycle and immutable Epoch validity separate; this reward profile does not add a bundled lifecycle-stop artifact.
- Makes repository release, conformance-suite and embedded wire versions independently machine-readable in `versions/release.json`; source branches are explicitly prohibited as release authority.
- Preserves both incompatible Campaign Epoch schema byte sets, requires the adopted schema by exact ID and SHA-256, excludes the legacy experimental schema from the profile, and prohibits title-only resolution. It does not cut the target release or change the current global `protocolVersion`, released conformance manifest, runtime, validator-network, funding, escrow, settlement, chain, deployment or production availability.
- Separates protocol publication from Campaign launch: runtime and distributed validator admission remain later launch requirements rather than circular prerequisites for publishing the profile.
- The release status is `RELEASED`; relying consumers authenticate the immutable `v1.0.0-rc.3` tag and exact release-manifest digest.

## v1.0.0-rc.2 admission update (2026-07-06)

- Defines the Verification Service and Proof Validator roles and the division of power between private verification and public admission: the party that reads evidence cannot unilaterally create network acceptance, and the parties that create acceptance never read evidence.
- Adds `02-proof-lifecycle/admission.md` with the Attested/Admitted states and the v1 statement-coverage admission mechanism: a Spend Attestation is admitted when a validator-finalized statement's committed leaf set covers its canonical head.
- Adds the proof-validator finality-certificate trust root with bounded scope: quorum re-verification of deterministic statements, never ground truth of receipts.
- Adds glossary terms: Verification Service, Proof Validator, Selected Committee, Finality Certificate, Admission.
- Reserves verification-service registry, adversarial audit probes, and disbelief status for a future version.
- Does not change the global `protocolVersion`; validator-network artifacts carry their own `schemaVersion` values.

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
