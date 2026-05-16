# Spend Tokens
## Spend Attestations, Commitments, and Aggregate Tokens: A Minimal Token Set for Economic Truth

Draft (based on Crinkl Protocol v1.0.0-rc.1)
Authors: Alvin Tanpoco with AI-assisted drafting and formalization
Status: Working draft / canonical explainer
Last updated: 2026-01-03

This document is a non-normative explainer aligned with Crinkl Protocol v1.0.0-rc.1.
Normative rules live in `protocol/INTRODUCTION.md`, `protocol/TOKENS.md`,
`protocol/STATE_MACHINES.md`, `protocol/SECURITY_MODEL.md`, and related references.

If this explainer uses MUST/SHOULD/MAY, it mirrors normative requirements in those
core documents; it does not introduce new requirements.

## Abstract

Modern systems make decisions from reported commerce: marketing allocation, loyalty,
creator payouts, underwriting, agent recommendations, and forecasts. Most commerce
data, however, is not portable or independently verifiable: it is siloed in private
logs, inferred by opaque attribution, or exposed only through trusted APIs.

Spend Tokens define a minimal set of issuer-signed, machine-verifiable artifacts
that represent (1) canonical spend truth under uncertainty, (2) economic actions
taken on that truth, and (3) aggregate economic throughput, while minimizing
identity exposure. Tokens are portable (verifiable without private APIs),
correction-aware (truth evolves via append-only events), and separable from
application-layer economics (funding and incentives). Optional zero-knowledge
predicates support eligibility proofs without revealing receipt details.

This explainer presents token semantics, verification procedures, portability
boundaries, privacy guardrails, and extensions (ZK predicates, deterministic
bucketing, on-chain commitments), along with usage patterns and explicit non-claims.

## 1. Purpose and Scope

We want a verifier to answer four questions using portable artifacts:

1) Is this spend true under protocol-defined verification rules?
2) Was value issued because of this spend, and can that issuance be proven later?
3) How much verified activity occurred in a time window, without revealing users?
4) Where is verified activity distributed by category or market bucket, without revealing users?

These answers should be deterministic, correction-aware, portable, and
identity-minimizing.

### Non-goals (explicit)

Spend Tokens do not attempt to:
- prove merchant authenticity or payment settlement/finality,
- prove the absence of fraud beyond protocol verification tiers,
- establish user intent or ownership unless explicitly stated,
- replace application-specific economics, incentives, or payout logic.

## 2. Definitions (informative)

- Spend stream: Append-only event sequence keyed by `spendId`.
- Head event / `headEventHash`: The current end of the spend stream.
- Canonical spend: The state derived by replaying the spend stream per protocol.
- Verification tier: Protocol-defined confidence tier (e.g., SOFT, HARD).
- As-of time: The computation time that a snapshot claims to reflect.
- Lineage: The binding from a token to a spend-stream head (e.g., `headEventHash`).
- Token hash: SHA-256 of RFC 8785 canonical JSON for the unsigned token.
- Portable verifier: A verifier that can decide validity from public inputs only.

## 3. Design Principles

### 3.1 Separation of truth and economics

- Spend truth is an epistemic commitment: a claim about what is true under
  protocol rules at a point in time.
- Economic action is an economic commitment: a record that value was issued.

Truth can be corrected without rewriting economic history. Economic issuance can
be audited without trusting private operator claims.

### 3.2 Scarcity through process, not syntax

Tokens are scarce because producing them correctly is costly: it requires real
commerce, verification under protocol rules, and (for economic commitments) a
cryptographically anchored issuance record.

### 3.3 Minimal identity exposure

Canonical spend truth and aggregate throughput claims do not require identity.
Identity appears only where it is necessary to verify economic issuance.

The issuer's internal spend stream can be wallet-scoped for replay, routing,
abuse controls, and reward handling. The portable Spend Attestation Token is not
the internal stream: it proves a commerce fact and should omit wallet, user,
account, and session identifiers by default.

### 3.4 Explicit non-claims

Unless explicitly stated, tokens do not prove user intent/ownership, merchant
authenticity, payment settlement/finality, or absence of fraud.

## 4. Core Model: Spend as an Event-Sourced Stream

A spend is represented as an append-only event stream keyed by `spendId`. The
canonical spend truth is derived by replaying events. Corrections append new
events; prior events remain.

Key properties:
- Append-only: corrections add events; history is never rewritten.
- Correction-aware: canonical truth can evolve via new events.
- Tiered verification: provisional and authoritative tiers are supported.

Spend Tokens are snapshots over the canonical stream and bind to a specific head
via a lineage hash (e.g., `headEventHash`).

## 5. Token Framework

### 5.1 Shape: issuer-signed verifiable artifacts

Spend Tokens follow the verifiable credential pattern: a signed claim object that
holders can present to verifiers who validate signatures and apply acceptance
policies.

### 5.2 Deterministic hashing and signing

- Canonical serialization: RFC 8785 (canonical JSON)
- Digest: SHA-256 over canonical bytes (tokenHash)
- Signature: Ed25519 by an authorized issuer key

Key hashes:
- `eventHash`: SHA-256 hash of a canonical event envelope
- `headEventHash`: pointer to a specific spend-stream head
- `tokenHash`: SHA-256 hash of the canonical unsigned token

### 5.3 Portability boundary

A token is portable if a verifier can compute a definitive validity result using
only the token, its included proof material, public trust roots, and public chain
or public protocol data when referenced.

Portable verification MUST NOT depend on private operator databases, non-public
state, or trusting an HTTP API response as truth.

**Portable verification inputs (allowed):**
- token bytes and embedded proofs (Merkle proofs, ZK artifacts)
- public trust roots / authorized issuer keysets
- public chain data when referenced by a token

**Disallowed dependencies:**
- private APIs, logs, or database queries
- non-public pipeline state
- raw receipt images or OCR text
- local file paths, storage keys, or ingestion metadata

Portable tokens may include hashed references and commitment-safe roots/proofs.

## 6. The Four Core Spend Token Types

The Crinkl Protocol defines four core token outputs as the minimal basis for
representing economic truth, economic action, aggregate scale, and aggregate distribution.

### 6.1 Spend Attestation Token

**Purpose:** canonical truth under uncertainty.

**Asserts:**
- A spend exists and reached a canonical verification state under protocol rules.
- Canonical spend fields (e.g., totals, timestamps, store hash) per schema.
- Verification tier (e.g., HARD verified).
- Lineage binding to a spend-stream head (`headEventHash`).
- Issuer signature.

**Does not assert:**
- Ownership.
- Reward entitlement.
- Aggregate behavior.

**Interpretation:** This is a snapshot as of issuance time. If a spend is later
corrected, a newer token may supersede prior snapshots for that spend.

### 6.2 Reward Commitment Token

**Purpose:** economic consequence made verifiable.

**Asserts:**
- A reward issuance occurred under a defined batch and policy.
- Recipient identifier as required by schema (wallet or blinded commitment).
- Commitment information tying issuance to an auditable record (off-chain ledger
  and/or on-chain commitment).

**Does not assert:**
- Current balance.
- Current spend validity "as of now."
- Clawback or reversal semantics unless explicitly specified elsewhere.

### 6.3 Verified GMV Token

**Purpose:** aggregate economic throughput without surveillance.

**Asserts:**
- As of a computation time, total verified spend for a fixed window equals X.
- Total volume and spend count for the window.
- A commitment to which spends were counted (e.g., root or set commitment).

**Does not assert:**
- User identities.
- Individual receipts.
- Reward balances.

**Interpretation:** Verified GMV is a snapshot with explicit as-of semantics.
Tokens can be reissued for the same window as corrections occur.

### 6.4 Verified Spend Distribution Token

**Purpose:** aggregate category and market distribution without surveillance.

**Asserts:**
- As of a computation time, verified spend is distributed across declared categories and geographic buckets as shown.
- Aggregate totals and counts per category and, when present, per geographic bucket.
- The same spend snapshot model and `spendHeadSetRoot` semantics as the Verified GMV Token.

**Does not assert:**
- User identities.
- Individual receipts.
- Reward balances or ownership.

**Interpretation:** Verified Spend Distribution is a privacy-safe dimensional snapshot. Tokens can be reissued for the same window as corrections occur.

## 7. Verification: What a Verifier Does

A portable verifier generally performs:

1) Canonicalization: RFC 8785 canonical JSON for unsigned token bytes.
2) Hashing: compute `tokenHash = SHA-256(canonical_bytes)`.
3) Signature verification: verify Ed25519 signature against authorized issuer
   keys for the token's protocol version and scope.
4) Acceptance policy: apply local rules (tier requirements, issuer allowlists,
   latest-as-of selection, etc.).
5) Optional proof checks: verify Merkle inclusion proofs, authority registry
   references, or ZK proofs if included.

Acceptance policy is intentionally local. Different verifiers can choose stricter
or looser thresholds while relying on the same canonical semantics.

## 8. Supersession and Correction Awareness

Tokens are immutable artifacts after signing. Corrections do not mutate prior
tokens; they emit new events and new tokens.

- Spend tokens: new heads supersede old snapshots for the same `spendId`.
- Verified GMV tokens: reissued for the same window; verifiers choose the newest
  trusted `computedAt` for "latest-as-of" semantics.
- Verified Spend Distribution tokens: reissued for the same window and snapshot model as Verified GMV.
- Reward commitments: do not roll back by default when spends are corrected.

This maintains a stable audit trail while supporting operational correction.

## 9. Privacy Model and Guardrails

### 9.1 Identity minimization defaults

- Spend truth does not require identity exposure (truth != ownership).
- Verified GMV explicitly prohibits recipient identity exposure.
- Reward commitments include a recipient identifier only because issuance must be
  auditable.
- Wallet scope in the issuer's internal stream is not a portability requirement.
  A portable Spend Attestation Token can be identity-free even when derived from
  a wallet-scoped event stream.

### 9.2 Portable token "no footguns"

Portable tokens MUST NOT contain:
- receipt images,
- raw OCR text,
- local file paths or storage object keys,
- ingestion pipeline metadata that could deanonymize users or systems.

Portable tokens MAY contain:
- hashed identifiers (e.g., storeHash),
- `headEventHash`,
- Merkle roots/proofs and ZK artifacts designed not to leak receipt details.

## 10. Trust Model and Threat Boundaries (informative)

Assumptions:
- Verifiers trust the issuer authorization model and public trust roots
  appropriate to the protocol version.

Threat boundaries:
- Issuer key compromise invalidates trust for affected signatures.
- Malicious submitters can attempt fraud; verification tiers bound confidence but
  do not claim fraud impossibility.
- A verifier that ignores acceptance policy can accept stale or weak tokens.

## 11. Optional Extensions

### 11.1 Zero-knowledge predicates

Spend Tokens can be paired with ZK proofs that show eligibility conditions over
spend (thresholds, categories, allowlists) without revealing receipt details.
A scope-specific nullifier supports anti-replay without revealing identity.

### 11.2 Deterministic bucketing for controlled rollouts

The protocol supports deterministic assignment of eligible wallets into
control/treatment buckets via issuer-signed artifacts or via ZK-contained
bucketing to avoid stable identifiers.

### 11.3 On-chain commitment layer

Reward issuance can be committed to a blockchain via Merkle roots:
- Off-chain reward ledger records per-spend issuance events.
- On-chain commitments record per-recipient-per-batch aggregates.

This enables inclusion proofs and non-repudiation.

## 12. Application Patterns (informative)

- Brand promotions without surveillance: users present Spend Attestation Tokens
  and optional ZK proofs to prove eligibility without revealing receipts.
- Measurement and negotiation: partners consume signed Verified GMV snapshots for
  a window, enabling auditing without private dashboards.
- Market/category planning: consumers verify aggregate distribution snapshots
  without access to raw receipts or identity-linked history.
- Agent-compatible verification: agents verify tokens locally rather than relying
  on untrusted claims.
- Auditable reward programs: Reward Commitment Tokens plus on-chain commitments
  support third-party audit of issuance integrity.

## 13. Implementation Checklist (informative)

- Reference verifier libraries implementing RFC 8785 + SHA-256 + Ed25519.
- Test vectors for `tokenHash` and signature verification.
- Public trust root distribution for offline verification.
- Clear acceptance policy examples (HARD-only for payouts; SOFT allowed for
  previews).
- Minimal token bundles with any required proof material for portability.
- A privacy checklist ensuring portable tokens never leak raw receipt/OCR data.

## 14. Conclusion

Spend Tokens define a minimal, portable, correction-aware representation of
verified commerce:
- Spend Attestation: "Is this spend true under protocol semantics?"
- Reward Commitment: "Was value issued (and committed)?"
- Verified GMV: "How much verified activity occurred, as-of time T, without
  surveillance?"
- Verified Spend Distribution: "Where did verified activity occur by category
  or market bucket, without surveillance?"

By separating truth from economics and making tokens portable, Spend Tokens turn
real-world commerce into machine-verifiable facts that downstream systems and
agents can validate without trusted APIs or identity graphs.

## Appendix A: Minimal Pseudocode

```text
verify_token(token):
  unsigned = remove_fields(token, ["signatures"])
  bytes = RFC8785_canonical_json(unsigned)
  digest = SHA256(bytes)  # tokenHash
  pubkey = lookup_authorized_pubkey(token.signatures.issuedBy, token.protocol.protocolVersion, token.scope)
  if !ed25519_verify(pubkey, digest, token.signatures.signature):
    return INVALID_SIGNATURE
  return apply_acceptance_policy(token)
```
