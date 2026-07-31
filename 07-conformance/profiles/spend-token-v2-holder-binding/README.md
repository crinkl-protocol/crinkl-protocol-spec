---
status: release-candidate
layer: portability
version: v2
normative: true
---

# Spend Attestation Token V2 Holder Binding Profile

Maturity: `release-candidate`.

This profile publishes the optional, identity-excluded holder-control mechanism
for `SpendAttestationTokenV2`. The token remains a valid portable Spend
attestation when `holderBinding` is absent. When it is present, a verifier can
require a fresh challenge response from the per-Spend Ed25519 key committed by
the issuer-signed token.

The profile binds:

- schema-v2 unsigned-token canonicalization and `tokenHash`;
- the `crinkl.holder.v2` per-Spend public-key commitment;
- a verifier-authenticated challenge with a maximum lifetime of 300 seconds;
- an Ed25519 signature over the raw SHA-256 challenge digest;
- one-time challenge consumption; and
- valid, wrong-key, wrong-signature, changed-context, expired, replayed, and
  absent-binding decisions.

The holder key is distinct per `spendId`. Holder control establishes neither a
wallet, legal identity, person, complete purchase history, Campaign
qualification, reward, settlement, nor cross-Spend linkage.

Run the exact profile verifier:

```bash
node 07-conformance/profiles/spend-token-v2-holder-binding/scripts/check_holder_binding_vectors.mjs
```

Or require the profile through the released-suite verifier:

```bash
node scripts/verify_conformance.mjs \
  --require-kind token.spendAttestation.holderBinding.v2
```

The deterministic key material is public test data. The profile contains no
production key, holder secret, receipt, wallet, user identifier, or private
Spend witness.
