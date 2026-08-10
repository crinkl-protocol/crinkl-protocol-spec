---
status: draft
layer: core
version: v1
normative: true
---

# Privacy Boundaries

Internal Crinkl processing may use wallet-scoped or session-scoped references for replay, routing, abuse controls, and reward handling. Portable spend proofs must not require user identity, raw receipt access, or cross-context behavioral profiles.

Preferred claims are identity-minimized and identity-excluded from portable proofs. The protocol does not claim full anonymity.

## Portable Proof Boundary

A portable Spend Attestation Token SHOULD omit wallet, user, account, and session identifiers unless recipient binding is explicitly required by verifier policy. A verifier MUST NOT require private wallet lookup or app-user lookup to validate a portable Spend Attestation Token.
