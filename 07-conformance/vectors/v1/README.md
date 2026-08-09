---
status: release-candidate
layer: conformance
version: v1
normative: true
---

# Crinkl Protocol Conformance Suite (v1, suite version 3)

This folder contains versioned conformance vectors for the Crinkl Protocol. The
repository runner executes 14 manifest kinds and reports 3 kinds as data-only.
The data-only kinds are the two reward-batch Merkle kinds and the ZK fixture
descriptor; the ZK package-specific checks are not executed by this runner.

Goal: any implementation (server, platform, third-party verifier) can run the same vectors and must produce identical:

- RFC 8785 JSON canonicalization output
- SHA-256 hashes over canonical bytes (event hashes, token hashes)
- Ed25519 signature verification (and, where applicable, deterministic signature bytes)
- Commitment-layer Merkle roots and inclusion proofs
- Cross-wallet nullifier derivation (scope-bound, privacy-preserving)
- Blinded recipient commitments (hash of wallet + blinder)

Executable verifier:
- See [`../../verifier-test-suite.md`](../../verifier-test-suite.md)
- Run `node scripts/verify_conformance.mjs` from repo root.
- Require the Campaign profile explicitly with
  `node scripts/verify_conformance.mjs --require-kind campaign.directBuyerReward.profileV1`.
- Require the Spend Token V2 profile explicitly with
  `node scripts/verify_conformance.mjs --require-kind token.spendAttestation.holderBinding.v2`.
- Require the W3C Spend Attestation profile explicitly with
  `node scripts/verify_conformance.mjs --require-kind credential.spendAttestation.vcdm2.eddsaJcs2022`.

## Layout

- `manifest.json` — lists vector files and basic metadata.
- `vectors/*.json` — test vectors grouped by surface area.

## Vector Types

### Core Primitives
- `canonicalization.json` — RFC 8785 JSON canonicalization
- `eventHash.json` — Event hash computation
- `ed25519.json` — Ed25519 signature verification

### Tokens
- `token.spendAttestation.portableV1.fromSpendStream.json` — Spend attestation token derivation
- `tokenHash.spendAttestation.v1.json` — Spend token hash computation
- `token.verifiedSpendDistribution.v1.json` — Verified spend distribution token derivation
- `token.spendAttestation.holderBinding.v2` — manifest-bound external
  verification of the optional per-Spend holder commitment and fresh
  challenge-response proof
- `credential.spendAttestation.vcdm2.eddsaJcs2022` — manifest-bound fixture
  harness for the optional W3C VC 2.0 Spend Attestation wire form; candidate
  only and not a generic VC/VP API or runtime authorization

### Commitment Layer
- `merkle.rewardBatch.schemaV1.json` — Merkle tree for aggregated reward leaves (schema 1a/1b)
- `merkle.rewardBatch.schemaV2.rewardEventsRoot.json` — Reward events root for spend linkage (schema 2a/2b)

### Privacy Features
- `nullifier.crossWallet.json` — Cross-wallet nullifier derivation for multi-wallet proofs
- `recipient.blinded.schemaV1b.json` — Blinded recipient commitments (schema 1b/2b)

### ZK Proofs
- `zk.h2PromoOpenMin.v1.json` — Descriptor for the `H2_PROMO_OPEN_MIN_V1` public beta fixture set.
- `zk/h2-promo-open-min-v1/` — Proof artifact, spend token binding fixture, verifier registry manifest, and fixture metadata.

### Campaign Profiles

- `campaign.directBuyerReward.profileV1` — manifest-bound external verification of
  the exact byte-pinned sponsor-neutral direct buyer-reward
  package. Release consumers must authenticate the accepted tag and exact
  `versions/release.json` digest before relying on it.

### Object Model (OM4)

- `schema.objectModel.om4.v1` — manifest-bound structural and semantic
  verification of the four candidate object-model schemas:
  `VerificationPolicy`, `IssuerRegistrySnapshot`, `AttestationStatus`, and
  `SpendPredicate`. The checker recomputes content addresses and executes
  timestamp-ordering and cross-field failures. See
  `../../profiles/object-model-v1/README.md`.
- `objectModel.collapsedArtifactKind.rejected` — whole-object dispatcher
  conformance. The shipped checker owns the thirteen-name canonical object
  inventory in `README.md#protocol-objects`; vectors supply only artifact
  inputs. `eligibilityProof` and `conversionProof` are rejected, with
  `ProofOfMatch` and a valid `SpendPredicate` as positive controls.

## Contract

- Released vector files are **append-only** within a given suite.
- Untagged candidate profile fixtures may be corrected in place only when the
  profile artifact digests are updated in the same independently reviewed
  slice. A released semantic change requires a new suite version.
- Implementations SHOULD allow overriding the protocol repo path via an env var (e.g., `CRINKL_PROTOCOL_DIR`) so CI can locate these vectors.

## Privacy Vectors

The `nullifier.crossWallet.json` and `recipient.blinded.schemaV1b.json` vectors define canonical behavior for:

1. **Cross-wallet nullifier derivation**: Proves multiple wallets can generate matching scope-bound nullifiers without revealing wallet addresses. Validates:
   - Master secret derivation is order-independent
   - Nullifiers are scope-specific (no cross-campaign linkage)
   - Anti-replay protection without identity disclosure

2. **Blinded recipient commitments**: Proves recipients can participate in reward batches without revealing wallet addresses. Validates:
   - `recipientId = hash(wallet + blinder)` computation
   - Cross-batch unlinkability (fresh blinders per batch)
   - Selective disclosure via opening proofs
   - Aggregation with blinded commitments
