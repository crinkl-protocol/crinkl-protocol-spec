---
status: experimental
layer: extension
version: v1
normative: true
---

# Zero-Knowledge Extension Layer

> **Status: v1 optional extension — interface stable, concrete commitment schemes and some circuits incomplete**
>
> This section defines the interface for ZK extensions. Concrete statement types and the circuits that implement them are captured in `zk-circuit-catalog.md`.
>
> Implementation status: the minimal promo-open proof lane is demo-supported. Wallet-secret rollout proofs and general commitment-scheme standardization are target architecture, not required core protocol behavior.

## Purpose

Enable privacy-preserving proofs of spend properties (and, as verified schemas expand, spend-adjacent properties) without revealing underlying receipt data. ZK extensions are optional and additive — they do not alter core verification or ledger semantics.

ZK statements attest only to the truth of the stated rule under protocol semantics and MUST NOT be interpreted as preventing all indirect inference about spend attributes.

ZK statements do not strengthen or supersede the verification tier of the underlying Spend; they only enable selective disclosure about already-verified fields.

For the minimum viable promo use case and the associated “wallet witness” foundation concepts, see `zk-foundation.md`.

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

**Commitment scheme:** To be specified. Candidates include Pedersen commitments (for range proofs) and Poseidon hash (for SNARK compatibility). For Halo2 IPA circuits in `zk-circuit-catalog.md`, commitments are Poseidon-based and bind `(spendIdHash, headEventHash, label, value, blinding)`; see the circuit entry for the exact encoding rules.

### Binding and derivation (normative)

ZK commitments are carried inside a signed `SpendAttestationTokenV1` (see `../03-portability/spend-attestation-token.md`). Verifiers treat commitments as **opaque values** unless accompanied by a proof; the primary security requirement is that any proof claiming something about a commitment is replay-safe and unambiguous about what the commitment commits to.

All ZK commitments MUST:

1. Commit to canonical (hard-verified/corrected) Spend fields at a specific attestation head, and
2. Be cryptographically bound to the corresponding `spendId` and attestation head `headEventHash` (e.g., by domain-separated binding inside the commitment statement / circuit / preimage).

This binding prevents commitments and proofs from being replayed across spends or across different attestation heads for the same spend.

**Label binding (normative):** each commitment MUST be bound to its intended semantic label (e.g., `"C_total"`) so that a proof about one commitment cannot be substituted for a proof about a different commitment field.

### Commitment scheme requirements (normative)

Regardless of scheme choice, commitments MUST be:

- **Binding** (a prover cannot open the same commitment to two different values), and
- **Hiding against feasible enumeration** of the committed field domains (schemes MUST incorporate adequate blinding/salting where domains are small, and that blinding MUST NOT be derivable from public protocol data).

**Determinism note (normative):** the protocol does not require commitments to be publicly recomputable or deterministic across issuers. If a commitment scheme uses blinding/randomness, the required opening material MUST be delivered only via wallet-only witness material (see `../03-portability/spend-attestation-token.md#optional-wallet-witness-non-portable-normative`). If a scheme uses deterministic blinding, the determinism MUST be keyed by secret witness material (e.g., wallet secret) such that third parties cannot enumerate small domains.

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

**Circuit catalog (normative intent):** statement `type` values are only interoperable if verifiers agree on which proof circuits implement them. The mapping from statement types to supported `(proofSystem, circuitId, verifyingKeyId)` MUST be captured in `zk-circuit-catalog.md`.

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

`statementId` identifies the predicate independent of redemption scope. `scopeId` identifies the verification, redemption, or settlement context in which that predicate is being used.

When a ZK proof is used inside a scoped flow:
- the proof transcript or public inputs MUST bind both `statementId` and `scopeId`;
- changing either `statementId` or `scopeId` MUST make proof verification fail;
- `scopeId` MUST NOT be folded back into `statementId`, because `scopeId` itself may reference `statementId` in higher-level artifacts;
- commitment domain separation MAY include `scopeId` when a circuit profile requires context-specific commitments, but this is circuit-specific and must be documented in `zk-circuit-catalog.md`.

**Privacy note on scope binding:**

Scope binding does NOT prevent correlation of the same `spendId` across different scopes. It only ensures that:
- Proofs are cryptographically bound to their intended verification context
- Proofs cannot be copied and replayed in unintended contexts
- Audit trails can track proof usage without exposing user wallet addresses

If multiple proofs reference the same `spendId` across different scopes, verifiers who collude can still correlate those proofs as originating from the same identity-excluded spend. This correlation reveals behavioral patterns (e.g., "this spend qualified for two different conditions") but does NOT reveal user identity when `wallet` is omitted from the underlying Spend Attestation Token.

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

Proof artifacts MUST reference unambiguous, versioned circuit identifiers and verification keys (see ../03-portability/spend-attestation-token.md for a portable proof shape).

**Minimum proof metadata (normative):** portable ZK proof bundles MUST carry enough metadata for an independent verifier to reproduce exactly what was verified:

- proof system identifier (e.g., Groth16/PLONK/STARK; carried as `proofSystem` in `../03-portability/spend-attestation-token.md`)
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


## Spend Token ZK Proof and Wallet Witness Shape

The following proof and witness shapes were moved from the portability layer because ZK is optional extension material. They can accompany a Spend Attestation Token but do not change Core Spend Attestation validity.

### Optional: ZK statement proof (normative)

A ZK statement proof provides a privacy-preserving proof about a Spend without revealing underlying receipt data. It is optional proof material that can accompany a Spend Attestation Token and does not change the Spend’s canonical status.

ZK proofs SHOULD be bound to the referenced spend token hash (`spendTokenHash`) to prevent replay across re-issuance of new spend tokens for the same spend (e.g., when a token changes due to commitment scheme upgrades or corrections).

#### Proof shape (normative)

```text
SpendZkStatementProofV1 {
  schemaVersion: 1,
  spendId: Identifier,
  spendTokenHash: "sha256:" + Hash,
  binding: { headEventHash: Hash }, // MUST match token.lineage.headEventHash
  statement: Object,             // RFC 8785 canonical JSON
  statementId: "sha256:" + Hash, // sha256(RFC8785_canonicalize(statement)); statement MUST include domain+schemaVersion (see ../06-extensions/zk-proof-extension.md)
  proofSystem: String,
  circuitId: String,             // versioned, unambiguous circuit identifier
  verifyingKeyId: "sha256:" + Hash, // identifier of verifier parameters / verifying key bytes (scheme-specific)
  publicInputs: Object,
  proof: Base64
}
```

**Verifying key note (normative):** some proof systems do not have standalone “verifying key bytes” (e.g., Bulletproofs range proofs parameterize verification by generators and bit-length). In that case, `verifyingKeyId` MUST be computed as the hash of a canonical JSON description of the verifier parameters (e.g., `{ domain, proofSystem, circuitId, bits, ... }`), and verifiers MUST recompute it the same way.

#### Verification (normative)

To verify a `SpendZkStatementProofV1`, a verifier MUST:

1. Fetch the referenced Spend Attestation Token, verify its signature, and verify that its `signatures.tokenHash` equals `spendTokenHash`.
2. Verify `binding.headEventHash` equals the referenced token’s `lineage.headEventHash`; reject if mismatched.
3. Recompute `statementId = sha256(RFC8785_canonicalize(statement))` and verify it equals `statementId`.
4. Enforce statement schema policy: reject unknown `statement.domain` or unsupported `statement.schemaVersion` (see `../06-extensions/zk-proof-extension.md`).
5. Resolve the verifying key bytes referenced by `verifyingKeyId` for `(proofSystem, circuitId)`; if the verifier cannot resolve them, it MUST reject.
6. Verify the ZK proof using `proofSystem`, `circuitId`, `verifyingKeyId`, and `publicInputs`.
7. If the referenced Spend Attestation Token includes `zk.commitments`, verify the proof’s `publicInputs` are bound to those commitments and the token’s binding context (`spendId`, `lineage.headEventHash`) (commitment scheme–specific; see ../06-extensions/zk-proof-extension.md).
8. Proof verification MUST be performed in a way that is cryptographically bound to `spendTokenHash` (proof-system specific: e.g., a circuit public input or transcript binding). A proof that is not bound to `spendTokenHash` MUST NOT be treated as a proof about the referenced token.

**Redemption note:** redemption anti-replay requirements (e.g., `scopeId`/`nullifier`) are defined separately in `../06-extensions/zk-foundation.md`. This proof type is an eligibility proof; redemption introduces additional binding requirements.

### Optional: Wallet witness (non-portable, normative)

To enable **client-side proving**, implementations MAY issue a wallet-only “witness envelope” that contains the commitment openings required to prove ZK statements without revealing underlying receipt data.

This witness material is **not portable** and MUST be treated as sensitive private data. It MUST NOT be embedded in portable tokens.

#### Witness shape (normative)

```text
SpendZkWitnessV1 {
  schemaVersion: 1,
  spendId: Identifier,
  spendTokenHash: "sha256:" + Hash,      // hash of the referenced Spend Attestation Token (portable)
  binding: { headEventHash: Hash },      // MUST match token.lineage.headEventHash
  openings: {
    storeHash?: { value: Hash, blinding: Base64 }, // opening for zk.commitments.C_store (scheme-specific encoding)
    totalCents?: { value: Amount, blinding: Base64 }, // opening for zk.commitments.C_total (scheme-specific encoding)
    dayIndex?: { value: String, blinding: Base64 }, // opening for zk.commitments.C_dayIndex (days since epoch; scheme-specific encoding)
    geoRegion?: { value: String, blinding: Base64 },   // opening for zk.commitments.C_geoRegion (scheme-specific encoding)
    cbsaCode?: { value: String, blinding: Base64 }     // opening for zk.commitments.C_cbsaCode (scheme-specific encoding)
  }
}
```

#### Distribution (normative)

`SpendZkWitnessV1` MUST be distributed only inside a trusted boundary, typically by encrypting it to a wallet-controlled public key and delivering it to the wallet (e.g., via authenticated API).

#### Constraints (normative)

- A witness MUST be bound to a single spend token via `spendTokenHash`.
- A witness MUST be bound to a single attestation head via `binding.headEventHash`.
- If a spend is corrected and the attestation head changes, prior witnesses MUST NOT be reused.
- A witness MUST NOT include receipt images, raw OCR text, or ingestion metadata.
- A witness SHOULD contain only the minimum opening material required to prove statements over commitments; it MUST NOT include stable identifiers that enable cross-spend linkage beyond `spendId` and the bound `headEventHash`.
