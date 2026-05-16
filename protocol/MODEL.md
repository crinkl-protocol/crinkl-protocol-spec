# Protocol Model

The protocol is **spend-centric**: canonical truth is keyed by spend-stream and system-stream events, while wallet or recipient exposure appears only where a specific artifact requires ownership, routing, or reward inclusion semantics.

Terms are defined in GLOSSARY.md and used normatively throughout this specification.

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
| Reward Ledger | Issuance events (points, sats) | Immutable (no clawback)* |

*Attestation corrections don't revoke rewards; fraud detection is application-layer*

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
5. **No Clawback (Protocol):** The protocol does not define reward revocation events; issued rewards are immutable protocol outputs
6. **Sealed hard rejections:** `REJECTED`/`INVALIDATED` are terminal. The spec does not define an appeal/re-review transition after hard rejection; adding one would require a new state + spend-stream event without violating append-only ordering.

## Wallet and recipient scope (plain English)

Problem:
Some app flows use user account ids (like Privy DIDs or tenant ids) as routing handles. Those handles are application-layer identifiers and MUST NOT be embedded into portable Spend Attestation Tokens.

Solution:
When a protocol artifact requires wallet or recipient scope, use the appropriate protocol field (`WalletRef` or `RecipientRef`) and keep login/session identifiers out of protocol-visible artifacts. Internal issuer-managed wallet routing MAY exist in platform systems, but portable Spend Attestation Tokens remain identity-free unless a future schema explicitly defines optional ownership binding.

## Determinism (LLM clarification)

Determinism is satisfied when LLM normalization is constrained to a closed choice set and the prompt/model/choice set are versioned. The recorded `verificationVersion` must uniquely identify the prompt, model, and choice set used for canonical fields.

## Token Outputs

Beyond internal event streams, the protocol produces **portable tokens**—signed, privacy-safe claim bundles that downstream systems can verify without replaying events or trusting APIs (see TOKENS.md):

- **Spend Attestation Token:** portable, identity-free claim about canonical Spend attestation for a `spendId` (excludes receipt images/OCR)
- **Reward Commitment Token:** Merkle inclusion proof for a recipient's committed rewards under a specific on-chain batch root, optionally with audit attachments
- **Verified GMV Token:** append-only, "as-of" daily commitment to Verified GMV (sum of verified spend) and optionally Issued/Rewarded GMV, without exposing individual receipts
- **Verified Spend Distribution Token:** append-only, "as-of" dimensional breakdown of verified spend by category and geographic bucket, without exposing individual receipts or identities

### Optional: Spend ↔ Reward Linkage

When the Commitment Layer uses linkable leaf schemas (`schemaVersion` 2a or 2b), verifiers can prove that a specific `spendId`'s reward issuance is included in a committed batch without fetching every reward event. This produces compact, per-spend reward proofs for audit/compliance use cases.
