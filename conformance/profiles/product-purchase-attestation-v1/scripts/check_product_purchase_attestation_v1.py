#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[4]
SCHEMA = ROOT / "schemas/experimental/campaigns/product_purchase_attestation_v1.schema.json"
VECTORS = ROOT / "conformance/profiles/product-purchase-attestation-v1/conformance/v1/vectors.json"
SOURCE_MEMBERSHIP_VECTORS = ROOT / "conformance/profiles/product-purchase-attestation-v1/conformance/v1/source-membership-vectors.json"
SOURCE_TREE_PROFILE_REF = "sha256:c207c15ee1d264b042afc9a04cd252eec3d7120fcf424b359406047c0a95da42"
PASTA_FP_MODULUS = int(
    "40000000000000000000000000000000224698fc094cf91b992d30ed00000001", 16
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def pointer_parent(value: Any, pointer: str) -> tuple[Any, str]:
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
    current = value
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current, parts[-1]


def mutate(source: Any, case: dict[str, Any]) -> Any:
    value = copy.deepcopy(source)
    parent, key = pointer_parent(value, case["path"])
    target = parent[int(key)] if isinstance(parent, list) else parent.get(key)
    if case["op"] in ("replace", "add"):
        if isinstance(parent, list):
            parent[int(key)] = case["value"]
        else:
            parent[key] = case["value"]
    elif case["op"] == "reverse":
        target.reverse()
    elif case["op"] == "duplicate-first":
        target[1] = target[0]
    else:
        raise AssertionError(f"unsupported mutation: {case['op']}")
    return value


def semantic_errors(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    facts = value.get("productFacts", {})
    categories = facts.get("categoryRefs", [])
    if isinstance(categories, list) and categories != sorted(categories):
        errors.append("categoryRefs must use ascending unsigned-byte lexical order")
    for field, maximum in (
        ("purchasedAtUnixMs", 9_999_999_999_999),
        ("quantity", 4_294_967_295),
        ("netProductAmountMinor", 18_446_744_073_709_551_615),
    ):
        raw = facts.get(field)
        if isinstance(raw, str) and raw.isdigit() and int(raw) > maximum:
            errors.append(f"{field} exceeds its declared unsigned range")
    for field in ("productPurchaseCommitment", "supersedesProductPurchaseCommitment"):
        raw = value.get(field)
        if isinstance(raw, str) and raw.startswith("poseidon:"):
            try:
                if int(raw.removeprefix("poseidon:"), 16) >= PASTA_FP_MODULUS:
                    errors.append(f"{field} is not a canonical Pasta Fp element")
            except ValueError:
                pass
    issued_at = value.get("issuedAt")
    if isinstance(issued_at, str):
        try:
            datetime.strptime(issued_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            errors.append("issuedAt is not a real UTC calendar timestamp")
    return errors


def errors_for(validator: Draft202012Validator, value: dict[str, Any]) -> list[str]:
    return [error.message for error in validator.iter_errors(value)] + semantic_errors(value)


def content_ref(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def source_membership_vector_errors(
    vector: Any, validator: Draft202012Validator
) -> list[str]:
    errors: list[str] = []
    if not isinstance(vector, dict):
        return ["source membership vector must be an object"]
    if vector.get("kind") != "productSourceMembership.v1" or vector.get("vectorVersion") != 1:
        errors.append("source membership vector kind/version drift")
    if vector.get("treeProfileRef") != SOURCE_TREE_PROFILE_REF:
        errors.append("source membership vector tree profile drift")
    product = vector.get("product")
    status = vector.get("status")
    if not isinstance(product, dict) or not isinstance(status, dict):
        return [*errors, "source membership product/status missing"]
    product_path = product.get("path")
    status_path = status.get("path")
    status_entry = status.get("entry")
    cutoff = status.get("cutoff")
    if not all(isinstance(value, dict) for value in (product_path, status_path, status_entry, cutoff)):
        return [*errors, "source membership path/status structure missing"]
    if product_path.get("treeProfileRef") != SOURCE_TREE_PROFILE_REF or status_path.get("treeProfileRef") != SOURCE_TREE_PROFILE_REF:
        errors.append("source membership path profile drift")
    if product_path.get("treeDomain") != "CRINKL:MERKLE:PRODUCT_EVIDENCE:V1" or status_path.get("treeDomain") != "CRINKL:MERKLE:PRODUCT_EVIDENCE_STATUS:V1":
        errors.append("source membership tree domain drift")
    if product.get("payload") != product_path.get("payload"):
        errors.append("product payload/path mismatch")
    attestation = product.get("attestation")
    if not isinstance(attestation, dict):
        errors.append("product attestation missing")
    else:
        if errors_for(validator, attestation):
            errors.append("product attestation schema/semantic drift")
        if product.get("attestationRef") != content_ref(attestation):
            errors.append("product attestation content reference drift")
        if attestation.get("productPurchaseCommitment") != product.get("payload"):
            errors.append("product attestation/commitment payload mismatch")
        authentication = attestation.get("authentication")
        if not isinstance(authentication, dict) or authentication.get("leafIndex") != product_path.get("leafIndex"):
            errors.append("product attestation/path leaf index mismatch")
        if attestation.get("evidenceStatusEntryRef") != status.get("entryRef"):
            errors.append("product attestation/status entry reference mismatch")
    if status.get("entryRef") != content_ref(status_entry):
        errors.append("status entry content reference drift")
    if status_entry.get("productPurchaseCommitment") != product.get("payload") or status.get("payload") != status_path.get("payload"):
        errors.append("status commitment/payload/path mismatch")
    for path_name, path in (("product", product_path), ("status", status_path)):
        siblings = path.get("siblings")
        leaf_index = path.get("leafIndex")
        if not isinstance(siblings, list) or len(siblings) != 32:
            errors.append(f"{path_name} path sibling count drift")
        if not isinstance(leaf_index, int) or not 0 <= leaf_index < 2**32:
            errors.append(f"{path_name} path leaf index drift")
    cutoff_values = [cutoff.get(name) for name in ("snapshotCutoffUnixMs", "dependencyCutoffUnixMs", "evaluationContextCutoffUnixMs")]
    if not all(isinstance(value, str) and value.isdigit() for value in cutoff_values) or len(set(cutoff_values)) != 1:
        errors.append("status cutoff equality drift")
    elif status_entry.get("status") != "ACCEPTED" or not isinstance(status_entry.get("effectiveAtUnixMs"), str) or not status_entry["effectiveAtUnixMs"].isdigit() or int(status_entry["effectiveAtUnixMs"]) > int(cutoff_values[0]):
        errors.append("status acceptance/effective cutoff drift")
    fields = [
        product.get("payload"), product.get("expectedLeaf"), product_path.get("payload"), product_path.get("expectedRoot"),
        status_entry.get("productPurchaseCommitment"), status.get("payload"), status.get("expectedLeaf"), status_path.get("payload"), status_path.get("expectedRoot"),
        *product_path.get("siblings", []), *status_path.get("siblings", []),
    ]
    if any(not isinstance(value, str) or re.fullmatch(r"poseidon:[0-9a-f]{64}", value) is None or int(value[9:], 16) >= PASTA_FP_MODULUS for value in fields):
        errors.append("source membership noncanonical Pasta field")
    hostile_cases = vector.get("hostileCases")
    expected_hostile_ids = {
        "wrong-profile-ref", "swapped-product-status-domain", "wrong-root", "wrong-payload", "wrong-leaf-index", "wrong-sibling", "reordered-siblings", "short-path", "noncanonical-field", "status-commitment-mismatch", "status-not-accepted", "status-after-cutoff", "status-cutoff-mismatch",
    }
    if not isinstance(hostile_cases, list) or len(hostile_cases) != len(expected_hostile_ids) or {case.get("id") for case in hostile_cases if isinstance(case, dict)} != expected_hostile_ids or any(not isinstance(case, dict) or case.get("expected") != "REJECTED" for case in hostile_cases):
        errors.append("source membership hostile cases drift")
    return errors


def main() -> None:
    schema = load(SCHEMA)
    vectors = load(VECTORS)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    valid = vectors["valid"]
    accepted_errors = errors_for(validator, valid)
    if accepted_errors:
        raise SystemExit(f"valid vector rejected: {accepted_errors}")

    rejected = 0
    for case in vectors["reject"]:
        hostile = mutate(valid, case)
        if not errors_for(validator, hostile):
            raise SystemExit(f"hostile vector accepted: {case['id']}")
        rejected += 1

    membership_errors = source_membership_vector_errors(load(SOURCE_MEMBERSHIP_VECTORS), validator)
    if membership_errors:
        raise SystemExit(f"source membership vector rejected: {membership_errors}")

    print(json.dumps({"accepted": 1, "rejected": rejected, "sourceMembershipHostilesRejected": 13, "schema": schema["$id"]}, sort_keys=True))


if __name__ == "__main__":
    main()
