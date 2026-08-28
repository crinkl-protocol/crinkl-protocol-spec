---
status: draft
layer: applications
version: v1
normative: true
---

# H2 Single Product Purchase Match V1

`H2_SINGLE_PRODUCT_PURCHASE_MATCH_V1` is the only circuit identity authorized
for the initial `SINGLE_PRODUCT_PURCHASE_MATCH_V1` ProofProfile. This document
defines the implementation handoff required to turn that specified relation
into an immutable, interoperable verifier contract.

The circuit implements the relation in
[`single-product-purchase-match-v1.md`](./single-product-purchase-match-v1.md).
Its exact input order and required return fields are mirrored by the
[`machine-readable build contract`](../artifacts/single_product_purchase_match_v1_build_contract.json).
When the two documents conflict, the ProofProfile relation controls and the
circuit implementation must stop for a specification decision.

## Cryptographic family

The official tuple is:

```text
proofSystem: HALO2_IPA
curveFamily: PASTA
circuitId: H2_SINGLE_PRODUCT_PURCHASE_MATCH_V1
```

The implementation team must freeze the exact Halo2 protocol, polynomial
commitment parameters, transcript construction, challenge encoding, proof-byte
serialization, verifier-key serialization, and security parameter before the
profile can be adopted. A library default is not a protocol definition.

## Circuit boundary

The circuit proves private relations and private membership paths. The
validator performs authenticated public dependency checks before invoking the
circuit verifier. The implementation must not silently move a required check
out of either boundary.

The validator-side prechecks are:

- exact ProofProfile, Epoch, purpose, rule, dependency-set, and ProcedureProfile
  binding;
- signatures and authority on the Epoch and public registry snapshots;
- snapshot version, cutoff, freshness, and non-equivocation checks;
- selected-validator assignment and supported-version checks;
- proof-byte hash, named-public-input shape, and implementation admission; and
- replay-registry reads required by the ProcedureProfile.

The circuit constraints are:

- one Spend Token witness and one product-purchase witness;
- reconstruction and membership of the Spend-acceptance entry under the public
  Spend-acceptance snapshot root;
- equality of their Spend ID, Spend Token hash, and canonical-head hash;
- authenticated membership of the private product-purchase commitment in the
  accepted product-evidence snapshot;
- equality of the attestation snapshot reference and leaf index with the
  resolved snapshot and membership-path position;
- product, brand, and category membership under the public roots and committed
  tree profiles;
- exact evaluation of the committed closed rule over the same purchase;
- accepted evidence status at the exact `statusCutoffUnixMs` with equality to
  the dependency set and signed status-snapshot cutoff;
- RFC 8785/SHA-256 equality of the witnessed status entry and the attestation's
  `evidenceStatusEntryRef`;
- recipient-binding and recipient-scope-opening validity;
- domain-separated proof-replay, purchase-reuse, and entitlement nullifiers;
- equality of evaluated and Epoch-bound rule commitments;
- all 39 typed named public commitments; and
- a `MATCH` result commitment only when every enabled constraint is true.

## Instance encoding

The circuit receives the 39 named `sha256:` value commitments in the exact order
defined by `SINGLE_PRODUCT_PURCHASE_MATCH_V1`. Each decoded 32-byte digest is
split without reduction:

```text
high = unsigned_big_endian(bytes[0..16])
low  = unsigned_big_endian(bytes[16..32])
```

The instance vector is:

```text
[name[0].high, name[0].low, ..., name[38].high, name[38].low]
```

Every limb is range-constrained to 128 bits. The adapter recomputes every typed
value commitment and the complete public-input-set commitment before invoking
the verifier. Implementations must reject wrong counts, ordering, names,
types, values, prefixes, lengths, non-lowercase hex, or values that disagree
with the `ProofOfMatchV1` envelope.

The circuit implements SHA-256 for the fixed binding and nullifier preimages
defined by the ProofProfile. Substituting Poseidon, reducing a SHA-256 digest to
one field element, or treating an unconstrained host-computed digest as a
private relation check is prohibited.

## Spend evidence authentication

The circuit implements the Spend-acceptance leaf relation in
[`product-evidence-snapshots-v1.md`](./product-evidence-snapshots-v1.md). The
validator verifies the signed snapshot and its exact issuer-registry and policy
refs. The circuit reconstructs the private leaf from the admitted Spend Token,
proves membership under `spendAcceptanceSnapshotRoot`, and reuses the same
Spend ID, token hash, head hash, and holder-binding opening in every downstream
constraint. Validators do not receive the token.

## Product evidence authentication

The circuit implements
[`PRODUCT_EVIDENCE_SNAPSHOT_MEMBERSHIP_V1`](./product-purchase-attestation-v1.md#product-evidence-authentication).
Proof Validators do not receive raw product facts. The field-native commitment
binds:

- issuer and key identity;
- product-verification policy;
- Spend ID, Spend Token hash, and canonical head;
- product, brand, categories, purchase time, quantity, net product amount, and
  currency;
- issuance and supersession identity.

Evidence-status identity is not inside the product-purchase commitment because
that would make the status entry circular. The separate authenticated status
leaf binds the recomputed product-purchase commitment, its status, cutoff, and
replacement commitment.

The validator verifies the issuer-signed product-evidence snapshot against the
Epoch-bound Trusted Platform Product Signers binding and policy before proof verification. The
`productEvidenceSnapshotRoot` and
`productEvidenceSnapshotTreeProfileRef` are resolved publicly and must agree
with the relation. The circuit recomputes the private commitment and proves its
snapshot membership under that root and tree profile. The root, leaf, path,
domain, empty-leaf, and tree rules are frozen by the content-addressed depth-32
tree profile. The implementation cannot substitute direct signature disclosure
or an implementation-local leaf.

## Registry encoding

Product, brand, category, Spend-acceptance, product-evidence, and status
registries use the schemas and common tree contract in
[`product-evidence-snapshots-v1.md`](./product-evidence-snapshots-v1.md), which
freeze:

```text
registry object schema and authority
leaf schema and canonical ordering
hash and field encoding
tree arity and depth
empty-leaf construction
duplicate and normalization rules
membership-path encoding
snapshot time and cutoff semantics
```

The product registry leaf binds the selected product to its brand and category
set; independent membership of unrelated entries cannot satisfy the relation.
Brand strings such as `MONSTER` are never hashed directly by an
implementation-local convention. The proof uses the exact registered entity
reference and registry encoding selected by the Epoch.

## Artifact separation

The ProofProfile binds the interoperable verifier contract:

```text
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

An implementation manifest binds one implementation:

```text
profileRef
relationRef
implementationRef
sourceCommit
dependencyLockRef
toolchainRef
target
binaryRef | containerRef | serviceAttestationRef
supportedOperations
conformanceEvidenceRef
benchmarkEvidenceRef
admissionStatus
```

CPU, GPU, FPGA, WASM, native, and service implementations may share the same
ProofProfile. A different binary or implementation hash does not change the
profile when it remains proof-compatible with the exact verifier contract.

## Required implementation return packet

The implementation team returns all of the following as immutable evidence:

1. circuit source commit and complete dependency lock;
2. relation manifest and `relationRef`;
3. exact security parameter and parameter-generation procedure;
4. canonical verifier-key bytes and `verifyingKeyRef`;
5. canonical transcript profile and `transcriptBindingRef`;
6. canonical proof encoding and `proofEncodingRef`;
7. canonical public-input encoding and `publicInputEncodingRef`;
8. positive proof fixture with no private witness persisted;
9. hostile vectors for every public input and every relation clause;
10. cross-build proof/verifier interoperability evidence;
11. CPU correctness and performance evidence;
12. implementation manifest with its binary or service artifact refs; and
13. a deterministic verifier command suitable for `DriverContractV1`.

Performance evidence records setup, key generation, proof, verification,
memory, proof size, concurrency, warm/cold state, target, and build profile.
Performance does not alter validity and no minimum performance claim is part of
the ProofProfile.

## Closure rule

The implementation packet is acceptable only when an independent verifier can
resolve the exact refs, verify the positive fixture, reject every hostile
fixture, and reproduce the profile hash without relying on an implementation
repository for expected semantics.

Until then, the profile remains `SPECIFIED_NOT_IMPLEMENTED`, and validators
return `PROFILE_ARTIFACT_UNAVAILABLE` rather than a certificate.
