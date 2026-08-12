---
status: experimental
layer: extension
version: v1
normative: true
---

# Solana Commitment Binding

Solana commitment binding is an optional chain binding for publishing commitment roots or settlement references. It is downstream of Core spend proof.

The binding MUST NOT redefine Spend Attestation validity. A chain transaction can anchor a commitment root, but the validity of a Spend Attestation still depends on canonicalization, hashes, signatures, issuer authority, and verification state.

Current chain-binding rules and anti-replay requirements are specified in `../applications/economics/settlement-bindings.md#chain-bindings`.

Campaign liability and resolution are defined by
`../applications/campaigns/README.md`. A future Solana profile may bind those
canonical objects without changing their meaning.
