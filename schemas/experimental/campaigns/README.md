# Campaign schema candidates

Status: `SPECIFIED_NOT_IMPLEMENTED`.

These are the public mirrors of the reduced-spine schemas adopted at
`crinkl-protocol@bdac6d3f9f32a312544b3adadbb379f98607198f` for the unimplemented
Campaign object family. They are not listed in a released public manifest and
do not establish runtime support. `CampaignEpochV2` has a successor identity because its
required fields, signed bytes, and validation meaning differ from adopted
`CampaignEpochV1`; the V1 schema and its released profile bindings remain
unchanged. Prototype artifacts without compatibility standing require no
aliases or adapters.

Spend Token schemas and the SOFT-to-HARD verification pipeline are outside this
directory and unchanged.

| Schema | Family decision |
|---|---|
| `campaign_epoch_v2.schema.json` | reduced-spine successor to the adopted signed Campaign Epoch V1 family |
| `proof_of_match_v1.schema.json` | first canonical serialized ProofOfMatch envelope |
| `proof_profile_v1.schema.json` | immutable adopted verifier contract for the first proof relation |
| `single_product_purchase_rule_v1.schema.json` | closed conversion-only rule for one product purchase |
| `single_product_purchase_dependencies_v1.schema.json` | exact transitive snapshot, policy, and nullifier-registry bindings for the first profile |
| `product_purchase_attestation_v1.schema.json` | private canonical product-purchase witness artifact |
| `spend_acceptance_entry_v1.schema.json` | private accepted Spend leaf bound to one token, head, issuer, policy, and holder commitment |
| `spend_acceptance_snapshot_v1.schema.json` | signed public Spend-acceptance root |
| `product_evidence_snapshot_v1.schema.json` | signed public product-evidence root |
| `product_evidence_status_entry_v1.schema.json` | private current-state leaf for accepted, corrected, returned, revoked, or superseded evidence |
| `product_evidence_status_snapshot_v1.schema.json` | signed public evidence-status root and cutoff |
| `commerce_entity_registry_entry_v1.schema.json` | product-to-brand/category relationship and brand/category entity leaf |
| `commerce_entity_registry_snapshot_v1.schema.json` | signed public product, brand, or category registry root |
| `validator_certificate_v1.schema.json` | first certificate restricted to `PROOF_OF_MATCH_VERIFICATION`; historical for Campaign acceptance |
| `assignment_record_v1.schema.json` | portable only for a named cross-system, dispute, or independent-consumer use |
| `campaign_outcome_v1.schema.json` | first narrow Outcome composition; superseded by V2 for the Solana path |
| `reward_obligation_v1.schema.json` | first recipient-scoped Campaign liability family |
| `settlement_record_v1.schema.json` | first liability-resolution record |
| `campaign_proof_of_match_procedure_profile_v1.schema.json` | preserved first adopted content-addressed procedure profile |
| `campaign_proof_of_match_procedure_profile_v2.schema.json` | preserved second adopted procedure profile (validator quorum); historical for Campaign acceptance |
| `campaign_proof_of_match_procedure_profile_v3.schema.json` | current adopted procedure profile: finalized Solana verification, no validator quorum |
| `solana_proof_evidence_v1.schema.json` | authenticated finalized Solana `ACCEPT` evidence for one exact ProofOfMatch |
| `campaign_outcome_v2.schema.json` | Outcome successor substituting `solanaProofEvidenceRef` for `validatorCertificateRef`; audience-only Outcomes permitted |
| `condition_v1.schema.json` | ConditionV1 rule grammar mirrored from adopted engineering source; SPECIFIED_NOT_IMPLEMENTED |
| `buyer_state_merchant_match_statement_v1.schema.json` | ConditionV1 rule grammar mirrored from adopted engineering source; SPECIFIED_NOT_IMPLEMENTED |
| `spend_total_cents_gte_statement_v1.schema.json` | ConditionV1 rule grammar mirrored from adopted engineering source; SPECIFIED_NOT_IMPLEMENTED |
| `buyer_state_purchase_in_window_statement_v1.schema.json` | ConditionV1 rule grammar mirrored from adopted engineering source; SPECIFIED_NOT_IMPLEMENTED |
| `buyer_state_purchase_in_market_statement_v1.schema.json` | ConditionV1 rule grammar mirrored from adopted engineering source; SPECIFIED_NOT_IMPLEMENTED |
| `buyer_state_distinct_purchase_count_gte_statement_v1.schema.json` | ConditionV1 rule grammar mirrored from adopted engineering source; SPECIFIED_NOT_IMPLEMENTED |
| `buyer_state_single_product_purchase_statement_v1.schema.json` | ConditionV1 rule grammar mirrored from adopted engineering source; SPECIFIED_NOT_IMPLEMENTED |
| `buyer_state_evaluation_context_v1.schema.json` | ConditionV1 rule grammar mirrored from adopted engineering source; SPECIFIED_NOT_IMPLEMENTED |
| `buyer_state_evaluation_context_v2.schema.json` | ConditionV1 rule grammar mirrored from adopted engineering source; SPECIFIED_NOT_IMPLEMENTED |
| `buyer_state_evaluation_policy_artifact_v1.schema.json` | ConditionV1 rule grammar mirrored from adopted engineering source; SPECIFIED_NOT_IMPLEMENTED |

The ConditionV1 rule-grammar rows are byte-identical mirrors of the
`protocol/applications/schemas/` files at
`crinkl-protocol@156d63c37d4d4b9a31287e86d7623afdbe642997`. Their
normative text is
[`condition-v1.md`](../../../protocol/applications/conditions/condition-v1.md),
[`buyer-state-statements-v1.md`](../../../protocol/applications/conditions/buyer-state-statements-v1.md),
and
[`buyer-state-evaluation-policies-v1.md`](../../../protocol/applications/conditions/buyer-state-evaluation-policies-v1.md).
`spend_total_cents_gte_statement_v1.schema.json` keeps its adopted filename;
its `title` is `BuyerStateSpendTotalCentsGteStatementV1`. `EvidenceCompletenessPolicyV1`
and the other typed policy artifacts are variants inside
`buyer_state_evaluation_policy_artifact_v1.schema.json`. Publishing these
mirrors is an unreleased experimental candidate and establishes no runtime,
evaluator, or deployment support.

The current artifact is
[`campaign_proof_of_match_procedure_profile_v3.json`](../../../protocol/applications/artifacts/campaign_proof_of_match_procedure_profile_v3.json),
canonical content reference
`sha256:73306e3b904dd05fda008da1ca6c2858d545f3dd9503366836d6833da7aee3ec`,
mirrored from `crinkl-protocol@156d63c37d4d4b9a31287e86d7623afdbe642997`.
ProcedureProfile V2 remains available at
`sha256:6aef46ed82deb6cb197812f8b0de130915a7ecf9e926a809df996421202be915`
and V1 at
`sha256:5472a7d975a6abbc8c8b99b85e3007bb3d57a980d203d36898d91ed746a58fb0`;
both are historical for Campaign proof acceptance.

## Common content references and signatures

Unless a schema says otherwise, an artifact reference is:

```text
"sha256:" + lowercase_hex(SHA-256(RFC8785(complete artifact bytes)))
```

For signed objects, compute the unsigned canonical bytes by omitting the entire
top-level `signatures` member. `signatures.objectHash` is the lowercase SHA-256
hex digest without the `sha256:` prefix. Ed25519 signs the raw 32 digest bytes.
The external reference is `sha256:` plus `objectHash`.

`ProofOfMatchV1` has no additional object signature: its subject hash is the
artifact reference over the complete envelope. Its `proof.proofBytesHash`
separately authenticates the decoded ZK proof bytes.

`SolanaProofEvidenceV1` has no object signature: its reference is the artifact
reference over the complete object, recomputed by the relying Consumer from its
own finalized observation. Historical `ValidatorCertificateV1` signatures sign
the raw 32 bytes identified by `decisionHash` as fixed by
[`../../../governance/proof-validator-campaign-refactor-handoff.md`](../../../governance/proof-validator-campaign-refactor-handoff.md).

JSON Schema cannot enforce reference resolution, hash equality across fields,
signature authority, time ordering, proof verification, deterministic
assignment, atomic capacity admission, or nullifier uniqueness. Every
conforming implementation must run the normative semantic procedures in the
Campaign architecture and applicable profile in addition to schema validation.
