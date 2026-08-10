---
status: experimental
layer: extension
version: v1
normative: true
---

# Public Proof Endpoint Appendix

> **Status: non-normative API appendix**
>
> This document lists example endpoint surfaces for serving already-defined protocol artifacts. It is not part of core protocol validity, and deployments MAY expose different paths or authentication policies as long as token/proof verification follows the normative procedures in `../portability/spend-attestation-token.md`, `../applications/economics/settlement-bindings.md`, and `../portability/verifier-requirements.md`.

Any public proof endpoint MUST avoid PII and MUST NOT become a lookup oracle over receipt history, wallet identity, campaign participation, or campaign-scoped audience membership.

**RecipientId note:** Reward commitment tokens expose a `recipientId`. By default this is a **blinded hash** (not a wallet address). It is safe to return publicly as a non-identifying commitment.

**SpendId lookup note:** Per-spend proof lookup is safe only when `spendId` values are high entropy and the endpoint applies an explicit access policy or holder-provided proof of knowledge. Public enumeration of spend IDs, recent spend IDs, or campaign-scoped spend membership is not a protocol requirement and SHOULD be avoided.

## 1) GET `/v1/gmv/daily/:date/token`
**Returns:** Verified GMV token for a UTC day.
**Proves:** The issuer attested the aggregate GMV snapshot for that date (no DB trust; signature checkable).

## 2) POST `/v1/gmv/verify`
**Input:** GMV token.  
**Returns:** signature + issuer checks.  
**Proves:** The GMV token is authentic and signed by an authorized issuer.

## 3) POST `/v1/spend-tokens/verify`
**Input:** Spend attestation token.  
**Returns:** signature + schema checks.  
**Proves:** The canonical spend head (date/total/currency/status) was attested by the issuer.

## 4) GET `/api/public/proofs/gmv-inclusion/:spendId?date=YYYY-MM-DD`
**Returns:** `{gmvTokenHash, spendLeaf, merkleProof}`.  
**Proves:** This spend was included in the GMV snapshot for that day (Merkle inclusion under `spendHeadSetRoot`).

## 5) POST `/api/public/proofs/reward-commitment/verify`
**Input:** Reward commitment token.  
**Returns:** signature + schema checks.  
**Proves:** The reward commitment token is authentic and issued by the issuer.

## 6) GET `/api/public/proofs/reward-commitment/:batchId`
**Returns:** `{batchId, merkleRoot, createdAt, onchainAnchor}`.  
**Proves:** The batch root exists and is anchored on-chain (economic issuance is externally committed).

## 7) GET `/api/public/proofs/reward-commitment/:batchId/spend/:spendId`
**Returns:** `{spendId, batchId, leafHash, merkleProof}`.  
**Proves:** The spend’s reward commitment is included in the anchored batch (Merkle inclusion).

## 8) GET `/api/public/proofs/issued-gmv/recent?limit=N`
**Status:** deployment-specific audit endpoint, not a required public protocol endpoint.
**Returns:** aggregate or redacted recent proof samples; MUST NOT expose raw recent `spendId` lists unless an explicit audit policy allows it.
**Proves:** bounded audit sampling of issued-GMV proof construction, without making recent spend history publicly enumerable.

## 9) POST `/api/public/proofs/issued-gmv/verify`
**Input:** `spendToken + gmvToken + gmvInclusionProof + rewardToken + batchProof + batchAnchor`.  
**Returns:** step‑by‑step checks + final ok.  
**Proves:** Full expression for a spend: **attested spend → counted in GMV → reward issued → anchored**.

## 10) GET `/api/public/proofs/campaign-settlement/:settlementBatchId`
**Status:** optional extension endpoint for `CAMPAIGN_SETTLEMENT_COMMITTED`.
**Returns:** `{settlementBatchId, campaignId, campaignParamsHash, root, leafCount, totalPayoutAmount, payoutAsset, schemaVersion, txRef, committedAt}` plus the signed system-stream event when available.
**Proves:** A campaign settlement batch root was signed by an authorized committer and publicly anchored.

## 11) GET `/api/public/proofs/campaign-settlement/:settlementBatchId/approval/:approvalHash`
**Status:** optional extension endpoint for holder-, sponsor-, or auditor-authorized lookup.
**Returns:** `{settlementBatchId, approvalHash, leafHash, merkleProof, leaf}` where `leaf` is a `CampaignSettlementLeafV1` or a redacted leaf plus disclosure proof.
**Proves:** A verifier-approved campaign conversion was included in a public campaign settlement batch.

This endpoint MUST NOT allow public enumeration of campaign participants. Deployments SHOULD require the requester to know `approvalHash`, `settlementNullifier`, or another high-entropy authorization handle.

---

### Minimal verification order (for any verifier)
1) Verify GMV token signature.  
2) Verify spend token signature.  
3) Verify GMV inclusion proof.  
4) Verify reward token signature.  
5) Verify reward batch inclusion proof.  
6) Verify batch anchor on-chain.  
7) For campaign settlement, verify `CAMPAIGN_SETTLEMENT_COMMITTED`, leaf inclusion, and `txRef` anchoring.

If all pass, the proof does **not** depend on the Crinkl DB. Endpoint availability itself is still deployment policy, not protocol validity.
