# Crinkl Protocol v1.0.0-rc.5 Release Snapshot

Status: `RELEASE_CANDIDATE_NOT_PUBLISHED`

The exact finalization transitions, authorization, pre-tag gates, post-tag
gates, and rollback rules are machine-readable in
[`finalization.json`](finalization.json).

## Version surfaces

- Public repository release: `1.0.0-rc.5` candidate.
- Conformance suite version: `3`.
- Default Crinkl Platform binding `protocolVersion`: `1.0.0-rc.2`.
- Spend Attestation Token V2 embedded `protocolVersion`: `1.0.0-rc.1`.
- Supported wire protocol versions: `1.0.0-rc.1` and `1.0.0-rc.2`.

These values are intentionally distinct. The candidate does not relabel or
rewrite signed native wire objects. The released `v1.0.0-rc.4` tag and its
snapshot remain immutable.

## Candidate W3C profile

`credential.spendAttestation.vcdm2.eddsaJcs2022` is an optional, opt-in W3C
VC 2.0 Spend Attestation wire form issued alongside an independently
verifiable native token. Suite version 3 executes its manifest-bound fixture
harness. The profile remains candidate-only and makes no claim of complete
official-suite conformance, peer interoperability, generic VC/VP API,
endpoint operation, runtime, QA completion, release, or production.

The profile pins adopted source from `crinkl-protocol` commit
`ae6382f1ed11b88f9bbfdcc4ef12119647cc7698`, including 32 applicable official
self-cell rows passed and 8 pending profile-optional or upstream-skipped rows.

## Authority boundary

This candidate does not activate any Crinkl service or client. DID, immutable
context, signed status-list, and refresh endpoints remain launch blockers;
runtime adoption, QA, and production authority are separately governed.
