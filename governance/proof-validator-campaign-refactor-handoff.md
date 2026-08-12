---
status: draft
layer: governance
version: v1
normative: false
---

# Proof Validator Campaign refactor handoff

This is the implementation handoff for the next slice. It does not change
Proof Validator code, procedure dispatch, certificates, network state, or alpha
runtime behavior.

Exact validator source examined:
`crinkl-proof-validator origin/main@e282562da6a2f1edac5a97d7ae4591023c8453a5`.

Exact adopted protocol source:
`crinkl-protocol main@184133e64bae81c614cc30283ca34382b3b089de`.

## 1. Required procedure

```text
procedureId: PROOF_OF_MATCH_VERIFICATION
procedureVersion: 1
procedureProfileRef: sha256:5472a7d975a6abbc8c8b99b85e3007bb3d57a980d203d36898d91ed746a58fb0
subjectType: PROOF_OF_MATCH
```

The exact public profile artifact is
[`campaign_proof_of_match_procedure_profile_v1.json`](../protocol/applications/artifacts/campaign_proof_of_match_procedure_profile_v1.json).
The procedure ID names an unversioned family; executable behavior is selected
only by the full triplet above.

### Subject hash

The subject is one complete schema-valid `ProofOfMatchV1` object.

```text
subjectHash =
  "sha256:" + lowercase_hex(SHA-256(RFC8785(proofOfMatchV1)))
```

No field is omitted. The object has no separate top-level signature envelope.
The ZK proof-byte hash remains an independently checked inner binding.

### Required public inputs

The selected proof profile fixes encoding and order. The verified relation must
bind at least:

1. `purpose`;
2. `campaignId` and exact `campaignEpochRef`;
3. `evaluatedRuleCommitment`;
4. `scopeRef`;
5. `inputSetCommitment` and every declared scoped Spend Token/head binding;
6. issuer-registry and verification-policy dependencies;
7. distinctness, temporal, and value aggregate commitments;
8. observable-history boundary when absence is used;
9. proof-replay and purchase-reuse nullifiers and scopes, plus entitlement
   nullifier and scope when the committed Campaign can create or reserve an
   economic claim; and
10. `resultCommitment`.

The envelope's named public inputs, `publicInputsCommitment`, resolved verifier
inputs, and proof-system verifier inputs must be byte-equivalent under the
profile. A display field or package summary is not an accepted substitute.

### Proof-profile requirements

The resolved `procedureProfileRef` and `ProofOfMatchV1.proofProfile.profileRef`
must identify immutable, content-addressed profiles. Together they define:

- supported `ProofOfMatchV1` schema and purpose;
- proof system and exact verifier implementation contract;
- proof-profile version, verifying key, transcript, and domain separation;
- public-input names, order, encoding, and bounds;
- witness relation and disclosure boundary;
- maximum Spend input count;
- Spend authenticity/head/status rules;
- purchase distinctness relation;
- temporal, currency/value, rounding, and overflow rules;
- multi-issuer compatibility rules;
- absence/completeness construction when supported;
- nullifier derivation and registry scopes; and
- stable failure-code mapping.

Changing any accepted relation, binding, verifier input, nullifier derivation,
or failure behavior requires a new content-addressed procedure/proof profile and
semantic version. `procedureId` alone must never select mutable behavior.

### Verification checks

Each selected validator independently:

1. parses the exact `ProofOfMatchV1` schema;
2. recomputes `subjectHash` and decoded `proofBytesHash`;
3. resolves the Campaign Epoch and verifies its content hash, authority,
   signature, succession reference where applicable, and effective window;
4. confirms purpose selects the exact Epoch rule and required proof profile;
5. enforces `evaluatedRuleCommitment = ruleCommitment = Epoch purpose rule`;
6. resolves the procedure profile, proof profile, verifying key, transcript,
   and verifier inputs, and verifies the outer and inner proof-system
   identifiers agree;
7. recomputes named public-input and input-set bindings;
8. verifies the proof relation over every declared Spend Token/head commitment
   and resolves only the issuer-registry, verification-policy,
   status/correction, and observation-cutoff material that the proof profile
   declares public;
9. enforces input count, canonical ordering, purchase distinctness, temporal
   predicates, aggregate value arithmetic, and multi-issuer rules;
10. resolves and verifies an observable-history boundary when the rule uses
    absence;
11. recomputes all declared nullifiers and checks their referenced registry
    views;
12. verifies `resultCommitment` and claimed `MATCH` result;
13. runs the declared ZK verifier over the exact proof bytes and public inputs;
14. constructs the canonical decision preimage; and
15. signs its digest or returns exactly one stable failure code.

Validators do not fetch private witness data unless the proof profile declares
it public. Implementations must not silently fall back from ZK verification to
trusting hashes, proof receipts, Platform signatures, or package summary fields.

### Registry dependencies

The procedure fails closed unless it can resolve the exact applicable:

- Campaign authority/key registry and Epoch signature policy;
- issuer registry snapshot(s) and key-history/status material;
- verification-policy artifacts;
- proof-profile/verifying-key registry;
- observable-history source/snapshot registry when absence is used;
- proof-replay, purchase-reuse, and entitlement registry views;
- validator-set/selection reference; and
- quorum-policy reference.

Version skew is normal. A validator may reject an unsupported profile without
changing the procedure meaning. A quorum certificate is valid only for the
declared validator set and profile, never because operator tooling shows enough
machines online.

### Nullifier and replay checks

The V1 procedure verifies derivation and reports
`NO_CONFLICT_OBSERVED` against exact referenced registry views. It does not
write a registry:

```text
ValidatorCertificateV1.stateTransition = NONE
```

Consequently, the certificate does not establish durable replay finality. The
Campaign runtime, economic-admission ledger, or Reward Ledger must name and
perform the atomic compare-and-record transition before claiming a unique
entitlement. If a later validator procedure is intended to update canonical
nullifier state, it needs a versioned procedure, explicit registry authority,
atomic transition semantics, and a certificate that names that transition. It
must not silently change this V1 procedure.

### Decision hash and signatures

For an accepted subject, construct this exact JCS object:

```json
{
  "domain": "crinkl.validator-certificate.decision.v1",
  "subjectType": "PROOF_OF_MATCH",
  "subjectHash": "sha256:<64 lowercase hex>",
  "procedureId": "PROOF_OF_MATCH_VERIFICATION",
  "procedureVersion": "1",
  "procedureProfileRef": "sha256:5472a7d975a6abbc8c8b99b85e3007bb3d57a980d203d36898d91ed746a58fb0",
  "applicableEpochRef": "sha256:<64 lowercase hex>",
  "validatorSetReference": "sha256:<64 lowercase hex>",
  "quorumPolicyReference": "sha256:<64 lowercase hex>",
  "registryDependencies": ["<canonical ordered hash refs>"],
  "replayChecks": {
    "registryRefs": ["<canonical ordered hash refs>"],
    "result": "NO_CONFLICT_OBSERVED"
  },
  "decision": "ACCEPT",
  "stateTransition": "NONE",
  "issuedAt": "<deterministic certificate-round timestamp>"
}
```

Arrays are sorted by unsigned UTF-8 byte order and contain no duplicates.
The procedure profile defines how the certificate-round timestamp is selected;
every signer signs the same value. `issuedAt` is therefore authenticated and
cannot be rewritten by the certificate assembler.

```text
decisionHash = "sha256:" + lowercase_hex(SHA-256(RFC8785(preimage)))
certificateId = "vc:" + lowercase_hex(decisionHash bytes)
```

Each individual validator signs the raw 32 decision-hash bytes. An aggregate
profile signs the same digest and binds its signer set/bitmap. Certificate
assembly verifies that accepted signer identities are distinct, selected by the
exact validator-set reference, authorized at issue time, and sufficient under
the exact quorum-policy reference.

### Certificate output

An accepted quorum emits
[`ValidatorCertificateV1`](../schemas/experimental/campaigns/validator_certificate_v1.schema.json)
with the exact decision fields, issue time, and individual or aggregate
signature evidence.

The certificate means quorum acceptance of the exact proof under the exact
procedure. It does not create an Outcome, obligation, settlement, assignment,
immutable global state, or canonical nullifier write.

### Stable failure codes

No acceptance certificate is emitted on failure.

| Code | Meaning |
|---|---|
| `SUBJECT_SCHEMA_INVALID` | ProofOfMatch fails the supported schema |
| `SUBJECT_HASH_MISMATCH` | supplied and recomputed subject hashes differ |
| `PROCEDURE_UNSUPPORTED` | procedure or version is unsupported |
| `PROCEDURE_PROFILE_UNRESOLVED` | procedure profile cannot be authenticated |
| `PROOF_PROFILE_UNRESOLVED` | proof profile cannot be authenticated |
| `PROOF_PROFILE_UNSUPPORTED` | profile is known but unsupported by this validator |
| `PROOF_BYTES_HASH_MISMATCH` | decoded proof bytes do not match their hash |
| `PROOF_SYSTEM_MISMATCH` | outer proof profile and inner proof object name different proof systems |
| `VERIFIER_INPUTS_UNRESOLVED` | exact proof-system inputs cannot be resolved |
| `CAMPAIGN_EPOCH_UNRESOLVED` | exact Epoch bytes cannot be resolved |
| `CAMPAIGN_EPOCH_SIGNATURE_INVALID` | Epoch signature or object hash is invalid |
| `CAMPAIGN_AUTHORITY_UNAUTHORIZED` | Epoch signer lacks applicable authority |
| `CAMPAIGN_WINDOW_INVALID` | proof falls outside the committed window |
| `PURPOSE_RULE_MISSING` | Epoch has no rule for the declared purpose |
| `PURPOSE_PROFILE_MISMATCH` | proof profile differs from the Epoch requirement |
| `RULE_COMMITMENT_MISMATCH` | evaluated, envelope, and Epoch rule commitments differ |
| `PUBLIC_INPUT_COMMITMENT_MISMATCH` | named, set, and verifier public inputs differ |
| `SPEND_INPUT_SET_INVALID` | input count/order/set binding is invalid |
| `SPEND_AUTHENTICITY_BINDING_INVALID` | the proof does not establish the profile-required Spend Token/head authenticity relation, or a required public binding cannot be resolved |
| `SPEND_HEAD_INVALID` | canonical head/status/correction rule fails |
| `ISSUER_REGISTRY_UNRESOLVED` | an issuer registry dependency is unavailable |
| `ISSUER_UNAUTHORIZED` | an input issuer/key is outside accepted authority |
| `VERIFICATION_POLICY_UNRESOLVED` | exact verification policy is unavailable |
| `VERIFICATION_POLICY_MISMATCH` | input policy does not satisfy the proof/Epoch profile |
| `MULTI_ISSUER_PROFILE_UNSUPPORTED` | profile cannot compose the declared issuer set |
| `PURCHASE_DISTINCTNESS_INVALID` | inputs are duplicated or distinctness proof fails |
| `TEMPORAL_AGGREGATE_INVALID` | timing/window relation fails |
| `VALUE_AGGREGATE_INVALID` | amount/unit/rounding/overflow relation fails |
| `OBSERVABLE_HISTORY_BOUNDARY_REQUIRED` | absence is claimed without a boundary |
| `OBSERVABLE_HISTORY_BOUNDARY_UNRESOLVED` | boundary or completeness evidence is unavailable |
| `NULLIFIER_DERIVATION_INVALID` | a proof, purchase, or entitlement nullifier is wrong |
| `REPLAY_REGISTRY_UNRESOLVED` | required registry view is unavailable |
| `REPLAY_CONFLICT` | referenced view already contains a prohibited use |
| `RESULT_COMMITMENT_MISMATCH` | result does not bind the verified statement output |
| `ZK_PROOF_INVALID` | cryptographic proof verification fails |
| `VALIDATOR_SET_UNRESOLVED` | exact selected set cannot be authenticated |
| `VALIDATOR_NOT_SELECTED` | signer is not selected for this duty |
| `QUORUM_POLICY_UNRESOLVED` | exact quorum policy cannot be authenticated |
| `SIGNATURE_INVALID` | validator decision signature is invalid |
| `QUORUM_NOT_SATISFIED` | accepted selected signatures are insufficient |
| `INTERNAL_ERROR` | validator could not complete deterministically; never an acceptance |

## 2. Existing statementType inventory

Current source declares:

```text
BOOST_MATCH_BUNDLE_V0
QUALIFIED_GMV_BURN_EPOCH_V1
QUALIFIED_GMV_BURN_EPOCH_V2
CAMPAIGN_DIRECT_BUYER_REWARD_ADMISSION_V1
```

Evidence:
`crinkl-proof-validator@e282562:packages/proof-package/src/index.ts:16-29`.

| Current identifier | Actual subject/procedure | Target mapping |
|---|---|---|
| `BOOST_MATCH_BUNDLE_V0` | mixed Boost package verification with profile-specific artifacts and non-ZK bindings | prototype supporting envelope; not equivalent to `ProofOfMatchV1` |
| `QUALIFIED_GMV_BURN_EPOCH_V1` | GMV aggregation/burn procedure | no Campaign target mapping |
| `QUALIFIED_GMV_BURN_EPOCH_V2` | different GMV procedure/version | no Campaign target mapping |
| `CAMPAIGN_DIRECT_BUYER_REWARD_ADMISSION_V1` | exact release/Epoch/reward-policy/cutoff admission procedure | prototype profile-specific Campaign gate; not ProofOfMatch verification |

The procedures are not equivalent:

| Current identifier | Actual inputs and recomputation | Finalized result / consumer | Naming finding |
|---|---|---|---|
| `BOOST_MATCH_BUNDLE_V0` | prototype Epoch and `BoostMatchStatementV1`; recomputes Epoch/rule/statement hashes and checks condition, reward, payout, timing, actor-separation, settlement, funding, queue/proof-package bindings (`packages/campaign/src/index.ts:60-123,271-355`; engine adapter `packages/proof-validator-engine/src/profiles/campaign.ts:10-36`) | Campaign verification report inside the generic proof-result lane; Boost match recording and settlement-support prototype consumers | names a mixed bundle/profile, not one proof purpose or one deterministic procedure; it combines pre-action, buyer, routing, funding, and settlement bindings |
| `QUALIFIED_GMV_BURN_EPOCH_V1` | statement plus spend/election/claim leaf sets; recomputes three roots, counts, total, set equality, issuer/mint/policy/artifact/nullifier bindings (`packages/gmv/src/index.ts:55-98,161-226`) | GMV verification report consumed by GMV admission/accounting | “burn” overstates the procedure: validators verify an aggregate statement but do not execute a burn |
| `QUALIFIED_GMV_BURN_EPOCH_V2` | signed daily GMV references, optional daily preimages/day witnesses/election leaves, chain context, price context, runtime policy and lifecycle facts; verifies roots/totals/signatures/maturity/price and recomputes an on-chain epoch commitment (`packages/gmv/src/burnEpochV2.ts:1-23,69-87,146-231,265-324`; engine adapter `packages/proof-validator-engine/src/profiles/qualified-gmv-v2.ts:32-185`) | V2 GMV verification/lifecycle reports and recomputed epoch commitment for the density-burn consumption path | shares the V1 economic name but is a materially different procedure, input set, output, and consumer; V2 is not merely a compatible implementation revision |
| `CAMPAIGN_DIRECT_BUYER_REWARD_ADMISSION_V1` | exact release identity, Epoch and reward-policy artifacts, cutoff, registry/assignment, profile policy and Campaign admission nullifier; then generic strict-BFT certificate checks (`packages/campaign/src/admission.ts:30-59,193-261,264-334,337-387`) | profile-specific Campaign admission finality consumed by current Platform business-Campaign admission (`crinkl-platform@42d28cc:services/attestation-gateway/src/domain/businessCampaignAdmission.ts:199-360`) | narrow name is closer to behavior, but “admission” still needs one explicitly named durable activation/non-equivocation state and consumer before becoming target architecture |

V1 GMV and Boost reuse the statement string as the proof-profile identifier;
V2 GMV and Campaign admission use different profile identifiers. Package
version, runtime policy, evidence shape, profile registry, and implementation
code also select behavior. Similar suffixes therefore do not establish semantic
version compatibility, and distinct names do not imply distinct authority
lanes. Behavior can drift without changing `statementType` today. The target
fix is not to rename these strings in place; it is to pin behavior with
`procedureId + procedureVersion + procedureProfileRef`, keep `subjectType`
separate, and require a new profile reference/version for every semantic change.

`statementType` currently participates in dispatch while profile ID, package
version, policy hash, artifact set, and implementation code also determine
behavior. It therefore does not uniquely identify the full deterministic
procedure. The refactor must make `procedureId + procedureVersion +
procedureProfileRef` the behavior identity and keep `subjectType` separate.

The current implementation certificate binds `proofId`, proof-package hash,
`statementType`, result hash, policy, registry snapshot, validator assignment,
public artifact, quorum, signatures, and time
(`crinkl-proof-validator@e282562:packages/finality/src/index.ts:71-86,188-230,292-311`).
It does not carry canonical `subjectType` or a content-addressed procedure
profile and therefore is not `ValidatorCertificateV1`. The next implementation
slice must implement the canonical certificate directly; it must not translate
the prototype certificate or infer equivalence from overlapping fields.

## 3. Campaign admission disposition

`CAMPAIGN_DIRECT_BUYER_REWARD_ADMISSION_V1` is prototype implementation
behavior, not a Campaign protocol predecessor and not a compatibility
requirement for the canonical Campaign specification. Prototype status alone
does not prove that implementation removal is safe: the implementation refactor
must inventory its exact producers, consumers, stored payloads, and deployed
dependencies, and determine whether the path prevents one distinct trust
failure.

Before defining any generic Campaign procedure, identify one of these distinct
security requirements and its authoritative consumer:

- cross-runtime non-equivocation for one Campaign Epoch/profile;
- shared activation state that downstream runtimes or escrow must verify;
- quorum verification of a release/profile availability boundary that cannot be
  rechecked during ProofOfMatch verification; or
- another explicit state transition not created by the Campaign authority
  signature.

If no relying consumer needs such quorum-created state, retire the prototype
Campaign admission path as part of the validator/runtime refactor and resolve
the Campaign signature and bindings during `PROOF_OF_MATCH_VERIFICATION`. If a
consumer does need it, stop and define a separate target procedure only after
its subject and state-transition semantics are fixed. Do not rename the
prototype identifier into a generic Campaign procedure.

## 4. Exact implementation starting point

Begin the next code slice at:

```text
crinkl-proof-validator
origin/main@e282562da6a2f1edac5a97d7ae4591023c8453a5
```

First implementation step:

1. add a procedure registry entry for `PROOF_OF_MATCH_VERIFICATION` whose
   behavior is pinned by a content-addressed procedure profile;
2. add canonical parsers and hashers for `ProofOfMatchV1` and
   `ValidatorCertificateV1` directly, with no predecessor translation;
3. leave unrelated GMV procedures unchanged, and plan explicit removal of the
   two prototype Campaign statement paths only after an exact producer,
   consumer, stored-payload, and runtime-dependency inventory plus canonical
   replacement tests pass;
4. implement schema/hash/profile/binding failures before adding native
   proof-system verifier integrations; and
5. add negative tests proving that prototype packages and certificates are not
   accepted as canonical V1 objects.
