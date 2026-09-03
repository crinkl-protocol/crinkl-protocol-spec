---
status: draft
layer: applications
version: v1
normative: true
implementationStatus: SPECIFIED_NOT_IMPLEMENTED
---

# Conditions

Mirrored from `crinkl-protocol@156d63c37d4d4b9a31287e86d7623afdbe642997`, `protocol/applications/conditions/CONDITIONS.md`; the internal page is authority.

This document defines the optional Condition layer for Crinkl Protocol v1. It is normative for implementations that create, evaluate, or verify a `ConditionV1` object. It does not change Spend Attestation validity, reward issuance, existing promo objects, or any state machine.

## 1. Purpose

A Condition is an immutable, hash-identifiable rule over one or more accepted protocol attestations or statements. Conditions are downstream of Spend truth:

- they do not create or correct a Spend;
- they do not mint a Spend Attestation Token;
- they do not change verification tier;
- they do not define campaign funding, rewards, routing, exposure, conversion, or settlement; and
- they do not authorize an economic action.

`BUYER_STATE_V1` is the first registered Condition profile. The Crinkl business term **Buyer-State Predicate** means a `ConditionV1` whose `profile` is `BUYER_STATE_V1`. It is not a separate wrapper or independently hashed object.

## 2. `ConditionV1`

The machine-readable schema is [`schemas/experimental/campaigns/condition_v1.schema.json`](../../../schemas/experimental/campaigns/condition_v1.schema.json).

```text
ConditionV1 {
  domain: "crinkl:condition:v1",
  schemaVersion: 1,
  protocolVersion: Version,
  profile: "BUYER_STATE_V1",

  requirements: [
    {
      requirementId: Identifier,
      primitive:
        "SPEND_VALIDITY" |
        "MERCHANT_PRODUCT_CATEGORY_RELATIONSHIP" |
        "FREQUENCY_INTENSITY" |
        "RECENCY_LIFECYCLE" |
        "MARKET_CONTEXT" |
        "ABSENCE_NON_MEMBERSHIP",
      statementId?: "sha256:" + Hash,
      relativeWindow?: {
        startOffsetDays: Integer <= 0,
        endOffsetDays: Integer <= 0
      }
    }
  ],

  composition: {
    operator: "ALL" | "ANY" | "AT_LEAST",
    requirementIds: [Identifier],
    minimumSatisfied?: Integer >= 1
  },

  timeSemantics: {
    sourceField: "SPEND_TIMESTAMP",
    anchor: "EVALUATION_CUTOFF"
  },

  provenanceRequirement: {
    acceptedEvidenceClasses: [
      "INDEPENDENT_ORGANIC" |
      "CAMPAIGN_INFLUENCED" |
      "EXPERIMENTAL_CONTROL" |
      "UNKNOWN_LEGACY"
    ],
    unknownEvidenceTreatment: "INDETERMINATE"
  },

  absencePolicyRequirement: {
    mode:
      "NOT_REQUIRED" |
      "COMPLETENESS_OR_NON_MEMBERSHIP_REQUIRED"
  }
}
```

Unknown `domain`, `schemaVersion`, `profile`, primitive, composition operator, evidence class, unknown-evidence treatment, or absence-policy mode values MUST be rejected.

## 3. Condition identity

`conditionId` is the only canonical identity for a Condition:

```text
conditionId = "sha256:" + SHA-256(RFC8785_canonicalize(condition))
```

The complete `ConditionV1` object is the hash preimage. `conditionId` is not included inside that preimage.

For a `BUYER_STATE_V1` Condition:

```text
buyerStatePredicateId = conditionId
```

`buyerStatePredicateId` is an acceptable field or API alias only when it carries the exact `conditionId` bytes. An implementation MUST NOT:

- wrap the Condition and hash the wrapper;
- derive a second identifier from a business label;
- omit `profile` or any other Condition field from the hash preimage; or
- treat `predicateId` from `PredicateDefinitionV1` as the same identifier.

Changing any Condition field produces a new `conditionId`.

## 4. Canonical ordering

Before hashing, a producer MUST construct the semantic object in canonical form:

1. `requirements` MUST be sorted by UTF-8 bytewise ascending `requirementId`.
2. `requirementId` values MUST be unique.
3. `composition.requirementIds` MUST contain every non-`SPEND_VALIDITY` requirement ID exactly once, MUST exclude the `SPEND_VALIDITY` guard ID, and MUST be sorted by the same rule.
4. `provenanceRequirement.acceptedEvidenceClasses` MUST contain no duplicates and MUST be sorted by UTF-8 bytewise ascending value.
5. `relativeWindow.startOffsetDays` MUST be less than or equal to `relativeWindow.endOffsetDays`.
6. RFC 8785 canonicalization is then applied to the full object.

A verifier MUST reject nonconforming order, duplicate requirement IDs, a composition that omits or adds an ID, or an inverted relative window. A verifier MUST NOT silently sort or repair a received Condition before checking its claimed identifier.

## 5. `BUYER_STATE_V1` primitive registry

The profile is a restricted composition layer, not an arbitrary rule language.

| Primitive | Meaning | `statementId` | Relative window |
|---|---|---|---|
| `SPEND_VALIDITY` | Every Spend Attestation input used by another requirement is an accepted canonical head under the evaluation context. | MUST be absent; context policies define acceptance. | Optional. |
| `MERCHANT_PRODUCT_CATEGORY_RELATIONSHIP` | Accepted evidence establishes the relationship encoded by a registered statement over merchant, store, brand, product, or category material. | REQUIRED. | Optional. |
| `FREQUENCY_INTENSITY` | Accepted evidence establishes the count or spend-intensity statement over distinct purchase units under the bound integrity policy when multiple stream keys contribute. | REQUIRED. | REQUIRED. |
| `RECENCY_LIFECYCLE` | Accepted evidence establishes a recency or ordered lifecycle statement. | REQUIRED. | REQUIRED. |
| `MARKET_CONTEXT` | Accepted evidence establishes the market/context statement under a bound market snapshot or equivalent committed set. | REQUIRED. | Optional. |
| `ABSENCE_NON_MEMBERSHIP` | An accepted completeness or non-membership profile establishes the absence statement inside the declared window. | REQUIRED. | REQUIRED. |

`statementId` uses the statement identity and circuit rules in `ZK_LAYER.md` and `ZK_CIRCUIT_CATALOG.md`. A Condition composes registered statements; it does not redefine their proof semantics.

`OUTCOME_CONVERSION` is deliberately not a `BUYER_STATE_V1` primitive. A pre-action buyer state MUST NOT contain the post-action outcome used to evaluate the same campaign.

Every `BUYER_STATE_V1` Condition MUST contain exactly one `SPEND_VALIDITY` requirement and at least one non-guard requirement. Other primitives cannot bypass that guard.

Business labels such as new, repeat, active, lapsed, reactivated, category buyer, or competitor buyer are templates that compile into these primitives. A label string is not a protocol primitive and is not included merely to assert proof meaning.

## 6. Composition rules

- `SPEND_VALIDITY` is an unconditional guard and is not part of Boolean counting.
- `ALL` is satisfied only when every named non-guard requirement is satisfied.
- `ANY` is satisfied when at least one named non-guard requirement is satisfied.
- `AT_LEAST` is satisfied when at least `minimumSatisfied` named non-guard requirements are satisfied.
- `minimumSatisfied` MUST be present only for `AT_LEAST`.
- For `AT_LEAST`, `minimumSatisfied` MUST be no greater than the number of named non-guard requirements.
- There is no general `NOT` operator.

The Condition is never satisfied unless the `SPEND_VALIDITY` guard is satisfied, regardless of composition operator.

### 6.1 Tri-state composition

Each requirement evaluates to `SATISFIED`, `NOT_SATISFIED`, or `INDETERMINATE`.

The unconditional guard is applied first:

- guard `SATISFIED` permits evaluation of the non-guard composition;
- guard `NOT_SATISFIED` makes the Condition `NOT_SATISFIED`; and
- guard `INDETERMINATE` makes the Condition `INDETERMINATE`.

When the guard is satisfied:

- `ALL` is `SATISFIED` when every non-guard result is satisfied, `NOT_SATISFIED` when any result is not satisfied, and otherwise `INDETERMINATE`.
- `ANY` is `SATISFIED` when any non-guard result is satisfied, `NOT_SATISFIED` when every result is not satisfied, and otherwise `INDETERMINATE`.
- `AT_LEAST N` is `SATISFIED` when at least N results are satisfied; it is `NOT_SATISFIED` only when the satisfied plus indeterminate results cannot reach N; otherwise it is `INDETERMINATE`.

An implementation MUST NOT collapse an indeterminate requirement to false before composition.

Negative meaning is permitted only through `ABSENCE_NON_MEMBERSHIP`, whose evidence requirements are explicit. This prevents missing or partial evidence from being interpreted as a proven negative.

## 7. Time semantics

All relative windows are anchored to the separately hashed evaluation context's `asOf` cutoff:

```text
windowStart = asOf + startOffsetDays
windowEnd   = asOf + endOffsetDays
```

Offsets are whole UTC days and are non-positive. Boundary comparison is inclusive unless the referenced statement definition specifies a stricter interval and that statement identity is bound by `statementId`.

Evaluation MUST NOT depend on the verifier's current clock, database `now()`, or a mutable registry lookup. A moving cutoff produces a different evaluation context, not a different reusable Condition.

## 8. Evidence provenance

`provenanceRequirement.acceptedEvidenceClasses` declares which purchase-evidence provenance classes can satisfy the Condition. The evaluation context binds the adopted provenance policy that assigns and verifies those classes.

- `INDEPENDENT_ORGANIC`: no recorded campaign influence under the bound provenance policy.
- `CAMPAIGN_INFLUENCED`: the purchase is linked to campaign exposure or participation under the bound policy.
- `EXPERIMENTAL_CONTROL`: the subject was assigned to a reconstructible control condition under the bound policy.
- `UNKNOWN_LEGACY`: provenance is unavailable or predates the adopted classification contract.

If an input's class cannot be established, the affected requirement result is `INDETERMINATE`. `UNKNOWN_LEGACY` is accepted only when it is explicitly listed; it MUST NOT be silently treated as independent organic evidence.

## 9. Absence and non-membership

Absence from one wallet, issuer, application, database, or observation window does not prove that a purchase did not occur.

When any requirement uses `ABSENCE_NON_MEMBERSHIP`:

- `absencePolicyRequirement.mode` MUST be `COMPLETENESS_OR_NON_MEMBERSHIP_REQUIRED`;
- the evaluation context MUST carry `completenessPolicyRef`;
- the referenced statement and policy MUST define the observed scope and the completeness or non-membership basis; and
- missing, stale, partial, or unverifiable coverage MUST yield `INDETERMINATE`.

A Condition without `ABSENCE_NON_MEMBERSHIP` MUST use `NOT_REQUIRED`.

## 10. Evaluation context

Condition meaning is reusable. Mutable-world inputs are frozen in `BuyerStateEvaluationContextV1` or `BuyerStateEvaluationContextV2`, whose schemas are [`schemas/experimental/campaigns/buyer_state_evaluation_context_v1.schema.json`](../../../schemas/experimental/campaigns/buyer_state_evaluation_context_v1.schema.json) and [`schemas/experimental/campaigns/buyer_state_evaluation_context_v2.schema.json`](../../../schemas/experimental/campaigns/buyer_state_evaluation_context_v2.schema.json). V1 remains unchanged; V2 is required for multi-purchase private-grouping semantics.

The typed policy artifacts referenced by this context are defined in [`buyer-state-evaluation-policies-v1.md`](./buyer-state-evaluation-policies-v1.md). A hash reference alone is not evidence; verifiers must resolve the correct artifact type, recompute its hash, and verify its referenced source material.

The first interoperable signed source profile for Spend-issuer authorization and canonical-head freshness is defined in `BUYER_STATE_ISSUER_AND_HEAD_SOURCES.md` (internal, not yet published). It admits independently verifiable positive Spend evidence only; it does not supply provenance, scoped-subject, or absence-completeness artifacts.

The first interoperable positive campaign-provenance source profile is defined in `BUYER_STATE_PROVENANCE_SOURCES.md` (internal, not yet published). It can assign `CAMPAIGN_INFLUENCED` only from a verified positive event-to-exact-Spend-head link. It supplies no organic/control absence inference and no independently proven scoped-subject binding.

The first interoperable scoped-subject source profile is defined in `BUYER_STATE_SUBJECT_BINDING_SOURCES.md` (internal, not yet published). It supplies private, publisher-attested same-scoped-subject correlation for exact accepted Spend heads. It does not prove natural-person identity, holder control, distinct real-world purchases, action replay, validator finality, or settlement.

The adopted interface/schema contract and first closed private policy/component profile for distinct-purchase integrity are defined in `BUYER_STATE_PURCHASE_GROUPING_SOURCES.md` (internal, not yet published) and `BUYER_STATE_PURCHASE_GROUPING_POLICIES.md` (internal, not yet published). At the protocol layer they group exact scoped-subject bindings and inherited canonical Spend heads into private publisher-attested purchase units under Manifest V2. No live source or qualification deployment is established here, and the artifacts do not independently prove real-world transaction uniqueness, merchant authenticity, payment finality, or cross-issuer distinctness.

The first strict identity, catalog, commercial entity-set, and market source profile is defined in `BUYER_STATE_IDENTITY_CATALOG_MARKET_SOURCES.md` (internal, not yet published). It gives the four existing registry snapshot fields exact, signed artifact types while preserving both context schemas. Competitor, sponsor, target, and allowlist sets remain separately bound statement or campaign meaning; they do not become category truth. Registry membership is positive-only and does not prove that a referenced product was purchased.

The framework for declaring how one concrete statement type may be evaluated is defined in `BUYER_STATE_STATEMENT_EVALUATION_PROFILES.md` (internal, not yet published). A profile selects one strict statement schema, one non-guard primitive, exact input/source requirements, and one disclosed, registered-ZK, or authorized-private-evaluator mode. A strict non-portable input manifest freezes the exact Condition, requirement, statement, profile, context, cutoff, scope, Spend heads, source snapshots, and source selections for one local evaluation. The profile content reference is separate from the existing `statementId`; neither profile nor input manifest defines a portable result or makes a deployment claim. Until a concrete statement schema and independently pinned evaluation profile are adopted and resolvable, the affected requirement is `INDETERMINATE`.

The first strict statement schemas and their exact claim ceilings are defined in
[`buyer-state-statements-v1.md`](./buyer-state-statements-v1.md).
Their disclosed profile candidates remain unavailable until the required
implementation, conformance, and recipient-disclosure artifacts resolve and are
independently pinned. Separate requirements do not imply a shared Spend witness.

The first registered disclosed artifact graph is the purchase-window profile in
`BUYER_STATE_DISCLOSED_EVALUATOR_REGISTRATION.md` (internal, not yet published).
It pins a pure implementation, conformance suite and disclosure policy, but its
live recipient authority remains unresolved and execution remains unavailable.
Registration and conformance-only credentials do not authorize disclosure.

```text
BuyerStateEvaluationContextV2 {
  domain: "crinkl:buyer-state-evaluation-context:v2",
  schemaVersion: 2,
  protocolVersion: Version,
  conditionId: "sha256:" + Hash,
  asOf: TimestampISO,
  acceptedIssuerPolicyRef: "sha256:" + Hash,
  acceptedSpendStatusPolicyRef: "sha256:" + Hash,
  latestHeadAndCorrectionPolicyRef: "sha256:" + Hash,
  provenancePolicyRef: "sha256:" + Hash,
  subjectDeduplicationPolicyRef: "sha256:" + Hash,
  distinctPurchaseIntegrityPolicyRef: "sha256:" + Hash,
  storeRegistrySnapshotRef?: "sha256:" + Hash,
  productCatalogSnapshotRef?: "sha256:" + Hash,
  categorySnapshotRef?: "sha256:" + Hash,
  marketSnapshotRef?: "sha256:" + Hash,
  completenessPolicyRef?: "sha256:" + Hash
}
```

Context identity is:

```text
evaluationContextHash =
  "sha256:" + SHA-256(RFC8785_canonicalize(evaluationContext))
```

The complete context is the preimage. `evaluationContextHash` is not included inside the object.

A verifier MUST reject a context when:

- `conditionId` does not identify the exact Condition being evaluated;
- a required policy or snapshot cannot be resolved and verified;
- an `ABSENCE_NON_MEMBERSHIP` Condition lacks `completenessPolicyRef`;
- a `MARKET_CONTEXT` statement requires a market snapshot and none is bound;
- a supplied store, product, category, or market snapshot does not resolve to the exact strict registry kind, policy, authority, cutoff, dependencies, and signed root required by its context field;
- the issuer, status, correction, provenance, subject-deduplication, or supplied distinct-purchase-integrity policy is unknown; or
- `asOf` is not the cutoff used to select canonical attestation heads.

Existing V1 context bytes remain valid for their adopted semantics. Before more than one composite Spend stream key may satisfy `FREQUENCY_INTENSITY` or another multi-purchase statement, the evaluator MUST receive V2 and the exact policy/profile/source, Manifest V2 candidate/component material, request-time checkpoint, and source-selection material MUST verify. Otherwise the affected requirement is `INDETERMINATE`. An older V1 context or different Spend IDs never grant distinct-purchase meaning. The protocol policy formats are defined in `BUYER_STATE_PURCHASE_GROUPING_POLICIES.md`; a live source or evaluator remains a separate implementation/deployment claim.

## 11. Evaluation result

Every `BUYER_STATE_V1` evaluation is tri-state:

| Result | Meaning |
|---|---|
| `SATISFIED` | Accepted evidence establishes the Condition under the bound context. |
| `NOT_SATISFIED` | Accepted evidence establishes that the Condition is false under a policy capable of making that determination. |
| `INDETERMINATE` | Evidence, policy coverage, freshness, completeness, or proof material is insufficient to establish either state. |

`INDETERMINATE` MUST NOT be converted into proof of ineligibility or proof of absence. Aggregate buyer-supply computation may count only distinct subjects with `SATISFIED` results.

This document does not define a portable result, qualification-proof, or aggregate-supply schema. `BuyerStateStatementEvaluationProfileV1` defines how one requirement may be evaluated locally; it is not such a result. Those artifacts require their own schema, relying scope, action-nullifier when applicable, privacy, and verifier-policy contracts. A scoped-subject grouping tag is repeatable evidence inside one subject scope; it is not a one-time nullifier.

## 12. Proof and scope binding

A Condition is proof-system independent. A relying profile may verify disclosed Spend Attestations, a registered ZK proof, or an authorized evaluator result, but it MUST bind:

- `conditionId`;
- `evaluationContextHash`;
- the relying scope when the result is campaign- or verifier-scoped;
- every referenced statement and proof-system identifier;
- the exact accepted `statementEvaluationProfileRef` when the Step 9 framework is used;
- the relevant Spend token and canonical-head bindings; and
- any separately required action nullifier.

A proof verifies the Condition under a context. It does not upgrade the verification tier of its input Spend Attestations.

## 13. Compatibility with `PredicateDefinitionV1`

`PredicateDefinitionV1` in `PROMO_PROTOCOL.md` remains a distinct legacy coordination object. Its `predicateId` hashes routing, exclusion, promoter-gate, and settlement inputs that are outside Condition truth.

An adapter MAY compile the proof-relevant meaning of a legacy predicate into a `BUYER_STATE_V1` Condition only when it:

1. excludes routing, display, promoter-capacity, reward, and settlement fields from the Condition;
2. maps every rule to a registered Condition primitive and statement;
3. emits the separately resolved evaluation context;
4. records the source `predicateId` to `conditionId` mapping; and
5. fails closed when the legacy object does not provide enough information.

The two identifiers MUST remain distinct. Existing `PredicateDefinitionV1`, promo messages, routes, and verifier behavior are unchanged.

## 14. Security and privacy invariants

- A Condition MUST NOT contain a materialized buyer or wallet list.
- A Condition or evaluation context MUST NOT contain campaign funding, rewards, settlement, display metadata, routing scores, or agent recommendations.
- A context policy reference is not proof that the referenced policy was followed; verifiers MUST validate the applicable evidence.
- A compiler or publisher signature is not network finality.
- One validator result is not network acceptance.
- No verifier may assume that other validators share its local filesystem or evidence view.

## 15. Versioning

`ConditionV1` and `BuyerStateStatementEvaluationProfileV1` are optional additive protocol objects. Existing event, token, promo, and binding verifiers do not receive these objects and require no acceptance change. The current event/token `protocolVersion` therefore remains `1.0.0-rc.1`.

Changing the identity derivation, canonical ordering, primitive meaning, composition semantics, or required binding rules requires a new Condition schema/profile version. New optional profiles may be registered additively, but unknown profiles MUST be rejected.
