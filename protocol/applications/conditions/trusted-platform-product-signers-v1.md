---
status: draft
layer: applications
version: v1
normative: true
---

# Trusted Platform Product Signers V1

`ProductSourceSignerAuthorityBindingV1` is the canonical, versioned and
content-addressed record of the two Crinkl Platform keys trusted to supply the
product source for one exact Campaign evaluation coordinate. It is not a
general issuer registry, a signer self-attestation, a runtime key-discovery
mechanism, a Campaign decision, reward authorization, or settlement artifact.

The strict schema is
[`product_source_signer_authority_binding_v1.schema.json`](../../../schemas/experimental/campaigns/product_source_signer_authority_binding_v1.schema.json).
Unknown fields are invalid.

## One fixed Platform pair

The binding contains exactly two named signer records:

| Record | Role | May sign |
|---|---|---|
| `productEvidenceSigner` | `PRODUCT_EVIDENCE` | `ProductEvidenceSnapshotV1` and the `productEvidenceIssuer` projection slot only |
| `productStatusSigner` | `PRODUCT_STATUS` | `ProductEvidenceStatusSnapshotV1` and the `statusAuthority` projection slot only |

Both are operated by Crinkl Platform for V1, but they must have different
`authorityId`, `keyRef`, and `publicKey` values. A product-evidence key cannot
sign a status checkpoint and a status key cannot sign product evidence.

Each record freezes its exact snapshot series/reference, authorized policy,
public key, inclusive `validFromUnixMs`, exclusive `validUntilUnixMs`, and
`ACTIVE` or `REVOKED` lifecycle. At the
exact evaluation cutoff, a relying implementation MUST reject a signer whose
role, authority ID, key reference, public key, policy, validity window, or
active status does not match. A revoked key may remain in historical bytes but
is not admitted at or after `revokedAtUnixMs`; for a Campaign coordinate, both
records must be `ACTIVE` at its cutoff. A missing cutoff, status, key, policy
or binding is `INDETERMINATE`.

## Exact Campaign coordinate

The binding freezes `campaignScope.campaignNamespaceRef`, `campaignScope.campaignId`,
`campaignScope.epochSeriesId`, `campaignScope.epochVersion`,
`campaignScope.conditionId`, and `campaignScope.evaluationContextHash`. Its `bindingProfile` is
`PINNED_CRINKL_PLATFORM_PRODUCT_SOURCE_SIGNERS_V1`, its `operatorId` is
`crinkl-platform`, and `selection` fails closed. It deliberately does not carry a Campaign Epoch
content reference: adding that reference would create a content-addressing
cycle because the Epoch transitively carries the binding through its dependency
set and `registryRefs`.

The binding is admitted only when its coordinate equals the resolved Campaign
Epoch, conversion Condition and evaluation context. Its content reference is:

```text
productSourceSignerAuthorityBindingRef =
  "sha256:" + SHA-256(RFC8785(ProductSourceSignerAuthorityBindingV1))
```

`SingleProductPurchaseDependenciesV1` carries that exact reference. The internal
canonical successor dependency profile also carries it. The
Campaign Epoch's `registryRefs` must contain both the dependency-set reference
and the binding reference. This is the authorization path; the binding is not
self-signed and a signer cannot authorize itself.

## Verification

For a product-evidence snapshot, a verifier MUST require exact equality among:

```text
binding.productEvidenceSigner.authorityId
snapshot.issuerId
snapshot.signature.issuedBy

binding.productEvidenceSigner.keyRef
snapshot.issuerKeyRef
snapshot.signature.keyRef

binding.productEvidenceSigner.productVerificationPolicyRef
snapshot.productVerificationPolicyRef
```

For a product-status snapshot, the same rule applies to
`productStatusSigner`, `statusAuthorityId`, `authorityKeyRef`,
`signature.keyRef`, and `statusPolicyRef`.

The verifier uses the binding's pinned public key to verify the canonical
Ed25519 snapshot signature. It must reject a self-selected key, wrong-role
signature, expired key, revoked key, substituted policy, or a binding from a
different Campaign coordinate before product membership or proof acceptance.
