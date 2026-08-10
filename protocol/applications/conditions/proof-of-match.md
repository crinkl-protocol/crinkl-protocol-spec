---
status: draft
layer: predicate
version: v1
normative: true
---

# Proof of Match

Proof of Match is the result of evaluating one or more Spend Attestations against a Spend Predicate. It proves that the referenced attestations satisfy the predicate within a declared scope.

Proof of Match is downstream of Spend Attestation and upstream of Reward Commitment, settlement, campaigns, analytics, or agent responses. It MUST NOT be treated as a new Spend Attestation and MUST NOT mutate the underlying spend proof.

For campaign flows, a **ProofOfMatch** MUST bind to exactly one CampaignEpoch by `campaignId`, `epochId`, `epochVersion`, and `ruleSetHash`. A verifier MUST select the epoch using the CampaignEpoch `timingRule`:

- `SPEND_TIMESTAMP`
- `ATTESTATION_TIMESTAMP`
- `CLAIM_TIMESTAMP`

If `timingRule` is missing, the CampaignEpoch is invalid and no valid ProofOfMatch can be produced. A single ProofOfMatch MUST NOT span multiple epochs; spends that fall under different epochs require separate ProofOfMatch results.

A RewardCommitment may be produced only after a valid ProofOfMatch. The ProofOfMatch does not define reward math; it only proves that the selected epoch's predicate was satisfied.
