---
status: draft
layer: governance
version: v1
normative: false
---

# Campaign architecture inventory and migration

This document records the evidence used to reduce the Campaign vocabulary. The
normative target is
[`../protocol/applications/campaigns/README.md`](../protocol/applications/campaigns/README.md).

## 1. Evidence baseline

| Repository | Exact branch and commit | Authority used here |
|---|---|---|
| `crinkl-protocol-spec` | `origin/main@700be7942efecb5863acb764f004b122f9e3c5fa` | current public wording and released public schemas |
| `crinkl-protocol` | `origin/main@47df2a1f6bdb7aa53d70060401cd0297e2547362` | adopted engineering schemas and candidate escrow profile |
| `crinkl-platform` | `origin/main@42d28cc06f8456cf293f9eded04c3726e1b706af` | exact current alpha source behavior |
| `crinkl-proof-validator` | `origin/main@e282562da6a2f1edac5a97d7ae4591023c8453a5` | exact current validator procedures and certificates |
| `campaign-escrow-program` | `origin/main@8f29e539c2360b16fc2c08de20262ea5c289c324` | candidate escrow execution behavior |

Source, adoption, public publication, release, runtime, validator-network
adoption, and production deployment are separate states. Implementation source
can demonstrate a prototype or expose drift; it does not silently redefine the
public protocol.

## 2. Current object and procedure inventory

| Current item | Kind | Producer / authority | Binding and consumer | Evidence |
|---|---|---|---|---|
| Spend Attestation Token V1/V2 | serialized signed object | Verification Issuer | token hash, issuer signature, policy/key/status/head resolution; holder and downstream verifier | public portability schemas and conformance; unchanged by this slice |
| public experimental `CampaignEpochV1` | serialized draft object | legacy issuer/Campaign authority | ID `crinkl://protocol/schemas/experimental/campaign-epoch.v1`, SHA-256 `d7d87f28acaf9a4f9e13974c0faf9c19b55bcadc4e1ca32ea59b22fd08495d87`; `ruleSetHash` and historical Campaign composition | `schemas/experimental/campaign-epoch.v1.schema.json` |
| released signed `CampaignEpochV1` | serialized signed object | Epoch authority | ID `crinkl://protocol/schemas/campaign_epoch_v1`, SHA-256 `019628fcb7d2b218cf0104cffa393d41f418047598e6b2e35afb0d239f46e033`; exact content references and signature | `conformance/profiles/campaign-direct-buyer-reward-v1/protocol/schemas/campaign_epoch_v1.schema.json` |
| `CampaignRuleV1` / generic Campaign commitment | prose shape | Campaign author | overlaps Epoch rules/economics; no independent canonical schema | legacy `protocol/applications/conditions/campaign-commitment.md` before this refactor |
| `ProofOfMatch` | prose role and multiple implementation-specific packages | holder/prover or package producer | no prior canonical public envelope/hash procedure | prior `protocol/applications/conditions/proof-of-match.md`; validator package types below |
| `CAMPAIGN_DIRECT_BUYER_REWARD_ADMISSION_V1` | validator `statementType` and profile-specific procedure | Campaign admission package producer and selected validators | release identity, Epoch, reward policy, cutoff, registry assignment, nullifier, strict-BFT finality | `crinkl-proof-validator@e282562:packages/campaign/src/admission.ts:30-59,193-261,264-334,337-387` |
| `BOOST_MATCH_BUNDLE_V0` | validator legacy statement/package | Platform/proof-service package producer and validators | Boost-specific artifacts, public inputs, hashes, nullifier, and verifier logic | `crinkl-proof-validator@e282562:packages/proof-package/src/index.ts:22-29`; Boost verifier sources |
| `QUALIFIED_GMV_BURN_EPOCH_V1/V2` | validator GMV procedures | GMV pipeline and validators | distinct GMV aggregation/finality behavior | `crinkl-proof-validator@e282562:packages/proof-package/src/index.ts:22-29` |
| `ProofFinalizationCertificateV1` | validator implementation certificate | selected validator quorum | exact fields bind `proofId`, proof-package hash, `statementType`, result hash, policy, registry snapshot, validator assignment, public artifact, quorum, signatures, and finalization time; it has no generic `subjectType` or content-addressed procedure profile | `crinkl-proof-validator@e282562:packages/finality/src/index.ts:71-86,188-230,292-311` |
| `ValidatorFinalityCertificateV1` | adopted schema with authority unavailable | no active authority | ID `crinkl://schemas/validator_finality_certificate_v1.schema.json`, SHA-256 `9ff413f3ff33111681a4f8b94a093f098d96f5e82c953f73d32f1cd169521d4e`; explicitly `authorityState=UNAVAILABLE`, `grantsFinalityAuthority=false` and carries no validator signatures or quorum policy | `crinkl-protocol@47df2a1:protocol/applications/schemas/validator_finality_certificate_v1.schema.json:1-102` |
| `CampaignExperimentPolicyV1` and rollout proof | adopted policy plus proof interface | experiment authority / holder | deterministic assignment inputs; portable assignment object previously absent | `protocol/extensions/campaign-experiment-profile.md` |
| `CampaignConversionEvidenceV1` | adopted candidate serialized signed object | Campaign conversion-evidence authority / Platform adapter | Epoch/rules/parameters/funding/settlement/escrow, accepted Spend Token/head/policies, liability nullifier | `crinkl-protocol@47df2a1:protocol/applications/schemas/campaign_conversion_evidence_v1.schema.json:1-160` |
| `CampaignLiabilityBatchV1` | adopted candidate batch/root | liability authority | conversion evidence root, liability leaves, aggregates, nullifiers | `crinkl-protocol@47df2a1:protocol/applications/schemas/campaign_liability_batch_v1.schema.json:1-169` |
| `CampaignConversionResolutionEvidenceV1` | adopted candidate resolution evidence | conversion-evidence authority | current heads and settle/cancel decision for one liability batch | adopted escrow profile and schema |
| `CampaignEscrowReceiptV1` | adopted candidate Solana action receipt | escrow receipt authority | reserve/settle/cancel/refund/close action and chain/accounting evidence | `crinkl-protocol@47df2a1:protocol/applications/schemas/campaign_escrow_receipt_v1.schema.json:1-246` |
| `RewardCommitmentV1` | adopted serialized signed obligation | authorized Applications authority | Epoch, reward policy, ProofOfMatch, recipient, reward, funding lineage | `crinkl-protocol@47df2a1:protocol/applications/schemas/reward_commitment_v1.schema.json:1-78` |
| `RewardCommitmentTokenV1` | portable reward-batch inclusion token | Reward Ledger/token issuer | batch inclusion; not escrow settlement | adopted portability docs and public reward-commitment page |

## 3. Collision table

| Collision | Classification | Resolution |
|---|---|---|
| `CampaignCommitment` and `CampaignEpoch` both describe committed Campaign state | same mechanism, two terms | canonical `CampaignEpoch`; retain the old name only for exact historical roots/accounts |
| two incompatible objects titled `CampaignEpochV1` | same title, different IDs, bytes, and meaning | preserve both exact digests above; resolve by exact ID + digest; add `CampaignEpochV2` as a new successor |
| `CampaignRuleV1` and Epoch rule/economic references | overlapping composition | fold canonical meaning into Epoch references; keep legacy descriptions non-normative |
| Eligibility Proof, Audience Qualification, Conversion Proof, Verified Conversion | multiple names for one mechanism or its business result | `ProofOfMatch` with `purpose=AUDIENCE|CONVERSION`; ordinary terms remain roles/results |
| `FinalityCertificate`, `ProofFinalizationCertificateV1`, `ValidatorFinalityCertificateV1` | one generic name and multiple incompatible schemas/guarantees | target `ValidatorCertificate`; legacy names remain exact-schema terms only |
| “finality” used for quorum acceptance, immutable state, replay registry, and economic approval | one term carrying multiple meanings | certificate means quorum acceptance only; every state transition names its registry/ledger/chain |
| `statementType` selects both subject label and executable procedure | name implies one dimension while controlling several | target separates `subjectType`, `subjectHash`, `procedureId`, version, and content-addressed procedure profile |
| `CampaignConversionEvidenceV1` treated as complete outcome | object name understates/overstates depending on consumer | supporting conversion-to-escrow evidence; map into part of `CampaignOutcome`, never silently rename |
| `CampaignQualifiedConversion` | proposed extra object with no repository consumer found | eliminate from canonical vocabulary pending deletion-test evidence |
| `ConversionApproval` | state name implies post-conversion discretion | deprecate; Outcome composes accepted proof plus required economic admission deterministically |
| `RewardCommitment` used for liability, portable inclusion, and cryptographic commitment language | one term carries multiple meanings and stronger cryptographic implication | canonical liability is `RewardObligation`; preserve exact legacy object/token names |
| `CampaignSettlementCommitment`, `CampaignEscrowReceipt`, and “SettlementReceipt” | roots, action receipts, and liability resolution conflated | canonical liability resolution is `SettlementRecord`; other artifacts are supporting/profile-specific evidence |
| assignment and exposure | distinct facts treated as synonyms | assignment selects an arm; exposure records delivered intervention |
| proof validity and economic entitlement | unrelated decisions collapsed | optional deterministic economic admission occurs between accepted conversion proof and Outcome |

## 4. Legacy-to-canonical mapping

| Legacy or current item | Target meaning | Compatibility action |
|---|---|---|
| public experimental `CampaignEpochV1` | historical draft Epoch | preserve bytes and mark deprecated |
| released signed `CampaignEpochV1` | strict V1 predecessor | preserve bytes; `CampaignEpochV2` is additive and not automatically accepted |
| generic `CampaignCommitment` / `CampaignRuleV1` | Epoch-contained rule/economic references | redirect prose; do not create a second object |
| audience qualification / eligibility proof | `ProofOfMatch(AUDIENCE)` | purpose alias only |
| verified conversion / conversion proof | `ProofOfMatch(CONVERSION)` | purpose alias only |
| Boost promoter activation/qualification proof | closest pre-action `ProofOfMatch(AUDIENCE)` role | semantic mapping, not schema conformance |
| Boost buyer claim proof | `ProofOfMatch(CONVERSION)` role | semantic mapping, not schema conformance |
| Boost match bundle / settlement-binding artifact | legacy envelope or supporting Outcome evidence | retain exact artifact identity |
| `CampaignConversionEvidenceV1` | supporting conversion evidence and possible direct-Outcome adapter input | preserve V1; target Outcome references it through `legacyEvidenceRefs` |
| `CampaignQualifiedConversion` | none | deprecated/absent unless deletion test later passes |
| `ConversionApproval` | accepted match plus required admission composed in Outcome | deprecated as discretionary decision |
| `RewardCommitmentV1` | legacy Applications obligation lacking canonical Outcome and entitlement-nullifier bindings | preserve; migrate with a versioned adapter to `RewardObligationV1` only when exact bindings are available |
| `RewardCommitmentTokenV1` | portable reward issuance/batch evidence | preserve; not an Obligation or Settlement Record |
| `CampaignSettlementCommitment` | legacy batch/root publication | supporting settlement evidence only |
| `CampaignEscrowReceiptV1` | profile-specific escrow action evidence | may support or satisfy a profile mapping to `SettlementRecord`; no rename |
| `FinalityCertificate` | exact legacy certificate family | target ProofOfMatch certificate is `ValidatorCertificateV1` |

## 5. CampaignConversionEvidenceV1 mapping

The existing object adequately binds these direct-conversion/escrow inputs:

- `campaignEpochRef`, `campaignRuleSetRef`, and `campaignParametersRef`;
- funding, settlement, and escrow references;
- accepted Spend Token, envelope, canonical head, issuer/head snapshots,
  inclusion proof, accepted-status and correction policies;
- commerce-source and issuer-generation profiles; and
- `liabilityNullifier` plus conversion-evidence authority signature.

It does **not** bind:

- an accepted `ProofOfMatch(AUDIENCE)` and Validator Certificate;
- experimental assignment or exposure;
- an accepted `ProofOfMatch(CONVERSION)` and Validator Certificate;
- whether economic admission was required or succeeded;
- the authoritative capacity state and ordering position;
- the final measurement contribution decision;
- the exact reward amount/asset and recipient binding selected by committed
  policy; and
- a canonical `RewardObligation` reference.

This is visible in the exact runtime type at
`crinkl-platform@42d28cc:packages/protocol/src/campaignEscrowConversion.ts:174-209`
and the Platform assembler at
`services/attestation-gateway/src/domain/campaignConversionEvidenceAssembler.ts:52-125`:
the object carries the Epoch/rule/economic references, accepted Spend token/head
and liability nullifier, but no audience proof/certificate, experimental
assignment/exposure, conversion ProofOfMatch/certificate, or capacity-admission
reference. `liabilityNullifier` supplies a legacy economic replay binding; it
does not by itself bind a target entitlement-nullifier registry transition or
the exact payout projection.

Therefore V1 remains useful and implemented at alpha source level, but cannot be
declared equivalent to `CampaignOutcomeV1`. For a direct uncapped Campaign, an
adapter can construct the missing proof/certificate and Outcome fields from
separately verified evidence. For qualified, experimental, or capacity-limited
Campaigns, the missing bindings are material and must be supplied explicitly.

## 6. Campaign admission decision

Current validator source implements
`CAMPAIGN_DIRECT_BUYER_REWARD_ADMISSION_V1`. It verifies an exact public release,
Epoch, direct-reward policy, cutoff, registry assignment, policy, and
Campaign-admission nullifier, then applies the generic strict-BFT finality path.
Platform source consumes this profile in Business Campaign admission routes and
transport (`crinkl-platform@42d28cc:services/attestation-gateway/src/domain/businessCampaignAdmission.ts:202-339`).

That is a real alpha procedure, so it must not be deleted or repurposed in this
specification slice. However, the repository evidence does not establish that
*every* Campaign needs quorum approval in addition to its authority signature.
The verified material can be resolved again while checking each ProofOfMatch.

The distinct potential trust purpose is shared, pre-use non-equivocation or a
cross-runtime activation gate for one exact Campaign release/profile. The
target therefore:

1. does not define a generic `CAMPAIGN_EPOCH_ADMISSION` procedure;
2. preserves the existing profile-specific alpha identifier and behavior;
3. classifies it as `PROTOTYPE`, not equivalent to ProofOfMatch verification;
4. asks the validator refactor to retain it only if a named consumer relies on
   quorum-created activation/non-equivocation state; and
5. otherwise recommends narrowing it to deterministic Campaign material
   verification or removing the quorum layer after an explicit compatibility
   migration.

This is the smallest unresolved design decision. No current alpha code changes
are made here.

### Escrow-source contradiction preserved

The escrow repository README says “Proof Validators admit the Campaign
definition once” (`campaign-escrow-program@8f29e53:README.md:61-66`). That is a
candidate architecture assertion, but it is not evidence that the current
program consumes a generic validator certificate. The same exact README says
the candidate is not deployed, has no connected Platform runtime or custody
signer, and treats protocol hashes as account-constraint inputs rather than
running the artifact verifier (`README.md:121-141`). Its conformance test also
requires superseded universal-finality fields, including
`validatorFinalityCertificateRef`, to be absent
(`programs/campaign-escrow/tests/protocol_vectors.rs:519-535`), and its authority
test expressly rejects validator payment permission
(`programs/campaign-escrow/tests/instructions.rs:507-529`).

This specification therefore does not let that incomplete escrow README create
a generic Campaign consensus layer. If a future escrow initializer must consume
quorum-created Campaign activation state, the next design must name that exact
subject, state transition, certificate/profile, and failure it prevents. Until
then, the Campaign authority signature and proof-time Epoch verification are
the target authority model, while the existing alpha admission profile remains
untouched for compatibility.

## 7. Economic admission and Boost mapping

| Boost/current behavior | Target classification | ZK? |
|---|---|---|
| promoter activation/qualification proof | closest `ProofOfMatch(AUDIENCE)` role | genuine Halo2 where native proof bytes/profile are verified |
| buyer claim proof | `ProofOfMatch(CONVERSION)` role | genuine Halo2 where native proof bytes/profile are verified |
| actor-separation hash/fallback signature | supporting evidence | no |
| campaign/rule/policy hashes | commitments/bindings | no |
| settlement-binding artifact | supporting Outcome/settlement evidence | no unless it embeds separately identified ZK proof bytes |
| `BOOST_MATCH_BUNDLE_V0` | legacy package/envelope | mixed; package identity alone is not ZK |
| Platform FIFO queue and selection | economic-admission ordering | no |
| budget enforcement and slot consumption | authoritative economic-admission state transition | no |
| duplicate-nullifier persistence | replay/entitlement state | no |

The prototype proves that Crinkl has real Halo2 Campaign proving components. It
does not prove conformance to the new envelopes. The target keeps FIFO, queue,
budget, concurrency, and slot consumption out of the ZK primitive while
requiring the Epoch to bind their policy and the Outcome to reference auditable
admission evidence.

## 8. Current-versus-target implementation matrix

The status applies to the exact row, not to a similarly named broader system.

| Object or procedure | Status | Evidence boundary |
|---|---|---|
| Spend Token issuance | `IMPLEMENTED` | existing issuer, portability, policy, key-history, status, and Spend Stream code/conformance; unchanged here |
| Boost Halo2 proofs | `PROTOTYPE` | Rust proof service and `H2_PROMO_*` routes/tests exist; target schema conformance is not claimed |
| generalized `ProofOfMatchV1` | `SPECIFIED_NOT_IMPLEMENTED` | first canonical envelope added here |
| generalized Campaign-to-ZK compilation | `PLANNED` | Boost-specific construction exists; no compiler for arbitrary Epoch rule/profile references found |
| Campaign-authority signing | `PROTOTYPE` | signed Epoch/profile artifacts and alpha adapters exist; production deployment is not inferred |
| `CAMPAIGN_DIRECT_BUYER_REWARD_ADMISSION_V1` | `PROTOTYPE` | profile-specific validator and Platform source/tests; generic necessity unresolved |
| generalized Campaign admission | `PLANNED` | deliberately not specified pending distinct trust failure and consumer |
| legacy Boost validator verification | `PROTOTYPE` | `BOOST_MATCH_BUNDLE_V0` executable package procedure |
| `PROOF_OF_MATCH_VERIFICATION` | `SPECIFIED_NOT_IMPLEMENTED` | target handoff only |
| `ValidatorCertificateV1` | `SPECIFIED_NOT_IMPLEMENTED` | target schema; legacy certificates are not equivalent |
| canonical proof/purchase/entitlement nullifier recording | `PLANNED` | scoped stores exist in prototypes, but no one target cross-system registry transition is adopted |
| deterministic assignment verification | `PROTOTYPE` | existing experiment/rollout proof interface; portable target record is not implemented |
| `AssignmentRecordV1` | `SPECIFIED_NOT_IMPLEMENTED` | used only when deletion test passes |
| Boost FIFO/budget/slot economic admission | `PROTOTYPE` | application runtime behavior; not generalized protocol admission |
| generalized economic admission | `SPECIFIED_NOT_IMPLEMENTED` | Epoch policy + Outcome projection defined; authoritative runtime/ledger profile remains to implement |
| `CampaignConversionEvidenceV1` | `PROTOTYPE` | adopted candidate plus Platform assembly, signing, verification, persistence, and alpha tests |
| `CampaignOutcomeV1` | `SPECIFIED_NOT_IMPLEMENTED` | first canonical target schema |
| adopted `RewardCommitmentV1` | `IMPLEMENTED` | adopted schema and Platform/Reward Ledger source exist for legacy meaning; no target-equivalence claim |
| `RewardObligationV1` | `SPECIFIED_NOT_IMPLEMENTED` | canonical target liability family |
| dispute lifecycle | `PLANNED` | policy references exist; no complete generalized target lifecycle found |
| `SettlementRecordV1` | `SPECIFIED_NOT_IMPLEMENTED` | canonical target resolution family |
| Campaign escrow profile/program | `PROTOTYPE` | adopted candidate profile, program source, and tests; profile explicitly says runtime unavailable |
| Spend-layer multi-issuer support | `IMPLEMENTED` | issuer registry/policy model supports multiple issuers |
| multi-issuer `ProofOfMatch` | `SPECIFIED_NOT_IMPLEMENTED` | target relation requirements defined; generalized prover/verifier absent |
| distributed validator authority for current alpha procedures | `IMPLEMENTED` | current devnet validator/finality machinery exists for exact legacy procedures |
| distributed authority for target `PROOF_OF_MATCH_VERIFICATION` | `SPECIFIED_NOT_IMPLEMENTED` | handoff only; no implementation mutation in this slice |

## 9. Schema and version migration plan

1. Preserve both published `CampaignEpochV1` byte sets and their exact IDs.
2. Publish `CampaignEpochV2` only after adopted engineering parity, vectors,
   independent review, release identity, and explicit runtime acceptance.
3. Treat the six new V1 object families as new identities, not retroactive
   serializations of old prose or packages.
4. Keep `ValidatorCertificateV1` restricted to
   `PROOF_OF_MATCH_VERIFICATION`. A later Campaign procedure must establish its
   own stable identifier and profile without changing this V1 meaning.
5. Preserve `RewardCommitmentV1` and `RewardCommitmentTokenV1`; introduce
   `RewardObligationV1` as the canonical successor term only through explicit
   adapters and consumer migrations.
6. Preserve `CampaignConversionEvidenceV1`, liability batches, resolution
   evidence, and escrow receipts. Outcome and Settlement adapters must verify
   every additional binding; they cannot infer missing fields.
7. Do not add these schemas to `versions/release.json`, a released manifest, or
   a tag in this source-only refactor.
8. Keep `versions/CHANGELOG.md` byte-identical in this slice because the current
   unpublished rc.8 finalization plan pins it as a controlling artifact. The
   next release composition must add this source candidate to its changelog and
   identifier inventory only when review/adoption state is known.

## 10. Intentionally retained legacy vocabulary

- `CampaignCommitment` in exact historical Solana account/root names;
- both `CampaignEpochV1` schemas, identified by exact path/ID/digest;
- `FinalityCertificate`, `ProofFinalizationCertificateV1`, and
  `ValidatorFinalityCertificateV1` only for their exact legacy artifacts;
- `RewardCommitmentV1` and `RewardCommitmentTokenV1` only for their exact
  adopted/portable families;
- `CampaignSettlementCommitment` and `CampaignEscrowReceiptV1` only for exact
  legacy settlement/root/action evidence;
- `ConversionApproval` only in explicitly marked historical text; and
- existing validator `statementType` strings until the subsequent validator
  refactor supplies versioned compatibility adapters.

## 11. Validation receipt

Validation was run in
`/mnt/worktrees/crinkl-protocol-spec-campaign-protocol-reduced-spine-spec-20260812`
against public-spec base
`700be7942efecb5863acb764f004b122f9e3c5fa`.

| Command or check | Result |
|---|---|
| `python3 scripts/check_repository_layout.py` | PASS; repository layout and local Markdown links OK |
| `git diff --check` | PASS |
| Draft 2020-12 `check_schema` over `schemas/experimental/campaigns/*.schema.json` | PASS; seven unique schemas |
| positive instance validation for all seven new schemas | PASS |
| negative conditional vectors: Epoch audience/profile and succession mismatches; ProofOfMatch entitlement-pair, producer-authority, and input-mode mismatches; Outcome admission-shape and rejected-admission/reward mismatches; paid Settlement Record without transaction | PASS; eight rejected |
| `node scripts/verify_conformance.mjs` | PASS; 99 checks, 16 executable kinds, 3 data-only kinds |
| `python3 scripts/check_drift.py` | PASS; release `1.0.0-rc.8/RELEASE_CANDIDATE_NOT_PUBLISHED`, manifest and leak guard clean |
| `python3 scripts/check_release_registry.py --adopted-repo /home/azureuser/crinkl-protocol` | PASS; schema, registry, public/adopted Git evidence, and profile consistency |
| `python3 scripts/check_living_version_claims.py` | PASS |
| direct buyer-reward vector checker | PASS |
| Spend Token V2 holder-binding vector checker | PASS; one positive and seven negative cases |
| `python3 scripts/check_version_identifier_inventory.py --adopted-repo /home/azureuser/crinkl-protocol` | FAILS on a pre-existing tracked `campaign.directBuyerReward.releaseReconciliationV1.json` path that the inventory rules do not classify |
| legacy direct-profile release checker | NOT APPLICABLE to the current rc.8 candidate; it assumes repository release identity rc.3 and fails its maturity comparison |
| legacy successor-finalization checker | NOT APPLICABLE to the current rc.8 candidate; it expects an older fixed control set |

The identifier-inventory failure predates this slice: the failing conformance
file exists at the exact public baseline, while the checker, inventory, failing
file, release manifest, and rc.8 finalization plan are unchanged here. New
schemas were placed beneath the inventory's already recognized
`schemas/experimental/` prefix. No gate failure was hidden or converted into a
passing claim.

## 12. Stale-vocabulary scan

The required repository scan found no unmarked target use of deprecated
Campaign vocabulary:

- `FinalityCertificate` / “Finality Certificate” remains in exact legacy core
  admission prose, changelog history, old schema-vector checks, and explicit
  migration warnings;
- `RewardCommitment` / “Reward Commitment” remains extensively because the
  adopted object and portable token families are still real compatibility
  artifacts, including whitepaper and portability documentation;
- `SettlementReceipt` remains only in deprecation/migration mappings;
- `CampaignCommitment` remains in the exact Solana account name and explicit
  deprecation/migration text;
- `CampaignQualifiedConversion` remains only in deletion-test/deprecation
  mappings; and
- `ConversionApproval` remains only in deprecation text and the exact legacy
  `approvalHash` compatibility explanation.

Searches for claims that Proof Validators generically admit Campaigns or
authorize settlement/payment found none. The legacy profile-specific
`CAMPAIGN_DIRECT_BUYER_REWARD_ADMISSION_V1` identifier remains documented as
`PROTOTYPE` pending its distinct-consumer/security decision.
