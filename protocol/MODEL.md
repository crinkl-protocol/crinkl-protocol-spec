# Protocol Model

The protocol is **wallet-anchored**—all state binds to wallet addresses, not user accounts—enabling operator independence and future decentralization.

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

1. **Wallet-anchored:** Every object binds to exactly one wallet
2. **Deterministic (versioned):** Same input + protocolVersion + verificationVersion = same output
3. **Append-only:** Ledgers grow; entries are never deleted
4. **Replayable:** Final state reconstructible from events alone
5. **No Clawback (Protocol):** The protocol does not define reward revocation events; issued rewards are immutable protocol outputs
6. **Sealed hard rejections:** `REJECTED`/`INVALIDATED` are terminal. The spec does not define an appeal/re-review transition after hard rejection; adding one would require a new state + spend-stream event without violating append-only ordering.

## Wallet-anchored identity (plain English)

Problem:
Some app flows are putting a user account id (like a Privy DID or tenant id) into the `wallet` field. That field is supposed to be a real wallet address. When it is not a wallet address, the tokens are not portable and outside agents cannot verify or use them.

Solution:
Always put a real wallet address in the `wallet` field. If the user does not provide one, the platform should provision a custodial wallet address and use that. Keep Privy DIDs and tenant ids only for login/session ownership, never in protocol wallet fields. Capture `walletRef` at session creation and propagate it into spend-stream events and tokens.

## Determinism (LLM clarification)

Determinism is satisfied when LLM normalization is constrained to a closed choice set and the prompt/model/choice set are versioned. The recorded `verificationVersion` must uniquely identify the prompt, model, and choice set used for canonical fields.

## Token Outputs

Beyond internal event streams, the protocol produces **portable tokens**—signed, privacy-safe claim bundles that downstream systems can verify without replaying events or trusting APIs (see TOKENS.md):

- **Spend Attestation Token:** portable claim about canonical Spend attestation for a `spendId` (excludes receipt images/OCR)
- **Reward Commitment Token:** Merkle inclusion proof for a recipient's committed rewards under a specific on-chain batch root, optionally with audit attachments
- **Observed GMV Token:** append-only, "as-of" daily commitment to Observed GMV (sum of verified spend) and optionally Issued/Rewarded GMV, without exposing individual receipts

### Optional: Spend ↔ Reward Linkage

When the Commitment Layer uses linkable leaf schemas (`schemaVersion` 2a or 2b), verifiers can prove that a specific `spendId`'s reward issuance is included in a committed batch without fetching every reward event. This produces compact, per-spend reward proofs for audit/compliance use cases.
