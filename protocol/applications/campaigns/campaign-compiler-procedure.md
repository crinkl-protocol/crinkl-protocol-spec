---
status: draft
layer: applications
version: vnext
normative: true
implementationStatus: PARTIAL_NON_PRODUCTION_ENGINEERING
---

# Campaign compiler procedure

The compiler turns a Campaign definition into a signed `CampaignEpochV2` that
names an exact proof family for each purpose slot. It is the procedure that
makes "many Campaigns, one pipeline" true: every Campaign passes through the
same steps, and any definition the procedure cannot route fails closed.

Mirrored from the merged engineering contract at
`crinkl-platform@2a3a7d6eaf1f7ef9a609ca997951bf3960b17975`
(`services/attestation-gateway/src/domain/businessCampaignSolanaCompilation.ts`)
and `crinkl-protocol@156d63c37d4d4b9a31287e86d7623afdbe642997`. The engineering
implementation is authority for exact behavior; this page is the public
contract. Maturity is non-production and compile-only: no proof, Solana
transaction, Outcome, entitlement, reward or settlement is created by
compilation.

## Inputs

1. one `ConditionV1` per purpose slot, with its exact statements;
2. the evaluation context (`BuyerStateEvaluationContextV1` or `V2` as the
   statements require) and its cutoff;
3. the dependency set the family requires (for the atomic family,
   `SingleProductPurchaseDependenciesV2` including the Campaign-pinned
   `ProductSourceSignerAuthorityBindingV1`);
4. the Epoch slot purpose, `AUDIENCE` or `CONVERSION`;
5. the committed reuse, replay, timing, observation and dispute policies and
   any reward, admission, capacity, budget, inventory or allocation policy; and
6. the Campaign authority signing key.

## Procedure

1. **Definition identity.** `definitionRef = conditionId(ConditionV1)`, the
   SHA-256 over the RFC 8785 bytes of the Condition. The compiler creates no
   second definition hash. Purpose is supplied by the slot, not by the
   definition: the same Condition may fill `audienceRuleRef` in one Epoch and
   `conversionRuleRef` in another without changing its hash.
2. **Graph validation.** Validate the complete Condition graph before family
   selection: exactly one `SPEND_VALIDITY` guard; every non-guard requirement
   carries a resolvable `statementId`; window-bearing primitives carry a
   relative window; statement types match the evaluation context version;
   absence-bearing requirements carry a completeness policy reference.
3. **Family selection.** Return an already registered proof profile: its
   circuit identity, verifying-key reference and hash, public-input order and
   evaluated-rule commitment rule. Selection is exact: one composition shape
   maps to one family. At this revision the admitted mappings are:

   | Composition | Family |
   |---|---|
   | `ALL` over the guard and exactly one `BUYER_STATE_SINGLE_PRODUCT_PURCHASE_V1` requirement, purpose `CONVERSION` | `campaign.atomicProductPurchase.solanaGroth16.v1` |
   | `ALL` over the guard and exactly one `BUYER_STATE_DISTINCT_PURCHASE_COUNT_GTE_V1` requirement with `minimumDistinctPurchaseCount = 4`, window `-44..0`, `acceptedEvidenceClasses = [CAMPAIGN_INFLUENCED]`, evaluation context V2, purpose `AUDIENCE` | `campaign.distinctPurchaseCount.audience.groth16.v1` |

4. **Evaluated rule.** Materialize the family's evaluated-rule object from the
   Condition, context, dependencies and, where the family requires it, the
   signed Epoch reference; compute `evaluatedRuleCommitment` as the SHA-256 of
   its RFC 8785 bytes. For the atomic family the evaluated rule is committed
   in-circuit as `CLOSED_RULE_COMMITMENT`; for the distinct-count family the
   circuit binds the same preimage through an in-circuit hash.
5. **Epoch assembly.** Write `definitionRef` into the purpose slot and the
   family's profile reference into `requiredProofProfiles`; pin the dependency
   set, signer binding, reuse registry and replay registry references in
   `registryRefs`; require `purchaseReuseRegistryRef` to equal the Epoch's
   `reusePolicyRef`; sign with the Campaign authority.
6. **Fail closed.** Any of the following rejects with no Epoch:
   - a composition with no admitted family, including `ALL` over several
     non-guard requirements, `ANY` and `AT_LEAST`;
   - an absence-bearing requirement (`ABSENCE_NON_MEMBERSHIP`, or any
     statement whose meaning is "has not purchased") — there is no admitted
     completeness authority;
   - a distinct-count statement whose count, window, provenance class or
     context version differs from the frozen family;
   - a product, brand or category set where the family admits one exact
     reference;
   - a runtime selection of a profile whose availability is not runtime-enabled
     (every registered family at this revision);
   - a missing, unresolved, self-authorized, wrong-role, expired or revoked
     product signer; and
   - a reuse or replay registry not pinned in `registryRefs` or not equal to
     the Epoch policy.

## Parameter versus family

A change is configuration when the admitted family reads the value from the
committed rule: the atomic family reads product, brand and category
references, store set root, day and time bounds, minimum quantity, minimum net
amount and currency. Such a change produces a new `definitionRef` and the same
family, circuit and verifying key.

A change is a new family when the witness shape changes: a set of products
instead of one, a different count or window in the distinct-count relation, a
conversion-purpose count, a second requirement over a second purchase, or any
negative proposition. The compiler rejects these until a family is registered;
it never widens an existing family to admit them.

## What compilation establishes

- one immutable, content-addressed Campaign definition per slot;
- one signed Epoch that names exactly which registered relation may prove it;
- deterministic recompilation: identical inputs produce an identical Epoch
  reference; and
- nothing else. Compilation does not prove qualification, create a proof,
  reach Solana, create an Outcome, or authorize any economic effect.

## Sources

- `crinkl-platform@2a3a7d6e`: `services/attestation-gateway/src/domain/businessCampaignSolanaCompilation.ts`, `businessCampaignSolanaCompilation.test.ts`, `packages/protocol/src/campaignSolanaProof.ts`, `packages/protocol/src/buyerStateCondition.ts`.
- `crinkl-protocol@156d63c3`: `protocol/applications/schemas/condition_v1.schema.json`, `campaign_epoch_v2.schema.json`, `atomic_product_purchase_evaluated_rule_v1.schema.json`, `distinct_purchase_count_audience_evaluated_rule_v1.schema.json`, `product_source_signer_authority_binding_v1.schema.json`.
