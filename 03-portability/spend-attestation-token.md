---
status: draft
layer: portability
version: v1
normative: true
---

# Spend Attestation Token

This document defines the portable representation of a signed Spend Attestation. Reward, GMV, distribution, ZK, and settlement material are downstream and live in later layers.

Tokens are protocol outputs designed for machine consumption: they encode finalized claims with explicit verification rules so downstream systems can validate spend attestations, reward commitments, and aggregate GMV without replaying event streams or trusting APIs.

Crinkl tokens use a conceptual credential pattern: issuer-signed claims that a
presenter can provide to a verifier for local validation. Native Crinkl tokens
are not W3C Verifiable Credentials in v1.0.0-rc.4. Unlike static credentials,
Crinkl spend tokens are correction-aware—canonical truth may evolve via
append-only corrections—and support optional ZK predicates for
privacy-preserving selective disclosure.

Terms are defined in ../08-governance/glossary.md and used normatively throughout this specification.

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

**Wallet-scope boundary (normative):** portable token verification is intentionally downstream of internal spend-stream construction. Internal wallet-scoped event fields do not become portable token fields unless they are explicitly included in the signed token. The default portable Spend Attestation Token for external verification omits wallet, user, account, and session identifiers.

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

## Layered Token Outputs

The protocol defines four v1 token outputs, each derived from existing protocol primitives. Only Spend Attestation Token belongs to the proof portability layer. Reward Commitment, Verified GMV, and Verified Spend Distribution are downstream reward/settlement artifacts.

1. **Spend Attestation Token** — canonical spend attestation derived from the spend-stream. This is an **epistemic claim**: it asserts canonical spend state according to protocol verification rules.
2. **Reward Commitment Token** — externally committed reward issuance derived from the reward ledger + commitment layer. This records **economic consequence**: value issued based on a spend attestation.
3. **Verified GMV Token** — a privacy-safe daily "as-of" commitment to aggregate spend totals (and optionally issued/rewarded totals) without exposing receipts.
4. **Verified Spend Distribution Token** — a privacy-safe daily "as-of" dimensional breakdown of aggregate spend by store category and geographic region (CBSA metro area), derived from the same snapshot as the Verified GMV Token.

**Closed set (normative, protocol v1):** `tokenType` values for v1 portable tokens are a closed set:
`SPEND_ATTESTATION`, `REWARD_COMMITMENT`, `VERIFIED_GMV`, `VERIFIED_SPEND_DISTRIBUTION`.
New token types require an explicit specification update (and potentially a protocol version bump); experimental/extension tokens MUST be clearly labeled and MUST NOT be required for Core Spend Attestation verification.

See the Economic Reinforcement Invariant in ../00-purpose/what-crinkl-proves.md for the relationship between epistemic and economic commitments.

Per the Identity Minimization Invariant (../00-purpose/what-crinkl-proves.md), wallet exposure follows token-specific rules:
- **Spend Attestation** — wallet is optional; canonical spend truth does not require identity disclosure
- **Reward Commitment** — `recipientId` is required (scoped to unique recipient); representation is schema-defined (WalletRef or Commitment)
- **Verified GMV** — wallet MUST NOT appear; aggregate claims are privacy-preserving
- **Verified Spend Distribution** — wallet MUST NOT appear; aggregate claims are privacy-preserving

These token types are intentionally separable:
- Spend attestation is defined by the Attestation Ledger state machine.
- Reward issuance is defined by policy outputs and (optionally) anchored via the Commitment Layer.

## Spend Attestation Token

A Spend Attestation Token is a native signed issuer attestation representing an
OCR-derived purchase claim with correction semantics. It is not a W3C
Verifiable Credential in v1.0.0-rc.4. It supports optional ZK predicates for
privacy-preserving promotion eligibility.

### Claim

The claim is a **signed issuer attestation** about the canonical spend head for a `spendId` at issuance time:

- `canonical.status` is the spend's canonical head class as of `lineage.headEventHash` under the rules of `protocol.protocolVersion` (and the included `canonical.verificationVersion` when present).
- `lineage.headEventHash` identifies the specific spend-stream head event the issuer attests to.

**Conceptual roles:**
- **Issuer:** the protocol operator (identified by `signatures.issuedBy` + `signatures.publicKey`)
- **Holder:** the wallet owner (optional `wallet` field; spend truth ≠ ownership)
- **Verifier:** any party checking signatures and applying acceptance policy
- **Selective Disclosure:** ZK commitments (`zk.commitments`) + statement proofs enable proving predicates (e.g., "total ≥ threshold") without revealing underlying fields

#### Explicit non-claims (normative)

A Spend Attestation Token:
- does NOT prove user intent, legal identity, or wallet control; a schema-v2
  token with `holderBinding` can establish control of its per-Spend holder key
  only when accompanied by a valid fresh holder-control proof;
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
    cbsaCode?: CBSACode,            // OPTIONAL metro area code (e.g., "12420") — see ../01-core/canonicalization.md
    verificationVersion?: Version
  },
  lineage: { headEventHash: Hash, eventCount: Integer },
  protocol: { protocolVersion: Version },
  zk?: { commitments?: ZKCommitments }, // optional; see ../06-extensions/zk-proof-extension.md
  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

### Optional holder binding and holder control (v2)

`SpendAttestationTokenV2` retains the complete v1 shape and verification
procedure, changes `schemaVersion` to `2`, and adds one OPTIONAL signed field:

```text
SpendAttestationTokenV2 {
  tokenType: "SPEND_ATTESTATION",
  schemaVersion: 2,
  spendId: Identifier,
  wallet?: WalletRef,
  canonical: { ...SpendAttestationTokenV1.canonical },
  lineage: { headEventHash: Hash, eventCount: Integer },
  protocol: { protocolVersion: Version },
  zk?: { commitments?: ZKCommitments },
  holderBinding?: {
    scheme: "crinkl.holder.v2",
    commitment: "sha256:" + Hash
  },
  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

When `holderBinding` is absent it is absent from the unsigned-token hash
preimage. The token remains a valid schema-v2 Spend attestation, but portable
holder control is unavailable. A verifier MUST NOT infer holder control from
token possession, `spendId`, a wallet lookup, a delivery key, a ZK proof, or an
issuer signature.

`SpendAttestationTokenV1` and `SpendAttestationTokenV2` are both supported.
There is no protocol-wide token issuance default: each profile or runtime must
explicitly select its issuance behavior, and V2 availability does not select it.

#### Holder commitment

For `scheme = "crinkl.holder.v2"`:

```text
holderCommitmentBytes =
  SHA-256(
    UTF8("crinkl.holder.v2:") ||
    UTF8(spendId) ||
    holderPublicKeyBytes
  )

holderBinding.commitment =
  "sha256:" + lowercaseHex(holderCommitmentBytes)
```

`holderPublicKeyBytes` MUST be one raw 32-byte Ed25519 public key. The holder
MUST use a distinct keypair for every `spendId`; the same public key MUST NOT
be reused across Spend Tokens. Key generation, deterministic vault derivation,
backup, and hardware custody are holder implementation concerns and do not
change this portable verification contract.

The issuer MUST validate the field shape and sign the commitment as part of
the complete unsigned token. The issuer does not need the holder private key.
Once signed, `holderBinding` is immutable for that token and Spend head.
Correction follows the normal supersession rule and MUST preserve the same
holder binding for the same `(issuedBy, spendId)` scope. It MUST NOT rotate
ownership by substituting another commitment.

#### Holder challenge

A relying verifier that needs proof of holder-key control MUST issue or
authenticate one exact challenge:

```text
SpendHolderChallengeV2 {
  domain: "crinkl.spend-holder-challenge.v2",
  schemaVersion: 2,
  nonceBase64: Base64,                 // exactly 32 random bytes
  spendTokenHash: "sha256:" + Hash,
  scopeId: "sha256:" + Hash,
  requestContextHash: "sha256:" + Hash,
  purpose:
    "TOKEN_PRESENTATION" |
    "CAMPAIGN_PROOF_AUTHORIZATION" |
    "CAMPAIGN_ACTION_AUTHORIZATION",
  verifierId: Identifier,
  issuedAt: TimestampISO,
  expiresAt: TimestampISO
}
```

The nonce MUST come from a cryptographically secure random source. The
challenge lifetime MUST be positive and MUST NOT exceed 300 seconds.
`requestContextHash` MUST identify the exact relying request under the
consumer profile. `scopeId`, `requestContextHash`, `purpose`, and `verifierId`
MUST equal the relying verifier's expected context; accepting caller-selected
substitutes is forbidden.

```text
challengeCanonical = RFC8785_canonicalize(SpendHolderChallengeV2)
challengeDigest = SHA-256(UTF8(challengeCanonical))
challengeId = "sha256:" + lowercaseHex(challengeDigest)
```

#### Holder proof

The holder responds:

```text
SpendHolderControlProofV2 {
  schemaVersion: 2,
  scheme: "crinkl.holder.v2",
  spendTokenHash: "sha256:" + Hash,
  scopeId: "sha256:" + Hash,
  challengeId: "sha256:" + Hash,
  holderPublicKeyBase64: Base64,       // raw 32-byte Ed25519 public key
  signatureBase64: Base64              // Ed25519 over raw challengeDigest bytes
}
```

The signature input is the raw 32-byte `challengeDigest`, not its hexadecimal
text and not the prefixed `challengeId` string.

To verify holder control, a verifier MUST:

1. verify the referenced `SpendAttestationTokenV2` normally and require a
   supported `holderBinding`;
2. require the challenge's `spendTokenHash`, `scopeId`,
   `requestContextHash`, `purpose`, and `verifierId` to equal the exact
   expected request context;
3. require that it issued or cryptographically authenticated the challenge,
   that `issuedAt <= now < expiresAt`, that the lifetime is at most 300
   seconds, and that the `(verifierId, nonceBase64)` challenge is outstanding;
4. decode `holderPublicKeyBase64` as exactly 32 bytes, recompute the holder
   commitment from the token's `spendId`, and compare it to the signed
   `holderBinding.commitment`;
5. recompute `challengeId` from the complete challenge and require exact
   equality with the proof;
6. require the proof's `spendTokenHash` and `scopeId` to equal the challenge;
7. verify `signatureBase64` over the raw `challengeDigest`; and
8. only after every preceding check succeeds, atomically consume the
   outstanding challenge. A prior consumption or concurrent consume race MUST
   fail as replay.

The successful claim is limited to:

> The responder controlled the per-Spend private key committed by this signed
> Spend Token for this verifier, scope, exact request context, purpose, and
> fresh challenge.

It does not establish legal identity, a wallet address, a natural person,
cross-Spend same-holder linkage, complete purchase history, qualification,
conversion, settlement recipient binding, or authority to use the Spend
outside the signed scope and purpose.

Repeated presentations of the same token can remain linkable through
`spendId`, `spendTokenHash`, and the disclosed per-Spend public key. The
one-key-per-Spend rule prevents that public key from becoming an additional
cross-Spend identifier; it does not make repeated use of one Spend unlinkable.

**Portability boundary (normative):** verification of this portable token MUST NOT require retrieving the spend-stream from a private operator database. Deep-audit replay against the spend-stream is optional and may be provided via audit bundles.

**Derivation rules (normative):**
- `wallet` is OPTIONAL. When present, it MUST equal the wallet from the spend-stream. Portable tokens intended for third-party verification SHOULD omit `wallet` unless recipient binding is required.
- `SpendStreamEvent.wallet` is internal source scope. `SpendAttestationTokenV1.wallet` is optional disclosure, not a field inherited by default from the spend-stream.

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
- User requests identity-excluded verification or behavioral qualification without identity disclosure

Default for portable tokens intended for external verifiers: **omit wallet**.

**Identity-excluded correlation (normative intent):**

When `wallet` is omitted from Spend Attestation Tokens:
- `spendId` remains present and may be correlatable across verification contexts
- This correlation can reveal spend-pattern reuse without including wallet, user, account, or session identifiers (e.g., "same identity-excluded spend qualified for two different predicates")
- This correlation is not a user identity claim and does not, by itself, disclose wallet, account, or session identity
- This enables legitimate uses: fraud detection (same spend claimed multiple times), incremental sales analysis (did coffee promo drive breakfast purchases), cross-promotion strategy, and aggregate market intelligence

**Identity unlinkability vs. behavioral correlation:** The protocol prevents identity linkage (no persistent user identifier across contexts) while allowing behavioral linkage over identity-excluded spend patterns. This distinction is critical for real-world commerce: verifiers can understand market behavior without tracking individuals.

If a user intentionally discloses `wallet` or uses the same wallet-included token across multiple verifiers, correlation becomes identity-linked. This is a deliberate user action, not a protocol leak.

- `canonical` MUST be derived deterministically from the spend-stream state machine (../01-core/verification-state.md).
- `canonical.status` MUST reflect the final spend attestation state at the time of issuance.
- `canonical.storeHash` MUST be computed deterministically from the canonical store identifier (when available) as:
  - `storeHash = "sha256:" + SHA-256( UTF8("crinkl.store.v1:") || UTF8(storeId) )`, where the `Hash` portion is lowercase hex.
- `canonical.geoRegion` is OPTIONAL. When present, it MUST equal the `geoRegion` from the canonical spend-stream head, expressed as an ISO 3166-2 subdivision code (e.g., `US-CA`) or ISO 3166-1 alpha-2 country code.
- `canonical.cbsaCode` is OPTIONAL. When present, it MUST equal the `cbsaCode` from the canonical spend-stream head, derived from the store's physical location via the OMB CBSA crosswalk (see `../01-core/canonicalization.md#cbsacode`). Portable tokens intended for brand/local-business verification SHOULD include `cbsaCode` when available.
- `lineage.headEventHash` MUST equal the `eventHash` of the last spend-stream event at issuance time.
- `lineage.eventCount` MUST equal the number of spend-stream events included in the canonical replay up to `headEventHash`.
- If `zk.commitments` is present, each commitment MUST commit to canonical Spend fields at `lineage.headEventHash` and MUST be cryptographically bound to `spendId` and `lineage.headEventHash` (see `../06-extensions/zk-proof-extension.md`). Commitments are treated as opaque unless accompanied by a proof; the protocol does not require public recomputation of commitment values.
- ZK commitments and proofs do not strengthen or supersede the verification tier of the underlying Spend; they only enable selective disclosure about already-verified fields.
- **Selective disclosure rule (normative intent):** if a field is intended to be proven via ZK (e.g., `totalCents`, `timestamp`, `storeHash`), portable tokens SHOULD omit that field and rely on `zk.commitments` + proof instead, unless explicit disclosure is required by verifier policy.
- `signatures.signature` MUST be an Ed25519 signature over `signatures.tokenHash`, where `tokenHash = sha256(RFC8785_canonicalize(unsignedToken))`. Domain separation is structural: `tokenType` and `schemaVersion` are included in the hashed unsigned token.

**Optionality rule (normative):** all fields present in the unsigned token are covered by `tokenHash` and therefore by the signature. Absent optional fields are absent from the hash preimage. Optional fields MUST NOT silently change the meaning of `canonical.status`; they may only add additional, non-required context.

### Verification procedure (normative)

To verify a Spend Attestation Token, a verifier MUST:

1. Verify required fields and supported versions (`schemaVersion`, `protocol.protocolVersion`); reject on unsupported versions.
2. Recompute `tokenHash` from the unsigned token (RFC 8785 canonical JSON) and verify `signatures.signature` against `signatures.publicKey`.
3. Verify that `signatures.publicKey` is an authorized issuer key for `signatures.issuedBy` under the applicable trust root mapping (Authority Registry or configured issuer set); reject if unauthorized (see `../00-purpose/threat-model.md#trust-roots`).
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

Spend tokens are snapshots and may be superseded by later spend-stream heads
(corrections/invalidations). Supersession is scoped by `(signatures.issuedBy,
spendId)`. If presented with multiple valid spend tokens for the same scope, a
verifier MUST treat the token with the greatest `lineage.eventCount` as newest.
Tokens with equal `lineage.eventCount` but different `headEventHash` MUST be
treated as invalid/ambiguous (fork or equivocation).

If a spend is corrected/invalidated and the head changes:
- A new Spend Attestation Token MUST be issued for the new head.
- Old spend tokens remain cryptographically valid historical artifacts, but may be obsolete per verifier freshness policy.
- Any ZK proofs or witnesses bound to the old `spendTokenHash` / `headEventHash` MUST NOT be treated as proofs about the new head.
- A schema-v2 successor for the same `(issuedBy, spendId)` MUST preserve the
  existing `holderBinding` when one is present.

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
