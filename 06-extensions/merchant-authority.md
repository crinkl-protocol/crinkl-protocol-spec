---
status: experimental
layer: extension
version: v1
normative: true
---

# Merchant Authority (v1) - Store Claim Authority Extension

> **Status:** v1 optional extension; non-core.
>
> This document defines how an actor can hold verified authority over a
> `storeId`, `storeLocationId`, brand, or franchise group without changing
> Spend Attestation Token semantics.

## Scope and Boundary

Merchant authority is authority over store identity. It is not proof of spend.

This extension composes:

- `storeId`, `storeHash`, `storeLocationId`, and `storeLocationHash` from
  `store-registry.md`
- system-stream envelope rules from `../protocol/core/spend-event.md`
- campaign rule and epoch bindings from
  `../protocol/applications/conditions/campaign-commitment.md`
- settlement commitment bindings from
  `../protocol/applications/economics/campaign-settlement-gcd.md`

This extension does **not**:

- change `SpendAttestationTokenV1`
- assert that a receipt is valid
- assert that payment settled with a merchant
- define private evidence verification procedures
- require Etch or other validators to decide merchant ownership
- make merchant authority mandatory for operator or system campaigns

The protocol cares only that a trusted merchant-claim verifier issued a signed
claim attestation with explicit scope, status, and validity window. How the
verifier reached that decision is deployment policy.

## Versioning

Merchant authority is an rc.2-compatible extension. It uses artifact-level
`schemaVersion` fields:

- `MerchantClaimAttestationV1.schemaVersion = 1`
- `MerchantClaimEventV1.schemaVersion = 1`
- `CampaignAuthorityV1.schemaVersion = 1`

`1.0.0-rc.2` is supported embedded wire/source/binding history; it is not an
observed public tag or public release classification.

Adding this extension does not by itself require a global `protocolVersion`
bump because core spend event validity, Spend Attestation Token validity, and
operator/system campaign validity are unchanged. A future change that makes
merchant authority mandatory for all campaign verification would require a
protocol-version review.

## Core Objects

### MerchantClaimAttestationV1

`MerchantClaimAttestationV1` is a signed verifier attestation that an actor has
authority over a bounded store identity scope.

```text
MerchantClaimAttestationV1 {
  schemaVersion: 1,
  attestationType: "MERCHANT_CLAIM_ATTESTATION",

  claimId: Identifier,
  actorId: Identifier,

  storeId: Identifier,
  storeHash: "sha256:" + Hash,
  storeLocationId?: Identifier,
  storeLocationHash?: "sha256:" + Hash,
  targetMerchantSetRoot?: Hash,

  claimScope: "STORE" | "LOCATION" | "BRAND" | "FRANCHISE_GROUP",
  status: "PENDING" | "VERIFIED" | "REJECTED" | "REVOKED",

  evidenceRefs: [EvidenceRefV1],
  verifiedBy?: Identifier,
  verifiedAt?: TimestampISO,
  expiresAt?: TimestampISO,
  revokedAt?: TimestampISO,
  rejectionReasonHash?: "sha256:" + Hash,
  revocationReasonHash?: "sha256:" + Hash,

  issuedAt: TimestampISO,
  claimAttestationHash: "sha256:" + Hash,
  signatures: {
    issuedBy: Identifier,
    publicKey: Base64,
    signature: Base64
  }
}
```

`claimAttestationHash` MUST be computed over `MerchantClaimAttestationV1` with
`claimAttestationHash` and `signatures` omitted, using RFC 8785 canonical JSON
and SHA-256 encoded as `"sha256:" + lowercase hex`.

The verifier signature MUST be over `claimAttestationHash`. Verifiers MUST
reject an attestation signed by an authority that is not authorized for merchant
claim verification at `issuedAt`.

`expiresAt` is self-enforcing. A verifier MUST reject an otherwise `VERIFIED`
claim after `expiresAt`, even if no `MERCHANT_CLAIM_EXPIRED` event exists.

`evidenceRefs` are references, not evidence blobs. They MAY point to private
review records, domain verification, payment-processor proofs, Google Business
Profile checks, documents, or manual review packets. Portable artifacts SHOULD
carry only references and hashes needed for audit.

### EvidenceRefV1

```text
EvidenceRefV1 {
  evidenceType:
    "DOMAIN" |
    "PAYMENT_PROCESSOR" |
    "GOOGLE_BUSINESS_PROFILE" |
    "DOCUMENT" |
    "MANUAL_REVIEW" |
    String,
  evidenceRef: String,
  evidenceHash?: "sha256:" + Hash,
  collectedAt?: TimestampISO
}
```

## Claim Events

Merchant claim events use an append-only authority stream. They MUST NOT be
mixed into spend streams.

Candidate event names:

```text
MERCHANT_CLAIM_SUBMITTED
MERCHANT_CLAIM_EVIDENCE_ADDED
MERCHANT_CLAIM_VERIFIED
MERCHANT_CLAIM_REJECTED
MERCHANT_CLAIM_REVOKED
MERCHANT_CLAIM_EXPIRED
```

`MERCHANT_CLAIM_EXPIRED` is operational. Expiry validity is determined by the
latest signed attestation and its `expiresAt` value.

### MerchantClaimEventV1

```text
MerchantClaimEventV1 {
  schemaVersion: 1,
  eventName: MerchantClaimEventName,
  claimId: Identifier,
  actorId?: Identifier,
  storeId: Identifier,
  storeHash: "sha256:" + Hash,
  storeLocationId?: Identifier,
  storeLocationHash?: "sha256:" + Hash,
  targetMerchantSetRoot?: Hash,
  claimScope: "STORE" | "LOCATION" | "BRAND" | "FRANCHISE_GROUP",
  evidenceRefs?: [EvidenceRefV1],
  claimAttestationHash?: "sha256:" + Hash,
  statusAfter: "PENDING" | "VERIFIED" | "REJECTED" | "REVOKED" | "EXPIRED",
  occurredAt: TimestampISO
}
```

If carried in the system stream, the system-stream envelope supplies `chainId`,
`eventId`, `prevHash`, `eventHash`, `protocolVersion`, and `signature`.

## Campaign Authority

`CampaignAuthorityV1` binds campaign creation authority to a campaign rule or
epoch. It is not a marketing metadata field.

```text
CampaignAuthorityV1 {
  schemaVersion: 1,
  authorityType: "OPERATOR" | "SYSTEM" | "VERIFIED_MERCHANT",
  actorId: Identifier,
  merchantClaimId?: Identifier,
  claimAttestationHash?: "sha256:" + Hash,
  claimScope?: "STORE" | "LOCATION" | "BRAND" | "FRANCHISE_GROUP",
  storeId?: Identifier,
  storeHash?: "sha256:" + Hash,
  storeLocationId?: Identifier,
  storeLocationHash?: "sha256:" + Hash,
  targetMerchantSetRoot?: Hash,
  issuedAt: TimestampISO,
  expiresAt?: TimestampISO
}
```

For `authorityType = "VERIFIED_MERCHANT"`:

- `merchantClaimId` is REQUIRED.
- `claimAttestationHash` is REQUIRED.
- The referenced merchant claim attestation MUST be `VERIFIED`.
- The referenced claim MUST be unexpired and unrevoked at the campaign
  authority evaluation time.
- The claim scope MUST cover the campaign target:
  - `STORE` covers matching `storeId` / `storeHash`.
  - `LOCATION` covers matching `storeLocationId` / `storeLocationHash`.
  - `BRAND` or `FRANCHISE_GROUP` covers the committed target merchant set or a
    deployment-defined brand/franchise grouping bound into the campaign rule.

For `authorityType = "OPERATOR"` or `"SYSTEM"`, merchant claim fields MUST be
absent unless a stricter deployment profile explicitly requires them.

## Official Actions

Official merchant actions MUST verify `CampaignAuthorityV1` or an equivalent
merchant authority proof.

Minimum guarded actions:

- official merchant campaign creation
- official store or merchant response
- official store dashboard administration
- merchant-origin campaign amendment

User-promoted, operator-funded, and system campaigns MAY continue without
merchant claims as long as their authority type is not `VERIFIED_MERCHANT`.

## Verification Procedure

A verifier evaluating an official merchant action MUST:

1. Verify the referenced store identity against the store registry or campaign
   target merchant set binding.
2. Verify the merchant claim attestation hash and signature.
3. Verify the signer is authorized as a merchant-claim verifier.
4. Verify status is `VERIFIED`.
5. Reject expired or revoked claims.
6. Verify the claim scope covers the action target.
7. Verify `CampaignAuthorityV1` is included in the campaign rule or equivalent
   immutable action material.
8. Reject attempts to satisfy spend proof requirements with merchant authority
   artifacts. Merchant authority never substitutes for a valid Spend
   Attestation Token or ProofOfMatch.

## Security Notes

- A merchant claim proves authority over a bounded store identity, not that the
  merchant likes, disputes, or funded a particular spend.
- Evidence verification can improve over time without changing
  `MerchantClaimAttestationV1` as long as the emitted attestation semantics stay
  the same.
- Revocation is prospective. Historical campaign epochs remain auditable with
  the authority artifact that was valid when they were created, unless the
  deployment defines a fraud or legal override policy outside this protocol
  extension.
- Merchant authority artifacts MUST NOT include raw personal documents, private
  account credentials, payment processor secrets, or raw customer data.
