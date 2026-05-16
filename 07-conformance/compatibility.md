---
status: draft
layer: conformance
version: v1
normative: false
---

# Reference Implementation Notes

> Non-normative implementation guidance and notes.

## Producer/Consumer Compatibility

| Producer protocolVersion | Consumer supports | Expected behavior |
| --- | --- | --- |
| N (current) | N, N-1 | Accept and validate deterministically. |
| N-1 (previous) | N, N-1 | Accept; may log deprecation warnings but MUST remain readable. |
| < N-1 | N, N-1 | Accept only if explicitly within the published deprecation window; otherwise reject as VersionMismatch. |
| N+1 (future) | N, N-1 | Reject with VersionMismatch; future-version events MUST NOT be accepted without explicit feature negotiation. |

Compatibility matrices SHOULD be extended per release to enumerate schema-level requirements (required/optional fields, hashing/signature algorithms) and interop results across reference implementations.

## Rollout Guidance
- Stage new protocol versions behind feature flags; enable on a canary subset of producers before global rollout.
- Maintain dual-write or dual-hash capability during migrations where feasible to allow consumers to validate both old and new encodings.
- Prefer additive changes that remain readable by N-1 consumers; avoid destructive field renames or type changes during normal releases.

## Rollback Guidance
- Preserve the ability to emit `protocolVersion` N-1 during rollback windows; producers should retain the prior deterministic serialization paths until the rollout is declared stable.
- During rollback, consumers should keep accepting N and N-1, but write-path enforcement should revert to N-1 rules if emitting downgraded events.
- Document data re-ingestion or re-hashing steps required to realign ledgers when rolling back canonicalization or signature algorithm changes.

## Receipt Status Summaries (Non-normative)
Some implementations expose per-session receipt status lists for UI polling. Because storage backends may return an unordered set, clients SHOULD NOT infer "latest" from array order alone. A recommended pattern is to return a `best` summary object computed deterministically from the set (e.g., best store/date/total by confidence + updatedAt, plus aggregated canSubmit/softReason). This summary is operational UI state and MUST NOT be treated as protocol truth.
