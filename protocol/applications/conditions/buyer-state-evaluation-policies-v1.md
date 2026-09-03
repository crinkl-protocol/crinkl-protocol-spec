---
status: draft
layer: applications
version: v1
normative: true
implementationStatus: SPECIFIED_NOT_IMPLEMENTED
---

# Buyer-State Evaluation Policies

Mirrored from `crinkl-protocol@156d63c37d4d4b9a31287e86d7623afdbe642997`, `protocol/applications/conditions/BUYER_STATE_EVALUATION_POLICIES.md`; the internal page is authority.

This document defines the typed policy artifacts referenced by `BuyerStateEvaluationContextV1` and `BuyerStateEvaluationContextV2`. It is normative for implementations that evaluate or verify `ConditionV1/profile=BUYER_STATE_V1`.

These artifacts are acceptance and reproducibility rules. They do not:

- create, correct, or invalidate Spend truth;
- upgrade a Spend Attestation verification tier;
- prove that a referenced source, root, snapshot, or statement exists;
- create buyer identity;
- prove global absence;
- authorize campaign funding, reward issuance, or settlement; or
- turn a compiler, issuer, or individual validator result into network finality.

The machine-readable union schema is [`schemas/experimental/campaigns/buyer_state_evaluation_policy_artifact_v1.schema.json`](../../../schemas/experimental/campaigns/buyer_state_evaluation_policy_artifact_v1.schema.json).

## 1. Artifact identity

Every artifact in this document is immutable and uses the same identity rule:

```text
policyId = "sha256:" + SHA-256(RFC8785_canonicalize(policyArtifact))
```

The complete artifact is the hash preimage. `policyId` is not included inside the artifact.

Changing any field produces a different `policyId`. A verifier MUST:

1. resolve the exact artifact referenced by the evaluation context;
2. verify that the artifact domain is the type required by that context field;
3. recompute and match its `policyId`;
4. reject unknown domains, schema versions, protocol versions, enum values, or extra fields; and
5. apply the artifact without silently repairing ordering or substituting a newer policy.

Policy resolution transport is out of protocol. A mutable API response is not sufficient unless its returned artifact is independently hash-matched to the context reference.

## 2. Context reference map

| Evaluation-context field | Required artifact domain |
|---|---|
| `acceptedIssuerPolicyRef` | `crinkl:buyer-state:accepted-issuer-policy:v1` |
| `acceptedSpendStatusPolicyRef` | `crinkl:buyer-state:accepted-spend-status-policy:v1` |
| `latestHeadAndCorrectionPolicyRef` | `crinkl:buyer-state:latest-head-correction-policy:v1` |
| `provenancePolicyRef` | `crinkl:buyer-state:evidence-provenance-policy:v1` |
| `subjectDeduplicationPolicyRef` | `crinkl:buyer-state:subject-deduplication-policy:v1` |
| `distinctPurchaseIntegrityPolicyRef` (`BuyerStateEvaluationContextV2`) | `crinkl:buyer-state:distinct-purchase-integrity-policy:v1` |
| `completenessPolicyRef` | `crinkl:buyer-state:evidence-completeness-policy:v1` |

The first five references are required by both context schemas. `BuyerStateEvaluationContextV1` remains unchanged. `BuyerStateEvaluationContextV2` additionally requires `distinctPurchaseIntegrityPolicyRef` before more than one composite Spend stream key can satisfy a frequency, repeat, spend-intensity, or ordered multi-purchase lifecycle statement. `completenessPolicyRef` is required only when the Condition includes `ABSENCE_NON_MEMBERSHIP`.

## 3. `AcceptedIssuerPolicyV1`

This artifact restricts which Spend Attestation issuers and keys may provide evaluation inputs.

```text
AcceptedIssuerPolicyV1 {
  domain: "crinkl:buyer-state:accepted-issuer-policy:v1",
  schemaVersion: 1,
  protocolVersion: Version,
  authoritySource: {
    type:
      "AUTHORITY_REGISTRY_HISTORY" |
      "SIGNED_ISSUER_SET_SNAPSHOT",
    sourceRef: "sha256:" + Hash
  },
  acceptedIssuerIds: [Identifier],
  authorizationTimeBasis: "EVALUATION_CUTOFF",
  keyMatchRule: "ISSUER_ID_AND_PUBLIC_KEY_MUST_MATCH_SOURCE",
  unresolvedAuthorityTreatment: "REJECT_CONTEXT",
  unauthorizedIssuerTreatment: "REJECT_INPUT"
}
```

Normative rules:

- `acceptedIssuerIds` MUST be non-empty, unique, and sorted by UTF-8 bytewise ascending value.
- The token's `signatures.issuedBy` MUST be listed.
- The token's `signatures.publicKey` MUST be authorized for that issuer under the referenced authority source and selected time basis.
- A source that cannot establish both issuer ID and key authorization MUST fail closed.
- A configured issuer ID without a bound public key source is not sufficient.
- The policy restricts trust; it cannot make an otherwise invalid signature valid.

`authoritySource.sourceRef` MUST identify an authority source whose declared scope includes Spend Attestation issuers. The commitment-chain authority registry in `COMMITMENT_LAYER.md` is not automatically a Spend-issuer registry; it is applicable only if a separately adopted registry profile explicitly gives it that scope.

The first interoperable source profile supports `EVALUATION_CUTOFF` only. It uses the authority source frozen for the evaluation cutoff and may reject historically valid tokens signed by a key no longer authorized at that cutoff.

`ATTESTATION_HEAD_EFFECTIVE_TIME` is not safe for current `SpendAttestationTokenV1` because the token does not bind a signed issuance timestamp or key ID. A key could sign a new token later for an older head. A future policy version may introduce head-effective-time authorization only when it also requires independently committed token-issuance evidence or a current-authority re-attestation. Implementations MUST reject that time basis under v1 rather than infer issuance time from the head.

The signed issuer-set source and canonical-head source profile is defined in `BUYER_STATE_ISSUER_AND_HEAD_SOURCES.md` (internal, not yet published).

## 4. `AcceptedSpendStatusPolicyV1`

This artifact declares which finalized canonical statuses may be used as positive evidence.

```text
AcceptedSpendStatusPolicyV1 {
  domain: "crinkl:buyer-state:accepted-spend-status-policy:v1",
  schemaVersion: 1,
  protocolVersion: Version,
  acceptedStatuses: ["CORRECTED" | "HARD_VERIFIED"],
  requireFinalized: true,
  unacceptedStatusTreatment: "REJECT_INPUT",
  missingStatusTreatment: "REJECT_INPUT"
}
```

Normative rules:

- `acceptedStatuses` MUST be non-empty, unique, and sorted.
- `INVALIDATED` is not an accepted positive-evidence status in this profile.
- An input with an unaccepted or missing status MUST NOT satisfy `SPEND_VALIDITY`.
- Rejecting one input does not prove that the subject lacks other qualifying evidence.
- Status acceptance occurs after cryptographic token verification and issuer authorization.

## 5. `LatestHeadAndCorrectionPolicyV1`

This artifact defines how a verifier establishes the canonical Spend head at the context cutoff.

```text
LatestHeadAndCorrectionPolicyV1 {
  domain: "crinkl:buyer-state:latest-head-correction-policy:v1",
  schemaVersion: 1,
  protocolVersion: Version,
  selectionMode: "CANONICAL_HEAD_AS_OF_CUTOFF",
  freshnessEvidenceMode:
    "CONTIGUOUS_SPEND_STREAM_TO_CUTOFF" |
    "SIGNED_HEAD_SET_SNAPSHOT",
  freshnessSourceRef: "sha256:" + Hash,
  sourceAsOf: TimestampISO,
  headOrderingRule: "GREATEST_EVENT_COUNT_PER_SPEND",
  equalCountConflictTreatment: "REJECT_CONTEXT",
  invalidatedHeadTreatment: "EXCLUDE_INPUT",
  laterCorrectionTreatment: "NEW_CONTEXT_DO_NOT_REWRITE_HISTORY",
  missingFreshnessEvidenceTreatment: "INDETERMINATE"
}
```

Normative rules:

- `sourceAsOf` MUST equal the evaluation context's `asOf`.
- A token alone does not prove it was the globally latest head at the cutoff.
- `CONTIGUOUS_SPEND_STREAM_TO_CUTOFF` requires a fork-free stream or audit bundle through the cutoff.
- `SIGNED_HEAD_SET_SNAPSHOT` requires a hash-matched signed artifact that commits the accepted head for each included composite `(spendStreamNamespaceRef, issuerId, spendId)` stream key at the cutoff.
- Among valid heads for one `spendId`, the greatest `lineage.eventCount` wins.
- Equal event counts with different head hashes or statuses are an ambiguity; a verifier MUST NOT pick a winner.
- A later correction creates a new context or evaluation. It does not rewrite the earlier result.
- A missing freshness artifact yields `INDETERMINATE`; it MUST NOT be treated as proof that the presented token is current.

This policy specializes the canonical supersession rules in `TOKENS.md`; it does not replace them.

The signed source profile is defined in `BUYER_STATE_ISSUER_AND_HEAD_SOURCES.md` (internal, not yet published). Its head-set snapshot attests freshness for included stream keys and explicitly does not claim a complete universe of Spend streams.

## 6. `EvidenceProvenancePolicyV1`

This artifact defines how accepted purchase evidence is classified relative to recorded campaign influence and controls.

```text
EvidenceProvenancePolicyV1 {
  domain: "crinkl:buyer-state:evidence-provenance-policy:v1",
  schemaVersion: 1,
  protocolVersion: Version,
  sourceType:
    "COMMITTED_INFLUENCE_LEDGER" |
    "SIGNED_PROVENANCE_SNAPSHOT",
  sourceRef: "sha256:" + Hash,
  coverageManifestRef: "sha256:" + Hash,
  campaignNamespaceRef: "sha256:" + Hash,
  coverageStart: TimestampISO,
  sourceAsOf: TimestampISO,
  organicRule: "COMPLETE_COVERAGE_NO_INFLUENCE_LINK",
  influencedRule: "POSITIVE_CAMPAIGN_INFLUENCE_LINK",
  controlRule: "SIGNED_CONTROL_ASSIGNMENT_NO_QUALIFYING_EXPOSURE",
  legacyRule: "OUTSIDE_COVERAGE_OR_EXPLICITLY_UNCLASSIFIED",
  unknownEvidenceTreatment: "INDETERMINATE",
  selfBaselineRule: "PRE_STATE_CUTOFF_PRECEDES_CAMPAIGN_START"
}
```

Normative rules:

- `sourceAsOf` MUST equal the evaluation context's `asOf`.
- The coverage manifest MUST define the campaign namespace, event types, issuers, time range, and completeness claim covered by the source.
- `INDEPENDENT_ORGANIC` requires complete declared coverage and no influence link in that coverage. Mere absence from an incomplete table or application log is insufficient.
- `CAMPAIGN_INFLUENCED` requires a positive, policy-valid campaign influence link.
- `EXPERIMENTAL_CONTROL` requires a policy-valid control assignment and no qualifying exposure under complete declared coverage.
- `UNKNOWN_LEGACY` requires an explicit classification under the source policy; it MUST NOT be inferred solely because no record was found.
- Evidence that cannot be classified under the source and coverage manifest yields `INDETERMINATE`.
- A campaign's pre-state cutoff MUST precede that campaign's start. Later outcomes cannot rewrite the frozen pre-state.

Current receipt or Spend Attestation artifacts do not automatically satisfy this policy. Deployments without a committed influence ledger or signed provenance snapshot cannot claim authoritative organic, influenced, or control classification through this artifact alone.

The first interoperable `SIGNED_PROVENANCE_SNAPSHOT` source profile is defined in `BUYER_STATE_PROVENANCE_SOURCES.md` (internal, not yet published). It can establish only a positive `CAMPAIGN_INFLUENCED` link for an exact canonical Spend head. Its manifest explicitly claims no complete universe, so omitted evidence remains `INDETERMINATE`; it cannot establish `INDEPENDENT_ORGANIC` or `EXPERIMENTAL_CONTROL`.

## 7. `SubjectDeduplicationPolicyV1`

This artifact defines how multiple accepted Spends are linked to one scoped proof subject without creating a stable global identity.

```text
SubjectDeduplicationPolicyV1 {
  domain: "crinkl:buyer-state:subject-deduplication-policy:v1",
  schemaVersion: 1,
  protocolVersion: Version,
  subjectBindingMode:
    "SCOPED_NULLIFIER" |
    "SCOPED_HOLDER_COMMITMENT" |
    "ISSUER_BLINDED_SUBJECT",
  derivationProfileRef: "sha256:" + Hash,
  scopeRule:
    "CONDITION_CUTOFF_AND_MARKET_IF_PRESENT" |
    "CONDITION_CONTEXT_CUTOFF_MARKET_RELYING_SCOPE_AND_PURPOSE",
  crossScopeLinkability: "PROHIBITED",
  missingBindingTreatment: "INDETERMINATE",
  collisionTreatment: "REJECT_CONTEXT",
  correctionDedupRule: "ONE_SPEND_ID_ONE_CANONICAL_HEAD",
  multipleSpendRule: "DISTINCT_SPEND_IDS_MAY_LINK_WITHIN_SCOPE",
  buyerCountRule:
    "ONE_SCOPED_SUBJECT_ONE_BUYER" |
    "ONE_SCOPED_SUBJECT_ONE_COUNTING_UNIT"
}
```

Normative rules:

- Every derivation profile MUST bind the subject key to `conditionId`, `asOf`, and `marketSnapshotRef` when present.
- An interoperable profile that prohibits cross-campaign or cross-relying-party correlation MUST additionally use `CONDITION_CONTEXT_CUTOFF_MARKET_RELYING_SCOPE_AND_PURPOSE` and bind `evaluationContextHash`, the relying purpose, and an exact `relyingScopeRef`. The earlier `CONDITION_CUTOFF_AND_MARKET_IF_PRESENT` value is insufficient on its own when two relying scopes reuse one Condition, cutoff, and market; no scoped-subject source profile adopts that value.
- The same scoped subject may link distinct Spend IDs only inside that scope.
- Multiple heads for one `spendId` reduce to the one canonical head selected by the correction policy; they are not distinct purchases.
- Subject material MUST NOT be exported as a public membership list or stable cross-scope identifier.
- A missing subject binding yields `INDETERMINATE` for multi-spend or distinct-buyer evaluation.
- A collision or conflicting binding fails closed.
- `ISSUER_BLINDED_SUBJECT` is an explicit issuer/publisher-trust profile; it does not provide the holder-verifiable properties of a nullifier or holder commitment.
- `ONE_SCOPED_SUBJECT_ONE_COUNTING_UNIT` is the required scoped-subject rule. The counting unit is a publisher-attested scope-bounded pseudonym. It is not a claim that the unit is one natural person, household, complete wallet set, or Sybil-resistant identity.

The derivation profile, witness format, and cryptographic proof remain separate versioned artifacts. This policy selects one; it does not invent a derivation algorithm.

The first interoperable issuer-blinded source and derivation profile are defined in `BUYER_STATE_SUBJECT_BINDING_SOURCES.md` (internal, not yet published). `SCOPED_NULLIFIER` and `SCOPED_HOLDER_COMMITMENT` remain unsupported for this source profile. Existing action or redemption nullifiers MUST NOT be used as subject-grouping tags.

## 8. `DistinctPurchaseIntegrityPolicyV1`

This artifact defines how multiple accepted canonical Spend stream keys are grouped into publisher-attested purchase units without treating different IDs or an absent duplicate match as proof of distinct real-world purchases.

```text
DistinctPurchaseIntegrityPolicyV1 {
  domain: "crinkl:buyer-state:distinct-purchase-integrity-policy:v1",
  schemaVersion: 1,
  protocolVersion: Version,
  integrityMode: "PRIVATE_PURCHASE_GROUPING",
  sourceProfileRef: HashId,
  scopeRule: "EXACT_BUYER_STATE_SUBJECT_SCOPE",
  purchaseUnit: "STANDARD_MERCHANT_CHECKOUT",
  countingRule: "ONE_SCOPED_PURCHASE_TAG_ONE_COUNTING_UNIT",
  canonicalStreamRule: "ONE_COMPOSITE_STREAM_ONE_CANONICAL_HEAD",
  sameTagRule: "COLLAPSE_AS_ONE_PURCHASE_UNIT",
  differentTagRule: "PUBLISHER_ATTESTED_DISTINCT_WITHIN_SOURCE",
  missingBindingTreatment: "INDETERMINATE",
  ambiguousEvidenceTreatment: "INDETERMINATE",
  correctionRule: "EXACT_CANONICAL_HEAD_REBIND_REQUIRED",
  absentDuplicateSignalTreatment: "NOT_EVIDENCE_OF_DISTINCTNESS",
  selectedInputClosureRule:
    "ALL_KNOWN_CANDIDATE_RELATIONSHIPS_TOUCHING_SELECTED_INPUTS_RESOLVED",
  omittedConnectedCandidateTreatment: "INDETERMINATE",
  statementFieldResolutionRule:
    "ALL_STATEMENT_RELEVANT_FIELDS_AGREE_OR_RESOLVE_DETERMINISTICALLY",
  purchaseSubjectAssignmentRule:
    "ONE_SCOPED_PURCHASE_TAG_ONE_SCOPED_SUBJECT_TAG",
  sourceSelectionRule:
    "EXACT_CHECKPOINT_GREATEST_SEQUENCE_AT_REQUEST_BOUND_SELECTION_TIME",
  missingSourceCheckpointTreatment: "INDETERMINATE",
  staleSourceTreatment: "INDETERMINATE",
  returnVoidTreatment: "INDETERMINATE",
  splitTenderTreatment: "INDETERMINATE_UNLESS_ONE_PRIVATE_ANCHOR",
  crossIssuerSemantics: "UNSUPPORTED",
  claimLevel: "PUBLISHER_ATTESTED_PRIVATE_PURCHASE_GROUPING"
}
```

Normative rules:

- Subject grouping and purchase grouping are separate axes; this policy MUST NOT be merged into `SubjectDeduplicationPolicyV1`.
- One composite stream key first reduces to one exact canonical head. Different composite keys do not by themselves establish different purchases.
- Every selected input used by a multi-purchase statement MUST have one exact private purchase-grouping binding under one exact verified source snapshot.
- Equal scoped purchase tags collapse to one purchase unit. Unequal tags carry only the declared publisher-attested assurance.
- Store/date/amount tuples, OCR or image hashes, different issuers, different Spend IDs, and missing database matches are not positive distinctness evidence.
- Every known candidate relationship touching a selected input, including through an omitted connected candidate, MUST resolve in the exact content-addressed decision manifest; otherwise the connected selected component is `INDETERMINATE`.
- Every statement-relevant field must agree or resolve deterministically, and one purchase tag may map to only one scoped-subject tag.
- Every multi-purchase evaluation must bind a request-time source selection backed by an independently authorized signed checkpoint. The selected snapshot must be the checkpointed greatest sequence; a missing checkpoint or stale source is `INDETERMINATE`.
- A missing or ambiguous binding yields `INDETERMINATE`; it MUST NOT be treated as a new purchase.
- Corrected heads require new exact bindings. Historical contexts and source references are not silently rewritten.
- The first profile is one exact Spend namespace and issuer, accepts only resolved standard positive purchases, and does not establish return, void, reversal, refund, split-tender, transaction-anchor, or cross-issuer semantics.
- A grouping tag is repeatable evidence and MUST NOT be used as an action, redemption, conversion, or settlement nullifier.

The adopted source contract is defined in `BUYER_STATE_PURCHASE_GROUPING_SOURCES.md` (internal, not yet published). Its exact private policy, signer-authority, frozen candidate-input, transitive component-decision, and Manifest V2 profile is defined in `BUYER_STATE_PURCHASE_GROUPING_POLICIES.md` (internal, not yet published). The evaluation context selects the policy and source profile; a later result or proof binds the exact request-time source-selection object, snapshot, and signed checkpoint to avoid a content-hash cycle and historical-sequence selection. Protocol resolvability does not prove runtime implementation or deployment.

## 9. `EvidenceCompletenessPolicyV1`

This artifact limits and supports an `ABSENCE_NON_MEMBERSHIP` claim.

```text
EvidenceCompletenessPolicyV1 {
  domain: "crinkl:buyer-state:evidence-completeness-policy:v1",
  schemaVersion: 1,
  protocolVersion: Version,
  conditionId: "sha256:" + Hash,
  absenceStatementIds: ["sha256:" + Hash],
  coveredIssuerPolicyRef: "sha256:" + Hash,
  coveredSpendStatusPolicyRef: "sha256:" + Hash,
  coveredCorrectionPolicyRef: "sha256:" + Hash,
  coveredProvenancePolicyRef: "sha256:" + Hash,
  coverageScopeRef: "sha256:" + Hash,
  coverageEvidenceRef: "sha256:" + Hash,
  coverageStart: TimestampISO,
  coverageAsOf: TimestampISO,
  proofMode:
    "COMMITTED_UNIVERSE_NON_MEMBERSHIP" |
    "SIGNED_COVERAGE_ATTESTATION",
  statementBindingRule: "STATEMENT_AND_WINDOW_MUST_BE_BOUND",
  claimLimit: "NO_OBSERVED_MATCH_WITHIN_DECLARED_SCOPE",
  globalAbsenceClaim: "PROHIBITED",
  missingOrUnverifiableTreatment: "INDETERMINATE"
}
```

Normative rules:

- `conditionId` MUST equal the evaluated Condition.
- `absenceStatementIds` MUST exactly equal the sorted statement IDs used by the Condition's `ABSENCE_NON_MEMBERSHIP` requirements.
- Every covered policy reference MUST equal the corresponding evaluation-context policy reference.
- `coverageAsOf` MUST equal the evaluation context's `asOf`.
- `coverageStart` MUST be early enough to cover every absence window claimed by the Condition.
- `coverageScopeRef` MUST bind the issuer, merchant/product/category, market, campaign namespace, and time scope needed by the absence statement.
- `COMMITTED_UNIVERSE_NON_MEMBERSHIP` requires a verifiable non-membership proof against the referenced committed universe.
- `SIGNED_COVERAGE_ATTESTATION` is a bounded issuer/evaluator claim about declared coverage; it is not proof of the whole world.
- Missing, partial, stale, mismatched, or unverifiable coverage yields `INDETERMINATE`.
- External language MUST say “no observed match within the declared scope” unless a stronger separately adopted claim is proven. Global absence is prohibited in v1.

## 10. Context validation procedure

Before evaluating a Condition, a verifier MUST:

1. verify the Condition and `conditionId`;
2. verify the evaluation context and `evaluationContextHash`;
3. resolve each required policy reference and enforce the field-to-domain map in §2;
4. recompute each `policyId` and reject mismatches;
5. verify issuer signature and authority under `AcceptedIssuerPolicyV1`, including the signed issuer source rules in `BUYER_STATE_ISSUER_AND_HEAD_SOURCES.md` when selected;
6. apply `AcceptedSpendStatusPolicyV1`;
7. establish the canonical head at cutoff under `LatestHeadAndCorrectionPolicyV1`, including the signed head source and inclusion rules when selected;
8. classify provenance under `EvidenceProvenancePolicyV1`;
9. establish scoped subject linkage under `SubjectDeduplicationPolicyV1` when required;
10. when using `BuyerStateEvaluationContextV2`, establish distinct purchase grouping under `DistinctPurchaseIntegrityPolicyV1` before more than one composite Spend stream key contributes to a multi-purchase statement;
11. resolve every supplied or statement-required merchant/brand, product, category, commercial entity-set, and market reference under the strict policy, authority, snapshot, dependency, entry, cutoff, and disclosure rules in `BUYER_STATE_IDENTITY_CATALOG_MARKET_SOURCES.md`;
12. if the Condition includes absence, cross-bind and verify `EvidenceCompletenessPolicyV1`; and
13. evaluate the Condition with the tri-state rules in `CONDITIONS.md`.

An unresolved or wrong-type policy reference makes the evaluation context invalid. A resolved policy whose required per-subject evidence is missing or unverifiable yields `INDETERMINATE` where this document specifies it.

## 11. Canonical ordering

Before hashing:

- `AcceptedIssuerPolicyV1.acceptedIssuerIds` MUST be sorted by UTF-8 bytewise ascending value and contain no duplicates.
- `AcceptedSpendStatusPolicyV1.acceptedStatuses` MUST be sorted by UTF-8 bytewise ascending value and contain no duplicates.
- `EvidenceCompletenessPolicyV1.absenceStatementIds` MUST be sorted by UTF-8 bytewise ascending value and contain no duplicates.

A verifier MUST reject noncanonical ordering. It MUST NOT silently sort a received artifact before matching a claimed `policyId`.

## 12. Evidence and authority boundary

```text
policy artifact
  says which evidence and rules are acceptable

referenced source/coverage/derivation artifact
  supplies the declared evidence substrate

subject proof or evaluator result
  applies the policy to one scoped subject

qualification proof
  binds the result to a relying scope
```

These layers MUST NOT collapse. In particular:

- a policy hash is not a qualification proof;
- a source hash is not proof that a subject is included or absent;
- an issuer signature is not independent verification;
- a compiler output is not automatically canonical;
- one validator signature is not network finality; and
- no verifier may assume that independent validators share a local filesystem or identical uncommitted evidence view.

## 12. Versioning and compatibility

These are optional additive Condition-layer artifacts. Existing events, tokens, promo objects, and runtime bindings do not receive them and are unchanged. The current event/token `protocolVersion` remains `1.0.0-rc.1`.

Unknown policy domains or schema versions MUST be rejected. Changing a field's meaning, identity derivation, canonical ordering, or fail-closed treatment requires a new schema version.

The policy artifacts make evaluation references typed and reproducible. They do not define the referenced issuer-set, freshness, provenance, coverage, subject-derivation, or non-membership artifact formats. Until those separately versioned formats and their authority rules exist, an implementation MUST treat unavailable or unverifiable source material according to the fail-closed rules above.
