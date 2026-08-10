---
status: draft
layer: core
version: v1
normative: true
---

# Spend Attestation Model

The protocol is **spend-centric**: canonical truth is keyed by spend-stream events, while wallet or recipient exposure appears only where a specific artifact requires ownership, routing, or downstream reward inclusion semantics.

Terms are defined in ../08-governance/glossary.md and used normatively throughout this specification.

## Core Objects

```
ReceiptUpload ──→ SoftSpend ──→ Spend
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
               HARD_VERIFIED  INVALIDATED  CORRECTED

Legend: ──→ verification transition  │ terminal states
```

| Object | Purpose | Canonical? |
|--------|---------|------------|
| ReceiptUpload | Raw submission (image ref + metadata) | No |
| SoftSpend | Preliminary extraction (approximate values) | No |
| Spend | Normalized, attested economic record | **Yes (stateful)** |

*Canonical = authoritative protocol output, not economic validity; Spend validity is expressed by state (HARD_VERIFIED / CORRECTED / INVALIDATED).*

## Ledgers

| Ledger | Content | Mutability |
|--------|---------|------------|
| Attestation Ledger | Verification state transitions | Append-only (corrections via new events) |

Reward and settlement ledgers are downstream of Core. They may consume attestations, but they do not define spend truth.

## Verification Tiers

| Tier | Latency | Output | Canonical? |
|------|---------|--------|------------|
| Soft Verification | Low | SoftSpend | No |
| Hard Verification | Higher | Spend | **Yes** |

## Key Invariants

1. **Identity-minimized:** Spend truth does not require wallet or user identity; recipient/wallet scope appears only in reward, ownership, or application-routing artifacts that explicitly require it.
2. **Deterministic (versioned):** Same input + protocolVersion + verificationVersion = same output
3. **Append-only:** Ledgers grow; entries are never deleted
4. **Replayable:** Final state reconstructible from events alone
5. **Rewards downstream:** Core does not define reward formulas, campaign budgets, settlement assets, or reward clawbacks
6. **Sealed hard rejections:** `REJECTED`/`INVALIDATED` are terminal. The spec does not define an appeal/re-review transition after hard rejection; adding one would require a new state + spend-stream event without violating append-only ordering.

## Wallet and recipient scope (plain English)

Problem:
Some app flows use user account ids (like Privy DIDs or tenant ids) as routing handles. Spend-stream envelopes also carry `wallet: WalletRef` in protocol v1. These handles can be necessary inside an issuer's system, but they are not the portable proof that a spend happened.

Solution:
Keep two scopes separate:

- **Internal event stream scope:** `SpendStreamEvent.wallet` is required in v1 so issuers can replay, route, dedupe, investigate abuse, and handle rewards within a bounded system.
- **Portable proof scope:** a Spend Attestation Token is a derived token. It SHOULD omit `wallet` for third-party verification unless recipient binding is explicitly required by the verifier policy.

When a protocol artifact requires wallet or recipient scope, use the appropriate protocol field (`WalletRef` or `RecipientRef`) and keep login/session identifiers out of protocol-visible artifacts. Internal issuer-managed wallet routing MAY exist in platform systems, but it MUST NOT be copied into portable Spend Attestation Tokens by default.

## Determinism (LLM clarification)

Determinism is satisfied when LLM normalization is constrained to a closed choice set and the prompt/model/choice set are versioned. The recorded `verificationVersion` must uniquely identify the prompt, model, and choice set used for canonical fields.

## Downstream Outputs

Beyond internal event streams, the protocol can produce portable or downstream artifacts that systems verify without requiring raw receipt access or user identity:

- **Spend Attestation Token:** portable, identity-excluded claim about canonical Spend attestation for a `spendId` (see `../protocol/portability/spend-attestation-token.md`)
- **Reward Commitment Token:** downstream Merkle inclusion proof for committed rewards (see `../protocol/applications/economics/reward-commitment.md`)
- **Verified GMV Token:** downstream aggregate spend snapshot (see `../protocol/applications/economics/gmv-token.md`)
- **Verified Spend Distribution Token:** downstream dimensional aggregate snapshot (see `../protocol/applications/economics/distribution-token.md`)

### Optional: Spend ↔ Reward Linkage

When the Commitment Layer uses linkable leaf schemas (`schemaVersion` 2a or 2b), verifiers can prove that a specific `spendId`'s reward issuance is included in a committed batch without fetching every reward event. This produces compact, per-spend reward proofs for audit/compliance use cases.
