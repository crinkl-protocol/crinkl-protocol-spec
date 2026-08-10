---
status: draft
layer: lifecycle
version: v1
normative: true
---

# Hard Verification

Comprehensive evaluation producing the canonical Spend.

**Input:** ReceiptUpload, optional SoftSpend (present if Soft Verification was performed first; absent for direct Hard Verification)
**Output:** Spend with `verificationStatus` = `HARD_VERIFIED`, `INVALIDATED`, or `CORRECTED`

*If SoftSpend is present, Hard Verification MAY use it as a hint but MUST be able to derive canonical Spend from ReceiptUpload alone.*

Hard verification produces the canonical Spend record, which can be packaged as a Spend Attestation Token for downstream verification (see ../portability/spend-attestation-token.md).

**Requirements:**
- Derive all required Spend fields (storeId, totalCents, currency, timestamp)
- Record `verificationVersion` used
- Emit Attestation Ledger entry for the state transition
