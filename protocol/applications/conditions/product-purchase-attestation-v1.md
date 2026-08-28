---
status: draft
layer: applications
version: v1
normative: true
---

# Product Purchase Attestation V1

`ProductPurchaseAttestationV1` is a private canonical statement that one
product-level purchase fact was derived from one exact accepted Spend Token and
canonical Spend head under one product-verification policy.

It is an input to a ZK prover. It is not a portable disclosure token, payment
record, Campaign decision, reward authorization, or settlement artifact.

## Canonical object

The strict schema is
[`product_purchase_attestation_v1.schema.json`](../../../schemas/experimental/campaigns/product_purchase_attestation_v1.schema.json).
Unknown fields are invalid.

```text
ProductPurchaseAttestationV1 {
  tokenType: PRODUCT_PURCHASE_ATTESTATION
  schemaVersion: 1
  protocol: { protocolVersion: 1.0.0-rc.1 }
  attestationId
  productIssuerId
  issuerKeyRef
  productVerificationPolicyRef
  spendBinding {
    spendId
    spendTokenHash
    canonicalHeadEventHash
  }
  productFacts {
    productRef
    brandRef
    categoryRefs[]
    purchasedAtUnixMs
    quantity
    netProductAmountMinor
    currency
  }
  recipientBindingCommitment
  evidenceStatusEntryRef
  supersedesProductPurchaseCommitment
  productPurchaseCommitment
  authentication {
    mode: PRODUCT_EVIDENCE_SNAPSHOT_MEMBERSHIP_V1
    snapshotRef
    leafIndex
  }
  issuedAt
}
```

The complete object reference is:

```text
productPurchaseAttestationRef =
  "sha256:" + SHA-256(RFC8785(ProductPurchaseAttestationV1))
```

This reference identifies the private artifact. It does not replace the
field-native commitment used by the circuit.

## Exact field rules

- `attestationId`, `productIssuerId`, and `spendId` use the closed Crinkl
  identifier grammar.
- All `*Ref`, `*Hash`, and `*Commitment` fields labeled `sha256:` are exactly
  32 lowercase hexadecimal bytes.
- `productRef`, `brandRef`, and every `categoryRef` are content references to
  entries in the exact registry snapshots selected by the Campaign Epoch.
- `categoryRefs` contains one through eight distinct references in ascending
  unsigned-byte lexicographic order. Verifiers and provers must reject rather
  than sort or deduplicate input.
- `purchasedAtUnixMs` is a canonical unsigned decimal string in the range
  `0..9999999999999`, with no sign and no leading zero except `0`.
- `quantity` is a canonical positive decimal integer in the range
  `1..4294967295`.
- `netProductAmountMinor` is a canonical unsigned decimal integer in the range
  `0..18446744073709551615`. The profile's rule decides whether zero can match.
- `currency` is exactly three uppercase ASCII letters and uses the Epoch-bound
  currency policy. The schema does not claim that every three-letter value is
  an admitted ISO-4217 code.
- `issuedAt` is RFC 3339 UTC with exactly millisecond precision.
- `supersedesProductPurchaseCommitment` is null for an original attestation and
  names the immediately replaced product-purchase commitment for a corrected
  or superseding attestation. It must not skip an intermediate replacement.
- `authentication.leafIndex` is an unsigned 32-bit integer. The snapshot's
  tree profile may impose a smaller bound.

Floating-point JSON numbers, locale-formatted quantities, decimal currency
amounts, implicit unit conversions, Unicode normalization by a verifier, and
implementation-selected category ordering are invalid.

## Spend binding

The product evidence and Spend Token describe the same commerce event only
when all three values are equal inside the verified relation:

```text
attestation.spendBinding.spendId
attestation.spendBinding.spendTokenHash
attestation.spendBinding.canonicalHeadEventHash
```

The prover must also establish that the Spend Token is authentic, admitted by
the bound Spend issuer and verification policies, and current under the
canonical-head and correction policy at the proof cutoff. Equality of three
unverified strings is insufficient.

## Product evidence authentication

V1 uses `PRODUCT_EVIDENCE_SNAPSHOT_MEMBERSHIP_V1`. The strict snapshot and tree
contract is
[`Product and Spend Evidence Snapshots V1`](./product-evidence-snapshots-v1.md).
The product issuer publishes an immutable signed `ProductEvidenceSnapshotV1`
containing:

```text
issuerId
issuerKeyRef
productVerificationPolicyRef
sequence
asOf
previousSnapshotRef
entriesRoot
treeProfileRef
signature
```

The snapshot signature is verified outside the circuit against the exact
Trusted Platform Product Signers binding bound by the Epoch. The circuit proves that the private
`productPurchaseCommitment` occupies `leafIndex` under `entriesRoot` using the
exact `treeProfileRef`.

The product signer cannot be selected by the prover. The attestation issuer,
snapshot issuer, exact `ProductSourceSignerAuthorityBindingV1` evidence-signer
entry, key validity window, and product-verification policy must all agree. A
missing, rolled-back, equivocal, expired, revoked, wrong-role or unauthorized
snapshot fails before cryptographic proof acceptance.

## Field-native product purchase commitment

The implementation must compute the commitment inside the circuit from the
typed fields. It must not hash implementation JSON or reduce a complete
SHA-256 digest to one field element.

`ref128x2(value)` removes the `sha256:` prefix, decodes the exact 32 digest
bytes, and returns the unsigned big-endian high and low 128-bit limbs.
`text128x2(label, value)` returns the same two limbs for:

```text
SHA-256(
  UTF8("CRINKL:PRODUCT_PURCHASE_ATTESTATION:TEXT:V1") || 0x00 ||
  UTF8(label) || 0x00 || UTF8(value)
)
```

Decimal strings are parsed to their declared unsigned integer ranges.
Currency is encoded as:

```text
(ASCII(currency[0]) << 16) |
(ASCII(currency[1]) << 8)  |
 ASCII(currency[2])
```

The commitment is the Halo2 Poseidon
`Hash<PastaFp, P128Pow5T3, ConstantLength<47>, 3, 2>` over this exact
47-field-element message:

```text
text128x2("domain", "CRINKL:PRODUCT_PURCHASE_ATTESTATION:V1")
text128x2("attestationId", attestationId)
text128x2("productIssuerId", productIssuerId)
ref128x2(issuerKeyRef)
ref128x2(productVerificationPolicyRef)
text128x2("spendId", spendId)
ref128x2(spendTokenHash)
ref128x2(canonicalHeadEventHash)
ref128x2(productRef)
ref128x2(brandRef)
categoryCount
for i in 0..7:
  ref128x2(categoryRefs[i]) when i < categoryCount
  (0, 0) when i >= categoryCount
purchasedAtUnixMs
quantity
netProductAmountMinor
currencyU24
ref128x2(recipientBindingCommitment)
text128x2("issuedAt", issuedAt)
supersedesPresent                 // 0 when null; 1 when present
supersedesCommitment             // 0 when null; decoded Pasta Fp otherwise
```

`P128Pow5T3` means the exact constants supplied by the pinned Halo2 dependency
identified by the implementation return packet. Constant-length Poseidon
padding and finalization are part of the profile and cannot be replaced by a
variable-length sponge. Category padding uses sixteen zero field elements
across the remaining slots. A category reference whose two limbs are both zero
is invalid.

The resulting canonical field element is encoded as 32-byte big-endian Pasta
Fp and represented externally as `poseidon:` plus 64 lowercase hexadecimal
characters. Values greater than or equal to
`0x40000000000000000000000000000000224698fc094cf91b992d30ed00000001`
are non-canonical and invalid. The circuit constrains the supplied
`productPurchaseCommitment` to equal the recomputed value.

`evidenceStatusEntryRef`, `authentication.snapshotRef`, and
`authentication.leafIndex` are excluded from this commitment to avoid a
circular dependency and to keep status and snapshot placement independently
replaceable. `issuerKeyRef` and supersession identity are included. The
verified status entry must bind the recomputed
`productPurchaseCommitment`; the authenticated product-evidence membership
path must place that same commitment at the declared snapshot and leaf index.
The circuit also recomputes the RFC 8785/SHA-256 status-entry reference and
requires it to equal `evidenceStatusEntryRef`, and requires
`authentication.snapshotRef` and `authentication.leafIndex` to equal the
publicly resolved snapshot and witnessed path position. Exclusion from the
Poseidon commitment does not make these metadata fields unconstrained.

## Evidence status and corrections

`evidenceStatusEntryRef` identifies the RFC 8785/SHA-256 content reference of
the product evidence's private
[`ProductEvidenceStatusEntryV1`](../../../schemas/experimental/campaigns/product_evidence_status_entry_v1.schema.json)
in the exact `ProductEvidenceStatusSnapshotV1` selected by the Campaign Epoch.
That signed snapshot binds:

- the product-purchase commitment;
- one status from `ACCEPTED`, `CORRECTED`, `RETURNED`, `REVOKED`, or
  `SUPERSEDED`;
- the status effective time;
- a replacement commitment only for `CORRECTED` or `SUPERSEDED`; and
- its sequence, cutoff, previous snapshot, root, tree profile, and authority.

For `SINGLE_PRODUCT_PURCHASE_MATCH_V1`, the circuit proves membership of an
`ACCEPTED` status entry under the Epoch-bound `evidenceStatusRoot`, and the
validator verifies that the signed snapshot cutoff equals the proof's exact
`statusCutoff` value committed by the profile. Absence of a correction record
is not proof of accepted status.

A correction or return after the bound cutoff does not rewrite historical
proof bytes. Downstream hold, outcome, and settlement policies separately
decide whether later status evidence prevents economic consumption.

## Recipient binding

`recipientBindingCommitment` is the public commitment selected by the Spend
Token's holder/recipient mechanism. The private witness contains the matching
opening. The circuit establishes equality with the Spend Token binding and
uses the same opening in the profile's recipient-scope and nullifier
derivations.

For `SINGLE_PRODUCT_PURCHASE_MATCH_V1`, that opening is the raw 32-byte
per-Spend Ed25519 public key for `crinkl.holder.v2`. The circuit recomputes the
portable holder commitment from `spendId` and that key, then derives the scoped
secret from the same key and public `scopeRef` exactly as defined by the
ProofProfile. A separately chosen nullifier secret is invalid.

The attestation contains no wallet address, account ID, stable person ID, raw
holder public key, or recipient opening.

## Disclosure and retention

The complete attestation, product facts, membership paths, and recipient
opening remain inside the authorized proving boundary. Proof Validators may
receive only the profile-authorized commitments, signed public snapshots, and
the ZK proof.

An implementation must not persist private witness material merely because it
generated a proof. Retention, deletion, encryption, access control, and audit
requirements belong to the separately admitted implementation manifest and
prover policy.

## Stable validation failures

Before proof execution, parsers and resolvers distinguish:

```text
PRODUCT_ATTESTATION_SCHEMA_INVALID
PRODUCT_ATTESTATION_NON_CANONICAL
PRODUCT_EVIDENCE_SNAPSHOT_UNAVAILABLE
PRODUCT_EVIDENCE_SNAPSHOT_UNAUTHORIZED
PRODUCT_EVIDENCE_SNAPSHOT_ROLLBACK
PRODUCT_EVIDENCE_POLICY_MISMATCH
PRODUCT_EVIDENCE_MEMBERSHIP_INVALID
PRODUCT_EVIDENCE_STATUS_UNAVAILABLE
PRODUCT_EVIDENCE_STATUS_NOT_ACCEPTED
PRODUCT_EVIDENCE_STATUS_CUTOFF_MISMATCH
```

These are evidence and dependency failures. They must not be reported as
`PROOF_VERIFICATION_FAILED`, which means the cryptographic verifier executed
against available, correctly shaped artifacts and rejected the proof.
