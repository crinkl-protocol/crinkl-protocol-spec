---
status: draft
layer: applications
version: v1
normative: true
implementationStatus: SPECIFIED_NOT_IMPLEMENTED
---

# Buyer-State Concrete Statements

Mirrored from `crinkl-protocol@156d63c37d4d4b9a31287e86d7623afdbe642997`, `protocol/applications/conditions/BUYER_STATE_CONCRETE_STATEMENTS.md`; the internal page is authority.

This document defines the first Step 9B concrete statement schemas that may be
referenced by `ConditionV1/profile=BUYER_STATE_V1`. It is normative for
implementations that create, resolve, or evaluate one of these statements.

Step 9B defined statement meaning and four exact disclosed-attestation profile
candidates. Step 9C1 separately registers the purchase-window reference
implementation, conformance suite, disclosure policy and replacement profile;
live execution remains unavailable because recipient authority is unresolved.
These documents do not deploy an evaluator, create a portable result or
qualification proof, establish a stable buyer identity, publish aggregate buyer
supply, authorize a campaign, create a nullifier, establish validator finality,
or authorize settlement.

## 1. Shared identity and evaluation boundary

Every statement keeps the existing identity rule:

```text
statementId =
  "sha256:" + SHA-256(RFC8785(statementDefinition))
```

The full strict statement object is the hash preimage. A
`statementEvaluationProfileRef` remains a separate content reference and never
replaces `statementId`.

The four specified profile candidates use `DISCLOSED_SPEND_ATTESTATION`. The
disclosure is permitted only inside the recipient boundary authorized by the
exact profile and relying policy. It is not sponsor disclosure. Each profile
has `deploymentClaim: NONE`, produces only a local tri-state requirement result,
and grants no portable, finality, or economic authority. The original four
candidates remain unavailable and unchanged. Step 9C1 creates a separate
purchase-window profile reference over real registered artifact hashes; its
execution remains unavailable until a live recipient authority and short-lived
authorization independently resolve. Candidate bytes, registration, schema
validity and conformance-only credentials are not execution acceptance.

Every selected Spend must be an accepted cutoff-pinned canonical head under the
Condition and evaluation context. Required canonical fields are exact signed
Spend Attestation fields. Missing, stale, ambiguous, unauthorized, or
unresolvable material yields `INDETERMINATE`; optional Spend fields are never
defaulted to zero, an empty value, or false.

Whenever a Condition requirement carries `relativeWindow`, the evaluator must
apply that exact window to the selected Spend's `canonical.timestamp` using the
bound evaluation-context `asOf`. The amount and purchase-window statements
always require the Condition window. Merchant and market statements apply it
whenever present. An out-of-window selected Spend is `NOT_SATISFIED`; missing,
invalid, current-clock, or substituted cutoff/window/time material is
`INDETERMINATE`.

The Condition's provenance requirement remains authoritative. Campaign-
influenced evidence may satisfy only a Condition that explicitly accepts that
class. A missing influence link does not prove `INDEPENDENT_ORGANIC`, and a
missing exposure does not prove `EXPERIMENTAL_CONTROL`.

## 2. Concrete statements

### 2.1 `BUYER_STATE_MERCHANT_MATCH_V1`

Schema:
[`buyer_state_merchant_match_statement_v1.schema.json`](../../../schemas/experimental/campaigns/buyer_state_merchant_match_statement_v1.schema.json)

The statement asks whether one exact accepted Spend's
`canonical.storeHash` resolves to the named active `MERCHANT` identity under the
exact `storeRegistrySnapshotRef` bound by the evaluation context.

Resolution uses the registered `CRINKL_STORE_HASH_V1` canonical-key namespace.
Free text, display names, aliases, slugs, current mutable lookup, store-location
identity, merchant-category membership, or a later registry snapshot cannot
substitute. A mismatch can establish only that the selected Spend does not
match the named merchant. It does not establish that the scoped subject has
never purchased from that merchant.

The disclosed profile candidate maps this statement to
`MERCHANT_PRODUCT_CATEGORY_RELATIONSHIP`, uses one accepted purchase, and
requires:

- context V1 or V2 plus `storeRegistrySnapshotRef`;
- `canonical.storeHash` and `canonical.timestamp` plus universal Spend/head
  binding fields;
- `MERCHANT_IDENTITY_REGISTRY_V1` and
  `SPEND_ISSUER_AND_CANONICAL_HEAD_SOURCES_V1`; and
- `SPEND_STORE_HASH` and `SPEND_TIME` commerce evidence.

Time is always required because this primitive permits a Condition-relative
window. When the requirement has no window, the timestamp still remains part of
the accepted evidence and cutoff discipline.

### 2.2 `BUYER_STATE_SPEND_TOTAL_CENTS_GTE_V1`

Schema:
[`spend_total_cents_gte_statement_v1.schema.json`](../../../schemas/experimental/campaigns/spend_total_cents_gte_statement_v1.schema.json)

This statement preserves the existing amount-field and threshold vocabulary
but uses a new type so it does not silently change the canonical bytes or
`statementId` of the older `SPEND_TOTAL_CENTS_GTE` catalog statement. It asks
whether one exact accepted Spend has
`canonical.totalCents >= thresholdCents` in the exact declared currency.

`thresholdCents` is a canonical non-negative integer string. Currency must
match exactly; this profile performs no foreign-exchange conversion. Missing
amount, currency, or timestamp is `INDETERMINATE`.

The disclosed profile candidate maps this statement to `FREQUENCY_INTENSITY`, uses one
accepted purchase, and requires:

- context V1 or V2;
- `canonical.totalCents`, `canonical.currency`, and `canonical.timestamp` plus
  universal Spend/head binding fields;
- `SPEND_ISSUER_AND_CANONICAL_HEAD_SOURCES_V1`; and
- `SPEND_AMOUNT` and `SPEND_TIME` commerce evidence.

The Condition requirement supplies the mandatory relative window. The statement
does not duplicate that window.

No registered-ZK buyer-state profile is adopted here. The existing amount
commitment does not by itself bind exact currency, and this repository does not
contain the complete independently pinned verifier artifact and concrete proof
conformance material required by the statement-profile framework.

### 2.3 `BUYER_STATE_PURCHASE_IN_WINDOW_V1`

Schema:
[`buyer_state_purchase_in_window_statement_v1.schema.json`](../../../schemas/experimental/campaigns/buyer_state_purchase_in_window_statement_v1.schema.json)

This statement asks whether one exact accepted Spend's
`canonical.timestamp` falls inside the exact relative window carried by the
Condition requirement. The window is anchored only to the evaluation context's
`asOf`; it never uses verifier `now()`, ingestion time, upload time, verification
time, or mutable Atlas time. Boundaries use the inclusive UTC-day rules in
`CONDITIONS.md`.

The disclosed profile maps this statement to `RECENCY_LIFECYCLE`, uses one
accepted purchase, and requires context V1 or V2, `canonical.timestamp`, the
universal Spend/head source and binding fields, and `SPEND_TIME`.

Step 9C1 registers an exact reference implementation, conformance suite,
recipient disclosure policy, replacement profile and profile registration in
`BUYER_STATE_DISCLOSED_EVALUATOR_REGISTRATION.md` (internal, not yet published).
Its status is `REGISTERED_RECIPIENT_AUTHORITY_UNRESOLVED`; execution is
`UNAVAILABLE`, and `deploymentClaim` remains `NONE`.

This is a positive purchase-in-window claim. It does not prove that the Spend is
the subject's latest purchase, that no later purchase exists, that the subject
is globally active, or that the subject is lapsed or reactivated.

### 2.4 `BUYER_STATE_PURCHASE_IN_MARKET_V1`

Schema:
[`buyer_state_purchase_in_market_statement_v1.schema.json`](../../../schemas/experimental/campaigns/buyer_state_purchase_in_market_statement_v1.schema.json)

This first market statement accepts only the selected Spend's signed
`canonical.cbsaCode`. The exact `marketSnapshotRef` supplies the scheme, dataset
release, market type, code, derivation, and active identity/relationship
material for the named `marketEntityId`.

The disclosed profile candidate maps this statement to `MARKET_CONTEXT`, uses one
accepted purchase, and requires:

- context V1 or V2 plus `marketSnapshotRef`;
- `canonical.cbsaCode` and `canonical.timestamp` plus universal Spend/head
  binding fields;
- `MARKET_REGISTRY_V1` and
  `SPEND_ISSUER_AND_CANONICAL_HEAD_SOURCES_V1`; and
- `PURCHASE_LOCATION_MARKET_IDENTITY` and `SPEND_TIME` commerce evidence.

Merchant headquarters, merchant primary market, routing market, device or IP
location, buyer residence, unresolved city, a five-digit code without the bound
scheme/release, and a later market snapshot cannot substitute. The local result
must not disclose the CBSA or registry path to the sponsor. No registered-ZK
market profile is adopted here.

### 2.5 `BUYER_STATE_DISTINCT_PURCHASE_COUNT_GTE_V1`

Schema:
[`buyer_state_distinct_purchase_count_gte_statement_v1.schema.json`](../../../schemas/experimental/campaigns/buyer_state_distinct_purchase_count_gte_statement_v1.schema.json)

This statement is defined now so its identity and positive lower-bound meaning
are no longer ambiguous. It asks whether at least N publisher-attested private
purchase units were assigned to one publisher-attested scoped subject under the
exact Context V2, C1, C2, and C2b policies and source selection.

`minimumDistinctPurchaseCount` is at least two. Different Spend IDs do not prove
different purchases. The strongest possible result under the currently adopted
source profile is `SATISFIED` for a verified lower bound. Fewer than N accepted
units is `INDETERMINATE`, not `NOT_SATISFIED`, because no complete purchase
universe is established.

The statement does not prove a natural person, holder control, a household,
global or cross-issuer identity, independent real-world transaction uniqueness,
or publisher honesty. Private grouping tags and histories remain inside the
authorized evaluator boundary and are not action nullifiers.

No evaluation profile is adopted for this statement in Step 9B. A future
`AUTHORIZED_PRIVATE_EVALUATOR` profile must bind a real independently selected
evaluator authority, immutable implementation, conformance suite, private-input
access policy, output-disclosure policy, Context V2, one exact namespace/issuer
pair, and the complete request/checkpoint/selection path. Until those artifacts
exist and are independently pinned, evaluation is `INDETERMINATE`.

### 2.6 `BUYER_STATE_SINGLE_PRODUCT_PURCHASE_V1`

Schema:
[`buyer_state_single_product_purchase_statement_v1.schema.json`](../../../schemas/experimental/campaigns/buyer_state_single_product_purchase_statement_v1.schema.json)

This statement asks whether one exact accepted product-purchase attestation
contains the exact product, brand and category references and meets the minimum
quantity and minimum net product amount in the exact currency. Its Condition
requirement supplies the mandatory relative window; the statement does not
duplicate it.

The statement maps only to `MERCHANT_PRODUCT_CATEGORY_RELATIONSHIP`. The first
profile requires one `SPEND_VALIDITY` guard, this one non-guard requirement and
`ALL` composition. That exact profile binds all predicates to the same accepted
Spend and product-purchase witness, so it does not inherit the general
separate-witness limitation described in Section 3.

The positive source and correction/status boundary are defined in
`BUYER_STATE_PRODUCT_PURCHASE_SOURCES.md` (internal, not yet published).
The Campaign-level Groth16 relation and exact Condition/Epoch mapping are
defined in
`CAMPAIGN_SINGLE_PRODUCT_PURCHASE_GROTH16_PROFILE.md` (internal, not yet published).

The source and proof profile are protocol-defined candidates with executable
sealed-alpha lineage, but live selection remains unavailable pending human
adoption, holder/prover authorization, program/VK admission and Platform reader
integration. A schema-valid statement or proof-profile reference alone cannot
produce a result.

## 3. Requirement composition and witness identity

Each statement profile evaluates one Condition requirement. Separate merchant,
amount, time, or market requirements may be satisfied by different accepted
Spend inputs. `ConditionV1` composition does not currently assert that all
requirements share one purchase witness.

Therefore an implementation must not describe a composed result as "one
purchase at merchant M, over amount A, in window W, and in market X" unless a
separately adopted composition or result profile binds the same accepted Spend
identity across those requirements. Step 9B establishes no such shared-witness
profile.

## 4. Deliberately unavailable statements

The following remain unavailable and must evaluate to `INDETERMINATE`:

- product, brand, category, or competitor claims outside the exact
  `BUYER_STATE_SINGLE_PRODUCT_PURCHASE_V1` source/profile; the defined profile
  itself remains runtime-unavailable until its named activation gates pass;
- new-to, lapsed, no-sponsor, and other absence or non-membership claims,
  because no completeness-capable evidence source is adopted;
- independent-organic or experimental-control classification inferred from a
  missing influence or exposure record;
- buyer residence inferred from purchase, store, merchant, routing, device, or
  IP geography; and
- any claim that a local requirement result is a portable qualification proof,
  validator finality, campaign authorization, reward decision, or settlement
  authority.

Existing platform promo booleans, JSON Logic, SQL segment counts, Atlas labels,
hosted verifier responses, and draft specification objects remain adapter or
design candidates. Matching a field name does not promote them to this
protocol's authority.

## 5. Compatibility and next authority

These objects are additive under protocol version `1.0.0-rc.1`. They do not
change existing Spend, Condition, evaluation-context, registry, campaign,
proof, or settlement bytes.

Step 9C1 does not complete roadmap Step 9. It registers purchase-window
semantics and conformance without live recipient authority. Remaining work
includes live authorization/deployment review, the private distinct-count
evaluator authority, activation review for the single-product source/Groth16
profile, broader product/category relations, absence/completeness sources and
profiles, and additional reviewed ZK profiles. Step 10 must separately define
any portable minimum-disclosure result or qualification proof.
