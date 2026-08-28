#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[4]
SCHEMAS = ROOT / "schemas/experimental/campaigns"
VECTORS = ROOT / "conformance/profiles/single-product-purchase-match-v1/conformance/v1/object-vectors.json"
PASTA_FP_MODULUS = int("40000000000000000000000000000000224698fc094cf91b992d30ed00000001", 16)
TREE_PROFILE_REF = "sha256:c207c15ee1d264b042afc9a04cd252eec3d7120fcf424b359406047c0a95da42"


def replace_pointer(value: Any, pointer: str, replacement: Any) -> None:
    parts = pointer.removeprefix("/").split("/")
    current = value
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    if isinstance(current, list):
        current[int(parts[-1])] = replacement
    else:
        current[parts[-1]] = replacement


def pointer(value: Any, path: str) -> Any:
    current = value
    for part in path.removeprefix("/").split("/"):
        current = current[part]
    return current


def content_ref(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def semantic_errors(file_name: str, value: Any) -> list[str]:
    errors: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for nested in item.values():
                walk(nested)
        elif isinstance(item, list):
            for nested in item:
                walk(nested)
        elif isinstance(item, str) and item.startswith("poseidon:"):
            if int(item.removeprefix("poseidon:"), 16) >= PASTA_FP_MODULUS:
                errors.append("non-canonical Pasta Fp value")

    walk(value)
    if file_name.endswith("snapshot_v1.schema.json"):
        if value.get("treeProfileRef") != TREE_PROFILE_REF:
            errors.append("wrong tree profile")
        authority_field = {
            "spend_acceptance_snapshot_v1.schema.json": "authorityId",
            "product_evidence_snapshot_v1.schema.json": "issuerId",
            "product_evidence_status_snapshot_v1.schema.json": "statusAuthorityId",
            "commerce_entity_registry_snapshot_v1.schema.json": "authorityId",
        }.get(file_name)
        key_field = "issuerKeyRef" if file_name == "product_evidence_snapshot_v1.schema.json" else "authorityKeyRef"
        if authority_field and value["signature"]["issuedBy"] != value[authority_field]:
            errors.append("signature authority mismatch")
        if authority_field and value["signature"]["keyRef"] != value[key_field]:
            errors.append("signature key mismatch")
    if file_name == "commerce_entity_registry_entry_v1.schema.json":
        categories = value.get("categoryRefs", [])
        if categories != sorted(categories):
            errors.append("categoryRefs not sorted")
    if file_name == "single_product_purchase_rule_v1.schema.json":
        window = value.get("purchaseTimeInclusive")
        if window and int(window["minimumUnixMs"]) > int(window["maximumUnixMs"]):
            errors.append("purchase time range inverted")
    if file_name == "product_source_signer_authority_binding_v1.schema.json":
        evidence = value["productEvidenceSigner"]
        status = value["productStatusSigner"]
        for field in ("authorityId", "keyRef", "publicKey"):
            if evidence[field] == status[field]:
                errors.append(f"signer {field} must be distinct")
        for signer in (evidence, status):
            valid_from = int(signer["validFromUnixMs"])
            valid_until = signer["validUntilUnixMs"]
            if valid_until is not None and valid_from >= int(valid_until):
                errors.append("signer validity window inverted")
            if signer["authorityState"] == "REVOKED":
                revoked_at_text = signer["revokedAtUnixMs"]
                if revoked_at_text is not None:
                    revoked_at = int(revoked_at_text)
                    if revoked_at < valid_from:
                        errors.append("signer revocation precedes validity")
    return errors


def errors_for(file_name: str, validator: Draft202012Validator, value: Any) -> list[str]:
    return [error.message for error in validator.iter_errors(value)] + semantic_errors(file_name, value)


def signer_is_admitted(signer: Any, cutoff: datetime) -> bool:
    if signer["authorityState"] != "ACTIVE":
        return False
    cutoff_unix_ms = int(cutoff.timestamp() * 1000)
    if cutoff_unix_ms < int(signer["validFromUnixMs"]):
        return False
    valid_until = signer["validUntilUnixMs"]
    return valid_until is None or cutoff_unix_ms < int(valid_until)


def binding_errors(binding: Any, evidence_snapshot: Any, status_snapshot: Any, dependency: Any) -> list[str]:
    errors: list[str] = []
    campaign_cutoff = datetime.fromtimestamp(int(dependency["statusCutoffUnixMs"]) / 1000, tz=timezone.utc)
    evidence = binding["productEvidenceSigner"]
    status = binding["productStatusSigner"]
    if evidence["role"] != "PRODUCT_EVIDENCE":
        errors.append("product evidence signer has the wrong role")
    if status["role"] != "PRODUCT_STATUS":
        errors.append("product status signer has the wrong role")
    if not signer_is_admitted(evidence, campaign_cutoff):
        errors.append("product evidence signer is not admitted at Campaign cutoff")
    if not signer_is_admitted(status, campaign_cutoff):
        errors.append("product status signer is not admitted at Campaign cutoff")
    if evidence["authorityId"] != evidence_snapshot["issuerId"] or evidence["keyRef"] != evidence_snapshot["issuerKeyRef"]:
        errors.append("product evidence snapshot does not match trusted signer")
    if evidence["snapshotSeriesId"] != evidence_snapshot["snapshotSeriesId"] or evidence["snapshotRef"] != content_ref(evidence_snapshot):
        errors.append("product evidence signer did not pin the exact snapshot")
    if evidence["productVerificationPolicyRef"] != evidence_snapshot["productVerificationPolicyRef"]:
        errors.append("product evidence snapshot policy does not match trusted signer")
    if status["authorityId"] != status_snapshot["statusAuthorityId"] or status["keyRef"] != status_snapshot["authorityKeyRef"]:
        errors.append("product status snapshot does not match trusted signer")
    if status["snapshotSeriesId"] != status_snapshot["snapshotSeriesId"] or status["snapshotRef"] != content_ref(status_snapshot):
        errors.append("product status signer did not pin the exact snapshot")
    if status["statusPolicyRef"] != status_snapshot["statusPolicyRef"]:
        errors.append("product status snapshot policy does not match trusted signer")
    return errors


def epoch_errors(epoch: Any, evaluation_context: Any, binding: Any, dependency: Any) -> list[str]:
    errors: list[str] = []
    scope = binding["campaignScope"]
    for binding_name, epoch_name in (
        ("campaignNamespaceRef", "campaignNamespaceRef"),
        ("campaignId", "campaignId"),
        ("epochSeriesId", "epochSeriesId"),
        ("epochVersion", "epochVersion"),
        ("conditionId", "conversionRuleRef"),
    ):
        if scope[binding_name] != epoch[epoch_name]:
            errors.append("Campaign Epoch coordinate does not match signer binding")
    if scope["evaluationContextHash"] != evaluation_context["evaluationContextHash"]:
        errors.append("resolved evaluation context does not match signer binding")
    if {content_ref(binding), content_ref(dependency)} - set(epoch["registryRefs"]):
        errors.append("Campaign Epoch does not pin dependency and signer binding")
    return errors


def main() -> None:
    vectors = json.loads(VECTORS.read_text())
    validators: dict[str, Draft202012Validator] = {}
    for file_name in vectors["valid"]:
        schema = json.loads((SCHEMAS / file_name).read_text())
        Draft202012Validator.check_schema(schema)
        validators[file_name] = Draft202012Validator(schema)

    for file_name, value in vectors["valid"].items():
        errors = errors_for(file_name, validators[file_name], value)
        if errors:
            raise SystemExit(f"valid {file_name} rejected: {errors}")

    for case in vectors["reject"]:
        value = copy.deepcopy(vectors["valid"][case["schema"]])
        if case.get("op") == "reverse":
            pointer(value, case["path"]).reverse()
        else:
            replace_pointer(value, case["path"], case["value"])
        if not errors_for(case["schema"], validators[case["schema"]], value):
            raise SystemExit(f"hostile object accepted: {case}")

    binding = vectors["valid"]["product_source_signer_authority_binding_v1.schema.json"]
    evidence_snapshot = vectors["valid"]["product_evidence_snapshot_v1.schema.json"]
    status_snapshot = vectors["valid"]["product_evidence_status_snapshot_v1.schema.json"]
    dependency = vectors["valid"]["single_product_purchase_dependencies_v1.schema.json"]
    if binding_errors(binding, evidence_snapshot, status_snapshot, dependency):
        raise SystemExit("valid trusted Platform signer binding rejected")
    if vectors["valid"]["single_product_purchase_dependencies_v1.schema.json"]["productSourceSignerAuthorityBindingRef"] != content_ref(binding):
        raise SystemExit("dependency did not pin the signer binding")
    epoch = vectors["campaignEpoch"]
    evaluation_context = vectors["evaluationContext"]
    if epoch_errors(epoch, evaluation_context, binding, dependency):
        raise SystemExit("valid Campaign Epoch relation rejected")
    for case in vectors["epochReject"]:
        changed = copy.deepcopy(epoch)
        replace_pointer(changed, case["path"], case["value"])
        if not epoch_errors(changed, evaluation_context, binding, dependency):
            raise SystemExit(f"hostile Campaign Epoch accepted: {case}")
    for case in vectors["evaluationContextReject"]:
        changed = copy.deepcopy(evaluation_context)
        replace_pointer(changed, case["path"], case["value"])
        if not epoch_errors(epoch, changed, binding, dependency):
            raise SystemExit(f"hostile evaluation context accepted: {case}")
    for case in vectors["bindingReject"]:
        changed = copy.deepcopy(binding)
        replace_pointer(changed, case["path"], case["value"])
        if not (
            errors_for(
                "product_source_signer_authority_binding_v1.schema.json",
                validators["product_source_signer_authority_binding_v1.schema.json"],
                changed,
            )
            + binding_errors(changed, evidence_snapshot, status_snapshot, dependency)
        ):
            raise SystemExit(f"hostile signer binding accepted: {case}")

    print(json.dumps({
        "acceptedObjects": len(vectors["valid"]),
        "rejectedObjects": len(vectors["reject"]),
        "rejectedSignerBindings": len(vectors["bindingReject"]),
        "rejectedEpochRelations": len(vectors["epochReject"]),
        "rejectedEvaluationContexts": len(vectors["evaluationContextReject"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
