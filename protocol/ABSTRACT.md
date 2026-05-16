The Crinkl Protocol transforms raw receipt submissions into cryptographically signed attestations of **canonical spend state**: the authoritative, correction-aware record of a transaction as derived from an append-only event stream under a specific protocol version.

Canonical spend state is deterministic and replayable: given the same event stream and protocol version, any verifier derives the same result. Truth is advanced only by appending new events (e.g., corrections or invalidations), never by mutating history.

## Conceptual Model

Crinkl defines a spend-centric attestation system that separates truth formation from economic action, enabling verification, correction, and downstream use without requiring identity disclosure.

A **Spend Attestation Token** is a signed claim representing the current canonical head of a spend's event stream at a specific verification tier.

To aid interoperability, Crinkl spend tokens can be understood through the lens of verifiable credentials, while preserving protocol-specific semantics such as correction awareness and tiered verification.

| VC Concept | Crinkl Realization |
|------------|-------------------|
| **Credential** | Spend Attestation Token — a signed claim about canonical spend state |
| **Issuer** | Protocol operator (spend-stream trust root) |
| **Holder** | Wallet owner (optional binding; spend truth ≠ ownership) |
| **Verifier** | Any party verifying signatures and applying acceptance policy |
| **Claim** | Canonical spend fields (store, total, currency, timestamp) at a defined tier |
| **Selective Disclosure** | ZK commitments + statement proofs over canonical fields |

Unlike static credentials, Crinkl spend attestations are **correction-aware**: canonical truth evolves via append-only events (e.g., `SPEND_CORRECTED`) while preserving full audit history.

Optional zero-knowledge predicates allow parties to prove eligibility conditions over spend (e.g., thresholds, categories) without revealing receipt details.

## Invariants (Normative Properties)

The protocol enforces the following invariants:

| Property | Meaning |
|----------|---------|
| **Deterministic** | Same event stream + protocol version → identical output |
| **Append-only** | Ledger entries are never deleted or modified; corrections append |
| **Tiered verification** | Soft (provisional, low-latency) and Hard (authoritative, canonical) |
| **Attestation ≠ Rewards** | Attestation and Reward Ledgers are independent domains |

These invariants ensure that spend truth remains protocol-defined and replayable, independent of application-layer economics.

## Ledgers

The protocol defines two distinct ledgers with non-overlapping responsibilities:

**Attestation Ledger**
Per-spend event streams recording verification state transitions (Soft → Hard → Corrected / Invalidated).

**Reward Ledger**
Immutable records of issuance events gated by verification tier. Economic logic, funding sources, and incentives are application-layer concerns.

The protocol does not define reward clawback semantics; reward issuance does not mutate or upgrade spend verification state.

## Economic Reinforcement

Canonical spend state is derived from probabilistic inputs (OCR, heuristics, validation pipelines). To account for epistemic uncertainty, the protocol distinguishes two reinforcing commitments:

1. **Epistemic commitment** — the Spend Attestation, asserting canonical spend state according to protocol rules at a specific point in time.
2. **Economic commitment** — the Reward Attestation, recording that value was issued based on that spend attestation.

Issuing rewards does not redefine spend truth or verification tier. Instead, it attaches economic consequence to the attestation, increasing issuer accountability for epistemic error.

This separation ensures that:

- truth remains protocol-defined and replayable, and
- economic action bears the cost of misclassification.

## Identity Minimization

The protocol minimizes identity exposure by default.

Canonical spend truth and aggregate economic claims MUST NOT require or imply user identity disclosure. Recipient identifiers are exposed only when required to verify economic issuance.

Internal spend-stream envelopes MAY include `wallet: WalletRef` for issuer-side replay, routing, abuse controls, or reward handling. That field is internal stream scope, not a public identity claim and not a requirement for portable proof. Portable Spend Attestation Tokens are distinct derived artifacts and SHOULD omit wallet for external verification unless recipient binding is explicitly required.

| Token Type | Recipient Exposure |
|------------|-------------------|
| Spend Attestation | Optional — truth ≠ ownership |
| Reward Commitment | Required — scoped to `recipientId` (schema-defined) |
| Verified GMV | Prohibited — aggregate, privacy-preserving claim |
| Verified Spend Distribution | Prohibited — aggregate, privacy-preserving claim |

The Commitment Layer proves that rewards were issued under a verifiable recipient scope; it does not define who a user is or how value is routed.

## Derived Protocol Primitives

In addition to per-spend attestations, the protocol defines system-scoped primitives that summarize or economically anchor spend without reasserting individual receipt claims:

**Commitment Layer** (optional)
Anchors reward batches on-chain via Merkle roots, providing non-repudiation and verifiable inclusion.

**Verified GMV Token**
Privacy-preserving, append-only "as-of" snapshots of aggregate GMV. Corrections emit new tokens for the same window rather than mutating history.

**Verified Spend Distribution Token**
Privacy-preserving, append-only "as-of" snapshots of aggregate spend distribution by category and geographic bucket. It shares the same snapshot model as Verified GMV without exposing receipt details, wallet identifiers, or per-user spend patterns.

## Deployment Posture

The protocol is designed for centralized operator deployment while preserving cryptographic invariants—signed events, hash-chained streams, and optional Merkle commitments—required for future decentralized verification.

This ensures that downstream systems remain compatible across deployment models without redefining truth semantics.

---

Terms are defined in GLOSSARY.md and used normatively throughout this specification.
