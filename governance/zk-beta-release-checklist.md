---
status: draft
layer: governance
version: v1
normative: true
---

# ZK Beta Release Checklist

This checklist gates any public or partner-shared beta claim for Crinkl ZK spend proof verification. It is tied to the current public artifact home in this repository and to the executable verifier package.

Beta is not complete until every required item below is checked for the release candidate being announced.

## Release Candidate Identity

Required release inputs:

- `protocolVersion`: `1.0.0-rc.2`
- public spec artifact commit: `46a4ad6` or a later commit that includes the same ZK artifact set
- verifier package commit: `7a2e9cc` or a later commit that keeps the same fixture hash and release-binary checksum contract
- platform proof source commit: `f4636c7148a0b2f993b2064e690c6bc60d609c7e`
- circuit profile: `H2_PROMO_OPEN_MIN_V1`
- proof system: `HALO2_IPA`

A beta announcement MUST name these commits or a release tag that resolves to them.

`1.0.0-rc.2` is an embedded wire/source/binding history label, not an observed
public tag or public-release classification. A beta announcement remains a
separately authorized release claim.

## Public Artifact Inventory

The public artifact home is `conformance/vectors/v1/zk/h2-promo-open-min-v1/`.

Required files:

- `valid-proof.json`
- `spend-token.json`
- `manifest.json`
- `fixture-metadata.json`
- `README.md`

The vector descriptor is `conformance/vectors/v1/vectors/zk.h2PromoOpenMin.v1.json` and MUST be listed in `conformance/vectors/v1/manifest.json`.

Required artifact identifiers:

- `verifyingKeyId`: `sha256:fe210bf4e5a3901c6fcb39a3b1e131dc67bc9006d3ef686d591264d4b773f228`
- `artifactHash`: `sha256:581d7c6f500093d8451f4cc1014bcc08b41ea77ab63fa35560cd167bd03e1ea1`
- `valid-proof.json`: `sha256:4bfefc423c729e64c91edf9b7a65af93d6c5bda323b7c0f5dfe26a9cfcfea96a`
- `spend-token.json`: `sha256:b0e574c64f4568eed58908e58fdd3f7f68b4267a5982d493d3402aba248bf741`
- `manifest.json`: `sha256:649624e30379061542bb61e696b5fee1556bcc94e4efd0198f44af7d97fabff5`
- `fixture-metadata.json`: `sha256:a6713fa9fac9c0cbde05584868ecb4f5ff3046401bb4491369faaa5299ad0d3e`

A release candidate MUST fail if any listed hash changes without a new descriptor entry, migration note, or deprecation entry.

## Required Verification Commands

Run from `crinkl-protocol-spec`:

```bash
python3 scripts/check_drift.py
node scripts/verify_conformance.mjs
```

Run from `crinkl-zk-verifier`:

```bash
npm run test:preproduction
npm run verify:release-binary
npm run test:release-binary
CRNKL_ZK_DEMO_MANIFEST_PATH=/path/to/crinkl-platform/scripts/zk-demo-rs/Cargo.toml npm run test:halo2
```

The `test:release-binary` command MUST verify the published fixture proof through the packaged release binary. The `test:halo2` command MUST verify the published fixture proof and retain the source-build Cargo path as an additional check, not as the only public backend path.

## Acceptance Matrix

The release candidate MUST prove these outcomes with package tests or equivalent partner verification evidence:

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
- changed registry `artifactHash` fails or blocks cryptographic acceptance

A hosted Crinkl API response is not sufficient evidence for any item in this matrix.

## Nullifier And Replay Evidence

The release candidate MUST state:

- nullifier scope: one spend token, one statement, one scope
- replay store owner for the consuming flow
- replay rejection behavior before any protected action is granted
- whether replay evidence comes from gateway tests, verifier tests, or partner verifier logs

## Privacy And Custody Disclosure

For this beta fixture, Crinkl generated the proof using platform-side witness custody. Release notes MUST say plainly that external verifiers do not receive private witness values, but Crinkl's proof service can see selected witness values while generating platform-side proofs.

A release candidate MUST NOT claim that Crinkl never sees witness values unless
a separated prover boundary, such as an attested TEE prover, has passed its own
release checklist.

## Backend Distribution Gate

This checklist does not by itself approve a production-grade verifier backend distribution.

The selected backend distribution profile is a Linux x64 release binary in `@crnkl/zk-verifier`:

- binary: `bin/crnkl-zk-demo-linux-x64`
- binary SHA-256: `62e697ad391587f167c2006ffd91397b36207b577533dafc7edf5683f7f38af5`
- checksum file: `bin/checksums.sha256`
- verification command: `npm run verify:release-binary`
- published-fixture command: `npm run test:release-binary`

A non-Linux partner release MUST add a Rust/WASM package, a platform-specific release binary with checksums, or partner-pinned source build instructions before making the same backend-distribution claim for that platform.

## Audit Package Gate

The release candidate MUST include an audit package. Current package: `governance/zk-beta-audit-package.md`.

The audit package MUST include:

- this checklist
- public artifact inventory and hashes
- verifier package commit or release tag
- platform proof source commit or release tag
- public input order
- verifier registry manifest
- acceptance matrix evidence
- known limitations, including direct-store alpha profile and platform-side proving
- audit owner and target date

## Partner Integration Gate

The release candidate MUST include an external verifier integration guide. Current guide: `protocol/extensions/zk-external-verifier-integration-guide.md`.

The guide MUST explain:

- what files to download
- how to verify file hashes
- how to install or run the verifier package
- how to run the public fixture
- how to interpret fail-closed reasons
- how to enforce nullifier replay protection for the consuming action
- what privacy claims are and are not supported

## Decision Rule

A beta release is blocked if any required artifact, hash, command, acceptance-matrix item, audit package item, or partner integration item is missing.
