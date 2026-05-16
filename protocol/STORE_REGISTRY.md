# Store Registry (v1) — Canonical Merchant + Location Taxonomy (Extension)

> **Status:** v1 (optional extension; non-core)
>
> This document defines a **portable, publicly replicable** way to standardize store and store-location identifiers across implementations without changing the core token set in `TOKENS.md`.

## Goals

- Provide a **standard identifier** for:
  - a merchant / chain / brand (`storeId`)
  - an optional physical location (`storeLocationId`)
- Allow third parties to deterministically compute:
  - `storeHash` (already used by Spend Attestation Tokens)
  - optional `storeLocationHash` (extension primitive; not in core tokens)
- Provide a **verifiable registry snapshot** (signed + Merkle-rooted) so verifiers can resolve store identities without trusting a private API.

## Non-goals

- This registry does **not** define a new protocol trust root. It reuses existing issuer/authority key authorization rules (see `SECURITY_MODEL.md#trust-roots`).
- This registry does **not** change core Spend Attestation / Reward Commitment / Verified GMV / Verified Spend Distribution verification procedures.
- This registry does **not** require any recipient identity exposure.

## Core primitives

### `storeId` (canonical merchant identifier)

`storeId` is an **Identifier string** (see `DATA_STRUCTURES.md#identifier`) representing a merchant family identity (typically chain/brand-level).

**Normative recommendation (namespacing):** `storeId` SHOULD be namespaced to avoid collisions and to allow multiple authorities to interoperate. Because core `Spend.storeId` is a normalized identifier (see `DATA_STRUCTURES.md#spend`), prefer **prefix-style namespacing** using the same character set (e.g., lowercase + digits + hyphens).

- `crinkl-store-<slug>` (Crinkl-curated namespace)
- `gs1-gcp-<id>` (GS1 Company Prefix / party identifiers when available)
- `visa-merchant-<id>` / `mc-merchant-<id>` (network merchant identities, if available)

### `storeLocationId` (optional physical location identifier)

`storeLocationId` is an **Identifier string** representing a specific physical location.

**Normative recommendation:** when a globally standardized location identifier exists, implementations SHOULD prefer it:

- `gs1-gln-<digits>` (GS1 Global Location Number)

Otherwise, a namespaced operator identifier MAY be used:

- `crinkl-storeloc-<slug>` (operator-curated; must be stable)

### Hashes (portable primitives)

**Store hash (core, already in `TOKENS.md`):**

- `storeHash = "sha256:" + SHA-256( UTF8("crinkl.store.v1:") || UTF8(storeId) )`

**Store location hash (extension primitive):**

- `storeLocationHash = "sha256:" + SHA-256( UTF8("crinkl.storeloc.v1:") || UTF8(storeLocationId) )`

> Privacy note: `storeHash` is not intended as a privacy mechanism; it is a deterministic public identifier. Avoid embedding raw `storeLocationId` into portable tokens unless explicitly required.

## Registry snapshots (portable, signed, Merkle-rooted)

The registry is distributed as a signed snapshot object. A verifier can:

1. verify the snapshot signature using the issuer authorization mapping, and
2. verify inclusion proofs against the snapshot’s published Merkle roots.

### Snapshot token (non-core extension token)

```text
StoreRegistrySnapshotTokenV1 {
  tokenType: "STORE_REGISTRY_SNAPSHOT", // non-core extension tokenType
  schemaVersion: 1,

  registry: {
    registryId: Identifier,          // e.g. "crinkl-store-registry-main"
    registryVersion: Version,        // issuer-chosen; monotonic per registryId (policy)
    generatedAt: TimestampISO,       // snapshot generation time
    entryCount: Integer,
    entriesRoot: Hash,               // Merkle root over StoreEntryV1 leaves

    locationEntryCount?: Integer,
    locationEntriesRoot?: Hash       // Merkle root over StoreLocationEntryV1 leaves (optional)
  },

  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

**Derivation rules (normative):**

- `tokenHash` and signature rules match `TOKENS.md` (`tokenHash = sha256(RFC8785(unsignedToken))`).
- `entriesRoot` MUST be computed using the Merkle rules in `COMMITMENT_LAYER.md#merkle-tree`:
  - leaf hash: `SHA-256(0x00 || RFC8785(leaf))`
  - internal hash: `SHA-256(0x01 || min(left,right) || max(left,right))`
  - leaves sorted by `storeId` in lexicographic UTF-8 byte order
  - duplicates rejected
- If `locationEntriesRoot` is present, its tree MUST follow the same Merkle rules and be sorted by `storeLocationId` (UTF-8 byte order).

### Store entry (leaf)

```text
StoreEntryV1 {
  storeId: Identifier,              // canonical key (namespaced)
  displayName: String,              // human-friendly name ("Example Merchant")
  logo?: StoreLogoV1,               // OPTIONAL; display-only UI hint (not needed for token verification)
  brandKey?: Identifier,            // optional grouping key (issuer-defined)
  categories?: [String],            // optional; array MUST be sorted lexicographically
  externalIds?: [ExternalIdV1],     // optional; array MUST be sorted deterministically
  aliases?: [String],               // optional; curated alternate names; array MUST be sorted lexicographically
  status?: "ACTIVE"|"DEPRECATED"    // optional lifecycle hint
}

StoreLogoV1 {
  uri: BlobRef,                     // pointer to logo bytes (e.g., https://... or ipfs://...)
  contentHash?: "sha256:" + Hash,   // OPTIONAL; sha256 of raw bytes for integrity pinning
  mimeType?: String                 // OPTIONAL; e.g. "image/png"
}
```

```text
ExternalIdV1 {
  namespace: String,                // e.g. "gs1", "google", "osm"
  type: String,                     // e.g. "gln", "place_id"
  value: String                     // opaque external identifier string
}
```

**Array ordering (normative):**

- `categories` MUST be sorted lexicographically (UTF-16 code units) before hashing (see RFC 8785 array rules note in `DATA_STRUCTURES.md`).
- `aliases` MUST be sorted lexicographically.
- `externalIds` MUST be sorted by `(namespace, type, value)` lexicographically.

**Alias intent (normative):**

`aliases` are intended as a low-churn set of alternate merchant names for interoperability and display. Implementations MAY include none, some, or many aliases, but verifiers MUST NOT require aliases to be present for correctness.

### Store location entry (leaf, optional)

```text
StoreLocationEntryV1 {
  storeLocationId: Identifier,      // canonical key (namespaced)
  storeId: Identifier,              // parent store identity
  geoRegion?: RegionCode,           // e.g. "US-CA" (ISO 3166-2 subdivision)
  cbsaCode?: CBSACode,              // e.g. "12420" (OMB CBSA metro area) — see DATA_STRUCTURES.md
  label?: String,                   // e.g. "Store #001"
  externalIds?: [ExternalIdV1]      // optional; sorted deterministically
}
```

> Implementations SHOULD avoid embedding precise addresses inside this portable registry unless there is a strong interop need; prefer standardized external IDs (e.g. GLN / Place IDs) plus coarse `geoRegion`.

## Inclusion proofs (portable)

This extension reuses the Merkle proof structure from `COMMITMENT_LAYER.md` (siblings are hashes; direction bits unnecessary due to sorted-pair hashing).

```text
RegistryInclusionProofV1 {
  registryId: Identifier,
  registryVersion: Version,
  leaf: StoreEntryV1 | StoreLocationEntryV1,
  leafHash: Hash,
  siblings: [Hash]
}
```

Verifiers MUST:

1. recompute `leafHash` using the Merkle leaf rule and reject if mismatched, and
2. walk `siblings` using the Merkle internal hash rule, and
3. compare to `entriesRoot` / `locationEntriesRoot` from a signature-verified snapshot token.

## Using the registry in ZK predicates (non-normative guidance)

- Prefer predicates over `storeHash` / `storeLocationHash` rather than raw names.
- For “brand campaigns”, prefer `storeHash ∈ allowedStoresRoot` (set-membership) so campaign rules can reference a stable allowlist root.
- If location-level proofs are needed, use `storeLocationHash` or a set root of permitted locations (region/campaign-specific).

## Security & evolution

- This is a **non-core extension**. Core token verification MUST NOT depend on this registry.
- Unknown `schemaVersion` MUST be rejected for portable verification of this extension artifact (see `PROTOCOL_EVOLUTION.md`).
- Changes that alter Merkle hashing rules, leaf field semantics, or hash preimages require a new `schemaVersion`.

## Example (non-normative)

- Example store list: `protocol/examples/store-registry/v1/stores.json`
- Example location list: `protocol/examples/store-registry/v1/locations.json`
