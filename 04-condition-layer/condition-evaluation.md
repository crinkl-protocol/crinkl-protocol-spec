---
status: draft
layer: condition
version: v1
normative: true
---

# Condition Evaluation

Condition Evaluation consumes Spend Attestations or privacy-preserving proofs over Spend Attestations and returns whether the condition is satisfied under an explicit scope and time window.

Evaluation MUST bind the condition parameters, version, scope, verifier policy, and replay/nullifier rules where payment or settlement depends on the result. Evaluation MUST NOT require raw receipt access or user identity unless a downstream profile explicitly requires recipient binding.

See `campaign-commitment.md` for the current draft campaign rule composition surface.
