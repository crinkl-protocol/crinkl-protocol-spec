---
status: draft
layer: core
version: v1
normative: true
---

# Signatures and Hashes

Crinkl uses SHA-256, RFC 8785 canonical JSON, and Ed25519 signatures as its v1 cryptographic discipline.

## Event Hashes

`eventHash` is the SHA-256 hash of the RFC 8785 canonical event envelope excluding `eventHash` and `signature`.

## Token Hashes

`tokenHash` is the SHA-256 hash of the unsigned token object after RFC 8785 canonicalization. Token signatures cover the raw digest bytes.

## Domain Separation

Domain separation is structural unless a document defines an explicit byte prefix. Event envelopes include event names and stream keys; tokens include token type and schema version; commitment leaves use the leaf/internal prefixes in the settlement binding layer.

See `canonicalization.md` for scalar encodings and preimage rules.
