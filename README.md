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

See the [full object inventory](#core-objects) for every artifact.

[![Version](https://img.shields.io/badge/version-v1.0.0--rc.5-blue)](versions/CHANGELOG.md)
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

## Core Objects

Complete inventory of thirteen artifacts; anything not on this list is prose
(defined in the [glossary](08-governance/glossary.md), not a schema or a table
row). Four artifacts are named but not yet schema-defined; they carry an
explicit `(schema pending, OM4)` marker below.

| Object | Layer | Purpose |
|---|---|---|
| `SpendStreamEvent` | Record | The serialized append-only atom. |
| `SpendAttestation` | Record | Issuer's signed statement about the stream head, under a named policy. |
| `VerificationPolicy` | Trust | Content-addressed rules defining what "verified" means. (schema pending, OM4) |
| `IssuerRegistrySnapshot` | Trust | Immutable authority set at a point in time, including retired keys and validity windows. (schema pending, OM4) |
| `AttestationStatus` | Trust | Revocation and supersession. (schema pending, OM4) |
| `SpendAttestationToken` | Portability | Native identity-minimized form. |
| `SpendAttestationCredential` | Portability | W3C VC 2.0 serialization. |
| `SpendPredicate` | Rule | Reusable rule over one or more Spend Attestations. (schema pending, OM4) |
| `ProofOfMatch` | Rule | Result of evaluating a predicate. |
| `CampaignEpoch` | Campaign | Immutable, append-only funded rule window. |
| `FinalityCertificate` | Finality/Settlement | Quorum acceptance of a specific statement. |
| `RewardCommitment` | Finality/Settlement | Recipient-scoped inclusion. |
| `CampaignSettlementCommitment` | Finality/Settlement | Campaign-scoped settlement. |

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

## Current Version

**v1.0.0-rc.5** release candidate source — not yet published. See
[`versions/release.json`](versions/release.json) and
[`versions/CHANGELOG.md`](versions/CHANGELOG.md). The exact, machine-checkable
release transition and rollback rules are in
[`versions/v1.0.0-rc.5/finalization.json`](versions/v1.0.0-rc.5/finalization.json).
This is an unpublished SemVer prerelease candidate, not a stable `v1.0.0`
release. The immutable released `v1.0.0-rc.4` tag remains available for
historical verification.
Each document's frontmatter `status` states that document's maturity separately
and does not change the repository release status. A successor release identity
is selected as `v1.0.0-rc.5`. P4.4 and P9 remain blockers.

## Verification

```bash
python3 scripts/check_drift.py
node scripts/verify_conformance.mjs
python3 07-conformance/profiles/campaign-direct-buyer-reward-v1/scripts/check_campaign_direct_reward_profile_vectors.py
node 07-conformance/profiles/spend-token-v2-holder-binding/scripts/check_holder_binding_vectors.mjs
```

Verify the rc.5 candidate transition locally:

```bash
python3 scripts/check_successor_release_finalization.py --mode candidate
```

PDF export:

```bash
./scripts/export_protocol_pdf.sh
```

The governed record for this lifecycle refactor is in
[`08-governance/refactor-record.md`](08-governance/refactor-record.md).
