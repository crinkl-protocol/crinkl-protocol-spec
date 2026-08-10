---
status: draft
layer: core
version: v1
normative: true
---

# Canonicalization and Data Structures

This section defines the canonical byte rules and core data structures used by the Crinkl Protocol. Many internal event-stream structures are wallet-scoped (spend-stream), while some are system-scoped (system-stream) and are not bound to a wallet. Wallet-scoped event structure does not imply that portable Spend Attestation Tokens must expose wallet identity.

Shared scalar encodings and domain-separated hash names may be reused by downstream layers. That reuse does not make reward, settlement, ZK, Solana, or campaign semantics part of Core.

## Serialization

All protocol data MUST be serialized using **RFC 8785 JSON Canonicalization Scheme (JCS)**:
- UTF-8 encoding
- Object keys sorted lexicographically by UTF-16 code units
- No whitespace between tokens
- Numbers in shortest form without leading zeros (except `0`), no `+` prefix, no trailing decimal zeros
- Strings escaped per RFC 8259

### Global hashing rule (normative)

Unless a section explicitly defines a non-JSON preimage, **all hashes and signatures in this protocol MUST be computed over RFC 8785-canonicalized JSON** of the relevant object.

Examples:
- `eventHash` is computed from the canonical JSON of an event envelope (excluding `eventHash` and `signature`).
- `tokenHash` is computed from the canonical JSON of an unsigned token object (see `../protocol/portability/spend-attestation-token.md`).

Implementations MAY use alternative internal encodings, but the canonical hash/signature preimages MUST be RFC 8785 canonical JSON as specified in this document.

### Arrays and ordering (normative)

RFC 8785 canonicalizes object keys, but **does not canonicalize array order**.

- Array ordering is part of the canonical preimage: changing element order changes hashes.
- If an array field is semantically a set/unordered collection, the specification for that field MUST define a canonical order and producers MUST construct the array in that order.
- Verifiers MUST NOT reorder arrays prior to hashing or signature verification.

## Cryptographic Primitives

| Primitive | Specification |
|-----------|---------------|
| Hash | SHA-256, output as lowercase hex (64 chars) |
| Signature | Ed25519 (RFC 8032), output as base64 |
| Timestamps | ISO 8601 with milliseconds, UTC (`YYYY-MM-DDTHH:mm:ss.sssZ`) |

### Domain separation (normative)

The protocol uses domain separation to prevent cross-artifact ambiguity. Domain separation may be achieved via:
- explicit prefix bytes/strings inside the hashed preimage, and/or
- structural separation (hashing different canonical objects that include a type field).

| Artifact | Digest name | Preimage type | Domain separation mechanism | Where defined |
|---|---|---|---|---|
| Event integrity | `eventHash` | RFC 8785 canonical JSON | Structural (envelope includes `eventName`, stream key, `protocolVersion`) | `canonicalization.md#integrity-envelope` + `spend-event.md` |
| Token signature digest | `tokenHash` | RFC 8785 canonical JSON | Structural (unsigned token includes `tokenType`, `schemaVersion`) | `../protocol/portability/spend-attestation-token.md` |
| Store hash (token field) | `storeHash` | bytes | ASCII prefix `"crinkl.store.v1:"` + canonical `storeId` | `../protocol/portability/spend-attestation-token.md#spend-attestation-token` |
| Commitment-layer Merkle leaf | (binary hash) | bytes | Prefix `0x00` | `../protocol/applications/economics/settlement-bindings.md#merkle-tree` |
| Commitment-layer Merkle internal | (binary hash) | bytes | Prefix `0x01` | `../protocol/applications/economics/settlement-bindings.md#merkle-tree` |
| Blinded recipient id | `recipientId` | bytes | ASCII prefix `"crinkl.recipient.v1:"` + context | `../protocol/applications/economics/settlement-bindings.md#recipient-blinding` |
| ZK statement identity (extension) | `statementId` | RFC 8785 canonical JSON | Structural (statement object is type-tagged) | `../06-extensions/zk-foundation.md`, `../06-extensions/zk-proof-extension.md` |

### Privacy note on low-entropy fields (normative)

Hashing a low-entropy value (e.g., region codes, booleans, small categorical values) is **not** a privacy mechanism: such hashes are enumerable.

If a value must be represented in a portable artifact without disclosure, the protocol MUST either:
- omit it,
- commit to it with a hiding commitment scheme (e.g., ZK commitments), or
- include it only inside a proof system that provides hiding (scheme-specific).

## Scalar Types

All protocol fields are expressed using a small set of scalar types. Implementations MUST follow the encoding rules below to avoid cross-language drift (notably JavaScript number precision).

### Identifier

- **Type:** JSON string
- **Constraints:** non-empty; treated as opaque by the protocol
- **Normalization:** none (byte-preserving); do not trim, case-fold, or normalize
- **Range:** unbounded by the protocol; implementations SHOULD apply sane maximum lengths to avoid DoS
-
**Privacy note (normative intent):** any identifier that may be shared outside a trusted boundary (notably `spendId`) SHOULD be unpredictable (high-entropy / non-sequential) to reduce enumeration and linkability risks in proofs and tokens.

### WalletRef

- **Type:** JSON string
- **Constraints:** non-empty; treated as opaque by the protocol
- **Normalization:** none (byte-preserving); do not trim, case-fold, or normalize
- **Range:** unbounded by the protocol; implementations SHOULD apply sane maximum lengths to avoid DoS

### Version

- **Type:** JSON string
- **Format:** `MAJOR.MINOR.PATCH` (SemVer-compatible)

### Timestamp

- **Type:** JSON string
- **Format:** `YYYY-MM-DDTHH:mm:ss.sssZ` (UTC, milliseconds required)
- **Unit:** milliseconds
- **Normalization:** MUST be UTC with `Z` suffix; offsets MUST be normalized to UTC before hashing/signing
- **Leap seconds:** MUST NOT be used; inputs containing leap seconds MUST be rejected or normalized prior to inclusion in signed artifacts

### DateISO

- **Type:** JSON string
- **Format:** `YYYY-MM-DD` (UTC date; no time component)
- **Normalization:** MUST be zero-padded and represent the UTC day boundary used by the protocol (including downstream windowed aggregate artifacts).

### Points / Satoshis

- **Type:** JSON string
- **Format:** base-10 integer with no leading `+`; use `0` or a non-zero digit followed by digits: `^(0|[1-9][0-9]*)$`
- **Unit:** integer points / integer satoshis
- **Range:** non-negative arbitrary precision integer; implementations MUST support at least unsigned 64-bit range
- **Rationale:** avoids JS precision drift and makes canonicalization unambiguous across implementations

### Amount (Cents)

- **Type:** JSON string
- **Format:** base-10 non-negative integer: `^(0|[1-9][0-9]*)$`
- **Unit:** smallest currency unit for the referenced currency (e.g., cents for USD)
- **Range:** non-negative arbitrary precision integer; implementations MUST support at least unsigned 64-bit range
- **Rationale:** aggregate spend totals can exceed JS safe integer range; string encoding ensures cross-language consistency (same pattern as Points/Satoshis)

### Hash

- **Type:** JSON string
- **Format:** lowercase hex SHA-256 digest (64 chars): `^[0-9a-f]{64}$`
- **Normalization:** none; MUST already be lowercase hex

### Signature

- **Type:** JSON string
- **Format:** base64 encoding of 64-byte Ed25519 signature
- **Normalization:** none

### PublicKey

- **Type:** JSON string
- **Format:** base64 encoding of 32-byte Ed25519 public key
- **Normalization:** none

## Integrity Envelope

Every protocol **event** MUST include the following envelope fields. Ledger entries are derived views projected from events and do not carry their own envelope.

```text
IntegrityEnvelope {
    eventHash: Hash,              // REQUIRED. SHA-256 of canonical serialization excluding eventHash and signature fields.
    prevHash: Optional<Hash>,     // REQUIRED. Hash of prior event in stream; null for stream bootstrap.
    signature: Signature          // REQUIRED. Ed25519 signature over eventHash bytes (not hex string).
}
```

`prevHash` is defined per stream key: spend-stream events chain per `spendId`, and system-stream events chain per `chainId` (see spend-event.md). The first event in any stream MUST set `prevHash` to `null`.

**eventHash computation:**
1. Start with the complete event object
2. Remove the `eventHash` field (since we're computing it)
3. Remove the `signature` field (since signature covers the hash)
4. Canonicalize remaining fields per RFC 8785
5. Compute SHA-256, output as lowercase hex (64 chars)

Signature covers the raw 32-byte SHA-256 digest, not the hex-encoded string.

### Context binding (normative)

To prevent cross-stream ambiguity and replay, verifiers MUST validate that the event object conforms to the correct envelope schema for its stream type (see `spend-event.md`).

`eventHash` binds the event to:
- its `eventName`,
- its `protocolVersion`, and
- its stream key (`spendId` for spend-stream, `chainId` for system-stream),
because those fields are part of the hashed envelope object for the corresponding schema.

## ReceiptUpload

Payload for the `RECEIPT_UPLOADED` event (see spend-event.md). This structure is embedded inside a SpendStreamEvent envelope.

```text
ReceiptUpload {
    uploadId: Identifier,
    imageDataRef: BlobRef,
    metadata: Optional<Metadata>
}
```

- **uploadId** – unique submission identifier.
- **imageDataRef** – reference to the receipt image data (see BlobRef below).
- **metadata** – optional unverified hints (e.g., store name, receipt timestamp).

> **Note:** `wallet`, `timestamp`, and `protocolVersion` are carried in the SpendStreamEvent envelope. The payload does not duplicate them.

## SoftSpend
Represents the output of Soft Verification.

```text
SoftSpend {
    spendId: Identifier,
    wallet: WalletRef,
    softVerificationStatus: SoftVerificationStatus,
    softExtractedFields: ExtractedFieldsApprox,
    riskFlags: List<RiskFlag>,
    createdAt: Timestamp
}
```

- spendId – identifier provisionally associated with the record.
- wallet – wallet tied to the submission.
- softVerificationStatus – preliminary classification.
- softExtractedFields – approximated extraction values.
- riskFlags – optional diagnostic indications.
- createdAt – Soft Verification timestamp.

## Spend
Represents the canonical, normalized economic record after Hard Verification.

```text
Spend {
    spendId: Identifier,
    wallet: WalletRef,
    storeId: StoreIdentifier,
    totalCents: Amount,
    currency: CurrencyCode,
    timestamp: Timestamp,
    geoRegion: RegionCode,
    cbsaCode?: CBSACode,
    verificationStatus: VerificationStatus,
    verificationVersion: Version,
    normalizedAt: Timestamp
}
```

### Field Specifications

**storeId** — Canonical merchant identifier. Normalization rules:
1. Convert to lowercase
2. Apply NFKD Unicode normalization
3. Strip combining marks (Unicode category `Mn`) to remove diacritics
4. Replace whitespace and word separators (spaces, slashes, ampersands) with hyphens
5. Remove remaining non-alphanumeric characters except hyphens
6. Collapse consecutive hyphens to single hyphen
7. Trim leading/trailing hyphens
8. Example: `"Example Market #1234"` -> `"example-market-1234"`

**totalCents** — Base-10 integer string cents (or smallest currency unit). MUST be non-negative and MUST match the `Amount (Cents)` format.

**currency** — ISO 4217 three-letter code, uppercase (e.g., `USD`, `EUR`, `GBP`).

**timestamp** — Transaction time from receipt, normalized to ISO 8601 UTC.

**geoRegion** — ISO 3166-2 subdivision code (e.g., `US-CA`, `GB-ENG`) or ISO 3166-1 alpha-2 country code if subdivision unknown.

**cbsaCode** — OPTIONAL. CBSA metro area code (e.g., `"12420"`) or non-metro fallback (e.g., `"non-metro:US-MT"`). Derived from store location via public OMB crosswalk. See `CBSACode` scalar type.

**verificationStatus** — One of: `HARD_VERIFIED`, `INVALIDATED`, `CORRECTED`.

## Attestation Ledger Entry

```text
AttestationLedgerEntry {
    spendId: Identifier,
    wallet: WalletRef,
    previousState: VerificationState,
    nextState: VerificationState,
    eventName: EventName,
    eventPayload: EventPayload,
    timestamp: Timestamp
}
```

## Downstream Reward Ledger Entries

Reward ledger entries are defined in `../protocol/applications/economics/reward-layer.md`. They reuse the scalar encodings in this file, but reward issuance is downstream of Core spend attestation.

## Referenced Types

The following types are used in structures above. Enumerations are normative; implementations MUST reject unknown values.

### BlobRef

- **Type:** JSON string
- **Format:** URI or content-addressable hash reference to binary data
- **Constraints:** non-empty; scheme-specific (e.g., `ipfs://`, `sha256://`, or platform storage URI)

### Metadata

- **Type:** JSON object
- **Constraints:** arbitrary key-value pairs; keys MUST be strings; values MUST be JSON primitives or arrays of primitives
- **Note:** unverified hints from the submitter; not used for protocol decisions

### StoreIdentifier

- **Type:** JSON string
- **Format:** normalized merchant identifier (see storeId normalization rules in Spend)

### CurrencyCode

- **Type:** JSON string
- **Format:** ISO 4217 three-letter code, uppercase (e.g., `USD`, `EUR`, `GBP`)

### RegionCode

- **Type:** JSON string
- **Format:** ISO 3166-2 subdivision code (e.g., `US-CA`) or ISO 3166-1 alpha-2 country code (e.g., `US`)
- **Usage:** carried in spend events and portable tokens as geographic identifier derived from receipt/store data

### CBSACode

- **Type:** JSON string
- **Format:** CBSA numeric code as string (e.g., `"12420"` for Austin-Round Rock-Georgetown, TX) or a non-metro fallback in the format `"non-metro:{RegionCode}"` (e.g., `"non-metro:US-MT"`)
- **Source:** US Office of Management and Budget (OMB) Core Based Statistical Area definitions. Free public crosswalk: city/county → CBSA. Updated periodically by OMB.
- **Usage:** optional metro-area-level geographic bucketing for predicate evaluation, aggregate outputs, and optional enrichment of per-spend data. Provides local-business-meaningful granularity while preserving reasonable privacy properties for aggregation.

**Derivation (normative):**

- For US spends: implementations MUST derive `CBSACode` from the store's physical location via city/county → CBSA lookup using the OMB delineation file or equivalent public crosswalk. If a store falls outside any CBSA (rural area), the code MUST be `"non-metro:{state}"` where `{state}` is the ISO 3166-2 state code (e.g., `"non-metro:US-MT"`).
- For non-US spends: `CBSACode` is not applicable. Implementations SHOULD use the ISO 3166-1 alpha-2 country code as a fallback region key in aggregate tokens.
- If the store's location cannot be resolved to a CBSA, implementations MUST use `"UNKNOWN"`.

**Privacy note:** some CBSAs have small populations. Implementations SHOULD define a minimum-spend-count threshold below which a CBSA bucket is rolled up into a coarser grouping (e.g., state or non-metro) in aggregate tokens. This threshold is an implementation/policy decision, not a protocol-level constant.

### SoftVerificationStatus

Preliminary classification from Soft Verification.

| Value | Description |
|-------|-------------|
| `PENDING` | Awaiting Soft Verification |
| `SOFT_VERIFIED` | Passed Soft Verification; queued for Hard Verification |
| `REJECTED` | Failed Soft Verification (e.g., not a receipt, unreadable) |

### VerificationStatus

Final classification after Hard Verification.

| Value | Description |
|-------|-------------|
| `HARD_VERIFIED` | Passed Hard Verification; canonical spend record |
| `INVALIDATED` | Failed Hard Verification or flagged as fraud |
| `CORRECTED` | Previously verified but corrected (e.g., duplicate resolution) |

### VerificationState

FSM state for spend-stream (see verification-state.md).

| Value | Description |
|-------|-------------|
| `UPLOADED` | Receipt uploaded, awaiting Soft Verification |
| `SOFT_VERIFIED` | Passed Soft Verification |
| `HARD_VERIFIED` | Passed Hard Verification |
| `INVALIDATED` | Terminal invalid state |
| `CORRECTED` | Canonical spend interpretation superseded |

### ExtractedFieldsApprox

Approximate extraction from Soft Verification (low-confidence).

```text
ExtractedFieldsApprox {
    storeName: Optional<String>,
    totalAmount: Optional<String>,
    currency: Optional<CurrencyCode>,
    transactionDate: Optional<Timestamp>,
    confidence: Number  // 0.0–1.0
}
```

### RiskFlag

Diagnostic indicators from verification pipeline.

| Value | Description |
|-------|-------------|
| `low_confidence_ocr` | OCR confidence below threshold |
| `potential_duplicate` | Similar receipt detected; Hard Verification MUST invalidate or correct instead of emitting `SPEND_HARD_VERIFIED` |
| `unusual_amount` | Amount outside normal range |
| `velocity_warning` | Submission rate anomaly |
| `geo_mismatch` | Store location inconsistent with claimed or observed submission context |

### EventName

Event type identifier (see spend-event.md for full list).

- **Type:** JSON string
- **Constraints:** uppercase snake_case (e.g., `RECEIPT_UPLOADED`, `HARD_VERIFIED`, `FRAUD_FLAGGED`)

### EventPayload

- **Type:** JSON object
- **Constraints:** structure depends on EventName; see spend-event.md for payload schemas

---

## Schema Evolution

- **Additive only:** New optional fields with safe defaults; new event types rather than overloading existing fields.
- **No semantic drift:** If behavior changes, introduce a new field (e.g., `verificationVersionV2`).
- **Reserved namespaces:** `_meta` and `extensions` are reserved for future use; preserve during canonicalization.
- **No removal:** Fields may only be removed after the corresponding `protocolVersion` range is declared unsupported.

### Verifier behavior under version skew (normative)

Verifiers MUST apply the following rules to prevent forked behavior:

| Situation | Verifier action |
|---|---|
| Unknown `protocolVersion` | Reject (cannot verify semantics safely). |
| Known `protocolVersion`, unknown additional fields | Include in hash/signature verification; ignore semantics unless explicitly specified; do not drop fields before hashing. |
| Unknown enum value in a normative enum | Reject (unknown semantics). |
| Unknown event type (`eventName`) | Reject. |
| Unknown token `schemaVersion` for a portable token | Reject (cannot interpret claim/verification procedure safely). |

**Implementation note (normative):** to verify hashes/signatures under forward-compatibility, verifiers SHOULD hash the raw parsed JSON object (preserving unknown fields) before decoding into a typed structure that may drop unknown members.

**Reserved namespaces:** if `_meta` or `extensions` objects are present, verifiers MUST preserve them during hash/signature verification and MUST ignore their semantics unless an explicit `protocolVersion` extension defines behavior.

## Token Bundles

Token bundles (see ../protocol/portability/spend-attestation-token.md) are composed of existing protocol objects (events, leaves, proofs). When a token bundle includes protocol events or leaves, verifiers MUST treat them as the canonical inputs to hashing/signature verification:

- Recompute hashes from the embedded objects (do not trust precomputed hashes without checking).
- Verify signatures against the correct trust root for the embedded object’s `protocolVersion` / authority registry validity windows.
- Apply the global hashing rule: all embedded object hashes/signatures are verified over RFC 8785 canonical JSON unless the embedded object’s section defines a binary preimage (e.g., Merkle node hashing in the Commitment Layer).
