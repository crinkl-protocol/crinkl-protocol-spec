---
status: draft
layer: governance
version: v1
normative: true
---

# ZK Beta Audit Package

This package collects the evidence required to review the current Crinkl ZK beta verifier surface for `H2_PROMO_OPEN_MIN_V1`.

It is an audit package for the beta verifier artifacts. It is not a claim that public production or an external audit is complete.

## Scope

Included:

- public proof artifact contract for `SpendZkStatementProofV1`
- verifier registry manifest shape and artifact hashes
- public beta fixture proof, spend token binding fixture, registry manifest, and metadata
- verifier package commit and release-binary checksum
- public input order and acceptance matrix
- known limitations and release blockers

Excluded:

- CBSA-in-circuit proof
- store-set membership proof for `H2_PROMO_OPEN_MIN_V1`
- wallet-side proving
- non-Linux release binary distribution
- public production incident runbook

## Owner And Timing

- audit owner: Crinkl release owner/operator
- execution owner: agent or engineer preparing the beta release candidate
- target: before the first public or partner-shared beta announcement
- external audit status: not complete in this package

A release candidate MUST replace the timing line above with a concrete audit date or explicit risk-acceptance decision before public production claims.

## Source Commits

- public spec artifact home: `crinkl-protocol-spec` commit `22aece1` or later
- verifier package: `crinkl-zk-verifier` commit `7a2e9cc` or later
- fixture-producing verifier package commit: `crinkl-zk-verifier` commit `0f73afb`
- platform proof source: `crinkl-platform` commit `f4636c7148a0b2f993b2064e690c6bc60d609c7e`

## Public Artifact Inventory

Artifact directory:

```text
07-conformance/vectors/v1/zk/h2-promo-open-min-v1/
```

Descriptor:

```text
07-conformance/vectors/v1/vectors/zk.h2PromoOpenMin.v1.json
```

Required files and hashes:

| File | SHA-256 |
|---|---|
| `valid-proof.json` | `sha256:4bfefc423c729e64c91edf9b7a65af93d6c5bda323b7c0f5dfe26a9cfcfea96a` |
| `spend-token.json` | `sha256:b0e574c64f4568eed58908e58fdd3f7f68b4267a5982d493d3402aba248bf741` |
| `manifest.json` | `sha256:649624e30379061542bb61e696b5fee1556bcc94e4efd0198f44af7d97fabff5` |
| `fixture-metadata.json` | `sha256:a6713fa9fac9c0cbde05584868ecb4f5ff3046401bb4491369faaa5299ad0d3e` |

Registry identifiers:

- `proofSystem`: `HALO2_IPA`
- `circuitId`: `H2_PROMO_OPEN_MIN_V1`
- `verifyingKeyId`: `sha256:fe210bf4e5a3901c6fcb39a3b1e131dc67bc9006d3ef686d591264d4b773f228`
- `artifactHash`: `sha256:581d7c6f500093d8451f4cc1014bcc08b41ea77ab63fa35560cd167bd03e1ea1`

## Backend Distribution Evidence

Current distribution profile:

- package: `@crnkl/zk-verifier`
- platform: Linux x64
- binary: `bin/crnkl-zk-demo-linux-x64`
- binary checksum: `62e697ad391587f167c2006ffd91397b36207b577533dafc7edf5683f7f38af5`
- checksum file: `bin/checksums.sha256`

Required checks:

```bash
npm run verify:release-binary
npm run test:release-binary
```

The release-binary test MUST verify the published fixture proof without requiring `CRNKL_ZK_DEMO_MANIFEST_PATH`.

## Public Input Order

The verifier registry entry MUST preserve this order:

```text
spendIdHash
headEventHash
spendTokenHash
statementId
scopeId
nullifier
expectedStoreHash
minDayIndex
thresholdCents
commitmentStore
commitmentDayIndex
commitmentTotal
```

Changing this order requires a new registry entry or a documented migration/deprecation entry.

## Acceptance Matrix Evidence

Required verifier outcomes:

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

Package evidence commands:

```bash
npm run test:preproduction
npm run verify:release-binary
npm run test:release-binary
CRNKL_ZK_DEMO_MANIFEST_PATH=/path/to/crinkl-platform/scripts/zk-demo-rs/Cargo.toml npm run test:halo2
```

Spec evidence commands:

```bash
python3 scripts/check_drift.py
node scripts/verify_conformance.mjs
```

## Known Limitations

- `H2_PROMO_OPEN_MIN_V1` is the active direct-store profile. It proves the expected store hash, minimum day index, and minimum total relation. It does not prove store-set membership.
- CBSA is not proven inside this circuit.
- The current beta fixture was generated with platform-side proving. Crinkl's proof service can see selected witness values while generating the proof.
- The packaged release binary is Linux x64 only.
- Public production still requires a release tag, external audit completion or explicit risk acceptance, a production incident runbook, and a circuit/key deprecation plan.

## Audit Decision Rule

The audit package is incomplete if any source commit, artifact hash, verifier command, acceptance-matrix result, custody disclosure, or known limitation is missing from the release candidate.
