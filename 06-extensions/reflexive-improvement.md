---
status: experimental
layer: extension
version: v1
normative: true
---

# Reflexive Improvement

This document defines normative requirements for reflexive improvement capability in the Crinkl Protocol. The protocol MUST enable verification pipelines to improve over time without requiring protocol changes.

Terms are defined in ../08-governance/glossary.md and used normatively throughout this specification.

## Scope

Reflexive improvement refers to system behaviors where each successful verification contributes to future verification accuracy, coverage, or cost efficiency. This includes:

- Store taxonomy expansion from OCR extraction patterns
- Soft → Hard verification calibration
- Correction-driven model improvement
- Cost amortization at scale

## Global Invariants

The protocol MUST enable reflexive improvement without requiring protocol changes.

Reflexive improvement MUST NOT violate determinism, auditability, or append-only semantics.

**Final invariant:** Reflexive improvement is optional, but reflexive improvement capability is mandatory.

---

## Normative Requirements

### 1. Store Taxonomy Expansion

The protocol MUST allow unknown or unmatched store identifiers to be verified without rejection.

The protocol MUST support alias expansion via a versioned, signed store registry.

The protocol MUST preserve validity of historical verifications after taxonomy updates.

The protocol MUST bind each hard verification to the active store registry version.

The protocol MUST allow retroactive reinterpretation of historical spends via correction events, not mutation.

### 2. Soft → Hard Calibration

The protocol MUST support a two-tier verification model where provisional predictions can be compared against canonical outcomes.

The protocol MUST preserve both soft-extracted and hard-extracted fields for deterministic comparison.

The protocol MUST treat hard verification as the ground truth for calibration purposes.

The protocol MUST allow soft verification policies to evolve without invalidating past verifications.

The protocol MUST allow verification rule evolution to be tracked via explicit versioning.

### 3. Policy Injection vs Extraction Separation

The protocol MUST distinguish policy-injected fields from extraction-derived fields.

The protocol MUST prevent policy-layer assumptions from overwriting extracted ground truth.

The protocol MUST make mismatches between policy-injected and extracted fields observable.

The protocol MUST allow these mismatches to be used for heuristic refinement and quality assessment.

### 4. Correction-Driven Learning

The protocol MUST represent corrections as append-only events.

The protocol MUST explicitly identify which fields were corrected.

The protocol MUST preserve the original verification for auditability.

The protocol MUST bind corrections to the verification rules that detected the error.

The protocol MUST allow correction frequency to be measured over time.

### 5. Verified Data as Training Substrate

The protocol MUST allow verified outputs to function as labeled ground truth.

The protocol MUST maintain a deterministic linkage between source images and canonical outputs.

The protocol MUST ensure training data can be derived without protocol-specific heuristics.

The protocol MUST allow model upgrades to occur under new verification versions.

The protocol MUST preserve interpretability across model upgrades.

### 6. Cost Amortization via Batching

The protocol MUST support batch commitments with constant on-chain cost.

The protocol MUST expose batch size and leaf count as observable metadata.

The protocol MUST allow operators to tune batch size without protocol changes.

The protocol MUST ensure per-verification cost decreases with scale.

The protocol MUST allow cost savings to be reinvested into verification quality.

### 7. Risk Flag Feedback

The protocol MUST support extensible risk flag emission.

The protocol MUST propagate risk flags through the verification pipeline unchanged.

The protocol MUST allow invalidation reasons to be explicitly labeled.

The protocol MUST allow reward policy to gate on risk flags without affecting verification validity.

The protocol MUST allow correlation analysis between risk flags and invalidations.

### 8. Versioning & Measurement

The protocol MUST version verification rules, models, and normalization logic explicitly.

The protocol MUST allow performance metrics to be segmented by verification version.

The protocol MUST preserve comparability across versions.

The protocol MUST make improvement measurable over time.

### 9. Observability Requirements

The protocol MUST emit sufficient data to compute accuracy, correction rate, and invalidation rate.

The protocol MUST make soft–hard deltas observable.

The protocol MUST allow replay of historical data under newer analysis logic without altering past outcomes.

### 10. Non-Requirements (Explicit)

The protocol MUST NOT require reflexive improvement to function correctly.

The protocol MUST NOT mandate specific models, heuristics, or training methods.

The protocol MUST NOT encode operator-specific learning logic into protocol rules.

---

## Protocol Primitives Supporting Reflexive Improvement

| Primitive | Location | Improvement It Enables |
|-----------|----------|----------------------|
| `verificationVersion` | ../02-proof-lifecycle/ingestion.md | Rule evolution without breaking old verifications |
| `SPEND_CORRECTED` | ../01-core/spend-event.md | Labeled error examples for model training |
| `StoreEntryV1.aliases` | store-registry.md | Taxonomy expansion from OCR mismatches |
| `softExtractedFields` | ../02-proof-lifecycle/ingestion.md | Soft vs hard comparison for calibration |
| `riskFlags` | ../01-core/canonicalization.md | Predictive signal for deferral/review |
| Merkle batching | ../05-reward-and-settlement/settlement-bindings.md | Cost amortization at scale |
| Append-only event stream | ../01-core/verification-state.md | Replayable labeled dataset |

---

## Mechanism Details

### Store Taxonomy Expansion

```
OCR extracts raw store name
        ↓
Normalization attempts taxonomy match
        ↓
Unknown storeId verified (not rejected)
        ↓
Pattern analysis identifies alias candidate
        ↓
Store Registry updated with new alias
        ↓
Future receipts match directly
        ↓
New StoreRegistrySnapshotToken issued
```

**Protocol support:**
- `StoreEntryV1.aliases` array captures alternate names
- `registryVersion` increments monotonically; old snapshots remain valid
- `SPEND_CORRECTED` can retroactively apply new taxonomy to old spends

### Soft → Hard Calibration

```
Soft verification predicts fields (provisional)
        ↓
Hard verification produces canonical outcome
        ↓
Compare: soft prediction vs hard extraction
        ↓
Analyze mismatches for systematic patterns
        ↓
Update soft verification thresholds
        ↓
Future soft verification more accurate
```

**Policy-injected vs extracted fields:**

Soft verification policy MAY inject a `storeId` based on heuristics (session context, user history, brand campaign). Hard verification is responsible for extracting the actual store name from the receipt image.

Hard verification OCR is generally accurate at store name extraction unless the receipt image is naturally poor quality (faded thermal paper, motion blur, partial crop). This makes hard-extracted `storeId` a reliable ground truth signal for:

1. **Policy calibration** — When policy-injected ≠ hard-extracted, investigate the mismatch source
2. **Image quality detection** — When extraction fails, flag as `riskFlags = ["low_image_quality"]`
3. **Alias discovery** — When policy says "Example Merchant" and OCR extracts "EXMPL MERCH", candidate alias identified

### Correction-Driven Learning

```
Hard verification produces canonical Spend
        ↓
Later review detects error
        ↓
SPEND_CORRECTED emitted with correctedFields
        ↓
Correction patterns analyzed
        ↓
OCR model / normalization rules updated
        ↓
Future receipts verified correctly first time
```

**Protocol support:**
- `correctedFields` explicitly identifies what changed
- `verificationVersion` binds corrections to detection rules
- Original events preserved for audit

### Cost Amortization

```
More spends → more rewards → larger batches
        ↓
Fixed on-chain cost amortized across recipients
        ↓
Per-verification cost decreases
        ↓
Economic headroom for verification investment
```

**Protocol support:**
- Merkle root commitment is O(1) regardless of leaf count
- `leafCount` in `REWARD_BATCH_COMMITTED` tracks batch size

### Risk Flag Feedback

```
Soft verification emits riskFlags
        ↓
Hard verification confirms or invalidates
        ↓
Analyze: which flags predict invalidation?
        ↓
Update soft verification flag emission
        ↓
Fewer false-positive provisional rewards
```

**Protocol support:**
- `riskFlags` is extensible (operator-defined vocabulary)
- Flags flow through pipeline unchanged
- Reward policy can gate on flags without affecting verification validity

---

## Relationship to Other Specifications

- **../02-proof-lifecycle/ingestion.md** — Defines two-tier verification, `verificationVersion`, normalization rules
- **../01-core/spend-event.md** — Defines `SPEND_CORRECTED`, `correctedFields`, append-only semantics
- **store-registry.md** — Defines alias expansion, `StoreEntryV1`, registry versioning
- **../01-core/canonicalization.md** — Defines `riskFlags`, field schemas
- **../05-reward-and-settlement/settlement-bindings.md** — Defines Merkle batching, `leafCount`
- **../01-core/verification-state.md** — Defines append-only event stream, replay semantics
