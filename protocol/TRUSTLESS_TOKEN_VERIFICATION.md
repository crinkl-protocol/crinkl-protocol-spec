# Trustless Verification of Crinkl Tokens (No DB Required)

This doc shows how to validate Crinkl’s token set without trusting the Crinkl database. Each section is a short, step-by-step checklist and what it proves.

## 0) Establish issuer trust (one-time)

Steps:
1) Obtain the authorized issuer public keys (crinkl-authority).  
2) Pin them as the trust root (config or registry).  

Proves:
- Any token signed by these keys is attributable to the authorized issuer, not an arbitrary server.

## 1) Verify a Spend Attestation Token

Steps:
1) Recompute the token hash from the unsigned fields.  
2) Verify the Ed25519 signature against the issuer public key.  
3) Verify the canonical spend head fields (amount, currency, timestamp, status).  
can 
Proves:
- The issuer attests to a specific finalized spend head without DB access.

## 2) Verify an Observed GMV Token

Steps:
1) Recompute the GMV token hash from the unsigned fields.  
2) Verify the Ed25519 signature against the issuer public key.  
3) Read `window.date`, `asOf.computedAt`, and `observedGMV`.  

Proves:
- The issuer attests to the GMV total for that UTC day as-of a specific time, without DB trust.

## 3) Prove a spend is counted in Observed GMV (Merkle inclusion)

Steps:
1) Obtain the inclusion proof: `{spendLeaf, leafHash, siblings}` for the GMV token.  
2) Recompute `leafHash = SHA256(0x00 || RFC8785(spendLeaf))`.  
3) Fold `siblings` with `SHA256(0x01 || sort(left,right))` to produce a root.  
4) Compare to the GMV token’s `asOf.spendHeadSetRoot`.  

Proves:
- The specific spend head was included in the GMV snapshot, without revealing the full spend list or using the DB.

## 4) Prove a spend was rewarded (Issued GMV)

Steps:
1) Verify the Reward Commitment Token signature (same hash + Ed25519 check).  
2) Obtain the batch inclusion proof for that reward token (Merkle path).  
3) Verify the batch root matches `linkage.rewardBatchRoots` (from GMV token or commitment batch metadata).  
4) Verify the batch root is anchored on-chain (onchain processor).  

Proves:
- Rewards were actually issued and anchored, independent of the DB.

## 5) (Optional) Audit continuity across days

Steps:
1) Verify `prevGMVTokenHash` chains for consecutive GMV tokens.  
2) Select the token with the latest `asOf.computedAt`.  

Proves:
- No silent history rewrite: later tokens supersede earlier ones with an auditable chain.

---

If you can verify steps 1–4, you have a complete, DB‑independent proof of:  
- a spend is real (spend attestation),  
- it is included in GMV (Merkle inclusion),  
- and it was rewarded (reward batch root anchored on-chain).
