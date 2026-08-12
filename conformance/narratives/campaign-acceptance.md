---
status: draft
layer: conformance
version: vnext
normative: true
implementationStatus: SPECIFIED_NOT_IMPLEMENTED
---

# Campaign acceptance narratives

These narratives test required composition and failure behavior. They are
normative target requirements but are not claims of current runtime support.

## 1. Monster treatment/holdout Campaign

### Committed terms

Monster's `CampaignEpochV2` commits:

- audience rule: verified Celsius or Red Bull buyer during the prior 30 days;
- optional exclusion rule: no Monster purchase within an exact
  observable-history boundary;
- audience proof profile supporting the positive and optional bounded-absence
  relation;
- assignment policy: 50% treatment and 50% holdout under one deterministic
  assignment profile;
- one intervention policy per arm: offer for treatment, no Campaign offer for
  holdout;
- conversion rule: verified Monster purchase within 14 days of the committed
  Campaign timing event;
- conversion proof profile;
- treatment reward: 1,000 points;
- no reward for holdout;
- reuse, observation, measurement, resolution, and dispute policies; and
- Campaign authority and required registry references.

The user holds a Celsius Spend Token.

### Flow

```text
Celsius SpendToken
+ Monster CampaignEpoch
-> ProofOfMatch(AUDIENCE)
-> ValidatorCertificate
-> deterministic AssignmentRecordV1
-> treatment user sees offer; holdout user does not
-> user buys Monster
-> Verification Issuer creates Monster SpendToken
-> ProofOfMatch(CONVERSION)
-> ValidatorCertificate
-> CampaignOutcome
    |-- treatment conversion: measurement -> RewardObligation(1,000 points)
    |                           -> SettlementRecord
    `-- holdout conversion: measurement only
```

This narrative uses a portable `AssignmentRecordV1` because offer delivery and
measurement are independent consumers and the assignment must remain available
for replay and dispute. A single-authority implementation with no independent
consumer could retain the same deterministic result as application state
instead, but it would not serialize or claim an `AssignmentRecordV1`.

### Required acceptance checks

1. The audience proof binds the exact Monster Epoch, audience rule commitment,
   Celsius token/head, issuer, verification policy, 30-day window, scope, proof
   profile, and nullifiers.
2. If the exclusion is enabled, the Epoch and proof bind the exact issuer/source
   set, canonical-head snapshot/cutoff, accepted statuses, correction policy,
   30-day or other declared observation interval, and unavailable-source rule.
3. Merely omitting a Monster token is rejected; the proof establishes absence
   only inside the declared boundary, not global nonexistence.
4. The audience Validator Certificate identifies the exact proof hash and
   `PROOF_OF_MATCH_VERIFICATION`. It creates no assignment.
5. Assignment is computed from the Epoch policy before exposure. When a
   portable `AssignmentRecordV1` is used, an independent consumer can recompute
   its digest, bucket, and arm from resolved seed material and canonical
   assignment inputs, and can verify that seed was committed before exposure.
6. Assignment and exposure remain separate. Treatment assignment without a
   delivered offer is not treatment exposure; holdout assignment alone is not
   proof that no external exposure occurred.
7. The conversion proof binds the newly issued Monster Spend Token, exact
   conversion rule/profile, Epoch, canonical head/status, conversion window,
   and purchase/entitlement nullifiers.
8. The Outcome references both accepted match proofs where applicable,
   assignment state, optional exposure state, and the conversion proof. No
   economic-admission step is required for this uncapped example.
9. A treatment Outcome creates exactly a 1,000-point Reward Obligation. The
   Outcome producer cannot choose zero, 500, or 2,000 points.
10. A holdout Outcome contributes to measurement and creates no Reward
    Obligation.
11. The Settlement Record resolves only an existing treatment obligation. It
    does not retroactively create eligibility or conversion acceptance.

### Required rejection cases

- audience proof uses the conversion rule commitment or wrong Epoch;
- proof profile or verifying key differs from the Epoch requirement;
- observable-history coverage is missing while absence is claimed;
- assignment is recomputed after exposure or changes arm on retry;
- exposure is inferred from assignment;
- corrected/invalidated Monster head falls outside the accepted status policy;
- a certificate refers to a different proof hash;
- holdout Outcome creates a reward;
- treatment Outcome changes the committed amount; or
- settlement proceeds without an exact Reward Obligation.

## 2. Direct Monster promotion

Business statement:

```text
Anyone who buys Monster receives 1,000 points.
```

The Epoch has no audience rule, assignment policy, experiment arm, exposure
requirement, or economic-admission policy. It commits the Monster conversion
rule/profile, 1,000-point reward, timing, reuse, resolution, dispute, authority,
and registry references.

```text
CampaignEpoch
-> Monster SpendToken
-> ProofOfMatch(CONVERSION)
-> ValidatorCertificate
-> CampaignOutcome
-> RewardObligation
-> SettlementRecord
```

Conformance requires:

- `CampaignEpochV2.audienceRuleRef = null`;
- `requiredProofProfiles.audienceProofProfileRef = null`;
- `assignmentPolicyRef = null`;
- `economicAdmissionPolicyRef = null`;
- `CampaignOutcomeV1.audienceMatch = null`;
- `CampaignOutcomeV1.assignment = null`;
- `CampaignOutcomeV1.exposureRef = null`;
- `CampaignOutcomeV1.economicAdmission.required = false` and
  `decision = NOT_REQUIRED`; and
- a valid Outcome deterministically creates the exact 1,000-point obligation.

A verifier that requires an audience proof, experiment assignment, or Campaign
quorum-admission certificate for this mode is non-conforming unless a separate
profile names the distinct dependency.

## 3. Capacity-limited Liquid Death promotion

Business statement:

```text
Buy three distinct Liquid Death purchases totaling at least $30
within 21 days and receive 2,000 points.

Limited to the first 10,000 qualifying buyers.
```

### Epoch commitments

The Epoch commits:

- conversion rule: at least three distinct accepted Liquid Death purchases;
- a 21-day window and exact boundary timestamp rule;
- aggregate value at least 3,000 USD cents under a named currency,
  normalization, rounding, and overflow policy;
- accepted issuers, verification policies, statuses, and correction rules;
- a multi-input conversion proof profile;
- purchase-distinctness and purchase-reuse policy;
- 2,000-point reward policy;
- economic-admission policy with capacity exactly 10,000;
- authoritative capacity-ledger reference and authority;
- total ordering, concurrency, retry, reservation, correction, and expiry rules;
- entitlement-nullifier registry and reuse scope;
- funding/budget, resolution, and dispute policies; and
- Campaign authority and registries.

For this narrative, “first” means the order in which complete, valid admission
attempts commit atomically to the named capacity ledger—not receipt purchase
time, proof creation time, operator wall-clock observation, or UI arrival. A
different meaning requires a different committed allocation policy with an
independently auditable ordering source and tie-break rule.

### Proof validity

```text
three or more SpendTokens
+ Liquid Death CampaignEpoch
-> ProofOfMatch(CONVERSION)
-> ValidatorCertificate
```

The proof relation must establish:

1. every token/head is authentic under its issuer and verification policy;
2. every accepted canonical head is within the committed status/correction
   policy;
3. at least three inputs represent distinct purchases under the committed
   purchase identity rule;
4. a corrected successor of one purchase cannot count as a second purchase;
5. all counted purchases fall inside the same committed 21-day relation;
6. normalized values sum without overflow to at least 3,000 USD cents;
7. the input set and aggregate commitments cover exactly the counted inputs;
8. each purchase-reuse nullifier is correctly scoped; and
9. the entitlement nullifier is correctly derived for this Campaign claim.

Multi-issuer inputs are accepted only if the proof profile resolves and composes
every issuer and policy. Three token references without a valid aggregate proof
do not satisfy the rule.

The Validator Certificate establishes quorum acceptance of this proof only. It
does not reserve one of 10,000 positions.

### Deterministic economic admission

The committed capacity ledger is the authoritative state. It maintains a
hash-chained or otherwise content-addressed total order of admission attempts
under one named authority. One atomic transaction must:

1. reject or idempotently return an existing row for the same entitlement
   nullifier;
2. verify the proof and certificate references match the attempt;
3. assign the next monotonic admission sequence under the committed ordering
   rule;
4. test that admitted count is below 10,000;
5. reserve the exact 2,000-point/funding capacity when required; and
6. record `ADMITTED` or `REJECTED` with the resulting state and evidence hashes.

Concurrent different claims are serialized by that transaction. Equal retries
are idempotent; a conflicting payload with the same entitlement nullifier is
rejected. The policy must state how a failed funding reservation, timeout,
correction, reversal, or abandoned attempt affects capacity. Operator wall-clock
arrival, an in-memory queue, or UI display order cannot silently override the
committed ordering rule.

No universal standalone economic-admission object is required. The
authoritative ledger row is the state transition; `CampaignOutcomeV1` carries
its policy, state, evidence, decision, and time references, while the Outcome's
`nullifiers` projection binds the entitlement nullifier. A separate portable
artifact is justified only if an independent
consumer cannot authenticate those references under the applicable profile.

### Outcomes

For positions 1 through 10,000:

```text
accepted conversion proof
+ ADMITTED economic admission
-> CampaignOutcome(conversionVerified=true, rewardObligation.created=true)
-> RewardObligation(2,000 points)
-> SettlementRecord
```

After capacity is exhausted:

```text
accepted conversion proof
+ REJECTED economic admission
-> CampaignOutcome(conversionVerified=true, rewardObligation.created=false)
```

The later valid proof remains cryptographically valid. It creates no economic
entitlement and no Reward Obligation because the signed Epoch made entitlement
capacity-dependent.

### Required rejection cases

- duplicate token/head or corrected versions of one purchase counted twice;
- value or time aggregation performed only by unbound package metadata;
- unsupported issuer mixed into the proof;
- purchase-reuse or entitlement-nullifier conflict;
- capacity decision made from a stale non-authoritative counter;
- two concurrent claims both receive sequence 10,000;
- a rejected admission creates a Reward Obligation;
- admitted amount differs from 2,000 points;
- admission succeeds without an atomic funding reservation when policy requires
  one; or
- settlement record omits the exact obligation and entitlement nullifier.

## 4. Reporting boundary

Monster lift reporting consumes assignment, exposure coverage, and Outcomes.
Liquid Death capacity reporting also consumes admission decisions. A report may
calculate cohort conversion or incremental lift under a frozen method, but no
individual Spend Token, proof, certificate, Outcome, Obligation, or Settlement
Record is intrinsically incremental.
