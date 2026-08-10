---
status: draft
layer: portability
version: v1
normative: true
---

# Identity Exclusion

Portable Spend Attestation Tokens are identity-excluded by default. They prove a spend claim under protocol rules without requiring wallet identity, app-user identity, session identifiers, raw receipt access, or private operator lookup.

Internal Crinkl processing may use wallet-scoped or session-scoped references for replay, routing, abuse controls, and reward handling. Those internal references do not become portable proof fields unless explicitly included in a signed artifact under a verifier policy that requires recipient binding.

## Verifier Requirement

A verifier MUST be able to validate a portable Spend Attestation Token by checking canonical bytes, hashes, signatures, issuer authority, supported versions, and included proof material. A verifier MUST NOT require private wallet lookup or app-user lookup to decide portable token validity.

## Language Boundary

Use identity-minimized, identity-excluded from portable proofs, and privacy-preserving. Do not claim full anonymity unless a concrete proof system and threat model provide that guarantee.
