---
status: draft
layer: lifecycle
version: v1
normative: true
---

# Soft Verification

Low-latency preliminary assessment producing provisional values for user feedback and optional provisional rewards. Does not produce canonical Spend records.

**Input:** ReceiptUpload
**Output:** SoftSpend

| Field | Description |
|-------|-------------|
| spendId | Stable identifier (same across Soft → Hard transitions) |
| softVerificationStatus | `SOFT_VERIFIED` \| `REJECTED` \| `PENDING` (see `../01-core/canonicalization.md`) |
| softExtractedFields | Approximate values (store, total, timestamp) |
| riskFlags | Optional diagnostic indicators |

**Invariant:** SoftSpend values MAY be approximate but MUST NOT be contradictory. If Hard Verification produces materially different values, the delta MUST be explainable as an extraction refinement, not arbitrary reassignment.

*A SoftSpend field is non-contradictory if the Hard-verified value can be derived via refinement (e.g., precision increase, store disambiguation) rather than categorical reversal (e.g., different merchant class, different currency).*

**Duplicate suspicion (normative):** If duplicate suspicion exists at Hard Verification time (e.g., `riskFlags` contains `potential_duplicate`), the verifier MUST NOT emit `SPEND_HARD_VERIFIED` or a spend token. The verifier MUST emit either:
- `SPEND_INVALIDATED` with `reason` indicating duplicate suspicion (e.g., `POTENTIAL_DUPLICATE`), or
- `SPEND_CORRECTED` if the spend is being explicitly linked to a canonical prior spend (duplicate resolution).

Implementations MAY surface `potential_duplicate` earlier in `SPEND_SOFT_VERIFIED` for UX and reward gating, but the hard-verification outcome MUST reflect the duplicate finding (invalidation/correction, not acceptance).
