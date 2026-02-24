# ZK Circuit Catalog (v1)

> **Status: v1.0-ready for the demo statement set**
>
> This document is the missing “wiring layer” between:
> - a brand campaign’s **eligibility rule** (`statementId`), and
> - the **proof artifact** a verifier expects (`proofSystem`, `circuitId`, `verifyingKeyId`).
>
> The Promo Protocol does not define an arbitrary “campaign DSL”. Instead, campaigns reference **statement types** from a closed catalog, and each statement type has one or more supported proof circuits.

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

This triad is what a verifier pins and what conformance tests target. See `TOKENS.md` for the portable proof container `SpendZkStatementProofV1`.

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

Spend eligibility is proven with `SpendZkStatementProofV1` (see `TOKENS.md`), where `statementId` identifies the rule being proven.

**Positioning note:** Bulletproofs are suitable for **single-field range checks** (e.g., total ≥ threshold). The realistic promo demo uses **Halo2 IPA** to combine store membership + time window + total in one proof while keeping store sets private via a Merkle root.

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

**Required wallet witness openings:**
- `SpendZkWitnessV1.openings.totalCents` (value + blinding) MUST be present.

**Binding context (normative):**

Proof verification MUST fail if any of the following change:
- `spendId`
- `binding.headEventHash`
- `spendTokenHash`
- `statementId`
- `scopeId` (redemption scope binding)

**Promo binding profile (required when used inside the Promo Protocol):**

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

This statement type is designed to match the demo promo narrative (“apparel & footwear in the last 30 days”) while staying implementable with the current Spend commitments + wallet witness model.

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
- If `canonical.timestamp` is omitted from the portable token for privacy, the wallet witness MUST still carry `dayIndex` as the opening value for `C_dayIndex`.

**Required wallet witness openings:**
- `SpendZkWitnessV1.openings.dayIndex` MUST be present.

**Binding context (normative intent):**

Proof verification MUST fail if any of the following change:
- `spendId`
- `binding.headEventHash`
- `spendTokenHash`
- `statementId`
- `scopeId` (redemption scope binding)

**Promo binding profile (required when used inside the Promo Protocol):**

When this spend proof is used in a `PromoEligibilityClaimV1`:
- `publicInputs.scopeId` MUST equal the claim’s `scopeId`
- `publicInputs.nullifier` MUST be present
- `publicInputs.bucket`, `publicInputs.variantCount`, `publicInputs.rolloutThreshold` MUST be present when the campaign uses rollouts

And verification MUST fail if any of those values are changed. (In Bulletproofs, this means they MUST be transcript-bound.)

### 3.3 Statement type: `SPEND_STOREHASH_IN_ROOT_AND_DAYINDEX_GTE_AND_TOTAL_GTE` (realistic promo)

**Intent (realistic promo demo):**
- “Purchased at a store in this allowlist” (membership proof), AND
- “Purchase dayIndex is on/after `minDayIndex`”, AND
- “TotalCents ≥ thresholdCents”,
without revealing the store, dayIndex, or total.

**Supported circuits (v1 demo path):**

#### Circuit: `H2_PROMO_V1` (Halo2 IPA)

- `proofSystem`: `HALO2_IPA`
- `circuitId`: `H2_PROMO_V1`
- `verifyingKeyId`: `sha256:` hash of the circuit verifying key bytes (scheme-specific; verifiers MUST recompute and reject mismatches)
  - **Demo profile (current implementation):** `verifyingKeyId = sha256( UTF8( format!("{:?}", vk.pinned()) ) )`.
    This matches the demo prover today and is subject to change once a canonical Halo2 VK byte encoding is standardized.

**Required statement fields:**

```text
statement.domain = "crinkl:statement:v1"
statement.schemaVersion = 1
statement.type = "SPEND_STOREHASH_IN_ROOT_AND_DAYINDEX_GTE_AND_TOTAL_GTE"
statement.protocolVersion = Version

statement.storeSetRoot = "poseidon:" + Hex32          // Poseidon Merkle root
statement.minDayIndex = String(Integer >= 0)
statement.thresholdCents = String(Integer >= 0)
statement.currency = String(ISO-4217)
```

**Merkle root encoding (normative for this circuit):**
- `storeSetRoot` is a Poseidon hash over a fixed-depth binary Merkle tree.
- Leaves are `canonical.storeHash` values (32-byte SHA-256 digests) interpreted as field elements via modulo reduction.
- The tree depth is fixed by the circuit (**v1 demo uses depth = 4**).
- The root is encoded as 32-byte big-endian hex and prefixed with `poseidon:`.
- **Poseidon parameters (normative for H2_PROMO_V1):** Pasta Fp, `P128Pow5T3`, width=3, rate=2.
- **Store set construction (normative for H2_PROMO_V1):**
  - Normalize each store hash to lowercase `"sha256:" + hex32`.
  - Sort lexicographically and dedupe.
  - Pad to `2^depth` leaves using `emptyLeaf = Fp( "crnkl:store:empty" )` (the UTF-8 bytes reduced mod p).
  - Internal nodes are `Poseidon(left, right)` in positional order (no sorted-pair hashing).

**Merkle proof encoding (normative for H2_PROMO_V1):**
- `siblings`: array of `depth` elements, each encoded as `"poseidon:" + hex32` (sibling node).
- `pathBits`: string of length `depth` where each char is:
  - `"0"` = current node is the left child
  - `"1"` = current node is the right child

**Required token commitments:**
- `SpendAttestationTokenV1.zk.commitments.C_store`
- `SpendAttestationTokenV1.zk.commitments.C_dayIndex`
- `SpendAttestationTokenV1.zk.commitments.C_total`

**Committed value encoding (normative for this circuit):**
- `C_store` commits to `canonical.storeHash` (the SHA-256 store hash).
- `C_dayIndex` commits to `dayIndex = floor(Date.parse(canonical.timestamp) / 1000 / 86400)`.
- `C_total` commits to `canonical.totalCents`.

**Commitment encoding (normative for H2_PROMO_V1):**
- `spendIdHash = sha256(UTF8(spendId))` (prefixed as `"sha256:" + hex` in public inputs; the 32-byte digest is reduced to a field element inside the circuit).
- `labelConst = Fp( SHA256("crnkl:zk:commitment:v1:" || label) )` where `label ∈ {"C_store","C_dayIndex","C_total"}` and the hash bytes are reduced mod p.
- Commitment is Poseidon-chained as:
  - `h1 = Poseidon(labelConst, spendIdHash)`
  - `h2 = Poseidon(h1, headEventHash)`
  - `h3 = Poseidon(h2, value)`
  - `C = Poseidon(h3, blinding)`
- `value` is `canonical.storeHash` (32-byte digest → field element), `dayIndex`, or `canonical.totalCents` respectively.
- `blinding` is a 32-byte field element (base64 in wallet witness).

**Blinding derivation (demo profile, non-normative):**
- The demo derives each `blinding` deterministically as:
  - `blinding = Fp( SHA256("crnkl:zk:halo2:blinding:v1" || seed || label || spendId || headEventHash) )`
  - `seed` is issuer-controlled secret material (MUST NOT be public).

**Required wallet witness openings:**
- `SpendZkWitnessV1.openings.storeHash`
- `SpendZkWitnessV1.openings.dayIndex`
- `SpendZkWitnessV1.openings.totalCents`

**Public inputs (normative for H2_PROMO_V1):**
The proof MUST expose and bind the following public inputs:
- `spendIdHash` (sha256 of `spendId`)
- `binding.headEventHash`
- `spendTokenHash`
- `statementId`
- `scopeId`
- `nullifier`
- `storeSetRoot`
- `minDayIndex`
- `thresholdCents`
- `commitmentStore`
- `commitmentDayIndex`
- `commitmentTotal`

`commitmentStore`, `commitmentDayIndex`, and `commitmentTotal` are encoded as `"poseidon:" + hex32` (field element).

#### Circuit slimming guidance (non-normative)

These are the highest impact levers for on-device proving. They change *what* is proven while preserving the same guarantees.

1) **Merkle depth is the main cost driver**
   - Each extra level adds a Poseidon hash and many constraints.
   - Store set size only matters if it forces a deeper tree.

2) **Use smaller range checks when possible**
   - Prefer 32-bit cents if max spend fits (< $42M).
   - Use day indexes (days since epoch) instead of timestamps in seconds.
   - Collapse multiple range checks into a single bound where feasible.

3) **Minimize commitments / hashes**
   - Commit to fewer fields, or pack values before hashing.
   - Avoid re-hashing derived values; reuse wires.

4) **Avoid expensive boolean logic**
   - Replace conditionals/comparisons with arithmetic identities.
   - Move checks outside the circuit if the protocol allows it.

#### Promo circuit slimming checklist (H2_PROMO_V1 family)

- **Depth:** pick the smallest Merkle depth that still fits the allowlist size.
  - depth 4 → 16 stores
  - depth 5 → 32 stores
  - depth 6 → 64 stores
  - depth 8 → 256 stores
  - depth 12 → 4,096 stores
  - depth 16 → 65,536 stores
  - depth 20 → 1,048,576 stores
- **Cents range:** if max spend < $42M, use 32-bit cents (avoid 64-bit range checks).
- **Time range:** prefer day indexes (days since epoch) instead of seconds timestamps.
- **Range checks:** if issuance already bounds totals/timestamps, only range-check the *diff* (`total - threshold`, `dayIndex - minDayIndex`) inside the circuit.
- **Commitments:** keep only the required commitments (`C_store`, `C_dayIndex`, `C_total`) and avoid extra hashes/packings unless you’re intentionally changing the statement shape.
- **k:** use the smallest k that still fits the circuit (don’t overprovision).

#### Recommended demo profile (proposal)

This profile is sized for “realistic promo” on-device proving and is meant for a **slimmed circuit variant**:

- **Depth:** 4 (max 16 stores)
- **Total/threshold:** 32-bit cents
- **Time:** day index (days since epoch) with a 32-bit bound
- **Commitments:** `C_store`, `C_dayIndex`, `C_total`
- **Statement:** `storeSetRoot + minDayIndex + thresholdCents` (promo statement)

The current demo encodes **dayIndex** (32-bit) and uses depth 4.

**Public input encoding note (H2_PROMO_V1):**
- `*Hash`, `*Id`, and `nullifier` use `"sha256:" + hex`.
- `storeSetRoot` and `commitment*` use `"poseidon:" + hex32`.
- `minDayIndex` and `thresholdCents` are unsigned integers (numeric).

Verifiers MUST reject if any of these values change, or if `publicInputs` do not match the statement fields.

**Promo binding profile (required when used inside the Promo Protocol):**

When this spend proof is used in a `PromoEligibilityClaimV1`:
- `publicInputs.scopeId` MUST equal the claim’s `scopeId`
- `publicInputs.nullifier` MUST be present
- `publicInputs.bucket`, `publicInputs.variantCount`, `publicInputs.rolloutThreshold` MUST be present when the campaign uses rollouts

## 3.4 v1 demo profile (what 1.0 supports)

For v1.0, the protocol supports a demo brand campaign by constraining eligibility to statement types that exist in this catalog.

The v1 demo statement types are:
- `SPEND_TOTAL_CENTS_GTE` (Bulletproofs range proof over `C_total`)
- `SPEND_STOREHASH_IN_SET_AND_DAYINDEX_GTE` (store allowlist + Bulletproofs range proof over `C_dayIndex`)
- `SPEND_STOREHASH_IN_ROOT_AND_DAYINDEX_GTE_AND_TOTAL_GTE` (private store + time window + total, Halo2 IPA)

This is sufficient to demonstrate the **end-to-end promo protocol** (campaign → wallet filter → claim → brand verification → encrypted decision) with real ZK statement proofs.

## 3.5 How “category in last 30 days” is expressed in v1

The v1 demo predicate “apparel & footwear in the last 30 days” is represented as:

- `allowedStoreHashes`: the set of store hashes that the verifier considers part of the “Apparel & Footwear” category, and
- `minDayIndex`: the lower bound for “last 30 days”.

In other words, “category” is expressed as a **store allowlist** at verification time.

How the verifier gets the allowlist is outside the ZK proof system and is typically one of:
- derived from a signed Store Registry snapshot (`STORE_REGISTRY.md`), using `StoreEntryV1.categories`, or
- a verifier-curated allowlist (explicitly not a new protocol trust root; it’s the verifier’s campaign definition).

This gives v1 a complete, interoperable path to run the demo promo end-to-end without introducing a SNARK/STARK/zkVM yet.

**Scaling note (non-normative):** to avoid large statements, future statement types can replace explicit `allowedStoreHashes` with a committed set reference (e.g., Merkle root) and require a set-membership circuit (typically SNARK/STARK/zkVM) when the verifier does not want to reveal the allowlist.

## 4) Rollout + only-once circuits (wallet rollout proofs)

Promos need a second artifact that prevents bucket/nullifier gaming:
- deterministic rollout assignment (`bucket`), and
- “only once per wallet per scope” (`nullifier`),
without exposing a stable wallet identifier.

This is expressed as `WalletRolloutProofV1` in `PROMO_PROTOCOL.md`.

### 4.1 Transitional path (v0.5)

Until a wallet-secret-derived rollout proof is deployed, implementations MAY use:
- `RolloutAssignmentTokenV1` (issuer-signed; defined in `ZK_FOUNDATION.md`).

This is explicitly additional issuer trust and is not the long-term “brands rely only on spend tokens” target.

### 4.2 Target path (brand-verifiable)

**Minimum requirement (normative intent):**

`WalletRolloutProofV1` MUST convince the verifier that:
- `nullifier` is derived from wallet-private secret material and `scopeId`, and
- `bucket` is derived from the same wallet-private secret material and `scopeId`, with `bucket ∈ [0, variantCount)`,
so the wallet cannot “retry” to get a better bucket.

**Catalog entry (placeholder):**

For v1, the interface is fixed (`WalletRolloutProofV1`), but the concrete circuit is still under selection (SNARK vs zkVM).

Once selected, this catalog MUST be updated to include at least one concrete entry like:

```text
proofSystem: "ZKVM_*" or "PLONK_*" or "STARK_*"
circuitId:   "WALLET_ROLLOUT_V1"
verifyingKeyId: sha256(...) (pinned verifier parameters)
public outputs: { bucket, nullifier }
public inputs:  { scopeId, variantCount, rolloutThreshold }
private inputs: { walletSecret }
```

## 5) What v1 enables (practical)

With the catalog entries above, a v1 promo verifier can implement a stable rule:
- if the campaign’s `statement.type` is supported (e.g., `SPEND_TOTAL_CENTS_GTE`), verify the spend proof,
- then verify rollout/only-once using either:
  - `RolloutAssignmentTokenV1` (transitional), or
  - `WalletRolloutProofV1` (target).

More complex campaigns (multiple predicates, set membership, time windows) are added by defining additional statement types and listing their supported circuits here.
