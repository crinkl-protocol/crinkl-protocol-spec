---
status: draft
layer: predicate
version: v1
normative: true
---

# Condition

This page is the entry point for campaign rule grammar. The current grammar is
[`ConditionV1`](./condition-v1.md). The earlier "Spend Predicate" text below is
kept as historical context only.

## Historical context: Spend Predicate

A Spend Predicate is a rule over one or more Spend Attestations. Spend Predicates are downstream of attestations: they do not create spend truth and they do not mint Spend Attestation Tokens.

The `SpendPredicateV1` envelope in
[`schemas/spend_predicate_v1.schema.json`](./schemas/spend_predicate_v1.schema.json)
is an earlier candidate for that idea. It is **not** the grammar that
`CampaignEpochV2.audienceRuleRef` and `CampaignEpochV2.conversionRuleRef`
refer to. Those references are `conditionId(ConditionV1)`, the content address
of a `ConditionV1` object, as stated in the
[Campaign architecture](../campaigns/README.md). The earlier `predicateId` /
`predicateHash` reference model is not used by `CampaignEpochV2`.

## Current grammar: `ConditionV1`

[`condition-v1.md`](./condition-v1.md) defines `ConditionV1`
(`domain = "crinkl:condition:v1"`, `profile = "BUYER_STATE_V1"`), its
`conditionId` identity rule, canonical ordering, tri-state evaluation, time
semantics, evidence provenance, and evaluation context. The schema is
[`condition_v1.schema.json`](../../../schemas/experimental/campaigns/condition_v1.schema.json).

A `BUYER_STATE_V1` Condition composes requirements drawn from exactly six
primitives:

| Primitive | Meaning |
|---|---|
| `SPEND_VALIDITY` | Every Spend Attestation input used by another requirement is an accepted canonical head under the evaluation context; an unconditional guard, present exactly once. |
| `MERCHANT_PRODUCT_CATEGORY_RELATIONSHIP` | Accepted evidence establishes the relationship encoded by a registered statement over merchant, store, brand, product, or category material. |
| `FREQUENCY_INTENSITY` | Accepted evidence establishes a count or spend-intensity statement over distinct purchase units inside a required relative window. |
| `RECENCY_LIFECYCLE` | Accepted evidence establishes a recency or ordered lifecycle statement inside a required relative window. |
| `MARKET_CONTEXT` | Accepted evidence establishes a market/context statement under a bound market snapshot or equivalent committed set. |
| `ABSENCE_NON_MEMBERSHIP` | An accepted completeness or non-membership profile establishes an absence statement inside the declared window; the only permitted negative meaning. |

Non-guard requirements are combined with one of three composition operators:

- `ALL` — every named non-guard requirement is satisfied;
- `ANY` — at least one named non-guard requirement is satisfied;
- `AT_LEAST` — at least `minimumSatisfied` named non-guard requirements are satisfied.

There is no general `NOT` operator, and `OUTCOME_CONVERSION` is deliberately
not a buyer-state primitive: the post-action outcome lives in
`CampaignEpochV2.conversionRuleRef`, not in the pre-action buyer state.

Concrete statement types that a requirement's `statementId` may bind are
defined in [`buyer-state-statements-v1.md`](./buyer-state-statements-v1.md);
the typed policy artifacts the evaluation context references are defined in
[`buyer-state-evaluation-policies-v1.md`](./buyer-state-evaluation-policies-v1.md).

Conditions remain downstream of Core Spend Attestation validity. A Condition
MUST NOT rewrite Spend Attestation Token fields, change verification state, or
move reward logic into Core.
