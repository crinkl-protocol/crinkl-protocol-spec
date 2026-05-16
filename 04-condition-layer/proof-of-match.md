---
status: draft
layer: condition
version: v1
normative: true
---

# Proof of Match

Proof of Match is the result of evaluating one or more Spend Attestations against a Condition. It proves that the referenced attestations satisfy the condition within a declared scope.

Proof of Match is downstream of Spend Attestation and upstream of Reward Commitment, settlement, campaigns, analytics, or agent responses. It MUST NOT be treated as a new Spend Attestation and MUST NOT mutate the underlying spend proof.
