---
status: draft
layer: governance
version: v1
normative: false
---

# Campaign architecture evidence and implementation status

This document records the repository evidence used to define the canonical
Campaign vocabulary in
[`../protocol/applications/campaigns/README.md`](../protocol/applications/campaigns/README.md).
It is an evidence and implementation-status record, not a predecessor migration
guide.

## 1. Exact evidence baseline

| Repository | Exact branch and commit | Authority used here |
|---|---|---|
| `crinkl-protocol-spec` | `origin/main@700be7942efecb5863acb764f004b122f9e3c5fa` | public source wording at the start of this refactor |
| `crinkl-protocol` | `main@bdac6d3f9f32a312544b3adadbb379f98607198f` | adopted reduced-spine schemas and ProcedureProfile V2; historical experiments and escrow-profile evidence |
| `crinkl-platform` | `origin/main@42d28cc06f8456cf293f9eded04c3726e1b706af` | current alpha source behavior |
| `crinkl-proof-validator` | `origin/main@e282562da6a2f1edac5a97d7ae4591023c8453a5` | current validator procedure and certificate evidence |
| `campaign-escrow-program` | `origin/main@8f29e539c2360b16fc2c08de20262ea5c289c324` | candidate escrow execution evidence |

Source, specification, adoption, release, implementation, validator-network
adoption, and production deployment are separate evidence-bearing states.

## 2. Artifact-scoped compatibility boundary

The owner confirmed that the Campaign protocol object family has no production
or deployed consumer. Similar shapes in implementation repositories are
prototypes and experiments, not wire contracts that the public Campaign
specification must preserve.

Compatibility and break risk are evaluated per artifact, not inferred from a
repository or maturity label. Preservation is required when evidence identifies
an external or cross-system wire consumer, persisted state, an immutable
released identity, a deployed runtime dependency, or another relying party.
`IMPLEMENTED` and `PROTOTYPE` labels neither establish nor eliminate that
evidence by themselves.

Accordingly:

- the living Campaign specification has no predecessor aliases, adapters,
  deprecation objects, or inherited family versions;
- each canonical Campaign schema family begins at V1;
- no runtime prototype is declared conformant to these V1 schemas;
- Spend Token formats, verification-policy resolution, issuer-key history,
  attestation status, canonical Spend Stream heads, and the SOFT-to-HARD
  verification pipeline are confirmed compatibility-sensitive surfaces and
  remain unchanged in this slice; this is not an exhaustive inventory of every
  wire- or production-sensitive Crinkl artifact; and
- immutable Git tags and their vendored release payloads remain historical
  evidence only. They are not linked as supported Campaign predecessors.

Prototype source, tests, names, envelopes, or statement identifiers do not by
themselves impose a compatibility layer on the target protocol. A later code
refactor must nevertheless inventory exact producers, consumers, stored
payloads, and deployed dependencies before changing or removing implementation
artifacts.

## 3. Canonical object and procedure inventory

| Item | Kind | Producer / authority | Primary binding | Consumer | Status |
|---|---|---|---|---|---|
| SpendToken | issuer-authenticated user-held commerce fact | Verification Issuer | issuer key, verification policy, status, canonical head | prover and relying verifier | `IMPLEMENTED` |
| CampaignEpochV2 | signed serialized Campaign definition | Campaign authority | rules, policies, economics, windows, proof profiles, registries | prover, validator, runtime, Reward Ledger, settlement | `SPECIFIED_NOT_IMPLEMENTED` |
| ProofOfMatchV1 | standardized ZK statement envelope | holder or authorized prover | exact Epoch, rule, proof profile, Spend/head inputs, issuer/policy dependencies, nullifiers, result | Proof Validators | `SPECIFIED_NOT_IMPLEMENTED` |
| PROOF_OF_MATCH_VERIFICATION | deterministic validator procedure | each selected Proof Validator independently | proof subject hash, procedure profile, public inputs, registries, replay rules | certificate assembler and Campaign runtime | `SPECIFIED_NOT_IMPLEMENTED` |
| ValidatorCertificateV1 | quorum certificate over one exact proof subject | selected Proof Validators | subject, procedure, validator set, quorum policy, signatures | Campaign runtime and Outcome verifier | `SPECIFIED_NOT_IMPLEMENTED` |
| AssignmentRecordV1 | optional portable deterministic assignment result | Campaign runtime | Epoch policy, assignment inputs, seed material, subject scope, arm | delivery, measurement, dispute verifier | `SPECIFIED_NOT_IMPLEMENTED` |
| exposure | application/measurement state | delivery application | assignment and delivery evidence | Outcome builder and measurement | `PLANNED` |
| economic admission | authoritative deterministic runtime or ledger transition | capacity/budget/inventory authority named by the Epoch | accepted conversion, policy, ordering, capacity state, entitlement nullifier | Outcome builder and dispute verifier | `SPECIFIED_NOT_IMPLEMENTED` |
| CampaignOutcomeV1 | signed application composition | Campaign runtime | exact Epoch, accepted proof(s), optional assignment/exposure/admission, nullifiers, reward decision | Reward Ledger and measurement | `SPECIFIED_NOT_IMPLEMENTED` |
| RewardObligationV1 | signed recipient-scoped liability | Reward Ledger | Outcome, Epoch reward terms, recipient, amount, entitlement nullifier, resolution policy | settlement authority and recipient | `SPECIFIED_NOT_IMPLEMENTED` |
| SettlementRecordV1 | signed liability-resolution record | settlement authority | obligation, status, amount, policy, resolution evidence, prior record | reconciliation, recipient, dispute handling | `SPECIFIED_NOT_IMPLEMENTED` |
| CampaignReport | derived application output | measurement application | assignments, exposures, admissions, outcomes, frozen method | sponsor/business reporting | `PLANNED` |

## 4. Collision table and resolution

This table records semantic collisions without preserving discarded draft names
as vocabulary.

| Collision | Failure | Canonical resolution |
|---|---|---|
| separate Campaign-definition object and Epoch object | two objects claim authority over the same immutable rules | `CampaignEpoch` alone owns the committed Campaign state |
| separate audience-proof and conversion-proof mechanisms | purpose was confused with proof type | one `ProofOfMatch` family with `purpose=AUDIENCE` or `purpose=CONVERSION` |
| certificate name used for both quorum acceptance and global state finality | name implied an unstated registry transition | `ValidatorCertificate` means quorum acceptance only; any state transition names its ledger, registry, or chain |
| statement label also selects executable behavior | one identifier can drift or select unrelated procedures | separate `subjectType`, `subjectHash`, stable `procedureId`, version, and content-addressed procedure profile |
| assignment and exposure | selection and delivered treatment were conflated | assignment is deterministic arm selection; exposure is delivery/measurement state |
| proof validity and economic entitlement | a valid proof could create an unfunded liability after capacity exhaustion | optional deterministic economic admission precedes Outcome liability creation |
| liability creation and payment resolution | one artifact could be read as both owed and paid | `RewardObligation` records what is owed; `SettlementRecord` records resolution |
| outcome and catch-all proof package | application composition could absorb unrelated runtime artifacts | `CampaignOutcome` contains only the Campaign facts required by committed policy |
| Campaign admission and proof verification | validator authority over Campaign creation was assumed | Campaign authority signs the Epoch; validators verify its bindings while checking each proof unless a distinct future trust failure justifies another procedure |

## 5. Deletion-test decisions

| Candidate concept | Distinct need found? | Decision |
|---|---|---|
| second generic Campaign-definition object | no distinct consumer or authority boundary | omit; Epoch is authoritative |
| standalone audience proof family | no; it is one purpose of the same relation | omit |
| standalone conversion proof family | no; it is one purpose of the same relation | omit |
| portable AssignmentRecord | conditional | retain only for cross-system use, independent measurement, or dispute evidence |
| universal exposure object | no cross-authority requirement established | application/measurement state |
| universal economic-admission object | no universal cross-system shape established | authoritative runtime/ledger state plus a narrow Outcome projection |
| per-conversion Campaign-authority decision | no legitimate discretion after committed rules hold | omit |
| separate object between Outcome and liability | no additional lifecycle or authority boundary | omit |
| universal Campaign admission certificate | no distinct trust failure demonstrated | omit from the canonical procedure set |

## 6. Boost semantic mapping

| Boost prototype behavior | Canonical role | Cryptographic classification |
|---|---|---|
| promoter activation or qualification proof | closest pre-action `ProofOfMatch(AUDIENCE)` role | genuine Halo2 when native proof bytes and profile are verified |
| buyer claim proof | `ProofOfMatch(CONVERSION)` role | genuine Halo2 when native proof bytes and profile are verified |
| actor-separation fallback signature | supporting evidence | non-ZK signed evidence |
| Campaign, rule, and policy hashes | bindings | non-ZK commitments/hashes |
| settlement-binding artifact | supporting Outcome or settlement evidence | non-ZK unless it embeds separately identified ZK proof bytes |
| Boost match package | mixed supporting envelope | package identity is not itself a ZK proof |
| Platform FIFO queue and selection | economic-admission ordering | application runtime state |
| budget enforcement and slot consumption | economic-admission state transition | application runtime state |
| duplicate-nullifier persistence | replay and entitlement state | registry/ledger state |

The Boost prototype is evidence that Crinkl has real Halo2 Campaign proving
components. It is not evidence that those packages conform to the canonical V1
schemas, and it does not make Boost package names, envelope shapes, statement
identifiers, or mixed procedure semantics canonical predecessors. FIFO, budget,
concurrency, and slot consumption remain outside the ZK primitive while the
Epoch binds their governing policy. Any later removal of Boost implementation
artifacts still requires an exact runtime producer/consumer and persisted-state
inventory.

## 7. Current-versus-target implementation matrix

Status applies to the exact row, not to a similarly named broader system.

| Object or procedure | Status | Evidence boundary |
|---|---|---|
| Spend Token issuance | `IMPLEMENTED` | issuer, policy, key-history, status, portability, and Spend Stream behavior exists and is unchanged |
| SOFT-to-HARD verification pipeline | `IMPLEMENTED` | current attestation status and correction flow; unchanged |
| Boost Halo2 proofs | `PROTOTYPE` | Rust proof service, circuits, routes, and tests exist; canonical V1 conformance is not claimed |
| generalized ProofOfMatchV1 | `SPECIFIED_NOT_IMPLEMENTED` | first canonical envelope in this source candidate |
| generalized Campaign-to-ZK compilation | `PLANNED` | no arbitrary Epoch rule compiler found |
| Campaign-authority signing | `PROTOTYPE` | signed experiments exist; reduced-spine CampaignEpochV2 support is not established |
| current profile-specific Campaign admission procedure | `PROTOTYPE` | validator and Platform producer/consumer code exists; it is not a canonical Campaign protocol predecessor, and later code removal requires an exact runtime and stored-payload inventory |
| Campaign admission | `PLANNED` | not specified because no distinct security purpose is currently demonstrated |
| PROOF_OF_MATCH_VERIFICATION | `SPECIFIED_NOT_IMPLEMENTED` | specification and validator handoff only |
| ValidatorCertificateV1 | `SPECIFIED_NOT_IMPLEMENTED` | first canonical certificate schema |
| canonical nullifier recording | `PLANNED` | prototype stores exist; no adopted cross-system state transition is identified |
| assignment verification | `PROTOTYPE` | deterministic experiment code exists; canonical record support is absent |
| generalized economic admission | `SPECIFIED_NOT_IMPLEMENTED` | policy and Outcome projection specified; authoritative runtime profile remains to implement |
| CampaignOutcomeV1 | `SPECIFIED_NOT_IMPLEMENTED` | first canonical Outcome schema |
| RewardObligationV1 | `SPECIFIED_NOT_IMPLEMENTED` | first canonical liability schema |
| dispute lifecycle | `PLANNED` | policy reference exists; complete lifecycle is not implemented |
| SettlementRecordV1 | `SPECIFIED_NOT_IMPLEMENTED` | first canonical resolution schema |
| escrow | `PROTOTYPE` | candidate program and tests exist; canonical Campaign object support is not established |
| Spend-layer multi-issuer support | `IMPLEMENTED` | issuer registry and verification-policy model supports multiple issuers |
| multi-issuer ProofOfMatch | `SPECIFIED_NOT_IMPLEMENTED` | target relation requirements exist; generalized prover/verifier is absent |
| distributed authority for existing non-Campaign validator procedures | `IMPLEMENTED` | current validator selection, quorum, and certificate machinery exists for its exact implemented procedures |
| distributed authority for PROOF_OF_MATCH_VERIFICATION | `SPECIFIED_NOT_IMPLEMENTED` | no implementation change in this slice |

## 8. Schema and release decision

1. `CampaignEpochV2`, `ProofOfMatchV1`, `ValidatorCertificateV1`,
   `AssignmentRecordV1`, `CampaignOutcomeV1`, `RewardObligationV1`, and
   `SettlementRecordV1` form the reduced-spine Campaign schema set.
   `CampaignEpochV2` uses the schema ID
   `crinkl://protocol/schemas/campaigns/campaign_epoch_v2`. Its successor
   identity preserves adopted `CampaignEpochV1`, whose required fields,
   signed bytes, and released profile bindings remain distinct and immutable.
2. The adopted engineering objects remain outside `versions/release.json` and
   every released public manifest.
3. Engineering adoption supplies exact conformance vectors and a
   content-addressed procedure profile. A future public release still requires
   its own review, identifier inventory, maturity, and release evidence;
   runtime acceptance remains separately governed.
4. No compatibility claim may be inferred from a similar object or field name
   in an implementation repository.
5. Existing release tags are not rewritten. Their contents remain accessible
   as historical publication evidence and have no inbound link from the living
   Campaign specification.
6. Release-pinned, non-Campaign documents and vendored conformance payloads are
   validated at their immutable release identity. They do not supply Campaign
   aliases or canonical object definitions.

## 9. Validation receipt

Validation ran in
`/mnt/worktrees/crinkl-protocol-spec-campaign-protocol-reduced-spine-spec-20260812`
against public-spec base
`700be7942efecb5863acb764f004b122f9e3c5fa`.

| Command or check | Result |
|---|---|
| `python3 scripts/check_repository_layout.py` | PASS; living links valid; immutable release payloads and the rc.8-pinned settlement document are checked at their release identity rather than used as living Campaign inputs |
| `git diff --check` | PASS |
| Draft 2020-12 `check_schema` over `schemas/experimental/campaigns/*.schema.json` | PASS; seven schemas |
| repository-wide `$id` collision check for the seven Campaign schemas | PASS; seven unique IDs; reduced-spine Epoch uses the successor `.../campaigns/campaign_epoch_v2` ID |
| positive instance validation for all seven Campaign schemas | PASS |
| negative conditional vectors for Epoch audience/profile and succession; Proof entitlement pair, producer authority, and input mode; Outcome admission shape and rejected-admission reward; paid Settlement Record transaction binding | PASS; eight rejected |
| `node scripts/verify_conformance.mjs` | PASS; 99 checks, 16 executable kinds, 3 data-only kinds |
| `python3 scripts/check_drift.py` | PASS; rc.8 remains an unreviewed, unpublished source candidate and rc.7 remains immutable |
| `python3 scripts/check_release_registry.py --adopted-repo /home/azureuser/crinkl-protocol` | PASS |
| `python3 scripts/check_living_version_claims.py` and its hostile-regression test | PASS |
| protocol/business/onchain boundary check | PASS |
| protected Spend Token and SOFT-to-HARD path diff | PASS; no changes to the token schema/spec, ingestion, SOFT verification, HARD verification, verification state, or correction/revocation documents |
| canonical Campaign stale-vocabulary scan | PASS; no occurrence of the discarded Campaign names, conversion-evidence adapter, or inherited Epoch V2 name |
| `python3 scripts/check_version_identifier_inventory.py --adopted-repo /home/azureuser/crinkl-protocol` | FAILS on the pre-existing unclassified `campaign.directBuyerReward.releaseReconciliationV1.json` path |

The identifier-inventory failure predates and is outside this slice: the exact
failing path exists at the public baseline, and neither the checker nor that
vendored release payload is modified here. The canonical Campaign schemas use
the inventory's existing `schemas/experimental/` classification.
