# Changelog

`v1.0.0-rc.7` is the latest released public package. Current public repository
release: **1.0.0-rc.7** (`RELEASED`), conformance suite 4; it does not promote
candidate profiles or activate runtime, validator, authority, deployment, or
production behavior.
The following preserved
rc.5 transition text applies only to public-spec commit
`81237937833ab32e5ce92d3b5ceed72854baecef` / tree
`9121bdfbfc428f73557e993f1bd6e295ba733a12`:

The historical exact reviewed source candidate is **v1.0.0-rc.5**, an
unpublished SemVer prerelease. Repository release maturity is separate from
each document's frontmatter maturity. The immutable `v1.0.0-rc.4` tag remains
the prior released package; no stable successor release is declared.

## Unreleased — Campaign layer alignment with adopted engineering (2026-09-02)

Documentation and experimental-schema changes only (public-spec #52, #53, #54,
#55); no released package, manifest, tag, runtime, validator-network,
deployment or production behavior changes.

- Adopts finalized Solana acceptance as the Campaign proof path: publishes
  Procedure Profile V3 (`campaign_proof_of_match_procedure_profile_v3`, content
  reference `sha256:73306e3b904dd05fda008da1ca6c2858d545f3dd9503366836d6833da7aee3ec`),
  `SolanaProofEvidenceV1` and `CampaignOutcomeV2` as unreleased experimental
  mirrors of `crinkl-protocol@156d63c37d4d4b9a31287e86d7623afdbe642997`; every
  Campaign flow now ends at `ProofOfMatch -> finalized Solana ACCEPT ->
  CampaignOutcome`. Validator quorum certification (`ValidatorCertificateV1`,
  Procedure Profiles V1 and V2) is retained as a historical acceptance
  candidate and is not used for Campaign proof acceptance.
- Publishes the `ConditionV1` rule grammar, six buyer-state statements,
  evaluation contexts and evaluation policies as unreleased experimental
  mirrors of the same engineering commit; replaces the Spend Predicate
  placeholder and repairs the offer-delivery primitive pointer.
- Adds the Campaign template catalog (every template as primitives,
  parameters, purpose slot, executing family and maturity; absence templates
  `BLOCKED — COVERAGE`) and the Campaign compiler procedure (definition
  identity `conditionId(ConditionV1)`, exact family selection, parameter
  versus family, fail-closed cases).

## v1.0.0-rc.5 release candidate (not published)

It does not classify any later tree; any later tree remains unassigned unless a
new exact candidate identity and independent review record it.

- Publishes a source-only, byte-pinned candidate bundle for the optional W3C
  VC 2.0 Spend Attestation wire form, anchored to adopted `crinkl-protocol`
  commit `ae6382f1ed11b88f9bbfdcc4ef12119647cc7698`.
- Supports opt-in dual issuance alongside independently verifiable native Spend
  Attestation Tokens while preserving native token bytes, embedded wire
  versions, and the immutable released `v1.0.0-rc.4` manifest and tag.
- Pins applicable official self-cell evidence at 32 passing rows and 8 pending
  profile-optional or upstream-skipped rows; complete official-suite
  conformance, peer interoperability, generic VC/VP APIs, endpoint operation,
  runtime, release, and production remain unclaimed. The rc.5 candidate adds
  the fixture harness as an executable manifest-bound suite-version-3 kind;
  this does not promote the W3C profile beyond candidate maturity.

## Schema identifier erratum candidate (not published)

- Adds a [released schema identifier collision erratum](errata/released-schema-identifier-collisions-v1.md)
  as a source candidate. It preserves immutable released identities and bytes,
  pins the corrected 22-row D4 receipt, and names adopted-source D3.1
  successors without making any migration, public release, runtime, or
  deployment claim.

## Reward-commitment rc.7 publication defect erratum candidate (not published)

- Adds an [immutable rc.7 publication-defect erratum](errata/reward-commitment-rc7-publication-defect-v1.md) that pins the released tag, tree, affected paths, and exact byte digests.
- Adds the suite-5 successor identity `token.spendAttestation.portableV1.fromSpendStream.v2`; it preserves Spend-token schema and wire identities while making issuer-scoped supersession executable.
- Pins adopted candidate `crinkl-protocol@4a9dff4002a4016638e213d2f6dce71c4d371515` as source evidence only. No public release, runtime consumption, deployment, or authority activation follows from this candidate.

## Unreleased governance update

- Requires every spec or requirements change to classify business policy,
  protocol artifacts, offchain state and computation, optional onchain
  commitment or execution, verification/dispute handling, and maturity.
- Adds a pull-request template and CI boundary check. This governance update
  does not change protocol object semantics or the global `protocolVersion`.

## v1.0.0-rc.4 (2026-07-31)

- Publishes `SpendAttestationTokenV2` with an optional signed
  `holderBinding` commitment and identity-excluded fresh challenge-response
  holder-control proof.
- Publishes byte-identical adopted-engineering test vectors for valid,
  wrong-key, wrong-signature, changed-context, expired, replayed, and
  absent-binding cases.
- Scopes Spend-token supersession by `(issuedBy, spendId)` and requires
  schema-v2 successors to preserve an existing holder binding within that
  issuer scope.
- Keeps the embedded token `protocolVersion` at `1.0.0-rc.1`, the default
  Platform binding at `1.0.0-rc.2`, and conformance suite version at `2`.
- Adds no wallet, legal-identity, qualification, reward, settlement, runtime,
  deployment, Android, or native claim.

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
