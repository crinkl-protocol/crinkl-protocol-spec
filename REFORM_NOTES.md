---
status: draft
layer: governance
version: v1
normative: false
---

# Reform Notes

This file records semantic tensions found during the proof-lifecycle refactor instead of silently deleting conflicting material.

## Preserved Meaning

Existing cryptographic, event, token, commitment, ZK, campaign, and conformance material was moved into lifecycle-oriented layers. The refactor is documentation architecture only.

## Corrected or Flagged Tensions

- Wallet scope: internal spend streams may be wallet-scoped, but portable Spend Attestation Tokens remain identity-excluded by default.
- Rewards and aggregate tokens: Reward Commitment, GMV, and Distribution Token material is downstream of Spend Attestation and belongs in reward/settlement docs, not Core.
- Downstream schemas: reward policy schemas now live with reward/settlement, and store registry schemas now live with the store-registry extension. Core retains only the event schema needed for spend proof replay.
- Campaigns and promos: campaign rule composition belongs in the condition layer; offer delivery, encrypted envelopes, and brand/wallet message profiles are extensions.
- Revocation language: v1 has correction, invalidation, and rejection semantics. A distinct `revoked` verification state is not introduced by this refactor.
- ZK: ZK proof material remains optional extension material; it is not required for Core Spend Attestation validity.
