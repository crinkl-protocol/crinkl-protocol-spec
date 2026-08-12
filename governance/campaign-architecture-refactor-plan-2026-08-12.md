---
status: complete
layer: governance
version: v1
normative: false
---

# Campaign architecture refactor plan — 2026-08-12

## Plan anchor

This page is the durable plan for the public-specification-only refactor of the
Campaign vocabulary. The controlling architecture is documented in
[`../protocol/applications/campaigns/README.md`](../protocol/applications/campaigns/README.md).

## Exact source baseline

| Source | Branch | Commit | Use in this slice |
|---|---|---|---|
| `crinkl-protocol-spec` | `origin/main` | `700be7942efecb5863acb764f004b122f9e3c5fa` | edited public specification |
| `crinkl-protocol` | `origin/main` | `47df2a1f6bdb7aa53d70060401cd0297e2547362` | adopted object and escrow-profile evidence |
| `crinkl-platform` | `origin/main` | `42d28cc06f8456cf293f9eded04c3726e1b706af` | current alpha runtime evidence only |
| `crinkl-proof-validator` | `origin/main` | `e282562da6a2f1edac5a97d7ae4591023c8453a5` | validator handoff gap evidence only |
| `campaign-escrow-program` | `origin/main` | `8f29e539c2360b16fc2c08de20262ea5c289c324` | candidate escrow execution evidence only |

No implementation repository is modified by this slice. A source implementation,
adopted engineering protocol object, public specification, public release,
runtime support, validator-network adoption, and production deployment remain
separate evidence-bearing states.

## Current slice

Refactor public campaign language and add compatibility-safe target schemas.

## Objective

Make one composable campaign spine precise without mutating published wire
formats or claiming that the target is deployed:

```text
SpendToken
-> CampaignEpoch
-> optional ProofOfMatch(AUDIENCE)
-> optional AssignmentRecord / exposure
-> ProofOfMatch(CONVERSION)
-> optional economic admission
-> CampaignOutcome
-> optional RewardObligation
-> SettlementRecord
```

## Non-goals

- no Spend Token redesign;
- no Platform, gateway, proof-service, validator, escrow, or Reward Ledger code;
- no public release, manifest promotion, tag, or deployment;
- no new object for exposure, reporting, FIFO, offer delivery, or orchestration;
- no claim that commitments, hashes, signed evidence, or packages are ZK proofs.

## Compatibility strategy

1. Preserve every released and published V1 schema byte-for-byte.
2. Add `CampaignEpochV2` because direct campaigns, optional audience rules,
   optional assignment and economic admission policies, and exact proof-profile
   commitments change the required signed shape.
3. Add first versions of the previously unserialized `ProofOfMatch`, generic
   `ValidatorCertificate`, `AssignmentRecord`, `CampaignOutcome`,
   `RewardObligation`, and `SettlementRecord` families. Retain
   `AssignmentRecord` as a portable object only where a relying profile names a
   cross-system, dispute, or independent-consumer need.
   The five signed object families share one explicit RFC 8785 + SHA-256 +
   Ed25519 object-reference construction; ProofOfMatch and ValidatorCertificate
   retain their separately defined subject/decision hash constructions.
4. Deprecate `RewardCommitment` as the canonical liability name without
   mutating the adopted `RewardCommitmentV1` family; map it explicitly to the
   new `RewardObligationV1` successor family.
5. Treat the new schemas as `SPECIFIED_NOT_IMPLEMENTED` source candidates.
   They are outside every released manifest until separately adopted, reviewed,
   versioned, published, and implemented.
6. Treat `PROOF_OF_MATCH_VERIFICATION` as the only required validator
   procedure. Retain or define Campaign admission only if the repository
   inventory proves a distinct trust failure, consumer, or state transition.
7. Preserve legacy documents and names as explicit compatibility mappings
   until their inbound references are migrated.

## Work sequence

The atomic execution board is
[`campaign-architecture-refactor-board-2026-08-12.md`](campaign-architecture-refactor-board-2026-08-12.md).

## Completion

The specification-only slice is complete. Seven additive schema candidates,
the normative reduced architecture, compatibility mappings, conformance
narratives, implementation-status inventory, and validator handoff are present.
No released manifest, published V1 bytes, implementation repository, runtime,
validator network, escrow state, Reward Ledger, deployment, or production
service was changed.
