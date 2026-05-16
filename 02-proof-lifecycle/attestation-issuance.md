---
status: draft
layer: lifecycle
version: v1
normative: true
---

# Attestation Issuance

A hard-verified or corrected Spend Event may produce a Spend Attestation. That attestation may then be packaged as a portable Spend Attestation Token. Issuance is downstream of evidence, normalization, and verification state.

## Issuance Rules

- A Spend Attestation MUST be derived from the canonical spend-stream head.
- A Spend Attestation Token MUST be signed by an authorized issuer key.
- Corrections produce new attestations; signed tokens are immutable historical artifacts.
- Portable tokens SHOULD omit wallet unless recipient binding is explicitly required.

See `../03-portability/spend-attestation-token.md` for the portable token shape and verifier procedure.
