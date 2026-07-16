# Changelog

This repository is being prepared for its **first public release**. Earlier internal iterations existed, but version numbers have been reset for the public SemVer track.

## Unreleased tokenomics reference publication

- Adds `docs/tokenomics/tokenomics.md`, a non-normative reference narrative of the
  token economy, versioned against the protocol (`protocol: 1.0.0-rc.2 · revision:
  2026-07-16`) and superseding the standalone Tokenomics White Paper series (v1–v8),
  now archived.
- The document defers to `05-reward-and-settlement/` on all normative semantics and
  restates no constants as independent truth; it corrects three standalone-era claims
  to match the spec: parameter governance is the timelocked gatekeeper over
  `c`/`K`/`λ`/`revenue_enabled` (not "no levers"), the density burn is not a buyback,
  and the reward rate is verification-service policy bound by the
  IssuerPolicyCommitment.
- Discloses business-policy commitments (issuer treasury 3-year vest by beta) and
  records forward-looking items (earner reward vesting, verification-service staking,
  CBSA population-gated rewards) at explicit non-commitment maturity.
- Adds no schema bytes, changes no protocol object semantics, and does not change the
  global `protocolVersion`.

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
