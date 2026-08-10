---
status: draft
layer: predicate
version: v1
normative: true
---

# Spend Predicate Evaluation

Spend Predicate Evaluation consumes Spend Attestations or privacy-preserving proofs over Spend Attestations and returns whether the predicate is satisfied under an explicit scope and time window.

Evaluation MUST bind the predicate parameters, version, scope, verifier policy, and replay/nullifier rules where payment or settlement depends on the result. Evaluation MUST NOT require raw receipt access or user identity unless a downstream profile explicitly requires recipient binding.

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

See `campaign-commitment.md` for the current draft campaign rule composition surface.
