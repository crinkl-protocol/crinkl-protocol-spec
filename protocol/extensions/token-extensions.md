---
status: experimental
layer: extension
version: v1
normative: true
---

# Token Extensions (Privacy-First, Additive)

> **Status: v1 (optional extension)**
>
> This document captures additive extensions without changing core protocol invariants (determinism, append-only ledgers, replayability).
>
> Core token definitions and verification procedures live in **../portability/spend-attestation-token.md**.

## 1) Baseline (What Exists in the Core Spec)

The protocol already produces four verifiable token outputs:

1. **Spend Attestation Token** — a privacy-safe, portable claim about canonical Spend attestation (HARD_VERIFIED / CORRECTED / INVALIDATED), derived from the spend-stream.
2. **Reward Commitment Token** — system-stream commitment events + recipient inclusion proofs under committed batch roots.
3. **Verified GMV Token** — Crinkl formalizes GMV as a privacy-safe daily “as-of” commitment to aggregate spend totals (and optionally issued/rewarded totals) without exposing receipts.
4. **Verified Spend Distribution Token** — privacy-safe dimensional breakdowns of verified spend by category and region.

Spend Attestation Tokens MAY additionally include ZK commitments and be accompanied by ZK statement proofs as optional proof material (see zk-proof-extension.md and ../portability/spend-attestation-token.md).

These are derived from protocol primitives; they do not introduce new roots (no "user object", no identity graph). These outputs MUST NOT introduce new protocol trust roots, identity graphs, or mutable user-scoped state.

**Extension token boundary (normative):** any additional token types introduced by extensions MUST be explicitly labeled non-core and MUST NOT be required to verify the core token set defined in `../portability/spend-attestation-token.md` (`SPEND_ATTESTATION`, `REWARD_COMMITMENT`, `VERIFIED_GMV`, `VERIFIED_SPEND_DISTRIBUTION`).

## 2) Spend ↔ Reward Linkage (Optional, Additive)

Reward commitments are recipient-scoped and batch-scoped. To support compact proofs that a specific `spendId`'s reward issuance is included in a committed batch, the Commitment Layer MAY use a linkable leaf schema (`schemaVersion` 2a or 2b).

At a high level:

- The batch commitment still has **one leaf per recipient** (aggregation preserved).
- Each recipient leaf additionally commits a `rewardEventsRoot`, which is a Merkle root over per-spend reward issuance references for that recipient+batch.
- A verifier can link a spend to a committed reward with two proofs:
  1) reward issuance leaf ∈ `rewardEventsRoot`
  2) recipient aggregated leaf ∈ batch root (on-chain)

**Uniqueness invariant:** Within a given recipient+batch, each `spendId` MUST appear at most once in `rewardEventsRoot`.

See ../applications/economics/settlement-bindings.md for the normative structures and verification rules.

## 3) Privacy Constraints (Non-Negotiable)

Extensions MUST preserve:

- Recipient-scoped objects and streams (no protocol-level identity graph).
- Append-only semantics (corrections append; no rewrites).
- Deterministic bytes/hashes/signatures for any committed or signed artifact.

If/when privacy-preserving proofs are added (e.g., ZK statements over spend history), they should be designed so that a verifier can validate the statement without requiring raw ledger export. Such proofs MUST NOT enable reconstruction of recipient-level aggregates, cross-recipient correlations, or spend ordering beyond what is already revealed by committed roots.

Where possible, implementations SHOULD attach ZK statement proofs as optional proof material that references existing tokens (e.g., a Spend Attestation Token hash) rather than minting new token categories that reinterpret protocol truth.

## Privacy Footguns (Normative Guardrails)

Extensions are the easiest way to accidentally violate privacy invariants. Implementations MUST treat the following as prohibited or constrained:

- **Portable tokens MUST NOT carry stable identifiers** beyond what is explicitly required for the token’s claim (avoid device ids, account ids, phone/email, stable user handles, stable internal database ids).
- **Audit-only artifacts MUST NOT leak into portability**: portable token verification MUST NOT depend on audit-only fields, and audit-only fields MUST NOT be copied into portable tokens “for convenience”.
- **Recipient identifiers in public commitments MUST be schema-scoped**:
  - If using transparent recipient schemas, `WalletRef` is publicly linkable by design.
  - If using blinded recipient schemas, the commitment MUST be per-batch/per-epoch scoped so it does not create a stable on-chain identity graph.
- **Rate limiting MUST NOT create protocol-visible identity**: rate-limit keys and reputation systems are operational and MUST NOT become public identifiers or be embedded into tokens/proofs.
- **Redemption anti-replay MUST be scope-scoped**: `nullifier` MUST be scoped by `scopeId` to prevent cross-campaign linkability.

## 4) Per-Spend Verified GMV Proofs (Optional, Additive)

Verified GMV Tokens commit to the set of spends counted via `asOf.spendHeadSetRoot` (see ../portability/spend-attestation-token.md). As an additive capability, issuers MAY return a **per-spend inclusion proof** to a user who knows a `spendId`, so the user can verify that their hard-verified (or corrected) spend was counted in a specific day’s Verified GMV snapshot without the issuer publishing the full spend list.

**Verification tier bound:** Only spends that have reached a terminal verification state (HARD_VERIFIED or CORRECTED) at the snapshot boundary MAY be provable as included.

This is intended to be:

- **private-by-default:** the proof can be given only to the user (no global spend list),
- **portable:** the user can verify it locally against the public GMV token, and
- **receipt-safe:** it does not require providing receipt images or OCR text.

**Non-transferability:** Per-spend inclusion proofs demonstrate inclusion of a spend in an aggregate snapshot; they do not assert spend ownership, reward entitlement, or user identity.

See ../portability/spend-attestation-token.md for the proof shape and verification procedure.

## 5) Verified Spend Distribution Token (Additive)

The Verified Spend Distribution Token extends the GMV primitive with **dimensional breakdowns**: the same aggregate spend data sliced by store category and geographic region. It shares the same `spendHeadSetRoot`, spend filtering, and as-of semantics as the Verified GMV Token for the same window.

**Key properties:**

- **Derived from same snapshot** — identical `spendHeadSetRoot` and spend filtering as GMV token; implementations SHOULD compute both tokens from a single snapshot pass.
- **Same cryptographic model** — Ed25519 signed, authority-authenticated, temporally chained via `prevDistributionTokenHash`.
- **Identity-free** — only aggregated counts and totals per dimension; no wallet identifiers, no per-user data.
- **Dual accounting** — `verifiedDistribution` (all verified spends) vs `issuedDistribution` (rewarded spends only), mirroring GMV's verified/issued split.

**Geographic dimension — CBSA metro areas:**

`byGeoRegion` keys use canonical region bucket values derived from the canonical spend head (see `../core/canonicalization.md#regioncode` and `../core/canonicalization.md#cbsacode`). Implementations MAY use US OMB Core Based Statistical Area codes, non-metro fallbacks, ISO 3166-2 subdivisions, or ISO 3166-1 alpha-2 country codes when those are the verifier's canonical buckets. Unresolvable locations use `"Unknown"`.

CBSA codes are derived from store physical location via the store registry and public OMB crosswalk (city/county → CBSA), not from receipt text. Implementations SHOULD define a privacy floor (minimum spend count per CBSA bucket) below which small-population areas are rolled up into a coarser grouping.

**Category dimension:**

`byCategory` keys are canonical store category identifiers from the store registry (see `store-registry.md`). Unresolvable stores are bucketed under `"Unknown"`.

See `../portability/spend-attestation-token.md#verified-spend-distribution-token` for the normative portable shape and verification procedure.

## 6) Future Extensions (Placeholder)

Future additions SHOULD prefer:

- optional proof material attached to existing token bundles (Spend Attestation / Reward Commitment), and/or
- new commitment types and leaf schemas within the Commitment Layer when external anchoring is required.

Future extensions SHOULD NOT introduce new token categories that duplicate or reinterpret protocol truth, reward eligibility, or verification semantics. Campaign rule composition SHOULD use Campaign Spend Proof Primitives (`../applications/conditions/campaign-commitment.md`) over existing token and proof surfaces.

## 7) Store Registry Snapshots (Optional, Additive)

Interoperable “store” and “store location” identification requires a shared taxonomy. The core protocol intentionally keeps Spend Attestation Tokens portable and privacy-safe by including only:

- `canonical.storeHash` (deterministic hash over a canonical `storeId`)
- optionally coarse location (`geoRegion`) and metro area (`cbsaCode`) when available

To let verifiers compute `storeHash` deterministically for a known merchant (e.g., “Example Merchant”) without trusting a private API, issuers MAY publish a **signed, Merkle-rooted store registry snapshot** as a **non-core extension token**.

This snapshot is:
- publicly replicable (portable verification requires only the snapshot token + public rules),
- additive (not required to verify core tokens), and
- suitable as an input to campaign allowlists and ZK set-membership predicates.

See `store-registry.md` for the normative snapshot/leaf/proof shapes and hashing rules.

---

All token outputs are derived views over canonical event history; they do not constitute independent sources of truth.
