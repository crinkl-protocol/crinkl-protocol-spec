# Protocol Governance

This document declares **what is authoritative** in the Crinkl protocol ecosystem and **what CI must enforce** to prevent drift, ambiguity, and “spec-by-accident”.

## Goals

- **Single intent**: everyone can answer “what must never break?” without guesswork.
- **Determinism**: identical inputs produce identical bytes/hashes across implementations.
- **Non-drift**: docs, schemas, bindings, and codegen stay mechanically aligned.
- **Minimal surface area**: one way to represent things; derived artifacts are derived.

## Authority Hierarchy (Highest → Lowest)

When two artifacts disagree, the higher authority wins and the lower one is considered a bug.

1. **External cryptographic/serialization standards**
   - RFC 8785 (JCS), SHA-256, Ed25519 (RFC 8032), ISO 8601 / RFC 3339 timestamps.
2. **Normative protocol spec**
   - `crinkl-protocol/protocol/*.md`
   - Defines semantics, invariants, canonicalization rules, hashing/signing rules, state machines.
3. **Formal model (invariants check)**
   - `crinkl-protocol/formal/*`
   - Not a replacement for the spec; it is an executable consistency check of invariants.
   - If the model contradicts the spec, either the model is wrong or the spec is underspecified.
4. **Bindings + machine-readable schemas (wire/transport contracts)**
   - `crinkl-protocol/bindings/**`
   - JSON Schemas referenced by bindings define event *shape* for a given integration surface.
   - Bindings MUST NOT redefine protocol semantics; they map the protocol to a transport.
5. **Reference material (non-normative)**
   - `crinkl-protocol/reference/**`, diagrams, examples, prose notes.
   - Useful for implementers, not authoritative on behavior.
6. **Generated artifacts**
   - e.g. generated TypeScript validators, subject maps, stream maps, derived proto stubs.
   - Generated code is disposable and MUST be reproducible from authoritative inputs.
7. **Implementations**
   - `crinkl-platform/**`, `crinkl-server/**`, on-chain programs, workers, etc.
   - Must conform to the protocol; they are not the protocol.

## Source-of-Truth Map (What Each Directory Owns)

- `protocol/`
  - Canonical semantics + invariants (what the protocol *means*).
  - Canonical byte rules (what is hashed/signed and how).
- `bindings/`
  - Canonical transport mapping (subjects/streams for NATS, schema selection, binding version).
  - Canonical payload JSON Schemas used for runtime validation on that transport.
- `formal/`
  - Canonical invariant checks (model-checking expectations).
- `reference/`
  - Test vectors and examples; MUST match the spec if presented as vectors.

## Versioning and Change Control

### Versioning

Protocol versions use `MAJOR.MINOR.PATCH` (see `protocol/PROTOCOL_EVOLUTION.md`).

- **MAJOR**: breaking changes (hashing/signing/canonicalization changes, required field changes).
- **MINOR**: additive changes (new optional fields, new event types, new optional layers).
- **PATCH**: clarifications and non-behavioral fixes.

### What MUST happen in a protocol change

For any change that affects semantics, bytes, schemas, or wire contracts:

1. Update the normative spec in `protocol/`.
2. Update or add JSON Schemas in `bindings/**/schemas` if wire shape changes.
3. Update `versions/CHANGELOG.md`.
4. Update any impacted formal invariants in `formal/` (or explicitly justify why not).
5. Regenerate derived artifacts (codegen outputs) and ensure CI reports no drift.

## CI Enforcement Points

CI is part of the protocol. If CI doesn’t enforce it, it’s not real.

### Required checks (must be green to merge)

1. **Governance consistency**
   - No contradictory versions between `README.md` and `versions/CHANGELOG.md`.
   - Commitment Layer event payloads in `protocol/EVENTS.md` match `protocol/COMMITMENT_LAYER.md`.
   - Reference “test vectors” do not contradict the normative event envelope; if they are illustrative, they must be labeled non-normative.
2. **Binding/schema integrity**
   - Every referenced schema has a `$id`.
   - No duplicate `$id`s in a binding.
   - Every stream subject key exists in `subjects`.
   - `python3 scripts/check_drift.py` MUST pass (spec ↔ bindings ↔ reference alignment).
3. **Codegen drift**
   - Generated files in implementation repos must be identical to running codegen from `crinkl-protocol`.
   - Example: `crinkl-platform` MUST run `pnpm protocol:check` in CI.
4. **Determinism bans**
   - Ban locale-/environment-dependent ordering in deterministic paths:
     - No `localeCompare` in merkle/tree ordering, hashing inputs, canonical comparators.
     - Comparators must be defined as byte/ASCII/UTF-8 lexicographic rules (as specified).
5. **Focused tests**
   - Merkle proofs verify across build/generate/verify cycle.
   - Canonicalization stable tests (at least one leaf serialization vector).

### Recommended checks (should be green; may be phased in)

- Run the TLA+ model checker in CI for bounded configs (or on release branches).
- Cross-language interop vectors (JSON → hash → signature) for at least one event type.

## Ownership and Authority

- Protocol changes are merged only via PR review.
- Any change to hashing/canonicalization/state machine rules requires explicit review sign-off from protocol maintainers.
- Generated artifacts MUST NOT be edited directly; edits must flow from authoritative inputs.
