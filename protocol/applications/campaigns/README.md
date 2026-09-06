---
status: draft
layer: applications
version: vnext
normative: true
implementationStatus: PARTIAL_NON_PRODUCTION_ENGINEERING
---

# Campaign protocol architecture

This document defines the target Campaign vocabulary. It composes existing
Spend evidence without changing Spend Token issuance, verification-policy,
issuer-key-history, attestation-status, or Spend Stream rules.

The schemas and procedure profile in
[`schemas/experimental/campaigns/`](../../../schemas/experimental/campaigns/)
and
[`protocol/applications/artifacts/`](../artifacts/)
describe an earlier public Campaign candidate anchored at
`crinkl-protocol@bdac6d3f9f32a312544b3adadbb379f98607198f`. They do not mirror
the current non-production substrate byte-for-byte. Current reviewed
engineering is anchored at `crinkl-protocol@47d0e358bb10e261dd8ab41c096cf3deaa8e333c`
and `crinkl-platform@2a3a7d6eaf1f7ef9a609ca997951bf3960b17975`.

Neither the older public candidate nor the current engineering families are in
a released public manifest, runtime-enabled, deployed to production, or an
economic authorization. Discarded Campaign drafts are not supported
predecessors. This refactor does not change Spend Token or SOFT-to-HARD
verification compatibility. That scoped protection is not a claim that those
are the only wire- or production-sensitive Crinkl surfaces; each artifact is
evaluated against its actual consumers, persisted state, release identity, and
deployed dependencies.

A compact forked flow is available in the
[`Campaign architecture diagram`](../../../diagrams/campaign-architecture.md).

## 0. Current reviewed substrate boundary

The current non-production compiler uses the existing Condition content
address as the purpose-free Campaign definition identity:

```text
definitionRef = conditionId(ConditionV1)
              = "sha256:" + SHA-256(RFC8785(ConditionV1))
```

Purpose is supplied only by the signed `CampaignEpochV2` slot:
`audienceRuleRef` or `conversionRuleRef`. The compiler validates the complete
Condition graph and routes only an exact admitted relation. A parameter change
creates a new definition reference while retaining a proof family only when
that family already admits the parameter. A different private witness shape
requires another reviewed proof family; it does not require another Campaign
model or Platform pipeline.

Two engineering families are currently routed through the same compiler and
signed Epoch path:

| Purpose | Exact admitted relation | Proof profile | Current maturity |
|---|---|---|---|
| `CONVERSION` | one exact product, brand and category purchase; quantity, amount, store set and time bounds are committed | `sha256:720fcfb3af3490ba98d151aa7c334aeb10b23dfc7abf088195cf11430f463c68` | non-production atomic Groth16 family; compiler replayed with the retained Monster 14-day definition |
| `AUDIENCE` | exactly four distinct qualifying purchases in the inclusive `-44..0` calendar-day interval under the admitted positive-provenance source contract | `sha256:95f70a5f920be518cfa8a1d56a6dbccc792eeba8258492014bab1f2afddd7319` | non-production count Groth16 family; compiler replayed with a non-sentinel Epoch reuse policy; parameterized V2 profile `sha256:883c900809637233393db6b7ba198dda25f83b754ceccb5c3fb6f6030f1c18f8` is registered internally; compiler dispatch, local proof, program and runtime remain unavailable |

The atomic compiler pins the Campaign-scoped
`ProductSourceSignerAuthorityBindingV1`; evidence and status signers must be
distinct, active at the evaluation cutoff, and bound to the exact policies and
snapshots in the dependency set. The signed Epoch's `registryRefs` contains
both the dependency-set reference and signer-binding reference.

The parameterized Family B V2 proof-family candidate now has adopted internal
source contracts, not an executable evaluator. Its purpose-aware dependency
object binds the exact context, manifest, positive provenance Epoch, product
and status sources, set selections, cutoff and replay roles. Its BN254 store
selection binds a complete ordered set of authenticated `(entryRef,
storeHash)` mappings to the depth-four root. The candidate profile records the
future strict evaluator requirements, but no strict evaluator-profile artifact
or evaluator-linked V2 rule is accepted yet. Platform evaluation, circuit,
setup, key, proof, Solana and runtime availability therefore remain
unavailable.

Unsupported count/window changes, category sets, product or brand wildcards,
ambiguous graphs and unregistered profiles fail closed. Conquest, lapsed and
new-to-brand rules additionally require an authorized Coverage relation before
an absence claim can be compiled. Missing Coverage is `INDETERMINATE`, not a
negative buyer fact.

The compiler creates no proof, network transaction, Outcome, entitlement,
reward, settlement or escrow authority. Current local compiler evidence does
not establish an authenticated Platform runtime or production proving path.
For the current substrate, the no-discretion acceptance path is
`ProofOfMatch -> finalized Solana ACCEPT -> separately authorized Platform Outcome`;
neither a discretionary `ConversionApproval` nor a `ValidatorCertificate` is
required between proof acceptance and Outcome authority. The
`ValidatorCertificate` flow is retained in Appendix A as the earlier public
candidate and is not current substrate authority.
Related pages for the current substrate boundary:
[`solana-proof-verification.md`](./solana-proof-verification.md) (acceptance
path), [`campaign-compiler-procedure.md`](./campaign-compiler-procedure.md)
(definition to signed Epoch), [`campaign-template-catalog.md`](./campaign-template-catalog.md)
(templates over primitives) and the rule grammar in
[`condition-v1.md`](../conditions/condition-v1.md).

The public `single-product-purchase-match-v1` conformance package remains a
separate earlier candidate with a different relation and public-input ABI; it
must not be used as an alias for either current engineering profile.

## 1. Canonical dependency order

A `CampaignEpoch` governs every Campaign proof and outcome. It therefore comes
before `ProofOfMatch` in the authority and verification order even when a user
already holds historical Spend Tokens before the Epoch is signed.

```text
Campaign definition
  Campaign authority
  -> signed CampaignEpoch

Evidence and match
  issuer-authenticated SpendToken(s)
  + resolved CampaignEpoch
  -> optional ProofOfMatch(AUDIENCE)
  -> finalized Solana ACCEPT (SolanaProofEvidence), when the audience proof is present
  -> optional AssignmentRecord
  -> exposure state, if applicable
  -> new SpendToken(s)
  -> ProofOfMatch(CONVERSION)
  -> finalized Solana ACCEPT (SolanaProofEvidence)

Application and economics
  CampaignEpoch
  + accepted match proof(s)
  + optional assignment and exposure
  + optional economic admission
  -> CampaignOutcome
      -> measurement input
      -> optional RewardObligation
          -> optional SettlementRecord
```

No validator approval of a Campaign Epoch is required. A Campaign authority
signature is sufficient; every relying party resolves it and rechecks the Epoch
bindings. Proof acceptance is `PROOF_OF_MATCH_VERIFICATION` under
[Procedure Profile V3](./solana-proof-verification.md): the exact proof bytes
and ordered public inputs are verified by a frozen Solana program, and a
finalized `ACCEPT` record is reconstructed by the relying Consumer as
`SolanaProofEvidenceV1`. No quorum, validator set, vote or certificate sits
between the proof and the Outcome authority.

A Settlement Record exists only when a Reward Obligation or other named
economic liability requires resolution. A measurement-only holdout outcome
can stop at `CampaignOutcome`.

## 2. Composable campaign modes

### 2.1 Direct promotion

```text
CampaignEpoch
-> SpendToken
-> ProofOfMatch(CONVERSION)
-> finalized Solana ACCEPT (SolanaProofEvidence)
-> CampaignOutcome
-> RewardObligation
-> SettlementRecord
```

There is no audience proof, assignment, holdout, or separate economic-admission
step when the Epoch promises an uncapped, sufficiently funded reward for every
accepted conversion.

### 2.2 Qualified promotion without holdout

```text
CampaignEpoch
-> historical SpendToken(s)
-> ProofOfMatch(AUDIENCE)
-> finalized Solana ACCEPT (SolanaProofEvidence)
-> offer
-> new SpendToken(s)
-> ProofOfMatch(CONVERSION)
-> finalized Solana ACCEPT (SolanaProofEvidence)
-> CampaignOutcome
-> RewardObligation
-> SettlementRecord
```

The offer is application behavior, not a core proof object.

### 2.3 Treatment/holdout experiment

```text
CampaignEpoch
-> historical SpendToken(s)
-> ProofOfMatch(AUDIENCE), only if prior private commerce is required
-> finalized Solana ACCEPT (SolanaProofEvidence)
-> AssignmentRecord
-> exposure, if treatment is delivered
-> new SpendToken(s)
-> ProofOfMatch(CONVERSION)
-> finalized Solana ACCEPT (SolanaProofEvidence)
-> CampaignOutcome
    |-- treatment: measurement + deterministic reward obligation
    `-- holdout: measurement only
```

An audience proof exists only when a prior private commerce condition must be
established. Assignment exists only when the Epoch commits multiple
experimental arms.

### 2.4 Capacity-limited promotion

```text
CampaignEpoch
-> SpendToken(s)
-> ProofOfMatch(CONVERSION)
-> finalized Solana ACCEPT (SolanaProofEvidence)
-> deterministic economic admission
-> CampaignOutcome
-> RewardObligation, only if admitted
-> SettlementRecord
```

Proof validity and economic entitlement are separate. A valid proof submitted
after committed capacity is exhausted creates no Reward Obligation.

## 3. Canonical vocabulary

### 3.1 SpendToken

`SpendToken` is the Campaign-layer short name for an issuer-authenticated,
user-held commerce fact represented by a supported Spend Attestation Token.
It does not create a new token family or wire format.

The Verification Issuer produces it. A relying verifier resolves issuer
authority, key history, verification policy, status, canonical Spend Stream
head, and applicable portability profile under the existing Spend rules.

### 3.2 CampaignEpoch

`CampaignEpoch` is the immutable, signed version of a Campaign's rules and
economic terms. [`CampaignEpochV2`](../../../schemas/experimental/campaigns/campaign_epoch_v2.schema.json)
commits:

- an audience rule, when present;
- one conversion rule;
- an assignment policy, when present;
- a reward policy, when present;
- economic-admission, capacity, budget, inventory, allocation, and reuse
  policies when applicable;
- timing and observation windows;
- settlement-resolution and dispute policies;
- required proof profiles;
- Campaign authority; and
- applicable registry roots or content-addressed references.

The exact Campaign mode follows from those references; it is not a mutable mode
flag. A new signed Epoch is required to change a committed rule, profile,
economic term, authority, registry dependency, or window.

Rules may remain private, but their exact canonical bytes MUST be
content-addressed. A predictable plaintext hash is a binding commitment, not
confidentiality; sensitive rule material requires a hiding commitment or an
access-controlled resolution profile.

### 3.3 ProofOfMatch

`ProofOfMatch` is one standardized Crinkl ZK statement establishing that
authenticated private commerce facts satisfy one rule committed by exactly one
`CampaignEpoch`.

```text
ProofOfMatch(purpose = AUDIENCE)
ProofOfMatch(purpose = CONVERSION)
```

Audience and conversion are purposes of the same mechanism, not separate proof
families. Crinkl standardizes the statement envelope, bindings, and verifier
contract; it does not claim to have invented a new cryptographic primitive.

The holder or an authorized prover produces
[`ProofOfMatchV1`](../../../schemas/experimental/campaigns/proof_of_match_v1.schema.json). Its declared proof
profile determines the proof system, verifying key, transcript, public-input
encoding, witness relation, and verification algorithm. The envelope binds:

- proof purpose and Campaign scope;
- exactly one Campaign Epoch and the applicable committed rule;
- proof profile and profile version;
- one or more scoped Spend Token or canonical Spend-head commitments;
- issuer registries and verification-policy references for every input;
- an observable-history boundary when the statement relies on absence;
- proof-replay, purchase-reuse, and entitlement-reuse scopes and nullifiers;
- public outputs and a result commitment; and
- the hash of genuine ZK proof bytes.

The proof model supports a profile-defined bounded input set. A multi-purchase
profile MUST prove each input's authenticity and accepted head, require distinct
purchase bindings, bind the aggregation operation, enforce temporal and value
thresholds inside the statement relation, and expose only the public outputs
declared by the Epoch. Multi-issuer input is valid only when every issuer and
verification-policy dependency is resolved and the proof profile defines how
their authenticated statements enter one relation.

Proof replay, purchase reuse, and entitlement reuse are different failures. A
proof-replay nullifier scopes duplicate proof submission. A purchase-reuse
nullifier prevents the same commerce fact from satisfying a prohibited second
use in its committed scope. An entitlement nullifier prevents a second reward
admission or obligation for the same economic claim and is required when a
Campaign can create or reserve one. A finalized Solana `ACCEPT` record blocks exact proof-byte replay only; it does not update any Campaign registry; the relying profile MUST name the
authoritative registry or ledger and its atomic state transition.

The envelope lists private witness *categories*, never private witness values.
The verifier program verifies declared public inputs and proof bytes. Neither
it nor the relying Consumer receives raw Spend Tokens or witness data unless the
proof profile explicitly makes those values public.

The normative rule-binding invariant is:

```text
commitment(rule actually evaluated)
=
rule commitment bound by CampaignEpoch
```

A verifier MUST reject a mismatch, unresolved rule commitment, or profile that
does not cryptographically bind the evaluated rule commitment.

A hash, Merkle root, signed platform decision, commitment, receipt, validator
signature, proof receipt, or package containing such items is not by itself a
`ProofOfMatch`. A package may carry genuine ZK proof bytes plus non-ZK
supporting evidence; each component retains its own meaning.

### 3.4 SolanaProofEvidence

`SolanaProofEvidence` is the authenticated record that one exact `ProofOfMatch`
was accepted by the frozen verifier program under one exact procedure:

```text
PROOF_OF_MATCH_VERIFICATION, procedureVersion 3
```

[`SolanaProofEvidenceV1`](../../../schemas/experimental/campaigns/solana_proof_evidence_v1.schema.json)
binds the procedure profile reference, the complete `ProofOfMatchV1` content
reference, Campaign Epoch, purpose, rule and evaluated-rule commitments, scope,
selected proof profile, result commitment, circuit and verifying-key identity,
proof-bytes hash, the exact ordered BN254 public inputs, the replay, reuse and
entitlement nullifiers with their registries, and the Solana finality facts:
chain and genesis, program, ProgramData address and executable hash,
instruction-data hash, `ACCEPT` record PDA and hash, transaction, slot,
blockhash and instruction index.

The relying Consumer does not trust a transaction signature, a log line or a
caller-supplied status. It reconstructs the object through a locally trusted
observation boundary at `FINALIZED` commitment, following the
[finalized observation procedure](./solana-proof-verification.md#6-finalized-observation-procedure),
and recomputes:

```text
solanaProofEvidenceRef =
  "sha256:" + lowercase_hex(SHA-256(RFC8785(completeEvidenceObject)))
```

The verifier program is frozen: its ProgramData has no upgrade authority, and
evidence binds the exact executable hash. An upgrade is a new executable
identity and a new admission decision.

The evidence establishes that the registered relation accepted those proof
bytes over those inputs. It does not, by itself:

- update a Campaign nullifier registry beyond the program's own exact-replay
  record;
- perform assignment;
- construct a Campaign Outcome;
- create a Reward Obligation; or
- authorize or execute payment.

The verifier program and the observing Consumer do not:

- inspect private witness data;
- choose targeted buyers;
- perform treatment/holdout assignment;
- present offers or record exposure;
- execute FIFO selection or slot consumption;
- choose Campaign or conversion rules;
- choose reward amounts;
- create discretionary payout approvals;
- operate the Reward Ledger; or
- reserve, move, settle, or refund Campaign funds.

### 3.5 AssignmentRecord

Assignment is the deterministic treatment/holdout or multi-arm result under the
policy committed by the Epoch. It exists only for a Campaign with multiple
experimental arms.

An assignment remains application state when its producer and every consumer
share one authority boundary and no independent dispute or replay consumer
needs portable evidence. A serialized
[`AssignmentRecordV1`](../../../schemas/experimental/campaigns/assignment_record_v1.schema.json) is justified
when assignment crosses a system or authority boundary, is consumed by an
independent measurement or delivery system, or must be produced in a dispute.

The record binds the exact Epoch and policy, deterministic algorithm/profile,
precommitted seed, content-addressed seed material or derivation evidence,
content-addressed canonical assignment inputs, scope-specific subject
nullifier, bucket and arm result, assignment result hash, issue time, and
producer signature. An independent implementation MUST resolve the policy,
profile, `seedMaterialRef`, and `assignmentInputRef`; verify the seed material
opens or derives the committed seed without having been chosen after exposure;
and recompute the assignment digest, bucket, and arm. Unavailable or mismatched
material is `INDETERMINATE`, not an invitation to trust the producer signature.
No Proof Validator vote is required merely because the result is persisted or
transported.

The portable record's `resultHash` is:

```text
"sha256:" + lowercase_hex(SHA-256(RFC8785({
  domain: "crinkl.assignment-result.v1",
  campaignEpochRef,
  assignmentPolicyRef,
  assignmentScopeRef,
  subjectNullifier,
  algorithm,
  arm
})))
```

The resolved assignment profile defines the preimage and domain separation for
`algorithm.assignmentDigest`, the seed commitment/opening or beacon/VRF
derivation, the canonical assignment input, and bucket-to-arm mapping. Changing
any of that behavior requires a new profile reference/version.

### 3.6 Exposure

Exposure records whether an assigned intervention was actually delivered.
Assignment does not prove exposure, and holdout assignment does not by itself
prove absence of exposure.

Exposure remains application and measurement state. It is not a generic core
protocol object in this target because current repository evidence identifies
no additional authority boundary that requires another universal wire object.
An Epoch may commit an exposure policy, and an Outcome may carry a
content-addressed exposure reference when a measurement or dispute profile
requires it.

### 3.7 Economic admission

Economic admission is the deterministic and auditable decision that a valid
match receives capacity under the allocation policy committed by the Epoch.
It is optional: an uncapped and sufficiently funded Campaign can define match
acceptance as direct entitlement.

For a constrained Campaign, the resolved economic-admission policy MUST name:

- the authoritative budget, inventory, capacity, or reservation state;
- the maximum entitlement count or value and its units;
- ordering and deterministic tie-breaking rules;
- atomic concurrency behavior;
- purchase-reuse, claim-replay, and entitlement-nullifier rules;
- the runtime or ledger authorized to record admission;
- the evidence reference and state position consumed by `CampaignOutcome`;
- failure, expiry, correction, and dispute behavior; and
- whether a reservation can later be reversed.

The default target does not introduce a standalone universal admission object.
The authoritative runtime or ledger records admission atomically, and
`CampaignOutcomeV2.economicAdmission` carries the smallest cross-system
projection: policy reference, requirement flag, decision, state reference,
evidence reference, and recorded time; `CampaignOutcomeV2.nullifiers` separately
binds the applicable entitlement nullifier. A profile MAY
define a separate versioned admission artifact only when a named independent
consumer cannot verify that projection against the authoritative state.

A valid `ProofOfMatch` MUST NOT create an unfunded Reward Obligation when the
Epoch makes entitlement capacity-dependent.

### 3.8 CampaignOutcome

`CampaignOutcome` is the narrow application-level composition of the facts
that apply to one Campaign result:

```text
CampaignEpoch
+ optional accepted ProofOfMatch(AUDIENCE) with its SolanaProofEvidence
+ optional assignment
+ optional exposure
+ accepted ProofOfMatch(CONVERSION) with its SolanaProofEvidence
+ optional economic admission
+ applicable nullifiers
-> CampaignOutcome
```

It is not another ZK primitive and MUST NOT become a generic proof package,
report, escrow action, or orchestration envelope. The Campaign runtime produces
[`CampaignOutcomeV2`](../../../schemas/experimental/campaigns/campaign_outcome_v2.schema.json) by applying the
policy committed by the Epoch. `CampaignOutcomeV2` preserves every
`CampaignOutcomeV1` field and rule and substitutes `solanaProofEvidenceRef` for
`validatorCertificateRef`; an audience-only Outcome carries `audienceMatch`
with `conversionMatch = null` and creates no entitlement. It states:

- whether an accepted verified conversion occurred;
- the experimental arm, when applicable;
- whether the result contributes to measurement;
- whether required economic admission succeeded;
- whether a Reward Obligation is created; and
- the exact recipient scope and reward terms when one is created.

For an uncapped Campaign, an eligible accepted conversion may deterministically
create the promised obligation. For a constrained Campaign, the obligation
arises only when both the match and committed economic-admission requirements
are satisfied. The Outcome producer cannot alter committed entitlement rules or
reward amounts.

### 3.9 RewardObligation

`RewardObligation` is a recipient-scoped reward liability deterministically
created by an eligible `CampaignOutcome`. It records what is owed, to which
recipient reference or commitment, under which Outcome and Campaign Epoch, and
under which resolution policy. It does not prove payment.

The Reward Ledger produces
[`RewardObligationV1`](../../../schemas/experimental/campaigns/reward_obligation_v1.schema.json) from the exact
Outcome, Epoch reward policy, recipient binding, amount and asset, funding
lineage, entitlement nullifier, and resolution policy. The producer MUST NOT
alter the amount or entitlement selected by committed policy.

The object is named for its liability semantics. Its content hash and signature
authenticate the record; they do not turn the liability into a separate hiding
commitment scheme.

### 3.10 SettlementRecord

`SettlementRecord` is evidence that one `RewardObligation` was paid, reversed,
expired, disputed, cancelled, or otherwise resolved. Liability creation and
liability resolution are separate.

[`SettlementRecordV1`](../../../schemas/experimental/campaigns/settlement_record_v1.schema.json) binds the
Outcome, Reward Obligation, entitlement nullifier, exact resolution policy,
status, amount and asset, supporting transaction or resolution evidence, prior
record when this is a successor resolution, authority, time, and signature.

Escrow reserve is not settlement, and a batch/root commitment is not a
Settlement Record. Candidate `CampaignEscrowReceiptV1` is a Solana-specific
action receipt that may supply supporting evidence or satisfy a profile mapping
for this role. It is not relabeled or mutated.

A Campaign authority signs the Epoch before conversions occur. Once its
committed match and admission conditions hold, neither the authority nor the
Outcome producer may choose whether or how much to pay.

### 3.11 Canonical object references and signatures

Target references MUST be computed from exact schema-valid objects. For
`CampaignEpochV2`, `AssignmentRecordV1`, `CampaignOutcomeV2`,
`RewardObligationV1`, and `SettlementRecordV1`, the common signed-object
construction is:

```text
unsignedObject = remove_top_level_member(object, "signatures")
objectHashBytes = SHA-256(RFC8785(unsignedObject))
signatures.objectHash = lowercase_hex(objectHashBytes)
objectRef = "sha256:" + signatures.objectHash
signatures.signature = base64(Ed25519_sign(signingKey, objectHashBytes))
```

`signatures.publicKey` is the standard base64 encoding of the 32-byte Ed25519
public key. The relying verifier MUST resolve `issuedBy` and `keyId` under the
object's named authority reference at `issuedAt`, `assignedAt`, `decidedAt`, or
`recordedAt`, as applicable; recompute `objectHash`; and reject an unauthorized
key, hash mismatch, non-canonical encoding, or invalid signature. A field such
as `campaignEpochRef`, `assignmentRef`, `campaignOutcomeRef`,
`rewardObligationRef`, or `previousSettlementRecordRef` uses `objectRef`, not a
business identifier or display digest.

`ProofOfMatchV1` is not signed by this envelope. Its `proofOfMatchRef` and
verification subject hash are the SHA-256 reference over RFC 8785 canonical bytes
of the complete schema-valid object, including proof bytes:

```text
proofOfMatchRef = "sha256:" + lowercase_hex(SHA-256(RFC8785(proofOfMatchV1)))
```

`SolanaProofEvidenceV1` is not signed by this envelope. Its reference is the
SHA-256 over RFC 8785 canonical bytes of the complete schema-valid object, and
the relying Consumer recomputes it from its own finalized observation:

```text
solanaProofEvidenceRef =
  "sha256:" + lowercase_hex(SHA-256(RFC8785(solanaProofEvidenceV1)))
```

Every target object uses only the construction specified for its canonical
family. The historical `validatorCertificateRef` construction is preserved in
Appendix A.

### 3.12 CampaignReport

`CampaignReport` is derived application output over assignments, exposures,
economic admissions, and outcomes under a frozen measurement method. It is not
a cryptographic primitive. Lift calculation, confidence, report layout, offer
discovery, UI delivery, and general Campaign orchestration remain outside the
core proof vocabulary.

## 4. Authority matrix

| Authority or role | Produces or decides | Must not be inferred to control |
|---|---|---|
| Campaign authority | signed Epoch and committed policies | post-conversion payout discretion |
| Verification Issuer | Spend Token and status/lineage evidence | Campaign qualification, assignment, or reward |
| holder / authorized prover | ProofOfMatch under the declared profile | Campaign rule selection |
| Solana verifier program | deterministic `ACCEPT` or `REJECT` over exact proof bytes, verifying key and ordered public inputs; exact-replay record | targeting, assignment, economic admission, Outcome, reward, escrow, or payment |
| Platform finalized observer | authenticated `SolanaProofEvidence` reconstructed from a locally trusted RPC | proof validity beyond what the program accepted; Outcome authority |
| Campaign runtime / Platform | committed-policy application, deterministic assignment, exposure state, economic admission, CampaignOutcome | issuer truth, verifier program identity, rule selection, or discretionary economics |
| capacity/budget ledger | authoritative atomic admission state | proof validity or Campaign rule selection |
| Reward Ledger | recipient-scoped RewardObligation and ledger events | Campaign qualification or escrow movement |
| settlement / escrow authority | policy-constrained reserve and SettlementRecord | proof verification or reward amount selection |
| measurement application | CampaignReport from frozen inputs/method | per-user causal claims or protocol quorum acceptance |

## 5. Producer and consumer matrix

| Artifact or state | Producer | Required inputs | Downstream consumer |
|---|---|---|---|
| SpendToken | Verification Issuer | canonical Spend head, evidence, verification policy, issuer authority | prover, Campaign runtime, verifier |
| CampaignEpoch | Campaign authority | exact rules, economics, policies, registries, windows | prover, verifier program (via bound public inputs), runtime, Reward Ledger, settlement |
| ProofOfMatch | holder or authorized prover | Epoch, rule, Spend commitments, proof profile, private witness | Solana verifier program, then the finalized observer |
| SolanaProofEvidence | Platform finalized observer | exact ProofOfMatch, Procedure Profile V3, frozen program, ProgramData hash, VK account, finalized transaction and `ACCEPT` record | Outcome authority, dispute verifier |
| assignment state / AssignmentRecord | Campaign runtime | Epoch assignment policy, scoped input/nullifier, seed commitment | offer/exposure runtime, measurement, dispute verifier |
| exposure state | delivery application | assignment and delivered intervention | Outcome builder and measurement |
| economic-admission state | authorized runtime or capacity ledger | accepted match, allocation policy, authoritative state, entitlement nullifier | Outcome builder, Reward Ledger, dispute verifier |
| CampaignOutcome | Outcome authority | Epoch, required SolanaProofEvidence, optional assignment/exposure/admission | Reward Ledger, measurement, dispute handling |
| RewardObligation | Reward Ledger | eligible Outcome and exact Epoch reward terms | settlement and recipient presentation |
| SettlementRecord | settlement/escrow authority | obligation, resolution policy, resolution evidence | recipient, reconciliation, dispute handling |
| CampaignReport | measurement application | assignments, exposure coverage, admissions, outcomes, frozen method | sponsor/business reporting |

## 6. Object lifecycle and failure rules

1. The Campaign authority signs an immutable Epoch.
2. Every relying party resolves the authority, signature, rules, policies,
   registries, and window. A profile-specific Campaign quorum procedure is not
   presumed.
3. A prover constructs only the match purposes required by the Epoch.
4. The frozen verifier program runs `PROOF_OF_MATCH_VERIFICATION` for each
   exact proof submission and writes one exact-replay `ACCEPT` record. The
   relying Consumer reconstructs `SolanaProofEvidenceV1` at `FINALIZED`.
5. The Outcome authority verifies the required Solana evidence, assignment,
   exposure, and economic admission, then constructs the Outcome exactly once.
6. An eligible admitted Outcome deterministically creates a Reward Obligation.
7. Settlement authorities apply the precommitted resolution policy and issue a
   Settlement Record.
8. Measurement consumes assignment, exposure, admission, and Outcome facts
   separately.

A component MUST fail closed or return `INDETERMINATE` when a required content
reference, authority, registry, proof profile, rule, canonical Spend head,
Solana evidence, assignment input, exposure boundary, admission state, nullifier
state, or policy is unavailable or mismatched. Business intent and
implementation defaults cannot fill missing cryptographic or authority
bindings.

## 7. Absence and observable history

A witness that omits a token does not prove that no such purchase exists. Any
statement such as “no Monster purchase” MUST bind a completeness or
observable-history boundary committed by the Epoch and supported by the proof
profile. That boundary identifies, at minimum, the issuer/source set, canonical
head snapshot or cutoff, observation interval, accepted statuses, correction
policy, and rule for unresolved or missing sources.

The proof establishes absence only within that declared boundary. It never
upgrades bounded observable history into global nonexistence.

## 8. Conformance narratives

The Monster experiment, direct promotion, and capacity-limited Liquid Death
campaign are specified in
[`conformance/narratives/campaign-acceptance.md`](../../../conformance/narratives/campaign-acceptance.md).

## 9. Boundary impact

- **Business policy:** Campaign authorities still choose audiences, conversion
  rules, arms, rewards, capacity, allocation, timing, disputes, and measurement
  methods; this specification binds and composes those choices but does not
  choose their commercial values.
- **Protocol artifacts:** unreleased schema families define the target Epoch,
  match proof, Solana proof evidence, Procedure Profile V3, conditional
  assignment record, Outcome V2, Obligation, and Settlement Record. The
  quorum-certificate family is historical (Appendix A).
- **Offchain state and computation:** offer delivery, exposure, campaign
  orchestration, report calculation, and economic-admission runtime remain
  application or ledger functions governed by committed policies.
- **Onchain commitment or execution:** proof acceptance under Procedure
  Profile V3 executes on Solana; the current engineering families are frozen
  on Devnet only. Capacity, escrow, and settlement evidence may be bound to a
  chain by an adopted profile without changing proof meaning.
- **Verification and disputes:** exact hashes, signatures, proof profiles,
  program and verifying-key identity, registry dependencies, nullifiers,
  admission state, Outcome composition, and
  liability resolution are independently checkable at their named authority
  boundaries; missing required evidence fails closed.
- **Maturity and adoption:** the architecture, schemas, and exact procedure
  profile are adopted engineering objects at
  `crinkl-protocol@bdac6d3f9f32a312544b3adadbb379f98607198f` and remain
  `SPECIFIED_NOT_IMPLEMENTED`. This public source is not a released package,
  validator-network behavior, runtime support, deployment, or production
  state.

### 9.1 Maturity-record backfill for public-spec #58–#60

This single follow-up record classifies the campaign-maturity prose merged by
public-spec #58 (`8db147f`), #59 (`ba6fcd8`), and #60 (`167b36f`). It records
that historical documentation boundary without rewriting those merge commits.

- **Business policy:** No campaign authority choice changed. Audiences,
  conversion rules, capacity, rewards, timing, measurement, and disputes
  remain deployment-specific selections.
- **Protocol artifacts:** The merged prose recorded already-adopted internal
  source contracts and candidate proof-family identities for the product-set
  and parameterized-count families. It changed no released schema, manifest,
  binding, verifier rule, canonical bytes, or protocol object.
- **Offchain state and computation:** Platform contract ports, evaluator
  selection, proof generation, runtime evaluation, Outcome construction, and
  economics remain separately governed implementation work. The unavailable
  evaluator and proof machinery cannot be supplied by documentation.
- **Onchain commitment or execution:** No program, account, transaction,
  finalized acceptance, escrow, settlement, or other chain state was added.
  The candidate families remain unavailable where the required circuit, setup,
  key, proof, program, or acceptance evidence is absent.
- **Verification and disputes:** A relying verifier continues to require the
  named profile content reference, evaluator-linked rule, proof, and acceptance
  evidence; missing evidence fails closed. The source-contract and Platform
  port statements are independently auditable against the commits cited in the
  campaign catalog, but do not establish proof acceptance or dispute outcome.
- **Maturity and adoption:** #58 recorded the product-set candidate and reuse
  policy source maturity, #59 recorded merged Platform contract ports, and #60
  recorded Family B V2 source-contract maturity. All remain unreleased,
  non-runtime, and non-production; no package or protocol-version change
  occurred.

## Appendix A. Historical acceptance candidate: ValidatorCertificate

The text below was the target acceptance edge before the Solana successor was
adopted. It is retained so earlier public candidates remain interpretable. It
is not the current Campaign acceptance path and MUST NOT be used for Campaign
proof acceptance under Procedure Profile V3. `ValidatorCertificateV1` and
Procedure Profiles V1 and V2 remain valid only under their exact prior
profiles.

### A.1 ValidatorCertificate (historical)

`ValidatorCertificate` is a Proof Validator quorum certificate over one exact
subject under one exact procedure. The required procedure is:

```text
PROOF_OF_MATCH_VERIFICATION
```

[`ValidatorCertificateV1`](../../../schemas/experimental/campaigns/validator_certificate_v1.schema.json) binds
the subject type and hash, procedure identifier and version,
content-addressed procedure profile, validator-set reference, quorum-policy
reference, signatures or aggregate signature, issue time, applicable Epoch,
registry dependencies, and the accepted decision.

Proof Validators verify a `ProofOfMatch` against its declared proof profile,
public inputs, `CampaignEpoch` bindings, registry dependencies, and
replay/nullifier rules. If the required quorum accepts the proof, they issue a
`ValidatorCertificate` identifying the exact proof hash and procedure.

The current
[`ProcedureProfile V2`](../artifacts/campaign_proof_of_match_procedure_profile_v2.json)
defines validator processing and certification, including the authenticated
assignment timestamp used for `issuedAt`. The accepted ProofProfile defines the
cryptographic statement and proof-system relation. The ProcedureProfile binds
that ProofProfile by content reference and does not redefine its relation.

The certificate establishes quorum acceptance of that subject under the
declared procedure. It does not, by itself:

- make the subject globally immutable;
- update a canonical nullifier registry;
- perform assignment;
- construct a Campaign Outcome;
- create a Reward Obligation; or
- authorize or execute payment.

Any state transition or replay finality MUST identify the canonical registry,
ledger, or chain that records it. A certificate for one proof hash cannot be
reused for another proof, Epoch, procedure, or economic-claim scope.

Proof Validators do not:

- inspect private witness data unless the proof profile makes it public;
- choose targeted buyers;
- perform treatment/holdout assignment;
- present offers or record exposure;
- execute FIFO selection or slot consumption;
- choose Campaign or conversion rules;
- choose reward amounts;
- create discretionary payout approvals;
- operate the Reward Ledger; or
- reserve, move, settle, or refund Campaign funds.
