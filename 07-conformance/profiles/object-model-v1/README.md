---
status: release-candidate
layer: core/predicate
version: v1
normative: true
---

# Object-Model OM4 Conformance Bundle

Maturity: `candidate`.

This bundle registers the conformance fixtures for board step OM4 of the
object-model refactor
(`governance/protocol-object-model-decisions-2026-08-08.md`): the four new
standalone schemas (`VerificationPolicy`, `IssuerRegistrySnapshot`,
`AttestationStatus`, `SpendPredicate`) and the negative conformance cases for
the two collapsed campaign roles (`eligibilityProof`, `conversionProof`).

Unlike the other profile bundles in `07-conformance/profiles/`, this bundle
does not publish a previously-adopted internal engineering implementation —
`VerificationPolicy`, `AttestationStatus`, and `SpendPredicate` are authored
directly in this public spec repository from its own existing normative
prose, and `IssuerRegistrySnapshot` is modeled on (not copied from) the
internal `SpendIssuerSetSnapshotV1` artifact as a read-only reference. This
manifest therefore omits the `engineeringSource` field the other bundles
carry rather than assert an adopted-engineering provenance that does not
exist for three of the four schemas.

The bundle binds:

- Draft 2020-12 schema validation for each of the four schemas (one valid
  instance accepted, one invalid instance rejected per schema), via
  `jsonschema.Draft202012Validator` — the same mechanism
  `07-conformance/profiles/w3c-vc-2.0-spend-attestation-v1` already uses; and
- rejection of `eligibilityProof` and `conversionProof` as artifact kinds,
  against the thirteen-name canonical registry in `README.md#core-objects`,
  with `ProofOfMatch` and `SpendPredicate` as positive controls.

The four schemas themselves live at their canonical spec locations, not
inside this profile directory:

- `01-core/schemas/verification_policy_v1.schema.json`
- `01-core/schemas/issuer_registry_snapshot_v1.schema.json`
- `01-core/schemas/attestation_status_v1.schema.json`
- `04-condition-layer/schemas/spend_predicate_v1.schema.json`

None of the four schemas is required for Core Spend Attestation, Token, or
Credential validity. `verificationPolicyHash` is not added to any existing
artifact by this bundle or by the schemas it tests (that binding is a
separate, later-sliced change, OM5).

## Open points

See the OM4 pull request body for the full per-schema derivation notes and
open points where existing prose was silent (`VerificationPolicy.rules`,
`SpendPredicate.ruleExpression`, and the `IssuerRegistrySnapshot` fields the
internal artifact models that this public schema does not yet, in
particular per-authority key rotation via a separate `keyId`).
