# Tokens

Tokens are protocol outputs designed for machine consumption: they encode finalized claims with explicit verification rules so downstream systems can validate spend attestations, reward commitments, and aggregate GMV without replaying event streams or trusting APIs.

Crinkl tokens follow the **verifiable credential** model: issuer-signed claims that holders can present to verifiers for local validation. Unlike static credentials, Crinkl spend tokens are correction-aware—canonical truth may evolve via append-only corrections—and support optional ZK predicates for privacy-preserving selective disclosure.

Terms are defined in GLOSSARY.md and used normatively throughout this specification.

## Definitions

### Token

A token is a **signed, portable claim object** with:

- **Canonical bytes** (RFC 8785 JSON canonicalization)
- **Deterministic hashes** (SHA-256)
- **Verifiable signatures and/or commitments** (Ed25519 signatures; optional on-chain Merkle inclusion)
- **Explicit scope** (what the claim refers to: a spend, a recipient, a batch, a policy)
- **Explicit verification procedure** (what a verifier must check)

### Token Bundle

Token bundles are *transport objects* that package:

- the **claim payload** (what is being asserted), and
- the **proof material** needed for verification (event stream fragments, Merkle proofs, authority references).

Token bundles are not required for internal implementations, but they are the preferred interop surface for third parties.

### Portable vs Audit (normative)

This specification distinguishes between:

- **Portable tokens** — privacy-safe, minimal claim objects intended to be shared with third parties and verified with local computation.
- **Audit bundles** — high-detail internal artifacts (e.g., raw event streams) intended for operators/auditors inside a trusted boundary.

#### Operational definition of “portable” (normative)

A token is **portable** iff a verifier can compute a definitive validity result using only:
- the token (and any proof material included in it),
- the protocol’s public rules (hashing, canonicalization, schemas, verification procedures),
- public trust roots (authorized issuer keys / authority registry), and
- public chain data when the token references on-chain commitments (e.g., `txRef` / `committedAt`), and
- publicly replicable protocol event streams (signed + hash-chained) when a token references system-stream artifacts.

Portable verification MUST NOT require:
- querying private operator databases,
- fetching non-public state,
- trusting an HTTP API response as a source of truth.

#### Portable vs audit-only boundary (normative)

Verification of a **portable** token MUST NOT depend on any audit-only field or attachment.

Audit bundles MAY include sensitive or voluminous context (e.g., raw event streams), but they are strictly optional: they can support deeper audit, never baseline verification.

**Clarification (normative intent):** spend-stream events may contain operational references (e.g., `imageDataRef` in `RECEIPT_UPLOADED`) that are meaningful inside an issuer’s pipeline but are not required (and often not appropriate) for third-party portability. A portable token verifier MUST be able to decide validity without fetching those references or replaying non-public pipeline state.

**Portable tokens MUST NOT include:**

- receipt images or raw OCR text
- local filesystem paths, storage keys, object keys, or ingestion/bridge metadata
- raw event payloads that contain the above

Portable tokens MAY include hashed or commitment-safe references (e.g., `headEventHash`, `storeHash`, Merkle roots/proofs).

#### Explicit non-claims (normative, defensive)

Unless a token type explicitly states otherwise, all Crinkl tokens:
- do NOT prove user intent or identity ownership,
- do NOT prove merchant authenticity or payment settlement/finality,
- do NOT prove “no fraud occurred” (they only prove protocol-defined verification outcomes and commitments),
- do NOT require an online lookup to remain true; they are immutable snapshots at issuance.

## Token Lifecycle

All Crinkl tokens follow a common pattern:

1. **Derivation** — Token content is deterministically derived from event streams
2. **Canonicalization** — Token bytes are canonicalized (RFC 8785)
3. **Signing** — Token hash is signed with issuer's Ed25519 key
4. **Distribution** — Token is provided to users/brands/verifiers
5. **Verification** — Recipients verify signature + apply acceptance policies
6. **Supersession** (optional) — Newer tokens for the same scope may be published; old tokens remain valid historical artifacts

Tokens are **immutable after signing**—corrections emit new tokens rather than mutating existing ones.

### Supersession and conflicts (normative)

Tokens are snapshots “as of issuance time”. Some protocol truths are correction-aware, so a later token may supersede an earlier token for the same scope.

Verifiers MUST distinguish:
- **Validity:** cryptographic verification of the token’s claim and proof material.
- **Freshness:** whether the token represents the latest head/state for its scope (an acceptance policy decision).

If multiple valid tokens are presented for the same scope:
- **Spend Attestation Tokens:** scope key is `spendId`. The token with the greatest `lineage.eventCount` MUST be treated as the newest snapshot. If two tokens share the same `spendId` and `lineage.eventCount` but differ in `lineage.headEventHash` or `canonical.status`, verifiers MUST treat this as an error (`OrderingViolation` / fork or issuer equivocation) and MUST NOT pick a winner.
- **Verified GMV Tokens:** scope key is `(window.type, window.date)`. Verifiers SHOULD select the token with the greatest `asOf.computedAt` they trust; `prevGMVTokenHash` may be used to audit continuity.
- **Reward Commitment Tokens:** scope key is `(chainId, batch.batchId, recipientId)`. These tokens refer to a specific committed batch; they are not superseded by later spend corrections. If two valid tokens share the same scope key but disagree on committed root/leaf/proof, verifiers MUST treat this as an error and MUST NOT pick a winner.

## Core Token Types

The protocol defines four token outputs, each derived from existing protocol primitives:

1. **Spend Attestation Token** — canonical spend attestation derived from the spend-stream. This is an **epistemic claim**: it asserts canonical spend state according to protocol verification rules.
2. **Reward Commitment Token** — externally committed reward issuance derived from the reward ledger + commitment layer. This records **economic consequence**: value issued based on a spend attestation.
3. **Verified GMV Token** — a privacy-safe daily "as-of" commitment to aggregate spend totals (and optionally issued/rewarded totals) without exposing receipts.
4. **Verified Spend Distribution Token** — a privacy-safe daily "as-of" dimensional breakdown of aggregate spend by store category and geographic region (CBSA metro area), derived from the same snapshot as the Verified GMV Token.

**Closed set (normative, protocol v1):** `tokenType` values for core portable tokens are a closed set:
`SPEND_ATTESTATION`, `REWARD_COMMITMENT`, `VERIFIED_GMV`, `VERIFIED_SPEND_DISTRIBUTION`.
New core token types require an explicit specification update (and potentially a protocol version bump); experimental/extension tokens MUST be clearly labeled and MUST NOT be required for core verification.

See the Economic Reinforcement Invariant in ABSTRACT.md for the relationship between epistemic and economic commitments.

Per the Identity Minimization Invariant (ABSTRACT.md), wallet exposure follows token-specific rules:
- **Spend Attestation** — wallet is optional; canonical spend truth does not require identity disclosure
- **Reward Commitment** — `recipientId` is required (scoped to unique recipient); representation is schema-defined (WalletRef or Commitment)
- **Verified GMV** — wallet MUST NOT appear; aggregate claims are privacy-preserving

These token types are intentionally separable:
- Spend attestation is defined by the Attestation Ledger state machine.
- Reward issuance is defined by policy outputs and (optionally) anchored via the Commitment Layer.

## Spend Attestation Token

A Spend Attestation Token is a **verifiable credential** representing an OCR-derived purchase claim with correction semantics. It supports optional ZK predicates for privacy-preserving promotion eligibility.

### Claim

The claim is a **signed issuer attestation** about the canonical spend head for a `spendId` at issuance time:

- `canonical.status` is the spend's canonical head class as of `lineage.headEventHash` under the rules of `protocol.protocolVersion` (and the included `canonical.verificationVersion` when present).
- `lineage.headEventHash` identifies the specific spend-stream head event the issuer attests to.

**VC Roles:**
- **Issuer:** the protocol operator (identified by `signatures.issuedBy` + `signatures.publicKey`)
- **Holder:** the wallet owner (optional `wallet` field; spend truth ≠ ownership)
- **Verifier:** any party checking signatures and applying acceptance policy
- **Selective Disclosure:** ZK commitments (`zk.commitments`) + statement proofs enable proving predicates (e.g., "total ≥ threshold") without revealing underlying fields

#### Explicit non-claims (normative)

A Spend Attestation Token:
- does NOT prove user intent, user identity ownership, or wallet control;
- does NOT prove absence of fraud, only the protocol-defined verification outcome;
- does NOT prove merchant authenticity or payment settlement/finality;
- does NOT prove completeness of “the world” (e.g., that no other events exist elsewhere);
- does NOT, by itself, prove that `lineage.headEventHash` is the globally latest head unless the verifier has additional spend-stream evidence (audit).

### Portable shape (normative)

```text
SpendAttestationTokenV1 {
  tokenType: "SPEND_ATTESTATION",
  schemaVersion: 1,
  spendId: Identifier,
  wallet?: WalletRef,              // OPTIONAL per Identity Minimization Invariant
  canonical: {
    status: "HARD_VERIFIED" | "CORRECTED" | "INVALIDATED",
    storeHash?: "sha256:" + Hash,
    date?: DateISO,                 // YYYY-MM-DD derived from canonical timestamp
    totalCents?: Amount,
    currency?: CurrencyCode,
    timestamp?: TimestampISO,
    geoRegion?: RegionCode,         // OPTIONAL ISO 3166-2 subdivision (e.g., "US-CA")
    cbsaCode?: CBSACode,            // OPTIONAL metro area code (e.g., "12420") — see DATA_STRUCTURES.md
    verificationVersion?: Version
  },
  lineage: { headEventHash: Hash, eventCount: Integer },
  protocol: { protocolVersion: Version },
  zk?: { commitments?: ZKCommitments }, // optional; see ZK_LAYER.md
  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

**Portability boundary (normative):** verification of this portable token MUST NOT require retrieving the spend-stream from a private operator database. Deep-audit replay against the spend-stream is optional and may be provided via audit bundles.

**Derivation rules (normative):**
- `wallet` is OPTIONAL. When present, it MUST equal the wallet from the spend-stream. Portable tokens intended for third-party verification SHOULD omit `wallet` unless recipient binding is required.

**Wallet inclusion policy (normative guidance):**

Include `wallet` when:
- Token is used for reward routing or issuance
- Token is used for spend lifecycle management (corrections, fraud investigation)
- Verifier requires recipient binding (e.g., preventing token theft or unauthorized replay)
- Explicit user consent for identity disclosure

Omit `wallet` when:
- Token is used for third-party qualification (brand offers, promotions, eligibility checks)
- Token is shared across multiple verifiers (privacy-preserving aggregation)
- ZK proofs are generated for selective disclosure
- User requests anonymous verification or behavioral qualification without identity disclosure

Default for portable tokens intended for external verifiers: **omit wallet**.

**Anonymous correlation (normative intent):**

When `wallet` is omitted from Spend Attestation Tokens:
- `spendId` remains present and may be correlatable across verification contexts
- This correlation reveals behavioral patterns without revealing identity (e.g., "same anonymous spend qualified for coffee promotion and breakfast offer")
- This correlation does NOT constitute identity disclosure (no wallet address, no personal identifiers, no user-linkable data)
- This enables legitimate uses: fraud detection (same spend claimed multiple times), incremental sales analysis (did coffee promo drive breakfast purchases), cross-promotion strategy, and aggregate market intelligence

**Identity unlinkability vs. behavioral correlation:** The protocol prevents identity linkage (no persistent user identifier across contexts) while allowing behavioral linkage (anonymous spend patterns). This distinction is critical for real-world commerce: verifiers can understand market behavior without tracking individuals.

If a user intentionally discloses `wallet` or uses the same wallet-included token across multiple verifiers, correlation becomes identity-linked. This is a deliberate user action, not a protocol leak.

- `canonical` MUST be derived deterministically from the spend-stream state machine (STATE_MACHINES.md).
- `canonical.status` MUST reflect the final spend attestation state at the time of issuance.
- `canonical.storeHash` MUST be computed deterministically from the canonical store identifier (when available) as:
  - `storeHash = "sha256:" + SHA-256( UTF8("crinkl.store.v1:") || UTF8(storeId) )`, where the `Hash` portion is lowercase hex.
- `canonical.geoRegion` is OPTIONAL. When present, it MUST equal the `geoRegion` from the canonical spend-stream head, expressed as an ISO 3166-2 subdivision code (e.g., `US-CA`) or ISO 3166-1 alpha-2 country code.
- `canonical.cbsaCode` is OPTIONAL. When present, it MUST equal the `cbsaCode` from the canonical spend-stream head, derived from the store's physical location via the OMB CBSA crosswalk (see `DATA_STRUCTURES.md#cbsacode`). Portable tokens intended for brand/local-business verification SHOULD include `cbsaCode` when available.
- `lineage.headEventHash` MUST equal the `eventHash` of the last spend-stream event at issuance time.
- `lineage.eventCount` MUST equal the number of spend-stream events included in the canonical replay up to `headEventHash`.
- If `zk.commitments` is present, each commitment MUST commit to canonical Spend fields at `lineage.headEventHash` and MUST be cryptographically bound to `spendId` and `lineage.headEventHash` (see `ZK_LAYER.md`). Commitments are treated as opaque unless accompanied by a proof; the protocol does not require public recomputation of commitment values.
- ZK commitments and proofs do not strengthen or supersede the verification tier of the underlying Spend; they only enable selective disclosure about already-verified fields.
- **Selective disclosure rule (normative intent):** if a field is intended to be proven via ZK (e.g., `totalCents`, `timestamp`, `storeHash`), portable tokens SHOULD omit that field and rely on `zk.commitments` + proof instead, unless explicit disclosure is required by verifier policy.
- `signatures.signature` MUST be an Ed25519 signature over `signatures.tokenHash`, where `tokenHash = sha256(RFC8785_canonicalize(unsignedToken))`. Domain separation is structural: `tokenType` and `schemaVersion` are included in the hashed unsigned token.

**Optionality rule (normative):** all fields present in the unsigned token are covered by `tokenHash` and therefore by the signature. Absent optional fields are absent from the hash preimage. Optional fields MUST NOT silently change the meaning of `canonical.status`; they may only add additional, non-required context.

### Verification procedure (normative)

To verify a Spend Attestation Token, a verifier MUST:

1. Verify required fields and supported versions (`schemaVersion`, `protocol.protocolVersion`); reject on unsupported versions.
2. Recompute `tokenHash` from the unsigned token (RFC 8785 canonical JSON) and verify `signatures.signature` against `signatures.publicKey`.
3. Verify that `signatures.publicKey` is an authorized issuer key for `signatures.issuedBy` under the applicable trust root mapping (Authority Registry or configured issuer set); reject if unauthorized (see `SECURITY_MODEL.md#trust-roots`).
4. Apply local acceptance policy to `canonical.status` (and any other included canonical fields).

> Verifying `lineage.headEventHash` against the full spend-stream is optional for most consumers and is primarily used for deep audit.

### Optional verification service (non-normative)

Implementations MAY expose a convenience HTTP endpoint that accepts a `SpendAttestationTokenV1` and returns verification results. This is a transport convenience only; verifiers MUST NOT treat an API response as authoritative, and MUST be able to perform the verification steps locally.

Example (illustrative only):

```text
POST /v1/spend-tokens/verify
{
  "token": { ...SpendAttestationTokenV1... }
}

200 OK
{
  "object": "token_verification",
  "type": "spend_attestation",
  "ok": true,
  "checks": {
    "tokenHashMatch": true,
    "signatureValid": true,
    "protocolVersionSupported": true,
    "issuerAuthorized": true
  },
  "issuer": { "issuedBy": "crinkl-authority", "publicKey": "Base64..." },
  "lineage": { "headEventHash": "Hash", "eventCount": 3 },
  "status": "HARD_VERIFIED"
}
```

The verification result MUST reflect the same cryptographic checks described above. Issuer authorization checks MUST be anchored to the local trust root mapping (e.g., authority registry or configured issuer set), not to an API response alone.

### Supersession rule (normative)

Spend tokens are snapshots and may be superseded by later spend-stream heads (corrections/invalidations). If presented with multiple valid spend tokens for the same `spendId`, a verifier MUST treat the token with the greatest `lineage.eventCount` as newest. Tokens with equal `lineage.eventCount` but different `headEventHash` MUST be treated as invalid/ambiguous (fork or equivocation).

If a spend is corrected/invalidated and the head changes:
- A new Spend Attestation Token MUST be issued for the new head.
- Old spend tokens remain cryptographically valid historical artifacts, but may be obsolete per verifier freshness policy.
- Any ZK proofs or witnesses bound to the old `spendTokenHash` / `headEventHash` MUST NOT be treated as proofs about the new head.

### Optional: ZK statement proof (normative)

A ZK statement proof provides a privacy-preserving proof about a Spend without revealing underlying receipt data. It is optional proof material that can accompany a Spend Attestation Token and does not change the Spend’s canonical status.

ZK proofs SHOULD be bound to the referenced spend token hash (`spendTokenHash`) to prevent replay across re-issuance of new spend tokens for the same spend (e.g., when a token changes due to commitment scheme upgrades or corrections).

#### Proof shape (normative)

```text
SpendZkStatementProofV1 {
  schemaVersion: 1,
  spendId: Identifier,
  spendTokenHash: "sha256:" + Hash,
  binding: { headEventHash: Hash }, // MUST match token.lineage.headEventHash
  statement: Object,             // RFC 8785 canonical JSON
  statementId: "sha256:" + Hash, // sha256(RFC8785_canonicalize(statement)); statement MUST include domain+schemaVersion (see ZK_LAYER.md)
  proofSystem: String,
  circuitId: String,             // versioned, unambiguous circuit identifier
  verifyingKeyId: "sha256:" + Hash, // identifier of verifier parameters / verifying key bytes (scheme-specific)
  publicInputs: Object,
  proof: Base64
}
```

**Verifying key note (normative):** some proof systems do not have standalone “verifying key bytes” (e.g., Bulletproofs range proofs parameterize verification by generators and bit-length). In that case, `verifyingKeyId` MUST be computed as the hash of a canonical JSON description of the verifier parameters (e.g., `{ domain, proofSystem, circuitId, bits, ... }`), and verifiers MUST recompute it the same way.

#### Verification (normative)

To verify a `SpendZkStatementProofV1`, a verifier MUST:

1. Fetch the referenced Spend Attestation Token, verify its signature, and verify that its `signatures.tokenHash` equals `spendTokenHash`.
2. Verify `binding.headEventHash` equals the referenced token’s `lineage.headEventHash`; reject if mismatched.
3. Recompute `statementId = sha256(RFC8785_canonicalize(statement))` and verify it equals `statementId`.
4. Enforce statement schema policy: reject unknown `statement.domain` or unsupported `statement.schemaVersion` (see `ZK_LAYER.md`).
5. Resolve the verifying key bytes referenced by `verifyingKeyId` for `(proofSystem, circuitId)`; if the verifier cannot resolve them, it MUST reject.
6. Verify the ZK proof using `proofSystem`, `circuitId`, `verifyingKeyId`, and `publicInputs`.
7. If the referenced Spend Attestation Token includes `zk.commitments`, verify the proof’s `publicInputs` are bound to those commitments and the token’s binding context (`spendId`, `lineage.headEventHash`) (commitment scheme–specific; see ZK_LAYER.md).
8. Proof verification MUST be performed in a way that is cryptographically bound to `spendTokenHash` (proof-system specific: e.g., a circuit public input or transcript binding). A proof that is not bound to `spendTokenHash` MUST NOT be treated as a proof about the referenced token.

**Redemption note:** redemption anti-replay requirements (e.g., `scopeId`/`nullifier`) are defined separately in `ZK_FOUNDATION.md`. This proof type is an eligibility proof; redemption introduces additional binding requirements.

### Optional: Wallet witness (non-portable, normative)

To enable **client-side proving**, implementations MAY issue a wallet-only “witness envelope” that contains the commitment openings required to prove ZK statements without revealing underlying receipt data.

This witness material is **not portable** and MUST be treated as sensitive private data. It MUST NOT be embedded in portable tokens.

#### Witness shape (normative)

```text
SpendZkWitnessV1 {
  schemaVersion: 1,
  spendId: Identifier,
  spendTokenHash: "sha256:" + Hash,      // hash of the referenced Spend Attestation Token (portable)
  binding: { headEventHash: Hash },      // MUST match token.lineage.headEventHash
  openings: {
    storeHash?: { value: Hash, blinding: Base64 }, // opening for zk.commitments.C_store (scheme-specific encoding)
    totalCents?: { value: Amount, blinding: Base64 }, // opening for zk.commitments.C_total (scheme-specific encoding)
    dayIndex?: { value: String, blinding: Base64 }, // opening for zk.commitments.C_dayIndex (days since epoch; scheme-specific encoding)
    geoRegion?: { value: String, blinding: Base64 },   // opening for zk.commitments.C_geoRegion (scheme-specific encoding)
    cbsaCode?: { value: String, blinding: Base64 }     // opening for zk.commitments.C_cbsaCode (scheme-specific encoding)
  }
}
```

#### Distribution (normative)

`SpendZkWitnessV1` MUST be distributed only inside a trusted boundary, typically by encrypting it to a wallet-controlled public key and delivering it to the wallet (e.g., via authenticated API).

#### Constraints (normative)

- A witness MUST be bound to a single spend token via `spendTokenHash`.
- A witness MUST be bound to a single attestation head via `binding.headEventHash`.
- If a spend is corrected and the attestation head changes, prior witnesses MUST NOT be reused.
- A witness MUST NOT include receipt images, raw OCR text, or ingestion metadata.
- A witness SHOULD contain only the minimum opening material required to prove statements over commitments; it MUST NOT include stable identifiers that enable cross-spend linkage beyond `spendId` and the bound `headEventHash`.

## Spend Attestation Bundle (Audit Only)

An audit bundle is a high-detail representation of a spend-stream intended for internal audit, reconciliation, and debugging. It is not the preferred portable interop surface.

```text
SpendAttestationBundle {
  spendId: Identifier,
  wallet: WalletRef,              // Included for internal routing; audit bundles are not portable
  events: [SpendStreamEvent],     // ordered, prevHash-linked, contiguous from genesis to head
  derivedSpend: Spend | null,
  head: { eventHash: Hash, signature: Signature, timestamp: Timestamp, protocolVersion: Version }
}
```

Audit bundles MAY contain sensitive metadata (including wallet identifiers) depending on the event schemas in use. Implementations MUST treat audit bundles as private and MUST NOT publish them as "tokens" intended for third-party agent consumption. The Identity Minimization Invariant applies only to portable tokens, not internal audit artifacts.

## Reward Commitment Token

### Claim

The claim is that a recipient has a **leaf included under a committed batch root**:
- the provided `leaf` (recipient-scoped aggregate for `batch.batchId`) is included under `batch.root` via `proof`, and
- `batch.root` is authenticated by the included system-stream commitment history (`systemEvents` + Authority Registry rules).

#### Explicit non-claims (normative)

A Reward Commitment Token:
- does NOT prove current wallet balance (it proves inclusion in a specific batch, not cumulative balance),
- does NOT prove funds custody, redemption availability, solvency, reserves, or “already paid out”,
- does NOT claw back or negate previously issued rewards when spends are later invalidated or corrected,
- does NOT prove spend truth beyond the protocol semantics that gated issuance.

Reward commitments are batch-level, recipient-scoped, and derive from Reward Ledger events (REWARD_*_ISSUED) plus a system-stream commitment event (REWARD_BATCH_COMMITTED and related).

**Recipient scoping:** Reward Commitment Tokens require recipient binding for verification of economic issuance. The `recipientId` field is REQUIRED. The representation of `recipientId` is schema-defined:
- `WalletRef` (transparent, schema v1a/v2a)
- `Commitment` (blinded, schema v1b/v2b)

See COMMITMENT_LAYER.md for schema definitions and recipient blinding.

**Linkability note (normative intent):**
- If `recipientId` is a `WalletRef` (transparent schemas), third parties can link the same recipient across batches by wallet address.
- If `recipientId` is a blinded `Commitment` (blinded schemas), the identifier is intentionally per-batch and does not create a stable public identifier across batches; recipients may selectively disclose underlying wallet/blinder to prove inclusion (see `COMMITMENT_LAYER.md#recipient-blinding`).

### Portable shape (normative)

```text
RewardCommitmentTokenV1 {
  tokenType: "REWARD_COMMITMENT",
  schemaVersion: 1,
  chainId: String,
  economicTier: "COMMITTED" | "COMMITTED_BACKED",
  commitmentEvent: SystemStreamEvent, // eventName = REWARD_BATCH_COMMITTED
  backingEvent?: SystemStreamEvent,   // eventName = REWARD_BATCH_BACKING_ATTESTED (required when economicTier = COMMITTED_BACKED)
  systemEvents: [SystemStreamEvent],  // ordered, prevHash-linked; MUST include commitmentEvent and authority events needed to validate its signer at effective time
  batch: { batchId: Identifier, root: Hash, schemaVersion: String, txRef: String, committedAt: Timestamp }, // schemaVersion: "1a"|"1b"|"2a"|"2b"
  recipientId: RecipientRef,          // WalletRef or Commitment per batch.schemaVersion
  leaf: AggregatedRewardLeaf | LinkableAggregatedRewardLeaf, // schemaVersion-defined
  proof: InclusionProof,          // Merkle proof from leaf to batch.root
  // audit-only attachments:
  // rewardEvents?: [SpendStreamEvent] // supporting REWARD_*_ISSUED events (audit / reconciliation)
  rewardInclusionProof?: RewardInclusionProof // optional when batch.schemaVersion is "2a" or "2b": spend↔reward linkage
}
```

**Derivation rules (normative):**
- `commitmentEvent` MUST be a valid `REWARD_BATCH_COMMITTED` system-stream event for `chainId`.
- `batch` MUST equal `commitmentEvent.payload`.
- `systemEvents` MUST be a contiguous, fork-free system-stream segment for `chainId` that includes `commitmentEvent` and is sufficient to validate:
  - integrity + `prevHash` linkage for the included segment, and
  - authority validity for `commitmentEvent.signedBy` at the event-effective time (typically `committedAt`) per `COMMITMENT_LAYER.md#authority-registry`.
  If the included segment does not start at genesis (`prevHash = null`), a verifier MUST treat authority validation as **indeterminate** until it obtains any missing publicly replicable system-stream history and validates it cryptographically.
- `economicTier` MUST be:
  - `"COMMITTED"` when only the commitment proof material is present, or
  - `"COMMITTED_BACKED"` when a valid `REWARD_BATCH_BACKING_ATTESTED` is also included.
- If `economicTier = "COMMITTED_BACKED"`, then:
  - `backingEvent` MUST be present and MUST be a valid `REWARD_BATCH_BACKING_ATTESTED` for the same `chainId`.
  - `backingEvent.payload.batchId` MUST equal `batch.batchId`.
- `proof` MUST conform to the Merkle proof structure and hashing rules defined in `COMMITMENT_LAYER.md#proof-structure` and `COMMITMENT_LAYER.md#merkle-tree` (canonical leaf bytes, `0x00` leaf prefix, `0x01` internal prefix, sorted-pair hashing).

### Verification procedure (normative)

To verify a Reward Commitment Token, a verifier MUST:

1. Verify `systemEvents` as a contiguous, fork-free system-stream for `chainId` (integrity envelope + `prevHash` chaining) and verify authority validity per `EVENTS.md` and `COMMITMENT_LAYER.md#authority-registry`.
2. Verify `commitmentEvent` is included in `systemEvents`, and verify `batch` equals `commitmentEvent.payload`.
3. Verify the Merkle inclusion proof (`proof`) against `batch.root` per `COMMITMENT_LAYER.md#verification-algorithm` (including leaf canonicalization and domain separation).
4. If `economicTier = "COMMITTED_BACKED"`, verify `backingEvent` integrity + authority validity and verify it references the same `batch.batchId`.
5. Apply local chain acceptance policy:
   - verifiers MAY rely solely on the signed system-stream history as authenticity for `batch.root`, and/or
   - verifiers MAY additionally verify `batch.txRef` on-chain and apply chain-specific finality thresholds (reorg handling is defined by chain bindings; see `COMMITMENT_LAYER.md#chain-bindings`).
6. If audit attachments are provided (e.g., `rewardEvents`), verify their envelopes and ensure they are consistent with the committed leaf semantics (e.g., totals and/or linkage roots).

### Corrections and reorgs (normative interpretation)

- **Batch corrections:** correction batches are additional commitment-layer artifacts that adjust balances without negating historical issuance. A Reward Commitment Token for an original batch remains a valid proof of inclusion in that batch. It MUST NOT be interpreted as “current balance”; current balance requires processing correction batches and/or snapshots (see `COMMITMENT_LAYER.md#correction-batches` and `COMMITMENT_LAYER.md#cumulative-snapshots`).
- **Chain reorg / probabilistic finality:** verifiers SHOULD treat non-finalized on-chain anchoring as indeterminate/pending according to chain bindings and finality thresholds. This does not change the token’s signed system-stream validity, but may change whether a verifier accepts the anchoring as stable.

## Linking Spend ↔ Reward (Optional)

Reward commitments are recipient-scoped and may be **optionally linkable to per-spend reward issuance**.

When the Commitment Layer uses a linkable leaf schema (`schemaVersion` 2a or 2b, see COMMITMENT_LAYER.md), a verifier can prove that:

- a specific reward issuance (identified by `spendId` + policy output) is included in the committed batch for a recipient, and
- that inclusion is bound to the on-chain root via a compact proof.

This produces a portable “spend ↔ reward” linkage without requiring the verifier to fetch and sum every reward event in the batch.

**Bounded claim (normative):** when present, `rewardInclusionProof` proves only that a `(spendId, rewardEventHash)` reference is included under the aggregated leaf’s `rewardEventsRoot`, and that the aggregated leaf is included in the batch root. Verifying the underlying reward event envelope (and therefore the meaning of `rewardEventHash`) is optional audit material and may be provided out-of-band.

## Verified GMV Token

> “Aggregate economic throughput must be provable, append-only, correction-aware, and privacy-preserving.”
**Identity prohibition:** Per the Identity Minimization Invariant (ABSTRACT.md), Verified GMV Tokens MUST NOT include wallet identifiers, recipient references, or any data that would enable reconstruction of per-user spend patterns. Spends are referenced only via `spendId` within the committed `spendHeadSetRoot`; aggregates expose only totals and Merkle roots.

### Explicit non-claims (normative)

A Verified GMV Token:
- does NOT claim “all receipts are valid forever”; it is an **as-of snapshot** that may be superseded by later tokens for the same window;
- does NOT imply rewards were issued or economically backed unless `issuedGMV` and/or explicit commitment/backing artifacts are provided;
- does NOT reveal wallet ownership or user identity; per-spend inclusion proofs do not imply ownership.
### Primary Use Case: Brand Partnership Verification (non-normative)

GMV tokens enable brands to verify Crinkl's aggregate audience reach and spending power (without exposing individual user transactions) when negotiating reward partnerships.

**The negotiation problem:** Brands need verifiable proof of audience size before committing marketing budget.

Brands allocate 15–25% of revenue to customer acquisition. Crinkl aggregates users actively spending in brand-relevant categories. GMV tokens allow brands to audit claimed audience size and spend volume before redirecting marketing budget to user rewards.

This is analogous to Nielsen ratings (prove audience size for TV ad negotiations) or credit scores (prove creditworthiness for lending decisions)—but with cryptographic non-repudiation and privacy preservation.

### Dispute Resolution (non-normative)

If a brand disputes a published GMV figure, the issuer can provide:

1. The underlying `spendHeadSetRoot` leaf set (aggregate data, no receipt images)
2. Per-spend inclusion proofs for a sample of spends
3. Audit bundles (if the brand has appropriate data access agreements)

This allows third-party auditors to verify GMV calculations without compromising user privacy or requiring full database access.

### GMV Commitments (non-normative)

Crinkl treats GMV as an append-only aggregate claim derived from canonical spend attestations, not a trusted database export.

GMV commitments preserve user privacy by committing only to aggregate totals and Merkle roots of spend heads, without exposing receipt data, merchants, or individual transactions. Corrections are expressed via new GMV commitment artifacts rather than mutation of historical records.

### How a Receipt Becomes Verified GMV

A receipt contributes to Verified GMV only after **Hard Verification** (or subsequent **Correction**) produces a finalized spend (see STATE_MACHINES.md)—a canonical spend record with total amount, currency, and timestamp. Rewards and economic backing (e.g., BTC moving) are separate: they may happen around the same time, but they do not define Verified GMV.

Verified GMV is included when an issuer **publishes a Verified GMV Token** for a specific UTC day. To compute it, the issuer picks an “as-of” time (`asOf.computedAt`), selects all finalized spends whose finalized timestamp falls in that UTC day and are not `INVALIDATED`, and sums their totals into `verifiedGMV`.

The token contains no receipt images/text; instead it includes a single hash (`asOf.spendHeadSetRoot`) that acts like a fingerprint of “the set of spends that were counted”, so the issuer can later give a user a small proof that their spend was included without publishing every spend or sharing receipts (see per-spend inclusion proofs below).

If later corrections change a spend’s finalized timestamp or total, the issuer publishes a newer token for that same day rather than revising history.

### Claim

The claim is:

- the **Verified GMV** for a fixed UTC day (sum of finalized spend totals as-of a specific computation time), and
- optionally the **Issued/Rewarded GMV** (sum over spends for which rewards were issued). **Critical:** Verified GMV and Issued GMV are independent—spend corrections do not trigger reward clawbacks.

Every GMV token MUST be explicit about its **window** and its **as-of** semantics.

### Portable shape (normative)

```text
VerifiedGmvTokenV1 {
  tokenType: "VERIFIED_GMV",
  schemaVersion: 2,

  window: { type: "UTC_DAY", date: DateISO }, // YYYY-MM-DD

  anchoringTier?: "SIGNED" | "ANCHORED", // default: "SIGNED" if `anchoring` absent, "ANCHORED" if present

  asOf: {
    computedAt: TimestampISO,
    spendHeadSetRoot: "sha256:" + Hash,
    spendRule: "CANONICAL_HEAD_ASOF"
  },

  verifiedGMV: { currency: CurrencyCode, totalCents: Amount, spendCount: Integer },

  issuedGMV?: {
    currency: CurrencyCode,
    totalCents: Amount,
    rewardedSpendCount: Integer,
    policyVersion?: String
  },

  linkage?: { rewardBatchRoots: [Hash] },

  anchoring?: { chainId: String, txRef: String },

  prevGMVTokenHash?: "sha256:" + Hash,

  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

### Interpretation rules (normative)

#### As-of anchor and supersession

- `asOf.computedAt` is the as-of anchor: the issuer asserts the spend set and aggregate values are computed from canonical heads **as they existed at** `asOf.computedAt`.
- Supersession preference over a set of candidate tokens for the same `(window.type, window.date)` is deterministic:
  1) prefer greater `asOf.computedAt`; if tied,
  2) prefer the token with lexicographically greatest `signatures.tokenHash` (tie-break only; should be rare).
- Verifiers MAY additionally enforce a local freshness policy (e.g., reject tokens older than X days) but that is an acceptance policy, not part of cryptographic validity.

#### Bucketing and time semantics

- `window` is defined in UTC (`window.type = UTC_DAY`).
- A spend is included in a GMV window according to the canonical spend attestation timestamp produced by the spend-stream state machine (STATE_MACHINES.md), not raw receipt-local timestamps.
- If the canonical timestamp for a spend changes due to correction, the spend MAY move between windows in subsequent GMV tokens; this is expressed only by publishing new GMV commitment artifacts.

#### `issuedGMV` semantics

- If `issuedGMV` is present, the issuer asserts those values are computed for the window as-of `asOf.computedAt`.
- If `issuedGMV` is absent, the issuer is not asserting issued/rewarded GMV for that window (unknown / not computed / intentionally omitted).
- To assert that no rewards were issued for a window, issuers SHOULD include `issuedGMV` with `totalCents = "0"` and `rewardedSpendCount = 0`.

#### Supersession and corrections for the same window

Issuers MAY publish multiple Verified GMV Tokens for the same `window.date` over time.

- Later tokens for the same window are interpreted as newer **as-of snapshots**, not mutations of history.
- If the issuer knows the immediately prior published GMV token for the same window, it SHOULD set `prevGMVTokenHash` to form a chain.
- Verifiers SHOULD select the token with the greatest `asOf.computedAt` that they trust, and MAY additionally verify `prevGMVTokenHash` continuity for audit.

Auditors can compute deltas between two snapshots for the same window as:

- `verifiedGMV.totalCentsDelta = BigInt(verifiedGMV.totalCents(new)) - BigInt(verifiedGMV.totalCents(old))`
- `verifiedGMV.spendCountDelta = verifiedGMV.spendCount(new) - verifiedGMV.spendCount(old)`

> Optional extension: an issuer MAY also publish an explicit delta token type (e.g., `VERIFIED_GMV_DELTA`) for audit-friendly “GMV went down because spends were invalidated” narratives. This is non-normative and not required for verifiers.

### spendHeadSetRoot construction (normative)

To commit to "which spends were counted" and "which finalized spend head states were used" **while preserving user privacy** (no receipt images, merchant names, or transaction details), issuers MUST compute `spendHeadSetRoot` as a Merkle root over per-spend leaves.

For each included `spendId`, the issuer MUST construct a leaf object:

```text
SpendHeadLeafV1 {
  spendId: Identifier,
  canonicalHeadEventHash: Hash,
  totalCents: Amount,
  currency: CurrencyCode,
  status: "HARD_VERIFIED" | "CORRECTED",
  geoRegion?: RegionCode,              // OPTIONAL ISO 3166-2 subdivision (e.g., "US-CA")
  cbsaCode?: CBSACode                  // OPTIONAL metro area code (e.g., "12420")
}
```

Leaf bytes MUST be `RFC8785_canonicalize(SpendHeadLeafV1)` and leaf hash MUST be `SHA256(0x00 || leafBytes)`.

Internal node hash MUST be `SHA256(0x01 || sort(left,right))` (domain-separated, sorted-pair Merkle tree) and leaves MUST be sorted deterministically by `spendId` before tree construction.

**Duplicate rule (normative):** each `spendId` MUST appear at most once in the leaf set. Duplicate `spendId` values MUST be rejected by the issuer; verifiers/auditors MUST treat a leaf set containing duplicates as invalid.

> This matches the Commitment Layer Merkle hashing conventions (0x00 leaves / 0x01 internal) and is intentionally chain-agnostic.

### Verification procedure (normative)

To verify a Verified GMV Token, a verifier MUST:

1. Verify required fields and supported versions (`schemaVersion`); reject on unsupported versions.
2. Recompute `tokenHash` from the unsigned token and verify `signatures.signature` against `signatures.publicKey`.
3. Verify that `signatures.publicKey` is an authorized issuer key for `signatures.issuedBy` under the applicable trust root mapping (Authority Registry or configured issuer set); reject if unauthorized (see `SECURITY_MODEL.md#trust-roots`).
4. Apply local acceptance policy:
   - treat `verifiedGMV` as an "as-of" snapshot that may be superseded by later GMV tokens for the same window, and
   - treat `issuedGMV` (when present) as a statement about issued rewards, not about spend attestation.

If an issuer provides the underlying leaf set and optional inclusion proofs out-of-band, a verifier MAY recompute `spendHeadSetRoot` and audit which spends were counted.

### Optional: Per-spend inclusion proof (normative)

An issuer MAY provide a per-spend inclusion proof that allows a holder of a `spendId` (typically the user who uploaded the receipt) to verify that their spend was included in a specific Verified GMV Token, without requiring the issuer to publish the full set of spends.

**Semantics (normative):** this proof asserts only **membership** of `spendLeaf` under `asOf.spendHeadSetRoot` for the referenced GMV token. It does not assert ownership, identity, or reward eligibility.

#### Proof shape (normative)

```text
VerifiedGmvInclusionProofV1 {
  schemaVersion: 1,
  gmvTokenHash: "sha256:" + Hash,
  spendLeaf: SpendHeadLeafV1,
  leafHash: Hash,
  siblings: [Hash] // sibling hashes from leaf to `asOf.spendHeadSetRoot`
}
```

#### Verification (normative)

To verify a `VerifiedGmvInclusionProofV1`, a verifier MUST:

1. Fetch the referenced Verified GMV Token and verify its signature, and verify that its `signatures.tokenHash` equals `gmvTokenHash`.
2. Recompute `leafHash = SHA256(0x00 || RFC8785_canonicalize(spendLeaf))` and verify it equals `leafHash`.
3. Starting from `leafHash`, iteratively compute the parent hash with each element of `siblings` using `SHA256(0x01 || sort(left,right))` until a candidate root is produced, and verify it equals the token’s `asOf.spendHeadSetRoot`.

> A user can additionally check that `spendLeaf` matches the spend they expect (same `spendId` and finalized total/currency/status) using their Spend Attestation Token.

### Optional: Scoped inclusion attestation (non-transferability) (normative)

If a verifier needs a **non-transferable** inclusion artifact (e.g., a brand requests “prove inclusion for this request scope”), the issuer MAY provide a signed, scope-bound attestation.

This is distinct from Merkle membership: it binds inclusion to a `scopeId` so the artifact cannot be reused across scopes without detection.

```text
VerifiedGmvInclusionAttestationV1 {
  schemaVersion: 1,
  gmvTokenHash: "sha256:" + Hash,
  scopeId: "sha256:" + Hash,
  spendId: Identifier,
  attestedAt: TimestampISO,
  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

To verify a `VerifiedGmvInclusionAttestationV1`, a verifier MUST:
1. Verify the referenced Verified GMV Token and verify `gmvTokenHash` matches its `signatures.tokenHash`.
2. Recompute the attestation `tokenHash` and verify its signature, and verify issuer authorization for `issuedBy/publicKey`.
3. Verify the `scopeId` matches the verifier's expected scope for the request.

## Verified Spend Distribution Token

The Verified Spend Distribution Token extends the GMV primitive with **dimensional breakdowns** — the same aggregate spend data sliced by geographic region and store category. It shares the same `spendHeadSetRoot`, spend filtering, and as-of semantics as the Verified GMV Token for the same window.

**Identity prohibition:** Like Verified GMV Tokens, Verified Spend Distribution Tokens MUST NOT include wallet identifiers, recipient references, or any data that would enable reconstruction of per-user spend patterns. Only aggregate counts and totals per dimension are exposed.

### Explicit non-claims (normative)

A Verified Spend Distribution Token:
- does NOT claim individual spend details; it is an aggregate snapshot by dimension;
- does NOT reveal wallet ownership or user identity;
- does NOT imply rewards were issued unless `issuedDistribution` is present;
- does NOT guarantee completeness of category or region resolution (best-effort enrichment is expected).

### Portable shape (normative)

```text
VerifiedSpendDistributionTokenV1 {
  tokenType: "VERIFIED_SPEND_DISTRIBUTION",
  schemaVersion: 2,

  window: { type: "UTC_DAY", date: DateISO },

  asOf: {
    computedAt: TimestampISO,
    spendHeadSetRoot: "sha256:" + Hash,    // MUST equal the GMV token's spendHeadSetRoot for the same window+computedAt
    spendRule: "CANONICAL_HEAD_ASOF"
  },

  verifiedDistribution: {
    currency: CurrencyCode,
    totalCents: Amount,
    spendCount: Integer,
    byCategory: Record<String, { spendCount: Integer, totalCents: Amount }>,
    byGeoRegion?: Record<RegionCode, { spendCount: Integer, totalCents: Amount }>
  },

  issuedDistribution?: {
    currency: CurrencyCode,
    totalCents: Amount,
    rewardedSpendCount: Integer,
    byCategory: Record<String, { spendCount: Integer, totalCents: Amount }>,
    byGeoRegion?: Record<RegionCode, { spendCount: Integer, totalCents: Amount }>,
    policyVersion?: String
  },

  prevDistributionTokenHash?: "sha256:" + Hash,

  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

### Derivation rules (normative)

- `asOf.spendHeadSetRoot` MUST be computed identically to the Verified GMV Token for the same window and as-of time. Implementations SHOULD derive both tokens from the same snapshot computation.
- `byCategory` keys MUST be canonical store category identifiers as defined by the store registry (see `STORE_REGISTRY.md`). Spends whose store cannot be resolved to a category MUST be bucketed under the key `"Unknown"`.
- `byGeoRegion` keys MUST be canonical region bucket values derived from the canonical spend head. Implementations MAY use ISO 3166-2 subdivisions, ISO 3166-1 alpha-2 country codes, CBSA numeric codes, or non-metro fallbacks when those are the canonical region buckets emitted by the verifier. Spends with no resolvable geographic data MUST be bucketed under `"Unknown"`.
- `byCategory` and `byGeoRegion` record keys MUST be sorted lexicographically (UTF-8 byte order) for canonical serialization.
- `verifiedDistribution.totalCents` MUST equal the sum of all `byCategory` values' `totalCents`. The same holds for `spendCount`.
- If `issuedDistribution` is present, it follows the same rules scoped to rewarded spends only.
- `prevDistributionTokenHash`, when present, MUST reference the `tokenHash` of the immediately prior published distribution token for the same `(window.type, window.date)`.

### Privacy floor (implementation guidance, non-normative)

Implementations SHOULD define a minimum-spend-count threshold below which a `byGeoRegion` bucket is rolled up into a coarser grouping (e.g., state-level or `"Unknown"`) to prevent re-identification via small-population geographic areas cross-tabulated with category and time. The specific threshold is an implementation/policy decision.

### Supersession

Distribution tokens follow the same supersession rules as Verified GMV Tokens: scope key is `(window.type, window.date)`, preference by greatest `asOf.computedAt`.

### Verification procedure (normative)

To verify a Verified Spend Distribution Token, a verifier MUST:

1. Verify required fields and supported versions (`schemaVersion`); reject on unsupported versions.
2. Recompute `tokenHash` from the unsigned token and verify `signatures.signature` against `signatures.publicKey`.
3. Verify that `signatures.publicKey` is an authorized issuer key for `signatures.issuedBy` under the applicable trust root mapping; reject if unauthorized.
4. Apply local acceptance policy (treat as an as-of snapshot that may be superseded).
