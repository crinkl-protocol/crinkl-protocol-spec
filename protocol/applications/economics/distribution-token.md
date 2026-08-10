---
status: draft
layer: reward-settlement
version: v1
normative: true
---

# Distribution Token

Verified Spend Distribution Tokens are downstream aggregate analytics artifacts derived from the same spend-head snapshot model as Verified GMV. They are not Core spend proof.

## Verified Spend Distribution Token

The Verified Spend Distribution Token extends the GMV primitive with **dimensional breakdowns** — the same aggregate spend data sliced by geographic region and store category. It shares the same `spendHeadSetRoot`, spend filtering, and as-of semantics as the Verified GMV Token for the same window.

**Identity prohibition:** Like Verified GMV Tokens, Verified Spend Distribution Tokens MUST NOT include wallet identifiers, recipient references, or any data that would enable reconstruction of per-user spend patterns. Only aggregate counts and totals per dimension are exposed.

### Explicit non-claims (normative)

A Verified Spend Distribution Token:
- does NOT claim individual spend details; it is an aggregate snapshot by dimension;
- does NOT reveal wallet ownership or user identity;
- does NOT imply rewards were issued unless `issuedDistribution` is present;
- does NOT guarantee completeness of category or region resolution (best-effort enrichment is expected).

### Portable shape (normative)

```text
VerifiedSpendDistributionTokenV1 {
  tokenType: "VERIFIED_SPEND_DISTRIBUTION",
  schemaVersion: 2,

  window: { type: "UTC_DAY", date: DateISO },

  asOf: {
    computedAt: TimestampISO,
    spendHeadSetRoot: "sha256:" + Hash,    // MUST equal the GMV token's spendHeadSetRoot for the same window+computedAt
    spendRule: "CANONICAL_HEAD_ASOF"
  },

  verifiedDistribution: {
    currency: CurrencyCode,
    totalCents: Amount,
    spendCount: Integer,
    byCategory: Record<String, { spendCount: Integer, totalCents: Amount }>,
    byGeoRegion?: Record<RegionCode, { spendCount: Integer, totalCents: Amount }>
  },

  issuedDistribution?: {
    currency: CurrencyCode,
    totalCents: Amount,
    rewardedSpendCount: Integer,
    byCategory: Record<String, { spendCount: Integer, totalCents: Amount }>,
    byGeoRegion?: Record<RegionCode, { spendCount: Integer, totalCents: Amount }>,
    policyVersion?: String
  },

  prevDistributionTokenHash?: "sha256:" + Hash,

  signatures: { issuedBy: AuthorityId, publicKey: Base64, tokenHash: Hash, signature: Base64 }
}
```

### Derivation rules (normative)

- `asOf.spendHeadSetRoot` MUST be computed identically to the Verified GMV Token for the same window and as-of time. Implementations SHOULD derive both tokens from the same snapshot computation.
- `byCategory` keys MUST be canonical store category identifiers as defined by the store registry (see `../06-extensions/store-registry.md`). Spends whose store cannot be resolved to a category MUST be bucketed under the key `"Unknown"`.
- `byGeoRegion` keys MUST be canonical region bucket values derived from the canonical spend head. Implementations MAY use ISO 3166-2 subdivisions, ISO 3166-1 alpha-2 country codes, CBSA numeric codes, or non-metro fallbacks when those are the canonical region buckets emitted by the verifier. Spends with no resolvable geographic data MUST be bucketed under `"Unknown"`.
- `byCategory` and `byGeoRegion` record keys MUST be sorted lexicographically (UTF-8 byte order) for canonical serialization.
- `verifiedDistribution.totalCents` MUST equal the sum of all `byCategory` values' `totalCents`. The same holds for `spendCount`.
- If `issuedDistribution` is present, it follows the same rules scoped to rewarded spends only.
- `prevDistributionTokenHash`, when present, MUST reference the `tokenHash` of the immediately prior published distribution token for the same `(window.type, window.date)`.

### Privacy floor (implementation guidance, non-normative)

Implementations SHOULD define a minimum-spend-count threshold below which a `byGeoRegion` bucket is rolled up into a coarser grouping (e.g., state-level or `"Unknown"`) to prevent re-identification via small-population geographic areas cross-tabulated with category and time. The specific threshold is an implementation/policy decision.

### Supersession

Distribution tokens follow the same supersession rules as Verified GMV Tokens: scope key is `(window.type, window.date)`, preference by greatest `asOf.computedAt`.

### Verification procedure (normative)

To verify a Verified Spend Distribution Token, a verifier MUST:

1. Verify required fields and supported versions (`schemaVersion`); reject on unsupported versions.
2. Recompute `tokenHash` from the unsigned token and verify `signatures.signature` against `signatures.publicKey`.
3. Verify that `signatures.publicKey` is an authorized issuer key for `signatures.issuedBy` under the applicable trust root mapping; reject if unauthorized.
4. Apply local acceptance policy (treat as an as-of snapshot that may be superseded).
