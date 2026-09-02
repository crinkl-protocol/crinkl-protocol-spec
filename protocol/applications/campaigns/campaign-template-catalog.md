---
status: draft
layer: applications
version: vnext
normative: true
implementationStatus: PARTIAL_NON_PRODUCTION_ENGINEERING
---

# Campaign template catalog

A Campaign is a row in this catalog: a composition of `ConditionV1` primitives,
its parameters, the `CampaignEpochV2` purpose slot it fills, and the proof
family that executes it. Marketing names are catalog rows. They are never
schema fields, enum values, circuit identities or public inputs.

This page restores the marketing-alias table that the earlier public
`CAMPAIGN_SPEND_PROOF_PRIMITIVES.md` carried (last full text at public-spec
commit `bb8f021`, removed 2026-08-12), re-expressed over the current grammar in
`../conditions/condition-v1.md` (grammar page, in review as a separate pull request). The internal mirror is
`crinkl-protocol` `protocol/applications/campaigns/CAMPAIGN_TEMPLATE_CATALOG.md`;
the two pages are kept identical in substance, and the internal page is
authority when they differ.

## Reading rules

1. **Executing family.** A template is runnable only when a registered proof
   family executes its exact composition. A family is a circuit identity,
   verifying key, public-input ABI and profile reference. "Planned" means a
   family identity has not been assigned; it is not a promise of a date.
2. **Parameter versus family.** A value is a parameter only when the executing
   family reads it from the committed rule. A value baked into a circuit as a
   constant is not a parameter, however it is labelled.
3. **Positive only.** Every runnable template proves that qualifying purchases
   exist. No template proves absence. Templates whose meaning includes "has not
   purchased" are `BLOCKED — COVERAGE` until an adopted completeness authority
   and a non-membership relation exist; their evaluation is `INDETERMINATE`,
   never `NOT_SATISFIED`.
4. **Purpose slot.** `AUDIENCE` templates fill `CampaignEpochV2.audienceRuleRef`
   and qualify who may be offered something; `CONVERSION` templates fill
   `conversionRuleRef` and establish the purchase a Campaign pays for. The same
   Condition hash may fill either slot; purpose is not part of definition
   identity.
5. **Definition identity.** `definitionRef = conditionId(ConditionV1)`, the
   SHA-256 of the RFC 8785 bytes of the Condition. Two Campaigns that share a
   Condition share a definition reference.

## Registered families at this revision

| Family | Relation | Proof profile | Public inputs | Maturity |
|---|---|---|---|---|
| Atomic product purchase | one purchase of one exact product, brand and category, at a store in a committed set of up to sixteen, inside committed day and time bounds, with minimum quantity, minimum net amount and currency | `campaign.atomicProductPurchase.solanaGroth16.v1`, ref `sha256:720fcfb3af3490ba98d151aa7c334aeb10b23dfc7abf088195cf11430f463c68`, circuit `ATOMIC_PRODUCT_PURCHASE_MATCH_GROTH16_BN254_V1` | `CAMPAIGN_FIELD, CAMPAIGN_EPOCH_FIELD, PURPOSE_FIELD, CLOSED_RULE_COMMITMENT, APPROVED_PURCHASE_ROOT, ENTITLEMENT_NULLIFIER, RESULT_COMMITMENT, RECIPIENT_COMMITMENT` | non-production; one finalized Devnet `ACCEPT` |
| Distinct purchase count, audience | exactly four distinct qualifying purchases inside the inclusive `-44..0` day interval, `CAMPAIGN_INFLUENCED` provenance, one issuer and namespace, positive lower bound only | `campaign.distinctPurchaseCount.audience.groth16.v1`, ref `sha256:95f70a5f920be518cfa8a1d56a6dbccc792eeba8258492014bab1f2afddd7319`, circuit `BUYER_STATE_DISTINCT_PURCHASE_COUNT_GTE_AUDIENCE_GROTH16_BN254_V1` | `CAMPAIGN_FIELD, CAMPAIGN_EPOCH_FIELD, PURPOSE_FIELD, CLOSED_RULE_COMMITMENT, HISTORY_INPUT_COMMITMENT, DISTINCTNESS_COMMITMENT, TEMPORAL_AGGREGATE_COMMITMENT, RESULT_COMMITMENT` | non-production; one finalized Devnet `ACCEPT`; `AUDIENCE` only |
| Set-membership product purchase (planned) | as atomic, with product, brand and category each checked by membership in a committed set root | unassigned | unassigned | design identity only |
| Parameterized purchase count (planned) | at least `N` distinct qualifying purchases inside `-W..0` over a committed set, for `AUDIENCE` or `CONVERSION` | unassigned | unassigned | design identity only |

The earlier public `single-product-purchase-match-v1` conformance package is a
separate draft relation with a different ABI and is not an alias for either
registered family.

## Templates

| Template | Primitive composition | Parameters | Purpose slot | Executing family | Maturity |
|---|---|---|---|---|---|
| Verified purchase | `SPEND_VALIDITY` | issuer set, accepted statuses, window | either | any family (guard) | runnable inside every family; never standalone |
| Exact product purchase | `SPEND_VALIDITY` + `MERCHANT_PRODUCT_CATEGORY_RELATIONSHIP` (`BUYER_STATE_SINGLE_PRODUCT_PURCHASE_V1`) | product, brand, category refs; store set; day and time bounds; minimum quantity; minimum net amount; currency | `CONVERSION` | atomic product purchase | non-production |
| Product-set purchase | as above with product in a committed set | product set root; brand set root; category set root; same bounds | `CONVERSION` | set-membership (planned) | design only; fails closed today |
| Brand purchase | as above with any product of one brand | brand set of one; product set = all of brand | `CONVERSION` | set-membership (planned) | design only; fails closed today |
| Category purchase | as above with any product in a category | category set; product set = all in category | `CONVERSION` or `AUDIENCE` | set-membership (planned) | design only; fails closed today |
| In-window buyer | `SPEND_VALIDITY` + `RECENCY_LIFECYCLE` (`BUYER_STATE_PURCHASE_IN_WINDOW_V1`) | relative window | `AUDIENCE` | atomic or set-membership family via committed time bounds | positive only; compiles onto an existing family's bounds |
| Frequent buyer, four in 45 days | `SPEND_VALIDITY` + `FREQUENCY_INTENSITY` (`BUYER_STATE_DISTINCT_PURCHASE_COUNT_GTE_V1`, `minimumDistinctPurchaseCount = 4`, window `-44..0`) | none beyond the frozen values; issuer and namespace | `AUDIENCE` | distinct purchase count, audience | non-production |
| Repeat buyer at brand, N of W | `SPEND_VALIDITY` + `FREQUENCY_INTENSITY` over a brand set | `N`, `W`, brand set | `AUDIENCE` or `CONVERSION` | parameterized count (planned) | design only; fails closed today. A Platform tally over accepted Outcomes is an application computation, not this template |
| Spend intensity | `SPEND_VALIDITY` + `FREQUENCY_INTENSITY` (`BUYER_STATE_SPEND_TOTAL_CENTS_GTE_V1`) | threshold, currency, window | `AUDIENCE` | none | statement adopted; no family |
| Market buyer | `SPEND_VALIDITY` + `MARKET_CONTEXT` (`BUYER_STATE_PURCHASE_IN_MARKET_V1`) | market entity; window | `AUDIENCE` | none | statement adopted; no family; store geography, not residence |
| Competitor-category buyer, positive | `SPEND_VALIDITY` + `FREQUENCY_INTENSITY` over a competitor category set | `N`, `W`, category set | `AUDIENCE` | parameterized count (planned) | design only |
| Conquest, new-to-brand | competitor-category buyer + `ABSENCE_NON_MEMBERSHIP` on the sponsor brand | as above + coverage window | `AUDIENCE` | none | `BLOCKED — COVERAGE` |
| New-to-brand | `ABSENCE_NON_MEMBERSHIP` on one brand within a coverage window | brand set; coverage window | `AUDIENCE` | none | `BLOCKED — COVERAGE` |
| Lapsed buyer | prior brand purchase + `ABSENCE_NON_MEMBERSHIP` since a cutoff | brand set; lapse window; coverage window | `AUDIENCE` | none | `BLOCKED — COVERAGE` |
| Treated buyer | any positive template + `provenanceRequirement.acceptedEvidenceClasses = [CAMPAIGN_INFLUENCED]` with an authenticated exposure link | exposure policy | `AUDIENCE` | distinct purchase count, audience (only registered provenance-bound family) | non-production |
| Verified conversion after qualification | any `AUDIENCE` template + an exact-product or product-set `CONVERSION` template in one signed Epoch | both sets of parameters | both slots | atomic (conversion leg) + distinct count (audience leg) | compile-only; two-leg Epoch demonstrated in engineering |

Composition of two positive requirements over different purchases in one proof
(`ALL` over several witnesses, `ANY`, `AT_LEAST`) has no registered family. A
template that needs it is design only until a composition profile is adopted.

## What a catalog row is not

- It is not a reward policy. Reward, budget, capacity and settlement terms are
  separate content-addressed policies on the Epoch.
- It is not a runtime capability. Every family above is non-production
  engineering with Devnet evidence only.
- It is not a business claim. A runnable template proves that qualifying
  purchases exist; it does not prove complete history, absence, neutrality,
  causal lift or market supply.

## Sources

- `crinkl-protocol@156d63c37d4d4b9a31287e86d7623afdbe642997`:
  `protocol/applications/schemas/condition_v1.schema.json`,
  `protocol/applications/conditions/BUYER_STATE_CONCRETE_STATEMENTS.md`,
  `protocol/applications/campaigns/CAMPAIGN_ATOMIC_PRODUCT_PURCHASE_GROTH16_PROFILE.md`,
  `protocol/applications/campaigns/CAMPAIGN_DISTINCT_PURCHASE_COUNT_AUDIENCE_GROTH16_PROFILE.md`,
  `protocol/applications/artifacts/distinct_purchase_count_audience_groth16_proof_profile_v1.json`.
- `crinkl-protocol-spec@660dd846`, `protocol/CAMPAIGN_SPEND_PROOF_PRIMITIVES.md`
  and `bb8f021`, `protocol/applications/conditions/campaign-commitment.md`:
  historical six-family grammar and marketing-alias table.
