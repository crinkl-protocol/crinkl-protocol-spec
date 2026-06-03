---
status: experimental
layer: extension
version: v1
normative: true
---

# Encryption Envelopes (Prover / Brand Confidential Messages)

> **Status: v1 (optional extension) — prover/brand encrypted envelopes**
>
> This document standardizes a minimal encrypted “envelope” used to transport:
> - private witness material (non-portable), and
> - holder/prover ↔ brand offer-delivery messages
>
> The relay (e.g., Crinkl infrastructure) is assumed to be **untrusted for secrecy** and MUST NOT be required to decrypt these envelopes.

## 1) Envelope: `X25519_HKDF_SHA256_AES_256_GCM` (V1)

### 1.1 Portable shape (normative)

```text
X25519AesGcmEnvelopeV1 {
  schemaVersion: 1,
  alg: "X25519_HKDF_SHA256_AES_256_GCM",

  recipientPublicKeySpkiBase64: Base64,        // X25519 public key (DER SPKI)
  ephemeralPublicKeySpkiBase64: Base64,        // X25519 public key (DER SPKI)

  saltBase64: Base64,                          // 16 bytes
  nonceBase64: Base64,                         // 12 bytes
  ciphertextBase64: Base64,
  authTagBase64: Base64,

  aad: Object                                  // authenticated, not encrypted
}
```

### 1.2 Key formats (normative)

- `recipientPublicKeySpkiBase64` and `ephemeralPublicKeySpkiBase64` MUST be base64-encoded DER SubjectPublicKeyInfo (SPKI) bytes for an X25519 key.

### 1.3 Encryption algorithm (normative)

Given:
- recipient X25519 public key `PK_recipient`,
- fresh ephemeral X25519 keypair `(SK_eph, PK_eph)`,
- random salt `salt` (16 bytes),
- random nonce `nonce` (12 bytes),
- info string `info = UTF-8("crnkl:zk:envelope:v1")`,
- AAD object `aad`,
- plaintext JSON value `plaintext`,

Compute:

1) `shared = X25519(SK_eph, PK_recipient)`  
2) `key = HKDF-SHA256(ikm = shared, salt = salt, info = info, L = 32)`  
3) `aadBytes = UTF-8(RFC8785_canonicalize(aad))`  
4) `plaintextBytes = UTF-8(JSON_encode(plaintext))`  
5) `ciphertext, authTag = AES-256-GCM(key, nonce, plaintextBytes, aadBytes)`  

Return `X25519AesGcmEnvelopeV1` with:
- `ephemeralPublicKeySpkiBase64 = base64(DER_SPKI(PK_eph))`
- `saltBase64 = base64(salt)`
- `nonceBase64 = base64(nonce)`
- `ciphertextBase64 = base64(ciphertext)`
- `authTagBase64 = base64(authTag)`
- `aad = aad`

### 1.4 Decryption algorithm (normative)

Given a `X25519AesGcmEnvelopeV1` and the recipient private key `SK_recipient`:

1) Parse `PK_eph` from `ephemeralPublicKeySpkiBase64` (DER SPKI).  
2) `shared = X25519(SK_recipient, PK_eph)`  
3) Recompute `key` using HKDF as above.  
4) Recompute `aadBytes = UTF-8(RFC8785_canonicalize(envelope.aad))`.  
5) Decrypt and authenticate using AES-256-GCM; if authentication fails, reject.  
6) Parse decrypted bytes as JSON.

## 2) AAD binding rules (required for protocol safety)

The AAD object is part of the protocol surface: it is authenticated (integrity-protected) and MUST be treated as required binding context for the encrypted plaintext.

Implementations MUST:
- canonicalize AAD with RFC 8785 before passing to AEAD,
- reject envelopes whose AAD does not match the expected binding context for the message type.

**AAD derivation (normative):** for protocol messages, the sender MUST derive `aad` from the plaintext fields listed below (not from an independent caller-supplied object). The receiver MUST recompute the expected `aad` from the decrypted plaintext and reject if mismatched.

### 2.1 Spend witness delivery (private, non-portable)

When encrypting a `SpendZkWitnessV1` to an approved prover boundary, AAD MUST include:

```text
{ spendId, headEventHash, spendTokenHash }
```

This binds the witness to a specific spend token and attestation head.

### 2.2 Promo eligibility claim (wallet → brand)

When encrypting `PromoEligibilityClaimV1` to a brand verifier, AAD MUST include:

```text
{ spendId, headEventHash, spendTokenHash, statementId, scopeId }
```

This binds the claim to a specific spend token, statement, and promotion scope.

### 2.3 Promo decision delivery (brand → wallet)

When encrypting a `PromoGrantV1` or `PromoRejectionV1` to a wallet’s per-campaign delivery key, AAD MUST include:

```text
{ payloadId, scopeId, nullifier }
```

Implementations MAY additionally include spend-scoped anti-replay context (e.g., `spendTokenHash` or a `spendNullifier`) when applicable.

## 3) Metadata visibility note (non-normative)

This envelope format treats AAD as authenticated metadata and does not encrypt it. Deployments that require hiding AAD from relays/observers SHOULD wrap this envelope in an outer confidentiality layer (transport or message-level).
