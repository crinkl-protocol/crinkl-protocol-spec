# Crinkl Protocol

Crinkl Protocol defines how real-world commerce evidence becomes signed, privacy-preserving spend proof.

A spend attestation proves that a purchase event was observed, normalized, verified, and signed by an authorized verifier.

The protocol is designed so that campaigns, reward systems, analytics tools, agents, and settlement layers can verify commerce facts without requiring raw receipt access or user identity.

[![Version](https://img.shields.io/badge/version-v1.0.0--rc.2-blue)](versions/CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![CI](https://github.com/crinkl-protocol/crinkl-protocol-spec/actions/workflows/drift-check.yml/badge.svg)](https://github.com/crinkl-protocol/crinkl-protocol-spec/actions/workflows/drift-check.yml)

## What Crinkl Proves

Crinkl proves that commerce evidence advanced through a defined proof lifecycle:

1. Evidence is submitted.
2. Evidence is normalized into a Spend Event.
3. The Spend Event receives a verification state.
4. A hard-verified Spend Event may produce a Spend Attestation.
5. The Spend Attestation may be packaged as a Spend Attestation Token.
6. Selected proof validators may admit attestations to the shared record by finalizing statements over committed attestation sets.
7. External systems may verify the attestation.
8. Conditions and CampaignEpochs may evaluate one or more attestations.
9. Valid ProofOfMatch results may trigger rewards, settlement, campaigns, analytics, or agent responses.

## What Crinkl Does Not Prove

Crinkl Core does not define checkout, payment authorization, card processing, merchant order management, ad delivery, identity graph construction, behavioral targeting, loyalty program ownership, brand campaign strategy, or agent purchasing.

Crinkl may support those systems downstream by providing verified spend proof.

## Core Lifecycle

The spec follows this dependency order:

```text
Evidence before claims.
Claims before attestations.
Attestations before conditions.
Conditions before rewards.
Rewards before campaigns.
Campaigns before agents and markets.
```

Core protocol validity does not depend on campaigns, rewards, Solana, ZK, MCP, REST, agents, ads, brand budgets, or promotion logic.

## Core Objects

| Object | Layer | Purpose |
|---|---|---|
| Commerce Evidence | Purpose/Core | Raw or semi-structured input that may support a spend claim. |
| Spend Event | Core | Normalized representation of a purchase event. |
| Verification State | Core/Lifecycle | Current confidence and status for a Spend Event. |
| Spend Attestation | Core | Signed claim that a Spend Event was verified according to Crinkl rules. |
| Spend Attestation Token | Portability | Portable representation of a Spend Attestation for external verification. |
| Condition | Condition Layer | Rule over one or more Spend Attestations. |
| CampaignEpoch | Condition Layer | Immutable, append-only funded rule window for campaign eligibility. |
| Proof of Match | Condition Layer | Result of evaluating attestations against a condition. |
| Reward Commitment | Reward/Settlement | Downstream accounting or promise based on valid proof of match. |
| Finality Certificate | Lifecycle | Quorum evidence that selected proof validators independently re-verified and co-signed a deterministic statement, admitting the covered attestations to the shared record. |
| Merchant Claim Attestation | Extension | Optional authority proof over store identity for official merchant actions. |

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
| Condition rules and CampaignEpochs | [`04-condition-layer/`](04-condition-layer/) |
| Reward and settlement | [`05-reward-and-settlement/`](05-reward-and-settlement/) including [`campaign-settlement-gcd.md`](05-reward-and-settlement/campaign-settlement-gcd.md) |
| ZK, merchant authority, agent, REST/MCP, Solana, offer delivery | [`06-extensions/`](06-extensions/) including [`merchant-authority.md`](06-extensions/merchant-authority.md), [`zk-external-verifier-integration-guide.md`](06-extensions/zk-external-verifier-integration-guide.md), and [`solana-campaign-settlement-binding.md`](06-extensions/solana-campaign-settlement-binding.md) |
| Conformance | [`07-conformance/`](07-conformance/) |
| ZK beta release checklist | [`08-governance/zk-beta-release-checklist.md`](08-governance/zk-beta-release-checklist.md) |
| ZK beta audit package | [`08-governance/zk-beta-audit-package.md`](08-governance/zk-beta-audit-package.md) |
| Governance | [`08-governance/`](08-governance/) |

## Repository Structure

| Directory | Role |
|---|---|
| [`00-purpose/`](00-purpose/) | Purpose, non-goals, and threat model. |
| [`01-core/`](01-core/) | Evidence, Spend Events, verification states, canonicalization, signatures, privacy boundaries. |
| [`02-proof-lifecycle/`](02-proof-lifecycle/) | Ingestion, normalization, soft/hard verification, correction, attestation issuance. |
| [`03-portability/`](03-portability/) | Spend Attestation Tokens, verifier requirements, identity exclusion, replay/auditability. |
| [`04-condition-layer/`](04-condition-layer/) | Conditions, condition evaluation, proof of match, campaign commitment. |
| [`05-reward-and-settlement/`](05-reward-and-settlement/) | Reward Commitment, GMV, distribution, settlement bindings. |
| [`06-extensions/`](06-extensions/) | Optional ZK, merchant authority, agent query, transport, Solana, offer-delivery, and registry profiles. |
| [`07-conformance/`](07-conformance/) | Vectors, verifier test suite, compatibility notes. |
| [`08-governance/`](08-governance/) | Versioning, change process, authority hierarchy, and shared glossary. |
| [`schemas/experimental/`](schemas/experimental/) | Candidate non-core extension schemas; not required for Core Spend Attestation validity. |

## Current Version

**v1.0.0-rc.2** — see [`versions/CHANGELOG.md`](versions/CHANGELOG.md).
Planned stable release tag: **v1.0.0**.

## Verification

```bash
python3 scripts/check_drift.py
node scripts/verify_conformance.mjs
```

PDF export:

```bash
./scripts/export_protocol_pdf.sh
```

Reform notes for this lifecycle refactor are in [`REFORM_NOTES.md`](REFORM_NOTES.md).
