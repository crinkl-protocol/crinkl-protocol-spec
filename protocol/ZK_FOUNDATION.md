# ZK Foundation (Minimum Viable Promo Flow)

> **Status: explanatory / demo foundation for optional ZK proofs**
>
> This document describes the minimum proof spine for proof-backed offer opening. It is not required for core Spend Token validity, does not define campaign settlement, and does not make wallet-secret rollout proofs production-ready.

This document captures the **minimum ZK foundation** needed to support a simple brand promo use case in v1.0.

Example v1 promo predicates:

- “If `canonical.totalCents >= 1000`, grant promo”
- “If `canonical.storeHash ∈ allowlist` AND `canonical.timestamp ≥ now - 30 days`, grant promo”

It is intentionally **not** a complex campaign DSL. It defines the proof spine we can build on, while keeping v1 statement types closed and interoperable. Campaign rule composition is defined separately in `CAMPAIGN_SPEND_PROOF_PRIMITIVES.md`.

For the normative offer-delivery wire formats (campaign message, eligibility claim, encrypted delivery), see `PROMO_PROTOCOL.md` and `ENCRYPTION_ENVELOPES.md`.

## Goal

Enable a user (or platform) to prove **eligibility** for a promo using a verified spend, without revealing the underlying receipt or the total amount.
This implements the **selective disclosure** pattern from verifiable credentials: the holder (wallet owner) can prove specific predicates about a credential (spend attestation) without revealing the full claim contents.

| VC Pattern | Crinkl ZK Realization |
|------------|----------------------|
| **Credential** | Spend Attestation Token with `zk.commitments` |
| **Holder** | Wallet owner with decrypted witness material |
| **Selective Disclosure** | ZK statement proof (e.g., "total ≥ threshold") |
| **Verifier** | Brand verifying proof without learning receipt details |
| **Anti-Replay** | `scopeId` + `nullifier` for redemption scoping |
## Non-goals (for now)

- No SKU-level / line-item rules
- No category sets, co-purchase rules, or audience segmentation
- No cross-spend aggregation (“spent >= X over N days”)
- No full “campaign language” with arbitrary composition

## Target end-to-end flow (receipt total > 1000 → promo)

1) **Upload**: user uploads receipt via PWA; Crinkl binds submission to wallet → `spendId`
2) **Verify**: pipeline emits `SPEND_SOFT_VERIFIED` then `SPEND_HARD_VERIFIED` (canonical fields include `totalCents`)
3) **Attest**: Crinkl issues `SpendAttestationTokenV1`:
   - signed
   - includes the required `zk.commitments` bound to (`spendId`, `lineage.headEventHash`) for the statement type being proven (e.g., `C_total`, `C_dayIndex`)
   - **portable token omits the committed field** (selective disclosure via ZK proof)
4) **Campaign arrives**: brand publishes a campaign referencing a `statementId` for the eligibility rule and provides a brand public key + endpoints
5) **Local check + proof** (client-side option): PWA decrypts wallet-only witness and generates `SpendZkStatementProofV1`
6) **Blind send**: PWA encrypts the proof to the brand’s public key; sends via relay (platform can’t read it)
7) **Verify + grant**: brand verifies token + statementId + proof; returns an encrypted promo artifact
8) **Display**: PWA decrypts and displays promo

## Demo support boundary

The demo profile can illustrate the proof spine without making every transport or settlement surface normative:

- demo/implementation surfaces: PWA UX, campaign delivery, relay, and brand offer issuance
- normative proof spine: commitments, wallet witness, proof binding rules, and verifier behavior

The demo can use scripts to act as PWA and verifier simulators. Those scripts are not the protocol.

## The spine (minimal primitives to standardize)

### 1) Spend Attestation Token (portable)

Already defined in `TOKENS.md`:
- `SpendAttestationTokenV1` MAY include `zk.commitments`
- portable tokens MUST remain receipt-private

For the foundation flow, portable spend tokens SHOULD omit any spend fields that are being selectively disclosed via ZK (e.g., omit `canonical.totalCents` and/or `canonical.timestamp`) and rely on:
- `zk.commitments` and a proof artifact for eligibility

### 2) Wallet witness envelope (new, non-portable)

To support **client-side proving**, the user needs “opening material” for the commitment(s) required by the statement (e.g., `C_total` and/or `C_dayIndex`).

This must be **wallet-only** and **not** part of the portable token.

Minimum requirements (see `TOKENS.md#optional-wallet-witness-non-portable-normative`):
- encrypted to a wallet-controlled public key
- bound to (`spendTokenHash`, `headEventHash`) so corrections naturally invalidate old witness
- includes only the minimum opening material needed to generate proofs (no receipt/OCR ingestion artifacts)

This envelope can be defined as a separate artifact (not a “token”) alongside spend tokens.

### 3) Statement identity (minimal, not a DSL)

Keep the existing pattern:
- `statementId = sha256(RFC8785_canonicalize(statementDefinition))`

For v1, statement types are a closed set captured in `ZK_CIRCUIT_CATALOG.md`. The foundation introduces two statement families that are sufficient to support the demo promo flow end-to-end.

Foundation statement example A (normative):

```text
SpendTotalCentsGteStatementV1 {
  domain: "crinkl:statement:v1",
  schemaVersion: 1,
  protocolVersion: Version,
  type: "SPEND_TOTAL_CENTS_GTE",
  field: "canonical.totalCents",
  thresholdCents: Amount
}
```

Foundation statement example B (normative intent; full mapping in `ZK_CIRCUIT_CATALOG.md`):

```text
SpendStoreHashInSetAndDayIndexGteStatementV1 {
  domain: "crinkl:statement:v1",
  schemaVersion: 1,
  protocolVersion: Version,
  type: "SPEND_STOREHASH_IN_SET_AND_DAYINDEX_GTE",
  minDayIndex: String(Integer >= 0),
  allowedStoreHashes: [ "sha256:" + Hash ]  // array MUST be sorted
}
```

**Private store + time + total (realistic promo):** for a single proof that hides store, timestamp, and total while proving all three predicates, see the composite statement type in `ZK_CIRCUIT_CATALOG.md` (`SPEND_STOREHASH_IN_ROOT_AND_DAYINDEX_GTE_AND_TOTAL_GTE`).

**Demo profile (advanced):** the current demo uses `HALO2_IPA` / `H2_PROMO_V1` to combine store membership + time window + total in a single proof. This is the scalable path beyond Bulletproof-only range proofs for real promo campaigns.

**Canonicalization (normative):** verifiers MUST compute `statementId` over the RFC 8785 canonical JSON of the statement object, and MUST reject unknown `domain` or unsupported `schemaVersion`.

Routing/distribution predicates MAY reference `statementId` via a separate predicate definition and `predicateId` (see `PROMO_PROTOCOL.md`); this does not alter statement verification semantics.

This document does not standardize campaign types. Campaign rule composition is defined in `CAMPAIGN_SPEND_PROOF_PRIMITIVES.md`.

### 4) Proof binding rules (tighten what must be bound)

For replay-resistance and unambiguous verification, a proof for this foundation use case MUST be bound to:

- `spendId`
- `lineage.headEventHash`
- `statementId`
- **`spendTokenHash`** (so a proof can’t be replayed across token re-issuances)

**Where the binding lives (normative):**
- The spend token signature already binds `spendId`, `headEventHash`, and the included commitments.
- The ZK proof MUST additionally bind to `spendTokenHash` and `statementId` so that a proof cannot be swapped between tokens or between statements.

#### Binding split: inside proof vs outside (normative)

For portability and replay-resistance, verifiers MUST treat the following as required binding locations:

- **MUST be inside the proof statement (public inputs or transcript binding):**
  - `spendId`
  - `headEventHash`
  - `statementId`
  - `spendTokenHash`

- **SHOULD be bound by the signed spend token (and checked before trusting the proof):**
  - commitment values (e.g., `zk.commitments.C_total`)
  - token `schemaVersion` and `protocol.protocolVersion` (semantic gate)

- **If the proof is used for redemption (anti-replay), it MUST additionally include:**
  - `scopeId`
  - a verifier-storable, scope-specific `nullifier` (see §5) so the verifier can enforce “only once”

See `TOKENS.md#optional-zk-statement-proof-normative` for the portable proof bundle shape and verification steps.

### 5) Anti-replay for redemption (defer, but reserve)

Promo redemption adds a new problem: “don’t allow the same spend to be redeemed repeatedly”.

We do not need the full design now, but we SHOULD reserve two **neutral** (non-brand-specific) primitives that make redemption privacy-preserving:

#### A) `RedemptionScopeV1` and `scopeId`

A **redemption scope** defines *where* a redemption is considered “the same” for dedupe / rate limiting, without requiring the verifier to learn wallet identity.

Recommended shape (draft):

```text
RedemptionScopeV1 {
  schemaVersion: 1,
  scopeType: "REDEMPTION_SCOPE",
  verifierId: Identifier,         // the counterparty who enforces dedupe (e.g., a brand verifier)
  campaignId: Identifier,         // verifier-chosen id for a campaign/offer
  statementId: "sha256:" + Hash   // bind the scope to a specific statement shape+params
}
```

`scopeId` SHOULD be computed as:
- `scopeId = sha256(RFC8785_canonicalize(scope))`

#### B) `nullifier` (campaign-scoped anti-replay)

A **nullifier** is a verifier-storable, scope-specific identifier that allows “only once” redemption **without revealing** the wallet.

There are two useful anti-replay semantics (both compatible with this protocol surface):

- **Spend-scoped nullifier (demo-supported, per-spend anti-replay):**
  - `nullifier = sha256(RFC8785({ v: 1, scopeId, spendTokenHash }))`
  - Enforces: “only once per *(scopeId, spendTokenHash)*”.
  - Note: this is not wallet-secret; a verifier can compute it from public context. It prevents double redemption of the same spend within a scope, but does not prove wallet possession.

- **Wallet-secret nullifier (normative, privacy-preserving):**
  - Inputs: `walletSecrets` (array of 32-byte hex secrets, lowercase, no prefix) and `scopeId`.
  - Normalize each secret to lowercase hex (no prefix) and sort lexicographically.
  - `masterSecret = sha256(RFC8785({ v: 1, walletSecrets }))`
  - `nullifier = sha256(RFC8785({ v: 1, scopeId, masterSecret }))`
  - `masterSecret` is represented as lowercase hex (no prefix).
  - `nullifier` is represented as `"sha256:" + Hash`.
  - For a single wallet, `walletSecrets` has one entry. For cross-wallet proofs, all participating wallet secrets MUST be included; sorting makes the derivation order-independent.
  - Enforces: “only once per wallet (or wallet group) per scope” without revealing wallet identity and without allowing verifier precomputation.

High-level requirements (normative):
- `nullifier` MUST be scope-specific (changes when `scopeId` changes).
- `nullifier` MUST be included in redemption proofs as a public output (or public input) so verifiers can store “seen nullifiers”.

> The proof system MUST enforce the derivation above (e.g., by computing it inside the circuit or proving equivalence to the declared hash).

This can be added later without changing the spend token format.

#### C) Deterministic bucketing (controlled rollouts / A/B)

Brands often want a controlled rollout (A/B testing): “for this `scopeId`, deterministically assign each eligible wallet to control/treatment, and enforce only-once redemption per wallet per scope”.

This protocol can support that without introducing a user/identity layer, but there is an important sequencing:

- **Near-term (recommended, non-ZK):** keep brands blind to the wallet by using an **issuer-signed rollout assignment** that carries a scope-bound bucket + nullifier, plus a per-scope delivery key. This uses the same audit-friendly primitives as the rest of the protocol (RFC8785 + SHA-256 + Ed25519) and does not require a SNARK/STARK circuit.
- **Target (privacy-preserving ZK):** move the same bucketing/nullifier computation **inside the proof system** so the verifier does not need (or receive) any issuer-signed assignment and does not learn a stable wallet key.

**A practical v0.5 construction (non-normative, recommended until a circuit exists):**

- Wallet generates a **per-scope delivery key** `deliveryPublicKeySpkiBase64` (fresh per campaign/scope) for promo encryption.
- Issuer computes wallet-scoped outputs (issuer-only anchor, not exposed):
  - `walletNullifier = sha256(RFC8785({ v: 1, scopeId, walletAnchor, purpose: "redeem" }))`
  - `bucketSeed = sha256(RFC8785({ v: 1, scopeId, walletAnchor }))`
  - `bucket = int_be(bucketSeed) mod N`
- Issuer signs and returns a non-core extension token:

```text
RolloutAssignmentTokenV1 {
  tokenType: "ROLLOUT_ASSIGNMENT",        // non-core extension token
  schemaVersion: 1,
  scopeId: "sha256:" + Hash,
  variantCount: Integer,                  // N
  rolloutThreshold: Integer,              // < N
  bucket: Integer,                        // in [0, N)
  walletNullifier: "sha256:" + Hash,      // per wallet per scope
  deliveryPublicKeySpkiBase64: Base64,    // X25519 DER SPKI, per-scope key used to encrypt promo
  signatures: { issuedBy, publicKey, tokenHash, signature }
}
```

The verifier can then enforce:
- **Rollout membership:** `bucket < rolloutThreshold`
- **Only-once per wallet per scope:** store `walletNullifier` and reject repeats

> This does not change spend verification tier; it is a verifier policy layer over already-verified spends. The verifier learns only a scope-bound `walletNullifier` and the per-scope `deliveryPublicKeySpkiBase64`, not a stable wallet identifier.

### 6) Ciphertext observation receipt (optional, defer but reserve)

Some redemption flows also need a verifiable signal that the wallet **observed** (decrypted) an encrypted payload (e.g., a promo, link, or coupon) without revealing wallet identity.

We reserve an optional “observation receipt” artifact name:

```text
CiphertextObservedAckV1 {
  schemaVersion: 1,
  scopeId: "sha256:" + Hash,
  nullifier: "sha256:" + Hash,          // scope-specific anti-replay id
  payloadId: Identifier,                // verifier-defined id for the encrypted payload
  observeNonceHash: "sha256:" + Hash,   // hash of a random nonce that exists only inside the ciphertext
  observedAt: TimestampISO,
  ack: Object                           // authentication material (scheme-specific)
}
```

This keeps “promo” out of the protocol surface area while still standardizing the *cryptographic* behavior: **proof of decryption / observation**.

## Security / semantics reminders

- ZK statements prove only the stated predicate under protocol semantics; they do not prevent indirect inference.
- ZK proofs do not upgrade the verification tier of the underlying spend; they only enable selective disclosure over already-verified fields.
- Corrections that change `lineage.headEventHash` require re-issuing commitments, witness, and any derived proofs.

## Privacy notes (foundation)

- A proof necessarily reveals which `statementId` was proven; if `thresholdCents` is embedded in the statement, the threshold becomes public to the verifier.
- Reusing the same proof material across different verifiers/campaigns is unsafe; redemption flows MUST incorporate `scopeId`/`nullifier` binding to prevent cross-scope replay.

## Acceptance checklist (for the foundation demo)

- A verifier can validate a spend token signature locally
- A verifier can validate `statementId` deterministically
- A verifier can validate the proof *without* seeing `totalCents`
- Proof verification fails if any of these change:
  - `spendId`
  - `headEventHash`
  - `spendTokenHash`
  - `thresholdCents`

## Atomic implementation plan (non-normative)

1) Confirm minimal scope (only `TOTAL_GTE`)
2) Define wallet witness envelope format
3) Choose encryption + keying for wallet witness
4) Add endpoint(s) to retrieve `{token, witness}` for a spend
5) Bind proofs to `spendTokenHash`
6) Add mock PWA → brand verifier scripts
7) Update docs + acceptance checklist
