# Zero-Knowledge Extension Layer

> **Status: v1 (optional extension) — closed statement set for interoperability**
>
> This section defines the interface for ZK extensions. Concrete statement types and the circuits that implement them are captured in `ZK_CIRCUIT_CATALOG.md`.

## Purpose

Enable privacy-preserving proofs of spend properties (and, as verified schemas expand, spend-adjacent properties) without revealing underlying receipt data. ZK extensions are optional and additive — they do not alter core verification or ledger semantics.

ZK statements attest only to the truth of the stated rule under protocol semantics and MUST NOT be interpreted as preventing all indirect inference about spend attributes.

ZK statements do not strengthen or supersede the verification tier of the underlying Spend; they only enable selective disclosure about already-verified fields.

For the minimum viable promo use case and the associated “wallet witness” foundation concepts, see `ZK_FOUNDATION.md`.

## Commitments

Implementations MAY attach cryptographic commitments to Spend records (and to other deterministically-derived, hard-verified fields as the canonical schema evolves):

```text
ZKCommitments {
    C_store: Commitment,      // Commitment to canonical.storeHash
    C_total: Commitment,      // Commitment to totalCents
    C_dayIndex: Commitment,   // Commitment to dayIndex (days since epoch)
    C_geoRegion: Commitment,  // Commitment to geoRegion (ISO 3166-2 subdivision)
    C_cbsaCode?: Commitment   // OPTIONAL commitment to cbsaCode (CBSA metro area)
}
```

**Commitment scheme:** To be specified. Candidates include Pedersen commitments (for range proofs) and Poseidon hash (for SNARK compatibility). For Halo2 IPA circuits in `ZK_CIRCUIT_CATALOG.md`, commitments are Poseidon-based and bind `(spendIdHash, headEventHash, label, value, blinding)`; see the circuit entry for the exact encoding rules.

### Binding and derivation (normative)

ZK commitments are carried inside a signed `SpendAttestationTokenV1` (see `TOKENS.md`). Verifiers treat commitments as **opaque values** unless accompanied by a proof; the primary security requirement is that any proof claiming something about a commitment is replay-safe and unambiguous about what the commitment commits to.

All ZK commitments MUST:

1. Commit to canonical (hard-verified/corrected) Spend fields at a specific attestation head, and
2. Be cryptographically bound to the corresponding `spendId` and attestation head `headEventHash` (e.g., by domain-separated binding inside the commitment statement / circuit / preimage).

This binding prevents commitments and proofs from being replayed across spends or across different attestation heads for the same spend.

**Label binding (normative):** each commitment MUST be bound to its intended semantic label (e.g., `"C_total"`) so that a proof about one commitment cannot be substituted for a proof about a different commitment field.

### Commitment scheme requirements (normative)

Regardless of scheme choice, commitments MUST be:

- **Binding** (a prover cannot open the same commitment to two different values), and
- **Hiding against feasible enumeration** of the committed field domains (schemes MUST incorporate adequate blinding/salting where domains are small, and that blinding MUST NOT be derivable from public protocol data).

**Determinism note (normative):** the protocol does not require commitments to be publicly recomputable or deterministic across issuers. If a commitment scheme uses blinding/randomness, the required opening material MUST be delivered only via wallet-only witness material (see `TOKENS.md#optional-wallet-witness-non-portable-normative`). If a scheme uses deterministic blinding, the determinism MUST be keyed by secret witness material (e.g., wallet secret) such that third parties cannot enumerate small domains.

## ZK Statements

A **ZK statement** is a machine-readable rule that can be proven true about a Spend using commitments, without revealing the underlying spend fields or receipt data.

Examples (non-normative):
- `storeHash ∈ {merchant_set}`
- `totalCents ≥ threshold`
- `timestamp ∈ [start, end]`
- `geoRegion ∈ {region_set}`

### Statement definition and identifier

To enable composability across systems, statements SHOULD be referenced by a stable identifier.

**Statement identifier (recommended):**
- `statementId = sha256(RFC8785_canonicalize(statementDefinition))`

`statementDefinition` is a JSON object whose internal format is intentionally not fixed in this draft; it MUST be canonicalizable and MUST be immutable once referenced by `statementId`.

**Statement minimum fields (normative):** every statement object MUST include:
- `domain` (string): MUST be `"crinkl:statement:v1"` for v1 statements
- `schemaVersion` (integer): statement schema version, starting at `1`
- `type` (string): statement type identifier
- `protocolVersion` (string): the protocol version whose field semantics this statement assumes

Verifiers MUST reject statements with unknown `domain` or unsupported `schemaVersion`.

**Circuit catalog (normative intent):** statement `type` values are only interoperable if verifiers agree on which proof circuits implement them. The mapping from statement types to supported `(proofSystem, circuitId, verifyingKeyId)` MUST be captured in `ZK_CIRCUIT_CATALOG.md`.

Statement definitions SHOULD reference large sets (e.g., SKU/merchant/category lists) by commitment (e.g., Merkle root) rather than embedding raw lists, to keep statements small and portable.

### Scope Binding (Normative)

ZK statements MAY be bound to a verification scope to enable context-specific proofs and prevent unauthorized reuse:

```typescript
interface ScopeParameters {
  schemaVersion: 1;
  scopeType: "REDEMPTION_SCOPE" | "AUDIT_SCOPE" | "AGGREGATION_SCOPE";
  verifierId?: string;      // identifier of the verifying party
  campaignId?: string;      // specific offer, promotion, or campaign identifier
  context?: string;         // additional context string
  validUntil?: string;      // ISO 8601 timestamp for time-bound scopes
}

scopeId = "sha256:" + SHA-256(RFC8785(scope))
```

**Scope binding purpose:**
1. **Anti-replay:** Proof is valid only for the specified verifier/campaign/context
2. **Audit trails:** Track which proofs were presented where (without exposing user identity)
3. **Fraud detection:** Same `spendId` qualifying for multiple incompatible scopes may indicate fraudulent behavior
4. **Context isolation:** Prevent proof intended for one verifier from being replayed to another

**Scope incorporation (normative):**

When a ZK statement includes scope binding:
- The `scopeId` MUST be incorporated into the statement identifier calculation (so statements with different scopes are cryptographically distinct)
- Commitment domain separation SHOULD include `scopeId` (implementation-specific; see circuit catalog)
- Public inputs to the proof circuit MAY include `scopeId` or its hash to enforce binding at verification time

**Privacy note on scope binding:**

Scope binding does NOT prevent correlation of the same `spendId` across different scopes. It only ensures that:
- Proofs are cryptographically bound to their intended verification context
- Proofs cannot be copied and replayed in unintended contexts
- Audit trails can track proof usage without exposing user wallet addresses

If multiple proofs reference the same `spendId` across different scopes, verifiers who collude can still correlate those proofs as originating from the same anonymous spend. This correlation reveals behavioral patterns (e.g., "this spend qualified for both coffee and breakfast promotions") but does NOT reveal user identity when `wallet` is omitted from the underlying Spend Attestation Token.

### Statement constraints (normative)

Statement definitions MUST be pure predicates over committed Spend fields and referenced constants (e.g., set roots). They MUST NOT depend on:

- ledger state (beyond the committed fields being proven),
- reward state,
- time-of-verification,
- verifier identity (except via explicit scope binding), or
- external oracles.

## Proof System

**Candidates under evaluation:**
- Groth16 (small proofs, trusted setup)
- PLONK / Halo2 (universal setup; **Halo2 IPA is used in the v1 demo circuit**)
- STARKs (no trusted setup, larger proofs)

**Circuit specifications:** To be defined.

Proof artifacts MUST reference unambiguous, versioned circuit identifiers and verification keys (see TOKENS.md for a portable proof shape).

**Minimum proof metadata (normative):** portable ZK proof bundles MUST carry enough metadata for an independent verifier to reproduce exactly what was verified:

- proof system identifier (e.g., Groth16/PLONK/STARK; carried as `proofSystem` in `TOKENS.md`)
- a versioned `circuitId`
- a `verifyingKeyId` that identifies the exact verifier parameters / verifying key bytes (scheme-specific hash identifier)
- the `statementId` being proven
- binding context (`spendId`, `headEventHash`, and `spendTokenHash` for spend proofs)

## Invariants (Fixed)

These constraints are stable regardless of proof system choice:

1. ZK extensions MUST NOT alter canonical Spend fields
2. ZK extensions MUST NOT influence verification outcomes
3. ZK extensions MUST NOT modify Truth or Reward Ledger entries
4. Proof verification failure MUST NOT invalidate the underlying Spend
5. Commitments are optional; absence MUST NOT affect spend validity
6. ZK commitments and proofs MUST NOT be required to reconstruct canonical state or verify ledger integrity
7. ZK statements MUST NOT be interpreted as upgrading spend verification tier
