---
status: experimental
layer: extension
version: v1
normative: true
---

# Brand-Verifiable Offer Delivery Profile

> **Status: v1 optional extension — offer delivery profile, not campaign protocol**
>
> This document defines the **message formats** and **verifier rules** for delivering brand offers to wallets and unlocking them using Crinkl protocol artifacts.
>
> It is intentionally minimal: it standardizes *how wallets and brands interoperate*, without defining a full campaign rule or settlement layer. Campaign rule composition is defined by `../04-condition-layer/campaign-commitment.md`.
>
> Implementation status: the message/profile boundary is normative. The demo profile and wallet-secret rollout proof target are explicitly transitional until `zk-circuit-catalog.md` defines a concrete wallet rollout circuit.

## 1) Boundary

This document is an offer-delivery profile. It is not the campaign primitive.

Use `../04-condition-layer/campaign-commitment.md` for:

- composing campaign rules from Spend Validity, Buyer State, Frequency / Intensity, Category / Competitive Relationship, Market / Context, and Outcome / Conversion
- audience qualification and verified conversion terminology
- verifier-signed conversion approval
- settlement binding requirements

Use this document for:

- campaign or offer messages sent to wallets
- holder proof submission
- rollout and only-once proof interfaces
- encrypted grant or rejection payloads

## 2) Objectives

This offer-delivery profile aims to make the following true:

1) Brands define promotion rules and fund rewards.  
2) Promotions are delivered to wallet apps.  
3) Wallet apps locally decide which promotions matter (filtering).  
4) Purchases are already verified by the system (spend tokens).  
5) Wallet proves it qualifies without sharing receipt details (ZK statements over commitments).  
6) Each promotion has a unique identifier (`scopeId`).  
7) A wallet can only qualify once per promotion (`nullifier`).  
8) Wallets are consistently assigned to test groups (deterministic bucketing).  
9) Wallets cannot retry to get a better reward (anti-gaming for rollout assignment).  
10) The unlocked reward/promo is sent so only that wallet can see it (encryption to wallet delivery key).  

## 3) Non-goals

- No “user” object or protocol identity graph (wallets only).
- No full campaign language with arbitrary composition (beyond statement registry).
- No verified conversion settlement. See `../04-condition-layer/campaign-commitment.md`.
- No promise that campaigns are broadcast end-to-end encrypted (delivery encryption is specified; broadcast privacy is deferred).
- No reward policy math in-protocol (reward math is a Reward Layer concern; see `../05-reward-and-settlement/reward-layer.md` + `../05-reward-and-settlement/policy-layer.md`).

## 4) Actors and trust boundaries

- **Issuer (Crinkl protocol operator)**: signs `SpendAttestationTokenV1` (ground truth of verified spend). May publish verifier parameter registries.
- **Wallet**: receives non-portable witness material, generates eligibility proofs, and decrypts delivered promos.
- **Brand Verifier**: validates spend tokens + proofs locally and decides whether to grant a promo.
- **Relay (e.g., Crinkl infrastructure)**: transports messages. The protocol assumes the relay is **not** a secrecy boundary.

## 5) Canonical identifiers

### 5.1 Statement identity

Statements are defined in `zk-foundation.md` and `zk-proof-extension.md`.

- `statementId = "sha256:" + SHA-256(RFC8785_canonicalize(statement))`

### 5.2 Redemption scope and `scopeId`

`scopeId` defines where “only once” dedupe applies, without requiring wallet identity disclosure.

Canonical scope shape (from `zk-foundation.md`):

```text
RedemptionScopeV1 {
  schemaVersion: 1,
  scopeType: "REDEMPTION_SCOPE",
  verifierId: Identifier,         // the counterparty who enforces dedupe (e.g., a brand verifier)
  campaignId: Identifier,         // verifier-chosen id for a campaign/offer
  statementId: "sha256:" + Hash   // bind the scope to a specific statement shape+params
}
```

- `scopeId = "sha256:" + SHA-256(RFC8785_canonicalize(scope))`

### 5.3 Promo payload identity

Brands MAY define a `payloadId` (opaque) to identify a specific encrypted promo payload they return (e.g., to reference in an observation ack).

### 5.4 Predicate definition identity (`predicateId`) for pointer-based distribution

For closed-loop promos and external surfaces, distribution MUST reference a predicate pointer, not an audience list.

Minimum predicate definition shape for promo routing (`PredicateDefinitionV1`):

```text
PredicateDefinitionV1 {
  schemaVersion: 1,
  protocolVersion: Version,
  statementId: "sha256:" + Hash,
  routing: {
    cbsaCode: String,           // canonical CBSA code
    categorySlug: String        // canonical store category slug
  },
  exclusion: {
    storeId: Identifier,        // canonical store identifier (e.g., crinkl-store-*)
    lookbackDays: Integer       // recipient exclusion window for prior store spend
  },
  promoterGate: {
    minTokenUnits: String(Integer >= 0)
  },
  settlement: {
    recipientRewardUnits: String(Integer >= 0),
    promoterRewardUnits: String(Integer >= 0)
  }
}
```

Canonical identity:
- `predicateId = "sha256:" + SHA-256(RFC8785_canonicalize(predicateDefinition))`

Normative requirements:
- `statementId` MUST be computed per §5.1 and MUST be immutable once referenced by `predicateId`.
- `protocolVersion` MUST match campaign/proof artifacts used with this predicate.
- Predicate definitions MUST be immutable by version; changing any field produces a new `predicateId`.
- Distribution payloads MUST reference `predicateId` (and promo metadata) only; they MUST NOT contain materialized audience lists.
- `routing` / `exclusion` / `promoterGate` / `settlement` semantics are coordination-layer inputs and MUST NOT alter proof verification semantics.

## 6) Campaign message (brand → wallets)

This profile does not define broadcast transport. It defines the *portable campaign object* that may be carried by any transport.

```text
PromoCampaignV1 {
  schemaVersion: 1,
  protocolVersion: Version,

  verifierId: Identifier,     // brand/verifier identifier
  campaignId: Identifier,     // brand-chosen id

  // Eligibility rule
  statementId: "sha256:" + Hash,
  statement?: Object,         // OPTIONAL: included when rule disclosure is acceptable

  // Rollout parameters (controlled rollouts / A-B)
  variantCount: Integer,      // N > 0
  rolloutThreshold: Integer,  // in [0, N]

  // Confidential submission: wallets encrypt eligibility claims to this key.
  proofSubmissionPublicKeySpkiBase64: Base64,

  // Non-normative UI metadata (wallet filtering)
  display?: {
    title?: String,
    subtitle?: String,
    body?: String,
    brandName?: String,
    imageUrl?: String,
    ctaText?: String,
    expiresAt?: TimestampISO,
    termsUrl?: String
  }
}
```

**Verifier requirements (normative):**
- If `statement` is present, verifiers MUST recompute `statementId` and reject if it does not match.
- `variantCount` MUST be > 0.
- `rolloutThreshold` MUST be in `[0, variantCount]`.

## 7) Wallet eligibility claim (wallet → brand, via relay)

Wallets decide locally whether to engage a campaign. If they engage, they submit an eligibility claim.

### 7.1 Required fields

```text
PromoEligibilityClaimV1 {
  schemaVersion: 1,

  // Scope
  scope: RedemptionScopeV1,
  scopeId: "sha256:" + Hash,

  // Spend truth
  spendToken: SpendAttestationTokenV1,

  // Proof of eligibility for `statementId`
  spendProof: SpendZkStatementProofV1,

  // Rollout + only-once (one of the following)
  walletRolloutProof?: WalletRolloutProofV1,             // target: brand-verifiable
  rolloutAssignmentToken?: RolloutAssignmentTokenV1,     // v0.5: issuer-signed (extra trust)

  // Where to deliver the promo (wallet-generated, per-campaign key)
  deliveryPublicKeySpkiBase64: Base64

  // Demo profile convenience only (see §7.5)
  nullifier?: "sha256:" + Hash
}
```

**Encryption (normative):**
- The wallet MUST deliver `PromoEligibilityClaimV1` inside an encrypted envelope to `proofSubmissionPublicKeySpkiBase64` (see `encryption-envelopes.md`).

### 7.1a Promo binding profile (normative)

To keep offer delivery **brand-verifiable**, the verifier MUST be able to check that the eligibility proof and the rollout/only-once outputs are about the same promotion scope.

For `PromoEligibilityClaimV1`:

- `spendProof.publicInputs.scopeId` MUST be present and MUST equal `scopeId`.
- `spendProof.publicInputs.nullifier` MUST be present and MUST equal the rollout proof output `nullifier`.
- If the campaign uses controlled rollouts (A/B), then `spendProof.publicInputs.bucket`, `variantCount`, and `rolloutThreshold` MUST be present and MUST match the rollout proof output and campaign parameters.

**Cryptographic binding requirement:** verification of `spendProof` MUST fail if any of the bound values above are changed. (In a SNARK, these are public inputs; in a transcript-based proof system, they MUST be transcript-bound.)

### 7.2 Rollout proof (target: brand-verifiable, wallet-secret-derived)

To satisfy “consistent assignment” and “no retry”, a brand needs a verifier-checkable artifact that prevents a wallet from choosing its own bucket/nullifier.

This profile standardizes the **interface**; the proof system/circuit is versioned by `(proofSystem, circuitId, verifyingKeyId)`.

```text
WalletRolloutProofV1 {
  schemaVersion: 1,
  scopeId: "sha256:" + Hash,

  variantCount: Integer,
  rolloutThreshold: Integer,

  // Public outputs used by the verifier
  bucket: Integer,                 // in [0, variantCount)
  nullifier: "sha256:" + Hash,     // scope-specific, verifier-storable

  proofSystem: String,
  circuitId: String,
  verifyingKeyId: "sha256:" + Hash,
  publicInputs: Object,
  proof: Base64
}
```

**Normative semantics:**
- `nullifier` MUST be scope-specific (changes when `scopeId` changes).
- The verifier MUST store “seen” `nullifier` values and reject repeats for the same promotion scope (“only once per wallet per promotion”).
- The proof MUST convince the verifier that `bucket` and `nullifier` are correctly derived from wallet-private secret material and `scopeId` (anti-gaming).

> The wallet-secret nullifier derivation is defined in `zk-foundation.md`; circuits MUST enforce that derivation (or prove equivalence).

### 7.3 Rollout assignment token (v0.5 transitional, issuer-signed)

Some deployments may use an issuer-signed assignment until a wallet-secret-derived rollout proof is available.

This token is described in `zk-foundation.md` (“Deterministic bucketing”) and is explicitly **non-core** (see `token-extensions.md`).

**Important:** this is additional issuer trust and is not sufficient for the “brands rely only on spend tokens” target.

**1.0 target (normative intent):** deployments that aim for “brands rely only on spend tokens” MUST reject `rolloutAssignmentToken` and require `walletRolloutProof`.

### 7.4 Spend-scoped nullifier note (transitional)

Some implementations may additionally compute a **spend-scoped** anti-replay identifier:

- `spendNullifier = sha256(RFC8785({ v: 1, scopeId, spendTokenHash }))`

This is useful as a *per-spend* replay guard, but it is **precomputable** from public context and is not the privacy target for “only once per wallet per promotion”. A brand-verifiable 1.0 design SHOULD rely on the wallet-secret-derived `nullifier` (from `WalletRolloutProofV1`) for “only once”.

### 7.5 Demo profile (Halo2 promo, current implementation)

The v1 demo showcases the **advanced** promo flow using Halo2 proofs for real commerce predicates:
- Eligibility proofs use `SpendZkStatementProofV1` with:
  - `statement.type = "SPEND_STOREHASH_IN_ROOT_AND_TIMESTAMP_GTE_AND_TOTAL_GTE"`
  - `proofSystem = "HALO2_IPA"` and `circuitId = "H2_PROMO_V1"` (see `zk-circuit-catalog.md`).

To keep the demo runnable before wallet-secret rollout proofs are finalized, the demo profile allows:
- **No rollout proof when `variantCount = rolloutThreshold = 1`.** The verifier treats the wallet as always in rollout (implicit bucket=0).
- **Spend-scoped nullifier** derived as `sha256(RFC8785({ v: 1, scopeId, spendTokenHash }))` (see `zk-foundation.md`).
- **Optional top-level `nullifier` in the claim** for convenience; verifiers MUST still enforce `spendProof.publicInputs.nullifier`.

This demo profile is **non-normative** and intended to illustrate the Halo2-based statement capabilities; production deployments SHOULD use `WalletRolloutProofV1` once available.

**Demo decision payload (non-normative):** the demo harness may return a simplified decision object with
`type` (`PROMO_GRANT` / `PROMO_REJECTION`), `granted` (boolean), `arm` (`control`/`treatment`), and `observeNonce`
instead of the full `PromoGrantV1` / `PromoRejectionV1` shapes. Production deployments SHOULD use the normative
grant/rejection payloads defined in §9.

## 8) Brand verification procedure (normative)

Given a decrypted `PromoEligibilityClaimV1`, a brand verifier MUST:

1) Recompute `scopeId` from `scope` and verify it equals `scopeId`.  
2) Verify protocol version consistency:
   - the verifier MUST support the campaign’s declared `PromoCampaignV1.protocolVersion`
   - `spendToken.protocol.protocolVersion` MUST equal `PromoCampaignV1.protocolVersion`
   - `spendProof.statement.protocolVersion` MUST equal `PromoCampaignV1.protocolVersion`  
3) Verify `spendToken` per `../03-portability/spend-attestation-token.md` (signature + issuer authorization + acceptance policy).
4) Verify `spendProof` per `../03-portability/spend-attestation-token.md` and verify it proves `statementId` for the referenced spend token.
5) Enforce scope binding:
   - verify `spendProof.statementId` equals `scope.statementId`
   - verify `spendProof.publicInputs.scopeId` equals `scopeId`
   - verify `spendProof.publicInputs.nullifier` is present  
6) Verify rollout + only-once:
   - If `walletRolloutProof` is present: verify the proof and extract `(bucket, nullifier)`.
   - Else if `rolloutAssignmentToken` is present: verify the issuer signature and extract `(bucket, nullifier)` (transitional deployments only).
   - Else: reject (cannot enforce rollout/only-once).  
   - **Demo profile exception (non-normative):** if `variantCount = rolloutThreshold = 1` and the campaign is the Halo2 demo profile, a verifier MAY accept a claim without rollout proof, treat `bucket = 0`, and use `spendProof.publicInputs.nullifier` as the only-once key.
7) Cross-check consistency:
   - `spendProof.publicInputs.nullifier` MUST equal the rollout `nullifier`.
   - `spendProof.publicInputs.bucket`, `variantCount`, and `rolloutThreshold` MUST match the campaign’s rollout parameters.  
8) Determine the offer delivery key:
   - If `walletRolloutProof` is present: use `deliveryPublicKeySpkiBase64` from the claim.
   - If `rolloutAssignmentToken` is present: the claim’s `deliveryPublicKeySpkiBase64` MUST match the token’s delivery key; use the token’s value.
9) Only-once enforcement: if `nullifier` was already seen for this `scopeId`, reject. Otherwise store it.  
10) Determine control/treatment: `inRollout = (bucket < rolloutThreshold)`.  
11) If granting, encrypt a promo payload to the selected delivery key and return it.
12) If rejecting, return a `PromoRejectionV1` encrypted to the selected delivery key (see §9.2).

## 9) Promo decision (brand → wallet)

The brand returns exactly one encrypted decision payload per request: either a grant (§9.1) or a rejection (§9.2).

### 9.1 Promo grant

```text
PromoGrantV1 {
  schemaVersion: 1,
  scopeId: "sha256:" + Hash,
  nullifier: "sha256:" + Hash,
  payloadId: Identifier,
  arm: "TREATMENT" | "CONTROL",

  // Non-normative payload (coupon, link, instructions, etc.)
  promo: Object,

  grantedAt: TimestampISO
}
```

**Encryption (normative):**
- The brand MUST return `PromoGrantV1` inside an encrypted envelope to `deliveryPublicKeySpkiBase64` (see `encryption-envelopes.md`).

**Control arm guidance (normative intent):**
- For A/B experiments, brands SHOULD return a `PromoGrantV1` for both treatment and control (the difference is `arm` and the `promo` payload content, e.g., with vs without bonus points). This avoids “no response” ambiguity at the wallet.

### 9.2 Promo rejection (structured)

When rejecting an eligibility claim (invalid token/proof, already redeemed, unsupported version, etc.), brands SHOULD return a structured rejection so wallets can display deterministic outcomes and implement backoff/retry correctly.

```text
PromoRejectionV1 {
  schemaVersion: 1,
  scopeId: "sha256:" + Hash,
  nullifier: "sha256:" + Hash,
  payloadId: Identifier,

  rejection: {
    code: String,             // stable, machine-parseable identifier
    retryable: Boolean,
    message?: String,         // OPTIONAL human-readable string
    details?: Object          // OPTIONAL structured debug fields (MUST NOT include receipt details)
  },

  rejectedAt: TimestampISO
}
```

Recommended `rejection.code` values (non-exhaustive):
- `UNSUPPORTED_PROTOCOL_VERSION`
- `INVALID_SPEND_TOKEN`
- `INVALID_ELIGIBILITY_PROOF`
- `INVALID_ROLLOUT_PROOF`
- `DELIVERY_KEY_MISMATCH`
- `ALREADY_REDEEMED`

**Encryption (normative):**
- The brand MUST return `PromoRejectionV1` inside an encrypted envelope to `deliveryPublicKeySpkiBase64` (see `encryption-envelopes.md`).

## 10) Reward issuance and Reward Commitment Tokens

Offer eligibility and delivery are distinct from reward issuance:

- This offer-delivery profile MUST NOT require `RewardCommitmentTokenV1` as an eligibility input.
- Reward issuance is an economic consequence recorded by Reward Ledger events and (optionally) anchored by the Commitment Layer (`../05-reward-and-settlement/reward-layer.md`, `../01-core/spend-event.md`, `../05-reward-and-settlement/settlement-bindings.md`).
- `RewardCommitmentTokenV1` exists to provide **verifiable proof that rewards were actually issued** (economic non-repudiation), and MAY be used for:
  - brand reconciliation/invoicing,
  - audit, and
  - partner reporting.

**Privacy note (normative intent):** reward commitment tokens are recipient-scoped (`recipientId` is required). If brands receive reward commitment tokens, deployments SHOULD prefer blinded recipient schemas (`"1b"`/`"2b"`) to avoid creating a brand-visible wallet identity graph (see `../05-reward-and-settlement/settlement-bindings.md#recipient-blinding`).
