# Product Purchase Attestation V1 conformance

This package checks the strict object shape and semantic bounds that can be
validated before the official circuit artifacts exist. It contains one
accepted vector and fifteen hostile mutations. In addition to JSON Schema, the
checker enforces canonical Pasta Fp encoding for Poseidon commitments.

Run from the repository root:

```bash
python3 conformance/profiles/product-purchase-attestation-v1/scripts/check_product_purchase_attestation_v1.py
```

The source-membership vector pins the two depth-32 source paths, their exact
domains, canonical Pasta encodings, and status-at-cutoff semantics. Its
cryptographic execution is performed only by the canonical Platform
verifier/harness; this checker does not implement Poseidon. Recomputing the
47-field product-purchase commitment is also outside this vector. Passing this
source check does not establish circuit implementation, runtime availability,
validator adoption, or production deployment.
