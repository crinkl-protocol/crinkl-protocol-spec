---
status: draft
layer: governance
version: v1
normative: false
---

# Single Product ProofProfile Rollout Plan — 2026-08-13

Plan anchor: protocol-conformance POM-05.

Objective: adopt the first content-addressed ProofProfile and give the circuit
and validator teams a deterministic implementation contract without binding
the profile to one executable or hardware backend.

Revision: 2026-08-13T02:00:00Z

| ID | Status | Owner | Exit condition |
|---|---|---|---|
| SPF-01 | done | protocol-spec | `ProofOfMatchV1` represents the official circuit, proof/public-input encoding refs, typed public values, and product-evidence witness category. |
| SPF-02 | done | protocol-spec | The conversion rule, dependency set, Spend acceptance, product evidence, entity registries, status entries, snapshots, and common tree profile are canonical and linked. |
| SPF-03 | done | protocol-spec | Public-input commitments, input-set binding, proof replay, purchase reuse, entitlement, recipient scope, result, and `proofId` binding have exact preimages and hostile vectors. |
| SPF-04 | done | protocol-conformance | The machine-readable build contract and conformance vectors pin all 39 typed inputs, 78 instance elements, object schemas, and initial hostile dependency mutations. |
| SPF-05 | pending external return | circuit team | Return source/dependency lock, relation manifest, parameters, verifying key, transcript, proof encoding, public-input encoding, positive proof, hostile proofs, and performance evidence. |
| SPF-06 | pending | protocol-spec | Assemble the complete immutable ProofProfile, compute `proofProfileRef`, and adopt it through the authority process. |
| SPF-07 | in progress | crinkl-zk-verifier | Package, binary, environment, fixture, and source names use verifier terminology; the profile-driven command and implementation manifest await the circuit return packet. |
| SPF-08 | pending | crinkl-proof-validator | Resolve the adopted profile and dependencies, enforce prechecks, invoke `DriverContractV1`, and pass the complete conformance suite. |

POM-05 remains blocked until SPF-06. SPF-01 through SPF-04 are the completed
protocol handoff gate and do not depend on compiled proof bytes. The circuit
team may begin from the build contract. The validator team may implement schema,
resolution, authority, typed-input, and fail-closed adapter scaffolding against
SPF-04, but must return `PROFILE_ARTIFACT_UNAVAILABLE` until SPF-06 and SPF-07
are complete.

The proof-byte contract is the exact `proofEncodingRef` returned by the circuit
team. A JSON Schema Base64 minimum length is not a cryptographic proof-size
contract.

## Adoption invariants

- `proofProfileRef` binds the relation, proof system, circuit, verifying key,
  transcript, proof encoding, public-input encoding, and input order.
- Executable, container, compiler, CPU, GPU, FPGA, service, and deployment
  identity belong to an implementation manifest, not the ProofProfile.
- A proof-compatible optimized implementation does not create a new profile.
- A relation, key, transcript, encoding, tree, commitment, or nullifier change
  creates a new immutable profile identity.
- Prototype circuit identifiers are historical evidence only and are never
  aliases or predecessors in the official profile identity.
