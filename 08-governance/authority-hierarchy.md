---
status: draft
layer: governance
version: v1
normative: true
---

# Authority Hierarchy

Protocol authority follows the proof lifecycle. Core definitions of evidence, spend events, verification state, canonicalization, signatures, privacy boundaries, portability, verifier requirements, and conformance come before downstream profiles.

Downstream layers may depend on Core; Core MUST NOT depend on campaigns, rewards, Solana, ZK, MCP, REST, agents, ads, brand budgets, or promotion logic.

Normative conflicts should be resolved by this order: purpose, core, lifecycle, portability, condition, reward-settlement, extension, conformance, governance.
