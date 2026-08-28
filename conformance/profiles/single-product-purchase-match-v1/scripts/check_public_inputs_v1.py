#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[4]
VECTOR = ROOT / "conformance/profiles/single-product-purchase-match-v1/conformance/v1/public-input-vector.json"
BUILD_CONTRACT = ROOT / "protocol/applications/artifacts/single_product_purchase_match_v1_build_contract.json"
TREE_PROFILE = ROOT / "protocol/applications/artifacts/h2_binary_poseidon_pasta_fp_depth32_v1.json"
PROOF_PROFILE_SCHEMA = ROOT / "schemas/experimental/campaigns/proof_profile_v1.schema.json"

ORDER = [
    ("proofProfileRef", "SHA256_REF"),
    ("purpose", "ENUM"),
    ("proofId", "IDENTIFIER"),
    ("campaignId", "IDENTIFIER"),
    ("campaignEpochRef", "SHA256_REF"),
    ("ruleCommitment", "SHA256_REF"),
    ("scopeRef", "SHA256_REF"),
    ("inputSetCommitment", "SHA256_REF"),
    ("spendTokenBinding", "SHA256_REF"),
    ("canonicalHeadBinding", "SHA256_REF"),
    ("spendIssuerRegistryRef", "SHA256_REF"),
    ("spendVerificationPolicyRef", "SHA256_REF"),
    ("spendAcceptanceSnapshotRef", "SHA256_REF"),
    ("spendAcceptanceSnapshotRoot", "POSEIDON_FP"),
    ("spendAcceptanceSnapshotTreeProfileRef", "SHA256_REF"),
    ("productSourceSignerAuthorityBindingRef", "SHA256_REF"),
    ("productVerificationPolicyRef", "SHA256_REF"),
    ("productRegistrySnapshotRef", "SHA256_REF"),
    ("productRegistryRoot", "POSEIDON_FP"),
    ("productRegistryTreeProfileRef", "SHA256_REF"),
    ("brandRegistrySnapshotRef", "SHA256_REF"),
    ("brandRegistryRoot", "POSEIDON_FP"),
    ("brandRegistryTreeProfileRef", "SHA256_REF"),
    ("categoryRegistrySnapshotRef", "SHA256_REF"),
    ("categoryRegistryRoot", "POSEIDON_FP"),
    ("categoryRegistryTreeProfileRef", "SHA256_REF"),
    ("productEvidenceSnapshotRef", "SHA256_REF"),
    ("productEvidenceSnapshotRoot", "POSEIDON_FP"),
    ("productEvidenceSnapshotTreeProfileRef", "SHA256_REF"),
    ("evidenceStatusSnapshotRef", "SHA256_REF"),
    ("evidenceStatusRoot", "POSEIDON_FP"),
    ("evidenceStatusTreeProfileRef", "SHA256_REF"),
    ("statusCutoffUnixMs", "UNIX_MS"),
    ("recipientScopeCommitment", "SHA256_REF"),
    ("proofReplayInputsCommitment", "SHA256_REF"),
    ("proofReplayNullifier", "SHA256_REF"),
    ("purchaseReuseNullifier", "SHA256_REF"),
    ("entitlementNullifier", "SHA256_REF"),
    ("resultCommitment", "SHA256_REF"),
]


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def hash_ref(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest(value: str) -> bytes:
    return bytes.fromhex(value.removeprefix("sha256:"))


def poseidon_bytes(value: str) -> bytes:
    return bytes.fromhex(value.removeprefix("poseidon:"))


def value_commitment(name: str, value_type: str, value: str) -> str:
    return hash_ref(canonical({
        "domain": "crinkl:proof-of-match:public-input:v1",
        "name": name,
        "valueType": value_type,
        "value": value,
    }))


def derive(vector: dict[str, Any]) -> dict[str, Any]:
    values = dict(vector["values"])
    private = vector["private"]
    holder_public_key = bytes.fromhex(private["holderPublicKeyHex"])
    if len(holder_public_key) != 32:
        raise AssertionError("holder public key must be 32 bytes")

    def fixed_hash(domain: str, *parts: bytes) -> str:
        return hash_ref(domain.encode() + b"\x00" + b"".join(parts))

    secret = digest(fixed_hash(
        "CRINKL:POM:RECIPIENT_SCOPE_SECRET:SINGLE_PRODUCT_PURCHASE_MATCH:V1",
        holder_public_key, digest(values["scopeRef"]),
    ))

    values["recipientScopeCommitment"] = fixed_hash(
        "CRINKL:POM:RECIPIENT_SCOPE:SINGLE_PRODUCT_PURCHASE_MATCH:V1", secret
    )
    values["spendTokenBinding"] = fixed_hash(
        "CRINKL:POM:SPEND_TOKEN_BINDING:SINGLE_PRODUCT_PURCHASE_MATCH:V1",
        digest(private["spendTokenHash"]), secret,
    )
    values["canonicalHeadBinding"] = fixed_hash(
        "CRINKL:POM:CANONICAL_HEAD_BINDING:SINGLE_PRODUCT_PURCHASE_MATCH:V1",
        digest(private["canonicalHeadEventHash"]), secret,
    )

    campaign_commitment = value_commitment("campaignId", "IDENTIFIER", values["campaignId"])
    epoch_commitment = value_commitment("campaignEpochRef", "SHA256_REF", values["campaignEpochRef"])
    purpose_commitment = value_commitment("purpose", "ENUM", values["purpose"])
    values["purchaseReuseNullifier"] = fixed_hash(
        "CRINKL:POM:PURCHASE_REUSE:SINGLE_PRODUCT_PURCHASE_MATCH:V1",
        digest(campaign_commitment), digest(epoch_commitment), digest(purpose_commitment),
        poseidon_bytes(private["productPurchaseCommitment"]), secret,
    )
    values["entitlementNullifier"] = fixed_hash(
        "CRINKL:POM:ENTITLEMENT:SINGLE_PRODUCT_PURCHASE_MATCH:V1",
        digest(campaign_commitment), digest(epoch_commitment), digest(purpose_commitment),
        digest(values["ruleCommitment"]), poseidon_bytes(private["productPurchaseCommitment"]), secret,
    )
    values["resultCommitment"] = fixed_hash(
        "CRINKL:POM:RESULT:SINGLE_PRODUCT_PURCHASE_MATCH:V1", b"MATCH"
    )
    values["inputSetCommitment"] = hash_ref(canonical({
        "domain": "crinkl:pom:single-product-input-set:v1",
        "inputs": [{
            "inputIndex": 0,
            "spendTokenBinding": values["spendTokenBinding"],
            "canonicalHeadBinding": values["canonicalHeadBinding"],
            "issuerRegistryRef": values["spendIssuerRegistryRef"],
            "verificationPolicyRef": values["spendVerificationPolicyRef"],
            "purchaseReuseNullifier": values["purchaseReuseNullifier"],
        }],
    }))

    pre_replay = {
        name: value_commitment(name, value_type, values[name])
        for name, value_type in ORDER
        if name not in {"proofReplayInputsCommitment", "proofReplayNullifier"}
    }
    replay_names = [name for name, _ in ORDER[:34]] + [
        "purchaseReuseNullifier", "entitlementNullifier", "resultCommitment"
    ]
    values["proofReplayInputsCommitment"] = hash_ref(canonical({
        "domain": "crinkl:pom:proof-replay-inputs:v1",
        "entries": [pre_replay[name] for name in replay_names],
    }))
    values["proofReplayNullifier"] = fixed_hash(
        "CRINKL:POM:PROOF_REPLAY:SINGLE_PRODUCT_PURCHASE_MATCH:V1",
        digest(values["proofReplayInputsCommitment"]), secret,
    )

    entries = [
        {
            "name": name,
            "valueType": value_type,
            "value": values[name],
            "valueCommitment": value_commitment(name, value_type, values[name]),
        }
        for name, value_type in ORDER
    ]
    public_inputs_commitment = hash_ref(canonical({
        "domain": "crinkl:proof-of-match:public-input-set:v1",
        "encoding": "RFC8785_NAMED_COMMITMENTS_V1",
        "entries": entries,
    }))
    return {
        "spendTokenBinding": values["spendTokenBinding"],
        "canonicalHeadBinding": values["canonicalHeadBinding"],
        "recipientScopeCommitment": values["recipientScopeCommitment"],
        "inputSetCommitment": values["inputSetCommitment"],
        "proofReplayInputsCommitment": values["proofReplayInputsCommitment"],
        "proofReplayNullifier": values["proofReplayNullifier"],
        "purchaseReuseNullifier": values["purchaseReuseNullifier"],
        "entitlementNullifier": values["entitlementNullifier"],
        "resultCommitment": values["resultCommitment"],
        "publicInputsCommitment": public_inputs_commitment,
        "firstValueCommitment": entries[0]["valueCommitment"],
        "proofIdValueCommitment": entries[2]["valueCommitment"],
        "lastValueCommitment": entries[-1]["valueCommitment"],
        "instanceElementCount": len(entries) * 2,
    }


def main() -> None:
    vector = json.loads(VECTOR.read_text())
    actual = derive(vector)
    if "--emit" in sys.argv:
        print(json.dumps(actual, indent=2, sort_keys=True))
        return
    if actual != vector["expected"]:
        raise SystemExit(f"public input vector mismatch: {json.dumps(actual, sort_keys=True)}")

    changed = json.loads(json.dumps(vector))
    changed["values"]["proofId"] = "proof-single-product-002"
    changed_actual = derive(changed)
    for field in ("proofReplayInputsCommitment", "proofReplayNullifier", "publicInputsCommitment"):
        if changed_actual[field] == actual[field]:
            raise SystemExit(f"proofId mutation did not change {field}")

    for schema_path in sorted((ROOT / "schemas/experimental/campaigns").glob("*.schema.json")):
        Draft202012Validator.check_schema(json.loads(schema_path.read_text()))

    build_contract = json.loads(BUILD_CONTRACT.read_text())
    expected_order = [{"name": name, "valueType": value_type} for name, value_type in ORDER]
    if build_contract["publicInputOrder"] != expected_order:
        raise SystemExit("build-contract public input order drift")
    for source in build_contract["relationSources"]:
        actual_hash = hash_ref((ROOT / source["path"]).read_bytes())
        if actual_hash != source["fileSha256"]:
            raise SystemExit(f"relation source hash drift: {source['path']}")
    tree_profile_ref = hash_ref(canonical(json.loads(TREE_PROFILE.read_text())))
    if tree_profile_ref != build_contract["treeProfileRef"]:
        raise SystemExit("tree profile content reference drift")
    profile_schema_ref = hash_ref(canonical(json.loads(PROOF_PROFILE_SCHEMA.read_text())))
    if profile_schema_ref != build_contract["deployedProfileSchemaRef"]:
        raise SystemExit("deployed ProofProfile schema content reference drift")

    print(json.dumps({
        "accepted": 1,
        "hostileProofIdMutations": 3,
        "namedInputs": len(ORDER),
        "instanceElements": actual["instanceElementCount"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
