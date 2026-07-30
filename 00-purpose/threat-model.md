---
status: draft
layer: purpose
version: v1
normative: true
---

# Security Model

Security properties required for correctness and integrity across implementations.

Terms are defined in ../08-governance/glossary.md and used normatively throughout this specification.

## Cryptographic Requirements

| Component | Specification |
|-----------|---------------|
| Serialization | RFC 8785 (JSON Canonicalization Scheme) |
| Hash | SHA-256, lowercase hex output |
| Signature | Ed25519 (RFC 8032), base64 output |
| Signature input | Raw 32-byte SHA-256 digest (not hex string) |

### Fixed invariants vs versioned parameters (normative)

For a given `protocolVersion`, implementations MUST treat the following as fixed security invariants:

- **Canonicalization:** RFC 8785 JSON canonicalization (JCS) is the sole source of truth for hash preimages.
- **Hash function:** SHA-256 with lowercase-hex encoding for `Hash` fields.
- **Signature scheme:** Ed25519 over the raw 32-byte SHA-256 digest.
- **Integrity envelope construction:** exactly as defined in `../01-core/canonicalization.md#integrity-envelope`.
- **Commitment-layer Merkle hashing rules:** domain separation + ordering rules as defined in `../05-reward-and-settlement/settlement-bindings.md`.

The following parameters are versioned/evolvable and MUST be treated as data (not implicit assumptions):

- Token `schemaVersion` and commitment `schemaVersion` values.
- ZK proof system choice, circuit identifiers, and verification keys (when present).
- Chain bindings (finality assumptions, tx references, address formats), as defined by the deployment.

Changing a fixed invariant requires a protocol MAJOR version bump (see `../08-governance/versioning.md`).

## Integrity Envelope

**Normative source:** `../01-core/canonicalization.md#integrity-envelope` is authoritative. This section is a security-focused restatement; in case of conflict, `../01-core/canonicalization.md` wins.

Every event MUST include:
- `eventHash` — SHA-256 of RFC 8785 canonical JSON excluding `eventHash` and `signature`
- `prevHash` — `eventHash` of prior event in stream (null for bootstrap)
- `signature` — Ed25519 signature over raw 32-byte SHA-256 digest (not hex string)

**eventHash computation (normative):**
1. Start with the complete event object
2. Remove `eventHash`
3. Remove `signature`
4. RFC 8785 canonicalize the remaining JSON
5. Compute SHA-256 and encode as lowercase hex

**Signature input (normative):** signature MUST cover the raw 32-byte digest (the bytes of SHA-256 output), not the hex string.

## Trust Roots

### Trust roots (normative, closed categories)

The protocol assumes trust in the following categories of roots. Each has a bounded scope: it enables verification of *specific claims* and MUST NOT be interpreted as asserting anything beyond that scope.

| Trust root category | What it is trusted to assert | What it is NOT trusted to assert | Where defined |
|---|---|---|---|
| Spend-stream signing keys | Authenticity/integrity of spend-stream events for a given `protocolVersion` | Ground truth of receipts; user ownership; fraud intent | `../01-core/spend-event.md` + deployment configuration (v1), evolvable via `protocolVersion` |
| System-stream authority keys (Authority Registry) | Authenticity/integrity of system-stream events (commitments, authority changes) for a `chainId` | Correctness of off-chain reward policy; spend truth beyond what is committed | `../01-core/spend-event.md`, `../05-reward-and-settlement/settlement-bindings.md` |
| External chain consensus (when used) | Immutability/finality of published commitment records and authority registry transactions | Economic backing correctness; issuer honesty; availability of off-chain proofs | Chain bindings + deployment assumptions |
| Token issuer authorization | That a token signature key is an authorized issuer key for the referenced `issuedBy` | That the token’s claim corresponds to external reality beyond the claim definition | `../03-portability/spend-attestation-token.md` + the applicable trust root mapping (Authority Registry or configured issuer set) |
| Merchant-claim verifier authorization (optional extension) | That a merchant claim verifier issued a signed claim attestation for a bounded store identity scope | Spend truth; payment settlement; merchant intent for any spend; correctness of private evidence beyond the attestation semantics | `../06-extensions/merchant-authority.md` + deployment authorization mapping |
| Proof-validator finality certificates | That a quorum of selected, registered proof validators independently recomputed a deterministic public statement from committed material and co-signed the identical result | Ground truth of receipts; honesty of the verification service beyond its committed output; payout authority; production chain finality | `../02-proof-lifecycle/admission.md` + authority-signed registry/assignment artifacts |

Proof-validator registry and quorum consumers MUST enforce
[`validator-signing-key-independence.md`](../02-proof-lifecycle/validator-signing-key-independence.md).
An authority signature authenticates registry bytes but does not turn two
active rows sharing one Ed25519 public key into two independent actors.

**Signer-role isolation (normative):**
- Keys authorized for system-stream signing MUST NOT be accepted for spend-stream event signing, and vice versa.
- Verifiers MUST reject signatures from unknown, expired, or revoked authorities under the applicable root.

**v1 note (normative intent):** protocol v1 assumes spend-stream events are signed by an operator/verifier authority key (a spend-stream trust root). Wallet addresses are carried as data and are not assumed to be signers unless explicitly introduced by a future protocol version.

### Spend-stream issuer key distribution (non-normative guidance)

Portable verification requires that verifiers can obtain the issuer authorization mapping (which `publicKey` values are authorized for a given `issuedBy`) without trusting a mutable private API response as a source of truth.

The protocol allows this mapping to be provided by either:
- an Authority Registry (system-stream / chain-bound governance), or
- deployment configuration (“configured issuer set”) for protocol v1-style deployments.

**Recommended operational pattern (non-normative):**
- publish a cacheable, versioned issuer keyset artifact (e.g., a signed “issuer keyset snapshot” document or extension token) that includes validity windows and revocation markers, and
- have verifiers pin or cache that artifact (similar to how they would treat a trust root bundle).

This does not introduce a new trust root category; it is a distribution mechanism for the existing “Token issuer authorization” trust root.

### Key formats, rotation, and revocation (normative)

- **Key format:** Ed25519 public keys are 32 bytes and MUST be encoded as base64 when carried in protocol artifacts (`publicKey`). Ed25519 signatures are 64 bytes and MUST be encoded as base64 (`signature`).
- **Authority rotation (system-stream):** system-stream events MUST be verified against the Authority Registry validity window at the event-effective time (see `../01-core/spend-event.md` and `../05-reward-and-settlement/settlement-bindings.md`).
- **Revocation semantics:** events/commitments signed by an authority during its validity window remain valid historical artifacts; verifiers MUST reject events whose effective time falls outside the signer’s validity window (including after revocation).

## Verification Checklist

Checklist items MUST be implementable as boolean checks with reject conditions.

For every ingested event, a verifier MUST:
1. **Schema presence:** require all required envelope fields for the stream type (`../01-core/spend-event.md`); reject if missing.
2. **Protocol version:** require `protocolVersion`; reject if missing or unsupported.
3. **Integrity:** recompute `eventHash` per `../01-core/canonicalization.md#integrity-envelope`; reject on mismatch.
4. **Signature:** verify the Ed25519 signature over the raw digest; reject on failure.
5. **Trust root:** verify the signing key is authorized under the applicable trust root; reject if unauthorized/expired/revoked.
6. **Ordering/linkage:** verify `prevHash` matches the prior canonical event in the same stream (spend-stream keyed by `spendId`, system-stream keyed by `chainId`); reject forks and gaps. If local history is incomplete, the verifier MAY return “indeterminate” until it has sufficient history to decide.

## Token Verification

Tokens are verification-ready bundles built from the same primitives: signed events and (optionally) committed Merkle roots. Token verification MUST reduce to the event and commitment verification rules defined in this document and in ../05-reward-and-settlement/settlement-bindings.md (see ../03-portability/spend-attestation-token.md).

At minimum, a verifier MUST:
- Recompute the token hash (`tokenHash`) from the unsigned token and verify its signature.
- Verify the token’s `issuedBy`/`publicKey` is an authorized issuer key under the applicable trust root mapping (Authority Registry or configured issuer set); reject if not authorized.

### Aggregate Commitments (GMV)

Verified GMV Tokens are intended to be portable and privacy-safe. They MUST NOT include receipt images, raw OCR text, store names, itemization, or ingestion metadata.

Their integrity rests on:

- a deterministic token hash (RFC 8785 canonicalization + SHA-256), signed by the protocol authority, and
- a deterministic Merkle root (`spendHeadSetRoot`) committing to which spends and which canonical head states were counted (domain-separated leaf/internal hashing consistent with the Commitment Layer).

Verified GMV Tokens attest that the included spends reached a defined verification tier and were counted under the token's declared as-of rule. They do not imply reward eligibility unless `issuedGMV`, reward commitment artifacts, or an explicit policy artifact is present. The confidence conveyed is bounded by protocol verification semantics and does not imply external ground-truth validation or fraud impossibility.

## Protocol Invariants

| Invariant | Meaning |
|-----------|---------|
| Append-only | Ledger entries are never deleted or modified |
| Deterministic | Same input + protocolVersion = same output |
| Replayable | Final state reconstructible from events alone |
| Linearly chained | Spend-stream events chain per `spendId`; system-stream events chain per `chainId` via `prevHash` |
| Reward-isolated | Attestation corrections don't mutate prior rewards |

## Negative Invariants (Normative)

These are testable “MUST NOT” constraints intended to prevent protocol drift into non-portable or identity-bearing designs:

- The protocol MUST NOT require access to private operator databases or internal event stores to verify a **portable token**.
- The protocol MUST NOT require trusting any HTTP API response as an authority for protocol “truth” (only signed and/or committed artifacts per this spec).
- The protocol MUST NOT require receipt images, OCR text, or human review artifacts to validate portable tokens.
- The protocol MUST NOT define or require a protocol-level identity graph (wallet routing and identity are application-layer concerns).
- The protocol MUST NOT require private wallet lookup or app-user lookup to validate a portable Spend Attestation Token.
- The protocol MUST NOT introduce mutable, user-scoped state as a verification prerequisite (verification relies on append-only streams and commitments only).

## Fraud Handling

**Hard boundary (normative):** the protocol does not adjudicate intent or “fraud”. It records verifiable events, commitments, and corrections under well-defined semantics.

Application layer may determine fraud and emit `FRAUD_FLAGGED`:
- `FRAUD_FLAGGED` is observational and MUST NOT participate in attestation state transitions (`../01-core/spend-event.md`).
- `FRAUD_FLAGGED` MUST NOT modify the Reward Ledger (no clawback / no reward adjustments).
- `FRAUD_FLAGGED` MUST NOT retroactively invalidate signatures, hashes, or commitments already published.
- Protocol-canonical changes to spend state occur only via `SPEND_INVALIDATED` or `SPEND_CORRECTED` in the Attestation Ledger.

## Threat assumptions (surface even if mitigations are operational)

- **Compromised issuer key:** an attacker may sign artifacts. Mitigation is bounded by key rotation/revocation under the applicable trust root; consumers SHOULD treat post-compromise artifacts as invalid once revocation is known.
- **Malicious client inputs:** clients may submit crafted payloads. The protocol does not assume client honesty; integrity comes from verification pipeline outputs + signer authorization.
- **Chain reorg/finality lag:** on-chain commitments depend on chain consensus; verifiers SHOULD apply chain-specific finality thresholds before treating commitments as stable.
- **Availability:** proofs and tokens may be unavailable; availability is not guaranteed by the protocol and MUST be handled operationally (caching, replication, audits).

## Non-Goals

Out of scope: receipt image authenticity, secure enclaves, device security, wallet authentication, PII encryption, economic modeling, Sybil resistance.
