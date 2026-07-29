---
status: draft
layer: conformance
version: v1
normative: true
---

# GMV Price Aggregate Verification

Normative verifier behavior for `GmvPriceAggregateV1` (format: `../02-proof-lifecycle/gmv-price-aggregate-v1.md`).

Two independent verifier implementations exist: the producer-side verifier run by proof validators, and a platform-side seal-admission verifier. **The producer-side (validator) semantics are normative.** Where the implementations are known to diverge, conformance is judged against the behavior specified here, which follows the producer side.

## Inputs

| Input | Meaning |
|---|---|
| `aggregate` | The candidate `GmvPriceAggregateV1` object (untrusted). |
| `resolvedArtifactContentHash` | Content hash the caller independently resolved for the aggregate artifact. |
| `resolvedSampleSetRoot` | Sample-set root the caller independently resolved. |
| `registry` | Registry key view derived from the authenticated registry snapshot: `{registrySequence, registryHash, keys[]}` with rows `(validatorId, keyId, publicKey, active)`. |
| `expectedCanonicalArtifactByteLength` | OPTIONAL expected canonical byte length (present when a candidate binds one). |

The registry view MUST be derived only from a registry snapshot whose authority signature was verified, and whose paired committee assignment was verified, before aggregate verification begins. Authenticating that evidence is the caller's responsibility; this page specifies verification of the aggregate against an already-authenticated view.

## Error Model

A verification failure carries a semantic code and a reason. Semantic codes:

| Code | Meaning |
|---|---|
| `GMV_PRICE_AGGREGATE_INVALID` | The aggregate itself is malformed or fails a check. |
| `GMV_PRICE_AGGREGATE_BINDING_MISMATCH` | A candidate or attempt does not bind to the aggregate correctly. |
| `GMV_PRICE_VALUE_MISMATCH` | A bound price value disagrees with the aggregate beyond tolerance. |

Operational conditions are not verification verdicts. When price evidence cannot be obtained at all, a validator MUST emit an explicit operational no-vote (`classification: OPERATIONAL`, `proofVote: NONE`) with one of:

- `GMV_PRICE_LOCAL_INPUT_UNAVAILABLE`
- `GMV_PRICE_AGGREGATE_QUORUM_UNAVAILABLE`
- `GMV_PRICE_EVIDENCE_UNAVAILABLE`

## Ordered Check Sequence

A conforming verifier MUST evaluate the checks in this order and fail closed at the first violation. Order is normative: it fixes which reason a given malformed input reports, and conformance vectors assert exact reasons.

1. **Schema.** Parse the aggregate: exact key sets on every object, literal fields, ASCII-only strings, identifier/hash/timestamp/base58/base64 formats, safe integers, tolerance-policy pairing, authority-boundary flags all `false`, 1–1024 signatures, canonicalizability. Any violation → `AGGREGATE_SCHEMA_INVALID`.
2. **Committee canonical order.** `selectedValidatorIds` strictly increasing under UTF-8 byte order → else `SELECTED_VALIDATORS_NON_CANONICAL`.
3. **Strict-BFT threshold.** `requiredSignatures == floor(2n/3) + 1` for committee size `n` → else `STRICT_BFT_THRESHOLD_MISMATCH`.
4. **Observation window.** `windowStart <= firstObservedAt <= lastObservedAt < windowEndExclusive` → else `OBSERVATION_WINDOW_INVALID`.
5. **Slot bounds.** `firstFinalizedSlot <= lastFinalizedSlot` → else `FINALIZED_SLOT_BOUNDS_INVALID`.
6. **Publication window.** `windowEndExclusive <= publishedAt <= windowEndExclusive + maximumPublicationDelaySeconds` (millisecond arithmetic MUST stay within safe-integer range) → else `PUBLICATION_WINDOW_INVALID`.
7. **Sample floor.** `validSampleCount >= contributingValidatorCount * minimumSamplesPerContributor` (product MUST be a safe integer) → else `SAMPLE_FLOOR_UNSATISFIED`.
8. **Sample root.** `sampleCommitment.sampleSetRoot == resolvedSampleSetRoot` → else `SAMPLE_ROOT_MISMATCH`.
9. **Aggregate hash.** Recompute the domain-separated hash of the unsigned aggregate; MUST equal the stored `aggregateHash` → else `AGGREGATE_HASH_MISMATCH`.
10. **Artifact content hash.** Recompute the content hash of the full canonical artifact; MUST equal `resolvedArtifactContentHash` → else `ARTIFACT_CONTENT_HASH_MISMATCH`.
11. **Artifact byte length.** When `expectedCanonicalArtifactByteLength` is provided, it MUST be a positive safe integer equal to the canonical byte length → else `ARTIFACT_BYTE_LENGTH_MISMATCH`.
12. **Registry binding.** `registry.registrySequence == committee.registrySequence` and `registry.registryHash == committee.registryHash` → else `REGISTRY_BINDING_MISMATCH`.
13. **Signature-list order.** Signature `validatorId`s strictly increasing under UTF-8 byte order. If out of order with all ids distinct → `SIGNATURE_ORDER_INVALID`; if any id repeats → `DUPLICATE_SIGNER`.
14. **Registry-view integrity.** For each registry row: `validatorId`/`keyId` MUST be identifiers and `publicKey` canonical 32-byte base64 → else `REGISTRY_BINDING_MISMATCH`. Rows MUST be unique on `(validatorId, keyId)` and unique on `(keyId, publicKey)` → else `DUPLICATE_SIGNING_KEY`.
15. **Per-signature checks**, in list order, each signature evaluated fully before the next:
    1. `validatorId` MUST be in `selectedValidatorIds` → else `UNSELECTED_SIGNER`.
    2. The signature's `(keyId, publicKey)` pair MUST NOT repeat within the signature list → else `DUPLICATE_SIGNING_KEY`.
    3. `(validatorId, keyId)` MUST resolve to a registry-view row that is active and whose `publicKey` equals the signature's `publicKey` → else `SIGNING_KEY_NOT_ACTIVE`.
    4. The Ed25519 signature MUST verify over the raw 32-byte digest decoded from the recomputed aggregate hash → else `SIGNATURE_INVALID`.
16. **Quorum.** The signature count MUST be at least `requiredSignatures` → else `SIGNATURE_QUORUM_UNSATISFIED`.

Signature verification precedes the quorum gate: a verifier MUST NOT report `SIGNATURE_QUORUM_UNSATISFIED` for a list containing an invalid signature — the invalid signature's own reason wins. `SIGNATURE_QUORUM_UNSATISFIED` means every present signature verified and there were too few of them.

On success the verifier reports the recomputed `aggregateHash`, `artifactContentHash`, canonical byte length, the distinct valid signature count, and the required-signature threshold.

## Candidate and Attempt Binding (Candidate V4)

When a day-seal candidate consumes the aggregate, the verifier MUST first extract the candidate's price projection (exact key sets on every price-bearing object; version pin `GmvPriceAggregateV1/1`; artifact reference type/version pins) — any violation → `CANDIDATE_V4_PROJECTION_INVALID` with code `GMV_PRICE_AGGREGATE_BINDING_MISMATCH`. It then runs the full aggregate sequence above with the candidate's declared artifact `byteLength` as `expectedCanonicalArtifactByteLength`, and finally checks the bindings, in order:

| # | Check | Reason on failure |
|---|---|---|
| 1 | Candidate artifact `contentHash`/`byteLength` equal resolved and recomputed values | `CANDIDATE_ARTIFACT_BINDING_MISMATCH` |
| 2 | Candidate `aggregateHash` equals the verified aggregate hash | `CANDIDATE_AGGREGATE_HASH_MISMATCH` |
| 3 | Candidate `networkId` equals aggregate `networkId` | `CANDIDATE_NETWORK_MISMATCH` |
| 4 | `sourceProfileHash` equal | `CANDIDATE_SOURCE_PROFILE_MISMATCH` |
| 5 | `aggregationPolicyHash` equal | `CANDIDATE_AGGREGATION_POLICY_MISMATCH` |
| 6 | `sampleSetRoot` equal | `CANDIDATE_SAMPLE_ROOT_MISMATCH` |
| 7 | `registrySequence` and `registryHash` equal | `CANDIDATE_REGISTRY_MISMATCH` |
| 8 | `assignmentId` and `assignmentHash` equal | `CANDIDATE_ASSIGNMENT_MISMATCH` |
| 9 | `windowStart` and `windowEndExclusive` equal | `CANDIDATE_WINDOW_MISMATCH` |
| 10 | `publishedAt` equal | `CANDIDATE_PUBLICATION_MISMATCH` |
| 11 | Candidate evidence price equals aggregate price exactly | `CANDIDATE_PRICE_VALUE_MISMATCH` (code `GMV_PRICE_VALUE_MISMATCH`) |
| 12 | Candidate statement price equals aggregate price, or differs within the aggregate's signed `toleranceBps` | `CANDIDATE_PRICE_VALUE_MISMATCH` (code `GMV_PRICE_VALUE_MISMATCH`) |
| 13 | Aggregate `windowStart` is not before the candidate day-window end | `CANDIDATE_PRICE_WINDOW_ORDER_MISMATCH` |

When a sealing attempt is supplied, additionally:

| Check | Reason on failure |
|---|---|
| Attempt declares the `GMV_PRICE_AGGREGATE_V1` evidence capability | `ATTEMPT_PRICE_CAPABILITY_MISSING` |
| Aggregate `publishedAt` is at or before attempt start | `CANDIDATE_PRICE_AFTER_ATTEMPT_START` |
| Attempt start minus `publishedAt` is at most `maximumPublicationDelaySeconds` | `CANDIDATE_PRICE_STALE_FOR_ATTEMPT` |

Binding-check reasons carry code `GMV_PRICE_AGGREGATE_BINDING_MISMATCH` except the two price-value reasons noted above, which carry `GMV_PRICE_VALUE_MISMATCH`.

## Failure-Reason Vocabulary

The complete normative reason vocabulary. A conforming verifier MUST NOT invent reasons outside this list.

Aggregate verification (code `GMV_PRICE_AGGREGATE_INVALID`):

`AGGREGATE_SCHEMA_INVALID` · `SELECTED_VALIDATORS_NON_CANONICAL` · `STRICT_BFT_THRESHOLD_MISMATCH` · `OBSERVATION_WINDOW_INVALID` · `FINALIZED_SLOT_BOUNDS_INVALID` · `PUBLICATION_WINDOW_INVALID` · `SAMPLE_FLOOR_UNSATISFIED` · `SAMPLE_ROOT_MISMATCH` · `AGGREGATE_HASH_MISMATCH` · `ARTIFACT_CONTENT_HASH_MISMATCH` · `ARTIFACT_BYTE_LENGTH_MISMATCH` · `REGISTRY_BINDING_MISMATCH` · `SIGNATURE_ORDER_INVALID` · `DUPLICATE_SIGNER` · `UNSELECTED_SIGNER` · `DUPLICATE_SIGNING_KEY` · `SIGNING_KEY_NOT_ACTIVE` · `SIGNATURE_INVALID` · `SIGNATURE_QUORUM_UNSATISFIED`

Candidate/attempt binding (code `GMV_PRICE_AGGREGATE_BINDING_MISMATCH` unless noted):

`CANDIDATE_V4_PROJECTION_INVALID` · `CANDIDATE_ARTIFACT_BINDING_MISMATCH` · `CANDIDATE_AGGREGATE_HASH_MISMATCH` · `CANDIDATE_NETWORK_MISMATCH` · `CANDIDATE_SOURCE_PROFILE_MISMATCH` · `CANDIDATE_AGGREGATION_POLICY_MISMATCH` · `CANDIDATE_SAMPLE_ROOT_MISMATCH` · `CANDIDATE_REGISTRY_MISMATCH` · `CANDIDATE_ASSIGNMENT_MISMATCH` · `CANDIDATE_WINDOW_MISMATCH` · `CANDIDATE_PUBLICATION_MISMATCH` · `CANDIDATE_PRICE_VALUE_MISMATCH` (code `GMV_PRICE_VALUE_MISMATCH`) · `CANDIDATE_PRICE_WINDOW_ORDER_MISMATCH` · `ATTEMPT_PRICE_CAPABILITY_MISSING` · `CANDIDATE_PRICE_AFTER_ATTEMPT_START` · `CANDIDATE_PRICE_STALE_FOR_ATTEMPT`

## Known Verifier Divergences

The producer-side semantics above are normative. Known platform-side deviations, listed so an implementer comparing verdicts does not mistake them for spec ambiguity:

- **Quorum-gate position.** The platform verifier evaluates the signature-count gate before the per-signature checks; the normative order verifies every signature first and applies `SIGNATURE_QUORUM_UNSATISFIED` last.
- **Contributor-count bound.** The platform verifier additionally rejects `contributingValidatorCount > selectedValidatorIds.length` (a reason outside this vocabulary). The normative verifier imposes no such bound.
- **Attempt-freshness reasons.** The platform collapses the two attempt-freshness failures into a single reason; the normative vocabulary distinguishes `CANDIDATE_PRICE_AFTER_ATTEMPT_START` from `CANDIDATE_PRICE_STALE_FOR_ATTEMPT`.
- **Registry `publicKey` sharing.** See the open hardening question below.

## Open Hardening Questions

1. **Shared `publicKey` across ACTIVE registry rows.** Should a registry view containing two ACTIVE rows that share a `publicKey` under different `keyId`s be rejected as `DUPLICATE_SIGNING_KEY`? The platform verifier currently rejects this shape; the producer-side verifier accepts it (it deduplicates only on `(validatorId, keyId)` and `(keyId, publicKey)`). The normative behavior is **accept**, pending an explicit rule decision. Rejecting would close a key-aliasing avenue (one physical key counted under multiple registrations) at the cost of forbidding legitimate key sharing across registrations.
