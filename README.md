# Crinkl Protocol

> Crinkl turns verified commerce evidence into portable, privately usable
> proof through four concepts.
>
> - **Spend Attestation** — an issuer's signed statement that spend was verified under a named policy.
> - **Spend Attestation Token** — its identity-minimized portable representation.
> - **Verification Policy** — the content-addressed rules defining what "verified" means.
> - **Spend Predicate** — a reusable rule that evaluates one or more Spend Attestations without changing them.
>
> A Campaign binds an exact rule in a signed **Campaign Epoch**. A successful
> private evaluation produces a purpose-scoped **Proof of Match**; Campaign
> Outcomes may then create a **Reward Obligation** under the Epoch's committed
> economic and admission policy.

See the [full object inventory](#protocol-objects) for every artifact.

[![Version](https://img.shields.io/badge/version-v1.0.0--rc.7-blue)](versions/CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![CI](https://github.com/crinkl-protocol/crinkl-protocol-spec/actions/workflows/drift-check.yml/badge.svg)](https://github.com/crinkl-protocol/crinkl-protocol-spec/actions/workflows/drift-check.yml)

## Verify the Candidate Native V1 Fixture

From a clean checkout, use the repository-shipped verifier and vector:

```bash
node scripts/verify_conformance.mjs \
  --require-kind token.spendAttestation.portableV1.fromSpendStream
```

This proves consistency among the repository fixture's native V1 canonical
bytes, token hash, Ed25519 signature, and declared public key without private
infrastructure or network access. It does not prove issuer authorization,
currentness, purchase acceptance, or release-tag authenticity, and it does not
verify or activate a W3C credential profile.

## What Crinkl Proves

Crinkl proves that commerce evidence advanced through a defined proof lifecycle:

1. Evidence is submitted.
2. Evidence is normalized into a Spend Event.
3. The Spend Event receives a verification state.
4. A hard-verified Spend Event may produce a Spend Attestation.
5. The Spend Attestation may be packaged as a Spend Attestation Token.
6. Selected proof validators may admit attestations to the shared record by finalizing statements over committed attestation sets.
7. External systems may verify the attestation.
8. A signed CampaignEpoch may commit audience, conversion, assignment,
   economic-admission, reward, timing, reuse, and dispute policy references.
9. A purpose-scoped ProofOfMatch may prove that one or more Spend Tokens satisfy
   the Epoch's audience or conversion rule.
10. A Campaign runtime composes accepted proofs with optional assignment,
    exposure, and economic admission into a CampaignOutcome.
11. An eligible admitted Outcome may deterministically create a
    RewardObligation, later resolved by a SettlementRecord.

## What Crinkl Does Not Prove

Crinkl Core does not define checkout, payment authorization, card processing, merchant order management, ad delivery, identity graph construction, behavioral targeting, loyalty program ownership, brand campaign strategy, or agent purchasing.

Crinkl may support those systems downstream by providing verified spend proof.

## Core Lifecycle

The spec follows this dependency order:

```text
Evidence before claims.
Claims before attestations.
Attestations before predicates and Campaign proofs.
Campaign rules before Campaign proofs.
Accepted proofs before Campaign outcomes.
Eligible admitted outcomes before reward obligations.
Reward obligations before settlement records.
Protocol facts before agents, reports, and markets.
```

Core protocol validity does not depend on campaigns, rewards, Solana, ZK, MCP, REST, agents, ads, brand budgets, or promotion logic.

## Protocol Objects

The target inventory contains fifteen protocol-level artifact families across
Core, Portability, and Applications. Campaign vNext entries are additive
`SPECIFIED_NOT_IMPLEMENTED` candidates outside every released manifest.
Anything not listed is prose, a role, state, deterministic procedure, or
off-protocol function unless an optional profile gives it a separate schema.
`VerificationPolicy`, `IssuerRegistrySnapshot`, `AttestationStatus`, and
`SpendPredicate` remain untagged candidate schemas (object-model board steps
OM4/OM4r). None of this adds fields to `SpendAttestation`,
`SpendAttestationToken`, or `SpendAttestationCredential`.

| Object | Layer | Purpose |
|---|---|---|
| `SpendStreamEvent` | Record | The serialized append-only atom. |
| `SpendAttestation` | Record | Issuer's signed statement about the stream head, under a named policy. |
| [`VerificationPolicy`](protocol/core/schemas/verification_policy_v1.schema.json) | Trust | Content-addressed rules defining what "verified" means. (untagged candidate, OM4r) |
| [`IssuerRegistrySnapshot`](protocol/core/schemas/issuer_registry_snapshot_v1.schema.json) | Trust | Immutable authority set at a point in time, including retired keys and validity windows. (untagged candidate, OM4r) |
| [`AttestationStatus`](protocol/core/schemas/attestation_status_v1.schema.json) | Trust | Revocation and supersession. (untagged candidate, OM4r) |
| `SpendAttestationToken` | Portability | Native identity-minimized form. |
| `SpendAttestationCredential` | Portability | W3C VC 2.0 serialization. |
| [`SpendPredicate`](protocol/applications/conditions/schemas/spend_predicate_v1.schema.json) | Rule | Reusable rule over one or more Spend Attestations. (untagged candidate, OM4r) |
| [`CampaignEpoch`](protocol/applications/campaigns/README.md#32-campaignepoch) | Campaign | Immutable signed Campaign rules and economic terms; reduced-spine V2 candidate. |
| [`ProofOfMatch`](protocol/applications/conditions/proof-of-match.md) | Proof | Purpose-scoped ZK statement over authenticated commerce facts; target V1 candidate. |
| [`ValidatorCertificate`](protocol/applications/campaigns/README.md#34-validatorcertificate) | Proof acceptance | Quorum acceptance of one exact proof subject under one exact procedure; target V1 candidate. |
| [`AssignmentRecord`](protocol/applications/campaigns/README.md#35-assignmentrecord) | Experiment | Optional portable deterministic arm assignment when an independent consumer/dispute boundary requires it; target V1 candidate. |
| [`CampaignOutcome`](protocol/applications/campaigns/README.md#38-campaignoutcome) | Campaign | Narrow composition of accepted matches, optional assignment/exposure/admission, and deterministic reward decision; target V1 candidate. |
| [`RewardObligation`](protocol/applications/campaigns/README.md#39-rewardobligation) | Economics | Recipient-scoped liability created by an eligible admitted Outcome; target V1 candidate. |
| [`SettlementRecord`](protocol/applications/campaigns/README.md#310-settlementrecord) | Economics | Evidence that an Obligation was paid, reversed, expired, disputed, cancelled, or otherwise resolved; target V1 candidate. |

These fifteen are the target protocol-level families. Exposure and economic
admission remain application/ledger state unless a named cross-system profile
proves a need for a portable artifact; `CampaignReport` is derived output.
Discarded Campaign drafts have no aliases or adapters in the living
specification. Exact source and implementation evidence is recorded in the
[`Campaign evidence inventory`](governance/campaign-architecture-evidence.md).

## Privacy Boundary

Internal Crinkl processing may use wallet-scoped or session-scoped references for replay, routing, abuse controls, and reward handling.

Portable spend proofs must not require user identity, raw receipt access, private wallet lookup, app-user lookup, or cross-context behavioral profiles. The protocol is identity-minimized and identity-excluded from portable proofs by default; it does not claim full anonymity.

## Verification and Portability

Portable verification depends on canonical bytes, RFC 8785 serialization, SHA-256 hashes, Ed25519 signatures, issuer authority, supported versions, and included proof material.

A portable Spend Attestation Token must exclude raw receipt images and must not require user identity. Deep audit may use event fragments or audit bundles, but those are not required for baseline portable verification.

## Optional Profiles and Extensions

Downstream layers consume spend proof; they do not define it.

| Layer | Documents |
|---|---|
| Campaign architecture and V1 schemas | [`protocol/applications/campaigns/`](protocol/applications/campaigns/) |
| Spend Predicate rules and ProofOfMatch | [`protocol/applications/conditions/`](protocol/applications/conditions/) |
| Reward and settlement | [`protocol/applications/economics/`](protocol/applications/economics/); canonical Campaign liability and resolution are defined by the Campaign architecture |
| ZK, merchant authority, agent, REST/MCP, Solana, and offer delivery | [`protocol/extensions/`](protocol/extensions/) including [`merchant-authority.md`](protocol/extensions/merchant-authority.md) and [`zk-external-verifier-integration-guide.md`](protocol/extensions/zk-external-verifier-integration-guide.md) |
| Conformance | [`conformance/`](conformance/) |
| ZK beta release checklist | [`governance/zk-beta-release-checklist.md`](governance/zk-beta-release-checklist.md) |
| ZK beta audit package | [`governance/zk-beta-audit-package.md`](governance/zk-beta-audit-package.md) |
| Governance | [`governance/`](governance/), including the required [`protocol/business/onchain boundary`](governance/protocol-business-boundary.md) for spec and requirements changes |

## Repository Structure

| Directory | Role |
|---|---|
| [`protocol/purpose/`](protocol/purpose/) | Purpose, non-goals, and threat model. |
| [`protocol/core/`](protocol/core/) | Evidence, Spend Events, verification states, canonicalization, signatures, privacy boundaries. |
| [`protocol/core/`](protocol/core/) | Ingestion, normalization, soft/hard verification, correction, attestation issuance. |
| [`protocol/portability/`](protocol/portability/) | Spend Attestation Tokens, verifier requirements, identity exclusion, replay/auditability. |
| [`protocol/applications/campaigns/`](protocol/applications/campaigns/) | Canonical Campaign architecture, authority boundaries, lifecycle, and first V1 schemas. |
| [`protocol/applications/conditions/`](protocol/applications/conditions/) | Spend Predicates, evaluation, and ProofOfMatch. |
| [`protocol/applications/economics/`](protocol/applications/economics/) | GMV, distribution, and general settlement-binding profiles; Campaign liability and resolution live under the Campaign architecture. |
| [`protocol/extensions/`](protocol/extensions/) | Optional ZK, merchant authority, agent query, transport, Solana, offer-delivery, and registry profiles. |
| [`conformance/`](conformance/) | Vectors, verifier test suite, compatibility notes. |
| [`governance/`](governance/) | Versioning, change process, authority hierarchy, and shared glossary. |
| [`schemas/experimental/`](schemas/experimental/) | Candidate non-core extension schemas; not required for Core Spend Attestation validity. |

## Release and source state

`v1.0.0-rc.7` is the latest released public package. Current public repository
source candidate: **v1.0.0-rc.8** (`RELEASE_CANDIDATE_NOT_PUBLISHED`),
conformance suite 5; it is unreviewed, unpublished, not publishable, and does
not inherit rc.5 review. The candidate corrects
the rc.7 reward-linkage and Spend-supersession publication defect without
changing the rc.1/rc.2 wire support set, any Spend Token schema, or runtime,
validator, authority, and production state. Its machine-readable candidate
manifest is [`versions/release.json`](versions/release.json), and its source
controls are in
[`versions/v1.0.0-rc.8/finalization.json`](versions/v1.0.0-rc.8/finalization.json).
The immutable rc.7 release remains available at tag `v1.0.0-rc.7` with its
historical controls in
[`versions/v1.0.0-rc.7/finalization.json`](versions/v1.0.0-rc.7/finalization.json).
The following preserved
rc.5 transition text applies only to public-spec commit
`81237937833ab32e5ce92d3b5ceed72854baecef` / tree
`9121bdfbfc428f73557e993f1bd6e295ba733a12`:

**v1.0.0-rc.5** historical exact reviewed source candidate — not published.
Its historical transition controls are in
[`versions/v1.0.0-rc.5/finalization.json`](versions/v1.0.0-rc.5/finalization.json)
and [`versions/v1.0.0-rc.5/snapshot.md`](versions/v1.0.0-rc.5/snapshot.md).
This is an unpublished SemVer prerelease candidate, not a stable `v1.0.0`
release. The immutable released `v1.0.0-rc.4` tag remains available for
historical verification.
P4.4 and P9 remain blockers. This is rc.5 plan text for that exact reviewed
candidate.
It does not classify any later tree; any later tree remains unassigned unless a
new exact candidate identity and independent review record it.
Each document's frontmatter `status` states that document's maturity separately
and does not change the repository release status. A successor release identity
is selected only by a separately reviewed candidate identity.

## Verification

```bash
python3 scripts/check_drift.py
node scripts/verify_conformance.mjs
python3 conformance/profiles/campaign-direct-buyer-reward-v1/scripts/check_campaign_direct_reward_profile_vectors.py
node conformance/profiles/spend-token-v2-holder-binding/scripts/check_holder_binding_vectors.mjs
```

Verify the rc.7 candidate transition locally:

```bash
python3 scripts/check_successor_release_finalization.py --mode candidate
```

PDF export:

```bash
./scripts/export_protocol_pdf.sh
```

The governed record for this lifecycle refactor is in
[`governance/refactor-record.md`](governance/refactor-record.md).
