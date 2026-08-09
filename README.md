# Crinkl Protocol

> Crinkl turns verified commerce evidence into portable, privately usable
> proof through four concepts.
>
> - **Spend Attestation** — an issuer's signed statement that spend was verified under a named policy.
> - **Spend Attestation Token** — its identity-minimized portable representation.
> - **Verification Policy** — the content-addressed rules defining what "verified" means.
> - **Spend Predicate** — a reusable rule that evaluates one or more Spend Attestations without changing them.
>
> A successful predicate evaluation produces a **Proof of Match** that
> campaigns, rewards, analytics and agents consume.

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
8. Spend Predicates and CampaignEpochs may evaluate one or more attestations.
9. Valid ProofOfMatch results may trigger rewards, settlement, campaigns, analytics, or agent responses.

## What Crinkl Does Not Prove

Crinkl Core does not define checkout, payment authorization, card processing, merchant order management, ad delivery, identity graph construction, behavioral targeting, loyalty program ownership, brand campaign strategy, or agent purchasing.

Crinkl may support those systems downstream by providing verified spend proof.

## Core Lifecycle

The spec follows this dependency order:

```text
Evidence before claims.
Claims before attestations.
Attestations before predicates.
Predicates before rewards.
Rewards before campaigns.
Campaigns before agents and markets.
```

Core protocol validity does not depend on campaigns, rewards, Solana, ZK, MCP, REST, agents, ads, brand budgets, or promotion logic.

## Protocol Objects

Complete inventory of thirteen protocol-level artifacts, spanning all three
layers (Core, Portability, Applications); anything not on this list is prose
at the protocol level (defined in the [glossary](08-governance/glossary.md),
not a schema or a table row here) — see the note below the table for
dependent artifacts that profiles and extensions define with their own
schemas. `VerificationPolicy`, `IssuerRegistrySnapshot`, `AttestationStatus`,
and `SpendPredicate` are untagged candidate schemas (object-model board steps
OM4/OM4r). They sit below the release-candidate line, are not required for
Core validity, and do not add fields to `SpendAttestation`,
`SpendAttestationToken`, or `SpendAttestationCredential`.

| Object | Layer | Purpose |
|---|---|---|
| `SpendStreamEvent` | Record | The serialized append-only atom. |
| `SpendAttestation` | Record | Issuer's signed statement about the stream head, under a named policy. |
| [`VerificationPolicy`](01-core/schemas/verification_policy_v1.schema.json) | Trust | Content-addressed rules defining what "verified" means. (untagged candidate, OM4r) |
| [`IssuerRegistrySnapshot`](01-core/schemas/issuer_registry_snapshot_v1.schema.json) | Trust | Immutable authority set at a point in time, including retired keys and validity windows. (untagged candidate, OM4r) |
| [`AttestationStatus`](01-core/schemas/attestation_status_v1.schema.json) | Trust | Revocation and supersession. (untagged candidate, OM4r) |
| `SpendAttestationToken` | Portability | Native identity-minimized form. |
| `SpendAttestationCredential` | Portability | W3C VC 2.0 serialization. |
| [`SpendPredicate`](04-condition-layer/schemas/spend_predicate_v1.schema.json) | Rule | Reusable rule over one or more Spend Attestations. (untagged candidate, OM4r) |
| `ProofOfMatch` | Rule | Result of evaluating a predicate. |
| `CampaignEpoch` | Campaign | Immutable, append-only funded rule window. |
| `FinalityCertificate` | Finality/Settlement | Quorum acceptance of a specific statement. |
| `RewardCommitment` | Finality/Settlement | Recipient-scoped inclusion. |
| `CampaignSettlementCommitment` | Finality/Settlement | Campaign-scoped settlement. |

These thirteen are the protocol-level artifact inventory. Serialization
profiles and extensions define dependent artifacts documented in their own
homes — the W3C representation's `W3CIssuerKeyHistoryV1` and Bitstring
Status List credential, and extension artifacts such as
`MerchantClaimAttestationV1` in [`06-extensions/`](06-extensions/) — which do
not appear in this table.

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
| Spend Predicate rules and CampaignEpochs | [`04-condition-layer/`](04-condition-layer/) |
| Reward and settlement | [`05-reward-and-settlement/`](05-reward-and-settlement/) including [`campaign-settlement-gcd.md`](05-reward-and-settlement/campaign-settlement-gcd.md) |
| ZK, Campaign experiments, direct buyer rewards, merchant authority, agent, REST/MCP, Solana, offer delivery | [`06-extensions/`](06-extensions/) including the public-draft [`campaign-experiment-profile.md`](06-extensions/campaign-experiment-profile.md), released [`campaign-direct-buyer-reward-profile.md`](06-extensions/campaign-direct-buyer-reward-profile.md), [`merchant-authority.md`](06-extensions/merchant-authority.md), [`zk-external-verifier-integration-guide.md`](06-extensions/zk-external-verifier-integration-guide.md), and [`solana-campaign-settlement-binding.md`](06-extensions/solana-campaign-settlement-binding.md) |
| Conformance | [`07-conformance/`](07-conformance/) |
| ZK beta release checklist | [`08-governance/zk-beta-release-checklist.md`](08-governance/zk-beta-release-checklist.md) |
| ZK beta audit package | [`08-governance/zk-beta-audit-package.md`](08-governance/zk-beta-audit-package.md) |
| Governance | [`08-governance/`](08-governance/), including the required [`protocol/business/onchain boundary`](08-governance/protocol-business-boundary.md) for spec and requirements changes |

## Repository Structure

| Directory | Role |
|---|---|
| [`00-purpose/`](00-purpose/) | Purpose, non-goals, and threat model. |
| [`01-core/`](01-core/) | Evidence, Spend Events, verification states, canonicalization, signatures, privacy boundaries. |
| [`02-proof-lifecycle/`](02-proof-lifecycle/) | Ingestion, normalization, soft/hard verification, correction, attestation issuance. |
| [`03-portability/`](03-portability/) | Spend Attestation Tokens, verifier requirements, identity exclusion, replay/auditability. |
| [`04-condition-layer/`](04-condition-layer/) | Spend Predicates, predicate evaluation, proof of match, campaign commitment. |
| [`05-reward-and-settlement/`](05-reward-and-settlement/) | Reward Commitment, GMV, distribution, settlement bindings. |
| [`06-extensions/`](06-extensions/) | Optional ZK, merchant authority, agent query, transport, Solana, offer-delivery, and registry profiles. |
| [`07-conformance/`](07-conformance/) | Vectors, verifier test suite, compatibility notes. |
| [`08-governance/`](08-governance/) | Versioning, change process, authority hierarchy, and shared glossary. |
| [`schemas/experimental/`](schemas/experimental/) | Candidate non-core extension schemas; not required for Core Spend Attestation validity. |

## Release and source state

`v1.0.0-rc.4` is the latest released public package. Current public repository
source candidate: **v1.0.0-rc.7** (`RELEASE_CANDIDATE_NOT_PUBLISHED`),
conformance suite 4; it is unreviewed, unpublished, not publishable, and does
not inherit rc.5 review. Its current machine-readable release manifest is
[`versions/release.json`](versions/release.json), and its candidate controls
are in [`versions/v1.0.0-rc.7/finalization.json`](versions/v1.0.0-rc.7/finalization.json).
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
python3 07-conformance/profiles/campaign-direct-buyer-reward-v1/scripts/check_campaign_direct_reward_profile_vectors.py
node 07-conformance/profiles/spend-token-v2-holder-binding/scripts/check_holder_binding_vectors.mjs
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
[`08-governance/refactor-record.md`](08-governance/refactor-record.md).
