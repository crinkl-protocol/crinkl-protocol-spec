---
status: draft
layer: applications
version: vnext
normative: true
implementationStatus: PARTIAL_NON_PRODUCTION_ENGINEERING
---

# Campaign Solana proof-verification profile (Procedure Profile V3)

Mirrored from `crinkl-protocol@156d63c37d4d4b9a31287e86d7623afdbe642997`,
`protocol/applications/campaigns/CAMPAIGN_SOLANA_PROOF_VERIFICATION_PROFILE.md`;
the internal page is authority. This is the current Campaign proof-acceptance
path. Validator quorum certification (`ValidatorCertificateV1`, Procedure
Profiles V1 and V2) is retained as a historical acceptance candidate in the
[`Campaign architecture`](./README.md) appendix and is not used by this path.

Maturity: non-production engineering. Two engineering families have reached
finalized Solana Devnet `ACCEPT` with replay rejection and one isolated
exactly-once Platform Outcome each. No runtime, production deployment, key
ceremony or economic authority is established.
## 1. Purpose and bounded change

This profile changes only the proof-acceptance edge of the adopted Campaign
reduced spine:

```text
Existing spine:
ProofOfMatchV1
-> ValidatorCertificateV1
-> CampaignOutcomeV1

Adopted internal successor:
ProofOfMatchV1
-> SolanaProofEvidenceV1
-> CampaignOutcomeV2
```

`CampaignEpochV2` and `ProofOfMatchV1` remain unchanged. Validator assignment,
validator-set resolution, quorum policy, validator votes and
`ValidatorCertificateV1` are not used by the successor path. Existing validator
profiles, certificates and Outcomes remain valid only under their exact prior
profiles and are not reinterpreted.

The generic procedure does not adopt buyer-state tree bytes, a buyer-key
derivation, a root publisher, a completeness policy, a Solana deployment or a
runtime. The separately adopted, runtime-unavailable
`CAMPAIGN_SINGLE_PRODUCT_PURCHASE_GROTH16_PROFILE.md` (internal, not yet published)
defines the first exact positive purchase circuit/key lineage and source
mapping under this procedure. It remains runtime-unavailable and grants no
buyer-history or deployment claim.

## 2. Successor identities and compatibility

The procedure is identified by:

```text
procedureId: PROOF_OF_MATCH_VERIFICATION
procedureVersion: 3
procedureProfileRef:
  sha256:73306e3b904dd05fda008da1ca6c2858d545f3dd9503366836d6833da7aee3ec
```

The complete machine profile is
[`campaign_proof_of_match_procedure_profile_v3.json`](../artifacts/campaign_proof_of_match_procedure_profile_v3.json).
It supports `ProofOfMatchV1`, `CampaignEpochV2`, `AUDIENCE` and `CONVERSION`
purposes, and only registered `GROTH16_BN254` proof profiles.

Procedure Profile V3 is the adopted successor because Procedure Profiles V1
and V2 already exist. `CampaignOutcomeV2` is the next Outcome version because
only `CampaignOutcomeV1` preceded it. This is the first canonical
`SolanaProofEvidence`, so its version is V1.

Earlier unmerged alpha branches reused the evidence V1/V2 and Outcome V2 labels
for a single-product eight-input relation. Their Outcome candidate has digest
`28ee4dfd3e1175edabf1cc466553f7b568f8b64938b06715c38faedced402350`
at `9bc0c88` and
`a031c5e604a71901230a7428046a90a393777032524744bc751fca16fbeee48b`
at `a396384`;
their evidence V2 candidate has digest
`33d63b07cfa752c25aa8f2982f84f2d401d5831f3fc862b0246aa6ae3017d659`
at `eeb1690` and
`6d2af8c4c0417125a90c370358f887f834acf0972d17bb34b58038e075bb47c0`
at `a396384`.
The later Outcome also narrows recipient binding. Those commit-pinned artifacts
remain branch-local alpha evidence only. They do not reserve canonical schema
versions and no canonical protocol reference resolves to either alpha byte
sequence.

### 2.1 Sealed alpha adoption baseline

The sealed isolated-alpha run recorded by
`crinkl-platform/docs/operations/solana-groth16-v2-alpha-e2e-postmortem-and-next-circuit-runbook.md`
is the executable integration baseline for this successor. Its exact audited
source pins are `crinkl-protocol@a396384623f3fec534596f45ff62c5eda6961f6f`
and `crinkl-platform@2afa1c5287316fd4bcbad04e84dbcc0a42272969`.
It demonstrated the complete direct-Solana chain from authenticated product and
status sources through a Groth16 proof, frozen Devnet program and VK, finalized
ACCEPT, Platform atomic consumption, reward and alpha settlement, replay and
hostile zero-effect, and sealed evidence.

That result is implementation evidence, not permission to copy every alpha
identity or make its instance parameters universal:

| Sealed alpha surface | Canonical successor treatment |
|---|---|
| `SINGLE_PRODUCT_PURCHASE_MATCH_GROTH16_BN254_V2` and its eight ordered inputs | First executed Groth16 conversion lineage and reference implementation. The exact count, names and order belong to its future reviewed proof profile; they are not Procedure Profile V3 defaults. |
| Alpha `SolanaGroth16ProofVerificationEvidenceV2` | Map the authenticated fields into `SolanaProofEvidenceV1`. Preserve the finalized transaction, program, ProgramData, VK, instruction, proof, ordered-input, record and replay bindings; do not preserve the branch-local schema identity. |
| Alpha `CampaignOutcomeV2` | Do not copy its recipient-mode narrowing. The adopted internal `CampaignOutcomeV2` preserves V1 conversion and economic semantics, substitutes `solanaProofEvidenceRef`, and admits a separately authorized non-economic audience-only branch. A selected proof profile may require recipient-commitment mode without narrowing the shared Outcome schema. |
| Product/status snapshots, purchase attestation, BN254 projection, dependencies, closed rule and Campaign authority view | The exact V1 source schema bytes are preserved, and V2 dependencies plus a Condition-derived evaluated rule replace the alpha's missing Condition/context bindings. The canonical source and proof profiles remain runtime-unavailable pending review; the alpha closed-rule and authority-view identities are not adopted. |
| Entitlement transition, Reward Obligation and Settlement successors used by the alpha | Required field-dependency audit only. Proof acceptance does not grant any of those authorities, and no alpha economic value becomes a protocol default. |
| Frozen program, VK account, ACCEPT record and sealed Devnet receipts | Conformance and reproducibility evidence for the exact alpha identity. They do not establish a reusable production deployment or make future circuit/VK/program identities equivalent. |

The adoption task is therefore to promote the reusable source, relation,
mapping and authority contracts needed by that successful lineage, while
retaining the run's business values, eight-input ABI, proving setup, Devnet
addresses and economic result as profile- or instance-specific evidence.

## 3. Proof-profile ownership

The selected proof profile owns the cryptographic relation. It must define:

- the exact circuit and circuit-artifact identity;
- the exact verifying-key reference and bytes hash;
- the exact ordered public inputs and their semantic mappings;
- the BN254 field encoding and rejection rules;
- the private witness categories and derivations;
- the Condition, Campaign Epoch, purpose, rule, cutoff, root, Spend-head,
  result, recipient and nullifier commitments required by that relation; and
- whether the relation is available for use.

The procedure profile does not redefine those facts. It requires an accepted
proof profile to be selected by the exact purpose-specific proof-profile
reference in `CampaignEpochV2`, and it verifies the final Solana observation
against that resolved profile.

When an exact statement and proof profile are admitted, business labels,
brands, products, categories, thresholds and relative windows are data
committed through the Campaign rule and proof profile. They do not become
procedure IDs, circuit families or verifying-key identities merely by being
used in a Campaign.

## 4. Initial Condition capability boundary

`ConditionV1/profile=BUYER_STATE_V1` remains the sole Campaign rule surface.
Procedure Profile V3 never admits a primitive, statement type or composition
operator merely because `ConditionV1` can encode it. Admission requires one
exact purpose-specific Groth16 proof profile that owns the whole relation.

The following labels describe internal capability maturity only; they are not
new protocol enums or fields.

| `ConditionV1` surface | First Solana successor scope | Maturity | Fail-closed boundary |
|---|---|---|---|
| `SPEND_VALIDITY` | Mandatory guard for every admitted relation; never a standalone qualification profile. | Required by every admitted profile. | Missing issuer, status, canonical-head, correction, provenance, subject or exact Spend binding yields no accepted proof. |
| `MERCHANT_PRODUCT_CATEGORY_RELATIONSHIP` | The first profile is the sealed alpha's single-product relation: exact product, brand, category, inclusive Condition-relative time, minimum quantity, minimum amount and currency over one approved purchase witness. | Internally adopted with executed alpha lineage; runtime unavailable. | `CampaignEpochV2.conversionRuleRef` and proof `ruleCommitment` equal `conditionId`; the absolute evaluated rule is separately bound. Exact product/status sources, V2 dependencies and projection are required. `BUYER_STATE_MERCHANT_MATCH_V1` remains a separate statement profile. |
| `FREQUENCY_INTENSITY` | The registered internal non-production `campaign.distinctPurchaseCount.audience.groth16.v1` profile covers only `BUYER_STATE_DISTINCT_PURCHASE_COUNT_GTE_V1` with threshold four, the inclusive `asOf - 44 days` through `asOf` window, `CAMPAIGN_INFLUENCED`, one namespace/issuer and positive-lower-bound-only meaning. It does not cover `BUYER_STATE_SPEND_TOTAL_CENTS_GTE_V1`. | Exact circuit, setup receipt and verifying key are registered for non-production offline conformance; runtime unavailable. | Context V2 and the complete A2c graph are required. A non-production offline-conformance Campaign Epoch may select the exact profile ref, but runtime selection requires a separate verifier registry binding; no program, runtime or Solana acceptance exists. |
| `RECENCY_LIFECYCLE` | No standalone Solana profile in the first slice. The atomic candidate's day bounds do not establish latest purchase, lifecycle state, lapse or reactivation. | Deferred. | Positive purchase-in-window and ordered lifecycle statements require exact successor profiles; negative lifecycle meaning also requires completeness. |
| `MARKET_CONTEXT` | No Solana profile in the first slice. | Deferred. | `BUYER_STATE_PURCHASE_IN_MARKET_V1` requires the exact market snapshot and a registered ZK profile; market-derived store sets remain policy inputs, not proof of buyer residence. |
| `ABSENCE_NON_MEMBERSHIP` | No Solana profile in the first slice. | Blocked. | A sparse-root non-membership path is insufficient without an adopted completeness universe, checkpoint authority, cutoff and fork policy; otherwise the result is `INDETERMINATE`. |

The initial composition boundary is similarly narrow:

| Composition | First Solana treatment |
|---|---|
| `ALL` with exactly one non-guard `BUYER_STATE_SINGLE_PRODUCT_PURCHASE_V1` requirement mapped to `sha256:9c025984870a785f34762ec3835245a7494ce9631cebdec5aebf90448fea8b4a` | Internally adopted; runtime unavailable. `SPEND_VALIDITY` remains the unconditional guard and all product, time, quantity, amount and currency predicates share one approved purchase witness. |
| `ALL` with multiple non-guard requirements | Blocked until one registered composition profile binds the required witness identity or identities. Separate proofs must not be informally combined. |
| `ANY` or `AT_LEAST` | Deferred until a registered profile defines exact requirement-result bindings, tri-state behavior, public inputs and composition limits. |

The existing Halo2 atomic-purchase profile remains immutable and unavailable.
It is not the proof artifact used by the sealed direct-Solana alpha and must not
be relabeled as that lineage. Any shared one-witness semantics require an
explicit mapping; the Halo2 circuit and key identities must not be aliased.

The first exact machine profile is
`single_product_purchase_groth16_proof_profile_v1.json` (internal artifact, not yet published).
Its presence defines source semantics and conformance; its declared
`PROTOCOL_DEFINED_RUNTIME_UNAVAILABLE` status still requires the Campaign
compiler to reject live selection. For this profile and every Condition outside
an available registered Groth16 profile, the result is `INDETERMINATE`; it
cannot produce `SolanaProofEvidenceV1` or a Campaign Outcome.

## 5. Evidence object

[`SolanaProofEvidenceV1`](../../../schemas/experimental/campaigns/solana_proof_evidence_v1.schema.json)
binds the following groups:

| Group | Required bindings |
|---|---|
| Procedure | Procedure family, version and exact ProcedureProfile content reference |
| Subject | Complete `ProofOfMatchV1` content reference, Campaign Epoch, purpose, rule, evaluated rule, scope, selected proof profile and result commitment |
| Groth16 | Circuit ID/version/artifact, VK reference/hash/account, proof hash, exact ordered BN254 fields and their ordered commitment |
| Replay | Proof-replay, purchase-reuse and optional entitlement nullifiers plus their registries |
| Solana | Chain and genesis, program, ProgramData address and executable hash, instruction-data hash, ACCEPT record PDA/hash, transaction, slot, blockhash and instruction index |

Its object reference is:

```text
solanaProofEvidenceRef =
  "sha256:" + lowercase_hex(SHA-256(RFC8785(completeEvidenceObject)))
```

No transaction signature, record PDA, proof hash or log line is a substitute
for this complete object reference.

The schema permits one to 256 named BN254 public inputs because their exact
count, names, order and meanings belong to the selected proof profile. Semantic
verification must reject duplicate names, a missing or extra input, a reordered
input, an unknown name, a mapping mismatch, or any scalar greater than or equal
to the BN254 Fr modulus. A reducing field decoder is not conformant.

## 6. Finalized observation procedure

The evidence object is transport until a relying Consumer independently
reconstructs it through a locally trusted Solana observation boundary. A caller
cannot select the RPC endpoint or supply a trusted Boolean status.

The Consumer must:

1. validate the complete evidence object and recompute its content reference;
2. resolve the exact `ProofOfMatchV1`, `CampaignEpochV2`, ProcedureProfile and
   selected purpose-specific proof profile;
3. require exact equality for Campaign, Epoch, purpose, rule, evaluated rule,
   scope, result, proof bytes, proof profile, verifying key and nullifiers;
4. apply the selected proof profile's exact public-input count, order, encoding
   and commitment mappings;
5. query the configured chain, require the exact genesis and a successful
   transaction at `FINALIZED`, and require the stated slot and blockhash;
6. locate the exact top-level instruction at `instructionIndex`, require the
   admitted program ID, hash its complete instruction bytes, parse them under
   the selected program/profile ABI, and bind the parsed proof and public
   inputs to the evidence;
7. resolve the loader ProgramData account, require the stated address, and hash
   the exact executable bytes used by that instruction;
8. resolve the program-owned verifying-key account, require its PDA, owner,
   content hash, registered VK bytes hash and circuit identity;
9. resolve the program-owned verification record, require its PDA, owner, raw
   account hash and deterministic `ACCEPT` contents for the same proof, inputs,
   VK and replay identity; and
10. check the ProofOfMatch replay, purchase-reuse and entitlement registries
    before creating an Outcome.

Missing, pruned, ambiguous, forked, stale, malformed, non-finalized or
unresolvable observations reject. A matching event log is insufficient.

An upgradeable alpha program may be observed, but evidence acceptance always
binds the exact ProgramData address and executable hash used. An upgrade is a
new executable identity and requires a new admission decision even when the
program address is unchanged.

## 7. Campaign Outcome successor

[`CampaignOutcomeV2`](../../../schemas/experimental/campaigns/campaign_outcome_v2.schema.json) preserves the
complete `CampaignOutcomeV1` field set and its conversion, assignment,
exposure, economic-admission, measurement, reward, recipient, authority and
signature semantics. Its deliberate accepted-match reference replacement is:

```text
validatorCertificateRef
-> solanaProofEvidenceRef
```

It also admits one closed audience-only result shape for an independently
authorized Outcome authority: `audienceMatch` must resolve the accepted proof
and evidence, `conversionMatch` is null, `conversionVerified` is false, the
entitlement nullifier is null, and exactly four Campaign-Epoch-scoped
purchase-reuse guards are retained. This branch records audience
qualification only. It creates no conversion, entitlement, reward, redemption,
escrow, settlement or economic authority.

This additive Outcome branch does not change any registered proof-family
identity, circuit, verifying key or public-input ABI. In particular, the
single-product proof-profile artifact retains its original historical
`outcomeSchemaRef`; Procedure Profile V3 resolves the current canonical
`CampaignOutcomeV2` by schema ID at the later Outcome-authority boundary.

The Outcome authority must resolve both `proofOfMatchRef` and the complete
Solana evidence reference and must verify that they bind the same Campaign
Epoch, purpose, rule, result and nullifiers. A valid proof or ACCEPT record does
not create an Outcome. A valid Outcome does not by itself create a Reward
Obligation, redemption, escrow release or settlement.

## 8. State and economic boundaries

ProcedureProfile V3 has `stateTransition: NONE`. It is the Campaign
qualification/finality successor only. Buyer-product or buyer-store root
transitions require their own adopted state-domain, root, checkpoint,
completeness, correction, authorization, circuit and program profile. A
Campaign conversion must not silently update buyer state, and a buyer-state
transition must not create a Campaign conversion.

The existing authority sequence remains:

```text
finalized proof verification
-> Campaign Outcome authority
-> optional Reward Obligation authority
-> Wallet Redemption authority
-> escrow and Settlement authority
```

Every boundary retains its own replay and atomicity requirements.

## 9. Adoption gates and non-claims

Before this profile can become runtime-available, implementation gates must approve:

- the canonical evidence V1 and Outcome V2 names, exact bytes and alpha
  non-adoption record;
- the sealed-alpha-to-canonical adoption crosswalk and its instance-specific
  exclusions;
- the first atomic Condition scope and fail-closed capability matrix;
- purpose-specific Condition-to-Epoch rule mapping;
- the complete single-product Groth16 proof profile, Condition-derived
  evaluated-rule mapping and hostile vectors;
- exact program ABI, ProgramData and VK account formats;
- finalized observation and replay behavior; and
- `CampaignOutcomeV2` reference-graph conformance.

This internal profile does not establish complete buyer history, root
completeness, natural-person identity, ontology correctness, circuit or VK
ceremony safety, program governance, runtime availability, deployment,
throughput, cost, Campaign authorization, reward entitlement or settlement.
