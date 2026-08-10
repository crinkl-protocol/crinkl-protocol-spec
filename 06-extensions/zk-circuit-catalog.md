---
status: experimental
layer: extension
version: v1
normative: true
---

# ZK Circuit Catalog (v1)

> **Status: v1 optional extension — current beta profile plus reserved future profiles**
>
> This document is the missing “wiring layer” between:
> - a brand campaign’s **eligibility rule** (`statementId`), and
> - the **proof artifact** a verifier expects (`proofSystem`, `circuitId`, `verifyingKeyId`).
>
> The offer-delivery profile in `offer-delivery-profile.md` does not define arbitrary campaign rules. Campaign rule composition uses `../protocol/applications/conditions/campaign-commitment.md`; this catalog maps referenced **statement types** to supported proof circuits.
>
> Implementation status: `H2_PROMO_OPEN_MIN_V1` is the current public beta
> profile. Additional private-witness proof profiles are release-reserved until
> Crinkl publishes a concrete circuit entry, verifier registry entry, public
> input order, and conformance vectors for that profile.

## 1) What this catalog is for

Engineers need a deterministic answer to:

1) “If a campaign says `statement.type = X`, what proof system / circuit verifies it?”  
2) “What must be bound into the proof so it can’t be replayed for a different spend or campaign?”  

This document provides those answers for v1.

## 2) Keying and identifiers (normative)

All portable proofs MUST carry:
- `proofSystem`
- `circuitId`
- `verifyingKeyId`

This triad is what a verifier pins and what conformance tests target. See `../protocol/portability/spend-attestation-token.md` for the portable proof container `SpendZkStatementProofV1`.

### 2.1 `verifyingKeyId` for systems without “verifying key bytes”

Some proof systems (e.g., Bulletproofs) parameterize verification by a small set of values (like `bits`) rather than a file of key bytes.

In these cases:

```text
verifyingKeyId = "sha256:" + SHA-256( RFC8785_canonicalize({
  domain: "crnkl:zk:vk:v1",
  proofSystem,
  circuitId,
  ...verifierParams
}))
```

Verifiers MUST recompute `verifyingKeyId` from the same canonical JSON and reject mismatches.

## 3) Spend eligibility circuits (statement proofs)

Spend eligibility is proven with `SpendZkStatementProofV1` (see `../protocol/portability/spend-attestation-token.md`), where `statementId` identifies the rule being proven.

**Positioning note:** Bulletproofs are suitable for **single-field range
checks** (e.g., total >= threshold). Public beta acceptance is limited to
published verifier registry entries and conformance vectors.

### 3.1 Statement type: `SPEND_TOTAL_CENTS_GTE`

**Intent:** prove `canonical.totalCents ≥ thresholdCents` without revealing `totalCents`.

**Supported circuits (v1):**

#### Circuit: `BP_TOTAL_GTE_V2` (Bulletproofs)

- `proofSystem`: `BULLETPROOFS`
- `circuitId`: `BP_TOTAL_GTE_V2`
- `verifyingKeyId`: computed per §2.1 with `verifierParams = { bits }`

**Required statement fields:**

```text
statement.domain = "crinkl:statement:v1"
statement.schemaVersion = 1
statement.type = "SPEND_TOTAL_CENTS_GTE"
statement.field = "canonical.totalCents"
statement.thresholdCents = String(Integer >= 0)
statement.currency = String(ISO-4217)
statement.protocolVersion = Version
```

**Required token commitments:**
- `SpendAttestationTokenV1.zk.commitments.C_total` MUST be present.

**Required private witness openings:**
- `SpendZkWitnessV1.openings.totalCents` (value + blinding) MUST be present.

**Binding context (normative):**

Proof verification MUST fail if any of the following change:
- `spendId`
- `binding.headEventHash`
- `spendTokenHash`
- `statementId`
- `scopeId` (redemption scope binding)

**Offer-delivery binding profile (required when used inside `offer-delivery-profile.md`):**

When this spend proof is used in a `PromoEligibilityClaimV1`:
- `publicInputs.scopeId` MUST equal the claim’s `scopeId`
- `publicInputs.nullifier` MUST be present
- `publicInputs.bucket`, `publicInputs.variantCount`, `publicInputs.rolloutThreshold` MUST be present when the campaign uses rollouts

And verification MUST fail if any of those values are changed. (In Bulletproofs, this means they MUST be transcript-bound.)

### 3.2 Statement type: `SPEND_STOREHASH_IN_SET_AND_TIMESTAMP_GTE` (demo promo)

**Intent (v1 demo):**
- “Purchased at a store in this allowlist” (storeHash check), AND
- “Purchase timestamp is on/after `minTimestamp`” (time-window foundation),
without revealing the actual timestamp.

This statement type is designed to match the demo promo narrative (“apparel &
footwear in the last 30 days”) while staying implementable with the current
Spend commitments + private witness model.

**Supported circuits (v1):**

#### Circuit: `BP_DAYINDEX_GTE_V1` (Bulletproofs)

- `proofSystem`: `BULLETPROOFS`
- `circuitId`: `BP_DAYINDEX_GTE_V1`
- `verifyingKeyId`: computed per §2.1 with `verifierParams = { bits }`

**Required statement fields:**

```text
statement.domain = "crinkl:statement:v1"
statement.schemaVersion = 1
statement.type = "SPEND_STOREHASH_IN_SET_AND_DAYINDEX_GTE"
statement.protocolVersion = Version

statement.minDayIndex = String(Integer >= 0)
statement.allowedStoreHashes = [ "sha256:" + Hash ]  // array MUST be sorted lexicographically
```

**Eligibility verification (normative intent):**

The verifier MUST:
1) verify the spend proof `BP_DAYINDEX_GTE_V1` (dayIndex is ≥ `minDayIndex`), and
2) verify `spendToken.canonical.storeHash ∈ statement.allowedStoreHashes`.

**Required token commitments:**
- `SpendAttestationTokenV1.zk.commitments.C_dayIndex` MUST be present.

**Committed value encoding (normative for this circuit):**
- The value committed under `C_dayIndex` MUST be `dayIndex = floor(Date.parse(canonical.timestamp) / 1000 / 86400)`.
- If `canonical.timestamp` is omitted from the portable token for privacy, the
  private witness MUST still carry `dayIndex` as the opening value for
  `C_dayIndex`.

**Required private witness openings:**
- `SpendZkWitnessV1.openings.dayIndex` MUST be present.

**Binding context (normative intent):**

Proof verification MUST fail if any of the following change:
- `spendId`
- `binding.headEventHash`
- `spendTokenHash`
- `statementId`
- `scopeId` (redemption scope binding)

**Offer-delivery binding profile (required when used inside `offer-delivery-profile.md`):**

When this spend proof is used in a `PromoEligibilityClaimV1`:
- `publicInputs.scopeId` MUST equal the claim’s `scopeId`
- `publicInputs.nullifier` MUST be present
- `publicInputs.bucket`, `publicInputs.variantCount`, `publicInputs.rolloutThreshold` MUST be present when the campaign uses rollouts

And verification MUST fail if any of those values are changed. (In Bulletproofs, this means they MUST be transcript-bound.)

### 3.3 Broader campaign proof profiles (not public beta)

Broader campaign predicates that hide store sets or bind additional business
context are release-reserved. They are not public beta claims until Crinkl
publishes a dedicated profile with:

- statement type and circuit identifier
- verifier registry entry and artifact/profile hash
- public input order
- conformance vectors and expected failure matrix
- privacy and custody disclosure

Verifiers MUST NOT infer support for these profiles from roadmap language,
platform behavior, or a hosted API response.

### 3.4 Current alpha direct-store profile: `H2_PROMO_OPEN_MIN_V1`

**Intent (alpha current-business profile):**

Prove that a verified spend opens a promo because:

- the private `storeHash` equals the public `expectedStoreHash`,
- the private `dayIndex` is greater than or equal to `minDayIndex`, and
- the private `totalCents` is greater than or equal to `thresholdCents`.

This is a direct-store profile. It does not prove store-set membership and MUST NOT be described as proving CBSA inside ZK.

**Supported circuit:**

#### Circuit: `H2_PROMO_OPEN_MIN_V1` (Halo2 IPA)

- `proofSystem`: `HALO2_IPA`
- `circuitId`: `H2_PROMO_OPEN_MIN_V1`
- `verifyingKeyId`: `sha256:` hash of the pinned Halo2 verifier profile.
  - Alpha implementation profile: `sha256( UTF8( format!("{:?}", vk.pinned()) ) )`.
  - Public beta MUST publish the exact registry entry and artifact/profile hash used by external verifiers.

**Required statement fields:**

```text
statement.domain = "crinkl:statement:v1"
statement.schemaVersion = 1
statement.type = "SPEND_STOREHASH_EQ_AND_DAYINDEX_GTE_AND_TOTAL_GTE"
statement.protocolVersion = Version

statement.expectedStoreHash = "sha256:" + Hex32
statement.minDayIndex = String(Integer >= 0)
statement.thresholdCents = String(Integer >= 0)
statement.currency = String(ISO-4217)
```

**Required token commitments:**

- `SpendAttestationTokenV1.zk.commitments.C_store`
- `SpendAttestationTokenV1.zk.commitments.C_dayIndex`
- `SpendAttestationTokenV1.zk.commitments.C_total`

**Required private witness openings:**

- `SpendZkWitnessV1.openings.storeHash`
- `SpendZkWitnessV1.openings.dayIndex`
- `SpendZkWitnessV1.openings.totalCents`

**Public inputs (normative for H2_PROMO_OPEN_MIN_V1):**

The proof MUST expose and bind the following public inputs in this exact order:

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

**Encoding:**

- `spendIdHash`, `headEventHash`, `spendTokenHash`, `statementId`, `scopeId`, `nullifier`, and `expectedStoreHash` use `"sha256:" + hex32`.
- `commitmentStore`, `commitmentDayIndex`, and `commitmentTotal` use `"poseidon:" + hex32`.
- `minDayIndex` and `thresholdCents` are unsigned integers.

**Verification failure matrix:**

Verification MUST fail if any of the following change:

- `proofSystem`
- `circuitId`
- `verifyingKeyId`
- `spendIdHash`
- `headEventHash`
- `spendTokenHash`
- `statementId`
- `scopeId`
- `nullifier`
- `expectedStoreHash`
- `minDayIndex`
- `thresholdCents`
- any commitment public input
- proof bytes

The consuming verifier or gateway MUST reject replayed `nullifier` values in the relevant `scopeId`.

**Release-profile rule:** `H2_PROMO_OPEN_MIN_V1` is the only current public
beta profile in this catalog. Broader campaign, geography-bound, or multi-actor
proof profiles require a separate release-profile publication before any public
support claim.

## 3.5 Public beta profile (what is supported now)

For public beta, a verifier MUST constrain eligibility to statement types that
have a published verifier registry entry and conformance vector set.

The current public beta statement profile is:

- `SPEND_STOREHASH_EQ_AND_DAYINDEX_GTE_AND_TOTAL_GTE` with
  `H2_PROMO_OPEN_MIN_V1`

This is sufficient to demonstrate independent beta verification for the current
direct-store proof artifact without exposing future release-profile internals.

## 3.6 How “category in last 30 days” is expressed in v1

The v1 demo predicate “apparel & footwear in the last 30 days” is represented as:

- `allowedStoreHashes`: the set of store hashes that the verifier considers part of the “Apparel & Footwear” category, and
- `minDayIndex`: the lower bound for “last 30 days”.

In other words, “category” is expressed as a **store allowlist** at verification time.

How the verifier gets the allowlist is outside the ZK proof system and is typically one of:
- derived from a signed Store Registry snapshot (`store-registry.md`), using `StoreEntryV1.categories`, or
- a verifier-curated allowlist (explicitly not a new protocol trust root; it’s the verifier’s campaign definition).

This gives v1 a complete, interoperable path to run the public beta
offer-opening flow end-to-end without requiring private rollout proofs yet.

**Scaling note (non-normative):** future profiles can replace explicit
allowlists with committed references when Crinkl publishes a dedicated release
profile. Until then, public beta verifier claims are limited to published
registry entries and vectors.

## 4) Rollout + only-once circuits (private rollout proofs)

Promos need a second artifact that prevents bucket/nullifier gaming:
- deterministic rollout assignment (`bucket`), and
- “only once per wallet per scope” (`nullifier`),
without exposing a stable wallet identifier.

This is expressed as `WalletRolloutProofV1` in `offer-delivery-profile.md`.
The reserved type name does not imply near-term mobile or client-device proving.

### 4.1 Transitional path (v0.5)

Until a private rollout proof is deployed, implementations MAY use:
- `RolloutAssignmentTokenV1` (issuer-signed; defined in `zk-foundation.md`).

This is explicitly additional issuer trust and is not the long-term “brands rely only on spend tokens” target.

### 4.2 Target path (brand-verifiable)

**Minimum requirement (normative intent):**

`WalletRolloutProofV1` MUST convince the verifier that:
- `nullifier` is derived from private holder/prover secret material and
  `scopeId`, and
- `bucket` is derived from the same private holder/prover secret material and
  `scopeId`, with `bucket ∈ [0, variantCount)`,
so the holder cannot “retry” to get a better bucket.

**Catalog entry (placeholder):**

For v1, the interface is reserved (`WalletRolloutProofV1`), but the concrete
prover boundary, proof system, circuit identifier, and verifier profile are not
part of this public beta catalog. A deployment MUST NOT claim support for
private rollout proofs until this catalog contains a concrete `proofSystem`,
`circuitId`, and `verifyingKeyId` profile.

## 5) What v1 enables (practical)

With the catalog entries above, a v1 promo verifier can implement a stable rule:
- if the campaign’s `statement.type` is supported (e.g., `SPEND_TOTAL_CENTS_GTE`), verify the spend proof,
- then verify rollout/only-once using either:
  - `RolloutAssignmentTokenV1` (transitional), or
  - `WalletRolloutProofV1` (reserved future interface).

More complex campaigns are added only by defining additional statement types and
listing their supported circuits here with matching registry entries and
conformance vectors.
