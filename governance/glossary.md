---
status: draft
layer: governance
version: v1
normative: true
---

# Glossary

This glossary defines protocol terms used **normatively** across the specification. Implementations and documents MUST use these terms consistently.

Normative keywords (MUST/SHOULD/MAY) in this glossary define **term semantics and invariants only**. Behavioral requirements and verification procedures are specified in the relevant protocol sections (e.g., `../protocol/core/canonicalization.md`, `../protocol/core/spend-event.md`, `../protocol/portability/spend-attestation-token.md`, `../protocol/applications/economics/settlement-bindings.md`).

## Attestation

The protocol’s signed statement about spend state at a given verification tier, derived from spend-stream events and recorded in the Attestation Ledger.

**Attestation is:** a claim about spend state under protocol semantics.  
**Attestation is not:** necessarily portable; not authoritative state independent of the append-only Attestation Ledger history.

## Verification State

The current confidence and status of a Spend Event, derived by replaying its event stream. Verification State is a concept, not a stored artifact — the protocol defines no state database; state is always recomputed from append-only event history.

## Provisional (Soft Attestation)

An attestation produced at **Soft Verification**. It is an intermediate, non-final statement that MUST NOT be treated as canonical Spend attestation.

## Final (Hard Attestation)

An attestation produced at **Hard Verification**. It is a final statement that produces a canonical `Spend` (or declares invalidation) and is suitable for downstream consumption.

## Token

A signed, portable verification artifact with an explicit claim and verification procedure (see `../protocol/portability/spend-attestation-token.md`).

Crinkl tokens follow the **verifiable credential** model: they are issuer-signed claims that holders can present to verifiers for local validation without requiring trust in an API or database query. Unlike static credentials, Crinkl spend tokens are correction-aware—canonical truth may evolve via append-only corrections.

**Token is:** a derived, portable artifact intended for third-party verification.  
**Token is not:** authoritative protocol state (authority lives in append-only streams and, where applicable, on-chain commitments).

**Token version compatibility:** `SpendAttestationTokenV1` and
`SpendAttestationTokenV2` are supported sibling schemas. V2 `holderBinding` is
OPTIONAL, so a V2 token without it remains valid. The protocol has no
protocol-wide token issuance default; a profile or runtime explicitly selects
issuance behavior.

## Verifiable Credential (VC)

A tamper-evident, machine-verifiable claim about a subject, digitally signed by an issuer. Crinkl spend tokens instantiate the VC model for OCR-derived purchase claims:

| VC Role | Crinkl Realization |
|---------|-------------------|
| Issuer | Protocol operator (spend-stream trust root) |
| Holder | Wallet owner (optional; spend truth ≠ ownership) |
| Verifier | Any party checking signatures and applying acceptance policy |
| Claim | Canonical spend fields at a specific verification tier |

Unlike W3C VCs, Crinkl tokens are specialized for correction-aware commerce claims with optional ZK selective disclosure rather than general-purpose identity assertions.

## Verification Service

The party that receives commerce evidence, evaluates it under protocol rules inside the privacy boundary, and signs Spend Attestations and Spend Attestation Tokens. The role names the operator of the spend-stream and token-issuer trust roots; it is not a new trust root category (see `../protocol/purpose/threat-model.md`, `../protocol/core/admission.md`).

**Verification Service is:** the reader of evidence and signer of claims; the origination trust root for spend truth.
**Verification Service is not:** an admission authority; its signature is a proposal toward the record, never network acceptance.

## Proof Validator

Proof validator: a Crinkl protocol role that checks attestation admissibility, proof integrity, uniqueness, and settlement, and finalizes verified GMV. Unrelated to Solana consensus validators.

A party that independently re-verifies deterministic public protocol statements from committed material and co-signs the exact result it checked, so that claims can be admitted to the shared record (see `../protocol/core/admission.md`).

**Proof Validator is:** a public-plane checker of correctness — schema, signatures, key authorization, commitments, roots, totals, nullifier replay scope.
**Proof Validator is not:** a reader of receipts, a prover of ground truth, or a payout authority.

The role is open by conformance and economic exposure through the authority registry. PriceChain Labs is currently the sole reference operator on the alpha network. The alpha quorum is identity/threshold based, not economically bonded or staked; economic bonding, staking, and slashing are deferred to Phase 5 and are not live.

## Selected Committee

The bounded subset of registered proof validators assigned to one statement by an authority-signed assignment artifact. Only selected validators verify, sign, and count toward quorum for that statement; non-selected validators observe and replay certificates asynchronously. Eligibility is not duty.

## Finality Certificate

Quorum evidence of network acceptance: an aggregation of valid selected-validator signatures over the identical deterministic result, under a named registry snapshot, assignment, and quorum rule (`floor(2N/3) + 1` over the selected committee in v1).

**Finality Certificate is:** the only artifact that represents network acceptance of a statement.
**Finality Certificate is not:** payout authority, production chain finality, or proof that covered purchases occurred in the world.

## Admission

The lifecycle stage where a signed claim becomes part of the shared record. A Spend Attestation is **Attested** when the Verification Service signs it and **Admitted** when a validator-finalized statement covers its canonical head (statement-coverage granularity in v1; see `../protocol/core/admission.md`).

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

In this protocol, GMV is always defined with explicit window and “as-of” semantics (see the Verified GMV Token in ../protocol/portability/spend-attestation-token.md).

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

Wallet exposure elsewhere is governed by the **Identity Minimization Invariant**: wallets appear only where verification semantics require them. In protocol v1, `SpendStreamEvent.wallet` is internal event-stream scope for issuer replay, routing, abuse controls, or reward handling. It is not a user identity claim and it is not a requirement for portable Spend Attestation Token verification.

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

**Status:** normative placeholder; statement binding/derivation rules are defined in `../protocol/extensions/zk-foundation.md` and `../protocol/extensions/zk-proof-extension.md`.

## predicateId

A stable identifier for a predicate definition used by routing/distribution, computed as `sha256(RFC8785_canonicalize(predicateDefinition))`.

`predicateDefinition` references `statementId` and adds coordination-layer inputs (for example routing scope, exclusion rules, promoter gate, settlement parameters). It is a pointer artifact and does not change protocol truth or proof verification semantics.

## Campaign Spend Proof Primitive

A finite proof family used to express campaign rules over identity-free Spend Attestation Tokens. The v1 campaign primitive families are Spend Validity, Buyer State, Frequency / Intensity, Category / Competitive Relationship, Market / Context, and Outcome / Conversion.

Campaign Spend Proof Primitives are defined in `../protocol/applications/conditions/campaign-commitment.md`. They compose existing token, proof, scope, nullifier, reward, and commitment surfaces; they do not introduce a new core token type.

## Campaign

A mutable parent container for sponsor objective, campaign type, market scope, and CampaignEpoch history. A Campaign does not itself define final eligibility.

## AnchorBrand

A sponsor or reference brand whose observed activity may help discover a CandidateSet. AnchorBrand activity is discovery input only; it is not campaign eligibility by itself.

## CandidateSet

A discovered set of merchants or merchant references that may be reviewed for campaign use. CandidateSet discovery is not the same as campaign eligibility.

## EligibleMerchant

A merchant entry approved for inclusion in a TargetMerchantSet for a specific campaign epoch.

## TargetMerchantSet

The reviewed set of EligibleMerchant entries bound to a CampaignEpoch by `targetMerchantSetRoot` or `targetMerchantSetHash`.

## CampaignEpoch

An immutable, append-only, funded rule window. A CampaignEpoch binds `campaignId`, `epochId`, `epochVersion`, effective window, timing rule, predicate hash, RuleSetHash, TargetMerchantSet reference, reward rule hash, FundingTranche, claim level, previous epoch reference when present, issuer authority, and creation time.

**Publication boundary:** this is the earlier public `v1.0.0-rc.2` conceptual/experimental CampaignEpoch candidate. It is not wire-compatible with the exact signed adopted engineering `CampaignEpochV1` used by the Campaign Experiment Profile or the adopted-engineering dependency in the Direct Buyer Reward release-candidate package. See `../protocol/extensions/campaign-experiment-profile.md` and `../protocol/extensions/campaign-direct-buyer-reward-profile.md`.

## CampaignAmendment

A forward-only event that closes or supersedes a prior CampaignEpoch and appends a new CampaignEpoch. A CampaignAmendment MUST NOT mutate prior epochs.

## FundingTranche

A budget allocation bound to a specific CampaignEpoch. A FundingTranche may fund rewards only under the rule set it was committed to.

Budget increases are represented as child FundingTranche records (`parentFundingTrancheId`) bound to the same CampaignEpoch and same RuleSetHash. The original FundingTranche amount MUST NOT be mutated.

## RuleSetHash

The canonical hash over predicate, TargetMerchantSet reference/root, reward rule, claim level, effective window, timing rule, and funding reference.

## ClaimLevel

The campaign claim strength asserted by a CampaignEpoch. Allowed values are:

- `OBSERVED` — verified spend occurred under the epoch rule.
- `ATTRIBUTED` — spend matched attribution conditions defined by the epoch.
- `INCREMENTAL` — requires a baseline, holdout, or incrementality method specified by the epoch.

The `INCREMENTAL` value above belongs to the earlier experimental public candidate. It does not make an individual receipt, conversion, or Epoch a causal result. In the Campaign Experiment Profile, incrementality is a cohort- or market-level derived result under the frozen measurement method.

## Campaign Experiment Policy

The signed, immutable optional policy that binds one exact adopted Campaign Epoch and pre-state evaluation context to deterministic exclusive pre-exposure assignment, one intervention-policy reference per arm, an exposure-coverage policy, and a measurement-method reference. The public profile is a publication draft and is not released `v1.0.0-rc.2` conformance.

## Campaign Direct Buyer Reward Policy

The engineering-candidate signed policy resolved by one exact adopted-engineering `CampaignEpochV1.rewardPolicyRef`. It fixes one buyer reward leg, no promoter/referrer split, exact reward terms and outcome-evidence references, and an explicit boundary that affiliate link/coupon use and commission do not determine the buyer reward.

**Publication boundary:** the public profile and byte-pinned package are released in
`v1.0.0-rc.3` / conformance suite 2. Profile release does not establish
product-purchase evidence, funding, escrow, settlement, validator finality,
runtime, deployment, or production availability.

## ProofOfMatch

The campaign-facing spelling of Proof of Match. A ProofOfMatch evaluates spend against exactly one CampaignEpoch and is downstream of Spend Attestation.

## RewardCommitment

The campaign-facing spelling of Reward Commitment. A RewardCommitment is produced only after valid proof material such as ProofOfMatch and records downstream economic consequence without changing spend truth.

## Eligibility Rule

The audience-side criteria a campaign uses to admit a holder into a campaign flow. Eligibility Rule is a role a Spend Predicate plays inside a campaign, not a distinct object type.

## Eligibility Proof

Evidence that a holder satisfies a campaign's Eligibility Rule. Eligibility Proof is a role a ProofOfMatch plays inside a campaign, not a distinct object type.

## Conversion Rule

The outcome-side criteria a campaign uses to determine that its required commerce event occurred. Conversion Rule is a role a Spend Predicate plays inside a campaign, not a distinct object type.

## Conversion Proof

Evidence that a holder satisfied a campaign's Conversion Rule. Conversion Proof is a role a ProofOfMatch plays inside a campaign, not a distinct object type.

## Audience Qualification

A campaign-scoped proof that a holder satisfies the audience side of a Campaign Rule. Audience Qualification is a marketing-facing term for qualification proof over Campaign Spend Proof Primitives.

Audience Qualification MUST NOT mint a Spend Attestation Token. It only proves campaign qualification within an explicit scope and time window.

## Verified Conversion

A campaign-scoped proof that the required commerce outcome occurred. In payout-bearing campaigns, a Verified Conversion references a Spend Attestation Token produced by the normal verification pipeline.

Verified Conversion is a marketing-facing term for an Outcome / Conversion proof. It is not a new token type.

## Conversion Approval

A ProofOfMatch that has reached finality for a campaign flow: the state in which Audience Qualification and Verified Conversion have satisfied a Campaign Rule and settlement may proceed. Conversion Approval is a state, not a distinct object type.

The finalized state binds the campaign parameters, qualification proof, conversion Spend Token hash, payout terms, settlement scope, and settlement nullifier.

## Issuer Key History

The sequence of an issuer's key registrations and revocations over time. Issuer Key History is a concept, derivable from the series of `IssuerRegistrySnapshot` artifacts plus the `AUTHORITY_REGISTERED`/`AUTHORITY_REVOKED` system-stream events; it is not a fourth representation requiring its own artifact.

## Campaign Settlement Commitment

A public settlement commitment for cleared campaign conversions. It is represented by `CAMPAIGN_SETTLEMENT_COMMITTED` plus a Merkle root over `CampaignSettlementLeafV1` leaves.

Campaign Settlement Commitment is not a token and does not publish raw audience proofs, raw Spend Tokens, wallet identities, raw receipt data, or sensitive market details. It binds campaign settlement to campaign parameters, verifier approval, conversion Spend Token hash, payout totals, authority signature, and public chain anchoring.

## ZK Witness

Wallet-only private material that allows a holder to open ZK commitments and generate ZK statement proofs (e.g., openings for `zk.commitments.C_total`). ZK witness material is not portable and must be treated as sensitive.

## Redemption Scope

A canonical, hash-identifiable scope used to make redemption proofs and dedupe **non-linkable across campaigns** while still allowing “only once” enforcement by a verifier.

## scopeId

A stable identifier for a redemption scope, typically computed as `sha256(RFC8785_canonicalize(scope))`.

**Status:** normative placeholder; the exact binding requirements for redemption are defined in `../protocol/extensions/zk-foundation.md` (and may evolve without changing core token classes).

## Nullifier

A verifier-storable, scope-specific identifier used to enforce anti-replay (“only once”) redemption without revealing wallet identity. A nullifier is unique per *(wallet secret, scopeId)* and should not be linkable across different scopes.

## Ciphertext Observation Ack

A wallet-produced acknowledgement that proves the wallet observed (decrypted) an encrypted payload by returning an authentication artifact bound to a nonce that exists only inside the ciphertext.

## eventHash

The SHA-256 hash of a single event envelope’s RFC 8785 canonical JSON, excluding `eventHash` and `signature` fields (see `canonicalization.md`).

**eventHash is:** the canonical event identifier used for integrity and stream linkage.  
**eventHash is not:** an application-chosen identifier.

## headEventHash

The `eventHash` of the current terminal head of a spend’s canonical spend-stream at a specific point in time (used for lineage binding in tokens and ZK material).

**headEventHash is:** a pointer to a specific spend attestation head.  
**headEventHash is not:** stable across corrections; it is expected to change when a spend is corrected/invalidated.

## tokenHash

The SHA-256 hash of an unsigned token’s RFC 8785 canonical JSON (the bytes that are signed), as defined in `../protocol/portability/spend-attestation-token.md`.

**tokenHash is:** the signing/verification digest for portable tokens.  
**tokenHash is not:** an `eventHash` and does not imply anything about the spend-stream beyond what the token claims.

## leafHash

The SHA-256 digest of a Merkle leaf preimage under the protocol’s Merkle conventions:
- `leafHash = SHA-256(0x00 || leafBytes)` (see `../protocol/applications/economics/settlement-bindings.md#merkle-tree` and `../protocol/portability/spend-attestation-token.md#spendheadsetroot-construction-normative`).

**leafHash is:** the domain-separated digest of a canonical leaf object.  
**leafHash is not:** an `eventHash` or `tokenHash`, and does not carry stream linkage semantics.

## emptyLeafHash

The fixed padding hash used to pad Merkle trees to a power of two:
- `emptyLeafHash = SHA-256(0x00 || "")` (see `../protocol/applications/economics/settlement-bindings.md#merkle-tree`).

**emptyLeafHash is:** padding only.  
**emptyLeafHash is not:** an admissible “real leaf”.
