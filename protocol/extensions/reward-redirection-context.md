---
status: draft
layer: extension
version: v1
normative: false
---

# Reward Redirection Context

**Problem:** Receipt data is unstructured, non-standard, and hard to attest at scale.

**Solution:** A two-tier verification pipeline producing cryptographically-signed, append-only event streams.

## Why Two Tiers?

| Tier | Latency | Finality | Use Case |
|------|---------|----------|----------|
| **Soft** | Low (seconds) | Provisional (ML/OCR) | Instant feedback; provisional rewards |
| **Hard** | Higher (minutes–hours) | Canonical (audited) | Authoritative spend record; final rewards |

Soft verification enables responsive UX. Hard verification produces the canonical truth. Both emit signed events; neither mutates the other.

## Example Flow

A user photographs a grocery receipt:

1. **Ingest** — `RECEIPT_UPLOADED` binds submission to wallet inside the issuer-managed spend stream
2. **Soft Verify** — `SPEND_SOFT_VERIFIED` emits approximate extraction; operators may issue provisional rewards
3. **Hard Verify** — `SPEND_HARD_VERIFIED` produces canonical Spend (store, total, currency, timestamp); operators may issue final rewards
4. **Commit** (optional) — reward batch anchored on-chain via Merkle root
5. **Tokenize** — portable Spend Attestation Token + Reward Commitment Token (if committed)

Corrections append (`SPEND_CORRECTED`); they never mutate.

The wallet binding in step 1 is internal stream scope for replay, routing, abuse controls, and reward handling. The portable Spend Attestation Token produced at tokenization is a separate derived artifact and is identity-free by default; it can prove that the spend happened without exposing wallet, user, account, or session identity.

## Reward Gating

Rewards are gated by verification tier:

- **Provisional rewards** may issue after Soft Verification
- **Final rewards** may issue after Hard Verification

The Reward Ledger is append-only; the protocol does not define clawback events. Reward amounts, formulas, and payout rules are application-layer (see ../applications/economics/reward-layer.md).

## Outputs

The protocol emits portable, privacy-preserving tokens for downstream composition:

- **Spend Attestation Token** — canonical spend claim; wallet optional (../portability/spend-attestation-token.md)
- **Reward Commitment Token** — inclusion proof under committed batch; `recipientId` required, representation schema-defined (../portability/spend-attestation-token.md, ../applications/economics/settlement-bindings.md)
- **Verified GMV Token** — aggregate spend commitment; wallet prohibited (../portability/spend-attestation-token.md)
- **Verified Spend Distribution Token** — aggregate category and region distribution; wallet prohibited (../portability/spend-attestation-token.md)

## Business Context (non-normative)

The protocol supports a **reward redirection model**:

1. Users upload receipts and earn rewards
2. Crinkl aggregates verified commerce into GMV attestations
3. Brands verify audience reach via cryptographically signed GMV tokens
4. Brands redirect existing marketing budget to fund user rewards
5. Crinkl coordinates the flow

Tokens in this protocol are portable verification artifacts—machine-verifiable claims about spend state, reward inclusion, or aggregate throughput. They enable downstream systems to consume Crinkl outputs without replaying event streams or trusting API responses.

In probabilistic domains such as OCR, Crinkl separates epistemic truth from economic action; see the Economic Reinforcement Invariant in what-crinkl-proves.md.

---

For invariants and protocol-level properties, see what-crinkl-proves.md. For terms, see ../../governance/glossary.md.
