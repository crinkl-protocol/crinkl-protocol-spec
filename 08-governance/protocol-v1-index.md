---
status: draft
layer: governance
version: v1
normative: true
---

# Crinkl Protocol V1

Canonical entrypoint for version 1 of the Crinkl Protocol specification. Each section below is normative unless explicitly marked non-normative.

- [glossary.md](glossary.md) — normative term definitions
- [../00-purpose/what-crinkl-proves.md](../00-purpose/what-crinkl-proves.md) — protocol overview and scope
- [../01-core/spend-attestation.md](../01-core/spend-attestation.md) — core protocol concepts (spend-centric objects, scoped recipients, and ledgers)
- [../03-portability/spend-attestation-token.md](../03-portability/spend-attestation-token.md) — token outputs (attestation + commitments)
- [../01-core/canonicalization.md](../01-core/canonicalization.md) — canonical schema definitions
- [../02-proof-lifecycle/ingestion.md](../02-proof-lifecycle/ingestion.md) — soft and hard verification flows
- [../02-proof-lifecycle/gmv-price-aggregate-v1.md](../02-proof-lifecycle/gmv-price-aggregate-v1.md) — GmvPriceAggregateV1 artifact format, canonicalization, and registry/committee binding
- [../07-conformance/gmv-price-aggregate-verification.md](../07-conformance/gmv-price-aggregate-verification.md) — normative verifier check order and failure-code vocabulary for GmvPriceAggregateV1
- [../01-core/verification-state.md](../01-core/verification-state.md) — attestation and reward lifecycle transitions
- [../01-core/spend-event.md](../01-core/spend-event.md) — event schemas and ordering requirements
- [../05-reward-and-settlement/reward-layer.md](../05-reward-and-settlement/reward-layer.md) — application-layer reward interface (non-protocol)
- [../06-extensions/zk-proof-extension.md](../06-extensions/zk-proof-extension.md) — optional zero-knowledge extension layer
- [../06-extensions/zk-foundation.md](../06-extensions/zk-foundation.md) — minimum viable promo flow (ZK spine)
- [../06-extensions/zk-circuit-catalog.md](../06-extensions/zk-circuit-catalog.md) — mapping from statement types to proof circuits (optional extension)
- [../04-condition-layer/campaign-commitment.md](../04-condition-layer/campaign-commitment.md) — campaign rule composition from finite spend proof primitives (optional extension)
- [../06-extensions/campaign-experiment-profile.md](../06-extensions/campaign-experiment-profile.md) — public publication draft for the adopted engineering cross-vertical experiment profile; not released `v1.0.0-rc.2` conformance and runtime unavailable
- [../06-extensions/campaign-direct-buyer-reward-profile.md](../06-extensions/campaign-direct-buyer-reward-profile.md) — `v1.0.0-rc.3` / conformance suite-2 release candidate for the engineering-candidate sponsor-neutral direct buyer-reward profile; byte-pinned package and executable verifier present, release not published, and runtime unavailable
- [../06-extensions/merchant-authority.md](../06-extensions/merchant-authority.md) — optional merchant claim authority for official merchant actions
- [../06-extensions/offer-delivery-profile.md](../06-extensions/offer-delivery-profile.md) — offer delivery profile + verifier rules (optional extension)
- [../06-extensions/encryption-envelopes.md](../06-extensions/encryption-envelopes.md) — encrypted envelope formats for wallet/brand messages (optional extension)
- [../06-extensions/token-extensions.md](../06-extensions/token-extensions.md) — privacy-first credentials + agent delegation (optional extension)
- [../00-purpose/threat-model.md](../00-purpose/threat-model.md) — protocol security properties and invariants
- [protocol-business-boundary.md](protocol-business-boundary.md) — required protocol/business/offchain/onchain classification for spec and requirements changes
- [change-process.md](change-process.md) — authority, change-control, and CI requirements
- [versioning.md](versioning.md) — governance and upgrade processes
- [refactor-record.md](refactor-record.md) — non-normative proof-lifecycle refactor history and preserved tensions

## Protocol Requirements

**Integrity:** All events MUST include `eventHash` (SHA-256) and `prevHash` (linking to prior event in stream). Events MUST be signed with Ed25519.

**Identity boundary:** Internal spend-stream events MAY be wallet-scoped for issuer replay, routing, abuse controls, and reward handling. Portable Spend Attestation Tokens are separate derived artifacts and SHOULD omit wallet, user, account, and session identifiers for external verification unless recipient binding is explicitly required.

**Serialization:** Canonical JSON per RFC 8785 is REQUIRED. Alternative encodings (e.g., deterministic protobuf) MUST produce byte-identical hashes.
