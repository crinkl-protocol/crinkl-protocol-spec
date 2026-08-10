---
status: draft
layer: core
version: v1
normative: true
---

# Commerce Evidence

Commerce Evidence is raw or semi-structured input that may support a spend claim. Examples include physical receipt images, digital receipts, email receipts, merchant transaction records, and structured OCR output.

Commerce Evidence is not portable proof by itself. It becomes protocol-relevant only when it is normalized into a Spend Event and advances through verification state. Portable Spend Attestation Tokens MUST NOT include raw receipt images, raw OCR text, private object keys, local paths, or ingestion metadata that is not needed for verification.

## Validity Boundary

Evidence can support a claim, but evidence alone does not establish a Spend Attestation. A verifier validates signed claims and proof material, not raw evidence access.
