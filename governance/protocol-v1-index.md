---
status: draft
layer: governance
version: v1
normative: true
---

# Crinkl Protocol V1

Canonical entrypoint for version 1 of the Crinkl Protocol specification. Each section below is normative unless explicitly marked non-normative.

- [glossary.md](glossary.md) — normative term definitions
- [../protocol/purpose/what-crinkl-proves.md](../protocol/purpose/what-crinkl-proves.md) — protocol overview and scope
- [../protocol/core/spend-attestation.md](../protocol/core/spend-attestation.md) — core protocol concepts (spend-centric objects, scoped recipients, and ledgers)
- [../protocol/portability/spend-attestation-token.md](../protocol/portability/spend-attestation-token.md) — token outputs (attestation + commitments)
- [../protocol/portability/w3c-vc-2.0-binding.md](../protocol/portability/w3c-vc-2.0-binding.md) — candidate optional W3C VC 2.0 Spend Attestation wire form; reviewed only at public-spec rc.5 commit `81237937833ab32e5ce92d3b5ceed72854baecef` / tree `9121bdfbfc428f73557e993f1bd6e295ba733a12`, not released conformance or runtime
- [../protocol/core/canonicalization.md](../protocol/core/canonicalization.md) — canonical schema definitions
- [../protocol/core/ingestion.md](../protocol/core/ingestion.md) — soft and hard verification flows
- [../protocol/core/gmv-price-aggregate-v1.md](../protocol/core/gmv-price-aggregate-v1.md) — GmvPriceAggregateV1 artifact format, canonicalization, and registry/committee binding
- [../conformance/gmv-price-aggregate-verification.md](../conformance/gmv-price-aggregate-verification.md) — normative verifier check order and failure-code vocabulary for GmvPriceAggregateV1
- [../protocol/core/verification-state.md](../protocol/core/verification-state.md) — attestation and reward lifecycle transitions
- [../protocol/core/spend-event.md](../protocol/core/spend-event.md) — event schemas and ordering requirements
- [../protocol/applications/economics/reward-layer.md](../protocol/applications/economics/reward-layer.md) — application-layer reward interface (non-protocol)
- [../protocol/extensions/zk-proof-extension.md](../protocol/extensions/zk-proof-extension.md) — optional zero-knowledge extension layer
- [../protocol/extensions/zk-foundation.md](../protocol/extensions/zk-foundation.md) — minimum viable promo flow (ZK spine)
- [../protocol/extensions/zk-circuit-catalog.md](../protocol/extensions/zk-circuit-catalog.md) — mapping from statement types to proof circuits (optional extension)
- [../protocol/applications/campaigns/README.md](../protocol/applications/campaigns/README.md) — canonical reduced Campaign architecture, authority model, economic-admission boundary, and first V1 schemas (`SPECIFIED_NOT_IMPLEMENTED`)
- [../protocol/applications/conditions/proof-of-match.md](../protocol/applications/conditions/proof-of-match.md) — canonical `ProofOfMatch(AUDIENCE|CONVERSION)` envelope and verification procedure
- [../protocol/extensions/merchant-authority.md](../protocol/extensions/merchant-authority.md) — optional merchant claim authority for official merchant actions
- [../protocol/extensions/offer-delivery-profile.md](../protocol/extensions/offer-delivery-profile.md) — offer delivery profile + verifier rules (optional extension)
- [../protocol/extensions/encryption-envelopes.md](../protocol/extensions/encryption-envelopes.md) — encrypted envelope formats for wallet/brand messages (optional extension)
- [../protocol/extensions/token-extensions.md](../protocol/extensions/token-extensions.md) — privacy-first credentials + agent delegation (optional extension)
- [../protocol/purpose/threat-model.md](../protocol/purpose/threat-model.md) — protocol security properties and invariants
- [protocol-business-boundary.md](protocol-business-boundary.md) — required protocol/business/offchain/onchain classification for spec and requirements changes
- [change-process.md](change-process.md) — authority, change-control, and CI requirements
- [versioning.md](versioning.md) — governance and upgrade processes
- [refactor-record.md](refactor-record.md) — non-normative proof-lifecycle refactor history and preserved tensions
- [campaign-architecture-evidence.md](campaign-architecture-evidence.md) — source inventory, collision decisions, Boost mapping, deletion-test results, and current-versus-target status
- [proof-validator-campaign-refactor-handoff.md](proof-validator-campaign-refactor-handoff.md) — exact non-implementing handoff for `PROOF_OF_MATCH_VERIFICATION`
- [../conformance/narratives/campaign-acceptance.md](../conformance/narratives/campaign-acceptance.md) — Monster and capacity-limited Campaign acceptance narratives
- [../diagrams/campaign-architecture.md](../diagrams/campaign-architecture.md) — canonical Campaign flow and authority-boundary diagram

## Protocol Requirements

**Integrity:** All events MUST include `eventHash` (SHA-256) and `prevHash` (linking to prior event in stream). Events MUST be signed with Ed25519.

**Identity boundary:** Internal spend-stream events MAY be wallet-scoped for issuer replay, routing, abuse controls, and reward handling. Portable Spend Attestation Tokens are separate derived artifacts and SHOULD omit wallet, user, account, and session identifiers for external verification unless recipient binding is explicitly required.

**Serialization:** Canonical JSON per RFC 8785 is REQUIRED. Alternative encodings (e.g., deterministic protobuf) MUST produce byte-identical hashes.
