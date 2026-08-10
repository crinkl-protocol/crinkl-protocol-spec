---
status: experimental
layer: extension
version: v1
normative: true
---

# Agent Query Extension

Agent-facing query surfaces are optional extensions. They may ask for spend proofs, predicates, or aggregate commitments, but they do not define Core proof validity.

An agent query extension MUST preserve the proof lifecycle: evidence before claims, claims before attestations, attestations before predicates, and predicates before rewards, campaigns, agents, or markets.

No agent extension may require checkout authority, payment authorization, or user identity as a Core protocol precondition.
