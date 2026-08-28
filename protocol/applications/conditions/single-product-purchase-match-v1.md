---
status: draft
layer: applications
version: v1
normative: true
---

# Single Product Purchase Match V1

`SINGLE_PRODUCT_PURCHASE_MATCH_V1` is the first ProofProfile for
`PROOF_OF_MATCH_VERIFICATION`. It proves that one authenticated private product
purchase satisfies the conversion rule committed by one `CampaignEpochV2`.
This profile supports `purpose = CONVERSION` only.

The official circuit contract is
[`H2_SINGLE_PRODUCT_PURCHASE_MATCH_V1`](./h2-single-product-purchase-match-v1.md).
The machine-readable implementation handoff is
[`single_product_purchase_match_v1_build_contract.json`](../artifacts/single_product_purchase_match_v1_build_contract.json).

```text
proofProfileId = SINGLE_PRODUCT_PURCHASE_MATCH_V1
circuitId      = H2_SINGLE_PRODUCT_PURCHASE_MATCH_V1
proofSystem    = HALO2_IPA
```

The profile and circuit identities do not name a brand, product, category,
Campaign, processor architecture, programming language, executable, or prover
implementation. Those are either committed rule inputs or implementation
choices.

## Maturity and authority

The relation in this document is a normative draft. It is not an adopted
ProofProfile until the exact machine-readable profile, relation manifest,
verifying key, transcript profile, proof encoding, public-input encoding, and
conformance vectors have immutable content references.

No prototype, demonstration, candidate, or implementation-local circuit is an
alias for `H2_SINGLE_PRODUCT_PURCHASE_MATCH_V1`. Earlier implementation
evidence may inform engineering and performance work but has no authority over
this profile.

## Exact claim

For exactly one accepted `SpendAttestationToken` and one
`ProductPurchaseAttestationV1`, the proof establishes all of the following:

1. The Spend Token is admitted under the Epoch-bound Spend issuer registry and
   verification policy.
2. The product-purchase attestation is admitted under the Epoch-bound product
   issuer registry, product-verification policy, and evidence-status snapshot.
3. Both artifacts bind the same `spendId`, `spendTokenHash`, and
   `canonicalHeadEventHash`.
4. The product, brand, and category facts are members of the exact registry
   snapshots committed by the Epoch.
5. The private facts satisfy the exact rule whose commitment is bound by the
   Epoch. V1 may constrain product, brand, category, purchase time, quantity,
   net product amount, and currency.
6. The evidence is not corrected, returned, revoked, invalidated, or
   superseded as of the bound `statusCutoff` under the exact status policy.
7. The recipient-scope opening is bound to the Spend Token's selected
   holder/recipient mechanism.
8. The rule evaluated by the circuit has the same commitment as the Epoch's
   conversion rule.
9. The proof is bound to the exact Campaign, Epoch, purpose, proof scope,
   input set, and profile.
10. Proof-replay, purchase-reuse, and entitlement nullifiers are derived under
    distinct domain separators and bind the required private openings.
11. The result commitment represents `MATCH` for that complete relation.

This profile does not establish Campaign admission, validator assignment,
quorum, reward authority, settlement, payment, or production deployment.

## Public dependencies

The verifier resolves authenticated, content-addressed evidence for:

- the exact `CampaignEpochV2` and its conversion rule and ProofProfile refs;
- the Spend issuer registry and Spend verification policy;
- the Spend-acceptance snapshot and its root plus tree profile;
- the Trusted Platform Product Signers binding and product-verification policy;
- product, brand, and category registry snapshots;
- the product-evidence snapshot and its `entriesRoot` plus tree profile;
- the evidence-status snapshot and its cutoff policy;
- proof-replay, purchase-reuse, and entitlement registries; and
- the selected validator assignment required by the ProcedureProfile.

Registry membership alone does not establish authority. Each snapshot must
carry or resolve the profile-defined authority signature, version, cutoff, leaf
encoding, tree construction, and non-equivocation evidence.

## Private witness

The prover supplies only inside the authorized proving boundary:

- the complete Spend Token and its admission evidence;
- `ProductPurchaseAttestationV1`;
- the canonical conversion rule and its opening;
- Spend issuer membership and exact trusted Platform product signer binding;
- product, brand, and category membership paths;
- evidence-status membership and non-terminal-status evidence at the cutoff;
- the recipient-binding proof and recipient-scope opening;
- the product-purchase and rule commitment openings; and
- the secrets required for the three domain-separated nullifiers.

The profile does not permit raw witness material to be sent to Proof
Validators.

Spend admission, product-evidence admission, entity relationships, and status
use the authenticated snapshot contract in
[`product-evidence-snapshots-v1.md`](./product-evidence-snapshots-v1.md).

## Product-purchase attestation contract

[`ProductPurchaseAttestationV1`](./product-purchase-attestation-v1.md) is the
private canonical artifact consumed by this relation. It uses
`PRODUCT_EVIDENCE_SNAPSHOT_MEMBERSHIP_V1`: the validator verifies the public
issuer-signed snapshot authority, and the circuit proves membership of the
private field-native product-purchase commitment. Its exact fields are:

```text
attestationId
productIssuerId
issuerKeyRef
productVerificationPolicyRef
spendBinding { spendId, spendTokenHash, canonicalHeadEventHash }
productFacts {
  productRef
  brandRef
  categoryRefs
  purchasedAtUnixMs
  quantity
  netProductAmountMinor
  currency
}
recipientBindingCommitment
evidenceStatusEntryRef
supersedesProductPurchaseCommitment
productPurchaseCommitment
authentication { mode, snapshotRef, leafIndex }
issuedAt
```

The linked contract freezes field bounds, decimal and currency rules,
timestamp precision, category ordering, canonical bytes, authentication,
field-native commitment construction, and correction/supersession semantics.
The circuit must establish authenticity without disclosing the artifact or
its private product facts.

## Closed rule and dependency language

The canonical rule is
[`SingleProductPurchaseRuleV1`](../../../schemas/experimental/campaigns/single_product_purchase_rule_v1.schema.json).
Its identity and the public `ruleCommitment` are identical:

```text
ruleCommitment = "sha256:" + hex(SHA-256(UTF8(RFC8785(rule))))
```

The rule is a conjunction over one product-purchase event. Every non-null
field applies to that same event. At least one of `productRef`, `brandRef`, or
`categoryRef` is non-null. `minimumUnixMs <= maximumUnixMs` is mandatory when
the time predicate is present. Unknown fields, overflow, mixed currencies,
unsorted categories, and substitutions of another dependency set are invalid.

The rule's `dependencySetRef` resolves exactly one
[`SingleProductPurchaseDependenciesV1`](../../../schemas/experimental/campaigns/single_product_purchase_dependencies_v1.schema.json).
The Epoch's `conversionRuleRef` must equal `ruleCommitment`; the Epoch's
`registryRefs` must contain the dependency-set ref and every reference carried
by that dependency set. Business-selected values such as `MONSTER`, quantity
`1`, and a fourteen-day window are rule values, not circuit constants or
profile identities.

## Typed named public inputs

The envelope encoding is `RFC8785_NAMED_COMMITMENTS_V1`. Every entry contains
`name`, `valueType`, `value`, and `valueCommitment`. The exact order is:

1. `proofProfileRef` — `SHA256_REF`
2. `purpose` — `ENUM`, exactly `CONVERSION`
3. `proofId` — `IDENTIFIER`
4. `campaignId` — `IDENTIFIER`
5. `campaignEpochRef` — `SHA256_REF`
6. `ruleCommitment` — `SHA256_REF`
7. `scopeRef` — `SHA256_REF`
8. `inputSetCommitment` — `SHA256_REF`
9. `spendTokenBinding` — `SHA256_REF`
10. `canonicalHeadBinding` — `SHA256_REF`
11. `spendIssuerRegistryRef` — `SHA256_REF`
12. `spendVerificationPolicyRef` — `SHA256_REF`
13. `spendAcceptanceSnapshotRef` — `SHA256_REF`
14. `spendAcceptanceSnapshotRoot` — `POSEIDON_FP`
15. `spendAcceptanceSnapshotTreeProfileRef` — `SHA256_REF`
16. `productSourceSignerAuthorityBindingRef` — `SHA256_REF`
17. `productVerificationPolicyRef` — `SHA256_REF`
18. `productRegistrySnapshotRef` — `SHA256_REF`
19. `productRegistryRoot` — `POSEIDON_FP`
20. `productRegistryTreeProfileRef` — `SHA256_REF`
21. `brandRegistrySnapshotRef` — `SHA256_REF`
22. `brandRegistryRoot` — `POSEIDON_FP`
23. `brandRegistryTreeProfileRef` — `SHA256_REF`
24. `categoryRegistrySnapshotRef` — `SHA256_REF`
25. `categoryRegistryRoot` — `POSEIDON_FP`
26. `categoryRegistryTreeProfileRef` — `SHA256_REF`
27. `productEvidenceSnapshotRef` — `SHA256_REF`
28. `productEvidenceSnapshotRoot` — `POSEIDON_FP`
29. `productEvidenceSnapshotTreeProfileRef` — `SHA256_REF`
30. `evidenceStatusSnapshotRef` — `SHA256_REF`
31. `evidenceStatusRoot` — `POSEIDON_FP`
32. `evidenceStatusTreeProfileRef` — `SHA256_REF`
33. `statusCutoffUnixMs` — `UNIX_MS`
34. `recipientScopeCommitment` — `SHA256_REF`
35. `proofReplayInputsCommitment` — `SHA256_REF`
36. `proofReplayNullifier` — `SHA256_REF`
37. `purchaseReuseNullifier` — `SHA256_REF`
38. `entitlementNullifier` — `SHA256_REF`
39. `resultCommitment` — `SHA256_REF`

The raw values are resolved from the ProofProfile, envelope, rule, dependency
set, and signed snapshots. A validator must recompute them; a caller-supplied
value cannot select a different dependency.

For each entry:

```text
valueCommitment = "sha256:" + hex(SHA-256(UTF8(RFC8785({
  domain: "crinkl:proof-of-match:public-input:v1",
  name,
  valueType,
  value
}))))
```

`ProofOfMatchV1.publicInputsCommitment` is:

```text
"sha256:" + hex(SHA-256(UTF8(RFC8785({
  domain: "crinkl:proof-of-match:public-input-set:v1",
  encoding: "RFC8785_NAMED_COMMITMENTS_V1",
  entries: publicInputs
}))))
```

The Halo2 instance vector contains the 39 decoded `valueCommitment` digests.
Each digest is split into unsigned 128-bit big-endian high and low limbs,
without field reduction, producing exactly 78 instance elements. Duplicate,
missing, additional, reordered, mistyped, or incorrectly committed entries are
invalid.

`evaluatedRuleCommitment`, `ruleCommitment`, and the resolved Epoch
`conversionRuleRef` must be equal. `proofProfile.profileRef`, `circuitId`, key,
transcript, proof encoding, public-input encoding, and the resolved profile
must also agree exactly.

## Bindings and nullifiers

`holderPublicKeyBytes` is the exact private 32-byte Ed25519 public key that
opens the accepted Spend Token's signed `crinkl.holder.v2` commitment. The
circuit recomputes that commitment using the portable Spend Token V2 rule and
requires equality with the Spend-acceptance leaf. It then derives:

```text
recipientScopeSecret = SHA-256(
  UTF8("CRINKL:POM:RECIPIENT_SCOPE_SECRET:SINGLE_PRODUCT_PURCHASE_MATCH:V1") ||
  0x00 || holderPublicKeyBytes || digest(scopeRef)
)
```

`digest(ref)` removes the `sha256:` prefix and returns the 32 digest bytes.
`poseidonBytes(value)` removes the `poseidon:` prefix and returns the canonical
32-byte Pasta Fp encoding. All concatenations below are byte concatenations and
`0x00` is one byte.

```text
recipientScopeCommitment = "sha256:" + hex(SHA-256(
  UTF8("CRINKL:POM:RECIPIENT_SCOPE:SINGLE_PRODUCT_PURCHASE_MATCH:V1") ||
  0x00 || recipientScopeSecret
))

spendTokenBinding = "sha256:" + hex(SHA-256(
  UTF8("CRINKL:POM:SPEND_TOKEN_BINDING:SINGLE_PRODUCT_PURCHASE_MATCH:V1") ||
  0x00 || digest(spendTokenHash) || recipientScopeSecret
))

canonicalHeadBinding = "sha256:" + hex(SHA-256(
  UTF8("CRINKL:POM:CANONICAL_HEAD_BINDING:SINGLE_PRODUCT_PURCHASE_MATCH:V1") ||
  0x00 || digest(canonicalHeadEventHash) || recipientScopeSecret
))
```

For this single-input profile, `inputSetCommitment` is the RFC 8785/SHA-256
content reference of:

```json
{
  "domain": "crinkl:pom:single-product-input-set:v1",
  "inputs": [{
    "inputIndex": 0,
    "spendTokenBinding": "<exact binding>",
    "canonicalHeadBinding": "<exact binding>",
    "issuerRegistryRef": "<exact dependency value>",
    "verificationPolicyRef": "<exact dependency value>",
    "purchaseReuseNullifier": "<exact nullifier>"
  }]
}
```

`proofReplayInputsCommitment` is the RFC 8785/SHA-256 content reference of:

```text
{
  domain: "crinkl:pom:proof-replay-inputs:v1",
  entries: [
    valueCommitment entries 1 through 34 in profile order,
    valueCommitment entry 37,
    valueCommitment entry 38,
    valueCommitment entry 39
  ]
}
```

Each element in `entries` is the complete lowercase `sha256:` string. This
construction excludes itself and `proofReplayNullifier`, so it has no cycle;
it includes `proofId` through entry 3.

The three nullifiers are:

```text
proofReplayNullifier = "sha256:" + hex(SHA-256(
  UTF8("CRINKL:POM:PROOF_REPLAY:SINGLE_PRODUCT_PURCHASE_MATCH:V1") || 0x00 ||
  digest(proofReplayInputsCommitment) || recipientScopeSecret
))

purchaseReuseNullifier = "sha256:" + hex(SHA-256(
  UTF8("CRINKL:POM:PURCHASE_REUSE:SINGLE_PRODUCT_PURCHASE_MATCH:V1") || 0x00 ||
  digest(valueCommitment("campaignId")) ||
  digest(valueCommitment("campaignEpochRef")) ||
  digest(valueCommitment("purpose")) ||
  poseidonBytes(productPurchaseCommitment) || recipientScopeSecret
))

entitlementNullifier = "sha256:" + hex(SHA-256(
  UTF8("CRINKL:POM:ENTITLEMENT:SINGLE_PRODUCT_PURCHASE_MATCH:V1") || 0x00 ||
  digest(valueCommitment("campaignId")) ||
  digest(valueCommitment("campaignEpochRef")) ||
  digest(valueCommitment("purpose")) ||
  digest(ruleCommitment) ||
  poseidonBytes(productPurchaseCommitment) || recipientScopeSecret
))

resultCommitment = "sha256:" + hex(SHA-256(
  UTF8("CRINKL:POM:RESULT:SINGLE_PRODUCT_PURCHASE_MATCH:V1") || 0x00 ||
  UTF8("MATCH")
))
```

The circuit computes every private-dependent binding and nullifier. The
validator recomputes every public-only commitment and checks each nullifier in
the registry named by the dependency set. Because this profile is conversion
only, the entitlement nullifier and registry are mandatory and never null.

## Disclosure

Proof Validators learn the exact profile, Campaign, Epoch, purpose, committed
rule result, scoped nullifiers, result, and pinned registry and policy refs.
They do not learn the buyer, Spend Token, product, brand, merchant, quantity,
amount, recipient opening, or purchase history.

The product or brand may still be guessable from a Campaign's public rule or
registry selection. The ZK relation prevents witness disclosure; it does not
make public Campaign policy secret.

## Stable failures

```text
UNSUPPORTED_PROOF_PROFILE
PROFILE_ARTIFACT_UNAVAILABLE
VERIFIER_KEY_UNAVAILABLE
UNSUPPORTED_PROOF_ENCODING
PUBLIC_INPUT_SHAPE_MISMATCH
PROOF_VERIFICATION_FAILED
```

Schema, authority, registry, status, replay, assignment, and ProcedureProfile
failures remain separately typed by their owning contracts. Implementations
must not collapse an unavailable key or unsupported encoding into a false
cryptographic result.

## Profile, circuit, and implementation identity

The adopted object uses the strict
[`ProofProfileV1`](../../../schemas/experimental/campaigns/proof_profile_v1.schema.json)
schema. The canonical ProofProfile binds:

```text
profileId
profileVersion
purpose
relationRef
proofSystem
curveFamily
circuitId
verifyingKeyRef
transcriptBindingRef
proofEncodingRef
publicInputEncodingRef
publicInputOrder
treeProfileRefs
conformanceSuiteRef
```

Its identity is:

```text
proofProfileRef = "sha256:" + SHA-256(RFC8785(complete ProofProfile bytes))
```

Executable, container, source-commit, compiler, operating-system, CPU, GPU,
FPGA, and architecture hashes are not part of `proofProfileRef`. They belong
to separately admitted implementation manifests. Multiple independent prover
or verifier implementations may implement this same profile when their proof
bytes interoperate with the pinned verifier contract and they pass the exact
conformance suite.

A faster implementation does not create a new ProofProfile. A change to the
relation, proof system, circuit constraints, verifying key, transcript, proof
encoding, public-input encoding/order, registry encoding, or nullifier
derivation requires a new immutable profile identity.
