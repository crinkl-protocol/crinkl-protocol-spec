---
status: draft
layer: predicate
version: v1
normative: true
---

# Spend Predicate Evaluation

Spend Predicate Evaluation consumes Spend Tokens or privacy-preserving proofs
over Spend Tokens and returns whether the predicate is satisfied under an
explicit scope and time window. `SpendToken` is the Campaign-layer short name
for a supported Spend Attestation Token; no Spend wire is changed here.

Evaluation MUST bind the predicate parameters, version, scope, verifier policy,
and replay/nullifier rules where an Outcome or economic entitlement depends on
the result. Evaluation MUST NOT require raw receipt access or user identity
unless a downstream profile explicitly requires recipient binding.

`SpendPredicateV1` carries those bindings as `parameters`,
`predicateVersion`, `evaluationContext.scopeId`,
`evaluationContext.verifierPolicyRef`, and
`evaluationContext.replayNullifierRules`. `parameters`, `ruleExpression`, and
`replayNullifierRules` are non-empty profile-defined objects. Their complete
contents are part of the predicate commitment.

`predicateHash` is `"sha256:" + lowercaseHex(SHA-256(JCS(predicate)))`, where
JCS is RFC 8785 canonical JSON and the top-level `predicateHash` member is the
only omitted member. Verifiers MUST reject a predicate whose declared hash
does not equal that recomputation.

For Campaign use, the predicate or private rule bytes are committed by one
`CampaignEpoch`, and successful private evaluation is represented by one
[`ProofOfMatch`](proof-of-match.md) with purpose `AUDIENCE` or `CONVERSION`.
The proof relation MUST enforce:

```text
evaluatedRuleCommitment = CampaignEpoch rule commitment for the declared purpose
```

Multiple Spend inputs, purchase distinctness, aggregation, observable-history
boundaries, and purchase/entitlement reuse rules are profile-defined proof
requirements, not implied by a boolean predicate result. See the
[`Campaign architecture`](../campaigns/README.md).
