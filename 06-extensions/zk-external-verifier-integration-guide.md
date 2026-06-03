---
status: draft
layer: extensions
version: v1
normative: false
---

# ZK External Verifier Integration Guide

This guide is for external Consumers, Issuers, and brand verifiers that need to check a Crinkl ZK spend proof without trusting the Crinkl gateway decision.

It covers the current beta verifier surface for `H2_PROMO_OPEN_MIN_V1`.

## What You Need

From `crinkl-protocol-spec`:

- `07-conformance/vectors/v1/vectors/zk.h2PromoOpenMin.v1.json`
- `07-conformance/vectors/v1/zk/h2-promo-open-min-v1/valid-proof.json`
- `07-conformance/vectors/v1/zk/h2-promo-open-min-v1/spend-token.json`
- `07-conformance/vectors/v1/zk/h2-promo-open-min-v1/manifest.json`
- `07-conformance/vectors/v1/zk/h2-promo-open-min-v1/fixture-metadata.json`
- `08-governance/zk-beta-release-checklist.md`

From `@crnkl/zk-verifier`:

- verifier package commit `7a2e9cc` or later
- Linux x64 release binary `bin/crnkl-zk-demo-linux-x64`
- checksum file `bin/checksums.sha256`

## Verify Public Artifact Hashes

Compare the downloaded files against the descriptor and metadata hashes:

```bash
sha256sum valid-proof.json spend-token.json manifest.json fixture-metadata.json
```

Expected hashes:

```text
valid-proof.json       4bfefc423c729e64c91edf9b7a65af93d6c5bda323b7c0f5dfe26a9cfcfea96a
spend-token.json       b0e574c64f4568eed58908e58fdd3f7f68b4267a5982d493d3402aba248bf741
manifest.json          649624e30379061542bb61e696b5fee1556bcc94e4efd0198f44af7d97fabff5
fixture-metadata.json  a6713fa9fac9c0cbde05584868ecb4f5ff3046401bb4491369faaa5299ad0d3e
```

Reject the artifact set if any hash differs and no new descriptor entry explains the change.

## Verify The Release Binary

From the verifier package root:

```bash
npm run verify:release-binary
```

Expected binary checksum:

```text
62e697ad391587f167c2006ffd91397b36207b577533dafc7edf5683f7f38af5  bin/crnkl-zk-demo-linux-x64
```

## Run The Public Fixture

From the verifier package root:

```bash
npm run test:release-binary
```

This command verifies the published fixture proof through the bundled release binary. It does not require a local `crinkl-platform` Cargo manifest.

For source-build verification, also run:

```bash
CRNKL_ZK_DEMO_MANIFEST_PATH=/path/to/crinkl-platform/scripts/zk-demo-rs/Cargo.toml npm run test:halo2
```

## Application Verification Flow

An application verifier should:

1. Load the proof artifact.
2. Load the Spend Attestation Token or equivalent token fields.
3. Load the verifier registry manifest.
4. Recompute `statementId` from canonical statement JSON.
5. Check artifact shape, token binding, public input order, and replay policy.
6. Run the cryptographic backend.
7. Store the `(scopeId, nullifier)` replay key before granting the protected action.

Example package call:

```js
import { createHash } from "node:crypto";
import { createHalo2CliBackend, verifySpendZkProof } from "@crnkl/zk-verifier";

const result = await verifySpendZkProof({
  proof,
  spendToken,
  manifest,
  hashStatement: (statement) => `sha256:${createHash("sha256").update(canonicalJson(statement), "utf8").digest("hex")}`,
  backend: createHalo2CliBackend(),
  seenNullifiers
});
```

`createHalo2CliBackend()` uses the bundled Linux x64 binary by default on Linux x64. Use `createHalo2CliBackend({ command: "/path/to/crnkl-zk-demo" })` for a separately supplied binary.

## Fail-Closed Reasons

A verifier MUST reject rather than warn on these failures:

- unknown `proofSystem`
- unknown `circuitId`
- unknown or mismatched `verifyingKeyId`
- mismatched public input order
- changed statement, scope, nullifier, spend token hash, or head event hash
- malformed proof artifact
- unsupported backend
- cryptographic proof rejection
- replayed nullifier for the same scope

A hosted Crinkl API response is not a substitute for local verification.

## Nullifier Replay Policy

Current scope rule:

```text
one spend token, one statement, one scope
```

The consuming verifier or gateway must store the used nullifier for the scope before granting the protected action. If the same `(scopeId, nullifier)` appears again, reject it as replay.

## Privacy Claims

Supported for this beta fixture:

- external verifiers receive proof artifacts and public inputs, not private witness openings
- external verifiers can verify eligibility without trusting the Crinkl gateway decision

Not supported for this beta fixture:

- wallet-side proving
- a claim that Crinkl never sees witness values
- CBSA proven inside ZK
- store-set membership proof for `H2_PROMO_OPEN_MIN_V1`

## Non-Linux Verifiers

The current packaged binary is Linux x64. Non-Linux verifier environments need one of:

- a platform-specific release binary with checksum
- a Rust/WASM package
- a partner-pinned source build with reproducible build instructions

Do not claim the Linux x64 binary release covers other platforms.
