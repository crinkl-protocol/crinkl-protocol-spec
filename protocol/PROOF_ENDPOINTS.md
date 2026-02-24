# Public Proof Endpoints (Trustless GMV + Issuance)

This doc lists the public endpoints and the exact proof each one provides. All endpoints are unauthenticated and must avoid PII.

**RecipientId note:** Reward commitment tokens expose a `recipientId`. By default this is a **blinded hash** (not a wallet address). It is safe to return publicly as a non-identifying commitment.

## 1) GET `/v1/gmv/daily/:date/token`
**Returns:** Observed GMV token for a UTC day.  
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
**Returns:** last N spendIds + per‑spend step results and proof material.  
**Proves:** “These are the last N spends and each is both GMV‑counted and reward‑issued,” without DB trust.

## 9) POST `/api/public/proofs/issued-gmv/verify`
**Input:** `spendToken + gmvToken + gmvInclusionProof + rewardToken + batchProof + batchAnchor`.  
**Returns:** step‑by‑step checks + final ok.  
**Proves:** Full expression for a spend: **attested spend → counted in GMV → reward issued → anchored**.

---

### Minimal verification order (for any verifier)
1) Verify GMV token signature.  
2) Verify spend token signature.  
3) Verify GMV inclusion proof.  
4) Verify reward token signature.  
5) Verify reward batch inclusion proof.  
6) Verify batch anchor on-chain.  

If all pass, the proof does **not** depend on the Crinkl DB.
