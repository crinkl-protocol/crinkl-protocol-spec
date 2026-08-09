---
status: draft
layer: predicate
version: v1
normative: true
---

# Spend Predicate Evaluation

Spend Predicate Evaluation consumes Spend Attestations or privacy-preserving proofs over Spend Attestations and returns whether the predicate is satisfied under an explicit scope and time window.

Evaluation MUST bind the predicate parameters, version, scope, verifier policy, and replay/nullifier rules where payment or settlement depends on the result. Evaluation MUST NOT require raw receipt access or user identity unless a downstream profile explicitly requires recipient binding.

See `campaign-commitment.md` for the current draft campaign rule composition surface.
