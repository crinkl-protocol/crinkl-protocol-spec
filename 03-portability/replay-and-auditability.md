---
status: draft
layer: portability
version: v1
normative: true
---

# Replay and Auditability

Crinkl proof is replayable because spend truth is derived from append-only, hash-linked event streams. A verifier can reconstruct state from signed events and can validate portable artifacts from their canonical bytes and proof material.

## Replay

Spend-stream replay follows `prevHash` ordering. Forks, gaps, unsupported versions, malformed payloads, or invalid signatures invalidate or make the stream indeterminate under the verification rules.

## Portable Audit

Portable Spend Attestation Tokens are snapshots of a canonical spend head. They do not require private database access for baseline verification. Deep audit can use event fragments or audit bundles, but those bundles are not portable proof and may contain internal wallet-scoped or ingestion-scoped material.

## Freshness

A signed token can be cryptographically valid while stale. Freshness is an acceptance-policy decision unless the artifact carries enough public spend-stream or system-stream evidence to prove latest-head status.
