#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[4]
SCHEMA = ROOT / "schemas/experimental/campaigns/product_purchase_attestation_v1.schema.json"
VECTORS = ROOT / "conformance/profiles/product-purchase-attestation-v1/conformance/v1/vectors.json"
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

    print(json.dumps({"accepted": 1, "rejected": rejected, "schema": schema["$id"]}, sort_keys=True))


if __name__ == "__main__":
    main()
