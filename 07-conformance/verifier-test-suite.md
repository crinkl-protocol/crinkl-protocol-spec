---
status: draft
layer: conformance
version: v1
normative: true
---

# Conformance Verification

This document describes the executable verifier for `vectors/v1`.

## Run

From repo root:

```bash
node scripts/verify_conformance.mjs
```

## What Is Checked

`scripts/verify_conformance.mjs` currently validates these kinds end-to-end:

- `canonicalization`
- `eventHash`
- `ed25519`
- `scenario.spend.lifecycle`
- `tokenHash.spendAttestation.v1`
- `token.spendAttestation.portableV1.fromSpendStream`
- `token.verifiedSpendDistribution.v1`
- `nullifier.crossWallet`
- `recipient.blinded.schemaV1b` (recipient-id + canonical leaf construction checks)

Checks include:

- RFC-8785/JCS-style canonical serialization used by vectors.
- SHA-256 hashes over canonical bytes.
- Ed25519 deterministic signing and verification (including vector key material).
- Portable spend-attestation token hash/signature consistency.
- Verified spend distribution token hash/signature consistency.
- Nullifier derivation determinism and scope isolation.

## Current Data-Only Kinds

These kinds are present in `manifest.json` but are not yet machine-checked by this script:

- `merkle.rewardBatch.schemaV1`
- `merkle.rewardBatch.schemaV2.rewardEventsRoot`

They remain versioned conformance artifacts; executable Merkle verification is tracked separately because chain-binding hashing semantics differ by implementation environment.

## Optional Strict Mode

To fail when any data-only kinds remain:

```bash
node scripts/verify_conformance.mjs --strict-coverage
```
