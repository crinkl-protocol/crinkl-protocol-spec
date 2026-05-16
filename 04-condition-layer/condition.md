---
status: draft
layer: condition
version: v1
normative: true
---

# Condition

A Condition is a rule over one or more Spend Attestations. Conditions are downstream of attestations: they do not create spend truth and they do not mint Spend Attestation Tokens.

Examples include threshold, merchant, category, market, new-buyer, repeat-spender, and time-window rules. Implementations SHOULD express Conditions as parameterized rules over finite proof primitives rather than custom campaign logic.
