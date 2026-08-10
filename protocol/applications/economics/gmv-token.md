---
status: draft
layer: reward-settlement
version: v1
normative: true
---

# GMV Token

Verified GMV Tokens are downstream aggregate accounting artifacts derived from Spend Attestations. They are not Core spend proof.

## Verified GMV Token

> “Aggregate economic throughput must be provable, append-only, correction-aware, and privacy-preserving.”
**Identity prohibition:** Per the Identity Minimization Invariant (../protocol/purpose/what-crinkl-proves.md), Verified GMV Tokens MUST NOT include wallet identifiers, recipient references, or any data that would enable reconstruction of per-user spend patterns. Spends are referenced only via `spendId` within the committed `spendHeadSetRoot`; aggregates expose only totals and Merkle roots.

### Explicit non-claims (normative)

A Verified GMV Token:
- does NOT claim “all receipts are valid forever”; it is an **as-of snapshot** that may be superseded by later tokens for the same window;
- does NOT imply rewards were issued or economically backed unless `issuedGMV` and/or explicit commitment/backing artifacts are provided;
- does NOT reveal wallet ownership or user identity; per-spend inclusion proofs do not imply ownership.
### Primary Use Case: Brand Partnership Verification (non-normative)

GMV tokens enable brands to verify Crinkl's aggregate audience reach and spending power (without exposing individual user transactions) when negotiating reward partnerships.

**The negotiation problem:** Brands need verifiable proof of audience size before committing marketing budget.

Brands allocate 15–25% of revenue to customer acquisition. Crinkl aggregates users actively spending in brand-relevant categories. GMV tokens allow brands to audit claimed audience size and spend volume before redirecting marketing budget to user rewards.

This is analogous to Nielsen ratings (prove audience size for TV ad negotiations) or credit scores (prove creditworthiness for lending decisions)—but with cryptographic non-repudiation and privacy preservation.

### Dispute Resolution (non-normative)

If a brand disputes a published GMV figure, the issuer can provide:

1. The underlying `spendHeadSetRoot` leaf set (aggregate data, no receipt images)
2. Per-spend inclusion proofs for a sample of spends
3. Audit bundles (if the brand has appropriate data access agreements)

This allows third-party auditors to verify GMV calculations without compromising user privacy or requiring full database access.

### GMV Commitments (non-normative)

Crinkl treats GMV as an append-only aggregate claim derived from canonical spend attestations, not a trusted database export.

GMV commitments preserve user privacy by committing only to aggregate totals and Merkle roots of spend heads, without exposing receipt data, merchants, or individual transactions. Corrections are expressed via new GMV commitment artifacts rather than mutation of historical records.

### How a Receipt Becomes Verified GMV

A receipt contributes to Verified GMV only after **Hard Verification** (or subsequent **Correction**) produces a finalized spend (see ../../core/verification-state.md)—a canonical spend record with total amount, currency, and timestamp. Rewards and economic backing (e.g., BTC moving) are separate: they may happen around the same time, but they do not define Verified GMV.

Verified GMV is included when an issuer **publishes a Verified GMV Token** for a specific UTC day. To compute it, the issuer picks an “as-of” time (`asOf.computedAt`), selects all finalized spends whose finalized timestamp falls in that UTC day and are not `INVALIDATED`, and sums their totals into `verifiedGMV`.

The token contains no receipt images/text; instead it includes a single hash (`asOf.spendHeadSetRoot`) that acts like a fingerprint of “the set of spends that were counted”, so the issuer can later give a user a small proof that their spend was included without publishing every spend or sharing receipts (see per-spend inclusion proofs below).

If later corrections change a spend’s finalized timestamp or total, the issuer publishes a newer token for that same day rather than revising history.

### Claim

The claim is:

- the **Verified GMV** for a fixed UTC day (sum of finalized spend totals as-of a specific computation time), and
- optionally the **Issued/Rewarded GMV** (sum over spends for which rewards were issued). **Critical:** Verified GMV and Issued GMV are independent—spend corrections do not trigger reward clawbacks.

Every GMV token MUST be explicit about its **window** and its **as-of** semantics.

### Portable shape (normative)

```text
VerifiedGmvTokenV1 {
  tokenType: "VERIFIED_GMV",
  schemaVersion: 2,

  window: { type: "UTC_DAY", date: DateISO }, // YYYY-MM-DD

  anchoringTier?: "SIGNED" | "ANCHORED", // default: "SIGNED" if `anchoring` absent, "ANCHORED" if present

  asOf: {
    computedAt: TimestampISO,
    spendHeadSetRoot: "sha256:" + Hash,
    spendRule: "CANONICAL_HEAD_ASOF"
  },

  verifiedGMV: { currency: CurrencyCode, totalCents: Amount, spendCount: Integer },

  issuedGMV?: {
    currency: CurrencyCode,
    totalCents: Amount,
    rewardedSpendCount: Integer,
    policyVersion?: String
  },

  linkage?: { rewardBatchRoots: [Hash] },

  anchoring?: { chainId: String, txRef: String },

  prevGMVTokenHash?: "sha256:" + Hash,

  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

### Interpretation rules (normative)

#### As-of anchor and supersession

- `asOf.computedAt` is the as-of anchor: the issuer asserts the spend set and aggregate values are computed from canonical heads **as they existed at** `asOf.computedAt`.
- Supersession preference over a set of candidate tokens for the same `(window.type, window.date)` is deterministic:
  1) prefer greater `asOf.computedAt`; if tied,
  2) prefer the token with lexicographically greatest `signatures.tokenHash` (tie-break only; should be rare).
- Verifiers MAY additionally enforce a local freshness policy (e.g., reject tokens older than X days) but that is an acceptance policy, not part of cryptographic validity.

#### Bucketing and time semantics

- `window` is defined in UTC (`window.type = UTC_DAY`).
- A spend is included in a GMV window according to the canonical spend attestation timestamp produced by the spend-stream state machine (../../core/verification-state.md), not raw receipt-local timestamps.
- If the canonical timestamp for a spend changes due to correction, the spend MAY move between windows in subsequent GMV tokens; this is expressed only by publishing new GMV commitment artifacts.

#### `issuedGMV` semantics

- If `issuedGMV` is present, the issuer asserts those values are computed for the window as-of `asOf.computedAt`.
- If `issuedGMV` is absent, the issuer is not asserting issued/rewarded GMV for that window (unknown / not computed / intentionally omitted).
- To assert that no rewards were issued for a window, issuers SHOULD include `issuedGMV` with `totalCents = "0"` and `rewardedSpendCount = 0`.

#### Supersession and corrections for the same window

Issuers MAY publish multiple Verified GMV Tokens for the same `window.date` over time.

- Later tokens for the same window are interpreted as newer **as-of snapshots**, not mutations of history.
- If the issuer knows the immediately prior published GMV token for the same window, it SHOULD set `prevGMVTokenHash` to form a chain.
- Verifiers SHOULD select the token with the greatest `asOf.computedAt` that they trust, and MAY additionally verify `prevGMVTokenHash` continuity for audit.

Auditors can compute deltas between two snapshots for the same window as:

- `verifiedGMV.totalCentsDelta = BigInt(verifiedGMV.totalCents(new)) - BigInt(verifiedGMV.totalCents(old))`
- `verifiedGMV.spendCountDelta = verifiedGMV.spendCount(new) - verifiedGMV.spendCount(old)`

> Optional extension: an issuer MAY also publish an explicit delta token type (e.g., `VERIFIED_GMV_DELTA`) for audit-friendly “GMV went down because spends were invalidated” narratives. This is non-normative and not required for verifiers.

### spendHeadSetRoot construction (normative)

To commit to "which spends were counted" and "which finalized spend head states were used" **while preserving user privacy** (no receipt images, merchant names, or transaction details), issuers MUST compute `spendHeadSetRoot` as a Merkle root over per-spend leaves.

For each included `spendId`, the issuer MUST construct a leaf object:

```text
SpendHeadLeafV1 {
  spendId: Identifier,
  canonicalHeadEventHash: Hash,
  totalCents: Amount,
  currency: CurrencyCode,
  status: "HARD_VERIFIED" | "CORRECTED",
  geoRegion?: RegionCode,              // OPTIONAL ISO 3166-2 subdivision (e.g., "US-CA")
  cbsaCode?: CBSACode                  // OPTIONAL metro area code (e.g., "12420")
}
```

Leaf bytes MUST be `RFC8785_canonicalize(SpendHeadLeafV1)` and leaf hash MUST be `SHA256(0x00 || leafBytes)`.

Internal node hash MUST be `SHA256(0x01 || sort(left,right))` (domain-separated, sorted-pair Merkle tree) and leaves MUST be sorted deterministically by `spendId` before tree construction.

**Duplicate rule (normative):** each `spendId` MUST appear at most once in the leaf set. Duplicate `spendId` values MUST be rejected by the issuer; verifiers/auditors MUST treat a leaf set containing duplicates as invalid.

> This matches the Commitment Layer Merkle hashing conventions (0x00 leaves / 0x01 internal) and is intentionally chain-agnostic.

### Verification procedure (normative)

To verify a Verified GMV Token, a verifier MUST:

1. Verify required fields and supported versions (`schemaVersion`); reject on unsupported versions.
2. Recompute `tokenHash` from the unsigned token and verify `signatures.signature` against `signatures.publicKey`.
3. Verify that `signatures.publicKey` is an authorized issuer key for `signatures.issuedBy` under the applicable trust root mapping (Authority Registry or configured issuer set); reject if unauthorized (see `../protocol/purpose/threat-model.md#trust-roots`).
4. Apply local acceptance policy:
   - treat `verifiedGMV` as an "as-of" snapshot that may be superseded by later GMV tokens for the same window, and
   - treat `issuedGMV` (when present) as a statement about issued rewards, not about spend attestation.

If an issuer provides the underlying leaf set and optional inclusion proofs out-of-band, a verifier MAY recompute `spendHeadSetRoot` and audit which spends were counted.

### Optional: Per-spend inclusion proof (normative)

An issuer MAY provide a per-spend inclusion proof that allows a holder of a `spendId` (typically the user who uploaded the receipt) to verify that their spend was included in a specific Verified GMV Token, without requiring the issuer to publish the full set of spends.

**Semantics (normative):** this proof asserts only **membership** of `spendLeaf` under `asOf.spendHeadSetRoot` for the referenced GMV token. It does not assert ownership, identity, or reward eligibility.

#### Proof shape (normative)

```text
VerifiedGmvInclusionProofV1 {
  schemaVersion: 1,
  gmvTokenHash: "sha256:" + Hash,
  spendLeaf: SpendHeadLeafV1,
  leafHash: Hash,
  siblings: [Hash] // sibling hashes from leaf to `asOf.spendHeadSetRoot`
}
```

#### Verification (normative)

To verify a `VerifiedGmvInclusionProofV1`, a verifier MUST:

1. Fetch the referenced Verified GMV Token and verify its signature, and verify that its `signatures.tokenHash` equals `gmvTokenHash`.
2. Recompute `leafHash = SHA256(0x00 || RFC8785_canonicalize(spendLeaf))` and verify it equals `leafHash`.
3. Starting from `leafHash`, iteratively compute the parent hash with each element of `siblings` using `SHA256(0x01 || sort(left,right))` until a candidate root is produced, and verify it equals the token’s `asOf.spendHeadSetRoot`.

> A user can additionally check that `spendLeaf` matches the spend they expect (same `spendId` and finalized total/currency/status) using their Spend Attestation Token.

### Optional: Scoped inclusion attestation (non-transferability) (normative)

If a verifier needs a **non-transferable** inclusion artifact (e.g., a brand requests “prove inclusion for this request scope”), the issuer MAY provide a signed, scope-bound attestation.

This is distinct from Merkle membership: it binds inclusion to a `scopeId` so the artifact cannot be reused across scopes without detection.

```text
VerifiedGmvInclusionAttestationV1 {
  schemaVersion: 1,
  gmvTokenHash: "sha256:" + Hash,
  scopeId: "sha256:" + Hash,
  spendId: Identifier,
  attestedAt: TimestampISO,
  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

To verify a `VerifiedGmvInclusionAttestationV1`, a verifier MUST:
1. Verify the referenced Verified GMV Token and verify `gmvTokenHash` matches its `signatures.tokenHash`.
2. Recompute the attestation `tokenHash` and verify its signature, and verify issuer authorization for `issuedBy/publicKey`.
3. Verify the `scopeId` matches the verifier's expected scope for the request.
