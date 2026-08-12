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

A Crinkl protocol role, unrelated to Solana consensus validators, that
independently verifies an exact public protocol subject under an exact named
procedure and signs the canonical decision it reached.

**Proof Validator is:** a public-plane checker of schema, signatures, key
authorization, proof profiles, public inputs, commitments, roots, arithmetic,
and declared replay/nullifier registry views.

**Proof Validator is not:** a reader of private receipts or witnesses unless a
profile explicitly discloses them; a prover of ground truth; a Campaign
authority; an assignment, economic-admission, Outcome, Reward Ledger, escrow,
or payout authority.

The role is open by conformance and economic exposure through the authority registry. PriceChain Labs is currently the sole reference operator on the alpha network. The alpha quorum is identity/threshold based, not economically bonded or staked; economic bonding, staking, and slashing are deferred to Phase 5 and are not live.

## Selected Committee

The bounded subset of registered proof validators assigned to one statement by an authority-signed assignment artifact. Only selected validators verify, sign, and count toward quorum for that statement; non-selected validators observe and replay certificates asynchronously. Eligibility is not duty.

## ValidatorCertificate

A Proof Validator quorum certificate over one exact `subjectType` and
`subjectHash` under one exact `procedureId`, validator-set reference, and
quorum-policy reference. Target `ValidatorCertificateV1` is restricted to
`PROOF_OF_MATCH_VERIFICATION` and declares `stateTransition = NONE`.

**ValidatorCertificate is:** quorum acceptance of the exact subject under the
declared procedure.

**ValidatorCertificate is not:** global immutability, a canonical nullifier
write, Campaign assignment, an Outcome, a Reward Obligation, payout authority,
production-chain finality, or proof that a purchase occurred in the world.

## Finality Certificate

The existing certificate used by the implemented Spend statement-coverage
admission pipeline. Its scope is defined by
[`protocol/core/admission.md`](../protocol/core/admission.md). It is not a
Campaign object and MUST NOT be used for Campaign proof acceptance;
`ValidatorCertificate` is the only Campaign certificate term.

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

The immutable, signed version of a Campaign's rules and economic terms. It
binds or commits audience rule when present, conversion rule, assignment policy
when present, reward policy, economic-admission/capacity/budget/allocation/reuse
constraints, timing and observation windows, resolution and dispute policies,
required proof profiles, Campaign authority, and applicable registries.

`CampaignEpochV2` is the reduced-spine Campaign schema candidate and is
`SPECIFIED_NOT_IMPLEMENTED`. Adopted `CampaignEpochV1` remains a distinct,
immutable object-family version.

## ProofOfMatch

One standardized Crinkl ZK statement establishing that one or more
authenticated private commerce facts satisfy the audience or conversion rule
committed by exactly one Campaign Epoch. Purpose is `AUDIENCE` or `CONVERSION`;
it does not select a different proof family.

## AssignmentRecord

Optional portable evidence of deterministic experimental-arm assignment under
the Epoch policy. It is a protocol object only when assignment crosses a system
or authority boundary, supports a dispute, or has an independent consumer;
otherwise assignment remains application state. Assignment does not prove
exposure.

## Economic Admission

The deterministic, auditable decision that an accepted match receives capacity
under the Epoch's budget, inventory, FIFO/allocation, or recipient-limit policy.
It is runtime or ledger state by default, not a ZK proof and not automatically a
standalone object. Proof validity alone does not establish entitlement when the
Epoch makes admission capacity-dependent.

## CampaignOutcome

The narrow application-level composition of the applicable Epoch, accepted
audience and conversion matches, optional assignment/exposure, optional
economic admission, and nullifiers. It determines measurement contribution and
whether committed policy creates an exact Reward Obligation. It is not a ZK
primitive or discretionary payout approval.

## RewardObligation

A recipient-scoped reward liability deterministically created by an eligible
Campaign Outcome. It records what is owed under an exact resolution policy and
does not prove payment.

## SettlementRecord

Evidence that one Reward Obligation was paid, reversed, expired, disputed,
cancelled, or otherwise resolved. It is separate from liability creation and
does not establish proof validity or Campaign entitlement.

## CampaignReport

Derived application output over assignments, exposure coverage, economic
admissions, and Campaign Outcomes under a frozen measurement method. It is not
a cryptographic primitive, Validator Certificate, or per-user causal claim.

## Eligibility Rule

The audience-side criteria a campaign uses to admit a holder into a campaign flow. Eligibility Rule is a role a Spend Predicate plays inside a campaign, not a distinct object type.

## Eligibility Proof

Business phrase for `ProofOfMatch(purpose = AUDIENCE)`, not a distinct proof
type.

## Conversion Rule

The outcome-side criteria a campaign uses to determine that its required commerce event occurred. Conversion Rule is a role a Spend Predicate plays inside a campaign, not a distinct object type.

## Conversion Proof

Business phrase for `ProofOfMatch(purpose = CONVERSION)`, not a distinct proof
type.

## Audience Qualification

Business term for an accepted `ProofOfMatch(AUDIENCE)`. It does not mint a
Spend Token, assign an experimental arm, prove exposure, or create economic
entitlement.

## Verified Conversion

Business term for an accepted `ProofOfMatch(CONVERSION)` over one or more Spend
Tokens produced by the normal verification pipeline. It is not a new token,
Campaign Outcome, or economic-admission decision.

## Issuer Key History

The sequence of an issuer's key registrations and revocations over time. Issuer Key History is a concept, derivable from the series of `IssuerRegistrySnapshot` artifacts plus the `AUTHORITY_REGISTERED`/`AUTHORITY_REVOKED` system-stream events; it is not a fourth representation requiring its own artifact.

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
