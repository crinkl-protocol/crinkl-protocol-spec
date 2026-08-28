# Product Purchase Attestation V1 conformance

This package checks the strict object shape and semantic bounds that can be
validated before the official circuit artifacts exist. It contains one
accepted vector and fifteen hostile mutations. In addition to JSON Schema, the
checker enforces canonical Pasta Fp encoding for Poseidon commitments.

Run from the repository root:

```bash
python3 conformance/profiles/product-purchase-attestation-v1/scripts/check_product_purchase_attestation_v1.py
```

The source-membership vector pins one complete PPA input, its expected
47-field commitment, RFC 8785 content reference, product path, linked status
entry/reference, status path, exact domains, canonical Pasta encodings, and
status-at-cutoff semantics. This checker validates those object and reference
links but does not implement Poseidon; cryptographic execution and the
47-field commitment recomputation are performed only by the canonical Platform
verifier/harness. The fixture's `authentication.snapshotRef` is a canonical
literal, not snapshot authority: Platform constructs and verifies the signed
snapshot/ref separately. Passing this source check does not establish circuit
implementation, runtime availability, validator adoption, or production
deployment.
