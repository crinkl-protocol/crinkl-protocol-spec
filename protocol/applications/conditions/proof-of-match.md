---
status: draft
layer: applications
version: vnext
normative: true
---

# ProofOfMatch

`ProofOfMatch` is one standardized Crinkl ZK statement proving that one or more
authenticated private commerce facts satisfy one rule committed by exactly one
`CampaignEpoch`.

The canonical schema is
[`ProofOfMatchV1`](../../../schemas/experimental/campaigns/proof_of_match_v1.schema.json). The
complete Campaign composition and authority boundaries are in the
[`Campaign architecture`](../campaigns/README.md).

## Purposes

```text
ProofOfMatch(purpose = AUDIENCE)
ProofOfMatch(purpose = CONVERSION)
```

Purpose selects the applicable Epoch rule and relying use. It does not create a
different proof family or imply that a validator has been “assigned” to an
audience or conversion role.

An audience proof exists only when prior private commerce must be established.
A conversion proof is required for the Campaign Outcomes defined by the target
architecture.

## Producer and verifier

The holder or an Epoch-authorized prover produces the proof. Proof Validators
verify the public statement under `PROOF_OF_MATCH_VERIFICATION`. A relying
application verifies the resulting `ValidatorCertificate` before treating the
proof as quorum-accepted.

Neither the envelope nor certificate gives the prover, validator, Campaign
authority, or relying application a power assigned to another role.

## Canonical envelope

The complete `ProofOfMatchV1` object is RFC 8785 canonicalized and SHA-256
hashed. Its subject reference is:

```text
proofOfMatchRef = "sha256:" + lowercase_hex(SHA-256(RFC8785(proofOfMatch)))
```

The envelope includes:

- `purpose`, `campaignId`, `campaignEpochRef`, and `scopeRef`;
- `ruleCommitment` and `evaluatedRuleCommitment`;
- producer role and optional authority reference;
- exact proof profile, version, proof system, verifying key, transcript, and
  public-input encoding;
- a bounded ordered set of scoped Spend Token and canonical-head bindings;
- each input's issuer registry, verification policy, and purchase-reuse
  nullifier;
- input-set, distinctness, temporal-aggregate, and value-aggregate hashes;
- observable-history boundary reference when absence is claimed;
- proof-replay, purchase-reuse, and, when the Campaign can create an economic
  claim, entitlement nullifiers plus their authoritative registry references;
- named public-input hashes and their set hash;
- private witness category labels, not witness values;
- claimed `MATCH` result and result hash;
- ZK proof bytes, decoded-byte hash, and verifier-input reference; and
- content-addressed supporting-evidence references whose accepted types are
  fixed by the proof profile.

`proof.proofBytesHash` is:

```text
"sha256:" + lowercase_hex(SHA-256(base64_decode(proof.proofBytes)))
```

It does not replace verification of the proof bytes.

## Required public inputs

The proof profile fixes exact encodings. At minimum, the verified public-input
relation MUST bind:

- purpose;
- exact Campaign Epoch reference;
- exact evaluated rule commitment;
- Campaign and proof scope;
- ordered input-set commitment;
- issuer registry and verification-policy dependencies;
- canonical Spend-head commitments;
- observable-history boundary, when used;
- proof-replay and purchase-reuse nullifiers, plus an entitlement nullifier
  when the committed Campaign can create or reserve an economic claim;
- aggregation outputs required by the rule; and
- result commitment.

Public input names and hashes in the envelope are an index over the actual
proof-verifier inputs. A validator MUST reject any disagreement among the
profile encoding, verifier inputs, named envelope entries, or
`publicInputsCommitment`.

The ProcedureProfile defines validator execution and certification semantics.
The ProofProfile defines the cryptographic statement, witness relation, and
proof-system relation. A ProcedureProfile that accepts a ProofProfile MUST bind
it by content reference and MUST NOT redefine its cryptographic relation.

## Private witness categories

Permitted category labels are:

- Spend Token authenticity material;
- canonical Spend-head material;
- private subject linkage;
- purchase distinctness;
- temporal aggregation;
- value aggregation;
- observable-history completeness; and
- private rule parameters.

The labels disclose the relation category, not witness values. Validators MUST
NOT require raw Spend Tokens, receipt data, identities, private subject links,
or rule plaintext unless the selected proof profile explicitly declares those
values public. A disclosure profile must not be described as private merely
because its data travels inside a proof package.

## Rule binding

The normative invariant is:

```text
commitment(rule actually evaluated)
=
rule commitment bound by CampaignEpoch
```

Concretely:

```text
proofOfMatch.evaluatedRuleCommitment
= proofOfMatch.ruleCommitment
= resolved Epoch audienceRuleRef     when purpose = AUDIENCE
  or resolved Epoch conversionRuleRef when purpose = CONVERSION
```

The proof relation itself MUST bind `evaluatedRuleCommitment`. Equality in the
outer JSON envelope without proof-system binding is insufficient.

Private rule material may be resolved inside an authorized proving boundary,
but the canonical bytes and commitment procedure must be fixed by the proof
profile. Predictable hashes do not hide rule plaintext.

## One or multiple Spend inputs

A profile may support one or a bounded number of Spend Tokens. For every input,
the proof relation MUST establish the profile-defined authenticity, issuer,
verification-policy, accepted-status, and canonical-head conditions. Public
`spendTokenBinding` and `canonicalHeadBinding` values are profile-defined
commitments; they do not require disclosure or public resolvability of the raw
token or head.

A multi-input proof MUST additionally establish:

1. the input count is within the profile limit;
2. input indices are canonical and contiguous;
3. each purchase binding is distinct under the Epoch's distinctness rule;
4. temporal comparisons use the Epoch's timing and observation policies;
5. value arithmetic uses the committed unit, currency, rounding, and overflow
   rules;
6. aggregation covers exactly the committed input set; and
7. every issuer and policy dependency is authorized and compatible with the
   rule.

This supports statements such as three distinct purchases totaling at least a
threshold inside a fixed window. Merely supplying three token references does
not prove distinctness or aggregation.

## Absence statements

Omission is not a proof of nonexistence. A statement such as “no Monster
purchase” is valid only within an Epoch-committed observable-history or
completeness boundary. The proof and profile must bind the source/issuer set,
snapshot or cutoff, interval, accepted states, correction policy, and behavior
for unavailable sources.

The result means no matching purchase was found within that boundary. It never
means global nonexistence.

## Replay and reuse

The following scopes are distinct:

- proof replay: reusing the same proof submission where prohibited;
- purchase reuse: reusing a commerce fact across a prohibited Campaign scope;
- entitlement reuse: receiving or reserving the same economic entitlement
  twice.

The Epoch and proof profile define derivation and registry scope for each
nullifier. `proofReplayNullifier` and `proofReplayRegistryRef` are always
present. Entitlement nullifier and registry references are both present or both
null; they are required when the committed Campaign policy can create or reserve
an economic entitlement. When derivation uses only public data, a validator
recomputes it directly. When derivation uses private witness data, the verified
proof relation establishes correct derivation; the validator verifies the
exposed nullifier binding and checks that value against the required registry
view. The validator does not fetch the private witness. Issuing a
`ValidatorCertificate` does not update that registry. The relying runtime or
ledger must perform the named atomic write before it claims replay finality or
economic admission.

## Deterministic validator procedure

For `PROOF_OF_MATCH_VERIFICATION`, each validator independently:

1. parses the exact schema and recomputes `subjectHash`;
2. resolves and verifies the Campaign authority signature on the exact Epoch;
3. confirms purpose selects the matching Epoch rule and proof profile;
4. resolves the proof profile, verifying key, transcript, and public-input
   encoding;
5. confirms outer and inner proof-system identifiers agree and recomputes the
   decoded proof-byte and public-input hashes;
6. verifies the rule, Epoch, Campaign, scope, Spend-input, issuer,
   verification-policy, observable-history, result, and nullifier bindings;
7. verifies each required public registry dependency and the proof-bound
   canonical Spend status relation;
8. enforces profile-specific input count, distinctness, temporal, value,
   multi-issuer, and arithmetic rules;
9. checks declared replay/nullifier registries without claiming to update them;
10. executes the proof-system verifier; and
11. signs the canonical acceptance decision hash or returns one failure code.

Only a quorum satisfying the declared validator-set and quorum-policy
references can assemble a `ValidatorCertificateV1` for the exact proof hash.

## Verification result

The successful result is a `ValidatorCertificate` with:

```text
subjectType = PROOF_OF_MATCH
subjectHash = proofOfMatchRef
procedureId = PROOF_OF_MATCH_VERIFICATION
decision = ACCEPT
stateTransition = NONE
```

A rejection does not produce an acceptance certificate. The validator handoff
defines stable failure codes and the exact decision-hash preimage.

## Non-ZK components

Commitments, hashes, signed evidence, Merkle proofs, validator certificates,
economic-admission records, and proof packages remain distinct from the ZK
proof. A package can contain both genuine ZK and non-ZK components; describing
the package as a whole as “the proof” MUST NOT erase those distinctions.
