# Single Product Purchase Match V1 conformance

This package pins the 39 typed named public inputs, their individual RFC 8785
commitments, the complete public-input-set commitment, the recipient and Spend
bindings, all three nullifiers, the result commitment, and the 78-element
Halo2 instance shape.

Run from the repository root:

```bash
python3 conformance/profiles/single-product-purchase-match-v1/scripts/check_public_inputs_v1.py
python3 conformance/profiles/single-product-purchase-match-v1/scripts/check_object_contracts_v1.py
```

The package also proves that changing the envelope `proofId` changes the replay
aggregate, replay nullifier, and public-input-set commitment. Circuit proofs,
verifier keys, and transcript fixtures remain part of the circuit-team return
packet.
