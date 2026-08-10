---
status: draft
layer: portability
version: v1
normative: false
---

# Crinkl Protocol Tokens

Machine-verifiable economic claims, designed for composition.

## Overview

The Crinkl Protocol defines a small set of primitive, verifiable tokens that transform messy real-world commerce evidence into machine-legible issuer claims.

These native tokens are issuer-signed portable verification artifacts
representing OCR-derived purchase claims, extended with correction semantics and
optional ZK predicates to support privacy-preserving promotion and reward
settlement. They are not assets, identities, application objects, or W3C
Verifiable Credentials in v1.0.0-rc.4. They are cryptographically signed claims
that downstream systems can verify locally, without replaying event streams or
trusting APIs.

| Conceptual credential role | Crinkl realization |
|----------------------------|--------------------|
| **Issuer** | Protocol operator signing spend attestations |
| **Holder** | Wallet owner who may present tokens or generate ZK proofs |
| **Verifier** | Brands, agents, or systems validating claims locally |
| **Selective Disclosure** | ZK predicates prove eligibility without revealing receipt details |

Crinkl tokens are intentionally minimal. Each token asserts one thing only, with explicit verification rules. More complex behavior is achieved by composition, not by expanding token semantics.

Core belief:
- Durable systems start with narrow, truthful primitives that machines can verify and combine.

## Design Principles

### 1) Machine-legible first

All Crinkl tokens are designed to be consumed by software agents:
- Deterministic bytes (RFC 8785 canonical JSON)
- Deterministic hashes (SHA-256)
- Explicit verification procedures
- No reliance on human interpretation or API trust

A verifier can answer “Is this claim valid?” using only the token, public keys, and (when applicable) Merkle proofs.

### 2) Scarcity through process, not syntax

Crinkl tokens are scarce because they are expensive to produce correctly:
- They require submitted commerce evidence and protocol verification work
- They require verification under protocol rules
- They require issuer accountability
- Some require irreversible economic commitment

Scarcity emerges from process, not from token type proliferation.

### 3) Separation of truth and economics

Crinkl distinguishes between:
- Epistemic commitment — asserting what is true
- Economic commitment — acting on that assertion

These commitments reinforce each other but are recorded separately, preserving determinism and auditability.

### 4) Minimal identity exposure

Crinkl tokens do not introduce a protocol-level identity graph:
- Recipient binding is included only when required to verify economic issuance.
- Aggregate and truth tokens do not expose wallets or users.
- Identity and payout routing are application-layer concerns.

The issuer's internal spend stream may still carry `wallet: WalletRef` for replay, routing, abuse controls, and reward handling. That internal scope is not the portable token. Portable Spend Attestation Tokens are identity-free by default and omit wallet unless recipient binding is explicitly required.

## The Four Core Token Types

The protocol defines four token outputs. Together, they form the minimum viable set needed to represent economic reality, economic action, economic scale, and economic distribution.

### 1) Spend Attestation Token

Canonical issuer attestation under uncertainty.

**What it asserts**
- “The issuer derived this specific spend claim and verification state under the named Crinkl Protocol rules.”
- Canonical spend fields (as defined by the state machine)
- Verification tier (e.g., `HARD_VERIFIED`)
- Lineage (attestation head hash)
- Issuer signature

**What it does not assert**
- Independent proof that the underlying physical purchase occurred
- Ownership
- Reward entitlement
- Aggregate behavior

**Why it matters**
- Portable
- Replayable
- Correction-aware
- Independent of application logic

Downstream systems can rely on it without knowing how verification was performed.

### 2) Reward Commitment Token

Economic consequence, made verifiable.

**What it asserts**
- “A reward issuance occurred and was committed under a specific batch, optionally with economic backing.”
- Inclusion under a committed batch root
- Recipient-scoped aggregation
- Batch metadata
- Optional backing attestation

**What it does not assert**
- Current balance
- Spend validity at present time
- Clawback or reversal semantics

**Why it matters**

Economic action strengthens truth.

Issuing rewards is not merely an application feature — it is skin in the game. By committing reward issuance cryptographically (and optionally economically), the issuer accepts the cost of being wrong.

This makes reward attestations credible to:
- Users
- Auditors
- Agents
- Counterparties

### 3) Verified GMV Token

Aggregate economic throughput, without surveillance.

**What it asserts**
- “As of a specific computation time, total verified spend for a fixed window equals X.”
- Total volume
- Spend count
- Commitment to which spends were counted

**What it does not assert**
- User identities
- Individual receipts
- Reward balances

**Why it matters**

Verified GMV Tokens provide:
- Append-only aggregate snapshots
- Explicit “as-of” semantics
- Correction via supersession, not mutation
- Privacy-preserving commitments to the underlying spend set

Verified GMV Tokens allow third parties to verify throughput claims without database access, receipt exposure, or blind trust.

They are designed to support:
- Auditing
- Negotiation
- Agent-based reasoning
- Historical comparison

### 4) Verified Spend Distribution Token

Dimensional distribution of verified spend, without surveillance.

**What it asserts**
- “As of a specific computation time, verified spend is distributed across categories and regions as shown.”
- Aggregate totals by category
- Aggregate totals by region (CBSA / fallback region buckets)
- Alignment to the same spend snapshot model as Verified GMV

**What it does not assert**
- User identities
- Individual receipt details
- Recipient ownership or payout balances

**Why it matters**

Verified Spend Distribution Tokens provide:
- Auditable dimensional breakdowns for category/region strategy
- Privacy-safe local-business signal without per-user exposure
- Compatibility with the same as-of/supersession model as GMV snapshots

## Why Only Four Tokens?

Crinkl deliberately avoids proliferating token types. Each token corresponds to a fundamental question:

| Question | Token |
|---|---|
| “What exact Spend claim did the issuer attest?” | Spend Attestation |
| “Was value issued?” | Reward Commitment |
| “How much activity occurred?” | Verified GMV |
| “Where is activity distributed?” | Verified Spend Distribution |

More complex claims (eligibility, attribution, segmentation, incentives) are built by composing these primitives — not by redefining them.

## Tokens as Factory Outputs

Crinkl operates as a token factory:
- Raw inputs: receipt images, human actions
- Refinement: verification, correction, aggregation
- Outputs: high-signal, verifiable tokens

These outputs can be:
- Stored
- Exchanged
- Verified
- Recombined

They are designed to feed downstream agents and systems that were not known at design time.

Composability and the Agent Future

Crinkl tokens are designed for a future where:

software agents consume proofs directly

APIs are untrusted

databases are opaque

verification happens locally

Each token has:

explicit scope

explicit meaning

explicit verification rules

Agents can reason about:

truth

economic commitment

scale

Without requiring privileged access or bespoke integrations.

What Crinkl Does Not Do

The protocol intentionally does not:

define identity wallets

define user graphs

define reward policies

define payout routing

define business logic

These are application concerns.

Crinkl’s role is narrower and more durable:

turning real-world commerce evidence into machine-verifiable economic claims.
