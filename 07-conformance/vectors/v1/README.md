---
status: released
layer: conformance
version: v1
normative: true
---

# Crinkl Protocol Conformance Suite (v1, suite version 2)

This folder contains **versioned, data-only conformance vectors** for the Crinkl Protocol.

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

## Contract

- Vector files are **append-only** within a given `v1` suite.
- If semantics change, add a new suite version (e.g., `v2`) instead of rewriting `v1`.
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
