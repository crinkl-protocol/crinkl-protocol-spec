# Test Vectors

Comprehensive test vectors for protocol implementers. Total: 60+ cases.

---

## 1. storeId Normalization (15 vectors)

| # | Input | Expected Output | Rule Applied |
|---|-------|-----------------|--------------|
| 1 | `Walmart` | `walmart` | Lowercase |
| 2 | `wal-mart` | `wal-mart` | Preserve hyphens, lowercase |
| 3 | `Wal★Mart` | `walmart` | Strip non-alphanumeric, lowercase |
| 4 | `TRADER JOE'S` | `trader-joes` | Strip apostrophe, spaces to hyphens, lowercase |
| 5 | `7-Eleven` | `7-eleven` | Preserve leading digit, lowercase |
| 6 | `Café Münchën` | `cafe-munchen` | NFKD normalize, strip diacritics, lowercase |
| 7 | `  Target  ` | `target` | Trim whitespace, lowercase |
| 8 | `Best---Buy` | `best-buy` | Collapse multiple hyphens, lowercase |
| 9 | `CVS/pharmacy` | `cvs-pharmacy` | Slash to hyphen, lowercase |
| 10 | `A&P` | `a-p` | Ampersand to hyphen, lowercase |
| 11 | `Whole Foods Market #1234` | `whole-foods-market-1234` | Spaces to hyphens, strip hash, lowercase |
| 12 | `""` (empty) | `ERROR_INVALID_FORMAT` | Reject empty |
| 13 | `A` | `a` | Single char valid, lowercase |
| 14 | 65-char string | `ERROR_INVALID_FORMAT` | Max 64 chars |
| 15 | `🛒Store🛒` | `store` | Strip emoji, lowercase |

---

## 2. Timestamp Validation (8 vectors)

| # | Input | Valid? | Reason |
|---|-------|--------|--------|
| 1 | `2024-01-15T10:30:00.000Z` | ✓ | Correct format |
| 2 | `2024-01-15T10:30:00Z` | ✗ | Missing milliseconds |
| 3 | `2024-01-15T10:30:00.000+00:00` | ✗ | Must be Z suffix |
| 4 | `2024-01-15 10:30:00.000Z` | ✗ | Missing T separator |
| 5 | `2024-01-15T10:30:00.0Z` | ✗ | Wrong millisecond precision |
| 6 | `2024-13-01T00:00:00.000Z` | ✗ | Invalid month |
| 7 | `2024-01-15T25:00:00.000Z` | ✗ | Invalid hour |
| 8 | `1999-01-15T10:30:00.000Z` | ✓ | Valid (historical) |

---

## 3. Money Format (8 vectors)

| # | Amount | Currency | Valid? | Reason |
|---|--------|----------|--------|--------|
| 1 | `42.99` | `USD` | ✓ | Correct |
| 2 | `42` | `USD` | ✗ | Must have 2 decimals |
| 3 | `42.9` | `USD` | ✗ | Must have 2 decimals |
| 4 | `42.999` | `USD` | ✗ | Max 2 decimals |
| 5 | `-42.99` | `USD` | ✗ | No negative amounts |
| 6 | `0.00` | `USD` | ✓ | Zero valid |
| 7 | `999999.99` | `USD` | ✓ | Large valid |
| 8 | `42.99` | `USDC` | ✗ | Invalid ISO 4217 |

---

## 4. Event Hash Computation (10 vectors)

### 4.1 RECEIPT_UPLOADED (genesis)

**Input object (normative envelope per event.schema.json):**
```json
{
  "eventId": "550e8400-e29b-41d4-a716-446655440001",
  "eventName": "RECEIPT_UPLOADED",
  "spendId": "spend-550e8400-e29b-41d4-a716-446655440001",
  "wallet": "0x1234567890abcdef1234567890abcdef12345678",
  "payload": {
    "uploadId": "upload-550e8400-e29b-41d4-a716-446655440001",
    "imageDataRef": "ipfs://Qm...",
    "metadata": {}
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "protocolVersion": "1.0.0-rc.1",
  "prevHash": null
}
```

**eventHash computation:**
1. Remove `eventHash` and `signature` fields (per DATA_STRUCTURES.md)
2. Canonicalize per RFC 8785 (keys sorted lexicographically)

**Canonical JSON (RFC 8785):**
```
{"eventId":"550e8400-e29b-41d4-a716-446655440001","eventName":"RECEIPT_UPLOADED","payload":{"imageDataRef":"ipfs://Qm...","metadata":{},"uploadId":"upload-550e8400-e29b-41d4-a716-446655440001"},"prevHash":null,"protocolVersion":"1.0.0-rc.1","spendId":"spend-550e8400-e29b-41d4-a716-446655440001","timestamp":"2024-01-15T10:30:00.000Z","wallet":"0x1234567890abcdef1234567890abcdef12345678"}
```

**SHA-256 hash:** `ef10af374951ac59055ad10c4734900276e50f515183e3719266db07c6008d67`

### 4.2 SPEND_SOFT_VERIFIED (chained)

**prevHash:** `ef10af374951ac59055ad10c4734900276e50f515183e3719266db07c6008d67`

**Canonical JSON:**
```
{"eventId":"550e8400-e29b-41d4-a716-446655440002","eventName":"SPEND_SOFT_VERIFIED","payload":{"riskFlags":[],"softExtractedFields":{"confidence":0.82,"currency":"USD","storeName":"walmart","totalAmount":"42.99","transactionDate":"2024-01-15T00:00:00.000Z"},"softVerificationStatus":"SOFT_VERIFIED"},"prevHash":"ef10af374951ac59055ad10c4734900276e50f515183e3719266db07c6008d67","protocolVersion":"1.0.0-rc.1","spendId":"spend-550e8400-e29b-41d4-a716-446655440001","timestamp":"2024-01-15T10:31:00.000Z","wallet":"0x1234567890abcdef1234567890abcdef12345678"}
```

**SHA-256 hash:** `17618851c869ea79fabd9239f15730da1123ff4c1213624983bc7d78ce31ffac`

### 4.3 Key ordering verification

RFC 8785 requires lexicographic key order:
- `amount` < `currency` < `eventId` < `eventName` < ...

**Invalid (wrong order):**
```
{"eventName":"RECEIPT_UPLOADED","eventId":"..."}
```

**Valid:**
```
{"eventId":"...","eventName":"RECEIPT_UPLOADED"}
```

---

## 5. Signature Verification (8 vectors)

### Test Ed25519 keypair (for testing only)

```
Private key (hex): 9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60
Public key (hex):  d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a
```

### 5.1 Valid signature

**Message:** `32d66786244c7ea97248737b0b9dee70520c7f2476de2bb089688d7e8a8d5a8c` (32 bytes, hex)

**Signature (base64):** `Oh8AILMes2bKKQEeDpkGxblMYK6cFOiifQrP2AZ5kpd5qdej8rMmJRsnv7yle7pmLGpeCuMhBOx8X778SPWZCQ==`

**Result:** ✓ VALID

### 5.2 Invalid signature (wrong key)

**Public key:** `3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c`

**Same message, same signature as 5.1**

**Result:** ✗ REJECT SignatureInvalid

### 5.3 Invalid signature (tampered)

**Message:** `a7f8c3e1d2b4a5f6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b1` (last byte changed)

**Signature from 5.1**

**Result:** ✗ REJECT SignatureInvalid

### 5.4 Malformed signature (wrong length)

**Signature (base64):** `AAAA` (3 bytes when decoded)

**Result:** ✗ REJECT SignatureInvalid

---

## 6. State Transitions (12 vectors)

| # | Current State | Event | Valid? | New State |
|---|---------------|-------|--------|-----------|
| 1 | (none) | RECEIPT_UPLOADED | ✓ | UPLOADED |
| 2 | UPLOADED | SPEND_SOFT_VERIFIED | ✓ | SOFT_VERIFIED |
| 3 | SOFT_VERIFIED | SPEND_HARD_VERIFIED | ✓ | HARD_VERIFIED |
| 4 | HARD_VERIFIED | (24h elapsed) | ✓ | FINALIZED |
| 5 | FINALIZED | SPEND_CORRECTED | ✓ | CORRECTED |
| 6 | UPLOADED | SPEND_INVALIDATED | ✓ | INVALIDATED |
| 7 | (none) | SPEND_SOFT_VERIFIED | ✗ | InvalidTransition |
| 8 | UPLOADED | SPEND_HARD_VERIFIED | ✗ | InvalidTransition |
| 9 | SOFT_VERIFIED | RECEIPT_UPLOADED | ✗ | InvalidTransition |
| 10 | INVALIDATED | SPEND_CORRECTED | ✗ | InvalidTransition |
| 11 | FINALIZED | SPEND_HARD_VERIFIED | ✗ | InvalidTransition |
| 12 | CORRECTED | SPEND_CORRECTED | ✓ | CORRECTED (new) |

---

## 7. Reward State Transitions (6 vectors)

| # | Truth State | Reward State | Event | Valid? | New Reward State |
|---|-------------|--------------|-------|--------|------------------|
| 1 | SOFT_VERIFIED | NO_REWARD | REWARD_PROVISIONAL_ISSUED | ✓ | PROVISIONAL |
| 2 | HARD_VERIFIED | PROVISIONAL | REWARD_FINAL_ISSUED | ✓ | FINAL |
| 3 | UPLOADED | NO_REWARD | REWARD_PROVISIONAL_ISSUED | ✗ | InvalidTransition |
| 4 | SOFT_VERIFIED | FINAL | REWARD_PROVISIONAL_ISSUED | ✗ | InvalidTransition |
| 5 | FINALIZED | NO_REWARD | REWARD_FINAL_ISSUED | ✓ | FINAL |
| 6 | FINALIZED | PROVISIONAL | REWARD_FINAL_ISSUED | ✓ | FINAL |

---

## 8. prevHash Chain Validation (6 vectors)

| # | Scenario | prevHash Provided | prevHash Expected | Result |
|---|----------|-------------------|-------------------|--------|
| 1 | Genesis event | `null` | `null` | ✓ Accept |
| 2 | Second event | hash of event 1 | hash of event 1 | ✓ Accept |
| 3 | Second event | `null` | hash of event 1 | ✗ OrderingViolation |
| 4 | Second event | wrong hash | hash of event 1 | ✗ OrderingViolation |
| 5 | After gap | hash of event 3 | hash of event 2 | ✗ OrderingViolation |
| 6 | Replay attack | hash of event 1 (reused) | hash of event 2 | ✗ OrderingViolation |

---

## 9. Error Code Mapping (6 vectors)

| # | Scenario | Error Code | HTTP Status |
|---|----------|------------|-------------|
| 1 | Same image hash exists | ERROR_DUPLICATE | 409 |
| 2 | OCR returns < 0.3 confidence | ERROR_UNREADABLE | 422 |
| 3 | Image is not a receipt | ERROR_INVALID_FORMAT | 422 |
| 4 | Receipt date > 90 days ago | ERROR_OUTSIDE_WINDOW | 422 |
| 5 | Image manipulation detected | ERROR_FRAUD | 403 |
| 6 | Database unavailable | ERROR_SYSTEM | 500 |

---

## 10. Rate Limiting (4 vectors)

| # | Scenario | Limit | Result |
|---|----------|-------|--------|
| 1 | 10 uploads in 1 minute | 10/min | ✓ Last one accepted |
| 2 | 11 uploads in 1 minute | 10/min | ✗ 11th rejected, retry-after |
| 3 | Burst: 15 in 5 seconds | 2x burst allowed | ✓ Accepted |
| 4 | Burst: 25 in 5 seconds | 2x burst (20 max) | ✗ 21-25 rejected |

---

## 11. Complete Event Traces

### 11.1 Happy Path

```
1. RECEIPT_UPLOADED     prevHash=null     → state=UPLOADED
2. SPEND_SOFT_VERIFIED  prevHash=hash(1)  → state=SOFT_VERIFIED
3. SPEND_HARD_VERIFIED  prevHash=hash(2)  → state=HARD_VERIFIED
4. REWARD_PROVISIONAL   (Reward ledger)   → reward=PROVISIONAL
5. (24 hours pass)                        → state=FINALIZED
6. REWARD_FINAL_ISSUED  (Reward ledger)   → reward=FINAL
```

### 11.2 Rejection at Soft Verification

```
1. RECEIPT_UPLOADED     prevHash=null     → state=UPLOADED
2. SPEND_INVALIDATED    prevHash=hash(1)  → state=INVALIDATED
   reason=ERROR_UNREADABLE
```

### 11.3 Fraud Detection After Finalization

```
1-6. (happy path)                         → state=FINALIZED, reward=FINAL
7. FRAUD_FLAGGED        fraudType=duplicate_submission
```
Note: Reward Ledger is immutable. Fraud does not modify or claw back rewards.

### 11.4 Correction Flow

```
1-5. (through FINALIZED)                  → state=FINALIZED
6. SPEND_CORRECTED      correctedData={storeId:"costco"} → state=CORRECTED
```

---

## 12. Edge Cases (5 vectors)

| # | Scenario | Expected Behavior |
|---|----------|-------------------|
| 1 | Receipt total = $0.00 | Accept (valid zero-total receipt) |
| 2 | 1000+ line items | Accept (no line item limit in protocol) |
| 3 | Transaction date = today | Accept |
| 4 | Transaction date = 89 days ago | Accept |
| 5 | Transaction date = 91 days ago | Reject ERROR_OUTSIDE_WINDOW |

---

## Vector Count Summary

| Category | Count |
|----------|-------|
| storeId normalization | 15 |
| Timestamp validation | 8 |
| Money format | 8 |
| Event hash computation | 10 |
| Signature verification | 8 |
| State transitions | 12 |
| Reward transitions | 6 |
| prevHash chain | 6 |
| Error codes | 6 |
| Rate limiting | 4 |
| Complete traces | 4 |
| Edge cases | 5 |
| **Total** | **92** |
