---
status: draft
layer: governance
version: v1
normative: true
---

# Protocol, Business, and Onchain Boundary

This document defines the classification that every Crinkl protocol or
requirements change MUST complete before its semantics are accepted.

The protocol/business boundary and the onchain/offchain boundary are different
decisions:

- **Protocol** describes stable facts, artifacts, and verification rules on
  which independent parties rely.
- **Business** describes objectives, prices, operating policies, targeting
  choices, workflow, reporting, and decisions made by a particular deployment.
- **Onchain** is a deployment and enforcement choice for the smallest protocol
  or economic state that requires public ordering, custody, non-equivocation,
  replay prevention, or composability.
- **Offchain** is where private evidence, computation, workflow, and reporting
  normally remain. Offchain protocol verification is still protocol behavior.

Neither "protocol" nor "business" means "onchain". A protocol artifact may be
created and verified entirely offchain. A business parameter may be committed
onchain when it controls funded settlement, without becoming a universal
protocol policy.

## Classification Test

A proposed field, rule, object, or requirement belongs at the protocol level
when at least one of these statements is true:

1. An independent verifier needs a stable definition to accept or reject it.
2. It changes the meaning, validity, lineage, replay safety, or authority of a
   portable proof or settlement artifact.
3. Two parties could otherwise present conflicting versions of the same rule or
   outcome during a dispute.
4. It determines whether a committed outcome can be settled or consumed.
5. Implementations must interpret it identically to interoperate safely.

A proposed value or decision normally belongs at the business layer when it:

1. selects a product, category, audience, retailer, channel, market, campaign
   size, intervention, price, budget, margin threshold, or reporting view;
2. ranks, forecasts, optimizes, or recommends opportunities;
3. controls operator permissions or workflow without changing portable proof
   validity; or
4. computes a commercial metric that no external party is expected to verify
   from a defined evidence contract.

Business inputs that affect eligibility, assignment, attribution, conversion,
or settlement MUST be frozen or referenced by a protocol artifact before they
are used as proof-bearing facts. The protocol defines how those selected values
are bound and verified; it does not choose the values for the business.

## Onchain Routing Test

Protocol state SHOULD be committed or executed onchain only when the deployment
requires one or more of these properties:

- custody or release of value;
- public budget debit or settlement;
- globally ordered replay/nullifier state;
- public non-equivocation or immutable rule history;
- public authority or finality state; or
- composable state for another program.

Raw receipts, OCR, private line items, identity, buyer histories, model state,
audience discovery, campaign planning, user experience, and detailed reporting
MUST NOT be placed onchain merely because they contribute to a protocol proof.
Where private offchain facts affect public settlement, the public artifact
SHOULD bind only the minimum hash, root, certificate, nullifier, or aggregate
needed for verification.

## Required Change Record

Every pull request that changes normative prose, requirements, schemas,
bindings, conformance artifacts, formal models, or declared maturity MUST
include a **Boundary impact** record containing all of the following:

1. **Business policy** — the deployment-specific choices affected, or a reason
   none are affected.
2. **Protocol artifacts** — the portable objects, fields, hashes, statements,
   events, schemas, or verifier rules affected, or a reason none are affected.
3. **Offchain state and computation** — what remains private, mutable, derived,
   or implementation-specific.
4. **Onchain commitment or execution** — the minimum state routed onchain and
   why, or an explicit reason no onchain state is required.
5. **Verification and disputes** — who can verify the claim, from which
   evidence, under which authority, and what happens when evidence is missing,
   corrected, returned, replayed, or disputed.
6. **Maturity and adoption** — whether the change is adopted protocol behavior,
   an optional profile, experimental material, or an implementation proposal,
   including its version impact.

The record MUST describe the actual change. Blank answers, placeholders, or an
unexplained "N/A" do not satisfy the requirement. "None" is acceptable only
with a reason.

Reviewers MUST reject a change when:

- a business label is presented as proof truth without a finite verification
  rule;
- a selected commercial value is hard-coded as universal protocol policy;
- protocol validity depends on private implementation state that a stated
  verifier cannot obtain or validate;
- onchain placement is used as a substitute for defining evidence, authority,
  correction, or dispute semantics;
- a report claims attribution or incrementality beyond the treatment,
  assignment, conversion, return-window, and estimator evidence actually bound;
  or
- draft or experimental content is described as adopted or released behavior.

## Requirements Writing Rules

Requirements MUST identify the subject of each normative keyword. For example:

- "A campaign operator MUST select one market" is a business-profile
  requirement.
- "`CampaignRuleV1` MUST bind `marketScope`" is a protocol artifact
  requirement.
- "A settlement program MUST reject a reused nullifier" is an onchain execution
  requirement for deployments claiming that binding.

A requirement MUST NOT imply that an offchain fact is unimportant. Privacy,
measurement, assignment, estimator, return-window, and reporting rules may stay
offchain while remaining necessary business or conformance requirements. If an
external party is expected to reproduce a result, the specification MUST define
the input commitments, method/version, authority, and failure state needed to
do so.

## Campaign Example

For a controlled product campaign:

| Decision or artifact | Classification |
| --- | --- |
| Product, retailer/channel, market, target population size, intervention, price, and margin objective | Business policy |
| Frozen audience, assignment, conversion, return-window, and settlement parameters | Business inputs bound by protocol artifacts |
| Receipt evidence, eligibility computation, treatment/control construction, estimator execution, confidence calculation, and detailed reporting | Normally offchain |
| Qualification proof, assignment commitment, verified conversion, correction/return status, result-method reference, approval, and settlement leaf | Protocol artifacts when independently verified or disputed |
| Funded campaign state, rule hash, settlement root, budget debit, nullifier, and payout/claim state | Optional onchain commitment or execution when public economic enforcement is required |

This classification lets the business choose and operate the campaign while the
protocol makes the relied-upon facts portable, replay-safe, and auditable.
