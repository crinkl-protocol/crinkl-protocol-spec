---
status: released
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

To require the direct buyer-reward profile to execute rather than be skipped:

```bash
node scripts/verify_conformance.mjs \
  --require-kind campaign.directBuyerReward.profileV1
```

To require the Spend Token V2 holder-binding profile:

```bash
node scripts/verify_conformance.mjs \
  --require-kind token.spendAttestation.holderBinding.v2
```

Release consumers additionally use `--require-released`. The `v1.0.0-rc.4`
released manifest must pass that gate.

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
- `campaign.directBuyerReward.profileV1` through its manifest-bound, byte-pinned
  Python verifier
- `token.spendAttestation.holderBinding.v2` through its manifest-bound,
  byte-pinned Node verifier

Checks include:

- RFC-8785/JCS-style canonical serialization used by vectors.
- SHA-256 hashes over canonical bytes.
- Ed25519 deterministic signing and verification (including vector key material).
- Portable spend-attestation token hash/signature consistency.
- Verified spend distribution token hash/signature consistency.
- Nullifier derivation determinism and scope isolation.
- Exact Campaign profile schemas, canonical bytes, hashes, Ed25519 signatures, Epoch
  composition, protected-term exclusions,
malformed-composition rejection and same-position equivocation rejection.
- Spend Token V2 canonicalization, issuer signature, holder commitment,
  challenge binding, holder signature, expiry, replay, and absent-binding
  decisions.

Manifest-bound external verifiers are restricted to files under
`07-conformance/profiles/`, receive no shell interpolation or manifest-supplied arguments,
have a bounded execution time and output buffer, and fail the parent verifier on any
nonzero exit. A vector and verifier path outside the accepted conformance roots is
rejected.

## Current Data-Only Kinds

Three kinds are present in `manifest.json` but are data-only in this runner:

- `merkle.rewardBatch.schemaV1`
- `merkle.rewardBatch.schemaV2.rewardEventsRoot`
- `zk.h2PromoOpenMin.v1` (data descriptor; package-specific checks are provided
  by `@crnkl/zk-verifier`, but this runner does not execute them)

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
