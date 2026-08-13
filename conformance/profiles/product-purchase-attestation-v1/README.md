# Product Purchase Attestation V1 conformance

This package checks the strict object shape and semantic bounds that can be
validated before the official circuit artifacts exist. It contains one
accepted vector and fifteen hostile mutations. In addition to JSON Schema, the
checker enforces canonical Pasta Fp encoding for Poseidon commitments.

Run from the repository root:

```bash
python3 conformance/profiles/product-purchase-attestation-v1/scripts/check_product_purchase_attestation_v1.py
```

The Poseidon commitment, product-evidence snapshot membership, status
membership, and ZK relation require the separately generated official circuit
vectors. Passing this source check does not establish circuit implementation,
runtime availability, validator adoption, or production deployment.
