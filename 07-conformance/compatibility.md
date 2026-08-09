---
status: draft
layer: conformance
version: v1
normative: false
---

# Reference Implementation Notes

> Non-normative implementation guidance and notes.

## Compatibility and release-state record

| Surface | Exact supported or observed state | Compatibility / authority boundary |
| --- | --- | --- |
| Public specification releases | `v1.0.0-rc.3` and `v1.0.0-rc.4` are released immutable tags; `v1.0.0-rc.4` is the latest released public package. | Resolve a release by its tag, exact commit/tree, and release-manifest digest. |
| `v1.0.0-rc.5` source candidate | Reviewed only at `81237937833ab32e5ce92d3b5ceed72854baecef` / tree `9121bdfbfc428f73557e993f1bd6e295ba733a12`; it is not published or released. | Later source, including this branch, is unassigned and cannot inherit that review. |
| Embedded wire and binding history | `1.0.0-rc.1` and `1.0.0-rc.2` are supported embedded wire values; `1.0.0-rc.2` is not an observed public tag or public release. | A verifier accepts only its explicitly supported wire values; a wire label does not classify a public release. |
| Spend Attestation Token schemas | `SpendAttestationTokenV1` and `SpendAttestationTokenV2` remain valid supported sibling schemas. | V2 `holderBinding` is OPTIONAL; a V2 token without it remains valid, but has no portable holder-control proof. |
| Holder-binding profile | `token.spendAttestation.holderBinding.v2` is released as a profile with separately governed runtime support. | Profile release does not assert runtime, deployment, or a protocol-wide issuance choice. |
| Token issuance | There is **no protocol-wide token issuance default**. | Each profile or runtime explicitly selects its issuance behavior; availability of V2 never silently selects it. |
| Maturity and runtime | Source review, adopted-main containment, public release, runtime support, and deployment are separate evidence-bearing states. | No source candidate or released document alone activates runtime or production behavior. |

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
