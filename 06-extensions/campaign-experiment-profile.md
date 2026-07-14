---
status: publication-draft
layer: optional-extension
version: campaign-experiment-profile-v1
normative: true
---

# Campaign Experiment Profile

> **Maturity: public publication draft; not part of released `v1.0.0-rc.2` conformance.**
>
> Adopted engineering source: `crinkl-protocol` commit `40dc0e8c23826a48d579cae1c30ca0dbefba13ef`, `protocol/CAMPAIGN_EXPERIMENT_PROFILE.md`, `CampaignExperimentPolicyV1` schema, and its conformance vectors.
>
> This page publishes the intended public meaning and implementation boundary. It does not publish the exact schema bytes or vectors into this repository, declare runtime availability, or change the global `protocolVersion`. A later release must vendor and pin the exact adopted artifacts before public verifier conformance may be claimed.

## Purpose

The Campaign Experiment Profile defines the smallest cross-vertical experiment binding over one immutable Campaign Epoch. It is not a CPG Campaign, restaurant Campaign, offer wall, audience list, causal estimator, finance report, settlement profile, runtime, or deployment.

The shared experiment is:

```text
one Campaign Epoch and exact pre-state evaluation context
+ one deterministic, exclusive, pre-exposure arm rule
+ one immutable intervention-policy reference per arm
+ the Epoch's common conversion and timing boundary
+ one exposure-coverage policy reference
+ one measurement-method reference
= one reproducible Campaign experiment policy
```

Product, retailer, merchant, category, market, channel, incentive, allocation, sample-size, confidence, margin, and report choices are campaign-defined values. The protocol freezes relied-upon references and verification rules; it does not choose commercially correct values.

## Public maturity and source authority

This repository owns the public specification claim at the maturity declared above. `crinkl-protocol` owns the adopted engineering object, exact schema bytes, canonical hashes, signatures, vectors, and current conformance behavior.

The adopted `CampaignExperimentPolicyV1` bytes carry `protocol.protocolVersion = "1.0.0-rc.1"`. This repository's current documentation release marker `v1.0.0-rc.2` does not rewrite those bytes or silently create a second object. A later public release must state its exact compatibility/acceptance effect while preserving the adopted canonical object.

Until a public release vendors those exact artifacts:

- this page is a normative publication draft, not released public conformance;
- implementers must use the adopted engineering source for exact bytes;
- no implementation may claim `v1.0.0-rc.2` Campaign Experiment conformance from this page alone; and
- a difference between this page and the adopted engineering artifacts is a publication defect to be reconciled, not permission to choose either meaning opportunistically.

## Legacy public CampaignEpoch disambiguation

The conceptual `CampaignEpochV1` shape in `../04-condition-layer/campaign-commitment.md` and `../schemas/experimental/campaign-epoch.v1.schema.json` is an earlier public experimental candidate. It uses fields such as `epochId`, `ruleSetHash`, `fundingTrancheId`, `issuerAuthority`, and `claimLevel`. It is not the exact signed adopted engineering `CampaignEpochV1` referenced by `CampaignExperimentPolicyV1`.

For this profile:

- the legacy experimental schema MUST NOT be used as the resolved Campaign Epoch;
- the exact adopted signed Epoch, evaluation-context, and experiment-policy artifacts MUST be used;
- the legacy `claimLevel = "INCREMENTAL"` candidate does not make a receipt, conversion, or Epoch intrinsically incremental; and
- incrementality remains a cohort- or market-level derived result under the frozen measurement method. The adopted Campaign Epoch supplies only its declared maximum conversion-claim ceiling.

The legacy candidate remains historical public material until separately deprecated or replaced. Its similar name does not grant wire compatibility or adopted status.

## Protocol and business-layer split

| Protocol requirement | Business/offchain choice |
|---|---|
| exact content references, versions, canonical hashes, signatures, authorities, non-equivocation, correction and cutoff bindings | target product/merchant/category/market/channel and commercial objective |
| exact pre-state Condition and evaluation context | audience-size feasibility and selected eligibility values |
| deterministic exclusive pre-exposure assignment scope and replay/nullifier rule | allocation ratio selected within the adopted policy bounds |
| one immutable intervention-policy reference per arm | benefit, message, price, creative, and delivery operations |
| exposure-coverage and measurement-method references | estimator implementation, sample sufficiency, confidence convention, margin model, report, and rerun decision |
| claim ceilings and failure behavior | commercial success threshold and budget-owner approval |

Offchain does not mean optional or unimportant. A private/offchain rule becomes a protocol concern when another party must reproduce, verify, settle, dispute, or rely on it without trusting the operator that selected it.

No onchain commitment is required merely to define the experiment. Funding, settlement, replay, custody, or public non-equivocation may be routed onchain only under a separately adopted binding. Raw receipts, buyer histories, audience construction, estimator execution, and detailed reporting remain offchain.

## Required artifact relationships

A conforming verifier must resolve and validate:

1. one exact signed `CampaignExperimentPolicyV1`;
2. its exact signed adopted `CampaignEpochV1`;
3. its exact `BuyerStateEvaluationContextV1` or `V2`;
4. `evaluationContext.conditionId == campaignEpoch.preStateConditionRef`;
5. `campaignEpoch.issuedAt <= experimentPolicy.issuedAt <= campaignEpoch.effectiveFrom`;
6. the canonical experiment-policy reference and non-circular assignment-scope derivation;
7. exactly two ordered arms, `CONTROL` then `TREATMENT`, with distinct intervention-policy references;
8. `1 <= rolloutThreshold < variantCount` and the fixed bucket rule;
9. current authority, key-scope, key-status, and independent pre-exposure publication acceptance;
10. same-position non-equivocation for `(experimentAuthorityRef, experimentId)`; and
11. every intervention, coverage, measurement, Epoch-policy, registry, evidence-source, and correction artifact required by the relying use.

Missing, stale, unauthorized, mismatched, forked, unverified, or unavailable required material is rejected or `INDETERMINATE`. A verifier must not fill missing proof material from business intent or implementation defaults.

## Assignment contract

The existing private-holder rollout proof interface supplies a scope-specific nullifier, deterministic bucket, modulus, threshold, and arm result. The proof scope must equal the canonical assignment scope of the exact experiment policy.

Before any arm-specific intervention or relying action, the implementation must:

```text
accept exact policy, Epoch, context, authority, and publication evidence
-> accept eligibility under the exact pre-state context
-> verify the rollout proof and policy-bound outputs
-> durably and exclusively commit (assignmentScopeId, nullifier)
-> return or perform the arm-specific action
```

The durable assignment is implementation-local. This publication draft does not adopt a portable assignment object, storage schema, API, table, route, service, queue, cloud, or chain.

An identical retry may return the committed assignment. A retry that would change the policy reference, bucket, or arm for the same scope/nullifier pair must fail closed; it must not overwrite or select a convenient arm. The nullifier remains scope-specific and must not become a stable participant or cross-experiment correlation identifier.

## Assignment, exposure, outcome, and incrementality

These are separate facts:

- assignment identifies the arm whose intervention policy applies;
- assignment does not prove delivery or qualifying exposure;
- control-arm assignment does not prove no qualifying exposure;
- policy-valid control classification additionally requires the declared exposure universe and a valid no-qualifying-exposure result;
- missing or positive-only exposure data is `INDETERMINATE`, not control;
- an accepted commerce outcome remains bounded by the Epoch's conversion, timing, attribution, evidence, correction, and deduplication rules; and
- incrementality is a cohort- or market-level result under the frozen measurement method, never a field on one receipt, Spend Attestation, assignment, conversion, reward, settlement, or payout.

Observed conversion, modeled or estimated lift, and controlled incrementality must not be represented as interchangeable claim strengths. Cryptographic validity does not upgrade evidence completeness or causal strength; estimator and report semantics remain governed by the frozen method and business/offchain reporting contract.

## Cross-vertical acceptance matrix

| Position | Product/CPG value | Restaurant value | Shared representation |
|---|---|---|---|
| Target | one product, retailer/channel, market | one merchant/location set, visit channel/daypart, market | Epoch, registry, and entity-set references |
| Eligibility | recent category buyers plus exclusions | recent category diners plus exclusions | one Condition and exact evaluation context |
| Arms | control and product intervention | control and visit intervention | one deterministic exclusive assignment scope |
| Intervention | benefit, message, or no-benefit policy | benefit, message, or no-benefit policy | immutable intervention-policy reference per arm |
| Outcome | product purchase within window and return/correction boundary | merchant/location purchase within window and correction boundary | common conversion, timing, attribution, evidence, correction, and deduplication policies |
| Measurement | cohort buyer/unit lift | cohort diner/visit lift | frozen measurement-method reference |
| Economics | cost per incremental buyer and contribution margin | cost per incremental diner and contribution margin | business/offchain report, not experiment-policy fields |

The profile is cross-vertical only if both examples use the same exact schema and differ through referenced identities and campaign values. A `verticalType`, restaurant object, CPG object, SKU field, menu-item field, universal sample size, confidence target, estimator, margin formula, or report layout must not be added to the experiment policy.

V1 is exactly two-arm: one `CONTROL` and one `TREATMENT`. An arbitrary multi-arm or shared-control experiment requires a separately adopted profile version. Unrelated two-arm policies must not be combined after outcomes are visible and represented as one precommitted multi-arm experiment.

Current Spend Attestation evidence does not itself establish canonical product or line-item truth. A product-level CPG conversion remains unavailable until separately accepted product-purchase and return/correction evidence exists. That is an evidence-profile gap, not an experiment-policy gap.

## Runtime availability gate

A deployment must not claim this profile is available until it names and validates the components required for the claims it exposes:

- exact artifact and current authority/publication resolution;
- pre-state Buyer State evaluation;
- rollout-proof verification;
- durable exclusive pre-action assignment;
- intervention resolution and arm-specific action;
- exposure-source coverage for exposure/control claims;
- corrected outcome evidence for conversion claims; and
- frozen method execution plus sufficient cohort/market evidence for incrementality claims.

A database row, endpoint, feature flag, UI label, receipt, reward, or analytics event alone does not satisfy this gate.

## Public release gate

Public verifier conformance remains unavailable until a later release:

1. vendors the exact adopted Epoch, evaluation-context, and experiment-policy schemas;
2. vendors the exact canonicalization, hash, signature, scope, cross-binding, and adversarial vectors;
3. lists those artifacts in the public conformance manifest and verifier suite;
4. records the release/version effect in the changelog and version snapshot; and
5. proves no unresolved conflict with the legacy experimental CampaignEpoch material.

Passing schema/vector checks would establish artifact interoperability only. It would not establish commercial soundness, source completeness, assignment timing in a live system, product-level evidence, statistical power, causal validity, runtime deployment, or production availability.

## Boundary impact

- **Business policy:** no product, merchant, category, market, allocation, intervention, sample-size, confidence, margin, pricing, or report value is selected.
- **Protocol artifacts:** this publication draft describes the already adopted engineering Campaign experiment composition; it introduces no new public schema bytes in this repository.
- **Offchain state and computation:** eligibility evaluation, assignment persistence, evidence joins, exposure coverage, estimator execution, uncertainty, economics, and reporting remain offchain.
- **Onchain commitment or execution:** none is required or introduced.
- **Verification and disputes:** exact references, authority/publication acceptance, nullifier exclusivity, failure boundaries, correction material, and claim ceilings are stated; unavailable evidence fails closed.
- **Maturity and adoption:** adopted engineering profile; public publication draft; not released in `v1.0.0-rc.2`; runtime unavailable.
