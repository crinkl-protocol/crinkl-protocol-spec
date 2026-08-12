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

State the artifact-scoped compatibility rule precisely: the Campaign and Boost
prototypes do not impose predecessor vocabulary on the target specification,
while every implementation change remains subject to evidence about actual
wire consumers, persisted state, release identity, and deployed dependencies.

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

## Alpha replacement and compatibility boundary

1. The Campaign object family has no deployed or production consumer. Its
   discarded draft names and shapes receive no aliases, adapters, deprecation
   objects, or successor mappings in the living specification.
2. The canonical Campaign families introduced by this refactor start at V1,
   including `CampaignEpochV1`.
3. Published Git tags and their release payloads remain immutable historical
   evidence. They do not make discarded Campaign drafts supported predecessors
   and are not linked from the living Campaign specification.
4. Spend Token schemas, issuer verification policy, issuer-key history,
   attestation status, canonical Spend Stream heads, and the SOFT-to-HARD
   verification pipeline are confirmed compatibility-sensitive surfaces and
   remain unchanged in this slice. This inventory is not an exhaustive claim
   about every wire- or production-sensitive artifact in Crinkl.
5. `AssignmentRecord` remains a portable object only where a relying profile
   names a cross-system, dispute, or independent-consumer need.
6. The signed target object families share one explicit RFC 8785 + SHA-256 +
   Ed25519 object-reference construction. `ProofOfMatch` and
   `ValidatorCertificate` retain their separately defined subject/decision hash
   constructions.
7. The new schemas remain `SPECIFIED_NOT_IMPLEMENTED` source candidates outside
   every released manifest until separately adopted, reviewed, versioned,
   published, and implemented.
8. `PROOF_OF_MATCH_VERIFICATION` is the only required validator procedure.
   Campaign admission is added only if a future design proves a distinct trust
   failure, consumer, and state transition.
9. Compatibility standing is decided per artifact. Evidence includes an
   external or cross-system wire consumer, persisted state, an immutable
   released identity, a deployed runtime dependency, or another relying party.
   `IMPLEMENTED`, `PROTOTYPE`, and other maturity labels neither establish nor
   eliminate that evidence by themselves.
10. Campaign and Boost prototype names, envelopes, statement identifiers, and
    procedure semantics are not canonical predecessors merely because source
    code or tests exist. A later implementation refactor must still inventory
    their exact producers, consumers, stored payloads, and runtime dependencies
    before removing or changing implementation code.

## Work sequence

The atomic execution board is
[`campaign-architecture-refactor-board-2026-08-12.md`](campaign-architecture-refactor-board-2026-08-12.md).

## Completion

Complete. The living Campaign specification has one reduced vocabulary and
seven first canonical V1 schema families. Campaign and Boost prototype
artifacts impose no predecessor aliases or translation burden on that target.
Compatibility and break risk are evaluated per artifact from exact consumer,
persisted-state, release, and deployed-dependency evidence; prototype status
alone is not a removal-safety conclusion. Immutable release evidence remains
unchanged, as do the confirmed Spend Token and SOFT-to-HARD surfaces in this
slice. Local schema, conformance, link, release-integrity, drift, and boundary
gates pass; the repository's pre-existing identifier-inventory defect remains
separately recorded in the evidence receipt.
