---
status: draft
layer: governance
version: v1
normative: true
---

# Protocol Evolution

Current public repository source candidate: **1.0.0-rc.5** (`RELEASE_CANDIDATE_NOT_PUBLISHED`)

Current default Crinkl Platform binding `protocolVersion`: **1.0.0-rc.2**

This document's frontmatter maturity is `draft`. Document maturity is separate
from repository/package maturity: `v1.0.0-rc.5` is an unpublished SemVer prerelease candidate,
while each document retains its own reviewed status. Neither state promotes or
demotes the other, no stable `v1.0.0` release is declared here, and the prior
`v1.0.0-rc.4` tag remains immutable.

This document describes how the Crinkl Protocol evolves without creating forked implementations. It is normative only where it constrains verifier behavior; governance and rollout timelines are non-normative.

## Version surfaces

A version is meaningful only within the surface that owns it. A specification
release label is not, by itself, an object-schema, wire, profile, suite,
binding, context, cryptographic-domain, document-maturity, runtime-support, or
authority-state version.

| Surface | Identifies | Resolution rule |
| --- | --- | --- |
| Specification release | One exact public package and its declared artifacts | Resolve the SemVer label with its manifest, commit/tree, and conformance suite. A source candidate is not a release merely because it has a version-like label. |
| Wire protocol | Signed envelope and event/token interoperability | `protocolVersion` is compared against the receiver's explicitly supported wire set. Unknown values MUST be rejected (see `../01-core/canonicalization.md#schema-evolution`). |
| Object schema | The shape and meaning of one object family | The schema version is scoped to that family; it is not a global protocol version. Unknown portable schema versions MUST be rejected. |
| Profile and conformance suite | An optional behavior profile and its executable checks | The profile or suite declares the object and wire versions it composes. |
| Binding, context, and cryptographic domain | A transport mapping, signing context, hash construction, or domain separator | Each has its own identity and successor rules; compatibility is never inferred from a nearby schema label. |
| Document maturity | The status of this prose | Draft, candidate, and released documentation do not themselves establish implementation or deployment state. |
| Runtime support | Behavior of one named implementation | Support and default selection are declared by that runtime or applicable profile. |
| Authority state | Candidate, adopted, released, superseded, or withdrawn standing | This state is established by the evidence appropriate to the authority, not by a filename or version string. |

A source implementation, repository-main containment, engineering adoption,
public release, runtime support, authority acceptance, validator-network
adoption, and production deployment are distinct evidence-bearing states. No
one state implies another.

### Artifact-scoped schema versions

`verification_policy_v1.json`, its `$id`, and the `VerificationPolicyV1`
schema-V1 aliases identify the same schema artifact. Its `policyVersion` field
instead identifies an instance revision under that schema. These are separate
axes and must not be compared as competing protocol releases.

`SpendAttestationTokenV1` and `SpendAttestationTokenV2` are supported sibling
schemas. V2 adds an optional signed `holderBinding`; V1 remains valid, and a
V2 token without `holderBinding` remains valid. The issuance default is
declared separately by the applicable profile or runtime; it is never inferred
from the highest available schema version.

Lower, artifact-scoped names such as `V1` remain correct when they identify
their own stable family. A later specification release does not globally rename
them.

### Identifier stability and release evidence

Aliases for one artifact must agree on the same identity and bytes. Agreement
does not resolve a same-identifier, different-byte collision: that collision
is invalid and requires explicit handling rather than alias preference.

Released identities and bytes are immutable. A repair is made with a successor
identity or an additive erratum that preserves the original release evidence;
it is not made by silently replacing bytes at an existing identity.

[`../versions/release.json`](../versions/release.json) is the machine-readable
authority for declarations made by a public specification release. A source
branch, README marker, directory name, or candidate manifest is not a released
identity. Portable consumers require the authority-accepted tag and exact
release-manifest digest, and must reject a manifest whose status is not
`RELEASED`.

Release finalization is an explicit state transition:

1. review the exact source candidate and byte-parity evidence;
2. merge the corresponding adopted engineering source;
3. change both release-status fields to `RELEASED` in one final public release commit;
4. tag that exact commit with the `requiredTag`; and
5. publish and accept the exact `versions/release.json` digest through the configured
   release authority.

Changing a README, creating a branch, or adding a conformance-manifest entry
satisfies none of these steps by itself.

Schema display titles and filenames are non-authoritative. When two schemas
share a title, a portable verifier MUST resolve the intended schema by its
exact schema identifier and, where a profile pins bytes, its content hash.
Title-only resolution is prohibited.

## Version numbering

Where SemVer is used, format is `MAJOR.MINOR.PATCH`:

- **MAJOR**: breaking verifier changes (hash/signature/canonicalization changes; required field changes; semantics changes).
- **MINOR**: additive changes that still require verifier awareness (new optional fields that change interpretation, new event types, new token schemas).
- **PATCH**: clarifications, typos, and non-behavioral documentation changes.

## Compatibility rules (normative)

Verifiers MUST follow `../01-core/canonicalization.md#schema-evolution`. In particular:

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
