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
- `zk.h2PromoOpenMin.v1` (data artifact; machine-checked by `@crnkl/zk-verifier`)

They remain versioned conformance artifacts; executable Merkle verification is tracked separately because chain-binding hashing semantics differ by implementation environment.

## Public ZK verifier conformance

Public ZK verifier vectors are a beta requirement. The selected package is `@crnkl/zk-verifier`. The public fixture descriptor is `vectors/v1/vectors/zk.h2PromoOpenMin.v1.json`, and the proof artifacts live under `vectors/v1/zk/h2-promo-open-min-v1/`. They are machine-checked by the package-specific commands listed in the descriptor.

For `H2_PROMO_OPEN_MIN_V1`, public beta verifier vectors MUST include:

- valid proof artifact passes
- unknown `proofSystem` fails closed
- unknown `circuitId` fails closed
- unknown or mismatched `verifyingKeyId` fails closed
- missing `publicInputs` fails closed
- missing proof bytes fails closed
- changed `spendIdHash` fails
- changed `headEventHash` fails
- changed `spendTokenHash` fails
- changed `statementId` fails
- changed `scopeId` fails
- changed `nullifier` fails or is rejected by replay policy
- changed `expectedStoreHash` fails
- changed `minDayIndex` fails
- changed `thresholdCents` fails
- changed commitment public input fails
- changed proof bytes fails
- replayed nullifier in the same scope is rejected by the consuming flow

The public verifier MUST verify the proof from the artifact and registry manifest. A hosted Crinkl verifier response is not sufficient conformance evidence by itself. The beta release checklist is `../08-governance/zk-beta-release-checklist.md`.

## Optional Strict Mode

To fail when any data-only kinds remain:

```bash
node scripts/verify_conformance.mjs --strict-coverage
```
