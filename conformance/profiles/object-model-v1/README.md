---
status: release-candidate
layer: core/predicate
version: v1
normative: true
---

# Object-Model OM4r Conformance Bundle

Maturity: `candidate`.

This bundle registers the conformance fixtures for board steps OM4 and OM4r of the
object-model refactor
(`governance/protocol-object-model-decisions-2026-08-08.md`): the four new
standalone schemas (`VerificationPolicy`, `IssuerRegistrySnapshot`,
`AttestationStatus`, `SpendPredicate`) and the negative conformance cases for
the two collapsed campaign roles (`eligibilityProof`, `conversionProof`).

This bundle is derived directly from public-spec normative prose.
`IssuerRegistrySnapshot` also uses the internal
`SpendIssuerSetSnapshotV1` artifact as a read-only modeling reference. The
manifest omits `engineeringSource` because this candidate bundle does not
claim an adopted engineering implementation.

The bundle binds:

- Draft 2020-12 structural validation and executable content-hash,
  timestamp-ordering, and cross-field fixtures for the four schemas, via
  `jsonschema.Draft202012Validator` — the same mechanism
  `conformance/profiles/w3c-vc-2.0-spend-attestation-v1` already uses; and
- whole-object dispatch through the checker's independent thirteen-name
  canonical registry in `README.md#protocol-objects`, rejecting
  `eligibilityProof` and `conversionProof` while accepting `ProofOfMatch` and
  a schema-valid `SpendPredicate` as positive controls.

The four schemas themselves live at their canonical spec locations, not
inside this profile directory:

- `protocol/core/schemas/verification_policy_v1.schema.json`
- `protocol/core/schemas/issuer_registry_snapshot_v1.schema.json`
- `protocol/core/schemas/attestation_status_v1.schema.json`
- `protocol/applications/conditions/schemas/spend_predicate_v1.schema.json`

None of the four schemas is required for Core Spend Attestation, Token, or
Credential validity. The separate OM5 wire slice governs the
`verificationPolicyHash` binding and is outside this bundle.

## Contract boundary

`VerificationPolicy.rules`, `SpendPredicate.parameters`,
`SpendPredicate.ruleExpression`, and replay/nullifier rule vocabulary are
profile-defined non-empty objects whose complete contents are hash-bound.
`IssuerRegistrySnapshot` uses the public authority-event vocabulary and does
not import fields from the internal reference artifact that lack a public
protocol definition.
