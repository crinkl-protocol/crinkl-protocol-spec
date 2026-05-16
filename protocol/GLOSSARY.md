# Glossary

This glossary defines protocol terms used **normatively** across the specification. Implementations and documents MUST use these terms consistently.

Normative keywords (MUST/SHOULD/MAY) in this glossary define **term semantics and invariants only**. Behavioral requirements and verification procedures are specified in the packeted protocol sections (e.g., `DATA_STRUCTURES.md`, `EVENTS.md`, `TOKENS.md`, `COMMITMENT_LAYER.md`).

## Attestation

The protocol’s signed statement about spend state at a given verification tier, derived from spend-stream events and recorded in the Attestation Ledger.

**Attestation is:** a claim about spend state under protocol semantics.  
**Attestation is not:** necessarily portable; not authoritative state independent of the append-only Attestation Ledger history.

## Provisional (Soft Attestation)

An attestation produced at **Soft Verification**. It is an intermediate, non-final statement that MUST NOT be treated as canonical Spend attestation.

## Final (Hard Attestation)

An attestation produced at **Hard Verification**. It is a final statement that produces a canonical `Spend` (or declares invalidation) and is suitable for downstream consumption.

## Token

A signed, portable verification artifact with an explicit claim and verification procedure (see `TOKENS.md`).

Crinkl tokens follow the **verifiable credential** model: they are issuer-signed claims that holders can present to verifiers for local validation without requiring trust in an API or database query. Unlike static credentials, Crinkl spend tokens are correction-aware—canonical truth may evolve via append-only corrections.

**Token is:** a derived, portable artifact intended for third-party verification.  
**Token is not:** authoritative protocol state (authority lives in append-only streams and, where applicable, on-chain commitments).

## Verifiable Credential (VC)

A tamper-evident, machine-verifiable claim about a subject, digitally signed by an issuer. Crinkl spend tokens instantiate the VC model for OCR-derived purchase claims:

| VC Role | Crinkl Realization |
|---------|-------------------|
| Issuer | Protocol operator (spend-stream trust root) |
| Holder | Wallet owner (optional; spend truth ≠ ownership) |
| Verifier | Any party checking signatures and applying acceptance policy |
| Claim | Canonical spend fields at a specific verification tier |

Unlike W3C VCs, Crinkl tokens are specialized for correction-aware commerce claims with optional ZK selective disclosure rather than general-purpose identity assertions.

## Attestation Ledger

The append-only, per-`spendId` event stream that records verification state transitions (Soft/Hard verification, invalidation, correction). It is the protocol’s authoritative history for spend state.

## Reward Ledger

The append-only event stream of reward issuance (`REWARD_*_ISSUED`) gated by verification tier. Reward entries are immutable once issued.

## Reward Issuance

The act of emitting a reward ledger event (provisional or final) derived from application-layer policy, gated by protocol verification tier.

## Commitment (Commitment Layer)

An **external** cryptographic commitment to reward issuance history, typically by publishing a Merkle root to an immutable chain. Commitments provide non-repudiation and public verifiability of reward issuance, not independent verification of spend attestation.

**Commitment is:** anchoring evidence for reward issuance artifacts.  
**Commitment is not:** a spend claim; not a replacement for spend attestation semantics.

## Backing (Economic Backing)

An operator-asserted, externally verifiable economic action intended to back reward liabilities (e.g., moving cbBTC/USDC into a designated vault). Backing increases the strength of *economic* guarantees for rewards but does not change the semantics of spend attestations.

## Economic Tier

A protocol-defined, machine-readable label on Reward Commitment Tokens that states which minimum evidence is present for economic guarantees (e.g., committed only vs committed + externally verifiable backing).

## Spend-Stream

The per-`spendId` event stream of protocol events. Ordering is enforced via `prevHash` chaining.

## System-Stream

The per-`chainId` event stream of protocol system events (e.g., authority registry and reward batch commitments). Ordering is enforced via `prevHash` chaining.

## GMV (Gross Merchandise Value)

An aggregate sum of spend totals over a specified time window.

In this protocol, GMV is always defined with explicit window and “as-of” semantics (see the Verified GMV Token in TOKENS.md).

## Verified GMV

GMV computed by summing canonical (hard-verified and corrected) spend totals for a given window, as-of a specific computation time; it may change over time as corrections append.

## Verified Spend Distribution

A privacy-preserving aggregate breakdown of verified spend by category and geographic bucket for a given window, as-of a specific computation time. It shares the same snapshot semantics as Verified GMV and MUST NOT expose wallet identifiers, recipient references, or per-user spend patterns.

## Issued GMV (Rewarded GMV)

GMV derived from reward issuance artifacts (append-only with no clawbacks), and therefore should remain stable for a given policy epoch.

**Relationship invariant:** Issued GMV MAY diverge permanently from Verified GMV due to corrections/invalidations after issuance; the protocol does not assume clawbacks as a mechanism to force equality.

## RecipientRef

A unique recipient identifier used to scope reward commitment leaves. The representation is implementation-defined:

- `WalletRef` — transparent wallet address (schema v1a, v2a)
- `Commitment` — blinded commitment hash (schema v1b, v2b)
- Other cryptographic identifier as defined by future schemas

Wallet semantics (address routing, ownership verification) are application-layer concerns. The Commitment Layer proves that rewards were issued and economically committed; it does not define who a user is or how value is routed, only that issuance occurred under a verifiable recipient scope.

**RecipientRef is:** an identifier used for deterministic recipient-scoped aggregation and inclusion proofs.  
**RecipientRef is not:** a protocol-level identity; not required to be globally stable across time.

**Stability/rotation (normative intent):**
- In transparent schemas (v1a/v2a), `RecipientRef` is a `WalletRef` and is stable across batches by definition.
- In blinded schemas (v1b/v2b), `RecipientRef` is computed with `batchId` and a user-held blinder and therefore is **intentionally per-batch** (not stable across batches).

**Mapping notes (normative intent):**
- Multiple `RecipientRef` values MAY correspond to the same underlying wallet across different batches (blinded schemas).
- In any given batch commitment tree, each recipient scope MUST appear at most once (one leaf per recipient per batch).

## WalletRef

A reference to a wallet address (Solana public key or equivalent). In the Commitment Layer, `WalletRef` is one representation of `RecipientRef` (transparent schemas v1a, v2a).

Wallet exposure elsewhere is governed by the **Identity Minimization Invariant**: wallets appear only where verification semantics require them.

- **Spend Attestation Tokens**: `wallet` is **optional**—spend truth does not imply ownership.
- **Reward Commitment Tokens**: `recipientId` is **required**—but MAY be `WalletRef` or `Commitment` per schema.
- **Verified GMV Tokens**: `wallet` is **prohibited**—aggregate claims have no wallet semantics.
- **Verified Spend Distribution Tokens**: `wallet` is **prohibited**—aggregate distribution claims have no wallet semantics.

**Deployment note (non-normative):** In early deployments, an Issuer MAY treat `WalletRef` as an issuer-provisioned or custodial wallet address (i.e., a routing scope for value), rather than a user-supplied self-custody address. This does not change protocol semantics: spend truth does not imply ownership, and any mapping from app user → wallet is application-layer and out of protocol.

**Visibility note (normative intent):**
- If `WalletRef` is used as `RecipientRef` (schemas v1a/v2a), it is expected to be publicly observable in on-chain commitment artifacts.
- If blinded recipient schemas are used (v1b/v2b), `WalletRef` is not present in on-chain commitment artifacts; it may be revealed selectively by the recipient when proving inclusion.

## ZK Statement

A machine-readable rule about a Spend (or other committed protocol facts) that can be proven true with a zero-knowledge proof without revealing the underlying fields.

## statementId

A stable identifier for a ZK statement, typically computed as `sha256(RFC8785_canonicalize(statementDefinition))`.

**Status:** normative placeholder; statement binding/derivation rules are defined in `ZK_FOUNDATION.md`, `ZK_LAYER.md`, and the proof shapes in `TOKENS.md`.

## predicateId

A stable identifier for a predicate definition used by routing/distribution, computed as `sha256(RFC8785_canonicalize(predicateDefinition))`.

`predicateDefinition` references `statementId` and adds coordination-layer inputs (for example routing scope, exclusion rules, promoter gate, settlement parameters). It is a pointer artifact and does not change protocol truth or proof verification semantics.

## Campaign Spend Proof Primitive

A finite proof family used to express campaign rules over identity-free Spend Attestation Tokens. The v1 campaign primitive families are Spend Validity, Scoped Buyer State, Frequency / Intensity, Category / Competitive Relationship, Market / Context, and Outcome / Conversion.

Campaign Spend Proof Primitives are defined in `CAMPAIGN_SPEND_PROOF_PRIMITIVES.md`. They compose existing token, proof, scope, nullifier, reward, and commitment surfaces; they do not introduce a new core token type.

## Audience Qualification

A campaign-scoped proof that a holder satisfies the audience side of a Campaign Rule. Audience Qualification is a marketing-facing term for qualification proof over Campaign Spend Proof Primitives.

Audience Qualification MUST NOT mint a Spend Attestation Token. It only proves campaign qualification within an explicit scope and time window.

## Verified Conversion

A campaign-scoped proof that the required commerce outcome occurred. In payout-bearing campaigns, a Verified Conversion references a Spend Attestation Token produced by the normal verification pipeline.

Verified Conversion is a marketing-facing term for an Outcome / Conversion proof. It is not a new token type.

## Conversion Approval

A verifier-signed decision that Audience Qualification and Verified Conversion satisfy a Campaign Rule and may proceed to settlement.

Conversion Approval binds the campaign parameters, qualification proof, conversion Spend Token hash, payout terms, settlement scope, and settlement nullifier.

## Campaign Settlement Commitment

A public settlement commitment for cleared campaign conversions. It is represented by `CAMPAIGN_SETTLEMENT_COMMITTED` plus a Merkle root over `CampaignSettlementLeafV1` leaves.

Campaign Settlement Commitment is not a token and does not publish raw audience proofs, raw Spend Tokens, wallet identities, raw receipt data, or sensitive market details. It binds campaign settlement to campaign parameters, verifier approval, conversion Spend Token hash, payout totals, authority signature, and public chain anchoring.

## ZK Witness

Wallet-only private material that allows a holder to open ZK commitments and generate ZK statement proofs (e.g., openings for `zk.commitments.C_total`). ZK witness material is not portable and must be treated as sensitive.

## Redemption Scope

A canonical, hash-identifiable scope used to make redemption proofs and dedupe **non-linkable across campaigns** while still allowing “only once” enforcement by a verifier.

## scopeId

A stable identifier for a redemption scope, typically computed as `sha256(RFC8785_canonicalize(scope))`.

**Status:** normative placeholder; the exact binding requirements for redemption are defined in `ZK_FOUNDATION.md` (and may evolve without changing core token classes).

## Nullifier

A verifier-storable, scope-specific identifier used to enforce anti-replay (“only once”) redemption without revealing wallet identity. A nullifier is unique per *(wallet secret, scopeId)* and should not be linkable across different scopes.

## Ciphertext Observation Ack

A wallet-produced acknowledgement that proves the wallet observed (decrypted) an encrypted payload by returning an authentication artifact bound to a nonce that exists only inside the ciphertext.

## eventHash

The SHA-256 hash of a single event envelope’s RFC 8785 canonical JSON, excluding `eventHash` and `signature` fields (see `DATA_STRUCTURES.md`).

**eventHash is:** the canonical event identifier used for integrity and stream linkage.  
**eventHash is not:** an application-chosen identifier.

## headEventHash

The `eventHash` of the current terminal head of a spend’s canonical spend-stream at a specific point in time (used for lineage binding in tokens and ZK material).

**headEventHash is:** a pointer to a specific spend attestation head.  
**headEventHash is not:** stable across corrections; it is expected to change when a spend is corrected/invalidated.

## tokenHash

The SHA-256 hash of an unsigned token’s RFC 8785 canonical JSON (the bytes that are signed), as defined in `TOKENS.md`.

**tokenHash is:** the signing/verification digest for portable tokens.  
**tokenHash is not:** an `eventHash` and does not imply anything about the spend-stream beyond what the token claims.

## leafHash

The SHA-256 digest of a Merkle leaf preimage under the protocol’s Merkle conventions:
- `leafHash = SHA-256(0x00 || leafBytes)` (see `COMMITMENT_LAYER.md#merkle-tree` and `TOKENS.md#spendheadsetroot-construction-normative`).

**leafHash is:** the domain-separated digest of a canonical leaf object.  
**leafHash is not:** an `eventHash` or `tokenHash`, and does not carry stream linkage semantics.

## emptyLeafHash

The fixed padding hash used to pad Merkle trees to a power of two:
- `emptyLeafHash = SHA-256(0x00 || "")` (see `COMMITMENT_LAYER.md#merkle-tree`).

**emptyLeafHash is:** padding only.  
**emptyLeafHash is not:** an admissible “real leaf”.
