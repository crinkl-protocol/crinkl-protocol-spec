#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[4]
SCHEMAS = ROOT / "schemas/experimental/campaigns"
VECTORS = ROOT / "conformance/profiles/single-product-purchase-match-v1/conformance/v1/object-vectors.json"
PASTA_FP_MODULUS = int("40000000000000000000000000000000224698fc094cf91b992d30ed00000001", 16)
TREE_PROFILE_REF = "sha256:78bf87e5d917babe69fb0ca794d45f6fb759b6aab11ce4d5077a57958243f50d"


def replace_pointer(value: Any, pointer: str, replacement: Any) -> None:
    parts = pointer.removeprefix("/").split("/")
    current = value
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = replacement


def pointer(value: Any, path: str) -> Any:
    current = value
    for part in path.removeprefix("/").split("/"):
        current = current[part]
    return current


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
    return errors


def errors_for(file_name: str, validator: Draft202012Validator, value: Any) -> list[str]:
    return [error.message for error in validator.iter_errors(value)] + semantic_errors(file_name, value)


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

    print(json.dumps({
        "acceptedObjects": len(vectors["valid"]),
        "rejectedObjects": len(vectors["reject"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
