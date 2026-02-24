# Protocol Evolution

Current version: **1.0.0-rc.1**

This document describes how the Crinkl Protocol evolves without creating forked implementations. It is normative only where it constrains verifier behavior; governance and rollout timelines are non-normative.

## Version surfaces

The protocol has multiple version “surfaces” with different compatibility expectations:

- **`protocolVersion`** (events, tokens): gates semantic interpretation of envelopes and required rules. Unknown `protocolVersion` MUST be rejected (see `DATA_STRUCTURES.md#schema-evolution`).
- **`schemaVersion`** (token schemas, event payload schemas, commitment leaf schemas, statement schemas): gates structure and verification procedure. Unknown `schemaVersion` MUST be rejected for portable verification surfaces.
- **ZK metadata** (`proofSystem`, `circuitId`, `verifierKeyId`): gates proof verification. Unknown circuits/keys MUST be rejected.

## Version numbering

Where SemVer is used, format is `MAJOR.MINOR.PATCH`:

- **MAJOR**: breaking verifier changes (hash/signature/canonicalization changes; required field changes; semantics changes).
- **MINOR**: additive changes that still require verifier awareness (new optional fields that change interpretation, new event types, new token schemas).
- **PATCH**: clarifications, typos, and non-behavioral documentation changes.

## Compatibility rules (normative)

Verifiers MUST follow `DATA_STRUCTURES.md#schema-evolution`. In particular:

- Unknown `protocolVersion` ⇒ reject.
- Known `protocolVersion` with unknown additional fields ⇒ include fields in hash/signature verification and ignore semantics unless explicitly defined; do not drop fields prior to hashing.
- Unknown enum value in a normative enum ⇒ reject.
- Unknown `eventName` ⇒ reject.
- Unknown portable token `schemaVersion` ⇒ reject.

## Additive changes without breaking old verifiers

To minimize unnecessary version churn:

- Prefer adding optional fields inside reserved namespaces (`_meta`, `extensions`) when semantics are explicitly “ignored unless understood”.
- Prefer new event types over overloading existing event payload meaning.
- Prefer new `schemaVersion` for a token/proof schema when verification procedure changes.
- Avoid changing `protocolVersion` unless a verifier must change its acceptance logic to remain safe.

## Breaking change examples (MAJOR)

- Changing the canonicalization rule (RFC 8785 → other).
- Changing the hash function or signature scheme.
- Changing `eventHash` / `tokenHash` preimage rules or domain separation.
- Changing ordering semantics for streams or Merkle constructions.
- Changing token claim semantics or allowed terminal state meanings.
- Changing `statementId` derivation rules or statement schema rules used for verification.
- Changing ZK proof binding requirements (required public inputs / transcript binding) or the meaning of any existing proof metadata fields.
- Adding/removing/reordering fields in a commitment leaf schema in a way that changes `leafHash` computation (requires a new leaf `schemaVersion`).

## Deprecation (non-normative process)

1. Mark a field/feature as deprecated in the spec.
2. Provide a migration path and an explicit “removal version”.
3. Remove only after verifiers have a defined upgrade window.
