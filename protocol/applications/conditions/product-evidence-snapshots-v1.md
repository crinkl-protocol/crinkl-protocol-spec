---
status: draft
layer: applications
version: v1
normative: true
---

# Product and Spend Evidence Snapshots V1

This contract supplies authenticated public roots for private Spend admission,
product evidence, commerce-entity relationships, and product-evidence status.
It lets a Proof Validator verify snapshot authority without receiving the
private leaf, while the circuit proves membership of that leaf.

The common tree profile is
[`H2_BINARY_POSEIDON_PASTA_FP_DEPTH32_V1`](../artifacts/h2_binary_poseidon_pasta_fp_depth32_v1.json):

```text
treeProfileRef = sha256:c207c15ee1d264b042afc9a04cd252eec3d7120fcf424b359406047c0a95da42
```

That reference is the SHA-256 of the RFC 8785 bytes of the linked artifact.
Every snapshot in this profile must carry that exact reference. A different
depth, field, domain derivation, Poseidon parameterization, path order, or
empty-leaf rule requires a different tree profile reference.

`P128Pow5T3` is pinned to `halo2_gadgets` 0.3.1
(`73a5e510d58a07d8ed238a5a8a436fe6c2c79e1bb2611f62688bc65007b4e6e7`),
`halo2_poseidon` 0.1.0
(`0fa3da60b81f02f9b33ebc6252d766f843291fb4d2247a07ae73d20b791fc56f`),
and `pasta_curves` 0.5.1
(`d3e57598f73cc7e1b2ac63c79c517b31a0877cd7c402cdcaa311b5208de7a095`).
For a membership path, sibling zero is the leaf-level sibling and sibling 31
is the root-level sibling. The node `level` input is the Pasta Fp encoding of
the corresponding unsigned u64 zero-based level, from 0 through 31.

## Snapshot identity and signatures

The strict snapshot schemas are:

- [`SpendAcceptanceSnapshotV1`](../../../schemas/experimental/campaigns/spend_acceptance_snapshot_v1.schema.json);
- [`ProductEvidenceSnapshotV1`](../../../schemas/experimental/campaigns/product_evidence_snapshot_v1.schema.json);
- [`ProductEvidenceStatusSnapshotV1`](../../../schemas/experimental/campaigns/product_evidence_status_snapshot_v1.schema.json); and
- [`CommerceEntityRegistrySnapshotV1`](../../../schemas/experimental/campaigns/commerce_entity_registry_snapshot_v1.schema.json).

For every snapshot, `signedPayload` is the complete object with the `signature`
member removed. The signature rules are:

```text
signedPayloadHash = "sha256:" + hex(SHA-256(UTF8(RFC8785(signedPayload))))
signatureBase64   = canonical Base64(Ed25519_sign(raw signedPayloadHash bytes))
snapshotRef       = "sha256:" + hex(SHA-256(UTF8(RFC8785(complete snapshot))))
```

`signature.issuedBy` and `signature.keyRef` must equal the authority and key
fields of the snapshot. Validators resolve the key through the exact
Epoch-bound `ProductSourceSignerAuthorityBindingV1`, verify its role, policy,
active/revoked state and validity at the snapshot cutoff, and reject a
self-selected signer, rollback, missing predecessor, sequence fork, or two
different accepted snapshots at the same series and sequence. The binding
contract is [`Trusted Platform Product Signers V1`](./trusted-platform-product-signers-v1.md).

Every `poseidon:` value must decode to an integer smaller than the Pasta Fp
modulus recorded by the tree profile.

## Leaf payload commitments

All references use `ref128x2` and text values use `text128x2` exactly as
defined by `ProductPurchaseAttestationV1`. The entry-payload `domainField(text)`
in the formulas below is the unsigned big-endian SHA-512 digest of
`UTF8("CRINKL:LEAF-DOMAIN:V1") || 0x00 || UTF8(text)`, reduced modulo Pasta Fp.

This payload-domain field is intentionally distinct from the profile's
tree-domain field: the latter is derived from
`UTF8("CRINKL:TREE-DOMAIN:V1") || 0x00 || UTF8(treeDomain)` and is used only by
the profile's tree leaf, node, and empty-leaf hashes. The local names clarify
the two layers; no payload or tree-domain wire value is renamed.

### Spend acceptance

The private entry uses
[`SpendAcceptanceEntryV1`](../../../schemas/experimental/campaigns/spend_acceptance_entry_v1.schema.json).
Its payload is:

```text
Hash<PastaFp, P128Pow5T3, ConstantLength<16>, 3, 2>(
  domainField("CRINKL:SPEND_ACCEPTANCE_ENTRY:V1"),
  text128x2("spendId", spendId),
  ref128x2(spendTokenHash),
  ref128x2(canonicalHeadEventHash),
  text128x2("spendIssuerId", spendIssuerId),
  ref128x2(issuerKeyRef),
  ref128x2(spendVerificationPolicyRef),
  ref128x2(holderBindingCommitment),
  acceptedAtUnixMs
)
```

The validator verifies the public snapshot authority and exact Platform signer
binding and verification-policy bindings. The circuit recomputes this private payload,
proves membership, and constrains the same Spend ID, token hash, head hash, and
holder binding throughout the product relation. This is the profile's Spend
Token authenticity mechanism; possession of three unverified strings is not
sufficient.

Only accepted `SpendAttestationTokenV2` tokens with `scheme =
"crinkl.holder.v2"` may produce entries for this profile. Issuance of an entry
requires complete portable token verification, canonical-head acceptance, and
holder-binding preservation under the referenced policies.

### Product evidence

The product-evidence payload is the canonical Pasta Fp value represented by
`ProductPurchaseAttestationV1.productPurchaseCommitment`. The snapshot leaf is
the common tree profile's domain-separated leaf hash for
`CRINKL:MERKLE:PRODUCT_EVIDENCE:V1`.

The attestation's issuer, key, policy, snapshot reference, and leaf index must
agree with the verified snapshot. Duplicate product-purchase commitments in one
snapshot are invalid.

### Product-evidence status

The private status entry uses
[`ProductEvidenceStatusEntryV1`](../../../schemas/experimental/campaigns/product_evidence_status_entry_v1.schema.json).
Status codes are fixed as:

```text
ACCEPTED = 1
CORRECTED = 2
RETURNED = 3
REVOKED = 4
SUPERSEDED = 5
```

Its payload is:

```text
Hash<PastaFp, P128Pow5T3, ConstantLength<6>, 3, 2>(
  domainField("CRINKL:PRODUCT_EVIDENCE_STATUS_ENTRY:V1"),
  productPurchaseCommitment,
  statusCode,
  effectiveAtUnixMs,
  replacementPresent,
  replacementProductPurchaseCommitmentOrZero
)
```

An accepted match proves membership of an `ACCEPTED` leaf whose effective time
is not later than the snapshot cutoff. The validator requires exact equality
between the snapshot cutoff, dependency-set cutoff, and public
`statusCutoffUnixMs`. Correction, return, revocation, and supersession are
positive terminal entries; absence of one is never treated as accepted status.
Each status snapshot contains exactly one current-state entry for each included
product-purchase commitment as of its cutoff. Duplicate current-state entries,
an entry that omits a prior effective transition, or a snapshot whose sequence
does not extend its accepted predecessor is invalid.

### Product, brand, and category registries

The private registry entry uses
[`CommerceEntityRegistryEntryV1`](../../../schemas/experimental/campaigns/commerce_entity_registry_entry_v1.schema.json).
Registry-kind codes are `PRODUCT = 1`, `BRAND = 2`, and `CATEGORY = 3`.
The fixed 23-field payload is:

```text
Hash<PastaFp, P128Pow5T3, ConstantLength<23>, 3, 2>(
  domainField("CRINKL:COMMERCE_ENTITY_REGISTRY_ENTRY:V1"),
  registryKindCode,
  ref128x2(entityRef),
  ref128x2(brandRef) or (0, 0),
  categoryCount,
  eight ref128x2(categoryRef) slots, padded with (0, 0)
)
```

A product leaf binds its product reference to exactly one brand and one through
eight ordered categories. Brand and category leaves set `brandRef = null` and
use an empty category list. The circuit proves the product leaf and the
corresponding brand and category leaves, so independently valid but unrelated
entities cannot be combined into a match.

## Campaign binding

The conversion rule references one
[`SingleProductPurchaseDependenciesV1`](../../../schemas/experimental/campaigns/single_product_purchase_dependencies_v1.schema.json).
The Epoch binds the rule through `conversionRuleRef` and must contain the
dependency-set reference and every registry, policy, snapshot, and nullifier
registry reference from that set in `registryRefs`. Resolution is transitive
but not implicit: missing or extra substitutions fail.

Snapshot authority verification occurs before proof execution. Membership,
private entry reconstruction, Spend/product equality, relationship checks, and
status evaluation occur inside the circuit.
